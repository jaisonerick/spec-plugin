---
name: miro-board
description: >-
  Read and interpret any Miro board the user can open, without the Miro API or an
  installed app. Use when asked what a board contains, to summarise or explain one,
  to pull its flow, groupings or notes into text, or to answer questions about a
  board from its URL.
---

# miro-board

Reads a board through the browser session, then helps you say what is on it.

The reading is solved and mechanical. The interpretation is not, and it is the whole job: a board carries meaning in where things sit, what colour they are and what is drawn around them, and almost none of that is recorded as structure. This skill splits those two problems on purpose. **The scripts measure and never conclude. You read the text and conclude.**

## Before you run anything

Chrome must be running with remote debugging on port 9222 and signed in to Miro. `extract.py` opens the board in a tab, reads the live session and the client build, and closes the tab. Nothing is stored: the credential lives in memory for the length of the run.

If it reports that the board never booted, the user is not signed in to an account that can open that board. Say so and stop; do not look for another way in.

Python needs the `websockets` package. If the import fails, say what is missing rather than working around it.

## Two commands

Both live next to this file. Call them by absolute path, from any directory: Python puts a script's own directory on the import path, so the modules resolve wherever you run it from. On Claude Code the skill root is `${CLAUDE_PLUGIN_ROOT}/skills/miro-board`; on other agents it is the directory holding this `SKILL.md`.

```bash
python3 <skill>/scripts/extract.py 'https://miro.com/app/board/<id>/'   # ~30s, writes /tmp/miro-board/<id>.json
python3 <skill>/scripts/query.py /tmp/miro-board/<id>.json <command>
```

`extract.py` prints a summary and writes the full extract. **Read the summary, not the JSON.** The JSON is for `query.py` to answer specific questions; loading it whole wastes the context you need for the text.

| Query | Answers |
| --- | --- |
| `groups --kind declared_container` | what Miro itself says is grouped |
| `groups --kind proximity --scale 0.9 --min 8` | candidate clusters at one scale |
| `group <id>` | one grouping: members, their text, label candidates |
| `refine <id> --scales 0.5 0.7 0.9` | does this group hold together, or is it several |
| `element <id>` | one item and every grouping it participates in |
| `inside <id>` / `near <id>` | what a shape encloses, what sits beside an item |
| `text --kind sticker --fill '#EA94BB'` | the text of one colour cohort |
| `find <term>` | every element mentioning a term, and where it sits |
| `residue` | what no declared structure covers |

Everything is printed as extents, `x[left,right] y[top,bottom]`, not centres. That is deliberate: the relations that carry meaning on a board are between edges.

## The method

**Declared beats inferred, always.** Frame membership, connector endpoints, kanban columns and mindmap topology are recorded by Miro and are fact. Proximity, colour and alignment are measurements you are interpreting. Never present the second kind as the first.

How much is declared varies enormously and is a property of the board, not of your effort. A board built with the diagramming tool can be 100% declared. A workshop board of loose sticky notes can be under 30%. The summary tells you which one you have, and it should change how confident you sound.

**A board is not one thing.** It is regions, and they are usually of different kinds: a flow in one corner, an org chart in another, a legend, some stray notes. Classify per region. "This board is a flowchart" is almost always wrong.

**No proximity scale is the right one.** The extract clusters at six scales because structure appears in a band and vanishes outside it. On a real org chart, one scale merged thirty stickers into a single blob while a finer one resolved the three teams cleanly. When a grouping matters, `refine` it and look at where it splits. `scales_with_same_members` in the evidence tells you how stable a grouping is: high means uncontroversial, low means this is exactly where your reading is doing the work.

**An element belongs to many groupings at once**, and that is deliberate. The same sticky note is in a proximity cluster at 0.7x, another at 0.9x, a colour cohort, and possibly a drawn rectangle. All are reported. Deciding which one expresses the author's intent is reading, not measuring.

**A block as wide as the row above it is a layer, not a sibling.** This is the `spanning` grouping, and it is the one structure that neither containment nor proximity can find, because the spanning block encloses nothing and touches everything. It is how a platform under four product lines is drawn, how a table header sits over its columns, and how a manager sits over the roles reporting to them. The evidence names the spanner, what it spans and the gap in pixels. Read the summary for these before anything else: they carry the architecture of a region in one line, and mistaking a layer for a sibling inverts the meaning of the whole picture.

`edge_row` and `edge_column` are the underlying bands, blocks sharing two opposite edges and sitting end to end. Swimlanes, table columns and stacked layers are all built this way, out of blocks of different sizes, which is why comparing centres misses them.

**A term that appears once on a whole board marks a region that speaks a different language.** `find` answers that in one call. When a region uses names the rest of the board never uses, it usually came from another conversation, another moment or another level of the organisation, and reading it as part of the main argument is a mistake.

**Labels are candidates with measurements, never answers.** For each grouping you get nearby texts with the offset from its centre axis, the distance above it, the size relative to other text and the character count. Centring identifies a title; size does not. The largest text near a group is usually a legend or an explanation. A short, centred one is usually the name. Read them and decide.

**Colour is a category, not a caption.** Testing showed the "differently coloured note is the group's title" idea does not hold. What colour does encode is a type the author chose: people, roles, areas, actions. Pull the text of a cohort with `text --fill` and the scheme usually becomes obvious in one read.

## Working through a board

1. Run `extract.py` and read the summary: size, kinds, how much is declared, how much is loose.
2. Take the declared structure as the skeleton. For each container and each connected component, read the members' text with `group`.
3. **Check the container's own title before trusting it.** Miro names frames `Frame 1`, `Frame 2` by default, and authors rarely rename them. The real section name is usually a text element sitting above the frame, which appears in the label candidates.
4. For the residue, list proximity candidates, `refine` the big ones, and read the text at the scale where the split looks meaningful.
5. Use colour cohorts to find the categorical dimension.
6. Say what you could not attach to anything.

## What to report

Structure first, then meaning, and mark which is which. A useful answer says what the regions are, what each one is about, and how the items in it relate. It also says, plainly, how much of that was read off declared structure and how much you inferred from layout.

**Always report the residue.** If 300 of 418 items were grouped only by geometry, say so. That is the difference between a tool the user can trust and one that is confidently wrong, and the user cannot tell from the prose alone.

Do not invent a hierarchy Miro does not record and geometry does not support. "These twelve notes sit together and all mention roles" is a finding. "These twelve notes report to that one" needs an arrow or an unambiguous layout.

## Traps that have already cost time

**The style vocabulary differs per widget kind.** A sticky note keeps its colour in `sbc`, a shape in `bc`, and a text element has no font size at all. `extract.py` normalises this into `fill`, so use that. The reason it matters to you: if you go back to raw payloads and read a field generically, you get null, and a broken reader is indistinguishable from a refuted hypothesis.

**Not every line is a widget.** On a mindmap, edges are implied by the structure and are not stored as objects. Connectors are the edge list for flowcharts, not for mindmaps.

**Duplicate items are real.** Boards contain the same note twice, adjacent. It may be an accident, emphasis, or the same person in two places. Report it; do not silently collapse it.

**Positions come in three schemes** and `extract.py` has already resolved them to one absolute frame. Do not recompute geometry from the raw payload.

`references/protocol.md` is how the transport works, for when it breaks. `references/schema.md` is the widget vocabulary: kinds, style keys per kind, and what each `ns:*` extension carries.
