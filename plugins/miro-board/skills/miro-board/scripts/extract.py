"""Read a Miro board and write an extract: elements, overlapping candidate groupings, edges.

Chrome is opened once on the board, which is what proves the session is live, confirms the
client build and keeps the credential out of any file. Everything after that is a socket.
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import json
import re
import sys
from pathlib import Path

import grouping
import inventory
import model
import rtc
import session as session_module

DEFAULT_OUTPUT_DIR = Path("/tmp/miro-board")
_BOARD_URL = re.compile(r"miro\.com/app/board/([^/?#]+)")


def board_id_from(target: str) -> str:
    match = _BOARD_URL.search(target)
    return match.group(1) if match else target


def _summary(
    board_id: str,
    elements: list[model.Element],
    edges: list[model.Edge],
    groupings: list[grouping.Grouping],
    missing: set[str],
    inventory_size: int,
    output: Path,
) -> str:
    by_kind = collections.Counter(e.kind for e in elements)
    declared = [g for g in groupings if g.kind in ("declared_container", "connected")]
    attached = {member for g in declared for member in g.members}
    drawn = [g for g in groupings if g.kind == "drawn_container"]
    fills = [g for g in groupings if g.kind == "colour"]
    schemes = collections.Counter(e.position_scheme for e in elements)

    lines = [
        f"board {board_id}",
        f"  {len(elements)} elements and {len(edges)} connectors, from {inventory_size} widgets"
        + ("  READ COMPLETE" if not missing else f"  <- {len(missing)} WIDGETS MISSING"),
        f"  kinds: {', '.join(f'{k} {n}' for k, n in by_kind.most_common())}",
        f"  positioning: {', '.join(f'{k} {n}' for k, n in schemes.most_common())}",
        "",
        "DECLARED structure (Miro records it; treat as fact)",
    ]
    for group in declared:
        title = group.evidence.get("title") or ""
        lines.append(
            f"  {group.id:22s} {len(group.members):4d} members"
            + (f'  "{title[:40]}"' if title else "")
            + (
                f"  edges={group.evidence['edges']} directed={group.evidence['directed_edges']}"
                if group.kind == "connected"
                else ""
            )
        )
    if not declared:
        lines.append("  none")

    lines += ["", "INFERRED candidates (measured, not decided)"]
    for group in drawn:
        lines.append(
            f"  {group.id:22s} {len(group.members):4d} inside a translucent untitled shape"
            f"  opacity={group.evidence['opacity']}"
        )
    for group in [g for g in groupings if g.kind == "spanning"]:
        lines.append(
            f"  {group.id[:22]:22s} {group.evidence['spanner_text'] or '(untitled)'!r}"
            f" spans {group.evidence['spans']} ({group.evidence['gap_px']}px {group.evidence['side']})"
        )
    rows = [g for g in groupings if g.kind == "edge_row"]
    columns = [g for g in groupings if g.kind == "edge_column"]
    if rows or columns:
        lines.append(
            f"  edge-aligned bands: {len(rows)} rows, {len(columns)} columns"
            " (blocks sharing edges, side by side)"
        )
    scales = collections.Counter(
        g.scale for g in groupings if g.kind == "proximity" and len(g.members) >= 3
    )
    if scales:
        lines.append(
            "  proximity groups by scale: "
            + ", ".join(f"{scale}x={count}" for scale, count in sorted(scales.items()))
        )
    for group in sorted(fills, key=lambda g: -len(g.members))[:6]:
        lines.append(
            f"  fill {group.evidence['fill']:10s} {len(group.members):4d} elements"
            f"  ({group.evidence['share_of_coloured']:.0%} of coloured)"
        )
    aligned = collections.Counter(
        g.kind for g in groupings if g.kind.startswith("aligned_")
    )
    if aligned:
        lines.append(
            "  alignment: " + ", ".join(f"{k.split('_')[1]}s {n}" for k, n in aligned.items())
        )

    loose = [e for e in elements if e.id not in attached]
    lines += [
        "",
        f"UNATTACHED to any declared structure: {len(loose)} of {len(elements)}"
        f"  ({', '.join(f'{k} {n}' for k, n in collections.Counter(e.kind for e in loose).most_common(5))})",
        "",
        f"extract written to {output}",
        "query it with: python3 scripts/query.py <path> <command>",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", help="board URL or the id inside it")
    parser.add_argument("--out", type=Path, help="where to write the extract")
    parser.add_argument("--settle", type=float, default=20.0, help="seconds to keep reading")
    args = parser.parse_args()

    board_id = board_id_from(args.board)
    try:
        live = session_module.harvest_session(board_id)
    except (session_module.ChromeUnavailable, session_module.MiroNotAuthenticated) as err:
        print(f"session: {err}", file=sys.stderr)
        return 2

    known_ids = frozenset(inventory.widget_ids(board_id, live))
    try:
        records = rtc.read_board(board_id, live, known_ids, settle_seconds=args.settle)
    except rtc.BoardUnreadable as err:
        print(f"gateway: {err}", file=sys.stderr)
        return 3

    raw = [{"id": r.widget_id, "kind": r.kind, "payload": r.payload} for r in records]
    missing = known_ids - {r.widget_id for r in records if r.widget_id}
    elements, edges = model.build(raw)
    groupings = grouping.candidates(elements, edges)

    by_id = {e.id: e for e in elements}
    text_areas = [e.area for e in elements if e.kind == "text" and e.area]
    median_text = sorted(text_areas)[len(text_areas) // 2] if text_areas else 0.0

    output = args.out or DEFAULT_OUTPUT_DIR / f"{re.sub(r'[^A-Za-z0-9_-]', '_', board_id)}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "board": {
                    "id": board_id,
                    "inventory_widgets": len(known_ids),
                    "missing_widgets": sorted(missing),
                },
                "elements": [dataclasses.asdict(e) for e in elements],
                "edges": [dataclasses.asdict(e) for e in edges],
                "groupings": [
                    dataclasses.asdict(g)
                    | {"label_candidates": grouping.label_candidates(g, by_id, median_text)}
                    for g in groupings
                ],
            },
            indent=1,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(_summary(board_id, elements, edges, groupings, missing, len(known_ids), output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
