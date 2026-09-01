# Shopping List UX v4 — the surface pass

**Status:** **BUILT 2026-09-01** — chunks 0-5 complete; chunk 4 (the blocking cutover audit) passed. See §9.
**Date:** 2026-08-31.
**Extends:** `PROPOSAL_SHOPPING_LIST_UX_V3.md` (BUILT 2026-08-29). v3 replaced the
top section of the detail page with `ShoppingListOverviewCard` and settled the
information architecture. **v4 does not re-litigate any of that.** It changes only
the *surface* — containers, grid, type scale, control density — plus the row, which
v3 never touched.
**Source feedback:** the 2026-08-31 owner session (W1–W12 below), following a
four-direction mockup review.

---

## 0. Feedback being addressed (verbatim, numbered)

| # | Bullet |
|---|---|
| W1 | "the page looks quite bland, flat, uninspired" |
| W2 | "the UI elements are very plain and slapped together in 5 min like a default card with default borders, all square and boring" |
| W3 | "the rows themselves are horrible with the UI elements all over the place misaligned and weirdly offset/placed/spaced" — *stated as the biggest gripe* |
| W4 | "text feels small where it should be big" |
| W5 | "followed by the overview card (could look 1000% nicer)" |
| W6 | "i do like the general direction of B and C" |
| W7 | "A could possibly be used for receipts/done lists to visually indicate (with a bit of fun) that it is now a receipt" |
| W8 | "no loss of functionality should happen unless it makes sense to cut it and we make a conscious decision to cut it" |
| W9 | "i am concerned the UI will accidentally hide something we previously had shown" |
| W10 | "'saving X.XX' … smells like 'product offers' … product offer data is a niche set of data that only a very small percentage of users will enjoy … the bulk of users will not see those UI elements, and so the design should facilitate that well" |
| W11 | "some of your designs can look nicer/more polished in the demos than the actual end result. lets make sure the end result looks very nice" |
| W12 | "document for yourself before doing the new UI what the existing page actually does under all scenarios (all settings/options/changeable and visual UI) so you can ensure there is a clean cutover" |

---

## 1. Audit findings (what the code actually says)

Verified 2026-08-31 against `ShoppingListDetail.vue` (3,571 lines),
`ShoppingListOverviewCard.vue`, `get_shopping_list_detail.py`, `tokens.scss`,
`themes.scss` and `health_check.py`.

### 1.1 W1/W2 are a token-selection problem, not a taste problem

`tokens.scss` defines `--radius-lg` (10px), `--radius-xl` (16px), `--radius-2xl`
(22px), `--elevation-1/2/3`, `--elevation-card`, `--elevation-card-hover`,
`--hero-gradient` and `--savings-accent`.

The shopping surface uses `--radius-md` (6px — the squarest non-trivial rung) and a
flat `1px solid var(--border-default)` on the overview card, the line list, the
empty-state card and `StoreSpendCard` alike. It uses **zero** elevation tokens.
Every container therefore has identical visual weight, so nothing recedes and
nothing advances. The page looks like a default card because it is functionally
painting with the dullest available subset of a palette that already contains the
answer.

### 1.2 W3 has a precise mechanical cause: there is no grid

The line row is a `q-item` laid out with flex. Each row measures itself
independently:

- name is `flex: 1 1 0` (`:3425`)
- the quantity block carries `min-width: 150px`
- the store select carries `min-width: 132px` (`.sld-plan-store`)
- the price is a **button** with `min-width: 96px` (`.sld-price-btn`)

Nothing shares a column, so quantity, money and store land at different
x-positions per row depending on name length and which optional chips render. The
misalignment the owner is seeing is structural, not a spacing-value mistake.

The second half is **count**: the plan row renders up to nine affordances
simultaneously at equal weight — a three-button vertical reorder stack, drag grip,
name link, `BuyVerdictBadgeInline`, an `added_via` chip, a quantity stepper, a
price button, a store select, swap and delete.

