# IMPL_PLAN_HELP_CHIPS — FU-044 narrowed-scope help chips

**Origin.** User re-scoped FU-044 on 2026-07-06. Dropped the full opt-in
help-overlay mechanism from `PROPOSAL_HELP_OVERLAY.md`; retained only the
narrower ask: add targeted `(?)` hover-help chips next to **specific
confusing controls** already identified. No new component, no toggle, no
overlay engine — just the shape already used at
[RecipeDetailPage.vue:756-770](web_app/src/pages/RecipeDetailPage.vue).

**Superseded design.** `docs/04_proposals/PROPOSAL_HELP_OVERLAY.md` is
retired in favour of this plan; the "?" toolbar toggle, `v-help`
directive, coachmark engine, and DoraBot fronting are all deferred as
someday. Help/guides page + assistant remain the deep-help fallback.

**Why this exists.** The audit + copy draft are already done in the
2026-07-06 session; recording them here so the next session can execute
without re-discovery.

---

## The pattern (do not deviate)

```vue
<q-icon :name="ICONS.help_outline" size="14px" class="q-ml-xs">
    <q-tooltip>[copy]</q-tooltip>
</q-icon>
```

**Rules:**
- `size="14px"` — smaller than surrounding text; a hint, not a shout.
- `class="q-ml-xs"` when placed after a label; `q-mr-xs` when placed
  before. Adjust if the surrounding layout needs different spacing.
- **Place inside the same element as the label** it's clarifying (so
  hovering the icon anchors the tooltip near the label, not floating
  detached). If the label lives in a chip/button, sit the icon
  immediately after the label text; do NOT put the tooltip on the
  chip/button itself — the chip may already have an interaction
  tooltip.
- **Tooltip copy:** plain English, present tense, one or two sentences.
  Explain WHAT the number/control does and WHERE the derivation comes
  from. No jargon that isn't defined in the tooltip itself.
- **Do not add a chip where a `q-tooltip` already exists** on the same
  element — check first; the audit table already flags
  already-covered items, but a small number may have been added
  between the audit and the implementation. Grep the file for
  `q-tooltip` around the target line before editing.
- **Import once, use many:** `import { ICONS } from 'src/style/icons';`
  is already present on every target file (verified during the audit) —
  no new imports needed.

## Style rules that apply

- **R-002 (theme tokens only):** the icon inherits colour from its
  parent context; do NOT set `color=` on the `q-icon`. Let the caption
  / chrome class carry the muted tone.
- **R-008 (code-style minimalism):** no comment blocks around the
  chips — the copy IS the explanation. One `<!-- FU-044 chip -->`
  marker per file at the top of the first chip is fine but not
  required.
- Not translation-ready: strings inline (not `$t()`). Layer C locale
  translation is parked (FU-043 close-gate).

## What NOT to touch this session

- `RecipeDetailPage.vue` "Estimated cost" chip — already has help
  ([RecipeDetailPage.vue:758-770](web_app/src/pages/RecipeDetailPage.vue)).
- `PantryBeliefChip.vue` — already has a full tooltip (lines 19-24).
- `StocktakeRunner.vue` "Mute" button — has a native confirmation
  dialog, sufficient.
- Toolbar `help_outline` icon linking to `/help` — leave as-is; no
  overlay engine to add.

---

## The 32 chips

**Format:** `#`. **File:line — control label** — copy (paste into
`<q-tooltip>…</q-tooltip>`).

### Dashboard / Reports / Alerts (7)

1. **[DashboardPage.vue:637](web_app/src/pages/DashboardPage.vue) — Kitchen health score card**
   > A 0–100 score of how your kitchen's tracking right now — waste,
   > on-budget, freshness, unplanned run-outs, and stocktake staleness,
   > averaged. Only signals with real data count; missing signals
   > don't drag the score down.

