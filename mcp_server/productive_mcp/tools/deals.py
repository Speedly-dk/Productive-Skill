"""Read tools for /deals.

Productive's "deal" is what most other tools call a project. We use the
API's term throughout for clarity.
"""

from __future__ import annotations

from typing import Any

from productive_mcp.client import ProductiveClient
from productive_mcp.formatting import flatten_jsonapi, flatten_resource
from productive_mcp.tools._helpers import build_params, cap_max_results
from productive_mcp.tools._registry import mcp


async def _list(
    client: ProductiveClient,
    *,
    company_id: str | None = None,
    deal_type_id: int | None = None,
    extra_filters: dict[str, str] | None = None,
    include: list[str] | None = None,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    capped = cap_max_results(max_results)
    params = build_params(
        filters={"company_id": company_id, "deal_type_id": deal_type_id},
        extra_filters=extra_filters,
        include=include,
    )
    payload = await client.get("/deals", params=params, max_results=capped)
    return flatten_jsonapi(payload)


async def _get(
    client: ProductiveClient,
    *,
    deal_id: str,
    include: list[str] | None = None,
) -> dict[str, Any]:
    params = build_params(include=include)
    payload = await client.get(f"/deals/{deal_id}", params=params, max_results=1)
    if not payload["data"]:
        # Shouldn't reach here -- a 404 raises before we get this far.
        return {}
    included_index = {(r.get("type", ""), r.get("id", "")): r for r in payload["included"]}
    return flatten_resource(payload["data"][0], included_index=included_index)


@mcp.tool()
async def productive_list_deals(
    company_id: str | None = None,
    deal_type_id: int | None = None,
    include: list[str] | None = None,
    extra_filters: dict[str, str] | None = None,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    """List Productive deals (projects).

    Args:
        company_id: Optional client/company id to filter by.
        deal_type_id: Optional. Productive uses 1 = Internal, 2 = Client.
        include: Sideload list, e.g. ``["company"]``. When set, related
            resources are flattened into the deal dict.
        extra_filters: Escape hatch for filters not exposed above.
        max_results: Default 50, hard cap 500.
    """
    async with ProductiveClient() as client:
        return await _list(
            client,
            company_id=company_id,
            deal_type_id=deal_type_id,
            extra_filters=extra_filters,
            include=include,
            max_results=max_results,
        )


@mcp.tool()
async def productive_get_deal(
    deal_id: str,
    include: list[str] | None = None,
) -> dict[str, Any]:
    """Fetch a single deal by id.

    Args:
        deal_id: The Productive deal id.
        include: Sideload list, e.g. ``["company"]``.

    Returns:
        Compact dict with deal attributes and resolved relationships.
    """
    async with ProductiveClient() as client:
        return await _get(client, deal_id=deal_id, include=include)
