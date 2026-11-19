"""Two distances between chords: melodic (VL, frets) and tonal (TD, log2 odd limit), one formula.

    VL(X, Y) = min over pairings σ of Σ d(x_i, y_σ(i)),   d = frets the short way round
    TD(X, Y) = min over pairings σ of Σ t(x_i, y_σ(i)),   t = log2(odd limit) on the grid

For TD each chord sits on the grid as its own rigid shape (a triad = a triangle, pure intervals
inside) and Y's shape slides to the copy nearest X. The minimum then picks the natural spelling
by itself (Cm's E♭ = 6/5, never D♯). Asked for in Newton - Music 2026-10-10.

Run:  python3 chord_distance.py   -> book/chord-distance-c.{svg,png}, prints the C table
Import: vl(), td(), neighbours() (the HTML book's calculator re-implements these in JS and is
checked against them by `python3 chord_distance.py --check-js`).
"""
import json
import subprocess
import sys
from fractions import Fraction
from itertools import permutations
from math import log2
from pathlib import Path

NAMES = "C C♯ D E♭ E F F♯ G A♭ A B♭ B".split()
SHARP = "C C♯ D D♯ E F F♯ G G♯ A A♯ B".split()            # the two names of each fret
FLAT = "C D♭ D E♭ E F G♭ G A♭ A B♭ B".split()
L3, L5 = log2(3), log2(5)
SHAPES = {"": [(0, 0), (0, 1), (1, 0)],        # major: root, M3 (↗), 5th (→)
          "m": [(0, 0), (1, -1), (1, 0)],       # minor: root, m3 (→↘), 5th (→)
          "°": [(0, 0), (1, -1), (2, -2)]}      # diminished: two minor thirds, a straight ↘↘ chain
# The key's own chords, by fret above the tonic (natural minor for a minor tonic).
KEY_STEPS = {"": [(0, "", "I"), (2, "m", "ii"), (4, "m", "iii"), (5, "", "IV"), (7, "", "V"),
                  (9, "m", "vi"), (11, "°", "vii°")],
             "m": [(0, "m", "i"), (2, "°", "ii°"), (3, "", "III"), (5, "m", "iv"), (7, "m", "v"),
                   (8, "", "VI"), (10, "", "VII")]}
OUT = Path(__file__).parent / "book"


def fret(p):
    return (7 * p[0] + 4 * p[1]) % 12


def kees(k, j):
    """Tonal distance of the grid step (k fifths, j thirds) = log2(odd limit of 3^k 5^j)."""
    if k * j >= 0:
        return abs(k) * L3 + abs(j) * L5
    return max(abs(k) * L3, abs(j) * L5)


def odd_limit(k, j):
    r = Fraction(3) ** k * Fraction(5) ** j
    n, d = r.numerator, r.denominator
    while n % 2 == 0:
        n //= 2
    while d % 2 == 0:
        d //= 2
    return max(n, d)


def chord(root, kind):
    """Grid points of a triad with its root at fret `root`, placed at the copy nearest C."""
    a = {0: 0, 7: 1, 2: 2, 9: 3, 4: 4, 11: 5, 6: 6, 1: -5, 8: -4, 3: -3, 10: -2, 5: -1}[root]
    return [(a + p[0], p[1]) for p in SHAPES[kind]]


def name(root, kind):
    return NAMES[root] + kind


def short(a, b):
    return min((a - b) % 12, (b - a) % 12)


def vl(X, Y):
    """X, Y: lists of grid points (only their frets matter). Returns (total, moves)."""
    fx, fy = [fret(p) for p in X], [fret(p) for p in Y]
    best = min((sum(short(x, y) for x, y in zip(fx, P)), P) for P in permutations(fy))
    return best[0], [(x, y, short(x, y)) for x, y in zip(fx, best[1]) if x != y]


def td(X, Y, window=4):
    """Slide Y's rigid shape over every comma copy near X; pair voices; sum tonal distances."""
    best = None
    for da in range(-12, 13):
        for db in range(-window, window + 1):
            if (7 * da + 4 * db) % 12:
                continue
            Yc = [(p[0] + da, p[1] + db) for p in Y]
            for P in permutations(Yc):
                c = sum(kees(q[0] - p[0], q[1] - p[1]) for p, q in zip(X, P))
                held = sum(p == q for p, q in zip(X, P))     # ties: keep common tones
                if best is None or c < best[0] - 1e-9 or (abs(c - best[0]) < 1e-9
                                                           and held > best[2]):
                    best = (c, list(zip(X, P)), held)
    moves = [(fret(p), fret(q), odd_limit(q[0] - p[0], q[1] - p[1]),
              kees(q[0] - p[0], q[1] - p[1])) for p, q in best[1] if p != q]
    return best[0], moves


