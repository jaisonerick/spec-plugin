#!/usr/bin/env node
// theme.mjs — the theme toolkit for html-report. No dependencies, Node 18+.
//
//   node theme.mjs extract <report.html>        pull the theme block out of a report
//   node theme.mjs check   <report.html>        check the theme block in a report
//   node theme.mjs check   "#hex,#hex,…"        check a candidate series palette
//   node theme.mjs ramp    "#hex,#hex,…"        check a sequential ramp, report --on-flip
//   node theme.mjs derive  --brand #hex [--ink #hex] [--surface #fff]
//                                               propose a full theme block
//
// What it computes exactly: WCAG contrast, OKLab lightness and chroma, OKLab ΔE
// between adjacent slots, ramp monotonicity, and the ramp's text-flip index.
// What it does NOT compute: colour-vision-deficiency simulation. For that, and for
// chart-form guidance, use the `dataviz` skill. The checks here are the ones that
// catch the failures seen most often: unreadable text and a saturated ramp.

import fs from 'node:fs';

const A = process.argv.slice(2);
const cmd = A[0];

/* ---------- colour ---------- */
const hex2rgb = (h) => {
  const s = h.replace('#', '').trim();
  const f = s.length === 3 ? s.split('').map((c) => c + c).join('') : s;
  return [0, 2, 4].map((i) => parseInt(f.slice(i, i + 2), 16) / 255);
};
const toLinear = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const toSrgb = (c) => (c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055);

