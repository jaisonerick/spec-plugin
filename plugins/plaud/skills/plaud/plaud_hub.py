#!/usr/bin/env python3
"""Plaud recordings engine.

Talks to the `plaud` CLI and, when the repository asks for one, maintains a
catalog of recordings. It has no opinion about where a transcript should be
filed: that belongs to the repository, declared in `.plaud.json` at its root.

Two modes, decided by whether `.plaud.json` sets `hub`:

  ad-hoc      No catalog. `fetch` brings one recording's transcript into a path
              you choose, and nothing is stored about it.
  catalog     `hub` names a directory holding catalog.jsonl (source of truth,
              git-tracked), a rebuildable sqlite index, and the raw transcripts
              and summaries pulled so far.

The `plaud` CLI it drives is a single Go binary. If one is not already on PATH,
this installs the pinned release into the user's data directory: no sudo, no
PATH changes, and nothing written inside the plugin, which is wiped on update.

Commands:
  doctor             Check the CLI, the authentication and this repository's setup.
  install            (Re)install the pinned CLI, without waiting to need it.
  config             Print the resolved configuration and mode.
  fetch ID           Download one transcript (and summary) to a path. Works in both modes.
  refresh            Merge `plaud list` + tags into catalog.jsonl, preserving curation.
  build              Recompile the sqlite index from catalog.jsonl.
  query SQL          Read-only query against the index, no sqlite3 binary needed.
  pull ID            fetch into the hub's raw store and record the paths in the catalog.
  set ID k=v ...     Edit curation fields of one recording, then run `build`.
  status             Print counts by status.
  gen-links          Regenerate the pending-transcription page from the catalog.

Run `plaud_hub.py <command> --help` for the flags of each.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(HERE, "schema.sql")
LINKS_TEMPLATE = os.path.join(HERE, "links_template.html")

# The CLI this skill is written against. Pinned rather than tracking the latest
# release, so the commands and flags documented here are the ones that run.
# Override with PLAUD_CLI_VERSION=latest, or with an explicit tag.
CLI_REPO = "jaisonerick/plaud-cli"
CLI_VERSION = "0.7.0"

CONFIG_NAME = ".plaud.json"
CONFIG_KEYS = {"hub", "scratch", "filing", "exclude_tags", "exclude_reason", "utc_offset"}

# Curation is set by a person or an agent, and a refresh never clobbers it.
CURATION_FIELDS = ("project", "path", "repo", "transcript_path", "summary_path", "notes")
# `status` is recomputed on refresh only while it still holds one of these.
AUTO_STATUS = {None, "", "pending", "transcribed"}

DB_COLUMNS = ["id", "filename", "start_time", "recorded_at", "duration_ms", "duration_min",
              "scene", "url", "is_trans", "is_summary", "tags", "project", "path", "repo",
              "status", "transcript_path", "summary_path", "excluded_reason", "notes"]


# --------------------------------------------------------------------------- repo & config

class Repo:
    """The repository the command is running against, plus its .plaud.json."""

    def __init__(self):
        self.root = _git_root() or os.getcwd()
        self.config_path = os.path.join(self.root, CONFIG_NAME)
        raw = {}
        if os.path.exists(self.config_path):
            try:
                raw = json.load(open(self.config_path))
            except json.JSONDecodeError as e:
                sys.exit(f"{self.config_path} is not valid JSON: {e}")
            unknown = sorted(set(raw) - CONFIG_KEYS)
            if unknown:
                print(f"warning: ignoring unknown key(s) in {CONFIG_NAME}: {', '.join(unknown)}",
                      file=sys.stderr)
        self.raw = raw
        self.hub = self._abs(raw.get("hub"))
        self.scratch = self._abs(raw.get("scratch"))
        self.filing = raw.get("filing")
        self.exclude_tags = set(raw.get("exclude_tags") or [])
        self.exclude_reason = raw.get("exclude_reason") or "excluded-by-config"
        self.utc_offset = raw.get("utc_offset")

    def _abs(self, value):
        return os.path.join(self.root, value) if value else None

    def rel(self, path):
        return os.path.relpath(path, self.root) if path else None

    # Hub layout, only meaningful when `hub` is configured.
    @property
    def catalog(self):
        return os.path.join(self.hub, "catalog.jsonl")

    @property
    def db(self):
        return os.path.join(self.hub, "recordings.db")

    @property
    def transcripts(self):
        return os.path.join(self.hub, "transcripts")

    @property
    def summaries(self):
        return os.path.join(self.hub, "summaries")

    @property
    def links_page(self):
        return os.path.join(self.hub, "ativar-transcricao.html")

    def require_hub(self, command):
        if not self.hub:
            sys.exit(f"`{command}` needs a catalog, and this repository has none.\n"
                     f"Set \"hub\" in {self.config_path} to the directory that should hold it, "
                     f"or use `fetch` to bring down a single transcript without a catalog.")
        os.makedirs(self.hub, exist_ok=True)
        return self.hub

    def local_time(self, epoch_ms):
        """Recording timestamps in the repository's timezone (local unless configured)."""
        tz = timezone(timedelta(hours=self.utc_offset)) if self.utc_offset is not None else None
        return datetime.fromtimestamp(epoch_ms / 1000, tz=tz).strftime("%Y-%m-%d %H:%M:%S")


