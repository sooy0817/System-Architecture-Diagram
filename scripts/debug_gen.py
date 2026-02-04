#!/usr/bin/env python
import sys
import os

os.chdir(r"C:\Users\suyeon\graph_lang\scripts")

# make_dataset_v4_1.py를 직접 import해서 실행
import random
from collections import Counter
from make_dataset_v4_1 import (
    REL_TYPES,
    LABELS,
    gen_has_center,
    gen_has_zone,
    validate_example,
    spanify_example,
)

random.seed(42)

print("=== 단일 샘플 생성 테스트 ===")
for i in range(5):
    print(f"\n테스트 {i + 1}:")
    ex = gen_has_center(0.12)
    print(f"  텍스트: {ex['input']}")

    ok, reason = validate_example(ex)
    print(f"  검증: {ok} ({reason})")

    if ok:
        span_ex = spanify_example(ex)
        if span_ex:
            print(
                f"  ✅ Spanify 성공! entities={len(span_ex['entities'])}, relations={len(span_ex['relations'])}"
            )
        else:
            print(f"  ❌ Spanify 실패!")
    else:
        print(f"  ❌ 검증 실패: {reason}")
