"""MCP server bootstrap.

Tool registration lives in ``productive_mcp.tools``: each module imports
``mcp`` from ``tools._registry`` and decorates its functions with
``@mcp.tool()``. This file imports each tool module to trigger the
side-effecting registration, then runs ``mcp`` over stdio.
"""

from __future__ import annotations

import os

# Importing the tool modules registers their @mcp.tool decorators against
# the shared FastMCP instance. The noqa marker keeps linters from
# stripping these "unused" imports.
from productive_mcp.tools import (  # noqa: F401
    companies,
    deals,
    health,
    people,
    services,
    tasks,
    time_entries,
)
from productive_mcp.tools._registry import mcp


def main() -> None:
    """Entry point for ``productive-mcp``. Runs over stdio."""
    missing = [
        name
        for name in ("PRODUCTIVE_API_TOKEN", "PRODUCTIVE_ORGANIZATION_ID")
        if not os.environ.get(name)
    ]
    if missing:
        names = ", ".join(missing)
        raise SystemExit(
            f"productive-mcp: missing required environment variable(s): {names}. "
            f"Set them before launching the server."
        )
    mcp.run()
