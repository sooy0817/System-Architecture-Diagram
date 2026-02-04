from __future__ import annotations
from typing import TypedDict, Optional, Any, Dict, List


class GraphState(TypedDict, total=False):
    # session
    run_id: str
    raw_text: Optional[str]

    # chat messages
    messages: List[Dict[str, Any]]  # 채팅 메시지 히스토리
    user_message: Optional[str]  # 현재 처리할 사용자 메시지
    last_response: Optional[str]  # 마지막 응답
    last_ui_data: Optional[Dict[str, Any]]  # 마지막 UI 데이터

    # step1: corp/center
    corporation: Optional[Dict[str, Any]]  # {"name": "은행"}
    centers: List[str]  # ["의왕", "안성"]
    current_center_index: Optional[int]  # 현재 처리 중인 센터 인덱스

    # step2: networks
    networks_payload: Optional[Dict[str, Any]]  # API 입력 데이터
    center_networks: Dict[str, Any]  # {"의왕": {...}, "안성": {...}}
    external_networks: List[Dict[str, Any]]

    # scope loop
    pending_scopes: List[
        Dict[str, Any]
    ]  # [{"center": "의왕", "zone": "internal", "display": "의왕 내부망"}, ...]
    current_scope: Optional[
        Dict[str, Any]
    ]  # {"center": "의왕", "zone": "internal", "display": "의왕 내부망"}

    scope_details: Dict[str, Any]  # {"의왕:internal": {...}, ...}
    scope_detail_text: Optional[str]

    # edges
    edge_text: Optional[str]
    edges: Dict[str, Any]

    # routing
    requested_step: Optional[str]
    next_step: Optional[str]

    # validation
    edge_validation: Dict[str, Any]  # {"missing_nodes": [...], "ambiguous": [...]}

    # misc flags
    prefill_done: bool
