# Proposal — Stock Overview Redesign (C-1)

**Status:** Draft for discussion · **Date:** 2026-06-06 · Changes NO code.  
**Scope:** Redesign the stock overview — top area, the row (kill the "chip", make
stock-level the focus action), the detail-navigation model, filters, footer
counts, scan mode, images, and the per-item metric. Defers the cart button to
**C-7**; consumes that component. Honours Wave-A standards (tokens, BaseButton,
A7 sticky footer).

> **Charter tie-break:** Effortless (P1) + Anti-creep (P10) + Fast UX (P11). The
> overview is the app's most-used screen; every element must earn its place or go.

---

## 1. Current state (what we're changing)

From the live code (`StockOverview.vue`, `StockItemRow.vue`,
`StockItemChip.vue`, `useStockFilters.ts`):

- **Top area** is a flat row of New / Scan / Stocktake / Export + a separate
  search box; the **filter bar is always visible** (collapsible only on mobile).
  Counts already live in a sticky `PageCountsFooter`.
- **The row leads with a dense `StockItemChip`** that crams in: a level-colour
  avatar, the name, a "OK/Mid/Low/Out" badge, a cart icon, a red attention dot,
  and an overflow (⋮) menu. Then the row adds a location chip, an "On N lists"
  chip, an expiry button, a "# recipes" button, a **right-aligned stock-level
  dropdown**, an open/in-use lock toggle, and a cart quick-add button.
- **Row click** toggles a desktop split-pane "peek" (embedded detail); bulk mode
  is entered via a filter-bar button + per-row checkboxes.
- **Expiry** is a dropdown with +7 / +30 / clear (no date-picker, no +1/+14).
- **No images**, no show/hide preference.
- **# recipes** counts recipes referencing the item.

The user's verdict (L75): *"the stock item chip is a bad idea… looks too messy,
too much detail squished together."* The row has **three** competing focal points
(chip, mid-row buttons, right-side level dropdown) and no clear primary action.

---

## 2. The redesign

### 2.1 The row — one focus action, a clean right cluster

**Kill the chip entirely** (L75). Rebuild the row left-to-right as:

```
[■ LEVEL]   Name (emphasised)            ·  Zone        [img?]   [⏰ expiry] [🍽 N] [🛒 cart]
  ▲ focus     ▲ bigger / bolder            ▲ main zone            ▲──── right cluster ────▲
```

1. **Stock-level button — first in row, the focus** (L70). A big, coloured,
   **text-less** button (the level colour *is* the signal); tap → level picker.
   This *replaces* both the chip's level avatar **and** the right-side level
   dropdown — one control, unmistakably the primary action. (The original spec's
   `q-btn-dropdown` colour-push snippet is exactly this shape — §6.)
2. **Name** — larger / bolder (L79); the row reads name-first after the colour.
3. **Main zone** — show the top-level location zone, not "right shelf" (L81); a
   light, optionally-clickable affordance to filter-to-location. (Exact location
   display is C-cross; see §5.)
4. **Optional image** — a thumbnail when "show images" is on (L74; §2.5).
5. **Right cluster** (grouped, L86):
   - **Expiry** (§2.4),
   - **planned-meals metric** (§2.6),
   - **cart button** (the C-7 component).

**Removed from the row:** the OK/Mid/Low/Out badge (L76), the red status dot
(L82), the in-chip cart icon (L83), the "On N lists" chip (L85), and the ⋮
overflow menu (L90 — all its actions exist on the detail page). Rows get a touch
taller (L78).

> **Open:** the **open/in-use lock toggle** currently in the row isn't named in
> the feedback. Proposed: move it to detail to keep the row calm; keep only if
> you want a one-tap "mark opened" here (§7).

### 2.2 Highlighting & selection (define the rules — L66, L77, L80, L91)

