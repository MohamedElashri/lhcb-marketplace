#!/usr/bin/env python3
"""Generate client adapters from canonical marketplace and plugin metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from _lib import ROOT, CheckError, load_json

CODEX_MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
CLAUDE_MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"


def canonical_plugins() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    marketplace = load_json(ROOT / "marketplace.json")
    plugins = [
        load_json(ROOT / entry["path"] / "plugin.json")
        for entry in marketplace["plugins"]
    ]
    return marketplace, plugins


def codex_plugin(plugin: dict[str, Any]) -> dict[str, Any]:
    interface = plugin["interface"]
    capabilities = plugin["capabilities"]
    output: dict[str, Any] = {
        "name": plugin["name"],
        "version": plugin["version"],
        "description": plugin["description"],
        "author": plugin["author"],
        "license": plugin["license"],
        "keywords": plugin["keywords"],
        "interface": {
            "displayName": plugin["display_name"],
            "shortDescription": interface["short_description"],
            "longDescription": interface["long_description"],
            "developerName": plugin["author"]["name"],
            "category": interface["category"],
            "capabilities": [
                name
                for name, enabled in (
                    ("Skills", capabilities["skills"]),
                    ("MCP", capabilities["mcp"]),
                )
                if enabled
            ],
            "defaultPrompt": interface["default_prompts"],
        },
    }
    if capabilities["skills"]:
        output["skills"] = "./skills/"
    if capabilities["mcp"]:
        output["mcpServers"] = "./.mcp.json"
    return output


def claude_plugin(plugin: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {
        "name": plugin["name"],
        "version": plugin["version"],
        "description": plugin["description"],
        "author": plugin["author"],
        "license": plugin["license"],
        "keywords": plugin["keywords"],
    }
    if plugin["capabilities"]["skills"]:
        output["skills"] = "./skills/"
    return output


def claude_marketplace_entry(plugin: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {
        "name": plugin["name"],
        "description": plugin["description"],
        "author": plugin["author"],
        "source": f"./plugins/{plugin['name']}",
        "version": plugin["version"],
        "keywords": plugin["keywords"],
    }
    if plugin["capabilities"]["skills"]:
        output["skills"] = "./skills/"
    return output


def generated_files() -> dict[Path, dict[str, Any]]:
    marketplace, plugins = canonical_plugins()
    files: dict[Path, dict[str, Any]] = {}
    for entry, plugin in zip(marketplace["plugins"], plugins, strict=True):
        plugin_root = ROOT / entry["path"]
        files[plugin_root / ".codex-plugin" / "plugin.json"] = codex_plugin(plugin)
        files[plugin_root / ".claude-plugin" / "plugin.json"] = claude_plugin(plugin)

    files[CODEX_MARKETPLACE] = {
        "name": marketplace["name"],
        "interface": {"displayName": "LHCb Agent Marketplace"},
        "plugins": [
            {
                "name": plugin["name"],
                "source": {
                    "source": "local",
                    "path": f"./plugins/{plugin['name']}",
                },
                "policy": {
                    "installation": "AVAILABLE",
                    "authentication": "ON_USE",
                },
                "category": plugin["interface"]["category"],
            }
            for plugin in plugins
        ],
    }
    files[CLAUDE_MARKETPLACE] = {
        "name": marketplace["name"],
        "owner": marketplace["owner"],
        "metadata": {"description": marketplace["description"]},
        "plugins": [claude_marketplace_entry(plugin) for plugin in plugins],
    }
    return files


def serialized(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of updating when generated adapters are stale",
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
            "generated client adapters are stale: "
            + ", ".join(stale)
            + "; run scripts/build_adapters.py"
        )
    if args.check:
        print("OK: generated client adapters are current")


if __name__ == "__main__":
    try:
        main()
    except CheckError as error:
        raise SystemExit(f"error: {error}") from error
