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
HUB="${CLAUDE_PLUGIN_ROOT}/skills/plaud/plaud_hub"
```

`$HUB` runs itself: it finds this machine's Python 3 — `python3`, `python` or the `py` launcher — and runs the engine with it, so nothing here assumes a name that a given machine may not have.

## Start by checking the ground

```bash
"$HUB" doctor
```

One report covering the CLI, both sign-ins, and how this repository is configured. When something is missing this is what says which one, so run it before concluding that a recording is the problem. `NOT AUTHENTICATED` on the Plaud line and `NOT SIGNED IN` on the service line both send you to *Signing the user in*, and neither is a blocker to hand back.

```bash
"$HUB" config
```

Prints the resolved configuration alone, and which of the two modes applies:

- **ad-hoc**: no catalog. Recordings are fetched one at a time, on demand, and nothing about them is stored. This is the right mode for a repository that only wants the occasional transcript.
- **catalog**: the repository keeps an index of every recording it knows about: what it is, whether it has been transcribed, where it was filed. Worth it when the set of recordings is itself something to keep track of.

`filing` in the output is the document that says where a transcript belongs in this repository. **Read it before writing anything.** If it is absent, the repository has not declared a convention: look at its `CLAUDE.md`/`AGENTS.md`, and if that settles nothing, ask.

**A repository with no `.plaud.json` declares no context either, and then describing the recording is your job.** Nothing is broken and nothing needs to be created: pass `--context` on the fetch, in the same call. What it must carry is who is in the recording and what it is about, in real names:

```bash
"$HUB" fetch <id> --context "Reunião entre Jaison Erick (NexaEdge) e Amanda Destro (Aurora)
sobre o faturamento da CERC. Termos: CCB, agenda, trava."
```

Take those names from the calendar event at the recording's time, from the repository's own documents, or from the person you are working for. **Never write a description about work other than this recording's.** What the polisher reads there is how names are spelt, and a description naming other companies makes it write those over the ones being said: a briefing about Bayer and Aurora turned NexaEdge into "DIN" and "DIGI", and naming NexaEdge fixed it.

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
"$HUB" fetch <id> --to comms/2026-08-06-reuniao-x/transcript.md
"$HUB" fetch <id>                       # into the configured directory, slug-named
```

`--to` ending in `.md` is the transcript's file; anything else is a directory, and the summary lands beside it (`--summary-to` puts it somewhere specific).

**A recording without a transcript is transcribed on the way.** `fetch` finishes the job whichever state the recording is in, and takes minutes rather than seconds when there is nothing on record yet. Never offer the user a choice about that or ask them to weigh it: finishing the transcript is what the tool is for.

**A recording is transcribed once.** The service keeps what it decoded, so fetching the same recording again — to another path, after the file was filed elsewhere, on another machine — comes back in seconds and with the names as they are known today. Nothing is decoded twice unless somebody asks for it, and asking is what `--force` on the CLI is for.

Language auto-detects, speakers are separated, and the ones the service recognises come back named: a line reads `**Jaison Erick (NexaEdge)** (00:00:09):` rather than `SPEAKER_01`. A summary comes along only when Plaud already has one.

**Fetching a transcript that is already there does not transcribe it again: it brings the names in it up to date.** A voice named after the file was written is still called `SPEAKER_01` in it, and this is what goes back and fixes that. It costs a request, so it is worth doing after naming anybody.

The file carries, in its front matter, which voice each name in it stands for:

```
---
voices:
  "Jaison Erick (NexaEdge)": [v_7f3a91]
  "SPEAKER_02": [v_91bc04]
---
```

**Keep that block when you file the transcript somewhere else.** It is what lets the names be corrected later; a copy without it can only be fixed by transcribing the audio again, which renumbers the voices and loses the names already given.

### Saying who was in the room

The repository's `context` document is the base and covers every recording in it: what gets read out of it is who the people are and how their names, companies and systems are spelt, which the subject of one meeting barely changes. **You do not need to know what a recording is about to fetch it well.**

What that document cannot know is who was in this particular room. The calendar can, and knows it before anybody has heard the audio: the event at the recording's time carries a title and a guest list of real names and email domains, which is exactly the material a name is corrected from. Look it up when the recording involves people the repository does not name — an outside company, a first meeting, a recording nobody can place — and pass what you find:

```bash
"$HUB" fetch <id> --context "Calendário: CERC x Vexia, esteira de pagamentos.
Presentes: Éricles Bento (CERC), Luana (Vexia), Thiago Duarte (Vexia)."
```

