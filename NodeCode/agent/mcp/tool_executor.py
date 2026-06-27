"""
mcp/tool_executor.py - Execute tool calls and format results
"""

import json
import time
from typing import Any

from mcp.manager import MCPManager
from utils.compression import compress_output
from utils.colors import tool_running, tool_done, tool_error


def extract_text_from_result(result: Any) -> str:
    """
    MCP tools/call returns a result object.
    Extract human-readable text from it.
    """
    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        # Standard MCP content array
        content = result.get("content", [])
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        parts.append(item.get("text", ""))
                    elif item.get("type") == "resource":
                        parts.append(str(item.get("resource", "")))
                    else:
                        parts.append(json.dumps(item))
                else:
                    parts.append(str(item))
            return "\n".join(parts)

        # Fallback: just dump the dict
        return json.dumps(result, ensure_ascii=False, indent=2)

    return str(result)


class ToolExecutor:
    def __init__(self, manager: MCPManager, max_output_lines: int = 200):
        self.manager = manager
        self.max_output_lines = max_output_lines

    def execute(self, tool_name: str, arguments: dict) -> tuple[str, float]:
        """
        Execute a tool. Returns (formatted_result, elapsed_seconds).
        """
        # Determine server for display
        registry_entry = self.manager.tool_registry.get(tool_name, {})
        server_name = registry_entry.get("_server", "?")

        print(tool_running(tool_name, server_name), flush=True)

        start = time.time()
        try:
            raw_result = self.manager.call_tool(tool_name, arguments)
            elapsed = time.time() - start

            text = extract_text_from_result(raw_result)
            compressed = compress_output(text, self.max_output_lines)

            print(tool_done(tool_name, elapsed), flush=True)
            return compressed, elapsed

        except Exception as e:
            elapsed = time.time() - start
            msg = str(e)
            print(tool_error(tool_name, msg), flush=True)
            return f"ERROR: {msg}", elapsed
