# INV-6 — Recipe-comparison worth assessment

**Status:** investigation memo · **no code changes** · feeds the C-4
Cookbook brief (which defers to this outcome).
**Brief:** `docs/prompts/INV_investigations.md §INV-6`.
**One-page deliverable**, not a full design.

---

## 1. What it does today (live code)

- Surface: a `Compare` toggle button on `web_app/src/pages/RecipesOverview.vue`
  header. Toggling enters a row-selection mode (cap **3 recipes**;
  picking a 4th drops the oldest selection in insertion order).
- Trigger: a second button `Show comparison` appears once ≥2 are
  selected. Opens a `BaseDialog` (~`95vw × 90vh`).
- Layout inside the dialog: **N cards side-by-side**, not a shared-row
  table. Each card carries:
  - recipe name, `cuisine · category`;
  - **Prep + cook** (sum of `prep_time_minutes + cook_time_minutes`);
  - **Servings**;
  - **Difficulty**;
  - **# ingredients**;
  - **Missing right now** (count of ingredients whose linked stock
    item is at low/out level);
  - a chip-grid of the recipe's ingredients, with **red chips for
    missing** items.
- Backend: there is **no comparison-specific endpoint**. The dialog
  re-renders client-side from the cached `recipes` store.
- Footprint: ~100 lines in `RecipesOverview.vue` (button + dialog +
  `selectedIds`/`compareMode` state + 5–6 helpers); plus a
  `selectable` prop the dialog reads from `RecipeCard`.
- Charter-relevant feedback already on the page from the user
  (`Feedback _ Fixes - as of [06-Jun-2026].md`):
  - "Recipe comparison tool in its current state feels useless. Is
    there any way to make this more useful? Would people actually use
    this? I feel they wouldn't. If not, let's remove it."
  - "Comparison feature feels useless without some sort of sorting,
    highlighting or some way to make comparison easier than reading
    a table of info."
  - "Attribute header in comparison feels unnecessary, leave that
    header blank."
  - "Recipe comparison chips are not theme aware or colour choice is
    bad in dark mode pesto. The white on grey colour is not readable."
  - "Formatting of comparison looks awkward/bad. E.g. prep+cook time
    is very far from the info, and the info is on 2 lines. 2, new
    line, min."

## 2. Signal of use

- **No telemetry** on either the `compareMode` toggle or
  `showComparison` open. Zero objective usage data.
- **No backend route** that would even let a server-side counter
  exist.
- **No reference** to the dialog anywhere outside `RecipesOverview`
  — nothing else in the app routes the user toward it.
- **User self-report** (above): "I feel they wouldn't [use it]."
- **Discoverability:** `Compare` lives in a row of buttons next to
  Search and New recipe. It's a noun, not a verb in context — the
  user has to *decide* they want to compare and intentionally enter
  a mode. That's a step zero most users never take.

Conclusion: there is no positive signal of use and at least one
negative self-report. The default-OFF Charter rule (P10) bites
already.

## 3. What a *useful* comparison would actually need

If we were to keep the feature, it would need to answer one of three
real cook-decision questions:

1. **"Which one tonight?"** — fewest missing ingredients × shortest
   total time × wasn't cooked recently.
2. **"Which one feeds the house?"** — servings vs. headcount.
3. **"Which one's cheaper?"** — cost-estimate per serving (gated by
   the money opt-in in C-4 and the budget feature; not in scope here).

A minimally useful redesign would carry:

- **Two recipes max** (three is rare in real "which one tonight"
  decisions and forces tiny cards).
- A **shared-row table** with attributes on the left, recipes
  across — not card islands. This matches the user's "attribute
  header should just be blank" remark, which only makes sense if the
  intended layout is rows-of-attributes.
- **Per-row winners highlighted** (shortest time gets a chip; fewest
  missing gets a chip; etc.).
- A **single decision line at the bottom** ("**Cook A** — fastest
  and fewest missing.") — Charter P6 (every insight leads to one
  action).
- **Sort axis picker at the top** — sort by time / missing /
  last-made / cost. Today's dialog ignores ordering entirely.
- **Theme-aware chips** (use tokens — A1).

Even with all this, the core feature still requires the user to:

1. Decide they want to compare;
2. Enter `Compare` mode;
3. Tap 2 rows;
4. Tap `Show comparison`;
5. Read the table;
6. Decide.

