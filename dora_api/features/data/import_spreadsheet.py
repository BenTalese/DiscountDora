"""Spreadsheet import — Data → Import → Spreadsheet.

Two endpoints:
  POST /api/data/import/spreadsheet/inspect
      Body: {"upload_id": "<staged-uuid>"}
      Returns: { sheets, preview_rows, detected_columns, auto_mapping }
  POST /api/data/import/spreadsheet/commit
      Body: { upload_id, sheet, column_map, options }
      Returns: { summary: {created, skipped, errors}, rows: [...] }

The user uploads via the existing chunked-upload stack
(POST /api/data/uploads/*) and passes the resulting `upload_id` to both
endpoints. Inspect leaves the staged file in place; commit consumes it.

Supported formats: .xlsx (via openpyxl) and .csv (stdlib `csv` module).
Detection is by extension fallback to magic bytes; the SPA passes the
filename so we know which path to take.

Mapping is opinionated:
  required: name
  optional: level, location, group, expiry, is_essential
The frontend's column-mapping UI sets which spreadsheet column feeds
each target. `is_essential` maps to StockItem.is_flagged (the schema
has no is_essential — is_flagged is the closest existing flag).

Row-level errors carry the row number, the offending value, and a
human-readable reason. Halt-on-error aborts the whole transaction;
otherwise the valid rows still land and the errors are surfaced row-by-
row in the response.
"""
import csv
import io
import logging
import os
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Iterator

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import insert, select

from dora_api.app import db
from dora_api.domain.entities.stock_group import StockGroup
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_level import StockLevel
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.domain.stock_status import StockStatus, level_for_status
from dora_api.features.auth.admin_gate import require_admin
from dora_api.features.data.uploads import staged_path
from dora_api.features.routers import DATA_ROUTER
from dora_api.infrastructure.api_response import bad_request, internal_server_error, not_found, ok
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


# Target fields with their synonyms for auto-mapping. Lowercased,
# trimmed, punctuation stripped before matching.
TARGET_FIELDS: tuple[str, ...] = (
    "name", "level", "location", "group", "expiry", "is_essential",
)
COLUMN_SYNONYMS: dict[str, tuple[str, ...]] = {
    "name": ("name", "item", "itemname", "product", "productname", "title"),
    "level": ("level", "stocklevel", "stock", "status", "quantity"),
    "location": ("location", "where", "place", "shelf", "pantry", "spot"),
    "group": ("group", "category", "tag", "type", "kind"),
    "expiry": ("expiry", "bestbefore", "useby", "expires", "expiration", "expirydate"),
    "is_essential": ("isessential", "essential", "essentials", "flagged", "important", "starred"),
}

# How many rows to ship back in the preview from /inspect.
PREVIEW_ROW_COUNT = 5


def _normalise_header(value: str) -> str:
    """Lowercase + strip whitespace and punctuation for fuzzy column matching."""
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _is_truthy(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    s = str(value).strip().lower()
    return s in {"y", "yes", "true", "1", "t", "on", "x", "✓"}


def _coerce_to_date(value: Any) -> date | None:
    """Accept date / datetime / ISO string / common locale strings. Returns
    None for empty cells; raises ValueError for unparseable non-empty values.
    """
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        # Try ISO first, then a couple of common fallbacks (au-style D/M/Y
        # and US-style M/D/Y as a last resort — surface unambiguous formats
        # cleanly and let weird shapes raise).
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
    raise ValueError(f"Could not parse '{value}' as a date.")


def _read_sheets(path: str, filename: str) -> dict[str, list[list[Any]]]:
    """Returns {sheet_name: [row_0, row_1, ...]} for any supported format.
    Row 0 is the header row. Cells preserve their original Python types
    (openpyxl returns datetime/int/etc.; csv returns strings).
    """
    lower = filename.lower()
    if lower.endswith(".csv"):
        # CSVs are single-sheet; we synthesise one named after the file.
        with open(path, "rb") as raw:
            data = raw.read()
        # UTF-8 with BOM is common from Excel; sniff and strip.
        if data.startswith(b"\xef\xbb\xbf"):
            data = data[3:]
        text = data.decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(text))
        rows = [row for row in reader]
        sheet_name = os.path.basename(filename) or "csv"
        return {sheet_name: rows}

    if lower.endswith(".xlsx"):
        # Importing here so installs without openpyxl don't blow up the
        # whole api on module import (only matters if you actually try to
        # import a spreadsheet).
        from openpyxl import load_workbook
        wb = load_workbook(filename=path, read_only=True, data_only=True)
        try:
            out: dict[str, list[list[Any]]] = {}
            for sheet in wb.sheetnames:
                ws = wb[sheet]
                rows: list[list[Any]] = []
                for row in ws.iter_rows(values_only=True):
                    rows.append(list(row))
                out[sheet] = rows
            return out
        finally:
            wb.close()

    raise ValueError(
        f"Unsupported file type for spreadsheet import: '{filename}'. "
        "Supported: .xlsx, .csv."
    )


