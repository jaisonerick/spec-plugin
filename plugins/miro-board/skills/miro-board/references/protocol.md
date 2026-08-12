# How the reading works, for when it breaks

Miro's public REST API is not usable here: a token is bound to a pair of user and team, and the app must be installed on the team that owns the board. A board you were invited to in someone else's team returns 404. The board is also not scrapeable from the page, because Miro renders the canvas in WebAssembly and WebGL and the content is never in the DOM.

What works is the browser session against Miro's own two internal channels.

## Internal REST, cookie-authenticated

`https://miro.com/api/v1/...` accepts the session cookies. Field selection is GraphQL-like in a `fields` parameter, and the collection wrapper matters: `fields=data{id}` works, bare `fields=id` returns `400 Field 'id' does not exist`. Unknown fields inside `data{...}` are dropped silently, so the error is only an oracle at the top level.

- `GET /api/v1/boards/{urlencoded_id}/widgets` returns `{total, data:[{id, createdAt, updatedAt}]}`. **Inventory only: no content, no type.**
- `GET /api/v1/boards/{id}/widgets/{widgetId}` → 404. There is no per-widget read.
- POSTs need an `x-csrf-token` header.

The inventory is what makes the read verifiable. It is the authoritative id list, so `missing_widgets` is a real check rather than a hope.

## The realtime gateway, where the content is

`wss://miro.com/rtc-gateway/mux?client_auth_user_id={userId}`, with the session cookies and a browser `User-Agent` on the upgrade.

Frames are binary: a six-byte header `[0, kind_hi, kind_lo, 0, 0, 1]` then payload, which is either plain ASCII or zlib-deflate starting at magic `78 9c`.

**The channel-open frame** carries a string map of `boardId`, `client_platform`, `client_version`, `last_known_time`, `app_type`, `device_os`, `anonymous_id`, `app_mode`. `last_known_time: 0` is what requests the complete state instead of deltas. `build_open_frame` in `rtc.py` reproduces it byte-for-byte.

The server answers with `CanvasObjectsPreloader.load`, zlib-compressed, containing length-prefixed records that each hold **a plain JSON string**. The whole board arrives on this initial push; viewport-aware loading governs rendering, not the wire.

**Send nothing else after the open frame.** An unexpected frame makes the gateway go silent without closing the connection, which looks exactly like an authentication failure and is not one.

## Recovering ids and types

Neither is in the JSON. Both are in the binary envelope preceding it.

The **widget id** is an eight-byte big-endian integer, 23 or 24 bytes before the JSON; the one-byte variance is the length of the type name. It is matched against the REST inventory rather than decoded blind, which resolves ids and proves completeness in the same step.

The **type tag** is a lowercase name stored immediately after its own length byte. Reading it as "the last run of lowercase letters" mislabels roughly one record in seven, because id bytes fall in the ASCII lowercase range.

## Where it will break

`client_version` is read live from `window.rtb.version` on every run, which is why the Chrome step is not optional. If Miro starts rejecting the handshake, that is the first thing to check. `session.py` fails loudly when the board never boots, which is the same signal as not being signed in.
