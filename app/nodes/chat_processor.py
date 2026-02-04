# app/nodes/chat_processor.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.graph.state import GraphState
from app.core.candidates import get_candidate_extractor


# =========================================================
# 0) Small utilities
# =========================================================
def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _ensure_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _dedupe_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out


def _sort_centers_preferred(centers: List[str]) -> List[str]:
    """
    사용자 입장에서 자연스러운 시작 센터 우선순위.
    필요 시 프로젝트별로 튜닝.
    """
    preferred = ["의왕", "안성", "AWS", "IDC"]
    return sorted(
        centers,
        key=lambda x: preferred.index(x) if x in preferred else 999,
    )


# =========================================================
# 1) Chat history (절대 삭제하지 않음)
# =========================================================
def _ensure_history(state: GraphState) -> None:
    if "chat_history" not in state or not isinstance(state.get("chat_history"), list):
        state["chat_history"] = []


def _push_history(
    state: GraphState,
    *,
    role: str,
    text: str,
    step: str,
    ui_data: Optional[dict] = None,
    meta: Optional[dict] = None,
) -> None:
    _ensure_history(state)
    state["chat_history"].append(
        {
            "role": role,
            "text": text,
            "step": step,
            "ts": _now_iso(),
            "ui_data": ui_data or {},
            "meta": meta or {},
        }
    )


# =========================================================
# 2) UI schema (front-friendly) + bubble rendering (세련된 텍스트)
# =========================================================
def _ui_actions(*actions: str) -> List[dict]:
    """
    프론트가 버튼으로 렌더링할 수 있는 액션들.
    value를 그대로 사용자 입력으로 보내면 됨.
    """
    mapping = {
        "back": {"type": "back", "label": "이전", "value": "다시"},
        "reset": {"type": "reset", "label": "처음부터", "value": "다시"},
        "summary": {"type": "summary", "label": "요약", "value": "요약"},
    }
    return [mapping[a] for a in actions if a in mapping]


def _ui_payload(
    *,
    title: str,
    subtitle: Optional[str],
    step: str,
    progress: Tuple[int, int],  # (current, total)
    summary: dict,
    target: dict,
    extracted: dict,
    examples: List[str],
    actions: List[str],
    helper: Optional[str] = None,
) -> dict:
    cur, tot = progress
    return {
        "header": {"title": title, "subtitle": subtitle},
        "progress": {"step": step, "current": cur, "total": tot},
        "summary": summary,
        "target": target,
        "extracted": extracted,
        "examples": [{"label": x, "value": x} for x in examples],
        "actions": _ui_actions(*actions),
        "helper_text": helper,
    }


def _format_status_block(
    *,
    step_label: str,
    corporation: Optional[str],
    centers: List[str],
    current_center: Optional[str] = None,
    center_index: Optional[int] = None,
    center_total: Optional[int] = None,
    center_networks: Optional[dict] = None,
) -> str:
    centers = centers or []
    center_networks = center_networks or {}

    # 제목은 딱 한 줄 (아이콘 X / 필요하면 []만)
    lines: List[str] = [f"[{step_label}]"]

    if corporation:
        lines.append(f"법인: {corporation}")

    if centers:
        lines.append(f"센터: {', '.join(centers)}")

    if current_center:
        if center_index is not None and center_total is not None:
            lines.append(
                f"현재 입력: {current_center} ({center_index + 1}/{center_total})"
            )
        else:
            lines.append(f"현재 입력: {current_center}")

    # 완료 요약(있는 것만)
    done_chunks = []
    for c, info in center_networks.items():
        zones = info.get("zones", [])
        if isinstance(zones, list):
            z = ", ".join(zones)
        else:
            z = str(zones)
        if z:
            done_chunks.append(f"{c}=[{z}]")

    lines.append(f"완료: {' | '.join(done_chunks) if done_chunks else '-'}")

    return "\n".join(lines)


def _bubble(
    *,
    question: str,
    examples: List[str],
    hint: Optional[str] = None,
    show_back_hint: bool = True,
) -> str:
    """
    사이드바에 이미 상태 정보가 표시되므로, 메시지는 질문과 예시만 간결하게.
    """
    ex = " / ".join(examples) if examples else ""

    parts = [question]

    if ex:
        parts.append(f"\n💡 예시: {ex}")
    if hint:
        parts.append(f"\n💬 {hint}")

    if show_back_hint:
        parts.append("\n\n🔄 수정하려면 '다시'라고 입력하세요")

    return "\n".join(parts)


