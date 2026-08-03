# html-report

Turns finished analysis results into one self-contained HTML file: charts, cohort heatmaps, sortable tables and stat tiles, with the CSS, the JavaScript and the data inline. It opens by double-click, works with no network, and survives being served from a sandboxed iframe — which is how most artifact hosts serve it.

It handles the **visual layer only**. You bring numbers that are already correct and a message that is already decided; the skill decides the form, the theme and the markup. It does not query anything and it does not decide what is true.

## Install

```
/plugin marketplace add nexaedge-marketplace --source github --repo nexaedge/nexaedge-marketplace
/plugin install html-report@nexaedge-marketplace
```

## Use

Ask for a report and hand over the material:

> Monta o relatório disso. Os números estão em `resultado.json`, a mensagem é que a base instalada carrega o volume, e é para o time de crédito.

The skill asks for whatever it still needs — who reads it, whose brand it wears — then writes the file.

## Themes

The plugin ships **no brand**. A theme is only what sits between the `/* THEME */` and `/* /THEME */` markers in the report's stylesheet, and there are three ways to get one:

**Lift it from an earlier report.** Any report built with this skill carries its theme in a machine-readable block:

```
node theme.mjs extract relatorio-anterior.html
```

Point the skill at a previous file and the new report matches it exactly. This is the normal path once an organisation has one report.

**Derive it from a brand color.** For a new organisation:

```
node theme.mjs derive --brand "#E4572E"
```

It proposes the ink, the greys, the text accent and the full sequential ramp, and it measures where light text has to take over. It deliberately leaves the categorical series slots empty: picking hues that stay apart is judgement, not arithmetic.

**Use the neutral default.** The base template ships with an unbranded theme that passes every check — fine for an internal report that belongs to no brand.

Either way, check it:

```
node theme.mjs check relatorio.html        # the whole theme, in place
node theme.mjs check "#hex,#hex,#hex"      # a candidate series palette
```

`check` verifies text contrast, the series (lightness band, chroma floor, adjacent separation), ramp monotonicity, and that the declared text-flip index matches the measured one. It exits non-zero on failure, so it fits a build step. It does not simulate colour-vision deficiency; for that, and for choosing a chart form, use the `dataviz` skill.

## What is inside

```
skills/html-report/
  SKILL.md              the procedure and the non-negotiables
  references/
    structure.md        document skeleton, embedding data, self-containment, size limits
    charts.md           which form to pick, the SVG patterns, the traps that cost a rebuild
    themes.md           the token contract, extracting, deriving, validating
    writing.md          section order, headline first, glossing, honesty rules
  assets/skeleton.html  the base file to copy
  scripts/theme.mjs     extract / derive / check, no dependencies, Node 18+
```

There is no chart library and no generator. The references carry short snippets for the parts that are genuinely reusable — the chart frame, the hover layer, the stacked bar, the heatmap, the sortable table — and the skill writes the rest for the data at hand.

## Composes with

- **`dataviz`** for chart-form guidance and a palette validator that also simulates colour-vision deficiency.
- **`artifact-publish`** for turning the file into a shareable link.
