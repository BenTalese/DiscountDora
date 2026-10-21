# Shopping List UX v2 — single-page shopping experience

**Status:** BUILT 2026-06-12 (same-day approve + build) — §11 calls resolved in
§12. Implementation verified static (lint, vue-tsc, 21/21 shopping e2e tests);
browser pass tracked as FU-165.
**Supersedes / extends:** `SHOPPING_LIST_REDESIGN_PROPOSAL.md` (v1). v1's structural
work (status enum, overview-into-detail merge, inferred primary, planned shop date,
shop-mode receipt loop) **shipped** as P6-01 Chunks 1–7 and is not re-litigated here.
v2 is the *presentation and interaction* layer the user has now reviewed and rejected,
plus the shop-mode → single-page merge.
**Absorbs:** FU-158 (responsive layout + today's-date picking), FU-159 (planned shop
date surfacing — partially built since it was raised), FU-160 (shopping-day alert —
stays open, depends on this), FU-097 (formatQuantity rollout, opportunistic).
**Source feedback:** the 2026-06-12 session bullets (S1–S18 below) + the original
L400–L421 bullets from `Feedback _ Fixes - as of [06-Jun-2026].md`.

---

## 0. Feedback being addressed (verbatim, numbered)

From the 2026-06-12 session:

| # | Bullet (condensed) |
|---|---|
| S1 | Hate the stock item chips. Where else is this used? Can it be axed from the app entirely? |
| S2 | Should be able to clear custom name → creation date or shop date replaces it |
| S3 | Display name = custom name > planned date > creation date |
| S4 | Tab title should say "Shopping lists" not "Shopping list" |
| S5 | Hate most buttons hidden behind ellipsis. Use the toolbar area, consistent with other pages |
| S6 | "No lists" view flashes briefly in the list-items area on page load |
| S7 | Desktop: right panel listing all lists ordered by relevant date (finalised > planned > created), auto-scrolled to selection, virtualised. Mobile: dropdown at top |
| S8 | Old "primary list detail" → top info area of the current list; the doughnut completion graph is gone — bring it back |
| S9 | First navigation should land on the "next up" list (first date-wise after the last completed list) |
| S10 | Overall UI looks garbage — make it nice, modern, polished, follow UX standards |
| S11 | What is "shop mode"? Nobody shops one item at a time in a pre-set order. Merge it onto the main page — but first fully understand what's built into it |
| S12 | Per-item buttons hidden behind ellipsis — move them onto the row directly. Fewer clicks |
| S13 | (Keep) I do like the icons used in the current list-selector dropdown |
| S14 | Shop day button is just text — make it a proper button, almost missed it |
| S15 | Show the list's current state next to the name as a big badge (not a tiny chip) |
| S16 | Info text ("3 items, 0 ticked, created…") feels too tiny |
| S17 | Price button is tiny; didn't even know it was clickable (detail page) |
| S18 | What other improvements can you see? Make a solid shopping experience |

Original L400–L421 bullets are mapped in the coverage table (§10).

---

## 1. Audit findings (what the code actually says)

Verified against code on branch `prototype/claude-upgrades`, 2026-06-12:

1. **StockItemChip has exactly two call sites** (S1):
   - `web_app/src/pages/ShoppingListDetail.vue:557` — per shopping-list line.
   - `web_app/src/pages/StockItemDetailPage.vue:380` — the substitutes list on a
     stock item's detail page.
   Nothing else imports it. It **can be axed entirely** — see §6.
2. **Custom name cannot be cleared today** (S2). `UpdateShoppingListRequest.name`
   has `min_length=1`, and the handler skips `None`
   (`dora_api/features/shopping_lists/manage_shopping_list.py:87,113`). The
   create handler always materialises a date string into `name`, so "no custom
   name" isn't representable — the date-name is baked in at creation and goes
   stale relative to a later-set shop date. Backend change required — see §5.
3. **Tab title source** (S4): `routes.ts:137` — `meta: { title: 'Shopping list' }`.
   One-word fix.
4. **The "no lists" flash** (S6) is real and root-caused: `loading = ref(false)`
   (`ShoppingListDetail.vue:1041`) and `load()` only fires in `onMounted`, so the
   first render frame has `loading=false, detail=null` → the `v-else` fallback
   ("This list isn't available… create a new one", line 920) flashes until the
   loader flips. One-line fix (`ref(true)`), plus the same guard on the v2 rail.
