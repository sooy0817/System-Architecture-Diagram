import json
import random
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--train_out", required=True)
parser.add_argument("--val_out", required=True)
parser.add_argument("--val_ratio", type=float, default=0.1)
parser.add_argument("--seed", type=int, default=42)
args = parser.parse_args()

with open(args.input, encoding="utf-8") as f:
    lines = f.readlines()

random.seed(args.seed)
random.shuffle(lines)

n_val = int(len(lines) * args.val_ratio)
val = lines[:n_val]
train = lines[n_val:]

with open(args.train_out, "w", encoding="utf-8") as f:
    f.writelines(train)

with open(args.val_out, "w", encoding="utf-8") as f:
    f.writelines(val)

print(f"TRAIN: {len(train)}")
print(f"VAL  : {len(val)}")
