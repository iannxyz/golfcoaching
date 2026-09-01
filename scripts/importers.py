"""Turn raw exports into the canonical round log.

Two sources, merged on date:

* ``data/raw/18birdies-archive-*.json`` -- the backbone. Every round Ian has
  posted in the app, with hole-by-hole strokes, fairway and GIR splits by miss
  direction, putts, and the app's own handicap estimate at the time.
* ``data/raw/round-log.csv`` -- the hand-kept log. Fewer rounds, but it carries
  things the app does not: tee played, course yardage, three-putts, penalty
  strokes, up-and-down percentage, and the notes that explain a round.

Where both have a value the CSV wins, because it was written by a human who was
there -- with one exception. The four hole counts (birdies, pars, bogeys,
doubles-or-worse) must total the holes played, and the app derives them from a
scorecard it knows the pars for. When the hand count disagrees with a
self-consistent app count, the app wins and the conflict is reported. That
matters more than it sounds: ``doubles_or_worse`` carries the scoring model, and
a hand tally is off by one more often than an automatic one.

Everything is rewritten from the raw files on every run, so this is safe to
re-run whenever a new export lands.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

#: Canonical column order for ``data/rounds.csv``.
FIELDS = [
    "date", "course", "tee", "yards", "par", "holes", "score", "to_par",
    "front", "back", "fairways_hit", "fairways_total",
    "fairways_left", "fairways_right",
    "gir", "gir_total", "gir_short", "gir_long", "gir_left", "gir_right",
    "putts", "three_putts", "penalties", "up_down_pct",
    "birdies", "pars", "bogeys", "doubles_or_worse",
    "app_handicap", "source", "notes",
]


def _date(ts_ms: int) -> str:
    return dt.datetime.utcfromtimestamp(ts_ms / 1000).date().isoformat()


def _int(v):
    """18Birdies writes 0 for 'not recorded' as well as for a real zero.

    Treated as missing here. The one place that matters is ``penalties``, which
    the app does not track at all -- it comes from the CSV or not at all.
    """
    return v if v else None


def load_18birdies(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text())
    my = data["myData"]
    clubs = {c["clubId"]: c["name"] for c in my["clubData"]["playedClubs"]}
    out: dict[str, dict] = {}
    for r in my["activityData"]["rounds"]:
        strokes = r["holeStrokes"]
        holes = sum(1 for h in strokes if h)
        if not holes:
            continue                      # a round posted with no scorecard
        s = r["stats"]
        date = _date(r["timestamp"])
        out[date] = {
            "date": date,
            "course": clubs.get(r["clubId"]["id"], ""),
            "holes": holes,
            "score": r["strokes"],
            "front": sum(strokes[:9]) or None,
            "back": sum(strokes[9:]) or None,
            "fairways_hit": _int(s.get("fairwayMiddles")),
            "fairways_total": _int(s.get("fairwayHoleCount")),
            "fairways_left": _int(s.get("fairwayLefts")),
            "fairways_right": _int(s.get("fairwayRights")),
            "gir": _int(s.get("gir")),
            "gir_total": _int(s.get("girHoleCount")),
            "gir_short": _int(s.get("girShorts")),
            "gir_long": _int(s.get("girLongs")),
            "gir_left": _int(s.get("girLefts")),
            "gir_right": _int(s.get("girRights")),
            "putts": _int(s.get("putts")),
            "birdies": s.get("birdies"),
            "pars": s.get("pars"),
            "bogeys": s.get("bogeys"),
            "doubles_or_worse": s.get("doubleBogeyOrWorse"),
            "app_handicap": r.get("roundHandicap"),
            "source": "18birdies",
            "_holeStrokes": strokes,
        }
    return out


def load_csv_log(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    out = {}
    with path.open() as fh:
        for row in csv.DictReader(fh):
            row = {k: (v.strip() if isinstance(v, str) else v)
                   for k, v in row.items()}
            out[row["date"]] = {k: v for k, v in row.items() if v not in ("", None)}
    return out


#: These four must total the holes played, so they are only trusted as a set.
HOLE_COUNTS = ("birdies", "pars", "bogeys", "doubles_or_worse")


def _counts_total(row: dict, holes: int) -> bool:
    """True if all four hole counts are present and add up to the holes played."""
    try:
        return sum(int(row[k]) for k in HOLE_COUNTS) == holes
    except (KeyError, TypeError, ValueError):
        return False


def merge(app: dict[str, dict], hand: dict[str, dict],
          conflicts: list[str] | None = None) -> list[dict]:
    """Union of both sources by date. The hand-kept CSV wins, except on the
    hole counts, where a self-consistent app tally beats a hand tally."""
    rows = []
    for date in sorted(set(app) | set(hand)):
        a, h = app.get(date), hand.get(date)
        row = dict(a or {"date": date})
        if h:
            row.update(h)                          # CSV overrides by default
        if a and h:
            row["source"] = "18birdies+csv"
            holes = a.get("holes") or 18
            # Restore the app's counts if they add up and the merged ones do not.
            if _counts_total(a, holes) and not _counts_total(row, holes):
                for k in HOLE_COUNTS:
                    if k in a:
                        if conflicts is not None and str(h.get(k, "")) not in ("", str(a[k])):
                            conflicts.append(
                                f"{date}: {k} logged as {h[k]}, app says {a[k]} "
                                f"(app counts total {holes}); using {a[k]}")
                        row[k] = a[k]
        elif h:
            row["source"] = "csv"
        rows.append(row)
    return rows


def derive(row: dict) -> dict:
    """Fill in what can be computed from what is already there."""
    par, score = row.get("par"), row.get("score")
    if par and score and not row.get("to_par"):
        row["to_par"] = int(score) - int(par)
    # 18Birdies reports par-relative counts but not par itself. Every course in
    # this log is a par 72; only claim it for full 18-hole rounds.
    if not row.get("par") and row.get("holes") == 18:
        row["par"] = 72
        if score:
            row["to_par"] = int(score) - 72
    return row


def write_rounds(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(derive(r))


def write_holes(app: dict[str, dict], path: Path) -> None:
    """Long-format hole-by-hole strokes: one row per hole played."""
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "course", "hole", "strokes"])
        for date in sorted(app):
            r = app[date]
            for i, n in enumerate(r["_holeStrokes"], start=1):
                if n:
                    w.writerow([date, r["course"], i, n])


def main() -> int:
    archives = sorted(RAW.glob("18birdies-archive-*.json"))
    app: dict[str, dict] = {}
    for a in archives:
        app.update(load_18birdies(a))         # later archives supersede earlier
    hand = load_csv_log(RAW / "round-log.csv")
    conflicts: list[str] = []
    rows = merge(app, hand, conflicts)

    write_rounds(rows, ROOT / "data" / "rounds.csv")
    write_holes(app, ROOT / "data" / "holes.csv")

    both = sum(1 for r in rows if r.get("source") == "18birdies+csv")
    print(f"rounds.csv: {len(rows)} rounds "
          f"({len(app)} from app, {len(hand)} hand-logged, {both} in both)")
    print(f"holes.csv:  {sum(len(r['_holeStrokes']) for r in app.values())} hole rows")
    for c in conflicts:
        print(f"  conflict  {c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
