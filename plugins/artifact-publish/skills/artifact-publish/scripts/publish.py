#!/usr/bin/env python3
"""Publish a self-contained HTML file as an artifact and print the link.

    publish.py report.html                 publish with the default account
    publish.py report.html --as acme.com   publish as another domain's account
    publish.py report.html --share 7       also return a link that needs no login
    publish.py report.html --slug proposal force the folder on the server
    publish.py --whoami [--as acme.com]    show the signed-in account
    publish.py --logout [--as acme.com]    forget the account on this machine

THE ACCOUNT DECIDES WHO CAN OPEN IT. An artifact belongs to the domain of the
Google account that published it, and only accounts of that domain can open it.
Publishing a client's material under your own domain leaves the client out of it.

Standard library only, on purpose: this ships as a plugin and cannot depend on
any project's environment. Authorization is a Google sign-in, not a cloud
credential: the first run per account opens a browser, then the refresh token
stays on this machine with mode 600.

Optional config at ~/.config/nexaedge/artifacts.json — every key is optional:

    {
      "service": "https://artifacts.nexaedge.com",
      "default_domain": "acme.com",
      "accounts": {"acme.com": "you@acme.com"}
    }

`accounts` only preselects the account on Google's screen. `default_domain` is
the account used without `--as`; with a single account signed in, that one wins
and no config is needed at all.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import json
import os
import re
import secrets
import stat
import sys
import threading
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any, NamedTuple

CONFIG_FILE = Path.home() / ".config" / "nexaedge" / "artifacts.json"
SESSION_DIR = Path.home() / ".config" / "nexaedge" / "artifact-share"
DEFAULT_SERVICE = "https://artifacts.nexaedge.com"

TIMEOUT = 30
LOGIN_TIMEOUT = 300
CONTENT_TYPE = "text/html; charset=utf-8"

# Cloudflare rejects urllib's default User-Agent ("Python-urllib/3.x") with error
# 1010, the browser integrity check. Identifying ourselves fixes it, and is the
# right thing anyway: whoever reads the service log deserves to know who called.
USER_AGENT = "artifact-publish/1.0 (+https://artifacts.nexaedge.com)"

_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

# Names that name a file, not a document. Publishing under one of these means
# publishing something nobody finds again in the listing.
_DULL = {"index", "report", "untitled", "document", "page", "output"}


class Failure(RuntimeError):
    """Failed in a way the user needs to read, without a traceback."""


# --- configuration -----------------------------------------------------------


def config() -> dict[str, Any]:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text())
    except (OSError, ValueError) as exc:
        raise Failure(f"{CONFIG_FILE} is not readable JSON: {exc}") from exc


def service_url() -> str:
    return str(
        os.environ.get("ARTIFACTS_SERVICE") or config().get("service") or DEFAULT_SERVICE
    ).rstrip("/")


class Account(NamedTuple):
    domain: str
    """Sign-in hint, when the config knows the address. Empty is fine."""
    email: str = ""

    @property
    def session_file(self) -> Path:
        # One file per domain. The service hosts several domains, and a single
        # file would silently publish the next artifact under the previous
        # account's domain, which is who gets to read it.
        return SESSION_DIR / f"{self.domain}.json"


def signed_in_domains() -> list[str]:
    if not SESSION_DIR.is_dir():
        return []
    return sorted(p.stem for p in SESSION_DIR.glob("*.json"))


def pick_account(asked: str | None) -> Account:
    """`--as`, then the configured default, then the only account signed in.

    With none of those it returns an empty domain, and the sign-in runs without
    a domain hint: whichever corporate account the person picks defines it. That
    is what makes the first run work with no configuration.
    """
    accounts = {str(k).lower(): str(v) for k, v in (config().get("accounts") or {}).items()}

    if asked:
        asked = asked.strip().lower().lstrip("@")
        if "@" in asked:
            return Account(asked.split("@")[-1], asked)
        return Account(asked, accounts.get(asked, ""))

    padrao = str(config().get("default_domain") or "").lower()
    if padrao:
        return Account(padrao, accounts.get(padrao, ""))

    existing = signed_in_domains()
    if len(existing) == 1:
        return Account(existing[0], accounts.get(existing[0], ""))
    if len(existing) > 1:
        raise Failure(
            "More than one account is signed in and no default is set: "
            f"{', '.join(existing)}.\nPick one with --as <domain>, or set "
            f'"default_domain" in {CONFIG_FILE}.'
        )
    return Account("", "")


# --- HTTP with the standard library ------------------------------------------


def _request(url: str, *, data: bytes | None = None, headers: dict[str, str] | None = None,
             method: str = "GET") -> tuple[int, bytes]:
    request = urllib.request.Request(
        url, data=data, headers={"User-Agent": USER_AGENT, **(headers or {})}, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()
    except urllib.error.URLError as exc:
        raise Failure(f"Could not reach {url}: {exc.reason}") from exc


def _error_of(body: bytes, status: int) -> str:
    try:
        return str(json.loads(body).get("error") or body.decode()[:200])
    except (ValueError, UnicodeDecodeError):
        return body.decode(errors="replace")[:200] or f"HTTP {status}"


# --- stored session ----------------------------------------------------------


def _load(account: Account) -> dict[str, Any]:
    if not account.domain or not account.session_file.exists():
        return {}
    try:
        return json.loads(account.session_file.read_text())
    except (OSError, ValueError):
        return {}


def _store(domain: str, data: dict[str, Any]) -> None:
    path = SESSION_DIR / f"{domain}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
    # 600: a refresh token is worth a whole Google account until it is revoked.
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def signed_in_as(account: Account) -> str | None:
    return _load(account).get("email")


def forget(account: Account) -> bool:
    if account.domain and account.session_file.exists():
        account.session_file.unlink()
        return True
    return False


# --- Google sign-in ----------------------------------------------------------


def _oauth_config(service: str) -> dict[str, Any]:
    """The OAuth client comes from the service, so this plugin carries none."""
    status, body = _request(f"{service}/api/publish/config")
    if status != 200:
        raise Failure(
            f"{service} did not return the sign-in configuration ({status}). "
            f"{_error_of(body, status)}"
        )
    parsed = json.loads(body)
    missing = [k for k in ("client_id", "client_secret", "auth_uri", "token_uri")
               if not parsed.get(k)]
    if missing:
        raise Failure(f"Sign-in configuration is incomplete (missing {', '.join(missing)}).")
    return parsed


class _Catcher(http.server.BaseHTTPRequestHandler):
    """Receives Google's redirect and keeps the query."""

    result: dict[str, str] = {}

    def do_GET(self) -> None:  # noqa: N802 (name required by BaseHTTPRequestHandler)
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if "code" not in query and "error" not in query:
            self.send_error(404)  # favicon and friends
            return
        _Catcher.result = {k: v[0] for k, v in query.items()}
        body = (
            "<!DOCTYPE html><meta charset=utf-8>"
            "<style>body{font-family:-apple-system,system-ui,sans-serif;"
            "text-align:center;padding-top:20vh;color:#0f172a}</style>"
            "<h2>Done.</h2><p>You can close this tab and go back to the terminal.</p>"
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: Any) -> None:
        """Silence http.server's log, which would clutter the output."""


