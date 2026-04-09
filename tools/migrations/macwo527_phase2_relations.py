"""MACWO-527 Phase 2: Add it_system relation_kinds and catalog overlays.

Adds 6 new relation_kinds paired with ref-field attributes from phase 1:
  1. rel_it_system_owned_by_team
  2. rel_it_system_business_owned_by_employee
  3. rel_it_system_business_owner_delegate_employee
  4. rel_it_system_it_owned_by_employee
  5. rel_it_system_architected_by_employee
  6. rel_it_system_legal_entity_org_unit

Support expert relations (support_expert_1_id, support_expert_2_id) and
owner team for legal entity reuse existing scalar attributes only — no
new relation_kinds because the semantic is already covered by
organizational relations.

Idempotent.
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


def rel_kind(rel_id, name, from_kind, to_kind, category, description, *, metamodel_level="solution_details", direction="directed"):
    return {
        "id": rel_id, "name": name,
        "from_kind": from_kind, "to_kind": to_kind,
        "metamodel_level": metamodel_level,
        "category": category, "direction": direction,
        "description": description,
    }


NEW_RELATION_KINDS = [
    rel_kind(
        "rel_it_system_owned_by_team",
        "IT system owned by team",
        "it_system", "team", "governance",
        "Команда — владелец ИТ-системы (PDF 1.0 #10 Owner Team).",
    ),
    rel_kind(
        "rel_it_system_business_owned_by_employee",
        "IT system business-owned by employee",
        "it_system", "employee", "governance",
        "Бизнес-владелец ИТ-системы (PDF 1.0 #11 Business owner).",
    ),
    rel_kind(
        "rel_it_system_business_owner_delegate_employee",
        "IT system business owner delegate",
        "it_system", "employee", "governance",
        "Заместитель бизнес-владельца ИТ-системы (PDF 1.0 #13).",
    ),
    rel_kind(
        "rel_it_system_it_owned_by_employee",
        "IT system IT-owned by employee",
        "it_system", "employee", "governance",
        "ИТ-владелец системы (PDF 1.0 #12 IT owner).",
    ),
    rel_kind(
        "rel_it_system_architected_by_employee",
        "IT system architected by employee",
        "it_system", "employee", "governance",
        "Корпоративный архитектор системы (PDF 1.0 #15).",
    ),
    rel_kind(
        "rel_it_system_legal_entity_org_unit",
        "IT system legal entity organizational unit",
        "it_system", "organizational_unit", "association",
        "Юридическое лицо-владелец ПО (PDF 1.0 #16 Org_Unit).",
    ),
]


def catalog_rel(
    rel_id, name, description, from_kind, to_kind, category,
    *, source_cardinality="many", target_cardinality="one",
    ui_label_out="", ui_label_in="", ui_group="ownership",
    path_priority="secondary", impact_mode="propagate",
    supports_qualifiers=False, allowed_qualifiers=None,
):
    return {
        "id": rel_id, "name": name, "description": description,
        "from_kind": from_kind, "to_kind": to_kind,
        "category": category, "direction": "directed",
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


NEW_CATALOG_RELATIONS = [
    catalog_rel(
        "rel_it_system_owned_by_team",
        "IT system owned by team",
        "Команда — владелец ИТ-системы.",
        "it_system", "team", "governance",
        ui_label_out="owned by team", ui_label_in="owns it system",
        path_priority="primary",
    ),
    catalog_rel(
        "rel_it_system_business_owned_by_employee",
        "IT system business-owned by employee",
        "Бизнес-владелец ИТ-системы.",
        "it_system", "employee", "governance",
        ui_label_out="business owned by", ui_label_in="business owns",
        path_priority="primary",
    ),
    catalog_rel(
        "rel_it_system_business_owner_delegate_employee",
        "IT system business owner delegate",
        "Заместитель бизнес-владельца ИТ-системы.",
        "it_system", "employee", "governance",
        ui_label_out="business owner delegate", ui_label_in="deputy for",
    ),
    catalog_rel(
        "rel_it_system_it_owned_by_employee",
        "IT system IT-owned by employee",
        "ИТ-владелец системы.",
        "it_system", "employee", "governance",
        ui_label_out="it owned by", ui_label_in="it owns",
        path_priority="primary",
    ),
    catalog_rel(
        "rel_it_system_architected_by_employee",
        "IT system architected by employee",
        "Корпоративный архитектор системы.",
        "it_system", "employee", "governance",
        ui_label_out="architected by", ui_label_in="architects",
    ),
    catalog_rel(
        "rel_it_system_legal_entity_org_unit",
        "IT system legal entity organizational unit",
        "Юридическое лицо-владелец ПО.",
        "it_system", "organizational_unit", "association",
        ui_label_out="legal entity", ui_label_in="legal owner of",
        ui_group="legal",
    ),
]


def load_yaml(path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_yaml(path, data):
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, width=120, default_flow_style=False)


def main():
    print(f"[macwo527_phase2] Loading {METAMODEL_PATH}")
    model = load_yaml(METAMODEL_PATH)
    relation_kinds = model.setdefault("relation_kinds", [])
    existing_rel_ids = {r.get("id") for r in relation_kinds if r.get("id")}

    added_rel = 0
    for new_rel in NEW_RELATION_KINDS:
        if new_rel["id"] in existing_rel_ids:
            continue
        relation_kinds.append(new_rel)
        existing_rel_ids.add(new_rel["id"])
        added_rel += 1
    print(f"[macwo527_phase2] relation_kinds added: {added_rel}")

    if added_rel > 0:
        dump_yaml(METAMODEL_PATH, model)

    print(f"[macwo527_phase2] Loading {RELATION_CATALOG_PATH}")
    catalog = load_yaml(RELATION_CATALOG_PATH)
    catalog_relations = catalog.setdefault("relation_catalog", {}).setdefault("relations", [])
    existing_cat_ids = {r.get("id") for r in catalog_relations if r.get("id")}

    added_cat = 0
    for new_cat in NEW_CATALOG_RELATIONS:
        if new_cat["id"] in existing_cat_ids:
            continue
        catalog_relations.append(new_cat)
        existing_cat_ids.add(new_cat["id"])
        added_cat += 1
    print(f"[macwo527_phase2] catalog relations added: {added_cat}")

    if added_cat > 0:
        dump_yaml(RELATION_CATALOG_PATH, catalog)

    print("[macwo527_phase2] Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
