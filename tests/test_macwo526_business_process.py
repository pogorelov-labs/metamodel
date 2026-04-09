"""Regression tests for MACWO-526: PDF 1.0 business_process attributes.

These tests pin the expected attribute and relation_kind surface added in
PR-1 so a future refactor cannot silently drop fields that downstream
ingest (S1/Archer/BCM/AppSec) depends on.
"""

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
def business_process(metamodel: dict) -> dict:
    for kind in metamodel["entity_kinds"]:
        if kind["id"] == "business_process":
            return kind
    pytest.fail("business_process entity_kind not found in metamodel.yaml")


@pytest.fixture(scope="module")
def bp_attribute_ids(business_process: dict) -> set[str]:
    return {attr["id"] for attr in business_process.get("attributes", [])}


@pytest.fixture(scope="module")
def bp_attributes_by_id(business_process: dict) -> dict[str, dict]:
    return {attr["id"]: attr for attr in business_process.get("attributes", [])}


# ---------------------------------------------------------------------------
# Attribute surface: count and coverage by display_group
# ---------------------------------------------------------------------------


def test_business_process_has_at_least_58_attributes(business_process: dict) -> None:
    """PR-1 adds 54 new attributes on top of 4 legacy ones."""
    assert len(business_process["attributes"]) >= 58


def test_legacy_attributes_preserved(bp_attribute_ids: set[str]) -> None:
    """Legacy attributes from the pre-PR-1 baseline must remain."""
    legacy = {
        "business_process.business_capability_id",
        "business_process.business_domain_id",
        "business_process.business_owner_id",
        "business_process.tier",
    }
    assert legacy.issubset(bp_attribute_ids)


@pytest.mark.parametrize(
    "attr_id",
    [
        # core
        "business_process.code",
        "business_process.name",
        "business_process.name_eng",
        "business_process.short_description",
        "business_process.board_area",
        "business_process.status_lifecycle",
        "business_process.trigger",
        "business_process.result",
        "business_process.comments",
        "business_process.version",
        "business_process.created_at",
        "business_process.updated_at",
        "business_process.cbr_techprocess_code",
        # regulatory
        "business_process.code_716p",
        "business_process.risk_classifier_l4",
        "business_process.criticality_716p",
        "business_process.internal_regulation",
        "business_process.npa",
        # ics
        "business_process.ics_prioritization",
        "business_process.ics_classification",
        "business_process.ib_risks",
        "business_process.op_risks",
        "business_process.ics_controls",
        "business_process.archer_id",
        "business_process.archer_name",
        "business_process.orm_owner_id",
        "business_process.dors_owner_ids",
        # bcm
        "business_process.bcm_criticality",
        "business_process.confidentiality_ref",
        "business_process.integrity_ref",
        "business_process.availability_ref",
        "business_process.rto_bp",
        "business_process.rpo_bp",
        "business_process.mtpd_bp",
        "business_process.mbco_bp",
        "business_process.customer_segment_impact",
        "business_process.has_external_counterparty",
        "business_process.counterparty_names",
        # ops
        "business_process.avg_execution_time",
        "business_process.execution_time_variance",
        "business_process.first_pass_yield",
        "business_process.operating_cost",
        "business_process.fai",
        "business_process.stp",
        # dependencies
        "business_process.inbound_process_codes",
        "business_process.outbound_process_codes",
        # ownership
        "business_process.owner_department",
        "business_process.owner_team_id",
        "business_process.participant_employee_ids",
        "business_process.participant_org_unit_ids",
        "business_process.participant_collective_bodies",
        "business_process.control_owner_employee_id",
        "business_process.control_owner_department",
        # landscape
        "business_process.related_it_system_ids",
    ],
)
def test_pdf_pr1_attribute_present(bp_attribute_ids: set[str], attr_id: str) -> None:
    assert attr_id in bp_attribute_ids, f"missing PR-1 attribute: {attr_id}"


# ---------------------------------------------------------------------------
# v2 contract compliance
# ---------------------------------------------------------------------------


def test_pr1_attributes_have_v2_fields(bp_attributes_by_id: dict[str, dict]) -> None:
    """Each PR-1 attribute must carry v2 contract fields."""
    pr1_attrs = [
        attr
        for attr_id, attr in bp_attributes_by_id.items()
        if attr.get("introduced_in") == "2.1"
    ]
    assert pr1_attrs, "no PR-1 attributes found (introduced_in 2.1)"
    for attr in pr1_attrs:
        assert "data_type" in attr, f"{attr['id']} missing data_type"
        assert "cardinality" in attr, f"{attr['id']} missing cardinality"
        assert "category" in attr, f"{attr['id']} missing category"
        assert "display_group" in attr, f"{attr['id']} missing display_group"
        assert "status" in attr, f"{attr['id']} missing status"
        assert attr["status"] == "active"


