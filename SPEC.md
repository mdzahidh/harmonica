# Tonnetz neighbourhood app: specification

The target is the **"Key's neighbourhood" map** from the Harmonic Grid book (Chapter 7). It should be the same diagram, with the same geometry, numbers, colour code and labels. After that, the UI and styling are free to change.

- **Look:** `demo/index.html` (open it in a browser) and `reference/demo-screenshot-C.png`.
- **Truth:** `reference/book_widgets.js`. The `CD` module (lines 6–222) holds the maths; `neighbourMap()` holds the drawing. `reference/chord_distance.py` is the Python original it was checked against.
- **Test:** `golden/*.json` holds every number and label the map shows, for all 24 home chords. `tests/check.mjs` compares the app's export against them.

If this text and the reference code disagree, the code wins. Report the disagreement.

---

## 1 · The idea in one paragraph

Every note sits on a 2-D lattice. **One step right is a perfect fifth (×3/2).** **One step up the slant is a major third (×5/4).** Notes that are close on the map are harmonically close. Each edge is drawn at its true **tonal distance**: log₂ of the interval's odd limit, which counts how many octaves you climb a shared harmonic series before both notes appear. Major triads are ▲ triangles and minor triads are ▼ triangles. Triangles that share an edge share two notes. A key is a strip of 6 triangles. The map colours every major and minor triad by how far it is from a home chord, in two senses: **TD** (how far the harmony moves) as colour, and **VL** (how far the fingers move, in frets) as a dot pattern.

## 2 · The lattice

A point **(a, b)** is the pitch class **3ᵃ · 5ᵇ** (octaves ignored). *a* counts fifths and *b* counts major thirds.

| Quantity | Formula |
|---|---|
| fret above C (12-TET pitch class) | `fret(a,b) = (7a + 4b) mod 12` |
| fifth edge → | (a+1, b): ×3/2, +7 frets |
| major-third edge ↗ | (a, b+1): ×5/4, +4 frets |
| minor-third edge ↘ | (a+1, b−1): ×6/5, +3 frets |
| ↘↘ | the tritone (6 frets), e.g. B → D → F |
| spelling | `n = a + 4b`; letter = `"FCGDAEB"[(n+1) mod 7]`; accidentals = `floor((n+1)/7)`, sharps if positive, flats if negative |

**Root positions.** The home triad's root sits on row b = 0, at its place on the line of fifths:
`C 0, G 1, D 2, A 3, E 4, B 5, F♯ 6, F −1, B♭ −2, E♭ −3, A♭ −4, D♭ −5` (`POS` in the code).

**Triad shapes** (offsets from the root point):
- major `[(0,0), (0,1), (1,0)]`: root, M3 ↗, 5th →. Drawn as ▲ `tri('up', a, b) = [(a,b), (a,b+1), (a+1,b)]`.
- minor `[(0,0), (1,−1), (1,0)]`: root, m3, 5th. Drawn as ▼ `tri('dn', a, b) = [(a,b+1), (a+1,b), (a+1,b+1)]`, root first.
- diminished `[(0,0), (1,−1), (2,−2)]`: a straight ↘↘ chain, a collapsed triangle.

Rotating the map 180° swaps parents and children, and so swaps major and minor. A major triad has one parent and two children (4:5:6). A minor triad has two parents sharing one child (10:12:15).

## 3 · The geometry, and why it is exactly this (the important part)

```
xy(a, b) = ( a·log₂3 + b·log₂5·cos θ ,  b·log₂5·sin θ )      (y up; flip y for the screen)
cos θ = log₂3 / (2·log₂5)   →   θ = 70.04°
log₂3 = 1.58496   log₂5 = 2.32193
```

**Rule: every edge is drawn at its true tonal distance.** The tonal distance of an interval p/q is log₂ of its odd limit, the larger odd number left after removing all factors of 2.
- **Fifth edge:** length log₂3 = 1.585, since the odd limit of 3/2 is 3. This fixes the horizontal unit.
- **Major-third edge:** length log₂5 = 2.322, since the odd limit of 5/4 is 5. This fixes the slant edge's length.
- **The angle θ is the one free parameter, and it is not a style choice.** It is chosen so that the third edge, the minor third (1, −1), also comes out at its true tonal distance. 6/5 has odd limit 5, so it must be drawn log₂5 long:
  - vector = (log₂3 − log₂5·cos θ, −log₂5·sin θ)
  - its horizontal part = log₂3 − ½·log₂3 = **½·log₂3**
  - its length² = ¼(log₂3)² + (log₂5)²·(1 − cos²θ) = ¼(log₂3)² + (log₂5)² − ¼(log₂3)² = **(log₂5)²** ✓
  - Setting length = log₂5 forces cos θ = log₂3 / (2·log₂5). There is exactly one such angle.

What follows from it, so check all three on screen:
1. **Every triad is isosceles:** two sides log₂5 (the thirds) and a base of log₂3 (the fifth). Major and minor are mirror images.
2. **A note and its sharp or flat stack straight up and down.** The step (−1, +2), 25/24, has horizontal part −log₂3 + 2·log₂5·cos θ = 0. So C and C♯ share an x.
3. **Every edge on the page is drawn at its true distance,** so the eye reads harmonic closeness directly.

