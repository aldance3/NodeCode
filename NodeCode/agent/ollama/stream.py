"""
ollama/stream.py - Handle streaming responses from Ollama
"""

import json
from typing import Generator, IO


def iter_streamed_tokens(response) -> Generator[str, None, None]:
    """
    Yields text tokens from a streaming Ollama /api/chat response.
    response is a requests.Response with stream=True.
    """
    for line in response.iter_lines():
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = obj.get("message", {})
        content = message.get("content", "")
        if content:
            yield content
        if obj.get("done", False):
            break
