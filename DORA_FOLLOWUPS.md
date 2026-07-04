# Dora Follow-ups Ledger — Open

Stateful backlog of **open follow-ups, deferred jobs, leftovers, and findings**
surfaced while running prompts — the stuff that's easy for the user to miss in a
long session summary. Distinct from the other logs:

- `CHANGELOG.md` = product/code changes that shipped.
- `DORA_WORKLOG.md` = per-session handoff narrative.
- `DORA_FOLLOWUPS.md` (this file) = **open loops** that outlive a single session.
- `DORA_FOLLOWUPS_RESOLVED.md` = the archive of items that have been resolved
  (kept for the trail — never delete).

## How to use this file

- **On session start:** scan for items here. Surface the ones whose *recommended
  resolution point* is "now" or matches the work about to start, and **ask the
  user** whether they want to review/resolve them now or defer.
- **On ending a work unit:** add any new follow-ups/leftovers/findings you
  generated. If you actually resolved an item, **move its entry from this file
  to `DORA_FOLLOWUPS_RESOLVED.md`**, flip the heading from `[OPEN]` to
  `[RESOLVED]`, and add a one-line state note on how. Do not leave resolved
  items in this file, and do not delete them either — the trail matters.
- **Reported defect that "doesn't reproduce" → still log it here** as `[OPEN]`
  type `finding`, resolution "confirm in browser". A static code read is not
  proof a user-reported bug is fixed. Track each reported item individually;
  never bury several as one "all fine" note.
- Keep the newest items at the top.

## Entry template

```
## [OPEN] FU-NNN — short title
- **Raised:** YYYY-MM-DD (prompt id / task)
- **Type:** follow-up | deferred job | leftover | finding
- **What:** one or two lines.
- **Why deferred:** the reason it wasn't done in-line.
- **Recommended resolution:** now | later during <Phase/Prompt X> | when <trigger> | opportunistic
```

---

## [OPEN] FU-NNN — short title
- **Raised:** YYYY-MM-DD (prompt id / task)
- **Type:** follow-up | deferred job | leftover | finding
- **What:** one or two lines.
- **Why deferred:** the reason it wasn't done in-line.
- **Recommended resolution:** now | later during <Phase/Prompt X> | when <trigger> | opportunistic
- **State note:** (filled in when resolved — date + how)
```

---

# Open


## [OPEN] FU-465 — Native push notifications (FCM bridge) not wired
- **Raised:** 2026-07-04 (P8-10 close-gate).
- **Type:** deferred job.
- **What:** VAPID web push works in the browser + PWA install path but Android's WebView doesn't expose the Push / PushManager / Notification APIs, so the Capacitor build's push toggle reads `unsupported`. To make proactive alerts (deal-for-you, run-out, expiry) work on the native app, wire `@capacitor/push-notifications` + Firebase Cloud Messaging on Android (and APNS on iOS when that platform is built). Server-side: a native-endpoint subscription store parallel to the web-push VAPID one, plus a fan-out in `push_sender.py`. Manifest already declares `POST_NOTIFICATIONS`.
- **Why deferred:** user picked "keep VAPID web push" at P8-10 scope-lock — smallest surface, avoids a Firebase dependency, matches self-host posture. Native push is only worth the FCM/Firebase cost once there's actual demand.
- **Recommended resolution:** when someone actually installs the native app and complains about missing notifications (or when Phase 4 commercialisation starts). Firebase project setup + `google-services.json` + backend fan-out is roughly a half-day of work.

## [OPEN] FU-464 — Auto-add-when-low threshold is stale after the 3-band collapse (`>= 2` = Out only)
- **Raised:** 2026-07-03 (spotted while wiring P8-07 consumption events into `update_stock_item.py`).
- **Type:** finding (real bug — behaviour drift).
- **What:** [`update_stock_item.py`](dora_api/features/stock_items/update_stock_item.py) auto-add hook fires on `_NewLevelSeq >= 2` with a stale comment `# 2 = Low, 3 = Out (see seed)`. That comment reflects the OLD 4-band sequences (0 Stocked / 1 Sufficient / 2 Low / 3 Out). After the 2026-07-02 Sufficient-band collapse the canonical sequences are **0 Stocked / 1 Low / 2 Out** (`dora_api/domain/stock_status.py`). So `>= 2` now means **Out only** — an item transitioning to **Low** no longer auto-adds, even with `auto_add_when_low` set. The intent is low-or-out (`needs_restock`, seq ≥ 1).
- **Why not fixed here:** out of P8-07 scope (R-007); touches the auto-add behaviour which has its own DORA_VERIFY coverage. Flagged per the engineering-standards close-gate (R-003 — a bare `2` literal duplicating a domain threshold).
- **Recommended resolution:** now/opportunistic — replace the `>= 2` + `< 2` literals with `needs_restock(...)` / `LOW_STOCK_SEQUENCE` from `stock_status.py` (server-side single source), and re-verify the auto-add-when-low DORA_VERIFY item. Small, high-value fix.

## [OPEN] FU-463 — Sibling `text() + str(uuid) IN :ids` queries silently returning zero rows on SQLite
- **Raised:** 2026-07-03 (spotted during FU-171 resolution).
- **Type:** finding (latent bug on SQLite deployments; harmless on Postgres).
- **What:** Two remaining call sites use the same broken shape that FU-171 fixed:
  - `dora_api/features/stock_items/get_stock_items.py:_hydrate_linked_product_count` — the `linked_product_count` on every stock-item DTO defaults to 0 on SQLite because the `WHERE stock_item_id IN :ids` bind never matches BINARY(16) ids.
  - `dora_api/features/recipes/get_recipes.py:_compute_estimated_cost` — recipe-detail cost estimation joins through `StockItemProduct` on `stock_item_id IN :ids`; same reason it silently returns no rows on SQLite, so `estimated_cost` is always None.
- **Why deferred:** neither is on the surface the user reported (FU-171 was strictly the recipe-image toggle); rewrites are less mechanical than the recipe one (aggregations across a link table). Postgres deployments were never affected.
- **Recommended resolution:** now-ish — same pattern as FU-171's fix (drop raw `text()`, use ORM `select()` with SQLAlchemy Core so UUIDType coerces the bindings). Small pass; verify by curl against a SQLite-backed dev instance that `linked_product_count > 0` for a stock item with linked products, and `estimated_cost != null` for a recipe whose ingredients have priced products.

## [OPEN] FU-462 — Sweep the ~237 prompt-ID comments (`P[0-9]-` / `C-[0-9]` / `B[0-9]`) from shipped source
- **Raised:** 2026-07-03 (FU-196 umbrella disassembly — item (f) sub-part).
- **Type:** deferred job / pre-release polish.
- **What:** The senior review flagged ~237 prompt-ID comments in shipped source (e.g. `// C-4 Chunk 2 —`, `# P8-05 — …`) — useful during construction, noise pre-release. Sweep by category: keep the ones that document a *rule* (R-003 / R-014 / ADR references) or an incident's *why*; drop the ones that only name the prompt that produced them. FU-424 also tracks this as one of the review's Tier-2 items — the two FUs are the same finding.
- **Why deferred:** cross-cutting, pre-release-only polish; no user-visible effect.
- **Recommended resolution:** later — pre-release polish pass, or fold into FU-424's broader Tier-2 delta re-audit.

## [OPEN] FU-461 — Account-deletion endpoint (GDPR) — design + build
- **Raised:** 2026-07-03 (FU-196 umbrella disassembly — item (e) sub-part).
- **Type:** deferred job / feature (compliance).
- **What:** No account-deletion path exists (`DELETE /auth/me` etc.). Needed for GDPR "right to erasure" once the product is user-facing. Design questions: soft-delete (retention window) vs hard-delete, cascade rules (personal data vs household-shared data like recipes/products), auth (password reprompt), audit trail, self-service UI location (Settings → Account danger-zone). Recommend a short brief before building.
- **Why deferred:** real feature with UX + policy calls, not a fix.
- **Recommended resolution:** before Phase 4 commercialization. Write a short brief in `docs/04_proposals/` first (`PROPOSAL_ACCOUNT_DELETION.md`), then implement as its own chunk.

