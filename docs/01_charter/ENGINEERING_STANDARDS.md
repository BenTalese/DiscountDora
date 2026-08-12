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
  feature with no portable fallback; a `tenant_id` added speculatively;
  `server_default=sa.text('0')` / `sa.text('1')` on Boolean columns (SQLite-only
  literal, breaks on Postgres) — use `sa.false()` / `sa.true()` instead, which
  render portably to `0`/`1` on SQLite and `false`/`true` on Postgres; raw-SQL
  boolean comparisons of the form `WHERE flag = 1` (use the bare column —
  `WHERE flag` — or `= TRUE`).
- **Carve-outs:** documented in §7.5 / Decision 5.
- **Source:** `RECONCILED_FINISHING_PLAN.md` Decision 5 + §7.5; `CLAUDE.md`; FU-045
  (Postgres-default switch landed 2026-06-26).

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
  invariant, a workaround, an R-00x/ADR carve-out). **A comment must be useful to a
  reader who has no memory of how the code got here.** No WHAT-comments (they
  restate what the code already says). No task/PR/prompt/FU-ID references in code
  — those live in `DORA_WORKLOG.md` / `CHANGELOG.md` / commit messages, not the
  source. No multi-paragraph docstrings. No emojis in code. No AI self-references.
  No gratuitous `.md` files.
- **Why:** Comments that restate the code rot; prompt/FU-ID prefixes have zero
  value once the prompt is closed and clutter every skim; the user has repeatedly
  asked for this.
- **Apply:** Default to zero comments; add one only when a future reader would
  otherwise be confused. If the substance of a comment *is* real WHY, keep the
  substance but drop the prompt-ID / FU-ID prefix (e.g. `# P8-05 — buy-verdict
  defaults on because ...` → `# Buy-verdict defaults on because ...`).
- **Violation signal / close-gate greps** (run before closing any unit that
  touched code):
  ```
  rg -nE '(#|//) +(P[0-9]|C-[0-9]|B[0-9]|INV-[0-9]|FU-[0-9])' \
     dora_api/ tests/ web_app/src/
  ```
  Expected output: **nothing outside test-only setup helpers**. Any hit is a
  fix-in-place before close. Standing R-0NN / ADR-0NN references are allowed
  (`# R-003 —`, `# ADR-014 —` etc.) — the numeric pattern above deliberately
  excludes them.
- **Violation signal (WHAT-comments):** a comment that could be deleted without
  a future reader losing information — because it just names what the next line
  does — is a WHAT-comment. Delete it. Signals: `# Set X to Y`, `// Loop through
  items`, `# Handler for /foo endpoint` directly above `def foo():`.
- **Carve-outs:** the explain-in-place comments R-00x enforcement *requires* (an
  R-0NN or ADR-0NN reference that names the rule) — those are wanted. A one-line
  reference to a live FU that is *currently open* and load-bearing on this exact
  code (e.g. `# workaround for FU-045 — remove when Postgres migration lands`)
  is a carve-out; delete it when the FU closes.
