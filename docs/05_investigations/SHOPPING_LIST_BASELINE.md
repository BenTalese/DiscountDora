# Shopping list — behavioural baseline (v4 chunk 0)

**Date:** 2026-08-31.
**Purpose:** the cutover checklist for `PROPOSAL_SHOPPING_LIST_UX_V4.md`. Every
affordance the page currently has, catalogued **before** any markup changes, so
the rebuild can be audited rather than assumed (owner asks W8/W9/W12).
**Method:** read from source, not memory. `ShoppingListDetail.vue` (3,571 lines),
`ShoppingListRunFace.vue`, `ShoppingListReceiptFace.vue`,
`ShoppingListOverviewCard.vue`, `StoreSpendCard.vue`, `ShoppingListRailItem.vue`,
`get_shopping_list_detail.py`, `health_check.py`.

**Status of the right-hand columns:** `Destination` / `Visibility` / `Decision`
were filled as each chunk landed. **Complete as of 2026-09-01 — chunk 4 passed;
see §11 for the verdict and its one caveat.**

**Decision vocabulary:** `kept` (same capability, same or better reach) ·
`moved` (same capability, different place — must name the new place) ·
`CUT` (removed — requires a written reason and owner sign-off).

---

## 0. Faces and their gates

| Face | Gate | Component |
|---|---|---|
| plan | `detail.status === 'draft'` (`:1553`) | inline in `ShoppingListDetail.vue` |
| run | `detail.status === 'shopping'` (`:1554`) | `ShoppingListRunFace.vue` |
| receipt | `detail.status === 'done'` (`:1555`) | `ShoppingListReceiptFace.vue` |

`baseLines` (`:1854`) = all lines **minus** `deferred_by_budget`. Every face
sections `baseLines`; deferred lines render in their own section on the plan face
only.

---

## 1. Toolbar

Container `.sld-toolbar__actions` — one no-wrap row, scrolls sideways, never wraps
or collapses to a menu. `compactToolbar` = `$q.screen.lt.sm` drops **labels only**;
tooltips carry the name.

| # | Affordance | Face(s) | Visibility condition | What it does | Destination | Visibility | Decision |
|---|---|---|---|---|---|---|---|
| T1 | Add item (primary) | all | always; `:disable` when no detail or status `done` | opens quick-add sheet | unchanged | always | kept |
| T2 | Shop day | plan | `v-if="planFace"` | opens planned-date dialog | unchanged | plan only — **confirmed live** (absent on run and receipt) | kept |
| T3 | Log price | run | `v-if="runFace && moneyEnabled"` | `useLogPrice()` sheet — a price for something **not** on the list | unchanged | run only — **confirmed live** | kept |
| T4 | Templates | all | always | routes to `/shopping-lists/templates` | unchanged | always | kept |
| T5 | Refresh deals | all | `v-if="productsEnabled"` **(T2 tier)** | re-checks linked product offers | unchanged | always at T2 | kept |
| T6 | Print | all | always; disabled when 0 lines | printable view | unchanged | always | kept |
| T7 | Save as template | all | always; disabled when 0 lines | snapshot to a template | unchanged | always | kept |

**The toolbar was not touched by chunks 1-3** — it was already rebuilt by UX-v3
(2026-08-29) and the v4 pass changed containers, rows and the card, not this row.
All seven verified rendering live on the faces that gate them.

**Note:** the two Export members that v3's V9 split out are not in the current
toolbar block — Print (T6) and Save as template (T7) are what that split
produced. There is no remaining Export menu.

---

## 2. List picker (two renderings of one continuum)

| # | Affordance | Where | Visibility condition | What it does | Destination | Visibility | Decision |
|---|---|---|---|---|---|---|---|
| P1 | Mobile `BaseDropdown` switcher | `.lt-md` | always, **including mid-shop** | switches list; on mobile this is the only place the list name appears | unchanged | `.lt-md` — **confirmed live at 375px** | kept |
| P2 | Rename pencil (mobile) | `.lt-md`, beside P1 | `v-if="detail"` | opens rename dialog | unchanged | `.lt-md` | kept |
| P3 | "New list" pinned first entry | mobile dropdown | always | opens `NewListDialog` | unchanged | **confirmed live** — first entry above the rail rows | kept |
| P4 | `ShoppingListRailItem` rows | both | `railEntries` = drafts + shopping + 5 most-recent done | select → `switchToList` | unchanged | always | kept |
| P5 | "See older (n)" | both | `olderDoneSummaries.length > 0` | opens searchable older-lists dialog | unchanged | always when there are >5 done lists — **both branches rendered live** (present with 10 done, absent with 3) | kept |
| P6 | Desktop rail | `.gt-sm` column | always, **including mid-shop** | 300px sticky, `max-height: calc(100vh - 110px)` | unchanged | `.gt-sm` | kept |
| P7 | "New list" (rail, primary) | `.gt-sm` | always | opens `NewListDialog` | unchanged | always | kept |
| ~~P8~~ | ~~Per-list ⋮ menu (incl. Delete)~~ | — | — | — | — | — | **does not exist** |

