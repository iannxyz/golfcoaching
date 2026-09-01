---
description: Log a round from scorecard screenshots, then read it back honestly
argument-hint: [screenshot paths, or the numbers, or nothing to be prompted]
allowed-tools: Read, Bash, Glob
---

Log a round and tell Ian what it actually was.

Input: $ARGUMENTS

## 1. Get the numbers

If screenshots or image paths were given, read them with the Read tool. Ian
posts 18Birdies scorecard and stats pages — usually two images, sometimes more.
Pull out:

| Field | Where it lives |
|---|---|
| date, course, tee, yards, par | scorecard header |
| score, front, back | scorecard totals |
| fairways hit (of 14) | stats page |
| greens in regulation (of 18) | stats page |
| putts, three-putts | stats page |
| penalties | stats page, or ask — the app under-reports these |
| up-and-down % | stats page |
| doubles or worse | count them off the scorecard row |

If he typed the numbers instead of attaching images, use those. If something is
missing, ask for just the missing fields — don't re-ask for what you already
have. **Never invent a stat to fill a column.** A blank is fine; a guess
corrupts the trend.

Voice-to-text mangles golf words. `pug` is putt, `t` is tee, `gear` is GIR,
`birdy` is birdie. Read through the transcription errors.

## 2. Count the doubles yourself

Doubles-or-worse is the single most important field in this repo — it carries
the scoring model (R² = 0.75, ~2.1 strokes each). Count them off the scorecard
holes rather than trusting a summary tile, and sanity-check:

    birdies + pars + bogeys + doubles_or_worse == 18

## 3. Write it

```bash
python3 scripts/add_round.py --date DATE --course "COURSE" --tee TEE \
  --yards N --par 72 --score N --front N --back N \
  --fairways N --gir N --putts N --three-putts N --penalties N \
  --up-down N --doubles N --notes "what happened, in one or two sentences"
```

Omit any flag you don't have. The script validates the read (front + back must
equal the score, stats must be in range) and refuses to write a card that
doesn't add up — if it refuses, re-read the screenshot rather than forcing the
number through. It then rebuilds `data/rounds.csv` and `TRENDS.md`.

Notes matter. Record fatigue, food, wind, first visit to the course, what the
driver was doing, and any club he switched to. Those explain more of his
variance than the swing does.

## 4. Read the round back

Then run:

```bash
PYTHONPATH=scripts python3 -c "
import model
rs = model.load(); r = rs[-1]
print('round underneath:', r.round_underneath, 'vs actual', r.score)
print('flags:', model.flags(rs, r))
print('recent:', model.averages(rs, 10))
"
```

And tell him, in this order and in a few sentences — not a report:

1. **The honest read first.** What the number was, and what the round
   underneath was (doubles replayed as bogeys). He finds this motivating and
   it is accurate, so lead with it.
2. **What moved the score.** Doubles first. Then penalties. Only then ball
   striking — it is usually not the limiter.
3. **Context before diagnosis.** If `flags()` reports consecutive days, a first
   visit, or a layoff, say so before blaming a swing. Ask about food and rest
   rather than assuming.
4. **One thing for next time**, drawn from the established mantras in
   `context/golf-coaching-context.md`. Reinforce an existing one; do not invent
   new mechanics. He is a feel player and over-tinkers when loaded with
   swing thoughts.

Direct and specific. Encouragement paired with real accountability — he wants
both, and he can tell when a number is being softened.
