from cr_mas.graph.state import ReviewState
from cr_mas.memory.sqlite_store import get_agent_accuracy
from cr_mas.llm.client import parse_llm_json


def _build_memory_context() -> str:
    """
    从长期记忆里读取 Agent 的历史采纳率，
    供 LLM参考
    """
    rows = get_agent_accuracy()
    if not rows:
        return "暂无历史数据，按默认权重裁决。\n"
    
    lines = ["各 Agent 历史采纳率："]
    for r in rows:
        lines.append(
            f"  - [{r['module'] or '全部模块'}] {r['agent_source']:}"
            f"{r['accepted']}/{r['total']} 采纳，"
            f"准确率 {r['rate']}%"
        )
    return "\n".join(lines)


def _detect_conflicts_with_llm(reports: dict, memory_text: str) -> dict:
    """
    将6份报告打包发给 V4 Pro，检测 Agent 间的矛盾并裁决
    返回 LLM 的建议裁决，失败时返回空 dict
    """
    import json
    from cr_mas.llm.client import get_pro_llm

    prompt = (
        "你是代码审查委员会的主编。收到了 6 位专家 Agent 的审查报告，"
        "请检测报告之间是否存在矛盾，并给出裁决。\n\n"
        f"## 历史记忆\n{memory_text}\n"
        f"## 风格警察报告\n{json.dumps(reports.get('style', {}), ensure_ascii=False)}\n\n"
        f"## 安全哨兵报告\n{json.dumps(reports.get('security', {}), ensure_ascii=False)}\n\n"
        f"## 性能顾问报告\n{json.dumps(reports.get('performance', {}), ensure_ascii=False)}\n\n"
        f"## 可读性顾问报告\n{json.dumps(reports.get('readability', {}), ensure_ascii=False)}\n\n"
        f"## 扩展顾问报告\n{json.dumps(reports.get('extension', {}), ensure_ascii=False)}\n\n"
        f"## Bug 猎人报告\n{json.dumps(reports.get('bug', {}), ensure_ascii=False)}\n\n"
        "## 裁决规则\n"
        "1. 安全哨兵 is_critical=True → 无条件采纳，放在 must_fix\n"
        "2. 风格/可读性建议互相矛盾时 → 查历史采纳率，采纳率高的优先\n"
        "3. 性能 vs 可读性矛盾时 → 保守：性能优先\n"
        "4. 扩展建议 → 始终放 lowest 优先级\n"
        "5. Bug 猎人 severity=CRITICAL → 必须修复；MEDIUM → 强烈建议\n"
        "## 输出格式\n"
        "输出纯 JSON（不要 markdown 包裹），结构如下：\n"
        '{\n'
        '  "conflicts_detected": true/false,\n'
        '  "conflicts": [\n'
        '    {"between": ["可读性顾问", "性能顾问"], "issue": "描述", '
        '"resolution": "裁决理由", "winner": "胜出一方"}\n'
        '  ],\n'
        '  "overrides": [\n'
        '    {"source": "可读性顾问", "original_line": 2, '
        '"action": "downgrade/upgrade", "reason": "理由"}\n'
        '  ]\n'
        '}'
    )

    try:
        llm = get_pro_llm()
        response = llm.invoke(prompt)
        return parse_llm_json(response.content)
    except Exception:
        return {}


