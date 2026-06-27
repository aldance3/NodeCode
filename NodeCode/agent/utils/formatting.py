"""
utils/formatting.py - Pretty formatting helpers
"""


def format_tool_list(tool_registry: dict) -> str:
    if not tool_registry:
        return "  (no tools discovered)"
    lines = []
    for name in sorted(tool_registry.keys()):
        desc = tool_registry[name].get("description", "")
        short = desc[:70] + "..." if len(desc) > 70 else desc
        lines.append(f"  {name:<40} {short}")
    return "\n".join(lines)


def truncate(text: str, max_chars: int = 300) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"... [{len(text)-max_chars} more chars]"
