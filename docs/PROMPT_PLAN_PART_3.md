# DiscountDora - Prompt Plan Part 3

This plan closes the gap between "feature-rich grocery system" and the original
DiscountDora vision:

> Dora should do what Grocy does, but way better: less manual work, less data
> ceremony, faster grocery actions, and more helpful automation. The app works
> for the user, not the other way around.

Part 1 made the app interconnected.
Part 2 made the app smarter.
Part 3 makes the app lighter.

This is the anti-Grocy plan. It is not about adding another layer of settings,
tables, forms, or reports. It is about protecting the product from becoming
tiring.

---

## How the Existing Plans Match the Vision

The good:

- Part 1 already pushes toward speed with QuickAddSheet, chips, bulk actions,
  inline expiry controls, one-click list generation, stocktake focus mode,
  global command palette, keyboard shortcuts, undo, and Dora quick-actions.
- Part 2 adds the right "assistant" signals: receipt import, purchase memory,
  forecasting, suggestion inbox, budget-aware lists, waste rescue, voice, and
  one-handed shopping.
- Both plans are strongest when they turn data into actions: "add missing",
  "cook this", "generate list", "use soon", "finish shopping", "undo".

The risk:

- Too many screens can make Dora feel like Grocy with nicer paint.
- Too many optional fields can make stock items feel like admin records.
- Too many graphs/reports/importers can make the app feel like a database.
- Some Part 2 features, especially receipts, household sharing, dietary profiles,
  budget optimization, and automation controls, could become complex if exposed
  as heavy configuration instead of simple workflows.
- "Explainability" can become more UI noise unless it appears only when useful.

The correction:

- Every feature needs a "fast path" first.
- Advanced detail must be progressive and mostly hidden.
- Data should be captured from natural actions, not demanded upfront.
- Dora should suggest, infer, remember, and clean up.
- Users should rarely have to maintain the system manually.

---

## Recommended Order

1. **Product guardrails first** - P3-01 -> P3-02
2. **Friction removal** - P3-03 -> P3-04 -> P3-05
3. **Hands-off data capture** - P3-06 -> P3-07 -> P3-08
4. **Simplified daily surface** - P3-09 -> P3-10
5. **Progressive disclosure** - P3-11 -> P3-12
6. **Automation calibration** - P3-13 -> P3-14
7. **Proof that Dora is easier** - P3-15 -> P3-16

---

## Cross-Cutting Rules

Every Part 3 prompt must enforce these rules:

- **No data for data's sake.** Every field must either drive an action, improve a
  suggestion, reduce future work, or be removed/hidden.
- **Fast path before full path.** The first visible path should solve the common
  case in seconds. Advanced detail belongs behind "More".
- **Capture from behavior.** Prefer learning from shopping, cooking, receipts,
  scans, voice, and list actions over asking users to fill forms.
- **One screen, one primary job.** Do not turn pages into dashboards of every
  possible relationship.
- **Dora should clean up after itself.** Suggestions, auto-added items, old
  alerts, duplicate products, stale data, and low-confidence matches need tidy
  flows.
- **Defaults matter more than settings.** Add settings only when users truly need
  persistent control.
- **Undo beats confirmation.** Use confirmation for destructive actions. Use undo
  for ordinary reversible actions.
- **Measure friction.** New flows must define target click/tap counts and time
  expectations.

---

# Tier P3-A - Product Guardrails

## P3-01 - Dora Product Constitution

