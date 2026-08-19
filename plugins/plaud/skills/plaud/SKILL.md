---
name: plaud
description: >-
  Work with Plaud.ai voice recordings: find a recording, activate its transcription, bring the transcript into the current repository, and optionally keep a catalog of what came in. Where the transcript then gets filed is read from the repository's own configuration, never assumed. Triggers "plaud", "gravação", "recording", "transcrição", "transcript", "processa essa call", "essa reunião foi gravada".
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

**Python 3 is the only thing that has to be there.** The Plaud client is a single Go binary, and if one is not already on PATH the engine installs the pinned release into the user's data directory on first use: no sudo, no PATH changes, nothing written inside the plugin. That needs network on the first run, and an account that is signed in.

**There are two sign-ins, and they answer different questions** (see *Signing the user in*). The Plaud account says which recordings can be read; a Google account says whether anything can be transcribed, because transcription runs on a service shared between the domains it serves. Being signed in to one and not the other is the confusing half-state `doctor` names explicitly.

**Signing in is your job, not the user's.** Assume the person you are working for will never run a command: walk them through it in the conversation, asking for an emailed code and never for a password.

```bash
HUB="${CLAUDE_PLUGIN_ROOT}/skills/plaud/plaud_hub.py"
```

## Start by checking the ground

```bash
python3 "$HUB" doctor
```

One report covering the CLI, both sign-ins, and how this repository is configured. When something is missing this is what says which one, so run it before concluding that a recording is the problem. `NOT AUTHENTICATED` on the Plaud line and `NOT SIGNED IN` on the service line both send you to *Signing the user in*, and neither is a blocker to hand back.

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
```

`--to` ending in `.md` is the transcript's file; anything else is a directory, and the summary lands beside it (`--summary-to` puts it somewhere specific).

**A recording without a transcript is transcribed on the way.** Plaud itself no longer makes transcripts for these accounts, so `fetch` sends the audio to the Whisper service and brings the text back. That takes minutes rather than seconds, and it wakes a GPU that somebody pays for — so it is worth doing on a recording somebody asked for, and worth thinking about before doing it to a hundred.

Language auto-detects, speakers are separated, and the ones the service recognises come back named: a line reads `**Jaison Erick (NexaEdge)** (00:00:09):` rather than `SPEAKER_01`. A summary comes along only when Plaud already has one.

Then read the file. A long transcript is raw speech: expect false starts, crosstalk and names spelled by ear, and treat what people said as claims rather than facts.

## Who is speaking

Transcripts come back with the voices the service recognises already named, as `First Last (Company)`. A voice it has never heard stays `SPEAKER_01`, and naming it is what teaches it:

```bash
plaud speaker list                       # everyone it knows
plaud speaker name <recording-id> SPEAKER_01 "Jaison Erick" --company NexaEdge
```

The recording id is the one `plaud list` shows; nothing about the voices is kept on this machine, so naming one needs no file and no audio.

People are shared by everyone using the service, which is why a first name alone is refused: "Amanda" names whichever Amanda the person typing meant. A surname nobody knows is a different thing and takes `--surname-unknown`, after which the company does the identifying.

**Ask, do not infer.** Working out from context that SPEAKER_01 is probably the person whose meeting it was is exactly the guess that puts a wrong name on a voice for every other user. If nobody in the conversation knows, leave it.

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

Transcribing in bulk is the one place worth being careful, because each recording is a download and a GPU pass. Filter to what is worth transcribing, and confirm the batch with the user first:

```bash
for id in $(python3 "$HUB" query "SELECT id FROM pending_transcription WHERE duration_min >= 5" --no-header); do
  python3 "$HUB" pull "$id"
done
```

`pending` here means Plaud holds no transcript, which is now the normal state rather than a problem: pulling one transcribes it.

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

**The binary takes care of itself.** `doctor` (or the first command that needs it) installs the pinned release of [`jaisonerick/plaud-cli`](https://github.com/jaisonerick/plaud-cli) under `~/.local/share/plaud-cli/bin`, matched to the platform and checked against the release's sha256. A `plaud` already on PATH always wins, so an existing install is never disturbed. If that one is too old to reach the transcription service, `doctor` says so rather than failing obscurely halfway through a recording.

## Signing the user in

Two accounts, and `doctor` reports them on separate lines because being signed in to one and not the other fails in the middle of a task rather than at the start.

### The Plaud account — which recordings can be read

When `doctor` reports `NOT AUTHENTICATED`, **conduct the login yourself, in the conversation.** The person you are working for is not going to open a terminal, and they do not need to: two questions and two commands is the whole procedure.

**Never ask for their password.** A password opens the account forever and lands in the transcript; a login code expires in minutes and works once. Ask for the code.

1. Ask for the email on the Plaud account, and send the code:

   ```bash
   plaud login --send-code --email <email> --json
   ```

   That prints an `otp_token`, which is a handle for the pending login, not a credential to keep. Nothing is stored yet.

2. Ask the user for the code that just arrived in their inbox (six digits, from Plaud), and finish:

   ```bash
   plaud login --email <email> --otp-token <otp_token> --code <code>
   ```

   `Token saved. You're logged in.` means done. Confirm with `doctor` and carry on with what they originally asked for.

