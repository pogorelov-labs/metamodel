"""Dedicated Wave 1 relation catalog validator."""
from __future__ import annotations

import re
from typing import Iterable, List, Mapping, Optional, Sequence, Tuple

from .model import NormalizedOntology, RelationCatalogRelation
from .validation_types import ValidationMessage, ValidationResult

_ALLOWED_DIRECTIONS = {"directed", "undirected", "bidirectional"}
_ALLOWED_CARDINALITIES = {"one", "many"}
_ALLOWED_VISIBILITY = {"visible", "collapsed", "hidden"}
_ALLOWED_PATH_PRIORITY = {"primary", "secondary", "tertiary", "excluded"}
_ALLOWED_IMPACT_MODE = {"propagate", "explain_only", "exclude"}
_ALLOWED_STATUS = {"active", "deprecated", "experimental"}
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

_REQUIRED_RELATION_FIELDS = (
    "id",
    "from_kind",
    "to_kind",
    "direction",
    "source_cardinality",
    "target_cardinality",
    "has_inverse",
    "default_visibility",
    "path_priority",
    "impact_mode",
    "supports_qualifiers",
    "allowed_qualifiers",
    "required_qualifiers",
    "status",
    "introduced_in",
    "applies_to_profiles",
)


class RelationCatalogValidationError(ValueError):
    """Raised when relation catalog fails dedicated validation checks."""


def validate_relation_catalog(ontology: NormalizedOntology) -> ValidationResult:
    """Validate the relation catalog section of a normalized ontology."""

    errors: List[ValidationMessage] = []
    warnings: List[ValidationMessage] = []

    catalog = ontology.relation_catalog
    if catalog is None:
        return ValidationResult(errors=(), warnings=())

    entity_ids = {entity.id for entity in ontology.entity_kinds}
    qualifier_ids = {qualifier.id for qualifier in ontology.qualifier_definitions}
    qualifier_ids.update(qualifier.id for qualifier in catalog.qualifier_references)
    declared_profiles = set(ontology.profiles) | set(catalog.profiles)

    _append_duplicate_errors([relation.id for relation in catalog.relations], "relation_catalog.relations", errors)
    _append_duplicate_errors(
        [qualifier.id for qualifier in catalog.qualifier_references],
        "relation_catalog.qualifier_references",
        errors,
    )

    relations_by_id = {relation.id: relation for relation in catalog.relations}
    for relation in catalog.relations:
        _validate_relation_entry_fields(relation, errors)
        _validate_endpoint_integrity(relation, entity_ids, warnings)
        _validate_inverse_integrity(relation, relations_by_id, errors)
        _validate_controlled_fields(relation, errors)
        _validate_qualifier_policy(relation, qualifier_ids, errors)
        _validate_semantics_consistency(relation, errors, warnings)
        _validate_profile_lifecycle_rules(relation, declared_profiles, errors)

    if any("atlas_mvp" in _as_str_list(r.payload.get("applies_to_profiles")) for r in catalog.relations):
        if "atlas_mvp" not in declared_profiles:
            errors.append(
                ValidationMessage(
                    code="missing_reference",
                    path="profiles",
                    message="atlas_mvp is referenced but not declared in ontology/relation catalog profiles",
                )
            )

    return ValidationResult(errors=tuple(sorted(errors, key=_message_sort_key)), warnings=tuple(sorted(warnings, key=_message_sort_key)))


def ensure_valid_relation_catalog(ontology: NormalizedOntology) -> ValidationResult:
    """Validate relation catalog and raise readable fatal error when invalid."""

    result = validate_relation_catalog(ontology)
    if not result.errors:
        return result

    lines = ["Wave 1 relation catalog validation failed:"]
    for issue in result.errors:
        lines.append(f"- [{issue.code}] {issue.path}: {issue.message}")
    raise RelationCatalogValidationError("\n".join(lines))


def _validate_relation_entry_fields(relation: RelationCatalogRelation, errors: List[ValidationMessage]) -> None:
    payload = relation.payload
    for field in _REQUIRED_RELATION_FIELDS:
        if field not in payload or payload.get(field) is None:
            errors.append(
                ValidationMessage(
                    code="missing_field",
                    path=f"relation_catalog.relations.{relation.id}.{field}",
                    message="required relation catalog field is missing",
                )
            )


def _validate_endpoint_integrity(
    relation: RelationCatalogRelation,
    entity_ids: set[str],
    warnings: List[ValidationMessage],
) -> None:
    _validate_endpoint_value("from_kind", relation.from_kind, relation.id, entity_ids, warnings)
    _validate_endpoint_value("to_kind", relation.to_kind, relation.id, entity_ids, warnings)


