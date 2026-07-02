from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import uproot

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "plugins" / "lhcb" / "skills"
ENV_SCRIPT = SKILLS / "lhcb-software-environment" / "scripts" / "check_environment.py"
DV_ROOT = SKILLS / "davinci-run3"
FT_ROOT = SKILLS / "funtuple"


def run_script(script: Path, *arguments: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *(str(argument) for argument in arguments)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_environment_command_is_explicit_and_portable() -> None:
    result = run_script(ENV_SCRIPT, "--version", "v65r0")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["command"] == "lb-run DaVinci/v65r0 lbexec --help"
    assert payload["probed"] is False


def test_environment_rejects_unpinned_release() -> None:
    result = run_script(ENV_SCRIPT, "--version", "latest")
    assert result.returncode != 0
    assert "explicit release" in result.stderr


def test_davinci_example_passes_static_validation() -> None:
    result = run_script(
        DV_ROOT / "scripts" / "validate_job.py",
        DV_ROOT / "assets" / "print_decay_tree.py",
        DV_ROOT / "assets" / "options.example.yaml",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["input_process"] == "Hlt2"
    assert payload["simulation"] is True


def test_davinci_validator_rejects_legacy_default(tmp_path: Path) -> None:
    module = tmp_path / "legacy.py"
    module.write_text(
        "from DaVinci import Options, make_config\n"
        "DaVinci().UserAlgorithms = []\n"
        "def main(options: Options):\n"
        "    return make_config(options, [])\n",
        encoding="utf-8",
    )
    result = run_script(
        DV_ROOT / "scripts" / "validate_job.py",
        module,
        DV_ROOT / "assets" / "options.example.yaml",
    )
    assert result.returncode != 0
    assert "legacy Run 1/2 markers" in result.stderr


def test_funtuple_example_passes_static_validation() -> None:
    result = run_script(
        FT_ROOT / "scripts" / "validate_config.py",
        FT_ROOT / "assets" / "tuple_job.py",
        FT_ROOT / "assets" / "options.example.yaml",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["fields"] == ["B", "BachelorPi", "Ds"]
    assert payload["ntuple_file"] == "tuple.root"


def test_funtuple_validator_rejects_legacy_default(tmp_path: Path) -> None:
    module = tmp_path / "legacy_tuple.py"
    module.write_text("from Configurables import DecayTreeTuple\n", encoding="utf-8")
    result = run_script(
        FT_ROOT / "scripts" / "validate_config.py",
        module,
        FT_ROOT / "assets" / "options.example.yaml",
    )
    assert result.returncode != 0
    assert "legacy tuple markers" in result.stderr


def test_funtuple_output_verifier_checks_tree_and_branches(tmp_path: Path) -> None:
    output = tmp_path / "tuple.root"
    with uproot.recreate(output) as root_file:
        root_file["BToDsPiTuple/DecayTree"] = {
            "B_PT": np.array([1200.0, 2400.0]),
            "B_M": np.array([5279.0, 5281.0]),
        }

    result = run_script(
        FT_ROOT / "scripts" / "verify_output.py",
        output,
        "--tree",
        "BToDsPiTuple/DecayTree",
        "--branch",
        "B_PT",
        "--branch",
        "B_M",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["entries"] == 2

    missing = run_script(
        FT_ROOT / "scripts" / "verify_output.py",
        output,
        "--tree",
        "BToDsPiTuple/DecayTree",
        "--branch",
        "DOES_NOT_EXIST",
    )
    assert missing.returncode != 0
    assert "missing required branches" in missing.stderr


@pytest.mark.parametrize(
    "skill",
    ["lhcb-software-environment", "davinci-run3", "funtuple"],
)
def test_phase4_skills_declare_run3_scope_and_non_triggers(skill: str) -> None:
    text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
    assert "era: run3" in text
    assert "Do not use" in text
    assert "## Failure handling" in text
    assert "## Provenance and scope" in text
