"""Ask the extract questions, one at a time, the way reading a board actually goes.

The extract is too large to hold at once and reading it whole defeats the point: what is
worth knowing is which grouping survives a closer look, and that is a sequence of questions.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import sys
from pathlib import Path
from typing import Any

import grouping
import model


class ExtractMissing(RuntimeError):
    """The extract is gone, which is ordinary: /tmp is swept between sessions."""


def _load(path: Path) -> tuple[dict[str, Any], dict[str, model.Element]]:
    if not path.exists():
        raise ExtractMissing(
            f"no extract at {path}. Run extract.py on the board first; it takes about "
            "30 seconds and writes this file. Extracts live in /tmp and do not survive."
        )
    document = json.loads(path.read_text(encoding="utf-8"))
    elements = {}
    for raw in document["elements"]:
        elements[raw["id"]] = model.Element(
            id=raw["id"],
            kind=raw["kind"],
            text=raw["text"],
            fill=raw["fill"],
            opacity=raw["opacity"],
            center=tuple(raw["center"]) if raw["center"] else None,
            size=tuple(raw["size"]) if raw["size"] else None,
            parent_id=raw["parent_id"],
            position_scheme=raw["position_scheme"],
            ns=raw["ns"],
        )
    return document, elements


def _show(element: model.Element, prefix: str = "  ") -> str:
    """Extents, not centres: the relations that matter are between edges."""
    box = element.box
    where = (
        f"x[{box[0]:7.0f},{box[2]:7.0f}] y[{box[1]:7.0f},{box[3]:7.0f}]"
        if box
        else " " * 15 + "(unpositioned)"
    )
    return (
        f"{prefix}{element.id[-6:]} {element.kind:9s} {element.fill or '-':8s} "
        f"{where} {element.text[:52]!r}"
    )


def cmd_groups(document: dict, elements: dict, args: argparse.Namespace) -> None:
    for group in document["groupings"]:
        if args.kind and group["kind"] != args.kind:
            continue
        if args.scale is not None and group["scale"] != args.scale:
            continue
        if len(group["members"]) < args.min:
            continue
        evidence = {k: v for k, v in group["evidence"].items() if k != "bbox"}
        print(f"{group['id']:24s} {group['kind']:19s} n={len(group['members']):4d}  {evidence}")
        for candidate in group["label_candidates"][:2]:
            print(
                f"    label? {candidate['text'][:44]!r}"
                f" offset={candidate['offset_from_centre_axis_px']}px"
                f" above={candidate['above_group_px']}px"
                f" area={candidate['area_vs_median_text']}x"
                f" chars={candidate['characters']}"
            )


def cmd_group(document: dict, elements: dict, args: argparse.Namespace) -> None:
    found = [g for g in document["groupings"] if g["id"] == args.group_id]
    if not found:
        print(f"no grouping {args.group_id}")
        return
    group = found[0]
    print(f"{group['id']}  kind={group['kind']}  n={len(group['members'])}")
    print(f"evidence: {group['evidence']}")
    for candidate in group["label_candidates"]:
        print(
            f"  label? {candidate['text'][:50]!r} offset={candidate['offset_from_centre_axis_px']}px"
            f" above={candidate['above_group_px']}px area={candidate['area_vs_median_text']}x"
        )
    print("members:")
    members = [elements[i] for i in group["members"] if i in elements]
    for element in sorted(members, key=lambda e: (e.center[1], e.center[0]) if e.center else (0, 0)):
        print(_show(element))


def cmd_refine(document: dict, elements: dict, args: argparse.Namespace) -> None:
    found = [g for g in document["groupings"] if g["id"] == args.group_id]
    if not found:
        print(f"no grouping {args.group_id}")
        return
    members = [elements[i] for i in found[0]["members"] if i in elements]
    widths = [e.size[0] for e in members if e.size]
    typical = sorted(widths)[len(widths) // 2] if widths else 100.0
    for scale in args.scales:
        clusters = sorted(
            grouping.single_linkage(members, typical * scale), key=len, reverse=True
        )
        print(f"\nat {scale}x ({typical * scale:.0f}px): {len(clusters)} subgroups")
        for cluster in clusters:
            if len(cluster) < 2 and not args.all:
                continue
            fills = dict(collections.Counter(e.fill for e in cluster))
            print(f"  n={len(cluster):3d} fills={fills}")
            for element in cluster[: args.sample]:
                print(_show(element, "     "))


def cmd_element(document: dict, elements: dict, args: argparse.Namespace) -> None:
    element = elements.get(args.element_id) or next(
        (e for e in elements.values() if e.id.endswith(args.element_id)), None
    )
    if not element:
        print("not found")
        return
    print(_show(element, ""))
    print(f"ns fields: {element.ns}")
    print("belongs to:")
    for group in document["groupings"]:
        if element.id in group["members"]:
            print(f"  {group['id']:24s} {group['kind']:19s} n={len(group['members'])}")
    print("connected to:")
    for edge in document["edges"]:
        if element.id in (edge["source"], edge["target"]):
            other = edge["target"] if edge["source"] == element.id else edge["source"]
            arrow = "->" if edge["directed"] else "--"
            print(f"  {arrow} {other} {edge['label'][:30]!r}")


def cmd_inside(document: dict, elements: dict, args: argparse.Namespace) -> None:
    container = elements.get(args.element_id)
    if not container:
        print("not found")
        return
    for element in elements.values():
        if container.contains(element):
            print(_show(element))


def cmd_near(document: dict, elements: dict, args: argparse.Namespace) -> None:
    anchor = elements.get(args.element_id)
    if not anchor or not anchor.center:
        print("not found or unpositioned")
        return
    scored = []
    for element in elements.values():
        if element.id == anchor.id or not element.center:
            continue
        distance = math.dist(anchor.center, element.center)
        if distance <= args.radius:
            scored.append((distance, element))
    for distance, element in sorted(scored)[: args.limit]:
        print(f"{distance:7.0f}px {_show(element, '')}")


def cmd_text(document: dict, elements: dict, args: argparse.Namespace) -> None:
    for element in elements.values():
        if args.kind and element.kind != args.kind:
            continue
        if args.fill and element.fill != args.fill:
            continue
        if element.text:
            print(f"{element.id[-6:]} {element.text}")


def cmd_find(document: dict, elements: dict, args: argparse.Namespace) -> None:
    needle = args.term.lower()
    found = [e for e in elements.values() if needle in e.text.lower()]
    print(f"{len(found)} elements mention {args.term!r}")
    for element in found[: args.limit]:
        print(_show(element))


def cmd_residue(document: dict, elements: dict, args: argparse.Namespace) -> None:
    attached = {
        member
        for group in document["groupings"]
        if group["kind"] in ("declared_container", "connected")
        for member in group["members"]
    }
    loose = [e for e in elements.values() if e.id not in attached]
    print(f"{len(loose)} elements in no declared structure")
    for element in loose[: args.limit]:
        print(_show(element))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("extract", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)

    groups = sub.add_parser("groups", help="list candidate groupings")
    groups.add_argument("--kind")
    groups.add_argument("--scale", type=float)
    groups.add_argument("--min", type=int, default=3)
    groups.set_defaults(run=cmd_groups)

    one = sub.add_parser("group", help="one grouping with its members and label candidates")
    one.add_argument("group_id")
    one.set_defaults(run=cmd_group)

    refine = sub.add_parser("refine", help="recluster a grouping at finer scales")
    refine.add_argument("group_id")
    refine.add_argument("--scales", type=float, nargs="+", default=[0.5, 0.7, 0.9])
    refine.add_argument("--sample", type=int, default=6)
    refine.add_argument("--all", action="store_true")
    refine.set_defaults(run=cmd_refine)

    element = sub.add_parser("element", help="one element and everything it belongs to")
    element.add_argument("element_id")
    element.set_defaults(run=cmd_element)

    inside = sub.add_parser("inside", help="what falls within an element's box")
    inside.add_argument("element_id")
    inside.set_defaults(run=cmd_inside)

    near = sub.add_parser("near", help="nearest elements to one")
    near.add_argument("element_id")
    near.add_argument("--radius", type=float, default=600)
    near.add_argument("--limit", type=int, default=20)
    near.set_defaults(run=cmd_near)

    text = sub.add_parser("text", help="the text of elements, filtered")
    text.add_argument("--kind")
    text.add_argument("--fill")
    text.set_defaults(run=cmd_text)

    find = sub.add_parser("find", help="which elements mention a term, and where they sit")
    find.add_argument("term")
    find.add_argument("--limit", type=int, default=40)
    find.set_defaults(run=cmd_find)

    residue = sub.add_parser("residue", help="elements no declared structure covers")
    residue.add_argument("--limit", type=int, default=60)
    residue.set_defaults(run=cmd_residue)

    args = parser.parse_args()
    try:
        document, elements = _load(args.extract)
    except ExtractMissing as err:
        print(err, file=sys.stderr)
        return 2
    args.run(document, elements, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
