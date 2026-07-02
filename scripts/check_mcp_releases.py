#!/usr/bin/env python3
"""Check pinned MCP versions and wheel hashes against PyPI."""

from __future__ import annotations

import json
import urllib.request
from typing import Any

from _lib import CheckError, load_json
from smoke_mcp import INVENTORY


def pypi_metadata(package: str) -> dict[str, Any]:
    request = urllib.request.Request(
        f"https://pypi.org/pypi/{package}/json",
        headers={"User-Agent": "lhcb-agent-marketplace-release-check/0.1"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def main() -> None:
    inventory = load_json(INVENTORY)
    errors: list[str] = []
    for server in inventory["servers"]:
        metadata = pypi_metadata(server["package"])
        latest = metadata["info"]["version"]
        if latest != server["version"]:
            errors.append(
                f"{server['package']}: pinned {server['version']}, latest {latest}"
            )
            continue
        wheels = [
            artifact
            for artifact in metadata["releases"][server["version"]]
            if artifact["packagetype"] == "bdist_wheel"
        ]
        hashes = {artifact["digests"]["sha256"] for artifact in wheels}
        if server["wheel_sha256"] not in hashes:
            errors.append(
                f"{server['package']}=={server['version']}: wheel hash is not on PyPI"
            )
    if errors:
        raise CheckError("\n".join(errors))
    print(f"OK: {len(inventory['servers'])} MCP pins match current PyPI releases")


if __name__ == "__main__":
    try:
        main()
    except (CheckError, OSError) as error:
        raise SystemExit(f"error: {error}") from error
