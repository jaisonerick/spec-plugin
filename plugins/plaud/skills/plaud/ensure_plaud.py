#!/usr/bin/env python3
"""Put a current plaud CLI on this machine, and say where it is.

The CLI does the work: it talks to Plaud, transcribes, recognises voices, and
reads what each repository declares about where a transcript belongs. None of
that is here. What is here is the one thing the CLI cannot do for itself —
arrive on a machine that does not have it, somewhere the shell will find it.

Run it with no arguments: it prints the path to a binary at least as new as the
version pinned below, installing one if it has to, and does nothing else.

  PLAUD_BIN          use this binary as given, and install nothing
  PLAUD_CLI_VERSION  install a different release (`latest`, or a tag)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.request


# Windows hands a console whose code page is not UTF-8, and the first accented
# name written to it ends the run on a UnicodeEncodeError.
def _speak_utf8():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


# The CLI this skill is written against. Pinned rather than tracking the latest
# release, so the commands and flags the skill documents are the ones that run.
CLI_REPO = "jaisonerick/plaud-cli"
CLI_VERSION = "0.23.0"


_BIN = None


def plaud_bin(install=True):
    """Path to a plaud CLI new enough for this skill, installing one if needed.

    A binary that merely exists is not enough: this skill and the CLI move
    together, and a copy from before a flag existed fails in the middle of a
    recording rather than at the start. So whatever is found is checked against
    the version pinned here, and anything older is replaced by the managed copy.

    PLAUD_BIN is the exception and is used as given: naming a binary is a
    decision, and second-guessing it would defeat the point of saying so.
    Nothing here writes to the plugin's own directory, which is wiped on update.
    """
    global _BIN
    if _BIN:
        return _BIN

    override = os.environ.get("PLAUD_BIN")
    if override:
        _BIN = override
        return _BIN

    wanted = _as_version(_resolve_version())
    on_path = shutil.which("plaud")
    managed = os.path.join(_managed_dir(), _bin_name())

    # The copy on PATH is the one that runs, for this skill and for whoever
    # types `plaud`, so it is the one kept current. Installing beside it leaves
    # two, and the older one goes on being the one that answers.
    if on_path and os.path.exists(on_path):
        _sweep_old(on_path)
        if _version_of(on_path) < wanted:
            if not install:
                sys.exit(f"{on_path} is older than this skill needs. Run `ensure_plaud --install`")
            try:
                install_cli(on_path)
            except PermissionError:
                print(f"cannot write {on_path}, so the copy this skill manages is used instead. "
                      "Two plaud binaries now differ; delete that one or make it writable.",
                      file=sys.stderr)
                _BIN = _managed_copy(wanted, install)
                return _BIN
        _drop_managed_copy(managed, on_path)
        _BIN = on_path
        return _BIN

    _BIN = _managed_copy(wanted, install)
    return _BIN


def _managed_copy(wanted, install):
    """The copy this skill keeps, for a machine with no plaud of its own.

    It goes somewhere the shell looks, so the person whose machine it is can
    type the name too.
    """
    managed = os.path.join(_managed_dir(), _bin_name())
    _sweep_old(managed)
    legacy = os.path.join(_legacy_dir(), _bin_name())
    if os.path.exists(legacy) and not os.path.exists(managed):
        os.makedirs(_managed_dir(), exist_ok=True)
        os.replace(legacy, managed)
    if os.path.exists(managed) and _version_of(managed) >= wanted:
        return managed
    if not install:
        sys.exit("the plaud CLI is missing or too old. Run `ensure_plaud --install`")
    return install_cli()


def _drop_managed_copy(managed, in_use):
    """Two binaries that differ is how an old one goes on being the one that
    runs, so the ones nobody reaches for go once the other is current."""
    for spare in (managed, os.path.join(_legacy_dir(), _bin_name())):
        if spare == in_use or not os.path.exists(spare):
            continue
        try:
            os.remove(spare)
            print(f"removed {spare}, now that {in_use} is the one kept up to date.", file=sys.stderr)
        except OSError:
            pass


def _old_path(target):
    return target + ".old"


def _sweep_old(target):
    """Drop what an update moved aside, on the first run where nothing holds it."""
    try:
        os.remove(_old_path(target))
    except OSError:
        pass


def _as_version(text):
    found = re.search(r"(\d+)\.(\d+)\.(\d+)", text or "")
    return tuple(int(part) for part in found.groups()) if found else (0, 0, 0)


def _version_of(path):
    """The version a binary reports, or nothing when it will not say."""
    try:
        out = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=15)
    except Exception:
        return (0, 0, 0)
    return _as_version(out.stdout)


def _managed_dir():
    """Where a binary of our own goes: somewhere typing `plaud` finds it.

    A directory only this skill knows about is how a machine ends up with a
    plaud that answers the skill and nothing that answers the person.
    """
    if platform.system() == "Windows":
        base = os.environ.get("LOCALAPPDATA") or os.path.join(
            os.path.expanduser("~"), "AppData", "Local")
        return os.path.join(base, "plaud")
    return os.path.join(os.path.expanduser("~"), ".local", "bin")


def _legacy_dir():
    """Where this skill used to put it, out of reach of the shell."""
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "plaud-cli", "bin")


def _on_path(directory):
    here = os.path.normcase(os.path.normpath(directory))
    return any(
        os.path.normcase(os.path.normpath(entry)) == here
        for entry in os.environ.get("PATH", "").split(os.pathsep)
        if entry
    )


def _put_on_path(directory):
    """Make the shell find what was just installed.

    Windows keeps a PATH of the user's own, which is a setting and safe to
    write. Everywhere else PATH is built by files somebody else manages — a
    dotfile repository, a profile under version control — so this says what to
    add rather than editing them.
    """
    if _on_path(directory):
        return

    if platform.system() != "Windows":
        print(f"add {directory} to your PATH to type `plaud` yourself:\n"
              f'  export PATH="{directory}:$PATH"', file=sys.stderr)
        return

    script = (
        "$d = [Environment]::GetEnvironmentVariable('Path','User'); "
        f"if ($d -notlike '*{directory}*') {{ "
        f"[Environment]::SetEnvironmentVariable('Path', ($d.TrimEnd(';') + ';{directory}'), 'User') }}"
    )
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", script], check=True,
                       capture_output=True, timeout=30)
        print(f"added {directory} to your PATH; a new terminal will find `plaud`.", file=sys.stderr)
    except Exception:
        print(f"add {directory} to your PATH to type `plaud` yourself.", file=sys.stderr)


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


def install_cli(target=None):
    """Download the pinned release over `target`, or into the user's data dir.

    No sudo and no PATH changes: what is replaced is a file that is already
    where it is used."""
    version = _resolve_version()
    asset = _asset_name()
    base = f"https://github.com/{CLI_REPO}/releases/download/v{version}"
    target = target or os.path.join(_managed_dir(), _bin_name())
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

    os.makedirs(os.path.dirname(target), exist_ok=True)
    tmp = target + ".part"
    with open(tmp, "wb") as f:
        f.write(payload)
    os.chmod(tmp, 0o755)
    _put_in_place(tmp, target)
    _unblock(target)
    _put_on_path(os.path.dirname(target))
    return target


def _put_in_place(tmp, target):
    """Windows will not write over a binary that is running, but it will rename
    one: the name is freed for the new file and what was moved aside goes on the
    next run, the first moment nothing holds it."""
    try:
        os.replace(tmp, target)
        return
    except PermissionError:
        if not os.path.exists(target):
            raise

    aside = _old_path(target)
    _sweep_old(target)
    os.replace(target, aside)
    try:
        os.replace(tmp, target)
    except OSError:
        os.replace(aside, target)  # better the old binary back than none
        raise


def _unblock(path):
    """Clear the tag Windows puts on a downloaded file.

    SmartScreen refuses a tagged binary that carries no signature, and this one
    carries none. Writing the file from here should never set the tag — that is
    a browser's doing — but a copy fetched by hand does, and it ends up in the
    same place under the same name.
    """
    if platform.system() != "Windows":
        return
    try:
        os.remove(path + ":Zone.Identifier")
    except OSError:
        # Absent is the normal case, and a filesystem with no alternate data
        # streams cannot carry the tag in the first place.
        pass


def main():
    _speak_utf8()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--install", action="store_true",
                        help="install the pinned release even if a current one is here")
    args = parser.parse_args()

    print(install_cli() if args.install else plaud_bin())


if __name__ == "__main__":
    main()
