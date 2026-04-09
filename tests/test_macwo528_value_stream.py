"""Regression tests for MACWO-528: PDF 1.0 value_stream attributes."""

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
def value_stream(metamodel):
    for kind in metamodel["entity_kinds"]:
        if kind["id"] == "value_stream":
            return kind
    pytest.fail("value_stream not found")


@pytest.fixture(scope="module")
def attrs_by_id(value_stream):
    return {a["id"]: a for a in value_stream.get("attributes", [])}


def test_has_at_least_29_attributes(value_stream):
    """2 legacy + 27 new = 29."""
    assert len(value_stream["attributes"]) >= 29


def test_legacy_preserved(attrs_by_id):
    assert "value_stream.goal" in attrs_by_id
    assert "value_stream.owner" in attrs_by_id


@pytest.mark.parametrize(
    "attr_id",
    [
        "value_stream.code",
        "value_stream.name",
        "value_stream.short_description",
        "value_stream.domain",
        "value_stream.is_deterministic",
        "value_stream.status_lifecycle",
        "value_stream.maturity_level",
        "value_stream.criticality",
        "value_stream.version",
        "value_stream.job_family_id",
        "value_stream.product_id",
        "value_stream.consumer_type",
        "value_stream.trigger",
        "value_stream.delivered_value",
        "value_stream.lead_time",
        "value_stream.process_time",
        "value_stream.delay_time",
        "value_stream.value_added_time",
        "value_stream.first_pass_yield",
        "value_stream.operating_cost",
        "value_stream.customer_satisfaction",
        "value_stream.fai",
        "value_stream.stp",
        "value_stream.risks",
        "value_stream.org_unit_id",
        "value_stream.created_at",
        "value_stream.updated_at",
    ],
)
def test_pr3_attribute_present(attrs_by_id, attr_id):
    assert attr_id in attrs_by_id


def test_vsm_four_times_have_days_unit(attrs_by_id):
    for name in ("lead_time", "process_time", "delay_time", "value_added_time"):
        assert attrs_by_id[f"value_stream.{name}"]["unit"] == "days"


def test_consumer_type_enum(attrs_by_id):
    consumer_type = attrs_by_id["value_stream.consumer_type"]
    assert consumer_type["data_type"] == "enum"
    assert set(consumer_type["enum_values"]) == {
        "end_customer", "external_counterparty", "internal_stakeholder"
    }


def test_criticality_enum(attrs_by_id):
    crit = attrs_by_id["value_stream.criticality"]
    assert set(crit["enum_values"]) == {
        "mission_critical", "business_critical", "business_support", "office_productivity"
    }


def test_display_groups_cover_expected(attrs_by_id):
    pr3_groups = {
        a["display_group"] for a in attrs_by_id.values()
        if a.get("introduced_in") == "2.1"
    }
    expected = {"core", "consumer", "value", "vsm", "metrics", "risks", "ownership", "lifecycle"}
    assert expected.issubset(pr3_groups)


@pytest.fixture(scope="module")
def relation_kind_ids(metamodel):
    return {r["id"] for r in metamodel.get("relation_kinds", [])}


@pytest.fixture(scope="module")
def catalog_ids(relation_catalog):
    return {r["id"] for r in relation_catalog.get("relation_catalog", {}).get("relations", [])}


@pytest.mark.parametrize(
    "rel_id",
    [
        "rel_value_stream_targets_job_family",
        "rel_value_stream_governed_by_org_unit",
    ],
)
def test_pr3_relation_in_metamodel(relation_kind_ids, rel_id):
    assert rel_id in relation_kind_ids


@pytest.mark.parametrize(
    "rel_id",
    [
        "rel_value_stream_targets_job_family",
        "rel_value_stream_governed_by_org_unit",
    ],
)
def test_pr3_relation_in_catalog(catalog_ids, rel_id):
    assert rel_id in catalog_ids
