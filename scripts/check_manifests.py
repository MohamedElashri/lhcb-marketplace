#!/usr/bin/env python3
"""Validate canonical marketplace and plugin manifests."""

from __future__ import annotations

from _lib import ROOT, CheckError, load_json, relative_files, validate_json


def main() -> None:
    plugin_paths = relative_files("plugins/*/plugin.json")
    plugin_dirs = sorted(path for path in (ROOT / "plugins").glob("*") if path.is_dir())
    missing = [path for path in plugin_dirs if not (path / "plugin.json").is_file()]
    if missing:
        names = ", ".join(str(path.relative_to(ROOT)) for path in missing)
        raise CheckError(f"plugin directories missing plugin.json: {names}")

    plugins: dict[str, tuple[object, object]] = {}
    for path in plugin_paths:
        data = load_json(path)
        validate_json(data, "plugin.schema.json", path)
        name = data["name"]
        if path.parent.name != name:
            raise CheckError(
                f"{path.relative_to(ROOT)}: name {name!r} must match directory"
            )
        if name in plugins:
            raise CheckError(f"duplicate plugin name: {name}")
        plugins[name] = (path, data)

    marketplace_path = ROOT / "marketplace.json"
    if marketplace_path.exists():
        marketplace = load_json(marketplace_path)
        validate_json(marketplace, "marketplace.schema.json", marketplace_path)
        names = [entry["name"] for entry in marketplace["plugins"]]
        paths = [entry["path"] for entry in marketplace["plugins"]]
        if len(names) != len(set(names)):
            raise CheckError("marketplace.json contains duplicate plugin names")
        if len(paths) != len(set(paths)):
            raise CheckError("marketplace.json contains duplicate plugin paths")
        listed = {entry["name"]: entry["path"] for entry in marketplace["plugins"]}
        if set(listed) != set(plugins):
            raise CheckError(
                "marketplace plugins do not match plugin manifests: "
                f"catalog={sorted(listed)}, manifests={sorted(plugins)}"
            )
        for name, path in listed.items():
            expected = f"plugins/{name}"
            if path != expected:
                raise CheckError(
                    f"marketplace.json: plugin {name!r} path must be {expected!r}"
                )
    elif plugins:
        raise CheckError("marketplace.json is required when plugins exist")

    print(f"OK: {len(plugin_paths)} plugin manifests are valid")


if __name__ == "__main__":
    try:
        main()
    except CheckError as error:
        raise SystemExit(f"error: {error}") from error