2. **[DashboardPage.vue:898-908](web_app/src/pages/DashboardPage.vue) — Savings captured range chips (30d/90d/1y)**
   > Total savings vs. RRP across every shopping list you finished in
   > this window. Includes only lines where a real deal price was
   > captured.

3. **[ReportsPage.vue:268-277](web_app/src/pages/ReportsPage.vue) — Year-over-year card**
   > This window's total spend compared to the same-length window a
   > year earlier — so a 90-day view compares this 90 days to the
   > matching 90 days last year.

4. **[AlertsPage.vue:10,257-259](web_app/src/pages/AlertsPage.vue) — Needs action / FYI tier segmented control**
   > **Needs action** = things you should decide on soon (expiring
   > items, low stock, run-outs). **FYI** = things worth knowing about
   > but no decision required (price drops, stocktake nudges).

5. **[DashboardPage.vue:1198](web_app/src/pages/DashboardPage.vue) — Cookable tonight label**
   > Recipes where every ingredient is currently in stock — nothing
   > to buy or swap first.

6. **[ReportsPage.vue:188](web_app/src/pages/ReportsPage.vue) — Meals-worth metric**
   > Total portions you cooked in this range, summed from the "how
   > many meals?" answer at the end of each cook. Different from
   > **cook count** — one cook can yield several meals.

7. **[AlertsPage.vue:142-152](web_app/src/pages/AlertsPage.vue) — Alert tier override row**
   > Choose whether this alert kind lands in **Needs action**, **FYI**,
   > or is silenced entirely. Overrides the app-wide default set in
   > Settings.

### Meal plans / Recipes (6)

8. **[MealPlansOverview.vue:136-141](web_app/src/pages/MealPlansOverview.vue) — Shortfall metric chip**
   > Meal-plan slots whose recipe doesn't have enough cooked-and-frozen
   > portions to cover them. You'll need to cook or shop for the
   > missing ingredients.

9. **[MealPlansBoardPage.vue:120-126](web_app/src/pages/MealPlansBoardPage.vue) — Shortfall metric chip (sticky bar)**
   > Same as above — meal-plan slots without enough cooked portions
   > in the pool.

10. **[RecipeDetailPage.vue:287-294](web_app/src/pages/RecipeDetailPage.vue) — Unallocated meals subtitle**
    > Portions of this recipe already in your pool but not yet
    > earmarked for any meal-plan slot. Cook mode adds to the pool;
    > planning a meal subtracts from it.

11. **[RecipesOverview.vue:80-88](web_app/src/pages/RecipesOverview.vue) — Cookable now filter chip**
    > Recipes where every ingredient is currently in stock. Distinct
    > from **Have meals in pool** — that one shows recipes with
    > cooked-ahead portions ready to serve.

12. **[RecipeCookMode.vue:37-45](web_app/src/pages/RecipeCookMode.vue) — Sous Chef toggle**
    > Reads each step aloud as you go, hands-free. Off = silent
    > cook mode; you tap through the steps yourself.

13. **[RecipeCookMode.vue:46-54](web_app/src/pages/RecipeCookMode.vue) — Listen for hands-free mic icon**
    > Turns on the mic so **next / previous / repeat / pause**
    > navigate cook mode without touching the screen. Independent
    > of Sous Chef — you can listen without narration or narrate
    > without listening.

### Stock surfaces (8)

14. **[StockOverview.vue:174](web_app/src/pages/StockOverview.vue) — Needs check filter chip**
    > Items whose recorded stock level is old enough that Dora's
    > stocktake mode wants you to verify it's still correct.

15. **[StockOverview.vue:162](web_app/src/pages/StockOverview.vue) — Will auto-add on low filter chip**
    > Items with the **Auto-add when low** toggle on — they drop
    > into your primary shopping list automatically when they hit
    > Low.

16. **[StockOverview.vue:158](web_app/src/pages/StockOverview.vue) — Essential filter chip**
    > Items you've flagged as household staples. Surfaced first in
    > filters and prioritised in shopping-list suggestions.