def _build_auto_mapping(headers: list[str]) -> dict[str, str | None]:
    """Pick the most-likely spreadsheet column for each target field."""
    normalised = [(_normalise_header(h or ""), h) for h in headers]
    mapping: dict[str, str | None] = {field: None for field in TARGET_FIELDS}
    used: set[str] = set()
    for target in TARGET_FIELDS:
        for synonym in COLUMN_SYNONYMS[target]:
            for norm, original in normalised:
                if not norm or original in used:
                    continue
                if norm == synonym:
                    mapping[target] = original
                    used.add(original)
                    break
            if mapping[target] is not None:
                break
        if mapping[target] is not None:
            continue
        # Fall back to substring match if no exact synonym landed.
        for synonym in COLUMN_SYNONYMS[target]:
            for norm, original in normalised:
                if not norm or original in used:
                    continue
                if synonym in norm:
                    mapping[target] = original
                    used.add(original)
                    break
            if mapping[target] is not None:
                break
    return mapping


# ── Inspect ────────────────────────────────────────────────────────────

class InspectSpreadsheetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    upload_id: str
    filename: str = Field(min_length=1)


@dataclass(slots=True)
class InspectSpreadsheetResponse:
    sheets: list[str]
    preview_rows: dict[str, list[list[Any]]]
    detected_columns: dict[str, list[str]]
    auto_mapping: dict[str, dict[str, str | None]]
    target_fields: list[str]
    warnings: list[str] = field(default_factory=list)


class InspectSpreadsheetHandler:
    def handle(self, request: InspectSpreadsheetRequest) -> InspectSpreadsheetResponse | str:
        path = staged_path(request.upload_id)
        if not path.exists():
            return f"No staged upload found for id {request.upload_id}."
        try:
            sheets = _read_sheets(str(path), request.filename)
        except ValueError as exc:
            return str(exc)
        except Exception as exc:  # noqa: BLE001
            logging.getLogger(__name__).exception("Failed to read spreadsheet.")
            return f"Could not read spreadsheet: {exc}"

        sheet_names = list(sheets.keys())
        preview_rows: dict[str, list[list[Any]]] = {}
        detected_columns: dict[str, list[str]] = {}
        auto_mapping: dict[str, dict[str, str | None]] = {}
        warnings: list[str] = []

        for name in sheet_names:
            rows = sheets[name]
            if not rows:
                detected_columns[name] = []
                preview_rows[name] = []
                auto_mapping[name] = {f: None for f in TARGET_FIELDS}
                warnings.append(f"Sheet '{name}' is empty.")
                continue

            header = [str(h) if h is not None else "" for h in rows[0]]
            detected_columns[name] = header

            # JSON-serialise dates/datetimes/bytes etc.; cells we can't
            # represent cleanly fall back to str().
            sample = []
            for row in rows[1:1 + PREVIEW_ROW_COUNT]:
                cells = []
                for value in row:
                    if isinstance(value, (date, datetime)):
                        cells.append(value.isoformat())
                    elif isinstance(value, bytes):
                        cells.append(value.decode("utf-8", errors="replace"))
                    elif value is None or isinstance(value, (str, int, float, bool)):
                        cells.append(value)
                    else:
                        cells.append(str(value))
                sample.append(cells)
            preview_rows[name] = sample

            mapping = _build_auto_mapping(header)
            auto_mapping[name] = mapping
            if mapping["name"] is None:
                warnings.append(
                    f"Sheet '{name}': couldn't auto-detect a Name column. "
                    f"Pick one manually."
                )

        return InspectSpreadsheetResponse(
            sheets=sheet_names,
            preview_rows=preview_rows,
            detected_columns=detected_columns,
            auto_mapping=auto_mapping,
            target_fields=list(TARGET_FIELDS),
            warnings=warnings,
        )


