"""MACWO-528 Phase 2: value_stream relation_kinds and catalog overlays."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METAMODEL_PATH = REPO_ROOT / "model" / "metamodel.yaml"
RELATION_CATALOG_PATH = REPO_ROOT / "model" / "relation_catalog.yaml"
CATALOG_VERSION = "2.1.0"


def rel_kind(rel_id, name, from_kind, to_kind, category, description, *,
             metamodel_level="business_details", direction="directed"):
    return {
        "id": rel_id, "name": name,
        "from_kind": from_kind, "to_kind": to_kind,
        "metamodel_level": metamodel_level,
        "category": category, "direction": direction,
        "description": description,
    }


NEW_RELATION_KINDS = [
    rel_kind(
        "rel_value_stream_targets_job_family",
        "Value stream targets job family",
        "value_stream", "job_family", "association",
        "Поток ценности ориентирован на Job Family (PDF 1.0 #5).",
    ),
    rel_kind(
        "rel_value_stream_governed_by_org_unit",
        "Value stream governed by organizational unit",
        "value_stream", "organizational_unit", "governance",
        "Подразделение-владелец потока ценности (PDF 1.0 #25).",
    ),
]


def catalog_rel(rel_id, name, description, from_kind, to_kind, category, *,
                source_cardinality="many", target_cardinality="one",
                ui_label_out="", ui_label_in="", ui_group="ownership",
                path_priority="secondary", impact_mode="propagate",
                supports_qualifiers=False, allowed_qualifiers=None):
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
        "rel_value_stream_targets_job_family",
        "Value stream targets job family",
        "Поток ценности ориентирован на Job Family.",
        "value_stream", "job_family", "association",
        ui_label_out="targets", ui_label_in="served by",
        ui_group="consumer",
    ),
    catalog_rel(
        "rel_value_stream_governed_by_org_unit",
        "Value stream governed by org unit",
        "Подразделение-владелец потока ценности.",
        "value_stream", "organizational_unit", "governance",
        ui_label_out="governed by", ui_label_in="governs",
        path_priority="primary",
    ),
]


def load_yaml(path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_yaml(path, data):
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, width=120, default_flow_style=False)


def main():
    model = load_yaml(METAMODEL_PATH)
    relation_kinds = model.setdefault("relation_kinds", [])
    existing = {r.get("id") for r in relation_kinds if r.get("id")}
    added = 0
    for r in NEW_RELATION_KINDS:
        if r["id"] in existing:
            continue
        relation_kinds.append(r)
        added += 1
    print(f"[macwo528_phase2] relation_kinds added: {added}")
    if added:
        dump_yaml(METAMODEL_PATH, model)

    catalog = load_yaml(RELATION_CATALOG_PATH)
    catalog_relations = catalog.setdefault("relation_catalog", {}).setdefault("relations", [])
    existing_cat = {r.get("id") for r in catalog_relations if r.get("id")}
    added_cat = 0
    for r in NEW_CATALOG_RELATIONS:
        if r["id"] in existing_cat:
            continue
        catalog_relations.append(r)
        added_cat += 1
    print(f"[macwo528_phase2] catalog relations added: {added_cat}")
    if added_cat:
        dump_yaml(RELATION_CATALOG_PATH, catalog)
    return 0


if __name__ == "__main__":
    sys.exit(main())
