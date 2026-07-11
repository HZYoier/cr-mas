"""风格警察"""
import subprocess
import json
from cr_mas.graph.state import ReviewState

def run(file_path: str) -> dict:
    """
    对单个文件运行 flake8，返回标准化的问题列表
    参数:
        file_path: 要检查的 Python 文件路径
    返回:
        {"issues": [...], "summary": {...}}
    """
    result = subprocess.run(["flake8", "--format=json", file_path], capture_output = True, text = True)
    issues = []
    if result.stdout.strip():
        file_issues = json.loads(result.stdout).get(file_path, [])
        for v in file_issues:
            issues.append({
                "file": file_path,
                "line": v["line_number"],
                "col": v["column_number"],
                "rule_id": v["code"], # 违反哪条规则
                "desc": v["text"] # 具体描述
            })

    return {
        "agent": "Style",
        "issues": issues,
        "summary": {"total": len(issues)}
    }
    

def review_node(state: ReviewState) -> dict:
    # 遍历变更文件，汇总风格警察报告
    all_issues = []
    for file_path in state["changed_files"]:
        if not file_path.endswith(".py"): # 过滤非.py文件
            continue

        try:
            result = run(file_path)
        except Exception as e:
            all_issues.append({
                "file": file_path,
                "line": 0,
                "col": 0,
                "rule_id": "ERROR",
                "desc": f"风格警察运行失败: {e}"
            })
            continue
        
        all_issues.extend(result["issues"])

    return{
        "style_report": {
            "agent": "Style",
            "issues": all_issues,
            "summary": {"total": len(all_issues)},
        }
    }

