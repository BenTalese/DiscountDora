from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


@dataclass
class PushSubscription(BaseEntity):
    """C-9.8 — one browser's web-push registration for a user.

    Web Push (RFC 8030 + VAPID) gives each subscribed browser+device a
    unique ``endpoint`` URL on its vendor's push service (Mozilla AutoPush
    / Google FCM / Apple). The ``p256dh`` + ``auth`` pair are the
    application-server keys the browser provides so we can ECE-encrypt
    payloads only that browser can decrypt. The endpoint is the de-facto
    primary key — a re-subscribe from the same browser produces the same
    endpoint, so re-inserts on conflict update the keys in place rather
    than stacking duplicate rows. ``user_agent`` is captured so the
    Preferences page can show "Chrome on Linux" / "Firefox on Android"
    when (later) we surface a per-device list.
    """
    user_id: UUID
    endpoint: str
    p256dh: str
    auth: str
    user_agent: str | None
    created_at: datetime
    last_seen_at: datetime | None = None

    class Fields(BaseEntity.Fields):
        USER_ID = "user_id"
        ENDPOINT = "endpoint"
        P256DH = "p256dh"
        AUTH = "auth"
        USER_AGENT = "user_agent"
        CREATED_AT = "created_at"
        LAST_SEEN_AT = "last_seen_at"
