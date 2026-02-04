# scripts/make_dataset.py
from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# =========================================================
# 1) VOCAB (사용자 제공 JSON 기반)
#  - 요구사항:
#    - Diagram 엔티티 포함(아래 ensure_diagram에서 강제)
#    - 의왕 / 의왕센터 둘 다 허용(make_center에서 처리)
# =========================================================
VOCAB = {
    "ko": {
        "Corporation": ["은행", "중앙회"],
        # ⚠️ "센터" 단독은 학습 품질에 악영향 가능 -> 권장: 제거
        # 요구사항에 없지만 전체 코드 정리 김에 안정성 개선
        "Center": ["AWS", "의왕", "안성"],
        "NetworkZone": [
            "내부망",
            "내부SDN망",
            "인터넷망(DMZ)",
            "사용자망",
            "대외망",
            "영업점망",
        ],
        "ServerGroup": [
            "발급공통 AP",
            "CA AP",
            "인증 AP",
            "계정계 AP",
            "카드 AP",
            "발급공통 DB",
            "CA DB",
            "인증 DB",
            "계정계 DB",
            "카드 DB",
        ],
        "server_class": ["AP", "DB", "WEB", "WAS", "ETL"],
        "GSLB": ["외부 GSLB", "내부 GSLB"],
        "Line": ["SK브로드밴드", "KT", "LG데이콤"],
        "Firewall": [],
        "NetworkDevice": ["L4 SWITCH", "L3 SWITCH", "IRT 라우터", "ISW 라우터"],
        "ExternalSystem": ["휴대폰본인확인 nice", "유심인증 라온시큐어", "금융결제원"],
        "DBMS": ["ORACLE", "TIBERO", "MS_SQL"],
        "Interface": [
            "EAI",
            "IGW",
            "NGW",
            "API_GW",
            "MCI",
            "영업점MCA",
            "대외MCA",
            "MFT",
            "FOS",
        ],
        "data_replication": ["DISK 복제", "DBMS 복제", "CDC"],
        "dbms_cluster": ["ORACLE CLUSTER", "TIBERO CLUSTER"],
        "count": ["2", "3", "4"],
        "SystemGroup": [
            "시스템 그룹",
            "발급공통시스템",
            "인증 시스템",
            "CA 시스템",
            "배치 시스템",
            "결제 시스템",
        ],
    },
    "en": {
        "Corporation": ["Bank", "Head Office"],
        "Center": ["AWS", "Uiwang Center", "Anseong Center"],
        "NetworkZone": [
            "Internal",
            "Internal SDN",
            "Internet DMZ",
            "User Zone",
            "External",
            "Branch Network",
            "DMZ",
        ],
        "SystemGroup": ["Issuance System", "Auth System", "CA System", "Batch System"],
        "ServerGroup": [
            "Issuance Common AP",
            "RA AP",
            "CA DB",
            "Auth WAS",
            "Batch ETL",
            "Web WEB",
        ],
        "server_class": ["AP", "DB", "WEB", "WAS", "ETL"],
        "GSLB": ["External GSLB", "Internal GSLB"],
        "Line": ["SK Broadband", "KT", "LG Dacom"],
        "NetworkDevice": ["IRT ROUTER", "ISW ROUTER", "L4 SWITCH", "L3 SWITCH"],
        "ExternalSystem": ["NICE phone verification", "RaonSecure USIM auth", "KFTC"],
        "DBMS": ["ORACLE", "TIBERO", "MS_SQL"],
        "Interface": [
            "EAI",
            "IGW",
            "NGW",
            "API_GW",
            "MCI",
            "Branch MCA",
            "External MCA",
            "MFT",
            "FOS",
        ],
        "data_replication": ["DISK replication", "DBMS replication", "CDC"],
        "dbms_cluster": ["ORACLE CLUSTER", "TIBERO CLUSTER"],
        "count": ["2", "3", "4"],
    },
}


# =========================================================
# 1.5) VARIANT / HINT POOLS (CandidateExtractor friendly)
#  - 중복 정의 제거(원본에 2번 있었음)
# =========================================================
HINT_POOLS = {
    # Zone type hints
    "zone_internal": ["내부망", "업무망", "내부", "사내", "internal"],
    "zone_external": ["대외망", "외부망", "외부", "external", "인터넷망", "Internet"],
    "zone_dmz": ["DMZ", "DMZ망", "Internet DMZ", "인터넷 DMZ", "인터넷망(DMZ)"],
    "zone_internal_sdn": [
        "내부SDN망",
        "내부 SDN",
        "SDN망",
        "internal sdn",
        "Internal SDN",
    ],
    "zone_user": ["사용자망", "유저망", "User Zone", "user zone"],
    "zone_branch": ["영업점망", "지점망", "Branch Network", "branch network"],
    # Device type hints
    "layer3": ["L3", "l3", "Layer3", "layer3", "레이어3"],
    "layer4": ["L4", "l4", "Layer4", "layer4", "레이어4"],
    "router": ["라우터", "router", "RT", "rt"],
    "switch": ["스위치", "switch", "SW", "sw"],
    "irt": ["IRT", "irt", "IRT router", "irt-router", "IRT 라우터", "irt 라우터"],
    "isw": ["ISW", "isw", "ISW router", "isw-router", "ISW 라우터", "isw 라우터"],
    # Engine hints
    "oracle": ["ORACLE", "Oracle", "orcl", "ORCL"],
    "postgres": ["POSTGRES", "PostgreSQL", "postgres", "postgresql", "pg", "PG"],
    "mssql": ["MS_SQL", "MSSQL", "MS SQL", "sqlserver", "SQLSERVER", "SQL Server"],
    "tibero": ["TIBERO", "Tibero", "tibero"],
    # Line context
    "line_context": [
        "회선",
        "전용회선",
        "대외회선",
        "망연계",
        "MPLS",
        "mpls",
        "VPN",
        "vpn",
        "인터넷구간",
        "ISP",
        "isp",
        "회선사",
        "통신",
        "라인",
        "line",
    ],
    "isp_short": ["sk", "kt", "lg"],
}

