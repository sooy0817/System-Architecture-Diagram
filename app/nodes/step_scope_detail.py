# app/nodes/step_scope_detail.py
from __future__ import annotations

from typing import Any, Dict
from app.graph.state import GraphState
from app.core.candidates import get_candidate_extractor


def _scope_key(scope: Dict[str, Any]) -> str:
    """scope 객체를 키 문자열로 변환"""
    return f"{scope.get('center')}:{scope.get('zone')}"


def step_scope_detail(state: GraphState) -> GraphState:
    """
    current_scope의 상세 정보를 처리하여 scope_details에 저장하는 단계.
    - scope_detail_text를 받아서 candidate_extractor로 후보 추출
    - scope_details에 저장 후 다음 scope로 이동
    """
    current_scope = state.get("current_scope")
    if not current_scope:
        state.setdefault("edge_validation", {})
        state["edge_validation"]["scope_detail_error"] = "current_scope is null"
        state["next_step"] = "edges"
        return state

    detail_text = (state.get("scope_detail_text") or "").strip()

    print("\n" + "=" * 80)
    print("🔍 STEP: SCOPE DETAIL EXTRACTION")
    print("=" * 80)
    print(f"📍 Current Scope:")
    print(f"   - Center: {current_scope.get('center')}")
    print(f"   - Zone: {current_scope.get('zone')}")
    print(f"   - Display: {current_scope.get('display')}")
    print(f"\n📝 Input Text:")
    print(f"   '{detail_text}'")
    print(f"\n🤖 Running candidate_extractor.extract()...")

    # candidate_extractor로 후보 추출
    extractor = get_candidate_extractor()
    candidates = extractor.extract(detail_text) if detail_text else []

    print(f"\n✅ Extracted {len(candidates)} candidates:")
    print("-" * 80)

    if candidates:
        for i, c in enumerate(candidates, 1):
            print(f"\n[{i}] Type: {c.type}")
            print(f"    Text: '{c.text}'")
            print(f"    Normalized: {c.normalized}")
            print(f"    Span: {c.span}")
            print(f"    Context: {c.context}")
    else:
        print("   (No candidates extracted)")

    print("\n" + "-" * 80)

    # scope_details에 저장할 레코드 생성
    record: Dict[str, Any] = {
        "scope": current_scope,
        "text": detail_text,
        "candidates": [
            {
                "text": c.text,
                "type": c.type,
                "span": list(c.span),
                "context": c.context,
                "normalized": c.normalized,
            }
            for c in candidates
        ],
    }

    # scope_details에 저장
    key = _scope_key(current_scope)
    scope_details = dict(state.get("scope_details") or {})
    scope_details[key] = record
    state["scope_details"] = scope_details

    print(f"\n💾 Saved to scope_details['{key}']")
    print(f"📊 Total scopes collected: {len(scope_details)}")
    print(f"   Keys: {list(scope_details.keys())}")
    print("=" * 80 + "\n")

    # 입력 텍스트 소비
    state["scope_detail_text"] = None

    # 다음 단계는 next-scope (다음 scope로 이동)
    state["next_step"] = "next-scope"

    return state