def _git_root():
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None


# --------------------------------------------------------------------------- the CLI itself

_BIN = None


def plaud_bin(install=True):
    """Path to the plaud CLI, installing it into the user's data dir if needed.

    Order: PLAUD_BIN, then whatever is on PATH, then the copy this skill manages.
    Nothing here writes to the plugin's own directory, which is wiped on update.
    """
    global _BIN
    if _BIN:
        return _BIN
    candidate = os.environ.get("PLAUD_BIN") or shutil.which("plaud")
    if not candidate:
        managed = os.path.join(_managed_dir(), _bin_name())
        candidate = managed if os.path.exists(managed) else (install_cli() if install else None)
    if not candidate:
        sys.exit("the plaud CLI is not available. Run `plaud_hub.py install`")
    _BIN = candidate
    return _BIN


def _managed_dir():
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "plaud-cli", "bin")


def _bin_name():
    return "plaud.exe" if platform.system() == "Windows" else "plaud"


def _asset_name():
    systems = {"Darwin": "darwin", "Linux": "linux", "Windows": "windows"}
    machines = {"x86_64": "amd64", "amd64": "amd64", "arm64": "arm64", "aarch64": "arm64"}
    system = systems.get(platform.system())
    machine = machines.get(platform.machine().lower())
    if not system or not machine:
        sys.exit(f"no plaud-cli build for {platform.system()}/{platform.machine()}. "
                 f"Build it from source ({CLI_REPO}) and point PLAUD_BIN at it")
    return f"plaud-cli_{system}_{machine}" + (".exe" if system == "windows" else "")


def _resolve_version():
    version = os.environ.get("PLAUD_CLI_VERSION", CLI_VERSION)
    if version != "latest":
        return version.lstrip("v")
    url = f"https://api.github.com/repos/{CLI_REPO}/releases/latest"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)["tag_name"].lstrip("v")


def install_cli():
    """Download the pinned release into the user's data dir. No sudo, no PATH changes."""
    version = _resolve_version()
    asset = _asset_name()
    base = f"https://github.com/{CLI_REPO}/releases/download/v{version}"
    target = os.path.join(_managed_dir(), _bin_name())
    print(f"installing plaud-cli v{version} ({asset}) -> {target}", file=sys.stderr)

    try:
        with urllib.request.urlopen(f"{base}/checksums.txt", timeout=60) as r:
            checksums = r.read().decode()
        with urllib.request.urlopen(f"{base}/{asset}", timeout=300) as r:
            payload = r.read()
    except Exception as e:
        sys.exit(f"could not download plaud-cli v{version} from {base}: {e}")

    expected = next((l.split()[0] for l in checksums.splitlines()
                     if l.strip().endswith(asset)), None)
    if not expected:
        sys.exit(f"{asset} is not listed in the release checksums. Refusing to install")
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected:
        sys.exit(f"checksum mismatch for {asset}: expected {expected}, got {actual}")

    os.makedirs(_managed_dir(), exist_ok=True)
    tmp = target + ".part"
    with open(tmp, "wb") as f:
        f.write(payload)
    os.chmod(tmp, 0o755)
    os.replace(tmp, target)
    return target


def _token_expiry():
    """When the current session dies, read from the token itself.

    There is no refresh anywhere in this stack: an expired token can only be
    replaced by a fresh login, which needs a one-time code by email. So the
    expiry date is worth surfacing before it stops a task halfway.
    """
    token = os.environ.get("PLAUD_TOKEN")
    if not token:
        path = os.path.join(os.path.expanduser("~"), ".config", "plaud", "token.json")
        try:
            token = json.load(open(path)).get("access_token")
        except (OSError, ValueError):
            return None
    try:
        payload = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        return datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
    except Exception:
        return None


