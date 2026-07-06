"""A compact description of what Dora can do, used to ground the assistant's
answers to how-to / app-help / general questions.

Keep it concise — it's injected into the model's context on every general
question, and small models follow short, concrete guides best. Update this when
features land so the assistant's advice stays accurate.
"""

APP_OVERVIEW = """\
Dora is a grocery, pantry, recipe, and shopping app. Products and store data
come from whichever merchants the household has configured — the app is not
tied to a particular country or retailer. Main areas (left-hand navigation):

- Dashboard (home): pantry health at a glance, upcoming planned meals, quick
  stats, items needing attention.
- Stock: every item the user tracks. Search and filter by stock level, location,
  group, essentials/flagged, or whether it's already on a shopping list; sort
  the list; click an item for its detail page (adjust stock level, link
  products, see which recipes use it, set expiry, mark as opened, push expiry).
  Each row has a cart button to add the item to the primary shopping list.
- Product Search: an admin-configured external search surface (Phase D);
  opens in a new tab when set. Pushes data into Dora via the ingestion seam.
- Recipes: the user's recipes, with ingredients (and where each lives),
  instructions, cook time, difficulty, cuisine, category, and a step-by-step
  Cook mode. Each recipe also tracks "available meals" — portions of that
  dish currently in the pool (e.g. cooked-ahead servings in the freezer).
  Cook mode ends by asking how many meals were cooked; that count is added
  to the pool. Favourite recipes are surfaced first in suggestions.
- Meal Plans: plan a week by assigning recipes to days + slots
  (breakfast/lunch/dinner) with a servings count. When a day passes the
  entries auto-decrement the recipe's available-meals pool (floored at 0)
  and lock read-only. Past days can't be edited. If commitments exceed
  the pool, the planner surfaces a "needs cooking" shortfall.
- Shopping Lists: multiple lists with one marked PRIMARY (the default target
  for new additions). Archive completed lists, copy lists, use templates,
  group items by store, and a "finish shopping" flow that bumps ticked
  items back to a stocked level. Lists can be marked in-progress while
  shopping.
- Alerts: the bell icon (top bar) opens a panel of things needing attention —
  expired, expiring soon, low/out of stock, stocktake overdue — with inline
  actions to fix them.
- Settings: preferences (theme, font, density), account (change password /
  username), stock locations (zone/area/section tree editor — items reference
  these locations from Stock), stock groups, and version info. Admins
  also get Stores (user-curated retail stores; upload logos), Users (manage accounts),
  and System (configure the AI assistant — that's the BYO-LLM panel).
- Help: guides by area, the changelog, the assistant.

The assistant (you) can do natural-language data lookup and actions over the
user's data. Available tools include: searching stock / products / recipes,
recipe suggestions (by mood or what's in stock), pantry health snapshots,
expiry lookups with a horizon, deal hunting, meal-plan-for-date, reverse
recipe lookups ("what can I make with these strawberries"), kitchen unit
conversion (volume / mass / temperature, density-aware for flour / sugar /
butter / rice / etc.), ingredient substitution suggestions, and adding items
to the primary shopping list.
"""
