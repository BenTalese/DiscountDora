# Dora Follow-ups Ledger — Open

Stateful backlog of **open follow-ups, deferred jobs, leftovers, and findings**
surfaced while running prompts — the stuff that's easy for the user to miss in a
long session summary. Distinct from the other logs:

- `CHANGELOG.md` = product/code changes that shipped.
- `DORA_WORKLOG.md` = per-session handoff narrative.
- `DORA_FOLLOWUPS.md` (this file) = **open loops** that outlive a single session.
- `DORA_FOLLOWUPS_RESOLVED.md` = the archive of items that have been resolved
  (kept for the trail — never delete).

## How to use this file

- **On session start:** scan for items here. Surface the ones whose *recommended
  resolution point* is "now" or matches the work about to start, and **ask the
  user** whether they want to review/resolve them now or defer.
- **On ending a work unit:** add any new follow-ups/leftovers/findings you
  generated. If you actually resolved an item, **move its entry from this file
  to `DORA_FOLLOWUPS_RESOLVED.md`**, flip the heading from `[OPEN]` to
  `[RESOLVED]`, and add a one-line state note on how. Do not leave resolved
  items in this file, and do not delete them either — the trail matters.
- **Reported defect that "doesn't reproduce" → still log it here** as `[OPEN]`
  type `finding`, resolution "confirm in browser". A static code read is not
  proof a user-reported bug is fixed. Track each reported item individually;
  never bury several as one "all fine" note.
- Keep the newest items at the top.

## Entry template

```
## [OPEN] FU-NNN — short title
- **Raised:** YYYY-MM-DD (prompt id / task)
- **Type:** follow-up | deferred job | leftover | finding
- **What:** one or two lines.
- **Why deferred:** the reason it wasn't done in-line.
- **Recommended resolution:** now | later during <Phase/Prompt X> | when <trigger> | opportunistic
```

---

