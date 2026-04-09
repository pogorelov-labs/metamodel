"""MACWO-528: Drop 25 orphan relations that duplicate inverse pairs in the same direction.

While exploring the downstream Metamodel Reference graph we discovered
that kind-pairs had 2+ relations in the same direction — each pair
had a proper forward/reverse inverse pair plus an extra "orphan"
relation (``inverse: None``) that semantically restated one direction
of the inverse pair.

This migration removes 25 such orphans, keeping the legitimate
inverse pair (or the rc-enriched version) intact. Each drop has been
hand-reviewed.

## First batch (14 drops from the initial MACWO-528 sweep)

| Pair                                      | Dropped (orphan dup)                      |
|-------------------------------------------|-------------------------------------------|
| bank_product ↔ customer_segment           | rel_bank_product_targets_segment          |
| business_capability ↔ goal                | rel_capability_required_for_goal          |
| component ↔ component_instance            | rel_component_instance_of_component       |
| component ↔ logical_resource              | rel_component_runs_on_logical_resource    |
| component ↔ technology                    | rel_technology_has_component              |
| value ↔ value_consumer                    | rel_value_consumer_seeks_value            |
| data_contract ↔ data_product              | rel_data_product_has_contract             |
| data_process ↔ data_product               | rel_data_product_implemented_by_pipeline  |
| business_entity ↔ information_flow        | rel_information_flow_for_business_entity  |
| business_function ↔ business_operation    | rel_operation_relates_to_function         |
| component_instance ↔ infra_resource       | rel_infra_resource_serves_instance        |
| business_operation ↔ business_process     | rel_process_aggregates_operation          |
| business_role ↔ organizational_unit       | rel_org_unit_aggregates_role              |
| technology ↔ vendor_product               | rel_vendor_product_has_technology         |

## Second batch (11 additional drops — review sweep)

After applying the first batch, a full scan still surfaced 12 pair groups
with two same-direction relations in the same category. Eleven of those
are clearly duplicates (same semantic, different wording). The twelfth
(`business_entity → it_system`: managed_by vs mastered_by) is NOT a
duplicate in data-governance terms (operational management vs master
data management), so it stays.

| Pair                                      | Dropped (mm-only orphan)                  | Kept (rc-enriched)                        |
|-------------------------------------------|-------------------------------------------|-------------------------------------------|
| api ↔ api_method                          | rel_api_composed_of_methods               | rel_api_contains_method                   |
| api_method ↔ api_method_parameter         | rel_method_composed_of_params             | rel_method_has_parameter                  |
| business_capability ↔ business_domain     | rel_capability_part_of_domain             | rel_capability_belongs_to_domain          |
| business_operation ↔ business_action      | rel_operation_consists_of_actions         | rel_operation_contains_action             |
| business_process ↔ business_capability    | rel_process_implements_capability         | rel_process_realizes_capability           |
| business_process ↔ value_stream_stage     | rel_process_realizes_stage                | rel_process_belongs_to_stage              |
| information_flow ↔ business_entity        | rel_info_flow_serves_entity               | rel_information_flow_carries_entity       |
| infra_resource ↔ logical_resource         | rel_infra_resource_serves_logical_resource | rel_infra_resource_serves_resource       |
| integration ↔ information_flow **(typo)** | rel_integration_realizes_info_flow        | rel_integration_realizes_information_flow |
| it_system ↔ information_flow **(typo)**   | rel_it_system_serves_info_flow            | rel_it_system_serves_information_flow     |
| value_consumer ↔ channel                  | rel_consumer_contacts_via_channel         | rel_value_consumer_uses_channel           |

Two of these (integration→information_flow, it_system→information_flow)
are pure typo duplicates — the only difference is `info_flow` vs
`information_flow` in the name. Identical semantic, identical category.

## Description upgrades (8 fixes)

Several "kept" relations have placeholder descriptions like
"Inverse: API contains method." — these get upgraded to the better-written
description from the dropped orphan, so no information is lost.

## Left intact (semantically distinct, not duplicates)

- business_operation ↔ organizational_unit (owns + performs are
  different concepts — responsibility vs execution)
- business_process self-loop (depends/required — dependency; parent —
  hierarchy, different category)
- business_operation self-loop (follows ↔ precedes — legitimate
  inverse pair on a self-loop)
- api ↔ component (aggregates + exposes — different categories)
- business_entity ↔ it_system (managed_by = operational, mastered_by =
  master data — different concepts in data governance)
- business_process ↔ employee (4 roles: owner/participant/control/risk
  — added by MACWO-526, each semantically distinct)
- it_system ↔ employee (4 roles: business/delegate/it/architect
  — added by MACWO-527, each semantically distinct)
- bank_product ↔ value, business_capability ↔ value_stream_stage,
  data_object ↔ data_process — implicit cross-direction inverse pairs
  without explicit linkage. Should be linked via `has_inverse`/
  `inverse_relation_id` in a follow-up, but they are not duplicates
  and stay.

## Borderline cases (NOT dropped, need semantic review)

21 pair groups remain where the two relations have DIFFERENT categories
but overlapping semantics (e.g. `organizational_unit → it_system` as
`serves` and `ownership`). These are judgment calls that require
domain-owner input. They are explicitly out of scope for this PR.

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
    # First batch — 14 drops from the initial MACWO-528 sweep
    "rel_bank_product_targets_segment",
    "rel_capability_required_for_goal",
    "rel_component_instance_of_component",
    "rel_component_runs_on_logical_resource",
    "rel_technology_has_component",
    "rel_value_consumer_seeks_value",
    "rel_data_product_has_contract",
    "rel_data_product_implemented_by_pipeline",
    "rel_information_flow_for_business_entity",
    "rel_operation_relates_to_function",
    "rel_infra_resource_serves_instance",
    "rel_process_aggregates_operation",
    "rel_org_unit_aggregates_role",
    "rel_vendor_product_has_technology",
    # Second batch — 11 additional drops from the review sweep
    "rel_api_composed_of_methods",
    "rel_method_composed_of_params",
    "rel_capability_part_of_domain",
    "rel_operation_consists_of_actions",
    "rel_process_implements_capability",
    "rel_process_realizes_stage",
    "rel_info_flow_serves_entity",
    "rel_infra_resource_serves_logical_resource",
    "rel_integration_realizes_info_flow",
    "rel_it_system_serves_info_flow",
    "rel_consumer_contacts_via_channel",
}

# Description upgrades: the "kept" relation inherits the better-written
# description from the dropped orphan. Format: kept_id → new description.
DESCRIPTION_UPGRADES: dict[str, str] = {
    "rel_api_contains_method": "API раскрывает набор методов.",
    "rel_method_has_parameter": "Метод включает параметры запроса/ответа.",
    "rel_capability_belongs_to_domain": "Бизнес-способность является частью бизнес-домена.",
    "rel_operation_contains_action": "Бизнес-операция состоит из элементарных бизнес-действий.",
    "rel_process_realizes_capability": "Бизнес-процесс реализует бизнес-способность.",
    "rel_process_belongs_to_stage": "Бизнес-процесс обеспечивает выполнение стадии потока.",
    "rel_information_flow_carries_entity": (
        "Информационный поток транспортирует данные о сущности. "
        "Qualified relation that specifies which business entity semantics is carried."
    ),
    "rel_value_consumer_uses_channel": "Потребитель взаимодействует с банком через канал.",
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

    # Drop target relations from both files
    mm["relation_kinds"] = [
        r for r in mm["relation_kinds"] if r["id"] not in RELATIONS_TO_REMOVE
    ]
    rc["relation_catalog"]["relations"] = [
        r
        for r in rc["relation_catalog"]["relations"]
        if r["id"] not in RELATIONS_TO_REMOVE
    ]

    # Defensive: clear any inverse pointer that referenced a removed id.
    for rel in rc["relation_catalog"]["relations"]:
        if rel.get("inverse_relation_id") in RELATIONS_TO_REMOVE:
            rel["inverse_relation_id"] = None
            rel["has_inverse"] = False

    # Description upgrades — transfer better prose to the kept relations
    upgrades_applied = 0
    for rel in mm["relation_kinds"]:
        if rel["id"] in DESCRIPTION_UPGRADES:
            new_desc = DESCRIPTION_UPGRADES[rel["id"]]
            if rel.get("description") != new_desc:
                rel["description"] = new_desc
                upgrades_applied += 1
    for rel in rc["relation_catalog"]["relations"]:
        if rel["id"] in DESCRIPTION_UPGRADES:
            new_desc = DESCRIPTION_UPGRADES[rel["id"]]
            if rel.get("description") != new_desc:
                rel["description"] = new_desc

    dump_yaml(METAMODEL_PATH, mm)
    dump_yaml(RELATION_CATALOG_PATH, rc)

    after_mm = len(mm["relation_kinds"])
    after_rc = len(rc["relation_catalog"]["relations"])
    print(
        f"MACWO-528 dedupe applied: "
        f"mm.relation_kinds {before_mm} -> {after_mm} (-{before_mm - after_mm}), "
        f"rc.relations {before_rc} -> {after_rc} (-{before_rc - after_rc}), "
        f"description upgrades: {upgrades_applied}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
