# Engineering Standards & ADR Log

**Status:** Living. Seeded 2026-06-06; grows by ADR.
**Scope:** The code/architecture rubric every agent obeys on **every** task —
features, fixes, *and tidy-ups*. This is the engineering counterpart to the
**Dora Decision Charter** (`DASHY_DORA_CHAMPION_PLAN.md` Part II): the Charter
governs *product/UX* decisions; this doc governs *how the code is built* so the
same cleanup never has to be done twice.

> **Why this exists.** Repeated audits (theme-token compliance, `q-btn` →
> `BaseButton`, dialog-chrome unification, server/client state duplication,
> filter-bar standardisation) keep finding the *same* drift re-introduced by
> later work that didn't know the rule. A rule that lives only in a finished
> proposal doc is invisible to the next agent. These rules are loaded into every
> session (via `CLAUDE.md`) so they are seen *before* the code is written, not
> discovered in the next audit.

---

## How to use this doc (MANDATORY — every task)

1. **Before building / tidying:** read the standing rules (§ Rules). State, in
   your plan or worklog, that the approach honours them — or which one it bends
   and why.
2. **While building:** prefer the compliant option. Do not take the shortcut that
   creates future cleanup. *No lazy code. Do it properly, do it consistently.*
3. **When you find an existing violation** (yours or pre-existing), you have
   exactly two honest exits — never a silent third:
   - **Explain it in place** — an inline comment stating *why* the rule is bent
     here (a real constraint, an approved carve-out, a deliberate exception). The
     comment must name the rule (e.g. `// R-002 carve-out: brand logo hex`).
   - **Flag it** — log a `DORA_FOLLOWUPS.md` item (`[OPEN]`, type `finding`) with
     the rule id, the location, and a recommended resolution point.
   A violation that is neither fixed, explained, nor flagged **blocks the work
   unit from closing.** This is enforced in the `CLAUDE.md` end-of-work ritual.
4. **At end of work:** run the **ADR evaluation** (§ ADR process) — did this task
   surface a recurring decision worth promoting into a new rule? If yes, write the
   ADR.

A reviewer (human or agent) should be able to read a diff and see, for every
deviation, either a fix, a self-explaining comment, or a follow-up. Nothing
unexplained.

---

## Rules

Each rule: **Rule** (the imperative) · **Why** · **Apply** (when/how) ·
**Violation signal** (how to grep/spot it) · **Carve-outs** (the legitimate
exceptions, which still must be commented) · **Source** (where it was established).

### R-001 — Componentisation first
- **Rule:** Build UI from the shared base components (`BaseButton`, `BaseDialog`,
  `FilterBar`, the `dora-*` primitives). Do **not** hand-roll a raw `q-btn` /
  `q-dialog` / bespoke filter or multi-select chrome when a base component exists
  or should. If a pattern recurs (≈2–3 uses), extract a component rather than
  copy it a third time.
- **Why:** Hand-rolled chrome is the single biggest source of "make it consistent"
  cleanup (button styling, dialog headers/actions, filter containers all drifted).