def _validate_endpoint_value(
    field_name: str,
    value: Optional[str],
    relation_id: str,
    entity_ids: set[str],
    warnings: List[ValidationMessage],
) -> None:
    if not value:
        warnings.append(
            ValidationMessage(
                code="missing_reference",
                path=f"relation_catalog.relations.{relation_id}.{field_name}",
                message=f"{field_name} is empty",
            )
        )
        return

    if value not in entity_ids:
        warnings.append(
            ValidationMessage(
                code="external_reference",
                path=f"relation_catalog.relations.{relation_id}.{field_name}",
                message=f"{field_name} '{value}' is not in current ontology entity_kinds",
            )
        )


def _validate_inverse_integrity(
    relation: RelationCatalogRelation,
    relations_by_id: Mapping[str, RelationCatalogRelation],
    errors: List[ValidationMessage],
) -> None:
    payload = relation.payload
    has_inverse = payload.get("has_inverse")
    inverse_relation_id = payload.get("inverse_relation_id")

    if has_inverse is True:
        if not isinstance(inverse_relation_id, str) or inverse_relation_id not in relations_by_id:
            errors.append(
                ValidationMessage(
                    code="missing_reference",
                    path=f"relation_catalog.relations.{relation.id}.inverse_relation_id",
                    message="has_inverse=true requires existing inverse_relation_id",
                )
            )
            return

        inverse_relation = relations_by_id[inverse_relation_id]
        inverse_payload = inverse_relation.payload

        if inverse_payload.get("has_inverse") is not True:
            errors.append(
                ValidationMessage(
                    code="invalid_inverse",
                    path=f"relation_catalog.relations.{relation.id}.inverse_relation_id",
                    message="inverse relation must also declare has_inverse=true",
                )
            )

        if inverse_payload.get("inverse_relation_id") != relation.id:
            errors.append(
                ValidationMessage(
                    code="invalid_inverse",
                    path=f"relation_catalog.relations.{relation.id}.inverse_relation_id",
                    message="inverse relation must point back to source relation",
                )
            )

        if relation.from_kind != inverse_relation.to_kind or relation.to_kind != inverse_relation.from_kind:
            errors.append(
                ValidationMessage(
                    code="invalid_inverse",
                    path=f"relation_catalog.relations.{relation.id}",
                    message="inverse relation endpoints must be reversed",
                )
            )
    elif inverse_relation_id:
        errors.append(
            ValidationMessage(
                code="invalid_inverse",
                path=f"relation_catalog.relations.{relation.id}.inverse_relation_id",
                message="inverse_relation_id is only allowed when has_inverse=true",
            )
        )


def _validate_controlled_fields(relation: RelationCatalogRelation, errors: List[ValidationMessage]) -> None:
    payload = relation.payload
    _validate_enum_field(payload, relation.id, "direction", _ALLOWED_DIRECTIONS, errors)
    _validate_enum_field(payload, relation.id, "source_cardinality", _ALLOWED_CARDINALITIES, errors)
    _validate_enum_field(payload, relation.id, "target_cardinality", _ALLOWED_CARDINALITIES, errors)
    _validate_enum_field(payload, relation.id, "default_visibility", _ALLOWED_VISIBILITY, errors)
    _validate_enum_field(payload, relation.id, "path_priority", _ALLOWED_PATH_PRIORITY, errors)
    _validate_enum_field(payload, relation.id, "impact_mode", _ALLOWED_IMPACT_MODE, errors)
    _validate_enum_field(payload, relation.id, "status", _ALLOWED_STATUS, errors)


def _validate_qualifier_policy(
    relation: RelationCatalogRelation,
    qualifier_ids: set[str],
    errors: List[ValidationMessage],
) -> None:
    payload = relation.payload
    supports_qualifiers = payload.get("supports_qualifiers")
    allowed_qualifiers = _as_str_list(payload.get("allowed_qualifiers"))
    required_qualifiers = _as_str_list(payload.get("required_qualifiers"))

    if supports_qualifiers is False and (allowed_qualifiers or required_qualifiers):
        errors.append(
            ValidationMessage(
                code="invalid_qualifier_policy",
                path=f"relation_catalog.relations.{relation.id}",
                message="supports_qualifiers=false cannot define allowed/required qualifiers",
            )
        )

    missing_qualifiers = sorted({*allowed_qualifiers, *required_qualifiers} - qualifier_ids)
    for qualifier_id in missing_qualifiers:
        errors.append(
            ValidationMessage(
                code="missing_reference",
                path=f"relation_catalog.relations.{relation.id}.qualifiers",
                message=f"qualifier '{qualifier_id}' is not declared",
            )
        )

    if set(required_qualifiers) - set(allowed_qualifiers):
        errors.append(
            ValidationMessage(
                code="invalid_qualifier_policy",
                path=f"relation_catalog.relations.{relation.id}.required_qualifiers",
                message="required_qualifiers must be a subset of allowed_qualifiers",
            )
        )