Six steps before the cook decision. The Cookbook overview already
shows time, missing count, and cookable indicator on every row —
**the same answers as comparison, with sort + filter** — in zero
extra steps.

## 4. Charter check

| Principle | Verdict |
|---|---|
| **P1 Effortless** | **Fails.** Six-step deliberate flow for a question already answered by the overview's sort + filter. |
| **P5 Closed loop** | **Fails.** Comparison doesn't write anything back to pantry/lists/prices/plan. It's a read-only side-pane. |
| **P6 Insight → action** | **Fails today** (no per-row winner, no decision line). Could be fixed by §3's redesign, but a "Cook A" button at the bottom of a dialog just duplicates the recipe-row `Cook` action. |
| **P10 Anti-creep (anti-Grocy)** | **Fails.** Surface area for a question better answered on the same overview by sorting. The reconciled finishing plan (`§4`) literally lists "Remove the comparison tools" as a Charter-P10-aligned cut. |
| **P11 Fast UX** | **Fails on mobile.** 3-card layout collapses to vertical stack at narrow widths, defeating the side-by-side premise. |

There is no Charter principle the feature actively serves. Anti-creep
is the dominant signal.

## 5. Where the real use cases land if we cut

Cutting the comparison dialog doesn't lose any answer; it just moves
each question to a Charter-aligned surface:

| Question | Better home |
|---|---|
| "Which one tonight?" | **Cookbook overview** — already sortable by `time`, `missing`, `last_made` (some of these still need to be wired as sort axes; tiny addition, no comparison-specific code). Plus the C-4 Cookbook redesign and the C-2 "Haven't had in a while" tray. |
| "Which one feeds the house?" | **Servings auto-adjust** in Cook Mode (C-3 brief, with `meals_per_week` / headcount from onboarding). |
| "Which one's cheaper?" | **Cost estimate** per recipe (C-4, gated by money opt-in). Per-serving cost shows on each row; no comparison ritual needed. |
| "What should I cook tonight?" | **Dora assistant** intent — "what should I cook?" — backed by stock + plan + last-made. Closed-loop (P5) and effortless (P1). |

Every replacement is either already on the roadmap or is a small
addition to surface that already exists. None require a "Compare"
mode.

## 6. Cleanup cost if we cut

- `RecipesOverview.vue`: drop the two header buttons, the dialog
  block, `compareMode` / `selectedIds` / `showComparison` /
  `MAX_COMPARE` state, `toggleCompareMode` / `onToggleSelect` /
  `selectedRecipes` helpers, and the `selectable` prop wiring on
  `RecipeCard` instances. ~100 lines, single file.
- `RecipeCard.vue`: the `selectable` prop has no other caller (worth
  a grep to confirm at implementation time). Likely deletable.
- No backend changes; no migration; no API contract change.
- Documentation: `STATUS.md` X2 = `DONE` flips to `CUT`. Master plan
  already lists this as resolved-cut (Decision 3 / §4).
- Risk: nil. Read-only feature with no downstream dependencies.

## 7. Recommendation

**Cut it.**

The feature has:

- no usage signal,
- a negative self-report from the only known user,
- five Charter-principle fails,
- a small clean cleanup cost,
- every real use case better served by surfaces already on the
  roadmap (Cookbook sort + filter, Cook Mode auto-adjust, money-opt-in
  per-row cost, Dora "what should I cook?").

**Where to put the cut in the plan:** fold into **C-4 Cookbook
redesign** as a Charter-aligned removal. The proposal can explicitly
state X2 is removed in the same chunk that introduces the row-level
sort axes (`time`, `missing`, `last_made`, optional `cost_per_serving`),
so the user lands on the Cookbook overview and finds the answer
comparison was meant to give — without ever entering a dialog.

## 8. Open follow-up after cut

- Add the sort-axis additions to the Cookbook redesign brief (C-4),
  specifically: `last_made_on` (already a recipe field), `missing`
  count (already computed for the comparison and the `cookable`
  indicator), and `total_time` (`prep + cook`). Cost-per-serving
  arrives with the money opt-in work.
- Once C-4 ships, flip X2 in `STATUS.md` from DONE to **CUT (INV-6,
  2026-06-06)** with a one-line note.

---

*Memo ends.*
