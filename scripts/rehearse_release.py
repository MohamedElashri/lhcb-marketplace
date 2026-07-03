#!/usr/bin/env python3
"""Run the clean-snapshot and isolated-client release rehearsal."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    from _lib import ROOT, CheckError, load_json
except ModuleNotFoundError:
    from scripts._lib import ROOT, CheckError, load_json

PLUGINS = ("lhcb", "cern-code", "root-analysis", "hep-research")
MARKETPLACE = "lhcb-agent-marketplace"
IGNORED_NAMES = {
    ".codex",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".uv-cache",
    ".uv-tools",
    ".venv",
    "__pycache__",
    "plan.md",
}


def command(
    arguments: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
) -> str:
    result = subprocess.run(
        arguments,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        output = (result.stdout + result.stderr).strip()
        raise CheckError(f"{' '.join(arguments)} failed:\n{output}")
    return result.stdout.strip()


def json_command(
    arguments: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
) -> Any:
    output = command(arguments, cwd=cwd, environment=environment)
    try:
        return json.loads(output)
    except json.JSONDecodeError as error:
        raise CheckError(
            f"{' '.join(arguments)} did not return JSON: {output}"
        ) from error


def copy_release_tree(destination: Path) -> None:
    def ignore(_directory: str, names: list[str]) -> set[str]:
        return {name for name in names if name in IGNORED_NAMES}

    shutil.copytree(ROOT, destination, ignore=ignore)
    for name in IGNORED_NAMES:
        if (destination / name).exists():
            raise CheckError(f"release snapshot retained local-only path {name}")


def canonical_versions(checkout: Path) -> dict[str, str]:
    versions: dict[str, str] = {}
    for plugin in PLUGINS:
        versions[plugin] = load_json(checkout / "plugins" / plugin / "plugin.json")[
            "version"
        ]
    return versions


def create_clean_checkout(
    temporary: Path,
    environment: dict[str, str],
) -> Path:
    source = temporary / "release-source"
    checkout = temporary / "checkout"
    copy_release_tree(source)
    command(
        ["git", "init", "--initial-branch=main"],
        cwd=source,
        environment=environment,
    )
    command(
        ["git", "config", "user.name", "Release Rehearsal"],
        cwd=source,
        environment=environment,
    )
    command(
        ["git", "config", "user.email", "release-rehearsal@example.invalid"],
        cwd=source,
        environment=environment,
    )
    command(["git", "add", "."], cwd=source, environment=environment)
    command(
        ["git", "commit", "-m", "Stage release"],
        cwd=source,
        environment=environment,
    )
    command(
        ["git", "clone", "--quiet", str(source), str(checkout)],
        cwd=temporary,
        environment=environment,
    )
    status = command(
        ["git", "status", "--porcelain"],
        cwd=checkout,
        environment=environment,
    )
    if status:
        raise CheckError(f"release checkout is dirty:\n{status}")
    return checkout


def inspect_install(path: Path, plugin: str) -> None:
    if not (path / ".codex-plugin" / "plugin.json").is_file():
        raise CheckError(f"{plugin}: installed Codex manifest is missing")
    if plugin == "lhcb":
        skills = list((path / "skills").glob("*/SKILL.md"))
        if len(skills) != 6:
            raise CheckError(f"{plugin}: expected six installed skills")
    elif not (path / ".mcp.json").is_file():
        raise CheckError(f"{plugin}: installed MCP configuration is missing")


def codex_rehearsal(
    checkout: Path,
    temporary: Path,
    base_environment: dict[str, str],
) -> dict[str, Any]:
    codex_home = temporary / "codex-home"
    codex_home.mkdir()
    environment = {**base_environment, "CODEX_HOME": str(codex_home)}
    version = command(["codex", "--version"], cwd=checkout, environment=environment)
    json_command(
        ["codex", "plugin", "marketplace", "add", str(checkout), "--json"],
        cwd=checkout,
        environment=environment,
    )
    installed: list[str] = []
    for plugin in PLUGINS:
        result = json_command(
            [
                "codex",
                "plugin",
                "add",
                f"{plugin}@{MARKETPLACE}",
                "--json",
            ],
            cwd=checkout,
            environment=environment,
        )
        listing = json_command(
            ["codex", "plugin", "list", "--json"],
            cwd=checkout,
            environment=environment,
        )
        names = {item["name"] for item in listing["installed"] if item["installed"]}
        if names != {plugin}:
            raise CheckError(
                f"codex: installing {plugin} also installed {sorted(names - {plugin})}"
            )
        inspect_install(Path(result["installedPath"]), plugin)
        installed.append(plugin)
        json_command(
            [
                "codex",
                "plugin",
                "remove",
                f"{plugin}@{MARKETPLACE}",
                "--json",
            ],
            cwd=checkout,
            environment=environment,
        )
    json_command(
        ["codex", "plugin", "marketplace", "remove", MARKETPLACE, "--json"],
        cwd=checkout,
        environment=environment,
    )
    return {"version": version, "plugins": installed}


def claude_installed_names(listing: Any) -> set[str]:
    if not isinstance(listing, list):
        raise CheckError("claude plugin list returned an unexpected JSON shape")
    names: set[str] = set()
    for item in listing:
        if not isinstance(item, dict):
            raise CheckError("claude plugin list contains a non-object entry")
        name = item.get("name") or item.get("id", "").split("@", maxsplit=1)[0]
        if name:
            names.add(name)
    return names


def claude_rehearsal(
    checkout: Path,
    temporary: Path,
    base_environment: dict[str, str],
) -> dict[str, Any]:
    claude_home = temporary / "claude-home"
    claude_config = temporary / "claude-config"
    claude_home.mkdir()
    claude_config.mkdir()
    environment = {
        **base_environment,
        "HOME": str(claude_home),
        "CLAUDE_CONFIG_DIR": str(claude_config),
    }
    version = command(["claude", "--version"], cwd=checkout, environment=environment)
    command(
        [
            "claude",
            "plugin",
            "marketplace",
            "add",
            str(checkout),
            "--scope",
            "user",
        ],
        cwd=checkout,
        environment=environment,
    )
    installed: list[str] = []
    for plugin in PLUGINS:
        command(
            [
                "claude",
                "plugin",
                "install",
                f"{plugin}@{MARKETPLACE}",
                "--scope",
                "user",
            ],
            cwd=checkout,
            environment=environment,
        )
        listing = json_command(
            ["claude", "plugin", "list", "--json"],
            cwd=checkout,
            environment=environment,
        )
        names = claude_installed_names(listing)
        if names != {plugin}:
            raise CheckError(
                f"claude: installing {plugin} also installed {sorted(names - {plugin})}"
            )
        installed.append(plugin)
        command(
            [
                "claude",
                "plugin",
                "uninstall",
                f"{plugin}@{MARKETPLACE}",
                "--scope",
                "user",
            ],
            cwd=checkout,
            environment=environment,
        )
    command(
        ["claude", "plugin", "marketplace", "remove", MARKETPLACE],
        cwd=checkout,
        environment=environment,
    )
    return {"version": version, "plugins": installed}


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="lhcb-rc-rehearsal-") as directory:
        temporary = Path(directory)
        environment = os.environ.copy()
        checkout = create_clean_checkout(temporary, environment)
        command(
            [sys.executable, "scripts/check_all.py"],
            cwd=checkout,
            environment=environment,
        )
        result = {
            "release_versions": canonical_versions(checkout),
            "clean_checkout": "passed",
            "repository_gate": "passed",
            "codex": codex_rehearsal(checkout, temporary, environment),
            "claude_code": claude_rehearsal(checkout, temporary, environment),
        }
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except CheckError as error:
        raise SystemExit(f"error: {error}") from error
