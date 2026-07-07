"""POST /api/data/backup/restore — apply a (possibly partial) backup.

Round 2 of N2. Wraps the whole apply in a single SQLAlchemy transaction;
any error rolls back. Returns a structured summary of what landed, what
was skipped, and any FK-resolution warnings.

Two modes:
  - "all_skip_duplicates": import every row whose duplicate-key doesn't
    collide with an existing row.
  - "partial": import only the IDs the user selected. Hard-FK targets
    (locations, groups, recipe collections, parent locations, stock levels)
    are pulled in transparently. Soft-FK columns to missing targets are
    nulled with a warning. Required-FK rows whose target is missing are
    skipped with a warning.

Existing PKs are always skipped — we never overwrite. The user's expected
shape on an existing row is "don't touch it"; rename-on-collide is out of
scope and would surprise everyone.
"""
import json
import logging
import os
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import insert, select

from dora_api.app import db
from dora_api.features.auth.admin_gate import require_admin
from dora_api.features.data.backup import BACKUP_SCHEMA_VERSION
from dora_api.features.data.uploads import staged_path
from dora_api.features.data.restore_shared import (
    BACKUP_KEY_BY_TABLE_NAME,
    CHILD_AUTO_INCLUDE,
    DUPLICATE_KEY_BY_BACKUP_KEY,
    HARD_FK_PULL_IN,
    REQUIRED_FKS,
    RESTORE_ORDER,
    SECTION_BY_BACKUP_KEY,
    SOFT_FK_NULLABLE,
    TABLE_NAME_BY_BACKUP_KEY,
    composite_key,
    decode_value,
    primary_key_columns,
)
from dora_api.features.routers import DATA_ROUTER
from dora_api.infrastructure.api_response import bad_request, internal_server_error, ok
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body


MODE_ALL_SKIP_DUPLICATES = "all_skip_duplicates"
MODE_PARTIAL = "partial"
ALLOWED_MODES = (MODE_ALL_SKIP_DUPLICATES, MODE_PARTIAL)


class RestoreBackupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Exactly one of these must be set. `backup` carries the document
    # inline (small files, tests). `upload_id` references a file staged
    # via /api/data/uploads/* — the canonical path for the SPA now that
    # chunked-resumable uploads are the default.
    backup: dict[str, Any] | None = None
    upload_id: str | None = None
    # Per-section list of selected IDs (or composite PK tuples encoded as
    # comma-joined strings for the m2m tables). Only consulted in "partial".
    selection: dict[str, list[str]] = Field(default_factory=dict)
    mode: str = MODE_ALL_SKIP_DUPLICATES


class RestoreSummary(BaseModel):
    created: dict[str, int]
    skipped: dict[str, int]
    warnings: list[str]


