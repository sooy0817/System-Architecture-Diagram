# app/nodes/step_next_scope.py
from __future__ import annotations
from typing import Any, Dict, List

from app.graph.state import GraphState


def step_next_scope(state: GraphState) -> GraphState:
    pending: List[Dict[str, Any]] = list(state.get("pending_scopes") or [])

    if not pending:
        state["current_scope"] = None
        state["next_step"] = "user-info"
        return state

    # FIFO
    cur = pending.pop(0)
    state["current_scope"] = cur
    state["pending_scopes"] = pending
    state["next_step"] = "scope-detail"
    return state