**Corrected by chunk 0 (2026-08-31):** "nine always-visible" overstates it. The
reorder stack is already gated on `canReorder`, which requires
`effectiveMode === 'manual'` (`:1792`), and the verdict badge, chips, provenance
caption, offer chips and buy-hint dropdown are all data-conditional. The genuinely
always-on set on a plain row is **name, quantity stepper, price, store select,
delete**. The density problem is real, but it is driven as much by *optional*
elements stacking on a busy row as by a fixed nine — so chunk 1 must not over-cut.
See `05_investigations/SHOPPING_LIST_BASELINE.md` §5.1.

The 2026-08-26 mobile fix (`:3410`) wrapped the row to two lines and **kept all
nine**, so the phone row is twice as tall and equally noisy.

### 1.3 W4 is confirmed

The item name — the only thing on the row that is actually read — renders around
`0.9rem`, losing to a `1.9rem` money figure (`.sl-overview__amount`, itself a magic
number off the `--font-size-*` scale) and to three chip variants. The hierarchy
currently runs money → chips → name. It should run name → money → metadata.

Other off-scale values on this surface: `0.92em`, `0.95em`, `1.1rem`,
`border-radius: 6px` on receipt thumbs, `min-width: 132px`, `2.25rem` nest indent.

### 1.4 W10 is correct, and stronger than stated

`_line_savings()` (`get_shopping_list_detail.py:220`) returns `0.0` unless
`_chosen_offer(line)` exists **and** that offer has a `price_was`. There is no
other path to a non-zero saving.

By contrast `_line_price()` reads `estimated_unit_price`, which the handler
resolves **actual → historic → offer**. Prices therefore work off the user's own
purchase history with no products or offers present at all.

So price surfaces and savings surfaces have different audiences, and the design
must not treat them as one "money" concept.

Further: both governing flags are **off by default** in `health_check.py` —
`"money": False` (`:128`) and `"products": False` (`:135`). The default install
shows no dollar figures whatsoever. **The mockup's B card, built around a large
dollar headline, is designed for a tier most installs never reach.** This is the
single most important correction v4 carries over the mockup.

### 1.5 An existing concealment, relevant to W9

`priced_line_count` exists on `StoreSpendDto` precisely so the UI can admit when a
total is short because some lines carry no price. It is consumed **only** inside
`StoreSpendCard.vue` (`:61`, `:200`, `:206`), which lives inside the overview
card's collapsed disclosure. The headline figure can therefore be quietly
incomplete while the top level of the card says nothing. v4 should fix this; the
baseline census (§2) is what makes such gaps findable rather than incidental.

### 1.6 Dark themes will undermine the two-tier surface premise

`pesto-dark` sets `--surface-page: hsl(165 60% 5%)` and
`--surface-sunken: hsl(165 60% 3%)` — a two-percentage-point delta near black,
which is invisible. Drop shadows do not read on near-black surfaces either, so
`--elevation-card` contributes nothing there.

Direction B's core device (sunken canvas, elevated card) therefore **inverts** in
dark themes: elevation must be expressed as *lightness plus border*, with the card
lighter than the page. This must be designed up front, not discovered at the end.

`--hero-gradient` is redefined per theme, so the card's band re-themes for free —
but it must be checked in every theme, not only Pesto.

---

## 2. Chunk 0 — the behavioural baseline (BLOCKING, W12)

**DONE 2026-08-31 — `docs/05_investigations/SHOPPING_LIST_BASELINE.md`.** 79
catalogued affordances across toolbar, picker, page furniture, overview card, three
row variants, eight dialogs, keyboard/DnD/responsive behaviour and thirteen
edge states, plus the T0/T1/T2 tier matrix. Its `Destination` / `Visibility` /
`Decision` columns are deliberately unfilled and are completed by chunks 1–3;
chunk 4 is blocked until no cell reads `TBD`. Six findings came out of it — see
its §10, two of which amended this document (§1.2 and §4.2).

**Nothing in §4 starts until this exists.** Its output is a new document,
`docs/05_investigations/SHOPPING_LIST_BASELINE.md`, written by reading the code —
not from memory and not from this proposal.

Its purpose is a **clean cutover**: it is the checklist the rebuilt UI is audited
against, and the answer to W8 and W9. It must enumerate, for the detail page and
its three faces:

