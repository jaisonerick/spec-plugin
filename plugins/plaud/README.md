# plaud

Plaud.ai records the meeting; this plugin is how that audio becomes text inside a repository.

It stops at the transcript. Turning it into a note, naming the file, choosing where it goes: that is the repository's business, declared in `.plaud.json` at its root. The same skill then serves a knowledge base that indexes every recording it has ever seen and a client project that only wants the occasional call, without knowing anything about either.

## Install

```
/plugin marketplace add nexaedge/nexaedge-marketplace
/plugin install plaud@nexaedge-marketplace
```

Python 3 is the only thing that has to be installed. The Plaud client is a single Go binary, and if one is not already on PATH the plugin fetches the pinned release of [`plaud-cli`](https://github.com/jaisonerick/plaud-cli) into `~/.local/share/plaud-cli/bin` on first use, matched to the platform and verified against the release's sha256. No sudo, no PATH changes, and nothing written inside the plugin directory, which is replaced on every update.

What a fresh environment still needs is an authenticated account:

| Variable | Effect |
| :-- | :-- |
| `PLAUD_TOKEN` | Access token, standing in for `~/.config/plaud/token.json` entirely. This is what makes the plugin work in a container, a CI job or on someone else's machine. |
| `PLAUD_BIN` | Use this binary instead of resolving one. |
| `PLAUD_CLI_VERSION` | Install a different release: `latest`, or an explicit tag. |

Without `PLAUD_TOKEN`, `plaud login` walks through a one-time code by email and writes the token to disk. `python3 <engine> doctor` reports which of these is missing.

## Configure the repository

`.plaud.json` at the repository root. Every key is optional, and so is the file.

```json
{
  "filing": "docs/meeting-notes.md",
  "scratch": "workspace/plaud"
}
```

`filing` points at the document that says where a transcript belongs here. It is the one key worth setting even in the simplest repository, because it is what stops the agent from inventing a destination. `scratch` is where a fetched transcript lands by default; point it at a git-ignored directory when transcripts should not be committed as they arrive.

Adding `hub` turns on catalog mode:

```json
{
  "hub": "studio/plaud",
  "filing": "studio/plaud/plaud.md",
  "exclude_tags": ["Client A"],
  "exclude_reason": "handled-in-the-client-repo"
}
```

The hub directory then holds `catalog.jsonl` (source of truth, git-tracked, one JSON object per recording), a git-ignored sqlite index rebuilt from it, and the transcripts pulled so far. Each recording carries a `status` (`pending`, `transcribed`, `filed` or `excluded`), which is what keeps the same call from being processed twice. Curation survives every refresh; only the Plaud-side fields are overwritten.

`utc_offset` (hours from UTC) fixes the timezone of recording timestamps when the machine's own is not the right one.

## Use

Ask Claude to process a recording. Claude resolves the engine through `${CLAUDE_PLUGIN_ROOT}`; to drive it by hand, the installed copy sits under `~/.claude/plugins/cache/<marketplace>/plaud/<version>/skills/plaud/plaud_hub.py`, where `<version>` moves on every update.

```bash
python3 "$HUB" doctor                                            # CLI, auth, repository setup
python3 "$HUB" config                                            # resolved setup and mode
python3 "$HUB" fetch <id> --to comms/2026-08-06-call/transcript.md
python3 "$HUB" fetch <id> --generate                             # transcribe first, then fetch

python3 "$HUB" refresh && python3 "$HUB" build                   # catalog mode
python3 "$HUB" pull <id> --project acme --file comms/2026-08-06-call/
python3 "$HUB" query "SELECT id, filename FROM unfiled"          # no sqlite3 binary needed
python3 "$HUB" status
```

Transcription is not automatic and consumes the Plaud account's quota, so `fetch` refuses a recording that has none until `--generate` says otherwise. Nothing here deletes anything from the account.
