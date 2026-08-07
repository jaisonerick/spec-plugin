---
name: plaud
description: Work with Plaud.ai voice recordings: find a recording, activate its transcription, bring the transcript into the current repository, and optionally keep a catalog of what came in. Where the transcript then gets filed is read from the repository's own configuration, never assumed. Triggers "plaud", "gravação", "recording", "transcrição", "transcript", "processa essa call", "essa reunião foi gravada".
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
---

Plaud.ai records meetings and calls; this skill is how that audio becomes text inside a repository.

It stops at the transcript. Turning it into a note, filing it, naming the file, choosing the language: that is the repository's business, and this skill reads it from the repository rather than assuming it. Do not invent a destination.

**Python 3 is the only thing that has to be there.** The Plaud client is a single Go binary, and if one is not already on PATH the engine installs the pinned release into the user's data directory on first use: no sudo, no PATH changes, nothing written inside the plugin. That needs network on the first run, and an authenticated account (see *Setup*).

```bash
HUB="${CLAUDE_PLUGIN_ROOT}/skills/plaud/plaud_hub.py"
```

## Start by checking the ground

```bash
python3 "$HUB" doctor
```

One report covering the CLI, whether it can activate transcription, whether the account is authenticated, and how this repository is configured. When something is missing this is what says which one, so run it before concluding that a recording is the problem.

```bash
python3 "$HUB" config
```

Prints the resolved configuration alone, and which of the two modes applies:

- **ad-hoc**: no catalog. Recordings are fetched one at a time, on demand, and nothing about them is stored. This is the right mode for a repository that only wants the occasional transcript.
- **catalog**: the repository keeps an index of every recording it knows about: what it is, whether it has been transcribed, where it was filed. Worth it when the set of recordings is itself something to keep track of.

`filing` in the output is the document that says where a transcript belongs in this repository. **Read it before writing anything.** If it is absent, the repository has not declared a convention: look at its `CLAUDE.md`/`AGENTS.md`, and if that settles nothing, ask.

## Finding the recording

Recordings live in Plaud's cloud, named by date and topic. Narrow before listing everything:

```bash
plaud list --since 2026-08-01 --limit 20        # recent
plaud list --search "orçamento" --json          # by name
plaud search "texto dito na reunião"            # inside the transcripts already made
plaud info <id>                                 # one recording: duration, what content exists
```

When several could be the one, show the candidates with date and duration and let the user pick, rather than guessing from the title.

## Bringing one transcript in

```bash
python3 "$HUB" fetch <id> --to comms/2026-08-06-reuniao-x/transcript.md
python3 "$HUB" fetch <id>                       # into the configured directory, slug-named
python3 "$HUB" fetch <id> --generate            # transcribe first if there is no transcript yet
```

`--to` ending in `.md` is the transcript's file; anything else is a directory, and the summary lands beside it (`--summary-to` puts it somewhere specific).

**Transcription is not automatic and it consumes the account's quota.** A recording with no transcript makes `fetch` stop and say so; `--generate` transcribes and waits, and only pass it when the user asked for that recording specifically. Language auto-detects, speakers are separated by default, and a summary is always produced along with the transcript because Plaud's remote trigger has no transcript-only mode.

Then read the file. A long transcript is raw speech: expect false starts, crosstalk and names spelled by ear, and treat what people said as claims rather than facts.

## Handing off

Follow the `filing` document. If the repository has its own skill for meeting notes or for filing documents, use it, since that skill owns the destination, the naming and the structure, and this one has already done its part by putting readable text on disk.

Say where the transcript landed and where the note went, so the next reader can follow the thread back to the source.

## Catalog mode

Only when `config` reports a hub. The catalog is `catalog.jsonl` (source of truth, git-tracked, one JSON object per recording), a git-ignored sqlite index rebuilt from it, and the raw transcripts pulled so far.

```bash
python3 "$HUB" refresh     # merge `plaud list` + tags into the catalog; curation is preserved
python3 "$HUB" build       # recompile the sqlite index from the catalog
python3 "$HUB" status      # counts by status
python3 "$HUB" pull <id>   # fetch into the raw store and record the paths
python3 "$HUB" set <id> project=<label> path=<repo-relative> status=filed
python3 "$HUB" gen-links   # regenerate the page listing what still needs transcription
```

`status` is the manifest, so check it before processing a recording twice: `pending` (no transcript yet), `transcribed` (has one, not filed), `filed` (mapped to a destination through `path` and/or `repo`), `excluded` (out of scope for this repository). The first two are recomputed on every refresh; the last two are sticky, and a refresh never touches them or any other curation field.

Ad-hoc queries go through `query`, which is read-only and needs no `sqlite3` binary. The index has a `pending_transcription` and an `unfiled` view:

