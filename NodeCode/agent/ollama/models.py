"""
ollama/models.py - Pydantic models / data classes for Ollama API
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OllamaMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class OllamaRequest:
    model: str
    messages: list[OllamaMessage]
    stream: bool = True
    options: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in self.messages],
            "stream": self.stream,
            "options": self.options,
        }