# ---- Tonal distance for any interval in cents (Appendix B; Zahid 2026-10-12) -------------------
# The ear hears an interval of c cents as one of the simple ratios near it. Each grid ratio r_i
# (3^a 5^b, |a| <= 6, |b| <= 3, folded into one octave) gets the weight
#     w_i = exp(-(c - c_i)^2 / (2 sigma^2)) * L_i^(-PRIOR)        (L_i = odd limit of r_i)
# and the expected tonal distance is  TD(c) = sum w_i log2(L_i) / sum w_i.
# sigma = 15 cents: the guitar's own thirds (14-16 cents off 5/4 and 6/5) must still read as thirds
# (sigma >= ~10), and a minor third must never be confused with a major one (sigma << 50).
# PRIOR = 2 gives simple ratios the wider share of the pitch line (as harmonic entropy does).
SIGMA, PRIOR = 15.0, 2.0
ETD_CANDS = [((1200 * log2(Fraction(3) ** a * Fraction(5) ** b)) % 1200, kees(a, b), (a, b))
             for a in range(-6, 7) for b in range(-3, 4)]


def etd_weights(c, sigma=SIGMA, prior=PRIOR):
    """[(probability, ratio (a, b), cents, tonal distance)] for an interval of c cents, best first."""
    from math import exp
    out = []
    for ci, t, ab in ETD_CANDS:
        d = min(abs(c - ci), 1200 - abs(c - ci))
        out.append((exp(-d * d / (2 * sigma * sigma)) * 2 ** (-prior * t), ab, ci, t))
    tot = sum(w for w, *_ in out)
    return sorted(((w / tot, ab, ci, t) for w, ab, ci, t in out), reverse=True)


def etd(c, sigma=SIGMA, prior=PRIOR):
    """Expected tonal distance of an interval of c cents (any real number)."""
    return sum(p * t for p, _, _, t in etd_weights(c, sigma, prior))


ETD_FRET = [round(etd(100 * f), 4) for f in range(12)]      # 12-TET: the TD of each fret


def td12(X, Y):
    """Chord TD in 12-TET: the pure shapes decide which voice goes where (td's pairing), and each
    move is priced at its tempered size, ETD_FRET[frets moved]. Returns (total, moves)."""
    _, moves = td(X, Y)
    m12 = [(a, b, ETD_FRET[(b - a) % 12]) for a, b, _, _ in moves]
    return sum(c for *_, c in m12), m12


def key_of(root, kind):
    """{(root, kind): numeral} for the key whose tonic is this triad."""
    return {((root + d) % 12, k): rn for d, k, rn in KEY_STEPS[kind]}


def neighbours(root=0, kind=""):
    """Every triad sharing at least one note with the given one, plus every chord of its key."""
    X = chord(root, kind)
    fx = {fret(p) for p in X}
    key = key_of(root, kind)
    rows = []
    for r in range(12):
        for k in ("", "m", "°"):
            if (r, k) == (root, kind):
                continue
            Y = chord(r, k)
            shared = len(fx & {fret(p) for p in Y})
            if not ((shared and k != "°") or (r, k) in key):
                continue
            v, vm = vl(X, Y)
            t, tm = td(X, Y)
            rows.append(dict(chord=name(r, k), key=key.get((r, k), ""), shared=shared, vl=v,
                             td=round(t, 2), kind=k,
                             vl_moves=[f"{NAMES[a]}→{NAMES[b]} ({n})" for a, b, n in vm],
                             td_moves=[f"{NAMES[a]}→{NAMES[b]} ({lim})" for a, b, lim, _ in tm]))
    return rows


KEY_TRIS = [("up", 0, 0, "I"), ("up", -1, 0, "IV"), ("up", 1, 0, "V"), ("dn", -1, 0, "vi"),
            ("dn", 0, 0, "iii"), ("dn", -2, 0, "ii")]       # around the (relative) major tonic
MINOR_RN = {"I": "III", "ii": "iv", "iii": "v", "IV": "VI", "V": "VII", "vi": "i", "vii°": "ii°"}


def tri(kind, a, b):
    """Grid points of the triangle (kind, a, b), root first: 'up' = major, 'dn' = minor."""
    return [(a, b), (a, b + 1), (a + 1, b)] if kind == "up" else [(a, b + 1), (a + 1, b), (a + 1, b + 1)]


