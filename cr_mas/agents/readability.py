"""可读性顾问"""

import ast
from cr_mas.graph.state import ReviewState
from cr_mas.tools.file_reader import read_source


def _find_magic_numbers(tree: ast.AST) -> list[dict]:
    # 用AST找出所有数字字面量
    candidates = []
    skip_values = {0, 1, -1} # 不需要命名的数字

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            value = node.value
            if value not in skip_values:
                candidates.append({
                    "line": node.lineno,
                    "value": value
                })
    
    return candidates



def run(file_path: str) -> dict:
    """
    分析单个文件的可读性指标
    参数:
        file_path: 目标文件路径
    返回:
        {"metrics": {...}, "suggestions": [...]}
    """
    source = read_source(file_path)

    lines = source.split("\n")
    total_lines = len(lines)
    comment_lines = 0 # 注释行总数
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
            comment_lines += 1

    # 注释率
    comment_ratio = round(comment_lines / total_lines, 2) if total_lines > 0 else 0

    tree = ast.parse(source)

    # 检查数字字面量
    magic_candidates = _find_magic_numbers(tree)
    magic_suggestions = []


    if magic_candidates:
        try:
            from cr_mas.llm.client import get_fast_llm

            lines = source.split("\n")
            items = []
            for mc in magic_candidates:
                snippet = lines[mc["line"] - 1].strip()
                items.append(f"第{mc['line']}行：{snippet}")
            
            prompt = (
                "你是代码可读性专家。以下数字字面量中，哪些应该用命名常量替换？\n"
                "只标记含义不明确、或将来可能变化的数字。\n\n"
                + "\n".join(items)
                + "\n\n输出格式: JSON数组 [{line: 行号, name_hint: '建议的常量名'}]，不要 markdown 包裹\n"
                "不需要替换的直接省略。例如: [{\"line\": 3, \"name_hint\": \"TAX_RATE\"}]"
            )

            llm = get_fast_llm()
            response = llm.invoke(prompt)
            import json
            try:
                content = response.content.strip()
                # 去掉markdown包裹
                if content.startswith("```"):
                    content = content.split("\n", 1)[-1] # 去掉第一行
                    if content.endswith("```"):
                        content = content.rsplit("\n", 1)[0] # 去掉最后一行
                magic_suggestions = json.loads(content)
            except json.JSONDecodeError:
                pass
        except Exception:
            pass

    functions = [] # 存储每个函数详细信息
    for node in ast.walk(tree):
        # 普通函数或异步函数
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_lines = node.end_lineno - node.lineno + 1
            functions.append({
                "name": node.name,
                "line": node.lineno,
                "end_line": node.end_lineno,
                "lines": func_lines
            })

    max_function_lines = max((f["lines"] for f in functions), default = 0)

    return {
        "metrics": {
            "total_lines": total_lines,
            "comment_lines": comment_lines,
            "comment_ratio": comment_ratio,
            "function_count": len(functions),
            "max_function_lines": max_function_lines
        },
        "functions": functions,
        "magic_suggestions": magic_suggestions
    }
    


def review_node(state: ReviewState) -> dict:
    """
    遍历变更文件，分析每个文件的可读性指标
    """
    all_metrics = {}
    all_functions = []
    all_magic = []

    for file_path in state["changed_files"]:
        if not file_path.endswith(".py"):
            continue
        
        try:
            result = run(file_path)
        except Exception as e:
            all_metrics[file_path] = {
                "total_lines": 0,
                "comment_lines": 0,
                "comment_ratio": 0,
                "function_count": 0,
                "max_function_lines": 0,
                "error": str(e)
            }
            continue

        all_metrics[file_path] = result["metrics"]
        all_functions.extend(
            {"file": file_path, **f} for f in result["functions"]
        )
        all_magic.extend(
            {"file": file_path, **m} for m in result.get("magic_suggestions", [])
        )

    return {
        "readability_report": {
            "metrics": all_metrics,
            "functions": all_functions,
            "magic_suggestions": all_magic
        }
    }