# =========================================================
# 3) Public entry
# =========================================================
def process_chat_message(state: GraphState, user_message: str) -> Dict[str, Any]:
    extractor = get_candidate_extractor()
    step = state.get("next_step", "corp-center")

    msg = (user_message or "").strip()

    # 기록: 사용자 입력은 무조건 누적
    _push_history(state, role="user", text=msg, step=step, meta={})

    # 특수 명령
    if msg.lower() in ["요약", "상태", "summary"]:
        res = _handle_summary(state)
        _push_history(
            state,
            role="assistant",
            text=res["response"],
            step=res["next_step"],
            ui_data=res.get("ui_data"),
        )
        return res

    if msg.lower() in ["다시", "돌아가", "이전", "뒤로", "reject", "back"]:
        res = _handle_back(state, current_step=step)
        _push_history(
            state,
            role="assistant",
            text=res["response"],
            step=res["next_step"],
            ui_data=res.get("ui_data"),
        )
        return res

    # 단계별 처리
    if step == "corp-center":
        res = _step_corp_center(state, msg, extractor)
    elif step == "networks":
        res = _step_networks(state, msg, extractor)
    elif step == "scope-detail":
        res = _step_scope_detail(state, msg, extractor)
    elif step == "edges":
        res = _step_edges(state, msg, extractor)
    else:
        ui = _ui_payload(
            title="오류",
            subtitle="단계를 인식할 수 없습니다",
            step=step,
            progress=(1, 1),
            summary={"next_step": step},
            target={},
            extracted={"message": msg},
            examples=[],
            actions=["summary", "reset"],
            helper="next_step 값을 확인해주세요.",
        )
        res = {
            "response": "단계를 인식할 수 없습니다.",
            "next_step": step,
            "ui_data": ui,
        }

    # 기록: 어시스턴트 응답도 누적
    _push_history(
        state,
        role="assistant",
        text=res["response"],
        step=res["next_step"],
        ui_data=res.get("ui_data"),
    )
    return res


# =========================================================
# 4) Summary + Back (대화 삭제 금지)
# =========================================================
def _handle_summary(state: GraphState) -> Dict[str, Any]:
    corp = (state.get("corporation") or {}).get("name")
    centers = _ensure_list(state.get("centers"))
    center_networks = state.get("center_networks", {})
    cur_idx = state.get("current_center_index", 0)
    cur_center = centers[cur_idx] if centers and 0 <= cur_idx < len(centers) else None

    status = _format_status_block(
        step_label=state.get("next_step", "corp-center"),
        corporation=corp,
        centers=centers,
        current_center=cur_center,
        center_index=cur_idx if cur_center else None,
        center_total=len(centers) if centers else None,
        center_networks=center_networks,
    )

    ui = _ui_payload(
        title="현재 요약",
        subtitle="지금까지 입력된 값",
        step=state.get("next_step", "corp-center"),
        progress=(1, 1),
        summary={
            "corporation": corp,
            "centers": centers,
            "center_networks": center_networks,
            "current_center_index": cur_idx,
            "current_scope": state.get("current_scope"),
        },
        target={"current_center": cur_center},
        extracted={},
        examples=["다시", "이전", "계속 진행"],
        actions=["back", "reset"],
        helper="원하는 단계로 돌아가려면 '다시'를 입력하세요. (기록은 유지됩니다)",
    )

    response = _bubble(
        question="요약 화면입니다. 계속 진행하려면 현재 단계에 맞는 입력을 해주세요.",
        examples=["(단계에 맞는 입력)"],
        hint="요약은 상태 확인용이며, 대화 기록은 삭제되지 않습니다.",
    )

    return {
        "response": response,
        "next_step": state.get("next_step", "corp-center"),
        "ui_data": ui,
    }


