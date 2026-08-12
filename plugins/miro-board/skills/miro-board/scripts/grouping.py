"""Candidate groupings over the same elements, deliberately overlapping.

Nothing here decides which grouping is the real one. An element belongs to every candidate
it satisfies, each carrying the measurement that put it there, because choosing between a
proximity cluster, a drawn container and a colour cohort needs the text read, not the
geometry measured.
"""

from __future__ import annotations

import collections
import itertools
import statistics
from dataclasses import dataclass, field
from typing import Any

from model import Edge, Element

PROXIMITY_SCALES = (0.5, 0.7, 0.9, 1.2, 1.6, 2.2)
_MIN_MEMBERS = 3
_CONTAINER_MAX_OPACITY = 0.6
_ALIGNMENT_TOLERANCE = 0.15
_LABEL_SEARCH_BANDS = 2.5
_EDGE_TOLERANCE = 0.1
_GAP_TOLERANCE = 0.5
_SPAN_TOLERANCE = 0.2


@dataclass(frozen=True)
class Grouping:
    id: str
    kind: str
    members: list[str]
    evidence: dict[str, Any] = field(default_factory=dict)
    scale: float | None = None


def _bbox(elements: list[Element]) -> tuple[float, float, float, float] | None:
    boxes = [e.box for e in elements if e.box]
    if not boxes:
        return None
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def _typical_width(elements: list[Element]) -> float:
    widths = [e.size[0] for e in elements if e.size]
    return statistics.median(widths) if widths else 100.0


