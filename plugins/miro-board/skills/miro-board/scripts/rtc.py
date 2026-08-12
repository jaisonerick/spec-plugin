"""Read a board's objects from Miro's realtime gateway, with no browser attached."""

from __future__ import annotations

import json
import zlib
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from websockets.exceptions import WebSocketException
from websockets.sync.client import connect

from session import MiroSession

GATEWAY_URL = "wss://miro.com/rtc-gateway/mux?client_auth_user_id={user_id}"
_ORIGIN = "https://miro.com"
_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
)
_OPEN_CHANNEL_HEADER = b"\x00\x12\x00\x00\x00\x01"
_STRING_TAG = b"\x05"
_MAP_TERMINATOR = b"\x00"
_ZLIB_MAGIC = b"\x78\x9c"
_FULL_STATE = "0"
_ENVELOPE_LOOKBACK = 40
_WIDGET_ID_BYTES = 8


class BoardUnreadable(RuntimeError):
    """The gateway accepted the connection but never sent the board."""


@dataclass(frozen=True)
class BoardObject:
    """One record from the preloader: its widget id, its type tag and its JSON.

    The id and the type live in the binary envelope rather than in the JSON, so both
    are read back out of the bytes preceding the payload.
    """

    widget_id: str | None
    kind: str
    payload: dict[str, Any]
    envelope: bytes = field(repr=False)

    @property
    def identity(self) -> str:
        """What makes two records the same widget rather than two look-alikes.

        Two empty sticky notes serialise to identical JSON, so the payload alone
        collapses them into one.
        """
        if self.widget_id:
            return self.widget_id
        return f"{self.kind}:{json.dumps(self.payload, sort_keys=True)}"


def _length_prefixed(value: str) -> bytes:
    encoded = value.encode("utf-8")
    if len(encoded) > 0xFF:
        raise ValueError(f"value too long for a one-byte length: {value!r}")
    return bytes([len(encoded)]) + encoded


def _string_map(entries: dict[str, str]) -> bytes:
    count = bytes([len(entries)])
    keys = b"".join(_length_prefixed(key) for key in entries)
    values = b"".join(_length_prefixed(value) for value in entries.values())
    return b"\x00" + count + count + keys + count + values + _MAP_TERMINATOR


def build_open_frame(board_id: str, session: MiroSession) -> bytes:
    """The frame that joins a board channel and asks for its complete state.

    `last_known_time` of zero is what makes the gateway send everything rather than
    the deltas since a previous connection.
    """
    handshake = _string_map(
        {
            "boardId": board_id,
            "client_platform": "html",
            "client_version": session.client_version,
            "last_known_time": _FULL_STATE,
            "app_type": "desktop",
            "device_os": "MacOS",
            "anonymous_id": session.anonymous_id,
            "app_mode": "full",
        }
    )
    return (
        _OPEN_CHANNEL_HEADER
        + _STRING_TAG
        + _length_prefixed(board_id)
        + len(handshake).to_bytes(2, "big")
        + handshake
    )


def _inflated_payloads(frame: bytes) -> Iterator[bytes]:
    offset = frame.find(_ZLIB_MAGIC)
    if offset < 0:
        yield frame
        return
    try:
        yield zlib.decompress(frame[offset:])
    except zlib.error:
        yield frame


def _object_end(buffer: bytes, start: int) -> int | None:
    depth = 0
    inside_string = False
    escaped = False
    for index in range(start, len(buffer)):
        byte = buffer[index]
        if inside_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                inside_string = False
            continue
        if byte == 0x22:
            inside_string = True
        elif byte == 0x7B:
            depth += 1
        elif byte == 0x7D:
            depth -= 1
            if depth == 0:
                return index + 1
    return None


def _kind_in(envelope: bytes) -> str:
    """The type tag is a lowercase name stored right after its own length byte."""
    for index in range(len(envelope) - 1, 0, -1):
        length = envelope[index - 1]
        if not 3 <= length <= 16:
            continue
        token = envelope[index : index + length]
        if len(token) == length and all(0x61 <= byte <= 0x7A for byte in token):
            return token.decode("ascii")
    return "unknown"


def _widget_id_in(envelope: bytes, known_ids: frozenset[str]) -> str | None:
    for offset in range(len(envelope) - _WIDGET_ID_BYTES + 1):
        candidate = str(
            int.from_bytes(envelope[offset : offset + _WIDGET_ID_BYTES], "big")
        )
        if candidate in known_ids:
            return candidate
    return None


def _objects_in(buffer: bytes, known_ids: frozenset[str]) -> Iterator[BoardObject]:
    cursor = 0
    while True:
        start = buffer.find(b'{"', cursor)
        if start < 0:
            return
        end = _object_end(buffer, start)
        if end is None:
            cursor = start + 1
            continue
        try:
            payload = json.loads(buffer[start:end])
        except (UnicodeDecodeError, json.JSONDecodeError):
            cursor = start + 1
            continue
        envelope = buffer[max(0, start - _ENVELOPE_LOOKBACK) : start]
        yield BoardObject(
            widget_id=_widget_id_in(envelope, known_ids),
            kind=_kind_in(envelope),
            payload=payload,
            envelope=envelope,
        )
        cursor = end


def read_board(
    board_id: str,
    session: MiroSession,
    known_ids: frozenset[str],
    settle_seconds: float = 12.0,
) -> list[BoardObject]:
    """Join the board channel and collect every object the gateway pushes.

    `known_ids` comes from the widget inventory and is what turns an eight-byte run in
    the envelope into a widget id, instead of guessing at the id encoding.
    """
    objects: list[BoardObject] = []
    seen: set[str] = set()
    url = GATEWAY_URL.format(user_id=session.user_id)
    headers = {
        "Cookie": session.cookie_header,
        "Origin": _ORIGIN,
        "User-Agent": _BROWSER_USER_AGENT,
    }

    with connect(url, additional_headers=headers, max_size=None, open_timeout=20) as socket:
        socket.send(build_open_frame(board_id, session))
        try:
            while True:
                frame = socket.recv(timeout=settle_seconds)
                if isinstance(frame, str):
                    continue
                for payload in _inflated_payloads(frame):
                    for board_object in _objects_in(payload, known_ids):
                        if board_object.identity in seen:
                            continue
                        seen.add(board_object.identity)
                        objects.append(board_object)
        except (TimeoutError, WebSocketException):
            pass

    if not objects:
        raise BoardUnreadable(
            "gateway sent no board objects; the client version may have been rejected"
        )
    return objects
