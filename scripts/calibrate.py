"""Sanity-check the handicap model in ``sg.py``.

The expected-strokes table for a tee shot *is* the expected score for the hole,
so summing it over a course gives the model's predicted scoring average. If a
14 index does not come out somewhere near 86 on a normal par 72, the ``SPREAD``
coefficients are wrong and every strokes-gained number downstream is wrong too.

Run it after touching ``BENCHMARK`` or ``SPREAD``::

    python3 scripts/calibrate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sg import hole_baseline  # noqa: E402

# A generic par 72: four par 3s, ten par 4s, four par 5s, 6,600 yards.
COURSE = [
    (4, 380), (4, 410), (3, 165), (5, 530), (4, 395), (4, 350),
    (3, 190), (4, 440), (5, 555), (4, 415), (4, 360), (3, 145),
    (5, 505), (4, 425), (4, 390), (3, 175), (5, 545), (4, 400),
]

#: What each index is actually expected to shoot on a course like that.
#: Source: USGA handicap-to-score research -- a player shoots their index over
#: course rating only about one round in five; the *average* differential runs
#: roughly three strokes higher.
TARGETS = {0: 71.0, 5: 77.5, 10: 82.5, 14: 86.5, 18: 90.5, 25: 98.0}


def predicted_score(handicap: float, course=COURSE) -> float:
    return sum(hole_baseline(yards, handicap, par) for par, yards in course)


def main() -> int:
    par = sum(p for p, _ in COURSE)
    yards = sum(y for _, y in COURSE)
    print(f"course: par {par}, {yards:,} yards\n")
    print(f"{'index':>6} {'predicted':>10} {'target':>8} {'error':>7}")
    worst = 0.0
    for h, target in TARGETS.items():
        pred = predicted_score(h)
        err = pred - target
        worst = max(worst, abs(err))
        print(f"{h:>6} {pred:>10.1f} {target:>8.1f} {err:>+7.1f}")
    print(f"\nworst error: {worst:.1f} strokes")
    if worst > 2.0:
        print("FAIL: recalibrate SPREAD in scripts/sg.py")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
