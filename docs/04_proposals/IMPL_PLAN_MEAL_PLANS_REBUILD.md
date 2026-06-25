# Meal Plans Rebuild — Design Critique + Implementation Plan

**Status:** 📋 Critique + rebuild brief (v2, polished + principle-grounded) —
ready for the remaining decisions, then phased execution.
**Raised:** 2026-06-25 (a `/design-critique` pass on `MealPlansOverview.vue` + the
live app, mirroring the Settings and Dashboard rebuild flows). Revised the same
day across three review rounds; v2 reorders for a clean read and grounds findings
in named UX/accessibility standards (§3).
**Owns:** `web_app/src/pages/MealPlansOverview.vue` (→ decomposed into a new
`web_app/src/components/meal-plans/` directory + a `useMealPlanner()` composable),
`web_app/src/components/MealPlanCalendar.vue`,
`web_app/src/components/MealPlanEntryChip.vue`,
`web_app/src/components/SequentialBuilderDialog.vue`,
`web_app/src/pages/MealPlanTemplatesPage.vue`, and a **new** Direction-B page.

**Relationship to prior docs:** a **fresh re-evaluation of the shipped C-2
result**, not a re-spec. `PROPOSAL_MEAL_PLANS.md` + `IMPL_PLAN_MEAL_PLANS.md`
(both 2026-06-14) defined what was built; every F1–F49 bullet shipped. This brief
asks: *now that all 49 ideas are live together, how does the surface hold up?*
§13 re-grades each bullet.

**Cross-references:**
- `docs/01_charter/ENGINEERING_STANDARDS.md` — R-001 (componentisation), R-002
  (theme tokens), R-003 (state-ownership), R-007 (scope), R-008 (comment-or-flag),
  R-011 (framework-idiomatic Quasar/Vue), R-014 (empty states), R-016 (lazy
  hydration).
- `docs/01_charter/DASHY_DORA_CHAMPION_PLAN.md` Part II — Charter principles;
  tiebreak **P10 Effortless + Anti-creep**, **P11 Fast**.
- `docs/04_proposals/IMPL_PLAN_DASHBOARD_REBUILD.md` /
  `IMPL_PLAN_SETTINGS_REBUILD.md` — the established rebuild pattern (diagnosis →
  IA → layout → phased, each phase shippable).
- `docs/04_proposals/STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` — derived facts stay
  server-side (R-003); see §10.
- `docs/02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md` §MEAL PLANS — the
  source of truth re-checked in §13.
- Open follow-up **FU-179** (browser-verify the surface) — partly discharged here;
  **FU-304** tracks this rebuild.

### Document map

§1 diagnosis · §2 current state · **§3 design principles applied (the grounding
lens)** · §4 design critique · §5 structural diagnosis · §6 best-possible UX ·
§7 UI craft bar · §8 resolved direction (build A + B) · §9 deeper analysis ·
§10 engineering-standards · §11 open decisions · §12 phased plan ·
§13 feedback coverage (F1–F49) · §14 references · §15 next step.

---

## 1. Read this first — the diagnosis

The current planner has **good craft and faithful execution** — it built every
idea the feedback asked for. The problem is **not any single feature; it is
emergent**: individually reasonable ideas, rendered unconditionally, combine into
a page that is mostly **empty space and "tap to add" labels**, where the
answer-bearing content (what to cook, what to buy) scrolls away first.

> **In one line:** the planner shows a **35-cell grid to fill** when the user came
> to fill three. Every lever (carousel + all-slots-always + non-sticky columns +
> centre-weighted grid) trades density for sprawl — so the page reads as *work to
> do*, not *a plan at a glance*. This is, precisely, a violation of Nielsen
> heuristic #8 (aesthetic & minimalist design) and Hick's Law (§3).

Order of operations: **(1)** kill the empty-cell sprawl → **(2)** fix the
two-surface story (desktop context, mobile add) → **(3)** decompose the
1,222-line file (R-001) → **(4)** polish (hierarchy, colour, a11y). Each step is
independently shippable; do **not** roll them into one PR.

---

## 2. Current state (source of truth)

**Page:** `MealPlansOverview.vue` — **1,222 lines**; template + script + scoped
SCSS in one file (**R-001 violation**, as the dashboard was).

