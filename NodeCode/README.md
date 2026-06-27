# Ollama Code Agent

A local Claude Code-style agent powered by **Ollama** + **MCP servers**.

## Setup

1. **Install dependencies:**
   ```
   install.bat
   ```
   or manually: `pip install -r requirements.txt`

2. **Edit the mcp_config.json With your preferred MCP servers & local ai server IP.

3. **Run:**
   ```
   run.bat
   ```
   or: `python main.py`

---

## mcp_config.json format

```json
{
  "server": {
    "host": "192.168.50.12",
    "port": 11434
  },
  "model": "qwen2.5-coder:14b",
  "temperature": 0.2,
  "context_size": 32768,
  "max_output_lines": 200,
  "mcpServers": {
    "cmd-mcp-server": {
      "command": "C:\\Python312\\python.exe",
      "args": ["C:\\path\\to\\server.py"]
    },
    "github-local": {
      "command": "C:\\Python312\\python.exe",
      "args": ["C:\\path\\to\\github_server.py"]
    },
    "Roblox_Studio": {
      "command": "cmd.exe",
      "args": ["/c", "%LOCALAPPDATA%\\Roblox\\mcp.bat"]
    }
  }
}
```

Environment variables like `%LOCALAPPDATA%` are automatically expanded.

---

## CLI Options

```
python main.py --help
python main.py --config path/to/other_config.json
python main.py --model llama3.1:8b
python main.py --no-mcp
```

---

## Slash Commands

| Command    | Action                         |
|------------|-------------------------------|
| `/help`    | Show help                     |
| `/tools`   | List all available tools      |
| `/clear`   | Clear conversation history    |
| `/history` | Show message history summary  |
| `/models`  | List Ollama models            |
| `/exit`    | Exit                          |

---

## Tool Calling

The model emits tool calls as JSON:

```json
{
  "tool_calls": [
    {
      "tool": "server_name.tool_name",
      "arguments": { "key": "value" }
    }
  ]
}
```

The agent automatically executes them and feeds results back.

---

## Project Structure

```
Ollama Code/
├── main.py              ← Entry point
├── requirements.txt
├── run.bat
├── install.bat
├── mcp_config.json      ← Your config (bring your own)
└── agent/
    ├── agent.py         ← Agent loop
    ├── config.py        ← Config loader
    ├── conversation.py  ← History management
    ├── prompt_builder.py← Dynamic system prompt
    ├── json_parser.py   ← Tool call extraction
    ├── logger.py        ← JSONL session logging
    ├── logs/            ← Log files
    ├── ollama/
    │   ├── client.py    ← Ollama REST client
    │   ├── stream.py    ← Streaming support
    │   └── models.py    ← Data models
    ├── mcp/
    │   ├── process.py   ← Subprocess launcher
    │   ├── protocol.py  ← JSON-RPC over stdio
    │   ├── client.py    ← Per-server MCP client
    │   ├── manager.py   ← Multi-server manager
    │   └── tool_executor.py ← Tool dispatch + compression
    └── utils/
        ├── colors.py    ← Terminal colors
        ├── compression.py ← Output truncation
        ├── formatting.py
        └── json_tools.py
```
