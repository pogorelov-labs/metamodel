"""MACWO-528 Phase 1: Port PDF value_stream attributes into metamodel.yaml.

Source: PDF 1.0 — Поток ценности (Value Stream)
Target: model/metamodel.yaml → entity_kinds[value_stream].attributes

Adds 26 new attributes in v2 contract form. Two PDF fields overlap with
existing legacy attributes and are skipped:
  - PDF #24 "Владелец"          ≡ existing value_stream.owner
  - PDF #3  "Краткое описание"  → kept as new field short_description since
    existing legacy only has goal (different semantic)

Actually the two existing legacy attributes are:
  - value_stream.goal  — цель VS (semantic ≠ PDF "Краткое описание")
  - value_stream.owner — владелец (≡ PDF #24)

So we skip only PDF #24 and add 27 new attributes. But "Домен" (PDF #4) is
close to legacy business_domain_id pattern — we keep it as a new scalar
(enum) because business_domain_id is not present on value_stream.

Final count: 27 new attributes.

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
        "id": f"value_stream.{field_id}",
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


VALUE_STREAM_ATTRIBUTES = [
    # ==================== display_group: core (9) ====================
    attr("code", "Code", "Код",
         "Уникальный идентификатор потока ценности.",
         data_type="string", category="identity", display_group="core",
         required=True, example_values=["VS-IP-LOAN-ORIG-001"],
         quality_expectation="required_for_mvp"),
    attr("name", "Name", "Название",
         "Наименование объекта.",
         data_type="string", category="identity", display_group="core",
         required=True, example_values=["Выдача кредита"],
         quality_expectation="required_for_mvp"),
    attr("short_description", "Short Description", "Краткое описание",
         "Цель и основные этапы потока создания ценности.",
         data_type="text", category="business", display_group="core",
         display_mode="long_text", required=True),
    attr("domain", "Business Domain", "Домен",
         "Бизнес-домен потока ценности.",
         data_type="enum", category="business", display_group="core",
         display_mode="badge", required=True,
         enum_values=["retail", "cib", "finance", "risk_compliance", "operations", "hr_tech", "infrastructure"],
         example_values=["retail"]),
    attr("is_deterministic", "Is Deterministic", "Детерминирован",
         "Управляется ли поток строгим workflow (детерминирован) или "
         "допускает управление со стороны AI (недетерминирован).",
         data_type="boolean", category="business", display_group="core",
         display_mode="badge", required=True),
    attr("status_lifecycle", "Lifecycle Status", "Статус",
         "Жизненный цикл записи: draft / production / archive.",
         data_type="enum", category="lifecycle", display_group="core",
         display_mode="badge", required=True,
         enum_values=["draft", "production", "archive"],
         example_values=["production"]),
    attr("maturity_level", "Maturity Level", "Уровень зрелости",
         "Уровень зрелости потока ценности.",
         data_type="enum", category="business", display_group="core",
         display_mode="badge",
         enum_values=["initial", "repeatable", "defined", "managed", "optimized"]),
    attr("criticality", "Criticality", "Критичность",
         "Уровень критичности потока ценности.",
         data_type="enum", category="business", display_group="core",
         display_mode="badge", required=True,
         enum_values=["mission_critical", "business_critical", "business_support", "office_productivity"],
         example_values=["business_critical"]),
    attr("version", "Version", "Версия",
         "Версия потока создания ценности.",
         data_type="string", category="lifecycle", display_group="core",
         required=True, example_values=["1.0"]),

    # ==================== display_group: consumer (3) ====================
    attr("job_family_id", "Job Family", "Job Family",
         "Job Family, в случае если потребитель — конечный клиент.",
         data_type="id", category="business", display_group="consumer",
         display_mode="entity_ref", ref_kind="job_family"),
    attr("product_id", "Product", "Продукт",
         "Связанный банковский продукт, в случае если потребитель — конечный клиент.",
         data_type="id", category="business", display_group="consumer",
         display_mode="entity_ref", ref_kind="bank_product"),
    attr("consumer_type", "Consumer Type", "Тип потребителя ценности",
         "Тип потребителя ценности.",
         data_type="enum", category="business", display_group="consumer",
         display_mode="badge", required=True,
         enum_values=["end_customer", "external_counterparty", "internal_stakeholder"],
         example_values=["end_customer"]),

    # ==================== display_group: value (2) ====================
    attr("trigger", "Trigger", "Триггер",
         "Потребность или запрос потребителя, запускающая ПСЦ.",
         data_type="text", category="business", display_group="value",
         display_mode="long_text", required=True),
    attr("delivered_value", "Delivered Value", "Доставляемая ценность",
         "Доставляемая ценность потребителю.",
         data_type="text", category="business", display_group="value",
         display_mode="long_text", required=True),

    # ==================== display_group: vsm (4) ====================
    attr("lead_time", "Lead Time", "Время цикла (Lead Time) / Time to Job",
         "Общее время от старта до завершения. Lead Time = Process Time + Delay Time.",
         data_type="number", category="data", display_group="vsm",
         unit="days", example_values=[3]),
    attr("process_time", "Process Time", "Время обработки (Process Time)",
         "Время, затрачиваемое на полезную работу.",
         data_type="number", category="data", display_group="vsm",
         unit="days", example_values=[0.5]),
    attr("delay_time", "Delay Time", "Время ожидания (Delay Time)",
         "Время, затрачиваемое на ожидание или задержки.",
         data_type="number", category="data", display_group="vsm",
         unit="days", example_values=[2.5]),
    attr("value_added_time", "Value-Added Time", "Время создания ценности (Value-Added Time)",
         "Часть времени обработки, затрачиваемого непосредственно на создание "
         "ценности, имеющей значение для потребителя.",
         data_type="number", category="data", display_group="vsm",
         unit="days", example_values=[0.4]),

    # ==================== display_group: metrics (5) ====================
    attr("first_pass_yield", "First Pass Yield", "Процент завершения без ошибок (FPY)",
         "Процент завершения процесса без ошибок с первой попытки.",
         data_type="number", category="data", display_group="metrics",
         unit="percent", example_values=[98]),
    attr("operating_cost", "Operating Cost", "Затраты",
         "Операционные издержки потока ценности.",
         data_type="number", category="data", display_group="metrics",
         unit="rub", example_values=[20000]),
    attr("customer_satisfaction", "Customer Satisfaction (NPS/CSI)",
         "Удовлетворённость потребителя",
         "NPS или CSI потребителя.",
         data_type="number", category="data", display_group="metrics",
         unit="percent", example_values=[78]),
    attr("fai", "Function Automation Index (FAI)", "FAI",
         "Индекс автоматизации потока: отношение автоматизированных FTE "
         "этапов к общему количеству FTE этапов.",
         data_type="number", category="data", display_group="metrics",
         unit="percent", example_values=[20]),
    attr("stp", "Straight Through Processing (STP)", "STP",
         "Уровень автоматизации сквозной обработки: отношение количества "
         "экземпляров потока, реализованных полностью автоматически, к общему "
         "количеству экземпляров.",
         data_type="number", category="data", display_group="metrics",
         unit="percent", example_values=[50]),

    # ==================== display_group: risks (1) ====================
    attr("risks", "Risks", "Риски",
         "Ключевые риски потока ценности.",
         data_type="text", category="business", display_group="risks",
         display_mode="long_text"),

    # ==================== display_group: ownership (1) ====================
    attr("org_unit_id", "Organizational Unit", "Подразделение",
         "Подразделение владельца потока ценности.",
         data_type="id", category="organizational", display_group="ownership",
         display_mode="entity_ref", ref_kind="organizational_unit",
         required=True),

    # ==================== display_group: lifecycle (2) ====================
    attr("created_at", "Created At", "Дата создания",
         "Дата создания записи.",
         data_type="string", category="lifecycle", display_group="lifecycle",
         display_mode="date", required=True, example_values=["2024-11-12"]),
    attr("updated_at", "Updated At", "Дата редактирования",
         "Дата последнего изменения записи.",
         data_type="string", category="lifecycle", display_group="lifecycle",
         display_mode="date", required=True, example_values=["2024-11-17"]),
]

for idx, attribute in enumerate(VALUE_STREAM_ATTRIBUTES, start=1):
    attribute.setdefault("display_order", idx * 10)


def main():
    print(f"[macwo528_phase1] Loading {METAMODEL_PATH}")
    with METAMODEL_PATH.open("r", encoding="utf-8") as f:
        model = yaml.safe_load(f)

    target_kind = None
    for kind in model.get("entity_kinds", []):
        if kind.get("id") == "value_stream":
            target_kind = kind
            break

    if target_kind is None:
        print("ERROR: value_stream not found", file=sys.stderr)
        return 2

    existing_ids = {a.get("id") for a in target_kind.get("attributes", []) if a.get("id")}
    print(f"[macwo528_phase1] Existing: {len(existing_ids)}")

    attributes = target_kind.setdefault("attributes", [])
    added = 0
    for new_attr in VALUE_STREAM_ATTRIBUTES:
        if new_attr["id"] in existing_ids:
            continue
        attributes.append(new_attr)
        existing_ids.add(new_attr["id"])
        added += 1
    print(f"[macwo528_phase1] Added {added}, total {len(attributes)}")

    if added:
        with METAMODEL_PATH.open("w", encoding="utf-8") as f:
            yaml.safe_dump(model, f, allow_unicode=True, sort_keys=False, width=120, default_flow_style=False)
    print("[macwo528_phase1] Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
