from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.check_hardening import routing_accuracy

ROOT = Path(__file__).resolve().parent.parent


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_hardening_gate_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_hardening.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "codex=100.0%" in result.stdout
    assert "claude-code=100.0%" in result.stdout


def test_routing_measurement_covers_every_skill_and_defer_case() -> None:
    cases = load("tests/skill-routing.json")["cases"]
    evidence = load("tests/evidence/hardening.json")
    expected_skills = {case["expected_skill"] for case in cases} - {None}
    assert len(expected_skills) == 6
    assert sum(case["expected_skill"] is None for case in cases) == 6

    for client in evidence["routing_measurement"]["clients"]:
        accuracy, by_skill = routing_accuracy(client["predictions"], cases)
        assert accuracy == 1
        assert set(by_skill) == expected_skills
        assert set(by_skill.values()) == {1}


def test_adversarial_matrix_has_one_case_per_required_boundary() -> None:
    evaluations = load("tests/hardening-evaluations.json")
    categories = {case["category"] for case in evaluations["adversarial_cases"]}
    assert categories == {
        "incorrect-era",
        "missing-credentials",
        "untrusted-instructions",
        "unsafe-file-path",
        "excessive-permissions",
    }


def test_root_and_mcp_permissions_fail_closed() -> None:
    inventory = load("mcp-dependencies.json")
    assert all(server["read_only"] for server in inventory["servers"])
    root = next(server for server in inventory["servers"] if server["name"] == "root")
    assert root["required_env"] == ["ROOT_MCP_DATA_PATH"]
    assert root["args"].count("${ROOT_MCP_DATA_PATH}") == 2
    assert "--allowed-root" in root["args"]
    assert "--no-allow-remote" in root["args"]
    assert "--no-export" in root["args"]


def test_public_services_do_not_require_credentials() -> None:
    inventory = load("mcp-dependencies.json")
    public = {"cerngitlab", "inspirehep", "hepdata", "cds"}
    servers = {server["name"]: server for server in inventory["servers"]}
    for name in public:
        assert servers[name]["public_without_credentials"]
        assert servers[name]["required_env"] == []


def test_cds_exclusion_has_owner_and_milestone() -> None:
    cds = load("tests/evidence/hardening.json")["cds_search"]
    assert cds["anonymous_search"] == "failed"
    assert cds["decision"] == "excluded-from-v0.1-support"
    assert cds["owner"]
    assert "before 0.1.0" in cds["follow_up_milestone"]
