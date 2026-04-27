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


# -- write paths -----------------------------------------------------------


async def test_create_returns_compact_task_with_deal_relationship():
    import json
    import pytest

    captured: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith("/tasks"):
            captured.append(json.loads(request.content))
            return httpx.Response(
                201,
                json={
                    "data": {
                        "id": "77",
                        "type": "tasks",
                        "attributes": {"title": "New work"},
                        "relationships": {
                            "project": {"data": {"id": "5", "type": "projects"}}
                        },
                    }
                },
            )
        return httpx.Response(404)

    async with make_client(handler) as client:
        result = await tasks._create(client, deal_id="5", title="New work")

    assert result["id"] == "77"
    assert result["title"] == "New work"
    assert result["project_id"] == "5"
    assert (
        captured[0]["data"]["relationships"]["project"]["data"]["id"] == "5"
    )


async def test_create_rejects_empty_title_before_http():
    import pytest

    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(201, json={"data": {}})

    async with make_client(handler) as client:
        with pytest.raises(ValueError, match="title"):
            await tasks._create(client, deal_id="5", title="")
        with pytest.raises(ValueError, match="title"):
            await tasks._create(client, deal_id="5", title="   ")

    assert calls["n"] == 0


async def test_create_on_unknown_deal_id_surfaces_404():
    import pytest

    from productive_mcp.client import ProductiveAPIError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text='{"errors":[{"detail":"deal not found"}]}')

    async with make_client(handler) as client:
        with pytest.raises(ProductiveAPIError) as excinfo:
            await tasks._create(client, deal_id="99999", title="Doomed task")

    assert excinfo.value.status == 404


async def test_update_patches_only_status_field():
    import json

    captured: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "PATCH":
            captured.append(json.loads(request.content))
            return httpx.Response(
                200,
                json={
                    "data": {
                        "id": "77",
                        "type": "tasks",
                        "attributes": {"status": "done"},
                        "relationships": {},
                    }
                },
            )
        return httpx.Response(404)

    async with make_client(handler) as client:
        result = await tasks._update(client, task_id="77", fields={"status": "done"})

    payload = captured[0]
    assert payload["data"]["id"] == "77"
    assert payload["data"]["attributes"] == {"status": "done"}
    assert "relationships" not in payload["data"]
    assert result["status"] == "done"


async def test_create_task_comment_returns_compact_dict():
    import json

    captured: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith("/comments"):
            captured.append(json.loads(request.content))
            return httpx.Response(
                201,
                json={
                    "data": {
                        "id": "1234",
                        "type": "comments",
                        "attributes": {"body": "Hello"},
                        "relationships": {
                            "commentable": {
                                "data": {"id": "77", "type": "tasks"}
                            }
                        },
                    }
                },
            )
        return httpx.Response(404)

    async with make_client(handler) as client:
        result = await tasks._create_comment(client, task_id="77", body="Hello")

    assert result["id"] == "1234"
    assert result["body"] == "Hello"
    assert (
        captured[0]["data"]["relationships"]["commentable"]["data"]["id"] == "77"
    )


async def test_create_then_get_round_trip():
    """Integration: create_task -> the API returns the new id, then we
    immediately fetch the task and confirm fields match."""
    import json

    state: dict[str, dict] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith("/tasks"):
            payload = json.loads(request.content)
            new_id = "100"
            state[new_id] = {
                "id": new_id,
                "type": "tasks",
                "attributes": payload["data"]["attributes"],
                "relationships": payload["data"]["relationships"],
            }
            return httpx.Response(201, json={"data": state[new_id]})

        # Simulate /tasks?filter[id]=100 returning the just-created task.
        if request.url.path.endswith("/tasks") and request.method == "GET":
            requested = request.url.params.get("filter[id]")
            if requested in state:
                return httpx.Response(
                    200,
                    json=jsonapi_page([state[requested]]),
                )
            return httpx.Response(200, json=jsonapi_page([]))

        return httpx.Response(404)

    async with make_client(handler) as client:
        created = await tasks._create(
            client, deal_id="5", title="Round-trip me"
        )
        fetched = await tasks._list(client, extra_filters={"id": created["id"]})

    assert created["id"] == "100"
    assert fetched[0]["id"] == "100"
    assert fetched[0]["title"] == "Round-trip me"