def _handle_back(state: GraphState, current_step: str) -> Dict[str, Any]:
    """
    '다시' 입력 시: 단계만 되돌리고, chat_history는 절대 삭제하지 않음.
    """
    corp = (state.get("corporation") or {}).get("name")
    centers = _ensure_list(state.get("centers"))

    if current_step == "networks":
        # networks 단계에서는 이전 센터로 돌아가기
        idx = int(state.get("current_center_index", 0) or 0)

        if idx > 0:
            # 이전 센터로 돌아가기
            prev_idx = idx - 1
            state["current_center_index"] = prev_idx
            prev_center = (
                centers[prev_idx] if centers and prev_idx < len(centers) else None
            )

            # 이전 센터의 네트워크 정보 삭제 (다시 입력받기 위해)
            center_networks = state.get("center_networks", {})
            if prev_center and prev_center in center_networks:
                del center_networks[prev_center]
                state["center_networks"] = center_networks

            ui = _ui_payload(
                title="이전 센터로 돌아가기",
                subtitle=f"{prev_center} 센터 재입력",
                step="networks",
                progress=(prev_idx + 1, len(centers)),
                summary={
                    "corporation": corp,
                    "centers": centers,
                    "center_networks": center_networks,
                },
                target={"center": prev_center},
                extracted={"action": "back_to_prev_center"},
                examples=["내부망, DMZ망", "내부망만"],
                actions=["summary"],
            )
            response = _bubble(
                question=f"이전 센터로 돌아갑니다.\n\n`{prev_center}` 센터의 네트워크 영역을 다시 입력해주세요.",
                examples=["내부망, DMZ망", "내부망만"],
                show_back_hint=False,
            )
            return {"response": response, "next_step": "networks", "ui_data": ui}
        else:
            # 첫 번째 센터인 경우 corp-center로 돌아가기
            state["next_step"] = "corp-center"
            state["current_center_index"] = 0
            # 법인/센터 정보 삭제
            state["corporation"] = None
            state["centers"] = []
            state["center_networks"] = {}

            ui = _ui_payload(
                title="법인/센터 단계",
                subtitle="다시 입력해주세요",
                step="corp-center",
                progress=(1, 1),
                summary={},
                target={},
                extracted={"action": "back_to_corp_center"},
                examples=["은행 의왕센터와 AWS 구성도", "중앙회 안성센터 구성도"],
                actions=["summary"],
            )
            response = _bubble(
                question="법인과 센터를 다시 입력해주세요.",
                examples=["은행 의왕센터와 AWS 구성도", "중앙회 안성센터 구성도"],
                show_back_hint=False,
            )
            return {"response": response, "next_step": "corp-center", "ui_data": ui}

    if current_step == "scope-detail":
        state["next_step"] = "networks"
        state["current_center_index"] = 0
        # 네트워크 정보 삭제
        state["center_networks"] = {}

        cur_center = centers[0] if centers else None
        ui = _ui_payload(
            title="네트워크 단계",
            subtitle="센터별 네트워크를 다시 입력",
            step="networks",
            progress=(1, max(len(centers), 1)),
            summary={
                "centers": centers,
                "center_networks": {},
            },
            target={"center": cur_center},
            extracted={"action": "back_to_networks"},
            examples=["내부망, DMZ망", "내부망만"],
            actions=["summary"],
        )
        response = _bubble(
            question=f"`{cur_center or '첫 센터'}`의 네트워크 영역을 다시 입력해주세요.",
            examples=["내부망, DMZ망", "내부망만", "지점망, 사용자망"],
            show_back_hint=False,
        )
        return {"response": response, "next_step": "networks", "ui_data": ui}

    if current_step == "edges":
        state["next_step"] = "scope-detail"
        ui = _ui_payload(
            title="스코프 상세",
            subtitle="영역별 시스템을 다시 입력",
            step="scope-detail",
            progress=(1, 1),
            summary={"current_scope": state.get("current_scope")},
            target={"scope": state.get("current_scope")},
            extracted={"action": "back_to_scope_detail"},
            examples=["서버: nbefapp01", "DB: orclprod", "장비: IRT 라우터"],
            actions=["summary"],
        )
        response = _bubble(
            question="영역 상세 입력 단계로 돌아갑니다. 현재 영역 정보를 다시 입력해주세요.",
            examples=["서버: nbefapp01, nbefapp02", "DB: orclprod", "장비: IRT 라우터"],
            show_back_hint=False,
        )
        return {"response": response, "next_step": "scope-detail", "ui_data": ui}

    # corp-center 에서 다시 누르면 안내만
    ui = _ui_payload(
        title="첫 단계",
        subtitle="이미 첫 단계입니다",
        step=current_step,
        progress=(1, 1),
        summary={},
        target={},
        extracted={"action": "no_more_back"},
        examples=["은행 의왕센터와 AWS 구성도"],
        actions=["summary"],
    )
    response = _bubble(
        question="이미 첫 단계입니다. 법인/센터 정보를 입력해주세요.",
        examples=["은행 의왕센터와 AWS 구성도"],
    )
    return {"response": response, "next_step": current_step, "ui_data": ui}