@DATA_ROUTER.route("/import/spreadsheet/inspect", methods=["POST"])
@has_request_body(InspectSpreadsheetRequest)
def inspect_spreadsheet():
    # FU-341 / FU-198 — import inserts arbitrary stock rows across
    # the install. Same admin gate as backup restore.
    _, err = require_admin()
    if err is not None:
        return err
    _Request: InspectSpreadsheetRequest = get_request_body()
    _Result = get_container().inject(InspectSpreadsheetHandler).handle(_Request)
    if isinstance(_Result, str):
        if _Result.startswith("No staged upload"):
            return not_found("Upload", _Request.upload_id)
        return bad_request(_Result)
    # `field`s on the dataclass don't serialise via jsonify directly; convert.
    return ok({
        "sheets": _Result.sheets,
        "preview_rows": _Result.preview_rows,
        "detected_columns": _Result.detected_columns,
        "auto_mapping": _Result.auto_mapping,
        "target_fields": _Result.target_fields,
        "warnings": _Result.warnings,
    })


# ── Commit ─────────────────────────────────────────────────────────────

class ImportOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skip_duplicates: bool = True
    create_missing_locations: bool = False
    create_missing_groups: bool = False
    halt_on_error: bool = False


class CommitSpreadsheetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    upload_id: str
    filename: str = Field(min_length=1)
    sheet: str = Field(min_length=1)
    column_map: dict[str, str | None]
    options: ImportOptions = Field(default_factory=ImportOptions)


@dataclass(slots=True)
class RowReport:
    row_number: int
    status: str           # "created" | "skipped_duplicate" | "error"
    name: str
    reason: str | None = None


@dataclass(slots=True)
class CommitSpreadsheetResponse:
    summary: dict[str, int]
    rows: list[RowReport]


class CommitSpreadsheetHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CommitSpreadsheetRequest) -> CommitSpreadsheetResponse | str:
        path = staged_path(request.upload_id)
        if not path.exists():
            return f"No staged upload found for id {request.upload_id}."

        # ── Read spreadsheet ─────────────────────────────────────────
        try:
            sheets = _read_sheets(str(path), request.filename)
        except ValueError as exc:
            return str(exc)
        except Exception as exc:  # noqa: BLE001
            logging.getLogger(__name__).exception("Failed to read spreadsheet on commit.")
            return f"Could not read spreadsheet: {exc}"

        if request.sheet not in sheets:
            return f"Sheet '{request.sheet}' is not in the uploaded file."

        rows = sheets[request.sheet]
        if not rows:
            return f"Sheet '{request.sheet}' is empty."

        header = [str(h) if h is not None else "" for h in rows[0]]
        # name is mandatory; if the user mapped no Name column we can't
        # do anything useful — fail before touching the DB.
        if not request.column_map.get("name"):
            return "A column must be mapped to 'name' before importing."
        for col_name in request.column_map.values():
            if col_name is None:
                continue
            if col_name not in header:
                return f"Column '{col_name}' is not in sheet '{request.sheet}'."

        col_index: dict[str, int | None] = {
            target: (header.index(col) if col is not None and col in header else None)
            for target, col in request.column_map.items()
        }

        # ── Index existing entities for FK + duplicate resolution ────
        existing_items = self.repository.get(StockItem).all()
        existing_item_names = {
            (it.name or "").strip().lower(): it.id for it in existing_items
        }
        existing_groups = self.repository.get(StockGroup).all()
        existing_group_names: dict[str, Any] = {
            (g.name or "").strip().lower(): g.id for g in existing_groups
        }
        existing_locations = self.repository.get(StockLocation).all()
        existing_location_names: dict[str, Any] = {
            (loc.name or "").strip().lower(): loc.id for loc in existing_locations
        }
        existing_levels = self.repository.get(StockLevel).all()
        level_choices = sorted({lvl.name for lvl in existing_levels})

        # ── Iterate body rows ────────────────────────────────────────
        reports: list[RowReport] = []
        created = 0
        skipped = 0
        errors = 0

        try:
            for offset, row in enumerate(rows[1:], start=2):  # 1-based, header = row 1
                row_name_raw = (
                    row[col_index["name"]]
                    if col_index["name"] is not None and col_index["name"] < len(row)
                    else None
                )
                row_name = (str(row_name_raw).strip() if row_name_raw is not None else "")

                if not row_name:
                    # Don't error on entirely blank rows — common at end of
                    # CSV. Skip silently. But if any other mapped column has
                    # data, surface it as a real error.
                    if all(
                        (v is None or str(v).strip() == "")
                        for v in row
                    ):
                        continue
                    reports.append(RowReport(
                        row_number=offset, status="error",
                        name="", reason="Missing 'name' value.",
                    ))
                    errors += 1
                    if request.options.halt_on_error:
                        raise _HaltOnError()
                    continue

                # Duplicate check.
                if row_name.lower() in existing_item_names and request.options.skip_duplicates:
                    reports.append(RowReport(
                        row_number=offset, status="skipped_duplicate", name=row_name,
                    ))
                    skipped += 1
                    continue

                # Resolve foreign keys.
                try:
                    stock_level_id = self._resolve_level(
                        row, col_index["level"], existing_levels, level_choices,
                    )
                    stock_location_id = self._resolve_location(
                        row, col_index["location"],
                        existing_location_names, request.options.create_missing_locations,
                    )
                    stock_group_id = self._resolve_group(
                        row, col_index["group"],
                        existing_group_names, request.options.create_missing_groups,
                    )
                    expiry = (
                        _coerce_to_date(row[col_index["expiry"]])
                        if col_index["expiry"] is not None and col_index["expiry"] < len(row)
                        else None
                    )
                    is_flagged = (
                        _is_truthy(row[col_index["is_essential"]])
                        if col_index["is_essential"] is not None and col_index["is_essential"] < len(row)
                        else False
                    )
                except _RowError as exc:
                    reports.append(RowReport(
                        row_number=offset, status="error",
                        name=row_name, reason=exc.reason,
                    ))
                    errors += 1
                    if request.options.halt_on_error:
                        raise _HaltOnError()
                    continue

                # Insert via the StockItem table directly so we don't have
                # to fully hydrate StockLevel/Location/Group entities just
                # to call the repository. Mirrors N2's restore path.
                stock_item_table = db.metadata.tables["StockItem"]
                from uuid import uuid4
                db.session.execute(insert(stock_item_table).values(
                    id=uuid4(),
                    name=row_name,
                    notes=None,
                    image=None,
                    days_until_stocktake_alert=0,
                    stocktake_alerts_are_enabled=False,
                    stock_level_id=stock_level_id,
                    stock_location_id=stock_location_id,
                    stock_group_id=stock_group_id,
                    stock_level_last_updated=datetime.now(),
                    expiry_date=expiry,
                    is_flagged=is_flagged,
                    is_open=False,
                    auto_add_when_low=False,
                    opened_on=None,
                ))
                existing_item_names[row_name.lower()] = True  # mark for downstream dup checks
                reports.append(RowReport(
                    row_number=offset, status="created", name=row_name,
                ))
                created += 1

            db.session.commit()
        except _HaltOnError:
            db.session.rollback()
            return CommitSpreadsheetResponse(
                summary={"created": 0, "skipped": 0, "errors": errors, "halted": 1},
                rows=reports,
            )
        except Exception as exc:  # noqa: BLE001
            db.session.rollback()
            logging.getLogger(__name__).exception("Spreadsheet import failed; rolled back.")
            return f"Import failed and was rolled back: {exc}"

        # Successful commit — consume the staged file so the upload area
        # doesn't accumulate.
        try:
            path.unlink()
        except OSError:
            pass

        return CommitSpreadsheetResponse(
            summary={"created": created, "skipped": skipped, "errors": errors, "halted": 0},
            rows=reports,
        )

    @staticmethod
    def _resolve_level(
        row: list[Any], idx: int | None,
        existing_levels: list[StockLevel], choices: list[str],
    ) -> Any:
        # Pick a sensible default — the Sufficient-Stock level (resolved by
        # status identity, not name) is the middle-of-the-road option; users
        # can edit individual items post-import.
        sufficient = level_for_status(existing_levels, StockStatus.SUFFICIENT_STOCK)
        default = (
            sufficient.id if sufficient
            else (existing_levels[0].id if existing_levels else None)
        )
        if idx is None or idx >= len(row):
            return default
        raw = row[idx]
        if raw is None or str(raw).strip() == "":
            return default
        needle = str(raw).strip().lower()
        # Case-insensitive substring match; "low" matches "Low Stock", etc.
        matches = [lvl for lvl in existing_levels if needle in lvl.name.lower()]
        if len(matches) == 1:
            return matches[0].id
        if len(matches) > 1:
            # Prefer an exact (case-insensitive) match if one is in the set.
            exact = [lvl for lvl in matches if lvl.name.lower() == needle]
            if exact:
                return exact[0].id
            raise _RowError(
                f"Stock level '{raw}' is ambiguous; matches multiple of "
                f"{', '.join(lvl.name for lvl in matches)}."
            )
        raise _RowError(
            f"Stock level '{raw}' isn't recognised. Valid options: "
            f"{', '.join(choices)}."
        )

    @staticmethod
    def _resolve_location(
        row: list[Any], idx: int | None,
        existing: dict[str, Any], allow_create: bool,
    ) -> Any | None:
        if idx is None or idx >= len(row):
            return None
        raw = row[idx]
        if raw is None or str(raw).strip() == "":
            return None
        key = str(raw).strip().lower()
        if key in existing:
            return existing[key]
        if not allow_create:
            raise _RowError(
                f"Location '{raw}' doesn't exist. Tick 'Create missing locations' "
                f"to add it on the fly."
            )
        # Auto-create as a zone (the simplest level of the hierarchy).
        from uuid import uuid4
        loc_table = db.metadata.tables["StockLocation"]
        new_id = uuid4()
        db.session.execute(insert(loc_table).values(
            id=new_id,
            name=str(raw).strip(),
            kind="zone",
            parent_id=None,
            sequence=0,
        ))
        existing[key] = new_id
        return new_id

    @staticmethod
    def _resolve_group(
        row: list[Any], idx: int | None,
        existing: dict[str, Any], allow_create: bool,
    ) -> Any | None:
        if idx is None or idx >= len(row):
            return None
        raw = row[idx]
        if raw is None or str(raw).strip() == "":
            return None
        key = str(raw).strip().lower()
        if key in existing:
            return existing[key]
        if not allow_create:
            raise _RowError(
                f"Group '{raw}' doesn't exist. Tick 'Create missing groups' "
                f"to add it on the fly."
            )
        from uuid import uuid4
        group_table = db.metadata.tables["StockGroup"]
        new_id = uuid4()
        db.session.execute(insert(group_table).values(
            id=new_id, name=str(raw).strip(),
        ))
        existing[key] = new_id
        return new_id


