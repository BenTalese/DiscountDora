# DiscountDora - Prompt Plan Part 2

A second wave of paste-ready prompts for turning DiscountDora from a rich pantry
and shopping app into a genuinely intelligent household grocery system.

Part 1 focused on the core loops: stock, lists, recipes, deals, data management,
resilience, design system, documentation, DevOps, and tests.

Part 2 focuses on the next layer of end-user value:

- closing the loop between planned shopping and real purchases
- predicting what the household will need next
- preventing waste before it happens
- making automation trustworthy and explainable
- supporting real households, routines, budgets, dietary needs, and in-store use

Each prompt is self-contained. A fresh AI coding session can run it cold. Every
prompt starts with a READ FIRST step so it survives stale-code drift.

---

## How to Use

- Run Part 1 prompts first where dependencies are called out.
- Do not run prompts in parallel when they touch the same tables, stores, routes,
  or shared composables.
- After each prompt lands, read CHANGELOG.md and update the next prompt if the
  code has drifted.
- These prompts assume the project is still pre-release unless CHANGELOG.md says
  otherwise. If the schema has become user-facing and migration safety matters,
  stop and adapt before destructive changes.

---

## Recommended Order

1. **Close the purchase loop** - P2-01 -> P2-02
2. **Prediction and automation** - P2-03 -> P2-04 -> P2-05
3. **Waste reduction and meal intelligence** - P2-06 -> P2-07 -> P2-08
4. **Household and collaboration** - P2-09
5. **Shopping experience upgrades** - P2-10 -> P2-11
6. **Trust, explanation, and user control** - P2-12
7. **Voice and ambient UX** - P2-13
8. **Advanced imports and sharing** - P2-14 -> P2-15
9. **Final polish and E2E coverage** - P2-16

---

## Cross-Cutting Rules

Apply these to every Part 2 prompt:

- **Every automatic action must be explainable.** The user should be able to see
  why Dora suggested, added, ranked, or warned about something.
- **Automation should prefer preview -> approve -> commit.** Silent changes need
  undo and a clear notification.
- **Real-world shopping data beats intent.** Receipts, actual prices, skipped
  items, and bought quantities should feed future suggestions.
- **Do not invent facts.** AI features must use tool calls or explicit app data.
- **Every new insight should lead to an action.** If the app says something will
  expire, run out, cost more, or break the budget, give the user a one-click next
  step.
- **Preserve household trust.** Shared actions need attribution, undo, audit
  history, and conflict handling.
- **Respect privacy by default.** Local-first and bring-your-own integrations are
  preferred. Anything external must be opt-in and documented.

---

# Tier P2-A - Close the Purchase Loop

## P2-01 - Receipt Import and Purchase Reconciliation

