"""Scoring model and round analysis.

The organising fact, measured over 95 complete rounds in ``data/rounds.csv``:

    score ~ doubles-or-worse      R^2 = 0.76      +2.1 strokes per double
    score ~ GIR                   R^2 = 0.55
    score ~ putts                 R^2 = 0.05
    score ~ fairways              R^2 = 0.03

Ball-striking is not the limiter. Disaster holes are. So the headline number
this file produces is not strokes gained -- it is :func:`round_underneath`, the
score with the doubles played as bogeys. That is the round that actually
happened underneath the blow-ups, and it is the honest version of "you played
better than the number says".

:func:`fit` re-derives the relationship from whatever data is in the log, so the
coefficients stay current as rounds are added rather than being frozen here.
"""

from __future__ import annotations

import csv
import datetime as dt
import statistics
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROUNDS_CSV = ROOT / "data" / "rounds.csv"

#: Rounds before this date predate detailed stat capture -- fairways, putts and
#: up-and-down are blank or unreliable. Trend work filters to this onward.
COMPLETE_STATS_FROM = "2026-07-31"


def _num(v, cast=float):
    if v in (None, "", "None"):
        return None
    try:
        return cast(v)
    except (TypeError, ValueError):
        return None


@dataclass
class Round:
    date: str
    course: str = ""
    tee: str = ""
    score: int | None = None
    par: int | None = None
    holes: int | None = None
    yards: int | None = None
    front: int | None = None
    back: int | None = None
    fairways_hit: int | None = None
    fairways_total: int | None = None
    fairways_left: int | None = None
    fairways_right: int | None = None
    gir: int | None = None
    gir_short: int | None = None
    gir_long: int | None = None
    putts: int | None = None
    three_putts: int | None = None
    penalties: int | None = None
    up_down_pct: float | None = None
    birdies: int | None = None
    pars: int | None = None
    bogeys: int | None = None
    doubles_or_worse: int | None = None
    app_handicap: float | None = None
    source: str = ""
    notes: str = ""

    @property
    def is_full(self) -> bool:
        return self.holes == 18 and self.score is not None

    @property
    def to_par(self) -> int | None:
        if self.score is None or self.par is None:
            return None
        return self.score - self.par

    @property
    def disaster_strokes(self) -> int | None:
        """Strokes given away on double-or-worse holes, over par.

        ``to_par = -birdies + bogeys + (strokes over par on the disaster
        holes)``, so the last term falls out of the other three.
        """
        if None in (self.to_par, self.birdies, self.bogeys):
            return None
        return self.to_par + self.birdies - self.bogeys

    @property
    def round_underneath(self) -> int | None:
        """The score with every double-or-worse hole played as a bogey.

        Not a hypothetical good round -- it still counts every bogey, every
        missed green, every three-putt. It only removes the damage past bogey.
        """
        d = self.disaster_strokes
        if d is None or self.doubles_or_worse is None:
            return None
        return self.score - (d - self.doubles_or_worse)

    @property
    def scrambling_holes(self) -> int | None:
        if self.gir is None:
            return None
        return (self.holes or 18) - self.gir


def load(path: Path = ROUNDS_CSV) -> list[Round]:
    rows = []
    with path.open() as fh:
        for r in csv.DictReader(fh):
            rows.append(Round(
                date=r["date"], course=r.get("course", ""), tee=r.get("tee", ""),
                score=_num(r.get("score"), int), par=_num(r.get("par"), int),
                holes=_num(r.get("holes"), int), yards=_num(r.get("yards"), int),
                front=_num(r.get("front"), int), back=_num(r.get("back"), int),
                fairways_hit=_num(r.get("fairways_hit"), int),
                fairways_total=_num(r.get("fairways_total"), int),
                fairways_left=_num(r.get("fairways_left"), int),
                fairways_right=_num(r.get("fairways_right"), int),
                gir=_num(r.get("gir"), int),
                gir_short=_num(r.get("gir_short"), int),
                gir_long=_num(r.get("gir_long"), int),
                putts=_num(r.get("putts"), int),
                three_putts=_num(r.get("three_putts"), int),
                penalties=_num(r.get("penalties"), int),
                up_down_pct=_num(r.get("up_down_pct")),
                birdies=_num(r.get("birdies"), int), pars=_num(r.get("pars"), int),
                bogeys=_num(r.get("bogeys"), int),
                doubles_or_worse=_num(r.get("doubles_or_worse"), int),
                app_handicap=_num(r.get("app_handicap")),
                source=r.get("source", ""), notes=r.get("notes", ""),
            ))
    return sorted(rows, key=lambda r: r.date)


# --------------------------------------------------------------------------
# Regression
# --------------------------------------------------------------------------

@dataclass
class Fit:
    slope: float
    intercept: float
    r2: float
    n: int
    predictor: str

    def predict(self, x: float) -> float:
        return self.intercept + self.slope * x

    def __str__(self) -> str:
        return (f"score = {self.intercept:.1f} + {self.slope:+.2f} x {self.predictor}"
                f"  (R^2={self.r2:.2f}, n={self.n})")


