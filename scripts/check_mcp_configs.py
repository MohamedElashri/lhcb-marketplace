#!/usr/bin/env python3
"""Validate MCP inventory, generated configs, and capability declarations."""

from __future__ import annotations

from _lib import ROOT, CheckError, load_json, relative_files, validate_json


def main() -> None:
    inventory_path = ROOT / "mcp-dependencies.json"
    inventory = load_json(inventory_path)
    validate_json(inventory, "mcp-inventory.schema.json", inventory_path)

    names = [server["name"] for server in inventory["servers"]]
    packages = [server["package"] for server in inventory["servers"]]
    if len(names) != len(set(names)):
        raise CheckError("MCP inventory contains duplicate server names")
    if len(packages) != len(set(packages)):
        raise CheckError("MCP inventory contains duplicate packages")

    configured_plugins = {server["plugin"] for server in inventory["servers"]}
    config_paths = relative_files("plugins/*/.mcp.json")
    if {path.parent.name for path in config_paths} != configured_plugins:
        raise CheckError("MCP config files do not match inventory plugin assignments")

    for path in config_paths:
        config = load_json(path)
        validate_json(config, "mcp-config.schema.json", path)
        for server in config["mcpServers"].values():
            args = server["args"]
            for index, argument in enumerate(args[:-1]):
                next_argument = args[index + 1]
                non_stdio_transport = (
                    argument == "--transport" and next_argument != "stdio"
                ) or (argument == "--mode" and next_argument in {"http", "auto"})
                if non_stdio_transport:
                    raise CheckError(
                        f"{path.relative_to(ROOT)}: non-stdio transport is forbidden"
                    )

    for server in inventory["servers"]:
        if set(server["required_env"]) & set(server["optional_env"]):
            raise CheckError(f"{server['name']}: environment requirements overlap")
        config = load_json(ROOT / "plugins" / server["plugin"] / ".mcp.json")
        args = config["mcpServers"][server["name"]]["args"]
        for variable in server["required_env"]:
            if f"${{{variable}}}" not in args:
                raise CheckError(
                    f"{server['name']}: required variable {variable} is not in args"
                )

    for plugin_path in relative_files("plugins/*/plugin.json"):
        plugin = load_json(plugin_path)
        expected = plugin["name"] in configured_plugins
        if plugin["capabilities"]["mcp"] is not expected:
            raise CheckError(
                f"{plugin_path.relative_to(ROOT)}: mcp capability must be {expected}"
            )

    print(
        f"OK: {len(inventory['servers'])} pinned MCP servers across "
        f"{len(config_paths)} plugin configs are valid"
    )


if __name__ == "__main__":
    try:
        main()
    except CheckError as error:
        raise SystemExit(f"error: {error}") from error
