#!/usr/bin/env python3
"""Verify a FunTuple ROOT tree, entry count, and required branches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import uproot


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root_file", type=Path)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--branch", action="append", default=[])
    parser.add_argument("--allow-empty", action="store_true")
    args = parser.parse_args()

    if not args.root_file.is_file():
        raise SystemExit(f"error: ROOT file does not exist: {args.root_file}")
    try:
        with uproot.open(args.root_file) as root_file:
            keys = root_file.keys(cycle=False, recursive=True)
            if args.tree not in keys:
                available = ", ".join(keys)
                raise SystemExit(
                    f"error: tree {args.tree!r} is absent; available keys: {available}"
                )
            tree = root_file[args.tree]
            branches = set(tree.keys())
            missing = sorted(set(args.branch) - branches)
            if missing:
                raise SystemExit(
                    f"error: missing required branches: {', '.join(missing)}"
                )
            if not args.allow_empty and tree.num_entries == 0:
                raise SystemExit(f"error: tree {args.tree!r} has zero entries")
            result = {
                "file": str(args.root_file),
                "tree": args.tree,
                "entries": tree.num_entries,
                "branches": sorted(branches),
                "required_branches": sorted(args.branch),
            }
    except OSError as error:
        raise SystemExit(f"error: cannot read ROOT file: {error}") from error
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
