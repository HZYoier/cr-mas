"""性能顾问"""

import ast
import radon.complexity as radon_cc
from cr_mas.graph.state import ReviewState
from cr_mas.tools.file_reader import read_source

def _compute_nesting(node, depth = 0):
    # 计算控制流节点的最大嵌套深度
    max_d = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            d = _compute_nesting(child, depth + 1)
        else:
            d = _compute_nesting(child, depth)
        if d > max_d:
            max_d = d
    return max_d


def run(file_path: str, hot_lines: list = None) -> dict:
    """
    分析单个文件的代码圈复杂度指标
    参数:
        file_path: 目标文件路径
        hot_lines: 安全哨兵标记的高风险行号列表
    返回:
        {"metrics": {...}, "hotspot_details": [...]}
    """
    source = read_source(file_path)

    # 圈复杂度
    cc_results = radon_cc.cc_visit(source) # 块列表
    overall_cc = max((block.complexity for block in cc_results), default = 0)

    # 嵌套深度(AST)
    tree = ast.parse(source)
    max_depth = _compute_nesting(tree)

    # 高风险行分析
    hotspot_details = []
    if hot_lines:
        source_lines = source.split("\n")
        for line_no in hot_lines:
            if line_no <= len(source_lines):
                # 找到该行所在的函数
                line_cc = 0
                for block in cc_results:
                    if block.lineno <= line_no <= block.endline:
                        line_cc = block.complexity
                        break
                hotspot_details.append({
                    "file": file_path,
                    "line": line_no,
                    "cyclomatic_complexity": line_cc,
                    "code_snippet": source_lines[line_no - 1].strip()
                })

    return {
        "metrics": {
            "cyclomatic_complexity": overall_cc,
            "nesting_depth": max_depth
        },
        "hotspot_details": hotspot_details
    }


def review_node(state: ReviewState) -> dict:
    """
    遍历变更文件，分析每个文件的复杂度指标
    从安全哨兵获取 hot_lines 进行重点分析
    """
    hot_lines = []
    sec = state.get("security_report")
    if sec:
        hot_lines = sec.get("hot_lines", [])

    all_metrics = {}
    all_hotspots = []

    for file_path in state["changed_files"]:
        if not file_path.endswith(".py"):
            continue
        file_hot_lines = [h["line"] for h in hot_lines if h["file"] == file_path]
        
        try:
            result = run(file_path, file_hot_lines)
        except Exception as e:
            all_metrics[file_path] = {
                "cyclomatic_complexity": 0,
                "nesting_depth": 0,
                "error": str(e)
            }
            continue

        all_metrics[file_path] = result["metrics"]
        all_hotspots.extend(result["hotspot_details"])

    return {
        "performance_report": {
            "metrics": all_metrics,
            "hotspot_details": all_hotspots
        }
    }


