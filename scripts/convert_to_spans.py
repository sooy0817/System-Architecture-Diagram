# scripts/convert_v4_1_to_spans.py
import json
import argparse
from pathlib import Path
from collections import Counter


def find_span(text: str, needle: str):
    """Return (start, end) for first occurrence, else None."""
    i = text.find(needle)
    if i < 0:
        return None
    return (i, i + len(needle))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_path", required=True, help="v4.1 train/val jsonl")
    ap.add_argument("--out_path", required=True, help="span jsonl output")
    args = ap.parse_args()

    in_path = Path(args.in_path)
    out_path = Path(args.out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    stats = Counter()
    skipped_reasons = Counter()

    with (
        in_path.open("r", encoding="utf-8") as f_in,
        out_path.open("w", encoding="utf-8") as f_out,
    ):
        for line_no, line in enumerate(f_in, 1):
            line = line.strip()
            if not line:
                continue

            ex = json.loads(line)
            text = ex["input"]
            ents = ex["output"]["entities"]
            rels = ex["output"]["relations"]

            # 1) relation에 등장하는 엔티티부터 스팬 확보
            mention_map = {}  # (label, text) -> (start, end)
            ok = True

            for r in rels:
                h = r["head"]
                t = r["tail"]
                for side in (h, t):
                    key = (side["label"], side["text"])
                    if key in mention_map:
                        continue
                    sp = find_span(text, side["text"])
                    if sp is None:
                        ok = False
                        skipped_reasons["span_not_found_in_relation"] += 1
                        break
                    mention_map[key] = sp
                if not ok:
                    break

            if not ok:
                stats["skipped"] += 1
                continue

            # 2) entities에 있는 나머지도 스팬 확보 (중복은 dedupe)
            for label, texts in ents.items():
                for et in texts:
                    key = (label, et)
                    if key in mention_map:
                        continue
                    sp = find_span(text, et)
                    if sp is None:
                        # 엔티티는 있는데 텍스트에 없으면 스킵 (노이즈/공백 변형 때문)
                        ok = False
                        skipped_reasons["span_not_found_in_entities"] += 1
                        break
                    mention_map[key] = sp
                if not ok:
                    break

            if not ok:
                stats["skipped"] += 1
                continue

            # 3) 멘션 리스트 생성
            mentions = []
            for (label, et), (s, e) in mention_map.items():
                mentions.append({"label": label, "text": et, "start": s, "end": e})

            # 4) relation도 head/tail에 span을 붙여서 저장
            span_rels = []
            for r in rels:
                h = r["head"]
                t = r["tail"]
                hs, he = mention_map[(h["label"], h["text"])]
                ts, te = mention_map[(t["label"], t["text"])]
                span_rels.append(
                    {
                        "type": r["type"],
                        "head": {
                            "label": h["label"],
                            "text": h["text"],
                            "start": hs,
                            "end": he,
                        },
                        "tail": {
                            "label": t["label"],
                            "text": t["text"],
                            "start": ts,
                            "end": te,
                        },
                    }
                )

            # 5) 최종 포맷(권장): text/entities/relations
            out_ex = {"text": text, "entities": mentions, "relations": span_rels}

            f_out.write(json.dumps(out_ex, ensure_ascii=False) + "\n")
            stats["kept"] += 1

    print("✅ Convert done")
    print(dict(stats))
    if skipped_reasons:
        print("Skipped reasons:")
        for k, v in skipped_reasons.most_common():
            print(f" - {k}: {v}")


if __name__ == "__main__":
    main()
