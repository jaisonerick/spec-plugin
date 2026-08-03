# Themes: one structure, any brand

A theme is **only what sits between the `/* THEME */` and `/* /THEME */` markers** in the report's `<style>`. Layout, type scale, spacing and chart geometry are identical across every theme — two reports for two different organisations are recognisably the same object wearing different colors.

The markers are a contract, not decoration. Keep them bare, with no text on the marker lines, because `theme.mjs` reads the block back out of any report built this way.

**Charts read tokens, never hexes.** `token('--c1')`, not `'#2a78d6'`. If swapping a theme requires touching chart code, the theme is broken.

## The token contract

| Token | Role | Constraint |
|---|---|---|
| `--ink` | body and headings | ≥ 7:1 on `--bg` |
| `--muted` | subtitles, secondary prose | ≥ 6:1 |
| `--faint` | meta lines, tile captions, axis labels | ≥ 4.5:1 — this is small text |
| `--bg` `--panel` `--line` | surface, raised block, hairline | panel and line only need to be visible |
| `--accent` | small bold text: eyebrow, links, sort arrows | **≥ 4.5:1** |
| `--brand` | brand fills, rules, marks — never small text | ≥ 3:1 |
| `--pos` `--neg` `--warn` | status only, never a series | ship with a label, never color alone |
| `--c1`…`--c6` | categorical series, fixed order | validated as a set |
| `--h0`…`--h6` | sequential ramp, light → dark | lightness strictly monotonic |
| `--on-lo` `--on-hi` | text over the low / high end of the ramp | whichever wins contrast |
| `--on-flip` | first ramp index that uses `--on-hi` | measured per ramp, never guessed |

## Getting a theme, in order of preference

### 1. Extract it from a report that already has it

If any report was built with this skill, its theme is reusable verbatim. This is the normal path once an organisation has one report.

```
node ${CLAUDE_PLUGIN_ROOT}/skills/html-report/scripts/theme.mjs extract caminho/relatorio-antigo.html
```

Paste the printed block between the markers in the new report. Nothing else changes.

This also works on a report someone sent you, on a published artifact you saved locally, and on a themed shell kept in a project repo. If it has the markers, it is a theme source.

### 2. Derive it from the brand

For a new organisation, start from the brand's primary color:

```
node .../theme.mjs derive --brand "#E4572E"
node .../theme.mjs derive --brand "#E4572E" --ink "#101820" --surface "#ffffff"
```

It proposes ink, greys, accent and the full sequential ramp, and it measures `--on-flip`. It leaves `--c2`…`--c6` as `?` on purpose: picking hues that separate is a judgement call, not arithmetic. Fill them, then validate.

**Finding the real hexes.** Brand documents rarely state them; the assets do. Read the `fill` in a logo SVG, sample a corner pixel of a dark-background logo PNG, or pull the CSS custom properties off the organisation's site. Do not eyedrop from a screenshot — compression shifts the value.

### 3. Use the neutral default

`assets/skeleton.html` ships with an unbranded theme that passes every check. It is a legitimate answer for an internal report that belongs to no brand. It is not a fallback to leave in place for a client deliverable.

## Validating

```
node .../theme.mjs check relatorio.html        # the whole theme, in place
node .../theme.mjs check "#hex,#hex,#hex"      # a candidate series palette
node .../theme.mjs ramp  "#hex,…"              # a ramp, and its measured --on-flip
```

`check` verifies the ink contrasts, the series (lightness band, chroma floor, adjacent separation, surface contrast), the ramp's monotonicity, and that a declared `--on-flip` matches the measured one. It exits non-zero on failure, so it fits a build step.

It does **not** simulate colour-vision deficiency. For that, and for choosing a chart form, use the `dataviz` skill, whose validator adds CVD separation checks. Run it whenever you invent a new series palette; the checks here catch the failures that occur most often, not all of them.

## The three rules that generalise

**The brand color is usually not the text accent.** A hue tuned for a logo tends to land near 3:1 on white: fine for a filled mark, illegible for a 12px uppercase eyebrow. The pattern that works is `--brand` holding the brand hex and `--accent` holding a darker step of the same hue that clears 4.5:1. `derive` does this automatically and tells you when it had to.

**`--on-flip` is a property of the ramp, not a constant.** The step where light text starts winning depends on where the ramp's lightness falls, and two ramps built the same way land on different numbers. Measure it, put it in the theme, and read it in the chart:

```js
const flip = parseInt(token('--on-flip'), 10);
const tinta = (i) => i >= flip ? token('--on-hi') : token('--on-lo');
```

**Slot order is the mechanism, not decoration.** Separation is checked between *adjacent* slots, so the same six colors in a different order can pass or fail. When a palette fails, try reorderings before reaching for new hues.

## Dark mode

The default is light only, and that is a decision rather than an omission: reports are read and printed on white, and a dark variant means a second set of steps validated against a second surface.

**A dark theme is chosen and validated, never an automatic inversion.** Flipping a light palette reliably produces adjacent series that are indistinguishable — the failure looks fine to whoever built it and is invisible to everyone else until someone measures. If a dark variant is genuinely needed, write a second block guarded by both `@media (prefers-color-scheme: dark)` and a `[data-theme="dark"]` scope, and run `check` against the dark surface.