def neighbourhood(root=0, kind=""):
    """The key of a home triad and its neighbourhood, by order (Zahid 2026-10-12):
      0  the key's own chords (six triads + vii°, natural minor for a minor home)
      1  triads sharing an edge (two notes) with a chord of the key
      2  triads sharing at least one note with the key
      3  the rest: triads sharing no note with the key (two, opposite the key on the torus)
    Notes compare by fret (12-TET). Each chord gets one place on the grid: the key's own triangle,
    or the copy touching the key's points most, then nearest the key's centre. Distances (VL, TD)
    are from the home chord. Returns rows sorted by order, then TD."""
    X = chord(root, kind)
    M = X[0] if kind == "" else (X[0][0] + 1, X[0][1] - 1)
    rn_of = (lambda r: r) if kind == "" else MINOR_RN.get
    key_tris = [(k, M[0] + a, M[1] + b, rn_of(rn)) for k, a, b, rn in KEY_TRIS]
    vii = [(M[0] + 1, M[1] + 1), (M[0] + 2, M[1]), (M[0] + 3, M[1] - 1)]
    key_pts = {q for k, a, b, _ in key_tris for q in tri(k, a, b)}
    key_sets = [{fret(q) for q in tri(k, a, b)} for k, a, b, _ in key_tris] + [{fret(q) for q in vii}]
    key_pcs = set().union(*key_sets)
    cx = sum(xy_(q)[0] for q in key_pts) / len(key_pts)
    cy = sum(xy_(q)[1] for q in key_pts) / len(key_pts)
    placed = {}
    for k, a, b, rn in key_tris:
        placed[(fret(tri(k, a, b)[0]), "" if k == "up" else "m")] = (0, rn, (k, a, b))
    placed[(fret(vii[0]), "°")] = (0, rn_of("vii°"), ("dim", *vii[0]))
    todo = []
    for r in range(12):
        for q in ("", "m"):
            if (r, q) in placed:
                continue
            pcs = {(r + d) % 12 for d in ((0, 4, 7) if q == "" else (0, 3, 7))}
            if max(len(pcs & ks) for ks in key_sets) >= 2:
                order = 1
            elif pcs & key_pcs:
                order = 2
            else:
                order = 3                                  # shares no note with the key
            todo.append((order, r, q))
    for order, r, q in sorted(todo):
        # third-order chords touch no key point; place them against the chords already placed
        near = ({p for (o, _, pl) in placed.values() if pl[0] != "dim" for p in tri(*pl)}
                if order == 3 else set())
        rows_b = {p[1] for p in near}                    # stay inside the rows already in use
        k = "up" if q == "" else "dn"
        best = None
        for a in range(M[0] - 9, M[0] + 10):
            for b in range(M[1] - 4, M[1] + 5):
                pts = tri(k, a, b)
                if fret(pts[0]) != r:
                    continue
                mx = sum(xy_(p)[0] for p in pts) / 3 - cx
                my = sum(xy_(p)[1] for p in pts) / 3 - cy
                out = sum(p[1] not in rows_b for p in pts) if near else 0
                score = (-len(set(pts) & key_pts), out, -len(set(pts) & near), mx * mx + my * my)
                if best is None or score < best[0]:
                    best = (score, (k, a, b))
        placed[(r, q)] = (order, "", best[1])
    rows = []
    key_chords = [chord(r, q) for (r, q), (o, _, _) in placed.items() if o == 0]
    for (r, q), (order, rn, place) in placed.items():
        Y = chord(r, q)
        t_key = min(td(K, Y)[0] for K in key_chords)       # TD to the nearest chord of the key
        v, vm = vl(X, Y)
        t, tm = td(X, Y)
        t12 = td12(X, Y)[0]
        nm = name(r, q) if q == "°" else spell(*tri(*place)[0]) + q
        alt = "" if q == "°" else next((x + q for x in (SHARP[r], FLAT[r]) if x + q != nm), "")
        rows.append(dict(chord=nm, alt=alt, root=r, kind=q, order=order, key=rn or "",
                         home=(r, q) == (root, kind), place=place, vl=v, td=round(t, 2),
                         td_key=round(t_key, 2), td12=round(t12, 2),
                         shared=len({fret(p) for p in X} & {fret(p) for p in Y}),
                         vl_moves=[f"{NAMES[a]}→{NAMES[b]} ({n})" for a, b, n in vm],
                         td_moves=[f"{NAMES[a]}→{NAMES[b]} ({lim})" for a, b, lim, _ in tm]))
    return sorted(rows, key=lambda x: (x["order"], x["td12"], x["vl"], x["chord"]))


