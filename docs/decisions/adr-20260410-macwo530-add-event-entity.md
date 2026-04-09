# ADR — MACWO-530: Add `event` entity_kind

- **Status:** accepted
- **Date:** 2026-04-10
- **Ticket:** MACWO-530 (sub-issue of MACWO-525)

## Context

PDF «Глоссарий 1.0» § «Общие сущности» defines **Событие (Event)** — a fact of significant state change in a business process, system, or data lifecycle. Has a timestamp, type, source, optional payload and severity. Can trigger other processes, notifications or analytics.

The metamodel currently has only `incident`, which is a special case of an Event with high severity and a remediation workflow. Generic events (status changes, ETL completions, SLA violations) cannot be modeled.

## Decision

Add a new entity_kind `event` with 5 attributes and 4 paired relation_kinds connecting events to processes, systems, data products, and incidents.

### Entity

```yaml
- id: event
  name: Event
  name_ru: Событие
  metamodel_level: solution_details
  category: operational
  status: active
  introduced_in: '2.1'
```

### Attributes (5)

| id | data_type | required | display_group |
|---|---|---|---|
| `event.event_type` | enum [business, system, data, security] | yes | core |
| `event.occurred_at` | string (datetime, ISO 8601) | yes | core |
| `event.source` | string | yes | core |
| `event.payload` | text (JSON) | no | details |
| `event.severity` | enum [info, warning, error, critical] | no | details |

### New relations (4)

- `rel_event_emitted_by_business_process` → business_process
- `rel_event_emitted_by_it_system` → it_system
- `rel_event_emitted_by_data_product` → data_product
- `rel_incident_triggered_by_event` → event (incident as source)

### Why event ≠ incident

- **Event** is a fact (timestamped, immutable). Cardinality is high (every status change is an event).
- **Incident** is a workflow state (severity, status, owner, resolution). Cardinality is much lower.
- Mixing them collapses two distinct concerns. Keeping them separate aligns with the source PDF and makes Atlas projection cleaner.

### Why incident gains a new optional relation but stays unchanged

`rel_incident_triggered_by_event` lets an incident be linked back to the originating event when one exists. This is **optional** — incidents can still be created without a source event. No fields on `incident` are touched.

## Validation

- `make validate` — 0 errors, 3 pre-existing warnings
- `make test` — 18 new parametrised cases passed

## References

- Source: `~/msc_1/meta/глоссарий и атрибуты/глоссарий.yaml` → `contexts.common_entities.terms[4]` (Event)
- Epic: MACWO-525
