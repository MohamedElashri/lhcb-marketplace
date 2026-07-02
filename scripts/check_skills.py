#!/usr/bin/env python3
"""Validate Agent Skills and repository-required frontmatter."""

from __future__ import annotations

import shutil
import subprocess

import yaml
from _lib import (
    ROOT,
    CheckError,
    read_skill_frontmatter,
    relative_files,
    validate_json,
)


def main() -> None:
    skill_paths = relative_files("plugins/*/skills/*/SKILL.md")
    if skill_paths and shutil.which("agentskills") is None:
        raise CheckError("'agentskills' executable is not available")

    for path in skill_paths:
        metadata = read_skill_frontmatter(path)
        if path.parent.name != metadata.get("name"):
            raise CheckError(
                f"{path.relative_to(ROOT)}: skill name must match directory name"
            )
        validate_json(
            metadata,
            "skill-metadata.schema.json",
            path,
        )
        body = path.read_text(encoding="utf-8")
        for section in (
            "## Workflow",
            "## Validation",
            "## Failure handling",
            "## Provenance and scope",
        ):
            if section.lower() not in body.lower():
                raise CheckError(f"{path.relative_to(ROOT)}: missing {section}")
        if "Do not use" not in metadata["description"]:
            raise CheckError(
                f"{path.relative_to(ROOT)}: description must declare non-triggers"
            )
        if "TODO" in body:
            raise CheckError(f"{path.relative_to(ROOT)}: unresolved TODO")
        sources = metadata["metadata"]["sources"]
        if "https://" not in sources:
            raise CheckError(f"{path.relative_to(ROOT)}: public source URL required")

        agent_path = path.parent / "agents" / "openai.yaml"
        if not agent_path.is_file():
            raise CheckError(f"{path.relative_to(ROOT)}: agents/openai.yaml is missing")
        try:
            agent_data = yaml.safe_load(agent_path.read_text(encoding="utf-8"))
            interface = agent_data["interface"]
            default_prompt = interface["default_prompt"]
        except (OSError, yaml.YAMLError, KeyError, TypeError) as error:
            raise CheckError(f"{agent_path.relative_to(ROOT)}: {error}") from error
        if f"${metadata['name']}" not in default_prompt:
            raise CheckError(
                f"{agent_path.relative_to(ROOT)}: default prompt must name the skill"
            )

        result = subprocess.run(
            ["agentskills", "validate", str(path.parent)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            message = (result.stdout + result.stderr).strip()
            raise CheckError(f"{path.relative_to(ROOT)}: {message}")

    print(f"OK: {len(skill_paths)} Agent Skills are valid")


if __name__ == "__main__":
    try:
        main()
    except CheckError as error:
        raise SystemExit(f"error: {error}") from error
