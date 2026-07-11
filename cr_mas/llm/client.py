"""共享 LLM 客户端——所有 Agent 调用 LLM 的统一入口"""

from cr_mas.config.settings import settings


def get_fast_llm():
    """获取 V4 Flash 实例——日常审查用（安全哨兵、可读性顾问）"""
    from langchain_deepseek import ChatDeepSeek

    return ChatDeepSeek(
        model=settings.deepseek_fast_model,
        api_key=settings.deepseek_api_key,
        temperature=0.1,
    )


def get_pro_llm():
    """获取 V4 Pro 实例——复杂推理用（扩展顾问、主编）"""
    from langchain_deepseek import ChatDeepSeek

    return ChatDeepSeek(
        model=settings.deepseek_pro_model,
        api_key=settings.deepseek_api_key,
        temperature=0.1,
    )
