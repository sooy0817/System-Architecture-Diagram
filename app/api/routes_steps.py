from __future__ import annotations
from fastapi import APIRouter, HTTPException

from app.core.storage import store
from app.schemas.ui_payloads import (
    CorpCenterStepRequest,
    NetworksStepRequest,
    StepResponse,
    NextScopeResponse,
    ScopeDetailRequest,
    ScopeDetailResponse,
)
from app.nodes.step_corp_center import step_corp_center
from app.nodes.step_networks import step_networks

from app.nodes.step_next_scope import step_next_scope
from app.nodes.step_scope_detail import step_scope_detail

router = APIRouter(prefix="/steps", tags=["steps"])


@router.post("/{run_id}/corp-center", response_model=StepResponse)
def post_corp_center(run_id: str, req: CorpCenterStepRequest):
    state = store.get(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="run_id not found")

    # UI 입력을 state에 주입
    state["corporation"] = {"name": req.corporation}
    state["centers"] = req.centers

    # step 실행(지금은 함수 호출 MVP)
    state = step_corp_center(state)

    store.set(run_id, state)
    return {
        "run_id": run_id,
        "state": state,
        "next_step": "networks",
        "message": "법인/센터 저장 완료",
    }


@router.post("/{run_id}/networks", response_model=StepResponse)
def networks_step(run_id: str, req: NetworksStepRequest):
    state = store.get(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail="run_id not found")

    # 여기서 LangGraph 전체를 invoke하지 않고
    # step_networks 노드만 실행
    new_state = step_networks(state, payload=req.model_dump())

    store.set(run_id, new_state)

    return StepResponse(
        run_id=run_id,
        state=new_state,
        next_step="scope-detail",
        message="통신망/장비 저장 완료",
    )


@router.post("/{run_id}/next-scope", response_model=NextScopeResponse)
def next_scope(run_id: str):
    state = store.get(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="run_id not found")

    new_state = step_next_scope(state)
    store.set(run_id, new_state)

    current_scope = new_state.get("current_scope")
    remaining = len(new_state.get("pending_scopes", []))

    if current_scope is None:
        return {
            "run_id": run_id,
            "current_scope": None,
            "remaining": 0,
            "next_step": "user-info",
            "message": "pending_scopes 소진 (다음: 사용자 정보 단계)",
            "state": new_state,
        }

    return {
        "run_id": run_id,
        "current_scope": current_scope,
        "remaining": remaining,
        "next_step": "scope-detail",
        "message": f"다음 scope 준비: {current_scope.get('display')}",
        "state": new_state,
    }


@router.post("/{run_id}/scope-detail", response_model=ScopeDetailResponse)
def scope_detail(run_id: str, req: ScopeDetailRequest):
    state = store.get(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="run_id not found")

    state["scope_detail_text"] = req.detail_text

    new_state = step_scope_detail(state)
    store.set(run_id, new_state)

    return {
        "run_id": run_id,
        "next_step": "next-scope",
        "message": "scope-detail 저장 완료 (다음 scope로 이동 가능)",
        "state": new_state,
    }
