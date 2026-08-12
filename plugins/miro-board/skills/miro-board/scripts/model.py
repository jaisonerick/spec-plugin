"""Normalise raw gateway records into elements with comparable geometry and attributes.

Two things here are not obvious and cause silent wrong answers if skipped: a board uses
three different positioning schemes at once, and the style vocabulary differs per widget
kind, so "the background colour" is a different key depending on what you are looking at.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from typing import Any

_TAG = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")
_MAX_PARENT_DEPTH = 8
_TRANSPARENT = -1

_FILL_KEY_BY_KIND = {"sticker": "sbc"}
_DEFAULT_FILL_KEY = "bc"

BOARD_METADATA_KEYS = frozenset(
    {"app_metadata", "presentations", "properties", "reactionsConfig", "userStatuses"}
)


@dataclass(frozen=True)
class Element:
    id: str
    kind: str
    text: str
    fill: str | None
    opacity: float | None
    center: tuple[float, float] | None
    size: tuple[float, float] | None
    parent_id: str | None
    position_scheme: str | None
    ns: dict[str, Any] = field(default_factory=dict)

    @property
    def box(self) -> tuple[float, float, float, float] | None:
        if not self.center or not self.size:
            return None
        half_width, half_height = self.size[0] / 2, self.size[1] / 2
        return (
            self.center[0] - half_width,
            self.center[1] - half_height,
            self.center[0] + half_width,
            self.center[1] + half_height,
        )

    @property
    def area(self) -> float:
        return self.size[0] * self.size[1] if self.size else 0.0

    def contains(self, other: Element) -> bool:
        box, point = self.box, other.center
        if not box or not point or other.id == self.id:
            return False
        return box[0] <= point[0] <= box[2] and box[1] <= point[1] <= box[3]


@dataclass(frozen=True)
class Edge:
    source: str | None
    target: str | None
    directed: bool
    label: str


def _style(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("style")
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return {}


def _colour(value: Any) -> str | None:
    if not isinstance(value, int) or value == _TRANSPARENT:
        return None
    return f"#{value & 0xFFFFFF:06X}"


def _plain_text(payload: dict[str, Any]) -> str:
    for key in ("text", "title", "name", "description"):
        raw = payload.get(key)
        if isinstance(raw, dict):
            raw = raw.get("text")
        if isinstance(raw, str) and raw.strip():
            return _SPACE.sub(" ", html.unescape(_TAG.sub(" ", raw))).strip()
    return ""


def _parent_id(payload: dict[str, Any]) -> str | None:
    parent = payload.get("_parent")
    return str(parent["id"]) if isinstance(parent, dict) and "id" in parent else None


def _absolute_centre(
    record: dict[str, Any], records: dict[str, dict[str, Any]], depth: int = 0
) -> tuple[float, float] | None:
    payload = record["payload"]
    position = payload.get("_position") or {}
    offset = position.get("offsetPx")
    if not offset:
        return None
    if position.get("schema") == "parentOffsetPx" and depth < _MAX_PARENT_DEPTH:
        parent_id = _parent_id(payload)
        parent = records.get(parent_id or "")
        base = _absolute_centre(parent, records, depth + 1) if parent else None
        if base:
            return (base[0] + offset["x"], base[1] + offset["y"])
    return (offset["x"], offset["y"])


def _is_board_metadata(payload: dict[str, Any]) -> bool:
    return bool(BOARD_METADATA_KEYS & payload.keys())


def _edges(records: list[dict[str, Any]]) -> list[Edge]:
    edges = []
    for record in records:
        if record["kind"] != "line":
            continue
        payload = record["payload"]
        style = _style(payload)
        ends = []
        for side in ("primary", "secondary"):
            end = payload.get(side)
            widget = end.get("widget") if isinstance(end, dict) else None
            ends.append(str(widget["id"]) if isinstance(widget, dict) else None)
        captions = (payload.get("line") or {}).get("captions") or []
        edges.append(
            Edge(
                source=ends[0],
                target=ends[1],
                directed=bool(style.get("a_start") or style.get("a_end")),
                label=" ".join(_plain_text(c) for c in captions if isinstance(c, dict)),
            )
        )
    return edges


def build(records: list[dict[str, Any]]) -> tuple[list[Element], list[Edge]]:
    """Turn gateway records into elements with absolute geometry, plus the edge list."""
    by_id = {r["id"]: r for r in records if r.get("id")}
    elements = []
    for record in records:
        payload = record["payload"]
        if not record.get("id") or record["kind"] == "line" or _is_board_metadata(payload):
            continue
        style = _style(payload)
        size = payload.get("size") or {}
        position = payload.get("_position") or {}
        elements.append(
            Element(
                id=record["id"],
                kind=record["kind"],
                text=_plain_text(payload),
                fill=_colour(style.get(_FILL_KEY_BY_KIND.get(record["kind"], _DEFAULT_FILL_KEY))),
                opacity=style.get("bo"),
                center=_absolute_centre(record, by_id),
                size=(size["width"], size["height"]) if size.get("width") else None,
                parent_id=_parent_id(payload),
                position_scheme=position.get("schema"),
                ns={k: v for k, v in payload.items() if k.startswith("ns:")},
            )
        )
    return elements, _edges(records)
