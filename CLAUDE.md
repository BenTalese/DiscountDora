# Claude session instructions — DiscountDora / Dashy Dora

The repo is being finished against the planning library at `docs/` inside this
repo. Multiple Claude sessions may be working on this concurrently from
different computers — because `docs/` is versioned with the code, every
machine has the same copy automatically.

To keep handoffs clean:

## On session start — ALWAYS

1. **Read the last entry in `DORA_WORKLOG.md`** (at this repo's root). It tells
   you what was just done, what decisions were made, and what's next. If the
   last entry says "Next up: X", that's your starting point unless the user
   redirects.
2. **Planning docs live at `docs/` in this repo, organised by lifecycle.**
   Entry points:
   - `docs/00_DOCS_INDEX.md` — top-level navigation.
   - `docs/01_charter/` — vision + governance
     (`DASHY_DORA_CHAMPION_PLAN.md`, `RECONCILED_FINISHING_PLAN.md`,
     `STATUS.md`).
   - `docs/02_feedback/` — user input (source of truth):
     `Feedback _ Fixes - as of [DATE].md`, `FEEDBACK_TRIAGE_AND_PLAN.md`,
     `COVERAGE_GAPS.md`.
   - `docs/03_prompts/` — executable prompts (`00_INDEX.md` +
     `A*.md` / `B*.md` / `C_*.md` / `INV_*.md`).
   - `docs/04_proposals/` — outputs of Wave-C design briefs (no-code
     design docs).
   - `docs/05_investigations/` — outputs of INV prompts + ad-hoc audits.
   - `docs/06_legacy_prompt_plans/` — original `PROMPT_PLAN_PART_*`
     (historical reference; the active set lives in `03_prompts/`).
   - `docs/00_original_spec/` — the author's **very first spec** (Feature
     Boards + ~125 "I can …" Feature Notes + original PROMPT_PLAN), written
     *before* this branch's ~100k LOC. **Historical, NOT authoritative** — it
     pre-dates the charter/feedback, so where it disagrees, those win; it never
     auto-overrides. Mine it for dropped intent, half-built features, or a
     cleaner original framing — see the cross-check rule below.
   - `docs/99_scratch/` — raw notes awaiting triage.

   Read from there directly — don't search the filesystem and don't
   reconstruct from memory. If a path a prompt references is genuinely
   missing under `docs/`, ask the user.
3. **Verify state before acting.** The planning docs (esp. `STATUS.md`) are
   known stale; the code is the source of truth. Read the actual code paths
   the prompt references before assuming they exist.
4. **Read `CHANGELOG.md`** for the most recent product-level changes — context
   for what the code looks like now vs. what older docs describe.
5. **Scan `DORA_FOLLOWUPS.md` for `[OPEN]` items.** This is the stateful backlog
   of deferred jobs, leftovers, and findings from past prompts — the things the
   user may have missed in a long session summary. Surface the open items whose
   *recommended resolution point* is "now" or matches the work you're about to
   start, then **ask the user whether they want to review/resolve those now or
   defer them** before you dive into the main task. Don't silently work around an
   open item that's relevant to what you're doing.

## On ending a work unit — ALWAYS

Append a new entry to `DORA_WORKLOG.md` using the template at the top of that
file. Do this even if the unit was partial or blocked — the next session needs
to know where you stopped and why.

**Also update `DORA_FOLLOWUPS.md`** with anything the current job spun off:
follow-ups, deferred jobs, leftovers, or findings worth investigating later. The
user may not catch these from the response alone, so they must live somewhere
durable and stateful. For each new note record its **state** (`[OPEN]` /
`[RESOLVED]`) and a **recommended resolution point** (e.g. "now", "later during
Phase X / prompt Y", "when <trigger>", or "opportunistic"). If you actually
resolved an existing item this session, flip it to `[RESOLVED]` with a one-line
note on how — don't delete it; the trail matters. If the unit produced no new
loops and resolved none, that's fine — no edit needed.

**MANDATORY — reported defects you conclude are "non-issues" still get a
follow-up.** When a prompt (or the user) reports a bug and your investigation
finds it *doesn't reproduce / already fixed / can't be found in the code*, you
must NOT silently drop it. The report came from real usage; a static code read
is not proof it's fixed (it may fail only at runtime, on a specific path, or you
may have misread). Log it as `[OPEN]` with type `finding`, note that it didn't
reproduce in a static read, and set the recommended resolution to **"confirm in
browser"**. Only flip it to `[RESOLVED]` once it's actually been verified
not-broken in the running app. This applies per-defect — don't bury several
reported items as one vague "all fine" note.