If it comes back `Code expired or invalid`, the code aged out or was mistyped: go back to step 1 and send a fresh one. The handle from the first call belongs to that code, so a new code needs a new handle.

Nothing in this needs a browser, an open port, or a terminal the user can see, so it works the same in a terminal, a desktop app, a phone or a sandbox. Do not try to open a browser.

Two other ways in exist, and neither replaces the above as the default:

- **`PLAUD_TOKEN`** in the environment, when the user already has a token. Nothing is written to disk, which suits an ephemeral container.
- **`plaud login --password`**, only when the user volunteers a password or a machine is being provisioned unattended (`--password-stdin`, `PLAUD_PASSWORD`). Accounts created through Google, Apple or Microsoft have no password at all until one is set in the Plaud app, so the code flow is the one that always works.

The token is a JWT valid for months, and **nothing in this stack refreshes it**. `doctor` prints the expiry date so a task does not discover it halfway through; when it does expire, the cure is another login, exactly as above.

Accounts are per person and each one sees only its own recordings. A teammate's call is not missing, it is simply not in the account this environment is authenticated as.

### The transcription service — whether anything can be transcribed

Transcription runs on a service shared by everyone at the domains it serves, and a Google account is what gets in. Nothing from the cloud it runs on is needed: no account there, no keys.

```bash
plaud auth status      # who is signed in, and whether it still works
plaud auth logout      # forget it
```

**Conduct this login too, in the conversation.** It asks nothing of the machine — no browser, no port, no visible terminal — so it works the same over ssh, in a container, or on a phone.

Start it in the background and read the first line it prints:

```bash
plaud auth login --json > /tmp/plaud-login.json 2>&1 &
```

The first line arrives immediately and carries `user_code` and `verification_url`. **Show both to the user and ask them to enter the code**, then watch the same file: the command is still running, and writes a second line when the sign-in lands.

```json
{"status":"pending","user_code":"QPB-QYM-SFSJ","verification_url":"https://www.google.com/device","expires_in":1800}
{"status":"signed-in","email":"someone@nexaedge.com","served":true}
```

`signed-in` with `served: true` means done; carry on with what they originally asked for. `served: false` means the account is outside the domains this service serves, and the cure is another sign-in as the right one. `failed` carries the reason, and an expired code just needs the command run again.

An account outside those domains is refused by name later too, saying which domains they are — a wrong-account answer, not a broken-setup one.

The two sign-ins are independent. A machine can read recordings and be unable to transcribe them, or the reverse; `doctor` is what tells the two apart.

| Variable | Effect |
| :-- | :-- |
| `PLAUD_TOKEN` | Access token, no config file needed |
| `PLAUD_EMAIL`, `PLAUD_CODE`, `PLAUD_OTP_TOKEN` | The code flow without flags |
| `PLAUD_PASSWORD` | Password for `login --password`, unattended |
| `PLAUD_WHISPER_URL` | Point at a different transcription service |
| `PLAUD_BIN` | Use this binary instead of resolving one |
| `PLAUD_CLI_VERSION` | Install a different release (`latest`, or a tag) |
| `ANTHROPIC_API_KEY` | Needed only by `plaud summarize` and `plaud ask` |

## CLI reference

```bash
plaud list [--tag NAME] [--since YYYY-MM-DD] [--before YYYY-MM-DD] [--has-transcript]
           [--has-summary] [--search STR] [--limit N] [--json]
plaud info <id> [--json]

plaud download <id> [--audio] [--transcript] [--summary] [--all]
                    [--format json|txt|srt|md] [--output-dir DIR] [--language pt]
                    [--whisper=false]                # refuse to transcribe, just report
plaud transcribe <id> [--format md|json|txt|srt] [--language pt] [--options no-polish]
                      [--output-dir DIR] [--identify]

plaud auth login | auth status | auth logout        # the transcription service

plaud speaker list [--long]
plaud speaker name <recording-id> <label> "First Last" --company X [--surname-unknown]
plaud speaker rename <current> "First Last" --company X
plaud speaker forget "First Last"
plaud speaker enroll --company X [--dry-run] [--limit N] [--max-per-speaker N]

plaud search "text" [--limit N] [--no-cache]     # over transcripts, cached locally
plaud summarize <id> [--template meeting|detailed] [--prompt "..."] [--output FILE]
plaud ask <id> "question"                        # streams the answer

plaud tag list | tag create "Name" | tag delete "Name"
plaud me
```

`--debug`, `--json` and `--help` work on every command. `plaud sync` bulk-downloads everything to a local folder; prefer `fetch` or `pull`, which put the file where the repository wants it.

## Rules

- **Never delete a recording from Plaud.** This skill reads, transcribes and organizes, and nothing here removes anything from the account.
- **Transcribing costs a download and a GPU pass**, so it is a decision, not a step. One recording on request, a batch only after the user confirms the batch.
- **Never invent who a speaker is.** The service names the voices it already knows; an unnamed one stays `SPEAKER_01` until somebody who was in the room says otherwise. Guessing from context puts a name on a voice for everyone else too.
- **Keep the transcript in the language it was spoken.** Translating a meeting loses what made it worth keeping; a summary follows the destination's language if that differs.
- **The transcript is the source, the note is what people read.** Keep the transcript reachable from the note rather than replacing it.
