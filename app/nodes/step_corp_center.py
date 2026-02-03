from __future__ import annotations
from app.graph.state import GraphState


def step_corp_center(state: GraphState) -> GraphState:
    """
    UI에서 받은 corporation, centers를 state에 고정 저장하는 step.
    - validation은 Pydantic(Request)에서 이미 수행
    - 여기서는 저장 형태만 표준화
    """
    corp = state.get("corporation") or {}
    if isinstance(corp, str):
        corp = {"name": corp}
    # corporation은 dict {"name": "..."} 형태로 통일
    if "name" not in corp:
        # state["corporation"]가 {"name":...}로 안 들어왔으면 raw에서 꺼내기
        # (routes에서 주입할 거라 대부분 안 타겠지만 안전장치)
        corp = {"name": state.get("corporation")}

    state["corporation"] = {"name": corp.get("name")}
    state["centers"] = list(state.get("centers") or [])

    # 다음 단계 준비용 기본값
    state.setdefault("center_networks", {})
    state.setdefault("external_networks", [])
    state.setdefault("pending_scopes", [])
    state.setdefault("current_scope", None)

    return state
