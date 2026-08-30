# Design brief — the meal planner's recipe rail, page shell, and calendar

**Build status (2026-08-30):** **Unit 1 (app-shell) and Unit 2 (the rail) are
built and driven live.** **Unit 3 (the month-grid calendar) is not started** —
and when it lands it must also update `DESIGN_REMEDIATION_PLAN.md` to record
DR-12 as overruled by D7. Two deviations from this document are deliberate and
recorded in the worklog: Unit 1's toolbar needed a `compactToolbar` fallback the
§3.2 acceptance criteria didn't anticipate (it met "≤96px at 1280" but wrapped
at 1024), and Unit 2's chip row wraps to three lines at 280px rather than §4.3's
predicted two. One §4.5 instruction was **not** followed and is logged as
**FU-791**: the rail row's chrome was not promoted to a shared class, because
that means re-skinning `StockItemRow` and `RecipeRow` in a rail-scoped unit.

**Status:** **approved to build, 2026-08-29.** All eight §9 decisions were
answered by the owner in a single confirmation pass (see §9 — each carries its
answer inline); **FU-782 is resolved**. Two answers depart from the brief's
recommendation — **D3** (rail is always closed on arrival, no empty-week
auto-open) and **D4** (no page title at all, not even the week range promoted
to one). The four §2.5 items that revise earlier owner feedback were put to the
owner explicitly and confirmed: F9 (drag), F13 (calendar), F40 (title) and F43
(cookable-now) are all revised as this brief proposes.
**Governs:** the planner page's *layout and recipe-choosing interaction*.
[PROPOSAL_MEAL_PLANS.md](PROPOSAL_MEAL_PLANS.md) (Wave C-2) stays the master for
the surface's shape and data model; this brief does not restate its domain
behaviour, cook batches, reconcile, or templates.
**Raised:** 2026-08-28, from owner feedback in session — *"I really hate the look
and feel of the left side where you pick and search for recipes… nothing is off
the table, even transforming it to some other form factor… the calendar also
looks not that great."*

**Owner's synthesis after a first round of nine options** (the actual brief):
keep the rail but collapse it by default; open it on click, and also on a
slot-click with a pulse and clear highlighting of the destination slot; click
another slot to swap destination; use the cookbook's compact row; replace the
accordions with quick-filter chips; add a *Dora suggests* chip alongside them;
make the middle column its own scroll region like Stock Overview; give the right
rail its own scroll or merge it; move next-week up beside prev-week; and for the
calendar, take the month-grid direction with pips, clickable days and real dates,
polished with hover and animation.

---

## 0. Relationship to prior docs — read this first

**This is not a greenfield brief.** Three existing docs already hold territory
here, and one reached owner-resolved decisions on the same three topics.

### 0.1 `IMPL_PLAN_MEAL_PLANS_REBUILD.md` (2026-06-25) — the direct predecessor

A `/design-critique` pass on this exact page. **Its findings agree with the owner's
2026-08-28 complaint almost verbatim**, which is the strongest evidence this brief
is addressing something real and not a matter of taste:

- **U2** — *"Non-sticky context columns. Scrolling the week scrolls the palette
  and the shopping rail off-screen — the drag source and the impact readout
  vanish mid-task."* That is the owner's "the middle section scrolls beyond the
  left rail", found two months earlier.
- **U1** — empty-slot sprawl (🔴). **U3** — mobile scroll-pogo (🔴).
  **U4** — wasted desktop width (🟡).
- §5: *"3-column centre-weighting + non-sticky columns waste width and drop
  context on scroll."*

**What that doc proposed, and how this brief differs:**

| Topic | Rebuild plan (2026-06-25) | This brief | Relationship |
|---|---|---|---|
| Left rail | §8.1 — *"On-demand pinnable picker drawer from a cell `+`"* | Collapsible in-place rail, never a drawer | **Narrows** — same instinct (on-demand), different mechanism. The drawer route was chosen before D-023 existed (2026-08-28); a per-mode drawer is now the thing D-023 warns about. §4.2. |
| Scroll fix | §6.4 — sticky side columns + a *"full-width, sticky consequences bar"* | Fixed-height three-pane shell | **Supersedes**. Sticky columns were the partial fix; they shipped (`.planner-sticky`) and the owner is complaining about the result. See §3.1. |
| Calendar | §8.1 — *"Month-jump popover in the top strip"*; but §4.7 lists the widget under **"What works well (keep)"** | Month grid, stays in the right pane | **Supersedes both**. §5, and the honesty note in §2.5. |
| Direction A vs B | §8 Q1 — *"keep the experiment, don't pre-pick"*: upgrade this page to Direction A, build a separate Direction-B board page, add a temporary toggle | Single page | **Already superseded by FU-304** (closed 2026-07-07 — Direction A won, the toggle and `/meal-plans/board` were retired; recorded at `MealPlansOverview.vue:65-68`). This brief does not reopen it. |
| Q4 mobile picker | ✅ resolved → bottom-sheet from a cell `+` | Unchanged | **Honoured.** §3.4, §4.8. |

**Also inherit from it:** its §13 re-grade of all 49 feedback bullets, which
marked **13 as 🟡 regressed/new-concern** — including F16, F20, F41, F42, F44,
F46, F9 and F22, i.e. precisely this brief's three topics. Its §15 instructed a
`COVERAGE_GAPS.md` flip that **never happened**; §11 of this brief does it.

### 0.2 `DESIGN_REMEDIATION_PLAN.md` DR-12 — a live directive on the calendar

DR-12 (P2): *"Actionable list first; calendar becomes a labelled 14-day strip
(counts on cells) or moves below; same treatment for the meal-plans mini-month."*
Its coverage table records item 16 as *"rides the redesign"* — **DR-12 is waiting
on this document.**