## [OPEN] FU-460 — `SESSION_COOKIE_SECURE` default: keep off or flip on?
- **Raised:** 2026-07-03 (FU-196 umbrella disassembly — item (e) sub-part).
- **Type:** finding / policy call.
- **What:** [`app.py:90`](dora_api/app.py) sets `SESSION_COOKIE_SECURE` from `DORA_SECURE_COOKIES` env var, **defaulting off**. Correct for local HTTP dev but a footgun for a first-time SaaS operator who forgets to set the var — session cookies then travel over cookie-visible transports. Options: (a) keep default off, add a boot-time WARNING when `DORA_ENV=prod` + `SECURE_COOKIES` unset; (b) flip default on and require an explicit `DORA_SECURE_COOKIES=false` for dev; (c) auto-detect from request scheme (Flask's `PREFERRED_URL_SCHEME` or `X-Forwarded-Proto`). Distribution-posture rule (§7.5) wants same artifact, different config — option (a) fits that shape best.
- **Why deferred:** policy call, not a bug per se.
- **Recommended resolution:** before Phase 4 commercialization. If (a): add the boot-time warning now (10 lines in `startup.py`, mirroring the existing "refuse to boot in production when required env vars are missing" pattern).

## [OPEN] FU-459 — App-wide security headers (CSP / X-Frame-Options / X-Content-Type-Options / Referrer-Policy)
- **Raised:** 2026-07-03 (FU-196 umbrella disassembly — item (e) sub-part).
- **Type:** deferred job / hardening.
- **What:** No app-wide security-header middleware. Add a response-hook in `infrastructure/middleware.py` that sets `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer-when-downgrade`, and a permissive-but-honest `Content-Security-Policy` (script-src 'self' 'unsafe-inline'/'unsafe-eval' initially — Quasar's runtime uses eval-ish patterns; tighten later). Flask-Talisman is one option; hand-rolled is fine at this scope.
- **Why deferred:** Tier-2 hardening, not ship-blocking; CSP tuning has to be done carefully to avoid breaking Piper TTS / print-view / any inline styles the SPA relies on.
- **Recommended resolution:** later — pair with the security-review Tier-2 delta re-audit (FU-424). Write a one-hit browser-verify sweep after landing (all pages still render, no CSP violations in the console).

## [OPEN] FU-458 — Rate-limit assistant endpoints
- **Raised:** 2026-07-03 (FU-196 umbrella disassembly — item (e) sub-part).
- **Type:** deferred job / hardening.
- **What:** `dora_api/features/assistant/ask_assistant.py:368` (`POST /assistant/ask`) and the confirm-actions endpoint have no rate limit. In multi-tenant (Phase 4) an authenticated user could burn a lot of upstream LLM tokens by looping requests. Options: `flask-limiter` (per-user token bucket, in-memory or Redis), or hand-rolled per-user counter in a DB table. Rate limits should be per-user (`session.user_id`), not per-IP (shared households).
- **Why deferred:** Tier-2 hardening; Phase 3 is single-user personal-use so the risk is theoretical.
- **Recommended resolution:** before Phase 4 commercialization / when the first tenancy work starts. Pair with a per-user token accounting design if paid-provider LLM is on.

## [OPEN] FU-457 — Boot-time resolved-route assertion for reflection-based wiring
- **Raised:** 2026-07-03 (FU-196 umbrella disassembly — item (c)).
- **Type:** finding / hardening.
- **What:** [`startup.py:135`](dora_api/startup.py) uses `get_attributes_ending_with('router', ...)` to auto-register blueprints; [`service_wiring.py:17`](dora_api/infrastructure/service_wiring.py) and [`decorators.py:13`](dora_api/infrastructure/decorators.py) also do reflection-based wiring. If a router file has a broken import or is renamed, the failure surfaces at the first request (opaque 404), not at boot. Add a boot-time assertion that (a) every discovered `*_ROUTER` was successfully registered on `app.url_map` (compare expected vs `app.url_map.iter_rules()`), (b) every `@has_request_body`-decorated handler has a registered URL rule. Fail-fast → operator sees the misconfiguration on `flask run`, not on the first 404.
- **Why deferred:** Tier-2 hardening; current failure mode is a 404 which is diagnosable, just not obvious.
- **Recommended resolution:** opportunistic — small (30-line assertion in `startup.py` after `register_routers()`), useful the first time a router silently breaks.

## [OPEN] FU-456 — Unit-of-work refactor for multi-commit handlers (starting with `create_recipe.py`)
- **Raised:** 2026-07-03 (FU-196 umbrella disassembly — item (b)).
- **Type:** deferred job / architecture.
- **What:** [`create_recipe.py`](dora_api/features/recipes/create_recipe.py) calls `self.repository.save_changes()` five times in one handler (L273/317/332/362/379) — no unit-of-work; a partial failure leaves committed rows plus dirty session state. FU-196's belt-and-braces `db.session.rollback()` in the global handler (shipped 2026-07-03) covers the *dirty-session* half; the *partial-commit* half needs the handler restructured to a single commit at the end. Sweep other multi-commit handlers when this pattern is decided (grep `save_changes` for count-per-file). Constraint: some handlers `add()` a parent → need its id → then `add()` children referencing that id, which currently uses an interstitial `save_changes()` to force a flush. Look at whether `db.session.flush()` (no commit) is enough for those cases so the whole handler stays one transaction.
- **Why deferred:** real refactor, not a one-liner; safer to do after the rollback safety net (done 2026-07-03) rather than before.
- **Recommended resolution:** later — Type-B aggregates pass, or the next serious cookbook-editor touch.

## [OPEN] FU-452 — P6-11 location-aware grouping (put-away + expiry-by-location) never built
- **Raised:** 2026-07-02 (P6 legacy-plan cross-check).
- **Type:** deferred job (Phase 1 loop item, un-started; fell off the map when spatial locations were retired).
- **What:** `docs/06_legacy_prompt_plans/PROMPT_PLAN_PART_6_POLISH.md:688` specified two flows on the (now simple) location tree: **(A)** after `Finish & restock`, offer a put-away checklist grouped by `stock_location` tree node ("Freezer: 3 · Pantry: 2 · Fridge: 4") with tick-per-group + quick-assign for unsorted items; **(B)** in the expiry/alerts view, allow grouping expiring items by location node ("Back of freezer: 2 expiring"). No new alert type — just a presentation grouping over `get_alerts` data. Grep confirms neither flow exists: the only `_group_by_location` hit is in [`export_stock_overview.py`](dora_api/features/data/export_stock_overview.py) (a CSV export helper, not either P6-11 surface). Explicitly **not** on `PROJECT_STATE.md`'s attention list — probably dropped off after the spatial-location idea was cut (they simplified past the goal).
- **Why deferred:** believed absorbed by other work; nothing built.
- **Recommended resolution:** later during Phase 1 mop-up. Small — no data model change, uses existing tree + alerts data. Or, if the appetite isn't there, **explicitly cut** and log it (better a clean CUT than a silent drop). MUST NOT reintroduce stock-map / spatial coordinates / location routing (charter Removed-features list).

## [OPEN] FU-451 — P6-09 budget-defense swaps (the "negotiator" half) never built
- **Raised:** 2026-07-02 (P6 legacy-plan cross-check).
- **Type:** deferred job (partial coverage — only the passive tracker half shipped).
- **What:** `PROMPT_PLAN_PART_6_POLISH.md:594` had two halves. **Shipped:** per-recipe cost estimate (Cookbook Chunk 9, uses `paid_price` via FU-216). **Missing:** the headline "negotiator" — `cost_per_week` on meal-plan weeks (no `cost_per_week` grep hits), and the budget-defense loop that, when a week is over budget, emits ranked swap suggestions with concrete dollar savings and one-tap apply — **(a)** PRODUCT swap ("Buy the on-special <brand> for the chicken instead of your usual → save $X"; reuse `compare_prices`), **(b)** RECIPE swap ("Swap Thursday's <expensive recipe> for <cheaper saved recipe> → save $Y"). Must NOT use a stock-item substitute graph (that surface is retired). Depends on P6-03 deal-quality signal being present (see FU-450) for the "prefer genuinely-good-price products" ranking.
- **Why deferred:** the negotiator loop needs the P6-03 signal + a design call on where the swaps surface (meal-plan week, budget card, both?); recipe cost shipped standalone and no one closed the rest.
- **Recommended resolution:** later during Phase 1 mop-up; or fold into the P8-08 Dora Score card (over-budget bullet → "Save $X: apply this swap"), which is where FU-352 already parks the daily-briefing bullets. Do FU-450 (P6-03 signal) first or in parallel.

## [OPEN] FU-450 — P6-03 deal-quality (deal_score / fake_markdown / percentile) never built as spec'd
- **Raised:** 2026-07-02 (P6 legacy-plan cross-check).
- **Type:** deferred job (superseded framing; specific pieces still worth extracting).
- **What:** `PROMPT_PLAN_PART_6_POLISH.md:233` specified a pure-function scorer over per-product offer history (`lowest_price`, `is_lowest_in_window`, percentile, **`fake_markdown` flag**, 0–100 `deal_score`), a `good_deal` alert type with one-tap add-to-list + per-user threshold + throttle, and a lowest/median overlay on `PriceHistoryPage.vue`. Zero code hits for `deal_score`, `fake_markdown`, or `is_lowest_in_window`; `find_deals` in `dora_api/features/assistant/tools.py` still returns raw offers. **Superseded framing:** the **P8-05 buy-verdict oracle** (shipped 2026-07-02) answers "is this a good price" with a verdict badge on rows + shopping-lines — different shape, same intent. **Missing pieces still valuable:** (a) the **`fake_markdown` flag** (detects inflated "was" prices — truth-in-advertising for a product literally called Dora that tracks *discounts*); (b) the **`good_deal` alert type** with one-tap add-to-list + throttle (proactive, not just passive on-page).
- **Why deferred:** framing moved from "score" to "verdict" (P8-05); the leftover pieces weren't back-ported.
- **Recommended resolution:** opportunistic — fold the `fake_markdown` detection into `BuyVerdictCard` (also un-wires FU-437), and add the `good_deal` alert type to `get_alerts.py`. Skip the 0–100 score + percentile UI — P8-05 replaces that surface. Feeds FU-451 (budget defense wants a deal-quality signal to rank product swaps).

## [OPEN] FU-448 — P2-05 tail: budget-aware auto-generated shopping lists (optimizer piece never built)
- **Raised:** 2026-07-02 (surfaced while checking whether P2-05 was done).
- **Type:** deferred job (design + build; nice-to-have).
- **What:** P2-05 in the original plan
  ([`docs/06_legacy_prompt_plans/PROMPT_PLAN_PART_2.md:400`](docs/06_legacy_prompt_plans/PROMPT_PLAN_PART_2.md)
  "Budget-Aware Auto Lists") had **two halves**. The *user-facing budget* half
  is fully shipped: [`features/budget/budget.py`](dora_api/features/budget/budget.py),
  migration `a6e3b5d2c8f1_20260606_user_budget.py`,
  `User.budget_amount` / `budget_period` handled in
  [`update_me.py:49-56, 164-178`](dora_api/features/auth/update_me.py),
  budget-vs-spend surfacing at
  [`DashboardPage.vue:380`](web_app/src/pages/DashboardPage.vue) (the P2-05
  "Grocery budget" card). The **optimizer half was not built** — the
  auto-generated shopping-list flow
  ([`features/shopping_lists/auto_generate.py`](dora_api/features/shopping_lists/auto_generate.py))
  does not consult `budget_amount` anywhere (verified: `grep -n budget` on that
  file returns only unrelated `frequently_added_limit` matches). No "keep the
  list under $X" / "trim items to fit the budget" pass, no per-list
  `budget_target` / `budget_strategy` columns, no `POST /shopping-lists/optimize`
  route, no strategy segmented control in the auto-generate modal, no
  explainability chips ("Deferred because it would exceed budget"), no
  "Build me a $120 shop" assistant intent. What the original P2-05 spec called
  for on that side is all missing.
- **What NOT to keep from the original spec:** `preferred_merchants` +
  cross-store strategies (`"fewest_stores"` / `"preferred_store"`) are coupled
  to hosted multi-store scraping, which the reconciled plan explicitly retired
  (`RECONCILED_FINISHING_PLAN.md` Decision 7). Any brief here should drop those
  strategies or reshape them around ingested product data (C-10).
- **Why deferred:** shipped the simpler user-facing budget + alert first; the
  optimizer wants a proper design (which items to drop first, how essentials +
  low-stock priorities compose with budget, whether it warns or hard-caps,
  whether the budget is per-shop or per-period remaining, and how it interacts
  with P8-05 buy-verdict on individual items).
- **Recommended resolution:** later (opportunistic Phase 3-ish, or bundled with
  the next shopping-list intelligence pass) — **needs a proper design brief
  first, not a direct build.** The brief should cover: (a) UX shape (soft warn
  vs auto-trim vs suggest-swap), (b) priority stack (essential > low-stock >
  frequently-added when budget-constrained), (c) whether "budget" ties to
  `budget_period` remaining or a single-shop cap, (d) explainability (per-line
  "why deferred" reasons), (e) interaction with P8-05 (each candidate already
  has a buy/wait/skip verdict — the optimizer can lean on those instead of
  re-deriving priorities), (f) which of the original P2-05 spec pieces
  (multi-store strategies, `preferred_merchants`) get dropped per the
  post-scrape-divorce charter.

## [OPEN] FU-447 — Security: AUTH_ASSISTANT findings (HIGH CSRF + MEDIUM email-change) still unfixed
- **Raised:** 2026-07-02 (surfaced by the full doc-register audit).
- **Type:** finding (security).
- **What:** `docs/05_investigations/AUTH_ASSISTANT_SECURITY_FINDINGS.md` (dated
  2026-06-04, "Draft for discussion") records a **HIGH-severity CSRF** flaw and a
  **MEDIUM email-change** flaw. No fix is logged in CHANGELOG/worklog; the report
  is still `[OPEN]` with the findings standing.
- **Why deferred:** The report was written but never actioned; it's orphaned from
  the "needs attention" view, so it silently aged.
- **Recommended resolution:** now — review the two findings and decide fix-vs-accept
  before more Phase-3 champion work. Now surfaced at the top of `PROJECT_STATE.md`.

## [OPEN] FU-445 — Stale "no code yet" status headers on ~15 shipped docs
- **Raised:** 2026-07-02 (doc-register audit).
- **Type:** finding.
- **What:** ~13 `IMPL_PLAN_*` (Alerts, Cart, Cookbook, Cook-Mode, Dashboard,
  Error-Handling, Ingestion, Meal-Plans, State-Ownership, Stock-Item-Detail,
  Stock-Overview, Waste) + 2 proposals (Auth-Shell, Buy-Verdict-Oracle) still carry
  a top "Status: … no code yet / Implementing" line despite the feature having fully
  shipped. Doc *bodies* are accurate design records — only the header lies. Full list
  in the `PROJECT_STATE.md` document register (marked "stale header").
- **Why deferred:** Purely cosmetic per-file edit; batch it rather than interleave.
- **Recommended resolution:** opportunistic — batch-flip each header to a
  done/record status (e.g. "✅ Shipped — see CHANGELOG"). The `PROJECT_STATE.md`
  register already carries the truth, so this is de-risked, not urgent.

## [OPEN] FU-444 — `test__all_axes_thin__collapses_to_single_not_enough_history` fails on pre-existing composer behaviour
- **Raised:** 2026-07-02 (surfaced while running `pytest` for the Sufficient-band axe close-gate).
- **Type:** finding (pre-existing, not introduced this session).
- **What:** [`tests/test_buy_verdict.py:222`](tests/test_buy_verdict.py) asserts that "three thin axes ⇒ one honest reason" — but the fixture (`price_samples=[one]`, `stock_level_band="unknown"`, `waste_events_12mo=0, purchases_12mo=1`) only produces two thin axes: `_waste_axis` returns `(None, "no_waste_history")`, not `thin_data`, when purchases is under `_MIN_PURCHASES_FOR_WASTE_RATE` **and** waste_events is 0. The composer at [`get_buy_verdict.py:314`](dora_api/features/stock_items/get_buy_verdict.py) only surfaces the collapsed "not enough history yet" reason when `len(thin) == 3`, so this test lands with an empty `reasons` list. Confirmed pre-existing via `git stash` re-run against `main`.
- **Resolution options:**
  1. Loosen the composer trigger to "zero reasons produced" (broadest — matches the test's intent that a bare-data verdict should carry one honest message).
  2. Widen the fixture to actually trigger three thin axes (e.g. `purchases_12mo=1, waste_events_12mo=1` so the waste axis returns `thin_data` per the `< _MIN_PURCHASES_FOR_WASTE_RATE` branch line 243).
  3. Retire the test if the composer's stricter contract is intentional.
- **Why deferred:** unrelated to the Sufficient-band axe; pre-existed on `main`. Small enough to be a single unit later.
- **Recommended resolution:** opportunistic — next time buy-verdict is opened for change (P8-06 wait-until work looks likely; see FU-438). Not blocking anything.

## [OPEN] FU-442 — §LOGIN password-policy feedback still uncovered
- **Raised:** 2026-07-02 (C-19 audit — spotted while writing coverage table).
- **Type:** finding.
- **What:** feedback bullet "Password policy feels too restrictive, do
  minimum of 8 characters, and allow admins to turn the restrictions
  off." C-19 explicitly leaves this alone (out of shell-styling scope).
  Not tracked by any Wave-A prompt or existing proposal — grep for
  "password polic|8 char|admin.*toggle" only hits the C-19 note that
  says it's out-of-scope. Real gap.
- **Why deferred:** doesn't belong in an auth-shell styling proposal;
  needs its own decision (default min length, admin override storage —
  `AppSetting` config; C-cross may already own the settings shell).
- **Recommended resolution:** later during `PROPOSAL_CONFIG_AND_OPTINS.md`
  extension, or spin a small standalone prompt. Not blocking C-19.

## [OPEN] FU-454 — BuyVerdictCard `mark_stocked` + `remove_from_list` one-tap actions unwired
- **Raised:** 2026-07-02 (P8-06 close, spotted while closing FU-437).
- **Type:** deferred job (polish; nice-to-have).
- **What:** the card's one-tap-action button now renders in
  `StockItemDetailPage.vue` overview tab, and the `add_to_list` variant is
  fully wired. The other two variants (`mark_stocked` when
  wastes-often + stocked → "Already stocked"; `remove_from_list` when the
  item is already on an open list → "Remove from list") emit their
  `@action` events but the handler in `onBuyVerdictAction` is a no-op
  nudge — the fact editors immediately below the card *are* the primary
  way to change level or remove a list line. Tapping the button is silent,
  which is quietly-broken UX (Charter P3).
- **Why deferred:** wiring these needs the "Well-Stocked" `StockLevel` id
  lookup (from `stockLevelStore`) + a specific list-line target (find the
  open list containing this item + drop that line). Neither is difficult;
  it just wasn't the P8-06 story and the fact editors cover both cases.
- **Recommended resolution:** opportunistic — either wire both handlers
  properly, OR hide the card's one-tap button for these two `kind` values
  (reveal-and-disable, R-014) so users don't tap a dead button. Small
  either way.

## [OPEN] FU-434 — Pre-existing `AdminDataImport.vue` `exactOptional` errors
- **Raised:** 2026-07-02 (P8-02 close-gate — spotted via `vue-tsc`).
- **Type:** finding (pre-existing, not touched by P8-02).
- **What:** `vue-tsc --noEmit` reports two errors in
  [`AdminDataImport.vue:33,35`](web_app/src/pages/settings/AdminDataImport.vue):
  a `find(...)` result assigned to `ImportTemplate` without narrowing
  the possible `undefined`. Fires under `exactOptionalPropertyTypes:
  true`. Confirmed pre-existing (git status was clean at session start;
  `git diff` empty on the file).
- **Why deferred:** out of scope for P8-02; the file works at runtime
  (find over a fixed template list that always has entries).
- **Recommended resolution:** opportunistic — next Admin/Data touch,
  fix with either an assertion or an explicit fallback. Two-line fix.

## [OPEN] FU-432 — Recipe Detail residual polish: uncovered NO_HOME bullets
- **Raised:** 2026-07-01 (12-June feedback-audit delta).
- **Type:** deferred job (small residual cluster).
- **What:** Recipe Detail feedback had 33 bullets; Cookbook C-4 Chunks 1–10 shipped 17 and PROPOSED 11; **5 remain NO_HOME**. Named: **RD-11 ingredient-notes value** (open design question — do per-ingredient notes surface in cook mode / shopping list / just detail?); RD-18 substitutes-available status (already tracked by [[FU-407]]); plus ~3 other minor items (walk the audit doc for the current list).
- **Why deferred:** small enough that each didn't earn its own home; Cookbook C-4 finished without picking them up.
- **Recommended resolution:** next Cookbook touch — walk the audit's Recipe Detail table for `NO_HOME` rows, close each with a one-line call (kept / dropped / build). RD-11 is the only real design question; the rest are one-shot polish.

## [OPEN] FU-431 — Product History: deeper redesign brief (feature discoverability + desktop drawer pattern)
- **Raised:** 2026-07-01 (12-June feedback-audit delta).
- **Type:** deferred job.
- **What:** Product History has 10 bullets; B9.6 shipped 1 (chart-width fix); 7 are PROPOSED across A1/A6/B9/C-9. **2 remain NO_HOME:** **PH-1 "feature hidden away"** (surface-visibility redesign — how does a user land on Product History without knowing the URL?) and **PH-10 "drawer-style page on desktop"** (design open question). Deeper redesign has no brief. Overlaps with [[FU-227]] resolved "your prices" work but that closed the *stock-item* side, not the *product* side.
- **Why deferred:** briefs went to higher-priority surfaces; Product History is Products-layer, data-gated, so it only matters once real product data is ingested.
- **Recommended resolution:** discussion — decide whether a Product History redesign is worth its own brief (given the Products layer is data-presence-gated) or whether the "your prices" intel layer subsumes the user need. Wait until [[FU-214]] product-surface browser verify surfaces real usage patterns.

## [OPEN] FU-430 — Stocktake mode deeper redesign brief (4 NO_HOME UX items)
- **Raised:** 2026-07-01 (12-June feedback-audit delta).
- **Type:** deferred job.
- **What:** Stocktake mode has 11 feedback bullets; B7/B9 fixes shipped 3; PROPOSED 4; **4 remain NO_HOME:** SK-2 (top queue info feels obvious), SK-4 (keyboard shortcuts on buttons tacky), SK-5 (Skip button as big as others), SK-9 (Skip shortcut should be `4`). Micro-polish + a broader "review rules for queue selection" (SK-6) that was PROPOSED loosely but never briefed. No dedicated Stocktake redesign brief exists.
- **Why deferred:** Stocktake was flagged as "brief deferred" during the Wave-C planning; nothing forced the redesign since the feature works.
- **Recommended resolution:** small `PROPOSAL_STOCKTAKE_MODE.md` brief when Stocktake next opens for change (or opportunistic — the micro items can land inline). Not blocking anything upstream. **Coordinate with [[FU-226]]** — the queue-inclusion-rules assessment there was extended 2026-07-02 with two candidate additions (expiry as an engagement signal, waste as a stocktake resolution + bulk API); those give the brief a stronger anchor than the four SK NO_HOME items alone.

## [OPEN] FU-214 — Products-as-overlay Phase F tail: product-surface browser verify + L197/205/206/223/225 items
- **Raised:** 2026-06-22 (Phase F kickoff — reconstructed 2026-07-01 from `PRODUCTS_OVERLAY_RUNBOOK.md` + 8 worklog references; **the FU entry itself was missing from both ledgers**).
- **Type:** deferred job (multi-item Phase-F tail).
- **What:** Original scope was **product-surface browser verify + build the L205/206 bulk-select variants + decide L197 hard-delete**. Over time it accumulated:
  - **L197** — hard-delete decision for products (still not made).
  - **L205 / L206** — bulk-select variants on product surfaces (not built).
  - **L223** — Price-History hover-bubble dark-mode bug (added 2026-06-22 worklog).
  - **L225** — Price-History box-fit bug (redirected here from FU-227 scope, worklog).
  - Product-surface browser verify (My Products page, Price History page, stock-item Products tab) — waits on a running app.
- **Why deferred:** every item needs a running browser session; bulk-select is real UI work; L197 is a design call.
- **Recommended resolution:** when the next browser-verify session opens **and** the products layer has real data — knock out L223/L225 as bugs, do the browser-verify checklist, then split L197 (design call) and L205/206 (build) into their own FUs if this one gets too heavy. **This FU is the runbook's Phase F blocker** ([`PRODUCTS_OVERLAY_RUNBOOK.md`](docs/04_proposals/PRODUCTS_OVERLAY_RUNBOOK.md) §Status row F). Related: [[FU-227]] (resolved), [[FU-212]] (resolved), [[FU-210]] (resolved).

## [OPEN] FU-429 — DORA_ASSISTANT_ARCHITECTURE_PROPOSAL: not built + collision with in-flight SLM work
- **Raised:** 2026-07-01 (audit follow-up — file was missed on first pass because it lacks the `PROPOSAL_` prefix).
- **Type:** deferred job (design reconciliation + build).
- **What:** `docs/04_proposals/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md` proposes **one capability registry + two renderers** to collapse the three overlapping decision systems ([tools.py](dora_api/features/assistant/tools.py) server-side, [doraIntents.ts](web_app/src/services/doraIntents.ts) client rule engine, [doraContextualActions.ts](web_app/src/services/doraContextualActions.ts) client contextual chips) — none of which agree on what Dora can do. Proposal has been *augmented* multiple times (§2.2.1 mutation-confirmation model, §7 LLM-provider/connectivity) but **the structural refactor was never built** — all three systems still exist, no `CapabilityRegistry` exists anywhere, and `DoraChat.vue`'s missing-ingredients recompute (the Type-A duplication called out in §1) hasn't been deleted. **Collides with the in-flight SLM replacement** (memory `project_dora_slm_assistant`): the SLM direction may supersede parts of this proposal (rule-engine deletion becomes trivial once the SLM is always available), keep others (the capability registry is still the right shape for the SLM to call), or invalidate the whole thing. Nobody has reconciled the two directions.
- **Why deferred:** the SLM work was in-flight when the proposal was drafted; sequencing was never firmed up.
- **Recommended resolution:** **discussion first, not build** — a short session to reconcile: (a) which parts of the proposal survive the SLM pivot, (b) whether the capability registry lands before/after the SLM, (c) fate of the client-side rule engine (`doraIntents.ts`) once the SLM is the default. Outcome should either be a refreshed proposal or an explicit "superseded by SLM work, close" call. Tightly coupled to [[FU-390]] (P5-05 eval suite — tests whichever architecture wins) and [[FU-386]] (dangling client-only `doraContextualActions.ts` handle from the state-ownership plan).

## [OPEN] FU-426 — Waste-page scratch assessment: confirm fully absorbed by C-waste
- **Raised:** 2026-07-01 (docs audit).
- **Type:** finding (audit trail).
- **What:** `docs/99_scratch/WASTE_PAGE_ASSESSMENT_2026-06-24.md` became `PROPOSAL_WASTE_MINIMISATION.md` + `IMPL_PLAN_WASTE_MINIMISATION.md`. Confirm every keep-item from the scratch note is either in the shipped proposal, a landed FU, or explicitly-dropped-with-rationale. If clean, archive the scratch note.
- **Why deferred:** low risk, just a delta-check.
- **Recommended resolution:** opportunistic; also fold the archive step into it (move to `06_legacy_prompt_plans/` or delete).

## [OPEN] FU-425 — Pricing reassessment handoff: confirm fully executed
- **Raised:** 2026-07-01 (docs audit).
- **Type:** finding.
- **What:** `docs/99_scratch/PRICING_SYSTEM_REASSESSMENT_HANDOFF.md` is marked "RATIFIED — READY FOR EXECUTION." Chunks landed via `IMPL_PLAN_YOUR_PRICES` (all 8 built per FU-227). Delta-check that every §6/§6a/§6b decision made it into shipped code + docs, then archive the handoff note.
- **Why deferred:** verification only.
- **Recommended resolution:** opportunistic delta-check; then move the note to `06_legacy_prompt_plans/`.

## [OPEN] FU-424 — Senior review Tier-2 credibility gaps — confirm status
- **Raised:** 2026-07-01 (docs audit).
- **Type:** finding.
- **What:** `docs/99_scratch/SENIOR_REVIEW_2026-06-16.md` Tier-1 ship-blockers were closed (register-first-admin, CSRF, build). Tier-2 "credibility gaps" — ~237 prompt-ID comments in shipped source, half-finished base-component adoption, missing request-level transaction safety, unreachable Postgres posture — were not systematically verified this session. Postgres is closed (FU-045). The other three need a delta pass.
- **Why deferred:** re-audit vs shipped code, not a fix.
- **Recommended resolution:** before any commercialization gate — grep for prompt-ID comments (`P[0-9]-\|C-[0-9]\|B[0-9]`) in shipped source; count non-Base component usage; audit for missing `db.session.commit()` boundaries. Log a proper FU or plan per finding.

## [OPEN] FU-422 — Search: display which products already link to a stock item
- **Raised:** 2026-07-01 (original-spec sweep).
- **Type:** deferred job (dropped intent from original spec).
- **What:** Original spec (`docs/00_original_spec/Unprocessed Ideas (from Google Docs).md`) asked that when searching for products, the UI should visibly mark ones **already linked to a stock item** so the user isn't tempted to re-link. Search now lives in the companion, but the *linkage-display* rule may still belong in Dora (the "Products" tab on a stock item) or become part of the companion's ingestion contract. Decide where it lives.
- **Why deferred:** search moved to companion mid-flight; the rule was never re-homed.
- **Recommended resolution:** during any companion↔Dora ingestion-boundary work — call whether Dora surfaces "already-linked" itself, or the companion queries a Dora endpoint. If the latter, add to the ingestion API's read-side.

## [OPEN] FU-421 — "Remind me to use this" on opened items (use-by reminder)
- **Raised:** 2026-07-01 (original-spec sweep).
- **Type:** deferred job (dropped intent).
- **What:** Original spec asked for a "remind me" affordance when an item is opened (e.g. "I opened this Thai curry paste, remind me in 2 months"). Distinct from expiry (expiry is intrinsic to the product; this is user-set per-open event). Not modelled today — `is_open` + `opened_at` exist, no reminder field/UI.
- **Why deferred:** never made it into the finishing plan.
- **Recommended resolution:** when P8-07 Zero-Input Pantry or the alerts refactor next opens — decide keep/cut; if keep, a `use_by_reminder_at` field on `StockItem` + one alert type + a modal on the "opened" toggle covers it.

## [OPEN] FU-420 — Recipes: non-linked ingredients still fully accounted for (verify model)
- **Raised:** 2026-07-01 (original-spec sweep).
- **Type:** finding (verification).
- **What:** Original spec required that not every recipe ingredient needs to be linked to a stock item, but **all** ingredients are still accounted for in the system (for shopping lists, cook mode, missing-count). Verify: does `RecipeIngredient` support a `stock_item_id`-null row cleanly through shopping-list generation, cook-mode, and `cookable`/`missing_count`? Or are unlinked ingredients silently skipped?
- **Why deferred:** unverified in this audit.
- **Recommended resolution:** during Cookbook C-4 next-touch or opportunistic — trace the null-`stock_item_id` path through `auto_generate.py`, cook-mode finish flow, and cookable derivation; fix any drop-offs.

## [OPEN] FU-419 — Recipes: healthy/unhealthy rating + filter/sort
- **Raised:** 2026-07-01 (original-spec sweep).
- **Type:** deferred job (dropped intent).
- **What:** Original spec proposed a 5-star healthiness rating on recipes with corresponding filter/sort. Never surfaced in Wave-C; nutrition mode does kcal only. Overlaps with the nutrition-off/simple/complex ladder but is a separate axis (perceived healthiness ≠ kcal).
- **Why deferred:** de-emphasised when nutrition was scoped to off+simple.
- **Recommended resolution:** discussion — decide whether this is (a) a distinct healthiness dimension, (b) subsumed by the nutrition-complex mode when eventually built, or (c) dropped. Not now; revisit when nutrition or Cookbook next opens.

## [OPEN] FU-417 — MAGIC_BEHAVIOUR_AUDIT verdicts — confirm each landed
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** finding (delta check).
- **What:** `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` has a "Verdicts (2026-06-28)" section listing keep / clean-up calls on specific magic behaviours. Not all verdicts were verified against shipped code in this session.
- **Why deferred:** delta-check only.
- **Recommended resolution:** opportunistic — walk each verdict, confirm code state, close.

## [OPEN] FU-416 — ORPHANED_FIELDS_AUDIT: confirm all placements acted on
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** finding (delta check).
- **What:** `docs/05_investigations/ORPHANED_FIELDS_AUDIT.md` has a "Recommended placement in the prompt plan" section. Some fields were fixed via later work (e.g. `StockItem.barcode` dropped via P6-02); the full list wasn't re-verified this session.
- **Why deferred:** delta-check only.
- **Recommended resolution:** opportunistic — cross-reference each orphan against current schema; close-or-open per finding.

## [OPEN] FU-415 — FEATURE_CLARIFICATIONS: expiry ↔ open interaction rule
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** deferred job (decision).
- **What:** `docs/05_investigations/FEATURE_CLARIFICATIONS.md §(c)` asks whether expiry and "opened" state affect each other (e.g. opened item → shortened effective expiry). No decision recorded. Currently they're independent.
- **Why deferred:** never resolved.
- **Recommended resolution:** discussion — 5-minute call on the rule (independent / opened shortens expiry by X / prompt for reminder). If a rule is chosen, small code change; if independent, close as decided.

## [OPEN] FU-414 — LOGGING_AND_DATA_LAYOUT investigation: delta-check
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** finding.
- **What:** `docs/05_investigations/LOGGING_AND_DATA_LAYOUT.md` had recommendations around log rolling / `.local` layout. Some landed; comprehensive delta not confirmed.
- **Why deferred:** verification only.
- **Recommended resolution:** opportunistic; when next touching logging config or data-dir layout.

## [OPEN] FU-413 — EMAIL_SETUP_FINDINGS: promote proposal to IMPL
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** deferred job.
- **What:** `docs/05_investigations/EMAIL_SETUP_FINDINGS.md` produced a §"Proposal" section for the forgot-password / email-wiring path. No IMPL plan; nothing shipped. This is the managed-convenience-that-degrades-gracefully case from §7.5 discipline #6.
- **Why deferred:** feature-absent when unconfigured is currently acceptable; only becomes a blocker at commercialization.
- **Recommended resolution:** before Phase 4 / any hosted deployment — draft `IMPL_PLAN_EMAIL_SETUP.md`, wire SMTP config through `AppSetting` with a "degrades to feature-absent" default.

## [OPEN] FU-412 — COMMERCIALIZATION_REPORT: dormant, not yet actioned
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** deferred job.
- **What:** `docs/05_investigations/COMMERCIALIZATION_REPORT.md` is a Phase 4 planning input. Not translated into a plan or prompts.
- **Why deferred:** Phase 4 territory.
- **Recommended resolution:** at Phase 4 kick-off — read the report top-to-bottom, spawn per-recommendation FUs / plans.

## [OPEN] FU-410 — MULTI_USER_READINESS §5 open questions
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** deferred job.
- **What:** `docs/05_investigations/MULTI_USER_READINESS.md §5` lists open questions gating Phase 4 tenancy work.
- **Why deferred:** Phase 4.
- **Recommended resolution:** at Phase 4 tenancy kick-off; part of P7-A1 / P7-A2 (see [[FU-406]] / [[FU-407]]).

## [OPEN] FU-409 — AUTH_ASSISTANT_SECURITY_FINDINGS: delta re-audit before commercialization
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** finding.
- **What:** `docs/05_investigations/AUTH_ASSISTANT_SECURITY_FINDINGS.md` originally listed CSRF / email-change / register-first-admin issues. Most were resolved (per resolved-FUs trail). A comprehensive item-by-item confirmation vs shipped code was not re-run.
- **Why deferred:** the delta itself is the work.
- **Recommended resolution:** before any public deployment — walk every finding, tick "fixed" or reopen. Overlaps with [[FU-424]] (senior-review credibility gaps).

## [OPEN] FU-408 — INV-8 substitute swap: cross-ref inside stock-item detail is stale
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** finding.
- **What:** `IMPL_PLAN_STOCK_ITEM_DETAIL.md` line ~83 cross-refs INV-8's swap rework as "not built here." INV-8's target surface (Shop Mode) no longer exists as a separate page — merged into ShoppingListDetail per UX v2. The cross-ref is stale until [[FU-407]] re-scopes the rework.
- **Why deferred:** blocked by [[FU-407]].
- **Recommended resolution:** update the cross-ref when [[FU-407]] resolves; same session.

## [OPEN] FU-407 — INV-8 substitute swap rework: re-scope for merged Shop Mode
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** finding (design call).
- **What:** `docs/05_investigations/SUBSTITUTE_SWAP_ASSESSMENT.md` recommended surfacing the stock-item substitute swap **inside Shop Mode + disambiguating the two "Substitute" labels** (line stock-item swap vs merchant-offer swap). Shop Mode has since been merged into ShoppingListDetail (UX v2); the recommendation is stale as written. Currently the only surface is a buried "Swap … with" line-menu action at [ShoppingListDetail.vue:1890](web_app/src/pages/ShoppingListDetail.vue:1890).
- **Why deferred:** the target surface changed mid-flight; nobody re-scoped the fix.
- **Recommended resolution:** short design brief — decide (a) do the rework against the merged surface (a shopping-mode-active affordance surfaced when a line is marked out-of-stock), or (b) cut the list-level swap outright and rely on cook-mode swaps + manual edit. Address the two-"Substitute" collision either way.

## [OPEN] FU-406 — P7-10 Launch readiness
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4 gate).
- **What:** `docs/06_legacy_prompt_plans/PROMPT_PLAN_PART_7_COMMERCIALIZATION.md §P7-10` — final launch-readiness checklist (marketing, legal, incident channels, escalation, on-call). Nothing done.
- **Why deferred:** last-mile.
- **Recommended resolution:** at Phase 4 finish.

## [OPEN] FU-405 — P7-09 Ops (observability, CI/CD deploy, staging, backups)
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-09 — production ops. CI is deliberately disabled in this repo (`.github/workflows/*.yml` commented out to preserve GH free-tier — see memory `feedback_ci_disabled_policy`). Observability, staging, backups all unplanned. **Do not silently re-enable CI as part of this** — separate call.
- **Why deferred:** Phase 4 + CI-cost policy.
- **Recommended resolution:** Phase 4 — pair with billing (P7-06) so ops cost lands with revenue.

## [OPEN] FU-404 — P7-08 Compliance (privacy policy, DSAR, deletion, security headers)
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-08 — full compliance surface. Partial: some security-headers work has landed; the privacy-policy hooks + full data-export/deletion (DSAR) contract not confirmed. Overlaps with [[FU-401]] (P5-02 Privacy).
- **Why deferred:** Phase 4.
- **Recommended resolution:** Phase 4 — merge P5-02 + P7-08 into one compliance work-unit.

## [OPEN] FU-403 — P7-07 Plan gating + usage limits
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-07 — feature/usage limits gated by plan tier once billing is in.
- **Why deferred:** Phase 4, gated by [[FU-402]] Stripe billing.
- **Recommended resolution:** immediately after Stripe lands.

## [OPEN] FU-402 — P7-06 Stripe billing
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-06 — Stripe integration for the SaaS Path A + managed Path B.
- **Why deferred:** Phase 4; only after tenancy ([[FU-400]] / [[FU-401]]).
- **Recommended resolution:** Phase 4.

## [OPEN] FU-401 — P7-A2 Repository-enforced tenant isolation + leak tests
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4, Path A).
- **What:** P7-A2 — tenant scoping enforced at the repository layer + cross-tenant leak tests. §7.5 discipline #1 keeps this a one-layer change when the time comes.
- **Why deferred:** Path A is Phase 4.
- **Recommended resolution:** with [[FU-400]] (Households-as-tenant) as one work-unit.

## [OPEN] FU-400 — P7-A1 Households-as-tenant + admin → owner / platform-admin split
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4, Path A).
- **What:** P7-A1 — introduce households as the tenancy boundary; split "admin" into household-owner and platform-admin. Gated by [[FU-410]] (MULTI_USER_READINESS §5).
- **Why deferred:** Phase 4.
- **Recommended resolution:** first Path-A work item once Phase 4 opens.

