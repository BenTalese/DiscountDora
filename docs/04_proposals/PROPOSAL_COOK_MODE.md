# Proposal — Cook Mode Redesign (C-3)

**Status:** **Decisions resolved 2026-06-08** (see §5a) · brief otherwise unchanged · **Date drafted:** 2026-06-06 · Changes NO code.  
**Scope:** Redesign cook mode — the finish-cooking loop, serving auto-adjust,
location-grouped ingredients, tools, highlight-vs-tick, timer, unit formatting,
the "sous chef" voice affordance, and a finish celebration. Ripples to recipes
(C-4: tools, versions, structured steps, notes), onboarding (C-5: headcount), and
the shopping list (C-7).

> **Charter tie-break:** Effortless (P1) + Closed-loop (P5). Cook mode is where the
> loop closes — cooking *consumes* stock and *produces* meals. The finish flow is
> the highest-value surface: it must turn "I cooked" into accurate stock + a
> restock nudge with near-zero friction.

---

## 1. Current state (from live code)

Cook mode (`RecipeCookMode.vue`) is already fairly rich: a single-step layout with
progress bar, an expandable ingredient panel, a "all steps" navigator, **B8
session-only substitute swaps** (good — keep), a **timer** auto-detected from step
text, and **voice** (TTS + speech-recognition commands). Gaps and rough edges:

- **Instructions are a freeform blob split on newlines** (`:356-363`) — there are
  no structured steps, so per-step ingredient association is done by **fragile
  text-matching** (`:424-432`).
- **Ticking** ingredients *and* steps (`usedIds` set + per-step checkboxes) — the
  user finds this odd and unnecessary.
- **Finish flow is blunt:** one "update stock levels" toggle that just decrements
  every used item by **one** level (`:572-584`), a meals-cooked input defaulting
  to **1**, and a blanket "add anything that ran out" toggle. No per-item level
  choice, no celebration.
- **No serving/headcount adjust**, **no tools**, **no location grouping**, **no
  fill-bar/sound** on the timer (toast only, not theme-aware, reset hidden), and
  **"2scoops"**-style unit formatting.

---

## 2. The redesign

### 2.1 Finish-cooking flow — actually close the loop (L319, L334-338)
Replace the blunt toggle with a **per-item checklist** — the cooking equivalent of
the shopping "receipt" close-out:

- For each ingredient actually used, show its **current level** and let the user
  **set the new level of their choosing** (not a forced one-step decrement). Quick
  defaults (e.g. "↓ one level", "Out") with the option to pick any level.
- A **per-item add-to-shopping-list** affordance (the **C-7** cart component) on
  each row — this **removes the need for the blanket "add ran out?" toggle**
  (L336).
- **Meals cooked starts at 0** and is optional (L338) — "leave at 0 if you just
  ate it."
- Modal **click-out cancels** (→ A3) (L334).
- **Celebration on finish** (L333, L337): a "hooray" moment — confetti/animation
  + a **"you saved N meals"** framing for batch cookers (uses the meals-cooked
  count). Replaces the flat "Nice cooking!" toast.
- Session substitutes already route correctly (the *substitute's* item is the one
  decremented/restocked, `:568-570`) — keep.

### 2.2 Serving auto-adjust by headcount (L320)
"**How many are we cooking for today?**" — a zero-friction control that **scales
ingredient quantities** for the session:

- **Default from onboarding** (C-5 captures household headcount); adjustable per
  session without leaving the flow.
- Scales displayed quantities (e.g. recipe serves 4 → cooking for 6 → ×1.5).
- Session-only; never edits the saved recipe (same discipline as B8 swaps).

> **Open:** rounding/units — scaling "1.5 eggs" or "0.66 cups" needs sensible
> display (fractions? round?). Proposed: show scaled value, round sensibly, don't
> overthink exactness (P1). Confirm (§5).

### 2.3 Ingredients during cooking — grouped by location, level de-emphasised (L321, L334, L323-styling)
- **Group by base location only** (fridge / pantry / …), no sub-areas (L321; the
  original spec: "so you don't run back and forth"). Sorted within group.
- **Stock level is not relevant mid-cook** — "we've decided to cook" (L334). Drop
  the level/missing emphasis from the in-cook list; all stock-level interaction
  moves to the finish checklist (§2.1).
- Rebuild the ingredient UI — the current one "looks horrible" (L323) and the page
  "feels boring/basic" (L330). Token-driven (A1), more cook-friendly (large, calm).

### 2.4 Highlight instead of tick (L327, L328) — and the structured-steps dependency
- **Remove ticking** for both ingredients and steps; instead **highlight the
  ingredients used in the current step**.