## [OPEN] FU-NNN — short title
- **Raised:** YYYY-MM-DD (prompt id / task)
- **Type:** follow-up | deferred job | leftover | finding
- **What:** one or two lines.
- **Why deferred:** the reason it wasn't done in-line.
- **Recommended resolution:** now | later during <Phase/Prompt X> | when <trigger> | opportunistic
- **State note:** (filled in when resolved — date + how)
```

---

# Open


## [OPEN] FU-553 — `downgrade base` fails on SQLite: alembic batch can't drop the RecipeIngredient named CHECK constraint
- **Raised:** 2026-07-13 (surfaced by the FU-536 round-trip test once FU-549 unblocked the from-empty chain).
- **Type:** finding (**downgrade-only — not a boot/production risk**; prod only ever upgrades).
- **What:** `flask_migrate.downgrade(revision='base')` dies in `c5a8e1f7d3b2_20260704_recipe_ingredient_unlinked.py`'s downgrade at `batch.drop_constraint('recipe_ingredient_anchor', type_='check')` with `ValueError: No such constraint: 'ck_RecipeIngredient_recipe_ingredient_anchor'`.
- **Root cause (diagnosed 2026-07-13):** a **naming-convention × batch-rebuild double-application**. Plain `Table(autoload_with=...)` reflects the CHECK correctly as `ck_RecipeIngredient_recipe_ingredient_anchor`. But when alembic batch rebuilds the table, it re-renders that already-final name through the metadata's `ck_%(table_name)s_%(constraint_name)s` convention → `ck_RecipeIngredient_ck_RecipeIngredient_recipe_ingredient_anchor` (proven: leaving the CHECK undropped, the rebuilt `CREATE TABLE` emits exactly that doubled name). So batch's `named_constraints` is keyed by the doubled name and `drop_constraint` by any single-rendered name misses. And you can't just skip the drop — the CHECK references `raw_text`, which the same downgrade drops.
- **Approaches TRIED that DON'T work (don't repeat):** (1) `drop_constraint('recipe_ingredient_anchor')` (logical name) → misses; (2) removing the drop and relying on the `drop_column('raw_text')` rebuild to omit the CHECK → the rebuild instead re-creates it with the doubled name and fails; (3) `op.batch_alter_table(..., naming_convention=NAMING_CONVENTION)` → still misses. Left the downgrade in its clean intended form (fails only under SQLite batch), with an inline NOTE.
- **Why low-priority:** production never runs `downgrade base` (fresh boot only upgrades — fixed under FU-549). Dev/rollback tooling only. **Likely SQLite-batch-specific**: Postgres drops named CHECKs natively (no table rebuild), so the round-trip probably already passes there — the cheapest "fix" is to confirm that under FU-045 Postgres CI and gate this test to Postgres.
- **Pinned by:** `tests/test_migrations.py::test__migrations__down_up_roundtrip_is_clean` (strict-xfail → flips to XPASS/un-xfail when fixed).
- **Recommended resolution:** confirm-on-Postgres + gate the round-trip test there ([[FU-045]] / FU-405 CI); OR, only if a SQLite downgrade is ever genuinely needed, rebuild `RecipeIngredient` via raw SQL in the downgrade (recreate without the CHECK) rather than fighting batch. Not worth a fragile workaround now.

## [OPEN] FU-547 — FU-537 security-test tail: auth-token single-use / expiry / cross-purpose reuse not yet pinned
- **Raised:** 2026-07-12 (FU-537 scope note — the filter-injection / mass-assignment / stored-XSS halves shipped; token lifecycle deferred).
- **Type:** deferred job (test-writing).
- **What:** `test_security_injection.py` covers query-grammar injection, mass-assignment, and stored-XSS-in-email. The **token-lifecycle** half of the FU-537 stub is not yet done: (a) a password-reset / verify token is single-use (using it twice fails the 2nd), (b) an expired token is rejected, (c) a token minted for purpose A (reset) is rejected on route B (verify) — the FU-522 cross-purpose concern as a security pin. `test_auth_flows.py` has invalid-token 400s + anti-enumeration but not these. Needs a real token round-trip (issue via the flow or mint directly through `issue_token`), so it's a bit more setup than the rest.
- **Recommended resolution:** opportunistic / next auth-surface touch — add beside `test_auth_flows.py` or the security suite.

## [OPEN] FU-545 — SettingsFileDrop: `nested-interactive` a11y violation (native file input inside a role="button" drop-zone)
- **Raised:** 2026-07-12 (found by the new FU-542 axe tests).
- **Type:** finding (real a11y defect — `serious` per axe; screen-reader/keyboard users get an interactive control nested inside another).
- **What:** `SettingsFileDrop.vue` is a `<div role="button" tabindex="0">` drop-zone that CONTAINS a native `<input type="file">`. axe flags `nested-interactive` (interactive controls must not be nested) in the enabled (non-disabled) states. The unlabelled-input half was already fixed in the FU-542 pass (`aria-hidden="true" + tabindex="-1"` on the input); the nesting remains because a native file input is inherently interactive regardless of aria-hidden.
- **Proper fix (a small refactor, but it rewrites the interaction model + existing tests → out of scope for the test-infra FU that found it):** adopt the standard accessible-file-input pattern — wrap the input in a `<label>` (label is non-interactive, so no nesting; clicking the label triggers the input natively), drop the `role="button"` / `tabindex` / `keydown` / programmatic `inputEl.click()` machinery, keep the drag-drop handlers on the label. Then the input is the single labelled interactive control. Re-enable the empty/filled axe assertions in `settingsFileDrop.spec.ts` (currently only the disabled state is checked) once done.
- **Cross-ref:** [[FU-531]] (RESOLVED 2026-07-13 — the hidden-input click re-entrancy was fixed interim with `@click.stop`; the eventual label-wrap refactor here supersedes that machinery). FU-545's remaining scope is now *purely* the `nested-interactive` a11y violation.
- **Recommended resolution:** opportunistic, next time SettingsFileDrop or the Settings import surfaces are touched.

## [OPEN] FU-520 — Test-suite improvements Phase 4: frontend Vitest + Hypothesis + Postgres CI + scraper/emailer fixture tests
- **Raised:** 2026-07-09 (split from FU-169 close-out).
- **Type:** deferred job (large — should be its own multi-session unit).
- **What:** the Phase-4 slice of [`docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md`](docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md) §5.E-F P2. Status after the 2026-07-10 targeted sweep:
  1. **Frontend Vitest + Vue Test Utils — SHIPPED incl. first component tests (2026-07-10, two passes).** 9 util/composable spec files (139 tests) + `stockLevelDot.spec.ts` (11 component tests over both StockLevelDot components) → 203 total, ~1.5s. The Quasar component-mount pattern is now established in `vitest.config.ts` + that spec: `@vitejs/plugin-vue` wired, `quasar` aliased to its client bundle (the SSR bundle throws under vitest), real Quasar components registered per-mount, per-file `// @vitest-environment jsdom` pragma. **Remaining:** `AddToListButton` (601 lines, API-coupled — needs service mocking) + shopping rail + lifecycle-coupled composables (`useMealPlanExport`, `useOfflineQueue`); all unblocked by the established pattern.
  2. **`merchant_api` scraper tests** against saved HTML fixtures — **still open**; the scraper lives in the sibling `dora-companion` repo, so this belongs there ([[FU-161]] Aldi net).
  3. **`emailer` tests — SHIPPED 2026-07-10.** `tests/test_email_templates.py` (13) + `tests/test_email_sender.py` (16): all 5 content templates + layout + autoescape, MIME assembly, SMTP wire choreography via fake transport, dry-run degradation, error propagation. Found [[FU-522]].
  4. **Hypothesis property tests — SHIPPED 2026-07-10.** `tests/test_domain_properties.py` (26): invariants over `recipe_cookability` (incl. the canonical *cookable ⇒ nothing required missing*), `stock_status`, `product_offer`, `units`. Found [[FU-524]]. `hypothesis` pinned in requirements.txt.
  5. **Postgres-backed CI test runs** once CI is un-commented ([[FU-405]] / `.github/workflows/ci.yml`) — **still open**. Note the commented workflow was fixed 2026-07-10 to run bare `pytest` (full suite) + `npm test`, so un-commenting inherits the right scope.
