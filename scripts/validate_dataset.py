# scripts/validate_dataset.py
from __future__ import annotations

import argparse
import json
from typing import Dict, List, Optional


ALLOWED_TRIPLES = {
    ("Diagram", "HAS_COVERS", "Corporation"),
    ("Corporation", "HAS_CENTER", "Center"),
    ("Center", "HAS_ZONE", "NetworkZone"),
    ("Center", "HAS_DEVICE", "NetworkDevice"),
    ("NetworkDevice", "CONNECTED_TO", "NetworkDevice"),
    ("NetworkDevice", "CONNECTED_TO", "Server"),
    ("NetworkDevice", "CONNECTED_TO", "Interface"),
    ("NetworkDevice", "CONNECTED_TO", "ExternalSystem"),
    ("Server", "IN_ZONE", "NetworkZone"),
    ("Server", "IN_GROUP", "SystemGroup"),
    ("Server", "CONNECTED_TO", "DBMS"),
    ("Server", "CONNECTED_TO", "NetworkDevice"),
    ("Server", "CONNECTED_TO", "Interface"),
    ("Server", "CONNECTED_TO", "ExternalSystem"),
    ("Server", "CONNECTED_TO", "Server"),
    ("SystemGroup", "IN_ZONE", "NetworkZone"),
    ("Interface", "IN_ZONE", "NetworkZone"),
    ("Interface", "IN_GROUP", "SystemGroup"),
    ("Interface", "CONNECTED_TO", "NetworkDevice"),
    ("Interface", "CONNECTED_TO", "Interface"),
    ("Interface", "CONNECTED_TO", "ExternalSystem"),
    ("ExternalSystem", "IN_ZONE", "NetworkZone"),
    ("ExternalSystem", "IN_GROUP", "SystemGroup"),
    ("ExternalSystem", "CONNECTED_TO", "NetworkDevice"),
    ("ExternalSystem", "CONNECTED_TO", "Interface"),
    ("ExternalSystem", "CONNECTED_TO", "ExternalSystem"),
    ("DBMS", "CONNECTED_TO", "DBMS"),
}


def label_of(entities: Dict[str, List[str]], name: str) -> Optional[str]:
    for label, xs in entities.items():
        if name in xs:
            return label
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", type=str, required=True)
    ap.add_argument("--min_rel", type=int, default=2)
    args = ap.parse_args()

    total = 0
    ok = 0
    bad = 0
    reasons: Dict[str, int] = {}

    with open(args.path, "r", encoding="utf-8") as f:
        for line in f:
            total += 1
            obj = json.loads(line)
            entities = obj["output"]["entities"]
            relations = obj["output"]["relations"]

            if len(relations) < args.min_rel:
                bad += 1
                reasons["min_relations"] = reasons.get("min_relations", 0) + 1
                continue

            violated = False
            for r in relations:
                h = label_of(entities, r["head"])
                t = label_of(entities, r["tail"])
                if h is None or t is None:
                    bad += 1
                    reasons["unknown_entity_in_relation"] = (
                        reasons.get("unknown_entity_in_relation", 0) + 1
                    )
                    violated = True
                    break
                if (h, r["type"], t) not in ALLOWED_TRIPLES:
                    bad += 1
                    key = f"disallowed_triple:{h}-{r['type']}-{t}"
                    reasons[key] = reasons.get(key, 0) + 1
                    violated = True
                    break

            if not violated:
                ok += 1

    print(f"TOTAL: {total}")
    print(f"OK: {ok}")
    print(f"BAD: {bad}")
    if reasons:
        print("REASONS:")
        for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
            print(f" - {k}: {v}")


if __name__ == "__main__":
    main()
