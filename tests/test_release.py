from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "0.1.0"
PLUGINS = ("lhcb", "cern-code", "root-analysis", "hep-research")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_release_gate_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_release.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert VERSION in result.stdout


def test_canonical_and_generated_versions_match_release() -> None:
    claude_marketplace = load(ROOT / ".claude-plugin" / "marketplace.json")
    marketplace_versions = {
        plugin["name"]: plugin["version"] for plugin in claude_marketplace["plugins"]
    }
    assert marketplace_versions == dict.fromkeys(PLUGINS, VERSION)

    for plugin in PLUGINS:
        root = ROOT / "plugins" / plugin
        assert load(root / "plugin.json")["version"] == VERSION
        assert load(root / ".codex-plugin" / "plugin.json")["version"] == VERSION
        assert load(root / ".claude-plugin" / "plugin.json")["version"] == VERSION


def test_release_rehearsal_covers_independent_installs() -> None:
    evidence = load(ROOT / "tests" / "evidence" / "release.json")
    assert evidence["rehearsal"]["clean_checkout"] == "passed"
    assert evidence["rehearsal"]["repository_gate"] == "passed"
    for client in evidence["rehearsal"]["clients"]:
        assert client["isolated_home"] is True
        assert client["independent_install"] == "passed"
        assert client["plugins"] == list(PLUGINS)


def test_release_notes_preserve_cds_exclusion() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Anonymous CDS record search is excluded from v0.1 support" in " ".join(
        readme.split()
    )
    manifest = load(ROOT / "plugins" / "hep-research" / "plugin.json")
    prompts = " ".join(manifest["interface"]["default_prompts"])
    assert "Find the corresponding CERN document record" not in prompts


def test_release_has_maintenance_inventory() -> None:
    evidence = load(ROOT / "tests" / "evidence" / "release.json")
    maintenance = load(ROOT / evidence["maintenance_inventory"])
    assert maintenance["verification_policy"]["cadence_months"] == 6
    assert len(maintenance["skills"]) == 6
    assert len(maintenance["integrations"]) == 5
