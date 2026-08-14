"""Nutrition complex-mode endpoints — source status + dataset import.

    GET  /api/nutrition/sources          — what can answer a lookup right now
    POST /api/nutrition/datasets/import  — start a bulk import (admin)

Status is deliberately a *read of reality* rather than a stored flag: a
dataset is "available" iff it holds rows. The transient import phase is
in-memory (the import runs on a daemon thread), so a server restart mid-import
reports `idle` with whatever rows had been committed — honest, and recoverable
by starting again.
"""
import logging

from flask import request

from dora_api.features.app_settings.access import get_or_create_app_setting
from dora_api.features.nutrition.lookup import resolve_food, search_foods
from dora_api.features.nutrition.dataset_import import (
    dataset_label, default_url, start_import, state_for,
)
from dora_api.features.nutrition.sources import nutrition_mode, source_statuses
from dora_api.features.routers import NUTRITION_ROUTER
from dora_api.features.users.update_user_as_admin import _require_admin
from dora_api.infrastructure.api_response import bad_request, ok
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository
from dora_api.domain.entities.nutrition_food import (
    NUTRITION_DATASET_SOURCES, NUTRITION_SOURCE_LABELS,
)

_LOG = logging.getLogger(__name__)


def _source_payload():
    repository = SqlAlchemyRepository()
    setting = get_or_create_app_setting(repository)
    statuses = source_statuses(repository, setting)

    sources = []
    for status in statuses:
        entry = {
            "id": status.id,
            "label": status.label,
            "kind": status.kind,
            "available": status.available,
            "food_count": status.food_count,
        }
        if status.kind == "dataset":
            state = state_for(status.id)
            entry.update({
                "phase": state.phase,
                "error": state.error,
                "default_url": default_url(status.id),
            })
        sources.append(entry)

    return {
        "mode": nutrition_mode(setting),
        "sources": sources,
        # Any source at all can answer — the page uses this to explain a
        # `complex` mode that has nothing behind it yet.
        "any_available": any(s.available for s in statuses),
    }


@NUTRITION_ROUTER.route("/sources", methods=["GET"])
def get_nutrition_sources():
    return ok(_source_payload())


@NUTRITION_ROUTER.route("/lookup", methods=["GET"])
def lookup_foods():
    """Unified search across every enabled source. Not admin-gated — any
    member linking a stock item needs it."""
    _Query = (request.args.get("q") or "").strip()
    _Repository = SqlAlchemyRepository()
    _Setting = get_or_create_app_setting(_Repository)
    return ok(search_foods(_Repository, _Setting, _Query))


@NUTRITION_ROUTER.route("/foods/resolve", methods=["POST"])
def resolve_food_endpoint():
    """Persist a picked live suggestion and return the saved food.

    Takes only (source, source_ref) — the values are re-fetched server-side
    rather than trusted from the request, so this can't be used to write
    arbitrary nutrition numbers into the catalogue.
    """
    _Body = get_request_body() or {}
    _Source = (_Body.get("source") or "").strip()
    _Ref = (_Body.get("source_ref") or "").strip()
    if not _Source or not _Ref:
        return bad_request("Both 'source' and 'source_ref' are required.")

    _Repository = SqlAlchemyRepository()
    _Setting = get_or_create_app_setting(_Repository)
    _Food = resolve_food(_Repository, _Setting, _Source, _Ref)
    if _Food is None:
        return bad_request(
            "That food couldn't be fetched from its source — it may have been "
            "removed, or the source may be switched off."
        )
    return ok({
        "id": str(_Food.id),
        "source": _Food.source,
        "source_label": NUTRITION_SOURCE_LABELS.get(_Food.source, _Food.source),
        "source_ref": _Food.source_ref,
        "name": _Food.name,
        "brand": _Food.brand,
        "barcode": _Food.barcode,
        "kcal_per_100g": _Food.kcal_per_100g,
        "protein_g_per_100g": _Food.protein_g_per_100g,
        "carbs_g_per_100g": _Food.carbs_g_per_100g,
        "fat_g_per_100g": _Food.fat_g_per_100g,
    })


@NUTRITION_ROUTER.route("/datasets/import", methods=["POST"])
def start_dataset_import():
    _, _Error = _require_admin()
    if _Error is not None:
        return _Error

    _Body = get_request_body() or {}
    _Source = (_Body.get("source") or "").strip()
    if _Source not in NUTRITION_DATASET_SOURCES:
        return bad_request(f"Unknown nutrition dataset '{_Source}'.")

    # Optional override so a superseded USDA release URL (or a local mirror on
    # an air-gapped install) doesn't turn the button into a dead end. See the
    # release-date note in dataset_import.py.
    _Url = (_Body.get("url") or "").strip() or None

    _LOG.info("Starting nutrition dataset import: %s", dataset_label(_Source))
    start_import(_Source, _Url)
    return ok(_source_payload())