def review_node(state: ReviewState):
    """
    收集所有 Agent 报告，按严重程度分成四档：
    🔴 必须修复 / 🟡 强烈建议 / 🔵 可选优化 / 💡 扩展建议
    返回:
        {"final_report": {...}, "react_trace": [...]}
    """
    style = state.get("style_report", {})
    security = state.get("security_report", {})
    performance = state.get("performance_report", {})
    readability = state.get("readability_report", {})
    extension = state.get("extension_report", {})
    bug = state.get("bug_report", {})
    trace = [] # ReAct推理链

    # LLM冲突检测
    reports = {
        "style": style,
        "security": security,
        "performance": performance,
        "readability": readability,
        "extension": extension,
        "bug": bug
    }
    memory_text = _build_memory_context()
    llm_analysis = _detect_conflicts_with_llm(reports, memory_text)
    if llm_analysis.get("conflicts_detected"):
        trace.append(
            f"LLM检测到 {len(llm_analysis.get('conflicts', []))} 个 Agent 冲突"
        )
        for conflict in llm_analysis.get("conflicts", []):
            trace.append(
                f"  ⚡ {conflict.get('between')} 冲突: "
                f"{conflict.get('issue')} → {conflict.get('resolution')}"
            )
    else:
        trace.append("LLM未检测到 Agent 间冲突， 按默认规则分类")


    critical_fixes = [] # 必须修复
    strong_suggestions = [] # 强烈建议
    optional_improvements = [] # 可选优化
    extension_advice = [] # 扩展建议
    

    # 处理安全哨兵的报告
    if security:
        alerts = security.get("alerts", [])
        is_critical = security.get("is_critical", False)

        for alert in alerts:
            if alert.get("severity") == "CRITICAL":
                critical_fixes.append({
                    "file": alert.get("file"),
                    "line": alert.get("line"),
                    "type": f"安全问题 - {alert.get('risk_type')}",
                    "desc": alert.get("description"),
                    "source": "安全哨兵"
                })

        trace.append(
            f"安全哨兵：{len(alerts)} 个安全问题， 其中{len(critical_fixes)} 个严重"
        )


    # 处理Bug猎人的报告
    if bug:
        bugs = bug.get("bugs", [])
        for b in bugs:
            item = {
                "file": b.get("file"),
                "line": b.get("line"),
                "type": f"潜在 bug",
                "desc": f"{b.get('description', '')} → {b.get('fix', )}",
                "source": "Bug 猎人"
            }
            if b.get("severity") == "CRITICAL":
                critical_fixes.append(item)
            else:
                strong_suggestions.append(item)
        
        trace.append(
            f"Bug 猎人：发现 {len(bugs)} 个潜在缺陷，"
            f"其中 {len([b for b in bugs if b.get('severity') == 'CRITICAL'])} 个严重"
        )
    

    # 处理性能顾问的报告
    if performance:
        metrics = performance.get("metrics", {})
        hotspots = performance.get("hotspot_details", [])

        for hotspot in hotspots:
            cc = hotspot.get("cyclomatic_complexity", 0)
            if cc >= 10:
                strong_suggestions.append({
                    "file": hotspot.get("file"),
                    "line": hotspot.get("line"),
                    "type": "圈复杂度较高",
                    "desc": f"圈复杂度为 {cc}, 代码片段：{hotspot.get('code_snippet')}",
                    "source": "性能顾问"
                })

        trace.append(
            f"性能顾问：分析了 {len(metrics)} 个文件，热点行 {len(hotspots)} 处，其中 {len(strong_suggestions)} 处圈复杂度较高"
        )


    # 处理可读性顾问的报告
    if readability:
        metrics = readability.get("metrics", {})
        functions = readability.get("functions", [])

        for file_path, m in metrics.items():
            if m.get("comment_ratio", 1) < 0.1:
                strong_suggestions.append({
                    "file": file_path,
                    "line": None,
                    "type": "注释率过低",
                    "desc": f"注释率仅 {m['comment_ratio']:.0%}（{m.get('comment_lines', 0)}/{m.get('total_lines', '?')} 行），建议为关键逻辑和函数添加注释",
                    "source": "可读性顾问"
                })
            
            # 魔法数字
            magic_list = readability.get("magic_suggestions", [])
            for magic in magic_list:
                if magic.get("file") == file_path:
                    strong_suggestions.append({
                        "file": file_path,
                        "line": magic.get("line"),
                        "type": "魔法数字",
                        "desc": f"建议定义常量 {magic.get('name_hint', 'UNNAMED')}",
                        "source": "可读性顾问"
                    })
            # 变量命名
            naming_list = readability.get("naming_suggestions", [])
            for naming in naming_list:
                if naming.get("file") == file_path:
                    strong_suggestions.append({
                        "file": file_path,
                        "line": naming.get("line"),
                        "type": "命名建议",
                        "desc": f"变量 {naming.get('name', '')} → {naming.get('suggestion', '')}",
                        "source": "可读性顾问"
                    })

            # 函数拆分
            split_list = readability.get("split_suggestions", [])
            for split in split_list:
                if split.get("name") in [f["name"] for f in functions if f.get("file") == file_path]:
                    strong_suggestions.append({
                        "file": file_path,
                        "line": split.get("line"),
                        "type": "建议拆分函数 - {split.get('reason', '')}",
                        "desc": f"建议拆分为: {', '.join(split.get('suggested_split', []))}",
                        "source": "可读性顾问"
                    })

            if m.get("max_function_lines", 0) > 50:
                long_funcs = [f for f in functions if f['file'] == file_path and f['lines'] > 50]
                for lf in long_funcs:
                    strong_suggestions.append({
                        "file": lf["file"],
                        "line": lf["line"],
                        "type": "函数过长",
                        "desc": f"函数 {lf['name']} 长度为 {lf['lines']} 行，建议拆分为更小的函数",
                        "source": "可读性顾问"
                    })

        trace.append(
            f"可读性顾问：分析了 {len(metrics)} 个文件，"
            f"共 {len(functions)} 个函数"
        )


    # 处理扩展顾问的报告
    if extension:
        suggestions = extension.get("suggestions", [])
        for sug in suggestions:
            trigger = sug.get("trigger", {})
            extension_advice.append({
                "file": trigger.get("file"),
                "line": trigger.get("line"),
                "type": f"{sug.get('type', '建议')}",
                "desc": f"现状：{sug.get('current', 'N/A')} → {sug.get('improvement', 'N/A')}",
                "priority": sug.get("priority", "MEDIUM"),
                "effort_hours": sug.get("effort_hours"),
                "source": "扩展顾问"
            })
        
        trace.append(
            f"扩展顾问：{len(suggestions)} 条架构优化建议"
        )


    # 处理风格警察的报告，进入可选优化
    if style:
        issues = style.get("issues", [])

        for issue in issues:
            optional_improvements.append({
                "file": issue.get("file"),
                "line": issue.get("line"),
                "col": issue.get("col"),
                "type": f"风格问题 - {issue.get('rule_id')}",
                "desc": issue.get("desc"),
                "source": "风格警察"
            })

        trace.append(
            f"风格警察：发现 {len(issues)} 个风格问题"
        )

    # 汇总最终报告
    total = len(critical_fixes) + len(strong_suggestions) + len(optional_improvements) + len(extension_advice)

    return {
        "final_report": {
            "critical_fixes": critical_fixes,
            "strong_suggestions": strong_suggestions,
            "optional_improvements": optional_improvements,
            "extension_advice": extension_advice,
            "summary": {
                "total": total,
                "critical": len(critical_fixes),
                "strong": len(strong_suggestions),
                "optional": len(optional_improvements),
                "extension": len(extension_advice)
            }
        },
        "react_trace": trace
    }
    