Three logs, three purposes — keep them separate:
- **`CHANGELOG.md`** = product/code changes (user-visible, "the app now does
  X"). Updated per the master plan's rule that every prompt updates it.
- **`DORA_WORKLOG.md`** = process/handoff log (which prompt ran, decisions
  made, what's next, open questions). Internal — for agent-to-agent handoff.
- **`DORA_FOLLOWUPS.md`** = stateful backlog of open loops (deferred work,
  leftovers, findings) that outlive a single session. Each item carries a state
  and a recommended resolution point. The session-start scan reads from here.

## Governing documents (read on demand, not every session)

All paths below are *inside* `docs/` in this repo.

The master is `docs/01_charter/RECONCILED_FINISHING_PLAN.md`. It owns
order and scope. Inside it:

- **§5** — phased plan (Phase 0 foundations → Phase 1 loop → Phase 2 ingestion
  API → Phase 3 champion → Phase 4 commercialize).
- **§7** — resolved decisions. Scraper → standalone companion; recipe
  comparison gets INV-6'd before keep/cut; nutrition off+simple only;
  gamification → someday.

The **Dora Decision Charter** (12 principles, tiebreak: Effortless + Anti-creep)
lives in `docs/01_charter/DASHY_DORA_CHAMPION_PLAN.md` Part II. Every
design call is checked against it.

The executable prompts live in `docs/03_prompts/`. Each one is
self-contained — read its "Impact & decisions" block first, resolve any
choices with the user, then run it. After running, log it.

## Cross-checking against the original feedback — MANDATORY

Every design brief, proposal, assessment, or implementation plan that
targets a specific app surface (Wave-C briefs, INV reports,
implementation plans, design proposals) **MUST end with a flat coverage
table** mapping each feedback bullet for that surface — from
`docs/02_feedback/Feedback _ Fixes - as of [DATE].md` — to a section in
the proposal, OR explicitly mark it out-of-scope with a one-line reason.

A reviewer should be able to audit "is anything missing?" at a glance.
The `F1..F49` table at the end of
`docs/04_proposals/PROPOSAL_MEAL_PLANS.md` is the reference shape.

For cross-cutting work (Wave A) rather than per-surface, the table maps
each feedback bullet that motivated the work — not every bullet across
the app.

A proposal without this table is incomplete. Open
`docs/02_feedback/COVERAGE_GAPS.md` after writing one to flip any
bullets that now have a home from gap → covered.

## Consulting the original spec — for briefs/investigations

When a brief, proposal, or investigation targets a specific surface, **also skim
the matching Feature Board / Feature Notes under `docs/00_original_spec/`** for
that surface (it's the author's first spec, pre-~100k-LOC). It is **historical
and non-authoritative** — the charter, reconciled plan, and current feedback
override it, and it never silently changes a decision. Use it only to *extract*
dropped intent, half-built features, or a cleaner original framing. When you do
pull something in, add it to the doc in its own clearly-labelled section, tagged
**keep / consider / superseded**, noting how old the source is. The reference
shape is `PROPOSAL_CART_BUTTON.md §9` ("From the original spec"). If nothing
there is worth extracting, that's fine — no section needed.

## Removed features — do not reintroduce

- Substitute **graph** — the standalone visual graph *page* (the old N7
  `/substitutes` route / `SubstitutesGraph.vue`). That page is deleted; don't
  rebuild it. **NOT removed:** the basic per-stock-item substitutes — the
  substitutes list on a stock item's detail page, surfaced in recipes and as a
  *temporary, cook-session-only* swap in cook mode (B8). Keep those. (The old
  docs conflated the two by writing "Substitute graph (stock-item substitutes)";
  they are different things.)
- Stock map / spatial layout. Locations is a simple tree, never spatial.
- Product / real-world barcodes for deal lookup (P6-02). Dora's own per-item
  QR labels are kept but off by default.
- Central retailer scraping as a hosted service (P7-01). It survives only as
  a self-hosted, off-by-default module / the standalone companion.

## Naming

The code still reads "DiscountDora" until P8-01 lands. That's expected — the
rename to "Dashy Dora" is itself a planned prompt, not a drift to fix
piecemeal.

## State-ownership principle (check new work against it)

**Server owns derived domain facts and cross-entity aggregates; the client owns
presentation and ephemeral view state. No domain constant or threshold lives in
two languages.** A client computing a cross-entity rule (e.g. "cookable"), summing
across a fetched collection, or hardcoding a domain constant (a stock-level name, a
"7-day" window) is a smell — push it to the server, don't copy it a fourth time.
The full triage + app-wide audit is in
`docs/04_proposals/STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` (§8 addendum); but the
"already clean — do not relocate" list there is equally binding (don't
over-correct fine client display math into the API).

## Distribution & tenancy posture (check new work against it)

The product is built the **GitLab way: one codebase, SaaS-style, self-hostable** —
the *same artifact* runs as a self-hosted single instance, a managed single-tenant
instance (Path B), or a multi-tenant SaaS (Path A, deferred). SaaS and self-host are
**not conflicting architectures**; only deployment/tenancy/managed-conveniences
differ. Don't dig a self-hosted-only hole, and don't pre-build multi-tenancy. Run
the **§7.5 distribution-posture checklist** in
`docs/01_charter/RECONCILED_FINISHING_PLAN.md` (repository-routed data access;
**Postgres is the standard datastore target, SQLite still supported** for lightweight
self-host, so keep the DB layer portable both ways; env/config-driven differences;
auth behind an interface with a local default; no speculative `tenant_id`; managed
conveniences degrade gracefully) on any prompt touching data access, auth, config, or
deployment. Full rationale: that doc's **Decision 5** (§7). Postgres migration is
tracked as `DORA_FOLLOWUPS.md` FU-045.

## Don'ts

- Don't rewrite the framework. Stay on Flask / Quasar / Vue 3.
- Don't add features beyond the prompt's scope, even if adjacent code looks
  rough. Log it as a finding in `DORA_FOLLOWUPS.md` instead (with a state and a
  recommended resolution point).
- Don't silently skip the worklog entry at end of work, even for tiny tasks.
  The whole point is that the *other* agent can pick up cold.
