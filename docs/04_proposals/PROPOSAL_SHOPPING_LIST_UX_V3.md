# Shopping List UX v3 — the overview card

**Status:** **BUILT 2026-08-29** (same-day approve + build). Driven live across
all three faces at 1280px and 375px; suites green (`vue-tsc`, `eslint src/`,
560 vitest). Three deviations from this document are recorded in §10.
**Date:** 2026-08-29 (written), 2026-08-29 (built).
**Extends:** `PROPOSAL_SHOPPING_LIST_UX_V2.md` (BUILT 2026-06-12). v2 merged
overview-into-detail, killed shop mode as a separate page, and set the toolbar
convention. v3 does not re-litigate any of that — it replaces the **top section**
of the detail page, which v2 left as a loose header block plus two stranded cards.
**Source feedback:** the 2026-08-29 owner session (V1–V11 below), plus the six
follow-on calls answered in the same session (§7).

---

## 0. Feedback being addressed (verbatim, numbered)

| # | Bullet |
|---|---|
| V1 | Swap the pencil and the state chip |
| V2 | Move set shop date to the toolbar as a standard toolbar button |
| V3 | Why does the whole page refresh when I pick a shop date? |
| V4 | Remove the hint for the list name (moves the UI too much) |
| V5 | Make the state pill/chip a bit bigger/fancier |
| V6 | Use a modal for mobile editing the list name, the input looks awkward when it pops up and moves UI |
| V7 | Why does the state disappear (e.g. draft) when editing the list name? |
| V8 | I feel we could do a much better job with the top section of draft mode. Lets build a better, all in one header and make more use of a collapsible card design. The whole "where you'll spend/shop" can be hidden inside it, the creation date hidden too, shop day can be just text, button in toolbar is responsible for setting it now. Estimated cost could be the main figure shown always, then the details in the expanded card. Start shopping button could be incorporated into this card as well. It can be a polished overview card with detail review. The name, edit pencil, state |
| V9 | I don't like the export button here, split it out to the two sub items so they are their own primary toolbar buttons |
| V10 | Can we move new list to only be with the shopping lists list? Having it right next to the add item to this list button is confusing. Must ensure it still works well with no lists. I think then the add to this list button can be styled like the current new list button |
| V11 | The order by controls looks odd on its own like it is. Not sure what to do with it. …The redesigned overview card can be a slimmer version for shop mode. E.g. no need for creation date when…shopping. The order by controls could possibly be part of that as well |

---

## 1. Audit findings (what the code actually says)

Verified 2026-08-29 against `ShoppingListDetail.vue` (3825 lines, one SFC).

1. **V3 and V7 are bugs, not design calls.**
   - V3: `savePlannedDate()` (`:2359`) → `refreshAll()` (`:2561`) → `load()`
     (`:2505`), and `load()` sets `detail.value = null` at `:2511`. The template's
     `FadeTransition` (`:267`) switches on `loading && !detail`, so nulling flips
     the whole page to the skeleton branch and back. A sibling
     `refreshDetailQuietly()` (`:2535`) already re-reads without blanking — it is
     used for optimistic tick reconciliation and is the correct call here.
     The same blanking hits `clearPlannedDate()` (`:2375`) and `saveName()`
     (`:2594`), which is a second cause of V6's "moves UI".
   - V7: the `v-if="!editingName"` template at `:309` wraps the title, the status
     pill **and** the pencil. All three are replaced by the bare input.

2. **There is no shopping-lists index page in practice.**
   `ShoppingListsOverview.vue` is 82 lines of empty/error state, and
   `routes.ts:124` redirects `/shopping-lists` → `/shopping-lists/:id` whenever a
   list exists. The only live "list of lists" is the desktop rail and the mobile
   `BaseDropdown`. V10's destination is therefore the rail/dropdown, not a page.

3. **The toolbar has no shop-date button and no order-by control.** Shop date is
   a header meta-row button (`:365`); order-by is a bare bar at `:606` for draft,
   **duplicated** inside `ShoppingListRunFace.vue:6` for shop mode.