1. **Every toolbar button** — label, icon, `aria-label`, its `v-if` condition, its
   compact-mode behaviour (`compactToolbar` = `$q.screen.lt.sm`), and what it opens
   or mutates. Known set includes Add item, Shop day (`planFace`), Log price
   (`runFace && moneyEnabled`), Templates, Refresh deals (`productsEnabled`),
   Print, Save as template, plus the two export items split out by v3's V9.
2. **Every affordance on a line row**, per face — reorder arrows, drag grip, name
   link, buy-verdict badge, `added_via` chip, nested-product chip, product-only
   chip, quantity stepper, price button, price provenance caption, store select,
   swap, delete — each with its visibility condition.
3. **Every dialog** and its trigger. Known set from the template: rename
   (`:1180`), planned date (`:1205`), older lists (`:1132`), `NewListDialog`,
   `PutAwayDialog`, plus the three `BaseDialog`s at `:1252`, `:1354` and the inline
   one at `:970`.
4. **Every install-flag combination** and its visible effect — `money`,
   `products`, `scanning`, `budget`, `nutrition_mode` — including the practical
   third tier where `products` is on but a given list has no offers.
5. **Every list state and transition** — draft → shopping → done, plus what each
   transition does to the toolbar, the card, the row and the danger footer.
6. **Every empty, partial and edge state** — no lists at all, empty list, list with
   no priced lines, no store set on any line, all lines ticked, all lines unticked,
   deferred-by-budget lines, nested product lines, product-only lines,
   single-item lists, and a list long enough to matter for scroll.
7. **Every bulk-bar action** and how selection mode changes the row.
8. **Every section mode** (`SECTION_MODES` / `PLAN_SECTION_MODES`), including which
   modes are unavailable for a given list and how that is signalled.
9. **Every keyboard affordance** — the `useShortcut` registry entries live on this
   page, plus focus management and the `.shopping-line-focused` outline.
10. **Every drag-and-drop behaviour** and the `canReorder` conditions that gate it.
11. **Responsive behaviour at 375px, 768px and 1280px**, including the desktop rail
    and the mobile `BaseDropdown` list picker.

**Format:** one row per affordance —
`Affordance | Face(s) | Visibility condition | What it does | v4 destination | Visibility class | Decision`.

`v4 destination` and `Decision` start empty and are filled during §4. `Decision` is
one of **kept / moved / consciously cut**. A cut requires a written reason and the
owner's sign-off — that is the W8 contract.

**The W9 rule, stated explicitly:** *hover-only is a loss on touch.* Every control
that moves to hover-reveal must have a named touch path — swipe, long-press, or a
row overflow menu — recorded in its baseline row. The mockup failed this test: its
375px panel showed no swap, reorder or delete at all. That failure is the reason
this chunk is blocking.

---

## 3. The flag matrix

Faces are `plan` / `run` / `receipt`. Money tiers derive from two install flags,
both default-off, plus a data condition.

| Tier | Condition | Population | Prices | Savings |
|---|---|---|---|---|
| **T0 — no money** | `money = false` | **default install** | none | none |
| **T1 — money, no offers** | `money = true`, `products = false` | enthusiast | yes, from actual → historic | never (always `$0`) |
| **T2 — money + offers** | `money = true`, `products = true`, offers present on the list | niche | yes | yes |

**Design targets, in priority order:**

1. **T0 is the baseline the card must look excellent in.** With no dollar figure
   there is no headline number, so the card needs a non-money headline that is
   genuinely the point of the surface rather than a consolation. Today it falls
   back to the raw item count.
2. **T1 is the design's centre of gravity.** Prices present, savings structurally
   absent. Any layout whose balance depends on a savings element is wrong.
3. **T2 is additive polish.** Offer surfaces must slot into space that is
   *legitimately empty* in T1 — never leave a hole, never be load-bearing for
   the composition.

**Deliverable:** §4's design must state all nine cells (3 faces × 3 tiers),
specifically what occupies the headline slot in each. Today those nine cells are
handled by scattered `v-if`s, which is exactly how a state gets accidentally
hidden.

---

## 4. The design

