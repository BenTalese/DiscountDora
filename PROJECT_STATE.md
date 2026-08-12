# Dashy Dora — Project State

**Last reviewed: 2026-08-12.** Milestone-progress front door — phase board, workstreams, and what needs your attention. This is *not* a changelog; shipped-work history lives in `CHANGELOG.md` + `DORA_WORKLOG.md`.

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
| **4 — ~~Commercialize~~ → Open-source release** | ~~Tenancy, billing, compliance~~ → README/showcase + release process + support channel (Postgres already done) | ⚪ ~0% | **Not being sold (reversed 2026-07-31): donation-funded, open-source, MIT kept, all features free.** Billing/tiers/relicense are **won't-do** (FU-562/FU-567 RESOLVED); no billing code ever existed. Remaining Phase-4 work is **open-source *release* readiness** — FU-406 (README + GitHub Releases process + Sponsors link) + FU-557 (best-effort GitHub-issues support). **Postgres done + default** (FU-045). SaaS/hosted parked (OPTIONAL_SAAS). |

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
| ~~Commercialization~~ → Open-source release (P7) | ⚪ | **Not sold — donation/open-source/all-free (reversed 2026-07-31).** No billing/tenancy code, none planned. Remaining: README/showcase, release process, support channel (FU-406/557). | [PLAN §5](docs/01_charter/RECONCILED_FINISHING_PLAN.md) |
| **Finalisation sweep** | 🔵 | **Designed, not started (2026-07-10; model revised 2026-07-13).** 20 feature chunks, **strict two-stage**: **Stage 1 — Analysis** (read file-by-file; 4 written tracks — FST / help & guides / senior code review / test-plan; the review record is *execution-ready*: exact file:line + change per finding; **no code changed**), then **Stage 2 — Execution** (apply the exact changes from the record — DRY/dead-code/componentisation/placement/naming/standards + verified bugs — test-guarded, **no re-investigation**). **North-star (owner directive):** the app must be hand-maintainable by one person with no AI. Feature-rewrites / contract / large-blast-radius items → new proposal/FU, not in scope. Rolls in FU-361/320/395 (fully), FU-510 Phase 1 + safe Phase-2 swaps, FU-406/404 (partially), FU-010/224 (ride-along). Runs late-game before Phase 4 close-out. | [PLAN](docs/01_charter/FINALISATION_PLAN.md) + [COVERAGE](docs/01_charter/FINALISATION_COVERAGE.md) |

---

## ⚠️ Needs your attention now

Full backlog is **~60 open items** in `DORA_FOLLOWUPS.md`; these are the
ones that want a decision or a running-app check *now*, most important
first.

0. **🔴 BLOCKER — [FU-595](DORA_FOLLOWUPS.md) a past meal you didn't cook FREEZES the whole week.** Found 2026-07-22 walking the planner. If a week holds a past-dated entry with no `consumed_at`, **every** attempt to add a meal to that week returns 400 and **hard-crashes the planner to the error screen**. The server preserves history by `consumed_at is not None` but rejects submissions by `scheduled_for < today`, so a past-but-unconsumed entry can neither be kept by the server nor resent by the client — and the client resends it. Reachable two first-class ways: **auto-drain OFF**, and **reconcile → "Didn't cook"**. Needs a contract decision (preserve past entries regardless of consumption / ignore-rather-than-reject unchanged past entries / stop sending them) — three viable shapes, so it wasn't a safe drive-by fix. The secondary half — a 400 taking down the whole screen instead of a toast — is worth fixing either way. **This also blocks further planner verification:** any week with an unreconciled past meal can't be walked for adds.

