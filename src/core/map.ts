// The drawn map for a home chord (SPEC §6): the non-DOM half of neighbourMap() in reference/book_widgets.js.
// The view renders only what this returns.
import { chord, degreeOf, fret, name, names, neighbourhood, pcTD, spell, tile, tri, xy, type Pt, type Row, type TriKind } from './cd';

export interface MapTriangle {
  chord: string; names: string[]; numeral: string; order: number; place: [TriKind, number, number];
  home: boolean; star: boolean; faded: boolean; label: string; row: Row;
}
export interface MapNote {
  a: number; b: number; xy: Pt; names: string[]; vl: number; td12: number;
  used: boolean; root: boolean; tritoneEnd: boolean;
}
export interface MapModel {
  name: string; rows: [number, number]; window: [number, number];
  triangles: MapTriangle[]; notes: MapNote[];
  tritone: { chord: string; chain: Pt[]; ends: [string, string]; row: Row };
  neighbourhood: Row[];
}

const id = (p: Pt) => p[0] + ',' + p[1];

/** scope: highest order shown (0 = key only … 3 = everything) */
export function buildMap(r0: number, k0: '' | 'm', scope = 3): MapModel {
  const all = neighbourhood(r0, k0), rows = all.filter(r => r.order <= scope);
  const tris = rows.filter(r => r.place[0] !== 'dim');
  const homePts = new Set(chord(r0, k0).map(id));
  const allp = tris.flatMap(r => tri(r.place[0] as TriKind, r.place[1], r.place[2]));
  const b0 = Math.min(...allp.map(p => p[1])), b1 = Math.max(...allp.map(p => p[1]));
  const X0 = Math.min(...allp.map(p => xy(p)[0])) - 0.2, X1 = Math.max(...allp.map(p => xy(p)[0])) + 0.2;
  const pts: Pt[] = [], has = new Set<string>();
  for (let b = b0; b <= b1; b++) for (let a = -30; a <= 30; a++) {
    const x = xy([a, b])[0];
    if (x >= X0 && x <= X1) { pts.push([a, b]); has.add(id([a, b])); }
  }
  const byId = new Map(tris.map(r => [`${r.root}|${r.kind}`, r]));
  const T = tile(all), shown: MapTriangle[] = [];
  for (let b = b0 - 1; b <= b1; b++) for (let a = -30; a <= 30; a++) (['up', 'dn'] as const).forEach(k => {
    const q = tri(k, a, b);
    if (!q.every(p => has.has(id(p)))) return;
    const r = byId.get(`${fret(q[0])}|${k === 'up' ? '' : 'm'}`);
    if (r) shown.push({ chord: r.chord, names: names(q[0]).map(n => n + r.kind), numeral: r.key, order: r.order,
      place: [k, a, b], home: r.home, star: r.home && q.every(p => homePts.has(id(p))), faded: !T.has([k, a, b].join(',')),
      label: r.home ? 'home' : `${r.vl} | ${r.td12.toFixed(1)}`, row: r });
  });
  const v7 = all.find(r => r.place[0] === 'dim')!, [, va, vb] = v7.place;
  const chain: Pt[] = [0, 1, 2].map(i => [va + i, vb - i]);
  const used = new Set([...shown.filter(r => !r.faded).flatMap(r => tri(...r.place).map(id)), ...chain.map(id)]);
  const [ah, bh] = chord(r0, k0)[0];
  const notes: MapNote[] = pts.map(([a, b]) => {
    const f = fret([a - ah, b - bh]);
    return { a, b, xy: xy([a, b]), names: names([a, b]).map(n => `${n} (${degreeOf(n, fret([a, b]), r0, k0)})`),
      vl: Math.min(f, 12 - f), td12: pcTD(f), used: used.has(id([a, b])), root: a === ah && b === bh,
      tritoneEnd: id([a, b]) === id([va, vb]) || id([a, b]) === id([va + 2, vb - 2]) };
  });
  return { name: name(r0, k0), rows: [b0, b1], window: [X0, X1], triangles: shown, notes,
    tritone: { chord: `${v7.chord} (${v7.key})`, chain, ends: [spell(va, vb), spell(va + 2, vb - 2)], row: v7 },
    neighbourhood: rows };
}
