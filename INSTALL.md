# Instructions for an agent

You are reading this because someone asked you to set up NexaEdge on this machine. Follow the branch for whichever agent you are. Do not follow more than one.

Install **only** the plugin named `nexaedge`. It is the front end for everything else, and the person chooses the rest afterwards through conversation.

Adding the catalog is not enough on its own. Both commands in your branch have to run: the first registers where plugins come from, the second installs `nexaedge`.

Everything here installs at **user scope**, once per machine. Do not copy anything into the repository you are working in.

---

## If you are Claude Code

```bash
claude plugin marketplace add nexaedge/nexaedge-marketplace
claude plugin install nexaedge@nexaedge-marketplace --scope user
```

Then tell the person to run `/reload-plugins`, or restart. You cannot do it for them.

---

## If you are Codex

```bash
codex plugin marketplace add nexaedge/nexaedge-marketplace --ref main
codex plugin add nexaedge@nexaedge-marketplace
```

If `codex plugin` reports that plugins are unavailable, they are behind a feature flag on this machine. Enable it and retry:

```bash
codex --enable plugins plugin add nexaedge@nexaedge-marketplace
```

Then tell the person to start a new thread.

---

## If you are Antigravity

Antigravity has no marketplace. It discovers customizations from roots on disk, so this is one clone plus one symlink per plugin, with nothing copied.

```bash
git clone https://github.com/nexaedge/nexaedge-marketplace ~/.nexaedge/marketplace
~/.nexaedge/marketplace/plugins/nexaedge/scripts/nexaedge.sh install nexaedge --platform antigravity
```

The script links the plugin into `~/.gemini/config/plugins/`, Antigravity's global customization root. It touches nothing else. Then tell the person to quit and reopen Antigravity: reloading the window is not always enough, because customizations are read when the language server starts.

---

## If you are some other agent

Check whether it reads `SKILL.md` files from a directory you can register globally. If it does, clone the repository and point that mechanism at `plugins/nexaedge/skills/`. If it does not, say so plainly rather than improvising: this marketplace supports Claude Code, Codex and Antigravity today.

---

## After it is installed

Load the `plugins` skill and follow its "Right after this plugin is installed" section. In short: tell the person it is installed machine-wide, that nothing was added to their repository, and that they can now just ask for things ("what plugins are available?", "install the html report one", "update my plugins"). Run the skill's `list` command so they see real options instead of an abstract promise.

Do not install anything else on your own initiative.
