# mcp_servers_default — Built-in MCP Servers

These servers are always loaded automatically. Do not delete this folder.

## Included servers

| Folder         | Tools                  | Notes                                      |
|----------------|------------------------|--------------------------------------------|
| google_search  | search, fetch_page     | Free via DuckDuckGo. Set SERPAPI_KEY env var for Google results. |

## Adding more default servers

Same format as `mcp_servers/` — add a subfolder with a `server_config.json`.

## google_search — optional upgrade

By default the search tool uses DuckDuckGo (no key needed).
To get real Google results, sign up at https://serpapi.com (free tier available)
and add to your `mcp_config.json`:

```json
{
  "mcpServers": {},
  "defaults_env": {
    "google_search": {
      "SERPAPI_KEY": "your_key_here"
    }
  }
}
```

Or just set the environment variable before launching:
```
set SERPAPI_KEY=your_key_here
python main.py
```
