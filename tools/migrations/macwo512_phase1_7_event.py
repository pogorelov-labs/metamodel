"""MACWO-517 (Phase 1.7): Delete the orphan ``event`` entity_kind.

The ``event`` entity_kind has no metamodel_level, zero attributes, and is
referenced only by two stub relations in the catalog
(``rel_event_emitted_by_operation``, ``rel_operation_emits_event``). It was
identified as a half-orphan during the metamodel audit (MACWO-512).

Operations:
1. Delete entity_kind ``event`` from ``model/metamodel.yaml``.
2. Delete the two catalog relations that reference it from
   ``model/relation_catalog.yaml``.
3. Drop any inverse pointer that referenced one of the deleted relations.

Idempotent.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METAMODEL_PATH = REPO_ROOT / "model" / "metamodel.yaml"
RELATION_CATALOG_PATH = REPO_ROOT / "model" / "relation_catalog.yaml"

ENTITY_TO_REMOVE = "event"
RC_RELATIONS_TO_DELETE = {
    "rel_event_emitted_by_operation",
    "rel_operation_emits_event",
}


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_yaml(path: Path, data) -> None:
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, width=120)


def main() -> int:
    mm = load_yaml(METAMODEL_PATH)
    rc = load_yaml(RELATION_CATALOG_PATH)

    mm["entity_kinds"] = [
        e for e in mm["entity_kinds"] if e["id"] != ENTITY_TO_REMOVE
    ]
    # Sanity: also drop any mm relation_kinds that reference the deleted entity
    # (there should be none, but stay safe).
    mm["relation_kinds"] = [
        r
        for r in mm["relation_kinds"]
        if r.get("from_kind") != ENTITY_TO_REMOVE
        and r.get("to_kind") != ENTITY_TO_REMOVE
    ]

    rels = rc["relation_catalog"]["relations"]
    rels = [r for r in rels if r["id"] not in RC_RELATIONS_TO_DELETE]
    for rel in rels:
        if rel.get("inverse_relation_id") in RC_RELATIONS_TO_DELETE:
            rel["inverse_relation_id"] = None
            rel["has_inverse"] = False
    rc["relation_catalog"]["relations"] = rels

    dump_yaml(METAMODEL_PATH, mm)
    dump_yaml(RELATION_CATALOG_PATH, rc)
    print("MACWO-517 phase 1.7 migration applied:")
    print(f"  entity_kinds:        {len(mm['entity_kinds'])}")
    print(f"  mm.relation_kinds:   {len(mm['relation_kinds'])}")
    print(f"  rc.relations:        {len(rc['relation_catalog']['relations'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