```
Build receipt import for DiscountDora so users can turn real shopping receipts
into stock updates, price history, and better future recommendations.

READ FIRST:
- PROMPT_PLAN.md, especially P5 Shopping List Detail, N3 Import, N8 Price History,
  X5 Auto-generated shopping lists, and I1+I2 Audit log.
- web_app/src/pages/ShoppingListDetail.vue and the finish-shopping flow.
- dora_api shopping list, product, stock item, saved product, and price history
  models.
- merchant_api price snapshot storage, if present.
- Existing image upload/file handling patterns, if any.
- CHANGELOG.md for current version and style.

DATA MODEL:
1. Add purchase_receipts:
   - id, user_id, source ("upload" | "manual" | "email" | "share_target")
   - merchant_name, purchased_at, subtotal, total, tax, raw_text, image_path
   - status ("uploaded" | "parsed" | "reconciled" | "needs_review")
   - created_at, updated_at
2. Add purchase_receipt_lines:
   - id, receipt_id, raw_name, normalized_name, quantity, unit, unit_price,
     line_total, matched_product_id, matched_stock_item_id, confidence,
     reconciliation_status ("pending" | "accepted" | "ignored" | "split")
3. Add shopping_list_items.actual_price and actual_quantity if not already
   present. Planned price and actual price must be separate.
4. Add product_price_observations if merchant price history cannot already store
   user-observed receipt prices.

BACKEND:
1. POST /api/receipts/upload
   - Auth required.
   - Accepts image or PDF.
   - Stores the file safely under DATA_DIR/uploads/receipts.
   - Extracts text using the lightest available local OCR/PDF path. If no OCR
     dependency exists, implement a pluggable parser interface and support
     manual text paste first.
   - Returns receipt payload with parsed line candidates.

2. POST /api/receipts/parse-text
   - Body: { "merchant_name"?: str, "purchased_at"?: iso, "text": str }
   - Parses pasted receipt text into line candidates.
   - Useful as a fallback when OCR is unavailable.

3. POST /api/receipts/<id>/match
   - Runs matching against known products and stock items.
   - Returns each line with match candidates:
     { stock_item, product, confidence, reason }
   - Reasons should be readable: exact barcode, saved product alias, fuzzy name,
     merchant product match, historical receipt match.

4. POST /api/receipts/<id>/reconcile
   - Body:
     {
       "lines": [
         {
           "line_id": uuid,
           "action": "accept" | "ignore" | "split",
           "stock_item_id"?: uuid,
           "product_id"?: uuid,
           "quantity"?: number,
           "stock_level_after"?: str,
           "shopping_list_item_id"?: uuid
         }
       ]
     }
   - Transactional.
   - Accepted lines can:
     - update stock levels
     - mark matching shopping list items as picked
     - store actual prices
     - create price observations
     - improve frequent-item stats
   - Returns a summary of stock updates, list updates, price observations, and
     ignored lines.

FRONTEND:
1. New route /receipts.
2. Receipts page:
   - Upload card: image/PDF picker plus "Paste receipt text" fallback.
   - Recent receipts list with status chips.
   - Empty state links to Shopping Lists and explains that receipts improve
     stock and savings accuracy.
3. Receipt review page:
   - Left pane: receipt image or raw text.
   - Right pane: parsed lines table.
   - Each line shows raw name, quantity, price, match confidence, and candidate
     chips.
   - Inline actions: accept match, choose another stock item, create stock item,
     split line, ignore.
   - "Reconcile all high-confidence matches" button.
   - Confirmation dialog before applying stock/list/price updates.
4. ShoppingListDetail integration:
   - Add toolbar action "Reconcile from receipt".
   - When launched from a list, matching should prefer items on that list.
5. Dora integration:
   - "I bought these" accepts pasted receipt text.
   - Dora opens the receipt review flow rather than silently mutating data.

UX DETAILS:
- Never auto-commit OCR results. Always preview first.
- Confidence below a chosen threshold must require manual acceptance.
- Show what will change before commit: stock level, list ticked state, actual
  price, and product link.
- If OCR is not available locally, the feature still works with pasted text and
  manual line entry.

DEFINITION OF DONE:
- A user can paste receipt text, match lines, reconcile to a shopping list, and
  see stock levels and actual prices update.
- Reconciliation creates price observations for matched products.
- Re-importing the same receipt warns about possible duplicate purchase.
- CHANGELOG entry under [Unreleased].
- Backend tests cover parsing, matching confidence, reconciliation transaction,
  and duplicate receipt detection.

STOP AND ASK before coding if adding OCR dependencies would be heavy or
platform-fragile. Implement manual/pasted receipt text first if needed.
```

## P2-02 - Purchase Memory and Actual Price Intelligence

```
Turn historical purchases into a first-class signal for better lists, prices,
budgets, and Dora recommendations.

READ FIRST:
- P2-01 Receipt Import, if implemented.
- Shopping list finish flow and archived list models.
- Reports / Analytics prompt N6.
- Price History Explorer prompt N8.
- QuickAddSheet and frequently-added suggestions.

DATA MODEL:
1. Ensure each completed shopping list item can store:
   - planned_quantity, actual_quantity
   - planned_offer_price, actual_unit_price, actual_total_price
   - planned_merchant, actual_merchant
   - skipped_reason nullable
   - purchased_at
2. Add stock_item_purchase_stats materialized view or query helper:
   - average_days_between_purchase
   - average_quantity
   - last_purchased_at
   - usual_merchant
   - usual_price
   - price_volatility

BACKEND:
1. GET /api/purchase-memory/stock-items/<id>
   - Returns purchase history, usual cadence, usual price, and merchant pattern.
2. GET /api/purchase-memory/suggestions
   - Returns items likely due soon based on purchase cadence and current stock.
3. POST /api/shopping-list-items/<id>/skip
   - Body: { "reason": "too_expensive" | "not_needed" | "out_of_stock_store" |
             "bought_elsewhere" | "other", "note"?: str }
   - Captures why planned purchases did not happen.
4. Update auto-generation and QuickAdd suggestions to consider purchase memory,
   not just raw list frequency.

FRONTEND:
1. StockItemDetail gains a "Purchase Memory" section:
   - Last bought
   - Usual cadence
   - Usual merchant
   - Typical price range
   - Recent skipped reasons
2. ShoppingListDetail:
   - Unticked items during finish-shopping can be marked with a skip reason.
   - If an item is much pricier than usual, show a small warning chip.
3. Reports:
   - "Often skipped" card.
   - "Price above usual" card.
4. Dora:
   - Can answer "what do I usually pay for coffee?"
   - Can answer "what did I skip last shop?"

DEFINITION OF DONE:
- Actual purchased prices and skipped reasons are captured.
- Frequently-added suggestions become purchase-memory suggestions.
- Stock item detail explains buying patterns in plain language.
- CHANGELOG entry under [Unreleased].
- Tests cover cadence calculation and skipped item capture.
```

---

# Tier P2-B - Prediction and Automation

## P2-03 - Consumption Forecasting and Run-Out Prediction