def _cli_version():
    out = subprocess.run([plaud_bin(), "--version"], capture_output=True, text=True)
    return out.stdout.strip().split()[-1] if out.returncode == 0 else "unknown"


def _supports(command):
    """Ask the CLI whether it has a command, instead of doing version arithmetic."""
    out = subprocess.run([plaud_bin(), command, "--help"], capture_output=True, text=True)
    return out.returncode == 0


# --------------------------------------------------------------------------- plaud CLI

def _plaud_json(args):
    out = subprocess.run([plaud_bin(), *args, "--json"], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"plaud {' '.join(args)} failed:\n{out.stderr.strip()}")
    return _first_json(out.stdout, f"plaud {' '.join(args)}")


def _first_json(text, what):
    """Parse the first JSON value in the output, tolerating banners around it."""
    start = min((i for i in (text.find("{"), text.find("[")) if i >= 0), default=-1)
    if start < 0:
        sys.exit(f"{what} produced no JSON:\n{text.strip()}")
    try:
        return json.JSONDecoder().raw_decode(text[start:])[0]
    except json.JSONDecodeError as e:
        sys.exit(f"{what} produced unreadable JSON: {e}")


def _probe(rid):
    """Current Plaud-side state of one recording."""
    info = _plaud_json(["info", rid])
    ready = {c.get("data_type") for c in info.get("content_list", []) if c.get("task_status") == 1}
    return {
        "id": info.get("file_id") or rid,
        "filename": info.get("file_name"),
        "start_time": info.get("start_time"),
        "duration_ms": info.get("duration"),
        "is_trans": any(t and t.startswith("transaction") for t in ready),
        "is_summary": any(t and "sum" in t for t in ready),
    }


def _download(rid, kind, target):
    """Download one content kind as markdown to `target`. Returns the path, or None."""
    tmp = tempfile.mkdtemp(prefix="plaud-")
    try:
        subprocess.run([plaud_bin(), "download", rid, f"--{kind}", "--format", "md",
                        "--output-dir", tmp], check=True)
        produced = [f for f in sorted(os.listdir(tmp)) if f.endswith(".md")]
        if not produced:
            return None
        os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        shutil.move(os.path.join(tmp, produced[0]), target)
        return target
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _generate(rid):
    if not _supports("generate"):
        sys.exit(f"this plaud CLI ({_cli_version()} at {plaud_bin()}) has no `generate` command.\n"
                 f"  Upgrade it, or let this skill install its own copy by unsetting PLAUD_BIN "
                 f"and taking `plaud` off PATH.")
    subprocess.run([plaud_bin(), "generate", rid, "--wait"], check=True)


# --------------------------------------------------------------------------- catalog

def load_catalog(repo):
    rows = {}
    if os.path.exists(repo.catalog):
        with open(repo.catalog) as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    rows[r["id"]] = r
    return rows


def save_catalog(repo, rows):
    ordered = sorted(rows.values(), key=lambda r: r.get("start_time") or 0, reverse=True)
    with open(repo.catalog, "w") as f:
        for r in ordered:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _slug(rec):
    day = (rec.get("recorded_at") or "")[:10] or "nodate"
    name = re.sub(r"[^\w\-]+", "-", rec.get("filename") or "").strip("-").lower()[:60]
    return f"{day}-{name or 'recording'}-{rec['id'][:8]}"


# --------------------------------------------------------------------------- commands

def cmd_config(repo, _args):
    print(json.dumps({
        "repo_root": repo.root,
        "config_file": repo.config_path if os.path.exists(repo.config_path) else None,
        "mode": "catalog" if repo.hub else "ad-hoc",
        "hub": repo.rel(repo.hub),
        "scratch": repo.rel(repo.scratch),
        "filing": repo.filing,
        "exclude_tags": sorted(repo.exclude_tags),
        "exclude_reason": repo.exclude_reason,
        "default_download_dir": repo.rel(_default_dir(repo)) if _default_dir(repo) else "(temp dir)",
    }, indent=2, ensure_ascii=False))
    if not os.path.exists(repo.config_path):
        print(f"\nNo {CONFIG_NAME} at {repo.root}. Running ad-hoc: `fetch` works, "
              f"nothing is stored, and where a transcript belongs is not declared anywhere.",
              file=sys.stderr)


