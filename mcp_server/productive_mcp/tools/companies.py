"""Read tools for /companies."""

from __future__ import annotations

from typing import Any

from productive_mcp.client import ProductiveClient
from productive_mcp.formatting import flatten_jsonapi
from productive_mcp.tools._helpers import build_params, cap_max_results
from productive_mcp.tools._registry import mcp


async def _list(
    client: ProductiveClient,
    *,
    name: str | None = None,
    extra_filters: dict[str, str] | None = None,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    capped = cap_max_results(max_results)
    params = build_params(filters={"name": name}, extra_filters=extra_filters)
    payload = await client.get("/companies", params=params, max_results=capped)
    return flatten_jsonapi(payload)


@mcp.tool()
async def productive_list_companies(
    name: str | None = None,
    extra_filters: dict[str, str] | None = None,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    """List companies (clients).

    Args:
        name: Optional name filter (matches Productive's name field).
        extra_filters: Escape hatch for filters not exposed above.
        max_results: Default 50, hard cap 500.
    """
    async with ProductiveClient() as client:
        return await _list(
            client,
            name=name,
            extra_filters=extra_filters,
            max_results=max_results,
        )
