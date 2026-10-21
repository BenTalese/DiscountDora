# Implementation Plan — Stock Overview Redesign (C-1)

**Status:** Plan for review · **Date:** 2026-06-09 · **No code yet** — phased
plan + first reviewable chunk.
**Source proposal:** `PROPOSAL_STOCK_OVERVIEW.md` (2026-06-06; decisions
resolved §7a 2026-06-09).
**Adjacent work:** `PROPOSAL_CART_BUTTON.md` (C-7 — the row's cart control;
**not built yet**); `IMPL_PLAN_STATE_OWNERSHIP.md` (server-owned status/
metrics); `STOCK_OVERVIEW_PERF.md` (the 50-item-cap investigation);
`IMPL_PLAN_COOKBOOK.md` Chunk 5 (the recipe **image pattern** this plan reuses
for stock images).
**Phase:** Master plan **Phase 1** — the overview is the app's most-used
screen (Charter P1 Effortless · P10 Anti-creep · P11 Fast UX).

---

## 0. Verify-state-first: no drift

Re-checked 2026-06-09 against the live code:

- **`pages/StockOverview.vue`** (~685 lines) already uses the shared
  `FilterBar` (A4) and `PageCountsFooter` (A7). Rows render via
  `components/stock/StockItemRow.vue`, which leads with
  `components/chips/StockItemChip.vue`.
- **`StockItemChip.vue` is shared** beyond the overview (recipe-detail
  ingredients, substitutes). C-1 removes it **from the overview row only**;
  an app-wide sweep of other call sites is a separate follow-up (proposal §5).
- **50-item cap (FU-035 / INV-2):** `stockItemStore.getStockItemsAsync()`
  calls `stockItemApiService.getAllAsync()` with no query string → page 1,
  limit 50. The backend (`get_stock_items.py`) paginates correctly; the bug is
  purely the client fetching one page. Decision 7: **virtualise** (not a
  one-line limit bump).
- **Gating not-yet-built deps:** the **C-7 cart button** (row right cluster),
  **`StockItem.image`** (FU-033, for Chunk 6 images), and **C-2 allocation**
  (the "# upcoming planned meals" metric) are all unbuilt. Chunks that need
  them ship a placeholder or keep today's behaviour (see each chunk).

Re-verify exact paths/线 numbers at the start of each chunk — this plan is the
spine, the code is the source of truth.

---

## 1. Resolved decisions driving this plan (from proposal §7a)

1. Detail nav: **desktop drawer + mobile full-page**, one shared component.
2. Miss-tap: **rely on well-sized buttons** (no extra open affordance).
3. Open/in-use toggle: **keep one-tap in the row**.
4. Scan: **one unified action-first scan-mode** (gated `scanning_enabled`).
5. Metric: **keep "# recipes" until C-2**, then swap to planned-meals.
6. Visuals: **status outline** (neutral / amber expiring / red out) + **fill on
   select**; out dims; essential is a filter.
7. 50-cap: **virtualised / infinite-scroll paging**.

---

## 2. Chunked plan (each chunk = one reviewable PR)

### Chunk 1 — Correctness: virtualised list + filtered export ★ FIRST CHUNK
**Closes:** §3 + L65 / L67. **Resolves FU-035.**

The redesign must sit on a list that actually shows every item. No visual
redesign here — just make the data correct and the list scale.

- **Virtualised paging** (decision 7): replace the page-1-only fetch with
  windowed rendering. Options, in order of preference: Quasar `q-virtual-scroll`
  over a fully-loaded set fetched by looping pages until exhausted; or true
  infinite-scroll that fetches pages as you scroll. Pick per
  `STOCK_OVERVIEW_PERF.md`; keep `stockItemStore` the single owner of the list.
- **Filtered export** (L67): CSV **and** PDF/print export the *currently
  filtered* set, not all items. Thread the active filter predicate (or the
  resolved id list) into the export call.
- **Keep the existing row/filters/footer** untouched — this chunk is invisible
  except that all items now appear and export respects filters.

**Risk:** virtualisation interacts with the existing row height + the desktop
peek; keep row markup stable this chunk. *Acceptance:* a pantry of >50 items
shows all of them and stays smooth; export matches the on-screen filtered set.

### Chunk 2 — Top area + footer + filters (layout, no model change)
**Closes:** §2.7 + §2.8 + L92 / L93 / L94 / L95 / L96 / L97 / L98 / L99.

Low-risk, presentation-only.

- **One button group across the top** (L94): New item · Export · **Bulk select**
  (moved up from the filter bar) · Scan · Stocktake.
- **Filter panel hidden by default on desktop too** (L95) — the `FilterBar`
  toggle already supports this; flip the default.
- **Search** stays separate + always visible (L99); **shorten the placeholder**
  (L98).
