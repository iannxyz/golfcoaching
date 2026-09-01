"""Strokes gained engine.

Two levels of fidelity:

1. :func:`sg_from_shots` -- true strokes gained. Needs a start lie and distance
   for every shot. Exact, but you have to log shot by shot.
2. :func:`sg_from_scorecard` -- an *estimate* of the four categories from the
   stats a scorecard photo actually gives you (score, par, fairway, GIR, putts,
   penalties). Less precise, but it is what you can produce from a phone photo
   in thirty seconds.

The model in three pieces
------------------------
**Benchmark.** :data:`BENCHMARK` holds expected strokes to hole out for a PGA
Tour field, by lie and distance -- approximating the tables published in Mark
Broadie's *Every Shot Counts*. Every shot-level number is measured against this
and this only. One fixed table means shot-level SG telescopes correctly: the
categories always sum to (benchmark score - actual score), with no leftover.

**Hole model.** :func:`hole_baseline` answers a different question -- what a
player of handicap ``h`` is expected to *score* on a hole of a given length.
It stretches the tee benchmark by a factor fitted to published handicap-to-score
data (see :data:`HOLE_STRETCH` and ``scripts/calibrate.py``). This absorbs both
effects that separate an amateur from a tour player: worse shots, and shorter
ones.

**Category baseline.** Comparing yourself to tour is demoralising and not very
actionable. :func:`category_baseline` splits the whole gap between your handicap
and the benchmark across the four categories, so ``sg_vs_handicap`` tells you
where you are beating or missing *your own level*. That is the number worth
practising against.

An earlier version of this file stretched each lie's table independently. Don't
go back to that: it makes the category split incoherent (a 210-yard drive into
the rough came out as a stroke *gained*), because the tee shot gets credit for
a gap the following shot's table no longer carries.
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Tour benchmark: distance (yards, or feet on the green) -> expected strokes
# --------------------------------------------------------------------------

BENCHMARK: dict[str, list[tuple[float, float]]] = {
    # Tee shot on a par 4 or 5. The value is the expected score for the hole.
    "tee": [
        (100, 2.92), (120, 2.99), (140, 2.97), (160, 2.99), (180, 3.05),
        (200, 3.12), (220, 3.17), (240, 3.25), (260, 3.45), (280, 3.65),
        (300, 3.71), (320, 3.79), (340, 3.86), (360, 3.92), (380, 3.98),
        (400, 4.04), (420, 4.08), (440, 4.12), (460, 4.17), (480, 4.22),
        (500, 4.28), (520, 4.34), (540, 4.40), (560, 4.45), (580, 4.51),
        (600, 4.58),
    ],
    "fairway": [
        (20, 2.40), (30, 2.52), (40, 2.60), (50, 2.66), (60, 2.70),
        (70, 2.72), (80, 2.75), (90, 2.77), (100, 2.80), (120, 2.85),
        (140, 2.91), (160, 2.98), (180, 3.06), (200, 3.15), (220, 3.23),
        (240, 3.32), (260, 3.42), (280, 3.51), (300, 3.62),
    ],
    "rough": [
        (20, 2.59), (30, 2.72), (40, 2.82), (50, 2.87), (60, 2.91),
        (70, 2.93), (80, 2.94), (90, 2.96), (100, 2.98), (120, 3.02),
        (140, 3.08), (160, 3.15), (180, 3.23), (200, 3.31), (220, 3.39),
        (240, 3.47), (260, 3.56), (280, 3.65), (300, 3.74),
    ],
    "sand": [
        (20, 2.53), (30, 2.66), (40, 2.82), (50, 2.92), (60, 3.00),
        (70, 3.03), (80, 3.06), (90, 3.08), (100, 3.09), (120, 3.15),
        (140, 3.22), (160, 3.29), (180, 3.36), (200, 3.44), (220, 3.53),
        (240, 3.61), (260, 3.70), (280, 3.79), (300, 3.88),
    ],
    # Trees, deep native, unplayable-adjacent: you are advancing, not attacking.
    "recovery": [
        (20, 3.00), (40, 3.20), (60, 3.30), (80, 3.40), (100, 3.45),
        (120, 3.51), (140, 3.57), (160, 3.64), (180, 3.71), (200, 3.79),
        (220, 3.87), (240, 3.95), (260, 4.03), (280, 4.11), (300, 4.20),
    ],
    # Putting: distance is in FEET, not yards. Derived from tour make rates --
    # at short range E = 2 - make%, with three-putts folded in past ~25 feet.
    "green": [
        (1, 1.001), (2, 1.010), (3, 1.040), (4, 1.120), (5, 1.230),
        (6, 1.340), (7, 1.420), (8, 1.500), (9, 1.550), (10, 1.600),
        (12, 1.690), (15, 1.780), (20, 1.870), (25, 1.930), (30, 1.980),
        (35, 2.030), (40, 2.070), (45, 2.110), (50, 2.140), (60, 2.210),
        (70, 2.270), (80, 2.340), (90, 2.400),
    ],
}

LIES = tuple(BENCHMARK)

#: Whole-hole stretch factor as a function of handicap index:
#: ``factor = HOLE_STRETCH[0] + HOLE_STRETCH[1] * handicap``. Least-squares fit
#: against published handicap-to-score data; ``scripts/calibrate.py`` re-runs the
#: check. Only the strokes *above* holing out are stretched.
HOLE_STRETCH: tuple[float, float] = (1.0349, 0.020469)

#: How the gap between a handicap and the tour benchmark divides across the four
#: categories. Approximates Broadie's amateur-vs-tour breakdown: the long game
#: is about two thirds of it, which is why "just work on your putting" is
#: usually bad advice.
GAP_WEIGHTS: dict[str, float] = {
    "ott": 0.27,
    "approach": 0.37,
    "short": 0.18,
    "putting": 0.18,
}

CATEGORIES = tuple(GAP_WEIGHTS)

#: Shots from a non-tee lie inside this many yards count as around-the-green.
ARG_YARDS = 30.0

#: The reference course the category baseline is scaled on: a par 72 of 6,600
#: yards. Rounds on much longer or shorter courses are scaled in
#: :func:`category_baseline` via their own par-and-yardage total.
REFERENCE_HOLES = [
    (4, 380), (4, 410), (3, 165), (5, 530), (4, 395), (4, 350),
    (3, 190), (4, 440), (5, 555), (4, 415), (4, 360), (3, 145),
    (5, 505), (4, 425), (4, 390), (3, 175), (5, 545), (4, 400),
]


def _interpolate(table: list[tuple[float, float]], d: float) -> float:
    """Linear interpolation, extrapolating along the end slope past the table."""
    if d <= table[0][0]:
        return table[0][1]
    if d >= table[-1][0]:
        (x0, y0), (x1, y1) = table[-2], table[-1]
        return y1 + (d - x1) * (y1 - y0) / (x1 - x0)
    i = bisect_left([x for x, _ in table], d)
    (x0, y0), (x1, y1) = table[i - 1], table[i]
    return y0 + (d - x0) * (y1 - y0) / (x1 - x0)


def expected_strokes(lie: str, distance: float) -> float:
    """Tour-benchmark strokes to hole out from ``lie`` at ``distance``.

    ``distance`` is yards for every lie except ``green``, which is feet.
    """
    lie = lie.lower()
    if lie == "holed":
        return 0.0
    if lie not in BENCHMARK:
        raise ValueError(f"unknown lie {lie!r}; expected one of {LIES}")
    if distance < 0:
        raise ValueError(f"negative distance: {distance}")
    return _interpolate(BENCHMARK[lie], distance)


def hole_baseline(yards: float, handicap: float, par: int | None = None) -> float:
    """Expected score on a hole of ``yards`` for a player of ``handicap``."""
    if not yards:
        yards = {3: 155.0, 4: 385.0, 5: 520.0}.get(par or 4, 385.0)
    tour = expected_strokes("tee", yards)
    a, b = HOLE_STRETCH
    return 1.0 + (tour - 1.0) * (a + b * handicap)


def round_baseline(holes, handicap: float) -> float:
    """Expected 18-hole score for ``handicap``. ``holes`` is (par, yards) pairs."""
    return sum(hole_baseline(y, handicap, p) for p, y in holes)


def category_baseline(handicap: float, holes=None) -> dict[str, float]:
    """Expected SG-vs-tour in each category for a player of ``handicap``.

    All four numbers are negative for any amateur -- they are how many strokes
    per round that handicap gives up to a tour field in each part of the game.
    Subtract them from measured SG-vs-tour to get SG against your own level.
    """
    holes = holes or REFERENCE_HOLES
    gap = round_baseline(holes, handicap) - round_baseline(holes, 0.0)
    # round_baseline at handicap 0 is still slightly above the raw tour table
    # (a scratch amateur is not a tour player); measure the gap from the table.
    gap = round_baseline(holes, handicap) - sum(
        expected_strokes("tee", y) for _, y in holes
    )
    return {c: -gap * w for c, w in GAP_WEIGHTS.items()}


def category_for(lie: str, distance: float, is_tee_shot: bool = False) -> str:
    """Bucket a shot into one of :data:`CATEGORIES`."""
    lie = lie.lower()
    if lie == "green":
        return "putting"
    if lie == "tee" or is_tee_shot:
        return "ott"
    if distance <= ARG_YARDS:
        return "short"
    return "approach"


# --------------------------------------------------------------------------
# Shot-level strokes gained
# --------------------------------------------------------------------------

@dataclass
class Shot:
    """One golf shot.

    ``lie``/``distance`` are where the shot *started*; ``end_lie``/
    ``end_distance`` where it finished. Use ``end_lie="holed"`` for the shot that
    goes in. ``penalty`` is strokes added for the shot: 1 for a lateral drop, 2
    for out of bounds under stroke and distance.
    """

    hole: int
    lie: str
    distance: float
    end_lie: str
    end_distance: float = 0.0
    penalty: int = 0

    @property
    def is_tee_shot(self) -> bool:
        return self.lie.lower() == "tee"


def sg_from_shots(shots: list[Shot], handicap: float | None = None,
                  holes=None) -> dict[str, float]:
    """True strokes gained per category, against the tour benchmark.

    For each shot::

        SG = E(start) - E(finish) - 1 - penalty

    Pass ``handicap`` to also get ``*_vs_handicap`` keys, which re-express the
    same round against a player of that index instead of a tour field.
    """
    out: dict[str, float] = {c: 0.0 for c in CATEGORIES}
    out["total"] = 0.0
    for s in shots:
        start = expected_strokes(s.lie, s.distance)
        end = expected_strokes(s.end_lie, s.end_distance)
        gained = start - end - 1 - s.penalty
        out[category_for(s.lie, s.distance, s.is_tee_shot)] += gained
        out["total"] += gained
    result = {k: round(v, 3) for k, v in out.items()}
    if handicap is not None:
        base = category_baseline(handicap, holes)
        for c in CATEGORIES:
            result[f"{c}_vs_handicap"] = round(out[c] - base[c], 3)
        result["total_vs_handicap"] = round(
            out["total"] - sum(base.values()), 3
        )
    return result


# --------------------------------------------------------------------------
# Scorecard-level strokes gained (estimate)
# --------------------------------------------------------------------------

@dataclass
class HoleStat:
    """What you can read off a scorecard photo for one hole."""

    hole: int
    par: int
    score: int
    yards: float | None = None
    putts: int | None = None
    fairway: bool | None = None      # None on a par 3 -- no fairway stat
    gir: bool | None = None
    penalties: int = 0
    sand: bool = False               # any bunker shot on the hole

    @property
    def to_par(self) -> int:
        return self.score - self.par


@dataclass
class RoundSG:
    ott: float = 0.0
    approach: float = 0.0
    short: float = 0.0
    putting: float = 0.0
    total: float = 0.0
    method: str = "estimated"
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "sg_ott": round(self.ott, 2),
            "sg_approach": round(self.approach, 2),
            "sg_short": round(self.short, 2),
            "sg_putting": round(self.putting, 2),
            "sg_total": round(self.total, 2),
            "sg_method": self.method,
        }


def expected_putts(gir: bool | None, handicap: float) -> float:
    """Baseline putts for a hole, given whether the green was hit in regulation.

    Non-GIR holes take *fewer* putts than GIR holes at every level: you have
    already chipped it close, or you are putting from six feet after a good
    pitch. Counting all putts against one flat number is the classic way to make
    a good short game look like good putting.
    """
    g = 1.87 + 0.13 * handicap / 18.0
    m = 1.71 + 0.10 * handicap / 18.0
    if gir is None:
        return (g + m) / 2
    return g if gir else m


def sg_from_scorecard(
    holes: list[HoleStat],
    handicap: float = 0.0,
    baseline_handicap: float | None = None,
) -> RoundSG:
    """Estimate the four SG categories from scorecard stats.

    ``handicap`` is who you are; ``baseline_handicap`` is who you are measuring
    against (defaults to the same, so a par-for-you round reads as 0.0). Set it
    to your *target* index to see the gap to the player you want to be.

    Method
    ------
    Putting and around-the-green come straight off the card. Off-the-tee comes
    from fairways and penalties. Approach is then the residual::

        SG_total = baseline_score - actual_score
        SG_app   = SG_total - SG_ott - SG_short - SG_putt

    Approach absorbs the model error, which is the right place for it: it is the
    largest category, so a given bias distorts it proportionally least. This is
    an estimate -- log shot-level data and use :func:`sg_from_shots` when you
    want the real number.
    """
    base_h = handicap if baseline_handicap is None else baseline_handicap
    sg = RoundSG(method="estimated")

    actual = sum(h.score for h in holes)
    baseline = sum(hole_baseline(h.yards or 0, base_h, h.par) for h in holes)
    sg.total = baseline - actual

    # --- putting -----------------------------------------------------------
    have_putts = [h for h in holes if h.putts is not None]
    if have_putts:
        for h in have_putts:
            sg.putting += expected_putts(h.gir, base_h) - h.putts
        if len(have_putts) < len(holes):
            sg.notes.append(f"putts on {len(have_putts)}/{len(holes)} holes")
    else:
        sg.notes.append("no putts recorded; SG-putting not separated")

    # --- around the green --------------------------------------------------
    # Scrambling: missed the green, still made par or better. A scratch player
    # gets up and down about 60% of the time, an 18 about 30%.
    misses = [h for h in holes if h.gir is False]
    if misses:
        saves = sum(1 for h in misses if h.to_par <= 0)
        base_rate = max(0.12, 0.60 - 0.017 * base_h)
        sg.short = saves - base_rate * len(misses)   # ~1 stroke per scramble
        sand_misses = sum(1 for h in misses if h.sand)
        if sand_misses:
            sg.notes.append(f"{sand_misses} bunker holes")
    elif any(h.gir is None for h in holes):
        sg.notes.append("no GIR recorded; SG-short not separated")

    # --- off the tee -------------------------------------------------------
    tee_holes = [h for h in holes if h.par >= 4 and h.fairway is not None]
    if tee_holes:
        hit = sum(1 for h in tee_holes if h.fairway)
        base_rate = max(0.25, 0.62 - 0.011 * base_h)
        sg.ott = 0.26 * (hit - base_rate * len(tee_holes))  # ~1/4 shot a fairway
    else:
        sg.notes.append("no fairway data; SG-off-the-tee is penalty-only")
    penalties = sum(h.penalties for h in holes)
    sg.ott -= penalties - (0.9 + 0.13 * base_h)   # baseline penalties per round

    # --- approach is the residual -----------------------------------------
    sg.approach = sg.total - sg.ott - sg.short - sg.putting
    return sg
