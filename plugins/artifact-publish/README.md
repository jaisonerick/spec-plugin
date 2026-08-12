# artifact-publish

Publish a self-contained HTML file as a shareable artifact on **artifacts.nexaedge.com**, and get a link back.

It exists because a self-contained HTML solves "generate" but not "share": sending the file over chat loses the version, and a raw bucket link resolves against the browser's default account, which 403s anyone with more than one.

## How access works

**An artifact belongs to the domain of the Google account that published it, and only that domain can open it.** There is no registration and no allowlist: sign in with your work account and the domain of that account becomes the boundary. Personal accounts (`gmail.com` and friends) are refused, because treating `gmail.com` as a domain would mean granting access to everyone with a Gmail.

For people outside the domain, `--share N` returns a link that opens with no sign-in and expires in N days.

The listing shows only what **you** published, not the whole domain. There is no index of who uses the service.

## Install

```
/plugin marketplace add nexaedge/nexaedge-marketplace
/plugin install artifact-publish@nexaedge-marketplace
```

Requires Python 3 (standard library only) and a browser for the first sign-in.

## Use

Ask Claude to publish, share or send a link to an HTML file. Or run it directly:

```bash
python3 <skill-dir>/scripts/publish.py report.html
python3 <skill-dir>/scripts/publish.py report.html --as acme.com --share 7
python3 <skill-dir>/scripts/publish.py --whoami
```

## Configuration (optional)

`~/.config/nexaedge/artifacts.json` — every key optional:

```json
{
  "service": "https://artifacts.nexaedge.com",
  "default_domain": "acme.com",
  "accounts": {"acme.com": "you@acme.com"}
}
```

`accounts` only preselects the account on Google's sign-in screen. `default_domain` is the account used without `--as`; with a single account signed in, that one wins and no configuration is needed.

Sessions live in `~/.config/nexaedge/artifact-share/<domain>.json` with mode 600, one file per domain. A refresh token is worth a whole Google account until revoked; revoke at [myaccount.google.com/connections](https://myaccount.google.com/connections).

## Quota

Publishing is open to any Workspace domain, so a quota is what bounds it: a new domain starts with a low ceiling on artifact count and total bytes. The refusal says how much is in use. Ask for a larger ceiling at hello@nexaedge.com.

Each file is capped at 100 MB.

## Writing the HTML

Prefer self-contained: CSS, JS and data inside the file, images as data URIs. External resources do load — CDN scripts, remote fonts, images by URL, cross-origin `fetch` all work — so this is a recommendation and not a limit the service imposes. An artifact is a frozen copy meant to open weeks after the link went out, and a CDN that moves takes the page with it, a network that blocks the host renders it wrong, and every open tells whoever serves the asset who is reading.

The isolated origin (`sandbox allow-scripts`, no `allow-same-origin`) is what keeps a published document away from this service's own origin and session. Its cost is anything tied to an origin: `localStorage`, `sessionStorage` and cookies are unavailable, so a page cannot remember state between visits. The document's own JavaScript runs normally — charts, filters, sorting, canvas, blob downloads.

Give it a real `<title>`. It becomes the name in the listing and in the browser tab, so `index` or `report` makes the artifact unfindable later. Whoever published can fix it afterwards by clicking the title in the top bar.
