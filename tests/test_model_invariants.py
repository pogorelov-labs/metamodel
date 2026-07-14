"""Model invariants (MACWO-670): inverse-pair cardinality mirroring + dedup guards.

These tests protect two properties of the canonical model that the 2026-07
review had to repair by hand, so they cannot silently regress:

1. **Inverse cardinality mirroring.** Every *linked* inverse pair in
   ``relation_catalog.yaml`` must have mirror-image cardinalities. For a
   relation ``R (A->B, sc, tc)`` and its inverse ``R' (B->A, sc', tc')``,
   the same real-world side must carry the same cardinality in both
   directions, i.e. ``sc == tc'`` **and** ``tc == sc'``. A copy-paste that
   forgets to flip the cardinalities breaks this and corrupts downstream
   traversal/impact semantics (e.g. ``it_system(many)->api(one)`` reads
   "many systems expose one API", the inverse of the truth).

2. **Duplicate removal stays done.** The two core-only legacy duplicate
   relations removed in MACWO-670 must not reappear, and their canonical
   catalog-era supersessors must remain.

``KNOWN_UNMIRRORED_CARDINALITY_PAIRS`` is the shrinking allow-list of pairs
still awaiting a fix — empty, because MACWO-670 corrected all 11 the review
found. If you *intentionally* add a non-mirrored pair, list it here with a
comment justifying it; if you fix one, remove it (a stale entry — one that is
actually mirrored now — fails ``test_known_unmirrored_entries_are_not_stale``).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
METAMODEL_PATH = ROOT / "model" / "metamodel.yaml"
RELATION_CATALOG_PATH = ROOT / "model" / "relation_catalog.yaml"

# Unordered {id, id} pairs whose catalog cardinalities are still NOT mirror
# images. Empty: MACWO-670 fixed all 11 found by the 2026-07 model review.
KNOWN_UNMIRRORED_CARDINALITY_PAIRS: frozenset[frozenset[str]] = frozenset()

# Core-only legacy duplicate relations removed in MACWO-670, mapped to the
# canonical catalog-era relation that supersedes each. Guard: the removed ids
# stay gone (both files); the canonical ids stay present.
KNOWN_DUPLICATE_RELATION_FAMILIES: dict[str, str] = {
    "rel_data_product_contains_data_object": "rel_data_product_contains_object",
    "rel_org_unit_creates_product": "rel_org_unit_creates_bank_product",
}


@pytest.fixture(scope="module")
def metamodel():
    with METAMODEL_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def relation_catalog():
    with RELATION_CATALOG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def catalog_relations(relation_catalog):
    """Map of relation id -> relation dict from the catalog overlay."""
    return {r["id"]: r for r in relation_catalog["relation_catalog"]["relations"]}


def _iter_linked_inverse_pairs(catalog_relations):
    """Yield each catalog inverse pair once as ``(rel_a, rel_b)``.

    A pair is included when a relation names an ``inverse_relation_id`` that is
    also present in the catalog. Self-inverse relations are skipped (no
    meaningful cardinality mirror). Ordering within the pair is by id so the
    two directions are visited exactly once.
    """
    seen: set[frozenset[str]] = set()
    for rid, rel in catalog_relations.items():
        inverse_id = rel.get("inverse_relation_id")
        if not inverse_id or inverse_id not in catalog_relations:
            continue
        key = frozenset((rid, inverse_id))
        if len(key) < 2 or key in seen:  # skip self-inverse and already-seen
            continue
        seen.add(key)
        a_id, b_id = sorted((rid, inverse_id))
        yield catalog_relations[a_id], catalog_relations[b_id]


def _is_cardinality_mirror(a, b) -> bool:
    return (
        a.get("source_cardinality") == b.get("target_cardinality")
        and a.get("target_cardinality") == b.get("source_cardinality")
    )


def _describe(rel) -> str:
    return (
        f"{rel['id']} ({rel.get('from_kind')}:{rel.get('source_cardinality')} -> "
        f"{rel.get('to_kind')}:{rel.get('target_cardinality')})"
    )


def test_catalog_has_linked_inverse_pairs(catalog_relations):
    """Guard against a vacuous mirror test (e.g. if the catalog shape changes)."""
    pairs = list(_iter_linked_inverse_pairs(catalog_relations))
    assert len(pairs) >= 40, f"expected many linked inverse pairs, found {len(pairs)}"


def test_inverse_pairs_mirror_cardinality(catalog_relations):
    """Every linked inverse pair must mirror, except entries in the allow-list."""
    violations: list[str] = []
    for a, b in _iter_linked_inverse_pairs(catalog_relations):
        if _is_cardinality_mirror(a, b):
            continue
        if frozenset((a["id"], b["id"])) in KNOWN_UNMIRRORED_CARDINALITY_PAIRS:
            continue
        violations.append(f"{_describe(a)}  <!=>  {_describe(b)}")

    assert not violations, (
        "Inverse pairs with non-mirrored cardinalities "
        "(source/target must be swapped between a relation and its inverse):\n  "
        + "\n  ".join(sorted(violations))
    )


def test_known_unmirrored_entries_are_not_stale(catalog_relations):
    """A pair in the allow-list that is gone or now mirrored must be removed from it."""
    stale: list[str] = []
    for pair in KNOWN_UNMIRRORED_CARDINALITY_PAIRS:
        ids = tuple(pair)
        missing = [i for i in ids if i not in catalog_relations]
        if missing:
            stale.append(f"{set(ids)}: no longer in catalog ({missing})")
            continue
        a, b = catalog_relations[ids[0]], catalog_relations[ids[1]]
        if _is_cardinality_mirror(a, b):
            stale.append(f"{set(ids)}: now mirrored")

    assert not stale, (
        "Stale KNOWN_UNMIRRORED_CARDINALITY_PAIRS entries (remove them):\n  "
        + "\n  ".join(stale)
    )


def test_removed_duplicate_relations_stay_removed(metamodel, catalog_relations):
    """The MACWO-670 legacy duplicates stay gone; their supersessors stay present."""
    mm_ids = {r["id"] for r in metamodel["relation_kinds"]}
    for removed, canonical in KNOWN_DUPLICATE_RELATION_FAMILIES.items():
        assert removed not in mm_ids, (
            f"{removed} is a removed legacy duplicate — do not re-add it to "
            f"metamodel.yaml; use the canonical {canonical}"
        )
        assert removed not in catalog_relations, (
            f"{removed} is a removed legacy duplicate — do not add it to "
            f"relation_catalog.yaml"
        )
        assert canonical in mm_ids, (
            f"canonical relation {canonical} (supersedes {removed}) is missing "
            f"from metamodel.yaml"
        )
