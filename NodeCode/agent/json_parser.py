"""
json_parser.py - Robustly extract JSON tool_calls from model output
"""

import json
import re
from typing import Any


def _try_parse_tool_calls(text: str) -> list[dict] | None:
    """Try to parse text as JSON and return tool_calls if present."""
    text = text.strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and "tool_calls" in obj:
            calls = obj["tool_calls"]
            if isinstance(calls, list) and len(calls) > 0:
                return calls
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def _extract_json_objects(text: str) -> list[str]:
    """
    Extract all {...} blobs from text using a brace-depth scanner.
    More reliable than regex for nested JSON.
    """
    results = []
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start != -1:
                results.append(text[start:i+1])
                start = -1
    return results


def extract_tool_calls(text: str) -> list[dict[str, Any]] | None:
    """
    Find and parse tool_calls JSON from model output.
    Handles: fenced code blocks, raw JSON, prose-wrapped JSON,
    and partial matches anywhere in the text.
    """
    # 1. Try fenced code blocks first (```json ... ``` or ``` ... ```)
    fenced = re.findall(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    for candidate in fenced:
        result = _try_parse_tool_calls(candidate)
        if result is not None:
            return result

    # 2. Use brace scanner to find all JSON objects in the text
    blobs = _extract_json_objects(text)
    for blob in blobs:
        result = _try_parse_tool_calls(blob)
        if result is not None:
            return result

    # 3. Last resort: find anything after a bare { that contains "tool_calls"
    if '"tool_calls"' in text:
        # Try the whole text from first { to last }
        first = text.find('{')
        last = text.rfind('}')
        if first != -1 and last != -1 and last > first:
            candidate = text[first:last+1]
            result = _try_parse_tool_calls(candidate)
            if result is not None:
                return result

    return None


def strip_tool_call_json(text: str) -> str:
    """Remove JSON tool_call blocks from the text for cleaner display."""
    # Remove fenced blocks containing tool_calls
    text = re.sub(r"```(?:json)?\s*\{[^`]*\"tool_calls\"[^`]*\}\s*```", "", text, flags=re.DOTALL)
    # Remove bare JSON objects containing tool_calls
    blobs = _extract_json_objects(text)
    for blob in blobs:
        if '"tool_calls"' in blob:
            text = text.replace(blob, "", 1)
    return text.strip()