def tile(rows):
    """The torus tile around a key (Chapter 5, "The whole map"): 24 places, every major and minor
    chord once. The middle row is the key's six triangles; nine run below from the left of IV's
    neighbour, nine above from one step further left. Neighbourhood maps draw a copy outside it
    dimmed (Zahid 2026-10-19), so the full-strength chords are exactly the whole-map tile."""
    key = [r["place"] for r in rows if r["order"] == 0 and r["place"][0] != "dim"]
    (b0,) = {b for _, _, b in key}
    a0 = min(a for k, a, _ in key if k == "up")

    def row(b, a, k):
        out = []
        while len(out) < 9:
            out.append((k, a, b))
            k, a = ("dn", a) if k == "up" else ("up", a + 1)
        return out
    return set(row(b0 - 1, a0 - 1, "up")) | set(key) | set(row(b0 + 1, a0 - 2, "dn"))


def spell(a, b):
    """Letter name of grid point (a, b), spelled along the line of fifths (C = 0)."""
    n = a + 4 * b
    acc = (n + 1) // 7
    return "FCGDAEB"[(n + 1) % 7] + ("♯" * acc if acc > 0 else "♭" * -acc)


def xy_(p):
    """Drawing coordinates of a grid point (the book's slanted grid, 70°)."""
    from math import sqrt
    c = L3 / (2 * L5)
    return p[0] * L3 + p[1] * L5 * c, p[1] * L5 * sqrt(1 - c * c)


def group(r):
    return ("smooth" if r["vl"] <= SMOOTH_MAX else "leap") + ", " + band(r["td12"])


# The visual code shared by every distance chart and by book_widgets.js (Zahid, 2026-10-12):
# two quantities, two channels, ONE configuration used everywhere in the book.
#   colour  = one quantity on a continuous, perceptually ordered colour map (Parula by default)
#   pattern = the other quantity in buckets: none / sparse / dense
# ENCODING is the default; the HTML book lets the reader change all four keys (stored in the
# browser), and every chart and widget redraws with the same choice.
ENCODING = {"cmap": "parula", "colour_by": "td", "pattern": "dots", "reverse": False,
            "note_colour": False}  # note circles painted in the same code, off by default (Zahid 2026-10-12)
RANGE = {"td": (0.0, 12.0), "vl": (0.0, 6.0)}          # the colour map spans these values
TD_BANDS = [(5.5, "near"), (7.5, "far"), (float("inf"), "remote")]
BAND_TEXT = {"near": "near: TD < 5.5", "far": "far: TD 5.5–7.5", "remote": "remote: TD ≥ 7.5"}
SMOOTH_MAX = 2
QUANTITY = {"td": "TD, how far the harmony moves", "vl": "VL, how far the fingers move"}

# MATLAB's Parula, 64 entries.
PARULA = [
    (0.2081, 0.1663, 0.5292), (0.2116, 0.1898, 0.5777), (0.2123, 0.2138, 0.6270), (0.2081, 0.2386, 0.6771),
    (0.1959, 0.2645, 0.7279), (0.1707, 0.2919, 0.7792), (0.1253, 0.3242, 0.8303), (0.0591, 0.3598, 0.8683),
    (0.0117, 0.3875, 0.8820), (0.0060, 0.4086, 0.8828), (0.0165, 0.4266, 0.8786), (0.0329, 0.4430, 0.8720),
    (0.0498, 0.4586, 0.8641), (0.0629, 0.4737, 0.8554), (0.0723, 0.4887, 0.8467), (0.0779, 0.5040, 0.8384),
    (0.0793, 0.5200, 0.8312), (0.0749, 0.5375, 0.8263), (0.0641, 0.5570, 0.8240), (0.0488, 0.5772, 0.8228),
    (0.0343, 0.5966, 0.8199), (0.0265, 0.6137, 0.8135), (0.0239, 0.6287, 0.8038), (0.0231, 0.6418, 0.7913),
    (0.0228, 0.6535, 0.7768), (0.0267, 0.6642, 0.7607), (0.0384, 0.6743, 0.7436), (0.0590, 0.6838, 0.7254),
    (0.0843, 0.6928, 0.7062), (0.1133, 0.7015, 0.6859), (0.1453, 0.7098, 0.6646), (0.1801, 0.7177, 0.6424),
    (0.2178, 0.7250, 0.6193), (0.2586, 0.7317, 0.5954), (0.3022, 0.7376, 0.5712), (0.3482, 0.7424, 0.5473),
    (0.3953, 0.7459, 0.5244), (0.4420, 0.7481, 0.5033), (0.4871, 0.7491, 0.4840), (0.5300, 0.7491, 0.4661),
    (0.5709, 0.7485, 0.4494), (0.6099, 0.7473, 0.4337), (0.6473, 0.7456, 0.4188), (0.6834, 0.7435, 0.4044),
    (0.7184, 0.7411, 0.3905), (0.7525, 0.7384, 0.3768), (0.7858, 0.7356, 0.3633), (0.8185, 0.7327, 0.3498),
    (0.8507, 0.7299, 0.3360), (0.8824, 0.7274, 0.3217), (0.9139, 0.7258, 0.3063), (0.9450, 0.7261, 0.2886),
    (0.9739, 0.7314, 0.2666), (0.9938, 0.7455, 0.2403), (0.9990, 0.7653, 0.2164), (0.9955, 0.7861, 0.1967),
    (0.9880, 0.8066, 0.1794), (0.9789, 0.8271, 0.1633), (0.9697, 0.8481, 0.1475), (0.9626, 0.8705, 0.1309),
    (0.9589, 0.8949, 0.1132), (0.9598, 0.9218, 0.0948), (0.9661, 0.9514, 0.0755), (0.9763, 0.9831, 0.0538)]
