# app/nodes/step_edges.py
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from app.graph.state import GraphState
from app.core.candidates import get_candidate_extractor


HEADER_RE = re.compile(r"^\s*\[(?P<header>[^\]]{1,60})\]\s*$", re.MULTILINE)


def _split_by_headers(text: str) -> List[Tuple[str, str]]:
    """
    [헤더] 블록으로 분할.
    반환: [(header, block_text), ...]
    - 헤더가 하나도 없으면 [("GLOBAL", text)]로 반환
    """
    text = (text or "").strip()
    if not text:
        return []

    matches = list(HEADER_RE.finditer(text))
    if not matches:
        return [("GLOBAL", text)]

    blocks: List[Tuple[str, str]] = []
    for i, m in enumerate(matches):
        header = m.group("header").strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        if block:
            blocks.append((header, block))
        else:
            blocks.append((header, ""))  # 빈 블록도 기록은 남김(원하면 skip 가능)
    return blocks


def _header_to_scope_key(state: GraphState, header: str) -> str:
    """
    헤더 문자열을 state의 scope 키(예: '의왕:internal')로 매핑.
    - 아주 MVP 버전: header에 '의왕 내부망' 같은 display가 오면 pending/current_scope의 display로 매칭
    - 못 찾으면 header 그대로 key 사용
    """
    header_norm = header.strip()

    # 1) scope_details/ pending_scopes/current_scope의 display와 매칭 시도
    all_scopes = []
    cur = state.get("current_scope")
    if cur:
        all_scopes.append(cur)
    all_scopes.extend(state.get("pending_scopes") or [])

    for sc in all_scopes:
        if (sc.get("display") or "").strip() == header_norm:
            return f"{sc.get('center')}:{sc.get('zone')}"

    # 2) scope_details에 이미 있는 키들의 display를 보고 매칭(있으면)
    # (현재 scope_details record에 display는 있지만 key는 center:zone이라서 직접 매칭은 제한적)

    # 3) 못 찾으면 header 자체를 key로 둠(나중에 resolver에서 정리)
    return header_norm


def step_edges(state: GraphState) -> GraphState:
    edge_text = (state.get("edge_text") or "").strip()
    if not edge_text:
        state.setdefault("edge_validation", {})
        state["edge_validation"]["edges_error"] = "edge_text is empty"
        state["next_step"] = "edges"
        return state

    extractor = get_candidate_extractor()
    blocks = _split_by_headers(edge_text)

    edges_out: Dict[str, Any] = dict(state.get("edges") or {})
    edges_by_scope: Dict[str, Any] = {}

    for header, block in blocks:
        scope_key = _header_to_scope_key(state, header)
        cands = extractor.extract(block) if block else []

        edges_by_scope[scope_key] = {
            "header": header,
            "text": block,
            "candidates": [
                {
                    "text": c.text,
                    "type": c.type,
                    "span": list(c.span),
                    "context": c.context,
                    "normalized": c.normalized,
                }
                for c in cands
            ],
        }

    edges_out["raw"] = edge_text
    edges_out["by_scope"] = edges_by_scope
    state["edges"] = edges_out

    # 입력 소비
    state["edge_text"] = None

    # 다음 단계: 일단 done(혹은 review)
    state["next_step"] = "done"
    return state