NOISE_DECORATORS = [
    lambda s: s,
    lambda s: f"({s})",
    lambda s: f"[{s}]",
    lambda s: f"-{s}-",
    lambda s: f"{s}",
]


def _maybe_space_variation(rng: random.Random, s: str) -> str:
    if rng.random() < 0.25:
        s = s.replace("브로드밴드", " 브로드밴드")
    if rng.random() < 0.12:
        s = s.replace("데이콤", " 데이콤")
    if rng.random() < 0.10:
        s = s.replace("_", rng.choice(["_", "-", " "]))
    if rng.random() < 0.10:
        s = s.replace("-", rng.choice(["-", "_", ""]))
    return re.sub(r"\s+", " ", s).strip()


def _case_variation(rng: random.Random, s: str) -> str:
    if any("a" <= c.lower() <= "z" for c in s):
        r = rng.random()
        if r < 0.20:
            return s.lower()
        if r < 0.40:
            return s.upper()
        if r < 0.55:
            return s.title()
    return s


def _decorate(rng: random.Random, s: str) -> str:
    if rng.random() < 0.22:
        s = rng.choice(NOISE_DECORATORS)(s)
    if rng.random() < 0.18:
        s = s.replace("(", rng.choice(["(", " ("])).replace(
            ")", rng.choice([")", ") "])
        )
    return s


def mention_variant(
    rng: random.Random, base: str, extra_hints: Optional[List[str]] = None
) -> str:
    """
    base: canonical 문자열(entities에 넣는 값)
    extra_hints: candidate_extractor 힌트 토큰을 표면에 같이 노출하고 싶을 때
    """
    s = base
    s = _maybe_space_variation(rng, s)
    s = _case_variation(rng, s)

    if extra_hints and rng.random() < 0.70:
        hint = rng.choice(extra_hints)
        hint = _case_variation(rng, _maybe_space_variation(rng, hint))
        style = rng.randrange(4)
        if style == 0:
            s = f"{s}({hint})"
        elif style == 1:
            s = f"{s} - {hint}"
        elif style == 2:
            s = f"{hint} {s}"
        else:
            s = f"{s} [{hint}]"

    s = _decorate(rng, s)
    return s


# =========================================================
# 2) Schema: labels / relations / allowed triples
# =========================================================
LABELS = [
    "Diagram",
    "Corporation",
    "Center",
    "NetworkZone",
    "SystemGroup",
    "ServerGroup",
    "Server",
    "DBMS",
    "Interface",
    "ExternalSystem",
    "NetworkDevice",
    "GSLB",
    "Line",
    "Firewall",
    "User",
]

REL_TYPES = [
    "HAS_COVERS",
    "HAS_CENTER",
    "HAS_ZONE",
    "HAS_DEVICE",
    "IN_ZONE",
    "IN_GROUP",
    "CONNECTED_TO",
]

DEVICE_LABELS = ["GSLB", "Line", "Firewall", "NetworkDevice"]

