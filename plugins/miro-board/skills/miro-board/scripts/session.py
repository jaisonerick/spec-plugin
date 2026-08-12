"""Harvest a live Miro session from the running Chrome, without storing it."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from websockets.sync.client import connect

DEFAULT_CDP = "http://localhost:9222"
BOARD_URL = "https://miro.com/app/board/{board_id}/"
_BOOT_TIMEOUT_SECONDS = 45.0
_REQUIRED_COOKIES = ("token", "mr-anon-id-1")


class ChromeUnavailable(RuntimeError):
    """Chrome is not listening for automation on the debugging port."""


class MiroNotAuthenticated(RuntimeError):
    """The board never booted, so no signed-in Miro session is available."""


@dataclass(frozen=True)
class MiroSession:
    cookie_header: str
    user_id: str
    anonymous_id: str
    client_version: str


class _Tab:
    def __init__(self, socket: Any) -> None:
        self._socket = socket
        self._next_id = 0

    def call(self, method: str, **params: Any) -> dict[str, Any]:
        self._next_id += 1
        call_id = self._next_id
        self._socket.send(json.dumps({"id": call_id, "method": method, "params": params}))
        while True:
            message = json.loads(self._socket.recv())
            if message.get("id") != call_id:
                continue
            if "error" in message:
                raise RuntimeError(f"{method} failed: {message['error']}")
            return message.get("result", {})

    def evaluate(self, expression: str) -> Any:
        result = self.call(
            "Runtime.evaluate", expression=expression, returnByValue=True, awaitPromise=True
        )
        return result.get("result", {}).get("value")


def _open_tab(cdp_url: str, page_url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{cdp_url}/json/new?{urllib.parse.quote(page_url, safe='')}", method="PUT"
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.load(response)
    except OSError as err:
        raise ChromeUnavailable(
            f"no Chrome answering automation on {cdp_url}: {err}"
        ) from err


def _close_tab(cdp_url: str, target_id: str) -> None:
    request = urllib.request.Request(f"{cdp_url}/json/close/{target_id}", method="PUT")
    try:
        urllib.request.urlopen(request, timeout=10).close()
    except OSError:
        pass


def _wait_for_board_app(tab: _Tab) -> str:
    deadline = time.monotonic() + _BOOT_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        version = tab.evaluate("window.rtb && window.rtb.version")
        if version:
            return str(version)
        time.sleep(0.5)
    raise MiroNotAuthenticated(
        "the board never finished booting; sign in to Miro in Chrome and retry"
    )


def _read_cookies(tab: _Tab) -> dict[str, str]:
    tab.call("Network.enable")
    cookies = tab.call("Network.getCookies", urls=["https://miro.com"])["cookies"]
    return {cookie["name"]: cookie["value"] for cookie in cookies}


def _user_id(cookies: dict[str, str]) -> str:
    raw_profile = cookies.get("userInfo")
    if raw_profile:
        return str(json.loads(urllib.parse.unquote(raw_profile))["id"])
    return urllib.parse.unquote(cookies.get("ajs_user_id", "")).strip('"')


def harvest_session(board_id: str, cdp_url: str = DEFAULT_CDP) -> MiroSession:
    """Open the board in Chrome, read the live session and client build, close the tab.

    The board is opened every time on purpose: it is what proves the session is still
    valid and pins the client version the headless client will claim to be.
    """
    target = _open_tab(cdp_url, BOARD_URL.format(board_id=board_id))
    try:
        with connect(target["webSocketDebuggerUrl"], max_size=None) as socket:
            tab = _Tab(socket)
            tab.call("Page.enable")
            tab.call("Runtime.enable")
            client_version = _wait_for_board_app(tab)
            cookies = _read_cookies(tab)
    finally:
        _close_tab(cdp_url, target["id"])

    missing = [name for name in _REQUIRED_COOKIES if name not in cookies]
    if missing:
        raise MiroNotAuthenticated(f"session cookies missing: {', '.join(missing)}")

    return MiroSession(
        cookie_header="; ".join(f"{name}={value}" for name, value in cookies.items()),
        user_id=_user_id(cookies),
        anonymous_id=urllib.parse.unquote(cookies["mr-anon-id-1"]).strip('"'),
        client_version=client_version,
    )