- **Status → whole-row outline** (L77), not a chip border. Out-of-stock rows dim
  (existing). One documented scheme: neutral border default; amber border =
  expiring-soon; red border = out/expired. No per-item "essential" decoration —
  essential is a *filter*, not a row badge (L66, L82).
- **Selection → fills the row** (L91) rather than recolouring the outline, so
  selection never collides with the status outline colour.

### 2.3 Detail navigation model (the #1 open decision — L68, L71)

Proposed, reconciling the two feedback bullets:

- **Desktop:** row click → **side drawer** (the embedded peek), Google-Drive
  style.
- **Mobile:** row click → **full page**; **no drawer**; **long-press → multi-
  select** (L72). Row-tap is the only nav to detail (L68 "locks navigation to row
  selection").
- The **detail component is identical** in drawer and full-page (L69) — one
  component, two frames.

> L68's wording ("detail view should only appear on mobile…") conflicts with L71
> (desktop drawer) and L69 (implies both drawer + standalone exist). I read L68 as
> *"on mobile, use full-page detail, no drawer"* — not "remove desktop detail."
> **Confirm.** Also the **miss-tap risk** (L71): with well-sized buttons + the
> level button being the only large hit-target on the left, accidental row-opens
> should be rare; worst case a row-open is harmless (read-only). Confirm you're
> comfortable, or we add a tiny non-button "open" affordance.

### 2.4 Expiry control (L86, L87, L88)

Move to the right cluster (L86). Behaviour by state:

- **No expiry set** → click opens a **date-picker** (L87) — not a dropdown.
- **Expiry set** → dropdown with **+1 / +7 / +14 / Clear** (L88) (replacing the
  current +7 / +30 / clear).

### 2.5 Images + missing-picture placeholder (L74)

- **Show/hide images** toggle in the top area, **preference saved** (L74).
- When on and an item has no image, show a clear **"no picture" placeholder**
  (the original spec's greyed food/slash icon — §6).
- Depends on `StockItem.image` actually being populated — that feature is unbuilt
  (**FU-033**; own-image + linked-product-image fallback). Until it ships, "show
  images" renders placeholders / product images only. Cross-ref FU-033.

### 2.6 Per-item metric: "# upcoming planned meals" (L89)

Replace "# recipes" with **"# upcoming planned meals"** — far more decision-useful
("Milk is low **and** on 5 planned meals" → buy). Requirements:

- Count **future, not-yet-cooked** allocations only (distinguish "going to cook"
  from "already cooked") — L89.
- **Depends on meal-plan allocation** (C-2 / B6). That allocation model is the
  subject of `PROPOSAL_MEAL_PLANS.md`. Until it lands, either keep "# recipes" or
  hide the metric — don't ship a misleading count.

### 2.7 Top area (L92-99)

- **One button group across the top** (L94): New item · Export · **Bulk select**
  (move it up from the filter bar) · Scan · Stocktake.
- **Filter button toggles a filter panel, hidden by default** (L95) — on desktop
  too, not just mobile.
- **Search stays separate and always visible** (L99); **shorten its placeholder**
  so the end is visible (L98).
- **Stock-level filter** → a **dropdown defaulting to "any level"**, with the
  **count badges removed** (L97). Counts live in the footer instead.
- **Remove the "used in a recipe" filter** (L96).

### 2.8 Footer counts (L93) — A7 sticky footer

The sticky `PageCountsFooter` already exists; refine it: minified, with **space
between it and the scroll area**, reflecting the **filtered** set, showing
Shown · Well-stocked · Sufficient · Low · Out · Flagged · Auto-add · Needs-
attention. (Matches the original spec's "info summary panel at the bottom" — §6.)

### 2.9 Scan mode (L73)

Add a **scan mode**: pick an **action** first, then scan items to apply it —
"open details", "mark out of stock", "mark well-stocked", etc. Distinct from
today's Scan button (which just jumps to the scanned item).

> **Open:** does scan-mode live here, or **fold into stocktake** (scan-to-check)?
> The brief flags this. Proposed: a single scan-mode that *offers* stock-level
> actions (covering the stocktake case) so we don't build two scanners (§7).

---

## 3. Correctness prerequisites (fix before/with the redesign)

- **The overview silently shows only the first 50 items** (FU-035 / INV-2):
  `getStockItemsAsync` fetches page 1 only. A redesigned overview that still drops
  items >50 is broken. Fix as part of this work — raise the limit, page, or
  virtualise (see `STOCK_OVERVIEW_PERF.md`).
- **Export must use the filtered set, not all items** (L67) — both CSV and PDF.

---

## 4. What this removes (net less surface — P10)

Chip component (from this surface) · OK/Mid/Low/Out badge · red status dot ·
in-row "On N lists" chip · ⋮ overflow menu · in-chip cart icon · the duplicate
right-side level dropdown · the "used in a recipe" filter · stock-level filter
count badges. **Three focal points → one** (the level button).

---

## 5. Ripple & dependencies

- **Cart button → C-7.** The right-cluster cart control is the
  `PROPOSAL_CART_BUTTON.md` component, incl. its state-aware colour + the quick-
  remove path. Do not design cart logic here.
- **`StockItemChip` is shared** (recipe detail ingredients, substitutes, etc.).
  L75 says it's bad "in its usages across the app" — removing it app-wide is
  bigger than this surface. C-1 removes it from the overview row; a follow-up
  sweeps the other call sites.
- **Location display → C-cross** (zone vs full breadcrumb). C-1 just needs "show
  the main zone" (L81).
- **Planned-meals metric → C-2** allocation (§2.6).
- **Images → FU-033** (`StockItem.image` unbuilt).
- **Detail component** shared drawer/full-page → coordinate with the Stock Item
  Detail polish (the detail surface has its own feedback cluster).

---

## 6. From the original spec (historical — `docs/00_original_spec/`)

Non-authoritative; included where it adds or corroborates. Tagged keep / consider
/ superseded.

| Original note | Verdict | Effect |
|---|---|---|
| Stock-level indicator as a coloured `q-btn-dropdown` (push, no-caps); "circle or square shaped" taskboard note | **keep (corroborates)** | This is exactly the §2.1 focus button (L70's "copy what I had before"). Decide circle vs square as a styling detail. |
| "Info summary panel at the bottom" / "Total Items 150 \| Low 12 \| High 88" | **keep (corroborates)** | The §2.8 sticky footer. |
| "Missing picture placeholder — food icon greyed with a slash" | **keep** | The §2.5 placeholder. |
| Cart on overview: colour-on-add, quick-**remove** if on one list, multi-list remove prompt, swipe-right to choose list, auto-primary if only one list | **keep → C-7** | Already folded into `PROPOSAL_CART_BUTTON.md §9`. C-1 just hosts that component. |
| "Set a stock item's picture from a linked product's picture" | **keep (cross-ref)** | Corroborates the FU-033 image fallback (§2.5). |
| Long-press → multi-select; Google-Drive hover/selected styling; select/deselect | **keep (corroborates)** | §2.2 / §2.3 (L71/L72/L91). |
| **"Sort by clicking column headers" — author ARCHIVED it** ("It's a list view now, all controlled via filters") | **superseded** | Do **not** add column-header sorting; sort stays a filter dropdown. |

---

## 7. Open decisions (for co-design)

1. **Detail nav model** — confirm desktop-drawer + mobile-full-page (§2.3), and
   the L68 reading (mobile = no drawer, *not* "remove desktop detail").
2. **Miss-tap risk** (L71) — comfortable relying on well-sized buttons, or add a
   dedicated non-button open affordance?
3. **Open/in-use toggle** — move to detail (proposed) or keep a one-tap "mark
   opened" in the row?
4. **Scan mode vs stocktake** (L73) — one unified scanner with level actions
   (proposed), or a separate overview scan-mode?
5. **Planned-meals metric fallback** — until C-2 allocation ships, keep "#
   recipes" or hide the metric?
6. **Outline colour scheme** (L80) — confirm the status-outline palette (neutral
   / amber expiring / red out) and that selection = row fill.
7. **50-item cap fix** — quick `?limit` bump now vs virtualised paging (ties to
   `STOCK_OVERVIEW_PERF.md`).

---

## 8. Suggested sequencing

1. **Correctness first:** fix the 50-item cap + filtered export (§3) — small, and
   the redesign is built on a list that actually shows everything.
2. **Top area + footer + filters** (§2.7, §2.8) — layout-only, low risk, no model
   change.
3. **Row rebuild:** kill the chip, level-button-first, right cluster, outline/
   selection rules (§2.1, §2.2). Host the C-7 cart button (after/with C-7).
4. **Expiry control** (§2.4) and **images** (§2.5, gated on FU-033).
5. **Detail nav model** (§2.3) once confirmed.
6. **Scan mode** (§2.9) and **planned-meals metric** (§2.6, gated on C-2).

---

## 9. Feedback coverage

Maps every STOCK OVERVIEW bullet (L63-99) from
`docs/02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md`.

| Bullet (line) | Summary | Where |
|---|---|---|
| L65 | Nav lag / DS4 | INV-2 (`STOCK_OVERVIEW_PERF.md`); §3 50-cap fix |
| L66 | Weird highlighting; essential → red dot | §2.2 (status outline; essential is a filter, no dot) |
| L67 | Export filtered, not all (CSV+PDF) | §3 |
| L68 | Detail only on mobile; mobile no drawer; lock nav to row | §2.3 (+ open decision 1) |
| L69 | Detail same in standalone & drawer | §2.3 (one component) |
| L70 | Stock-level button first, big, coloured, no text — the focus | §2.1 |
| L71 | Row click → detail (drawer/page), Google-Drive; miss-tap concern | §2.3 (+ open decision 2) |
| L72 | Mobile long-press → multi-select | §2.3 |
| L73 | Scan mode (pick action for scanned items); maybe into stocktake | §2.9 (+ open decision 4) |
| L74 | Show/hide images (save pref) | §2.5 |
| L75 | The chip is bad — remove | §2.1, §4 |
| L76 | Remove OK/Mid/Low/Out badge | §2.1, §4 |
| L77 | Highlight → whole-row outline | §2.2 |
| L78 | Taller rows | §2.1 |
| L79 | Emphasise the name | §2.1 |
| L80 | Define highlight/outline colour rules | §2.2 (+ open decision 6) |
| L81 | Location chip → main zone, not "right shelf" | §2.1, §5 (C-cross) |
| L82 | Remove red status dot | §2.1, §2.2, §4 |
| L83 | Cart icon in chip unnecessary; one multi-purpose button | §5 → C-7 |
| L84 | Cart complexity | C-7 (`PROPOSAL_CART_BUTTON.md`) |
| L85 | "On N lists" chip — remove | §2.1, §4 |
| L86 | Expiry button → right cluster | §2.4 |
| L87 | No expiry → date picker | §2.4 |
| L88 | Expiry set → +1/+7/+14/clear | §2.4 |
| L89 | "# recipes" → "# upcoming planned meals" | §2.6 (+ open decision 5; C-2 dep) |
| L90 | Remove ⋮ overflow (fluff) | §2.1, §4 |
| L91 | Selection fills row (not outline) | §2.2 |
| L92 | Top area tidy-up | §2.7 |
| L93 | Counts → sticky footer, add more | §2.8 |
| L94 | All buttons grouped across top | §2.7 |
| L95 | Filter button, hidden by default | §2.7 |
| L96 | Remove "used in a recipe" filter | §2.7, §4 |
| L97 | Stock-level filter → dropdown, no counts, "any" default | §2.7 |
| L98 | Shorten search placeholder | §2.7 |
| L99 | Keep search separate from other filters | §2.7 |
