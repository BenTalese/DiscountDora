# Proposal — Test-suite coverage, quality & cleanup

**Status:** ➗ **BUILT (with carve-outs) — 2026-07-13.** Executed across ~8
sessions (2026-07-09 → 2026-07-12) via phase-children FU-519 (Phase 3) /
FU-520 (Phase 4), plus a bonus hardening fleet (FU-534..542). Phases 1-3 done;
Phase 4 mostly shipped. **Remaining carve-outs:** Postgres-backed CI + the
coverage gate/ratchet (blocked on CI being un-commented — FU-405, P7-09 Ops);
`merchant_api` scraper fixtures (companion repo — FU-161); a few opportunistic
component/composable specs. Full resolution trail: `DORA_FOLLOWUPS_RESOLVED.md`
FU-371.
**Author/date:** 2026-06-13, written off the back of FU-166 (legacy e2e
triage + test-client conversion).
**Type:** cross-cutting engineering proposal (test infrastructure). Not a
product-surface brief — see *Coverage cross-check* at the end for why the
`F1..F49` feedback table doesn't apply.

---

## 1. Why now

FU-166 just (a) made the API suite **~95× faster** (live server → Flask test
client, R-013/ADR-008) and (b) realigned ~132 drifted assertions to the
current contract. The suite is green and fast for the first time in a while —
which is exactly the moment to invest, because every problem below was either
*caused by* or *surfaced during* that triage. This proposal turns the one-off
cleanup into a standing, trustworthy safety net.

The guiding principle (charter: Effortless + Anti-creep): **a test suite earns
its keep only if "green" means "correct" and "red" means "you broke
something."** Today neither is fully true.

---

## 2. Current state (grounded, 2026-06-13)

| Layer | What exists | Count |
|---|---|---|
| Domain unit tests (`tests/*.py`) | cookability, stock-status, product-offer, recipe-filters, shopping-list totals, snapshot price, confirm-actions level | **7 files** |
| API e2e (`tests/e2e/dora_api/`) | 19 files, now via in-process test client | **~242 tests** |
| Persistence / repository | — | **0** |
| Frontend (Vue/composables) | — | **0 (`*.spec.ts` count: 0)** |
| `merchant_api`, `emailer` | byte-compile smoke only | **0 real tests** |

**What CI actually runs** (`.github/workflows/ci.yml`):
- Frontend: `lint` + `vue-tsc` + `build` (no tests).
- API: **`pytest tests/e2e/dora_api -v`** — note the path. **The 7 domain unit
  test files under `tests/` are never run in CI.** `pytest tests` (everything)
  only happens locally, by habit.
- `merchant_api` / `emailer`: `compileall` only.

**No** `pytest-cov`, **no** coverage gate, **no** `pytest.ini`/`pyproject`
config (markers, `xfail_strict`, `filterwarnings`), **no** parallelism, **no**
per-test DB isolation.

---

## 3. Problems (all observed first-hand during FU-166)

1. **CI scope gap.** CI runs `tests/e2e/dora_api` only — the domain unit tests
   (the cheapest, fastest, most stable layer) don't gate merges. A regression
   in `stock_status` / `recipe_cookability` ships green.
2. **No coverage signal.** Nobody can answer "is this code path tested?" ~24 of
   41 API surfaces have **no** e2e file (see §4); we only *discovered* that by
   hand. Coverage % would have made it obvious.
3. **Shared mutable DB → order-coupled, fragile tests.** One SQLite file is
   seeded once per session and mutated by every test. FU-166 hit this directly:
   5 tests passed in isolation but failed in the full suite because
   `auth_flows` registers users and another suite creates a lowercase
   `two-drafts-…` stock item. We patched around it (filter-to-known-row,
   case-insensitive sortedness) — the *root* fix is isolation.
4. **Assertion duplication.** The same RFC-7807 problem-detail dict is written
   out inline **~40 times** across the router tests (every 400/404/422 case).
   When the error contract changed, all ~40 had to be hand-edited. A shared
   matcher would have made FU-166 a fraction of the work and prevents the next
   drift.
5. **Two naming conventions.** `test__get_x__Condition__Result` (legacy router
   tests) vs `test_create_with_..._roundtrips` (newer suites). Pick one.