- This only works reliably if steps know *which ingredients they use* — today
  that's text-matched and breaks when an ingredient appears across steps 1/2/3
  (L327). **Reliable highlighting needs structured steps** (§2.6) that carry an
  explicit ingredient (and tool) association.

> **Open (brief):** ticking removal — confirm full removal (proposed), or keep an
> optional "mark done" for users who like it. (§5)

### 2.5 Tools section (L322)
If the recipe has **tools** (the configurable list added in **C-4**), show a tools
section and **highlight tools per step** like ingredients. **Don't render it when
the recipe has no tools.**

### 2.6 Sub-steps & per-step hints — structured steps (L323)
The user asks how sub-steps work, how they're added, and whether a step can carry
a **hint shown as a footer on the current step**. All of cook-mode's richer
per-step behaviour (reliable highlighting §2.4, per-step tools §2.5, per-step
timers §2.7, hints) depends on **steps being a structured list rather than a
freeform blob**.

**Recommendation:** model recipe instructions as **structured steps** (each step =
text + optional sub-steps + optional hint + the ingredients/tools it uses). This is
a **recipe-model change that belongs in C-4** (it's adjacent to C-4's multi-part
"sections"). Cook mode then renders steps richly; a freeform recipe degrades
gracefully to one-step-per-line with text-matched highlighting (today's behaviour)
as the fallback.

> **Open (brief):** sub-step model — full structured steps (proposed, via C-4) vs
> keep freeform + the fragile text-match. (§5)

### 2.7 Timer (L324, L325)
- **Theme-aware** (A1), with a **visible reset** button.
- **Sound** on finish (not just a toast).
- The timer component itself **changes styling** when it fires, and renders as a
  **bar that fills up** (visual progress), not just MM:SS text.
- Keep the auto-detect-from-step-text + voice control (already present).

### 2.8 Unit formatting (L326)
Fix "2scoops". Use an **inclusion list of units that attach directly to the
number** (no space) — `ml, g, kg, l, mg, tsp, tbsp, …` → "200ml"; everything else
gets a space → "2 scoops". 

> **Open (brief):** the exact attach-directly unit list. (§5)

### 2.9 Voice / "sous chef" (L329)
The voice button is a hidden feature and "enable voice" is unclear. **Make it an
obvious, named affordance — your digital *sous chef*** (have a little fun with it).
Surface what it does (say "next" / "previous" / "repeat" / "start timer"). The
underlying TTS + recognition already exist; this is discoverability + branding.

### 2.10 Substitutes (B8) — keep
The session-only swap is correct and well-built (`:216`, `:390`, `:568-570`):
temporary, never edits the recipe, and the finish flow consumes the substitute.
No change; cross-reference only.

---

## 3. Cross-cutting (covered elsewhere)

| Feedback | Home |
|---|---|
| Finish modal click-out to cancel (L334) | **A3** modal standard |
| Theme-awareness: timer, page styling (L324, L330) | **A1/A1b** |
| Per-item add-to-list at finish (L336) | **C-7** cart component |
| Tools field + **structured steps** + versions + personal notes | **C-4** (recipe model) |
| Headcount default (L320) | **C-5** onboarding |
| Substitute swap (L302 etc.) | **B8** (done) |

---

## 4. From the original spec (historical — `docs/00_original_spec/`)

| Original note | Verdict | Effect |
|---|---|---|
| *Cook mode "could be an interactive mode with text-to-speech, voice recognition like 'next step', and timers"* | **keep (already built)** | The current TTS/voice/timer matches the original vision; §2.7/§2.9 polish it (sound, fill-bar, sous-chef branding). |
| *Ingredients grouped by stock location ("so you don't run back and forth")* | **keep (grounds §2.3)** | Base-location grouping during cooking. |

(No superseded items; the original cook-mode vision aligns with the current build.)

---

## 5. Open decisions (for co-design)

1. **Ticking removal** (L327/328) — remove entirely + per-step highlight
   (proposed), or keep an optional "mark done"?
2. **Sub-step / structured-steps model** (L323) — model structured steps in C-4
   (proposed; enables reliable highlighting, per-step tools/hints/timers), or keep
   freeform + text-match?
3. **Quantity-unit inclusion list** (L326) — confirm which units attach with no
   space (`ml, g, kg, l, mg, tsp, tbsp`?) vs spaced.
4. **Serving scaling display** (§2.2) — how to render fractional scaled
   quantities (round / fractions / show as-is)?
5. **Finish-flow level controls** — per-item "set any level" (proposed) vs simpler
   "↓ one / Out / unchanged" quick choices only?

---

## 5a. Resolved decisions (2026-06-08)

Decisions §5 closed out with the user. The canonical answers below override
the "proposed" hints in §5.

| # | Topic | Resolution |
|---|---|---|
| **DEC-1** | Ticking in cook mode | **Removed entirely.** Per-step highlight of the current step's ingredients/tools replaces tick boxes. No optional "mark done". |
| **DEC-2** | Sub-steps / structured steps | **Model structured steps in C-4.** Recipe instructions become a list of `{ text, sub_steps?, hint?, ingredient_refs[], tool_refs[] }`. Cook mode renders steps richly when structured; degrades to one-step-per-line + text-matched highlight as the fallback for freeform recipes. **Closes FU-040.** C-3's per-step features (reliable highlight §2.4, per-step tools §2.5, per-step timers §2.7, per-step hints §2.6) are gated on this C-4 model change landing first. |
| **DEC-3** | Quantity-unit attach list | **Metric + US customary attach (no space); culinary attaches with a space.** No-space units: `ml, g, kg, l, mg, oz, lb, floz, pt, qt`. Spaced (always): `tsp, tbsp, teaspoon, tablespoon, cup, cups, clove, cloves, scoop, scoops, slice, slices, …` (any word-shaped unit). User's framing: *"metric and US makes most sense; culinary like tsp/teaspoon should have a space."* |
| **DEC-4** | Fractional scaled qty | **Round sensibly.** 1.5 eggs → 2 eggs; 0.66 cups → ⅔ cup (or "2/3 cup"); never show raw decimals. Cooking is forgiving (P1 Effortless). |
| **DEC-5** | Finish-flow level picker | **Quick chips + full picker.** Each row carries chips "↓ one level / Out / Unchanged" plus a level-dropdown override. Fast for the common case, full control when needed. |

**Sequencing impact:** DEC-2 promotes the C-4 structured-steps work to a
*blocker* for C-3 sub-features §2.4/§2.5/§2.6/§2.7. Adjust the §6
sequence accordingly: the C-4 step-model change lands before C-3 chunks 4
(highlight) and onward. Chunk 1 (finish flow §2.1) and chunk 2 (polish
§2.7–2.9) stay independent and can ship first.

---

## 6. Suggested sequencing

1. **Finish flow** (§2.1) — the highest-value, loop-closing change: per-item level
   checklist + C-7 add-to-list + meals-start-at-0 + click-out. (Needs C-7 for the
   per-item add; can ship with a simple add fallback first.)
2. **Celebration** (§2.1) + **timer polish** (§2.7) + **unit formatting** (§2.8) +
   **sous-chef** discoverability (§2.9) — independent, low-risk polish.
3. **Location grouping** (§2.3) + ingredient-UI rebuild + de-emphasise level
   mid-cook (§2.3).
4. **Serving auto-adjust** (§2.2) — needs the onboarding headcount default (C-5).
5. **Structured steps** (§2.6, via C-4) → then **highlight-instead-of-tick**
   (§2.4), **tools per step** (§2.5), **per-step hints**. This cluster is gated on
   the C-4 recipe-model change.

---

## 7. Feedback coverage

Maps COOK MODE (L317-338).

| Bullet (line) | Summary | Where |
|---|---|---|
| L319 | Set stock levels at finish (checklist) + add-to-list after cooking | §2.1 |
| L320 | Auto-adjust quantities by headcount (default from onboarding) | §2.2 (C-5 dep) |
| L321 | Ingredients grouped by base location | §2.3 |
| L322 | Tools section, highlighted per step; hide if none | §2.5 (C-4 dep) |
| L323 | Sub-steps: how added/displayed; per-step hints as footer | §2.6 (+ open 2) |
| (L323b) | Ingredients UI looks horrible | §2.3 |
| L334 | Stock level not relevant mid-cook | §2.3 |
| L324 | Timer not theme-aware; reset not visible | §2.7 (A1) |
| L325 | Timer no sound; should restyle + fill-bar | §2.7 |
| L326 | "2scoops" — unit inclusion list | §2.8 (+ open 3) |
| L327 | Ticking calc odd (ingredient across steps) → highlight | §2.4 (+ open 1) |
| L328 | Ticking unnecessary for ingredients & steps → highlight only | §2.4 |
| L329 | Voice button not obvious; "enable voice" unclear; sous chef | §2.9 |
| L330 | Page styling boring/basic | §2.3 (A1) |
| L334b | Finish modal click-out doesn't cancel | §2.1 → A3 |
| L337 | Finish feels boring — where's the hooray/congrats | §2.1 (celebration) |
| L336 | Mark levels individually; removes "add to list?" toggle; per-item add button | §2.1 |
| L338 | Meals cooked should start at 0, optional | §2.1 |
