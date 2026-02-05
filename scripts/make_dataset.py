# scripts/make_dataset_relpair_rich_add.py
# 목적: "관계쌍(head-tail) 많은 멀티 문장" + "라벨 고정용 hard-negative" 샘플을 추가로 생성해서
#      기존 train6/val6에 이어 붙일 수 있는 add 파일(train_add.jsonl / val_add.jsonl)을 만든다.
#
# 사용 예:
#   python scripts/make_dataset_relpair_rich_add.py --out data_add --n 4000 --seed 7 --multi_ratio 0.7 --hard_ratio 0.3 --noise_ratio 0.15
#
# 출력:
#   data_add/train_add.jsonl
#   data_add/val_add.jsonl
#
# 참고:
# - GLiNER2 포맷: {"input": "...", "output": {"entities": {...}, "relations": [{"REL": {"head": "...", "tail": "..."}} ...]}}
# - 여기 add 파일은 "추가분"만 생성하므로, 기존 파일에 합치는 건 별도 스크립트/커맨드로 처리하세요.

import json
import random
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Callable, Any
import re


# -----------------------------
# SCHEMA
# -----------------------------
REL_TYPES = [
    "HAS_COVERS",
    "HAS_CENTER",
    "HAS_ZONE",
    "HAS_DEVICE",
    "IN_ZONE",
    "IN_GROUP",
    "CONNECTED_TO",
]

LABELS = [
    "Diagram",
    "Corporation",
    "Center",
    "NetworkZone",
    "SystemGroup",
    "Server",
    "Interface",
    "ExternalSystem",
    "NetworkDevice",
    "DBMS",
]

# -----------------------------
# VOCAB (원본과 동일/호환)
# -----------------------------
VOCAB = {
    "Corporation": ["은행", "중앙회"],
    "Center": ["의왕센터", "AWS센터", "안성센터"],
    "NetworkZone": [
        "내부망",
        "내부SDN망",
        "영업점망",
        "대외망",
        "사용자망",
        "인터넷망(DMZ)",
        "대외연계망",
        "업무망",
        "관리망",
        "백본망",
        "전산망",
        "개발망",
        "운영망",
        "인터넷존(DMZ)",
    ],
    "SystemGroup": ["인증 시스템", "결제 시스템", "계정계 시스템", "카드 시스템"],
    "DBMS": ["ORACLE", "TIBERO", "MS_SQL", "POSTGRES"],
    "Interface": [
        "EAI",
        "NGW",
        "IGW",
        "I-GW",
        "I GW",
        "Internal GW",
        "Internal Gateway",
        "MFT",
        "FOS",
        "MCA",
        "API_GW",
        "API GW",
        "APIGW",
        "API-GW",
        "API Gateway",
        "API G/W",
        "MCI",
        "영업점 MCA",
        "대외 MCA",
    ],
    "ExternalSystem": [
        "휴대폰본인확인 nice",
        "금융결제원",
        "유심인증 라온시큐어",
        "디지털FDS",
        "UMS",
    ],
    "NetworkDevice": ["ISW 라우터", "IRT 라우터", "L3 스위치", "L4 스위치"],
    "Line": ["KT 회선", "SK브로드밴드 회선", "LG데이콤"],
}
ALIAS = {
    "Center": {
        "의왕센터": [
            "의왕센터",
            "의왕 센터",
            "의왕",
            "의왕 DC",
            "의왕 데이터센터",
            "의왕센터(DC)",
        ],
        "AWS센터": ["AWS센터", "AWS 센터", "AWS", "AWS 리전", "AWS 데이터센터"],
        "안성센터": ["안성센터", "안성 센터", "안성", "안성 DC"],
    },
    "NetworkZone": {
        "내부망": [
            "내부망",
            "내부 망",
            "내부존",
            "내부 구역",
            "내부 Zone",
            "내부 네트워크존",
        ],
        "내부SDN망": ["내부SDN망", "내부 SDN망", "내부 SDN망", "내부 SDN"],
        "인터넷망(DMZ)": ["인터넷망(DMZ)", "DMZ", "DMZ망", "인터넷 DMZ", "인터넷망"],
        "대외망": ["대외망", "대외 망", "대외연계망", "대외 연계망"],
        "사용자망": ["사용자망", "사용자 망", "업무단말망", "단말망"],
    },
    "Interface": {
        "API_GW": ["API_GW", "API GW", "APIGW", "API-GW", "API Gateway", "API G/W"],
        "IGW": ["IGW", "I-GW", "I GW", "Internal GW", "Internal Gateway"],
    },
    "DBMS": {
        "POSTGRES": ["POSTGRES", "PostgreSQL", "Postgres", "PG", "PGSQL"],
        "MS_SQL": ["MS_SQL", "MSSQL", "MS SQL", "SQL Server", "MS-SQL"],
        "ORACLE": ["ORACLE", "Oracle", "ORCL"],
    },
    "Diagram": {
        "구성도": [
            "구성도",
            "시스템 구성도",
            "네트워크 구성도",
            "아키텍처 구성도",
            "토폴로지 구성도",
        ]
    },
    "Line": {
        "KT 회선": [
            "KT 전용회선",
            "케이티",
            "KT 회선",
            "KT 전용회선",
            "KT 전용 회선",
            "KT MPLS",
            "KT VPN",
        ],
        "SK브로드밴드 회선": [
            "SK브로드밴드",
            "SK 브로드밴드",
            "SK Broadband",
            "SKB 회선",
            "SKB 전용회선",
        ],
        "LG데이콤": [
            "LG데이콤",
            "LG 데이콤",
            "LGU+",
            "LG U+",
            "엘지유플러스",
            "LGU+ 회선",
            "U+ 전용회선",
        ],
    },
    "ExternalSystem": {
        "휴대폰본인확인 nice": [
            "휴대폰본인확인 nice",
            "휴대폰 본인확인 NICE",
            "NICE 본인확인",
            "나이스 본인확인",
            "NICE평가정보",
            "나이스평가정보",
            "NICE 인증",
        ],
        "금융결제원": [
            "금융결제원",
            "금결원",
            "KFTC",
            "금융결제원(KFTC)",
        ],
        "유심인증 라온시큐어": [
            "유심인증 라온시큐어",
            "라온시큐어",
            "RAONSECURE",
            "라온 유심인증",
        ],
        "디지털FDS": [
            "디지털FDS",
            "Digital FDS",
            "FDS",
            "이상거래탐지시스템",
        ],
        "UMS": [
            "UMS",
            "통합메시징시스템",
            "메시징 시스템",
            "Unified Messaging System",
        ],
    },
}


