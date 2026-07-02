#!/usr/bin/env python3
"""Statically validate the structure of a modern Run 3 DaVinci job."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

import yaml

LEGACY_MARKERS = (
    "DaVinci()",
    "UserAlgorithms",
    "TupleFile",
    "gaudirun.py",
    "DecayTreeTuple",
)
REQUIRED_OPTIONS = (
    "input_files",
    "input_type",
    "evt_max",
    "input_process",
    "print_freq",
    "simulation",
)


def fail(message: str) -> None:
    raise SystemExit(f"error: {message}")


def load_options(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        fail(f"{path}: {error}")
    if not isinstance(value, dict):
        fail(f"{path}: options must be a YAML mapping")
    missing = [key for key in REQUIRED_OPTIONS if key not in value]
    if missing:
        fail(f"{path}: missing options: {', '.join(missing)}")
    if not isinstance(value["input_files"], list) or not value["input_files"]:
        fail(f"{path}: input_files must be a non-empty list")
    if not all(isinstance(item, str) and item for item in value["input_files"]):
        fail(f"{path}: every input file must be a non-empty string")
    if not isinstance(value["simulation"], bool):
        fail(f"{path}: simulation must be true or false")
    if not isinstance(value["evt_max"], int) or value["evt_max"] == 0:
        fail(f"{path}: evt_max must be a non-zero integer")
    return value


def validate_python(path: Path) -> ast.Module:
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
    except (OSError, SyntaxError) as error:
        fail(f"{path}: {error}")
    found = [marker for marker in LEGACY_MARKERS if marker in text]
    if found:
        fail(f"{path}: legacy Run 1/2 markers found: {', '.join(found)}")

    imports_options = False
    imports_make_config = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "DaVinci":
            names = {alias.name for alias in node.names}
            imports_options |= "Options" in names
            imports_make_config |= "make_config" in names
    if not imports_options or not imports_make_config:
        fail(f"{path}: import Options and make_config from DaVinci")

    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    valid_functions = []
    for function in functions:
        if not function.args.args:
            continue
        returns_make_config = any(
            isinstance(node, ast.Return)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "make_config"
            for node in ast.walk(function)
        )
        if returns_make_config:
            valid_functions.append(function.name)
    if not valid_functions:
        fail(f"{path}: define a function taking options and returning make_config(...)")
    return tree


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("module", type=Path)
    parser.add_argument("options", type=Path)
    args = parser.parse_args()

    tree = validate_python(args.module)
    options = load_options(args.options)
    functions = [
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.args.args
    ]
    result = {
        "module": str(args.module),
        "options": str(args.options),
        "functions": functions,
        "input_files": len(options["input_files"]),
        "input_process": options["input_process"],
        "simulation": options["simulation"],
        "status": "static validation passed; runtime verification still required",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
