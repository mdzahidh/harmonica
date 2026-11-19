// CD = chord distance. A typed, DOM-free port of the CD module in reference/book_widgets.js.
// Locked: every number and label here is checked against golden/ by `npm run check`.
import { PALETTE } from './palette';

export type Kind = '' | 'm' | '°';
export type Pt = [number, number];                 // (a, b) = 3^a · 5^b
export type TriKind = 'up' | 'dn';
export type Place = [TriKind | 'dim', number, number];

export const NAMES = ['C', 'C♯', 'D', 'E♭', 'E', 'F', 'F♯', 'G', 'A♭', 'A', 'B♭', 'B'];
export const L3 = Math.log2(3), L5 = Math.log2(5);
const SHAPES: Record<Kind, Pt[]> = { '': [[0, 0], [0, 1], [1, 0]], m: [[0, 0], [1, -1], [1, 0]], '°': [[0, 0], [1, -1], [2, -2]] };
// the key's own chords, by fret above the tonic (natural minor for a minor tonic)
const KEY_STEPS: Record<'' | 'm', [number, Kind, string][]> = {
  '': [[0, '', 'I'], [2, 'm', 'ii'], [4, 'm', 'iii'], [5, '', 'IV'], [7, '', 'V'], [9, 'm', 'vi'], [11, '°', 'vii°']],
  m: [[0, 'm', 'i'], [2, '°', 'ii°'], [3, '', 'III'], [5, 'm', 'iv'], [7, 'm', 'v'], [8, '', 'VI'], [10, '', 'VII']],
};
export const keyOf = (root: number, kind: '' | 'm') =>
  new Map(KEY_STEPS[kind].map(([d, k, rn]) => [`${(root + d) % 12}|${k}`, rn]));
/** root position of each pitch class on the line of fifths (row b = 0) */
export const POS: Record<number, number> = { 0: 0, 7: 1, 2: 2, 9: 3, 4: 4, 11: 5, 6: 6, 1: -5, 8: -4, 3: -3, 10: -2, 5: -1 };
export const mod = (n: number, m: number) => ((n % m) + m) % m;
export const fret = (p: Pt) => mod(7 * p[0] + 4 * p[1], 12);
/** log₂ of the odd limit of 3^k·5^j (Kees height) */
export const kees = (k: number, j: number) => (k * j >= 0 ? Math.abs(k) * L3 + Math.abs(j) * L5
  : Math.max(Math.abs(k) * L3, Math.abs(j) * L5));
export const oddLimit = (k: number, j: number) => {
  const n = 3 ** Math.max(k, 0) * 5 ** Math.max(j, 0);
  const d = 3 ** Math.max(-k, 0) * 5 ** Math.max(-j, 0);
  return Math.max(n, d);
};
const short = (a: number, b: number) => Math.min(mod(a - b, 12), mod(b - a, 12));
const perms = <T>(a: T[]): T[][] => a.length <= 1 ? [a] :
  a.flatMap((x, i) => perms([...a.slice(0, i), ...a.slice(i + 1)]).map(r => [x, ...r]));
export const chord = (root: number, kind: Kind): Pt[] => SHAPES[kind].map(p => [POS[root] + p[0], p[1]]);
export const name = (root: number, kind: Kind) => NAMES[root] + kind;

export interface VLMove { from: string; to: string; cost: number }
export interface VLResult { total: number; pairs: [number, number][]; moves: VLMove[] }
export function vl(X: Pt[], Y: Pt[]): VLResult {
  const fx = X.map(fret);
  let best: { total: number; pairs: [number, number][] } | null = null;
  for (const P of perms(Y.map(fret))) {
    const t = fx.reduce((s, x, i) => s + short(x, P[i]), 0);
    if (!best || t < best.total) best = { total: t, pairs: fx.map((x, i) => [x, P[i]] as [number, number]) };
  }
  const b = best!;
  return { ...b, moves: b.pairs.filter(([a, c]) => a !== c).map(([a, c]) => ({ from: NAMES[a], to: NAMES[c], cost: short(a, c) })) };
}