# =========================================================
# 5) Step: corp-center (Fuzzy Matching 적용)
# =========================================================
def _step_corp_center(state: GraphState, message: str, extractor) -> Dict[str, Any]:
    from app.extract.fuzzy_matcher import fuzzy_matcher

    # Fuzzy 매칭 실행
    match_result = fuzzy_matcher.match_entities(message)

    # 확인 대기 상태 체크
    pending_confirmation = state.get("pending_confirmation")

    # 사용자가 확인 응답을 한 경우
    if pending_confirmation:
        confirm_keywords = ["확인", "네", "yes", "맞아", "맞습니다", "ok", "ㅇㅋ"]
        reject_keywords = ["아니", "no", "다시", "아니요"]

        msg_lower = message.lower().strip()

        if any(k in msg_lower for k in confirm_keywords):
            # 확인 완료 - pending 데이터 사용
            corporations = pending_confirmation.get("corporations", [])
            centers = pending_confirmation.get("centers", [])

            # pending 상태 제거
            state.pop("pending_confirmation", None)

            # 다음 단계로 진행 (아래 성공 로직과 동일)
            corporation = corporations[0] if corporations else "기본법인"
            if not centers:
                centers = ["센터1"]

            state["corporation"] = {"name": corporation}
            state["centers"] = centers
            state["current_center_index"] = 0
            state["center_networks"] = state.get("center_networks", {})
            state["next_step"] = "networks"

            current_center = centers[0]
            total_centers = len(centers)

            centers_display = ", ".join([f"`{c}`" for c in centers])
            confirmation = f"✅ `{corporation}` 구성도를 만들어드리겠습니다!\n\n📋 총 {len(centers)}개 센터: {centers_display}\n\n먼저 `{current_center}`부터 시작하겠습니다."

            ui = _ui_payload(
                title=f"{corporation} 구성도",
                subtitle="센터별 네트워크 영역을 수집합니다",
                step="networks",
                progress=(1, total_centers),
                summary={
                    "corporation": corporation,
                    "centers": centers,
                    "center_networks": state.get("center_networks", {}),
                },
                target={"center": current_center},
                extracted={
                    "confirmed": True,
                    "corporations": corporations,
                    "centers": centers,
                },
                examples=["내부망, DMZ망, 외부망", "내부망만", "지점망, 사용자망"],
                actions=["back", "summary"],
                helper="지금은 '네트워크 영역'만 입력받습니다. 장비는 다음 단계에서 확장 가능합니다.",
            )

            response = _bubble(
                question=f"{confirmation}\n\n어떤 네트워크 영역들이 있나요?",
                examples=["내부망, DMZ망, 외부망", "내부망만"],
                hint="키워드 기반으로 인식합니다. (내부망/DMZ망/외부망/지점망/사용자망)",
            )

            return {"response": response, "next_step": "networks", "ui_data": ui}

        elif any(k in msg_lower for k in reject_keywords):
            # 거부 - pending 제거하고 다시 입력 요청
            state.pop("pending_confirmation", None)

            ui = _ui_payload(
                title="법인/센터 입력",
                subtitle="다시 입력해주세요",
                step="corp-center",
                progress=(1, 1),
                summary={},
                target={},
                extracted={"rejected": True},
                examples=[
                    "은행 의왕센터와 AWS 구성도 만들어줘",
                    "중앙회 안성센터 구성도",
                ],
                actions=["summary"],
                helper="법인(은행/중앙회 등)과 센터(의왕/AWS/안성 등)를 포함해 주세요.",
            )

            response = _bubble(
                question="알겠습니다. 법인과 센터를 다시 입력해주세요.",
                examples=[
                    "은행 의왕센터와 AWS 구성도 만들어줘",
                    "중앙회 안성센터 구성도",
                ],
                hint="예시처럼 '법인 + 센터'가 같이 들어가면 인식이 안정적입니다.",
            )

            return {"response": response, "next_step": "corp-center", "ui_data": ui}

    # 매칭 결과 추출
    corporations = fuzzy_matcher.get_best_matches(
        match_result.corporations, min_confidence=fuzzy_matcher.CONFIDENCE_ASK
    )
    centers = fuzzy_matcher.get_best_matches(
        match_result.centers, min_confidence=fuzzy_matcher.CONFIDENCE_ASK
    )

    centers = _sort_centers_preferred(centers)

    extracted = {
        "message": message,
        "corporations_found": corporations,
        "centers_found": centers,
        "match_details": {
            "corporations": [
                {"matched": m.matched, "confidence": m.confidence, "type": m.match_type}
                for m in match_result.corporations
            ],
            "centers": [
                {"matched": m.matched, "confidence": m.confidence, "type": m.match_type}
                for m in match_result.centers
            ],
        },
        "needs_confirmation": match_result.needs_confirmation,
    }

    # 실패: 아무것도 못 찾음
    if not corporations and not centers:
        status = _format_status_block(
            step_label="법인/센터 입력", corporation=None, centers=[]
        )
        ui = _ui_payload(
            title="법인/센터 입력",
            subtitle="추출 실패",
            step="corp-center",
            progress=(1, 1),
            summary={},
            target={},
            extracted=extracted,
            examples=["은행 의왕센터와 AWS 구성도 만들어줘", "중앙회 안성센터 구성도"],
            actions=["summary"],
            helper="법인(은행/중앙회 등)과 센터(의왕/AWS/안성 등)를 포함해 주세요.",
        )
        response = _bubble(
            question="법인/센터 정보를 찾지 못했어요. 다시 입력해주세요.",
            examples=["은행 의왕센터와 AWS 구성도 만들어줘", "중앙회 안성센터 구성도"],
            hint="예시처럼 '법인 + 센터'가 같이 들어가면 인식이 안정적입니다.",
        )
        return {"response": response, "next_step": "corp-center", "ui_data": ui}

    # 케이스: 두 개 이상 애매함 → 전체 재입력 요청
    if match_result.confirmation_message == "multiple_uncertain":
        ui = _ui_payload(
            title="법인/센터 입력",
            subtitle="입력 내용이 불명확합니다",
            step="corp-center",
            progress=(1, 1),
            summary={},
            target={},
            extracted=extracted,
            examples=["은행 의왕센터와 AWS 구성도 만들어줘", "중앙회 안성센터 구성도"],
            actions=["summary"],
            helper="법인과 센터를 명확하게 입력해 주세요.",
        )
        response = _bubble(
            question="입력하신 내용을 정확히 인식하지 못했어요.\n법인과 센터를 다시 명확하게 입력해주세요.",
            examples=["은행 의왕센터와 AWS 구성도", "중앙회 안성센터 구성도"],
            hint="오타가 있거나 알 수 없는 단어가 포함되어 있을 수 있습니다.",
        )
        return {"response": response, "next_step": "corp-center", "ui_data": ui}

    # 확인 필요: Confidence가 애매한 경우 (하나만)
    if match_result.needs_confirmation:
        # pending 상태 저장
        state["pending_confirmation"] = {
            "corporations": corporations,
            "centers": centers,
            "message": message,
        }

        ui = _ui_payload(
            title="법인/센터 확인",
            subtitle="입력 내용을 확인해주세요",
            step="corp-center",
            progress=(1, 1),
            summary={},
            target={},
            extracted=extracted,
            examples=["확인", "네", "아니요", "다시"],
            actions=["summary"],
            helper="'확인' 또는 '네'를 입력하면 진행됩니다.",
        )

        response = _bubble(
            question=match_result.confirmation_message,
            examples=["확인", "네", "아니요"],
            hint="정확하지 않으면 다시 입력해 주세요.",
            show_back_hint=False,
        )

        return {"response": response, "next_step": "corp-center", "ui_data": ui}

    # 법인이 없으면 재입력 요청 (기본법인 사용 안 함)
    if not corporations:
        ui = _ui_payload(
            title="법인/센터 입력",
            subtitle="법인 정보가 필요합니다",
            step="corp-center",
            progress=(1, 1),
            summary={},
            target={},
            extracted=extracted,
            examples=["은행 의왕센터와 AWS 구성도", "중앙회 안성센터 구성도"],
            actions=["summary"],
            helper="법인(은행/중앙회 등)을 반드시 포함해 주세요.",
        )
        response = _bubble(
            question="법인 정보를 찾지 못했어요. 법인명을 포함해서 다시 입력해주세요.",
            examples=["은행 의왕센터와 AWS 구성도", "중앙회 안성센터 구성도"],
            hint="법인: 은행, 중앙회, 농협, 신협, 카드, 증권, 보험 등",
        )
        return {"response": response, "next_step": "corp-center", "ui_data": ui}

    # 센터가 없으면 재입력 요청
    if not centers:
        ui = _ui_payload(
            title="법인/센터 입력",
            subtitle="센터 정보가 필요합니다",
            step="corp-center",
            progress=(1, 1),
            summary={},
            target={},
            extracted=extracted,
            examples=["은행 의왕센터와 AWS 구성도", "중앙회 안성센터 구성도"],
            actions=["summary"],
            helper="센터(의왕/AWS/안성 등)를 반드시 포함해 주세요.",
        )
        response = _bubble(
            question="센터 정보를 찾지 못했어요. 센터명을 포함해서 다시 입력해주세요.",
            examples=["은행 의왕센터와 AWS 구성도", "중앙회 안성센터 구성도"],
            hint="센터: 의왕, 안성, AWS, IDC 등",
        )
        return {"response": response, "next_step": "corp-center", "ui_data": ui}

    corporation = corporations[0]

    # 상태 업데이트
    state["corporation"] = {"name": corporation}
    state["centers"] = centers
    state["current_center_index"] = 0
    state["center_networks"] = state.get(
        "center_networks", {}
    )  # 기존 입력이 있으면 유지
    state["next_step"] = "networks"

    current_center = centers[0]
    total_centers = len(centers)

    status = _format_status_block(
        step_label="센터별 네트워크 입력",
        corporation=corporation,
        centers=centers,
        current_center=current_center,
        center_index=0,
        center_total=total_centers,
        center_networks=state.get("center_networks", {}),
    )

    ui = _ui_payload(
        title=f"{corporation} 구성도",
        subtitle="센터별 네트워크 영역을 수집합니다",
        step="networks",
        progress=(1, total_centers),
        summary={
            "corporation": corporation,
            "centers": centers,
            "center_networks": state.get("center_networks", {}),
        },
        target={"center": current_center},
        extracted=extracted,
        examples=["내부망, DMZ망, 외부망", "내부망만", "지점망, 사용자망"],
        actions=["back", "summary"],
        helper="지금은 '네트워크 영역'만 입력받습니다. 장비는 다음 단계에서 확장 가능합니다.",
    )

    # 확인 메시지 생성
    centers_display = ", ".join([f"`{c}`" for c in centers])
    confirmation = f"✅ `{corporation}` 구성도를 만들어드리겠습니다!\n\n📋 총 {len(centers)}개 센터: {centers_display}\n\n먼저 `{current_center}`부터 시작하겠습니다."

    response = _bubble(
        question=f"{confirmation}\n\n어떤 네트워크 영역들이 있나요?",
        examples=["내부망, DMZ망, 외부망", "내부망만"],
        hint="키워드 기반으로 인식합니다. (내부망/DMZ망/외부망/지점망/사용자망)",
    )

    return {"response": response, "next_step": "networks", "ui_data": ui}


