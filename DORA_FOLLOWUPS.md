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



## [OPEN] FU-562 — Self-host billing: decide revenue model (enforcement = offline license key; platform = Lemon Squeezy MoR — both decided)
- **Raised:** 2026-07-14 (billing discussion under the self-host-first decision).
- **Type:** decision + deferred job (self-host commercialization track; the self-host counterpart to the relocated subscription FU-402).
- **The constraint (why self-host billing is different):** the app runs on the customer's machine, so payment/feature-gating **can't be technically enforced** (any binary check is bypassable; self-hosters skew technical). Design around gating the **download/update channel** (which you control), not the running app. This is also why plan-gating/usage-limits (FU-403) is SaaS-only and got parked in `docs/04_proposals/OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md`.
- **DECIDED — enforcement = offline license key.** A signed key file that unlocks the app / gates downloads+updates. Adds friction + legitimacy, bypassable by determined users but standard for paid self-host. **No phone-home activation** (breaks air-gapped self-host + contradicts the privacy posture, Charter P8).
- **OPEN DECISION 1 — revenue model:**
  - **(a) Recurring annual license** — yearly fee = ongoing updates + support; stop paying → keep your last build, lose new updates (JetBrains-style). Predictable income; self-host-friendly because you gate *updates*, not the app. *Best recurring option without runtime DRM.*
  - **(b) One-time + paid upgrades** — buy once, own that version; major versions are a new/discounted purchase (Sublime-style). Lumpier income, no subscription feel.
  - **(c) Pure one-time perpetual** — pay once, own forever, updates included. Simplest/most generous; no recurring revenue.
  - **(d) Free + donations / sponsor** — free to run, optional pay. Max goodwill, minimal/uncertain revenue.