- **Apply:** New or touched UI uses the base primitive. When you touch a file
  still on raw `q-btn`/`q-dialog`, migrate the bits you touch (don't rewrite the
  whole file — that's R-007 scope), and leave the rest flagged.
- **Violation signal:** new `q-btn`/`q-dialog` in a diff; a second copy of a
  layout/interaction that a component already owns.
- **Carve-outs:** a genuinely one-off primitive a base component can't express —
  comment it.
- **Source:** `DORA_FOLLOWUPS.md` FU-005/006/008/009/011/012/013.

### R-002 — Theme tokens only; no hardcoded colour
- **Rule:** All colour rides semantic CSS tokens (`var(--text-*)`,
  `var(--surface-*)`, `var(--semantic-*)`) or the `dora-*` helper classes, or
  theme-aware Quasar semantics (`color="primary"`, `text-positive`). **Never**
  hex, `rgb()/rgba()/hsl()`, Quasar *numbered* palette classes (`text-grey-7`,
  `bg-red-1`), or palette `color=`/`text-color=`/`track-color=` props with a
  numbered/named palette value.
- **Why:** Hardcoded colour breaks every dark theme and has regressed *repeatedly*
  after each paint pass (see FU-046).
- **Apply:** For a chip/badge with a neutral state, route the neutral branch
  through `dora-bg-sunken dora-text-secondary` / `dora-text-muted` and keep only
  the saturated semantic branch (`positive`/`negative`/`warning`) on its
  `color=`/`text-color="white"` props (white-on-saturated is theme-stable).
- **Violation signal:**
  `grep -nE "#[0-9a-f]{3,8}|rgba?\(|text-(grey|red|green|amber|blue)-[0-9]|bg-\w+-[0-9]|'grey-[0-9]'"`
- **Carve-outs (must be commented):** brand-logo hex (Aldi/Coles/IGA),
  deterministic hash swatches (`ProductSearchCard` DEC-8), `ScanOverlay` rings
  (DEC-4), `MerchantLogo` placeholder (DEC-9), settings theme-picker swatches
  (DEC-10), the `read('--token', '#hexfallback')` canvas pattern. The colour-value
  source files are exempt: `tokens.scss`, `themes.scss`, `colours.scss`,
  `quasar.variables.scss`, `themeService.ts`, `motion.scss`.
- **Source:** `web_app/THEME_AUDIT.md`, `prompts/A1_theme_compliance.md`, FU-046.

### R-003 — Single source of truth for domain logic & constants
- **Rule:** A domain rule, threshold, or constant lives in **exactly one place**.
  The **server owns derived domain facts and cross-entity aggregates**; the
  **client owns presentation and ephemeral view state**. No domain constant (a
  stock-level name, a "7-day" window, a status sequence) or cross-entity rule (e.g.
  "cookable") exists in two languages.
- **Why:** Duplicated logic silently diverges; the `"Out of Stock"` literal alone
  was found in ~28 spots, each guarding against the others drifting.
- **Apply:** A client computing a cross-entity rule, summing across a fetched
  collection, or hardcoding a domain constant is a smell → push it to the server
  and expose it on the DTO; don't copy it a fourth time. Reuse the one existing
  helper (e.g. `scrapedProductOfferLogic.ts`) rather than re-deriving.
- **Violation signal:** the same constant string/number on both sides of the wire;
  a `.find(l => l.name === '…')` domain match in a component; a client re-sum of a
  total the server already computes.
- **Carve-outs:** pure *display* math on server-provided values is fine on the
  client (discount %, unit price) — do **not** over-correct these to the server.
  See the "already clean — do not relocate" list.
- **Source:** `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` §8.4 (the standing principle),
  mirrored in `CLAUDE.md`.

### R-004 — Stay on the existing framework
- **Rule:** Flask / Quasar / Vue 3. Productionize what exists; do not introduce a
  new framework, language, or parallel stack (no FastAPI, no C#, no rewrite).
- **Why:** A solo-dev finishing project; framework churn is unbounded scope.
- **Apply:** Solve within the current stack's idioms.
- **Violation signal:** a new web framework / second backend appearing.
- **Carve-outs:** none without an ADR.
- **Source:** `CLAUDE.md` Don'ts; Charter Part III cross-cutting build rules.

### R-005 — Portable data access & distribution posture
- **Rule:** Data access is **repository-routed**; the DB layer stays portable
  across **SQLite *and* Postgres** (Postgres is the standard target, SQLite the
  lightweight self-host option); cloud-vs-self-host differences are env/config
  driven (no build forks); auth sits behind an interface with a local default;
  **no speculative `tenant_id`** (single-tenant = tenancy of size 1); managed
  conveniences degrade gracefully.
- **Why:** Keeps the "one codebase, SaaS-style, self-hostable" (GitLab-way) trunk
  reachable without paying for multi-tenancy now.
- **Apply:** On any task touching data access, auth, config, or deployment, run the
  `RECONCILED_FINISHING_PLAN.md` §7.5 checklist. Prefer the Postgres-native path
  where SQLite forces a wrinkle (e.g. the UUID/`text()` binding), but keep both
  working.
- **Violation signal:** raw SQL bypassing the repository layer; an engine-specific
  feature with no portable fallback; a `tenant_id` added speculatively.
- **Carve-outs:** documented in §7.5 / Decision 5.
- **Source:** `RECONCILED_FINISHING_PLAN.md` Decision 5 + §7.5; `CLAUDE.md`.

### R-006 — Clean migrations & explicit dev resets
- **Rule:** Alembic migrations are clean and forward-only — **no idempotent
  guards** (`IF NOT EXISTS` defensiveness) papering over a messy history. Dev
  schema resets go through `drop_all`, gated by `DORA_ALLOW_DESTRUCTIVE`.
- **Why:** Guarded migrations hide drift and make the history un-trustworthy.
- **Apply:** When changing schema, write a clean migration; reset dev data via the
  destructive flag, not by hand-editing.
- **Violation signal:** `IF NOT EXISTS` / try-except guards inside a migration;
  ad-hoc schema mutation outside Alembic.
- **Carve-outs:** none without an ADR.
- **Source:** memory `feedback_migrations_schema`.

### R-007 — Scope discipline / anti-creep
- **Rule:** Do exactly the task. No features, refactors, or abstractions beyond
  what it requires; no premature abstraction (three similar lines beat a wrong
  helper); no half-finished implementations; **pre-release means no
  backwards-compat shims** (no renamed `_unused` vars, re-export stubs, "removed"
  comments — just change the code). Adjacent rough code is **flagged, not fixed
  inline.**
- **Why:** Creep is how a finishing project never finishes (Charter P10).
- **Apply:** Spot something out of scope → `DORA_FOLLOWUPS.md` finding with a
  recommended resolution point, and move on.
- **Violation signal:** a diff touching far more than the task; a new abstraction
  with one caller; a compat shim in pre-release code.
- **Carve-outs:** a fix genuinely required to make the task work — note it.
- **Source:** `CLAUDE.md` Don'ts; Charter P10; memory `feedback_working_style`.

### R-008 — Code-style minimalism
- **Rule:** Minimal comments — only the non-obvious *why* (a constraint, a subtle
  invariant, a workaround, an R-00x carve-out). No WHAT-comments, no
  task/PR/caller references in code, no multi-paragraph docstrings. No emojis in
  code. No AI self-references. No gratuitous `.md` files.
- **Why:** Comments that restate the code rot; the user has repeatedly asked for
  this.
- **Apply:** Default to zero comments; add one only when a future reader would
  otherwise be confused.
- **Violation signal:** comments explaining *what*; "added for X flow" notes;
  emojis; new docs nobody asked for.
- **Carve-outs:** the explain-in-place comments R-00x enforcement *requires* — those
  are wanted.
- **Source:** memory `feedback_code_style`.

### R-009 — Safe mutations: preview → approve → commit
- **Rule:** No silent writes. User-facing mutations are previewable, undoable, and
  explainable (show *why*). Never log secrets or PII.
- **Why:** Charter P7 + P3 (self-correcting & honest).
- **Apply:** A new write path surfaces what it will do before doing it where the
  UX allows; destructive/irreversible actions confirm first.
- **Violation signal:** a fire-and-forget mutation with no preview/undo; secrets in
  logs.
- **Carve-outs:** trivially reversible, low-blast-radius writes.
- **Source:** Charter P7/P8/P12.

### R-010 — Strong types over stringly-typed matching
- **Rule:** Where the language permits, model values with the strongest type
  available and let the compiler/type-checker enforce correctness. Prefer enums,
  typed IDs, and proper types to bare strings; prefer typed comparisons to
  string-coerced ones. Don't side-step the type system (no `any`, no `# type:
  ignore`, no `str()`-both-sides to make a comparison "work") to silence a checker
  that is correctly objecting.
- **Why:** The compiler/type-checker is free, always-on review. Stringly-typed
  code pushes whole classes of bugs to runtime: this branch shipped a guard that
  compared a `UUID` to a `str` path param and so **always** mismatched (line
  tick/delete silently 404'd, FU-059) — a typed comparison or a coerced-at-the-
  boundary `UUID` would have made it impossible. A `str(...) != str(...)` patch
  fixes the symptom but keeps the values weakly typed; the root fix is to carry the
  strong type.
- **Apply:** New code carries the strong type end-to-end. Coerce external input
  (HTTP path/query params, JSON, env) to its real type **once at the boundary**,
  not by stringifying the strong side at each comparison. Reach for an enum/literal
  union over free strings when the value has a known closed set. On the frontend,
  prefer discriminated unions + exhaustive `switch` over string equality scattered
  across call sites; never reintroduce `any` to dodge a `vue-tsc` error.
- **Violation signal:** `str(x) != str(y)` (or `String(x) === String(y)`) bridging
  two differently-typed values; comparing a domain object to a raw string; a path
  param used as an id without coercion; `any` / `@ts-ignore` / `# type: ignore`
  added to quiet the checker rather than fix the type.
- **Carve-outs:** Values that are *genuinely* strings end-to-end (a name, a free-text
  note) stay strings. Plain-string **status sentinels backed by a closed
  `*_VALUES` set + a single validation point** (as in the shopping-list `status`
  model) are an accepted lightweight stand-in for a DB enum **only** while every
  read goes through the named constants and writes are validated against the set —
  don't let raw status literals leak across the codebase. The boundary coercion
  itself (one `UUID(raw)` / `int(raw)` at an edge) is the correct shape, not a
  violation.
- **Source:** ADR-003; this session's UUID-vs-str guard bug (FU-059).

### R-011 — Use the framework's idiomatic, current-recommended pattern
- **Rule:** Solve problems with the framework's first-party feature, not a
  hand-rolled workaround — and use the *current-recommended* version of that
  feature for the framework version pinned in `package.json` / `pyproject.toml`.
  For Vue 3.4+ that means `defineModel()` over manual `modelValue` prop +
  `update:modelValue` emit pairs; `<script setup>` over Options API; composables
  + `provide/inject` over ad-hoc global state. For Quasar that means using its
  plugins (`Screen`, `Dark`, `Dialog`, `Notify`) and **activating them per
  Quasar's docs** (e.g. `Screen.setDebounce()` in a boot file) before relying
  on their reactivity. For Flask/SQLAlchemy that means the ORM patterns the
  installed major version recommends, not pre-2.0 query idioms.
- **Why:** Hand-rolled equivalents drift from the framework's evolution,
  miss bug fixes shipped upstream, and produce subtle bugs that only show up
  at runtime. This session caught two at once in `FilterBar`: a manual
  controlled/uncontrolled `modelValue` computed silently failed because Vue
  coerces unset Boolean props to `false` (defeating the `=== undefined`
  sentinel), and `$q.screen.gt.sm` was being read without the Screen plugin
  ever being activated, so every viewport check returned `false`. The
  idiomatic patch — `defineModel()` + a `Screen.setDebounce()` boot file —
  is shorter, type-safer, and tracks Quasar/Vue upstream.
- **Apply:** Before writing custom state-sync, lifecycle, reactivity, or
  responsive code, check whether the framework already ships the primitive.
  When using a Quasar plugin that requires activation (`Screen`, `AddressbarColor`,
  etc.), wire the activation in `src/boot/` and register it in
  `quasar.config.ts`. When the framework has multiple ways to do a thing,
  pick the one the current major-version docs recommend.
- **Violation signal:** manual `modelValue` + `update:modelValue` plumbing in
  new code; reading `$q.screen.*` without a Screen activation boot file;
  custom resize listeners replicating Quasar's; Options API in a new
  component; a hand-rolled `ref` pattern that mirrors `defineModel` /
  `useTemplateRef` / `toRefs`; SQLAlchemy 1.x-style `Query.filter_by` in new
  code on a 2.x install.
- **Carve-outs:** A framework primitive that genuinely doesn't fit (rare —
  document with an inline comment + ADR). Legacy code that pre-dates the
  framework version bump can stay until it's next touched (no opportunistic
  rewrites).
