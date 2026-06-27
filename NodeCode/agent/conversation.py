"""
conversation.py - Conversation history management
"""

from typing import Any


class Conversation:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.messages: list[dict[str, Any]] = []

    def add_user(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def add_tool_result(self, tool_name: str, result: str):
        # Inject tool result as a user message so Ollama sees it
        self.messages.append({
            "role": "user",
            "content": f"[Tool Result: {tool_name}]\n{result}"
        })

    def get_messages(self) -> list[dict]:
        return self.messages

    def clear(self):
        self.messages = []

    def to_ollama_payload(self) -> list[dict]:
        """Return messages list for Ollama API (system is separate)."""
        return self.messages
