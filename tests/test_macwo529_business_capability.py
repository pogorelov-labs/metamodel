"""Regression tests for MACWO-529: PDF 1.0 business_capability attributes."""

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
def business_capability(metamodel):
    for k in metamodel["entity_kinds"]:
        if k["id"] == "business_capability":
            return k
    pytest.fail("business_capability not found")


@pytest.fixture(scope="module")
def attrs_by_id(business_capability):
    return {a["id"]: a for a in business_capability.get("attributes", [])}


def test_has_at_least_19_attributes(business_capability):
    """1 legacy + 18 new = 19."""
    assert len(business_capability["attributes"]) >= 19


def test_legacy_preserved(attrs_by_id):
    assert "business_capability.maturity_level" in attrs_by_id


@pytest.mark.parametrize(
    "attr_id",
    [
        "business_capability.code",
        "business_capability.code_rbi",
        "business_capability.name",
        "business_capability.name_rbi",
        "business_capability.cbr_techprocess_code",
        "business_capability.short_description",
        "business_capability.hierarchy_level",
        "business_capability.specialization",
        "business_capability.domain",
        "business_capability.status_lifecycle",
        "business_capability.opex_cost",
        "business_capability.kpi_target",
        "business_capability.regulatory_compliance",
        "business_capability.used_it_system_ids",
        "business_capability.owner_employee_id",
        "business_capability.org_unit_id",
        "business_capability.created_at",
        "business_capability.updated_at",
    ],
)
def test_pr4_attribute_present(attrs_by_id, attr_id):
    assert attr_id in attrs_by_id


def test_hierarchy_level_enum(attrs_by_id):
    h = attrs_by_id["business_capability.hierarchy_level"]
    assert h["data_type"] == "enum"
    assert set(h["enum_values"]) == {"l1", "l2", "l3"}


def test_specialization_enum(attrs_by_id):
    s = attrs_by_id["business_capability.specialization"]
    assert set(s["enum_values"]) == {
        "strategic_capability", "operational_capability", "other"
    }


def test_rbi_fields_have_adoit_source(attrs_by_id):
    for fid in ("business_capability.code_rbi", "business_capability.name_rbi"):
        assert "ADOIT" in attrs_by_id[fid]["source_expectation"]


@pytest.fixture(scope="module")
def relation_kind_ids(metamodel):
    return {r["id"] for r in metamodel.get("relation_kinds", [])}


@pytest.fixture(scope="module")
def catalog_ids(relation_catalog):
    return {r["id"] for r in relation_catalog.get("relation_catalog", {}).get("relations", [])}


@pytest.mark.parametrize(
    "rel_id",
    [
        "rel_business_capability_owned_by_employee",
        "rel_business_capability_governed_by_org_unit",
    ],
)
def test_pr4_relation_in_metamodel(relation_kind_ids, rel_id):
    assert rel_id in relation_kind_ids


@pytest.mark.parametrize(
    "rel_id",
    [
        "rel_business_capability_owned_by_employee",
        "rel_business_capability_governed_by_org_unit",
    ],
)
def test_pr4_relation_in_catalog(catalog_ids, rel_id):
    assert rel_id in catalog_ids
