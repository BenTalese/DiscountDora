from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from dora_api.domain.entities.base_entity import BaseEntity


# Status tokens. Small enum, plain str at rest (matches WasteEvent.reason /
# ExpiryEvent.kind conventions).
STATUS_READY = "ready"
STATUS_FAILED = "failed"

# Trigger tokens. `manual` is the only Shape A writer; the column exists
# so scheduled backups (deferred FU) don't need a migration to land.
TRIGGER_MANUAL = "manual"


@dataclass
class Backup(BaseEntity):
    """One row per persisted backup — the library that replaces the
    download-only fast-path (FU-342). A `Backup` row owns a file on
    disk at `storage_path`; deleting the row drops the file too.

    `sections` is the JSON-encoded list of backup_key strings the file
    actually carries (matches the `sections` field inside the file's
    own JSON envelope — surfaced at row level so the library list can
    render "which sections" without opening the file).

    `sha256` is captured on write so the library can flag corruption
    without a full re-read on every visit; the download path streams
    the file directly and the restore path re-reads it in-place.

    `created_by_user_id` FK is SET NULL so removing an admin doesn't
    wipe the backup trail. The row keeps the backup accessible; only
    the "created by" label degrades to "(deleted user)" in the UI.
    """
    created_at: datetime
    created_by_user_id: UUID | None
    size_bytes: int
    sections: str  # JSON-encoded list[str] — see docstring above.
    sha256: str
    status: str
    trigger_kind: str
    storage_path: str

    class Fields(BaseEntity.Fields):
        CREATED_AT = "created_at"
        CREATED_BY_USER_ID = "created_by_user_id"
        SIZE_BYTES = "size_bytes"
        SECTIONS = "sections"
        SHA256 = "sha256"
        STATUS = "status"
        TRIGGER_KIND = "trigger_kind"
        STORAGE_PATH = "storage_path"
