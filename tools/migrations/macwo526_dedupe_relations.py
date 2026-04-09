"""MACWO-526: Dedupe relations that rendered as duplicate edges downstream.

Eight relations in the post-MACWO-521 promotion shadowed existing inverse
pairs with a third "has_X"-style relation that had ``inverse=None``. In the
rbank-atlas Metamodel Reference graph they rendered as extra edges between
the same (from, to) pair on top of the legitimate inverse pair, visually
duplicating the connection.

Each removal leaves an intact forward/reverse inverse pair in place:

| Pair                                       | Removed (shadow)                        |
|--------------------------------------------|-----------------------------------------|
| business_action  ↔ business_operation      | rel_operation_has_action                |
| api              ↔ api_method              | rel_api_has_method                      |
| api_method       ↔ api_method_parameter    | rel_api_method_has_parameter            |
| data_object      ↔ data_product            | rel_data_product_has_data_object        |
| component        ↔ it_system               | rel_it_system_has_component             |
| business_process ↔ value_stream_stage      | rel_value_stream_stage_implements_process |
| business_entity  ↔ business_process        | rel_process_serves_business_entity      |
| value_stream     ↔ value_stream_stage      | rel_value_stream_has_stage              |

Idempotent.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METAMODEL_PATH = REPO_ROOT / "model" / "metamodel.yaml"
RELATION_CATALOG_PATH = REPO_ROOT / "model" / "relation_catalog.yaml"

RELATIONS_TO_REMOVE: set[str] = {
    "rel_operation_has_action",
    "rel_api_has_method",
    "rel_api_method_has_parameter",
    "rel_data_product_has_data_object",
    "rel_it_system_has_component",
    "rel_value_stream_stage_implements_process",
    "rel_process_serves_business_entity",
    "rel_value_stream_has_stage",
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

    before_mm = len(mm["relation_kinds"])
    before_rc = len(rc["relation_catalog"]["relations"])

    mm["relation_kinds"] = [
        r for r in mm["relation_kinds"] if r["id"] not in RELATIONS_TO_REMOVE
    ]
    rc["relation_catalog"]["relations"] = [
        r
        for r in rc["relation_catalog"]["relations"]
        if r["id"] not in RELATIONS_TO_REMOVE
    ]
    # Drop any inverse pointers that referenced a removed relation.
    for rel in rc["relation_catalog"]["relations"]:
        if rel.get("inverse_relation_id") in RELATIONS_TO_REMOVE:
            rel["inverse_relation_id"] = None
            rel["has_inverse"] = False

    dump_yaml(METAMODEL_PATH, mm)
    dump_yaml(RELATION_CATALOG_PATH, rc)

    after_mm = len(mm["relation_kinds"])
    after_rc = len(rc["relation_catalog"]["relations"])
    print(
        f"MACWO-526 dedupe applied: "
        f"mm.relation_kinds {before_mm} -> {after_mm} (-{before_mm - after_mm}), "
        f"rc.relations {before_rc} -> {after_rc} (-{before_rc - after_rc})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
