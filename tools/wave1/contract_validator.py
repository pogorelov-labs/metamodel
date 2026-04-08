"""mm/rc contract validator (Phase 5, MACWO-521).

Enforces the two-layer contract between ``model/metamodel.yaml`` (the core
ontology) and ``model/relation_catalog.yaml`` (the profile overlay):

- **Rule 1**: every relation in the catalog **must** have a matching
  ``relation_kind`` in ``metamodel.yaml`` (looked up by ``id``).
- **Rule 2**: ``from_kind``, ``to_kind``, ``category`` and ``direction``
  on a catalog relation **must** match the corresponding mm relation_kind.
- **Rule 3**: it is **allowed** for a relation_kind to live in mm without
  a catalog overlay — the catalog only enriches relations that are part of
  a profile (e.g. ``atlas_mvp``). Such core-only relations surface as a
  warning, not an error, so the team has visibility into how many remain.

The validator additionally re-checks that all ``from_kind`` / ``to_kind``
references resolve to a real entity_kind (a structural sanity check that
also catches accidental typos when promoting catalog relations into mm).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

import yaml


@dataclass(frozen=True)
class ContractMessage:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ContractResult:
    errors: Tuple[ContractMessage, ...]
    warnings: Tuple[ContractMessage, ...]

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)


def validate_contract(
    metamodel_path: Path | str,
    relation_catalog_path: Path | str,
) -> ContractResult:
    """Run all contract checks against on-disk YAML files."""

    mm_data = yaml.safe_load(Path(metamodel_path).read_text(encoding="utf-8"))
    rc_data = yaml.safe_load(Path(relation_catalog_path).read_text(encoding="utf-8"))

    entity_ids = {e["id"] for e in mm_data.get("entity_kinds", [])}
    mm_relations = {r["id"]: r for r in mm_data.get("relation_kinds", [])}
    rc_relations = {
        r["id"]: r
        for r in rc_data.get("relation_catalog", {}).get("relations", [])
    }

    errors: list[ContractMessage] = []
    warnings: list[ContractMessage] = []

    # Rule 1: every catalog relation has a matching mm relation_kind
    for rid, rc_rel in sorted(rc_relations.items()):
        if rid not in mm_relations:
            errors.append(
                ContractMessage(
                    code="rule1_missing_in_mm",
                    path=f"relation_catalog.relations.{rid}",
                    message=(
                        f"relation '{rid}' is present in relation_catalog.yaml "
                        "but has no relation_kind in metamodel.yaml (Rule 1)."
                    ),
                )
            )

    # Rule 2: from_kind/to_kind/category/direction match mm relation_kind
    for rid in sorted(rc_relations.keys() & mm_relations.keys()):
        mm_rel = mm_relations[rid]
        rc_rel = rc_relations[rid]
        for field in ("from_kind", "to_kind", "category", "direction"):
            if mm_rel.get(field) != rc_rel.get(field):
                errors.append(
                    ContractMessage(
                        code=f"rule2_{field}_mismatch",
                        path=f"relation_catalog.relations.{rid}.{field}",
                        message=(
                            f"{field} mismatch: mm.yaml='{mm_rel.get(field)}' "
                            f"vs rc.yaml='{rc_rel.get(field)}' (Rule 2)."
                        ),
                    )
                )

    # Rule 3 (warning only, single summary): mm relations without a catalog
    # overlay. Summarised so the harness output stays compact even when
    # dozens of core relations are not part of any profile.
    mm_only = sorted(mm_relations.keys() - rc_relations.keys())
    if mm_only:
        sample = ", ".join(mm_only[:5])
        suffix = "" if len(mm_only) <= 5 else f", ... (+{len(mm_only) - 5} more)"
        warnings.append(
            ContractMessage(
                code="rule3_core_only_relations",
                path="metamodel.relation_kinds",
                message=(
                    f"{len(mm_only)} relation_kind(s) have no relation_catalog "
                    f"overlay (allowed under Rule 3): {sample}{suffix}. "
                    "Inspect with `python -m tools.wave1.contract_validator`."
                ),
            )
        )

    # Structural sanity: from/to references resolve to real entity_kinds
    for source_name, source_map in (
        ("metamodel.relation_kinds", mm_relations),
        ("relation_catalog.relations", rc_relations),
    ):
        for rid, rel in sorted(source_map.items()):
            for field in ("from_kind", "to_kind"):
                value = rel.get(field)
                if value is None:
                    errors.append(
                        ContractMessage(
                            code="missing_endpoint",
                            path=f"{source_name}.{rid}.{field}",
                            message=f"{field} is missing on '{rid}'.",
                        )
                    )
                elif value not in entity_ids:
                    errors.append(
                        ContractMessage(
                            code="dangling_endpoint",
                            path=f"{source_name}.{rid}.{field}",
                            message=(
                                f"{field}='{value}' on '{rid}' does not match "
                                "any entity_kind."
                            ),
                        )
                    )

    return ContractResult(errors=tuple(errors), warnings=tuple(warnings))


def main(argv: Iterable[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Validate mm/rc two-layer contract")
    parser.add_argument(
        "metamodel_path",
        type=Path,
        nargs="?",
        default=Path("model/metamodel.yaml"),
    )
    parser.add_argument(
        "--relation-catalog-path",
        type=Path,
        default=Path("model/relation_catalog.yaml"),
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only the summary line, not individual messages.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    result = validate_contract(args.metamodel_path, args.relation_catalog_path)
    print(
        f"contract_validation errors={result.error_count} "
        f"warnings={result.warning_count}"
    )
    if not args.summary_only:
        for error in result.errors:
            print(f"  ERROR [{error.code}] {error.path}: {error.message}")
        for warning in result.warnings[:20]:
            print(f"  WARN  [{warning.code}] {warning.path}: {warning.message}")
        if len(result.warnings) > 20:
            print(f"  ... +{len(result.warnings) - 20} more warnings")
    return 0 if result.error_count == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