**Distance between any two notes on the map** (k fifths and j thirds apart):
- `t(k, j) = |k|·log₂3 + |j|·log₂5` if k and j have the same sign;
- `t(k, j) = max(|k|·log₂3, |j|·log₂5)` if they have opposite signs.

This is log₂ of the odd limit of 3ᵏ·5ʲ ("Kees height"). The shared root of the two notes is the lower-left corner of their bounding box, and the longer walk from it is the distance. `kees()` in the code computes this.

**Why "tonal distance" and not Tenney's harmonic distance log₂(p·q):** Tenney's measure scores 6/5 like 15/8, but the ear hears the minor third as consonant. The odd limit fixes that. (Book §2, "Under the hood".)

**The torus.** On a guitar, (0, 3) is the same fret as (0, 0), because three major thirds make an octave. (4, −1) is too, because four fifths make a major third plus two octaves (the syntonic comma, 81/80). So the 12-TET lattice wraps into a torus. The flat map shows a window wider than one torus tile, so some chords appear twice: **comma copies**. They get the same colour and label, and the copies outside the tile are faded (§6).

## 4 · The two distances

**Melodic distance between notes** = frets the short way round: `d(a, b) = min(|a−b| mod 12, 12 − |a−b| mod 12)`.

**VL (voice leading) between chords** = minimum over the 3! pairings of Σ d(xᵢ, y_σ(i)).

**TD pure between chords:** each chord is a **rigid** shape on the lattice. Slide Y's shape by every (da, db) with `7·da + 4·db ≡ 0 (mod 12)`, da ∈ [−12, 12], db ∈ [−4, 4]. Take the pairing and slide with the smallest Σ `kees(Δ)`. On a tie, prefer more held notes (zero moves). This spells notes by itself: Cm's E♭ comes out as 6/5, never as D♯.

**TD in 12-TET (what the map shows):** keep the pure pairing, and price each moving voice at the tempered size of its fret interval, `etdFret[(to − from) mod 12]`.

**etdFret** is the expected tonal distance of each 12-TET fret (Appendix B of the book):
- candidates rᵢ = 3ᵃ·5ᵇ, |a| ≤ 6, |b| ≤ 3, folded into one octave; cᵢ is the size in cents, tᵢ = kees(a, b);
- weight wᵢ = exp(−dᵢ² / 2σ²) · 2^(−2·tᵢ), where dᵢ is the circular cent distance and σ = 15¢. The prior L⁻² equals 2^(−2t);
- TD(c) = Σ wᵢ·tᵢ / Σ wᵢ.

```
etdFret = [0.0007, 4.0374, 3.1718, 2.4552, 2.3709, 1.6022, 5.2368, 1.6022, 2.3709, 2.4552, 3.1718, 4.0374]
```

The reason for 12-TET is that the guitar plays it. For example, C → E costs 6.97 in pure tuning but **4.74** on frets, because G♯ and A♭ are the same fret.

**Each note on the map** carries its distance from the home root: VL = min(f, 12−f) and TD = etdFret[f], where f = fret above the home root. Comma twins therefore read the same.

**Groups:** VL ≤ 2 is *smooth*, otherwise *leap*. TD₁₂ < 5.5 is *near*, < 7.5 is *far*, otherwise *remote*.

## 5 · The key and its neighbourhood (`CD.neighbourhood`)

For a **major** home, M = the home root point. For a **minor** home (natural minor), M = the relative major's tonic = root + (1, −1). Numerals are remapped `I→III, ii→iv, iii→v, IV→VI, V→VII, vi→i, vii°→ii°`.

**The key (order 0):** 6 triangles relative to M:
`up(0,0) I · up(−1,0) IV · up(1,0) V · dn(−1,0) vi · dn(0,0) iii · dn(−2,0) ii`
plus **vii°** as the chain M+(1,1) → M+(2,0) → M+(3,−1), e.g. B–D–F for C. The key is a strip along row b = 0, between rows −1 … +1.

**Every other major and minor triad gets one order:**
- **1:** it shares ≥ 2 notes (an edge) with some key chord, vii° included. For C: Cm, Gm, E, A, Fm, Bm, B♭, D.
- **2:** it shares ≥ 1 note with the key. For C: A♭, E♭, C♯m, F♯m, G♯m, B, D♭, B♭m.
- **3:** it shares no note. For C: F♯ and E♭m.

Orders 0–3 together cover all 24 triads. Measured as pure TD to the nearest key chord, the orders are strict shells (0 · 3.91–4.64 · 6.97 · 10.87) for all 24 homes.

**Placement:** each non-key triad gets one position, in order 1 → 2 → 3, then by root and kind. Search a in M.a ± 9 and b in M.b ± 4 over triangles with the right root fret. Minimise the score tuple lexicographically:
`[ −(points shared with the key's points), (order 3 only) points outside rows already used, −(order 3 only) points shared with placed chords, squared distance of the centroid from the key's centroid ]`.
Copy this exactly from the reference. It decides where chords such as B♭ and D land.

