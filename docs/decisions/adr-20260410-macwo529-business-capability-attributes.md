# ADR — MACWO-529: Port PDF 1.0 business_capability attributes

- **Status:** accepted
- **Date:** 2026-04-10
- **Ticket:** MACWO-529 (sub-issue of MACWO-525)

## Context

PDF 1.0 describes 19 business_capability attributes including the RBI (ADOIT) mapping fields `code_rbi` and `name_rbi` — critical for integration with the RBI Atlas / ITAR. Prior to this PR `business_capability` had only 1 legacy attribute (`maturity_level`).

## Decision

Port 18 new business_capability attributes in v2 contract form. Skip PDF #9 «Уровень зрелости» — already represented by legacy `maturity_level`. Add 2 ownership relations.

### Groups (18 new + 1 legacy)

| display_group | # | Notable |
|---|---:|---|
| `identity` | 5 | code, code_rbi, name, name_rbi, cbr_techprocess_code |
| `classification` | 4 | short_description, hierarchy_level, specialization, domain |
| `lifecycle` | 3 | status_lifecycle, created_at, updated_at |
| `economics` | 3 | opex_cost, kpi_target, regulatory_compliance |
| `landscape` | 1 | used_it_system_ids (many) |
| `ownership` | 2 | owner_employee_id, org_unit_id |

### RBI integration

`code_rbi` and `name_rbi` carry `source_expectation: [ADOIT]` so downstream ingestors can sync from RBI's ADOIT directly without manual mapping. This unlocks the ITAR migration path mentioned in the PDF source notes.

### `used_it_system_ids` reuses inverse relation

The «Используемые ИТ-системы» field is modeled as a scalar `id`-typed attribute (cardinality: many) with `ref_kind: it_system`. The graph edge is provided by the existing `rel_it_system_realizes_capability` relation in the inverse direction — no new relation_kind needed.

### 2 new ownership relations

- `rel_business_capability_owned_by_employee` → employee
- `rel_business_capability_governed_by_org_unit` → organizational_unit

### `maturity_level` left untouched

Legacy `business_capability.maturity_level` is preserved as-is. Future PR may enrich it with `min_value: 1, max_value: 5` validation hints, but that is out of scope here.

## Validation

- `make validate` — 0 errors, 3 pre-existing warnings
- `make test` — 27 new parametrised cases passed

## References

- Source: `~/msc_1/meta/глоссарий и атрибуты/атрибутивный_состав.yaml` → `contexts.business_context.entities[2].attributes`
- Epic: MACWO-525
