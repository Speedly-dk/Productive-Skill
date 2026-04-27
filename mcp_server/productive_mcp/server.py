"""MCP server bootstrap.

Registers the operational ``productive_health`` tool. Resource tools land
in U3/U4 and register through ``register_tools(mcp, client)``.
"""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from productive_mcp.client import (
    BASE_URL,
    ConfigError,
    ProductiveAPIError,
    ProductiveClient,
)

mcp = FastMCP("productive")


def _build_client() -> ProductiveClient:
    return ProductiveClient()


@mcp.tool()
async def productive_health() -> dict[str, object]:
    """Verify the Productive MCP server can reach the API.

    Returns a small dict describing the configured organization, the base
    URL, and a hint about whether the current token has read-write access.
    Use this as a pre-flight check after install.
    """
    try:
        client = _build_client()
    except ConfigError as exc:
        return {"ok": False, "error": str(exc)}

    async with client:
        token_scope_hint = "unknown"
        try:
            await client.get("/people/me", max_results=1)
            token_scope_hint = "valid"
        except ProductiveAPIError as exc:
            return {
                "ok": False,
                "organization_id": client.organization_id,
                "base_url": client.base_url,
                "error": str(exc),
            }

        return {
            "ok": True,
            "organization_id": client.organization_id,
            "base_url": client.base_url,
            "token_scope_hint": token_scope_hint,
            "version": _read_version(),
        }


def _read_version() -> str:
    from productive_mcp import __version__

    return __version__


def main() -> None:
    """Entry point for ``productive-mcp``. Runs over stdio."""
    # Surface configuration problems before starting the transport so users
    # see the env-var error rather than an opaque "server died" message.
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
