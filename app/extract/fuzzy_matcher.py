# app/extract/fuzzy_matcher.py
"""
rapidfuzz 기반 엔티티 매칭 시스템
- 후보 공간 고정 (Corporation, Center)
- 문자열 유사도로 오타/변형 흡수
- Confidence 기준으로 자동/확인 분기
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

try:
    from rapidfuzz import fuzz, process

    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    print("Warning: rapidfuzz not installed. Falling back to exact matching.")


@dataclass
class MatchResult:
    """매칭 결과"""

    matched: str  # 매칭된 후보
    original: str  # 원본 입력
    confidence: float  # 신뢰도 (0.0 ~ 1.0)
    match_type: str  # "exact", "fuzzy", "none"


@dataclass
class EntityMatchResult:
    """엔티티 매칭 전체 결과"""

    corporations: List[MatchResult]
    centers: List[MatchResult]
    needs_confirmation: bool  # 사용자 확인 필요 여부
    confirmation_message: Optional[str]  # 확인 메시지


class FuzzyEntityMatcher:
    """
    후보 공간 기반 Fuzzy 매칭

    Confidence 기준:
    - 0.85 이상: 자동 승인 (확실함)
    - 0.60 ~ 0.85: 사용자 확인 필요 (애매함)
    - 0.60 미만: 매칭 실패
    """

    # 후보 공간 (프로젝트별로 확장 가능)
    CORPORATION_CANDIDATES = [
        "은행",
        "중앙회",
        "농협",
        "신협",
        "카드",
        "증권",
        "보험",
        "캐피탈",
        "저축은행",
    ]

    CENTER_CANDIDATES = [
        "의왕",
        "안성",
        "AWS",
        "IDC",
        "본점",
        "지점",
    ]

    # Confidence 임계값
    CONFIDENCE_AUTO = 0.85  # 이상이면 자동 승인
    CONFIDENCE_ASK = 0.60  # 이상이면 확인 요청

    def __init__(self):
        self.use_rapidfuzz = RAPIDFUZZ_AVAILABLE

    def match_text(
        self, text: str, candidates: List[str], threshold: float = 0.60
    ) -> Optional[MatchResult]:
        """
        텍스트를 후보 리스트와 매칭

        Args:
            text: 입력 텍스트
            candidates: 후보 리스트
            threshold: 최소 신뢰도

        Returns:
            MatchResult 또는 None
        """
        if not text or not candidates:
            return None

        text_clean = text.strip()

        # 1. 정확한 매칭 시도
        for candidate in candidates:
            if text_clean == candidate or candidate in text_clean:
                return MatchResult(
                    matched=candidate, original=text, confidence=1.0, match_type="exact"
                )

        # 2. Fuzzy 매칭
        if self.use_rapidfuzz:
            # WRatio: 부분 문자열 매칭에 강함
            result = process.extractOne(text_clean, candidates, scorer=fuzz.WRatio)

            if result:
                matched_text, score, _ = result
                confidence = score / 100.0  # 0~100을 0~1로 정규화

                if confidence >= threshold:
                    return MatchResult(
                        matched=matched_text,
                        original=text,
                        confidence=confidence,
                        match_type="fuzzy",
                    )
        else:
            # rapidfuzz 없으면 간단한 포함 검사
            for candidate in candidates:
                if candidate.lower() in text_clean.lower():
                    return MatchResult(
                        matched=candidate,
                        original=text,
                        confidence=0.8,
                        match_type="fuzzy",
                    )

        return None

    def extract_corporations(self, text: str) -> List[MatchResult]:
        """법인 추출"""
        results = []

        for candidate in self.CORPORATION_CANDIDATES:
            if candidate in text:
                match = self.match_text(candidate, [candidate])
                if match:
                    results.append(match)

        # 중복 제거
        seen = set()
        unique_results = []
        for r in results:
            if r.matched not in seen:
                seen.add(r.matched)
                unique_results.append(r)

        return unique_results

    def extract_centers(self, text: str) -> List[MatchResult]:
        """센터 추출 (우선순위 + 패턴 + Fuzzy)"""
        import re

        results = []

        # 1. 우선순위 키워드 정확 매칭
        for candidate in self.CENTER_CANDIDATES:
            if candidate in text:
                results.append(
                    MatchResult(
                        matched=candidate,
                        original=candidate,
                        confidence=1.0,
                        match_type="exact",
                    )
                )

        # 2. 패턴 매칭 (센터/지점/본점)
        patterns = [
            r"([가-힣A-Za-z0-9]+)센터",
            r"([가-힣A-Za-z0-9]+)지점",
            r"([가-힣A-Za-z0-9]+)본점",
        ]

        for pat in patterns:
            for m in re.finditer(pat, text):
                name = m.group(1)
                if name and name != "센터" and len(name) >= 2:
                    # Fuzzy 매칭 시도
                    match = self.match_text(name, self.CENTER_CANDIDATES)
                    if match:
                        results.append(match)
                    else:
                        # 후보에 없으면 그대로 추가 (낮은 confidence)
                        results.append(
                            MatchResult(
                                matched=name,
                                original=name,
                                confidence=0.7,
                                match_type="pattern",
                            )
                        )

        # 3. 대문자 영어 (AWS, IDC 등)
        english_caps = re.findall(r"\b[A-Z]{2,}\b", text)
        for cap in english_caps:
            match = self.match_text(cap, self.CENTER_CANDIDATES)
            if match:
                results.append(match)
            else:
                results.append(
                    MatchResult(
                        matched=cap, original=cap, confidence=0.8, match_type="pattern"
                    )
                )

        # 중복 제거
        seen = set()
        unique_results = []
        for r in results:
            if r.matched not in seen:
                seen.add(r.matched)
                unique_results.append(r)

        return unique_results

    def match_entities(self, text: str) -> EntityMatchResult:
        """
        텍스트에서 법인/센터 추출 + Confidence 기반 확인 필요 여부 판단

        로직:
        - 두 개 이상 애매함 → 전체 재입력 요청
        - 하나만 애매함 → 그것만 확인 요청
        - 법인도 오타면 확인 요청 (기본법인 X)

        Returns:
            EntityMatchResult (needs_confirmation=True면 사용자 확인 필요)
        """
        corporations = self.extract_corporations(text)
        centers = self.extract_centers(text)

        # 애매한 항목들 찾기
        uncertain_corps = [
            c
            for c in corporations
            if self.CONFIDENCE_ASK <= c.confidence < self.CONFIDENCE_AUTO
        ]
        uncertain_centers = [
            c
            for c in centers
            if self.CONFIDENCE_ASK <= c.confidence < self.CONFIDENCE_AUTO
        ]

        total_uncertain = len(uncertain_corps) + len(uncertain_centers)

        # 케이스 1: 두 개 이상 애매함 → 전체 재입력 요청
        if total_uncertain >= 2:
            return EntityMatchResult(
                corporations=corporations,
                centers=centers,
                needs_confirmation=False,  # 확인이 아니라 재입력
                confirmation_message="multiple_uncertain",  # 특수 플래그
            )

        # 케이스 2: 하나만 애매함 → 확인 요청
        if total_uncertain == 1:
            if uncertain_corps:
                entity = uncertain_corps[0]
                entity_type = "법인"
            else:
                entity = uncertain_centers[0]
                entity_type = "센터"

            confirmation_message = (
                f"혹시 '{entity_type}: {entity.matched}' 를 의미하신 걸까요?\n"
                f"맞다면 '확인' 또는 '네'를 입력해 주세요.\n"
                f"아니면 다시 입력해 주세요."
            )

            return EntityMatchResult(
                corporations=corporations,
                centers=centers,
                needs_confirmation=True,
                confirmation_message=confirmation_message,
            )

        # 케이스 3: 모두 확실함 → 바로 진행
        return EntityMatchResult(
            corporations=corporations,
            centers=centers,
            needs_confirmation=False,
            confirmation_message=None,
        )

    def get_best_matches(
        self, results: List[MatchResult], min_confidence: float = 0.60
    ) -> List[str]:
        """
        신뢰도 기준 이상인 매칭 결과만 반환

        Args:
            results: 매칭 결과 리스트
            min_confidence: 최소 신뢰도

        Returns:
            매칭된 엔티티 이름 리스트
        """
        return [r.matched for r in results if r.confidence >= min_confidence]


# 싱글톤 인스턴스
fuzzy_matcher = FuzzyEntityMatcher()
