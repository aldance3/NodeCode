"""
mcp/manager.py - Manage all MCP server clients
"""

import sys
from typing import Any

from mcp.client import MCPClient
from utils.colors import info, error as color_error, dim


class MCPManager:
    def __init__(self, mcp_servers_config: dict):
        self.config = mcp_servers_config
        self.clients: dict[str, MCPClient] = {}  # server_name -> MCPClient
        self.tool_registry: dict[str, dict] = {}  # "server.tool" -> info

    def start_all(self):
        for server_name, server_cfg in self.config.items():
            command = server_cfg.get("command", "")
            args = server_cfg.get("args", [])
            env = server_cfg.get("env") or None  # None if missing or empty
            print(info(f"  Starting MCP server: {server_name}..."), flush=True)
            client = MCPClient(server_name, command, args, env)
            try:
                client.start()
                self.clients[server_name] = client
                count = len(client.tools)
                print(info(f"  ✓ {server_name}: {count} tools discovered"), flush=True)
                # Register tools in global registry
                for tool_name, tool_info in client.tools.items():
                    full_name = f"{server_name}.{tool_name}"
                    self.tool_registry[full_name] = {
                        **tool_info,
                        "_server": server_name,
                        "_tool": tool_name,
                    }
            except Exception as e:
                print(color_error(f"  Failed to start {server_name}: {e}"), flush=True)

    def stop_all(self):
        for client in self.clients.values():
            try:
                client.stop()
            except Exception:
                pass

    def get_tool_registry(self) -> dict[str, dict]:
        return self.tool_registry

    def call_tool(self, full_tool_name: str, arguments: dict) -> Any:
        """
        full_tool_name is like 'server_name.tool_name'
        """
        info_entry = self.tool_registry.get(full_tool_name)
        if not info_entry:
            raise ValueError(f"Unknown tool: {full_tool_name}")

        server_name = info_entry["_server"]
        tool_name = info_entry["_tool"]

        client = self.clients.get(server_name)
        if not client:
            raise RuntimeError(f"Server '{server_name}' is not running")

        if not client.is_alive():
            raise RuntimeError(f"Server '{server_name}' has crashed")

        return client.call_tool(tool_name, arguments)
