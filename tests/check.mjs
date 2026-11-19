// Compare the new app's exported numbers with the golden files from the book.
// Run: node tests/check.mjs <dir>     <dir> holds the app's own pairs.json / neighbourhoods.json / maps.json,
// written in the same shape as golden/ (see tools/make_golden.mjs). Numbers must agree to 1e-3; strings exactly.
// With no <dir>, the golden files are compared with themselves (a smoke test of this script).
import { readFileSync, existsSync } from 'fs';
const dir = process.argv[2] || 'golden';
let bad = 0, n = 0;
const same = (g, c, path) => {
  n++;
  if (typeof g === 'number') { if (typeof c !== 'number' || Math.abs(g - c) > 1e-3) { bad++; if (bad <= 25) console.log('MISMATCH', path, 'want', g, 'got', c); } return; }
  if (g === null || typeof g !== 'object') { if (g !== c) { bad++; if (bad <= 25) console.log('MISMATCH', path, 'want', JSON.stringify(g), 'got', JSON.stringify(c)); } return; }
  if (c === null || typeof c !== 'object') { bad++; if (bad <= 25) console.log('MISSING', path); return; }
  if (Array.isArray(g) && g.length !== c.length) { bad++; if (bad <= 25) console.log('LENGTH', path, g.length, c.length); return; }
  for (const k of Object.keys(g)) same(g[k], c[k], `${path}.${k}`);
};
for (const f of ['pairs.json', 'neighbourhoods.json', 'maps.json']) {
  const p = `${dir}/${f}`;
  if (!existsSync(p)) { console.log('skip (not exported yet):', p); continue; }
  same(JSON.parse(readFileSync(`golden/${f}`)), JSON.parse(readFileSync(p)), f);
}
console.log(`${n - bad}/${n} values agree`);
process.exit(bad ? 1 : 0);
