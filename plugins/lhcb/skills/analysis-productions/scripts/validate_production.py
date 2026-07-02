#!/usr/bin/env python3
"""Statically validate a modern Run 3 Analysis Production example."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any

import yaml

APPLICATION = re.compile(
    r"^[A-Za-z][A-Za-z0-9]*/v\d+r\d+(?:p\d+)?(?:@[A-Za-z0-9_.+\-]+)?$"
)
ENTRYPOINT = re.compile(
    r"^(?P<module>[A-Za-z_][A-Za-z0-9_.]*):(?P<function>[A-Za-z_][A-Za-z0-9_]*)$"
)
RUN3_PROCESSES = {"Hlt2", "Spruce", "TurboSpruce", "TurboPass"}
LEGACY_MARKERS = ("gaudirun.py", "DaVinci()", "UserAlgorithms", "DecayTreeTuple")


def fail(message: str) -> None:
    raise SystemExit(f"error: {message}")


def mapping(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{name} must be a mapping")
    return value


def validate_entrypoint(root: Path, value: object) -> tuple[str, str]:
    if not isinstance(value, str) or not (match := ENTRYPOINT.fullmatch(value)):
        fail("defaults.options.entrypoint must be a module:function string")
    module = match.group("module")
    function = match.group("function")
    module_path = root / f"{module.replace('.', '/')}.py"
    if not module_path.is_file():
        fail(f"entrypoint module is absent: {module_path}")
    text = module_path.read_text(encoding="utf-8")
    legacy = [marker for marker in LEGACY_MARKERS if marker in text]
    if legacy:
        fail(f"{module_path}: legacy markers found: {', '.join(legacy)}")
    try:
        tree = ast.parse(text, filename=str(module_path))
    except SyntaxError as error:
        fail(f"{module_path}: {error}")
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    if function not in functions:
        fail(f"{module_path}: function {function!r} is absent")
    return str(module_path), function


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("production", type=Path)
    args = parser.parse_args()

    info_path = args.production / "info.yaml"
    try:
        text = info_path.read_text(encoding="utf-8")
        if "{%" in text or "{{" in text:
            fail("portable validation does not render Jinja; run lb-ap render")
        data = yaml.safe_load(text)
    except (OSError, yaml.YAMLError) as error:
        fail(f"{info_path}: {error}")
    data = mapping(data, str(info_path))
    defaults = mapping(data.get("defaults"), "defaults")

    application = defaults.get("application")
    if not isinstance(application, str) or not APPLICATION.fullmatch(application):
        fail("defaults.application must pin an exact Application/vXrY[@platform]")
    output = defaults.get("output")
    if not isinstance(output, str) or not output.upper().endswith(".ROOT"):
        fail("defaults.output must name a ROOT output")
    options = mapping(defaults.get("options"), "defaults.options")
    module_path, function = validate_entrypoint(
        args.production.parent, options.get("entrypoint")
    )
    extra = mapping(options.get("extra_options"), "defaults.options.extra_options")
    required = {
        "input_type",
        "input_process",
        "simulation",
        "data_type",
    }
    missing = sorted(required - extra.keys())
    if missing:
        fail(f"defaults.options.extra_options is missing: {', '.join(missing)}")
    if extra["input_process"] not in RUN3_PROCESSES:
        fail("input_process must be a current Run 3 persisted process")
    if not isinstance(extra["simulation"], bool):
        fail("simulation must be true or false")
    if "input_files" in extra:
        fail("put production inputs under each job, not extra_options.input_files")
    if extra["simulation"]:
        if not (extra.get("dddb_tag") and extra.get("conddb_tag")):
            fail("simulation requires source-backed dddb_tag and conddb_tag")
    elif not (extra.get("geometry_version") and extra.get("conditions_version")):
        fail("data requires geometry_version and conditions_version")
    inform = defaults.get("inform")
    if (
        not isinstance(inform, list)
        or not inform
        or not all(isinstance(value, str) and value for value in inform)
    ):
        fail("defaults.inform must list at least one CERN username")

    jobs: list[dict[str, object]] = []
    for name, raw_job in data.items():
        if name == "defaults":
            continue
        job = mapping(raw_job, f"job {name}")
        input_data = mapping(job.get("input"), f"job {name}.input")
        sources = [
            key
            for key in ("bk_query", "job_name", "transform_ids")
            if key in input_data
        ]
        if len(sources) != 1:
            fail(f"job {name}.input must define exactly one supported input source")
        source = sources[0]
        if source == "bk_query":
            query = input_data[source]
            if not isinstance(query, str) or not query.startswith("/"):
                fail(f"job {name}.input.bk_query must be an absolute Bookkeeping path")
        jobs.append({"name": name, "input_source": source})
    if not jobs:
        fail("at least one production job is required")

    print(
        json.dumps(
            {
                "production": args.production.name,
                "application": application,
                "entrypoint": options["entrypoint"],
                "entrypoint_file": module_path,
                "entrypoint_function": function,
                "output": output,
                "jobs": jobs,
                "status": (
                    "portable validation passed; run the version-supported "
                    "lb-ap dry-run and test commands"
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
