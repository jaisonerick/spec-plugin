# Structure: the document, the data, self-containment

## The skeleton

Copy `assets/skeleton.html`. It is the whole contract: a theme block, ~20 classes, and four JS helpers (`F` for pt-BR formatting, `n` for SVG nodes, `TIP` for the shared hover layer, `token` for reading theme colors). Everything else you write per report.

It is deliberately not a chart library. A chart written for its data beats a generic one configured into shape, and the snippets in `charts.md` are shorter than the configuration would be.

## Self-containment

The file has to render with no network, from `file://` and from inside `<iframe sandbox="allow-scripts">`.

- CSS and JS inline. No `<link>`, no `<script src>`, no CDN, no Google Fonts.
- System font stack only. A remote font silently falls back and the layout shifts.
- Images as `data:` URIs. An `<img src="https://…">` renders as a broken icon in the sandbox.
- No `fetch`, no `localStorage` reads you depend on. Sandboxed origins may deny storage.

Test the real thing: open the file, not the source, and check the console.

## Embedding the data

```js
const DATA = { curva: [...], safras: [...] };
```

Three things break here, all quiet:

- **`NaN` is not JSON.** `json.dumps` writes it as the bare literal `NaN`, which is a syntax error in a `<script>` and, when it survives a different serializer, renders as the string "NaN" in a cell. Convert to `null` before serializing.
- **`</` closes the tag.** Any string in your data containing `</` (a stray `</div>`, a regex) ends the script block. Replace `</` with `<\/` in the serialized JSON — it is identical to the JS parser.
- **Dates and Decimals are not JSON either.** Emit ISO strings and floats.

Python side, the whole of it:

```python
import json, math

def registros(df):
    """Real nulls, not NaN, and no numpy scalars."""
    return [{k: (None if isinstance(v, float) and math.isnan(v) else v)
             for k, v in linha.items()} for linha in df.to_dict(orient="records")]

payload = json.dumps({"curva": registros(df)}, default=str, ensure_ascii=False,
                     separators=(",", ":")).replace("</", "<\\/")
```

## How much data

**Aggregate before embedding.** The reader needs the series the charts draw and the rows the table shows, not the row-level detail behind them.

Past roughly **5 MB of JSON** the browser stalls on parse and the file stops being pleasant to open. If you are near it, aggregate harder, cut the table to the rows that matter with a note saying what was cut, or accept that this is a local app and not a report.

A useful check: if the table would have more than a few thousand rows, nobody is reading it — they want a filter, a different grain, or a query.

## Head matter

- **`<title>`**: what the report answers plus the scope. `Retenção por safra · out/2023 a jul/2026`. Never "report", never "index", never the file name. It becomes the tab, the listing entry and how the link is referred to.
- **Eyebrow**: organisation and subject, e.g. `Acme · Carteira de crédito`.
- **`.meta` line**: when it was generated, the source, and the data's own as-of date. These are three different dates and the reader needs the last one most.
- **Footer**: confidentiality and where the field semantics live.

## Parameterizing

If the report is generated from a script, keep the HTML as one template string and the numbers as variables. Do not build prose by concatenating fragments in a loop — the prose is the part a human rereads, and it should be legible in the source.

Compute every number that appears in prose, never type it:

```python
f"No MOB 12 sobram {num(em(12, 'logo'), 0)}% dos merchants"
```

A hardcoded number in prose rots on the next run and nothing warns you. This is the single most common way a report ends up self-contradicting: the chart updates, the sentence does not.
