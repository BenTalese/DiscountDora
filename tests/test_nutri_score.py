"""Unit tests for the Nutri-Score algorithm (Updated Algorithm, 2023).

The value of this file is that it pins a **transcription**. `domain/
nutri_score.py` is a copy of published Santé publique France tables (scientific
and technical FAQ V11, Tables 5/6, cross-checked against the official
calculation workbook); the risk is not that the code is subtly wrong, it's that
a threshold was typed wrong, an inequality is `>` where the source says `≥`, or
a band edge is off by one. So most assertions below sit exactly on a published
threshold, or one step either side of it.

The first block is stronger than boundary-poking: it replays the three worked
examples that ship *inside the official workbook*, with the inputs and the
results its own formulas produced. If Dora's arithmetic and the tool European
manufacturers use ever disagree about a named real food, these fail.

A second guard matters here more than usual. The workbook computes the 2017
original and the 2023 update side by side, and several third-party
transcriptions of "Nutri-Score" silently mix them. `test__is_the_updated_
algorithm__not_the_2017_original` asserts the specific values where the two
generations disagree, so a future edit that reaches for the wrong column fails
loudly instead of quietly regrading the cookbook.
"""
import pytest

from dora_api.domain.nutri_score import (
    GRADES,
    PROTEIN_GATE_N_POINTS,
    SALT_G_PER_SODIUM_G,
    NutrientProfile,
    grade_for_score,
    rate,
    sodium_mg_to_salt_g,
)


def _profile(**overrides) -> NutrientProfile:
    """A nutritionally blank food — every component scores zero — so a test can
    vary exactly one axis and read the effect of that axis alone."""
    base = dict(
        energy_kj = 0.0,
        saturated_fat_g = 0.0,
        total_sugars_g = 0.0,
        sodium_mg = 0.0,
        protein_g = 0.0,
        fibre_g = 0.0,
        fvl_percent = 0.0,
    )
    base.update(overrides)
    return NutrientProfile(**base)


# ── The official worked examples ────────────────────────────────────────
# Inputs and expectations lifted from the "General foods" sheet of
# `Nutri-Score_Updated-algorithm_20240404.xlsx` (rows 3–5), reading the updated
# algorithm's own columns: N total `AB`, P total `AC`, score `AD`, grade `AE`.

@pytest.mark.parametrize("name,profile,negative,positive,score,grade", [
    (
        "Apple sauce tinned",
        dict(energy_kj=321, total_sugars_g=17.1, saturated_fat_g=0, sodium_mg=10,
             fvl_percent=90, fibre_g=1.9, protein_g=0.2),
        5, 5, 0, "A",
    ),
    (
        "Salt sea",
        dict(energy_kj=0, total_sugars_g=0, saturated_fat_g=0, sodium_mg=33_800,
             fvl_percent=0, fibre_g=0, protein_g=0),
        20, 0, 20, "E",
    ),
    (
        "Sugar granulated",
        dict(energy_kj=1700, total_sugars_g=100, saturated_fat_g=0, sodium_mg=0,
             fvl_percent=0, fibre_g=0, protein_g=0),
        20, 0, 20, "E",
    ),
])
def test__official_worked_examples__match_the_published_workbook(
        name, profile, negative, positive, score, grade):
    result = rate(_profile(**profile))
    assert result.negative_points == negative, name
    assert result.positive_points == positive, name
    assert result.score == score, name
    assert result.grade == grade, name


def test__apple_sauce__lands_on_the_grade_a_boundary():
    """The worked example is load-bearing beyond its own row: it scores exactly
    0, which is an A under the 2023 bands and a B under the 2017 ones. It is the
    single cheapest guard against the whole file drifting back a generation."""
    result = rate(_profile(energy_kj=321, total_sugars_g=17.1, saturated_fat_g=0,
                           sodium_mg=10, fvl_percent=90, fibre_g=1.9, protein_g=0.2))
    assert result.score == 0
    assert result.grade == "A"


def test__is_the_updated_algorithm__not_the_2017_original():
    """Each assertion is a place the two published generations disagree."""
    # Sugars ran 0–10 on a 4.5 g step originally; now 0–15 on its own scale.
    assert rate(_profile(total_sugars_g=100)).total_sugars_points == 15
    # Protein ran 0–5; now 0–7.
    assert rate(_profile(protein_g=100)).protein_points == 7
    # Salt (g) replaced sodium (mg), 0–10 becoming 0–20.
    assert rate(_profile(sodium_mg=100_000)).salt_points == 20
    # Grade A moved from "< 0" to "< 1".
    assert grade_for_score(0) == "A"
    # The original spared protein above the gate when fvl scored 5; the update
    # does not, so a dish with maximal fruit still loses its protein credit.
    high_n = rate(_profile(total_sugars_g=100, protein_g=100, fvl_percent=100))
    assert high_n.negative_points >= PROTEIN_GATE_N_POINTS
    assert high_n.fvl_points == 5
    assert high_n.protein_counted is False
    assert high_n.protein_points == 7  # reported, but not subtracted
    assert high_n.score == high_n.negative_points - high_n.fibre_points - 5


# ── Negative component: Table 5 boundaries ──────────────────────────────

@pytest.mark.parametrize("energy_kj,expected", [
    (335, 0),      # row 0 is "≤335"
    (335.1, 1),    # row 1 is ">335"
    (3350, 9),
    (3350.1, 10),
    (99_999, 10),  # energy caps at 10
])
def test__energy_points__sit_on_the_published_band_edges(energy_kj, expected):
    assert rate(_profile(energy_kj=energy_kj)).energy_points == expected


