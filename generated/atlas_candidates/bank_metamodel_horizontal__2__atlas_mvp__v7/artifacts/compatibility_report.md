# Wave 1 Compatibility Report

## Bundle Identity
- model_name: `bank_metamodel_horizontal`
- model_version: `2`
- bank_code: `BANK`
- profile: `atlas_mvp`

## Artifact Inventory
- `compatibility_report` (generated) → `artifacts/compatibility_report.md`
- `metamodel_snapshot` (generated) → `artifacts/metamodel_snapshot.json`
- `relation_catalog` (generated) → `artifacts/relation_catalog.json`
- `search_aliases` (generated) → `artifacts/search_aliases.json`
- `type_catalog` (generated) → `artifacts/type_catalog.json`

## Artifact Summary Counts
- entity_kinds: `49`
- attributes: `310`
- relations: `188`
- qualifiers: `11`
- aliases: `132`
- unresolved_aliases: `0`

## Validation/Compatibility Status
- snapshot_type_kind_count_match: **PASS** (snapshot=49, type_catalog=49)
- relation_catalog_non_empty: **PASS** (relation_count=188)
- search_aliases_non_empty: **PASS** (alias_count=132)
- relation_inverse_integrity: **PASS** (validated from generated relation_catalog)

## Import-Relevant Notes
- No compatibility warnings detected.
