# ADR — business_operation as a first-class entity_kind

- **Status:** accepted (decision) · **implementation: pending** (currently `stub`)
- **Date:** 2026-07-01 (dated record of a prior undated decision)
- **Supersedes framing of:** [`formal_decision_business_operation.md`](formal_decision_business_operation.md)

## Why this ADR exists

The `business_operation` decision was captured in
[`formal_decision_business_operation.md`](formal_decision_business_operation.md)
as a rich but **undated, un-ticketed** document. This ADR gives it a dated,
time-indexed entry in the decision log (consistent with the MACWO-526..531 ADRs)
and records the **gap between the decision and the current model state**.

## Decision (restated)

`business_operation` is accepted as a **first-class, mandatory execution-layer
entity_kind** — the canonical target for BPMN activity/task mapping and the
seam between the process layer and functions/systems/data/entities. It is not a
future-state extension. Full rationale, the canonical definition, the 8 MVP
attributes (`id`, `name`, `status`, `process_local_code`, `criticality`,
`automation_level`, `trigger`, `outcome`) and the 3 P0 relations
(`process → operation`, `operation → function`, `operation → system/component`)
live in the formal decision document and are not repeated here.

## Current state vs. decision (the gap)

As of this ADR the kind is present but **unimplemented**:

```yaml
- id: business_operation
  metamodel_level: business_details
  category: process
  status: stub          # ← declared, 0 attributes
```

Consequences of the gap, all consistent with other findings:

- `business_operation` is one of the 9 `stub` entity_kinds (0 attributes).
- The P0 relations that depend on it (`rel_process_decomposes_to_operation`,
  `rel_operation_executes_function`, …) are named in
  `business_layer_relation_matrix.md` but are **not** present under those ids in
  the post-MACWO-512 model — see
  [`adr-20260701-core-only-relations.md`](adr-20260701-core-only-relations.md).

## Decision now

1. Keep the decision **accepted** — `business_operation` stays first-class in
   intent; do not demote or delete it.
2. Track its **implementation** (promote `stub` → `active`: the 8 MVP
   attributes + 3 P0 relations + BPMN mapping) as a roadmap item under the
   stub-promotion effort (MACWO-534) — see `ROADMAP.md`.
3. When implemented, reconcile the relation ids with
   `business_layer_relation_matrix.md` in the same pass.

## Consequences

- The decision log now has a dated entry for `business_operation`.
- The stub↔decision gap is explicit and tracked, not silent.
- No model change in this PR (documentation only).
