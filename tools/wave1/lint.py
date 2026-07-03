"""Wave 1 ontology semantic lint checks on top of the normalized model."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

from .model import GlossaryAlias, NormalizedOntology

_SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class LintMessage:
    severity: str
    code: str
    message: str
    path: str


@dataclass(frozen=True)
class LintResult:
    errors: Tuple[LintMessage, ...]
    warnings: Tuple[LintMessage, ...]

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)


def lint_ontology(ontology: NormalizedOntology) -> LintResult:
    """Run Wave 1 lint checks for semantic consistency and naming quality."""

    findings: List[LintMessage] = []

    _lint_naming_consistency(ontology, findings)
    _lint_alias_glossary_consistency(ontology, findings)
    _lint_relation_consistency(ontology, findings)
    _lint_profile_readiness(ontology, findings)

    ordered = sorted(findings, key=lambda item: (item.severity, item.path, item.code, item.message))
    errors = tuple(item for item in ordered if item.severity == "error")
    warnings = tuple(item for item in ordered if item.severity == "warning")
    return LintResult(errors=errors, warnings=warnings)


def _lint_naming_consistency(ontology: NormalizedOntology, findings: List[LintMessage]) -> None:
    for entity in ontology.entity_kinds:
        _lint_snake_case(entity.id, f"entity_kinds.{entity.id}.id", findings)

    for relation in ontology.relation_kinds:
        _lint_snake_case(relation.id, f"relation_kinds.{relation.id}.id", findings)
        if not relation.id.startswith("rel_"):
            findings.append(
                LintMessage(
                    severity="warning",
                    code="relation_id_prefix",
                    path=f"relation_kinds.{relation.id}.id",
                    message="relation id should start with 'rel_'",
                )
            )

    for attribute in ontology.attribute_definitions:
        _lint_snake_case(attribute.id.replace(".", "_"), f"attribute_definitions.{attribute.id}.id", findings)

    _lint_duplicate_names(
        section_name="entity_kinds",
        items=[(item.id, item.name) for item in ontology.entity_kinds],
        findings=findings,
    )
    _lint_duplicate_names(
        section_name="relation_kinds",
        items=[(item.id, item.name) for item in ontology.relation_kinds],
        findings=findings,
    )


def _lint_alias_glossary_consistency(ontology: NormalizedOntology, findings: List[LintMessage]) -> None:
    alias_targets: Dict[Tuple[str, str], set[str]] = {}
    for alias in ontology.glossary_aliases:
        key = ((alias.language or "").strip().lower(), (alias.alias or "").strip().lower())
        if not key[1]:
            continue
        alias_targets.setdefault(key, set()).add((alias.term or alias.id).strip().lower())

    for (language, alias_value), targets in sorted(alias_targets.items()):
        if len(targets) > 1:
            findings.append(
                LintMessage(
                    severity="warning",
                    code="alias_ambiguous_target",
                    path=f"glossary_aliases.{language}:{alias_value}",
                    message="same alias points to multiple canonical targets",
                )
            )

    canonical_names = {
        *(item.id.lower() for item in ontology.entity_kinds),
        *(item.id.lower() for item in ontology.relation_kinds),
        *(item.name or "" for item in ontology.entity_kinds),
        *(item.name or "" for item in ontology.relation_kinds),
    }
    canonical_names = {item.strip().lower() for item in canonical_names if item and item.strip()}

    for alias in ontology.glossary_aliases:
        alias_value = (alias.alias or "").strip().lower()
        if not alias_value:
            continue
        canonical_for_alias = (alias.term or alias.id).strip().lower()
        if alias_value in canonical_names and alias_value != canonical_for_alias:
            findings.append(
                LintMessage(
                    severity="warning",
                    code="alias_collides_with_canonical",
                    path=f"glossary_aliases.{alias.id}.alias",
                    message="alias collides with canonical id/name of a different concept",
                )
            )

    _lint_weak_bilingual_alias_coverage(ontology.glossary_aliases, findings)


def _singularize(token: str) -> str | None:
    """Naive English singular of a token, or None if it is not a plural.

    Lets relation ids use natural plural endpoint nouns (e.g. 'processes' for
    to_kind 'business_process', 'capabilities' for 'business_capability')
    without tripping the endpoint-token check.
    """
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    for suffix in ("ses", "xes", "zes", "ches", "shes"):
        if token.endswith(suffix) and len(token) > len(suffix):
            return token[:-2]
    if token.endswith("s") and not token.endswith("ss") and len(token) > 2:
        return token[:-1]
    return None


def _endpoint_tokens(name: str) -> set:
    """Tokens of a snake_case id/kind, expanded with naive singular variants."""
    tokens: set = set()
    for token in name.split("_"):
        tokens.add(token)
        singular = _singularize(token)
        if singular:
            tokens.add(singular)
    return tokens


def _lint_relation_consistency(ontology: NormalizedOntology, findings: List[LintMessage]) -> None:
    catalog = ontology.relation_catalog
    if catalog is None:
        return

    relations_by_id = {relation.id: relation for relation in catalog.relations}
    endpoint_families: Dict[Tuple[str, str], List[Mapping[str, object]]] = {}

    for relation in catalog.relations:
        payload = relation.payload
        from_kind = str(payload.get("from_kind") or "")
        to_kind = str(payload.get("to_kind") or "")
        endpoint_families.setdefault((from_kind, to_kind), []).append(payload)

        inverse_id = payload.get("inverse_relation_id")
        if isinstance(inverse_id, str) and inverse_id in relations_by_id:
            inverse_payload = relations_by_id[inverse_id].payload
            label_out = _as_clean_str(payload.get("ui_label_out"))
            inverse_label_in = _as_clean_str(inverse_payload.get("ui_label_in"))
            if label_out and inverse_label_in and label_out != inverse_label_in:
                findings.append(
                    LintMessage(
                        severity="warning",
                        code="inverse_label_mismatch",
                        path=f"relation_catalog.relations.{relation.id}",
                        message="ui_label_out should mirror inverse ui_label_in for explainability",
                    )
                )

        relation_tokens = _endpoint_tokens(relation.id)
        if from_kind and not _endpoint_tokens(from_kind) & relation_tokens:
            findings.append(
                LintMessage(
                    severity="warning",
                    code="relation_id_endpoint_mismatch",
                    path=f"relation_catalog.relations.{relation.id}.id",
                    message="relation id does not mention source endpoint tokens",
                )
            )
        if to_kind and not _endpoint_tokens(to_kind) & relation_tokens:
            findings.append(
                LintMessage(
                    severity="warning",
                    code="relation_id_endpoint_mismatch",
                    path=f"relation_catalog.relations.{relation.id}.id",
                    message="relation id does not mention target endpoint tokens",
                )
            )

    for (from_kind, to_kind), payloads in sorted(endpoint_families.items()):
        names = [str(payload.get("name") or "").strip().lower() for payload in payloads if payload.get("name")]
        if len(names) != len(set(names)) and names:
            findings.append(
                LintMessage(
                    severity="warning",
                    code="relation_family_duplicate_name",
                    path=f"relation_catalog.families.{from_kind}->{to_kind}",
                    message="multiple relations with same endpoints share the same display name",
                )
            )

        groups = {str(payload.get("ui_group") or "").strip().lower() for payload in payloads if payload.get("ui_group")}
        if len(groups) > 2:
            findings.append(
                LintMessage(
                    severity="warning",
                    code="relation_ui_group_scatter",
                    path=f"relation_catalog.families.{from_kind}->{to_kind}",
                    message="same endpoint family is spread across many ui_group values",
                )
            )


def _lint_profile_readiness(ontology: NormalizedOntology, findings: List[LintMessage]) -> None:
    catalog = ontology.relation_catalog
    if catalog is None:
        return

    declared_profiles = set(ontology.profiles) | set(catalog.profiles)
    used_profiles = set()

    for relation in catalog.relations:
        applies = relation.payload.get("applies_to_profiles")
        if isinstance(applies, list):
            used_profiles.update(item for item in applies if isinstance(item, str))

    for profile in sorted(declared_profiles - used_profiles):
        findings.append(
            LintMessage(
                severity="warning",
                code="unused_profile",
                path=f"profiles.{profile}",
                message="profile is declared but not referenced by relation catalog entries",
            )
        )


def _lint_weak_bilingual_alias_coverage(
    aliases: Sequence[GlossaryAlias],
    findings: List[LintMessage],
) -> None:
    coverage: Dict[str, set[str]] = {}
    for alias in aliases:
        canonical = (alias.term or alias.id).strip().lower()
        if not canonical:
            continue
        language = (alias.language or "").strip().lower()
        if not language:
            continue
        coverage.setdefault(canonical, set()).add(language)

    for canonical, languages in sorted(coverage.items()):
        if "en" in languages and "ru" not in languages:
            findings.append(
                LintMessage(
                    severity="warning",
                    code="weak_bilingual_coverage",
                    path=f"glossary_aliases.{canonical}",
                    message="english alias exists without russian counterpart",
                )
            )


def _lint_snake_case(value: str, path: str, findings: List[LintMessage]) -> None:
    if not _SNAKE_CASE_RE.match(value):
        findings.append(
            LintMessage(
                severity="warning",
                code="id_naming_convention",
                path=path,
                message="id should use lower snake_case",
            )
        )


def _lint_duplicate_names(
    *,
    section_name: str,
    items: Sequence[Tuple[str, str | None]],
    findings: List[LintMessage],
) -> None:
    seen: Dict[str, str] = {}
    for item_id, name in items:
        normalized = (name or "").strip().lower()
        if not normalized:
            continue
        if normalized in seen and seen[normalized] != item_id:
            findings.append(
                LintMessage(
                    severity="warning",
                    code="duplicate_canonical_name",
                    path=f"{section_name}.{item_id}.name",
                    message=f"name duplicates canonical name of '{seen[normalized]}'",
                )
            )
        seen.setdefault(normalized, item_id)


def _as_clean_str(value: object) -> str:
    return value.strip().lower() if isinstance(value, str) else ""
