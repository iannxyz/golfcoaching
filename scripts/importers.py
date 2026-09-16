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
    "date", "round_id", "course", "tee", "yards", "par", "holes", "score", "to_par",
    "front", "back", "fairways_hit", "fairways_total",
    "fairways_left", "fairways_right",
    "gir", "gir_total", "gir_short", "gir_long", "gir_left", "gir_right",
    "putts", "three_putts", "penalties", "up_down_pct",
    "birdies", "pars", "bogeys", "doubles_or_worse",
    "putts_made_5_15", "putts_faced_5_15",
    "greens_firm", "green_speed", "wind", "tee_club",
    "app_handicap", "source", "notes",
]


#: The app and the hand log spell some courses differently, which silently
#: splits one course into two -- two course offsets, two sets of history. Map
#: every spelling to one canonical name. Match is case-insensitive on the
#: stripped name.
COURSE_ALIASES = {
    "enagic golf club at eastlake": "Enagic at Eastlake",
    "enagic at eastlake": "Enagic at Eastlake",
    "club social y deportivo campestre de tijuana a c": "Campestre de Tijuana",
    "campestre de tijuana": "Campestre de Tijuana",
    "miami beach gc": "Miami Beach Golf Club",
    "miami beach golf club": "Miami Beach Golf Club",
    "torrey pines north": "Torrey Pines North",
    "torrey pines golf course": "Torrey Pines North",
}


def canonical_course(name: str) -> str:
    if not name:
        return ""
    return COURSE_ALIASES.get(name.strip().lower(), name.strip())


def _date(ts_ms: int) -> str:
    return dt.datetime.utcfromtimestamp(ts_ms / 1000).date().isoformat()


def _as_int(v):
    """Hand-logged CSV values arrive as strings; compare numbers as numbers."""
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _int(v):
    """18Birdies writes 0 for 'not recorded' as well as for a real zero.

    Treated as missing here. The one place that matters is ``penalties``, which
    the app does not track at all -- it comes from the CSV or not at all.
    """
    return v if v else None


def load_18birdies(path: Path) -> dict[str, dict]:
    """Keyed by the app's own round id, NOT by date.

    He plays twice in a day often enough to matter -- 2026-05-23 is an 89 and a
    91, and 2026-05-30 is a nine-hole 41 and an eighteen-hole 85. Keying on date
    silently kept one of each and dropped six real rounds.
    """
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
        out[r["id"]] = {
            "round_id": r["id"],
            "date": date,
            "course": canonical_course(clubs.get(r["clubId"]["id"], "")),
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
            "_holes_sum": sum(strokes),
        }
    return out


def pick_for_csv_row(candidates: list[dict], row: dict) -> dict | None:
    """Which app round a hand-logged row refers to, when a day holds several.

    Prefer an exact score match, then the one with the most holes -- a hand log
    entry describes the real round of the day, not the nine he added on.
    """
    if not candidates:
        return None
    try:
        want = int(row.get("score", ""))
    except (TypeError, ValueError):
        want = None
    if want is not None:
        exact = [c for c in candidates if c.get("score") == want]
        if exact:
            return exact[0]
    return max(candidates, key=lambda c: c.get("holes") or 0)


def load_csv_log(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    out = {}
    with path.open() as fh:
        for row in csv.DictReader(fh):
            row = {k: (v.strip() if isinstance(v, str) else v)
                   for k, v in row.items()}
            row = {k: v for k, v in row.items() if v not in ("", None)}
            if row.get("course"):
                row["course"] = canonical_course(row["course"])
            out[row["date"]] = row
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
    """Union of both sources. The hand-kept CSV wins, with two exceptions.

    App rounds are keyed by round id and hand-logged rows by date, so each CSV
    row is attached to one app round via :func:`pick_for_csv_row`; the other
    rounds that day pass through untouched rather than being overwritten.

    The CSV loses on the four hole counts when the app's tally is self-
    consistent, and on ``score`` when the app's hole-by-hole strokes add up to
    its own total and the hand figure disagrees. Both conflicts are reported.
    """
    by_date: dict[str, list[dict]] = {}
    for r in app.values():
        by_date.setdefault(r["date"], []).append(r)

    claimed: dict[str, dict] = {}                 # round_id -> hand row
    for date, row in hand.items():
        pick = pick_for_csv_row(by_date.get(date, []), row)
        if pick is not None:
            claimed[pick["round_id"]] = row

    rows = []
    for a in app.values():
        row = dict(a)
        h = claimed.get(a["round_id"])
        if h:
            row.update(h)
            row["source"] = "18birdies+csv"
            holes = a.get("holes") or 18
            if _counts_total(a, holes) and not _counts_total(row, holes):
                for k in HOLE_COUNTS:
                    if k in a:
                        if conflicts is not None and _as_int(h.get(k)) not in (None, a[k]):
                            conflicts.append(
                                f"{a['date']}: {k} logged as {h[k]}, app says "
                                f"{a[k]} (app counts total {holes}); using {a[k]}")
                        row[k] = a[k]
            # The scorecard is the arbiter of the score itself. Hand-logged
            # values are strings, so coerce before comparing or every round
            # reads as a conflict with itself.
            if (a.get("_holes_sum") == a.get("score")
                    and _as_int(row.get("score")) not in (None, a["score"])):
                if conflicts is not None:
                    conflicts.append(
                        f"{a['date']}: score logged as {row.get('score')}, "
                        f"app scorecard sums to {a['score']}; using {a['score']}")
                row["score"] = a["score"]
                row["to_par"] = None           # recomputed in derive()
        rows.append(row)

    # Hand-logged rounds with no app counterpart at all.
    for date, row in hand.items():
        if not pick_for_csv_row(by_date.get(date, []), row):
            rows.append({**row, "source": "csv"})

    def order(r: dict) -> tuple:
        # Hand-logged values arrive as strings; coerce before comparing.
        def num(v, default=0):
            try:
                return int(v)
            except (TypeError, ValueError):
                return default
        return (r["date"], -num(r.get("holes")), num(r.get("score")))

    rows.sort(key=order)
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
    """Long-format hole-by-hole strokes: one row per hole played.

    ``round_id`` is carried so two rounds on one date stay distinguishable.
    """
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "round_id", "course", "hole", "strokes"])
        for r in sorted(app.values(), key=lambda x: (x["date"], x["round_id"])):
            for i, n in enumerate(r["_holeStrokes"], start=1):
                if n:
                    w.writerow([r["date"], r["round_id"], r["course"], i, n])


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