- **2026-07-11 update:** component-level Vitest expanded — **AddToListButton (20, the queued item), AlertRow (13, incl. the unknown-kind degrade regression), DoraModeSlider (6), SettingsFileDrop (12)**; frontend suite now 254 tests / 15 files. Pattern note for future specs: module-boundary Pinia store mocks must return `reactive({...})`, not plain objects of refs (`storeToRefs` rewraps computeds — documented in `addToListButton.spec.ts`). Remaining: scraper tests (companion repo), Postgres CI.
- **2026-07-12 update:** **Pinia store layer** now covered — `stockItemStore` (16, incl. optimistic level-swap + rollback-registry contract + FU-511 cross-store toast), `shoppingListStore` (10), `alertStore` (9, pins server-owned `actionable_count` = R-003), `locationStore` (9). Frontend suite now **298 tests / 19 files**. `authStore` (bootstrap retry / in-flight sharing / 401 clear) flagged as the strongest remaining single-store candidate; thin fetch-wrapper stores deliberately skipped. Store oddities noted (not bugs): `stockItemStore` rollback is index-captured (narrow race) and only fires via the global unhandled-rejection handler — a caller that `catch`es strands optimistic state (documented design). Remaining: scraper tests (companion repo), Postgres CI, authStore spec.
- **2026-07-13 update — parent FU-371 resolved; this FU tightened to its three real remnants (everything else shipped):**
  1. **Postgres-backed CI + coverage gate/ratchet** — blocked on CI being un-commented ([[FU-405]] P7-09 Ops; `.github/workflows/ci.yml` is deliberately fully commented). No point gating coverage while CI doesn't run. Un-blocks as a set when FU-405 lands.
  2. **`merchant_api` scraper fixture tests** — the scraper lives in the sibling `dora-companion` repo; belongs there under [[FU-161]], not this repo.
  3. **Opportunistic component/composable specs** — `authStore` (strongest remaining candidate), shopping rail, lifecycle-coupled composables (`useMealPlanExport`, `useOfflineQueue`); pattern is established, done per-touch when the surface next changes.
- **Recommended resolution (remaining):** items 1–2 are cross-repo / CI-policy-gated (not unblocked work here); item 3 is opportunistic per surface. **Recommended resolution point:** opportunistic per workstream; Postgres CI with [[FU-405]].
- **Cross-ref:** parent [[FU-371]] (RESOLVED 2026-07-13); [[FU-519]] Phase 3 (RESOLVED 2026-07-13).

## [OPEN] FU-510 — Late-game sweep: hand-rolled code that should be a battle-tested library
- **Raised:** 2026-07-07 (user request).
- **Type:** deferred job (audit-first, then refactor).
- **What:** Full-codebase pass looking for **wheels we reinvented** — hand-rolled implementations of problems a well-known, well-maintained library solves better (correctness, security, ergonomics, performance). Focus areas to check (non-exhaustive):
  - **Security-adjacent:** custom CSRF double-submit vs Flask-WTF / Flask-SeaSurf, hand-rolled Fernet key handling vs `cryptography` recipes, the hand-rolled security headers (FU-459) vs Flask-Talisman, session/cookie hardening, password hashing choices.
  - **HTTP / API surface:** pagination + query-string parsing (`queryStringBuilder.ts`, `parse_query_options`) vs Flask-Smorest / API-spec libs; response envelope + error translation vs a marshalling lib; audit-retention + audit hooks.
  - **Data access:** the generic repository (`SqlAlchemyRepository`), `EntityField`, `include`/`then_include` chains — vs plain SQLAlchemy 2.0 selectinload/joinedload patterns. Is our wrapper carrying its weight or fighting the ORM?
  - **Domain infra:** unit conversion (`units.py`), locale display denominators, currency + locale formatting, timezone / calendar-day helpers (`household_today`), fuzzy matching (RapidFuzz already used, but check the wrappers around it).
  - **Frontend:** own drag-drop composables (`useDragDropList`) vs vue-draggable / dnd-kit; own toast/notify wrappers; own shortcut registry (`useShortcut`) vs a library; own offline queue (`useOfflineQueue`) vs Workbox background sync; own rollback registry vs a proper undo/redo stack lib.
  - **Ops:** log rotation (already time-based), scheduling (APScheduler in place), rate limiting (present? if hand-rolled, flag it), config layering (`ConfigurationManager`) vs pydantic-settings.
- **Method (two phases, do not skip Phase 1):**
  1. **Phase 1 — assessment only.** Produce `docs/05_investigations/HANDROLLED_VS_LIBRARIES.md` listing each hand-rolled site: what it is, what library would replace it, honest verdict `keep` / `replace` / `wrap-thin-adapter`, and rough effort/risk. **No code touched.** Verdict has to weigh Charter tie-breaks (Effortless + Anti-creep): sometimes the hand-rolled thing is right because it's smaller, has no supply-chain risk, and stays coupled to our domain. Do NOT default to "always prefer library."
  2. **Phase 2 — action.** For each `replace` verdict, open a per-item FU (or an implementation plan when the surface is broad, e.g. auth stack replacement). Sequence by risk + blast radius; ship one at a time with browser-verify per swap.
