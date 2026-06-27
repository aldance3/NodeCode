"""
prompt_builder.py - Build system prompt from discovered tools
"""

import json
from typing import Any


def build_system_prompt(tool_registry: dict[str, dict]) -> str:
    lines = [
        "You are a powerful coding and systems agent, similar to Claude Code.",
        "You have access to tools you MUST use to answer requests that require real data.",
        "",
        "## CRITICAL: Tool Calling Format",
        "",
        "When you need to call a tool, you MUST output ONLY a raw JSON object like this",
        "(no prose before or after, no markdown fences, just the JSON):",
        "",
        '{',
        '  "tool_calls": [',
        '    {',
        '      "tool": "server.tool_name",',
        '      "arguments": {',
        '        "arg1": "value1"',
        '      }',
        '    }',
        '  ]',
        '}',
        "",
        "After the tool runs, you will receive the result and can continue.",
        "Only give your final answer AFTER you have received tool results.",
        "",
        "Rules:",
        "- If a task requires a tool, OUTPUT THE JSON IMMEDIATELY. Do not describe what you are about to do.",
        "- NEVER invent tool names or argument names not listed below.",
        "- NEVER say 'I will call X' — just call it.",
        "- You may call multiple tools in one response.",
        "- Stop calling tools when you have enough information to answer.",
        "",
        "## Available Tools",
        "",
    ]

    if not tool_registry:
        lines.append("(No tools available)")
    else:
        for full_name, info in sorted(tool_registry.items()):
            lines.append(f"### {full_name}")
            desc = info.get("description", "No description.")
            lines.append(f"Description: {desc}")
            schema = info.get("inputSchema", {})
            props = schema.get("properties", {})
            required = schema.get("required", [])
            if props:
                args_doc = {}
                for pname, pinfo in props.items():
                    ptype = pinfo.get("type", "any")
                    pdesc = pinfo.get("description", "")
                    req = " (required)" if pname in required else " (optional)"
                    args_doc[pname] = f"{ptype}{req} - {pdesc}" if pdesc else f"{ptype}{req}"
                lines.append("Arguments:")
                lines.append(json.dumps(args_doc, indent=2))
            else:
                lines.append("Arguments: none")
            lines.append("")

    return "\n".join(lines)
