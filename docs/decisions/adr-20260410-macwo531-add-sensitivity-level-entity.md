# ADR — MACWO-531: Add `sensitivity_level` entity_kind

- **Status:** accepted
- **Date:** 2026-04-10
- **Ticket:** MACWO-531 (sub-issue of MACWO-525)

## Context

PDF «Глоссарий 1.0» § «Общие сущности» defines **Категория чувствительной информации** — a classification level with handling rules, encryption requirements, and retention policy.

In the metamodel today the concept exists only as **string-typed** attributes:
- `business_attribute.sensitive_level`
- `data_product.sensitive_level`

This means:
- No validation of allowed values
- No central source of handling rules
- No way to update rules without touching every consumer
- No graph traversal from a sensitivity level to its governed entities

## Decision

Add `sensitivity_level` as a first-class entity_kind with 6 attributes and 3 paired relation_kinds. Migration of the existing scalar fields to graph references is **out of scope** for this PR — see follow-up MACWO-532 (PR-7).

### Entity

```yaml
- id: sensitivity_level
  name: Sensitivity Level
  name_ru: Категория чувствительной информации
  metamodel_level: data_details
  category: governance
  status: active
  introduced_in: '2.1'
```

### Attributes (6)

| id | data_type | required | display_group |
|---|---|---|---|
| `sensitivity_level.level_code` | enum [public, internal, restricted, confidential, secret] | yes | core |
| `sensitivity_level.name_ru` | string | yes | core |
| `sensitivity_level.handling_rules` | text | yes | rules |
| `sensitivity_level.required_encryption` | boolean | yes | rules |
| `sensitivity_level.retention_policy` | text | no | rules |
| `sensitivity_level.regulatory_basis` | text | no | rules |

### 3 new governance relations

- `rel_sensitivity_level_governs_business_attribute` → business_attribute (1:N)
- `rel_sensitivity_level_governs_data_product` → data_product (1:N)
- `rel_sensitivity_level_governs_data_object` → data_object (1:N)

### Why a separate entity, not just a dictionary

A sensitivity_level carries non-trivial governance metadata (handling rules, retention policy, regulatory basis). A flat dictionary doesn't fit:

- Rules can change over time without renaming the level
- Different `level_code`s can be governed by different regulatory bases
- Atlas should support querying "all data products under regulatory basis X" — only graph edges enable this

### Why migration is out of scope

PR-7 (MACWO-532) will:
- Change `business_attribute.sensitive_level` and `data_product.sensitive_level` from `data_type: string` → `data_type: id` + `ref_kind: sensitivity_level`
- Document the change as a breaking change for downstream consumers

Doing both in one PR mixes net-new with breaking change. Splitting them lets PR-6 land safely while PR-7 takes longer review.

## Validation

- `make validate` — 0 errors, 3 pre-existing warnings
- `make test` — 16 new parametrised cases passed

## References

- Source: `~/msc_1/meta/глоссарий и атрибуты/глоссарий.yaml` → `contexts.common_entities.terms[2]`
- Epic: MACWO-525
- Follow-up: MACWO-532 (PR-7 migration of existing sensitive_level fields)
