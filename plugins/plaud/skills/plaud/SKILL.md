---
name: plaud
description: >-
  Work with Plaud.ai voice recordings: find a recording, bring its transcript into the current repository, keep a set of recordings in sync, and say who is speaking. Where the transcript lands, what it is called and what describes it are read from the repository's own `.plaud.json`, never assumed. Triggers "plaud", "gravação", "recording", "transcrição", "transcript", "processa essa call", "essa reunião foi gravada".
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

Everything is the `plaud` CLI. It talks to Plaud, transcribes, recognises voices, and reads what the repository declares about where a transcript belongs. Your job is to point it at the right recording, make sure the repository declares what it needs, and hand the result to whatever files it.

## Get the CLI

```bash
PLAUD=$("${CLAUDE_PLUGIN_ROOT}/skills/plaud/ensure_plaud")
```

That prints the path to a current binary, installing one if the machine has none. It is the only Python here, it needs network on the first run, and it puts the binary somewhere the shell looks so the person whose machine it is can type `plaud` too. Use `"$PLAUD"` in every command below, since a freshly installed directory is not on the PATH of a shell that is already running.

## Start by checking the ground

```bash
"$PLAUD" doctor
```

One report covering both sign-ins and how this repository is configured. When something is missing this is what says which one, so run it before concluding that a recording is the problem.

**There are two sign-ins and they answer different questions.** The Plaud account says which recordings can be read; a Google account says whether anything can be transcribed, because transcription runs on a shared service. Being signed in to one and not the other fails halfway through a task, which is why `doctor` reports them separately. `NOT AUTHENTICATED` and `NOT SIGNED IN` both send you to *Signing the user in*, and neither is a blocker to hand back.

**Signing in is your job, not the user's.** Assume the person you are working for will never open a terminal: walk them through it in the conversation, asking for an emailed code and never for a password.

## What the repository declares

```bash
"$PLAUD" config
```

`.plaud.json` at the repository's root says where transcripts go, what they are called, what describes them and where they belong afterwards. It is found from the working directory upwards, so it works from anywhere inside the repository.

**A repository with no `.plaud.json` is not broken, and it is not yours to fix silently.** Transcripts can still be fetched into a path named on the call. But a repository that will take in more than one recording should declare itself, and writing that file is part of this skill — see *Configuring a repository*.

`filing` in the output is the document saying where a transcript belongs here. **Read it before writing anything.** If it is absent, look at the repository's `CLAUDE.md`/`AGENTS.md`, and if that settles nothing, ask.

## Finding the recording

```bash
"$PLAUD" list --since 2026-08-01 --limit 20     # recent
"$PLAUD" list --search "orçamento" --json       # by name
"$PLAUD" list --tag "PPFX - Amanda"             # by tag
"$PLAUD" info <id>                              # one recording
```

When several could be the one, show the candidates with date and duration and let the user pick, rather than guessing from the title.

## Bringing one transcript in

```bash
"$PLAUD" fetch <id>
"$PLAUD" fetch <id> --to comms/2026-08-06/transcript.md
```

With no `--to` it lands where the repository puts transcripts, under the name the repository uses. `--to` ending in a file extension is the transcript's exact file; anything else is a directory, and the repository's naming still applies. The summary comes along when Plaud has one.

**A recording without a transcript is transcribed on the way.** `fetch` finishes the job whichever state the recording is in, and takes minutes rather than seconds when the service has not decoded it yet. Never offer the user a choice about that or ask them to weigh it: finishing the transcript is what the tool is for.

**A recording is transcribed once.** The service keeps what it decoded, so fetching the same recording again — to another path, on another machine, after the file was filed elsewhere — comes back in seconds, and with the names as they are known today.

Two flags override that, and both cost a GPU pass, so neither is a default:

```bash
"$PLAUD" fetch <id> --force          # the transcript on record is wrong; make it again
"$PLAUD" fetch <id> --language pt    # it came back in the wrong language; settle it
```

