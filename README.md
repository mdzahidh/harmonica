# Tonnetz app: starter kit

This kit is the starting point for a standalone web app of the **"Key's neighbourhood" map** from the Harmonic Grid book (Chapter 7). You build it on the Mac with Claude Code, outside the vault. The kit fixes the parts that must not change: the geometry, the distances, the colour code and the labels. Everything else is open for you to iterate on.

## What is in here

| Path | What it is |
|---|---|
| `SPEC.md` | **Read first.** The geometry and why it is exactly that, the two distances, the neighbourhood orders, what is drawn, the colour code, test vectors |
| `demo/index.html` | The book's live widgets as one file. Open it in a browser: this is the target |
| `reference/book_widgets.js` | The reference implementation. `CD` = the maths (runs in Node: `require()` it); `neighbourMap()` = the drawing |
| `reference/chord_distance.py` | The Python original, used to check the JS (book tooling; not needed to run anything) |
| `reference/neighbour-grid.svg/.png`, `demo-screenshot-C.png` | The static book chart and a screenshot of the live map, home = C |
| `golden/*.json` | Every number and label for all 24 home chords: `pairs.json` (1,296 chord pairs: VL, TD, TD₁₂), `neighbourhoods.json`, `maps.json` (triangles, faded flags, note labels, tritone), `constants.json` (etdFret and the colour maps) |
| `tools/make_golden.mjs` | Regenerates `golden/` from the reference |
| `tests/check.mjs` | `node tests/check.mjs <dir>` compares the app's export with `golden/` (numbers to 1e-3, strings exact) |
| `CLAUDE.md` | Rules for Claude Code in the new repo. It goes to the repo root unchanged |

## Start on the Mac

1. Copy the kit out of the vault:
   ```
   mkdir -p ~/src && cp -R "<vault>/music/tonnetz-app-starter" ~/src/tonnetz && cd ~/src/tonnetz
   git init && git add -A && git commit -m "Starter kit from the Harmonic Grid book"
   ```
2. Open `demo/index.html` in Safari or Chrome. Click a few chords to see the target behaviour.
3. Run `node tests/check.mjs` to make sure Node works. It should print `38832/38832 values agree`.
4. Run `claude` in `~/src/tonnetz` and paste the prompt below.

## First prompt for Claude Code

> Read CLAUDE.md, SPEC.md, and reference/book_widgets.js (the CD module and neighbourMap). Build a standalone web app that shows the Key's neighbourhood map, identical to demo/index.html: same geometry, numbers, colour code and labels.
> Stack: Vite + TypeScript, plain SVG, no UI framework yet. Vitest for tests.
> Step 1: port CD to `src/core/` as pure, typed functions with no DOM. Add `npm run export-golden`, which writes pairs.json, neighbourhoods.json and maps.json in the golden/ shapes to `out/`. Make `node tests/check.mjs out` pass 100 %.
> Step 2: render the map in `src/view/` from the core's output only. Compare it with demo/index.html side by side for home C, Am, F♯ and E♭m.
> Step 3: home select, scope select, hover tooltip, click-to-move with the progression trail, and the display settings (colour map, colour = TD or VL, reverse, colour the notes), saved in localStorage.
> Stop after each step and show me the result before going on.

After that, the UI and styling are yours to change. The core stays locked by the golden test.
