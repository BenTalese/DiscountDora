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
