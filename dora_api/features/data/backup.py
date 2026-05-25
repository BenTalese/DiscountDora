"""GET /api/data/backup — install-wide JSON snapshot.

Dumps every section listed in `SECTIONS` (restore_shared) column-by-column
to a single JSON document. Callers can narrow the dump by passing
`?sections=stock_items,recipes,...`; omitting the query string falls back
to the default-on sections.

Per-section `excluded_columns` (e.g. `password_hash` on User) are dropped
from the output and not restored either, so credentials never round-trip.
"""
import base64
import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from flask import Response, jsonify, request, session
from sqlalchemy import select

from dora_api.app import db
from dora_api.domain.entities.user import User
from dora_api.features.auth.register_user import SESSION_USER_ID_KEY
from dora_api.features.data.restore_shared import SECTIONS, SECTION_BY_BACKUP_KEY
from dora_api.features.routers import DATA_ROUTER
from dora_api.infrastructure.api_response import bad_request, unauthorized
from dora_api.infrastructure.utils import get_container
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# Schema version for the on-disk format. Bump when the JSON shape changes in
# a way the restore endpoint can't tolerate.
BACKUP_SCHEMA_VERSION = 1


def _encode_value(value: Any) -> Any:
    """Coerce SQLAlchemy row values into JSON-safe primitives. Bytes go to
    base64 so images round-trip without losing data."""
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return base64.b64encode(bytes(value)).decode("ascii")
    return value


def _dump_table(table_name: str, excluded_columns: frozenset[str]) -> list[dict[str, Any]]:
    table = db.metadata.tables[table_name]
    rows = db.session.execute(select(table)).all()
    column_names = [c.name for c in table.columns if c.name not in excluded_columns]
    indices = [i for i, c in enumerate(table.columns) if c.name not in excluded_columns]
    return [
        {column_names[k]: _encode_value(row[indices[k]]) for k in range(len(column_names))}
        for row in rows
    ]


@dataclass(slots=True)
class BackupResult:
    payload: dict[str, Any]
    filename: str


class GetBackupHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(
        self,
        exported_by_user_id: UUID | None,
        selected_keys: frozenset[str],
    ) -> BackupResult:
        username = "unknown"
        user: User | None = None
        if exported_by_user_id is not None:
            user = self.repository.get(User).by_id(exported_by_user_id)
            if user is not None:
                username = user.username

        now_utc = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "schema_version": BACKUP_SCHEMA_VERSION,
            "exported_at": now_utc.isoformat(),
            "exported_by": username,
            # Honest record of which sections this backup carries — restore
            # can refuse to wipe non-included data on a future "replace, don't
            # merge" mode without re-deriving it from the entity list.
            "sections": sorted(selected_keys),
        }
        for section in SECTIONS:
            if section.backup_key not in selected_keys:
                continue
            payload[section.backup_key] = _dump_table(
                section.table_name, section.excluded_columns,
            )

        # Stamp the user as having taken a backup. Side-effect of the
        # successful dump; persisted so the UI can show "last backup N ago"
        # across sessions.
        if user is not None:
            user.last_backup_at = now_utc
            self.repository.save_changes()

        filename = f"dora-backup-{now_utc.date().isoformat()}.json"
        return BackupResult(payload=payload, filename=filename)


def _resolve_selected_sections() -> frozenset[str] | Response:
    """Honour `?sections=a,b,c` if present; otherwise return every section
    flagged `default_on`. Unknown keys → 400.
    """
    raw = request.args.get("sections")
    if raw is None:
        return frozenset(s.backup_key for s in SECTIONS if s.default_on)
    requested = {token.strip() for token in raw.split(",") if token.strip()}
    unknown = requested - set(SECTION_BY_BACKUP_KEY.keys())
    if unknown:
        return bad_request(
            f"Unknown backup section(s): {', '.join(sorted(unknown))}."
        )
    return frozenset(requested)


@DATA_ROUTER.route("/backup", methods=["GET"])
def get_backup():
    _Logger = logging.getLogger(__name__)
    _UserIdRaw = session.get(SESSION_USER_ID_KEY)
    # Middleware has already gated for an authenticated session before we
    # get here, but we still want the UUID for `exported_by`. Fall back
    # gracefully if the session somehow has a bad value.
    _UserId: UUID | None = None
    if _UserIdRaw:
        try:
            _UserId = UUID(_UserIdRaw)
        except (ValueError, TypeError):
            session.clear()
            return unauthorized()

    _Selected = _resolve_selected_sections()
    if isinstance(_Selected, Response):
        return _Selected

    _Result = get_container().inject(GetBackupHandler).handle(_UserId, _Selected)
    _Logger.info(
        "Built backup: %d section(s), exported_by=%s",
        len(_Selected), _Result.payload.get("exported_by"),
    )

    response: Response = jsonify(_Result.payload)
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{_Result.filename}"'
    )
    return response
