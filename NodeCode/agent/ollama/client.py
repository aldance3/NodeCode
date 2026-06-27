"""
ollama/client.py - Ollama API client
"""

import json
import requests
from typing import Generator

from ollama.models import OllamaMessage
from ollama.stream import iter_streamed_tokens


class OllamaClient:
    def __init__(self, base_url: str, model: str, temperature: float = 0.2,
                 context_size: int = 32768):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.context_size = context_size
        self.chat_url = f"{self.base_url}/api/chat"

    def _build_payload(self, system_prompt: str, messages: list[dict],
                       stream: bool) -> dict:
        all_messages = [{"role": "system", "content": system_prompt}] + messages
        return {
            "model": self.model,
            "messages": all_messages,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.context_size,
            },
        }

    def chat_stream(self, system_prompt: str,
                    messages: list[dict]) -> Generator[str, None, None]:
        payload = self._build_payload(system_prompt, messages, stream=True)
        resp = requests.post(
            self.chat_url,
            json=payload,
            stream=True,
            timeout=120,
        )
        resp.raise_for_status()
        yield from iter_streamed_tokens(resp)

    def chat(self, system_prompt: str, messages: list[dict]) -> str:
        payload = self._build_payload(system_prompt, messages, stream=False)
        resp = requests.post(
            self.chat_url,
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")

    def list_models(self) -> list[str]:
        resp = requests.get(f"{self.base_url}/api/tags", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return [m["name"] for m in data.get("models", [])]
