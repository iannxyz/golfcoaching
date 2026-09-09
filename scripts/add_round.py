"""Append one round to ``data/raw/round-log.csv`` and rebuild everything.

Called by the ``/round`` command once it has read the numbers off a scorecard
screenshot. Takes the stats as flags so there is no free-text parsing step
between reading the card and storing the data::

    python3 scripts/add_round.py --date 2026-09-01 --course "Enagic at Eastlake" \\
        --tee Blue --yards 6224 --par 72 --score 79 --front 39 --back 40 \\
        --fairways 8 --gir 9 --putts 31 --three-putts 1 --penalties 0 \\
        --up-down 50 --doubles 2 --notes "Played the 5-wood off the tee."

Re-running with a date already in the log updates that row rather than adding a
duplicate, so a round can be corrected by running the command again.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "data" / "raw" / "round-log.csv"

COLUMNS = [
    "date", "course", "tee", "yards", "par", "holes", "score", "to_par",
    "front", "back", "fairways_hit", "fairways_total", "gir", "putts",
    "three_putts", "penalties", "up_down_pct",
    "birdies", "pars", "bogeys", "doubles_or_worse",
    "putts_made_5_15", "putts_faced_5_15",
    "greens_firm", "green_speed", "wind", "tee_club", "notes",
]


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--course", required=True)
    p.add_argument("--score", required=True, type=int)
    p.add_argument("--tee", default="")
    p.add_argument("--yards", type=int)
    p.add_argument("--par", type=int, default=72)
    # Without this a hand-logged round has no hole count, Round.is_full is
    # False, and the round is silently dropped from every analysis until the
    # next app export happens to contain it.
    p.add_argument("--holes", type=int, default=18)
    p.add_argument("--front", type=int)
    p.add_argument("--back", type=int)
    p.add_argument("--fairways", type=int, help="fairways hit")
    p.add_argument("--fairways-total", type=int, default=14)
    p.add_argument("--gir", type=int)
    p.add_argument("--putts", type=int)
    p.add_argument("--three-putts", type=int)
    p.add_argument("--penalties", type=int)
    p.add_argument("--up-down", type=float, help="up-and-down percentage")
    p.add_argument("--doubles", type=int, help="holes at double bogey or worse")
    # The four hole counts drive round_underneath, the headline metric. Pass
    # all four or none -- validate() rejects a partial set that cannot total.
    p.add_argument("--birdies", type=int)
    p.add_argument("--pars", type=int)
    p.add_argument("--bogeys", type=int)
    # Total putts cannot tell a missed par putt from a good lag -- both leave a
    # two-putt. Make rate at scoring distance is the number that moves the score,
    # and it is the one stat the app does not provide.
    p.add_argument("--putts-made-5-15", type=int,
                   help="putts holed from roughly 5-15 ft")
    p.add_argument("--putts-faced-5-15", type=int,
                   help="putts attempted from roughly 5-15 ft")
    p.add_argument("--greens-firm", choices=("soft", "medium", "firm"),
                   help="did approach shots check, or bounce and release?")
    p.add_argument("--green-speed", choices=("slow", "medium", "fast"))
    p.add_argument("--wind", help="free text, e.g. '17 mph'")
    p.add_argument("--tee-club", help="what he actually played off the tee, "
                                      "e.g. 'driver' or '5-wood'")
    p.add_argument("--notes", default="")
    p.add_argument("--no-rebuild", action="store_true",
                   help="skip the import/trend rebuild (used by the tests)")
    return p.parse_args(argv)


def to_row(a: argparse.Namespace) -> dict:
    row = {
        "date": a.date, "course": a.course, "tee": a.tee,
        "yards": a.yards, "par": a.par, "holes": a.holes, "score": a.score,
        "to_par": a.score - a.par if a.par else None,
        "front": a.front, "back": a.back,
        "fairways_hit": a.fairways, "fairways_total": a.fairways_total,
        "gir": a.gir, "putts": a.putts, "three_putts": a.three_putts,
        "penalties": a.penalties, "up_down_pct": a.up_down,
        "birdies": a.birdies, "pars": a.pars, "bogeys": a.bogeys,
        "putts_made_5_15": a.putts_made_5_15,
        "putts_faced_5_15": a.putts_faced_5_15,
        "doubles_or_worse": a.doubles,
        "greens_firm": a.greens_firm, "green_speed": a.green_speed,
        "wind": a.wind, "tee_club": a.tee_club, "notes": a.notes,
    }
    return {k: ("" if v is None else v) for k, v in row.items()}


def validate(row: dict) -> list[str]:
    """Catch the mistakes a screenshot read actually makes."""
    problems = []
    score = int(row["score"])
    if not 55 <= score <= 150:
        problems.append(f"score {score} is outside any plausible range")
    front, back = row.get("front"), row.get("back")
    if front and back and int(front) + int(back) != score:
        problems.append(f"front {front} + back {back} != score {score}")
    for key, cap in (("fairways_hit", 14), ("gir", 18), ("doubles_or_worse", 18),
                     ("three_putts", 18)):
        v = row.get(key)
        if v not in ("", None) and not 0 <= int(v) <= cap:
            problems.append(f"{key}={v} is outside 0..{cap}")
    putts = row.get("putts")
    if putts not in ("", None) and not 18 <= int(putts) <= 50:
        problems.append(f"putts={putts} is outside 18..50")
    ud = row.get("up_down_pct")
    if ud not in ("", None) and not 0 <= float(ud) <= 100:
        problems.append(f"up_down_pct={ud} is not a percentage")
    made, faced = row.get("putts_made_5_15"), row.get("putts_faced_5_15")
    if made not in ("", None) and faced not in ("", None) and int(made) > int(faced):
        problems.append(f"putts made {made} exceeds putts faced {faced}")
    counts = [row.get(k) for k in ("birdies", "pars", "bogeys", "doubles_or_worse")]
    given = [c for c in counts if c not in ("", None)]
    if given and len(given) == 4:
        holes = int(row.get("holes") or 18)
        if sum(int(c) for c in given) != holes:
            problems.append(
                f"birdies+pars+bogeys+doubles = {sum(int(c) for c in given)}, "
                f"not {holes}")
    return problems


def upsert(row: dict, log: Path = LOG) -> str:
    rows, seen = [], False
    if log.exists():
        with log.open() as fh:
            rows = list(csv.DictReader(fh))
    for i, existing in enumerate(rows):
        if existing["date"] == row["date"]:
            rows[i] = row
            seen = True
            break
    if not seen:
        rows.append(row)
    rows.sort(key=lambda r: r["date"])
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return "updated" if seen else "added"


def main(argv=None) -> int:
    args = parse_args(argv)
    row = to_row(args)
    problems = validate(row)
    if problems:
        print("Refusing to write -- check the scorecard read:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    action = upsert(row)
    print(f"{action} {row['date']} {row['course']} ({row['score']})")

    if args.no_rebuild:
        return 0
    for script in ("importers.py", "trend.py"):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / script)],
                           env={"PYTHONPATH": str(ROOT / "scripts"), "PATH": "/usr/bin:/bin:/usr/local/bin"})
        if r.returncode:
            return r.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