- **Source:** ADR-004; this session's FilterBar bug (FU-087).

### R-012 — Discoverability: working features stay visible
- **Rule:** A feature the user is expected to *use* must be visibly reachable
  on the surface where it applies — a labelled button, a toolbar action, an
  inline control. Overflow/ellipsis menus ("⋮", "More") are reserved for
  actions that are **rare or destructive** (delete, clear-all, export/print,
  one-a-month housekeeping). Never bury a working action three taps deep to
  save visual space; if the toolbar is crowded, that's a design problem to
  solve with hierarchy, not with hiding.
- **Why:** If it's hidden, the user is less likely to find out it exists.
  The shopping-list surface proved it repeatedly: group-by/refresh-deals/
  move/export all sat behind one unlabelled ellipsis, the per-row actions sat
  behind a second one, the price editor hid behind an unstyled text chip and
  the shop-day setter behind an unstyled text link — the user reported
  *missing the existence* of several of these (UX-v2 feedback S5/S12/S14/S17).
- **Apply:** When adding an action, default it to a visible labelled control
  on the page toolbar (`PageToolbar` actions slot) or directly on the row it
  affects. Move it into a "More" overflow only if it is rare or destructive —
  and label that dropdown "More", never a bare icon. Buttons that *look* like
  text (links with no affordance) count as hidden.
- **Violation signal:** a new q-menu/ellipsis holding everyday actions; an
  action only reachable from a kebab when there's row/toolbar space; a
  clickable element styled as plain text; a feature whose only entry point is
  inside another feature's dialog.
- **Carve-outs:** dense list rows (e.g. a virtualised rail) may keep per-item
  housekeeping behind a kebab — the row's *primary* action (select/open) must
  still be direct. Document anything else inline with the rule id.
