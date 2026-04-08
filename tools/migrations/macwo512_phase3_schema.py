"""MACWO-519 (Phase 3): Bring metamodel.yaml to 0 schema errors.

The JSON Schema in ``model/schema/metamodel.schema.yaml`` is enforced by
external consumers; after the Phase 1 semantic cleanup the validator still
reports two structural gaps that need to be filled in (rather than worked
around in the schema).

Operations:
1. **A1.1** — add ru-RU ``name`` for every entry in
   ``dictionaries.entity_categories`` (the schema requires ``name`` on every
   ``dictionary_item`` and we never gave it one).
2. **A2.1** — fill ``metamodel_level`` for the 8 attributes inside ``api``,
   ``data_product`` and ``data_object`` that lack it. The level is inherited
   from the parent entity (which carries the canonical level).
3. **B** — set ``requirement.metamodel_level: business_details``.

After running this migration, ``jsonschema`` validation against
``model/schema/metamodel.schema.yaml`` is expected to report 0 errors.
The script is idempotent.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METAMODEL_PATH = REPO_ROOT / "model" / "metamodel.yaml"

# ru-RU labels for the 24 declared entity categories.
CATEGORY_NAMES_RU: dict[str, str] = {
    "goal": "Цель",
    "business_structure": "Бизнес-структура",
    "offering": "Предложение банка",
    "value_definition": "Определение ценности",
    "stakeholder": "Стейкхолдер",
    "channel": "Канал",
    "value_delivery": "Доставка ценности",
    "capability": "Бизнес-способность",
    "process": "Бизнес-процесс",
    "business_object": "Бизнес-объект",
    "application": "Приложение",
    "vendor_solution": "Вендорское решение",
    "interface": "Интерфейс",
    "integration": "Интеграция",
    "infrastructure": "Инфраструктура",
    "data": "Данные",
    "technology": "Технология",
    "source_tracking": "Источник происхождения",
    "governance": "Управление и контроль",
    "operational": "Операционная сущность",
    "metadata": "Метаданные",
    "metric": "Метрика",
    "people": "Люди и роли",
    "tooling": "Инструментарий",
}

# Entities whose attributes inherit the parent metamodel_level by default.
ENTITIES_WITH_INHERITED_ATTR_LEVEL = ("api", "data_product", "data_object")

REQUIREMENT_LEVEL = "business_details"


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_yaml(path: Path, data) -> None:
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, width=120)


def patch_categories(mm: dict) -> int:
    cats = mm["dictionaries"].get("entity_categories", [])
    patched = 0
    for cat in cats:
        if "name" in cat and cat["name"]:
            continue
        label = CATEGORY_NAMES_RU.get(cat["id"])
        if label is None:
            raise RuntimeError(
                f"Missing ru-RU label for category id '{cat['id']}'. "
                "Add it to CATEGORY_NAMES_RU before running this migration."
            )
        cat["name"] = label
        patched += 1
    return patched


def patch_attribute_levels(mm: dict) -> int:
    patched = 0
    for entity in mm["entity_kinds"]:
        if entity["id"] not in ENTITIES_WITH_INHERITED_ATTR_LEVEL:
            continue
        parent_level = entity.get("metamodel_level")
        if not parent_level:
            raise RuntimeError(
                f"Entity '{entity['id']}' is in the inherit list but has no "
                "metamodel_level itself; cannot inherit."
            )
        for attr in entity.get("attributes", []) or []:
            if attr.get("metamodel_level"):
                continue
            attr["metamodel_level"] = parent_level
            patched += 1
    return patched


def patch_requirement_level(mm: dict) -> int:
    for entity in mm["entity_kinds"]:
        if entity["id"] != "requirement":
            continue
        if entity.get("metamodel_level") == REQUIREMENT_LEVEL:
            return 0
        entity["metamodel_level"] = REQUIREMENT_LEVEL
        return 1
    raise RuntimeError("entity_kind 'requirement' not found")


def main() -> int:
    mm = load_yaml(METAMODEL_PATH)
    patched_cats = patch_categories(mm)
    patched_attrs = patch_attribute_levels(mm)
    patched_req = patch_requirement_level(mm)
    dump_yaml(METAMODEL_PATH, mm)
    print("MACWO-519 phase 3 migration applied:")
    print(f"  entity_categories patched: {patched_cats}")
    print(f"  attribute levels patched:  {patched_attrs}")
    print(f"  requirement level set:     {patched_req}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