class _RowError(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class _HaltOnError(Exception):
    pass


@DATA_ROUTER.route("/import/spreadsheet/commit", methods=["POST"])
@has_request_body(CommitSpreadsheetRequest)
def commit_spreadsheet():
    _, err = require_admin()
    if err is not None:
        return err
    _Request: CommitSpreadsheetRequest = get_request_body()
    _Result = get_container().inject(CommitSpreadsheetHandler).handle(_Request)
    if isinstance(_Result, str):
        if _Result.startswith("No staged upload"):
            return not_found("Upload", _Request.upload_id)
        if _Result.startswith("Import failed and was rolled back"):
            return internal_server_error(_Result)
        return bad_request(_Result)
    return ok({
        "summary": _Result.summary,
        "rows": [
            {
                "row_number": r.row_number,
                "status": r.status,
                "name": r.name,
                "reason": r.reason,
            }
            for r in _Result.rows
        ],
    })


# ── Templates (FU-343) ─────────────────────────────────────────────────
#
# Downloadable per-section CSV templates so users don't have to guess the
# schema. Headers come straight from `TARGET_FIELDS` above (the same
# source of truth the auto-mapping + commit paths read) so a template
# can never drift from what the importer accepts. CSV-only for now;
# `.xlsx` with dropdown validation is a deferred follow-on (see FU-343
# discussion — ship CSV first, revisit if users ask).
#
# Only stock_items is a real "section" today. The endpoint is scoped as
# a section index so the frontend affordance stays the same shape when
# more sections land later (recipes, shopping lists, etc.).


@dataclass(slots=True)
class ImportTemplate:
    section: str
    label: str
    caption: str
    headers: tuple[str, ...]
    # One-line example row shown as the second line of the CSV so users
    # see the expected shape at a glance. Optional cells may be blank.
    example: tuple[str, ...]


IMPORT_TEMPLATES: tuple[ImportTemplate, ...] = (
    ImportTemplate(
        section="stock_items",
        label="Stock items",
        caption="One row per pantry item. Only `name` is required; the rest are optional.",
        headers=TARGET_FIELDS,
        # Example values are illustrative — the level / location / group
        # matchers are name-based, so any string that resembles an existing
        # entity is a valid starting point for a real import.
        example=("Rice", "In stock", "Pantry", "Grains", "2027-01-01", "no"),
    ),
)

IMPORT_TEMPLATES_BY_SECTION: dict[str, ImportTemplate] = {t.section: t for t in IMPORT_TEMPLATES}


@DATA_ROUTER.route("/import/templates", methods=["GET"])
def list_import_templates():
    # Same admin gate as the rest of import (see FU-341 / FU-198): only
    # admins can invoke the importer, so only admins need the template
    # index. Non-admins hitting this get a plain 403 rather than an
    # index that hints at endpoints they can't use.
    _, err = require_admin()
    if err is not None:
        return err
    return ok({
        "sections": [
            {
                "section": t.section,
                "label": t.label,
                "caption": t.caption,
                "headers": list(t.headers),
            }
            for t in IMPORT_TEMPLATES
        ],
    })


@DATA_ROUTER.route("/import/templates/<section>.csv", methods=["GET"])
def download_import_template(section: str):
    _, err = require_admin()
    if err is not None:
        return err
    template = IMPORT_TEMPLATES_BY_SECTION.get(section)
    if template is None:
        return not_found("Import template", section)

    # Build the CSV in memory — headers row + one example row so the shape
    # is obvious. StringIO + csv.writer keeps escaping honest for names
    # containing commas / quotes even in the illustrative row.
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(template.headers)
    writer.writerow(template.example)
    body = buf.getvalue().encode("utf-8")

    from flask import Response
    response = Response(body, mimetype="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = (
        f'attachment; filename="dora-import-{template.section}.csv"'
    )
    return response
