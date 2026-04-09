"""MACWO-530 Phase 1: Add new entity_kind 'event' to metamodel.yaml.

Source: PDF 1.0 — Общие сущности — Событие
Target: model/metamodel.yaml → entity_kinds[]

PDF describes Event as a fact of significant state change in business process,
system, or data lifecycle. Has timestamp and can trigger other processes.

The metamodel currently has only 'incident' which is a special case of events
with high severity. This PR adds the general Event entity_kind.

Idempotent — adds the entity only if not present.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METAMODEL_PATH = REPO_ROOT / "model" / "metamodel.yaml"
INTRODUCED_IN = "2.1"

EVENT_ENTITY = {
    "id": "event",
    "name": "Event",
    "name_ru": "Событие",
    "metamodel_level": "solution_details",
    "category": "operational",
    "description": (
        "Факт наступления значимого изменения состояния в рамках бизнес-процесса, "
        "работы системы или жизненного цикла данных, который фиксируется, имеет "
        "временную метку и может служить триггером для других процессов, "
        "уведомлений или аналитики."
    ),
    "scope_notes": (
        "Всегда имеет тип события, временную метку и источник. Может содержать "
        "полезную нагрузку (payload) с деталями. Регистрируется в логах, "
        "мониторинговых системах или хабе/шине событий. Может быть связано с "
        "Incident, Дата Продуктом, Бизнес-процессом, Пайплайном."
    ),
    "aliases": [
        {"value": "event", "lang": "en", "alias_type": "synonym", "status": "active"},
        {"value": "событие", "lang": "ru", "alias_type": "synonym", "status": "active"},
    ],
    "examples": [
        "Заявка переведена в статус Одобрена (бизнес-событие)",
        "Пайплайн завершился с ошибкой (системное событие)",
        "Нарушено требование SLA по актуальности данных (событие качества данных)",
        "Пользователь получил доступ к конфиденциальным данным (событие безопасности)",
    ],
    "usage_purpose": (
        "Фиксировать значимые изменения состояния и связывать их с реакциями, "
        "уведомлениями и аналитикой."
    ),
    "status": "active",
    "introduced_in": INTRODUCED_IN,
    "attributes": [
        {
            "id": "event.event_type",
            "name": "Event Type",
            "name_ru": "Тип события",
            "description": "Тип события: business, system, data, security.",
            "data_type": "enum",
            "enum_values": ["business", "system", "data", "security"],
            "cardinality": "one",
            "required": True,
            "category": "business",
            "metamodel_level": "solution_details",
            "display_mode": "badge",
            "display_group": "core",
            "status": "active",
            "introduced_in": INTRODUCED_IN,
            "quality_expectation": "required_for_mvp",
            "display_order": 10,
        },
        {
            "id": "event.occurred_at",
            "name": "Occurred At",
            "name_ru": "Время наступления",
            "description": "Временная метка события (UTC, ISO 8601).",
            "data_type": "string",
            "cardinality": "one",
            "required": True,
            "category": "lifecycle",
            "metamodel_level": "solution_details",
            "display_mode": "datetime",
            "display_group": "core",
            "status": "active",
            "introduced_in": INTRODUCED_IN,
            "quality_expectation": "required_for_mvp",
            "example_values": ["2026-04-09T10:30:00Z"],
            "display_order": 20,
        },
        {
            "id": "event.source",
            "name": "Source",
            "name_ru": "Источник",
            "description": "Система или компонент, зафиксировавший событие.",
            "data_type": "string",
            "cardinality": "one",
            "required": True,
            "category": "technical",
            "metamodel_level": "solution_details",
            "display_mode": "plain",
            "display_group": "core",
            "status": "active",
            "introduced_in": INTRODUCED_IN,
            "quality_expectation": "required_for_mvp",
            "example_values": ["payment-service", "ETL-airflow", "CRM"],
            "display_order": 30,
        },
        {
            "id": "event.payload",
            "name": "Payload",
            "name_ru": "Полезная нагрузка",
            "description": (
                "Детали события в формате JSON: идентификатор объекта, "
                "старый/новый статус, значения метрик."
            ),
            "data_type": "text",
            "cardinality": "one",
            "required": False,
            "category": "data",
            "metamodel_level": "solution_details",
            "display_mode": "json",
            "display_group": "details",
            "status": "active",
            "introduced_in": INTRODUCED_IN,
            "display_order": 40,
        },
        {
            "id": "event.severity",
            "name": "Severity",
            "name_ru": "Серьёзность",
            "description": (
                "Опциональная оценка серьёзности события: info, warning, error, critical."
            ),
            "data_type": "enum",
            "enum_values": ["info", "warning", "error", "critical"],
            "cardinality": "one",
            "required": False,
            "category": "business",
            "metamodel_level": "solution_details",
            "display_mode": "badge",
            "display_group": "details",
            "status": "active",
            "introduced_in": INTRODUCED_IN,
            "display_order": 50,
        },
    ],
}


def main():
    print(f"[macwo530_phase1] Loading {METAMODEL_PATH}")
    with METAMODEL_PATH.open("r", encoding="utf-8") as f:
        model = yaml.safe_load(f)

    entity_kinds = model.get("entity_kinds", [])
    if any(k.get("id") == "event" for k in entity_kinds):
        print("[macwo530_phase1] event entity already present — no-op")
        return 0

    entity_kinds.append(EVENT_ENTITY)
    print(f"[macwo530_phase1] Added event entity_kind with {len(EVENT_ENTITY['attributes'])} attributes")

    with METAMODEL_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(model, f, allow_unicode=True, sort_keys=False, width=120, default_flow_style=False)
    print("[macwo530_phase1] Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