def single_linkage(elements: list[Element], threshold: float) -> list[list[Element]]:
    parent = {e.id: e.id for e in elements}

    def root(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for left, right in itertools.combinations(elements, 2):
        if not left.center or not right.center:
            continue
        if (
            abs(left.center[0] - right.center[0]) < threshold
            and abs(left.center[1] - right.center[1]) < threshold
        ):
            parent[root(left.id)] = root(right.id)

    clustered: dict[str, list[Element]] = collections.defaultdict(list)
    for element in elements:
        clustered[root(element.id)].append(element)
    return list(clustered.values())


def _proximity(elements: list[Element]) -> list[Grouping]:
    positioned = [e for e in elements if e.center]
    width = _typical_width(positioned)
    seen_at_scales: dict[frozenset[str], int] = collections.Counter()
    found: list[tuple[float, list[Element]]] = []

    for scale in PROXIMITY_SCALES:
        for cluster in single_linkage(positioned, width * scale):
            if len(cluster) < _MIN_MEMBERS:
                continue
            seen_at_scales[frozenset(e.id for e in cluster)] += 1
            found.append((scale, cluster))

    groupings = []
    for index, (scale, cluster) in enumerate(found):
        members = frozenset(e.id for e in cluster)
        groupings.append(
            Grouping(
                id=f"prox{scale}#{index}",
                kind="proximity",
                scale=scale,
                members=[e.id for e in cluster],
                evidence={
                    "threshold_px": round(width * scale),
                    "scales_with_same_members": seen_at_scales[members],
                    "of_scales_tried": len(PROXIMITY_SCALES),
                    "fills": dict(collections.Counter(e.fill for e in cluster)),
                    "bbox": _bbox(cluster),
                },
            )
        )
    return groupings


def _containers(elements: list[Element]) -> list[Grouping]:
    """A frame declares its children; a translucent untitled shape only looks like it does."""
    groupings = []
    by_parent: dict[str, list[Element]] = collections.defaultdict(list)
    for element in elements:
        if element.parent_id:
            by_parent[element.parent_id].append(element)

    for element in elements:
        children = by_parent.get(element.id, [])
        if children:
            groupings.append(
                Grouping(
                    id=f"frame#{element.id}",
                    kind="declared_container",
                    members=[c.id for c in children],
                    evidence={
                        "container_id": element.id,
                        "container_kind": element.kind,
                        "title": element.text,
                        "bbox": element.box,
                    },
                )
            )
        if element.kind not in ("shape", "frame") or element.text:
            continue
        if element.opacity is not None and element.opacity > _CONTAINER_MAX_OPACITY:
            continue
        enclosed = [e for e in elements if element.contains(e)]
        if len(enclosed) >= _MIN_MEMBERS:
            groupings.append(
                Grouping(
                    id=f"drawn#{element.id}",
                    kind="drawn_container",
                    members=[e.id for e in enclosed],
                    evidence={
                        "container_id": element.id,
                        "opacity": element.opacity,
                        "fill": element.fill,
                        "bbox": element.box,
                        "kinds_inside": dict(collections.Counter(e.kind for e in enclosed)),
                    },
                )
            )
    return groupings


def _colour_cohorts(elements: list[Element]) -> list[Grouping]:
    by_fill: dict[str, list[Element]] = collections.defaultdict(list)
    for element in elements:
        if element.fill:
            by_fill[element.fill].append(element)
    total = sum(len(members) for members in by_fill.values())
    return [
        Grouping(
            id=f"fill#{fill}",
            kind="colour",
            members=[e.id for e in members],
            evidence={
                "fill": fill,
                "share_of_coloured": round(len(members) / total, 3),
                "kinds": dict(collections.Counter(e.kind for e in members)),
            },
        )
        for fill, members in by_fill.items()
        if len(members) >= _MIN_MEMBERS
    ]


def _components(elements: list[Element], edges: list[Edge]) -> list[Grouping]:
    known = {e.id for e in elements}
    parent = {node: node for node in known}

    def root(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    linked = set()
    for edge in edges:
        if edge.source in known and edge.target in known:
            parent[root(edge.source)] = root(edge.target)
            linked.update((edge.source, edge.target))

    grouped: dict[str, list[str]] = collections.defaultdict(list)
    for node in linked:
        grouped[root(node)].append(node)

    return [
        Grouping(
            id=f"graph#{index}",
            kind="connected",
            members=members,
            evidence={
                "edges": sum(
                    1
                    for e in edges
                    if e.source in set(members) and e.target in set(members)
                ),
                "directed_edges": sum(
                    1
                    for e in edges
                    if e.directed and e.source in set(members) and e.target in set(members)
                ),
            },
        )
        for index, members in enumerate(grouped.values())
        if len(members) >= 2
    ]


def _alignments(elements: list[Element]) -> list[Grouping]:
    positioned = [e for e in elements if e.center]
    tolerance = _typical_width(positioned) * _ALIGNMENT_TOLERANCE
    groupings = []
    for axis, name in ((0, "column"), (1, "row")):
        buckets: dict[int, list[Element]] = collections.defaultdict(list)
        for element in positioned:
            buckets[round(element.center[axis] / tolerance)].append(element)
        for index, (_, members) in enumerate(sorted(buckets.items())):
            if len(members) >= _MIN_MEMBERS:
                ordered = sorted(members, key=lambda e: e.center[1 - axis])
                groupings.append(
                    Grouping(
                        id=f"{name}#{index}",
                        kind=f"aligned_{name}",
                        members=[e.id for e in ordered],
                        evidence={"tolerance_px": round(tolerance), "bbox": _bbox(members)},
                    )
                )
    return groupings


def _edge_runs(
    elements: list[Element], shared: tuple[int, int], along: tuple[int, int], extent: int
) -> list[list[Element]]:
    """Elements that share two opposite edges and sit end to end along the other axis."""
    boxed = sorted(
        (e for e in elements if e.box and e.size),
        key=lambda e: (e.box[shared[0]], e.box[along[0]]),
    )
    runs: list[list[Element]] = []
    for element in boxed:
        tolerance = max(4.0, element.size[extent] * _EDGE_TOLERANCE)
        current = runs[-1] if runs else None
        aligned = current and all(
            abs(element.box[edge] - current[0].box[edge]) <= tolerance for edge in shared
        )
        gap = (
            element.box[along[0]] - max(m.box[along[1]] for m in current)
            if current
            else None
        )
        reach = _GAP_TOLERANCE * min(
            element.size[1 - extent], min(m.size[1 - extent] for m in current or [element])
        )
        if aligned and gap is not None and gap <= reach:
            current.append(element)
        else:
            runs.append([element])
    return [run for run in runs if len(run) >= 2]


def _bands(elements: list[Element]) -> list[Grouping]:
    """Rows of side-by-side blocks and columns of stacked ones, found by their edges.

    Centres are the wrong thing to compare here: a swimlane, a table column and a layer
    diagram are all built by lining edges up, and the blocks doing it are different sizes.
    """
    groupings = []
    shapes = [
        (("row", (1, 3), (0, 2), 1)),
        (("column", (0, 2), (1, 3), 0)),
    ]
    for index, (name, shared, along, extent) in enumerate(shapes):
        for run_index, run in enumerate(_edge_runs(elements, shared, along, extent)):
            groupings.append(
                Grouping(
                    id=f"band_{name}#{index}{run_index}",
                    kind=f"edge_{name}",
                    members=[e.id for e in run],
                    evidence={
                        "labels": [e.text[:30] for e in run if e.text],
                        "extent": (
                            min(e.box[along[0]] for e in run),
                            max(e.box[along[1]] for e in run),
                        ),
                        "bbox": _bbox(run),
                    },
                )
            )
    return groupings


def _spanning(elements: list[Element], bands: list[Grouping]) -> list[Grouping]:
    """One block whose width is exactly the row above or below it: a layer, not a sibling.

    This is how a platform under four verticals is drawn, and how a table header sits over
    its columns. Nothing declares it and no containment test finds it, because the spanning
    block encloses none of them.
    """
    by_id = {e.id: e for e in elements}
    groupings = []
    for band in bands:
        if band.kind != "edge_row":
            continue
        members = [by_id[i] for i in band.members if i in by_id]
        left, right = band.evidence["extent"]
        widths = sorted(e.size[0] for e in members)
        heights = sorted(e.size[1] for e in members)
        edge_tolerance = widths[len(widths) // 2] * _SPAN_TOLERANCE
        reach = heights[len(heights) // 2] * _GAP_TOLERANCE
        top = min(e.box[1] for e in members)
        bottom = max(e.box[3] for e in members)

        for element in elements:
            if element.id in set(band.members) or not element.box:
                continue
            if (
                abs(element.box[0] - left) > edge_tolerance
                or abs(element.box[2] - right) > edge_tolerance
            ):
                continue
            below, above = element.box[1] - bottom, top - element.box[3]
            gap = below if 0 <= below <= reach else above if 0 <= above <= reach else None
            if gap is None:
                continue
            groupings.append(
                Grouping(
                    id=f"spans#{element.id}",
                    kind="spanning",
                    members=[element.id, *band.members],
                    evidence={
                        "spanner": element.id,
                        "spanner_text": element.text,
                        "side": "below" if below >= 0 else "above",
                        "gap_px": round(gap),
                        "spans": band.evidence["labels"],
                        "band": band.id,
                    },
                )
            )
    return groupings


def label_candidates(
    grouping: Grouping, elements: dict[str, Element], text_area: float
) -> list[dict[str, Any]]:
    """Texts that could name this grouping, each with what was measured about it.

    Which one is the label is not decided here: a long block far off the centre axis and a
    short one centred on it are both reported, with the numbers that tell them apart.
    """
    members = [elements[i] for i in grouping.members if i in elements]
    box = _bbox(members)
    if not box:
        return []
    axis = (box[0] + box[2]) / 2
    band = _typical_width(members) * _LABEL_SEARCH_BANDS
    member_ids = set(grouping.members)

    candidates = []
    for element in elements.values():
        if element.id in member_ids or not element.center or not element.text:
            continue
        if element.kind == "frame":
            continue
        above = box[1] - element.center[1]
        inside_span = box[0] - band <= element.center[0] <= box[2] + band
        if not inside_span or not -band / 2 < above < band:
            continue
        candidates.append(
            {
                "id": element.id,
                "kind": element.kind,
                "text": element.text,
                "offset_from_centre_axis_px": round(abs(element.center[0] - axis)),
                "above_group_px": round(above),
                "area_vs_median_text": round(element.area / text_area, 2) if text_area else None,
                "characters": len(element.text),
            }
        )
    return sorted(candidates, key=lambda c: c["offset_from_centre_axis_px"])[:5]


def candidates(elements: list[Element], edges: list[Edge]) -> list[Grouping]:
    bands = _bands(elements)
    return [
        *_containers(elements),
        *_components(elements, edges),
        *bands,
        *_spanning(elements, bands),
        *_proximity(elements),
        *_colour_cohorts(elements),
        *_alignments(elements),
    ]
