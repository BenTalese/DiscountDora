"""FU-334 — read/write helpers for shopping-list receipt attachments.

A shopping list (status='shopping' or 'done') owns 0..N
`ShoppingListAttachment` rows ordered by `sequence`. Each row stores
the same `data:image/...;base64,...` UTF-8 bytes shape as Recipe.image /
RecipeStepImage (client picks → `processImageFile` → data URL; server
stores encoded bytes; bytes endpoint decodes + serves raw).

Unlike step images, receipts are mutated **one at a time** (tap to add,
tap trash to delete) — there is no wholesale replace. So this module
exposes individual `add` / `delete` helpers rather than the recipe's
`replace_step_images_for_recipe`.

Pure record-keeping — no OCR, no parsing, no auto-matching to lines.
"""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import func, select

from dora_api.app import db


# Soft cap. Receipts can legitimately span several photos (long till
# rolls, two-store shops), but anything beyond this is almost certainly
# accidental. Mirrored on the client.
MAX_ATTACHMENTS_PER_LIST = 20

# Hard guard on encoded size. processImageFile caps at ~1600px JPEG q0.85
# which lands well under 1MB encoded; this is defence-in-depth against a
# runaway client payload. The data-URL prefix adds ~30 bytes of overhead.
MAX_ATTACHMENT_BYTES = 3 * 1024 * 1024


def _attachment_table():
    return db.metadata.tables["ShoppingListAttachment"]


def get_attachment_metadata_for_list(shopping_list_id: UUID) -> list[dict]:
    """Return ordered {id, sequence} dicts for the detail DTO. Bytes are
    never inlined — the SPA loads each image via the dedicated bytes
    endpoint so detail JSON stays slim."""
    table = _attachment_table()
    rows = db.session.execute(
        select(table.c.id, table.c.sequence)
        .where(table.c.shopping_list_id == shopping_list_id)
        .order_by(table.c.sequence)
    ).all()
    return [{"id": row[0], "sequence": row[1]} for row in rows]


def get_attachment_bytes(
    shopping_list_id: UUID, attachment_id: UUID
) -> bytes | None:
    """Load the encoded data-URL bytes for a single attachment. Returns
    None when the attachment isn't on this list (or doesn't exist)."""
    table = _attachment_table()
    row = db.session.execute(
        select(table.c.image)
        .where(table.c.id == attachment_id)
        .where(table.c.shopping_list_id == shopping_list_id)
    ).first()
    return row[0] if row else None


def count_attachments_for_list(shopping_list_id: UUID) -> int:
    table = _attachment_table()
    return db.session.execute(
        select(func.count(table.c.id))
        .where(table.c.shopping_list_id == shopping_list_id)
    ).scalar() or 0


def _next_sequence(shopping_list_id: UUID) -> int:
    table = _attachment_table()
    current_max = db.session.execute(
        select(func.max(table.c.sequence))
        .where(table.c.shopping_list_id == shopping_list_id)
    ).scalar()
    return (current_max + 1) if current_max is not None else 0


def _validate_data_url(image_data_url: str) -> None:
    if not (image_data_url or "").startswith("data:image/"):
        raise ValueError(
            "Attachment must be a 'data:image/<type>;base64,...' data URL."
        )
    if len(image_data_url) > MAX_ATTACHMENT_BYTES:
        raise ValueError(
            f"Attachment is too large (max {MAX_ATTACHMENT_BYTES // (1024 * 1024)}MB encoded)."
        )


def add_attachment(shopping_list_id: UUID, image_data_url: str) -> UUID:
    """Append a new attachment, returning its id. Raises ValueError on a
    malformed data URL, oversize payload, or when the list is already at
    MAX_ATTACHMENTS_PER_LIST. The lifecycle gate (draft lists rejected)
    lives in the handler — this helper only enforces shape + cap."""
    _validate_data_url(image_data_url)
    if count_attachments_for_list(shopping_list_id) >= MAX_ATTACHMENTS_PER_LIST:
        raise ValueError(
            f"Too many attachments (cap is {MAX_ATTACHMENTS_PER_LIST} per list)."
        )

    table = _attachment_table()
    attachment_id = uuid4()
    db.session.execute(table.insert(), [{
        "id": attachment_id,
        "shopping_list_id": shopping_list_id,
        "sequence": _next_sequence(shopping_list_id),
        "image": image_data_url.encode("utf-8"),
        "created_at": datetime.now(timezone.utc),
    }])
    return attachment_id


def delete_attachment(shopping_list_id: UUID, attachment_id: UUID) -> bool:
    """Delete a single attachment. Returns True when a row was removed,
    False when the id wasn't found on this list."""
    table = _attachment_table()
    result = db.session.execute(
        table.delete()
        .where(table.c.id == attachment_id)
        .where(table.c.shopping_list_id == shopping_list_id)
    )
    return result.rowcount > 0
