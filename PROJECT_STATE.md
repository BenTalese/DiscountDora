# Dashy Dora — Project State

**Regenerated: 2026-07-10 (pass 2)** — after the second test-sweep pass the
suite stands at backend **1238 passing** (~45 s; 1 pre-existing FU-328 fail,
5 deliberate strict-xfail FU pins) and frontend **203** Vitest tests. Pass 2
added: search e2e, **DTO contract snapshots** (27 endpoints pinned against a
committed `dto_snapshots.json`), 103 long-tail e2e tests (waste / budget / all
10 reports / stocktake lifecycle / 6 taxonomy routers), and the **first
component-level Vitest** (both StockLevelDots; Quasar mount pattern now
established). Four more findings logged: **[[FU-526]] stocktake queue 500s +
alerts bell breaks while a snooze is active on SQLite (fix next)**, [[FU-527]]
noload count bugs ×2 (third noload incident today — ADR candidate), [[FU-528]]
str/UUID delete-count mismatches, [[FU-529]] reconcile receipt-ordering flake.
FU-519 is now essentially done (minor-surface tail only); FU-520 keeps
AddToListButton / scraper / Postgres CI. Prior refresh: hand-edited row refresh after the
**FU-519/FU-520 targeted test sweep (2026-07-10)**: backend suite **920 → 1096
passing** (~41 s), frontend Vitest **53 → 192** (~1 s, 9 new spec files over the
pure utils/composables). New suites: recipe/meal-plan/dashboard router e2e
(search still open), `SqlAlchemyRepository` operator/paginate suite, emailer
render+send with fake transport, Hypothesis property invariants. The sweep
found **one user-visible production bug — the cookbook `?cookable` /
`?max_missing` / `?expiring_within_days` filters were silent no-ops
(identity-map/noload poisoning in `_restrict_query`) — fixed + test-pinned +
browser-walk queued in DORA_VERIFY** — plus four logged findings: [[FU-522]]
change-email plain-text wrong link, [[FU-523]] Contains/StartsWith
`case_sensitive` inversion, [[FU-524]] `normalise_unit` non-idempotence,
[[FU-525]] buy-verdict UTC/household clock mix. [[FU-518]] closed (per-key
dedup rewrite + `GetAlertsHandler` `now` seam). FU-519/FU-520 bodies now carry
shipped-vs-remaining status; remaining slices (search e2e first, long-tail
surfaces, contract snapshots, component Vitest, Postgres CI) deliberately
deferred per user direction — suite scaled to the app, picked up per-touch.
Prior refresh: hand-edited row refresh after **FU-357 CLOSED
end-to-end + bell crash root-caused and fixed (2026-07-10)**: user's browser
walk on the FU-357 verify steps hit a real `ErrorBoundary` crash on the alerts
bell (`TypeError: all is undefined` at `AlertRow.vue:114`). Static-read root
cause: **FU-317 Chunk 4 (2026-07-09) added the `meal_reconcile_overdue` alert
kind on the backend but never extended the SPA's `AlertKind` union in
`alert.ts`.** Since the union didn't include it, TS couldn't warn about the
missing case in the five kind-switches (`iconFor` / `colorForKind` /
`kindTheme` / `actionsFor` / `linkFor`) — all fell through and returned
`undefined`, so `actionsFor(kind).slice()` threw and blew up the bell. Fixed
by (a) extending the union + adding a case to all five switches with sane
defaults (nav-only nudge, icon `playlist_add_check`, link
`/meal-plans/reconcile`), (b) defensive `?? []` at `AlertRow:112-118` so the
next backend-only kind rollout degrades to a nav row instead of crashing.
Same session also fixed a second finding — **Dashboard alert-action was
silently succeeding/failing** (no `$q.notify` call), so `AlertsBell` +
`AlertsPage` toasted "Done." but Dashboard didn't; parity restored. **FU-357
closed** (the reported "cross-app undo seems off" turned out to be this toast
inconsistency, not an undo — no undo exists on the push_expiry path
anywhere in the SPA, confirmed by grepping every `label: 'Undo'` site). New
**FU-521** logged (state-ownership drift — three hand-rolled alert-action
wrappers + five parallel kind-switch lists) for the finalisation plan Chunk
9 senior review to consolidate. Prior regen note: **Finalisation
plan drafted (2026-07-10)**: new [docs/01_charter/FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md)
+ companion [FINALISATION_COVERAGE.md](docs/01_charter/FINALISATION_COVERAGE.md)
lock the shape of the end-of-project sweep — 20 feature chunks × 4 output tracks
(FST procedure doc, in-app help & guides, senior code review, test plan
inventory). Each chunk gets one deep read with all four tracks advanced from
the same walk; coverage register keeps it honest. Rolled 8 FUs into it: **FU-361
A-4 help content overhaul / FU-320 auto-behaviour documentation / FU-395 P5-11
production readiness review CLOSED end-to-end** at plan draft (moved to
`_RESOLVED` — full scope absorbed into the plan, plan is the sole tracker for
their content). **FU-510 Phase 1** rolled into Track 3 as the hand-rolled-vs-
library per-chunk bucket (Phase 2 stays open for per-swap sequencing).
**FU-406 P7-10 launch readiness + FU-404 P7-08 compliance** stay open with
partial-coverage notes (FST doc handles the QA/exercise halves; legal +
marketing + on-call + DSAR drafting stay out). **FU-010 holistic theme review +
FU-224 colour-usage audit** stay open, riding along as per-chunk signal
collection — the plan populates their shortlists but eyes-on-app judgement
is still needed to close them. No code touched. Prior regen note: **FU-169
CLOSED end-to-end (2026-07-09)**: the earlier Phase-1-tail + Phase-2 land got a
close-out pass — FU-518 root-caused (not fixture-ordering; a freshly-POSTed
expired item generates *both* `stock:{id}:expired` + `stock:{id}:low_stock`
alerts, so dedup misses the second key — test-design flaw, not a Phase 2
architecture issue; xfail marker updated with the finding); parametrize
sweep collapsed the `PageValueIsNotInteger`/`LimitValueIsNotInteger` pair
in five router files into a single `@pytest.mark.parametrize`d test each
(10 → 5 test functions, no coverage loss); Phase 3 (coverage gaps / untested
API surfaces / repository + contract tests) spun off as **[[FU-519]]** and
Phase 4 (frontend Vitest / Hypothesis / scraper + emailer fixtures /
Postgres CI) spun off as **[[FU-520]]** so each can be sequenced
independently. FU-169 itself archived to `DORA_FOLLOWUPS_RESOLVED.md`
with a one-line close note. Prior refresh: a substantial
**FU-169 Phase 1 tail + Phase 2 close-out (2026-07-09)**: `pytest-cov` wired
(report-only, no gate); **per-test DB rollback via SQLite file snapshot**
(the session-scoped `api` fixture snapshots the seeded DB, autouse teardown
rolls back the ORM session + disposes the engine + restores the snapshot
in ~1-3 ms); `tests/factories.py` with `make_stock_location` /
`make_product` / `make_stock_item`; new `uuid_bind` helper in
`tests/support.py`. The pass surfaced + fixed **two real bugs from earlier
today's FU-317 chunks**: (a) `bump_pool`'s `str(uuid)` bind blew up on
SQLite's BINARY(16) UUIDType columns on the ORM caller path (`cook_recipe`)
— fixed via a shared `_id_bytes` normaliser; (b) `_sweep_auto_drain`
lacked the `NOT EXISTS` receipt-guard the manual branch has, so a
`Didn't cook` verb that cleared `consumed_at` triggered the next sweep to
re-drain the entry over the user's decision — guard added. Also hardened
a pre-existing safety hazard (`os.environ.setdefault("DORA_DB_PATH", ...)`
was silently letting `.env` route tests at the dev DB → clobbering it).
Suite state at close: **921 passed / 1 xfailed ([[FU-518]] — new: flaky
digest dedup test only fails during whole-file collection) / 1 failed
(FU-328 pre-existing CSV template hint-row shape, out of scope)**, ~22 s
full runtime. FU-169 remaining tail (parametrize sweep, CI un-comment,
`assert_problem` retrofit, Phase 3/4) stays deferred with a clear
recommended-resolution note. Prior refresh: hand-edited row refresh after **FU-317 Chunk 6
close-out (2026-07-09)**: new **Settings → Admin → System → Meal reconciliation**
page (single install-wide *auto-drain past-day meals* toggle wired to the existing
`AppSetting.auto_drain_past_meals` column + a deep-link chip to the reconcile page
for everyone); Settings left-nav row added; frontend `AppSettings` type extended
to expose the field. That closes the FU-317 impl stack end-to-end — Chunks 1-6
all shipped in a single day. `vue-tsc` clean for touched files (the three
pre-existing DashboardPage `'draft_shop'`/`CardId` errors are unchanged and
unrelated). Prior refresh: hand-edited row refresh after two more polish
units later the same day: **FU-359 A-2 data-pages UI revamp** (Import + Backup
& restore rebuilt onto the shared Settings design language via a new shared
`SettingsFileDrop.vue`; presentation-only, `vue-tsc` clean; FU-359 →
RESOLVED) and **FU-360 #3 mode-slider** (Dora chat header's read-only
Basic/AI chip replaced with a two-position `DoraModeSlider.vue` — tap flips
the user's `llm_enabled` and re-probes; disabled state carries an
explanatory tooltip when the install master's off or the user hasn't
finished configuring a provider; FU-360 remaining tail is #1/#4 browser
verifies only) — plus earlier same day **FU-407 / RD-18** (per-line "Swap
with substitute" on shopping lists disabled up front when the item has no
recorded substitute, via a new server-derived `has_substitutes` flag; also
relabels to disambiguate from the "store offers" picker). Earlier tail on
this date: **FU-387 P5-01 security & privacy hardening bundle sweep landed
end-to-end** (two-session split
— session 1 audited the six P5-01 buckets and produced a greenlit slate,
session 2 executed it). Shipped: prod-default `SESSION_COOKIE_SECURE=True`
(env stays as explicit opt-out), pinned scrypt password hashing via a new
`hash_password()` helper routed through all eight call-sites, backup
credential-exclusion widened (User `llm_api_key_encrypted` + AppSetting
`smtp_password_encrypted` + `vapid_private_key_encrypted`), full Python dep
bump clearing 16 CVEs (`flask-cors 4.0→6.0`, `flask 3.0.2→3.1.3`, `jinja2
3.1.2→3.1.6`, `requests 2.32.4→2.33.0`, `pytest 8.3.4→9.0.3` + compat pins),
`npm audit fix` resolving 3 of 5 frontend vulns (form-data/vite/js-yaml; 2
low-severity dev-only Windows-only esbuild transients accepted pending
upstream Quasar), new [SECURITY.md](SECURITY.md) at repo root, new
[docs/security/SECURITY_REVIEW.md](docs/security/SECURITY_REVIEW.md) as the
standing per-bucket audit doc, new [scripts/security-audit.sh](scripts/security-audit.sh)
on-demand runner. `pip-audit -r requirements.txt --strict` clean. Slate items
dropped by user during execution: P3 per-account lockout, P5 user-isolation
suite (correctly — single-household model has no user-vs-user boundary inside
a household). [[FU-387]] → RESOLVED; [[FU-405]] gained a "promote
security-audit.sh to CI at Phase 4" note.** Earlier same day: **`good_deal`
alert type ripped end-to-end (product-owner call): the alert kind, per-user threshold
column, Preferences → Notifications control, AlertsPage mapping, and migration
`d2f8a1c4b7e9` all removed; `--alert-kind-good-deal` renamed to `--savings-accent`
(still used by the swap-suggestions panel + dashboard savings signpost). Reason:
proactive "product is cheap right now" nudges read like the app pushing users to
buy from stores, which isn't Dora's posture. `DealQuality` compute + its use by
Buy Verdict (fake-markdown demotion) + the FU-451 swap-ranker fake-markdown
filter all unchanged. FU-516 (throttle deviation) deleted — the feature it
described no longer exists. `e3a9c7b1f2d8` rewired to `c7d1a9e3f2b6` as its
down_revision.** Earlier same day: **FU-450 + FU-451 shipped end-to-end (6 chunks):
the deal-quality signal (band enum + `fake_markdown` demotes a price-driven Buy
Verdict `buy`→`wait`) and budget-defense **recipe** swaps (over-budget week →
ranked cheaper-recipe suggestions, preview→apply→undo via `MealPlanSwapLedger`,
migration `e3a9c7b1f2d8`; Suggestions panel + Dashboard signpost). **Product/brand
swaps CUT** — they needed per-item "usual product" upkeep the owner rejected.
Recipe-cost pricing extracted to a shared `recipe_cost` module (R-003)**. Also **FU-432 resolved** — recipe
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
| **0 — Foundations** | Theme/buttons/modals/filters/text-size/renames + bug clusters + config/opt-ins | ✅ ~99% | Residual polish clusters (FU-360/363/431/432); FU-359 + FU-421 + FU-430 + **FU-361 (help content — absorbed into FINALISATION_PLAN)** closed to `_RESOLVED`. |
| **1 — Close the loop** | Shopping lists, cook mode, stock overview, cookbook, suggestions, costing, stocktake | ➗ ~90% | **Stocktake mode redesign shipped end-to-end** (Chunks 1–3 + housekeeping); SK-1..11 resolved. **FU-449 closed** — P6-07 cook→consume `ConsumptionEvent` persists. **FU-351 shipped** — P6-10 "Draft my shop" one-click dashboard card on top of the existing `/auto-generate` engine (2026-07-07). **FU-352 closed** — P6-12 briefing / P8-08 Score coexistence decided (2026-07-07: keep both cards, no fold). Remaining P6 gaps: **FU-450** P6-03 `fake_markdown` (shipped; `good_deal` alert cut same day); **FU-451** P6-09 budget-defense swaps; **FU-452** P6-11 put-away + expiry-by-location grouping. |
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
| **Finalisation sweep** | 🔵 | **Designed, not started (2026-07-10).** 20 feature chunks × 4 output tracks (FST procedure, in-app help & guides, senior code review, test plan inventory) with a coverage register. Rolls in FU-361/320/395 (fully), FU-510 Phase 1, FU-406/404 (partially), FU-010/224 (ride-along). Runs late-game before Phase 4 close-out. | [PLAN](docs/01_charter/FINALISATION_PLAN.md) + [COVERAGE](docs/01_charter/FINALISATION_COVERAGE.md) |