- **Source:** memory `feedback_code_style` + FU-462 close-out (2026-07-07).

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
> **⚠️ SUPERSEDED 2026-07-06 by [R-029](#r-029--respect-the-off-state-hide-dont-nag) / ADR-025.** The reveal-and-disable directive is retired: if a user or the household admin has *disabled or not configured* an optional feature, hide it — don't advertise it as a nag. The rule text below is preserved for audit trail only; do not follow it in new work. Empty-state "calm placeholder instead of vanishing" usages (the dashboard, meal-plan week banner, etc.) are unaffected — they're a separate pattern that was mistakenly labelled R-014 in some comments and lives on its own footing.

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

### R-019 — No magic: explicit, verbose, consistent
- **Rule:** Prefer **explicit, verbose, locally-readable** code over clever,
  implicit, or auto-discovered behaviour. A reader walking a file top-to-bottom
  must be able to see *what runs and in what order* without consulting a
  separate convention, framework annotation, or "everyone knows we do it this
  way" tribal rule. And when the codebase already has an established pattern
  for a problem, **follow it** — don't introduce a parallel approach in one
  spot "because it felt right here". One pattern, applied consistently, even
  when a one-off variant looks marginally tidier in isolation.
- **Why:** Magic — auto-mappers, decorator chains that mutate behaviour,
  convention-over-configuration past what the framework requires, "smart"
  defaults that vary per-entity, conditional loading that's invisible at the
  call site — moves understanding *away* from the code and into the reader's
  head. The reader has to remember the convention; if they're wrong, the bug
  is silent. The user has named this as a top-line value ("this is exactly why
  I absolutely hate AutoMapper in C# code") — the AutoMapper shape is the
  archetype: a field maps because the names happen to align, and a rename
  three files away silently breaks the mapping with no compile error and no
  obvious site to grep. Inconsistent local patterns ("most of the codebase
  does X but here we did Y because it felt right") force every future reader
  to memorise the exception list — the *consistency* is the value, even when
  the alternative is marginally nicer.
- **Apply:**
  - **Write explicit mappers** between layers (entity ↔ DTO, request ↔
    handler input). One named function per direction; every field listed.
    Verbose, greppable, type-checked end-to-end. No reflection, no name-based
    auto-population, no "*Mapper" libraries.
  - **Avoid decorator/metaclass magic** that hides what runs. A decorator
    that *only* annotates is fine; one that mutates behaviour, rewrites
    signatures, or pulls in side-effects belongs in framework code, not in
    feature code we own.
  - **Don't lean on "convention over configuration"** past what the
    framework already requires. If the framework needs a filename pattern
    or attribute name, fine — that's the framework's contract. Don't invent
    new conventions on top.
  - **Match the codebase's established pattern** for the problem you're
    solving. If 90% of the handlers spell out the entity assignment field
    by field, the 91st does too — even if `dataclasses.replace(...)` or a
    dict-spread would save four lines. Consistency > local cleverness.
  - **No implicit eager-load shortcuts.** When a relationship needs to be
    loaded, the *call site* declares it (`.include(...)` /
    `selectinload(...)` per query) rather than the entity quietly
    auto-loading it. The relationship's default loading stays the
    codebase-wide default (currently `noload`).
- **Violation signal:** auto-mapping libraries (`automapper`,
  reflection-based field copy, `**dataclass_dict`-shaped converters
  between layers); decorators that wrap business logic (`@retry`-style
  decorators that change control flow); per-entity SQLAlchemy
  `lazy="..."` overrides that opt one relationship into a different
  loading strategy than the codebase default; a function that
  short-circuits or transforms based on a name-string match
  ("if it's called 'special_*' then …"); two handlers in the same
  feature folder solving the same shape two different ways; a
  comment of the form "*usually we do X, but here we do Y because …*"
  that isn't documenting a rule's carve-out.
- **Carve-outs:**
  - The framework's *own* idiomatic patterns (R-011) are not magic — using
    `@RECIPE_ROUTER.route(...)`, `@dataclass`, or Vue's `<script setup>` is
    using the framework as documented.
  - A genuinely one-off real-world constraint (a third-party API quirk,
    a regulatory exception) may require a local divergence — explain it in
    place with a comment naming this rule and the reason, *not* just
    "felt right".
- **Source:** ADR-014; user message 2026-06-28 promoting FU-084 from a
  narrow "selectin loading" recommendation into this broader rule.

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

### R-021 — Calendar-day logic runs in the household timezone
- **Rule:** Any code that decides "what calendar day is it" — "today",
  "tomorrow", "N days ago / until", a date-boundary window — MUST evaluate
  in the **household timezone** (`AppSetting.timezone`, IANA) on the server,
  via `dora_api.features.app_settings.clock.household_today(repository)`.
  **Never `date.today()`** in feature code: that returns the server-local
  date, which has nothing to do with the household and silently desyncs by
  ±1 day for any household whose offset crosses midnight relative to the
  server. Wall-clock events (created_at, audit log, last_login) stay UTC
  via `datetime.now(UTC)`; **calendar boundaries** route through
  `household_today`. The two are different concerns; mixing them is the
  bug.
- **Why:** The product is a household pantry — every "today" the user sees
  is *their* today, not the server's. Once we run on Postgres in
  Frankfurt (or a managed single-tenant deploy anywhere), every
  `date.today()` quietly becomes wrong. The mechanism (household
  timezone in `AppSetting`, `clock.py` helpers) shipped with C-2.K for
  the meal-plan boundary; FU-174 was the followup to spread it
  everywhere. Without the rule, the next feature touches `date.today()`
  again because that's what Python developers reach for. The rule pins
  the convention: there's exactly one entry point for "what day is it"
  and it always knows the timezone.
- **Apply:**
  - **Server, calendar boundary:** `today = household_today(repository)`.
    Repository plumbing is already on every feature handler; pass it
    through.
  - **Server, wall-clock event:** `datetime.now(UTC)` (Python 3.12+
    canonical form). Storage: `DateTime(timezone=True)` column.
  - **Calendar columns** stay `Date` (no time, no tz). The day this
    expires / was opened / was scheduled is a calendar concept; tz
    semantics live in the *boundary check*, not in the value.
  - **Client:** the server is authoritative for "today". The client
    fetches the boundary (e.g. `mealPlanStore.todayIso`,
    `meal-plans/today`); never computes it from `new Date()` for any
    decision that affects state. A *display-only* fallback before the
    server response arrives (e.g. `localTodayIso()` to seed the calendar
    cursor for a frame) is allowed when commented as such — the data
    binding flips the moment the server response lands.
  - **Display path:** absolute datetimes still render via
    `toLocaleDateString()` (browser-local) — that's user-friendly for
    "when did this happen". Calendar dates (Date type) render as the
    day they represent, no timezone conversion (their semantics are
    timezone-free; `new Date("2026-07-01").toLocaleDateString()` parses
    to local midnight which is fine for read-only display).
- **Violation signal:**
  - `from datetime import date` followed by `date.today()` anywhere in
    `dora_api/features/` or `dora_api/domain/` (other than seed data).
  - `datetime.now()` with no `tz=` argument in feature/domain code.
  - Client `new Date()` / `Date.now()` used to build a date string that
    drives state (route filter, calendar navigation that's persisted,
    server payload). Display-only diffs (`relativeTime`) are OK.
  - A handler that needs a household date but doesn't take a repository
    argument — plumb the repository instead of falling back to
    `date.today()`.
- **Carve-outs (must be commented):**
  - **Seed data / fixtures** — `tests/`, `dora_api/persistence/seed.py`
    — `date.today()` is acceptable; the test environment owns its own
    notion of "now" and there's no household to respect.
  - **Pre-server-response display fallback** — a client-side
    `localTodayIso()` used purely to seed a cursor or highlight a cell
    on the first paint, before the server's boundary value arrives.
    Comment naming this rule.
- **Source:** ADR-016; FU-174 (raised 2026-06-14 during C-2.K design;
  swept 2026-06-29). The C-2.K work introduced
  `AppSetting.timezone` + `clock.household_today` for the meal-plan
  past-day rule; FU-174 extended the rule app-wide and promoted it
  here.

### R-020 — Deferred-save surfaces wire the unsaved-changes guard
- **Rule:** **Any page** that lets the user accumulate edits in local state
  and only persists them when a **dedicated Save action** is invoked **MUST**
  wire `useUnsavedChangesGuard(isDirtyRef)`
  (`web_app/src/composables/useUnsavedChangesGuard.ts`) so that any
  navigation away (router push, sidebar link, browser back, refresh, close)
  prompts to confirm discard while edits are pending. Equivalently: if the
  page has a Save / Update / Apply button gated by an `unchanged` or
  `isDirty` computed, it has a draft window — and that draft window must
  be guarded.
- **Why:** Silent discard of typed edits is a top-tier UX failure — the
  user did the work, the work disappeared, and there was no warning. The
  guard composable exists (one place, one confirm-dialog policy, covers
  `onBeforeRouteLeave` + `onBeforeRouteUpdate` + `beforeunload` at once);
  the only failure mode left is **forgetting to wire it on a new editor
  page**. The pattern recurred during FU-098: even after the composable
  shipped via FU-156 wired into the two large editor pages, the audit
  found two settings pages still silently discarding (account
  username/email, install AI-config). The rule prevents the third recurrence.
- **Apply:**
  - Build a `Ref<boolean>` / `ComputedRef<boolean>` that is `true` iff any
    draft on the page diverges from its last-persisted value. For
    multi-field pages, combine the per-field `unchanged` computeds:
    `computed(() => !aUnchanged.value || !bUnchanged.value)`.
  - Call `useUnsavedChangesGuard(isDirtyRef)` once near the top of
    `<script setup>`. The save path doesn't need any extra wiring — just
    flip the underlying drafts to match `saved.value` on successful save
    and the next nav passes through.
  - The standard discard-dialog copy ("Discard unsaved changes? — Your
    edits will be lost." + Cancel / Discard) lives inside the composable.
    Do **not** re-implement the prompt per-page; do **not** wire a
    page-specific `onBack` handler that bypasses the route-level guard
    (FU-156's exact root cause).
- **What does NOT need the guard (with reasons, so the audit is repeatable):**
  - **Inline / auto-save surfaces** — every edit fires the API on
    `@blur` / `@update:model-value` / toggle. No draft window exists.
    Examples: `ShoppingListDetail` line edits, every settings page that
    saves-on-change (theme, notifications, alert thresholds, timezone,
    money, voice, etc.).
  - **Real-time session state with no Save action** — a "Done" / "Finish"
    action that persists *derived* facts (not raw drafts). Cook mode is
    the canonical example: ticked-off ingredients aren't a draft; they're
    transient session state the user expects to lose on reload.
  - **Save buttons inside dialogs / drawers / popovers** — dialog state
    is intentionally transient (Cancel closes; route nav closes the
    parent and the dialog goes with it). Modal-close is not the same
    risk as silent discard on full-page nav. (If a future report says
    otherwise, a dialog-level guard is its own follow-up.)
  - **Password fields** — browsers expect typed passwords to be lost on
    nav; guarding here works against user expectation.
- **Violation signal:**
  - A page-level form with a `label="Save"` (or "Update"/"Apply") button
    + an `unchanged` / `isDirty` computed and no `useUnsavedChangesGuard`
    call in the same `<script setup>`.
  - A page-specific `onBack` / `confirmLeave` handler reimplementing the
    dialog locally (route-level guard not wired, only the back button
    is protected — FU-156's exact bug).
- **Carve-outs (must be commented):** the four categories above are
  the standing exclusions — if you're skipping the guard, the comment
  should name the category ("save-on-blur", "real-time session",
  "dialog-only", "password field") so the next audit can ratify or
  reject quickly.
- **Source:** ADR-015; FU-098 (2026-06-29) — sweep that promoted the
  pattern after FU-156 (2026-06-12) shipped the composable and wired
  the first two pages. Recurrence (recipe + stock-item detail in
  FU-156, then account + assistant settings in FU-098) is the
  rule-worthy signal.

### R-022 — DnD reorderable lists go through `useDragDropList`
- **Rule:** Any list whose rows are HTML5 drag-and-drop reorderable
  **MUST** plumb through the shared
  `web_app/src/composables/useDragDropList.ts` composable and the
  shared affordance classes in `web_app/src/css/dnd.scss`. Don't
  hand-roll `@dragstart` / `@dragover` / `@drop` listeners on a new
  surface, don't reinvent the dragging-row dim / drop-target ring
  CSS, and don't copy the state-machine pattern from another DnD
  surface into a fresh one.
- **Why:** Three DnD surfaces (shopping-list lines, recipe steps,
  recipe ingredients) independently grew ~80 lines of nearly-identical
  drag state + CSS, each diverging slightly on affordance details
  (outline vs box-shadow; opacity 0.4 vs 0.5; bespoke handle styles).
  Two of those used a sibling-only constraint; one used a cross-
  section reassignment effect; the *shape* of "guard the drag, light
  the drop target, dim the source, persist on drop" was the same in
  every case. Centralising the state machine + affordances behind
  the composable means a new DnD surface is ~10 lines, every list
  feels the same to the user, and accessibility/keyboard improvements
  land everywhere at once.
- **Apply:**
  - Import the composable:
    `import { useDragDropList } from 'src/composables/useDragDropList';`.
  - Construct one per list, supplying:
    - `mime` — a unique payload type (`application/x-dora-<thing>`)
      so a drag in this list never satisfies a drop check in another.
    - `getId(item)` — stable per-row id (UUID, `client_id`, etc.).
      Return null/undefined to mark the row non-draggable.
    - `onDrop({ id, item }, { id, item })` — the per-drop effect.
      The composable has already cleared its drag state by the time
      this fires.
    - **Optional:** `canDragStart(item)` (per-row drag gate; also
      use for a global "is reorder allowed at all?" predicate that
      reads a captured ref), `canDropOn(source, target)` (per-pair
      drop-target gate — defaults to "anything but self"; layer
      siblings-only / type-compat rules here).
  - In the template, spread `bind(item).rowProps` on the row body
    (drop target), `bind(item).handleProps` on the drag handle (icon
    button) **OR** the row body itself for whole-row mode (rows
    without inline editors). Apply `bind(item).rowClass` to the row.
  - Use `class="dora-dnd-handle"` on the handle wrapper to inherit
    the grab/grabbing cursor + sunken hover treatment.
- **What does NOT use this (with reasons, so the audit is
  repeatable):**
  - **Reordering via up/down arrow buttons.** Buttons are fine — DnD
    is the affordance upgrade, not the only valid pattern. The
    rule is "*if* the list uses HTML5 DnD, use the composable", not
    "every reorderable list must be DnD."
  - **External-drop targets (file uploads, image drops from outside
    the page).** Those use the platform's native `File` /
    `DataTransfer` paths, not the row-to-row reorder shape this
    composable solves.
- **Violation signal:**
  - A `.vue` file with a top-level `@dragstart` / `@dragover` /
    `@drop` listener and no `useDragDropList` import.
  - A component-scoped CSS rule that defines `opacity: 0.5` on a
    `*--dragging` class, or an outline / box-shadow on a
    `*--drop-over` class — the shared `.dora-dnd-row--dragging` /
    `.dora-dnd-row--drop-over` rules already do this.
  - A hardcoded `application/x-dora-…` MIME string outside the
    composable.
- **Carve-outs (must be commented):** none expected. If a new
  surface genuinely needs a different drag model (multi-row drag,
  reorder *and* nesting in one gesture, off-row drop zones for
  empty buckets), that's its own ADR — extend the composable
  rather than re-rolling state in the consumer.
- **Source:** ADR-018; FU-326 (2026-06-29) — extraction once three
  hand-rolled DnD surfaces (shopping-list lines [P6-01 Chunk 6],
  recipe steps [FU-094], recipe ingredients [FU-118]) made the
  duplication obvious.

### R-023 — Test naming + shared response matchers
- **Rule:** Tests follow the behavioural pattern
  `test__<unit>__<condition>__<result>` (two-underscore separators,
  greppable, readable in the failure summary). Router tests asserting
  RFC-7807 problem-detail bodies or `{items,total,page,limit}` list
  envelopes use the **shared matchers** in `tests/support.py`
  (`assert_problem`, `assert_envelope`) — never inline the dicts.
  Source-of-truth for the contract lives in one place; one update
  there propagates when the shape moves.
- **Why:** Two reasons fused into one rule. (1) The suite carried two
  naming conventions side-by-side
  (`test__get_x__Condition__Result` vs `test_create_with_…_roundtrips`),
  which made the failure summary jagged and prevented consistent
  grep / parametrize patterns. (2) FU-166 spent days re-aligning ~40
  inline problem-detail assertions when the error contract moved; the
  matchers reduce that to one fix in one file. Both are R-001 (single
  shared primitive) applied to tests.
- **Apply:**
  - New tests: name `test__<unit_under_test>__<condition>__<result>`.
    Examples: `test__create_product__OnZeroPrice__Returns400`,
    `test__get_recipes__WhenCookableFilterOn__OnlyReturnsFullyStocked`.
  - Use `assert_problem(resp, 400, field="name")` instead of writing
    `assert resp.status_code == 400; assert resp.headers['Content-Type']
    == 'application/problem+json'; assert 'name' in resp.json()['errors']`.
  - Use `items = assert_envelope(resp)` instead of re-parsing the
    `{items,total,page,limit}` shape. Pass `expect_total=N` to also
    assert the count.
  - Don't migrate green tests blindly — touch the matcher when you're
    already in the file editing that test. Standing inline assertions
    are flagged but not failure-blocking.
- **Violation signal:**
  - A new test using camelCase or `test_create_with_…` shape.
  - An inline
    `assert resp.headers['Content-Type'] == 'application/problem+json'`
    in a new test.
  - A list test re-asserting the `{items,total}` keys by hand.
- **Carve-outs (must be commented):** legacy tests using the older
  naming may stay until they're next touched. When you edit one, rename
  it. Don't open a "rename all tests" PR — the migration is per-edit.
- **Source:** ADR-019; FU-169 / PROPOSAL_TEST_SUITE_IMPROVEMENTS Phase 1
  (2026-06-29). The naming-convention split + the ~40 inline
  problem-detail assertions were both surfaced during FU-166's
  test-client conversion.

### R-025 — Session-mutating writes need both proof-of-possession and CSRF
- **Rule:** Any HTTP endpoint that mutates a session-bearing user's
  authentication identity (password, email, MFA factors, primary
  recovery channel) or that issues credentials usable to take over the
  account (API key, recovery code, OAuth grant on behalf of the user)
  must require **re-proof of the current password** in the request body
  *and* be gated by the CSRF double-submit defence in
  [`dora_api/infrastructure/csrf.py`](../../dora_api/infrastructure/csrf.py).
  The two layers are independent — neither is sufficient alone, and
  there is no asymmetry between sensitive flows (e.g. "change-password
  needs the password, change-email doesn't" is the bug R-025 exists to
  prevent).
- **Why:** FU-197 found that the email-change endpoint required no
  password proof while the password-change endpoint did. Combined with
  the then-absent CSRF token, that was a complete account-takeover
  chain: a victim browsing an attacker page while logged in could be
  silently switched to the attacker's email + reset link, all without
  the attacker knowing or guessing the victim's password. Both gaps
  fixed at once; the rule keeps them fixed by making asymmetry between
  sensitive flows a violation rather than a judgement call.
- **Apply:**
  - New auth-identity write endpoints: add `current_password: str` to
    the request model, verify with `werkzeug.security.check_password_hash`
    against the loaded `User.password_hash`, return
    `business_rule_violation("Current password is incorrect.")` on
    mismatch. Mirror the shape of
    [`ChangePasswordRequest`](../../dora_api/features/auth/change_password.py)
    /
    [`ChangeEmailRequest`](../../dora_api/features/auth/email_flows.py).
  - Side-effect notification: when the change is async (token-confirmed
    email change, recovery-code regeneration), send a heads-up to the
    address the user **currently** controls before kicking off the new
    flow — see `email_change_notice.html`.
  - CSRF is automatic: the middleware in
    [`dora_api/infrastructure/middleware.py`](../../dora_api/infrastructure/middleware.py)
    gates every mutating call on `/api/*` unless the endpoint name is
    in `PUBLIC_ENDPOINTS` or `CSRF_EXEMPT_ENDPOINTS`. **Do not** add new
    endpoints to those lists without a written rationale (bearer auth,
    pre-session bootstrap, etc.).
  - Audit emit on both success (`SEVERITY_AUDIT`) and password-mismatch
    (`SEVERITY_WARN`) so a brute-force attempt against the password gate
    is visible in the audit log.
- **Violation signal:**
  - A new `@AUTH_ROUTER.route(...)` mutator without `current_password`
    in its request schema.
  - A new endpoint added to `PUBLIC_ENDPOINTS` or `CSRF_EXEMPT_ENDPOINTS`
    without a comment explaining why.
  - SPA wiring that posts an auth-identity change without prompting for
    the current password.
  - An "admin-side" path that lets an authenticated user change their
    own auth identity without re-prove (admin acting on **other** users
    is a separate flow — those go through the audited admin endpoints,
    which require admin role, not password re-prove).
- **Carve-outs (must be commented):**
  - The token-driven recovery flows (`reset-password`,
    `confirm-email-change`, `verify-email`) are exempt because the
    one-shot token IS the proof-of-possession; the user clicking the
    link is the equivalent of re-prove.
  - Bearer-authenticated machine endpoints (currently only
    `submit_ingestion_batch`) skip CSRF because the long-lived API key
    is never browser-ambient.
- **Source:** FU-197 (2026-06-30). Promoted to a rule because the
  asymmetry between password-change and email-change shipped without
  triggering a review — the gap was invisible until a security pass
  spotted it. Codifying "both sensitive flows or neither" makes the
  next asymmetry impossible to ship silently.

### R-024 — Image upload UX goes through `ImageSourcePicker`
- **Rule:** Every site that lets the user upload an image renders its
  source-pick affordance via the shared
  [`web_app/src/components/ImageSourcePicker.vue`](../../web_app/src/components/ImageSourcePicker.vue)
  primitive. The picker owns the **Take photo / Choose image** split,
  the touch-device detection that decides whether to show the camera
  button, the hidden `<input type="file">` elements (with/without
  `capture="environment"`), and the call into `processImageFile` (R-003).
  Consumers receive a `ProcessedImage` (or an `error` message) and only
  decide what to do with the data URL. No bespoke `<input type="file">`
  or `<q-file>` in feature code.
- **Why:** The first cut of receipt-photo upload (FU-334) used a single
  `<input accept="image/*" capture="environment">`. That biased Android
  Chrome straight to the camera with no gallery option — exactly the
  opposite of "let me also pick a photo I already took". The audit that
  followed found three different upload shapes across the SPA
  (`ImageUploadField`, `RecipeStepImagesEditor`, `StoresSettings`,
  `ShoppingListDetail`), each making its own camera-vs-gallery choice
  silently. R-003 already centralised resize/encode; the *pick UX* needs
  the same chokepoint or the same bug appears N times.
- **Apply:**
  - New upload sites: drop `ImageSourcePicker` in directly, listen for
    `@pick="(image) => ..."` (a `ProcessedImage`) and `@error`.
  - Sites with chrome around the picker (preview + Remove button):
    compose `ImageUploadField` (which now delegates to the picker
    internally) rather than reinventing the wrapper.
  - Bulk-upload (recipe step images, receipt batches if it ever
    arrives) pass `multiple` — the picker emits one `pick` per file in
    order; coalesce in the parent if needed.
  - Don't pass `capture="environment"` on a bespoke input — that's the
    primitive's job and it varies by platform.
- **Violation signal:**
  - A new `<input type="file" accept="image/*">` in feature code.
  - A new `<q-file>` for image upload.
  - A handler that calls `processImageFile` directly from a bespoke
    `change` listener.
  - A site that has *only* a camera button or *only* a file button when
    both make sense.
- **Carve-outs (must be commented):**
  - `StoresSettings.vue` retains its `q-file` until FU-335 migrates it
    (drag-drop visual + clearable affordance need a measured swap).
- **Source:** FU-334 follow-on (2026-06-30). The single-`capture`
  receipt-upload button surfaced the gap; the standards rule turns the
  fix into a one-time decision.

### R-026 — Nav-state on list pages: persist within session, reset on full reload
- **Rule:** Any list page whose user has spent effort dialing in filters,
  search text, sort, or scroll position must preserve that shape when
  they navigate away (to a detail page, another route) and back within
  the same SPA session. A full browser reload should feel like a clean
  slate — no restored filters, no restored scroll. Persistence goes
  through the shared
  [`useListState(scope, factory)`](../../web_app/src/composables/useListState.ts)
  composable (module-level Map, gone on hard reload); scroll uses Vue
  Router's `savedPosition` via the app's `scrollBehavior`. No
  `localStorage`, no `sessionStorage`, no Pinia store slice for these
  refs.
- **Why:** Before A8 §3 the app was inconsistent — a couple of pages
  kept their state via ad-hoc mechanisms (product search URL, filter
  panel expanded), most didn't. Users reported the "click a stock item,
  hit back, lose your filters" tax. Full-reload persistence via
  `localStorage` was rejected because a stale filter that survives a
  browser restart traps users on an empty list they don't remember
  configuring; the session boundary is the honest one.
- **Apply:**
  - New list page: wrap filter / search / sort refs in a single
    `useListState('<page-key>', () => ({ ... }))` call and destructure.
    Non-persisted state (loading, in-flight fetches, hover, dialog
    open) stays as regular `ref()`.
  - Existing list page: migrate its refs into the composable using a
    stable scope key; keep the same defaults so first-visit UX doesn't
    shift.
  - Filter-composables that back multiple pages (`useStockFilters`)
    take an optional `persistScope` — callers pass their page key,
    the composable wires the refs through `useListState`.
  - The router's `scrollBehavior` already honours `savedPosition`; do
    NOT override per-page unless there's a genuine reason (e.g. the
    detail page anchors to a heading), and if so, document it inline.
- **Violation signal:**
  - A list page with `ref('')` search text bound to `v-model` and no
    `useListState` wrapper.
  - `sessionStorage`/`localStorage` used to persist a filter (except
    the FU-121 filter-panel-expanded preference, which is
    intentionally cross-session because it's a display preference
    rather than a filter value).
  - A per-page `scrollBehavior` override in `router/index.ts`.
- **Carve-outs (must be commented):**
  - `useFilterPanelExpanded` (FU-121) uses `localStorage` on purpose —
    it's an ambient display preference, not a filter value.
  - `useProductSearchUrl` mirrors state into the URL for
    deep-linking / share; that's a different contract and is
    intentionally not migrated.
- **Source:** A8 §3 landed 2026-07-01. Round-trip pattern established
  via `useStockFilters`, `RecipesOverview`, `MyProductsPage`; remaining
  list pages migrate opportunistically (tracked in `DORA_FOLLOWUPS`).

### R-027 — Styling encapsulation: component owns intrinsic appearance; parent owns layout context
- **Rule:** A shared component owns its **intrinsic appearance** — size,
  padding, border-radius, colours, hover, transitions, disabled-state
  styling — and callers must not re-declare or fudge them at the call
  site. The **parent** owns **layout context** — position in a flex row,
  spacing between siblings, alignment with surrounding chrome. A
  component **must not introduce a wrapper DOM element that fights the
  parent's layout scheme**. If a shared component renders multiple
  children (a paired button set, a label + control), the children
  render as top-level siblings via a Vue 3 multi-root template — never
  wrapped in an inner `<div>` that carries `q-gutter-*` or any other
  spacing scheme that collides with the parent container's own.
- **Why:** Two failure modes recur when the rule is broken.
  1. **Wrapper vs parent gutter collision.** Quasar's `q-gutter-*`
     classes are the negative-margin trick — the container gets
     `margin-top: -8px` and each direct child gets `margin-top: +8px`.
     If a component wraps its own children in a `<div class="row
     q-gutter-sm">` and that wrapper is placed inside a parent
     `q-gutter-sm` toolbar row, the wrapper receives `+8px` from
     outside AND `−8px` from its own inner gutter. Net displacement
     zero — but sibling `BaseButton`s (direct children of the outer
     row) only get the outer `+8px`, so they sit 8px lower than the
     wrapper. **This is the FilterToggleButton bug that surfaced
     2026-07-02.**
  2. **Call-site style fudge.** When the component underdelivers,
     each caller adds a `class="q-mt-xs"` or a `:style="{ marginTop:
     '-3px' }"` locally to nudge alignment. Every page drifts a
     different fudge. Consistency is destroyed silently.
- **Apply:**
  - Composite components (a Clear + Filters pair, a label + control,
    a search + action group) render children as top-level siblings.
    In Vue 3 the SFC `<template>` root can contain multiple nodes;
    use that instead of a wrapper `<div>`.
  - If a wrapper genuinely IS needed (e.g. the component needs a
    positioning context or a focus ring), it uses **flexbox `gap`**
    for inter-child spacing (`display: flex; gap: 8px`) — `gap`
    doesn't use margins, so there's no negative-margin dance to
    collide with the parent.
  - Callers do **not** re-declare intrinsic styling. If a caller
    wants to nudge alignment, the fix is in the component, not the
    caller.
  - Prefer a component prop over a call-site `class="..."` when the
    caller has a *legitimate* variant need (e.g. `size="sm"`).
    Variant proliferation is fine; call-site fudge is not.
- **Violation signal:**
  - A component's root is `<div class="row q-gutter-*">` wrapping
    other Base primitives, and it's meant to drop into a page toolbar.
  - A page toolbar contains a call-site inline `class` or `style`
    prop tweaking margin/padding/alignment of a shared button.
  - `git grep 'q-gutter' web_app/src/components/` returns shared
    components whose root wrapper carries a `q-gutter-*` class.
    Each hit is a candidate for the collision above; audit whether
    the component is used inside a parent that also carries a
    Quasar gutter class.
- **Carve-outs (must be commented, naming the rule):**
  - A component that is only ever used **standalone** (never dropped
    into a shared-gutter toolbar) may still use `q-gutter-*` — the
    collision only happens when it's a direct child of another
    `q-gutter-*` container. If you carve out, add an inline
    comment: `<!-- R-027 carve-out: only ever mounted at page root,
    no parent gutter -->` so a future author knows why the wrapper
    is safe there but not elsewhere.
- **Source:** ADR-023; FilterToggleButton misalignment surfaced
  2026-07-02 during a toolbar-parity review. The fix was a Vue 3
  multi-root template on FilterToggleButton itself; the rule was
  promoted because the same mistake is easy to make on any future
  paired-primitive component.

### R-028 — Domain inference = pure decision core + thin repo-gather
- **Rule:** A feature that *derives a domain judgement* (a verdict, a belief,
  a score, a prediction) splits into two pieces: a **pure function** that takes
  an already-gathered inputs dataclass and returns the result — no repository,
  no HTTP, no clock reads passed in as an arg — and a **thin gather layer**
  that does the repo access and calls the pure core. The endpoint calls the
  gather layer; unit tests call the pure core directly with fixture inputs.
- **Why:** Domain judgements are where the subtle rules live (cadence cuts,
  confidence decay, override precedence) and where regressions hide. A pure
  core is exhaustively unit-testable without a DB or Flask, so the rules get
  pinned cheaply; mixing repo access into the logic forces slow, brittle e2e
  setup for what is really arithmetic. It also keeps the judgement **server-
  owned** (R-003) with one obvious home.
- **Apply:** New derivation features follow `get_buy_verdict.compose_verdict`
  / `pantry_belief.compute_belief`: an `XInputs` dataclass, a pure
  `compute_x(inputs)`, a `gather_x_inputs(repo, …)` (batched — no N+1 for
  list overlays), and a `tests/test_x.py` that drives the pure fn with
  fixtures. Pass `today`/clock values *into* the inputs so time-dependent
  logic is deterministic in tests.
- **Violation signal:** a handler that queries the repo and computes the
  judgement inline; a domain-judgement test that needs the Flask test client
  or a seeded DB to assert a branch.
- **Carve-outs:** trivial one-line derivations don't need the split — the rule
  is for judgements with ≥2 interacting rules.
- **Source:** established from `get_buy_verdict` (P8-05) and re-applied in
  `pantry_belief` (P8-07); promoted 2026-07-03 (ADR-024) once the second use
  confirmed the pattern.

### R-029 — Respect the off-state: hide, don't nag
- **Rule:** When a user or the household admin has **disabled** an optional
  feature — via a per-user preference, a household `AppSetting` flag, or by
  never configuring the required backend (SMTP, VAPID, LLM, scanning, etc.) —
  its **entry points elsewhere in the app are hidden**, not shown-disabled with
  a "not set up" hint. Respect the off-state; don't advertise a capability the
  household has opted out of. The one place the disabled control legitimately
  appears is **the settings screen that owns its configuration** (Admin →
  System, Preferences, etc.) — that surface exists precisely to enable it.
- **Why:** A disabled-with-hint control everywhere the feature *would* attach
  is a nag: it takes up space and attention advertising something the user
  already said no to (or the household hasn't set up). The Dora product
  posture is calm, effortless, anti-nag — the settings screens are the front
  door for enabling features; the rest of the app respects the current state.
  This supersedes R-014 (reveal-and-disable), which optimised for discovery at
  the cost of nagging. It aligns with ADR-002 (a single flag, respected
  everywhere) and R-012 (working features stay visible — the inverse: *not-
  working / opted-out* features stay hidden).
- **Apply:** Gate the entry point on the same capability flag the functionality
  uses (`useFeatureFlags().hasEmail`, `useScanningEnabled()`, etc.) with `v-if`
  — not `:disable`. The settings screen that configures the feature still
  renders (that's where enabling happens); nowhere else advertises the
  unavailable state.
- **Violation signal:** a `:disable`d button with a "Set up X in Settings"
  tooltip appearing in a workflow surface (a builder, a dialog, a page action
  bar); a comment referencing R-014 on a gated entry point outside the
  feature's own settings screen.
- **Carve-outs (must be commented):** the settings screen that *owns* the
  feature's config obviously shows its own disabled state so it can be turned
  on. Calm empty-state placeholders (dashboard "all clear", empty-week banner,
  score-row explainer) are a different pattern — they're not gating a feature
  the user disabled, they're describing "no data yet". Those stay.
- **Source:** ADR-025; user directive 2026-07-06 walking back R-014 ("if a
  user has disabled something either personally or for the household it should
  not be in their face").

### R-030 — Operational config lives on `AppSetting`, not env
- **Rule:** Install-wide *operational* config — the values an admin would
  tweak after deploy without redeploying (SMTP host / password / port, VAPID
  keys, Piper paths, retention windows, feature toggles, public URL, etc.)
  — lives as columns on the singleton `AppSetting` row, edited from
  **Settings → Admin → System**. **Env vars are reserved for bootstrap**:
  values the app has to read before the DB is reachable (`DORA_SECRET_KEY`,
  `DORA_ENV`, `DORA_SPA_DIR`, storage-path overrides) or root wrapping keys
  the DB ciphertext depends on (`DORA_SECRET_ENCRYPTION_KEY`). Everything
  else — including secrets — belongs on the row, with real secrets stored
  as Fernet ciphertext wrapped by `DORA_SECRET_ENCRYPTION_KEY`.
- **Why:** Bootstrap-vs-runtime is the canonical split in every well-built
  self-hosted app (GitLab `gitlab.rb` vs application_settings; Discourse env
  vs site_settings; Mattermost `config.json` vs admin UI). Blurring it grows
  a long env-var table for operators and — on desktop — makes a
  double-click install untenable. Keeping this on `AppSetting` also honours
  R-005 (portable data access; the row travels with backups; a SaaS tenant
  gets one via the same code path). Real secrets on the row need the FU-153
  Fernet helper so a DB dump doesn't leak them — that's cheap given the
  helper already exists.
- **Apply:** New install-wide config gets an `AppSetting` column + a
  Settings → Admin → System page, not an env var. If the value is a
  bootstrap-time input (read before the DB) OR a wrapping key that decrypts
  the row itself, keep it env. If it's a runtime secret (an API key, an
  SMTP password) it goes on the row *encrypted*, with the response DTO
  surfacing a `<field>_configured: bool` instead of the ciphertext.
- **Violation signal:** a new `DORA_<X>` env read for something an admin
  would want to change post-deploy; a plaintext secret column on
  `AppSetting`; a settings page that reads env directly instead of the
  operational-config resolver.
- **Carve-outs (must be commented):** the seven bootstrap vars listed in
  ADR-026; a genuinely install-location value the desktop bootstrap
  detects at boot and *seeds into* the row (see `desktop_app._seed_desktop_paths`).
- **Source:** ADR-026; FU-333 close-out (2026-07-06) — Buckets B (12 vars),
  C (2 encrypted secrets), D (desktop first-run) shipped end-to-end. Env
  footprint went from 19 → 2 on server self-host and 0 on desktop.

### R-031 — Constructor injection via Protocols; no DI container
- **Rule:** Handlers (and other collaborators-owning classes) declare their
  dependencies as constructor parameters typed against **structural**
  Protocols in `dora_api/infrastructure/ports.py` — not against
  `I`-prefixed ABCs, not by resolving them from a container at call time.
  Wiring happens explicitly at the router / app-factory edge: `Handler(
  repository=SqlAlchemyRepository()).handle(...)`. No reflection-based
  auto-wiring. No `get_container().inject(X)`.
- **Why:** In Python, a Protocol + explicit constructor call gives you the
  entire testability + composability payoff of DI with a fraction of the
  ceremony a container brings. Handler tests substitute a fake by passing
  it to the constructor — no `patch.object`, no framework registration.
  A container earns its keep when you have deep dependency graphs,
  layered lifetimes, and many swappable implementations decided at boot;
  this app has none of that. The prior `dependency_injector`-based
  `DependencyContainer` was reflection over 175 handlers whose only real
  dependency was `SqlAlchemyRepository`, and the container was used as
  a service locator (`get_container().inject(X)`) rather than as real
  DI — a .NET habit imported where it doesn't fit. See ADR-027 for the
  full walk-back.
- **Apply:** New handler → `def __init__(self, repository: Repository) ->
  None: self.repository = repository`. New collaborator that's genuinely
  swappable (email transport, push transport, LLM client, clock, blob
  storage) → add a Protocol to `ports.py`, take it in the ctor, wire the
  concrete at the router or in the app factory. When a real swap surface
  arrives (auth per R-005, email transport, etc.), do it by adding a
  Protocol + a small wiring step in `create_app` — do not reintroduce a
  container.
- **Violation signal:** any new file importing a "container" or a
  registration API; any handler that constructs its own `SqlAlchemyRepository()`
  inside `__init__` instead of receiving one; any `I`-prefix nominal
  interface used as a DI seam.
- **Carve-outs (must be commented):** a handler that legitimately needs
  no repository (e.g. `AskAssistantHandler`, which builds an LLM client
  per-user from Flask session context) skips the parameter — that's
  fine, and the `__init__`'s absence is self-documenting. Never
  synthesise a fake ctor arg just for uniformity.
- **Source:** ADR-027; user directive 2026-07-08 ("is this app just not
  in need of DI, or is the code not written well enough to make use of
  it?") — resolved as "constructor injection yes, container no."

---

### R-032 — Never read a `lazy="noload"` relationship off an un-included load
- **Rule:** If code reads a relationship that is mapped `lazy="noload"`
  (the app's default for most FK relationships), the entity **must** have
  been loaded with that relationship `.include(...)`d on the *same* query.
  A plain `.by_id()` / `.all()` load followed by a relationship read returns
  `None`/empty **silently** — no error, just wrong data. Corollary: within
  one request, build any relationship-dependent map (cookability, expiring
  counts, etc.) *before* the plain id-universe load of the same entity, so
  the identity map doesn't hand back already-loaded noload-empty instances.
  When you only need the FK *value* (an id, for bucketing/comparison), read
  the underscore-prefixed FK property (`item._stock_group_id`) directly — no
  relationship load required — rather than `.include`-ing the whole object.
- **Why:** `noload` is a performance default (don't auto-fetch), but it turns
  every un-guarded relationship read into a silent correctness bug. This is
  the single most recurrent defect class in the codebase — six distinct
  production bugs in two weeks, all the same shape: cookbook filters no-op'd,
  the keeps-running-out report dropped items, stock-group counts read 0, and
  three PATCH bugs including **silent loss of every cook-mode ConsumptionEvent**.
  None raised; all shipped; all were caught by tests, not review.
- **Apply:** Reading `x.some_relationship`? Confirm the query that loaded `x`
  has `.include(SomeEntity.Fields.SOME_RELATIONSHIP)`. Only need its id? Read
  `x._some_fk_id`. Clearing an FK on a noload relationship? Write the
  underscore FK column directly (`x._cuisine_id = None`) — a relationship-side
  `= None` doesn't dirty the column. Add a query-count guard (FU-534) on hot
  read paths so an accidental per-row lazy load also fails loudly.
- **Violation signal:** any `.by_id(...)` / `.all(...)` immediately followed
  by a read of a relationship attribute on the result, without a matching
  `.include` on that same query; any relationship-side `= None` assignment
  used to clear an FK.
- **Source:** ADR-028; recurrent noload family (cookbook identity-map fix
  2026-07-10, FU-527, FU-533).

### R-033 — Entity-id path params use the `uuid` converter; handlers never receive an unvalidated `str` id
- **Rule:** Flask routes whose path param is an entity UUID declare it with
  the `uuid` converter — `@ROUTER.route("/<uuid:stock_item_id>")` — never the
  default string converter (`<stock_item_id>`). With the converter, Flask
  parses the segment to a real `uuid.UUID` before the handler runs and 404s a
  malformed value at routing time; the handler's `id: UUID` annotation is then
  honest. Without it the param arrives as a **`str`** despite the annotation,
  so `entity.id == param` silently fails, `dict[UUID]` lookups miss, and a
  non-UUID segment reaches a query and 500s.
- **Why:** Same root cause, many faces — this str/UUID mismatch produced the
  taxonomy delete-count-always-0 bugs, the product-unlink-always-404 bug, the
  rename-to-own-name-rejected bug at five surfaces, and **82 routes returning
  500 instead of 404** on a non-UUID path segment. The converter fixes the
  entire class at the routing edge and removes the need for per-handler
  `str(...)`/`UUID(...)` coercion workarounds.
- **Apply:** New route with an entity-id param → `<uuid:foo_id>`. The handler
  receives a `uuid.UUID`; compare/kick it around as one. Existing per-site
  `str(id)`/`UUID(str(id))` coercions added before this rule are harmless
  (defensive) and may be removed opportunistically once the route uses the
  converter. Path params that are legitimately **not** UUIDs (tokens, slugs,
  external codes) keep their appropriate converter — this rule is for entity
  ids only.
- **Violation signal:** a route decorator with a bare `<..._id>` segment that
  the handler treats as a UUID; any `str(entity.id) != path_param` workaround
  on a route that could instead use `<uuid:...>`.
- **Source:** ADR-029; str/UUID family (FU-528, FU-532).

### R-034 — The ORM model is the source of truth for the *whole* schema, indexes included; a migration is not a place to hold schema the model doesn't declare
- **Rule:** Every index, unique constraint, and FK covering index that exists in
  the production (migrated) schema must also be **declared in the ORM model**
  (`table_mappings.py`), so `create_all()` (dev + the e2e suite) builds the same
  schema `flask_migrate.upgrade()` builds. A migration adds the DDL to existing
  installs; it never *owns* a schema object the model is silent about. Foreign-key
  columns get a covering index by default (neither SQLite nor Postgres auto-indexes
  them — an unindexed FK full-scans the child table on a parent delete and leaves
  every join on that key unindexed).
- **Why:** For a long time every secondary index lived *only* in the Alembic chain
  and was never mirrored back, so dev + the entire e2e suite ran on a near-unindexed
  schema (1 index) that didn't match production (32) — behaviour depending on an
  index or a `UNIQUE` couldn't be exercised where the model didn't declare it, and
  42 FK columns were unindexed in prod (FU-393 sweep, Findings 1–2). Two build paths
  that disagree is drift by construction; the model being the single source of truth
  (R-003) has to include indexes, not just tables + columns.
- **Apply:** New index/unique/FK → declare it on the model (an `Index(...)` in
  `table_mappings.py`, or `index=True`/`unique=True` on the `Column`) **and** write
  the additive migration. Adding a table? Every FK column on it gets a covering index
  in the same change. The `test__migrations__migrated_schema_matches_orm_metadata`
  gate compares tables + columns + nullability + index/unique colsets + FK `ondelete`
  rules between the two build paths and fails on any undocumented difference; a
  genuinely-intentional divergence goes in that test's allowlist with an owner, never
  silently.
- **Violation signal:** an `op.create_index` in a migration with no matching
  `Index(...)`/`index=True` in `table_mappings.py`; a new FK column with no covering
  index; the schema-match test flipping red without an allowlist entry explaining why.
- **Source:** ADR-030; FU-563 (from the FU-393 data-model sanity sweep).

### R-035 — UI-affecting work is checked against the Design Style Guide (D-rules)
- **Rule:** Any task that adds or changes something a user sees is checked against
  `docs/01_charter/DESIGN_STYLE_GUIDE.md` exactly like the R-rules: fix, explain
  in place (`// D-00N carve-out: …`), or log a `DORA_FOLLOWUPS.md` finding. R-002
  owns the tokens-only *mechanics*; the Design Style Guide owns *usage* — which
  token, what size, how much space, what shape, and what the finished thing must
  look like. It is **prescriptive**: **Part A** (Foundations) maps every role to
  an exact token (colour/type/spacing/radius/elevation/border/icon/breakpoint),
  **Part B** gives per-component specs (buttons, chips, inputs, cards, list rows,
  dialogs, toasts, menus, empty states, skeletons, tables, the floating layer),
  and **Part C** is the enforceable checklist **D-001..D-019** (level-colour
  semantics, contrast floors, type floor, tap targets, icon naming, one
  date/number formatter, skeleton loading, dialog conventions, toast/floating
  placement, micro-feedback, page composition, data-density, state legends, copy
  voice, pattern reuse, full interactive-state coverage, snap-to-scale/no-off-token
  values, alignment/rhythm consistency, no transient-disable on focusable
  controls). When Part A/B states a value, use it
  exactly — an off-token literal is a carve-out, not a judgement call.
- **Why:** the 2026-07-18 UX audit (FU-578, 54 findings +
  `docs/05_investigations/UX_DESIGN_CRITIQUE_2026-07-18.md`) showed a strong
  token architecture leaking Quasar defaults and drifting per-surface (three
  date formats, casing drift, semantically-inverted level colours, sub-AA muted
  text) precisely because no usage-level rubric existed for the close-gate to
  check. Same failure mode ADR-001 fixed for engineering — rules that live only
  in finished audit docs get re-violated by the next session that never read them.
- **Apply:** existing-screen violations are backlog, not licence —
  `docs/04_proposals/DESIGN_REMEDIATION_PLAN.md` tracks them (DR-1..DR-16); new
  work complies from the start. New recurring design decisions get promoted to a
  new D-rule at close-gate, same lifecycle as R-rules/ADRs.
- **Violation signal:** off-scale spatial/type literals in a component
  (`padding: 5px`, `border-radius: 8px`, `font-size: 13px`, hand-mixed
  `box-shadow`) instead of `--space-*`/`--radius-*`/`--font-size-*`/`--elevation-*`
  (D-017); literal `ms` durations; `toLocaleDateString`/hand-formatted dates
  (D-006); "Loading…" strings instead of skeletons (D-007); default-caps `q-btn`
  in dialogs (D-008); icon-only buttons without `aria-label`+tooltip (D-005);
  `outline: none` without a replacement focus ring (A6/D-016); text on a `-soft`
  token using the soft (not full-strength) colour (A1/D-002); any new
  colour-to-meaning mapping not derived from the semantic/severity tokens.
- **Source:** ADR-031; FU-578 audit + owner directive 2026-07-18; strengthened to
  the prescriptive Part A/B spec 2026-07-19 (owner: "leave less guess-work").

---

### R-036 — A `MainLayout`-hosted route component roots on `<q-page>`; never hardcode the layout offset
- **Rule:** every route rendered inside `MainLayout`'s `<q-page-container>` roots on
  `<q-page>`, not a bare `<div>`. `<q-page>` is the only thing that gives a page a
  **height contract** — it sets `min-height: viewport − layoutOffset` from *live*
  layout state (header size, and a footer if one ever lands). Two shapes, pick by
  scroll model:
  - **Document-scroll page** (a growing list/grid; the window scrolls): bare
    `<q-page class="q-pa-md">`, no `:style-fn`. The default min-height is what makes
    a `position: sticky` footer (`PageCountsFooter`) pin to the viewport bottom even
    when the content is shorter than the viewport. **Reference: `RecipesOverview.vue`.**
  - **Fixed-height app-shell** (chrome + an internally-scrolling pane, e.g. a virtual
    list that caps its own height): `<q-page :style-fn>` returning
    `height: height === 0 ? calc(100vh − ${offset}px) : ${height − offset}px`.
    **Reference: `StockOverview.vue` (`pageStyleFn`).**
  Never hardcode the offset (`calc(100dvh − 64px)`, a magic `64`): it silently rots
  when chrome changes (e.g. `OfflineBanner` adds 48px when the API is unreachable) —
  take the live `offset` from `:style-fn`.
- **Why:** a bare-`<div>` page has no height contract, so anything height-dependent —
  a sticky footer, a fill-the-viewport shell, an internally-scrolling pane — must
  hand-roll the offset with a pixel guess that drifts from reality. This is exactly
  how the Stock Overview scroll/footer bugs happened (a self-capping virtual list
  defeated document scroll; the first patch hardcoded a 64px offset that was already
  wrong). At R-036's introduction only 10 of ~29 top-level pages used `<q-page>`.
- **Apply:** the initial `MainLayout` inventory is now **fully converted** (FU-609
  closed 2026-08-11) — new pages comply from the start. `pages/settings/*` mount inside
  `SettingsShell`'s own scroller (not the layout) and stay plain divs (`SettingsShell`
  itself is now `<q-page :style-fn>` with a `!important` mobile override back to
  window-scroll); auth/setup/error pages render outside `q-page-container` where
  `<q-page>` can't resolve a layout, so they're correctly exempt. `StockItemDetailPage`
  is dual-host (also embedded in the Stock Overview peek) — it roots on `<component :is>`
  that resolves to `QPage` when routed and a plain `<div>` when embedded, so it stays
  layout-agnostic in the peek. Shapes chosen: **document-scroll** (bare `<q-page>`) for
  Dashboard, Meal Plans, Meal-Plan Templates, Price History, Cook Mode, Reports, Shop-Now
  redirect, Stock Item detail; **app-shell** (`<q-page :style-fn>`) for the two runner
  shells (Meal Reconcile, Stocktake) + SettingsShell.
- **Violation signal:** a `<div class="q-pa-md">` (or any bare root) as the top
  element of a `pages/*.vue` routed under `MainLayout`; a `calc(100vh − <literal>px)`
  / `height: calc(100dvh − 64px)` in a page or shell; a `position: sticky` footer on
  a page with no `<q-page>` ancestor.
- **Source:** ADR-032; FU-609 (from the 2026-08-04 Stock Overview scroll-model
  rebuild); `RecipesOverview` converted as the document-scroll worked example 2026-08-11;
  the remaining 11-page inventory converted + FU-609 closed 2026-08-11.

### R-037 — `MainLayout`'s router-view transition is a plain cross-fade, never `mode="out-in"`
- **Rule:** the `<router-view>` inside `MainLayout` wraps its pages in a plain
  cross-fade transition (both the leaving and entering page animate at once). It must
  **not** use `<transition mode="out-in">` (nor a `<transition-group>` equivalent) once
  every route root is a `<q-page>` (R-036). `mode="out-in"` fully unmounts the old page
  before mounting the new one; combined with a `<q-page>` root that registers itself with
  the parent `QLayout` on mount, the swap can wedge and paint a **blank screen on
  navigation**.
- **Why:** `out-in` looks like the "clean swap" default (no visual overlap), so it's the
  intuitive thing a future dev re-adds. But `<q-page>` participates in the layout's
  height/offset contract at mount time; sequencing the unmount fully before the mount
  leaves a frame where no page is registered with the layout, and under real timing the
  new page's `<q-page>` failed to resolve its container and rendered nothing. This is the
  blank-nav regression that landed the moment R-036 made every page root a `<q-page>`.
- **Apply:** `MainLayout`'s router-view uses the default simultaneous cross-fade. If a
  page-swap animation ever needs reworking, keep it modeless; never reach for `out-in` on
  a layout that hosts `<q-page>` roots.
- **Violation signal:** `mode="out-in"` on the `<router-view>` transition in `MainLayout`
  (or any layout whose routes root on `<q-page>`); a blank content area after a nav that
  only recovers on reload.
- **Source:** ADR-033; the blank-screen-on-nav regression fix that followed the R-036
  rollout (FU-619, 2026-08-11).

---

### R-038 — Settings that operate over shared/household data live install-wide (AppSetting), not per-user
- **Rule:** a setting whose effect is computed over **shared/household data** — data that
  isn't scoped to a `user_id` (stock, shopping lists, recipes, meal plans) — belongs on the
  install-wide `AppSetting` singleton, not as a `User` column. If two members holding
  different values for the setting would produce a **contradictory or whose-value-wins**
  result over that shared data, it is a household concept and must be install-wide. Read it
  via `/api/health` (a `*_policy` block) so every client sees one answer; edit it via a
  dedicated endpoint (admin `PATCH /app-settings`, or an any-member endpoint when the
  setting is kitchen-setup-grade shared config).
- **Why:** the app is single-household; its domain data is shared. A per-user *behavioural*
  setting layered over shared data means the outcome depends on **who triggered the
  computation** — e.g. a per-user grocery budget compared against a spend total summed
  across every shared shopping list: "is the household over budget?" resolved differently
  per member, and (worse) a per-user budget silently changed what got written into the
  shared meal plan. This has now bitten three times (`household_headcount`,
  `batch_features_enabled`, `budget_amount`/`budget_period`) — each was put on `User` only
  as a convenient home and had to be relocated.
- **Apply:** before adding a `User` column, ask "does this change what the system computes
  or writes over shared data?" If yes → `AppSetting` + `/api/health` read. Reserve `User`
  for genuine **presentation / view / per-device / identity** preferences (theme, fonts,
  voice, image-display, dashboard layout, email-digest timing) — those legitimately differ
  per person and suppress only that person's own view, never mutating shared state.
- **Violation signal:** a `User` column read inside a handler that sums/derives/writes over
  a shared entity (no `user_id` filter); a "policy" value fetched from `currentUser` rather
  than `/api/health`; two members able to hold conflicting values for something that has one
  physical truth (the household's budget, headcount, cook-style).
- **Source:** ADR-034; the grocery-budget relocation (2026-08-12). Extends R-003
  (state ownership) and mirrors R-030 (operational config on `AppSetting`).

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
  **Presentation:** when the flag is off, entry points **hide** — this is the
  R-029 rule (ADR-025). The 2026-06-14 ADR-009 / R-014 "reveal-and-disable"
  detour that partially revisited this presentation was walked back on
  2026-07-06; ADR-002's original hide-when-off is the whole story again.
- **Promotes rule:** none (a pattern/recipe, not a new standing rule; R-003
  state-ownership already covers "server owns domain facts").
- **See also:** R-029 / ADR-025 (the presentation rule this ADR relies on).

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
- **Status:** superseded by ADR-025 (2026-07-06)
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

### ADR-014 — No magic: explicit, verbose, consistent
- **Date / task:** 2026-06-28 (user message promoting FU-084 from its
  original narrow scope into a top-line engineering value).
- **Status:** accepted
- **Context:** FU-084 originally proposed promoting the SQLAlchemy
  `lazy="selectin"` shortcut (added on `Recipe.cuisine`/`.category` so the
  ~10 read sites didn't each need an explicit `.include()`) into a
  standing rule for "small always-wanted lookups". The user pushed back
  on the *meta*-shape rather than the specifics: that kind of "this
  relationship loads itself, but only because we picked it; the others
  don't" is exactly the **magic** they want the codebase to avoid. They
  reframed it as a broader rule: prefer **verbose, explicit code** with
  **no guess-work**; reject "*most times it's done this way, but in
  these few places we decided to do it another way because it felt
  right*" inconsistency; explicitly cited C# AutoMapper as the
  archetypal misfeature.
- **Decision:** Adopt R-019. Explicit, verbose, locally-readable code
  beats clever / implicit / auto-discovered behaviour. When the codebase
  has an established pattern for a problem, *follow it* — don't introduce
  a parallel approach in one spot because the alternative looks tidier
  in isolation. Auto-mapping libraries (AutoMapper-shaped reflection
  between layers) are banned; mappers are hand-written, one named
  function per direction, every field listed. Decorator/metaclass magic
  that *mutates* behaviour stays in framework code, not feature code we
  own. SQLAlchemy relationship loading defaults stay codebase-wide
  (`noload`); per-entity `lazy="selectin"` overrides are themselves a
  flavour of magic (the read site no longer reflects what it loads) and
  should be retired in favour of explicit `.include()` / `selectinload()`
  at the call site. Existing per-entity `selectin` opt-ins from before
  this rule (`Recipe.cuisine`, `.category`) are grandfathered for
  R-007's scope-discipline reasons — flagged as a follow-up cleanup,
  not refactored this session.
- **Consequences:** New mapper code is more verbose (one named function
  per direction, every field listed) — that verbosity *is* the value:
  greppable, type-checked end-to-end, no silent breakage when a field
  is renamed three files away. New SQLAlchemy queries always declare
  what they load at the call site; the entity stays a passive shape.
  Reviewers can read a diff and check rule-fit with no convention to
  consult. Cost: short-term, more lines for hand-written mappers + a
  recurring nag against the temptation to reach for a "smart" decorator
  / convention / auto-loader.
- **Promotes rule:** R-019.

### ADR-018 — DnD reorderable lists go through `useDragDropList`
- **Date / task:** 2026-06-29 (FU-326 extraction).
- **Status:** accepted
- **Context:** Three reorderable-list surfaces in the web app
  (shopping-list lines [P6-01 Chunk 6], structured recipe steps
  [FU-094], recipe ingredients [FU-118]) had each grown its own
  hand-rolled HTML5 DnD plumbing: `dragLineId` / `draggingClientId` /
  `draggingIngredientClientId` refs that all meant the same thing;
  near-identical `@dragstart` / `@dragover` / `@dragleave` / `@drop`
  handlers; and three slightly-different CSS treatments for "source
  being dragged" (opacity 0.4 vs 0.5) and "active drop target"
  (outline-dashed vs box-shadow ring). The shape was always: guard
  the drag with a MIME token, light the drop target, dim the source,
  call a per-list "insert source at target's slot" effect on drop.
  Only two things genuinely differed: the drop-target predicate
  (anything / siblings-only / per-row guarded) and the per-drop
  effect (server reorder API / local reorder / local reorder +
  section reassignment). The shared surface area is exactly what
  an abstraction should own.
- **Decision:** Extract `web_app/src/composables/useDragDropList.ts`
  (state machine + per-row bindings) and `web_app/src/css/dnd.scss`
  (`.dora-dnd-row` / `--dragging` / `--drop-over` / `.dora-dnd-handle`).
  All three existing surfaces refactor onto it. New DnD lists go
  through it from day one. Two row shapes are supported:
  **handle mode** (small drag-grip icon is the only draggable
  element; row body keeps default cursor so inline editors stay
  interactive — used by both recipe editors) and **whole-row mode**
  (the whole row is grabbable — used by shopping-list lines where
  rows have no inline editors). The composable doesn't care which;
  it's a matter of where the consumer spreads `handleProps`.
- **Consequences:**
  - **Removed code** (~190 lines net): ~50-line drag block in
    `RecipeStepsEditor.vue` + ~50-line block in `RecipeStepRow.vue`,
    ~75-line block in `RecipeDetailPage.vue`, ~70-line block in
    `ShoppingListDetail.vue`, plus three near-duplicate CSS rule
    sets — replaced by one composable (~190 lines incl. JSDoc) and
    one shared stylesheet (~50 lines). The composable is bigger
    than any single removed block, but the *aggregate* shrinks and
    every future DnD surface is ~10 lines.
  - **Visual consistency**: source dim, drop-target ring, and
    handle treatment now identical app-wide (one shared `--motion-
    fast` transition, `--brand-primary` ring, 0.5 opacity). A user
    who learns one DnD list reads the next correctly.
  - **One MIME convention**: `application/x-dora-<thing>` enforced
    by the composable's `mime` option, so cross-list drops can
    never accidentally satisfy a dragover check.
  - **Plumbing cost**: the composable's `bind(item)` returns
    fresh closure objects on each call, so calling it 3× per row
    in a template (rowClass, rowProps, handleProps) re-allocates
    on every render. For the lists we have (10-50 rows) this is
    negligible; if a much larger DnD list ever ships, the obvious
    optimization is a memoizing wrapper keyed on the item id.
  - **Future**: multi-row drag, drop into off-row zones (e.g.
    "drop here to put into an empty section"), and keyboard
    reordering for accessibility are all extensions to this one
    composable rather than three parallel implementations.
- **Promotes rule:** R-022.

### ADR-019 — Test naming + shared response matchers
- **Date / task:** 2026-06-29 (FU-169 Phase 1 —
  `PROPOSAL_TEST_SUITE_IMPROVEMENTS.md` §C / §F).
- **Status:** accepted.
- **Context:** FU-166 spent days realigning ~40 inline RFC-7807
  problem-detail assertions across the router suite when the error
  contract moved (the same `assert resp.status_code == 400;
  assert resp.headers['Content-Type'] == 'application/problem+json';
  assert 'errors' in resp.json()` triplet, written out every time).
  The same audit found two naming conventions running in parallel —
  `test__get_x__Condition__Result` (older router tests) and
  `test_create_with_..._roundtrips` (newer suites) — which made the
  failure summary jagged and prevented uniform parametrize / grep
  patterns. Both are duplication-of-contract problems: the test
  suite is asserting the same shape (or naming the same thing) in
  many places, so a contract or convention move ripples through ~40
  files instead of one.
- **Decision:** Adopt **`assert_problem` + `assert_envelope`** in
  `tests/support.py` as the canonical matchers for the two repeated
  shapes; the proposal's §C names exactly these two. Adopt the
  behavioural naming convention
  `test__<unit>__<condition>__<result>` for new tests, with a
  per-edit migration policy for existing names (don't open a
  rename-all PR; rename when you're already editing the file).
  Codified as R-023.
- **Consequences:**
  - **Future contract moves are a one-file fix.** When the
    problem-detail shape changes again, `assert_problem` is the
    single update site; ditto for the list envelope.
  - **Per-edit migration** keeps the rename cost amortised — every
    PR that touches a test brings it into line, no big-bang
    cleanup needed.
  - The shared matchers add ~80 lines to `tests/support.py`; this
    pays back the moment more than ~6 callers exist, which is
    already true.
  - **Doesn't ban inline assertions in non-router tests.** Domain
    unit tests assert plain objects; the matchers are for the
    HTTP-contract surfaces only.
- **Promotes rule:** R-023.

### ADR-016 — Calendar-day boundaries run in the household timezone
- **Date / task:** 2026-06-29 (FU-174 close-out sweep; mechanism shipped
  with C-2.K on 2026-06-14).
- **Status:** accepted
- **Context:** Python's `date.today()` returns the server-local date.
  For a self-hostable household app (R-005 distribution posture), the
  server can be anywhere — a managed deploy in Frankfurt with a
  Sydney household crosses midnight by 9–11 hours, and every
  "expiring today" / "next 7 days" / "scheduled for today" decision
  silently desyncs ±1 day. The meal-plan past-day-drop bug (F29 from
  the feedback round) was the surface — fixed locally in C-2.K with
  `AppSetting.timezone` (IANA string), `clock.resolve_timezone`, and
  `household_today(repository)`. The FU-174 audit found 15+ other
  `date.today()` sites in alerts / dashboard / suggestions /
  assistant tools / budget / waste / location attention / shopping
  lists / recipes / stock items, each one a latent F29-shape bug.
- **Decision:** Adopt R-021. `clock.household_today(repository)` is
  the single entry point for "what calendar day is it". Every
  feature handler that gates on "today" uses it; `date.today()` is
  reserved for seeds/fixtures. Wall-clock events keep
  `datetime.now(UTC)` (different concern: when, not which day).
  Storage stays mixed by intent — `DateTime(timezone=True)` for
  events, `Date` for calendar values — and the boundary check is
  where the timezone lives, not the value.
- **Consequences:** Every new feature with a date boundary now
  has one canonical path and reviewers have a one-line grep target
  (`date.today()` in feature code = violation). The household
  timezone lives in one column, set once per install; changing it
  cascades through the app correctly. Cost: handlers that compute
  "today" must take a repository argument so the helper can read
  `AppSetting`. The few that didn't have one already (a handful in
  budget / waste / location attention) gain one — minor plumbing.
  The client is intentionally not authoritative: it reads
  `mealPlanStore.todayIso` (or the equivalent server-fetched
  boundary); any client-side "today" computation is a display
  fallback, never a decision.
- **Promotes rule:** R-021.

### ADR-015 — Deferred-save surfaces must wire the unsaved-changes guard
- **Date / task:** 2026-06-29 (FU-098 close-out sweep).
- **Status:** accepted
- **Context:** `useUnsavedChangesGuard` shipped on 2026-06-12 (FU-156)
  after the user repro'd silently-discarded recipe edits — root cause
  was a per-handler `onBack` confirm that didn't fire on sidebar
  navigation. The composable wraps `onBeforeRouteLeave` +
  `onBeforeRouteUpdate` + `beforeunload` and was wired into
  `RecipeDetailPage` + `StockItemDetailPage` at that time. FU-098 then
  asked for the broader sweep. The audit found exactly two additional
  pages that fit the shape (account settings, install AI-config
  settings) and ~22 surfaces that *looked* like candidates but
  legitimately don't need the guard (save-on-blur settings, dialog
  Saves, cook-mode session state, etc.). The recurrence — two
  separate "we built another deferred-save page and forgot the
  guard" events six weeks apart — is the rule-worthy signal: without
  a standing rule, the audit will need to run again every time
  another draft-state page lands.
- **Decision:** Adopt R-020. Every page with a dedicated Save action
  and locally-mutable draft state wires `useUnsavedChangesGuard` with
  a dirty predicate derived from the same `unchanged` / `isDirty`
  computed that gates the Save button itself. The four exclusion
  categories (inline-save, real-time session, dialog-only, password
  fields) are documented in the rule so future audits can ratify or
  reject quickly. No reinvention of the discard-prompt copy or the
  route-level wiring — both live in the composable.
- **Consequences:** New editor pages cost one additional one-line
  call (`useUnsavedChangesGuard(...)`) plus the dirty-predicate
  expression they already need for the Save button's `:disable`.
  Reviewers can grep for "Save" + missing `useUnsavedChangesGuard` to
  catch the violation in a diff. The rule's exclusion list doubles
  as an audit checklist — re-running the FU-098 sweep on a new
  candidate page is now a five-minute "which category does this fit?"
  check, not a 30-minute file-by-file read.
- **Promotes rule:** R-020.

### ADR-020 — One image-source picker for the SPA (Take photo / Choose image)
- **Date / task:** 2026-06-30 (FU-334 follow-on).
- **Status:** accepted
- **Context:** The first cut of receipt-photo upload for shopping lists
  used a single `<input accept="image/*" capture="environment">` button.
  On Android Chrome that biases straight to the rear camera with no
  gallery option, defeating the common "let me pick a receipt photo my
  partner already took" path. An audit of the existing image-upload
  surfaces (recipe hero, recipe step images, stock item image, user
  avatar, store logo, product image, recipes detail) found three
  different upload shapes: `ImageUploadField` (4 consumers), a bespoke
  `<input>` in `RecipeStepImagesEditor`, and a Quasar `q-file` in
  `StoresSettings` — each made its own camera-vs-gallery choice
  silently, and none offered both consistently. R-003 already pinned the
  resize/encode chokepoint at `processImageFile`; the *pick UX* was the
  matching gap.
- **Decision:** Adopt R-024. A single SPA-wide
  `ImageSourcePicker.vue` primitive renders the two-affordance
  picker (Take photo + Choose image), detects touch-primary devices via
  `pointer: coarse` to decide whether to surface the camera button, owns
  the hidden inputs (one with `capture="environment"`, one without), and
  calls `processImageFile` internally. Consumers receive a
  `ProcessedImage` via `@pick`. `ImageUploadField` composes the
  primitive internally so its 4 existing consumers (stock item, recipe
  edit, recipe detail, user avatar) gain the camera affordance with no
  per-site change. `RecipeStepImagesEditor` and the new receipts UI use
  the primitive directly.
- **Consequences:** Camera-vs-gallery becomes one platform-aware
  decision instead of N per-site decisions. The "Take photo" button
  appears only where it makes sense (mobile / touch tablet), so desktop
  isn't cluttered with a no-op control. Multi-file flows compose the
  primitive with `multiple` — each file emits its own `pick` in order;
  the parent decides batching. Cost: one indirection layer; the
  primitive is ~100 lines and small enough to read end-to-end. The
  scanning case (iOS Files → Scan Documents) reaches users via the
  Choose-image path on iOS — no dedicated scan button needed.
  `StoresSettings.q-file` stays as a single carve-out tracked under
  FU-335.
- **Promotes rule:** R-024.

### ADR-021 — Session-mutating auth writes need password re-proof + CSRF
- **Date / task:** 2026-06-30 (FU-197).
- **Status:** accepted
- **Context:** A senior security review flagged two coupled gaps in the
  authentication surface that, together, formed a full account-takeover
  chain: (a) `request_email_change` required no `current_password`
  proof (asymmetric with `change_password`, which did) and (b) no CSRF
  defence existed at all (`SameSite=Lax` alone, no token / Origin
  check). Investigation surfaced a third gap: the SPA's
  Settings → Email "Save" actually called `PATCH /auth/me` with
  `{"email": …}`, which the backend silently accepted — the verified
  flow at `POST /auth/me/email` existed but was never reached. Three
  asymmetries (between flows, between defences, between intended and
  actual code paths) compounding.
- **Decision:** Adopt **R-025**. Close every asymmetry at once: remove
  `email` from `UpdateMeRequest` (`extra="forbid"` then rejects the
  legacy path with 400); require `current_password` on `ChangeEmailRequest`
  and verify in the handler; notify the **old** address before issuing
  the confirmation token to the new one; introduce double-submit CSRF
  in `dora_api/infrastructure/csrf.py` + `middleware.py` (cookie
  auto-issued on every response without one, header required on every
  mutating call against a non-public, non-bearer endpoint, constant-time
  compare). SPA axios interceptor reads the cookie and attaches the
  header. Public endpoints (login/register/forgot/reset/verify/
  bootstrap) are exempt so a cold client can authenticate; bearer-auth
  `submit_ingestion_batch` exempt because Bearer tokens aren't
  browser-ambient. Dev-only `DORA_CSRF_DISABLED=1` escape hatch refuses
  to weaken production. Test conftest mirrors the axios interceptor so
  the existing suite stays transparent; explicit CSRF tests bypass that
  helper by passing `X-CSRF-Token: ""` to confirm the gate fires.
- **Consequences:**
  - Every future auth-identity write (password, email, recovery
    channel, API key) is now expected to ship both halves of R-025.
    Asymmetry between sensitive flows becomes a violation rather than
    a judgement call.
  - SPA `requestEmailChangeAsync(newEmail, currentPassword)` signature is
    a breaking change for any caller — currently only `AccountSettings.vue`.
  - The `dora_csrf` cookie's `httponly=False` is deliberate; the
    defence relies on the SPA reading it. A future XSS would still let
    an attacker read the token (the defence stops cross-site, not
    in-page-script attacks). XSS-hardening is its own sweep (FU-196
    security-headers / CSP item) — R-025 doesn't claim to fix that.
  - `PUBLIC_ENDPOINTS` and `CSRF_EXEMPT_ENDPOINTS` are now load-bearing
    lists; additions need a written rationale (R-025 violation signal).
- **Promotes rule:** R-025.

### ADR-022 — Nav-state on list pages: session-scoped, no full-reload persistence
- **Date:** 2026-07-01
- **Context:** A8 §3 called for one consistent rule for filter / search /
  sort / scroll on list pages. Before this, the app was inconsistent
  (some pages persisted via URL, most reset on every mount). The
  question was persist-across-reload (localStorage) vs
  persist-within-session (in-memory) vs always-reset.
- **Decision:** Persist within the SPA session, reset on full reload.
  Filters/search/sort go through a module-level Map keyed by page
  scope (`useListState`). Scroll goes through the router's
  `savedPosition`. Neither uses `localStorage` or `sessionStorage`.
- **Alternatives considered:**
  - **localStorage-backed persistence across reloads.** Rejected: a
    stale filter that survives a browser restart traps users on a
    filter set they don't remember configuring; the session boundary
    is honest.
  - **Vue Router `<keep-alive>` on list routes.** Rejected: caches
    every route indefinitely (memory spike), and re-mount-on-visit
    is what stores rely on for fresh data.
  - **Pinia store slice per list page.** Rejected as over-engineered
    for what is view-only state; stores own domain data, not
    per-page UI knobs.
- **Consequences:**
  - New primitive `useListState` is now the standard for list-page
    view state; two existing patterns (`useFilterPanelExpanded`,
    `useProductSearchUrl`) survive as explicit carve-outs with
    different contracts.
  - Remaining list pages (MealPlansOverview, ShoppingListsOverview,
    Stocktake, settings-list surfaces) migrate opportunistically;
    tracked as an open follow-up.
  - Sign-out should call `clearAllListState()` when it's wired, so a
    second user on a shared device doesn't inherit the previous
    user's filter shape. Currently a full reload happens on sign-out
    anyway, so this is a nice-to-have rather than a defect.
- **Promotes rule:** R-026.

### ADR-023 — Styling encapsulation: component owns intrinsic appearance; parent owns layout context
- **Date / task:** 2026-07-02 (toolbar-parity review — user spotted the Filters button sitting 8px above its BaseButton siblings on Stock Overview).
- **Status:** accepted
- **Context:** The Filters button and the other toolbar buttons (New item / Scan / Stocktake / Bulk select / Export) all share the same base (`BaseButton`). But the Filters button visually sat higher than the rest. Root cause was not the base component — it was the `FilterToggleButton` wrapper: `<div class="row items-center q-gutter-sm no-wrap">` around the (Clear + Filters) pair. `q-gutter-*` is Quasar's negative-margin trick (`margin-top: -8px` on the container, `+8px` on each direct child). When the wrapper sat inside the parent toolbar's own `q-gutter-sm`, it received `+8px` from the parent AND applied `-8px` to itself internally — net displacement zero. Sibling `BaseButton`s that were direct children of the outer container only got the outer `+8px`, so they sat 8px lower than the wrapper. Every other composite component that wraps children in its own `q-gutter-*` `<div>` has the same latent bug — the failure mode isn't specific to FilterToggleButton, it's a class of collision.
- **Decision:** Adopt R-027. Component owns intrinsic appearance (size / padding / border / colour / hover); parent owns layout context (position in a flex row, spacing between siblings). A composite component that renders multiple children uses a **Vue 3 multi-root template** so the children participate directly in the parent's layout — no wrapper `<div>` that carries a spacing scheme colliding with the parent. Where a wrapper is genuinely needed, it uses flexbox `gap` (no negative-margin trick) so it can't collide. Callers never re-declare intrinsic styling or fudge alignment with call-site `class="q-mt-xs"` — the fix is in the component.
- **Alternatives considered:**
  - **Fix the specific FilterToggleButton bug and log the general lesson as an FU.** Rejected — the class of collision recurs anywhere a shared component wraps children in a gutter-carrying div, and the R-001 componentisation rule doesn't cover it explicitly. Promoting to a rule now means it's on the close-gate checklist for every future paired-primitive component.
  - **Wrap children in a `<div style="display: flex; gap: 8px">`.** Valid alternative for the specific fix and worked as a fallback. Rejected as the *primary* pattern because it introduces an extra DOM node with no semantic purpose; the multi-root template is one less element and clearer intent.
  - **Push the Clear button up to the caller.** Rejected — Clear and Filters are logically paired (they appear/disappear together as a unit; FU-121 encoded that pairing). Splitting them means every caller re-implements the appear/disappear + ordering rules.
- **Consequences:**
  - The `q-gutter-*` negative-margin scheme is now considered *hazardous inside shared components*. Toolbar rows on pages can still use it freely — the hazard is only when a *component wraps children* in it.
  - Existing paired-button components get an audit: `git grep 'q-gutter' web_app/src/components/` surfaces candidates. Each hit is checked against "is this component ever mounted inside a parent that also carries a Quasar gutter class?" — if yes, migrate to multi-root or `gap`.
  - The rule extends R-001 (componentise first) — R-001 said *create the primitive*; R-027 adds *and don't sabotage it with wrapper DOM that fights the caller's layout*.
- **Promotes rule:** R-027.

### ADR-024 — Domain inference = pure decision core + thin repo-gather
- **Date / task:** 2026-07-03 (P8-07 Zero-Input Pantry belief service).
- **Status:** accepted
- **Context:** P8-07 needed a per-item belief (band + confidence + reason) derived from four interacting signals (intake, cadence, cooking, time decay) with subtle rules — override precedence, confidence decay, coarse-band cuts. This is the same *shape* as the P8-05 buy-verdict, which had already split into a pure `compose_verdict(_AxisInputs)` + a thin `_gather_inputs` repo walk, and whose rules are pinned by `tests/test_buy_verdict.py` with zero DB. Building the belief the same way (pure `compute_belief(BeliefInputs)` + `gather_beliefs_for_items`) meant the tricky logic got a fast fixture-driven unit suite (`tests/test_pantry_belief.py`) while the repo access stayed a thin, separately-verified layer. Two independent uses of the pattern = the "don't do it twice differently" bar.
- **Decision:** Adopt R-028. Domain-judgement features split into a pure function over an inputs dataclass (no repo / HTTP / ambient clock) + a thin gather layer that the endpoint calls; tests drive the pure core with fixtures. Time values are passed *into* the inputs for determinism. Keeps the judgement server-owned (R-003) with one testable home.
- **Alternatives considered:**
  - **Compute inline in the endpoint handler.** Rejected — forces slow, brittle e2e setup to exercise arithmetic branches, and buries the domain rules in repo plumbing.
  - **Leave it as a one-off (don't promote).** Rejected — two independent uses (buy_verdict, pantry_belief) is exactly when a pattern should become a rule so the next derivation feature (e.g. P8-08 Dora Score) follows it by default rather than re-discovering it.
- **Consequences:**
  - P8-08 Dora Score and any future prediction/score feature start from this shape.
  - The gather layer must still batch for list overlays (no N+1) — called out in R-028's Apply.
- **Promotes rule:** R-028.

### ADR-025 — Respect the off-state: hide disabled/unconfigured features outside their own settings screen
- **Date / task:** 2026-07-06 (user directive walking back R-014).
- **Status:** accepted; supersedes ADR-009
- **Context:** ADR-009 / R-014 (2026-06-14) established "reveal-and-disable" — showing gated feature entry points as visible-disabled with a "not set up" hint, so users would discover capabilities. In practice this reads as nagging: a disabled Email button sitting in the meal-plan builder for a household that has no SMTP configured, a scanning button greyed-out for a household where the admin turned it off, etc. The user's directive is unambiguous — "if a user has disabled something (either personally or for the household) it should not be in their face". This applies whether the off-state is an explicit toggle (`scanning_enabled=false`), a per-user preference, or an unconfigured backend (SMTP/VAPID/LLM never set up = the household implicitly opted out).
- **Decision:** Adopt R-029. Gate optional-feature entry points with `v-if` on the same capability flag the functionality uses; hide them when off. The settings screen that owns the config still renders the disabled control (that's where enabling happens). Calm empty-state placeholders ("no data yet") are a different pattern and stay.
- **Alternatives considered:**
  - **Keep R-014 with per-surface judgement.** Rejected — the user explicitly wants the principle inverted, not softened. "Show disabled everywhere" was the wrong default.
  - **Split "explicitly disabled" vs "never configured".** Rejected — the household not setting up SMTP *is* an opt-out; treating unconfigured as "discoverable-nag" is exactly what the user is walking back. One consistent rule.
- **Consequences:**
  - The FU-176 sweep flips direction: any place currently rendering a disabled-with-hint gated control outside its config screen becomes a `v-if` hide. A fresh follow-up ([[FU-500]]) tracks the inverse sweep — most visibly the scanning button, the meal-plan builder Email button (C-2.J), and the notification/push/LLM controls that appear outside their settings screen.
  - ADR-002's original hide-when-off presentation is restored — it no longer needs the "R-014 revisits it" note.
  - Empty-state usages (dashboard "all clear", meal-plan empty week, `DoraScoreCard` explainer) are unaffected — they're a distinct pattern that some code comments mislabelled as R-014. They stay; the R-014 comment references on those sites can be re-labelled opportunistically.
- **Promotes rule:** R-029.
- **Supersedes:** ADR-009 (R-014).

### ADR-026 — Operational config lives on `AppSetting`, not env
- **Date / task:** 2026-07-06 (FU-333 close-out — Buckets B + C + D shipped end-to-end).
- **Status:** accepted
- **Context:** Dora accumulated 19 `DORA_*` env vars at boot — every optional feature (SMTP, VAPID, TTS, audit retention, public URL, etc.) added one or more. Operators self-hosting had to configure a long environment table before the app was useful; desktop end-users would never see one at all. The FU-333 audit split the vars into three buckets — Bucket A (7 vars, genuine bootstrap: read before the DB or root wrapping keys), Bucket B (12 operational vars — SMTP host/port/username/from/use-TLS, VAPID public+subject, Piper paths, email_enabled, audit_retention_days, public_url), Bucket C (2 real secrets — SMTP password, VAPID private key). Bucket B shipped 2026-07-05 as `AppSetting` columns with an env-fallback lane. This ADR closes out Buckets C + D and drops the fallback (pre-release; no operators to preserve — user directive 2026-07-06).
- **Decision:** Adopt **R-030**. `AppSetting` is the single source of truth for install-wide operational config; env vars are reserved for the 7 bootstrap values and the wrapping key (`DORA_SECRET_ENCRYPTION_KEY`). Real secrets live on the row *encrypted-at-rest* with the FU-153 Fernet helper. The response DTO surfaces a `<field>_configured: bool` for every secret; ciphertext never leaves the DB. Desktop bundles auto-generate the two remaining bootstrap keys on first launch (Bucket D), so end-users see no env var at all.
- **Alternatives considered:**
  - **Keep the Bucket-B env fallbacks for one release.** Rejected — pre-release, no operators to preserve. Fallback code is dead weight and hides the strict-AppSetting contract from future readers.
  - **Store SMTP password + VAPID private key in a JSON keychain file.** Rejected — makes backups + Postgres migrations harder (a second data location); doesn't compose with SaaS's shared-DB story. `AppSetting` + Fernet is the same pattern per-user LLM keys already use.
  - **Auto-generate `DORA_SECRET_ENCRYPTION_KEY` on server self-host too.** Rejected for the server path — operators want an explicit "I made a choice" signal about the wrapping key (matches the FU-153 rationale). Desktop is the odd one out because the "operator" *is* the end user.
- **Consequences:**
  - Env footprint: 19 → **2** on server self-host (`DORA_SECRET_KEY` + `DORA_SECRET_ENCRYPTION_KEY`); **0** on desktop bundles. The `.env.example` block for the promoted vars is gone.
  - New pattern for any future "where should this config live?" call: default to `AppSetting` unless it's read pre-DB or is a wrapping key.
  - Rotating `DORA_SECRET_ENCRYPTION_KEY` invalidates the two operational secrets + every per-user LLM API key; the resolver degrades to dry-run (with a warning log) rather than crashing. Admin re-enters secrets in Settings — documented in `key_encryption.py` and `.env.example`.
  - Desktop bundle: `desktop_app._detect_bundled_piper_paths()` + `_seed_desktop_paths()` write detected `piper_bin` / `piper_bundled_voice_dir` into the row *post-init*; no env fallback path to lose in the resolver.
- **Promotes rule:** R-030.

### ADR-027 — Constructor injection via Protocols; no DI container
- **Date / task:** 2026-07-08 (rip-out of the `dependency_injector`-based `DependencyContainer`).
- **Status:** accepted
- **Context:** The codebase had a `DependencyContainer` (a ~215-line wrapper around `dependency_injector.containers.DynamicContainer`) that auto-registered every `*Handler` under `dora_api/features/` via reflection, then routers resolved handlers with `get_container().inject(FooHandler)` at 200+ callsites. An audit found: **175 of 179 handlers** just constructed `self.repository = SqlAlchemyRepository()` in `__init__` — no injected params, no interfaces exercised, no lifetime rules beyond `Factory`. The container's own example lines for interface-based registration (`IRepository[Merchant]`, `IConfigurationManager`) were commented out. Zero tests used the container. In practice it was a fancy service-locator around a zero-arg constructor call, plus a boot-time reflection surface that spawned its own hardening FU ([[FU-457]] — boot-time resolved-route assertion). The whole shape (`I`-prefix nominal interfaces, generic-alias name mangling, `SqlAlchemyGateway[T]`) read as C#/.NET conventions ported into a language that doesn't need them.
- **Decision:** Adopt **R-031**. Delete the container; delete `service_wiring.py`; delete the `get_container()` accessor; remove `dependency_injector` from requirements. Introduce `dora_api/infrastructure/ports.py` with a `Repository` Protocol (structural typing — any object with the right method surface satisfies it, no ABC inheritance). Rewrite every handler `__init__(self)` → `__init__(self, repository: Repository)`. Rewrite every `get_container().inject(X)` callsite → `X(SqlAlchemyRepository())`. Three handlers that legitimately don't need a repository (`RestoreBackupHandler`, `InspectSpreadsheetHandler`, `GetShortfallHandler`) stay parameter-less; `AskAssistantHandler` remains as the "no repo, per-user LLM client" carve-out it already was.
- **Alternatives considered:**
  - **Keep the container, add the boot-time assertion FU-457 wants.** Rejected — the assertion protects a reflection surface we can just delete. Cheaper to remove the fragility than to shore it up.
  - **Handler ctor with `repository: Repository | None = None` defaulting to `SqlAlchemyRepository()`.** Rejected — pragmatic but dishonest. Hides the dependency and lets callers keep the old service-locator habit indefinitely. Force the caller to pass it.
  - **Move to `I`-prefix ABCs + a hand-rolled DI without the container.** Rejected — `typing.Protocol` is the Python-native, structural way to say "this shape". Any nominal hierarchy is unnecessary ceremony.
- **Consequences:**
  - `-215` LOC (`dependency_container.py`), `-21` LOC (`service_wiring.py`), `-1` runtime dep (`dependency_injector`). ~200 callsites became a direct constructor call.
  - Testability payoff realised immediately — 3 tests that previously did `patch.object(handler, "repository", stub)` now pass the stub through the constructor and are 3-5 lines shorter each.
  - **FU-457 dissolved by construction.** No reflection-based handler-wiring surface left to protect. Router discovery (`get_attributes_ending_with('router', ...)`) is a separate reflection surface; if it needs the same boot-time assertion, that's a much smaller FU to reopen.
  - The 4 files in `dora_api/features/data/` that didn't already import `SqlAlchemyRepository` got the import added.
  - When a genuine swap surface arrives (R-005 auth interface; email transport per FU-500 sweep; push transport; LLM client per-tenant), the pattern is: **add a Protocol to `ports.py`, take it in the ctor, wire the concrete at the router edge or on `app.services` in `create_app`.** No container.
  - The .NET-flavoured naming (`I`-prefix generic interfaces, `SqlAlchemyGateway[T]`) is now discouraged for new work — this ADR is the reference for "why we don't do that here."
- **Promotes rule:** R-031.

### ADR-028 — Reading a `noload` relationship without including it is a silent-correctness bug; make it a rule
- **Date / task:** 2026-07-12 (test-suite hardening passes; user confirmed promotion)
- **Status:** accepted
- **Context:** Six distinct production bugs in two weeks shared one root cause:
  code loaded an entity (plain `.by_id()`/`.all()`), then read a `lazy="noload"`
  relationship off it, which returns `None`/empty **silently**. Instances:
  cookbook `?cookable`/`?expiring` filters were no-ops (identity-map poisoning);
  the keeps-running-out report dropped history-less items (FU-527); stock-group
  `item_count` was always 0 (FU-527); PATCH appended phantom stock-level history,
  lost every cook-mode `ConsumptionEvent`, and no-op'd recipe FK null-clears
  (FU-533). None raised an error; all were caught by tests, never by review.
  FU-527's original note set the trigger "one more incident → promote a rule";
  it fired repeatedly.
- **Decision:** Promote **R-032**. Every read of a `noload` relationship must
  sit behind an `.include` on the same query; relationship-dependent maps load
  before any plain entity load in the same request; read the underscore FK
  property when only the id is needed; clear FKs by writing the underscore
  column, not a relationship-side `= None`.
- **Consequences:** New relationship reads carry an explicit `.include`
  (marginally more verbose, always correct). Pairs with the FU-534 query-count
  guards, which catch the inverse failure (an accidental per-row lazy load).
  Does **not** mandate changing the `noload` default itself — that's a
  deliberate perf posture; the rule governs how you *read* under it.
- **Promotes rule:** R-032.

### ADR-029 — Entity-id path params use Flask's `uuid` converter
- **Date / task:** 2026-07-12 (test-suite hardening passes; user confirmed promotion)
- **Status:** accepted
- **Context:** Routes declared entity-id params with the default string
  converter (`<stock_item_id>`) while handlers annotated them `UUID`. Flask
  delivers a `str`, so `entity.id == param` silently failed and UUID-keyed
  dict lookups missed — producing the taxonomy delete-count-always-0 bugs, the
  product-unlink-always-404 bug, and the rename-to-own-name-rejected bug across
  five surfaces (all FU-528). Worse, a non-UUID segment flowed into a UUID query
  and 500'd — **82 routes** return 500 instead of 404 on garbage input (FU-532).
  The handler-level instances were fixed with per-site `str(...)` coercion, but
  that papers over the class.
- **Decision:** Promote **R-033**. Entity-id path params use `<uuid:id>`; Flask
  parses to `uuid.UUID` and 404s malformed values at routing time before the
  handler runs. This fixes the whole class at the edge and lets the per-site
  coercion workarounds be retired.
- **Consequences:** FU-532 becomes a mechanical sweep of route decorators
  (`<foo_id>` → `<uuid:foo_id>`) for the entity-id routes, verified by the
  existing `test_api_fuzz.py` path-param pin flipping from xfail to pass.
  Non-UUID path params (tokens, slugs) are explicitly out of scope. Handlers
  now receive a real `UUID`, so defensive coercions become no-ops (harmless;
  removable opportunistically).
- **Promotes rule:** R-033.

### ADR-030 — The ORM model owns the whole schema (indexes included); reconcile the model↔migration drift and gate it with a schema-match test
- **Date / task:** 2026-07-15 (FU-563, from the FU-393 data-model sanity sweep)
- **Status:** accepted
- **Context:** `table_mappings.py` declared almost no secondary indexes — 1, vs
  the 32 the Alembic chain builds. Every other index (and 4 unique constraints)
  lived only in migrations, so `create_all()` (dev + the whole e2e suite) built a
  near-unindexed schema that didn't match production, and behaviour depending on an
  index/UNIQUE couldn't be exercised where the model was silent. Separately, 43 FK
  columns had no covering index in prod (parent-delete full-scans + unindexed joins).
  The guard that should have caught it — `test__migrations__migrated_schema_matches_orm_metadata`
  — only compared table *names*, so all of it passed CI blind.
- **Decision:** Promote **R-034**. The model is the single source of truth for the
  entire schema, indexes and unique constraints included; FK columns are indexed by
  default. Mirrored all 32 pre-existing prod indexes/uniques into `table_mappings.py`
  (names copied from the migrations so autogenerate stays a no-op on them), added the
  43 FK covering indexes to both the model and one additive forward-only migration
  (`b9d4f2a7c3e1`), and rewrote the schema-match test to compare tables + columns +
  nullability + index/unique colsets with a small documented allowlist.
- **Consequences:** dev/test now build the same schema as prod (drift went from 31
  missing indexes + 4 missing uniques to zero). The additive index migration is
  portable (pure `CREATE INDEX`, no table rewrite — SQLite + Postgres, R-005/R-006).
  Two classes of drift needing risky batch table rebuilds were split off from this
  additive change and finished in follow-on migrations the same day: the 4 nullability
  drifts (3 `Product` cols reconciled + the `User.username` deferral documented —
  **FU-564**, migration `c1e8a5f3d9b2`) and the 6 FK `ondelete` mismatches (model
  declares CASCADE/SET NULL/RESTRICT, prod had none — **FU-565**, migration
  `d3f8b1a6c4e2`). The schema-match gate was extended each time (it now also compares
  nullability + FK `ondelete`), so the whole FU-393 sweep is closed and every class it
  found is now enforced, not just detected. Batch-mode fragility (this repo's
  double-render trap) was navigated with `batch.f(...)`-wrapped constraint names; the
  rebuilds preserved all other FKs + the covering indexes.
- **Promotes rule:** R-034.

### ADR-031 — Adopt a Design Style Guide (D-rules) as a standing usage rubric beside the R-rules
- **Date / task:** 2026-07-18 (owner directive after the FU-578 UX audit + design critique)
- **Status:** accepted
- **Context:** Seven real-pixel UX passes (FU-578, 54 findings;
  `docs/05_investigations/UX_DESIGN_CRITIQUE_2026-07-18.md`) found the token/theme
  architecture strong but per-surface execution drifting: three simultaneous date
  formats, dialog-casing drift (Quasar uppercase defaults), a semantically inverted
  stock-level colour scale (Out = grey reading calmer than Low = red), sub-AA muted
  text in light mode, unlabelled icon-only controls, and inconsistent loading
  treatments. R-002 policed token *mechanics* but nothing policed token *usage*, so
  each surface re-decided visual questions locally — the exact rules-only-in-
  finished-docs failure ADR-001 fixed for engineering.
- **Decision:** Author `docs/01_charter/DESIGN_STYLE_GUIDE.md` (D-001..D-015) as the
  authoritative look-and-feel rubric — colour semantics, contrast floors, type/tap
  minimums, icon naming/metaphors, single format authority, loading/skeleton rules,
  dialog/toast conventions, motion usage, composition, legends, copy voice, pattern
  reuse — and promote **R-035** so UI-affecting tasks check D-rules at the same
  close-gate as R-rules (fix / explain-in-place / log). Existing violations are
  backlog in `docs/04_proposals/DESIGN_REMEDIATION_PLAN.md` (DR-1..DR-16), not
  licence to copy. D-rules share the R-rule lifecycle (propose at close-gate).
- **Consequences:** UI diffs carry a second, cheap rubric check; design decisions
  get recorded as D-rules instead of re-argued per surface; the remediation plan
  gives the backlog a home so new work is never blocked on old debt. Rules out
  surface-local conventions (per-page date formats, ad-hoc status colours) without
  a commented carve-out.
- **Promotes rule:** R-035.

### ADR-032 — A `MainLayout`-hosted route roots on `<q-page>` for the layout height contract; never hardcode the offset
- **Date / task:** 2026-08-11 (FU-609, from the 2026-08-04 Stock Overview scroll-model rebuild)
- **Status:** accepted
- **Context:** `<q-page>` is the only element that gives a routed page a height
  contract — `min-height: viewport − layoutOffset`, computed from live layout state.
  Only 10 of ~29 top-level pages used it; the rest rooted on a bare `<div>` and, when
  they needed a height (sticky footer, fill-the-viewport shell, internal scroll),
  hand-rolled the offset with a hardcoded pixel guess. That guess rots: the Stock
  Overview rebuild found a magic `64px` that was already wrong when `OfflineBanner`
  adds 48px. `RecipesOverview` shares Stock Overview's `PageCountsFooter` but as a
  bare div, so its footer floats mid-screen on a short list (no min-height to pin to).
- **Decision:** Promote **R-036**. A `MainLayout`-hosted route roots on `<q-page>`;
  document-scroll pages use a bare `<q-page>` (default min-height pins the sticky
  footer), fixed-height app-shells use `<q-page :style-fn>` reading the live `offset`;
  never hardcode the offset. Converted `RecipesOverview` to a bare `<q-page>` as the
  document-scroll worked example (StockOverview is the app-shell reference). The
  remaining pages are **opportunistic per-page conversions**, not a blind sweep — the
  inventory + per-page notes stay in FU-609; several need a document-scroll-vs-shell
  call and `SettingsShell`'s own hardcoded offset is a separate fix.
- **Consequences:** the sticky-footer-on-short-content bug is fixed on the one page
  that shared Stock Overview's footer, and the pattern is now enforced at the
  close-gate so new pages don't reintroduce bare-div roots or magic offsets — without
  taking on the regression risk of converting 11 unreported surfaces at once.
- **Promotes rule:** R-036.

### ADR-033 — Page-root route transitions cross-fade, never `mode="out-in"` (paired with ADR-032/R-036)
- **Date / task:** 2026-08-11 (FU-619, blank-screen-on-nav regression that followed the R-036 rollout)
- **Status:** accepted
- **Context:** the moment R-036 (ADR-032) made every `MainLayout` route root a
  `<q-page>`, navigation started painting a **blank screen** — the content area went
  empty and only recovered on a reload. Root cause: `MainLayout`'s router-view wrapped
  its pages in `<FadeTransition mode="out-in">`. `out-in` fully unmounts the leaving page
  before mounting the entering one; a `<q-page>` registers with its parent `QLayout` at
  mount, so sequencing the unmount fully ahead of the mount left a frame with no page
  registered, and the new `<q-page>` failed to resolve its container and rendered nothing.
  Dropping `out-in` (plain simultaneous cross-fade) fixed it. This is a recurring-shaped
  trap: `out-in` is the intuitive "clean swap" default a future dev will re-add, and it
  only breaks in combination with `<q-page>` roots — exactly the combination R-036 now
  mandates everywhere.
- **Decision:** Promote **R-037**. `MainLayout`'s router-view transition stays a modeless
  cross-fade; never use `mode="out-in"` (or a `transition-group` equivalent) on a layout
  whose routes root on `<q-page>`.
- **Consequences:** the blank-nav regression can't be reintroduced silently — the rule
  names the exact anti-pattern and its violation signal, so a future transition rework is
  steered away from `out-in`. Pairs with ADR-032: R-036 forces `<q-page>` roots, R-037
  guards the one page-swap footgun that mandate created.
- **Promotes rule:** R-037.

---

### ADR-034 — The grocery budget is a household concept: install-wide, not per-user (promotes R-038)
- **Date / task:** 2026-08-12 (owner call on Settings → Money; "the budget affects everyone via the shopping list — why is it on the user row?")
- **Status:** accepted
- **Context:** the grocery `budget_amount` / `budget_period` lived on `User`, but the
  budget engine sums "spent" across **every shared shopping list** in the period (the
  schema is single-household; `budget.period_spent` even carried the comment *"Not
  per-user because the schema is single-household"*). So the household spend total was
  compared against whichever member's personal budget row happened to be loaded, and the
  meal-plan auto-build / swap-defence read the *triggering* user's budget to decide the cap
  applied to the **shared** week — "is the week over budget?" depended on who pressed the
  button, and a per-user budget silently changed what got written into shared data. This is
  the exact shape FU-615 already fixed twice (`household_headcount`, `batch_features_enabled`
  moved User → AppSetting: "a household has one headcount, not one per person"). The
  per-user `money_features_enabled` opt-in was removed in the same pass (owner: money is
  "kitchen setup, not personal" — one install flag, no per-user layer).
- **Decision:** Move `budget_amount` / `budget_period` to `AppSetting`; surface via
  `/api/health.budget_policy`; edit via a new **any-authenticated-member**
  `PATCH /api/budget/settings` (kitchen-setup-grade shared config, same access class as
  shared stores/locations — the first non-admin write to an `AppSetting` field, deliberately
  so). Value-driven: amount null/0 ⇒ off (no separate enabled flag — which also removed the
  "toggle on with no amount, change period, toggle flips off" bug, since there was no longer
  a derived-enabled state to stomp). Promote the general lesson to **R-038**.
- **Consequences:** the household budget now has one physical truth; meal-plan budget-defence
  and the dashboard read the same shared value regardless of which member is signed in.
  Establishes that AppSetting can carry an any-member-editable field (not only admin config).
  Pre-release hard migration — the three `User` columns dropped, no data preserved.
- **Promotes rule:** R-038.

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
