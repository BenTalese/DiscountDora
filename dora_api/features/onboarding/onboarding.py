"""F1 — first-run wizard backend.

Three endpoints power the /welcome wizard:

  GET  /api/onboarding/state    — snapshot of what the user has + has done
  POST /api/onboarding/complete — stamp onboarding_completed_at = NOW()
  POST /api/onboarding/seed     — import bundled default groups / locations
  POST /api/onboarding/restart  — clear the completion timestamp

Seed catalogues live as JSON next to this file so designers can edit
without touching Python. They're idempotent: a second seed call won't
duplicate groups/locations that already exist by name (we match on the
visible label rather than ids — the user is supposed to be able to
re-import without thinking about the bookkeeping).
"""
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from flask import session
from pydantic import BaseModel, ConfigDict

from dora_api.domain.entities.merchant import Merchant
from dora_api.domain.entities.stock_group import StockGroup
from dora_api.domain.entities.stock_item import StockItem
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.domain.entities.user import User
from dora_api.features.auth.register_user import SESSION_USER_ID_KEY
from dora_api.features.routers import ONBOARDING_ROUTER
from dora_api.infrastructure.api_response import (no_content, not_found, ok,
                                                  unauthorized)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


_LOGGER = logging.getLogger(__name__)
_SEED_DIR = Path(__file__).parent


def _load_seed(name: str) -> list[dict[str, Any]]:
    """Read a bundled seed JSON. Defensive — bad JSON shouldn't 500 the wizard."""
    try:
        with open(_SEED_DIR / name, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, list) else []
    except FileNotFoundError:
        _LOGGER.warning("Seed file missing: %s", name)
        return []
    except json.JSONDecodeError as exc:
        _LOGGER.error("Seed file invalid JSON (%s): %s", name, exc)
        return []


def _current_user_id() -> UUID | None:
    raw = session.get(SESSION_USER_ID_KEY)
    if not raw:
        return None
    try:
        return UUID(str(raw))
    except (TypeError, ValueError):
        return None


# ─── State ───────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class MerchantStatusDto:
    total: int
    enabled: int


@dataclass(frozen=True, slots=True)
class OnboardingStateDto:
    completed: bool
    completed_at: datetime | None
    first_user: bool
    has_locations: bool
    has_groups: bool
    has_stock_items: bool
    merchant_status: MerchantStatusDto


class GetOnboardingStateHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, user: User) -> OnboardingStateDto:
        total_users = self.repository.get(User).count()
        groups_count = self.repository.get(StockGroup).count()
        locations_count = self.repository.get(StockLocation).count()
        items_count = self.repository.get(StockItem).count()
        merchant_total = self.repository.get(Merchant).count()
        # `is_enabled` lives on Merchant; not all installs have any merchants
        # configured (it's an opt-in scrape target). We just surface counts.
        merchants = self.repository.get(Merchant).all()
        enabled_count = sum(
            1 for m in merchants if getattr(m, "is_enabled", False)
        )
        return OnboardingStateDto(
            completed = user.onboarding_completed_at is not None,
            completed_at = user.onboarding_completed_at,
            first_user = total_users <= 1,
            has_locations = locations_count > 0,
            has_groups = groups_count > 0,
            has_stock_items = items_count > 0,
            merchant_status = MerchantStatusDto(
                total = merchant_total,
                enabled = enabled_count,
            ),
        )


@ONBOARDING_ROUTER.route("/state", methods=["GET"])
def get_onboarding_state():
    user_id = _current_user_id()
    if user_id is None:
        return unauthorized("Sign in to use the onboarding endpoints.")
    repo = SqlAlchemyRepository()
    user = repo.get(User).by_id(user_id)
    if user is None:
        return not_found("User", user_id)
    state = get_container().inject(GetOnboardingStateHandler).handle(user)
    return ok(state)


# ─── Complete + restart ──────────────────────────────────────────────


@ONBOARDING_ROUTER.route("/complete", methods=["POST"])
def complete_onboarding():
    user_id = _current_user_id()
    if user_id is None:
        return unauthorized("Sign in to use the onboarding endpoints.")
    repo = SqlAlchemyRepository()
    user = repo.get(User).by_id(user_id)
    if user is None:
        return not_found("User", user_id)
    user.onboarding_completed_at = datetime.now(timezone.utc)
    repo.save_changes()
    _LOGGER.info("Onboarding completed for user %s", user_id)
    return no_content()


