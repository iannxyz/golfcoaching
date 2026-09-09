# Golf Coaching Context — Ian

**Last updated:** 2026-09-09

**Purpose:** Carries forward an ongoing golf-coaching relationship so a new session (or an agent) can pick up seamlessly. Ian submits rounds as app screenshots (scorecard + stats pages). He wants direct, honest, data-driven coaching — encouragement paired with real accountability. Voice-to-text messages sometimes have transcription errors (e.g. "pug" = putt, "t" = tee).

Companion file: `round-log.csv` — structured round-by-round data.

---

## Player Profile

- **Age / level:** 27. Handicap index 22.6 (Aug 2025) → **9.2 (Sep 2026)**, computed as the
  best 8 of the last 20 differentials in `data/rounds.csv`. Trajectory: 12.3 (May),
  11.4 (1 Aug), 9.2 (30 Aug), **8.7 (8 Sep)**.
- **Goals:** Break 80 consistently; long-term mid-single-digit handicap.
- **Based:** San Diego. Relocating to Mexico City (expect a temporary dip — unfamiliar courses have cost 4–8 strokes every time).
- **Swing speed:** 100–106 mph. Steep angle of attack.
- **Home courses:**
  - **Enagic Golf Club at Eastlake** (par 72). Blue 6224 yds, Black 6606 yds. Knows it cold.
    **Greens are receptive and he reads the speed well** — the ball checks. So a bad
    short-game or putting number at Eastlake has no conditions excuse behind it;
    read it as a skill result. (Contrast Incline Village, where it was all conditions.)
  - **Campestre de Tijuana** (par 72). White/Blanco ~6261 yds, Azul/Blue ~6581 yds.
- **Player type:** A **feel player**. Historically played his best golf with minimal/no warmup; over-tinkers when he warms up. Best swing thought is simply **"smooth tempo."** Do NOT load him up with mechanics.

---

## Bag

- Driver, 3W, 5W, 7W (stiff shafts on 3W/7W — "game changers")
- Irons through 4-iron (4i ~205y, 5i 190–200y)
- Wedges: 56° (14° bounce), 52°, 50° (12° bounce), 46°, PW (43°)
- Putter: **L.A.B. Golf DF3i** (zero-torque / Lie Angle Balance), bought off the rack 2026-08-18
- Dropped the 4-hybrid — 7W reaches 220 from the rough; 7W carries ~215y
- 2026-08-16: simplified a 16-club inventory down to 14

**Full-swing yardages:** PW 135–145y · 46° 120–135y · 50° 100–120y · 56° under 100y · 5-iron 190–200y · 5-wood 220–250y

**Under consideration:** adding a 54° and 58°. Leaning Vokey — 54° at 14° bounce (F grind), 58° at 12–14° bounce (K grind). Advised against a 60° for now.

---

## Core Diagnosis

Ball-striking is **not** the primary limiter. Scoring leaks are decision/discipline based:

1. **Disaster holes** — the single biggest score driver. Score tracks doubles-or-worse almost perfectly (see round log: 1 double = 76, 6 doubles = 91, with near-identical ball-striking).
2. **Penalty strokes** — 0–1 produces low 80s or better; 3–4 produces high 80s / low 90s.
3. **Short game / putting volatility — now the biggest single lever.** Up-and-down has
   swung **0% to 83%** across eleven measured rounds (mean 33%, sd 24). It is by far the
   least stable thing in his game, and on a round where he misses 10 greens the band
   between his worst and best is worth **3 to 8 strokes**.

   The cleanest evidence is twelve days apart, same course, same tees:

   | | 2026-08-27 | 2026-09-08 |
   |---|---|---|
   | Score | **76** | **86** |
   | GIR | 6 | 8 |
   | Fairways | 5 | 6 |
   | Up-and-down | **83%** | **0%** |
   | Putts | 26 | 36 |
   | Pars / bogeys | 14 / 1 | 4 / 12 |

   He struck it *better* on the 86 and scored ten worse. Ball-striking is not the
   variable; the short game is. Note this is the one place where the doubles model
   does not explain a round — 09-08 had a single disaster hole and still cost him
   four strokes over what the model predicts. Death by bogey, not by disaster.