```
Write a product constitution for DiscountDora and wire it into the repo so
future prompts and contributors protect the "easy grocery assistant" vision.

READ FIRST:
- PROMPT_PLAN.md.
- PROMPT_PLAN_PART_2.md.
- README.md and CONTRIBUTING.md if present.
- CHANGELOG.md to understand the current product direction.
- Any docs, roadmap, or feature board files in the repo.

CREATE:
1. docs/product/DORA_PRODUCT_CONSTITUTION.md

CONTENT:
1. One-paragraph product promise:
   - Dora is a grocery assistant, not an inventory accounting system.
   - The user should do less work over time, not more.
   - Data exists only when it makes actions faster, smarter, or safer.

2. The "Anti-Grocy" rules:
   - Avoid mandatory detail.
   - Avoid maintenance chores.
   - Avoid exposing database structure as UI.
   - Avoid forms where a quick action, scan, receipt, voice command, or default
     can do the job.
   - Avoid reports that do not produce a next action.

3. Feature acceptance questions:
   - Does this reduce user work?
   - Can the common case be done in under 10 seconds?
   - What data can Dora infer instead of asking for?
   - What happens if the user never configures this?
   - Is there an undo or recovery path?
   - Can this be hidden until needed?

4. Interaction targets:
   - Add common item to primary list: <= 2 taps or one natural-language command.
   - Mark item low/out/restocked: <= 2 taps.
   - Finish shopping: <= 1 main action plus optional review.
   - Generate useful list: <= 2 taps from dashboard or list page.
   - Correct Dora's wrong assumption: <= 2 taps.
   - Ignore/snooze noise: <= 1 tap.

5. Data policy:
   - Required fields should be minimal.
   - Optional fields must be hidden behind progressive disclosure.
   - Every stored field needs a named use.
   - Unknown is valid. Dora should degrade gracefully.

6. UI policy:
   - Primary action first.
   - Secondary actions grouped.
   - Advanced/admin flows tucked away.
   - Avoid dense tables for daily use.
   - Prefer chips, sheets, command palette, scan, voice, and inline actions.

WIRE INTO CONTRIBUTING:
- Add a "Product fit check" section to CONTRIBUTING.md if it exists.
- Add a PR checklist entry:
  "This change reduces user work or keeps advanced detail out of the daily path."

DEFINITION OF DONE:
- Constitution exists and is linked from README/CONTRIBUTING where appropriate.
- New product-fit checklist is present.
- CHANGELOG entry under [Unreleased].
```

## P3-02 - Feature Complexity Budget Audit

```
Audit existing and planned features against Dora's simplicity vision. Produce a
living complexity budget that identifies which features should be simplified,
hidden, deferred, or split into fast/advanced paths.

READ FIRST:
- PROMPT_PLAN.md.
- PROMPT_PLAN_PART_2.md.
- docs/product/DORA_PRODUCT_CONSTITUTION.md from P3-01.
- Current web_app/src/pages and major components.
- CHANGELOG.md.

CREATE:
1. docs/product/COMPLEXITY_BUDGET.md

AUDIT EACH MAJOR AREA:
- Pantry / Stock Overview
- Stock Item Detail
- Locations
- Shopping Lists
- Recipes
- Cook Mode
- Meal Plans
- Product Search / Saved Products
- Dashboard
- Alerts
- Dora Assistant
- Data Management
- Reports / Analytics
- Barcodes / QR
- Stocktake
- Receipts
- Forecasting
- Budget optimization
- Household sharing
- Automation controls

FOR EACH AREA, SCORE:
1. User value: low / medium / high
2. Manual effort required: low / medium / high
3. Daily-use visibility: daily / occasional / admin
4. Configuration burden: none / small / heavy
5. Risk of becoming Grocy-like: low / medium / high
6. Simplification recommendation:
   - Keep prominent
   - Keep but simplify
   - Hide under advanced
   - Make assistant-driven
   - Defer
   - Remove if unused

OUTPUT:
- A summary table.
- Top 10 friction risks.
- Top 10 simplification opportunities.
- Specific UI changes to reduce daily complexity.

DEFINITION OF DONE:
- Complexity budget exists.
- At least five concrete simplification tickets/prompts are generated from it.
- CHANGELOG entry under [Unreleased].
```

---

# Tier P3-B - Friction Removal

## P3-03 - Interaction Friction Audit and Tap Count Tests

```
Measure the real friction in Dora's most important flows and add regression
tests so future features do not make them slower.

READ FIRST:
- T1 E2E test suite.
- P2-16 Part 2 E2E tests, if present.
- Current routes for stock, lists, recipes, Dora chat, stocktake, scan, and
  dashboard.

DEFINE CRITICAL FLOWS:
1. Add common item to primary list.
2. Add a new stock item with only a name.
3. Mark item low/out/restocked.
4. Generate a shopping list from low/out essentials.
5. Add missing recipe ingredients to a list.
6. Finish shopping.
7. Correct an auto-added item.
8. Snooze or dismiss an alert.
9. Ask Dora to add multiple items.
10. Start shopping mode for the primary list.

BUILD:
1. tests/e2e/friction.spec.ts
   - Count user interactions where practical.
   - Measure elapsed time for deterministic flows.
   - Assert target thresholds from DORA_PRODUCT_CONSTITUTION.md.
2. A helper that logs:
   - Flow name
   - Click/tap count
   - Page transitions
   - Modals/sheets opened
   - Time to completion
3. docs/product/FRICTION_BASELINE.md
   - Current baseline table.
   - Notes on worst offenders.

TARGETS:
- Common add-to-list: <= 2 interactions after page is open.
- Mark level: <= 2 interactions.
- Dismiss alert: <= 1 interaction.
- Generate useful list: <= 2 interactions.
- Finish shopping: <= 2 interactions in the common case.

DEFINITION OF DONE:
- E2E friction tests exist for the critical flows.
- Baseline document exists.
- Any flow exceeding the target gets a TODO or follow-up prompt.
- CHANGELOG entry under [Unreleased].
```

