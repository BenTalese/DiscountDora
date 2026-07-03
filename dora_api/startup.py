import logging
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# Load repo-root .env before any dora_api import — configuration_manager reads
# os.environ at import time. Real shell/Docker env vars still win (override=False).
load_dotenv(find_dotenv(), override=False)

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask_cors import CORS
from flask_migrate import upgrade
from werkzeug.exceptions import HTTPException

from dora_api.app import app, db
from dora_api.infrastructure.api_response import internal_server_error
from dora_api.infrastructure.audit_retention import prune_audit_events
from dora_api.infrastructure.configuration_manager import DORA_CONFIG
from dora_api.infrastructure.logging_setup import configure_logging
from dora_api.infrastructure.middleware import MIDDLEWARE
from dora_api.infrastructure.service_wiring import build_dependency_container
from dora_api.infrastructure.utils import get_attributes_ending_with
from dora_api.persistence.seed import seed_dev_data


def startup(is_test_env: bool = False):
    # D3: refuse to boot in production when required env vars are
    # missing. No-op in dev/test. Runs before *anything* else so the
    # friendly error fires before we read appsettings, build the DI
    # container, etc.
    from dora_api.infrastructure.profile import \
        validate_production_requirements
    validate_production_requirements()

    _Container = build_dependency_container()
    app.container = _Container  # type: ignore

    # D3: profile-aware CORS pinning. Dev = open localhost list, prod
    # = whatever DORA_CORS_ORIGINS contains (validated to be non-empty
    # by validate_production_requirements() above).
    # supports_credentials must be True for the browser to send the
    # `dora_session` cookie cross-origin. Origins must be an explicit
    # list (never '*') when credentials are enabled — the browser
    # refuses the wildcard in that case.
    CORS(
        app,
        resources={r'/api/*': {
            'origins': DORA_CONFIG.get_cors_origins(),
            'allow_headers': ['Content-Type', 'X-Request-Id', 'X-CSRF-Token'],
            'supports_credentials': True,
        }},
    )

    # D2: legacy-path migrations run *before* init_db so a relocated
    # DB file is in its new home by the time SQLAlchemy opens it.
    # FU-045: the legacy-DB migration is a SQLite-only file move; skip it
    # when running on Postgres (no file to relocate).
    from dora_api.infrastructure.path_migration import (
        migrate_legacy_db, migrate_legacy_uploads,
    )
    _db_url = DORA_CONFIG.get_db_connection_string()
    if _db_url.startswith("sqlite:///"):
        migrate_legacy_db(Path(_db_url.removeprefix("sqlite:///")))
    migrate_legacy_uploads(DORA_CONFIG.get_uploads_dir())

    init_db(is_test_env)
    configure_logging(
        "dapi",
        DORA_CONFIG.get_log_dir(),
        debug=DORA_CONFIG.is_debug_mode_enabled(),
    )
    register_routers()

    if not is_test_env:
        # Nightly audit-log retention sweep. Hour 3 local time keeps it
        # well clear of any deals-email schedule. Tests skip the
        # scheduler entirely — they don't run long enough to trip it,
        # and we don't want a background thread surviving the test
        # session.
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            prune_audit_events,
            CronTrigger(hour=3, minute=0),
            id="audit_retention",
            replace_existing=True,
        )
        # C-9.7 — alerts email digest. Runs once daily at 07:00; the job
        # gates per-user cadence + weekly-day internally (PROPOSAL_ALERTS
        # §3.5). 07:00 sits comfortably between the 03:00 audit sweep and
        # the typical workday so a "morning digest" lands before the user
        # opens the app.
        from dora_api.features.alerts.send_alerts_digest import \
            send_alerts_digest
        scheduler.add_job(
            send_alerts_digest,
            CronTrigger(hour=7, minute=0),
            id="alerts_digest",
            replace_existing=True,
        )
        # C-9.8 — alerts web-push. Hourly at :30 so it staggers from the
        # email digest's 07:00 fire. The job self-gates when VAPID isn't
        # configured (returns 0 without mutating the ledger) so an
        # unconfigured install spends nothing.
        from dora_api.features.alerts.send_alerts_push import \
            send_alerts_push
        scheduler.add_job(
            send_alerts_push,
            CronTrigger(minute=30),
            id="alerts_push",
            replace_existing=True,
        )
        scheduler.start()

    if not is_test_env:  # app.run blocks the thread where tests are ran from
        app.run(
            DORA_CONFIG.get_api_host(),
            DORA_CONFIG.get_api_port(),
            DORA_CONFIG.is_debug_mode_enabled(),
            use_reloader = DORA_CONFIG.is_reloader_enabled()
        )


