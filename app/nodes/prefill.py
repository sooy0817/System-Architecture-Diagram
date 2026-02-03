from __future__ import annotations
from app.graph.state import GraphState


def auto_prefill_from_raw(state: GraphState) -> GraphState:
    # MVP: raw_text가 있으면 prefill_done만 표시
    state["prefill_done"] = True
    return state
