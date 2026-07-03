# Metamodel Roadmap

Forward-looking plan for the metamodel ontology. Complements the decision log
(`docs/decisions/`) and architecture contracts (`docs/architecture/`). Items are
grouped, not strictly time-ordered; ticket ids are Plane MACWO where known.

## Status snapshot (2026-07-01)

- Model version `2` · **49** entity_kinds (38 active / 9 stub / 2 draft) ·
  **310** attributes · **231** relation_kinds (188 profile overlays).
- CI green: `make validate` 0 errors / 1 warning (the accepted
  `rule3_core_only_relations` notice), 314 tests.
- Downstream: `rbank-atlas` pinned to bundle **v7** (MACWO-529/530/531 promoted).

## Recently shipped — PDF 1.0 porting (epic MACWO-525)

Systematic port of the bank's attribute vocabulary from PDF «Глоссарий 1.0»
(SSCAR-615105454) into the canonical model, making the metamodel the single
source of truth for downstream ingest. All merged 2026-04-09..10:

| Ticket | Delivered |
|--------|-----------|
| MACWO-526 | business_process +54 attributes |
| MACWO-527 | it_system +41 attributes |
| MACWO-528 | value_stream +27 attributes; same-direction relation dedupe |
| MACWO-529 | business_capability +18 attributes (RBI integration) |
| MACWO-530 | `event` entity_kind |
| MACWO-531 | `sensitivity_level` entity_kind |

## Backlog

### MACWO-532 — migrate scalar `sensitive_level` → typed reference (breaking)

Change `business_attribute.sensitive_level` and `data_product.sensitive_level`
from `data_type: string` → `data_type: id` + `ref_kind: sensitivity_level`, so
they reference the `sensitivity_level` entity added in MACWO-531. Breaking for
downstream consumers — needs a migration/communication plan. (`id` is the
enforced reference type today; see
`docs/architecture/attribute_def_contract_v2.md` §4.3.)

### MACWO-533 — reconcile RTO/RPO duplication

RTO/RPO are modelled on both `business_process` and `sla`. Decide the canonical
owner and reference the other, to avoid divergent values.

### MACWO-534 — promote stub entity_kinds

Nine kinds are declared but empty (`status: stub`, 0 attributes):
`business_function`, `business_operation`, `business_action`, `vendor_product`,
`technology`, `source`, `component_instance`, `delivery_contract`, `job`.

**Promotion criteria (stub → active):** a kind is ready to promote when it has
(1) its MVP attribute set from an authoritative source, (2) `key_attribute_id` +
`default_title_attribute_id`, (3) at least one P0 relation with an active
endpoint carrying a catalog overlay, and (4) an ADR if it changes the business
layer. Promoting a stub also clears any core-only relations touching it
(see below).

Priority within this effort: **`business_operation`** — already an accepted
first-class decision (`docs/decisions/adr-20260701-business-operation.md`) but
still a stub; implement its 8 MVP attributes + 3 P0 relations + BPMN mapping.

### Profile-enrichment triage (core-only relations)

Per `docs/decisions/adr-20260701-core-only-relations.md`: 37 active-to-active
relation_kinds have no `atlas_mvp` overlay. Before touching them:

1. **Reconcile `docs/architecture/business_layer_relation_matrix.md`** with the
   post-MACWO-512 relation ids (the matrix still names pre-restructuring ids
   like `rel_value_stream_contains_stage`).
2. Promote the matrix-**P0** subset into the overlay; leave P1/P2 core-only.

## Accepted / known states (not defects)

- `rule3_core_only_relations` harness warning — governed by
  `docs/decisions/adr-20260701-core-only-relations.md`.
- `data_type` "Planned / reserved" values (`date`, `datetime`, `url`,
  `urn_ref`, `json`, `external_key`) are documented but intentionally not yet
  accepted by the validator — see `attribute_def_contract_v2.md` §4.3.

## Release & promotion

Cutting and promoting bundles is documented in
`generated/atlas_candidates/README.md`. In short: `make bundle` →
move under an immutable `__vN` in `generated/atlas_candidates/` → commit →
`promote-bundle.yaml` promotes to `rbank-atlas` on merge (idempotent).