export interface TDMove { from: string; to: string; fromF: number; toF: number; limit: number; cost: number }
export interface TDResult { total: number; held: number; pairs: [Pt, Pt][]; moves: TDMove[] }
/** pure TD: Y slides rigidly by every 12-TET-neutral (da, db); best pairing, ties → more held notes */
export function td(X: Pt[], Y: Pt[], win = 4): TDResult {
  let best: { total: number; held: number; pairs: [Pt, Pt][] } | null = null;
  for (let da = -12; da <= 12; da++) for (let db = -win; db <= win; db++) {
    if (mod(7 * da + 4 * db, 12)) continue;
    const Yc = Y.map(p => [p[0] + da, p[1] + db] as Pt);
    for (const P of perms(Yc)) {
      let c = 0, held = 0;
      X.forEach((p, i) => {
        c += kees(P[i][0] - p[0], P[i][1] - p[1]);
        held += +(P[i][0] === p[0] && P[i][1] === p[1]);
      });
      if (!best || c < best.total - 1e-9 || (Math.abs(c - best.total) < 1e-9 && held > best.held))
        best = { total: c, held, pairs: X.map((p, i) => [p, P[i]] as [Pt, Pt]) };
    }
  }
  const b = best!;
  return { ...b, moves: b.pairs.filter(([p, q]) => p[0] !== q[0] || p[1] !== q[1]).map(([p, q]) => ({
    from: NAMES[fret(p)], to: NAMES[fret(q)], fromF: fret(p), toF: fret(q),
    limit: oddLimit(q[0] - p[0], q[1] - p[1]), cost: kees(q[0] - p[0], q[1] - p[1]) })) };
}

export const etdFret: readonly number[] = PALETTE.etdFret;
/** TD in 12-TET: td's pairing, each move priced at its tempered size */
export function td12(X: Pt[], Y: Pt[]) {
  const t = td(X, Y), moves = t.moves.map(m => ({ ...m, cost12: etdFret[mod(m.toF - m.fromF, 12)] }));
  return { total: moves.reduce((a, m) => a + m.cost12, 0), moves, pure: t.total };
}
export const group = (v: number, t: number) => (v <= 2 ? 'smooth' : 'leap') + ', ' + (t < 5.5 ? 'near' : t < 7.5 ? 'far' : 'remote');

// ---------------------------------------------------------------- geometry (SPEC §3, locked)
export const CS = L3 / (2 * L5), SN = Math.sqrt(1 - CS * CS);
export const xy = (p: Pt): Pt => [p[0] * L3 + p[1] * L5 * CS, p[1] * L5 * SN];
export const tri = (k: TriKind, a: number, b: number): Pt[] =>
  k === 'up' ? [[a, b], [a, b + 1], [a + 1, b]] : [[a, b + 1], [a + 1, b], [a + 1, b + 1]];
