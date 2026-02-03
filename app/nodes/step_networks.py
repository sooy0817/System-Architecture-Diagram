from __future__ import annotations

from typing import Any, Dict, List

from app.graph.state import GraphState
from app.extract.candidate_extractor import CandidateExtractor

_ce = CandidateExtractor()

ZONE_CANON_ALLOW = {"internal", "dmz", "internal_sdn", "external", "user", "branch"}


def _extract_zone_norms(text: str) -> List[str]:
    """자유 텍스트에서 ZoneHint만 뽑아 normalized 목록으로 반환"""
    zones = []
    for c in _ce.extract(text):
        if c.type == "ZoneHint" and c.normalized in ZONE_CANON_ALLOW:
            zones.append(c.normalized)
    # 중복 제거(순서 유지)
    seen = set()
    out = []
    for z in zones:
        if z not in seen:
            seen.add(z)
            out.append(z)
    return out


DEVICE_CAND_TYPES = {"DeviceTypeHint", "DeviceSubtypeHint"}


def _extract_device_tokens(text: str) -> List[Dict[str, Any]]:
    """자유 텍스트에서 Device 후보를 전부 저장 (type + subtype)"""
    items = []
    for c in _ce.extract(text):
        if c.type in DEVICE_CAND_TYPES:
            items.append(
                {
                    "text": c.text,
                    "normalized": c.normalized,
                    "span": c.span,
                    "kind": c.type,
                }
            )
    items.sort(key=lambda x: (x["span"][0], x["span"][1]))
    return items


def step_networks(state: GraphState, payload: Dict[str, Any]) -> GraphState:
    """
    payload 예:
      {
        "center_zones": {"의왕":"내부망, DMZ망", "안성":"내부망, DMZ망"},
        "center_devices": {"의왕":"외부GSLB, SK회선, ..."},
        "external_networks": [{"name":"중계기관", "zones":"대외망"}]
      }
    """
    centers = state.get("centers", [])
    center_zones: Dict[str, str] = payload.get("center_zones") or {}
    center_devices: Dict[str, str] = payload.get("center_devices") or {}
    external_networks_in = payload.get("external_networks") or []

    # 1) center_networks 채우기
    center_networks: Dict[str, Any] = {}

    for center in centers:
        zones_text = center_zones.get(center, "")
        devices_text = center_devices.get(center, "")

        zone_norms = _extract_zone_norms(zones_text)
        device_items = _extract_device_tokens(devices_text) if devices_text else []

        center_networks[center] = {
            "zones_raw": zones_text,  # 원문 보존
            "zones": zone_norms,  # normalized
            "devices_raw": devices_text,  # 원문 보존
            "devices": device_items,  # 후보 저장
        }

    # 2) external_networks 저장 (원문 + normalized)
    external_networks_out: List[Dict[str, Any]] = []
    for item in external_networks_in:
        name = item.get("name", "")
        zones_raw = item.get("zones", "") or ""
        zone_norms = _extract_zone_norms(zones_raw)

        external_networks_out.append(
            {
                "name": name,
                "zones_raw": zones_raw,
                "zones": zone_norms,
            }
        )

    # 3) pending_scopes 생성
    pending_scopes: List[Dict[str, str]] = []
    for center, info in center_networks.items():
        for z in info.get("zones", []):
            display = f"{center} {'DMZ망' if z == 'dmz' else _zone_display_ko(z)}"
            pending_scopes.append(
                {
                    "center": center,
                    "zone": z,
                    "display": display,
                }
            )

    # 외부 네트워크도 scope로 처리하고 싶다면(선택)
    for ex in external_networks_out:
        for z in ex.get("zones", []):
            display = f"{ex['name']} {_zone_display_ko(z)}"
            pending_scopes.append(
                {
                    "center": ex[
                        "name"
                    ],  # center 자리에 외부네트워크 이름을 넣는 정책(단순)
                    "zone": z,
                    "display": display,
                }
            )

    # state 업데이트
    state["center_networks"] = center_networks
    state["external_networks"] = external_networks_out
    state["pending_scopes"] = pending_scopes
    state["current_scope"] = None

    # 다음 스텝 안내
    state["next_step"] = "scope-detail"

    return state


def _zone_display_ko(z: str) -> str:
    return {
        "internal": "내부망",
        "dmz": "DMZ망",
        "internal_sdn": "내부SDN망",
        "external": "대외망",
        "user": "사용자망",
        "branch": "영업점망",
    }.get(z, z)
