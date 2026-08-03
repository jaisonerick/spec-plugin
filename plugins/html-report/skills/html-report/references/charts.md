# Charts: which form, the patterns, the traps

## Pick the form from the job

| The data's job | Form |
|---|---|
| One number that is the headline | Stat tile. Not a chart. |
| Compare magnitude across categories | Horizontal bars, sorted by value |
| Composition of a total over time | Stacked bars, one bar per period |
| Change over time, few series | Lines with markers |
| Two dimensions, one value | Heatmap (cohort × period is the common case) |
| Everything else the reader may want to cross | Sortable table |

Two rules that decide most cases:

- **A chart with three numbers is a sentence.** Write the sentence.
- **A table beats ten rows you picked.** If you find yourself choosing which rows to show, ship the table and let the reader choose.

Color comes last, and it comes from the theme tokens. If you are reaching for a hue that is not `--c1..--c6`, you are either drawing too many series (fold the tail into "Outros") or you want a sequential ramp (`--h0..--h6`), not a categorical one.

## The frame

Every chart starts the same way: a viewBox, four paddings, two scale functions, a grid.

```js
const w = 900, h = 330, padL = 54, padR = 132, padT = 16, padB = 42;
const px = (v) => padL + ((v - x0) / (x1 - x0)) * (w - padL - padR);
const py = (v) => padT + (1 - v / maxY) * (h - padT - padB);
const svg = n('svg', {viewBox: `0 0 ${w} ${h}`, role: 'img', 'aria-label': 'o que o gráfico mostra'});

for (let i = 0; i <= 4; i++) {                       // 4 gridlines is plenty
  const v = maxY * (1 - i / 4), y = py(v);
  svg.append(
    n('line', {x1: padL, x2: w - padR, y1: y, y2: y, class: 'grid-line'}),
    n('text', {x: padL - 10, y: y + 4, 'text-anchor': 'end'}, rotulo(v)));
}
```

`padR` is generous on purpose: it is where the direct labels live. The SVG is `width:100%;height:auto`, so it scales; never set pixel width on the element.

**Axis tick labels: do not `Math.round`.** On a scale that is not a multiple of 4 it prints duplicates — a 0 to 2.5 axis becomes `3× 2× 1× 1× 0×` and looks broken. Format for the scale you have.

## Lines

```js
series.forEach(s => {
  const pts = rows.filter(r => r[s.k] != null);
  svg.appendChild(n('path', {
    d: pts.map((r, i) => `${i ? 'L' : 'M'}${px(r.x).toFixed(1)},${py(r[s.k]).toFixed(1)}`).join(' '),
    fill: 'none', stroke: s.cor, 'stroke-width': 2,
    'stroke-linejoin': 'round', 'stroke-linecap': 'round',
    'stroke-dasharray': s.tracejada ? '5 4' : 'none'}));
  // A 2px ring in the surface color so overlapping markers stay countable.
  pts.forEach(r => svg.appendChild(n('circle', {cx: px(r.x), cy: py(r[s.k]), r: 4,
    fill: s.cor, stroke: token('--bg'), 'stroke-width': 2})));
});
```

**Direct labels at the line ends, and declutter them.** Two series that end close together overlap, because each label is two stacked lines:

```js
const ALTURA = 34;
fins.sort((a, b) => a.y - b.y);
for (let i = 1; i < fins.length; i++) {
  if (fins[i].y - fins[i - 1].y < ALTURA) fins[i].y = fins[i - 1].y + ALTURA;
}
fins.forEach(f => svg.append(
  // style, NOT a fill attribute — `.chart .val{fill:var(--ink)}` outranks the attribute.
  n('text', {x: f.x, y: f.y + 4, class: 'val', style: `fill:${f.cor}`}, f.texto),
  n('text', {x: f.x, y: f.y + 19, 'font-size': 10}, f.curto)));
```

**Crosshair and tooltip**, one transparent hit rect over the plot area:

```js
const cross = n('line', {y1: padT, y2: h - padB, class: 'grid-line',
  'stroke-width': 1.5, opacity: 0, 'stroke-dasharray': '3 3'});
svg.appendChild(cross);
const hit = n('rect', {x: padL, y: padT, width: w - padL - padR, height: h - padT - padB, fill: 'transparent'});
hit.addEventListener('mousemove', (ev) => {
  const box = svg.getBoundingClientRect();
  const rel = (ev.clientX - box.left) / box.width * w;      // viewBox units, not pixels
  const x = Math.round(x0 + (rel - padL) / (w - padL - padR) * (x1 - x0));
  const r = rows.find(d => d.x === x); if (!r) return;
  cross.setAttribute('x1', px(x)); cross.setAttribute('x2', px(x)); cross.setAttribute('opacity', 1);
  TIP.show(`<b>${rotuloX(x)}</b>` + series.map(s => TIP.row(s.nome, fmt(r[s.k]), s.cor)).join(''), ev);
});
hit.addEventListener('mouseleave', () => { TIP.hide(); cross.setAttribute('opacity', 0); });
svg.appendChild(hit);
```

The tooltip is where the supporting numbers go: the base the percentage came from, how many cohorts are in the point, the absolute value behind the ratio. That is how the chart stays clean and still answers "out of how many?".

**A numeric x axis must be numeric.** Sorting period labels as text turns 2, 3, 10, 11, 12 into 10, 11, 12, 2, 3. Keep the number, format at draw time.

## Stacked bars

```js
rows.forEach((r, i) => {
  const x = padL + i * bw + bw * 0.16, bar = bw * 0.68;
  let acc = 0;
  chaves.forEach((k, j) => {
    const v = r[k] || 0; if (v <= 0) { acc += v; return; }
    const y0 = py(acc), y1 = py(acc + v);
    // 2px surface gap between segments; only the top one gets rounded ends.
    const topo = j === chaves.length - 1;
    const alt = Math.max(1, y0 - y1 - (topo ? 0 : 2));
    svg.appendChild(n('rect', {x, y: y1, width: bar, height: alt, rx: topo ? 4 : 0, fill: cores[j]}));
    acc += v;
  });
  // One hit area per period, full height: hovering a thin segment must not be a game.
  const hit = n('rect', {x: padL + i * bw, y: padT, width: bw, height: h - padT - padB, fill: 'transparent'});
  hit.addEventListener('mousemove', (ev) => TIP.show(tooltipDoMes(r), ev));
  hit.addEventListener('mouseleave', TIP.hide);
  svg.appendChild(hit);
});
```

Stack order carries meaning: put the series whose *change* is the story on top, against the free edge, where its movement is readable. Buried in the middle, a shrinking band is invisible.

Label every other x tick when they crowd, and always the last one.

## Heatmap

The two things that decide whether it is readable:

```js
// 1. Map the ramp over the range the data OCCUPIES, not 0–100. Values that live
//    between 40% and 110% mapped over 0–100 land in the top three steps and the
//    map reads as a wall of one color.
const LO = 20, HI = 110;
const idx = (v) => Math.min(6, Math.max(0, Math.floor((v - LO) / (HI - LO) * 7)));

// 2. Flip the text color by STEP INDEX, not by value: the crossover is a property
//    of the ramp, and it differs between two ramps built the same way.
const flip = parseInt(token('--on-flip'), 10);
const tinta = (i) => i >= flip ? token('--on-hi') : token('--on-lo');
```

```js
svg.appendChild(n('rect', {x: cx + 1, y: cy + 1, width: cw - 2, height: ch - 2, rx: 3,
  fill: ramp[i], opacity: fraca ? 0.5 : 1}));           // 2px gap: cells must not bleed
svg.appendChild(n('text', {x: cx + cw / 2, y: cy + ch / 2 + 4, 'text-anchor': 'middle',
  'font-size': 10, 'font-weight': 600, style: `fill:${tinta(i)}`}, Math.round(v) + '%'));
```

