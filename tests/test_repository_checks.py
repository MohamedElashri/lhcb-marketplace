from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts._lib import CheckError, read_skill_frontmatter, validate_json

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize(
    "script",
    [
        "check_schemas.py",
        "check_manifests.py",
        "check_mcp_configs.py",
        "check_adapters.py",
        "check_skills.py",
        "evaluate_skills.py",
        "check_provenance.py",
    ],
)
def test_repository_check_passes(script: str) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_catalog_is_current() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_catalog.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_client_adapters_are_current() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_adapters.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_mcp_configs_are_current() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_mcp_configs.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_plugin_schema_rejects_an_invalid_name(tmp_path: Path) -> None:
    source = tmp_path / "plugin.json"
    source.write_text("{}", encoding="utf-8")
    instance = {
        "schema_version": 1,
        "name": "Invalid Name",
        "display_name": "Invalid",
        "description": "A sufficiently long plugin description.",
        "version": "0.1.0",
        "license": "MIT",
        "capabilities": {"skills": True, "mcp": False},
    }
    with pytest.raises(CheckError, match="does not match"):
        validate_json(instance, "plugin.schema.json", source)


def test_skill_frontmatter_requires_delimiters(tmp_path: Path) -> None:
    skill = tmp_path / "SKILL.md"
    skill.write_text("# Missing frontmatter\n", encoding="utf-8")
    with pytest.raises(CheckError, match="opening YAML delimiter"):
        read_skill_frontmatter(skill)


def test_schemas_are_json() -> None:
    for path in sorted((ROOT / "schemas").glob("*.json")):
        assert isinstance(json.loads(path.read_text(encoding="utf-8")), dict)


def test_public_markdown_surface_stays_small() -> None:
    root_markdown = {path.name for path in ROOT.glob("*.md")}
    assert root_markdown <= {"README.md", "CONTRIBUTING.md", "SECURITY.md", "plan.md"}
    assert not list((ROOT / "docs").glob("**/*.md"))

    plugin_markdown = {
        path.relative_to(ROOT) for path in (ROOT / "plugins").glob("**/*.md")
    }
    assert plugin_markdown
    assert all(path.name == "SKILL.md" for path in plugin_markdown)


@pytest.mark.parametrize(
    "path",
    [
        ROOT / ".github" / "dependabot.yml",
        ROOT / ".github" / "workflows" / "check.yml",
    ],
)
def test_github_configuration_is_yaml(path: Path) -> None:
    assert isinstance(yaml.safe_load(path.read_text(encoding="utf-8")), dict)


def test_v01_plugin_boundary() -> None:
    marketplace = json.loads((ROOT / "marketplace.json").read_text(encoding="utf-8"))
    assert [plugin["name"] for plugin in marketplace["plugins"]] == [
        "lhcb",
        "cern-code",
        "root-analysis",
        "hep-research",
    ]


def test_adapters_claim_only_implemented_capabilities() -> None:
    lhcb_path = ROOT / "plugins" / "lhcb" / ".codex-plugin" / "plugin.json"
    lhcb = json.loads(lhcb_path.read_text(encoding="utf-8"))
    assert lhcb["skills"] == "./skills/"
    assert "mcpServers" not in lhcb
    assert lhcb["interface"]["capabilities"] == ["Skills"]

    for path in sorted((ROOT / "plugins").glob("*/.codex-plugin/plugin.json")):
        plugin = json.loads(path.read_text(encoding="utf-8"))
        if plugin["name"] == "lhcb":
            continue
        assert "skills" not in plugin
        assert plugin["mcpServers"] == "./.mcp.json"
        assert plugin["interface"]["capabilities"] == ["MCP"]


def test_mcp_inventory_is_pinned_and_read_only() -> None:
    inventory = json.loads((ROOT / "mcp-dependencies.json").read_text(encoding="utf-8"))
    assert [server["name"] for server in inventory["servers"]] == [
        "cerngitlab",
        "root",
        "inspirehep",
        "hepdata",
        "cds",
    ]
    assert all(server["read_only"] for server in inventory["servers"])
    assert all(server["runtime_python"] == "3.12" for server in inventory["servers"])
    assert all(len(server["wheel_sha256"]) == 64 for server in inventory["servers"])


def test_root_mcp_fails_closed_in_generated_config() -> None:
    config = json.loads(
        (ROOT / "plugins" / "root-analysis" / ".mcp.json").read_text(encoding="utf-8")
    )
    args = config["mcpServers"]["root"]["args"]
    assert args.count("${ROOT_MCP_DATA_PATH}") == 2
    assert "--allowed-root" in args
    assert "--no-allow-remote" in args
    assert "--no-export" in args
    assert "--enable-root" not in args
