from __future__ import annotations
from app.graph.state import GraphState


def mode_router(state: GraphState) -> str:
    return "prefill" if state.get("raw_text") else "skip"


# 나머지 두 개는 다음 단계에서 붙입니다(스코프/엣지 검증 들어갈 때)
def scope_loop_router(state: GraphState) -> str:
    return "has_scope" if state.get("pending_scopes") else "done"


def edge_validation_router(state: GraphState) -> str:
    ev = state.get("edge_validation") or {}
    return "review" if (ev.get("missing_nodes") or ev.get("ambiguous")) else "export"
