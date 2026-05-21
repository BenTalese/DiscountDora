"""A compact description of what Dora can do, used to ground the assistant's
answers to how-to / app-help / general questions.

Keep it concise — it's injected into the model's context on every general
question, and small models follow short, concrete guides best. Update this when
features land so the assistant's advice stays accurate.
"""

APP_OVERVIEW = """\
Dora is a grocery, pantry and shopping app. Main areas (reachable from the
left-hand navigation menu):

- Dashboard (home): stock health at a glance, upcoming planned meals, quick stats.
- Stock: every item you track. Search and filter by stock level, location,
  group, essentials, or whether it's already on a shopping list; sort the list;
  click an item for its detail (adjust stock level, link merchant products, see
  which recipes use it, set expiry). Each row has a cart button to add the item
  to your shopping list.
- Locations: your storage as hierarchical zones > areas > sections, shown as a
  heatmap by how much attention each needs. Drag items between zones to move them.
- Product Search: search for products across configured merchants (Coles,
  Woolworths, IGA, Aldi). Link a product to a stock item so its deal price
  tracks alongside your pantry. This is the page to use for finding products and
  deals.
- Recipes: your recipes, with ingredients (and where each lives), instructions
  and a step-by-step Cook mode.
- Meals: bundle one or more recipes together (e.g. a roast plus sides).
- Meal Plans: plan the week — drag meals onto days and set servings.
- Shopping Lists: multiple lists with one marked primary. Archive on completion,
  copy lists, use templates, group by merchant, and a "finish shopping" flow
  that bumps ticked items back to well-stocked.
- Alerts: the bell icon (top bar) opens a panel of things needing attention —
  expired, expiring soon, low/out of stock, stocktake overdue — with inline
  actions.
- Settings: preferences (theme, font), account (change password/username),
  locations, and version info. Admins also get Merchants (toggle scrapers) and
  Users (manage accounts).
- Help: guides by area, the changelog, and the assistant (that's Dora).

The assistant can also answer questions about your data ("what's low?", "any
specials on cheese?"), suggest recipes (by mood or from what's in stock), and
add items to your shopping list ("add 2 milk").
"""
