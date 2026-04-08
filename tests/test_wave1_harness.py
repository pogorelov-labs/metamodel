from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from tools.wave1 import load_ontology
from tools.wave1.harness import (
    format_harness_report,
    run_wave1_validation_harness,
    run_wave1_validation_harness_on_model,
)
from tools.wave1.model import GlossaryAlias


ROOT = Path(__file__).resolve().parents[1]


def _baseline_ontology():
    return load_ontology(
        ROOT / "model/metamodel.yaml",
        relation_catalog_path=ROOT / "model/relation_catalog.yaml",
    )


def _replace_relation_payload(ontology, relation_id: str, patch: dict):
    relations = []
    for relation in ontology.relation_catalog.relations:
        if relation.id == relation_id:
            payload = dict(relation.payload)
            payload.update(patch)
            relations.append(
                replace(
                    relation,
                    payload=payload,
                    from_kind=payload.get("from_kind"),
                    to_kind=payload.get("to_kind"),
                )
            )
        else:
            relations.append(relation)
    return replace(ontology, relation_catalog=replace(ontology.relation_catalog, relations=tuple(relations)))


def test_harness_baseline_success_from_paths() -> None:
    result = run_wave1_validation_harness(
        ROOT / "model/metamodel.yaml",
        relation_catalog_path=ROOT / "model/relation_catalog.yaml",
    )

    assert result.success
    assert [stage.name for stage in result.stages] == [
        "ontology_validation",
        "ontology_lint",
        "relation_catalog_validation",
        "schema_validation",
        "contract_validation",
    ]


def test_harness_surfaces_ontology_validation_failure() -> None:
    ontology = _baseline_ontology()
    broken = replace(ontology, entity_kinds=(*ontology.entity_kinds, ontology.entity_kinds[0]))

    result = run_wave1_validation_harness_on_model(broken)

    stage = next(item for item in result.stages if item.name == "ontology_validation")
    assert not result.success
    assert any("[duplicate_id] entity_kinds" in message for message in stage.errors)


def test_harness_surfaces_lint_issue() -> None:
    ontology = _baseline_ontology()
    broken = replace(
        ontology,
        glossary_aliases=(
            GlossaryAlias(id="a1", term="business_process", alias="ops", language="en", extra={}),
            GlossaryAlias(id="a2", term="business_operation", alias="ops", language="en", extra={}),
        ),
    )

    result = run_wave1_validation_harness_on_model(broken)

    stage = next(item for item in result.stages if item.name == "ontology_lint")
    assert any("alias_ambiguous_target" in message for message in stage.warnings)


def test_harness_surfaces_relation_catalog_validation_failure() -> None:
    ontology = _baseline_ontology()
    relation = ontology.relation_catalog.relations[0]
    broken = _replace_relation_payload(ontology, relation.id, {"default_visibility": "always"})

    result = run_wave1_validation_harness_on_model(broken)

    stage = next(item for item in result.stages if item.name == "relation_catalog_validation")
    assert not result.success
    assert any("default_visibility" in message and "invalid_enum" in message for message in stage.errors)


def test_harness_report_is_deterministic() -> None:
    ontology = _baseline_ontology()
    relation = ontology.relation_catalog.relations[0]
    broken = _replace_relation_payload(
        ontology,
        relation.id,
        {
            "path_priority": "invalid",
            "default_visibility": "invalid",
        },
    )

    report = format_harness_report(run_wave1_validation_harness_on_model(broken))

    first_index = report.index("default_visibility")
    second_index = report.index("path_priority")
    assert first_index < second_index
