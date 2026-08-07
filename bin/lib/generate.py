#!/usr/bin/env python3
"""Emit every agent's manifests from the standard ones.

The source is the Agent Plugins Specification 1.0.0 manifest each plugin already
carries at `plugins/<name>/plugin.json`, plus `catalog.json`, which only says
which plugins exist and where they come from. Distribution has no standard yet,
so that thin catalog is the one place we still speak for ourselves.

    https://agent-plugins.org/schemas/1.0.0/plugin.schema.json
    https://agentskills.io/specification   (SKILL.md, already conformant)

Anything an agent needs beyond the standard rides in `extensions`, under our
namespace, which is exactly what that field is for. Each agent's own manifest is
output, so a format change lands here and nowhere else.

Written per run:

    .claude-plugin/marketplace.json              Claude catalog
    .agents/plugins/marketplace.json             Codex catalog
    plugins/<name>/.claude-plugin/plugin.json    Claude manifest
    plugins/<name>/.codex-plugin/plugin.json     Codex manifest
    index.json                                   runtime listing for the marketplace plugin

Antigravity reads `plugins/<name>/plugin.json` directly, so the standard
manifest serves as its manifest too and nothing is generated for it.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "catalog.json"
NAMESPACE = "com.nexaedge.marketplace"
SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"

WRITTEN: list[str] = []


def write_json(path: Path, data: dict) -> None:
    """Write only when the content changed, so reruns are quiet and CI diffs stay honest."""
    body = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text() == body:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    WRITTEN.append(str(path.relative_to(ROOT)))


def to_semver(version: str) -> str:
    """We version plugins as v1, v2, v3. Codex validates strict semver."""
    if re.fullmatch(r"\d+\.\d+\.\d+", version):
        return version
    match = re.fullmatch(r"v?(\d+)", version)
    if not match:
        raise SystemExit(f"cannot turn version {version!r} into semver")
    return f"{match.group(1)}.0.0"


def load() -> tuple[dict, list[dict]]:
    """Return the marketplace block and one merged record per plugin.

    A local plugin's record comes from its standard manifest; an external one
    from the catalog, since we cannot put a manifest in someone else's repo.
    """
    catalog = json.loads(CATALOG.read_text())
    records = []

    for entry in catalog["plugins"]:
        record = {"name": entry["name"], "source": entry["source"]}

        if entry["source"]["kind"] == "local":
            manifest = json.loads((ROOT / "plugins" / entry["name"] / "plugin.json").read_text())
            record["manifest"] = manifest
            record["listing"] = manifest.get("extensions", {}).get(NAMESPACE, {})
        else:
            record["manifest"] = None
            record["listing"] = entry.get("listing", {})

        records.append(record)

    return catalog["marketplace"], records


# ── Claude Code ───────────────────────────────────────────────────────────────

def claude_source(record: dict) -> str | dict:
    source = record["source"]
    kind = source["kind"]
    ref = {"ref": source["ref"]} if "ref" in source else {}
    if kind == "local":
        return f"./plugins/{record['name']}"
    if kind == "git":
        return {"source": "url", "url": source["url"], **ref}
    if kind == "git-subdir":
        return {"source": "git-subdir", "url": source["url"], "path": source["path"], **ref}
    raise SystemExit(f"unknown source kind {kind!r} for {record['name']}")


def emit_claude(market: dict, records: list[dict]) -> None:
    owner = market["owner"]

    write_json(ROOT / ".claude-plugin" / "marketplace.json", {
        "name": market["name"],
        "metadata": {"description": market["description"], "version": market["version"]},
        # Claude reads only name and email here.
        "owner": {"name": owner["name"], "email": owner["email"]},
        # Entries carry name and source only: the plugin manifest owns the version.
        "plugins": [{"name": r["name"], "source": claude_source(r)} for r in records],
    })

    for record in records:
        manifest = record["manifest"]
        if manifest is None:
            continue
        author = manifest["author"]
        write_json(ROOT / "plugins" / record["name"] / ".claude-plugin" / "plugin.json", {
            "name": manifest["name"],
            "description": manifest["description"],
            "version": manifest["version"],
            "author": {"name": author["name"], "url": author["url"]},
        })


# ── Codex ─────────────────────────────────────────────────────────────────────

def emit_codex(market: dict, records: list[dict]) -> None:
    entries = []

    for record in records:
        manifest, listing = record["manifest"], record["listing"]
        # Codex installs only what carries a Codex manifest, and we do not write
        # manifests into other people's repositories.
        if manifest is None or "codex" not in listing.get("platforms", []):
            continue

        name = manifest["name"]
        author = manifest["author"]
        codex = {
            "name": name,
            "version": to_semver(manifest["version"]),
            "description": manifest["description"],
            "author": author,
            "skills": "./skills/",
            "interface": {
                "displayName": listing["displayName"],
                "shortDescription": listing["tagline"],
                "longDescription": manifest["description"],
                "developerName": author["name"],
                "category": listing["category"],
                "capabilities": listing.get("capabilities", ["Interactive", "Write"]),
                # Codex keeps the first three and truncates each at 128 characters.
                "defaultPrompt": listing["prompts"][:3],
            },
        }
        for optional in ("homepage", "repository", "license", "keywords"):
            if optional in manifest:
                codex[optional] = manifest[optional]
        # Codex rejects a `hooks` field today, and only accepts `mcpServers` when
        # the companion file is really there.
        if (ROOT / "plugins" / name / ".mcp.json").exists():
            codex["mcpServers"] = "./.mcp.json"

        write_json(ROOT / "plugins" / name / ".codex-plugin" / "plugin.json", codex)
        entries.append({
            "name": name,
            "source": {"source": "local", "path": f"./plugins/{name}"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_USE"},
            "category": listing["category"],
        })

    write_json(ROOT / ".agents" / "plugins" / "marketplace.json", {
        "name": market["name"],
        "interface": {"displayName": market["displayName"]},
        "plugins": entries,
    })


# ── Runtime index ─────────────────────────────────────────────────────────────

def emit_index(market: dict, records: list[dict]) -> None:
    """The marketplace plugin fetches one file to answer "what can I install?".

    It cannot read eight manifests over the network, and an installed plugin is a
    copy frozen at install time, so the listing has to be fetchable and current.
    """
    write_json(ROOT / "index.json", {
        "marketplace": {"name": market["name"], "displayName": market["displayName"]},
        "plugins": [
            {
                "name": r["name"],
                "tagline": r["listing"].get("tagline", ""),
                "description": r["manifest"]["description"] if r["manifest"] else r["listing"].get("tagline", ""),
                "platforms": r["listing"].get("platforms", []),
                "keywords": (r["manifest"] or r["listing"]).get("keywords", []),
                **({"requires": r["listing"]["requires"]} if "requires" in r["listing"] else {}),
            }
            for r in records
        ],
    })


# ── Consistency ───────────────────────────────────────────────────────────────

def check(records: list[dict]) -> list[str]:
    """Catch the drift the agents would only report at install time."""
    problems = []
    names = [r["name"] for r in records]

    for duplicate in sorted({n for n in names if names.count(n) > 1}):
        problems.append(f"{duplicate}: listed more than once in catalog.json")

    for record in records:
        name, manifest, listing = record["name"], record["manifest"], record["listing"]

        if record["source"]["kind"] == "local" and not (ROOT / "plugins" / name).is_dir():
            problems.append(f"{name}: source is local but plugins/{name}/ does not exist")

        if manifest is not None:
            if manifest.get("$schema") != SCHEMA:
                problems.append(f"{name}: plugin.json must declare $schema {SCHEMA}")
            if manifest.get("name") != name:
                problems.append(f"{name}: plugin.json name is {manifest.get('name')!r}")
            if "version" not in manifest:
                problems.append(f"{name}: local plugins need a version")

        for required in ("displayName", "tagline", "category", "platforms"):
            if required not in listing:
                problems.append(f"{name}: listing is missing {required}")

        if "codex" in listing.get("platforms", []) and manifest is not None and not listing.get("prompts"):
            problems.append(f"{name}: Codex requires at least one entry in prompts")

    for directory in sorted((ROOT / "plugins").iterdir()):
        if directory.is_dir() and directory.name not in names:
            problems.append(f"{directory.name}: directory exists but is missing from catalog.json")

    return problems


def main() -> int:
    market, records = load()

    problems = check(records)
    if problems:
        print("the marketplace is inconsistent:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    emit_claude(market, records)
    emit_codex(market, records)
    emit_index(market, records)

    if WRITTEN:
        print(f"→ Wrote {len(WRITTEN)} file(s):")
        for path in WRITTEN:
            print(f"    {path}")
    else:
        print("→ Everything already up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