def cmd_doctor(repo, _args):
    """Everything that has to be true for this skill to work, and whether it is."""
    binary = plaud_bin()
    auth = subprocess.run([binary, "me"], capture_output=True, text=True)
    source = "PLAUD_TOKEN" if os.environ.get("PLAUD_TOKEN") else "~/.config/plaud/token.json"
    lines = [
        f"python        {platform.python_version()} ({sys.executable})",
        f"plaud CLI     {_cli_version()} at {binary}",
        f"  generate    {'yes' if _supports('generate') else 'NO, cannot activate transcription'}",
        f"  auth        {'ok, from ' + source if auth.returncode == 0 else 'NOT AUTHENTICATED: ' + (auth.stderr or auth.stdout).strip()}",
    ]
    expiry = _token_expiry()
    if expiry:
        left = expiry - datetime.now(tz=timezone.utc)
        warn = "  <-- renew it, there is no refresh" if left.days < 21 else ""
        lines.append(f"  expires     {expiry.date()} ({left.days} days){warn}")
    lines += [
        f"repository    {repo.root}",
        f"  config      {repo.config_path if os.path.exists(repo.config_path) else 'none (ad-hoc, no filing declared)'}",
        f"  mode        {'catalog' if repo.hub else 'ad-hoc'}",
    ]
    if repo.hub:
        catalog = f"{len(load_catalog(repo))} recordings" if os.path.exists(repo.catalog) else "not created yet"
        lines.append(f"  catalog     {catalog}")
        lines.append(f"  index       {'built' if os.path.exists(repo.db) else 'not built, run `build`'}")
    print("\n".join(lines))
    if auth.returncode != 0:
        print(f"\nAuthenticate with `{os.path.basename(binary)} login`, or put an existing token in "
              f"PLAUD_TOKEN, which needs no file on disk and is how this runs in a container "
              f"or on someone else's machine.", file=sys.stderr)


def cmd_install(_repo, _args):
    print(install_cli())


def cmd_query(repo, args):
    repo.require_hub("query")
    if not os.path.exists(repo.db):
        sys.exit(f"no index at {repo.rel(repo.db)}. Run `build` first")
    con = sqlite3.connect(f"file:{repo.db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(args.sql).fetchall()
    except sqlite3.Error as e:
        sys.exit(f"query failed: {e}")
    finally:
        con.close()
    if args.json:
        print(json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))
    elif rows:
        if not args.no_header:
            print("\t".join(rows[0].keys()))
        for r in rows:
            print("\t".join("" if v is None else str(v) for v in r))


def _default_dir(repo):
    return repo.scratch or (repo.transcripts if repo.hub else None)


def _targets(repo, meta, to, summary_to):
    """Where the transcript and the summary should land."""
    rec = {"id": meta["id"], "filename": meta["filename"],
           "recorded_at": repo.local_time(meta["start_time"]) if meta.get("start_time") else None}
    slug = _slug(rec)
    to_is_file = bool(to) and to.endswith(".md")

    if to_is_file:
        transcript = os.path.join(repo.root, to) if not os.path.isabs(to) else to
    else:
        base = os.path.join(repo.root, to) if to else _default_dir(repo)
        if not base:
            base = tempfile.mkdtemp(prefix="plaud-")
        transcript = os.path.join(base, f"{slug}.md")

    if summary_to:
        summary = os.path.join(repo.root, summary_to) if not os.path.isabs(summary_to) else summary_to
    elif to_is_file:
        summary = None  # an explicit file names the transcript, and only the transcript
    else:
        summary = os.path.join(os.path.dirname(transcript), f"{slug}-summary.md")
    return transcript, summary


def cmd_fetch(repo, args):
    meta = _probe(args.id)
    if not meta["is_trans"]:
        if not args.generate:
            sys.exit(f"{args.id} has no transcript in Plaud yet.\n"
                     f"  Activate it: plaud generate {args.id} --wait   (consumes Plaud quota)\n"
                     f"  Or re-run this with --generate.")
        _generate(args.id)
        meta = _probe(args.id)
        if not meta["is_trans"]:
            sys.exit(f"{args.id} still has no transcript after generate; check `plaud info {args.id}`.")

    transcript, summary = _targets(repo, meta, args.to, args.summary_to)
    transcript = _download(args.id, "transcript", transcript)
    if not transcript:
        sys.exit(f"plaud produced no transcript file for {args.id}")
    if summary and meta["is_summary"]:
        summary = _download(args.id, "summary", summary)
    else:
        summary = None

    if repo.hub and os.path.exists(repo.catalog):
        catalog = load_catalog(repo)
        rec = catalog.get(args.id)
        if rec is not None:
            rec["is_trans"] = True
            rec["transcript_path"] = repo.rel(transcript)
            if summary:
                rec["summary_path"] = repo.rel(summary)
            if rec.get("status") in AUTO_STATUS:
                rec["status"] = "transcribed"
            save_catalog(repo, catalog)

    print(f"transcript: {repo.rel(transcript) if transcript.startswith(repo.root) else transcript}")
    if summary:
        print(f"summary:    {repo.rel(summary) if summary.startswith(repo.root) else summary}")
    if repo.filing:
        print(f"\nWhere this belongs in this repository: {repo.filing}")


