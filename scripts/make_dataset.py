# scripts/make_dataset_v4_1.py
import json
import random
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Callable, Any, Set

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
# RELATION DIRECTION CONSTRAINTS (너랑 합의했던 방향 고정)
# (head_label, rel_type, tail_label)
# -----------------------------
ALLOWED_TRIPLES = {
    ("Diagram", "HAS_COVERS", "Corporation"),
    ("Corporation", "HAS_CENTER", "Center"),
    ("Center", "HAS_ZONE", "NetworkZone"),
    ("Center", "HAS_DEVICE", "NetworkDevice"),
    ("Server", "IN_ZONE", "NetworkZone"),
    ("SystemGroup", "IN_ZONE", "NetworkZone"),
    ("Interface", "IN_ZONE", "NetworkZone"),
    ("ExternalSystem", "IN_ZONE", "NetworkZone"),
    ("Server", "IN_GROUP", "SystemGroup"),
    ("Interface", "IN_GROUP", "SystemGroup"),
    ("ExternalSystem", "IN_GROUP", "SystemGroup"),
}

CONNECTED_UNDIRECTED = {
    ("NetworkDevice", "NetworkDevice"),
    ("NetworkDevice", "Server"),
    ("NetworkDevice", "Interface"),
    ("NetworkDevice", "ExternalSystem"),
    ("Server", "DBMS"),
    ("Server", "NetworkDevice"),
    ("Server", "Interface"),
    ("Server", "ExternalSystem"),
    ("Server", "Server"),
    ("Interface", "Interface"),
    ("Interface", "ExternalSystem"),
    ("ExternalSystem", "ExternalSystem"),
    ("DBMS", "DBMS"),
}

# -----------------------------
# VOCAB
# -----------------------------
VOCAB = {
    "Corporation": ["은행", "중앙회"],
    "Center": ["의왕센터", "안성센터", "AWS센터"],
    "NetworkZone": [
        "내부망",
        "영업점망",
        "대외망",
        "사용자망",
        "인터넷망(DMZ)",
        "대외연계망",
    ],
    "ServerGroup": [
        "발급공통 AP",
        "발급공통 DB",
        "CA DB",
        "인증 AP",
        "계정계 AP",
        "카드 AP",
    ],
    "SystemGroup": ["인증 시스템", "결제 시스템", "계정계 시스템", "카드 시스템"],
    "DBMS": ["ORACLE", "TIBERO", "MS_SQL", "POSTGRES"],
    "Interface": ["EAI", "NGW", "IGW", "MFT", "FOS", "영업점MCA", "API_GW"],
    "ExternalSystem": ["휴대폰본인확인 nice", "금융결제원", "KISA", "NICE평가정보"],
    "NetworkDevice": ["ISW 라우터", "IRT 라우터", "FW01 방화벽", "L4 스위치"],
    "GSLB": ["내부 GSLB", "외부 GSLB"],
    "Line": ["KT 회선", "SK브로드밴드 회선", "LGU+ 회선"],
}


# -----------------------------
# HELPERS
# -----------------------------
def one_of(*xs):
    return random.choice(xs)


def choice(label: str) -> str:
    return random.choice(VOCAB[label])


def is_allowed_relation(head_label: str, rel_type: str, tail_label: str) -> bool:
    if rel_type == "CONNECTED_TO":
        a, b = head_label, tail_label
        return (a, b) in CONNECTED_UNDIRECTED or (b, a) in CONNECTED_UNDIRECTED
    return (head_label, rel_type, tail_label) in ALLOWED_TRIPLES


def rand_server() -> str:
    patterns = [
        lambda: f"nbefsalora{random.randint(1, 99):02}",
        lambda: f"nbefmcap{random.randint(1, 99):02}",
        lambda: f"nbefapi{random.randint(1, 99):02}",
        lambda: f"nbefwas{random.randint(1, 99):02}",
        lambda: f"nbsrv{random.randint(100, 999)}",
    ]
    return random.choice(patterns)()


def ent_map(pairs: List[Tuple[str, str]]) -> Dict[str, List[str]]:
    out = defaultdict(list)
    for lab, txt in pairs:
        if txt and txt not in out[lab]:
            out[lab].append(txt)
    return dict(out)


def rel(
    rel_type: str, head_label: str, head_text: str, tail_label: str, tail_text: str
) -> Dict[str, Any]:
    return {
        "type": rel_type,
        "head": {"text": head_text, "label": head_label},
        "tail": {"text": tail_text, "label": tail_label},
    }


