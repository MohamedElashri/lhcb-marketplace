#!/usr/bin/env python3
"""Validate generated Claude and Codex adapter manifests."""

from __future__ import annotations

from _lib import ROOT, CheckError, load_json, relative_files, validate_json


def main() -> None:
    codex_marketplace = ROOT / ".agents" / "plugins" / "marketplace.json"
    claude_marketplace = ROOT / ".claude-plugin" / "marketplace.json"
    validate_json(
        load_json(codex_marketplace),
        "codex-marketplace.schema.json",
        codex_marketplace,
    )
    validate_json(
        load_json(claude_marketplace),
        "claude-marketplace.schema.json",
        claude_marketplace,
    )

    codex_plugins = relative_files("plugins/*/.codex-plugin/plugin.json")
    claude_plugins = relative_files("plugins/*/.claude-plugin/plugin.json")
    for path in codex_plugins:
        data = load_json(path)
        validate_json(data, "codex-plugin.schema.json", path)
        if data["name"] != path.parent.parent.name:
            raise CheckError(f"{path.relative_to(ROOT)}: name must match plugin")
        if "skills" in data and not (path.parent.parent / "skills").is_dir():
            raise CheckError(f"{path.relative_to(ROOT)}: skills directory is missing")
        if "mcpServers" in data and not (path.parent.parent / ".mcp.json").is_file():
            raise CheckError(f"{path.relative_to(ROOT)}: .mcp.json is missing")
    for path in claude_plugins:
        data = load_json(path)
        validate_json(data, "claude-plugin.schema.json", path)
        if data["name"] != path.parent.parent.name:
            raise CheckError(f"{path.relative_to(ROOT)}: name must match plugin")

    if len(codex_plugins) != len(claude_plugins):
        raise CheckError("Claude and Codex plugin adapter counts differ")
    print(
        f"OK: {len(codex_plugins)} Codex and "
        f"{len(claude_plugins)} Claude plugin adapters are valid"
    )


if __name__ == "__main__":
    try:
        main()
    except CheckError as error:
        raise SystemExit(f"error: {error}") from error