`--language` is the way out when a meeting comes back translated: Whisper renders rather than mis-spells when it reads the language wrong, so the file is fluent and entire in a language nobody spoke, with nothing in it to say a decision was made.

**Fetching a transcript that is already there does not transcribe it again: it brings the names in it up to date.** A voice named after the file was written is still `SPEAKER_01` in it, and this is what goes back and fixes that. It costs a request, so it is worth doing after naming anybody.

## Bringing in a set

```bash
"$PLAUD" sync --profile cerc --dry-run
"$PLAUD" sync --profile cerc
"$PLAUD" sync --tag "PPFX - Amanda" --since 2026-08-01
```

A profile names both where the recordings are filed and the tag that selects them, so `--profile cerc` is the whole instruction. Running it twice decodes nothing the second time: what says a recording is here is the file at the destination.

**The tag is not in the repository, and that is deliberate** — see *Two owners, one profile*. A profile whose tag nobody has set is refused, with the command that sets it. An account with no tags at all takes the other route, *When the account has no tags*.

A recording turned down with `triage skip` is left alone here from then on.

It does not leave the transcripts already here alone, though. Every one in range is asked about again, and **the ones whose turns changed name are listed at the end of the run** — that is how a name settled since reaches a file that was written before it. `--only-new` skips that half.

**Always `--dry-run` a sync first and show the user the list.** A batch is a decision somebody should make on purpose, not because transcribing is expensive.

## Saying who was in the room

The repository's `context` document is the base and covers every recording in it: what gets read out of it is who the people are and how their names, companies and systems are spelt, which the subject of one meeting barely changes. **You do not need to know what a recording is about to fetch it well.**

What that document cannot know is who was in this particular room. The calendar can, and knows it before anybody has heard the audio: the event at the recording's time carries a title and a guest list of real names and email domains, which is exactly the material a name is corrected from. Look it up when the recording involves people the repository does not name, and pass what you find:

```bash
"$PLAUD" fetch <id> --context "Calendário: CERC x Vexia, esteira de pagamentos.
Presentes: Éricles Bento (CERC), Luana (Vexia), Thiago Duarte (Vexia)."
```

**`--context` is added to the repository's document, not swapped for it**, so the project's spellings and the room's both reach the transcript. `--context-file` is the other way: it stands in for that document, which is how one recording described by a paper of its own is fetched.

**Never write a description about work other than this recording's.** What the polisher reads there is how names are spelt, and a description naming other companies makes it write those over the ones being said: a briefing about Bayer and Aurora turned NexaEdge into "DIN" and "DIGI", and naming NexaEdge fixed it.

Never invent a guest list either: an attendee you guessed at becomes a name written into the record.

Then read the file. A long transcript is raw speech: expect false starts, crosstalk and names spelled by ear, and treat what people said as claims rather than facts.

## Who is speaking

Transcripts come back with the voices the service recognises already named, as `First Last (Company)`. A voice it has never heard stays `SPEAKER_01`, and naming it is what teaches it:

```bash
"$PLAUD" speaker list
"$PLAUD" speaker name <recording-id> SPEAKER_01 "Jaison Erick" --company NexaEdge
```

The recording id is the one `list` shows; nothing about the voices is kept on this machine, so naming one needs no file and no audio.

After naming somebody, fetch the transcript again — or run `sync`, which does it for everything at once and says which files changed.

The file carries, in its front matter, which voice each name in it stands for, and the recording it came from:

```
---
recording: bf1ee96b1f14cff5c2d71bf6fda842f0
voices:
  "Jaison Erick (NexaEdge)": [v_7f3a91]
  "SPEAKER_02": [v_91bc04]
---
```

**Keep that block when you file the transcript somewhere else.** It is what lets the names be corrected later; a copy without it can only be fixed by transcribing the audio again, which renumbers the voices and loses the names already given.

A label can hold two people, which happens when they talk over each other. Naming it teaches the average of the two voices and helps nobody, so that one is cut apart by the stretches instead:

```bash
"$PLAUD" speaker teach <recording-id> --ranges divisao.json --dry-run
```

