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
are **unfilled** for anything chunk 1–3 has not designed yet. They are filled as
each chunk lands. **Chunk 4 is blocked until no cell reads `TBD`.**

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
| T1 | Add item (primary) | all | always; `:disable` when no detail or status `done` | opens quick-add sheet | TBD | TBD | TBD |
| T2 | Shop day | plan | `v-if="planFace"` | opens planned-date dialog | TBD | TBD | TBD |
| T3 | Log price | run | `v-if="runFace && moneyEnabled"` | `useLogPrice()` sheet — a price for something **not** on the list | TBD | TBD | TBD |
| T4 | Templates | all | always | routes to `/shopping-lists/templates` | TBD | TBD | TBD |
| T5 | Refresh deals | all | `v-if="productsEnabled"` **(T2 tier)** | re-checks linked product offers | TBD | TBD | TBD |
| T6 | Print | all | always; disabled when 0 lines | printable view | TBD | TBD | TBD |
| T7 | Save as template | all | always; disabled when 0 lines | snapshot to a template | TBD | TBD | TBD |

**Note:** the two Export members that v3's V9 split out are not in the current
toolbar block — Print (T6) and Save as template (T7) are what that split
produced. There is no remaining Export menu.

---

## 2. List picker (two renderings of one continuum)

| # | Affordance | Where | Visibility condition | What it does | Destination | Visibility | Decision |
|---|---|---|---|---|---|---|---|
| P1 | Mobile `BaseDropdown` switcher | `.lt-md` | always, **including mid-shop** | switches list; on mobile this is the only place the list name appears | TBD | TBD | TBD |
| P2 | Rename pencil (mobile) | `.lt-md`, beside P1 | `v-if="detail"` | opens rename dialog | TBD | TBD | TBD |
| P3 | "New list" pinned first entry | mobile dropdown | always | opens `NewListDialog` | TBD | TBD | TBD |
| P4 | `ShoppingListRailItem` rows | both | `railEntries` = drafts + shopping + 5 most-recent done | select → `switchToList` | TBD | TBD | TBD |
| P5 | "See older (n)" | both | `olderDoneSummaries.length > 0` | opens searchable older-lists dialog | TBD | TBD | TBD |
| P6 | Desktop rail | `.gt-sm` column | always, **including mid-shop** | 300px sticky, `max-height: calc(100vh - 110px)` | TBD | TBD | TBD |
| P7 | "New list" (rail, primary) | `.gt-sm` | always | opens `NewListDialog` | TBD | TBD | TBD |
| P8 | Per-list ⋮ menu (incl. Delete) | `ShoppingListRailItem` | per row | acts on *that* list, not the open one | TBD | TBD | TBD |

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
| N1 | Whole row is the tap target | always | ticks the line; checkbox icon is **decorative** (a real one would double-fire) | TBD | TBD | TBD |
| N2 | Quantity prefix `n×` | `quantity > 1` | inline with the name | TBD | TBD | TBD |
| N3 | Caption | `captionFor(line)` | buy hint + store, only when sectioning isn't already saying it | TBD | TBD | TBD |
| N4 | Price button | `moneyEnabled` | opens the price sheet; estimate vs actual styled differently | TBD | TBD | TBD |
| N5 | Cleared-section one-liner | section fully picked | "Label — all n picked" instead of vanishing | TBD | TBD | TBD |
| N6 | "Picked (n)" section | `pickedLines.length > 0` | collapsed by default, tap a row to put it back | TBD | TBD | TBD |
| N7 | All-picked reassurance | `allPicked` | "That's everything." | TBD | TBD | TBD |
| N8 | Nothing-on-list state | `lines.length === 0` | reachable when trim deferred everything | TBD | TBD | TBD |

**Absent by design on the run face** (documented in the component header, must stay
absent): drag handles, delete, quantity steppers, buy-hint pickers, offer chips,
provenance, suggestions, budget banner.

### 5.3 Receipt face (`ShoppingListReceiptFace.vue`)

| # | Affordance | Visibility condition | What it does | Destination | Visibility | Decision |
|---|---|---|---|---|---|---|
| E1 | Amend banner | `amending` | states the consequence: correcting does **not** re-run the restock | TBD | TBD | TBD |
| E2 | Own header | always | "n items bought" + completed label + `text-h5` total + "n not priced" | TBD | TBD | TBD |
| E3 | Bought-line rows | `boughtLines` | qty prefix, store, "estimated, no price entered" | TBD | TBD | TBD |
| E4 | Line amount + unit price | `moneyEnabled && !amending` | amount, plus "X each" when qty > 1 | TBD | TBD | TBD |
| E5 | Amend controls | `amending` | qty stepper + price/store edit **only** — no add, remove or reorder | TBD | TBD | TBD |
| E6 | "Didn't buy (n)" chips | `skippedLines.length > 0` | unticked lines as chips | TBD | TBD | TBD |
| E7 | Own `StoreSpendCard` | always | `tense="receipt"`, collapsed on every width | TBD | TBD | TBD |

