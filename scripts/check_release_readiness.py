#!/usr/bin/env python3
"""Validate release-candidate metadata and rehearsal evidence."""

from __future__ import annotations

from typing import Any

try:
    from _lib import ROOT, CheckError, load_json, validate_json
except ModuleNotFoundError:
    from scripts._lib import ROOT, CheckError, load_json, validate_json

EVIDENCE = ROOT / "tests" / "evidence" / "release-readiness.json"
CANDIDATE = "0.1.0-rc.1"
PLUGINS = ("lhcb", "cern-code", "root-analysis", "hep-research")
CLIENTS = {"codex", "claude-code"}


def canonical_plugins() -> list[dict[str, Any]]:
    marketplace = load_json(ROOT / "marketplace.json")
    names = [entry["name"] for entry in marketplace["plugins"]]
    if names != list(PLUGINS):
        raise CheckError("release candidate must retain the four-plugin boundary")
    return [
        load_json(ROOT / entry["path"] / "plugin.json")
        for entry in marketplace["plugins"]
    ]


def validate_versions(plugins: list[dict[str, Any]]) -> None:
    for plugin in plugins:
        if plugin["version"] != CANDIDATE:
            raise CheckError(
                f"{plugin['name']}: expected release candidate {CANDIDATE}"
            )
        for client in (".codex-plugin", ".claude-plugin"):
            adapter = load_json(
                ROOT / "plugins" / plugin["name"] / client / "plugin.json"
            )
            if adapter["version"] != CANDIDATE:
                raise CheckError(
                    f"{plugin['name']}: {client} version is not synchronized"
                )

    claude_marketplace = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    versions = {
        entry["name"]: entry["version"] for entry in claude_marketplace["plugins"]
    }
    if versions != dict.fromkeys(PLUGINS, CANDIDATE):
        raise CheckError("Claude marketplace release versions are not synchronized")


def validate_documentation() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    normalized = " ".join(readme.split())
    required = (
        "## Release candidate: 0.1.0-rc.1",
        "### Release notes",
        "### Access requirements and limitations",
        "### Migration notes",
        "community alpha",
        "not an official or endorsed LHCb product",
        "Anonymous CDS record search is excluded from v0.1 support",
        "Linux is the only supported v0.1 platform",
        "mcp-dependencies.json",
        "scripts/rehearse_release.py",
    )
    for text in required:
        if text not in normalized:
            raise CheckError(f"README.md lacks required release text {text!r}")

    if "Find the corresponding CERN document record." in readme:
        raise CheckError("release documentation claims unsupported CDS search")
    hep_manifest = load_json(ROOT / "plugins" / "hep-research" / "plugin.json")
    prompts = hep_manifest["interface"]["default_prompts"]
    if any("corresponding CERN document record" in prompt for prompt in prompts):
        raise CheckError("HEP Research still advertises unsupported CDS search")

    root_markdown = {path.name for path in ROOT.glob("*.md")}
    if root_markdown - {"README.md", "CONTRIBUTING.md", "SECURITY.md", "plan.md"}:
        raise CheckError("release documentation must stay in the root document set")


def validate_evidence(evidence: dict[str, Any]) -> None:
    clients = evidence["rehearsal"]["clients"]
    names = [client["client"] for client in clients]
    if set(names) != CLIENTS or len(names) != len(CLIENTS):
        raise CheckError("release rehearsal must cover each supported client once")
    for client in clients:
        if client["plugins"] != list(PLUGINS):
            raise CheckError(
                f"{client['client']}: rehearsal must cover every plugin in order"
            )

    hardening = load_json(ROOT / "tests" / "evidence" / "hardening.json")
    if hardening["open_critical_issues"]:
        raise CheckError("hardening critical issues block the release candidate")
    if hardening["cds_search"]["decision"] != "excluded-from-v0.1-support":
        raise CheckError("release readiness must preserve the CDS exclusion")

    inventory = load_json(
        ROOT / evidence["release_documentation"]["dependency_inventory"]
    )
    if len(inventory["servers"]) != 5:
        raise CheckError("release dependency inventory must contain five MCP servers")


def main() -> None:
    evidence = load_json(EVIDENCE)
    validate_json(evidence, "release-readiness.schema.json", EVIDENCE)
    plugins = canonical_plugins()
    validate_versions(plugins)
    validate_documentation()
    validate_evidence(evidence)
    print(
        f"OK: {CANDIDATE} release evidence covers "
        f"{len(PLUGINS)} independent plugins on {len(CLIENTS)} clients"
    )


if __name__ == "__main__":
    try:
        main()
    except CheckError as error:
        raise SystemExit(f"error: {error}") from error