where the file lists each person and the milliseconds they speak — `[{"name": "Jaison Erick", "company": "NexaEdge", "ranges": [[262000, 271000]]}]`. Read the transcript's timestamps to build it, and confirm with the audio before running it without `--dry-run`.

People are shared by everyone using the service, which is why a first name alone is refused: "Amanda" names whichever Amanda the person typing meant. A surname nobody knows is a different thing and takes `--surname-unknown`, after which the company does the identifying.

**Ask, do not infer.** Working out from context that SPEAKER_01 is probably the person whose meeting it was is exactly the guess that puts a wrong name on a voice for every other user. If nobody in the conversation knows, leave it.

## Handing off

Follow the `filing` document. If the repository has its own skill for meeting notes or for filing documents, use it: that skill owns the destination, the naming and the structure, and this one has already done its part by putting readable text on disk.

Say where the transcript landed and where the note went, so the next reader can follow the thread back to the source.

## Configuring a repository

When a repository will take in more than the occasional recording, write `.plaud.json` at its root. **Read the repository first** — its `CLAUDE.md`/`AGENTS.md`, its meeting-notes or filing skill, and how the documents already there are named — and then propose the file to the user before writing it. What you are encoding is that repository's convention, and getting it wrong files every future transcript in the wrong place.

```json
{
  "context": "contexto/briefing.md",
  "filing": ".agents/skills/meeting-notes/SKILL.md",
  "scratch": "workspace/plaud",
  "language": "pt",
  "name": "{date}-{slug}.md",
  "front_matter": { "type": "Transcript" },
  "profiles": {
    "cerc": { "dest": "reunioes/{year}", "front_matter": { "client": "CERC" } }
  }
}
```

| Key | What to put there |
| :-- | :-- |
| `context` | A file describing this work: a briefing, an agenda, the people and companies involved. **The one key worth having in every repository**, because it is what settles how names are spelt, so two transcripts of the same people agree. A thin one is better than none. If nothing suitable exists, write one with the user. |
| `filing` | The document saying where a transcript belongs here. Point it at the repository's own meeting-notes skill or filing convention, not at a copy. |
| `scratch` | Where transcripts land when nothing names a destination. Point it at a git-ignored directory when transcripts should not be committed as they are. |
| `language` | The language these meetings are held in, when it is always the same one. Removes a whole class of translated transcript, and costs nothing: a transcript already on record in that language is still handed back. |
| `name`, `dest` | Templates over `{date}`, `{year}`, `{month}`, `{day}`, `{time}`, `{slug}`, `{id}`, `{short_id}`. Match what the repository already does; a field nothing answers is refused rather than written into a filename. |
| `front_matter` | Keys every transcript should arrive with, so the filing step is not editing them in afterwards. |
| `profiles` | One per recurring set of recordings: where they go and what they are called. **Never the tag** — that is the user's half. |
| `hub` | Turns on the catalog and names the directory holding it. Only for a repository where the set of recordings is itself something to track. |
| `exclude_tags`, `exclude_reason` | Tags whose recordings are out of scope here — typically because another repository owns them. Catalog only. |
| `utc_offset` | Hours from UTC, so two machines file one recording under one day. |

Check it with `"$PLAUD" config`, and fetch one recording before declaring it done.

## Two owners, one profile

**A Plaud tag lives in one person's account.** "PPFX - Amanda" is a tag Amanda made; a teammate who clones the repository has their own account, their own tags, and a committed tag selects nothing for them. So a profile is written by two people:

- The **repository** says where transcripts of that kind go, what they are called and what their front matter carries. That is in `.plaud.json` and is committed.
- The **person** says which of *their* recordings are of that kind. That is in `~/.config/plaud/settings.json`, is never committed, and is written with:

```bash
"$PLAUD" tag list                                   # what this account actually has
"$PLAUD" profile set cerc --tag "PPFX - Amanda"
"$PLAUD" profile list                               # which profiles can select anything
```

The settings are keyed by where the repository is hosted, so they survive a fresh clone, a second checkout and another machine.

