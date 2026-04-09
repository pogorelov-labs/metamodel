"""MACWO-526 Phase 2: Add business_process relation_kinds and catalog overlays.

Source: PDF 1.0 (Атрибутивный состав business_process)
Targets:
  - model/metamodel.yaml → relation_kinds[]
  - model/relation_catalog.yaml → relation_catalog.relations[]

Phase 1 added scalar attributes. Phase 2 adds 8 new relation_kinds for the
reference fields and enriches them in the relation_catalog overlay so the
two-layer mm/rc contract holds (Rule 1: every catalog relation must have a
relation_kind in mm).

Relations added (business_process as source):
  1. rel_business_process_owned_by_employee         (PDF #36)
  2. rel_business_process_owned_by_team             (PDF #38)
  3. rel_business_process_has_participant_employee  (PDF #39, many)
  4. rel_business_process_has_participant_org_unit  (PDF #40, many)
  5. rel_business_process_affects_customer_segment  (PDF #52, many)
  6. rel_business_process_control_owned_by_employee (PDF #48)
  7. rel_business_process_risk_owned_by_employee    (PDF #46 ORM)
  8. rel_business_process_uses_it_system            (PDF #51, many)

Relations NOT added (already exist in mm):
  - PDF #17 (capability)       — rel_process_implements_capability
  - PDF #20/21 (dependencies)  — rel_process_depends_on_process
  - PDF #9 (domain)            — covered by scalar business_domain_id

Idempotent — each relation is appended only if its id is not already present.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METAMODEL_PATH = REPO_ROOT / "model" / "metamodel.yaml"
RELATION_CATALOG_PATH = REPO_ROOT / "model" / "relation_catalog.yaml"
INTRODUCED_IN = "2.1"
CATALOG_VERSION = "2.1.0"


# ---------------------------------------------------------------------------
# relation_kinds for metamodel.yaml
# ---------------------------------------------------------------------------

def rel_kind(
    rel_id: str,
    name: str,
    from_kind: str,
    to_kind: str,
    category: str,
    description: str,
    *,
    metamodel_level: str = "business_details",
    direction: str = "directed",
) -> dict:
    return {
        "id": rel_id,
        "name": name,
        "from_kind": from_kind,
        "to_kind": to_kind,
        "metamodel_level": metamodel_level,
        "category": category,
        "direction": direction,
        "description": description,
    }


NEW_RELATION_KINDS: list[dict] = [
    rel_kind(
        "rel_business_process_owned_by_employee",
        "Business process owned by employee",
        from_kind="business_process",
        to_kind="employee",
        category="governance",
        description="Сотрудник — владелец бизнес-процесса (PDF 1.0 #36).",
    ),
    rel_kind(
        "rel_business_process_owned_by_team",
        "Business process owned by team",
        from_kind="business_process",
        to_kind="team",
        category="governance",
        description="Agile- или функциональная команда-владелец процесса (PDF 1.0 #38).",
    ),
    rel_kind(
        "rel_business_process_has_participant_employee",
        "Business process has participant employee",
        from_kind="business_process",
        to_kind="employee",
        category="association",
        description="Сотрудник — участник бизнес-процесса (PDF 1.0 #39).",
    ),
    rel_kind(
        "rel_business_process_has_participant_org_unit",
        "Business process has participant organizational unit",
        from_kind="business_process",
        to_kind="organizational_unit",
        category="association",
        description="Организационное подразделение — участник процесса (PDF 1.0 #40).",
    ),
    rel_kind(
        "rel_business_process_affects_customer_segment",
        "Business process affects customer segment",
        from_kind="business_process",
        to_kind="customer_segment",
        category="association",
        description="Процесс влияет на клиентский сегмент (PDF 1.0 #52).",
    ),
    rel_kind(
        "rel_business_process_control_owned_by_employee",
        "Business process control owned by employee",
        from_kind="business_process",
        to_kind="employee",
        category="governance",
        description="Сотрудник — владелец контроля бизнес-процесса (PDF 1.0 #48).",
    ),
    rel_kind(
        "rel_business_process_risk_owned_by_employee",
        "Business process risk owned by employee (ORM)",
        from_kind="business_process",
        to_kind="employee",
        category="governance",
        description="Operational Risk Manager — владелец рисков процесса (PDF 1.0 #46).",
    ),
    rel_kind(
        "rel_business_process_uses_it_system",
        "Business process uses IT system",
        from_kind="business_process",
        to_kind="it_system",
        category="dependency",
        description="Процесс использует ИТ-систему (PDF 1.0 #51).",
    ),
]


# ---------------------------------------------------------------------------
# catalog overlays for relation_catalog.yaml
# ---------------------------------------------------------------------------

def catalog_rel(
    rel_id: str,
    name: str,
    description: str,
    from_kind: str,
    to_kind: str,
    category: str,
    *,
    source_cardinality: str = "many",
    target_cardinality: str = "one",
    ui_label_out: str = "",
    ui_label_in: str = "",
    ui_group: str = "ownership",
    path_priority: str = "secondary",
    impact_mode: str = "propagate",
    supports_qualifiers: bool = False,
    allowed_qualifiers: list | None = None,
) -> dict:
    return {
        "id": rel_id,
        "name": name,
        "description": description,
        "from_kind": from_kind,
        "to_kind": to_kind,
        "category": category,
        "direction": "directed",
        "source_cardinality": source_cardinality,
        "target_cardinality": target_cardinality,
        "has_inverse": False,
        "is_traversable_by_default": True,
        "allowed_in_neighbors": True,
        "allowed_in_paths": True,
        "allowed_in_impact": True,
        "default_visibility": "visible",
        "path_priority": path_priority,
        "impact_mode": impact_mode,
        "supports_qualifiers": supports_qualifiers,
        "allowed_qualifiers": allowed_qualifiers or [],
        "required_qualifiers": [],
        "evidence_required": False,
        "ui_label_out": ui_label_out,
        "ui_label_in": ui_label_in,
        "ui_group": ui_group,
        "exportable": True,
        "status": "active",
        "introduced_in": CATALOG_VERSION,
        "applies_to_profiles": ["atlas_mvp"],
    }


NEW_CATALOG_RELATIONS: list[dict] = [
    catalog_rel(
        "rel_business_process_owned_by_employee",
        "Business process owned by employee",
        "Сотрудник — владелец бизнес-процесса.",
        from_kind="business_process",
        to_kind="employee",
        category="governance",
        source_cardinality="many",
        target_cardinality="one",
        ui_label_out="owned by",
        ui_label_in="owns",
        ui_group="ownership",
        path_priority="primary",
    ),
    catalog_rel(
        "rel_business_process_owned_by_team",
        "Business process owned by team",
        "Команда-владелец бизнес-процесса.",
        from_kind="business_process",
        to_kind="team",
        category="governance",
        source_cardinality="many",
        target_cardinality="one",
        ui_label_out="owned by team",
        ui_label_in="owns process",
        ui_group="ownership",
        path_priority="primary",
    ),
    catalog_rel(
        "rel_business_process_has_participant_employee",
        "Business process has participant employee",
        "Сотрудник — участник процесса.",
        from_kind="business_process",
        to_kind="employee",
        category="association",
        source_cardinality="many",
        target_cardinality="many",
        ui_label_out="has participant",
        ui_label_in="participates in",
        ui_group="participation",
        supports_qualifiers=True,
        allowed_qualifiers=["role"],
    ),
    catalog_rel(
        "rel_business_process_has_participant_org_unit",
        "Business process has participant organizational unit",
        "Подразделение — участник процесса.",
        from_kind="business_process",
        to_kind="organizational_unit",
        category="association",
        source_cardinality="many",
        target_cardinality="many",
        ui_label_out="has participant org unit",
        ui_label_in="participates in process",
        ui_group="participation",
        supports_qualifiers=True,
        allowed_qualifiers=["role"],
    ),
    catalog_rel(
        "rel_business_process_affects_customer_segment",
        "Business process affects customer segment",
        "Процесс влияет на клиентский сегмент.",
        from_kind="business_process",
        to_kind="customer_segment",
        category="association",
        source_cardinality="many",
        target_cardinality="many",
        ui_label_out="affects segment",
        ui_label_in="affected by process",
        ui_group="impact",
        impact_mode="propagate",
    ),
    catalog_rel(
        "rel_business_process_control_owned_by_employee",
        "Business process control owned by employee",
        "Сотрудник — владелец контроля процесса.",
        from_kind="business_process",
        to_kind="employee",
        category="governance",
        source_cardinality="many",
        target_cardinality="one",
        ui_label_out="control owned by",
        ui_label_in="owns control of",
        ui_group="ownership",
    ),
    catalog_rel(
        "rel_business_process_risk_owned_by_employee",
        "Business process risk owned by employee",
        "ORM — владелец рисков процесса.",
        from_kind="business_process",
        to_kind="employee",
        category="governance",
        source_cardinality="many",
        target_cardinality="one",
        ui_label_out="risk owned by",
        ui_label_in="owns risk of",
        ui_group="ownership",
    ),
    catalog_rel(
        "rel_business_process_uses_it_system",
        "Business process uses IT system",
        "Процесс использует ИТ-систему. Qualifier dependency_type уточняет тип.",
        from_kind="business_process",
        to_kind="it_system",
        category="dependency",
        source_cardinality="many",
        target_cardinality="many",
        ui_label_out="uses",
        ui_label_in="used by process",
        ui_group="landscape",
        path_priority="primary",
        impact_mode="propagate",
        supports_qualifiers=True,
        allowed_qualifiers=["dependency_type", "criticality"],
    ),
]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_yaml(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            allow_unicode=True,
            sort_keys=False,
            width=120,
            default_flow_style=False,
        )


def main() -> int:
    # --- metamodel.yaml: add relation_kinds ---
    print(f"[macwo526_phase2] Loading {METAMODEL_PATH}")
    model = load_yaml(METAMODEL_PATH)
    relation_kinds = model.setdefault("relation_kinds", [])
    existing_rel_ids = {r.get("id") for r in relation_kinds if r.get("id")}
    print(f"[macwo526_phase2] Existing relation_kinds: {len(existing_rel_ids)}")

    added_rel = 0
    skipped_rel = 0
    for new_rel in NEW_RELATION_KINDS:
        if new_rel["id"] in existing_rel_ids:
            skipped_rel += 1
            continue
        relation_kinds.append(new_rel)
        existing_rel_ids.add(new_rel["id"])
        added_rel += 1
    print(
        f"[macwo526_phase2] relation_kinds: added {added_rel}, skipped {skipped_rel}"
    )

    if added_rel > 0:
        print(f"[macwo526_phase2] Writing {METAMODEL_PATH}")
        dump_yaml(METAMODEL_PATH, model)

    # --- relation_catalog.yaml: add overlays ---
    print(f"[macwo526_phase2] Loading {RELATION_CATALOG_PATH}")
    catalog = load_yaml(RELATION_CATALOG_PATH)
    catalog_relations = catalog.setdefault("relation_catalog", {}).setdefault(
        "relations", []
    )
    existing_cat_ids = {r.get("id") for r in catalog_relations if r.get("id")}
    print(f"[macwo526_phase2] Existing catalog relations: {len(existing_cat_ids)}")

    added_cat = 0
    skipped_cat = 0
    for new_cat in NEW_CATALOG_RELATIONS:
        if new_cat["id"] in existing_cat_ids:
            skipped_cat += 1
            continue
        catalog_relations.append(new_cat)
        existing_cat_ids.add(new_cat["id"])
        added_cat += 1
    print(
        f"[macwo526_phase2] catalog relations: added {added_cat}, skipped {skipped_cat}"
    )

    if added_cat > 0:
        print(f"[macwo526_phase2] Writing {RELATION_CATALOG_PATH}")
        dump_yaml(RELATION_CATALOG_PATH, catalog)

    if added_rel == 0 and added_cat == 0:
        print("[macwo526_phase2] No changes — idempotent no-op")
    print("[macwo526_phase2] Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