class RestoreBackupHandler:
    def handle(self, request: RestoreBackupRequest) -> RestoreSummary | str:
        # ── Resolve the backup document ───────────────────────────────
        backup, err = self._resolve_backup(request)
        if err is not None:
            return err

        # ── Validate envelope ─────────────────────────────────────────
        version = backup.get("schema_version")
        if not isinstance(version, int):
            return "Backup is missing 'schema_version'."
        if version > BACKUP_SCHEMA_VERSION:
            return (
                f"Backup schema_version {version} is newer than this server "
                f"supports ({BACKUP_SCHEMA_VERSION})."
            )
        if request.mode not in ALLOWED_MODES:
            return f"Unknown mode '{request.mode}'."

        # ── Index backup rows by (key, id) ────────────────────────────
        rows_by_key: dict[str, list[dict[str, Any]]] = {}
        rows_by_id: dict[str, dict[Any, dict[str, Any]]] = {}
        for backup_key, table_name in TABLE_NAME_BY_BACKUP_KEY.items():
            section = backup.get(backup_key, [])
            if not isinstance(section, list):
                return f"Section '{backup_key}' must be a list."
            rows_by_key[backup_key] = section
            table = db.metadata.tables[table_name]
            pk_cols = primary_key_columns(table)
            rows_by_id[backup_key] = {
                composite_key(row, pk_cols): row for row in section
            }

        # ── Existing DB state for duplicate + FK checks ───────────────
        existing_pks: dict[str, set] = {}
        existing_dup_keys: dict[str, set] = {}
        for backup_key, table_name in TABLE_NAME_BY_BACKUP_KEY.items():
            table = db.metadata.tables[table_name]
            pk_cols = primary_key_columns(table)
            existing_rows = db.session.execute(select(table)).all()
            column_names = [c.name for c in table.columns]
            existing_pks[backup_key] = {
                composite_key(
                    {col: r[idx] for idx, col in enumerate(column_names)}, pk_cols
                )
                for r in existing_rows
            }
            if backup_key in DUPLICATE_KEY_BY_BACKUP_KEY:
                key_fn = DUPLICATE_KEY_BY_BACKUP_KEY[backup_key]
                existing_dup_keys[backup_key] = {
                    key_fn({col: r[idx] for idx, col in enumerate(column_names)})
                    for r in existing_rows
                }

        # ── Build the selection set per section ───────────────────────
        # In "all_skip_duplicates" mode the selection is "everything";
        # in "partial" it starts from the user's picks and is expanded.
        selected: dict[str, set] = {k: set() for k in TABLE_NAME_BY_BACKUP_KEY}

        if request.mode == MODE_ALL_SKIP_DUPLICATES:
            for backup_key, section in rows_by_key.items():
                table = db.metadata.tables[TABLE_NAME_BY_BACKUP_KEY[backup_key]]
                pk_cols = primary_key_columns(table)
                for row in section:
                    selected[backup_key].add(composite_key(row, pk_cols))
        else:
            for backup_key, ids in request.selection.items():
                if backup_key not in selected:
                    return f"Unknown selection section '{backup_key}'."
                # IDs come from the SPA as strings; m2m composite IDs come
                # as "<id>|<id>" so we round-trip the same string here.
                for raw_id in ids:
                    selected[backup_key].add((raw_id,) if "|" not in raw_id else tuple(raw_id.split("|")))

            # Children of selected parents ride along.
            for parent_key, child_key, child_fk_col in CHILD_AUTO_INCLUDE:
                # Each parent_pk is single-column for the tables in this map.
                selected_parent_ids = {pk[0] for pk in selected[parent_key]}
                child_table = db.metadata.tables[TABLE_NAME_BY_BACKUP_KEY[child_key]]
                child_pk_cols = primary_key_columns(child_table)
                for row in rows_by_key[child_key]:
                    if str(row.get(child_fk_col)) in selected_parent_ids:
                        selected[child_key].add(composite_key(row, child_pk_cols))

            # Hard-FK pull-in: locations, groups, recipe collections, levels,
            # location parents. Run to fixed point so a deeply nested
            # location subtree fully expands.
            changed = True
            while changed:
                changed = False
                for (src_key, fk_col), target_key in HARD_FK_PULL_IN.items():
                    target_table = db.metadata.tables[TABLE_NAME_BY_BACKUP_KEY[target_key]]
                    target_pk_cols = primary_key_columns(target_table)
                    for src_pk in list(selected[src_key]):
                        src_row = rows_by_id[src_key].get(src_pk)
                        if src_row is None:
                            continue
                        fk_value = src_row.get(fk_col)
                        if not fk_value:
                            continue
                        target_pk = (str(fk_value),)
                        if target_pk in selected[target_key]:
                            continue
                        # Already in DB? Nothing to do.
                        if target_pk in existing_pks[target_key]:
                            continue
                        # Only pull in if the backup actually carries it.
                        if rows_by_id[target_key].get(target_pk) is None:
                            continue
                        selected[target_key].add(target_pk)
                        changed = True

            # m2m join rows where both endpoints land (in DB or in selection)
            # ride along automatically.
            for backup_key in ("product_stock_item_links", "stock_item_substitutes", "meal_recipes"):
                table = db.metadata.tables[TABLE_NAME_BY_BACKUP_KEY[backup_key]]
                pk_cols = primary_key_columns(table)
                for row in rows_by_key[backup_key]:
                    pk = composite_key(row, pk_cols)
                    # Both endpoint targets must be either pre-existing or in selection.
                    endpoints_ok = True
                    for col in pk_cols:
                        target_key = self._resolve_fk_target(backup_key, col)
                        if target_key is None:
                            continue
                        target_pk = (str(row.get(col)),)
                        if (
                            target_pk not in existing_pks.get(target_key, set())
                            and target_pk not in selected[target_key]
                        ):
                            endpoints_ok = False
                            break
                    if endpoints_ok:
                        selected[backup_key].add(pk)

        # ── Apply in dependency order ─────────────────────────────────
        created: dict[str, int] = {}
        skipped: dict[str, int] = {}
        warnings: list[str] = []

        # FK-target tracker: union of pre-existing PKs and freshly-inserted
        # ones. Lets a later row find an earlier sibling without round-tripping.
        present_pks: dict[str, set] = {k: set(v) for k, v in existing_pks.items()}

        try:
            for backup_key in RESTORE_ORDER:
                table = db.metadata.tables[TABLE_NAME_BY_BACKUP_KEY[backup_key]]
                pk_cols = primary_key_columns(table)
                created[backup_key] = 0
                skipped[backup_key] = 0

                for row in rows_by_key[backup_key]:
                    pk = composite_key(row, pk_cols)

                    if pk not in selected[backup_key]:
                        continue
                    if pk in present_pks[backup_key]:
                        skipped[backup_key] += 1
                        continue
                    if backup_key in DUPLICATE_KEY_BY_BACKUP_KEY:
                        key_fn = DUPLICATE_KEY_BY_BACKUP_KEY[backup_key]
                        if key_fn(row) in existing_dup_keys[backup_key]:
                            skipped[backup_key] += 1
                            continue

                    decoded, row_warnings, skip_row = self._decode_row(
                        backup_key, table, row, present_pks
                    )
                    warnings.extend(row_warnings)
                    if skip_row:
                        skipped[backup_key] += 1
                        continue

                    db.session.execute(insert(table).values(**decoded))
                    present_pks[backup_key].add(pk)
                    created[backup_key] += 1

            db.session.commit()
        except Exception as exc:  # noqa: BLE001
            db.session.rollback()
            logging.getLogger(__name__).exception("Restore failed; rolled back.")
            return f"Restore failed and was rolled back: {exc}"

        return RestoreSummary(created=created, skipped=skipped, warnings=warnings)

    @staticmethod
    def _resolve_backup(req: RestoreBackupRequest) -> tuple[dict | None, str | None]:
        """Pull the backup document out of either the inline body or a
        staged upload. Consumes (unlinks) the staged file on success so
        the upload area doesn't accumulate one stale .bin per restore.
        """
        if req.backup is not None and req.upload_id is not None:
            return None, "Provide exactly one of 'backup' or 'upload_id'."
        if req.backup is not None:
            return req.backup, None
        if req.upload_id is None:
            return None, "Either 'backup' or 'upload_id' is required."
        path = staged_path(req.upload_id)
        if not path.exists():
            return None, f"No staged upload found for id {req.upload_id}."
        try:
            with open(path, "rb") as fh:
                doc = json.load(fh)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return None, f"Could not parse staged upload as JSON ({exc})."
        if not isinstance(doc, dict):
            return None, "Staged upload is not a JSON object."
        # Consume — the upload was successfully loaded; subsequent calls
        # with the same id will 404 (which is the intent).
        try:
            os.unlink(path)
        except OSError:
            pass
        return doc, None

    @staticmethod
    def _resolve_fk_target(backup_key: str, column: str) -> str | None:
        # Read the FK target from the SQLAlchemy table definition. Returns
        # the backup_key of the target table, or None for non-FK columns.
        table = db.metadata.tables[TABLE_NAME_BY_BACKUP_KEY[backup_key]]
        col = table.columns.get(column)
        if col is None or not col.foreign_keys:
            return None
        target_table_name = next(iter(col.foreign_keys)).column.table.name
        return BACKUP_KEY_BY_TABLE_NAME.get(target_table_name)

    def _decode_row(
        self,
        backup_key: str,
        table,
        row: dict[str, Any],
        present_pks: dict[str, set],
    ) -> tuple[dict[str, Any], list[str], bool]:
        """Returns (decoded_row, warnings, skip_row)."""
        decoded: dict[str, Any] = {}
        warnings: list[str] = []
        excluded = SECTION_BY_BACKUP_KEY[backup_key].excluded_columns
        for col in table.columns:
            if col.name in excluded:
                # Never restore excluded columns (e.g. password hashes), even
                # if a malformed backup somehow carries them.
                continue
            raw = row.get(col.name)
            value = decode_value(raw, col.type)

            # FK resolution
            target_key = self._resolve_fk_target(backup_key, col.name)
            if target_key is not None and value is not None:
                target_pk = (str(value),)
                if target_pk not in present_pks.get(target_key, set()):
                    # Target missing.
                    if (backup_key, col.name) in SOFT_FK_NULLABLE:
                        warnings.append(
                            f"{backup_key}.{col.name}: target {value} not present; "
                            f"set to null."
                        )
                        value = None
                    elif (backup_key, col.name) in REQUIRED_FKS:
                        warnings.append(
                            f"{backup_key} row {row.get('id') or '<m2m>'} skipped: "
                            f"required {col.name}={value} not present."
                        )
                        return decoded, warnings, True
                    elif col.nullable:
                        warnings.append(
                            f"{backup_key}.{col.name}: target {value} not present; "
                            f"set to null."
                        )
                        value = None
                    else:
                        warnings.append(
                            f"{backup_key} row {row.get('id') or '<m2m>'} skipped: "
                            f"{col.name}={value} not present."
                        )
                        return decoded, warnings, True

            decoded[col.name] = value
        return decoded, warnings, False


@DATA_ROUTER.route("/backup/restore", methods=["POST"])
@has_request_body(RestoreBackupRequest)
def restore_backup():
    _Logger = logging.getLogger(__name__)
    # restore inserts arbitrary rows across every
    # table (users, app_settings, historic offers). Any authenticated
    # caller could invoke it before; the gate closes that HIGH-severity
    # hole.
    _, err = require_admin()
    if err is not None:
        return err
    _Request: RestoreBackupRequest = get_request_body()
    _Result = get_container().inject(RestoreBackupHandler).handle(_Request)
    if isinstance(_Result, str):
        _Logger.warning("Restore validation failed: %s", _Result)
        # User-facing errors land as 400; "rolled back" as 500.
        if _Result.startswith("Restore failed and was rolled back"):
            return internal_server_error(_Result)
        return bad_request(_Result)
    summary = _Result.model_dump()
    _Logger.info(
        "Restore complete: created=%s skipped=%s warnings=%d",
        summary["created"], summary["skipped"], len(summary["warnings"]),
    )
    return ok(summary)