---

## ⚠️ Needs your attention now

Full backlog is **~60 open items** in `DORA_FOLLOWUPS.md`; these are the
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

- **Test sweep pass 2 — +142 backend / +11 frontend tests; FU-519 essentially closed (2026-07-10, later).** Search router e2e (scoring order, per-type subtitles, filter semantics), DTO contract snapshots over 27 endpoints (`dto_snapshots.json`, refresh-via-env-var workflow), 103 long-tail e2e tests across waste/budget/reports/stocktake + the six taxonomy routers, and the first component-level Vitest (both StockLevelDot components; the Quasar mount pattern — client-bundle alias + plugin-vue + per-file jsdom — is now established for future component specs). Four more real findings logged without scope creep: **FU-526 (stocktake queue 500 + broken alerts bell while a snooze is active, SQLite naive/aware compare — fix next)**, FU-527 (two noload-reads-as-empty count bugs; third noload incident today, ADR candidate), FU-528 (str/UUID delete-count mismatches), FU-529 (reconcile receipt ordering lacks a deterministic tie-break; transient idempotence flake observed and root-suspected). Suite: 1238 passed / 5 strict-xfail pins / 1 pre-existing fail, ~45 s; frontend 203, ~1.5 s.
- **FU-519/FU-520 targeted test sweep — +176 backend / +139 frontend tests, cookbook-filter production bug found+fixed (2026-07-10).** Backend pytest 920 → 1096 passing (~41 s); frontend Vitest 53 → 192 (~1 s). New suites: recipe/meal-plan/dashboard router e2e (search still open on FU-519), `SqlAlchemyRepository` operator/paginate/field-map/NOCASE suite on a standalone fixture, emailer template-render + fake-SMTP send-path (29 tests), Hypothesis property invariants over recipe_cookability/stock_status/product_offer/units (26 tests), and 9 frontend spec files over the pure utils/composables. The recipe e2e suite exposed a real user-visible bug — **the cookbook `?cookable` / `?max_missing` / `?expiring_within_days` filters were silent no-ops** (plain id-universe load before the eager cookability/expiring maps left identity-mapped `ingredients` empty, so `cookable=true` kept everything and `cookable=false` returned an empty page) — fixed in `_restrict_query` with the trap documented in place, pinned by four tests, browser walk queued in DORA_VERIFY. Four findings logged (FU-522 change-email plain-text wrong link, FU-523 Contains/StartsWith `case_sensitive` inversion, FU-524 `normalise_unit` non-idempotence, FU-525 buy-verdict UTC/household clock mix — the test-side version of which flaked every AEST morning and was fixed). FU-518 closed: digest dedup test rewritten to per-alert-key assertions; `GetAlertsHandler.handle()` gained a `now` seam. Commented-out CI updated to run bare `pytest` + `npm test` on re-enable (FU-405).
- **Alerts bell crash fixed + Dashboard toast parity + FU-357 closed (2026-07-10).** User's browser walk on FU-357 hit a real `ErrorBoundary` crash on the bell after pushing a few expiries. Root cause: FU-317 Chunk 4 (2026-07-09) added `meal_reconcile_overdue` on the backend but never extended the SPA's `AlertKind` union, so TS couldn't enforce the five kind-switches — all fell through to `undefined` and `AlertRow.vue:114`'s `.slice()` threw. Fixed by extending the union + all five switches (icon `playlist_add_check`, link `/meal-plans/reconcile`, nav-only nudge) + a defensive `?? []` in AlertRow so the next kind rollout can't crash. Same session found and fixed a second real drift — Dashboard's alert-action was silently succeeding (no `$q.notify` while AlertsBell + AlertsPage both toasted "Done."); parity restored. **FU-357 closed** — the reported "cross-app undo seems off" turned out to be this toast inconsistency, not an undo (no undo exists on the push_expiry path anywhere in the SPA, confirmed by grepping every `label: 'Undo'` site). New **FU-521** logged for the state-ownership drift (three hand-rolled alert-action wrappers + five parallel kind-switch lists) — folds into finalisation plan Chunk 9 senior review.
- **Finalisation plan drafted + 3 FUs closed by absorption (2026-07-10).** New [FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md) + [FINALISATION_COVERAGE.md](docs/01_charter/FINALISATION_COVERAGE.md) at `docs/01_charter/`. 20 feature chunks × 4 output tracks (Full Systems Test procedure with an 8-persona × device × condition matrix / in-app help & guides / senior code review / test plan inventory) built up in the same code-walk per chunk. **FU-361 A-4 help content + FU-320 auto-behaviour documentation + FU-395 P5-11 production readiness review CLOSED** — full scope absorbed into the plan (moved to `_RESOLVED`; plan is the sole tracker for their content). **FU-510 hand-rolled-vs-library Phase 1** rolled into Track 3 as a per-chunk `keep / replace / wrap-thin-adapter` bucket, Phase 2 stays open. **FU-406 launch readiness + FU-404 P7-08 compliance** stay open with partial-coverage notes (FST doc + persona flows exercise the QA/DSAR halves; marketing/legal/on-call/DSAR-drafting stay in their own FUs). **FU-010 holistic theme review + FU-224 colour-usage assessment** stay open, riding along — every chunk's senior review logs candidate sites against them so the eventual eyes-on-app pass starts with a triaged shortlist. No code touched.

