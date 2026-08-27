# Dashy Dora — Project State

**Last reviewed: 2026-08-27.** Milestone-progress front door — phase board,
workstreams, and what needs your attention. This is *not* a changelog;
shipped-work history lives in `CHANGELOG.md` + `DORA_WORKLOG.md`.

This is the single front door: where every phase and workstream is up
to, and what needs your attention. For *where things stand* this doc
wins; for *how/why* a decision was made, follow the linked planning
doc. Regenerated after each substantive close-gate (see
`CLAUDE.md → Regenerating PROJECT_STATE.md`); if it looks out of date,
the last session skipped its close-gate — trust `DORA_WORKLOG.md` +
`CHANGELOG.md` over it.

Status key: ✅ done-clean · ➗ done-with-carve-outs · 🟡 active/in-progress ·
🔵 designed-not-built · ⚪ not-started · 🔴 needs-a-decision · 🕸 stale ·
📦 superseded · 🗄 historical.

---

## Where we are right now

Phases **0** and **2** are effectively done, **Phase 1** sits at ~95% with only
meal-reconcile Chunk 6 left to build, and **Phase 3 (champion) is fully built**
at ~95% pending device walks. The work remains a sustained **owner-feedback
polish stream**, and the last three sessions have all landed on the recipe page:
the old page was deleted on 2026-08-26 (FU-688), and on **2026-08-27** a 26-item
batch shipped **driven live** — R-055 block-editing finally reached the
ingredient rail and the method (one `RecipeStructuredMethod` renders both faces,
three components deleted), step↔ingredient highlighting became bidirectional and
tappable, and a full **FSANZ Health Star Rating** was built from the FoodData
Central category data the importer was already downloading but never opening.
Suites are green at their highest-ever counts — backend **2067 passed** / 1
skipped / 1 xfailed, frontend **497 vitest**, `vue-tsc` + lint clean.
A second **2026-08-27** batch then swept four
surfaces at once (stock overview, settings, stocktake, cook mode), also driven
live: cook mode now follows the recipe's chosen `steps_mode` instead of guessing
from whichever payload is populated, **units became an install-wide setting**
(metric / imperial / US, replacing the invisible `unit_pricing_locale` — R-056 /
ADR-053), and both seeds finally put items with real purchase history into the
stocktake rotation, which is what makes its three-phase shape visible at all.
A third **2026-08-27** batch closed the meal-plan feedback: the planner's
one-shot "generate the week's list" became the *same* reviewable add-to-list
picker the recipe page uses (one component, one flow, four call sites), its
"to buy" count now subtracts what's already on a list, and the Build-my-week
modal was made to fit a phone. That swap produced **R-057 / ADR-054** — *a
replaced endpoint's response is an inventory, not a casualty list* — after the
old endpoint turned out to be the only place the app ever mentioned ingredients
it couldn't put on a list.

The dominant debt is still not building: a large stacked body of shipped UI has
never been seen in a browser, and `DORA_VERIFY.md` holds a long tail of unwalked
checks across stock, stocktake, cookbook, recipe, inference, offline sync and the
whole champion sequence. **Phase 4 (open-source release) remains at ~0%** and needs an
owner call on scope and timing.

---

## Phase board