```
Add consumption forecasting so Dora can predict what the household will need
before it becomes low or out.

READ FIRST:
- Stock item level model and history/timeline from P2 Stock Item Detail.
- Purchase memory from P2-02, if implemented.
- X1 Stocktake and X5 Auto-generated shopping lists.
- Alerts panel P13.

DATA MODEL:
1. Add stock_item_usage_events:
   - id, user_id, stock_item_id, event_type ("level_change" | "cook" |
     "stocktake" | "receipt" | "manual_use"), quantity_delta nullable,
     level_before, level_after, occurred_at, source_id nullable
2. Ensure recipe cook mode and shopping finish flows write usage events.

BACKEND:
1. Build a forecasting service:
   - Inputs: usage events, purchase cadence, current level, item category,
     household size if available.
   - Output per item:
     {
       "estimated_run_out_at": iso|null,
       "confidence": "low" | "medium" | "high",
       "reason": str,
       "recommended_action": "watch" | "add_to_list" | "buy_soon" | "none"
     }
   - Start with deterministic heuristics. Do not use an LLM for the core math.
2. GET /api/forecasts/stock-items
   - Supports filters: due_within_days, confidence, essentials_only.
3. GET /api/stock-items/<id>/forecast
   - Returns detailed reasoning and input history.
4. Alerts integration:
   - Optional "likely to run out soon" alert type.
   - User setting controls whether forecast alerts are shown.

FRONTEND:
1. Dashboard card: "Likely needed soon".
2. StockOverview filter: "Running out soon".
3. StockItemDetail Forecast section:
   - Expected run-out date
   - Confidence
   - Plain-English reason
   - "Add to list" and "Ignore for now"
4. Shopping list auto-generation:
   - New source toggle "Predicted to run out soon".
5. Dora:
   - Can answer "what will I need this week?"
   - Must include why each item is suggested.

UX DETAILS:
- Show low confidence honestly.
- Let users dismiss a forecast for an item for a configurable period.
- A wrong forecast should be correctable: "I don't use this often" adjusts or
  excludes the item from forecasting.

DEFINITION OF DONE:
- Forecasts appear for items with enough history.
- Forecast source can generate a shopping list.
- Dora explains each predicted need without hallucinating.
- CHANGELOG entry under [Unreleased].
- Tests cover simple cadence prediction, sparse-history fallback, and dismissed
  forecast suppression.
```

## P2-04 - Dora Suggestion Inbox

```
Create a suggestion inbox where Dora proposes useful actions without silently
changing the user's household data.

READ FIRST:
- Dora assistant P14 and current LLM/tool-calling implementation.
- Alerts Panel P13.
- Undo system F5.
- Forecasting P2-03, Waste Rescue P2-06, Budget-Aware Lists P2-05.
- Audit log I1+I2.

DATA MODEL:
1. Add dora_suggestions:
   - id, user_id, household_id nullable
   - kind ("add_to_list" | "cook_recipe" | "use_expiring" | "budget_swap" |
     "stocktake" | "price_alert" | "waste_warning" | "household_conflict")
   - title, body, confidence, reason_json
   - proposed_action_json
   - status ("new" | "accepted" | "dismissed" | "snoozed" | "expired")
   - expires_at, snoozed_until, created_at, acted_at
2. Store reasons as structured JSON so the UI can render "because..." lines.

BACKEND:
1. GET /api/dora/suggestions
   - Returns current suggestions grouped by kind/severity.
2. POST /api/dora/suggestions/generate
   - Runs deterministic suggestion generators:
     - forecasted run-outs
     - expiring items
     - budget risks
     - unusually expensive products
     - stocktake overdue
     - meal ideas using expiring stock
   - LLM may summarize, but generators decide facts and actions.
3. POST /api/dora/suggestions/<id>/accept
   - Executes proposed_action_json through existing composables/services.
   - Returns undo token where possible.
4. POST /api/dora/suggestions/<id>/dismiss
5. POST /api/dora/suggestions/<id>/snooze

FRONTEND:
1. New route /dora/inbox.
2. Dashboard card: "Dora suggests".
3. Suggestion cards:
   - Title
   - Plain reason
   - Affected chips
   - Confidence
   - Accept, snooze, dismiss
   - "Why?" expandable detail
4. Dora chat:
   - "Review suggestions" opens the inbox.
   - Dora can answer questions about a suggestion using reason_json.

UX DETAILS:
- Avoid noisy suggestions. Default max 5 active suggestions on Dashboard.
- Dismissed suggestions should not immediately regenerate unchanged.
- Accepting a suggestion must show exactly what happened.

DEFINITION OF DONE:
- Suggestions are generated from real app data.
- Accepting a suggestion performs the action and logs it.
- Dismissing/snoozing suppresses repeats.
- CHANGELOG entry under [Unreleased].
- Tests cover generation dedupe, accept action execution, snooze suppression.
```

## P2-05 - Budget-Aware Auto Lists

