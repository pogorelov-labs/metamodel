"""MACWO-530 Phase 2: event relation_kinds and catalog overlays."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METAMODEL_PATH = REPO_ROOT / "model" / "metamodel.yaml"
RELATION_CATALOG_PATH = REPO_ROOT / "model" / "relation_catalog.yaml"
CATALOG_VERSION = "2.1.0"


def rel_kind(rel_id, name, from_kind, to_kind, category, description, *,
             metamodel_level="solution_details", direction="directed"):
    return {
        "id": rel_id, "name": name,
        "from_kind": from_kind, "to_kind": to_kind,
        "metamodel_level": metamodel_level,
        "category": category, "direction": direction,
        "description": description,
    }


NEW_RELATION_KINDS = [
    rel_kind(
        "rel_event_emitted_by_business_process",
        "Event emitted by business process",
        "event", "business_process", "association",
        "Событие порождено бизнес-процессом.",
    ),
    rel_kind(
        "rel_event_emitted_by_it_system",
        "Event emitted by IT system",
        "event", "it_system", "association",
        "Событие порождено ИТ-системой.",
    ),
    rel_kind(
        "rel_event_emitted_by_data_product",
        "Event emitted by data product",
        "event", "data_product", "association",
        "Событие порождено дата-продуктом (например DQ нарушение).",
    ),
    rel_kind(
        "rel_incident_triggered_by_event",
        "Incident triggered by event",
        "incident", "event", "dependency",
        "Инцидент создан в ответ на событие.",
    ),
]


def catalog_rel(rel_id, name, description, from_kind, to_kind, category, *,
                source_cardinality="many", target_cardinality="one",
                ui_label_out="", ui_label_in="", ui_group="event_flow",
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
        "rel_event_emitted_by_business_process",
        "Event emitted by business process",
        "Событие порождено бизнес-процессом.",
        "event", "business_process", "association",
        ui_label_out="emitted by", ui_label_in="emits event",
    ),
    catalog_rel(
        "rel_event_emitted_by_it_system",
        "Event emitted by IT system",
        "Событие порождено ИТ-системой.",
        "event", "it_system", "association",
        ui_label_out="emitted by system", ui_label_in="emits event",
    ),
    catalog_rel(
        "rel_event_emitted_by_data_product",
        "Event emitted by data product",
        "Событие порождено дата-продуктом.",
        "event", "data_product", "association",
        ui_label_out="emitted by data product", ui_label_in="emits event",
    ),
    catalog_rel(
        "rel_incident_triggered_by_event",
        "Incident triggered by event",
        "Инцидент создан в ответ на событие.",
        "incident", "event", "dependency",
        ui_label_out="triggered by event", ui_label_in="triggered incident",
        ui_group="incident_flow", path_priority="primary",
    ),
]


def load_yaml(p):
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_yaml(p, d):
    with p.open("w", encoding="utf-8") as f:
        yaml.safe_dump(d, f, allow_unicode=True, sort_keys=False, width=120, default_flow_style=False)


def main():
    model = load_yaml(METAMODEL_PATH)
    rks = model.setdefault("relation_kinds", [])
    existing = {r.get("id") for r in rks if r.get("id")}
    added = 0
    for r in NEW_RELATION_KINDS:
        if r["id"] in existing:
            continue
        rks.append(r)
        added += 1
    print(f"[macwo530_phase2] relation_kinds added: {added}")
    if added:
        dump_yaml(METAMODEL_PATH, model)

    catalog = load_yaml(RELATION_CATALOG_PATH)
    crs = catalog.setdefault("relation_catalog", {}).setdefault("relations", [])
    existing_cat = {r.get("id") for r in crs if r.get("id")}
    added_cat = 0
    for r in NEW_CATALOG_RELATIONS:
        if r["id"] in existing_cat:
            continue
        crs.append(r)
        added_cat += 1
    print(f"[macwo530_phase2] catalog relations added: {added_cat}")
    if added_cat:
        dump_yaml(RELATION_CATALOG_PATH, catalog)
    return 0


if __name__ == "__main__":
    sys.exit(main())