ALLOWED_TRIPLES = {
    # hierarchy
    ("Diagram", "HAS_COVERS", "Corporation"),
    ("Corporation", "HAS_CENTER", "Center"),
    ("Center", "HAS_ZONE", "NetworkZone"),
    *{("Center", "HAS_DEVICE", d) for d in DEVICE_LABELS},
    # in_zone
    ("Server", "IN_ZONE", "NetworkZone"),
    ("SystemGroup", "IN_ZONE", "NetworkZone"),
    ("ServerGroup", "IN_ZONE", "NetworkZone"),
    ("Interface", "IN_ZONE", "NetworkZone"),
    ("ExternalSystem", "IN_ZONE", "NetworkZone"),
    # in_group
    ("Server", "IN_GROUP", "SystemGroup"),
    ("Interface", "IN_GROUP", "SystemGroup"),
    ("ExternalSystem", "IN_GROUP", "SystemGroup"),
    ("Server", "IN_GROUP", "ServerGroup"),
    ("Interface", "IN_GROUP", "ServerGroup"),
    ("ExternalSystem", "IN_GROUP", "ServerGroup"),
    # connected_to (non-device)
    ("Server", "CONNECTED_TO", "Server"),
    ("Server", "CONNECTED_TO", "DBMS"),
    ("DBMS", "CONNECTED_TO", "DBMS"),
    ("Server", "CONNECTED_TO", "NetworkDevice"),
    ("Server", "CONNECTED_TO", "Interface"),
    ("Server", "CONNECTED_TO", "ExternalSystem"),
    ("Interface", "CONNECTED_TO", "Interface"),
    ("Interface", "CONNECTED_TO", "NetworkDevice"),
    ("Interface", "CONNECTED_TO", "ExternalSystem"),
    ("ExternalSystem", "CONNECTED_TO", "NetworkDevice"),
    ("ExternalSystem", "CONNECTED_TO", "Interface"),
    ("ExternalSystem", "CONNECTED_TO", "ExternalSystem"),
    # device ↔ *
    *{
        (d, "CONNECTED_TO", x)
        for d in DEVICE_LABELS
        for x in DEVICE_LABELS + ["Server", "Interface", "ExternalSystem"]
    },
    *{
        (x, "CONNECTED_TO", d)
        for d in DEVICE_LABELS
        for x in ["Server", "Interface", "ExternalSystem"]
    },
}


# =========================================================
# 3) Template pools
# =========================================================
TEMPLATE_POOLS: Dict[str, List[str]] = {
    "HAS_COVERS": [
        "구성도는 {corp}을 포함한다",
        "{corp}이(가) 구성도에 포함된다",
        "해당 구성도에는 {corp} 범위가 포함된다",
    ],
    "HAS_CENTER": [
        "{corp}은 {center}를 운영한다",
        "{center}는 {corp}에서 운영된다",
        "{corp} 산하에 {center}가 있다",
    ],
    "HAS_ZONE": [
        "{center}는 {zone}을 포함한다",
        "{zone}은 {center}에 구성되어 있다",
        "{center} 구간에는 {zone}이 존재한다",
    ],
    "HAS_DEVICE": [
        "{center}에는 {device}가 배치되어 있다",
        "{device}가 {center}에 설치되어 있다",
        "{center}는 {device}를 운영한다",
    ],
    "IN_ZONE": [
        "{node}은 {zone}에 위치한다",
        "{zone}에는 {node}이 배치되어 있다",
        "{node}은 {zone} 환경에서 동작한다",
        "{node}이 {zone} 구간에 존재한다",
        "{node}은 {zone}을 통해 서비스된다",
    ],
    "IN_GROUP": [
        "{node}는 {group}에 속한다",
        "{group} 구성 요소로 {node}가 포함된다",
        "{group}은 {node}로 구성된다",
        "{node}는 {group} 단위로 관리된다",
    ],
    "SERVER_DB": [
        "{server}는 {dbms}에 연결한다",
        "{server}가 {dbms}로 쿼리를 수행한다",
        "{dbms}는 {server}에서 사용된다",
        "{server}의 데이터는 {dbms}에 저장된다",
    ],
    "IFACE_DB": [
        "{iface}는 {dbms}와 연동된다",
        "{dbms} 연계를 위해 {iface}가 사용된다",
        "{iface}를 통해 {dbms}에 접속한다",
    ],
    "SERVER_SERVER": [
        "{a}는 {b}를 호출한다",
        "{a}에서 {b}로 요청을 보낸다",
        "{a}와 {b}는 내부 연동된다",
        "{b}는 {a}의 요청을 처리한다",
    ],
    "DB_REPLICATION": [
        "{a}는 {b}로 복제된다",
        "{a}와 {b}는 동기화한다",
        "{a}에서 {b}로 로그를 전송한다",
        "{a}–{b} 간 이중화 구성이 적용되어 있다",
    ],
    "EXTERNAL": [
        "{ext}은 {iface}를 통해 내부망과 연계된다",
        "{ext}에서 {target}로 요청이 들어온다",
        "{ext} 연계를 위한 통신 구간이 구성되어 있다 ({iface})",
    ],
    "DEVICE_CONNECT": [
        "{device}는 {target}와 연결된다",
        "{target}은 {device}를 통해 연결된다",
        "{device}와 {target} 간 연결이 구성되어 있다",
    ],
    "AMBIGUOUS": [
        "{a}와 {b} 간 연계가 있다",
        "{a}–{b} 간 통신 구성이 적용되어 있다",
        "{a}에서 {b}로 트래픽이 흐른다",
        "{a}과(와) {b} 사이 연결이 존재한다",
    ],
    "MULTI_LIST_ZONE": [
        "{zone}에는 {a}, {b}, {c}가 배치되어 있다",
        "{a}, {b}, {c}는 {zone} 구간에 존재한다",
        "{zone} 환경에서 {a}와 {b}가 동작하며 {c}가 연계된다",
        "{zone}에는 {a}와 {b}가 있고, {c}는 해당 구간에서 서비스된다",
    ],
    "CHAIN": [
        "{a}는 {iface}를 통해 {device}와 연결되고, {device}를 경유하여 {ext}와 연계된다",
        "{ext} 요청은 {device}를 거쳐 {iface}로 전달되고, {iface}는 {a}를 호출한다",
        "{a}–{iface}–{device}–{ext} 순으로 통신 경로가 구성되어 있다",
    ],
}


