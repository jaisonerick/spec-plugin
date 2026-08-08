---
name: plugins
description: Install, find, update and remove NexaEdge plugins, on whichever agent is running. Use when someone asks to install a plugin or skill, wants to know what is available, asks to update their plugins, or says something like "what can I install", "what plugins do I have", "add the html report skill", "update my plugins". Also use right after the nexaedge plugin is installed, to explain to the person what they just got.
---

# NexaEdge plugins

One front end for the NexaEdge plugin catalog across Claude Code, Codex and Antigravity.

Everything installs at **user scope**, once per machine. Never copy a skill into a project repository to make it available: that is what creates the same skill in five places with five different versions.

## The script

Always invoke it as `~/.nexaedge/bin/nexaedge`, written exactly that way. Referred to as `MKT` below.

**Do not resolve that path, expand it, or substitute the file it points at.** Agents that ask permission before running a shell command match on the literal command string, so reaching this script by a second path means the person gets asked to approve it all over again. One spelling, one approval, forever.

Only if that launcher does not exist, fall back to `scripts/nexaedge.sh` in this plugin, at `../../scripts/nexaedge.sh` relative to this file, or `"${CLAUDE_PLUGIN_ROOT}"/scripts/nexaedge.sh` on Claude Code. Running any command creates the launcher, so the fallback should be needed at most once.

```bash
"$MKT" list [query]        # what this agent can install
"$MKT" install <name>...   # install at user/global scope
"$MKT" remove <name>...    # remove
"$MKT" update              # refresh the catalog and installed plugins
"$MKT" status              # detected platform + what is installed
"$MKT" detect              # just the platform
```

The script detects which agent is running from environment markers. If more than one agent is installed and the markers are absent, it refuses to guess and asks for `--platform`. **You know which agent you are**, so pass `--platform claude`, `--platform codex` or `--platform antigravity` when that happens instead of picking one at random.

## Handling requests

**"What is available?"** → `"$MKT" list`. The listing is already filtered to what runs on this agent, so do not offer the person something that will not work here. If they ask why a plugin they heard about is missing, `catalog.json` in the repository has a `requires` field explaining what that plugin needs.

**"Install X"** → `"$MKT" install X`. Then relay the activation line the script prints, because it differs per agent and the person will otherwise think nothing happened:

- Claude Code: run `/reload-plugins`, or restart
- Codex: start a new thread
- Antigravity: reload the window

**"Update"** → `"$MKT" update`. Safe to run any time.

**"Remove X"** → `"$MKT" remove X`.

## Right after this plugin is installed

The person who just bootstrapped has the `nexaedge` plugin and nothing else. Do not install anything more on your own. Tell them, briefly:

1. It is installed at user scope, so it works in every project on this machine, and nothing was added to the repository they are in.
2. They can now ask for things in plain language: "what plugins are available?", "install the html report one", "update my plugins".
3. Run `"$MKT" list` and show them what they can install, so the next step is concrete rather than abstract.
4. The activation step for this agent, from the list above.

Keep it to a few lines. They asked for a setup, not a tutorial.

## Keeping plugins current

`"$MKT" update --if-stale` is a no-op unless the last update was more than 12 hours ago, which makes it cheap enough to run at the start of every session.

On Claude Code this plugin already wires that into a `SessionStart` hook. On Codex and Antigravity the hook format for plugin-provided hooks is not confirmed, so nothing is wired automatically there. If someone on those agents wants it, the honest answer is that they run `"$MKT" update` when they feel like it, or add the command to their own shell startup. Do not invent a hook configuration for them.
