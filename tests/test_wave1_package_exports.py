from __future__ import annotations

from pathlib import Path

from tools.wave1 import (
    format_harness_report,
    load_ontology,
    run_wave1_validation_harness,
    run_wave1_validation_harness_on_model,
)


ROOT = Path(__file__).resolve().parents[1]


def test_wave1_package_exports_include_harness_entrypoints() -> None:
    ontology_path = ROOT / "model/metamodel.yaml"
    relation_catalog_path = ROOT / "model/relation_catalog.yaml"

    # Compare path-based vs model-based runs without the path-only stages
    # (schema and contract validation both re-read the source files and
    # cannot be reproduced from an already-normalized ontology).
    by_path = run_wave1_validation_harness(
        ontology_path,
        relation_catalog_path=relation_catalog_path,
        schema_path=None,
        run_contract_validation=False,
    )

    ontology = load_ontology(ontology_path, relation_catalog_path=relation_catalog_path)
    by_model = run_wave1_validation_harness_on_model(ontology)

    assert by_path == by_model
    report = format_harness_report(by_path)
    assert report.startswith("success=true")
    assert "[ontology_validation]" in report


def test_wave1_harness_includes_schema_validation_stage_by_default() -> None:
    ontology_path = ROOT / "model/metamodel.yaml"
    relation_catalog_path = ROOT / "model/relation_catalog.yaml"

    result = run_wave1_validation_harness(
        ontology_path,
        relation_catalog_path=relation_catalog_path,
    )

    stage_names = [stage.name for stage in result.stages]
    assert "schema_validation" in stage_names
    schema_stage = next(s for s in result.stages if s.name == "schema_validation")
    assert schema_stage.error_count == 0


def test_wave1_harness_includes_contract_validation_stage_by_default() -> None:
    ontology_path = ROOT / "model/metamodel.yaml"
    relation_catalog_path = ROOT / "model/relation_catalog.yaml"

    result = run_wave1_validation_harness(
        ontology_path,
        relation_catalog_path=relation_catalog_path,
    )

    stage_names = [stage.name for stage in result.stages]
    assert "contract_validation" in stage_names
    contract_stage = next(s for s in result.stages if s.name == "contract_validation")
    assert contract_stage.error_count == 0