| Phase | Scope | Status | Remaining |
|---|---|---|---|
| **0 — Foundations** | Theme/buttons/modals/filters/text-size/renames + bug clusters + config/opt-ins | ✅ ~99% | Residual polish only. Live token debt: FU-674 (`--text-on-primary` fails D-002 in three themes), FU-709 (dark themes' `--surface-page` never paints). |
| **1 — Close the loop** | Shopping lists, cook mode, stock overview, cookbook, suggestions, costing, stocktake | ➗ ~95% | **Nothing left to build except meal-reconcile Chunk 6** (settings row/copy). Everything else is browser-verify: stock overview (three batches, 08-20/21/22), stocktake's three-phase runner, cookbook batch 3, and the recipe page's now-four stacked batches. |
| **2 — Ingestion API + companion** | `/api/ingest` seam; standalone companion; Merchant→Store rename | ✅ done (backend-green) | Phase-F tail only: product-surface browser-verify (FU-214), L197 hard-delete decision, L205/206 bulk-select unbuilt. |
| **3 — Champion** | Zero-Input Pantry, buy/wait oracles, barcode-add, Dora Score, culinary memory, native app | ➗ ~95% (verify pending) | P8-01..P8-10 fully built. Browser/device-verify of P8-07/08/09/10 remains; native FCM push parked until SaaS (FU-465). |
| **4 — Open-source release** (was Commercialize) | README/showcase + release process + support channel (Postgres done) | ⚪ ~0% | **Not sold — donation/OSS/MIT, all free.** FU-406 (README+release), FU-608 (donation/OSS infra), FU-557 (support channel). Ops/CI (FU-405) gates FU-520/FU-404. SaaS parked. |

---

## Major workstreams

| Workstream | Status | Where it's at | Governing doc |
|---|---|---|---|
| **Recipe page** | ➗ | **Four batches deep and, since 08-26, the only page — the 2,727-line original is deleted.** The **2026-08-27 batch (26 items) shipped driven live** and its spine was R-055 arriving where it hadn't: the ingredient rail had every editing affordance permanently on and the method's pencil opened a **modal over the thing you were reading**. Both regions now flip whole, and the rule's prose carve-out was retired. `RecipeStructuredMethod.vue` renders **both faces off one `editing` prop** (replacing `RecipeStepsEditor` + `RecipeStepRow` + `RecipeMethodEditorDialog`, all deleted) — promoted as **ADR-052 / a corollary on R-055**, since two components meant numbering, indent and spacing maintained twice. Also: step↔ingredient highlighting is now **bidirectional and tap-driven** (the hover-only version was unreachable on a phone) and the per-step "Uses flour, butter" line went with it; tools are **derived from structured steps** server-side, ordered after the `steps_mode` flip; sub-step indent is measured not eyeballed (numeral centre 33.0px, rule centre 33.0px). The image-steps bug had two causes and the second was the real one — the viewer read `recipe.step_images` (the last-*loaded* list) so a photo picked this session was invisible until save-and-return. Owed: the browser walk (four stacked `DORA_VERIFY` sections) with FU-691 queued behind it | [PROPOSAL](docs/04_proposals/PROPOSAL_COOKBOOK.md) · worklog 2026-08-27 |
| **Health Star Rating** | ➗ | **New 2026-08-27, built end-to-end and verified live.** Full FSANZ HSR, transcribed from Calculator + Style Guide v8.1 (June 2025) — not a homegrown heuristic, the owner's call. The unlock was that FVNL % is **not** a heuristic here: every FoodData Central bundle already carries `food_category.csv`, measured **100% populated across all 7,793 SR Legacy foods**, and the rollup resolves grams, so it's exact arithmetic. `domain/health_star_rating.py` is pure and repository-free so the auditable part is I/O-free; 84 tests, each on a published band edge. Category 2 only. Shows on the nutrition panel with **full working**, plus a cookbook chip, a "Health stars ≥" filter and a sort axis. **Off by default everywhere**; `AdminSystemRegionSettings`' "Match this device" offers it on AU/NZ — reading **IANA timezone first, language second**, after testing found this machine reports `en-GB` with `Australia/Sydney`. Coverage is reported per-nutrient and mass-weighted because the gap is asymmetric (sugars known for only 77% of SR Legacy; a missing penalty nutrient makes a recipe rate *better*). Two honest departures, both surfaced: raw ingredient weight as denominator (FU-748) and no Step-1 automatic ratings | `dora_api/domain/health_star_rating.py` · FU-746..750 |
| Shopping lists (three-face redesign) | ➗ | All three faces built (plan / run / receipt); price comes from **what you last paid**, resolved server-side with provenance (R-053/ADR-049, promoted to R-054/ADR-050). The 2026-08-26 owner batch (16 items) was **driven live at 375px and 1280px**: rebuilt to the Stock-overview toolbar shape, store colours **derived from the uploaded logo server-side** (`Store.brand_colour`, migration `c9f2a7d4e1b8`), phone row relaid out (201px → 130px), and a pre-existing 105px page-wide horizontal scroll found and fixed. Owed: run/receipt faces on the new toolbar (FU-739), real-device walk (FU-729), one owner call (FU-738) | worklog 2026-08-26 + `DORA_VERIFY` → Shopping list |
| Stock Overview | ➗ | Signal consolidation **code-complete, all six chunks**; the row went 9 visual channels → 4, attention is one server-owned rule (`stock_attention.py`) read by outline/count/chip/bell. Three feedback batches since (08-20/21/22) added the expiry-menu date header, the uncertainty ring off the box edge, and **six bulk endpoints** replacing per-item request loops. **None of it walked in a browser** | [IMPL_PLAN](docs/04_proposals/IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md) |
| Stock-item detail | ➗ | 08-21 batch (10/12) plus the 08-24 batch: Barcodes tab became **Scanning** and absorbed the QR label (header button + modal deleted), new shared `HelpHint` (?) moved explainer prose into Help → Guides, header stopped wrapping long names. FU-648 + FU-710 both sit on this tab's critical path and both need a phone or non-localhost host | `DORA_VERIFY` → Stock: 2026-08-24 |
| Buy verdict oracle (P8-05/06) | ➗ | Regraded 2026-08-24 on the owner's own suggestion: a `strength` scale (0–3) from `is_essential` × stock band, modulated by price + waste, replaced the if-ladder that answered "worth buying now" for *any* low item — contradicting `stock_attention.py`'s own rule. `confidence` was split out and means evidence quality only ("Data confidence"). Wording-verify owed | [PROPOSAL](docs/04_proposals/PROPOSAL_BUY_VERDICT_ORACLE.md) |
| Cookbook | ➗ | Chunks 1–10 plus three feedback batches; batch 3 re-ordered filters to reported use, added `Serves ≥`, ran a one-glyph-one-meaning pass, deleted meal-slot names from Category (migration `c8b3e5f0a712`). Now also carries the HSR chip in **both** views — the row-only version shipped invisible on 08-27 and was caught only by looking (FU-747). Open: FU-691, FU-692, FU-693 | [PROPOSAL](docs/04_proposals/PROPOSAL_COOKBOOK.md) |
| Nutrition (complex mode) | ➗ | Built end to end: install-wide mode, USDA + OFF import, 15 micronutrients, server-rendered panel, recipe rollup, cookbook badge, auto-suggest matching. HSR now rides on top. Open: FU-643 (no synonym layer), FU-645, FU-646, FU-657, and **FU-750** (existing installs' `food_category` is NULL, so ratings are systematically pessimistic until a re-import) | `AdminSystemNutritionSettings.vue` |
| Products-as-overlay | ➗ | Phases 0–E code-complete; Phase-F tail is FU-214 browser-verify + L197 hard-delete decision + L205/206 bulk-select | [RUNBOOK](docs/04_proposals/PRODUCTS_OVERLAY_RUNBOOK.md) |
| Prices surface | 🔴 | Investigation confirms the owner's diagnosis: all price *reading* capability sits on the product axis at `/price-history`, which has **no nav entry**, while the everyday user gets a single-item modal with no range and no compare. Placement settled; the keep/cut call is **FU-703** and gates FU-708. A fourth candidate (a Shopping tab on the stock item) was added 08-24 to be weighed, not built | [ASSESSMENT](docs/05_investigations/PRICES_SURFACE_UX_ASSESSMENT.md) |
| ⭐ Zero-Input Pantry (P8-07) | 🟡 | Built and extended (FU-653) to recipes, shopping lists and the meal planner, each behind its own off-by-default opt-in. Server verified live; **all three client renders and the original P8-07 walk unseen** | [PROPOSAL](docs/04_proposals/PROPOSAL_ZERO_INPUT_PANTRY.md) |
| Stocktake Mode | ✅ | Three-phase runner, queue least-certain-first, install-wide switch. **2026-08-27: it finally has a dataset.** Every row used to read the same because the only items in the rotation had no purchase history — the belief fixtures existed but were never `stocktake_alerts` enabled, so nothing could ever rank `confident` and the **Review phase was unreachable by construction**. Both seeds now span all three ranks plus a Sweep fixture; seeding that Sweep exposed a 500 (`resolve_newly_swept` compared a naive `stocktake_last_session_at` against tz-aware values — FU-526's trap, hidden because no user had ever had a past session). The runner's (?) also stopped opening a modal and now deep-links to Help → Guides → Stocktake. Verify owed; FU-700 open | [PROPOSAL](docs/04_proposals/PROPOSAL_STOCKTAKE_MODE.md) |
| Meal Plans | ➗ | Auto-planner, cook batches, per-day calories, lighter swaps shipped + verified. **2026-08-27 feedback batch:** the week's "Generate shopping list" replaced by the *shared* `AddToListDialog` the recipe page uses (rows now carry quantity + which meals want them; optional ingredients aggregated week-wide server-side), the "N to buy" count now subtracts what's already on a list, and the Build-my-week modal fits a phone — all driven live. Evening brief shipped, device-verify owed. Per-slot reminders **won't-do** | [PROPOSAL](docs/04_proposals/PROPOSAL_MEAL_PLANS.md) |
| Meal reconcile | ➗ | Chunks 1–5 shipped; **Chunk 6 (settings row/copy) is the last unbuilt Phase-1 item** | [IMPL_PLAN](docs/04_proposals/IMPL_PLAN_MEAL_RECONCILE.md) |
| Alerts control centre | ✅ | Nine kinds cut to six, severity the only importance scale, email digest deleted whole. Open: FU-702, FU-701 | [PROPOSAL](docs/04_proposals/PROPOSAL_ALERTS.md) |
| Settings & config polish | 🟡 | Active owner-driven stream: nav regrouped, Admin split into five flat groups, Users rebuilt with deactivate-not-delete, Region & locale rebuilt preview-first (now also the HSR nudge host). Several verify walks queued | `CHANGELOG [Unreleased]` |
| Assistant surface | ✅ | Per-user rate limits, SLM default path, multi-provider config, chat-window batch. Browser-verify owed | `ask_assistant.py` |
| Offline / resilience (F3) | ➗ | Was broken end-to-end (replay never attached CSRF, every drain 403'd silently while the UI said "Synced everything"); fixed, R-047/ADR-043. **Live round-trip verify owed** — a mocked transport cannot reproduce it | `useOfflineQueue.ts` |
| Design remediation (DR) | 🟡 | DR-1..11/14/15 done or done-with-carve-outs; **DR-12, DR-13, DR-16 (owner call) remain** | [DESIGN_REMEDIATION_PLAN](docs/04_proposals/DESIGN_REMEDIATION_PLAN.md) |
| Postgres datastore | ✅ | Implemented + default (SQLite fallback). CI wiring remains, blocked on FU-405 | `configuration_manager.py` |
| Test suite | ✅ | Green 2026-08-27: backend **2067 passed** / 1 skipped / 1 xfailed, frontend **497**. This machine: bare `pytest` throws ~56 spurious setup errors — pass `--basetemp=<real dir>` (or set `TMP`/`TEMP`). Remnant: Postgres CI (FU-520) | [PROPOSAL](docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md) |
| Open-source release (P7) | ⚪ | Not sold — donation/OSS/all-free. README/showcase, release process, support channel (FU-406/557/608) | [PLAN §5](docs/01_charter/RECONCILED_FINISHING_PLAN.md) |
| Finalisation sweep | 🔵 | Designed, not started — 20 chunks, two-stage, single-maintainer north-star | [PLAN](docs/01_charter/FINALISATION_PLAN.md) |

---

## ⚠️ Needs your attention now

**Total open backlog is 123 items in `DORA_FOLLOWUPS.md`** (counted 2026-08-27).
These are the ones wanting a decision or a running-app check, most important first.

1. **🟡 One character in `deploy-dora.sh`, and it's still on your desktop (FU-717, resolved-with-cause).** The deploy rsyncs with `--exclude='data'`, which matches the **basename at any depth** — so every deploy deleted `dora_api/features/data/` (15 files) off the server and all of `/api/data/*` 404'd. Change it to `--exclude='/data'` and redeploy. Until you do, FU-648 and FU-710 stay unreproducible. The script also holds your SSH password in plaintext at mode 0664. Follow-ups: **FU-720** (nothing verifies the deployed route map — the app booted clean while serving 404s) and **FU-719**.
2. **🔴 One shopping-list toolbar call (FU-738).** The rebuilt toolbar scrolls sideways exactly as you asked, and the button that runs off the right edge at 1280px is **"Start shopping"** — the lifecycle CTA. Pin it outside the scroller, move it first, or let the band wrap on desktop and scroll only on phones. One decision, then a few lines.
3. **🔴 Decide the fate of the product price axis (FU-703).** You named the cause yourself: products got demoted to a push-your-own-data niche while the stock item was upgraded to carry everyday price functionality. Placement is already settled (price lens on Stock overview + trend section in Reports; alerts advanced-only). The keep/cut call is yours and **gates FU-708**. FU-704/705/706/707 are independent and can start whenever.
4. **Existing installs need a re-import prompt or their Health Star Ratings are wrong in a specific direction (FU-750).** USDA's category was never stored before migration `d1e5b8c3f7a2`, so pre-existing foods score **0 fvnl points** — and on a dish with ≥13 baseline points that *also* locks out the protein credit under the FSANZ gate. Ratings come out systematically pessimistic with nothing on screen saying so. The fix is a user action ("re-run the import"); what's missing is the banner telling them. Small, and worth doing now.
5. **Walk the Health Star Rating against a real USDA import.** Everything was verified end-to-end on **hand-seeded foods**, not your ~7,800-row catalogue — so match quality and panel behaviour at real scale are unknown, as is the AU/NZ nudge on a second device (FU-746). The nutrition surfaces generally need the same walk, and it's that walk that should decide **FU-643** (the missing AU/US synonym layer).
6. **Walk the recipe page — it's now four stacked batches deep with no browser pass underneath.** The 08-26 and 08-27 items were themselves driven live; what's owed is everything beneath them: `DORA_VERIFY.md` → the 08-20 parity pass, the 08-24 batch, the 08-26 section. Two things genuinely can't be agent-driven — the **native file picker** on Change photo, and any **Quasar dropdown**, which never renders in the agent pane (FU-737). FU-691's stylesheet sweep is queued behind this walk, your call.
7. **Walk the 2026-08-22 stock-overview batch — the bulk-bar network check is the one that matters.** Six bulk endpoints replaced per-item request loops on log-waste (and Undo), add-to-list, add-to-chosen-list, mark-restocked, remove-from-list and move. Open devtools Network: **if any bulk action still fires N requests, a call site was missed.**
8. **Walk the whole stock + stocktake surface — it's all built and none of it has been seen (FU-683).** Six chunks, Chunks 3–6 never run in front of a human. Two things to *confirm* rather than check: an overdue shopping day now counts on the bell badge, and the Review phase **legitimately won't appear** until Dora has ~3 logged purchases for something.
9. **Confirm the "Needs attention" chip in a browser after a bulk action (FU-715).** The static read found the chip now does a bare `needs_attention === true` with no client fallback, plus two gaps that would look intermittent: optimistic/offline mutations don't recompute attention until a refetch, and the rule honours mutes but not snooze/dismiss — so **the chip and the bell disagree on a real install**.
10. **🔴 Two install-state bugs that only reproduce on your box.** FU-710 — the barcode register POSTs 404 (same module as the QR 404). FU-648 — the QR dialog failure has never reproduced in three attempts, but the error now names status + ref. Both are downstream of item 1 and both need a phone or a non-localhost host.
11. **🔴 Pick a lever for `--text-on-primary` (FU-674).** Three themes (pesto 3.88, blueberry 4.21, midnight 2.86) fail D-002's 4.5:1 floor **app-wide**. Either darken those themes' ink or darken their `--brand-primary`. One decision, then mechanical.
12. **🔴 Dark themes never paint their authored page colour (FU-709).** Every dark theme declares a `--surface-page` that nothing renders. A colour decision, not a bug fix.
13. **🔴 Small decisions that clear the stock row (FU-685, FU-686).** The row's expiry button still colours off a hardcoded 7 days while its outline reads your configured window — a 14-day setting can outline a row whose expiry pill is still green. And `PantryBeliefChip.vue` is orphaned while three comments still call it the live row form.
14. **Walk the new inference surfaces (FU-653) and round-trip offline sync.** Inference: recipes / shopping lists / meal planner, each toggled separately, all off by default; the seed carries two "Belief demo:" recipes that make it a 30-second check. Offline: it once queued changes and lost every one while reporting success — go offline, change something, come back, **and reload to confirm the server kept it**.
15. **⭐ Verify the champion sequence (P8-07/08/09/10) and the products Phase-F tail (FU-214).** Four champion surfaces stacked and untested, plus the native Android APK build + device walk; pairs naturally with FU-389. Products need a real-data walk, L197 hard-delete is undecided and L205/206 bulk-select is unbuilt.
16. **Phase-4 release readiness needs your steer on scope and timing.** FU-406 (README/showcase + Releases process), FU-608 (make the repo public, stand up Sponsors / BMC / PayPal, then one placeholder-swap pass), FU-557 (support channel — a one-line config change lights up Help / error-report). Ops/CI (FU-405) gates FU-520/FU-404.

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

17. **✅ Security thread closed.** `AUTH_ASSISTANT_SECURITY_FINDINGS` is now a triaged standing register — the HIGH CSRF + MEDIUM email-change were fixed under FU-197 (2026-06-30); the 8 residual Medium/Low findings went to FU-515 (resolved); the orphan audit-follow-up FU-447 was reconciled + closed. A.5/A.6/A.7 are accepted risks (A.6 → Phase-4). Nothing open.
18. **🕸 Stale "no code yet" / "designed-not-built" headers on ~15 shipped docs (FU-445).** Bodies are accurate records; only the top status line lies (e.g. IMPL_PLAN_ALERTS, IMPL_PLAN_MEAL_RECONCILE). Judge by this register, not the header.
19. **🕸 `docs/00_DOC_GRAPH.md` is a retired stub (FU-428).** Superseded by this doc + the CLAUDE.md anti-drift rule.
20. **Backlog right-sized.** The old dashboard cited "~60 open items"; the ledger actually holds **17**. Most of the prior attention list had long since moved to `_RESOLVED`.

## 01_charter — governance (6)

| Doc | Type | State | Purpose | Evidence |
|---|---|---|---|---|
| DASHY_DORA_CHAMPION_PLAN.md | Charter / vision | 🟢 authoritative | Part 8 vision + 12-principle Decision Charter + operating procedure | Governing rubric cited across CLAUDE.md |
| RECONCILED_FINISHING_PLAN.md | Master plan | 🟢 authoritative | Phases 0–4, resolved decisions §7, scope arbiter | "Active — all decisions resolved"; owns order/scope |
| ENGINEERING_STANDARDS.md | Rules / ADR log | 🟢 authoritative | R-001..R-040 code rubric + ADR log, checked every task | Living; R-039/040 + ADR-035/036 (dialog noCaps + dialog-gated mutations) added 2026-08-12 |
| DESIGN_STYLE_GUIDE.md | Design spec | 🟢 authoritative | Prescriptive D-rules token/component spec, enforced via R-035 | Authoritative since 2026-07-18; D-020 (indicator tokens) + **D-021 (nav is one flat level)** added 2026-08-16/17 |
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

## 04_proposals — designs, impl-plans, runbook (64)

**IMPL plans & runbook (A–M):**

| Doc | Type | State | Purpose | Evidence |
|---|---|---|---|---|
| DESIGN_REMEDIATION_PLAN | Design backlog | 🟡 active | Action the 2026-07-18 UX/design audit (DR-1…16) | DR-1/1b/2/3/4/5/6/8/10/11 done (10=owner leave-as-is), DR-7 ➗ (FU-624), DR-9 ➗ (FU-631), DR-14 ➗ (FU-632), DR-15 ➗ (FU-694); remaining: DR-12/13/16 |
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
| IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION | Impl plan | 🟡 active | Collapse the stock row's 9 competing signals → 4; one attention rule, one cadence engine | Written 2026-08-19; **Chunks 1–4 landed** — C1: one cadence engine, D-11 belief→verdict, bulk verdicts endpoint, + the FU-684 bug that made the verdict inert; C2: verdict off the row (D-10), `buy_verdict_enabled` AppSetting→User (D-12/B7, migration `d9f4b2c7e803`), shopping list on the bulk endpoint (B6), all three walked live; C3: Step-0 cuts (3 alert kinds + the digest lane, migration `e4b1c7a95d20`) and one server-owned attention rule; C4: sort + row treatments, 9 channels → 4. **Chunks 5–6 open** (queue ranking, runner rebuild), neither blocked; FU-683 |
| IMPL_PLAN_WASTE_MINIMISATION | Impl plan | ✅ done | Waste-minimisation cluster (C-waste) | `wasteApiService.ts` + mark-as-wasted |
| IMPL_PLAN_YOUR_PRICES | Impl plan | ➗ done-with-carve-outs | "Your prices" intelligence (Phase F) | All 8 chunks landed (FU-227/425) — but the **reading** side never grew a stock-item twin: PRICES_SURFACE_UX_ASSESSMENT (2026-08-21) found compare/range/alerts still product-only; FU-703 |
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
| PROPOSAL_SHOPPING_LIST_UX_V2 | Proposal | ➗ superseded in part | Single-page shopping experience | "BUILT 2026-06-12"; the rail + status enum survive, but its toolbar, header cluster and row anatomy are replaced by the 2026-08-23 three-face redesign (worklog) |
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
| PRICES_SURFACE_UX_ASSESSMENT | INV memo | 🔴 needs-a-decision | "My prices" + price-history UX; the product/stock axis split | 2026-08-21; D2/D3/D4 answered, D1 open as FU-703; defects FU-704..708 |
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
