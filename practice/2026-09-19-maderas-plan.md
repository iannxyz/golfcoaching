# Maderas Golf Club — Blue tees, 2026-09-19

**6,670 yards · par 72 · rating 73.3 · slope 136**

Verified from the club scorecard. For comparison, Eastlake Blue is 70.4/128 —
**Maderas is 3.6 strokes harder for him**. Course handicap at a 9.5 index is
**13 strokes**, so personal par is **85**.

He has played it once: 98 on 2025-12-30, as a 22 handicap, with 9 doubles and
**2 greens in regulation off 8 fairways**. That pattern is the course, not the
swing — elevated greens, uphill approaches, forced carries. Finding fairways at
Maderas does not produce greens.

**Prediction: 87–91, centre 89.** A good day is 85, a bad one 95. Anyone who
tells him 82 is flattering him.

## The tee club question, answered with his own numbers

Expected strokes for each driving hole, from the benchmark tables in `sg.py`,
5-wood (230) against driver (270):

| driver penalty rate | fairways | 5-wood | driver | edge |
|---|---|---|---|---|
| 0% | 62% | 55.4 | 54.1 | driver by 1.3 |
| 3% | 57% | 55.4 | 54.9 | driver by 0.5 |
| **5–6%** | 54% | 55.4 | 55.3 | **break-even** |
| 10% | 47% | 55.4 | 56.6 | 5-wood by 1.2 |
| 15% | 40% | 55.4 | 57.8 | 5-wood by 2.4 |

**The break-even is roughly one penalty per round** (14 driving holes × 6%).
His last 15 rounds average exactly 1.0 penalty, so a *normal* driver is about
break-even here and not worth agonising over.

A driver in a severe hook is nowhere near that rate. At 15% it costs **2.4
strokes**. The decision is therefore conditional, not dogmatic:

> **5-wood off the tee until the driver proves itself. Driver only on 5, 12 and
> 16, and only if the first two swings of the day are clean.**

Those three are the only holes where the extra 40 yards changes the club in
hand meaningfully, and even there driver leaves 140–190 in. It does not turn a
single hole into a birdie chance. The upside is small; the hook downside is not.

## Hole by hole

Approach yardage is what a 230-yard 5-wood leaves. Target is personal par —
he gets a stroke on all but five holes.

| # | Par | Yds | SI | Tee club | Leaves | Target |
|---|---|---|---|---|---|---|
| 1 | 4 | 355 | 17 | 5-wood | 125 (46°) | **4** — no stroke |
| 2 | 4 | 357 | 5 | 5-wood | 127 (46°) | 5 |
| 3 | 5 | 560 | 3 | 5-wood ×2 | 100 (50°) | 6 — three shots, no heroics |
| 4 | 3 | 164 | 15 | 6-iron | — | **3** — no stroke |
| 5 | 4 | 460 | 1 | 5-wood | 230 | 5 — **play it as a par 5** |
| 6 | 4 | 333 | 11 | 5-wood or 4-iron | 103–128 | 5 |
| 7 | 3 | 190 | 13 | 5-iron | — | 4 |
| 8 | 5 | 491 | 7 | 5-wood ×2 | 31 | 6 |
| 9 | 4 | 351 | 9 | 5-wood | 121 (46°) | 5 |
| 10 | 4 | 305 | 16 | **4-iron** | 100 (50°) | **4** — no stroke |
| 11 | 4 | 343 | 14 | 5-wood | 113 (50°) | **4** — no stroke |
| 12 | 4 | 410 | 10 | 5-wood | 180 (5-iron) | 5 |
| 13 | 4 | 385 | 8 | 5-wood | 155 | 5 |
| 14 | 5 | 526 | 2 | 5-wood ×2 | 66 | 6 |
| 15 | 3 | **240** | 12 | 5-wood | — | 4 — **bogey is a good score** |
| 16 | 4 | 439 | 6 | 5-wood | 209 | 5 |
| 17 | 3 | 165 | 18 | 6-iron | — | **3** — no stroke |
| 18 | 5 | 580 | 4 | 5-wood ×2 | 120 | 6 |

Personal par: **out 43, in 42, total 85.**

**Hole 10 is the one to be disciplined about.** At 305 yards it is drivable-ish
and that is exactly the trap. A 4-iron leaves a full wedge and it is one of only
five holes where he does not get a stroke — a par there is worth more than a
gambled birdie.

**Hole 15 is a 240-yard par 3.** Treat it as a short par 4: 5-wood, pitch, putt.
Trying to reach it in one with anything he'd have to force is how a 4 becomes a 7.

**Hole 5 is stroke index 1 at 460 yards.** He gets a stroke. Bogey is a par.
Playing it as a three-shot hole is the correct play, not a concession.

## The five holes that decide the round

1, 4, 10, 11, 17 — the five where he gets no stroke. They are also the five
shortest and easiest. **Par those five and bogey everything else and he shoots
85.** That framing is the round: there is no hole on this course where he needs
to make birdie.

## What I could not verify

Per-hole hazard positions are not reliably published for Maderas, so nothing
above tells him which side the trouble is on. Use the GPS and the course guide
on the day. What the plan does not depend on is exactly that — it is built on
yardage, stroke index and his own carry distances.

## Standing rules

- **First mistake = bogey is now the goal.** More important here than anywhere.
  He made 9 doubles last time; the model says each costs ~2.1 strokes.
- **One more club on approach.** Uphill, elevated greens, and his misses run
  short 62 to 19. Take one extra and commit.
- **Chip and lag into a 3-foot circle**, not at the hole.
- **Record:** putts made and faced from 5–15 ft, and what the greens are doing.

---

## Result: 92 (+20). Round underneath: **85 — exactly personal par.**

Differential 15.5, against 20.5 on his first visit. Same course, same 2 GIR,
**six strokes better.**

### Against the plan, hole by hole

| | |
|---|---|
| Matched or beat the plan | **13 of 18 holes** |
| Beat it | 9, 15, 16, 18 — including a **par on the 240-yard 15th** |
| Cost the round | **4 (+2), 8 (+3), 10 (+3)** |

Those three holes are +8. The other fifteen came in at −1 against plan. He
played the strategy and it worked everywhere he followed it.

**Hole 10 is the painful one.** 305 yards, no stroke, the plan said 4-iron and
take the par, and it went for 7. That was the single hole flagged in advance as
the discipline test.

**Hole 8** — a 9 on a par 5 — is the other. Plan was three shots and a bogey.

### What was genuinely good

- **31 putts with 2 greens in regulation.** Top 9% at the course. He was
  chipping on almost every hole and still only took 31, with one three-putt.
- **Up-and-down 42%**, against a 33% career average, top 21% at the course.
- **Par-par-par-par to finish** on 15 through 18, beating the plan by 3 over
  the closing stretch. The old back-nine fatigue pattern did not appear.

### The lesson, and it is the one the plan predicted

**Four penalties.** Across 14 driving holes that is a **29% penalty rate**
against the 5–6% break-even computed beforehand. At that rate the model says the
driver costs ~3.6 strokes over the 5-wood.

The tee-club decision was the whole plan, and the round is the evidence for it.
Short game and putting were both *better* than his averages; the score came from
disaster holes and penalty strokes, exactly where it was forecast to come from.

**Prediction was 87–91, centre 89. Actual 92** — one outside the range, and the
four penalties are the gap.
