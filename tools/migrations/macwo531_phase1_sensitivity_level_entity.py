"""MACWO-531 Phase 1: Add new entity_kind 'sensitivity_level' to metamodel.yaml.

Source: PDF 1.0 — Общие сущности — Категория чувствительной информации
Target: model/metamodel.yaml → entity_kinds[]

In the metamodel today the concept of "sensitivity level" exists as string-typed
attributes (business_attribute.sensitive_level, data_product.sensitive_level)
without validation, central reference, or governance metadata.

This PR introduces a first-class sensitivity_level entity_kind. The follow-up
PR-7 (MACWO-532) will migrate the existing scalar fields to urn_ref so they
become graph references.

Idempotent.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METAMODEL_PATH = REPO_ROOT / "model" / "metamodel.yaml"
INTRODUCED_IN = "2.1"

SENSITIVITY_LEVEL_ENTITY = {
    "id": "sensitivity_level",
    "name": "Sensitivity Level",
    "name_ru": "Категория чувствительной информации",
    "metamodel_level": "data_details",
    "category": "governance",
    "description": (
        "Классификационный уровень, который определяет степень "
        "конфиденциальности данных и предписывает правила их обработки, "
        "хранения и передачи."
    ),
    "scope_notes": (
        "Определяет обязательные меры защиты в зависимости от уровня. "
        "Содержит инструкции по обращению с чувствительной информацией. "
        "Используется как ссылка из business_attribute, data_product, "
        "data_object для централизованного управления правилами обработки."
    ),
    "aliases": [
        {"value": "sensitivity level", "lang": "en", "alias_type": "synonym", "status": "active"},
        {"value": "уровень чувствительности", "lang": "ru", "alias_type": "synonym", "status": "active"},
        {"value": "data classification", "lang": "en", "alias_type": "synonym", "status": "active"},
    ],
    "examples": [
        "public",
        "internal",
        "restricted",
        "confidential",
        "secret",
    ],
    "usage_purpose": (
        "Единый справочник уровней конфиденциальности для атрибутов, "
        "дата-продуктов и data-объектов."
    ),
    "status": "active",
    "introduced_in": INTRODUCED_IN,
    "attributes": [
        {
            "id": "sensitivity_level.level_code",
            "name": "Level Code",
            "name_ru": "Код уровня",
            "description": "Короткий идентификатор уровня (public, internal, restricted, confidential, secret).",
            "data_type": "enum",
            "enum_values": ["public", "internal", "restricted", "confidential", "secret"],
            "cardinality": "one",
            "required": True,
            "category": "identity",
            "metamodel_level": "data_details",
            "display_mode": "badge",
            "display_group": "core",
            "status": "active",
            "introduced_in": INTRODUCED_IN,
            "quality_expectation": "required_for_mvp",
            "display_order": 10,
        },
        {
            "id": "sensitivity_level.name_ru",
            "name": "Russian Label",
            "name_ru": "Локальное название",
            "description": "Русское название уровня для UI.",
            "data_type": "string",
            "cardinality": "one",
            "required": True,
            "category": "identity",
            "metamodel_level": "data_details",
            "display_mode": "plain",
            "display_group": "core",
            "status": "active",
            "introduced_in": INTRODUCED_IN,
            "example_values": ["Конфиденциально", "Публично"],
            "display_order": 20,
        },
        {
            "id": "sensitivity_level.handling_rules",
            "name": "Handling Rules",
            "name_ru": "Правила обращения",
            "description": (
                "Обязательные меры защиты и инструкции по обращению с данными "
                "соответствующего уровня."
            ),
            "data_type": "text",
            "cardinality": "one",
            "required": True,
            "category": "security",
            "metamodel_level": "data_details",
            "display_mode": "long_text",
            "display_group": "rules",
            "status": "active",
            "introduced_in": INTRODUCED_IN,
            "display_order": 30,
        },
        {
            "id": "sensitivity_level.required_encryption",
            "name": "Requires Encryption",
            "name_ru": "Обязательное шифрование",
            "description": "Требуется ли шифрование при передаче и хранении данных.",
            "data_type": "boolean",
            "cardinality": "one",
            "required": True,
            "category": "security",
            "metamodel_level": "data_details",
            "display_mode": "badge",
            "display_group": "rules",
            "status": "active",
            "introduced_in": INTRODUCED_IN,
            "display_order": 40,
        },
        {
            "id": "sensitivity_level.retention_policy",
            "name": "Retention Policy",
            "name_ru": "Политика хранения",
            "description": "Срок и условия хранения данных соответствующего уровня.",
            "data_type": "text",
            "cardinality": "one",
            "required": False,
            "category": "security",
            "metamodel_level": "data_details",
            "display_mode": "long_text",
            "display_group": "rules",
            "status": "active",
            "introduced_in": INTRODUCED_IN,
            "display_order": 50,
        },
        {
            "id": "sensitivity_level.regulatory_basis",
            "name": "Regulatory Basis",
            "name_ru": "Регуляторная основа",
            "description": "Ссылки на регуляторные требования (152-ФЗ, GDPR, PCI DSS).",
            "data_type": "text",
            "cardinality": "one",
            "required": False,
            "category": "evidence",
            "metamodel_level": "data_details",
            "display_mode": "long_text",
            "display_group": "rules",
            "status": "active",
            "introduced_in": INTRODUCED_IN,
            "example_values": ["152-ФЗ", "GDPR Art. 9", "PCI DSS v4.0"],
            "display_order": 60,
        },
    ],
}


def main():
    print(f"[macwo531_phase1] Loading {METAMODEL_PATH}")
    with METAMODEL_PATH.open("r", encoding="utf-8") as f:
        model = yaml.safe_load(f)

    entity_kinds = model.get("entity_kinds", [])
    if any(k.get("id") == "sensitivity_level" for k in entity_kinds):
        print("[macwo531_phase1] sensitivity_level already present — no-op")
        return 0

    entity_kinds.append(SENSITIVITY_LEVEL_ENTITY)
    print(f"[macwo531_phase1] Added sensitivity_level with {len(SENSITIVITY_LEVEL_ENTITY['attributes'])} attributes")

    with METAMODEL_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(model, f, allow_unicode=True, sort_keys=False, width=120, default_flow_style=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