```
Upgrade auto-generated shopping lists so they can optimize for a user's budget,
not just collect missing items.

READ FIRST:
- X5 Auto-generated shopping lists.
- Reports N6 and Price History N8.
- Purchase memory P2-02.
- Merchant/product offer models.

DATA MODEL:
1. Add user_budget_settings:
   - weekly_grocery_budget nullable
   - monthly_grocery_budget nullable
   - savings_priority ("lowest_total" | "fewest_stores" | "preferred_store" |
     "balanced")
   - max_store_count
   - preferred_merchants array/json
2. Add shopping_lists.budget_target nullable and budget_strategy nullable.

BACKEND:
1. POST /api/shopping-lists/optimize
   - Body:
     {
       "candidate_items": [stock_item_id],
       "budget_target": number|null,
       "strategy": "lowest_total" | "fewest_stores" | "preferred_store" |
                   "balanced",
       "max_store_count": number|null,
       "must_include": [stock_item_id],
       "nice_to_have": [stock_item_id]
     }
   - Returns:
     - selected items
     - deferred items with reasons
     - merchant assignment
     - estimated total
     - estimated savings
     - warnings
2. Integrate optimizer into /api/shopping-lists/auto-generate.
3. Add explainability:
   - "Deferred because it would exceed budget"
   - "Swapped merchant because same item is cheaper"
   - "Kept preferred merchant because savings were small"

FRONTEND:
1. Auto-generate modal gains:
   - Budget target input
   - Strategy segmented control
   - Max stores selector
   - Preview split: included vs deferred
2. ShoppingListDetail:
   - Budget strip: target, estimated total, remaining headroom.
   - "Re-optimize" action when prices change.
3. Settings:
   - Budget defaults and shopping strategy.
4. Dora:
   - "Build me a $120 shop"
   - "Can I keep this under $80?"
   - "What should I drop?"

UX DETAILS:
- Essentials should not be dropped without clearly saying so.
- If the budget is impossible, show the minimum viable total.
- Do not overfit to tiny savings if it creates extra store trips.

DEFINITION OF DONE:
- User can generate a list under a budget with included/deferred items.
- Dora can explain what was dropped and why.
- CHANGELOG entry under [Unreleased].
- Tests cover budget selection, must-include behavior, max-store constraint.
```

---

# Tier P2-C - Waste Reduction and Meal Intelligence

## P2-06 - Expiry Rescue and Food Waste Prevention

```
Turn expiry tracking into proactive waste prevention.

READ FIRST:
- Expiry controls in StockOverview and StockItemDetail.
- Recipes Overview P6, Recipe Detail P7, Cook Mode P8, Meal Plans P9.
- Alerts Panel P13.
- Reports N6.

DATA MODEL:
1. Add stock_item_waste_events:
   - id, user_id, stock_item_id, quantity nullable, reason
     ("expired" | "spoiled" | "did_not_like" | "overbought" | "other"),
     estimated_value nullable, occurred_at, note
2. Add stock_items.opened_at if not already present.
3. Add stock_items.shelf_life_days_after_open nullable.

BACKEND:
1. GET /api/waste/rescue
   - Returns items expiring soon or opened too long.
   - Includes recipes that use them, missing companion ingredients, and
     estimated value at risk.
2. POST /api/waste/events
   - Logs discarded/wasted item.
   - Optionally lowers stock level to out.
3. GET /api/waste/insights
   - Waste frequency by item/group.
   - "Buy smaller next time" candidates.
   - Estimated value wasted.
4. Suggestion Inbox integration:
   - Generates "Use this soon" suggestions.

FRONTEND:
1. Dashboard card: "Use soon".
2. New route /waste or Reports section "Waste".
3. Expiry Rescue page:
   - Items expiring soon as stock chips.
   - Recipe suggestions ranked by how many expiring items they use.
   - "Add missing companions to list".
   - "I used this", "Freeze it", "Log as wasted".
4. StockItemDetail:
   - Opened date and shelf-life-after-open controls.
   - Waste history.
5. Dora:
   - "What should I use before it expires?"
   - "What am I wasting often?"

UX DETAILS:
- Avoid shame-heavy wording. Use practical, calm language.
- Waste logging should be fast: one tap plus optional detail.
- Freezing an item should extend or clear expiry with an audit trail.

DEFINITION OF DONE:
- Expiring items produce rescue suggestions and recipe actions.
- Users can log waste and see insights.
- CHANGELOG entry under [Unreleased].
- Tests cover rescue ranking and waste event effects.
```

## P2-07 - Leftovers Mode

