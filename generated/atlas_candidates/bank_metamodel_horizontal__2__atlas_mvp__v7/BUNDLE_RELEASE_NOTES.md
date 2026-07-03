# Atlas candidate bundle — release notes

- Version: `2` (bundle id `bank_metamodel_horizontal__2__atlas_mvp__v7`)
- Profile: `atlas_mvp`
- Source ontology: `model/metamodel.yaml`
- Source relation catalog: `model/relation_catalog.yaml`

## Summary counts

- entity_kinds: `49`
- attributes: `310`
- relations (profile overlay): `188`
- qualifiers: `11`
- aliases: `132` (unresolved: `0`)

## Delta vs. `…__v6` (last promoted bundle)

This bundle cuts the accumulated, previously-unpromoted delta on top of `v6`
(which was pinned in `rbank-atlas` at the MACWO-528 state: 47 kinds / 171 relations).

New entity_kinds (+2):

- `event` — MACWO-530 (5 attributes, 4 relations to process / system / data_product / incident)
- `sensitivity_level` — MACWO-531 (6 attributes, 3 governance relations)

Enriched entity_kinds:

- `business_capability` — MACWO-529: +18 attributes ported from PDF 1.0 (incl. RBI `code_rbi` / `name_rbi`)

Relation dedupe carried in the same head:

- MACWO-528 final review pass (#57) — dropped same-direction orphan relations duplicating inverse pairs

## Compatibility

All generated checks PASS (see `artifacts/compatibility_report.md`):
snapshot↔type_catalog kind count match, relation inverse integrity, non-empty
catalogs, 0 unresolved aliases. Deterministic build verified
(`make determinism`, epoch-zeroed timestamps).

## Artifact inventory

- `bundle_manifest.json`
- `artifacts/metamodel_snapshot.json`
- `artifacts/type_catalog.json`
- `artifacts/relation_catalog.json`
- `artifacts/search_aliases.json`
- `artifacts/compatibility_report.md`

Earlier bundle ids remain immutable and unchanged.