4. **Totals are already server-owned.** `:2237-2243` reads `detail.totals`
   (`total_price` / `total_savings` / `remaining_price`) and carries an explicit
   state-ownership Type-B comment. `by_store` buckets pass straight to
   `StoreSpendCard` with no client aggregation. The overview card inherits this —
   **it must not re-sum lines** (R-003).

5. **The shop-mode sticky footer is broken, and V11 lets us delete it.**
   `.sld-shop-footer` (`:1188`, CSS `:3574`) is `position: sticky; bottom: 8px;
   z-index: 3`, the **last child of the content column**, with **no spacer, no
   container `padding-bottom`, and no `env(safe-area-inset-bottom)`**. It floats
   over the last list rows and over the danger footer for the whole scroll.
   Worse: `DoraBubble` is `position: fixed; bottom 18px + safe-area; z-index:
   3000` (`DoraBubble.vue:396`) and lands exactly on the "Finish & restock" CTA.
   Quasar toasts were already lifted 112px for this reason (`app.scss:54`); the
   footer never was.

6. **Collapse defaults: no persistence anywhere, one exception.** Every
   collapsible in the app defaults closed and stores nothing —
   `PantryBeliefCard.vue:74`, `RecipeNutritionCard.vue:227/266`,
   `RecipeDetailPage.vue:1219`, `FilterToggleButton.vue:69`, and ~11 bare
   `q-expansion-item`s. `useFilterPanelExpanded.ts` had localStorage **removed**
   by owner call 2026-08-20. The lone survivor is
   `StockLocationsSettings.vue:135`. **Correction to the session assumption:**
   `StoreSpendCard.vue:113` is `ref(!props.collapsible)`, and both callers pass
   `:collapsible="$q.screen.lt.md"` — so it is **expanded on desktop, collapsed
   on mobile**, and that ref is evaluated once at setup, so a resize never
   re-evaluates it (spun out as **FU-783**).

7. **There is no generic `CollapsibleCard.vue`.** `DashboardCard.vue` is the
   shared card shell but has no collapse. `StoreSpendCard.vue` holds the closest
   pattern (header toggle + collapsed one-line `summaryLine` at `:22-24`).

8. **Receipt mode is a genuinely different animal.** `ShoppingListReceiptFace.vue`
   already renders its own header (`:27-44`) with an `h5` actual total and a
   "Shopped {date}" caption, its own line list, a "Didn't buy (n)" chip row, and
   its **own** `StoreSpendCard` with `tense="receipt"` (`:145`). The page's
   `TripCard` and plan `StoreSpendCard` are both `v-if="planFace"` (`:410`), so
   **`total_savings` is never shown on the receipt face at all**.

---

## 2. The overview card

One component, `components/shoppingList/ShoppingListOverviewCard.vue`, rendered
in all three faces with a `face` prop. It replaces the header block (`:306-403`),
`TripCard`, the plan `StoreSpendCard`, the order-by bar, and the shop-mode sticky
footer.

### 2.1 Anatomy (collapsed — always visible)

```
┌──────────────────────────────────────────────────────────┐
│  [ Draft ]  Weekly shop            ✏         ⌄           │  ← identity row
│                                                          │
│  $184.20                          Shopping Sat 31 Aug    │  ← figure row
│  Estimated cost                                          │
│                                                          │
│  [ Sort: Aisle ▾ ]                    [ Start shopping ] │  ← control row
└──────────────────────────────────────────────────────────┘
```

- **Identity row** — state chip **first**, then name, then pencil (V1). The chip
  is upsized from the current `sld-status-pill` to a proper badge: `--space-2`
  padding, chip-height ≥24px, `--font-size-sm`, tonal background + matching text
  per D-002 contrast floors, `--radius-pill` (V5). Never a bare colour — the word
  always shows (D-013).
  **The chip, the name and the pencil are three siblings** — nothing wraps them
  in a shared `v-if`, which is the structural fix for V7.
- **Figure row** — the headline number, `text-h5`, with a caption label beneath.
  Per face: draft = **estimated cost**, shop = **remaining spend**, receipt =
  **actual spent**. Right side is the shop-day line as plain text (V8), tinted by
  the existing `shopDayToneClass` (`:2340`).
- **Control row** — the sort control (V11) and the face's primary action (V8/§7.3).
- **Chevron** toggles the detail region.

