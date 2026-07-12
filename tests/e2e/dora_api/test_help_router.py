"""FU-519 tail — e2e for the /api/help router.

Three read-only endpoints behind the Help panel:

  - GET /help/version    — current version + best-effort GitHub update check
    (network failure degrades to `latest_version: null` + `error`, never 5xx),
  - GET /help/changelog  — CHANGELOG.md parsed into per-version entries,
  - GET /help/food-fact  — random pick from the curated local list (shape +
    membership only; the pick is deliberately non-deterministic).

All three require an authenticated session (they're not in
PUBLIC_ENDPOINTS) — pinned via a fresh anonymous client.
"""
import requests

from dora_api.features.help.get_food_fact import FOOD_FACTS
from dora_api.features.help.version_info import CURRENT_VERSION
from tests.support import assert_problem

BASE = "http://localhost:5170/api"
HELP = f"{BASE}/help"

VERSION_KEYS = {
    "current_version", "latest_version", "update_available", "release_url", "error",
}


#region ---------------- version ----------------


def test__get_version__Shape__MatchesContractAndCurrentVersion(api):
    resp = requests.get(f"{HELP}/version")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body.keys()) == VERSION_KEYS
    assert body["current_version"] == CURRENT_VERSION
    assert isinstance(body["update_available"], bool)
    # The GitHub lookup is best-effort: either we got a tag, or we got an
    # error string and no update claim. Never both empty-and-claiming.
    if body["latest_version"] is None:
        assert body["update_available"] is False
    else:
        assert isinstance(body["latest_version"], str)
    if body["error"] is not None:
        assert body["latest_version"] is None
        assert body["update_available"] is False


#endregion version

#region ---------------- changelog ----------------


def test__get_changelog__ReadsRepoChangelog__ContentBearingEntries(api):
    resp = requests.get(f"{HELP}/changelog")

    assert resp.status_code == 200, resp.text
    entries = resp.json()["entries"]
    assert entries, "expected CHANGELOG.md at the repo root to parse into entries"
    assert set(entries[0].keys()) == {"version", "date", "body"}
    # Keep-a-changelog shape: an [Unreleased] block heads the file.
    versions = [e["version"] for e in entries]
    assert "Unreleased" in versions
    # Entries carry real markdown bodies, not empty splits.
    assert any(e["body"].strip() for e in entries)
    # Released entries carry their heading date.
    dated = [e for e in entries if e["version"] != "Unreleased"]
    if dated:
        assert any(e["date"] for e in dated)


#endregion changelog

#region ---------------- food fact ----------------


def test__get_food_fact__ReturnsOneCuratedFact(api):
    resp = requests.get(f"{HELP}/food-fact")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body.keys()) == {"fact"}
    # Random pick — assert membership in the curated list, not a value.
    assert body["fact"] in FOOD_FACTS


#endregion food fact

#region ---------------- auth posture ----------------


def test__help_endpoints__Anonymous__401(api):
    anon = requests.Session()
    for path in ("version", "changelog", "food-fact"):
        assert_problem(anon.get(f"{HELP}/{path}"), 401)


#endregion auth posture
