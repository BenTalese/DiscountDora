"""Settings rebuild Phase 4 (§2.9) — user profile-picture route.

  GET /api/users/<user_id>/image

Returns the user's profile picture bytes, or 404 when unset. Images are
stored as data-URL strings on the entity (`data:image/png;base64,…`) so the
SPA can point a plain `<img src>` at this route without inlining megabytes of
base64 into every user JSON. Same pattern as the store / stock-item / recipe
image routes.

Auth: any authenticated user can fetch any user's picture (used by the menu
bar, the Account header, and the admin Users list). The session middleware
already gates the route; we don't add a per-user check — the StockItem /
Store image endpoints set the same precedent.
"""
import base64
import re

from flask import Response

from dora_api.domain.entities.user import User
from dora_api.features.routers import USER_ROUTER
from dora_api.infrastructure.api_response import not_found
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


_DATA_URL_RE = re.compile(r"^data:(?P<mime>[\w/+.-]+);base64,(?P<data>.+)$", re.DOTALL)


def _decode_data_url(blob: bytes | None) -> tuple[str, bytes] | None:
    """Return `(mime, raw_bytes)` from a stored data-URL blob, or None when
    the blob is empty or malformed (caller treats either as "no image")."""
    if not blob:
        return None
    try:
        data_url = blob.decode("utf-8", "ignore")
    except Exception:  # pragma: no cover — bytes.decode("utf-8", "ignore") doesn't raise
        return None
    match = _DATA_URL_RE.match(data_url)
    if not match:
        return None
    try:
        raw = base64.b64decode(match.group("data"), validate=False)
    except (ValueError, TypeError):
        return None
    return match.group("mime"), raw


@USER_ROUTER.route("/<uuid:user_id>/image", methods=["GET"])
def get_user_image(user_id):
    repository = SqlAlchemyRepository()
    user = repository.get(User).by_id(user_id)
    if user is None:
        return not_found(User.__name__, user_id)
    decoded = _decode_data_url(getattr(user, "image", None))
    if decoded is None:
        return not_found(User.__name__, user_id)
    mime, raw = decoded
    return Response(
        raw,
        mimetype=mime,
        headers={"Cache-Control": "no-cache"},
    )
