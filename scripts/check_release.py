#!/usr/bin/env python3
"""Validate release metadata, ownership, and rehearsal evidence."""

from __future__ import annotations

from typing import Any

try:
    from _lib import ROOT, CheckError, load_json, validate_json
except ModuleNotFoundError:
    from scripts._lib import ROOT, CheckError, load_json, validate_json

EVIDENCE = ROOT / "tests" / "evidence" / "release.json"
VERSION = "0.1.0"
PLUGINS = ("lhcb", "cern-code", "root-analysis", "hep-research")
CLIENTS = {"codex", "claude-code"}


def canonical_plugins() -> list[dict[str, Any]]:
    marketplace = load_json(ROOT / "marketplace.json")
    names = [entry["name"] for entry in marketplace["plugins"]]
    if names != list(PLUGINS):
        raise CheckError("release must retain the four-plugin boundary")
    return [
        load_json(ROOT / entry["path"] / "plugin.json")
        for entry in marketplace["plugins"]
    ]


def validate_versions(plugins: list[dict[str, Any]]) -> None:
    for plugin in plugins:
        if plugin["version"] != VERSION:
            raise CheckError(f"{plugin['name']}: expected release {VERSION}")
        for client in (".codex-plugin", ".claude-plugin"):
            adapter = load_json(
                ROOT / "plugins" / plugin["name"] / client / "plugin.json"
            )
            if adapter["version"] != VERSION:
                raise CheckError(
                    f"{plugin['name']}: {client} version is not synchronized"
                )

    claude_marketplace = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    versions = {
        entry["name"]: entry["version"] for entry in claude_marketplace["plugins"]
    }
    if versions != dict.fromkeys(PLUGINS, VERSION):
        raise CheckError("Claude marketplace release versions are not synchronized")


def validate_documentation() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    normalized = " ".join(readme.split())
    required = (
        "## Release 0.1.0",
        "### Release notes",
        "### Access requirements and limitations",
        "### Migration notes",
        "community alpha",
        "not an official or endorsed LHCb product",
        "Anonymous CDS record search is excluded from v0.1 support",
        "Linux is the only supported v0.1 platform",
        "mcp-dependencies.json",
        "scripts/rehearse_release.py",
        "git clone --branch 0.1.0 --depth 1",
        "maintenance.json",
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
        raise CheckError("hardening critical issues block the release")
    if hardening["cds_search"]["decision"] != "excluded-from-v0.1-support":
        raise CheckError("release readiness must preserve the CDS exclusion")

    inventory = load_json(
        ROOT / evidence["release_documentation"]["dependency_inventory"]
    )
    if len(inventory["servers"]) != 5:
        raise CheckError("release dependency inventory must contain five MCP servers")


def validate_maintenance(evidence: dict[str, Any]) -> None:
    path = ROOT / evidence["maintenance_inventory"]
    maintenance = load_json(path)
    validate_json(maintenance, "maintenance.schema.json", path)

    skill_names = {skill["name"] for skill in maintenance["skills"]}
    installed_skills = {
        path.parent.name for path in (ROOT / "plugins/lhcb/skills").glob("*/SKILL.md")
    }
    if skill_names != installed_skills:
        raise CheckError("maintenance inventory must cover every LHCb skill")
    if any(
        skill["next_verification"] != "2027-01-02" for skill in maintenance["skills"]
    ):
        raise CheckError("every skill must have a six-month verification date")
    for skill in maintenance["skills"]:
        for runtime_path in skill["runtime_evidence"]:
            if not (ROOT / runtime_path).is_file():
                raise CheckError(f"{skill['name']}: missing {runtime_path}")

    inventory = load_json(ROOT / "mcp-dependencies.json")
    expected_integrations = {
        server["name"]: (
            server["plugin"],
            f"{server['package']}=={server['version']}",
        )
        for server in inventory["servers"]
    }
    observed_integrations = {
        item["name"]: (item["plugin"], item["package"])
        for item in maintenance["integrations"]
    }
    if observed_integrations != expected_integrations:
        raise CheckError("maintenance inventory must cover every pinned integration")

    issues = {item["issue"] for item in maintenance["follow_ups"]}
    if issues != {
        "https://github.com/MohamedElashri/lhcb-marketplace/issues/4",
        "https://github.com/MohamedElashri/lhcb-marketplace/issues/5",
    }:
        raise CheckError("maintenance follow-ups must link both release issues")


def main() -> None:
    evidence = load_json(EVIDENCE)
    validate_json(evidence, "release.schema.json", EVIDENCE)
    plugins = canonical_plugins()
    validate_versions(plugins)
    validate_documentation()
    validate_evidence(evidence)
    validate_maintenance(evidence)
    print(
        f"OK: {VERSION} release evidence covers "
        f"{len(PLUGINS)} independent plugins on {len(CLIENTS)} clients"
    )


if __name__ == "__main__":
    try:
        main()
    except CheckError as error:
        raise SystemExit(f"error: {error}") from error
