"""
agent.py - Core agent loop
"""

import sys
import time
from typing import Any

from ollama.client import OllamaClient
from mcp.manager import MCPManager
from mcp.tool_executor import ToolExecutor
from conversation import Conversation
from json_parser import extract_tool_calls, strip_tool_call_json
from logger import Logger
from utils.colors import assistant_prefix, tool_running, info, error as color_error, dim


class Agent:
    def __init__(
        self,
        ollama: OllamaClient,
        mcp_manager: MCPManager,
        system_prompt: str,
        logger: Logger,
        max_output_lines: int = 200,
    ):
        self.ollama = ollama
        self.mcp_manager = mcp_manager
        self.system_prompt = system_prompt
        self.logger = logger
        self.executor = ToolExecutor(mcp_manager, max_output_lines)
        self.conversation = Conversation(system_prompt)

    def run_turn(self, user_input: str):
        """Process a single user turn through the full agent loop."""
        self.conversation.add_user(user_input)
        self.logger.log_user(user_input)

        iteration = 0
        while True:
            iteration += 1

            # Stream response from model
            print(f"\n{assistant_prefix()}", end="", flush=True)
            full_response = ""
            try:
                for token in self.ollama.chat_stream(
                    self.system_prompt,
                    self.conversation.get_messages(),
                ):
                    print(token, end="", flush=True)
                    full_response += token
            except Exception as e:
                print(color_error(f"\nOllama error: {e}"), flush=True)
                self.logger.log_error(str(e), context="ollama_stream")
                break

            print(flush=True)
            self.logger.log_assistant(full_response)

            # Check for tool calls
            tool_calls = extract_tool_calls(full_response)

            if not tool_calls:
                # No tools → final answer, end loop
                clean = strip_tool_call_json(full_response)
                self.conversation.add_assistant(full_response)
                break

            # Add assistant message (with the raw JSON) to history
            self.conversation.add_assistant(full_response)

            # Execute each tool
            any_success = False
            for call in tool_calls:
                tool_name = call.get("tool", "")
                arguments = call.get("arguments", {})

                if not tool_name:
                    continue

                self.logger.log_tool_call(tool_name, arguments)

                result, elapsed = self.executor.execute(tool_name, arguments)
                self.logger.log_tool_result(tool_name, result, elapsed)

                # Feed result back into conversation
                self.conversation.add_tool_result(tool_name, result)
                any_success = True

            if not any_success:
                # Couldn't execute anything — break to avoid infinite loop
                break

    def slash_command(self, cmd: str) -> bool:
        """Handle slash commands. Returns True if handled."""
        cmd = cmd.strip().lower()

        if cmd == "/help":
            print(info(
                "\nSlash commands:\n"
                "  /help          - Show this help\n"
                "  /tools         - List all available tools\n"
                "  /clear         - Clear conversation history\n"
                "  /history       - Show conversation summary\n"
                "  /models        - List available Ollama models\n"
                "  /model <name>  - Switch to a different model\n"
                "  /exit          - Exit the agent\n"
            ))
            return True

        if cmd == "/tools":
            from utils.formatting import format_tool_list
            print(info("\nAvailable tools:"))
            print(format_tool_list(self.mcp_manager.get_tool_registry()))
            print()
            return True

        if cmd == "/clear":
            self.conversation.clear()
            print(info("Conversation cleared.\n"))
            return True

        if cmd == "/history":
            msgs = self.conversation.get_messages()
            print(info(f"\nConversation: {len(msgs)} messages\n"))
            for i, m in enumerate(msgs):
                role = m["role"].upper()
                content = m["content"][:100].replace("\n", " ")
                print(dim(f"  [{i}] {role}: {content}..."))
            print()
            return True

        if cmd == "/models":
            try:
                models = self.ollama.list_models()
                print(info(f"\nAvailable models (current: {self.ollama.model}):"))
                for m in models:
                    marker = " ◀ active" if m == self.ollama.model else ""
                    print(f"  {m}{info(marker)}")
                print()
            except Exception as e:
                print(color_error(f"Could not list models: {e}"))
            return True

        if cmd.startswith("/model "):
            new_model = cmd[len("/model "):].strip()
            if not new_model:
                print(color_error("Usage: /model <model_name>"))
                return True
            old_model = self.ollama.model
            self.ollama.model = new_model
            print(info(f"Model switched: {old_model} → {new_model}"))
            self.logger.log("model_switch", old=old_model, new=new_model)
            print(dim("  Tip: use /models to list available models\n"))
            return True

        if cmd in ("/exit", "/quit"):
            print(info("Goodbye!"))
            sys.exit(0)

        return False