# =========================================================
# 6) Step: networks (센터별 순차)
# =========================================================
def _step_networks(state: GraphState, message: str, extractor) -> Dict[str, Any]:
    centers: List[str] = _ensure_list(state.get("centers"))
    corp = (state.get("corporation") or {}).get("name")
    center_networks: dict = state.get("center_networks", {})
    idx: int = int(state.get("current_center_index", 0) or 0)

    if not centers:
        # 안전장치
        state["next_step"] = "corp-center"
        status = _format_status_block(
            step_label="법인/센터 필요", corporation=corp, centers=[]
        )
        ui = _ui_payload(
            title="법인/센터 필요",
            subtitle="센터가 없습니다",
            step="corp-center",
            progress=(1, 1),
            summary={},
            target={},
            extracted={"message": message},
            examples=["은행 의왕센터와 AWS 구성도"],
            actions=["summary"],
        )
        response = _bubble(
            question="센터 정보가 없어요. 법인/센터부터 다시 입력해주세요.",
            examples=["은행 의왕센터와 AWS 구성도"],
        )
        return {"response": response, "next_step": "corp-center", "ui_data": ui}

    if idx >= len(centers):
        return _finalize_networks(state)

    current_center = centers[idx]

    # 키워드 인식 (표준화된 zone label로 저장)
    zone_map = {
        "내부망": ["내부망", "업무망"],
        "DMZ망": ["dmz", "dmz망", "디엠지", "대외dmz"],
        "외부망": ["외부망", "대외망", "인터넷망", "인터넷", "외부"],
        "지점망": ["지점망", "영업점망", "점포망"],
        "사용자망": ["사용자망", "유저망"],
    }

    found: List[str] = []
    lower = message.lower()
    for label, keys in zone_map.items():
        for k in keys:
            if k.lower() in lower:
                found.append(label)
                break
    found = _dedupe_keep_order(found)

    extracted = {
        "message": message,
        "center": current_center,
        "zones_found": found,
        "index": idx,
        "total": len(centers),
    }

    if not found:
        status = _format_status_block(
            step_label="네트워크 영역 입력",
            corporation=corp,
            centers=centers,
            current_center=current_center,
            center_index=idx,
            center_total=len(centers),
            center_networks=center_networks,
        )
        ui = _ui_payload(
            title="네트워크 영역 입력",
            subtitle=f"{current_center} 센터",
            step="networks",
            progress=(idx + 1, len(centers)),
            summary={
                "corporation": corp,
                "centers": centers,
                "center_networks": center_networks,
            },
            target={"center": current_center},
            extracted=extracted,
            examples=["내부망, DMZ망", "내부망만", "지점망, 사용자망"],
            actions=["back", "summary"],
            helper="인식 키워드: 내부망/DMZ망/외부망/지점망/사용자망",
        )
        response = _bubble(
            question=f"`{current_center}` 센터의 네트워크 영역을 인식하지 못했어요. 다시 입력해주세요.",
            examples=["내부망, DMZ망", "내부망만"],
            hint="예시처럼 키워드를 포함해서 입력해 주세요.",
        )
        return {"response": response, "next_step": "networks", "ui_data": ui}

    # 저장: zones는 리스트로 유지(후처리/표시 쉬움)
    center_networks[current_center] = {
        "zones": found,
        "devices": center_networks.get(current_center, {}).get("devices", []),
    }
    state["center_networks"] = center_networks

    # 방금 입력한 센터 확인 메시지
    zones_display = ", ".join([f"`{z}`" for z in found])
    confirmation = f"✅ `{current_center}` 센터: {zones_display} 저장 완료!"

    # 다음 센터로 이동
    next_idx = idx + 1
    state["current_center_index"] = next_idx

    # 디버깅: 상태 확인
    print(
        f"DEBUG: current_center={current_center}, idx={idx}, next_idx={next_idx}, len(centers)={len(centers)}"
    )
    print(f"DEBUG: centers={centers}")
    print(f"DEBUG: center_networks keys={list(center_networks.keys())}")

    if next_idx < len(centers):
        next_center = centers[next_idx]
        confirmation += (
            f"\n\n다음은 `{next_center}` 센터입니다. ({next_idx + 1}/{len(centers)})"
        )

        status = _format_status_block(
            step_label="네트워크 영역 입력",
            corporation=corp,
            centers=centers,
            current_center=next_center,
            center_index=next_idx,
            center_total=len(centers),
            center_networks=center_networks,
        )
        ui = _ui_payload(
            title="네트워크 영역 입력",
            subtitle="센터별로 순차 진행",
            step="networks",
            progress=(next_idx + 1, len(centers)),
            summary={
                "corporation": corp,
                "centers": centers,
                "center_networks": center_networks,
            },
            target={"center": next_center},
            extracted=extracted,
            examples=["내부망, DMZ망, 외부망", "내부망만"],
            actions=["back", "summary"],
        )
        response = _bubble(
            question=f"{confirmation}\n\n어떤 네트워크 영역들이 있나요?",
            examples=["내부망, DMZ망, 외부망", "내부망만"],
        )
        print(f"DEBUG: Returning next_step=networks for next_center={next_center}")
        return {"response": response, "next_step": "networks", "ui_data": ui}

    # 마지막 센터 완료 - finalize로 넘어가기 전에 확인 메시지 포함
    print(f"DEBUG: All centers done, calling _finalize_networks")
    return _finalize_networks(state, last_center=current_center, last_zones=found)