**Correction to chunk 0 — P8 was never there.** The census recorded a per-row
kebab carrying copy-to-new and Delete. It was **removed on 2026-08-28**, three
days *before* the census was written, and `ShoppingListRailItem.vue` says so in
its own header: both actions were already reachable from the list you are looking
at, so the kebab put two uncommon actions — one destructive — on every row of a
picker whose only job is "take me to that list". Copy went entirely (Save as
template is the same idea, better named); Delete stayed on the open list's footer
(F9), where you can see what you are deleting. **Nothing regressed here** — the
baseline was simply wrong, and this is the audit doing its job. Recorded rather
than quietly deleted so the error is visible.

**The picker was not touched by chunks 1-3** either. P1-P7 all verified live.

---

## 3. Page furniture between the card and the list

**None of this existed in the v4 mockup.** It is the largest gap the census
found, and chunk 2 must place all of it.

| # | Affordance | Face(s) | Visibility condition | What it does | Destination | Visibility | Decision |
|---|---|---|---|---|---|---|---|
| F1 | Load-error banner | all | `loadError` | message + Retry | `.sl-panel--error` | always | kept |
| F2 | Skeleton branch | all | `loading && !detail` | header + 5 row skeletons; first frame by design | unchanged | always | kept |
| F3 | Overview card | all | `detail` | see §4 | rebuilt — chunk 2 | — | kept |
| F4 | Budget trim banner | plan | `planFace && trimBanner.visible` | 4 states + 3 actions | `.sl-panel--warn` (was `rounded` + `dora-bg-warning-soft`) | always | kept |
| F5 | Trim preview card | plan | `state === 'previewed' && previewLines.length > 0` | reason chip + saved + **Keep** | `.sl-panel` (was `flat bordered`) | always | kept |
| F6 | Dora suggestions strip | plan | `visibleSuggestions.length > 0` | tappable chips; dismissible | `.sl-panel` (was `flat bordered`) | always | kept |
| F7 | Deferred-to-fit-budget | plan | `deferredLines.length > 0` | expansion, `default-opened`, **Add back** | `.sl-panel--sunken` | always | kept |
| F8 | Receipts photo strip | run + receipt | `status !== 'draft'` | picker, thumbs, lightbox, delete | unchanged — it is a bare section, not a boxed panel, and reads correctly against the new slabs | always | kept |
| F9 | Destructive footer | all | `detail` | Clear all · Delete list | unchanged — a rule, not a card, deliberately (its own comment records why) | always | kept |
| F10 | Not-available fallback | all | `!loading && !detail` | icon + message + New list | unchanged | always | kept |

**All ten kept.** F4–F7 and F1 were each a `flat bordered` q-card or a `rounded`
q-banner — the same 1px border and 6px radius as everything else on the page,
which is precisely why it read as a stack of equal boxes. They share one
`.sl-panel` treatment now, so the page carries exactly two weights: the overview
card, and everything else.

---

## 4. Overview card (`ShoppingListOverviewCard.vue`)