- **Why deferred:** late-game / pre-commercialization hardening. Not urgent while the app is still gaining new surfaces; do it when the feature surface has stabilised so a lib swap doesn't collide with in-flight redesigns. Doing it earlier risks churning code that's about to be reshaped anyway.
- **Recommended resolution:** **Phase 1 (assessment) rolled into [FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md) Track 3 as a per-chunk bucket** (§3.3 "Hand-rolled-vs-library verdicts"). Each chunk's senior-review section captures the `keep` / `replace` / `wrap-thin-adapter` verdict for the hand-rolled surfaces it walks past, using the shape this FU specified. The plan's close-out consolidates them into `HANDROLLED_VS_LIBRARIES.md`. **Phase 2 (per-swap actions) stays open on this FU** — each `replace` verdict spawns its own per-swap FU at plan close, sequenced by risk + blast radius. Pair the Phase-2 sequencing with [[FU-412]] COMMERCIALIZATION_REPORT + [[FU-409]] auth security re-audit + [[FU-424]] senior-review Tier-2 delta.


## [OPEN] FU-431 — Product History: deeper redesign brief (feature discoverability + desktop drawer pattern)
- **Raised:** 2026-07-01 (12-June feedback-audit delta).
- **Type:** deferred job.
- **What:** Product History has 10 bullets; B9.6 shipped 1 (chart-width fix); 7 are PROPOSED across A1/A6/B9/C-9. **2 remain NO_HOME:** **PH-1 "feature hidden away"** (surface-visibility redesign — how does a user land on Product History without knowing the URL?) and **PH-10 "drawer-style page on desktop"** (design open question). Deeper redesign has no brief. Overlaps with [[FU-227]] resolved "your prices" work but that closed the *stock-item* side, not the *product* side.
- **Why deferred:** briefs went to higher-priority surfaces; Product History is Products-layer, data-gated, so it only matters once real product data is ingested.
- **Recommended resolution:** discussion — decide whether a Product History redesign is worth its own brief (given the Products layer is data-presence-gated) or whether the "your prices" intel layer subsumes the user need. Wait until [[FU-214]] product-surface browser verify surfaces real usage patterns.


## [OPEN] FU-214 — Products-as-overlay Phase F tail: product-surface browser verify + L197/205/206/223/225 items
- **Raised:** 2026-06-22 (Phase F kickoff — reconstructed 2026-07-01 from `PRODUCTS_OVERLAY_RUNBOOK.md` + 8 worklog references; **the FU entry itself was missing from both ledgers**).
- **Type:** deferred job (multi-item Phase-F tail).
- **What:** Original scope was **product-surface browser verify + build the L205/206 bulk-select variants + decide L197 hard-delete**. Over time it accumulated:
  - **L197** — hard-delete decision for products (still not made).
  - **L205 / L206** — bulk-select variants on product surfaces (not built).
  - **L223** — Price-History hover-bubble dark-mode bug (added 2026-06-22 worklog).
  - **L225** — Price-History box-fit bug (redirected here from FU-227 scope, worklog).
  - Product-surface browser verify (My Products page, Price History page, stock-item Products tab) — waits on a running app.
- **Why deferred:** every item needs a running browser session; bulk-select is real UI work; L197 is a design call.
- **Recommended resolution:** when the next browser-verify session opens **and** the products layer has real data — knock out L223/L225 as bugs, do the browser-verify checklist, then split L197 (design call) and L205/206 (build) into their own FUs if this one gets too heavy. **This FU is the runbook's Phase F blocker** ([`PRODUCTS_OVERLAY_RUNBOOK.md`](docs/04_proposals/PRODUCTS_OVERLAY_RUNBOOK.md) §Status row F). Related: [[FU-227]] (resolved), [[FU-212]] (resolved), [[FU-210]] (resolved).

## [OPEN] FU-413 — EMAIL_SETUP_FINDINGS: promote proposal to IMPL
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** deferred job.
- **What:** `docs/05_investigations/EMAIL_SETUP_FINDINGS.md` produced a §"Proposal" section for the forgot-password / email-wiring path. No IMPL plan; nothing shipped. This is the managed-convenience-that-degrades-gracefully case from §7.5 discipline #6.
- **Why deferred:** feature-absent when unconfigured is currently acceptable; only becomes a blocker at commercialization.
- **Recommended resolution:** before Phase 4 / any hosted deployment — draft `IMPL_PLAN_EMAIL_SETUP.md`, wire SMTP config through `AppSetting` with a "degrades to feature-absent" default.

## [OPEN] FU-412 — COMMERCIALIZATION_REPORT: dormant, not yet actioned
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** deferred job.
- **What:** `docs/05_investigations/COMMERCIALIZATION_REPORT.md` is a Phase 4 planning input. Not translated into a plan or prompts.
- **Why deferred:** Phase 4 territory.
- **Recommended resolution:** at Phase 4 kick-off — read the report top-to-bottom, spawn per-recommendation FUs / plans.

## [OPEN] FU-410 — MULTI_USER_READINESS §5 open questions
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** deferred job.
- **What:** `docs/05_investigations/MULTI_USER_READINESS.md §5` lists open questions gating Phase 4 tenancy work.
- **Why deferred:** Phase 4.
- **Recommended resolution:** at Phase 4 tenancy kick-off; part of P7-A1 / P7-A2 (see [[FU-406]] / [[FU-407]]).