5. **The doughnut existed** (S8): the pre-merge overview had a
   `q-circular-progress` completion ring per list, deleted in commit `3e07e2e`
   ("Finishing P6-01") when the overview page was gutted. v1's merge dropped it
   instead of relocating it. It returns in the top info area — see §4.
6. **Shop day UI exists but is a text link** (S14) buried in the caption line
   (`ShoppingListDetail.vue:154–162`) — FU-159 was *partially* resolved by Chunk 7;
   the discoverability complaint stands.
7. **`PageToolbar.vue` exists** (title/subtitle/actions-slot component, currently
   used only by `StocktakePage.vue`) — the right base for S5 instead of a third
   bespoke header.
8. **Virtualisation precedent**: `StockOverview.vue` already uses Quasar
   virtual scroll — same approach for the rail (S7).
9. **Old L414 "drag and drop index off"** — not addressed by any logged fix I can
   find; needs a browser repro before/after the row rebuild (logged as FU, §9).

---

## 2. Shop mode — complete inventory and disposition (S11)

Everything built into `ShoppingListShopMode.vue` (~1,135 lines), and where each
piece lands in the merged single page. Nothing falls on the floor silently.

| # | Shop-mode feature | What it does today | Disposition in v2 |
|---|---|---|---|
| M1 | One-item-at-a-time card | Shows a single "current item" big card | **Cut.** This is the rejected interaction model (S11). |
| M2 | Location-ordered walk | Sorts unticked → location breadcrumb → sequence | **Cut as a shopping behaviour** *(revised on review)*: stock-item location (where it lives at home) ≠ shelf location in the store, and users must not be pushed to enter location data to shop. Group-by stays a purely manual view option with **no** shopping-time default or recommendation. |
| M3 | "Got it" big green CTA | Ticks current line | **Merged.** The row tick checkbox, with enlarged touch targets while shopping (§7). |
| M4 | Skip (persisted reorder) | Pushes current item to end via reorder API | **Cut.** Meaningless when the whole list is visible — you just tick in any order. Reorder API stays (drag). |
| M5 | Up-next preview (2 items) | Jump-ahead buttons | **Cut.** Same reason as M4. |
| M6 | Whole-list peek dialog | Modal copy of the list | **Cut.** The page *is* the whole list now. |
| M7 | Tap-to-type quantity | Dialog numeric editor | **Merged.** Detail rows already have a qty input; keep stepper + direct input. |
| M8 | Price-as-you-go editor | actual_unit_price + purchased merchant ("list becomes the receipt", L419) | **Merged.** Same editor, now behind a *proper visible price button* on every row (S17, §7). No behaviour change to the P2-02 receipt loop. |
| M9 | Substitute picker | Radio list of the line's *offers* | **Merged.** Offer chips on the row already do this; the row keeps the "swap with substitute" action for stock-item-level subs (L418). |
| M10 | Progress bar + picked count | Linear progress in header | **Merged → doughnut** + counts in the top info area (S8), plus the sticky shopping footer (§7). |
| M11 | Estimated remaining cost | Footer total | **Merged.** Server-owned `totals.remaining_price` shown in info area + shopping footer. |
| M12 | Finish & restock / finish early | POST /finish → DONE + restock ticked + snapshot | **Merged + upgraded** *(revised on review; per-item pickers **SUPERSEDED 2026-07-22, FU-582**)*: Finish opens a **finish review modal** — a summary of the ticked items above a single primary **Restock & finish** button. Every ticked item restocks to Stocked; there is no per-item level choice and the endpoint takes no options (the `level_overrides` field was removed). Product-only lines (no stock item) are listed as not stock-tracked. |
| M13 | Exit (back) → stop shopping | POST /stop → back to draft | **Cut** *(revised on review)*: no Pause. Lifecycle is Start shopping → Finish & restock (→ Reopen if needed). The orphaned `/stop` endpoint is deleted with the page. |
| M14 | Keyboard shortcuts (space/enter pick, s skip, u undo, esc exit) | Shop-mode-scoped | **Partially merged.** Detail already has space-tick + arrow focus + `n` add; add `u` = untick last ticked. `s`/`esc` die with M1/M4. |
| M15 | Status guard (bounces non-shopping lists) | onMounted redirect | **Obsolete** — route deleted. |