## 6 · What is drawn (`neighbourMap` render; golden: `maps.json`)

1. **Window.** Rows b0…b1 = the min and max b of all placed triangles. x from (min x − 0.2) to (max x + 0.2) of their points. **Every lattice point in that window is drawn.**
2. **Triangles.** Every whole ▲/▼ in the window whose chord is in the neighbourhood (up to the chosen order) is painted, **including comma copies**. A copy has the same chord, colour and label.
3. **Fading.** `CD.tile()` is one torus tile: the row below the key (9 triangles), the key (6) and the row above (9). That makes 24, every chord exactly once. Triangles outside the tile get a white overlay at 62 % opacity. For C, the faded ones are G, Gm and B♭ on the left and Bm, D and Dm on the right.
4. **Edges.** Every lattice edge in the window: → and ↗ solid and thin, ↘ dotted. They are drawn over the fills.
5. **Key outline.** The edges that belong to exactly one key triangle, **bold black**.
6. **Tritone.** A broad translucent red band along the vii° chain, red rings on its two end notes, and a three-line label below the chain's lower end: "B° (vii°)", "tritone B–F", "VL | TD".
7. **Chord label** (centroid). First line: the name, with both names when the root has two (e.g. "A♭ / G♯"), the grid spelling first, plus " (numeral)" if the chord is in the key. Second line: "VL | TD₁₂" to 1 decimal, or "home".
8. **Stars.** A gold ★ on the home triangle at the exact home coordinates, and on the home root note. These are the only stars.
9. **Notes.** A white circle (r = 0.4 lattice units). One line per name: "G♯ (♯5̂)" over "A♭ (♭6̂)". The degree is the accidental, the digit and a combining circumflex U+0302. The last line is "VL | TD" from the home root. Notes not used by any full-strength triangle are greyed.
10. **Scale degree:** the letter gives the number (counted from the home root's letter). The accidental is the fret difference from the major or natural-minor scale step, wrapped to −6…+5.

## 7 · The colour code (`PALETTE`, in `golden/constants.json`)

- **Default:** colour = TD₁₂ on **Parula**, with range [0, 12] mapped to 33 stops and interpolated linearly in RGB. Band marks sit at 5.5 (near|far) and 7.5 (far|remote).
- **Dots = VL:** the dot level for VL 0…6 is `[0, 0, 0, 1, 2, 3, 5]`. There are no dots while the move is smooth (VL ≤ 2). Dot spacing is u = unit·1.7/√level and dot radius is unit·0.075.
- **Dot ink:** dark `rgba(0,0,0,.42)` when the fill's luminance is > 0.45, otherwise light `rgba(255,255,255,.62)`. Chord text is white on dark fills.
- **Swap mode:** colour = VL on range [0, 6], and dots = TD band (near 0, far 3, remote 6).
- **Options:** colour maps Parula, Viridis, Cividis, Plasma, Magma, Inferno and Grey (stops in the palette); *reverse*; *colour the notes* (off by default). The reader's choice is remembered.
- The home chord takes colour 0, the first colour of the map.

## 8 · Behaviour in the reference (a baseline you are free to redesign)

- Select a home chord (24 options). "Show" selects the scope: key / + 1st / + 2nd / + 3rd order (default: all).
- Hovering a chord shows a tooltip: "C → G (V) · key / VL 3: C→B (1), E→D (2) / TD 4.77 in 12-TET (pure 4.75): …".
- **Clicking a chord makes it the new home.** Its key and neighbourhood redraw, and the move is added to a trail: "Progression: C → G (3 | 4.8) → … · total VL, TD".
- Companion views: a VL × TD scatter with a sortable table, and a two-chord calculator.

## 9 · Test vectors (home = C; all in `golden/`)

| Chord | Order | VL | TD₁₂ | TD pure | TD to key |
|---|---|---|---|---|---|
| Am (vi) | 0 | 2 | 3.17 | 3.17 | 0 |
| Em (iii) | 0 | 1 | 4.04 | 3.91 | 0 |
| F (IV), G (V) | 0 | 3 | 4.77 | 4.75 | 0 |
| Dm (ii), B° (vii°) | 0 | 5 | 7.95 | 7.92 | 0 |
| Cm | 1 | 1 | 4.04 | 4.64 | 4.64 |
| E | 1 | 2 | 4.74 | 6.97 | 4.64 |
| B♭ / A♯ | 1 | 6 | 9.52 | 9.51 | 3.91 |
| A♭ / G♯ | 2 | 2 | 4.74 | 6.97 | 6.97 |
| B | 2 | 3 | 12.11 | 11.72 | 6.97 |
| E♭m (D♯m) | 3 | 4 | 8.08 | 11.61 | 10.87 |
| G♭ / F♯ | 3 | 6 | 15.71 | 13.93 | 10.87 |

Geometry checks: θ = 70.04°; |minor-third edge| = |major-third edge| = 2.3219; x(C) = x(C♯) on the map; the C map has 30 painted triangles and 24 notes.
