"""Shared helpers for repository validation scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "schemas"


class CheckError(RuntimeError):
    """A repository validation failure."""


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CheckError(f"{display_path(path)}: {error}") from error


def validate_json(instance: Any, schema_name: str, source: Path) -> None:
    schema = load_json(SCHEMAS / schema_name)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        details = []
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            details.append(f"{display_path(source)}:{location}: {error.message}")
        raise CheckError("\n".join(details))


def read_skill_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise CheckError(f"{display_path(path)}: missing opening YAML delimiter")
    try:
        closing = lines.index("---", 1)
    except ValueError as error:
        raise CheckError(
            f"{display_path(path)}: missing closing YAML delimiter"
        ) from error
    try:
        value = yaml.safe_load("\n".join(lines[1:closing]))
    except yaml.YAMLError as error:
        raise CheckError(f"{display_path(path)}: invalid YAML: {error}") from error
    if not isinstance(value, dict):
        raise CheckError(f"{display_path(path)}: frontmatter must be a mapping")
    return value


def relative_files(pattern: str) -> list[Path]:
    return sorted(ROOT.glob(pattern), key=lambda path: path.as_posix())
