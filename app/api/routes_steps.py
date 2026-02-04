# app/api/routes_steps.py
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from langfuse.langchain import CallbackHandler


from app.graph.graph import graph
from app.schemas.ui_payloads import (
    CorpCenterStepRequest,
    NetworksStepRequest,
    ScopeDetailRequest,
    EdgesRequest,
    StepResponse,
    NextScopeResponse,
    ScopeDetailResponse,
    EdgesResponse,
)

router = APIRouter(prefix="/steps", tags=["steps"])


def _load_state(run_id: str) -> dict:
    snap = graph.get_state(config={"configurable": {"thread_id": run_id}})
    if snap is None or snap.values is None:
        raise HTTPException(status_code=404, detail="run_id not found")
    return dict(snap.values)


def _invoke(run_id: str, state: dict) -> dict:
    langfuse_handler = CallbackHandler(
        session_id=run_id,
        # user_id="(로그인 유저 있으면 여기에)",
        # tags=["graph_lang", state.get("requested_step", "unknown")],
    )

    return graph.invoke(
        state,
        config={
            "configurable": {"thread_id": run_id},
            "callbacks": [langfuse_handler],
            "metadata": {
                "run_id": run_id,
                "requested_step": state.get("requested_step"),
            },
        },
    )


@router.post("/{run_id}/corp-center", response_model=StepResponse)
def post_corp_center(run_id: str, req: CorpCenterStepRequest):
    state = _load_state(run_id)

    state["corporation"] = {"name": req.corporation}
    state["centers"] = req.centers
    state["requested_step"] = "corp_center"

    new_state = _invoke(run_id, state)
    return StepResponse(
        run_id=run_id,
        state=new_state,
        next_step="networks",
        message="법인/센터 저장 완료",
    )


@router.post("/{run_id}/networks", response_model=StepResponse)
def post_networks(run_id: str, req: NetworksStepRequest):
    state = _load_state(run_id)

    state["networks_payload"] = req.model_dump()
    state["requested_step"] = "networks"

    new_state = _invoke(run_id, state)
    return StepResponse(
        run_id=run_id,
        state=new_state,
        next_step="next-scope",
        message="통신망/장비 저장 완료",
    )


@router.post("/{run_id}/next-scope", response_model=NextScopeResponse)
def next_scope(run_id: str):
    state = _load_state(run_id)
    state["requested_step"] = "next_scope"

    new_state = _invoke(run_id, state)
    cur = new_state.get("current_scope")
    remaining = len(new_state.get("pending_scopes") or [])

    if cur is None:
        return {
            "run_id": run_id,
            "current_scope": None,
            "remaining": 0,
            "next_step": "edges",
            "message": "pending_scopes 소진 (다음: edges)",
            "state": new_state,
        }

    return {
        "run_id": run_id,
        "current_scope": cur,
        "remaining": remaining,
        "next_step": "scope-detail",
        "message": f"다음 scope 준비: {cur.get('display')}",
        "state": new_state,
    }


@router.post("/{run_id}/scope-detail", response_model=ScopeDetailResponse)
def scope_detail(run_id: str, req: ScopeDetailRequest):
    state = _load_state(run_id)

    state["scope_detail_text"] = req.detail_text
    state["requested_step"] = "scope_detail"

    new_state = _invoke(run_id, state)
    return {
        "run_id": run_id,
        "next_step": "next-scope",
        "message": "scope-detail 저장 완료",
        "state": new_state,
    }


@router.post("/{run_id}/edges", response_model=EdgesResponse)
def post_edges(run_id: str, req: EdgesRequest):
    state = _load_state(run_id)

    state["edge_text"] = req.edge_text
    state["requested_step"] = "edges"

    new_state = _invoke(run_id, state)
    return {
        "run_id": run_id,
        "next_step": new_state.get("next_step", "done"),
        "message": "엣지 텍스트 저장 완료",
        "state": new_state,
    }
