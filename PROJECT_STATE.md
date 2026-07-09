# Dashy Dora — Project State

**Regenerated: 2026-07-09** — hand-edited row refresh after **FU-450 + FU-451 shipped
end-to-end (6 chunks): the deal-quality signal (band enum + `fake_markdown` demotes a
price-driven Buy Verdict `buy`→`wait`; new money-gated `good_deal` alert + per-user
threshold, migration `d2f8a1c4b7e9`) and budget-defense **recipe** swaps (over-budget
week → ranked cheaper-recipe suggestions, preview→apply→undo via `MealPlanSwapLedger`,
migration `e3a9c7b1f2d8`; Suggestions panel + Dashboard signpost). **Product/brand swaps
CUT** — they needed per-item "usual product" upkeep the owner rejected. Recipe-cost
pricing extracted to a shared `recipe_cost` module (R-003). 30 new tests; full suite
886 pass / 9 pre-existing-unrelated fail. New open FU-516 (good_deal throttle is
stateless-freshness, not a stateful counter)**. Also **FU-432 resolved** — recipe
personal notes shipped (RD-29, migration `f4b2d8e6a1c3`, shown in cook mode under the
steps); RD-11 per-ingredient notes dropped (anti-creep), RD-3/RD-33 verified
already-done, RD-18 dup of FU-407. Earlier: **FU-515 assistant security triage (B.1 prompt-injection defence + B.3 tool-arg bounds + B.4 current_path sanitisation shipped; B.2/A.3/A.4 verified already-fixed; A.5/A.6/A.7 accepted; audit doc "✅ Fully triaged")**. Earlier same day: **FU-390 assistant eval suite (vitest stood up in web_app; 53-case Basic-mode corpus + 9 AI-path reliability tests; caught+fixed 3 real bugs incl. an orphaned `set_primary_list` tool) and FU-514 (onboarding seed-items 500 fix)**. Earlier same day: **FU-429 assistant-architecture reconciliation (SLM has landed → the big "capability registry + two routers" refactor deliberately NOT built per Effortless+Anti-creep; instead closed the highest-value gap by giving Basic mode its first action verb — typed "add milk"/"buy eggs and bread" now resolves against the pantry and adds to the primary list; §1 dup + §2.1 registry + mutation gate already satisfied. Related: FU-386 closed already-honoured, FU-390 eval suite unblocked+re-scoped, FU-360 subset shipped — hide-Dora setting, per-user greeting, chip sizing)**. Earlier same day: **FU-447 close-out (already-satisfied by [[FU-197]] 2026-06-30 — A.1 CSRF + A.2 email-change password-proof both fixed and pinned by tests; AUTH_ASSISTANT_SECURITY_FINDINGS.md doc header + priority table stamped with per-finding status; remaining 8 medium/low items carried forward as new FU-515)**. Earlier same day: **FU-512 close-out (unit-of-work sweep applied to 10 more handlers — `CreateMealPlanTemplate`, `CloneMealPlanTemplate`, `CreateSet`, `NewRecipeVersion`, `AutoGenerate`, `Seed` onboarding, `CopyShoppingList`, plus 3 shopping-list-template handlers; habit-commits deleted, `flush()` used where child inserts need FK visibility; 10 new happy-path e2e tests, all green; surprise pre-existing bug found in `SeedItemsHandler` logged as FU-514)** and **FU-513 close-out (GET /api/suggestions writes eliminated; snooze pruning moved to a daily APScheduler job)**. Earlier same day: **DI walk-back (R-031 / ADR-027 — `DependencyContainer` deleted; 175 handlers rewritten to constructor injection typed against a `Repository` Protocol; ~200 `get_container().inject(X)` callsites rewritten; `dependency_injector` dropped; FU-457 dissolved by construction; 828 pass / 2 pre-existing fail — 0 regressions)**, **FU-456 (`create_recipe` unit-of-work refactor — 5 commits → 1, 3 new e2e tests, FU-512 opened for the sweep of remaining multi-commit handlers — now closed)**, **FU-500 (R-029 hide-don't-nag sweep — Product Search nav flipped to hide, MenuButtonProps shed disabled fields, 17 R-014 comment refs audited)**, and **FU-504 (base-component sweep — 40 raw `<q-btn>` migrated, `BaseButton` gains `filled-icon` variant + `color` prop)**. Prior refresh: **2026-07-06** — hand-edited row refresh after **FU-333 close-out (env-var sprawl finished; Buckets C + D + fallback drop)**, **FU-502 (locale/currency backend coverage tests)**, **FU-503 / FU-044 (help chips shipped)**, and **FU-043 (Locale
& international readiness Layers A + B)** shipped end-to-end: install-wide
currency + locale on `AppSetting`, one shared `Intl.NumberFormat` wrapper
routing every money render, voice-input locale following the setting, AU
merchant name-drops removed from assistant copy, new admin **Settings → System
→ Currency & locale** page. Also earlier the same day: **FU-003** resolved by
reverting the Pesto `--text-muted` bump instead of propagating it. Baseline
below is unchanged from the 2026-07-04 full rebuild.

**Original regen note (2026-07-04):** — full dashboard rebuild after a long session
that shipped the **Stocktake mode redesign trilogy** (Chunks 1–3
end-to-end from `PROPOSAL_STOCKTAKE_MODE.md`), the **stocktake
housekeeping pass** (retired the dead `locations/attention.py` heatmap +
dropped two deprecated columns via alembic `e5c8b3a1f4d2`), and
resolved **7 follow-ups**: FU-226 (queue-rules assessment → became the
proposal), FU-430 (redesign brief written), FU-455 (buy-verdict
all-thin-axes test drift fixed), FU-464 (auto-add-when-low regression
from the 3-band collapse), FU-463 (two more SQLite `text()+str(uuid)`
zero-row sites rewritten), FU-458 (per-user rate limits on
`/assistant/ask` + `/act` + `/confirm`, extending `auth_helpers.rate_limit`
with an optional `subject` arg), and FU-421 (closed as
already-satisfied — existing expiry surface covers the "remind me to
use this" spec ask). Backend pytest: **303/303 green** (was 297/298 at
session start — 5 new tests, 1 pre-existing failure eliminated).
`vue-tsc --noEmit`: clean throughout (only pre-existing Capacitor
typing errors from the P8-10 native scaffold on this dev box).
Migration head-count: 1 (was 2 — Chunk 1's `d1f9c3a8b2e4` merged the
divergent 07-03/07-04 heads and Chunk-house `e5c8b3a1f4d2` chained
cleanly). Session's front-door is the single **PROPOSAL_STOCKTAKE_MODE.md**
brief; every decision it locks is live in code.

This is the single front door: where every phase and workstream is up
to, and what needs your attention. For *where things stand* this doc
wins; for *how/why* a decision was made, follow the linked planning
doc. Regenerated after each substantive close-gate (see
`CLAUDE.md → Regenerating PROJECT_STATE.md`); if it looks out of date,
the last session skipped its close-gate — trust `DORA_WORKLOG.md` +
`CHANGELOG.md` over it.

Status key: ✅ done · ➗ done, with skipped/deferred items · 🟡 in progress ·
🔵 designed, not built · ⚪ not started · 🔴 needs your decision · 🕸 stale doc.

---

## Where we are right now

Phases **0** and **2** are effectively done: foundations, and the
ingestion API + standalone companion. **Phase 1** just closed a big
outstanding piece — the **stocktake-mode redesign shipped end-to-end**
(new engagement gate + cadence bands + Auto self-tuning; runner rebuilt
around Still-correct/Change-level primaries + Skip/Push/Mute
secondaries + completion-screen batch add-to-list; Settings block +
Stock Overview "Needs check" filter + pulsing outline on overdue rows).
That closes SK-1..11 from the feedback pass; loop-progression items
FU-450 + FU-451 shipped 2026-07-09 (deal-quality + budget-defense recipe swaps);
FU-452/351/352 remain. **Phase 3 sits at ~95%** — the champion
sequence `P8-01 → P8-02 → P8-05 → P8-06 → ⭐ P8-07 → P8-08 → P8-09 →
P8-10` is fully built. Nothing champion is left to construct; three
surfaces still need a browser walk (P8-07 flagship, P8-08 Kitchen
health card + P8-09 Memory reports, P8-10 Native Android).
**Next up:** either a **browser-verify sweep** across the pending
surfaces (P8-07 flagship + the two new stocktake redesign blocks +
P8-10 native), or **Phase 4 kick-off** (commercialisation report →
per-recommendation FUs; email setup; multi-tenant readiness). Also
worth grabbing while surfaces are open: FU-464 auto-add re-verify
(fixed this session but e2e-only coverage) and FU-355 sign-out
list-state clear.

---

## Phase board

