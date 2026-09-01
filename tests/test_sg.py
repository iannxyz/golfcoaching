"""Tests for the strokes-gained engine."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import sg  # noqa: E402
from sg import HoleStat, Shot  # noqa: E402


# --- benchmark tables ------------------------------------------------------

def test_holed_costs_nothing():
    assert sg.expected_strokes("holed", 0) == 0.0


def test_a_tap_in_is_nearly_one_stroke():
    assert 1.0 <= sg.expected_strokes("green", 1) < 1.05


def test_longer_is_harder_from_every_lie():
    for lie in ("fairway", "rough", "sand", "green"):
        table = sg.BENCHMARK[lie]
        values = [sg.expected_strokes(lie, d) for d, _ in table]
        assert values == sorted(values), f"{lie} is not monotonic"


def test_rough_is_worse_than_fairway_at_the_same_distance():
    for d in (40, 100, 150, 200):
        assert sg.expected_strokes("rough", d) > sg.expected_strokes("fairway", d)


def test_recovery_is_the_worst_lie():
    for d in (100, 150, 200):
        others = [sg.expected_strokes(l, d)
                  for l in ("fairway", "rough", "sand")]
        assert sg.expected_strokes("recovery", d) > max(others)


def test_interpolation_lands_between_the_table_rows():
    lo = sg.expected_strokes("fairway", 140)
    hi = sg.expected_strokes("fairway", 160)
    assert lo < sg.expected_strokes("fairway", 150) < hi


def test_past_the_table_it_keeps_getting_harder():
    # A 700-yard par 5 must not score the same as the last row of the table.
    assert sg.expected_strokes("tee", 700) > sg.expected_strokes("tee", 600)


def test_unknown_lie_and_negative_distance_are_errors():
    with pytest.raises(ValueError):
        sg.expected_strokes("cabbage", 100)
    with pytest.raises(ValueError):
        sg.expected_strokes("fairway", -1)


# --- the hole model --------------------------------------------------------

def test_higher_handicap_expects_a_higher_score():
    scores = [sg.hole_baseline(400, h) for h in (0, 5, 10, 18, 25)]
    assert scores == sorted(scores)


def test_the_hole_model_reproduces_scoring_averages():
    """The check that keeps the whole model honest -- see scripts/calibrate.py."""
    import calibrate
    for handicap, target in calibrate.TARGETS.items():
        predicted = calibrate.predicted_score(handicap)
        assert abs(predicted - target) < 2.0, (
            f"{handicap} index predicts {predicted:.1f}, expected ~{target}")


def test_missing_yardage_falls_back_to_par():
    assert sg.hole_baseline(0, 10, par=3) < sg.hole_baseline(0, 10, par=5)


# --- shot-level strokes gained --------------------------------------------

def test_categories_sum_to_the_total():
    shots = [
        Shot(1, "tee", 400, "fairway", 150),
        Shot(1, "fairway", 150, "green", 20),
        Shot(1, "green", 20, "green", 3),
        Shot(1, "green", 3, "holed"),
    ]
    r = sg.sg_from_shots(shots)
    assert r["total"] == pytest.approx(
        r["ott"] + r["approach"] + r["short"] + r["putting"], abs=1e-6)


def test_total_equals_benchmark_minus_strokes_taken():
    """Strokes gained telescopes: only the first and last term survive."""
    shots = [
        Shot(1, "tee", 400, "rough", 190),
        Shot(1, "rough", 190, "green", 24),
        Shot(1, "green", 24, "green", 3),
        Shot(1, "green", 3, "holed"),
    ]
    expected = sg.expected_strokes("tee", 400) - len(shots)
    assert sg.sg_from_shots(shots)["total"] == pytest.approx(expected, abs=1e-6)


def test_holing_a_long_putt_gains_strokes():
    r = sg.sg_from_shots([Shot(1, "green", 30, "holed")])
    assert r["putting"] > 0.9


def test_three_putting_loses_strokes():
    shots = [Shot(1, "green", 20, "green", 4), Shot(1, "green", 4, "green", 1),
             Shot(1, "green", 1, "holed")]
    assert sg.sg_from_shots(shots)["putting"] < -1.0


def test_a_penalty_costs_a_stroke():
    clean = sg.sg_from_shots([Shot(1, "tee", 400, "fairway", 150)])
    penal = sg.sg_from_shots([Shot(1, "tee", 400, "fairway", 150, penalty=1)])
    assert clean["ott"] - penal["ott"] == pytest.approx(1.0)


def test_shots_are_bucketed_by_lie_and_distance():
    assert sg.category_for("tee", 400) == "ott"
    assert sg.category_for("green", 10) == "putting"
    assert sg.category_for("fairway", 150) == "approach"
    assert sg.category_for("rough", 20) == "short"


def test_vs_handicap_is_kinder_than_vs_tour():
    shots = [Shot(1, "tee", 400, "fairway", 150),
             Shot(1, "fairway", 150, "green", 20),
             Shot(1, "green", 20, "green", 3), Shot(1, "green", 3, "holed")]
    r = sg.sg_from_shots(shots, handicap=12)
    assert r["total_vs_handicap"] > r["total"]


def test_category_baseline_is_negative_and_grows_with_handicap():
    b10 = sg.category_baseline(10)
    b20 = sg.category_baseline(20)
    assert all(v < 0 for v in b10.values())
    assert all(b20[c] < b10[c] for c in sg.CATEGORIES)
    # A scratch amateur is not a tour player, but the gap should be small --
    # a couple of strokes a round, not a couple of strokes a hole.
    assert -4.0 < sum(sg.category_baseline(0).values()) < 0.0


# --- scorecard estimate ----------------------------------------------------

def card(score, **kw):
    """A flat 18-hole card, par 72, scoring ``score``."""
    holes = []
    over = score - 72
    for i in range(18):
        par = 4
        s = par + (1 if i < over else 0)
        holes.append(HoleStat(hole=i + 1, par=par, score=s, yards=385, **kw))
    return holes


def test_a_round_at_your_own_baseline_is_about_zero():
    holes = [HoleStat(hole=i + 1, par=4, score=5, yards=385) for i in range(18)]
    r = sg.sg_from_scorecard(holes, handicap=18, baseline_handicap=18)
    # 90 is close to an 18-handicap's expected score on this course.
    assert abs(r.total) < 4.0


def test_shooting_better_than_baseline_gains_strokes():
    good = [HoleStat(hole=i + 1, par=4, score=4, yards=385) for i in range(18)]
    r = sg.sg_from_scorecard(good, handicap=18)
    assert r.total > 10


def test_the_four_categories_reconstruct_the_total():
    holes = [HoleStat(hole=i + 1, par=4, score=5, yards=385, putts=2,
                      fairway=i % 2 == 0, gir=i % 3 == 0) for i in range(18)]
    r = sg.sg_from_scorecard(holes, handicap=12)
    assert r.total == pytest.approx(
        r.ott + r.approach + r.short + r.putting, abs=1e-6)


def test_fewer_putts_reads_as_better_putting():
    def putting(n):
        holes = [HoleStat(hole=i + 1, par=4, score=5, yards=385, putts=n,
                          gir=True) for i in range(18)]
        return sg.sg_from_scorecard(holes, handicap=12).putting
    assert putting(1) > putting(2) > putting(3)


def test_missing_greens_is_not_scored_as_good_putting():
    """A one-putt after a chip is a short-game save, not a putting gain."""
    gir = [HoleStat(hole=i + 1, par=4, score=4, yards=385, putts=1, gir=True)
           for i in range(18)]
    miss = [HoleStat(hole=i + 1, par=4, score=4, yards=385, putts=1, gir=False)
            for i in range(18)]
    assert (sg.sg_from_scorecard(gir, handicap=12).putting
            > sg.sg_from_scorecard(miss, handicap=12).putting)


def test_penalties_are_charged_to_the_tee():
    clean = card(85, fairway=True, gir=False, putts=2)
    penal = card(85, fairway=True, gir=False, putts=2)
    penal[0].penalties = 3
    assert sg.sg_from_scorecard(penal, 12).ott < sg.sg_from_scorecard(clean, 12).ott


def test_notes_explain_what_could_not_be_separated():
    holes = [HoleStat(hole=i + 1, par=4, score=5, yards=385) for i in range(18)]
    r = sg.sg_from_scorecard(holes, handicap=12)
    assert any("putts" in n for n in r.notes)
    assert r.method == "estimated"