**Historic pattern:** strong front nines, weaker back nines (fatigue). Reversed in several recent rounds.

**Fast, firm greens are a bigger variable than altitude.** The two Incline Village
rounds (~6,300 ft, first visit) were played on the fastest greens he has ever seen.
Approach shots would not check — they bounced and released straight over the back.
He also could not find the driver and **played the 5-wood off the tee both days**.

| | Incline (2 rds) | home courses (recent) |
|---|---|---|
| Fairways | 8.5 | 6.0 |
| GIR | **3.0** | 7.2 |
| Putts | **38.0** | 34.3 |
| Doubles | **8.5** | 3.5 |

Read that table with the 5-wood in mind: the high fairway count is a *conservative
club finding short grass*, not driving that improved. The mechanism compounds —
5-wood off the tee leaves a longer approach, altitude carries it further still, and
a rock-hard green rejects it. GIR 3 follows, the 38 putts follow from the same green
speed, and the doubles come from being short-sided over the back. Round underneath
both was 85.

**Caution for Mexico City (7,350 ft):** the altitude is worse, but the lesson here is
that *green firmness and speed* need to be scouted alongside carry numbers. Re-learn
carry distances in the first week, and add a landing-zone plan for firm greens —
land it short and let it release rather than flying it to the flag.

**The driver question is still open.** The one clean piece of post-lesson evidence is
2026-09-02 (78 at Eastlake, 9 fairways). The Incline fairway counts say nothing about
the driver because he was not hitting it. The hook has returned before; treat this as
one good round, not a fix confirmed.

**Do not diagnose an away round from app stats alone.** Rounds imported from
18Birdies carry no conditions and no notes. Both Incline rounds looked from the data
like an altitude distance-control problem; the actual causes were green speed and a
club change that the numbers could not show. Ask before concluding.

**Confirmed non-golf variables:** fatigue and fueling. The 91 on 2026-08-18 came after four straight days of golf with no food. Rested + fed rounds are 5–10 strokes better.

---

## Established Coaching Rules / Mantras

- **"First mistake = bogey is now the goal."** After trouble (OB, water, bad lie), reset the target to bogey. Single most important damage-control rule.
- **"Past the hole is fine, short is the problem."** Fixes lag-putt deceleration.
- **One more club on approaches** — his on-course yardages run shorter than his range numbers. Applies to wedges too: don't max out a 50° from 110, hit a smooth 46°.
- **Play the lie, not the number.** From thick rough, take loft and advance the ball; don't ask a low-loft club to reach a number.
- **No par 5 in two** unless the up-and-down game is hot. Par-5 average has been the difference in several rounds (5.3 on good days, 6.0–6.5 on bad).
- **If the driver misbehaves in the first three holes, go to the 5-wood for the day.** He shot his career-best 76 doing exactly this.
- **On heavily contoured/unfamiliar greens:** aim at the pin's tier, not the middle of the green. 20 minutes of lag putts before the round, no exceptions on a new course.

---

## Short Game / Technique Notes

- **Duff and thin are the same low-point error.** Fix: sternum over/ahead of the ball, eyes down through contact, weight slightly forward, don't hang back and scoop.
- **Wedge selection system:**
  - Tight fairway lie + green to work with → **8-iron bump-and-run** (nearly duff-proof)
  - Tight fairway lie + more carry → **50° (12° bounce)** — low bounce for firm turf
  - Fluffy lie / rough / need to stop it → **56° (14° bounce)** — high bounce is *for* soft lies
  - He historically defaults to the 56° on tight lies, which causes the thins