# =========================================================
# 4) Helpers
# =========================================================
def pick_template(rng: random.Random, key: str, **kwargs) -> str:
    return rng.choice(TEMPLATE_POOLS[key]).format(**kwargs)


def _join_sentences(rng: random.Random, sents: List[str]) -> str:
    sep = rng.choice([" ", "  ", "\n", ". "])
    out = sep.join([s.strip().rstrip(".") + "." for s in sents if s and s.strip()])
    out = re.sub(r"\.\.+", ".", out)
    return out.strip()


def apply_light_variations(rng: random.Random, text: str) -> str:
    swaps = [
        ("위치한다", rng.choice(["존재한다", "배치되어 있다", "있다"])),
        ("연계된다", rng.choice(["연동된다", "연계됨", "연동됨"])),
        ("연결된다", rng.choice(["접속된다", "연결됨", "연동된다"])),
        ("요청이 들어온다", rng.choice(["요청이 전달된다", "호출이 발생한다"])),
    ]
    for a, b in swaps:
        if rng.random() < 0.12:
            text = text.replace(a, b)
    if rng.random() < 0.15:
        text = text.replace(". ", rng.choice([".  ", ".\n"]))
    return text


def inject_ambiguity_and_noise(
    rng: random.Random, text: str, ambig_p: float, noise_p: float
) -> str:
    if rng.random() < ambig_p:
        tail = rng.choice(TEMPLATE_POOLS["AMBIGUOUS"]).format(a="시스템", b="연계구간")
        text = text.rstrip(".") + ". " + tail.rstrip(".") + "."

    if rng.random() < noise_p:
        text = apply_light_variations(rng, text)
        if rng.random() < 0.25:
            text = text.replace("는", rng.choice(["는", "은", "에서는"]))
        if rng.random() < 0.20:
            text = text.replace("가", rng.choice(["가", "이", "에서는"]))
    return text


