"""Rebuild the web app's embedded round history from the repo.

The app at `app/index.html` carries the round history inside the page so it
renders complete with no loading state. That history is generated, not authored:
run this after importing a new archive, then republish the artifact.

    PYTHONPATH=scripts python3 scripts/build_app.py

Rounds added through the app itself live in the artifact's `added` collection
and are NOT touched here -- merge those into `data/raw/round-log.csv` first if
you want them in the embedded history.
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import model

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app" / "index.html"

#: Per-hole pars, only where they are known rather than inferred. Each set was
#: checked against his own hole scores before being trusted: with pars right,
#: every hole's mean sits within about a stroke of the round's average over par,
#: and a mis-assigned par shows up as a ~1.0 outlier.
#:
#: Eastlake  -- read off a TheGrint card, verified over 47 rounds.
#: Maderas   -- published club scorecard.
#: Campestre -- published card (its Blue 6,579 / White 6,305 match the tees he
#:              plays), verified over 25 rounds: every hole +0.45 to +1.45 over
#:              par against a +0.94 average, no outliers.
COURSE_PARS = {
    "Enagic at Eastlake":   [4,4,4,3,5,4,3,4,5,4,4,3,4,5,4,4,3,5],
    "Maderas Golf Club":    [4,4,5,3,4,4,3,5,4,4,4,4,4,5,3,4,3,5],
    "Campestre de Tijuana": [5,3,4,4,4,3,4,4,5,4,4,3,4,4,4,5,5,3],
}
#: Autofill for the app's add-round form. Rating and slope only where they are
#: published for the tee he actually plays -- a guessed rating would silently
#: corrupt every differential computed from it.
COURSE_META = {
    "Enagic at Eastlake":   {"rating":70.4,"slope":128,"yards":6224,"tee":"Blue"},
    "Maderas Golf Club":    {"rating":73.3,"slope":136,"yards":6670,"tee":"Blue"},
    "Campestre de Tijuana": {"yards":6305,"tee":"White"},
}


def build_payload() -> dict:
    holes = defaultdict(dict)
    with (ROOT / "data" / "holes.csv").open() as fh:
        for row in csv.DictReader(fh):
            holes[row["round_id"]][int(row["hole"])] = int(row["strokes"])
    rounds = []
    for r in model.load():
        if not r.is_full:
            continue
        h = holes.get(r.round_id) or {}
        rounds.append({k: v for k, v in {
            "id": r.round_id or f"{r.date}-{r.score}",
            "date": r.date, "course": r.course, "tee": r.tee or None,
            "par": r.par, "score": r.score, "front": r.front, "back": r.back,
            "rating": r.course_rating, "slope": r.slope,
            "fw": r.fairways_hit, "fwTot": r.fairways_total, "gir": r.gir,
            "putts": r.putts, "tp": r.three_putts, "pen": r.penalties,
            "ud": r.up_down_pct, "b": r.birdies, "p": r.pars, "bo": r.bogeys,
            "d": r.doubles_or_worse, "diff": r.app_handicap,
            "holes": [h.get(i) for i in range(1, 19)] if len(h) == 18 else None,
            "notes": r.notes or None,
        }.items() if v is not None})
    return {"rounds": rounds, "coursePars": COURSE_PARS,
            "courseMeta": COURSE_META, "source": "golfcoaching repo"}


def main() -> int:
    payload = build_payload()
    html = APP.read_text()
    blob = json.dumps(payload, separators=(",", ":"))
    new, n = re.subn(
        r'(<script id="history-data" type="application/json">).*?(</script>)',
        lambda m: m.group(1) + blob + m.group(2),
        html, count=1, flags=re.S)
    if not n:
        print("could not find the history-data block in app/index.html")
        return 1
    APP.write_text(new)
    print(f"embedded {len(payload['rounds'])} rounds into "
          f"{APP.relative_to(ROOT)} ({len(blob)/1024:.0f} KB)")
    print("now republish the artifact with the same file path")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
