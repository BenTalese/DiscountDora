# Dashy Dora — Documentation Index

The single entry point to this planning library. Read this first.

> **Per-prompt required reading lives in `00_DOC_GRAPH.md`.** Before executing
> any prompt in `03_prompts/`, open its section there for the cross-reference
> map (charter anchors, engineering rules, feedback bullets, related
> proposals/investigations, open follow-ups, removed-features watchlist,
> cross-prompt dependencies). The graph is the anti-drift spine of this
> library.

> **Product name:** **Dashy Dora** (formerly *Discount Dora*). The rename is
> performed in code by **P8-01**. Until that lands, **code identifiers,
> package names, and the repo still read "DiscountDora"** — so the prompt
> plans intentionally reference "DiscountDora" when pointing at current code.
> Treat "Discount Dora" / "DiscountDora" in any doc as the *current code name
> of Dashy Dora*, not an inconsistency to fix.

---

## Folder layout

```
docs/
├── 00_DOCS_INDEX.md            this file
├── 00_DOC_GRAPH.md             per-prompt required-reading cross-reference
├── 00_original_spec/           the project's FIRST spec (historical, non-authoritative)
├── 01_charter/                 vision + governance — read on demand
├── 02_feedback/                INPUTS — source of truth
├── 03_prompts/                 EXECUTABLE prompts (Wave A/B/C + INV)
├── 04_proposals/               OUTPUTS of Wave-C briefs (no-code design)
├── 05_investigations/          OUTPUTS of INV prompts + ad-hoc audits
├── 06_legacy_prompt_plans/     historical PROMPT_PLAN_PART_*
└── 99_scratch/                 raw notes awaiting triage
```

Lifecycle: **charter → feedback → prompt → proposal/investigation →
implementation.** Inputs and outputs are deliberately separated.

---

## 00_original_spec — the project's first spec (historical)

The author's **very first spec notes**, written *before* this branch's ~100k
lines of code existed. Feature Boards + ~125 "I can …" Feature Notes + the
original `PROMPT_PLAN.md`, taskboard, roadmap and navigation sketch.

**Status: historical reference, NOT authoritative.** It pre-dates almost every
decision recorded in `01_charter/` and `02_feedback/`, so where it disagrees with
the charter, the reconciled plan, or the current feedback, **those win** — the old
spec never overrides. Treat it as a *source of ideas and a memory aid*: it can
surface intent that the code half-implemented, requirements that were dropped by
accident rather than on purpose, or a cleaner original framing worth reviving.
Always weigh how old it is, and confirm against live code + the charter before
acting on anything found here.

**How to use it:** when writing a Wave-C brief or an investigation for a surface,
skim the matching Feature Board / Notes for that surface and *extract* anything
worth keeping into the brief — explicitly tagged as sourced from the original
spec, with a keep / consider / superseded call. (Worked example: the cart-button
extractions in `04_proposals/PROPOSAL_CART_BUTTON.md §9`.)

> Note: `00_original_spec/Distribution Spec …` is the original of the same-named
> legacy copy under `05_investigations/`.

## 01_charter — vision & governance

| Doc | Purpose |
|---|---|
| `01_charter/RECONCILED_FINISHING_PLAN.md` | **START HERE.** The current phased finishing plan. Records resolved strategic decisions (scraper → companion via ingestion API; Foundations → loop → champion). |
| `01_charter/DASHY_DORA_CHAMPION_PLAN.md` | Vision + the **Dora Decision Charter** (Part II) + the verify-state-first operating procedure (Part III) that govern every prompt. |
| `01_charter/ENGINEERING_STANDARDS.md` | The **code/architecture rubric** — standing rules `R-001..` (componentisation, theming, single-source-of-truth, scope, code-style, …) + ADR log. Checked on **every** task; violations must be fixed, commented, or flagged. The engineering counterpart to the Charter. |

## 02_feedback — user input (source of truth)