- **DECIDED — payment platform = Lemon Squeezy** (merchant-of-record). Owner chose MoR over raw Stripe to offload global sales-tax/VAT compliance (too much burden for a solo dev), and **Lemon Squeezy** specifically (indie-friendly, simplest onboarding; now Stripe-owned, so effectively Stripe's MoR layer — tax offload without direct-Stripe tax liability). Bonus: LS issues + validates **license keys** and hosts download/update delivery, so most of the decided offline-license-key plumbing comes built-in — the build is mostly wiring the app to check an LS-minted key, not a from-scratch licensing system. Ruled out: raw Stripe (owner tax-liable everywhere + build key issuance/delivery yourself); Paddle (fine too, but LS is the simpler indie fit).
- **Also decide here:** the free-tier / trial shape (a genuinely useful free tier or time-limited trial so the "aha" lands before the ask), and that the licence + terms disclaim scraping (push it to the off-by-default companion — legal de-risk, COMMERCIALIZATION_REPORT §1–2).
- **Why deferred:** no pricing decision made yet; part of the self-host commercialization push.
- **Recommended resolution:** with [[FU-412]] (self-host commercialization plan) — decide 1 + 2, then build the key issuance/validation + the MoR/Stripe checkout + download-gate. **Recommended resolution point:** at the self-host commercialization push, or sooner if you want to start charging.

## [OPEN] FU-557 — Stand up + wire the real support channel (FU-370 hook-up)
- **Raised:** 2026-07-14 (FU-370 build).
- **Type:** deferred job (out-of-app operator action + a one-line code change).
- **What:** FU-370 shipped the full support/"Report an issue" plumbing **dormant** —
  it renders nothing until a channel is configured. To turn it on:
  1. Pick + stand up a channel (see `docs/04_proposals/PROPOSAL_SUPPORT_CHANNEL.md`
     §3 / §6 — Option A public `dashy-dora-issues` repo w/ a `bug_report.yml`
     template is the recommendation; Option B hosted form; Option C email).
  2. Set the target in **one** place: either edit `_DEFAULT_SUPPORT_URL` /
     `_DEFAULT_SUPPORT_EMAIL` in
     [`support_channel.py`](dora_api/features/support/support_channel.py) and commit,
     OR set `DORA_SUPPORT_URL` / `DORA_SUPPORT_EMAIL` env for that install.
  3. Rewrite the Help "About" copy (currently a solid honest draft) into your own
     voice if you want — `HelpPage.vue`, the `support-copy` block.
  Once set, the Help button, the error-state "Report this" button, and the DoraBot
  `report_issue` link all light up automatically. No further code needed.
- **Why deferred:** the channel is an out-of-app decision that involves creating
  external infrastructure (repo/form/alias) — the user's to make, on his time.
- **Recommended resolution:** when you're ready to point people at a channel (the
  user asked for this FU explicitly so the hook-up isn't forgotten).

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
- **2026-07-14 update — item 3 `authStore` SHIPPED.** `web_app/test/unit/authStore.spec.ts` (17 tests): bootstrap probe (existing-session /me, fresh-install skip, **shared in-flight promise**, post-boot short-circuit), the **parked-promise boot-retry loop** (network vs generic message; real `NormalisedApiError` so the `isNetworkError` branch runs), credential entry points, the **FU-355 logout + silent-401 → clear-user + `clearAllListState`** contract (401 handler captured via a spied `setUnauthorizedHandler`), and the avatar cache-bust. Frontend suite now **360 tests / 27 files**. Pattern note: partial-mock `axiosHttpClient` with `vi.importActual` to keep the real error class while spying the unauthorized-handler setter. Remaining item-3 surfaces (shopping rail, `useMealPlanExport`, `useOfflineQueue`) stay opportunistic.
- **2026-07-14 update (later) — Postgres runs + scraper fixtures + two divergence bug fixes SHIPPED; item 1 reduced to CI wiring only.** Ran the **full backend suite on real Postgres** via a new `DORA_TEST_DB=postgres` selector (`tests/db_backend.py`) + a Postgres per-test isolation snapshot (DELETE-all reverse-FK + bulk reinsert; `tests/e2e/dora_api/conftest.py`). 37 failures → **0**; 1490 passed on both PG and SQLite (no regression). The failures traced to **two systemic SQLite-vs-Postgres divergence bugs, fixed at source** (real runtime bugs on a PG deployment): (a) **raw-`text()` UUID bind is dialect-dependent** — SQLite wants `bytes`, Postgres wants `str` (a wrong bind is a 500 on PG / silent zero-rows on SQLite); fixed `recipes/pool.py:bump_pool`, `meal_plans/reconcile.py:_id_bytes`, `tests/support.py:uuid_bind`; (b) **over-length `alert_key` (String(255)) 500s on Postgres** (`StringDataRightTruncation`) but passes silently on SQLite — `alerts/interact_with_alert.py` now length-guards to an idempotent no-op. **Item 2 (scraper fixtures) DONE** — `dora-companion/tests/test_provider_parsers.py` (8: Coles JSON translate + Aldi HTML parse via real selectors). **Item 3 leftovers:** shopping-rail (`shoppingListRailItem.spec.ts`, 9) + `useMealPlanExport` (3) DONE; frontend suite **372**. So item 1 is now **just the CI wiring** (gated on [[FU-405]]); only `useOfflineQueue` remains opportunistic on item 3. The dialect-aware-bind lesson is recorded in the `sqlite-uuid-text-binding` memory for future hand-rolled `text()` sites.
- **Recommended resolution (remaining):** item 1's *run-on-Postgres* half is done (suite is green on PG via the selector) — only the CI wiring remains, gated on [[FU-405]]. Item 3's `useOfflineQueue` is opportunistic per surface. **Recommended resolution point:** Postgres CI with [[FU-405]]; `useOfflineQueue` when that composable next changes.
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

## [OPEN] FU-412 — Action the COMMERCIALIZATION_REPORT into a self-host commercialization plan
- **Raised:** 2026-07-01 (investigations audit). **Scoped 2026-07-14 (self-host-first).**
- **Type:** deferred job.
- **What:** turn `docs/05_investigations/COMMERCIALIZATION_REPORT.md` into the actual **self-host** commercialization plan — legal de-risk (§1–2), robustness (§3–4), and the *product-value* monetization (§6) via a one-time licence / paid download. **The report's SaaS/managed recommendations (§5, §7, freemium/plan-gating half of §6) are out of scope here** — they live in `docs/04_proposals/OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md` for a later revisit.
- **Why deferred:** at the self-host commercialization push.
- **Recommended resolution:** read §1–4 + §6-product-value, spawn per-recommendation self-host FUs/plans. **The self-host pricing/billing decision is already captured as [[FU-562]]** (enforcement decided = offline license key; revenue model + payment platform open with options) — resolve it as part of this push.

## [OPEN] FU-406 — Self-host launch readiness (on-call/SLA sliver relocated)
- **Raised:** 2026-07-01 (legacy prompt-plan audit). **Narrowed 2026-07-14 (self-host-first).**
- **Type:** deferred job (launch gate for the self-host product).
- **What:** the launch checklist for *selling self-host* — **marketing** (landing/sales page), **legal** (a self-host licence + the scraping disclaimer), a **support / incident channel** (the FU-370/557 support-channel work is the seed), and a **release process**. **The operate-the-service sliver — uptime/SLA, on-call rotation, escalation — is relocated** to `docs/04_proposals/OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md` §3 (only meaningful when you host for customers).
- **Why deferred:** last-mile, at the self-host commercialization push.
- **Recommended resolution:** at the self-host launch. **QA half already covered by [FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md)** (Track 1 FST + release-gate). Remaining: marketing, legal/licence, support-channel stand-up (FU-557), release process.

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

## [OPEN] FU-394 — P5-10 Merchant data quality & support bundle: confirm companion-scope only
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** finding.
- **What:** P5-10 — merchant data quality is now companion-scope per Decision 1. Confirm nothing in the P5-10 spec landed in Dora-core, and formally mark the P5-10 prompt as "moved to companion project."
- **Why deferred:** scoping-only.
- **Recommended resolution:** doc edit — add a "moved to companion" banner to P5-10 in the legacy plan file; close.

## [OPEN] FU-563 — Data-model: schema drift (model≠migrations) + FK index coverage
- **Raised:** 2026-07-14 (spun from the FU-393 data-model sanity sweep — see [`DATA_MODEL_SANITY_SWEEP_FU393.md`](docs/05_investigations/DATA_MODEL_SANITY_SWEEP_FU393.md) Findings 1, 2, 6).
- **Type:** deferred job (remediation; cites **R-003** single-source + **R-006** clean-migrations).
- **What:** `table_mappings.py` (`create_all`, used by dev + the whole e2e suite) builds **1** secondary index; the Alembic chain (`upgrade`, production) builds **32**. 31 index colsets live only in prod, so dev/test run a materially different (near-unindexed) schema. Separately, **42 FK columns have no covering index in prod** (35 with CASCADE/SET NULL → parent-delete scans the child table). And `test__migrations__migrated_schema_matches_orm_metadata` only compares **table names**, so none of this trips CI.
- **Fix:** make the ORM model the source of truth for indexes — mirror the 31 migration-only index colsets into `table_mappings.py` + declare `index=True` on the 42 FK columns; generate one clean forward-only migration; **strengthen the schema-match test** to compare columns + nullability + index colsets. Spot-confirm the handful of FKs SQLite reflected as `ondelete=None` (Product.store_id, ProductOffer/ProductHistoricOffer.product_id, StockItem.stock_group_id/stock_level_id/stock_location_id) while there.
- **Recommended resolution:** pre-Phase-4 gate; low-risk/additive. Pairs with [[FU-564]] (same reconciliation migration can carry both if done together).

## [OPEN] FU-564 — Data-model: nullability drift (model vs migrated), 3 Product columns
- **Raised:** 2026-07-14 (spun from FU-393 — see the sweep report Finding 3).
- **Type:** finding → small fix.
- **What:** 4 columns disagree model-vs-prod. `User.username` (model NOT NULL / prod nullable) is a **known, documented deferral** (the `add_user_auth` migration explains the risk; app enforces on insert) — keep, just comment it. The 3 `Product` columns look unintentional: `merchant_stockcode` (model nullable / prod NOT NULL — dev accepts NULL, prod rejects), `is_active` + `is_available` (model NOT NULL / prod nullable — prod can hold NULLs the ORM assumes never occur).
- **Fix:** per column, decide intended nullability → clean `ALTER SET/DROP NOT NULL` migration (backfill first where tightening) or relax the model to match; add a one-line comment on `User.username` pointing at the deferral.
- **Recommended resolution:** fold into [[FU-563]]'s reconciliation migration, or a small standalone.

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

## [OPEN] FU-373 — PROPOSAL_BARCODE_SCANNING deferred slices (register-against-product + scan-unknown)
- **Raised:** 2026-07-01 (proposals audit).
- **Type:** deferred job.
- **What:** `PROPOSAL_BARCODE_SCANNING.md` cleanup slice landed; **register-against-product UI + scan-unknown rework** deferred to Phase 2 (ingestion). Ingestion has landed but these barcode slices did not follow through. §6 "Scan tab under QR codes placement" also open.
- **Why deferred:** waited on ingestion; ingestion landed without pulling these along.
- **Recommended resolution:** next barcode-touch — build the register-against-product UI (unknown EAN → offer to link to an existing Product) + scan-unknown rework. Resolve §6 placement while there.

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

