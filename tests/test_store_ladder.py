"""The store ladder's rung ordering.

`resolve_store_id` decides which store a shopping line belongs to, which is
what puts it in a section under Order-by → Store and which bucket it feeds in
"Where you'll spend it". Getting a rung wrong doesn't fail — it silently
re-groups the list, which is exactly the class of bug a hand-check is bad at
catching and a test is cheap at pinning (the `DORA_VERIFY_TRIAGE.md` bar).

The two orderings under test are both deliberate and both counter-intuitive
in one direction or the other:

* **Intent beats history**, the reverse of `line_paid_unit_price`. That ladder
  answers "what did this cost", where what you really paid beats an advertised
  price. This one answers "where do I plan to buy it", where a stated intention
  beats where you happened to shop last time.
* **The more specific intent wins.** `planned_store_id` is a choice made for
  *this* list; `usual_store_id` is a habit spanning every list. The exception
  must not be overruled by the rule — that was the whole point of adding the
  planned rung on 2026-08-28.
"""
from uuid import UUID

from dora_api.features.shopping_lists._line_price import resolve_store_id


PURCHASED = UUID(int=1)
PLANNED = UUID(int=2)
USUAL = UUID(int=3)
LAST = UUID(int=4)
OFFER = UUID(int=5)


def _resolve(**overrides):
    """All five rungs populated by default, so each test can knock one out and
    assert what the ladder falls through to."""
    kwargs = {
        "purchased_store_id": PURCHASED,
        "planned_store_id": PLANNED,
        "usual_store_id": USUAL,
        "last_purchase_store_id": LAST,
        "chosen_offer_store_id": OFFER,
    }
    kwargs.update(overrides)
    return resolve_store_id(**kwargs)


def test__purchased_wins_over_everything():
    """Where you actually bought it is a fact; the rest are predictions."""
    assert _resolve() == PURCHASED


def test__planned_beats_usual__the_exception_outranks_the_habit():
    """The rung added 2026-08-28. "Get this one at Aldi, just this week" must
    not be overruled by "I usually buy this at Coles"."""
    assert _resolve(purchased_store_id=None) == PLANNED


def test__planned_beats_history_and_offers_too():
    assert _resolve(
        purchased_store_id=None, usual_store_id=None,
    ) == PLANNED


def test__usual_beats_last_purchase__intent_over_history():
    """The inversion against the money ladder. Buying somewhere once because
    you were passing does not change where you intend to shop."""
    assert _resolve(purchased_store_id=None, planned_store_id=None) == USUAL


def test__last_purchase_beats_the_offer():
    """Your own history outranks an advertised price from a store you may have
    never set foot in."""
    assert _resolve(
        purchased_store_id=None, planned_store_id=None, usual_store_id=None,
    ) == LAST


def test__offer_is_the_last_resort():
    assert _resolve(
        purchased_store_id=None, planned_store_id=None, usual_store_id=None,
        last_purchase_store_id=None,
    ) == OFFER


def test__no_rung_populated_is_the_no_store_set_bucket():
    """None is a real answer, not a failure: it routes the line to the
    "No store set" bucket rather than inventing a store."""
    assert resolve_store_id(
        purchased_store_id=None, planned_store_id=None, usual_store_id=None,
        last_purchase_store_id=None, chosen_offer_store_id=None,
    ) is None
