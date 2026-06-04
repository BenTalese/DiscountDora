# DiscountDora — Implementation Status

Audit of the codebase against the five `PROMPT_PLAN` documents (Parts 1–5).
Generated 2026-05-27 by cross-referencing each spec item's "DONE WHEN"
criteria against `CHANGELOG.md` and the actual code (`web_app/`, `dora_api/`,
`merchant_api/`, `emailer/`, `tests/`).

Status legend:

- **DONE** — implemented and matches the spec's done criteria.
- **PARTIAL** — some of it exists but is incomplete or stubbed.
- **NOT STARTED** — no evidence in code.

> Confidence: high for Parts 2/3 (cleanly absent) and for built screens;
> softer on a few Part 1 "partials" that may be considered done depending on
> how strictly the spec criteria are read. Statuses below reflect a strict
> reading of "DONE WHEN".

---

## Executive summary

The app is **Part 1 complete** (the core product) and has **barely begun
Parts 2–5**. Approximate totals across ~100 spec items: **~38 DONE, ~22
PARTIAL, ~70 NOT STARTED**. Everything end-users touch is built; the gaps are
(a) a handful of Part 1 foundation/docs/devops loose ends, and (b) the entire
"intelligence" (Part 2), "simplification" (Part 3), "dev polish" (Part 4) and
"production-readiness" (Part 5) waves.

Two cross-cutting absences recur through Parts 3–5:

- **No `docs/` tree** existed before this file.
- **No frontend/E2E test coverage** beyond backend `pytest` — no Playwright,
  and `web_app` `npm test` is still a stub (`echo "No test specified"`).

---

## Part 1 — Core product (`PROMPT_PLAN.md`)

Mostly complete. Screens P0–P14, greenfield pages N1–N9 (bar Grocy import),
heavy features X1/X5, auth A1, PWA M1, audit logging, and design tokens
(DS1/DS2/DS4) are all implemented and corroborated by code + CHANGELOG.

### Partial (half-built)

| ID | Feature | What's missing |
|----|---------|----------------|
| N3 | Import (Grocy + spreadsheet) | Spreadsheet importer done; **Grocy importer absent** |
| N4 | Export & Print | CSV/PDF exports done; confirm print views are complete |
| F2 | Empty states & loading skeletons | Per-page fades exist; no shared `EmptyState` / `LoadingSkeleton` components |
| F4 | Notify / Confirm primitives | Only `useNotifyUndoable`; no centralized `useNotify` / `useConfirm`; direct `$q.notify` calls not fully consolidated |
| S4 | Breadcrumbs everywhere | `PageTitle` exists; no breadcrumb component |
| DS5 | Naming consistency pass | Event handlers renamed (no `@click="handleX"` remain); no eslint rule enforcing the convention |
| Doc3 | API docs | FastAPI auto-docs likely live; no committed static API docs |
| Doc4 | User-facing help content | Help pages exist; no markdown guide content directory |
| D1 | Docker compose finalisation | `compose.yml` / `nginx.conf` / `startup.sh` present; healthcheck/volume completeness unverified |
| D2 | Cache & data path discipline | Config modules exist; full removal of hard-coded paths unverified |
| D3 | Production vs dev config | `server_settings.py` exists; layered profiles / fail-fast unconfirmed |
| D4 | CI pipeline | `.github/workflows` runs **backend pytest only** — no frontend lint/typecheck/build, no image push |
| T1 | E2E test suite | Backend e2e only; **no Playwright** frontend specs |

### Not started

| ID | Feature | Notes |
|----|---------|-------|
| F6 | Validation library | No `web_app/src/validation/`; no shared schemas |
| DS3 | Component gallery / Storybook | No Histoire/Storybook dependency or config |
| Doc1 | Proper README | README is still a stub (no quick-start / screenshots) |
| Doc2 | CONTRIBUTING.md | Absent |
| D5 | Release automation | No release/tag-and-publish workflow |

### Done (for reference)

P0 primitives; P1–P14 screens; N1, N2, N5–N9; S1 command palette; S5 shortcuts +
cheatsheet; F1 onboarding; F3 offline + error boundary; F5 undo; A1 auth /
registration / reset; M1 PWA; X1 stocktake; X5 auto-generated lists; audit log;
DS1 tokens; DS2 icon set (mdi-v7); DS4 animation library.

---

## "Deferred (decide later)" list — corrected status

The spec's own deferred list, checked directly. **Three are actually built**
despite being listed as deferred:

| ID | Feature | Status | Note |
|----|---------|--------|------|
| X2 | Recipe comparison tool | **DONE** | `RecipesOverview` compare mode + `showComparison` dialog |
| X3 | Product comparison tool | **DONE** | `ProductSearch` compare tray + `compareOpen` dialog |
| X8 | Recipe import from URL | **DONE** | `recipeApi.importFromUrlAsync` + import dialog |
| X6 | Nutrition tracking | **PARTIAL** | Single freeform `nutrition` text field only; no structured tracking |
| X13 | Automated meal-plan generator | **PARTIAL** | A "suggest" helper + list-generation (X5) exist; no true auto-build of the plan |
| A2 | Household / multi-user sharing | NOT STARTED | Only a comment in `WelcomeWizard`; instance-level user admin exists but not household scoping/invites |
| X4 | Deals catalogue view | NOT STARTED | "On deal" flags/filters scattered; no standalone catalogue page |
| X7 | Unit conversion | NOT STARTED | Only conversational mention in Dora |
| X9 | Recipe-as-markdown storage | NOT STARTED | Recipes are structured; likely obsolete given the structured editor |
| L1 | i18n wiring | **DECISION NEEDED** | `boot/i18n.ts` is wired but **zero `$t()` usage** — dead scaffolding. Either remove (ship English-only) or extract strings |

---

## Part 2 — Intelligence layer (`PROMPT_PLAN_PART_2.md`)

**0/16 DONE.** Essentially unbuilt. No CHANGELOG references any P2 item.

| ID | Feature | Status |
|----|---------|--------|
| P2-01 | Receipt import & purchase reconciliation | NOT STARTED |
| P2-02 | Purchase memory & actual-price intelligence | NOT STARTED |
| P2-03 | Consumption forecasting / run-out prediction | NOT STARTED |
| P2-04 | Dora suggestion inbox | NOT STARTED |
| P2-05 | Budget-aware auto lists | NOT STARTED |
| P2-06 | Expiry rescue & waste prevention | NOT STARTED |
| P2-07 | Leftovers mode | NOT STARTED |
| P2-08 | Dietary preferences & meal fit | NOT STARTED |
| P2-09 | Household sharing + real-time collaboration | NOT STARTED |
| P2-10 | Store-aware route & split lists | NOT STARTED |
| P2-11 | One-handed shopping mode | NOT STARTED |
| P2-12 | Explanation center & automation controls | NOT STARTED |
| P2-13 | Voice-first Dora & hands-free cook | NOT STARTED (pre-existing per-step cook-mode voice is Part 1) |
| P2-14 | Recipe import (URL / photo / markdown) | PARTIAL — URL JSON-LD import only; no text/photo paths |
| P2-15 | Share targets, calendar export, links | NOT STARTED |
| P2-16 | Part 2 E2E tests | NOT STARTED |

---

## Part 3 — Anti-Grocy simplification (`PROMPT_PLAN_PART_3.md`)

**0/16 — not started.** Every spec-mandated artifact is absent (`docs/product/`,
`/today` route, `/api/corrections`, `/api/housekeeping`, inference service,
`assistant_mode`, ease-score script).

> Caution: several Part 3 items run **counter to the current Part 1 design** and
> would be redesigns, not additions — notably **P3-09 "Today" page** (app lands
> on the feature-dense `DashboardPage`), **P3-10 nav simplification** (nav is
> currently flat), and **P3-11 detail-page diet** (StockItemDetail is a 6-tab hub).

| ID | Feature | Status |
|----|---------|--------|
| P3-01 | Dora product constitution | NOT STARTED |
| P3-02 | Feature complexity budget audit | NOT STARTED |
| P3-03 | Interaction friction audit + tap-count tests | NOT STARTED |
| P3-04 | Fast add everywhere | NOT STARTED (Part 1 `QuickAddSheet` is stock-item bound) |
| P3-05 | One-tap corrections | NOT STARTED |
| P3-06 | Minimal stock-item model / progressive fields | NOT STARTED |
| P3-07 | Smart defaults / inference engine | NOT STARTED |
| P3-08 | Stale data cleanup / housekeeping | NOT STARTED |
| P3-09 | Today page (daily dashboard) | NOT STARTED |
| P3-10 | Navigation simplification / advanced area | NOT STARTED |
| P3-11 | Detail page diet | NOT STARTED (current design is opposite) |
| P3-12 | Forms → sheets → inline actions | NOT STARTED |
| P3-13 | Automation noise throttle | NOT STARTED |
| P3-14 | Assistant autopilot levels | NOT STARTED |
| P3-15 | Grocy migration → Dora simplification | NOT STARTED |
| P3-16 | Dora ease score / release gate | NOT STARTED |