**Desktop layout** — a 3-column `row q-col-gutter-md`:
- **Left `col-md-3`** — recipe palette: search + `q-expansion-item` trays
  (Favourites / Haven't had in a while / Frequently planned / All recipes). Each
  row = name + `n free` caption + `− [pool] +` + a "log cook" fork. Internally
  scrolls (`.recipe-list { max-height:65vh; overflow-y:auto }`).
- **Middle `col-md-6`** — vertical week carousel: week-range header (`↑ 22/06 –
  28/06`, print + clear-week icons), one `q-card` per day rendering **every**
  configured slot row (Breakfast/Lunch/Dinner/Snack/Dessert), then a down-arrow.
  Week changes via ↑/↓ buttons, ArrowUp/Down keys, or vertical swipe.
- **Right `col-md-3`** — `MealPlanCalendar`, then "This week's shopping" (count +
  cook-by line + per-item buy rows + Generate button), "Full ingredient demand"
  expansion, and a "Templates" card (save / apply / recurring / manage).

**Mobile (`col-12`):** the three columns stack in **DOM order** → palette first,
week second, sidebar last.

**Two add models:** drag-to-add (`dragAllowed = e.pointerType === 'mouse'`,
L607 — *mouse only*) and tap-slot-then-pick-recipe (L585–602), the latter
discovered only via a toast.

**Client-side derivations** (R-003, see §10): `cookByLabel` (L534–540), `trays`
(L555–578), `needToBuy` (L748–750), calendar `dayStatus`
(`MealPlanCalendar.vue` L71–79).

**Confirmed:** no `position: sticky` anywhere — side columns are normal flow and
scroll away (screenshot 1: day cards floating in a void once the rails leave).

---

## 3. Design principles applied (the grounding lens)

Every finding below maps to an established, citable standard. This section is the
spine; the critique (§4) and recommendations (§6–§7) reference these by id.

| Principle | Source | How it applies here |
|---|---|---|
| **H8 — Aesthetic & minimalist design** | NN/g 10 Heuristics (Nielsen 1994/2020) | The 32 empty "tap to add" rows are noise competing with the plan. Every extra unit of UI steals attention from the relevant. → de-sprawl (U1). |
| **H1 — Visibility of system status** | NN/g | "What to cook / buy" is the system's most important status; it must be always-visible, not in the first column to scroll away. → sticky consequences bar (U2). |
| **H2 — Match system & real world** | NN/g | People think "what's for dinner," not "fill slot grids." → slot-as-tag + dinner-first (§6.2). |
| **H5 — Error prevention** | NN/g | Destructive "clear week" sits at icon size beside "print." → labelled, in an overflow menu, behind confirm (U7). |
| **H6 — Recognition rather than recall** | NN/g | Drag is invisible until tried; tap-add is taught by a *post-error* toast. Affordances must be seen, not remembered. → explicit `+` targets, visible picker (U5). |
| **H7 — Flexibility & efficiency** | NN/g | Power users want drag + a builder; novices want tap. Offer both; make drag the accelerator, not the requirement (U5, §6.3). |
| **H4 — Consistency & standards** | NN/g | One stock-status colour mapping; one accent; reused components. → token + component discipline (§7, §10). |
| **Hick's Law** | Laws of UX (Yablonski) | Decision time grows with the number/complexity of choices. 35 cells, 3 template entry points, 5 always-on slots → reduce/segment (U1, §9-E). |
| **Fitts's Law** | Laws of UX | Target acquisition time ∝ distance / size. Tiny clustered ± buttons + destructive-next-to-benign + long carousel drag distances all fail it. → ≥24–44px targets, grid shortens drag (U7, §9-H, a11y). |
| **Jakob's Law** | Laws of UX | Users expect this to behave like calendars/planners they know (Google/Apple Calendar week grid; Mealime/Paprika meal cards; mobile bottom-sheet + FAB). → adopt conventions, don't invent (§6). |
| **Tesler's Law (conservation of complexity)** | Laws of UX | Batch-cooking complexity can't be deleted, only relocated. → an opt-in batch posture, default-hidden, not removed (§6.6). |
| **Progressive disclosure** | NN/g | Show the common case; reveal the rest on demand. → used slots + "show all slots"; "group by slot"; batch layer (U1, §6.2/6.6). |
| **Von Restorff (isolation) effect** | Laws of UX | The item that differs is remembered. One accent colour + a clearly anchored "Today" beat many competing colours (§7). |
| **Aesthetic–Usability effect** | NN/g | Polished UIs are *perceived* as more usable and forgiven more readily — the explicit ask for "professional" (§7). |
| **Doherty threshold (<400 ms)** | Laws of UX | Keep interactions feeling instant → optimistic add + skeleton screens (§7, §9-I). |
| **Empty-state / "blank slate" design** | NN/g | First-run should teach one next step, not present four empty regions. → designed first-run (§6.7, §9-A). |
| **WCAG 2.2 AA** | W3C | 1.4.3 contrast (the muted "tap to add"); 1.4.1 use-of-colour (status by icon/border + text, not hue alone); 2.1.1 keyboard (drag needs a non-drag path); 2.5.8 target size ≥24px (the ± cluster, icon actions); 4.1.2 name/role/value (clickable `<div>`s → buttons; grid cells need `aria-label`). |
| **Gestalt: proximity / common region** | Interaction-design canon | Meals read as "belonging to" a day when grouped in a bounded region under it → card-stack-under-day (§6.4). |

---

## 4. Design critique

### 4.1 Overall impression

Visually competent and clearly loved — warm brand, coherent dark theme, a genuinely
clever minimalist calendar widget, a real attempt at dual add-affordances. But the
**eye lands first on a column of empty "tap to add" rows**, and the **most valuable
content sits in the column that disappears first**. It communicates *chores*, not
*a plan*. (H8, H1.)

### 4.2 First impression (2 seconds)

- **What draws the eye:** repeated italic "tap to add" hints and empty slot labels
  — i.e. *absence*. On a 1080p desktop the viewport often shows **one day's five
  slots** with empty columns either side. Signal-to-noise is inverted. (H8.)
- **Emotional read:** "there's a lot to fill in." Discouraging for the fresh-cook
  persona — the layout assumes you'll populate 35 cells (undercuts F26). (H2,
  Tesler.)