# the choices offered in the book; (matplotlib name or table, low end, high end) — the ends of
# magma/inferno are trimmed so the darkest swatch still shows its pattern and label
CMAPS = {"parula": ("Parula", PARULA, 0.0, 1.0), "viridis": ("Viridis", "viridis", 0.0, 1.0),
         "cividis": ("Cividis (colour-blind safe)", "cividis", 0.0, 1.0),
         "plasma": ("Plasma", "plasma", 0.0, 0.94), "magma": ("Magma", "magma", 0.18, 0.97),
         "inferno": ("Inferno", "inferno", 0.15, 0.95), "grey": ("Grey", "Greys_r", 0.18, 0.92)}
# the pattern is dots only; their density counts the pattern quantity in up to 6 steps
# (Zahid 2026-10-19: VL <= SMOOTH_MAX is one class, no dots; above it each fret is a clearly distinct
# step. Densities 4-6 blur into a tint, so VL 3/4/5/6 take levels 1/2/3/5: the key chart only
# reaches VL 5, and the jump to 5 keeps VL 6 apart from VL 5 in the full chord chart)
PATTERNS = {"dots": "Dots"}
MAX_LEVEL = 6
VL_DOTS = [0, 0, 0, 1, 2, 3, 5]                     # dot level for VL 0..6


def hatch(lv):
    """matplotlib hatch for a dot-density level 1-6 (each extra '.' adds a row of dots)."""
    return "." * lv


def cmap_stops(key, n=33):
    """n evenly spaced colours of a colour map, as hex, low end first."""
    import matplotlib
    from matplotlib.colors import LinearSegmentedColormap, to_hex
    _, src, lo, hi = CMAPS[key]
    cm = LinearSegmentedColormap.from_list(key, src) if isinstance(src, list) else matplotlib.colormaps[src]
    return [to_hex(cm(lo + (hi - lo) * i / (n - 1))) for i in range(n)]


def band(t):
    return next(name for hi, name in TD_BANDS if t < hi)


def level(v, t, enc=ENCODING):
    """Dot-density level 0-6 of a chord or note. The dots carry whichever quantity the colour does
    not: VL through VL_DOTS (no dots while smooth, VL <= 2), or TD by band (near 0, far 3, remote 6)."""
    if enc["colour_by"] == "td":
        return VL_DOTS[max(0, min(len(VL_DOTS) - 1, int(round(v))))]
    return (0, 3, 6)[[b for _, b in TD_BANDS].index(band(t))]


def colour(v, t, enc=ENCODING):
    """Fill colour of a chord at (VL v, TD t) under the encoding."""
    from matplotlib.colors import to_hex, to_rgb
    q = enc["colour_by"]
    lo, hi = RANGE[q]
    x = min(1.0, max(0.0, ((t if q == "td" else v) - lo) / (hi - lo)))
    if enc.get("reverse"):
        x = 1 - x
    stops = cmap_stops(enc["cmap"])
    f = x * (len(stops) - 1)
    i = min(int(f), len(stops) - 2)
    c0, c1 = to_rgb(stops[i]), to_rgb(stops[i + 1])
    return to_hex(tuple(a + (b - a) * (f - i) for a, b in zip(c0, c1)))


