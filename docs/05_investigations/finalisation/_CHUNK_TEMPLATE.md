# Finalisation — per-chunk analysis template (Stage 1)

Governing plan: [`docs/01_charter/FINALISATION_PLAN.md`](../../01_charter/FINALISATION_PLAN.md).
Register: [`docs/01_charter/FINALISATION_COVERAGE.md`](../../01_charter/FINALISATION_COVERAGE.md).

One file per chunk in this folder: `CHUNK_NN_<slug>.md`. The four master
documents the plan names (`FULL_SYSTEMS_TEST.md`, `FINALISATION_REVIEW.md`,
`TEST_PLAN_INVENTORY.md`, and the help-content record) are **assembled from
these chunk files** — so the section headings below are a contract. Use them
verbatim, in this order, at these heading levels.

## Ground rules for the analyst

1. **Stage 1 changes no code.** Not a rename, not a comment, not a test. The
   deliverable is this file. (If you find a verified bug, write it up in §C1
   and §E; the orchestrator opens the FU — do **not** edit `DORA_FOLLOWUPS.md`
   yourself, several analysts run at once and ids would collide.)
2. **Read the code, file by file.** Backend feature(s) first, then SPA
   pages/components/composables/stores, then tests. List every file you opened
   in §0 — that list is the evidence the walk happened. Grep every entry point
   (router registration, store usage, component imports) rather than assuming.
3. **Execution-ready or it doesn't count.** Every §C finding records the exact
   `path:line` (or line range) and the exact change, so Stage 2 can apply it
   without re-reading. "Consider tidying X" is not a finding.
4. **Evidence for dead code.** A "dead / unused" claim must quote the grep you
   ran (pattern + the fact it returned only the definition). Check `web_app/src`,
   `web_app/test`, `dora_api`, `tests`, `scripts`, and `docs/03_prompts` is *not*
   evidence of use.
5. **Don't re-raise what's already tracked.** `DORA_FOLLOWUPS.md` holds ~215
   open items; grep it for the surface before writing. If a finding is already
   an FU, reference the id (`tracked: FU-NNN`) instead of restating it, and
   still give it a Stage-2 verdict if it's in the maintainability class.
6. **Owner context (2026-10-22).** The owner has walked every page as product
   owner and is ≥90 % happy with the app *as it is*. So: no redesigns, no
   "this feature should work differently". §C executes the maintainability
   class (DRY / dead code / componentisation / placement / naming / efficiency
   / standards) and verified bugs. Anything design-level goes to §C8 and stops
   there.
7. **Test stance (owner, 2026-07-20) — lean, manual-first.** §D lists tests
   only where they pin a *stable, low-churn contract* that is expensive to
   re-check by hand. Backend pytest and Vitest only. **No Playwright
   feature-flow specs** — the e2e layer is a 3-spec smoke layer and stays so.
   The "must-write-before-ship" bucket is expected to be tiny.
8. **Charter tie-breaks** (Effortless + Anti-creep) and `ENGINEERING_STANDARDS.md`
   (`R-001..R-096`) are the rubric. Cite rule ids. For library-vs-hand-rolled,
   "keep" is a legitimate verdict — don't default to "replace".
9. Don't run the full test suites in Stage 1 (the orchestrator holds the
   baseline). Running one targeted test file to confirm a bug is fine.

---

# Chunk NN — <name>

**Analysed:** YYYY-MM-DD · **Analyst session:** finalisation overnight run
**Scope (from PLAN §4):** <one line>
**Boundaries:** <what neighbouring chunks own that this one deliberately skips>

## 0. Reading list + files walked

**Planning docs consulted:** bullet list (proposal / impl plan / investigation /
feedback section / open FUs on this surface).

**Files walked (every file opened, with line count):**

| File | Lines | Role |
|---|---|---|
| `dora_api/features/<x>/<y>.py` | 123 | handler — … |

## A. Full Systems Test — <surface>

### A1. Preconditions
### A2. Golden path
Numbered steps, each `→ expected`. Name the persona.
### A3. Edge cases
One bullet per edge (empty state, validation, permission, offline mid-write,
session expiry, feature flag off …).
### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓/– | … |
### A5. Load-bearing conditions
Which of: Android PWA · native Capacitor · desktop installer · iOS PWA ·
bad network/offline · 360×640 · 1920+ · all themes × light/dark ·
reduced-motion/high-contrast — and *why* for each ticked.
### A6. Release-gate rows
The 1–4 rows from this surface that belong on the launch tollgate.

## B. Help content — <surface>

### B1. Current help audit
What `HelpPage.vue` `GUIDES`, the `(?)` `HelpHint` chips, `DoraHelpPage.vue`,
and `dora_api/features/assistant/app_knowledge.py` `APP_OVERVIEW` currently say
about this surface; which lines are stale/wrong (quote + path:line).

### B2. Help entries (one per feature / auto-behaviour)
For each, the §3.2 shape:

#### <Entry title — this is the HelpPage entry title>
- **Group:** <HelpPage GUIDES group title — existing or proposed new>
- **What it does:** one plain sentence.
- **When it fires / how to trigger it:**
- **What controls it:** exact `/settings/...` path (or "always on — no setting", stated honestly).
- **What it costs / might get wrong:**
- **Related:** other entry titles.
- **Chip:** where a `<HelpHint topic="<title>">` belongs (`path:line`) or "none".
- **Source:** MAGIC_BEHAVIOUR_AUDIT F-row / proposal § / code path.

### B3. DoraBot corpus delta
Exact replacement text for the `APP_OVERVIEW` lines about this surface.

## C. Senior review — <surface>

Finding id format: `NN-Rk` (chunk-number dash R-k). Every finding has:
`class` · `where` (path:line) · `what's wrong` · `exact change` ·
`blast radius` (S/M/L) · `test guard` (existing test file, or "none — run X") ·
`Stage-2 verdict` (**execute** / **FU** / **waive** + reason) · `tracked:` FU id if any.

### C1. Bugs (verified or high-confidence latent)
### C2. Redundancy / DRY (R-001, R-003)
### C3. Dead code / unused fields / unread endpoints
### C4. Componentisation opportunities (R-001)
### C5. Placement / layering (R-003, R-005)
### C6. Naming & idiom
### C7. Efficiency
### C8. Design-level findings — out of Stage-2 scope
(Record and stop. These become proposals/FUs only if the owner wants them.)
### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict (keep / replace / wrap) | Effort / risk | Note |
### C10. Standards drift (R-0NN)
### C11. Ride-along signals for FU-010 / FU-224 (theme / colour)

## D. Test plan — <surface>

| Test | Layer (pytest / vitest) | Priority (must-write-before-ship / nice-to-have) | Trigger to write it |
|---|---|---|---|

## E. Proposed follow-ups (orchestrator allocates ids)

One bullet per item that needs a `DORA_FOLLOWUPS.md` entry, in the ledger's
own shape (type · what · why deferred · recommended resolution). Verified bugs
first, marked **urgent**.

## F. Summary for the register

- FST rows: n · Help entries: n (new n / reworded n) · Review findings: n
  (execute n / FU n / waive n) · Tests: n (must-write n) · Bugs: n
- One-line "what came out of it".
