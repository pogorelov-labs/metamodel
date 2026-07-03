"""Wave 1 ontology validator built on top of the normalized model."""
from __future__ import annotations

from typing import Mapping, Optional, Sequence

from .model import NormalizedOntology
from .relation_catalog_validator import validate_relation_catalog
from .validation_types import ValidationMessage, ValidationResult

_ALLOWED_DIRECTIONS = {"directed", "undirected", "bidirectional"}
# Normative attribute data_type whitelist. Keep in sync with the "Enforced"
# list in docs/architecture/attribute_def_contract_v2.md §4.3. Types documented
# there as "Planned / reserved" (date, datetime, url, urn_ref, external_key,
# json) are intentionally NOT here until generator/runtime support lands.
_ALLOWED_VALUE_TYPES = {
    "string",
    "text",
    "integer",
    "number",
    "boolean",
    "enum",
    "id",
    "uri",
}
_ALLOWED_QUALIFIER_CARDINALITY = {"one", "many", "optional"}
_ALLOWED_LIFECYCLE_STATUS = {"active", "deprecated", "experimental", "draft", "stub"}


class OntologyValidationError(ValueError):
    """Raised when ontology fails Wave 1 validation checks."""


def validate_ontology(ontology: NormalizedOntology) -> ValidationResult:
    """Validate normalized ontology and return structured Wave 1 findings."""

    errors: list[ValidationMessage] = []
    warnings: list[ValidationMessage] = []

    _validate_core_structure(ontology, errors)
    _validate_entity_kinds(ontology, errors)
    _validate_attribute_definitions(ontology, errors)
    _validate_relation_kinds(ontology, errors)
    _validate_qualifiers(ontology, errors)
    _validate_glossary_aliases(ontology, errors, warnings)

    relation_catalog_result = validate_relation_catalog(ontology)
    errors.extend(relation_catalog_result.errors)
    warnings.extend(relation_catalog_result.warnings)

    return ValidationResult(errors=tuple(errors), warnings=tuple(warnings))


def ensure_valid_ontology(ontology: NormalizedOntology) -> ValidationResult:
    """Validate ontology and raise a readable fatal error if it is invalid."""

    result = validate_ontology(ontology)
    if result.is_valid:
        return result

    lines = ["Wave 1 ontology validation failed:"]
    for issue in result.errors:
        lines.append(f"- [{issue.code}] {issue.path}: {issue.message}")
    raise OntologyValidationError("\n".join(lines))


def _validate_core_structure(ontology: NormalizedOntology, errors: list[ValidationMessage]) -> None:
    for key in ("model_name", "version", "bank_code"):
        value = ontology.meta.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(
                ValidationMessage(
                    code="missing_meta",
                    path=f"meta.{key}",
                    message="required metadata field is missing",
                )
            )

    if not ontology.entity_kinds:
        errors.append(ValidationMessage("missing_section", "entity_kinds section is empty", "entity_kinds"))
    if not ontology.relation_kinds:
        errors.append(ValidationMessage("missing_section", "relation_kinds section is empty", "relation_kinds"))


def _validate_entity_kinds(ontology: NormalizedOntology, errors: list[ValidationMessage]) -> None:
    entity_ids = [entity.id for entity in ontology.entity_kinds]
    _append_duplicate_errors(entity_ids, "entity_kinds", errors)

    attribute_ids = {attribute.id for attribute in ontology.attribute_definitions}
    for entity in ontology.entity_kinds:
        if entity.name is not None and not entity.name.strip():
            errors.append(ValidationMessage("invalid_entity", "name cannot be blank", f"entity_kinds.{entity.id}.name"))

        for key in ("key_attribute_id", "default_title_attribute_id"):
            attr_id = entity.extra.get(key)
            if attr_id is None:
                continue
            if not isinstance(attr_id, str) or attr_id not in attribute_ids:
                errors.append(
                    ValidationMessage(
                        code="missing_reference",
                        path=f"entity_kinds.{entity.id}.{key}",
                        message=f"attribute reference '{attr_id}' does not exist",
                    )
                )

        for key in ("status", "lifecycle_status"):
            status_value = entity.extra.get(key)
            if status_value is None:
                continue
            if not isinstance(status_value, str) or status_value not in _ALLOWED_LIFECYCLE_STATUS:
                errors.append(
                    ValidationMessage(
                        code="invalid_enum",
                        path=f"entity_kinds.{entity.id}.{key}",
                        message=f"unsupported lifecycle/status value '{status_value}'",
                    )
                )