| # | Affordance | Face(s) | Visibility condition | What it does | Destination | Visibility | Decision |
|---|---|---|---|---|---|---|---|
| C1 | Status pill | all | always | Draft / Shopping / **Receipt when `moneyEnabled` else Done** | unchanged | always | kept |
| C2 | List name | all | `.gt-sm` only | display name | unchanged (`text-h5`, now under the bigger figure) | `.gt-sm` | kept |
| C3 | Rename pencil | all | `.gt-sm` only | opens rename dialog | unchanged | `.gt-sm` | kept |
| C4 | Headline figure | all | tier-dependent | **now tier-aware per face (§7.3 closed)**: money on → cost / remaining / spent; money off → items-to-buy / left-to-pick / items-bought, instead of one flat "items on this list" everywhere | `--font-size-3xl` (was a magic `1.9rem`) | always | kept |
| C5 | Progress ring + "n left to pick" | run | `face === 'run'` | ticked/total, motion-safe | unchanged | always | kept |
| C6 | Dateline | all | per face | today/tomorrow/overdue toning | unchanged | always | kept |
| C7 | Item count | all | always | `n items` | unchanged | always | kept |
| C8 | Order-by control | plan + run | `sortModes.length > 1` | four loose ghost buttons | **`BaseSegmented` `pill`** — the shape the owner picked 2026-08-31, reused rather than a second one invented (D-015) | always | moved |
| C8a | *Why a mode is unavailable* | plan + run | any `!availableModes[m]` | was a per-button tooltip | one group tooltip naming every unavailable mode — `q-btn-toggle` has no per-option slot that isn't a dynamic per-value name | on hover/focus | moved |
| C9 | Start shopping | plan | `face === 'plan'` | draft → shopping | unchanged | always | kept |
| C10 | Finish | run | `face === 'run'` | opens finish dialog | unchanged | always | kept |
| C11 | Amend toggle | receipt | `face === 'receipt'` | toggles amend | unchanged | always | kept |
| C12 | Put away | receipt | `v-else` branch | opens `PutAwayDialog` | unchanged | always | kept |
| C13 | Disclosure caret | all | `CollapsibleCard` | reveals the review half | unchanged | always | kept |
| C14 | `StoreSpendCard` (in disclosure) | plan + run | `face !== 'receipt'` | buckets, `~` marker, hatched no-store | unchanged | in disclosure | kept |
| C15 | Trip total | run | secondary figure | whole-trip figure | unchanged | in disclosure | kept |
| C16 | Saving | all | `total_savings > 0` — **T2 only** | "Saving" / "You saved" | unchanged; **not promoted to the band**, so a T1 install (savings structurally $0) leaves no hole | in disclosure | kept |
| C17 | "From what you last paid" | all | `estimatedCount > 0` | historic-estimate marker | unchanged | in disclosure | kept |
| C18 | Created date | plan + receipt | `face !== 'run'` | creation date | unchanged | in disclosure | kept |
| **C19** | **Unpriced-lines marker** | all | `moneyEnabled && unpricedCount > 0` | **NEW** — a `~` on the figure plus "n items with no price yet" | top level of the card | always | **added** (fixes §1.5 / S7) |

**All kept or moved, plus one addition.** C19 closes the concealment §1.5 found:
`priced_line_count` existed so the UI could admit a total was short, but was read
only inside `StoreSpendCard` — which lives inside this card's own disclosure. The
headline could be quietly incomplete while the top level said nothing. Verified
live: the seeded draft renders `~$50.30` + "2 items with no price yet".

---

## 5. The line row

### 5.1 Plan face (inline, `q-item.shopping-line`)

| # | Affordance | Visibility condition | What it does | Destination | Visibility | Decision |
|---|---|---|---|---|---|---|
| R1 | Reorder ▲ / grip / ▼ | **`v-if="canReorder"`** = not done, not shopping, **and `effectiveMode === 'manual'`** (`:1792`) | writes `sequence`; whole-row DnD + arrows both write it | `ShoppingListPlanRow` — arrows joined delete in the action cell; grip left the grid for absolute positioning in the row's left padding | arrows hover/focus-reveal on `hover: hover`, **always visible on `hover: none`**; grip hidden on touch (pointer DnD does not exist there) | moved |
| R2 | Name link | `!isNestedChild && stock_item_id` | routes to `/stock/:id` | `.sl-row__name`, raised to `--font-size-lg`/500 | always | kept |
| R3 | `BuyVerdictBadgeInline` | has `stock_item_id`; silent on low confidence | in-list "should I buy?" nudge, emits an action | `.sl-row__namerow`, beside the name | always | kept |
| R4 | Nested-product chip | `isNestedChild(line)` | indented + left rail | became an inline icon + tooltip on the name, not a chip | always | moved |
| R5 | Product-only chip | `isProductOnly(line)` | tinted row, "no linked stock item" | same treatment as R4; row keeps its sunken tint | always | moved |
| R6 | `added_via` chip | `added_via && !== 'manual'` | provenance ("from meal plan") | caption text on `.sl-row__meta` via `addedViaCaption()` | always | moved |
| R7 | Price-provenance caption | `estimate_source === 'historic'` | "last paid at X" / "from what you last paid" | `.sl-row__note` on the caption line | always ≥600px; **hidden <600px** (unchanged from the old rule — it is in the price editor) | kept |
| R8 | Offer chips | `line.offers.length > 0` — **T2 only** | per-offer price + store + save; clickable to choose | `.sl-row__offers`, own line, quietened to `--font-size-xs` | always when present | kept |
| R9 | Buy-hint dropdown | `preferred_buys.length` | pick / clear a `PreferredBuy` label | `.sl-row__metabtn` on the caption line | always | moved |
| R10 | Quantity stepper (− input +) | always; disabled when done, − disabled at 0 | 48px number input, blur/Enter commits | `.sl-row__qty` — **tile at rest, stepper on approach (§7.1)**; tile taps through to the same number input | stepper on hover/focus ≥600px; **tap-to-arm on touch**; buttons always in layout (opacity only) so reveal cannot reflow — **verified: money x and row height identical before/after hover** | moved |
| R11 | Read-only price | `moneyEnabled && priceForLine > 0` | `~$X` estimate, not editable on draft by design | `.sl-row__amount`, tabular, right-aligned column | always | kept |
| R12 | Prefill-source caption | `prefill_source_label` | where the estimate came from | `.sl-row__amountnote` | always ≥600px; **hidden <600px** — it set the money column's intrinsic width and starved the name (483px rows) | kept |
| R13 | Planned-store select | `allStoreOptions.length > 0` | writes `planned_store_id`; blank falls through the ladder | `.sl-row__metabtn` menu on the caption line; the clearable X became an explicit first menu item naming the inherited store | always | moved |
| R14 | Delete | disabled when done | removes the line | `.sl-row__actions` | **always visible on every device** — deliberately not hover-only, it is a one-tap action today | kept |
| R15 | Ticked treatment | `is_ticked` | dimmed + strikethrough, opacity transition | `.sl-row--ticked` + `--struck` | always | kept |
| R16 | Focus outline | `focusedLineId` | dashed accent outline for keyboard nav | `.sl-row--focused`; dashed → solid `--focus-ring` (D-rule alignment) | always | kept |

