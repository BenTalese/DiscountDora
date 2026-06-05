# Codex session instructions — DiscountDora / Dashy Dora

The repo is being finished against the planning library at `docs/` inside this
repo. Multiple Codex sessions may be working on this concurrently from
different computers — because `docs/` is versioned with the code, every
machine has the same copy automatically.

To keep handoffs clean:

## On session start — ALWAYS

1. **Read the last entry in `DORA_WORKLOG.md`** (at this repo's root). It tells
   you what was just done, what decisions were made, and what's next. If the
   last entry says "Next up: X", that's your starting point unless the user
   redirects.
2. **Planning docs live at `docs/` in this repo.** Entry points:
   `docs/00_DOCS_INDEX.md`, `docs/RECONCILED_FINISHING_PLAN.md`,
   `docs/STATUS.md`, `docs/prompts/00_INDEX.md`. Read from there directly —
   don't search the filesystem and don't reconstruct from memory. If a path a
   prompt references is genuinely missing under `docs/`, ask the user.
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

The master is `docs/RECONCILED_FINISHING_PLAN.md`. It owns order
and scope. Inside it:

- **§5** — phased plan (Phase 0 foundations → Phase 1 loop → Phase 2 ingestion
  API → Phase 3 champion → Phase 4 commercialize).
- **§7** — resolved decisions. Scraper → standalone companion; recipe
  comparison gets INV-6'd before keep/cut; nutrition off+simple only;
  gamification → someday.

The **Dora Decision Charter** (12 principles, tiebreak: Effortless + Anti-creep)
lives in `docs/DASHY_DORA_CHAMPION_PLAN.md` Part II. Every design call is
checked against it.

The executable prompts live in `docs/prompts/`. Each one is self-contained —
read its "Impact & decisions" block first, resolve any choices with the user,
then run it. After running, log it.

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

## Don'ts

- Don't rewrite the framework. Stay on Flask / Quasar / Vue 3.
- Don't add features beyond the prompt's scope, even if adjacent code looks
  rough. Log it as a finding in `DORA_FOLLOWUPS.md` instead (with a state and a
  recommended resolution point).
- Don't silently skip the worklog entry at end of work, even for tiny tasks.
  The whole point is that the *other* agent can pick up cold.
