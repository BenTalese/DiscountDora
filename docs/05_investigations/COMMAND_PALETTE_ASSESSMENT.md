# COMMAND_PALETTE_ASSESSMENT — INV-9

> **⚠ OUTCOME 2026-06-12 — palette retired entirely.** This memo
> recommended SHRINK (cut the redundant nav commands + promote
> entity search to a visible global bar). The user then escalated
> to **CUT** — palette UI, commands registry, and recents storage
> all removed (see worklog + FU-029). The Ctrl-K trigger no
> longer exists; `useShortcut` keyboard shortcuts (`?`, `/`,
> `g s` / `g l` / …) and `ShortcutsCheatsheet` are kept. The
> analysis below is preserved as the trail that led to the cut
> decision.

**Date:** 2026-06-06 · **Type:** Read-only, no code changes · One-page memo.  
**Question:** The user asked "how useful is the command palette really?" Assess
the Ctrl-K palette (`CommandPalette.vue` + `useCommands`).

---

## What it is today

The palette does **two separate jobs in one modal**:

**(a) Command accelerator** — 18 static commands registered in
`MainLayout.vue:323-346`, fuzzy-filtered client-side and ranked by a local
usage counter (`useCommands.ts`, `dora.commandUsage.v1` in localStorage):
- **13 are navigation** ("Go to Dashboard / Stock / Recipes / Settings…") that
  duplicate the always-visible sidebar.
- 5 are genuinely palette-worthy actions: auto-generate-low, open-primary,
  shop-mode, create-stock-item, toggle-dark (+ help: shortcuts, restart-onboarding).

**(b) Entity search** — live cross-entity lookup via
`searchApiService.searchAsync` → `GET /search?q=…&limit=8`
(`global_search.py:252-266`), scoring across stock items, lists, recipes,
locations, products, meal plans (exact 200 → starts-with → contains → fuzzy,
threshold 75). When the query is empty it shows Recents + most-used commands.

**Usage signals:** none off-device. Only the localStorage usage counter exists;
no analytics. So "is it used?" can't be answered from data today — note that.

## Charter read

- **P1 Effortless:** Ctrl-K is one keystroke (good), but the high-value half —
  entity search — is *hidden* behind a shortcut a casual user won't discover.
- **P10 Anti-creep:** the 13 navigation commands are pure duplication of the
  sidebar; surface area with no unique job.
- The entity search is the part that genuinely earns its keep; the nav-command
  bulk is the part that doesn't.

## Stale labels (FU-031)

The palette still says **"Go to Recipes" → `/recipes`** (`MainLayout.vue` ~327)
after the A8 Cookbook rename; same for the `g r` shortcut legend and sidebar.
Works via redirect, label is stale. Already tracked as FU-031.

## Recommendation: **SHRINK + PROMOTE**

- **Shrink (a):** drop the 13 redundant navigation commands; keep the ~5–7 real
  actions. Removes anti-creep surface without losing any capability (nav is one
  sidebar click away).
- **Promote (b):** the entity search is the valuable bit — it belongs on an
  always-visible global search affordance (header), not hidden behind Ctrl-K.
  Backend scoring already exists; this is mostly a placement change.
- Keep Ctrl-K as the power-user accelerator for the surviving actions + as a way
  to focus the same search.
- Fix the stale "Recipes" labels (FU-031) as part of whatever touches this.

If a redesign isn't wanted now, the conservative fallback is **keep as-is** (it
does no active harm) and revisit once there's any usage signal — but the
Charter-aligned move is shrink + promote.

---

## Feedback coverage

| User-flagged item | Finding |
|---|---|
| "how useful is the command palette really?" | Two jobs in one modal: 18 static commands (13 redundant nav) + valuable hidden entity search. No usage telemetry. **Recommend SHRINK** the command set **+ PROMOTE** entity search to a visible global bar. |
| (related) FU-031 stale "Recipes" labels | Confirmed in palette + shortcut legend + sidebar; fix opportunistically with this work. |
