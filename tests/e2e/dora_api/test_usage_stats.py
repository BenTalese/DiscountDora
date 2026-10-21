"""GET /api/dashboard/usage-stats — the About page's "how you've used Dora".

Owner 2026-09-05. The endpoint exists because About was rendering the
dashboard's *current-state* summary (what's low, what's out, what's this week)
under a heading that promised usage.

Two things are worth pinning here and nothing else is: the money gate, and the
agreement with the reports page. The plain counts are `SELECT COUNT(*)` and a
test that re-counts them would just be the implementation twice.
"""
import requests

from tests.support import set_money_enabled

BASE = "http://localhost:5170/api"
USAGE = f"{BASE}/dashboard/usage-stats"

MONEY_FIELDS = ("total_spend", "prices_recorded")
COUNT_FIELDS = (
    "stock_items", "recipes", "meals_planned",
    "meals_cooked", "shopping_lists", "shops_completed",
)


def test__usage_stats__money_off__gated_fields_are_null_not_zero(api):
    """R-058. Zero would claim "you have tracked no spend", which is a
    different statement from "this install doesn't do money" — and the SPA
    needs to tell them apart to decide whether to drop the tile or show £0."""
    original = requests.get(f"{BASE}/app-settings").json()["money_enabled"]
    set_money_enabled(False)
    try:
        body = requests.get(USAGE).json()
        for field in MONEY_FIELDS:
            assert body[field] is None, (
                f"{field} should be null with money off, got {body[field]!r}"
            )
        # The non-money half must still answer — turning money off doesn't
        # make the household's recipe count a secret.
        for field in COUNT_FIELDS:
            assert isinstance(body[field], int), f"{field} missing with money off"
    finally:
        set_money_enabled(original)


def test__usage_stats__money_on__gated_fields_are_populated(api):
    original = requests.get(f"{BASE}/app-settings").json()["money_enabled"]
    set_money_enabled(True)
    try:
        body = requests.get(USAGE).json()
        for field in MONEY_FIELDS:
            assert body[field] is not None, f"{field} should be populated with money on"
    finally:
        set_money_enabled(original)


def test__usage_stats__total_spend__agrees_with_spend_by_store_report(api):
    """The R-003 claim in `get_usage_stats._total_spend`, actually checked.

    About and Reports both answer "what has this household spent". They compute
    it in different places, so nothing but a test stops them drifting — and two
    screens quoting different lifetime totals for the same install is the exact
    failure that makes a user distrust every number in the app. If this breaks,
    the two definitions have diverged; reconcile them rather than updating the
    expected value.
    """
    original = requests.get(f"{BASE}/app-settings").json()["money_enabled"]
    set_money_enabled(True)
    try:
        mine = requests.get(USAGE).json()["total_spend"]
        report = requests.get(f"{BASE}/reports/spend-by-store?range=all").json()
        theirs = report.get("total_spend")
        if theirs is None:
            theirs = round(sum(row["spend"] for row in report["rows"]), 2)

        assert abs(mine - theirs) < 0.01, (
            f"About says {mine} lifetime spend, spend-by-store says {theirs}. "
            f"Both read ticked lines on completed lists, priced actual-then-"
            f"picked; one of them has drifted."
        )
    finally:
        set_money_enabled(original)