- **Purpose clarity:** partial. The *primary action* ("add a meal") has no
  obvious, always-visible entry point. (H6.)

### 4.3 Usability findings

Severity: 🔴 critical · 🟡 moderate · 🟢 minor. Principle ids per §3.

| # | Finding (principle) | Sev | Recommendation |
|---|---|---|---|
| U1 | **Empty-slot sprawl.** 5 slots × 7 days = 35 rows, ~32 empty; a week is 3+ screens. *(H8, Hick, progressive disclosure)* | 🔴 | Render only **used** slots + one quiet `+ add a meal` per day; "show all slots" opt-in. Root fix in §6.2 (slot-as-tag). |
| U2 | **Non-sticky context columns.** Scrolling the week scrolls the palette *and* the shopping rail off-screen — the drag source and the impact readout vanish mid-task. *(H1, Gestalt)* | 🔴 | Sticky side columns on desktop; promote consequences to an always-visible bar (§6.4). |
| U3 | **Mobile scroll-pogo.** DOM order palette→week→sidebar; tap-add needs the palette *after* picking a cell → scroll down, tap, scroll back up, tap. *(H6, Fitts, Jakob)* | 🔴 | Bottom-sheet picker from the cell `+` (the platform convention); week is the top surface on mobile. |
| U4 | **Wasted desktop width.** The centre `col-md-6` pins content to ~50%; scrolled, both sides are void. Old fear was "squishing" (F44); the build overcorrected into *unused* width. *(H8, Jakob)* | 🟡 | A compact 7-day grid uses the width (Direction B, §8). |
| U5 | **Two add models, both low-discoverability.** Drag invisible + mouse-only; tap-add taught by a post-error toast. *(H6, H7)* | 🟡 | Explicit per-cell `+`; drag as a labelled accelerator (grab cursor/handle); never teach core interaction via a toast. |
| U6 | **Dense "pool" model.** Palette fuses *browse-to-add* with *batch-inventory* (`n free`, `− [pool] +`, log-cook). "free" is jargon; two identical-looking ± do different things. *(Tesler, Miller, H4)* | 🟡 | Gate the batch layer behind a posture (§6.6); relabel "free" → "ready"; de-conflate the two ±. |
| U7 | **Destructive "clear week" at icon size beside print**, tooltip-only. *(H5, Fitts)* | 🟡 | Overflow menu + text label; keep confirm; never destructive-adjacent-to-benign at icon size. |
| U8 | **No always-visible primary CTA / page identity.** Header band near-empty (a floating "Plan step-by-step"). *(H1, H6)* | 🟢 | Compact header identity + week-status summary; host the primary add there. |

### 4.4 Visual hierarchy

The eye should land on the plan and its status; today it lands on empty rows.
Invert emphasis: **planned meals loud, day structure quiet, empty slots
near-silent** (a hairline `+`, not a full italic row). Promote the week's status
to the top of the working area (H1, Von Restorff).

### 4.5 Consistency

