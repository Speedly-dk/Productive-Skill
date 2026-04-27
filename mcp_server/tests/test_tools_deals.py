"""Tests for productive_mcp.tools.deals."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from productive_mcp.client import ProductiveAPIError
from productive_mcp.tools import deals

from .conftest import jsonapi_page, make_client


def _deal(did: str, name: str = "Acme website", company_id: str = "10") -> dict:
    return {
        "id": did,
        "type": "deals",
        "attributes": {"name": name, "deal_type_id": 2},
        "relationships": {"company": {"data": {"id": company_id, "type": "companies"}}},
    }


def _company(cid: str, name: str) -> dict:
    return {"id": cid, "type": "companies", "attributes": {"name": name}}


async def test_list_resolves_company_when_included():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=jsonapi_page(
                [_deal("1", company_id="10"), _deal("2", company_id="10")],
                included=[_company("10", "Acme Inc.")],
            ),
        )

    async with make_client(handler) as client:
        result = await deals._list(client, include=["company"])

    assert len(result) == 2
    assert result[0]["company_id"] == "10"
    assert result[0]["company"] == {"id": "10", "type": "companies", "name": "Acme Inc."}


async def test_list_passes_filter_params():
    captured: list[dict[str, list[str]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(parse_qs(urlparse(str(request.url)).query))
        return httpx.Response(200, json=jsonapi_page([]))

    async with make_client(handler) as client:
        await deals._list(client, company_id="10", deal_type_id=2)

    qs = captured[0]
    assert qs["filter[company_id]"] == ["10"]
    assert qs["filter[deal_type_id]"] == ["2"]


async def test_get_returns_single_deal_with_company_resolved():
    def handler(request: httpx.Request) -> httpx.Response:
        # /deals/123 returns a single resource, but the client wraps via
        # paginated_fetch -- Productive returns it as data: {...} when
        # singular. We simulate the same shape it produces for our tests
        # by returning a list with one item, which our client handles
        # consistently.
        return httpx.Response(
            200,
            json=jsonapi_page(
                [_deal("123", company_id="10")],
                included=[_company("10", "Acme Inc.")],
            ),
        )

    async with make_client(handler) as client:
        result = await deals._get(client, deal_id="123", include=["company"])

    assert result["id"] == "123"
    assert result["company"] == {"id": "10", "type": "companies", "name": "Acme Inc."}


async def test_get_unknown_deal_id_surfaces_404():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text='{"errors":[{"detail":"not found"}]}')

    async with make_client(handler) as client:
        with pytest.raises(ProductiveAPIError) as excinfo:
            await deals._get(client, deal_id="99999")

    assert excinfo.value.status == 404


async def test_list_max_results_default_is_50():
    """Defaults matter -- a Claude tool call without max_results should
    return a token-cheap default, not the full workspace."""
    captured_pages: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_pages.append(str(request.url))
        return httpx.Response(
            200,
            json=jsonapi_page(
                [_deal(str(n)) for n in range(1, 101)],  # one page of 100
                next_url=None,
            ),
        )

    async with make_client(handler) as client:
        result = await deals._list(client)

    assert len(result) == 50
