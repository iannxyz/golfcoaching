"""Export the round history in a portable, hole-by-hole shape.

Neither 18Birdies nor TheGrint offers a self-serve bulk import, so this exists
for two reasons: to hand a support team something they can actually load, and
so the history is never trapped in whichever app is current. The repo is the
system of record; the apps are just capture devices.

    PYTHONPATH=scripts python3 scripts/export_rounds.py
    PYTHONPATH=scripts python3 scripts/export_rounds.py --since 2026-01-01

Writes ``export/rounds-holes.csv`` (one row per round, H1..H18 plus totals) and
``export/rounds-summary.csv`` (one row per round, no hole detail). The first is
what a bulk loader or a spreadsheet paste wants; the second covers the rounds
that have no hole-by-hole record.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import model

ROOT = Path(__file__).resolve().parent.parent
HOLES_CSV = ROOT / "data" / "holes.csv"
OUT_DIR = ROOT / "export"

HOLE_COLS = [f"H{i}" for i in range(1, 19)]
SUMMARY_COLS = [
    "date", "course", "tee", "yards", "par", "holes", "score", "to_par",
    "front", "back", "fairways_hit", "fairways_total", "gir", "putts",
    "three_putts", "penalties", "up_down_pct",
    "birdies", "pars", "bogeys", "doubles_or_worse", "notes",
]


def load_hole_scores() -> dict[str, dict[int, int]]:
    """date -> {hole number: strokes}."""
    out: dict[str, dict[int, int]] = defaultdict(dict)
    if not HOLES_CSV.exists():
        return out
    with HOLES_CSV.open() as fh:
        for row in csv.DictReader(fh):
            out[row["date"]][int(row["hole"])] = int(row["strokes"])
    return out


def summary_row(r: model.Round) -> dict:
    row = {c: getattr(r, c, None) for c in SUMMARY_COLS}
    row["date"] = r.date
    row["to_par"] = r.to_par
    return {k: ("" if v is None else v) for k, v in row.items()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", help="only rounds on or after this date (YYYY-MM-DD)")
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args(argv)

    rounds = model.load()
    if args.since:
        rounds = [r for r in rounds if r.date >= args.since]
    holes = load_hole_scores()

    args.out.mkdir(parents=True, exist_ok=True)

    with_holes, without = [], []
    for r in rounds:
        got = holes.get(r.date, {})
        row = summary_row(r)
        if len(got) >= 9:
            row.update({f"H{i}": got.get(i, "") for i in range(1, 19)})
            with_holes.append(row)
        else:
            without.append(row)

    hole_path = args.out / "rounds-holes.csv"
    with hole_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=SUMMARY_COLS + HOLE_COLS,
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(with_holes)

    sum_path = args.out / "rounds-summary.csv"
    with sum_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=SUMMARY_COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(with_holes + without)

    def show(p: Path) -> str:
        """Repo-relative when it is inside the repo, absolute otherwise."""
        try:
            return str(p.relative_to(ROOT))
        except ValueError:
            return str(p)

    print(f"{show(hole_path)}: {len(with_holes)} rounds "
          f"with hole-by-hole scores")
    print(f"{show(sum_path)}: {len(with_holes) + len(without)} rounds "
          f"({len(without)} without hole detail)")
    if without:
        print("  no hole detail: "
              + ", ".join(r["date"] for r in without[:10])
              + (" ..." if len(without) > 10 else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
