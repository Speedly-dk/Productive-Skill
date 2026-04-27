"""JSON:API → compact dict formatting.

Productive's JSON:API responses are verbose. These helpers flatten a
resource's attributes and resolve simple to-one relationships against the
``included`` sideload, producing dicts that are cheap to send through Claude.
"""

from __future__ import annotations

from typing import Any


def _included_index(included: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(r.get("type", ""), r.get("id", "")): r for r in included}


def flatten_resource(
    resource: dict[str, Any],
    *,
    included_index: dict[tuple[str, str], dict[str, Any]] | None = None,
    resolve_to_one: bool = True,
) -> dict[str, Any]:
    """Flatten a single JSON:API resource into a compact dict.

    Includes ``id``, ``type``, all ``attributes``, and the IDs of every
    relationship. When ``resolve_to_one`` is True and ``included_index`` is
    supplied, to-one relationships are resolved to a small embedded object
    with ``{id, type, name|title}`` when those attributes exist on the
    sideloaded resource.
    """
    out: dict[str, Any] = {
        "id": resource.get("id"),
        "type": resource.get("type"),
        **(resource.get("attributes") or {}),
    }
    relationships = resource.get("relationships") or {}
    for rel_name, rel in relationships.items():
        data = rel.get("data") if isinstance(rel, dict) else None
        if data is None:
            continue
        if isinstance(data, list):
            out[f"{rel_name}_ids"] = [item.get("id") for item in data if isinstance(item, dict)]
        elif isinstance(data, dict):
            ref_id = data.get("id")
            ref_type = data.get("type")
            out[f"{rel_name}_id"] = ref_id
            if resolve_to_one and included_index and ref_type and ref_id:
                hit = included_index.get((ref_type, ref_id))
                if hit:
                    attrs = hit.get("attributes") or {}
                    label = attrs.get("name") or attrs.get("title") or attrs.get("first_name")
                    out[rel_name] = {"id": ref_id, "type": ref_type, "name": label}
    return out


def flatten_jsonapi(payload: dict[str, Any], *, resolve_to_one: bool = True) -> list[dict[str, Any]]:
    """Flatten a JSON:API list payload into a list of compact dicts."""
    data = payload.get("data") or []
    included = payload.get("included") or []
    index = _included_index(included) if resolve_to_one else None
    return [
        flatten_resource(item, included_index=index, resolve_to_one=resolve_to_one)
        for item in data
    ]
