#!/usr/bin/env python3
"""Build and optionally probe an explicit LHCb released environment command."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess

VERSION = re.compile(r"^v\d+r\d+(?:p\d+)?$")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--application", default="DaVinci")
    parser.add_argument("--version", required=True)
    parser.add_argument("--platform")
    parser.add_argument(
        "--probe",
        action="store_true",
        help="execute lbexec --help in the selected environment",
    )
    args = parser.parse_args()

    if not VERSION.fullmatch(args.version):
        parser.error("--version must be an explicit release such as v65r0")

    command = ["lb-run"]
    if args.platform:
        command.extend(["-c", args.platform])
    command.extend([f"{args.application}/{args.version}", "lbexec", "--help"])

    result: dict[str, object] = {
        "application": args.application,
        "version": args.version,
        "platform": args.platform,
        "command": shlex.join(command),
        "lb_run_available": shutil.which("lb-run") is not None,
        "probed": False,
    }

    if args.probe:
        if not result["lb_run_available"]:
            raise SystemExit("error: lb-run is unavailable on this host")
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        result["probed"] = True
        result["returncode"] = completed.returncode
        if completed.returncode:
            message = (completed.stderr or completed.stdout).strip()
            raise SystemExit(f"error: environment probe failed: {message}")

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