def _validate_attribute_definitions(ontology: NormalizedOntology, errors: list[ValidationMessage]) -> None:
    attribute_ids = [attribute.id for attribute in ontology.attribute_definitions]
    _append_duplicate_errors(attribute_ids, "attribute_definitions", errors)

    entity_ids = {entity.id for entity in ontology.entity_kinds}
    for attribute in ontology.attribute_definitions:
        if attribute.owner_kind_id is not None and attribute.owner_kind_id not in entity_ids:
            errors.append(
                ValidationMessage(
                    code="missing_reference",
                    path=f"attribute_definitions.{attribute.id}.owner_kind_id",
                    message=f"owner kind '{attribute.owner_kind_id}' does not exist",
                )
            )

        datatype = _first_present(attribute.extra, "datatype", "data_type", "value_type", "type")
        if datatype is not None and (not isinstance(datatype, str) or datatype not in _ALLOWED_VALUE_TYPES):
            errors.append(
                ValidationMessage(
                    code="invalid_enum",
                    path=f"attribute_definitions.{attribute.id}.datatype",
                    message=f"unsupported datatype '{datatype}'",
                )
            )

        cardinality = _first_present(attribute.extra, "cardinality", "value_cardinality")
        if cardinality is not None and (
            not isinstance(cardinality, str) or cardinality not in _ALLOWED_QUALIFIER_CARDINALITY
        ):
            errors.append(
                ValidationMessage(
                    code="invalid_enum",
                    path=f"attribute_definitions.{attribute.id}.cardinality",
                    message=f"unsupported cardinality '{cardinality}'",
                )
            )

        allowed_values = _first_present(attribute.extra, "allowed_values", "enum_values")
        if allowed_values is not None:
            if not isinstance(allowed_values, list) or not allowed_values:
                errors.append(
                    ValidationMessage(
                        code="invalid_attribute",
                        path=f"attribute_definitions.{attribute.id}.allowed_values",
                        message="enum values must be a non-empty list",
                    )
                )
            elif any(not isinstance(item, str) or not item.strip() for item in allowed_values):
                errors.append(
                    ValidationMessage(
                        code="invalid_attribute",
                        path=f"attribute_definitions.{attribute.id}.allowed_values",
                        message="enum values must be non-empty strings",
                    )
                )

        ref_kind = _first_present(attribute.extra, "ref_kind", "reference_kind_id")
        if ref_kind is not None and (not isinstance(ref_kind, str) or ref_kind not in entity_ids):
            errors.append(
                ValidationMessage(
                    code="missing_reference",
                    path=f"attribute_definitions.{attribute.id}.ref_kind",
                    message=f"reference target kind '{ref_kind}' does not exist",
                )
            )


