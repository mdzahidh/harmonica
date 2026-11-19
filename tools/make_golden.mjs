// Writes golden/*.json from the reference implementation (reference/book_widgets.js).
// Run: node tools/make_golden.mjs        The new app must reproduce these numbers (tests/check.mjs).
import { createRequire } from 'module';
import { writeFileSync } from 'fs';
const require = createRequire(import.meta.url);
const CD = require('../reference/book_widgets.js');
const r4 = x => Math.round(x * 1e4) / 1e4;
const KINDS = ['', 'm', '°'];

// 1. every ordered pair of triads (36 x 36): VL, TD pure, TD 12-TET
const pairs = {};
for (let r1 = 0; r1 < 12; r1++) for (const k1 of KINDS) for (let r2 = 0; r2 < 12; r2++) for (const k2 of KINDS) {
  const X = CD.chord(r1, k1), Y = CD.chord(r2, k2);
  pairs[`${r1}|${k1}>${r2}|${k2}`] = { vl: CD.vl(X, Y).total, td: r4(CD.td(X, Y).total), td12: r4(CD.td12(X, Y).total) };
}

// 2. the neighbourhood of each of the 24 home triads (what the map colours and labels)
const hoods = {};
for (let r = 0; r < 12; r++) for (const k of ['', 'm']) hoods[`${r}|${k}`] = CD.neighbourhood(r, k).map(x => ({
  chord: x.chord, alt: x.alt, root: x.root, kind: x.kind, order: x.order, numeral: x.key, home: x.home,
  place: x.place, shared: x.shared, vl: x.vl, td: r4(x.td), td12: r4(x.td12), tdKey: r4(x.tdKey), group: x.group,
  vlMoves: x.vlMoves.map(m => `${m.from}>${m.to}:${m.cost}`), tdMoves: x.tdMoves.map(m => `${m.from}>${m.to}:${m.limit}`) }));

// 3. the drawn map for each home (scope 3 = everything): the non-DOM half of neighbourMap() in book_widgets.js
const id = p => p[0] + ',' + p[1];
const maps = {};
for (let r0 = 0; r0 < 12; r0++) for (const k0 of ['', 'm']) {
  const rows = CD.neighbourhood(r0, k0), tris = rows.filter(r => r.place[0] !== 'dim');
  const homePts = new Set(CD.chord(r0, k0).map(id));
  const allp = tris.flatMap(r => CD.tri(...r.place));
  const b0 = Math.min(...allp.map(p => p[1])), b1 = Math.max(...allp.map(p => p[1]));
  const X0 = Math.min(...allp.map(p => CD.xy(p)[0])) - 0.2, X1 = Math.max(...allp.map(p => CD.xy(p)[0])) + 0.2;
  const pts = [], has = new Set();
  for (let b = b0; b <= b1; b++) for (let a = -30; a <= 30; a++) { const x = CD.xy([a, b])[0]; if (x >= X0 && x <= X1) { pts.push([a, b]); has.add(id([a, b])); } }
  const byId = new Map(tris.map(r => [`${r.root}|${r.kind}`, r]));
  const T = CD.tile(rows), shown = [];
  for (let b = b0 - 1; b <= b1; b++) for (let a = -30; a <= 30; a++) ['up', 'dn'].forEach(k => {
    const q = CD.tri(k, a, b);
    if (!q.every(p => has.has(id(p)))) return;
    const r = byId.get(`${CD.fret(q[0])}|${k === 'up' ? '' : 'm'}`);
    if (r) shown.push({ chord: r.chord, names: CD.names(CD.tri(k, a, b)[0]).map(n => n + r.kind), numeral: r.key, order: r.order,
      place: [k, a, b], home: r.home, star: r.home && q.every(p => homePts.has(id(p))), faded: !T.has([k, a, b].join(',')),
      label: r.home ? 'home' : `${r.vl} | ${r.td12.toFixed(1)}` });
  });
  const v7 = rows.find(r => r.place[0] === 'dim'), [, va, vb] = v7.place;
  const used = new Set([...shown.filter(r => !r.faded).flatMap(r => CD.tri(...r.place).map(id)), ...[0, 1, 2].map(i => id([va + i, vb - i]))]);
  const [ah, bh] = CD.chord(r0, k0)[0], fa = p => CD.fret(p);
  const notes = pts.map(([a, b]) => { const f = CD.fret([a - ah, b - bh]);
    return { a, b, xy: CD.xy([a, b]).map(r4), names: CD.names([a, b]).map(n => `${n} (${CD.degreeOf(n, fa([a, b]), r0, k0)})`),
      vl: Math.min(f, 12 - f), td12: r4(CD.pcTD(f)), used: used.has(id([a, b])), root: a === ah && b === bh,
      tritoneEnd: id([a, b]) === id([va, vb]) || id([a, b]) === id([va + 2, vb - 2]) }; });
  maps[`${r0}|${k0}`] = { name: CD.name(r0, k0), rows: [b0, b1], window: [r4(X0), r4(X1)], triangles: shown, notes,
    tritone: { chord: `${v7.chord} (${v7.key})`, chain: [0, 1, 2].map(i => [va + i, vb - i]), ends: [CD.spell(va, vb), CD.spell(va + 2, vb - 2)] } };
}

writeFileSync('golden/pairs.json', JSON.stringify(pairs));
writeFileSync('golden/neighbourhoods.json', JSON.stringify(hoods, null, 1));
writeFileSync('golden/maps.json', JSON.stringify(maps));
writeFileSync('golden/constants.json', JSON.stringify({ etdFret: CD.PALETTE.etdFret, palette: CD.PALETTE }, null, 1));
console.log('pairs', Object.keys(pairs).length, '· homes', Object.keys(hoods).length, '· C map triangles', maps['0|'].triangles.length, 'notes', maps['0|'].notes.length);
