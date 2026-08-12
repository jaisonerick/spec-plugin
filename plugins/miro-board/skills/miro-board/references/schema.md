# The widget vocabulary

Observed across four boards of 46, 450, 120 and 52 widgets. `extract.py` normalises most of this; read here when something looks missing or wrong.

## No kind has a stable key set

`shape` appeared with three distinct key signatures, `line` with four, `text` with three. A field is written only when it has a value, and older clients wrote fewer of them. **Treat every field as optional.** A parser that requires `relativeScale` works on a board made this year and fails on one made three years ago.

## Style keys differ per kind

This is the one that silently returns null and looks like an answer.

| Kind | Fill | Notes |
| --- | --- | --- |
| `sticker` | `sbc` | also `fs`, `ta`, `tav`, `taw`, `tah`, `lh`. No `bc`. |
| `shape` | `bc` | plus `bo` opacity, `brc`/`brw`/`brs` border, `st` shape type, `fs` |
| `text` | `bc` | **no font size at all**; the box size is the size. `fw`, `b`, `i`, `u`, `s` |
| `line` | `lc` | `lt` type, `a_start`/`a_end` arrowheads, `jump` |

Colours are decimal integers; `-1` means none. `extract.py` exposes them as `#RRGGBB` in `fill`.

**Arrowheads carry direction.** `a_end` non-zero means the arrow points at the secondary widget. `(0,0)` on both ends is an undirected line, which is association rather than sequence. A mindmap's edges are all `(0,0)`.

## Positioning comes in three schemes

`_position.schema` says which:

- `canvasOffsetPx` — absolute board coordinates
- `parentOffsetPx` — relative to `_parent`, so it must be resolved up the chain
- `kanbanOrder` — an ordinal, not pixels at all

Mixing them corrupts any spatial reasoning quietly, because the numbers look plausible either way. `extract.py` resolves everything to absolute centres.

## `ns:*` is where specialised meaning lives

| Field | On | Carries |
| --- | --- | --- |
| `ns:diagrammingNotation` | stencil | `{element: "flowchart-terminator", collection: "flowchart"}`, what the node *is* |
| `schema` | stencil | the stencil template and its computed geometry |
| `ns:kanbanRoot` | kanban | every column (uuid, title, wipLimit, subColumns) inside one widget |
| `ns:assignee`, `ns:dueDate` | card | assignment and dates |
| `ns:mindmap` | text, line | topology, theme and layout |
| `ns:miroAI` | stencil, diagram, line | `{createdWithAI: true, lastModifiedAt}` |
| `ns:diagrammingTheme` | shape | the palette the diagram was drawn in |

**Container structure is sometimes a payload, not a layout.** A kanban's columns are a list inside the kanban widget and its cards reference their place by ordinal. Nothing in the geometry says which column a card is in, so grouping kanban cards spatially produces a plausible wrong answer.

## Kinds seen

`shape`, `text`, `sticker`, `line`, `frame`, `image`, `stencil`, `diagram`, `kanban`, `card`. Every board also carries exactly one record with `app_metadata`, `presentations`, `properties`, `reactionsConfig`, `userStatuses`, `widgetsAliases`, which is board settings rather than a widget and has no id. `extract.py` drops it.

## Text is HTML

`<p>` wrappers and HTML entities. `extract.py` flattens it to plain text; the original markup is not preserved, so bold and line breaks are lost. If that matters for a board, read the raw payload.