def cmd_refresh(repo, _args):
    repo.require_hub("refresh")
    tag_map = {t["id"]: t["name"] for t in _plaud_json(["tag", "list"])}
    listing = _plaud_json(["list"])
    catalog = load_catalog(repo)

    seen, added, updated = set(), 0, 0
    for x in listing:
        rid = x["id"]
        seen.add(rid)
        base = {
            "id": rid,
            "filename": x.get("filename"),
            "start_time": x.get("start_time"),
            "recorded_at": repo.local_time(x["start_time"]) if x.get("start_time") else None,
            "duration_ms": x.get("duration"),
            "duration_min": round((x.get("duration") or 0) / 60000, 2),
            "scene": x.get("scene"),
            "url": f"https://web.plaud.ai/file/{rid}",
            "is_trans": bool(x.get("is_trans")),
            "is_summary": bool(x.get("is_summary")),
            "tags": [tag_map.get(t, t) for t in x.get("filetag_id_list", [])],
        }
        rec = catalog.get(rid)
        if rec is None:
            rec = dict(base, status=None, excluded_reason=None)
            for k in CURATION_FIELDS:
                rec.setdefault(k, None)
            added += 1
        else:
            rec.update(base)  # Plaud-side fields refresh; curation is untouched
            updated += 1

        if rec.get("status") in AUTO_STATUS:
            if repo.exclude_tags & set(rec["tags"]):
                rec["status"], rec["excluded_reason"] = "excluded", repo.exclude_reason
            else:
                rec["status"] = "transcribed" if rec["is_trans"] else "pending"
                rec["excluded_reason"] = None
        catalog[rid] = rec

    save_catalog(repo, catalog)
    gone = [rid for rid in catalog if rid not in seen]
    print(f"refresh: {added} added, {updated} updated, {len(catalog)} total"
          + (f", {len(gone)} in catalog but no longer in Plaud" if gone else ""))


def cmd_build(repo, _args):
    repo.require_hub("build")
    catalog = load_catalog(repo)
    if os.path.exists(repo.db):
        os.remove(repo.db)
    con = sqlite3.connect(repo.db)
    con.executescript(open(SCHEMA).read())
    placeholders = ",".join("?" for _ in DB_COLUMNS)
    for r in catalog.values():
        vals = []
        for c in DB_COLUMNS:
            v = r.get(c)
            if c == "tags":
                v = json.dumps(v or [], ensure_ascii=False)
            elif c in ("is_trans", "is_summary"):
                v = 1 if v else 0
            vals.append(v)
        con.execute(f"INSERT INTO recordings ({','.join(DB_COLUMNS)}) VALUES ({placeholders})", vals)
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM recordings").fetchone()[0]
    con.close()
    print(f"build: {n} recordings -> {repo.rel(repo.db)}")


def cmd_pull(repo, args):
    repo.require_hub("pull")
    catalog = load_catalog(repo)
    rec = catalog.get(args.id)
    if rec is None:
        sys.exit(f"unknown recording {args.id}. Run `refresh` first")
    if not rec.get("is_trans"):
        sys.exit(f"{args.id} has no transcript in Plaud yet (activate it: plaud generate {args.id} --wait)")

    slug = _slug(rec)
    transcript = _download(args.id, "transcript", os.path.join(repo.transcripts, f"{slug}.md"))
    rec["transcript_path"] = repo.rel(transcript) if transcript else None
    if rec.get("is_summary"):
        summary = _download(args.id, "summary", os.path.join(repo.summaries, f"{slug}.md"))
        rec["summary_path"] = repo.rel(summary) if summary else None
    if args.file:
        rec["path"] = args.file
        rec["status"] = "filed"
    elif rec.get("status") in AUTO_STATUS:
        rec["status"] = "transcribed"
    if args.project:
        rec["project"] = args.project
    catalog[args.id] = rec
    save_catalog(repo, catalog)

    print(f"pulled {args.id}: transcript -> {rec['transcript_path']}"
          + (f", summary -> {rec['summary_path']}" if rec.get("summary_path") else ""))
    print("run `plaud_hub.py build` to refresh the index")