- **Stock-level filter → dropdown defaulting to "any level"**, **count badges
  removed** (L97) — counts live in the footer.
- **Remove the "used in a recipe" filter** (L96).
- **Footer** (`PageCountsFooter`): minified, spaced off the scroll area,
  reflecting the **filtered** set: Shown · Well-stocked · Sufficient · Low ·
  Out · Flagged · Auto-add · Needs-attention (L93).

*Acceptance:* one tidy top toolbar; filters collapse by default; level filter is
a no-badge dropdown; footer reads the filtered counts.

### Chunk 3 — Row rebuild: kill the chip, one focus action
**Closes:** §2.1 + §2.2 + L70 / L75 / L76 / L77 / L78 / L79 / L80 / L82 / L85 /
L90 / L91 (+ L81 main-zone display, L66 essential-as-filter).

The heart of the redesign — all in `StockItemRow.vue`.

- **Kill `StockItemChip` from the row** (L75). Rebuild left→right:
  `[■ LEVEL button]  Name (emphasised)  · Zone  [img?]  [⏰ expiry] [🍽 # recipes] [open toggle] [🛒 cart]`.
- **Stock-level button first** — big, coloured, **text-less**; tap → level
  picker. Replaces both the chip avatar and the old right-side level dropdown
  (one focus, L70).
- **Name** larger/bolder (L79); **main zone** shown, lightly clickable to
  filter-to-location (L81; full breadcrumb is C-cross).
- **Right cluster**: expiry (Chunk 4), **# recipes** metric (decision 5 — keep
  today's count, relabelled later in C-2), **open/in-use toggle kept in-row**
  (decision 3), **cart button** (C-7 component — until C-7 ships, render a
  disabled placeholder slot + log it; don't design cart logic here).
- **Image collapse toggle (C-cross §2.8 / FU-106).** A small inline button
  in the overview header (next to the existing filter affordances) flips the
  `show_stock_images` user flag — when off, the row's `[img?]` slot
  collapses out of the layout entirely (denser rows). The User flag +
  `useImagePrefs()` composable are wired by C-cross Chunk 5; this chunk owns
  the row-layout change + the inline button (deferred from C-cross
  intentionally so the row geometry is decided here, not retroactively).
  Pair with FU-033 image rendering when that lands.
- **Remove:** OK/Mid/Low/Out badge (L76), red dot (L82), "On N lists" chip
  (L85), ⋮ overflow (L90). Rows get **taller** (L78).
- **Status → whole-row outline** (decision 6): neutral default / amber
  expiring-soon / red out-or-expired; out rows dim. **Selection fills the row**
  (L91). "Essential" stays a filter, no row badge (L66).
- Use A1 theme tokens + `BaseButton`; no raw colours.

**Risk:** `StockItemChip` is shared — only swap it out *in the overview row*;
leave the component for its other callers. The level button + outline must read
in all themes (Pesto light/dark, Cherry Cola dark). *Acceptance:* one focus
(level button); chip gone from the row; outline/selection rules hold; no
badge/dot/overflow.

### Chunk 4 — Expiry control
**Closes:** §2.4 + L86 / L87 / L88.

- Expiry lives in the right cluster (L86).
- **No expiry set → date-picker** (L87).
- **Expiry set → dropdown +1 / +7 / +14 / Clear** (L88), replacing +7/+30/clear.

*Acceptance:* both states behave; dates persist.

### Chunk 5 — Detail navigation model
**Closes:** §2.3 + L68 / L69 / L71 / L72 (decisions 1 + 2).

- **Desktop:** row-tap → **side drawer** (the embedded peek).
- **Mobile:** row-tap → **full page**, no drawer; **long-press → multi-select**.
- **One shared detail component** in both frames (L69). Row-tap is the only nav
  to detail (L68); rely on well-sized buttons for miss-tap (decision 2).
- Coordinate with the Stock Item Detail polish (the detail surface has its own
  feedback cluster) so the shared component isn't forked.

**Risk:** the current code already has a desktop peek; this chunk formalises the
two-frame model + adds mobile long-press. *Acceptance:* drawer on desktop,
full-page on mobile, same component; long-press multi-selects on mobile.

### Chunk 6 — Images (gated on FU-033)
**Closes:** §2.5 + L74.

- **Show/hide images** toggle in the top area, **preference saved** (L74).
- Thumbnail in the row when on; **"no picture" placeholder** otherwise.
- **Reuse the recipe image pattern** (`IMPL_PLAN_COOKBOOK.md` Chunk 5): data-URL
  string storage + a `GET /stock-items/<id>/image` bytes endpoint + `has_image`
  on the DTO + an `<img>` with placeholder fallback. **This effectively builds
  FU-033** (own image + linked-product-image fallback) — coordinate so there's
  one mechanism.

**Risk:** depends on `StockItem.image` being populated (FU-033). *Acceptance:*
toggle persists; images show with placeholder fallback.

### Chunk 7 — Unified scan-mode (gated `scanning_enabled`)
**Closes:** §2.9 + L73 (decision 4).

- A single **action-first** scan-mode: pick an action (open details / mark out /
  mark well-stocked / …), then scan items to apply it — covering the stocktake
  scan-to-check case so there aren't two scanners.
- **Gated behind the install-wide `scanning_enabled` flag** (off by default) per
  the charter's removed-features note — the whole scanning surface stays opt-in.

*Acceptance:* with scanning enabled, action-first scan applies level actions;
hidden entirely when the flag is off.

### Chunk 8 — Planned-meals metric (deferred, gated on C-2)
**Closes:** §2.6 + L89.

Swap the row's **"# recipes" → "# upcoming planned meals"** (future,
not-yet-cooked allocations only) once C-2 / B6 allocation lands. Until then the
row keeps "# recipes" (decision 5). Not part of the initial C-1 build.