### 2.2 Anatomy (expanded)

Adds, in order: the `StoreSpendCard` ("Where you'll spend it" / "Where you
shopped"), the secondary figures (savings, "N from what you last paid", estimated
line count), and the created date. Nothing else moves.

### 2.3 Per-face matrix

| | Draft | Shopping | Receipt |
|---|---|---|---|
| Headline figure | Estimated cost (`totals.total_price`) | **Remaining** (`totals.remaining_price`) | Actual spent (`totals.total_price`) |
| Progress ring | — | yes, left of figure, + "N left to pick" | — |
| Shop day | text, tinted | text, tinted | "Shopped {date}" |
| Created date | expanded only | **absent entirely** | expanded only |
| Sort control | yes | yes | — (receipt is a record, not a job) |
| Primary action | Start shopping | Finish / Finish early | Put away |
| Secondary action | — | — | Amend (ghost) |
| Expanded: StoreSpend | yes | yes ("Where you're spending") | **no** — the receipt face renders its own at `:145` |
| Expanded: savings | yes | yes | **yes — new**, closes the gap in §1.8 |
| Expanded: total | — | yes (full total, since headline is remaining) | — |

Receipt is deliberately the slimmest: no sort, no StoreSpendCard (it would
double up), and the card reduces to identity + actual total + shop date +
Put away, with savings and created date behind the chevron.

### 2.4 Rules of engagement

- **Collapsed on mount, every visit, every face, no persistence** (§7.6). This
  matches every other collapsible in the app bar one; it is a *change* only for
  desktop `StoreSpendCard`, which currently opens expanded.
- **Reads `detail.totals` only.** No client re-summing (R-003, and the existing
  Type-B comment at `:2237`).
- **Built on a new shared `CollapsibleCard.vue`** (§7.8), extracted from the
  `StoreSpendCard` pattern and adopted by `StoreSpendCard` + `PantryBeliefCard`
  in the same unit so the extraction is proven by more than one caller.
- **D-004:** chevron, pencil and every control ≥44px on touch.
- **D-005:** pencil and chevron are icon-only → `aria-label` + tooltip, and the
  chevron carries `aria-expanded`.

---

## 3. Toolbar

Final composition, left to right. New list **leaves** (V10); shop date **arrives**
(V2); Export **splits** (V9); the four lifecycle actions **leave** for the card.

| Button | Was | Now |
|---|---|---|
| **Add item** | secondary, next to New list | **primary** styling — inherits the look New list vacates (V10) |
| **Set shop date** | header meta-row `:365` | toolbar, **draft only — vanishes once shopping starts** (§7.4) |
| Log price | toolbar | unchanged (`runFace && moneyEnabled`) |
| Templates | toolbar | unchanged |
| Refresh deals | toolbar | unchanged |
| **Print / Save as PDF** | inside Export menu `:113` | own toolbar button (V9) |
| **Save as template** | inside Export menu `:124` | own toolbar button (V9) |
| ~~Export~~ | `q-menu` `:104` | **removed** — the menu shell goes |
| ~~New list~~ | `:34` | **moves to rail + dropdown** (§4) |
| ~~Start shopping / Finish / Amend / Put away~~ | `:141-199` | **move to the card** |

Net: 8 → 7 in the widest state, and the confusing New-list/Add-item adjacency is
gone. The owner accepted a fuller bar for now (§7.2); FU-738's toolbar thinning
remains open and is unaffected.

**Copy change:** "Finish & restock" → **"Finish"**, "Finish early & restock" →
**"Finish early"** (§7.3). The restock is understood; the confirm dialog already
spells it out.

---

## 4. New list moves to the rail (V10)

- **Desktop:** a full-width "New list" button pinned at the **top** of the lists
  rail, above the `ShoppingListRailItem` rows.
- **Mobile:** a pinned first entry inside the existing `BaseDropdown` list picker,
  visually separated from the list rows.
- **Empty state:** `ShoppingListsOverview.vue` keeps its own New-list CTA — it is
  the only reachable surface when no list exists, and `routes.ts:124` only
  redirects when one does. This is the "must still work with no lists" guard;
  it needs a test, since the redirect makes the page easy to forget.

