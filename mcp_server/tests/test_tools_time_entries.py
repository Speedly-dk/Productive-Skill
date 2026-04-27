"""Tests for productive_mcp.tools.time_entries."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from productive_mcp.client import ProductiveAPIError
from productive_mcp.tools import time_entries

from .conftest import jsonapi_page, make_client, time_entry


async def test_search_happy_path_returns_compact_entries():
    captured: list[dict[str, list[str]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(parse_qs(urlparse(str(request.url)).query))
        return httpx.Response(
            200,
            json=jsonapi_page(
                [time_entry("1", minutes=120), time_entry("2", minutes=60)],
                included=[{"id": "1", "type": "people", "attributes": {"name": "Alice"}}],
            ),
        )

    async with make_client(handler) as client:
        result = await time_entries._search(
            client, after="2026-04-01", before="2026-04-30", include=["person"]
        )

    assert len(result) == 2
    assert result[0]["id"] == "1"
    assert result[0]["time"] == 120
    assert result[0]["person_id"] == "1"
    assert result[0]["person"] == {"id": "1", "type": "people", "name": "Alice"}

    # Confirms the filter[*] params were sent and include resolves to a CSV.
    qs = captured[0]
    assert qs["filter[after]"] == ["2026-04-01"]
    assert qs["filter[before]"] == ["2026-04-30"]
    assert qs["include"] == ["person"]


async def test_search_empty_range_returns_empty_list_not_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=jsonapi_page([]))

    async with make_client(handler) as client:
        result = await time_entries._search(
            client, after="2026-04-01", before="2026-04-30"
        )

    assert result == []


async def test_search_max_results_short_circuits_pagination():
    pages: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        pages.append(str(request.url))
        return httpx.Response(
            200,
            json=jsonapi_page(
                [time_entry(str(n)) for n in range(1, 21)],
                next_url="https://api.productive.io/api/v2/time_entries?page=2",
            ),
        )

    async with make_client(handler) as client:
        result = await time_entries._search(
            client, after="2026-04-01", before="2026-04-30", max_results=10
        )

    assert len(result) == 10
    assert len(pages) == 1  # second page never fetched


async def test_search_invalid_person_id_returns_empty_list():
    """Productive returns an empty data list for a non-matching filter
    rather than 4xx; we should pass that through cleanly."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=jsonapi_page([]))

    async with make_client(handler) as client:
        result = await time_entries._search(
            client, after="2026-04-01", before="2026-04-30", person_id="999999"
        )

    assert result == []


async def test_search_caps_at_hard_limit():
    captured_max: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        # The client sends page[size]=200 by default, but the tool's hard
        # cap should still bound how many records we accumulate.
        return httpx.Response(
            200,
            json=jsonapi_page(
                [time_entry(str(n)) for n in range(1, 600)],
                next_url=None,
            ),
        )

    async with make_client(handler) as client:
        result = await time_entries._search(
            client, after="2026-04-01", before="2026-04-30", max_results=99999
        )
        captured_max.append(len(result))

    assert captured_max[0] == 500  # hard cap from _helpers.HARD_CAP


async def test_search_extra_filters_pass_through():
    captured: list[dict[str, list[str]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(parse_qs(urlparse(str(request.url)).query))
        return httpx.Response(200, json=jsonapi_page([]))

    async with make_client(handler) as client:
        await time_entries._search(
            client,
            after="2026-04-01",
            before="2026-04-30",
            extra_filters={"service_id": "42"},
        )

    assert captured[0]["filter[service_id]"] == ["42"]


async def test_search_propagates_api_errors():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text='{"errors":[{"detail":"unauthorized"}]}')

    async with make_client(handler) as client:
        with pytest.raises(ProductiveAPIError) as excinfo:
            await time_entries._search(
                client, after="2026-04-01", before="2026-04-30"
            )

    assert excinfo.value.status == 401


# -- write paths -----------------------------------------------------------


async def test_create_posts_correct_jsonapi_document():
    captured: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        if request.method == "POST":
            captured.append(json.loads(request.content))
            return httpx.Response(
                201,
                json={
                    "data": {
                        "id": "999",
                        "type": "time_entries",
                        "attributes": {
                            "date": "2026-04-15",
                            "time": 60,
                            "billable_time": 60,
                        },
                        "relationships": {},
                    }
                },
            )
        return httpx.Response(404)

    async with make_client(handler) as client:
        result = await time_entries._create(
            client,
            date="2026-04-15",
            person_id="1",
            service_id="100",
            minutes=60,
            billable_minutes=60,
            note="Worked on X",
            task_id="9",
        )

    assert result["id"] == "999"
    payload = captured[0]
    assert payload["data"]["type"] == "time_entries"
    assert payload["data"]["attributes"]["date"] == "2026-04-15"
    assert payload["data"]["attributes"]["time"] == 60
    assert payload["data"]["attributes"]["billable_time"] == 60
    assert payload["data"]["attributes"]["note"] == "Worked on X"
    assert payload["data"]["relationships"]["person"]["data"]["id"] == "1"
    assert payload["data"]["relationships"]["service"]["data"]["id"] == "100"
    assert payload["data"]["relationships"]["task"]["data"]["id"] == "9"


async def test_create_zero_minutes_rejected_before_http():
    """No HTTP request should be made when validation fails."""
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(201, json={"data": {}})

    async with make_client(handler) as client:
        with pytest.raises(ValueError, match="minutes"):
            await time_entries._create(
                client,
                date="2026-04-15",
                person_id="1",
                service_id="100",
                minutes=0,
            )

    assert calls["n"] == 0


async def test_create_missing_required_fields_rejected_before_http():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(201, json={"data": {}})

    async with make_client(handler) as client:
        with pytest.raises(ValueError, match="person_id"):
            await time_entries._create(
                client,
                date="2026-04-15",
                person_id="",
                service_id="100",
                minutes=60,
            )

    assert calls["n"] == 0


async def test_create_with_read_only_token_surfaces_403():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            text='{"errors":[{"detail":"This token is read-only"}]}',
        )

    async with make_client(handler) as client:
        with pytest.raises(ProductiveAPIError) as excinfo:
            await time_entries._create(
                client,
                date="2026-04-15",
                person_id="1",
                service_id="100",
                minutes=60,
            )

    assert "read-only" in str(excinfo.value)


async def test_update_patches_only_supplied_fields():
    captured: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        if request.method == "PATCH":
            captured.append(json.loads(request.content))
            return httpx.Response(
                200,
                json={
                    "data": {
                        "id": "999",
                        "type": "time_entries",
                        "attributes": {"note": "Updated"},
                        "relationships": {},
                    }
                },
            )
        return httpx.Response(404)

    async with make_client(handler) as client:
        result = await time_entries._update(
            client,
            entry_id="999",
            fields={"note": "Updated"},
        )

    assert result["note"] == "Updated"
    payload = captured[0]
    assert payload["data"]["id"] == "999"
    assert payload["data"]["attributes"] == {"note": "Updated"}


async def test_update_requires_at_least_one_field():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"data": {}})

    async with make_client(handler) as client:
        with pytest.raises(ValueError):
            await time_entries._update(client, entry_id="999", fields={})

    assert calls["n"] == 0