6. **Seed-coupled magic values.** Tests hard-code "9 stock items", exact
   orderings, specific seeded names. Every seed edit silently breaks unrelated
   tests (the meals→recipes rework is why FU-164's test failed). Builders /
   explicit per-test fixtures decouple this.
7. **Zero frontend tests.** The composables I just edited (`useMealPlanExport`)
   and components (rail, `StockLevelDot`, `AddToListButton`, the whole shopping
   surface) have no unit coverage — only typecheck + build.
8. **Untested companions.** `merchant_api` (the scraper) and `emailer` are
   compile-checked only; the Aldi-scraper follow-up (FU-161) has no safety net.
9. **Thin shared helpers + noisy output.** `tests/support.py` is 3 validators;
   there are no data factories, no auth helpers, no response matchers. The
   `fuzzywuzzy` "Using slow pure-python SequenceMatcher" warning fires every
   run unfiltered.

---

## 4. Coverage gaps — API surfaces with no e2e file

Tested today: audit, auth, data, health, logging, merchants, price-history,
products, shopping-lists, stock-items/levels/locations, users (+ cross-cutting
auto-generate, primary-target).

**Untested API surfaces (24):** `recipes` ⚠️, `meal_plans` ⚠️ (only the
data-export path + auto-generate touch it), `dashboard` ⚠️, `search` ⚠️,
`alerts`, `budget`, `waste`, `reports`, `stocktake`, `recipe_collections`,
`substitutes`, `suggestions`, `assistant`, `onboarding`, `locations`,
`stock_groups`, `categories`, `cuisines`, `dietary_tags`, `tools`,
`shopping_list_templates`, `app_settings`, `client_logs`, `help`, `tts`.

⚠️ = high-value, high-churn surfaces that have shipped large features
(Cookbook, Meal Plans, dashboard) with **no API-level regression net**.

---

## 5. Proposed improvements

Organised by theme; each item tagged **[P0]** (do now — high value, low effort),
**[P1]** (structural, high value), **[P2]** (incremental coverage / polish).

### A. Make the safety net real
- **[P0] CI runs the whole suite.** Change the API job to `pytest` (or
  `pytest tests`) so domain unit tests gate merges too. ~6s now — no excuse.
- **[P0] Add `pytest.ini`/`pyproject` config:** `xfail_strict = true` (we
  already rely on it), `filterwarnings` to silence the fuzzywuzzy noise (or
  install `python-Levenshtein`), registered `markers` (see F), `testpaths`,
  `addopts = -ra`.
- **[P1] Coverage measurement + gate.** Add `pytest-cov`; report
  `--cov=dora_api` in CI, publish the number, and set a *ratchet* (fail if
  coverage drops below the current baseline — don't pick an arbitrary % target;
  forbid regressions). Surfaces §4 gaps objectively.

### B. Test isolation (unlocks parallelism + kills fragility)
- **[P1] Per-test DB rollback.** Wrap each test in a transaction/savepoint that
  rolls back on teardown (SQLAlchemy `connection.begin_nested()` + bind the
  session to it), or recreate the schema per-test for the fast unit layer. Each
  test starts from the seed baseline; no test sees another's writes.
  - Removes the order-coupling we hand-patched in FU-166 (the case-insensitive /
    filter-to-known-row workarounds become unnecessary, though harmless).
  - Lets us assert exact counts/orderings again *safely*.
  - Prerequisite for **`pytest-xdist`** (`-n auto`) — with isolation, 6s drops
    further on multi-core CI.
- **[P2] Consider Postgres-backed CI test runs** once FU-045 (Postgres
  migration) lands, so e2e exercises the production datastore, not just SQLite
  (keep SQLite for the fast local loop — R-005 portability).

### C. Reduce duplication (DRY — R-001)
- **[P0] Shared response matchers** in a `tests/support.py` (or
  `tests/e2e/dora_api/asserts.py`):
  - `assert_problem(resp, status, title=..., field=...)` for the RFC-7807 body
    (replaces ~40 inline dicts; one place to update when the contract moves).
  - `assert_envelope(resp)` → returns `items` and checks `{items,total,page,
    limit}` shape (centralises the pagination contract every list test
    re-asserts).
- **[P1] Data factories / builders.** A small `make_product(**overrides)`,
  `make_stock_item(...)`, `create_user(...)` layer (hand-rolled, or `factory_
  boy`/`faker`) so tests declare *only the fields they care about* and stop
  depending on seed magic values (problem #6).

### D. Coverage gaps by layer (the actual new tests)
- **[P1] Domain-logic unit tests** for the untested `domain/` modules:
  `recipe_tags`, `generics`, `types`, plus property-based invariants for the
  ones with rich logic (`recipe_cookability`, `stock_status`,
  `product_offer`) — e.g. *cookable ⇒ every ingredient in stock*. (See F /
  Hypothesis.)
- **[P1] API e2e for the ⚠️ surfaces first:** `recipes` (CRUD + filters +
  cookability surfacing), `meal_plans` (CRUD + entries + reconciliation),
  `dashboard`, `search`. Then the long tail in §4 by value.
- **[P2] Persistence/repository tests** for the shared query machinery
  (`SqlAlchemyRepository.paginate`, filter operators, `field_map`, NOCASE
  sort) — it's exercised *indirectly* by every list test but never directly;
  one focused suite would let the router tests stop re-proving operator
  semantics.
- **[P2] Contract/snapshot tests** for DTO shapes — a single test per endpoint
  that snapshots the response keys catches DTO drift (the exact thing FU-166
  spent days fixing) at the source, cheaply.
- **[P2] `merchant_api` scraper tests** against saved HTML fixtures (no live
  network) — gives FU-161 (Aldi scraper) a real net; **`emailer`** template-
  render + send-path tests with a fake transport.

### E. Frontend tests (new layer)
- **[P1] Vitest + Vue Test Utils.** Start with **composables** (pure-ish logic:
  `useMealPlanExport`, `useUndo`, `useShortcut`, cart/quantity helpers) — high
  value, low setup. Then key components (`StockLevelDot`, `AddToListButton`,
  shopping rail). Wire `npm run test:unit` into the CI frontend job.
- **[P2] Component interaction / a11y smoke** for the surfaces with the most
  feedback churn (shopping list, cookbook).

### F. Industry-standard practices
- **[P0] One naming convention.** Recommend the behavioural
  `test_<unit>__<condition>__<result>` (readable, greppable) and migrate the
  newer ad-hoc names to it (or vice-versa — just pick one, document in
  ENGINEERING_STANDARDS).
- **[P1] Parametrize** the repetitive cases (the per-operator filter tests, the
  page/limit validation matrix) with `@pytest.mark.parametrize` — turns ~10
  near-identical functions into one table.
- **[P1] Markers** (`unit`, `e2e`, `slow`, `scraper`) for selective runs
  (`pytest -m unit` for the sub-second inner loop).
- **[P2] Hypothesis** for domain invariants (cookability, stock-status
  thresholds, price snapshotting) — property tests find edge cases golden-value
  tests miss.
- **[P2] Arrange-Act-Assert** structure + remove the lingering `# TODO: Tests
  aren't working` / commented-out blocks (FU-166 already deleted the
  stock-item ones; sweep the rest).

### G. Cleanup
- **[P0]** Silence/triage the `fuzzywuzzy` slow-SequenceMatcher warning (filter
  or add `python-Levenshtein`).
- **[P1]** Grow `tests/support.py` into a real support package (matchers,
  factories, auth/login helper, the test-client adapter is already there).
- **[P2]** Audit for remaining seed-coupled magic numbers and dead/commented
  test code across all files.

---

## 6. Suggested sequencing

1. **Phase 1 — trust the net (P0, ~half a day).** CI runs all tests; add
   pytest config (`xfail_strict`, `filterwarnings`, markers, `testpaths`);
   add `pytest-cov` reporting (no gate yet); shared `assert_problem` /
   `assert_envelope` matchers + retrofit the router tests; pick the naming
   convention. *Immediate payoff: green = correct, and the duplication that
   made FU-166 expensive is gone.*
2. **Phase 2 — isolation + structure (P1).** Per-test DB rollback; data
   factories; parametrize the repetitive matrices; coverage ratchet on; enable
   `xdist`. *Payoff: fragility gone, counts/orderings safe to assert, suite
   parallel.*
3. **Phase 3 — close coverage gaps (P1→P2).** Domain unit tests for untested
   `domain/` modules; API e2e for `recipes`/`meal_plans`/`dashboard`/`search`,
   then the §4 tail; repository + contract tests.
4. **Phase 4 — new layers (P2).** Frontend Vitest (composables → components);
   `merchant_api`/`emailer` fixture tests; Hypothesis invariants; Postgres CI
   run once FU-045 lands.

Each phase is independently shippable and leaves the suite green.

---

## 7. Candidate engineering rules (for ENGINEERING_STANDARDS, on adoption)
- **Testing pyramid / new-feature rule:** every new feature ships with domain
  unit tests for its logic + at least one API contract test; bug fixes ship
  with a regression test. (Promotes a standing R-0NN.)
- **No inline problem-detail / envelope dicts** — assert via the shared
  matchers (extends R-001 to tests).
- **Tests must be isolation-safe** — no test may depend on another's writes or
  on seed magic values (codifies the Phase-2 fix).

These are *candidates* — adopt the ones that prove out, don't front-load the
ADR log.

---

## 8. Non-goals / risks
- **Not** chasing a coverage % vanity target — ratchet against regressions
  instead (Effortless + Anti-creep).
- **Not** rewriting the framework or the existing passing tests wholesale —
  retrofit incrementally behind the matchers.
- **Risk:** per-test rollback interacts with code that commits mid-request or
  relies on autoflush; needs care (savepoint + session rebind is the known-good
  pattern). Validate on a couple of suites before rolling out.
- **Risk:** frontend test setup (Vitest + Quasar) has non-trivial config; scope
  Phase 4 to composables first to derisk.

---

## 9. Coverage cross-check (why no `F1..F49` table)

The repo mandates a feedback-coverage table for proposals targeting a specific
**app surface** (mapping each `F#` bullet from `02_feedback/`). This proposal
targets the **test infrastructure**, not a user-facing surface — no feedback
bullet motivates it. Its drivers are engineering findings, not user feedback:

| Driver | Source |
|---|---|
| Suite was 13.5 min, ~40% drifted | FU-166 |
| Order-coupled / seed-coupled fragility | FU-166 (5 full-suite-only failures) |
| ~40× duplicated problem-detail assertions | FU-166 |
| CI runs e2e dir only; unit tests ungated | this audit (`ci.yml`) |
| 24 untested API surfaces; no coverage signal | this audit |
| 0 frontend tests; companions compile-only | this audit |
| Genuine defects hidden behind a red suite | FU-164/167/168 (found only because triage forced a read) |

Per the cross-cutting-work convention, the table above maps the *motivating
findings* rather than per-surface feedback bullets.
