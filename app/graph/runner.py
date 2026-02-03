from __future__ import annotations
from typing import Dict, Any

from app.graph.build import build_graph, run_graph

_graph = build_graph()


def run_node(node_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph 전체를 돌리는 게 아니라,
    특정 노드만 단독 실행하고 싶을 때 쓰는 runner.
    MVP에서는 '함수 호출'로도 충분하지만,
    callbacks(Langfuse)를 붙이려면 run_graph를 통해 통일하는 편이 편함.
    """
    # 노드 단독 실행: langgraph의 내부 API를 쓰기보다는
    # 현재는 노드 함수를 직접 호출하는 MVP 전략을 권장
    # -> Langfuse 관측은 다음 단계에서 graph run으로 통일
    raise NotImplementedError("use function-call approach in routes for now")