---

## Part 4 — Dev experience & final finish (`PROMPT_PLAN_PART_4.md`)

**0 DONE, 4 PARTIAL.** No `docs/` tree existed; zero P4 CHANGELOG entries. The
"partials" are pre-existing infrastructure from Parts 1–3, none with the
P4-required doc artifact.

| ID | Feature | Status | Note |
|----|---------|--------|------|
| P4-01 | Architecture map & codebase tour | NOT STARTED | No `docs/dev/ARCHITECTURE.md` |
| P4-02 | Domain glossary & naming cleanup | NOT STARTED | No glossary artifact |
| P4-03 | Frontend boundary cleanup | NOT STARTED | No patterns doc / refactor entry |
| P4-04 | Backend service layer cleanup | PARTIAL | Backend already feature-sliced (`dora_api/features/*`); no doc |
| P4-05 | Dead code / duplication / dependency audit | NOT STARTED | No cleanup backlog |
| P4-06 | Developer diagnostics panel | NOT STARTED | No diagnostics component / shortcut |
| P4-07 | Structured errors & friendly failures | PARTIAL | `request_id` + RFC7807 `ProblemDetails` exist, but spec wants stable `error.code` |
| P4-08 | Design system completion pass | PARTIAL | Tokens exist (DS1–DS4); no `UI_SYSTEM.md` |
| P4-09 | UI copy & microcopy polish | NOT STARTED | No voice/copy doc |
| P4-10 | Accessibility & keyboard polish | PARTIAL | Some aria/role/reduced-motion present; no axe/Playwright a11y checks |
| P4-11 | Visual QA sweep with screenshots | NOT STARTED | No QA report / script |
| P4-12 | Professional UI polish pass | NOT STARTED | Depends on P4-11 |
| P4-13 | One-command local development | NOT STARTED | compose/.env/seed exist but no Makefile / `dev:all` / documented workflow |
| P4-14 | Quality gate command | NOT STARTED | `npm test` is a stub; no quality-gate script |
| P4-15 | Release candidate checklist | NOT STARTED | No checklist artifact |

---

## Part 5 — Optional production-readiness (`PROMPT_PLAN_PART_5_OPTIONAL.md`)

**0 DONE, 4 PARTIAL.** No `docs/` artifacts; zero P5 CHANGELOG entries.

| ID | Feature | Status | Note |
|----|---------|--------|------|
| P5-01 | Security & privacy hardening | PARTIAL | Auth hardening + rate limits (A1) exist; **no security headers, no `SECURITY.md`, no dependency scanning** |
| P5-02 | Privacy controls & user data rights | NOT STARTED | No `/api/privacy/*`, no `DELETE /api/account`, no clear-history |
| P5-03 | Performance & scale pass | NOT STARTED | No perf baseline / bundle budgets |
| P5-04 | Mobile / PWA field test | PARTIAL | PWA infra (M1) shipped; no mobile smoke tests / field-test report |
| P5-05 | Dora AI reliability & evaluation suite | NOT STARTED | No eval fixtures / tool-call contract tests |
| P5-06 | Onboarding & first-week experience | PARTIAL | First-run wizard (F1) exists; no first-week nudges / demo seed |
| P5-07 | Demo / sellable showcase mode | NOT STARTED | No demo seed / reset / script |
| P5-08 | Data model sanity review | NOT STARTED | No data-model review / ERD |
| P5-09 | Backup, restore & recovery drills | PARTIAL | Backup/restore engine built (N2); no recovery-drill tests |
| P5-10 | Merchant data quality & support bundle | NOT STARTED | No merchant-status / support-bundle endpoints |
| P5-11 | Optional production readiness review | NOT STARTED | Depends on the above |

---

## Suggested priorities (not prescriptive)

1. **Decide L1 (i18n):** remove the dead `boot/i18n.ts` scaffolding or commit to
   string extraction. Cheapest win.
2. **Close Part 1 loose ends** that affect shipping: `Doc1` README, `D4` CI
   (add frontend lint/typecheck/build), `P4-14`/`npm test` quality gate.
3. **Prune the deferred list:** mark X2/X3/X8 as done; explicitly drop X9.
4. Treat **Parts 2/3** as genuine new product scope (and note Part 3's conflicts
   with the current Part 1 design before committing).
5. **Parts 4/5** are best done as a `docs/` + tooling pass once feature scope is
   frozen.
