"""Accessor for the single AppSetting row.

Used by the get/update endpoints (admin UI) and read server-side by the
assistant. Get-or-create means the install works before anyone visits Settings.
"""
from flask import g, has_app_context

from dora_api.domain.entities.app_setting import (
    RATING_SCHEME_NONE,
    AppSetting,
)
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository

# FU-560 — key under which the singleton is memoised on the Flask
# application-context `g` (see get_or_create_app_setting).
_G_SINGLETON_ATTR = "_dora_app_setting_singleton"


def get_or_create_app_setting(repository: SqlAlchemyRepository) -> AppSetting:
    """Return the one AppSetting row, creating it on first access.

    FU-560 — memoised on the Flask application-context ``g`` so a request (or a
    background job) issues **at most one** ``SELECT`` for this single-row table.
    It's read many times per request — feature gating on ``/health``, the
    clock/timezone helper, money/locale, stocktake cadence, the assistant — and
    profiling under load (FU-388) showed the same one-row query firing 3-4× on
    endpoints like ``/alerts`` and ``/health``.

    Safe **without** explicit invalidation because:
      * the cached value is the SQLAlchemy identity-map instance every other
        query in the same session would return, so the only way settings change
        — an in-place mutation + commit in ``update_app_settings`` — flows
        through the cached object (attributes reload after the commit-expire);
      * the singleton row is never deleted or replaced within a live request:
        the only ``drop_all`` callers are boot and the demo-reset job (each in
        its own short-lived app context), and restore is additive (it skips the
        existing row);
      * ``g`` shares the app-context lifetime with the scoped DB session, so a
        new context always starts with a fresh cache — no cross-request
        staleness.
    Falls straight through to the DB when there's no app context (imports,
    one-off scripts).
    """
    if has_app_context():
        cached = getattr(g, _G_SINGLETON_ATTR, None)
        if cached is not None:
            return cached

    setting = _get_or_create(repository)

    if has_app_context():
        setattr(g, _G_SINGLETON_ATTR, setting)
    return setting


def money_features_enabled(repository: SqlAlchemyRepository) -> bool:
    """True when this install has money features switched on.

    Money is a single install-wide concern (`AppSetting.money_enabled`); there
    is no per-user layer. Server-side gates read it through here so a feature
    that is *about* money can refuse outright rather than answer with dollar
    prose an install has opted out of. Goes through the memoised singleton
    accessor, so gating costs no extra query.
    """
    return bool(get_or_create_app_setting(repository).money_enabled)


def _get_or_create(repository: SqlAlchemyRepository) -> AppSetting:
    existing = repository.get(AppSetting).all()
    if existing:
        return existing[0]
    # LLM URL/model/enabled config is entirely per-user (on the User row) —
    # there is no install-wide AI switch. A fresh install lets each account
    # opt in to AI mode individually on Settings → Assistant.
    setting = AppSetting(
        scanning_enabled=False,
        nutrition_rating_scheme=RATING_SCHEME_NONE,
        # PROPOSAL_STOCKTAKE_MODE §8 — fresh installs get Fortnightly +
        # Auto-on so the queue "just works" without a Settings visit.
        stocktake_default_cadence_band="fortnightly",
        stocktake_auto_tuning_enabled=True,
        # 2026-08-20 — stocktake is on for a fresh install, and new items join
        # the rotation by default.
        stocktake_enabled=True,
        stocktake_new_items_opt_in=True,
    )
    repository.add(setting)
    repository.save_changes()
    return setting