def test_enum_attributes_have_enum_values(bp_attributes_by_id: dict[str, dict]) -> None:
    """Every data_type=enum attribute must declare enum_values."""
    enums = [
        attr
        for attr in bp_attributes_by_id.values()
        if attr.get("data_type") == "enum" and attr.get("introduced_in") == "2.1"
    ]
    assert len(enums) >= 5
    for attr in enums:
        values = attr.get("enum_values")
        assert values, f"{attr['id']} missing enum_values"
        assert all(isinstance(v, str) for v in values), (
            f"{attr['id']} enum_values must be strings"
        )


def test_ref_attributes_have_ref_kind(bp_attributes_by_id: dict[str, dict]) -> None:
    """Reference attributes use data_type=id and declare ref_kind."""
    refs = [
        attr
        for attr in bp_attributes_by_id.values()
        if attr.get("ref_kind") and attr.get("introduced_in") == "2.1"
    ]
    assert len(refs) >= 7
    for attr in refs:
        assert attr.get("data_type") == "id", (
            f"{attr['id']} has ref_kind but data_type is not 'id'"
        )


def test_bcm_rto_rpo_have_units(bp_attributes_by_id: dict[str, dict]) -> None:
    rto = bp_attributes_by_id["business_process.rto_bp"]
    rpo = bp_attributes_by_id["business_process.rpo_bp"]
    mtpd = bp_attributes_by_id["business_process.mtpd_bp"]
    mbco = bp_attributes_by_id["business_process.mbco_bp"]
    assert rto["unit"] == "minutes"
    assert rpo["unit"] == "hours"
    assert mtpd["unit"] == "hours"
    assert mbco["unit"] == "percent"


def test_display_groups_cover_expected_set(
    bp_attributes_by_id: dict[str, dict],
) -> None:
    pr1_groups = {
        attr["display_group"]
        for attr in bp_attributes_by_id.values()
        if attr.get("introduced_in") == "2.1"
    }
    expected = {
        "core",
        "regulatory",
        "ics",
        "bcm",
        "ops",
        "dependencies",
        "ownership",
        "landscape",
    }
    assert expected.issubset(pr1_groups)


# ---------------------------------------------------------------------------
# Relation kinds
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def relation_kind_ids(metamodel: dict) -> set[str]:
    return {r["id"] for r in metamodel.get("relation_kinds", [])}


@pytest.fixture(scope="module")
def catalog_relation_ids(relation_catalog: dict) -> set[str]:
    return {
        r["id"]
        for r in relation_catalog.get("relation_catalog", {}).get("relations", [])
    }


@pytest.mark.parametrize(
    "rel_id",
    [
        "rel_business_process_owned_by_employee",
        "rel_business_process_owned_by_team",
        "rel_business_process_has_participant_employee",
        "rel_business_process_has_participant_org_unit",
        "rel_business_process_affects_customer_segment",
        "rel_business_process_control_owned_by_employee",
        "rel_business_process_risk_owned_by_employee",
        "rel_business_process_uses_it_system",
    ],
)
def test_pr1_relation_in_metamodel(
    relation_kind_ids: set[str], rel_id: str
) -> None:
    assert rel_id in relation_kind_ids, f"missing PR-1 relation_kind: {rel_id}"


@pytest.mark.parametrize(
    "rel_id",
    [
        "rel_business_process_owned_by_employee",
        "rel_business_process_owned_by_team",
        "rel_business_process_has_participant_employee",
        "rel_business_process_has_participant_org_unit",
        "rel_business_process_affects_customer_segment",
        "rel_business_process_control_owned_by_employee",
        "rel_business_process_risk_owned_by_employee",
        "rel_business_process_uses_it_system",
    ],
)
def test_pr1_relation_in_catalog(
    catalog_relation_ids: set[str], rel_id: str
) -> None:
    """mm/rc Rule 1: every catalog relation must have mm relation_kind.
    Here we assert the PR-1 relations are also present in the catalog."""
    assert rel_id in catalog_relation_ids, (
        f"missing PR-1 catalog overlay: {rel_id}"
    )


def test_existing_dependency_relation_reused(
    relation_kind_ids: set[str],
) -> None:
    """PDF #20/21 inbound/outbound dependencies reuse rel_process_depends_on_process."""
    assert "rel_process_depends_on_process" in relation_kind_ids
