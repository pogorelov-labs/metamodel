"""MACWO-521 (Phase 5): Promote catalog-only relations into mm.relation_kinds.

After Phase 1 the metamodel has 91 relations that live in
``model/relation_catalog.yaml`` (the profile overlay) but have no
counterpart in ``model/metamodel.yaml`` (the core ontology). This breaks
the two-layer contract (Rule 1: every catalog relation must have a core
relation_kind).

This migration promotes each of those 91 relations into mm with a minimal
representation:

  - id, name, description, direction
  - from_kind, to_kind, category (copied verbatim — Rule 2 already holds)
  - metamodel_level (derived from the endpoint entities)

Idempotent — re-running on already-promoted catalog relations is a no-op.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METAMODEL_PATH = REPO_ROOT / "model" / "metamodel.yaml"
RELATION_CATALOG_PATH = REPO_ROOT / "model" / "relation_catalog.yaml"

# When endpoints belong to different metamodel levels, prefer the more
# detailed one (the relation can only "live" at the level both endpoints
# already exist in).
LEVEL_RANK = {
    "strategic_view": 0,
    "business_details": 1,
    "data_details": 2,
    "solution_details": 3,
    "component_details": 4,
    "infrastructure_details": 5,
}


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_yaml(path: Path, data) -> None:
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, width=120)


def derive_level(from_entity: dict, to_entity: dict) -> str:
    """Pick the more-detailed metamodel_level of the two endpoints."""
    levels = [
        e.get("metamodel_level")
        for e in (from_entity, to_entity)
        if e and e.get("metamodel_level")
    ]
    if not levels:
        return "business_details"
    levels.sort(key=lambda lvl: LEVEL_RANK.get(lvl, 99), reverse=True)
    return levels[0]


def build_core_relation(rc_rel: dict, entities_by_id: dict) -> dict:
    """Render a minimal mm relation_kind from a rich catalog relation."""
    from_entity = entities_by_id.get(rc_rel.get("from_kind"))
    to_entity = entities_by_id.get(rc_rel.get("to_kind"))
    return {
        "id": rc_rel["id"],
        "name": rc_rel.get("name") or rc_rel["id"],
        "from_kind": rc_rel.get("from_kind"),
        "to_kind": rc_rel.get("to_kind"),
        "metamodel_level": derive_level(from_entity, to_entity),
        "category": rc_rel.get("category"),
        "direction": rc_rel.get("direction") or "directed",
        "description": rc_rel.get("description") or "",
    }


def main() -> int:
    mm = load_yaml(METAMODEL_PATH)
    rc = load_yaml(RELATION_CATALOG_PATH)

    entities_by_id = {e["id"]: e for e in mm["entity_kinds"]}
    mm_rel_ids = {r["id"] for r in mm["relation_kinds"]}
    rc_relations = rc["relation_catalog"]["relations"]

    promoted = []
    for rc_rel in rc_relations:
        if rc_rel["id"] in mm_rel_ids:
            continue
        promoted.append(build_core_relation(rc_rel, entities_by_id))

    if promoted:
        # Append in catalog order so the diff is reviewable; the harness
        # is order-insensitive.
        mm["relation_kinds"].extend(promoted)
        dump_yaml(METAMODEL_PATH, mm)

    print(f"MACWO-521 phase 5 promotion: {len(promoted)} catalog-only relations promoted into mm")
    print(f"  mm.relation_kinds now: {len(mm['relation_kinds'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