```
Add leftovers as a first-class concept connected to cook mode, expiry rescue,
and meal planning.

READ FIRST:
- Cook Mode P8.
- Meals and Meal Plans P9.
- Stock item expiry/opened fields.
- Waste prevention P2-06.

DATA MODEL:
1. Add leftovers:
   - id, user_id, recipe_id nullable, meal_id nullable, name, servings,
     stored_location_id nullable, created_at, eat_by_at nullable,
     frozen_at nullable, status ("available" | "eaten" | "frozen" | "wasted")
2. Add leftover_events:
   - id, leftover_id, event_type, servings_delta, occurred_at, note

BACKEND:
1. POST /api/leftovers
2. GET /api/leftovers?status=available|frozen|all
3. PATCH /api/leftovers/<id>
4. POST /api/leftovers/<id>/eat
5. POST /api/leftovers/<id>/freeze
6. POST /api/leftovers/<id>/waste
7. Meal planning integration:
   - Leftovers can be planned as a meal slot.

FRONTEND:
1. Cook Mode finish prompt:
   - "Any leftovers?"
   - Servings stepper
   - Eat-by date suggestion
   - Storage location
2. Dashboard card: "Leftovers".
3. Meal planner:
   - Drag leftovers onto a day.
4. Leftover detail modal:
   - Eat, freeze, waste, edit servings.
5. Dora:
   - "What leftovers should I eat?"
   - "Plan leftovers for lunch this week."

UX DETAILS:
- Leftovers should not be modeled as stock items unless the existing domain
  strongly prefers that. They have different lifecycle and serving semantics.
- If leftovers expire, they appear in Expiry Rescue.

DEFINITION OF DONE:
- Cook mode can create leftovers.
- Leftovers show on dashboard and meal plan.
- Eating/freezing/wasting updates status and insights.
- CHANGELOG entry under [Unreleased].
- Tests cover lifecycle transitions.
```

## P2-08 - Dietary Preferences and Meal Fit

```
Make recipe, meal, and Dora suggestions aware of dietary needs, allergies, and
household preferences.

READ FIRST:
- Recipe models and tags.
- Meal Plans P9.
- Dora recipe suggestion features from CHANGELOG.md.
- Household sharing P2-09 if already implemented.

DATA MODEL:
1. Add dietary_profiles:
   - id, user_id or household_member_id, name
   - dietary_tags json/array
   - allergens json/array
   - disliked_ingredients json/array
   - nutrition_goals json nullable
2. Add recipe metadata fields if missing:
   - dietary_tags, allergens, estimated_servings, calories_per_serving nullable,
     protein/carbs/fat nullable
3. Add stock item allergen/dietary metadata optional.

BACKEND:
1. GET/POST/PATCH /api/dietary-profiles
2. Recipe fit service:
   - Returns fit status:
     "safe" | "warning" | "blocked" | "unknown"
   - Includes reasons: contains allergen, disliked ingredient, missing metadata.
3. GET /api/recipes/<id>/fit
4. Meal plan validation:
   - Warn if planned meals conflict with selected household profiles.

FRONTEND:
1. Settings > Dietary:
   - Profiles
   - Allergens
   - Dislikes
   - Nutrition goals optional
2. Recipe cards:
   - Fit chips and warning states.
3. Recipe detail:
   - Dietary metadata editor.
4. Meal planner:
   - Warnings for blocked meals.
5. Dora:
   - "Suggest dinners that work for everyone."
   - Must explain any exclusion.

UX DETAILS:
- Treat allergy warnings as high-severity.
- Unknown metadata should not be presented as safe.
- Keep nutrition optional. Do not force calorie tracking onto all users.

DEFINITION OF DONE:
- User can define dietary profiles.
- Recipe and meal suggestions respect blocked allergens/dislikes.
- CHANGELOG entry under [Unreleased].
- Tests cover recipe fit and meal plan warnings.
```

---

# Tier P2-D - Household and Collaboration

## P2-09 - Household Sharing and Real-Time Collaboration

```
Add household sharing so multiple people can use the same pantry, lists, recipes,
and meal plan safely.

READ FIRST:
- Auth A1 and current user/admin model.
- Shopping lists, stock items, recipes, meal plans, settings, audit log.
- Offline queue F3 and undo F5.
- Existing ownership checks on every backend route.

ARCHITECTURE DECISION:
Before writing code, inspect whether data is currently scoped by user_id
everywhere. If so, introduce household_id carefully and migrate existing users
into a single-person household.

DATA MODEL:
1. Add households:
   - id, name, owner_user_id, created_at
2. Add household_members:
   - household_id, user_id, role ("owner" | "admin" | "member" | "viewer"),
     display_name, joined_at
3. Add household_invites:
   - id, household_id, email, role, token_hash, expires_at, accepted_at
4. Add household_id to user-owned domain data:
   - stock items, locations, shopping lists, recipes, meals, meal plans,
     saved products, reports, suggestions, receipts, leftovers
5. Add actor_user_id to audit log entries.

BACKEND:
1. Household management endpoints:
   - GET /api/household
   - POST /api/household/invites
   - POST /api/household/invites/accept
   - PATCH /api/household/members/<id>
   - DELETE /api/household/members/<id>
2. Ownership checks become household membership checks.
3. Mutations record actor_user_id.
4. Shopping list collaboration:
   - Optional WebSocket/SSE channel for active list updates.
   - At minimum, polling with conflict-safe updates.
5. Conflict handling:
   - Ticking the same item twice is idempotent.
   - Editing quantity uses optimistic locking or updated_at checks.

FRONTEND:
1. Settings > Household:
   - Household name
   - Members
   - Invites
   - Roles
2. Shared activity indicators:
   - "Alex added milk"
   - "Sam finished shopping"
3. ShoppingListDetail:
   - Show who ticked/edited each item where available.
   - Refresh live or near-live.
4. Audit/activity page:
   - Filter by member and entity type.
5. Dora:
   - "Who added this?"
   - "What changed today?"

SECURITY:
- All routes must prevent cross-household access.
- Invite tokens hashed at rest.
- Viewer cannot mutate.
- Member cannot manage invites unless role allows.

DEFINITION OF DONE:
- Existing single-user install migrates into a household.
- A second user can join by invite and share stock/lists.
- Shopping list changes attribute the actor.
- CHANGELOG entry under [Unreleased].
- Tests cover household scoping, invite acceptance, role permissions, and
  cross-household access denial.

STOP AND ASK before coding if user_id scoping is inconsistent or if household
sharing would require too broad a rewrite for one prompt.
```