---

## Where the detail lives

- **`DORA_WORKLOG.md`** — per-session handoff narrative (what ran, decisions, what's next).
- **`CHANGELOG.md`** — product/code changes that shipped.
- **`DORA_FOLLOWUPS.md`** — the full ~60-item open backlog (this dashboard shows only the top).
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

## 01_charter — governance (5)

| Doc | Type | State | Purpose | Evidence |
|---|---|---|---|---|
| DASHY_DORA_CHAMPION_PLAN.md | Charter | 🟢 authoritative | Vision + 12-principle Decision Charter + P8 prompts | Cited library-wide as arbiter |
| ENGINEERING_STANDARDS.md | Standards | 🟢 authoritative | Code/architecture rubric R-001..R-026 + ADR log | Enforced by CLAUDE.md close-gate |
| RECONCILED_FINISHING_PLAN.md | Master-plan | 🟢 authoritative | 5-phase order, scope, §7 resolved decisions | Self-maintaining |
| FINALISATION_PLAN.md | End-plan | 🔵 designed, not started (2026-07-10) | End-of-project sweep: 20 chunks × 4 output tracks; FU rollup for FU-361/320/395/510/406/404/010/224 | New this session |
| FINALISATION_COVERAGE.md | Register | 🔵 blank (2026-07-10) | Per-chunk × per-track status matrix for the finalisation plan | Companion to FINALISATION_PLAN.md |

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
| PROPOSAL_MEAL_RECONCILE | 🔵 designed | 2026-07-09. "Stocktake mode for meals" — per-user auto-drain setting + new `/meal-plans/reconcile` surface + `MealPlanReconcileReceipt` audit table + `meal_reconcile_overdue` alert. Anchor for FU-317 close-out (F5/F6 magic-audit resolution). **Decisions locked; four residuals answered in the impl-plan.** No code yet. |
| IMPL_PLAN_MEAL_RECONCILE | 🟡 in-progress | 2026-07-09. Six-chunk executable plan. **Chunks 1-5 ✅ shipped 2026-07-09** — schema + receipt writer + sweep rewrite (Ch 1); R-003 pool-helper collapse (Ch 2); queue + verb endpoints (Ch 3); `meal_reconcile_overdue` alert + `reconcile_meals_pending` suggestion sharing one `reconcile_overdue_signal` authority (Ch 4); **UX shipped Ch 5** — `/meal-plans/reconcile` runner page + dashboard `ReconcilePastMealsChip` + meal-plans header nudge + `useReconcileQueue.ts` composable. **Chunk 6** (settings row + copy polish + COVERAGE_GAPS flip) is the last thing pending. |

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
