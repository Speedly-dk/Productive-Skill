"""Shared test fixtures.

We use ``httpx.MockTransport`` for unit tests because we do not have
recorded API responses yet and we want zero network dependency. When real
cassettes land (U6 manual smoke tests, future integration tests), introduce
a vcrpy-based fixture here with ``before_record_request`` /
``before_record_response`` filters that strip the X-Auth-Token and
X-Organization-Id headers and scrub URL-embedded tokens from JSON:API
``links.self`` fields.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from productive_mcp.client import ProductiveClient


@pytest.fixture(autouse=True)
def _clear_productive_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default to clean env so missing-var tests are deterministic."""
    monkeypatch.delenv("PRODUCTIVE_API_TOKEN", raising=False)
    monkeypatch.delenv("PRODUCTIVE_ORGANIZATION_ID", raising=False)


def make_client(handler: Callable[[httpx.Request], httpx.Response]) -> ProductiveClient:
    """Build a ProductiveClient with a mocked HTTP transport.

    Bypasses the env-var requirement so tests don't need to set fake
    tokens (which would also have to be scrubbed from any error output).
    """
    return ProductiveClient(
        token="test-token",
        organization_id="9999",
        transport=httpx.MockTransport(handler),
    )


def jsonapi_page(
    items: list[dict[str, Any]],
    *,
    included: list[dict[str, Any]] | None = None,
    next_url: str | None = None,
) -> dict[str, Any]:
    """Build a JSON:API response body shaped like Productive's."""
    return {
        "data": items,
        "included": included or [],
        "links": {"next": next_url} if next_url else {},
    }


def time_entry(eid: str, *, minutes: int = 60, person_id: str = "1") -> dict[str, Any]:
    return {
        "id": eid,
        "type": "time_entries",
        "attributes": {"date": "2026-04-15", "time": minutes, "billable_time": minutes},
        "relationships": {"person": {"data": {"id": person_id, "type": "people"}}},
    }