def _exchange(oauth: dict[str, Any], extra: dict[str, str]) -> dict[str, Any]:
    data = urllib.parse.urlencode(
        {"client_id": oauth["client_id"], "client_secret": oauth["client_secret"], **extra}
    ).encode()
    status, body = _request(
        oauth["token_uri"],
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    parsed = json.loads(body) if body else {}
    if status != 200:
        detail = f"{parsed.get('error', status)} {parsed.get('error_description', '')}"
        raise Failure(f"Google refused the token exchange: {detail.strip()}")
    return parsed


def _sign_in(account: Account, oauth: dict[str, Any]) -> dict[str, Any]:
    verifier = secrets.token_urlsafe(64)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    )
    state = secrets.token_urlsafe(16)

    _Catcher.result = {}
    server = http.server.HTTPServer(("127.0.0.1", 0), _Catcher)
    server.timeout = LOGIN_TIMEOUT
    redirect = f"http://127.0.0.1:{server.server_port}"

    params = {
        "client_id": oauth["client_id"],
        "redirect_uri": redirect,
        "response_type": "code",
        "scope": " ".join(oauth.get("scopes", ["openid", "email", "profile"])),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
        # offline + consent: without both, Google returns no refresh token and
        # the sign-in would come back every hour.
        "access_type": "offline",
        "prompt": "consent",
    }
    if account.domain:
        params["hd"] = account.domain
    if account.email:
        params["login_hint"] = account.email

    url = f"{oauth['auth_uri']}?{urllib.parse.urlencode(params)}"
    who = account.email or (f"an account of {account.domain}" if account.domain
                            else "your work Google account")
    print(f"Opening the browser to sign in as {who}…", file=sys.stderr)
    if not webbrowser.open(url):
        print(f"Could not open a browser. Open this URL:\n{url}", file=sys.stderr)

    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    while thread.is_alive() and not _Catcher.result:
        thread.join(timeout=0.5)
    server.server_close()

    result = _Catcher.result
    if not result:
        raise Failure("The sign-in did not come back in time. Run it again.")
    if "error" in result:
        raise Failure(f"Google refused the sign-in: {result['error']}")
    if result.get("state") != state:
        raise Failure("The returned `state` does not match. Sign-in discarded.")

    return _exchange(
        oauth,
        {
            "code": result["code"],
            "grant_type": "authorization_code",
            "redirect_uri": redirect,
            "code_verifier": verifier,
        },
    )


