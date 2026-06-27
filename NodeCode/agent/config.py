"""
config.py - Load and parse mcp_config.json, and auto-discover folder-based MCP servers
"""

import json
import os
from pathlib import Path
from typing import Any


def load_config(path: str = "mcp_config.json") -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_server_url(config: dict) -> str:
    server = config.get("server", {})
    host = server.get("host", "localhost")
    port = server.get("port", 11434)
    return f"http://{host}:{port}"


def get_model(config: dict) -> str:
    return config.get("model", "qwen2.5-coder:14b")


def get_temperature(config: dict) -> float:
    return config.get("temperature", 0.2)


def get_context_size(config: dict) -> int:
    return config.get("context_size", 32768)


def get_max_output_lines(config: dict) -> int:
    return config.get("max_output_lines", 200)


def get_mcp_servers(config: dict) -> dict[str, dict]:
    return config.get("mcpServers", {})


def expand_args(args: list[str]) -> list[str]:
    return [os.path.expandvars(a) for a in args]


def _resolve_args(args: list[str], base_dir: Path) -> list[str]:
    """Expand env vars in args and resolve relative paths against base_dir."""
    resolved = []
    for arg in args:
        expanded = os.path.expandvars(arg)
        p = base_dir / expanded
        resolved.append(str(p) if p.exists() else expanded)
    return resolved


def _load_folder_servers(folder: Path) -> dict[str, dict]:
    """
    Scan a folder for subfolders containing either:
      - server_config.json  (explicit config)
      - server.py           (bare file, auto-detected, launched as `python server.py`)

    Returns a dict of server_name -> server config ready to merge into mcpServers.
    Skips disabled servers and empty folders.
    """
    servers = {}
    if not folder.exists():
        return servers

    for entry in sorted(folder.iterdir()):
        if not entry.is_dir():
            continue

        cfg_file = entry / "server_config.json"

        if cfg_file.exists():
            # Explicit config — load it
            try:
                with open(cfg_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            if cfg.get("disabled", False):
                continue

            command = os.path.expandvars(cfg.get("command", "python"))
            args = _resolve_args(cfg.get("args", ["server.py"]), entry)
            env = cfg.get("env") or {}

        elif (entry / "server.py").exists():
            # Bare server.py — auto-detect, default to `python server.py`
            command = "python"
            args = [str(entry / "server.py")]
            env = {}

        else:
            # Nothing launchable found
            continue

        servers[entry.name] = {
            "command": command,
            "args": args,
            "env": env,
            "_source_dir": str(entry),
        }

    return servers


def build_merged_mcp_servers(config: dict, project_root: Path) -> dict[str, dict]:
    """
    Merge MCP server definitions from three sources (priority order, highest first):
      1. mcp_config.json  mcpServers  (user config — wins on conflict)
      2. mcp_servers/     (custom drop-in folder)
      3. mcp_servers_default/  (built-in servers — always loaded)
    """
    defaults = _load_folder_servers(project_root / "mcp_servers_default")
    custom   = _load_folder_servers(project_root / "mcp_servers")
    explicit = get_mcp_servers(config)

    # Merge: later dicts win on key collision
    merged = {}
    merged.update(defaults)   # lowest priority
    merged.update(custom)     # overrides defaults
    merged.update(explicit)   # highest priority — config always wins
    return merged
