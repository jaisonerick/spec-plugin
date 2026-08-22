# plaud

Plaud.ai records the meeting; this plugin is how that audio becomes text inside a repository.

It stops at the transcript. Turning it into a note, naming the file, choosing where it goes: that is the repository's business, declared in `.plaud.json` at its root. The same skill then serves a knowledge base that indexes every recording it has ever seen and a client project that only wants the occasional call, without knowing anything about either.

## Install

```
/plugin marketplace add nexaedge/nexaedge-marketplace
/plugin install plaud@nexaedge-marketplace
```

Python 3 is the only thing that has to be installed, and it does one job: put the CLI on the machine. Everything else is [`plaud-cli`](https://github.com/jaisonerick/plaud-cli), a single Go binary. A `plaud` already on PATH is the one kept up to date; with nothing on PATH the pinned release is fetched into `~/.local/bin` (`%LOCALAPPDATA%\plaud` on Windows), matched to the platform and verified against the release's sha256, so the person whose machine it is can type the name too. No sudo, and nothing written inside the plugin directory, which is replaced on every update.

That binary is not code-signed. SmartScreen reacts by naming the publisher as unknown and offering *Run anyway*; the installer clears the download tag it objects to, so that normally only appears for a copy fetched by hand. **Smart App Control** is stricter and simply refuses: no *Run anyway*, no per-app exception, and the only way through is turning it off in Windows Security, which recent Windows lets you turn back on.

What a fresh environment still needs is an authenticated account:

| Variable | Effect |
| :-- | :-- |
| `PLAUD_EMAIL`, `PLAUD_PASSWORD` | Credentials for `plaud login --password`, so a machine can be set up in one step with no prompt. |
| `PLAUD_WHISPER_URL` | Point at a different transcription service. |
| `PLAUD_TOKEN` | Access token, standing in for `~/.config/plaud/token.json` entirely. Nothing is written to disk, which suits an ephemeral container. |
| `PLAUD_BIN` | Use this binary instead of resolving one. |
| `PLAUD_CLI_VERSION` | Install a different release: `latest`, or an explicit tag. |
| `PLAUD_SETTINGS` | The file holding what you settle per repository. |

**The assistant signs the user in, and never asks for a password.** When the account is not authenticated, the skill runs the login as a conversation: it asks for the email, sends a one-time code, asks for the six digits that arrived in the inbox, and stores the token. A code expires in minutes and works once, which is what makes it safe to say out loud; a password is neither. Nothing in that flow needs a browser, an open port or a visible terminal, so it behaves the same in a terminal, a desktop app, a phone or a sandbox.

Transcription is a second sign-in, to the service that does it: `plaud auth login`, with a Google account on one of the domains that service serves. It asks nothing of the machine either — a short code and a URL the person opens on any device, so the assistant conducts this one too. `doctor` reports the two on separate lines, because being signed in to one and not the other fails in the middle of a task rather than at its start.

The two halves are callable separately, which is what makes it drivable by something that is not the account owner:

```bash
plaud login --send-code --email you@example.com --json   # → {"otp_token": "..."}
plaud login --email you@example.com --otp-token <handle> --code 123456
```

`plaud login --password` still exists for unattended provisioning, and accounts created through Google, Apple or Microsoft have no password at all until one is set in the Plaud app.

The resulting token is a JWT valid for months and nothing renews it, so `doctor` reports the expiry date alongside everything else it checks.

## Configure the repository

`.plaud.json` at the repository root says where transcripts go, what they are called, what describes them and where they belong afterwards. It is found from the working directory upwards, so it works from anywhere inside the repository. The file is optional, and so is every key in it.

```json
{
  "context": "contexto/briefing.md",
  "filing": ".agents/skills/meeting-notes/SKILL.md",
  "scratch": "workspace/plaud",
  "language": "pt",
  "name": "{date}-{slug}.md",
  "front_matter": { "type": "Transcript" },
  "profiles": {
    "cerc": { "tag": "PPFX - Amanda", "dest": "reunioes/{year}" }
  }
}
```

`context` is a file describing the work: the people, the companies, how their names are spelt. It is what makes two transcripts of the same people agree, and a thin one is better than none. `filing` points at the document that says where a transcript belongs here, which is what stops the agent inventing a destination. `scratch` is where a transcript lands when nothing names one; point it at a git-ignored directory when transcripts should not be committed as they arrive.

`name` and `dest` are templates over `{date}`, `{year}`, `{month}`, `{day}`, `{time}`, `{slug}`, `{id}` and `{short_id}`. A profile is a named set of those keys, and `plaud sync --profile cerc` brings in everything it selects.

**What a profile selects is not in this file.** A Plaud tag lives in one person's account, so a committed tag selects nothing for the next person who clones the repository. That half goes in `~/.config/plaud/settings.json`, is never committed, and is written with `plaud profile set cerc --tag "PPFX - Amanda"`. The settings are keyed by where the repository is hosted, so they survive a fresh clone and a second checkout, and the same file takes `defaults` for what is true of that person wherever they work. `plaud config` names the layer behind each value.

Adding `hub` turns on the catalog:

```json
{
  "hub": "studio/plaud",
  "filing": "studio/plaud/plaud.md",
  "exclude_tags": ["Client A"],
  "exclude_reason": "handled-in-the-client-repo"
}
```

That directory then holds `catalog.jsonl` — the source of truth, git-tracked, one JSON object per recording — and the transcripts pulled so far. Each recording carries a `status` (`pending`, `transcribed`, `filed` or `excluded`), which is what keeps the same call from being processed twice. Curation survives every refresh; only the Plaud-side fields are overwritten.

`utc_offset` (hours from UTC) fixes the timezone of recording timestamps when the machine's own is not the right one.

## Use

Ask Claude to process a recording. It resolves the installer through `${CLAUDE_PLUGIN_ROOT}`, which prints the path to a current binary; after that everything is the CLI.

```bash
PLAUD=$("${CLAUDE_PLUGIN_ROOT}/skills/plaud/ensure_plaud")

"$PLAUD" doctor                                      # both sign-ins and this repository
"$PLAUD" config                                      # what .plaud.json resolved to
"$PLAUD" fetch <id>                                  # into where this repository puts transcripts
"$PLAUD" fetch <id> --to comms/2026-08-06-call/transcript.md
"$PLAUD" profile set cerc --tag "PPFX - Amanda"       # which of your recordings feed it
"$PLAUD" sync --profile cerc --dry-run               # a whole set at once

"$PLAUD" catalog refresh                             # catalog mode
"$PLAUD" catalog list --unfiled --min-minutes 5
"$PLAUD" catalog set <id> project=acme status=filed
```

A recording without a transcript is transcribed on the way through, which takes minutes rather than seconds; one that has been through the service already comes back in seconds. Speakers the service recognises come back named as `First Last (Company)`, and fetching a transcript that is already on disk brings those names up to date rather than decoding anything. Nothing here deletes anything from the account.
