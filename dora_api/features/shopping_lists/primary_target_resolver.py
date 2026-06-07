"""Server-side resolver for "which list does a quick-add land on?"

P6-01 Chunk 2 replaces the stored `is_primary` flag with DRAFT-count inference.
The rule (shared by `/primary/lines` quick-add and the C-7 cart button):

  - 0 draft lists  -> NONE      (the client must create a list first)
  - 1 draft list   -> SINGLE    (quick-add lands silently)
  - 2+ draft lists -> AMBIGUOUS (the client asks; sessionStorage remembers)

SHOPPING and DONE lists never count as quick-add targets — quick-add is the
"add it to my next shop" flow, not the in-store ticking flow.

The resolver is a pure function over a list of ShoppingList rows so callers can
reuse the same draft set they already loaded.
"""
from dataclasses import dataclass, field
from typing import Iterable, List, Literal
from uuid import UUID

from dora_api.domain.entities.shopping_list import (SHOPPING_LIST_STATUS_DRAFT,
                                                    ShoppingList)

PrimaryTargetKind = Literal["none", "single", "ambiguous"]


@dataclass(frozen=True, slots=True)
class PrimaryTargetCandidate:
    shopping_list_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class PrimaryTargetOutcome:
    kind: PrimaryTargetKind
    target_list_id: UUID | None = None
    candidates: List[PrimaryTargetCandidate] = field(default_factory=list)


def resolve_primary_target(lists: Iterable[ShoppingList]) -> PrimaryTargetOutcome:
    drafts = [l for l in lists if l.status == SHOPPING_LIST_STATUS_DRAFT]
    if not drafts:
        return PrimaryTargetOutcome(kind="none")
    if len(drafts) == 1:
        return PrimaryTargetOutcome(kind="single", target_list_id=drafts[0].id)
    drafts.sort(key=lambda l: l.created_at)
    return PrimaryTargetOutcome(
        kind="ambiguous",
        candidates=[
            PrimaryTargetCandidate(shopping_list_id=l.id, name=l.name) for l in drafts
        ],
    )