def ink(hexcol):
    """Pattern ink for a fill: dark lines on light fills, light lines on dark ones."""
    from matplotlib.colors import to_rgb
    r, g, b = to_rgb(hexcol)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return (0, 0, 0, 0.42) if lum > 0.45 else (1, 1, 1, 0.62)


def level_text(enc=ENCODING):
    """Legend text for each pattern level."""
    if enc["colour_by"] == "td":
        return [f"0–{SMOOTH_MAX}"] + [str(v) for v in range(SMOOTH_MAX + 1, len(VL_DOTS))]
    return [BAND_TEXT[b] for _, b in TD_BANDS]


def paint_patch(ax, pts, v, t, enc=ENCODING, edge="white", lw=1.5, z=1.5):
    """A polygon in the shared code: colour fill, then the pattern overlay for its level."""
    from matplotlib.patches import Polygon
    fc = colour(v, t, enc)
    ax.add_patch(Polygon(pts, fc=fc, ec="none", zorder=z))
    lv = level(v, t, enc)
    if lv:
        ax.add_patch(Polygon(pts, fc="none", ec=ink(fc), hatch=hatch(lv),
                             lw=0, zorder=z + 0.05))
    if edge:
        ax.add_patch(Polygon(pts, fc="none", ec=edge, lw=lw, zorder=z + 0.1))


def colourbar(fig, rect, enc=ENCODING):
    """A horizontal colour bar for the coloured quantity, with the TD bands marked."""
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap
    ax = fig.add_axes(rect)
    q = enc["colour_by"]
    lo, hi = RANGE[q]
    stops = cmap_stops(enc["cmap"])
    if enc.get("reverse"):
        stops = stops[::-1]
    ax.imshow(np.linspace(0, 1, 256)[None, :], aspect="auto", extent=(lo, hi, 0, 1),
              cmap=LinearSegmentedColormap.from_list("e", stops))
    ax.set_yticks([])
    ticks = list(range(int(lo), int(hi) + 1))
    ax.set_xticks(ticks, [str(x) for x in ticks[:-1]] + [f"{ticks[-1]}+"])   # the top colour also covers beyond
    ax.tick_params(labelsize=10, colors="#52514e", length=3)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title("colour = " + QUANTITY[q], fontsize=11, color="#1a202c", loc="left", pad=4)
    if q == "td":
        for x in (5.5, 7.5):
            ax.axvline(x, color="white", lw=1.4)
        for x, s in ((2.75, "near"), (6.5, "far"), (8.5, "remote")):
            ax.text(x, 0.5, s, ha="center", va="center", fontsize=9.5, color="white",
                    weight="bold")
    return ax


def pattern_key(fig, rect, enc=ENCODING):
    """Grey swatches, one per pattern level, labelled."""
    from matplotlib.patches import Polygon
    ax = fig.add_axes(rect)
    ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    labs = level_text(enc)
    vl = enc["colour_by"] == "td"
    ax.text(0, 0.98, "dots = VL, frets the fingers move" if vl else "dots = " + QUANTITY["td"],
            fontsize=11, color="#1a202c", va="top")
    levels = VL_DOTS[SMOOTH_MAX:] if vl else [0, 3, 6]
    w = 1 / len(labs)
    for i, (s, lv) in enumerate(zip(labs, levels)):
        x = i * w
        sw = w * (0.7 if vl else 0.28)
        pts = [(x, 0.22), (x + sw, 0.22), (x + sw, 0.68), (x, 0.68)]
        ax.add_patch(Polygon(pts, fc="#c9ced6", ec="#9aa3b0", lw=0.8))
        if lv:
            ax.add_patch(Polygon(pts, fc="none", ec=(0, 0, 0, 0.55), lw=0, hatch=hatch(lv)))
        ax.text(x + sw / 2 if vl else x + w * 0.32, 0.17 if vl else 0.45, s, fontsize=10.5,
                color="#1a202c", va="top" if vl else "center", ha="center" if vl else "left")
    return ax


