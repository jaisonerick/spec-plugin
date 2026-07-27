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

Self-contained: CSS, JS and data inside the file. The service serves documents from an isolated origin (`sandbox allow-scripts`, no `allow-same-origin`), so the document's own JavaScript runs — charts, filters, sorting — while nothing external loads. CDN scripts, remote fonts and images by URL will not appear; embed images as data URIs.

Give it a real `<title>`. It becomes the name in the listing and in the browser tab, so `index` or `report` makes the artifact unfindable later. Whoever published can fix it afterwards by clicking the title in the top bar.
