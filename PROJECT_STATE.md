# Dashy Dora — Project State

**Last reviewed: 2026-09-03.** Milestone-progress front door — phase board,
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
meal-reconcile Chunk 6 left to build, **Phase 3 (champion)** is built at ~95%
pending device walks, and **Phase 4 (open-source release) remains ~0%**. The work
is a sustained **owner-feedback polish stream** that has now walked the app
surface by surface — shopping lists, meal planner, cook mode, the dashboard
review (6/6 chunks), the `/reports` review (5/5, closed 09-02), and on
**2026-09-03 alone four consecutive owner batches**: themes/segmented anatomy,
cook mode (5 items), cookbook + recipe view (15 items), and Settings (~35 items)
— every one driven live in a browser at 375 and 1280. The recurring finding has
hardened into a pattern: reported *design* complaints keep having real defects
underneath, and the 09-03 run produced three of the sharpest yet — a `NameError`
that made **every voice download fail, always**, in a module `tests/` never
referenced once; a **$16.50 three-egg omelette** caused by a pack model that
assumed one pack holds one countable thing; and an "install unavailable in this
browser" message that had never asked the browser anything (the real cause was
plain `http://`). Those became **R-076/ADR-073** (*a derived figure never rests
on a fact the data does not record*) and **R-077/ADR-074** (*an unavailable
capability names the condition it actually tested*), alongside **R-074/ADR-071**
(planned demand as a sibling signal, not a term inside `compute_belief`) and
**R-075/ADR-072** (*a layout fix isn't done until the running app is measured*).
Suites are at their highest — backend **2275 passed** / 1 skipped / 1 xfailed,
frontend **685 vitest across 61 files**, `vue-tsc` + `eslint src/` clean, with
the four pre-existing buy-verdict e2e reds outstanding (FU-762). The dominant
debt is unchanged: a large stacked body of shipped UI has still never been seen
in a browser by a human, though the last several units are now the exception
rather than the rule.

---

## Phase board

| Phase | Scope | Status | Remaining |
|---|---|---|---|
| **0 — Foundations** | Theme/buttons/modals/filters/text-size/renames + bug clusters + config/opt-ins | ✅ ~99% | Residual polish only. Live token debt: FU-674 (`--text-on-primary` fails D-002 in three themes), FU-801 (`--brand-primary` fails the same ink test), FU-850 (`--accent-mark` adoption beyond the sites this pass touched), FU-709 (dark themes' `--surface-page` never paints), FU-834/FU-764 (~20 undeclared custom properties app-wide; no lint gate), FU-777, FU-839. |
| **1 — Close the loop** | Shopping lists, cook mode, stock overview, cookbook, suggestions, costing, stocktake | ➗ ~95% | **Nothing left to build except meal-reconcile Chunk 6** (settings row/copy). Everything else is browser-verify: stock overview (08-20/21/22 batches), stocktake's three-phase runner, cookbook batch 3 + the cookbook-list lines the agent pane can't render, the recipe page's older stacked batches (08-20 parity pass, 08-24), the buy-verdict money gate, and the `planned_store_id` round trip (blocked, not skipped). |
| **2 — Ingestion API + companion** | `/api/ingest` seam; standalone companion; Merchant→Store rename | ✅ done (backend-green) | Phase-F tail only: product-surface browser-verify (FU-214), L197 hard-delete decision, L205/206 bulk-select unbuilt, FU-210 tail browser pass. **FU-856** — `pack_count` can't be recorded through the products API at all, so R-076's better answer is unreachable. |
| **3 — Champion** | Zero-Input Pantry, buy/wait oracles, barcode-add, Dora Score, culinary memory, native app | ➗ ~95% (verify pending) | P8-01..P8-10 fully built. Browser/device-verify of P8-07/08/09/10 remains; native FCM push parked until SaaS (FU-465). |
| **4 — Open-source release** (was Commercialize) | README/showcase + release process + support channel (Postgres done) | ⚪ ~0% | **Not sold — donation/OSS/MIT, all free.** FU-406 (README+release), FU-608 (donation/OSS infra), FU-557 (support channel), FU-861 (no real build number anywhere — needs a version source through bundle + API). Ops/CI (FU-405) gates FU-520/FU-404/FU-721. SaaS parked. |

---

## Major workstreams

| Workstream | Status | Where it's at | Governing doc |
|---|---|---|---|
| **Settings & config polish** | 🟡 | The most active stream. The 09-03 owner sweep took **~35 items across nine pages**, driven live at both widths: narrow-control rows keep two columns on a phone (Notifications/Assistant no longer read as orphaned switches), Zero-Input Pantry's five paragraphs became five named lines + info chips, Stores renames in place and changes its logo by clicking it, Stock locations reads as one tree again (one `LocationAddChip` for "+ Area"/"+ Section"), and three pages stopped speaking raw Quasar — new shared `css/settingsCards.scss`, plus new `settings/LocationAddChip.vue` and `nutritionMatchingStore.ts`. Open: FU-858, FU-859, FU-860, FU-861 | `CHANGELOG [Unreleased]` |
| **Recipes & cookbook** | ➗ | 15-item owner batch shipped 09-03. **R-076/ADR-073** came out of it: one `_item_price` helper now owns "what does one of these cost?" across both the offer and observation branches and is allowed to answer *no*; seeds set `eggs_woolies.pack_count = 12` so the case resolves to $0.46/egg rather than an honest blank. Free-text steps share the structured face's numbering via new `css/recipeSteps.scss`. Open: FU-855, FU-856, FU-857 | `recipe_cost.py` · `css/recipeSteps.scss` |
| **Cook mode** | ➗ | Five owner items 09-03: header collapsed to one band (first step ~60px higher at 375), Prev/Repeat/Next share one row and all clear the 44px floor (they previously missed by 2px), the finish modal's level picker became the shared `StockLevelPicker`, and its hand-rolled cart button — which named the retired "primary list" concept — is now the shared add-to-list button. Open: FU-853, FU-854 | `AddToListButton.vue` |
| **Reports page** | ✅ | Review closed — all five chunks shipped 09-02, every one driven live. Money-gated (R-058); eleven cards → four question-led ones plus a lede; **Price changes** added; **ECharts deleted** (route chunk 549 KB → 24 KB on the app's own 8 KB SVG chart, R-073/ADR-070). Open: FU-843, FU-844, FU-845 #8, FU-846, FU-847 | [REVIEW](docs/05_investigations/REPORTS_PAGE_REVIEW.md) |
| **Dashboard** | ✅ | Review closed — 6/6 chunks, all seven owner calls answered. 17 cards → 14 (11 default-on) with a test holding the count; all eleven loaders stopped turning a failed fetch into a reassuring empty state; `DashboardPage.vue` 3,258 → **1,888 lines** (R-072/ADR-069). Spin-offs: FU-831, FU-832, FU-835..839, FU-841 | [IMPL_PLAN_DASHBOARD_REBUILD](docs/04_proposals/IMPL_PLAN_DASHBOARD_REBUILD.md) |
| **Theming & design tokens** | 🟡 | Seven families now: **Salt & Pepper** (neutral — one warm graphite hue; semantics and the six chart hues deliberately kept) and **Dragonfruit** (first pink) added 09-03, every pairing measured live. Accent split into `--accent-ink` (text) and `--accent-mark` (~7 lightness points brighter, for marks graded at 3:1 by D-002). Open: FU-850, FU-801, FU-674, FU-709, FU-834, FU-764 | `themes.scss` · `DESIGN_STYLE_GUIDE.md` |
| **Shared component anatomy** | 🟡 | 09-03 collapsed **four looks of one control** into the pill anatomy with shared `--seg-*` tokens; the opt-in `pill` prop is gone (*a shape prop with a clear winner is an unfinished migration*). Primitives extracted the same day: **`StockLevelPicker`**, **`NumberStepper`**; and in the settings batch, **`LocationAddChip`** + `css/settingsCards.scss`. **FU-848** (merging `BaseSegmented` and `DoraSegmented`) stays its own unit — 19 consumers pass Quasar props that would go inert | `BaseSegmented.vue` · `StockLevelPicker.vue` |
| **Zero-Input Pantry / inference (P8-07)** | 🟡 | Built and extended to recipes, shopping lists and the planner, each behind its own off-by-default opt-in — now named *"<area> hints"* on the settings page. New 09-03: **planned demand** as a sibling signal (R-074/ADR-071), not a term in `compute_belief` — a raw-SQL duplicate of the batch-pool model deleted on the way. Open: FU-851, FU-849 | [PROPOSAL](docs/04_proposals/PROPOSAL_ZERO_INPUT_PANTRY.md) |
| **Stocktake Mode** | ✅ | Three-phase runner, queue least-certain-first, install-wide switch. Recorded for good: **"confidently Out" is unreachable by construction**. Verify owed; FU-700, FU-728 open | [PROPOSAL](docs/04_proposals/PROPOSAL_STOCKTAKE_MODE.md) |
| **Products-as-overlay** | ➗ | Phases 0–E code-complete, backend green throughout; **browser-verify never done on any of it**. Phase-F tail is FU-214 + L197 hard-delete decision + L205/206 bulk-select + the FU-210 tail pass. Single Alembic head after Phase 0: `c4e6a8b1d3f5` | [RUNBOOK](docs/04_proposals/PRODUCTS_OVERLAY_RUNBOOK.md) |
| **Prices surface** | 🔴 | All price *reading* capability sits on the product axis at `/price-history`, which has no nav entry, while the everyday user gets a single-item modal. Reports chunk 4 built the "trend in Reports" half, so the keep/cut call (**FU-703**) is better-informed but still open, and still gates FU-708 | [ASSESSMENT](docs/05_investigations/PRICES_SURFACE_UX_ASSESSMENT.md) |
| **Meal reconcile** | ➗ | Chunks 1–5 shipped; **Chunk 6 (settings row/copy) is the last unbuilt Phase-1 item** | [IMPL_PLAN](docs/04_proposals/IMPL_PLAN_MEAL_RECONCILE.md) |
| **Meal planner** | ➗ | Built; open defects from the 09-03 sweep — FU-852, FU-803, FU-802, FU-804 | [PROPOSAL](docs/04_proposals/PROPOSAL_MEAL_PLANS.md) |
| **Shopping lists (v4)** | ✅ | Built end to end — all three faces on one row skeleton after chunk 5 moved the shared visual language out of the page's *scoped* block. Open: FU-808, FU-805 | [SHOPPING_LIST_UX_V2](docs/04_proposals/SHOPPING_LIST_UX_V2.md) |
| **Alerts control centre** | ✅ | Nine kinds cut to six, severity the only importance scale, email digest deleted whole. Open: FU-701, FU-702, FU-854, and DR-12's Alerts half | [PROPOSAL](docs/04_proposals/PROPOSAL_ALERTS.md) |
| **Assistant / Voice / Offline** | ➗ | Voice download was **broken for every voice, always** (`NameError` from `_download_voice`'s rename block drifting into `_record_progress`) — fixed 09-03 with the first two tests ever to touch `voice_provision`. Settings → Voice copy trimmed and the PWA-install message stopped blaming the browser (R-077). Still never verified on Firefox (FU-751, FU-788, FU-787). Offline's CSRF replay bug is fixed (R-047/ADR-043) but the **live round-trip verify is still owed** (FU-724) | `useOfflineQueue.ts` |
| **Design remediation (DR)** | 🟡 | DR-1..11/14/15 done or done-with-carve-outs; **DR-13 and DR-16 (owner call) remain**; DR-12 half-settled. Adjacent: the undeclared-token class R-060 names but nothing enforces | [DESIGN_REMEDIATION_PLAN](docs/04_proposals/DESIGN_REMEDIATION_PLAN.md) |
| **Build & deploy** | 🔴 | The 08-23 backups/import 404 was **the deploy script, not the app**: `--exclude='data'` matches the basename at any depth, so every deploy `--delete`d `dora_api/features/data/`. One-character fix, still owner-side. FU-720, FU-719, FU-721, FU-790 | FU-719/720 |
| **Verify tooling** | 🟡 | A proven-safe isolated pairing is committed (`dora-verify-backend-5171[-linux]` + `dora-spa-5171`, scratch DB). Remaining limits: `QMenu` never opens, `screenshot` times out, some routes won't mount (**stock-item detail**, the cookbook list). The four original `:5170` + `DORA_ALLOW_DESTRUCTIVE=true` configs remain the footgun (**FU-758**) | FU-758 |
| **Postgres datastore** | ✅ | Implemented + default (SQLite fallback); migrations kept portable. CI wiring blocked on FU-405 | `configuration_manager.py` |
| **Test suite** | ✅ | Green 2026-09-03: backend **2275 passed** / 1 skipped / 1 xfailed, frontend **685 vitest / 61 files**, `vue-tsc` + `eslint src/` clean. Caveat: 4 pre-existing buy-verdict e2e reds (FU-762). This machine: bare `pytest` throws spurious setup errors from a missing system temp dir — pass `--basetemp`; the venv is `.venv/Scripts/python.exe`, not PATH python. Open: FU-756/743, FU-781, FU-778, FU-520 | [PROPOSAL](docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md) |
| **Open-source release (P7)** | ⚪ | Not sold — donation/OSS/all-free. README/showcase, release process, support channel (FU-406/557/608), build number (FU-861) | [PLAN §5](docs/01_charter/RECONCILED_FINISHING_PLAN.md) |
| **Finalisation sweep** | 🔵 | Designed, not started — 20 chunks, two-stage, single-maintainer north-star | [PLAN](docs/01_charter/FINALISATION_PLAN.md) |

---

## ⚠️ Needs your attention now

**Total open backlog is ~198 items in `DORA_FOLLOWUPS.md`** — recount before
quoting it; don't do arithmetic on this number, the last three recorded figures
were all wrong for exactly that reason. Latest movement: **FU-852..861 opened**
across the four 09-03 batches.

These are the ones wanting a decision or a running-app check, most important first.

1. **🔴 FU-860 wants a decision before anything is built.** With products off,
   Dora sends **no scheduled email at all** — the weekly deals mail is the only
   one, and its section is already hidden. Your own follow-on ("perhaps there's
   something we could email that users would want") is the real question; the
   evening brief is the cheapest candidate, since it already exists and is
   already scheduled — only the channel is missing.
2. **Walk the 09-03 Settings batch — all of it is device- or install-shaped and
   none of it can be agent-driven.** A real Piper voice download (the `NameError`
   fix, now test-covered but never watched end to end), the Docker-over-HTTP
   install message on a phone, a real file picker on Stores, and the
   Notifications email rows on an install that actually has SMTP.
3. **Walk the earlier 09-03 batches — three `DORA_VERIFY` sections, one never
   *seen*.** The two new themes, the segmented convergence across 19 consumers,
   and the **planned-demand card**, verified as data but whose stock-detail route
   won't mount in the agent's pane.
4. **🔴 FU-855 is your call, and FU-856 is the lever that fixes it.** Setting
   `pack_count = 12` on the eggs made the omelette right, but "2 tins" of a 400 g
   tin with no `pack_count` is now honestly *unpriced* where it used to be right
   by luck — and `pack_count` isn't on `CreateProductRequest`, so there is
   currently **no way to record the fact through the API at all**.
5. **🔴 May a planned meal change a buy verdict? (FU-774)** Your own idea, and the
   brief agrees — but your 2026-08-17 directive says "a planned meal's shortfall
   is unchanged", and an axis that moves `unsure` → `buy` breaks it head-on.
   Gates FU-775/776. 09-03 shipped planned demand as a *sibling* signal precisely
   because it must not change an answer (R-074); that precedent is on the table.
6. **🔴 Four launch configs will still destroy the dev DB (FU-758).** The
   `dora-verify-backend*` entries bind **:5170** with
   `DORA_ALLOW_DESTRUCTIVE=true`, which `drop_all`s on boot. The safe pairing is
   committed beside them. Point them at it, or delete them.
7. **🔴 Four buy-verdict e2e tests are red (FU-762).** They pre-date the
   money-gate change but sit directly on the surface it modified.
8. **🟡 One character in `deploy-dora.sh`, still on your desktop.**
   `--exclude='data'` matches the basename at any depth, so every deploy deleted
   `dora_api/features/data/`. Change to `--exclude='/data'` — until you do,
   **FU-648 and FU-710 stay unreproducible**. The script also holds your SSH
   password in plaintext at mode 0664.
9. **🟡 Four more surfaces still read "has a price" as "was bought" (FU-768).**
   The budget bug fixed on 08-28 was one instance of a class. Needs a call on what
   counts as proof of purchase, then a chokepoint in `_line_price.py`
   (R-061 / ADR-058).
10. **Does the re-brightened accent look right, and does the burger read at
    12–14px? (FU-850, FU-800.)** The rest of the sweep wants your eye on this
    pass first.
11. **🟡 A benign browser warning can silently revert an in-flight mutation
    (FU-785).** A `ResizeObserver` loop notification shows an "Oops" toast, but
    `window.onerror` also runs `executeRollbacks()` — a layout hiccup can roll
    back an optimistic write. The toast is the lesser half.
12. **🔴 Decide the fate of the product price axis (FU-703).** Reports chunk 4
    answers the everyday price question without a catalogue; the keep/cut call on
    the product surfaces is yours and **gates FU-708**.
13. **Walk the whole stock + stocktake surface — built and unseen (FU-683,
    FU-715).** On the 08-22 bulk-bar check: open devtools Network, and **if any
    bulk action still fires N requests, a call site was missed** (FU-714 names one).
14. **Existing installs need a re-import prompt or their ratings are wrong in one
    direction (FU-750),** and both schemes want a walk against a real USDA import
    — **Nutri-Score has had no browser pass at all** (FU-746, FU-643).
15. **🔴 Token and small-decision cleanups, all mechanical once called.** FU-674
    and **FU-801** (both fail the 4.5:1 ink test; the latter is consumed through
    Quasar's `color="primary"`, so it's its own unit); **FU-834/FU-764** — ~20
    undeclared custom properties that silently ignore your theme forever, no lint
    gate; FU-839, FU-709, FU-685/686.
16. **Round-trip the offline queue live (FU-724).** It once queued changes and
    lost every one while reporting "Synced everything" — a mocked transport
    cannot reproduce this.
17. **Phase-4 release readiness needs your steer on scope and timing.** FU-406,
    FU-608, FU-557 (a one-line config change lights up Help / error-report),
    FU-861 (a real build number). Ops/CI (FU-405) gates FU-520/FU-404/FU-721.

---

## Where the detail lives

- **`DORA_WORKLOG.md`** — per-session handoff narrative (what ran, decisions, what's next).
- **`CHANGELOG.md`** — product/code changes that shipped.
- **`DORA_FOLLOWUPS.md`** — the full 188-item open backlog (this dashboard shows only the top).
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

21. **✅ Security thread closed.** `AUTH_ASSISTANT_SECURITY_FINDINGS` is now a triaged standing register — the HIGH CSRF + MEDIUM email-change were fixed under FU-197 (2026-06-30); the 8 residual Medium/Low findings went to FU-515 (resolved); the orphan audit-follow-up FU-447 was reconciled + closed. A.5/A.6/A.7 are accepted risks (A.6 → Phase-4). Nothing open.
22. **🕸 Stale "no code yet" / "designed-not-built" headers on ~15 shipped docs (FU-445).** Bodies are accurate records; only the top status line lies (e.g. IMPL_PLAN_ALERTS, IMPL_PLAN_MEAL_RECONCILE). Judge by this register, not the header.
23. **🕸 `docs/00_DOC_GRAPH.md` is a retired stub (FU-428).** Superseded by this doc + the CLAUDE.md anti-drift rule.
24. **Backlog right-sized.** The old dashboard cited "~60 open items"; the ledger actually holds **17**. Most of the prior attention list had long since moved to `_RESOLVED`.

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
| DESIGN_REMEDIATION_PLAN | Design backlog | 🟡 active | Action the 2026-07-18 UX/design audit (DR-1…16) | DR-1/1b/2/3/4/5/6/8/10/11 done (10=owner leave-as-is), DR-7 ➗ (FU-624), DR-9 ➗ (FU-631), DR-14 ➗ (FU-632), DR-15 ➗ (FU-694); remaining: DR-13/16 + the **Alerts half** of DR-12 (its meal-plans mini-month was overruled by D7 and built as a month grid 2026-08-30) |
| DORA_ASSISTANT_ARCHITECTURE_PROPOSAL | Proposal | ➗ carve-outs | Unify assistant capability model + LLM config | §2.2 registry deliberately not built; §7 multi-provider shipped |
| IMPL_PLAN_ALERTS | Impl plan | ✅ done | Alerts control-centre (C-9) | Digest+push+prefs shipped; header stale |
| IMPL_PLAN_AUTH_SHELL | Impl plan | ✅ done | Extract shared AuthShell + AuthButton (C-19) | `AuthShell.vue`/`AuthButton.vue` exist |
| IMPL_PLAN_CART_BUTTON | Impl plan | ✅ done | Unify add-to-list into one cart control (C-7) | `AddToListButton` in use |
| IMPL_PLAN_CONFIG_AND_OPTINS | Impl plan | ✅ done | Feature-flag/opt-in spine (C-cross) | `useFeatureFlags`/health flags shipped |
| IMPL_PLAN_COOKBOOK | Impl plan | ✅ done | Recipe domain rebuild (C-4) | Structured steps/tags shipped |
| IMPL_PLAN_COOK_MODE | Impl plan | ✅ done | Cook-mode rebuild (C-3) | `RecipeCookMode.vue` live |
| IMPL_PLAN_DASHBOARD_REBUILD | Rebuild brief | ✅ done | Rebuild DashboardPage around savings | Phases 0-7 shipped; the **two commitments the 2026-09-02 re-audit found unmet are now both met**: §2.2's card census is encoded at 14 registered / 11 default-on with `dashboardCards.spec.ts` holding it (FU-830), and §6's DoD "thin composition over `components/dashboard/*` — the 1964-line monolith is gone" closed for real at chunk 5 — all 14 card bodies extracted, page 3,258 → 1,888 lines (FU-829, R-072/ADR-069) |
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
| BRIEF_BUY_VERDICT_PLAN_AXIS | Design brief (2026-08-28) | 🔴 needs-a-decision | A fourth `plan` axis feeding the buy verdict from planned meals | No code; blocked on FU-774 (collides with the 2026-08-17 "shortfall is unchanged" directive). FU-775/776 downstream |
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
| PROPOSAL_SHOPPING_LIST_UX_V2 | Proposal | ➗ superseded in part | Single-page shopping experience | "BUILT 2026-06-12"; the rail + status enum survive, but its toolbar, header cluster and row anatomy are replaced by the 2026-08-23 three-face redesign (worklog) and now by v3's overview card |
| PROPOSAL_SHOPPING_LIST_UX_V3 | Proposal | ✅ done | The overview card — replaces the detail page's header block, TripCard, plan StoreSpendCard, order-by bar and shop-mode sticky footer with one collapsible card across all three faces; toolbar recomposition (Export splits, shop date arrives, New list leaves for the rail, lifecycle actions leave for the card) | Written **and built** 2026-08-29 from an 11-bullet owner batch; all 11 decisions closed in §7, three build deviations in §10. New shared `CollapsibleCard.vue` (adopted by `StoreSpendCard` + `PantryBeliefCard`), new `ShoppingListOverviewCard.vue`, `TripCard.vue` deleted, sticky footer deleted, "Order by" deduped across faces, rename became a dialog on every width. Three reported bugs fixed (page-blanking `load()` on every list-level edit, chip vanishing while renaming, footer overlap). Driven live on all three faces at 1280/375. FU-783 resolved, FU-784 narrowed, **FU-785 new** (pre-existing: a benign ResizeObserver warning fires an "Oops" toast *and* `executeRollbacks()`) |
| PROPOSAL_SHOPPING_LIST_UX_V4 | Proposal | ✅ done | The surface pass — v3's information architecture is kept intact; this changes containers, grid, type scale and control density. Direction B (two-tier surface + row diet) for plan/run, direction A (document) for the receipt face; direction C (dense table) deferred as an evolution of the same row. **Chunk 0 is a blocking behavioural baseline** (`05_investigations/SHOPPING_LIST_BASELINE.md`) — every affordance, flag combination and edge state catalogued before any markup changes, so the cutover is auditable rather than assumed | Written 2026-08-31 from a 12-bullet owner batch (W1–W12). Findings: the surface uses `--radius-md` + a flat border everywhere and **zero** elevation tokens while `--radius-lg/xl/2xl`, `--elevation-card` and `--hero-gradient` sit unused; the row has **no grid** (flex + four competing `min-width`s), which is the mechanical cause of the reported misalignment; savings is **offer-only** (`_line_savings` returns 0 without an offer carrying `price_was`) while prices resolve actual→historic, so the two have different audiences; **both `money` and `products` default to `False`**, making the no-money tier the design baseline. Four open decisions; **7.1 and 7.2 closed 2026-08-31 by owner call** — quantity is a tile at rest that becomes a stepper on hover/focus, and the `--hero-gradient` band runs on plan+run but the receipt face is **flat**, which promotes the band from decoration to a state channel (gradient = still happening, flat paper = finished record). 7.3/7.4 resolve out of chunk 0. **Chunk 0 complete** — `05_investigations/SHOPPING_LIST_BASELINE.md`, 79 affordances catalogued from source (toolbar, both picker renderings, page furniture, overview card, three row variants, eight dialogs, keyboard/DnD/responsive, thirteen edge states, T0/T1/T2 matrix); destination/decision columns fill during chunks 1-3 and **chunk 4 is blocked until none read TBD**. Two findings amended the proposal: the mockups omitted six live page surfaces entirely (trim banner + preview, suggestions strip, deferred section, receipts strip, danger footer), and the "nine always-visible affordances" claim was an overstatement (reorder is already gated on manual sort; most of the rest is data-conditional). **Chunk 1 (the row) built and driven live** — new `ShoppingListPlanRow.vue`, `q-item` dropped for a CSS grid, always-on set cut to name/quantity/money, store select + three chip variants folded into one caption line, reorder arrows joined delete, name raised above the price. Alignment verified *numerically* (one distinct x per column across six rows) and the no-reflow constraint likewise (money x and row height identical across a hover). **Three defects the static suites missed and the running-app gate caught**: an import path `vue-tsc`+`eslint` both passed but the bundler rejected; a 375px overlap from keying the grip's hiding to `hover:none` while the column count keyed to `max-width`; and 483px phone rows from an auto-sized money column starved by its own caption. Baseline §5.1 filled — 16/16 kept-or-moved, **nothing cut**. **Chunk 2 (card + page furniture) built and driven live** on all three faces, in pesto-dark and at 375px. Card on `--radius-xl` + `--elevation-card`, headline off a magic `1.9rem` onto `--font-size-3xl`, `--hero-gradient` band on plan+run and **flat on the receipt** so the surface encodes state. **The §1.6 dark-theme worry dissolved**: `--surface-component` is already lighter than the page in dark and darker than white in light, so one declaration is correct both ways. **§7.3 closed** — the money-off headline is per-face (items-to-buy / left-to-pick / items-bought) instead of one flat count, which matters because money is the *default* install. **New C19** closes the §1.5 concealment: the total now carries `~` + "n items with no price yet" instead of burying it in the disclosure. Order-by is `BaseSegmented pill`, reusing the owner's 2026-08-31 shape (D-015). All ten furniture panels share one `.sl-panel`. Baseline §3+§4 filled; **still nothing CUT anywhere**. **Chunk 3 (receipt face) built and driven live** — the done list is a document: multiplier, name, dotted leader, amount, with `TOTAL` under the itemisation above a dashed rule and **no gradient band** (`bandIsGradient: false` against the other two faces' `true`). The §4.3 constraint was met by extracting the shared skeleton to **`src/css/shoppingRow.scss`** — grid shell, name/caption/money type scale, inset divider — consumed by both faces, rather than a `face` prop putting two mutually-exclusive control sets behind `v-if` in one component (R-001); this is the third application of the `dnd.scss`/`subbar.scss` precedent, so **no new ADR**. **A T0 carve-out came out of the running app**: with money off (the default install) the leader ran to the sheet edge and read as a number that failed to load — it is now suppressed when there is nothing at the end of it. The sheet's own header was removed as verbatim duplication of the overview card 40px above (E2 `moved`, not cut — count and date still on the card, total and unpriced-count in the footer). Plan face re-verified after the CSS extraction (single x per column, zero hover reflow). Baseline §5.3 filled; **still nothing CUT anywhere across chunks 1-3**. **Chunk 4 — the blocking cutover audit — PASSED 2026-09-01.** All 79 affordances carry a decision; **nothing was CUT across chunks 1-4**, so no owner sign-off is outstanding. §1/§2/§6/§5.2 were untouched by the rebuild and confirmed rendering live rather than assumed from a diff; all thirteen edge states rendered (five from seeded data, eight by rewriting the API payload in flight, stated as such). Three catches nothing else would have made: **P8 never existed** (the census recorded a picker kebab removed three days before it was written), **chunk 1 orphaned 165 lines of dead CSS** (`ShoppingListDetail.vue` 3,273 → 3,108 — neither `vue-tsc` nor `eslint` can see an unused class), and **the shop face is now the odd one out**, still `bordered` + `--radius-md` + `q-item` while the other two faces moved on. **K2 resolved**: `space`/`u` are guarded on `status !== 'shopping'` and verified inert on a draft — but advertised in the cheatsheet on every face (FU-808). **Chunk 5 closed FU-807 the same day** (owner: *"consistency matters"*), completing §4's "direction B for plan/run". Root cause was structural: `.sl-panel` / `.sl-list` / `.sl-section*` lived in the page's **scoped** block, so the run face *could not reach them* — a shared visual language in a page's scoped styles silently excludes every child component. They moved into the shared sheet (renamed `shoppingRow.scss` → `shoppingList.scss`), and a new `ShoppingListRunRow.vue` joined the plan and receipt rows on one skeleton. The row is a `role="button"` div (it contains the price button, and a button inside a button is invalid), so Enter/Space were wired explicitly and **re-verified live** — `q-item clickable` had been providing them for free. All three faces now measure the same slab radius, elevation and 18.5625px name; tick verified by click and by Enter; the price button opens the sheet without ticking. **v4 is built end to end.** Owed: `DORA_VERIFY` D8 (receipt lightbox — needs an attachment the seed doesn't ship); open FU-808, FU-805 |
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

## 05_investigations — reports (22)

| Doc | Type | State | Purpose/Notes | Evidence |
|---|---|---|---|---|
| DASHBOARD_PAGE_REVIEW | PO+eng review | ✅ all 6 chunks built | The dashboard as a **drift audit**, not a design pass — the surface was designed properly (`IMPL_PLAN_DASHBOARD_REBUILD`, 7 phases) and it is the plan's *structural* commitments that lapsed: curated 8-card default → 13 of 17; DoD "monolith is gone" → 3,258 lines. Also re-opens feedback D2 (dark mode) and L254 (money opt-in) | Written 2026-09-02; 13 FUs (817-829); all 8 §8 decisions closed. All 6 chunks shipped 2026-09-02 — both structural commitments met and the design-rule sweep done (FU-828/829/830/840 resolved). Spin-offs still open: FU-835/837/838/839/841 |
| REPORTS_PAGE_REVIEW | PO+eng review | 🟡 active/in-progress | `/reports` first-ever review — stands in for the empty REPORTS feedback section. **Chunks 1–4 of §7 built and driven live 2026-09-02**; only chunk 5 (the design sweep) remains | Written 2026-09-02; 8 FUs (809-816). §7 carries a live build-status block. FU-809/810/811/812 answered by the owner; FU-816/815/813/814/833 **resolved**; FU-843 item 2 closed, item 1 downgraded; FU-844/845/846/847 spun off; FU-703 D3’s trend half built. One item corrected by `DASHBOARD_PAGE_REVIEW` §3.10: the `themeTick` bug originated on the dashboard, so FU-824 superseded half of FU-814 |
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
