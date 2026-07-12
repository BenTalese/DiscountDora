"""STUB — FU-535: concurrency / race / idempotency behaviour.

WHY THIS MATTERS: every test to date issues requests strictly one-at-a-time
against a freshly-rolled-back DB, so nothing exercises two operations touching
the same row, a double-submitted mutation, or a replayed offline-queue action.
Real users double-tap buttons, the SPA's useOfflineQueue replays mutations on
reconnect, and FU-529 already caught a non-deterministic reconcile ordering
flake — all concurrency-shaped. These are the bugs that never show in
single-threaded tests and are brutal to debug in production.

FEASIBILITY — READ FIRST (this is why it's a stub, not written):
  The e2e conftest dispatches IN-PROCESS through Flask's test client over a
  single SQLite file with a per-test snapshot rollback. True parallel requests
  via ThreadPoolExecutor may hit SQLite's write-lock (`database is locked`) and
  the test client is not guaranteed thread-safe. The next agent must FIRST
  decide the right level for each case:
    (a) Genuine threads against the test client — try it; if SQLite locking
        makes it flaky, don't force it.
    (b) INTERLEAVED simulation — the higher-value, more deterministic option:
        drive the two operations' steps by hand in one thread in the
        adversarial order (read A, read B, write A, write B) to reproduce the
        lost-update / stale-read without real parallelism. Most of these bugs
        are logic races, not timing races, and reproduce interleaved.
    (c) Repository/handler level with a real short-lived Postgres (ties to
        FU-045 / FU-405 Postgres CI) for the cases that genuinely need MVCC.
  Document the choice per test in a comment.

CASES TO COVER:
  1. Double-submit idempotency — POST the same create twice (same client-
     generated id if the API takes one; else assert two distinct rows is the
     intended contract and pin it). The SPA's offline queue CAN replay, so a
     non-idempotent create is a real duplicate-data bug.
  2. Lost update on concurrent PATCH — two PATCHes to one stock item, one sets
     notes, one sets level; assert BOTH land (no last-writer-wins clobber of
     the untouched field). This is the read-modify-write window.
  3. Reconcile sweep vs manual verb (ties FU-529) — interleave the auto-drain
     sweep with a user "didn't cook" verb on the same entry; assert the user's
     decision wins and no duplicate receipt is written regardless of order.
  4. Concurrent stock-level drops — two drops on one item; assert the
     ConsumptionEvent / StockLevelChange ledger is consistent (no double-count,
     no skipped sequence). Depends on the FU-533 noload fix landing first.
  5. Delete-while-referenced race — delete an entity while another request adds
     a reference to it; assert a clean outcome (either the add 404s or the
     delete is blocked), never an orphan row or a 500.

CONVENTIONS: module-level `requests.*` is the authenticated admin client;
per-test rollback is automatic. Name tests test__<scenario>__<invariant>.
"""
import pytest

pytestmark = pytest.mark.skip(reason="FU-535 stub — assess feasibility per module docstring")


def test__double_submit_create__does_not_duplicate(api):
    ...


def test__concurrent_patch_disjoint_fields__both_land(api):
    ...


def test__reconcile_sweep_vs_manual_verb__user_decision_wins(api):
    """Ties FU-529 — deterministic ordering / no duplicate receipt."""
    ...


def test__concurrent_level_drops__ledger_stays_consistent(api):
    """Depends on the FU-533 consumption-event fix landing first."""
    ...


def test__delete_while_referenced__no_orphan_no_500(api):
    ...