---

## 3. Suggested run order

1 (correctness) → 2 (top/footer/filters) → 3 (row rebuild) → 4 (expiry) →
5 (detail nav) → 6 (images, when FU-033/Chunk-6-pattern is in) → 7 (scan-mode).
**8 deferred** until C-2.

Chunks 1, 2, 4 are independent and low-risk. Chunk 3 is the big one and softly
depends on C-7 for the cart control (ships a placeholder otherwise). Chunk 5
touches shared detail. Chunk 6 needs FU-033.

---

## 4. Cross-cutting notes

- **C-7 cart button** isn't built — Chunk 3 hosts a placeholder until it is;
  don't build cart logic in C-1.
- **`StockItemChip` app-wide removal** is out of scope — C-1 only drops it from
  the overview row; a follow-up sweeps recipe-detail/substitute call sites.
- **Location display** (zone vs full breadcrumb) is **C-cross**; C-1 shows the
  main zone only.
- **State-ownership (R-003):** status/outline class, needs-attention, and footer
  counts should be server-derived facts where they're cross-entity; keep the
  client rendering, not recomputing thresholds.
- Honour Wave-A standards throughout: theme tokens only, `BaseButton`,
  `FilterBar`, `PageCountsFooter`.

---

## 5. Feedback coverage (STOCK OVERVIEW, L63–L99)

Mirrors `PROPOSAL_STOCK_OVERVIEW.md §9`, mapped to chunks here.

| Line | Summary | Chunk |
|---|---|---|
| L65 | Nav lag / DS4 / 50-cap | 1 |
| L66 | Essential is a filter, not a row badge | 3 |
| L67 | Export the filtered set (CSV+PDF) | 1 |
| L68 | Mobile full-page, lock nav to row-tap | 5 |
| L69 | Same detail in drawer + standalone | 5 |
| L70 | Level button first, big, coloured, no text | 3 |
| L71 | Row-tap → detail (drawer/page) | 5 |
| L72 | Mobile long-press → multi-select | 5 |
| L73 | Scan-mode (action-first) | 7 |
| L74 | Show/hide images (saved pref) | 6 |
| L75 | Remove the chip | 3 |
| L76 | Remove OK/Mid/Low/Out badge | 3 |
| L77 | Whole-row outline | 3 |
| L78 | Taller rows | 3 |
| L79 | Emphasise the name | 3 |
| L80 | Outline colour rules | 3 |
| L81 | Main zone, not "right shelf" | 3 (full breadcrumb → C-cross) |
| L82 | Remove red status dot | 3 |
| L83 | One multi-purpose cart button | 3 → C-7 |
| L84 | Cart complexity | C-7 |
| L85 | Remove "On N lists" chip | 3 |
| L86 | Expiry → right cluster | 4 |
| L87 | No expiry → date picker | 4 |
| L88 | Expiry set → +1/+7/+14/clear | 4 |
| L89 | "# recipes" → planned meals | 8 (deferred; keep # recipes until C-2) |
| L90 | Remove ⋮ overflow | 3 |
| L91 | Selection fills row | 3 |
| L92 | Top area tidy-up | 2 |
| L93 | Counts → footer | 2 |
| L94 | Buttons grouped across top | 2 |
| L95 | Filter button hidden by default | 2 |
| L96 | Remove "used in a recipe" filter | 2 |
| L97 | Level filter → dropdown, no counts, "any" | 2 |
| L98 | Shorten search placeholder | 2 |
| L99 | Keep search separate | 2 |

Out-of-scope (own prompts): cart button (C-7), full location breadcrumb
(C-cross), planned-meals allocation (C-2), `StockItem.image` mechanism (FU-033 —
folded into Chunk 6).
