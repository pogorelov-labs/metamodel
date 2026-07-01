# ADR — Core-only relations (no atlas_mvp catalog overlay)

- **Status:** accepted
- **Date:** 2026-07-01
- **Scope:** two-layer mm/rc contract, Rule 3

## Context

The harness emits one standing warning:

```
[rule3_core_only_relations] metamodel.relation_kinds: 43 relation_kind(s)
have no relation_catalog overlay (allowed under Rule 3)
```

Rule 3 explicitly **permits** relation_kinds declared in `metamodel.yaml`
without a `relation_catalog.yaml` overlay — they exist in the core ontology but
are not projected into the `atlas_mvp` profile. The question this ADR settles is
*whether the current 43 are intentional, and what to do about them* — so the
warning is a governed state rather than an unexplained one.

## Analysis

Classifying the 43 by the lifecycle status of their endpoints
(reproduce with the snippet in the appendix):

| Bucket | Count | Interpretation |
|--------|-------|----------------|
| Touches a `stub`/`draft` endpoint | 6 | **Core-only by design** — the endpoint kind is not in the MVP surface, so no overlay is possible yet |
| Both endpoints `active` | 37 | Declared in core but not projected into `atlas_mvp` — a **profile-scoping** question, not automatically a bug |

### The 6 stub/draft-touching (core-only by design)

| Relation | Non-active endpoint |
|----------|---------------------|
| `rel_action_operates_on_entity` | `business_action` (stub) |
| `rel_role_performs_function` | `business_function` (stub) |
| `rel_delivery_contract_contracts_component` | `delivery_contract` (stub) |
| `rel_delivery_contract_part_of_data_contract` | `delivery_contract` (stub) |
| `rel_component_realized_by_vendor_product` | `vendor_product` (stub) |
| `rel_vendor_product_specializes_it_system` | `vendor_product` (stub) |

These gain overlays naturally when their endpoint kinds are promoted out of
`stub` (roadmap: stub-promotion, MACWO-534).

### The 37 active-to-active

These connect two `active` kinds yet carry no overlay, e.g. across domains:

- **value_stream:** `rel_value_stream_aggregates_stages`, `rel_value_stream_produces_value`, `rel_value_stream_serves_segment`, `rel_value_stream_uses_channel`, `rel_value_stream_composed_of_products`, `rel_stage_realizes_capability`, `rel_capability_serves_value_stream`
- **org_unit:** `rel_org_unit_achieves_goal`, `rel_org_unit_performs_capability`, `rel_org_unit_creates_product`, `rel_org_unit_serves_it_system`
- **goal / value:** `rel_goal_has_subgoal`, `rel_capability_needed_for_goal`, `rel_value_associated_with_goal`, `rel_value_sold_within_product`, `rel_product_delivers_value`, `rel_channel_serves_value`, `rel_product_belongs_to_domain`, `rel_job_family_aggregates_product`
- **data layer:** `rel_data_product_contains_data_object`, `rel_data_contract_covers_data_object`, `rel_data_contract_part_of_data_product`, `rel_data_object_has_meta_data_contract`, `rel_data_process_operates_on_data_object`, `rel_data_process_produces_metric`, `rel_business_entity_describes_data_product`, `rel_requirement_applies_to_data_object`, `rel_sla_covers_data_object`, `rel_component_creates_data_process`
- **it_system / infra:** `rel_it_system_contains_subsystem`, `rel_it_system_realizes_capability`, `rel_it_system_master_for_entity`, `rel_business_entity_managed_by_it_system`, `rel_infra_resource_serves_component`, `rel_logical_resource_serves_component`, `rel_logical_resource_serves_integration`, `rel_integration_uses_methods`

### Sub-finding: the relation matrix is partially stale

`docs/architecture/business_layer_relation_matrix.md` names several **P0
mandatory** relations under ids that predate the MACWO-512 relation
restructuring and no longer match the model, e.g.:

- matrix `rel_value_stream_contains_stage` ≈ model `rel_value_stream_aggregates_stages` (core-only, in the 37)
- matrix `rel_process_decomposes_to_operation`, `rel_operation_executes_function` reference `business_operation` / `business_function`, now **stubs**

So a subset of the 37 are actually **P0-concept** relations that lost their
overlay in the restructuring — a real gap masked by the id drift, not a
deliberate scoping choice.

## Decision

1. **Accept** the 6 stub/draft-touching relations as core-only until their
   endpoints are promoted (MACWO-534). No action now.
2. **Do not** bulk-author 37 overlays. Adding them blindly would inflate the
   `atlas_mvp` surface (and the downstream bundle) without product scoping
   sign-off, and would ship P1/P2 relations the matrix deliberately defers.
3. **Schedule a profile-enrichment triage pass** (roadmap) that:
   - first reconciles `business_layer_relation_matrix.md` ids with the
     post-MACWO-512 model, then
   - promotes the matrix-**P0** subset of the 37 into the `atlas_mvp` overlay,
     leaving P1/P2 as core-only by design.
4. Until that pass lands, the `rule3_core_only_relations` warning is an
   **expected, governed state**, not a defect.

## Consequences

- The harness keeps emitting exactly one warning (`rule3_core_only_relations`);
  it is now documented and traceable to this ADR.
- No change to the model, the profile, or the bundle in this PR.
- Two backlog items are created (see `ROADMAP.md`): matrix reconciliation +
  P0-overlay promotion; stub promotion (MACWO-534) clears the other 6.

## Appendix — reproduce the classification

```python
import yaml
mm = yaml.safe_load(open('model/metamodel.yaml'))
rc = yaml.safe_load(open('model/relation_catalog.yaml'))
status = {e['id']: e.get('status') for e in mm['entity_kinds']}
cat = {r['id'] for r in rc['relation_catalog']['relations']}
for rk in mm['relation_kinds']:
    if rk['id'] in cat:
        continue
    fs, ts = status.get(rk.get('from_kind')), status.get(rk.get('to_kind'))
    tag = 'by-design(stub/draft)' if 'active' not in (fs, ts) else 'active-active(triage)'
    print(tag, rk['id'], f"{rk.get('from_kind')}[{fs}] -> {rk.get('to_kind')}[{ts}]")
```