```bash
python3 "$HUB" query "SELECT id, recorded_at, duration_min, filename FROM unfiled"
python3 "$HUB" query "SELECT * FROM recordings WHERE project = 'acme'" --json
```

Activating transcription in bulk is the one place worth being careful, because every recording costs quota. Filter to what is worth transcribing, and confirm the batch with the user first:

```bash
plaud generate $(python3 "$HUB" query "SELECT id FROM pending_transcription WHERE duration_min >= 5" --no-header)
```

After activating, `refresh && build` flips those recordings from `pending` to `transcribed`.

Commit `catalog.jsonl` and whatever was pulled; the sqlite index is rebuildable and stays out of git.

## `.plaud.json`

At the repository root. Every key is optional; the file itself is optional, and without it the skill runs ad-hoc and has nothing to tell you about filing.

```json
{
  "filing": "docs/meeting-notes.md",
  "scratch": "workspace/plaud",
  "hub": "studio/plaud",
  "exclude_tags": ["Client A"],
  "exclude_reason": "handled-in-the-client-repo",
  "utc_offset": -3
}
```

| Key | Effect |
| :-- | :-- |
| `filing` | Path to the document that says where a transcript belongs here. The one key worth setting even in the simplest repository. |
| `scratch` | Default directory for `fetch` when `--to` is omitted. Point it at a git-ignored directory when transcripts should not be committed as they are. |
| `hub` | Turns on catalog mode and names the directory holding it. Absent means ad-hoc. |
| `exclude_tags` | Plaud tags whose recordings are out of scope: they stay indexed but are marked `excluded` on refresh. Catalog mode only. |
| `exclude_reason` | What to record as the reason for those. |
| `utc_offset` | Timezone for recording timestamps, in hours from UTC. Defaults to the machine's timezone. |

## Setup

**The binary takes care of itself.** `doctor` (or the first command that needs it) installs the pinned release of [`jaisonerick/plaud-cli`](https://github.com/jaisonerick/plaud-cli) under `~/.local/share/plaud-cli/bin`, matched to the platform and checked against the release's sha256. A `plaud` already on PATH always wins, so an existing install is never disturbed. If that one is too old to have `generate`, the error says so rather than failing obscurely.

**Authentication is the part a fresh environment still needs**, and there are only two ways in:

- `plaud login` sends a one-time code to the account's email and writes the token to `~/.config/plaud/token.json`. It needs a terminal and the mailbox, so it is how a person sets up their own machine, once.
- `PLAUD_TOKEN` in the environment carries a token someone already obtained that way. Nothing is written to disk, which is what makes a container, a CI job or a borrowed machine work at all: no mailbox there means no login there.

The token is a JWT valid for months, and **nothing in this stack refreshes it**. When it expires the only cure is another login, so `doctor` prints the expiry date instead of letting a task discover it halfway through. If a command reports an expired session, stop and get a valid token rather than working around it.

Accounts are per person and each one sees only its own recordings. A teammate's call is not missing, it is simply not in the account this environment is authenticated as.

| Variable | Effect |
| :-- | :-- |
| `PLAUD_TOKEN` | Access token, no config file needed |
| `PLAUD_BIN` | Use this binary instead of resolving one |
| `PLAUD_CLI_VERSION` | Install a different release (`latest`, or a tag) |
| `ANTHROPIC_API_KEY` | Needed only by `plaud summarize` and `plaud ask` |

## CLI reference

```bash
plaud list [--tag NAME] [--since YYYY-MM-DD] [--before YYYY-MM-DD] [--has-transcript]
           [--has-summary] [--search STR] [--limit N] [--json]
plaud info <id> [--json]

plaud generate <id>... [--lang auto|pt|en] [--speaker=false] [--summary-template ID]
                       [--reload] [--wait] [--timeout D] [--poll-interval D]
plaud download <id> [--audio] [--transcript] [--summary] [--all]
                    [--format json|txt|srt|md] [--output-dir DIR]

plaud search "text" [--limit N] [--no-cache]     # over transcripts, cached locally
plaud summarize <id> [--template meeting|detailed] [--prompt "..."] [--output FILE]
plaud ask <id> "question"                        # streams the answer

plaud tag list | tag create "Name" | tag delete "Name"
plaud me
```

`--debug`, `--json` and `--help` work on every command. `plaud sync` bulk-downloads everything to a local folder; prefer `fetch` or `pull`, which put the file where the repository wants it.

## Rules

- **Never delete a recording from Plaud.** This skill reads, transcribes and organizes, and nothing here removes anything from the account.
- **Transcription costs quota**, so activating it is a decision, not a step. One recording on request, a batch only after the user confirms the batch.
- **Keep the transcript in the language it was spoken.** Translating a meeting loses what made it worth keeping; a summary follows the destination's language if that differs.
- **The transcript is the source, the note is what people read.** Keep the transcript reachable from the note rather than replacing it.
