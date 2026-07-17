from langgraph.graph import StateGraph, END
from cr_mas.graph.state import ReviewState
from cr_mas.agents.style import review_node as style_node
from cr_mas.agents.security import review_node as security_node
from cr_mas.agents.performance import review_node as performance_node
from cr_mas.agents.readability import review_node as readability_node
from cr_mas.agents.chief import review_node as chief_node
from cr_mas.agents.extension import review_node as extension_node
from cr_mas.agents.bug import review_node as bug_node
from langgraph.checkpoint.memory import MemorySaver


def build_review_graph() -> StateGraph:
    builder = StateGraph(ReviewState)
    builder.add_node("style_keeper", style_node)
    builder.add_node("security", security_node)
    builder.add_node("performance", performance_node)
    builder.add_node("readability", readability_node)
    builder.add_node("chief", chief_node)
    builder.add_node("extension", extension_node)
    builder.add_node("bug", bug_node)

    builder.set_entry_point("style_keeper")

    builder.add_edge("style_keeper", "security")
    builder.add_edge("security", "performance")
    builder.add_edge("performance", "readability")
    builder.add_edge("readability", "extension")
    builder.add_edge("extension", "bug")
    builder.add_edge("bug", "chief")
    builder.add_edge("chief", END)
    
    return builder.compile(checkpointer = MemorySaver())

