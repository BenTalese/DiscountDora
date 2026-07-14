# Performance & scale sweep — P5-03 / FU-388

**Date:** 2026-07-14 · **Status:** ✅ DB/query-scale pass done (clean) ·
**Scope:** backend query behaviour under load. Frontend bundle-size is a
separate axis, not covered here (spun as a follow-up).

## Method

The dev seed now generates load by default (FU-388 — `DORA_SEED_BULK_ITEMS`,
default 500). Profiled the heavy read endpoints in-process (Flask test client)
with a SQLAlchemy `before/after_cursor_execute` listener counting **SQL
statements per request** and flagging any normalised statement repeated many
times (the N+1 signature). Ran the same sweep at **500** and **2000** bulk
stock items — if a query count grows with row count, it's an N+1; if it stays
flat, the endpoint is set-based/eager-loaded.

(Profiler script kept in the session scratchpad, not committed — the method is
cheap to reproduce: seed loaded, attach the cursor listener, hit the endpoints,
diff query counts across two load sizes.)

## Headline finding — the app scales cleanly

**No N+1s anywhere.** Query counts were *identical* at 500 and 2000 items on
every endpoint profiled — proof the row-count doesn't drive query volume:

| Endpoint | Queries @500 | Queries @2000 | Notes |
|---|---:|---:|---|
| `GET /api/stock-items` (+`?limit=100`) | 4 | 4 | flat; paginated count + page |
| `GET /api/recipes` (+`?limit=100`) | 14 | 14 | **cookability is set-based, not per-recipe** — the N+1 I most feared isn't one |
| `GET /api/recipes/<id>` | 14 | 14 | flat |
| `GET /api/stock-locations` (heatmap) | 3 | 3 | flat |
| `GET /api/shopping-lists` | 2 | 2 | flat |
| `GET /api/shopping-lists/<id>` | 9 | 9 | flat |
| `GET /api/meal-plans` | 6 | 6 | flat |
| `GET /api/products` | 6 | 6 | flat |
| `GET /api/alerts` | 11 | 11 | flat |
| `GET /api/health` | 5 → **3** (fixed) | — | see below |

Wall times stayed low throughout (single-digit to ~90ms, the ~90ms being
serialization of 100 recipes, not query scaling).

## The one inefficiency found + fixed

**`/api/health` re-read the `AppSetting` singleton ~4× per probe** — each of
`_feature_flags` / `_locale_policy` / `_image_policy` called
`get_or_create_app_setting` independently. Not a scale issue (constant, one-row
reads), but `/health` is polled by every client, so it's worth deduping.

**Fix (shipped):** `health_check()` now fetches the singleton **once** and
threads it through the three blocks (None on DB error → each falls back to its
existing conservative defaults, so resilience is unchanged). `/api/health`
dropped from **5 → 3** queries; the singleton reads went x4 → x2 (the residual
x2 is the one intentional fetch + one inside `resolved_operational_config`,
left alone as out-of-scope). Payload shape unchanged (DTO-contract +
health-router + onboarding-flags + locale + auth-flows tests all green).

## Residual (same redundant-singleton pattern, lower value)

`GET /api/alerts` (x3), `GET /api/recipes` / `/api/meal-plans` (the
`timezone, auto_drain_past_meals` read + others) still re-read the `AppSetting`
singleton a few times within a request. Same non-scaling constant overhead as
health was. The general fix is **request-scoped memoization** of the singleton
(a `g`-cached `get_or_create_app_setting`), which carries a small
invalidation nuance (a request that *mutates* settings must bust the cache), so
it's not a drive-by — spun as a follow-up rather than folded into this sweep.

## Not covered (spun as follow-up)

- **Frontend bundle size** — the P5-03 line item for JS bundle analysis /
  code-splitting was not touched here (this pass was backend query behaviour).
- **Request-scoped `AppSetting` memoization** for the other read endpoints
  (above).

Both tracked as **FU-560**.

---

## FU-560 addendum (2026-07-14) — the two remaining slices, done

### Frontend bundle-size — analysed, healthy, no action

`quasar build -m pwa` output: **route-level code-splitting is working** — every
page is its own lazy chunk. Entry is modest (`index` 144 KB, `MainLayout` 101
KB). Total JS 2701 KB / 233 files, but that's the *sum* of on-demand chunks, not
initial load.

The one >500 KB chunk (Vite's warning): **`ReportsPage` 549 KB + an `esm-*` 425
KB vendor chunk = echarts.** ReportsPage imports echarts the correct
tree-shakeable way (`echarts/charts` LineChart/PieChart + named components +
`CanvasRenderer`, via `vue-echarts`), and the page is route-split, so echarts
loads **only when the user opens /reports** — it never touches initial load.
Verdict: **acceptable, no change.** Charts are inherently heavy; lazy-loading
them behind their own route is exactly right. (Left the Vite warning in place
rather than raising `chunkSizeWarningLimit` — better to keep the signal and know
ReportsPage is the known-large chunk than to blanket-silence it.)

### Request-scoped `AppSetting` memoization — shipped

`get_or_create_app_setting` now memoises the singleton on the Flask
application-context `g` (`app_settings/access.py`). Safe without explicit
invalidation — the cached value is the identity-map instance (in-place mutations
+ commit flow through it), the row is never deleted/replaced within a live
request (only boot + the demo-reset job call `drop_all`, each in its own
context; restore is additive), and `g` shares the app-context lifetime with the
scoped session (fresh per request). Falls through to the DB when there's no app
context.

Effect (re-profiled at 500 items): `/api/health` **5→2** queries, `/api/alerts`
**11→10**. The residual `SELECT timezone, auto_drain_past_meals FROM AppSetting`
on recipes/meal-plans is a *different* projected query (the clock/reconcile path
reads those columns directly, not via the accessor) — out of this fix's scope,
left as-is. Full backend e2e suite **1006 passed** — the memoization is correct
across every settings/capabilities/stocktake/reports path, including the
settings-mutation path.

**FU-560 closed.** Pre-existing, unrelated finding surfaced while running the
top-level suite: `tests/test_migrations.py` two tests fail in the full
top-level run (pass in isolation) — logged as FU-561.
