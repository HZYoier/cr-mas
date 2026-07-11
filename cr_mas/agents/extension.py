"""扩展顾问——基于 LLM 的架构扩展建议"""

from cr_mas.tools.file_reader import read_source
from cr_mas.graph.state import ReviewState

def run(changed_files: list) -> dict:
    """
    分析所有变更文件，从全局视角给出增量式架构建议
    参数:
        changed_files: 变更文件路径列表
    返回:
        {"suggestions": [...]}
    """

    py_files = [f for f in changed_files if f.endswith(".py")]
    if not py_files:
        return {"suggestions": []}
    
    all_code = ""
    for file_path in py_files:
        source = read_source(file_path)
        all_code += f"\n// === {file_path} ===\n{source}\n"

    try:
        from cr_mas.llm.client import get_pro_llm

        prompt = (
            "你是资深软件架构师。请分析以下代码，给出增量式改进建议。\n\n"
            "分析视角（按优先级）：\n"
            "1. 设计模式——当前代码适合用什么设计模式重构？\n"
            "2. 库/框架——手写逻辑是否可用成熟库替代？\n"
            "3. 架构优化——模块拆分、公共逻辑抽取\n"
            "4. 功能扩展——基于现有代码，可加什么功能？\n"
            "5. 可测试性——是否容易写单元测试？\n\n"
            "规则：\n"
            "- 不要建议'从头重写'\n"
            "- 每个建议必须是增量式的、可落地的\n"
            "- 每个建议包含 type、trigger（文件+行号）、current（现状）、"
            "improvement（改进方向）、priority（HIGH/MEDIUM/LOW）、"
            "effort_hours（预估工时小时数）\n\n"
            f"代码:\n{all_code}\n\n"
            "输出纯 JSON 数组，不要 markdown 包裹。"
            '格式: [{"type": "...", "trigger": {"file": "...", "line": 0}, '
            '"current": "...", "improvement": "...", '
            '"priority": "HIGH", "effort_hours": 2}]'
        )

        llm = get_pro_llm()
        response = llm.invoke(prompt)

        import json
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            if content.endswith("```"):
                content = content.rsplit("\n", 1)[0]
        suggestions = json.loads(content)
        return {"suggestions": suggestions}

    except Exception:
        return {"suggestions": []}



def review_node(state: ReviewState) -> dict:
    result = run(state["changed_files"])
    return {"extension_report": result}

