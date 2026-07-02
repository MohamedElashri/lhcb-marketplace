#!/usr/bin/env python3
"""Validate an auditable LHCb Run 3 analysis specification."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

APPLICATION = re.compile(r"^[A-Za-z][A-Za-z0-9]*/v\d+r\d+(?:p\d+)?$")
USE_CASES = {"measurement", "efficiency", "control-study", "validation-study"}
DECISION_STATES = {"open", "resolved", "deferred"}


def fail(message: str) -> None:
    raise SystemExit(f"error: {message}")


def mapping(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{name} must be a mapping")
    return value


def nonempty_list(value: object, name: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        fail(f"{name} must be a non-empty list")
    return value


def text(data: dict[str, Any], key: str, section: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(f"{section}.{key} must be a non-empty string")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    args = parser.parse_args()
    try:
        spec = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        fail(f"{args.spec}: {error}")
    spec = mapping(spec, str(args.spec))
    if spec.get("schema_version") != 1:
        fail("schema_version must be 1")

    analysis = mapping(spec.get("analysis"), "analysis")
    text(analysis, "id", "analysis")
    if analysis.get("era") != "run3":
        fail("analysis.era must be run3")
    if analysis.get("use_case") not in USE_CASES:
        fail("analysis.use_case is invalid")
    text(analysis, "objective", "analysis")
    if analysis.get("status") not in {"draft", "execution-ready", "complete"}:
        fail("analysis.status is invalid")

    physics = mapping(spec.get("physics"), "physics")
    text(physics, "subject", "physics")
    nonempty_list(physics.get("observables"), "physics.observables")

    datasets = nonempty_list(spec.get("datasets"), "datasets")
    dataset_ids: set[str] = set()
    for index, raw in enumerate(datasets):
        dataset = mapping(raw, f"datasets[{index}]")
        identifier = text(dataset, "id", f"datasets[{index}]")
        if identifier in dataset_ids:
            fail(f"duplicate dataset id: {identifier}")
        dataset_ids.add(identifier)
        if dataset.get("kind") not in {"data", "simulation"}:
            fail(f"datasets[{index}].kind must be data or simulation")
        query = text(dataset, "bookkeeping_query", f"datasets[{index}]")
        if not query.startswith(("/", "evt+std://")):
            fail(
                f"datasets[{index}].bookkeeping_query must be an absolute "
                "path or Bookkeeping browser URI"
            )
        for key in ("role", "campaign", "polarity", "input_process"):
            text(dataset, key, f"datasets[{index}]")
        source = text(dataset, "source", f"datasets[{index}]")
        if not source.startswith(("https://", "cern:")):
            fail(f"datasets[{index}].source must be explicit")
        verified_at = text(dataset, "verified_at", f"datasets[{index}]")
        try:
            date.fromisoformat(verified_at)
        except ValueError:
            fail(f"datasets[{index}].verified_at must be an ISO date")

    software = mapping(spec.get("software"), "software")
    application = text(software, "application", "software")
    if not APPLICATION.fullmatch(application):
        fail("software.application must pin an exact Application/vXrY")
    text(software, "platform", "software")
    text(software, "entrypoint", "software")

    selection = mapping(spec.get("selection"), "selection")
    text(selection, "persisted_line", "selection")
    text(selection, "tes_location", "selection")
    text(selection, "stream", "selection")

    outputs = mapping(spec.get("outputs"), "outputs")
    text(outputs, "file", "outputs")
    text(outputs, "tree", "outputs")
    branches = nonempty_list(
        outputs.get("required_branches"), "outputs.required_branches"
    )
    if not all(isinstance(branch, str) and branch for branch in branches):
        fail("outputs.required_branches must contain strings")
    minimum_entries = outputs.get("minimum_entries")
    if not isinstance(minimum_entries, int) or minimum_entries < 1:
        fail("outputs.minimum_entries must be at least 1")

    checks = nonempty_list(spec.get("validation"), "validation")
    stages = set()
    for index, raw in enumerate(checks):
        check = mapping(raw, f"validation[{index}]")
        stages.add(text(check, "stage", f"validation[{index}]"))
        text(check, "criterion", f"validation[{index}]")
    required_stages = {"static", "runtime", "artifact"}
    if not required_stages <= stages:
        fail("validation must include static, runtime, and artifact stages")

    decisions = spec.get("decisions")
    if not isinstance(decisions, list):
        fail("decisions must be a list")
    decision_ids: set[str] = set()
    for index, raw in enumerate(decisions):
        decision = mapping(raw, f"decisions[{index}]")
        identifier = text(decision, "id", f"decisions[{index}]")
        if identifier in decision_ids:
            fail(f"duplicate decision id: {identifier}")
        decision_ids.add(identifier)
        if decision.get("status") not in DECISION_STATES:
            fail(f"decisions[{index}].status is invalid")
        text(decision, "owner", f"decisions[{index}]")
        if not isinstance(decision.get("evidence"), list):
            fail(f"decisions[{index}].evidence must be a list")

    preservation = mapping(spec.get("preservation"), "preservation")
    for key in ("code", "environment", "data", "outputs"):
        text(preservation, key, "preservation")

    requirements = spec.get("external_requirements")
    if not isinstance(requirements, list):
        fail("external_requirements must be a list")
    for index, raw in enumerate(requirements):
        requirement = mapping(raw, f"external_requirements[{index}]")
        text(requirement, "requirement", f"external_requirements[{index}]")
        source = text(requirement, "source", f"external_requirements[{index}]")
        if not source.startswith(("https://", "cern:")):
            fail(f"external_requirements[{index}].source must be explicit")

    open_decisions = [
        decision["id"] for decision in decisions if decision["status"] == "open"
    ]
    if analysis["status"] == "execution-ready" and open_decisions:
        fail("execution-ready specifications cannot have open decisions")

    print(
        json.dumps(
            {
                "spec": str(args.spec),
                "analysis_id": analysis["id"],
                "use_case": analysis["use_case"],
                "datasets": sorted(dataset_ids),
                "required_branches": sorted(branches),
                "open_decisions": open_decisions,
                "status": "analysis specification is auditable",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