## [OPEN] FU-399 — P7-B1 Provisioning control plane
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4, Path B).
- **What:** P7-B1 — automated provisioning for managed single-tenant instances (Path B). Same artifact, different env per §7.5 discipline #3.
- **Why deferred:** Phase 4.
- **Recommended resolution:** first Path-B work item when Phase 4 opens; can precede Path-A work.

## [OPEN] FU-398 — P7-05 Redis + object storage for images
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-05 — Redis for sessions/cache/rate-limit + object storage (S3-ish) for uploaded images. Managed-convenience per §7.5 #6 — must degrade gracefully to "feature absent" (in-memory / local disk) on self-host.
- **Why deferred:** Phase 4.
- **Recommended resolution:** with P7-04 as the "production stack" work-unit.

## [OPEN] FU-397 — P7-04 Production WSGI + web/worker split
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-04 — replace dev server with gunicorn/uwsgi, split web vs worker. Env-driven per §7.5 discipline #3.
- **Why deferred:** Phase 4.
- **Recommended resolution:** paired with [[FU-398]] Redis + [[FU-405]] Ops as the production-stack work-unit.

## [OPEN] FU-395 — P5-11 Production readiness review
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4 gate).
- **What:** P5-11 — comprehensive pre-launch review sweep.
- **Why deferred:** Phase 4.
- **Recommended resolution:** at Phase 4 near-completion, before [[FU-406]] launch readiness.

## [OPEN] FU-394 — P5-10 Merchant data quality & support bundle: confirm companion-scope only
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** finding.
- **What:** P5-10 — merchant data quality is now companion-scope per Decision 1. Confirm nothing in the P5-10 spec landed in Dora-core, and formally mark the P5-10 prompt as "moved to companion project."
- **Why deferred:** scoping-only.
- **Recommended resolution:** doc edit — add a "moved to companion" banner to P5-10 in the legacy plan file; close.

## [OPEN] FU-393 — P5-08 Data-model sanity review sweep
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-08 — comprehensive data-model sanity sweep. `ORPHANED_FIELDS_AUDIT` covered one slice; nullability audit, FK-consistency, index coverage, dead columns — not done as a single pass.
- **Why deferred:** hasn't been forced.
- **Recommended resolution:** opportunistic sweeps as touched (partial credit for [[FU-416]]); a single dedicated pass would be a good pre-Phase-4 gate.

## [OPEN] FU-392 — P5-07 Demo & sellable showcase mode
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-07 — seed a "showcase" install with representative data + a toggleable demo mode for prospects. Seed system exists; showcase toggle + curated dataset don't.
- **Why deferred:** Phase 4-ish; needed for sales conversations.
- **Recommended resolution:** with commercialization prep (Phase 4 opening).

## [OPEN] FU-391 — P5-06 first-week experience (post-onboarding nudges)
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-06 — first-week experience: gentle nudges to complete profile, add first recipe, run first stocktake, etc. First-day onboarding shipped (C-5); first-week nudges not built. Overlaps with [[FU-352]] (P6-12 daily briefing card).
- **Why deferred:** waiting on the alerts/dashboard-card model to firm up.
- **Recommended resolution:** fold into the P8-08 Dora Score card brief when [[FU-352]] opens — the same launchpad-alerts model fits first-week nudges.

## [OPEN] FU-390 — P5-05 Dora AI reliability + eval suite
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-05 — reliability tests + evaluation suite for the assistant. Assistant is currently being replaced by a local SLM (per memory `project_dora_slm_assistant`). Eval suite needs to be built against the SLM rather than the rule-based intent path.
- **Why deferred:** SLM work in-flight; eval-first would test the wrong subject.
- **Recommended resolution:** as the SLM lands — the eval suite is the acceptance gate. Reference the SLM work when picked up.

## [OPEN] FU-389 — P5-04 Mobile / PWA field test
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-04 — real-device mobile / PWA testing pass. Overlaps with [[FU-411]] platform builds + P8-10 native.
- **Why deferred:** Phase 3-adjacent.
- **Recommended resolution:** fold into the P8-10 native-app brief; a device-lab pass is a natural gate before deciding native vs PWA-only.

## [OPEN] FU-388 — P5-03 Performance & scale pass
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-03 — comprehensive perf sweep (query N+1s, bundle size, load-tests). Only `STOCK_OVERVIEW_PERF` investigation touched a slice. No app-wide pass.
- **Why deferred:** hasn't been forced by user pain.
- **Recommended resolution:** pre-Phase-4 gate — do one comprehensive pass with real seed data at pantry size 500+ items, catch N+1s + big-query issues before they hit paying users.

## [OPEN] FU-387 — P5-01 Security & privacy hardening bundle sweep
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-01 — comprehensive security/privacy hardening sweep. Auth findings (CSRF, register-first-admin, email-change) resolved per resolved-FUs. The full P5-01 bundle (security headers, rate-limits, secrets management, dependency audit) not executed as a single sweep.
- **Why deferred:** slices landed opportunistically.
- **Recommended resolution:** pre-Phase-4 gate — one dedicated sweep before any public deploy. Overlaps with [[FU-409]] auth findings re-audit + [[FU-424]] senior-review Tier-2.

## [OPEN] FU-386 — IMPL_PLAN_STATE_OWNERSHIP: dangling client-only `doraContextualActions.ts`
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** finding.
- **What:** `IMPL_PLAN_STATE_OWNERSHIP.md:25` flags a client-side `doraContextualActions.ts` handle whose server-side counterpart was **not implemented** — a dangling contract. Either build the server side or delete the client handle.
- **Why deferred:** noted in the plan doc, never actioned.
- **Recommended resolution:** when the assistant/SLM work next touches contextual actions — decide direction + close.

