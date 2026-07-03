from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from tools.wave1 import GlossaryAlias, load_ontology
from tools.wave1.lint import lint_ontology


ROOT = Path(__file__).resolve().parents[1]


def _load_baseline():
    return load_ontology(
        ROOT / "model/metamodel.yaml",
        relation_catalog_path=ROOT / "model/relation_catalog.yaml",
    )


def test_lint_happy_path_current_inputs() -> None:
    ontology = _load_baseline()

    result = lint_ontology(ontology)

    assert result.error_count == 0
    assert result.warning_count >= 0


def test_lint_duplicate_alias_collision_case() -> None:
    ontology = _load_baseline()
    aliases = (
        GlossaryAlias(id="a1", term="business_process", alias="ops", language="en", extra={}),
        GlossaryAlias(id="a2", term="business_operation", alias="ops", language="en", extra={}),
    )
    broken = replace(ontology, glossary_aliases=aliases)

    result = lint_ontology(broken)

    assert any(message.code == "alias_ambiguous_target" for message in result.warnings)


def test_lint_problematic_inverse_relation_label_case() -> None:
    ontology = _load_baseline()
    relation = ontology.relation_catalog.relations[0]
    payload = dict(relation.payload)
    payload["has_inverse"] = True
    payload["inverse_relation_id"] = ontology.relation_catalog.relations[1].id
    payload["ui_label_out"] = "mismatched outward label"
    broken_relation = replace(relation, payload=payload)
    broken_catalog = replace(
        ontology.relation_catalog,
        relations=(broken_relation, *ontology.relation_catalog.relations[1:]),
    )
    broken = replace(ontology, relation_catalog=broken_catalog)

    result = lint_ontology(broken)

    assert any(message.code == "inverse_label_mismatch" for message in result.warnings)


def test_lint_ambiguous_glossary_alias_collision_case() -> None:
    ontology = _load_baseline()
    aliases = (
        GlossaryAlias(id="a1", term="business_process", alias="business_process", language="en", extra={}),
        GlossaryAlias(id="a2", term="business_operation", alias="business_process", language="en", extra={}),
    )
    broken = replace(ontology, glossary_aliases=aliases)

    result = lint_ontology(broken)

    assert any(message.code == "alias_collides_with_canonical" for message in result.warnings)
    assert any(message.code == "alias_ambiguous_target" for message in result.warnings)


def test_lint_baseline_clean_of_relation_endpoint_and_label_warnings() -> None:
    """Regression: plural endpoint nouns (e.g. 'processes' for business_process)
    and mirrored inverse labels must not raise relation warnings on baseline."""
    ontology = _load_baseline()

    result = lint_ontology(ontology)

    codes = {message.code for message in result.warnings}
    assert "relation_id_endpoint_mismatch" not in codes
    assert "inverse_label_mismatch" not in codes


def test_singularize_handles_common_plurals() -> None:
    from tools.wave1.lint import _singularize

    assert _singularize("processes") == "process"
    assert _singularize("capabilities") == "capability"
    assert _singularize("products") == "product"
    assert _singularize("stages") == "stage"
    assert _singularize("business") is None  # trailing -ss is not a plural
    assert _singularize("data") is None  # no trailing -s