@pytest.mark.parametrize("saturated_fat_g,expected", [
    (1, 0), (1.1, 1), (10, 9), (10.1, 10), (500, 10),
])
def test__saturated_fat_points__sit_on_the_published_band_edges(
        saturated_fat_g, expected):
    assert rate(_profile(saturated_fat_g=saturated_fat_g)).saturated_fat_points == expected


@pytest.mark.parametrize("total_sugars_g,expected", [
    (3.4, 0),      # row 0 is "≤3.4"
    (3.5, 1),
    (6.8, 1),
    (6.9, 2),
    (51, 14),
    (51.1, 15),
    (500, 15),     # sugars cap at 15
])
def test__sugars_points__sit_on_the_published_band_edges(total_sugars_g, expected):
    assert rate(_profile(total_sugars_g=total_sugars_g)).total_sugars_points == expected


@pytest.mark.parametrize("salt_g,expected", [
    (0.2, 0),      # row 0 is "≤0.2"
    (0.21, 1),
    (4.0, 19),
    (4.1, 20),
    (99, 20),      # salt caps at 20
])
def test__salt_points__sit_on_the_published_band_edges(salt_g, expected):
    """Expressed in salt because Table 5 is; fed in as sodium because Dora is."""
    sodium_mg = salt_g / SALT_G_PER_SODIUM_G * 1000.0
    assert rate(_profile(sodium_mg=sodium_mg)).salt_points == expected


def test__sodium_converts_to_salt_by_the_published_factor():
    assert sodium_mg_to_salt_g(1000) == pytest.approx(2.5)
    assert sodium_mg_to_salt_g(None) is None


# ── Positive component: Table 6 boundaries ──────────────────────────────

@pytest.mark.parametrize("protein_g,expected", [
    (2.4, 0),      # row 0 is "≤2.4"
    (2.5, 1),
    (17, 6),
    (17.1, 7),
    (500, 7),
])
def test__protein_points__sit_on_the_published_band_edges(protein_g, expected):
    assert rate(_profile(protein_g=protein_g)).protein_points == expected


@pytest.mark.parametrize("fibre_g,expected", [
    (3.0, 0),      # row 0 is "≤3.0"
    (3.1, 1),
    (4.1, 1),
    (4.2, 2),
    (7.4, 4),
    (7.5, 5),
    (500, 5),
])
def test__fibre_points__sit_on_the_published_band_edges(fibre_g, expected):
    assert rate(_profile(fibre_g=fibre_g)).fibre_points == expected


@pytest.mark.parametrize("fvl_percent,expected", [
    (40, 0),       # row 0 is "<40"/"≤40"
    (40.1, 1),
    (60, 1),
    (60.1, 2),
    (80, 2),
    (80.1, 5),     # 3 and 4 points are unreachable, as published
    (100, 5),
])
def test__fvl_points__sit_on_the_published_band_edges(fvl_percent, expected):
    assert rate(_profile(fvl_percent=fvl_percent)).fvl_points == expected


def test__fvl_points__skip_three_and_four_entirely():
    """Not a transcription slip — Table 6 leaves those rows blank."""
    awarded = {rate(_profile(fvl_percent=p)).fvl_points for p in range(0, 101)}
    assert awarded == {0, 1, 2, 5}


# ── The protein gate ────────────────────────────────────────────────────

def test__protein_counts_below_the_gate():
    result = rate(_profile(total_sugars_g=20, protein_g=100))
    assert result.negative_points < PROTEIN_GATE_N_POINTS
    assert result.protein_counted is True
    assert result.score == result.negative_points - result.positive_points


def test__protein_drops_out_at_the_gate_exactly():
    """N == 11 is inside the gate: the rule is "greater than or equal to 11"."""
    at_gate = rate(_profile(total_sugars_g=37.5, protein_g=100))
    assert at_gate.negative_points == PROTEIN_GATE_N_POINTS
    assert at_gate.protein_counted is False


def test__gated_protein_is_reported_but_not_subtracted():
    """The UI needs to be able to say "your protein didn't count, here's why",
    so the points stay on the result even when the score ignores them."""
    result = rate(_profile(total_sugars_g=100, protein_g=100, fibre_g=100))
    assert result.protein_counted is False
    assert result.protein_points == 7
    assert result.score == result.negative_points - result.fibre_points - result.fvl_points


# ── Missing data ────────────────────────────────────────────────────────

def test__missing_nutrients_score_zero_points():
    blank = NutrientProfile(None, None, None, None, None, None, None)
    result = rate(blank)
    assert result.negative_points == 0
    assert result.positive_points == 0
    assert result.score == 0
    assert result.grade == "A"


def test__a_missing_negative_flatters_and_a_missing_positive_penalises():
    """The asymmetry the profile's docstring warns about, pinned so nobody
    'fixes' it into a symmetric default without reading why."""
    known_sugar = rate(_profile(total_sugars_g=50)).score
    unknown_sugar = rate(_profile(total_sugars_g=None)).score
    assert unknown_sugar < known_sugar

    known_fibre = rate(_profile(fibre_g=10)).score
    unknown_fibre = rate(_profile(fibre_g=None)).score
    assert unknown_fibre > known_fibre


# ── Grade bands ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("score,expected", [
    (-15, "A"), (0, "A"),
    (1, "B"), (2, "B"),
    (3, "C"), (10, "C"),
    (11, "D"), (18, "D"),
    (19, "E"), (55, "E"),
])
def test__grade_bands__sit_on_the_published_edges(score, expected):
    assert grade_for_score(score) == expected


def test__every_band_is_reachable_and_ordered():
    scores = range(-20, 60)
    seen = [grade_for_score(s) for s in scores]
    assert set(seen) == set(GRADES)
    # Monotonic: a worse score never yields a better letter.
    assert seen == sorted(seen)
