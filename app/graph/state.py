from __future__ import annotations
from typing import TypedDict, Optional, Any, Dict, List


class GraphState(TypedDict, total=False):
    # session
    run_id: str
    raw_text: Optional[str]

    # step1: corp/center
    corporation: Optional[Dict[str, Any]]  # {"name": "은행"}
    centers: List[str]  # ["의왕", "안성"]

    # step2 준비
    center_networks: Dict[str, Any]  # {"의왕": {...}, "안성": {...}}
    external_networks: List[Dict[str, Any]]

    # scope loop
    pending_scopes: List[str]  # ["의왕:internal", "의왕:dmz", ...]
    current_scope: Optional[str]

    scope_details: Dict[str, Any]
    scope_detail_text: Optional[str]

    # validation
    edge_validation: Dict[str, Any]  # {"missing_nodes": [...], "ambiguous": [...]}

    # misc flags
    prefill_done: bool
