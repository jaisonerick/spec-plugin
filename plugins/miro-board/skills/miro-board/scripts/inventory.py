"""The board's widget inventory, used to tell a partial read from a complete one."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from session import MiroSession

_WIDGETS_URL = "https://miro.com/api/v1/boards/{board_id}/widgets?fields={fields}"


def _get(url: str, session: MiroSession) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Cookie": session.cookie_header,
            "Accept": "application/json",
            "x-client-version": session.client_version,
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def widget_count(board_id: str, session: MiroSession) -> int:
    url = _WIDGETS_URL.format(board_id=urllib.parse.quote(board_id, safe=""), fields="total")
    return int(_get(url, session)["total"])


def widget_ids(board_id: str, session: MiroSession, limit: int = 5000) -> list[str]:
    url = (
        _WIDGETS_URL.format(board_id=urllib.parse.quote(board_id, safe=""), fields="data{id}")
        + f"&limit={limit}"
    )
    return [widget["id"] for widget in _get(url, session)["data"]]
