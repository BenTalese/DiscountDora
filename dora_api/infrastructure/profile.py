"""D3 — runtime profile (`development` / `production` / `test`).

Lives in dora_api's infrastructure package and is imported by both
service config managers so the profile concept stays single-source.
Profile is read once at module load via DORA_ENV; tests override by
setting the env var before importing.

The profile drives:
  - default log level
  - default debug flag
  - whether dev seed data may run
  - default CORS origins (open localhost set vs. required pinned list)
  - which "required env vars" must be present before boot

See `validate_production_requirements()` for the boot-time gate.
"""
import os
from enum import Enum
from typing import Sequence


class Profile(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"


_ALIASES = {
    "dev": Profile.DEVELOPMENT,
    "development": Profile.DEVELOPMENT,
    "local": Profile.DEVELOPMENT,
    "prod": Profile.PRODUCTION,
    "production": Profile.PRODUCTION,
    "test": Profile.TEST,
    "testing": Profile.TEST,
    "ci": Profile.TEST,
}


def current_profile() -> Profile:
    """Read DORA_ENV once per call. Cheap; we don't cache so tests
    that mutate the env var mid-run still see fresh values."""
    raw = (os.environ.get("DORA_ENV") or "").strip().lower()
    if not raw:
        return Profile.DEVELOPMENT
    return _ALIASES.get(raw, Profile.DEVELOPMENT)


def is_production() -> bool:
    return current_profile() is Profile.PRODUCTION


def is_test() -> bool:
    return current_profile() is Profile.TEST


# Required env vars per profile. Production demands a hard set;
# development asks for nothing. Test runs are gated by pytest's own
# fixtures so we don't require anything here.
PRODUCTION_REQUIRED_VARS: tuple[str, ...] = (
    # Signs session cookies. Without this every restart invalidates
    # every session AND the cookie is signable by anyone with the
    # source.
    "DORA_SECRET_KEY",
    # Pinned CORS origins (comma-separated). Without this the SPA
    # can't talk to the API from a real domain — production should
    # never fall back to the localhost defaults.
    "DORA_CORS_ORIGINS",
    # First admin account is bootstrapped against this email; without
    # it the first random visitor to /register becomes admin, which
    # is fine for dev but not for a public deploy.
    "ADMIN_BOOTSTRAP_EMAIL",
)


def validate_production_requirements(extra: Sequence[str] = ()) -> None:
    """Refuse to boot when in production and any required env var is
    missing. Prints a friendly multi-line error listing every missing
    var, then exits.

    `extra` lets a caller add service-specific requirements without
    touching the shared list (e.g. a future SMTP fan-in could require
    SMTP_HOST when DORA_EMAIL_ENABLED=true).

    Bypassed when DORA_SKIP_PROD_VALIDATION=true — the desktop bundle
    sets this because its required-vars story is different (no public
    CORS host, no bootstrap admin email, SECRET_KEY is auto-generated
    to the user-data dir). Never set this in a server deployment.
    """
    if not is_production():
        return
    if (os.environ.get("DORA_SKIP_PROD_VALIDATION") or "").lower() in {"1", "true", "yes", "on"}:
        return

    required = list(PRODUCTION_REQUIRED_VARS) + list(extra)
    missing = [name for name in required if not (os.environ.get(name) or "").strip()]
    if not missing:
        return

    lines = [
        "",
        "═══════════════════════════════════════════════════════════════",
        " DORA_ENV=production but required environment variables are",
        " missing. Refusing to start.",
        "═══════════════════════════════════════════════════════════════",
        "",
        " Missing:",
    ]
    for name in missing:
        lines.append(f"   - {name}")
    lines += [
        "",
        " Fix:  add the missing vars to your .env (or the deploy",
        " environment) and restart. See .env.example for what each",
        " var does.",
        "",
        " To run in dev mode instead, set DORA_ENV=development.",
        "═══════════════════════════════════════════════════════════════",
        "",
    ]
    msg = "\n".join(lines)
    # Print to stderr so container runtimes capture it even when the
    # logger isn't wired up yet, then exit non-zero so compose marks
    # the container as failed.
    import sys
    print(msg, file=sys.stderr, flush=True)
    sys.exit(1)