- **"Hover" feel:** hovering woods/long irons at address (subtly) gives a cleaner one-piece takeaway. **Watch:** if the hover creeps too high he tops it (esp. 3-wood). Keep it subtle — bottom of ball at the equator of the clubface. He does NOT hover the hybrid.
- **Driver lesson 2026-08-28** fixed a recurring hook. Immediate result: GIR jumped from ~6/round to 10 and 11 in the two rounds after.

---

## Putting / Grain Knowledge (already taught)

- Read grain via cup edges (shaggy side = grain direction); shiny = down-grain = fast; dull = into-grain = slow.
- Grain grows toward the setting sun (west) and toward water.
- **Kikuyu is the grainiest** he plays (Balboa, Coronado, National City) — grain effect stronger than Bermuda/Zoysia. Into-grain putts reward a firm, accelerating stroke.
- **Bent greens (Torrey Pines, Bay Area) = minimal grain** — read as pure slope, and they're faster.
- Trust feet over eyes for slope. Slope beats grain on undulating greens; grain dominates on flat greens.

---

## Milestones

- Pre-coaching PR: 84 (Jan 2026), plateaued there ~5 times.
- **2026-05-28 — 79 at Eastlake Blue.** First sub-80. Front 9 even par, 11 GIR, birdie on the last from 20 ft, no warmup.
- 2026-06-06 — 84 at Torrey Pines North (129 slope).
- ~7 weeks off own clubs (wedding + honeymoon), returned rusty late July.
- **2026-08-27 — 76 (+4) at Eastlake Blue. Career best.** 12 pars. Did it with only 6 GIR — 26 putts and 83% scrambling carried it. Driver was hooking so he played the 5-wood off the tee all day.
- **2026-09-02 — 78 at Eastlake Blue.** Second-best ever, and the first round that
  looks like the target card: **1 double, 10 GIR, 9 fairways**. Dropped the index to 8.7.
- **2026-09-03/04 — 99 and 95 at Incline Village (Lake Tahoe, ~6,300 ft).** Fastest
  greens he has played; nothing held. Played the 5-wood off the tee both days. See the
  conditions note below; do not read these as a form collapse.
- **2026-08-30 — 82 at Campestre from the Azul tees (6581).** 11 GIR (ties career best), 8 fairways, zero penalties. Same score as a week earlier from tees 320 yds shorter.

---

## Current Assessment (as of 2026-08-31)

- **Ceiling: 72–74.** He has shown 11 GIR and separately 26 putts. Those have not yet overlapped in one round.
- **Floor: 85–87.** Raised from 88–91 by the driver fix — bad days now start from 10–11 GIR and 0–1 penalties.
- **Working range: 78–85, averaging ~81.** Last four rounds: 82, 76, 83, 82.
- **Never had a zero-double round** in 92 complete rounds. Best is one double, eight
  times. This is the clearest unclaimed milestone in the log.
- **Biggest remaining leak:** putting consistency (26 → 35 → 34 over three rounds) and clustered doubles.
- **Putting matters more than the headline R² suggests.** Across all 92 rounds putts
  correlate with score at R² = 0.05, because disaster holes swamp the signal. Within
  recent low-double rounds the correlation is r = 0.79 (n = 12) — the 76 and the 81
  had identical GIR and doubles, and differed only by 26 putts vs 32. Putting sets the
  intercept, so it is the lever for a 6 handicap even though it is not the lever for
  breaking 80. Treat as a strong lead until n grows.
- **Caveat:** only two rounds of post-lesson data. The hook has returned before.

---

## How to Coach Him

- Lead with the honest data read, then the encouragement. He responds to both accountability and belief.
- Always compute the **"what this round really was"** math — strip out the doubles and extra penalties to show the round underneath. He finds this motivating and it's accurate.
- Reinforce established mantras rather than inventing new mechanics.
- Watch for fatigue on back-to-back and multi-day stretches; ask about food and rest before diagnosing a swing.
- Give **score predictions with ranges** when asked before a round — he uses them as a target to beat.
- When he's discouraged, the ball-striking base is real and repeatable; the remaining work is short game, putting, and discipline — the most coachable parts of golf.
