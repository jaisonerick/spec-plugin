---
name: html-report
description: Build a self-contained interactive HTML report from analysis results — charts, cohort matrices, sortable tables, stat tiles, all inline in one file that opens by double-click with no network. Handles the visual layer only: you bring the numbers and the message, this decides the form, the theme and the markup. Use when turning a finished analysis into a deliverable someone else will open, or when asked for a report, dashboard, detalhamento, painel, one-pager or "manda em HTML". Carries no brand of its own: it derives a theme from a brand color, or lifts one verbatim out of a report it built earlier. Triggers "monta o relatório", "gera o HTML", "quero isso em relatório", "build a report", "make this a dashboard", "põe num HTML pra mandar".
---

# html-report — the deliverable, not the analysis

You are given numbers that are already correct and a message that is already decided. Your job is the artifact: one HTML file that a person opens and understands without you in the room.

**This skill does not fetch data, does not run queries and does not decide what is true.** If the numbers are not settled yet, stop and settle them first — a beautiful chart of a wrong number is worse than no chart. If publishing is the next step, that is the `artifact-publish` skill, not this one.

## Input and output

**In:** the numbers (already aggregated), what the report has to say, who reads it, and which organisation it belongs to — plus, if one exists, an earlier report whose theme should carry over.
**Out:** one `.html` file. CSS, JS and data inline. No CDN, no remote font, no image by URL — images go in as data URIs. It has to render from a `file://` double-click and inside a sandboxed iframe, because that is how artifact hosts serve it.

If you were not told who reads it or whose brand it wears, ask. The theme and the amount of glossing both depend on it.

**The skill ships no brand.** Point it at an earlier report and it lifts that theme verbatim; give it a brand color and it derives one; give it neither and it uses a neutral default that passes every check.

## Procedure

1. **Write the message before the markup.** One sentence per section, in order, that a reader could take away. If you cannot write that sentence, the section has no reason to exist. → `references/writing.md`
2. **Pick the form per section from the job the data does.** Magnitude, composition, change over time, identity, a single number. Sometimes the answer is a stat tile or a sentence, not a chart. Never a chart because the section looks empty. → `references/charts.md`
3. **Copy `assets/skeleton.html` and settle the theme.** Extract it from an earlier report if one exists, derive it from the brand color if not. Never edit anything outside the theme block to change a color. → `references/themes.md`
4. **Aggregate, then embed.** The data goes in already reduced to what the charts read. → `references/structure.md`
5. **Build each chart from the snippets**, in the order axis → marks → labels → hover.
6. **Render it and look at it.** Open the file, screenshot it, read the console. The checks below are the ones that have actually broken.

## Non-negotiables

- **The `<title>` is the artifact's name**, not the file name. Write what the report answers, with its scope. A report called "report" cannot be found a month later.
- **Charts read theme tokens, never a hex.** `token('--c1')`, not `'#2a78d6'`. A theme swap that requires touching chart code is a broken theme.
- **One axis.** Two measures of different scale become two charts or get indexed to a common base. Never a second y-scale.
- **Colored SVG text needs `style="fill:…"`.** The stylesheet's `.chart text{fill:var(--muted)}` outranks a `fill` attribute, so an end label set by attribute renders gray. This one is silent and it will happen to you.
- **A legend for two or more series**, plus direct labels at the line ends. One series needs no legend — the title names it.
- **Hover by default** on anything with marks. An HTML chart that does not respond to the pointer is a picture.
- **Never publish a number whose base is too thin without marking it.** Fade it, asterisk it, or cut the series where the base thins out, and say which in a note. A 100% built on three merchants gets quoted back at you.
- **Say the scope in every section.** "45%" is not a finding; "45% do volume, nas safras de 2025, no 12º mês" is.

## References

Load the one you need, when you need it.

| File | What it answers |
|---|---|
| `references/structure.md` | The document skeleton, embedding data, self-containment, size limits |
| `references/charts.md` | Which form, the SVG patterns, the gotchas that cost a rebuild |
| `references/themes.md` | The token contract, extracting a theme, deriving one, validating |
| `references/writing.md` | Section order, headline first, glossing, the two closing sections |
| `assets/skeleton.html` | The base file to copy |
| `scripts/theme.mjs` | Extract, derive, check a theme. Run it; do not eyeball colors. |

## Composing with other skills

- **Choosing a chart form, or inventing a series palette:** the `dataviz` skill carries the method and a validator that also simulates colour-vision deficiency, which `theme.mjs` deliberately does not.
- **Publishing and sharing a link:** the `artifact-publish` skill. Getting the account wrong produces a link the reader cannot open, and it raises no error.
- **The report's prose reads badly after several passes:** the `doc-coherence` skill.