# -----------------------------
# HELPERS
# -----------------------------
def one_of(*xs):
    return random.choice(xs)


def choice(label: str) -> str:
    return random.choice(VOCAB[label])


def choice_line_text(noise_ratio: float) -> str:
    base = random.choice(VOCAB["Line"])
    return materialize("Line", base, noise_ratio)


def choice_external_text(noise_ratio: float) -> str:
    base = random.choice(VOCAB["ExternalSystem"])
    return materialize("ExternalSystem", base, noise_ratio)


def rand_server() -> str:
    patterns = [
        lambda: f"nbefsalora{random.randint(1, 99):02}",
        lambda: f"nbefmcap{random.randint(1, 99):02}",
        lambda: f"nbefapi{random.randint(1, 99):02}",
        lambda: f"nbefwas{random.randint(1, 99):02}",
        lambda: f"nbsrv{random.randint(100, 999)}",
    ]
    return random.choice(patterns)()


def vary_server_name(s: str) -> str:
    m = re.search(r"(\d{2})$", s)
    if m:
        tail = m.group(1)
        variants = [
            s,
            s.upper(),
            s[:-2] + "-" + tail,
            s[:-2] + "_" + tail,
            f"{s}(prd)",
            f"{s}(dev)",
        ]
    else:
        variants = [s, s.upper(), f"{s}(prd)"]
    return random.choice(variants)


def ent_map(pairs: List[Tuple[str, str]]) -> Dict[str, List[str]]:
    out = defaultdict(list)
    for lab, txt in pairs:
        if txt and txt not in out[lab]:
            out[lab].append(txt)
    return dict(out)


def rel(rel_type: str, head_text: str, tail_text: str) -> Dict[str, Any]:
    # GLiNER2 relation format
    return {rel_type: {"head": head_text, "tail": tail_text}}