## [OPEN] FU-409 — AUTH_ASSISTANT_SECURITY_FINDINGS: delta re-audit before commercialization
- **Raised:** 2026-07-01 (investigations audit).
- **Type:** finding.
- **What:** `docs/05_investigations/AUTH_ASSISTANT_SECURITY_FINDINGS.md` originally listed CSRF / email-change / register-first-admin issues. Most were resolved (per resolved-FUs trail). A comprehensive item-by-item confirmation vs shipped code was not re-run.
- **Why deferred:** the delta itself is the work.
- **Recommended resolution:** before any public deployment — walk every finding, tick "fixed" or reopen. Overlaps with [[FU-424]] (senior-review credibility gaps).


## [OPEN] FU-406 — P7-10 Launch readiness
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4 gate).
- **What:** `docs/06_legacy_prompt_plans/PROMPT_PLAN_PART_7_COMMERCIALIZATION.md §P7-10` — final launch-readiness checklist (marketing, legal, incident channels, escalation, on-call). Nothing done.
- **Why deferred:** last-mile.
- **Recommended resolution:** at Phase 4 finish. **Partially covered by [FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md)** — the FST document + release-gate checklist (Track 1) fulfil the *QA half* of P7-10 (the "have we actually verified this is ready?" tollgate). **Not covered** by the plan: marketing, legal, incident channels, escalation, on-call. Those remain in this FU's scope and want their own work-unit.

## [OPEN] FU-405 — P7-09 Ops (observability, CI/CD deploy, staging, backups)
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-09 — production ops. CI is deliberately disabled in this repo (`.github/workflows/*.yml` commented out to preserve GH free-tier — see memory `feedback_ci_disabled_policy`). Observability, staging, backups all unplanned. **Do not silently re-enable CI as part of this** — separate call.
- **Why deferred:** Phase 4 + CI-cost policy.
- **Recommended resolution:** Phase 4 — pair with billing (P7-06) so ops cost lands with revenue.
- **Note (2026-07-09, FU-387 audit):** when CI is re-enabled at Phase 4, wire in dependency scanning as part of this FU — a scheduled `pip-audit -r requirements.txt` + `npm audit --prefix web_app` job that opens an issue on new advisories. FU-387 shipped a manual `scripts/security-audit.sh` runner as the interim; promoting it to CI belongs here, not in a fresh FU. See [SECURITY_REVIEW.md](docs/security/SECURITY_REVIEW.md) §6 for the current baseline the CI job should measure against.

## [OPEN] FU-404 — P7-08 Compliance (privacy policy, DSAR, deletion, security headers)
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-08 — full compliance surface. Partial: some security-headers work has landed; the privacy-policy hooks + full data-export/deletion (DSAR) contract not confirmed. Overlaps with [[FU-401]] (P5-02 Privacy).
- **Why deferred:** Phase 4.
- **Recommended resolution:** Phase 4 — merge P5-02 + P7-08 into one compliance work-unit. **Partially covered by [FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md)** — the multi-user + admin FST persona flows (Track 1) will *exercise* the DSAR export, delete-account, and privacy-policy surfaces end-to-end, and the senior-review pass on the auth + backup chunks will catch drift on security headers + credential exclusion. **Not covered:** the legal drafting itself + the compliance contract wording. Those remain in this FU.

## [OPEN] FU-403 — P7-07 Plan gating + usage limits
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-07 — feature/usage limits gated by plan tier once billing is in.
- **Why deferred:** Phase 4, gated by [[FU-402]] Stripe billing.
- **Recommended resolution:** immediately after Stripe lands.

## [OPEN] FU-402 — P7-06 Stripe billing
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-06 — Stripe integration for the SaaS Path A + managed Path B.
- **Why deferred:** Phase 4; only after tenancy ([[FU-400]] / [[FU-401]]).
- **Recommended resolution:** Phase 4.

## [OPEN] FU-401 — P7-A2 Repository-enforced tenant isolation + leak tests
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4, Path A).
- **What:** P7-A2 — tenant scoping enforced at the repository layer + cross-tenant leak tests. §7.5 discipline #1 keeps this a one-layer change when the time comes.
- **Why deferred:** Path A is Phase 4.
- **Recommended resolution:** with [[FU-400]] (Households-as-tenant) as one work-unit.

## [OPEN] FU-400 — P7-A1 Households-as-tenant + admin → owner / platform-admin split
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4, Path A).
- **What:** P7-A1 — introduce households as the tenancy boundary; split "admin" into household-owner and platform-admin. Gated by [[FU-410]] (MULTI_USER_READINESS §5).
- **Why deferred:** Phase 4.
- **Recommended resolution:** first Path-A work item once Phase 4 opens.

## [OPEN] FU-399 — P7-B1 Provisioning control plane
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4, Path B).
- **What:** P7-B1 — automated provisioning for managed single-tenant instances (Path B). Same artifact, different env per §7.5 discipline #3.
- **Why deferred:** Phase 4.
- **Recommended resolution:** first Path-B work item when Phase 4 opens; can precede Path-A work.

