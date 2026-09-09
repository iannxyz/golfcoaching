"""What chip proximity is worth, in up-and-downs.

An up-and-down is two events: get the chip on the green, then hole the putt.
The second one is almost entirely decided by the first. Make rates fall off a
cliff between three feet and fifteen, so *where the chip finishes* sets the
up-and-down rate far more than how the putt is struck.

That matters because it points practice at the right thing. "Make more putts
after a chip" is not a skill you can train directly. "Leave the chip inside
five feet" is.

Make rates come from the tour putting benchmark in ``sg.py`` (make% = 2 - E for
short putts, where three-putts are negligible). They are a ceiling, not Ian's
rate -- his will be lower at every distance, which only sharpens the conclusion.

    PYTHONPATH=scripts python3 scripts/shortgame.py
    PYTHONPATH=scripts python3 scripts/shortgame.py 10    # 10 missed greens
"""

from __future__ import annotations

import sys

import model
import sg

#: Proximities worth showing, in feet.
DISTANCES = (3, 4, 5, 6, 8, 10, 12, 15, 20)


def make_rate(feet: float) -> float:
    """Tour one-putt probability from ``feet``, from the benchmark table."""
    return max(0.0, min(1.0, 2.0 - sg.expected_strokes("green", feet)))


def up_and_down_rate(feet: float, green_hit_rate: float = 1.0) -> float:
    """Up-and-down chance for a chip finishing at ``feet``.

    ``green_hit_rate`` is how often the chip finds the green at all; a duffed or
    thinned chip that never gets there cannot be holed.
    """
    return green_hit_rate * make_rate(feet)


def main(argv: list[str]) -> int:
    misses = int(argv[0]) if argv else 10
    rounds = [r for r in model.load() if r.is_full]
    measured = [r.up_down_pct for r in rounds if r.up_down_pct is not None]

    print("Chip proximity decides the up-and-down, not the putting stroke.\n")
    print(f"{'chip finishes':>14}  {'tour make %':>12}  "
          f"{'up-and-downs of ' + str(misses):>20}")
    for d in DISTANCES:
        r = make_rate(d)
        print(f"{str(d) + ' ft':>14}  {r:>11.0%}  {r * misses:>20.1f}")

    if measured:
        mean = sum(measured) / len(measured)
        print(f"\nIan's measured up-and-down rate: {mean:.0f}% "
              f"over {len(measured)} rounds "
              f"({min(measured):.0f}% to {max(measured):.0f}%).")
        # Which proximity would produce that rate at tour make rates?
        implied = min(DISTANCES, key=lambda d: abs(make_rate(d) - mean / 100))
        print(f"At tour make rates that is the rate you get chipping to about "
              f"{implied} feet.")
        print("His real make rate is below tour, so his true average chip is "
              "finishing further out than that.")
        print("\nThe lever is proximity. Going from ten feet to four roughly "
              "doubles the up-and-down rate\nwithout holing a single putt more "
              "than a tour player would from the same distance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
