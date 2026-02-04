# app/graph/nodes_wrapped.py
from __future__ import annotations

from typing import Any, Dict

from app.graph.state import GraphState

from app.nodes.step_corp_center import step_corp_center
from app.nodes.step_networks import step_networks
from app.nodes.step_next_scope import step_next_scope
from app.nodes.step_scope_detail import step_scope_detail

# LangGraph interrupt (없으면 fallback)
try:
    from langgraph.types import interrupt  # type: ignore
except Exception:  # pragma: no cover
    interrupt = None  # type: ignore


def node_corp_center(state: GraphState) -> GraphState:
    """
    routes_steps.py에서 state에 corporation/centers를 주입한 뒤 호출됨.
    """
    return step_corp_center(state)


def node_networks(state: GraphState) -> GraphState:
    """
    routes_steps.py에서 networks payload를 state에 주입한 뒤 호출됨.
    step_networks는 payload를 받는 시그니처라서, state에 저장된 payload를 꺼내 전달.
    """
    payload = state.get("_networks_payload") or {}
    new_state = step_networks(state, payload=payload)
    # payload는 소비했으니 제거(선택)
    new_state.pop("_networks_payload", None)
    return new_state


def node_next_scope(state: GraphState) -> GraphState:
    """
    pending_scopes에서 current_scope를 세팅/이동시키는 노드
    """
    return step_next_scope(state)


def node_scope_detail(state: GraphState) -> GraphState:
    """
    current_scope가 잡혀있으면 해당 scope의 detail_text를 받아 candidates 저장.
    - detail_text가 없으면 interrupt로 "입력 필요" 상태를 반환할 수 있음
    - 하지만 현재 /scope-detail 라우트로 텍스트를 받으니,
      여기서는 '없으면 그냥 next_step만 세팅'하거나 interrupt를 선택하면 됨.
    """
    scope = state.get("current_scope")
    if not scope:
        state["next_step"] = "done"
        return state

    detail_text = state.get("scope_detail_text")

    if (detail_text is None) or (not str(detail_text).strip()):
        # 정석: interrupt로 UI에게 "입력해줘" 신호
        if interrupt is not None:
            interrupt(
                {
                    "need": "scope_detail_text",
                    "scope": scope,
                    "message": f"{scope.get('display')} 영역의 상세 설명을 입력해 주세요.",
                }
            )
        # fallback: next_step만 설정
        state["next_step"] = "scope-detail"
        return state

    # detail_text가 있으면 기존 로직 실행
    new_state = step_scope_detail(state)

    # step_scope_detail은 보통 scope_detail_text를 None 처리했을 것
    # 다음 scope로 이동시키려면 next_scope로 넘어가야 함
    new_state["next_step"] = "next-scope"
    return new_state