## P3-04 - Fast Add Everywhere

```
Make adding grocery intent radically fast from anywhere in the app.

READ FIRST:
- QuickAddSheet from P0/P5.
- Dora natural-language add-to-list feature from CHANGELOG.md.
- Global command palette S1.
- PWA shortcut M1.
- Shopping list and stock item action composables.

BUILD:
1. A single FastAdd experience used by:
   - Header plus button.
   - Dashboard.
   - Primary shopping list.
   - Command palette.
   - Dora chat.
   - PWA shortcut.
   - Mobile bottom action if the app has one.

2. FastAdd input supports:
   - Plain item name: "milk"
   - Quantity: "2 milk"
   - Multiple items: "milk, eggs, bread"
   - Loose phrasing: "add milk and eggs"
   - Optional merchant/product match if obvious, but never required.

3. FastAdd behavior:
   - If item matches one stock item confidently, add to primary list.
   - If several match, show compact chips to choose.
   - If no match, offer:
     "Add as one-off list item" as the primary path.
     "Create tracked stock item" as the secondary path.
   - Do not force stock item creation for quick grocery intent.

4. One-off list items:
   - Add support for shopping list lines not yet linked to stock_items if this
     does not already exist.
   - They can be promoted to tracked stock items later.
   - They should not pollute pantry data by default.

5. Recent/common suggestions:
   - Opening FastAdd empty shows the user's most likely items.
   - One tap adds a suggestion.

UX DETAILS:
- The primary path is "put this on my list", not "complete a data model".
- Keep the sheet small and focused.
- Advanced product/deal selection is optional after the item is on the list.

DEFINITION OF DONE:
- User can add "milk, eggs, bread" to primary list from the header with minimal
  interactions.
- Unknown items can be added without creating stock records.
- The same FastAdd component powers every entry point.
- CHANGELOG entry under [Unreleased].
- E2E test covers known item, ambiguous item, unknown one-off item, and multiple
  item parse.
```

## P3-05 - One-Tap Corrections

```
Make it effortless to correct Dora without opening forms or detail pages.

READ FIRST:
- StockItemChip and ProductChip.
- Alerts Panel P13.
- Forecasting P2-03.
- Dora Suggestion Inbox P2-04.
- Automation controls P2-12.

BUILD:
1. A shared QuickCorrectionMenu component for stock items, list items, alerts,
   suggestions, and forecasts.

COMMON CORRECTIONS:
- "Not low"
- "Actually out"
- "Already bought"
- "Do not add this automatically"
- "Not this product"
- "Wrong match"
- "I do not use this often"
- "Snooze"
- "Hide this"
- "Undo"

BACKEND:
1. Add lightweight correction endpoints:
   - POST /api/corrections
   - Body includes entity type, entity id, correction kind, optional note.
2. Correction effects:
   - Update obvious state immediately where safe.
   - Feed forecasting/suggestion suppression.
   - Record an automation event/audit event.

FRONTEND:
1. Every auto-generated or suggested surface gets a small correction affordance.
2. Corrections should be one tap when possible.
3. More detailed correction opens a small sheet, not a full page.

UX DETAILS:
- Corrections should feel like teaching Dora, not filling a ticket.
- Use plain language: "Dora will remember this" where true.

DEFINITION OF DONE:
- User can correct a bad forecast, bad product match, or unwanted auto-add in
  under two interactions.
- Corrections suppress or improve future suggestions.
- CHANGELOG entry under [Unreleased].
- Tests cover correction persistence and suppression behavior.
```

