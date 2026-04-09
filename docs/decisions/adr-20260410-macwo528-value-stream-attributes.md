# ADR — MACWO-528: Port PDF 1.0 value_stream attributes into metamodel.yaml

- **Status:** accepted
- **Date:** 2026-04-10
- **Ticket:** MACWO-528 (sub-issue of MACWO-525)

## Context

PDF «Атрибутивный состав 1.0» describes 28 attributes for value_stream including the classical VSM time quartet (Lead Time / Process Time / Delay Time / Value-Added Time) and metrics FAI/STP/FPY/NPS. Prior to this PR `value_stream` had only 2 legacy attributes: `goal` and `owner`.

## Decision

Port 27 new value_stream attributes into `model/metamodel.yaml` in v2 contract form. Skip PDF #24 «Владелец» — already present as `value_stream.owner`. Add 2 new relation_kinds + catalog overlays.

### Groups (27 new)

| display_group | # | Notable fields |
|---|---:|---|
| `core` | 9 | code, name, short_description, domain, is_deterministic, status, maturity, criticality, version |
| `consumer` | 3 | job_family_id, product_id, consumer_type |
| `value` | 2 | trigger, delivered_value |
| `vsm` | 4 | lead_time, process_time, delay_time, value_added_time (all `unit: days`) |
| `metrics` | 5 | first_pass_yield, operating_cost, customer_satisfaction, fai, stp |
| `risks` | 1 | risks |
| `ownership` | 1 | org_unit_id |
| `lifecycle` | 2 | created_at, updated_at |

### VSM time quartet

All four VSM times are `data_type: number, unit: days, category: data, display_group: vsm`. This enables Atlas to render the classic VSM diagram from a single entity card and compute lead-time efficiency (Value-Added Time / Lead Time).

### New relation_kinds (2)

- `rel_value_stream_targets_job_family` → job_family
- `rel_value_stream_governed_by_org_unit` → organizational_unit

`product_id` is kept as scalar `id` ref only (no new relation_kind) because `rel_bank_product_has_value_stream` already exists in the inverse direction.

## Validation

- `make validate` — 0 errors, 3 pre-existing warnings
- `make test` — 37 new parametrised cases, all passed

## References

- Source: `~/msc_1/meta/глоссарий и атрибуты/атрибутивный_состав.yaml` → `contexts.business_context.entities[1].attributes`
- Epic: MACWO-525