| Element | Issue | Fix |
|---|---|---|
| Stock-status colour | Must use the **shared `useStockStatus` mapping** (F7 history), nothing local. | Route all status colour through the composable (R-003, H4). |
| Entry chip ✓/⚠ | Green ✓ (consumed) + orange ⚠ (shortfall) + count pill + name = busy (the user's "conflicting" complaint, F41). | One status token per chip (border/dot + icon), name primary (H4, 1.4.1). |
| Componentisation | One 1,222-line file; Dashboard/Settings were decomposed. | Decompose (§10, §12). |
| Empty states | Day-level empty = 5 identical "tap to add" rows, not a designed state (R-014). | One calm per-day empty affordance (§6.7). |

### 4.6 Accessibility (WCAG 2.2 AA)

- **Keyboard (2.1.1, 4.1.2):** drag is not keyboard-operable; tap relies on
  click handlers on **`<div>` slot rows** — not focusable/announceable. → real
  buttons; grid cells get `aria-label` ("Add a meal to Thursday 25 June").
- **Target size (2.5.8 ≥24px):** the palette `− [n] +` + fork cluster and the
  carousel icon actions are tight/small. (Fitts.)
- **Contrast (1.4.3):** muted italic "tap to add" on the sunken surface is low
  contrast — *and* there are 30+ of them (also H8).
- **Use of colour (1.4.1):** status conveyed by hue (green/orange) needs an icon
  or border + text too.
- **Motion:** carousel honours `prefers-reduced-motion` (L714) — keep that.
- A full pass via `/design:accessibility-review` once structure settles.

### 4.7 What works well (keep)

- The **custom calendar widget** — minimalist, month-banner, DD-only-first-column,
  status underlines, today dot. On-brief and elegant.
- **Templates / sets / recurring** — complete, well-scoped.
- **"This week's shopping"** — the best idea here; answers a real question with
  per-item add + generate. Deserves *more* prominence (H1).
- **Refresh-resume** (URL `?monday=`), **household-timezone correctness**,
  **same-recipe-same-slot increment**, **per-entry ± servings** — quietly correct.
- **Shortfall as chef-hat** (F4).

---

## 5. Structural diagnosis (why the carousel is on the table)

The vertical carousel was the **user's own idea** (F16) and was built faithfully.
The sprawl is the *compounding* of three faithful ideas:

1. **Time-of-day as rows** (F46) → 5 slot rows/day.
2. **All slots always rendered** (an unstated default) → 35 rows/week.
3. **Vertical carousel** (F16) → that ladder becomes the entire main axis (a week
   = 3+ screens), and week-navigation rides the *same* axis you scroll to read it
   (gesture ambiguity).

Plus 3-column centre-weighting + non-sticky columns waste width and drop context
on scroll. **The carousel is salvageable** — the sprawl is mostly #2 + the
layout, not "vertical" per se. The decisive lever is #1 (see §6.2). Both
directions are now being built (§8); §6 designs the more ambitious one (B) from
first principles.

---

## 6. Best-possible UX (first principles, for the Direction-B page)

### 6.1 North star + jobs-to-be-done

> Get from "empty week" to "a plan + the shopping/cooking to make it happen," in
> as few moves as possible, staying glanceable, without overwhelming someone who
> just cooks dinner.

JTBD, in priority order — note the dominant visit is *looking*, not editing:
1. **Glance** — "what are we eating, anything wrong?" (~80% of visits)
2. **Plan** — assign meals fast, any device
3. **Act on consequences** — buy / cook, in one motion

Governing constraint: serve **batch AND fresh** cookers from one surface (F26);
tiebreak **Effortless + Anti-creep**.

### 6.2 The reframing insight — slot-as-tag, not slot-as-scaffold

The dominant case is "what's for dinner this week." Rendering 5×7 cells optimises
for the rarest user. **Root fix:** meals are **cards that stack under a day**; the
meal-type is a **tag on the card**, not a pre-printed empty row. Empty days cost
one calm `+`, not five "tap to add" lines. This is the established convention
(Plan to Eat, Paprika, Mealime, Pestle) — **Jakob's Law** in action, and it
collapses the **Hick's-Law** choice space from 35 cells to 7 days.

> ⚠️ **Divergence from F46** ("time of day as rows") — needs sign-off (Q5). F46
> was written against the old cramped layout; its *intent* (organise by time of
> day) is better served by tag-on-card + an optional **"group by slot"** view.
> Also fixes F35 (slot ≠ always Dinner). Low-risk: trial on the B page only.

### 6.3 Design-space survey (angles considered, so the choice is deliberate)

- **Layout:** vertical agenda (A) · **7-day grid (B — chosen for desktop glance,
  Jakob)** · single-day focus (chosen for mobile) · kanban (too drag-centric,
  fails touch) · meal-type-major rows (great for "just dinners," awkward when
  slots vary → the "group by slot" view) · plan-as-list (calendar-blind).
- **Add interaction:** drag = desktop accelerator only (H7) · **day-first** (tap
  cell → picker; primary on touch) · **recipe-first** (pick recipe → "add to which
  day(s)?"; missing today, and how batch cookers think) · quick-add (later) ·
  builder/Dora (keep; route through the shared picker).

### 6.4 Recommended structure (content-forward week board)

- **Top strip** — week nav (‹ range ›, Today, month popover) · Templates ▾ · Plan
  step-by-step · temp A/B toggle · "group by slot" toggle.
- **The week** — 7 day columns; each holds **0..n meal cards that stack** (no
  empty slot rows). Today anchored (Von Restorff). Empty day = one ghost
  `+ add meal` (R-014).
- **Consequences bar** (full-width, sticky) — "N planned · N to cook by DATE ·
  N to buy · [Generate list]." The payoff, always visible (H1).
- **Picker** — pinnable drawer (search + trays; click-add or drag) = the *same
  component* as the mobile bottom-sheet (H4, Jakob).

### 6.5 The meal card (where "polished" lives)

Data exists on `Recipe` (image, `cuisine_name`/`category_name`,
`cook_time_minutes`, `servings`, `difficulty`, `kcal`). The **`MealPlanEntry` DTO
carries only** `recipe_id`/name/servings/slot/consumed_at — so rich cards need
either a client join to `recipeStore` (presentation-only, acceptable) or
**enriching `MealPlanEntryDto` server-side** (cleaner; preferred — Q6). Card =
small **thumbnail** (or category-tinted monogram) · **name** · quiet
**×servings**, **slot tag**, optional **cook-time** · status as a **restrained
left-border accent** (not a saturated fill) · tap → existing menu.

### 6.6 Dual persona — a quiet posture (Tesler's Law)

- **Fresh (default):** pure scheduling. No pool / "n free" / "N to cook by."
- **Batch (opt-in, tied to the existing money/batch posture):** reveals pool /
  "ready" counts, the cook-shortfall line, log-cook. (Resolves U6, §9-C/G, Q3.)

### 6.7 Designed states (empty-state best practice)

- **First-run (no recipes):** one hero → "Add recipes to start planning →
  Cookbook" (not four empty regions; §9-A).
- **Recipes, empty week:** one CTA → "Plan this week" (builder) or tap `+`.
- **Loading:** grid-shaped skeleton screens (Doherty; the grid is a fixed shape).

---

## 7. UI craft bar (polish / professional look)

The "professional" ask is governed by the **Aesthetic–Usability effect** —
polish is read as competence. The throughline is **restraint**: fewer colours,
stronger type hierarchy, imagery doing the visual work.

**Good now:** coherent warm dark theme; the calendar widget; the big "1" shopping
number; clean card structure.

| Aspect | Current | Bar (principle) |
|---|---|---|
| Density | Vast whitespace + 32 empty "tap to add" → unfinished | Purposeful whitespace; content fills the eye, empties whisper (H8) |
| Hierarchy | Day header / slot / entry similar weight | Plan loud, structure quiet, empties near-silent (Von Restorff) |
| Colour | Saturated orange shortfall *bar*, green checks, red badge competing (F41) | **One accent** (brand green) for planned; **one** attention colour (amber) as border/dot not fill; neutrals elsewhere (H4, 1.4.1) |
| Entries | Flat full-width bars, tiny pill, no imagery | Content-forward cards: thumbnail + name + light meta |
| Icon actions | Icon-only print/trash, ambiguous | Labelled / overflow; never destructive-adjacent at icon size (H5, Fitts) |
| Empty states | Raw repeated "tap to add" | Designed, single, inviting (empty-state pattern) |
| Motion | Carousel slide only | Optimistic add, gentle card-in, skeletons; keep reduced-motion gate (Doherty) |

**Restraint benchmarks:** Sunsama / Things (hierarchy + calm), Fantastical /
Notion calendar (dense-but-legible weeks), Mealime / Pestle (content-forward meal
cards). Lands in R-Phase 3 (structure + card + bar) and R-Phase 6 (hierarchy +
colour + skeletons); the persona posture is R-Phase 5.

---

## 8. Resolved direction — build both (A + B behind a temp toggle)

**Decision (2026-06-25):** keep the experiment, don't pre-pick. The existing page
is **upgraded to Direction A** (de-sprawled vertical carousel); a **new, separate
page** implements **Direction B** (content-forward week board, §6); a **temporary
desktop toggle** switches between them. The pages **share state + logic** (no
behaviour drift) and differ only in *layout*. Pick a winner after living with both,
then delete the loser + the toggle.

### 8.1 Where Direction B re-homes the current panels

| Today (3 permanent columns) | Under B |
|---|---|
| Left recipe palette | **On-demand pinnable picker drawer** from a cell `+` — same component as the mobile bottom-sheet; pin-open preserves desktop drag (F18). |
| Right: "This week's shopping" | **Full-width consequences bar** under the grid (more prominent, never scrolls away; H1). |
| Right: calendar widget | **Month-jump popover** in the top strip (the grid *is* the week). Component kept, host changed. |
| Right: Full ingredient demand | **"Full demand ▾"** disclosure on the bar (progressive disclosure). |
| Right: Templates card | **"Templates ▾"** menu + in-place apply/manage drawer (no route hop; §9-E). |

### 8.2 Two-page mechanics (UX contract)

- **Shared focused week** via URL `?monday=YYYY-MM-DD` — toggling layouts keeps the
  week + in-flight context (F28 parity).
- **Persisted view choice** (`?view=grid` or localStorage) — refresh keeps the
  layout; toggle clearly marked temporary/beta.
- **Toggle is desktop-only.** Both pages render the **same mobile single-day
  focus** — the experiment is *carousel vs grid on desktop*; mobile is not forked.

### 8.3 Shared extraction (so the pages aren't 1,222-line twins)

- `useMealPlanner()` composable — all mutations (add/adjust/remove/clear), week
  nav, ingredient + shortfall loading, list generation, template apply/recurring.
  Both pages consume it; behaviour can't diverge (R-001/R-003).
- Leaf components: `RecipePicker` (search + trays; click-add + drag; rail / drawer
  / bottom-sheet hosts), `MealEntryChip` (**+ compact variant** for grid cells),
  `ShoppingSummary` (rail form in A, bar form in B), `WeekDayCard` (A) vs
  `WeekGrid`/`WeekGridCell` (B). `MealPlanCalendar` already standalone.

---

## 9. Deeper analysis (surfaces/flows beyond the main grid)

- **A. First-run journey 🔴.** Four empty regions at once; the one CTA dead-ends
  with no recipes. → designed first-run (§6.7). *(Empty-state pattern, H10.)*
- **B. Sequential builder 🟡** (`SequentialBuilderDialog.vue`). Picker is a flat
  checkbox list of **every recipe — no search/trays** (inconsistent; unusable at
  scale — Hick). `targetCount` hardcoded to 7 ("0 / 7" unexplained). Auto-spreads
  with no placement preview. **Permanently disabled "Email" button** ("isn't set
  up yet") — the placeholder smell the user called out (hide until real, H2). Build
  + generate-list inseparably coupled. → reuse the shared `RecipePicker` + shared
  placement logic.
- **C. Pool / "free" / log-cook 🟡 — dual-persona crux.** (See U6, §6.6.) Tesler:
  relocate behind the batch posture, don't delete.
- **D. Entry chip density 🟡 — blocks B.** Full-width chip won't fit ~130px grid
  cells → compact variant (§8.3).
- **E. Templates ecosystem 🟡.** One concept, **three entry points** (sidebar card,
  `/templates` route, recurring dialog); managing leaves the planner. Apply uses
  plain `$q.dialog` radio lists. → unify apply + manage into one in-place drawer
  (Hick, H4).
- **F. Calendar widget role shift 🟢.** A: keep as rail navigator. B: month-jump
  popover. Same component.
- **G. Shortfall / "cook-by" relevance 🟡.** Batch-only concept; share the posture
  gate with §9-C.
- **H. Drag ergonomics — a point FOR B 🟢.** Carousel: source + target far apart /
  off-screen. Grid: whole week visible as drop targets, picker adjacent — shorter
  distances (**Fitts**).
- **I. Loading/resilience 🟢.** ~10 parallel loads on mount, no skeleton → cards
  pop in (Doherty). Grid skeletons are trivial. "Calculating…" already present —
  keep.
- **J. Keyboard/a11y deeper 🟡.** Global ArrowUp/Down=change-week is guarded only
  vs `INPUT`/`TEXTAREA`, so arrowing off a focused button jumps the week → scope to
  the focused region or require a modifier. `<div>` rows → buttons; grid cells →
  `aria-label`; calendar status needs a text alternative (4.1.2, 1.4.1).

---

## 10. Engineering-standards remediation (R-rules)

- **R-001 (componentisation):** the 1,222-line file is the headline violation →
  R-Phase 1 extraction.
- **R-003 (state-ownership):** re-audit client derivations.
  - `cookByLabel` (L534–540) — display-formatting of the server shortfall set;
    **acceptable**, document it (or surface the date server-side if reused).
  - Calendar `dayStatus` (L71–79) — presentation of server facts; **clean**.
  - `needToBuy` (L748) — routes through `useStockStatus`; **clean** if the
    composable is the only threshold source.
  - Cross-ref **FU-081** (cookbook "planned-in" filter client-side) — adjacent;
    resolve together with state-ownership work on recipes.
- **R-002 (theme tokens):** confirm no raw `grey-*`/hex remain (historical
  `grey-4`/`grey-5` notes near empty states) — sweep in R-Phase 6.
- **R-014 (empty states):** the per-day "5× tap to add" is undesigned → R-Phase 2.
- **ADR evaluation:** if R-Phase 2/3 establish a reusable "collapse-empty-cells /
  progressive-disclosure slot" pattern, promote to a new `R-0NN` + ADR.

---

## 11. Open decisions

- **Q1 — Direction. ✅ RESOLVED → build BOTH** (A upgraded + B new, temp toggle;
  §8).
- **Q2 — Default slot visibility.** "Used slots + add" default, "show all slots"
  opt-in — confirm. Any household that genuinely plans all 5 slots daily?
- **Q3 — Pool/batch location.** Gate batch affordances behind the posture (§6.6)
  vs keep in the palette — recommend gate; confirm.
- **Q4 — Mobile picker.** Bottom-sheet from cell `+` (recommended) vs sticky
  mini-search.
- **Q5 — Slot-as-tag vs slot-as-rows (highest leverage).** Adopt cards-stack +
  tag + "group by slot" (diverges from F46; §6.2) — needs sign-off before
  R-Phase 3. Low-risk: B page only.
- **Q6 — Rich-card data path.** Enrich `MealPlanEntryDto` server-side vs client
  join to `recipeStore` — recommend server; confirm scope.

---

## 12. Phased plan

Each phase independently shippable; ends with a clean diff + `DORA_WORKLOG.md`
entry + the engineering-standards close-gate. (Supersedes the earlier
single-direction phasing.)

- **R-Phase 0 — Verify-state + remaining decisions.** Browser-verify FU-179 (esp.
  F34 "needs x" math); confirm Q2–Q6. No code.
- **R-Phase 1 — Extract shared core (R-001, behaviour-preserving).** Pull
  `useMealPlanner()` + leaf components out of the current page; it keeps working,
  just thinner. *Before duplicating* — extraction-first beats a literal 1,222-line
  copy (which would double-maintain mutation logic and silently diverge).
- **R-Phase 2 — Upgrade existing page → Direction A.** De-sprawl (used slots +
  "show all" toggle, Q2), sticky columns, promoted week-status, calm per-day empty
  state (R-014), first-run path (§6.7).
- **R-Phase 3 — New page → Direction B + temp toggle.** Content-forward week board
  (§6.4); compact chip variant; pinnable picker drawer; consequences bar; top
  strip; toggle wired + view persisted (§8.2). Pending Q5/Q6.
- **R-Phase 4 — Shared mobile single-day focus** + bottom-sheet picker (both
  pages; Q4).
- **R-Phase 5 — Persona + flow cleanups.** Batch posture gate (§6.6, §9-C/G);
  unify the builder onto the shared picker + hide the dead "Email" button (§9-B);
  unify templates apply/manage (§9-E).
- **R-Phase 6 — Hierarchy + colour discipline + a11y + tokens + skeletons** (§7,
  §4.6, §9-I/J).
- **Later — pick the winner**, delete the loser page + toggle, fold surviving
  ideas across.

---

## 13. Feedback coverage — F1–F49 re-graded

Re-evaluation of the original §MEAL PLANS feedback now that C-2 has shipped.
**✅ still well-served · 🟡 regressed / new concern · ➖ out of scope here.**

| # | Feedback bullet | Grade | Note |
|---|---|---|---|
| F1 | Sequential builder flow | ✅ | Ships; but see §9-B (no search, dead Email btn). |
| F2 | Templates / rotating / auto-add | ✅ | Complete. |
| F3 | Page icon (meals, not calendar) | 🟡 | Nav still a **calendar** icon. U8 / R-Phase 2. |
| F4 | Shortfall = chef's hat | ✅ | Rail uses chef-hat. |
| F5 | Allocation broken | ✅ | Server-owned pool; works. |
| F6 | "I'm a notification!" placeholder | ✅ | Fixed (B7). |
| F7 | Ingredient-demand colour consistency | 🟡 | Verify shared token mapping (§4.5, R-Phase 6). |
| F8 | Drag/drop disabled on mobile | ✅ | `pointerType === 'mouse'` gate. |
| F9 | Tap alternative to drag | 🟡 | Exists but low-discoverability + pogo (U3, U5). |
| F10 | Plan instance name useless | ✅ | Dropped (C-2.E). |
| F11 | Date picker for new plan wrong | ✅ | Gone; implicit week create. |
| F12 | Template management | ✅ | Manage page + rail actions (consolidate, §9-E). |
| F13 | Calendar widget design | ✅ | A highlight. |
| F14 | Widget above shopping info | ✅ | Rail order correct. |
| F15 | Current day marked | ✅ | Today dot + badge. |
| F16 | Vertical carousel | 🟡 | Faithful, but compounds into sprawl (§5). Both built (§8). |
| F17 | Calendar changes with carousel | ✅ | `focusedMonday` bound. |
| F18 | Trays, draggable | ✅ | Trays ship; drag preserved via pinned drawer (§8.1). |
| F19 | Trays reusable on cookbook | ➖ | Enabled by R-Phase 1 extraction. |
| F20 | Main area centring | 🟡 | Over-centred → wasted width (U4). |
| F21 | All-recipes filterable/vertical | ✅ | Palette + search. |
| F22 | Add without drag | 🟡 | See F9. |
| F23 | Dora assistant planning | ➖ | Assistant scope. |
| F24 | Recurring / past read-only | ✅ | Both hold. |
| F25 | Recurring × editing | ✅ | Fork-on-edit. |
| F26 | Batch vs fresh personas | 🟡 | Layout assumes a populated grid (§4.2); fixed by §6.6. |
| F27 | Meal cards don't fit | ✅ | Chip wraps; needs compact variant for B (§8.3). |
| F28 | Refresh resumes focused week | ✅ | URL `?monday=`. |
| F29 | Past-day drop 400 bug | ✅ | C-2.K timezone fix. |
| F30 | Hover stock → highlight days | ✅ | Desktop hover. |
| F31 | Shopping-list status per item | ✅ | `listStatusLabel`. |
| F32 | Individual add | ✅ | `AddToListButton`. |
| F33 | Add-or-generate / existing-or-new | ✅ | `pickGenerateTarget`. |
| F34 | "Needs x" math correctness | 🟡 | FU-179 browser-verify (R-Phase 0). |
| F35 | Slot always "Dinner" bug | ✅ | Derives from cell; slot-as-tag improves further (§6.2). |
| F36 | "Edit entries" button gap | ✅ | Removed; inline edit. |
| F37 | Delete plan → "Clear week" | ✅ | But icon-only/risky placement (U7). |
| F38 | Theme-aware elements | 🟡 | Re-verify (R-Phase 6). |
| F39 | Remove CSV button | ✅ | Gone. |
| F40 | Remove "Week of…" title | ✅ | Range label only. |
| F41 | Colour/icon overload | 🟡 | Chip + colour still busy (§4.5, §7). |
| F42 | On-hand display in palette | 🟡 | "n free" cryptic (U6, §6.6). |
| F43 | Drop "cookable now" on planner | ✅ | Not surfaced. |
| F44 | Squishing horizontally | 🟡 | Inverted → wasted width (U4). |
| F45 | Shortfall banner redundant | ✅ | Single rail line. |
| F46 | Time of day as rows | 🟡 | Always-all-slots drives U1; slot-as-tag proposed (§6.2, Q5). |
| F47 | Same recipe+slot increments | ✅ | `servings += 1`. |
| F48 | Don't drag one-by-one | ✅ | Per-entry ± + pool ±. |
| F49 | Slots configurable + defaults | ✅ | Household slot vocabulary. |

**Net:** all 49 shipped; the re-grade surfaces **~13 regressions / new concerns**,
almost all tracing to one root (empty-slot sprawl + the two-surface layout).
R-Phase 2 + R-Phase 3 close the majority.

---

## 14. References (industry-standard sources)

- **Nielsen, J.** — *10 Usability Heuristics for User Interface Design* (NN/g,
  1994; rev. 2020). H1–H10 above.
- **Yablonski, J.** — *Laws of UX* (lawsofux.com / O'Reilly, 2020). Hick, Fitts,
  Jakob, Tesler, Miller, Von Restorff, Doherty, Aesthetic–Usability.
- **NN/g articles** — *Progressive Disclosure*; *Empty States / "Blank Slate"*;
  *Skeleton Screens & perceived performance*.
- **W3C** — *WCAG 2.2* (1.4.1 Use of Colour, 1.4.3 Contrast, 2.1.1 Keyboard,
  2.4.7 Focus Visible, 2.5.8 Target Size, 4.1.2 Name/Role/Value).
- **Platform conventions** — Material Design (bottom sheets, FAB); Apple HIG
  (clarity, deference) — for the mobile picker.
- **Domain conventions (Jakob's Law)** — Google/Apple Calendar (week grid);
  Plan to Eat, Paprika, Mealime, Pestle, Sunsama (meal/task cards, week boards).

---

## 15. Next step

R-Phase 0 → R-Phase 1 (extract shared core, behaviour-preserving) → R-Phase 2
(Direction A) → R-Phase 3 (Direction B + toggle). Highest-leverage open call is
**Q5** (slot-as-tag). On each phase close: append `DORA_WORKLOG.md`, update
`CHANGELOG.md`, flip the regraded bullets in `COVERAGE_GAPS.md`, run the
engineering-standards close-gate. Tracking: **FU-304**.
