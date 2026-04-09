# ADR — MACWO-526: Port PDF 1.0 business_process attributes into metamodel.yaml

- **Status:** accepted
- **Date:** 2026-04-10
- **Ticket:** MACWO-526 (sub-issue of MACWO-525 «PDF 1.0 → metamodel attributes»)
- **Deciders:** solo contributor (d1249)
- **Model version:** `meta.version: 2`; new attributes carry `introduced_in: '2.1'`

## Context

The Russian PDF **«Атрибутивный состав 1.0»** (SSCAR-615105454) describes **57 attributes** for `business_process`, grouped by downstream consumer:

- core process identification (14 fields)
- regulatory (716-П, ICS) (17 fields)
- BCM continuity (11 fields)
- operational metrics (6 fields)
- dependencies (2 fields)
- ownership (8 fields)
- IT landscape (1 field)
- misc / notes (1 field)

These are the fields actual downstream systems (S1, Archer, BCM, AppSec, SimpleOne CSP) populate when ingesting a business process.

Prior to this change `metamodel.yaml` declared only **4 attributes** for `business_process`:

- `business_capability_id`
- `business_domain_id`
- `business_owner_id`
- `tier`

This forced every downstream consumer to carry their own field catalogue, and blocked automatic ingestion because the metamodel was not the source of truth for the attributive surface.

## Decision

Port all PDF 1.0 business_process attributes into `model/metamodel.yaml` **in v2 contract form** (see `docs/architecture/attribute_def_contract_v2.md`), plus the ref-field relations into `relation_kinds[]` and `relation_catalog.yaml`. Leave the four legacy attributes untouched in this PR — they will be enriched with v2 fields in a follow-up.

### What this PR adds

- **54 new attributes** on `business_process.attributes` (3 PDF fields overlap with existing legacy attributes and are skipped — see «Trade-offs» below).
- **8 new relation_kinds** in `metamodel.yaml`.
- **8 new catalog relations** in `relation_catalog.yaml` (mm/rc contract Rule 1 satisfied).
- **2 migration scripts** in `tools/migrations/` (idempotent).
- **1 regression test** in `tests/test_macwo526_business_process.py` (39 parameterised cases).

### Attribute structure

Each new attribute is a dict in `v2` contract form:

```yaml
- id: business_process.code_716p
  name: Code 716-P
  name_ru: Код 716-П
  description: Классификатор процесса по положению ЦБ РФ 716-П.
  data_type: string
  cardinality: one
  required: false
  category: evidence
  metamodel_level: business_details
  display_mode: plain
  display_group: regulatory
  status: active
  introduced_in: '2.1'
  example_values:
  - 3.9.1.
  source_expectation:
  - S1
  - Archer
  quality_expectation: recommended
  display_order: 140
```

### Grouping via `display_group`

Even though the PR is a single big commit, attributes are organised into 9 logical groups so entity cards render them in the intended order:

| display_group | Count | PDF sections |
|---|---:|---|
| `core` | 13 | identification, status, lifecycle dates, trigger, result |
| `regulatory` | 5 | 716-П, ВНД, НПА |
| `ics` | 9 | ICS prioritization/classification, risks, controls, Archer, ORM, DORS |
| `bcm` | 11 | RTO/RPO/MTPD/MBCO, CIA refs, segment impact, counterparties |
| `ops` | 6 | lead time, FPY, cost, FAI, STP |
| `dependencies` | 2 | inbound/outbound process codes |
| `ownership` | 7 | employees, teams, org_units, collective bodies, control owners |
| `landscape` | 1 | related IT systems |
| **Total** | **54** | |

`display_order` is assigned sequentially (10, 20, 30, …) so entity cards respect the intended rendering.

### Reference fields — hybrid model

Per MACWO-600 plan (developer answered Q1 with «hybrid»), each «Ссылка на объект» PDF field is modelled as:

1. A scalar attribute with `data_type: id` + `ref_kind: <target_entity_kind>` (harness validator whitelists only `string, text, integer, number, boolean, enum, id, uri` — so `urn_ref` from the v2 contract doc is mapped to `id`).
2. A paired `relation_kind` in `metamodel.yaml`.
3. A paired catalog overlay in `relation_catalog.yaml`.

This lets ingestors populate the scalar FK while giving Atlas a first-class edge in the graph.

### BCM fields — direct in business_process

Per the plan (Q2), RTO/RPO/MTPD/MBCO are placed directly on `business_process`, not through the existing `sla` entity_kind. Reasons:

- Matches source system (AppSec) layout 1:1.
- Avoids join through `sla` during ingest.
- Matches PDF semantics: these are process-level facts, not separate SLA obligations.

The duplication with `sla.response_time / resolution_time` is tracked as tech debt in **MACWO-533** (Reconcile RTO/RPO between business_process and sla). The follow-up may move the source-of-truth to `sla` later if it turns out to be the right call.

### Enums — inline `enum_values`

Per the plan (Q3), enums are captured directly on the attribute via `enum_values: [...]` instead of via a separate dictionary. Examples:

- `status_lifecycle: [draft, production, archive]`
- `ics_prioritization: [key, non_key]`
- `ics_classification: [key_regulatory, key_business, financial_reporting, other]`
- `bcm_criticality: [mission_critical, business_critical, operational, supportive, do_not_recovery, not_defined]`
- `criticality_716p: [critically_important, main, other]`
- `customer_segment_impact: [mass, affluent, private, micro, small, medium, corporate, international]`

