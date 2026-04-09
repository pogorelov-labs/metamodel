"""MACWO-527 Phase 1: Port PDF it_system attributes into metamodel.yaml.

Source: ~/msc_1/meta/глоссарий и атрибуты/атрибутивный_состав.yaml (PDF 1.0)
Target: model/metamodel.yaml → entity_kinds[it_system].attributes

PDF 1.0 describes 41 attributes for it_system, matching SimpleOne CSP 1:1.
This migration adds 37 new attributes in v2 contract form.

Four PDF fields overlap with the semantics of existing legacy attributes and
are skipped:
  - "Категория значимости объекта КИИ"          → overlaps with legacy tier semantics (kept separate via new critical_infrastructure_level)
  - "Корпоративный архитектор (org)"            → semantic overlap via new architect_employee_id relation
  - "Юридическое лицо (Org_Unit)"               → via new legal_entity_org_unit_id
  - "Корпоративный архитектор (org)"            — no direct existing legacy field

So in fact all 37 non-overlapping PDF fields are added; the four legacy
attributes (org_unit_id, business_capability_id, business_domain_id, tier)
are left untouched and remain as coarse-grained associations.

Attributes are grouped by display_group:
identity, criticality, ownership, bcp, data_classification, pci, exposure,
support.

Security-sensitive attributes (PCI, confidential info flags) carry
sensitivity: confidential.

Idempotent — each attribute is appended only if its id is not already present.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METAMODEL_PATH = REPO_ROOT / "model" / "metamodel.yaml"
INTRODUCED_IN = "2.1"


def attr(
    field_id: str,
    name: str,
    name_ru: str,
    description: str,
    *,
    data_type: str,
    category: str,
    display_group: str,
    display_mode: str = "plain",
    metamodel_level: str = "solution_details",
    cardinality: str = "one",
    required: bool = False,
    enum_values: list | None = None,
    ref_kind: str | None = None,
    unit: str | None = None,
    example_values: list | None = None,
    source_expectation: list | None = None,
    quality_expectation: str = "recommended",
    sensitivity: str | None = None,
) -> dict:
    result: dict = {
        "id": f"it_system.{field_id}",
        "name": name,
        "name_ru": name_ru,
        "description": description,
        "data_type": data_type,
        "cardinality": cardinality,
        "required": required,
        "category": category,
        "metamodel_level": metamodel_level,
        "display_mode": display_mode,
        "display_group": display_group,
        "status": "active",
        "introduced_in": INTRODUCED_IN,
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
    if sensitivity is not None:
        result["sensitivity"] = sensitivity
    return result


IT_SYSTEM_ATTRIBUTES: list[dict] = [
    # ==================== display_group: identity (6) ====================
    attr(
        "name_short", "Short Name", "Наименование системы",
        "Короткое наименование системы — слово, словосочетание или аббревиатура. "
        "Должно быть кратким, удобно произносимым, не вызывать путаницы с именами "
        "существующих систем и общеупотребительными словами.",
        data_type="string", category="identity", display_group="identity",
        required=True,
        source_expectation=["SimpleOne"],
        quality_expectation="required_for_mvp",
    ),
    attr(
        "full_name", "Full Name", "Полное наименование системы",
        "Полное наименование системы. Должно раскрывать бизнес-смысл. "
        "Если система покупная — следует добавить вендорское наименование.",
        data_type="string", category="identity", display_group="identity",
        required=True,
        source_expectation=["SimpleOne"],
        quality_expectation="required_for_mvp",
    ),
    attr(
        "full_name_eng", "Full Name (English)",
        "Полное наименование системы на английском",
        "Перевод полного наименования на английский.",
        data_type="string", category="identity", display_group="identity",
        source_expectation=["SimpleOne"],
    ),
    attr(
        "alt_name", "Alternative Name", "Альтернативное наименование системы",
        "Альтернативное «неофициальное» наименование. Используется только для "
        "поиска и не используется в процессах управления системой. Может "
        "содержать исторические наименования.",
        data_type="string", category="identity", display_group="identity",
        cardinality="many",
        source_expectation=["SimpleOne"],
    ),
    attr(
        "description_text", "Description", "Описание системы",
        "Краткое, понятное описание функциональности ПО. Зачем нужна система, "
        "какую проблему решает, частью чего является, какую систему заменяет.",
        data_type="text", category="business", display_group="identity",
        display_mode="long_text",
        source_expectation=["SimpleOne"],
    ),
    attr(
        "description_eng", "Description (English)",
        "Описание системы на английском",
        "Перевод описания на английский.",
        data_type="text", category="business", display_group="identity",
        display_mode="long_text",
        source_expectation=["SimpleOne"],
    ),

    # ==================== display_group: criticality (6) ====================
    attr(
        "critical_infrastructure_level", "Critical Infrastructure Level",
        "Категория значимости объекта КИИ",
        "Категория значимости объектов критической информационной инфраструктуры "
        "согласно 187-ФЗ.",
        data_type="enum", category="security", display_group="criticality",
        display_mode="badge",
        enum_values=["category_1", "category_2", "category_3", "not_applicable"],
        source_expectation=["SimpleOne"],
    ),
    attr(
        "availability_tier", "Availability Tier", "Уровень доступности системы",
        "Уровень доступности системы, определяющий требования к RTP, RPO, "
        "Availability % и Availability Class.",
        data_type="enum", category="security", display_group="criticality",
        display_mode="badge",
        enum_values=["tier_0", "tier_1", "tier_2", "tier_3", "tier_4"],
        source_expectation=["SimpleOne"],
    ),
    attr(
        "mb_criticality", "MB Criticality", "Уровень критичности (MB)",
        "Уровень критичности системы в методологии MB.",
        data_type="enum", category="security", display_group="criticality",
        display_mode="badge",
        enum_values=["mission_critical", "business_critical", "operational", "supportive"],
        source_expectation=["SimpleOne"],
    ),
    attr(
        "application_type", "Application Type", "Тип системы",
        "Тип информационной системы.",
        data_type="enum", category="business", display_group="criticality",
        display_mode="badge",
        enum_values=["cots", "custom", "saas", "iaas", "paas", "other"],
        source_expectation=["SimpleOne"],
    ),
    attr(
        "application_operational_time", "Application Operational Time",
        "Время работы",
        "Интервал чч.мм-чч.мм использования приложения в бизнес-процессах.",
        data_type="string", category="business", display_group="criticality",
        example_values=["08:00-20:00"],
        source_expectation=["SimpleOne"],
    ),
    attr(
        "target_state", "Target State", "Целевое состояние",
        "Этап жизненного цикла ПО: plan / build / run / retire / decommissioned.",
        data_type="enum", category="lifecycle", display_group="criticality",
        display_mode="badge",
        enum_values=["plan", "build", "run", "retire", "decommissioned"],
        source_expectation=["SimpleOne"],
    ),

    # ==================== display_group: ownership (6) ====================
    attr(
        "owner_team_id", "Owner Team", "Команда-владелец системы",
        "Команда, осуществляющая разработку и развитие системы.",
        data_type="id", category="organizational", display_group="ownership",
        display_mode="entity_ref",
        ref_kind="team",
        required=True,
        source_expectation=["SimpleOne"],
        quality_expectation="required_for_mvp",
    ),
    attr(
        "business_owner_employee_id", "Business Owner", "Бизнес-владелец",
        "Контактное лицо Бизнеса, ответственное за использование системы. "
        "Product Owner команды-владельца или руководитель направления, которое "
        "делает систему (B-2).",
        data_type="id", category="organizational", display_group="ownership",
        display_mode="entity_ref",
        ref_kind="employee",
        required=True,
        source_expectation=["SimpleOne"],
        quality_expectation="required_for_mvp",
    ),
    attr(
        "business_owner_delegate_id", "Business Owner Delegate",
        "Заместитель бизнес-владельца",
        "Ответственный представитель бизнес-владельца.",
        data_type="id", category="organizational", display_group="ownership",
        display_mode="entity_ref",
        ref_kind="employee",
        source_expectation=["SimpleOne"],
    ),
    attr(
        "it_owner_employee_id", "IT Owner", "ИТ-владелец",
        "Контактное лицо ИТ, ответственное за развитие и эксплуатацию системы. "
        "TechLead команды или сотрудник с ролью ответственного за развитие "
        "и поддержку.",
        data_type="id", category="organizational", display_group="ownership",
        display_mode="entity_ref",
        ref_kind="employee",
        required=True,
        source_expectation=["SimpleOne"],
        quality_expectation="required_for_mvp",
    ),
    attr(
        "enterprise_architect_id", "Enterprise Architect",
        "Корпоративный архитектор",
        "Архитектор, ответственный за развитие и интеграцию системы в "
        "архитектуру банка.",
        data_type="id", category="organizational", display_group="ownership",
        display_mode="entity_ref",
        ref_kind="employee",
        source_expectation=["SimpleOne"],
    ),
    attr(
        "legal_entity_org_unit_id", "Legal Entity",
        "Юридическое лицо, использующее ПО",
        "Юридическое лицо-владелец. Заполняется только для ПО от юр.лиц. "
        "группы, не являющихся РайффайзенБанком.",
        data_type="id", category="organizational", display_group="ownership",
        display_mode="entity_ref",
        ref_kind="organizational_unit",
        source_expectation=["SimpleOne"],
    ),

    # ==================== display_group: bcp (5) ====================
    attr(
        "rto_bcp", "Recovery Time Objective (BCP & Support)",
        "Допустимое время простоя",
        "Допустимое время простоя системы в случае сбоя (RTO).",
        data_type="number", category="security", display_group="bcp",
        unit="minutes",
        source_expectation=["SimpleOne", "AppSec"],
    ),
    attr(
        "rpo_bcp", "Recovery Point Objective (BCP & Support)",
        "Допустимый объём потерь",
        "Допустимый период возможных потерь данных в случае сбоя (RPO).",
        data_type="number", category="security", display_group="bcp",
        unit="hours",
        source_expectation=["SimpleOne", "AppSec"],
    ),
    attr(
        "availability_percent", "Availability (%)",
        "Доступность системы",
        "Целевое значение доступности системы за год, выраженное в %.",
        data_type="number", category="security", display_group="bcp",
        unit="percent",
        source_expectation=["SimpleOne"],
        example_values=[99.9],
    ),
    attr(
        "availability_class", "Availability Class",
        "Уровень доступности системы по оценке RBI",
        "Класс доступности системы согласно политикам и методологии RBI.",
        data_type="enum", category="security", display_group="bcp",
        display_mode="badge",
        enum_values=["class_1", "class_2", "class_3", "class_4", "class_5"],
        source_expectation=["SimpleOne"],
    ),
    attr(
        "integrity_class", "Integrity Class",
        "Класс целостности данных",
        "Класс целостности данных, обрабатываемых системой.",
        data_type="enum", category="security", display_group="bcp",
        display_mode="badge",
        enum_values=["low", "medium", "high", "critical"],
        source_expectation=["SimpleOne"],
    ),

    # ==================== display_group: data_classification (6) ====================
    attr(
        "data_classification_level", "Data Classification Level",
        "Уровень конфиденциальности данных",
        "Уровень конфиденциальности данных, обрабатываемых в системе или "
        "планируемых к обработке после ввода в эксплуатацию.",
        data_type="enum", category="security", display_group="data_classification",
        display_mode="badge",
        enum_values=["public", "internal", "restricted", "confidential", "secret"],
        source_expectation=["SimpleOne"],
        sensitivity="confidential",
    ),
    attr(
        "personal_data", "Personal Data",
        "Персональные данные",
        "Обрабатываются ли в системе персональные данные.",
        data_type="boolean", category="security", display_group="data_classification",
        display_mode="badge",
        source_expectation=["SimpleOne"],
        sensitivity="confidential",
    ),
    attr(
        "bank_secret", "Bank Secret",
        "Банковская тайна",
        "Обрабатываются ли в системе сведения, составляющие банковскую тайну.",
        data_type="boolean", category="security", display_group="data_classification",
        display_mode="badge",
        source_expectation=["SimpleOne"],
        sensitivity="confidential",
    ),
    attr(
        "commercial_secret", "Commercial Secret",
        "Коммерческая тайна",
        "Обрабатываются ли в системе сведения, составляющие коммерческую тайну.",
        data_type="boolean", category="security", display_group="data_classification",
        display_mode="badge",
        source_expectation=["SimpleOne"],
        sensitivity="confidential",
    ),
    attr(
        "insider_information", "Insider Information",
        "Инсайдерская информация",
        "Обрабатывается ли в системе инсайдерская информация.",
        data_type="boolean", category="security", display_group="data_classification",
        display_mode="badge",
        source_expectation=["SimpleOne"],
        sensitivity="confidential",
    ),
    attr(
        "other_confidential_information", "Other Confidential Information",
        "Иная конфиденциальная информация",
        "Обрабатывается ли в системе иная конфиденциальная информация.",
        data_type="boolean", category="security", display_group="data_classification",
        display_mode="badge",
        source_expectation=["SimpleOne"],
        sensitivity="confidential",
    ),

    # ==================== display_group: pci (7) ====================
    attr(
        "audit_pci_dss", "PCI DSS Audit",
        "Аудит PCI DSS",
        "Подпадает ли система под аудит PCI DSS.",
        data_type="boolean", category="security", display_group="pci",
        display_mode="badge",
        source_expectation=["SimpleOne"],
        sensitivity="confidential",
    ),
    attr(
        "applicability_pci_dss", "Applicability of PCI DSS",
        "Применимость PCI DSS",
        "ИТ-система обрабатывает любые карточные данные либо непосредственно "
        "подключена к системам, которые их обрабатывают.",
        data_type="boolean", category="security", display_group="pci",
        display_mode="badge",
        source_expectation=["SimpleOne"],
        sensitivity="confidential",
    ),
    attr(
        "system_interacts_with_pci_dss", "System Interacts with PCI DSS",
        "Взаимодействие с контуром PCI DSS",
        "Присутствует любое взаимодействие с системами, которые находятся "
        "в контуре PCI DSS.",
        data_type="boolean", category="security", display_group="pci",
        display_mode="badge",
        source_expectation=["SimpleOne"],
        sensitivity="confidential",
    ),
    attr(
        "card_personalization", "Card Personalization",
        "Персонализация карт",
        "Участвует ли система в процессе выпуска именных пластиковых карт "
        "Райффайзенбанком.",
        data_type="boolean", category="security", display_group="pci",
        display_mode="badge",
        source_expectation=["SimpleOne"],
        sensitivity="confidential",
    ),
    attr(
        "payment_card_information", "Payment Card Information",
        "Данные платежных карт",
        "Обрабатываются ли данные банковских карт (PAN, cardholder name, "
        "дата истечения, service code, CAV2/CVC2/CVV2/CID, PIN).",
        data_type="boolean", category="security", display_group="pci",
        display_mode="badge",
        source_expectation=["SimpleOne"],
        sensitivity="confidential",
    ),
    attr(
        "pci_raiffeisen", "PCI Raiffeisen",
        "Данные платежных карт Райффайзенбанка",
        "Обрабатываются ли данные карт, выпущенных Райффайзенбанком. "
        "Определяется по первым шести цифрам номера карты (BIN).",
        data_type="boolean", category="security", display_group="pci",
        display_mode="badge",
        source_expectation=["SimpleOne"],
        sensitivity="confidential",
    ),
    attr(
        "pci_other_bank", "PCI Other Bank",
        "Данные платежных карт других банков",
        "Обрабатываются ли данные карт, выпущенных другими банками. "
        "Определяется по BIN карты.",
        data_type="boolean", category="security", display_group="pci",
        display_mode="badge",
        source_expectation=["SimpleOne"],
        sensitivity="confidential",
    ),

    # ==================== display_group: exposure (2) ====================
    attr(
        "internet_facing", "Internet Facing",
        "Доступна из сети Интернет",
        "Доступна ли система из сети Интернет.",
        data_type="boolean", category="security", display_group="exposure",
        display_mode="badge",
        source_expectation=["SimpleOne"],
    ),
    attr(
        "infosec_solution", "InfoSec Solution",
        "Решение по информационной безопасности",
        "Является ли система решением по информационной безопасности.",
        data_type="boolean", category="security", display_group="exposure",
        display_mode="badge",
        source_expectation=["SimpleOne"],
    ),

    # ==================== display_group: support (3) ====================
    attr(
        "support_group", "Support Group",
        "Группа поддержки",
        "Группа поддержки, на которую назначаются задачи по системе "
        "(аварии, инциденты, уведомления).",
        data_type="string", category="organizational", display_group="support",
        source_expectation=["SimpleOne"],
    ),
    attr(
        "support_expert_1_id", "Support Expert 1",
        "Эксперт поддержки",
        "Руководитель подразделения поддержки или штатный сотрудник, "
        "выполняющий ИТ-поддержку. Контактное лицо по техническим вопросам, "
        "авариям, проблемам и согласованиям CRQ.",
        data_type="id", category="organizational", display_group="support",
        display_mode="entity_ref",
        ref_kind="employee",
        source_expectation=["SimpleOne"],
    ),
    attr(
        "support_expert_2_id", "Support Expert 2 (Deputy)",
        "Заместитель эксперта поддержки",
        "Представитель ответственного за поддержку. Контактное лицо при "
        "недоступности эксперта поддержки.",
        data_type="id", category="organizational", display_group="support",
        display_mode="entity_ref",
        ref_kind="employee",
        source_expectation=["SimpleOne"],
    ),
]

for idx, attribute in enumerate(IT_SYSTEM_ATTRIBUTES, start=1):
    attribute.setdefault("display_order", idx * 10)


def main() -> int:
    print(f"[macwo527_phase1] Loading {METAMODEL_PATH}")
    with METAMODEL_PATH.open("r", encoding="utf-8") as f:
        model = yaml.safe_load(f)

    target_kind = None
    for kind in model.get("entity_kinds", []):
        if kind.get("id") == "it_system":
            target_kind = kind
            break

    if target_kind is None:
        print("[macwo527_phase1] ERROR: it_system entity_kind not found", file=sys.stderr)
        return 2

    existing_ids = {a.get("id") for a in target_kind.get("attributes", []) if a.get("id")}
    print(f"[macwo527_phase1] Existing attributes: {len(existing_ids)}")

    attributes = target_kind.setdefault("attributes", [])
    added = 0
    skipped = 0
    for new_attr in IT_SYSTEM_ATTRIBUTES:
        if new_attr["id"] in existing_ids:
            skipped += 1
            continue
        attributes.append(new_attr)
        existing_ids.add(new_attr["id"])
        added += 1

    print(f"[macwo527_phase1] Added {added}, skipped {skipped}")
    print(f"[macwo527_phase1] Total now: {len(attributes)}")

    if added == 0:
        return 0

    with METAMODEL_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(model, f, allow_unicode=True, sort_keys=False, width=120, default_flow_style=False)
    print("[macwo527_phase1] Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
