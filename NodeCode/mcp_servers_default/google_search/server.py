"""
google_search MCP server
Provides web search via SerpAPI (if SERPAPI_KEY is set) or
DuckDuckGo HTML scraping as a free fallback.

Tools exposed:
  - search(query, num_results?)
  - fetch_page(url)
"""

import json
import sys
import os
import urllib.request
import urllib.parse
import urllib.error
import html
import re


# ── JSON-RPC helpers ──────────────────────────────────────────────────────────

def _send(obj: dict):
    line = json.dumps(obj, ensure_ascii=False) + "\n"
    sys.stdout.write(line)
    sys.stdout.flush()


def _ok(req_id, result):
    _send({"jsonrpc": "2.0", "id": req_id, "result": result})


def _err(req_id, code: int, message: str):
    _send({"jsonrpc": "2.0", "id": req_id,
           "error": {"code": code, "message": message}})


def _text_content(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}]}


# ── Search backends ───────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _serpapi_search(query: str, num: int) -> list[dict]:
    key = os.environ.get("SERPAPI_KEY", "")
    params = urllib.parse.urlencode({
        "q": query,
        "num": num,
        "api_key": key,
        "engine": "google",
    })
    url = f"https://serpapi.com/search?{params}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    results = []
    for r in data.get("organic_results", [])[:num]:
        results.append({
            "title": r.get("title", ""),
            "url": r.get("link", ""),
            "snippet": r.get("snippet", ""),
        })
    return results


def _ddg_search(query: str, num: int) -> list[dict]:
    """DuckDuckGo HTML scrape — no API key needed."""
    params = urllib.parse.urlencode({"q": query, "kl": "us-en"})
    url = f"https://html.duckduckgo.com/html/?{params}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = resp.read().decode("utf-8", errors="replace")

    results = []
    # Extract result blocks
    blocks = re.findall(
        r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?'
        r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
        body, re.DOTALL
    )
    for href, title_raw, snippet_raw in blocks[:num]:
        title = html.unescape(re.sub(r"<[^>]+>", "", title_raw)).strip()
        snippet = html.unescape(re.sub(r"<[^>]+>", "", snippet_raw)).strip()
        # DDG wraps URLs — unwrap if needed
        if href.startswith("//duckduckgo.com/l/?"):
            m = re.search(r"uddg=([^&]+)", href)
            if m:
                href = urllib.parse.unquote(m.group(1))
        results.append({"title": title, "url": href, "snippet": snippet})

    return results


def do_search(query: str, num_results: int = 8) -> str:
    num_results = max(1, min(num_results, 20))
    serpapi_key = os.environ.get("SERPAPI_KEY", "")

    try:
        if serpapi_key:
            results = _serpapi_search(query, num_results)
            source = "Google (SerpAPI)"
        else:
            results = _ddg_search(query, num_results)
            source = "DuckDuckGo"
    except Exception as e:
        return f"Search error: {e}"

    if not results:
        return "No results found."

    lines = [f"Search results for: {query!r}  [{source}]\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   {r['url']}")
        if r.get("snippet"):
            lines.append(f"   {r['snippet']}")
        lines.append("")
    return "\n".join(lines)


def do_fetch_page(url: str, max_chars: int = 8000) -> str:
    """Fetch a URL and return readable plain text."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "html" not in content_type and "text" not in content_type:
                return f"Cannot read content type: {content_type}"
            body = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"Fetch error: {e}"

    # Strip scripts/styles
    body = re.sub(r"<script[^>]*>.*?</script>", " ", body, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r"<style[^>]*>.*?</style>", " ", body, flags=re.DOTALL | re.IGNORECASE)
    # Strip tags
    body = re.sub(r"<[^>]+>", " ", body)
    # Decode entities
    body = html.unescape(body)
    # Collapse whitespace
    body = re.sub(r"\s{2,}", "\n", body).strip()

    if len(body) > max_chars:
        half = max_chars // 2
        body = body[:half] + f"\n\n... [truncated {len(body)-max_chars} chars] ...\n\n" + body[-half:]

    return body


# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "search",
        "description": (
            "Search the web and return titles, URLs, and snippets. "
            "Uses Google via SerpAPI if SERPAPI_KEY env var is set, "
            "otherwise uses DuckDuckGo for free."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-20, default 8)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "fetch_page",
        "description": "Fetch a webpage by URL and return its plain text content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL to fetch"
                }
            },
            "required": ["url"]
        }
    }
]


# ── Main loop ─────────────────────────────────────────────────────────────────

def handle(msg: dict):
    method = msg.get("method", "")
    req_id = msg.get("id")
    params = msg.get("params", {})

    if method == "initialize":
        _ok(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "google_search", "version": "1.0.0"},
        })

    elif method == "notifications/initialized":
        pass  # no response needed

    elif method == "tools/list":
        _ok(req_id, {"tools": TOOLS})

    elif method == "tools/call":
        tool_name = params.get("name", "")
        args = params.get("arguments", {})

        if tool_name == "search":
            query = args.get("query", "")
            num = int(args.get("num_results", 8))
            if not query:
                _err(req_id, -32602, "Missing required argument: query")
                return
            result = do_search(query, num)
            _ok(req_id, _text_content(result))

        elif tool_name == "fetch_page":
            url = args.get("url", "")
            if not url:
                _err(req_id, -32602, "Missing required argument: url")
                return
            result = do_fetch_page(url)
            _ok(req_id, _text_content(result))

        else:
            _err(req_id, -32601, f"Unknown tool: {tool_name}")

    elif method == "ping":
        _ok(req_id, {})

    else:
        if req_id is not None:
            _err(req_id, -32601, f"Method not found: {method}")


def main():
    # Use binary stdin to avoid Windows line-ending issues, decode manually
    stdin = open(sys.stdin.fileno(), "rb", buffering=0)
    for raw_line in stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        try:
            handle(msg)
        except Exception as e:
            req_id = msg.get("id")
            if req_id is not None:
                _err(req_id, -32603, f"Internal error: {e}")


if __name__ == "__main__":
    main()
