from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


PURPOSE_VERIFY_EMAIL = "verify_email"
PURPOSE_RESET_PASSWORD = "reset_password"
# PURPOSE_CHANGE_EMAIL retired 2026-08-12 (FU-620) — the verified email-change
# flow was removed; email now edits directly via PATCH /auth/me.
ALLOWED_PURPOSES = (PURPOSE_VERIFY_EMAIL, PURPOSE_RESET_PASSWORD)


@dataclass
class AuthToken(BaseEntity):
    """A short-lived single-use credential for an out-of-band auth flow.

    `token_hash` is the SHA-256 of the raw token; the raw value only
    ever appears in the outbound email. `payload` is purpose-specific
    free text — used by `change_email` to carry the candidate new
    address until the user confirms.
    """
    user_id: UUID
    token_hash: str
    purpose: str
    expires_at: datetime
    created_at: datetime
    consumed_at: datetime | None = None
    payload: str | None = None

    class Fields(BaseEntity.Fields):
        USER_ID = "user_id"
        TOKEN_HASH = "token_hash"
        PURPOSE = "purpose"
        EXPIRES_AT = "expires_at"
        CONSUMED_AT = "consumed_at"
        CREATED_AT = "created_at"
        PAYLOAD = "payload"