## [OPEN] FU-398 — P7-05 Redis + object storage for images
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-05 — Redis for sessions/cache/rate-limit + object storage (S3-ish) for uploaded images. Managed-convenience per §7.5 #6 — must degrade gracefully to "feature absent" (in-memory / local disk) on self-host.
- **Why deferred:** Phase 4.
- **Recommended resolution:** with P7-04 as the "production stack" work-unit.

## [OPEN] FU-397 — P7-04 Production WSGI + web/worker split
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-04 — replace dev server with gunicorn/uwsgi, split web vs worker. Env-driven per §7.5 discipline #3.
- **Why deferred:** Phase 4.
- **Recommended resolution:** paired with [[FU-398]] Redis + [[FU-405]] Ops as the production-stack work-unit.

## [OPEN] FU-394 — P5-10 Merchant data quality & support bundle: confirm companion-scope only
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** finding.
- **What:** P5-10 — merchant data quality is now companion-scope per Decision 1. Confirm nothing in the P5-10 spec landed in Dora-core, and formally mark the P5-10 prompt as "moved to companion project."
- **Why deferred:** scoping-only.
- **Recommended resolution:** doc edit — add a "moved to companion" banner to P5-10 in the legacy plan file; close.

## [OPEN] FU-393 — P5-08 Data-model sanity review sweep
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-08 — comprehensive data-model sanity sweep. `ORPHANED_FIELDS_AUDIT` covered one slice; nullability audit, FK-consistency, index coverage, dead columns — not done as a single pass.
- **Why deferred:** hasn't been forced.
- **Recommended resolution:** opportunistic sweeps as touched (partial credit for [[FU-416]]); a single dedicated pass would be a good pre-Phase-4 gate.

## [OPEN] FU-392 — P5-07 Demo & sellable showcase mode
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-07 — seed a "showcase" install with representative data + a toggleable demo mode for prospects. Seed system exists; showcase toggle + curated dataset don't.
- **Why deferred:** Phase 4-ish; needed for sales conversations.
- **Recommended resolution:** with commercialization prep (Phase 4 opening).

## [OPEN] FU-391 — P5-06 first-week experience (post-onboarding nudges)
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-06 — first-week experience: gentle nudges to complete profile, add first recipe, run first stocktake, etc. First-day onboarding shipped (C-5); first-week nudges not built.
- **Why deferred:** waiting on the alerts/dashboard-card model to firm up. *(2026-07-07: [[FU-352]] resolved with "keep Attention + Kitchen Health coexisting", so the launchpad-alerts fold-in path for these nudges is gone; they need their own venue.)*
- **Recommended resolution:** treat as a small standalone brief when picked up — likely a nudges list on the Attention card *or* first-week-only overlay chips, not a Score-card row. Deliberately not folded into any existing dashboard card; keep the first-week experience honest as a first-week experience, not a permanent gauge.

## [OPEN] FU-389 — P5-04 Mobile / PWA field test
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-04 — real-device mobile / PWA testing pass. Overlaps with [[FU-411]] platform builds + P8-10 native.
- **Why deferred:** Phase 3-adjacent.
- **Recommended resolution:** fold into the P8-10 native-app brief; a device-lab pass is a natural gate before deciding native vs PWA-only.

## [OPEN] FU-388 — P5-03 Performance & scale pass
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-03 — comprehensive perf sweep (query N+1s, bundle size, load-tests). Only `STOCK_OVERVIEW_PERF` investigation touched a slice. No app-wide pass.
- **Why deferred:** hasn't been forced by user pain.
- **Recommended resolution:** pre-Phase-4 gate — do one comprehensive pass with real seed data at pantry size 500+ items, catch N+1s + big-query issues before they hit paying users.

## [OPEN] FU-378 — Stock Overview: action-first scan-mode ("pick action, then scan") never built
- **Raised:** 2026-07-01 (proposals audit); **tightened 2026-07-13** after the FU-364 §2.3/§7 reconciliation sweep.
- **Type:** deferred job.
- **What:** The whole `PROPOSAL_STOCK_OVERVIEW.md` open-decision set was walked against shipped C-1 code 2026-07-13 and annotated in-doc (§2.3 + new §7b). The flagged **#1 open decision (§2.3 detail nav model) is CLOSED**: `StockOverview.vue onRowClick` branches mobile→full-page / desktop→splitter-peek (one shared `StockItemDetailPage` in two frames), long-press→bulk on mobile, `@click.stop` on every in-row control covering the miss-tap concern. Six of seven §7 decisions closed; planned-meals metric superseded by `BuyVerdictBadge`. **Only §7.4 remains genuinely unbuilt:** the action-first "pick an action, then scan to apply" scan-mode — the Overview Scan button still does the old jump-to-item, gated behind `scanning_enabled` (off by default).
- **Why deferred:** scanning is an off-by-default surface; low priority.
- **Recommended resolution:** opportunistic — build with the next scanning/ingestion pass. **Note:** the §2.3 close unblocked [[FU-384]], but FU-384 has since resolved independently (via FU-508), so this is no longer load-bearing for it.

