#!/usr/bin/env python3
"""Validate hardening scenarios, measurements, evidence, and limitations."""

from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from _lib import ROOT, CheckError, load_json, validate_json
except ModuleNotFoundError:
    from scripts._lib import ROOT, CheckError, load_json, validate_json

EVALUATIONS = ROOT / "tests" / "hardening-evaluations.json"
EVIDENCE = ROOT / "tests" / "evidence" / "hardening.json"
ROUTING = ROOT / "tests" / "skill-routing.json"
INVENTORY = ROOT / "mcp-dependencies.json"

SKILLS = {
    "lhcb-software-environment",
    "davinci-run3",
    "funtuple",
    "analysis-productions",
    "lhcb-data-discovery",
    "lhcb-analysis-spec",
}
SCENARIO_COMPONENTS = SKILLS | {
    "cern-code",
    "root-analysis",
    "hep-research",
}
ADVERSARIAL_CATEGORIES = {
    "incorrect-era",
    "missing-credentials",
    "untrusted-instructions",
    "unsafe-file-path",
    "excessive-permissions",
}
AUDITS = {"provenance", "dependencies", "secrets", "documentation"}
CLIENTS = {"codex", "claude-code"}


def referenced_path(value: str) -> Path:
    path = ROOT / value.split("#", maxsplit=1)[0]
    if not path.is_file():
        raise CheckError(f"{EVALUATIONS.relative_to(ROOT)}: missing evidence {value}")
    return path


def validate_scenarios(data: dict[str, Any]) -> None:
    identifiers: set[str] = set()
    components: set[str] = set()
    for scenario in data["cross_skill_scenarios"]:
        identifier = scenario["id"]
        if identifier in identifiers:
            raise CheckError(f"duplicate hardening case {identifier!r}")
        identifiers.add(identifier)
        for step in scenario["steps"]:
            component = step["component"]
            if component not in SCENARIO_COMPONENTS:
                raise CheckError(f"{identifier}: unknown component {component!r}")
            components.add(component)

    required = {
        "cern-code",
        "hep-research",
        "davinci-run3",
        "analysis-productions",
        "root-analysis",
    }
    if missing := required - components:
        raise CheckError(
            "cross-skill scenarios lack required coverage: "
            + ", ".join(sorted(missing))
        )

    categories: Counter[str] = Counter()
    for case in data["adversarial_cases"]:
        identifier = case["id"]
        if identifier in identifiers:
            raise CheckError(f"duplicate hardening case {identifier!r}")
        identifiers.add(identifier)
        categories[case["category"]] += 1
        for reference in case["automated_evidence"]:
            referenced_path(reference)

    if set(categories) != ADVERSARIAL_CATEGORIES:
        raise CheckError("adversarial cases must cover every required category")
    repeated = sorted(category for category, count in categories.items() if count != 1)
    if repeated:
        raise CheckError(
            "adversarial categories must have one canonical case: "
            + ", ".join(repeated)
        )


def routing_accuracy(
    predictions: list[dict[str, Any]],
    cases: list[dict[str, Any]],
) -> tuple[float, dict[str, float]]:
    expected_ids = [case["id"] for case in cases]
    predicted_ids = [prediction["id"] for prediction in predictions]
    if predicted_ids != expected_ids:
        raise CheckError("client predictions must contain every routing case in order")

    correct = 0
    skill_total: Counter[str] = Counter()
    skill_correct: Counter[str] = Counter()
    for prediction, case in zip(predictions, cases, strict=True):
        selected = prediction["selected_skill"]
        if selected is not None and selected not in SKILLS:
            raise CheckError(f"{case['id']}: unknown predicted skill {selected!r}")
        expected = case["expected_skill"]
        if expected is not None:
            skill_total[expected] += 1
        if selected == expected:
            correct += 1
            if expected is not None:
                skill_correct[expected] += 1

    by_skill = {
        skill: skill_correct[skill] / skill_total[skill] for skill in sorted(SKILLS)
    }
    return correct / len(cases), by_skill


