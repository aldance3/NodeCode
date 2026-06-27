#!/usr/bin/env python3
"""
main.py - Entry point for Ollama Code Agent
A local Claude Code-style agent using Ollama + MCP servers.
"""

import os
import sys
import signal
import argparse
from pathlib import Path

# Force unbuffered stdout so streaming tokens print immediately
sys.stdout.reconfigure(line_buffering=False)
os.environ["PYTHONUNBUFFERED"] = "1"

# Ensure agent/ is on the path when running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agent"))

from config import (
    load_config, get_server_url, get_model, get_temperature,
    get_context_size, get_max_output_lines, build_merged_mcp_servers,
)
from logger import Logger
from mcp.manager import MCPManager
from ollama.client import OllamaClient
from prompt_builder import build_system_prompt
from agent import Agent
from utils.colors import info, error as color_error, user_prompt, dim


BANNER = r"""
    _   __          __     ______          __   
   / | / /___  ____/ /__  / ____/___  ____/ /__ 
  /  |/ / __ \/ __  / _ \/ /   / __ \/ __  / _ \
 / /|  / /_/ / /_/ /  __/ /___/ /_/ / /_/ /  __/
/_/ |_/\____/\__,_/\___/\____/\____/\__,_/\___/ 
                                                
  Local Claude Code-style agent  •  Ollama + MCP
"""


def main():
    parser = argparse.ArgumentParser(description="Ollama Code Agent")
    parser.add_argument(
        "--config", default="mcp_config.json",
        help="Path to mcp_config.json (default: mcp_config.json)"
    )
    parser.add_argument(
        "--model", default=None,
        help="Override model from config"
    )
    parser.add_argument(
        "--no-mcp", action="store_true",
        help="Skip MCP servers (useful for testing Ollama connectivity)"
    )
    args = parser.parse_args()

    print(info(BANNER))

    # Load config
    config_path = args.config
    # If config not found relative to cwd, try next to main.py
    if not os.path.exists(config_path):
        alt = os.path.join(os.path.dirname(__file__), config_path)
        if os.path.exists(alt):
            config_path = alt

    try:
        config = load_config(config_path)
        print(info(f"Config loaded: {config_path}"))
    except FileNotFoundError as e:
        print(color_error(str(e)))
        sys.exit(1)

    server_url = get_server_url(config)
    model = args.model or get_model(config)
    temperature = get_temperature(config)
    context_size = get_context_size(config)
    max_output_lines = get_max_output_lines(config)

    # Resolve project root (folder containing main.py)
    project_root = Path(os.path.dirname(os.path.abspath(__file__)))
    mcp_servers = build_merged_mcp_servers(config, project_root)

    print(info(f"Ollama: {server_url}  model={model}  temp={temperature}"))

    # Init logger
    log_dir = os.path.join(os.path.dirname(__file__), "agent", "logs")
    logger = Logger(log_dir)

    # Start MCP servers
    manager = MCPManager(mcp_servers)
    if mcp_servers and not args.no_mcp:
        print(info(f"\nStarting MCP servers ({len(mcp_servers)} total)..."))
        manager.start_all()
    else:
        print(dim("MCP servers skipped."))

    # Build system prompt from discovered tools
    tool_registry = manager.get_tool_registry()
    system_prompt = build_system_prompt(tool_registry)
    print(info(f"\n{len(tool_registry)} tools available across {len(manager.clients)} server(s)."))

    # Init Ollama client
    ollama = OllamaClient(server_url, model, temperature, context_size)

    # Test connectivity
    print(info(f"Connecting to Ollama at {server_url}..."))
    try:
        models = ollama.list_models()
        print(info(f"✓ Connected. {len(models)} model(s) available."))
    except Exception as e:
        print(color_error(f"Could not connect to Ollama: {e}"))
        print(dim("Continuing anyway — model calls may fail."))

    # Init agent
    agent = Agent(ollama, manager, system_prompt, logger, max_output_lines)

    # Graceful shutdown on Ctrl+C
    def _shutdown(sig, frame):
        print(info("\n\nShutting down..."))
        manager.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)

    print(info("\nType your request below. Type /help for commands.\n"))

    # Main REPL
    while True:
        try:
            raw = input(user_prompt("> ")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            _shutdown(None, None)

        if not raw:
            continue

        if raw.startswith("/"):
            agent.slash_command(raw)
            continue

        agent.run_turn(raw)


if __name__ == "__main__":
    main()