def _email_in(raw_id_token: str) -> str:
    """The e-mail inside the ID token, for display only.

    Deliberately unverified: the service verifies it, and verifying here would
    give a false sense of guarantee — this value decides nothing.
    """
    try:
        payload = raw_id_token.split(".")[1]
        padded = payload + "=" * (-len(payload) % 4)
        return str(json.loads(base64.urlsafe_b64decode(padded)).get("email", ""))
    except (IndexError, ValueError):
        return ""


def id_token(account: Account, service: str, *, relogin: bool = False) -> tuple[str, str]:
    """A fresh ID token, signing in through the browser when needed."""
    stored = _load(account)
    # The stored account has to belong to the requested domain. Reusing another
    # domain's session would publish in the wrong place, which is who can read it.
    same = bool(account.domain) and str(stored.get("email", "")).endswith(f"@{account.domain}")

    if not relogin and same and stored.get("refresh_token"):
        try:
            body = _exchange(
                _oauth_config(service),
                {"grant_type": "refresh_token", "refresh_token": stored["refresh_token"]},
            )
            if body.get("id_token"):
                return str(body["id_token"]), str(stored.get("email", ""))
        except Failure:
            # Revoked or expired: fall through to the browser, which is what the
            # person would do next anyway.
            pass

    body = _sign_in(account, _oauth_config(service))
    raw = body.get("id_token")
    if not raw:
        raise Failure("Google returned no ID token. Check the client's scopes.")

    email = _email_in(str(raw))
    domain = email.split("@")[-1] if "@" in email else account.domain
    if not domain:
        raise Failure("Could not tell the account's domain from the sign-in.")
    _store(
        domain,
        {
            "service": service,
            "email": email,
            "refresh_token": body.get("refresh_token", stored.get("refresh_token", "")),
        },
    )
    if email:
        print(f"Signed in as {email}.", file=sys.stderr)
    return str(raw), email