Put the number in the cell. A heatmap without values is a mood, and it also serves as the contrast relief when a ramp step is light.

**Row labels carry the base**: `mai/25 (96)` tells the reader instantly how much to trust the row. Mark the thin ones with an asterisk and fade them, and explain the mark in a note right below.

## Sortable table

The whole thing, once, in ~40 lines. Mount it into an empty `<div>`.

```js
function tabela(sel, rows, cols, opts = {}) {
  const mount = document.querySelector(sel), limite = opts.limite ?? 200;
  let sortKey = opts.sort || null, asc = false, termo = '';
  const tools = document.createElement('div'); tools.className = 'tbl-tools';
  const input = document.createElement('input');
  input.type = 'search'; input.placeholder = opts.placeholder || 'filtrar';
  input.oninput = e => { termo = e.target.value.toLowerCase(); draw(); };
  const count = document.createElement('span');
  tools.append(input, count);
  const scroll = document.createElement('div'); scroll.className = 'tbl-scroll';
  const tbl = document.createElement('table'); scroll.appendChild(tbl);
  mount.append(tools, scroll);

  function draw() {
    let vis = termo
      ? rows.filter(r => cols.some(c => String(r[c.key] ?? '').toLowerCase().includes(termo)))
      : rows;
    if (sortKey) vis = vis.slice().sort((a, b) => {
      const x = a[sortKey], y = b[sortKey];
      if (x == null) return 1; if (y == null) return -1;
      const cmp = typeof x === 'number' && typeof y === 'number'
        ? x - y : String(x).localeCompare(String(y), 'pt-BR');
      return asc ? cmp : -cmp;
    });
    count.textContent = vis.length > limite
      ? `${limite} de ${vis.length} linhas` : `${vis.length} linha(s)`;
    tbl.innerHTML = '';
    const head = tbl.createTHead().insertRow();
    for (const c of cols) {
      const th = document.createElement('th');
      th.textContent = c.label || c.key;
      if (c.key === sortKey) th.className = 'sorted' + (asc ? ' asc' : '');
      th.onclick = () => { asc = c.key === sortKey ? !asc : false; sortKey = c.key; draw(); };
      head.appendChild(th);
    }
    const body = tbl.createTBody();
    for (const r of vis.slice(0, limite)) {
      const tr = body.insertRow();
      for (const c of cols) {
        const raw = r[c.key], td = tr.insertCell();
        td.textContent = c.fmt ? c.fmt(raw, r) : (raw ?? '—');
        td.className = raw == null ? 'null' : (typeof raw === 'number' ? 'num' : '');
      }
    }
  }
  draw();
}
```

Numbers right-aligned with tabular figures (the `num` class does both), nulls visibly empty rather than zero. **A visible row cap is honest; a silent one is not** — the counter says "200 de 1.482 linhas" so nobody reads a truncated table as the whole thing.

## Traps that cost a rebuild

- **The stylesheet beats the SVG attribute.** `.chart text{fill:var(--muted)}` overrides `fill="…"` on a `<text>`. Colored labels need inline `style`. Rects are unaffected — only text has a matching CSS rule.
- **`Math.round` on axis ticks** prints duplicate labels on non-integer scales.
- **End labels collide** when two series finish within ~30px.
- **A ramp mapped over the wrong domain** saturates and hides all the variation.
- **A thin tail turns upward.** When later periods rest on few cohorts, survivorship bends the aggregate up and it reads as recovery. Cut the aggregate where the base thins, keep the detail in the per-cohort view, and say where you cut and why.
- **Emoji and ASCII art are not charts.** No `████` bars, no ⬆️ in a cell.
- **Do not repaint on filter.** A series keeps its color when its neighbours disappear; color follows the entity, never its position in the surviving list.
