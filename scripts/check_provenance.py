#!/usr/bin/env python3
"""Validate adapted-content provenance records and referenced local paths."""

from __future__ import annotations

from _lib import (
    ROOT,
    CheckError,
    load_json,
    read_skill_frontmatter,
    relative_files,
    validate_json,
)


def main() -> None:
    provenance_paths = relative_files("plugins/*/provenance.json")
    recorded: set[str] = set()
    for path in provenance_paths:
        data = load_json(path)
        validate_json(data, "provenance.schema.json", path)
        for item in data["items"]:
            local_path = item["local_path"]
            if local_path in recorded:
                raise CheckError(f"duplicate provenance local_path: {local_path}")
            target = (ROOT / local_path).resolve()
            if not target.is_relative_to(ROOT.resolve()) or not target.exists():
                raise CheckError(
                    f"{path.relative_to(ROOT)}: missing or unsafe local_path "
                    f"{local_path!r}"
                )
            recorded.add(local_path)

    for skill_path in relative_files("plugins/*/skills/*/SKILL.md"):
        frontmatter = read_skill_frontmatter(skill_path)
        origin = frontmatter.get("metadata", {}).get("origin")
        relative = skill_path.parent.relative_to(ROOT).as_posix()
        if origin == "adapted" and relative not in recorded:
            raise CheckError(
                f"{skill_path.relative_to(ROOT)}: adapted skill directory is not "
                "listed in a provenance record"
            )

    print(f"OK: {len(recorded)} adapted-content provenance records are valid")


if __name__ == "__main__":
    try:
        main()
    except CheckError as error:
        raise SystemExit(f"error: {error}") from error
