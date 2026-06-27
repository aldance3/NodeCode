"""
mcp/client.py - High-level MCP client for one server
"""

import time
from typing import Any

from mcp.process import start_process
from mcp.protocol import MCPProtocol


class MCPClient:
    def __init__(self, server_name: str, command: str, args: list[str],
                 env: dict[str, str] | None = None):
        self.server_name = server_name
        self.command = command
        self.args = args
        self.env = env
        self.proc = None
        self.protocol: MCPProtocol | None = None
        self.tools: dict[str, dict] = {}  # tool_name -> schema

    def start(self):
        self.proc = start_process(self.command, self.args, self.env)
        self.protocol = MCPProtocol(self.proc)
        self._initialize()
        self._discover_tools()

    def _initialize(self):
        """Send MCP initialize handshake."""
        result = self.protocol.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "ollama-code", "version": "1.0.0"},
        })
        self.protocol.send_notification("notifications/initialized")

    def _discover_tools(self):
        """Discover all tools from this server."""
        result = self.protocol.send_request("tools/list", {})
        for tool in result.get("tools", []):
            name = tool.get("name", "")
            self.tools[name] = {
                "description": tool.get("description", ""),
                "inputSchema": tool.get("inputSchema", {}),
            }

    def call_tool(self, tool_name: str, arguments: dict) -> Any:
        result = self.protocol.send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        }, timeout=60.0)
        return result

    def stop(self):
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass

    def is_alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None
