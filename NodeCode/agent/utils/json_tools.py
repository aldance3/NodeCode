"""
utils/json_tools.py - JSON helpers
"""

import json
from typing import Any


def safe_dumps(obj: Any, **kwargs) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, **kwargs)
    except (TypeError, ValueError):
        return str(obj)


def safe_loads(text: str) -> Any | None:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None