def validate_routing_measurement(
    measurement: dict[str, Any],
    cases: list[dict[str, Any]],
) -> list[str]:
    threshold = measurement["accepted_accuracy"]
    clients = measurement["clients"]
    names = [client["client"] for client in clients]
    if set(names) != CLIENTS or len(names) != len(CLIENTS):
        raise CheckError("routing evidence must contain Codex and Claude Code once")

    summaries: list[str] = []
    for client in clients:
        accuracy, by_skill = routing_accuracy(client["predictions"], cases)
        if accuracy < threshold:
            raise CheckError(
                f"{client['client']}: routing accuracy {accuracy:.1%} "
                f"is below {threshold:.1%}"
            )
        weak = [skill for skill, recall in by_skill.items() if recall < 2 / 3]
        if weak:
            raise CheckError(
                f"{client['client']}: per-skill recall is below 66.7% for "
                + ", ".join(weak)
            )
        summaries.append(f"{client['client']}={accuracy:.1%}")
    return summaries


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_runtime(evidence: dict[str, Any]) -> None:
    runtime = evidence["runtime_revalidation"]
    expected_paths = {
        "tests/evidence/davinci-funtuple-runtime.json",
        "tests/evidence/analysis-production-runtime.json",
    }
    observed_paths = {item["path"] for item in runtime["preserved_evidence"]}
    if observed_paths != expected_paths:
        raise CheckError(
            "runtime revalidation must cover execution and production evidence"
        )
    for item in runtime["preserved_evidence"]:
        path = ROOT / item["path"]
        if not path.is_file() or sha256(path) != item["sha256"]:
            raise CheckError(f"{item['path']}: runtime evidence digest mismatch")

    execution = load_json(ROOT / "tests/evidence/davinci-funtuple-runtime.json")
    production = load_json(ROOT / "tests/evidence/analysis-production-runtime.json")
    for name, artifact in (
        ("DaVinci/FunTuple", execution["funtuple"]["artifact"]),
        ("Analysis Productions", production["artifact"]),
    ):
        if artifact["entries"] <= 0:
            raise CheckError(f"{name}: preserved ROOT artifact must be non-empty")
        required = {"B_M", "B_PT", "Ds_PT"}
        if not required <= set(artifact["required_branches"]):
            raise CheckError(f"{name}: preserved ROOT artifact lacks required branches")

    acceptance = load_json(ROOT / "tests/evidence/reviewer-acceptance.json")
    if set(acceptance["accepted_skills"]) != SKILLS:
        raise CheckError("reviewer acceptance does not cover all six skills")
    accepted_evidence = set(acceptance["evidence"])
    if not expected_paths <= accepted_evidence:
        raise CheckError("reviewer acceptance does not cite both runtime records")


def validate_security_controls() -> None:
    inventory = load_json(INVENTORY)
    if not all(server["read_only"] for server in inventory["servers"]):
        raise CheckError("every v0.1 MCP integration must remain read-only")

    root = next(server for server in inventory["servers"] if server["name"] == "root")
    if root["args"].count("${ROOT_MCP_DATA_PATH}") != 2:
        raise CheckError("ROOT data path and allowed root must use one explicit root")
    for argument in ("--allowed-root", "--no-allow-remote", "--no-export"):
        if argument not in root["args"]:
            raise CheckError(f"ROOT MCP is missing required control {argument}")

    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8").lower()
    if not (
        "are untrusted content" in security and "never follow instructions" in security
    ):
        raise CheckError(
            "security policy must reject instructions in retrieved content"
        )

    fallback_skills = (
        ROOT / "plugins/lhcb/skills/analysis-productions/SKILL.md",
        ROOT / "plugins/lhcb/skills/lhcb-data-discovery/SKILL.md",
        ROOT / "plugins/lhcb/skills/lhcb-analysis-spec/SKILL.md",
    )
    if not all("CDS" in path.read_text(encoding="utf-8") for path in fallback_skills):
        raise CheckError("planning skills must retain non-CDS fallbacks")


def validate_evidence(data: dict[str, Any]) -> list[str]:
    cases = load_json(ROUTING)["cases"]
    summaries = validate_routing_measurement(data["routing_measurement"], cases)
    validate_runtime(data)

    audit_names = [audit["name"] for audit in data["audits"]]
    if set(audit_names) != AUDITS or len(audit_names) != len(AUDITS):
        raise CheckError("hardening evidence must contain each required audit once")

    cds = data["cds_search"]
    if "experiment metadata" not in cds["supported_surface"].lower():
        raise CheckError("CDS supported surface must be stated precisely")
    if not cds["owner"].strip() or not cds["follow_up_milestone"].strip():
        raise CheckError("CDS exclusion requires an owner and follow-up milestone")

    limitation_text = " ".join(
        item["limitation"].lower() for item in data["known_limitations"]
    )
    if "cds" not in limitation_text or "xrootd" not in limitation_text:
        raise CheckError("known limitations must cover CDS and runtime input access")
    return summaries


def main() -> None:
    evaluations = load_json(EVALUATIONS)
    validate_json(evaluations, "hardening-evaluations.schema.json", EVALUATIONS)
    validate_scenarios(evaluations)
    validate_security_controls()

    evidence = load_json(EVIDENCE)
    validate_json(evidence, "hardening-evidence.schema.json", EVIDENCE)
    summaries = validate_evidence(evidence)
    print(
        "OK: hardening covers "
        f"{len(evaluations['cross_skill_scenarios'])} cross-skill scenarios, "
        f"{len(evaluations['adversarial_cases'])} adversarial controls, and "
        + ", ".join(summaries)
    )


if __name__ == "__main__":
    try:
        main()
    except CheckError as error:
        raise SystemExit(f"error: {error}") from error
