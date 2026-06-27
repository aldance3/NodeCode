"""
http_requests MCP server
Exposes a single flexible tool: http_request

Supports any HTTP method (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS).
The AI provides the URL, method, headers, query params, and body.
"""

import json
import sys
import urllib.request
import urllib.parse
import urllib.error
import ssl


# ── JSON-RPC helpers ──────────────────────────────────────────────────────────

def _send(obj: dict):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _ok(req_id, result):
    _send({"jsonrpc": "2.0", "id": req_id, "result": result})


def _err(req_id, code: int, message: str):
    _send({"jsonrpc": "2.0", "id": req_id,
           "error": {"code": code, "message": message}})


def _text(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}]}


# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "http_request",
        "description": (
            "Send an HTTP request to any URL using any method "
            "(GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS). "
            "Supports custom headers, query parameters, and a request body. "
            "Returns the response status, headers, and body."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Full URL including scheme, e.g. https://api.example.com/endpoint"
                },
                "method": {
                    "type": "string",
                    "description": "HTTP method: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS (default: GET)"
                },
                "headers": {
                    "type": "object",
                    "description": "Optional dict of request headers, e.g. {\"Authorization\": \"Bearer token\", \"Content-Type\": \"application/json\"}"
                },
                "params": {
                    "type": "object",
                    "description": "Optional dict of query string parameters appended to the URL, e.g. {\"page\": \"1\", \"limit\": \"10\"}"
                },
                "body": {
                    "type": "string",
                    "description": "Optional request body as a string. For JSON, serialize it yourself and set Content-Type: application/json"
                },
                "body_json": {
                    "type": "object",
                    "description": "Optional request body as a JSON object. Automatically serialized and sets Content-Type: application/json if not already set"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds (default: 30)"
                },
                "verify_ssl": {
                    "type": "boolean",
                    "description": "Whether to verify SSL certificates (default: true)"
                }
            },
            "required": ["url"]
        }
    }
]


# ── HTTP execution ────────────────────────────────────────────────────────────

def do_request(args: dict) -> str:
    url = args.get("url", "").strip()
    if not url:
        return "ERROR: url is required"

    method = args.get("method", "GET").upper().strip()
    headers = dict(args.get("headers") or {})
    params = args.get("params") or {}
    body_str = args.get("body") or None
    body_json = args.get("body_json") or None
    timeout = int(args.get("timeout") or 30)
    verify_ssl = args.get("verify_ssl", True)

    # Append query params to URL
    if params:
        encoded = urllib.parse.urlencode({str(k): str(v) for k, v in params.items()})
        sep = "&" if "?" in url else "?"
        url = url + sep + encoded

    # Build body bytes
    body_bytes = None
    if body_json is not None:
        body_bytes = json.dumps(body_json, ensure_ascii=False).encode("utf-8")
        if "content-type" not in {k.lower() for k in headers}:
            headers["Content-Type"] = "application/json"
    elif body_str is not None:
        body_bytes = body_str.encode("utf-8")

    # Default User-Agent
    if "user-agent" not in {k.lower() for k in headers}:
        headers["User-Agent"] = "OllamaCode-HTTP/1.0"

    # SSL context
    if not verify_ssl:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
    else:
        ssl_ctx = None

    req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)

    try:
        opener = urllib.request.build_opener()
        if ssl_ctx:
            import urllib.request as ur
            https_handler = ur.HTTPSHandler(context=ssl_ctx)
            opener = urllib.request.build_opener(https_handler)

        with opener.open(req, timeout=timeout) as resp:
            status = resp.status
            reason = resp.reason
            resp_headers = dict(resp.headers)
            raw = resp.read()

            # Try to decode body
            content_type = resp_headers.get("Content-Type", "")
            charset = "utf-8"
            if "charset=" in content_type:
                charset = content_type.split("charset=")[-1].split(";")[0].strip()

            try:
                body_text = raw.decode(charset, errors="replace")
            except (LookupError, UnicodeDecodeError):
                body_text = raw.decode("utf-8", errors="replace")

            # Pretty-print JSON response if applicable
            if "application/json" in content_type:
                try:
                    parsed = json.loads(body_text)
                    body_text = json.dumps(parsed, indent=2, ensure_ascii=False)
                except (json.JSONDecodeError, ValueError):
                    pass

            # Truncate very large responses
            max_chars = 12000
            truncated = ""
            if len(body_text) > max_chars:
                truncated = f"\n\n[... {len(body_text) - max_chars} chars truncated ...]"
                body_text = body_text[:max_chars]

            # Format response headers (trim to useful ones)
            useful_headers = {
                k: v for k, v in resp_headers.items()
                if k.lower() in {
                    "content-type", "content-length", "x-request-id",
                    "x-ratelimit-remaining", "x-ratelimit-limit",
                    "location", "server", "date", "etag",
                }
            }
            headers_str = "\n".join(f"  {k}: {v}" for k, v in useful_headers.items())

            return (
                f"Status: {status} {reason}\n"
                f"URL: {url}\n"
                f"Method: {method}\n"
                + (f"Response Headers:\n{headers_str}\n" if headers_str else "")
                + f"\nBody:\n{body_text}{truncated}"
            )

    except urllib.error.HTTPError as e:
        # Still read the error body — often contains useful info
        try:
            err_body = e.read().decode("utf-8", errors="replace")[:3000]
        except Exception:
            err_body = "(could not read error body)"
        return (
            f"HTTP Error: {e.code} {e.reason}\n"
            f"URL: {url}\n"
            f"Method: {method}\n"
            f"\nError Body:\n{err_body}"
        )

    except urllib.error.URLError as e:
        return f"Connection error: {e.reason}\nURL: {url}"

    except TimeoutError:
        return f"Request timed out after {timeout}s\nURL: {url}"

    except Exception as e:
        return f"Unexpected error: {type(e).__name__}: {e}\nURL: {url}"


# ── Main loop ─────────────────────────────────────────────────────────────────

def handle(msg: dict):
    method = msg.get("method", "")
    req_id = msg.get("id")
    params = msg.get("params", {})

    if method == "initialize":
        _ok(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "http_requests", "version": "1.0.0"},
        })

    elif method == "notifications/initialized":
        pass

    elif method == "tools/list":
        _ok(req_id, {"tools": TOOLS})

    elif method == "tools/call":
        tool_name = params.get("name", "")
        args = params.get("arguments", {})

        if tool_name == "http_request":
            result = do_request(args)
            _ok(req_id, _text(result))
        else:
            _err(req_id, -32601, f"Unknown tool: {tool_name}")

    elif method == "ping":
        _ok(req_id, {})

    else:
        if req_id is not None:
            _err(req_id, -32601, f"Method not found: {method}")


def main():
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