---

# Tier P2-E - Shopping Experience Upgrades

## P2-10 - Store-Aware Shopping Route and Split Lists

```
Make shopping mode understand stores, merchants, and in-store route order.

READ FIRST:
- ShoppingListDetail P5.
- Product Search P10 and merchant offer models.
- Budget-aware optimizer P2-05.
- Locations hierarchy, but do not confuse home storage locations with store
  sections.

DATA MODEL:
1. Add merchants table metadata if missing:
   - id, name, logo, supports_sections bool
2. Add merchant_store_sections:
   - id, merchant_id, name, sequence
3. Add product_store_section mappings:
   - product_id, merchant_id, section_id nullable
4. Add user_merchant_preferences:
   - preferred_store_order, max_store_count, usual_store nullable

BACKEND:
1. GET /api/merchants/<id>/sections
2. POST/PATCH merchant section mappings, admin only or user-custom depending
   on existing product model.
3. Shopping list route service:
   - Groups by chosen merchant first.
   - Then by store section sequence.
   - Falls back to alphabetical when section unknown.
4. GET /api/shopping-lists/<id>/route
   - Returns grouped route with unknown-section bucket.
5. Split-list service:
   - Assigns list items to merchants based on price, preference, or budget
     strategy.

FRONTEND:
1. ShoppingListDetail mode switch:
   - Home location
   - Merchant
   - Store route
2. Store route view:
   - Big section headers
   - Progress by section
   - Unknown section bucket with quick "assign section" action.
3. Split by merchant:
   - Shows estimated total per merchant.
   - "Move this item to another merchant" action.
4. Settings:
   - Preferred stores
   - Max stores per shop
   - Store section order editor, if user-custom.

UX DETAILS:
- One-handed mobile use matters: large tap targets, sticky current section,
  minimal dense controls while shopping.
- Extra store trips should be justified by estimated savings.

DEFINITION OF DONE:
- Shopping list can be viewed in store-route order.
- Items can be split across merchants with totals.
- CHANGELOG entry under [Unreleased].
- Tests cover grouping fallback and merchant split logic.
```

## P2-11 - One-Handed Shopping Mode

```
Create a dedicated in-store shopping mode optimized for phones, speed, and poor
connectivity.

READ FIRST:
- ShoppingListDetail P5.
- Offline queue F3.
- PWA M1.
- Store-aware route P2-10 if implemented.

FRONTEND:
1. New route /shopping-lists/<id>/shop-mode.
2. Fullscreen mobile-first view:
   - Current section
   - Large next item card
   - Swipe/tap to mark picked
   - Quantity adjustment
   - Substitute/swap action
   - Skip reason action
   - Offline banner
3. Progress footer:
   - Picked count
   - Remaining count
   - Estimated total
   - Finish button
4. Keyboard/accessibility:
   - Space/Enter toggles picked
   - Large visible focus states
5. PWA shortcut:
   - Primary list opens directly into shop mode.

BACKEND:
- Reuse existing shopping list mutation endpoints.
- Ensure all shop-mode mutations are idempotent for offline replay.

UX DETAILS:
- Do not show dense admin controls in shop mode.
- Preserve scroll position and current section after reload.
- If app reconnects after offline work, show sync result clearly.

DEFINITION OF DONE:
- User can complete a list entirely from shop mode.
- Works acceptably offline with queued ticks.
- CHANGELOG entry under [Unreleased].
- E2E test covers mobile viewport shopping flow.
```

---

# Tier P2-F - Trust and Explanation

## P2-12 - Explanation Center and Automation Controls

