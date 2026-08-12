# miro-board

Reads a Miro board through your own browser session, and helps an agent say what is on it.

## Why not the API

Miro's public API is bound to a pair of user and team, and the app has to be installed on the team that owns the board. A board you were invited to in a client's workspace answers 404 no matter that you can open it in a tab. The page is no help either: Miro renders the canvas in WebAssembly and WebGL, so the content never enters the DOM and there is nothing to scrape. The one path that matches "any board I can open" is the session the browser already holds.

## Install

```
/plugin marketplace add nexaedge/nexaedge-marketplace
/plugin install miro-board@nexaedge-marketplace
```

Needs Python 3 with the `websockets` package, and Chrome running with remote debugging on port 9222, signed in to Miro.

## How it reads

Chrome is opened once, on the board. That single step does three jobs: it proves the session is still valid, it proves the signed-in account can open *that* board, and it reads the client build number the handshake has to claim. The tab closes and everything after it is a socket to Miro's realtime gateway. **No credential is written anywhere** — it lives in memory for the length of the run.

The board arrives whole on the first push, which was verified on boards of 46, 450, 120 and 52 widgets covering flowcharts, a workshop board, typed diagram stencils, a kanban and a mindmap. The read is checkable rather than hopeful: Miro's internal REST endpoint returns the authoritative list of widget ids, ids are recovered from the binary envelope by matching against that list, and anything the gateway did not send is reported as missing.

## What it does not do

It does not decide what the board means, and that separation is the point.

A Miro board records almost none of its own structure. Frames, connectors, kanban columns and mindmap topology are declared and can be trusted; everything else is arrangement. On a diagram-tool board that can be all of it, and on a workshop board of loose sticky notes it was under 30%. So the scripts measure and stop: proximity at six scales instead of one, because a real org chart resolved into its teams at one scale and collapsed into a single blob at the next; drawn rectangles as containers, since people box a theme instead of using a frame; edge-aligned bands and the block that spans one, which is how a platform under four product lines is drawn and which no containment test can find; colour cohorts; and, for every grouping, the nearby texts that might name it, each with its offset from the centre axis and its size relative to other text.

Every element belongs to several candidate groupings at once, each carrying the measurement that put it there. Choosing between them is reading, not measuring, and that is the agent's half.

## Layout

```
skills/miro-board/
  SKILL.md              the method, written for an agent with no prior context
  scripts/extract.py    board URL in, summary out, extract on disk
  scripts/query.py      the questions: groups, refine, inside, near, find, residue
  scripts/session.py    the Chrome step
  scripts/rtc.py        the gateway handshake and frame decoding
  scripts/inventory.py  the widget id list that makes completeness checkable
  scripts/model.py      normalisation: absolute geometry, colour per kind, plain text
  scripts/grouping.py   the candidate groupings and their evidence
  references/           the wire protocol, and the widget vocabulary
```

`references/protocol.md` is written for the day it breaks. The likeliest cause is the client version, which is why it is read live from the browser on every run rather than pinned in the code.
