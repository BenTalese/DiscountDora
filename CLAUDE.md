# Claude session instructions — DiscountDora / Dashy Dora

The repo is being finished against a planning library ("DORA DOCS") that lives
*outside* the repo on the user's local machine. Multiple Claude sessions may be
working on this concurrently from different computers, so the docs path is not
fixed.

**On the primary workstation** the docs are at `/home/benny/Downloads/DORA DOCS/`.
On other machines (or if that directory is missing), **ask the user where the
docs are** before proceeding — do not guess, do not search the filesystem, and
do not try to work from memory of the docs. If the user can't provide them in
this session, say so in your worklog entry and stop rather than improvising.

To keep handoffs clean:

## On session start — ALWAYS

1. **Read the last entry in `DORA_WORKLOG.md`** (at this repo's root). It tells
   you what was just done, what decisions were made, and what's next. If the
   last entry says "Next up: X", that's your starting point unless the user
   redirects.
2. **Locate the planning docs.** Check `/home/benny/Downloads/DORA DOCS/` first.
   If it's missing (e.g. you're on a different machine), **ask the user where
   the docs are** before doing anything that depends on them. Don't search the
   filesystem and don't try to reconstruct from memory.
3. **Verify state before acting.** The planning docs (esp. `STATUS.md`) are
   known stale; the code is the source of truth. Read the actual code paths
   the prompt references before assuming they exist.
4. **Read `CHANGELOG.md`** for the most recent product-level changes — context
   for what the code looks like now vs. what older docs describe.

## On ending a work unit — ALWAYS

Append a new entry to `DORA_WORKLOG.md` using the template at the top of that
file. Do this even if the unit was partial or blocked — the next session needs
to know where you stopped and why.

Two logs, two purposes — keep them separate:
- **`CHANGELOG.md`** = product/code changes (user-visible, "the app now does
  X"). Updated per the master plan's rule that every prompt updates it.
- **`DORA_WORKLOG.md`** = process/handoff log (which prompt ran, decisions
  made, what's next, open questions). Internal — for agent-to-agent handoff.

## Governing documents (read on demand, not every session)

All paths below are *inside* the DORA DOCS folder (whose location you confirmed
at session start — see step 2 above).

The master is `RECONCILED_FINISHING_PLAN.md`. It owns order
and scope. Inside it:

- **§5** — phased plan (Phase 0 foundations → Phase 1 loop → Phase 2 ingestion
  API → Phase 3 champion → Phase 4 commercialize).
- **§7** — resolved decisions. Scraper → standalone companion; recipe
  comparison gets INV-6'd before keep/cut; nutrition off+simple only;
  gamification → someday.

The **Dora Decision Charter** (12 principles, tiebreak: Effortless + Anti-creep)
lives in `DASHY_DORA_CHAMPION_PLAN.md` Part II. Every design call is checked
against it.

The executable prompts live in `prompts/` inside the docs folder. Each one is
self-contained — read its "Impact & decisions" block first, resolve any
choices with the user, then run it. After running, log it.

## Removed features — do not reintroduce

- Substitute graph (stock-item substitutes).
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
  rough. Note it in the worklog instead.
- Don't silently skip the worklog entry at end of work, even for tiny tasks.
  The whole point is that the *other* agent can pick up cold.
