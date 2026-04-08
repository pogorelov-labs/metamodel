"""MACWO-520 (Phase 4): Resolve 3 mm/rc category contradictions.

Three relation_kinds had a different ``category`` in
``model/metamodel.yaml`` (the canonical core ontology) and in
``model/relation_catalog.yaml`` (the profile overlay). Per the cleanup
decision, ``metamodel.yaml`` is the authoritative source for relation
metadata, so the catalog values are brought in line with mm:

| relation_id                    | rc was       | rc becomes    |
|--------------------------------|--------------|---------------|
| rel_consumer_consumes_value    | association  | consumption   |
| rel_org_unit_has_role          | ownership    | composition   |
| rel_process_serves_entity      | association  | service       |

Idempotent.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
RELATION_CATALOG_PATH = REPO_ROOT / "model" / "relation_catalog.yaml"

CATEGORY_FIXES = {
    "rel_consumer_consumes_value": "consumption",
    "rel_org_unit_has_role": "composition",
    "rel_process_serves_entity": "service",
}


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_yaml(path: Path, data) -> None:
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, width=120)


def main() -> int:
    rc = load_yaml(RELATION_CATALOG_PATH)
    patched = 0
    for rel in rc["relation_catalog"]["relations"]:
        target = CATEGORY_FIXES.get(rel["id"])
        if target is None:
            continue
        if rel.get("category") != target:
            rel["category"] = target
            patched += 1
    dump_yaml(RELATION_CATALOG_PATH, rc)
    print(f"MACWO-520 phase 4 migration applied: {patched} category fixes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
