from __future__ import annotations
import uuid
from typing import Dict, Any, List

PREFIX_MAP = {
    "Corporation": "corp",
    "Center": "ctr",
    "NetworkZone": "zone",
    "ServerGroup": "svrg",
    "Server": "svr",
    "DBMS": "dbms",
    "Interface": "if",
    "ExternalSystem": "ext",
    "NetworkDevice": "nd",
    "Line": "line",
    "User": "user",
}


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def assign_ids(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    - nodes 배열을 순회하며
    - id 없는 노드에만 prefix-uuid 부여
    - 이미 id가 있으면 절대 건드리지 않음
    """
    nodes: List[Dict[str, Any]] = state.get("nodes", [])

    for node in nodes:
        if "id" in node and node["id"]:
            continue

        label = node.get("label")
        if not label:
            raise ValueError("Node without label cannot get ID")

        prefix = PREFIX_MAP.get(label)
        if not prefix:
            raise ValueError(f"Unknown label for ID assignment: {label}")

        node["id"] = _new_id(prefix)

    state["nodes"] = nodes
    return state