export const spell = (a: number, b: number) => {
  const n = a + 4 * b, acc = Math.floor((n + 1) / 7);
  return 'FCGDAEB'[mod(n + 1, 7)] + (acc > 0 ? '♯'.repeat(acc) : '♭'.repeat(-acc));
};
const KEY_TRIS: [TriKind, number, number, string][] = [['up', 0, 0, 'I'], ['up', -1, 0, 'IV'], ['up', 1, 0, 'V'], ['dn', -1, 0, 'vi'], ['dn', 0, 0, 'iii'], ['dn', -2, 0, 'ii']];
const MINOR_RN: Record<string, string> = { I: 'III', ii: 'iv', iii: 'v', IV: 'VI', V: 'VII', vi: 'i', 'vii°': 'ii°' };
const STEPS = { '': [0, 2, 4, 5, 7, 9, 11], m: [0, 2, 3, 5, 7, 8, 10] };
/** scale degree of the note named nm at absolute fret f, in the key of the home triad */
export function degreeOf(nm: string, f: number, root: number, kind: '' | 'm') {
  const t = chord(root, kind)[0], L = (s: string) => 'CDEFGAB'.indexOf(s[0]);
  const d = mod(L(nm) - L(spell(...t)), 7);
  const diff = mod(f - (root + STEPS[kind][d]) + 6, 12) - 6;
  return (diff > 0 ? '♯'.repeat(diff) : '♭'.repeat(-diff)) + (d + 1) + '̂';
}
export const degree = (p: Pt, root: number, kind: '' | 'm') => degreeOf(spell(...p), fret(p), root, kind);
const SHARP = ['C', 'C♯', 'D', 'D♯', 'E', 'F', 'F♯', 'G', 'G♯', 'A', 'A♯', 'B'];
const FLAT = ['C', 'D♭', 'D', 'E♭', 'E', 'F', 'G♭', 'G', 'A♭', 'A', 'B♭', 'B'];
/** every name a fret goes by: the grid's spelling first, then its enharmonic twin */
export function names(p: Pt): string[] {
  const nm = spell(...p), f = fret(p);
  const alt = [SHARP[f], FLAT[f]].find(x => x !== nm);
  return alt && alt !== nm ? [nm, alt] : [nm];
}
/** TD of a pitch class f frets above the root, in 12-TET */
export const pcTD = (f: number) => etdFret[mod(f, 12)];

export interface Row {
  root: number; kind: Kind; order: number; key: string; home: boolean; place: Place;
  chord: string; alt: string; shared: number; vl: number; td: number; tdKey: number; td12: number;
  vlMoves: VLMove[]; tdMoves: TDMove[]; group: string;
}
const lt = (u: number[], w: number[]) => { for (let i = 0; i < u.length; i++) if (u[i] !== w[i]) return u[i] < w[i]; return false; };
const pid = (p: Pt) => p[0] + ',' + p[1];

