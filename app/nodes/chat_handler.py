# app/nodes/chat_handler.py
"""
채팅 메시지를 처리하는 LangGraph 노드
"""

from __future__ import annotations
from typing import Dict, Any

from app.graph.state import GraphState
from app.nodes.chat_processor import process_chat_message


def chat_handler(state: GraphState) -> dict:
    """
    채팅 메시지를 처리하고 상태를 업데이트하는 노드

    입력:
        - state["user_message"]: 사용자 입력 메시지
        - state["next_step"]: 현재 단계

    출력:
        - state 전체 업데이트 (current_center_index, center_networks 등)
    """
    # state가 튜플이면 딕셔너리로 변환
    if isinstance(state, tuple):
        state = dict(state[0]) if state else {}
    elif not isinstance(state, dict):
        state = dict(state) if state else {}

    user_message = state.get("user_message", "")

    if not user_message or user_message == "초기화":
        # 초기화 메시지면 환영 메시지만 설정하고 반환
        if user_message == "초기화":
            state["last_response"] = state.get("last_response", "")
            state["user_message"] = None
        return state

    # process_chat_message가 state를 직접 수정함
    chat_result = process_chat_message(state, user_message)

    # chat_result에서 반환된 정보를 state에 추가
    state["last_response"] = chat_result.get("response", "")
    state["last_ui_data"] = chat_result.get("ui_data", {})

    # user_message는 처리 완료 후 제거 (다음 호출 시 재처리 방지)
    state["user_message"] = None

    return state
