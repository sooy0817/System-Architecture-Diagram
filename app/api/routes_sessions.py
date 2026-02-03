from __future__ import annotations
from fastapi import APIRouter

from app.core.storage import store
from app.graph.build import build_graph, run_graph
from app.schemas.ui_payloads import CreateSessionRequest, CreateSessionResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])

graph = build_graph()


@router.post("", response_model=CreateSessionResponse)
def create_session(req: CreateSessionRequest):
    run_id = store.new_run_id()

    state = {
        "run_id": run_id,
        "raw_text": req.raw_text,
    }

    new_state = run_graph(graph, state)
    store.set(run_id, new_state)

    return {"run_id": run_id, "state": new_state}


@router.get("/{run_id}")
def get_session(run_id: str):
    return {"run_id": run_id, "state": store.get(run_id)}
