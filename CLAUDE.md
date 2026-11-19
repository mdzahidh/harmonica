# Tonnetz app: rules for Claude Code

A web app of the Key's neighbourhood map from Zahid's Harmonic Grid book. The spec is `SPEC.md` and the visual target is `demo/index.html`.

## Locked (do not change without Zahid's explicit OK)

- **Geometry:** `xy(a,b) = (a·log₂3 + b·log₂5·cosθ, b·log₂5·sinθ)` with `cosθ = log₂3/(2·log₂5)`. No "nicer" angle (60° etc.) and no rescaled axes: every edge is drawn at its true tonal distance (SPEC §3).
- **Lattice conventions:** (a, b) = 3ᵃ·5ᵇ; fifths → right, major thirds ↗; ▲ major, ▼ minor; the key strip along row 0; the placement scoring of SPEC §5.
- **Numbers:** VL, TD pure, TD₁₂ (etdFret, σ = 15¢, prior L⁻²), the orders, and the note and chord labels. `node tests/check.mjs out` must pass 100 % after every change to `src/core/`. Run `npm run export-golden` first.
- **Colour code defaults:** Parula, colour = TD₁₂ on [0, 12], bands at 5.5 and 7.5, VL dots `[0,0,0,1,2,3,5]`.
- `reference/` and `golden/` are read-only. If you believe the reference is wrong, say so. Do not "fix" the golden files.

## Free to change

- Layout, controls, typography, animation, zoom and pan, mobile, new views, extra info panels, audio playback, and any styling that keeps the locked content intact.

## Structure

- `src/core/`: pure TypeScript, no DOM. A port of `CD` from `reference/book_widgets.js`.
- `src/view/`: SVG rendering and UI. It reads only what the core returns.
- `scripts/export-golden.ts`: writes `out/pairs.json`, `out/neighbourhoods.json` and `out/maps.json` in the golden shapes (see `tools/make_golden.mjs`).

## Zahid's preferences

- He is technical (maths, signal processing, graphics). Show the derivation, not just the claim.
- He likes elegant, uncluttered design: one convention used everywhere, no redundant marks.
- He converges by reacting to working prototypes, so show a running build early.