---

# Tier P3-C - Hands-Off Data Capture

## P3-06 - Minimal Stock Item Model and Progressive Fields

```
Make stock item creation and editing feel lightweight. A stock item should be
valid with only a name.

READ FIRST:
- Stock item create/edit forms.
- Stock item backend schemas and validation.
- F6 Validation library.
- StockItemDetail tabs.
- Any required fields introduced by Part 1 or Part 2.

RULE:
The only required user-facing field for a stock item is name, unless the current
schema makes that impossible. Everything else must have a default, be inferred,
or be optional.

BACKEND:
1. Audit stock item schema required fields.
2. For each required field other than name:
   - Provide default.
   - Infer from context.
   - Or move to optional.
3. Add a "data_use" comment/documentation for optional fields:
   - level -> alerts/list generation
   - location -> finding/storage route
   - expiry -> waste rescue
   - product links -> deals
   - barcode -> scanning
   - substitute -> swap suggestions
   - etc.

FRONTEND:
1. Create Stock Item sheet:
   - Name field.
   - Optional quick chips: level, location.
   - Save button visible immediately.
   - "More details" expands advanced fields.
2. Edit form:
   - Daily fields first.
   - Advanced fields collapsed:
     products, barcode, nutrition, substitutes, custom settings, thresholds.
3. Empty/unknown states:
   - Unknown location is allowed.
   - Unknown level is allowed only if the domain supports it; otherwise default
     to "unknown" or a sensible neutral level.

UX DETAILS:
- Do not block saving because optional metadata is missing.
- Dora may later suggest filling useful missing data, but only when it unlocks a
  visible benefit.

DEFINITION OF DONE:
- A stock item can be created with name only.
- Advanced fields are hidden by default.
- Existing workflows still work with sparse stock items.
- CHANGELOG entry under [Unreleased].
- Tests cover creating minimal item and using it in a list.
```

## P3-07 - Smart Defaults and Inference Engine

```
Add a lightweight inference layer so Dora fills sensible defaults instead of
asking the user.

READ FIRST:
- Stock item model and forms.
- Shopping list history.
- Purchase memory P2-02.
- Locations hierarchy.
- Product matching.
- Existing settings/defaults.

BUILD:
1. dora_api inference service:
   - infer_stock_group(name, product_match)
   - infer_location(name, past_items, household defaults)
   - infer_is_essential(name, purchase frequency)
   - infer_restock_cadence(item history)
   - infer_preferred_merchant(item/product history)
   - infer_expiry_window(name/category) only if a safe generic mapping exists

2. Inference response shape:
   {
     "value": any,
     "confidence": "low" | "medium" | "high",
     "reason": str,
     "source": "history" | "similar_item" | "category_default" | "user_default"
   }

3. Frontend usage:
   - Pre-fill low-risk fields.
   - Show subtle "Dora guessed" indicator for medium-confidence fields.
   - Require user confirmation for high-impact fields.

4. Feedback:
   - If user changes an inferred value, record correction.
   - Future inference should learn from that correction.

UX DETAILS:
- Avoid making users approve every guess.
- Do not show inference machinery unless the user changes or inspects it.
- Wrong guesses must be easy to fix.

DEFINITION OF DONE:
- Creating a common item pre-fills useful defaults.
- User corrections improve future guesses.
- Sparse data still works.
- CHANGELOG entry under [Unreleased].
- Tests cover inference from history and correction feedback.
```

## P3-08 - Stale Data Cleanup and Gentle Housekeeping

```
Dora should maintain its own data hygiene instead of making users manually clean
up stale, duplicate, or low-value records.

READ FIRST:
- Stock items, products, saved products, shopping lists, recipes, alerts.
- Audit log and automation events.
- Suggestion Inbox P2-04.
- Data Management N1-N5.

BACKEND:
1. Add housekeeping service:
   - duplicate stock item candidates
   - unused one-off list items
   - inactive saved products
   - stale product links
   - expired alerts
   - empty archived lists
   - old suggestions
2. GET /api/housekeeping/suggestions
3. POST /api/housekeeping/actions/<id>/accept
4. POST /api/housekeeping/actions/<id>/dismiss

FRONTEND:
1. Do not create a big scary maintenance page for daily use.
2. Show a small "Tidy up" card only when there are useful, low-risk suggestions.
3. Tidy suggestions:
   - Merge duplicate items
   - Archive old empty list
   - Remove dead product link
   - Clear old dismissed alerts
4. Each suggestion has:
   - Plain explanation
   - Preview
   - Accept
   - Dismiss
   - Undo if possible

UX DETAILS:
- Housekeeping should never nag.
- It should feel like Dora offering to clean up, not assigning chores.

DEFINITION OF DONE:
- Dora identifies at least three kinds of stale/duplicate data.
- User can accept cleanup with preview and undo.
- CHANGELOG entry under [Unreleased].
- Tests cover duplicate detection and safe cleanup.
```

