"""
utils/compression.py - Truncate large tool outputs to fit context
"""


def compress_output(text: str, max_lines: int = 200) -> str:
    """
    If output exceeds max_lines*2, keep first and last max_lines lines
    and insert a summary of omitted lines in between.
    """
    if not text:
        return text

    lines = text.splitlines()
    total = len(lines)

    if total <= max_lines * 2:
        return text

    head = lines[:max_lines]
    tail = lines[-max_lines:]
    omitted = total - max_lines * 2

    result = "\n".join(head)
    result += f"\n\n... [{omitted} lines omitted] ...\n\n"
    result += "\n".join(tail)
    return result


def format_tool_result(stdout: str, stderr: str, exit_code: int | None,
                       max_lines: int = 200) -> str:
    parts = []
    if stdout:
        compressed = compress_output(stdout, max_lines)
        parts.append(f"stdout:\n{compressed}")
    if stderr:
        compressed = compress_output(stderr, max_lines)
        parts.append(f"stderr:\n{compressed}")
    if exit_code is not None:
        parts.append(f"exit_code: {exit_code}")
    return "\n\n".join(parts) if parts else "(no output)"
