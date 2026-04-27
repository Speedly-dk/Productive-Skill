"""Tests for the Productive REST client."""

from __future__ import annotations

import httpx
import pytest

from productive_mcp.client import (
    ConfigError,
    ProductiveAPIError,
    ProductiveClient,
)
from productive_mcp.formatting import flatten_jsonapi

from .conftest import jsonapi_page, make_client, time_entry


# -- env-var validation -----------------------------------------------------


def test_missing_token_raises_config_error_with_name():
    with pytest.raises(ConfigError) as excinfo:
        ProductiveClient(organization_id="9999")
    assert "PRODUCTIVE_API_TOKEN" in str(excinfo.value)


def test_missing_organization_id_raises_config_error_with_name():
    with pytest.raises(ConfigError) as excinfo:
        ProductiveClient(token="t")
    assert "PRODUCTIVE_ORGANIZATION_ID" in str(excinfo.value)


def test_explicit_credentials_bypass_env_lookup():
    client = ProductiveClient(token="t", organization_id="9999")
    assert client.organization_id == "9999"


# -- pagination -------------------------------------------------------------


async def test_get_combines_multi_page_data_and_included():
    pages_seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        pages_seen.append(str(request.url))
        if "page=2" in str(request.url):
            return httpx.Response(
                200,
                json=jsonapi_page(
                    [time_entry("3"), time_entry("4")],
                    included=[{"id": "1", "type": "people", "attributes": {"name": "Alice"}}],
                ),
            )
        return httpx.Response(
            200,
            json=jsonapi_page(
                [time_entry("1"), time_entry("2")],
                included=[{"id": "1", "type": "people", "attributes": {"name": "Alice"}}],
                next_url="https://api.productive.io/api/v2/time_entries?page=2",
            ),
        )

    async with make_client(handler) as client:
        result = await client.get("/time_entries")

    assert [item["id"] for item in result["data"]] == ["1", "2", "3", "4"]
    assert len(result["included"]) == 1
    assert result["meta"]["count"] == 4
    assert len(pages_seen) == 2


async def test_get_short_circuits_when_max_results_reached():
    pages_seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        pages_seen.append(str(request.url))
        return httpx.Response(
            200,
            json=jsonapi_page(
                [time_entry(str(n)) for n in range(1, 11)],
                next_url="https://api.productive.io/api/v2/time_entries?page=2",
            ),
        )

    async with make_client(handler) as client:
        result = await client.get("/time_entries", max_results=5)

    assert len(result["data"]) == 5
    # Critical: only the first page should have been fetched.
    assert len(pages_seen) == 1


async def test_pagination_terminates_when_no_next_link():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=jsonapi_page([time_entry("1")]))

    async with make_client(handler) as client:
        result = await client.get("/time_entries")

    assert len(result["data"]) == 1


# -- error mapping ----------------------------------------------------------


async def test_http_401_surfaces_token_hint():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text='{"errors":[{"detail":"unauthorized"}]}')

    async with make_client(handler) as client:
        with pytest.raises(ProductiveAPIError) as excinfo:
            await client.get("/time_entries")

    assert excinfo.value.status == 401
    assert "PRODUCTIVE_API_TOKEN" in str(excinfo.value)


async def test_http_403_read_only_token_hint():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            text='{"errors":[{"detail":"This token is read-only"}]}',
        )

    async with make_client(handler) as client:
        with pytest.raises(ProductiveAPIError) as excinfo:
            await client.post("/time_entries", json={"data": {}})

    assert "read-only" in str(excinfo.value)


async def test_http_404_surfaces_clearly():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text='{"errors":[{"detail":"not found"}]}')

    async with make_client(handler) as client:
        with pytest.raises(ProductiveAPIError) as excinfo:
            await client.get("/deals/99999")

    assert excinfo.value.status == 404


async def test_http_500_does_not_leak_token():
    sensitive_token = "real-secret-token-do-not-leak"
    body = (
        '{"errors":[{"detail":"server error","headers":{'
        f'"X-Auth-Token":"{sensitive_token}"'
        '}}]}'
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text=body)

    client = ProductiveClient(
        token=sensitive_token,
        organization_id="9999",
        transport=httpx.MockTransport(handler),
    )
    async with client:
        with pytest.raises(ProductiveAPIError) as excinfo:
            await client.get("/time_entries")

    rendered = f"{excinfo.value!s} {excinfo.value.detail or ''}"
    assert sensitive_token not in rendered
    assert "[REDACTED]" in (excinfo.value.detail or "")


# -- 429 backoff ------------------------------------------------------------


async def test_429_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch):
    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr("productive_mcp.client.asyncio.sleep", fake_sleep)

    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429, text='{"errors":[{"detail":"slow down"}]}')
        return httpx.Response(200, json=jsonapi_page([time_entry("1")]))

    async with make_client(handler) as client:
        result = await client.get("/time_entries")

    assert calls["n"] == 3
    assert len(result["data"]) == 1
    # Two backoff sleeps before the third (successful) attempt; doubling.
    assert sleeps == [1.0, 2.0]


async def test_persistent_429_raises_after_max_retries(monkeypatch: pytest.MonkeyPatch):
    async def fake_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr("productive_mcp.client.asyncio.sleep", fake_sleep)

    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(429, text='{"errors":[{"detail":"slow down"}]}')

    async with make_client(handler) as client:
        with pytest.raises(ProductiveAPIError) as excinfo:
            await client.get("/time_entries")

    assert excinfo.value.status == 429
    # 1 initial + 3 retries = 4 calls.
    assert calls["n"] == 4


# -- formatting -------------------------------------------------------------


def test_flatten_jsonapi_resolves_to_one_relationships():
    payload = {
        "data": [time_entry("1", person_id="42")],
        "included": [
            {"id": "42", "type": "people", "attributes": {"name": "Alice", "first_name": "A"}}
        ],
    }
    flat = flatten_jsonapi(payload)
    assert flat[0]["id"] == "1"
    assert flat[0]["person_id"] == "42"
    assert flat[0]["person"] == {"id": "42", "type": "people", "name": "Alice"}


def test_flatten_jsonapi_handles_missing_included():
    payload = {"data": [time_entry("1", person_id="42")], "included": []}
    flat = flatten_jsonapi(payload)
    assert flat[0]["person_id"] == "42"
    assert "person" not in flat[0]


# -- header injection -------------------------------------------------------


async def test_auth_headers_are_attached_to_every_request():
    seen_headers: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.append(dict(request.headers))
        return httpx.Response(200, json=jsonapi_page([]))

    async with make_client(handler) as client:
        await client.get("/people")

    assert seen_headers[0]["x-auth-token"] == "test-token"
    assert seen_headers[0]["x-organization-id"] == "9999"
