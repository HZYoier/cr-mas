"""安全哨兵"""
import subprocess
import json
from cr_mas.graph.state import ReviewState
from cr_mas.tools.file_reader import read_source

def run(file_path: str) -> dict:
    """
    对单个文件运行 bandit 安全扫描，返回标准化的问题列表
    参数:
        file_path: 要扫描的 Python 文件路径
    返回:
        {"alerts": [...], "is_critical": bool, "hot_lines": [...]}
    """
    source = read_source(file_path)
    result = subprocess.run(["bandit", "-f", "json", "-q", file_path], capture_output = True, text = True)
    if not result.stdout or not result.stdout.strip():
        return {
            "alerts": [],
            "is_critical": False,
            "hot_lines": []
        }

    bandit_output = json.loads(result.stdout)
    alerts = [] # 问题列表
    hot_lines = [] # 高风险行号
    is_critical = False # 是否有严重漏洞

    for issue in bandit_output.get("results", []):
        severity = "CRITICAL" if issue["issue_severity"] == "HIGH" else "MEDIUM"
        alerts.append({
            "file": file_path,
            "line": issue["line_number"],
            "risk_type": issue["test_id"],
            "severity": severity,
            "description": issue["issue_text"]
        })
        
        if severity == "CRITICAL":
            hot_lines.append(issue["line_number"])
            is_critical = True
    
    # LLM二次确认，判断CRITICAL问题是否误报
    if alerts:
        try:
            from cr_mas.llm.client import get_fast_llm
            source_lines = source.split("\n")
            for alert in alerts:
                if alert["severity"] != "CRITICAL":
                    continue

                # 截取周围共5行代码
                line_no = alert["line"]
                start = max(0, line_no - 3)
                end = min(len(source_lines), line_no + 2)
                context = "\n".join(
                    f"{i + 1}: {source_lines[i]}" for i in range(start, end)
                )

                prompt = (
                    f"你是安全专家，Bandit报告了以下安全问题，请判断是否是真漏洞。\n\n"
                    f"规则: {alert['risk_type']}\n"
                    f"描述: {alert['description']}\n"
                    f"代码:\n'''python\n{context}\n'''\n\n"
                    f"回答: [真] 或 [假]"
                )

                llm = get_fast_llm()
                response = llm.invoke(prompt)
                answer = response.content.strip()

                if answer.startswith("假"):
                    alert["severity"] = "MEDIUM"
                    alert["llm_review"] = "误报，已降级"
        except Exception:
            pass # llm不可用

    return {
        "alerts": alerts,
        "is_critical": is_critical,
        "hot_lines": hot_lines
    }


def review_node(state: ReviewState) -> dict:
    # 遍历变更文件，汇总安全问题
    all_alerts = []
    all_hot_lines = []
    is_critical = False # 有一个文件为CRITICAL则为True

    for file_path in state["changed_files"]:
        if not file_path.endswith(".py"):
            continue

        try:
            result = run(file_path)
        except Exception as e:
            all_alerts.append({
                "file": file_path,
                "line": 0,
                "risk_type": "ERROR",
                "severity": "MEDIUM",
                "description": f"安全哨兵运行失败: {e}"
            })
            continue
        
        all_alerts.extend(result["alerts"]) # 将问题逐一加入
        all_hot_lines.extend({
            "file": file_path,"line": line}
            for line in result["hot_lines"]
        )
        if result["is_critical"]:
            is_critical = True

    return {
        "security_report": {
            "alerts": all_alerts,
            "hot_lines": all_hot_lines,
            "is_critical": is_critical
        }
    }