| Phase | Scope | Status | Remaining |
|---|---|---|---|
| **0 — Foundations** | Theme/buttons/modals/filters/text-size/renames + bug clusters + config/opt-ins | ✅ ~99% | Residual polish clusters (FU-359/360/361/362/363/431/432); FU-421 + FU-430 closed to `_RESOLVED`. |
| **1 — Close the loop** | Shopping lists, cook mode, stock overview, cookbook, suggestions, costing, stocktake | ➗ ~90% | **Stocktake mode redesign shipped end-to-end** (Chunks 1–3 + housekeeping); SK-1..11 resolved. **FU-449 closed** — P6-07 cook→consume `ConsumptionEvent` persists. **FU-351 shipped** — P6-10 "Draft my shop" one-click dashboard card on top of the existing `/auto-generate` engine (2026-07-07). **FU-352 closed** — P6-12 briefing / P8-08 Score coexistence decided (2026-07-07: keep both cards, no fold). Remaining P6 gaps: **FU-450** P6-03 `fake_markdown` + `good_deal` alert; **FU-451** P6-09 budget-defense swaps; **FU-452** P6-11 put-away + expiry-by-location grouping. |
| **2 — Ingestion API + companion** | `/api/ingest` seam; extract scraper to standalone companion; Merchant→Store rename | ✅ done (backend-green) | Browser-verify pending (FU-214 + Phase-0/F verify FUs). |
| **3 — Champion** | Zero-Input Pantry (flagship), buy/wait oracles, barcode-add, Dora Score, culinary memory, native app | ➗ ~95% (verify pending) | **Champion sequence P8-01..P8-10 complete.** ⭐ P8-07 Zero-Input Pantry, P8-08 Dora Score, P8-09 Culinary memory, and P8-10 Native mobile app all BUILT (Capacitor 8 wraps the SPA; Android scaffolded locally, iOS scaffolded for a Mac session; runtime backend URL + first-run gate; wake-lock in cook + shop mode). P8-01/02/05/06 shipped earlier. P8-03 + P8-04 formally cut (§7 Decisions 6/7). Only remaining: browser-verify the four unverified surfaces (P8-07/08/09/10). Native FCM push deferred as [[FU-465]]. |
| **4 — Commercialize** | Tenancy, Stripe/billing, compliance, launch readiness (Postgres already done) | ⚪ ~0% | Not started (FU-387..406); zero billing/tenancy code. **Postgres is done + the default datastore** (FU-045 closed). Distribution-posture checklist gates daily work. Rate-limit primitives extended for per-user bucketing (FU-458 — one Phase-4 hardening item pulled forward this session). |

---

## Major workstreams