| Doc | Purpose |
|---|---|
| `02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md` | Archived MASTER feedback. The original raw bullets — every brief is cross-checked against it. |
| `02_feedback/FEEDBACK_TRIAGE_AND_PLAN.md` | The triage of the feedback into themes / waves / prompts. |
| `02_feedback/COVERAGE_GAPS.md` | Living list of feedback bullets that have no home in any prompt or proposal yet. Open when writing a new brief; close items as they get covered. |

## 03_prompts — executable prompts

| Doc | Purpose |
|---|---|
| `03_prompts/00_INDEX.md` | The waves + per-prompt index. |
| `03_prompts/A*.md` | **Wave A** foundations (theme, button, modal, filter, skeleton, text-size, sticky footer, renames). |
| `03_prompts/B*.md` | **Wave B** bug clusters. |
| `03_prompts/C_big_rock_design_briefs.md` | **Wave C** design briefs (each produces a proposal in `04_proposals/`). |
| `03_prompts/INV_investigations.md` | **INV** investigations (each produces a report in `05_investigations/`). |

## 04_proposals — outputs of Wave-C briefs

| Doc | Wave-C tag |
|---|---|
| `04_proposals/PROPOSAL_STOCK_OVERVIEW.md` | C-1 |
| `04_proposals/PROPOSAL_MEAL_PLANS.md` | C-2 |
| `04_proposals/PROPOSAL_COOK_MODE.md` | C-3 |
| `04_proposals/PROPOSAL_ONBOARDING.md` | C-5 |
| `04_proposals/PROPOSAL_COOKBOOK.md` | C-4 |
| `04_proposals/PROPOSAL_CART_BUTTON.md` | C-7 |
| `04_proposals/PROPOSAL_ALERTS.md` | C-9 |
| `04_proposals/PROPOSAL_INGESTION_API.md` | C-10 |
| `04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md` | Products as a data-presence overlay; Stock Item as the universal first-class entity (supersedes the spine of Simple Mode; retires the onboarding persona fork) |
| `04_proposals/IMPL_PLAN_PRODUCTS_AS_OVERLAY.md` | Execution order for the products-as-overlay pivot (Stages 0–4; FU-208..214 + 186/189/190) |
| `04_proposals/PRODUCTS_OVERLAY_RUNBOOK.md` | **⭐ MASTER RUNBOOK** — drive the whole products-as-overlay effort end-to-end from here: agreed order + live status + per-phase steps/acceptance/verify (companion → ingestion → decommission → rename → finish). |
| `04_proposals/PROPOSAL_CONFIG_AND_OPTINS.md` | C-cross (config / opt-ins / taxonomy settings) |
| `04_proposals/PROPOSAL_LOCALE_I18N.md` | C-locale (international readiness; currency/format + de-AU) |
| `04_proposals/PROPOSAL_HELP_OVERLAY.md` | C-help (opt-in contextual help overlay) |
| `04_proposals/SHOPPING_LIST_REDESIGN_PROPOSAL.md` | Shopping-list overhaul (pre-Wave-C) |
| `04_proposals/IMPL_PLAN_SHOPPING_LISTS.md` | C-impl: shopping-lists phased plan |
| `04_proposals/IMPL_PLAN_MEAL_PLANS.md` | C-2 impl: meal-plans phased plan (C-2.A…K) |
| `04_proposals/STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` | State-ownership proposal |
| `04_proposals/IMPL_PLAN_STATE_OWNERSHIP.md` | C-impl: state-ownership phased plan |
| `04_proposals/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md` | Dora assistant SLM design |

(More land here as the Wave-C briefs are run.)

## 05_investigations — outputs of INV prompts + ad-hoc audits

| Doc | Source |
|---|---|
| `05_investigations/RECIPE_COMPARISON_ASSESSMENT.md` | INV-6 |
| `05_investigations/AUTH_ASSISTANT_SECURITY_FINDINGS.md` | Ad-hoc security review |
| `05_investigations/MULTI_USER_READINESS.md` | Ad-hoc audit |
| `05_investigations/COMMERCIALIZATION_REPORT.md` | Strategic analysis (legacy) |
| `05_investigations/Distribution Spec - Desktop App & Mobile Client.md` | Strategic spec (legacy) |

## 06_legacy_prompt_plans — historical reference

