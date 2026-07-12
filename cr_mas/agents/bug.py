"""Bug 猎人——LLM 检测运行时错误和逻辑缺陷"""


from cr_mas.tools.file_reader import read_source
from cr_mas.graph.state import ReviewState
from cr_mas.llm.client import parse_llm_json


def run(file_path: str) -> dict:
    source = read_source(file_path)

    try:
        from cr_mas.llm.client import get_fast_llm
        import json

        prompt = (
            "你是代码审查专家，专门发现运行时错误和逻辑缺陷。\n\n"
            "请检查以下代码，找出可能导致程序崩溃、结果错误或行为异常的问题。\n"
            "关注：TypeError（类型不匹配）、逻辑错误（条件永远为真/假）、"
            "死代码（return/raise 后的不可达语句）、变量未定义、索引越界、"
            "除零风险、资源未关闭等。\n\n"
            "[重要] 你只负责运行时错误和逻辑缺陷。不要报告以下内容——它们由其他专家负责：\n"
            "- 代码格式、空格、import 顺序 → 风格警察\n"
            "- 硬编码密码、SQL 注入等安全问题 → 安全哨兵\n"
            "- 魔法数字、变量命名、注释率、函数拆分 → 可读性顾问\n"
            "- 设计模式、架构优化、库建议 → 扩展顾问\n\n"

            f"代码:\n```python\n{source}\n```\n\n"
            "输出纯 JSON 数组（不要 markdown 包裹）。每个 bug 包含:\n"
            "- line: 行号\n"
            "- severity: CRITICAL（必崩溃）或 MEDIUM（可能出错）\n"
            "- description: 简短描述问题\n"
            "- fix: 修复建议\n"
            '格式: [{"line": 5, "severity": "CRITICAL", '
            '"description": "字符串+数字导致TypeError", '
            '"fix": "将数字转为字符串: str(num)"}]'
        )

        llm = get_fast_llm()
        response = llm.invoke(prompt)
        bugs = parse_llm_json(response.content)
        return {"bugs": bugs}

    except Exception:
        return {"bugs": []}
    

def review_node(state: ReviewState) -> dict:
    all_bugs = []
    for file_path in state["changed_files"]:
        if not file_path.endswith(".py"):
            continue
        try:
            result = run(file_path)
            for bug in result.get("bugs", []):
                bug["file"] = file_path
                all_bugs.append(bug)
        except Exception:
            pass

    return {"bug_report": {"bugs": all_bugs}}


