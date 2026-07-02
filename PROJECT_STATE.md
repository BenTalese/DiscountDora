# Dashy Dora — Project State

**Regenerated: 2026-07-02** (workstream states **verified against the codebase**,
not just the docs). This is the single front door: where every phase and workstream
is up to, and what needs your attention. For *where things stand* this doc wins; for
*how/why* a decision was made, follow the linked planning doc. It is regenerated
after each chunk of work — if it looks out of date, the last session skipped its
close-gate (trust `DORA_WORKLOG.md` + `CHANGELOG.md` and regenerate).

Status key: ✅ done · ➗ done, with skipped/deferred items · 🟡 in progress ·
🔵 designed, not built · ⚪ not started · 🔴 needs your decision · 🕸 stale doc.

---

## Where we are right now

Phases 0–2 are effectively **done**: foundations, the full shop→cook→restock loop,
and the ingestion API + standalone companion all landed (the June baseline that
called Phase 2 "0%" is stale — it's backend-green now). You are in **Phase 3, the
champion features** (~25%): the "Should I buy this?" buy-verdict oracle (P8-05) and
barcode-to-add via Open Food Facts (P8-02) just shipped. The most recent work was
the onboarding starter-data rework (per-name checklists + paste-rows). **Next up:**
browser-verify the new onboarding flow, then continue the champion sequence toward
the flagship **Zero-Input Pantry (P8-07)** — but a governance call on crowd-sourced
prices (**FU-436**) is pending and blocks two of the champion features.

---

## Phase board

| Phase | Scope | Status | Remaining |
|---|---|---|---|
| **0 — Foundations** | Theme/buttons/modals/filters/text-size/renames + bug clusters + config/opt-ins | ✅ ~98% | Residual polish clusters (FU-359/360/361/362/363/430/431/432). |
| **1 — Close the loop** | Shopping lists, cook mode, stock overview, cookbook, suggestions, costing, stocktake | ✅ ~95% | P6-10 self-drafting plumbing done but unwired (FU-351); P6-12 daily briefing unbuilt (FU-352). |
| **2 — Ingestion API + companion** | `/api/ingest` seam; extract scraper to standalone companion; Merchant→Store rename | ✅ done (backend-green) | Browser-verify pending (FU-214 + Phase-0/F verify FUs). |
| **3 — Champion** | Zero-Input Pantry (flagship), buy/wait oracles, barcode-add, Dora Score, culinary memory, native app | 🟡 ~25% | Flagship P8-07 not started; P8-06 wait-until (FU-438), P8-08/09/10 not started. P8-02 + P8-05 shipped. |
| **4 — Commercialize** | Tenancy, Stripe/billing, compliance, launch readiness (Postgres already done) | ⚪ ~0% | Not started (FU-387..406); zero billing/tenancy code. **Postgres is done + the default datastore** (FU-045 closed). Distribution-posture checklist gates daily work. |

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
| Stock Overview | ✅ | 32/41 bullets; 3-band StockLevel; buy-verdict badge wired | `PROPOSAL_STOCK_OVERVIEW` |
| Buy-verdict oracle (P8-05) | ➗ | Row + shopping-line badges shipped; full `BuyVerdictCard` built but **not wired** to item-detail (FU-437); wait-until deferred (FU-438) | [PROPOSAL](docs/04_proposals/PROPOSAL_BUY_VERDICT_ORACLE.md) |
| Barcode-to-add (P8-02) | ✅ | OFF lookup for unknown EANs, gated by `scanning_enabled` | [PROPOSAL](docs/04_proposals/PROPOSAL_BARCODE_SCANNING.md) |
| Onboarding | 🟡 | Per-name picks + paste-rows just shipped; **verify pending**; preferred-stores step not built (FU-383) | [PROPOSAL](docs/04_proposals/PROPOSAL_ONBOARDING.md) |
| Meal Plans | ➗ | **Built end-to-end** (3 pages, 13 components, board/calendar/templates/shortfall + backend). Waiting on **your screen-style pick + feedback**, not construction | [PROPOSAL](docs/04_proposals/PROPOSAL_MEAL_PLANS.md) + `IMPL_PLAN_MEAL_PLANS_REBUILD.md` |
| Alerts control centre | ✅ | **Fully built**: `/alerts` hub, `ALERT_ROUTER` API, price-watch + email-digest + push delivery | [PROPOSAL](docs/04_proposals/PROPOSAL_ALERTS.md) |
| Data/Backup admin | ✅ | Collapsed under Settings→Admin→Data; backup library + admin-gating (code committed) | FU-341/342/198 |
| Auth shell | ➗ | Shared `AuthShell.vue` + `AuthButton.vue` across 8 pre-auth surfaces (no standalone register page) | `PROPOSAL_AUTH_SHELL.md` |
| Postgres datastore | ✅ | Implemented + **default** (SQLite fallback via `DORA_DB_PATH`); FU-045 closed | `configuration_manager.py` |
| Commercialization (P7) | ⚪ | Tenancy/Stripe/billing not started; zero such code yet | [PLAN §5](docs/01_charter/RECONCILED_FINISHING_PLAN.md) |

---

## ⚠️ Needs your attention now

Full backlog is 155 open items in `DORA_FOLLOWUPS.md`; these are the ones that want
a decision or a running-app check *now*, most important first.

0. **🔴 SECURITY — unfixed HIGH + MEDIUM findings.** `docs/05_investigations/AUTH_ASSISTANT_SECURITY_FINDINGS.md` records a **HIGH CSRF** flaw and a **MEDIUM email-change** flaw with no fix logged. Surfaced by the 2026-07-02 doc audit — decide whether to fix now before more champion work.
1. **🔴 FU-436 — Crowd-prices: KEEP / SHRINK / CUT?** Ledger recommends CUT. **Blocks** champion features P8-04 and P8-06 — needs your call before the next champion work.
2. **🔴 Meal Plans — pick the screen style + give feedback.** The feature is **built** (board/calendar/templates all shipped); it's waiting on *your* UX-direction call, not on engineering. This is the blocker you flagged.
3. **🔴 FU-346 — Admin settings "feel hidden."** You raised this. Short direction call needed (stay put / header icon / `/admin` route) before any code moves.
4. **🔴 FU-353 — Rename GitHub repo + local checkout to DashyDora.** Your action (`gh repo rename` + `mv`); until then release-check URLs + README badges 404.
5. **FU-195 — verify onboarding** (`DORA_VERIFY.md §Onboarding`). Walk the just-shipped per-name picks + paste-rows happy path.
6. **FU-085 — Cookbook tag-taxonomy never run in a real env.** Verify the migration on SQLite + Postgres before building on it.
7. **🕸 FU-178 — Fresh-SQLite boot is broken.** Migration chain dies at `d7c9e4a8c2b1`; tests bypass it via `drop_all+create_all`, so this hides until a real fresh boot.
8. **FU-434 — Pre-existing `AdminDataImport.vue` tsc errors.** Two `exactOptional` errors pollute the close-gate every session; two-line fix.
9. **FU-444 — `test_buy_verdict.py::test__all_axes_thin` fails (pre-existing).** One deselected test each run; needs a call on trigger vs. fixture.
10. **FU-442 — Login password-policy feedback has no design home.** Real gap (min-8 + admin toggle).
11. **FU-214 — Products-overlay Phase F verify + bulk-select/hard-delete.** Last real gate on that effort; needs the running app.
12. **FU-437 — Wire the full `BuyVerdictCard` into stock-item detail.** Built but dead-coded; pair with P8-05 verify.
13. **FU-429 — Assistant-architecture proposal collides with in-flight SLM work.** `DORA_ASSISTANT_ARCHITECTURE_PROPOSAL` proposes a capability registry that the SLM pivot may supersede; needs a reconcile-or-close decision.
14. **FU-025 follow-on — component labels ignore the text-scale tokens.** Button/input/toggle labels don't track the A6 scale; small global sweep.

---

## Recently shipped (newest first)

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
- **`DORA_FOLLOWUPS.md`** — the full 155-item open backlog (this dashboard shows only the top).
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

## 04_proposals — designs, impl-plans, runbook (48)

| Doc | State | Notes |
|---|---|---|
| PROPOSAL_STOCK_OVERVIEW / _MEAL_PLANS / _COOK_MODE / _COOKBOOK / _CART_BUTTON / _ALERTS / _INGESTION_API / _CONFIG_AND_OPTINS | ✅ done | Big-rock C-1/2/3/4/7/9/10/cross designs — all built via IMPL_PLANs |
| PROPOSAL_STOCK_OVERVIEW / _AUTH_SHELL / _BUY_VERDICT_ORACLE | ✅ done | Auth-shell + buy-verdict shipped 2026-07-02 (⚠️ stale headers, FU-445) |
| PROPOSAL_STOCK_ITEM_DETAIL / _ONBOARDING / _BARCODE_SCANNING / DORA_ASSISTANT_ARCHITECTURE | ➗ carve-outs | Mostly shipped; named deferrals |
| PROPOSAL_COOKBOOK_CARD_REVISION / _RECIPE_IMAGE_STEPS / _WASTE_MINIMISATION / _SHOPPING_LIST_UX_V2 | ✅ done | Shipped; were orphaned from indexes |
| STATE_OWNERSHIP_REFACTOR_PROPOSAL | ✅ done | R-003 authority; IMPL executed |
| PROPOSAL_PRODUCTS_AS_OVERLAY / IMPL_PLAN_PRODUCTS_AS_OVERLAY / PRODUCTS_OVERLAY_RUNBOOK | 🟡 active | Phase F in progress; RUNBOOK is the ⭐ live driver |
| PROPOSAL_HELP_OVERLAY / _LOCALE_I18N / _SUPPORT_CHANNEL / _TEST_SUITE_IMPROVEMENTS | 🔵 designed | Real pending design debt (FU-043/044 etc.) |
| PROPOSAL_SIMPLE_MODE | 📦 superseded | → products-as-overlay |
| SHOPPING_LIST_REDESIGN_PROPOSAL | 📦 superseded | v1 shipped (P6-01) → UX_V2 presentation |
| IMPL_PLAN_* (Alerts, Cart, Cookbook, Cook-Mode, Dashboard, Error-Handling, Ingestion, Meal-Plans, Meal-Plans-Rebuild, State-Ownership, Stock-Item-Detail, Stock-Overview, Waste, Your-Prices, Settings-Rebuild, Shopping-Lists, Shopping-List-Receipts, Config, Auth-Shell) | ✅ done | All executed & shipped. ~13 carry stale "no code yet" headers (FU-445). MEAL_PLANS_REBUILD is the live meal-plans authority. |

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

## 99_scratch — raw notes (6)

| Doc | State | Recommendation |
|---|---|---|
| PROGRESS_REPORT_2026-06-12 / FEEDBACK_AUDIT_2026-06-12 | 🗄 historical | Delete — superseded by this doc (kept briefly for FU cross-refs) |
| PRICING_SYSTEM_REASSESSMENT_HANDOFF / WASTE_PAGE_ASSESSMENT_2026-06-24 | 📦 superseded | Executed into their IMPL plans; archive/delete |
| SENIOR_REVIEW_2026-06-16 | 🗄 historical | Keep — still cited by open FUs |
| MINIMAL_USER_PRODUCTS_OFF_FRICTION | 🗒 untriaged | Only genuinely untriaged note — promote or keep |

## docs/00_original_spec — historical bucket (157 files)

The author's first spec (Feature Boards + ~125 "I can …" notes + original plan).
Charter-designated **historical / non-authoritative** — pre-dates the current
codebase; overridden by charter/plan/feedback. Mined opportunistically when writing
a brief. Treat the whole folder as 🗄 historical; not verified per-file.