## [OPEN] FU-376 — PROPOSAL_PRODUCTS_AS_OVERLAY §7 open decisions + GAP bucket
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_PRODUCTS_AS_OVERLAY.md:262` §7 build-time open decisions + `:391` "GAP = small, not yet built" bucket. IMPL landed but these residual bits were not swept.
- **Why deferred:** small-slice residuals.
- **Recommended resolution:** doc walk vs shipped; each GAP either becomes its own FU or gets closed with a state note.

## [OPEN] FU-373 — PROPOSAL_BARCODE_SCANNING deferred slices (register-against-product + scan-unknown)
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_BARCODE_SCANNING.md` cleanup slice landed; **register-against-product UI + scan-unknown rework** deferred to Phase 2 (ingestion). Ingestion has landed but these barcode slices did not follow through. §6 "Scan tab under QR codes placement" also open.
- **Why deferred:** waited on ingestion; ingestion landed without pulling these along.
- **Recommended resolution:** next barcode-touch — build the register-against-product UI (unknown EAN → offer to link to an existing Product) + scan-unknown rework. Resolve §6 placement while there.

## [OPEN] FU-370 — PROPOSAL_SUPPORT_CHANNEL: not built
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** Draft proposal for a user support channel; no IMPL, nothing shipped.
- **Why deferred:** commercialization-adjacent; no users to support.
- **Recommended resolution:** Phase 4 alongside [[FU-402]] Stripe + [[FU-404]] compliance.

## [OPEN] FU-363 — Cross-cutting / niche feedback (Bucket C in COVERAGE_GAPS)
- **Raised:** 2026-07-01 (COVERAGE_GAPS sweep).
- **Type:** deferred job (bundle — 8 sub-items).
- **What:** `COVERAGE_GAPS.md` Bucket C cross-cutting items with no per-surface home:
  1. Full systems QA test doc (final regression walkthrough of every feature). User wants done LAST to capture the final product.
  2. Usage analytics / telemetry — "I'd like to know how people are using my app." Privacy-conscious (Charter P8).
  3. UI uniqueness / polish design pass — "looks just okay, not polished/unique."
  4. Push notifications between users (share a shopping list via notify).
  5. Kivy P2P sync branch — decide whether the user's prior experiment has a home here.
  6. Main menu bottom border — micro polish.
  7. Real ALDI / IGA logos — asset request.
  8. General UI consistency — cross-cutting.
- **Why deferred:** no per-surface home; several are Phase 3/4-timed or design-only.
- **Recommended resolution:** split into per-item FUs *only when picked up*. Items 1 (QA test doc) and 3 (polish pass) are natural Phase 4 gates; item 2 (telemetry) is a Charter P8 decision + build; item 4 (push notifications) is a Phase 3-ish feature; items 5–8 are one-shots.

## [OPEN] FU-348 — Import templates: registry has no "every importable section has a template" symmetry check
- **Raised:** 2026-07-01 (post-FU-343 self-review).
- **Type:** finding (latent bug when a second importable section lands).
- **What:** The `IMPORT_TEMPLATES` tuple is manually curated. Today
  that's fine (`stock_items` is the only shape the importer supports)
  — but when a second importable section lands (recipes, shopping
  lists), someone has to remember to add an `ImportTemplate` entry
  or the "Download template" button silently misses that section.
  The commit handler and the templates registry don't share a
  registry-of-registries; nothing enforces symmetry.
- **Why deferred:** trivially true today; only bites when a second
  section lands.
- **Recommended resolution:** when a second importable section is
  planned, introduce an `IMPORTABLE_SECTIONS` registry that both the
  commit handler and the templates endpoint consume — one entry per
  section with `{name, target_fields, synonyms, example, commit_fn}`.
  Or, simpler: at module load, assert that every section the commit
  path recognises has a matching `ImportTemplate`. The exact shape
  falls out naturally when the second section is designed; don't
  pre-design it. **Recommended resolution point:** when the second
  importable section is designed.

## [OPEN] FU-552 — PWA ships Quasar-placeholder icons for iOS apple-touch + Safari pinned-tab
- **Raised:** 2026-07-13 (surfaced while shipping FU-336 — enabling PWA mode exposed the injected icon meta tags).
- **Type:** finding (branding defect — bounded to iOS/Safari).
- **What:** With `pwa.injectPwaMetaTags: true` now active, the generated
  `index.html` references `icons/apple-icon-{120,152,167,180}.png` and
  `icons/safari-pinned-tab.svg` for the iOS home-screen icon + Safari
  pinned-tab. Those files (in `web_app/public/icons/`, generated by Quasar on
  2026-06-22, **untracked**) are Quasar's **default placeholder logo** (blue
  gear), not Dora branding. **Android/Chrome/favicon are fine** — the
  `manifest.json` install icons + `<link rel=icon>` tags point at Dora's real
  `web-app-manifest-*` / `android-chrome-*` / `favicon-*`. So only the iOS
  add-to-home-screen icon and the Safari pinned-tab show the wrong logo.
- **Why deferred:** separable from the build-mode flip; a proper fix needs icon
  generation from Dora's source brand asset, not a hacky resize.