@ONBOARDING_ROUTER.route("/restart", methods=["POST"])
def restart_onboarding():
    user_id = _current_user_id()
    if user_id is None:
        return unauthorized("Sign in to use the onboarding endpoints.")
    repo = SqlAlchemyRepository()
    user = repo.get(User).by_id(user_id)
    if user is None:
        return not_found("User", user_id)
    user.onboarding_completed_at = None
    repo.save_changes()
    _LOGGER.info("Onboarding reset requested by user %s", user_id)
    return no_content()


# ─── Seed catalogues ─────────────────────────────────────────────────


class SeedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    groups: bool = False
    locations: bool = False


@dataclass(frozen=True, slots=True)
class SeedResultDto:
    groups_created: int
    groups_skipped: int
    locations_created: int
    locations_skipped: int


class SeedHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: SeedRequest) -> SeedResultDto:
        groups_created = groups_skipped = 0
        locations_created = locations_skipped = 0

        if request.groups:
            seed_groups = _load_seed("default_stock_groups.json")
            existing = {
                g.name.strip().lower()
                for g in self.repository.get(StockGroup).all()
            }
            for entry in seed_groups:
                name = (entry.get("name") or "").strip()
                if not name:
                    continue
                if name.lower() in existing:
                    groups_skipped += 1
                    continue
                self.repository.add(StockGroup(name=name))
                existing.add(name.lower())
                groups_created += 1
            self.repository.save_changes()

        if request.locations:
            seed_locations = _load_seed("default_locations.json")
            # Match the dedupe semantics of groups: skip locations whose
            # (parent_id, name) pair already exists. Top-level zones are
            # keyed by name alone.
            existing_pairs: set[tuple[str | None, str]] = set()
            for loc in self.repository.get(StockLocation).all():
                key_parent = str(loc.parent_id) if loc.parent_id else None
                existing_pairs.add((key_parent, loc.name.strip().lower()))

            for zone in seed_locations:
                z_name = (zone.get("name") or "").strip()
                z_kind = zone.get("kind") or "zone"
                if not z_name:
                    continue
                key = (None, z_name.lower())
                if key in existing_pairs:
                    locations_skipped += 1
                    zone_entity = self._find_existing(z_name, None)
                else:
                    zone_entity = StockLocation(
                        name=z_name, kind=z_kind, parent_id=None, sequence=0
                    )
                    self.repository.add(zone_entity)
                    self.repository.save_changes()
                    existing_pairs.add(key)
                    locations_created += 1

                for idx, child in enumerate(zone.get("children") or []):
                    c_name = (child.get("name") or "").strip()
                    c_kind = child.get("kind") or "area"
                    if not c_name or zone_entity is None:
                        continue
                    pair = (str(zone_entity.id), c_name.lower())
                    if pair in existing_pairs:
                        locations_skipped += 1
                        continue
                    self.repository.add(StockLocation(
                        name=c_name,
                        kind=c_kind,
                        parent_id=zone_entity.id,
                        sequence=idx,
                    ))
                    existing_pairs.add(pair)
                    locations_created += 1
            self.repository.save_changes()

        return SeedResultDto(
            groups_created=groups_created,
            groups_skipped=groups_skipped,
            locations_created=locations_created,
            locations_skipped=locations_skipped,
        )

    def _find_existing(self, name: str, parent_id: UUID | None) -> StockLocation | None:
        # Inline lookup so the upsert path can grab the existing zone to
        # parent children off — saves another all() round-trip.
        for loc in self.repository.get(StockLocation).all():
            if loc.name.strip().lower() != name.lower():
                continue
            same_parent = (loc.parent_id is None and parent_id is None) or (
                loc.parent_id is not None
                and parent_id is not None
                and loc.parent_id == parent_id
            )
            if same_parent:
                return loc
        return None


@ONBOARDING_ROUTER.route("/seed", methods=["POST"])
@has_request_body(SeedRequest)
def seed_onboarding():
    user_id = _current_user_id()
    if user_id is None:
        return unauthorized("Sign in to use the onboarding endpoints.")
    request: SeedRequest = get_request_body()
    if not request.groups and not request.locations:
        # Nothing requested — return zero-counts rather than 400 so the
        # frontend can call this unconditionally as "advance step 3".
        return ok(SeedResultDto(0, 0, 0, 0))
    result = get_container().inject(SeedHandler).handle(request)
    _LOGGER.info(
        "Onboarding seed (user %s): groups +%d/-%d, locations +%d/-%d",
        user_id,
        result.groups_created, result.groups_skipped,
        result.locations_created, result.locations_skipped,
    )
    return ok(result)
