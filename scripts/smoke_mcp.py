#!/usr/bin/env python3
"""Smoke-test pinned stdio MCP servers from the canonical inventory."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np
import uproot
from _lib import ROOT, CheckError, load_json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent

INVENTORY = ROOT / "mcp-dependencies.json"
PLACEHOLDER = re.compile(r"\$\{([A-Z][A-Z0-9_]*)\}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument(
        "--server",
        action="append",
        help="server name to test; repeat to select multiple servers",
    )
    result.add_argument(
        "--all",
        action="store_true",
        help="test every server in the inventory",
    )
    result.add_argument(
        "--live",
        action="store_true",
        help="call each server's harmless configured smoke tool",
    )
    result.add_argument(
        "--show-tools",
        action="store_true",
        help="print discovered tool names and input schemas",
    )
    result.add_argument(
        "--timeout",
        type=float,
        default=90.0,
        help="per-server timeout in seconds",
    )
    return result


def select_servers(names: list[str] | None, all_servers: bool) -> list[dict[str, Any]]:
    inventory = load_json(INVENTORY)
    servers = inventory["servers"]
    if all_servers:
        return servers
    if not names:
        raise CheckError("select at least one --server or pass --all")
    by_name = {server["name"]: server for server in servers}
    unknown = sorted(set(names) - set(by_name))
    if unknown:
        raise CheckError(f"unknown MCP servers: {', '.join(unknown)}")
    return [by_name[name] for name in names]


def expand(value: str, environment: dict[str, str]) -> str:
    missing: list[str] = []

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        resolved = environment.get(name)
        if not resolved:
            missing.append(name)
            return match.group(0)
        return resolved

    expanded = PLACEHOLDER.sub(replace, value)
    if missing:
        raise CheckError(
            f"required environment variables are unset: {', '.join(missing)}"
        )
    return expanded


def command_for(
    server: dict[str, Any],
    environment: dict[str, str],
) -> StdioServerParameters:
    args = [
        "--python",
        server["runtime_python"],
        "--from",
        f"{server['package']}=={server['version']}",
        server["executable"],
        *(expand(argument, environment) for argument in server["args"]),
    ]
    return StdioServerParameters(command="uvx", args=args, env=environment, cwd=ROOT)


def create_root_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with uproot.recreate(path) as root_file:
        root_file["Events"] = {
            "mass": np.array([5.20, 5.28, 5.36], dtype=np.float64),
            "pt": np.array([1.0, 2.0, 3.0], dtype=np.float64),
        }


@contextmanager
def root_environment() -> Iterator[tuple[dict[str, str], Path, Path]]:
    with tempfile.TemporaryDirectory(prefix="lhcb-root-mcp-") as temporary:
        base = Path(temporary)
        allowed = base / "allowed"
        allowed_file = allowed / "fixture.root"
        denied = base / "denied" / "outside.root"
        create_root_file(allowed_file)
        create_root_file(denied)
        environment = os.environ.copy()
        environment["ROOT_MCP_DATA_PATH"] = str(allowed.resolve())
        yield environment, allowed_file, denied


def tool_payload(result: CallToolResult) -> Any:
    texts = [
        content.text for content in result.content if isinstance(content, TextContent)
    ]
    if not texts:
        return None
    try:
        return json.loads(texts[0])
    except json.JSONDecodeError:
        return texts[0]


def assert_success(server_name: str, result: CallToolResult) -> Any:
    if result.isError:
        raise CheckError(f"{server_name}: smoke tool returned an MCP error")
    payload = tool_payload(result)
    if isinstance(payload, dict) and payload.get("error"):
        raise CheckError(f"{server_name}: smoke tool returned {payload['error']!r}")
    return payload


async def run_server(
    server: dict[str, Any],
    environment: dict[str, str],
    *,
    live: bool,
    show_tools: bool,
    root_paths: tuple[Path, Path] | None = None,
) -> dict[str, Any]:
    parameters = command_for(server, environment)
    async with (
        stdio_client(parameters) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        initialized = await session.initialize()
        listed = await session.list_tools()
        tool_names = [tool.name for tool in listed.tools]
        expected = server["smoke"]["tool"]
        if expected not in tool_names:
            raise CheckError(
                f"{server['name']}: expected smoke tool {expected!r} is absent"
            )
        result: dict[str, Any] = {
            "server": server["name"],
            "protocol": initialized.protocolVersion,
            "tools": len(tool_names),
        }
        if show_tools:
            result["tool_schemas"] = {
                tool.name: tool.inputSchema for tool in listed.tools
            }
        if live:
            called = await session.call_tool(
                expected,
                arguments=server["smoke"]["arguments"],
            )
            assert_success(server["name"], called)
            result["smoke_tool"] = expected
            if root_paths is not None:
                allowed, denied = root_paths
                allowed_result = await session.call_tool(
                    "inspect_file",
                    arguments={"path": str(allowed)},
                )
                assert_success(server["name"], allowed_result)
                denied_result = await session.call_tool(
                    "inspect_file",
                    arguments={"path": str(denied)},
                )
                denied_payload = tool_payload(denied_result)
                if not (
                    denied_result.isError
                    or (
                        isinstance(denied_payload, dict) and denied_payload.get("error")
                    )
                ):
                    raise CheckError("root: out-of-root file access was not denied")
                result["filesystem_boundary"] = "enforced"
        return result


async def run_selected(
    servers: list[dict[str, Any]],
    *,
    live: bool,
    show_tools: bool,
    timeout: float,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for server in servers:
        try:
            if server["name"] == "root":
                with root_environment() as (environment, allowed, denied):
                    result = await asyncio.wait_for(
                        run_server(
                            server,
                            environment,
                            live=live,
                            show_tools=show_tools,
                            root_paths=(allowed, denied),
                        ),
                        timeout=timeout,
                    )
            else:
                result = await asyncio.wait_for(
                    run_server(
                        server,
                        os.environ.copy(),
                        live=live,
                        show_tools=show_tools,
                    ),
                    timeout=timeout,
                )
        except TimeoutError as error:
            raise CheckError(
                f"{server['name']}: timed out after {timeout:g} seconds"
            ) from error
        results.append(result)
    return results


def main() -> None:
    args = parser().parse_args()
    servers = select_servers(args.server, args.all)
    results = asyncio.run(
        run_selected(
            servers,
            live=args.live,
            show_tools=args.show_tools,
            timeout=args.timeout,
        )
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    try:
        main()
    except CheckError as error:
        raise SystemExit(f"error: {error}") from error