**`--context` and `--context-file` are the CLI's own flags and mean the same thing here**, with one addition: a `--context` written for a single recording is **added** to the repository's document rather than replacing it, so the project's spellings and the room's both reach the transcript. `--context-file` replaces that document, which is how one recording is described by a paper of its own.

Never invent a guest list: an attendee you guessed at becomes a name written into the record.

Which of the two you pass is said, never guessed from the value: a description carries a date, a date carries a slash, and a slash read as a path turned the sentence into a filename nobody could open.

Then read the file. A long transcript is raw speech: expect false starts, crosstalk and names spelled by ear, and treat what people said as claims rather than facts.

## Who is speaking

Transcripts come back with the voices the service recognises already named, as `First Last (Company)`. A voice it has never heard stays `SPEAKER_01`, and naming it is what teaches it:

```bash
plaud speaker list                       # everyone it knows
plaud speaker name <recording-id> SPEAKER_01 "Jaison Erick" --company NexaEdge
```

The recording id is the one `plaud list` shows; nothing about the voices is kept on this machine, so naming one needs no file and no audio.

After naming somebody, fetch the transcript again: the file gets their name where it said `SPEAKER_01`, and so does every other transcript you fetch again that they speak in.

A label can hold two people, which happens when they talk over each other. Naming it teaches the average of the two voices and helps nobody, so that one is cut apart by the stretches instead:

```bash
plaud speaker teach <recording-id> --ranges divisao.json --dry-run
```

where the file lists each person and the milliseconds they speak — `[{"name": "Jaison Erick", "company": "NexaEdge", "ranges": [[262000, 271000]]}]`. Read the transcript's timestamps to build it, and confirm with the audio before running it without `--dry-run`.

People are shared by everyone using the service, which is why a first name alone is refused: "Amanda" names whichever Amanda the person typing meant. A surname nobody knows is a different thing and takes `--surname-unknown`, after which the company does the identifying.

**Ask, do not infer.** Working out from context that SPEAKER_01 is probably the person whose meeting it was is exactly the guess that puts a wrong name on a voice for every other user. If nobody in the conversation knows, leave it.

## Handing off

Follow the `filing` document. If the repository has its own skill for meeting notes or for filing documents, use it, since that skill owns the destination, the naming and the structure, and this one has already done its part by putting readable text on disk.

Say where the transcript landed and where the note went, so the next reader can follow the thread back to the source.

## Catalog mode

Only when `config` reports a hub. The catalog is `catalog.jsonl` (source of truth, git-tracked, one JSON object per recording), a git-ignored sqlite index rebuilt from it, and the raw transcripts pulled so far.

```bash
"$HUB" refresh     # merge `plaud list` + tags into the catalog; curation is preserved
"$HUB" build       # recompile the sqlite index from the catalog
"$HUB" status      # counts by status
"$HUB" pull <id>   # fetch into the raw store and record the paths
"$HUB" set <id> project=<label> path=<repo-relative> status=filed
"$HUB" gen-links   # regenerate the page listing what still needs transcription
```

`status` is the manifest, so check it before processing a recording twice: `pending` (no transcript yet), `transcribed` (has one, not filed), `filed` (mapped to a destination through `path` and/or `repo`), `excluded` (out of scope for this repository). The first two are recomputed on every refresh; the last two are sticky, and a refresh never touches them or any other curation field.

Ad-hoc queries go through `query`, which is read-only and needs no `sqlite3` binary. The index has a `pending_transcription` and an `unfiled` view:

```bash
"$HUB" query "SELECT id, recorded_at, duration_min, filename FROM unfiled"
"$HUB" query "SELECT * FROM recordings WHERE project = 'acme'" --json
```

A batch is worth agreeing on before it starts, because it is a lot of recordings and minutes each, not because of what it costs. Filter to what the user actually wants, and confirm the set with them first:

```bash
for id in $("$HUB" query "SELECT id FROM pending_transcription WHERE duration_min >= 5" --no-header); do
  "$HUB" pull "$id"
done
```

`pending` here means Plaud holds no transcript, which is now the normal state rather than a problem: pulling one transcribes it.

Commit `catalog.jsonl` and whatever was pulled; the sqlite index is rebuildable and stays out of git.

## `.plaud.json`

At the repository root. `context` is required to bring a transcript in; everything else is optional, and without the file the skill runs ad-hoc and has nothing to tell you about filing.

