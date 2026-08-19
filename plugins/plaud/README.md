# plaud

Plaud.ai records the meeting; this plugin is how that audio becomes text inside a repository.

It stops at the transcript. Turning it into a note, naming the file, choosing where it goes: that is the repository's business, declared in `.plaud.json` at its root. The same skill then serves a knowledge base that indexes every recording it has ever seen and a client project that only wants the occasional call, without knowing anything about either.

## Install

```
/plugin marketplace add nexaedge/nexaedge-marketplace
/plugin install plaud@nexaedge-marketplace
```

Python 3 is the only thing that has to be installed. The Plaud client is a single Go binary, and if one is not already on PATH the plugin fetches the pinned release of [`plaud-cli`](https://github.com/jaisonerick/plaud-cli) into `~/.local/share/plaud-cli/bin` on first use, matched to the platform and verified against the release's sha256. No sudo, no PATH changes, and nothing written inside the plugin directory, which is replaced on every update.

That binary is not code-signed, so Windows may refuse it and name the publisher as unknown. The installer clears the download tag on the copy it places; a copy fetched by hand needs `Unblock-File`, and a release nobody has run yet may still need **More info → Run anyway** once.

What a fresh environment still needs is an authenticated account:

| Variable | Effect |
| :-- | :-- |
| `PLAUD_EMAIL`, `PLAUD_PASSWORD` | Credentials for `plaud login --password`, so a machine can be set up in one step with no prompt. |
| `PLAUD_WHISPER_URL` | Point at a different transcription service. |
| `PLAUD_TOKEN` | Access token, standing in for `~/.config/plaud/token.json` entirely. Nothing is written to disk, which suits an ephemeral container. |
| `PLAUD_BIN` | Use this binary instead of resolving one. |
| `PLAUD_CLI_VERSION` | Install a different release: `latest`, or an explicit tag. |

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
python3 "$HUB" fetch <id>                                        # transcribing it first if needed

python3 "$HUB" refresh && python3 "$HUB" build                   # catalog mode
python3 "$HUB" pull <id> --project acme --file comms/2026-08-06-call/
python3 "$HUB" query "SELECT id, filename FROM unfiled"          # no sqlite3 binary needed
python3 "$HUB" status
```

Plaud no longer transcribes for these accounts: a recording without a transcript is sent to the Whisper service on the way through, which takes minutes and wakes a GPU somebody pays for. Speakers the service recognises come back named as `First Last (Company)`. Nothing here deletes anything from the account.
