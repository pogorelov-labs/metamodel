"""Regression tests for MACWO-530: new event entity_kind."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
METAMODEL_PATH = ROOT / "model" / "metamodel.yaml"
RELATION_CATALOG_PATH = ROOT / "model" / "relation_catalog.yaml"


@pytest.fixture(scope="module")
def metamodel():
    with METAMODEL_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def relation_catalog():
    with RELATION_CATALOG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def event_entity(metamodel):
    for k in metamodel["entity_kinds"]:
        if k["id"] == "event":
            return k
    pytest.fail("event entity_kind not found")


def test_event_entity_exists(event_entity):
    assert event_entity["id"] == "event"
    assert event_entity["name_ru"] == "Событие"
    assert event_entity["category"] == "operational"
    assert event_entity["status"] == "active"


def test_event_has_5_attributes(event_entity):
    assert len(event_entity["attributes"]) == 5


@pytest.mark.parametrize(
    "attr_id",
    [
        "event.event_type",
        "event.occurred_at",
        "event.source",
        "event.payload",
        "event.severity",
    ],
)
def test_event_attribute_present(event_entity, attr_id):
    ids = {a["id"] for a in event_entity["attributes"]}
    assert attr_id in ids


def test_event_type_enum(event_entity):
    et = next(a for a in event_entity["attributes"] if a["id"] == "event.event_type")
    assert et["data_type"] == "enum"
    assert set(et["enum_values"]) == {"business", "system", "data", "security"}
    assert et["required"] is True


def test_event_severity_enum(event_entity):
    sev = next(a for a in event_entity["attributes"] if a["id"] == "event.severity")
    assert set(sev["enum_values"]) == {"info", "warning", "error", "critical"}


def test_event_required_fields(event_entity):
    req = {a["id"] for a in event_entity["attributes"] if a.get("required")}
    assert req == {"event.event_type", "event.occurred_at", "event.source"}


@pytest.fixture(scope="module")
def relation_kind_ids(metamodel):
    return {r["id"] for r in metamodel.get("relation_kinds", [])}


@pytest.fixture(scope="module")
def catalog_ids(relation_catalog):
    return {r["id"] for r in relation_catalog.get("relation_catalog", {}).get("relations", [])}


@pytest.mark.parametrize(
    "rel_id",
    [
        "rel_event_emitted_by_business_process",
        "rel_event_emitted_by_it_system",
        "rel_event_emitted_by_data_product",
        "rel_incident_triggered_by_event",
    ],
)
def test_pr5_relation_in_metamodel(relation_kind_ids, rel_id):
    assert rel_id in relation_kind_ids


@pytest.mark.parametrize(
    "rel_id",
    [
        "rel_event_emitted_by_business_process",
        "rel_event_emitted_by_it_system",
        "rel_event_emitted_by_data_product",
        "rel_incident_triggered_by_event",
    ],
)
def test_pr5_relation_in_catalog(catalog_ids, rel_id):
    assert rel_id in catalog_ids
