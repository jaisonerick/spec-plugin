# Instructions for an agent

You are reading this because someone asked you to set up the nexaedge marketplace. Follow the branch for whichever agent you are. Do not follow more than one.

Install **only** the `marketplace` plugin. It is the front end for everything else, and the person chooses the rest afterwards through conversation.

Everything here installs at **user scope**, once per machine. Do not copy anything into the repository you are working in.

---

## If you are Claude Code

```bash
claude plugin marketplace add nexaedge/nexaedge-marketplace
claude plugin install marketplace@nexaedge-marketplace --scope user
```

Then tell the person to run `/reload-plugins`, or restart. You cannot do it for them.

---

## If you are Codex

```bash
codex plugin marketplace add nexaedge/nexaedge-marketplace --ref main
codex plugin add marketplace@nexaedge-marketplace
```

If `codex plugin` reports that plugins are unavailable, they are behind a feature flag on this machine. Enable it and retry:

```bash
codex --enable plugins plugin add marketplace@nexaedge-marketplace
```

Then tell the person to start a new thread.

---

## If you are Antigravity

Antigravity has no marketplace. It discovers customizations from roots on disk, so this is one clone plus one symlink per plugin, with nothing copied.

```bash
git clone https://github.com/nexaedge/nexaedge-marketplace ~/.nexaedge/marketplace
~/.nexaedge/marketplace/plugins/marketplace/scripts/marketplace.sh install marketplace --platform antigravity
```

The script links the plugin into `~/.gemini/config/plugins/`, Antigravity's global customization root. It touches nothing else. Then tell the person to quit and reopen Antigravity: reloading the window is not always enough, because customizations are read when the language server starts.

---

## If you are some other agent

Check whether it reads `SKILL.md` files from a directory you can register globally. If it does, clone the repository and point that mechanism at `plugins/marketplace/skills/`. If it does not, say so plainly rather than improvising: this marketplace supports Claude Code, Codex and Antigravity today.

---

## After it is installed

Load the `marketplace` skill and follow its "Right after this plugin is installed" section. In short: tell the person it is installed machine-wide, that nothing was added to their repository, and that they can now just ask for things ("what plugins are available?", "install the html report one", "update my plugins"). Run the skill's `list` command so they see real options instead of an abstract promise.

Do not install anything else on your own initiative.