Direction **B** for plan and run faces, direction **A** for the receipt face (W6,
W7). Direction **C** is explicitly deferred — see §6.

### 4.1 The row (chunk 1 — highest priority, W3)

- **Drop `q-item` entirely.** The row becomes a plain element with
  `display: grid` and fixed columns, so every row shares one column set and
  alignment is structural. This is also the W11 fix — see §5.
- **Always-visible set reduces to three:** quantity tile, name, money. Everything
  else moves to hover on pointer devices, with a named touch path per §2.
- **Quantity** becomes a rounded tap-to-edit tile rather than a `− n +` stepper.
  *Open decision — see §7.1.*
- **Name** rises to `--font-size-lg`-grade with weight 500; money matches it.
  Metadata drops to a single caption line, replacing the three competing chip
  variants (W4).
- **Section headers** become a real header — uppercase, tracked, with a count
  pill — rather than muted `text-subtitle2` floating above a bordered box.
- No `q-list bordered separator`. One soft slab, `--radius-lg`, `--elevation-1`,
  internal dividers inset to the content column.

### 4.2 The overview card (chunk 2, W5)

- `--radius-xl`, `--elevation-card`, on a `--surface-sunken` page canvas, with a
  dark-theme inversion per §1.6.
- Headline figure rises to roughly `--font-size-3xl`-grade, **tier-aware** per §3.
- `--hero-gradient` band on the **plan and run faces only**; the receipt face is
  flat (§7.2). This makes the band carry state rather than decoration: a gradient
  reads as a live, active surface, flat paper reads as a finished record. The
  three faces become differently-*material*, not merely differently-arranged,
  which is a stronger state cue than the status pill alone.
- Segmented control for sort, replacing the four loose ghost buttons.
- Surface the `priced_line_count` shortfall marker at the top level, not only
  inside the disclosure (§1.5).
- **Place the six pieces of page furniture the mockup omitted entirely** — the
  budget trim banner and its preview card, Dora's suggestions strip, the
  deferred-to-fit-budget section, the receipts photo strip and the destructive
  footer (baseline §3). This is the largest gap chunk 0 found: all six are live
  surfaces with real conditions, and none of them appeared in any of the four
  sketched directions. A design that only composes the card and the rows has not
  finished the page.

### 4.3 The receipt face (chunk 3, W7)

Direction A's document treatment, for a structural reason rather than a decorative
one: the receipt face is the only face with essentially no controls — it is a
record, and the sole action is Amend. A control-free typographic layout fits it
natively, and it makes the state transition legible: the list visibly *becomes* a
receipt.

**Surface:** flat — no gradient band (§7.2). "Flat" here still means a white slab
on the sunken canvas (paper on a desk), **not** fully borderless: borderless would
lose the canvas relationship B establishes for the other two faces, and A's
document style works fine on a defined sheet, which is what a receipt physically
is.

