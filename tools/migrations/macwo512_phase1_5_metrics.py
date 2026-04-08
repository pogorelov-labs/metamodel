"""MACWO-515 (Phase 1.5, G5.1): Metrics consolidation.

Collapses three near-overlapping entity_kinds (``metric``, ``business_metric``,
``tech_metric``) into a single canonical ``metric``. Detailed acceptance
criteria are in MACWO-515.

Operations:
1. Delete entity_kind ``business_metric`` (orphan, 0 relations, draft).
2. Delete the old ``metric`` entity (no metamodel_level, no attributes).
3. Rename ``tech_metric`` → ``metric``. The merged entity inherits:
   - id, name, name_ru from the old ``metric`` (canonical labels)
   - category, metamodel_level, attributes from ``tech_metric`` (filled in)
   - merged description, aliases, examples
4. Rename ``tech_metric.*`` attributes to ``metric.*`` and add a canonical
   ``metric.type`` enum (business | technical | sla | quality | performance).
5. Rewire any relation_kind / catalog relation that references ``tech_metric``
   so it points at the new ``metric`` (id is preserved, only ``from_kind`` /
   ``to_kind`` change).

Idempotent — re-running on a migrated repo is a no-op.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METAMODEL_PATH = REPO_ROOT / "model" / "metamodel.yaml"
RELATION_CATALOG_PATH = REPO_ROOT / "model" / "relation_catalog.yaml"

ENTITIES_TO_REMOVE = {"metric", "business_metric", "tech_metric"}
TECH_METRIC = "tech_metric"
MERGED_ID = "metric"

MERGED_METRIC_ENTITY = {
    "id": "metric",
    "name": "Metric",
    "name_ru": "Метрика",
    "metamodel_level": "data_details",
    "category": "metric",
    "description": (
        "Измеримый показатель состояния бизнес-процессов, дата-объектов, "
        "процессов или технических систем. Используется как объективная основа "
        "мониторинга, контроля и управления, а также для привязки к требованиям и SLA."
    ),
    "scope_notes": (
        "Метрика однозначно определена: имя, прямая связь с объектом измерения, "
        "период измерения, значение, единица измерения, источник данных. "
        "Тип метрики (`metric.type`) определяет, относится ли она к бизнесу, "
        "технике, качеству, производительности или SLA. Может быть привязана "
        "к требованиям и SLA."
    ),
    "aliases": [
        {"value": "показатель", "lang": "ru", "alias_type": "synonym", "status": "active"},
        {"value": "KPI", "lang": "neutral", "alias_type": "synonym", "status": "active"},
        {"value": "индикатор", "lang": "ru", "alias_type": "synonym", "status": "active"},
    ],
    "examples": [
        "Дата поставки",
        "Продолжительность работы ETL-дага",
        "Статус DQ проверки",
        "Конверсия в воронке продаж",
        "Latency p99 API-вызова",
    ],
    "usage_purpose": (
        "Объективно оценивать состояние и эффективность бизнес-процессов, данных "
        "и технических систем."
    ),
    "status": "active",
    "introduced_in": "1.0",
    "attributes": [
        {
            "id": "metric.type",
            "name": "Тип метрики",
            "metamodel_level": "data_details",
            "description": (
                "Тип метрики: business | technical | quality | performance | sla."
            ),
        },
        {
            "id": "metric.calculation_logic",
            "name": "Формула расчёта",
            "metamodel_level": "data_details",
            "description": "Описание алгоритма или формулы вычисления значения метрики.",
        },
        {
            "id": "metric.measurement_unit",
            "name": "Единица измерения",
            "metamodel_level": "data_details",
            "description": "Единица измерения значения (%, секунды, штуки, рубли и т.д.).",
        },
        {
            "id": "metric.data_source",
            "name": "Источник данных",
            "metamodel_level": "data_details",
            "description": "Откуда берутся значения метрики (data_object, data_process, внешний источник).",
        },
    ],
}


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
    """Replace tech_metric endpoints with metric (in place)."""
    if rel.get("from_kind") == TECH_METRIC:
        rel["from_kind"] = MERGED_ID
    if rel.get("to_kind") == TECH_METRIC:
        rel["to_kind"] = MERGED_ID
    desc = rel.get("description")
    if isinstance(desc, str) and TECH_METRIC in desc:
        rel["description"] = desc.replace(TECH_METRIC, MERGED_ID)


def migrate_metamodel(mm: dict) -> dict:
    new_entities = []
    metric_inserted = False
    for entity in mm["entity_kinds"]:
        if entity["id"] in ENTITIES_TO_REMOVE:
            # Insert the merged metric exactly where the old `metric` lived
            # (so the canonical position is preserved in the file).
            if entity["id"] == MERGED_ID and not metric_inserted:
                new_entities.append(MERGED_METRIC_ENTITY)
                metric_inserted = True
            continue
        new_entities.append(entity)
    if not metric_inserted:
        new_entities.append(MERGED_METRIC_ENTITY)
    mm["entity_kinds"] = new_entities

    for rel in mm["relation_kinds"]:
        rewire_relation(rel)
    return mm


def migrate_relation_catalog(rc: dict) -> dict:
    for rel in rc["relation_catalog"]["relations"]:
        rewire_relation(rel)
    return rc


def main() -> int:
    mm = load_yaml(METAMODEL_PATH)
    rc = load_yaml(RELATION_CATALOG_PATH)
    mm = migrate_metamodel(mm)
    rc = migrate_relation_catalog(rc)
    dump_yaml(METAMODEL_PATH, mm)
    dump_yaml(RELATION_CATALOG_PATH, rc)
    print("MACWO-515 phase 1.5 migration applied:")
    print(f"  entity_kinds:        {len(mm['entity_kinds'])}")
    print(f"  mm.relation_kinds:   {len(mm['relation_kinds'])}")
    print(f"  rc.relations:        {len(rc['relation_catalog']['relations'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
