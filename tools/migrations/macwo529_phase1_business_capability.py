"""MACWO-529 Phase 1: Port PDF business_capability attributes into metamodel.yaml.

Source: PDF 1.0 — Бизнес-способность (19 attributes)
Target: model/metamodel.yaml → entity_kinds[business_capability].attributes

Existing legacy: business_capability.maturity_level (1 attribute).
Skip PDF #9 «Уровень зрелости» — overlaps with legacy maturity_level.

Final: 18 new attributes added.

Idempotent.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METAMODEL_PATH = REPO_ROOT / "model" / "metamodel.yaml"
INTRODUCED_IN = "2.1"


def attr(field_id, name, name_ru, description, *, data_type, category, display_group,
         display_mode="plain", metamodel_level="business_details", cardinality="one",
         required=False, enum_values=None, ref_kind=None, unit=None,
         example_values=None, source_expectation=None, quality_expectation="recommended"):
    result = {
        "id": f"business_capability.{field_id}",
        "name": name, "name_ru": name_ru, "description": description,
        "data_type": data_type, "cardinality": cardinality, "required": required,
        "category": category, "metamodel_level": metamodel_level,
        "display_mode": display_mode, "display_group": display_group,
        "status": "active", "introduced_in": INTRODUCED_IN,
        "quality_expectation": quality_expectation,
    }
    if enum_values is not None:
        result["enum_values"] = enum_values
    if ref_kind is not None:
        result["ref_kind"] = ref_kind
    if unit is not None:
        result["unit"] = unit
    if example_values is not None:
        result["example_values"] = example_values
    if source_expectation is not None:
        result["source_expectation"] = source_expectation
    return result


BUSINESS_CAPABILITY_ATTRIBUTES = [
    # ==================== display_group: identity (5) ====================
    attr("code", "Code", "Код",
         "Локальный уникальный идентификатор RBRU.",
         data_type="string", category="identity", display_group="identity",
         required=True, example_values=["CAP-BS-CR-001"],
         quality_expectation="required_for_mvp"),
    attr("code_rbi", "Code (RBI)", "Код RBI",
         "Уникальный идентификатор соответствующей бизнес-способности в "
         "системе RBI ADOIT.",
         data_type="string", category="identity", display_group="identity",
         source_expectation=["ADOIT"], example_values=["02.11.03"]),
    attr("name", "Name", "Название",
         "Локальное наименование бизнес-способности RBRU.",
         data_type="string", category="identity", display_group="identity",
         required=True, example_values=["[BS-CR] Credit Risk Management"],
         quality_expectation="required_for_mvp"),
    attr("name_rbi", "Name (RBI)", "Название RBI",
         "Наименование соответствующей бизнес-способности в справочнике RBI.",
         data_type="string", category="identity", display_group="identity",
         source_expectation=["ADOIT"], example_values=["[BS-CR] Credit Risk Management"]),
    attr("cbr_techprocess_code", "CBR Techprocess Code", "Техпроцесс ЦБ",
         "Код соответствующего техпроцесса ЦБ РФ.",
         data_type="string", category="evidence", display_group="identity",
         example_values=["ТПрКО1"]),

    # ==================== display_group: classification (4) ====================
    attr("short_description", "Short Description", "Краткое описание",
         "Назначение и цель бизнес-способности.",
         data_type="text", category="business", display_group="classification",
         display_mode="long_text", required=True),
    attr("hierarchy_level", "Hierarchy Level", "Уровень иерархии",
         "Уровень в иерархии бизнес-способностей: L1 / L2 / L3.",
         data_type="enum", category="business", display_group="classification",
         display_mode="badge", required=True,
         enum_values=["l1", "l2", "l3"], example_values=["l3"]),
    attr("specialization", "Specialization", "Специализация",
         "Тип специализации: Strategic Capability / Operational Capability / Other.",
         data_type="enum", category="business", display_group="classification",
         display_mode="badge",
         enum_values=["strategic_capability", "operational_capability", "other"],
         example_values=["operational_capability"]),
    attr("domain", "Business Domain", "Домен",
         "Бизнес-домен.",
         data_type="enum", category="business", display_group="classification",
         display_mode="badge", required=True,
         enum_values=["retail", "cib", "finance", "risk_management", "operations", "hr_tech", "infrastructure"],
         example_values=["risk_management"]),

    # ==================== display_group: lifecycle (1) ====================
    attr("status_lifecycle", "Lifecycle Status", "Статус",
         "Жизненный цикл записи: draft / production / archived.",
         data_type="enum", category="lifecycle", display_group="lifecycle",
         display_mode="badge", required=True,
         enum_values=["draft", "production", "archived"],
         example_values=["production"]),

    # ==================== display_group: economics (3) ====================
    attr("opex_cost", "Operating Cost (OPEX)", "Затраты",
         "Операционные затраты на поддержание (OPEX, FTE).",
         data_type="number", category="data", display_group="economics",
         unit="rub_per_year", example_values=[200_000_000]),
    attr("kpi_target", "KPI", "KPI",
         "Описание целевого KPI.",
         data_type="text", category="business", display_group="economics",
         display_mode="long_text", example_values=["NPL < 5%"]),
    attr("regulatory_compliance", "Regulatory Compliance",
         "Соответствие регуляторным требованиям",
         "Ссылки на регуляторные требования.",
         data_type="text", category="evidence", display_group="economics",
         display_mode="long_text", example_values=["115-ФЗ"]),

    # ==================== display_group: landscape (1) ====================
    attr("used_it_system_ids", "Used IT Systems", "Используемые ИТ-системы",
         "Связанные ИТ-системы, реализующие бизнес-способность.",
         data_type="id", category="technical", display_group="landscape",
         display_mode="entity_ref", cardinality="many",
         ref_kind="it_system",
         example_values=[["RCRS", "CRMfB", "Provisions module", "SAS Default module"]]),

    # ==================== display_group: ownership (2) ====================
    attr("owner_employee_id", "Owner", "Владелец",
         "Владелец бизнес-способности.",
         data_type="id", category="organizational", display_group="ownership",
         display_mode="entity_ref", ref_kind="employee", required=True),
    attr("org_unit_id", "Organizational Unit", "Подразделение",
         "Подразделение владельца бизнес-способности.",
         data_type="id", category="organizational", display_group="ownership",
         display_mode="entity_ref", ref_kind="organizational_unit", required=True),

    # ==================== display_group: lifecycle dates (2) ====================
    attr("created_at", "Created At", "Дата создания",
         "Дата создания записи.",
         data_type="string", category="lifecycle", display_group="lifecycle",
         display_mode="date", required=True, example_values=["2024-11-12"]),
    attr("updated_at", "Updated At", "Дата редактирования",
         "Дата последнего изменения записи.",
         data_type="string", category="lifecycle", display_group="lifecycle",
         display_mode="date", required=True, example_values=["2024-11-17"]),
]

for idx, attribute in enumerate(BUSINESS_CAPABILITY_ATTRIBUTES, start=1):
    attribute.setdefault("display_order", idx * 10)


def main():
    print(f"[macwo529_phase1] Loading {METAMODEL_PATH}")
    with METAMODEL_PATH.open("r", encoding="utf-8") as f:
        model = yaml.safe_load(f)

    target = None
    for kind in model.get("entity_kinds", []):
        if kind.get("id") == "business_capability":
            target = kind
            break

    if target is None:
        print("ERROR: business_capability not found", file=sys.stderr)
        return 2

    existing_ids = {a.get("id") for a in target.get("attributes", []) if a.get("id")}
    print(f"[macwo529_phase1] Existing: {len(existing_ids)}")

    attributes = target.setdefault("attributes", [])
    added = 0
    for new_attr in BUSINESS_CAPABILITY_ATTRIBUTES:
        if new_attr["id"] in existing_ids:
            continue
        attributes.append(new_attr)
        existing_ids.add(new_attr["id"])
        added += 1
    print(f"[macwo529_phase1] Added {added}, total {len(attributes)}")

    if added:
        with METAMODEL_PATH.open("w", encoding="utf-8") as f:
            yaml.safe_dump(model, f, allow_unicode=True, sort_keys=False, width=120, default_flow_style=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
