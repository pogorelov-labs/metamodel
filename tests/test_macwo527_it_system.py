"""Regression tests for MACWO-527: PDF 1.0 it_system attributes."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
METAMODEL_PATH = ROOT / "model" / "metamodel.yaml"
RELATION_CATALOG_PATH = ROOT / "model" / "relation_catalog.yaml"


@pytest.fixture(scope="module")
def metamodel() -> dict:
    with METAMODEL_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def relation_catalog() -> dict:
    with RELATION_CATALOG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def it_system(metamodel: dict) -> dict:
    for kind in metamodel["entity_kinds"]:
        if kind["id"] == "it_system":
            return kind
    pytest.fail("it_system entity_kind not found")


@pytest.fixture(scope="module")
def attrs_by_id(it_system: dict) -> dict[str, dict]:
    return {attr["id"]: attr for attr in it_system.get("attributes", [])}


def test_has_at_least_45_attributes(it_system: dict) -> None:
    """PR-2 adds 41 new attributes on top of 4 legacy ones."""
    assert len(it_system["attributes"]) >= 45


def test_legacy_preserved(attrs_by_id: dict) -> None:
    legacy = {
        "it_system.org_unit_id",
        "it_system.business_capability_id",
        "it_system.business_domain_id",
        "it_system.tier",
    }
    assert legacy.issubset(attrs_by_id.keys())


@pytest.mark.parametrize(
    "attr_id",
    [
        # identity
        "it_system.name_short",
        "it_system.full_name",
        "it_system.full_name_eng",
        "it_system.alt_name",
        "it_system.description_text",
        "it_system.description_eng",
        # criticality
        "it_system.critical_infrastructure_level",
        "it_system.availability_tier",
        "it_system.mb_criticality",
        "it_system.application_type",
        "it_system.application_operational_time",
        "it_system.target_state",
        # ownership
        "it_system.owner_team_id",
        "it_system.business_owner_employee_id",
        "it_system.business_owner_delegate_id",
        "it_system.it_owner_employee_id",
        "it_system.enterprise_architect_id",
        "it_system.legal_entity_org_unit_id",
        # bcp
        "it_system.rto_bcp",
        "it_system.rpo_bcp",
        "it_system.availability_percent",
        "it_system.availability_class",
        "it_system.integrity_class",
        # data_classification
        "it_system.data_classification_level",
        "it_system.personal_data",
        "it_system.bank_secret",
        "it_system.commercial_secret",
        "it_system.insider_information",
        "it_system.other_confidential_information",
        # pci
        "it_system.audit_pci_dss",
        "it_system.applicability_pci_dss",
        "it_system.system_interacts_with_pci_dss",
        "it_system.card_personalization",
        "it_system.payment_card_information",
        "it_system.pci_raiffeisen",
        "it_system.pci_other_bank",
        # exposure
        "it_system.internet_facing",
        "it_system.infosec_solution",
        # support
        "it_system.support_group",
        "it_system.support_expert_1_id",
        "it_system.support_expert_2_id",
    ],
)
def test_pr2_attribute_present(attrs_by_id: dict, attr_id: str) -> None:
    assert attr_id in attrs_by_id


def test_pci_and_confidential_flagged(attrs_by_id: dict) -> None:
    """Security-sensitive fields must carry sensitivity: confidential."""
    sensitive_groups = {"pci", "data_classification"}
    for attr in attrs_by_id.values():
        if attr.get("introduced_in") != "2.1":
            continue
        if attr.get("display_group") in sensitive_groups:
            assert attr.get("sensitivity") == "confidential", (
                f"{attr['id']} in sensitive group lacks sensitivity: confidential"
            )


def test_enum_attributes_have_values(attrs_by_id: dict) -> None:
    enums = [
        a for a in attrs_by_id.values()
        if a.get("data_type") == "enum" and a.get("introduced_in") == "2.1"
    ]
    assert len(enums) >= 7
    for attr in enums:
        assert attr.get("enum_values"), f"{attr['id']} missing enum_values"


def test_ref_attributes_have_ref_kind(attrs_by_id: dict) -> None:
    refs = [
        a for a in attrs_by_id.values()
        if a.get("ref_kind") and a.get("introduced_in") == "2.1"
    ]
    assert len(refs) >= 8
    for attr in refs:
        assert attr.get("data_type") == "id"


def test_rto_rpo_have_units(attrs_by_id: dict) -> None:
    assert attrs_by_id["it_system.rto_bcp"]["unit"] == "minutes"
    assert attrs_by_id["it_system.rpo_bcp"]["unit"] == "hours"
    assert attrs_by_id["it_system.availability_percent"]["unit"] == "percent"


def test_display_groups_cover_expected(attrs_by_id: dict) -> None:
    pr2_groups = {
        a["display_group"] for a in attrs_by_id.values()
        if a.get("introduced_in") == "2.1"
    }
    expected = {
        "identity", "criticality", "ownership", "bcp",
        "data_classification", "pci", "exposure", "support",
    }
    assert expected.issubset(pr2_groups)


@pytest.fixture(scope="module")
def relation_kind_ids(metamodel: dict) -> set[str]:
    return {r["id"] for r in metamodel.get("relation_kinds", [])}


@pytest.fixture(scope="module")
def catalog_relation_ids(relation_catalog: dict) -> set[str]:
    return {r["id"] for r in relation_catalog.get("relation_catalog", {}).get("relations", [])}


@pytest.mark.parametrize(
    "rel_id",
    [
        "rel_it_system_owned_by_team",
        "rel_it_system_business_owned_by_employee",
        "rel_it_system_business_owner_delegate_employee",
        "rel_it_system_it_owned_by_employee",
        "rel_it_system_architected_by_employee",
        "rel_it_system_legal_entity_org_unit",
    ],
)
def test_pr2_relation_in_metamodel(relation_kind_ids: set[str], rel_id: str) -> None:
    assert rel_id in relation_kind_ids


@pytest.mark.parametrize(
    "rel_id",
    [
        "rel_it_system_owned_by_team",
        "rel_it_system_business_owned_by_employee",
        "rel_it_system_business_owner_delegate_employee",
        "rel_it_system_it_owned_by_employee",
        "rel_it_system_architected_by_employee",
        "rel_it_system_legal_entity_org_unit",
    ],
)
def test_pr2_relation_in_catalog(catalog_relation_ids: set[str], rel_id: str) -> None:
    assert rel_id in catalog_relation_ids