def write_js_palette():
    """Copy ENCODING, ranges, bands and every colour map's stops into book_widgets.js, so the
    HTML draws exactly as the static charts do."""
    js = Path(__file__).parent / "book_widgets.js"
    s = js.read_text()
    data = {"default": ENCODING, "range": RANGE, "smoothMax": SMOOTH_MAX, "vlDots": VL_DOTS, "etdFret": ETD_FRET,
            "bands": [[None if hi == float("inf") else hi, b] for hi, b in TD_BANDS],
            "cmaps": {k: {"label": v[0], "stops": cmap_stops(k)} for k, v in CMAPS.items()},
            "patterns": PATTERNS}
    a, b = s.index("/*PALETTE*/"), s.index("/*END PALETTE*/")
    js.write_text(s[:a] + "/*PALETTE*/" + json.dumps(data, ensure_ascii=False) + s[b:])


def chart(rows):
    import matplotlib.pyplot as plt
    from matplotlib import patheffects
    plt.rcParams["hatch.linewidth"] = 0.8
    INK, MUTED, GRID = "#1a202c", "#52514e", "#e2e8f0"
    fig, ax = plt.subplots(figsize=(11.5, 7.6))
    fig.subplots_adjust(left=0.08, right=0.97, top=0.83, bottom=0.19)
    fig.text(0.08, 0.95, "From C: the key of C and its neighbourhood, two distances each",
             fontsize=17, weight="bold", color=INK)
    fig.text(0.08, 0.875, "Across: voice leading in frets (VL), how far the fingers move.\n"
             "Up: tonal distance in 12-TET (TD, Appendix B), how far the harmony moves. Colour and pattern follow the "
             "book's display setting (default: colour = TD, pattern = VL).", fontsize=11, color=MUTED)
    ax.axvline(2.5, color=GRID, lw=1.5, zorder=0)
    for y in (5.5, 7.5):
        ax.axhline(y, color=GRID, lw=1.5, zorder=0)
    for x, y, t, ha in ((0.6, 2.75, "smooth, near", "left"), (6.4, 2.75, "leap, near", "right"),
                        (0.6, 12.35, "smooth, remote", "left"), (6.4, 12.35, "leap, remote", "right")):
        ax.text(x, y, t, ha=ha, va="center", fontsize=12, color=MUTED, style="italic")
    seen = {}
    for r in rows:
        seen.setdefault((r["vl"], r["td12"]), []).append(r)
    halo = [patheffects.withStroke(linewidth=3, foreground="white")]
    for (x, y), rs in seen.items():
        n = len(rs)
        for i, r in enumerate(sorted(rs, key=lambda r: r["chord"])):
            xx = x + (i - (n - 1) / 2) * (0.34 if any(q["key"] for q in rs) else 0.2)
            mk = {"": "^", "m": "v", "°": "D"}[r["kind"]]
            fc, lv, size = colour(r["vl"], r["td12"]), level(r["vl"], r["td12"]), 300 if r["key"] else 240
            ax.scatter([xx], [y], s=size, marker=mk, color=fc, linewidth=0, zorder=3)
            if lv:
                ax.scatter([xx], [y], s=size, marker=mk, facecolor="none", edgecolor=ink(fc),
                           hatch=hatch(lv), linewidth=0, zorder=3.05)
            ax.scatter([xx], [y], s=size, marker=mk, facecolor="none",
                       edgecolor="#000000" if r["key"] else fc,
                       linewidth=2.4 if r["key"] else 1.0, zorder=3.1)
            lab = r["chord"] + (f" {r['key']}" if r["key"] else "")
            ax.text(xx, y + 0.32, lab, ha="center", va="bottom", fontsize=11.5, color=INK,
                    weight="bold", zorder=4, path_effects=halo)
    ax.set_xlim(0.5, 6.5); ax.set_ylim(2.5, 12.6)
    ax.set_xticks([1, 2, 3, 4, 5, 6])
    ax.set_xlabel("VL: frets moved, all voices (smooth ← → leap)", fontsize=11, color=MUTED)
    ax.set_ylabel("TD in 12-TET, summed over voices (near ↓  ↑ remote)", fontsize=11, color=MUTED)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color("#a0aec0")
    ax.tick_params(colors=MUTED)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(fc="white", ec="#000000", lw=2, label="in the key of C (numeral)")],
              loc="lower right", bbox_to_anchor=(1.0, 0.1), frameon=False, fontsize=10.5,
              labelcolor=MUTED)
    colourbar(fig, [0.47, 0.035, 0.30, 0.03])
    pattern_key(fig, [0.80, 0.0, 0.19, 0.075])
    for ext in ("svg", "png"):
        fig.savefig(OUT / f"chord-distance-c.{ext}", facecolor="white",
                    dpi=110 if ext == "png" else None)
    plt.close(fig)
    print(OUT / "chord-distance-c.png")