def _finalize_networks(
    state: GraphState,
    last_center: Optional[str] = None,
    last_zones: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    center_networks -> step_networks payload 구성 후, pending_scopes 생성.
    """
    corp = (state.get("corporation") or {}).get("name")
    centers: List[str] = _ensure_list(state.get("centers"))
    center_networks: dict = state.get("center_networks", {})

    # step_networks가 문자열을 기대할 수 있어 join 처리
    center_zones: Dict[str, str] = {}
    center_devices: Dict[str, str] = {}
    for c, info in center_networks.items():
        zones = info.get("zones", [])
        if isinstance(zones, list):
            center_zones[c] = ", ".join(zones)
        else:
            center_zones[c] = str(zones)
        devs = info.get("devices", [])
        if isinstance(devs, list):
            center_devices[c] = ", ".join(devs)
        else:
            center_devices[c] = str(devs)

    from app.nodes.step_networks import step_networks

    state["networks_payload"] = {
        "center_zones": center_zones,
        "center_devices": center_devices,
        "external_networks": [],
    }

    updated = step_networks(state)
    pending = updated.get("pending_scopes", [])

    extracted = {
        "networks_payload": state.get("networks_payload"),
        "pending_scopes_count": len(pending),
    }

    if not pending:
        status = _format_status_block(
            step_label="네트워크 완료(오류)",
            corporation=corp,
            centers=centers,
            center_networks=center_networks,
        )
        ui = _ui_payload(
            title="스코프 생성 실패",
            subtitle="네트워크 정보로 스코프를 만들 수 없습니다",
            step="networks",
            progress=(1, 1),
            summary={"center_networks": center_networks},
            target={},
            extracted=extracted,
            examples=["다시", "요약"],
            actions=["back", "summary"],
            helper="센터별 네트워크 영역 입력이 정상인지 확인해주세요.",
        )
        response = _bubble(
            question="스코프를 생성할 수 없습니다. 네트워크 입력을 다시 확인해주세요.",
            examples=["(예) 의왕: 내부망, DMZ망", "(예) AWS: 외부망"],
        )
        return {"response": response, "next_step": "networks", "ui_data": ui}

    # 첫 스코프 지정
    from app.nodes.step_next_scope import step_next_scope

    updated = step_next_scope(updated)
    current_scope = updated.get("current_scope")
    remaining = len(updated.get("pending_scopes", []))
    total_scopes = remaining + 1

    # state 반영
    state.update(updated)
    state["next_step"] = "scope-detail"

    # 마지막 센터 확인 메시지 (있는 경우)
    last_center_msg = ""
    if last_center and last_zones:
        zones_display = ", ".join([f"`{z}`" for z in last_zones])
        last_center_msg = f"✅ `{last_center}` 센터: {zones_display} 저장 완료!\n\n"

    # 네트워크 입력 완료 요약
    network_summary_lines = []
    for c, info in center_networks.items():
        zones = info.get("zones", [])
        if isinstance(zones, list):
            zones_str = ", ".join([f"`{z}`" for z in zones])
        else:
            zones_str = str(zones)
        network_summary_lines.append(f"  • `{c}`: {zones_str}")

    network_summary = "\n".join(network_summary_lines)
    confirmation = f"{last_center_msg}✅ 네트워크 입력 완료!\n\n📋 입력된 네트워크 구성:\n{network_summary}\n\n이제 각 영역의 상세 정보를 입력받겠습니다."

    status = _format_status_block(
        step_label="영역 상세 입력",
        corporation=corp,
        centers=centers,
        center_networks=center_networks,
    )
    ui = _ui_payload(
        title="네트워크 입력 완료",
        subtitle="이제 영역별 상세 정보를 수집합니다",
        step="scope-detail",
        progress=(1, total_scopes),
        summary={
            "network_summary": [
                {"center": c, "zones": info.get("zones", [])}
                for c, info in center_networks.items()
            ]
        },
        target={"scope": current_scope},
        extracted=extracted,
        examples=["서버: nbefapp01, nbefapp02", "DB: orclprod", "장비: IRT 라우터"],
        actions=["back", "summary"],
        helper="여기서는 '해당 영역에 존재하는 시스템/장비'를 자유롭게 적어주세요.",
    )
    response = _bubble(
        question=f"{confirmation}\n\n먼저 `{(current_scope or {}).get('display', '현재 영역')}`에는 어떤 시스템들이 있나요?",
        examples=["서버: nbefapp01, nbefapp02", "DB: orclprod", "장비: IRT 라우터"],
    )
    return {"response": response, "next_step": "scope-detail", "ui_data": ui}


# =========================================================
# 7) Step: scope-detail
# =========================================================
def _step_scope_detail(state: GraphState, message: str, extractor) -> Dict[str, Any]:
    corp = (state.get("corporation") or {}).get("name")
    centers: List[str] = _ensure_list(state.get("centers"))
    center_networks: dict = state.get("center_networks", {})

    current_scope = state.get("current_scope")
    if not current_scope:
        from app.nodes.step_next_scope import step_next_scope

        updated = step_next_scope(state)
        current_scope = updated.get("current_scope")
        if not current_scope:
            state["next_step"] = "edges"
            status = _format_status_block(
                step_label="연결관계 입력",
                corporation=corp,
                centers=centers,
                center_networks=center_networks,
            )
            ui = _ui_payload(
                title="영역 입력 완료",
                subtitle="이제 연결관계로 이동",
                step="edges",
                progress=(1, 1),
                summary={"scope_details": state.get("scope_details", {})},
                target={},
                extracted={"message": message},
                examples=["A는 B와 통신", "IGW ↔ API_GW", "서버 → DBMS"],
                actions=["back", "summary"],
            )
            response = _bubble(
                question="모든 영역 입력이 끝났어요. 이제 시스템 간 연결 관계를 입력해주세요.",
                examples=["IGW ↔ API_GW", "서버 → DBMS"],
            )
            return {"response": response, "next_step": "edges", "ui_data": ui}

    # step_scope_detail 실행
    state["scope_detail_text"] = message
    from app.nodes.step_scope_detail import step_scope_detail

    updated = step_scope_detail(state)

    extracted = {
        "scope": current_scope.get("display"),
        "message": message,
        "scope_details_keys": list((updated.get("scope_details") or {}).keys()),
    }

    # 다음 스코프
    from app.nodes.step_next_scope import step_next_scope

    updated = step_next_scope(updated)
    next_scope = updated.get("current_scope")
    remaining = len(updated.get("pending_scopes", []))

    state.update(updated)

    if next_scope:
        total = remaining + 1 + 1  # next + current 포함 느낌으로 표시
        done_idx = total - (remaining + 1)

        status = _format_status_block(
            step_label="영역 상세 입력",
            corporation=corp,
            centers=centers,
            center_networks=center_networks,
        )
        ui = _ui_payload(
            title="영역 상세 입력",
            subtitle="다음 영역으로 진행",
            step="scope-detail",
            progress=(done_idx + 1, done_idx + remaining + 1),
            summary={"completed_scope": current_scope, "remaining": remaining},
            target={"scope": next_scope},
            extracted=extracted,
            examples=["서버: nbefapp01", "DB: orclprod", "인터페이스: IGW"],
            actions=["back", "summary"],
        )
        response = _bubble(
            question=f"저장 완료. 다음은 `{next_scope.get('display')}` 입니다. 이 영역의 시스템을 입력해주세요.",
            examples=["서버: nbefapp01", "DB: orclprod", "인터페이스: IGW"],
        )
        return {"response": response, "next_step": "scope-detail", "ui_data": ui}

    # 마지막이면 edges로
    state["next_step"] = "edges"
    status = _format_status_block(
        step_label="연결관계 입력",
        corporation=corp,
        centers=centers,
        center_networks=center_networks,
    )
    ui = _ui_payload(
        title="영역 상세 입력 완료",
        subtitle="이제 연결관계를 입력합니다",
        step="edges",
        progress=(1, 1),
        summary={"scope_details": state.get("scope_details", {})},
        target={},
        extracted=extracted,
        examples=["IGW ↔ API_GW", "서버 → DBMS", "외부시스템 ↔ 내부시스템"],
        actions=["back", "summary"],
    )
    response = _bubble(
        question="모든 영역 입력이 끝났어요. 이제 시스템 간 연결 관계를 입력해주세요.",
        examples=["IGW ↔ API_GW", "서버 → DBMS"],
    )
    return {"response": response, "next_step": "edges", "ui_data": ui}


# =========================================================
# 8) Step: edges
# =========================================================
def _step_edges(state: GraphState, message: str, extractor) -> Dict[str, Any]:
    corp = (state.get("corporation") or {}).get("name")
    centers: List[str] = _ensure_list(state.get("centers"))
    center_networks: dict = state.get("center_networks", {})

    state["edge_text"] = message
    from app.nodes.step_edges import step_edges

    updated = step_edges(state)
    state.update(updated)
    state["next_step"] = "done"

    extracted = {
        "message": message,
        "edges_keys": list((updated.get("edges") or {}).keys())
        if isinstance(updated.get("edges"), dict)
        else None,
    }

    status = _format_status_block(
        step_label="완료",
        corporation=corp,
        centers=centers,
        center_networks=center_networks,
    )
    ui = _ui_payload(
        title="구성도 완성",
        subtitle="처리가 완료되었습니다",
        step="done",
        progress=(1, 1),
        summary={
            "corporation": corp,
            "centers": centers,
            "center_networks": center_networks,
        },
        target={},
        extracted=extracted,
        examples=["요약", "다시"],
        actions=["summary", "reset"],
        helper="처음부터 다시 하려면 '다시'를 입력하세요. (기록은 유지됩니다)",
    )
    response = _bubble(
        question="구성도 생성이 완료되었습니다. 결과 화면에서 확인해 주세요.",
        examples=["요약", "다시"],
    )
    return {"response": response, "next_step": "done", "ui_data": ui}