```json
{
  "context": "docs/briefing.md",
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
| `context` | Path to a file describing this work: a briefing, an agenda, a list of the people and companies involved. Required, and it is what settles how their names are spelt, so two transcripts of the same people agree. Any file will do; a thin one is better than none. |
| `filing` | Path to the document that says where a transcript belongs here. The one key worth setting even in the simplest repository. |
| `scratch` | Default directory for `fetch` when `--to` is omitted. Point it at a git-ignored directory when transcripts should not be committed as they are. |
| `hub` | Turns on catalog mode and names the directory holding it. Absent means ad-hoc. |
| `exclude_tags` | Plaud tags whose recordings are out of scope: they stay indexed but are marked `excluded` on refresh. Catalog mode only. |
| `exclude_reason` | What to record as the reason for those. |
| `utc_offset` | Timezone for recording timestamps, in hours from UTC. Defaults to the machine's timezone. |

## Setup

**The binary takes care of itself.** `doctor` (or the first command that needs it) installs the pinned release of [`jaisonerick/plaud-cli`](https://github.com/jaisonerick/plaud-cli) under `~/.local/share/plaud-cli/bin`, matched to the platform and checked against the release's sha256. A `plaud` already on PATH always wins, so an existing install is never disturbed. If that one is too old to reach the transcription service, `doctor` says so rather than failing obscurely halfway through a recording.

## Windows

The binary carries no code signature, and two different Windows features object to that. They look alike and are not, so read which one the message names before advising anything.

**SmartScreen** says the publisher is unknown and offers **More info → Run anyway**. It objects to the tag Windows puts on a download; the installer clears that tag on the copy it places, so this normally only appears for a copy fetched by hand, which `Unblock-File <path>` settles.

**Smart App Control** just refuses. There is no *Run anyway*, no per-app exception, and `Unblock-File` does nothing, because it is not about the tag: SAC declines to run anything unsigned. The only way through is to turn it off, in **Windows Security → App & browser control → Smart App Control**. On a Windows kept up to date it can be turned back on afterwards; older builds could not, and needed a clean install, so check that before advising it and say which it is.

Turning SAC off is a real reduction in that machine's protection, and it is the user's call, not yours. Say what it costs and let them decide. Never suggest disabling SmartScreen or Defender, which is a different and worse trade.

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

plaud transcript <id> --context FILE|TEXT         # required: a file describing it, or the description
                      [--format md|json|txt|srt] [--language pt]
                      [--output-dir DIR] [--into FILE] [--identify]
                      [--force]                    # transcribe again instead of reusing
plaud download <id> [--audio] [--summary] [--output-dir DIR] [--force]

plaud auth login | auth status | auth logout        # the transcription service

plaud speaker list [--long]
plaud speaker name <recording-id> <label> "First Last" --company X [--surname-unknown]
plaud speaker rename <current> "First Last" --company X
plaud speaker forget "First Last"
plaud speaker enroll --company X [--dry-run] [--limit N] [--max-per-speaker N]
plaud speaker teach <recording-id> --ranges FILE [--dry-run]   # one label, two people

plaud search "text" [--limit N] [--no-cache]     # over transcripts, cached locally
plaud summarize <id> [--template meeting|detailed] [--prompt "..."] [--output FILE]
plaud ask <id> "question"                        # streams the answer

plaud tag list | tag create "Name" | tag delete "Name"
plaud me
```

`--debug`, `--json` and `--help` work on every command.

`--into` writes one recording to exactly that file, and refreshes the names in it when it is already there. It is how `fetch` puts a transcript where the repository wants it.

`transcript` and `download` also take the filters `list` takes, plus `--all`, and then act on every recording they keep. `download` skips what is already on disk; `transcript` refreshes the names in it. That is the bulk path, and it belongs to a person who asked for a batch: prefer `fetch` or `pull`, which put one file where the repository wants it.

## Rules

- **Never delete a recording from Plaud.** This skill reads, transcribes and organizes, and nothing here removes anything from the account.
- **A batch is agreed before it runs**, not because transcribing is expensive but because a hundred recordings is a decision somebody should make on purpose. One recording on request needs no ceremony.
- **Never invent who a speaker is.** The service names the voices it already knows; an unnamed one stays `SPEAKER_01` until somebody who was in the room says otherwise. Guessing from context puts a name on a voice for everyone else too.
- **Keep the transcript in the language it was spoken.** Translating a meeting loses what made it worth keeping; a summary follows the destination's language if that differs.
- **The transcript is the source, the note is what people read.** Keep the transcript reachable from the note rather than replacing it.
