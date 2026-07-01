"""GET /api/help/version — current Dora version + (optional) update check.

Update detection hits the GitHub Releases API server-side, so the browser
never has to deal with CORS and the call can be cached cheaply. If the
network call fails (offline, rate-limited, repo not public), we return the
current version with `latest_version` = null so the UI can still say
"you're on x.y.z" without claiming an update status it doesn't know.
"""
import json
import logging
from dataclasses import dataclass
from time import time
from typing import Optional
from urllib.request import Request, urlopen

from dora_api.features.help.version_info import CURRENT_VERSION
from dora_api.features.routers import HELP_ROUTER
from dora_api.infrastructure.api_response import ok


# Cache the latest-release lookup so every "is there an update?" check
# doesn't hit GitHub. 30 minutes is fine — Dora is not a security tool.
_CACHE: dict[str, object] = {"value": None, "fetched_at": 0.0}
_TTL_SECONDS = 60 * 30

_GITHUB_RELEASE_URL = "https://api.github.com/repos/BenTalese/DashyDora/releases/latest"


@dataclass(frozen=True, slots=True)
class VersionInfoDto:
    current_version: str
    latest_version: Optional[str]
    update_available: bool
    release_url: Optional[str]
    error: Optional[str]


def _fetch_latest_release() -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Returns (tag_name, html_url, error). Any of these can be None."""
    now = time()
    cached = _CACHE.get("value")
    fetched_at = _CACHE.get("fetched_at") or 0.0
    if cached is not None and (now - float(fetched_at)) < _TTL_SECONDS:
        # Cached tuple already in the shape we want.
        return cached  # type: ignore[return-value]

    try:
        req = Request(_GITHUB_RELEASE_URL, headers={
            "Accept": "application/vnd.github+json",
            # GitHub returns 403 for unauthenticated requests without a UA.
            "User-Agent": "DashyDora-Help",
        })
        with urlopen(req, timeout=4) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        tag = str(payload.get("tag_name") or "").lstrip("v") or None
        url = payload.get("html_url") or None
        result: tuple[Optional[str], Optional[str], Optional[str]] = (tag, url, None)
    except Exception as exc:
        # Don't fail the endpoint just because GitHub is unreachable; the
        # frontend treats `error` as "skip the update banner".
        result = (None, None, str(exc))

    _CACHE["value"] = result
    _CACHE["fetched_at"] = now
    return result


def _semver_tuple(version: str) -> tuple[int, ...]:
    """Naive semver parse — splits on '.', ignores non-numeric trailing bits.
    Sufficient for "is the latest tag newer than what's running?" without
    pulling in a dependency."""
    parts: list[int] = []
    for piece in version.split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


@HELP_ROUTER.route("/version", methods=["GET"])
def get_version():
    _Logger = logging.getLogger(__name__)
    latest, release_url, error = _fetch_latest_release()
    update_available = False
    if latest:
        try:
            update_available = _semver_tuple(latest) > _semver_tuple(CURRENT_VERSION)
        except Exception:
            update_available = False
    _Logger.debug(
        "version=%s latest=%s update=%s err=%s",
        CURRENT_VERSION, latest, update_available, error,
    )
    return ok(VersionInfoDto(
        current_version = CURRENT_VERSION,
        latest_version = latest,
        update_available = update_available,
        release_url = release_url,
        error = error,
    ))
