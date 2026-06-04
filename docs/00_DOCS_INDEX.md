# Dashy Dora — Documentation Index

The single entry point to this planning library. Read this first.

> **Product name:** **Dashy Dora** (formerly *Discount Dora*). The rename is performed
> in code by **P8-01**. Until that lands, **code identifiers, package names, and the repo
> still read "DiscountDora"** — so the prompt plans intentionally reference "DiscountDora"
> when pointing at current code. Treat "Discount Dora" / "DiscountDora" in any doc as the
> *current code name of Dashy Dora*, not an inconsistency to fix.

---

## The library, in reading order

| Doc | Purpose | ID namespace | Status |
|---|---|---|---|
| **RECONCILED_FINISHING_PLAN.md** | **START HERE.** Reconciles the whole library + code + the MASTER feedback into one phased finishing plan. Records the resolved strategic decisions (scraper → standalone companion via ingestion API; Foundations→loop→champion; someday-list; sell later). Supersedes the open "which direction?" questions across the library as of 2026-06-04. | — | Active — the current finishing plan |
| **STATUS.md** | Audit of what's actually built vs the Part 1–5 plans. The source of truth for current implementation state. **Note: dated 2026-05-27 — stale; the meals→recipes merge, substitutes/stock-map removal, and DS4 landed after. Re-baseline is Phase 0.** | — | Living — recheck before any work |
| **PROMPT_PLAN.md** (Part 1) | Core product: screens, stock/lists/recipes/deals, auth, PWA, design system, docs, devops, tests. | P/N/X/S/F/A/M/DS/Doc/D/T/L/I | Largely built (see STATUS) |
| **PROMPT_PLAN_PART_2.md** | Intelligence layer (reconciliation, prediction, waste, household, in-store). | P2-01 … P2-16 | Mostly NOT started |
| **PROMPT_PLAN_PART_3.md** | Anti-Grocy simplification. | P3-01 … P3-16 | NOT started (some conflicts w/ current design) |
| **PROMPT_PLAN_PART_4.md** | Dev experience & final finish. | P4-01 … P4-15 | NOT started |
| **PROMPT_PLAN_PART_5_OPTIONAL.md** | Production-readiness (security, privacy, perf, backups). | P5-01 … P5-11 | NOT started |
| **PROMPT_PLAN_PART_6_POLISH.md** | The closed loop: cook→consume, opportunistic meals, costing, self-drafting shop, briefing, confidence — plus barcode→QR cleanup. | P6-01 … P6-13 | Active (current wave) |
| **COMMERCIALIZATION_REPORT.md** | Strategic analysis of selling Dora: legal, robustness, monetization, SaaS paths. | — | Reference |
| **PROMPT_PLAN_PART_7_COMMERCIALIZATION.md** | De-risk (scraping → personal prices) + productionize + the SaaS branch (Path A multi-tenant / Path B managed instances). | P7-01 … P7-10, P7-A1/A2, P7-B1 | Active (branching) |
| **DASHY_DORA_CHAMPION_PLAN.md** | The vision + competitive findings + novel features (incl. the Zero-Input Pantry) and the Part 8 prompt plan. **Contains the Dora Decision Charter + the verify-state-first operating procedure that govern the whole library.** | P8-01 … P8-10 | Active (vision) |

Also in the tree: the repo at `DiscountDora-main/` with its own **README.md** and **CHANGELOG.md** (CHANGELOG is the authoritative running log — every prompt updates it).

---

## Dependency / reading order

```
STATUS.md (always recheck)
   │
Part 1 (built) ──► Part 6 (the loop) ──► Part 8 (champion features, incl. Zero-Input Pantry)
                         │                      ▲
                         └──► Part 7 (de-risk + SaaS) ──┘
Parts 2–5 = original backlog; Parts 6–8 refine/supersede much of it (mappings noted in each doc).
```

- **Part 6 is the foundation for Part 8.** The flagship **Zero-Input Pantry (P8-07)**
  requires P6-01 (reconciliation), P6-04 (prediction), P6-07 (cook→consume), P6-13
  (confidence). Don't build it on a missing loop.
- **Part 7's de-risk (P7-01) is a hard gate before any hosting**, and re-points P6-03/P6-09
  onto personal price history. Part 8's price features (P8-03/04/05/06) build on it.
- Part 7 inherits **P5-01/P5-02** (security headers, privacy/data rights) for compliance.

---

## Governance (applies to EVERY prompt, in every plan)

1. **Verify current state first.** Before acting on any prompt, read STATUS.md, CHANGELOG.md,
   the named code, and the prior plans; reconcile the prompt against reality; adapt or STOP if
   it has drifted or a dependency is missing. (Full procedure: DASHY_DORA_CHAMPION_PLAN.md
   Part III.)
2. **Obey the Dora Decision Charter.** Every design decision is checked against the 12
   principles in DASHY_DORA_CHAMPION_PLAN.md Part II (effortless above all, coarse-by-design,
   self-correcting, personal>generic, leverage the loop, no legal-risk scraping,
   anti-feature-creep, …). Violations are reworked or surfaced, never silently shipped.
3. **Preview → approve → commit; undoable; explainable.** No silent writes; always show why.
4. **Don't rewrite the framework** (no FastAPI/C#) — productionize the existing Flask stack.

---

## REMOVED features — do not reintroduce (canonical)

These were deliberately deleted as low-value or legally risky. Any lingering references are
**dead code to remove, not capabilities to build on**:

- **Substitute graph** (stock-item substitutes) — removed.
- **Stock map / spatial layout** — removed. **Locations is now a simple hierarchical tree**
  (settings-style), nothing spatial; use it only for grouping, never routing.
- **Product / real-world barcodes** (EAN→merchant-product, `StockItem.barcode`, deal lookup)
  — removed (P6-02). **Dora's own per-item QR labels are kept but OFF by default**
  (`qr_labels_enabled`). Note P8-02 adds a *separate* barcode-to-**add** via Open Food Facts
  (open data, add-only) — that is NOT the removed deal-barcode subsystem.
- **Central retailer scraping as a hosted service** — being removed (P7-01). Price data comes
  only from the user / personal history / loyalty-email / opt-in crowd / open data. Scraping
  may survive only as a self-hosted, off-by-default module.

---

## ID namespace legend

- Part 1: mixed prefixes (P#=screens, N=greenfield pages, X=heavy features, S=shortcuts/search,
  F=foundations, A=auth, M=mobile/PWA, DS=design system, Doc=docs, D=devops, T=tests, L=i18n,
  I=audit).
- Parts 2–5: `P2-`, `P3-`, `P4-`, `P5-`.
- Parts 6–8: `P6-`, `P7-` (+ `P7-A*` Path A multi-tenant, `P7-B*` Path B managed instances),
  `P8-`. No cross-part ID collisions — each part owns its prefix.