def fit(rounds: list[Round], predictor: str = "doubles_or_worse") -> Fit | None:
    """Least-squares fit of score against one predictor."""
    pairs = [(getattr(r, predictor), r.score) for r in rounds
             if r.is_full and getattr(r, predictor) is not None]
    if len(pairs) < 3:
        return None
    xs = [float(x) for x, _ in pairs]
    ys = [float(y) for _, y in pairs]
    if len(set(xs)) < 2:
        return None
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = my - slope * mx
    syy = sum((y - my) ** 2 for y in ys)
    r2 = (sxy ** 2) / (sxx * syy) if syy else 0.0
    return Fit(slope, intercept, r2, len(pairs), predictor)


def predict_score(rounds: list[Round], doubles: float,
                  spread: float = 1.0) -> tuple[float, float, float]:
    """Predicted score for a target number of doubles, as (low, mid, high).

    ``spread`` is in residual standard deviations. He uses the range as a target
    to beat, so it should be a real interval, not a point estimate dressed up.
    """
    f = fit(rounds)
    if f is None:
        raise ValueError("not enough rounds to fit a model")
    mid = f.predict(doubles)
    resid = [r.score - f.predict(r.doubles_or_worse) for r in rounds
             if r.is_full and r.doubles_or_worse is not None]
    sd = statistics.pstdev(resid) if len(resid) > 1 else 3.0
    return mid - spread * sd, mid, mid + spread * sd


# --------------------------------------------------------------------------
# Context flags -- the non-golf variables that move his scores
# --------------------------------------------------------------------------

def days_played_streak(rounds: list[Round], upto: str) -> int:
    """How many consecutive days of golf this round is the end of.

    Confirmed in the coaching notes: the 91 came on the fourth straight day.
    Fatigue is worth 5-10 strokes, so it gets checked before a swing is blamed.
    """
    dates = {dt.date.fromisoformat(r.date) for r in rounds if r.date <= upto}
    day = dt.date.fromisoformat(upto)
    streak = 0
    while day in dates:
        streak += 1
        day -= dt.timedelta(days=1)
    return streak


def is_first_visit(rounds: list[Round], r: Round) -> bool:
    """First time on this course. Historically worth 4-8 strokes."""
    if not r.course:
        return False
    return not any(o.course == r.course and o.date < r.date for o in rounds)


def layoff_days(rounds: list[Round], r: Round) -> int | None:
    prior = [o for o in rounds if o.date < r.date]
    if not prior:
        return None
    return (dt.date.fromisoformat(r.date)
            - dt.date.fromisoformat(prior[-1].date)).days


def flags(rounds: list[Round], r: Round) -> list[str]:
    """Context that should be read before diagnosing a swing."""
    out = []
    streak = days_played_streak(rounds, r.date)
    if streak >= 3:
        out.append(f"day {streak} of consecutive golf (fatigue: 5-10 strokes)")
    if is_first_visit(rounds, r):
        out.append("first time on this course (historically 4-8 strokes)")
    lay = layoff_days(rounds, r)
    if lay is not None and lay >= 21:
        out.append(f"{lay} days since previous round (rust)")
    if r.penalties is not None and r.penalties >= 3:
        out.append(f"{r.penalties} penalty strokes")
    if r.three_putts is not None and r.three_putts >= 4:
        out.append(f"{r.three_putts} three-putts")
    return out


# --------------------------------------------------------------------------
# Summaries
# --------------------------------------------------------------------------

def recent(rounds: list[Round], n: int = 10) -> list[Round]:
    return [r for r in rounds if r.is_full][-n:]


def floor_ceiling(rounds: list[Round], n: int = 10) -> dict:
    """Working range from the last ``n`` full rounds.

    Ceiling is the best round, floor the worst; ``typical`` is the median, which
    is more honest than the mean when one blow-up round is in the window.
    """
    rs = recent(rounds, n)
    scores = sorted(r.score for r in rs)
    if not scores:
        return {}
    return {
        "n": len(scores),
        "ceiling": scores[0],
        "floor": scores[-1],
        "typical": statistics.median(scores),
        "mean": round(statistics.mean(scores), 1),
    }


def averages(rounds: list[Round], n: int = 10) -> dict:
    """Mean of each tracked stat over the last ``n`` full rounds."""
    rs = recent(rounds, n)
    out = {}
    for key in ("score", "doubles_or_worse", "gir", "putts", "three_putts",
                "penalties", "fairways_hit", "up_down_pct", "birdies", "pars"):
        vals = [getattr(r, key) for r in rs if getattr(r, key) is not None]
        if vals:
            out[key] = round(statistics.mean(vals), 1)
    under = [r.round_underneath for r in rs if r.round_underneath is not None]
    if under:
        out["round_underneath"] = round(statistics.mean(under), 1)
    return out


def miss_bias(rounds: list[Round], n: int = 10) -> dict:
    """Which way the misses go -- the hook shows up here as left tee misses."""
    rs = recent(rounds, n)
    def total(key):
        return sum(getattr(r, key) or 0 for r in rs)
    return {
        "tee_left": total("fairways_left"),
        "tee_right": total("fairways_right"),
        "approach_short": total("gir_short"),
        "approach_long": total("gir_long"),
    }