```
Give users a central place to understand and control Dora's automations.

READ FIRST:
- Dora Assistant P14.
- Suggestion Inbox P2-04.
- Auto-generated lists X5 and Budget-Aware Lists P2-05.
- Forecasting P2-03.
- Audit log I1+I2.

DATA MODEL:
1. Add automation_preferences:
   - user_id/household_id
   - feature_key
   - enabled bool
   - mode ("off" | "suggest_only" | "auto_with_undo")
   - sensitivity/config json
2. Add automation_events:
   - id, user_id, household_id, feature_key, action, entity_type, entity_id,
     reason_json, created_at, undo_token nullable

BACKEND:
1. GET/PATCH /api/automation/preferences
2. GET /api/automation/events
3. All automated systems must read preferences:
   - forecast alerts
   - auto-add on low
   - Dora suggestions
   - budget optimizations
   - expiry rescue notifications
4. Every automation writes an event.

FRONTEND:
1. Settings > Automations:
   - One row per automation.
   - Mode selector: Off / Suggest only / Auto with undo.
   - Sensitivity controls where relevant.
2. Explanation Center route /automation:
   - Recent automated actions.
   - "Why did this happen?"
   - Undo where available.
   - Disable this automation shortcut.
3. Inline "Why?" affordance:
   - On auto-added list items.
   - On Dora suggestions.
   - On forecast alerts.

UX DETAILS:
- Use plain language. No hidden model jargon.
- The user must be able to turn off noisy automation quickly.
- "Never suggest this again" should map to a real preference or suppression.

DEFINITION OF DONE:
- Automation preferences control at least three existing automated features.
- Recent automation events are visible and explainable.
- CHANGELOG entry under [Unreleased].
- Tests cover preference enforcement and event logging.
```

---

# Tier P2-G - Voice and Ambient UX

## P2-13 - Voice-First Dora and Hands-Free Cook Mode

```
Add optional voice input and spoken feedback for Dora, kitchen use, and cook
mode.

READ FIRST:
- Dora Assistant P14 and LLM settings from CHANGELOG.md.
- Cook Mode P8.
- PWA M1.
- Browser support constraints for Web Speech API.

FRONTEND:
1. Build composable useVoiceInput:
   - Uses browser SpeechRecognition where available.
   - Gracefully degrades to push-to-talk text input when unavailable.
   - Permission errors get a friendly state.
2. Build composable useSpeechOutput:
   - Uses SpeechSynthesis where available.
   - User setting controls voice, rate, and enabled state.
3. Dora panel:
   - Mic button.
   - Live transcript.
   - Confirmation before mutating actions.
4. Cook Mode:
   - Voice commands:
     - "next step"
     - "previous step"
     - "start timer"
     - "repeat"
     - "mark done"
     - "add eggs to list"
   - Spoken timer completion optional.
5. Settings > Accessibility/Voice:
   - Enable voice input
   - Enable spoken replies
   - Push-to-talk vs continuous while cook mode is open

BACKEND:
- No direct backend speech processing in first version. The browser handles
  speech-to-text, and Dora receives text commands through existing paths.

UX DETAILS:
- Voice features are opt-in.
- Always show transcript before committing destructive or mutating actions.
- In cook mode, keep commands constrained and predictable.

DEFINITION OF DONE:
- User can add to a list through voice with confirmation.
- User can navigate cook mode hands-free.
- Unsupported browsers degrade cleanly.
- CHANGELOG entry under [Unreleased].
- Manual test matrix covers Chrome desktop, Chrome Android, Safari/iOS fallback.
```

---

# Tier P2-H - Advanced Imports and Sharing

## P2-14 - Recipe Import from URL, Photo, and Markdown

```
Implement robust recipe import beyond manual entry.

READ FIRST:
- Deferred items X8 Recipe import from URL and X9 Recipe-as-markdown storage.
- Recipe Detail/Edit P7.
- Data Import N3.
- Dora Assistant P14.

BACKEND:
1. POST /api/recipes/import/url
   - Fetches a URL server-side.
   - Extracts JSON-LD Recipe schema where available.
   - Falls back to readable HTML parsing.
   - Returns preview, does not save automatically.
2. POST /api/recipes/import/text
   - Accepts pasted text or markdown.
   - Parses title, ingredients, steps, servings, time.
3. POST /api/recipes/import/photo
   - Optional. If OCR dependency is unavailable, stop at upload plus manual
     transcription fallback.
4. POST /api/recipes/import/commit
   - Saves reviewed preview.
   - Ingredient rows must map to stock items or create new ones inline.

FRONTEND:
1. Recipe import dialog:
   - URL
   - Paste text/markdown
   - Upload photo
2. Review screen:
   - Editable title, servings, ingredients, steps.
   - Ingredient mapping to stock items.
   - "Create missing stock items" toggle.
3. Dora:
   - "Import this recipe" from URL or pasted text.

UX DETAILS:
- Never save imported recipes without review.
- Preserve source URL.
- Show parser confidence and warnings.

DEFINITION OF DONE:
- Import from a common recipe URL works via JSON-LD.
- Pasted markdown/text import works.
- Ingredients map to stock items.
- CHANGELOG entry under [Unreleased].
- Tests cover JSON-LD extraction and text fallback.
```

## P2-15 - Share Targets, Calendar Export, and Link Sharing