# --- publishing --------------------------------------------------------------


def title_of(html: str, fallback: str) -> str:
    found = _TITLE.search(html)
    if not found:
        return fallback
    return " ".join(found.group(1).split())[:200] or fallback


def dull_title_warning(title: str) -> str | None:
    if title.strip().lower().removesuffix(".html") in _DULL:
        return (
            f"The title came out as {title!r}, which names a file and not a document: that is "
            "how it will show up in the listing and in the tab of whoever opens it.\n"
            "Give it a <title> that says what the document is, then publish again. It can also "
            "be fixed later by clicking the title in the bar at the top of the link."
        )
    return None


def remote_path(local: Path, slug: str | None) -> str:
    folder = slug or local.parent.name
    if folder in ("", ".", "/"):
        folder = local.stem
    plain = unicodedata.normalize("NFKD", folder).encode("ascii", "ignore").decode()
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", plain).strip("-").lower() or "artifact"
    return f"{safe}/{local.name}"


def publish(account: Account, path: str, slug: str | None, share_days: int,
            relogin: bool) -> dict[str, str]:
    local = Path(path).expanduser()
    if not local.is_file():
        raise Failure(f"{local} does not exist.")
    if local.suffix.lower() != ".html":
        raise Failure(f"{local.name} is not .html. The service hosts self-contained HTML.")

    html = local.read_bytes()
    title = title_of(html.decode(errors="replace"), local.stem)
    warning = dull_title_warning(title)
    if warning:
        print(warning, file=sys.stderr)

    service = service_url()
    target = remote_path(local, slug)
    token, _ = id_token(account, service, relogin=relogin)

    query = {"path": target, "title": title}
    if share_days:
        query["share_days"] = str(share_days)

    status, body = _request(
        f"{service}/api/publish?{urllib.parse.urlencode(query)}",
        data=html,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": CONTENT_TYPE,
            # The service requires it: checking a quota against an unknown size
            # is not checking it.
            "Content-Length": str(len(html)),
        },
        method="POST",
    )

    if status in (401, 403):
        raise Failure(
            f"{_error_of(body, status)}\n"
            "Publishing needs a signed-in work Google account. Switch accounts with --relogin."
        )
    if status >= 400:
        raise Failure(f"The service refused it ({status}): {_error_of(body, status)}")

    return {str(k): str(v) for k, v in json.loads(body).items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="publish.py", description=__doc__)
    parser.add_argument("file", nargs="?", help="the self-contained .html")
    parser.add_argument("--as", dest="account", metavar="DOMAIN",
                        help="account that publishes (default: the configured or only one)")
    parser.add_argument("--slug", help="folder on the server (default: the file's folder)")
    parser.add_argument("--share", type=int, default=0, metavar="DAYS",
                        help="also return a link that opens without sign-in (max 30)")
    parser.add_argument("--no-open", action="store_true", help="do not open the browser")
    parser.add_argument("--relogin", action="store_true", help="sign in again")
    parser.add_argument("--whoami", action="store_true", help="show the signed-in account")
    parser.add_argument("--logout", action="store_true", help="forget the account here")
    args = parser.parse_args(argv)

    try:
        account = pick_account(args.account)

        if args.logout:
            print("Account forgotten." if forget(account) else "No account was stored.")
            return 0

        if args.whoami:
            who = signed_in_as(account)
            if who:
                print(who)
            else:
                others = signed_in_domains()
                print("Nobody signed in." + (f" Signed in elsewhere: {', '.join(others)}."
                                             if others else ""))
            return 0

        if not args.file:
            parser.error("missing the .html file (or use --whoami / --logout)")

        result = publish(account, args.file, args.slug, args.share, args.relogin)
    except Failure as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(result["url"])
    if result.get("share_url"):
        print(f"{result['share_days']}-day link, no sign-in: {result['share_url']}")
    if not args.no_open:
        webbrowser.open(result["url"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
