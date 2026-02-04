from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class Candidate:
    text: str
    type: str
    span: Tuple[int, int]
    context: str
    normalized: Optional[str] = None


class CandidateExtractor:
    def __init__(self, *, context_chars: int = 60, context_max: int = 200):
        self.context_chars = context_chars
        self.context_max = context_max

        self.re_name = re.compile(r"\b[A-Za-z][A-Za-z0-9_-]{3,}\b")

        self.corporation_allow = ["은행", "중앙회"]
        self.center_allow = ["의왕", "안성", "AWS"]
        self.corporation_patterns = self._build_ko_ascii_token_patterns(
            self.corporation_allow, allow_suffix=None, case_insensitive=True
        )

        self.center_patterns = self._build_ko_ascii_token_patterns(
            self.center_allow, allow_suffix=None, case_insensitive=True
        )

        self.engine_map = {
            "postgres": ["pg"],
            "oracle": ["orcl"],
            "mysql": [],
            "mssql": ["sqlserver"],
            "tibero": [],
        }

        self.dbms_role_map = {
            "GoldCopy": ["goldcopy", "gold copy", "standby", "replica"],
            "backup": ["backup", "백업"],
            "batch": ["batch", "배치"],
        }

        self.zone_map = {
            "internal": ["내부망", "업무망"],
            "dmz": [],
            "internal_sdn": ["내부sdn", "내부 sdn", "sdn망", "내부SDN망"],
            "external": ["대외망", "외부망", "인터넷망", "대외", "DMZ망"],
            "user": ["사용자망", "유저망"],
            "branch": ["영업점망", "지점망"],
        }

        self.server_class = ["AP", "WEB", "WAS", "DB", "ETL"]
        self.server_type = ["IaaS", "PaaS", "베어메탈", "BareMetal"]
        self.state = ["Active", "Standby", "ACTIVE", "STANDBY"]
        self.workload = ["발급공통", "CA", "인증", "계정계", "카드"]

        self.interface_map = {
            "MFT": [],
            "FOS": [],
            "EAI": [],
            "IGW": ["internal gw", "internal gateway"],
            "NGW": [],
            "API_GW": ["api gateway", "api g/w"],
            "MCA": ["mca"],
        }

        self.isp_short_tokens = ["sk", "kt", "lg"]

        self.re_line_context = re.compile(
            r"(회선|전용회선|대외회선|망연계|mpls|vpn|인터넷구간|대외|회선사|isp|line|라인|브로드밴드|데이콤|텔레콤|통신)",
            re.IGNORECASE,
        )

        self.device_type_map = {
            "GSLB": ["gslb"],
            "Firewall": ["firewall", "fw", "방화벽"],
            "Router": ["router", "rt", "라우터"],
            "Switch": ["switch", "sw", "스위치"],
            "Line": [
                "line",
                "라인",
                "회선",
                "전용회선",
                "망연계",
                "대외회선",
                "SK 브로드밴드",
                "LG 데이콤",
            ],
        }

        self.device_type_short_tokens = {
            "Router": ["rt"],
            "Switch": ["sw"],
        }

        self.device_subtype_map = {
            # 위치 / 경계
            "internal": ["internal", "내부", "사내"],
            "external": ["external", "외부"],
            # 네트워크 계층
            "L3": ["l3", "layer3", "레이어3"],
            "L4": ["l4", "layer4", "레이어4"],
            # 조직/용도 기반 Router 분류
            "IRT": ["irt", "irt router", "irt-router"],
            "ISW": ["isw", "isw router", "isw-router"],
        }

        self.re_device_anchor = re.compile(
            r"(gslb|firewall|fw|router|rt|switch|sw|방화벽|라우터|스위치|회선|line|라인)",
            re.IGNORECASE,
        )

        self.engine_patterns = self._build_alias_patterns(self.engine_map)
        self.zone_patterns = self._build_alias_patterns(self.zone_map)
        self.interface_patterns = self._build_alias_patterns(self.interface_map)

        self.interface_patterns = [
            (c, p) for (c, p) in self.interface_patterns if c != "IGW"
        ]
        self.interface_patterns.append(("IGW", re.compile(r"\bigw\b", re.IGNORECASE)))

        # (추가) 너무 짧아서 _build_alias_patterns에서 제외되는 엔진 약어 예외 처리
        # - pg / orcl 같은 건 필요하니까 별도로 등록
        short_engine_alias = {
            "postgres": ["pg"],
            "oracle": ["orcl"],
        }
        for canon, shorts in short_engine_alias.items():
            for s in shorts:
                k = self._norm_key(s)  # 'pg', 'orcl'
                rx = self._flex_regex_from_key(k)
                self.engine_patterns.append(
                    (canon, re.compile(rf"\b{rx}\b", re.IGNORECASE))
                )

    def _norm_key(self, s: str) -> str:
        """
        판별용 정규화 키:
        - 소문자
        - 공백/구분자 제거
        - 괄호 제거 (의미 없는 괄호)
        """
        s = s.lower().strip()
        # 괄호는 판별에 방해되면 제거 (필요시 유지해도 됨)
        s = re.sub(r"[()\[\]{}]", "", s)
        # 공백/구분자 제거
        s = re.sub(r"[\s/_\-]+", "", s)
        return s

    def _flex_regex_from_key(self, key: str) -> str:
        """
        정규화된 key(예: 'apigw', 'sqlserver', '내부sdn망')를
        원문에서 잡기 위한 유연 regex로 변환:
        - 문자 사이에 공백/구분자 허용
        - 대소문자 무시(compile 시 IGNORECASE)
        """
        # key는 이미 norm_key로 정규화된 문자열을 가정
        # 문자 사이에 [\s/_\-]* 허용
        parts = [re.escape(ch) for ch in key]
        return r"".join(p + r"[\s/_\-]*" for p in parts).rstrip(r"[\s/_\-]*")

    def _token_boundary_wrap(self, token: str, *, allow_suffix: str | None) -> str:
        """
        한글/영문 토큰 경계를 잡는다.
        - 한글 토큰(의왕/안성/은행 등): 뒤에 조사/접미어(센터/으로/에서 등) 붙는 걸 허용
        - 대신 영문/숫자/_ 가 바로 붙는 이상 결합은 차단
        """
        left = r"(?<![0-9A-Za-z_가-힣])"

        # token이 '순수 한글'이면 right 완화(조사 완화)
        if re.fullmatch(r"[가-힣]+", token):
            right = r"(?![0-9A-Za-z_])"
        else:
            right = r"(?![0-9A-Za-z_가-힣])"

        core = re.escape(token)
        if allow_suffix:
            core = core + allow_suffix

        return left + core + right

    def _build_ko_ascii_token_patterns(
        self,
        tokens: list[str],
        *,
        allow_suffix: str | None = None,
        case_insensitive: bool = True,
    ) -> list[tuple[str, re.Pattern]]:
        flags = re.IGNORECASE if case_insensitive else 0
        out: list[tuple[str, re.Pattern]] = []
        for tok in tokens:
            rx = self._token_boundary_wrap(tok, allow_suffix=allow_suffix)
            out.append((tok, re.compile(rx, flags)))
        return out

    def _find_section_range(self, text: str, header: str) -> Optional[Tuple[int, int]]:
        """
        예: header='[센터]'
        해당 헤더부터 다음 '[...]' 헤더 직전까지 범위를 반환
        """
        start = text.find(header)
        if start == -1:
            return None

        m = re.search(r"\n\[[^\]]+\]", text[start + len(header) :])
        if m:
            end = start + len(header) + m.start()
        else:
            end = len(text)

        return (start, end)

    def _build_alias_patterns(
        self, canonical_to_variants: dict[str, list[str]]
    ) -> list[tuple[str, re.Pattern]]:
        """
        canonical -> variants 를 받아서,
        variants를 정규화한 key로 만들고, 이를 유연 regex로 컴파일해 반환
        """
        patterns: list[tuple[str, re.Pattern]] = []
        seen = set()

        for canon, variants in canonical_to_variants.items():
            # canonical 자체도 alias로 포함
            keys = {self._norm_key(canon)}
            for v in variants:
                keys.add(self._norm_key(v))

            for k in sorted(keys, key=len, reverse=True):  # 긴 것 우선
                if not k:
                    continue
                # 너무 짧은 alias는 오탐 위험 (예: 'pg', 'rt' 같은 건 별도 정책)
                # 여기서는 engine에 필요한 'pg/orcl'은 따로 허용하도록 아래에서 예외 처리 가능
                # 기본은 길이 3 이상만
                if len(k) < 3:
                    continue

                rx = self._flex_regex_from_key(k)
                sig = (canon, rx)
                if sig in seen:
                    continue
                seen.add(sig)

                patterns.append((canon, re.compile(rx, re.IGNORECASE)))
        return patterns

    def _prune_overlaps_longest(
        self,
        candidates: List[Candidate],
        *,
        types: set[str],
        normalized_allow: Optional[set[str]] = None,
    ) -> List[Candidate]:
        """
        같은 type(+normalized) 내에서 span이 겹치면 '더 긴 span'만 남긴다.
        - normalized_allow를 주면, 해당 normalized에만 적용
        (예: DeviceTypeHint 중 Line만 overlap 제거)
        """
        buckets: dict[tuple[str, Optional[str]], List[Candidate]] = {}
        others: List[Candidate] = []

        for c in candidates:
            if c.type in types and (
                normalized_allow is None or (c.normalized in normalized_allow)
            ):
                buckets.setdefault((c.type, c.normalized), []).append(c)
            else:
                others.append(c)

        kept: List[Candidate] = []
        for (t, norm), lst in buckets.items():
            # 길이 내림차순(긴 토큰 우선), 시작 오름차순
            lst_sorted = sorted(
                lst, key=lambda x: (-(x.span[1] - x.span[0]), x.span[0], x.span[1])
            )
            chosen: List[Candidate] = []
            for c in lst_sorted:
                s, e = c.span
                if any(
                    not (e <= s2 or e2 <= s) for (s2, e2) in (x.span for x in chosen)
                ):
                    continue
                chosen.append(c)
            kept.extend(chosen)

        return others + kept

    BOUNDARY_CHARS = set(" \t\r\n,.:;()[]{}<>/\\|-")

    def is_boundary(self, text: str, pos: int) -> bool:
        if pos <= 0 or pos >= len(text):
            return True
        return text[pos] in self.BOUNDARY_CHARS

    def _is_standalone_token(self, text: str, s: int, e: int) -> bool:
        def is_wordish(ch: str) -> bool:
            return bool(ch) and (ch.isalnum() or ("가" <= ch <= "힣"))

        prev_pos = s - 1
        next_pos = e

        # 앞/뒤가 boundary 이거나 단어 문자가 아니면 standalone
        prev_ok = self.is_boundary(text, prev_pos) or not is_wordish(text[prev_pos])
        next_ok = self.is_boundary(text, next_pos) or not is_wordish(text[next_pos])

        return prev_ok and next_ok

    def _has_device_anchor_near(
        self, text: str, s: int, e: int, window: int = 25
    ) -> bool:
        left = max(0, s - window)
        right = min(len(text), e + window)
        return bool(self.re_device_anchor.search(text[left:right]))

    def _has_line_context_near(
        self, text: str, s: int, e: int, window: int = 30
    ) -> bool:
        left = max(0, s - window)
        right = min(len(text), e + window)
        return bool(self.re_line_context.search(text[left:right]))

    def _context(self, text: str, s: int, e: int) -> str:
        left = max(0, s - self.context_chars)
        right = min(len(text), e + self.context_chars)
        ctx = text[left:right]
        return ctx[: self.context_max]  # 상한

    def extract(
        self, text: str, *, depth: int = 0, max_depth: int = 1
    ) -> List[Candidate]:
        out: List[Candidate] = []

        # A) NameCandidate
        for m in self.re_name.finditer(text):
            s, e = m.span()
            token = m.group(0)
            out.append(
                Candidate(
                    token,
                    type="NameCandidate",
                    span=(s, e),
                    context=self._context(text, s, e),
                )
            )

        for canon, pat in self.corporation_patterns:
            for m in pat.finditer(text):
                s, e = m.span()
                out.append(
                    Candidate(
                        text=text[s:e],
                        type="CorporationHint",
                        span=(s, e),
                        context=self._context(text, s, e),
                        normalized=canon,
                    )
                )

        lowered = text.lower()

        # A-2) CenterHint
        for canon, pat in self.center_patterns:
            for m in pat.finditer(text):
                s, e = m.span()
                out.append(
                    Candidate(
                        text=text[s:e],
                        type="CenterHint",
                        span=(s, e),
                        context=self._context(text, s, e),
                        normalized=canon,
                    )
                )

        # B) EngineHint - 정규화/유연매칭 기반
        for canon, pat in self.engine_patterns:
            for m in pat.finditer(text):
                s, e = m.span()
                out.append(
                    Candidate(
                        text=text[s:e],
                        type="EngineHint",
                        span=(s, e),
                        context=self._context(text, s, e),
                        normalized=canon,
                    )
                )

        # B-2) DBMSRoleHint - 모두 찾기
        for norm, variants in self.dbms_role_map.items():
            for v in variants:
                vv = v.lower()
                for m in re.finditer(re.escape(vv), lowered):
                    s, e = m.span()
                    out.append(
                        Candidate(
                            text=text[s:e],
                            type="DBMSRoleHint",
                            span=(s, e),
                            context=self._context(text, s, e),
                            normalized=norm,
                        )
                    )

        # C) ZoneHint - 정규화/유연매칭 기반
        for canon, pat in self.zone_patterns:
            for m in pat.finditer(text):
                s, e = m.span()
                out.append(
                    Candidate(
                        text=text[s:e],
                        type="ZoneHint",
                        span=(s, e),
                        context=self._context(text, s, e),
                        normalized=canon,
                    )
                )

        # C-2) InterfaceHint - 정규화/유연매칭 기반
        for canon, pat in self.interface_patterns:
            for m in pat.finditer(text):
                s, e = m.span()
                out.append(
                    Candidate(
                        text=text[s:e],
                        type="InterfaceHint",
                        span=(s, e),
                        context=self._context(text, s, e),
                        normalized=canon,
                    )
                )

        # --- Quoted block ---
        re_quoted = re.compile(r'"([^"\n]{1,120})"')

        for m in re_quoted.finditer(text):
            qs, qe = m.span()
            inner = m.group(1).strip()
            if len(inner) < 2:
                continue

            # 대표 이름 (통째)
            out.append(
                Candidate(
                    text=inner,
                    type="QuotedNameCandidate",
                    span=(qs + 1, qe - 1),
                    context=self._context(text, qs, qe),
                    normalized=None,
                )
            )

            if depth < max_depth:
                inner_candidates = self.extract(
                    inner,
                    depth=depth + 1,
                    max_depth=max_depth,
                )
            else:
                inner_candidates = []

            base = qs + 1
            for c in inner_candidates:
                # QuotedNameCandidate 재귀 금지
                if c.type == "QuotedNameCandidate":
                    continue

                out.append(
                    Candidate(
                        text=c.text,
                        type=c.type,
                        span=(base + c.span[0], base + c.span[1]),
                        context=self._context(text, base + c.span[0], base + c.span[1]),
                        normalized=c.normalized,
                    )
                )

        # C-3) DeviceTypeHint - 모두 찾기
        for norm, variants in self.device_type_map.items():
            for v in variants:
                vv = v.lower()

                if norm in {"Router", "Switch"} and vv in {"rt", "sw"}:
                    continue

                for m in re.finditer(re.escape(vv), lowered):
                    s, e = m.span()
                    out.append(
                        Candidate(
                            text=text[s:e],
                            type="DeviceTypeHint",
                            span=(s, e),
                            context=self._context(text, s, e),
                            normalized=norm,
                        )
                    )

        for norm, toks in self.device_type_short_tokens.items():
            for tok in toks:
                for m in re.finditer(rf"\b{re.escape(tok)}\b", lowered):
                    s, e = m.span()
                    out.append(
                        Candidate(
                            text=text[s:e],
                            type="DeviceTypeHint",
                            span=(s, e),
                            context=self._context(text, s, e),
                            normalized=norm,
                        )
                    )

        # C-3-b) ISP + Line 표현: "sk회선", "sk 라인", "sk line", "sk-회선" 등 변형 커버
        # - ISP 토큰 단독은 Line으로 만들지 않고, Line류 단서가 근처/결합된 경우만 허용
        for tok in self.isp_short_tokens:
            # 1) 붙어있는 결합형: sk회선 / sk라인 / skline / sk전용회선 ...
            for m in re.finditer(
                rf"{re.escape(tok)}\s*(회선|전용회선|대외회선|망연계|line|라인)",
                lowered,
            ):
                s, e = m.span()
                out.append(
                    Candidate(
                        text=text[s:e],
                        type="DeviceTypeHint",
                        span=(s, e),
                        context=self._context(text, s, e),
                        normalized="Line",
                    )
                )

            # 2) 분리형: "sk line", "sk 라인" 등 (sk 자체가 standalone이면서 line 컨텍스트 근처인 경우)
            for m in re.finditer(rf"\b{re.escape(tok)}\b", lowered):
                s, e = m.span()
                if not self._has_line_context_near(text, s, e, window=30):
                    continue
                out.append(
                    Candidate(
                        text=text[s:e],
                        type="DeviceTypeHint",
                        span=(s, e),
                        context=self._context(text, s, e),
                        normalized="Line",
                    )
                )

        # C-4) DeviceSubtypeHint - 모두 찾기
        for norm, variants in self.device_subtype_map.items():
            for v in variants:
                vv = v.lower()
                for m in re.finditer(re.escape(vv), lowered):
                    s, e = m.span()

                    # internal/external은 "장비 단서"가 근처에 있을 때만 허용
                    if not self._is_standalone_token(text, s, e):
                        continue

                    if norm in {"internal", "external"}:
                        if not self._has_device_anchor_near(text, s, e, window=25):
                            continue

                    out.append(
                        Candidate(
                            text=text[s:e],
                            type="DeviceSubtypeHint",
                            span=(s, e),
                            context=self._context(text, s, e),
                            normalized=norm,
                        )
                    )

        # D) enum hints
        for word in self.server_class:
            for m in re.finditer(rf"\b{re.escape(word)}\b", text):
                s, e = m.span()
                out.append(
                    Candidate(
                        word,
                        type="ServerClassHint",
                        span=(s, e),
                        context=self._context(text, s, e),
                        normalized=word,
                    )
                )

        for word in self.server_type:
            for m in re.finditer(re.escape(word), text):
                s, e = m.span()
                out.append(
                    Candidate(
                        word,
                        type="ServerTypeHint",
                        span=(s, e),
                        context=self._context(text, s, e),
                        normalized=word,
                    )
                )

        for word in self.state:
            for m in re.finditer(rf"\b{re.escape(word)}\b", text):
                s, e = m.span()
                out.append(
                    Candidate(
                        word,
                        type="StateHint",
                        span=(s, e),
                        context=self._context(text, s, e),
                        normalized=word.capitalize(),
                    )
                )

        for word in self.workload:
            if re.fullmatch(r"[A-Z]{2,4}", word):
                pattern = rf"\b{re.escape(word)}\b"
            else:
                pattern = re.escape(word)

            for m in re.finditer(pattern, text):
                s, e = m.span()
                out.append(
                    Candidate(
                        text=text[s:e],
                        type="WorkloadHint",
                        span=(s, e),
                        context=self._context(text, s, e),
                        normalized=word,
                    )
                )

        # (권장) dedupe
        api_spans = {
            c.span
            for c in out
            if c.type == "InterfaceHint" and c.normalized == "API_GW"
        }
        out = [
            c
            for c in out
            if not (
                c.type == "InterfaceHint"
                and c.normalized == "IGW"
                and c.span in api_spans
            )
        ]
        out = self._prune_overlaps_longest(out, types={"ZoneHint"})
        out = self._prune_overlaps_longest(
            out, types={"DeviceTypeHint"}, normalized_allow={"Line"}
        )

        uniq = {}
        for c in out:
            key = (c.type, c.span, c.normalized or c.text)
            uniq[key] = c
        return list(uniq.values())


