"""Unit tests for the recipe query filters (Chunk 4 — `?cookable` / `?max_missing`).

Covers the pure pieces: param parsing, the empty/needs-cookability flags, and the
`matches_missing` predicate that decides which recipes survive the cookability
axes. The DB-backed `load_recipe_cookability` + `_restrict_query` wiring is
integration-level (exercised via the API), not unit-tested here.
"""
from werkzeug.datastructures import MultiDict

from dora_api.features.recipes.get_recipes import (RecipeFilters, _parse_bool,
                                                   _parse_recipe_filters)


# ── _parse_bool ─────────────────────────────────────────────────────────────

def test__parse_bool_tri_state():
    assert _parse_bool("true") is True
    assert _parse_bool("1") is True
    assert _parse_bool("yes") is True
    assert _parse_bool("false") is False
    assert _parse_bool("0") is False
    assert _parse_bool("no") is False
    assert _parse_bool(None) is None
    assert _parse_bool("  ") is None
    assert _parse_bool("maybe") is None  # unrecognised → no constraint


# ── _parse_recipe_filters ─────────────────────────────────────────────────────

def test__parse_filters_reads_cookable_and_max_missing():
    f = _parse_recipe_filters(MultiDict([("cookable", "true"), ("max_missing", "2")]))
    assert f.cookable is True
    assert f.max_missing == 2


def test__parse_filters_defaults_when_absent():
    f = _parse_recipe_filters(MultiDict())
    assert f.cookable is None
    assert f.max_missing is None
    assert f.is_empty is True


def test__parse_filters_rejects_bad_max_missing():
    assert _parse_recipe_filters(MultiDict([("max_missing", "abc")])).max_missing is None
    assert _parse_recipe_filters(MultiDict([("max_missing", "-1")])).max_missing is None


def test__parse_filters_still_reads_tags():
    f = _parse_recipe_filters(MultiDict([("tags_include", "vegan,gluten-free")]))
    assert f.tags_include == ("vegan", "gluten-free")


# ── RecipeFilters flags ───────────────────────────────────────────────────────

def test__is_empty_and_needs_cookability():
    assert RecipeFilters().is_empty is True
    assert RecipeFilters().needs_cookability is False
    assert RecipeFilters(cookable=True).is_empty is False
    assert RecipeFilters(cookable=False).needs_cookability is True
    assert RecipeFilters(max_missing=0).needs_cookability is True
    assert RecipeFilters(tags_include=("vegan",)).needs_cookability is False


# ── matches_missing predicate ─────────────────────────────────────────────────

def test__cookable_true_keeps_only_zero_missing():
    f = RecipeFilters(cookable=True)
    assert f.matches_missing(0) is True   # empty or fully-stocked recipe
    assert f.matches_missing(1) is False
    assert f.matches_missing(3) is False


def test__cookable_false_keeps_only_with_missing():
    f = RecipeFilters(cookable=False)
    assert f.matches_missing(0) is False
    assert f.matches_missing(1) is True


def test__max_missing_caps_the_count():
    f = RecipeFilters(max_missing=2)
    assert f.matches_missing(0) is True
    assert f.matches_missing(2) is True
    assert f.matches_missing(3) is False


def test__cookable_and_max_missing_compose():
    # cookable=True dominates: only 0 missing passes regardless of max_missing.
    f = RecipeFilters(cookable=True, max_missing=5)
    assert f.matches_missing(0) is True
    assert f.matches_missing(1) is False
