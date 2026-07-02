from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "plugins" / "lhcb" / "skills"
AP_ROOT = SKILLS / "analysis-productions"
DATA_ROOT = SKILLS / "lhcb-data-discovery"
SPEC_ROOT = SKILLS / "lhcb-analysis-spec"
AP_EVIDENCE = ROOT / "tests" / "evidence" / "phase5-analysis-production-runtime.json"
REVIEW_EVIDENCE = ROOT / "tests" / "evidence" / "reviewer-acceptance.json"


def run_script(script: Path, *arguments: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *(str(argument) for argument in arguments)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_analysis_production_example_passes_portable_validation() -> None:
    result = run_script(
        AP_ROOT / "scripts" / "validate_production.py",
        AP_ROOT / "assets" / "starterkit",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["application"] == "DaVinci/v66r7p2"
    assert payload["jobs"][0]["input_source"] == "bk_query"


def test_analysis_production_rejects_legacy_entrypoint(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    production = root / "starterkit"
    shutil.copytree(AP_ROOT / "assets" / "starterkit", production)
    module = production / "production_job.py"
    module.write_text(
        module.read_text(encoding="utf-8") + "\nDaVinci().UserAlgorithms = []\n",
        encoding="utf-8",
    )
    result = run_script(AP_ROOT / "scripts" / "validate_production.py", production)
    assert result.returncode != 0
    assert "legacy markers" in result.stderr


def test_dataset_record_example_passes_validation() -> None:
    result = run_script(
        DATA_ROOT / "scripts" / "validate_dataset_record.py",
        DATA_ROOT / "assets" / "dataset-record.example.yaml",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["sample_kind"] == "data"
    assert payload["input_process"] == "TurboSpruce"


def test_dataset_record_rejects_data_mc_mismatch(tmp_path: Path) -> None:
    record = yaml.safe_load(
        (DATA_ROOT / "assets" / "dataset-record.example.yaml").read_text(
            encoding="utf-8"
        )
    )
    record["selection"]["sample_kind"] = "simulation"
    path = tmp_path / "record.yaml"
    path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
    result = run_script(DATA_ROOT / "scripts" / "validate_dataset_record.py", path)
    assert result.returncode != 0
    assert "event_type" in result.stderr or "identify MC" in result.stderr


@pytest.mark.parametrize(
    ("use_case", "kind", "query"),
    [
        (
            "measurement",
            "data",
            "/LHCb/Collision24/Beam6800GeV-VeloClosed-MagDown/Real Data/"
            "Sprucing24c4a/94000000/B2OC.DST",
        ),
        (
            "efficiency",
            "simulation",
            "evt+std://MC/2024/13264021/"
            "Beam6800GeV-2024.W35.37-MagUp-Nu6.3-25ns-Pythia8/"
            "Sim10d/HLT2-2024.W35.39",
        ),
        (
            "control-study",
            "data",
            "/LHCb/Collision24/Beam6800GeV-VeloClosed-MagDown/Real Data/"
            "Sprucing24c4a/94000000/B2OC.DST",
        ),
    ],
)
def test_representative_analysis_specifications(
    tmp_path: Path, use_case: str, kind: str, query: str
) -> None:
    spec = yaml.safe_load(
        (SPEC_ROOT / "assets" / "analysis-spec.example.yaml").read_text(
            encoding="utf-8"
        )
    )
    spec = copy.deepcopy(spec)
    spec["analysis"]["id"] = f"run3-{use_case}"
    spec["analysis"]["use_case"] = use_case
    spec["physics"]["subject"] = f"Representative Run 3 {use_case} specification."
    spec["datasets"][0]["kind"] = kind
    spec["datasets"][0]["bookkeeping_query"] = query
    path = tmp_path / f"{use_case}.yaml"
    path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")

    result = run_script(SPEC_ROOT / "scripts" / "validate_spec.py", path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["use_case"] == use_case


def test_analysis_spec_rejects_uncited_external_policy(tmp_path: Path) -> None:
    spec = yaml.safe_load(
        (SPEC_ROOT / "assets" / "analysis-spec.example.yaml").read_text(
            encoding="utf-8"
        )
    )
    spec["external_requirements"] = [
        {"requirement": "Apply an unspecified collaboration policy.", "source": "none"}
    ]
    path = tmp_path / "uncited.yaml"
    path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
    result = run_script(SPEC_ROOT / "scripts" / "validate_spec.py", path)
    assert result.returncode != 0
    assert "source must be explicit" in result.stderr


def test_analysis_spec_rejects_dataset_without_provenance(tmp_path: Path) -> None:
    spec = yaml.safe_load(
        (SPEC_ROOT / "assets" / "analysis-spec.example.yaml").read_text(
            encoding="utf-8"
        )
    )
    del spec["datasets"][0]["source"]
    path = tmp_path / "missing-dataset-source.yaml"
    path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
    result = run_script(SPEC_ROOT / "scripts" / "validate_spec.py", path)
    assert result.returncode != 0
    assert "datasets[0].source" in result.stderr


def test_phase5_runtime_evidence_matches_assets() -> None:
    evidence = json.loads(AP_EVIDENCE.read_text(encoding="utf-8"))
    info = yaml.safe_load(
        (AP_ROOT / "assets" / "starterkit" / "info.yaml").read_text(encoding="utf-8")
    )
    job = evidence["production"]["job"]
    assert evidence["production"]["application"] == info["defaults"]["application"]
    assert evidence["production"]["bookkeeping_query"] == info[job]["input"]["bk_query"]
    assert evidence["production"]["dry_run_exit_code"] == 0
    assert evidence["production"]["test_exit_code"] == 0
    assert evidence["artifact"]["entries"] > 0
    assert set(evidence["artifact"]["required_branches"]) == {"B_M", "B_PT", "Ds_PT"}


def test_reviewer_acceptance_covers_every_lhcb_skill() -> None:
    evidence = json.loads(REVIEW_EVIDENCE.read_text(encoding="utf-8"))
    skills = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
    assert evidence["reviewer"] == {
        "name": "Mohamed Elashri",
        "account": "@MohamedElashri",
        "cern_username": "melashri",
        "email": "mohamed.elashri@cern.ch",
    }
    assert set(evidence["accepted_skills"]) == skills