def _validate_semantics_consistency(
    relation: RelationCatalogRelation,
    errors: List[ValidationMessage],
    warnings: List[ValidationMessage],
) -> None:
    payload = relation.payload
    allowed_in_paths = payload.get("allowed_in_paths")
    path_priority = payload.get("path_priority")
    allowed_in_impact = payload.get("allowed_in_impact")
    impact_mode = payload.get("impact_mode")
    default_visibility = payload.get("default_visibility")
    allowed_in_neighbors = payload.get("allowed_in_neighbors")

    if allowed_in_paths is False and path_priority not in {None, "excluded"}:
        errors.append(
            ValidationMessage(
                code="invalid_combination",
                path=f"relation_catalog.relations.{relation.id}",
                message="allowed_in_paths=false requires path_priority=excluded",
            )
        )

    if path_priority == "excluded" and allowed_in_paths is True:
        warnings.append(
            ValidationMessage(
                code="suspicious_combination",
                path=f"relation_catalog.relations.{relation.id}",
                message="path_priority=excluded while allowed_in_paths=true",
            )
        )

    if allowed_in_impact is False and impact_mode not in {None, "exclude"}:
        errors.append(
            ValidationMessage(
                code="invalid_combination",
                path=f"relation_catalog.relations.{relation.id}",
                message="allowed_in_impact=false requires impact_mode=exclude",
            )
        )

    if impact_mode == "exclude" and allowed_in_impact is True:
        warnings.append(
            ValidationMessage(
                code="suspicious_combination",
                path=f"relation_catalog.relations.{relation.id}",
                message="impact_mode=exclude while allowed_in_impact=true",
            )
        )

    if default_visibility == "hidden" and allowed_in_neighbors is True:
        warnings.append(
            ValidationMessage(
                code="suspicious_combination",
                path=f"relation_catalog.relations.{relation.id}",
                message="default_visibility=hidden while allowed_in_neighbors=true",
            )
        )


def _validate_profile_lifecycle_rules(
    relation: RelationCatalogRelation,
    declared_profiles: set[str],
    errors: List[ValidationMessage],
) -> None:
    payload = relation.payload

    introduced_in = payload.get("introduced_in")
    if introduced_in is not None and (not isinstance(introduced_in, str) or not _SEMVER_RE.match(introduced_in)):
        errors.append(
            ValidationMessage(
                code="invalid_format",
                path=f"relation_catalog.relations.{relation.id}.introduced_in",
                message="introduced_in must match semantic version pattern x.y.z",
            )
        )

    applies = payload.get("applies_to_profiles")
    if applies is not None and not isinstance(applies, list):
        errors.append(
            ValidationMessage(
                code="invalid_field",
                path=f"relation_catalog.relations.{relation.id}.applies_to_profiles",
                message="applies_to_profiles must be a list",
            )
        )
        return

    for profile in _as_str_list(applies):
        if profile not in declared_profiles:
            errors.append(
                ValidationMessage(
                    code="missing_reference",
                    path=f"relation_catalog.relations.{relation.id}.applies_to_profiles",
                    message=f"profile '{profile}' is not declared",
                )
            )


def _append_duplicate_errors(ids: Sequence[str], namespace: str, errors: List[ValidationMessage]) -> None:
    seen = set()
    duplicates = set()
    for item_id in ids:
        if item_id in seen:
            duplicates.add(item_id)
        seen.add(item_id)
    for duplicate in sorted(duplicates):
        errors.append(ValidationMessage(code="duplicate_id", path=namespace, message=f"duplicate id '{duplicate}'"))


def _validate_enum_field(
    payload: Mapping[str, object],
    relation_id: str,
    field_name: str,
    allowed_values: Iterable[str],
    errors: List[ValidationMessage],
) -> None:
    value = payload.get(field_name)
    if value is None:
        return

    if not isinstance(value, str) or value not in set(allowed_values):
        errors.append(
            ValidationMessage(
                code="invalid_enum",
                path=f"relation_catalog.relations.{relation_id}.{field_name}",
                message=f"unsupported value '{value}'",
            )
        )


def _as_str_list(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _message_sort_key(message: ValidationMessage) -> Tuple[str, str, str]:
    return (message.path, message.code, message.message)
