"""FU-334 — add / delete / serve-bytes for shopping-list receipt attachments.

Three endpoints, all under `/api/shopping-lists/<list_id>/attachments`:

  POST   /                   → add a new attachment from a data URL
  DELETE /<attachment_id>    → remove a single attachment
  GET    /<attachment_id>    → bytes endpoint (raw image with Content-Type)

The bytes endpoint mirrors `/recipes/<id>/step-images/<image_id>` exactly:
fetch encoded bytes → regex-parse data URL → base64 decode → raw response.

The lifecycle gate is enforced here (no attaching to a `draft` list); the
access helper enforces shape + cap. Unlike step images, receipts are
add/delete one at a time — there is no wholesale replace.
"""
import base64
import logging
import re as _re
from dataclasses import dataclass
from uuid import UUID

from flask import Response
from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.shopping_list import (
    SHOPPING_LIST_STATUS_DRAFT, ShoppingList)
from dora_api.features.routers import SHOPPING_LIST_ROUTER
from dora_api.features.shopping_lists.shopping_list_attachment_access import (
    MAX_ATTACHMENT_BYTES, add_attachment, delete_attachment,
    get_attachment_bytes)
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  no_content, not_found, ok)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


_DATA_URL_RE = _re.compile(
    r"^data:(?P<mime>[\w/+.-]+);base64,(?P<data>.+)$", _re.DOTALL
)


# ───── Add ────────────────────────────────────────────────────────────────

class AddShoppingListAttachmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # `data:image/<type>;base64,...` string. The client (processImageFile)
    # already validated MIME + resized + re-encoded; the server validates
    # shape + size as defence-in-depth.
    image_data_url: str = Field(min_length=1, max_length=MAX_ATTACHMENT_BYTES)


@dataclass(slots=True)
class AddShoppingListAttachmentResponse:
    not_found: bool = False
    draft_rejected: bool = False
    invalid_payload: str | None = None
    attachment_id: UUID | None = None


class AddShoppingListAttachmentHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(
        self,
        request: AddShoppingListAttachmentRequest,
        shopping_list_id: UUID,
    ) -> AddShoppingListAttachmentResponse:
        lst: ShoppingList | None = self.repository.get(ShoppingList).by_id(
            shopping_list_id
        )
        if lst is None:
            return AddShoppingListAttachmentResponse(not_found=True)
        if lst.status == SHOPPING_LIST_STATUS_DRAFT:
            return AddShoppingListAttachmentResponse(draft_rejected=True)

        try:
            attachment_id = add_attachment(
                shopping_list_id, request.image_data_url
            )
        except ValueError as exc:
            return AddShoppingListAttachmentResponse(invalid_payload=str(exc))

        self.repository.save_changes()
        return AddShoppingListAttachmentResponse(attachment_id=attachment_id)


@SHOPPING_LIST_ROUTER.route(
    "/<shopping_list_id>/attachments", methods=["POST"]
)
@has_request_body(AddShoppingListAttachmentRequest)
def add_shopping_list_attachment(shopping_list_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Request: AddShoppingListAttachmentRequest = get_request_body()
    _Response = get_container().inject(
        AddShoppingListAttachmentHandler
    ).handle(_Request, shopping_list_id)
    if _Response.not_found:
        return not_found("ShoppingList", shopping_list_id)
    if _Response.draft_rejected:
        return business_rule_violation(
            "Receipts can only be attached to a list that's being shopped or "
            "finished. Start shopping the list first."
        )
    if _Response.invalid_payload:
        return business_rule_violation(_Response.invalid_payload)
    _Logger.info(
        "Added attachment %s to shopping list %s",
        _Response.attachment_id, shopping_list_id,
    )
    return ok({"attachment_id": _Response.attachment_id})


# ───── Delete ─────────────────────────────────────────────────────────────

@dataclass(slots=True)
class DeleteShoppingListAttachmentResponse:
    not_found: bool = False


class DeleteShoppingListAttachmentHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(
        self, shopping_list_id: UUID, attachment_id: UUID,
    ) -> DeleteShoppingListAttachmentResponse:
        lst: ShoppingList | None = self.repository.get(ShoppingList).by_id(
            shopping_list_id
        )
        if lst is None:
            return DeleteShoppingListAttachmentResponse(not_found=True)
        removed = delete_attachment(shopping_list_id, attachment_id)
        if not removed:
            return DeleteShoppingListAttachmentResponse(not_found=True)
        self.repository.save_changes()
        return DeleteShoppingListAttachmentResponse()


@SHOPPING_LIST_ROUTER.route(
    "/<shopping_list_id>/attachments/<attachment_id>", methods=["DELETE"]
)
def delete_shopping_list_attachment(
    shopping_list_id: UUID, attachment_id: UUID,
):
    _Logger = logging.getLogger(__name__)
    _Response = get_container().inject(
        DeleteShoppingListAttachmentHandler
    ).handle(UUID(str(shopping_list_id)), UUID(str(attachment_id)))
    if _Response.not_found:
        return not_found("ShoppingListAttachment", attachment_id)
    _Logger.info(
        "Deleted attachment %s from shopping list %s",
        attachment_id, shopping_list_id,
    )
    return no_content()


# ───── Bytes ──────────────────────────────────────────────────────────────

@SHOPPING_LIST_ROUTER.route(
    "/<shopping_list_id>/attachments/<attachment_id>", methods=["GET"]
)
def get_shopping_list_attachment_bytes(
    shopping_list_id, attachment_id,
):
    raw_bytes = get_attachment_bytes(
        UUID(str(shopping_list_id)), UUID(str(attachment_id))
    )
    if not raw_bytes:
        return not_found("ShoppingListAttachment", attachment_id)
    data_url = raw_bytes.decode("utf-8", "ignore")
    match = _DATA_URL_RE.match(data_url)
    if not match:
        return not_found("ShoppingListAttachment", attachment_id)
    try:
        raw = base64.b64decode(match.group("data"), validate=False)
    except (ValueError, TypeError):
        return not_found("ShoppingListAttachment", attachment_id)
    return Response(
        raw,
        mimetype=match.group("mime"),
        headers={"Cache-Control": "no-cache"},
    )