def make_example(
    text: str, entities: Dict[str, List[str]], relations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    entities = {k: v for k, v in entities.items() if v}
    return {"input": text, "output": {"entities": entities, "relations": relations}}


# -----------------------------
# NORMALIZATION NOISE
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

    if label == "ServerGroup":
        if "발급공통" in s:
            return one_of(s, s.replace("발급공통", "발급 공통"))
        return s

    return s


def materialize_entity(label: str, canonical: str, noise_ratio: float) -> str:
    return maybe_noise(canonical, label, noise_ratio)


# -----------------------------
# CONSTRAINT VALIDATOR
# -----------------------------
def validate_example(ex):
    for r in ex["output"]["relations"]:
        t = r["type"]
        hl = r["head"]["label"]
        tl = r["tail"]["label"]

        if t == "CONNECTED_TO":
            a, b = hl, tl
            if (a, b) in CONNECTED_UNDIRECTED or (b, a) in CONNECTED_UNDIRECTED:
                continue
            return False, f"invalid_connected_pair:{hl}<->{tl}"

        if (hl, t, tl) not in ALLOWED_TRIPLES:
            return False, f"invalid_triple:{hl}-{t}-{tl}"
    return True, "ok"


# -----------------------------
# GENERATORS (single)
# -----------------------------
def gen_has_center(noise_ratio: float) -> Dict[str, Any]:
    corp = materialize_entity("Corporation", choice("Corporation"), noise_ratio)
    center = materialize_entity("Center", choice("Center"), noise_ratio)
    text = one_of(
        f"{corp}는 {center}를 운영한다.",
        f"{corp} 산하에 {center}가 있다.",
        f"{corp}는 {center}를 포함한다.",
    )
    entities = ent_map([("Corporation", corp), ("Center", center)])
    relations = [rel("HAS_CENTER", "Corporation", corp, "Center", center)]
    return make_example(text, entities, relations)


def gen_has_zone(noise_ratio: float) -> Dict[str, Any]:
    center = materialize_entity("Center", choice("Center"), noise_ratio)
    zone = materialize_entity("NetworkZone", choice("NetworkZone"), noise_ratio)
    text = one_of(
        f"{center}는 {zone}을 포함한다.",
        f"{center}에는 {zone}이 구성되어 있다.",
    )
    entities = ent_map([("Center", center), ("NetworkZone", zone)])
    relations = [rel("HAS_ZONE", "Center", center, "NetworkZone", zone)]
    return make_example(text, entities, relations)


def gen_in_zone_server(noise_ratio: float) -> Dict[str, Any]:
    zone = materialize_entity("NetworkZone", choice("NetworkZone"), noise_ratio)
    server = materialize_entity("Server", rand_server(), noise_ratio)
    text = one_of(
        f"{server} 서버는 {zone}에 위치한다.",
        f"{zone}에는 {server} 서버가 배치되어 있다.",
    )
    entities = ent_map([("Server", server), ("NetworkZone", zone)])
    relations = [rel("IN_ZONE", "Server", server, "NetworkZone", zone)]
    return make_example(text, entities, relations)


def gen_in_group_server(noise_ratio: float) -> Dict[str, Any]:
    grp = materialize_entity("SystemGroup", choice("SystemGroup"), noise_ratio)
    server = materialize_entity("Server", rand_server(), noise_ratio)
    text = one_of(
        f"{server}는 {grp}에 속한다.",
        f"{grp}에는 {server}가 포함된다.",
    )
    entities = ent_map([("SystemGroup", grp), ("Server", server)])
    relations = [rel("IN_GROUP", "Server", server, "SystemGroup", grp)]
    return make_example(text, entities, relations)


def gen_has_device(noise_ratio: float) -> Dict[str, Any]:
    center = materialize_entity("Center", choice("Center"), noise_ratio)
    dev = materialize_entity("NetworkDevice", choice("NetworkDevice"), noise_ratio)

    text = one_of(
        f"{center}에는 {dev}가 설치되어 있다.",
        f"{dev}가 {center}에 구성되어 있다.",
    )
    entities = ent_map([("Center", center), ("NetworkDevice", dev)])
    relations = [rel("HAS_DEVICE", "Center", center, "NetworkDevice", dev)]
    return make_example(text, entities, relations)


def gen_connected_server_dbms(noise_ratio: float) -> Dict[str, Any]:
    server = materialize_entity("Server", rand_server(), noise_ratio)
    dbms = materialize_entity("DBMS", choice("DBMS"), noise_ratio)
    text = one_of(
        f"{server}는 {dbms}와 연결되어 있다.",
        f"{server} 서버가 {dbms}에 접속한다.",
    )
    entities = ent_map([("Server", server), ("DBMS", dbms)])
    relations = [rel("CONNECTED_TO", "Server", server, "DBMS", dbms)]
    return make_example(text, entities, relations)


def gen_connected_ext_iface(noise_ratio: float) -> Dict[str, Any]:
    ext = materialize_entity("ExternalSystem", choice("ExternalSystem"), noise_ratio)
    iface = materialize_entity("Interface", choice("Interface"), noise_ratio)
    text = one_of(
        f"{ext}는 {iface}를 통해 연동된다.",
        f"{ext} 연동 채널은 {iface}이다.",
    )
    entities = ent_map([("ExternalSystem", ext), ("Interface", iface)])
    relations = [rel("CONNECTED_TO", "ExternalSystem", ext, "Interface", iface)]
    return make_example(text, entities, relations)


def gen_has_covers(noise_ratio: float) -> Dict[str, Any]:
    diagram = materialize_entity(
        "Diagram", "구성도", noise_ratio
    )  # 또는 "구성도1" 같은 고정값
    corp = materialize_entity("Corporation", choice("Corporation"), noise_ratio)
    text = one_of(
        f"{diagram}는 {corp}을 포함한다.",
        f"{diagram} 구성도는 {corp} 범위를 다룬다.",
    )
    entities = ent_map([("Diagram", diagram), ("Corporation", corp)])
    relations = [rel("HAS_COVERS", "Diagram", diagram, "Corporation", corp)]
    return make_example(text, entities, relations)


# -----------------------------
# MULTI GENERATORS (방향 제약 준수)
# -----------------------------
def gen_multi_core_stack(noise_ratio: float) -> Dict[str, Any]:
    corp = materialize_entity("Corporation", choice("Corporation"), noise_ratio)
    center = materialize_entity("Center", choice("Center"), noise_ratio)
    zone = materialize_entity("NetworkZone", choice("NetworkZone"), noise_ratio)

    sg_label = "SystemGroup"
    sg = materialize_entity("SystemGroup", choice("SystemGroup"), noise_ratio)

    server = materialize_entity("Server", rand_server(), noise_ratio)
    dbms = materialize_entity("DBMS", choice("DBMS"), noise_ratio)

    ext = materialize_entity("ExternalSystem", choice("ExternalSystem"), noise_ratio)
    iface = materialize_entity("Interface", choice("Interface"), noise_ratio)

    text = (
        f"{corp}의 {center}에는 {zone}이 구성되어 있고, "
        f"{zone}에서 {server}는 {sg} 소속으로 운영된다. "
        f"{server}는 {dbms}와 연결되어 있다. "
        f"또한 {ext}는 {iface}를 통해 연동되며 {iface}는 {zone}에 위치한다."
    )

    entities = ent_map(
        [
            ("Corporation", corp),
            ("Center", center),
            ("NetworkZone", zone),
            (sg_label, sg),
            ("Server", server),
            ("DBMS", dbms),
            ("ExternalSystem", ext),
            ("Interface", iface),
        ]
    )

    relations = [
        rel("HAS_CENTER", "Corporation", corp, "Center", center),
        rel("HAS_ZONE", "Center", center, "NetworkZone", zone),
        rel("IN_ZONE", "Server", server, "NetworkZone", zone),
        rel("IN_GROUP", "Server", server, "SystemGroup", sg),
        rel("CONNECTED_TO", "Server", server, "DBMS", dbms),
        rel("CONNECTED_TO", "ExternalSystem", ext, "Interface", iface),
        rel("IN_ZONE", "Interface", iface, "NetworkZone", zone),
    ]
    return make_example(text, entities, relations)


# -----------------------------
# REGISTRY + BALANCER
# -----------------------------
REGISTRY: Dict[str, List[Callable[[float], Dict[str, Any]]]] = {
    "HAS_CENTER": [gen_has_center],
    "HAS_ZONE": [gen_has_zone],
    "IN_ZONE": [gen_in_zone_server],
    "IN_GROUP": [gen_in_group_server],
    "HAS_DEVICE": [gen_has_device],
    "CONNECTED_TO": [gen_connected_server_dbms, gen_connected_ext_iface],
    "HAS_COVERS": [gen_has_covers],
}

MULTI_GENERATORS = [gen_multi_core_stack]


def extract_counts(ex: Dict[str, Any]) -> Tuple[Counter, Counter]:
    rel_cnt = Counter()
    lab_cnt = Counter()
    ents = ex["output"]["entities"]
    rels = ex["output"]["relations"]
    for lab, mentions in ents.items():
        lab_cnt[lab] += len(mentions)
    for r in rels:
        rel_cnt[r["type"]] += 1
    return rel_cnt, lab_cnt


def pick_primary_relation(rel_counter: Counter) -> str:
    mins = min(rel_counter[t] for t in REL_TYPES)
    candidates = [t for t in REL_TYPES if rel_counter[t] == mins]
    return random.choice(candidates)


def label_benefit(label_counter: Counter, ex: Dict[str, Any]) -> float:
    _, lab_add = extract_counts(ex)
    benefit = 0.0
    for lab, n in lab_add.items():
        benefit += n * (1.0 / (1.0 + label_counter[lab]))
    return benefit


def generate_balanced_sample(
    rel_counter: Counter,
    label_counter: Counter,
    noise_ratio: float,
    multi_ratio: float,
) -> Dict[str, Any]:
    if random.random() < multi_ratio:
        # multi 중에서도 희소 relation/label에 도움 되는 걸 선택
        best = None
        best_score = -1e9
        for fn in MULTI_GENERATORS:
            ex = fn(noise_ratio)
            ok, _ = validate_example(ex)
            if not ok:
                continue
            rel_add, _ = extract_counts(ex)
            score = 0.0
            for t in REL_TYPES:
                if rel_add[t] > 0:
                    score += rel_add[t] * (1.0 / (1.0 + rel_counter[t]))
            score += 0.5 * label_benefit(label_counter, ex)
            if score > best_score:
                best, best_score = ex, score
        if best is not None:
            return best

    primary = pick_primary_relation(rel_counter)
    cands = REGISTRY[primary]

    best = None
    best_benefit = -1e9
    for fn in cands:
        ex = fn(noise_ratio)
        ok, _ = validate_example(ex)
        if not ok:
            continue
        b = label_benefit(label_counter, ex)
        if b > best_benefit:
            best, best_benefit = ex, b

    # fallback (이론상 거의 안 탐)
    if best is None:
        # 아무거나 valid 나올 때까지
        for _ in range(50):
            ex = random.choice(random.choice(list(REGISTRY.values())))(noise_ratio)
            ok, _ = validate_example(ex)
            if ok:
                return ex
        # 그래도 안되면 그냥 마지막 생성본 반환(디버그 목적)
        return ex

    return best


# -----------------------------
# MAIN
# -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--val_ratio", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--multi_ratio", type=float, default=0.30)
    ap.add_argument("--noise_ratio", type=float, default=0.12)
    ap.add_argument(
        "--max_tries", type=int, default=30, help="invalid 샘플 재시도 횟수"
    )
    args = ap.parse_args()

    random.seed(args.seed)

    rel_counter = Counter({t: 0 for t in REL_TYPES})
    label_counter = Counter({l: 0 for l in LABELS})

    samples = []
    dropped = Counter()

    for _ in range(args.n):
        ex = None
        for _try in range(args.max_tries):
            cand = generate_balanced_sample(
                rel_counter=rel_counter,
                label_counter=label_counter,
                noise_ratio=args.noise_ratio,
                multi_ratio=args.multi_ratio,
            )
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

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    train_path = out.with_name("train.jsonl")
    val_path = out.with_name("val.jsonl")

    with open(train_path, "w", encoding="utf-8") as f:
        for s in train:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    with open(val_path, "w", encoding="utf-8") as f:
        for s in val:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print("✅ Saved:")
    print(f" - train: {train_path} ({len(train)})")
    print(f" - val  : {val_path} ({len(val)})")

    print("\n[Relation counts]")
    for k in REL_TYPES:
        print(f" - {k}: {rel_counter[k]}")

    if dropped:
        print("\n[Dropped (constraint violations)]")
        for k, v in dropped.most_common():
            print(f" - {k}: {v}")

    print("\n[Settings]")
    print(f" - multi_ratio: {args.multi_ratio}")
    print(f" - noise_ratio: {args.noise_ratio}")
    print(f" - seed: {args.seed}")


if __name__ == "__main__":
    main()
