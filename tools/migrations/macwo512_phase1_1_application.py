"""MACWO-513 (Phase 1.1, G1.1): Application layer cleanup.

Removes the `software_component` entity_kind and rewires its relations to
`component`. Detailed acceptance criteria are in MACWO-513.

Operations:
1. Delete entity_kind ``software_component``.
2. Add ``component.artifact_ref`` and ``component.type`` attributes
   (preserving the meaning of ``software_component.type``).
3. In ``model/metamodel.yaml``:
   - Drop ``rel_vendor_product_composed_of_software_components`` (duplicate of
     ``rel_vendor_product_has_component`` after rewiring).
   - Rewire 11 remaining relation_kinds: replace ``software_component`` with
     ``component`` in ``from_kind``/``to_kind``.
   - Rename relation ids that contain ``software_component``.
4. In ``model/relation_catalog.yaml``:
   - Drop the bridge pair ``rel_software_component_implements_component`` and
     ``rel_component_implemented_by_software`` (would become self-loops).
   - Rewire and rename the remaining 10 relations the same way.

The script is idempotent — re-running on already-migrated files is a no-op.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METAMODEL_PATH = REPO_ROOT / "model" / "metamodel.yaml"
RELATION_CATALOG_PATH = REPO_ROOT / "model" / "relation_catalog.yaml"

ENTITY_TO_REMOVE = "software_component"
ENTITY_TARGET = "component"

# Relation ids that should be deleted entirely (semantic dups or bridges).
MM_RELATIONS_TO_DELETE = {
    # Duplicate of rel_vendor_product_has_component after rewiring.
    "rel_vendor_product_composed_of_software_components",
    # Duplicate of pre-existing rel_component_creates_data_process (category=produces).
    "rel_software_component_creates_data_process",
}
RC_RELATIONS_TO_DELETE = {
    # The two bridge relations between component and software_component
    # become self-loops after rewiring; drop both ends.
    "rel_software_component_implements_component",
    "rel_component_implemented_by_software",
    # Catalog mirror of the pre-existing relation; would collide on rename.
    "rel_software_component_creates_data_process",
}

# id renames (apply to both mm and rc).
RELATION_ID_RENAMES = {
    "rel_infra_resource_serves_software_component": "rel_infra_resource_serves_component",
    "rel_software_component_aggregates_api": "rel_component_aggregates_api",
    "rel_software_component_contracts_data_object": "rel_component_contracts_data_object",
}

# New attributes added to `component` (replacing software_component meaning).
NEW_COMPONENT_ATTRIBUTES = [
    {
        "id": "component.type",
        "name": "Тип компонента",
        "metamodel_level": "component_details",
        "description": "Тип реализации: микросервис, БД, UI, batch-job и т.д.",
    },
    {
        "id": "component.artifact_ref",
        "name": "Ссылка на артефакт поставки",
        "metamodel_level": "component_details",
        "description": (
            "Ссылка на код, образ или артефакт поставки, реализующий компонент "
            "(например, путь в Git, имя docker-образа, координаты артефакта в реестре)."
        ),
    },
]


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_yaml(path: Path, data) -> None:
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )


def rewire_relation(rel: dict) -> None:
    """Replace software_component endpoints with component (in place)."""
    if rel.get("from_kind") == ENTITY_TO_REMOVE:
        rel["from_kind"] = ENTITY_TARGET
    if rel.get("to_kind") == ENTITY_TO_REMOVE:
        rel["to_kind"] = ENTITY_TARGET
    if rel["id"] in RELATION_ID_RENAMES:
        rel["id"] = RELATION_ID_RENAMES[rel["id"]]
    desc = rel.get("description")
    if isinstance(desc, str) and ENTITY_TO_REMOVE in desc:
        rel["description"] = desc.replace(ENTITY_TO_REMOVE, ENTITY_TARGET)


def migrate_metamodel(mm: dict) -> dict:
    # 1) Remove software_component entity, augment component with new attributes.
    new_entities = []
    component_seen = False
    for entity in mm["entity_kinds"]:
        if entity["id"] == ENTITY_TO_REMOVE:
            continue
        if entity["id"] == ENTITY_TARGET:
            component_seen = True
            existing_attr_ids = {a.get("id") for a in (entity.get("attributes") or [])}
            attrs = list(entity.get("attributes") or [])
            for new_attr in NEW_COMPONENT_ATTRIBUTES:
                if new_attr["id"] not in existing_attr_ids:
                    attrs.append(new_attr)
            entity["attributes"] = attrs
        new_entities.append(entity)
    if not component_seen:
        raise RuntimeError("`component` entity not found in metamodel.yaml")
    mm["entity_kinds"] = new_entities

    # 2) Rewrite relation_kinds.
    new_rels = []
    for rel in mm["relation_kinds"]:
        if rel["id"] in MM_RELATIONS_TO_DELETE:
            continue
        rewire_relation(rel)
        new_rels.append(rel)
    mm["relation_kinds"] = new_rels
    return mm


def migrate_relation_catalog(rc: dict) -> dict:
    rels = rc["relation_catalog"]["relations"]
    new_rels = []
    for rel in rels:
        if rel["id"] in RC_RELATIONS_TO_DELETE:
            continue
        rewire_relation(rel)
        # Update inverse_relation_id if it now points to a renamed/deleted id.
        inv = rel.get("inverse_relation_id")
        if inv in RC_RELATIONS_TO_DELETE:
            rel["inverse_relation_id"] = None
            rel["has_inverse"] = False
        elif inv in RELATION_ID_RENAMES:
            rel["inverse_relation_id"] = RELATION_ID_RENAMES[inv]
        new_rels.append(rel)
    rc["relation_catalog"]["relations"] = new_rels
    return rc


def main() -> int:
    mm = load_yaml(METAMODEL_PATH)
    rc = load_yaml(RELATION_CATALOG_PATH)

    mm = migrate_metamodel(mm)
    rc = migrate_relation_catalog(rc)

    dump_yaml(METAMODEL_PATH, mm)
    dump_yaml(RELATION_CATALOG_PATH, rc)

    print("MACWO-513 phase 1.1 migration applied:")
    print(f"  entity_kinds:        {len(mm['entity_kinds'])}")
    print(f"  mm.relation_kinds:   {len(mm['relation_kinds'])}")
    print(f"  rc.relations:        {len(rc['relation_catalog']['relations'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