```
Make DiscountDora easier to move data into and out of everyday workflows.

READ FIRST:
- PWA M1 share_target section.
- Export & Print N4.
- Meal Plans P9.
- Auth/household sharing P2-09, if implemented.

FEATURES:
1. PWA share target:
   - Accept shared URLs/text.
   - Product URLs open Product Search/import flow.
   - Recipe URLs open Recipe Import.
2. Calendar export:
   - Meal plans export as ICS.
   - Optional subscription URL for a household meal plan calendar.
3. Shareable links:
   - Shopping list read-only share link.
   - Recipe share link.
   - Expiring, revocable tokens.

BACKEND:
1. POST /api/share/receive
2. GET /api/meal-plans/<id>/export.ics
3. POST /api/share-links
4. GET /api/share-links/<token>
5. DELETE /api/share-links/<id>

FRONTEND:
1. /share route handles PWA share target payload.
2. Meal plan toolbar:
   - Download ICS
   - Copy subscription URL if supported
3. Recipe and shopping list overflow menus:
   - Create share link
   - Revoke share link
4. Public read-only views:
   - No app chrome requiring login.
   - Clear "shared by" and generated date.

SECURITY:
- Share tokens must be high entropy and revocable.
- Shared views are read-only.
- Do not expose private household metadata unnecessarily.

DEFINITION OF DONE:
- Sharing a recipe URL into the PWA opens import review.
- Meal plan downloads as ICS and imports into a calendar app.
- Share links can be created and revoked.
- CHANGELOG entry under [Unreleased].
- Tests cover token access and revocation.
```

---

# Tier P2-I - Final Polish and Testing

## P2-16 - Part 2 E2E and Value-Loop Tests

```
Extend the E2E suite so Part 2's real-world value loops are protected.

READ FIRST:
- T1 E2E test suite.
- P2-01 through P2-15 implementations that have landed.
- Existing Playwright fixtures and test-mode helpers.

TESTS:
1. receipts.spec.ts
   - Paste receipt text.
   - Match two lines to stock items.
   - Reconcile against an active shopping list.
   - Assert list items are picked, actual prices stored, stock updated.

2. forecasting.spec.ts
   - Seed purchase/usage history.
   - Forecast says item is due soon.
   - Generate list from forecast source.

3. waste-rescue.spec.ts
   - Seed expiring item and recipe that uses it.
   - Dashboard shows Use Soon.
   - Add missing companion ingredients to shopping list.
   - Log one item as wasted and see insight update.

4. budget-list.spec.ts
   - Create candidate items with offers.
   - Generate budget-aware list under a target.
   - Assert must-include items stay and nice-to-have items defer.

5. suggestions.spec.ts
   - Generate Dora suggestions.
   - Accept one suggestion.
   - Dismiss one suggestion.
   - Reload and assert dismissed suggestion does not reappear unchanged.

6. household.spec.ts
   - Invite second user.
   - Accept invite.
   - Both users see the same list.
   - Actor attribution appears after second user ticks an item.

7. shop-mode-mobile.spec.ts
   - Open primary list in mobile viewport.
   - Complete items in one-handed shop mode.
   - Finish shopping.

8. voice-fallback.spec.ts
   - In a browser/context without speech recognition, Dora shows text fallback
     and remains usable.

TEST-MODE HELPERS:
- Add helpers only when impossible through public APIs.
- Keep them gated behind E2E_MODE=1.
- Refuse to start in production with E2E_MODE enabled.

CI:
- Add Part 2 specs to existing E2E job.
- Tag slow/browser-permission tests so they can be run separately if needed.

DEFINITION OF DONE:
- The core Part 2 loops are covered by E2E.
- A broken receipt reconciliation, forecast list, or household scoping check
  fails CI.
- CHANGELOG entry under [Unreleased].
```

---

# Deferred or Research First

These are valuable, but should be investigated before turning into build prompts:

- **External supermarket account integrations** - likely high value, but brittle,
  auth-sensitive, and dependent on merchant terms.
- **Automatic email receipt ingestion** - useful, but needs Gmail/Outlook
  connector decisions, privacy language, and duplicate detection.
- **Nutrition database integration** - potentially useful, but scope depends on
  region, data source, licensing, and whether nutrition is core to the product.
- **Computer vision pantry scan** - attractive idea, but likely unreliable until
  item packaging, barcodes, or receipt data give better anchors.
- **Dynamic price prediction** - predicting future specials may be powerful, but
  needs enough historical price data before it is trustworthy.
- **Payments or direct cart checkout** - large scope and partnership-dependent.

---

# Notes

Part 2 should make DiscountDora feel less like a database and more like a
household rhythm: what came in, what went out, what will run out, what should be
used soon, what can wait, and what Dora can safely handle for you.

The strongest product direction is not more screens for their own sake. It is
closing feedback loops:

- planned vs actually bought
- bought vs actually used
- used vs wasted
- usual price vs today's price
- suggested action vs user accepted/dismissed
- individual action vs household context

That is where the next layer of end-user value is waiting.
