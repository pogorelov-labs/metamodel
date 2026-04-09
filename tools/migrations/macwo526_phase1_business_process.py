"""MACWO-526 Phase 1: Port PDF business_process attributes into metamodel.yaml.

Source: ~/msc_1/meta/глоссарий и атрибуты/атрибутивный_состав.yaml (PDF 1.0)
Target: model/metamodel.yaml → entity_kinds[business_process].attributes

PDF 1.0 contains 57 attributes for business_process. This migration adds 54
new attributes in v2 contract form (data_type, cardinality, required,
category, display_mode, display_group, status, introduced_in).

Three PDF attributes are SKIPPED because they overlap with existing legacy
attributes and the plan explicitly does not touch legacy fields:

- PDF #9  "Домен"              ≡ existing business_process.business_domain_id
- PDF #17 "Бизнес-способность" ≡ existing business_process.business_capability_id
- PDF #36 "Сотрудник-владелец" ≡ existing business_process.business_owner_id

Legacy `business_process.tier` is left untouched (it represents generic
criticality; PDF #11 and #12 are specific regulatory/BCM classifications
and are added as new attributes).

Attributes are grouped by display_group for readability in entity cards:
core, regulatory, ics, bcm, ops, dependencies, ownership, landscape, notes.

Idempotent — each attribute is appended only if its id is not already present
in business_process.attributes. Re-running on a migrated repo is a no-op.
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
    metamodel_level: str = "business_details",
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
    """Build an attribute dict in v2 contract form."""
    result: dict = {
        "id": f"business_process.{field_id}",
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
        # data_type remains 'id' (harness whitelist); ref_kind hints at
        # target entity_kind for runtime projection.
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


# All 54 new attributes, ordered by display_group then by PDF position.
BUSINESS_PROCESS_ATTRIBUTES: list[dict] = [
    # ==================== display_group: core (13) ====================
    # PDF #1 Код
    attr(
        "code", "Code", "Код",
        "Уникальный идентификатор процесса.",
        data_type="string", category="identity", display_group="core",
        metamodel_level="business_details",
        required=True,
        example_values=["BP0001094"],
        source_expectation=["S1"],
        quality_expectation="required_for_mvp",
    ),
    # PDF #3 Название
    attr(
        "name", "Name", "Название",
        "Наименование процесса.",
        data_type="string", category="identity", display_group="core",
        required=True,
        example_values=["Верификация клиента"],
        quality_expectation="required_for_mvp",
    ),
    # PDF #4 Название (Eng)
    attr(
        "name_eng", "Name (Eng)", "Название (Eng)",
        "Наименование процесса на английском.",
        data_type="string", category="identity", display_group="core",
    ),
    # PDF #5 Краткое описание
    attr(
        "short_description", "Short Description", "Краткое описание",
        "Цель и основные действия, бизнес-требования, ограничения, политики, "
        "регламенты (для ручного труда).",
        data_type="text", category="business", display_group="core",
        display_mode="long_text",
        example_values=["Верификация данных клиента с целью выдачи кредита"],
    ),
    # PDF #10 Board Area
    attr(
        "board_area", "Board Area", "Board Area",
        "Управленческий блок (Board Area), к которому относится процесс.",
        data_type="string", category="business", display_group="core",
        display_mode="badge",
        required=True,
        quality_expectation="required_for_mvp",
    ),
    # PDF #18 Статус
    attr(
        "status_lifecycle", "Lifecycle Status", "Статус",
        "Жизненный цикл записи процесса: draft / production / archive.",
        data_type="enum", category="lifecycle", display_group="core",
        display_mode="badge",
        required=True,
        enum_values=["draft", "production", "archive"],
        example_values=["production"],
        quality_expectation="required_for_mvp",
    ),
    # PDF #19 Триггер
    attr(
        "trigger", "Trigger", "Триггер",
        "События, запускающие бизнес-процесс.",
        data_type="text", category="business", display_group="core",
        display_mode="long_text",
        required=True,
        example_values=["Данные клиента заполнены и отправлены на верификацию"],
    ),
    # PDF #22 Результат
    attr(
        "result", "Result", "Результат",
        "Описание результата на выходе процесса.",
        data_type="text", category="business", display_group="core",
        display_mode="long_text",
        required=True,
        example_values=['Клиент переведён в статус "Проверен"'],
    ),
    # PDF #50 Комментарии
    attr(
        "comments", "Comments", "Комментарии",
        "Свободные комментарии владельца процесса.",
        data_type="text", category="custom", display_group="core",
        display_mode="long_text",
    ),
    # PDF #55 Версия
    attr(
        "version", "Version", "Версия",
        "Версия бизнес-процесса (semver или простая нумерация).",
        data_type="string", category="lifecycle", display_group="core",
        required=True,
        example_values=["1.0"],
        quality_expectation="required_for_mvp",
    ),
    # PDF #56 Дата создания
    attr(
        "created_at", "Created At", "Дата создания",
        "Дата создания записи процесса.",
        data_type="string", category="lifecycle", display_group="core",
        display_mode="date",
        required=True,
        example_values=["2024-11-12"],
    ),
    # PDF #57 Дата редактирования
    attr(
        "updated_at", "Updated At", "Дата редактирования",
        "Дата последнего изменения записи процесса.",
        data_type="string", category="lifecycle", display_group="core",
        display_mode="date",
        required=True,
        example_values=["2024-11-17"],
    ),
    # PDF #16 Техпроцесс ЦБ
    attr(
        "cbr_techprocess_code", "CBR Techprocess Code", "Код Техпроцесса ЦБ",
        "Код Техпроцесса ЦБ РФ, реализуемого данным бизнес-процессом.",
        data_type="string", category="evidence", display_group="core",
        example_values=["ТПрКО9"],
    ),

    # ==================== display_group: regulatory (5) ====================
    # PDF #2 Код 716-П
    attr(
        "code_716p", "Code 716-P", "Код 716-П",
        "Классификатор процесса по положению ЦБ РФ 716-П.",
        data_type="string", category="evidence", display_group="regulatory",
        example_values=["3.9.1."],
        source_expectation=["S1", "Archer"],
    ),
    # PDF #6 Классификатор процесса (риски)
    attr(
        "risk_classifier_l4", "Risk Classifier (L4)", "Классификатор процесса (риски)",
        "Значение 4-го уровня классификации процессов ОперРисков, включая все "
        "предыдущие уровни.",
        data_type="text", category="business", display_group="regulatory",
        display_mode="long_text",
        required=True,
        source_expectation=["S1"],
        example_values=[
            "2. Операции и сделки на финансовом рынке -> 2.2. Операции с "
            "производными финансовыми инструментами -> 2.2.1. Операции с "
            "производными финансовыми инструментами -> 2.2.2.2. Алгоритмическая "
            "торговля производными финансовыми инструментами"
        ],
    ),
    # PDF #11 Критичность процесса по 716-П
    attr(
        "criticality_716p", "Criticality (716-P)", "Критичность процесса по 716-П",
        "Критичность процесса согласно 716-П: critically_important / main / other.",
        data_type="enum", category="business", display_group="regulatory",
        display_mode="badge",
        required=True,
        enum_values=["critically_important", "main", "other"],
        example_values=["main"],
        source_expectation=["S1"],
    ),
    # PDF #42 ВНД
    attr(
        "internal_regulation", "Internal Regulation", "ВНД",
        "Реквизиты внутренних нормативных документов, регулирующих процесс.",
        data_type="text", category="evidence", display_group="regulatory",
        display_mode="long_text",
        example_values=['Приказ №235 "О регламенте проверки клиентов"'],
    ),
    # PDF #43 НПА
    attr(
        "npa", "External Regulation (NPA)", "НПА",
        "Реквизиты нормативно-правовых актов, регулирующих процесс.",
        data_type="text", category="evidence", display_group="regulatory",
        display_mode="long_text",
        example_values=['Положение Банка России №745 "О работе с данными клиентов"'],
    ),

    # ==================== display_group: ics (9) ====================
    # PDF #7 Приоритизация процесса ICS
    attr(
        "ics_prioritization", "ICS Prioritization", "Приоритизация процесса ICS",
        "Приоритизация процесса в рамках методологии ICS: Key / Non-Key.",
        data_type="enum", category="business", display_group="ics",
        display_mode="badge",
        required=True,
        enum_values=["key", "non_key"],
        example_values=["key"],
        source_expectation=["S1"],
    ),
    # PDF #8 Классификация процесса ICS
    attr(
        "ics_classification", "ICS Classification", "Классификация процесса ICS",
        "Классификация процесса в рамках методологии ICS: Key Regulatory / "
        "Key Business / Financial Reporting / Other.",
        data_type="enum", category="business", display_group="ics",
        display_mode="badge",
        required=True,
        enum_values=["key_regulatory", "key_business", "financial_reporting", "other"],
        example_values=["key_business"],
        source_expectation=["S1"],
    ),
    # PDF #33 Риски ИБ
    attr(
        "ib_risks", "InfoSec Risks", "Риски ИБ",
        "Маппинг на типы рисков информационной безопасности.",
        data_type="string", category="security", display_group="ics",
        cardinality="many",
        display_mode="chip_list",
        source_expectation=["S1"],
    ),
    # PDF #34 Риски Опер
    attr(
        "op_risks", "Operational Risks", "Риски Опер",
        "Маппинг на типы операционных рисков.",
        data_type="string", category="business", display_group="ics",
        cardinality="many",
        display_mode="chip_list",
        source_expectation=["S1"],
    ),
    # PDF #35 Контроли ICS
    attr(
        "ics_controls", "ICS Controls", "Контроли ICS",
        "Маппинг на операционные контроли ICS.",
        data_type="string", category="business", display_group="ics",
        cardinality="many",
        display_mode="chip_list",
        source_expectation=["S1"],
        example_values=[
            "Reconciliation of operation parameters in systems Midas, WSS, Bloomberg"
        ],
    ),
    # PDF #44 Код (Арчер)
    attr(
        "archer_id", "Archer ID", "Код (Арчер)",
        "Уникальный идентификатор процесса в системе Archer.",
        data_type="string", category="identity", display_group="ics",
        required=True,
        source_expectation=["Archer"],
        example_values=["RBRU_BP_3100"],
    ),
    # PDF #45 Название (Арчер)
    attr(
        "archer_name", "Archer Name", "Название (Арчер)",
        "Название процесса в системе Archer.",
        data_type="string", category="identity", display_group="ics",
        required=True,
        source_expectation=["Archer"],
        example_values=["Initial placement of bonds"],
    ),
    # PDF #46 ORM — urn_ref to employee (paired with rel in phase2)
    attr(
        "orm_owner_id", "ORM Owner", "ORM",
        "ФИО владельца риска (Operational Risk Manager).",
        data_type="id", category="organizational", display_group="ics",
        display_mode="entity_ref",
        ref_kind="employee",
        source_expectation=["S1"],
    ),
    # PDF #47 DORS — many urn_ref to employee
    attr(
        "dors_owner_ids", "DORS Owners", "DORS",
        "ФИО владельцев риска второй линии (Delegated Operational Risk "
        "Specialists).",
        data_type="id", category="organizational", display_group="ics",
        display_mode="entity_ref",
        cardinality="many",
        ref_kind="employee",
        source_expectation=["S1"],
    ),

    # ==================== display_group: bcm (11) ====================
    # PDF #12 Критичность (BCM)
    attr(
        "bcm_criticality", "BCM Criticality", "Критичность (BCM)",
        "Критичность процесса согласно BCM: Mission critical / Business "
        "critical / Operational / Supportive / Do not recovery / Not defined.",
        data_type="enum", category="security", display_group="bcm",
        display_mode="badge",
        enum_values=[
            "mission_critical",
            "business_critical",
            "operational",
            "supportive",
            "do_not_recovery",
            "not_defined",
        ],
        example_values=["business_critical"],
        source_expectation=["BCM"],
    ),
    # PDF #13 Confidentiality (CIA — на будущее, пока string)
    attr(
        "confidentiality_ref", "Confidentiality", "Confidentiality (CIA)",
        "Обеспечение доступа к конфиденциальным данным процесса только для "
        "тех, у кого есть соответствующее разрешение. На будущее.",
        data_type="text", category="security", display_group="bcm",
        display_mode="long_text",
        source_expectation=["S1"],
    ),
    # PDF #14 Integrity
    attr(
        "integrity_ref", "Integrity", "Integrity (CIA)",
        "Защита данных процесса от изменений, подделок или уничтожения — "
        "намеренно или случайно. На будущее.",
        data_type="text", category="security", display_group="bcm",
        display_mode="long_text",
        source_expectation=["S1"],
    ),
    # PDF #15 Availability
    attr(
        "availability_ref", "Availability", "Availability (CIA)",
        "Гарантия, что процесс доступен и пригоден для исполнения при "
        "необходимости. На будущее.",
        data_type="text", category="security", display_group="bcm",
        display_mode="long_text",
        source_expectation=["S1"],
    ),
    # PDF #27 RTO BP
    attr(
        "rto_bp", "Recovery Time Objective (BP)", "RTO BP",
        "Максимально допустимое время простоя процесса. См. MACWO-533 о "
        "согласовании с sla.response_time.",
        data_type="number", category="security", display_group="bcm",
        unit="minutes",
        source_expectation=["AppSec"],
        example_values=[5],
    ),
    # PDF #28 RPO BP
    attr(
        "rpo_bp", "Recovery Point Objective (BP)", "RPO BP",
        "Максимально допустимый период потери данных процесса.",
        data_type="number", category="security", display_group="bcm",
        unit="hours",
        source_expectation=["AppSec"],
    ),
    # PDF #29 MTPD BP
    attr(
        "mtpd_bp", "Maximum Tolerable Period of Disruption", "MTPD BP",
        "Максимально допустимый период нарушения работы процесса.",
        data_type="number", category="security", display_group="bcm",
        unit="hours",
        source_expectation=["AppSec"],
        example_values=[1],
    ),
    # PDF #30 MBCO BP
    attr(
        "mbco_bp", "Minimum Business Continuity Objective", "MBCO BP",
        "Минимальный уровень непрерывности бизнеса, поддерживаемый процессом "
        "в условиях деградации. Процент от нормального уровня.",
        data_type="number", category="security", display_group="bcm",
        unit="percent",
        source_expectation=["AppSec"],
        example_values=[50],
    ),
    # PDF #52 Влияние на клиентские сегменты — enum many
    attr(
        "customer_segment_impact", "Customer Segment Impact",
        "Влияние на клиентские сегменты",
        "Клиентские сегменты, на которые влияет процесс.",
        data_type="enum", category="business", display_group="bcm",
        display_mode="chip_list",
        cardinality="many",
        enum_values=[
            "mass",
            "affluent",
            "private",
            "micro",
            "small",
            "medium",
            "corporate",
            "international",
        ],
        example_values=[["mass", "affluent"]],
        source_expectation=["BCM"],
    ),
    # PDF #53 Есть внешний контрагент
    attr(
        "has_external_counterparty", "Has External Counterparty",
        "Есть внешний контрагент",
        "Связан ли процесс с внешним контрагентом.",
        data_type="boolean", category="business", display_group="bcm",
        display_mode="badge",
        required=True,
        example_values=[True],
        source_expectation=["BCM", "Risks"],
    ),
    # PDF #54 Наименования контрагентов
    attr(
        "counterparty_names", "Counterparty Names", "Наименования контрагентов",
        "Наименования внешних контрагентов процесса (если есть).",
        data_type="string", category="business", display_group="bcm",
        cardinality="many",
        display_mode="chip_list",
        example_values=[["Компания Х"]],
        source_expectation=["BCM", "Risks"],
    ),

    # ==================== display_group: ops (6) ====================
    # PDF #23 Среднее время выполнения
    attr(
        "avg_execution_time", "Average Execution Time",
        "Среднее время выполнения",
        "Общее среднее (арифметическое) время от старта до завершения процесса "
        "по историческим данным.",
        data_type="number", category="data", display_group="ops",
        unit="days",
        source_expectation=["Ops"],
        example_values=[2],
    ),
    # PDF #24 Дисперсия времени выполнения
    attr(
        "execution_time_variance", "Execution Time Variance",
        "Дисперсия времени выполнения",
        "Среднеквадратичное отклонение времени выполнения процесса, делённое "
        "на среднее время выполнения процесса.",
        data_type="number", category="data", display_group="ops",
        unit="percent",
        source_expectation=["Ops"],
    ),
    # PDF #25 First Pass Yield
    attr(
        "first_pass_yield", "First Pass Yield",
        "Процент завершения без ошибок (FPY)",
        "Процент завершения процесса без ошибок с первой попытки.",
        data_type="number", category="data", display_group="ops",
        unit="percent",
        source_expectation=["Ops"],
        example_values=[98],
    ),
    # PDF #26 Затраты
    attr(
        "operating_cost", "Operating Cost", "Затраты",
        "Операционные издержки процесса.",
        data_type="number", category="data", display_group="ops",
        unit="rub",
        source_expectation=["Ops"],
        example_values=[20000],
    ),
    # PDF #31 FAI
    attr(
        "fai", "Function Automation Index (FAI)", "FAI",
        "Индекс автоматизации процесса: отношение автоматизированных FTE "
        "этапов экземпляров процессов к общему количеству FTE этапов.",
        data_type="number", category="data", display_group="ops",
        unit="percent",
        source_expectation=["Ops"],
    ),
    # PDF #32 STP
    attr(
        "stp", "Straight Through Processing (STP)", "STP",
        "Уровень автоматизации сквозной обработки: отношение количества "
        "экземпляров процесса, реализованных полностью автоматически, к "
        "общему количеству экземпляров.",
        data_type="number", category="data", display_group="ops",
        unit="percent",
        source_expectation=["Ops"],
    ),

    # ==================== display_group: dependencies (2) ====================
    # PDF #20 Входящие зависимости — relation in phase2, keep as string for ingest
    attr(
        "inbound_process_codes", "Inbound Process Codes", "Входящие зависимости",
        "Коды бизнес-процессов, результаты которых поступают на вход данного "
        "процесса (от каких процессов зависит данный процесс).",
        data_type="string", category="integration", display_group="dependencies",
        cardinality="many",
        display_mode="chip_list",
        required=True,
        source_expectation=["BCM"],
    ),
    # PDF #21 Исходящие зависимости
    attr(
        "outbound_process_codes", "Outbound Process Codes", "Исходящие зависимости",
        "Коды бизнес-процессов, которые получают на вход результаты данного "
        "процесса.",
        data_type="string", category="integration", display_group="dependencies",
        cardinality="many",
        display_mode="chip_list",
        required=True,
        source_expectation=["BCM"],
    ),

    # ==================== display_group: ownership (6) ====================
    # PDF #37 Подразделение-владелец (string, not ref — PDF says "Текст")
    attr(
        "owner_department", "Owner Department", "Подразделение-владелец",
        "Подразделение-владелец процесса (линейная структура).",
        data_type="string", category="organizational", display_group="ownership",
        required=True,
        example_values=["Отдел верификации клиентов"],
    ),
    # PDF #38 Команда-владелец — urn_ref to team
    attr(
        "owner_team_id", "Owner Team", "Команда-владелец",
        "Agile- или функциональная команда, владеющая процессом.",
        data_type="id", category="organizational", display_group="ownership",
        display_mode="entity_ref",
        ref_kind="team",
        required=True,
    ),
    # PDF #39 Сотрудники-участники — many urn_ref employee
    attr(
        "participant_employee_ids", "Participant Employees", "Сотрудники-участники",
        "ФИО сотрудников-участников процесса.",
        data_type="id", category="organizational", display_group="ownership",
        display_mode="entity_ref",
        cardinality="many",
        ref_kind="employee",
        required=True,
    ),
    # PDF #40 Подразделения-участники — many urn_ref org_unit
    attr(
        "participant_org_unit_ids", "Participant Org Units", "Подразделения-участники",
        "Подразделения-участники процесса.",
        data_type="id", category="organizational", display_group="ownership",
        display_mode="entity_ref",
        cardinality="many",
        ref_kind="organizational_unit",
        required=True,
    ),
    # PDF #41 Коллегиальные органы-участники — string (no collective_body entity yet)
    attr(
        "participant_collective_bodies", "Participant Collective Bodies",
        "Коллегиальные органы-участники",
        "Коллегиальные органы, участвующие в процессе. На будущее может быть "
        "переведено на urn_ref после создания entity_kind collective_body.",
        data_type="string", category="organizational", display_group="ownership",
        cardinality="many",
        display_mode="chip_list",
        source_expectation=["S1"],
        example_values=[["Правление"]],
    ),
    # PDF #48 Сотрудник-владелец контроля — urn_ref employee
    attr(
        "control_owner_employee_id", "Control Owner Employee",
        "Сотрудник-владелец контроля",
        "ФИО сотрудника-владельца контроля.",
        data_type="id", category="organizational", display_group="ownership",
        display_mode="entity_ref",
        ref_kind="employee",
        required=True,
        source_expectation=["S1"],
    ),
    # PDF #49 Подразделение-владелец контроля — string (PDF says "Текст")
    attr(
        "control_owner_department", "Control Owner Department",
        "Подразделение-владелец контроля",
        "Подразделение-владелец контроля (линейная структура).",
        data_type="string", category="organizational", display_group="ownership",
        required=True,
        source_expectation=["S1"],
        example_values=["Отдел верификации клиентов"],
    ),

    # ==================== display_group: landscape (1) ====================
    # PDF #51 ИТ-системы — many urn_ref it_system
    attr(
        "related_it_system_ids", "Related IT Systems", "ИТ-системы",
        "Связанные ИТ-системы. На уровне связи могут уточняться tier и тип "
        "зависимости через qualifier в relation_catalog.",
        data_type="id", category="technical", display_group="landscape",
        display_mode="entity_ref",
        cardinality="many",
        ref_kind="it_system",
        source_expectation=["S1", "AppSec"],
    ),
]

# display_order is implied by position in the list above; harness doesn't
# enforce it, but we set it explicitly so entity cards show groups in the
# intended order.
for idx, attribute in enumerate(BUSINESS_PROCESS_ATTRIBUTES, start=1):
    attribute.setdefault("display_order", idx * 10)


def main() -> int:
    print(f"[macwo526_phase1] Loading {METAMODEL_PATH}")
    with METAMODEL_PATH.open("r", encoding="utf-8") as f:
        model = yaml.safe_load(f)

    target_kind = None
    for kind in model.get("entity_kinds", []):
        if kind.get("id") == "business_process":
            target_kind = kind
            break

    if target_kind is None:
        print("[macwo526_phase1] ERROR: business_process entity_kind not found", file=sys.stderr)
        return 2

    existing_ids = {a.get("id") for a in target_kind.get("attributes", []) if a.get("id")}
    print(f"[macwo526_phase1] Existing attributes on business_process: {len(existing_ids)}")

    attributes = target_kind.setdefault("attributes", [])
    added = 0
    skipped = 0
    for new_attr in BUSINESS_PROCESS_ATTRIBUTES:
        if new_attr["id"] in existing_ids:
            skipped += 1
            continue
        attributes.append(new_attr)
        existing_ids.add(new_attr["id"])
        added += 1

    print(f"[macwo526_phase1] Added {added} new attributes, skipped {skipped} (already present)")
    print(f"[macwo526_phase1] Total attributes on business_process now: {len(attributes)}")

    if added == 0:
        print("[macwo526_phase1] No changes — idempotent no-op")
        return 0

    print(f"[macwo526_phase1] Writing {METAMODEL_PATH}")
    with METAMODEL_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            model,
            f,
            allow_unicode=True,
            sort_keys=False,
            width=120,
            default_flow_style=False,
        )
    print("[macwo526_phase1] Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
