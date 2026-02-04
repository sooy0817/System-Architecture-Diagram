# app/api/routes_chat.py
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from datetime import datetime

from app.graph.graph import graph
from app.schemas.ui_payloads import ChatRequest, ChatResponse, ChatMessage

router = APIRouter(prefix="/chat", tags=["chat"])


def _load_state(run_id: str) -> dict:
    """상태 로드"""
    config = {"configurable": {"thread_id": run_id}}
    snap = graph.get_state(config)

    if snap is None:
        raise HTTPException(status_code=404, detail="run_id not found")

    # LangGraph의 StateSnapshot은 .values 속성을 가짐
    if hasattr(snap, "values"):
        return dict(snap.values)

    # 혹시 튜플이면 첫 번째 요소가 상태
    if isinstance(snap, tuple):
        return dict(snap[0]) if snap[0] else {}

    # 그 외의 경우
    return dict(snap) if snap else {}


@router.post("/{run_id}/message", response_model=ChatResponse)
def send_message(run_id: str, req: ChatRequest):
    """
    챗봇에 메시지 전송 - 간단한 invoke 방식
    """
    try:
        config = {"configurable": {"thread_id": run_id}}

        # 현재 상태 로드
        state = _load_state(run_id)
        print(f"\n=== Message received: {req.message} ===")
        print(f"Current state keys: {list(state.keys())}")
        print(f"Current step: {state.get('next_step')}")
        print(f"Current center index: {state.get('current_center_index')}")

        # 기존 메시지 히스토리 가져오기
        messages = state.get("messages", [])

        # 사용자 메시지 추가
        user_message = ChatMessage(
            role="user", content=req.message, timestamp=datetime.now().isoformat()
        )
        messages.append(user_message.model_dump())

        # 사용자 메시지를 state에 설정
        state["user_message"] = req.message
        state["messages"] = messages

        # 그래프 실행 - invoke 사용
        print(f"Invoking graph...")
        result = graph.invoke(state, config=config)
        print(f"Graph result type: {type(result)}")

        # 결과를 딕셔너리로 변환
        if isinstance(result, tuple):
            final_state = dict(result[0]) if result else {}
        elif isinstance(result, dict):
            final_state = result
        else:
            final_state = dict(result) if result else {}

        print(f"Final state keys: {list(final_state.keys())}")
        print(f"Next step: {final_state.get('next_step')}")
        print(f"Current center index: {final_state.get('current_center_index')}")

        # 어시스턴트 응답 추가
        assistant_response = final_state.get("last_response", "")
        if assistant_response:
            assistant_message = ChatMessage(
                role="assistant",
                content=assistant_response,
                timestamp=datetime.now().isoformat(),
            )
            messages.append(assistant_message.model_dump())
            final_state["messages"] = messages

        # ui_data 구성
        ui_data = final_state.get("last_ui_data", {})
        ui_data["corporation"] = (final_state.get("corporation") or {}).get("name")
        ui_data["centers"] = final_state.get("centers", [])
        ui_data["center_networks"] = final_state.get("center_networks", {})

        current_center_index = final_state.get("current_center_index", 0)
        centers = final_state.get("centers", [])
        ui_data["current_center"] = (
            centers[current_center_index]
            if centers and 0 <= current_center_index < len(centers)
            else None
        )
        ui_data["current_index"] = current_center_index
        ui_data["total_centers"] = len(centers)

        print(f"UI data: {ui_data}")
        print(f"=== End of message processing ===\n")

        return ChatResponse(
            run_id=run_id,
            messages=[ChatMessage(**msg) for msg in messages],
            current_step=final_state.get("next_step", "corp-center"),
            next_step=final_state.get("next_step"),
            state=final_state,
            ui_data=ui_data,
        )

    except Exception as e:
        import traceback

        traceback.print_exc()

        # 에러 메시지도 채팅 히스토리에 추가
        error_message = ChatMessage(
            role="assistant",
            content=f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}",
            timestamp=datetime.now().isoformat(),
        )

        try:
            state = _load_state(run_id)
            messages = state.get("messages", [])
            messages.append(error_message.model_dump())

            return ChatResponse(
                run_id=run_id,
                messages=[error_message],
                current_step="error",
                state=state,
                ui_data={"error": str(e)},
            )
        except:
            return ChatResponse(
                run_id=run_id,
                messages=[error_message],
                current_step="error",
                state={},
                ui_data={"error": str(e)},
            )


@router.get("/{run_id}/history", response_model=ChatResponse)
def get_chat_history(run_id: str):
    """채팅 히스토리 조회"""
    try:
        state = _load_state(run_id)
        messages = state.get("messages", [])
        current_step = state.get("next_step", "corp-center")

        # ui_data 구성
        ui_data = {}
        ui_data["corporation"] = (state.get("corporation") or {}).get("name")
        ui_data["centers"] = state.get("centers", [])
        ui_data["center_networks"] = state.get("center_networks", {})

        current_center_index = state.get("current_center_index", 0)
        centers = state.get("centers", [])
        ui_data["current_center"] = (
            centers[current_center_index]
            if centers and 0 <= current_center_index < len(centers)
            else None
        )
        ui_data["current_index"] = current_center_index
        ui_data["total_centers"] = len(centers)

        return ChatResponse(
            run_id=run_id,
            messages=[ChatMessage(**msg) for msg in messages],
            current_step=current_step,
            state=state,
            ui_data=ui_data,
        )
    except HTTPException:
        # 세션이 없으면 빈 히스토리 반환
        return ChatResponse(
            run_id=run_id, messages=[], current_step="corp-center", state={}
        )
