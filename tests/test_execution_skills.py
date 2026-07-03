from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import uproot
import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "plugins" / "lhcb" / "skills"
ENV_SCRIPT = SKILLS / "lhcb-software-environment" / "scripts" / "check_environment.py"
DV_ROOT = SKILLS / "davinci-run3"
FT_ROOT = SKILLS / "funtuple"
RUNTIME_EVIDENCE = ROOT / "tests" / "evidence" / "davinci-funtuple-runtime.json"


def run_script(
    script: Path,
    *arguments: object,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *(str(argument) for argument in arguments)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_environment_command_is_explicit_and_portable() -> None:
    result = run_script(ENV_SCRIPT, "--version", "v65r0")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["command"] == "lb-run DaVinci/v65r0 lbexec --help"
    assert payload["probed"] is False
    assert "cvmfs_setup_available" in payload


def test_environment_probe_accepts_lbexec_help_exit_one(tmp_path: Path) -> None:
    lb_run = tmp_path / "lb-run"
    lb_run.write_text(
        "#!/bin/sh\nprintf 'usage: lbexec [-h] function options\\n'\nexit 1\n",
        encoding="utf-8",
    )
    lb_run.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"

    result = run_script(ENV_SCRIPT, "--version", "v65r0", "--probe", env=env)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["probed"] is True
    assert payload["probe_returncode"] == 1
    assert payload["probe_status"] == "lbexec help available"


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


def test_runtime_evidence_matches_checked_in_examples() -> None:
    evidence = json.loads(RUNTIME_EVIDENCE.read_text(encoding="utf-8"))
    dv_options = yaml.safe_load(
        (DV_ROOT / "assets" / "options.example.yaml").read_text(encoding="utf-8")
    )
    ft_options = yaml.safe_load(
        (FT_ROOT / "assets" / "options.example.yaml").read_text(encoding="utf-8")
    )

    assert evidence["environment"]["application"] == "DaVinci/v65r0"
    assert "+detdesc-" in evidence["environment"]["platform"]
    assert evidence["input"]["uri"] == dv_options["input_files"][0]
    assert evidence["input"]["uri"] == ft_options["input_files"][0]
    assert evidence["input"]["dddb_tag"] == dv_options["dddb_tag"]
    assert evidence["input"]["conddb_tag"] == dv_options["conddb_tag"]
    assert evidence["davinci"]["processed_events"] == dv_options["evt_max"]
    assert evidence["funtuple"]["processed_events"] == ft_options["evt_max"]
    assert evidence["davinci"]["selected_events"] > 0
    assert evidence["funtuple"]["artifact"]["entries"] > 0


@pytest.mark.parametrize(
    "skill",
    ["lhcb-software-environment", "davinci-run3", "funtuple"],
)
def test_execution_skills_declare_run3_scope_and_non_triggers(skill: str) -> None:
    text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
    assert "era: run3" in text
    assert "Do not use" in text
    assert "## Failure handling" in text
    assert "## Provenance and scope" in text
