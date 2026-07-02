#!/usr/bin/env python3
"""Generate plugin MCP configurations from the pinned dependency inventory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from _lib import ROOT, CheckError, load_json

INVENTORY = ROOT / "mcp-dependencies.json"


def generated_files() -> dict[Path, dict[str, Any]]:
    inventory = load_json(INVENTORY)
    by_plugin: dict[str, dict[str, Any]] = {}
    for server in inventory["servers"]:
        plugin_servers = by_plugin.setdefault(server["plugin"], {})
        plugin_servers[server["name"]] = {
            "type": "stdio",
            "command": "uvx",
            "args": [
                "--python",
                server["runtime_python"],
                "--from",
                f"{server['package']}=={server['version']}",
                server["executable"],
                *server["args"],
            ],
        }
    return {
        ROOT / "plugins" / plugin / ".mcp.json": {"mcpServers": servers}
        for plugin, servers in by_plugin.items()
    }


def serialized(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of updating when generated MCP configs are stale",
    )
    args = parser.parse_args()

    stale: list[str] = []
    for path, value in generated_files().items():
        expected = serialized(value)
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == expected:
            continue
        if args.check:
            stale.append(str(path.relative_to(ROOT)))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected, encoding="utf-8")
        print(f"updated {path.relative_to(ROOT)}")

    if stale:
        raise CheckError(
            "generated MCP configs are stale: "
            + ", ".join(stale)
            + "; run scripts/build_mcp_configs.py"
        )
    if args.check:
        print("OK: generated MCP configs are current")


if __name__ == "__main__":
    try:
        main()
    except CheckError as error:
        raise SystemExit(f"error: {error}") from error