**This brief argues against the strip** and takes the month grid instead. The
reasoning: DR-12's target was the *Alerts* page, where a calendar competed with
an actionable list and lost. On the planner the calendar is not competing with an
action list — it is the surface's navigation, and the fault is the opposite one
(it looks like a calendar and doesn't behave like one). Reconciled in §5;
**flagged as decision D7** because overruling a standing remediation directive is
the owner's call, not a brief's.

### 0.3 `PROPOSAL_MEAL_PLANS_PART_2.md` — layout-neutral, must survive

Cook batches are explicitly *"no layout restructure"*. Its **per-entry linked
cook marker** must survive whatever slot shape this brief produces. Designed, not
built (FU-617).

---

## 1. Scope, and the three units

| Unit | What | Risk |
|---|---|---|
| **1** | Page shell: fixed-height three-pane layout, consolidated toolbar, right-pane split | High — largest change, one behavioural casualty |
| **2** | The rail: collapse, chips, compact rows, targeting, *Dora suggests* endpoint | Medium — three picker consumers + a server endpoint |
| **3** | The calendar: month grid, focusable days, pips, motion | Low — mostly a restyle, but depends on Unit 1 |

**Out of scope**, explicitly: the day-card internals (slot rows stay rows — F46
asked for that and got it), the auto-build wizard's own flow, reconcile, cook
batches, print, recurring plans, and the meal-plan data model. No new domain
concepts.

---

## 2. Why the current rail fails

Five faults. Recorded because the fix must answer each, and a future session will
otherwise re-litigate them.

1. **It is a filing cabinet.** Rows are plain text — which is the *correct* call,
   but not for the reason it looks like. See the image finding in §4.5.
2. **Two scroll mechanics nested in the page's narrowest column.** Four
   `q-expansion-item` trays inside `max-height: 65vh; overflow-y: auto`
   (`MealPlanRecipePicker.vue:232-236`), itself inside a second scroller
   (`.planner-sticky`, `MealPlansOverview.vue:634-639`).
3. **Roughly eight recipes visible.** Three of four trays are
   `defaultOpen: false`, so the resting state is mostly chrome. Directly against
   **F21** — *"it can hold hundreds of recipes"*.
4. **The mode change is announced in the quietest place available.** The rail is
   inert until a slot is targeted, and *"Adding to Dinner, Tue 25 Aug"* renders
   as a small `q-banner` above the list (`MealPlanRecipePicker.vue:15-23`).
5. **It holds 25% of the screen permanently** for a widget used in bursts —
   **F44**, which the owner raised in June: *"I am concerned with squishing the
   main working area too much."*

### 2.5 Four places this brief contradicts the owner's own earlier feedback

**These are the highest-risk items in the document.** In each case the current
code is a faithful implementation of a June-2026 request, and the August-2026
synthesis asks for something different. None can be treated as settled.

**(a) The calendar the owner is unhappy with is the calendar the owner
specified.** **F13** (`Feedback [06-Jun-2026].md:360`) reads: *"I'm picturing a
custom calendar widget for this as the week picker where the active week
highlights (colour/fill the squares), only the first day in each row displays any
text (the date but only DD…). Month at the top banner. The status of individual
days in the calendar is marked with underline under the day squares. The squares
are rounded boxes and that's it (minimalist look maybe? Futuristic?)… Help me
design this well!"* — and `MealPlanCalendar.vue` is precisely that, down to the
`border-bottom` status underline and `showLabel: i === 0`. The rebuild plan then
listed it under *"What works well (keep) — on-brief and elegant."*
**The month grid in §5 abandons this design.** That is a legitimate revision — the
owner has now seen it built and doesn't like it, which is exactly what feedback
is for — but it must be an explicit revision, not a silent overwrite. **Decision
D7.**

**(b) The bottom next-week arrow was requested, not inherited.** **F16/F17**
(`:363`): *"scrollable carousel, where scrolling reveals the previous or next
week. There should be an up arrow above the area to click previous and down arrow
below to go next. This should come with a nice smooth animation. The calendar
widget should change with it."* Moving next-week into the toolbar reverses the
"arrow below" half of that request. The *"calendar changes with it"* half stays
honoured. **Decision D8.**

**(c) Retiring drag-and-drop contradicts F9 head-on.** **F9** (`:349`):
*"Anywhere you can drag/drop, there should be a tap/click menu. Drag/drop is a
power user option. Offer both and let the user pick how to use the app."* The
recommendation in D1 is to retire drag because the new scroll model breaks it
below the fold. That is a direct reversal of a stated principle, and the
principle was about user choice rather than about drag specifically. **Decision
D1 — do not treat the recommendation as pre-approved.**

**(d) A `cookable_now` reason chip may be unwelcome on this page.** **F43**
(`:392`): *"Do I need to know if something is cookable now on this page? This is
the planner, not the cookbook. Suggest meals I can cook now and the green
highlighting with a checkmark feel like they don't belong."* The *Dora suggests*
vocabulary includes `cookable_now` → *"You have everything for this"*. It is
milder than the green-check treatment F43 objected to, and it is a *reason for a
suggestion* rather than an ambient status — but it is the same fact on the same
page. **Decision D6.**

**Related standing risk — F41.** *"The colouring and iconography feels so
conflicting on this page, between the recipe list, the shortfall banner and the
meals planned on the days. Perhaps there's too much going on."* This brief adds
accent-coloured surfaces: an active filter chip, a filled target banner, a filled
target slot, an accent day-card border, and calendar pips. **The unit is not
done until someone has counted the simultaneous accent surfaces on a populated
week and judged it against F41.** Put it in the verify list, not the "nice to
have" pile.

---

## 3. Unit 1 — the app-shell conversion

### 3.1 The scroll model

Convert `MealPlansOverview.vue` from **document-scroll** to the **fixed-height
app-shell** shape — the second of the two shapes R-036 already sanctions. A shape
*change*, not a new pattern.

**Why sticky columns were not enough.** The rebuild plan's U2 fix shipped:
`.planner-sticky` pins both side columns. The owner is still complaining, because
sticky-inside-document-scroll keeps the columns *visible* while the page's own
chrome scrolls away, and it leaves the drag source and the drop target in two
different scroll contexts. The fix is to stop the document scrolling at all.

**Canonical implementation — copy `StockOverview.vue`, do not invent:**

```
<q-page class="q-pa-md meal-plans" :style-fn="pageStyleFn">
```
```ts
function pageStyleFn(offset: number, height: number) {
    return {
        height: height === 0 ? `calc(100vh - ${offset}px)` : `${height - offset}px`,
    };
}
```
Reference: `StockOverview.vue:2` and `:843-853`.

Then the canonical inner-scroller shape (`.stock-list`,
`StockOverview.vue:1721-1836`):

- Page root: `display: flex; flex-direction: column; min-height: 0`.
- Page-level chrome (reconcile nudge) keeps natural height.
- The pane row: `flex: 1 1 auto; min-height: 0`.
- Each scrolling pane: `flex: 1 1 auto; min-height: 0; overflow-y: auto`, with
  `scrollbar-gutter: stable`.
- **Padding on the scroller, not the pane** — Stock Overview documents this
  specifically.

**Three panes, and exactly which scroll:**

| Pane | Width | Pinned | Scrolls |
|---|---|---|---|
| Left — rail | 46px collapsed / 262–300px open | search + chips + target banner | the recipe list |
| Middle — week | fills | toolbar + status strip | the seven day cards |
| Right — context | ~300px | the calendar | shopping summary (+ swaps, if D-moved) |

**R-036 bookkeeping this unit owes:**
- Move Meal Plans from the document-scroll list to the app-shell list in
  `ENGINEERING_STANDARDS.md` R-036 "Apply".
- Rewrite the page header comment (`MealPlansOverview.vue:3-6`), which currently
  states the sticky columns rely on the window scroller.
- Record it as an **application of ADR-032**, not a new ADR.

**A latent bug this fixes.** `.planner-sticky` uses
`max-height: calc(100vh - 32px)` with no account for the 64px header
(`MainLayout.vue:329-333`), so both rails currently overhang the viewport by
about a header's height — and by a further 48px whenever `OfflineBanner` renders.
That is the exact failure R-036's *"never hardcode the offset"* clause exists to
prevent. Taking the live `offset` removes it. **Do not** fix it by subtracting a
literal 64.

### 3.2 The consolidated toolbar

The middle pane gets a pinned two-row header.

**Row 1:** `‹` `›` · **week range** + a relative sub-label (*This week* / *Next
week* / *3 weeks ago*) · spacer · **Build my week** · `⋮`.

Answers **F40** (*"don't need the title 'Week of…'"*) — the range is the label,
with no redundant prefix. Follows **L102**'s app-wide directive: *"All buttons
should be the same width and height… Make a standard toolbar with a standard
toolbar button."*

**Row 2 — the status strip:** the existing `MealPlanWeekStatus.vue` content
unchanged in substance (planned count, cook-by when `batchEnabled`,
outstanding-to-buy, already-on-a-list). It moves from a block that scrolls away
into pinned chrome — which is what its own comment says it is for. It is also the
single home for the shortfall figure, answering **F45** (*"Is the shortfall
banner needed? It's showing information twice"*).

**⚠️ Placement conflict — see D8.** The owner has asked **three times**, in
app-wide terms, for page counts to be a **sticky footer**: L93 (*"Counts should
be minified and moved to the bottom of the page as a sticky footer (add space
between the footer and the scrollable area)"*), L212, and L231 (*"should be a
componentised sticky footer. Consistency!"*). That component exists —
`PageCountsFooter.vue`, used by Stock Overview, Cookbook and My Products. Putting
the planner's status at the *top* breaks that consistency. Both placements are
defensible (this is a *status* strip, not a count of listed records) but the
inconsistency must be a choice.

**The `⋮` overflow menu:**
1. Duplicate to next week
2. Print this week
3. — separator —
4. Save week as template…
5. Browse + apply templates…
6. — separator —
7. Show all meal slots (toggle, checked state visible)
8. — separator —
9. **Clear week** (danger colour, keeps its label — **F37**)

**Removed from the page body as a result:**

| Removed | Was at | Note |
|---|---|---|
| Bottom "next week" arrow | `:222-227` | **Reverses F17 — see D8** |
| `Show all slots` toggle row | `:132-146` | A full row for one preference |
| Duplicate / print / clear-week buttons | `:105-130` | Three siblings, one destructive |
| Templates card | `:259-277` | A right-pane card wrapping one drawer button (**F12** stays satisfied — the drawer is unchanged) |
| `MealPlanWeekStatus` as a scrolling block | `:150-156` | Becomes row 2 |

**Acceptance:** at 1280×900 with `batchEnabled` and a full week, the toolbar
occupies ≤ 96px, nothing wraps to a third line, and there is no horizontal page
scroll from 1024px up (D-011). **FU-738 is the cautionary tale** — a toolbar band
allowed to overflow put the primary CTA off-screen on the shopping list.

### 3.3 The right pane

Calendar pinned at the top, shopping summary scrolling beneath. This keeps
**F14** honoured verbatim (*"This widget I picture being on the right above the
shopping info"*).

**Do not merge the right pane into the middle one.** The calendar is navigation,
and scrolling navigation away repeats the bottom-arrow mistake; the shopping
summary is the payoff of planning, so putting it below seven day cards buries it.
This also answers the other half of **F44** — the owner's June suggestion was to
move the *recipes* into the right column; collapsing the rail achieves the width
goal without stacking two jobs in one column.

`MealPlanShoppingSummary.vue` needs no logic change; **F30** (hover-to-highlight),
**F31** (per-item list status), **F32** (individual + bulk add) and **F7** (shared
stock-level colouring) all keep working. Confirm its *Full ingredient demand*
`q-expansion-item` doesn't fight `scrollbar-gutter` when expanded inside a
scroller.

### 3.4 Mobile is untouched, and the CSS must say so

`MealPlansOverview.vue:33-64` already routes `$q.screen.lt.md` to
`MealPlanMobileFocus.vue`, with `MealPlanPickerSheet.vue` as the picker — which is
the rebuild plan's resolved **Q4** and answers **F8**. **Every fixed-height rule
in this unit is scoped `@media (min-width: 1024px)`**, exactly as
`.planner-sticky` is today. `SettingsShell.vue:463-467` is the precedent escape
hatch (`height: auto !important` on mobile).

### 3.5 Drag-and-drop is the casualty — see D1

Planner DnD will **silently stop working below the fold** once the week owns a
scroller.

- **Native HTML5 drag**: `draggable` + `dragstart`/`dragend` on the row,
  `@dragover.prevent` + `@drop.stop` on the slot
  (`MealPlanRecipePicker.vue:36-46`, `MealPlanWeekDayCard.vue:42-43`,
  `useMealPlanner.ts:192-214`).
- **The payload rides on a module ref** (`draggingRecipeId`), not `dataTransfer`
  — so the slot's bare `@dragover.prevent` accepts any drag (text, a file, an
  image) and `onDropOnSlot` only early-returns because the ref is null. No
  accept/reject cue, no drop-effect. (`useDragDropList.ts` does this properly with
  a MIME guard; the planner is the looser of the two.)
- **No edge auto-scroll anywhere in the app** — a repo-wide `scrollBy` grep is
  empty. Native auto-scroll inside a nested `overflow: auto` container is
  historically weak in Firefox and flaky in WebKit.
- Already **desktop-mouse-only**: `onRecipePointerDown` sets
  `dragAllowed = false` for `pointerType !== 'mouse'`.
- Does not use `.dora-dnd-*` or `useDragDropList` (those serve the reorderable
  list editors).

Note also that **F48** (*"I shouldn't have to drag one by one to increase the
count of a meal"*) and **F47** (duplicate drops should increment) were both
answered by the per-entry `Servings: ±n` control rather than by drag — so drag's
remaining unique value is small.

### 3.6 Why layout goes first

- The calendar's payoff — click a day, the week pane *scrolls to that day's card*
  — is only possible once the middle pane is a scroll container.
- D1 is a consequence of this unit.
- Building the rail first means building it twice.

### 3.7 A constraint the whole design depends on

**Day cards must stay a vertical stack of full-width blocks, with slot rows
inside them.** When the rail expands 46px → ~262px, the middle pane narrows;
because each card is a full-width stacked block, that reflow is **horizontal
only**, so a card's vertical position doesn't move and the slot just clicked
stays under the cursor. If the week ever became columnar, rail expansion would
move the target slot and the auto-open interaction in §4 stops being safe.

This is also already the owner's ask: **F46** (*"Could the time of day be made
into rows instead of displaying on the meal cards?"*) — implemented, keep it.
And **F27** (cards not fitting) was fixed by that same row shape. Record the
reason, or a later session will "improve" the week into a board and break both.

---

## 4. Unit 2 — the rail

### 4.1 The three states

**S1 — resting, collapsed (default).** A 46px vertical strip in the rail's
position: search glyph, a small accent dot when a filter is active, a vertical
`Recipes · 47` label, expand chevron. Full-height, no scroll.

**S2 — open, browsing.** ~262–300px. Pinned header: collapse affordance, search
input, chip row. Scrolling body: one flat list of compact rows.

**S3 — open, targeting.** As S2, but the header's first element is a filled
accent banner naming the destination — *"Adding to Wed 26 · Dinner"* — with a
`✕`. Rows grow a `→ Dinner` label on hover/focus.

### 4.2 The collapse contract — D-023 pushes back, resolution is "one-way"

`DESIGN_STYLE_GUIDE.md` **D-023** (`:636-666`): *a persistent control keeps its
shape and its place across modes… do not re-home it, and do not swap a
persistent control for a differently-shaped stand-in that does the same job.*
The establishing case is **a shopping-list side rail hidden per mode**, with the
owner's verdict of **2026-08-28**: *"this will only lead to confusion with UI
elements shape shifting."*

That rule is the same age as this brief and lands on it directly. **It is also
why this brief rejects the rebuild plan's "picker drawer" route** (§0.1) — a
drawer that appears per mode is the shape D-023 now forbids.

**Why a collapse toggle is nonetheless compliant:** D-023's stated violation
signal is *"two controls with different shapes and the same verb, each `v-if`'d
to a different mode."* A user-operated disclosure is one control in one place
whose size the user chose. The strip is deliberately **labelled**, not a bare
icon, so it reads as the same rail, smaller.

**Why auto-open needs its own rule, and what it is:** opening the rail because a
slot was clicked *is* a mode-driven change.

> **The system may only ever open the rail. It may never close it.**
> No auto-collapse after an add, on target cancel, or on week change. Nothing
> shape-shifts under the user unless the user did it.

**This must be a named carve-out comment in the component citing D-023**, or a
future tidy-up will "fix" the rail to close after an add and reintroduce exactly
the confusion the rule exists to prevent.

### 4.3 The chip row

`✨ Dora suggests` · `All` · `★ Favourites` · `Not lately` · `Regulars`

Wrapping to two lines at 262px; **never** horizontal scroll (D-011). This is the
direct answer to **F21** — *"It should be filterable and vertical because it's a
list, and it can hold hundreds of recipes."*

Three behavioural changes from the accordions:

**(a) The dedup must go.** `buildRecipeTrays` (`helpers/recipeTrays.ts`)
deliberately gives each recipe exactly one tray — FU-578 #47, because a favourite
appeared under both `Favourites` and `All recipes` and rendered two checkboxes in
the wizard. As *filters* that is wrong: `Regulars` should list every
frequently-planned recipe, favourites included. Filters solve the double-render
inherently — one active filter, one list. So the builder becomes **independent
predicates over the same fields**, and FU-578 #47 is **superseded, not
regressed**. Say so in the worklog; it will otherwise read as a regression.

**(b) Empty chips stay, disabled + tooltip'd.** B2a: *"Options that can't be
chosen stay in place, disabled + tooltip'd — don't filter them out. A row that
reflows as options drop away costs the user their spatial memory."* Today empty
trays are hidden entirely.

**(c) It is a new small component.** Neither shared control fits: `BaseSegmented`
is capped at 2–4 options by B2a and this is five; `BaseToggleGroup` is for
*independent* choices and these are mutually exclusive. Build a small chip-row
component with the full state set (hover / active / focus-visible / disabled /
selected — D-016), `aria-pressed` per chip, and the active fill from the
**indicator** token — **D-020 names active filter chips explicitly**. Follow the
app-wide filter conventions from L99–L100: *"Keep search filter separate to other
filters"* (the search input stays above the chips, not inside them) and
*"Filter button changes based on filter state"* (hence the accent dot on the
collapsed strip).

**Predicate sources — all server-derived, do not recompute:**

| Chip | Predicate | Field |
|---|---|---|
| All | — | — |
| ★ Favourites | `is_favourite` | `Recipe.is_favourite` |
| Not lately | `not_made_recently` | server-computed, household 21-day window |
| Regulars | `plan_count > 0`, ordered desc | `Recipe.plan_count` |
| ✨ Dora suggests | server ranking | §4.4 |

**An R-003 leak to fix while the file is open.** `recipeTrays.ts` sorts the
"haven't had in a while" tray by `last_made_on` **on the client** (`madeMs()`)
while the server already ships `not_made_recently`. Selection uses the server
flag; only the ordering leaks. Order server-side or drop the ordering — do not
keep a client-side recency computation.

**A candidate sixth chip, not proposed:** **L271** asks *"Would a filter 'planned
in' be useful? Where you can see recipes included in future/current meal
plans."* It has no home in any coverage table. It is a natural rail chip, but
five chips already wrap to two lines at 262px. Logged as a note, not a
recommendation.

### 4.4 *Dora suggests* — the engine already exists

The cheapest item in the brief, which is not obvious from outside.
`dora_api/features/meal_plans/build_week.py` already holds the ranking
apparatus, factored as **pure functions with no repository access** precisely so
fixtures can drive it:

- `RecipeCandidate` (frozen) carrying `expiring_count`, `cookable`,
  `is_favourite`, `plan_count`, `not_made_recently`, `cuisine_id`,
  `category_id`, `estimated_cost`, `servings`, `missing_stock_item_names`.
- `_base_score(candidate, emphasis, rng)` and `select_recipes(...)` with variety
  spread.
- A **frozen reason-chip vocabulary** (`:91-97`), annotated *"frozen server-side,
  R-003"*: `uses_expiring`, `cookable_now`, `favourite`, `not_made_recently`,
  `variety`, `budget_friendly`, `picked`.
- `reason_chip(candidate, emphasis, budget_swapped)`.
- The candidate-construction block in `compute_auto_build` (`:459-496`) —
  `_all_recipe_dtos`, `count_expiring_ingredients_per_recipe`,
  `estimate_costs_for`.

**The endpoint:** extract the candidate-construction block (currently inline in
`compute_auto_build`) into a reusable helper, then a read-only handler that
builds candidates, excludes recipes already planned in the focused week
(`_planned_recipe_ids_in_range` exists), calls `select_recipes` with the
**default** emphasis and a small `count`, and returns `[{recipe_id,
reason_chip}]`. No new domain logic, no new constants, no new vocabulary. R-003
holds by construction.

**Client copy map** (the token is the server's, the words are the UI's):

| Token | Copy |
|---|---|
| `uses_expiring` | Uses stock that's expiring |
| `cookable_now` | You have everything for this — **gated on D6** |
| `favourite` | A favourite |
| `not_made_recently` | Haven't had in a while |
| `variety` | Adds variety |
| `budget_friendly` | Cheaper — keeps you on budget |
| `picked` | *(no line — render the normal meta line)* |

**Two things this chip must not do.**

1. **It is not a filter.** It changes *ordering* and adds a reason line; it does
   not narrow a set. Putting it in a filter row is a real semantic mismatch,
   worth paying for because it is the most valuable thing in the rail — but it
   must be *marked*: first position, leading sparkle, accent outline even when
   inactive, rows visibly change shape when active.
2. **It must not surface the four emphases.** `MealPlanBuilderDialog.vue:62`
   already exposes a `BaseSegmented` over `use_up_stock` / `variety` /
   `favourites` / `surprise` for the same engine. Two vocabularies for one idea
   on one page is how a surface gets confusing. The rail's chip calls the default
   emphasis and stays one button. If emphasis-picking in the rail is ever wanted,
   it *supersedes* the builder's control rather than joining it.

**F23** (*"I should be able to ask Dorabot to assist with meal planning"*) is
adjacent and deliberately untouched: this chip is a ranked list with reasons, not
an assistant turn. It does not close F23.

### 4.5 The rail row component

**The image question is settled, and not by preference.** `RecipeRow.vue:23-27`
records an owner call of 2026-08-18: the show-photos toggle was folded into the
cards/compact switch, so *compact is definitionally the without-photos shape* and
the row does not consult `show_recipe_images` at all. Independently,
`dora_api/persistence/seed_builders.py:199` sets `image=None` on every seeded
recipe, so a freshly seeded install has **zero** recipe photos and every card
falls back to a name-hashed letter tile. **The rail is text-first.** Any future
thumbnail proposal must first answer the seed-coverage problem.

**`RecipeRow` cannot be dropped in as-is.** Four blockers:

1. `compact` is derived from the **viewport** (`$q.screen.lt.sm`, `:186-187`),
   not a prop. In a 262px rail on a desktop it thinks it has full width.
2. The trailing cluster is `flex: 0 0 auto` at ~180–200px (rating + favourite +
   cook + add-to-list); only the name zone shrinks, leaving ~60px for the name.
3. The squeeze that would help is behind `@media (max-width: 599px)` (`:286-300`)
   — a viewport query, so it never fires for a narrow rail on a desktop.
4. Its four actions are **cookbook verbs**. The rail's only verb is *add to the
   targeted slot*.

**Therefore a new `MealPlanRecipeRow.vue`:**

- **Share the derived figures, not the component.** Read `totalTime`,
  `ingredientCount`, `kcal` from `useRecipeDisplay` — the same composable both
  cookbook views use — so the rail cannot drift (R-003).
- **Promote the chrome to a shared class** rather than a third copy.
  `.recipe-row`'s look (bordered flat card, accent-tinted hover, no lift) is
  itself inherited from `StockItemRow`. Extracting it is the `.dora-subbar` move
  — precedent R-022 / ADR-018.
- **Density is an explicit prop** — not a container query, not a viewport sniff
  (R-019 / ADR-014).
- **The row is a real focusable control** with a visible `:focus-visible` ring.
  `RecipeRow` is a `q-card` with a click handler and no focus state, so it misses
  D-016 / A6 today — do not inherit that gap.
- **Keep the batch-cook controls when `batchEnabled`.** The current picker
  carries a `− N +` pool stepper and a "log a cook" action per row
  (`MealPlanRecipePicker.vue:69-98`, via `adjustPaletteMeals` / `logPaletteCook`).
  **F26** makes batch households a first-class audience and **F42** complains
  the on-hand count *"is a bit hidden, could be better displayed… make the
  number bigger maybe"* — so this is not merely to be preserved, it is a known
  open complaint. At 262px it likely needs the row's hover/expanded state rather
  than an inline cluster. Note that `PROPOSAL_MEAL_PLANS.md` §3.1 already carries
  **FU-088** — *"cooked-pool stepper relocates here"* — as unimplemented.
- **Content:** browsing → name (max 2 lines) + one meta line of ≤2 facts;
  targeting → name + `→ <Slot>`; suggesting → name + reason phrase.
- **FU-693 lands here.** `.recipe-row__name` is `font-size: 1.05rem`, off the
  D-003 scale, kept only for parity with `StockItemRow`. A rail row is a *third*
  site. **Recommendation: use the token** — a 262px rail is not where that parity
  is legible. Note the choice in FU-693 either way.
- **Long cookbooks (F21):** the flat filtered list can render every recipe where
  trays capped shortcuts at 10. Stock Overview switches to `q-virtual-scroll`
  above 50 items and shares row height via `--stock-row-height`
  (`StockOverview.vue:830-841`); **the virtual item size and the CSS row height
  must agree exactly** or Quasar re-measures mid-scroll.
  `PROPOSAL_MEAL_PLANS.md` §3.1 already specified `q-virtual-scroll` here.

### 4.6 Targeting — visuals, keyboard, a11y

This is the mechanism **F22** asked for (*"Need some sort of method to add
recipes/meals onto the days without drag and drop"*) and **F36** diagnosed
(*"The fact there's an 'edit entries' button shows there is a gap with the
current main working area"*).

**Visual.**
- The targeted slot is a **filled** `--accent-soft` with an inset 2px accent bar.
  Today it is `outline: 2px dashed` + sunken fill
  (`MealPlanWeekDayCard.vue:207-211`) — which reads as an *empty drop zone*, and
  once drag is gone (D1) a drop-zone idiom is actively misleading.
- The targeted **day card** takes an accent border, so the target is findable
  without scanning slot by slot.
- The slot's hint becomes `← pick a recipe`.
- The destination is **named at both ends** — rail banner and slot label. At
  1280px+ they are far apart; naming both ends is the reliable version of drawing
  a connector.
- **Count the accent surfaces against F41** before closing (§2.5).

**Behaviour.**
- Swapping targets **already works**: `selectSlot` (`useMealPlanner.ts:171-177`)
  sets a new target or toggles off the same one. No logic change — only the
  clearer visual. Verify it reads as a *move*, not two events.
- **`Esc` cancels the target.** No `Esc` handling exists today; `onKeydown`
  (`:401-413`) binds only `ArrowUp`/`ArrowDown` to week paging.
- **Arrow bindings follow the nav.** Vertical arrows match a vertical carousel;
  with `‹ ›` in the toolbar, `ArrowLeft`/`ArrowRight` is consistent. Keep both or
  migrate — and update `ShortcutsCheatsheet.vue`.
- **Focus moves into the rail's search on auto-open.** Not optional: the pulse is
  visual-only, and moving focus is its keyboard equivalent.
- Register rail collapse/expand in `useShortcut` and the `?` cheatsheet.
- **Past days stay read-only.** `selectSlot` already warns and refuses
  (`:172-176`) — the guard that **F29**'s exception needed.

**Announcement.** The target banner is a live region, so a target change is
*announced*, not only drawn.

### 4.7 Motion — the pulse fires once

The owner asked for a pulse. The house has litigated this; the answer is **one
shot, not a loop**.

`motion.scss:88-97`: the one-shot classes are driven by `useMicroFeedback()` and
*"do not use them on a **persistent** condition: an animation that repeats on its
own becomes wallpaper (the retired stocktake row pulse is the cautionary tale)"*.
`StockItemRow.vue:1011-1022` carries the post-mortem: *"Do not reintroduce an
animation per row… One quiet marker per row, one loud signal at the top."*

**Spec:**
- One `dora-settle` or `dora-bump` on auto-open via `useMicroFeedback()`. Never a
  repeating keyframe, never bound to "a target exists".
- The **durable** signal is the static filled banner. **Test:** enable
  `prefers-reduced-motion` — every `--motion-*` token collapses to 0.01ms
  (`motion.scss:139-168`), so if the animation was the only thing saying the rail
  is armed, the design fails.
- Collapse/expand width transition on `--motion-normal` + `--motion-ease`. **No
  literal `ms`** (D-010).
- **Fix an existing D-010 violation while here:** the week carousel hand-rolls
  `transition: transform 0.18s ease, opacity 0.18s ease` with a literal
  `translateY(20px)` (`MealPlansOverview.vue:618-626`). This is the *"nice smooth
  animation"* **F16** asked for and it should keep working — just on tokens.

### 4.8 The other two picker consumers

`MealPlanRecipePicker.vue` has **three** consumers. All change.

| Consumer | Mode | Needs |
|---|---|---|
| `MealPlansOverview.vue` (desktop rail) | `click-add` | The full redesign |
| `MealPlanPickerSheet.vue` (mobile sheet) | `click-add` | Same chips + *Dora suggests*, so both breakpoints teach one model. Rows stay **≥44px** (D-004) even if the desktop rail goes denser. A thin wrapper, so most comes free. |
| `MealPlanBuilderDialog.vue` (auto-build wizard) | `multi-select` | Chips must work with row checkboxes. Holds the emphasis collision (§4.4). Its `BaseToggleGroup` day/slot rows are B2a's reference consumer — don't disturb them. |

`buildRecipeTrays` is shared by all three — which is why it was centralised (its
docstring records that the logic existed twice and drifted). One change, three
surfaces, consistently.

---

## 5. Unit 3 — the calendar

**Read §2.5(a) first.** The current widget is a faithful build of **F13**, and
the rebuild plan called it *"on-brief and elegant"*. This section revises the
owner's own June specification on the strength of his August reaction to it. That
revision is **D7**, and it also overrules **DR-12**'s "14-day strip" directive
(§0.2).

**The diagnosis.** The component is a **week picker wearing a calendar costume**
— only the week row is clickable (`MealPlanCalendar.vue:19-40`), yet the day
squares carry the status colour, so they invite a click that does something else.
Two secondary faults: the status underline is a 2px border on a ~20px square, so
the `aria-label` carries more information than the visual; and only each Monday
shows a number (`showLabel: i === 0`), so six rows read as a barcode. **F13
asked for both of those**, which is precisely why this needs a decision rather
than a fix.

**Grid.** Seven columns, Monday-first, weekday header letters, six week rows,
month paging via `‹ ›`. Every cell shows its real date with
`font-variant-numeric: tabular-nums`. Out-of-month days are dimmed but **still
clickable** — they belong to real weeks.

**Pips.** One per meal on that day, capped at three plus `+N`. Colours:
planned / short / cooked, reusing the existing `dayStatus` derivation
(`:79-88`) which already reads the server's shortfall set rather than re-judging
cookability — **keep that (R-003)**.

**States, each distinct (D-016):**

| State | Treatment |
|---|---|
| Default | `--surface-sunken` cell |
| Focused week | tinted band across all seven cells, outer corners rounded |
| Today | **filled** accent disc on the number (**F15**) |
| Hover | lift + tint + tooltip |
| `:focus-visible` | outline ring, offset |
| Out-of-month | dimmed, still focusable |

**Today must not be a ring.** A ring would collide with the focus ring the moment
days become focusable. Filled disc for today, outline ring for focus.

**Hover names the meals.** The tooltip lists the day's actual entries
("Lunch · Leftover ragù / Dinner · Green curry — short 1 cook"), not a status
word. This is the reason to make days interactive at all: the calendar becomes a
*read* surface, not only a picker. It also satisfies B2 / D-013 — a coloured pip
cannot be the only signal.

**Click a day → focus that week *and* scroll the middle pane to that day's
card**, with a single `dora-settle` on the arriving card. The payoff, and only
possible because of Unit 1.

**Week selection.** The grid remains the week picker, which keeps **F11**
satisfied (*"it should show options to pick from upcoming weeks… greyed out or
not shown if there's an active plan"*) — status is now per-day pips rather than
greying, which is strictly more information. **F17**'s *"the calendar widget
should change with it"* stays honoured: toolbar nav and calendar selection are
two views of one `focusedMonday`.

**Motion.** Month paging slides horizontally, direction-aware, mirroring the week
transition. Tokens only.

**Keyboard.** Arrow-key grid navigation with a roving tabindex;
`PageUp`/`PageDown` for months. The current six-week button list has none.

**Keep the accessible labels.** `weekAccessibleLabel`, `dayTitle` and
`STATUS_LABEL` (`:138-157`) are genuinely good work against 1.4.1 — port them to
day cells rather than rewriting.

**Theme.** New components read tokens only — **F38** was a theme-awareness
complaint on this page.

**Fit.** At ~300px cells land near 38px, above the pip legibility floor. If the
right pane narrows, re-check `+N` at `--font-size-xs` before shrinking pips.

**Shared-component note.** **L61** asks for a *"unified 'this fortnight' calendar
widget"* on the Dashboard with coloured dots and click-through — owned by the
dashboard rebuild, not this brief. But if this month grid is built as a component
that can render small and read-only, that card comes nearly free, and
`PROMPT_PLAN.md:209`'s *"mini calendar from P9"* wanted the same. Worth building
with that seam; **out of scope to use it**.

---

## 6. Ripple register

| Surface | What happens | Severity |
|---|---|---|
| `MealPlanPickerSheet` | Same chips + *Dora suggests*, or the breakpoints teach different models. ≥44px rows (D-004). | must |
| `MealPlanBuilderDialog` | Chips must work with `multi-select`; emphasis collision (§4.4). | must |
| `buildRecipeTrays` | Independent predicates; FU-578 #47 dedup superseded. Three consumers. | must |
| `MealPlanMobileFocus` | Untouched, but every fixed-height rule scoped ≥1024px. | must |
| `PROPOSAL_MEAL_PLANS_PART_2` cook marker | The per-entry linked cook marker must survive the new slot shape (FU-617, designed-not-built). | must |
| `recipeTrays.ts` R-003 leak | Client re-derives staleness from `last_made_on`. | should |
| `MealPlanSkeleton` | Its `list` variant mimics the old three-column document-scroll shape — new shape, new skeleton, or it flashes the old layout on load. | should |
| `COVERAGE_GAPS.md` | The rebuild plan's 13 🟡 re-grades were never flipped (§0.1). §11 does it. | should |
| `DESIGN_REMEDIATION_PLAN.md` DR-12 | Records "rides the redesign". Needs updating to whatever D7 decides. | should |
| Long cookbooks | Virtual scroll above ~50 (F21). | should |
| Rail default state | See D3 — two house precedents disagree. | should |
| `printFocusedWeek` | Check a fixed-height ancestor doesn't clip the printed week. | should |
| `MealPlanFirstRun` | Replaces the whole layout, so fine — confirm under `:style-fn`. | should |
| `SwapSuggestionsPanel` | Below seven day cards, easy to miss. Budget-shaped; the right pane under the shopping summary is a better home. Check `PROPOSAL_BUDGET_DEFENSE_SWAPS.md` doesn't need real estate this brief reallocates. | consider |
| Reconcile nudge | Cross-week, stays above the panes — but it is chrome eating height now. Make it deliberate. | consider |
| Page title | The page has **no** title today. See D4, F40. | consider |
| `useShortcut` + cheatsheet | New collapse binding, `Esc`, possibly `ArrowLeft/Right`. | consider |
| `PageCountsFooter` | See D8 — the app-wide sticky-footer pattern this brief's status strip diverges from. | consider |

---

## 7. Standards check

| Rule | Bearing | Disposition |
|---|---|---|
| **R-036 / ADR-032** | Page height / scroll shape | Unit 1 moves Meal Plans from the document-scroll shape to the app-shell shape — both sanctioned. Update the Apply list + page header comment. **Fixes a live `100vh` violation** in `.planner-sticky`. Application, not a new ADR. |
| **R-003** | State ownership | *Dora suggests* ranks server-side by construction; filter predicates read server-derived fields; `dayStatus` keeps reading the server's shortfall set. **One existing leak fixed** (client staleness ordering). No domain constant moves clientward. |
| **R-001** | Componentisation / one implementation | New `MealPlanRecipeRow` shares `useRecipeDisplay`; `.recipe-row` chrome promoted to a shared class rather than copied a third time. |
| **R-019 / ADR-014** | No magic | Row density is an explicit prop. |
| **R-022 / ADR-018** | Shared-affordance extraction | Precedent for promoting the row chrome. |
| **D-023** | Persistent control keeps shape/place | The central tension. "System may open, never close" (§4.2) + **a named in-code carve-out comment**. Also why the drawer route is rejected. |
| **D-010** | Motion tokens or nothing | One-shot open feedback via `useMicroFeedback()`. **Fixes an existing violation** (week carousel literals). |
| **D-016 / A6** | All interactive states | Chips, rail rows and calendar cells carry the full set. Rail row becomes focusable. |
| **D-004 / A8** | 44px tap targets | Desktop rail may go dense (desktop-only chrome allows 32–36px); the mobile sheet stays ≥44px. |
| **D-011** | No horizontal page scroll | Chip row wraps; toolbar wraps rather than overflows (FU-738). |
| **D-020** | Indicator token for brand-as-indicator | Active filter chip reads the indicator token. Rule names filter chips explicitly. |
| **D-003 / D-017** | Type scale, no off-scale literals | FU-693 decision (§4.5). New code on tokens. |
| **B2 / B2a / D-013** | Chips, segmented, decodable state | New chip-row component because neither shared control fits; disabled-not-hidden; pips get tooltip + legend. |
| **B4** | Whole card is one target | Rail row is one target with `.stop`'d inner controls — tolerated, but must gain a focus state. |
| **D-001 / A1** | Colour semantics | **F41 is the live risk** — count simultaneous accent surfaces before closing (§2.5). |
| **§7.5 posture** | Data access / config | The new endpoint is repository-routed like its neighbours; no tenancy assumptions; no new config; nothing self-host-only. |

**ADR evaluation.** Two candidates, neither added unilaterally:

1. **Candidate D-024** — *a system-driven disclosure may open, never close.*
   Generalises §4.2 beyond the planner (it would also govern `FilterBar`, the
   Dora chat panel, any future rail). A genuine recurring decision, but promoting
   it is an owner call, not a brief's side-effect.
2. **No new R-rule for the shell.** Unit 1 applies R-036 / ADR-032. Resist.

---

## 8. Test and verify plan

Per the standing **lean, manual-first** stance (`DORA_VERIFY_TRIAGE.md` top
banner, owner 2026-07-20): do **not** convert these into automated tests
wholesale. Drive the running app once and delete the line. **No feature-flow
Playwright specs.**

**Automated — only where it pins a stable, low-churn contract:**
- **Backend (pytest).** The *Dora suggests* handler: excludes already-planned
  recipes for the focused week; returns at most `count`; every `reason_chip` is
  in the frozen vocabulary; an empty cookbook returns `[]`. Reuse the existing
  pure-ranker fixtures — do not build a parallel harness.
- **Frontend (vitest).** The filter predicates: each chip's set, and that a
  recipe which is both a favourite and a regular appears under **both**. That
  last one is the test that stops a future session "restoring" FU-578 #47.
- **Nothing else.** Layout, motion, hover and focus are manual.

**Manual — `DORA_VERIFY.md` under *Meal plans*, terse, delete-on-pass:**
- Rail collapsed by default; opens on click; opens on slot-click with exactly one
  settle; **never closes itself** after an add.
- Target banner + filled slot + `→ Dinner` row label name the same slot; clicking
  another slot swaps cleanly; `Esc` cancels.
- With `prefers-reduced-motion` on, the armed state is still obvious.
- **F41 check:** on a populated week with a target set and a filter active, count
  the simultaneous accent surfaces and judge whether the page got busier.
- Three panes scroll independently; the document does not scroll; no horizontal
  scroll from 1024px up; `OfflineBanner` visible does not push content off-screen.
- Toolbar holds at 1280px with `batchEnabled` and a full week.
- Calendar: click a day → week focuses **and** the pane scrolls to that day;
  hover names the meals; keyboard arrows walk the grid; today and focus are
  visually distinct.
- Mobile (375px) unchanged, and the sheet has the same chips.
- The batch pool stepper and "log a cook" still work from the new row (**F42**).

**Note on tooling:** the Browser pane cannot verify this surface — it never
advances a CSS transition, so no routed page renders in it, and
`DESIGN_REMEDIATION_PLAN.md` DR-15's verify note already records that *"the
shopping-list detail and the planner rail don't render in the verify pane"*. Use
Playwright from `web_app/`, against the scratch backend pairing (**not** the
`:5170` dev DB — FU-758).

---

## 9. Open decisions — CLOSED 2026-08-29

All eight were put to the owner in one pass and answered; **FU-782 is resolved**
and the build gate is cleared. Each decision below keeps its original
recommendation for the record, followed by the **owner's answer**. Six were
taken as recommended; **D3 and D4 were answered differently** and the builder
must follow the answer, not the recommendation.

**D1 — Does drag-and-drop survive?** *(reverses F9)*
Nested scrollers plus no auto-scroll means drag silently stops working below the
fold (§3.5). Building edge auto-scroll is a new composable and real cross-browser
testing. **F9** asked for both drag and tap, *"let the user pick how to use the
app"* — but F47/F48 were solved by the servings stepper, not by drag, and drag
has always been mouse-only.
→ **Recommend: retire it.** If retired, the grip glyph goes, and `dragAllowed` /
`draggingRecipeId` / `onDragStart` / `onDragEnd` / `onDropOnSlot` /
`onRecipePointerDown` come out of `useMealPlanner`.

**ANSWERED 2026-08-29 — retire it.** F9 is revised: tap-to-target is the single
way to place a recipe. The grip glyph and all six handlers come out.

**D2 — Collapsed rail: a 46px labelled strip, or gone entirely?**
A strip keeps the control in place (the D-023-friendly reading) and costs ~46px.
Nothing-plus-a-floating-tab gives the week everything but sits closer to the
shape-shifting D-023 forbids.
→ **Recommend: the 46px strip** with a vertical `Recipes · N` label. Cheap
insurance, and it gives the auto-open animation something to grow *from*.

**ANSWERED 2026-08-29 — the 46px labelled strip.** D-023 holds: the control
keeps its shape and its place across both states.

**D3 — Does the rail remember being open, or re-derive it per visit?**
`useListViewMode` persists to localStorage (device-shaped choice);
`useFilterPanelExpanded` deliberately **stopped** persisting in favour of *"the
panel is open when there is something in it"* — an owner call of 2026-08-20
annotated *"adopt elsewhere"*. **L213** also asks whether filters should default
open on desktop and closed on mobile.
→ **Recommend: derive it.** Open when a slot is targeted or the focused week is
empty; collapsed otherwise.

**ANSWERED 2026-08-29 — derive it, but narrower than recommended.** The rail is
**always collapsed on arrival**. It opens on exactly two events: a meal slot is
selected, or the collapsed strip itself is clicked/tapped. **The empty-week
auto-open is dropped** — do not open the rail because the week has no entries.
Nothing persists to localStorage. This is `useFilterPanelExpanded`'s
derive-don't-remember posture with a smaller trigger set; the builder must not
reintroduce the empty-week condition from the recommendation above.

**D4 — Is the week range the page title, or does "Meal plans" sit above it?**
The page has no title today. **F40** says the *"Week of…"* prefix isn't needed.
Height is now constrained.
→ **Recommend: the week range is the title.**

**ANSWERED 2026-08-29 — no page title, and no promotion.** The page keeps
exactly what it has today: the week date range sitting **between the prev/next
buttons**. It is not restyled into a page title, and "Meal plans" is not added
above it. F40 stands as written; the recommendation to promote the range to
title role is **not** taken.

**D5 — One work unit or three?**
→ **Recommend: three**, in the §1 order. Layout is the risky one; shipping it
alone makes it judgeable before the rest lands on top.

**ANSWERED 2026-08-29 — three units**, in §1 order, each with its own
close-gate and browser pass.

**D6 — Does *Dora suggests* keep the `cookable_now` reason?** *(tension with F43)*
**F43**: *"Do I need to know if something is cookable now on this page? This is
the planner, not the cookbook."* The reason line is milder than the green-check
treatment F43 objected to, and it is a *justification for a suggestion* rather
than ambient status — but it is the same fact on the same page.
→ **Recommend: keep it, reworded away from cookability language** — e.g.
*"Nothing to buy for this"*, which is the planner-relevant consequence rather
than a cookbook status. If the owner disagrees, the token is simply mapped to no
line and the server needs no change.

**ANSWERED 2026-08-29 — keep it, reworded.** F43 is revised, and the owner's
reasoning narrows the scope of that revision: *"do you have all the ingredients
for this already?"* is a legitimate input **to a suggestion**, and the value of
*Dora suggests* comes from having **several** indicators rather than one — a
single-reason suggestion isn't worth looking at. So the reason chip stays as
one member of the frozen reason vocabulary, worded as the planner-relevant
consequence (*"Nothing to buy for this"*), **not** as ambient cookable-now
status on the page at large. F43's original objection — the green-check
treatment applied to every row — remains in force everywhere outside the
suggestion chip.

**D7 — Month grid, or keep the F13 widget / take DR-12's 14-day strip?**
Three live options, and the current design is the owner's own June spec (§2.5a).
DR-12 independently directs a *"labelled 14-day strip (counts on cells)"* and is
recorded as waiting on this doc.
→ **Recommend: the month grid**, on the grounds that days already look clickable
and should be, and that DR-12's rationale (a calendar competing with an
actionable list) does not apply here. **This overrules a standing remediation
directive and revises F13 — it must be confirmed, and DR-12 updated to match.**

**ANSWERED 2026-08-29 — the month grid.** F13 is revised and **DR-12 is
overruled**; its 14-day-strip directive is superseded by this decision, and
`DESIGN_REMEDIATION_PLAN.md` must be updated to say so when Unit 3 ships (it
currently records DR-12 as *"rides the redesign"* — this is that redesign).

**D8 — Status strip at the top, or a sticky footer like every other page?**
The owner has asked three times, app-wide, for page counts as a **componentised
sticky footer** (L93, L212, L231), and `PageCountsFooter.vue` exists. Toolbar
row 2 diverges from that. Counter-argument: this is a *status* strip, not a count
of listed records, and **F45** wants the shortfall to have exactly one home near
the week nav. Also relevant: **F17** asked for the next-week arrow *below* the
working area, which a footer could carry.
→ **Recommend: keep it in the toolbar**, and note the divergence in the worklog
rather than pretending it is consistent. If the owner prefers the footer,
`PageCountsFooter` should be reused rather than a fourth variant invented.

**ANSWERED 2026-08-29 — keep it in the toolbar.** This is a *status* strip, not
a count of listed records, and F45 wants the shortfall to have one home near the
week nav. The divergence from L93/L212/L231 is **deliberate and must be recorded
in the worklog** when Unit 1 ships — not presented as consistency.

**Open decisions — closed.** All eight answered by the owner on 2026-08-29 in a
single pass; **FU-782 resolved** and moved to `DORA_FOLLOWUPS_RESOLVED.md`. Six
taken as recommended (D1, D2, D5, D6, D7, D8); **D3 and D4 answered against the
recommendation** — see their inline answers, which are what the builder follows.
No item in this section remains undecided.

---

## 10. Handoff notes for the builder

- **Read `IMPL_PLAN_MEAL_PLANS_REBUILD.md` §4–§8 and this doc's §0 first.** You
  are narrowing a predecessor, not starting fresh.
- **Read `StockOverview.vue`**, not this document's CSS snippets. It is the
  canonical shell and its comments record the bug the pattern replaced.
- **Do not** introduce `q-scroll-area` — one non-canonical use in the whole app
  (`DoraChat.vue`).
- **Do not** hardcode 64px or `calc(100dvh - Npx)`. R-036 names it as the
  violation signal.
- **Do not** auto-close the rail (§4.2). Leave the carve-out comment.
- **Do not** add a repeating pulse (§4.7).
- **Do not** expose the four emphases in the rail (§4.4).
- **Do not** make the week columnar (§3.7).
- **Do not** let the rail's search creep toward a command palette — that feature
  is cut, and the original spec's `S1 — Global command palette` is a landmine
  sitting right next to this surface.
- **Do not** let the rail's stock affordance grow substitute suggestions — the
  substitute *graph page* is cut, and the original spec's next card after
  "highlight out-of-stock" is exactly that.
- `useMealPlanner.ts` is the page's shared core and already exports
  `prefersReducedMotion`, `weekTransition`, `slideDir`, `focusedTarget`,
  `isTargeted`, `selectSlot`, `clearFocusedTarget`. Extend it rather than adding
  page-local state.

---

## 11. Cross-check against the original feedback

Every `§MEAL PLANS` bullet (F1–F49, the scheme minted by
`PROPOSAL_MEAL_PLANS.md` §13), plus the strays this surface is graded against.
Bullets this brief does not touch are marked out-of-scope with a reason — they
remain owned by `PROPOSAL_MEAL_PLANS.md`.

| # | Feedback | Covered |
|---|---|---|
| F1 | Sequential builder (pick → stock → list → print) | Out of scope — the builder's flow is untouched; only its picker changes (§4.8) |
| F2 | Templates, rotating, auto-add tie-in | §3.2 — templates move to the `⋮` menu; the drawer itself is unchanged |
| F3 | Page icon (meals, not calendar) | Out of scope — shipped |
| F4 | Chef's hat, not a warning symbol | Out of scope — shipped; the icon rides into §3.2's status strip unchanged |
| F5 | Allocation broken | Out of scope — shipped |
| F6 | Toast subtitle bug | Out of scope — shipped |
| F7 | Full-ingredient-demand colouring consistency | §3.3 — unchanged, now scrolls inside the right pane |
| F8 | Disable drag on mobile | §3.5 — already true (`pointerType !== 'mouse'`); unaffected by D1 |
| F9 | Offer both drag and tap; let the user pick | **§2.5(c) + D1** — the recommendation reverses this bullet |
| F10 | Plan name useless | Out of scope — shipped |
| F11 | Date picker wrong for new plans; pick from upcoming weeks | §5 — the month grid *is* the week picker; per-day pips replace greying |
| F12 | Template management | §3.2 — `⋮` → Browse + apply templates |
| F13 | Custom minimalist calendar widget (DD-only, underlines, month banner) | **§2.5(a) + §5 + D7** — this brief revises it |
| F14 | Widget on the right, above shopping info | §3.3 — honoured verbatim; now pinned |
| F15 | Current day marked | §5 — filled accent disc |
| F16 | Scrollable carousel revealing prev/next week + smooth animation | §3.1 — superseded by the pane scroll; the animation survives on tokens (§4.7) |
| F17 | Up arrow above, down arrow below; calendar changes with it | **§3.2 + D8** — the arrow-below half is reversed; the calendar-sync half is honoured (§5) |
| F18 | Favourites + haven't-had-in-a-while trays, draggable | §4.3 — the trays become chips; the metrics are unchanged |
| F19 | Reusable on the recipe overview, on a different metric | §4.5 — `useRecipeDisplay` + a promoted shared row chrome |
| F20 | Main working area more centred? | §3.1 + §4.2 — collapsing the rail widens it; three panes replace centre-weighting |
| F21 | "All recipes" inadequate; must be filterable, vertical, hundreds-capable | §4.3 (chips) + §4.5 (virtual scroll) — the brief's core answer |
| F22 | A way to add without drag and drop | §4.6 — target-then-pick becomes the primary path |
| F23 | Dorabot assists with meal planning | Out of scope — §4.4 is a ranked list, not an assistant turn; F23 stays open |
| F24 | Recurring plans | §3.2 — reachable via the `⋮` templates drawer; behaviour unchanged |
| F25 | How recurring and editing coexist | Out of scope — domain question, owned by the master proposal |
| F26 | Must work for batch cooks and fresh cooks alike | §4.5 — the pool stepper and log-a-cook survive the redesign |
| F27 | Meal cards don't fit / text overflows | §3.7 — the full-width card + slot-row shape that fixed this is preserved as a constraint |
| F28 | Refresh jumps to the earliest plan | Out of scope — `focusedMonday` init is untouched |
| F29 | Droppable past day threw an exception | §3.5 + §4.6 — `selectSlot`'s past-day guard is the surviving path under D1 |
| F30 | Hovering stock items reveals their meals | §3.3 — `hoverIngredient` preserved |
| F31 | Shopping-list status per stock item | §3.3 — unchanged |
| F32 | Add items individually or all at once | §3.3 — unchanged |
| F33 | What does "generate shopping list" do? | Out of scope — resolved 2026-08-27 by the shared `AddToListDialog` |
| F34 | Does "needs x" work? | Out of scope — shipped |
| F35 | Added meals always land in "Dinner" | Out of scope — shipped; §4.6 makes the chosen slot explicit, which reinforces it |
| F36 | An "edit entries" button proves a gap in the working area | §4.6 — targeting closes the gap |
| F37 | "Delete plan" → "Clear week" | §3.2 — keeps its label and danger colour inside the `⋮` menu |
| F38 | Some elements not theme-aware | §5 — all new components read tokens only |
| F39 | Drop the CSV export | Out of scope — removed |
| F40 | Don't need the "Week of…" title | §3.2 + D4 — the range is the label |
| F41 | Conflicting colour and iconography across the page | **§2.5 (standing risk) + §8** — this brief adds accent surfaces and must be measured against it before closing |
| F42 | Meals-on-hand is hidden in the chip; make the number bigger | §4.5 — a known-open complaint the new row must answer, not just preserve (see also FU-088) |
| F43 | Cookable-now doesn't belong on the planner | **§2.5(d) + D6** |
| F44 | Don't squish the working area; maybe combine recipes into the right column | §3.1, §3.7, D2 — the collapse achieves the width goal without stacking two jobs in one column |
| F45 | Shortfall banner shows information twice | §3.2 — the status strip is its single home |
| F46 | Time of day as rows, not on the cards | §3.7 — implemented; preserved as an explicit constraint |
| F47 | A repeat drop should increment the count | Out of scope — solved by the servings stepper; relevant to D1 as evidence drag's unique value is small |
| F48 | Shouldn't drag one by one to raise a count | Out of scope — same |
| F49 | Slots configurable with defaults | Out of scope — shipped; `slotNames` drives §3.7 |

**Strays this surface is graded against**

| Bullet | Feedback | Covered |
|---|---|---|
| L271 | A "planned in" recipe filter | §4.3 — logged as a candidate sixth chip, **not** proposed; had no home in any coverage table before now |
| L93 / L212 / L231 | Counts as a componentised sticky footer, app-wide | **D8** — this brief diverges and says so |
| L102 | One standard toolbar and toolbar button, app-wide | §3.2 |
| L99 / L100 | Search kept separate from other filters; filter control reflects filter state | §4.3 — search sits above the chips; the collapsed strip carries an active-filter dot |
| L213 | Should filters default open on desktop, closed on mobile? | D3 |
| L61 | Unified "this fortnight" dashboard calendar | §5 — build the grid with that seam; using it is out of scope (owned by the dashboard rebuild) |
| L89, L254, L272, L274, L275, L442, L38 | Planner-adjacent metrics, costs, alerts, demo data | Out of scope — owned by `PROPOSAL_MEAL_PLANS.md`, the dashboard rebuild, `PROPOSAL_ALERTS.md`, and onboarding respectively |

**Nothing newly stranded.** Every `§MEAL PLANS` bullet is either covered above,
already shipped under the master proposal, or explicitly out of scope with a
reason. `COVERAGE_GAPS.md` needs two edits, recorded in §6: flip the rebuild
plan's 13 🟡 re-grades (its §15 instructed this in June and it never happened),
and give **L271** a home.

---

## 12. From the original spec

`docs/00_original_spec/` is the author's first spec, pre-dating ~100k LOC.
**Historical and non-authoritative** — the charter, reconciled plan and current
feedback override it. Two findings are load-bearing and one negative finding
matters more than either.

### The negative finding, first

**There is no original intent for a month grid, a date picker, or any calendar
widget at all.** The entire vault contains one calendar-shaped line —
`💡 Unprocessed Ideas.md:101`, *"Check outlook calendar views for ideas"* — plus
`PROMPT_PLAN.md:172`'s *"weekly calendar grid"*, which describes the week view,
not the picker. The right-rail calendar is net-new invention with **no prior
intent to honour and no spec cover**. That cuts both ways for **D7**: nothing in
the original constrains the month grid, and nothing endorses it either. The only
authority on that widget is **F13**, which is why §2.5(a) matters so much.
Templates and the four-emphasis auto-build wizard are likewise entirely
net-new — the vault has nothing on either.

### keep — dropped intent worth reconsidering

**Availability as the rail's organising axis.** `💡 Unprocessed Ideas.md:85-92`:
*"Left pane has searchable/filterable list of meals in the system · Meals are
greyed out if they have zero available servings · … Each meal on the left pane
has a set of +/- buttons to increase or decrease the number of available
servings."* Today's rail groups by **history** (favourite / stale / frequent);
the original grouped by **what you can actually make**. The `+/-` buttons *did*
ship — they are the batch pool stepper in §4.5 — but the greying-out did not, and
the availability axis never became a grouping. Related:
`Feature Boards/Recipes.md:27` (*"recipes are greyed out when at least one of
their ingredients are out of stock"*), `:53` (*"the number of in stock, low stock
and out of stock ingredients"*).
**Tagged keep, but held:** this is the most obviously missing signal for a picker
whose job is choosing what to cook — and it collides directly with **F43** and
**D6**, which say stock-readiness does not belong on this page. Resolve D6 first;
if D6 keeps a stock-flavoured reason, this becomes the natural follow-up. Do not
build it in this brief.

**Deficit framing for the week's shopping.** `PROMPT_PLAN.md:172-175`: *"Sidebar
rolls up the week's combined ingredient demand vs current stock and shows
'You'll need to buy: X'."* The shipped summary now does exactly this (and better
— it subtracts what's already on a list). **Superseded**, recorded because the
phrasing confirms §3.3's judgement that the right pane's job is the *deficit*,
not a requirements list.

### consider — a cleaner original framing, deliberately not taken

**The planner as a toggleable panel over the recipe book.**
`💡 Unprocessed Ideas.md:104-107`: *"Don't lock people into using the planner in
a certain way, what if people just want a simple list view where they can track
the number of meals they have in stock? … could make the meal planner pop up in
a split view on the right side by clicking a button in the toolbar (show
planner), movable by dragging the splitter bar … This way it can be used, or not
at all."*

This inverts the whole page: the cookbook is the surface and the planner is the
panel, rather than the reverse. It is a real product position — *don't force the
calendar on someone who only wants to track meals* — and the current page-first
model appears to have been chosen without an explicit decision against it.
**Not taken**, for three reasons worth recording: the planner is a top-level nav
destination in the original's own navigation map
(`🧭 Navigation.excalidraw.md:1091`); `PROPOSAL_MEAL_PLANS.md` built and shipped
the page-first model against F1–F49; and the owner's 2026-08-28 brief explicitly
says *"we keep the rail"*, which presumes the page. Flagged so it is a decision
on the record rather than an omission.

**Toolbar outside the scroll container.** `Working Notes for UI.md:5`: *"The
toolbar at the top should probably always be visible? So it should be outside the
splitter container."* And `:31-32`: *"Splitter approach — 'to top' button doesn't
work, header reveal doesn't work / Drawer approach — it all works."* This is the
author reasoning about **exactly** §3.1's problem, two years of code earlier, and
landing on §3.2's answer. Quasar-implementation-era reasoning, possibly stale —
but the transferable rule (*chrome lives outside the scroller*) is what Unit 1
does, and the second transferable concern is a warning: `:13`, *"A concern I have
is if it will feel jarring to have the layout change when you click on a stock
item."* That is precisely the auto-open reflow risk §3.7 guards against.
**Tagged consider → already honoured.**

**Quantity on drop, and slot glyphs.** `💡 Unprocessed Ideas.md:95-100`: *"When
dropping a meal, it prompts you for 'how many to allocate?' … Likely can display
this as: # / # e.g. 4/6."* The prompt-on-drop is **superseded** (the servings
stepper answered F47/F48 better, without a modal per placement). The `4/6` slot
glyph — allocated vs available at a glance — is a compact idea that never
shipped. Out of scope here (§1 excludes day-card internals); worth a follow-up
if the batch audience's needs come up again.

**"Cookable now" as a one-tap suggestion.** `PROMPT_PLAN.md:176-177` (*"'Suggest
meals I can cook now' button"*) and `:206-207` (*"'Cookable tonight' (top 3
recipes)"*). This is a **single-slot, in-the-moment, stock-driven** suggestion,
distinct from the whole-week wizard — and it is arguably the more frequent need.
The *Dora suggests* chip (§4.4) is the closest thing to it that this brief
proposes, which is another reason D6 matters.

### superseded

- `Feature Boards/Meals.md:12` — *"a meal plan for a duration of time (maybe
  locked to a week)"*. The week view resolves the author's open "maybe".
- `Feature Boards/Recipes.md:29-32` — last-made-on, sort-by-last-made, favourites
  filter. The trays deliver the intent more directly; §4.3's chips deliver it
  *as* filters, which is closer to the original ask than the trays were.
- `Feature Notes/Automated meal plans.md:4-7` — nutrition-driven, per-person auto
  plans. Largely superseded by "Build my week"; the two axes it actually wanted
  (daily-intake targets, per-person plans) depend on `X6 — Nutrition tracking`
  and `A2 — Household / multi-user sharing`, both deferred. Know why it isn't
  there rather than treating it as a gap.
- `Feature Notes/Drag and drop to reorder.md` — scoped to reordering the recipe
  overview, not planner placement. Its whole body reads *"description: May not be
  necessary with filtering"*, which is mild corroboration for **D1**.

### Cut-feature landmines adjacent to this surface

Three of the project's removed features sit uncomfortably close, and the original
spec cheerfully proposes all of them. Repeated in §10 as build-time warnings:

1. **Command palette** (`PROMPT_PLAN.md:1064-1067`, `S1 — Global command
   palette`, Ctrl/Cmd-K). The rail's search box is the natural place to creep
   toward one. Keep it scoped to filtering the list.
2. **Substitute graph page** (`Feature Boards/Recipes.md:42`, `:52`). If the rail
   ever gains the out-of-stock affordance in the *keep* section above, the spec's
   very next card is offering substitutes. Per-stock-item substitutes are fine;
   the graph page is cut.
3. **Stock map / spatial layout** (`💡 Unprocessed Ideas.md:72-78`). The vault's
   *other* big drag-and-drop feature — so if D1 is ever argued from the spec's
   DnD precedent, cite `💡 Unprocessed Ideas.md:94`, not the map prompts.

Also noted: the shopping rollup at `PROMPT_PLAN.md:172-175` is deliberately
stock-vs-demand only. Don't let §3.3's summary acquire price or deal columns —
that direction leads to central retailer scraping, which is cut.