def init_db(is_test_env: bool):
    with app.app_context():
        # D3: is_seed_allowed() refuses in production regardless of
        # DORA_ALLOW_DESTRUCTIVE, so a misconfigured prod deploy can't
        # accidentally wipe its own database on boot.
        if is_test_env or (DORA_CONFIG.is_debug_mode_enabled() and DORA_CONFIG.is_seed_allowed()):
            db.drop_all()
            db.create_all()
            seed_dev_data()
            return

        if DORA_CONFIG.is_debug_mode_enabled():
            # Create any missing tables for local dev, but never drop existing data.
            # Set DORA_ALLOW_DESTRUCTIVE=true to wipe and re-seed (dev only).
            db.create_all()
            return

        upgrade()


def register_routers():
    # Lazy meal-plan reconciliation. Any read against recipes or meal
    # plans triggers the past-day consumption sweep first, so the pool
    # counts displayed to the user are always current. Idempotent via
    # conditional UPDATE in the helper. Must be attached *before*
    # register_blueprint — Flask freezes blueprint setup at registration.
    from dora_api.features.meal_plans.reconcile_consumed_meals import \
        reconcile_consumed_meals
    from dora_api.features.routers import (DASHBOARD_ROUTER, MEAL_PLAN_ROUTER,
                                           RECIPE_ROUTER)

    @DASHBOARD_ROUTER.before_request
    @MEAL_PLAN_ROUTER.before_request
    @RECIPE_ROUTER.before_request
    def _reconcile():
        # Swallow + log failures so a broken reconciliation can't 500
        # every recipe / meal-plan / dashboard read. Stale pool counts
        # are recoverable; total page failure isn't.
        try:
            reconcile_consumed_meals()
        except Exception:  # noqa: BLE001
            logging.getLogger(__name__).exception(
                "reconcile_consumed_meals failed; serving stale pool counts"
            )

    for _Router in get_attributes_ending_with('router', Path() / 'dora_api' / 'features'):
        app.register_blueprint(_Router)
    app.register_blueprint(MIDDLEWARE)


@app.errorhandler(Exception)
def handle_global_exception(error: Exception):
    # Deliberate HTTP errors (abort(404), abort(503), …) must pass through
    # with their intended status — before this guard, EVERY abort() in the
    # app was being rewritten into an opaque 500 "unexpected error" (found
    # via the SPA catch-all's 404/503 during the UX-v2 endpoint removals).
    # Only genuinely unhandled exceptions become 500s.
    if isinstance(error, HTTPException):
        return error
    # FU-196 (b, partial) — a handler that raises after add()/flush() but
    # before commit leaves dirty state on the request-scoped session.
    # Flask-SQLAlchemy's teardown does eventually `session.remove()`
    # (which rolls back), but doing it explicitly here removes the
    # window where a later teardown-time SQL error could obscure the
    # original one, and makes the "500 means clean" contract obvious to
    # anyone reading the handler. Full unit-of-work refactor of the
    # multi-commit `create_recipe.py` path stays as its own FU.
    try:
        db.session.rollback()
    except Exception:  # noqa: BLE001
        logging.getLogger().exception("rollback in global handler failed")
    logging.getLogger().exception("Unhandled exception", exc_info=error)
    return internal_server_error("An unexpected error occurred.")


if __name__ == '__main__':
    startup()
