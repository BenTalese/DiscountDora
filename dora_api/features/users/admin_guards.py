"""The one answer to "would this leave the install without an admin who can
sign in?" — shared by the PATCH (demote / deactivate) and DELETE guards.

With `is_active` in play, "the last admin" has to mean the last admin who
can actually get in. The DELETE guard used to count `is_admin` rows alone,
so with one active admin and one deactivated one the two guards disagreed
about whether the install still had an admin (finalisation 13-R3). Counted
in Python over the (household-sized) admin set rather than as a SQL `!=`,
so the UUID-vs-str comparison trap FU-528 hit can't reappear here.
"""
from __future__ import annotations

from uuid import UUID

from dora_api.domain.entities.user import User
from dora_api.infrastructure.ports import Repository
from dora_api.persistence.field import EntityField


def other_usable_admins(repository: Repository, user_id: UUID | str) -> int:
    """How many admins *other than `user_id`* are active (could still sign in)."""
    admins = repository.get(User).all(
        EntityField(User, User.Fields.IS_ADMIN).eq(True)
        & EntityField(User, User.Fields.IS_ACTIVE).eq(True)
    )
    return sum(1 for a in admins if str(a.id) != str(user_id))
