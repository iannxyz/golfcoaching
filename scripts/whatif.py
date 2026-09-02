"""What one more round does to the handicap index.

    PYTHONPATH=scripts python3 scripts/whatif.py            # a table of scores
    PYTHONPATH=scripts python3 scripts/whatif.py 80 Eastlake

The index here is the average of the best 8 differentials in the last 20
rounds. That is the shape of the WHS calculation, but not all of it -- the real
thing also applies playing-conditions adjustment and the soft/hard caps, which
are not modelled. Treat the output as the direction and size of a move, not as
a number to quote to a committee.

Course offsets are derived empirically: 18Birdies reports a per-round handicap
that behaves like a differential, so ``offset = score - differential`` averaged
over the rounds actually played there. That sidesteps needing published course
ratings and slopes, and it is calibrated to the tees he really plays.

The offset moves with the tee -- Campestre off the Azul tees rates about a
stroke harder than off the White -- so the offset is taken from the current
20-round window where possible rather than from all history.

The point of this file is the mechanism people get wrong: posting a round does
not push out your *worst* round. It pushes out your *oldest* one.
"""

from __future__ import annotations

import statistics
import sys

import model

WINDOW = 20
COUNTED = 8


def course_offsets(rounds, min_rounds: int = 2, current_only: bool = True
                   ) -> dict[str, float]:
    """``score - differential`` per course, from rounds actually played there.

    ``current_only`` keeps just the courses in the current 20-round window --
    the ones he might actually tee it up on next. Offsets are still averaged
    over every round ever played there.
    """
    acc: dict[str, list[float]] = {}
    for r in rounds:
        if r.app_handicap is not None and r.course:
            acc.setdefault(r.course, []).append(r.score - r.app_handicap)
    out = {c: statistics.mean(v) for c, v in acc.items() if len(v) >= min_rounds}
    if current_only:
        # Offsets shift with the tee played, so prefer the current window --
        # it reflects the tees he is actually using now. Fall back to all-time
        # for a course he has played only once recently.
        live: dict[str, list[float]] = {}
        for r in rounds[-WINDOW:]:
            if r.app_handicap is not None and r.course:
                live.setdefault(r.course, []).append(r.score - r.app_handicap)
        out = {c: (statistics.mean(v) if len(v) >= min_rounds else out.get(c, statistics.mean(v)))
               for c, v in live.items()} or out
    return out


def index_of(differentials: list[float]) -> float:
    """Average of the best :data:`COUNTED` differentials."""
    if not differentials:
        return 0.0
    return statistics.mean(sorted(differentials)[:min(COUNTED, len(differentials))])


def project(rounds, differential: float) -> tuple[float, float, object]:
    """Index now, index after posting ``differential``, and the round that ages out."""
    window = rounds[-WINDOW:]
    current = [r.app_handicap for r in window]
    dropped = window[0] if len(window) >= WINDOW else None
    kept = [r.app_handicap for r in (window[1:] if dropped else window)]
    return index_of(current), index_of(kept + [differential]), dropped


def main(argv: list[str]) -> int:
    rounds = [r for r in model.load() if r.is_full and r.app_handicap is not None]
    offsets = course_offsets(rounds)
    now, _, dropped = project(rounds, 99)

    print(f"index now: {now:.1f}  (best {COUNTED} of last {WINDOW})")
    if dropped:
        print(f"ages out when you post again: {dropped.date} "
              f"{dropped.course[:24]} — score {dropped.score}, "
              f"differential {dropped.app_handicap:.1f}")
        print("  (the OLDEST round leaves the window, not the worst)")
    print()

    if len(argv) >= 2:
        score = float(argv[0])
        name = argv[1]
        matches = [c for c in offsets if name.lower() in c.lower()]
        if not matches:
            print(f"no course matching {name!r}. Known: {sorted(offsets)}")
            return 1
        off = offsets[matches[0]]
        _, after, _ = project(rounds, score - off)
        print(f"{score:.0f} at {matches[0]} (differential {score - off:.1f})")
        print(f"  {now:.1f} -> {after:.1f}  ({after - now:+.1f})")
        return 0

    header = "score  " + "".join(f"{c[:20]:>22}" for c in sorted(offsets))
    print(header)
    for score in range(74, 89, 2):
        cells = ""
        for c in sorted(offsets):
            _, after, _ = project(rounds, score - offsets[c])
            cells += f"{after:>15.1f} ({after - now:+.1f})"
        print(f"{score:>5}  {cells}")
    print()
    print("A score whose differential lands above your current index cannot")
    print("lower it — it never reaches the best 8.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
