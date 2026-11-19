// Writes out/pairs.json, out/neighbourhoods.json and out/maps.json from src/core, in the shapes of
// golden/ (see tools/make_golden.mjs). Then: node tests/check.mjs out
import { mkdirSync, writeFileSync } from 'fs';
import { chord, td, td12, vl, neighbourhood, type Kind } from '../src/core/cd';
import { buildMap } from '../src/core/map';

const r4 = (x: number) => Math.round(x * 1e4) / 1e4;
const KINDS: Kind[] = ['', 'm', '°'];
const HOMES = Array.from({ length: 12 }, (_, r) => (['', 'm'] as const).map(k => [r, k] as const)).flat();

const pairs: Record<string, unknown> = {};
for (let r1 = 0; r1 < 12; r1++) for (const k1 of KINDS) for (let r2 = 0; r2 < 12; r2++) for (const k2 of KINDS) {
  const X = chord(r1, k1), Y = chord(r2, k2);
  pairs[`${r1}|${k1}>${r2}|${k2}`] = { vl: vl(X, Y).total, td: r4(td(X, Y).total), td12: r4(td12(X, Y).total) };
}

const hoods: Record<string, unknown> = {};
for (const [r, k] of HOMES) hoods[`${r}|${k}`] = neighbourhood(r, k).map(x => ({
  chord: x.chord, alt: x.alt, root: x.root, kind: x.kind, order: x.order, numeral: x.key, home: x.home,
  place: x.place, shared: x.shared, vl: x.vl, td: r4(x.td), td12: r4(x.td12), tdKey: r4(x.tdKey), group: x.group,
  vlMoves: x.vlMoves.map(m => `${m.from}>${m.to}:${m.cost}`), tdMoves: x.tdMoves.map(m => `${m.from}>${m.to}:${m.limit}`) }));

const maps: Record<string, unknown> = {};
for (const [r, k] of HOMES) {
  const m = buildMap(r, k);
  maps[`${r}|${k}`] = { name: m.name, rows: m.rows, window: m.window.map(r4),
    triangles: m.triangles.map(({ row, ...t }) => t),
    notes: m.notes.map(n => ({ ...n, xy: n.xy.map(r4), td12: r4(n.td12) })),
    tritone: { chord: m.tritone.chord, chain: m.tritone.chain, ends: m.tritone.ends } };
}

mkdirSync('out', { recursive: true });
writeFileSync('out/pairs.json', JSON.stringify(pairs));
writeFileSync('out/neighbourhoods.json', JSON.stringify(hoods, null, 1));
writeFileSync('out/maps.json', JSON.stringify(maps));
console.log('pairs', Object.keys(pairs).length, '· homes', Object.keys(hoods).length);