17. **[StockOverview.vue:166](web_app/src/pages/StockOverview.vue) — Open / in-use filter chip**
    > Items you've marked as opened — currently being used, worth
    > watching for expiry.

18. **[StockItemDetailPage.vue:327](web_app/src/pages/StockItemDetailPage.vue) — Essential toggle**
    > Flags this as a household staple. Surfaced first in the
    > Essential filter and prioritised in shopping-list suggestions.

19. **[StockItemDetailPage.vue:352](web_app/src/pages/StockItemDetailPage.vue) — Auto-add when low toggle**
    > When this item drops to Low, add it to your primary shopping
    > list automatically — no need to remember.

20. **[StocktakeRunner.vue:67](web_app/src/pages/StocktakeRunner.vue) — "Checked every X · Y days overdue" subline**
    > How often stocktake mode wants you to re-check this item
    > (**Weekly / Fortnightly / Monthly**) and how far past the last
    > check date you are. Cadence is set globally in Settings or
    > per-item on the detail page.

21. **[StocktakeRunner.vue:125](web_app/src/pages/StocktakeRunner.vue) — Push 3 days button**
    > Delays this item's next stocktake prompt by 3 days without
    > recording a check. Use when you'll be able to look properly
    > soon.

### Shopping / Pricing / Settings (11)

22. **[ShoppingListDetail.vue:144,146](web_app/src/pages/ShoppingListDetail.vue) — Finish & restock button**
    > Marks this shop as done: every ticked item moves back to
    > **Stocked** in your pantry, and the list is archived. Untick
    > anything you didn't actually buy first.

23. **[ShoppingListDetail.vue:284](web_app/src/pages/ShoppingListDetail.vue) — Calendar / "Plan which day" button**
    > Set the date you plan to shop this list. Helps Dora prioritise
    > which list is your "active" one this week, and drives
    > shop-day reminders if you have them on.

24. **[PriceHistoryPage.vue:150](web_app/src/pages/PriceHistoryPage.vue) — "currently X% above" chip**
    > You're paying more than your own usual price for this product,
    > based on prices you've logged. Not a comparison to the
    > all-time-low across all stores — it's personal.

25. **[PriceHistoryPage.vue:158-176](web_app/src/pages/PriceHistoryPage.vue) — Your usual / above usual chip**
    > **Usually** is the median of prices you've logged for this
    > item. **Above usual** means today's shelf price is
    > meaningfully higher than that median.

26. **[MyProductsPage.vue:76-79](web_app/src/pages/MyProductsPage.vue) — Select on-deal bulk button**
    > Selects every visible product that's currently on special —
    > a shortcut for bulk actions like adding all deals to your
    > primary list.

27. **[PriceEntry.vue:65-72](web_app/src/components/dora/PriceEntry.vue) — Add pack count (multipack) disclosure**
    > For multipacks (e.g. 4 × 125g yoghurt), open this and enter
    > the pack count so Dora computes the right per-unit price and
    > remembers the pack shape for next time.

28. **[PreferencesSettings.vue:104-105](web_app/src/pages/settings/PreferencesSettings.vue) — Always ask which list toggle**
    > When adding an item from anywhere in the app, always show the
    > list picker. Off = Dora remembers your last-used list per
    > tab and adds silently.

29. **[PreferencesSettings.vue:128-131](web_app/src/pages/settings/PreferencesSettings.vue) — Infer stock levels toggle**
    > Lets Dora guess your current stock level for items you
    > haven't checked lately, using purchase + cooking history.
    > Shown as **"Dora: ~Low"** next to the recorded level — never
    > overwrites it.

30. **[PreferencesSettings.vue:147-149](web_app/src/pages/settings/PreferencesSettings.vue) — Batch cooking style**
    > Cook once, eat several times. Dora tracks a pool of cooked
    > portions per recipe and warns when your meal plan asks for
    > more portions than you have.

