"""MACWO-670: Mirror inverse-pair cardinalities (11) + drop 2 legacy duplicate relations.

The 2026-07 model review found 11 inverse relation pairs in
``model/relation_catalog.yaml`` whose ``source_cardinality`` /
``target_cardinality`` are **not** mirror images — one member of each pair
was copy-pasted without flipping the cardinalities.

For an inverse pair ``R (A->B, sc, tc)`` and ``R' (B->A, sc', tc')`` to be
consistent, the *same real-world side* must carry the *same* cardinality in
both directions, i.e. ``sc == tc'`` and ``tc == sc'``. Every one of the 11
pairs is a whole/part (container/child) relationship, so the invariant is:

    the WHOLE (container) side is ``one``; the PART (child) side is ``many``.

## The 11 pairs (WHOLE ⊃ PART) — erroneous member flipped to mirror

| # | whole ⊃ part                              | correct member (kept)                  | flipped member                         |
|---|-------------------------------------------|----------------------------------------|----------------------------------------|
| 1 | business_domain ⊃ business_capability     | rel_domain_contains_capability         | rel_capability_belongs_to_domain       |
| 2 | organizational_unit ⊃ business_role       | rel_role_belongs_to_org_unit           | rel_org_unit_has_role                  |
| 3 | business_operation ⊃ business_action      | rel_action_part_of_operation           | rel_operation_contains_action          |
| 4 | business_entity ⊃ business_attribute      | rel_attribute_describes_entity         | rel_entity_has_attribute               |
| 5 | job_family ⊃ business_role                | rel_job_family_groups_role             | rel_role_belongs_to_job_family         |
| 6 | data_product ⊃ data_object                | rel_data_object_part_of_product        | rel_data_product_contains_object       |
| 7 | data_object ⊃ data_attribute              | rel_data_attribute_belongs_to_object   | rel_data_object_has_attribute          |
| 8 | it_system ⊃ api                           | rel_api_exposed_by_system              | rel_system_exposes_api                 |
| 9 | api ⊃ api_method                          | rel_api_method_belongs_to_api          | rel_api_contains_method                |
| 10| api_method ⊃ api_method_parameter         | rel_parameter_belongs_to_method        | rel_method_has_parameter               |
| 11| component ⊃ component_instance            | rel_instance_of_component              | rel_component_has_instance             |

In 9/11 pairs the child-side ``belongs_to``/``part_of``/``exposed_by`` edge was
already correct and the parent-side ``contains``/``has``/``exposes`` edge was the
copy-paste error. In pairs 1 and 5 it is the reverse (the ``contains``/``groups``
member was correct, the ``belongs_to`` member was wrong).

Rather than "flip" in place (order-dependent), this migration *sets* the
canonical (source_cardinality, target_cardinality) for **both** members of
each pair from the whole/part invariant. The already-correct members are
unchanged; only the 11 erroneous members move. This makes the migration
idempotent and self-correcting.

Cardinality lives only in the catalog overlay (``relation_catalog.yaml``);
core ``relation_kinds`` in ``metamodel.yaml`` carry no cardinality, and the
two-layer contract (Rule 2) checks from_kind/to_kind/category/direction only —
so this touches no contract field.

## Duplicate removal (2 core-only legacy relations)

Two relations exist only in the core ontology (no ``relation_catalog`` overlay)
and duplicate a canonical catalog-era relation over the same endpoints:

| removed (core-only legacy)               | superseded by (canonical, catalog)   |
|------------------------------------------|--------------------------------------|
| rel_data_product_contains_data_object    | rel_data_product_contains_object     |
| rel_org_unit_creates_product             | rel_org_unit_creates_bank_product    |

Both are core-only, so the ``atlas_mvp`` projection/bundle is unaffected; only
the ``metamodel_snapshot.json`` artifact loses two entries. Neither is
referenced by any ``inverse_relation_id`` (verified), so removal is clean.
This follows the MACWO-528 dedupe precedent (outright removal of duplicates).

Idempotent.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METAMODEL_PATH = REPO_ROOT / "model" / "metamodel.yaml"
RELATION_CATALOG_PATH = REPO_ROOT / "model" / "relation_catalog.yaml"

# Canonical (source_cardinality, target_cardinality) for both members of each
# of the 11 inverse pairs, derived from the whole=one / part=many invariant.
# Keyed by relation id; source is the cardinality of from_kind, target of to_kind.
CANONICAL_CARDINALITY: dict[str, tuple[str, str]] = {
    # 1. business_domain(whole) ⊃ business_capability(part)
    "rel_domain_contains_capability": ("one", "many"),   # domain -> capability
    "rel_capability_belongs_to_domain": ("many", "one"),  # capability -> domain  (flipped)
    # 2. organizational_unit(whole) ⊃ business_role(part)
    "rel_role_belongs_to_org_unit": ("many", "one"),      # role -> org_unit
    "rel_org_unit_has_role": ("one", "many"),             # org_unit -> role      (flipped)
    # 3. business_operation(whole) ⊃ business_action(part)
    "rel_action_part_of_operation": ("many", "one"),      # action -> operation
    "rel_operation_contains_action": ("one", "many"),     # operation -> action   (flipped)
    # 4. business_entity(whole) ⊃ business_attribute(part)
    "rel_attribute_describes_entity": ("many", "one"),    # attribute -> entity
    "rel_entity_has_attribute": ("one", "many"),          # entity -> attribute   (flipped)
    # 5. job_family(whole) ⊃ business_role(part)
    "rel_job_family_groups_role": ("one", "many"),        # job_family -> role
    "rel_role_belongs_to_job_family": ("many", "one"),    # role -> job_family     (flipped)
    # 6. data_product(whole) ⊃ data_object(part)
    "rel_data_object_part_of_product": ("many", "one"),   # data_object -> data_product
    "rel_data_product_contains_object": ("one", "many"),  # data_product -> data_object (flipped)
    # 7. data_object(whole) ⊃ data_attribute(part)
    "rel_data_attribute_belongs_to_object": ("many", "one"),  # data_attribute -> data_object
    "rel_data_object_has_attribute": ("one", "many"),         # data_object -> data_attribute (flipped)
    # 8. it_system(whole) ⊃ api(part)
    "rel_api_exposed_by_system": ("many", "one"),         # api -> it_system
    "rel_system_exposes_api": ("one", "many"),            # it_system -> api       (flipped)
    # 9. api(whole) ⊃ api_method(part)
    "rel_api_method_belongs_to_api": ("many", "one"),     # api_method -> api
    "rel_api_contains_method": ("one", "many"),           # api -> api_method      (flipped)
    # 10. api_method(whole) ⊃ api_method_parameter(part)
    "rel_parameter_belongs_to_method": ("many", "one"),   # api_method_parameter -> api_method
    "rel_method_has_parameter": ("one", "many"),          # api_method -> api_method_parameter (flipped)
    # 11. component(whole) ⊃ component_instance(part)
    "rel_instance_of_component": ("many", "one"),         # component_instance -> component
    "rel_component_has_instance": ("one", "many"),        # component -> component_instance (flipped)
}

# Core-only legacy duplicates → the canonical catalog-era relation they duplicate.
DUPLICATE_RELATIONS_TO_REMOVE: dict[str, str] = {
    "rel_data_product_contains_data_object": "rel_data_product_contains_object",
    "rel_org_unit_creates_product": "rel_org_unit_creates_bank_product",
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

    rc_relations = rc["relation_catalog"]["relations"]
    rc_by_id = {r["id"]: r for r in rc_relations}

    # --- 1. Set canonical cardinalities on both members of each pair ---
    missing = sorted(set(CANONICAL_CARDINALITY) - set(rc_by_id))
    if missing:
        print(f"ERROR: catalog is missing expected relations: {missing}", file=sys.stderr)
        return 1

    cardinality_changes = 0
    for rid, (sc, tc) in CANONICAL_CARDINALITY.items():
        rel = rc_by_id[rid]
        if rel.get("source_cardinality") != sc or rel.get("target_cardinality") != tc:
            rel["source_cardinality"] = sc
            rel["target_cardinality"] = tc
            cardinality_changes += 1

    # --- 2. Remove the 2 core-only legacy duplicate relations ---
    before_mm = len(mm["relation_kinds"])
    before_rc = len(rc_relations)
    remove_ids = set(DUPLICATE_RELATIONS_TO_REMOVE)

    mm["relation_kinds"] = [r for r in mm["relation_kinds"] if r["id"] not in remove_ids]
    rc["relation_catalog"]["relations"] = [
        r for r in rc_relations if r["id"] not in remove_ids
    ]

    # Defensive: clear any inverse pointer that referenced a removed id.
    for rel in rc["relation_catalog"]["relations"]:
        if rel.get("inverse_relation_id") in remove_ids:
            rel["inverse_relation_id"] = None
            rel["has_inverse"] = False

    dump_yaml(METAMODEL_PATH, mm)
    dump_yaml(RELATION_CATALOG_PATH, rc)

    removed_mm = before_mm - len(mm["relation_kinds"])
    removed_rc = before_rc - len(rc["relation_catalog"]["relations"])
    print(
        "MACWO-670 applied: "
        f"cardinality members corrected: {cardinality_changes} (expected 11 on first run), "
        f"duplicate relations removed: mm -{removed_mm}, rc -{removed_rc}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
