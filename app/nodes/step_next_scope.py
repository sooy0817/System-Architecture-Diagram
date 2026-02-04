# app/nodes/step_next_scope.py
from __future__ import annotations

from typing import Any, Dict
from app.graph.state import GraphState


def step_next_scope(state: GraphState) -> GraphState:
    """
    pending_scopes에서 다음 scope를 꺼내서 current_scope로 설정하는 단계.
    - pending_scopes가 비어있으면 모든 scope 처리 완료로 간주
    """
    pending_scopes = list(state.get("pending_scopes") or [])

    if not pending_scopes:
        # 모든 scope 처리 완료
        state["current_scope"] = None
        state["next_step"] = "edges"
        return state

    # 첫 번째 scope를 current_scope로 설정
    current_scope = pending_scopes.pop(0)
    state["current_scope"] = current_scope
    state["pending_scopes"] = pending_scopes

    # 다음 단계는 scope-detail 입력
    state["next_step"] = "scope-detail"

    return state
