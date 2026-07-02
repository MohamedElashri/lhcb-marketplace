#!/usr/bin/env python3
"""Statically validate a modern Run 3 FunTuple configuration."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

import yaml

LEGACY_MARKERS = (
    "DecayTreeTuple",
    "TupleTool",
    "addBranches",
    "LoKi::Hybrid",
    "DaVinci()",
)


def fail(message: str) -> None:
    raise SystemExit(f"error: {message}")


def mapping_node(tree: ast.Module, name: str) -> ast.Dict | None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            continue
        return node.value if isinstance(node.value, ast.Dict) else None
    return None


def validate_module(path: Path) -> tuple[dict[str, str], set[str]]:
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
    except (OSError, SyntaxError) as error:
        fail(f"{path}: {error}")
    found = [marker for marker in LEGACY_MARKERS if marker in text]
    if found:
        fail(f"{path}: legacy tuple markers found: {', '.join(found)}")
    required_text = (
        "FunTuple_Particles",
        "fields=",
        "variables=",
        "tuple_name=",
        "inputs=",
        "make_config",
    )
    missing = [marker for marker in required_text if marker not in text]
    if missing:
        fail(f"{path}: missing FunTuple structure: {', '.join(missing)}")

    fields_node = mapping_node(tree, "fields")
    if fields_node is None:
        fail(f"{path}: define a non-empty literal fields mapping")
    try:
        fields = ast.literal_eval(fields_node)
    except (ValueError, TypeError):
        fail(f"{path}: fields must be a literal mapping")
    if not isinstance(fields, dict) or not fields:
        fail(f"{path}: define a non-empty literal fields mapping")
    if not all(
        isinstance(key, str) and isinstance(value, str) for key, value in fields.items()
    ):
        fail(f"{path}: fields must map string names to string descriptors")
    if any(descriptor.count("^") > 1 for descriptor in fields.values()):
        fail(f"{path}: each field descriptor may select at most one particle")
    if len(fields) > 1 and not any("^" in descriptor for descriptor in fields.values()):
        fail(f"{path}: daughter fields must select particles with a caret")

    variables_node = mapping_node(tree, "variables")
    if variables_node is None:
        fail(f"{path}: define a literal variables mapping")
    try:
        variable_fields = {
            ast.literal_eval(key) for key in variables_node.keys if key is not None
        }
    except (ValueError, TypeError):
        fail(f"{path}: variable field names must be literal strings")
    if not all(isinstance(key, str) for key in variable_fields):
        fail(f"{path}: variable field names must be strings")
    unknown = variable_fields - set(fields)
    if unknown:
        fail(
            f"{path}: variables reference unknown fields: {', '.join(sorted(unknown))}"
        )
    return fields, variable_fields


def validate_options(path: Path) -> dict[str, Any]:
    try:
        options = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        fail(f"{path}: {error}")
    if not isinstance(options, dict):
        fail(f"{path}: options must be a YAML mapping")
    if not isinstance(options.get("ntuple_file"), str) or not options["ntuple_file"]:
        fail(f"{path}: ntuple_file must be a non-empty string")
    return options


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("module", type=Path)
    parser.add_argument("options", type=Path)
    args = parser.parse_args()

    fields, variable_fields = validate_module(args.module)
    options = validate_options(args.options)
    print(
        json.dumps(
            {
                "module": str(args.module),
                "fields": sorted(fields),
                "variable_fields": sorted(variable_fields),
                "ntuple_file": options["ntuple_file"],
                "status": (
                    "static validation passed; runtime verification still required"
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
