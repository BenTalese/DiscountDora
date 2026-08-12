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

Phases **0** and **2** are effectively done (foundations; ingestion API +
standalone companion, both backend-green). **Phase 1** is now in good shape —
the stocktake-mode redesign shipped end-to-end and the P6 loop tail closed out
(FU-450 deal-quality, FU-451 budget-defense swaps, FU-452 put-away all
**resolved**), and the planner-freeze blocker **FU-595 is fixed**. **Phase 3
(champion) sits at ~95%, fully built** — nothing champion is left to construct;
four surfaces (P8-07 Zero-Input Pantry, P8-08 Kitchen health, P8-09 Memory
reports, P8-10 native Android APK) still need a real-device / browser walk.
Recent work has been a steady **Settings/UX polish stream** (household budget,
AI master-switch removal, Region & locale merge, Account/Kitchen-setup
redesigns, cook-batches meal planner, Build-my-week auto-planner) plus test-infra
hardening. The whole security thread (CSRF + email-change + the residual
assistant findings) is **closed** — FU-447/515/197/620 all resolved.
**Next up:** either a **browser-verify sweep** of the four unverified
champion/native surfaces, or **Phase 4 open-source release readiness**
(README/showcase + release process + donation/support stand-up —
FU-406/608/557); the largest live design backlog is triaging the **FU-578
UX/UI review** into fix units.

---

## Phase board