---

# Tier P3-D - Simplified Daily Surface

## P3-09 - Today Page: The Only Daily Dashboard

```
Create a simplified Today page that becomes the user's daily grocery assistant
surface. It should answer: what needs attention, what can I do quickly, and what
can Dora handle for me?

READ FIRST:
- Dashboard P12.
- Alerts P13.
- Dora Suggestion Inbox P2-04.
- Forecasting P2-03.
- Waste Rescue P2-06.
- Shopping Lists Overview P4.
- Recipes Overview P6.

NEW ROUTE:
- /today

CONTENT:
1. Primary action row:
   - Fast Add
   - Open primary list
   - Generate list
   - Scan
2. Dora summary:
   - One short sentence.
   - Example: "You have 4 things worth dealing with today."
3. Action cards, max 5 by default:
   - Primary shopping list
   - Use soon
   - Likely needed soon
   - Best useful deals
   - Cookable tonight
   - Stocktake overdue
4. Each card must have:
   - One primary action.
   - One dismiss/snooze action if applicable.
   - No dense table.
5. "Show more" reveals secondary cards.

BACKEND:
1. GET /api/today
   - Aggregates only the most actionable items.
   - Applies user suppression/snooze preferences.
   - Returns prioritized cards with action payloads.

UX DETAILS:
- Today is not Reports.
- Today is not every metric.
- Today should feel finishable.
- If there is nothing important, show a calm "You're in good shape" state with
  Fast Add and primary list still available.

DEFINITION OF DONE:
- /today gives a concise, action-first view.
- No more than five attention cards appear by default.
- Every card has a next action.
- CHANGELOG entry under [Unreleased].
- E2E test covers the "daily glance -> action -> done" loop.
```

## P3-10 - Navigation Simplification and Advanced Area

```
Simplify the app navigation so daily grocery work is prominent and advanced
database/admin tools are tucked away.

READ FIRST:
- Current layouts/nav menu.
- SettingsShell.
- Data Management N1.
- Reports N6.
- Substitutes Graph N7.
- Price History N8.
- Stock Map N9.
- Automation controls P2-12.
- Today page P3-09.

DESIGN:
Primary nav should favor daily actions:
- Today
- Pantry
- List
- Recipes
- Dora

Secondary/advanced area should contain:
- Data Management
- Reports
- Price History
- Substitutes Graph
- Stock Map
- Automation
- Admin/System settings

BUILD:
1. Update nav layout with primary and advanced grouping.
2. Add a user setting:
   - "Show advanced tools in main navigation" default false.
3. Command palette can still find advanced tools.
4. Existing deep links must still work.
5. If a user visits an advanced tool directly, do not hide functionality.

UX DETAILS:
- Avoid making the app look smaller by removing power. Make power available but
  out of the daily path.
- Use plain labels: "Pantry", "List", "Today".

DEFINITION OF DONE:
- Daily nav is shorter and clearer.
- Advanced tools are accessible but not visually dominant.
- CHANGELOG entry under [Unreleased].
- E2E smoke test covers primary nav and command palette access to advanced.
```

---

# Tier P3-E - Progressive Disclosure

## P3-11 - Detail Page Diet

