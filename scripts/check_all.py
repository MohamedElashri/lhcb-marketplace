#!/usr/bin/env python3
"""Run the complete local repository gate."""

from __future__ import annotations

import subprocess
import sys

COMMANDS = [
    [sys.executable, "scripts/check_schemas.py"],
    [sys.executable, "scripts/check_manifests.py"],
    [sys.executable, "scripts/build_mcp_configs.py", "--check"],
    [sys.executable, "scripts/check_mcp_configs.py"],
    [sys.executable, "scripts/build_adapters.py", "--check"],
    [sys.executable, "scripts/check_adapters.py"],
    [sys.executable, "scripts/check_skills.py"],
    [sys.executable, "scripts/evaluate_skills.py"],
    [sys.executable, "scripts/check_provenance.py"],
    [sys.executable, "scripts/build_catalog.py", "--check"],
    [sys.executable, "-m", "pytest"],
    ["ruff", "check", "."],
    ["ruff", "format", "--check", "."],
]


def main() -> None:
    for command in COMMANDS:
        print(f"+ {' '.join(command)}", flush=True)
        subprocess.run(command, check=True)
    print("OK: complete repository gate passed")


if __name__ == "__main__":
    main()
