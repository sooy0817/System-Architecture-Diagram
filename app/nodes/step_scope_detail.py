# app/nodes/step_scope_detail.py
from __future__ import annotations

from typing import Any, Dict, List
from app.graph.state import GraphState
from app.core.candidates import get_candidate_extractor


def _scope_key(scope: Dict[str, Any]) -> str:
    return f"{scope.get('center')}:{scope.get('zone')}"


def step_scope_detail(state: GraphState) -> GraphState:
    scope = state.get("current_scope")
    if not scope:
        state.setdefault("edge_validation", {})
        state["edge_validation"]["scope_detail_error"] = "current_scope is null"
        state["next_step"] = "user-info"
        return state

    detail_text = (state.get("scope_detail_text") or "").strip()

    extractor = get_candidate_extractor()
    cands = extractor.extract(detail_text) if detail_text else []

    record: Dict[str, Any] = {
        "scope": scope,
        "text": detail_text,
        "candidates": [
            {
                "text": c.text,
                "type": c.type,
                "span": list(c.span),
                "context": c.context,
                "normalized": c.normalized,
            }
            for c in cands
        ],
    }

    key = _scope_key(scope)
    scope_details = dict(state.get("scope_details") or {})
    scope_details[key] = record
    state["scope_details"] = scope_details

    # 소비했으면 비워두기
    state["scope_detail_text"] = None

    # 다음은 next-scope를 호출해서 이동
    state["next_step"] = "next-scope"
    return state