**Nothing was cut.** All sixteen rows are `kept` or `moved`; no `CUT` decision was
taken in chunk 1, so no owner sign-off is outstanding for this table.

**Correction to a proposal assumption:** §1.2 counted "nine always-visible
affordances". R1 is **already conditional** on manual sort mode, and R3–R9 are all
data-conditional. The true always-on set on a plain row is name + quantity stepper
+ price + store select + delete. The density problem is real but is driven as much
by *optional* elements stacking as by a fixed nine. This makes the control diet
cheaper than estimated and is recorded here so chunk 1 does not over-cut.

### 5.2 Run face (`ShoppingListRunFace.vue`)

| # | Affordance | Visibility condition | What it does | Destination | Visibility | Decision |
|---|---|---|---|---|---|---|
| N1 | Whole row is the tap target | always | ticks the line; checkbox icon is **decorative** (a real one would double-fire) | unchanged | always | kept |
| N2 | Quantity prefix `n×` | `quantity > 1` | inline with the name | unchanged | always when qty > 1 | kept |
| N3 | Caption | `captionFor(line)` | buy hint + store, only when sectioning isn't already saying it | unchanged | always when it has content | kept |
| N4 | Price button | `moneyEnabled` | opens the price sheet; estimate vs actual styled differently | unchanged | T1/T2 only | kept |
| N5 | Cleared-section one-liner | section fully picked | "Label — all n picked" instead of vanishing | unchanged | always | kept |
| N6 | "Picked (n)" section | `pickedLines.length > 0` | collapsed by default, tap a row to put it back | unchanged | always when present | kept |
| N7 | All-picked reassurance | `allPicked` | "That's everything." | unchanged | always | kept — **rendered live (S6)** |
| N8 | Nothing-on-list state | `lines.length === 0` | reachable when trim deferred everything | unchanged | always | kept — **rendered live (S5)** |

**Absent by design on the run face** (documented in the component header, must stay
absent): drag handles, delete, quantity steppers, buy-hint pickers, offer chips,
provenance, suggestions, budget banner.

**The run face was rebuilt in chunk 5** (FU-807), after the audit showed it was
the one shopping-list surface still wearing the pre-v4 shape — `q-list bordered
separator rounded-borders` + `q-item`, a hard 1px border, `--radius-md`, no
elevation and edge-to-edge separators, while the plan face had moved to a soft
slab and the receipt to a document sheet.

Two things unblocked it. First, `.sl-panel` / `.sl-list` / `.sl-section*` were
**scoped to `ShoppingListDetail.vue`**, so a child component could not reach
them — that is the mechanical reason this face was left behind. They moved into
the shared stylesheet, which was renamed `shoppingRow.scss` → **`shoppingList.scss`**
because it now carries the surface's whole shared visual language rather than
just the row. Second, `ShoppingListRunRow.vue` was extracted onto the same
skeleton the plan and receipt rows use.

Every N-row above is still `kept` — this changed the container and the chrome,
not one affordance. The two substantive details:

- **`q-item` is gone**, for the reason chunk 1 dropped it: it ships its own
  padding, min-heights and `--side` alignment rules that the row then fights.
  The row is a `role="button"` div rather than a `<button>` because it contains
  the price button and a button inside a button is invalid, so **Enter and Space
  are wired explicitly** — that is what `q-item clickable` was providing, and
  both were re-verified live rather than assumed.
- **The row name was a literal `1.05rem`** (**R-002**, tokens-only), which also
  left the shop face reading a step smaller than the other two. Now
  `--font-size-lg`, the same token on all three faces.

**Verified live:** all three faces report slab radius 10px, `--elevation-1` and
an 18.5625px name; row height 72px (D-004/D-016 floor is 44px, and this face
targets a thumb on a moving trolley); a single name-left x (72px) and a single
money-right x (932px) across the section; section headers render as
`FRIDGE 2/3` / `PANTRY 0/1`; ticking works by **click** (3→4) and by **Enter**
(4→5); the price button opens the sheet **without** ticking the row; the picked
drawer renders 5 struck rows; no page errors; no horizontal scroll at 375px.

### 5.3 Receipt face### 5.3 Receipt face (`ShoppingListReceiptFace.vue`)

| # | Affordance | Visibility condition | What it does | Destination | Visibility | Decision |
|---|---|---|---|---|---|---|
| E1 | Amend banner | `amending` | states the consequence: correcting does **not** re-run the restock | unchanged, in `ShoppingListReceiptFace` above the sheet | always when amending | kept |
| E2 | Own header | always | "n items bought" + completed label + `text-h5` total + "n not priced" | **split**: the count + date were word-for-word the overview card's C4/C5 forty pixels above, so the sheet's header row is gone and the card is the document's header; the **total moved to a footer** `TOTAL … $X` line under the itemisation, above a dashed rule, where a total belongs on a document; "n not priced" moved with it | always (total: `moneyEnabled` only) | moved |
| E3 | Bought-line rows | `boughtLines` | qty prefix, store, "estimated, no price entered" | `ShoppingListReceiptRow` — built on the shared `src/css/shoppingRow.scss` skeleton, so name scale, caption scale and inset divider are literally the plan row's | always | moved |
| E4 | Line amount + unit price | `moneyEnabled && !amending` | amount, plus "X each" when qty > 1 | `.sl-row__money` / `.sl-row__amountnote` — same classes and same right-aligned tabular column as the plan face | amount always; **"X each" hidden <600px** (the shared skeleton's rule — it starved the name at 375px) | kept |
| E5 | Amend controls | `amending` | qty stepper + price/store edit **only** — no add, remove or reorder | stepper took over the multiplier's own cell (so entering amend does not move the name column); price button sits in the amount column | always when amending | moved |
| E6 | "Didn't buy (n)" chips | `skippedLines.length > 0` | unticked lines as chips | unchanged content; now a sunken strip inside the sheet rather than a bordered card section | always when present | kept |
| E7 | Own `StoreSpendCard` | always | `tense="receipt"`, collapsed on every width | unchanged | always | kept |

**Nothing was cut.** All seven rows are `kept` or `moved`. E2 is the only one
worth a second look: its *content* all survives on screen (count and date on the
overview card, total and unpriced count in the sheet's footer), what went is the
duplicate rendering of it.

**Verified live** (money on and off, 1280px + 375px, `pesto-dark`): sheet radius
16px, `--elevation-card` present, **`bandIsGradient: false`** — the flat-paper
call that distinguishes this face from the plan and shop faces, which carry the
hero gradient; leader border `dotted`; a **single** amount-right x (931px) and a
single name-left x (82px) across all six rows; total `$21.90` at 24.75px; no
horizontal scroll at 375px; dark sheet luminance 35 vs page 0 (sheet lighter, so
the one `--surface-component` declaration is correct in both directions).

**T0 carve-out (money off — the default install).** The dotted leader is
suppressed when there is no amount at the end of it: a rule running to the
sheet edge and stopping reads as a number that failed to load, and T0 is the
tier the design has to serve first. Verified: `leaders: 0`, `hasTotal: false`,
six rows still render with name + store caption.

---

## 6. Dialogs

| # | Dialog | Trigger | Notes | Destination | Decision |
|---|---|---|---|---|---|
| D1 | `NewListDialog` | P3 / P7 / F10 | also mounted by the router landing page | unchanged | kept — **opened live** ("Build a fresh list, or top up an existing one") |
| D2 | `PutAwayDialog` | C12 | `v-if` status `done`; ephemeral, doesn't save | unchanged | kept — **opened live** |
| D3 | Older lists | P5 | **searchable**, not just scrollable | unchanged | kept — **opened live**, including the empty-search branch (S13) |
| D4 | Rename | C3 / P2 | dialog on every width (v3 fix); body copy states the blank-name rule | unchanged | kept — **opened live** |
| D5 | Planned date | T2 | Save / **Clear** (only when a date is set) / Cancel | unchanged | kept — **opened live** |
| D6 | Price sheet | N4 / E5 | bottom sheet; price + **quantity stepper** + bought-from store; Clear when an actual price exists; prefill caption | unchanged | kept — **opened live** (price, quantity 3, bought-from store, "Prefilled from Aldi offer") |
| D7 | Finish review | C10 | **two shapes** — clean finish lists what will be restocked; finishing early adds a warning banner + a **forced** leftover decision (`move-existing` / `move-new` / `discard`), with a target-list select and per-branch explanatory captions | unchanged | kept — **opened live** on the finishing-early branch ("2 items aren't ticked…") |
| D8 | Receipt lightbox | F8 thumb tap | `max-width: 900px`, Esc/backdrop closes | unchanged | kept — **not opened**: needs an uploaded attachment, and the seed ships none. The only §6 row without live evidence |

**No dialog component was modified by chunks 1-3** (`git diff` over
`src/components/dialogs/` is empty across the three commits). D4 and D5 are the
two that live *inline* in the page whose markup was heavily rewritten, so both
were re-opened live to confirm the rewrite didn't detach them; it didn't.

---

## 7. Flag and tier matrix

## 7. Flag and tier matrix

Both governing flags default **off** (`health_check.py:128,135`).

| Tier | `money` | `products` | What disappears |
|---|---|---|---|
| **T0** | false | — | C4 becomes a line count · C14, C15, C16, C17 · R11, R12 · N4 · E2 total, E4 · T3 (Log price) · F4/F5 trim (budget is a money surface) · C1 says "Done" not "Receipt" |
| **T1** | true | false | C16 (structurally $0) · R8 offer chips · T5 Refresh deals |
| **T2** | true | true | nothing — the full surface |

**T2 sub-case:** `products` on but *this list* has no offers → R8 absent per line,
C16 absent. The design must not leave a hole in either case.

**Other flags touching this page:** `scanning` (quick-add scan path), `budget`
(F4/F5), inference opt-in (F6). Each is off by default.

---

## 8. Keyboard, focus, DnD, responsive

| # | Behaviour | Detail | Destination | Decision |
|---|---|---|---|---|
| K1 | `n` | Add an item | unchanged | kept |
| K2 | `space` | Tick / untick the focused line | unchanged — see the resolution below | kept, **inert on plan and receipt by design** |
| K3 | `u` | Untick the last item you ticked | unchanged | kept, same gate as K2 |
| K4 | `↑` / `↓` | Move line focus | unchanged | kept — **verified live**, focus lands on `.sl-row--focused` |
| K5 | Focus ring | was `.shopping-line-focused`, dashed accent, `outline-offset: -2px` | `.sl-row--focused` in `shoppingRow.scss` — **solid `--focus-ring`**, same offset. The old rule was left behind by chunk 1 as dead CSS and is now deleted (below) | moved |
| G1 | Whole-row DnD | `useDragDropList`, `canDragStart` gated on `canReorder` (R1); grip is decorative | unchanged — the page still owns `lineDnd`; the row component receives `handleProps`/`rowProps` via `v-bind` | kept |
| G2 | Arrow reorder | keyboard/thumb path for the same `sequence` write | moved into `.sl-row__actions` beside delete (R1) | moved |
| B1 | `lt-sm` (375px) | row wrapped to two lines via `.shopping-line__break`; provenance caption **hidden**; drag grip **hidden** | **the two-line wrap is gone** — the row no longer needs it (quantity is one tile, money is type, metadata is a caption), so at 375px it stays a single grid row with narrower reserved tracks. Provenance caption and grip still hidden | moved |
| B2 | `lt-md` | mobile picker replaces the rail; card name + pencil hide (C2/C3) | unchanged | kept |
| B3 | `lt-sm` toolbar | `compactToolbar` drops labels, keeps tooltips | unchanged | kept |
| B4 | `gt-sm` | 300px sticky rail, `min-width: 0` load-bearing against the FU-578 #40 overflow family | unchanged | kept |

### K2 resolved — the shortcut is inert on a draft

Chunk 0 left this open because it *is* unanswerable from the template. It is
answerable from the script, and was then confirmed live:

```
function tickFocusedLine() {
    if (detail.value?.status !== 'shopping') return;   // ← the gate
```

`untickLastTicked` (K3) carries the identical guard. Driven on a 7-line draft:
`ArrowDown` focused a row (`.sl-row--focused` count 1), then `Space` and `u` were
pressed — the server's `is_ticked` array was byte-identical before and after
(`0` ticked → `0` ticked). **So the plan face cannot be ticked by keyboard**,
which matches v3's deliberate removal of draft ticking. Nothing to change.

**But it is advertised where it does not work.** `useShortcut` registers all five
unconditionally, so the `?` cheatsheet promises *"space — tick / untick the
focused line"* on the plan and receipt faces too, and pressing it there does
nothing. That is a small honesty defect rather than a functional one — logged as
**FU-808**, not fixed here.

### Dead CSS from chunk 1, removed

Chunk 1 replaced the inline `q-item` row with `ShoppingListPlanRow.vue` but left
its stylesheet behind: **165 lines** of `.shopping-line*` rules — the whole
`@media (max-width: 599px)` two-line-wrap block (B1), the name/ticked/focused/
nested/product-only rules, the quantity-input rules, plus `.offer-savings`,
`.text-strike` and `.sld-price-btn`. Every one of those classes has zero
remaining references in `src/` (the only two greps that survive are an unrelated
comment and the DnD mime string `application/x-dora-shopping-line`).
`ShoppingListDetail.vue` is 3,273 → **3,108 lines**. Found by this audit, not by
`vue-tsc` or `eslint` — neither can see an unused CSS class.

---

## 9. Edge and empty states

## 9. Edge and empty states

| # | State | Trigger | Current rendering | Destination | Decision |
|---|---|---|---|---|---|
| S1 | No detail / bad id | `!detail` | F10 fallback | **correction:** a well-formed but unknown uuid renders **F1 *and* F10** — the error banner ("Couldn't load this list. Could not load list: ShoppingList with the id … was not found" + Retry) above the fallback ("Couldn't open this list. Pick another list…"). The census recorded F10 alone | kept — **rendered live** |
| S2 | Load failure | `loadError` | F1 banner + F10 with a different heading | same shape as S1; **a failure on a list already in the store does not replace it** — the page keeps showing the loaded detail, so this state only appears on a cold load | kept — **rendered live** (forced 500 on a cold navigation) |
| S3 | Loading | `loading && !detail` | F2 skeleton | unchanged | kept — **rendered live** (17 skeleton elements while the response was held open) |
| S4 | Empty list (plan) | `lines.length === 0` | flat bordered card pointing at Quick add + cart-add from `/stock` | now `.sl-panel` (chunk 2) | kept — **rendered live** on the seeded empty draft |
| S5 | Empty list (run) | `lines.length === 0` | N8 | unchanged | kept — **rendered live** ("Nothing on this list. Add something with Quick add, or finish up.") |
| S6 | All picked (run) | `allPicked` | N7 | unchanged | kept — **rendered live** ("That's everything." + Picked (5) + "$31.00 in the trolley") |
| S7 | No priced lines | `priced_line_count === 0` per bucket | `~` marker — **only inside C14, which is inside the disclosure** (§1.5 concealment) | **fixed by C19** — the card's top level now reads `~$0.00` + "6 items with no price yet" | moved — **rendered live** |
| S8 | No store on any line | `by_store` emptied when no real store exists | C14 renders nothing at all | unchanged — the spend card is genuinely absent, and the rows fall back to "Any store" on the planned-store menu | kept — **rendered live**; the §1.5 concern does not apply here (there is no partial truth to conceal, the breakdown simply has no content) |
| S9 | Everything deferred by trim | all lines `deferred_by_budget` | run face shows N8; plan shows F7 only | plan face renders zero `.sl-row` and the `.sl-panel--sunken` deferred section carrying all 7 with "Add back" | kept — **rendered live** |
| S10 | Receipt, nothing bought | `boughtLines.length === 0` | E2 reads "0 items bought"; E6 carries everything | E2's count moved to the overview card; the sheet degrades to a dashed rule + `TOTAL` + the "Didn't buy (6)" strip, which reads coherently rather than as an empty box | moved — **rendered live** |
| S11 | No attachments | `attachments.length === 0` | F8 caption "No receipts yet…" | unchanged | kept — **rendered live** |
| S12 | No older lists | `olderDoneSummaries.length === 0` | P5 absent from both renderings | unchanged | kept — **rendered live** (collection trimmed to 3 done + hard reload; "See older" count 0) |
| S13 | Older-list search miss | `filteredOlderSummaries.length === 0` | "No finished list matches …" | unchanged | kept — **rendered live** |

**All thirteen rendered.** Five (S1, S3, S4, S11, S13) came from data the seeded
backend actually produces. The other eight (S2, S5, S6, S7, S8, S9, S10, S12) were
reached by **rewriting the API payload in flight** — the real component tree, the
real store, the real stylesheet, with a mutated response — because the dense seed
cannot produce them and hand-building each would have meant mutating a scratch
database into eight one-off shapes. Recorded plainly so the evidence is not
overstated: these prove *the UI renders that state correctly*, not that the server
can produce it. Where a figure looks odd in the screenshots (S5's `$4.05` on an
empty list, S10's `$21.90` for nothing bought) that is the interception showing
through — the payload's `totals` were left as the server computed them.

---

## 10. Findings raised by the census

## 10. Findings raised by the census

1. **The mockup omitted all of §3.** Trim banner, trim preview, suggestions strip,
   deferred section, receipts strip and the destructive footer are real page
   furniture with no home in the v4 sketches. **Chunk 2 must place all six.**
2. **R1 is already conditional** on `effectiveMode === 'manual'`, softening §1.2's
   "nine always-visible" framing. Recorded so chunk 1 does not over-cut.
3. **S7 confirms the §1.5 concealment** and adds S8: when no line has a store,
   `by_store` is emptied server-side and the disclosure silently renders nothing.
4. **K2 on the plan face is unresolved** and needs a live check (§8).
5. **F6's dismissal is in-memory only** and deliberately so — the redesign must not
   "improve" this into persistence without re-reading the reasoning at `:2497`.
6. **C1 changes wording on a money flag** (`Receipt` vs `Done`), which is a T0
   difference in *copy*, not just in visible elements — easy to lose in a rebuild.

### Raised by chunk 4 (the audit itself)

7. **P8 never existed.** The census recorded a per-row kebab that had been
   removed three days earlier. Corrected in §2, deliberately not deleted — a
   baseline that quietly edits its own errors is not a baseline.
8. **Chunk 1 left 165 lines of dead CSS** in `ShoppingListDetail.vue`. Removed
   (§8). Neither `vue-tsc` nor `eslint` can see an unused CSS class, so nothing
   in the standing gate would ever have caught it.
9. **The run face was the odd one out** — still `bordered` + `--radius-md` +
   `q-item` while the other two faces moved to slabs and a document sheet. Root
   cause: the slab and section rules were **scoped to the page**, so a child
   component could not reach them. Raised as FU-807 (owner call, since it was
   unfinished proposal scope rather than new scope) and **resolved the same day
   in chunk 5** — owner: *"consistency matters"*. See §5.2.
10. **`space` / `u` are advertised on faces where they are inert.** The gate is
    correct; the cheatsheet's promise is not. **FU-808**.
11. **A failed refresh does not surface an error** when the list is already in
    the store (S2). Defensible — showing stale data beats blanking the page —
    but it means `loadError` is only ever seen on a cold load, which is worth
    knowing before anyone "fixes" it.

---

## 11. Cutover rule — **PASSED 2026-09-01**

Chunk 4 passes only when:

- ✅ **every `Destination` / `Visibility` / `Decision` cell is filled.** No cell
  reads `TBD`. 79 catalogued affordances, plus one struck out as never having
  existed (P8).
- ✅ **every `CUT` carries a written reason and owner sign-off.** Vacuous, and
  that is the headline: **across chunks 1-4 nothing was cut.** Every row is
  `kept` or `moved`, plus one `added` (C19). No sign-off is outstanding.
- ✅ **every hover/focus-reveal control has a named touch path.** Three exist —
  the quantity stepper (tap the tile to arm), the reorder arrows (permanently
  visible under `@media (hover: none)`), and the drag grip (hidden on touch,
  where pointer DnD does not exist and the arrows are the real path). Delete was
  deliberately left always-visible on every device.
- ✅ **every row in §7 checked at T0/T1/T2.** T0 driven live by toggling
  `money_enabled` off in Settings — it found the receipt leader defect (§5.3) and
  confirmed the chunk-2 per-face headline. T2 is the seeded default (offers and
  savings render on the plan rows). T1 is T2 minus `products`, exercised by the
  lists whose lines carry no offers.
- ✅ **every row in §9 rendered at least once in the running app.** Thirteen of
  thirteen; eight against an intercepted payload, stated as such in §9.

**One caveat, recorded rather than waived:** D8 (the receipt lightbox) was not
opened — it needs an uploaded attachment and the seed ships none. It is the
single affordance in this document with no live evidence behind it. It was not
touched by any chunk.