def entity_pack(**kwargs: List[str]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for k, v in kwargs.items():
        if not v:
            continue
        seen = set()
        dedup = []
        for x in v:
            if x not in seen:
                dedup.append(x)
                seen.add(x)
        out[k] = dedup
    return out


# =========================================================
# ✅ GLiNER2 Relations format helpers
# relations item: {"REL_TYPE": {"head": "...", "tail": "..."}}
# =========================================================
def rel(head: str, tail: str, type_: str) -> Dict[str, Dict[str, str]]:
    return {type_: {"head": head, "tail": tail}}


def rel_parts(r: Dict[str, Dict[str, str]]) -> Tuple[str, str, str]:
    ((t, payload),) = r.items()
    return t, payload["head"], payload["tail"]


def dedupe_relations(
    relations: List[Dict[str, Dict[str, str]]],
) -> List[Dict[str, Dict[str, str]]]:
    out = []
    seen = set()
    for r in relations:
        t, h, ta = rel_parts(r)
        key = (h, t, ta)
        if key not in seen:
            out.append(r)
            seen.add(key)
    return out


def vocab_pick(rng: random.Random, lang: str, label: str) -> str:
    xs = VOCAB.get(lang, {}).get(label, [])
    if not xs:
        return f"{label}-X"
    return rng.choice(xs)


def make_center(rng: random.Random, lang: str) -> str:
    # 요구: 의왕/의왕센터 둘 다 가능
    if lang == "ko":
        base = rng.choice(["AWS", "의왕", "안성"])
        return base + "센터" if rng.random() < 0.78 else base
    return vocab_pick(rng, lang, "Center")


def make_server_name(rng: random.Random, lang: str) -> str:
    prefix = rng.choice(["nbef", "nbe", "ra", "auth", "pay", "co"])
    mid = rng.choice(["ap", "web", "was", "etl"])
    num = rng.randrange(1, 99)
    return f"{prefix}{mid}{num:02d}" if lang == "ko" else f"{prefix}-{mid}{num:02d}"


def make_dbms_name(rng: random.Random) -> str:
    prefix = rng.choice(["NBEFMC", "AUTH", "PAY", "CO", "RA"])
    num = rng.randrange(1, 99)
    return f"{prefix}DB{num:02d}"


def paren_variant(rng: random.Random, name: str, hint: str) -> str:
    style = rng.randrange(3)
    if style == 0:
        return f"{name}({hint})"
    if style == 1:
        return f"{name} - {hint}"
    return f"{hint} {name}"


def label_of(entities: Dict[str, List[str]], name: str) -> Optional[str]:
    priority = [
        "Server",
        "DBMS",
        "ExternalSystem",
        "Interface",
        "NetworkDevice",
        "GSLB",
        "Line",
        "Firewall",
        "SystemGroup",
        "ServerGroup",
        "NetworkZone",
        "Center",
        "Corporation",
        "Diagram",
    ]
    for lab in priority:
        if name in entities.get(lab, []):
            return lab
    for lab, names in entities.items():
        if name in names:
            return lab
    return None


def schema_violation(
    entities: Dict[str, List[str]],
    relations: List[Dict[str, Dict[str, str]]],
) -> Optional[str]:
    for r in relations:
        t, h, ta = rel_parts(r)
        hl = label_of(entities, h)
        tl = label_of(entities, ta)
        if hl is None or tl is None:
            return f"unknown_entity_in_relation:{r}"
        if (hl, t, tl) not in ALLOWED_TRIPLES:
            return f"disallowed_triple:({hl},{t},{tl})"
    return None


def normalize_relation_directions(
    entities: Dict[str, List[str]],
    relations: List[Dict[str, Dict[str, str]]],
) -> List[Dict[str, Dict[str, str]]]:
    """
    생성된 CONNECTED_TO 관계 방향을 스키마 기준으로 최종 보정.
    핵심: (ExternalSystem CONNECTED_TO Server) => (Server CONNECTED_TO ExternalSystem)
    """
    out: List[Dict[str, Dict[str, str]]] = []
    for r in relations:
        t, h, ta = rel_parts(r)
        if t != "CONNECTED_TO":
            out.append(r)
            continue

        hl = label_of(entities, h)
        tl = label_of(entities, ta)

        if hl == "ExternalSystem" and tl == "Server":
            out.append(rel(ta, h, "CONNECTED_TO"))
            continue

        out.append(r)

    return dedupe_relations(out)


# =========================================================
# 5) Scenarios
# =========================================================
@dataclass
class Scenario:
    text: str
    entities: Dict[str, List[str]]
    relations: List[Dict[str, Dict[str, str]]]
    meta: Dict[str, str]


def ensure_diagram(rng: random.Random, sc: Scenario, lang: str) -> Scenario:
    """
    ✅ 요구사항: Diagram 엔티티는 반드시 포함해야 함.
    + Corporation이 존재하면 HAS_COVERS를 높은 확률로 보강(데이터 다양성/일관성).
    """
    if "Diagram" not in sc.entities or not sc.entities["Diagram"]:
        diagram = rng.choice(
            ["인증서 시스템 구성도", "결제 시스템 구성도", "계정계 구성도"]
        )
        sc.entities["Diagram"] = [diagram]
    else:
        diagram = sc.entities["Diagram"][0]

    corp_list = sc.entities.get("Corporation", [])
    if corp_list and rng.random() < 0.75:
        corp = corp_list[0]
        sc.relations.append(rel(diagram, corp, "HAS_COVERS"))

    sc.relations = dedupe_relations(sc.relations)
    return sc


def scenario_core_hierarchy(rng: random.Random, lang: str) -> Scenario:
    diagram = rng.choice(
        ["인증서 시스템 구성도", "결제 시스템 구성도", "계정계 구성도"]
    )
    corp = vocab_pick(rng, lang, "Corporation")
    center = make_center(rng, lang)
    zone = vocab_pick(rng, lang, "NetworkZone")

    server = make_server_name(rng, lang)
    iface = vocab_pick(rng, lang, "Interface")
    sysg = vocab_pick(rng, lang, "SystemGroup")

    dbms = make_dbms_name(rng)
    engine = vocab_pick(rng, lang, "DBMS")
    db_mention = paren_variant(rng, dbms, engine) if rng.random() < 0.65 else dbms

    sents: List[str] = []
    relations: List[Dict[str, Dict[str, str]]] = []

    entities = entity_pack(
        Diagram=[diagram],
        Corporation=[corp],
        Center=[center],
        NetworkZone=[zone],
        Server=[server],
        Interface=[iface],
        SystemGroup=[sysg],
        DBMS=[dbms],
    )

    if rng.random() < 0.80:
        sents.append(pick_template(rng, "HAS_COVERS", corp=corp))
        relations.append(rel(diagram, corp, "HAS_COVERS"))

    if rng.random() < 0.80:
        sents.append(pick_template(rng, "HAS_CENTER", corp=corp, center=center))
        relations.append(rel(corp, center, "HAS_CENTER"))

    if rng.random() < 0.90:
        sents.append(pick_template(rng, "HAS_ZONE", center=center, zone=zone))
        relations.append(rel(center, zone, "HAS_ZONE"))

    zone_target_kind = rng.choices(
        ["Server", "Interface", "SystemGroup"], weights=[0.55, 0.25, 0.20], k=1
    )[0]
    zone_target = (
        server
        if zone_target_kind == "Server"
        else (iface if zone_target_kind == "Interface" else sysg)
    )

    sents.append(pick_template(rng, "IN_ZONE", node=zone_target, zone=zone))
    relations.append(rel(zone_target, zone, "IN_ZONE"))

    if rng.random() < 0.15:
        sents.append(pick_template(rng, "IFACE_DB", iface=iface, dbms=db_mention))
        relations.append(rel(iface, dbms, "CONNECTED_TO"))
    else:
        sents.append(pick_template(rng, "SERVER_DB", server=server, dbms=db_mention))
        relations.append(rel(server, dbms, "CONNECTED_TO"))

    if rng.random() < 0.35:
        sents.append(pick_template(rng, "IN_GROUP", node=server, group=sysg))
        relations.append(rel(server, sysg, "IN_GROUP"))
        if rng.random() < 0.60:
            sents.append(pick_template(rng, "IN_GROUP", node=iface, group=sysg))
            relations.append(rel(iface, sysg, "IN_GROUP"))

    text = _join_sentences(rng, sents)
    relations = dedupe_relations(relations)
    return Scenario(text, entities, relations, meta={"scenario": "core_hierarchy"})


def scenario_group_membership(rng: random.Random, lang: str) -> Scenario:
    center = make_center(rng, lang)
    zone = vocab_pick(rng, lang, "NetworkZone")

    if rng.random() < 0.55:
        group_label = "SystemGroup"
        group = vocab_pick(rng, lang, "SystemGroup")
    else:
        group_label = "ServerGroup"
        group = vocab_pick(rng, lang, "ServerGroup")

    server = make_server_name(rng, lang)
    iface = vocab_pick(rng, lang, "Interface")
    ext = vocab_pick(rng, lang, "ExternalSystem") if rng.random() < 0.60 else None

    s1 = pick_template(rng, "HAS_ZONE", center=center, zone=zone)
    s2 = pick_template(rng, "IN_ZONE", node=group, zone=zone)
    s3 = pick_template(rng, "IN_GROUP", node=server, group=group)
    s4 = pick_template(rng, "IN_GROUP", node=iface, group=group)

    sents = [s1, s2, s3, s4]
    entities = entity_pack(
        Center=[center],
        NetworkZone=[zone],
        **{group_label: [group]},
        Server=[server],
        Interface=[iface],
    )
    relations: List[Dict[str, Dict[str, str]]] = [
        rel(center, zone, "HAS_ZONE"),
        rel(group, zone, "IN_ZONE"),
        rel(server, group, "IN_GROUP"),
        rel(iface, group, "IN_GROUP"),
    ]

    if ext:
        s5 = pick_template(rng, "IN_GROUP", node=ext, group=group)
        sents.append(s5)
        entities["ExternalSystem"] = [ext]
        relations.append(rel(ext, group, "IN_GROUP"))
        if rng.random() < 0.45:
            s6 = pick_template(rng, "IN_ZONE", node=ext, zone=zone)
            sents.append(s6)
            relations.append(rel(ext, zone, "IN_ZONE"))

    text = _join_sentences(rng, sents)
    relations = dedupe_relations(relations)
    return Scenario(text, entities, relations, meta={"scenario": "group_membership"})


def scenario_external_connections(rng: random.Random, lang: str) -> Scenario:
    ext = vocab_pick(rng, lang, "ExternalSystem")
    iface = vocab_pick(rng, lang, "Interface")
    zone = vocab_pick(rng, lang, "NetworkZone")

    device_label = rng.choice(["GSLB", "Line", "NetworkDevice"])
    device = vocab_pick(rng, lang, device_label)

    center = make_center(rng, lang)

    target_is_server = rng.random() < 0.55
    target = (
        make_server_name(rng, lang)
        if target_is_server
        else vocab_pick(rng, lang, "Interface")
    )

    s0 = pick_template(rng, "HAS_DEVICE", center=center, device=device)
    s1 = pick_template(rng, "EXTERNAL", ext=ext, iface=iface, target=target)
    s2 = pick_template(rng, "IN_ZONE", node=iface, zone=zone)
    s3 = pick_template(rng, "DEVICE_CONNECT", device=device, target=iface)
    text = _join_sentences(rng, [s0, s1, s2, s3])

    entities: Dict[str, List[str]] = {
        "ExternalSystem": [ext],
        "NetworkZone": [zone],
        device_label: [device],
        "Center": [center],
        "Interface": [iface],
    }
    if target_is_server:
        entities["Server"] = [target]
    else:
        if target != iface:
            entities["Interface"] = [iface, target]

    relations: List[Dict[str, Dict[str, str]]] = [
        rel(center, device, "HAS_DEVICE"),
        rel(ext, iface, "CONNECTED_TO"),
        rel(iface, zone, "IN_ZONE"),
        rel(device, iface, "CONNECTED_TO"),
        rel(ext, device, "CONNECTED_TO"),
    ]

    if target_is_server:
        relations.append(
            rel(target, ext, "CONNECTED_TO")
        )  # Server -> ExternalSystem (허용)
    else:
        relations.append(
            rel(ext, target, "CONNECTED_TO")
        )  # ExternalSystem -> Interface (허용)

    relations = dedupe_relations(relations)
    return Scenario(
        text, entities, relations, meta={"scenario": "external_connections"}
    )


def scenario_db_replication(rng: random.Random, lang: str) -> Scenario:
    db_a = make_dbms_name(rng)
    db_b = make_dbms_name(rng)
    eng_a = vocab_pick(rng, lang, "DBMS")
    eng_b = vocab_pick(rng, lang, "DBMS")

    a_m = paren_variant(rng, db_a, eng_a) if rng.random() < 0.70 else db_a
    b_m = paren_variant(rng, db_b, eng_b) if rng.random() < 0.70 else db_b

    s1 = pick_template(rng, "DB_REPLICATION", a=a_m, b=b_m)
    text = _join_sentences(rng, [s1])

    entities = entity_pack(DBMS=[db_a, db_b])
    relations: List[Dict[str, Dict[str, str]]] = [rel(db_a, db_b, "CONNECTED_TO")]
    return Scenario(text, entities, relations, meta={"scenario": "db_replication"})


def scenario_zone_multilist(rng: random.Random, lang: str) -> Scenario:
    zone = vocab_pick(rng, lang, "NetworkZone")
    center = make_center(rng, lang)

    a_server = make_server_name(rng, lang)
    b_iface = vocab_pick(rng, lang, "Interface")
    c_ext = vocab_pick(rng, lang, "ExternalSystem")

    s0 = (
        pick_template(rng, "HAS_ZONE", center=center, zone=zone)
        if rng.random() < 0.75
        else ""
    )
    s1 = pick_template(
        rng, "MULTI_LIST_ZONE", zone=zone, a=a_server, b=b_iface, c=c_ext
    )

    sents = [x for x in [s0, s1] if x]
    text = _join_sentences(rng, sents)

    entities = entity_pack(
        Center=[center],
        NetworkZone=[zone],
        Server=[a_server],
        Interface=[b_iface],
        ExternalSystem=[c_ext],
    )

    relations: List[Optional[Dict[str, Dict[str, str]]]] = [
        rel(center, zone, "HAS_ZONE") if s0 else None,
        rel(a_server, zone, "IN_ZONE"),
        rel(b_iface, zone, "IN_ZONE"),
        rel(c_ext, zone, "IN_ZONE"),
    ]
    relations = [r for r in relations if r is not None]
    relations = dedupe_relations(relations)

    return Scenario(text, entities, relations, meta={"scenario": "zone_multilist"})


def scenario_connection_chain(rng: random.Random, lang: str) -> Scenario:
    a = make_server_name(rng, lang)
    iface = vocab_pick(rng, lang, "Interface")
    ext = vocab_pick(rng, lang, "ExternalSystem")
    center = make_center(rng, lang)
    zone = vocab_pick(rng, lang, "NetworkZone")

    device_label = rng.choice(["GSLB", "Line", "NetworkDevice"])
    device = vocab_pick(rng, lang, device_label)

    s1 = pick_template(rng, "CHAIN", a=a, iface=iface, device=device, ext=ext)
    s2 = (
        pick_template(rng, "HAS_DEVICE", center=center, device=device)
        if rng.random() < 0.65
        else ""
    )
    s3 = (
        pick_template(rng, "IN_ZONE", node=iface, zone=zone)
        if rng.random() < 0.70
        else ""
    )
    s4 = pick_template(rng, "IN_ZONE", node=a, zone=zone) if rng.random() < 0.35 else ""

    sents = [x for x in [s1, s2, s3, s4] if x]
    text = _join_sentences(rng, sents)

    entities = entity_pack(
        Center=[center],
        NetworkZone=[zone],
        Server=[a],
        Interface=[iface],
        ExternalSystem=[ext],
        **{device_label: [device]},
    )

    relations: List[Dict[str, Dict[str, str]]] = [
        rel(a, iface, "CONNECTED_TO"),
        rel(iface, device, "CONNECTED_TO"),
        rel(device, ext, "CONNECTED_TO"),
    ]
    if s2:
        relations.append(rel(center, device, "HAS_DEVICE"))
    if s3:
        relations.append(rel(iface, zone, "IN_ZONE"))
    if s4:
        relations.append(rel(a, zone, "IN_ZONE"))

    relations = dedupe_relations(relations)
    return Scenario(text, entities, relations, meta={"scenario": "connection_chain"})


SCENARIOS = [
    scenario_core_hierarchy,
    scenario_group_membership,
    scenario_external_connections,
    scenario_db_replication,
    scenario_zone_multilist,
    scenario_connection_chain,
]


def min_relations_required(scenario_name: str, baseline: int) -> int:
    per = {
        "core_hierarchy": max(3, baseline),
        "group_membership": max(3, baseline),
        "external_connections": max(3, baseline),
        "zone_multilist": max(3, baseline),
        "connection_chain": max(3, baseline),
        "db_replication": 1,
    }
    return per.get(scenario_name, baseline)


def generate_one(rng: random.Random, lang: str, weights: List[float]) -> Scenario:
    fn = rng.choices(SCENARIOS, weights=weights, k=1)[0]
    sc = fn(rng, lang)
    sc.relations = dedupe_relations(sc.relations)

    # ✅ Diagram 강제 포함(+ HAS_COVERS 보강)
    sc = ensure_diagram(rng, sc, lang)

    return sc


# =========================================================
# 6) Main
# =========================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", type=str, choices=["ko", "en"], required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--out", type=str, required=True)
    ap.add_argument("--seed", type=int, default=7)

    ap.add_argument("--min_rel", type=int, default=2)
    ap.add_argument("--verbose", action="store_true")

    ap.add_argument("--ambiguous_ratio", type=float, default=0.07)
    ap.add_argument("--noise_ratio", type=float, default=0.25)
    ap.add_argument("--hard_negative_ratio", type=float, default=0.03)

    ap.add_argument("--report", action="store_true")
    ap.add_argument("--report_top", type=int, default=20)

    ap.add_argument("--debug_dump", type=str, default="")
    ap.add_argument("--debug_dump_max", type=int, default=5)

    args = ap.parse_args()

    for name, v in [
        ("ambiguous_ratio", args.ambiguous_ratio),
        ("noise_ratio", args.noise_ratio),
        ("hard_negative_ratio", args.hard_negative_ratio),
    ]:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"--{name} must be between 0 and 1. got={v}")

    rng = random.Random(args.seed)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    debug_path = Path(args.debug_dump) if args.debug_dump else None
    debug_written = 0
    if debug_path:
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        if debug_path.exists():
            debug_path.unlink()

    # ✅ 분포 제어: core 반복 줄이고, IN_ZONE/HAS_ZONE/chain 증가
    # core, group, external, db_rep, zone_multilist, chain
    weights = [0.24, 0.20, 0.18, 0.10, 0.14, 0.14]

    written = 0
    dropped = 0
    reasons: Dict[str, int] = {}

    entity_counts = Counter()
    rel_counts = Counter()
    triple_counts = Counter()

    def dump_drop(reason: str, sc: Scenario):
        nonlocal debug_written
        if not debug_path:
            return
        if debug_written >= args.debug_dump_max:
            return
        payload = {
            "reason": reason,
            "scenario": sc.meta.get("scenario"),
            "text": sc.text,
            "entities": sc.entities,
            "relations": sc.relations,
        }
        with debug_path.open("a", encoding="utf-8") as df:
            df.write(json.dumps(payload, ensure_ascii=False) + "\n")
        debug_written += 1

    with out_path.open("w", encoding="utf-8") as f:
        while written < args.n:
            sc = generate_one(rng, args.lang, weights)

            # hard negative
            if rng.random() < args.hard_negative_ratio:
                sc.relations = []
                sc.meta["hard_negative"] = "true"

            # 방향 정규화
            sc.relations = normalize_relation_directions(sc.entities, sc.relations)

            # min_rel check (hard negative 예외)
            need = min_relations_required(sc.meta.get("scenario", ""), args.min_rel)
            if sc.meta.get("hard_negative") != "true" and len(sc.relations) < need:
                dropped += 1
                reasons["min_relations_violation"] = (
                    reasons.get("min_relations_violation", 0) + 1
                )
                dump_drop("min_relations_violation", sc)
                continue

            # schema check (relations 있는 경우에만)
            if sc.relations:
                reason = schema_violation(sc.entities, sc.relations)
                if reason:
                    dropped += 1
                    reasons[reason] = reasons.get(reason, 0) + 1
                    dump_drop(reason, sc)
                    continue

            # ambiguity/noise injection
            sc.text = inject_ambiguity_and_noise(
                rng,
                sc.text,
                ambig_p=args.ambiguous_ratio,
                noise_p=args.noise_ratio,
            )

            if rng.random() < min(0.15, args.noise_ratio):
                sc.text = apply_light_variations(rng, sc.text)

            sample = {
                "input": sc.text,
                "output": {"entities": sc.entities, "relations": sc.relations},
            }
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
            written += 1

            # report counters
            for lab, names in sc.entities.items():
                entity_counts[lab] += len(names)

            for r in sc.relations:
                t, h, ta = rel_parts(r)
                rel_counts[t] += 1
                h_lab = label_of(sc.entities, h)
                t_lab = label_of(sc.entities, ta)
                triple_counts[(h_lab, t, t_lab)] += 1

    if args.verbose:
        print(f"WROTE: {written}")
        print(f"DROPPED: {dropped}")
        if reasons:
            print("DROP REASONS:")
            for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
                print(f" - {k}: {v}")
        if debug_path:
            print(
                f"DEBUG_DUMP: {debug_path} (max={args.debug_dump_max}, wrote={debug_written})"
            )

    if args.report:
        print("\n=== DATASET REPORT ===")
        print("Entities (label -> count):")
        for k, v in entity_counts.most_common():
            print(f" - {k}: {v}")

        print("\nRelations (type -> count):")
        for k, v in rel_counts.most_common():
            print(f" - {k}: {v}")

        print(f"\nTop {args.report_top} triples (head_label, rel, tail_label):")
        for (h, rel_t, t), v in triple_counts.most_common(args.report_top):
            print(f" - ({h}, {rel_t}, {t}): {v}")


if __name__ == "__main__":
    main()
