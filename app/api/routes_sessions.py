# app/api/routes_sessions.py
from __future__ import annotations

import uuid
from fastapi import APIRouter
from datetime import datetime

from app.graph.graph import graph
from app.schemas.ui_payloads import ChatMessage

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("")
def create_session():
    """
    새 세션 생성 - 간단한 초기화

    초기 상태만 설정하고, 그래프는 첫 메시지에서 시작
    """
    run_id = f"run-{uuid.uuid4().hex[:16]}"

    # 환영 메시지
    welcome_message = ChatMessage(
        role="assistant",
        content='안녕하세요! 구성도 생성 도구입니다.\n\n어떤 법인의 구성도를 만들어드릴까요?\n법인명과 센터 정보를 알려주세요.\n\n예시: "법인은 은행이고 AWS, 의왕으로 구성되어있습니다"',
        timestamp=datetime.now().isoformat(),
    )

    init_state = {
        "run_id": run_id,
        "raw_text": None,
        "corporation": None,
        "centers": [],
        "current_center_index": 0,
        "center_networks": {},
        "external_networks": [],
        "pending_scopes": [],
        "current_scope": None,
        "scope_details": {},
        "scope_detail_text": None,
        "edge_validation": {},
        "next_step": "corp-center",
        "messages": [welcome_message.model_dump()],
        "user_message": None,
        "last_response": welcome_message.content,
        "last_ui_data": {},
    }

    config = {"configurable": {"thread_id": run_id}}

    # 초기 상태를 저장 - invoke로 한 번만 실행
    try:
        # 그래프를 통해 초기 상태 저장
        result = graph.invoke(init_state, config=config)
        print(f"Session created: {run_id}")
        print(f"Initial state saved: {type(result)}")
    except Exception as e:
        print(f"Error initializing session: {e}")
        import traceback

        traceback.print_exc()
        result = init_state

    return {
        "run_id": run_id,
        "state": result if isinstance(result, dict) else init_state,
        "messages": [welcome_message.model_dump()],
        "current_step": "corp-center",
    }
