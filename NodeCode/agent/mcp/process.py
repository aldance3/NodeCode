"""
mcp/process.py - Launch and manage an MCP server subprocess
"""

import os
import subprocess
import sys
from pathlib import Path


def start_process(command: str, args: list[str], env: dict[str, str] | None = None) -> subprocess.Popen:
    """
    Start an MCP server subprocess with stdin/stdout pipes.
    Expands environment variables in all args.
    Merges optional env dict on top of the current environment.
    """
    expanded_args = [os.path.expandvars(a) for a in args]
    expanded_cmd = os.path.expandvars(command)

    full_cmd = [expanded_cmd] + expanded_args

    # Build environment: start from current env, overlay server-specific vars
    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)

    proc = subprocess.Popen(
        full_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,  # binary mode for reliable line reading
        bufsize=0,
        env=proc_env,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    return proc
