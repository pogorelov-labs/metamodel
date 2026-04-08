"""JSON-Schema validation for ``model/metamodel.yaml``.

The repository ships a JSON Schema (Draft 2020-12) at
``model/schema/metamodel.schema.yaml`` that describes the canonical shape of
``metamodel.yaml`` (meta, dictionaries, entity_kinds, relation_kinds). This
module wraps ``jsonschema.Draft202012Validator`` so the harness can run it as
a dedicated stage and so CI can fail when the canonical file drifts away
from its declared schema.

A separate stage (instead of folding the checks into ``validator.py``) keeps
the responsibilities clean: dataclass validation lives in ``validator.py``,
linting in ``lint.py``, schema validation here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

import yaml

DEFAULT_SCHEMA_PATH = Path("model/schema/metamodel.schema.yaml")


@dataclass(frozen=True)
class SchemaValidationMessage:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class SchemaValidationResult:
    errors: Tuple[SchemaValidationMessage, ...]
    warnings: Tuple[SchemaValidationMessage, ...]

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)


def validate_metamodel_schema(
    metamodel_path: Path | str,
    *,
    schema_path: Path | str = DEFAULT_SCHEMA_PATH,
) -> SchemaValidationResult:
    """Validate ``metamodel.yaml`` against its canonical JSON Schema."""

    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - environment guard
        raise RuntimeError(
            "jsonschema is required for schema validation. "
            "Install it with `pip install jsonschema`."
        ) from exc

    metamodel_path = Path(metamodel_path)
    schema_path = Path(schema_path)

    metamodel_data = yaml.safe_load(metamodel_path.read_text(encoding="utf-8"))
    schema_data = yaml.safe_load(schema_path.read_text(encoding="utf-8"))

    validator = jsonschema.Draft202012Validator(schema_data)
    raw_errors = sorted(
        validator.iter_errors(metamodel_data),
        key=lambda err: (list(err.absolute_path), err.message),
    )

    errors = tuple(_render(error) for error in raw_errors)
    return SchemaValidationResult(errors=errors, warnings=())


def _render(error) -> SchemaValidationMessage:
    path = "/".join(str(part) for part in error.absolute_path)
    return SchemaValidationMessage(
        code="schema_violation",
        path=path or "<root>",
        message=error.message,
    )


def main(argv: Iterable[str] | None = None) -> int:
    """CLI entrypoint: validate metamodel.yaml and print all violations."""

    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Validate metamodel.yaml against its JSON Schema."
    )
    parser.add_argument(
        "metamodel_path",
        type=Path,
        nargs="?",
        default=Path("model/metamodel.yaml"),
    )
    parser.add_argument(
        "--schema-path",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    result = validate_metamodel_schema(
        args.metamodel_path, schema_path=args.schema_path
    )
    print(
        f"schema_validation errors={result.error_count} "
        f"warnings={result.warning_count}"
    )
    for error in result.errors:
        print(f"  ERROR [{error.code}] {error.path}: {error.message}")
    return 0 if result.error_count == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
