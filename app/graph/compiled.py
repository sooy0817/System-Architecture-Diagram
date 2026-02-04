# app/graph/compiled.py
from __future__ import annotations

from typing import Literal

from langgraph.graph import StateGraph, START, END  # type: ignore

from app.graph.state import GraphState
from app.graph.checkpointer import get_checkpointer
from app.graph.nodes_wrapped import (
    node_corp_center,
    node_networks,
    node_next_scope,
    node_scope_detail,
)

# memory로 고정. 필요시 env로 변경
_checkpointer = get_checkpointer(mode="memory")


def _route_after_next_scope(state: GraphState) -> Literal["scope_detail", "__end__"]:
    """
    next_scope 실행 후 어디로 갈지 결정
    """
    if state.get("current_scope"):
        return "scope_detail"
    return "__end__"


def _route_after_scope_detail(
    state: GraphState,
) -> Literal["next_scope", "scope_detail"]:
    """
    scope_detail 처리 후 다음으로
    - detail_text가 없어서 입력대기면 다시 scope_detail
    - 저장까지 끝났으면 next_scope로
    """
    # step_scope_detail가 정상 처리되면 next_step을 "next-scope"로 세팅
    if state.get("next_step") == "next-scope":
        return "next_scope"
    return "scope_detail"


def build_graph():
    g = StateGraph(GraphState)

    # nodes
    g.add_node("corp_center", node_corp_center)
    g.add_node("networks", node_networks)
    g.add_node("next_scope", node_next_scope)
    g.add_node("scope_detail", node_scope_detail)

    # edges (기본 흐름)
    g.add_edge(START, "corp_center")
    g.add_edge("corp_center", "networks")
    g.add_edge("networks", "next_scope")

    # loop
    g.add_conditional_edges(
        "next_scope",
        _route_after_next_scope,
        {
            "scope_detail": "scope_detail",
            "__end__": END,
        },
    )
    g.add_conditional_edges(
        "scope_detail",
        _route_after_scope_detail,
        {
            "next_scope": "next_scope",
            "scope_detail": "scope_detail",
        },
    )

    graph = g.compile(checkpointer=_checkpointer)
    return graph


graph = build_graph()
