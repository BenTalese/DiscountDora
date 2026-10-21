"""Unit tests for the shared noun-pluralisation helper
(``dora_api.infrastructure.utils.pluralize``).

DR-4 (FU-578 #10): this helper is the single source for pluralising nouns in
user-facing copy, replacing the lazy "day(s)" placeholder and the scattered
``day{'s' if n != 1 else ''}`` idiom. The tests pin the |count| == 1 boundary
(including the negative case that the "days ago" copy relies on) and the custom
plural override.
"""
import pytest

from dora_api.infrastructure.utils import pluralize


@pytest.mark.parametrize(
    "count,expected",
    [
        (1, "day"),      # exactly one → singular
        (-1, "day"),     # one day ago → still singular (abs)
        (0, "days"),     # zero → plural, matches English usage
        (2, "days"),
        (-3, "days"),    # "expired 3 days ago"
        (100, "days"),
    ],
)
def test__pluralize__day(count: int, expected: str) -> None:
    assert f"{abs(count)} {pluralize(count, 'day')}" == f"{abs(count)} {expected}"


def test__pluralize__custom_plural() -> None:
    assert pluralize(1, "match", "matches") == "match"
    assert pluralize(3, "match", "matches") == "matches"


def test__pluralize__default_plural_appends_s() -> None:
    assert pluralize(2, "item") == "items"
