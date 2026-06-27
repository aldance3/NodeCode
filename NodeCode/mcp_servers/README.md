# mcp_servers — Custom MCP Servers

Drop your own MCP servers here. Each server should be in its own subfolder
containing a `server_config.json` that describes how to launch it.

## Folder structure

```
mcp_servers/
└── my_server/
    ├── server_config.json   ← required
    └── server.py            ← (or whatever your server is)
```

## server_config.json format

```json
{
  "command": "python",
  "args": ["server.py"],
  "env": {
    "MY_API_KEY": "optional_key_here"
  }
}
```

- `command` — executable to run (supports `%ENV_VARS%`)
- `args` — list of arguments (supports `%ENV_VARS%`)
- `env` — optional extra environment variables injected into the server process

The server name shown in the agent will be the folder name (e.g. `my_server.tool_name`).

## Notes

- Servers here are loaded **in addition to** `mcp_config.json` and `mcp_servers_default/`.
- If a name conflicts with one in `mcp_config.json`, the config file wins.
- You can disable a server by adding `"disabled": true` to its `server_config.json`.
