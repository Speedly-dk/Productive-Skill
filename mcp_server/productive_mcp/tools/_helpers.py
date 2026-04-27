"""Shared helpers used across resource tool modules."""

from __future__ import annotations

from typing import Any

HARD_CAP = 500
DEFAULT_LIST_RESULTS = 50
DEFAULT_TIME_ENTRY_RESULTS = 200


def cap_max_results(value: int, *, default: int = DEFAULT_LIST_RESULTS) -> int:
    """Clamp ``value`` to [1, HARD_CAP]; fall back to ``default`` on None/0."""
    if value is None or value <= 0:
        return default
    return min(value, HARD_CAP)


def build_params(
    *,
    filters: dict[str, str | int | None] | None = None,
    extra_filters: dict[str, str] | None = None,
    include: list[str] | None = None,
) -> dict[str, Any]:
    """Build JSON:API query params from structured inputs.

    ``filters`` keys map to ``filter[<key>]``; None values are skipped so
    callers can pass optional filters without conditionals.
    """
    params: dict[str, Any] = {}
    if filters:
        for key, value in filters.items():
            if value is None or value == "":
                continue
            params[f"filter[{key}]"] = value
    if extra_filters:
        for key, value in extra_filters.items():
            params[f"filter[{key}]"] = value
    if include:
        params["include"] = ",".join(include)
    return params