## [OPEN] FU-385 — Dashboard: DashboardCard extraction + "new low" signal
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `IMPL_PLAN_DASHBOARD_REBUILD.md:263` — DashboardCard extraction was **not** done; zones ship via CSS instead of a shared card component. `:320` — the "new low" server-side signal was **not built** (needed for the dashboard's "just went low" surface).
- **Why deferred:** dashboard rebuild landed without them; not blocking.
- **Recommended resolution:** when Dashboard next opens for change — extract the shared card component (R-002 componentisation) and add the server-side new-low signal. Feeds into [[FU-352]] Dora Score card too.

## [OPEN] FU-384 — StockOverview collapse/expand button (deferred from C-cross)
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `IMPL_PLAN_CONFIG_AND_OPTINS.md:320` — the StockOverview collapse/expand button was explicitly **NOT built** in C-cross; row-geometry deferred to the next C-1 chunk which never happened.
- **Why deferred:** owned by C-1 not C-cross; C-1 didn't include it.
- **Recommended resolution:** next C-1 (Stock Overview) touch — decide keep/cut; if keep, build inline with any other row-geometry change.

## [OPEN] FU-383 — Onboarding: "preferred stores/merchants" step not built
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_ONBOARDING.md:268` — the preferred-merchants step was **not built** ("same uncertain bucket as preferred-*product* removal, FU-180"). Onboarding currently skips it.
- **Why deferred:** merchants layer is companion-scope and its onboarding value was unclear.
- **Recommended resolution:** discussion — decide whether the everyday user needs a "preferred store" concept for `usual_store_id` (which does exist server-side). If yes, small onboarding step + settings mirror; if no, close as decided.

## [OPEN] FU-382 — PROPOSAL_SHOPPING_LIST_UX_V2 §11 open questions
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** finding (unresolved decisions).
- **What:** V2 shipped but §11 open questions were not all closed in-doc. Read the section and either resolve each against the shipped behaviour or turn each into its own FU.
- **Why deferred:** end-of-implementation admin miss.
- **Recommended resolution:** doc-only pass — walk §11, mark each RESOLVED (with the shipped behaviour) or spawn a per-question FU.

## [OPEN] FU-381 — PROPOSAL_COOK_MODE §5 open decisions
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_COOK_MODE.md:166` — open decisions: ticking removal, sub-step model, quantity-unit inclusion list. Cook mode C-3 shipped but the doc's open-decision block was not closed.
- **Why deferred:** built without fully resolving the doc's open calls.
- **Recommended resolution:** doc-only walk — mark each against shipped behaviour or spawn per-question FUs.

## [OPEN] FU-380 — PROPOSAL_CART_BUTTON §7 open decisions + swipe-right + success animation
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_CART_BUTTON.md:220` (§7 open decisions), plus §7.7 swipe-right affordance and success animation added as new open decisions. Cart button C-7 shipped; not all open decisions closed.
- **Why deferred:** built without fully resolving.
- **Recommended resolution:** walk §7 + §7.7 vs shipped, close or spawn.

## [OPEN] FU-379 — PROPOSAL_ALERTS §7 open decisions + still-open deferred cluster
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_ALERTS.md:326` §7 open decisions + `:341` "still open (deferred to their phase, not blocking)" cluster. C-9 Phase A shipped; the deferred cluster survives.
- **Why deferred:** flagged not-blocking.
- **Recommended resolution:** revisit when alerts next opens (or fold into [[FU-352]] Dora Score card if the alerts-as-launchpads reframing subsumes them).

## [OPEN] FU-378 — PROPOSAL_STOCK_OVERVIEW §2.3 detail navigation model + §7 open decisions
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job (design call).
- **What:** `PROPOSAL_STOCK_OVERVIEW.md:84` — §2.3 is flagged as **"the #1 open decision"** (detail navigation model — desktop drawer vs mobile full-page, row-tap vs button-tap miss risk, L68/L71). §7 has additional open decisions. C-1 shipped but this call was not closed.
- **Why deferred:** shipped without resolving the top-of-doc open decision.
- **Recommended resolution:** discussion — resolve §2.3 vs shipped behaviour + user preference, then walk §7. Prerequisite for [[FU-384]].

## [OPEN] FU-377 — PROPOSAL_COOKBOOK open decisions (cuisine-vs-category, versions UX, multi-part model)
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_COOKBOOK.md` has three named open decisions: cuisine-vs-category fate, versions UX (full snapshot vs branchable), multi-part model A vs B. C-4 shipped chunks 1–10; these calls were not all closed.
- **Why deferred:** shipped what was clear, deferred what wasn't.
- **Recommended resolution:** doc walk vs shipped state; the cuisine-vs-category call cascades into [[FU-XXX]] C-cross taxonomy editors ([[FU-372]]).

## [OPEN] FU-376 — PROPOSAL_PRODUCTS_AS_OVERLAY §7 open decisions + GAP bucket
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_PRODUCTS_AS_OVERLAY.md:262` §7 build-time open decisions + `:391` "GAP = small, not yet built" bucket. IMPL landed but these residual bits were not swept.
- **Why deferred:** small-slice residuals.
- **Recommended resolution:** doc walk vs shipped; each GAP either becomes its own FU or gets closed with a state note.

## [OPEN] FU-375 — PROPOSAL_MEAL_PLANS §11 smaller secondary open decisions
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_MEAL_PLANS.md:494` — §11 "smaller secondary open decisions" cluster. Meal-plans rebuild has an active IMPL (`IMPL_PLAN_MEAL_PLANS_REBUILD.md`); §11 not fully resolved.
- **Why deferred:** secondary, not blocking the rebuild.
- **Recommended resolution:** roll into the meal-plans rebuild close-gate — walk §11 vs shipped, close each.

## [OPEN] FU-374 — PROPOSAL_SIMPLE_MODE: sweep non-spine parts (spine superseded)
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** finding (doc drift).
- **What:** `PROPOSAL_SIMPLE_MODE.md` marked spine-superseded 2026-06-17 by PRODUCTS_AS_OVERLAY. The doc's non-spine parts (money opt-in framing, some UI notes) were not confirmed re-homed elsewhere.
- **Why deferred:** doc admin.
- **Recommended resolution:** doc walk — mark every non-spine section either "re-homed at X" or "dropped by pivot"; close.

## [OPEN] FU-373 — PROPOSAL_BARCODE_SCANNING deferred slices (register-against-product + scan-unknown)
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_BARCODE_SCANNING.md` cleanup slice landed; **register-against-product UI + scan-unknown rework** deferred to Phase 2 (ingestion). Ingestion has landed but these barcode slices did not follow through. §6 "Scan tab under QR codes placement" also open.
- **Why deferred:** waited on ingestion; ingestion landed without pulling these along.
- **Recommended resolution:** next barcode-touch — build the register-against-product UI (unknown EAN → offer to link to an existing Product) + scan-unknown rework. Resolve §6 placement while there.

## [OPEN] FU-372 — PROPOSAL_COOKBOOK_CARD_REVISION: not built
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** Design-only sequel to Cookbook §2.10. Two open-decision sections (§3, §5). No IMPL plan.
- **Why deferred:** Cookbook C-4 shipped without this revision.
- **Recommended resolution:** when Cookbook next opens for change — resolve open decisions + spawn `IMPL_PLAN_COOKBOOK_CARD_REVISION.md` if kept.

## [OPEN] FU-371 — PROPOSAL_TEST_SUITE_IMPROVEMENTS: not built
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** Draft proposal, no IMPL, nothing shipped.
- **Why deferred:** infra investment; hasn't been forced.
- **Recommended resolution:** pre-Phase-4 gate; better test suite is a commercialization prerequisite for confident refactors.

## [OPEN] FU-370 — PROPOSAL_SUPPORT_CHANNEL: not built
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** Draft proposal for a user support channel; no IMPL, nothing shipped.
- **Why deferred:** commercialization-adjacent; no users to support.
- **Recommended resolution:** Phase 4 alongside [[FU-402]] Stripe + [[FU-404]] compliance.

## [OPEN] FU-369 — PROPOSAL_RECIPE_IMAGE_STEPS: not built (draft for co-design)
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** Draft 2026-06-25 with 3 open decisions (peer switch across payload types §5.1; vertical vs swipe carousel §5.2; client-side resize target + image cap §5.3). No IMPL.
- **Why deferred:** waiting on co-design.
- **Recommended resolution:** 30-minute co-design session on the 3 open decisions, then `IMPL_PLAN_RECIPE_IMAGE_STEPS.md`.

## [OPEN] FU-368 — PROPOSAL_LOCALE_I18N: not built
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** Draft proposal; §4 open decisions (`:140`); no IMPL. Currency + locale currently AUD-hardcoded in places.
- **Why deferred:** single-locale is fine while personal-use.
- **Recommended resolution:** before commercialization (Phase 4-adjacent) — many customers won't be AU-based. Overlaps with [[FU-402]] Stripe (multi-currency).

## [OPEN] FU-367 — PROPOSAL_HELP_OVERLAY: not built
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** Proposal for a contextual help overlay; §4 open decisions (`:146`); no IMPL. Distinct from [[FU-366]] A-4 Help *content* — this is the UI shell.
- **Why deferred:** noted but not scheduled.
- **Recommended resolution:** discussion — decide whether overlay + content are one work-unit or two; if two, sequence overlay before content so content has a place to render into.

## [OPEN] FU-366 — Deferred surfaces: Reports, Settings shell, Mobile view
- **Raised:** 2026-07-01 (Wave-C audit).
- **Type:** deferred job.
- **What:** `C_big_rock_design_briefs.md` "do not redesign yet" list. Dashboard has been pulled forward and shipped. **Reports, Settings shell, Mobile view** remain officially deferred — no briefs. Feedback for Reports is empty; Settings has some deferred bullets (see [[FU-365]] A-5); Mobile view has no direct feedback.
- **Why deferred:** deliberately parked.
- **Recommended resolution:** discussion at some future point — decide whether each stays parked forever or gets a brief. Not on a critical path.

## [OPEN] FU-365 — INV-10 Essential flag: row-level quick-toggle in Stock Overview
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** deferred job.
- **What:** `ESSENTIAL_FLAG_FINDINGS.md` rec #1 (rename to "Essential") is done in detail. **Rec #2 (row-level quick-toggle in stock-overview row context menu or multi-select) is NOT built.** Only Reports has bulk `markAllEssential`.
- **Why deferred:** rec #1 alone resolved the "can't find it" complaint; #2 dropped off.
- **Recommended resolution:** next C-1 (Stock Overview) touch — add "Mark essential" to the row three-dot menu + the multi-select bulk action bar. Small change.

## [OPEN] FU-364 — Wave-C briefs: unresolved open-decision blocks across shipped proposals
- **Raised:** 2026-07-01 (proposals audit meta-item).
- **Type:** finding (meta).
- **What:** Multiple Wave-C proposals shipped without closing their in-doc "Open decisions" sections. Individual FUs exist for each ([[FU-378]] Stock Overview, [[FU-377]] Cookbook, [[FU-379]] Alerts, [[FU-375]] Meal Plans §11, [[FU-380]] Cart Button, [[FU-381]] Cook Mode, [[FU-382]] Shopping List V2). This meta-FU exists so the pattern is visible: **going forward, add an "open decisions closed / spawned as FUs" step to every proposal close-gate**.
- **Why deferred:** process gap surfaced only in aggregate.
- **Recommended resolution:** adopt the close-gate step in CLAUDE.md's "on ending a work unit" section next time it's edited. Meanwhile, individual per-proposal FUs (above) carry the actual delta work.

## [OPEN] FU-363 — Cross-cutting / niche feedback (Bucket C in COVERAGE_GAPS)
- **Raised:** 2026-07-01 (COVERAGE_GAPS sweep).
- **Type:** deferred job (bundle — 8 sub-items).
- **What:** `COVERAGE_GAPS.md` Bucket C cross-cutting items with no per-surface home:
  1. Full systems QA test doc (final regression walkthrough of every feature). User wants done LAST to capture the final product.
  2. Usage analytics / telemetry — "I'd like to know how people are using my app." Privacy-conscious (Charter P8).
  3. UI uniqueness / polish design pass — "looks just okay, not polished/unique."
  4. Push notifications between users (share a shopping list via notify).
  5. Kivy P2P sync branch — decide whether the user's prior experiment has a home here.
  6. Main menu bottom border — micro polish.
  7. Real ALDI / IGA logos — asset request.
  8. General UI consistency — cross-cutting.
- **Why deferred:** no per-surface home; several are Phase 3/4-timed or design-only.
- **Recommended resolution:** split into per-item FUs *only when picked up*. Items 1 (QA test doc) and 3 (polish pass) are natural Phase 4 gates; item 2 (telemetry) is a Charter P8 decision + build; item 4 (push notifications) is a Phase 3-ish feature; items 5–8 are one-shots.

## [OPEN] FU-362 — A-5 Settings: theme *type* separated from theme *identity*
- **Raised:** 2026-07-01 (COVERAGE_GAPS sweep).
- **Type:** deferred job.
- **What:** `COVERAGE_GAPS.md` A-5 — theme **type** (system / light / dark) should be separated from theme **identity** (pesto, lemon, …) — two dropdowns, not coloured light/dark buttons on each theme card.
- **Why deferred:** Settings shell is a deferred surface ([[FU-366]]).
- **Recommended resolution:** fold into any Settings polish pass — small self-contained change; can precede the full Settings shell redesign.

## [OPEN] FU-361 — A-4 Help content overhaul
- **Raised:** 2026-07-01 (COVERAGE_GAPS sweep).
- **Type:** deferred job (content task).
- **What:** `COVERAGE_GAPS.md` A-4 — 5 feedback bullets all about **content**: detailed per-feature help, guides, FAQ, easy navigability, UI screenshots / diagrams. No brief.
- **Why deferred:** content task typically deferred to post-launch.
- **Recommended resolution:** discussion — decide whether it lives as a dedicated `HELP_CONTENT_PLAN.md` proposal or folds into the existing HelpPage work. Distinct from [[FU-367]] (Help overlay shell).

## [OPEN] FU-360 — A-3 DORA BOT (assistant chat) polish
- **Raised:** 2026-07-01 (COVERAGE_GAPS sweep).
- **Type:** deferred job (bundle — 6 sub-items).
- **What:** `COVERAGE_GAPS.md` A-3 open bullets:
  1. Text size not honouring user settings (bug).
  2. Basic/AI chip squished/small.
  3. Make basic/AI chip a toggle slider (slanted thick, glow on slide).
  4. DS4 animation flashing on hover — regression to investigate.
  5. Don't show "Hi I'm Dora, click me…" every login (once-per-user acknowledge).
  6. Turn the bot off completely in settings.
- **Why deferred:** scattered across owners; no bundle owner.
- **Recommended resolution:** fold into the DORA_ASSISTANT_ARCHITECTURE polish appendix or a small Wave-C brief. Bug items (1, 4) are triage-first — can fix inline.

## [OPEN] FU-359 — A-2 DATA page redesign
- **Raised:** 2026-07-01 (COVERAGE_GAPS sweep).
- **Type:** deferred job (bundle — 7 sub-items).
- **What:** `COVERAGE_GAPS.md` A-2 open bullets. No dedicated brief. Items: (1) move under Settings → "My Data" (not top-level); (2) multiple export formats (json, csv, …); (3) page formatting overhaul — margins, alignment, headings, font/type; (4) card + checkbox layout; (5) drop the breadcrumb fluff; (6) schema-driven import templates (partially addressed by FU-343/344 but still open); (7) Export & Print tab utility — drop or rework; plus decide whether the optional/collapsed section should be the main view. Barcode-tab items are already covered.
- **Why deferred:** no owner brief.
- **Recommended resolution:** new Wave-C brief `C-DATA — Data Management redesign`. Sequence early if Settings shell ([[FU-366]]) is also opened, since #1 depends on it.

## [OPEN] FU-356 — Gamification: revisit the "someday-list" verdict as a discussion task
- **Raised:** 2026-07-01 (§7 decisions audit).
- **Type:** deferred job (discussion / re-decision — not an implementation).
- **What:** `RECONCILED_FINISHING_PLAN.md` §7 Decision 3c parked **gamification** (rewards / streaks / notify-users) on the someday-list — "captured, not built during finishing." That was a 2026-06-04 call made before P8-08 Dora Score and the C-waste de-emphasis. Worth a fresh discussion pass to decide whether any gamification element (streaks on the Score card, "N shops on budget in a row", waste-free week, first-time badges) is actually free-standing content once the P8-08 card exists — or whether it stays parked. Do NOT design or build off this FU; the deliverable is a **decision** (keep-parked / promote a specific slice into a brief / kill outright).
- **Why deferred:** the original call is defensible but was made without knowing what the Score card would look like; re-checking is cheap.
- **Recommended resolution:** later, during the P8-08 / FU-352 combined Dora Score brief — take 10 minutes at the top of that session to co-decide gamification's fate against the just-designed card, then update `RECONCILED_FINISHING_PLAN.md` §7 Decision 3c accordingly (either "still someday" with a date, or "promoted, see brief §X"). If P8-08 slips, the discussion can happen standalone whenever the user wants — it's not on a critical path. Related: [[FU-352]].

## [OPEN] FU-355 — Wire `clearAllListState()` into sign-out
- **Raised:** 2026-07-01 (A8 §3 landing).
- **Type:** leftover (nice-to-have on top of R-026).
- **What:** `useListState`'s module-level Map persists across sign-out
  because `authStore.signOut` currently does a soft router push rather
  than a full reload. On a shared device the next user could inherit
  the previous session's filter shape on any migrated list page. The
  fallout is minor (filters are per-page UI knobs, not sensitive
  data), but the honest close is to call `clearAllListState()` in the
  sign-out handler (or force a `window.location.reload()`, which some
  auth flows already do).
- **Why deferred:** cross-cutting hook into the auth store — not part
  of the A8 §3 shape and worth its own tiny prompt.
- **Recommended resolution:** opportunistic — bundle with the next
  auth-store touch, or when a shared-device concern surfaces.

## [OPEN] FU-354 — Migrate remaining list pages to `useListState` (R-026 rollout)
- **Raised:** 2026-07-01 (A8 §3 landing).
- **Type:** deferred job.
- **What:** R-026 (nav-state via `useListState`) was applied to
  `StockOverview` (via `useStockFilters`), `RecipesOverview`, and
  `MyProductsPage` as the canonical pattern. Remaining list surfaces
  still lose their filter/search/sort/scroll on navigate-back:
  `MealPlansOverview.vue`, `MealPlanTemplatesPage.vue`,
  `ShoppingListsOverview.vue`, `ShoppingListDetail.vue` (line
  filters + sort), `StocktakePage.vue` (if it grows filters),
  `settings/UsersAdminSettings.vue`, `settings/StoresSettings.vue`,
  `settings/ApiAccessSettings.vue`, and any surface added since. Each
  is a small wrap-in-`useListState` edit; nothing structural.
- **Why deferred:** scope discipline — Phase 0 closed the policy +
  the primitive + three canonical pages, not a repo-wide sweep.
- **Recommended resolution:** opportunistic — migrate a page the
  next time you're editing it for another reason. New list pages
  land with `useListState` from the outset (R-026 violation signal).

## [OPEN] FU-353 — Rename local checkout dir + GitHub repo to `DashyDora`
- **Raised:** 2026-07-01 (P8-01 landing).
- **Type:** leftover (external identifier).
- **What:** P8-01 renamed every in-repo identifier from
  Discount Dora / DiscountDora → Dashy Dora / DashyDora (UI copy,
  package name `dashy-dora`, PWA `appId`, container name
  `dashy_dora`, User-Agents, README + docs, docstrings, badges,
  release-check URL). Two external identifiers can't be flipped
  from inside the repo:
  1. The GitHub repository itself — still `BenTalese/DiscountDora`.
     Until the user renames it, the README badges (shields.io
     endpoints), `_GITHUB_RELEASE_URL` in
     [`dora_api/features/help/get_version.py`](dora_api/features/help/get_version.py),
     and the clone URL in the README all point at
     `BenTalese/DashyDora` and will 404. GitHub auto-redirects the
     old name for a while after rename, so flipping first is safe.
  2. The local checkout directory (`~/Repos/DiscountDora/`) —
     cosmetic; agent CLAUDE.md paths, Codex session paths, and
     shell muscle memory all still work but read wrong.
- **Why deferred:** the user has to run `gh repo rename` (or the web
  UI) and `mv ~/Repos/DiscountDora ~/Repos/DashyDora` — not
  something the agent should do unprompted.
- **Recommended resolution:** now (opportunistic — do it whenever
  the user has 30 seconds). After the GitHub rename, hit the Help
  → About panel in the SPA to confirm the release check resolves
  and the "newer version" banner logic still works. Once done,
  flip this to `[RESOLVED]`.

## [OPEN] FU-352 — P6-12 daily briefing → fold into a "Dora Score" dashboard card (with P8-07/P8-08)
- **Raised:** 2026-07-01 (Phase 1/2 audit vs code — nothing built for P6-12).
- **Type:** deferred job (Phase 1 loop item, un-started).
- **What:** The legacy plan's **P6-12 (proactive daily briefing + alerts-as-launchpads)** has no code — no briefing module server-side, no dashboard section, no follow-up trail. Rather than build it as its own surface, **combine it with the Phase 3 "Dora Score" (P8-08)** and roll both into a single dashboard card: the score is the headline number, the briefing bullets underneath are the "why" (top alerts, likely-due items, over-budget flag, no-planned-meals-next-week, etc.), each bullet is a launchpad link into the relevant surface. One card, one card only — replaces (does not add to) whatever alerts/summary blocks the dashboard has today.
- **Why deferred:** cross-phase design call — the sensible framing didn't exist until P8-08 was on the table.
- **Update 2026-07-04:** **P8-08 partially covered.** The Dora Score card shipped today with a per-component "why" model — every one of the five signals renders its own server-authored reason sentence + a launchpad link to the remediating feature (waste tab, budget prefs, expiring stock, shopping lists, stocktake). That's *the score portion* of this FU. What's still open: the *briefing bullets beyond the 5 signals* (no-planned-meals-next-week, top-active-alerts summary, likely-due items) and the "replaces the existing attention card" framing — my P8-08 sits alongside the existing "Needs your attention" card rather than replacing it. Decide separately whether to (a) leave alerts + Dora Score as two coexisting surfaces, or (b) fold alerts into Dora Score as further "briefing rows" beneath the 5 signals.
- **Recommended resolution:** **when Dashboard next opens** — reassess whether the coexisting-card model feels right in real use. If not, spin a follow-up FU to fold alerts into a "Briefing rows" section on the Dora Score card. Feeder data (suggestions, alerts, budget) is all wired; the composition is presentation-only.

## [OPEN] FU-351 — P6-10 "self-drafting weekly shop": plumbing is built, one-click entry point is missing
- **Raised:** 2026-07-01 (Phase 1/2 audit vs code).
- **Type:** deferred job (partial coverage — needs the shell on top).
- **What:** The multi-source builder [`auto_generate.py`](dora_api/features/shopping_lists/auto_generate.py) already dedupes across `auto_recipe > auto_meal_plan > auto_flagged > auto_essential > auto_low_stock > auto_frequently_added` — that **is** the self-drafting engine P6-10 called for. What's missing is the P6-10 UX framing: a prominent "Draft my shop" one-click entry point that pre-selects sensible defaults (probably meal-plan-for-the-week + low-stock + flagged), shows the reason chip per line ("usually rebuy ~every 12 days"), and lands the user in a DRAFT list ready to edit before starting shopping. Legacy prompt in `docs/06_legacy_prompt_plans/PROMPT_PLAN_PART_6_POLISH.md:646`.
- **Why deferred:** shipping X5 (`auto_generate`) satisfied the mechanics; the one-click "Draft my shop" surface was never built and no one flagged the gap.
- **Recommended resolution:** later, during Phase 1 mop-up before Phase 3 opens (P8-07 Zero-Input Pantry directly depends on P6-10 per §5). Small design brief first — decide entry-point location (Dashboard? Shopping Lists overview? both?), default source set, and whether the reason chip is new UI or reuses the existing `added_via` chip. Then a bounded implementation prompt on top of `auto_generate.py`.

## [OPEN] FU-350 — Import templates: example row is positional, silently drifts on schema change
- **Raised:** 2026-07-01 (post-FU-343 self-review).
- **Type:** finding (drift risk).
- **What:** In
  [`import_spreadsheet.py`](dora_api/features/data/import_spreadsheet.py)
  the `ImportTemplate.example` field is a positional `tuple[str, ...]`
  hand-crafted to match `TARGET_FIELDS`. Add a seventh target field and
  the CSV emits 7 headers + 6 example cells — misaligned in a very
  confusing way (`expiry`'s example lands under `is_essential`, etc.).
  Nothing fails; nothing warns.
- **Why deferred:** wasn't in scope for FU-343 shipping; noticed during
  the "is this future-proof?" review after the fact.
- **Recommended resolution:** change `example` to
  `dict[str, str]` keyed by field name. Reordering `TARGET_FIELDS` then
  becomes safe (the CSV column order is driven by `headers`; example
  values follow the key). Add module-load assertions:
  `assert set(t.example.keys()) <= set(t.headers)` and
  `assert set(t.headers) == set(TARGET_FIELDS)` so drift fails at
  boot instead of at user download time. Should also add an assertion
  that every ImportTemplate section is a registered target the commit
  handler actually knows how to process (today: single section, so
  trivially true — but wire the check now so future sections can't
  silently ship broken templates). Small (~30-line change).

## [OPEN] FU-349 — Import templates: example values reference seed-data strings, not the install's actual reference data
- **Raised:** 2026-07-01 (post-FU-343 self-review).
- **Type:** finding (correctness on customised installs).
- **What:** The stock_items template's example row is
  `("Rice", "In stock", "Pantry", "Grains", "2027-01-01", "no")`.
  `"In stock"`, `"Pantry"`, `"Grains"` are the names of the
  **default seeded** StockLevel / StockLocation / StockGroup rows. An
  install that renamed those (which is perfectly legal — the whole
  point of the taxonomy editors under Settings → Kitchen setup) gets
  an example CSV that would fail row-level validation on commit. The
  template is honest about the *schema* but not about *this install's
  actual reference data*.
- **Why deferred:** worth its own thinking — the fix isn't obvious and
  changes the endpoint's shape.
- **Recommended resolution:** decide between:
  - **(a)** Add an inline `# example values are illustrative; use your
    own level/location/group names` comment on the CSV as a third
    row starting with `#`, and rely on the user to overwrite. Cheap;
    doesn't require a DB read; still ships broken defaults.
  - **(b)** Have the template endpoint read the install's actual
    seeded StockLevel/StockLocation/StockGroup names and inject the
    first of each into the example row. Correct for every install
    but makes the template dynamic — the frontend cache-once
    pattern would need a nudge (or accept staleness across a rename,
    which is fine).
  - **(c)** Drop the example row entirely — just emit the header row.
    Cleanest schema story; loses a bit of "here's what a filled-in
    row looks like" hand-holding.
  My lean: **(b)**. Adds ~20 lines of backend, no UI change, and the
  template is now truly install-shaped. But (c) is defensible if we
  want the endpoint to stay stateless.

## [OPEN] FU-348 — Import templates: registry has no "every importable section has a template" symmetry check
- **Raised:** 2026-07-01 (post-FU-343 self-review).
- **Type:** finding (latent bug when a second importable section lands).
- **What:** The `IMPORT_TEMPLATES` tuple is manually curated. Today
  that's fine (`stock_items` is the only shape the importer supports)
  — but when a second importable section lands (recipes, shopping
  lists), someone has to remember to add an `ImportTemplate` entry
  or the "Download template" button silently misses that section.
  The commit handler and the templates registry don't share a
  registry-of-registries; nothing enforces symmetry.
- **Why deferred:** trivially true today; only bites when a second
  section lands.
- **Recommended resolution:** when a second importable section is
  planned, introduce an `IMPORTABLE_SECTIONS` registry that both the
  commit handler and the templates endpoint consume — one entry per
  section with `{name, target_fields, synonyms, example, commit_fn}`.
  Or, simpler: at module load, assert that every section the commit
  path recognises has a matching `ImportTemplate`. The exact shape
  falls out naturally when the second section is designed; don't
  pre-design it. **Recommended resolution point:** when the second
  importable section is designed.

## [OPEN] FU-347 — Import template CSV: no UTF-8 BOM — Excel-on-Windows garbles accented example values
- **Raised:** 2026-07-01 (post-FU-343 self-review).
- **Type:** finding (latent — only bites when non-ASCII enters the example).
- **What:** The templates endpoint in
  [`import_spreadsheet.py`](dora_api/features/data/import_spreadsheet.py)
  emits UTF-8 without a BOM. Today the example row is all ASCII, so
  nothing renders wrong. If a future example includes an accented
  character (`café`, `crème`, a currency symbol, etc.), Excel on
  Windows will show mojibake unless the user opens via Data → From
  Text and picks UTF-8. The inspect endpoint strips a BOM if
  present, so the round-trip works either way — this is a display-
  only concern for the *download*, not the *upload*.
- **Why deferred:** doesn't bite today (all-ASCII example).
- **Recommended resolution:** prepend `﻿` to the CSV body when
  writing (one line change). Trivial. **Recommended resolution
  point:** now if we ever want to add non-ASCII to an example
  (unlikely for stock_items), else pair with FU-349 if we go for
  option (b) — customer-named locations / groups might contain
  accents.

## [OPEN] FU-346 — Admin settings feel hidden — pick a better host / entry point
- **Raised:** 2026-07-01 (settings-scroll fix session).
- **Type:** design decision.
- **What:** User noted the Admin · global group inside `/settings/*`
  "feels a little hidden". The settings shell (see
  [`SettingsShell.vue`](web_app/src/pages/SettingsShell.vue)) puts it
  as the third sidebar group under Account + Kitchen setup, admin-
  gated. User floated "maybe as a separate option in the profile
  dropdown" but the header dropdown was retired 2026-07-01 (the
  avatar now goes straight to `/settings/account`), so there's no
  obvious host.
- **Why deferred:** Ambiguous design call — could stay put (with a
  visibility polish, e.g. a divider or shield-badge affordance),
  become a peer header icon for admins only (like the retired Help
  button pattern), get its own top-level `/admin` route, or land in
  a small avatar-tooltip menu. Each has trade-offs against the
  charter's Effortless + Anti-creep tiebreak and against the recent
  header-simplification work. Needs a user call, not a silent
  reshuffle.
- **Recommended resolution:** now — user asked the question; needs a
  short back-and-forth on direction before any code moves.

---

## [OPEN] FU-337 — Platform deliverables docs reference artifacts that don't actually ship
- **Raised:** 2026-06-30 (FU-327 audit — `docs/05_investigations/PLATFORM_BUILDS_AUDIT.md`).
- **Type:** finding / leftover.
- **What:** README + the FU-333 Bucket D copy reference AppImage *and*
  `.exe` *and* `.dmg` as if all three exist today. Only the AppImage
  actually does. A user reading the current docs would expect a
  Windows / macOS installer link in a release and find none. Either
  build the other two (paired with [[FU-327]]) or correct the docs
  to set expectations.
- **Why deferred:** docs-only sweep that's only worth doing once the
  build-script decision is made — the right copy depends on which
  targets actually ship.
- **Recommended resolution:** pair with [[FU-327]]. If FU-327 ships
  Windows + macOS scripts, the docs already-write themselves. If
  FU-327 defers further, this FU does the doc-correction pass so the
  README stops over-promising.

## [OPEN] FU-336 — PWA build mode never actually selected — Workbox/manifest config emits nothing
- **Raised:** 2026-06-30 (FU-327 audit — `docs/05_investigations/PLATFORM_BUILDS_AUDIT.md`).
- **Type:** finding (config wired, build step skips it).
- **What:** `web_app/quasar.config.ts` lines ~226–347 define a
  complete PWA: Workbox `GenerateSW`, manifest with 4 app shortcuts
  (primary list, shop-now, scan, add-item), NetworkFirst on `/api/`,
  CacheFirst on stock/merchant images, offline.html fallback.
  Client-side lifecycle + push subscription wiring are already
  shipped ([usePwaLifecycle.ts](web_app/src/composables/usePwaLifecycle.ts),
  [usePushSubscription.ts](web_app/src/composables/usePushSubscription.ts)),
  and the backend has Web Push end-to-end
  ([push_sender.py](dora_api/infrastructure/push_sender.py)). But
  `npm run build` runs `quasar build` (SPA mode), **not**
  `quasar build -m pwa`. The SW + manifest + offline.html therefore
  never land in shipped artifacts. The same is true of the
  PyInstaller bundle (it consumes whatever `web_app/dist/spa/`
  contains — which today is the SPA-mode build).
- **Why deferred:** out of scope of the audit prompt; the audit was
  recon-only.
- **Recommended resolution:** ~1 hour fix. Two options:
  1. Change `web_app/package.json`'s `build` script to
     `quasar build -m pwa`, or
  2. Add a sibling `build:pwa` script and update consumers
     (`packaging/build-linux.sh`, `Dockerfile`) accordingly.
  Then verify the manifest + SW are present in `dist/pwa/` (or
  `dist/spa/`, depending on what Quasar v2 emits today) and that
  the PyInstaller spec's `("web_app/dist/spa", "web_app/dist/spa")`
  data tuple still points at the right output path. **Highest-ROI
  platform move in the audit** — install-to-home-screen on every
  modern mobile + desktop with zero new code. Tagged "now" for the
  next platform-targeted session.

## [OPEN] FU-335 — Migrate StoresSettings logo upload to ImageSourcePicker
- **Raised:** 2026-06-30 (FU-334 follow-on — image-source-picker rollout)
- **Type:** leftover
- **What:** [`web_app/src/pages/settings/StoresSettings.vue`](web_app/src/pages/settings/StoresSettings.vue)
  still uses Quasar `q-file` for its store-logo upload. Every other
  image-upload site now routes through the shared `ImageSourcePicker`
  primitive (R-0NN), which gives users the **Take photo** vs **Choose
  image** split. Migrating means dropping `q-file` (loses its drag-drop
  visual + clearable affordance, gains the consistent UX). The store-logo
  surface also has its own bespoke chrome (preview + max-file-size hint +
  reject toast wiring) that needs careful re-housing.
- **Why deferred:** the `q-file` → custom-buttons swap is the only
  bespoke part of the chrome; the rest (preview + clear) belongs in
  `ImageUploadField` if we want it. Doing it right is a 30-line
  refactor with one cross-cutting concern (drag-drop equivalent), not
  trivial enough to slip into the FU-334 sweep. Charts as a quality
  follow-on, not a blocker.
- **Recommended resolution:** opportunistic, next time settings is
  touched OR when a second store-logo bug forces us into that file.

---

## [OPEN] FU-333 — Env-var sprawl: promote operational config to AppSetting + first-run wizard for desktop
- **Raised:** 2026-06-29 (user concern raised after the FU-153 / FU-330–332
  AI-assistant sweep added `DORA_LLM_KEY_ENCRYPTION_KEY` to an already
  long env-var list).
- **Type:** design + audit + implementation. Best-practice cleanup; UX
  unlock for desktop installs.

### The problem

Dora reads **19 `DORA_*` env vars** at boot. The mix isn't *bad* per se —
every individual var has a reason — but the result is a self-host
operator (and especially a desktop user) wading through a long
environment table to stand up the app. The user flagged this as
"perhaps difficult to manage" and asked whether an admin UI for the
vars would help.

**An "admin UI for env vars" is the wrong shape** (well-known
anti-pattern when the vars are secrets — you can't read the DB to
get the key that decrypts the DB). The *right* shape is to identify
which env vars genuinely need to stay env, promote the rest, and
hide what's left behind a setup wizard for the desktop path.

### Current env-var inventory (audit done 2026-06-29)

Each `DORA_*` env var sorted into one of three buckets:

#### Bucket A — must stay env (bootstrap / chicken-and-egg)

These are read **before** the DB is reachable, OR are the root key
that decrypts everything else in the DB. Cannot be moved.

| Env var | Read in | Why it's bootstrap |
|---|---|---|
| `DORA_SECRET_KEY` | `app.py:74` | Validates session cookies before any DB call. Required for the first request to even reach the auth layer. |
| `DORA_ENV` | `infrastructure/profile.py:43` | Decides debug vs prod mode — controls whether the DB seeds, whether destructive ops are allowed, etc. Read at process boot. |
| `DORA_LLM_KEY_ENCRYPTION_KEY` | `infrastructure/llm/key_encryption.py` | Root key for the Fernet ciphertext stored in `User.llm_api_key_encrypted`. If this lived in the DB, decrypting it would need... a different key. Chicken-and-egg. |
| `DORA_SECURE_COOKIES` | `app.py:90` | Set on `app.config` at startup; applies to *every* session cookie issued, including the one validating the admin's incoming request. |
| `DORA_SPA_DIR` | `features/spa/serve_spa.py:39` | Static-file root for the Quasar bundle. Read once at boot; needed before any route resolves. |
| `DORA_SKIP_PROD_VALIDATION` | `infrastructure/profile.py:92` | Dev/CI escape hatch; only meaningful at startup. |
| `DORA_ALLOW_DESTRUCTIVE` | `infrastructure/configuration_manager.py:239` | Gates `db.drop_all()` on dev boot. Read pre-DB by definition. |

**Verdict:** 7 vars genuinely stay in env. Documentation can make them less scary, but they don't move.

#### Bucket B — should move to AppSetting (operational config, not secrets)

These are not secrets and not bootstrap; they're values an admin would tweak operationally. They're env today purely by historic convenience. They belong in `AppSetting` rows with admin-UI editing — exactly the pattern Dora already uses for `master_llm_enabled`, `scanning_enabled`, `timezone`, `expiring_soon_window_days`, `product_search_url`, `unit_pricing_locale`, etc.

| Env var | Read in | Notes |
|---|---|---|
| `DORA_EMAIL_ENABLED` | `health_check.py:63` | Pure feature flag — exactly the shape of `meal_planning_enabled` / `money_enabled`. Move. |
| `DORA_AUDIT_RETENTION_DAYS` | `infrastructure/audit_retention.py:24` | Admin-configurable retention window. Move. |
| `DORA_PUBLIC_URL` | `infrastructure/auth_helpers.py:188` | Used for verification / password-reset email links. Operational; can be edited at any time. Move. |
| `DORA_SMTP_HOST` | `infrastructure/email_sender.py:56` | Operational config. Move. |
| `DORA_SMTP_PORT` | `infrastructure/email_sender.py:57` | Operational config. Move. |
| `DORA_SMTP_USERNAME` | `infrastructure/email_sender.py:54` | Not a secret on its own. Move. |
| `DORA_SMTP_FROM` | `infrastructure/email_sender.py:60` | Sender address. Move. |
| `DORA_SMTP_USE_TLS` | `infrastructure/email_sender.py:61` | TLS toggle. Move. |
| `DORA_VAPID_PUBLIC_KEY` | `infrastructure/push_sender.py:51` | Public key — by definition not secret. Move. |
| `DORA_VAPID_SUBJECT` | `infrastructure/push_sender.py:53` | Operator contact URL for the push service. Move. |
| `DORA_PIPER_BIN` | `features/tts/tts_synthesize.py:61` | Filesystem path. Operational. Move. |
| `DORA_PIPER_BUNDLED_VOICE_DIR` | `features/tts/voice_provision.py:81` | Filesystem path. Operational. Move. |
| `DORA_PIPER_VOICE` | `features/tts/tts_synthesize.py:70` | Default voice id. Move (or fold into an existing voice-catalog setting). |

**Verdict:** **12 vars** become 12 columns on `AppSetting` (or get folded into existing settings columns where the shape matches), edited via the existing admin Settings pages. Pure win — zero new security surface; reduces operator-onboarding from "configure 19 env vars" to "configure 7".

#### Bucket C — secrets that *could* move to encrypted DB (judgement call)

These are real secrets, but we now have the Fernet helper from FU-153 (`infrastructure/llm/key_encryption.py`) — so they *could* live in the DB encrypted at rest, using `DORA_LLM_KEY_ENCRYPTION_KEY` as the bootstrap key.

| Env var | Read in | Notes |
|---|---|---|
| `DORA_SMTP_PASSWORD` | `infrastructure/email_sender.py:59` | Real secret. Today: env. Could be: encrypted `AppSetting.smtp_password_encrypted` column. |
| `DORA_VAPID_PRIVATE_KEY` | `infrastructure/push_sender.py:52` | Real secret. Same shape. |

**Trade-off** to weigh before moving Bucket C:
- **Pro:** the operator's env footprint shrinks to **two** vars (`DORA_SECRET_KEY` + `DORA_LLM_KEY_ENCRYPTION_KEY`); the admin Settings UI can drive everything else end-to-end.
- **Pro:** matches the pattern we already shipped for per-user LLM keys. R-001 win.
- **Con:** `DORA_LLM_KEY_ENCRYPTION_KEY` becomes a *meta-key* — rotating it invalidates SMTP + VAPID + every user's LLM key in one stroke. Operator needs to know that.
- **Con:** the SMTP password is needed by a background job (the alerts-email digest) that may run on a worker process with a different code path; verify it can read `AppSetting` cleanly.

**Recommendation:** ship Bucket C *after* Bucket B has bedded in. The high-value move is Bucket B (12 vars promoted, no security trade-off). Bucket C is a nice-to-have that needs slightly more thought.

#### Bucket D — desktop UX (orthogonal but related)

Even after Buckets B + C land, a fresh desktop install still presents the user with at-minimum 2 env vars to set (`DORA_SECRET_KEY` + `DORA_LLM_KEY_ENCRYPTION_KEY`). For a household user who just double-clicked an AppImage / `.exe` / `.dmg`, that's still too much.

The right pattern (matches Bitwarden Desktop, Mattermost Desktop, etc.):
- The desktop wrapper (Electron / Tauri main process) owns a per-install JSON config at the OS's user-data path.
- **First-run wizard** on the Electron side auto-generates both bootstrap keys (`Fernet.generate_key()` for the encryption key; `secrets.token_urlsafe(48)` for the session key) and writes them to the config file.
- The wrapper's launcher reads that file and sets the env vars on the Python backend spawn. The user never sees an env var.
- Subsequent launches are silent — config exists, keys already generated.

This is **distinct from the server self-host path** (where env vars / systemd `EnvironmentFile=` / Docker `--env` are the right tool — operators have their own config management already and prefer it). The desktop bundle should *layer over* the env-var system, not replace it.

**Coordination:** the existing desktop-bundle work (FU-327 — Windows + macOS desktop build scripts for the Piper bundle) is the natural home for the wrapper-side setup wizard. Don't ship the wizard before the Linux AppImage / Windows / macOS bundles are wired; pair them.

### Sequencing recommendation

1. **Bucket B promotion** (~half-day, pure win). New migration adds 12 columns to `AppSetting` (or extends existing settings rows); update `get_app_settings.py` + `update_app_settings.py` DTOs; remove the env reads from the 7 named modules and replace with `AppSetting.x` lookups. Admin Settings UI gets new sections (Email, Push, Voice/TTS, Audit retention). Old env vars become **deprecated fallbacks** (read if set, but the AppSetting wins) for one release, then dropped. **No security surface change** — these were never secrets.

2. **Bucket C encryption** (~half-day, optional). New `AppSetting.{smtp_password_encrypted, vapid_private_key_encrypted}` columns. SMTP send path + push send path call `decrypt_api_key()` on use; SMTP-settings + push-settings admin UI accepts the plaintext on save and encrypts. Document the meta-key rotation impact. Env vars deprecated → dropped.

3. **Desktop wrapper first-run wizard** (paired with FU-327, ~1 day). Per-install JSON config under the OS user-data path; auto-generate both bootstrap keys on first run; launcher reads + sets env. Skip the wizard entirely for the server self-host path (operator-managed env stays the recommended pattern there).

### Why this is good engineering practice (not bikeshedding)

- **Bootstrap vs runtime config is the canonical split** in every well-built self-hosted app (GitLab `gitlab.rb` vs application_settings; Discourse env vs site_settings; Mattermost `config.json` vs admin UI). Dora today blurs the line; the audit cleans it up.
- **R-005 (distribution posture):** the same code runs as self-host single instance + managed instance + future SaaS. Today's env-heavy posture is fine for the first two; SaaS would need the runtime-config-in-DB pattern anyway. Doing it now means Path A doesn't need a re-architecture later.
- **Operator-onboarding reduction is real UX value.** Going from "edit 19 env vars correctly" → "set 2 bootstrap vars, configure the rest in Settings" is the kind of friction reduction that decides whether someone actually self-hosts vs gives up.
- **Aligns with the existing `AppSetting` pattern.** We already moved scanning, meal-planning, money, nutrition, etc. into per-install rows with admin-UI editing. SMTP / push / TTS / audit-retention are the same shape; they just got grandfathered into env earlier.

### Out of scope (for clarity)

- This FU does NOT propose touching the per-user `User.llm_*` columns shipped in FU-153 — those are the user's own config, not install config.
- This FU does NOT propose moving `DORA_SECRET_KEY` or `DORA_LLM_KEY_ENCRYPTION_KEY` into the DB — those are the bootstrap pair and stay env-only.
- This FU does NOT propose a "set arbitrary env vars from the admin UI" feature. That's the anti-pattern this FU exists to *avoid*.

### Recommended resolution

- **Step 1 (Bucket B)** — opportunistic, before the next self-hosted release. Highest leverage, smallest risk.
- **Step 2 (Bucket C)** — only after Step 1 has shipped + bedded in. Optional unless the operator-onboarding metric is a priority.
- **Step 3 (Desktop wizard)** — pair with FU-327 when the desktop-bundle work resumes. Don't ship in isolation.

### Engineering-standards note

This is large enough to warrant its own ADR when it lands (recommended title: "Operational config lives in `AppSetting`, not env"). The R-005 ("Portable data access & distribution posture") rule already implies this — explicitly calling it out in an ADR would put the principle in scope for every future "where should this config live?" call.


## [OPEN] FU-328 — Four pre-existing pytest failures (data_router / household_tz / product / recipe_is_planned)
- **Raised:** 2026-06-29 (FU-288 resolution — full-suite run uncovered a
  *different* set of failures than FU-288 originally named).
- **Type:** finding (pre-existing drift; confirmed on a clean stash).
- **What:** `./.venv/bin/pytest tests/` shows **4 failures, all pre-existing**,
  unrelated to the three profile-picture tests FU-288 named (those all pass
  now). Confirmed via `git stash` — they fail on clean HEAD too:
  - `tests/e2e/dora_api/test_data_router.py::test__chunked_upload__chunk_offset_mismatch__is_400`
  - `tests/e2e/dora_api/test_household_tz_boundaries.py::test__dashboard__upcoming_window_anchored_on_household_today`
  - `tests/e2e/dora_api/test_product_router.py::test__update_product__PriceNowAtZeroBoundary__IsBadRequest`
  - `tests/e2e/dora_api/test_recipe_is_planned.py::test__recipes__is_planned_true_when_future_unconsumed_entry_exists`
  Suite totals: 4 failed, 536 passed.
- **Why deferred:** out of scope of the FU-288 / FU-285 / FU-289 work unit
  (R-007); each failure belongs to its own feature area (data import,
  household-tz boundaries, product validation, planner-derived `is_planned`).
- **Recommended resolution:** opportunistic per area — when next touching
  data-import / dashboard upcoming-window / product validation / `is_planned`
  derivation, run that test first, see what it expects, and either fix the
  code or update the assertion. Don't bundle as one "fix the 4" job — each
  failure is its own story.

## [OPEN] FU-320 — Document every auto-behaviour in the in-app help and point at the setting that controls it
- **Raised:** 2026-06-28 (FU-092 magic-behaviour audit close-out).
- **Type:** documentation / discoverability.
- **What:** For every auto-behaviour catalogued in
  `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md`, write a plain-
  English entry in the relevant in-app help section (Settings help,
  feature-specific help cards, onboarding tooltips — whichever
  surface owns the feature). Each entry:
  1. Names the behaviour ("When you mark an item Low, Dora may add
     it to your shopping list automatically").
  2. States the trigger and what changes ("…when you turn on
     *Auto-add when low* on the item, and you have exactly one
     draft list").
  3. **Links to the setting / toggle that controls it** so the user
     can turn it off, switch it, or read more — never just "the app
     does this" with no escape hatch.
  All 18 findings get coverage (including the (a)-keep-silent ones —
  the doc is the receipt that proves they're not hidden, even if no
  per-event surface fires). Audit table → help-section map should be
  spelled out in this FU's eventual implementation chunk.
- **Gate (HARD):** **do NOT start until all related FUs are
  resolved.** The related set is:
  - [[FU-315]] auto-add toast/chip verify
  - [[FU-316]] remembered-list toast + "always ask" setting
  - [[FU-317]] manual meal-plan reconcile proposal **and** its
    implementation chunks (the F5 area is the one where the help
    copy would change most after the new feature lands)
  - [[FU-318]] cheapest-pick chip
  - [[FU-319]] inline-create pantry toast
  Starting this work earlier than that means the help copy goes
  stale the moment one of those follow-ups lands (new toast wording,
  new setting toggle, new manual-reconcile surface to point at).
- **Why deferred:** documentation that describes a moving target is
  worse than no documentation. Wait for the surface decisions to
  settle.
- **Recommended resolution:** focused doc-writing pass once the gate
  clears — own its own prompt under `docs/03_prompts/`.
- **Cross-ref:** `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` (the
  source-of-truth catalogue this FU documents into help).

## [OPEN] FU-319 — Toast "Added <name> to your pantry" on inline-create from the recipe ingredient picker (F9)
- **Raised:** 2026-06-28 (FU-092 magic-audit verdict on F9 — (b)).
- **Type:** UX / cleanup.
- **What:** The recipe ingredient `q-select` exposes a "Create '<typed>'"
  no-option entry that fires a POST to create a brand-new `StockItem`
  inline. The new item survives even if the user cancels the recipe save
  (verified during the audit). Add a small positive toast "Added <name>
  to your pantry" when that inline-create path fires so the user isn't
  surprised by a new tracked item on the next StockOverview visit.
- **Where:** `web_app/src/pages/RecipeDetailPage.vue:395` (the picker)
  and the create-stock-item handler the inline-create eventually calls.
- **Recommended resolution:** opportunistic — fold into the next cookbook /
  recipe-editor touch. 1–2 lines.
- **Cross-ref:** `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` F9.

## [OPEN] FU-318 — "Cheapest" chip on shopping-list lines using the auto-picked offer (F7)
- **Raised:** 2026-06-28 (FU-092 magic-audit verdict on F7 — (b)).
- **Type:** UX / cleanup.
- **What:** When a line has no `selected_product_id`, the displayed
  price / store comes from `chosenOfferFor(line)` falling back to
  `offers[0]` (server pre-sorted cheapest-first). Render a small
  `cheapest` chip on those lines so the user can see *why* the price is
  what it is — removes the only "did I really pick that store?" surprise
  on the list. Don't render the chip when `selected_product_id` is set
  (user picked) or when the user has typed an `actual_unit_price`
  override (the price-source label takes precedence).
- **Where:** `web_app/src/pages/ShoppingListDetail.vue` line render +
  `web_app/src/models/shoppingList.ts:172` (`chosenOfferFor`); confirm
  the same fallback shape at
  `dora_api/features/shopping_lists/get_shopping_list_detail.py:108-110`.
- **Recommended resolution:** opportunistic — fold into the next
  shopping-list-detail polish pass. ~10 LOC.
- **Cross-ref:** `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` F7.

## [OPEN] FU-317 — Proposal: manual meal-plan reconcile feature ("stocktake-mode for meals") + opt-in for auto-drain (F5)
- **Raised:** 2026-06-28 (FU-092 magic-audit verdict on F5 — plan-first).
- **Type:** proposal / design (no code yet).
- **What:** `reconcile_consumed_meals` is currently the heaviest implicit
  behaviour in the app — every dashboard / meal-plan / recipe read
  silently marks past-day plan entries as consumed and decrements the
  `Recipe.available_meals` pool. No receipt, no undo, no "did you
  actually cook this?" check.
  User wants this thought through before any code touches the
  reconcile path. The desired shape:
  1. **Per-user setting**, default **on**, for "auto-drain past-day
     plans". When off, past-day entries stay unconsumed until the user
     explicitly confirms them.
  2. **A new manual-reconcile feature** modelled on stocktake mode —
     its own page, its own surfacing (alert / dashboard chip), and a
     UX that **shows the user what *should* have been consumed** since
     they last reconciled, so they can confirm / amend per-entry
     before the pool decrements.
  3. Decide what happens to existing alerts (`no_planned_meals`, etc.)
     when manual-reconcile is overdue — does an "unreconciled meals"
     alert fire? At what severity?
  4. Decide whether auto-drain and manual-reconcile coexist (auto-drain
     decrements; manual-reconcile lets the user dispute / amend after
     the fact) or are mutually exclusive (off-by-default users never
     auto-drain; on-by-default users never reconcile).
- **Where to write:** new `docs/04_proposals/PROPOSAL_MEAL_RECONCILE.md`.
  Cross-cut feedback table at the end per the CLAUDE.md mandate.
- **Why deferred:** Charter-level UX call; needs a designed surface
  (page + alert + dashboard chip) before the implementation chunks make
  sense. The audit itself is FU-092's scope; the *feature* is not.
- **Recommended resolution:** focused design session — own its own
  prompt under `docs/03_prompts/`. Before any code touches
  `reconcile_consumed_meals.py` or the `before_request` hook in
  `startup.py:150`.
- **Cross-ref:** `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md` F5 (+
  F6, which rides this decision).

## [OPEN] FU-313 — Designed token ladder for graded severity / heatmap palettes
- **Raised:** 2026-06-26 (FU-046 A1 theme-token regression sweep).
- **Type:** deferred job.
- **What:** four surfaces still ride Quasar's numbered palette because they
  encode a *graded* severity / heatmap, not a binary semantic — a single
  `negative` / `warning` doesn't carry the ordinal signal. Sites:
  - `web_app/src/models/alert.ts:144-169` — alert-severity gradient
    (red → orange → amber → deep-orange → purple → teal → indigo).
  - `web_app/src/models/location.ts:41-45` — location-heatmap palette
    (green → teal → amber → orange → red).
  - `web_app/src/pages/AlertsPage.vue:422-423` — `historyChipColor`
    state ladder: `'orange-7'` (snoozed), `'blue-grey-5'` (read).
  - `web_app/src/components/AddToListButton.vue:247` and
    `web_app/src/pages/StockItemDetailPage.vue:1635` — `'amber-9'`
    "needs attention" tones (inspect; likely the same shape).
- **Why deferred:** swapping these to a single semantic loses ordinal info, and
  picking N specific palette stops is a design decision, not a sweep. They need
  a designed token ladder — e.g. `--severity-1`..`--severity-5` (and a
  `--heatmap-1..N`) — defined in `web_app/src/style/tokens.scss` +
  `themes.scss` so each step is theme-aware in both light and dark, and a tiny
  `severityClass(level)` helper to map an ordinal to the right token-bound
  class.
- **Recommended resolution:** opportunistic — bundle with the next visual
  pass on alerts/heatmaps, or when an A-wave design brief touches severity UI.
- **State note:** (filled in when resolved)

## [OPEN] FU-304 — Meal planner rebuild: build both layouts (A + B) behind a toggle
- **Raised:** 2026-06-25 (`/design-critique` on the meal planner →
  `docs/04_proposals/IMPL_PLAN_MEAL_PLANS_REBUILD.md`).
- **Type:** deferred job.
- **What:** the brief diagnoses the planner's emergent sprawl (all-slots ×
  all-days + vertical carousel + non-sticky columns + centre-weighted grid).
  **Q1 RESOLVED (2026-06-25):** build **both** directions and keep them live
  behind a **temp desktop toggle** — upgrade the existing page to **Direction A**
  (de-sprawled carousel) and add a **separate page** for **Direction B** (desktop
  week grid). Shared state/logic; pick a winner later, then delete the loser +
  toggle. Canonical phasing is **§12** of the brief.
- **Progress (2026-06-25 PM):**
  - **R-Phase 0 closed** — Q2 (used-slots default), Q3 (gate behind batch
    posture), Q4 (bottom-sheet picker), Q5 (slot-as-tag, B page only),
    Q6 (server-enrich `MealPlanEntryDto`) all locked with the recommended
    option. Brief §11 updated to reflect resolutions. FU-179 still left to
    user (browser-verify).
  - **R-Phase 1 landed** — extracted `useMealPlanner()` composable +
    `MealPlanRecipePicker.vue` + `MealPlanWeekDayCard.vue` +
    `MealPlanShoppingSummary.vue`. `MealPlansOverview.vue` shrinks
    1,222 → 304 lines, behaviour-preserving. vue-tsc + eslint clean on the
    five changed files.
  - **R-Phase 2 landed (2026-06-25 PM, same session)** — Direction A
    upgrade: de-sprawled per-day slots (Q2) with calm "+ add a meal" +
    show-all toggle, sticky context columns, new
    `MealPlanWeekStatus.vue` strip, `MealPlanFirstRun.vue` hero,
    empty-week "Plan this week" banner, U7 destructive-button fix. Seven
    files changed/added; vue-tsc + eslint clean. Browser walk folded into
    FU-305.
  - **R-Phase 3 landed (2026-06-25 PM, same session)** — Direction B
    page + A/B toggle. Q6 server-enriched `MealPlanEntryDto` (4 new
    display fields + bulk-hydrated `has_image`).
    `MealPlanRichCard.vue` (slot-as-tag per Q5), `MealPlanWeekBoard.vue`
    (7-day grid with day-major default + group-by-slot alt view),
    `MealPlansBoardPage.vue` (top strip + sticky consequences bar +
    pinnable picker drawer + calendar-as-popover), and the
    `useMealPlannerView` persistence helper. New route
    `/meal-plans/board`. List/Grid toggle on both pages (desktop-only).
    13 files touched; vue-tsc + eslint + AST-parse clean. Browser walk
    folded into FU-305.
  - **R-Phase 4 landed (2026-06-25 PM, same session)** — shared mobile
    single-day focus. `MealPlanMobileFocus.vue` (day-strip + focused-day
    cards + collapsible week status) and `MealPlanPickerSheet.vue`
    (bottom-sheet picker). Both pages render the same focus at `lt.md`;
    A/B toggle gated to desktop only. Slot-as-tag rich card reused on
    mobile. Drag is force-disabled at the picker level on mobile (H7).
    vue-tsc + eslint clean.
  - **R-Phase 5 landed (2026-06-25 PM, same session)** — three cleanups:
    (a) Q3 batch posture gate end-to-end (User column + migration +
    `useBatchEnabled` + Settings → Preferences toggle + 5 component
    gates); (b) sequential builder rebuilt onto the shared picker
    (multi-select mode) + dead Email button hidden + build decoupled
    from generate-list; (c) `MealPlanTemplatesDrawer.vue` apply/manage
    drawer wired into both pages. 14 files touched + new Alembic
    migration `e4c7a2f9b5d3`. vue-tsc + eslint + AST-parse clean.
    The migration needs to run on the user's DB before the next
    backend boot.
  - **R-Phase 6 landed (2026-06-26)** — hierarchy + a11y + skeletons.
    Calmer status accents on entry chip + rich card (border + icon +
    aria-label, not saturated fill). Slot rows / day columns / week
    rows / calendar weeks promoted to real `<button>` with combined
    accessible labels. Global ArrowUp/Down nav scoped via
    `closest('button,a,select,…')` so it doesn't steal focus keys.
    New `MealPlanSkeleton.vue` (list / grid / mobile variants) +
    `useMealPlanner.isInitialLoading` ref render layout-shaped
    placeholders during the ~10 parallel mount loads. Calendar status
    text alternatives via `title` + aria-label close 1.4.1.
    9 files touched; vue-tsc + eslint clean.
- **Sequencing (resolved):** extraction-first — **R-Phase 1** pulls a
  `useMealPlanner()` composable + leaf components out of the current page
  (behaviour-preserving R-001) **before** the B page is created, to avoid a
  1,222-line duplicate that double-maintains mutation logic. **Done.**
- **Recommended resolution:** next session — **"pick a winner" cleanup**
  (live with both layouts; once A or B wins, delete the loser page +
  `useMealPlannerView` + the A/B toggle + any leaf components unused by
  the survivor). After that FU-304 itself closes.

## [OPEN] FU-308 — Fold the /meal-plans/templates manager into the drawer (or retire it)
- **Raised:** 2026-06-25 (R-Phase 5 of the meal planner rebuild).
- **Type:** follow-up.
- **What:** R-Phase 5's templates drawer covers the daily Apply / Rename /
  Delete / Save flow. The dedicated `/meal-plans/templates` page still
  exists and is reachable via direct URL — it shipped before the drawer
  and overlaps with the drawer for the basic CRUD. Once browser-verified,
  either (a) fold any unique-to-page features (e.g. bulk reorder, full
  description editing) into the drawer and retire the route, or (b) keep
  the page as the "heavy management" screen and add a clearer entry
  point on the planner pages (right now neither the A page templates
  card nor the B page Templates button links to it).
- **Why deferred:** R-Phase 5 explicitly scoped to the drawer (§9-E);
  reworking the dedicated page is its own assessment.
- **Recommended resolution:** opportunistic — at the "pick a winner"
  cleanup, decide if the manager page survives.

## [OPEN] FU-309 — Run the batch-posture migration before next backend boot
- **Raised:** 2026-06-25 (R-Phase 5 of the meal planner rebuild).
- **Type:** finding (operational debt — built static; no Python
  interpreter on this host).
- **What:** R-Phase 5 adds `User.batch_features_enabled` as a non-null
  column (migration `e4c7a2f9b5d3_20260625_user_batch_optin.py`). The
  GET `/api/users/me` handler reads it through `from_entity`, so a
  backend boot against an unmigrated DB will 500 on every
  authenticated call. Run `flask db upgrade` (or your equivalent) on
  local DBs before restarting the API. Existing users default to
  False ("fresh"), matching the Charter P10 Anti-creep choice.
- **Why deferred:** no Python interpreter on the session host;
  migration is static.
- **Recommended resolution:** **now**, before the next backend boot
  on any environment.

## [OPEN] FU-307 — Per-entry cookability on the Direction-B meal card
- **Raised:** 2026-06-25 (R-Phase 3 of the meal planner rebuild).
- **Type:** follow-up (enhancement).
- **What:** the rich meal card on Direction B currently colours the left
  accent amber when the **recipe is in the cook-shortfall set** (the same
  signal the existing chip uses). It does **not** yet show "missing 3
  ingredients" / "ready to cook now" per entry. To do that the meal-plan
  query would need to include `MealPlanEntry.recipe.ingredients`
  (selectin-loaded), and the entry DTO would fold `missing_count_for(...)`
  + `cookable` through. The query expansion is modest but not free.
- **Why deferred:** §6.5 calls for status accent + tag, which the existing
  shortfall signal already drives; per-entry "what's missing" is the next
  precision step rather than a critical part of the card.
- **Recommended resolution:** opportunistic — when Direction B is named the
  winner and the cookability detail is wanted on the card. The same enrichment
  can flow into the A-page chip too (`MealPlanEntryChip.vue`).

## [OPEN] FU-306 — Persist "Show all slots" toggle across reload
- **Raised:** 2026-06-25 (R-Phase 2 of the meal planner rebuild).
- **Type:** follow-up (enhancement).
- **What:** the new "Show all slots" toggle above the meal-plan carousel is
  currently a session-local `ref` — refreshing the page reverts to the
  used-slots default. For a household that *does* plan all five slots a day,
  re-flicking the toggle every visit is friction.
- **Why deferred:** the default (used-slots) covers the dominant case
  cleanly. A genuine multi-slot household will tell us; pre-emptively
  wiring a household preference is small but not free (settings UI + a new
  pref column).
- **Recommended resolution:** opportunistic — when adding the next batch of
  household preferences, lift `showAllSlots` into the household
  `Preference` table (or a small local-storage cache if the call is "this
  is purely a per-device view choice").

## [OPEN] FU-302 — Dora Score reassessment: waste-as-pillar weight
- **Raised:** 2026-06-24 (C-waste design — `PROPOSAL_WASTE_MINIMISATION.md`).
- **Type:** finding
- **What:** `DASHY_DORA_CHAMPION_PLAN.md` §§334, 346, 444–447 treat waste as one of four Dora Score pillars ("low waste, on-budget, fresh, few run-outs"). The C-waste design deliberately de-emphasises waste as a UI feature — the `/waste` page is deleted, the capture flow shrinks to a single row dropdown action with no money/note capture, no Reports card. The *signal* is preserved (events still logged + queryable) so the Score can read it. But the de-emphasis is a quiet vote that the Score model itself may want re-weighting — perhaps waste shrinks to a smaller pillar, or merges with another (e.g. "fresh + low-waste" → one freshness pillar). This is a **charter-level** decision, not a UI cleanup, and was explicitly out of scope for C-waste.
- **Why deferred:** the Score isn't designed yet (Phase 3 / champion phase); doing the weighting now would be speculative. Better to revisit when the Score model is being built and the full pillar picture is on the table.
- **Recommended resolution:** later during pre-Phase 3 (when the Dora Score model is actually being designed; the reassessment is an input to that design, not its own deliverable).

## [OPEN] FU-295 — Confirm the Alerts page (D5) no longer 404s
- **Raised:** 2026-06-24 (Dashboard rebuild Phase 3).
- **Type:** finding (reported defect, static-only verification).
- **What:** feedback D5 reported "Alerts navigation is broken (goes to 404)". A
  static read shows the `/alerts` route IS registered (`routes.ts` →
  `pages/AlertsPage.vue`, the C-9 control surface), so it appears fixed — but a
  static read is not proof.
- **Recommended resolution:** the verify itself is tracked in `DORA_VERIFY.md`
  under "Dashboard rebuild" (it's the same click that exercises the Phase-3
  alert card → `/alerts` link). Close this FU once that pass is green.

## [OPEN] FU-357 — Cross-app undo off after dashboard "push expiry"
- **Raised:** 2026-06-23 (Dashboard `/design-critique` pass).
- **Type:** finding.
- **What:** feedback L480 — "Undo cross-app seems off, e.g. dashboard push
  expiry, then go to stock item and clear its expiry." An undo/toast initiated
  on the dashboard alert action doesn't behave correctly once you navigate to
  the stock item and mutate the same field. Marked **out-of-scope** in
  `IMPL_PLAN_DASHBOARD_REBUILD.md` §5 — it's an undo/toast-ownership defect, not
  a dashboard-design item.
- **Why deferred:** belongs to whoever owns the cross-app undo/toast mechanism,
  not the dashboard rebuild scope (R-007).
- **Recommended resolution:** confirm in browser, then route to the undo/toast
  owner (likely the global notify/undo layer).

## [OPEN] FU-284 — settings mobile nav still horizontal-scroll fallback (Phase 5 owes top tab strip)
- **Raised:** 2026-06-23 (Settings rebuild Phase 3).
- **Type:** deferred job.
- **What:** §6.3 was resolved as **top tab strip** but Phase 3 only ships the
  desktop shell + a `flex-direction: row; overflow-x: auto` fallback on
  `<1024px`. The real implementation (three top tabs → chip strip with the
  selected group's sub-items) is owned by Phase 5.
- **Why deferred:** Phase 3 owns desktop visuals only; mobile is a dedicated
  phase that also revisits SettingsSection row collapse + theme grid + the
  DoraSegmented overflow shape.
- **Recommended resolution:** later during Phase 5 (mobile pass).

## [OPEN] FU-226 — Assess the new stocktake-queue rules (history vs. current vs. desired)
- **Raised:** 2026-06-19 (Stock Overview bulk + stocktake feedback round)
- **Type:** finding (UX policy — needs user judgement)
- **What:** Round-18 swapped the stocktake queue's filter from "anything overdue
  surfaces" to a stricter engagement-based rule. The user wants this written down
  so they can sit with it and decide whether it's right, looser, or stricter
  before any more code lands.

### What it WAS (pre-round-18)

  In `dora_api/features/stocktake/stocktake.py::get_stocktake_queue`:

  An item entered the queue when **both** were true:
  1. `stocktake_alerts_are_enabled == True` (per-item manual opt-out).
  2. `_compute_overdue(item) > 0`, where overdue is:
     - **`9999`** if `last_checked_at is None` (never-checked sentinel — items
       always surfaced as "maximally overdue").
     - Otherwise: `max(0, days_since_last_check − days_until_stocktake_alert)`.
       The per-item cadence is `days_until_stocktake_alert` (default 14, set on
       create).

  Ordering: most-overdue first → oldest `last_checked_at` → name.

  Pain point the user reported: a freshly-created stub item ("nachos I don't
  really keep in stock") immediately landed at the top of the queue because
  it'd never been checked → 9999 overdue. Dora pestered the user about every
  item they'd ever typed into the system, including items they'd long ago
  decided not to manage.

### What it IS NOW (round-18, 2026-06-19)

  Same two existing gates (per-item opt-out + `overdue > 0`), PLUS a new
  **engagement gate** that runs before either. An item must show ≥1 sign the
  user actually manages it:

  1. `is_flagged` (Essential) **or** `auto_add_when_low` — explicit "this
     matters" flags.
  2. Currently in stock — `stock_level.sequence < OUT_OF_STOCK_SEQUENCE`.
  3. Ever opened — `opened_on is not None`.
  4. Level was changed at least once — any `StockLevelChange` row exists for
     this stock_item_id. (The history table only grows when a level actually
     moves, so this distinguishes "never touched" from "touched once and back
     to default".)
  5. On any shopping list, ever — any `ShoppingListLine` row references this
     stock_item_id, regardless of list status (active or done).

  Signals 4 + 5 are bulk-fetched in one DISTINCT query each, so the queue
  endpoint stays cheap on big pantries.

  The `9999` never-checked sentinel is **kept**. The intent: engaged-but-
  never-checked items (essential / on a list / in-stock / etc.) still surface
  first; the engagement gate just stops the queue from drowning in unengaged
  stubs.

### Things to weigh when assessing

  - **False negatives** — items the user DOES care about but that fail every
    engagement signal. Likeliest case: an item that's normally well-stocked
    but is genuinely depleted right now, and the user never opened it (not a
    sealed product they "open"), never flagged it essential, never put it on
    a list, never moved the level. Possibly: a recurring seasonal item the
    user wants to be reminded to restock but hasn't engaged with recently.
  - **False positives** — items that pass engagement but shouldn't really
    nag. Likeliest case: items that were on ONE shopping list once five
    months ago and have been ignored since. Signal 5 ("ever on a list") is
    intentionally permissive — should it be "on a recent list" instead?
    (e.g. last 60 days.) Trade-off: DB needs a join on list lifecycle
    timestamps; not free.
  - **Tuning knobs to consider**:
    - Time-bound the "on a list" signal (last N days).
    - Time-bound "level was changed" similarly (only count level changes in
      the last N days as engagement).
    - Add a "snooze for N days" affordance on the queue row so the user can
      mute individual items without flipping the binary `stocktake_alerts_
      are_enabled` flag.
    - Replace the global cadence with a smarter default (e.g. shorter for
      essentials, longer for "in-stock but lots of headroom" items).
    - Promote `stocktake_alerts_are_enabled` from "manual opt-out only" to
      "auto-set false when engagement decays past N days" so the data
      self-cleans.
  - **Candidate rule 4 — expiry as an engagement signal** (added
    2026-07-02, user feedback): the current engagement filter treats
    "opened" as a signal but does NOT treat "near-expiry" as one. Yet
    stocktake is exactly the moment the user walks the pantry and
    reviews expiring items, and near-expiry is arguably a stronger
    version of "in play" — a countdown ends in the discard bin.
    Currently near-expiry items surface via a **separate** flow
    ([`waste/rescue`](dora_api/features/waste/waste.py) endpoint + the
    Dashboard's "Needs your attention" card), so users have to check
    two surfaces for the same walk. Proposal to weigh: add "`expiry_date`
    within N days" (default 7, reusing `EXPIRING_SOON_WINDOW_DAYS`) as
    a sixth engagement signal.
    * **Frequency mismatch worth thinking through:** item-cadence is
      typically weekly-plus, but expiry-driven review wants **daily**
      surfacing. Two options:
      * (a) one queue, but expiring items get a synthetic-overdue score
        that pins them to the top regardless of `last_checked_at`. Simple;
        risks noise on a pantry with lots of dated items.
      * (b) two queue "modes" surfaced from the same page ("Overdue"
        cadence-driven + "Expiring" daily-driven, mode toggle on the
        header). Same list UI, filtered by mode. Cleaner UX; small
        extra API surface (`GET /stocktake/queue?mode=expiring`).
    * **Queue row shape:** whichever way, the queue row needs an
      `entry_reason` so the UI can render *why* it surfaced ("expiring
      in 2 days" vs "10 days overdue for a check"). The user shouldn't
      have to guess.
    * **R-003 check:** `waste/rescue` and the Dashboard expiry card
      stay — they're glance-surfaces (Dashboard) and cook-what-you-can
      rescue (rescue recipes matched to expiring ingredients).
      Stocktake would be the walk-the-pantry-and-decide surface. Shared
      SoT lives on a server-side `get_expiring_items` helper; UI cards
      read from it rather than duplicating expiry logic. Not a
      collision — three verbs (glance / cook / decide) on the same
      underlying data.
  - **Candidate verb 3 — waste as a stocktake resolution + bulk waste
    API** (added 2026-07-02, user feedback): today stocktake has two
    resolutions per item — Check (keep, bumps `last_checked_at`) and
    Set level (adjust). There's no **Waste** verb. If Rule 4 lands and
    expiring items enter the queue, the natural resolution for "past
    date" is bin-it → and the user shouldn't have to leave the
    stocktake flow to log it. Proposal to weigh:
    * Add "Waste" as a per-item resolution that logs a
      [`StockItemWasteEvent`](dora_api/domain/entities/stock_item_waste_event.py)
      AND flips the level to Out AND bumps `last_checked_at`, in one
      action. Charter P2 preserved — waste-capture stays
      reason-only (no quantity, no value, no note per
      `PROPOSAL_WASTE_MINIMISATION §5`).
    * New endpoint `POST /waste/events/bulk` taking a list of
      `{stock_item_id, reason}`. Bulk-select mode gains "Log waste on
      selected" alongside "Bulk check."
    * **Interaction with the check verb:** if an item is
      near-expiry AND the user hits "Check" (level still correct, not
      binning it yet), does it stay on the expiring queue? Probably
      yes — Check bumps `last_checked_at`, but expiry is unchanged.
      Worth surfacing this explicitly so a checked-but-still-close-to-
      expiry item doesn't silently drop off the rescue card.
  - **The combined framing worth naming:** stocktake and waste-rescue
    are two halves of the same walk (open the fridge → eyeball each
    item → resolve it), currently split into two surfaces. The clean
    long-term shape is stocktake as a *review* mode with three
    resolutions per item (Keep / Set level / Waste) and a queue that
    includes both cadence-overdue and expiry-imminent items. That's
    proposal-scope — probably belongs in a proper
    `PROPOSAL_STOCKTAKE_MODE.md` brief (see [[FU-430]]) rather than
    piecemeal, and the expiry+waste angle is a stronger anchor to
    build that brief around than the four remaining SK NO_HOME
    items alone.
  - **No-change cost**: if the round-18 rule turns out to be roughly right,
    the only required follow-on is the browser-verify pass (FU-222 covers
    the SPA side; this rule lives in the backend and wants its own dataset
    walk-through).

- **Why deferred:** the user explicitly wants to sit with this and decide
  later. No code change pending here yet — this entry is the substrate for
  that decision. **Extended 2026-07-02** with two candidate additions
  (expiry as an engagement signal, waste as a stocktake resolution + bulk
  API) surfaced from user feedback; the underlying framing is that
  stocktake and waste-rescue are two halves of the same walk. This
  extension is *for careful consideration*, not a build ask.
- **Recommended resolution:** opportunistic — re-open when the user has
  walked their pantry through the new queue and decided whether the
  engagement rule is too tight, too loose, or right. Coordinate with
  [[FU-430]] when either opens: the expiry+waste extension above is a
  stronger anchor for the missing `PROPOSAL_STOCKTAKE_MODE.md` brief
  than the four remaining SK NO_HOME items alone. Do not action either
  FU in isolation.

## [OPEN] FU-224 — App-wide colour-usage assessment (primary vs secondary vs accent)
- **Raised:** 2026-06-18 (Stock-pages feedback pass)
- **Type:** deferred job
- **What:** During the feedback pass the user noted that the open / in-use button on the
  Stock Overview row was using `secondary` and was hard to see in Pesto dark — that fix
  landed by promoting to `primary`, but the user flagged that the broader pattern
  ("majority primary usage; not sure where secondary actually pulls weight") may need a
  separate audit. Walk the app, list every place `color="secondary"` (and other lower-used
  semantics like `info`, `accent`) appears, decide which deserve to stay vs. which should
  consolidate to `primary` or theme tokens for visual hierarchy reasons. Likely outputs:
  a short proposal under `docs/04_proposals/` + targeted fixes.
- **Why deferred:** intentionally out of scope for the feedback pass (R-007). The user
  explicitly called it out as a separate task to think about.
- **Recommended resolution:** opportunistic — fold in next time a theming/styling pass
  comes around, or after FU-046 (theme-token compliance) gets another round.

## [OPEN] FU-220 — Repurpose `OnboardingLoop` in Help + consider menu re-ordering
- **Raised:** 2026-06-17 (FU-210 revisit — user direction)
- **Type:** follow-up (UX + IA)
- **What:** With the cinematic Story still alive (FU-210 revisit kept the hero loop there) and
  the Finish-step recap dropped, the loop is "a nice reminder of how to use the app." Find a
  durable home for it in **Help** so first-run users can revisit it after onboarding without
  rerunning the wizard. Two open IA questions to chew on at the same time:
  (a) **Help section order.** Should the Help sections be ordered in the loop's flow
      (Stock → Plan → List → Shop → Restock → Cook), so newcomers can read the help in the same
      order they'll actually use the app?
  (b) **Main menu order.** Same question for the left-nav: do the buttons map cleanly to the
      loop today? If not, is reordering worth doing — or is the loop's order aspirational
      and the menu's pragmatic (cookbook + recipes are nouns, not steps)?
- **Why deferred:** out of scope for the FU-210 revisit; needs a small Help-IA design pass
  (touches `HelpPage.vue` / `helpSections.ts` / nav). Not blocking.
- **Recommended resolution:** opportunistic / before commercialise (Phase 4). Keep the loop
  component (`OnboardingLoop.vue`) usable in non-onboarding contexts when you tackle this —
  it currently lives under `components/onboarding/`; consider promoting it to a more general
  location if Help also uses it (e.g. `components/dora/AppLoopDiagram.vue`).


## [OPEN] FU-188 — Back-in-stock subscriptions tier (deferred from Alerts C-9.5)
- **Raised:** 2026-06-15 (Alerts C-9.5 — subscriptions tier)
- **Type:** deferred job
- **What:** The proposal/impl plan for the subscriptions tier mentioned a **back-in-stock**
  subscription shape ("notify me when a merchant's product comes back in stock") alongside the
  price-watch (`PriceAlert`) tier that C-9.5 shipped. C-9.5 built **only** the price-watch
  surface (`SubscriptionsPanel.vue`, money-gated, reusing `/price-history/alerts`). Back-in-stock
  was **not** built: there is no data source / entity for it yet — it's companion/ingestion-scope
  (the producer would push availability), and the in-app side would just surface/manage rows like
  price watches do.
- **Why deferred:** anti-creep — no back-in-stock data exists to surface, so a placeholder UI/shape
  now would be speculative (charter: don't pre-build). User confirmed skipping it for C-9.5.
- **Recommended resolution:** **when** the companion/ingestion path (C-10) defines a back-in-stock
  signal — then add a second tier to `SubscriptionsPanel.vue` (same list/manage shape) reading it.

## [OPEN] FU-184 — Reconcile onboarding sell-copy + loop stages against actual app behaviour
- **Raised:** 2026-06-15 (Onboarding C-5 v3 design)
- **Type:** finding / deferred verification (P3 Honest gate)
- **What:** The C-5 onboarding redesign sells "the loop" cinematically (Stock → Plan → List →
  Shop → Restock → Cook, Dora at centre) with one-line claims per stage. These claims + the loop
  stages are **PROVISIONAL** (PROPOSAL_ONBOARDING §6). Before any onboarding copy ships, **walk
  the running app** and confirm each claim is literally true (does finishing a shop really
  auto-restock? does cook mode decrement stock? does price memory + an "inflated price" signal
  actually exist?). Cut/soften anything the app doesn't back.
- **The emerging "Insight / Spend-smarter" stage** (user links products to stock items → Dora
  flags prices that are higher than usual, from their own receipts) is the honest replacement
  for the divorced deal-scraping — but it **isn't a finished feature**. Do NOT promise it in
  onboarding copy until it's real; it's a design placeholder until then. Decide whether to build
  it (it's the spine of the **Spend-tracking** persona).
- **2026-06-16 (C-5.1 closed without tripping this gate):** C-5.1's copy edits are **labels +
  import wording only** (Skip; "spreadsheet or another app"), not aspirational feature claims, so
  the sell-copy honesty gate didn't apply to it. **Still open:** the welcome-card blurb mentions
  *"deals"* (flagged above) and the loop/Insight sell-copy land in **C-5.2/C-5.6** — those are the
  chunks this gate really bites on.
- **2026-06-16 (C-5.2 shipped the copy — gate now LIVE):** the cinematic intro + hero loop are built
  with the **provisional** sell-lines, centralised in **one file**:
  `web_app/src/pages/onboarding/onboardingContent.ts` (`LOOP_STAGES`, `LOOP_CENTRE`, `LOOP_INSIGHT`,
  `NARRATIVE_SCENES`, `PERSONA_PREVIEWS`). The user explicitly chose to **build-to-plan now and
  revisit with the assistant later** to confirm each claim against the finished app. The Insight beat
  is rendered as a dimmed, "soon"-tagged candidate (not a promise), and Shop's old "log what you paid"
  price claim was moved off Shop onto that provisional node. **Revisit = walk the running app, then
  edit that one content file** (cut/soften per claim); no component changes needed for copy-only fixes.
- **2026-06-16 (also spotted, C-5.3):** the onboarding **admin step** still says *"Pick which
  merchants to **scrape**"* (`WelcomeWizard.vue` admin card) — stale post scraping-divorce. Out of
  C-5.1/2/3 scope; reword in the loop/Insight copy pass (or the P8 rename), not piecemeal.
- **Why deferred:** needs the running app to verify; can't be cleared by a static read (env
  unprovisioned this session, same blocker as FU-183).
- **Recommended resolution:** **close-gate on the onboarding-copy chunks (C-5.1/C-5.2/C-5.6)** —
  validate when building them on a provisioned app. Not optional polish.

## [OPEN] FU-218 — Browser-verify the new admin "API access" page (C-10 / Phase B)
- **Raised:** 2026-06-17 (Phase B build)
- **Type:** verification
- **What:** New Settings page lives at `/settings/admin/api-access`. Confirm in the browser:
  (a) sidebar entry appears under Admin · global (admin only); (b) `New key` opens dialog → reveals
  raw key once → copy works → list shows the new row with `Never used` + `Accepted 0 / Skipped 0
  / Failed 0`; (c) expanding the row shows "Store mappings" panel; (d) push a record from any
  bearer client against an unknown store → reload → the source row shows a pending badge + the
  mapping appears in the panel marked "pending"; (e) merchant picker assigns it → the badge
  clears; (f) disable / enable / rename / revoke all round-trip; (g) revoked key is rejected by
  `/api/ingest` immediately.
- **Recommended resolution:** opportunistic — bundle with the other Phase 0 browser passes.

## [RESOLVED?] FU-190 — Ingestion API must honour "no auto-create stores"  *(move to RESOLVED on confirm)*
- **Update 2026-06-17 (Phase B build):** implemented as **(b) quarantine queue** end-to-end (the
  proposal's chosen safety net; the "(c) setup mapping step" is naturally produced by the same
  surface — admins map *before* pushing if they want, but unknown names on first sight quarantine
  instead of being rejected, which is friendlier). On every ingest record the producer's
  `merchant` string is resolved via `IngestionStoreMapping`: known → use the linked Merchant;
  unknown → create a quarantined mapping (`merchant_id IS NULL`), skip the record with reason
  `store_not_mapped`, surface as **pending** on the API access page. Stores themselves are
  **never** created by the endpoint. Admin assigns or clears the merchant via
  `PUT /api/ingestion-sources/<id>/store-mappings`. Covered by `test_ingest_batch.py` (quarantine
  + post-mapping roundtrip) + `test_ingestion_store_mappings.py` (CRUD + invalid merchant rejected).
  **Move to RESOLVED once the FU-218 browser pass confirms the pending → assign flow in the UI.**

## [OPEN] FU-176 — Apply R-014 (reveal-and-disable) app-wide
- **Raised:** 2026-06-14 (IMPL_PLAN_MEAL_PLANS review; new rule R-014 / ADR-009)
- **Type:** follow-up
- **What:** New engineering rule **R-014** says adoptable features that aren't
  yet configured/enabled should be **shown disabled with a "not set up" hint**,
  not hidden — so users discover they exist. The meal-plan builder's Email
  button adopts this in C-2.J. The rest of the app needs a sweep: most notably
  the **scanning button**, which today is *hidden* when `scanning_enabled` is
  off (ADR-002) and per the user should now render **disabled-with-a-hint**
  instead. Audit other gated/`v-if`-hidden adoptable surfaces (LLM/assistant
  affordances, any integration entry points) and convert the *presentation* of
  the off state from hidden → visible-disabled where it makes sense (R-014
  carve-outs: genuinely inapplicable or security-sensitive surfaces stay hidden).
- **Why deferred:** out of the meal-plans scope (R-007); it's a cross-cutting
  presentation change touching the scanning gate + others.
- **Recommended resolution:** opportunistic / a focused small sweep — pair with
  the next touch of each gated surface, and update ADR-002's note to point at
  R-014 for the presentation of the off state.

## [OPEN] FU-169 — Implement the test-suite improvements proposal
- **Raised:** 2026-06-13 (post-FU-166 proposal)
- **Type:** deferred job
- **⚠️ CI policy (2026-06-30):** the entire contents of
  `.github/workflows/ci.yml` and `release.yml` are intentionally
  commented out to preserve the user's GitHub Actions free-tier
  allowance during rapid Claude-driven development. **They must stay
  disabled while that cadence continues.** Do not un-comment them as
  part of any other prompt without an explicit user decision; the cost
  is per-push minutes on a free-tier account. When the user is ready
  to spend the minutes, this FU is the natural home for the revival —
  see also [[FU-327]] which depends on CI for its Windows/macOS matrix.
- **What:** `docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md` — phased
  plan to make the suite a trustworthy net: **Phase 1 (P0)** CI runs all tests
  (not just `tests/e2e/dora_api`) + pytest config (`xfail_strict`,
  `filterwarnings`, markers) + `pytest-cov` + shared `assert_problem`/
  `assert_envelope` matchers + one naming convention; **Phase 2** per-test DB
  rollback (isolation → kills order coupling, enables `xdist`) + data
  factories + parametrize; **Phase 3** close the 24 untested API surfaces +
  domain/repository/contract tests; **Phase 4** frontend Vitest +
  `merchant_api`/`emailer` fixture tests + Hypothesis + Postgres CI.
- **Why deferred:** sizeable; needs user prioritisation. Each phase ships
  independently green.
- **Recommended resolution:** start **Phase 1** opportunistically (half-day,
  no-regret); sequence the rest per the proposal. Relates to FU-045 (Postgres
  CI, Phase 4) and FU-161 (Aldi scraper — Phase 4 gives it a net).
- **Update 2026-06-29 — Phase 1 partially landed (no-deps slice).** Done in
  this session:
  - **`pytest.ini`** at repo root: `testpaths = tests` (so bare `pytest`
    collects unit + e2e), `xfail_strict = true`, `addopts = -ra`, the
    `unit`/`e2e`/`slow`/`scraper` marker registry, and `filterwarnings`
    silencing the fuzzywuzzy and pytest-asyncio noise the proposal §3.9
    flagged.
  - **Shared response matchers in `tests/support.py`** — `assert_problem(resp,
    status, *, field=None, detail=None, title=None)` and
    `assert_envelope(resp, *, expect_total=None)`. Returns the parsed body /
    items so callers can drill deeper without re-parsing.
  - **Naming convention codified** as R-023 + ADR-019 in ENGINEERING_STANDARDS:
    `test__<unit>__<condition>__<result>`, per-edit migration policy (don't
    open a rename-all PR).
  - Suite still 538/541 green (3 failures are FU-328 pre-existing; the
    flaky 4th from earlier passed under this run's ordering).
- **Still owed for Phase 1** (each needs a user decision):
  1. **`pytest-cov` reporting** — adds a pip dep and slows runs ~10-20%;
     proposal says "no gate yet" so it's report-only. Want me to add it?
  2. **Un-comment `.github/workflows/ci.yml`** — the entire workflow has
     been commented out since `20176e8` ("Comment out github workflows
     temporarily") and CI hasn't run since. Phase 1's "CI runs the whole
     suite" can't land without first un-commenting, then changing
     `pytest tests/e2e/dora_api` → `pytest`. This is the bigger ask.
  3. **Retrofit ~40 inline problem-detail assertions** to use
     `assert_problem` — R-023 explicitly says "per-edit migration, don't
     open a rename-all PR", so this is intentionally not done as a sweep.
     The matchers are available for any new test or any old one that gets
     touched.

## [OPEN] FU-161 — Shopping list drag-and-drop "index off" (feedback L414) — confirm in browser
- **Raised:** 2026-06-12 (shopping-list UX design session; original report L414, 06-Jun feedback)
- **Type:** finding (reported defect, not reproduced in static read)
- **What:** "Drag and drop is an index off somehow (wrong items being swapped)."
  *2026-06-12 update:* a deeper read found the fix **already shipped in P6-01
  Chunk 6** — `onLineDrop` carries a comment explicitly correcting the
  "subtract 1 when dragging down" off-by-one, and UX v2 preserved that logic
  verbatim. Per the reported-defect rule it stays open until verified in the
  running app (now part of the FU-165 checklist).
- **Recommended resolution:** confirm in browser (FU-165).

## [OPEN] FU-358 — Check / upgrade the Aldi scraper (site appears updated)
- **Raised:** 2026-06-12 (user note during Phase 1 wrap-up)
- **Type:** deferred job
- **What:** User flagged that Aldi's website appears to have
  changed; the existing Aldi scraper in the companion / merchant
  scraping module likely needs revisiting. Concrete steps when
  picked up:
  1. Hit a representative Aldi product page in a browser, compare
     the live DOM to what the scraper's selectors expect.
  2. Run the scraper against a known SKU and inspect the result
     (price, size, on-special detection) — note any fields that
     come back null / wrong / missing.
  3. Decide whether it's a selector tweak or a structural
     rewrite. Aldi historically uses a different layout from
     Coles/Woolworths, so changes there can ripple more than a
     simple class rename.
  4. If structural: cross-check the merchant scraping posture
     (`RECONCILED_FINISHING_PLAN.md` Decision 1 — scraper is the
     companion-app-only path; the core repo doesn't ship live
     scrape).
- **Why deferred:** out of scope of the current finishing-pass
  stream; needs live URLs + the companion app to investigate
  properly.
- **Recommended resolution:** opportunistic — when the user
  next needs Aldi pricing data, or as a focused session in the
  companion repo.

## [OPEN] FU-108 — Reorder Cookbook overview filters by usefulness
- **Raised:** 2026-06-10 (FU-083 follow-up; user, after the bug pass)
- **Type:** finding / UX polish
- **What:** The filter bar in `RecipesOverview.vue` lays controls out
  in the order they were added, not in the order users reach for
  them. The chip cluster (Favourites / Cookable now / Have meals in
  pool / Planned), the numeric inputs, the single-select dropdowns
  (Collection / Cuisine / Category), and the multi-select pickers
  (Uses ingredients / Doesn't use / Dietary / Tools) should be
  ordered by how often users actually flip them — most-used first,
  long-tail later. Pure template reorder, no logic changes.
- **What "useful" means here (open):** the user reads this. A
  reasonable starting cut: **(1) Favourites, Cookable now,
  Planned, Have meals in pool** (the quick-pick chips stay first
  because they're zero-effort); **(2) Cuisine, Category** (single-
  select, common during "what should I cook tonight?"); **(3) Uses
  ingredients / Doesn't use** (when fridge-clearing); **(4) Dietary
  + Tools** (occasional); **(5) Meals ≥ / Missing ingredients ≤**
  (numeric refinement); **(6) Collection** (visual grouping, almost
  set-and-forget). Confirm before moving — the actual answer is the
  user's, not the data's.
- **Recommended resolution:** opportunistic — fold into the next
  pass that touches this template. 10-minute job.

## [OPEN] FU-095 — RecipeEditDialog (quick-create) has no structured-steps surface
- **Raised:** 2026-06-09 (Cookbook Chunk 6 impl)
- **Type:** follow-up
- **What:** The quick "New recipe" dialog (`RecipeEditDialog.vue`) only
  collects the basics — name, ingredients, cuisine/category, tags, tools,
  image. Structured steps were intentionally **not** added to keep the dialog
  lean for the common "create a stub then edit it" workflow. Users add
  structure via the detail page's Structured/Freeform toggle. If a future
  prompt makes the dialog the primary create path (or users complain about
  switching to detail), wire the `RecipeStepsEditor` into the dialog with
  the same `steps_mode` toggle.
- **Recommended resolution:** opportunistic / when next touching the dialog.

## [OPEN] FU-085 — Run + verify Cookbook Chunk 2 (tag taxonomy overhaul) in a real env
- **Raised:** 2026-06-09 (Chunk 2 implementation; nothing was run — no Python venv / node_modules on the Windows dev box)
- **Type:** finding / verification (blocks trusting Chunk 2)
- **What:** Chunk 2 is a large, unrun backend+frontend change (FK-ify cuisine/category, DietaryTag table, 3 CRUD endpoints + settings, tri-state filter). Verify, in order:
  1. `alembic upgrade head` applies cleanly on **SQLite and Postgres** (migration `a7d2f4c9e1b8`: batch-mode Recipe alter dropping cuisine/category strings + adding cuisine_id/category_id FKs, RecipeTag rebuild to dietary_tag_id, vocab seed). Also test `downgrade`.
  2. App boots — `verify_mappings()` passes for Cuisine/Category/DietaryTag + the reshaped Recipe (risk: the `_cuisine_id`/`_category_id` hidden-FK mapping + the selectin relationships).
  3. `repository.get(Recipe).all()` actually selectin-loads `recipe.cuisine`/`.category` (assistant + global_search depend on it; if not, they'll show null cuisine/category).
  4. Recipe create/update/list round-trips `cuisine_id`/`category_id`/`dietary_tag_ids`; `GET /recipes/tags` returns DB-backed tags (value = id) + disclaimer.
  5. Overview: cuisine/category single-selects filter; tri-state DietaryTagFilter cycles +/−/neutral and stays open; RecipeCard shows cuisine/category names + tag chips.
  6. Edit dialog + detail page: cuisine/category selects + dietary multiselect populate from existing recipe + save correctly; URL importer pre-fills matched cuisine/category.
  7. Settings → "Recipe tags & categories": create/rename/delete for all three vocabularies; usage counts + delete warnings; deleting a cuisine/category nulls recipes (SET NULL), deleting a dietary tag removes the links (CASCADE).
  8. Backup → restore round-trips Cuisine/Category/DietaryTag/RecipeTag in FK-correct order.
  9. Dora assistant: search_recipes/suggest_recipes still filter by cuisine + dietary tags (now Python-side / name-resolved).
- **Recommended resolution:** now / first thing once a working env is available — before building Chunk 3+ on top.
- **State note:** 2026-06-09 — first user browser pass: migration applied + app boots + settings CRUD + add-modal dietary tags all **confirmed working** (items 1,2,4,7 effectively ✅). Two gaps found: (a) overview filters unusable → split out as **FU-087**; (b) no dietary-tag editor on the detail page (only the add modal) → **fixed** (added a multiselect to `RecipeDetailPage.vue`, L264). Still to verify: items 3 (selectin), 5 (filters), 6 (detail-page tags), 8 (backup), 9 (assistant).
- **State note:** 2026-06-12 — second user browser pass surfaced
  five concrete findings split out as their own FUs (so FU-085
  doesn't become an umbrella for everything cookbook-shaped):
  - **FU-146** (RESOLVED this session) — GitHub-issues mentions
    swept out (repo private).
  - **FU-147** — detail-page dietary-tag picker doesn't
    pre-populate + chips clear after save (item 6 partial fail).
  - **FU-148** — Cookbook overview missing "time of day" filter.
  - **FU-149** — Cookbook overview missing "# ingredients"
    filter + sort axis.
  - **FU-150** — assistant chat-mode doesn't recognise dietary
    or cuisine queries (item 9 partial fail). RESOLVED 2026-06-12
    (minimal fix shipped). The structural redesign is folded into
    `docs/04_proposals/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md` §2.2.1
    rather than tracked as its own FU.
  FU-085 itself stays OPEN until items 3 (selectin), 5 (filters
  end-to-end), 6 (FU-147 fix verified), 8 (backup), 9 (FU-150
  minimal fix verified in-browser) are all green.

## [OPEN] FU-056 (partial) — Phase 2 ingestion EAN auto-populate
- **Raised:** 2026-06-07 (P6-02); slice 1 closed 2026-06-28 (hybrid model)
- **Type:** deferred job (Phase-2 scoped)
- **What's left after the 2026-06-28 hybrid landing:**
  - **Ingestion auto-populate** — when the ingestion API imports a
    retailer catalogue, it should populate `Barcode` from the feed's
    EAN/UPC field automatically so most barcodes resolve without manual
    registration. Just calls `POST /api/data/barcodes` with
    `product_id` set; logic + endpoint already in place. Blocked on the
    ingestion API itself.
  - **Product detail EAN field** — when the Products UI gets touched,
    add a single-EAN row (gated on `features.products`). Uses the same
    endpoint. Per-Product UNIQUE constraint already enforced
    server-side ("one Product = one EAN").
- **Recommended resolution:** Phase 2 ingestion + the Products UI work,
  whichever lands first.

## [OPEN] FU-044 — C-help opt-in help-overlay brief written; awaiting approval + per-surface hint rollout
- **Raised:** 2026-06-06 (user-floated idea → `PROPOSAL_HELP_OVERLAY.md`)
- **Type:** deferred job (design brief done; implementation pending approval)
- **What:** A persistent "?" toggle overlaying dismissible per-element "what does
  this do" hints — the opt-in inverse of the forced tour C-5 removed. Net-new
  cross-cutting front-end component (no existing tour/coachmark system). The
  expensive part is **content** (a hint per control, kept from rotting), so the
  brief defers the hint corpus to a per-surface rollout folded into each C-1..C-9
  implementation prompt.
- **Why deferred:** brief-only per the Wave-C ritual; no code until the user
  approves and resolves §4 open decisions (reveal style, content model, mascot,
  discoverability).
- **Recommended resolution:** **when the user approves the brief** — build the
  mechanism + `v-help` directive first (§8.1), then seed hints on the highest-
  confusion surfaces, then roll out per-surface as each C-brief implements. Pair
  the C-5 finish-card mention (§4-4) with C-5 implementation.

## [OPEN] FU-043 — C-locale international-readiness brief written; awaiting approval
- **Raised:** 2026-06-06 (user-floated idea → `PROPOSAL_LOCALE_I18N.md`)
- **Type:** deferred job (design brief done; implementation pending approval)
- **What:** Make Dora usable outside Australia. Companion split solves product
  sourcing; Dora-core still has AU residue — hardcoded `$` currency, `en-AU` voice
  default (`useVoiceInput.ts`), AU merchant branding/copy/seed in core, and a
  **dormant vue-i18n scaffold** (installed in `boot/i18n.ts`, locale hardcoded
  `en-US`, stub messages, zero `$t()`). Brief recommends Layer A (currency/format
  neutrality) + Layer B (de-AU core) now; Layer C (full UI translation) deferred.
- **Why deferred:** brief-only; no code until approval + §3 open decisions
  (currency home, vue-i18n adopt-vs-rip, C-10 currency field, merchant-logo fate).
- **Recommended resolution:** **when the user approves** — fold the currency
  setting + shared money formatter into the C-cross config work (they share the
  config layer); coordinate the C-10 currency field with the ingestion impl;
  de-AU (voice/branding/seed) is independent and low-risk. Layer C stays parked.

## [OPEN] FU-041 — Onboarding "you already have groups/locations" copy on first-run
- **Raised:** 2026-06-06 (C-5 brief; feedback L32/L33)
- **Type:** finding (reported defect — didn't reproduce statically)
- **What:** User reported the seed step says "You already have some groups set
  up…" / "You already have locations…" during *first-time* setup. Static read
  shows that copy is gated on `has_groups`/`has_locations` (`onboarding.py:94-117`,
  `WelcomeWizard.vue:161-172,195-205`), which are false on a truly-empty DB — so it
  shouldn't render on a clean install. The user likely had dev/seed data or a prior
  seed run. No migration pre-creates *user* groups/locations (confirmed).
- **Why open:** the report came from real usage; a static read isn't proof.
- **2026-06-16 (C-5.1) re-confirm:** re-read the initial migration
  (`6e127e3cfa54`) — it only `bulk_insert`s **stock levels** and `create_table`s
  StockGroup/StockLocation (schema, no rows). The 8d3f/e9c2 migrations are
  schema-only. So **no migration inserts group/location rows**; the "already
  have" copy can only fire against `seed_dev_data()` output (dev dataset). Still
  needs a live clean-DB confirmation per the reported-defect rule.
- **Recommended resolution:** **confirm in browser** on a genuinely fresh DB
  (register first user → onboarding) that the "already have" copy does NOT appear
  and the seed checkboxes are enabled. If it DOES appear, find what's seeding user
  groups/locations and fix. **Folded into FU-192** (C-5.1 browser smoke).

## [OPEN] FU-032 — C-2: allocation count doesn't decrement after planner drop (live repro, root cause TBD)
- **Raised:** 2026-06-06 (C-2 recon); user repro confirmed 2026-06-12
- **Type:** finding (real bug, not yet root-caused)
- **What:** User dragged recipes from the palette onto future days; the
  chip's count next to the recipe name didn't change. Static read of
  the data path looks correct end-to-end:
  - Frontend `MealPlansOverview.onDropOnDay` → `persistEntries` →
    `mealPlanStore.updateMealPlanAsync` awaits the PATCH **and** the
    follow-up `getMealPlansAsync`, then in parallel
    `recipeStore.getRecipesAsync()` runs.
  - Backend `UpdateMealPlanHandler.handle` calls `save_changes()`
    before returning (commit guaranteed).
  - Backend `_hydrate_unallocated` (`get_recipes.py:591`) issues one
    GROUP BY against `MealPlanEntry` filtering
    `consumed_at IS NULL AND scheduled_for >= today AND recipe_id IN :ids`
    and subtracts from `available_meals`.
  - Frontend chip ([MealPlansOverview.vue:101](web_app/src/pages/MealPlansOverview.vue#L101))
    is `(N) = recipe.unallocated_meals` bound through
    `storeToRefs(recipeStore).recipes` — reassigning `recipes.value` in
    `getRecipesAsync` should trigger re-render.
- **Possible runtime causes (none verifiable without devtools):**
  1. **User is reading `available_meals` not `unallocated_meals`.** The
     chip shows `(unallocated_meals)` next to the recipe name; the
     click-menu shows `available_meals` as the big number. Drops only
     decrement `unallocated_meals` (cooked pool unchanged — that only
     moves on Cook / ± adjust). Worth confirming which number the user
     is tracking.
  2. **Reactivity edge case** with `storeToRefs` + sorted array
     reassignment. Unlikely but only visible at runtime.
  3. **`scheduled_for` date comparison** — backend filters
     `scheduled_for >= :today` using `date.today()` (server local).
     Drops on "today" land on the boundary; future drops shouldn't be
     affected. Cross-timezone client/server could in theory miss a
     same-day entry — unlikely with future drops.
- **C-2 redesign cross-ref:** `PROPOSAL_MEAL_PLANS.md §3.1` re-renders
  the same numbers (`(unallocated / pool)` chip — emphasised on the
  recipe row) and `§3.2` reworks the entry chip shape. The C-2 work is
  **design only — no impl plan yet**, so the chip surface in production
  isn't going to change soon. Don't defer the bug fix to "when C-2
  lands."
- **Recommended resolution:** when the user is next at a browser:
  1. Confirm whether the unchanging number is the `(N)` next to the
     recipe name (real bug) or the bigger `{{ available_meals }}` in
     the click-menu card (expected behaviour, not a bug).
  2. If the `(N)` is genuinely stuck, capture the network response from
     `GET /api/recipes` immediately after the drop — does the JSON
     show the new `unallocated_meals`? If yes, it's a frontend
     reactivity bug; if no, it's the backend's SUM not seeing the new
     row (transaction visibility / date filter).
  3. With that one bit of evidence the root cause collapses to either
     a Vue reactivity patch or a backend date / commit-visibility fix.

## [OPEN] FU-025 — A6 text scale: many surfaces still don't respond (likely needs its own sweep)
- **Raised:** 2026-06-05 (A6); user-verified gap 2026-06-12
- **Type:** finding (real, app-wide)
- **What:** Initial A6 in-browser check (2026-06-12) confirmed the scale
  steps themselves are working at the page level, BUT user observed that
  **a lot of secondary text still doesn't change size** when the scale is
  changed — e.g. **button labels, input text, toggle labels**, and likely
  other component-internal text. These almost certainly use Quasar's
  component CSS (`font-size` declared inside `.q-btn__content`,
  `.q-field__native`, `.q-toggle__label`, etc.) which doesn't inherit from
  the page-level rem-scaling tokens A6 set up. Fixing this is broader than
  any single page — likely a Wave-A-style "global pass" prompt that
  overrides the component-internal font-sizes to track the text-scale
  variable (or replaces hard-coded px with the same `rem`/var the body
  text already uses).
- **Why deferred:** out of FU-025's verify scope; needs its own sweep.
- **Recommended resolution:** now-ish — promote into a small Wave-A-shaped
  prompt ("A6b: text-scale follow-through into component-internal text").
  Audit method: grep `font-size` in `web_app/src/css/quasar.variables.scss`
  / overrides, plus a runtime walk through Stock Overview + a form-heavy
  page (Recipe edit, Stock-item detail) at Small vs Extra-large; list each
  surface that doesn't visibly change and convert its `px` to the same
  text-scale var. Deliberately-fixed-px carve-outs (ScanOverlay camera UI,
  PriceHistoryChart SVG labels, Dashboard 3px/7.5px micro-gauge) stay.


## [OPEN] FU-010 — Late-game holistic theme / colour / overall-look review
- **Raised:** 2026-06-05 (user request)
- **Type:** finding / deferred job
- **What:** A dedicated end-to-end pass over all themes, colours, and the overall
  visual feel of the app — viewed as a whole, in the browser, across the full
  theme set — rather than the per-chunk token work done piecemeal in A1/A1b.
- **Known input — Pesto looks over-dulled:** the user believes Pesto was dulled
  *too far*. Likely cause: the brightness tuning in A1b happened while a theme-logic
  bug was overriding the new values (the `themeService.ts` `THEMES` dict clobbering
  `themes.scss` via `setCssVar` — see the 2026-06-04 A1b round-2 worklog entry and
  the structural fix tracked in [[FU-004]]). So the dulling may have over-corrected
  against values that weren't actually rendering. Now that Pesto/Pesto Dark were
  synced, the *final* dulled value should be re-judged from scratch.
- **Also feed in:** other light themes' `--text-muted` contrast nudge ([[FU-003]]),
  and the structural dual-source collapse ([[FU-004]]) so the review isn't fighting
  a moving target.
- **Why deferred:** look-and-feel polish is best judged late, in one sitting, on a
  near-final app — not litigated token-by-token mid-build.
- **Recommended resolution:** later — a dedicated pass during **Phase 3 (champion
  polish)** or just before **Phase 4 (commercialize)**, once the app is feature-
  complete enough to eyeball holistically. Requires the app actually running
  (deps installed) and ideally a side-by-side across all themes.

## [OPEN] FU-003 — Other light themes' `--text-muted` contrast nudge
- **Raised:** 2026-06-04 (A1b)
- **Type:** follow-up
- **What:** only the Pesto family got the `--text-muted` 50→42 lightness bump.
  Other light themes (Lemon Tart, Blueberry, Cherry Cola light, Sourdough light)
  may want the same for AA contrast.
- **Why deferred:** wanted to eyeball Pesto first before touching the whole family.
- **Recommended resolution:** later during a dedicated A1b contrast pass, after the
  user has eyeballed the themes.

