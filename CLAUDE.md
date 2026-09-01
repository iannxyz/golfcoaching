# Working in this repo

A golf coaching repo: a round log, a scoring model, and a coach built on both.
Read `README.md` first for what the data says.

## The one thing to know

Doubles-or-worse explains 75% of Ian's scoring variance (R² = 0.75, ~2.1
strokes each). GIR explains 53%. Putts and fairways explain almost nothing.
Any analysis or advice that leads with ball-striking is aimed at the wrong
target — check the model before asserting a cause.

## Generated files

`data/rounds.csv`, `data/holes.csv` and `TRENDS.md` are **generated**. Never
edit them by hand; the next import silently overwrites the change. Edit
`data/raw/round-log.csv` and re-run:

```bash
python3 scripts/importers.py
PYTHONPATH=scripts python3 scripts/trend.py
```

`data/raw/` is source data. Don't rewrite the exports.

## Scripts import each other flatly

`model.py` and `calibrate.py` import their siblings by bare name, so anything
that runs them needs `PYTHONPATH=scripts`. `importers.py` and `add_round.py`
stand alone and don't.

## Changing the model

`scripts/calibrate.py` checks the handicap model against published
handicap-to-score data and fails if any index is off by more than two strokes.
Run it after touching `BENCHMARK`, `HOLE_STRETCH` or `GAP_WEIGHTS` in `sg.py`.
It has already caught two real errors, so trust it over intuition.

Do not go back to stretching each lie's benchmark table independently by
handicap — it makes the category split incoherent. The comment at the top of
`sg.py` explains why.

Run the tests after any model change:

```bash
PYTHONPATH=scripts pytest tests/ -q
```

## Data honesty

- A blank stat is better than a guessed one. `add_round.py` validates rather
  than coercing, and refuses cards that don't add up.
- Detailed stat capture starts 2026-07-31 (`model.COMPLETE_STATS_FROM`). Before
  that, penalties, putts and up-and-down are missing or unreliable — filter to
  that date onward for trend work, and say so when a finding rests on ten
  rounds rather than ninety.
- `TRENDS.md` marks any R² drawn from fewer than 15 rounds with an asterisk.
  Keep that habit; the thin rows look the most exciting and are the least real.

## Coaching voice

`context/golf-coaching-context.md` is hand-maintained and is the most important
file in the repo. It carries the player profile, the bag, the established
mantras and how he wants to be coached. Reinforce the mantras that are already
in it rather than inventing new mechanics — he is a feel player and over-tinkers
when loaded with swing thoughts. Update the file when something changes that
outlives a single round, and say that you did.
