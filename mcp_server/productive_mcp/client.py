"""Productive.io REST client.

Handles auth, pagination with max_results short-circuit, 429 backoff, and
token redaction in errors. Exposes a small async surface that tool modules
build on.
"""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any

import httpx

BASE_URL = "https://api.productive.io/api/v2"
DEFAULT_PAGE_SIZE = 200
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0

_TOKEN_HEADER = "X-Auth-Token"
_ORG_HEADER = "X-Organization-Id"


class ConfigError(RuntimeError):
    """Raised when required environment variables are missing or invalid."""


class ProductiveAPIError(RuntimeError):
    """Surfaces an actionable error from the Productive REST API.

    The message is shaped for end-user consumption (e.g., shown back to
    Claude as a tool error). The raw response body is exposed via
    ``.detail`` for callers that want it. Auth tokens are scrubbed.
    """

    def __init__(self, status: int, message: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.detail = detail


def _redact(text: str | None, token: str | None) -> str:
    if not text:
        return ""
    if token:
        text = text.replace(token, "[REDACTED]")
    text = re.sub(r"(X-Auth-Token['\"]?\s*:\s*['\"]?)[^'\"\s,}]+", r"\1[REDACTED]", text)
    return text


def _classify(status: int, body: str, token: str | None) -> ProductiveAPIError:
    safe_body = _redact(body, token)
    if status == 401:
        message = (
            "Productive returned 401 Unauthorized. Check your "
            "PRODUCTIVE_API_TOKEN environment variable."
        )
    elif status == 403:
        if "read" in safe_body.lower() and "only" in safe_body.lower():
            message = (
                "Productive returned 403: your token appears to be read-only. "
                "Mint a read-write Personal Access Token to use this tool."
            )
        else:
            message = "Productive returned 403 Forbidden."
    elif status == 404:
        message = "Productive returned 404. The requested resource does not exist."
    elif status == 429:
        message = "Productive rate limit hit and retries exhausted."
    elif 500 <= status < 600:
        message = f"Productive returned {status}. The API is failing upstream."
    else:
        message = f"Productive returned an unexpected {status} status."
    return ProductiveAPIError(status=status, message=message, detail=safe_body)


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ConfigError(
            f"Missing required environment variable {name}. "
            f"Set it before launching the Productive MCP server."
        )
    return value


class ProductiveClient:
    """Thin async REST client for Productive.io.

    Reads auth from environment variables at construction time and never
    persists them. The token is scrubbed from any error message that may
    surface to a caller.
    """

    def __init__(
        self,
        *,
        token: str | None = None,
        organization_id: str | None = None,
        base_url: str = BASE_URL,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._token = token if token is not None else _required_env("PRODUCTIVE_API_TOKEN")
        self._organization_id = (
            organization_id
            if organization_id is not None
            else _required_env("PRODUCTIVE_ORGANIZATION_ID")
        )
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Content-Type": "application/vnd.api+json",
                "Accept": "application/vnd.api+json",
                _TOKEN_HEADER: self._token,
                _ORG_HEADER: self._organization_id,
            },
            transport=transport,
            timeout=30.0,
        )

    @property
    def organization_id(self) -> str:
        return self._organization_id

    @property
    def base_url(self) -> str:
        return self._base_url

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> ProductiveClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        delay = INITIAL_BACKOFF_SECONDS
        for attempt in range(MAX_RETRIES + 1):
            response = await self._client.request(method, path, params=params, json=json)
            if response.status_code != 429 or attempt == MAX_RETRIES:
                return response
            await asyncio.sleep(delay)
            delay *= 2
        return response  # pragma: no cover - loop always returns

    async def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        max_results: int | None = None,
    ) -> dict[str, Any]:
        """GET a JSON:API endpoint, paginating until ``max_results`` or end.

        Returns ``{"data": [...], "included": [...], "meta": {...}}`` with
        ``data`` truncated to ``max_results`` records when set. Pagination
        short-circuits as soon as the accumulator reaches ``max_results`` --
        we never fetch a page only to discard it.
        """
        merged_params = dict(params or {})
        merged_params.setdefault("page[size]", DEFAULT_PAGE_SIZE)

        all_data: list[dict[str, Any]] = []
        included: dict[tuple[str, str], dict[str, Any]] = {}
        next_url: str | None = None
        first_iteration = True

        while True:
            if first_iteration:
                response = await self._request("GET", path, params=merged_params)
                first_iteration = False
            else:
                assert next_url is not None
                response = await self._request("GET", next_url)

            if response.status_code >= 400:
                raise _classify(response.status_code, response.text, self._token)

            body = response.json()
            for item in body.get("data", []):
                all_data.append(item)
                if max_results is not None and len(all_data) >= max_results:
                    break

            for resource in body.get("included") or []:
                key = (resource.get("type", ""), resource.get("id", ""))
                included.setdefault(key, resource)

            if max_results is not None and len(all_data) >= max_results:
                all_data = all_data[:max_results]
                break

            next_url = (body.get("links") or {}).get("next") or None
            if not next_url:
                break

        return {
            "data": all_data,
            "included": list(included.values()),
            "meta": {"count": len(all_data)},
        }

    async def post(self, path: str, *, json: dict[str, Any]) -> dict[str, Any]:
        response = await self._request("POST", path, json=json)
        if response.status_code >= 400:
            raise _classify(response.status_code, response.text, self._token)
        return response.json()

    async def patch(self, path: str, *, json: dict[str, Any]) -> dict[str, Any]:
        response = await self._request("PATCH", path, json=json)
        if response.status_code >= 400:
            raise _classify(response.status_code, response.text, self._token)
        return response.json()
