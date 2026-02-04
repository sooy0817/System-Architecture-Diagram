import json
import random
import argparse
from pathlib import Path


def read_jsonl(p: Path):
    out = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def write_jsonl(p: Path, items):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        for x in items:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old_train", required=True)
    ap.add_argument("--old_val", required=True)
    ap.add_argument("--new_train", required=True)
    ap.add_argument("--new_val", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--val_ratio", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)

    items = []
    items += read_jsonl(Path(args.old_train))
    items += read_jsonl(Path(args.old_val))
    items += read_jsonl(Path(args.new_train))
    items += read_jsonl(Path(args.new_val))

    random.shuffle(items)
    split = int(len(items) * (1 - args.val_ratio))
    train, val = items[:split], items[split:]

    out_dir = Path(args.out_dir)
    write_jsonl(out_dir / "train.jsonl", train)
    write_jsonl(out_dir / "val.jsonl", val)

    print("✅ merged+split done")
    print(f" - total: {len(items)}")
    print(f" - train: {len(train)} -> {out_dir / 'train.jsonl'}")
    print(f" - val  : {len(val)} -> {out_dir / 'val.jsonl'}")


if __name__ == "__main__":
    main()
