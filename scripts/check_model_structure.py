#!/usr/bin/env python
"""Check GLiNER2 model structure to understand layer names"""

import sys

sys.path.insert(0, "..")

from gliner2 import GLiNER

# Load model
print("Loading model...")
model = GLiNER.from_pretrained("urchade/gliner_small_news-v2.1")

print("\n=== Top-level modules ===")
for name, module in model.named_children():
    print(f"{name}: {type(module).__name__}")

print("\n=== All module paths (first 30) ===")
for i, (name, module) in enumerate(model.named_modules()):
    if i >= 30:
        print("...")
        break
    print(f"{name}: {type(module).__name__}")

print("\n=== Linear layers (first 20) ===")
import torch.nn as nn

count = 0
for name, module in model.named_modules():
    if isinstance(module, nn.Linear):
        print(f"{name}: Linear({module.in_features}, {module.out_features})")
        count += 1
        if count >= 20:
            print(
                f"... and {sum(1 for _, m in model.named_modules() if isinstance(m, nn.Linear)) - count} more"
            )
            break
