# golfcoaching

A round log, a scoring model, and a coach that reads both.

Ian shot 22.6 down to 11.2 in a year. The question this repo answers is not
"how did I play" — the app already says that — but **what should I practise
next**, argued from 97 rounds instead of from the last one.

## The finding the repo is built on

Regressing score against each tracked stat, over 92 complete rounds:

| Stat | R² | Strokes per unit |
|---|---|---|
| **Doubles or worse** | **0.75** | +2.08 |
| Greens in regulation | 0.53 | −1.66 |
| Putts | 0.05 | +0.36 |
| Fairways | 0.01 | −0.28 |

Doubles-or-worse explains three quarters of his scoring variance. Ball-striking
is not the limiter, and putts and fairways are nearly uncorrelated with the
number on the card. A practice plan aimed at the swing is aimed at the wrong
target — which is exactly what `/coach` will tell you.

**Read that +2.08 as correlational, not causal.** It is tempting to reason
"one fewer double, two fewer strokes" — that is wrong. His disaster holes
average 2.2 over par, so converting one to a bogey saves about **1.2** strokes
(`model.disaster_severity`). The slope is larger than the mechanical saving
because rounds with fewer doubles also have better putting, fewer penalties and
more pars; the coefficient carries all of it. The extra stroke is real but it
comes bundled with the rest of a clean card, and it cannot be banked on its
own.

The headline number is therefore not strokes gained. It is the **round
underneath**: the score with every double-or-worse hole replayed as a bogey.
Bogeys, missed greens and three-putts all still count; only the damage past
bogey comes out. Over the last ten rounds that gap — the disaster tax — is
**3.5 strokes per round**.

## Use it

```
/round  <screenshots>    # read a scorecard, log it, get an honest read back
/coach                   # read the whole history, say what to practise
```

`/round` pulls the numbers off 18Birdies screenshots, validates them (the front
and back nine have to add up to the score), writes the round, and rebuilds the
derived files. `/coach` is a skill: it reads the coaching context, the trends
and the full log, and produces a three-item practice plan into `practice/`.

## Layout

```
context/golf-coaching-context.md   Player profile, bag, mantras, how to coach him.
                                   Hand-maintained. The most important file here.
data/raw/                          Untouched exports. Never edited.
  18birdies-archive-*.json           106 rounds from the app
  round-log.csv                      hand-kept log, richer on recent rounds
data/rounds.csv                    Generated. One row per round, both sources merged.
data/holes.csv                     Generated. Hole-by-hole strokes, long format.
TRENDS.md                          Generated. The report /coach reads.
practice/                          Plans written by /coach, dated.
scripts/                           See below.
tests/                             50 tests. Run them after touching the model.
```

Everything under `data/` except `raw/` is derived, and so is `TRENDS.md`. Don't
hand-edit them — they are rewritten on every import.

## Scripts

| Script | Does |
|---|---|
| `importers.py` | Merges the app archive and the hand log into `data/rounds.csv` |
| `model.py` | Scoring model, round-underneath, fatigue and first-visit flags |
| `trend.py` | Rebuilds `TRENDS.md` |
| `add_round.py` | Appends one round, with validation. Called by `/round` |
| `sg.py` | Strokes gained — benchmark tables and both estimators |
| `calibrate.py` | Checks the handicap model against published scoring averages |
| `whatif.py` | What one more round at a given score does to the index |

```bash
PYTHONPATH=scripts python3 scripts/whatif.py            # table of next-round outcomes
PYTHONPATH=scripts python3 scripts/whatif.py 80 Eastlake

python3 scripts/importers.py                  # rebuild from raw
PYTHONPATH=scripts python3 scripts/trend.py   # rebuild TRENDS.md
PYTHONPATH=scripts python3 scripts/calibrate.py
PYTHONPATH=scripts pytest tests/ -q
```

No dependencies beyond the standard library; `pytest` only for the tests.

## Two sources, one log

The 18Birdies archive is the backbone — every round, with hole-by-hole strokes,
fairway and GIR splits by miss direction, and putts. The hand-kept CSV covers
fewer rounds but carries what the app doesn't: tee played, penalty strokes,
three-putts, up-and-down percentage, and the note explaining what happened.

They are merged on date. The CSV wins where they disagree, because a human was
there — except on the four hole counts (birdies, pars, bogeys, doubles), which
have to total 18. When a hand tally disagrees with a self-consistent app tally,
the app wins and the importer prints the conflict. Two such conflicts exist
today, both a hand count of doubles being one high.

## About strokes gained

`sg.py` implements it properly, at two fidelities: true shot-by-shot SG against
a tour benchmark, and an estimate decomposed from scorecard stats. But note
what the archive actually contains — the GPS shot entries are 1–3 measured
drives per round, not shot tracking. **There is no shot-level data to run true
SG on**, so nothing in the pipeline currently uses it.

It is here because it is the right tool the day he starts logging shots, and
because `calibrate.py` uses the same tables to sanity-check the handicap model
(currently accurate to 0.6 strokes against published scoring averages). Until
then, the doubles model is the one that earns its keep. Reaching for strokes
gained when the data can't support it would be precision theatre.

## Obsidian

`context/` and `practice/` are plain markdown with no front-matter
requirements, so the repo drops into a vault as-is and the generated `TRENDS.md`
renders as a note.