**When `profile list` shows a profile with no tag, that is the setup step, not a fault.** Show the user `tag list`, ask which tag is theirs for this work, and set it. Never guess: a wrong tag silently syncs another client's meetings into this repository.

The same file takes `defaults`, for what is true of the person wherever they work, and can override any repository key for one repository. `"$PLAUD" config` prints `set_in`, which names the layer behind each value — the repository, that person's settings for it, or their defaults — so a value that is not what the committed file says can be traced without guessing.

## When the account has no tags

**Plenty of people tag nothing.** `tag list` comes back empty or useless, and then nothing about a recording says which work it belongs to except what was said in it. That is the case `triage` is for, and it is a conversation with the user, not a command you run and report:

```bash
"$PLAUD" triage --since 2026-08-01
"$PLAUD" triage --limit 15 --json      # one object per recording, to reason over
```

Every recording that is not already here and has not been turned down comes back with its date, its length, **the speakers the service recognised**, and enough of what was said to place it. Nothing is written to disk: transcribing is what makes a recording readable at all, the service keeps what it decoded, so one kept afterwards arrives in seconds and one turned down cost a single pass, ever.

**Read the speakers first.** A recording whose voices are "Fabian Kluth (Dinie), Pedro Gomes (Dinie)" is Dinie's, whatever the opening minute of small talk says. The excerpt settles the ones the voices do not.

Then **propose, and let the user decide**:

```bash
"$PLAUD" fetch <id>                                    # it belongs here
"$PLAUD" triage skip <id> <id> --reason "Dinie"        # it does not, and stop offering it
"$PLAUD" triage skipped                                # what has been turned down, and why
"$PLAUD" triage unskip <id>                            # you were wrong
```

Group your proposal — "these six look like this client, these three look personal, these two I cannot place" — and show the date, the length and the speakers for each, so the user is confirming rather than reading. **Never skip on your own judgement.** A recording turned down stays turned down and stops being offered, which is the point and also why a wrong call is invisible afterwards.

Write the reason. What tells a recording turned down for being another client's from one turned down for being three seconds of pocket noise is the reason, and in six months neither the date nor the title says.

**Start narrow.** `--since` a month back, or `--limit 15`, before `--all`: an account with hundreds of untranscribed recordings is hours of GPU, and the user should agree to that set before it starts.

## The catalog

Only for a repository declaring `hub`: an index of every recording it knows about, what it is, whether it has been transcribed and where it was filed. It is `catalog.jsonl` in that directory, git-tracked, one JSON object per recording.

```bash
"$PLAUD" catalog refresh                  # merge the account's recordings in; curation is kept
"$PLAUD" catalog status                   # counts by status
"$PLAUD" catalog list --unfiled --min-minutes 5
"$PLAUD" catalog list --project dinie --json
"$PLAUD" catalog set <id> project=acme path=notes/acme.md status=filed
```

`status` is the manifest: `pending` (no transcript yet), `transcribed` (has one, not filed), `filed` (mapped to a destination), `excluded` (out of scope here). The first two are recomputed on every refresh; the last two are a person's decision and a refresh never touches them, nor any other curated field.

