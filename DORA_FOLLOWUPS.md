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


## [OPEN] FU-526 — Stocktake queue 500s (and alerts bell breaks) while any item snooze is active, on SQLite
- **Raised:** 2026-07-10 (found by the new `test_stocktake_router.py` suite; pinned by strict xfail).
- **Type:** finding (real user-visible bug — the worst of the sweep's finds).
- **What:** [dora_api/features/stocktake/stocktake.py:318](dora_api/features/stocktake/stocktake.py) compares `item.snoozed_until > now_` — SQLite loads the column tz-naive while `now_` is tz-aware, so the compare raises `TypeError`. `GET /api/stocktake/queue` returns 500 for as long as any snooze is active, and the alerts feed shares `resolve_overdue_map`, so the alerts bell breaks too. Postgres unaffected (tz-aware round-trip).
- **Recommended resolution:** **now / next stocktake touch** — normalise on load (or compare via a shared naive-UTC helper), flip the strict xfail green, and browser-verify snooze → queue → bell on a SQLite install. Same clock-mix family as [[FU-525]].

## [OPEN] FU-527 — noload relationships silently read as empty in two more count paths (reports fallback, stock-group item_count)
- **Raised:** 2026-07-10 (found by the new reports + stock-group e2e suites).
- **Type:** finding (real bugs, quiet wrong numbers; third incident of the noload family — ADR candidate, see below).
- **What:** two independent sites read a `lazy="noload"` relationship without `.include(...)`, so it's silently `None`/empty:
  1. [dora_api/features/reports/reports.py:588](dora_api/features/reports/reports.py) — the keeps-running-out fallback fetches items without `.include("stock_level")`, so items with no `StockLevelChange` history read `stock_level=None` and are dropped from the tally (pinned by strict xfail).
  2. [dora_api/features/stock_groups/manage_stock_groups.py:57](dora_api/features/stock_groups/manage_stock_groups.py) — the list's `item_count` buckets via the noload `item.stock_group`, so it's always 0 (delete's SQL-counted `items_affected` is correct; pinned with a comment).
- **ADR candidate:** this is the third noload-reads-as-empty incident in one day (the cookbook-filter identity-map bug fixed 2026-07-10 is the same family). If one more appears, promote a standing rule (e.g. "every read of a noload relationship must sit behind an `.include` on the same query, and relationship-dependent maps load before any plain entity load in the same request").
- **Recommended resolution:** opportunistic per surface — add the missing `.include`s, flip the xfail, delete the pinning comments.

## [OPEN] FU-528 — str/UUID dict-key mismatch: tool + dietary-tag delete responses always report 0 recipes affected
- **Raised:** 2026-07-10 (found by the new taxonomy-router e2e suites; pinned with comments).
- **Type:** finding (real bugs, cosmetic blast radius — the delete itself works, the count in the response is wrong).
- **What:** [dora_api/features/tools/manage_tools.py:178](dora_api/features/tools/manage_tools.py) and [dora_api/features/dietary_tags/manage_dietary_tags.py:192](dora_api/features/dietary_tags/manage_dietary_tags.py) do `counts.get(id, 0)` where the dict is keyed by `UUID` but the Flask path param is `str` — always 0. Same family as the FU-463 UUID-bind sweep.
- **Recommended resolution:** opportunistic — coerce the path param to `UUID` at both sites and strengthen the pinned assertions to the real counts.

## [OPEN] FU-529 — Reconcile "latest receipt" ordering has no deterministic tie-break; transient idempotence flake observed
- **Raised:** 2026-07-10 (observed live: `test__same_verb_replay_is_idempotent` failed in three consecutive runs in a ~10-minute window, then stopped reproducing — 5/5 green after, incl. the full suite).
- **Type:** finding (didn't re-reproduce; logged per the reported-defect rule rather than dropped).
- **What:** `_latest_receipt` in [dora_api/features/meal_plans/reconcile.py:409](dora_api/features/meal_plans/reconcile.py) (and the queue's correlated `r2.created_at > r.created_at` subqueries) order receipts purely by wall-clock `created_at`. A same-timestamp tie or a clock step backwards (Windows time sync is the prime suspect for the observed window) makes "latest" ambiguous — the sweep's `unresolved_auto` receipt can read as newer than the user's verb receipt, so a same-verb replay returns `idempotent: false` and writes a duplicate receipt. Debug dump during the window confirmed receipts + timestamps were well-formed 11 ms apart once the window passed.
- **Recommended resolution:** next reconcile touch — give receipts a deterministic order (monotonic sequence column, or at minimum a stable secondary sort key that works on both SQLite and Postgres per R-005), then re-run the file in a loop to confirm. Until then, treat a solitary failure of this test as this FU, not a regression.

## [OPEN] FU-522 — Change-email plain-text body links the wrong route (`/verify-email` instead of `/confirm-email-change`)
- **Raised:** 2026-07-10 (found by the FU-520 emailer test pass; static read, not yet reproduced live).
- **Type:** finding (likely real bug).
- **What:** in `request_email_change` ([dora_api/features/auth/email_flows.py:346](dora_api/features/auth/email_flows.py)) the HTML body rewrites the confirmation link to `/confirm-email-change` (line ~344), but the **plain-text** body uses the un-rewritten `build_verify_url(raw_token)` pointing at `/verify-email` — a change-email-purpose token delivered to the wrong route for text-only mail clients. The token purpose likely fails validation on that route, dead-ending the flow.
- **Also, while there (minor R-001):** [dora_api/features/users/change_password.py:111-126](dora_api/features/users/change_password.py) hand-rolls its own try/except-log around `send_email` instead of reusing `auth_helpers.try_send`.
- **Recommended resolution:** now-ish / next auth-surface touch — build the text link from the same rewritten URL as the HTML body, add a regression test beside the new `tests/test_email_sender.py` suite, then confirm the change-email flow end-to-end in browser.

## [OPEN] FU-523 — `Contains`/`StartsWith` invert `case_sensitive` on the value side; case-sensitive LIKE impossible on SQLite
- **Raised:** 2026-07-10 (found + pinned by the new `tests/test_sqlalchemy_repository.py` suite).
- **Type:** finding (real bug in shared query machinery, low blast radius today).
- **What:** [dora_api/persistence/bool_operation.py:143,155](dora_api/persistence/bool_operation.py) lower-case the search **value** when `case_sensitive=True` (compare `BoolOperation._resolve` line 19, which lowers when NOT case-sensitive — the flag is inverted on the value side). Independently, SQLite's `LIKE` is ASCII-case-insensitive regardless, so `case_sensitive=True` substring matching can't work on SQLite at all and is doubly broken (value pre-lowered) on Postgres. Pinned by two `@pytest.mark.xfail(strict=True)` tests — flipping them green is the done-signal.
- **Impact today:** no production callsite appears to pass `case_sensitive=True` to Contains/StartsWith, so this is latent — but it's exactly the kind of trap the R-005 SQLite/Postgres portability posture says to fix or document.
- **Recommended resolution:** opportunistic, next time `bool_operation.py` is touched — fix the inversion, and either implement case-sensitive LIKE portably (SQLite `GLOB`/`BINARY` collation vs Postgres `LIKE`) or drop the flag from the two operators and document them as always-insensitive.

## [OPEN] FU-524 — `normalise_unit` is not idempotent (`strip()` runs before the `°` removal)
- **Raised:** 2026-07-10 (found by the new Hypothesis property suite `tests/test_domain_properties.py`).
- **Type:** finding (real but minor).
- **What:** [dora_api/domain/units.py:338-341](dora_api/domain/units.py) does `strip().lower().replace("°", "")` — removing the degree mark can re-expose end whitespace, so `normalise_unit("gas °")` → `"gas "` (≠ `normalise_unit(normalise_unit(...))`). Impact: inputs like `"gas °"` / `"° C"` miss their `UNIT_TABLE`/gas-mark alias lookups and return None. Pinned by a deterministic `xfail(strict=True)`; the property-test strategy excludes `°` with a loud comment until fixed.
- **Recommended resolution:** opportunistic one-liner next time `units.py` is touched — strip **after** the replace, delete the xfail + strategy carve-out.

## [OPEN] FU-525 — Buy-verdict wait-hint mixes UTC sample dates with household-local `today` (possible one-day drift)
- **Raised:** 2026-07-10 (surfaced while fixing the same mix in `tests/test_buy_verdict.py`, which flaked every AEST morning).
- **Type:** finding (production nuance, unconfirmed impact).
- **What:** `_wait_hint` / `_price_axis` in [dora_api/features/stock_items/get_buy_verdict.py](dora_api/features/stock_items/get_buy_verdict.py) derive low-dates via `ts.date()` on **UTC** observation timestamps while `inputs.today` is the household-local calendar day (R-021). For UTC+10 households, any observation recorded before 10am local lands on the previous UTC calendar day, which can shift the predicted "next low" date by a day (cosmetic — the hint is "~every N days") and, at the edge, flip the `next_low <= today` staleness check. The test-side fix (2026-07-10) anchors test samples to local-noon; the production data path still mixes the two clocks.
- **Recommended resolution:** discussion / next buy-verdict touch — either convert observation timestamps to household-tz before `.date()` (R-021-consistent) or accept the ±1-day fuzz with a comment. Not worth its own unit; the hint is deliberately approximate.

## [OPEN] FU-521 — Alert-action toast + kind exhaustiveness sit in three copies (R-003 drift, senior-review track)
- **Raised:** 2026-07-10 (surfaced during FU-357 close-out — user hit the divergent-toast + missing-kind bug live).
- **Type:** finding (state-ownership drift).
- **What:** the same "user taps an inline alert action" mutation is wired three separate times in the SPA — [`DashboardPage.vue:1833`](web_app/src/pages/DashboardPage.vue) `applyAlertAction`, [`AlertsBell.vue:175`](web_app/src/components/AlertsBell.vue) `apply`, [`AlertsPage.vue:328`](web_app/src/pages/AlertsPage.vue) `onAction`. Same API call, three hand-rolled toast pairs, three refresh recipes. The bug that exposed this (Dashboard silently swallowed both success and error toasts) was fixed inline but the shape stays — the next surface added will re-invent it a fourth time. Also: the `AlertKind` union + its five switch sites (`iconFor` / `colorForKind` / `kindTheme` / `actionsFor` / `linkFor` in [`alert.ts`](web_app/src/models/alert.ts)) are three separate lists that must agree, but nothing enforces it — that's exactly how the 2026-07-10 crash happened (`meal_reconcile_overdue` added on the backend by FU-317 Chunk 4 without extending the union, so TS couldn't warn about the five missing cases). Fixed inline with a defensive `?? []` in `AlertRow`, but the pattern is fragile.
- **Why deferred:** two clean options — (a) extract a `useAlertActions()` composable that owns the applyAction + refresh + toast triad, then have all three surfaces call it (mirrors `useStockItemActions` / `useShoppingListActions`); (b) collapse the five per-kind switches in `alert.ts` into a single `ALERT_KIND_META: Record<AlertKind, {icon, color, theme, actions, link}>` so a new kind lands as one row instead of five cases. Both are Effortless + Anti-creep-safe R-003 wins and both are exactly the shape the finalisation-plan senior-review track (§3.3) is designed to consolidate. Doing them right now is scope-creep on a bug fix.
- **Recommended resolution:** **fold into [FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md) Chunk 9 (Alerts + Suggestions)** — the senior-review section for that chunk names both refactors, verdicts them, and either ships or logs. If either is `keep`, note why.
- **Cross-ref:** [[FU-510]] (hand-rolled vs library — same discipline, different surface), FU-357 close-out (state note lives in `_RESOLVED`).


## [OPEN] FU-520 — Test-suite improvements Phase 4: frontend Vitest + Hypothesis + Postgres CI + scraper/emailer fixture tests
- **Raised:** 2026-07-09 (split from FU-169 close-out).
- **Type:** deferred job (large — should be its own multi-session unit).
- **What:** the Phase-4 slice of [`docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md`](docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md) §5.E-F P2. Status after the 2026-07-10 targeted sweep:
  1. **Frontend Vitest + Vue Test Utils — SHIPPED incl. first component tests (2026-07-10, two passes).** 9 util/composable spec files (139 tests) + `stockLevelDot.spec.ts` (11 component tests over both StockLevelDot components) → 203 total, ~1.5s. The Quasar component-mount pattern is now established in `vitest.config.ts` + that spec: `@vitejs/plugin-vue` wired, `quasar` aliased to its client bundle (the SSR bundle throws under vitest), real Quasar components registered per-mount, per-file `// @vitest-environment jsdom` pragma. **Remaining:** `AddToListButton` (601 lines, API-coupled — needs service mocking) + shopping rail + lifecycle-coupled composables (`useMealPlanExport`, `useOfflineQueue`); all unblocked by the established pattern.
  2. **`merchant_api` scraper tests** against saved HTML fixtures — **still open**; the scraper lives in the sibling `dora-companion` repo, so this belongs there ([[FU-161]] Aldi net).
  3. **`emailer` tests — SHIPPED 2026-07-10.** `tests/test_email_templates.py` (13) + `tests/test_email_sender.py` (16): all 5 content templates + layout + autoescape, MIME assembly, SMTP wire choreography via fake transport, dry-run degradation, error propagation. Found [[FU-522]].
  4. **Hypothesis property tests — SHIPPED 2026-07-10.** `tests/test_domain_properties.py` (26): invariants over `recipe_cookability` (incl. the canonical *cookable ⇒ nothing required missing*), `stock_status`, `product_offer`, `units`. Found [[FU-524]]. `hypothesis` pinned in requirements.txt.
  5. **Postgres-backed CI test runs** once CI is un-commented ([[FU-405]] / `.github/workflows/ci.yml`) — **still open**. Note the commented workflow was fixed 2026-07-10 to run bare `pytest` (full suite) + `npm test`, so un-commenting inherits the right scope.
- **Recommended resolution (remaining):** component-level Vitest when a component surface next changes; scraper tests in the companion repo; Postgres CI with [[FU-405]]. **Recommended resolution point:** opportunistic per workstream.
- **Cross-ref:** [[FU-519]] Phase 3 (untested API surfaces) — separate; Phases 3 + 4 are proposal-parallel, not sequential.

## [OPEN] FU-519 — Test-suite improvements Phase 3: close coverage gaps
- **Raised:** 2026-07-09 (split from FU-169 close-out).
- **Type:** deferred job (large — should be its own multi-session unit).
- **What:** the Phase-3 slice of [`docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md`](docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md) §5.D. Status after the 2026-07-10 targeted sweep:
  1. **Domain-logic unit tests — CLOSED 2026-07-10 (honestly skipped).** `recipe_tags` / `generics` / `types` turned out to be a string constant, three TypeVars, and `EMPTY_UUID` — nothing behavioural to test; writing filler would violate the "green means correct" principle.
  2. **API e2e — effectively DONE 2026-07-10 (two passes).** Pass 1: `test_recipe_router.py` (found + fixed the identity-map filter bug), `test_meal_plan_router.py`, `test_dashboard_router.py`. Pass 2 (same day): `test_search_router.py` (12 — scoring order, per-type subtitles, types filter, per-type limit clamp), `test_waste_router.py` (13), `test_budget_router.py` (11), `test_reports_router.py` (15 — all 10 report endpoints), `test_stocktake_router.py` (16 — found [[FU-526]]), and the six taxonomy routers (cuisines/categories/dietary-tags/tools/stock-groups/recipe-collections, ~49 via shared `_taxonomy_crud.py`). Found [[FU-527]] + [[FU-528]]. **Remaining minor surfaces (opportunistic per-touch only):** locations tree router, client_logs, help, substitutes detail (metadata partially covered), suggestions detail, deals.
  3. **Persistence / repository tests — SHIPPED 2026-07-10.** `tests/test_sqlalchemy_repository.py`: paginate math, full operator matrix, field_map resolution, NOCASE sort, UUID round-trip, against a standalone SQLite fixture. Found [[FU-523]].
  4. **Contract / snapshot tests — SHIPPED 2026-07-10.** `tests/e2e/dora_api/test_dto_contracts.py`: 27 endpoints' response-key shapes pinned against `dto_snapshots.json` (self-seeding; refresh with `DORA_UPDATE_DTO_SNAPSHOTS=1` and commit the JSON diff — the diff is the reviewable contract change).
- **Recommended resolution (remaining):** the minor-surface tail per-touch as those surfaces change (matches R-023's per-edit spirit); add a `dto_snapshots.json` row whenever a new endpoint lands. **Recommended resolution point:** opportunistic per surface.
- **Cross-ref:** [[FU-520]] Phase 4 (frontend / Hypothesis / scraper / Postgres CI) — separate.


## [OPEN] FU-510 — Late-game sweep: hand-rolled code that should be a battle-tested library
- **Raised:** 2026-07-07 (user request).
- **Type:** deferred job (audit-first, then refactor).
- **What:** Full-codebase pass looking for **wheels we reinvented** — hand-rolled implementations of problems a well-known, well-maintained library solves better (correctness, security, ergonomics, performance). Focus areas to check (non-exhaustive):
  - **Security-adjacent:** custom CSRF double-submit vs Flask-WTF / Flask-SeaSurf, hand-rolled Fernet key handling vs `cryptography` recipes, the hand-rolled security headers (FU-459) vs Flask-Talisman, session/cookie hardening, password hashing choices.
  - **HTTP / API surface:** pagination + query-string parsing (`queryStringBuilder.ts`, `parse_query_options`) vs Flask-Smorest / API-spec libs; response envelope + error translation vs a marshalling lib; audit-retention + audit hooks.
  - **Data access:** the generic repository (`SqlAlchemyRepository`), `EntityField`, `include`/`then_include` chains — vs plain SQLAlchemy 2.0 selectinload/joinedload patterns. Is our wrapper carrying its weight or fighting the ORM?
  - **Domain infra:** unit conversion (`units.py`), locale display denominators, currency + locale formatting, timezone / calendar-day helpers (`household_today`), fuzzy matching (RapidFuzz already used, but check the wrappers around it).
  - **Frontend:** own drag-drop composables (`useDragDropList`) vs vue-draggable / dnd-kit; own toast/notify wrappers; own shortcut registry (`useShortcut`) vs a library; own offline queue (`useOfflineQueue`) vs Workbox background sync; own rollback registry vs a proper undo/redo stack lib.
  - **Ops:** log rotation (already time-based), scheduling (APScheduler in place), rate limiting (present? if hand-rolled, flag it), config layering (`ConfigurationManager`) vs pydantic-settings.
- **Method (two phases, do not skip Phase 1):**
  1. **Phase 1 — assessment only.** Produce `docs/05_investigations/HANDROLLED_VS_LIBRARIES.md` listing each hand-rolled site: what it is, what library would replace it, honest verdict `keep` / `replace` / `wrap-thin-adapter`, and rough effort/risk. **No code touched.** Verdict has to weigh Charter tie-breaks (Effortless + Anti-creep): sometimes the hand-rolled thing is right because it's smaller, has no supply-chain risk, and stays coupled to our domain. Do NOT default to "always prefer library."
  2. **Phase 2 — action.** For each `replace` verdict, open a per-item FU (or an implementation plan when the surface is broad, e.g. auth stack replacement). Sequence by risk + blast radius; ship one at a time with browser-verify per swap.
- **Why deferred:** late-game / pre-commercialization hardening. Not urgent while the app is still gaining new surfaces; do it when the feature surface has stabilised so a lib swap doesn't collide with in-flight redesigns. Doing it earlier risks churning code that's about to be reshaped anyway.
- **Recommended resolution:** **Phase 1 (assessment) rolled into [FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md) Track 3 as a per-chunk bucket** (§3.3 "Hand-rolled-vs-library verdicts"). Each chunk's senior-review section captures the `keep` / `replace` / `wrap-thin-adapter` verdict for the hand-rolled surfaces it walks past, using the shape this FU specified. The plan's close-out consolidates them into `HANDROLLED_VS_LIBRARIES.md`. **Phase 2 (per-swap actions) stays open on this FU** — each `replace` verdict spawns its own per-swap FU at plan close, sequenced by risk + blast radius. Pair the Phase-2 sequencing with [[FU-412]] COMMERCIALIZATION_REPORT + [[FU-409]] auth security re-audit + [[FU-424]] senior-review Tier-2 delta.


## [OPEN] FU-431 — Product History: deeper redesign brief (feature discoverability + desktop drawer pattern)
- **Raised:** 2026-07-01 (12-June feedback-audit delta).
- **Type:** deferred job.
- **What:** Product History has 10 bullets; B9.6 shipped 1 (chart-width fix); 7 are PROPOSED across A1/A6/B9/C-9. **2 remain NO_HOME:** **PH-1 "feature hidden away"** (surface-visibility redesign — how does a user land on Product History without knowing the URL?) and **PH-10 "drawer-style page on desktop"** (design open question). Deeper redesign has no brief. Overlaps with [[FU-227]] resolved "your prices" work but that closed the *stock-item* side, not the *product* side.
- **Why deferred:** briefs went to higher-priority surfaces; Product History is Products-layer, data-gated, so it only matters once real product data is ingested.
- **Recommended resolution:** discussion — decide whether a Product History redesign is worth its own brief (given the Products layer is data-presence-gated) or whether the "your prices" intel layer subsumes the user need. Wait until [[FU-214]] product-surface browser verify surfaces real usage patterns.


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

## [OPEN] FU-422 — Search: display which products already link to a stock item
- **Raised:** 2026-07-01 (original-spec sweep).
- **Type:** deferred job (dropped intent from original spec).
- **What:** Original spec (`docs/00_original_spec/Unprocessed Ideas (from Google Docs).md`) asked that when searching for products, the UI should visibly mark ones **already linked to a stock item** so the user isn't tempted to re-link. Search now lives in the companion, but the *linkage-display* rule may still belong in Dora (the "Products" tab on a stock item) or become part of the companion's ingestion contract. Decide where it lives.
- **Why deferred:** search moved to companion mid-flight; the rule was never re-homed.
- **Recommended resolution:** during any companion↔Dora ingestion-boundary work — call whether Dora surfaces "already-linked" itself, or the companion queries a Dora endpoint. If the latter, add to the ingestion API's read-side.

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


## [OPEN] FU-406 — P7-10 Launch readiness
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4 gate).
- **What:** `docs/06_legacy_prompt_plans/PROMPT_PLAN_PART_7_COMMERCIALIZATION.md §P7-10` — final launch-readiness checklist (marketing, legal, incident channels, escalation, on-call). Nothing done.
- **Why deferred:** last-mile.
- **Recommended resolution:** at Phase 4 finish. **Partially covered by [FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md)** — the FST document + release-gate checklist (Track 1) fulfil the *QA half* of P7-10 (the "have we actually verified this is ready?" tollgate). **Not covered** by the plan: marketing, legal, incident channels, escalation, on-call. Those remain in this FU's scope and want their own work-unit.

## [OPEN] FU-405 — P7-09 Ops (observability, CI/CD deploy, staging, backups)
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-09 — production ops. CI is deliberately disabled in this repo (`.github/workflows/*.yml` commented out to preserve GH free-tier — see memory `feedback_ci_disabled_policy`). Observability, staging, backups all unplanned. **Do not silently re-enable CI as part of this** — separate call.
- **Why deferred:** Phase 4 + CI-cost policy.
- **Recommended resolution:** Phase 4 — pair with billing (P7-06) so ops cost lands with revenue.
- **Note (2026-07-09, FU-387 audit):** when CI is re-enabled at Phase 4, wire in dependency scanning as part of this FU — a scheduled `pip-audit -r requirements.txt` + `npm audit --prefix web_app` job that opens an issue on new advisories. FU-387 shipped a manual `scripts/security-audit.sh` runner as the interim; promoting it to CI belongs here, not in a fresh FU. See [SECURITY_REVIEW.md](docs/security/SECURITY_REVIEW.md) §6 for the current baseline the CI job should measure against.

## [OPEN] FU-404 — P7-08 Compliance (privacy policy, DSAR, deletion, security headers)
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-08 — full compliance surface. Partial: some security-headers work has landed; the privacy-policy hooks + full data-export/deletion (DSAR) contract not confirmed. Overlaps with [[FU-401]] (P5-02 Privacy).
- **Why deferred:** Phase 4.
- **Recommended resolution:** Phase 4 — merge P5-02 + P7-08 into one compliance work-unit. **Partially covered by [FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md)** — the multi-user + admin FST persona flows (Track 1) will *exercise* the DSAR export, delete-account, and privacy-policy surfaces end-to-end, and the senior-review pass on the auth + backup chunks will catch drift on security headers + credential exclusion. **Not covered:** the legal drafting itself + the compliance contract wording. Those remain in this FU.

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
- **What:** P5-06 — first-week experience: gentle nudges to complete profile, add first recipe, run first stocktake, etc. First-day onboarding shipped (C-5); first-week nudges not built.
- **Why deferred:** waiting on the alerts/dashboard-card model to firm up. *(2026-07-07: [[FU-352]] resolved with "keep Attention + Kitchen Health coexisting", so the launchpad-alerts fold-in path for these nudges is gone; they need their own venue.)*
- **Recommended resolution:** treat as a small standalone brief when picked up — likely a nudges list on the Attention card *or* first-week-only overlay chips, not a Score-card row. Deliberately not folded into any existing dashboard card; keep the first-week experience honest as a first-week experience, not a permanent gauge.

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
- **Recommended resolution:** revisit when alerts next opens. *(The FU-352 "fold alerts into the Dora Score card" fallback path was closed 2026-07-07 as won't-do — Attention + Kitchen Health stay as coexisting cards — so this FU no longer has that shortcut. Resolve on the Alerts surface itself when it's next touched.)*

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

## [OPEN] FU-366 — Deferred surfaces: Reports, Settings shell, Mobile view
- **Raised:** 2026-07-01 (Wave-C audit).
- **Type:** deferred job.
- **What:** `C_big_rock_design_briefs.md` "do not redesign yet" list. Dashboard has been pulled forward and shipped. **Reports, Settings shell, Mobile view** remain officially deferred — no briefs. Feedback for Reports is empty; Settings has some deferred bullets (see [[FU-365]] A-5); Mobile view has no direct feedback.
- **Why deferred:** deliberately parked.
- **Recommended resolution:** discussion at some future point — decide whether each stays parked forever or gets a brief. Not on a critical path.

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

---


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
  comes around, or after FU-046 (theme-token compliance) gets another round. **Ride-along with [FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md) Track 3** — every chunk's senior-review pass logs any `color="secondary" | info | accent"` sites worth reconsidering against this FU, so by plan close the shortlist is already assembled. Actual resolution still needs eyes-on-the-app judgement, not a code walk — so this FU stays open past plan close.

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
- **Also feed in:** the structural dual-source collapse ([[FU-004]]) so the review
  isn't fighting a moving target. (Note: FU-003 — the Pesto-only `--text-muted`
  42% bump — was reverted 2026-07-06; all light themes are back on the original
  50% baseline, so this holistic review starts from parity across the family.)
- **Why deferred:** look-and-feel polish is best judged late, in one sitting, on a
  near-final app — not litigated token-by-token mid-build.
- **Recommended resolution:** later — a dedicated pass during **Phase 3 (champion
  polish)** or just before **Phase 4 (commercialize)**, once the app is feature-
  complete enough to eyeball holistically. Requires the app actually running
  (deps installed) and ideally a side-by-side across all themes. **Ride-along with [FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md) Track 3** — every chunk's senior-review pass logs theme/colour anomalies against this FU so the eventual holistic pass starts with a triaged shortlist instead of a blank slate. Doesn't replace the eyes-on-app judgement pass; complements it.

