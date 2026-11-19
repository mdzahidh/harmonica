// SPEC §3 geometry checks and the §9 test vectors (home = C).
import { describe, expect, it } from 'vitest';
import { CS, L3, L5, chord, td, td12, vl, xy, neighbourhood } from '../src/core/cd';
import { buildMap } from '../src/core/map';

describe('geometry (SPEC §3)', () => {
  it('θ = 70.04°', () => expect(Math.acos(CS) * 180 / Math.PI).toBeCloseTo(70.04, 2));
  it('every edge at its true tonal distance', () => {
    const len = (p: [number, number]) => Math.hypot(...xy(p));
    expect(len([1, 0])).toBeCloseTo(L3, 12);
    expect(len([0, 1])).toBeCloseTo(L5, 12);
    expect(len([1, -1])).toBeCloseTo(L5, 12);
  });
  it('a note and its sharp share an x (25/24 is vertical)', () => expect(xy([-1, 2])[0]).toBeCloseTo(0, 12));
  it('C map: 30 painted triangles, 24 notes', () => {
    const m = buildMap(0, '');
    expect(m.triangles.length).toBe(30);
    expect(m.notes.length).toBe(24);
  });
});

describe('test vectors (SPEC §9, home = C)', () => {
  const rows = neighbourhood(0, '');
  const C = chord(0, '');
  const cases: [string, number, number, number, number, number][] = [
    ['Am', 0, 2, 3.17, 3.17, 0], ['Em', 0, 1, 4.04, 3.91, 0], ['F', 0, 3, 4.77, 4.75, 0], ['G', 0, 3, 4.77, 4.75, 0],
    ['Dm', 0, 5, 7.95, 7.92, 0], ['B°', 0, 5, 7.95, 7.92, 0], ['Cm', 1, 1, 4.04, 4.64, 4.64], ['E', 1, 2, 4.74, 6.97, 4.64],
    ['B♭', 1, 6, 9.52, 9.51, 3.91], ['A♭', 2, 2, 4.74, 6.97, 6.97], ['B', 2, 3, 12.11, 11.72, 6.97],
    ['E♭m', 3, 4, 8.08, 11.61, 10.87], ['G♭', 3, 6, 15.71, 13.93, 10.87],
  ];
  for (const [nm, order, v, t12, t, tk] of cases) it(nm, () => {
    const r = rows.find(x => x.chord === nm || x.alt === nm)!;
    expect(r, nm).toBeDefined();
    expect(r.order).toBe(order);
    expect(r.vl).toBe(v);
    expect(r.td12).toBeCloseTo(t12, 2);
    expect(r.td).toBeCloseTo(t, 2);
    expect(r.tdKey).toBeCloseTo(tk, 2);
    const Y = chord(r.root, r.kind);
    expect(vl(C, Y).total).toBe(v);
    expect(td(C, Y).total).toBeCloseTo(t, 2);
    expect(td12(C, Y).total).toBeCloseTo(t12, 2);
  });
});
