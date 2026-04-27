"""Read tools for /time_entries."""

from __future__ import annotations

from typing import Any

from productive_mcp.client import ProductiveClient
from productive_mcp.formatting import flatten_jsonapi
from productive_mcp.tools._helpers import (
    DEFAULT_TIME_ENTRY_RESULTS,
    build_params,
    cap_max_results,
)
from productive_mcp.tools._registry import mcp


async def _search(
    client: ProductiveClient,
    *,
    after: str,
    before: str,
    person_id: str | None = None,
    deal_id: str | None = None,
    include: list[str] | None = None,
    extra_filters: dict[str, str] | None = None,
    max_results: int = DEFAULT_TIME_ENTRY_RESULTS,
) -> list[dict[str, Any]]:
    capped = cap_max_results(max_results, default=DEFAULT_TIME_ENTRY_RESULTS)
    params = build_params(
        filters={"after": after, "before": before, "person_id": person_id, "deal_id": deal_id},
        extra_filters=extra_filters,
        include=include,
    )
    payload = await client.get("/time_entries", params=params, max_results=capped)
    return flatten_jsonapi(payload)


@mcp.tool()
async def productive_search_time_entries(
    after: str,
    before: str,
    person_id: str | None = None,
    deal_id: str | None = None,
    include: list[str] | None = None,
    extra_filters: dict[str, str] | None = None,
    max_results: int = DEFAULT_TIME_ENTRY_RESULTS,
) -> list[dict[str, Any]]:
    """Search time entries within a date range.

    Args:
        after: Inclusive lower bound, YYYY-MM-DD.
        before: Inclusive upper bound, YYYY-MM-DD.
        person_id: Optional Productive person id to filter by.
        deal_id: Optional Productive deal id to filter by.
        include: JSON:API sideload list, e.g. ``["person", "service", "task"]``.
            When set, related resources are flattened into ``person`` /
            ``service`` / ``task`` fields on each entry.
        extra_filters: Escape hatch for filters not exposed above
            (each key is sent as ``filter[<key>]=<value>``).
        max_results: Maximum entries to return. Default 200, hard cap 500.
            Pagination short-circuits at this count -- pages are not fetched
            and discarded.

    Returns:
        List of compact dicts. Each entry has id, date, time (minutes),
        billable_time, note, and *_id fields for relationships.
    """
    async with ProductiveClient() as client:
        return await _search(
            client,
            after=after,
            before=before,
            person_id=person_id,
            deal_id=deal_id,
            include=include,
            extra_filters=extra_filters,
            max_results=max_results,
        )
