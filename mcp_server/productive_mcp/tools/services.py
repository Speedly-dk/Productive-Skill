"""Read tools for /services."""

from __future__ import annotations

from typing import Any

from productive_mcp.client import ProductiveClient
from productive_mcp.formatting import flatten_jsonapi
from productive_mcp.tools._helpers import build_params, cap_max_results
from productive_mcp.tools._registry import mcp


async def _list(
    client: ProductiveClient,
    *,
    deal_id: str | None = None,
    extra_filters: dict[str, str] | None = None,
    include: list[str] | None = None,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    capped = cap_max_results(max_results)
    params = build_params(
        filters={"deal_id": deal_id},
        extra_filters=extra_filters,
        include=include,
    )
    payload = await client.get("/services", params=params, max_results=capped)
    return flatten_jsonapi(payload)


@mcp.tool()
async def productive_list_services(
    deal_id: str | None = None,
    include: list[str] | None = None,
    extra_filters: dict[str, str] | None = None,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    """List services within a deal (or across all deals).

    Args:
        deal_id: Optional deal id to scope results.
        include: Sideload list, e.g. ``["deal"]``.
        extra_filters: Escape hatch for filters not exposed above.
        max_results: Default 50, hard cap 500.
    """
    async with ProductiveClient() as client:
        return await _list(
            client,
            deal_id=deal_id,
            extra_filters=extra_filters,
            include=include,
            max_results=max_results,
        )
