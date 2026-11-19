// Step 1 placeholder: the core's neighbourhood as a table. The SVG map arrives in Step 2.
import { NAMES, neighbourhood } from '../core/cd';
import './style.css';

const app = document.getElementById('app')!;
const HOMES = NAMES.flatMap((n, r) => [[r, '', n], [r, 'm', n + 'm']] as const);

function render(r: number, k: '' | 'm') {
  const rows = neighbourhood(r, k);
  app.innerHTML = `
    <h1>Harmonica <span>· the key's neighbourhood</span></h1>
    <p class="note">Step 1: the core port (checked against all 38,832 golden values). The map is next.
      Meanwhile, the book's widget: <a href="demo/">demo</a>.</p>
    <label>Home <select id="home">${HOMES.map(([hr, hk, n]) =>
      `<option value="${hr}|${hk}" ${hr === r && hk === k ? 'selected' : ''}>${n}</option>`).join('')}</select></label>
    <table><thead><tr><th>Chord</th><th>Order</th><th>Numeral</th><th>VL</th><th>TD₁₂</th><th>TD pure</th><th>TD to key</th><th>Group</th></tr></thead>
    <tbody>${rows.map(x => `<tr${x.home ? ' class="home"' : ''}><td>${x.chord}${x.alt ? ' / ' + x.alt : ''}</td><td>${x.order}</td><td>${x.key}</td>
      <td>${x.vl}</td><td>${x.td12.toFixed(2)}</td><td>${x.td.toFixed(2)}</td><td>${x.tdKey.toFixed(2)}</td><td>${x.group}</td></tr>`).join('')}</tbody></table>`;
  app.querySelector<HTMLSelectElement>('#home')!.onchange = e => {
    const [hr, hk] = (e.target as HTMLSelectElement).value.split('|');
    render(+hr, hk as '' | 'm');
  };
}
render(0, '');