```
Reduce cognitive load on detail pages by making them action-first and hiding
rarely used data until needed.

READ FIRST:
- StockItemDetailPage.
- Recipe Detail/Edit.
- Product detail or ProductCard flows.
- ShoppingListDetail.
- Complexity budget P3-02.

FOR EACH DETAIL PAGE:
1. Identify the top 3 user intents.
2. Make those intents visible above the fold.
3. Move secondary relationships into collapsed sections or tabs.
4. Move admin/raw metadata into "More details".
5. Remove or hide fields that do not drive actions.

STOCK ITEM DETAIL DEFAULT VIEW:
- Name, level, location, expiry if present.
- Primary actions:
  - Add to list
  - Mark restocked / mark low / mark out
  - Find deals
- Secondary collapsed:
  - Recipes
  - Products
  - Substitutes
  - History
  - Advanced settings

RECIPE DETAIL DEFAULT VIEW:
- Cook / Add missing to list / Plan meal.
- Ingredients and steps.
- Metadata hidden unless editing.

SHOPPING LIST DETAIL DEFAULT VIEW:
- Items and finish flow.
- Totals visible but not overwhelming.
- Deal/merchant details available inline, not dominant.

DEFINITION OF DONE:
- Detail pages feel shorter on first load.
- Primary actions are easier to find.
- Advanced data remains available.
- CHANGELOG entry under [Unreleased].
- Visual regression screenshots for desktop/mobile.
```

## P3-12 - Forms to Sheets, Sheets to Inline Actions

```
Replace heavy form-driven flows with sheets and inline actions where the task is
small and reversible.

READ FIRST:
- All create/edit pages and dialogs.
- QuickAddSheet.
- Notify/Confirm primitives F4.
- Undo system F5.

AUDIT FLOWS:
- Create stock item
- Edit stock level
- Set expiry
- Move location
- Add substitute
- Add product link
- Add recipe ingredient
- Add list item
- Add meal plan entry
- Log waste
- Add leftover

BUILD:
1. For small actions, use inline controls or bottom sheets.
2. Keep full-page forms only for genuinely complex editing.
3. Add autosave or save-on-action where safe.
4. Use undo for reversible actions.
5. Use confirmation only for destructive or hard-to-reverse actions.

UX DETAILS:
- Sheets should have one clear primary action.
- Do not require users to navigate away for tiny changes.
- Mobile bottom sheets should be thumb-friendly.

DEFINITION OF DONE:
- At least five heavy flows are converted to sheet/inline interactions.
- No regression in validation or accessibility.
- CHANGELOG entry under [Unreleased].
- E2E tests cover converted flows.
```

---

# Tier P3-F - Automation Calibration

## P3-13 - Automation Noise Throttle

```
Prevent Dora from becoming noisy as alerts, forecasts, suggestions, waste rescue,
budget warnings, and housekeeping all come online.

READ FIRST:
- Alerts Panel P13.
- Dora Suggestion Inbox P2-04.
- Automation controls P2-12.
- Forecasting P2-03.
- Waste Rescue P2-06.
- Housekeeping P3-08.

BACKEND:
1. Add notification/suggestion priority service.
2. Inputs:
   - severity
   - user interaction history
   - snooze/dismiss history
   - item essential status
   - expiry/run-out timing
   - confidence
3. Output:
   - show_now bool
   - channel ("today" | "alert" | "suggestion_inbox" | "silent")
   - priority score
   - reason
4. Hard caps:
   - Today page max active attention cards.
   - Alerts panel groups low-priority items.
   - Dora chat does not proactively interrupt unless user opened it.

FRONTEND:
1. Group low-priority noise.
2. Add "quiet this type" action.
3. Add "show fewer like this" correction.

DEFINITION OF DONE:
- Multiple suggestion sources do not flood Dashboard/Today.
- Dismissed low-value suggestions stay quiet.
- CHANGELOG entry under [Unreleased].
- Tests cover priority, caps, and suppression.
```

## P3-14 - Assistant Autopilot Levels

```
Make Dora's hands-off behavior user-friendly by defining simple autopilot levels
instead of dozens of separate automation settings.

READ FIRST:
- Automation controls P2-12.
- Dora Suggestion Inbox P2-04.
- Auto-add on low X5.
- Forecasting P2-03.
- Budget-aware lists P2-05.

AUTOPILOT LEVELS:
1. Manual:
   - Dora suggests nothing unless asked.
   - No auto-add.
2. Assist:
   - Dora shows suggestions.
   - User approves before changes.
   - Default for new users.
3. Proactive:
   - Dora can auto-add low-risk items with undo.
   - Still asks before budget, deletion, merge, or household-impacting changes.
4. Quiet:
   - Dora only surfaces urgent/essential alerts.

BACKEND:
1. Add user/household assistant_mode.
2. Map detailed automation preferences to assistant_mode defaults.
3. Existing detailed preferences remain available under Advanced.

FRONTEND:
1. Settings > Dora:
   - Simple mode selector with plain descriptions.
2. Onboarding:
   - Ask one question: "How hands-on should Dora be?"
3. Suggestion/automation UI:
   - Respect mode.
   - Offer "make Dora more/less proactive" after repeated accepts/dismissals.

DEFINITION OF DONE:
- Users can control Dora with one simple mode.
- Advanced automation settings still exist but are not required.
- CHANGELOG entry under [Unreleased].
- Tests cover mode behavior for suggestion and auto-add flows.
```