**Net result:** the `/shopping-lists/:id/shop` route and `ShoppingListShopMode.vue`
are deleted. The `shopping` **status stays** — it still drives the lifecycle
button (Start → Finish), the shopping footer, the shopping-day banner logic, the
receipt semantics, and FU-160's future alert. Only the *separate page* dies, and
with it the now-orphaned `POST /stop` endpoint (no Pause — §12 Q3). An
accidental "Start shopping" is escapable via Finish (nothing ticked = nothing
restocked) → Reopen; flagged as a watch-item, not worth a dedicated control.
References to the shop route (router guard at `routes.ts:110–131`,
`doraContextualActions.ts`, dashboard card links) are updated.

---

## 3. Page architecture (S7, S9, S13)

One route: `/shopping-lists/:id` (detail stays canonical; `/shopping-lists`
remains the no-lists landing + redirect). New layout:

```
Desktop (≥ md)                              Mobile (< md)
┌──────────────────────────┬──────────────┐ ┌──────────────────────┐
│ PageToolbar (title row + │  LISTS RAIL  │ │ List dropdown ▾      │
│ visible action buttons)  │  ┌────────┐  │ │ (current selector,   │
├──────────────────────────┤  │ + New  │  │ │  same icons, new     │
│ TOP INFO AREA            │  ├────────┤  │ │  date ordering)      │
│ name + STATUS BADGE      │  │ done ✓ │  │ ├──────────────────────┤
│ meta row · shop-day btn  │  │ done ✓ │  │ │ TOP INFO AREA        │
│ doughnut + totals        │  │ ▶ today│  │ │ (compact)            │
├──────────────────────────┤  │ future │  │ ├──────────────────────┤
│ quick add (slim, inline) │  │ future │  │ │ rows…                │
│ rows…                    │  └────────┘  │ │                      │
│                          │  (virtual    │ ├──────────────────────┤
│                          │   scroll)    │ │ sticky shop footer   │
└──────────────────────────┴──────────────┘ └──────────────────────┘
```

### 3.1 The lists rail (desktop)

- **Contents:** every list, active *and* done, in one continuum (old L408).
- **Order:** by **effective order date** = `completed_at` (finalised shop date)
  → else `planned_shop_date` → else `created_at`. Ascending: past at top,
  future at bottom (S7). Within the same date, `created_at` tiebreak.
- **Auto-scroll:** on load and on selection change, the rail scrolls the
  selected list into view (centre-ish). `q-virtual-scroll` `scrollTo` — the
  rail must be virtualised because it accretes forever (S7;
  precedent: `StockOverview.vue`).
- **Rail item:** status icon (keep the current dropdown's icons — S13: `list`
  for draft, `shopping_cart_checkout` for shopping, add `check_circle` muted
  for done) + display name + effective date + `ticked/total` mini-count. Done
  items render muted. The "next up" list (§3.3) gets a subtle ▶ / "next up"
  marker.
- **Per-item kebab stays, slimmed** (copy unticked → new / delete): rare,
  per-*other*-list operations; the S5/S12 complaint is about the *selected
  list's* working buttons, not rail housekeeping. **"Archive" is removed
  entirely** (§12 Q2): with the status enum, "archive" was just "mark done
  without restocking" — a redundant third path. Lists are *finished* (the
  real flow) or *deleted*.
- **Top of rail:** "New list" button. **Bottom:** "Manage templates" link.
- Rail header/footer never flash empty (same `loading` guard as §1.4).

### 3.2 Mobile

The rail collapses into the existing dropdown selector at the top of the page
(S7), reordered by the same effective-date rule, same icons (S13), same "next
up" marker. The dropdown's existing structure (New list / Active / Archived /
Manage templates) survives, but Active+Archived merge into the single
date-ordered continuum to match the rail semantics.

### 3.3 First-navigation pick — "next up" (S9)

Replaces the current route-guard heuristic (status, then `created_at desc` —
`routes.ts:110–131`). Per R-003 this is a cross-entity domain rule, so the
**server computes it**: `GET /api/shopping-lists` response gains
`next_up_list_id`, defined as:

1. Any list with status `shopping` (a live shop always wins; oldest if several).
2. Else: the non-done list with the **earliest effective date on/after the most
   recent `completed_at`** across done lists ("first date-wise after the last
   completed list"). Effective date = `planned_shop_date` else `created_at`.
   No done lists yet → earliest effective date overall.
3. Else (everything done): the most recently completed list.
4. Else (no lists): landing page empty state.

The route guard and the rail's "next up" marker both read this one field — no
client copy of the rule.

---

## 4. Top info area (S8, S14, S15, S16)

Replaces the current cramped header-caption. Layout (desktop; mobile stacks):

- **Line 1:** display name in `text-h4`/`h5` + **big status badge** right
  beside it (S15): `DRAFT` (neutral) / `SHOPPING` (positive, subtle pulse) /
  `DONE` (muted). A QBadge-based `ListStatusBadge` sized to the heading — not a
  dense chip. Inline pencil = rename; while editing, a **"Clear name"** action
  appears when a custom name exists (S2).
- **Line 2 — meta row in `body2`, not `caption`** (S16): `8 items · 3 ticked` ·
  `Created Thu 12 Jun` · (`Completed Sat 14 Jun` when done).
- **Shop day = a real outlined button** with the `event` icon (S14):
  label "Shop day: Fri 14 Jun" / "Set shop day", opens the existing date
  editor. Overdue state tints it warning — which lets the separate overdue
  *banner* shrink or disappear (one signal, not two).
- **Doughnut returns** (S8): `q-circular-progress` ring (the `3e07e2e`
  casualty), value = `ticked/line_count` from server-owned summary counts,
  centre label `3/8`. Sits right of the info block with the money block beside
  it: **Remaining $X · Full list $Y · Savings $Z** from `detail.totals` —
  i.e. the old totals card moves *up* into the info area (it's "current state
  of the list" info, and it's what shop-mode's header/footer showed — M10/M11).

---

## 5. Naming: nullable custom name + server-computed display name (S2, S3)

Backend:
- `ShoppingList.name` becomes nullable (migration). `null` = "no custom name".
- Create: stop materialising the date string into `name`; default is `null`.
- Update: allow explicit `name: null` to clear (mirror the
  `planned_shop_date` explicit-null pattern already in the PATCH handler);
  drop `min_length=1`, keep trimming — empty string ⇒ null.
- Summary + detail responses gain **`display_name`** (server-owned — the
  fallback chain is a domain naming rule used by rail, dropdown, header,
  dashboard card, exports; it must not be copied into TS — R-003):
  `name` → else `planned_shop_date` formatted → else `created_at` formatted
  (S3). Format `"%a %d %b"` (e.g. `Sat 14 Jun`), + ` %Y` when not the current
  year. A list named by its *shop day* re-labels itself if the day changes —
  that's the point.
- Migration backfill: existing rows whose `name` exactly matches the
  auto-generated `"%a %d %b"` of their `created_at` are set to `null` (they
  were never user-chosen names); everything else is preserved as a real
  custom name.
- CSV/print/copy ("Copy of …") use `display_name`.

---

## 6. Axe StockItemChip (S1)

Answering S1 directly: used in exactly two places (§1.1), and **yes — axed
entirely**, component file deleted.

- **Shopping list rows** → plain item name as a link to `/stock/:id` (covers
  the chip menu's "Open detail"), with a small stock-level dot + level
  short-name beside it, and the existing alert states (low/expiring) as a
  tint on the dot. The chip's six-action overflow menu (add to primary list /
  mark restocked / push expiry / find substitutes / see recipes) does **not**
  come along: on a *shopping list* those are off-task detours (Charter:
  Effortless + Anti-creep) — the name link gets you to the full stock item
  page where all of that lives. The "on a list" cart indicator is redundant
  on the list itself.
- **Stock item detail → substitutes section** (`StockItemDetailPage.vue:380`)
  → a plain substitute row: name-link + the same level dot. No cross-feature
  menu. (Substitutes themselves are explicitly kept — see CLAUDE.md "Removed
  features": only the graph *page* was cut, not per-item substitutes.)
- New tiny component `StockLevelDot.vue` (R-001) shared by both call sites.

---

## 7. Rows: direct actions, proper price button (S12, S17) + shopping state

Row anatomy (one row, no kebab):

```
[≡] [☐] Item name → · ●Low · Fridge>Dairy     [offer chips…]  [- 2 +] [$4.50 ▾] [⇄] [→] [✕]
```

- **Tick** stays leftmost; touch target ≥ 44px while status = shopping (M3).
- **Name** = stock-item link (§6); product-only lines keep the `shopping_bag`
  glyph.
- **Offer chips** unchanged in function (cheapest-first, selected solid,
  preferred star) — they already satisfy "swap to another product" (M9).
- **Price button gets real** (S17): outlined button, `$4.50` or `Set price`,
  with a dropdown caret so it *reads* clickable; same editor popup
  (actual price + bought-from, the M8 receipt loop). On rows with an override,
  the little pencil-indicator merges into the button itself.
- **Direct icon buttons replace the kebab** (S12): swap-substitute `⇄` and
  remove `✕` — always visible, `dense` on desktop, comfortable on mobile.
  **Per-line "move to another list" is axed** (§12 Q2: remove here + add there
  is easy enough; the *bulk* "move unticked" survives in More because moving
  five leftovers by hand is not). Remove asks nothing and shows **no undo
  toast** (§12 Q4) — re-adding is one quick-add away.
- **Drag handle** stays draft-only. The L414 "index off" bug gets a repro check
  during the rebuild (FU, §9).
- **While status = shopping:** same page, two changes — tick targets enlarge
  (M3) and a **sticky footer** appears: doughnut-mini + `picked X of Y` +
  `Remaining $Z` + **Finish & restock** (primary) (M10–M12; no Pause, no
  grouping change — §12 Q3 + M2 revision). Quick add stays available mid-shop
  (today it's hidden — but realising you need milk *in the store* is exactly
  when you add it). Ticked lines sink to the bottom of their group with
  strikethrough.
- **Finish & restock → finish review modal** (M12 revised; **per-item pickers
  SUPERSEDED 2026-07-22 — see FU-582**): ticked items listed for review, one
  primary "Restock & finish" button, a muted note for unticked leftovers ("N
  unticked items stay on the list") and for product-only lines (not
  stock-tracked). The per-item stock-level buttons this section originally
  specified were **cut** — owner's call: someone who has just bought an item
  would never mark it as anything other than Stocked, so the choice was
  ceremony over a foregone conclusion. A part-used item is corrected on the
  stock item itself, not at finish time. The L336 "individual level marking"
  read does not transfer: cook mode consumes stock (level genuinely varies),
  shopping replenishes it (level does not).
- FU-097: rows adopt `formatQuantity()` while being rebuilt.

## 8. Toolbar (S5) + quick fixes

- Adopt **`PageToolbar`** (title "Shopping lists", actions slot) — consistent
  with Stocktake and the intended app pattern, instead of a third bespoke
  header.
- **Visible toolbar actions:** primary lifecycle button (Start shopping /
  Finish & restock / Reopen — status-driven), Quick add, Group-by (compact
  button-toggle: None / Location / Merchant), Refresh deals, Select (bulk).
  The quick-add *card* (a full-width card today) dies; quick add becomes a
  toolbar button → frees vertical space for actual list rows.
- **"More" overflow keeps only rare/destructive:** Save as template,
  Print/PDF, Move unticked to another list, Copy to new list, Clear all,
  Delete list. Rationale: S5 objects to *working* buttons being hidden;
  burying once-a-month and destructive actions is standard UX (and Clear
  all/Delete *should* have friction). **CSV export is deleted outright**
  (§12 Q1 — print covers the only real use), **Archive is deleted** (§12 Q2),
  and the visibility principle is promoted to an engineering rule
  (`ENGINEERING_STANDARDS.md`, see §12 Q2).
- **Quick fixes batched here:** tab title → "Shopping lists" (`routes.ts:137`,
  S4); flash fix `loading = ref(true)` + attempted-load guard (S6, §1.4);
  shopping-day banner de-duplicated into the shop-day button tint (§4).

### Visual polish (S10)

The structural changes above do most of S10's work (info hierarchy, real
buttons, no kebab-hunting, doughnut focal point). Plus: consistent card/border
usage via theme tokens only (R-002), one spacing rhythm (`q-mb-md` page
sections, `sm` intra-row), `body2` minimum for meta text, skeletons for rail +
info area + rows on every load path, and motion kept to the existing
`FadeTransition` + doughnut animate-on-change. No new colours, no new
component library.

---

## 9. Scope, sequencing, spin-offs

Suggested build order (each lands shippable):

1. **Quick wins** — tab title, flash fix, shop-day proper button, status badge,
   meta-row sizing, doughnut + totals into info area. (No backend.)
2. **Naming** — nullable name migration + `display_name` + clear-name UI.
3. **Rail + next-up** — desktop rail (virtualised, auto-scroll), mobile
   dropdown reorder, server `next_up_list_id`, route-guard swap.
4. **Rows + chip axe** — row rebuild (direct actions, price button),
   `StockLevelDot`, StockItemChip deletion (both call sites), FU-097 rows,
   L414 drag repro.
5. **Shop-mode merge** — shopping footer, enlarged ticks,
   quick-add-while-shopping, restock review modal (+ `/finish`
   `level_overrides`), route + page + `/stop` deletion, CSV-export removal,
   contextual-action and dashboard link updates, shortcut merge.

Follow-ups this proposal spawns/updates (logged in `DORA_FOLLOWUPS.md`):
- FU-158/159 → folded into this proposal (resolve when it ships).
- FU-160 (shopping-day alert) → stays open; fires off `planned_shop_date`
  after step 1.
- New: L414 drag-index bug — confirm in browser during step 4.
- New: `PageToolbar` adoption beyond Stocktake/shopping is opportunistic,
  not this proposal's scope (R-007 scope discipline).

## 10. Coverage table (mandatory cross-check)

Session bullets:

| # | Where covered |
|---|---|
| S1 | §1.1, §6 — two call sites, axed entirely |
| S2 | §1.2, §5 — nullable name, explicit-null clear |
| S3 | §5 — server `display_name` fallback chain |
| S4 | §8 quick fixes |
| S5 | §8 — PageToolbar, visible actions, rare-only overflow |
| S6 | §1.4, §8 — root-caused, one-line fix |
| S7 | §3.1/§3.2 — virtualised date-ordered rail / mobile dropdown |
| S8 | §4 — info area + doughnut resurrected (§1.5 history) |
| S9 | §3.3 — server-owned `next_up_list_id` |
| S10 | §8 visual polish + whole-proposal structure |
| S11 | §2 — full inventory M1–M15 with dispositions, then merge |
| S12 | §7 — kebab removed, direct row actions |
| S13 | §3.1/§3.2 — icons kept |
| S14 | §4 — proper outlined shop-day button |
| S15 | §4 — heading-scale status badge |
| S16 | §4 — meta row at body2 |
| S17 | §7 — real price button with caret |
| S18 | §2 (M-cut rationale), §7 (quick-add-while-shopping), §8, §9 spin-offs |

Original L400–L421 (`Feedback _ Fixes - as of [06-Jun-2026].md`):

| Bullet | Status |
|---|---|
| L402 planned shop day | Built (Chunk 7); §4 makes it discoverable |
| L403 shopping-day alert | Out of scope here — FU-160, after step 1 |
| L404 merge overview into detail | Shipped (v1 Chunk 5) |
| L405 desktop right panel, date-ordered | §3.1 |
| L406 mobile dropdown | §3.2 |
| L407 primary detail → top info area | §4 |
| L408 archived lists in same list | §3.1 (one continuum, muted) |
| L409 landing pick by date | §3.3 (refined to "next up after last completed") |
| L410 primary-list rethink | Shipped (v1 Chunk 2, inferred target) — unchanged |
| L414 drag-drop index off | §9 — repro during row rebuild (new FU) |
| L418 substitutes in store | §2 M9 + §7 — offer chips + swap action kept on-row |
| L419 price as you go / list-becomes-receipt | §2 M8, §7 — preserved through merge |
| L420 finish → restock loop | Shipped (`/finish`); §7 keeps it as footer primary |
| L421 undo/reopen review | Shipped server-side (`finish_snapshot` restore); unchanged here |

## 11. Open questions

*All four resolved 2026-06-12 — see §12. Kept for the trail.*

**Status: reconciled 2026-07-13 (FU-382 / FU-364 remediation).** Every question
below was answered in §12 *and* has now been verified closed against the shipped
code — the proposal built and landed (CHANGELOG "Shopping lists UX v2 — one page
for the whole shop"). All four are ✅ closed by shipped behaviour; none remain
open. Per-question evidence annotated inline.

1. ✅ **CLOSED — Zero-overflow toolbar?** §8 keeps rare/destructive actions in one
   "More" menu. If you want literally everything visible, say so — it costs a row of
   buttons on mobile.
   *Shipped as decided (lean "More" menu, not zero-overflow): working actions
   (quick add, group-by, refresh deals, select, lifecycle) are visible toolbar
   buttons; only template/print/move-unticked/copy/clear/delete live in a labelled
   "More" menu; CSV export removed end-to-end. Promoted to engineering rule R-012.
   Evidence: CHANGELOG "Toolbar instead of ellipsis menus (new rule R-012)".*
2. ✅ **CLOSED — Rail kebab** (§3.1) — copy/archive/delete stay behind a kebab *on rail
   items only*. OK?
   *Shipped: `ShoppingListRailItem.vue:34–59` renders a `more_vert` kebab menu
   scoped to rail items with "Copy to new list", "Copy unticked → new", and
   "Delete list". Archive was dropped (comment at lines 70–71 cites §12 Q2 —
   "lists are finished or deleted"), consistent with the decision.*
3. ✅ **CLOSED — Pause button** (M13): keep a quiet way to drop from `shopping` back to
   `draft`, or is Start → Finish enough?
   *Shipped as "no Pause": the `POST /stop` endpoint was deleted with the shop-mode
   page; lifecycle is Start shopping → Finish & restock → (Reopen). Evidence:
   CHANGELOG "The `/stop` ("pause") endpoint is gone".*
4. ✅ **CLOSED — Remove-line with no confirm** (§7) — comfortable, or want an undo toast?
   *Shipped as "no undo toast": `ShoppingListDetail.vue:2589` `onRemoveLine` deletes
   the line and shows only a plain positive notify with an inline comment citing
   §12 Q4 (lines 2639–2640). The broader undo question flagged in §12 Q4 was
   subsequently resolved wholesale by FU-163 — app-wide undo (`useUndo`,
   tick/untick undo) and even shopping-list Reopen were removed (CHANGELOG
   "App-wide undo / shopping-list Reopen — gone (FU-163)"), so this is doubly
   settled. (Note: a product-only line still shows a scoped "also remove the
   linked stock item?" prompt — that is the Cart-Button rule-4 dialog, FU-131,
   not a remove-confirm, and does not reopen this question.)*

## 12. Decisions (2026-06-12 review)

- **Q1 — More menu allowed, but lean.** Hidden = undiscoverable, so keep it
  to genuinely rare/destructive actions. **CSV export removed from the app**
  — print is the only export anyone would use here.
- **Q2 — visibility becomes a standing engineering rule** (added to
  `ENGINEERING_STANDARDS.md`): features stay visible/easily reachable;
  overflow menus are for rare/destructive actions only. **Archive removed**
  — with the status enum it was just "done without restock", a redundant
  third path (finish or delete). **Per-line "move to another list" removed**
  — remove here + add there is easy; bulk "move unticked" stays (real work
  saver).
- **Q3 — no Pause.** Start shopping → Finish & restock is the whole
  lifecycle; `/stop` endpoint deleted as orphaned.
- **Q4 — no undo toast on remove-line.** Bigger: user is questioning undo
  affordances **app-wide** and leaning toward removal — logged as a
  follow-up (relates to FU-026's undo-oddity audit and the `useUndo`
  registry). Shopping-list *Reopen* (server-snapshot restore, L420/421) is
  kept for now as the one reviewed undo path, explicitly flagged as a
  candidate in that audit.
- **M2 revision — no location semantics in shopping.** Stock-item location
  is a *home* concept (where it lives in your pantry), not a shelf concept.
  Group-by-location stays available manually but is never a default or a
  shopping recommendation, and nothing in the shop flow asks for location
  data.
- **M12 revision — restock review modal**: ticked-item summary with
  per-item level buttons (default Well-Stocked) + single Restock & finish
  button. Fewer clicks for the common case, full control for the rest.

---

*From the original spec (`docs/00_original_spec/Feature Boards/Shopping Lists.md`):
skimmed per protocol. It's a flat wishlist almost entirely shipped (multi-list,
templates, groups, totals, ticks, copy-archived, start/finish, review-restock).
Two unshipped fragments noted: **(consider)** "warn when deleting a list with
unchecked items" — folds naturally into §8's Delete placement; **(superseded)**
"ISO vs DD-MMM name format option" — §5's display-name fallback makes the
stored date-name obsolete, and the spec itself questioned the option's value.
Nothing else worth extracting; the board pre-dates the status-enum redesign.*