The original Part-1..Part-7 plans (`PROMPT_PLAN.md`,
`PROMPT_PLAN_PART_2..7.md`). The active prompt set in `03_prompts/`
supersedes them; these stay for ID-namespace lookups and historical
context.

| Part | ID prefix | Status |
|---|---|---|
| 1 | P/N/X/S/F/A/M/DS/Doc/D/T/L/I | Largely built (see `06_legacy_prompt_plans/STATUS.md` — last audit 2026-05-27, now legacy; cross-reference `CHANGELOG.md` for current state) |
| 2 | P2-* | Mostly NOT started |
| 3 | P3-* | NOT started (some conflicts with current design) |
| 4 | P4-* | NOT started |
| 5 | P5-* | NOT started |
| 6 | P6-* | Active (current wave) |
| 7 | P7-*, P7-A*, P7-B* | Active (branching) |

## 99_scratch — raw notes awaiting triage

`claude convo.txt`, `prompt - up to speed.txt`, `Finish task DS1.txt`
and similar. Triage or delete; not loaded by any process.

---

## Governance (applies to EVERY prompt, in every plan)

1. **Verify current state first.** Before acting on any prompt, read
   `CHANGELOG.md`, the **top entry of `DORA_WORKLOG.md`**, the named code,
   and the active proposals/IMPL plans under `docs/04_proposals/`;
   reconcile the prompt against reality; adapt or STOP if it has drifted
   or a dependency is missing. (Full procedure:
   `01_charter/DASHY_DORA_CHAMPION_PLAN.md` Part III. The old
   `01_charter/STATUS.md` audit has been moved to
   `06_legacy_prompt_plans/STATUS.md` as legacy reference only.)
2. **Obey the Dora Decision Charter.** Every design decision is checked
   against the 12 principles in
   `01_charter/DASHY_DORA_CHAMPION_PLAN.md` Part II (effortless above
   all, coarse-by-design, self-correcting, personal>generic, leverage
   the loop, no legal-risk scraping, anti-feature-creep, …).
   Violations are reworked or surfaced, never silently shipped.
3. **Cross-check against the original feedback.** Every brief, proposal,
   assessment, or implementation plan ends with a flat coverage table
   mapping every relevant feedback bullet to a section in the
   proposal — see CLAUDE.md "Cross-checking against the original
   feedback — MANDATORY".
4. **Preview → approve → commit; undoable; explainable.** No silent
   writes; always show why.
5. **Don't rewrite the framework** (no FastAPI/C#) — productionize the
   existing Flask/Quasar/Vue stack.

---

## REMOVED features — do not reintroduce (canonical)

These were deliberately deleted as low-value or legally risky. Any
lingering references are **dead code to remove, not capabilities to
build on**:

- **Substitute graph** (stock-item substitutes) — removed.
- **Stock map / spatial layout** — removed. **Locations is now a simple
  hierarchical tree** (settings-style), nothing spatial; use it only
  for grouping, never routing.
- **Product / real-world barcodes** (EAN→merchant-product,
  `StockItem.barcode`, deal lookup) — removed (P6-02). **Dora's own
  per-item QR labels are kept but OFF by default**
  (`qr_labels_enabled`). Note P8-02 adds a *separate* barcode-to-**add**
  via Open Food Facts (open data, add-only) — that is NOT the removed
  deal-barcode subsystem.
- **Central retailer scraping as a hosted service** — being removed
  (P7-01). Price data comes only from the user / personal history /
  loyalty-email / opt-in crowd / open data. Scraping may survive only
  as a self-hosted, off-by-default module.

---

## ID namespace legend (legacy prompt plans)

- Part 1: mixed prefixes (P#=screens, N=greenfield pages, X=heavy
  features, S=shortcuts/search, F=foundations, A=auth, M=mobile/PWA,
  DS=design system, Doc=docs, D=devops, T=tests, L=i18n, I=audit).
- Parts 2-5: `P2-`, `P3-`, `P4-`, `P5-`.
- Parts 6-8: `P6-`, `P7-` (+ `P7-A*`, `P7-B*`), `P8-`. No cross-part ID
  collisions — each part owns its prefix.
</content>
