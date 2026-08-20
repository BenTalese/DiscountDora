"""How the stocktake queue is ordered — the canonical rule.

Chunk 5 of `docs/04_proposals/IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md` (**D-1**).

**Cadence decides membership; belief decides order.** Nothing here changes who
is *in* the queue — that stays `resolve_overdue_map`'s job (mute, snooze, the
engagement gate, the resolved band). This module only answers "of the items
already due, which is most worth walking to first?"

The reason the two can be separated so cleanly is that they are answering
different questions:

  * **cadence** answers *"when did you last look at this?"* — a calendar fact,
    available for every item, and completely indifferent to whether looking
    again would tell you anything new;
  * **belief** answers *"do we already know what's on the shelf?"* — evidence
    from purchases and cooks, available for some items, and exactly the thing
    that makes a walk worth taking.

A stocktake is an *activity* whose output is fresh `last_checked_at` data, so
the best first item is the one where checking produces the most new
information. That's the least-certain item, not the most-overdue one. Overdue
is a decent proxy in the absence of evidence, which is what it always was, and
it stays as the fallback rather than being deleted (D-1: "cadence survives as
the honest answer to 'what do we do with no evidence'").

**Three ranks, in walking order:**

    UNCERTAIN  — belief has signal but isn't confident. Dora doesn't know, so
                 your eyes are worth the most here. Least-certain first.
    OVERDUE    — no belief signal at all. No evidence either way; fall back to
                 most-overdue first, i.e. exactly today's behaviour.
    CONFIDENT  — belief has signal and is confident. Checking these confirms
                 what Dora already worked out, so they sink to the bottom of
                 the walk. **This is Chunk 6's Review set** (D-3/D-4) — the
                 phase that offers them pre-ticked at a desk instead of making
                 you walk to them — which is why the rank is named and exposed
                 rather than being an anonymous sort key.

**Why `CONFIDENT` sinks rather than leaves.** It is tempting to drop confident
items from the queue entirely, and wrong: belief has **no quantity awareness**
(plan §1.3 — buying 1 tin and 12 tins are identical signals) and its "high"
band is reachable off about three logged purchases. It is a good ranking signal
and a bad authority. Cadence still says these are due, so they stay due; belief
only gets to say "look here last".

**The whole thing is gated on the user's stock-inference opt-in.** A user who
switched inference off gets pure cadence order — ranking a list by an inference
they opted out of, on a screen that then can't explain the order, is worse than
not ranking it at all. Same gate the "Dora thinks" overlay uses
(`inference_overlay.SURFACE_STOCK`), so the two can't disagree about whether
belief is in play.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.stock_items.pantry_belief import PantryBelief

# Rank ids. Strings rather than an IntEnum because they ride the DTO to the
# client, which uses them to word its own copy ("least-certain first" vs
# "most-overdue first") — a bare integer would need a second lookup table on
# the far side, i.e. the same fact in two languages (R-003).
RANK_UNCERTAIN = "uncertain"
RANK_OVERDUE = "overdue"
RANK_CONFIDENT = "confident"

_RANK_ORDER = {RANK_UNCERTAIN: 0, RANK_OVERDUE: 1, RANK_CONFIDENT: 2}

# A belief only counts as *confident* at its top band. `medium` is deliberately
# treated as uncertain here even though `inference_overlay` will remark on a
# medium belief: remarking is cheap and reversible, whereas ranking an item
# *down* the walk on a medium hunch risks you never getting to it. Bias toward
# walking.
_CONFIDENT_BAND = "high"


@dataclass(frozen=True, slots=True)
class QueueRank:
    """One item's ranking verdict.

    `sort_key` is ready to hand to `list.sort` — see `rank_queue`. `rank` is
    the exposed reason, and `belief` is carried through so the caller can put
    the wording on the DTO without recomputing anything.
    """
    rank: str
    belief: PantryBelief | None

    @property
    def is_confident(self) -> bool:
        return self.rank == RANK_CONFIDENT


def rank_for(belief: PantryBelief | None) -> str:
    """Which of the three ranks an item falls in.

    A belief that merely echoes a level the user confirmed this week
    (`is_inferred == False`) is **not** signal for this purpose: it tells us
    the record is fresh, not that the shelf was counted. Those items rank as
    `OVERDUE` and sort by the calendar, which is the honest answer.
    """
    if belief is None or not belief.is_inferred:
        return RANK_OVERDUE
    if belief.confidence_band == _CONFIDENT_BAND:
        return RANK_CONFIDENT
    return RANK_UNCERTAIN


def _baseline(item: StockItem) -> datetime:
    """Tiebreak stand-in for "how long since anyone touched this". Mirrors
    `stocktake._overdue_baseline`'s intent, minus the None case — a missing
    baseline sorts as oldest, which is what an untouched item is."""
    stamp = item.last_checked_at
    if stamp is None:
        return datetime.min.replace(tzinfo=UTC)
    return stamp if stamp.tzinfo is not None else stamp.replace(tzinfo=UTC)


def sort_key(
    item: StockItem,
    overdue_days: int,
    belief: PantryBelief | None,
) -> tuple:
    """The full ordering key for one queued item.

    1. **rank** — uncertain, then no-evidence, then confident.
    2. **within `uncertain`: ascending confidence** — least certain first. This
       term is 0 for the other two ranks, so it can't reorder them; their order
       is decided entirely by the overdue term below, unchanged from before
       Chunk 5.
    3. **overdue days, descending** — the old primary key, now the secondary.
    4. **baseline, then name** — so the list is fully deterministic and doesn't
       reshuffle between two calls that see the same data.
    """
    rank = rank_for(belief)
    confidence_term = (
        belief.confidence if (rank == RANK_UNCERTAIN and belief is not None) else 0.0
    )
    return (
        _RANK_ORDER[rank],
        confidence_term,
        -overdue_days,
        _baseline(item),
        item.name.lower(),
    )


def rank_queue(
    entries: list[tuple[int, StockItem]],
    beliefs: dict[UUID, PantryBelief],
) -> list[tuple[StockItem, QueueRank]]:
    """Order `(overdue_days, item)` pairs and pair each with its verdict.

    `beliefs` empty ⇒ every item ranks `OVERDUE` and the result is ordered
    most-overdue-first: byte-for-byte the pre-Chunk-5 order, which is what a
    user with inference switched off must still get.
    """
    ranked = [
        (item, QueueRank(rank=rank_for(beliefs.get(item.id)),
                         belief=beliefs.get(item.id)), days)
        for days, item in entries
    ]
    ranked.sort(key=lambda row: sort_key(row[0], row[2], row[1].belief))
    return [(item, verdict) for item, verdict, _ in ranked]
