"""Shared ranking for "items you add to lists most often".

Two callers need the same ranked set and used to disagree about how to get
it. `auto_generate` ran the group-by itself; `trim_to_budget` dodged the
query entirely by reading a line's `added_via == auto_frequently_added`
stamp — i.e. trusting a label frozen at insert time to answer a question
about the user's *current* habits. That stamp was deleted on 2026-09-19
(one boolean replaced the provenance enum), so both now come here.

R-003: the "what counts as a habit buy" rule lives in one place on the
server, not once per feature.
"""
from typing import Dict, List, Set
from uuid import UUID

from sqlalchemy import func, select

from dora_api.domain.entities.shopping_list import ShoppingListLine


# How many items the ranking returns when a caller doesn't say. Matches the
# auto-generate dialog's own default so "frequently added" means the same
# set of items wherever the phrase appears.
DEFAULT_FREQUENTLY_ADDED_LIMIT = 10


def rank_frequently_added_ids(session, limit: int) -> List[UUID]:
    """Stock item ids by lifetime count of shopping-list lines, most first.

    Counts every line ever written — ticked and archived included — because
    the signal wanted is "do you buy this habitually", and a finished shop
    is the strongest evidence of that.
    """
    rows = session.execute(
        select(
            ShoppingListLine.stock_item_id,
            func.count().label("add_count"),
        ).group_by(ShoppingListLine.stock_item_id)
    ).all()
    counts: Dict[UUID, int] = {
        row[0]: int(row[1]) for row in rows if row[0] is not None
    }
    ranked = sorted(counts.keys(), key=lambda i: -counts[i])
    return ranked[: max(1, limit)]


def frequently_added_id_set(session, limit: int) -> Set[UUID]:
    """Membership-test shape of `rank_frequently_added_ids`."""
    return set(rank_frequently_added_ids(session, limit))
