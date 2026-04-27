"""Operational health check tool."""

from __future__ import annotations

from productive_mcp import __version__
from productive_mcp.client import ConfigError, ProductiveAPIError, ProductiveClient
from productive_mcp.tools._registry import mcp


@mcp.tool()
async def productive_health() -> dict[str, object]:
    """Verify the Productive MCP server can reach the API.

    Returns a small dict describing the configured organization, the base
    URL, and a hint about whether the current token has read-write access.
    Use this as a pre-flight check after install or when troubleshooting.
    """
    try:
        client = ProductiveClient()
    except ConfigError as exc:
        return {"ok": False, "error": str(exc)}

    async with client:
        try:
            await client.get("/people/me", max_results=1)
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
            "token_scope_hint": "valid",
            "version": __version__,
        }
