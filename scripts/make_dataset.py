# scripts/make_dataset_v2.py
import json
import random
import argparse
from pathlib import Path

# -----------------------------
# CONFIG
# -----------------------------
RELATIONS = [
    "HAS_CENTER",
    "HAS_ZONE",
    "IN_ZONE",
    "IN_GROUP",
    "HAS_DEVICE",
    "CONNECTED_TO",
]

LABELS = [
    "Corporation",
    "Center",
    "NetworkZone",
    "ServerGroup",
    "SystemGroup",
    "Server",
    "DBMS",
    "Interface",
    "ExternalSystem",
    "NetworkDevice",
    "GSLB",
    "Line",
]

# -----------------------------
# VOCAB (요약 버전 – 네 JSON 그대로 옮겨도 됨)
# -----------------------------
VOCAB = {
    "Corporation": ["은행", "중앙회"],
    "Center": ["의왕센터", "안성센터", "AWS센터"],
    "NetworkZone": ["내부망", "영업점망", "대외망", "사용자망"],
    "ServerGroup": ["발급공통 AP", "발급공통 DB", "CA DB"],
    "SystemGroup": ["인증 시스템", "결제 시스템"],
    "DBMS": ["ORACLE", "TIBERO", "MS_SQL"],
    "Interface": ["EAI", "NGW", "IGW", "MFT", "FOS", "영업점MCA"],
    "ExternalSystem": ["휴대폰본인확인 nice", "금융결제원"],
    "NetworkDevice": ["ISW 라우터", "IRT 라우터"],
    "GSLB": ["내부 GSLB", "외부 GSLB"],
}


# -----------------------------
# HELPERS
# -----------------------------
def rand_id(prefix="nbef"):
    return f"{prefix}{random.randint(10, 99)}"


def make_example(text, entities, relations):
    return {
        "input": text,
        "output": {
            "entities": entities,
            "relations": relations,
        },
    }


# -----------------------------
# TEMPLATE GENERATORS
# -----------------------------
def gen_center_zone():
    c = random.choice(VOCAB["Center"])
    z = random.choice(VOCAB["NetworkZone"])
    text = f"{c}는 {z}을 포함한다."
    return make_example(
        text,
        {
            "Center": [c],
            "NetworkZone": [z],
        },
        [{"HAS_ZONE": {"head": c, "tail": z}}],
    )


def gen_server_in_zone():
    z = random.choice(VOCAB["NetworkZone"])
    s = rand_id("nbef")
    text = f"{s} 서버는 {z}에 위치한다."
    return make_example(
        text,
        {
            "Server": [s],
            "NetworkZone": [z],
        },
        [{"IN_ZONE": {"head": s, "tail": z}}],
    )


def gen_servergroup():
    sg = random.choice(VOCAB["ServerGroup"])
    s = rand_id("nbef")
    text = f"{sg}에는 {s}가 포함된다."
    return make_example(
        text,
        {
            "ServerGroup": [sg],
            "Server": [s],
        },
        [{"IN_GROUP": {"head": s, "tail": sg}}],
    )


def gen_external_connection():
    ext = random.choice(VOCAB["ExternalSystem"])
    iface = random.choice(VOCAB["Interface"])
    text = f"{ext}는 {iface}를 통해 연동된다."
    return make_example(
        text,
        {
            "ExternalSystem": [ext],
            "Interface": [iface],
        },
        [{"CONNECTED_TO": {"head": ext, "tail": iface}}],
    )


def gen_device_install():
    c = random.choice(VOCAB["Center"])
    d = random.choice(VOCAB["NetworkDevice"] + VOCAB["GSLB"])
    text = f"{d}가 {c}에 설치되어 있다."
    return make_example(
        text,
        {
            "Center": [c],
            "NetworkDevice": [d] if "라우터" in d else [],
            "GSLB": [d] if "GSLB" in d else [],
        },
        [{"HAS_DEVICE": {"head": c, "tail": d}}],
    )


GENERATORS = [
    gen_center_zone,
    gen_server_in_zone,
    gen_servergroup,
    gen_external_connection,
    gen_device_install,
]


# -----------------------------
# MAIN
# -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--val_ratio", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)

    samples = []
    for _ in range(args.n):
        fn = random.choice(GENERATORS)
        samples.append(fn())

    random.shuffle(samples)

    split = int(len(samples) * (1 - args.val_ratio))
    train, val = samples[:split], samples[split:]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    with open(out.with_name("train.jsonl"), "w", encoding="utf-8") as f:
        for s in train:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    with open(out.with_name("val.jsonl"), "w", encoding="utf-8") as f:
        for s in val:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"train: {len(train)}, val: {len(val)}")


if __name__ == "__main__":
    main()