0. **✅ RELIABILITY — [FU-549](DORA_FOLLOWUPS_RESOLVED.md) fresh-install migration boot — FIXED 2026-07-13.** The empty-DB `upgrade head` crash (`a3e9f6c2d8b4`, Alembic batch/BINARY) is fixed (UUIDType-column renames pass `sa.BINARY(16)`); the full 116-migration chain now applies cleanly from empty, `alembic` is pinned, and 2 migration tests (from-empty upgrade + schema-vs-model match) now run + guard it. **Residual:** a one-time operator smoke on a real fresh `pip install` (DORA_VERIFY §Operator), and [[FU-553]] — a downgrade-only (`downgrade base`) SQLite CHECK-drop issue that doesn't affect boot.
0. **🔴 SECURITY — unfixed HIGH + MEDIUM findings.** `docs/05_investigations/AUTH_ASSISTANT_SECURITY_FINDINGS.md` records a **HIGH CSRF** flaw and a **MEDIUM email-change** flaw with no fix logged. Surfaced by the 2026-07-02 doc audit — decide whether to fix now before more champion work. Tracked as [FU-447](DORA_FOLLOWUPS.md).
1. **🔴 Meal Plans — pick the screen style + give feedback.** The feature is **built** (board/calendar/templates all shipped); it's waiting on *your* UX-direction call, not on engineering.
2. **🔴 FU-346 — Admin settings "feel hidden."** You raised this. Short direction call needed (stay put / header icon / `/admin` route) before any code moves.
3. **🔴 FU-353 — Rename GitHub repo + local checkout to DashyDora.** Your action (`gh repo rename` + `mv`); until then release-check URLs + README badges 404.
4. **⭐ Verify the champion sequence in-browser.** Four surfaces stacked and untested on this dev box: **P8-07 Zero-Input Pantry** (walk `DORA_VERIFY.md §Stock`); **P8-08 Kitchen health card**; **P8-09 Memory reports**; **P8-10 Native Android APK** (final build + device walk). The stocktake redesign's Chunks 2 + 3 verify blocks in `DORA_VERIFY.md` also want the same walk.
5. **FU-085 — Cookbook tag-taxonomy never run in a real env.** Verify the migration on SQLite + Postgres before building on it.
6. **FU-214/FU-208 — Products-overlay verify mostly cleared (2026-07-24).** My Products + Price History walked on the money seed (mark-inactive, Link…, price chart — with FU-605 fixed en route). What's left is the **FU-606 decision** below and the onboarding-wizard walk; hard-delete is confirmed a deliberate non-feature (soft-deactivate only, ingestion model).
6b. **🔴 FU-606 — quick yes/no: My Products bulk-select.** Confirm the generic "Select on-deal" bulk suffices (recommended) vs. building stock-level-aware variants ("low-stock-on-deal" / "out-of-stock-on-deal"). Recommend **won't-do** — stock-aware buying is already served by Draft-my-shop / buy-verdict / auto-add-on-low.
7. **FU-429 — Assistant-architecture proposal collides with in-flight SLM work.** `DORA_ASSISTANT_ARCHITECTURE_PROPOSAL` proposes a capability registry that the SLM pivot may supersede; needs a reconcile-or-close decision.
7b. **🔴 FU-612 — quick decision: what happens to the `meals_per_week` preference?** The meal-plan builder's count slider was its only consumer and is now gone, so the Settings → Preferences row saves a value nothing reads. Either delete it end-to-end, or repurpose it (e.g. seed the builder's default day selection instead of defaulting to every remaining day).
8. **FU-025 follow-on — component labels ignore the text-scale tokens.** Button/input/toggle labels don't track the A6 scale; small global sweep.

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
| FINALISATION_PLAN.md | End-plan | 🔵 designed, not started (2026-07-10; model revised 2026-07-13) | End-of-project sweep, 20 chunks, **strict two-stage** (Stage 1 analysis → execution-ready written findings; Stage 2 execution from the record, no re-investigation) under the single-maintainer north-star; FU rollup for FU-361/320/395/510/406/404/010/224 | Two-stage model 2026-07-13 |
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
| PROPOSAL_SUPPORT_CHANNEL | ➗ built (dormant) | FU-370: code half shipped off-by-default; hardcoded author-controlled switch, never an admin AppSetting (settled, FU-558; §4.1/§4.2 withdrawn). Channel stand-up = FU-557 |
| PROPOSAL_TEST_SUITE_IMPROVEMENTS | ➗ carve-outs | Built across ~9 sessions (FU-371 resolved 2026-07-13); Phases 1-3 done, Phase 4 (FU-520) all but item 1. `useOfflineQueue` spec (2026-07-15) drained item 3's last surface; frontend Vitest 385/30. Sole carve-out left: **Postgres CI + coverage gate, blocked on CI-off (FU-405)** — suite already green on PG via `DORA_TEST_DB` selector. (scraper tests live in companion repo, FU-161) |
| IMPL_PLAN_HELP_CHIPS | ✅ done | Executed 2026-07-06 (FU-503) |
| PROPOSAL_LOCALE_I18N | ➗ carve-outs | Layers A + B shipped 2026-07-06 (FU-043); Layer C (full UI translation) explicitly parked as someday |
| PROPOSAL_SIMPLE_MODE | 📦 superseded | → products-as-overlay |
| SHOPPING_LIST_REDESIGN_PROPOSAL | 📦 superseded | v1 shipped (P6-01) → UX_V2 presentation |
| IMPL_PLAN_* (Alerts, Cart, Cookbook, Cook-Mode, Dashboard, Error-Handling, Ingestion, Meal-Plans, Meal-Plans-Rebuild, State-Ownership, Stock-Item-Detail, Stock-Overview, Waste, Your-Prices, Settings-Rebuild, Shopping-Lists, Shopping-List-Receipts, Config, Auth-Shell) | ✅ done | All executed & shipped. ~13 carry stale "no code yet" headers (FU-445). MEAL_PLANS_REBUILD is the live meal-plans authority. |
| IMPL_PLAN_RECIPE_IMPORTER | 🔵 designed | 2026-07-04. Six-chunk paste-based rebuild; supersedes IMPL_PLAN_COOKBOOK §Chunk 7's URL-importer scope. Closes FU-104 / FU-199 / FU-396 (importer half). |
| PLAY_STORE_LISTING | 🔵 designed | 2026-07-04 (P8-10). Play Store copy draft, 6-shot screenshot plan, adaptive-icon note. **No submission** — reference for the day one happens. |
| PROPOSAL_STOCKTAKE_MODE | ✅ done | 2026-07-04. Full stocktake-mode redesign — decisions-locked brief AND shipped end-to-end (Chunks 1–3 backend engine + SPA runner + Settings/Overview surfacing + housekeeping). Anchor for FU-226/430 close-out; SK-1..11 feedback resolved. |
| PROPOSAL_MEAL_PLANS_PART_2 | ✅ built | 2026-08-11. **Cook batches** — one cook feeds several days. **BUILT END-TO-END + verified live** (FU-617 resolved). Backend: `CookBatch` entity/table/migration `d5a9f27c4e18`, `cook_key` grouping+validation, derived read view. Manual UI: "Cook · serves N"/"Leftovers" markers + link/unlink menu + day-picker, gated on the Batch cook-style. Builder: "Build my week" proposes cooks (one recipe per 3-day run for Batch households; ties off FU-611). `test_cook_batches.py` 10 + `test_build_week.py` +3; consolidated gate 59 green; verified live (18 markers → 6 CookBatch rows). Proposal Phases 2/3 dropped as no-ops (Σ-yield batch-invariance, pinned by test). One light owner-walk queued (the manual day-picker dialog). (same recipe+slot, distinct days). First-class `CookBatch` + `MealPlanEntry.cook_batch_id`; `cook_key` grouping on the write path; batch = demand unit (counted once at total yield), entry = consumption unit; 6 aggregation impact points listed; reconcile cook-once-drain-many; per-entry linked-cook UI (no layout rebuild); builder auto-proposals for Batch households (also the honest FU-611 fix). Folds into the existing `batch_features_enabled` cook-style. Open decisions all closed; grounded in a 4-agent code investigation. Build = **FU-617**. No code yet. |
| PROPOSAL_MEAL_RECONCILE | 🔵 designed | 2026-07-09. "Stocktake mode for meals" — per-user auto-drain setting + new `/meal-plans/reconcile` surface + `MealPlanReconcileReceipt` audit table + `meal_reconcile_overdue` alert. Anchor for FU-317 close-out (F5/F6 magic-audit resolution). **Decisions locked; four residuals answered in the impl-plan.** No code yet. |
| IMPL_PLAN_MEAL_RECONCILE | 🟡 in-progress | 2026-07-09. Six-chunk executable plan. **Chunks 1-5 ✅ shipped 2026-07-09** — schema + receipt writer + sweep rewrite (Ch 1); R-003 pool-helper collapse (Ch 2); queue + verb endpoints (Ch 3); `meal_reconcile_overdue` alert + `reconcile_meals_pending` suggestion sharing one `reconcile_overdue_signal` authority (Ch 4); **UX shipped Ch 5** — `/meal-plans/reconcile` runner page + dashboard `ReconcilePastMealsChip` + meal-plans header nudge + `useReconcileQueue.ts` composable. **Chunk 6** (settings row + copy polish + COVERAGE_GAPS flip) is the last thing pending. |

