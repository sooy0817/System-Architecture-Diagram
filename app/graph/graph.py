# app/graph/graph.py
from __future__ import annotations

from langgraph.graph import StateGraph, END

# from langgraph.checkpoint.memory import MemorySaver  # ← 기존
from langgraph.checkpoint.redis import RedisSaver  # ← Redis 사용

from app.graph.state import GraphState
from app.nodes.chat_handler import chat_handler

# Redis 체크포인터 (영구 저장)
checkpointer = RedisSaver(
    redis_url="redis://localhost:6379/0"  # Redis 연결 정보
)

# 또는 MemorySaver (개발용)
# checkpointer = MemorySaver() # 인스턴스 생성


def build_graph():
    """
    Human-in-the-Loop 패턴을 사용한 대화형 워크플로우

    흐름:
    1. chat_handler: 사용자 입력 처리
    2. router: 다음 단계 결정
    3. wait_for_input: 사용자 입력 대기 (interrupt)
    """
    g = StateGraph(GraphState)

    # 메인 노드: 채팅 처리
    g.add_node("chat_handler", chat_handler)

    # 사용자 입력 대기 노드 (더미 - 실제로는 interrupt에서 멈춤)
    g.add_node("wait_for_input", lambda s: s)

    # 라우터: 다음 단계 결정
    def router(state: GraphState) -> str:
        next_step = state.get("next_step")

        # 완료 상태면 END
        if next_step == "done":
            return END

        # 그 외에는 사용자 입력 대기
        # (corp-center, networks, scope-detail, edges 모두 사용자 입력 필요)
        return "wait_for_input"

    # 엔트리 포인트
    g.set_entry_point("chat_handler")

    # chat_handler 후 라우팅
    g.add_conditional_edges("chat_handler", router)

    # wait_for_input 후 다시 chat_handler로 (사용자가 입력하면 재개)
    g.add_edge("wait_for_input", "chat_handler")

    # interrupt_before: 이 노드 실행 전에 멈춤
    return g.compile(checkpointer=checkpointer, interrupt_before=["wait_for_input"])


graph = build_graph()
