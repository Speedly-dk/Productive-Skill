"""Tests for productive_mcp.tools.tasks."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import httpx

from productive_mcp.tools import tasks

from .conftest import jsonapi_page, make_client


def _task(tid: str, deal_id: str = "1", title: str = "Implement feature") -> dict:
    return {
        "id": tid,
        "type": "tasks",
        "attributes": {"title": title, "status_id": 1},
        "relationships": {"project": {"data": {"id": deal_id, "type": "projects"}}},
    }


async def test_list_scopes_by_deal_id_via_project_id_filter():
    """Productive's tasks endpoint uses filter[project_id] for deal scoping;
    our tool exposes deal_id and translates."""
    captured: list[dict[str, list[str]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(parse_qs(urlparse(str(request.url)).query))
        return httpx.Response(
            200, json=jsonapi_page([_task("1"), _task("2")])
        )

    async with make_client(handler) as client:
        result = await tasks._list(client, deal_id="1")

    assert len(result) == 2
    assert captured[0]["filter[project_id]"] == ["1"]


async def test_list_combines_assignee_and_status_filters():
    captured: list[dict[str, list[str]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(parse_qs(urlparse(str(request.url)).query))
        return httpx.Response(200, json=jsonapi_page([]))

    async with make_client(handler) as client:
        await tasks._list(client, deal_id="1", assignee_id="42", status="open")

    qs = captured[0]
    assert qs["filter[project_id]"] == ["1"]
    assert qs["filter[assignee_id]"] == ["42"]
    assert qs["filter[status]"] == ["open"]


async def test_chained_reads_deal_to_services_to_tasks():
    """Integration scenario from the plan: list_deals -> pick id ->
    list_services(deal_id=...) -> list_tasks(deal_id=...) end-to-end
    against a single mocked API."""
    from productive_mcp.tools import deals, services

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/deals"):
            return httpx.Response(
                200,
                json=jsonapi_page(
                    [
                        {
                            "id": "5",
                            "type": "deals",
                            "attributes": {"name": "Project X"},
                            "relationships": {},
                        }
                    ]
                ),
            )
        if path.endswith("/services"):
            assert request.url.params.get("filter[deal_id]") == "5"
            return httpx.Response(
                200,
                json=jsonapi_page(
                    [
                        {
                            "id": "100",
                            "type": "services",
                            "attributes": {"name": "Development"},
                            "relationships": {},
                        }
                    ]
                ),
            )
        if path.endswith("/tasks"):
            assert request.url.params.get("filter[project_id]") == "5"
            return httpx.Response(
                200, json=jsonapi_page([_task("9", deal_id="5")])
            )
        return httpx.Response(404, text="{}")

    async with make_client(handler) as client:
        deals_list = await deals._list(client)
        deal_id = deals_list[0]["id"]

        services_list = await services._list(client, deal_id=deal_id)
        tasks_list = await tasks._list(client, deal_id=deal_id)

    assert deal_id == "5"
    assert services_list[0]["name"] == "Development"
    assert tasks_list[0]["title"] == "Implement feature"