**Constraint:** built as a `face="receipt"` variant of the same row primitive and
the same tokens, not a bespoke style island — or it becomes the next thing that
drifts (the failure mode `CollapsibleCard`'s header comment already documents).

**How that landed (2026-09-01).** The constraint's *intent* is shared structure;
its literal reading — a `face` prop on `ShoppingListPlanRow` — would have bought
that at the price of one component holding two mutually-exclusive control sets
behind `v-if`, which is the componentisation R-001 exists to prevent. The two
faces genuinely share a skeleton (grid shell, name/caption/money type scale,
inset divider) and genuinely differ in grammar (a quantity tile and
reveal-on-approach controls vs a multiplier and a dotted leader). So the
skeleton was extracted to **`src/css/shoppingRow.scss`** and both faces consume
it, on the precedent `dnd.scss` and `subbar.scss` already set for shared visual
language (R-022 / ADR-018). Drift is prevented by the thing they share being
*one file*, which is what the constraint was actually protecting.

**One carve-out found in the running app.** The leader is suppressed when money
is off: a dotted rule running to the sheet edge and stopping reads as a number
that failed to load, and T0 is the majority install. Detail in baseline §5.3.

---

## 5. W11 — why mockups flatter, and the mitigation

The mockup rows are bare `<div>`s on a CSS grid. The real row is
`q-item` + `q-item-section`, which ships its own padding, min-heights and `--side`
alignment rules. The current stylesheet is **already** losing a fight with them:
the mobile block at `:3410` is largely `min-width: 0; padding-left: 0;
padding-top: …` overrides that exist only to undo Quasar defaults.

Building v4 on top of `q-item` yields the new spacing *plus* Quasar's, which lands
as "slightly nicer than today" — precisely the disappointment W11 describes.

**Mitigations, all mandatory:**

1. **Own the structure.** Drop `q-item` for the line row (§4.1). This is the same
   lesson `CollapsibleCard` encodes — own the structure, own the surface.
2. **Verify in the running app after chunk 1, before chunk 2.** Not at the end.
   The gap must surface while it is still cheap to correct.
3. **Check every theme**, light and dark, not only Pesto (§1.6).
4. **No magic numbers.** Every size, radius and space traces to a token. The
   off-scale values catalogued in §1.3 are removed, not carried across.

---

## 6. Direction C — deferred, not rejected

C (a dense plan table with column headers and a running total; oversized thumb rows
for the run face) is the better long-term fit, and the owner likes it (W6). It is
deferred because:

- It retires the v3 card shipped 2026-08-29.
- It requires two row components and a new table primitive.
- **B's row grid is the stepping stone to it.** C's table is the chunk-1 row at
  tighter density with a column header — an evolution, not a rewrite.

Revisit after v4 lands and has been lived with. Related: `FU-780` (extracting
`ShoppingListPlanFace.vue`, R-001) is a natural companion to C.

---

## 7. Open decisions

### 7.1 Quantity tile vs stepper

Replacing `− n +` with a tap-to-edit tile is a density win but costs one-tap
increment.

**CLOSED 2026-08-31 (owner): tile at rest, stepper on hover/focus.** Density at
rest, one-tap increment on approach. Three constraints this puts on chunk 1:

- **Touch has no hover**, so the tile must expand to the stepper on *tap* while
  keeping tap-to-edit reachable — this is a §7.4 touch-path row in the baseline,
  not an afterthought.
- The swap must not **reflow the row**. The stepper has to fit the tile's own
  footprint (or a reserved width), or every hover shoves the money column
  sideways — reintroducing W3 as a motion bug.
- Keyboard parity: focus reveals the stepper identically, and the revealed
  buttons are real tab stops meeting D-004's 44px floor.

### 7.2 Hero gradient on the card band

The strongest available answer to W1/W2, and the element most likely to date.

**CLOSED 2026-08-31 (owner): gradient on plan + run, flat on receipt.** This
promotes the band from decoration to a **state channel** — gradient means the list
is still happening, flat paper means it is a finished record — reinforcing W7's
"visually indicate it is now a receipt" through material rather than layout alone.
See §4.2 and §4.3. Flat still means a defined white sheet on the canvas, not
borderless.

Carry-through: the dark-theme inversion (§1.6) applies to the gradient faces too —
`--hero-gradient` is per-theme, so it re-themes for free, but the *card-vs-page*
separation it sits on still has to be re-established by lightness rather than
shadow in dark themes.

### 7.3 What leads the card in T0 (money off)

The default install has no dollar figure. The current fallback is the raw item
count, which is weak for the primary headline slot of the page's primary card.
Candidates: progress toward the shop, item count with the shop day promoted, or
section coverage. **To be resolved during chunk 0**, once the baseline records what
T0 actually renders today.

**Status: OPEN — resolved by chunk 0's findings.**

### 7.4 Touch paths for hover-revealed controls

Swipe, long-press, or a per-row overflow menu. **To be resolved during chunk 0**,
per affordance, in the baseline table.

**Status: OPEN — resolved by chunk 0.**

*Open decisions — swept 2026-08-31. **7.1 and 7.2 are CLOSED** by owner call, with
the decision and its consequences recorded inline above. **7.3 and 7.4 remain
open by design**, both resolved by chunk 0's output rather than needing a call
now. No item is left undecided without a named resolution point (per the FU-364
rule), and no FU was spawned — every one has a home inside this document.*

---

## 8. From the original spec

Skimmed `docs/00_original_spec/Feature Boards/Shopping Lists.md` (historical,
non-authoritative). Nothing there overrides the charter or current feedback. Two
items are worth carrying as surface considerations:

- **keep** — *"I can see the total price of my shopping list including ticked off
  items"* and *"…excluding ticked off items (remainder)"*. Both survive today as
  `total_price` / `remaining_price`, and the run face leads with remaining. v4 must
  keep both legible; the baseline census records where each renders.
- **consider** — *"I can sort my shopping list items by my own defined order"*.
  Manual `sequence` reorder exists, but v4 moves the reorder arrows to
  hover/overflow. The census must confirm the manual order remains discoverable,
  since the original spec treats it as a first-class capability rather than a
  power-user affordance.
- **superseded** — the deal-refresh and per-offer-selection items are gated behind
  the `products` flag and belong to the T2 tier (§3); they are not a design target
  for the common case.

---

## 9. Chunk sequence

| # | Chunk | Gate |
|---|---|---|
| 0 | Behavioural baseline (`SHOPPING_LIST_BASELINE.md`) | **Blocking.** Nothing starts before it. Resolves 7.3, 7.4. |
| 1 | The row — grid, `q-item` removal, control diet, type scale, quantity tile→stepper (7.1) | **Running-app verification before chunk 2** (§5). |
| 2 | The overview card — surface, tiers, dark-theme inversion, gradient on plan+run (7.2) | — |
| 3 | The receipt face — direction A as a `face` variant | ✅ **Done 2026-09-01.** Shipped as a shared *skeleton* (`src/css/shoppingRow.scss`) consumed by both faces rather than a `face` **prop** on one component — see the note under §4.3. Baseline §5.3 filled, nothing cut. |
| 4 | Cutover audit: every baseline row has a filled destination + decision | ✅ **PASSED 2026-09-01.** No cell reads `TBD`; nothing was `CUT` across the whole rebuild. Caught three things nothing else would have — P8 never existed, chunk 1 orphaned 165 lines of dead CSS, and the run face had been left behind. |
| 5 | The run face — same containers, same row skeleton (FU-807) | ✅ **Done 2026-09-01**, owner call: *"consistency matters"*. This completes §4's "direction B for plan/run"; the three faces now share one stylesheet. |

---

## 10. Feedback coverage

| # | Bullet | Where addressed |
|---|---|---|
| W1 | Bland, flat, uninspired | §1.1, §4.1, §4.2, §7.2 |
| W2 | Plain/default card, default borders, all square | §1.1, §4.1, §4.2 |
| W3 | Rows horrible, misaligned, weirdly offset | §1.2, §4.1 (chunk 1, first priority) |
| W4 | Text small where it should be big | §1.3, §4.1, §4.2 |
| W5 | Overview card could look 1000% nicer | §4.2 |
| W6 | Likes B and C | §4 (B adopted), §6 (C deferred with rationale) |
| W7 | A for receipts, with a bit of fun | §4.3 |
| W8 | No unconscious loss of functionality | §2 (census + Decision column), §9 chunk 4 |
| W9 | Fear of accidentally hiding something | §2 (hover-is-a-loss-on-touch rule), §1.5, §7.4 |
| W10 | Savings smells like offers; offers are niche | §1.4, §3 (tier matrix, T1 as centre of gravity) |
| W11 | Demos flatter the end result | §5 (all four mitigations) |
| W12 | Document existing behaviour before rebuilding | §2 (chunk 0, blocking) |

---

## 11. Standing-rules check

- **R-001** (componentisation) — chunk 1 does not reduce `ShoppingListDetail.vue`
  below the R-001 threshold; `FU-780` remains open and is not resolved here.
  Flagged, not silently carried.
- **R-002 / R-035 / D-rules** — no Quasar palette names in templates; every value
  from a token (§5 mitigation 4). Contrast floors re-checked per theme (§1.6).
- **R-003** (state ownership) — v4 changes presentation only. No figure is
  re-derived client-side; `detail.totals` stays authoritative, as v3 established.
- **D-004** (tap targets) — the control diet must not shrink any surviving target
  below 44px; recorded per affordance in the census.
