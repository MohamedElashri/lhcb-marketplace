#!/usr/bin/env python3
"""Validate an auditable LHCb Run 3 dataset-selection record."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

VERSION = re.compile(r"^v\d+r\d+(?:p\d+)?$")
POLARITIES = {"MagDown", "MagUp", "Both", "NotApplicable"}
PROCESSES = {"Hlt2", "Spruce", "TurboSpruce", "TurboPass", "Gen"}


def fail(message: str) -> None:
    raise SystemExit(f"error: {message}")


def mapping(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{name} must be a mapping")
    return value


def text_field(data: dict[str, Any], key: str, section: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(f"{section}.{key} must be a non-empty string")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    try:
        record = yaml.safe_load(args.record.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        fail(f"{args.record}: {error}")
    record = mapping(record, str(args.record))
    if record.get("schema_version") != 1:
        fail("schema_version must be 1")

    selection = mapping(record.get("selection"), "selection")
    if selection.get("era") != "run3":
        fail("selection.era must be run3")
    kind = selection.get("sample_kind")
    if kind not in {"data", "simulation"}:
        fail("selection.sample_kind must be data or simulation")
    text_field(selection, "purpose", "selection")

    bookkeeping = mapping(record.get("bookkeeping"), "bookkeeping")
    query = text_field(bookkeeping, "query", "bookkeeping")
    if not query.startswith("/"):
        fail("bookkeeping.query must be a complete absolute path")
    verified_at = text_field(bookkeeping, "verified_at", "bookkeeping")
    try:
        date.fromisoformat(verified_at)
    except ValueError:
        fail("bookkeeping.verified_at must be an ISO date")
    if not text_field(bookkeeping, "source_url", "bookkeeping").startswith("https://"):
        fail("bookkeeping.source_url must be public HTTPS provenance")

    metadata = mapping(record.get("metadata"), "metadata")
    for key in ("year", "campaign", "file_type", "stream"):
        text_field(metadata, key, "metadata")
    if metadata.get("polarity") not in POLARITIES:
        fail("metadata.polarity is invalid")
    event_type = metadata.get("event_type")
    if kind == "simulation":
        if not isinstance(event_type, str) or not event_type.isdigit():
            fail("simulation metadata.event_type must be a numeric string")
        if "/MC/" not in query:
            fail("simulation query must identify MC")
    else:
        if event_type is not None:
            fail("data metadata.event_type must be null")
        if not query.startswith("/LHCb/"):
            fail("data query must start with /LHCb/")

    runtime = mapping(record.get("runtime"), "runtime")
    if runtime.get("input_process") not in PROCESSES:
        fail("runtime.input_process is invalid")
    if runtime.get("simulation") is not (kind == "simulation"):
        fail("runtime.simulation disagrees with selection.sample_kind")
    application = mapping(runtime.get("application"), "runtime.application")
    text_field(application, "name", "runtime.application")
    if not VERSION.fullmatch(text_field(application, "version", "runtime.application")):
        fail("runtime.application.version must be exact")
    text_field(application, "platform", "runtime.application")
    conditions = mapping(runtime.get("conditions"), "runtime.conditions")
    if kind == "simulation":
        text_field(conditions, "dddb_tag", "runtime.conditions")
        text_field(conditions, "conddb_tag", "runtime.conditions")
    else:
        text_field(conditions, "geometry_version", "runtime.conditions")
        text_field(conditions, "conditions_version", "runtime.conditions")

    provenance = mapping(record.get("provenance"), "provenance")
    text_field(provenance, "selection_rationale", "provenance")
    alternatives = provenance.get("alternatives_considered")
    if not isinstance(alternatives, list):
        fail("provenance.alternatives_considered must be a list")
    text_field(provenance, "replica_check", "provenance")

    print(
        json.dumps(
            {
                "record": str(args.record),
                "sample_kind": kind,
                "query": query,
                "campaign": metadata["campaign"],
                "polarity": metadata["polarity"],
                "input_process": runtime["input_process"],
                "status": "dataset record is structurally complete",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
