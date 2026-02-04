# app/api/routes_export.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.graph.graph import graph

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/{run_id}/scope-details")
def export_scope_details(run_id: str):
    """
    특정 세션의 scope_details 추출
    GLiNER 학습 데이터 수집용
    """
    try:
        config = {"configurable": {"thread_id": run_id}}
        snap = graph.get_state(config)

        if snap is None:
            raise HTTPException(status_code=404, detail="Session not found")

        # 상태 추출
        if hasattr(snap, "values"):
            state = snap.values
        elif isinstance(snap, tuple):
            state = snap[0] if snap else {}
        else:
            state = snap or {}

        scope_details = state.get("scope_details", {})

        return {
            "run_id": run_id,
            "scope_details": scope_details,
            "total_scopes": len(scope_details),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all-sessions")
def export_all_sessions():
    """
    모든 세션의 scope_details 추출

    주의: MemorySaver는 모든 세션 목록을 제공하지 않으므로
    실제로는 run_id를 알아야 함
    """
    # MemorySaver의 경우 내부 storage에 직접 접근
    from app.graph.graph import checkpointer

    if hasattr(checkpointer, "storage"):
        all_data = []
        for thread_id, checkpoint_data in checkpointer.storage.items():
            # checkpoint_data 구조 확인 필요
            if isinstance(checkpoint_data, dict):
                state = checkpoint_data.get("checkpoint", {})
            else:
                state = checkpoint_data

            scope_details = (
                state.get("scope_details", {}) if isinstance(state, dict) else {}
            )

            if scope_details:
                all_data.append({"run_id": thread_id, "scope_details": scope_details})

        return {"total_sessions": len(all_data), "sessions": all_data}

    return {
        "error": "Cannot access checkpointer storage",
        "message": "Use Redis checkpointer for production",
    }