/** the key of a home triad and its neighbourhood, each chord with an order and one place (SPEC §5) */
export function neighbourhood(root: number, kind: '' | 'm'): Row[] {
  const X = chord(root, kind), M: Pt = kind === '' ? X[0] : [X[0][0] + 1, X[0][1] - 1];
  const rnOf = (rn: string) => kind === '' ? rn : MINOR_RN[rn];
  const keyTris = KEY_TRIS.map(([k, a, b, rn]) => [k, M[0] + a, M[1] + b, rnOf(rn)] as [TriKind, number, number, string]);
  const vii: Pt[] = [[M[0] + 1, M[1] + 1], [M[0] + 2, M[1]], [M[0] + 3, M[1] - 1]];
  const keyPts = new Set(keyTris.flatMap(([k, a, b]) => tri(k, a, b).map(pid)));
  const keySets = [...keyTris.map(([k, a, b]) => new Set(tri(k, a, b).map(fret))), new Set(vii.map(fret))];
  const keyPcs = new Set(keySets.flatMap(s => [...s]));
  const kp = [...keyPts].map(s => xy(s.split(',').map(Number) as Pt));
  const cx = kp.reduce((s, p) => s + p[0], 0) / kp.length, cy = kp.reduce((s, p) => s + p[1], 0) / kp.length;
  const placed = new Map<string, [number, string, Place]>();
  keyTris.forEach(([k, a, b, rn]) => placed.set(`${fret(tri(k, a, b)[0])}|${k === 'up' ? '' : 'm'}`, [0, rn, [k, a, b]]));
  placed.set(`${fret(vii[0])}|°`, [0, rnOf('vii°'), ['dim', ...vii[0]]]);
  const todo: [number, number, '' | 'm'][] = [];
  for (let r = 0; r < 12; r++) for (const q of ['', 'm'] as const) {
    if (placed.has(`${r}|${q}`)) continue;
    const pcs = new Set((q === '' ? [0, 4, 7] : [0, 3, 7]).map(d => (r + d) % 12));
    const order = Math.max(...keySets.map(ks => [...pcs].filter(x => ks.has(x)).length)) >= 2 ? 1
      : [...pcs].some(x => keyPcs.has(x)) ? 2 : 3;
    todo.push([order, r, q]);
  }
  todo.sort((x, y) => x[0] - y[0] || x[1] - y[1] || (x[2] < y[2] ? -1 : x[2] > y[2] ? 1 : 0));
  for (const [order, r, q] of todo) {
    // third-order chords touch no key point; place them against the chords already placed
    const near = new Set(order === 3 ? [...placed.values()].filter(v => v[2][0] !== 'dim')
      .flatMap(v => tri(v[2][0] as TriKind, v[2][1], v[2][2]).map(pid)) : []);
    const rowsB = new Set([...near].map(s => +s.split(',')[1]));
    const k: TriKind = q === '' ? 'up' : 'dn';
    let best: [number[], Place] | null = null;
    for (let a = M[0] - 9; a <= M[0] + 9; a++) for (let b = M[1] - 4; b <= M[1] + 4; b++) {
      const pts = tri(k, a, b);
      if (fret(pts[0]) !== r) continue;
      const c = pts.map(xy), mx = (c[0][0] + c[1][0] + c[2][0]) / 3 - cx, my = (c[0][1] + c[1][1] + c[2][1]) / 3 - cy;
      const sc = [-pts.filter(p => keyPts.has(pid(p))).length, near.size ? pts.filter(p => !rowsB.has(p[1])).length : 0,
        -pts.filter(p => near.has(pid(p))).length, mx * mx + my * my];
      if (!best || lt(sc, best[0])) best = [sc, [k, a, b]];
    }
    placed.set(`${r}|${q}`, [order, '', best![1]]);
  }
  const fx = new Set(X.map(fret)), rows: Row[] = [];
  const keyChords = [...placed].filter(([, v]) => v[0] === 0).map(([k]) => { const [r, q] = k.split('|'); return chord(+r, q as Kind); });
  placed.forEach(([order, rn, place], key) => {
    const [rs, qs] = key.split('|'), r = +rs, q = qs as Kind, Y = chord(r, q), v = vl(X, Y), t = td(X, Y), t12 = td12(X, Y).total;
    const tdKey = Math.min(...keyChords.map(K => td(K, Y).total));
    const p0 = place[0] === 'dim' ? null : tri(place[0], place[1], place[2])[0];
    rows.push({ root: r, kind: q, order, key: rn, home: r === root && q === kind, place,
      chord: p0 ? spell(...p0) + q : name(r, q),
      alt: p0 && names(p0)[1] ? names(p0)[1] + q : '',
      shared: Y.map(fret).filter(f => fx.has(f)).length, vl: v.total, td: t.total, tdKey, td12: t12,
      vlMoves: v.moves, tdMoves: t.moves, group: group(v.total, t12) });
  });
  return rows.sort((a, b) => a.order - b.order || a.td12 - b.td12 || a.vl - b.vl || a.chord.localeCompare(b.chord));
}

/** one torus tile around the key: every chord exactly once; copies outside it are faded */
export function tile(rows: Row[]): Set<string> {
  const key = rows.filter(r => r.order === 0 && r.place[0] !== 'dim').map(r => r.place);
  const b0 = key[0][2], a0 = Math.min(...key.filter(p => p[0] === 'up').map(p => p[1]));
  const row = (b: number, a: number, k: TriKind) => {
    const out: string[] = [];
    while (out.length < 9) { out.push([k, a, b].join(',')); [k, a] = k === 'up' ? ['dn', a] : ['up', a + 1]; }
    return out;
  };
  return new Set([...row(b0 - 1, a0 - 1, 'up'), ...key.map(p => p.join(',')), ...row(b0 + 1, a0 - 2, 'dn')]);
}
