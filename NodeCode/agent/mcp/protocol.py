"""
mcp/protocol.py - JSON-RPC 2.0 over stdio for MCP
"""

import json
import threading
from typing import Any


class MCPProtocol:
    """
    Handles JSON-RPC 2.0 messaging over subprocess stdin/stdout.
    Thread-safe request/response matching via id-based pending dict.
    """

    def __init__(self, proc):
        self.proc = proc
        self._id = 0
        self._lock = threading.Lock()
        self._pending: dict[int, Any] = {}
        self._pending_events: dict[int, threading.Event] = {}
        self._responses: dict[int, dict] = {}
        self._reader_thread = threading.Thread(target=self._reader, daemon=True)
        self._reader_thread.start()

    def _next_id(self) -> int:
        with self._lock:
            self._id += 1
            return self._id

    def _reader(self):
        """Background thread: read lines from stdout, dispatch responses."""
        while True:
            try:
                line = self.proc.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg_id = msg.get("id")
                if msg_id is not None and msg_id in self._pending_events:
                    self._responses[msg_id] = msg
                    self._pending_events[msg_id].set()
            except Exception:
                break

    def send_request(self, method: str, params: dict | None = None, timeout: float = 30.0) -> dict:
        req_id = self._next_id()
        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params or {},
        }
        event = threading.Event()
        self._pending_events[req_id] = event

        payload = json.dumps(request, ensure_ascii=False) + "\n"
        self.proc.stdin.write(payload.encode("utf-8"))
        self.proc.stdin.flush()

        if not event.wait(timeout=timeout):
            del self._pending_events[req_id]
            raise TimeoutError(f"MCP request '{method}' timed out after {timeout}s")

        response = self._responses.pop(req_id)
        del self._pending_events[req_id]

        if "error" in response:
            err = response["error"]
            raise RuntimeError(f"MCP error: {err.get('message', err)}")

        return response.get("result", {})

    def send_notification(self, method: str, params: dict | None = None):
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
        }
        payload = json.dumps(notification, ensure_ascii=False) + "\n"
        self.proc.stdin.write(payload.encode("utf-8"))
        self.proc.stdin.flush()
