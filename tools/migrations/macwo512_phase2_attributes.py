"""MACWO-518 (Phase 2): Fill attributes for the remaining zero-attr entities.

After Phase 1 there are 18 entity_kinds with zero attributes. They split
into two groups:

- **P0 — critical (9 entities)** — backbone strategic/business/governance
  entities that are referenced everywhere: goal, value, employee, team,
  business_role, customer_segment, channel, requirement, sla. They get
  3-5 attributes each, hand-curated by category.
- **P1 / P2 — stubs (9 entities)** — process subtypes
  (business_function, business_operation, business_action), application
  layer (component_instance, vendor_product), infra/tooling (technology,
  source), and incomplete drafts (job, delivery_contract). They get
  ``status: stub`` so the partial state is visible to consumers and to
  the future contract-validator iteration.

Idempotent — re-running on a migrated repo is a no-op (status check on
each entity prevents double-stubbing; attribute lists are checked for
the canonical id before insertion).
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METAMODEL_PATH = REPO_ROOT / "model" / "metamodel.yaml"

# P0 — entities that get hand-curated attribute sets.
# Each list of attributes is appended in declared order; duplicates by id are
# skipped so the script stays idempotent.
P0_ATTRIBUTES: dict[str, list[dict]] = {
    "goal": [
        {"id": "goal.owner", "name": "Владелец цели", "metamodel_level": "strategic_view",
         "description": "Стейкхолдер, отвечающий за достижение цели."},
        {"id": "goal.status", "name": "Статус", "metamodel_level": "strategic_view",
         "description": "Статус цели: draft | active | achieved | abandoned."},
        {"id": "goal.target_date", "name": "Целевая дата", "metamodel_level": "strategic_view",
         "description": "Дата, к которой цель должна быть достигнута."},
        {"id": "goal.parent_goal_id", "name": "Родительская цель", "metamodel_level": "strategic_view",
         "description": "Идентификатор вышестоящей цели в иерархии."},
        {"id": "goal.kpi", "name": "KPI", "metamodel_level": "strategic_view",
         "description": "Ключевой показатель, по которому измеряется достижение цели."},
    ],
    "value": [
        {"id": "value.type", "name": "Тип ценности", "metamodel_level": "strategic_view",
         "description": "Тип ценности: monetary | functional | emotional | social | regulatory."},
        {"id": "value.target_audience", "name": "Целевая аудитория", "metamodel_level": "strategic_view",
         "description": "Сегмент клиентов или стейкхолдеров, для которых формируется ценность."},
        {"id": "value.measurement", "name": "Метрика измерения", "metamodel_level": "strategic_view",
         "description": "Каким показателем измеряется поставка ценности."},
    ],
    "employee": [
        {"id": "employee.employee_id", "name": "Табельный номер", "metamodel_level": "business_details",
         "description": "Уникальный идентификатор сотрудника в HR-системе."},
        {"id": "employee.position", "name": "Должность", "metamodel_level": "business_details",
         "description": "Формальная должность сотрудника."},
        {"id": "employee.department", "name": "Подразделение", "metamodel_level": "business_details",
         "description": "Подразделение, к которому относится сотрудник (organizational_unit)."},
        {"id": "employee.hire_date", "name": "Дата приёма", "metamodel_level": "business_details",
         "description": "Дата приёма сотрудника в банк."},
    ],
    "team": [
        {"id": "team.lead", "name": "Руководитель", "metamodel_level": "business_details",
         "description": "Сотрудник, выполняющий роль лидера команды."},
        {"id": "team.size", "name": "Размер", "metamodel_level": "business_details",
         "description": "Текущее количество сотрудников в команде."},
        {"id": "team.mission", "name": "Миссия", "metamodel_level": "business_details",
         "description": "Краткая формулировка зоны ответственности команды."},
        {"id": "team.kind", "name": "Тип команды", "metamodel_level": "business_details",
         "description": "Тип: product | platform | enabling | stream-aligned | complicated-subsystem."},
    ],
    "business_role": [
        {"id": "business_role.responsibility", "name": "Зона ответственности", "metamodel_level": "business_details",
         "description": "За что отвечает роль в бизнес-процессе."},
        {"id": "business_role.required_skills", "name": "Требуемые навыки", "metamodel_level": "business_details",
         "description": "Перечень компетенций, необходимых для выполнения роли."},
        {"id": "business_role.seniority", "name": "Уровень роли", "metamodel_level": "business_details",
         "description": "Уровень роли: junior | middle | senior | lead | head."},
    ],
    "customer_segment": [
        {"id": "customer_segment.segment_type", "name": "Тип сегмента", "metamodel_level": "strategic_view",
         "description": "Тип сегмента: retail | sme | corporate | private_banking | public_sector."},
        {"id": "customer_segment.size", "name": "Размер сегмента", "metamodel_level": "strategic_view",
         "description": "Оценка количества клиентов в сегменте."},
        {"id": "customer_segment.persona_ref", "name": "Ссылка на персону", "metamodel_level": "strategic_view",
         "description": "Ссылка на каноническую персону сегмента (если ведётся отдельно)."},
    ],
    "channel": [
        {"id": "channel.type", "name": "Тип канала", "metamodel_level": "business_details",
         "description": "Тип канала: branch | mobile_app | web | call_center | atm | partner_api."},
        {"id": "channel.availability", "name": "Доступность", "metamodel_level": "business_details",
         "description": "Часы доступности канала и SLA по аптайму."},
        {"id": "channel.sla_response_time", "name": "SLA по реакции", "metamodel_level": "business_details",
         "description": "Целевое время реакции канала на обращение клиента."},
    ],
    "requirement": [
        {"id": "requirement.priority", "name": "Приоритет", "metamodel_level": "business_details",
         "description": "Приоритет требования: must | should | could | wont (MoSCoW)."},
        {"id": "requirement.status", "name": "Статус", "metamodel_level": "business_details",
         "description": "Статус: draft | approved | implemented | deprecated."},
        {"id": "requirement.source", "name": "Источник", "metamodel_level": "business_details",
         "description": "Источник требования: stakeholder, regulator, business case, incident."},
        {"id": "requirement.acceptance_criteria", "name": "Критерии приёмки", "metamodel_level": "business_details",
         "description": "Условия, при которых требование считается выполненным."},
    ],
    "sla": [
        {"id": "sla.metric_target", "name": "Целевое значение", "metamodel_level": "solution_details",
         "description": "Целевое значение метрики, обязательство по поддержанию."},
        {"id": "sla.response_time", "name": "Время реакции", "metamodel_level": "solution_details",
         "description": "Максимальное время от регистрации инцидента до начала работ."},
        {"id": "sla.resolution_time", "name": "Время разрешения", "metamodel_level": "solution_details",
         "description": "Максимальное время от регистрации инцидента до его разрешения."},
        {"id": "sla.penalty", "name": "Штраф / последствия", "metamodel_level": "solution_details",
         "description": "Последствия нарушения SLA: финансовые санкции, эскалация, переоформление контракта."},
    ],
}

# P1 / P2 — entities that stay zero-attr but get explicitly marked as stubs.
STUB_ENTITY_IDS = {
    "business_function",
    "business_operation",
    "business_action",
    "vendor_product",
    "technology",
    "source",
    "component_instance",
    "delivery_contract",
    "job",
}


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_yaml(path: Path, data) -> None:
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, width=120)


def main() -> int:
    mm = load_yaml(METAMODEL_PATH)

    p0_added = 0
    stubs_marked = 0
    for entity in mm["entity_kinds"]:
        eid = entity["id"]
        if eid in P0_ATTRIBUTES:
            existing_ids = {a.get("id") for a in (entity.get("attributes") or [])}
            attrs = list(entity.get("attributes") or [])
            for new_attr in P0_ATTRIBUTES[eid]:
                if new_attr["id"] not in existing_ids:
                    attrs.append(new_attr)
                    p0_added += 1
            entity["attributes"] = attrs
        if eid in STUB_ENTITY_IDS and entity.get("status") != "stub":
            entity["status"] = "stub"
            stubs_marked += 1

    dump_yaml(METAMODEL_PATH, mm)
    print(f"MACWO-518 phase 2 migration applied:")
    print(f"  P0 attributes added: {p0_added}")
    print(f"  P1/P2 stubs marked:  {stubs_marked}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