def make_example(
    text: str, entities: Dict[str, List[str]], relations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    entities = {k: v for k, v in entities.items() if v}
    return {"input": text, "output": {"entities": entities, "relations": relations}}


def rel_to_sentence(rel_type: str, head: str, tail: str) -> str:
    # 너무 자연스러울 필요는 없고, "반드시 문자열이 포함"되는 게 목표
    if rel_type == "HAS_COVERS":
        return f"{head}는 {tail}을 포함한다."
    if rel_type == "HAS_CENTER":
        return f"{head}는 {tail}을 포함한다."
    if rel_type == "HAS_ZONE":
        return f"{head}에는 {tail}이 구성되어 있다."
    if rel_type == "HAS_DEVICE":
        return f"{head}에는 {tail} 장비가 설치되어 있다."
    if rel_type == "IN_ZONE":
        return f"{head}는 {tail}에 위치한다."
    if rel_type == "IN_GROUP":
        return f"{head}는 {tail} 소속이다."
    if rel_type == "CONNECTED_TO":
        return f"{head}는 {tail}와 연결되어 있다."
    return f"{head} -[{rel_type}]-> {tail}."


# -----------------------------
# NORMALIZATION NOISE (원본과 호환)
# -----------------------------
def maybe_noise(s: str, label: str, noise_ratio: float) -> str:
    if random.random() >= noise_ratio:
        return s

    if label == "Center":
        if s.endswith("센터"):
            base = s[:-2]
            return one_of(s, f"{base} 센터", base)
        return s

    if label == "NetworkZone":
        if s.endswith("망") and "DMZ" not in s:
            base = s[:-1]
            return one_of(s, f"{base} 망", s)
        return s

    if label == "DBMS":
        up = s.upper()
        if up == "ORACLE":
            return one_of("ORACLE", "Oracle", "ORCL")
        if up == "POSTGRES":
            return one_of("POSTGRES", "Postgres", "PG")
        if up == "MS_SQL":
            return one_of("MS_SQL", "MSSQL", "MS SQL")
        if up == "TIBERO":
            return one_of("TIBERO", "Tibero")
        return s

    if label == "Interface":
        if s == "IGW":
            return one_of("IGW", "IGW", "IGW", "I-GW")
        if s == "API_GW":
            return one_of("API_GW", "API GW")
        return s

    if label == "ExternalSystem":
        if "nice" in s.lower():
            return one_of(s, s.replace("nice", "NICE"), s.replace("nice", "Nice"))
        if s == "NICE평가정보":
            return one_of("NICE평가정보", "NICE 평가정보")
        return s

    if label == "SystemGroup":
        if "시스템" in s:
            return one_of(s, s.replace("시스템", "시스템(업무)"), s.replace(" ", ""))
        return s

    return s


def materialize(label: str, canonical: str, noise_ratio: float) -> str:
    if random.random() < noise_ratio:
        canonical = random.choice(ALIAS.get(label, {}).get(canonical, [canonical]))
    return maybe_noise(canonical, label, noise_ratio)


# -----------------------------
# VALIDATION (최소 안전장치)
# -----------------------------
def _parse_relation_item(item: Dict[str, Any]) -> Tuple[str, str, str]:
    if len(item) != 1:
        raise ValueError(f"Invalid relation item (must have single key): {item}")
    rel_type = next(iter(item.keys()))
    payload = item[rel_type]
    if not isinstance(payload, dict) or "head" not in payload or "tail" not in payload:
        raise ValueError(f"Invalid relation payload for {rel_type}: {payload}")
    return rel_type, payload["head"], payload["tail"]


def _mention_in_text(text: str, mention: str) -> bool:
    # 기본은 substring으로 충분(여기선 토큰화/정규화까지 안 감)
    # 필요하면 공백 정규화 같은 것도 여기서 같이 처리 가능
    return mention in text


def validate_example(ex: Dict[str, Any]) -> Tuple[bool, str]:
    try:
        text = ex["input"]
        ents = ex["output"]["entities"]
        rels = ex["output"]["relations"]
        if not isinstance(text, str) or not text.strip():
            return False, "empty_text"
        if not isinstance(ents, dict) or not isinstance(rels, list):
            return False, "format_error"

        # 0) entities mention이 text에 실제로 존재하는지
        for lab, xs in ents.items():
            for x in xs:
                if not _mention_in_text(text, x):
                    return False, "entity_mention_not_in_text"

        # 0-2) relations head/tail이 text에 실제로 존재하는지
        for item in rels:
            rtype, h, t = _parse_relation_item(item)
            if not _mention_in_text(text, h) or not _mention_in_text(text, t):
                return False, "relation_head_tail_not_in_text"

        # 1) relation head/tail이 entities 안에 존재하는지(최소한 텍스트 기준)
        all_mentions = set()
        for lab, xs in ents.items():
            if not isinstance(xs, list):
                return False, "invalid_entities_list"
            for x in xs:
                all_mentions.add(x)

        for item in rels:
            rtype, h, t = _parse_relation_item(item)
            if rtype not in REL_TYPES:
                return False, "unknown_relation_type"
            if h == t:
                return False, "self_relation"
            if h not in all_mentions or t not in all_mentions:
                return False, "head_tail_not_in_entities"

        # 2) 같은 surface form이 여러 label로 등장하는지(혼선 방지)
        surface_to_labels = defaultdict(set)
        for lab, xs in ents.items():
            for x in xs:
                surface_to_labels[x].add(lab)
        multi = [(s, labs) for s, labs in surface_to_labels.items() if len(labs) > 1]
        if multi:
            return False, "surface_multi_label"

        return True, "ok"
    except Exception as e:
        return False, f"exception:{type(e).__name__}"


# -----------------------------
# HARD NEGATIVE (라벨 고정)
# - 모델이 자주 헷갈리는 애들을 "한 문장 = 한 라벨"로 못 박아줌
# -----------------------------


def gen_hard_mca_iface(noise_ratio: float) -> Dict[str, Any]:
    iface = "MCA"  # 일부러 고정(경계 토큰)
    text = one_of(
        f"여기서 {iface}는 업무 시스템명이 아니라 인터페이스(Interface) 채널이다.",
        f"{iface}는 연동 채널(Interface)로만 사용한다. 서버나 시스템명이 아니다.",
        f"{iface}(Interface)를 통해 외부 연동이 수행된다.",
    )
    ents = ent_map([("Interface", iface)])
    return make_example(text, ents, [])


def gen_hard_dmz_zone(noise_ratio: float) -> Dict[str, Any]:
    zone = one_of("DMZ", "DMZ망", "인터넷 DMZ", "인터넷망(DMZ)")
    text = one_of(
        f"{zone}는 네트워크 존(NetworkZone)을 의미한다. 장비명이 아니다.",
        f"이 문서에서 {zone} 구역은 NetworkZone이다.",
        f"{zone} 내에 서버가 배치될 수 있다.",
    )
    ents = ent_map([("NetworkZone", zone)])
    return make_example(text, ents, [])


def gen_hard_api_gw_iface(noise_ratio: float) -> Dict[str, Any]:
    iface = one_of("API_GW", "API GW", "API-GW", "API Gateway", "APIGW", "API G/W")
    text = one_of(
        f"{iface}는 인터페이스(Interface) 구성요소다.",
        f"{iface} 채널(Interface)로 외부 연동이 처리된다.",
        f"여기서 {iface}는 시스템명이 아니라 Interface다.",
    )
    ents = ent_map([("Interface", iface)])
    return make_example(text, ents, [])


def gen_hard_mssql_dbms(noise_ratio: float) -> Dict[str, Any]:
    dbms = one_of("MS_SQL", "MSSQL", "MS SQL", "SQL Server", "MS-SQL")
    text = one_of(
        f"{dbms}는 DBMS이다.",
        f"{dbms} DBMS에 접속하는 서버가 존재한다.",
        f"본 구성의 DBMS는 {dbms}로 정의한다.",
    )
    ents = ent_map([("DBMS", dbms)])
    return make_example(text, ents, [])


def gen_hard_zone(noise_ratio: float) -> Dict[str, Any]:
    zone = materialize("NetworkZone", choice("NetworkZone"), noise_ratio)
    text = one_of(
        f"{zone}은 네트워크 존(NetworkZone)이다.",
        f"이 문서에서 {zone}은 네트워크 구역(NetworkZone)을 의미한다.",
        f"{zone}에는 서버가 위치할 수 있다.",
        f"여기서 {zone}은 장비명이 아니라 NetworkZone이다.",
    )
    ents = ent_map([("NetworkZone", zone)])
    rels: List[Dict[str, Any]] = []
    return make_example(text, ents, rels)


def gen_hard_iface(noise_ratio: float) -> Dict[str, Any]:
    iface = materialize("Interface", choice("Interface"), noise_ratio)
    text = one_of(
        f"{iface}는 인터페이스(Interface)이다.",
        f"연동 채널은 {iface}(Interface)로 정의한다.",
        f"{iface}를 통해 외부 시스템이 연동된다.",
        f"여기서 {iface}는 서버가 아니라 Interface다.",
        f"{iface}(Interface) 채널로만 사용하며 시스템명으로 쓰지 않는다.",
    )
    ents = ent_map([("Interface", iface)])
    rels: List[Dict[str, Any]] = []
    return make_example(text, ents, rels)


def gen_hard_dbms(noise_ratio: float) -> Dict[str, Any]:
    dbms = materialize("DBMS", choice("DBMS"), noise_ratio)
    text = one_of(
        f"{dbms}는 데이터베이스(DBMS)이다.",
        f"{dbms} DBMS에 접속하는 서버가 존재한다.",
        f"본 시스템의 DBMS는 {dbms}로 구성된다.",
    )
    ents = ent_map([("DBMS", dbms)])
    rels: List[Dict[str, Any]] = []
    return make_example(text, ents, rels)


def gen_hard_server(noise_ratio: float) -> Dict[str, Any]:
    server = materialize("Server", vary_server_name(rand_server()), noise_ratio)
    text = one_of(
        f"{server}는 서버(Server) 식별자이다.",
        f"서버명 {server}가 운영 중이다.",
        f"{server} 서버가 배치되어 있다.",
    )
    ents = ent_map([("Server", server)])
    rels: List[Dict[str, Any]] = []
    return make_example(text, ents, rels)


def gen_hard_device(noise_ratio: float) -> Dict[str, Any]:
    dev = materialize("NetworkDevice", choice("NetworkDevice"), noise_ratio)
    text = one_of(
        f"{dev}는 네트워크 장비(NetworkDevice)이다.",
        f"네트워크 장비 {dev}가 설치되어 있다.",
        f"{dev} 장비가 트래픽을 처리한다.",
    )
    ents = ent_map([("NetworkDevice", dev)])
    rels: List[Dict[str, Any]] = []
    return make_example(text, ents, rels)


HARD_GENERATORS: List[Callable[[float], Dict[str, Any]]] = [
    gen_hard_zone,
    gen_hard_iface,
    gen_hard_dbms,
    gen_hard_server,
    gen_hard_device,
    # 추가
    gen_hard_mca_iface,
    gen_hard_dmz_zone,
    gen_hard_api_gw_iface,
    gen_hard_mssql_dbms,
]


def external_ctx(ext: str) -> str:
    return random.choice(EXT_PHRASES).format(ext=ext)


# -----------------------------
# RELPAIR-RICH MULTI (관계쌍 많은 버전)
# - head/tail 후보를 많이 만들되, surface 중복 라벨/자기자신 관계 금지
# -----------------------------
def gen_multi_relpair_rich_1(noise_ratio: float) -> Dict[str, Any]:
    corp = materialize("Corporation", choice("Corporation"), noise_ratio)
    center = materialize("Center", choice("Center"), noise_ratio)
    zone = materialize("NetworkZone", choice("NetworkZone"), noise_ratio)

    sg = materialize("SystemGroup", choice("SystemGroup"), noise_ratio)

    server1 = materialize("Server", vary_server_name(rand_server()), noise_ratio)
    server2 = materialize("Server", vary_server_name(rand_server()), noise_ratio)

    dbms1 = materialize("DBMS", choice("DBMS"), noise_ratio)

    iface1 = materialize("Interface", choice("Interface"), noise_ratio)
    ext1 = materialize("ExternalSystem", choice("ExternalSystem"), noise_ratio)

    dev1 = materialize("NetworkDevice", choice("NetworkDevice"), noise_ratio)

    zone_run_phrases = [
        "{zone}에서 {server}가 운영된다",
        "{zone} 내에서 {server}가 구동된다",
        "{server}는 {zone}에 위치해 운영된다",
    ]

    multi_server_phrases = [
        "{zone}에서 {s1}와 {s2}가 운영된다",
        "{zone} 내에 {s1}, {s2} 서버가 배치되어 있다",
        "{s1}와 {s2}는 {zone}에서 운영된다",
    ]

    server_group_phrases = [
        "{server}는 {sg} 소속이다",
        "{server}는 {sg} 산하이다",
        "{sg}에 속한 {server}는",
    ]

    server_dbms_phrases = [
        "{dbms}와 연결되어 있다",
        "{dbms}에 접속한다",
        "{dbms} DB를 사용한다",
    ]

    templates = [
        # A: 복수 서버 운영 강조
        (
            f"{corp}의 {center}에는 {zone}이 구성되어 있다. "
            f"{random.choice(multi_server_phrases).format(zone=zone, s1=server1, s2=server2)}."
        ),
        # B: 포함관계 + 개별 서버 DB 연결
        (
            f"{center}는 {zone}을 포함한다. "
            f"{server1}는 {random.choice(server_dbms_phrases).format(dbms=dbms1)}."
        ),
        # C: 위치/소속 중심 (server1 또는 server2 랜덤)
        (
            f"{random.choice(zone_run_phrases).format(zone=zone, server=random.choice([server1, server2]))}. "
            f"{random.choice(server_group_phrases).format(server=random.choice([server1, server2]), sg=sg)} "
            f"{random.choice(server_dbms_phrases).format(dbms=dbms1)}."
        ),
    ]

    text = random.choice(templates)

    ents = ent_map(
        [
            ("Corporation", corp),
            ("Center", center),
            ("NetworkZone", zone),
            ("NetworkDevice", dev1),
            ("Server", server1),
            ("Server", server2),
            ("SystemGroup", sg),
            ("DBMS", dbms1),
            ("ExternalSystem", ext1),
            ("Interface", iface1),
        ]
    )

    rels = [
        rel("HAS_CENTER", corp, center),
        rel("HAS_ZONE", center, zone),
        rel("HAS_DEVICE", center, dev1),
        rel("IN_ZONE", server1, zone),
        rel("IN_ZONE", server2, zone),
        rel("IN_GROUP", server1, sg),
        rel("CONNECTED_TO", server1, dbms1),
        rel("CONNECTED_TO", server2, dbms1),
        rel("CONNECTED_TO", ext1, iface1),
        rel("IN_ZONE", iface1, zone),
    ]

    # --- force include all relation mentions into text
    fact_lines = []
    for item in rels:
        rtype, h, t = _parse_relation_item(item)
        fact_lines.append(rel_to_sentence(rtype, h, t))
    text = text + " " + " ".join(fact_lines)
    text = re.sub(r"\s+", " ", text).strip()

    return make_example(text, ents, rels)


EXT_PHRASES = [
    "{ext}과 연동된다",
    "{ext}과 연계된다",
    "{ext}를 통해 통신한다",
    "{ext} 연계 구간이다",
    "{ext} 호출이 발생한다",
    "{ext}과의 외부 연동이 구성되어 있다",
    "{ext}을 경유해 연동된다",
]


def gen_multi_relpair_rich_2(noise_ratio: float) -> Dict[str, Any]:
    corp = materialize("Corporation", choice("Corporation"), noise_ratio)
    center = materialize("Center", choice("Center"), noise_ratio)
    zone1 = materialize("NetworkZone", choice("NetworkZone"), noise_ratio)
    zone2 = materialize("NetworkZone", choice("NetworkZone"), noise_ratio)

    # zone1과 zone2가 같은 문자열이면 다시 뽑기
    tries = 0
    while zone2 == zone1 and tries < 10:
        zone2 = materialize("NetworkZone", choice("NetworkZone"), noise_ratio)
        tries += 1

    sg1 = materialize("SystemGroup", choice("SystemGroup"), noise_ratio)
    sg2 = materialize("SystemGroup", choice("SystemGroup"), noise_ratio)

    # sg 중복도 최소화
    tries = 0
    while sg2 == sg1 and tries < 10:
        sg2 = materialize("SystemGroup", choice("SystemGroup"), noise_ratio)
        tries += 1

    server1 = materialize("Server", vary_server_name(rand_server()), noise_ratio)
    server2 = materialize("Server", vary_server_name(rand_server()), noise_ratio)
    dbms1 = materialize("DBMS", choice("DBMS"), noise_ratio)
    dbms2 = materialize("DBMS", choice("DBMS"), noise_ratio)

    tries = 0
    while dbms2 == dbms1 and tries < 10:
        dbms2 = materialize("DBMS", choice("DBMS"), noise_ratio)
        tries += 1

    iface = materialize("Interface", choice("Interface"), noise_ratio)
    ext = materialize("ExternalSystem", choice("ExternalSystem"), noise_ratio)
    dev = materialize("NetworkDevice", choice("NetworkDevice"), noise_ratio)
    belongs_phrases = [
        "{server}는 {group} 소속으로 운영되고",
        "{server}는 {group} 산하에서 운영되며",
        "{server}는 {group}에 속해 운영되고",
        "{group}에 속한 {server}는",
        "{group} 산하의 {server}는",
    ]
    connect_phrases = [
        "{dbms}와 연결되어 있다",
        "{dbms}에 접속한다",
        "{dbms}를 사용한다",
        "{dbms} DB와 연동된다",
    ]
    zone_prefixes = [
        "{zone}에서",
        "{zone} 내에서",
        "{zone} 구간에서",
        "{zone} 영역에서",
        "{zone} 네트워크에서",
    ]
    ext_iface_phrases = [
        "{ext}은 {iface}를 통해 연동된다",
        "{ext}은 {iface} 채널로 연계된다",
        "{ext}과 {iface}가 연동된다",
        "{ext}은 {iface} 인터페이스로 연결된다",
        "{iface}를 통해 {ext} 연동이 수행된다",
    ]
    iface_loc_phrases = [
        "{iface}는 {zone}에 위치한다",
        "{iface}는 {zone}에 배치된다",
        "{iface}는 {zone} 내에 존재한다",
        "{zone}에는 {iface}가 위치한다",
    ]

    ext_ctx = ""
    if random.random() < 0.5:
        ext_ctx = external_ctx(ext) + ". "

    text = (
        f"{corp}의 {center}에는 {zone1}과 {zone2}가 구성되어 있다. "
        f"{center}에는 {dev}가 설치되어 있다. "
        f"{random.choice(zone_prefixes).format(zone=zone1)} "
        f"{random.choice(belongs_phrases).format(server=server1, group=sg1)} "
        f"{random.choice(connect_phrases).format(dbms=dbms1)}. "
        f"{random.choice(zone_prefixes).format(zone=zone2)} "
        f"{random.choice(belongs_phrases).format(server=server2, group=sg2)} "
        f"{random.choice(connect_phrases).format(dbms=dbms2)}. "
        f"{ext_ctx}"
        f"{random.choice(ext_iface_phrases).format(ext=ext, iface=iface)}. "
        f"{random.choice(iface_loc_phrases).format(iface=iface, zone=zone1)}."
    )

    ents = ent_map(
        [
            ("Corporation", corp),
            ("Center", center),
            ("NetworkZone", zone1),
            ("NetworkZone", zone2),
            ("NetworkDevice", dev),
            ("Server", server1),
            ("SystemGroup", sg1),
            ("DBMS", dbms1),
            ("Server", server2),
            ("SystemGroup", sg2),
            ("DBMS", dbms2),
            ("ExternalSystem", ext),
            ("Interface", iface),
        ]
    )

    rels = [
        rel("HAS_CENTER", corp, center),
        rel("HAS_ZONE", center, zone1),
        rel("HAS_ZONE", center, zone2),
        rel("HAS_DEVICE", center, dev),
        rel("IN_ZONE", server1, zone1),
        rel("IN_GROUP", server1, sg1),
        rel("CONNECTED_TO", server1, dbms1),
        rel("IN_ZONE", server2, zone2),
        rel("IN_GROUP", server2, sg2),
        rel("CONNECTED_TO", server2, dbms2),
        rel("CONNECTED_TO", ext, iface),
        rel("IN_ZONE", iface, zone1),
    ]
    # --- force include all relation mentions into text
    fact_lines = []
    for item in rels:
        rtype, h, t = _parse_relation_item(item)
        fact_lines.append(rel_to_sentence(rtype, h, t))
    text = text + " " + " ".join(fact_lines)
    text = re.sub(r"\s+", " ", text).strip()

    return make_example(text, ents, rels)


def gen_multi_relpair_rich_3(noise_ratio: float) -> Dict[str, Any]:
    # Diagram/HAS_COVERS까지 포함해서 "상위 포함관계"도 같이 강화
    diagram = materialize("Diagram", "구성도", noise_ratio)
    corp = materialize("Corporation", choice("Corporation"), noise_ratio)
    center = materialize("Center", choice("Center"), noise_ratio)
    zone = materialize("NetworkZone", choice("NetworkZone"), noise_ratio)

    sg = materialize("SystemGroup", choice("SystemGroup"), noise_ratio)
    server = materialize("Server", vary_server_name(rand_server()), noise_ratio)
    dbms = materialize("DBMS", choice("DBMS"), noise_ratio)
    iface = materialize("Interface", choice("Interface"), noise_ratio)
    ext = materialize("ExternalSystem", choice("ExternalSystem"), noise_ratio)
    dev = materialize("NetworkDevice", choice("NetworkDevice"), noise_ratio)
    diagram_cover_phrases = [
        "{diagram}는 {corp}을 포함한다",
        "{diagram}에는 {corp}이 포함된다",
    ]

    center_zone_phrases = [
        "{center}에는 {zone}이 구성되어 있다",
        "{center}는 {zone}을 포함한다",
        "{zone}은 {center}에 속한다",
    ]

    server_run_phrases = [
        "{zone}에서 {server}가 운영된다",
        "{zone} 내에서 {server}가 구동된다",
        "{server}는 {zone}에 위치해 운영된다",
    ]

    server_group_phrases = [
        "{server}는 {sg} 소속이다",
        "{server}는 {sg} 산하이다",
        "{sg}에 속한 {server}는",
    ]

    dbms_conn_phrases = [
        "{dbms}와 연결되어 있다",
        "{dbms}에 접속한다",
        "{dbms} DB를 사용한다",
    ]

    iface_ext_phrases = [
        "{ext}은 {iface}를 통해 연동된다",
        "{iface}를 통해 {ext} 연동이 수행된다",
        "{ext}과 {iface}가 연계된다",
    ]

    iface_loc_phrases = [
        "{iface}는 {zone}에 위치한다",
        "{iface}는 {zone} 내에 존재한다",
    ]

    templates = [
        (
            f"{random.choice(diagram_cover_phrases).format(diagram=diagram, corp=corp)}. "
            f"{random.choice(center_zone_phrases).format(center=center, zone=zone)}. "
            f"{center}에는 {dev}가 설치되어 있다. "
            f"{random.choice(server_run_phrases).format(zone=zone, server=server)}. "
            f"{random.choice(server_group_phrases).format(server=server, sg=sg)} "
            f"{random.choice(dbms_conn_phrases).format(dbms=dbms)}. "
            f"{random.choice(iface_ext_phrases).format(ext=ext, iface=iface)}. "
            f"{random.choice(iface_loc_phrases).format(iface=iface, zone=zone)}."
        ),
        # B: 포함관계 강조
        (
            f"{random.choice(diagram_cover_phrases).format(diagram=diagram, corp=corp)}. "
            f"{random.choice(center_zone_phrases).format(center=center, zone=zone)}. "
            f"{server}는 {random.choice(dbms_conn_phrases).format(dbms=dbms)}. "
            f"{random.choice(iface_ext_phrases).format(ext=ext, iface=iface)}."
        ),
        # C: 위치/소속 중심
        (
            f"{random.choice(server_run_phrases).format(zone=zone, server=server)}. "
            f"{random.choice(server_group_phrases).format(server=server, sg=sg)} "
            f"{random.choice(dbms_conn_phrases).format(dbms=dbms)}. "
            f"{random.choice(iface_loc_phrases).format(iface=iface, zone=zone)}."
        ),
    ]

    text = random.choice(templates)

    ents = ent_map(
        [
            ("Diagram", diagram),
            ("Corporation", corp),
            ("Center", center),
            ("NetworkZone", zone),
            ("NetworkDevice", dev),
            ("Server", server),
            ("SystemGroup", sg),
            ("DBMS", dbms),
            ("ExternalSystem", ext),
            ("Interface", iface),
        ]
    )

    rels = [
        rel("HAS_COVERS", diagram, corp),
        rel("HAS_CENTER", corp, center),
        rel("HAS_ZONE", center, zone),
        rel("HAS_DEVICE", center, dev),
        rel("IN_ZONE", server, zone),
        rel("IN_GROUP", server, sg),
        rel("CONNECTED_TO", server, dbms),
        rel("CONNECTED_TO", ext, iface),
        rel("IN_ZONE", iface, zone),
    ]

    fact_lines = []
    for item in rels:
        rtype, h, t = _parse_relation_item(item)
        fact_lines.append(rel_to_sentence(rtype, h, t))
    text = text + " " + " ".join(fact_lines)
    text = re.sub(r"\s+", " ", text).strip()

    return make_example(text, ents, rels)


MULTI_GENERATORS: List[Callable[[float], Dict[str, Any]]] = [
    gen_multi_relpair_rich_1,
    gen_multi_relpair_rich_2,
    gen_multi_relpair_rich_3,
]


# -----------------------------
# COUNTERS (디버그용)
# -----------------------------
def extract_counts(ex: Dict[str, Any]) -> Tuple[Counter, Counter]:
    rel_cnt = Counter()
    lab_cnt = Counter()
    ents = ex["output"]["entities"]
    rels = ex["output"]["relations"]

    for lab, mentions in ents.items():
        lab_cnt[lab] += len(mentions)

    for item in rels:
        rtype, _, _ = _parse_relation_item(item)
        rel_cnt[rtype] += 1

    return rel_cnt, lab_cnt


# -----------------------------
# MAIN
# -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="output dir (recommended)")
    ap.add_argument("--n", type=int, default=4000)
    ap.add_argument("--val_ratio", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=42)

    # 구성 비율
    ap.add_argument(
        "--multi_ratio", type=float, default=0.7, help="멀티(관계쌍 많은) 샘플 비율"
    )
    ap.add_argument(
        "--hard_ratio",
        type=float,
        default=0.3,
        help="hard-negative(라벨 고정) 샘플 비율",
    )
    ap.add_argument("--noise_ratio", type=float, default=0.15)

    ap.add_argument(
        "--max_tries", type=int, default=50, help="invalid 샘플 재시도 횟수"
    )
    args = ap.parse_args()

    if abs((args.multi_ratio + args.hard_ratio) - 1.0) > 1e-6:
        raise SystemExit("multi_ratio + hard_ratio must be 1.0 (예: 0.7 + 0.3)")

    random.seed(args.seed)

    samples: List[Dict[str, Any]] = []
    dropped = Counter()
    rel_counter = Counter({t: 0 for t in REL_TYPES})
    label_counter = Counter({l: 0 for l in LABELS})

    for _ in range(args.n):
        ex = None
        for _try in range(args.max_tries):
            if random.random() < args.multi_ratio:
                cand = random.choice(MULTI_GENERATORS)(args.noise_ratio)
            else:
                cand = random.choice(HARD_GENERATORS)(args.noise_ratio)

            ok, reason = validate_example(cand)
            if ok:
                ex = cand
                break
            dropped[reason] += 1

        if ex is None:
            dropped["giveup"] += 1
            continue

        r_add, l_add = extract_counts(ex)
        rel_counter.update(r_add)
        label_counter.update(l_add)
        samples.append(ex)

    random.shuffle(samples)
    split = int(len(samples) * (1 - args.val_ratio))
    train, val = samples[:split], samples[split:]

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_path = out_dir / "train_add.jsonl"
    val_path = out_dir / "val_add.jsonl"

    with open(train_path, "w", encoding="utf-8") as f:
        for s in train:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    with open(val_path, "w", encoding="utf-8") as f:
        for s in val:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print("Saved add dataset (GLiNER2 format: input/output):")
    print(f" - train_add: {train_path} ({len(train)})")
    print(f" - val_add  : {val_path} ({len(val)})")

    print("\n[Relation counts in add]")
    for k in REL_TYPES:
        print(f" - {k}: {rel_counter[k]}")

    if dropped:
        print("\n[Dropped reasons]")
        for k, v in dropped.most_common():
            print(f" - {k}: {v}")

    print("\n[Settings]")
    print(f" - n: {args.n}")
    print(f" - val_ratio: {args.val_ratio}")
    print(f" - multi_ratio: {args.multi_ratio}")
    print(f" - hard_ratio: {args.hard_ratio}")
    print(f" - noise_ratio: {args.noise_ratio}")
    print(f" - seed: {args.seed}")


if __name__ == "__main__":
    main()
