# Dashy Dora — Implementation Prompt Pack

> **⚠️ STATUS COLUMN IS STALE (verified 2026-07-02).** The 🟢/🟡/🔵 legend below
> reflects *readiness at pack-authoring time*, not what's been run. In reality all
> Wave-A + Wave-B prompts shipped and every Wave-C brief produced its proposal
> (most now built via `IMPL_PLAN_*`). Read this as a historical execution map. For
> live per-doc state + where-we-are, see `PROJECT_STATE.md` (front door + register).

Generated from `Feedback / Fixes (MASTER).md` via `FEEDBACK_TRIAGE_AND_PLAN.md`.

## How to use this pack
- Each file is a **self-contained prompt**. Open it, read the **Impact & decisions** block first (your "check before acting" rule lives there), resolve any decisions, then run it against your live repo.
- **My code copy is stale** (esp. meals→recipes merge). Every prompt tells the executing agent to **read the current code first** and adapt. Treat any specific file/line reference as a hint, not gospel.
- Run **in order within a wave**. Waves: A (foundations) → B (bugs, can overlap A) → INV (investigations) → C (big rocks, gated by their own proposals).
- **Wave ↔ Phase:** these map onto the master plan (`../RECONCILED_FINISHING_PLAN.md`) — **Wave A + B + INV = Phase 0**; **Wave C = Phases 1–3**. The master owns *order*; this pack owns *execution*.
- Foundations resolve ~40% of the page-by-page notes for free. Do them before per-page polish or you'll redo work.

## Status legend
- 🟢 **Ready to run** — bounded, low design risk.
- 🟡 **Run, but has a decision** — read the Impact block; one or two choices to make first.
- 🔵 **Design brief** — produces a proposal/plan, changes no code. For big rocks with open questions.

## Wave A — Foundations (cross-cutting, do once)
| File | What | Status |
|---|---|---|
| `A1_theme_compliance.md` | Audit + chunked fix: route hardcoded colours through tokens (fixes dark mode app-wide) | 🟢 |
| `A2_standard_button_toolbar.md` | One standard button + toolbar + "create X" placement | 🟡 |
| `A3_standard_modal.md` | One modal standard (click-out to cancel + Cancel button) | 🟢 |
| `A4_filter_system.md` | Shared filter bar + fix "empty input wipes results" bug | 🟡 |
| `A5_loading_skeleton.md` | One loading/skeleton component everywhere | 🟢 |
| `A6_text_size.md` | Fix text-size scale (75/100/150) + apply globally | 🟡 |
| `A7_sticky_footer.md` | Componentised sticky footer for page counts | 🟢 |
| `A8_renames_refresh_navstate.md` | Renames (Dashy Dora / Mark cooked / Cookbook / D.O.R.A.), remove refresh buttons, nav-state policy | 🟡 |
| `A1b_token_value_tuning.md` | Tune token *values* (too-bright greens etc.) — AFTER A1 | 🟡 |

## Wave B — Bug clusters (mostly independent)
| File | What | Status |
|---|---|---|
| `B1_extra_forbid_payloads.md` | "Extra inputs are not permitted" on product save/link/quick-add/inactive | 🟢 |
| `B3_patch_semantics.md` | "Can't save unless I change the name" — partial-update semantics | 🟡 |
| `B4_delete_cascade.md` | Delete stock item → FOREIGN KEY constraint failed | 🟡 |
| `B5_dead_nav_buttons.md` | Onboarding skip/finish/"show me X" + dashboard continue + Alerts→404 | 🟢 |
| `B7_notification_defects.md` | "I'm a notification!" placeholder + duplicate/contradictory toasts | 🟢 |
| `B8_recipe_detail_actions.md` | Dead recipe actions, permanent substitute swap, deleted substitutes-graph ref | 🟡 |
| `B9_misc_bugs.md` | Drag off-by-one, menu double-outline, settings dup in nav, etc. (~~ctrl+k palette~~ — palette retired 2026-06-12, item 4 cancelled.) | 🟢 |

> **B2** (meal-plan `recipe_id` 400) — RESOLVED by your meals→recipes merge. Just confirm it no longer reproduces.
> **B6** (allocation logic) — lives in the merged recipes/meal-plan area; folded into the Meal Plans design brief (C).

## INV — Investigations (you asked; report, then we act)
| File | What | Status |
|---|---|---|
| `INV_investigations.md` | Orphaned-field audit, stock-overview perf/"DS4", log rolling/.local, forgot-password email wiring, QR-vs-barcode, relevancy filter, **recipe-comparison worth (INV-6)**, history-tab worth (INV-7), substitute swap-into-list (INV-8), ~~command-palette worth (INV-9)~~ (palette retired 2026-06-12; INV-9 superseded), essential-flag model (INV-10) | 🔵 |

## Wave C — Big rocks (design briefs → proposals you approve)
| File | What | Status |
|---|---|---|
| `C_big_rock_design_briefs.md` | One design-brief each: stock-overview, meal-plans, cook-mode, recipes/cookbook, onboarding, alerts control centre, **C-10 ingestion-API contract** (Dora-core). **C-6 product-search + C-8 merchant/provider are COMPANION-scope**, not Dora-core (master Decision 1). Plus implementation-planning prompts for shopping-lists & state-ownership. | 🔵 |

## Deferred (do NOT design yet — you said you'll revisit)
dashboard, reports, settings, mobile view. The app is interconnected; prompts above flag where they ripple into these.

> **Waste** was on this list until 2026-06-24, when `C-waste` (in `C_big_rock_design_briefs.md`) replaced the `/waste` page with a row-level capture + cookbook filter + StockOverview sort. See `04_proposals/PROPOSAL_WASTE_MINIMISATION.md` + `IMPL_PLAN_WASTE_MINIMISATION.md`.

## The per-prompt ritual
1. Open this prompt's section in `../00_DOC_GRAPH.md` and read every cited doc (charter anchors, engineering rules, feedback bullets, related proposals/investigations, open follow-ups, cross-prompt dependencies). If the cited docs and the prompt body disagree, the cited docs usually win — confirm with the user.
2. Read **Impact & decisions** in the prompt itself.
3. Resolve any open choices with the user.
4. Run → review the diff → close-gate against `../01_charter/ENGINEERING_STANDARDS.md` → worklog + follow-up updates → next.

For 🔵 briefs, the output is a proposal doc; nothing is implemented until you approve it.