const relLum = (h) => {
  const [r, g, b] = hex2rgb(h).map(toLinear);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const contrast = (a, b) => {
  const [x, y] = [relLum(a), relLum(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
};

// Ottosson's OKLab. Perceptual lightness and chroma; ΔE here is plain OKLab distance.
const oklab = (h) => {
  const [r, g, b] = hex2rgb(h).map(toLinear);
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return {
    L: 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
    a: 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
    b: 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s,
  };
};
const chroma = (h) => { const c = oklab(h); return Math.hypot(c.a, c.b); };
const deltaE = (p, q) => {
  const x = oklab(p), y = oklab(q);
  return Math.hypot(x.L - y.L, x.a - y.a, x.b - y.b) * 100;
};

// Move a colour along its own hue until it clears a contrast target on `surface`.
const rgb2hex = (r, g, b) =>
  '#' + [r, g, b].map((c) => Math.round(Math.min(1, Math.max(0, c)) * 255)
    .toString(16).padStart(2, '0')).join('');
const oklab2hex = ({ L, a, b }) => {
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3;
  return rgb2hex(
    toSrgb(+4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
    toSrgb(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
    toSrgb(-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s));
};
// Search lightness along the colour's own hue until it hits a contrast target.
// Must move in BOTH directions: a colour already above the target has to be
// lightened toward it, not darkened, or every role collapses onto the same hex.
const ajustarPara = (h, alvo, surface = '#ffffff', escalaCroma = 1) => {
  const c = oklab(h);
  const a = c.a * escalaCroma, b = c.b * escalaCroma;
  let lo = 0.02, hi = 0.99, melhor = oklab2hex({ L: c.L, a, b });
  // Contrast against a light surface decreases monotonically with L, so bisect.
  for (let i = 0; i < 40; i++) {
    const L = (lo + hi) / 2;
    const cor = oklab2hex({ L, a, b });
    melhor = cor;
    if (contrast(cor, surface) > alvo) lo = L; else hi = L;
  }
  return melhor;
};

/* ---------- theme block I/O ---------- */
const RE = /\/\*\s*THEME\s*\*\/([\s\S]*?)\/\*\s*\/THEME\s*\*\//;

/* ---------- checks ---------- */
const BANDA = [0.43, 0.77];   // categorical slots on a light surface
const CROMA_MIN = 0.10;       // below this a "colour" reads gray
const DE_MIN = 15;            // adjacent slots, normal vision

function ok(cond) { return cond ? 'PASS' : 'FAIL'; }
// An unfilled slot must FAIL loudly: `oklab('?')` yields NaN and every comparison
// against NaN is false, so without this a half-written theme reports OK.
const ehHex = (v) => typeof v === 'string' && /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(v.trim());
function invalidos(rot, cores) {
  const maus = cores.filter((c) => !ehHex(c));
  if (maus.length) linha(rot, 'FAIL', 'não é cor: ' + maus.join(', ') +
    ' — preencha o slot antes de conferir');
  return maus.length > 0;
}
function linha(rot, estado, detalhe) {
  console.log(`  [${estado}] ${rot.padEnd(22)} ${detalhe}`);
}

function checarSeries(cores, surface) {
  console.log(`\nSéries (${cores.length} slots, superfície ${surface})`);
  if (invalidos('Slots preenchidos', cores)) return false;
  let falhou = false;

  const fora = cores.filter((c) => { const L = oklab(c).L; return L < BANDA[0] || L > BANDA[1]; });
  falhou ||= fora.length > 0;
  linha('Banda de luminosidade', ok(!fora.length), fora.length
    ? `fora de L ${BANDA[0]}–${BANDA[1]}: ` + fora.map((c) => `${c} ${oklab(c).L.toFixed(3)}`).join(', ')
    : `todas dentro de L ${BANDA[0]}–${BANDA[1]}`);

  const cinza = cores.filter((c) => chroma(c) < CROMA_MIN);
  falhou ||= cinza.length > 0;
  linha('Piso de croma', ok(!cinza.length), cinza.length
    ? 'lê como cinza: ' + cinza.map((c) => `${c} ${chroma(c).toFixed(3)}`).join(', ')
    : `todas >= ${CROMA_MIN}`);

  let pior = { d: Infinity };
  for (let i = 1; i < cores.length; i++) {
    const d = deltaE(cores[i - 1], cores[i]);
    if (d < pior.d) pior = { d, par: `${cores[i - 1]}↔${cores[i]}` };
  }
  if (cores.length > 1) {
    falhou ||= pior.d < DE_MIN;
    linha('Separação adjacente', ok(pior.d >= DE_MIN),
      `pior par ${pior.par} ΔE ${pior.d.toFixed(1)}` + (pior.d < DE_MIN ? ` (piso ${DE_MIN})` : ''));
  }

  const fracas = cores.filter((c) => contrast(c, surface) < 3);
  linha('Contraste na superfície', fracas.length ? 'WARN' : 'PASS', fracas.length
    ? 'abaixo de 3:1, exige rótulo visível ou tabela: ' +
      fracas.map((c) => `${c} ${contrast(c, surface).toFixed(2)}`).join(', ')
    : 'todas >= 3:1');

  return !falhou;
}

function checarRampa(cores, surface, escura, clara) {
  console.log(`\nRampa sequencial (${cores.length} passos)`);
  if (invalidos('Passos preenchidos', cores)) return false;
  let anterior = Infinity, monot = true;
  cores.forEach((c) => { const L = oklab(c).L; if (L >= anterior) monot = false; anterior = L; });
  linha('Luminosidade monotônica', ok(monot), monot
    ? 'decresce em todos os passos' : 'um passo não é mais escuro que o anterior');

  let flip = null;
  cores.forEach((c, i) => {
    const venceClara = contrast(c, clara) > contrast(c, escura);
    if (venceClara && flip === null) flip = i;
  });
  console.log(`  --on-flip: ${flip ?? cores.length}   (primeiro passo em que a tinta clara vence)`);
  cores.forEach((c, i) => {
    const e = contrast(c, escura), l = contrast(c, clara);
    console.log(`    h${i} ${c}  L ${oklab(c).L.toFixed(3)}  tinta escura ${e.toFixed(2)} | clara ${l.toFixed(2)}` +
      `  -> ${l > e ? 'clara' : 'escura'}`);
  });
  return monot;
}

function checarTintas(vars, surface) {
  console.log(`\nTintas de texto (superfície ${surface})`);
  const alvos = { '--ink': 7, '--muted': 6, '--faint': 4.5, '--accent': 4.5, '--brand': 3 };
  let falhou = false;
  for (const [nome, alvo] of Object.entries(alvos)) {
    const cor = vars[nome];
    if (!cor) continue;
    if (!ehHex(cor)) { linha(nome, 'FAIL', `${cor} — não é cor`); falhou = true; continue; }
    const c = contrast(cor, surface);
    const passou = c >= alvo;
    falhou ||= !passou;
    linha(nome, ok(passou), `${cor}  ${c.toFixed(2)}:1  (mínimo ${alvo})`);
  }
  if (vars['--brand'] && vars['--accent'] && vars['--brand'] === vars['--accent']
      && contrast(vars['--brand'], surface) < 4.5) {
    console.log('  [WARN] --accent  a cor da marca está servindo de texto pequeno abaixo de 4,5:1;' +
      ' escureça-a para o accent e mantenha a original em --brand');
  }
  return !falhou;
}

/* ---------- parsing ---------- */
function varsDoBloco(bloco) {
  const out = {};
  for (const m of bloco.matchAll(/(--[a-z0-9-]+)\s*:\s*([^;]+);/gi)) out[m[1]] = m[2].trim();
  return out;
}
const listaSeries = (v) => Object.keys(v).filter((k) => /^--c\d+$/.test(k))
  .sort((a, b) => +a.slice(3) - +b.slice(3)).map((k) => v[k]);
const listaRampa = (v) => Object.keys(v).filter((k) => /^--h\d+$/.test(k))
  .sort((a, b) => +a.slice(3) - +b.slice(3)).map((k) => v[k]);

/* ---------- commands ---------- */
function lerArquivo(p) { return fs.readFileSync(p, 'utf8'); }

function cmdExtract(caminho) {
  const m = lerArquivo(caminho).match(RE);
  if (!m) {
    console.error(`Nenhum bloco /* THEME */ … /* /THEME */ em ${caminho}.\n` +
      'O arquivo não foi escrito por esta skill, ou os delimitadores sumiram.');
    process.exit(1);
  }
  console.log('/* THEME */' + m[1] + '/* /THEME */');
}

function cmdCheck(alvo) {
  let vars, surface = '#ffffff';
  if (alvo.includes('#') && !fs.existsSync(alvo)) {
    const cores = alvo.split(',').map((s) => s.trim()).filter(Boolean);
    const i = A.indexOf('--surface');
    if (i > -1) surface = A[i + 1];
    process.exit(checarSeries(cores, surface) ? 0 : 1);
  }
  const m = lerArquivo(alvo).match(RE);
  if (!m) { console.error(`Sem bloco de tema em ${alvo}.`); process.exit(1); }
  vars = varsDoBloco(m[1]);
  surface = vars['--bg'] || '#ffffff';
  const series = listaSeries(vars), rampa = listaRampa(vars);
  console.log(`Tema de ${alvo}`);
  let bom = checarTintas(vars, surface);
  if (series.length) bom = checarSeries(series, surface) && bom;
  if (rampa.length) {
    const okr = checarRampa(rampa, surface, vars['--on-lo'] || vars['--ink'], vars['--on-hi'] || '#ffffff');
    bom = okr && bom;
    const declarado = vars['--on-flip'];
    if (declarado !== undefined) {
      let real = rampa.length;
      rampa.forEach((c, i) => {
        const venceClara = contrast(c, vars['--on-hi'] || '#ffffff') > contrast(c, vars['--on-lo'] || vars['--ink']);
        if (venceClara && real === rampa.length) real = i;
      });
      if (+declarado !== real) {
        console.log(`\n  [FAIL] --on-flip           declarado ${declarado}, medido ${real}`);
        bom = false;
      }
    }
  }
  console.log(bom ? '\n→ tema OK' : '\n→ corrija o que está marcado');
  process.exit(bom ? 0 : 1);
}

function cmdRamp(lista) {
  const cores = lista.split(',').map((s) => s.trim()).filter(Boolean);
  const i = A.indexOf('--on-lo'), j = A.indexOf('--on-hi');
  checarRampa(cores, '#ffffff', i > -1 ? A[i + 1] : '#111111', j > -1 ? A[j + 1] : '#ffffff');
}

function cmdDerive() {
  const arg = (n, d) => { const i = A.indexOf(n); return i > -1 ? A[i + 1] : d; };
  const brand = arg('--brand');
  if (!brand) { console.error('uso: derive --brand #hex [--ink #hex] [--surface #ffffff]'); process.exit(1); }
  const surface = arg('--surface', '#ffffff');

  // Ink and the greys are the brand hue held at low chroma, so the page feels like the
  // brand without any of them competing with a data series for attention.
  const ink = arg('--ink') || ajustarPara(brand, 13, surface, 0.18);
  const muted = ajustarPara(ink, 6.5, surface, 1);
  const faint = ajustarPara(ink, 5.0, surface, 1);
  // The brand hex stays for fills; small text needs a darker step of the same hue.
  const accent = contrast(brand, surface) >= 4.5 ? brand : ajustarPara(brand, 4.6, surface, 1);

  // Sequential ramp: one hue, near-surface to the ink, chroma rising then settling.
  const bl = oklab(brand), il = oklab(ink);
  const rampa = Array.from({ length: 7 }, (_, i) => {
    if (i === 6) return ink;
    const t = i / 6;
    const L = 0.94 - t * (0.94 - il.L);
    const k = Math.sin(Math.PI * t * 0.75) * 0.9 + 0.15;   // fade the chroma toward the ink
    return oklab2hex({ L, a: bl.a * k, b: bl.b * k });
  });
  let flip = rampa.length;
  rampa.forEach((c, i) => {
    if (flip === rampa.length && contrast(c, '#ffffff') > contrast(c, ink)) flip = i;
  });

  console.log(`/* THEME */
:root{
  color-scheme: light;
  --ink:${ink}; --muted:${muted}; --faint:${faint};
  --bg:${surface}; --panel:#f5f6f8; --line:#e3e6ea;
  --accent:${accent}; --brand:${brand};
  --pos:#0ca30c; --neg:#d03b3b; --warn:#b26a00;
  --c1:${accent}; --c2:?; --c3:?; --c4:?; --c5:?; --c6:?;
  ${rampa.map((c, i) => `--h${i}:${c};`).join(' ')}
  --on-lo:${ink}; --on-hi:#ffffff; --on-flip:${flip};
}
/* /THEME */`);
  console.log(`
Falta escolher --c2..--c6: hues que se separem de --c1. Proponha e rode
  node theme.mjs check "${accent},#hex,#hex,…"
até passar, e note que a ordem dos slots é o mecanismo: as mesmas cores em outra
ordem podem reprovar. Depois cole o bloco no relatório e rode
  node theme.mjs check <relatorio.html>`);
}

switch (cmd) {
  case 'extract': cmdExtract(A[1]); break;
  case 'check':   cmdCheck(A[1]); break;
  case 'ramp':    cmdRamp(A[1]); break;
  case 'derive':  cmdDerive(); break;
  default:
    console.log(`theme.mjs — ferramenta de tema do html-report

  extract <report.html>              extrai o bloco /* THEME */ de um relatório
  check   <report.html>              confere o tema de um relatório inteiro
  check   "#hex,#hex,…" [--surface]  confere uma paleta de séries candidata
  ramp    "#hex,…" [--on-lo] [--on-hi]  confere uma rampa e mede o --on-flip
  derive  --brand #hex [--ink] [--surface]   propõe um bloco a partir da marca

Não simula daltonismo: para isso, e para escolha de forma de gráfico, use a skill dataviz.`);
}