| Workstream | Status | Where it's at | Governing doc |
|---|---|---|---|
| Products-as-overlay | ➗ | Phases 0–F code-complete; tail (FU-210, FU-214 bulk-select/hard-delete) **browser-verify pending** | [RUNBOOK](docs/04_proposals/PRODUCTS_OVERLAY_RUNBOOK.md) |
| Ingestion API | ✅ | Backend green (401/401 tests), bearer-auth lane, admin keys page | [PROPOSAL](docs/04_proposals/PROPOSAL_INGESTION_API.md) |
| Standalone companion | ✅ | Runs standalone (`../dora-companion`); round-trip tests pass | RUNBOOK Phase C |
| Merchant→Store rename | ✅ | `usual_store_id` + Stores page shipped | RUNBOOK Phase E |
| Shopping Lists | ✅ | 8/8 bullets; DRAFT→SHOPPING→DONE loop | [PROPOSAL](docs/04_proposals/SHOPPING_LIST_REDESIGN_PROPOSAL.md) |
| Cook Mode | ✅ | Chunks 1–6 (84% of feedback) | `C_big_rock_design_briefs.md` |
| Cookbook | ➗ | Chunks 1–10 shipped; 5 Recipe-Detail bullets remain (FU-432); tag-taxonomy needs env verify (FU-085) | [PROPOSAL](docs/04_proposals/PROPOSAL_COOKBOOK.md) |
| Stock Overview | ✅ | 32/41 bullets; 3-band StockLevel; buy-verdict badge wired; new "Needs check" filter + pulsing overdue outline (FU-226 tail) | `PROPOSAL_STOCK_OVERVIEW` |
| **Stocktake Mode redesign** | ✅ | **Built end-to-end 2026-07-04.** Chunk 1 backend engine (new engagement gate, cadence bands, Auto self-tuning, grace-period baseline, Push snooze endpoint) + Chunk 2 SPA runner (Still-correct/Change-level primaries + Skip/Push/Mute secondaries + `(?)` help + completion-screen batch add-to-list; landing page retired) + Chunk 3 Settings + Overview surfacing. Housekeeping pass extracted `resolve_overdue_map` shared authority for alerts feed (was a two-authority R-003 drift) and deleted the dead `locations/attention.py` heatmap system. Alembic `d1f9c3a8b2e4` + `e5c8b3a1f4d2`. 18/18 cadence pytest green. SK-1..11 feedback resolved. | [PROPOSAL](docs/04_proposals/PROPOSAL_STOCKTAKE_MODE.md) |
| ⭐ Zero-Input Pantry (P8-07) | 🟡 | Built end-to-end (belief service `pantry_belief.py` + `ConsumptionEvent`/FU-449 + `/stock-items/beliefs` + additive `PantryBeliefChip` + `pantry_check` quick-check + per-user pref). **Browser verify pending.** | [PROPOSAL](docs/04_proposals/PROPOSAL_ZERO_INPUT_PANTRY.md) |
| Buy-verdict oracle (P8-05 + P8-06) | ✅ | Row + shopping-line badges + full `BuyVerdictCard` wired into stock-item detail overview (FU-437 closed); P8-06 `wait_hint` on `wait` verdicts (FU-438 closed); one-tap `mark_stocked` + `remove_from_list` actions wired (FU-454). | [PROPOSAL](docs/04_proposals/PROPOSAL_BUY_VERDICT_ORACLE.md) |
| Barcode-to-add (P8-02) | ✅ | OFF lookup for unknown EANs, gated by `scanning_enabled` | [PROPOSAL](docs/04_proposals/PROPOSAL_BARCODE_SCANNING.md) |
| Native mobile app (P8-10) | 🟡 | Capacitor 8 wraps the SPA; Android scaffolded on this Linux dev box (adaptive icons, `CAMERA/WAKE_LOCK/VIBRATE/POST_NOTIFICATIONS` manifest, `allowMixedContent` for LAN self-hosts); iOS scaffolded for a Mac session. Runtime backend URL persists to `@capacitor/preferences`; first-run `/setup/backend` gate; wake-lock in cook + shop mode. **Final APK build + on-device browser-verify pending** (no Android SDK on this dev box). FCM push deferred as [[FU-465]]. | [BUILD_NATIVE.md](packaging/BUILD_NATIVE.md) |
| Onboarding | 🟡 | Per-name picks + paste-rows shipped; **verify pending**; preferred-stores step not built (FU-383) | [PROPOSAL](docs/04_proposals/PROPOSAL_ONBOARDING.md) |
| Meal Plans | ➗ | **Built end-to-end** (3 pages, 13 components, board/calendar/templates/shortfall + backend). Waiting on **your screen-style pick + feedback**, not construction | [PROPOSAL](docs/04_proposals/PROPOSAL_MEAL_PLANS.md) + `IMPL_PLAN_MEAL_PLANS_REBUILD.md` |
| Alerts control centre | ✅ | **Fully built**: `/alerts` hub, `ALERT_ROUTER` API, price-watch + email-digest + push delivery. `stocktake_overdue` alert kind now routes through the shared `resolve_overdue_map` (FU-464 housekeeping — was drifting from the runner's authority). | [PROPOSAL](docs/04_proposals/PROPOSAL_ALERTS.md) |
| Assistant surface | ✅ | Per-user rate limits wired (FU-458) — `/ask` 20/min, `/act` + `/confirm` 60/min. `rate_limit` helper extended with a `subject` override so a shared household IP doesn't cross-count users. | `ask_assistant.py`, `auth_helpers.py` |
| Data/Backup admin | ✅ | Collapsed under Settings→Admin→Data; backup library + admin-gating (code committed) | FU-341/342/198 |
| Auth shell | ➗ | Shared `AuthShell.vue` + `AuthButton.vue` across 8 pre-auth surfaces (no standalone register page) | `PROPOSAL_AUTH_SHELL.md` |
| Postgres datastore | ✅ | Implemented + **default** (SQLite fallback via `DORA_DB_PATH`); FU-045 closed | `configuration_manager.py` |
| Recipe importer (paste-based rebuild) | ✅ | **All six chunks landed 2026-07-04.** Parser green on 20/20 corpus; schema migration for unlinked-ingredient tri-state cookability; paste importer replaces the URL fetcher (FU-104 + FU-199 closed); bulk-linker page + PWA share target. Browser-verify pending. | [IMPL_PLAN](docs/04_proposals/IMPL_PLAN_RECIPE_IMPORTER.md) |
| Commercialization (P7) | ⚪ | Tenancy/Stripe/billing not started; zero such code yet | [PLAN §5](docs/01_charter/RECONCILED_FINISHING_PLAN.md) |

---

## ⚠️ Needs your attention now

Full backlog is **128 open items** in `DORA_FOLLOWUPS.md`; these are the
ones that want a decision or a running-app check *now*, most important
first.

0. **🔴 SECURITY — unfixed HIGH + MEDIUM findings.** `docs/05_investigations/AUTH_ASSISTANT_SECURITY_FINDINGS.md` records a **HIGH CSRF** flaw and a **MEDIUM email-change** flaw with no fix logged. Surfaced by the 2026-07-02 doc audit — decide whether to fix now before more champion work. Tracked as [FU-447](DORA_FOLLOWUPS.md).
1. **🔴 Meal Plans — pick the screen style + give feedback.** The feature is **built** (board/calendar/templates all shipped); it's waiting on *your* UX-direction call, not on engineering.
2. **🔴 FU-346 — Admin settings "feel hidden."** You raised this. Short direction call needed (stay put / header icon / `/admin` route) before any code moves.
3. **🔴 FU-353 — Rename GitHub repo + local checkout to DashyDora.** Your action (`gh repo rename` + `mv`); until then release-check URLs + README badges 404.
4. **⭐ Verify the champion sequence in-browser.** Four surfaces stacked and untested on this dev box: **P8-07 Zero-Input Pantry** (walk `DORA_VERIFY.md §Stock`); **P8-08 Kitchen health card**; **P8-09 Memory reports**; **P8-10 Native Android APK** (final build + device walk). The stocktake redesign's Chunks 2 + 3 verify blocks in `DORA_VERIFY.md` also want the same walk.
5. **FU-085 — Cookbook tag-taxonomy never run in a real env.** Verify the migration on SQLite + Postgres before building on it.
6. **FU-214 — Products-overlay Phase F verify + bulk-select/hard-delete.** Last real gate on that effort; needs the running app.
7. **FU-429 — Assistant-architecture proposal collides with in-flight SLM work.** `DORA_ASSISTANT_ARCHITECTURE_PROPOSAL` proposes a capability registry that the SLM pivot may supersede; needs a reconcile-or-close decision.
8. **FU-025 follow-on — component labels ignore the text-scale tokens.** Button/input/toggle labels don't track the A6 scale; small global sweep.

---

## Recently shipped (newest first)

- **FU-515 done — assistant security findings fully triaged (2026-07-08).** Worked the 8 medium/low items left in the AUTH_ASSISTANT audit. **Shipped:** prompt-injection defence (system-prompt "tool data ≠ instructions" rule + control-byte stripping — B.1), tool-arg bounds (reject absurd expiry pushes — B.3), and `current_path` prompt sanitisation (B.4), with 8 new tests. **Verified already-fixed:** assistant rate/input caps (B.2), verified change-email UI (A.3, FU-197), password-rule alignment (A.4, FU-442). **Accepted with rationale:** admin plaintext reset (self-host fallback), in-memory rate-limit (Phase-4 scaling), tokens-in-URL (mitigated). `AUTH_ASSISTANT_SECURITY_FINDINGS.md` now "✅ Fully triaged". 37 assistant+auth tests green.
- **FU-390 done — assistant eval suite, both paths (2026-07-08).** Stood up **vitest** in `web_app` (was a no-op test script) with a 53-case Basic-mode eval corpus over `detectIntent` + `extractAddToListItems`, plus 9 backend reliability tests pinning the AI-path mutation gate + tool-registry integrity + graceful no-model degradation. The suite immediately caught **3 real bugs**, all fixed: "put milk **on** my list" mis-parsed the item; "\<adjective\> recipe" phrasings fell through to fallback (no bare `recipe` trigger); and the retired `set_primary_list` tool was still advertised to the model (+ on the help page) with no proposer → silent no-op, now fully removed. `vitest` 53/53, backend assistant+auth 29/29, `vue-tsc` clean.
- **FU-514 fixed — onboarding seed-items no longer 500s (2026-07-08).** `POST /api/onboarding/seed-items` crashed on every call because `SeedItemsHandler` still passed a dropped `image` field to `StockItem` (leftover from FU-508's stock-item-image removal). One-line fix; `test_onboarding_flags.py` now 7/7.
- **FU-429 assistant-architecture reconciled + Basic mode gains an action verb (2026-07-08).** The 2026-06-04 assistant proposal was flagged as never-built/colliding with the SLM. Reconciliation: the SLM has **landed** (default AI path), and most of the proposal was already satisfied elsewhere (§1 missing-ingredients dup gone via state-ownership; §2.1 single `tools.py` registry; mutation gate + rate limits present). The one unbuilt piece — §2.2's shared-registry refactor so Basic mode reaches AI-parity — was **deliberately not built** (Effortless + Anti-creep). Product steer: most everyday users never wire up an LLM, so **Basic mode is the default experience and must be genuinely useful**. So we closed the single biggest gap directly — Basic mode had 27 answer intents and *no* action verb; it now understands **"add milk" / "buy eggs and bread" / "need to buy rice"**, resolves items against the pantry, and adds unambiguous matches to the primary list via the existing composable (ambiguous/not-found surfaced, never guessed). Proposal doc got a §0 reconciliation record. Related: [[FU-386]] closed (the `?cookable=true` server filter already shipped), [[FU-390]] eval suite unblocked + re-scoped (own session), [[FU-360]] subset shipped (below). `vue-tsc` clean; `test_auth_flows.py` 20 passed.
- **Dora helper polish — FU-360 subset (2026-07-08).** **Hide Dora entirely**: new per-user `show_assistant` preference (User column + migration `c7d1a9e3f2b6` + `PATCH /auth/me` + DTO) with a "Show Dora on every page" toggle in Settings → Assistant; `MainLayout` gates the bubble on it. **Greeting once-per-user**: the "Hi! I'm Dora" hint is now keyed by user id, so a shared household browser gives each account one acknowledge. **Chip legibility**: the AI/Basic mode chip dropped `dense` for a rem-based, padded style that follows the text-size preference. Remaining FU-360 items — chip→slider restyle (#3, design task) + text-size/DS4-hover verifies (#1/#4) — carried to `DORA_VERIFY.md`.
- **FU-447 closed as already-satisfied (2026-07-08).** No code change. The AUTH_ASSISTANT_SECURITY_FINDINGS.md audit that raised FU-447 (2026-07-02) flagged **A.1 CSRF (HIGH)** and **A.2 email-change without password proof (MEDIUM)** as still-open, but both were closed by [[FU-197]] on 2026-06-30 — three weeks before the audit. Verified live via code read of [`csrf.py`](dora_api/infrastructure/csrf.py) + [`email_flows.py`](dora_api/features/auth/email_flows.py) + `pytest test_auth_flows.py -k "csrf or email_change"` (2 passed). Findings doc header flipped from "Draft for discussion" → "➗ Partially actioned"; A.1 + A.2 rows now open with a "✅ RESOLVED (FU-197)" block preserving the original write-up as a blockquote for the audit trail; priority table gained a per-row Status column. The 8 remaining Medium/Low findings (B.1 scraped-data injection, B.2 assistant rate-limit, A.3 email-change UI half-shipped, A.4 password-rule drift, A.5 admin plaintext reset, A.6 in-memory rate-limit, A.7 tokens-in-URL, B.3 tool-arg bounds, B.4 current_path in prompt) opened as [[FU-515]] so they don't age silently the same way. Recommendation for the next security-tidy session: **B.1 + B.2** — B.1 becomes reachable once merchant ingestion goes live in Phase 2.
- **FU-512 closed — unit-of-work sweep applied to 10 more handlers (2026-07-08).** Mirrored the FU-456 "one flush, one commit" pattern across every other genuinely-multi-commit handler: `CreateMealPlanTemplate`, `CloneMealPlanTemplate`, `CreateSet` (meal-plan template sets), `NewRecipeVersion`, `AutoGenerate`, `Seed` (onboarding), `CopyShoppingList`, `CreateTemplate` + `InstantiateTemplate` + `SnapshotFromList` (shopping-list templates). Habit-commits after the parent `add()` deleted (uuids are client-assigned by `SqlAlchemyRepository.add()`); `if children:` guards around the final commit dropped (empty session commit is a no-op); `SeedHandler` locations-loop and `NewRecipeVersion` habit-commits converted to `flush()` where the child insert needs the parent FK visible on the wire (classic mapper has no self-referential `relationship()`). `AutoGenerate._create_list()` lost its commit; the downstream `.all()` autoflushes the pending ShoppingList, so FK visibility for the new lines is preserved without a manual flush. 10 new happy-path e2e tests (13 test cases across 10 files), all green. No rollback tests added per the runbook (none of the 10 has a reachable failure surface between the former commits). Surprise pre-existing bug found during regression check: `SeedItemsHandler` at `onboarding.py:514` passes an `image=...` kwarg to `StockItem(...)` which has no such field — logged as [[FU-514]]. Optional Batch 4 (docstring-noting the 9 no-refactor handlers) skipped to keep the diff tight.
- **FU-513 closed — GET /api/suggestions no longer mutates the DB (2026-07-08).** The read path used to delete expired snoozes and commit on every dashboard load, taking a write lock and violating the "GETs don't mutate" contract. The inline delete-and-commit is gone; correctness is unchanged because `_is_suppressed_now` already filters expired snoozes at read time. Table hygiene moved to a new daily APScheduler job `prune_expired_snoozes` (03:30 UTC) in [`dora_api/features/suggestions/prune_expired_snoozes.py`](dora_api/features/suggestions/prune_expired_snoozes.py). Also fixed a latent tz-mismatch in `_is_suppressed_now` — SQLite drops tzinfo on `DateTime(timezone=True)` columns on read, so the filter now treats naive `snoozed_until` as UTC (same pattern as `get_alerts.py`). Regression-pinned by [`test_suggestions_snooze_prune.py`](tests/e2e/dora_api/test_suggestions_snooze_prune.py) (4 tests).
- **DI walk-back — constructor injection via Protocols; no container (R-031 / ADR-027, 2026-07-08).** The `dependency_injector`-based `DependencyContainer` (~215 LOC wrapper + reflection-based `service_wiring.py`) was deleted. Handlers now receive their repository as a constructor arg typed against a `Repository` Protocol in [`dora_api/infrastructure/ports.py`](dora_api/infrastructure/ports.py) — 175 handler `__init__`s rewritten, ~200 `get_container().inject(X)` sites rewritten to `X(SqlAlchemyRepository())`. Three tests dropped their `patch.object` seams and pass stubs through the ctor directly (immediate testability payoff). `dependency_injector` dropped from `requirements.txt`. **[[FU-457]] dissolved by construction** — the boot-time assertion it asked for protected a reflection surface that no longer exists (moved to `DORA_FOLLOWUPS_RESOLVED.md`). New [[R-031]] + [[ADR-027]] codify the pattern; `I`-prefix nominal interfaces are discouraged for new work, `typing.Protocol` is the shape. Full pytest **828 pass / 2 pre-existing fails** — 0 regressions.
- **FU-456 closed — `POST /recipes` is a unit of work (5 commits → 1) (2026-07-08).** Recipe create used to commit 5 times so a validation failure on tags/steps/images left a partial recipe row behind; the handler now flushes after `add(recipe)` (so downstream FK-referencing inserts see the row) and commits once at the very end of the success path. Every early-return `invalid_*` branch drops `new_recipe_id` (pre-refactor the id named a committed partial recipe; post-refactor no row exists to name). 3 new e2e tests in [`test_create_recipe_unit_of_work.py`](tests/e2e/dora_api/test_create_recipe_unit_of_work.py) pin the invariant (invalid dietary tag → rollback, invalid step parent → rollback, happy path → single commit). Full pytest 828 pass, 2 pre-existing unrelated fails. Sweep of the other ~20 multi-commit handlers spun off as [[FU-512]] with a runbook + reference implementation named.
- **FU-500 closed — R-029 (hide, don't nag) app-wide sweep (2026-07-08).** One live behaviour flip + audit of every `R-014` reference in the SPA. The Product Search entry in the main nav now **hides** when the admin hasn't configured a `product_search_url` (was previously rendered disabled with a "Not set up yet — set the URL in Settings → System → Features" tooltip). `MenuButtonProps` shed its now-dead `disabled` / `disabledTooltip` fields; both menu-button components lost the disabled render branch. Nine R-014 comment references relabelled to R-029 (still valid carve-outs on settings screens that own the config — `NotificationsSettings`, `AssistantSettings`, `VoiceSettings`, `StockItemDetailPage` barcodes, etc.). Eight mislabelled R-014 tags on lifecycle / state-hydration / swallow-error / calm-empty-state sites (`useWakeLock`, `SubstituteMetadataDialog`, `StockItemRowPriceButton`, `DashboardPage` ×3, `MealPlansOverview`, `MealPlanWeekDayCard`, `DoraScoreCard`, `YourPricesWidget`) removed or relabelled with explicit "distinct from R-029" notes. `ENGINEERING_STANDARDS.md` ADR-002 gains a Presentation line re-affirming hide-when-off + a "See also: R-029 / ADR-025" cross-reference. `vue-tsc` clean.
- **FU-504 closed — raw `<q-btn>` sweep + `BaseButton` variant gap (2026-07-08).** The FU-424 senior-review audit's last base-component adoption residual, dispatched in one dedicated pass. `BaseButton` gains a new **`filled-icon`** variant (`unelevated round dense`, primary by default) plus an **optional `color` prop** that overrides the variant's default color — together they cover the "unelevated coloured icon button" shape (RecipeCard chef-hat toggling primary/warning was the marquee case) without callers reaching for raw q-btn. 40 raw `<q-btn>` sites migrated to `<BaseButton>` across 16 files (`RecipeCard`, `ScanOverlay`, `DoraChat` ×13, `MyProductsPage` ×17, six settings pages ×8, one on `AdminDataBackupRestore`); 10 raw sites deliberately kept as documented carve-outs (accent-palette Help CTA, Quasar-secondary outlines on timezone/locale, `type="a"` anchors, dynamic positive/warning outlines on ShoppingListDetail, StocktakeRunner's labeled-dynamic-color change-level button with custom stacked children). `vue-tsc` clean (no new errors). Verify checklist under `DORA_VERIFY.md` → Cross-cutting.
- **FU-333 closed — env-var sprawl finished; Buckets C + D shipped + fallbacks dropped (2026-07-06).** SMTP password + VAPID private key promoted onto `AppSetting` as encrypted-at-rest columns (Fernet ciphertext wrapped by `DORA_LLM_KEY_ENCRYPTION_KEY`, reusing the FU-153 helper); migration `a3e7d2c9b5f1` adds the two columns. Admin edits both from Settings → System → Email / Push notifications (write-only inputs; DTO returns only a `_configured` bool). Bucket D lands the desktop first-run: `desktop_app._bootstrap_keys()` auto-generates `DORA_SECRET_KEY` + `DORA_LLM_KEY_ENCRYPTION_KEY` into `<DATA_DIR>` on first launch, and `_seed_desktop_paths()` writes the detected piper binary + voice-dir into the row post-init (rather than exporting env). The Bucket-B env-var fallback lane is gone across the resolver + 7 read sites; `.env.example` and README purged of `DORA_SMTP_*` / `DORA_VAPID_*` / `DORA_PIPER_*` / `DORA_EMAIL_ENABLED` / `DORA_AUDIT_RETENTION_DAYS` / `DORA_PUBLIC_URL`. Env footprint on server self-host: 19 → **2** (`DORA_SECRET_KEY` + `DORA_LLM_KEY_ENCRYPTION_KEY`); on desktop: **0**. New R-030 + ADR-026 in ENGINEERING_STANDARDS codifies "operational config lives on `AppSetting`, not env" for future work. Also closes [[FU-467]] (the fallback-drop follow-up). Tests: new `test_bucket_c_secrets.py` (encrypt-on-write, `_configured` bool never leaks, clear-via-empty, round-trip decrypt, missing wrapping key → 400, rotated key → dry-run + warning). Browser verify checklist in `DORA_VERIFY.md` under Settings.
- **FU-502 resolved — locale/currency backend coverage tests (2026-07-06).** Closed the FU-043 R-013 coverage gap. New `tests/e2e/dora_api/test_locale_currency.py`, 19 cases: round-trip PATCH → `/health` `locale_policy`, currency valid/invalid tables (case-normalised on save; pydantic length + `isalpha` reject the malformed cases), locale valid/invalid tables (against the `_is_valid_bcp47` structural validator). Skipped the FU's "migration up/down against in-memory sqlite" line item as ceremony — the migration is exercised on every test run via alembic-managed schema; noted in the resolved FU. `vue-tsc` N/A (backend tests only). Full suite 787/2 (both pre-existing FU-466 flakes, unchanged).
- **FU-503 / FU-044 resolved — targeted (?) help chips (2026-07-06).** Executed `IMPL_PLAN_HELP_CHIPS.md` end-to-end: ~20 new `<q-tooltip>`-in-`<q-icon>` chips on genuinely-confusing controls (Kitchen health, Savings captured, Year-over-year, Meals-worth, Alerts tier concept + per-kind override, meal-plan Shortfall via shared `MealPlanWeekStatus`, RecipeDetail unallocated meals, RecipesOverview cookable-now filter, StockOverview filter chips, StocktakeRunner cadence + Push 3 days, ShoppingListDetail Finish & restock, PriceHistory usual/above-usual, MyProducts Select on-deal, PriceEntry multipack); 4 existing tooltips extended (RecipeCookMode Sous Chef + hands-free mic, ShoppingListDetail Plan-day, NotificationsSettings compact, AssistantSettings AI-mode description); 5 skipped as already covered by existing tooltip/help text; 1 skipped as N/A (dashboard "Cookable tonight" label was renamed to meal-plan-driven "Next to cook" since audit). Overlay mechanism from `PROPOSAL_HELP_OVERLAY.md` stays parked. `vue-tsc` clean.
- **FU-043 resolved — locale & international readiness Layers A + B (2026-07-06).** Dora is now usable outside Australia. Install-wide `currency` (ISO 4217) + `locale` (BCP-47) on `AppSetting` (migration `c4e9a2f7b1d3`, defaults `AUD` / `en-AU`). Every money render across the app — Dashboard budget/savings/deals/pantry-value, all Reports charts+totals, ShoppingListDetail line prices+offer chips, PriceHistory axes+tooltips+alert labels, StockItemDetail offers/observations/lifecycle, RecipeDetail cost, YourPricesWidget, PriceEntry, MoneySettings, ProductChip, QuickAddSheet, SubscriptionsPanel, MyProductsPage — routes through one shared [useMoney.ts](web_app/src/composables/useMoney.ts) wrapper around `Intl.NumberFormat`. `q-input :prefix` reads the same currency symbol so inputs flip atomically. `useVoiceInput` recognition locale derives from the setting (fallback: browser locale → `en-AU`). New admin page **Settings → Admin → System → Currency & locale** with validation, live preview, and "Use this device" locale detect. Assistant copy generalised — `APP_OVERVIEW` no longer names Coles/Woolworths/IGA/Aldi; two tool descriptions genericised. Locked as install-wide (not per-user), adopt-lite `vue-i18n` (kept installed as future translation seam, but the formatter is direct `Intl.NumberFormat`), no `currency` field on C-10 `price_observation`. Layer C (full UI translation) stays parked. Test coverage + AU-specific seasonal data logged as [[FU-362]] + [[FU-361]].
- **FU-003 resolved — reverted Pesto `--text-muted` bump instead of propagating (2026-07-06).** User's call: undo the A1b-era 50→42 lightness nudge on Pesto light rather than apply it to the other four light themes. Reverted [themes.scss:66](web_app/src/css/themes.scss:66) back to `hsl(168 8% 50%)`; Pesto Dark (independently tuned) untouched. All five light themes now share a common ~50% muted-lightness baseline — the FU-002 whole-app polish pass will re-judge muted contrast from parity, not from a Pesto-only outlier.
- **FU-421 closed as already-satisfied (2026-07-04).** No code change. The "remind me to use this on opened items" ask from the original spec is already implemented via the existing expiry surface — [item detail](web_app/src/pages/StockItemDetailPage.vue)'s Expiry row exposes `+1d`/`+7d`/`+14d` shift chips + a Set date-picker + Clear, and the Open toggle's tooltip explicitly documents the workflow ("for perishables it's the cue to set or shorten"). A user-set "use within 2 months" IS an expiry semantically, so reusing avoids duplicating a whole reminder infrastructure (R-003). Free alerts via the existing `expired`/`expiring_soon` kinds. Free auto-clear on waste. Only real gap is month-scale shift chips (`+1m`/`+3m` not there today) — user picked "close as-is" since he hasn't hit the pain; a ~10-line SPA change is available as an off-ramp if it becomes annoying.
- **FU-458 resolved — per-user rate limits on the assistant surface (2026-07-04).** Defense-in-depth against runaway LLM-cost loops. Extended `auth_helpers.rate_limit` with an optional `subject` arg — pre-auth callers keep the historic per-IP bucket, post-auth surfaces (assistant) pass `str(session.user_id)` so a shared household IP doesn't cross-count users. Wired 20/min on `/assistant/ask` (LLM round-trip), 60/min on `/assistant/act` + `/assistant/confirm`. 429 responses match the RFC 6585 §4 shape (Retry-After header). Also fixed a misleading "per-user" comment on `/assistant/probe` — the code was per-IP; now matches the comment. New `test_rate_limit_subject.py` (5 tests) locks subject isolation + IP-fallback back-compat. **303/303 pytest green** (was 298 → 5 new).
- **FU-463 resolved — SQLite `text()+str(uuid) IN :ids` zero-row regression in two hydration passes (2026-07-04).** Latent bug on SQLite self-hosts (Postgres unaffected). [`_hydrate_linked_product_count`](dora_api/features/stock_items/get_stock_items.py) and [`_compute_estimated_cost`](dora_api/features/recipes/get_recipes.py) both used raw `text()` binds with string uuids that never matched the `UUIDType` BINARY(16) storage — every stock-item DTO's `linked_product_count` was 0 and every recipe's `estimated_cost` was None on SQLite. Rewrote both as ORM `select()` against `db.metadata.tables[…]` — same shape `_hydrate_has_image` uses since FU-171. Verified via a live REPL round-trip against `data/dora.test.db` under `app.app_context()`. The `project_sqlite_uuid_text_binding` memory now covers three fixed surfaces + FU-171's pair; the pattern to grep for remains any `text() + str(uuid) IN :ids` combination.
- **FU-464 resolved — auto-add-when-low regression on Low transitions (2026-07-04).** Real user-visible bug that landed silently with the 2026-07-02 Sufficient-band collapse (`a1c7d9e42be0`). The auto-add hook in [`update_stock_item.py`](dora_api/features/stock_items/update_stock_item.py) was firing on `_NewLevelSeq >= 2` with the stale comment "2 = Low, 3 = Out". Under the new 3-band sequences (0 Stocked / 1 Low / 2 Out), `>= 2` = Out only — Stocked → Low transitions on `auto_add_when_low`-flagged items did NOT auto-add despite the whole point of the setting. Replaced the two literal-sequence comparisons with `needs_restock(level)` from `stock_status.py` (R-003, one authority for "restock-needing"). Sanity-tabled: `needs_restock` returns True for Low+Out, False for Stocked+None — correct semantics restored. Auto-add coverage is e2e-only, so the fix will be re-walked via the FU-315 auto-add block on the next browser session (heading nudged with a pointer).
- **FU-455 resolved — buy-verdict all-thin-axes test fixed (2026-07-04).** The failing `test__all_axes_thin__collapses_to_single_not_enough_history` was wrong, not the composer. Its inputs (`waste_events_12mo=0, purchases_12mo=1`) hit the composer's `no_waste_history` branch — a positive signal that "you've never wasted this" — not `thin_data`. Only 2 of 3 axes were thin, so the composer correctly didn't fire the `len(thin) == 3` collapse. `no_waste_history` vs `thin_data` is a real R-003 distinction (one is knowledge, one is absence-of-knowledge); merging them would have broken the composer's ability to nudge toward buying on a clean waste record. Fixed the test to use `waste_events_12mo=1, purchases_12mo=1` (waste seen but too few purchases to compute a rate) so the waste axis really is thin. Docstring gained a "waste-axis nuance" note. **298/298 pytest green** for the first time since Chunk 1.
- **Stocktake housekeeping — R-003 drift fixed, dead heatmap deleted, deprecated columns dropped (2026-07-04).** Survey after Chunk 3 found the `stocktake_overdue` alert kind + the location-attention heatmap were still computing overdue from the old per-item threshold — two authorities for the same fact. Extracted `stocktake.resolve_overdue_map(items, now)` from the queue endpoint; alerts feed now consumes the same map. Deleted the whole `locations/attention.py` heatmap system: `attention_score` / `attention_reasons` fields gone from both the location-tree DTO and stock-item-detail DTO, `AttentionReasons` type + helpers gone from SPA models (zero Vue consumers — it was pure dead code). New alembic revision `e5c8b3a1f4d2` drops `StockItem.days_until_stocktake_alert` and `AppSetting.default_days_until_stocktake_alert`; every backend + SPA caller pruned in the same pass (~14 file edits + 1 delete + 1 new migration). Backend pytest 297/298 (FU-455 unrelated); `vue-tsc` clean.
- **Stocktake redesign — Chunk 3 Settings + Stock Overview surfacing (2026-07-04).** Peripheral surfaces (§7 + §8) that close the redesign trilogy. New **Settings → Admin → System → Stocktake** page with `q-btn-toggle` cadence selector (Weekly / Fortnightly / Monthly) and a `q-toggle` for Auto self-tuning — eager-saves on change, reverts on failure. The old numeric "Default stocktake reminder" section on Alert thresholds is removed (superseded by the band system; column stays in the DB for now). **Stock Overview** gains a **"Needs check" FilterChip** in the chip strip (narrows to items currently in the stocktake queue — server-owned set via bumping the existing queue fetch from `limit=1` → `500`; no new endpoint), and **overdue rows get a 2-second brand-accent pulse outline around the stock-level button** (matches the toolbar Stocktake attention glow byte-for-byte; `prefers-reduced-motion` degrades to a static ring). One transient tsc error caught inline (`q-btn-toggle` wanted a mutable options array). `vue-tsc` clean; no backend change. Two housekeeping FUs deferred, not opened: drop `default_days_until_stocktake_alert` and `StockItem.days_until_stocktake_alert` columns whenever the next stocktake/alerts work opens.
- **Stocktake redesign — Chunk 2 SPA runner rebuild (2026-07-04).** The user-visible half of PROPOSAL_STOCKTAKE_MODE. Landing page retired ([StocktakePage.vue] deleted; `/stocktake` now loads the runner directly; empty state is a state of the runner). New button layout — two big primaries (**Still correct** | **Change level**, the latter tinted to the current level's colour with a "(change)" hint, resolving SK-8/9) + three small secondaries (**Skip** session-only / **Push 3 days** hits the Chunk-1 snooze endpoint / **Mute** with confirmation). Level picker gains coloured dots. `(?)` help affordance in the topbar opens a plain-English "how it works" dialog. Completion screen shows five counters (checked / changed / skipped / pushed / muted) + a batch **Add to list…** prompt for anything that went Low or Out during the session (resolves SK-7 — the old per-item button is gone). Dropped the standalone Out-of-stock button, all keyboard shortcuts + their `(1)/(2)/s` labels (SK-4/10), and the per-item Add-to-list. `vue-tsc` clean; no backend change.
- **Stocktake redesign — Chunk 1 backend engine (2026-07-04).** Ships PROPOSAL_STOCKTAKE_MODE §2 (new engagement gate — one honest question, no more flag-based signals, 60-day windows on the two history signals), §4 (Weekly/Fortnightly/Monthly bands + Auto self-tuning ON by default, driven by trailing-90d StockLevelChange history), §4.1 (grace period via `COALESCE(last_checked_at, stock_level_last_updated)` — `9999` sentinel dropped), §5 Push verb (fixed 3-day snooze; makes no truth claim so no `last_checked_at` stamp; cleared by any subsequent Check). Single new alembic revision `d1f9c3a8b2e4` also **merges the two open heads** (`a3e8b1f6c2d9` + `c5a8e1f7d3b2`) so the DB tracks a single linear history again. New pure module [cadence.py](dora_api/features/stocktake/cadence.py) with 18/18 pytest green ([test_stocktake_cadence.py](tests/test_stocktake_cadence.py)). Backend-only chunk; runner UX rebuild is Chunk 2. One pre-existing `test_buy_verdict` failure surfaced by the wider-suite run — logged as FU-455, not a stocktake regression.
- **Stock Overview bulk "Log waste…" (2026-07-04).** Spun off the FU-226 chat: since expiry+waste stays *out* of stocktake and lives on the Stock Overview instead, bulk-select gains a `Log waste…` button that reuses the existing single-item reason-picker (R-001) — one reason applies to every selected item, each gets its own reason-only `StockItemWasteEvent`, expiry dates cleared, batch Undo. New verify checklist in `DORA_VERIFY.md` under Stock; `vue-tsc` clean.
- **Stocktake Mode redesign brief — FU-226 + FU-430 (2026-07-04).** Design deliverable, no code; **all decisions locked** across four question-waves with the user. Untangled three concerns: **who** gets nagged (gate → one question "do you actually keep this item?" — in stock / opened / adjusted-in-60d / on-a-list-in-60d; Essential + auto-add dropped as gate signals; **60-day window** on the history signals), **how often** (Weekly/Fortnightly/Monthly **bands** — global default Fortnightly + full two-way **Auto** self-tuning **ON by default** from trailing-90d level-change frequency; Essential = one band faster and the *only* per-item lever, no per-item picker ever; never-checked → **grace period** not instant-top), and **what you can do** (two primaries Still-correct | Change-level + three smaller Skip / **Push** 3-day snooze / **Mute** — no Out-of-stock button, no keyboard shortcuts). **Expiry & Waste CUT from stocktake** (Overview expiring-filter is the single waste surface). No landing page (straight to runner + `(?)` help); add-to-list → completion-screen batch; new "Stocktake" settings block; Stock Overview overdue rows get a pulsing outline + "Needs check" filter. [PROPOSAL_STOCKTAKE_MODE.md](docs/04_proposals/PROPOSAL_STOCKTAKE_MODE.md) fully rewritten to the locked design + SK-1..11 coverage. Both FUs closed; next step an impl plan.
- **BuyVerdictCard one-tap actions wired end-to-end — FU-454 (2026-07-04).** The card renders on three surfaces (Stock Overview row, Stock Item Detail, Shopping List Detail line card) but two of its five action kinds — `mark_stocked` and `remove_from_list` — were previously silent no-ops or "use the row controls" info toasts. New shared composable [useBuyVerdictActions.ts](web_app/src/composables/useBuyVerdictActions.ts) exposes `markStocked(stockItemId)` (looks up the Well-Stocked band via the canonical `STOCKED_SEQUENCE = 0` constant, reuses the same `updateStockLevelAsync` seam the row dropdown uses — R-003 no duplicated mutation paths — and invalidates buy-verdict + refreshes pantry beliefs) and `removeFromAllOpenLists(stockItemId)` (fans out via `useShoppingListActions.removeFromAllLists` over every non-`done` list summary — the server's `by-stock-item` DELETE is a safe no-op on lists that don't contain the item, so no membership probe is needed). All three card mounts now delegate to this composable; the "use the row controls" fallback toasts are gone. `vue-tsc --noEmit` clean.
- **Password policy realigned to NIST 800-63B / ISO 27002 §5.17 — FU-442 (2026-07-04).** `MIN_PASSWORD_LENGTH` dropped from **10 → 8** (matches NIST minimum + the user's original feedback), the forced letter-and-digit **composition rules were removed** (NIST retired these in 2017 because they push users toward low-entropy substitutions like `Password1!`), and a bundled **breach-list check** was added — a `frozenset` of ~60 known-compromised passwords (`password123`, `qwerty123`, `letmein1`, `dashydora`, etc.) is rejected case-insensitively with a friendly message. **No admin toggle** — the policy is install-wide and non-overridable per the user's explicit call, which is what makes the ISO/NIST citation truthful. Frontend copy on SetupAdminPage, LoginPage, ResetPasswordPage, AccountSettings refreshed to "at least 8 characters, a passphrase works well"; AccountSettings' stale `>= 4` client rule tightened. **23/23 pytest green** on the new `tests/test_password_policy.py` (min-length, no-composition-rules, breach-list case-insensitive, policy-doc text). Rate-limit + Werkzeug scrypt/pbkdf2 hashing already covered the NIST throttle and no-truncation requirements. See [auth_helpers.py:43-108](dora_api/infrastructure/auth_helpers.py) for the policy header with the citations inline.
- **P8-10 Native mobile app scaffold (2026-07-04).** Capacitor 8 wraps the Quasar SPA — one codebase, no fork. Android platform fully scaffolded on this Linux dev box (`web_app/src-capacitor/android/`, adaptive launcher icons regenerated from the mascot on a `#F5C462` background, manifest permissions `CAMERA / WAKE_LOCK / VIBRATE / POST_NOTIFICATIONS`, `allowMixedContent` on for LAN `http` self-hosts). iOS platform scaffolded (`src-capacitor/ios/`) but never built here — awaits a Mac session. Runtime-configurable backend URL via new `services/api/backendUrl.ts` (persists to `@capacitor/preferences` on native, `localStorage` in the browser; axios interceptor prepends per-request); a first-run `/setup/backend` gate blocks every route until the user picks an instance; Settings → About gains a **Change** button + full-reload wiring. Screen wake-lock via new `useWakeLock` composable (standard `navigator.wakeLock`), held during cook mode and while a shopping list is `status === 'shopping'`. New docs: [packaging/BUILD_NATIVE.md](packaging/BUILD_NATIVE.md) (Android APK how-to, prerequisites, live-reload) + [docs/04_proposals/PLAY_STORE_LISTING.md](docs/04_proposals/PLAY_STORE_LISTING.md) (draft copy + screenshot plan; no submission). Push on native intentionally stays 'unsupported' (Android WebView has no Push API); FCM bridge deferred as [[FU-465]]. **FU-411 + FU-418 close** — target-matrix and Distribution Spec §4 questions answered in P8-10 scope-lock. `vue-tsc --noEmit` clean. Final APK build lives as a browser-verify step (no Android SDK on this dev box).
- **P8-09 Household culinary memory (2026-07-04).** A new **Memory · what you actually did** section on `/reports` with three cards: (1) Meals cooked — cook-count + meals-worth timeline over the range + top-N recipes by cook frequency, (2) Spend by category — donut + legend rolling up archived shopping-list lines through `StockItem.stock_group`, (3) Year-over-year — total + per-category delta vs. the same-length prior window (rate is `null` not `+∞%` for new-category cases — P3 Honest). Range vocabulary extended to `2y` / `5y` on every reports endpoint. Three new assistant tools (`meals_cooked_in_range`, `spend_by_category`, `spend_year_over_year`) compose over the same endpoints so chat answers "what did we make last Christmas?" and "how has dairy changed year on year?" with real stored data — no invention. Single-household scope, per the champion plan; multi-tenant (Path A SaaS) is a separate deployment posture and doesn't gate this. **22/22 pytest green** on the new report math + range vocab + grouping.
- **P8-08 The Dora Score (2026-07-04).** A single kitchen-health composite (0-100) computed server-side over a rolling 30-day window from five signals: waste (`StockItemWasteEvent` count), on-budget (reuses `/budget/status`), freshness (% of expiry-tracked items past their date), unplanned run-outs (`ConsumptionEvent` to Out with no active shopping-list line), and stocktake staleness (% checked in the window). Components with no data are excluded from the mean, never zeroed (charter P3 Honest). A trend arrow (score vs. same score 7 days ago, ±2-point hysteresis) travels with the DTO. Renders as a new **Kitchen health** card at the top of the dashboard's Your Kitchen zone with a big number, trend chip, and per-component mini-bar breakdown; each component's weak-side action links to the feature that improves it (waste → waste tab, budget → preferences, freshness → expiring stock, run-outs → shopping lists, stocktake → stocktake mode). New endpoint `GET /api/dashboard/dora-score`. **30/30 pytest green** on the pure decision core; SPA `vue-tsc` clean.
- **Recipe importer — paste-based rebuild complete, Chunks 1-6 (2026-07-04).** The URL importer is retired end-to-end. Chunks 1-3 stood up a 20/20-green corpus + text-first parser (Class A JSON-LD-free sites like RecipeTin, AllRecipes, HBH, Sally's, Simply, Woolworths, Taste; Class B `<h3>`/`<h4>`-headed sites like Smitten Kitchen). Chunk 4 added a schema-level "unlinked ingredient" affordance (persistable `raw_text` with tri-state cookability that renders neutral until every row is linked). Chunk 5 replaced `POST /api/recipes/import-from-url` with `POST /api/recipes/import-from-content` — server no longer fetches; the user pastes the recipe page and optionally types the source URL for provenance (closes **FU-104** + **FU-199**). Chunk 6 lands the "smart importer" speed thesis: a new **Settings → Admin → Data → Unlinked ingredients** page groups every unmatched ingredient by normalised raw_text and links a whole group with one click (or one click to create a new stock item pre-populated with the raw_text and link in the same request); a PWA `share_target` in `manifest.json` drops the OS Share sheet's title/text/url into `/cookbook`, auto-opening the paste dialog pre-filled; and a paste-friendly hint on the recipe-detail freeform-instructions field covers L261.
- **⭐ P8-07 The Zero-Input Pantry (FLAGSHIP)** — inferred inventory: a server-owned confidence-weighted belief (Out/Low/Stocked band + confidence + reason) per stock item from purchases + cooking + cadence + time-decay; additive "Dora: ~Low" chip beside the recorded level; manual check always wins; single targeted quick-checks only when a decision hinges on an uncertain item; per-user opt-out (default on). New `/api/stock-items/beliefs`. Verify pending (no py env) — 2026-07-03
- **P6-07 cook→consume depletion (FU-449)** — `ConsumptionEvent` now persists on recipe-finish level drops, so run-out prediction shifts when you cook, not only buy (the previously-missing loop leg) — 2026-07-03
- **Dashboard "Log price" quick action** — third button on the dashboard quick-action bar (money-gated); global `LogPriceSheet` mounted alongside `QuickAddSheet` picks a stock item then hands off to the shared `PriceEntry` in shelf mode (closes FU-300) — 2026-07-03
- **Dashboard stock donut deep-links** — Pantry donut low/out segments + legend rows now deep-link to `/stock?level_id=<id>`; card-level whole-card link replaced by a "View →" action for the unfiltered path (closes FU-299) — 2026-07-03
- **Dashboard "Price drops" widget** — new Money-zone card (product-gated, opt-in) + `GET /api/reports/price-drops?limit=N` returning tracked products whose current offer is strictly below every prior historic price (closes FU-296; endpoint smoke pending a Python-capable box) — 2026-07-03
- **Windows + macOS desktop build scripts** — `packaging/build-windows.ps1` (PowerShell) and `packaging/build-macos.sh` mirror `build-linux.sh` step-for-step; README's Desktop-bundle section rewritten to cover all three platforms; cross-platform verify user-driven (closes FU-327; installer packaging still deferred alongside FU-337) — 2026-07-03
- **iOS/WKWebView audio-unlock primer for Dora voice** — `useSpeechOutput` now claims the browser's autoplay credit on first user gesture via a 44-byte silent muted WAV; fixes chat replies going silent on iPhone/iPad after the LLM `await` + Piper synth (closes FU-287; iOS browser-verify pending device access) — 2026-07-03
- **Security + hardening batch** — Requests bumped past CVE-2024-35195 (2.31.0 → 2.32.4); fuzzywuzzy → rapidfuzz (MIT + maintained); global handler rolls back DB session on 500; dead `SelectComponent.vue` + pnpm-only `.npmrc` deleted; FU-196 umbrella disassembled into targeted FU-456..462 (closes FU-196) — 2026-07-03
- **Per-user "Meals per week" preference** — sequential builder's target count is now the user's `meals_per_week` pref (bounds 1-21, null = 7 fallback); wired via new `useMealsPerWeek` composable; Preferences → Meal planning gains a number input (closes FU-181 loose-end 2; loose-end 1 stale) — 2026-07-03
- **Dashboard drops dead `recipeStore.ensureLoadedAsync()` prefetch** — one fewer `GET /recipes` round-trip per dashboard load; nothing on the page consumed it (closes FU-455; FU-052 also resolved by audit) — 2026-07-03
- **Stale-cache guard-race audit** — admin self-patch and post-restore `currentUser` now refresh; onboarding + `/auth/me` paths verified already-correct (closes FU-016) — 2026-07-03
- **Retired last two `lazy="selectin"` overrides** (R-019 / ADR-014) — `Recipe.cuisine` / `Recipe.category` flipped to `noload`; every read site now names its `.include()` (closes FU-314) — 2026-07-03
- **Auto-add-when-low toast wired up** — SPA now surfaces the server's `auto_added` payload as a positive Notify + refreshes the shopping list (closes FU-315) — 2026-07-03
- **Quick-add toast names the destination list + "always ask" pref** (closes FU-316) — 2026-07-03
- **P8-06 Wait-or-Buy** — `wait_hint` on `wait` verdicts + BuyVerdictCard wired into stock-item detail overview (closes FU-437, FU-438) — 2026-07-02
- Onboarding starter-data: per-name checklists + inline paste-rows (FU-195) — 2026-07-02
- StockLevel collapsed to 3 bands: Stocked / Low / Out — 2026-07-02
- C-19 shared auth-shell + AuthButton across 9 pre-auth surfaces — 2026-07-02
- P8-05 "Should I buy this?" buy-verdict oracle (row + shopping-line badges) — 2026-07-02
- P8-02 barcode-to-add via Open Food Facts for unknown EANs — 2026-07-02
- P8-01 rename: Discount Dora → Dashy Dora (full in-repo sweep) — 2026-07-01
- D.O.R.A. bot rename + acronym easter egg — 2026-07-01
- Nav-state policy: filters/search/sort/scroll persist per session (R-026) — 2026-07-01
- QR labels moved to Settings → Kitchen setup (FU-340) — 2026-07-01
- Install-wide image compression settings (FU-345) — 2026-07-01
- Import templates + backup library + admin-gated Data endpoints (FU-343/342/198/341) — 2026-07-01
- Data area collapsed under Settings → Admin → Data; meal-plan Board print (FU-339/338) — 2026-07-01

---

## Where the detail lives

- **`DORA_WORKLOG.md`** — per-session handoff narrative (what ran, decisions, what's next).
- **`CHANGELOG.md`** — product/code changes that shipped.
- **`DORA_FOLLOWUPS.md`** — the full 152-item open backlog (this dashboard shows only the top).
- **`DORA_VERIFY.md`** — your browser-verify checklist (walk + delete as you confirm).
- **The full per-doc register is below** — every planning doc's verified state.
- **Charter / how & why:** `docs/01_charter/` (vision, standards, master plan).
- **To refresh this doc:** see the regeneration routine in `CLAUDE.md`.

**Do not trust as current** (kept for history only): the old `STATUS.md`
(retired to `06_legacy_prompt_plans/`), `99_scratch/PROGRESS_REPORT_2026-06-12.md`
and `FEEDBACK_AUDIT_2026-06-12.md` (June snapshots — say Phase 2/3 = 0%, both wrong
now), `docs/00_DOC_GRAPH.md` (stale, FU-428), and `00_original_spec/` (historical,
pre-dates the current codebase).

---

# Document register

Complete per-doc state map — every active planning doc opened, classified, and
cross-checked against `DORA_WORKLOG.md` + `CHANGELOG.md` + git (verified
2026-07-02). This is the "everything accounted for" backing for the dashboard
above; the dashboard is the rollup, this is the per-doc truth. **You don't need to
read this** — it's the audit trail. 107 active docs across 7 folders; the 157
`docs/00_original_spec/` files are charter-designated historical (one bucket, see
end).

State key: ✅ done-clean · ➗ done-with-carve-outs · 🟡 active · 🔵 designed-not-built ·
⚪ not-started · 🕸 stale · 📦 superseded (successor named) · 🗄 historical.
Investigations: ✅ closed-actioned · 🟡 open · 🔵 informational · 🕸 stale.

## Systemic findings (from the 2026-07-02 audit)

1. **🕸 `docs/00_DOC_GRAPH.md` is stale (FU-428/446).** Indexes ~25 of 48 proposals; cites 2 files that don't exist. Now shrunk to a stub.
2. **🕸 Stale "no code yet" headers on ~15 shipped docs (FU-445).** Bodies are accurate records; only the top status line lies. Judge by this register.
3. **🔴 Security (FU-447).** `AUTH_ASSISTANT_SECURITY_FINDINGS` has an unfixed HIGH CSRF + MEDIUM email-change flaw.
4. **~23 docs orphaned** from the (now-retired) indexes — real, mostly-shipped records.

## 01_charter — governance (3)

| Doc | Type | State | Purpose | Evidence |
|---|---|---|---|---|
| DASHY_DORA_CHAMPION_PLAN.md | Charter | 🟢 authoritative | Vision + 12-principle Decision Charter + P8 prompts | Cited library-wide as arbiter |
| ENGINEERING_STANDARDS.md | Standards | 🟢 authoritative | Code/architecture rubric R-001..R-026 + ADR log | Enforced by CLAUDE.md close-gate |
| RECONCILED_FINISHING_PLAN.md | Master-plan | 🟢 authoritative | 5-phase order, scope, §7 resolved decisions | Self-maintaining |

## 02_feedback — inputs (3)

| Doc | State | Purpose | Evidence |
|---|---|---|---|
| Feedback _ Fixes - as of [06-Jun-2026].md | 🟢 authoritative | Raw user feedback — source of truth | Named SoT in CLAUDE.md |
| COVERAGE_GAPS.md | 🟡 active-living | Tracker: feedback bullets lacking a home | Updated through 2026-06-16 |
| FEEDBACK_TRIAGE_AND_PLAN.md | 📦 superseded (partial) | Feedback→work map | Superseded for sequencing by RECONCILED plan |

## docs/ root — navigation & guides

| Doc | State | Purpose | Notes |
|---|---|---|---|
| 00_DOC_GRAPH.md | 🕸 stale→stub | Per-prompt required-reading map | Shrunk to a stub (FU-428/446) |
| INGESTION_GUIDE.md | 🟢 authoritative | Admin guide: sourcing data via /api/ingest | Matches shipped C-10.x |

## 03_prompts — executable prompts (19)

| Doc | State | Evidence |
|---|---|---|
| 00_INDEX.md | 🕸 stale (banner added) | Status column pre-dates shipped code |
| A1 / A1b / A3 / A6 / A8 | ✅ done | Theme, token-tuning, modal, text-size, renames — all shipped |
| A2 / A4 / A5 / A7 | ➗ carve-outs | Button, filter, skeleton, footer — shipped w/ opportunistic tails (FU-006/011-013/023/024) |
| B1 / B3 / B4 / B5 / B7 / B8 | ✅ done | All bug clusters shipped (CHANGELOG B-series) |
| B9 | ➗ carve-outs | Shipped; item 4 (command palette) deliberately cancelled |
| C_big_rock_design_briefs.md | 🔵→built | 14 briefs → proposals; most built via IMPL_PLANs |
| INV_investigations.md | 🔵→done | INV-1..8,10 produced memos; INV-9 superseded |

## 04_proposals — designs, impl-plans, runbook (49)

| Doc | State | Notes |
|---|---|---|
| PROPOSAL_STOCK_OVERVIEW / _MEAL_PLANS / _COOK_MODE / _COOKBOOK / _CART_BUTTON / _ALERTS / _INGESTION_API / _CONFIG_AND_OPTINS | ✅ done | Big-rock C-1/2/3/4/7/9/10/cross designs — all built via IMPL_PLANs |
| PROPOSAL_STOCK_OVERVIEW / _AUTH_SHELL / _BUY_VERDICT_ORACLE | ✅ done | Auth-shell + buy-verdict shipped 2026-07-02 (⚠️ stale headers, FU-445) |
| PROPOSAL_STOCK_ITEM_DETAIL / _ONBOARDING / _BARCODE_SCANNING / DORA_ASSISTANT_ARCHITECTURE | ➗ carve-outs | Mostly shipped; named deferrals |
| PROPOSAL_COOKBOOK_CARD_REVISION / _RECIPE_IMAGE_STEPS / _WASTE_MINIMISATION / _SHOPPING_LIST_UX_V2 | ✅ done | Shipped; were orphaned from indexes |
| STATE_OWNERSHIP_REFACTOR_PROPOSAL | ✅ done | R-003 authority; IMPL executed |
| PROPOSAL_PRODUCTS_AS_OVERLAY / IMPL_PLAN_PRODUCTS_AS_OVERLAY / PRODUCTS_OVERLAY_RUNBOOK | 🟡 active | Phase F in progress; RUNBOOK is the ⭐ live driver |
| PROPOSAL_HELP_OVERLAY | 📦 superseded | Overlay mechanism retired 2026-07-06 → executed as targeted `(?)` chips per `IMPL_PLAN_HELP_CHIPS.md` (FU-503 / FU-044 both resolved) |
| PROPOSAL_SUPPORT_CHANNEL / _TEST_SUITE_IMPROVEMENTS | 🔵 designed | Real pending design debt |
| IMPL_PLAN_HELP_CHIPS | ✅ done | Executed 2026-07-06 (FU-503) |
| PROPOSAL_LOCALE_I18N | ➗ carve-outs | Layers A + B shipped 2026-07-06 (FU-043); Layer C (full UI translation) explicitly parked as someday |
| PROPOSAL_SIMPLE_MODE | 📦 superseded | → products-as-overlay |
| SHOPPING_LIST_REDESIGN_PROPOSAL | 📦 superseded | v1 shipped (P6-01) → UX_V2 presentation |
| IMPL_PLAN_* (Alerts, Cart, Cookbook, Cook-Mode, Dashboard, Error-Handling, Ingestion, Meal-Plans, Meal-Plans-Rebuild, State-Ownership, Stock-Item-Detail, Stock-Overview, Waste, Your-Prices, Settings-Rebuild, Shopping-Lists, Shopping-List-Receipts, Config, Auth-Shell) | ✅ done | All executed & shipped. ~13 carry stale "no code yet" headers (FU-445). MEAL_PLANS_REBUILD is the live meal-plans authority. |
| IMPL_PLAN_RECIPE_IMPORTER | 🔵 designed | 2026-07-04. Six-chunk paste-based rebuild; supersedes IMPL_PLAN_COOKBOOK §Chunk 7's URL-importer scope. Closes FU-104 / FU-199 / FU-396 (importer half). |
| PLAY_STORE_LISTING | 🔵 designed | 2026-07-04 (P8-10). Play Store copy draft, 6-shot screenshot plan, adaptive-icon note. **No submission** — reference for the day one happens. |
| PROPOSAL_STOCKTAKE_MODE | ✅ done | 2026-07-04. Full stocktake-mode redesign — decisions-locked brief AND shipped end-to-end (Chunks 1–3 backend engine + SPA runner + Settings/Overview surfacing + housekeeping). Anchor for FU-226/430 close-out; SK-1..11 feedback resolved. |

## 05_investigations — reports (16)

| Doc | State | Notes |
|---|---|---|
| AUTH_ASSISTANT_SECURITY_FINDINGS | 🟡 open | 🔴 HIGH CSRF + MEDIUM email-change unfixed (FU-447) |
| STOCK_OVERVIEW_PERF / ORPHANED_FIELDS_AUDIT / FEATURE_CLARIFICATIONS / EMAIL_SETUP_FINDINGS / MAGIC_BEHAVIOUR_AUDIT / PLATFORM_BUILDS_AUDIT / Distribution Spec | 🟡 open | Findings stand; tracked (FU-411/413/415/416/417/418, P5-03) |
| COMMAND_PALETTE / ESSENTIAL_FLAG / HISTORY_TAB / LOGGING_AND_DATA_LAYOUT / RECIPE_COMPARISON | ✅ closed | Recommendations actioned |
| COMMERCIALIZATION_REPORT / MULTI_USER_READINESS | 🔵 informational | Act when the milestone is picked up |
| SUBSTITUTE_SWAP_ASSESSMENT | 🕸 stale | Rec obsoleted by Shop-Mode merge |

## 06_legacy_prompt_plans — historical (8)

All 🗄 historical & correctly retired: `PROMPT_PLAN.md`, `PROMPT_PLAN_PART_2..7`,
`STATUS.md` (self-labels retired 2026-05-27). Superseded by `03_prompts/`.

## 99_scratch — raw notes (5)

| Doc | State | Recommendation |
|---|---|---|
| PROGRESS_REPORT_2026-06-12 / FEEDBACK_AUDIT_2026-06-12 | 🗄 historical | Delete — superseded by this doc (kept briefly for FU cross-refs) |
| PRICING_SYSTEM_REASSESSMENT_HANDOFF | 📦 superseded | Executed into IMPL_PLAN_YOUR_PRICES; archive/delete (FU-425) |
| SENIOR_REVIEW_2026-06-16 | 🗄 historical | Keep — still cited by open FUs |
| MINIMAL_USER_PRODUCTS_OFF_FRICTION | 🗒 untriaged | Only genuinely untriaged note — promote or keep |

## docs/00_original_spec — historical bucket (157 files)

The author's first spec (Feature Boards + ~125 "I can …" notes + original plan).
Charter-designated **historical / non-authoritative** — pre-dates the current
codebase; overridden by charter/plan/feedback. Mined opportunistically when writing
a brief. Treat the whole folder as 🗄 historical; not verified per-file.