def check_js():
    """Compare the HTML book's JS implementation against this file for every pair of triads."""
    js = Path(__file__).parent / "book_widgets.js"
    script = js.read_text() + """
const out = {};
for (let r1 = 0; r1 < 12; r1++) for (const k1 of ['', 'm', '°'])
  for (let r2 = 0; r2 < 12; r2++) for (const k2 of ['', 'm', '°']) {
    const X = CD.chord(r1, k1), Y = CD.chord(r2, k2);
    out[`${r1}${k1}|${r2}${k2}`] = [CD.vl(X, Y).total, +CD.td(X, Y).total.toFixed(4)];
  }
console.log(JSON.stringify(out));
"""
    res = json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True,
                                    check=True).stdout)
    bad = 0
    for r1 in range(12):
        for k1 in ("", "m", "°"):
            for r2 in range(12):
                for k2 in ("", "m", "°"):
                    X, Y = chord(r1, k1), chord(r2, k2)
                    want = [vl(X, Y)[0], round(td(X, Y)[0], 4)]
                    got = res[f"{r1}{k1}|{r2}{k2}"]
                    if abs(want[0] - got[0]) > 0 or abs(want[1] - got[1]) > 1e-3:
                        bad += 1
                        print("MISMATCH", name(r1, k1), name(r2, k2), want, got)
    print(f"JS check: {1296 - bad}/1296 pairs agree")
    script = js.read_text() + """
const out = {};
for (let r = 0; r < 12; r++) for (const k of ['', 'm'])
  out[`${r}${k}`] = CD.neighbourhood(r, k).map(x => [x.chord, x.order, x.key, x.place.join(','), x.vl, +x.td.toFixed(2), +x.tdKey.toFixed(2), +x.td12.toFixed(2)]);
console.log(JSON.stringify(out));
"""
    res = json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True,
                                    check=True).stdout)
    nbad = 0
    for r in range(12):
        for k in ("", "m"):
            want = [[x["chord"], x["order"], x["key"], ",".join(map(str, x["place"])), x["vl"], x["td"], x["td_key"], x["td12"]]
                    for x in neighbourhood(r, k)]
            if want != res[f"{r}{k}"]:
                nbad += 1
                print("NEIGHBOURHOOD MISMATCH", name(r, k))
    print(f"JS check: {24 - nbad}/24 neighbourhoods agree")
    script = js.read_text() + """
const out = {};
for (let r = 0; r < 12; r++) for (const k of ['', 'm'])
  out[`${r}${k}`] = [...CD.tile(CD.neighbourhood(r, k))].sort();
console.log(JSON.stringify(out));
"""
    res = json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True,
                                    check=True).stdout)
    tbad = 0
    for r in range(12):
        for k in ("", "m"):
            T = tile(neighbourhood(r, k))
            chords = {((7 * tri(*pl)[0][0] + 4 * tri(*pl)[0][1]) % 12, pl[0]) for pl in T}
            if sorted(",".join(map(str, pl)) for pl in T) != res[f"{r}{k}"] or len(chords) != 24:
                tbad += 1
                print("TILE MISMATCH", name(r, k))
    print(f"JS check: {24 - tbad}/24 tiles agree, each with all 24 chords once")
    shells = 0
    for r in range(12):
        for k in ("", "m"):
            rows = neighbourhood(r, k)
            hi = [max((x["td_key"] for x in rows if x["order"] == o), default=0) for o in (0, 1, 2, 3)]
            lo = [min((x["td_key"] for x in rows if x["order"] == o), default=0) for o in (0, 1, 2, 3)]
            shells += hi[0] < lo[1] and hi[1] < lo[2] and hi[2] < lo[3]
    print(f"Shell check (TD to the key strictly grows with order): {shells}/24 homes")
    return bad == 0 and nbad == 0


if __name__ == "__main__":
    if "--check-js" in sys.argv:
        sys.exit(0 if check_js() else 1)
    rows = [r for r in neighbourhood(0, "") if not r["home"]]
    for r in rows:
        print(f"| {r['chord'] + (' / ' + r['alt'] if r['alt'] else '')} | {r['key']} | {r['order']} | {r['shared']} | {r['vl']} | {', '.join(r['vl_moves'])} | "
              f"{r['td12']:.2f} | {r['td']:.2f} | {', '.join(r['td_moves'])} | {r['td_key']:.2f} | {group(r)} |")
    chart(rows)
    write_js_palette()
