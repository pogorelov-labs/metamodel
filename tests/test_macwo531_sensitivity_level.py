"""Regression tests for MACWO-531: new sensitivity_level entity_kind."""

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
def sensitivity_level(metamodel):
    for k in metamodel["entity_kinds"]:
        if k["id"] == "sensitivity_level":
            return k
    pytest.fail("sensitivity_level not found")


def test_entity_exists(sensitivity_level):
    assert sensitivity_level["id"] == "sensitivity_level"
    assert sensitivity_level["name_ru"] == "Категория чувствительной информации"
    assert sensitivity_level["category"] == "governance"
    assert sensitivity_level["status"] == "active"


def test_has_6_attributes(sensitivity_level):
    assert len(sensitivity_level["attributes"]) == 6


@pytest.mark.parametrize(
    "attr_id",
    [
        "sensitivity_level.level_code",
        "sensitivity_level.name_ru",
        "sensitivity_level.handling_rules",
        "sensitivity_level.required_encryption",
        "sensitivity_level.retention_policy",
        "sensitivity_level.regulatory_basis",
    ],
)
def test_attribute_present(sensitivity_level, attr_id):
    ids = {a["id"] for a in sensitivity_level["attributes"]}
    assert attr_id in ids


def test_level_code_enum(sensitivity_level):
    lc = next(a for a in sensitivity_level["attributes"] if a["id"] == "sensitivity_level.level_code")
    assert lc["data_type"] == "enum"
    assert set(lc["enum_values"]) == {
        "public", "internal", "restricted", "confidential", "secret"
    }
    assert lc["required"] is True


def test_required_fields(sensitivity_level):
    req = {a["id"] for a in sensitivity_level["attributes"] if a.get("required")}
    assert "sensitivity_level.level_code" in req
    assert "sensitivity_level.handling_rules" in req
    assert "sensitivity_level.required_encryption" in req


@pytest.fixture(scope="module")
def relation_kind_ids(metamodel):
    return {r["id"] for r in metamodel.get("relation_kinds", [])}


@pytest.fixture(scope="module")
def catalog_ids(relation_catalog):
    return {r["id"] for r in relation_catalog.get("relation_catalog", {}).get("relations", [])}


@pytest.mark.parametrize(
    "rel_id",
    [
        "rel_sensitivity_level_governs_business_attribute",
        "rel_sensitivity_level_governs_data_product",
        "rel_sensitivity_level_governs_data_object",
    ],
)
def test_pr6_relation_in_metamodel(relation_kind_ids, rel_id):
    assert rel_id in relation_kind_ids


@pytest.mark.parametrize(
    "rel_id",
    [
        "rel_sensitivity_level_governs_business_attribute",
        "rel_sensitivity_level_governs_data_product",
        "rel_sensitivity_level_governs_data_object",
    ],
)
def test_pr6_relation_in_catalog(catalog_ids, rel_id):
    assert rel_id in catalog_ids
