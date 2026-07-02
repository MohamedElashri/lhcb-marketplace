#!/usr/bin/env python3
"""Validate the LHCb skill positive, negative, and era-routing contract."""

from __future__ import annotations

from collections import Counter

from _lib import ROOT, CheckError, load_json, relative_files, validate_json

CASES = ROOT / "tests" / "skill-routing.json"


def main() -> None:
    data = load_json(CASES)
    validate_json(data, "skill-evaluations.schema.json", CASES)
    known = {
        path.parent.name for path in relative_files("plugins/lhcb/skills/*/SKILL.md")
    }
    identifiers: set[str] = set()
    positive: Counter[str] = Counter()
    negative: Counter[str] = Counter()
    legacy = 0

    for case in data["cases"]:
        identifier = case["id"]
        if identifier in identifiers:
            raise CheckError(
                f"{CASES.relative_to(ROOT)}: duplicate case {identifier!r}"
            )
        identifiers.add(identifier)
        expected = case["expected_skill"]
        forbidden = set(case["forbidden_skills"])
        unknown = ({expected} if expected else set()) | forbidden
        unknown -= known
        if unknown:
            raise CheckError(
                f"{CASES.relative_to(ROOT)}:{identifier}: unknown skills: "
                + ", ".join(sorted(unknown))
            )
        if expected in forbidden:
            raise CheckError(
                f"{CASES.relative_to(ROOT)}:{identifier}: expected skill is forbidden"
            )
        if expected:
            positive[expected] += 1
        for skill in forbidden:
            negative[skill] += 1
        if case["expected_outcome"] == "reject-legacy-default":
            legacy += 1
            if expected is not None:
                raise CheckError(
                    f"{CASES.relative_to(ROOT)}:{identifier}: "
                    "legacy-default rejection cannot route to an LHCb skill"
                )

    for skill in known:
        if positive[skill] < 3:
            raise CheckError(f"{skill}: requires at least 3 positive routing cases")
        if negative[skill] < 3:
            raise CheckError(f"{skill}: requires at least 3 negative routing cases")
    if legacy < 3:
        raise CheckError("at least 3 legacy-default rejection cases are required")

    print(
        f"OK: {len(data['cases'])} routing cases cover "
        f"{len(known)} skills, including {legacy} legacy rejections"
    )


if __name__ == "__main__":
    try:
        main()
    except CheckError as error:
        raise SystemExit(f"error: {error}") from error
