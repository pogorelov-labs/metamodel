# ADR — MACWO-527: Port PDF 1.0 it_system attributes into metamodel.yaml

- **Status:** accepted
- **Date:** 2026-04-10
- **Ticket:** MACWO-527 (sub-issue of MACWO-525)
- **Model version:** new attributes carry `introduced_in: '2.1'`

## Context

PDF «Атрибутивный состав 1.0» describes **41 attributes** for `it_system`, matching **SimpleOne CSP** 1:1 at the field-name level (Name, FullName, AltName, Description, Availability Tier, RTO BCP, all PCI-* fields, etc.). Downstream ingest from SimpleOne is blocked without these fields in the upstream metamodel.

Prior to this PR `it_system` had only 4 attributes:
- `org_unit_id`, `business_capability_id`, `business_domain_id`, `tier`

## Decision

Port all 41 PDF `it_system` attributes into `model/metamodel.yaml` in v2 contract form, plus 6 paired `relation_kinds` + `relation_catalog.yaml` overlays for the reference fields (owners, architect, legal entity).

### Attribute groups (41 new + 4 legacy = 45 total)

| display_group | # | Fields |
|---|---:|---|
| `identity` | 6 | name_short, full_name, full_name_eng, alt_name, description_text, description_eng |
| `criticality` | 6 | critical_infrastructure_level, availability_tier, mb_criticality, application_type, application_operational_time, target_state |
| `ownership` | 6 | owner_team_id, business_owner_employee_id, business_owner_delegate_id, it_owner_employee_id, enterprise_architect_id, legal_entity_org_unit_id |
| `bcp` | 5 | rto_bcp, rpo_bcp, availability_percent, availability_class, integrity_class |
| `data_classification` | 6 | data_classification_level, personal_data, bank_secret, commercial_secret, insider_information, other_confidential_information |
| `pci` | 7 | audit_pci_dss, applicability_pci_dss, system_interacts_with_pci_dss, card_personalization, payment_card_information, pci_raiffeisen, pci_other_bank |
| `exposure` | 2 | internet_facing, infosec_solution |
| `support` | 3 | support_group, support_expert_1_id, support_expert_2_id |
| **Total** | **41** | |

### PCI and data_classification carry `sensitivity: confidential`

All 13 security-sensitive fields (7 PCI + 6 data classification) are marked with `sensitivity: confidential` in the attribute metadata. This is the v2 contract hint for runtime masking and access control. Downstream Atlas projection can honor this marker to hide values from unprivileged users.

### 6 new relation_kinds for ownership refs

| relation_kind | from | to | Purpose |
|---|---|---|---|
| `rel_it_system_owned_by_team` | it_system | team | Owner Team |
| `rel_it_system_business_owned_by_employee` | it_system | employee | Business owner |
| `rel_it_system_business_owner_delegate_employee` | it_system | employee | Business owner delegate |
| `rel_it_system_it_owned_by_employee` | it_system | employee | IT owner |
| `rel_it_system_architected_by_employee` | it_system | employee | Enterprise architect |
| `rel_it_system_legal_entity_org_unit` | it_system | organizational_unit | Legal entity |

Support expert 1/2 are kept as scalar `id` attributes only — no separate relation_kind because `rel_it_system_owned_by_team` already models operational ownership adequately and a separate "supports" relation would add graph noise without improving traversal.

### No legacy field removals

Legacy `org_unit_id`, `business_capability_id`, `business_domain_id`, `tier` remain untouched. They're coarser-grained associations and don't conflict with the new detailed attributes.

### Harness validator compliance

Same as PR-1: `data_type` must be in `{string, text, integer, number, boolean, enum, id, uri}`. `urn_ref → id`, `date → string` etc.

## Consequences

- +41 attributes on `it_system`, fully compatible with SimpleOne ingest
- +6 relation_kinds + 6 catalog overlays
- Security fields flagged `sensitivity: confidential` for runtime masking
- 60 parametrised regression tests pin the surface
- `make validate` → 0 errors, 3 pre-existing warnings
- `make test` → 214 passed (154 legacy + 60 new)

## References

- Epic: MACWO-525
- Source: `~/msc_1/meta/глоссарий и атрибуты/атрибутивный_состав.yaml` → `contexts.solution_component_context.entities[0].attributes`