31. **[NotificationsSettings.vue:47-48](web_app/src/pages/settings/NotificationsSettings.vue) — Compact format (deals email) toggle**
    > One line per deal (item, price, store). Off = expanded
    > card per deal with images and store logos.

32. **[AssistantSettings.vue:35-36](web_app/src/pages/settings/AssistantSettings.vue) — Tool-able requests in AI mode description**
    > Requests that need real actions on your data — for example
    > "add milk to my list" or "what's expiring?" — which the
    > assistant handles by calling app tools. **Basic mode** only
    > handles chat; **AI mode** unlocks these action requests.

---

## Execution recipe for the next session

1. **Open this file first**, then open the referenced source files in
   two-pane layout. Do NOT re-audit — the copy is drafted here.
2. **Line numbers may have drifted** by a few lines if unrelated commits
   have landed since 2026-07-06 — anchor by nearby label text (given
   above in bold), not line number alone.
3. **Skim each target for an existing `q-tooltip` on the same element
   first** — if one exists, either fold the new copy into it, or skip.
   Do NOT add a second tooltip to the same element.
4. **Batch by file** — open one file, do every chip in it, move on. There
   are 32 chips across ~15 files.
5. **Where the label is inside a chip / button component** (items 4, 8,
   9, 11, 14-17, 22, 24-27), the icon usually needs to sit in a
   *sibling* caption above/below the chip strip rather than inside the
   chip itself — chips already have hover interactions. When in doubt,
   put the `(?)` immediately after a section heading like
   "Filters" or "Shortfall" rather than on the chip. Judge on-site.
6. **Type check.** After each file, `vue-tsc` clean should pass — the
   changes are purely template-side.
7. **`vue-tsc` at the end of the batch** — no backend changes, no
   pytest run required.

## Close-gate for the batch

- **CHANGELOG.md** — under `[Unreleased]` → `### Added`, one bullet:
  *"Targeted (?) hover-help chips on 32 confusing controls across
  Dashboard, Reports, Alerts, Meal plans, Recipes, Stock, Shopping
  lists, Price history, and Settings (FU-044). Non-obvious metrics
  and Dora-specific terminology explained in-context without a
  toggle or overlay engine — a lightweight sibling to the Help page
  and assistant, not a replacement."*
- **DORA_FOLLOWUPS.md → DORA_FOLLOWUPS_RESOLVED.md** — move FU-044.
  Resolution note: *"Narrowed scope (2026-07-06). Instead of the
  opt-in help-overlay mechanism from `PROPOSAL_HELP_OVERLAY.md`,
  shipped 32 targeted `(?)` chips per
  `IMPL_PLAN_HELP_CHIPS.md`. Overlay mechanism +
  `v-help` directive + DoraBot fronting all parked as
  someday — help page + assistant remain the deep-help
  fallback."*
- **PROPOSAL_HELP_OVERLAY.md** — mark 📦 *superseded* in the document
  register (PROJECT_STATE.md), pointing at this impl plan + the
  resolved FU. Don't delete the file — it's the record of the
  parked design.
- **DORA_VERIFY.md** — append a section:
  *"Help chips (FU-044) — hover each chip listed in
  `IMPL_PLAN_HELP_CHIPS.md` and confirm the tooltip renders + reads
  correctly; check both desktop hover and mobile long-press."*
- **DORA_WORKLOG.md** — new entry at the top; list the 32
  chips-added-per-file counts, note the scope narrowing decision.
- **PROJECT_STATE.md** — hand-edit the "Recently shipped" section
  (one line) and the document register (mark PROPOSAL_HELP_OVERLAY
  📦 superseded, link this impl plan).

## Not for this batch (log if surfaced)

- If any control below appears *more* confusing in-app than the audit
  flagged, log an FU rather than expand scope now.
- If a control on the list turns out to already have a tooltip, note it
  in the worklog and skip; don't force a second one.
- **Do NOT** revive the `v-help` directive, "?" toolbar toggle, or
  overlay engine. Those are explicitly parked.