- **Recommended resolution:** regenerate the full apple-touch + maskable +
  safari-pinned-tab set from Dora's source logo (ideally a 1024px master via
  `@quasar/icongenie`, or hand-export), replace the placeholders in
  `web_app/public/icons/`, and **commit** them (they're currently untracked). Do
  **not** commit the current Quasar-placeholder `apple-icon-*` / `icon-*` /
  `ms-icon-*` / `safari-pinned-tab.svg` in the meantime. **Recommended
  resolution point:** opportunistic, next branding/mobile pass — low urgency
  (iOS is the lowest-priority PWA target per `PLATFORM_BUILDS_AUDIT.md`).

---


## [OPEN] FU-224 — App-wide colour-usage assessment (primary vs secondary vs accent)
- **Raised:** 2026-06-18 (Stock-pages feedback pass)
- **Type:** deferred job
- **What:** During the feedback pass the user noted that the open / in-use button on the
  Stock Overview row was using `secondary` and was hard to see in Pesto dark — that fix
  landed by promoting to `primary`, but the user flagged that the broader pattern
  ("majority primary usage; not sure where secondary actually pulls weight") may need a
  separate audit. Walk the app, list every place `color="secondary"` (and other lower-used
  semantics like `info`, `accent`) appears, decide which deserve to stay vs. which should
  consolidate to `primary` or theme tokens for visual hierarchy reasons. Likely outputs:
  a short proposal under `docs/04_proposals/` + targeted fixes.
- **Why deferred:** intentionally out of scope for the feedback pass (R-007). The user
  explicitly called it out as a separate task to think about.
- **Recommended resolution:** opportunistic — fold in next time a theming/styling pass
  comes around, or after FU-046 (theme-token compliance) gets another round. **Ride-along with [FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md) Track 3** — every chunk's senior-review pass logs any `color="secondary" | info | accent"` sites worth reconsidering against this FU, so by plan close the shortlist is already assembled. Actual resolution still needs eyes-on-the-app judgement, not a code walk — so this FU stays open past plan close.

## [OPEN] FU-358 — Check / upgrade the Aldi scraper (site appears updated)
- **Raised:** 2026-06-12 (user note during Phase 1 wrap-up)
- **Type:** deferred job
- **What:** User flagged that Aldi's website appears to have
  changed; the existing Aldi scraper in the companion / merchant
  scraping module likely needs revisiting. Concrete steps when
  picked up:
  1. Hit a representative Aldi product page in a browser, compare
     the live DOM to what the scraper's selectors expect.
  2. Run the scraper against a known SKU and inspect the result
     (price, size, on-special detection) — note any fields that
     come back null / wrong / missing.
  3. Decide whether it's a selector tweak or a structural
     rewrite. Aldi historically uses a different layout from
     Coles/Woolworths, so changes there can ripple more than a
     simple class rename.
  4. If structural: cross-check the merchant scraping posture
     (`RECONCILED_FINISHING_PLAN.md` Decision 1 — scraper is the
     companion-app-only path; the core repo doesn't ship live
     scrape).
- **Why deferred:** out of scope of the current finishing-pass
  stream; needs live URLs + the companion app to investigate
  properly.
- **Recommended resolution:** opportunistic — when the user
  next needs Aldi pricing data, or as a focused session in the
  companion repo.

## [OPEN] FU-010 — Late-game holistic theme / colour / overall-look review
- **Raised:** 2026-06-05 (user request)
- **Type:** finding / deferred job
- **What:** A dedicated end-to-end pass over all themes, colours, and the overall
  visual feel of the app — viewed as a whole, in the browser, across the full
  theme set — rather than the per-chunk token work done piecemeal in A1/A1b.
- **Known input — Pesto looks over-dulled:** the user believes Pesto was dulled
  *too far*. Likely cause: the brightness tuning in A1b happened while a theme-logic
  bug was overriding the new values (the `themeService.ts` `THEMES` dict clobbering
  `themes.scss` via `setCssVar` — see the 2026-06-04 A1b round-2 worklog entry and
  the structural fix tracked in [[FU-004]]). So the dulling may have over-corrected
  against values that weren't actually rendering. Now that Pesto/Pesto Dark were
  synced, the *final* dulled value should be re-judged from scratch.
- **Also feed in:** the structural dual-source collapse ([[FU-004]]) so the review
  isn't fighting a moving target. (Note: FU-003 — the Pesto-only `--text-muted`
  42% bump — was reverted 2026-07-06; all light themes are back on the original
  50% baseline, so this holistic review starts from parity across the family.)
- **Why deferred:** look-and-feel polish is best judged late, in one sitting, on a
  near-final app — not litigated token-by-token mid-build.
- **Recommended resolution:** later — a dedicated pass during **Phase 3 (champion
  polish)** or just before **Phase 4 (commercialize)**, once the app is feature-
  complete enough to eyeball holistically. Requires the app actually running
  (deps installed) and ideally a side-by-side across all themes. **Ride-along with [FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md) Track 3** — every chunk's senior-review pass logs theme/colour anomalies against this FU so the eventual holistic pass starts with a triaged shortlist instead of a blank slate. Doesn't replace the eyes-on-app judgement pass; complements it.