---

## 6. Dialogs

| # | Dialog | Trigger | Notes | Destination | Decision |
|---|---|---|---|---|---|
| D1 | `NewListDialog` | P3 / P7 / F10 | also mounted by the router landing page | TBD | TBD |
| D2 | `PutAwayDialog` | C12 | `v-if` status `done`; ephemeral, doesn't save | TBD | TBD |
| D3 | Older lists | P5 | **searchable**, not just scrollable | TBD | TBD |
| D4 | Rename | C3 / P2 | dialog on every width (v3 fix); body copy states the blank-name rule | TBD | TBD |
| D5 | Planned date | T2 | Save / **Clear** (only when a date is set) / Cancel | TBD | TBD |
| D6 | Price sheet | N4 / E5 | bottom sheet; price + **quantity stepper** + bought-from store; Clear when an actual price exists; prefill caption | TBD | TBD |
| D7 | Finish review | C10 | **two shapes** — clean finish lists what will be restocked; finishing early adds a warning banner + a **forced** leftover decision (`move-existing` / `move-new` / `discard`), with a target-list select and per-branch explanatory captions | TBD | TBD |
| D8 | Receipt lightbox | F8 thumb tap | `max-width: 900px`, Esc/backdrop closes | TBD | TBD |

---

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
| K1 | `n` | Add an item | TBD | TBD |
| K2 | `space` | Tick / untick the focused line | TBD | TBD |
| K3 | `u` | Untick the last item you ticked | TBD | TBD |
| K4 | `↑` / `↓` | Move line focus | TBD | TBD |
| K5 | Focus ring | `.shopping-line-focused`, dashed accent, `outline-offset: -2px` | TBD | TBD |
| G1 | Whole-row DnD | `useDragDropList`, `canDragStart` gated on `canReorder` (R1); grip is decorative | TBD | TBD |
| G2 | Arrow reorder | keyboard/thumb path for the same `sequence` write | TBD | TBD |
| B1 | `lt-sm` (375px) | row wraps to two lines via `.shopping-line__break`; provenance caption **hidden**; drag grip **hidden** | TBD | TBD |
| B2 | `lt-md` | mobile picker replaces the rail; card name + pencil hide (C2/C3) | TBD | TBD |
| B3 | `lt-sm` toolbar | `compactToolbar` drops labels, keeps tooltips | TBD | TBD |
| B4 | `gt-sm` | 300px sticky rail, `min-width: 0` load-bearing against the FU-578 #40 overflow family | TBD | TBD |

**Open question for §7.4 (touch paths):** K2's `space` ticks the focused line, but
**the plan face has no tick control** — ticking is a run-face concept (v3 removed
draft ticking deliberately). Whether the shortcut is inert or still mutates on a
draft is **not resolved by reading the template** and needs a live check. Recorded
as an open item, not assumed either way.

---

## 9. Edge and empty states

| # | State | Trigger | Current rendering | Destination | Decision |
|---|---|---|---|---|---|
| S1 | No detail / bad id | `!detail` | F10 fallback | TBD | TBD |
| S2 | Load failure | `loadError` | F1 banner + F10 with a different heading | TBD | TBD |
| S3 | Loading | `loading && !detail` | F2 skeleton | TBD | TBD |
| S4 | Empty list (plan) | `lines.length === 0` | flat bordered card pointing at Quick add + cart-add from `/stock` | TBD | TBD |
| S5 | Empty list (run) | `lines.length === 0` | N8 | TBD | TBD |
| S6 | All picked (run) | `allPicked` | N7 | TBD | TBD |
| S7 | No priced lines | `priced_line_count === 0` per bucket | `~` marker — **only inside C14, which is inside the disclosure** (§1.5 concealment) | TBD | TBD |
| S8 | No store on any line | `by_store` emptied when no real store exists | C14 renders nothing at all | TBD | TBD |
| S9 | Everything deferred by trim | all lines `deferred_by_budget` | run face shows N8; plan shows F7 only | TBD | TBD |
| S10 | Receipt, nothing bought | `boughtLines.length === 0` | E2 reads "0 items bought"; E6 carries everything | TBD | TBD |
| S11 | No attachments | `attachments.length === 0` | F8 caption "No receipts yet…" | TBD | TBD |
| S12 | No older lists | `olderDoneSummaries.length === 0` | P5 absent from both renderings | TBD | TBD |
| S13 | Older-list search miss | `filteredOlderSummaries.length === 0` | "No finished list matches …" | TBD | TBD |

---

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

---

## 11. Cutover rule

Chunk 4 passes only when:

- every `Destination`, `Visibility` and `Decision` cell above is filled;
- every `CUT` carries a written reason **and** owner sign-off;
- every control whose `Visibility` is hover- or focus-reveal has a **named touch
  path** (§7.4 of the proposal — *hover-only is a loss on touch*);
- every row in §7 has been checked at T0, T1 and T2;
- every row in §9 has been rendered at least once in the running app.
