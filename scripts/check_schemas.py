#!/usr/bin/env python3
"""Validate the repository's JSON Schema documents."""

from __future__ import annotations

from _lib import SCHEMAS, CheckError, load_json
from jsonschema import Draft202012Validator


def main() -> None:
    schema_paths = sorted(SCHEMAS.glob("*.schema.json"))
    if not schema_paths:
        raise CheckError("no schemas found")
    for path in schema_paths:
        Draft202012Validator.check_schema(load_json(path))
    print(f"OK: {len(schema_paths)} JSON schemas are valid")


if __name__ == "__main__":
    try:
        main()
    except CheckError as error:
        raise SystemExit(f"error: {error}") from error