test = [
    """ 구성도 명칭: mock MIC업무시스템

[기본정보]----------------------------------------------------

구성도 name: mock MIC(업무시스템)
[법인] ------------------------------------------------------- 해당 시스템 구성 법인은 은행입니다.

[센터]--------------------------------------------------------- 법인에는 다음 센터가 존재합니다:

은행: 의왕, 안성
[통신망 및 통신장비]-------------------------------------------- 센터 내 구성된 통신망과 네트워크 장비는 다음과 같이 구성되어있습니다:

의왕: 내부SDN망, 내부망
안성: 내부SDN망, 내부망
의왕 통신장비: L4 (내부SDN망 안에 구성됨)
안성 통신장비: L4 (내부SDN망 안에 구성됨)


[서버 및 장비]----------------------------------------------------------- 통신망 안의 서버, 시스템, 인터페이스, 네트워크 장비 등은 다음과 같이 포함관계를 가지고 구성되어있습니다.

의왕 내부SDN망:
BT WAS 서버그룹이 1대(PaaS) 존재합니다.
디지털금융 공동AP 서버그룹에 서버가 5대(nbmcidloap01 ~ nbmcidloap05, IaaS, Active), 디지털금융 은행AP 서버그룹에 서버가 4대(nbmcibloap01 ~ nbmcibloap04, IaaS, Active), 디지털금융 교차AP 서버그룹에 서버가 5대(nbmcebloap01 ~ nbmcebloap05, IaaS, Active)로 구성되어 있습니다.
디지털금융 공동DB 서버그룹에 서버 2대(Nbmcidlodb01: active, Nbmcidlodb02: standby, IaaS)
디지털금융 은행DB 서버그룹에 서버 2대(nbmciblodb01: active, nbmciblodb02: standby, IaaS)
디지털금융 교차중계AP 서버그룹에 서버 3대(nbmcebloap11 ~ nbmcebloap13, 베어메탈, Active)

의왕 내부망:
외부시스템(External System)으로 코어뱅킹, 연계뱅킹, 카드계정계, 카드승인계, 인증보안, UMS, 모바일신분증, BPR 이 구성되어있습니다.

안성 내부SDN망:
BT WAS 서버그룹이 1대(PaaS) 존재합니다.
디지털금융 공동AP 서버그룹에 서버 4대(nbmcidloap51 ~ nbmcidloap54, IaaS, Active), 디지털금융 은행AP 서버그룹에 서버 4대(nbmcibloap51 ~ nbmcibloap54, IaaS, Active), 디지털금융 교차AP 서버그룹에 서버 5대(nbmcebloap51 ~ nbmcebloap55, IaaS, Active)
디지털금융 공동DB 서버그룹에 서버 1대(nbmcidlodb51: standby), 디지털금융 은행DB 서버그룹에 서버 1대(nbmciblodb51: standby, IaaS)
디지털금융 교차중계AP 서버그룹에 서버 3대(nbmcebloap61 ~ nbmcebloap63, 베어메탈, Active)

안성 내부망:
외부시스템(External System)으로 코어뱅킹, 연계뱅킹, 카드계정계, 카드승인계, 인증보안, UMS, 모바일신분증, BPR 이 구성되어있습니다.

[사용자 정보]-------------------------------------------------------------- (해당 구성도 내 별도 사용자 장비/APP/브라우저 등 정보 기재 없음.)

[연결 관계 정보]------------------------------------------------------------ 구성요소들의 연결관계는 다음과 같습니다(방향 주의):

의왕 센터: L4 장비 BT WAS가 양방향으로 연결됨, L4 → 디지털금융 공동AP/은행AP/교차AP 각 서버그룹으로 연결됨
의왕 디지털금융 공동AP → 디지털금융 공동DB로 연결 (동일망 내)
의왕 디지털금융 은행AP/교차AP/교차중계AP  → 디지털금융 은행DB로 연결 (동일망 내)

안성 센터: L4 장비  BT WAS가 양방향으로 연결됨, L4 → 디지털금융 공동AP/은행AP/교차AP 각 서버그룹으로 연결됨됨
의왕센터 내부망의 외부시스템과 안성센터 내부망의 외부시스템이 서로 양방향 연결됨.
"""
]
ce = CandidateExtractor()
for t in test:
    print("\n===", t)
    for c in sorted(ce.extract(t), key=lambda x: x.span):
        print(c.type, c.text, c.normalized, c.span)