## 05_investigations — reports (18)

| Doc | State | Notes |
|---|---|---|
| DATA_MODEL_SANITY_SWEEP_FU393 | ✅ done | P5-08 whole-schema sweep (2026-07-14). Found model↔migration index drift (1 vs 32), 42 unindexed FK cols, 3 Product nullability mismatches → remediation FU-563/564. Read-only. **Fully remediated 2026-07-15** — FU-563 (index drift closed + 43 FK indexes), FU-564 (Product nullability), FU-565 (6 FK ondelete); schema-match test now enforces tables+columns+nullability+index/unique+FK-ondelete (R-034/ADR-030). No residual |
| PERF_SCALE_SWEEP_FU388 | ✅ done | P5-03 perf sweep — no N+1s; `/api/health` query fix; residual axes → FU-560 |
| AUTH_ASSISTANT_SECURITY_FINDINGS | 🟡 open | 🔴 HIGH CSRF + MEDIUM email-change unfixed (FU-447) |
| STOCK_OVERVIEW_PERF / ORPHANED_FIELDS_AUDIT / FEATURE_CLARIFICATIONS / MAGIC_BEHAVIOUR_AUDIT / PLATFORM_BUILDS_AUDIT / Distribution Spec | 🟡 open | Findings stand; tracked (FU-411/415/416/417/418) |
| EMAIL_SETUP_FINDINGS (INV-4) | ✅ shipped | Proposal (admin SMTP-on-AppSetting + hide forgot-password when unconfigured) shipped via FU-333; verified + closed FU-413 (2026-07-14) |
| COMMAND_PALETTE / ESSENTIAL_FLAG / HISTORY_TAB / LOGGING_AND_DATA_LAYOUT / RECIPE_COMPARISON | ✅ closed | Recommendations actioned |
| COMMERCIALIZATION_REPORT / MULTI_USER_READINESS | 🗄 historical (monetization) | **Selling reversed 2026-07-31 → donation/open-source/all-free.** The report's whole monetization thread (billing/tiers/relicense/freemium) is now historical; its productionization findings (§3–4) still stand + shipped. FU-400/401/399/398/403/402 stay parked in OPTIONAL_SAAS below |
| SELF_HOST_COMMERCIALIZATION_PLAN (04_proposals) | 📦 superseded | **Superseded 2026-07-31** (banner added) — sequenced the paid tracks; FU-562 (billing) + FU-567 (relicense) RESOLVED won't-do. Residual = open-source *release* readiness (FU-406/557) |
| OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT (04_proposals) | 🔵 deferred option | "Revisit later" bucket for multi-tenant SaaS (Path A) + managed single-tenant (Path B) + scale/billing. Even less likely post-pivot (donation/OSS) but **kept parked, not closed** (owner, 2026-07-31). Created 2026-07-14 |
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