- **Source:** ADR-006; shopping-list UX-v2 session (user: "keep features
  visible/easily reachable as much as possible — this should be an
  engineering rule").

---

### R-013 — E2E API tests dispatch in-process via the Flask test client
- **Rule:** API-level e2e tests drive the app through Flask's
  `app.test_client()` (in-process WSGI dispatch), never a real socket server
  booted in a background thread. The `tests/e2e/dora_api/conftest.py` `api`
  fixture owns this: it runs `startup(is_test_env=True)`, logs in once, and
  rebinds the module-level `requests.*` helpers **and** `requests.Session` to
  thin adapters over the test client — so test bodies keep calling
  `requests.get(...)` unchanged.
- **Why:** The old harness ran a werkzeug dev server on `localhost:5170` and
  hit it over the loopback TCP stack — ~2.7s/test (real connection setup plus
  the Windows `localhost` IPv6-fallback penalty, compounded by the dev
  server's `Connection: close`), ~13.5 min for ~300 tests. In-process dispatch
  is the same coverage with no socket: the suite dropped to **~6s (~95×)**, and
  the fail/pass set was byte-identical the moment it landed.
- **Apply:** New e2e tests just use `requests.*` / `requests.Session()` as
  before — the fixture is `autouse`, so the rebind is always active and tests
  no longer depend on some *other* test having triggered it first. The adapter
  covers `json=`/`params=`/`headers=` and multipart (`files=`/`data=`); extend
  it there if a test needs a new transport feature, don't reintroduce a live
  server.
- **Violation signal:** a test spinning up `app.run(...)` in a thread; a
  `time.sleep(N)` waiting for a server to boot; a bare `requests.get` against a
  hardcoded `localhost:<port>` that assumes a real listener.
- **Carve-outs:** a genuine cross-process / network-boundary test (CORS
  preflight, real WSGI server behaviour, nginx interplay) legitimately needs a
  live server — isolate it and document the rule id inline. Pure API contract
  tests do not.
- **Source:** ADR-008; FU-166 (legacy e2e suite triage).

### R-015 — Every DB constraint has a deterministic name (SQLite batch-mode compatibility)
- **Rule:** Every `UNIQUE`, `CHECK`, `FOREIGN KEY`, `PRIMARY KEY`, and `INDEX`
  in the schema **must end up with a deterministic name**. We get this by
  attaching the project `NAMING_CONVENTION` (defined in `dora_api/app.py`) to
  the SQLAlchemy `MetaData`, threading it into the Alembic context in
  `migrations/env.py`, and wrapping `op.batch_alter_table` there so every
  batch operation inherits the convention without each call having to pass it.
  When a migration writes a constraint with an explicit `name=`/literal, give
  it the **bare suffix** (e.g. `'shopping_list_line_anchor'`) and let the
  convention add the type prefix — never hard-code `ck_*`/`uq_*`/`fk_*`
  yourself (that double-prefixes under the convention).
- **Why:** SQLite has no `ALTER TABLE ADD/DROP CONSTRAINT`, so Alembic's
  batch mode rebuilds the table by copying rows into a fresh one — and to do
  that it has to re-emit every constraint. An **unnamed** constraint can't be
  reproduced, and the chain dies (`ValueError: Constraint must have a name`).
  Bit us twice already (FU-178: full-chain `flask db upgrade` died at
  `d7c9e4a8c2b1`; two-machine sessions where the second machine couldn't
  bootstrap a SQLite DB).
- **Apply:** All new constraints (on models and in migrations) inherit the
  convention automatically; you just need to **stop hand-writing `ck_*`-style
  literal names** in migrations — write the suffix only. New batch migrations
  need no per-call boilerplate; the `env.py` wrapper injects the convention.
  Postgres deploys benefit too — deterministic names make ops grep-able.
- **Violation signal:** a model `UniqueConstraint(...)` / `CheckConstraint(...)`
  with no `name=` **and no MetaData convention**; a migration adding an
  unnamed constraint inline (e.g. `db.UniqueConstraint('x','y')` with no
  name); a migration literal that re-prefixes its type
  (`'ck_<table>_<suffix>'`) and so double-prefixes under the convention;
  `flask db upgrade` from base failing with `ValueError: Constraint must
  have a name` or `ValueError: No such constraint: 'ck_<table>_ck_<suffix>'`.
- **Carve-outs (must be commented):** none — the convention covers all
  practical cases.
- **Source:** ADR-010; FU-178 (resolved 2026-06-17).

### R-014 — Reveal-and-disable: show a feature exists even when it isn't set up
- **Rule:** Prefer to **surface a feature's entry point even when the feature
  is not yet configured/enabled**, rendered in an obvious **disabled / "not set
  up" state** (a `:disable`d control + a tooltip/hint that says how to enable
  it), rather than `v-if`-removing it. The goal is discovery — users should
  learn a capability exists so they can choose to turn it on. Applies **where
  it makes sense** (judgement, not a blanket reveal of everything gated).
- **Why:** A hidden feature is one the user never discovers and never adopts.
  The product should advertise its own capabilities (show the email/scan
  affordance, disabled, with "Set up emailing in Settings" — not a blank
  space). Distinct from ADR-002, which gates *functionality* behind the flag;
  this rule governs the **presentation of the off/unconfigured state** —
  visible-disabled, not absent. It therefore partially revisits ADR-002's
  hide-when-off presentation.
- **Apply:** When gating an action on a config/enable flag (SMTP configured,
  `scanning_enabled`, an integration set up), render the control disabled with
  a one-line reason + a path to enable it, instead of removing it. The disabled
  affordance must read "available, not yet set up", **not** "broken"; the action
  must not fire while disabled.
- **Violation signal:** a `v-if="featureEnabled"` that removes an *adoptable*
  feature's only entry point (vs `:disable` + a hint); a blank toolbar where a
  setup-able action could advertise itself.
- **Carve-outs (must be commented):** features genuinely inapplicable to the
  install (not merely unconfigured); surfaces where a disabled control would
  mislead or clutter; security-sensitive surfaces that shouldn't advertise
  their existence.
- **Source:** ADR-009; meal-plans impl review (user: builder Email button
  disabled-not-hidden; "we want to SHOW features exist … but obvious it's not
  set up"; scanning button should now show disabled instead of hidden).

### R-016 — Lazy store hydration; boot files don't block app mount
- **Rule:** Pinia stores hydrate **lazily, on demand**, via an
  `ensureLoadedAsync()` method that no-ops if the collection is already
  populated and dedupes concurrent first-time loads. **Pages own their own
  data hydration** — call `ensureLoadedAsync()` in `onMounted` /
  `beforeRouteEnter` for what the page actually needs. The Quasar `boot/`
  layer must **never** `await` collection fetches at the top level — in
  practice this means no `boot/` file should be doing data hydration at all
  (Dora's `boot/stores.ts` was deleted, not just rewritten). Use the bare
  `getXAsync()` only as a **force refetch** (after a mutation,
  pull-to-refresh, manual reload button).
- **Why:** A top-level `await` in a boot file blocks the entire shell from
  rendering until every queued fetch resolves — on a cold backend that is a
  blank-screen second or two, the opposite of "smooth navigation". And as
  stores accrete, the boot list drifts: ours preloaded `productStore` long
  after Phase D moved products to an overlay, paying for a fetch nothing on
  the cold path needed. Lazy hydration means each page only pays for what
  it reads, while the boot warmup still primes the most-used collections in
  the background so navigation feels instant.
- **Apply:** New stores expose `getXAsync` (refetch) **and**
  `ensureLoadedAsync` (load-if-missing). The two-flag pattern is:
  ```ts
  let hydrated = false;
  let inflight: Promise<void> | null = null;
  const ensureLoadedAsync = (): Promise<void> => {
      if (hydrated) return Promise.resolve();
      inflight ??= getXAsync().finally(() => { inflight = null; });
      return inflight;
  };
  ```
  Pages: call `ensureLoadedAsync()` in `onMounted`. Don't gate on
  `length === 0` at the call site — that's what the store guard is for.
  Don't add new top-level `await`s in `boot/`.
- **Violation signal:** a `boot/` file with `await use…Store().getX…()`
  at module scope; a page that branches on `store.items.length === 0`
  around a `getXAsync()` call (the guard belongs in the store); a new
  store exposing only `getXAsync()` with no `ensureLoadedAsync`.
- **Carve-outs (must be commented):** post-mutation refresh after a
  save/move/delete (force the refetch via `getXAsync` and explain it's
  picking up server-derived fields); pull-to-refresh; explicit "reload"
  affordances. Stores whose state is purely client-local (no fetch) don't
  need the helper.
- **Source:** ADR-011; user query 2026-06-18 about boot-time preloading
  vs best practice (this work unit). Earlier inlined `length === 0`
  checks across DoraChat / QuickAddSheet / RecipeCookMode /
  ShoppingListDetail / MyProductsPage / BarcodesQR / ShoppingListTemplates
  were the recurring shape that prompted the rule.

### R-017 — Seed-data discipline: features land with seed coverage
- **Rule:** any code change that **adds, modifies, or removes a feature**
  MUST also update `dora_api/persistence/seed.py` in the same unit of work,
  so a fresh `DORA_ALLOW_DESTRUCTIVE` reset yields plentiful, varied test
  data that exercises the new/changed feature's **state matrix**. New
  entities → seed rows covering edge cases (empty / threshold / over).
  Modified entities → updated seed values (no orphan rows the new code
  can't render). Removed entities/columns → cleaned references. Pure
  refactors, non-feature tidy-ups, and shared-helper extractions are
  carve-outs (no behaviour change → no seed movement).
- **Why:** Repeatedly a feature has landed, code-reviewed clean, but a fresh
  dev env produced no row that triggered the new code path — the next agent
  (or the user, on browser walk) had to hand-click their way through the app
  to manufacture the state. The "Your prices" widget is the canonical
  example: without the FU-227 chunk-2 observation seed (3+ obs / 1 above-1.15× /
  count-dim / store-tagged / < MIN_SAMPLES variants), the widget renders the
  empty state on every item and the above-usual chip is invisible. Seed-data
  reviews then *also* drift behind code reviews. Move them together.
- **Apply:** When the diff touches a feature surface (new endpoint, new
  entity field, changed read shape, new conditional render), open `seed.py`
  in the same commit and ask "does the fresh seed surface this end-to-end?".
  Add rows that cover **(a)** the happy path, **(b)** at least one edge — the
  threshold, the empty state, the < min-samples branch, whatever the feature
  has. Use the existing helper functions when present (`make_item`,
  `make_product`, `price_obs`, …); extract one if a third use appears.
  Re-run the seed locally (`DORA_ALLOW_DESTRUCTIVE=1` + restart) and verify
  the new state renders before closing the work unit.
- **Violation signal:** a chunk's diff touches a feature but `seed.py` is
  untouched; the worklog entry doesn't mention seed updates; the close-gate
  browser walk requires hand-clicking through the app to manufacture a state
  the new code is supposed to render; a future PR adds seed rows "to test
  a feature that landed three chunks ago".
- **Carve-outs (must be commented):** pure refactors that don't change a
  user-visible shape (extracting a helper, renaming an internal symbol);
  bug fixes that don't introduce a new state (a one-line null-check); chunks
  that explicitly **remove** a feature without adding a replacement (the
  seed clean-up is the action, not new rows). For each carve-out, the
  worklog says "no seed change needed because…".
- **Source:** FU-227 chunk 1 → chunk 8 (the pricing-system reassessment).
  The handoff doc spelled out the matrix the widget needed to render —
  baseline-ready, above-1.15×, count-dim, store-tagged, < MIN_SAMPLES — and
  chunk 2 shipped exactly those seed rows in the same unit. Without that
  discipline the visible widget would have looked broken on every item in
  the dev env. The user asked for this to be a standing rule across every
  prompt, and chunk 8 promotes it here.

### R-018 — Optional engines degrade gracefully and never hard-block install or boot
- **Rule:** any feature backed by an **optional external/native engine** — a
  separate binary, a bring-your-own service, or a platform-specific native
  wheel — MUST (a) **degrade gracefully** when the engine is absent (the app
  still boots; the surface hides, disables, or falls back to a built-in
  alternative), and (b) **not** be added as a hard dependency in
  `requirements.txt` when it can't install cleanly on **every** supported
  platform — notably the Windows desktop build. Gate it behind a runtime
  availability probe (binary on PATH / endpoint reachable / model file present)
  and document the per-platform install instead of pinning it.
- **Why:** `piper-tts` (Dora's neural voice) can't be pip-installed on Windows —
  its `piper-phonemize` dependency ships no Windows wheel — so pinning it would
  break `pip install -r requirements.txt` for the desktop target, the opposite
  of "properly added". The LLM assistant is the prior instance of the same
  shape: bring-your-own Ollama, `llm_enabled` off by default, never bundled or
  auto-downloaded. Both are optional, runtime-detected, and fall back (TTS →
  browser speech; assistant → rule-based intents) so the standard artifact
  always boots.
- **Apply:** wiring an engine = add the probe + a graceful empty/503 + a client
  fallback path. Ship the engine automatically where you cleanly can (Docker
  `RUN pip install …`; bundle the binary into the desktop build via the spec —
  guard the bundle so a missing artifact doesn't fail the build) and document
  the optional install for the paths you can't (the 503 hint / README). Large
  data assets the engine needs (e.g. Piper voice models, ~60 MB each) are **not**
  committed to git — provision them at runtime into the data dir (download on
  demand from a pinned, checksum-verified source), so a clone stays lean and the
  asset rides the persistent data volume / backups.
- **Violation signal:** a heavy/native/platform-specific package pinned in the
  main `requirements.txt`; an engine surface that 500s or blocks boot when the
  engine is missing instead of degrading; an availability check that assumes the
  engine is always present.
- **Source:** Piper TTS wiring (2026-06-23) — the near-miss of pinning
  `piper-tts` and breaking the Windows install; generalised from the existing
  BYO-LLM posture. Promotes ADR-013.

---

## ADR process (evaluate every task)

At the end of each work unit, ask: **did this task make or rely on a decision that
a future agent will face again?** If yes, it deserves an ADR — and if the decision
is a *general engineering rule*, promote it into a new `R-0NN` above.

Write an ADR when: a recurring pattern got a canonical answer; a rule was bent for a
real reason (record the carve-out so it's not "fixed" later); a tooling/architecture
choice was made that constrains future work. Do **not** write one for routine,
one-off, or purely product/UX decisions (those go to the Charter check + worklog).

**ADR entry shape:**

```
### ADR-0NN — <short title>
- **Date / task:** YYYY-MM-DD (prompt id or task)
- **Status:** accepted | superseded by ADR-0MM | proposed
- **Context:** what forced the decision.
- **Decision:** what we chose.
- **Consequences:** what this commits us to; what it rules out.
- **Promotes rule:** R-0NN (or "none").
```

---

## ADR Log

### ADR-001 — Adopt engineering standards + mandatory explain-or-flag gate
- **Date / task:** 2026-06-06 (user request after repeated theme/component regressions)
- **Status:** accepted
- **Context:** The same architectural/style cleanups (themes, `BaseButton`, dialog
  chrome, server/client state duplication) kept being re-introduced by later work
  that never saw the rule, because the rules lived only in finished proposal docs.
- **Decision:** Establish this doc as the standing engineering rubric, loaded into
  every session via `CLAUDE.md`. Seed R-001..R-009 from the Charter, the
  state-ownership proposal, the theme audit, the followups backlog, and memory.
  Every task is checked against the rules; any violation must be fixed, explained
  in place (comment naming the rule), or flagged in `DORA_FOLLOWUPS.md` — an
  unexplained violation **blocks the work unit from closing.** Each task is
  evaluated for whether a new rule/ADR is warranted.
- **Consequences:** A small per-task overhead (the check + the close-gate) buys
  consistency and stops re-cleanup. Rules grow only through ADRs, keeping the set
  grounded. The seed set is deliberately partial — more rules accrete as decisions
  recur, rather than from an exhaustive up-front sweep.
- **Promotes rule:** R-001 through R-009 (seed set).

### ADR-002 — Optional features gate on a server-owned flag surfaced via health capabilities
- **Date / task:** 2026-06-07 (P6-02 barcode/QR cleanup)
- **Status:** accepted
- **Context:** Optional/off-by-default surfaces (the LLM assistant, now scanning &
  QR labels) need one authoritative on/off switch that both the server and every
  client entry point respect, without the client hardcoding the policy or each
  feature inventing its own toggle mechanism. Two instances now share the shape
  (`AppSetting.llm_enabled`, `AppSetting.scanning_enabled`).
- **Decision:** An optional feature is gated by a single boolean on the
  install-wide `AppSetting` singleton (default `false`), exposed to clients through
  the health capability endpoint as `features.<name>`, and consumed by a tiny
  composable (e.g. `useScanningEnabled()`) — **not** a new Pinia store. The admin
  toggle lives in Settings → System and PATCHes the setting. One flag gates the
  whole surface (anti-creep), not per-control toggles.
- **Consequences:** Adding a gated feature is a known recipe (AppSetting field →
  health flag → composable → admin toggle). Distribution-posture-correct: the same
  artifact self-hosts or runs managed; the difference is config, not a build fork.
  Rules out scattering feature policy across client code or spinning up a store per
  flag. Health flags are the single read path — keep `_feature_flags()` honest
  (this task fixed a latent bug where `assistant` never reflected the real setting).
- **Promotes rule:** none (a pattern/recipe, not a new standing rule; R-003
  state-ownership already covers "server owns domain facts").

### ADR-003 — Strong types over stringly-typed matching
- **Date / task:** 2026-06-07 (P6-01 Chunk 1; user request)
- **Status:** accepted
- **Context:** The new shopping-list lifecycle e2e surfaced a guard that compared a
  `ShoppingList`/`ShoppingListLine` `UUID` against a Flask path param (always a
  `str`); with no uuid converter registered the comparison never matched, so every
  line tick/delete silently 404'd (FU-059). The expedient patch — `str(x) != str(y)`
  — works but keeps both sides weakly typed and side-steps the type system rather
  than carrying the real type. The user asked to make "prefer strong types, don't
  side-step the compiler" a standing rule.
- **Decision:** Adopt R-010. Model values with the strongest available type; coerce
  external input to its real type once at the boundary; prefer enums/literal unions
  and typed comparisons over scattered string matching; never add
  `any`/`@ts-ignore`/`# type: ignore` to silence a checker that is correctly
  objecting. Closed-set status sentinels backed by a `*_VALUES` set + single
  validation point remain an accepted lightweight enum stand-in.
- **Consequences:** Pushes a class of runtime bugs back to compile/type-check time
  (free, always-on review). Costs a little up-front discipline (boundary coercion,
  defining enums/unions) and means future cleanup may *strengthen* the `str()`-patched
  line guards to typed ids rather than leave them. Rules out "stringify both sides to
  make it pass" as an acceptable fix.
- **Promotes rule:** R-010.

### ADR-004 — Use the framework's idiomatic, current-recommended pattern
- **Date / task:** 2026-06-09 (FU-087 FilterBar bug; user request)
- **Status:** accepted
- **Context:** `FilterBar.vue` shipped a hand-rolled controlled/uncontrolled
  `modelValue` pattern (manual prop + `update:modelValue` emit + a `computed`
  getter/setter), and read `$q.screen.gt.sm` without the Quasar Screen plugin
  being activated in any boot file. Two latent bugs collided in production:
  Vue 3 coerces an unset Boolean prop to `false`, so the `props.modelValue ===
  undefined` sentinel that distinguished controlled-vs-uncontrolled never
  fired (every consumer got `false`, the panel never opened, clicks went to
  a dead getter); and `$q.screen` returns `width: 0` until `setSizes()` /
  `setDebounce()` activates the listener, so the "open on desktop" default
  silently failed on every viewport. Both regressions were invisible to
  static type-checking and produced no console output. Vue 3.4 ships
  `defineModel()` (the recommended v-model macro) and Quasar 2.x documents
  Screen activation in a boot file; using both fixes the bugs and shortens
  the code.
- **Decision:** Adopt R-011. When the framework ships a primitive for the
  problem, use it; when a plugin needs activation per the framework docs
  (Quasar Screen, etc.), wire it in `src/boot/` and register in
  `quasar.config.ts`. Prefer current-recommended patterns for the pinned
  framework version (Vue 3.4+ → `defineModel`, `<script setup>`;
  Quasar 2.x → its plugin activation conventions).
- **Consequences:** New code tracks Vue/Quasar/Flask upstream and benefits
  from upstream bug fixes automatically. Reviewers can spot violations
  quickly (manual `update:modelValue` plumbing, unactivated plugin reads).
  Legacy hand-rolled equivalents stay until next touched — no opportunistic
  rewrite sweep.
- **Promotes rule:** R-011.

### ADR-005 — Opt-in / capability flag reads go through one composable per family
- **Date / task:** 2026-06-11 (C-cross Chunk 1)
- **Status:** accepted
- **Context:** C-cross's install-wide feature flags (proposal §2.6) plus
  the per-user opt-ins (money, nutrition, image display) need a uniform
  client read path. Without one, every new flag risks a new Pinia store
  + a new health probe + a new read site convention. The
  `useScanningEnabled` / `llm_enabled` pair already shipped under
  ADR-002 with a single-flag composable each — that's fine for one or
  two flags, but C-cross is bringing in five install flags + two per-user
  flags + a reserved nutrition seam. Multiplying single-flag
  composables is the wrong path.
- **Decision:** **One composable per feature *family***, not per flag.
  Install-wide flags live behind **`useFeatureFlags()`** which reads
  `/api/health features.*` once per session and exposes a named
  computed per flag (`features.money`, `features.nutrition`, etc.).
  Per-user flags live behind tiny family composables —
  `useMoneyEnabled()` / `useNutritionMode()` / `useImagePrefs()` — that
  layer the install bool from `useFeatureFlags()` with the per-user
  value read from `/api/users/me`, returning a single ready-to-render
  boolean or enum. Consumers never read AppSetting or User columns
  directly; they call the composable. The composable owns the cache
  refresh (`refresh()` after an admin PATCH; user-flag composables
  refresh after `authStore.updateMeAsync()`).
- **Consequences:** Adding a flag is a known recipe (column → DTO →
  `_feature_flags()` map → composable key → consumer). Eliminates a
  class of "two surfaces read the same flag and one misses a
  refresh" bugs. Costs one indirection between consumer and store,
  but the indirection is the point — the layering rule (install AND
  per-user) lives in one place.
- **Promotes rule:** none directly; reinforces R-001 (single shared
  primitive) + R-003 (server owns the fact, client doesn't shadow it)
  + ADR-002 (this is the consolidated form of the per-flag composable
  pattern ADR-002 seeded).

### ADR-006 — Working features stay visible; overflow menus only for rare/destructive actions
- **Date / task:** 2026-06-12 (shopping-list UX v2 build, user directive)
- **Status:** accepted
- **Context:** The shopping-list surface hid its everyday actions behind two
  layers of unlabelled ellipsis menus, styled its price editor as a tiny text
  chip and its shop-day setter as a plain text link. The user repeatedly
  failed to discover features that existed (their words: "If it's hidden,
  the user is less likely to find it exists … keep features visible/easily
  reachable as much as possible — this should be an engineering rule").
- **Decision:** Adopt R-012. Everyday actions get visible labelled controls
  (toolbar / on-row); overflow menus are reserved for rare or destructive
  actions and are labelled "More"; clickable things must look clickable.
- **Consequences:** Toolbars carry more visible buttons (acceptable — that's
  what the toolbar is for); audits of a surface now include "is anything
  load-bearing hidden in a kebab?". Rules out the reflex of shoving new
  actions into an existing ⋮ to avoid layout work. Dense-list rows keep a
  narrow carve-out for per-item housekeeping.
- **Promotes rule:** R-012.

### ADR-007 — API JSON serialises dates/datetimes as ISO 8601
- **Date / task:** 2026-06-12 (shopping-list UX v2 build)
- **Status:** accepted
- **Context:** Flask's default JSON provider emits `date`/`datetime` as
  RFC 1123 ("Tue, 01 Sep 2026 00:00:00 GMT"). Every client-side string
  comparison against ISO dates silently failed — the route guard's
  `planned_shop_date === '2026-09-01'` never matched (so today's-list
  landing never worked), and the Chunk-7 e2e tests that asserted ISO had
  never passed. Found while adding `effective_date` / `next_up_list_id`.
- **Decision:** `DoraJSONProvider` on the Flask app (`dora_api/app.py`):
  `datetime` → `isoformat()` (offset included), `date` → `YYYY-MM-DD`.
  New API fields assume ISO; client code may compare/sort date strings
  lexicographically (ISO sorts correctly; RFC never did).
- **Consequences:** Every date/datetime in every response changed format —
  one-off risk absorbed now (JS `new Date()` parses ISO at least as well as
  RFC), in exchange for date equality/sorting working at all. Rules out
  per-endpoint string formatting of dates in DTOs.
- **Promotes rule:** none — it's one global setting, not a recurring
  decision; R-003/R-010 already cover "don't stringly-type domain values".

---

### ADR-008 — E2E API tests run through the Flask test client, not a live server
- **Date / task:** 2026-06-13 (FU-166 legacy e2e suite triage)
- **Status:** accepted
- **Context:** The e2e suite booted a werkzeug dev server in a background
  thread and drove it with `requests` over loopback TCP. ~300 tests took
  ~13.5 min (~2.7s each) — real connection setup, the Windows `localhost`
  IPv6-fallback penalty, and the dev server's `Connection: close` defeating
  keep-alive. The slow fix→verify loop made the suite a maintenance liability,
  and ~40% of it had silently drifted off the current API contract.
- **Decision:** Adopt R-013. The `api` fixture dispatches in-process via
  `app.test_client()` and rebinds `requests.*` + `requests.Session` to thin
  adapters, so test bodies are untouched. Fixture made `autouse` to remove the
  latent ordering dependency (tests that didn't request `api` only worked when
  another test had already triggered the global rebind).
- **Consequences:** Suite runs in ~6s (~95× faster), behaviour-preserving
  (identical fail/pass set on the swap). Loses the literal network/WSGI
  boundary from the default path — acceptable for API contract tests; a real
  cross-process test must opt back into a live server and say so (R-013
  carve-out). Adapter must grow to cover any new transport feature
  (multipart already handled).
- **Promotes rule:** R-013.

---

### ADR-010 — Deterministic constraint names everywhere (SQLite batch-mode)
- **Date / task:** 2026-06-17 (resolving FU-178)
- **Status:** accepted
- **Context:** Fresh-SQLite `flask db upgrade base→head` was broken: chain
  died at `d7c9e4a8c2b1_20260612_shopping_list_line_product_anchor` with
  `ValueError: Constraint must have a name`. SQLite has no
  `ALTER TABLE ADD/DROP CONSTRAINT`; Alembic batch mode therefore rebuilds
  the table, and an unnamed constraint can't be re-emitted on the rebuild.
  Several historical tables were defined with anonymous UNIQUE/CHECK/FK
  constraints, so any later `batch_alter_table` against them tripped. Tests
  bypass this (they use `drop_all + create_all`), but a real prod boot from
  base would not.
- **Decision:** Adopt a project-wide naming convention on the SQLAlchemy
  `MetaData` (`fk_/uq_/ck_/ix_/pk_` + table + column0); thread it into
  Alembic's context in `migrations/env.py`; wrap `op.batch_alter_table` in
  `env.py` so every batch operation inherits it without each call site
  having to pass `naming_convention=`. Hard cutover: no compat shims, the
  project is pre-release. Constraint *literals* in migrations use the bare
  suffix (`'shopping_list_line_anchor'`); the convention adds the type prefix.
- **Consequences:** Base→head `flask db upgrade` is clean. Downgrade-from-head
  to base trips on a small number of legacy migrations that hard-coded
  `ck_*`-style literals (double-prefix under the convention); accepted —
  downgrade-from-head is not a product flow, dev resets go through
  `drop_all`/`DORA_ALLOW_DESTRUCTIVE`. Anyone hand-writing future migrations
  must follow the bare-suffix rule (R-015). Postgres path also benefits:
  constraint names become deterministic and grep-able.
- **Promotes rule:** R-015.

### ADR-009 — Reveal-and-disable unconfigured features instead of hiding them
- **Date / task:** 2026-06-14 (IMPL_PLAN_MEAL_PLANS review, user directive)
- **Status:** accepted
- **Context:** Gating discussion for the meal-plan sequential builder's Email
  button — SMTP may be unconfigured per install (INV-4). The user wants
  features advertised so users get interested and adopt them, but with the
  off/unconfigured state obvious. This refines ADR-002, which hid off-by-default
  gated surfaces entirely; the user's example is that the `scanning_enabled`
  button should now show **disabled**, not vanish.
- **Decision:** Adopt R-014. Surface an adoptable feature's entry point in a
  visible disabled "not set up" state with a path to enable, rather than hiding
  it; gate *functionality* (not visibility) on the flag. Apply with judgement —
  inapplicable or security-sensitive surfaces may still be hidden.
- **Consequences:** Gated features become discoverable; each gated surface now
  needs a disabled-state affordance + reason. Partially revisits ADR-002's
  hide-when-off *presentation* (the functionality gating is unchanged).
  App-wide application (the scanning button, any other hidden gated surfaces)
  is a follow-up sweep, not a blanket immediate change.
- **Promotes rule:** R-014.

### ADR-011 — Lazy store hydration; boot doesn't block app mount
- **Date / task:** 2026-06-18 (user query: boot-time preloading vs best practice)
- **Status:** accepted
- **Context:** `web_app/src/boot/stores.ts` had been a top-level `await` of an
  API health check + three collection fetches (`productStore`,
  `stockItemStore`, `stockLevelStore`). That blocked the router/app mount
  until everything resolved — exactly the wrong shape for perceived speed —
  and the file had drifted: `productStore` was still being preloaded long
  after Phase D moved products to an overlay, so every cold start paid for a
  fetch that almost no surface read. Several pages had also grown a private
  inline guard (`if (store.items.length === 0) await getXAsync()`) that
  duplicated the same intent across files.
- **Decision:** Adopt R-016. Stores hydrate lazily via `ensureLoadedAsync()`
  (cached + in-flight dedupe). Pages own their data hydration on mount.
  `boot/stores.ts` was **deleted outright** (and removed from
  `quasar.config.ts`); the API-reachability surface that the old boot
  health-check covered is already owned by `authStore.bootstrapAsync()` in
  `App.vue`, which sets `bootstrapError` and is rendered by `SplashScreen`
  with a Retry button — that is the canonical "backend is down" affordance.
  `getXAsync()` remains the explicit force-refetch for mutations /
  pull-to-refresh / reload affordances.
- **Consequences:** App shell mounts instantly; pages opt into the data
  they need; there is no longer a drift-prone "what to preload" list in a
  boot file. The cold-path landing page (typically the dashboard) pays a
  small first-fetch cost on first visit instead of paying it for every cold
  start regardless of where the user lands. Stores grow one extra method
  each. Remaining pages still calling `getXAsync()` unconditionally in
  `onMounted` (MealPlans / RecipeDetail / RecipesOverview / StockItemDetail
  / StockOverview) are an opportunistic follow-up — they work today, but
  each re-fetches on every visit instead of trusting the cache.
- **Promotes rule:** R-016.

### ADR-012 — Seed-data discipline: feature changes carry seed updates
- **Date / task:** 2026-06-22 (FU-227 chunk 8; user request raised in the
  pricing-system reassessment, locked in §9 of the handoff doc).
- **Status:** accepted
- **Context:** Repeatedly a feature has landed clean (vue-tsc + lint + tests
  green) but a fresh `DORA_ALLOW_DESTRUCTIVE` reset produced no row that
  triggered the new code path. The next agent — or the user, doing a browser
  walk — had to manually fabricate state to see the feature render. The
  "Your prices" widget made this acute: without the chunk-2 observation
  seed (3+ obs / 1 above-1.15× / count dimension / store-tagged / <
  MIN_SAMPLES variants), the widget renders the empty state on every item
  and the above-usual chip is invisible. Seed reviews lagged code reviews
  by a chunk, then two, then a whole feature pack. The user asked for this
  to be a standing rule.
- **Decision:** Adopt R-017. Every feature-touching diff opens `seed.py` in
  the same unit of work and ensures the **state matrix** the feature renders
  is exercised in the fresh seed — happy path + the obvious edges (empty,
  threshold, below-minimum, error-y). Pure refactors, bug fixes that don't
  introduce a new state, and explicit removals are carve-outs but must be
  named in the worklog. Existing seed helpers (`make_item`, `make_product`,
  `price_obs`, ...) are the preferred extension point — extract a new helper
  on the third use.
- **Consequences:** Marginal per-chunk overhead (open the seed; add a few
  rows; verify with a fresh reset). Big payoff: the close-gate browser walk
  becomes a real walk (every state matrix visible without hand-clicking),
  the dev env stays honest, future agents picking up cold see the feature
  the same way the user does. Rules out the lazy "I'll seed it later" path
  that always drifts. Doesn't replace e2e tests — seed is the *visible*
  surface; tests are the *correctness* surface.
- **Promotes rule:** R-017.

### ADR-013 — Optional engines degrade gracefully; never hard-pin a cross-platform-breaking dependency
- **Date / task:** 2026-06-23 (Piper TTS wiring — chat + cook mode + voice
  settings).
- **Status:** accepted
- **Context:** Wiring Dora's neural voice meant depending on Piper. The obvious
  move — add `piper-tts` to `requirements.txt` — turned out to break the install
  on Windows: `piper-tts`'s `piper-phonemize` has no Windows wheel, so
  `pip install -r requirements.txt` fails outright, and Dora ships as a Windows
  desktop app. The feature is also inherently optional: without Piper the app
  can still speak via the browser's Web Speech API. This is the same shape the
  LLM assistant already has (BYO Ollama, off by default, rule-based fallback).
- **Decision:** Adopt R-018. Optional external/native engines (a) must degrade
  gracefully when absent — app still boots; surface hides/disables/falls back —
  and (b) must not be hard-pinned in `requirements.txt` when they can't install
  cleanly on every supported platform. Gate behind a runtime availability probe
  (`/api/tts` checks for the `piper` binary + the selected voice model; returns
  503 with a setup hint; the SPA's `useSpeechOutput` then uses browser speech).
  Ship the engine automatically where clean — the **Docker image** installs
  `piper-tts` in a `RUN` step, the **desktop bundle** ships the prebuilt binary
  (fetched by `packaging/fetch_piper.py`, bundled by `dora.spec`, pointed to by
  `desktop_app.py`); document the install for bare source/pip runs. **Voice
  models are not in git** — they're downloaded on demand into the data dir
  (`voice_provision.py`, checksum-verified) when the user picks one in
  onboarding / Settings → Voice. No manual end-user steps; no repo bloat.
- **Consequences:** `requirements.txt` keeps installing everywhere; the neural
  voice is a progressive enhancement, not a gate, and "works out of the box" on
  the shipped artifacts without bloating the repo or forcing manual setup. Cost:
  the engine isn't guaranteed present on bare source runs, so every call site
  needs the probe + fallback (already the pattern for the LLM); the desktop
  binary-bundling is per-OS build wiring that can't be verified without a build
  runner (flag it as a build/browser-walk item, not "tested"). Runtime model
  download adds a one-time per-voice fetch + a checksum/atomic-rename path to
  get right (a partial download must never read as "ready").
- **Promotes rule:** R-018.

---

## Known fixes / things to try

A non-binding cookbook of solutions to recurring problems. Not rules — just a
"if you're chasing X, here are previously-found answers worth trying first."

### Snap / jump at the end of a `q-slide-transition` close
- **Symptom:** The collapsing panel slides smoothly, then a small gap
  disappears in one frame at the very end (or appears, on open).
- **Cause:** `q-slide-transition` animates the element's `height`. Any
  margin/padding that contributes to layout *outside* the animated height
  doesn't shrink with the animation — it's still there at `height: 0`, and
  then `v-if` removes it instantly. `box-sizing: content-box` makes
  `padding` part of this problem too: `height: 0` + `padding-top: 8px`
  still occupies 8px until removal.
- **Try first:** put **all** vertical spacing on the *non-transitioning*
  parent (`q-py-md` on the outer wrapper, etc.) and leave the
  height-animating element with **zero margin/padding** of its own. Fixed
  on FilterBar 2026-06-09.
- **If that's not viable:** `box-sizing: border-box` + `padding` (no
  `margin`) on the transitioning element can also work, but the parent-padding
  approach is simpler and has been the reliable answer.