---

# Tier P3-G - Proof Dora Is Easier

## P3-15 - Grocy Migration, Dora Simplification

```
When importing from Grocy, do not recreate Grocy's complexity by default.
Convert detailed Grocy data into a simpler Dora experience.

READ FIRST:
- N3 Import (Grocy + spreadsheet).
- P3-01 Product Constitution.
- P3-06 Minimal Stock Item Model.
- Existing Grocy import code if present.

BUILD:
1. Grocy import preview gains "Dora simplified import" default mode.
2. Mapping strategy:
   - Import core item names, quantities/levels, locations, expiry where useful.
   - Preserve detailed Grocy fields in raw import metadata only if needed.
   - Do not surface every Grocy field in daily UI.
   - Convert Grocy chores/tasks into Dora suggestions only when actionable.
3. Advanced mode:
   - Lets power users inspect and choose extra fields.
   - Hidden behind "Advanced import options".

FRONTEND:
1. Import preview explains:
   - "Dora will keep the useful grocery data and leave behind fields that do not
     help day-to-day shopping."
2. Show before/after counts:
   - Items imported
   - Locations simplified
   - Fields preserved as metadata
   - Fields ignored
3. Let user download ignored-field report.

DEFINITION OF DONE:
- Grocy import defaults to a simpler Dora-shaped model.
- Advanced details are not dumped into daily UI.
- CHANGELOG entry under [Unreleased].
- Tests cover simplified import and metadata preservation.
```

## P3-16 - Dora Ease Score and Release Gate

```
Add an internal release gate that checks whether Dora is becoming easier or more
tiring.

READ FIRST:
- Friction baseline P3-03.
- Complexity budget P3-02.
- E2E tests T1 and P2-16.
- CI pipeline D4.

CREATE:
1. scripts/dora_ease_score.*
   - Language should match repo conventions.
2. docs/product/DORA_EASE_SCORE.md

METRICS:
1. Critical flow tap counts from friction tests.
2. Number of visible primary nav items.
3. Number of required fields in common create forms.
4. Count of alerts/suggestions shown on Today by default.
5. Number of daily-use pages with dense tables.
6. Number of settings visible outside Advanced.
7. E2E pass/fail for fast paths.

OUTPUT:
- Score 0-100.
- Red/yellow/green status.
- Regressions since previous baseline.
- Suggestions:
  - "Move X to Advanced"
  - "Reduce required fields"
  - "Add fast path"
  - "Group noisy alerts"

CI:
- Run ease score on PR.
- Do not fail initially; publish as artifact/comment.
- Once stable, fail only on large regressions in critical flows.

DEFINITION OF DONE:
- Ease score can be generated locally.
- CI publishes it.
- A PR that adds required fields or increases fast-path interactions is flagged.
- CHANGELOG entry under [Unreleased].
```

---

# Deferred Unless They Reduce Work

These ideas should not be built unless they clearly reduce user effort:

- More analytics dashboards.
- More item metadata fields.
- Complex nutrition tracking.
- Detailed chore/task systems.
- Manual store aisle editors for every user.
- Deep admin tables for normal household users.
- Complex rule builders for automation.
- Any feature whose primary value is "now we store more data."

If one of these is built, it must have a fast default, an assistant-driven path,
and a visible user benefit.

---

# Notes

The north star is not "Dora has every feature Grocy has."

The north star is:

- Dora remembers what matters.
- Dora asks less over time.
- Dora fixes common grocery problems quickly.
- Dora keeps advanced power out of the daily path.
- Dora lets users correct it without punishment.
- Dora turns data into action, then gets out of the way.

If Part 1 and Part 2 are about capability, Part 3 is about restraint. This is
the layer that keeps DiscountDora from becoming the very thing it was meant to
replace.
