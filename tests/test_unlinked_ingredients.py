"""IMPL_PLAN_RECIPE_IMPORTER §Chunk 6 — unit tests for the raw_text
grouper the bulk-linker page hangs off.

The endpoints themselves round-trip through the Flask app + repository,
which we exercise implicitly via the SPA browser walk (checklist in
``DORA_VERIFY.md``). These tests pin the *pure* pieces so a
normalisation drift can't silently split what the user sees as one
group.
"""
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from dora_api.features.recipes.unlinked_ingredients import (
    GetUnlinkedIngredientsHandler,
    UnlinkedIngredientsDto,
    normalise_raw_text,
)


@pytest.mark.unit
class TestNormaliseRawText:
    def test__lowercases(self):
        assert normalise_raw_text("Onion") == "onion"

    def test__trims_leading_and_trailing_whitespace(self):
        assert normalise_raw_text("  onion  ") == "onion"

    def test__collapses_internal_whitespace(self):
        assert normalise_raw_text("ground   turkey") == "ground turkey"

    def test__collapses_tabs_and_newlines(self):
        assert normalise_raw_text("chicken\tbreast\nboneless") == \
            "chicken breast boneless"

    def test__matching_pastes_from_different_sites_normalise_to_same_key(self):
        # AllRecipes prints "1 pound Ground Turkey", RecipeTin prints
        # "1 pound  ground turkey  " — same underlying ingredient, must
        # collapse to one group.
        a = normalise_raw_text("1 pound Ground Turkey")
        b = normalise_raw_text("1 pound  ground turkey  ")
        assert a == b == "1 pound ground turkey"

    def test__empty_string_maps_to_empty_key(self):
        # The grouper drops rows whose key normalises to empty, so
        # this needs to stay empty so we don't create a phantom bucket.
        assert normalise_raw_text("") == ""
        assert normalise_raw_text("   \t\n  ") == ""


def _row(raw_text: str, recipe_id: UUID) -> SimpleNamespace:
    """A stub RecipeIngredient row — only the two attrs the handler
    reads: ``raw_text`` + the recipe FK. The ORM binds that FK to the
    underscore-prefixed ``_recipe_id`` property (hidden from
    verify_mappings), and the handler reads *that* name — so the stub
    must expose it under ``_recipe_id`` too. Binding it to the plain
    ``recipe_id`` here is what let this suite pass while the real
    endpoint reported "Used in 0 recipes" for every group (R-032; fixed
    2026-07-20). Using SimpleNamespace keeps the test off the ORM
    mapping registry entirely."""
    return SimpleNamespace(raw_text=raw_text, _recipe_id=recipe_id)


@pytest.mark.unit
class TestGroupUnlinkedIngredients:
    def _run_with_rows(self, rows) -> UnlinkedIngredientsDto:
        class _StubBuilder:
            def all(self, condition=None):
                return rows

        class _StubRepo:
            def get(self, entity_type):
                return _StubBuilder()

        # Constructor injection — no patch.object needed.
        return GetUnlinkedIngredientsHandler(_StubRepo()).handle()

    def test__groups_by_normalised_raw_text(self):
        recipe_a, recipe_b = uuid4(), uuid4()
        dto = self._run_with_rows([
            _row("Ground Turkey", recipe_a),
            _row("  ground   turkey", recipe_b),
        ])
        assert len(dto.unlinked) == 1
        assert dto.unlinked[0].count == 2
        assert set(dto.unlinked[0].used_in_recipe_ids) == {recipe_a, recipe_b}

    def test__sorts_by_count_desc_then_alpha(self):
        r1, r2, r3 = uuid4(), uuid4(), uuid4()
        dto = self._run_with_rows([
            _row("olive oil", r1),
            _row("chicken breast", r1),
            _row("chicken breast", r2),
            _row("chicken breast", r3),
            _row("zaatar", r1),
        ])
        # chicken breast (3) beats olive oil (1) beats zaatar (1);
        # alpha tiebreak keeps olive oil above zaatar.
        assert [g.raw_text for g in dto.unlinked] == [
            "chicken breast", "olive oil", "zaatar",
        ]

    def test__dedupes_recipe_ids_within_a_group(self):
        recipe = uuid4()
        # Same recipe pins the same raw_text twice (legal — e.g. "1
        # onion, diced" and "1 onion, sliced" both normalising to
        # "1 onion" would count once).
        dto = self._run_with_rows([
            _row("onion", recipe),
            _row("onion", recipe),
        ])
        assert dto.unlinked[0].count == 1
        assert dto.unlinked[0].used_in_recipe_ids == [recipe]

    def test__skips_rows_whose_key_normalises_to_empty(self):
        # A whitespace-only raw_text can't happen at write-time (the
        # CHECK constraint would let it through, but the parser
        # trims), but be defensive — the grouper must never emit an
        # empty-labelled bucket.
        dto = self._run_with_rows([
            _row("   ", uuid4()),
            _row("", uuid4()),
        ])
        assert dto.unlinked == []

    def test__display_form_preserves_first_seen_casing_and_spacing(self):
        # The user should see "Ground Turkey" (as pasted) rather than
        # the lowercase key. First-seen wins so the display is
        # deterministic for a given DB order.
        r = uuid4()
        dto = self._run_with_rows([
            _row("Ground Turkey", r),
            _row("ground turkey", r),
        ])
        assert dto.unlinked[0].raw_text == "Ground Turkey"

    def test__handles_no_rows(self):
        dto = self._run_with_rows([])
        assert dto.unlinked == []
