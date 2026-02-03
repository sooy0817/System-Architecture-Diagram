from __future__ import annotations
import uuid
from app.graph.state import GraphState


def init_session(state: GraphState) -> GraphState:
    # if not state.get("run_id"):
    #     state["run_id"] = uuid.uuid4().hex
    state.setdefault("corporation", None)
    state.setdefault("centers", [])

    state.setdefault("center_networks", {})
    state.setdefault("external_networks", [])

    state.setdefault("pending_scopes", [])
    state.setdefault("current_scope", None)

    state.setdefault("edge_validation", {})
    state.setdefault("prefill_done", False)

    state.setdefault("scope_details", {})
    state.setdefault("scope_detail_text", None)

    return state