Both entry points open the existing `NewListDialog.vue`. No new creation path.

---

## 5. Name editing (V4, V6, V7)

- **Remove the placeholder hint** — `dateFallbackName` (`:2579`) stops being the
  input placeholder (V4). The "blank clears the custom name" behaviour stays; it
  is explained by helper text inside the modal instead, where it cannot shift
  layout.
- **Mobile (`$q.screen.lt.md`): a `BaseDialog`.** Pencil opens it; the card
  underneath does not move (V6). Save / Cancel buttons, no blur-to-save.
- **Desktop: inline stays**, but as a sibling swap — only the name span is
  replaced by the input; chip and pencil hold their place (V7).
- **Save quietly** — `saveName()` calls `refreshDetailQuietly()`, not
  `refreshAll()` (§1.1).

---

## 6. Bug fixes folded in

| Bug | Fix |
|---|---|
| V3 full-page flash on date save | `savePlannedDate` / `clearPlannedDate` / `saveName` → `refreshDetailQuietly()`. Audit `load()`'s other callers in the same pass; the `detail = null` at `:2511` should arguably only happen on **list switch**, not on refresh. |
| V7 chip vanishes while renaming | Sibling swap, §5 |
| Sticky footer overlaps content + DoraBubble covers the CTA (§1.5) | **Deleted.** The card replaces it (§7.9). `.sld-shop-footer` markup and CSS both go. |
| Order-by bar duplicated in two places (§1.3) | Single control in the card, shared by draft and shop; the copy in `ShoppingListRunFace.vue:6` is removed |

---

## 7. Open decisions — closed

All eleven decisions were put to the owner on 2026-08-29 and answered. Recorded
here so no fork is left live (the FU-364 pattern).

1. **Where does New list go?** → Option A: top of the rail + in the mobile
   dropdown. Not a rebuilt index page. (§4)
2. **Toolbar count?** → Accept a fuller bar for now. FU-738 unaffected. (§3)
3. **Do all lifecycle actions move to the card, or only Start shopping?** →
   **All of them** — they share the same meaning/responsibility. Plus rename
   "Finish & restock" → "Finish". (§2.3, §3)
4. **Is Set shop date visible while shopping?** → **Vanishes.** Not relevant once
   you are already shopping. (§3)
5. **Mobile name-edit entry point?** → Clarified: the complaint is that today's
   pencil spawns an input *below the dropdown* and shoves the UI. Fix is the
   modal; the entry point stays the existing pencil. (§5)
6. **Expansion persistence?** → **Reset to collapsed on every visit.** Owner's
   read that this matches the rest of the app is correct with one exception —
   desktop `StoreSpendCard` currently opens expanded and will change. (§2.4, §1.6)
7. **Order-by controls?** → Owner took the recommendation: compact segmented
   control in the card's collapsed control row, shared by draft and shop. (§2.1)
8. **Componentise the collapsible?** → **Yes — always componentise where there is
   a candidate**, for app-wide consistency. New `CollapsibleCard.vue`, adopted by
   `StoreSpendCard` + `PantryBeliefCard` in the same unit. (§2.4)
9. **Slim shop card vs sticky footer?** → **Replace.** The footer already has
   overlap problems (owner-reported, confirmed §1.5). (§6)
10. **Receipt mode?** → Owner took the recommendation: slim card, no sort, no
    second StoreSpendCard, savings surfaced for the first time. (§2.3)
11. **Shop-mode headline figure?** → **Remaining spend**, with the full total in
    the expanded region. (§2.3)

---

## 8. Scope, sequencing, spin-offs

**In scope:** the card, the toolbar recomposition, New-list relocation, the name
modal, the three bug fixes, `CollapsibleCard.vue` extraction, deletion of
`TripCard.vue` (absorbed) and `.sld-shop-footer`.

**Out of scope, logged:**
- **FU-783** — `StoreSpendCard.vue:113` evaluates `ref(!props.collapsible)` once
  at setup, so resizing across the `lt.md` breakpoint never re-evaluates
  expansion. Pre-existing; fix opportunistically during the extraction.