def _validate_relation_kinds(ontology: NormalizedOntology, errors: list[ValidationMessage]) -> None:
    relation_ids = [relation.id for relation in ontology.relation_kinds]
    _append_duplicate_errors(relation_ids, "relation_kinds", errors)

    entity_ids = {entity.id for entity in ontology.entity_kinds}
    for relation in ontology.relation_kinds:
        if relation.from_kind is None or relation.from_kind not in entity_ids:
            errors.append(
                ValidationMessage(
                    code="missing_reference",
                    path=f"relation_kinds.{relation.id}.from_kind",
                    message=f"from_kind '{relation.from_kind}' does not resolve to an entity kind",
                )
            )
        if relation.to_kind is None or relation.to_kind not in entity_ids:
            errors.append(
                ValidationMessage(
                    code="missing_reference",
                    path=f"relation_kinds.{relation.id}.to_kind",
                    message=f"to_kind '{relation.to_kind}' does not resolve to an entity kind",
                )
            )
        if relation.direction is not None and relation.direction not in _ALLOWED_DIRECTIONS:
            errors.append(
                ValidationMessage(
                    code="invalid_enum",
                    path=f"relation_kinds.{relation.id}.direction",
                    message=f"unsupported direction '{relation.direction}'",
                )
            )


def _validate_qualifiers(ontology: NormalizedOntology, errors: list[ValidationMessage]) -> None:
    qualifier_ids = [qualifier.id for qualifier in ontology.qualifier_definitions]
    if ontology.relation_catalog is not None:
        qualifier_ids.extend(qualifier.id for qualifier in ontology.relation_catalog.qualifier_references)
    _append_duplicate_errors(qualifier_ids, "qualifier_definitions", errors)

    for qualifier in ontology.qualifier_definitions:
        value_type = _first_present(qualifier.extra, "value_type", "allowed_value_type")
        if value_type is not None and (not isinstance(value_type, str) or value_type not in _ALLOWED_VALUE_TYPES):
            errors.append(
                ValidationMessage(
                    code="invalid_enum",
                    path=f"qualifier_definitions.{qualifier.id}.value_type",
                    message=f"unsupported qualifier value_type '{value_type}'",
                )
            )
        cardinality = qualifier.extra.get("cardinality")
        if cardinality is not None and (
            not isinstance(cardinality, str) or cardinality not in _ALLOWED_QUALIFIER_CARDINALITY
        ):
            errors.append(
                ValidationMessage(
                    code="invalid_enum",
                    path=f"qualifier_definitions.{qualifier.id}.cardinality",
                    message=f"unsupported qualifier cardinality '{cardinality}'",
                )
            )


def _validate_glossary_aliases(
    ontology: NormalizedOntology,
    errors: list[ValidationMessage],
    warnings: list[ValidationMessage],
) -> None:
    alias_ids = [alias.id for alias in ontology.glossary_aliases]
    _append_duplicate_errors(alias_ids, "glossary_aliases", errors)

    entity_ids = {entity.id for entity in ontology.entity_kinds}
    seen_aliases = set()
    for alias in ontology.glossary_aliases:
        if alias.alias and alias.alias in entity_ids:
            errors.append(
                ValidationMessage(
                    code="alias_collision",
                    path=f"glossary_aliases.{alias.id}.alias",
                    message=f"alias '{alias.alias}' collides with an entity kind id",
                )
            )
        key = ((alias.language or "").strip().lower(), (alias.alias or "").strip().lower())
        if key in seen_aliases and key[1]:
            warnings.append(
                ValidationMessage(
                    code="duplicate_alias",
                    path=f"glossary_aliases.{alias.id}",
                    message=f"duplicate alias '{alias.alias}' for language '{alias.language}'",
                )
            )
        seen_aliases.add(key)


def _append_duplicate_errors(ids: Sequence[str], namespace: str, errors: list[ValidationMessage]) -> None:
    seen = set()
    duplicates = set()
    for item_id in ids:
        if item_id in seen:
            duplicates.add(item_id)
        seen.add(item_id)
    for duplicate in sorted(duplicates):
        errors.append(
            ValidationMessage(
                code="duplicate_id",
                path=namespace,
                message=f"duplicate id '{duplicate}'",
            )
        )


def _first_present(mapping: Mapping[str, object], *keys: str) -> Optional[object]:
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return value
    properties = mapping.get("properties")
    if isinstance(properties, Mapping):
        for key in keys:
            value = properties.get(key)
            if value is not None:
                return value
    return None