| Phase | Scope | Status | Remaining |
|---|---|---|---|
| **0 — Foundations** | Theme/buttons/modals/filters/text-size/renames + bug clusters + config/opt-ins | ✅ ~99% | Residual polish only; FU-025/346/609 etc. now closed. |
| **1 — Close the loop** | Shopping lists, cook mode, stock overview, cookbook, suggestions, costing, stocktake | ➗ ~95% | Stocktake redesign shipped; **P6 tail FU-450/451/452 all resolved**; **FU-595 planner-freeze fixed**. Residual browser-verify only. Meal-reconcile Chunk 6 (settings row/copy) pending. |
| **2 — Ingestion API + companion** | `/api/ingest` seam; standalone companion; Merchant→Store rename | ✅ done (backend-green) | Product-surface browser-verify pending (FU-214). |
| **3 — Champion** | Zero-Input Pantry, buy/wait oracles, barcode-add, Dora Score, culinary memory, native app | ➗ ~95% (verify pending) | Sequence P8-01..P8-10 **fully built**. Only browser/device-verify of P8-07/08/09/10 remains; native FCM push deferred (FU-465). |
| **4 — Open-source release** (was Commercialize) | README/showcase + release process + support channel (Postgres done) | ⚪ ~0% | **Not sold — donation/OSS/MIT, all free** (billing/tenancy won't-do). Remaining: FU-406 (README+release), FU-608 (donation/OSS infra), FU-557 (support channel). SaaS/hosted parked (OPTIONAL_SAAS). |

---

## Major workstreams

| Workstream | Status | Where it's at | Governing doc |
|---|---|---|---|
| Products-as-overlay | ➗ | Phases 0–E code-complete; Phase-F tail (FU-214 browser-verify + L197 hard-delete decision + L205/206 bulk-select) pending | [RUNBOOK](docs/04_proposals/PRODUCTS_OVERLAY_RUNBOOK.md) |
| Ingestion API | ✅ | Backend green, bearer-auth lane, admin keys page | [PROPOSAL](docs/04_proposals/PROPOSAL_INGESTION_API.md) |
| Standalone companion | ✅ | Runs standalone (`../dora-companion`); round-trip tests pass | RUNBOOK Phase C |
| Merchant→Store rename | ✅ | `usual_store_id` + Stores page shipped | RUNBOOK Phase E |
| Shopping Lists | ✅ | 8/8 bullets; DRAFT→SHOPPING→DONE loop | [PROPOSAL](docs/04_proposals/SHOPPING_LIST_REDESIGN_PROPOSAL.md) |
| Cook Mode | ✅ | Chunks 1–6 shipped | `C_big_rock_design_briefs.md` |
| Cookbook | ➗ | Chunks 1–10 shipped; recipe-detail residuals; tag-taxonomy env-verify (FU-085) | [PROPOSAL](docs/04_proposals/PROPOSAL_COOKBOOK.md) |
| Stock Overview | ✅ | 3-band StockLevel, buy-verdict badge, Needs-check filter, overdue pulse | `PROPOSAL_STOCK_OVERVIEW` |
| Stocktake Mode redesign | ✅ | Built end-to-end (Chunks 1–3 + housekeeping); SK-1..11 resolved | [PROPOSAL](docs/04_proposals/PROPOSAL_STOCKTAKE_MODE.md) |
| ⭐ Zero-Input Pantry (P8-07) | 🟡 | Built end-to-end; **browser-verify pending** | [PROPOSAL](docs/04_proposals/PROPOSAL_ZERO_INPUT_PANTRY.md) |
| Buy-verdict oracle (P8-05/06) | ✅ | Row + line badges + `BuyVerdictCard`; wait-hints; one-tap actions | [PROPOSAL](docs/04_proposals/PROPOSAL_BUY_VERDICT_ORACLE.md) |
| Barcode-to-add (P8-02) | ✅ | OFF lookup for unknown EANs, gated by `scanning_enabled`; real-barcode register shipped (FU-373) | [PROPOSAL](docs/04_proposals/PROPOSAL_BARCODE_SCANNING.md) |
| Native mobile app (P8-10) | 🟡 | Capacitor 8 wraps SPA; Android/iOS scaffolded; **final APK build + on-device verify pending** | [BUILD_NATIVE.md](packaging/BUILD_NATIVE.md) |
| Onboarding | ➗ | Per-name picks + paste-rows; slimmer bar + dark look; preferred-stores step done (FU-383); **verify pending** | [PROPOSAL](docs/04_proposals/PROPOSAL_ONBOARDING.md) |
| Meal Plans | ➗ | Built end-to-end **+ extended**: Build-my-week auto-planner, day/meal toggles, week-duplicate, cook batches (Part 2) all shipped + verified live. Residual browser-verify only | [PROPOSAL](docs/04_proposals/PROPOSAL_MEAL_PLANS.md) + `IMPL_PLAN_MEAL_PLANS_REBUILD.md` |
| Meal reconcile | ➗ | "Stocktake for meals" — Chunks 1–5 shipped; Chunk 6 (settings row/copy polish) pending | [IMPL_PLAN](docs/04_proposals/IMPL_PLAN_MEAL_RECONCILE.md) |
| Alerts control centre | ✅ | `/alerts` hub, ALERT_ROUTER, price-watch + email-digest + push; shared `resolve_overdue_map` | [PROPOSAL](docs/04_proposals/PROPOSAL_ALERTS.md) |
| Assistant surface | ✅ | Per-user rate limits; SLM default AI path; Basic-mode `add_to_list` verb; AI master-switch removed (per-user only); **multi-provider config + Mode-dropdown settings redesign** (`UserLlmProvider` table; browser-verify owed) | `ask_assistant.py`, `AssistantSettings.vue` |
| Settings & config polish | 🟡 | Active stream: household budget (value-driven), AI master-switch removed, Region & locale merged, Account/Kitchen-setup redesigns, encryption-key banner+generator. Several new DORA_VERIFY walks queued | `CHANGELOG [Unreleased]` |
| Data/Backup admin | ✅ | Under Settings→Admin→Data; backup library + admin-gating | FU-341/342/198 |
| Auth shell | ➗ | Shared `AuthShell`/`AuthButton` across pre-auth surfaces | `PROPOSAL_AUTH_SHELL.md` |
| Postgres datastore | ✅ | Implemented + **default** (SQLite fallback via `DORA_DB_PATH`); FU-045 closed; suite green on PG | `configuration_manager.py` |
| Recipe importer (paste-based) | ✅ | Six chunks landed; parser green 20/20; bulk-linker + PWA share target; **verify pending** | [IMPL_PLAN](docs/04_proposals/IMPL_PLAN_RECIPE_IMPORTER.md) |
| Open-source release (P7) | ⚪ | Not sold — donation/OSS/all-free. Remaining: README/showcase, release process, support channel (FU-406/557/608) | [PLAN §5](docs/01_charter/RECONCILED_FINISHING_PLAN.md) |
| Test suite | ➗ | Backend + frontend Vitest + property + PG all green (~1616 collected; ~412 vitest). Sole remnant: Postgres **CI wiring**, blocked on FU-405 | [PROPOSAL](docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md) |
| Finalisation sweep | 🔵 | Designed, not started — 20 chunks, two-stage, single-maintainer north-star | [PLAN](docs/01_charter/FINALISATION_PLAN.md) + [COVERAGE](docs/01_charter/FINALISATION_COVERAGE.md) |

---

## ⚠️ Needs your attention now

**Total open backlog is 18 items in `DORA_FOLLOWUPS.md`** (the old "~60"
figure was badly stale). These are the ones wanting a decision or a
running-app check, most important first.

1. **Continue the UX/UI review remediation (DR units).** A large owner-requested critical-drive bundle (~50 findings), mapped to DR-1..DR-16. **Done: DR-6, DR-4 (copy/leakage), DR-1 muted-contrast ramp** (all 10 themes ≥4.5:1), **DR-1b badges** (alerts + verdict, AA-verified), **DR-3** (dialog casing sweep + open-toggle glyph/a11y + bulk-bar disabled state; R-039/ADR-035 added), **DR-5** (open-toggle mutation trap — deferred PATCH + 3-outcome dialog, Vitest-pinned). **DR-7** (toast/helper-bubble placement — de-congested the toast corner, tip auto-dismiss, greeting copy; toast-die-on-route carved to FU-624). Remaining DR units: DR-8 (loading polish), then layout/redesigns; DR-10/DR-16 need an owner call. **A brand-secondary rethink spun out as FU-621** (owner: secondary "feels off" + it's invisible as text on dark themes — wants a visual options board, logged FU-622). [FU-578](DORA_FOLLOWUPS.md)
2. **Products-overlay Phase-F verify + hard-delete call.** Product surfaces need a running-app walk with real data; L197 hard-delete is still an undecided design call and L205/206 bulk-select is unbuilt — the runbook's Phase-F blocker. [FU-214](DORA_FOLLOWUPS.md)
3. **⭐ Verify the champion sequence in-browser.** Four surfaces stacked and untested on this dev box — P8-07 Zero-Input Pantry, P8-08 Kitchen health, P8-09 Memory reports, plus P8-10 native Android (APK build + device walk). Pairs with the queued Settings-rework `DORA_VERIFY.md` sections.
4. **Open-source release readiness.** README/showcase + GitHub Releases process + Sponsors link — the Phase-4 gate to publishing publicly; needs your call on scope/timing. [FU-406](DORA_FOLLOWUPS.md)
5. **Stand up donation + OSS infrastructure, then swap in-app placeholders.** Owner-external checklist: make repo public, set up Sponsors / Buy-Me-a-Coffee / PayPal.me, then one placeholder-swap pass. [FU-608](DORA_FOLLOWUPS.md)
6. **Stand up the support channel.** Pick + create the (recommended) public GitHub-issues channel; a one-line config change then lights up Help / error-report / DoraBot. Pairs with FU-406/608. [FU-557](DORA_FOLLOWUPS.md)
7. **Cross-cutting feedback bundle — 4 items still open.** Final QA regression doc, UI-polish/uniqueness pass, cross-user push notifications, general UI consistency — mostly Phase-4 gates needing your steer on when. [FU-363](DORA_FOLLOWUPS.md)
8. **Real-device mobile / PWA field test.** A hands-on device pass; natural to fold into the P8-10 native verify. [FU-389](DORA_FOLLOWUPS.md)
9. **Late-game holistic theme/colour review.** Eyes-on-app pass across the full theme set (Pesto suspected over-dulled); needs the running app. [FU-010](DORA_FOLLOWUPS.md)
10. **App-wide colour-usage assessment** (primary vs secondary/accent/info). Needs eyes-on-app judgement, not a code walk. [FU-224](DORA_FOLLOWUPS.md)
11. **Ops / CI / observability (Phase 4).** Deliberately-disabled CI, backups, staging still unplanned — and CI must not be silently re-enabled; a Phase-4 decision that also unblocks FU-520 (Postgres CI) and FU-404. [FU-405](DORA_FOLLOWUPS.md)

**Lower-priority / trigger-gated** (listed for completeness, not urgent):
FU-520 (Postgres CI — waits on FU-405), FU-404 (compliance — activates
only when hosting user data), FU-576 (uploads spec — needs a bundled-Chromium
run), FU-579 (quasar-dev checker overlay — re-test), FU-575
(name-uniqueness/whitespace — opportunistic), FU-358 (Aldi scraper — when
Aldi data is next needed). *(FU-584 e2e-flake resolved 2026-08-12 — the specs it
named were deleted in the Playwright cull.)*

> **Cleared since last review:** every item the previous PROJECT_STATE listed
> under "Needs attention" is now in `DORA_FOLLOWUPS_RESOLVED.md` — FU-595
> (planner freeze), the whole security thread (FU-447/515/197), FU-620
> (email-change removal), FU-612/609/346/353/606/085/429/025/549/464/355/383,
> and the P6 loop tail FU-450/451/452. Do not reintroduce them as live.

---

## Where the detail lives

- **`DORA_WORKLOG.md`** — per-session handoff narrative (what ran, decisions, what's next).
- **`CHANGELOG.md`** — product/code changes that shipped.
- **`DORA_FOLLOWUPS.md`** — the full 18-item open backlog (this dashboard shows only the top).
- **`DORA_VERIFY.md`** — your browser-verify checklist (walk + delete as you confirm).
- **The full per-doc register is below** — every planning doc's verified state.
- **Charter / how & why:** `docs/01_charter/` (vision, standards, master plan).
- **To refresh this doc:** see the regeneration routine in `CLAUDE.md`.

**Do not trust as current** (kept for history only): the old `STATUS.md`
(retired to `06_legacy_prompt_plans/`), `99_scratch/PROGRESS_REPORT_2026-06-12.md`
and `FEEDBACK_AUDIT_2026-06-12.md` (June snapshots — say Phase 2/3 = 0%, both wrong
now), `docs/00_DOC_GRAPH.md` (stale stub, FU-428), and `00_original_spec/` (historical,
pre-dates the current codebase).

---

# Document register

Complete per-doc state map — every active planning doc opened, classified, and
cross-checked against `DORA_WORKLOG.md` + `CHANGELOG.md` + code reality (verified
2026-08-12 via a 5-agent fan-out). This is the "everything accounted for" backing
for the dashboard above; the dashboard is the rollup, this is the per-doc truth.
**You don't need to read this** — it's the audit trail. **127 active docs** across 8
folders; the 157 `docs/00_original_spec/` files are charter-designated historical
(one bucket, see end).

State key: ✅ done-clean · ➗ done-with-carve-outs · 🟡 active · 🔵 designed-not-built ·
⚪ not-started · 🕸 stale · 📦 superseded (successor named) · 🗄 historical.
Investigations: ✅ closed-actioned · 🟡 open · 🔵 informational · 🕸 stale.

## Systemic findings (from the 2026-08-12 re-audit)

1. **✅ Security thread closed.** `AUTH_ASSISTANT_SECURITY_FINDINGS` is now a triaged standing register — the HIGH CSRF + MEDIUM email-change were fixed under FU-197 (2026-06-30); the 8 residual Medium/Low findings went to FU-515 (resolved); the orphan audit-follow-up FU-447 was reconciled + closed. A.5/A.6/A.7 are accepted risks (A.6 → Phase-4). Nothing open.
2. **🕸 Stale "no code yet" / "designed-not-built" headers on ~15 shipped docs (FU-445).** Bodies are accurate records; only the top status line lies (e.g. IMPL_PLAN_ALERTS, IMPL_PLAN_MEAL_RECONCILE). Judge by this register, not the header.
3. **🕸 `docs/00_DOC_GRAPH.md` is a retired stub (FU-428).** Superseded by this doc + the CLAUDE.md anti-drift rule.
4. **Backlog right-sized.** The old dashboard cited "~60 open items"; the ledger actually holds **17**. Most of the prior attention list had long since moved to `_RESOLVED`.

## 01_charter — governance (6)

| Doc | Type | State | Purpose | Evidence |
|---|---|---|---|---|
| DASHY_DORA_CHAMPION_PLAN.md | Charter / vision | 🟢 authoritative | Part 8 vision + 12-principle Decision Charter + operating procedure | Governing rubric cited across CLAUDE.md |
| RECONCILED_FINISHING_PLAN.md | Master plan | 🟢 authoritative | Phases 0–4, resolved decisions §7, scope arbiter | "Active — all decisions resolved"; owns order/scope |
| ENGINEERING_STANDARDS.md | Rules / ADR log | 🟢 authoritative | R-001..R-040 code rubric + ADR log, checked every task | Living; R-039/040 + ADR-035/036 (dialog noCaps + dialog-gated mutations) added 2026-08-12 |
| DESIGN_STYLE_GUIDE.md | Design spec | 🟢 authoritative | Prescriptive D-rules token/component spec, enforced via R-035 | Authoritative since 2026-07-18; D-019 in [Unreleased] |
| FINALISATION_PLAN.md | Late-game plan | 🔵 designed-not-built | Two-stage code-walk sweep (FST/Help/Review/Tests) | Self-labelled "designed, not started"; verify campaign has since covered similar ground ad hoc |
| FINALISATION_COVERAGE.md | Coverage register | 🔵 designed-not-built | Per-chunk × per-track status matrix for the sweep | All 20 chunk rows ⬜ |

## 02_feedback — inputs (3)

| Doc | State | Purpose | Evidence |
|---|---|---|---|
| Feedback _ Fixes - as of [06-Jun-2026].md | 🟢 authoritative | Raw user feedback — source of truth for coverage tables | Named SoT in CLAUDE.md |
| COVERAGE_GAPS.md | 🟡 active-living | Tracker: feedback bullets lacking a brief/proposal home | Living; entries flip gap→covered as briefs land |
| FEEDBACK_TRIAGE_AND_PLAN.md | 📦 superseded (RECONCILED_FINISHING_PLAN) | Feedback→work map | Superseded for sequencing/strategy; retains what/why map |

## docs/ root — navigation & guides (2)

| Doc | State | Purpose | Notes |
|---|---|---|---|
| 00_DOC_GRAPH.md | 📦 superseded → stub | Former per-prompt required-reading map | Retired (FU-428); CLAUDE.md calls it a legacy stub |
| INGESTION_GUIDE.md | ✅ done-clean | Power-user guide: sourcing data via `POST /api/ingest` | Matches shipped ingestion API (C-10.5) |

## 03_prompts — executable prompts (19)

The whole pack is a historical execution map — live state lives here in
PROJECT_STATE.md. Index banner (verified 2026-07-02): all Wave-A + Wave-B
prompts shipped; every Wave-C brief produced its proposal (most now built via
IMPL_PLAN_*); INV prompts produced their reports.

| Doc | State | Evidence |
|---|---|---|
| 00_INDEX.md | 🗄 historical (banner added) | "Status column is stale… read as historical execution map" |
| A1 / A1b / A2 / A3 / A4 / A5 / A6 / A7 / A8 | 🗄 historical | Wave-A foundation sweeps (tokens, button/modal/filter, skeletons, text-scale, footer, renames) — all shipped |
| B1 / B3 / B4 / B5 / B7 / B8 / B9 | 🗄 historical | Wave-B bug clusters — all shipped (B2/B6 folded); B9 item 4 (command palette) cancelled |
| C_big_rock_design_briefs.md | 🗄 historical | Big-rock briefs → proposals → IMPL_PLANs; C-6/C-8 companion-scope |
| INV_investigations.md | 🗄 historical | INV-1..10 → reports; INV-9 (palette) superseded |

## 04_proposals — designs, impl-plans, runbook (63)

**IMPL plans & runbook (A–M):**

| Doc | Type | State | Purpose | Evidence |
|---|---|---|---|---|
| DESIGN_REMEDIATION_PLAN | Design backlog | 🟡 active | Action the 2026-07-18 UX/design audit (DR-1…16) | DR-1/1b/3/4/5/6 done, DR-7 ➗ (toast-route carve-out FU-624); DR-8 next; rest phased |
| DORA_ASSISTANT_ARCHITECTURE_PROPOSAL | Proposal | ➗ carve-outs | Unify assistant capability model + LLM config | §2.2 registry deliberately not built; §7 multi-provider shipped |
| IMPL_PLAN_ALERTS | Impl plan | ✅ done | Alerts control-centre (C-9) | Digest+push+prefs shipped; header stale |
| IMPL_PLAN_AUTH_SHELL | Impl plan | ✅ done | Extract shared AuthShell + AuthButton (C-19) | `AuthShell.vue`/`AuthButton.vue` exist |
| IMPL_PLAN_CART_BUTTON | Impl plan | ✅ done | Unify add-to-list into one cart control (C-7) | `AddToListButton` in use |
| IMPL_PLAN_CONFIG_AND_OPTINS | Impl plan | ✅ done | Feature-flag/opt-in spine (C-cross) | `useFeatureFlags`/health flags shipped |
| IMPL_PLAN_COOKBOOK | Impl plan | ✅ done | Recipe domain rebuild (C-4) | Structured steps/tags shipped |
| IMPL_PLAN_COOK_MODE | Impl plan | ✅ done | Cook-mode rebuild (C-3) | `RecipeCookMode.vue` live |
| IMPL_PLAN_DASHBOARD_REBUILD | Rebuild brief | ✅ done | Rebuild DashboardPage around savings | `DashboardPage.vue` rebuilt |
| IMPL_PLAN_ENV_TO_APPSETTING | Impl plan | ✅ done | Promote 12 env vars to AppSetting (FU-333B) | Header "SHIPPED 2026-07-05/06" |
| IMPL_PLAN_ERROR_HANDLING | Impl plan | ➗ carve-outs | App-wide error-message polish (FU-099) | `apiErrorHandler.ts` live; full 166-catch sweep unconfirmed |
| IMPL_PLAN_HELP_CHIPS | Impl plan | ✅ done | Add (?) hover-help chips (FU-044) | `help_outline` tooltip pattern across pages |
| IMPL_PLAN_INGESTION_API | Impl plan | ➗ carve-outs | Ingestion `/api/ingest` + Your-Prices (C-10) | Built; browser-verify pending |
| IMPL_PLAN_MEAL_PLANS | Impl plan | ✅ done | Build meal-plans surface (C-2) | Rebuild doc: all F1–F49 shipped |
| IMPL_PLAN_MEAL_PLANS_REBUILD | Critique+rebuild | ✅ done | Re-critique + rebuild the C-2 result | `useMealPlanner.ts` + components exist |
| IMPL_PLAN_MEAL_RECONCILE | Impl plan | 🟡 in-progress | Manual meal-plan reconcile (FU-317) | Chunks 1–5 shipped; Chunk 6 pending; header stale |
| IMPL_PLAN_ONBOARDING | Impl plan | ✅ done | Onboarding redesign + de-persona (C-5/FU-210) | Onboarding pages live |
| IMPL_PLAN_PRODUCTS_AS_OVERLAY | Impl plan | ➗ carve-outs | Chunk detail for products overlay | Phases 0–E done; Phase-F tail open |
| IMPL_PLAN_RECIPE_IMPORTER | Impl plan | ✅ done | Paste-based recipe importer (FU-104/199/396) | Importer machinery present |
| IMPL_PLAN_SETTINGS_REBUILD | Rebuild brief | ✅ done | Rebuild settings shell + sections | "COMPLETE (Phases 1–5 landed)"; reworked since |
| IMPL_PLAN_SHOPPING_LISTS | Impl plan | ✅ done | Shopping-list status-model rebuild (P6-01) | Cited "landed" across surfaces |
| IMPL_PLAN_SHOPPING_LIST_RECEIPTS | Impl plan | ✅ done | Attach receipt photos (FU-334) | "Built 2026-06-30" |
| IMPL_PLAN_STATE_OWNERSHIP | Impl plan | ✅ done | Server-owned derived facts refactor | cookable/missing/allocation SSOT landed |
| IMPL_PLAN_STOCK_ITEM_DETAIL | Impl plan | ✅ done | Stock-item detail polish (C-1b) | Detail page live |
| IMPL_PLAN_STOCK_OVERVIEW | Impl plan | ✅ done | Stock overview redesign (C-1) | `StockOverview.vue`/`StockItemRow.vue` |
| IMPL_PLAN_WASTE_MINIMISATION | Impl plan | ✅ done | Waste-minimisation cluster (C-waste) | `wasteApiService.ts` + mark-as-wasted |
| IMPL_PLAN_YOUR_PRICES | Impl plan | ✅ done | "Your prices" intelligence (Phase F) | "All 8 chunks landed (FU-227/425)" |
| OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT | Option doc | 🔵 deferred | Parked multi-tenant SaaS / managed-host option | Deferred 2026-07-14; kept parked post-pivot |
| PLAY_STORE_LISTING | Listing draft | 🔵 designed | Play Store copy + screenshot plan | "Draft copy; no submission yet" |
| PRODUCTS_OVERLAY_RUNBOOK | Runbook/status | 🟡 active | Drive products-overlay end-to-end | Phases 0–E done, Phase F in progress |

**Proposals (N–Z):**

| Doc | Type | State | Purpose | Evidence |
|---|---|---|---|---|
| PROPOSAL_ALERTS | Proposal (C-9) | ✅ done | Design the alerts control-centre | Realized by IMPL_PLAN_ALERTS |
| PROPOSAL_AUTH_SHELL | Design brief (C-19) | ➗ carve-outs | Shared AuthShell for pre-auth pages | Built; header "no code" stale |
| PROPOSAL_BARCODE_SCANNING | Proposal (P6-02) | ➗ carve-outs | Fix scan data model, gate off-by-default | Implemented; §5.2 ingestion auto-populate deferred |
| PROPOSAL_BUDGET_AWARE_LISTS | Proposal (P2-05 tail) | 🔵 designed | Budget-aware auto shopping-list optimizer | Header "Draft"; no budget logic in `auto_generate.py` |
| PROPOSAL_BUDGET_DEFENSE_SWAPS | Design brief (FU-451/450) | ➗ carve-outs | Over-budget swaps + deal-quality signal | `swap_suggestions.py`/`deal_quality.py` shipped; good_deal alert + product swaps CUT |
| PROPOSAL_BUY_VERDICT_ORACLE | Proposal (P8-05) | ✅ done | In-aisle "should I buy this?" verdict | Leaned on as shipped by adjacent docs |
| PROPOSAL_CART_BUTTON | Proposal (C-7) | ✅ done | Unify all add-to-list controls | `IMPL_PLAN_CART_BUTTON.md` |
| PROPOSAL_CONFIG_AND_OPTINS | Design brief (C-cross) | ➗ carve-outs | Cross-cutting config/opt-in editors | Chunks shipped; chunk 6 verify-only |
| PROPOSAL_COOKBOOK | Proposal (C-4) | ✅ done | Recipe/cookbook domain redesign | `IMPL_PLAN_COOKBOOK.md`; comparison cut per INV-6 |
| PROPOSAL_COOKBOOK_CARD_REVISION | Proposal (FU-088) | ✅ done | Recipe card redesign + optional ingredients | "BUILT — A+B+C shipped" |
| PROPOSAL_COOK_MODE | Proposal (C-3) | ✅ done | Cook mode / finish-loop redesign | `IMPL_PLAN_COOK_MODE.md` |
| PROPOSAL_HELP_OVERLAY | Design brief (C-help) | 📦 superseded (IMPL_PLAN_HELP_CHIPS) | Opt-in contextual help overlay | Superseded 2026-07-06 → help chips |
| PROPOSAL_INGESTION_API | Proposal (C-10) | ➗ carve-outs | Inbound ingest endpoint + "your prices" | Built; register-against-product deferred Phase 2 |
| PROPOSAL_LOCALE_I18N | Design brief (C-locale) | ➗ carve-outs | De-AU currency/format neutrality | Region/currency shipped; full translation out-of-scope |
| PROPOSAL_MEAL_PLANS | Proposal (C-2) | ✅ done | Meal-plan surface redesign | `IMPL_PLAN_MEAL_PLANS(_REBUILD).md` |
| PROPOSAL_MEAL_PLANS_PART_2 | Proposal (FU-617) | ✅ built | Cook batches (one cook, several days) | CHANGELOG "cook batches" 2026-08-11 |
| PROPOSAL_MEAL_RECONCILE | Proposal | ✅ done | Manual meal-plan reconcile | `MealReconcilePage.vue`; header stale |
| PROPOSAL_ONBOARDING | Proposal (C-5) | ✅ done | First-run on-ramp redesign | `IMPL_PLAN_ONBOARDING.md`; personas cut |
| PROPOSAL_PRODUCTS_AS_OVERLAY | Proposal | 🟡 active | Products as data-presence-gated overlay | Runbook-tracked; Phase-F tail |
| PROPOSAL_RECIPE_IMAGE_STEPS | Proposal (C-4 add-on) | ✅ done | Photo-based recipe steps mode | "BUILT 2026-06-25" |
| PROPOSAL_SHOPPING_LIST_UX_V2 | Proposal | ✅ done | Single-page shopping experience | "BUILT 2026-06-12" |
| PROPOSAL_SIMPLE_MODE | Proposal | 📦 superseded (PRODUCTS_AS_OVERLAY) | Minimal-user workflow / pricing substrate | Spine superseded; substrate shipped |
| PROPOSAL_STOCKTAKE_MODE | Proposal (FU-430) | ✅ done | Walk-the-pantry stocktake redesign | Decisions locked + shipped end-to-end |
| PROPOSAL_STOCK_ITEM_DETAIL | Proposal (C-1b) | ✅ done | Stock-item detail polish/timeline | `IMPL_PLAN_STOCK_ITEM_DETAIL.md` |
| PROPOSAL_STOCK_OVERVIEW | Proposal (C-1) | ✅ done | Stock overview redesign | Reconciled against shipped reality |
| PROPOSAL_SUPPORT_CHANNEL | Action plan | ➗ built (dormant) | In-app support/feedback channel | Built off-by-default (FU-370); admin-editor half won't-build; stand-up = FU-557 |
| PROPOSAL_TEST_SUITE_IMPROVEMENTS | Engineering proposal | ➗ carve-outs | Test coverage/quality/cleanup | Built across ~8 sessions; Postgres CI carve-out open (FU-405) |
| PROPOSAL_USAGE_TELEMETRY | Proposal | 📦 superseded (OPTIONAL_SAAS) | Privacy-first usage analytics | Parked hosted-only; self-host won't-do |
| PROPOSAL_WASTE_MINIMISATION | Proposal (C-waste) | ✅ done | Dissolve waste page, keep signal | `IMPL_PLAN_WASTE_MINIMISATION.md` |
| PROPOSAL_ZERO_INPUT_PANTRY | Proposal (P8-07) | ✅ built (verify pending) | Inferred inventory / confidence beliefs | "Built 2026-07-03 server+SPA" |
| SELF_HOST_COMMERCIALIZATION_PLAN | Plan | 📦 superseded | Sequence to sell self-hosted Dora | Reversed 2026-07-31 → donation/OSS (FU-562/567 won't-do) |
| SHOPPING_LIST_REDESIGN_PROPOSAL | Proposal (v1) | 📦 superseded (SHOPPING_LIST_UX_V2) | Shopping-list lifecycle redesign | Structural work shipped as P6-01 |
| STATE_OWNERSHIP_REFACTOR_PROPOSAL | Proposal | ➗ carve-outs | Server-vs-client state ownership refactor | `IMPL_PLAN_STATE_OWNERSHIP.md`; §8 addendum binding |

## 05_investigations — reports (21)

| Doc | Type | State | Purpose/Notes | Evidence |
|---|---|---|---|---|
| DATA_MODEL_SANITY_SWEEP_FU393 | Schema sweep | ✅ closed-actioned | Whole-schema sanity; remediation spawned FU-563/564/565 | Fully remediated 2026-07-15; schema-match test enforces (R-034) |
| PERF_SCALE_SWEEP_FU388 | Perf sweep | ✅ closed-clean | Query-scale at 500/2000 items — no N+1s | "DB/query-scale pass done (clean)" |
| AUTH_ASSISTANT_SECURITY_FINDINGS | Security audit | ➗ closed-with-carve-outs | Auth+assistant register; re-audited 2026-07-13 | HIGH/MED fixed (FU-197/442/515); A.5/A.6/A.7 accepted |
| EMAIL_SETUP_FINDINGS (INV-4) | INV memo | ✅ closed-actioned | Password-reset flow + admin email-setup | Shipped via R-030/FU-413 |
| LOGGING_AND_DATA_LAYOUT (INV-3) | INV memo | ✅ closed-actioned | Time-based rotation + data/cache split | `logging_setup.py` uses TimedRotatingFileHandler (FU-027) |
| ESSENTIAL_FLAG_FINDINGS (INV-10) | INV memo | ✅ closed-actioned | `is_flagged`→`is_essential` wire-up + rename | CHANGELOG 2026-08-08 (migration `f4a2c7e9b1d3`) |
| RECIPE_COMPARISON_ASSESSMENT (INV-6) | INV memo | ✅ closed-actioned | Compare tool — verdict CUT | Comparison UI gone from RecipesOverview; §4 cut |
| COMMAND_PALETTE_ASSESSMENT (INV-9) | INV memo | ✅ closed-actioned | Ctrl-K palette — SHRINK→CUT | Palette/registry/recents removed (FU-029) |
| CROWD_PRICES_ASSESSMENT (INV-11) | INV memo | ✅ closed-actioned | P8-04 crowd price graph — verdict CUT | RECONCILED §7 Decision 6; unblocked FU-438 |
| MAGIC_BEHAVIOUR_AUDIT (FU-092) | Audit | ✅ closed-actioned | All implicit "magic" behaviours; spun FU-315..319 | "Complete; verdicts gathered 2026-06-28" |
| ORPHANED_FIELDS_AUDIT (INV-1) | Audit | ➗ closed-with-carve-outs | Fields set-but-unread; delta-checked FU-416 | Feeds DATA_MODEL_SANITY_SWEEP |
| STOCK_OVERVIEW_PERF (INV-2) | INV memo | ➗ closed-with-carve-outs | Mount cost + latent page-1-only fetch bug (logged FU) | Broader scale cleared by FU-388 |
| PLATFORM_BUILDS_AUDIT (FU-327) | Report | ➗ closed-with-carve-outs | Delivery-target audit; real blocker = dead CI | Report-only; gaps spun as FUs; FU-327 scoped-open |
| UX_DESIGN_CRITIQUE_2026-07-18 | Design critique | ➗ closed-with-carve-outs | Synthesis of FU-578 UX passes; system-vs-screens gap | Feeds DESIGN_STYLE_GUIDE + DESIGN_REMEDIATION_PLAN |
| FEATURE_CLARIFICATIONS (INV-5) | INV memo | 🔵 informational | QR vs register-barcode, product-search, expiry↔open | Partly superseded by barcode-on-Product (FU-373) |
| HISTORY_TAB_ASSESSMENT (INV-7) | INV memo | 🟡 open | Stock-item History tab weak → REWORK | No matching CHANGELOG entry found |
| SUBSTITUTE_SWAP_ASSESSMENT (INV-8) | INV memo | 🟡 open | List-level substitute swap → REWORK (move to Shop Mode) | Swap still lives in list ⋮ menu |
| FU_512_UNIT_OF_WORK_SWEEP_RUNBOOK | Runbook | 🟡 open (analysis-only) | Mechanical UoW refactor guide (10 handlers) | "Analysis-only, no code changes yet" |
| Distribution Spec - Desktop & Mobile Client | Spec/plan | 🔵 designed (partial) | Desktop (PyInstaller) + mobile packaging plan | Desktop/gunicorn shipped (FU-397); mobile Capacitor scaffolded |
| MULTI_USER_READINESS | Pre-flight checklist | 🔵 informational | Single-tenant assumptions to dismantle before multi-user | "Draft for discussion"; Phase-4; ties FU-045 |
| COMMERCIALIZATION_REPORT | Strategy report | 🗄 historical / 📦 partly superseded | Monetization analysis; selling reversed 2026-07-31 | Productionization findings (§3–4) shipped; monetization thread historical |

## 06_legacy_prompt_plans — historical (9)

All 🗄 historical — the original pre-charter plan library, retired 2026-06-12;
superseded by `docs/03_prompts/` (active prompts) and, for state, `CHANGELOG.md`
+ `DORA_WORKLOG.md`. Files: `PROMPT_PLAN.md`, `PROMPT_PLAN_PART_2..4.md`,
`PROMPT_PLAN_PART_5_OPTIONAL.md`, `PROMPT_PLAN_PART_6_POLISH.md`,
`PROMPT_PLAN_PART_7_COMMERCIALIZATION.md`, `STATUS.md` (🕸 stale, last regen
2026-05-27, self-labelled non-authoritative), and
`PRICING_SYSTEM_REASSESSMENT_HANDOFF.md` (✅ fully executed via
IMPL_PLAN_YOUR_PRICES — FU-227, delta-checked FU-425).

## 99_scratch — raw notes (4)

| Doc | State | Recommendation |
|---|---|---|
| MINIMAL_USER_PRODUCTS_OFF_FRICTION | 🗒 untriaged | Fuss-free (products-off) talk-time audit; promote or keep (FU-181) |
| SENIOR_REVIEW_2026-06-16 | 🗄 historical | "Is it sellable?" static review; findings already spun to FUs; LOC metrics dated |
| PROGRESS_REPORT_2026-06-12 | 🕸 stale / 🗄 historical | Point-in-time snapshot; superseded by this doc — safe to delete |
| FEEDBACK_AUDIT_2026-06-12 | 🕸 stale / 🗄 historical | 309-bullet snapshot, stale as of 2026-07-01; evidence pointers only |

## docs/00_original_spec — historical bucket (157 files)

The author's first spec (Feature Boards + ~125 "I can …" notes + original plan).
Charter-designated **historical / non-authoritative** — pre-dates the current
codebase; overridden by charter/plan/feedback. Mined opportunistically when writing
a brief. Treat the whole folder as 🗄 historical; not verified per-file.
