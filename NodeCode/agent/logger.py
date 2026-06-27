"""
logger.py - Session logging to JSONL
"""

import json
import os
from datetime import datetime
from pathlib import Path


class Logger:
    def __init__(self, log_dir: str = "logs"):
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = Path(log_dir) / f"session_{ts}.jsonl"
        self._write({"event": "session_start", "timestamp": ts})

    def _write(self, obj: dict):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def log(self, event: str, **kwargs):
        entry = {"event": event, "timestamp": datetime.now().isoformat(), **kwargs}
        self._write(entry)

    def log_user(self, message: str):
        self.log("user_message", content=message)

    def log_assistant(self, message: str):
        self.log("assistant_message", content=message)

    def log_tool_call(self, tool: str, arguments: dict):
        self.log("tool_call", tool=tool, arguments=arguments)

    def log_tool_result(self, tool: str, result: str, elapsed: float):
        self.log("tool_result", tool=tool, result=result[:2000], elapsed=elapsed)

    def log_error(self, error: str, context: str = ""):
        self.log("error", error=error, context=context)
