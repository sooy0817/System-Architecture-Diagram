from __future__ import annotations

from langgraph.graph import StateGraph, END

from app.graph.state import GraphState
from app.graph.routers import mode_router
from app.nodes.init_session import init_session
from app.nodes.prefill import auto_prefill_from_raw

from app.core.langfuse_client import get_langfuse_handler
from app.nodes.step_corp_center import step_corp_center


def build_graph():
    g = StateGraph(GraphState)

    g.add_node("init_session", init_session)
    g.add_node("prefill", auto_prefill_from_raw)
    g.add_node("step_corp_center", step_corp_center)

    g.set_entry_point("init_session")

    # init_session -> mode_router 분기
    g.add_conditional_edges(
        "init_session",
        mode_router,
        {
            "prefill": "prefill",
            "skip": END,
        },
    )

    # prefill 끝나면 일단 종료(다음 스텝 노드들은 다음 단계에서 붙임)
    g.add_edge("prefill", END)

    return g.compile()


def run_graph(graph, state: GraphState):
    """
    Langfuse tracing은 여기서만 주입합니다.
    (노드 내부에서 callbacks 신경 X)
    """
    handler = get_langfuse_handler()
    if handler is None:
        return graph.invoke(state)
    return graph.invoke(state, config={"callbacks": [handler]})