If reuse becomes needed across entity_kinds, values can be hoisted into the top-level `dictionaries` section in a follow-up without breaking downstream.

### IDs — English `snake_case`, Russian `name_ru`

Per the plan (Q4), attribute IDs are English `snake_case`, the English `name` carries a short label suitable for UI, and `name_ru` carries the Russian label from the PDF. This keeps the repo convention (existing attributes use snake_case IDs) while preserving the exact Russian labels for traceability.

## Trade-offs

### Three PDF attributes are NOT ported

To avoid duplication with existing legacy attributes:

- **PDF #9 «Домен»** is already represented by `business_process.business_domain_id`.
- **PDF #17 «Бизнес-способность»** is already represented by `business_process.business_capability_id`.
- **PDF #36 «Сотрудник-владелец»** is semantically close to the existing `business_process.business_owner_id` (whose description is «Ответственный руководитель»).

The PDF number «57» is therefore split into 54 new + 3 existing, totalling 58 attributes on `business_process` after this PR (54 new + 4 legacy).

### Two PDF dependency fields reuse an existing relation_kind

PDF #20 «Входящие зависимости» and #21 «Исходящие зависимости» are **not** exposed as new relation_kinds — `rel_process_depends_on_process` already exists in `metamodel.yaml` with the correct semantics. Instead:

- The scalar attributes `inbound_process_codes` and `outbound_process_codes` are added as `cardinality: many, data_type: string, category: integration` — these are ingest-friendly string lists.
- Downstream consumers that want the graph edge use the existing `rel_process_depends_on_process` relation.

### PDF #11 and `tier` are kept as separate attributes

`business_process.tier` (legacy) is generic criticality. PDF #11 «Критичность по 716-П» is specifically the regulatory classification. These are kept as separate attributes (`tier` and `criticality_716p`) because their semantics differ. A future PR may collapse them once business users confirm the same field.

### Harness validator is stricter than v2 contract doc

`docs/architecture/attribute_def_contract_v2.md` lists `date`, `datetime`, `urn_ref`, `url`, `external_key`, `json` as allowed `data_type`. The harness validator only whitelists `string, text, integer, number, boolean, enum, id, uri`. This PR conforms to the validator (not the doc): `date → string`, `urn_ref → id`. The `display_mode` field (which the validator doesn't check) carries the richer semantics (`date`, `entity_ref`).

### Breaking change risk — none

No fields are removed, no types are changed on existing attributes, no relation_kinds are deleted. Downstream consumers (Atlas bundle, RAG index) will see a larger `type_catalog.json` and new relations in the catalog but no breakage of existing contracts.

## Alternatives considered

1. **Split across 4 PRs by domain (risks / bcm / ops / core)** — rejected by the developer in plan Q3. Single-PR review was judged lighter than 4 separate reviews with partial state.
2. **Put BCM fields on `sla` entity_kind** — rejected per plan Q2. Would require join through sla at ingest time and doesn't match source system layout.
3. **Use external enum dictionaries** — deferred to a follow-up if reuse across entity_kinds emerges.
4. **Rename legacy `business_owner_id` to `responsible_manager_id`** — rejected. Plan explicitly forbids touching legacy.

## Consequences

### Positive

- Metamodel is now the source of truth for 54 more business_process facts.
- Downstream ingest from S1 / Archer / BCM / AppSec is a direct mapping, zero translation.
- Risk, BCM and Ops teams see their fields in the same place, reducing coordination cost.
- Regression test pins the surface for future refactors.

### Negative

- Temporary duplication of RTO/RPO between `business_process` and `sla`. Tracked in MACWO-533.
- v2 contract fields (`data_type`, `cardinality`, `required`, `category`, `display_group`, `source_expectation`, `quality_expectation`, etc.) are present only for new attributes; the 4 legacy attributes still use the minimal 3-field schema. Follow-up refactor to enrich them is not in scope for this PR.
- `display_group` as a partitioning mechanism is new for this repo — downstream UI may not yet honour it. It degrades gracefully (just a string annotation).

### Neutral

- `type_catalog.json` grows by ~54 attribute entries, ~8 relation entries — no structural change.
- No changes to `generated/` bundles required at the authoring layer; `make bundle` will pick them up automatically.

## Validation

Post-migration harness output:

```
make validate
  success=true errors=0 warnings=3
  [ontology_validation]         errors=0 warnings=0
  [ontology_lint]                errors=0 warnings=2  ← pre-existing
  [relation_catalog_validation]  errors=0 warnings=0
  [schema_validation]            errors=0 warnings=0
  [contract_validation]          errors=0 warnings=1  ← Rule 3 pre-existing

make test
  78 passed in 46.24s (76 legacy + 2 new files — conftest already registered)
```

The 3 remaining warnings are pre-existing and unrelated to this PR.

## References

- Epic: MACWO-525 «PDF 1.0 → metamodel attributes»
- Source PDF (YAML-изlocated): `~/msc_1/meta/глоссарий и атрибуты/атрибутивный_состав.yaml` → `contexts.business_context.entities[0].attributes`
- Plan: `~/msc_1/meta/глоссарий и атрибуты/contribution_plan.md` §3 «PR-1: business_process»
- v2 contracts: `docs/architecture/attribute_def_contract_v2.md`, `docs/architecture/relation_kind_contract_v2.md`
- Follow-ups: MACWO-533 (reconcile RTO/RPO), MACWO-534 (expand stub entity_kinds)