- **FU-784** — `DoraBubble` (z-3000, fixed bottom-right) has no placement budget
  against page-level bottom chrome. Deleting the shop footer removes today's
  collision but not the class of bug; D-009 says this should be systematic.
- **FU-738** — toolbar thinning. Still open, still deferred by owner.
- `ShoppingListDetail.vue` is 3825 lines in one SFC. Not this unit's job, but the
  card extraction should take real logic with it, not just markup (R-001).

**Sequencing:** (1) bug fixes — they are one-liners and independently verifiable;
(2) `CollapsibleCard.vue` + adopt in two existing callers; (3) the overview card,
draft face; (4) shop + receipt faces, delete the sticky footer; (5) toolbar +
New-list relocation.

---

## 9. Coverage table (mandatory cross-check)

The 2026-08-29 session bullets. This batch is surface-scoped (shopping lists), so
the table maps the V-bullets; no bullet in
`Feedback _ Fixes - as of [06-Jun-2026].md` is newly claimed here — that file's
shopping-list bullets (L400–L421) were closed by v2.

| # | Bullet | Section | Disposition |
|---|---|---|---|
| V1 | Swap pencil and state chip | §2.1 | Covered |
| V2 | Set shop date → toolbar button | §3 | Covered — draft only (§7.4) |
| V3 | Whole page refreshes on shop-date pick | §1.1, §6 | Covered — bug, `detail = null` in `load()` |
| V4 | Remove list-name hint | §5 | Covered |
| V5 | Bigger/fancier state pill | §2.1 | Covered |
| V6 | Modal for mobile name editing | §5 | Covered |
| V7 | State disappears while editing name | §1.1, §5 | Covered — bug, shared `v-if` at `:309` |
| V8 | All-in-one collapsible overview card for draft | §2 | Covered |
| V9 | Split Export into two primary toolbar buttons | §3 | Covered |
| V10 | New list moves to the lists list; Add item inherits its styling | §4, §3 | Covered — rail + dropdown; empty state guarded |
| V11 | Order-by controls; slim card for shop mode | §2.1, §2.3 | Covered — sort in the card, deduped across faces |

---

## 10. What the build changed (deviations from §2–§8)

Three, all decided during the build and all narrowing rather than widening:

1. **Renaming is a dialog on desktop too** (§5 specified an inline sibling swap
   there, modal only on mobile). Once the card gave the name a stable row, an
   inline input was *possible* — but the complaint it answers ("the input looks
   awkward when it pops up and moves UI") was true at both widths, and the
   structural fix for the vanishing status chip is the same either way. One
   editor beat two for a control used this rarely. Verified: renaming shifts the
   card by `dy=0.0 dh=0.0` and the pill stays visible throughout.
2. **`StoreSpendCard` gained a third tense, `shop`.** §2.3 called for "Where
   you're spending" mid-shop, but the component only had `plan` and `receipt`,
   and the run face was reading the past tense — "Where you spent it" on a trip
   with $7.99 still to spend. The component already centralises every wording so
   its callers can't drift, so the third tense went there rather than into a
   caller.
3. **The finish action is one label, "Finish", on both the button and the
   dialog.** §3 renamed only the button, and only its `& restock` half, leaving
   "Finish" / "Finish early" against a dialog headed "Finish early & restock" —
   one action under three names. Owner call closed it: *"people know if they are
   finishing early or not"*. So the button is always **Finish** and the dialog
   is always **Finish shopping**. Neither dropped word is lost — the body
   enumerates every item about to be restocked, and the leftovers section
   appears exactly when you *are* finishing early, which is a decision you must
   act on rather than an adjective in a heading.

**One thing §1.5 got wrong, corrected here:** the "Oops, something went wrong"
toast on viewport resize is **not** caused by anything in v3. It was chased
during the verify pass, initially blamed on the new card's nested transitions,
and then disproved — hiding the card changes nothing, and the dashboard and meal
planner reproduce it identically. The observer is
`components/menu/MainMenuButtonStrip.vue:47`. Logged as **FU-785**, which also
records the worse half: `window.onerror` runs `executeRollbacks()` for it.

## 11. From the original spec

`docs/00_original_spec/` has no Feature Board or Feature Note matching the
shopping-list surface by filename (checked 2026-08-29). Nothing to extract.