def cmd_set(repo, args):
    repo.require_hub("set")
    catalog = load_catalog(repo)
    rec = catalog.get(args.id)
    if rec is None:
        sys.exit(f"unknown recording {args.id}. Run `refresh` first")
    for a in args.assignments:
        if "=" not in a:
            sys.exit(f"bad assignment '{a}', expected key=value")
        k, v = a.split("=", 1)
        rec[k] = v if v != "" else None
    catalog[args.id] = rec
    save_catalog(repo, catalog)
    print(f"set {args.id}: " + ", ".join(args.assignments))
    print("run `plaud_hub.py build` to refresh the index")


def cmd_status(repo, _args):
    repo.require_hub("status")
    catalog = load_catalog(repo)
    print(f"catalog: {len(catalog)} recordings")
    for st, n in Counter(r.get("status") for r in catalog.values()).most_common():
        print(f"  {st or '(unset)'}: {n}")


def cmd_gen_links(repo, _args):
    repo.require_hub("gen-links")
    catalog = load_catalog(repo)
    pending = sorted((r for r in catalog.values() if r.get("status") == "pending"),
                     key=lambda r: r.get("start_time") or 0, reverse=True)
    items = [{
        "id": r["id"],
        "date": (r.get("recorded_at") or "")[:16],
        "day": (r.get("recorded_at") or "")[:10],
        "min": r.get("duration_min"),
        "name": r.get("filename"),
        "url": r.get("url"),
        "short": (r.get("duration_ms") or 0) < 60000,
    } for r in pending]
    page = open(LINKS_TEMPLATE).read().replace("__PAYLOAD__", json.dumps(items, ensure_ascii=False))
    open(repo.links_page, "w").write(page)
    significant = sum(1 for i in items if not i["short"])
    print(f"gen-links: {len(items)} pending ({significant} >=1min) -> {repo.rel(repo.links_page)}")


# --------------------------------------------------------------------------- entry point

def main():
    parser = argparse.ArgumentParser(
        prog="plaud_hub.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("config", help="print the resolved configuration").set_defaults(fn=cmd_config)
    sub.add_parser("doctor", help="check the CLI, the auth and this repository's setup").set_defaults(fn=cmd_doctor)
    sub.add_parser("install", help="(re)install the pinned plaud CLI into the user's data dir").set_defaults(fn=cmd_install)

    p = sub.add_parser("fetch", help="download one transcript to a path (works without a catalog)")
    p.add_argument("id")
    p.add_argument("--to", help="destination: a .md file for the transcript, or a directory")
    p.add_argument("--summary-to", help="destination file for the summary, if you want it")
    p.add_argument("--generate", action="store_true",
                   help="transcribe first if Plaud has no transcript yet (consumes quota)")
    p.set_defaults(fn=cmd_fetch)

    sub.add_parser("refresh", help="merge `plaud list` into the catalog").set_defaults(fn=cmd_refresh)
    sub.add_parser("build", help="recompile the sqlite index").set_defaults(fn=cmd_build)
    sub.add_parser("status", help="counts by status").set_defaults(fn=cmd_status)
    sub.add_parser("gen-links", help="regenerate the pending-transcription page").set_defaults(fn=cmd_gen_links)

    p = sub.add_parser("pull", help="fetch into the hub's raw store and record it in the catalog")
    p.add_argument("id")
    p.add_argument("--project", help="curation: project label")
    p.add_argument("--file", help="curation: where it was filed, relative to the repository root")
    p.set_defaults(fn=cmd_pull)

    p = sub.add_parser("query", help="run a read-only SQL query against the index")
    p.add_argument("sql")
    p.add_argument("--json", action="store_true", help="objects instead of tab-separated rows")
    p.add_argument("--no-header", action="store_true", help="values only, for piping into another command")
    p.set_defaults(fn=cmd_query)

    p = sub.add_parser("set", help="edit curation fields of one recording")
    p.add_argument("id")
    p.add_argument("assignments", nargs="+", metavar="key=value")
    p.set_defaults(fn=cmd_set)

    args = parser.parse_args()
    args.fn(Repo(), args)


if __name__ == "__main__":
    main()
