"""Tests for the scoring model and the round-underneath math."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import add_round  # noqa: E402
import model  # noqa: E402
from model import Round  # noqa: E402


def make(**kw):
    base = dict(date="2026-08-27", score=76, par=72, holes=18,
                birdies=1, pars=14, bogeys=1, doubles_or_worse=2)
    base.update(kw)
    return Round(**base)


# --- round underneath ------------------------------------------------------

def test_disaster_strokes_falls_out_of_the_counts():
    # 76 on a par 72 with 1 birdie, 14 pars, 1 bogey, 2 doubles.
    # to_par 4 = -1 birdie + 1 bogey + 4 over par on the two disaster holes.
    assert make().disaster_strokes == 4


def test_round_underneath_replays_doubles_as_bogeys():
    # Two holes cost 4 over par; as bogeys they would cost 2. Save 2 strokes.
    assert make().round_underneath == 74


def test_round_underneath_on_a_blow_up_round():
    # The real 2026-08-18: 91 with six doubles-or-worse.
    r = make(date="2026-08-18", score=91, birdies=0, pars=7, bogeys=5,
             doubles_or_worse=6)
    assert r.disaster_strokes == 14        # 19 to par + 0 birdies - 5 bogeys
    assert r.round_underneath == 83        # 91 - (14 - 6)


def test_round_underneath_never_beats_the_score():
    for r in model.load():
        if r.round_underneath is not None:
            assert r.round_underneath <= r.score


def test_a_clean_round_has_no_tax():
    r = make(score=74, birdies=0, pars=16, bogeys=2, doubles_or_worse=0)
    assert r.disaster_strokes == 0
    assert r.round_underneath == 74


def test_missing_inputs_give_none_not_a_wrong_number():
    assert make(birdies=None).round_underneath is None
    assert Round(date="2026-01-01").round_underneath is None


# --- regression ------------------------------------------------------------

def test_doubles_beat_gir_as_a_predictor():
    rounds = model.load()
    doubles, gir = model.fit(rounds), model.fit(rounds, "gir")
    assert doubles.r2 > gir.r2
    assert doubles.r2 > 0.6


def test_each_double_costs_about_two_strokes():
    f = model.fit(model.load())
    assert 1.5 < f.slope < 3.0


def test_fit_needs_variation_and_a_sample():
    assert model.fit([make(), make()]) is None                    # too few
    assert model.fit([make() for _ in range(5)]) is None           # no variation


def test_prediction_range_brackets_the_midpoint():
    lo, mid, hi = model.predict_score(model.load(), 2)
    assert lo < mid < hi


# --- context flags ---------------------------------------------------------

def test_consecutive_days_are_counted():
    rs = [Round(date=d, score=85, holes=18)
          for d in ("2026-08-15", "2026-08-16", "2026-08-17")]
    assert model.days_played_streak(rs, "2026-08-17") == 3
    assert model.days_played_streak(rs, "2026-08-15") == 1


def test_a_gap_breaks_the_streak():
    rs = [Round(date=d, score=85, holes=18)
          for d in ("2026-08-10", "2026-08-16", "2026-08-17")]
    assert model.days_played_streak(rs, "2026-08-17") == 2


def test_first_visit_detected_once():
    a = Round(date="2026-08-08", course="Corica Park North", score=90, holes=18)
    b = Round(date="2026-09-08", course="Corica Park North", score=84, holes=18)
    assert model.is_first_visit([a, b], a)
    assert not model.is_first_visit([a, b], b)


def test_layoff_flagged():
    rs = [Round(date="2026-06-06", score=84, holes=18),
          Round(date="2026-07-24", score=93, holes=18)]
    assert model.layoff_days(rs, rs[1]) == 48
    assert any("days since" in f for f in model.flags(rs, rs[1]))


# --- loading the real log --------------------------------------------------

def test_the_real_log_loads_and_is_sane():
    rounds = model.load()
    assert len(rounds) > 90
    full = [r for r in rounds if r.is_full]
    assert len(full) > 85
    assert all(55 <= r.score <= 150 for r in full)
    assert rounds == sorted(rounds, key=lambda r: r.date)


def test_hole_counts_add_up_where_all_four_are_present():
    for r in model.load():
        counts = (r.birdies, r.pars, r.bogeys, r.doubles_or_worse)
        if r.is_full and None not in counts:
            assert sum(counts) == 18, f"{r.date}: {counts} does not total 18"


# --- add_round validation --------------------------------------------------

@pytest.mark.parametrize("row, expected", [
    ({"score": 250}, "outside any plausible range"),
    ({"score": 80, "front": 40, "back": 41}, "!= score"),
    ({"score": 80, "gir": 19}, "outside 0..18"),
    ({"score": 80, "putts": 9}, "outside 18..50"),
    ({"score": 80, "up_down_pct": 140}, "not a percentage"),
])
def test_validation_rejects_bad_reads(row, expected):
    problems = add_round.validate({"score": 80, **row})
    assert any(expected in p for p in problems), problems


def test_validation_accepts_a_good_card():
    assert add_round.validate({
        "score": 82, "front": 41, "back": 41, "fairways_hit": 6, "gir": 6,
        "putts": 29, "three_putts": 0, "doubles_or_worse": 1, "up_down_pct": 12.5,
    }) == []


def test_blank_optional_fields_are_allowed():
    assert add_round.validate({"score": 82, "gir": "", "putts": None}) == []


def test_upsert_replaces_rather_than_duplicates(tmp_path):
    log = tmp_path / "round-log.csv"
    row = dict.fromkeys(add_round.COLUMNS, "")
    row.update(date="2026-09-01", course="Test", score=80)
    assert add_round.upsert(row, log) == "added"
    row["score"] = 78
    assert add_round.upsert(row, log) == "updated"
    text = log.read_text()
    assert text.count("2026-09-01") == 1
    assert "78" in text