`fetch` and `sync` update the entry themselves, so there is no separate step to remember. Commit `catalog.jsonl` and whatever was pulled.

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
   "$PLAUD" login --send-code --email <email> --json
   ```

   That prints an `otp_token`, which is a handle for the pending login, not a credential to keep. Nothing is stored yet.

2. Ask the user for the code that just arrived in their inbox (six digits, from Plaud), and finish:

   ```bash
   "$PLAUD" login --email <email> --otp-token <otp_token> --code <code>
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
"$PLAUD" auth status      # who is signed in, and whether it still works
"$PLAUD" auth logout      # forget it
```

**Conduct this login too, in the conversation.** It asks nothing of the machine — no browser, no port, no visible terminal — so it works the same over ssh, in a container, or on a phone.

Start it in the background and read the first line it prints:

```bash
"$PLAUD" auth login --json > /tmp/plaud-login.json 2>&1 &
```

The first line arrives immediately and carries `user_code` and `verification_url`. **Show both to the user and ask them to enter the code**, then watch the same file: the command is still running, and writes a second line when the sign-in lands.

```json
{"status":"pending","user_code":"QPB-QYM-SFSJ","verification_url":"https://www.google.com/device","expires_in":1800}
{"status":"signed-in","email":"someone@nexaedge.com","served":true}
```

`signed-in` with `served: true` means done; carry on with what they originally asked for. `served: false` means the account is outside the domains this service serves, and the cure is another sign-in as the right one. `failed` carries the reason, and an expired code just needs the command run again.

| Variable | Effect |
| :-- | :-- |
| `PLAUD_TOKEN` | Access token, no config file needed |
| `PLAUD_EMAIL`, `PLAUD_CODE`, `PLAUD_OTP_TOKEN` | The code flow without flags |
| `PLAUD_PASSWORD` | Password for `login --password`, unattended |
| `PLAUD_WHISPER_URL` | Point at a different transcription service |
| `PLAUD_BIN` | Use this binary instead of resolving one |
| `PLAUD_CLI_VERSION` | Install a different release (`latest`, or a tag) |
| `PLAUD_SETTINGS` | The file holding what you settle per repository |
| `ANTHROPIC_API_KEY` | Needed only by `plaud summarize` and `plaud ask` |

## CLI reference

```bash
plaud doctor                                     # both sign-ins and this repository
plaud config                                     # what .plaud.json resolved to

plaud fetch <id> [--to PATH] [--summary-to PATH] [--profile NAME]
                 [--context TEXT | --context-file FILE]
                 [--language pt] [--force] [--format md|json|txt|srt] [--json]
plaud sync [--profile NAME] [--tag NAME] [--since DATE] [--all]
           [--dry-run] [--only-new] [--json]

plaud list [--tag NAME] [--since YYYY-MM-DD] [--before YYYY-MM-DD] [--has-transcript]
           [--has-summary] [--search STR] [--limit N] [--json]
plaud info <id> [--json]

plaud catalog refresh | status | list [filters] | set <id> key=value ...

plaud profile list                                   # this repository's profiles
plaud profile set <name> --tag "<your tag>"          # your half, never committed
plaud profile unset <name>

plaud triage [--since DATE] [--limit N] [--all] [--excerpt N] [--json]
plaud triage skip <id> ... [--reason X] | unskip <id> ... | skipped

plaud speaker list [--long]
plaud speaker name <recording-id> <label> "First Last" --company X [--surname-unknown]
plaud speaker rename <current> "First Last" --company X
plaud speaker forget "First Last"
plaud speaker enroll --company X [--dry-run] [--limit N] [--max-per-speaker N]
plaud speaker teach <recording-id> --ranges FILE [--dry-run]

plaud auth login | auth status | auth logout        # the transcription service
plaud login --send-code --email <email> --json      # the Plaud account
plaud me

plaud search "text" [--limit N] [--no-cache]
plaud summarize <id> [--template meeting|detailed] [--prompt "..."] [--output FILE]
plaud ask <id> "question"
plaud download <id> [--audio] [--summary] [--output-dir DIR]
plaud tag list | tag create "Name" | tag delete "Name"
```

`--debug`, `--json` and `--help` work on every command.

`transcript` is the lower-level command `fetch` is built on: it takes an output directory or an exact file rather than reading the repository. Reach for it only when the repository's rules are not what you want.

## Rules

- **Never delete a recording from Plaud.** This skill reads, transcribes and organizes, and nothing here removes anything from the account.
- **A batch is agreed before it runs.** `sync --dry-run`, show the list, then run it. One recording on request needs no ceremony.
- **Never invent who a speaker is.** The service names the voices it already knows; an unnamed one stays `SPEAKER_01` until somebody who was in the room says otherwise.
- **Keep the transcript in the language it was spoken.** Translating a meeting loses what made it worth keeping; a summary follows the destination's language if that differs.
- **The transcript is the source, the note is what people read.** Keep the transcript reachable from the note rather than replacing it.
