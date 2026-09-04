# Dora Follow-ups Ledger — Open

Stateful backlog of **open follow-ups, deferred jobs, leftovers, and findings**
surfaced while running prompts — the stuff that's easy for the user to miss in a
long session summary. Distinct from the other logs:

- `CHANGELOG.md` = product/code changes that shipped.
- `DORA_WORKLOG.md` = per-session handoff narrative.
- `DORA_FOLLOWUPS.md` (this file) = **open loops** that outlive a single session.
- `DORA_FOLLOWUPS_RESOLVED.md` = the archive of items that have been resolved
  (kept for the trail — never delete).

## How to use this file

- **On session start:** scan for items here. Surface the ones whose *recommended
  resolution point* is "now" or matches the work about to start, and **ask the
  user** whether they want to review/resolve them now or defer.
- **On ending a work unit:** add any new follow-ups/leftovers/findings you
  generated. If you actually resolved an item, **move its entry from this file
  to `DORA_FOLLOWUPS_RESOLVED.md`**, flip the heading from `[OPEN]` to
  `[RESOLVED]`, and add a one-line state note on how. Do not leave resolved
  items in this file, and do not delete them either — the trail matters.
- **Reported defect that "doesn't reproduce" → still log it here** as `[OPEN]`
  type `finding`, resolution "confirm in browser". A static code read is not
  proof a user-reported bug is fixed. Track each reported item individually;
  never bury several as one "all fine" note.
- Keep the newest items at the top.

## Entry template

```
## [OPEN] FU-873 — `frequently_added.py` reads a `lazy="noload"` relationship and reports `None`
- **Raised:** 2026-09-04 (log-price picker ordering)
- **Type:** finding (R-082 trap, currently harmless)
- **What:** `GetFrequentlyAddedHandler` builds each row with
  `item.stock_level.id if item.stock_level else None`. Its query doesn't
  `.include(STOCK_LEVEL)`, and that relationship is mapped `lazy="noload"`, so
  the guard always takes the `None` branch: `/shopping-lists/frequently-added`
  has been returning `stock_level_id: null` for every row since it was written.
- **Why it's harmless today:** the only consumer, `QuickAddSheet`, uses the
  response for *ordering* and for `isFrequent()`, and reads each item's level
  from its own store — so nothing renders the null. The new
  `/stock-items/recently-priced` was deliberately shaped without the field for
  the same reason.
- **Recommended resolution:** opportunistic — either add the `include` (and
  resolve through `_level_access.py`, per R-082) or drop the field from the DTO
  so it can't be trusted by a future caller. The second is probably right.

## [OPEN] FU-872 — `load_recipe_cookability` silently returns wrong answers if StockItems are already in the session
- **Raised:** 2026-09-04 (dashboard feedback batch — browser walk)
- **Type:** finding (data-access trap; R-032 family)
- **What:** the helper eager-loads `RecipeIngredient → StockItem → StockLevel`,
  but `StockItem.stock_level` is `lazy="noload"`. If anything earlier in the same
  request has already pulled those StockItem rows in — a bare
  `repository.get(StockItem).all()` will do it — the identity map returns the
  cached instances and the eager load **does not populate `stock_level`**. Every
  linked ingredient then reads as unstocked, so `missing_count` is non-zero for
  every recipe. No error, no warning: a 200 and a confidently wrong number.
- **How it surfaced:** Kitchen health's new `plan_coverage` component rendered
  *"None of your 6 planned meals can be cooked right now"* beside a Next-to-cook
  card offering to cook five of them, because the freshness block above it loads
  every StockItem. Fixed **locally** by hoisting the cookability load to the top
  of `get_dora_score._gather_inputs`, with a comment saying why it must stay
  there — which is a fix that a future edit can silently undo by reordering.
- **Why it isn't fixed properly here:** the real fix is to make the helper
  independent of session state — resolve levels through the shared
  `resolve_levels_by_item` idiom (`_level_access.py`) rather than relying on an
  eager include, exactly as that module was written to do for the same trap. That
  touches the cookability rule every recipe surface reads (`?cookable`, the
  recipe DTO, the dashboard summary, this score), so it wants its own unit and
  its own test rather than a ride-along.
- **Worth checking while in there:** whether any *other* caller of
  `load_recipe_cookability` runs after a StockItem load in the same request. The
  dashboard summary computes it early and is fine; `GetRecipesHandler` uses its
  own `_base_query`. Neither was verified for ordering here.
- **Recommended resolution:** later — before any further use of
  `load_recipe_cookability`, and certainly before a fifth caller appears.

## [OPEN] FU-871 — Six retired dashboard card ids are still sitting in every user's saved layout
- **Raised:** 2026-09-04 (dashboard feedback batch)
- **Type:** follow-up (data hygiene, low urgency)
- **What:** `User.dashboard_layout` stores `{order, hidden}` as JSON. The cull
  retired `attention`, `draft_shop`, `suggestions`, `spend_trend`,
  `pantry_value`, `reconcile_pending` and renamed `cookable` → `next_to_cook`,
  `primary_list` → `shopping_lists`. Nothing rewrites the stored JSON: it is
  filtered to known ids on read (`parseLayout`), so behaviour is correct, but the
  dead ids persist in the row until the user next reorders something.
- **Why deferred:** harmless — `parseLayout` is the guard, and
  `dashboardCards.spec.ts` pins the retired ids as absent so one can't be
  resurrected for a different card and inherit somebody's hidden flag. A
  migration to scrub them is cosmetic.
- **Recommended resolution:** opportunistic — fold into the next migration that
  touches `User`, or never.

## [OPEN] FU-870 — Kitchen health's trend arrow now moves on four signals, not five
- **Raised:** 2026-09-04 (dashboard feedback batch)
- **Type:** finding (accepted trade, recorded so it isn't rediscovered)
- **What:** `plan_coverage` is deliberately forward-looking — it grades the next
  7 days — so the lagged recompute sees the same future and returns the same
  number, and it cancels out of `trend_delta` entirely. The arrow is therefore a
  mean over the other four components while the card presents five.
- **Why it's accepted:** the arrow is a secondary flourish; *"your plan is
  half-uncookable"* is the most actionable thing the card can say, and making it
  trend-comparable would mean grading a *past* week's coverage, which nobody can
  act on. Stated in `_score_plan_coverage`'s docstring.
- **Recommended resolution:** when the trend arrow is next revisited — decide
  whether to (a) leave it, (b) exclude forward-looking components from the trend
  explicitly rather than incidentally, or (c) drop the arrow.

## [OPEN] FU-869 — `/reports/keeps-running-out` lost its dashboard caller
- **Raised:** 2026-09-04 (dashboard feedback batch)
- **Type:** leftover (R-057 contract inventory)
- **What:** Restock radar was rebuilt on the new `/dashboard/restock-radar`, so
  `reportsApi.getKeepsRunningOutAsync` no longer has a dashboard caller. **The
  endpoint is NOT orphaned** — the reports page still calls it with its own range
  — so this is an inventory note, not a deletion candidate. Logged because R-057
  is explicit that a replaced surface's contracts get checked rather than
  assumed, and because the reports page is now its *only* consumer, which changes
  who owns its shape.
- **Recommended resolution:** opportunistic — confirm at the next reports-page
  visit that the range-passing behaviour is still what that page wants.

## [OPEN] FU-868 — Two dashboard cards were never seen with their feature gate OFF
- **Raised:** 2026-09-04 (dashboard feedback batch — browser walk)
- **Type:** finding (verification gap)
- **What:** the 09-04 walk ran on the dense seed, which has **both** money and
  products **on**. So: the Shopping-lists card's money-off body (counts only, no
  dollars) and the Price-drops card's products-off disappearance from both the
  grid and the Cards menu were reasoned about but not observed. The registry
  spec asserts the *gates*; it can't assert the rendered result.
- **Why deferred:** needs a second backend on a money-off / products-off seed,
  which is a whole verify pairing rather than a step in this one.
- **Recommended resolution:** when a money-off verify run next happens — the
  corresponding eyes-on steps are in `DORA_VERIFY.md` under Dashboard.

## [OPEN] FU-NNN — short title
- **Raised:** YYYY-MM-DD (prompt id / task)
- **Type:** follow-up | deferred job | leftover | finding
- **What:** one or two lines.
- **Why deferred:** the reason it wasn't done in-line.
- **Recommended resolution:** now | later during <Phase/Prompt X> | when <trigger> | opportunistic
```

---

## [OPEN] FU-867 — Add-user dialog still changes height when "Generate password" flips
- **Raised:** 2026-09-03 (owner feedback batch — admin settings)
- **Type:** follow-up
- **What:** the owner's complaint was that the dialog *grew* when you chose to
  generate a password. The cause was a caption that appeared only in that state;
  it's gone, so it no longer grows — but the password field itself is still
  `v-if`'d away, so the dialog now **shrinks** by ~82px (measured live: 507 →
  425). Less jarring, not zero.
- **Why deferred:** the remaining jump is the field genuinely leaving, which is
  arguably correct. Removing it entirely means rendering a disabled field that
  says "Dora will generate this", i.e. a dead control — a worse trade unless the
  owner finds the shrink annoying in use.
- **Recommended resolution:** opportunistic — decide when the owner has walked the
  dialog.

## [OPEN] FU-866 — `companion_ingestion_enabled` gates nothing: `POST /api/ingest` never checks it
- **Raised:** 2026-09-03 (admin settings batch — found while renaming the flag)
- **Type:** finding
- **What:** the switch now presented as **Product data ingestion** (Settings →
  Admin → Data & access) does not stop ingestion. `submit_ingestion_batch()`
  authenticates the bearer token against an `IngestionSource` and proceeds; it
  never reads `AppSetting.companion_ingestion_enabled`. Nothing in the SPA reads
  the `features.companion_ingestion` health flag either (nor
  `features.deals_email`). The column's only readers are its own settings page,
  the DTO and the health probe.
- **Why this matters more than usual:** it is the second instance of exactly the
  defect **R-078 / ADR-075** was written for this session, on the same page as the
  first (`meal_planning_enabled`, deleted in migration `a7c3e5d19f2b`) — and
  unlike that one, the owner-dictated copy now shipping *asserts* the gate
  ("Accept product offer data from an external source. Enable this if you have a
  tool…"). The toggle reads as a security control and isn't one.
- **Why deferred:** the fix is a one-line 403 guard in the route, but the flag
  **defaults to `False`**, so wiring it up would immediately break ingestion for
  any install already pushing data without having flipped it on — including the
  owner's. That is a deliberate behaviour change needing a call, not a tidy-up:
  guard it and accept that existing pushers must switch it on, or flip the
  default for existing rows in the same migration.
- **Recommended resolution:** **now** — before anyone relies on the toggle
  meaning what it says. R-078's own instruction applies: wire it up or drop it.
## [OPEN] FU-865 — Quasar palette vars are set on `<body>`, so the `html` scrollbar rule never gets the theme
- **Raised:** 2026-09-03 (owner misc batch — found while fixing FU-709)
- **Type:** finding
- **What:** `css/app.scss` styles the browser scrollbar with
  `html { scrollbar-color: var(--q-secondary) var(--q-page) }`, but Quasar's
  `setCssVar` writes to **`document.body`** by default, which is where
  `themeService.syncQuasarPaletteFromCssVars` puts the whole palette. A custom
  property set on `body` does not inherit *upwards*, so the `html` rule resolves
  against Quasar's own `:root` defaults and the scrollbar is the same colour in
  every theme. Confirmed live during the FU-709 walk: reading
  `--q-dark-page` off `document.documentElement` returned Quasar's `#14171a` in
  all themes while `document.body`'s background painted the synced value.
- **Why deferred:** out of scope for the batch that found it, and the fix has two
  candidate shapes worth one moment's thought rather than a reflex: either point
  the rule at the semantic tokens it should have used in the first place
  (`html { scrollbar-color: var(--brand-secondary) var(--surface-page) }` —
  those *are* on `:root`, and R-002 prefers them anyway), or move the rule to
  `body`. The first is better and is probably a two-line change.
- **Recommended resolution:** opportunistic — next time anything touches
  `app.scss` or the theming layer. Cheap, cosmetic, low risk.

## [OPEN] FU-864 — Two "Dora does this for you" actions still wear the wand, not the burger
- **Raised:** 2026-09-03 (meal-planner owner batch)
- **Type:** follow-up
- **What:** the owner asked for *"the consistent Dora burger icon"* on **Build my
  week**, which revised the wand/burger split recorded in `style/icons.ts`
  ("wand = an action she performs; burger = an opinion she holds"). The revised
  rule — the burger is Dora's mark on anything the user reads as Dora doing or
  thinking something — is now written into that file, and every meal-planner site
  flipped (toolbar, empty-week banner, phone, the builder's step icon and its
  primary button). Two sites did **not**, because they are outside this batch's
  surface: `components/dashboard/DraftShopCard.vue` (*Draft my shop* — the
  dashboard's exact counterpart to Build my week) and
  `components/shoppingList/ShoppingListPlanRow.vue`'s 12px inline hint.
  `auto_awesome` legitimately keeps the AI-mode marker (`DoraModeSlider`,
  `DoraHelpPage`, `SetupAdminPage`), where it means "a model is involved", not
  "Dora".
- **Why deferred:** R-007. The dashboard is a surface the owner reviewed and
  signed off visually across six chunks; changing its card icon now is an
  unasked visual edit to signed-off work, and it is one line whenever he wants it.
- **Recommended resolution:** now-ish — one line each, but it is the owner's call
  whether *Draft my shop* should match *Build my week*. Ask before sweeping.

## [OPEN] FU-863 — A cook batch straddling today loses its link when only one forward day is left
- **Raised:** 2026-09-03 (meal-planner owner batch — found during the multi-day QA walk)
- **Type:** finding
- **What:** a cook batch whose **cook day is in the past** keeps its leftover days
  linked, and this batch fixed the case where an unrelated edit split it in two
  (the reattach in `update_meal_plan`). But if the batch is left with a *single*
  forward leftover day, that day silently becomes a standalone meal. Walked live:
  a Wed-cooked Sunday Ragu with Thu + Fri leftovers, Thursday stepped to zero
  servings — Friday came back with its "Leftovers" marker gone.
- **Why it happens, and why it isn't simply a bug in the new code:** past entries
  are immutable and the client never resends them (FU-595), so a payload can only
  ever carry the *forward* members of a straddling batch. When that is one entry,
  the client's `dissolveOrphanCookKeys` strips the `cook_key` — because the server
  refuses a one-member group (`validate_cook_groups`: "a cook batch must cover at
  least two days"), and it is right to for a batch that is genuinely one day. The
  two rules are individually correct and jointly wrong for this shape.
- **Fix shape:** the server is the only party that can see both halves. Have the
  update handler count a group's *preserved* members alongside the payload's
  before validating, and let a one-member payload group survive when the same
  batch has a preserved entry. That means the client must stop stripping the key
  in that case, which it cannot detect — so the honest version is for the client
  to always send the key and let the server decide, i.e. move the orphan-dissolve
  rule server-side. That is a contract change to the write path, not a patch.
- **Impact:** cosmetic and small — a leftovers day loses an eyebrow. Nothing is
  double-cooked and no ingredient demand changes (the pool model already treats
  a lone entry as its own cook).
- **Recommended resolution:** later, with any pass over the meal-plan write path.

## [OPEN] FU-862 — `mealPlanStore.getShortfallAsync` has no client consumer left
- **Raised:** 2026-09-03 (meal-planner owner batch)
- **Type:** leftover
- **What:** the planner was the only client reader of `GET /meal-plans/shortfall`,
  and it used those recipe-level rows to decide which meal chips needed a cook —
  a recipe-level answer to a per-entry question, which is the defect the owner
  reported ("3 fried rice planned, 2 in the pool, all three light up"). That
  verdict is now per-entry on the plan (`MealPlanEntry.needs_cooking`), so the
  composable stopped fetching it — on mount, after every mutation, after a pool
  ±, and after a week clear (four fewer round trips). `mealPlanStore.shortfall`,
  `getShortfallAsync` and `MealPlanApiService.getShortfallAsync` are therefore
  written and read by nothing on the client. Annotated in place rather than
  deleted.
- **Why deferred:** the **endpoint** is live and answers a different question
  (how many *servings* short each recipe is, not which meals to cook) — the
  assistant's `meals_shortfall` tool reads it server-side, and it is plausibly
  what a future "what should I batch-cook this weekend" surface wants. Deleting
  the client plumbing is a two-minute job whenever it is clear nothing wants it.
- **Recommended resolution:** opportunistic — delete the store ref + api method
  if no client surface has claimed it by the next meal-plan unit.

## [OPEN] FU-861 — Technical details → Build has no real build number
- **Raised:** 2026-09-03 (owner feedback batch — settings/About)
- **Type:** follow-up
- **What:** About → Technical details renders `buildLabel` under a caption that
  admits *"Versioning isn't tagged in this fork yet."* The owner asked for a real
  build number there — the point of the row is that a bug report can name the
  exact artifact it came from, and a placeholder can't do that.
- **Why deferred:** it isn't a UI change. It needs a decision about where the
  version comes from (a git tag/describe, the package version, a CI-stamped
  build id) and a way to get it into both the SPA bundle and the Flask API so the
  two can't disagree — which touches the build/packaging pipeline, not this page.
- **Recommended resolution:** later during Phase 4 (open-source release), where
  tagging a version is on the critical path anyway.

## [OPEN] FU-860 — With products off, Dora sends no scheduled email at all
- **Raised:** 2026-09-03 (owner feedback batch — settings/Notifications)
- **Type:** finding
- **What:** the owner asked what email notifications exist when products is
  disabled, and whether the section is hidden. **It is** — the whole Email block
  is behind `v-if="productsEnabled"`, because the weekly deals email is the only
  thing Dora mails on a schedule and with no ingested product data it has no deal
  source. So the answer to "what's left?" is *nothing*, which is the actual
  finding: an install without products (the default self-host shape) has an empty
  email channel, and the owner's own follow-on — *"perhaps there is something we
  could email that users would want/enjoy and we're missing"* — is the open
  question. Candidates already computed elsewhere: the evening brief (currently
  push-only, so a user with no push support gets nothing), an expiring-soon
  digest, a week-ahead meal plan, an end-of-month spend summary.
- **Why deferred:** designing a second scheduled email is a feature, not a copy
  fix, and it needs a call on which one earns being unprompted mail. The evening
  brief is the cheapest — it already exists, is already scheduled, and only the
  delivery channel is missing.
- **Recommended resolution:** now-ish — it's a small product decision, and it
  wants the owner's answer before anything is built.

## [OPEN] FU-859 — Zone/area/section counts no longer distinguish direct from descendant items
- **Raised:** 2026-09-03 (owner feedback batch — settings/Stock locations)
- **Type:** finding
- **What:** per the owner (*"too much arithmetic/text going on, just show count
  of items"*), the area row's label went from `3 here · 11 in total` to plain
  `11 items`, and the zone header dropped its area tally. That is what was asked
  for and it reads far better, but it does lose one fact the old label carried:
  how many items sit **directly** on a level rather than in its children. A zone
  with 23 items and one area holding 23 now looks identical to a zone with 23
  loose items.
- **Why deferred:** the owner explicitly asked for less text here, so adding it
  back inline would be re-litigating the request. If it turns out to matter, the
  place for it is the overflow menu's "View items" (which now exists at all three
  levels) or a tooltip — not the row.
- **Recommended resolution:** opportunistic — only if the owner misses it in use.

## [OPEN] FU-858 — Nutrition-matching badge fetches for every user in complex mode
- **Raised:** 2026-09-03 (owner feedback batch — settings/Nutrition matching)
- **Type:** finding
- **What:** the new sidebar count (owner ask: *"count of unmatched items same as
  unlinked ingredients would be good"*) hydrates from
  `GET /api/nutrition/unmatched-items`, which on this seed returns the full 41
  rows — the whole unmatched list — to render one integer. `unlinkedIngredients`
  has exactly the same shape and the same cost, so this is consistent rather than
  novel, but it now happens twice per settings mount.
- **Why deferred:** it's a real but small waste, and fixing it properly means a
  count-only endpoint (or a `?count_only=1` on both), which is server work beyond
  a settings-polish batch. R-003 stays satisfied either way — the server owns the
  number; the client just over-fetches to read it.
- **Recommended resolution:** opportunistic, when either endpoint is next touched.

## [OPEN] FU-857 — Free-text steps are numbered twice unless we strip the author's own ordinal
- **Raised:** 2026-09-03 (recipe-view owner batch, item 10)
- **Type:** finding
- **What:** giving free-text steps the structured face's numbered circles made
  the seed's Carbonara read "(1) 1. Render the pancetta" — the author had typed
  their own "1. " prefixes, which is what people do in a free-text box. The read
  view now strips a leading ordinal (`/^\d{1,3}\s*[.):]\s+/`) for display only;
  the stored text and the editor are untouched. Two loose ends: (a) the strip is
  display-side, so the *editor* still shows "1. Render…" and an author who
  renumbers by hand gets no help; (b) the pattern is deliberately narrow and will
  miss "Step 1 — " or "(1) ".
- **Why deferred:** the owner asked for the circles, not for a numbering
  authority. Deciding whether free text should be *normalised on save* (strip the
  ordinals for real, since the app now draws them) is a data-shape call.
- **Recommended resolution:** opportunistic — or now, if the doubled numbering
  turns up in a recipe the strip doesn't catch.

## [OPEN] FU-856 — `pack_count` can't be recorded through the products API, so R-076's better answer is unreachable
- **Raised:** 2026-09-03 (recipe-view owner batch, item 13)
- **Type:** follow-up
- **What:** the cost fix (ADR-073) makes a bare count priceable whenever
  `Product.pack_count` is set — "3 eggs" off a 12pk costs $1.38 rather than being
  reported unpriced. But `CreateProductRequest` / `UpdateProductRequest` are
  `extra="forbid"` and neither carries `pack_count`, so the only way it gets set
  today is a seed script assigning the attribute directly. A user who links a
  multipack product has no way to tell Dora how many are in it, and their counted
  ingredients stay unpriced forever.
- **Why deferred:** it's an API + form change on the products surface, which is
  not what the owner's item was about, and it needs a UI decision (a field on the
  manual product-add form? inferred from the name's "12pk"?).
- **Recommended resolution:** now-ish — it is the half of the cost fix that turns
  a gap back into a number.

## [OPEN] FU-855 — Counted ingredients against a measured pack lost coverage they used to have
- **Raised:** 2026-09-03 (recipe-view owner batch, item 13)
- **Type:** finding
- **What:** deliberate consequence of ADR-073, logged because it is a *narrowing*
  and the owner should get to see it. "2 tins" of a product sized `400 g` with no
  `pack_count` is now reported **unpriced** ("Units don't match the price") where
  it previously billed 2 × the shelf price — which was the right answer for a tin
  and the wrong one for the eggs carton that produced the $16.50 report. The two
  are indistinguishable in the schema, so the honest gap won. Impact is visible
  as a lower "Priced N of M" ratio on recipes that count packs.
- **Why deferred:** it is the trade the fix was chosen for, not a bug — but if the
  owner would rather have the old guess back for single-container products, the
  lever is FU-856 (record `pack_count = 1`) rather than reverting the rule.
- **Recommended resolution:** when the owner has walked a costed recipe and said
  whether the narrower coverage reads acceptably.

## [OPEN] FU-854 — The Alerts bell still hands out the retired "primary list" dead end
- **Raised:** 2026-09-03 (cook-mode owner batch, item 5)
- **Type:** finding
- **What:** the owner's report was cook mode's finish-modal cart button ("there
  should be **no other instance** of this old button in the app"). That one is
  fixed. Sweeping for the same *class* of defect found one survivor:
  `AlertsBell.vue:183` — the "Add N low/out items to primary list" footer
  button reads `shoppingListStore.quickAddTargetListId`, which is non-null only
  when exactly ONE draft list exists, and otherwise raises a dialog titled
  **"No primary list"** telling the user to "set a primary shopping list
  first". Primary lists were retired in C-7 Chunk 2; with two drafts open (the
  dense seed's normal state) the bell's bulk shortcut is simply unusable.
- **Why deferred:** it is a different surface and a different control — a
  labelled bulk button, not the icon cart the owner reported — and the fix
  (`AddToListButton variant="bulk"`, which resolves the target by prompting)
  changes what the bell's footer *does*, not just how it reads. Doing it
  silently inside a cook-mode batch would have shipped an unverified behaviour
  change to Alerts. The label copy also needs a call: "add N to a list" vs
  naming the resolved list.
- **Recommended resolution:** now — it's a ~10-line swap plus one browser pass,
  and it is the last known instance of the pattern the owner asked to be rid of.

## [OPEN] FU-853 — Cook mode's timer chime is blocked by the app's own CSP
- **Raised:** 2026-09-03 (cook-mode owner batch — observed, not reported)
- **Type:** finding
- **What:** driving cook mode live logs, on every load:
  `Loading media from 'data:audio/wav;base64,…' violates the following Content
  Security Policy directive: "default-src 'self'". Note that 'media-src' was
  not explicitly set, so 'default-src' is used as a fallback.` The timer's
  end-of-countdown sound is a `data:` WAV and the CSP has no `media-src`, so
  **the chime never plays** — the one piece of feedback a hands-free cook with
  a pot on the stove is relying on. The visual bar and the toast still fire, so
  nothing looks broken.
- **Why deferred:** pre-existing, unrelated to the five reported items, and the
  fix is a server header change (`media-src 'self' data:`) that wants its own
  verification — including a check for any other `data:`/blob media the same
  directive would cover.
- **Recommended resolution:** opportunistic — next time cook mode or the CSP is
  touched. Pair with a live listen, since a silent-by-config chime and a
  silent-by-bug chime look identical in the code.

## [OPEN] FU-851 — Planned demand goes stale after a plan edit anywhere but the stock detail page
- **Raised:** 2026-09-03 (owner batch — planned-demand signal)
- **Type:** finding
- **What:** `usePlannedDemand` is a module-level cache, like `usePantryBeliefs`.
  It is invalidated on a level change from `StockItemDetailPage`, because that
  changes the urgency grade. It is **not** invalidated when the thing it is
  actually derived from changes: adding, moving, deleting or consuming a meal
  plan entry, or bumping a recipe's cooked pool. Within one SPA session, a user
  who plans three meals and then opens a stock item sees the pre-edit counts.
- **Why deferred:** the same exposure the belief cache has had since P8-07 (a
  finished shop changes a belief and nothing invalidates it either), so it is a
  pattern to fix once rather than a bug to patch here. The honest fix is
  probably an invalidation bus the meal-plan and cook mutations publish to,
  which both caches subscribe to — that is its own unit.
- **Recommended resolution:** opportunistic, with any pass over the overlay
  caches. Cross-ref: R-074, ADR-071.

## [OPEN] FU-850 — `--accent-mark` adoption is limited to the sites this pass touched
- **Raised:** 2026-09-03 (owner batch — accent ink too dark)
- **Type:** follow-up
- **What:** the ink/mark split gave the accent a second tier at D-002's 3:1
  floor for non-text marks and icons. Eleven declarations moved (tab indicator,
  settings nav indicator + mobile underline, settings page-header icons, theme
  card border + badge, voice-card borders + check, dashboard hairlines, the
  focused stock-row outline). The sweep was scoped to what the owner was
  looking at; there are almost certainly other `--accent-ink` declarations
  across the app painting borders, icons or indicators that are still one tier
  darker than they need to be.
- **How to find them:** `grep -rn "accent-ink" web_app/src` and read each
  declaration's *property*, not its selector — `color` on a `.q-icon`, any
  `border-color`, any `background` on a bar, and any text measured at >= 24px
  or >= 18px bold all belong on `--accent-mark`.
- **Why deferred:** the remaining sites are lower-visibility and the pass had
  four other owner items in it. No defect either way — the ink tier is legal
  everywhere, just darker than necessary.
- **Recommended resolution:** opportunistic, whenever a surface is next
  redesigned. Cross-ref: D-002, R-069.

## [OPEN] FU-849 — Planned demand isn't on the shopping list yet
- **Raised:** 2026-09-03 (owner batch — planned-demand signal)
- **Type:** deferred job
- **What:** D-10 (2026-08-19) says a derived signal belongs on *"the two
  surfaces the user opens to ask"* — the stock-item detail card and the
  shopping list. Planned demand shipped on the first. The second is arguably
  where it pays off most: *"3 planned meals need this by Friday"* on a line you
  are deciding whether to tick is a stronger argument than the same sentence on
  a page you had to go looking for.
- **Why deferred:** the shopping list has its own line model, its own gating
  and its own crowded row, and the owner asked about the *belief metric*, not
  about the list. Adding it there is a design call about that row, not a
  mechanical extension — the signal, the endpoint and the client cache are all
  already there.
- **Recommended resolution:** later, when the shopping-list surface is next
  open. Cross-ref: ADR-071, D-10.

## [OPEN] FU-848 — Two segmented-control components draw one anatomy
- **Raised:** 2026-09-03 (owner batch — inconsistent single-select rows)
- **Type:** finding (D-015 / R-001)
- **What:** the app has **two** implementations of the single-select row of
  buttons. `BaseSegmented` wraps Quasar's `q-btn-toggle` (nineteen consumers);
  `settings/DoraSegmented` is a hand-rolled radiogroup (seven, after this pass
  converted the last two raw `q-btn-toggle`s onto it). As of 2026-09-03 they
  render the **same** anatomy, and can't drift on colour or shape because both
  read the shared `--seg-*` tokens — but they are still two components, and
  nothing stops the next change landing on one of them.
- **Which one should survive, and why it isn't obvious:** the hand-rolled one
  has the better bones — real `radiogroup`/`radio` semantics, wraps on desktop
  and scrolls horizontally on phones (which the five-option font-family picker
  needs), and none of the `!important` fights `BaseSegmented`'s stylesheet
  documents against Quasar's `.text-primary` utility. But it is the *minority*
  by call sites, and the nineteen `BaseSegmented` consumers pass Quasar props
  (`dense`, `size`, `spread`) that would become inert, plus one passes a
  default slot. So the merge is a ~25-file change with real layout risk, not a
  rename.
- **Why deferred:** the owner's ask was visual consistency, which is delivered.
  Doing the structural merge in the same pass would have meant 25 unverified
  call sites inside a five-item batch.
- **Recommended resolution:** later, as its own unit. Cross-ref: D-015, R-001.

## [OPEN] FU-847 — Four hosts now measure their own box to size the SVG chart
- **Raised:** 2026-09-02 (FU-833 — dropping ECharts)
- **Type:** finding (R-001)
- **What:** `PriceHistoryChart` is sized in **px**, not by CSS, so every host
  measures its own content box with a `ResizeObserver` and passes `:width`.
  ECharts' `autoresize` did this internally; losing it is the one thing the swap
  cost. The same ~12 lines (`measure()` + observer + `onBeforeUnmount` cleanup)
  now exist in **four** places: `PriceHistoryPage.vue`,
  `PriceHistoryBottomSheet.vue`, `reports/PriceTrendsCard.vue` and
  `reports/ItemPriceMoversCard.vue`. Two of them differ slightly and for real
  reasons (one subtracts card padding, one re-attaches when the host appears as
  the card leaves its empty state), which is exactly how a fourth copy becomes a
  fifth that is subtly wrong.
- **Two ways out, and the second is better:** extract `useMeasuredWidth(elRef)`;
  or teach the chart to fill its container (a `viewBox` + `width: 100%` and
  internal coordinates in a fixed space), which deletes the prop and the
  observers together. The second is a change to the chart's coordinate handling
  and wants its own unit, since `preserveAspectRatio="none"` currently means a
  CSS-scaled SVG would distort (already noted in
  `PRICES_SURFACE_UX_ASSESSMENT.md` §5.5).
- **Why deferred:** ADR-070 called it at the third and fourth copies and chose to
  ship the swap rather than widen it. Not urgent: the copies work, and they were
  driven live on all four surfaces.
- **Recommended resolution:** opportunistic — with [[FU-705]] (the chart's
  missing touch interaction), since both are changes to the same interaction
  layer. Cross-ref: ADR-070, R-073, R-001.

## [OPEN] FU-846 — `/price-history`'s per-product cards still read `seriesColour(i)` by list position
- **Raised:** 2026-09-02 (FU-833)
- **Type:** finding
- **What:** the chart assigns a series' colour by its index in the array it is
  handed; `PriceHistoryPage.vue` colours its picker chips and comparison cards by
  calling `seriesColour(i)` with the index of *its own* `series` array. Those
  agree today only because `productSeriesToChart` preserves order 1:1. The moment
  the chart drops a series with no plottable points — which it already does,
  `plottable` filters them — the chart's index and the page's index diverge, and
  a chip is painted the colour of a different product's line. Not currently
  reachable: the page only lists products the API returned series for, and a
  series with zero points still renders a card. It is a latent off-by-one, not a
  live defect.
- **The fix is to key the colour, not the position:** have the adapter stamp each
  `PriceChartSeries` with its resolved colour, and let both the chart and the
  page read `series.colour`. That also kills the "call it inside a reactive
  scope" caveat on `seriesColour`, since the value would be computed once where
  the array is built.
- **Why deferred:** it is not reachable from the current UI, and the fix touches
  the colour contract for all four consumers — worth doing deliberately rather
  than inside the ECharts removal.
- **Recommended resolution:** opportunistic, or with [[FU-843]] item 1 (the
  categorical ramp's collision), which is the same "who owns a series' colour"
  question. Cross-ref: R-073, `useThemePalette.seriesColour`.

## [OPEN] FU-845 — One of §4.10's ten design moves is still unbuilt (#8, "every number is a door")
- **Raised:** 2026-09-02 (Reports chunk 3 close-gate)
- **Type:** deferred job
- **#2 DONE 2026-09-02 (chunk 5).** The range control names its window ("3 Aug –
  2 Sept"), from a new ungated `GET /reports/range-window` — the window is a
  property of the **range parameter**, not of any report, so it is one endpoint
  rather than a field on nine responses. It **removed** an R-003 duplication
  instead of adding one: the client's `RANGE_TO_DAYS` table was a second copy of
  the server's `_RANGE_DAYS`, kept only to feed the waste endpoint its day count,
  and is deleted. Driving it caught a defect in the label itself — the 1-year
  range rendered *"2 Sept – 2 Sept"* because the formatter dropped the year, so
  the control built to make the window concrete claimed a one-day window; the
  year now renders whenever the window crosses one. Only **#8** remains.
- **What:** `REPORTS_PAGE_REVIEW.md` §4.10 lists ten moves; chunk 3 built eight
  of them; chunk 5 built #2 (above). The one left:
  - **#8 — every number is a door.** N6 asked for this and it has never been
     built: a store row should filter shopping-list history to that store, a
     group row should open Stock filtered to that group, the wastage count
     should open the waste log. Chunk 3 landed the *cheap* half — recipe and
     stock-item rows in Kitchen memory are links now — so what remains is the
     aggregate rows, each of which needs a target route that accepts the filter.
- **Why deferred:** #8 is in neither chunk's brief, and its real cost is in the
  *destination* pages accepting a filter param, not in Reports at all.
- **Recommended resolution:** later — #8 on its own, since it touches three
  other pages. Cross-ref: `REPORTS_PAGE_REVIEW.md` §4.10 #8, [[FU-703]].

## [OPEN] FU-844 — Two pages have now shipped the same feature-flag race; the guard should be the composable's job
- **Raised:** 2026-09-02 (Reports chunk 1 — found by driving it live)
- **Type:** finding (R-003-adjacent)
- **What:** a gated loader written as `if (!moneyEnabled.value) return;` is a
  **race**, not a gate. `useFeatureFlags` reads `/api/health` once per document
  and the map is empty until that resolves, so on a cold load every gated loader
  early-returns and nothing re-runs it — the card then renders its *empty* state
  forever, which is the honesty failure the whole error-state chunk exists to
  kill. The dashboard hit this and fixed it with per-gate `watch`ers (**FU-586**,
  and the comment there explains it well); `ReportsPage.vue` reproduced it
  verbatim on its first live run — only the three ungated reports fetched, and
  the six money cards said "no completed shopping lists" on a seed with five
  stores of spend. Fixed the same way, so there are now **two** copies of the
  workaround and any third gated page will write a third.
- **The shape of the fix:** `useFeatureFlags()` already tracks `flagsLoaded`.
  Either expose the load promise (`await flagsReady()`) so a page can simply not
  fetch until the answer exists, or give the composable a `whenEnabled(flag, fn)`
  that owns the watcher. Either way the knowledge — *"a false flag might mean
  'not yet'"* — stops living in each caller.
- **Why deferred:** it is a small refactor across two pages plus the composable,
  and both call sites are correct today; doing it inside a defect chunk would
  widen the diff for no user-visible change.
- **Recommended resolution:** opportunistic — with [[FU-832]] (the shared card
  catalogue + `useCardLayout()`), which is already touching exactly this seam on
  both pages. Cross-ref: FU-586, `DashboardPage.vue:1629`, `ReportsPage.vue`.

## [OPEN] FU-843 — Reports' categorical colour ramp collides at six entries, and the no-store bucket has no hatch
- **Raised:** 2026-09-02 (Reports chunk 2 — measured live)
- **Type:** finding (D-001)
- **PARTIALLY DONE 2026-09-02 (Reports chunk 3). Item (2) is closed; item (1)
  survives but is smaller than it was.**
  - **(2) done** — the donut is gone and both spend axes render
    `ProportionBar`, **extracted from `StoreSpendCard.vue`** so the hatch, the
    zero-value floor and the unassigned bucket are one implementation rather
    than a second copy (R-001). Verified live: the no-store segment computes
    `repeating-linear-gradient(...)` over `--border-strong`, and its legend
    swatch is hatched to match — parity with the shopping list, not a lookalike.
  - **(1) still open, and downgraded** — `colourFor` still hashes into a sealed
    `--chart-1..6`, so two stock groups can still share a hue. What changed is
    that **colour is no longer the channel that ties a value to a name**: the
    donut it labelled is gone, and each group is now a labelled row carrying its
    own name, dollar figure and share. The collision went from misleading to
    cosmetic. The fix is still to rank-assign rather than hash.
- **What:** two related colour problems on the two legends, both visible on the
  dense seed at :5171.
  1. **`colourFor` hashes into `--chart-1..6`, so with more than a handful of
     buckets two adjacent rows share a hue.** Measured: "Pantry staples" and
     "Fruit & Veg" both render `rgb(249,208,6)` in the spend-by-category legend.
     Harmless-looking, but the legend's whole job is to tie a slice to a name.
     Stock groups routinely run to eight or more, which is also §4.6's argument
     for killing the donut outright.
  2. **The "No store set" bucket is drawn as a flat colour.** The shopping list
     solves the same bucket with a **hatched** themed grey, precisely because no
     flat grey can be guaranteed to separate from a logo-derived brand colour
     (D-001 — never distinguish by hue alone). Chunk 2 stopped it being handed a
     *store identity* colour (it was drawing the same slate as the farmers market
     directly above it) and gave it `--text-muted`, which is honest but is not
     parity.
- **Why deferred:** the real fix for both is §4.6's — replace the donut + legend
  with the shopping list's own `.sl-store-bar`, which already solves the
  zero-value bucket, the unassigned bucket **and** the hatch. Building a second
  hatch here would be the third copy of a component the review wants shared.
- **Recommended resolution (amended):** item (1) opportunistically, with
  chunk 5's colour sweep, or [[FU-846]] — which is the same "who owns a series'
  colour" question, and the better home now that [[FU-833]] has shipped. It is a
  cosmetic ranking change, not a legibility defect. Cross-ref:
  `REPORTS_PAGE_REVIEW.md` §4.6, `components/ProportionBar.vue`.

## [OPEN] FU-841 — `MarkAsWastedDialog`'s tiles remove the focus outline and replace it with their hover state
- **Raised:** 2026-09-02 (dashboard chunk 6 — found while fixing the same file's
  undeclared `--c-*` references, which the R-060 guard surfaced)
- **Type:** finding (A6 / D-016)
- **What:** `components/stock/MarkAsWastedDialog.vue` styles its reason tiles with
  a single `:hover, :focus-visible` rule that sets `outline: none` and changes the
  background + border colour. Two problems, the same pair `PantryDonutCard` had
  before chunk 6 fixed it there: **A6 forbids `outline: none` without a
  replacement**, and because hover and focus share one rule the two states are
  **byte-identical**, which D-016 requires be distinguishable. A keyboard user
  tabbing through the tiles gets the same feedback as a mouse hovering, and no
  ring.
- **Not fixed in chunk 6** — different surface (stock, not the dashboard), and the
  chunk only touched this file because retiring the dashboard's `--c-*` aliases
  made the R-060 guard fail on its undeclared token references. Fixing the focus
  ring too would have been scope creep into a dialog nobody was reviewing.
- **The fix is known and small**: split the rule, keep the background change on
  hover, and give `:focus-visible` a real `outline: 2px solid var(--focus-ring)`
  with an offset — copy `PantryDonutCard.vue`'s, which is the worked example.
- **Worth checking in the same pass:** how many other `outline: none` rules exist
  app-wide. The dashboard review counted one on its own surface; nobody has
  counted the rest.
- **Recommended resolution:** **opportunistic** — next time anyone is in the stock
  dialogs, or as part of an app-wide focus-ring pass alongside [[FU-631]].

## [OPEN] FU-834 — 20 undeclared design tokens app-wide, incl. two in the file R-060 was written from
- **Raised:** 2026-09-02 (dashboard chunk 1 — found by the new R-060 guard test)
- **Type:** finding (R-060)
- **What:** fixing the dashboard's two undeclared token families ([[FU-822]])
  warranted a test rather than a review habit, so
  `web_app/test/unit/designTokensDeclared.spec.ts` now walks every `var(--x)` in
  `src/` and asserts the property is declared in `css/` (or is runtime-written —
  `--q-*` by Quasar, `--dora-base-font-size` by `themeService.ts:412`). **On its
  first run it found 21**; one was fixed in passing (`--surface-card` in
  `TriStateFilter.vue`, a file the sweep already touched), leaving **20**
  enumerated in that spec's `KNOWN_UNDECLARED` ratchet with their call sites:
  `--space-sm`, `--space-xs`, `--surface`, `--surface-base`, `--surface-border`,
  `--surface-card`, `--surface-default`, `--surface-hover`, `--surface-muted`,
  `--surface-raised`, `--text-md`, `--text-sm`, `--text-xs`, `--text-warning`,
  `--font-mono`, `--overlay-pressed`, `--negative`, `--stock-row-height`,
  `--c-surface-2`, `--c-surface-3`, `--c-line-strong`.
  Every one is R-060's named smell — reaching for a name that *looks* like the
  scale (`--space-sm` where the scale is `--space-1..12`; `--surface-card` where
  the token is `--surface-component`). Affected surfaces include HelpPage,
  AccountSettings, ApiAccessSettings, StocktakeRunner, StockItemDetailPage,
  ShoppingListDetail, PutAwayDialog, RecipeNutriScore, VoicePicker.
- **The finding worth reading twice:** `RecipeCookMode.vue:19` references
  **`--space-sm` and `--space-xs`**, and cook mode's header is the **exact case
  that established R-060** on 2026-08-28 — the rule exists because that header
  was reported three separate times as "squished" / "no margin" / "looks like a 5
  year old did it" before anyone checked whether its gap tokens resolved to
  anything. Two of them still don't. The rule was written; the file was not
  finished.
- **Why deferred:** ~30 call sites across ~20 unrelated files, none of them the
  dashboard. Folding an app-wide CSS sweep into a dashboard chunk is exactly the
  scope bleed R-007 forbids, and each fix needs a judgement about *which* real
  token was meant (an invalid `background` silently inherits, so some of these
  have been visually "fine" by accident and will change appearance when fixed).
- **The guard means this cannot get worse:** a *new* undeclared token fails the
  suite, and the ratchet's second assertion fails if a listed token is fixed
  without being removed from the list, so the allowlist can't rot into a
  permanent exemption.
- **Recommended resolution:** opportunistic per-file — when you're next in one of
  those files, fix its entry and delete it from `KNOWN_UNDECLARED`. Or one
  dedicated sweep unit; either way the test tells you when you're done.

## [OPEN] FU-832 — One flat card catalogue + an extracted `useCardLayout()`, shared by the dashboard and Reports
- **Raised:** 2026-09-02 (owner decision on [[FU-809]])
- **Type:** deferred job (decided, not started)
- **What:** the owner resolved FU-809 as **share a flat catalogue plus the
  machinery — but not the card bodies.** Measured overlap: after [[FU-830]] the two
  surfaces share **five endpoints** (`savings-captured`, `spend-by-store`,
  `stock-value`, `price-drops`, `keeps-running-out`) and **no presentation** — the
  dashboard's cards are glance-sized, Reports' are full-size with range controls.
  So:
  1. **A flat data table** keyed by card id declaring `gate` / `label` / `icon` /
     `endpoint`, consumed by both surfaces, each picking which entries it renders
     and at what density. **Explicitly a table, not a plugin architecture or an
     abstraction layer** — the constraint the owner attached, and the right one for
     a hand-maintainable codebase. Resist a `render:` field or per-card component
     registry; the surfaces keep their own bodies and just look ids up.
  2. **Extract `useCardLayout()`** from `DashboardPage.vue:1473-1653` — visibility,
     within-zone order, the tap/drag reorder, and the server-persisted layout on
     `user.dashboard_layout`. Reports gets it too, which is what finally answers
     "Reports has too many widgets" with *the user decides* rather than a cut list.
     Note the persistence key: Reports' layout must not collide with the
     dashboard's on the same `User` column — either a second column or a namespaced
     payload (`{dashboard: {...}, reports: {...}}`), which is a migration decision
     to make inside this unit.
  3. **The `DashboardCard` shell** was [[FU-814]]'s job and is **done** (Reports
     chunk 3, 2026-09-02) — all four Reports cards render `<DashboardCard>`, so
     this FU just consumes it.
  **The concrete R-003 win:** the money/products **gate facts stop being declared
  twice** — today they are declared once on the dashboard and *zero* times on
  Reports, which is precisely why [[FU-816]] exists.
- **Why deferred:** it is an architecture change across two large pages and it
  wants both restructures ([[FU-830]] here, Reports chunk 3) to have settled which
  cards exist first — extracting a catalogue of cards that are about to be merged
  or cut is the same mistake the dashboard rebuild avoided in its Phases 0/1.
- **Do NOT block [[FU-816]] on this.** Adding the money/products gates to Reports
  is a live contradiction with feedback L254 and ships standalone in Reports
  chunk 1; the catalogue later moves those declarations, it does not need to
  introduce them.
- **Recommended resolution:** later — **both gating restructures have now
  landed** (FU-830 on the dashboard; Reports chunk 3 on 2026-09-02, which settled
  the card set at four), so the blocker this FU was waiting on is gone.
  Cross-ref: `REPORTS_PAGE_REVIEW.md` §3.2 + §8 D1, [[FU-809]] (resolved),
  [[FU-814]], [[FU-830]].

## [OPEN] FU-831 — Savings gets an own-price baseline: snapshot column, tense split, reseed (ADR-068)
- **Raised:** 2026-09-02 (owner decisions on the two page reviews)
- **Type:** deferred job (decided, not started)
- **What:** implement **ADR-068 / R-071**. The owner resolved [[FU-810]] as *keep
  the card, change the baseline*, and two follow-on calls set the app-wide scope:
  1. **Snapshot column.** Add a pick-time `usual_price_at_pick` (name TBD) beside
     `list_price_at_pick` on `ShoppingListLine`, written on the same finish-shop
     path that writes `picked_offer_price`. It must be a snapshot: deriving the
     household's usual price retroactively would make every past shop's savings
     move each time a price is logged — the failure the existing design avoids.
     Migration must stay Postgres/SQLite portable (§7.5) with a deterministic
     constraint name (R-015).
  2. **Retrospective handler onto the new baseline.** `SavingsCapturedHandler`
     (`reports.py:774-843`) currently sums `list_price_at_pick − picked_offer_price`.
     Move it to the own-price baseline, and **rename the DTO field to name its
     baseline** (`savings_vs_usual_price`, not `savings` / `total_savings`) per
     R-071.
  3. **R-041 coverage, replacing a silent zero.** The handler's current
     "no RRP snapshot ⇒ fall back to the picked price ⇒ contribute 0 savings"
     branch (`:814-820`) is not acceptable under the new baseline: an item with no
     price history has *no* baseline, which is a named gap, not zero savings. Ship
     `counted` / `total` alongside the figure and render the coverage whenever the
     number renders.
  4. **Spend becomes the headline** on the card, savings the support line — on both
     `/reports` and the dashboard's Money card.
  5. **Tense split, both halves labelled.** Live in-list savings **keep** the
     vs-shelf-price baseline — `ShoppingListDetail.totals.total_savings`,
     `ShoppingListOverviewCard.vue:496`, the primary-list card stat
     (`DashboardPage.vue:396`), and the per-line model (`shoppingList.ts:282`) are
     all correct as computations but must **stop rendering a bare "saved"**: they
     say "under shelf price", the report says "less than you usually pay".
  6. **Reseed, don't backfill.** No back-fill for already-archived lists; regenerate
     the dev/demo dataset (`seed.py` / `seed_dense.py`) so the metric is coherent
     from its first row. Pre-release, no real users — clean non-preserving migration
     is allowed. R-017: the seed change ships with this.
- **Why deferred:** it is a schema + write-path + handler + copy change across three
  surfaces, and it is the only item out of the two reviews that needs a migration.
  Everything else can ship around it.
- **Sequencing note:** do **not** block [[FU-830]] on this. Land the Budget/Savings
  card merge against the existing figure and let this FU swap the number underneath;
  only the card's final copy depends on it. `DASHBOARD_PAGE_REVIEW.md` §7 Chunk 3b.
- **Recommended resolution:** later — its own unit, parallel to the dashboard
  chunks. Cross-ref: ADR-068, R-071, R-041, [[FU-810]] (resolved), and
  `REPORTS_PAGE_REVIEW.md` §3.7 / `DASHBOARD_PAGE_REVIEW.md` §3.5.

## [OPEN] FU-839 — `BaseSegmented`'s selected segment is under the contrast floor, and two consumers may render it invisible
- **Raised:** 2026-09-02 (dashboard chunk 3 — found by introducing the bug myself)
- **Type:** finding (D-002)
- **Two separate things, both measured or code-evidenced:**
  1. **App-wide: the selected segment measures 3.88:1.** `BaseSegmented` forces
     `color: var(--text-on-primary) !important` on `[aria-pressed='true']` (it
     has to, to beat Quasar's `.text-primary !important`), and Quasar paints
     `--brand-primary` behind it. Measured in the pesto light theme:
     `rgb(255,255,255)` on `rgb(37,147,92)` = **3.88:1**. D-002 requires **4.5**
     for normal text and allows 3:1 only for large text (≥24px, or ≥18px bold);
     these labels are small, and the dashboard's are `dense size="sm"`. So every
     selected segment in the app — **9 call sites** — is under the floor. Not
     introduced here; the dashboard's two new toggles now match the other seven.
     The fix is a shared decision (a darker ink token for use on brand-primary
     fills, or bumping the fill's lightness), which is R-069's shape: a colour
     tuned as a *fill* is not automatically usable as a *background for white
     ink*.
  2. **Two `flat` consumers appear to have no fill at all** —
     `PriceHistoryPage.vue:84` and `RecipeCookMode.vue:667` pass `flat` and,
     unlike `TriStateFilter.vue:294`, declare no
     `:deep(.q-btn[aria-pressed='true']) { background: … }` rule. `flat`
     suppresses Quasar's fill, so the forced white ink lands on whatever surface
     is behind it. On the dashboard that measured **1.21:1 — invisible** before I
     removed `flat`. **Not confirmed on those two surfaces** (per the
     reported-defect rule): cook mode may sit on a dark ground where white works,
     and price history needs a product selected to reach. Confirm before fixing.
- **Why this is worth a rule-shaped look:** `BaseSegmented`'s own header comment
  documents this exact trap ("In `flat` mode, where the caller paints its own
  brand-primary fill…") and it still caught me, because nothing *enforces* the
  pairing — `flat` is just an attr passed through to Quasar. A component whose
  correct use depends on the caller also painting a fill should either paint it
  itself or refuse `flat` without one.
- **Recommended resolution:** (2) first — it is a possible invisible control on
  two surfaces, and confirming is a five-minute browser check. (1) with the
  chunk-6 design sweep or a deliberate contrast pass, since it restyles nine
  controls. Cross-ref: D-002, R-069, B2a, `BaseSegmented.vue:49-66`.

## [OPEN] FU-838 — Cutting Best deals orphaned an endpoint, a client method and a helper
- **Raised:** 2026-09-02 (dashboard chunk 3 — [[FU-819]]'s cut)
- **Type:** leftover
- **What:** the Best-deals card was the **only** consumer of three contracts, all
  now unreferenced by the SPA:
  - `productApiService.getBestDealsAsync(limit)` (`productApiService.ts:18`) and
    the `/products/best-deals` endpoint behind it — a server-side ranked+sliced
    query written for exactly this card (state-ownership §8.2).
  - `helpers/scrapedProductOfferLogic.discountPercent()` — grepped app-wide,
    **zero** callers now. Note the review and ADR-068 both say this "survives as
    a per-offer display helper"; that is a statement about it being *legitimate*
    (one offer's % off its own ticket is a shelf-price question), not about it
    having a consumer. It has none.
- **Why deferred:** R-057/ADR-054 is explicit that a replaced surface's contracts
  are an inventory to check, not a casualty list — deleting a live endpoint plus
  its tests is a bigger call than a UI chunk should make unilaterally. There is
  also a plausible future consumer: the `/reports` restructure keeps a deals
  angle, and FU-831's own-price baseline work may want a per-offer discount.
- **Recommended resolution:** opportunistic — owner's call. Delete all three, or
  keep `discountPercent` with a note saying why and retire the endpoint. Same
  shape as [[FU-766]] (the shopping list's orphaned `bulk-tick` +
  `has_substitutes`), and worth deciding together.

## [OPEN] FU-837 — A short dashboard card stretches to its tall row-mate, which reads as dead space
- **Raised:** 2026-09-02 (dashboard chunk 2 — seen in the verification screenshot)
- **Type:** finding (design)
- **What:** cards in a row stretch to the tallest (the default `align-items:
  stretch`, plus `DashboardCard`'s own `height: 100%`). Measured at 1440px on the
  dense dataset, "Draft this week's shop" — three lines of copy and a button — is
  stretched to match "Needs your attention" beside it, leaving roughly **180px of
  empty card** below its button. This is *not* the D-011 dead-grid air chunk 2
  fixed (that row is 100% used); it is empty space *inside* a card, which arguably
  reads worse because the card's border draws a box around it.
- **Why it isn't just "set `align-items: flex-start`":** equal-height cards are
  what makes the zone bands read as tidy rows; natural heights give a ragged
  bottom edge on every row. Both are defensible, so it is a design call — and it
  interacts with [[FU-830]], which changes who sits next to whom. There is also a
  middle option: centre the short card's *content* vertically instead of
  top-aligning it, filling the box without touching the grid.
- **Recommended resolution:** later, with `DASHBOARD_PAGE_REVIEW.md` §7 Chunk 6
  (the design sweep), once Chunk 3 has settled the card pairs. Cross-ref: B4,
  D-011, [[FU-631]] #3.

## [OPEN] FU-836 — `col-lg-*` does not mean "desktop", and the dashboard was the surface that assumed it did
- **Raised:** 2026-09-02 (dashboard chunk 2 — found while measuring [[FU-631]] #3)
- **Type:** finding (A8 / breakpoint discipline)
- **What:** the design guide (A8) defines **desktop as ≥1024px**. Quasar's grid
  breakpoints are `xs <600 · sm ≥600 · md ≥1024 · lg ≥1440 · xl ≥1920`, so the
  class meaning "from the app's desktop up" is **`col-md-*`**, not `col-lg-*`.
  `quasar.config.ts` sets no override — checked; the defaults apply. The dashboard
  was the one surface reaching for `col-lg-*` (**2** usages app-wide against
  **14** for `col-md-*` and 25 for `col-sm-*`), and the consequence was
  measurable: its `col-lg-6` / `col-lg-4` / `col-lg-8` classes **did nothing below
  1440px**, so on an ordinary 1280px laptop "Needs your attention" and "The week
  ahead" rendered **full-width** — neither carried a `col-sm-*` step — while every
  other card was already half. Almost certainly not the intent, and it is why the
  review's "five dead regions on a default desktop" was wrong below 1440 (two
  there).
- **Already handled:** the dashboard no longer uses `col-lg-*` at all (chunk 2),
  and `helpers/dashboardGrid.ts` carries a ⚠️ comment naming the trap so it isn't
  re-added.
- **What's left:** the remaining `col-lg-*` call site in `src/` (2 total, one was
  the dashboard's — worth one grep), and a decision on whether A8 should say this
  out loud. A8 lists the app's breakpoints without noting that Quasar's `lg` is
  *not* one of them, which is precisely the gap that produced this; a one-line
  note ("the class for the app's desktop tier is `col-md-*` — Quasar's `lg` is
  ≥1440") is cheaper than any amount of review.
- **Recommended resolution:** opportunistic — a two-minute A8 edit next time
  anyone is in `DESIGN_STYLE_GUIDE.md`. Cross-ref: A8, `DASHBOARD_PAGE_REVIEW.md`
  §4.6 correction.

## [OPEN] FU-808 — `space` and `u` are advertised in the shortcut cheatsheet on faces where they do nothing
- **Raised:** 2026-09-01 (v4 chunk 4 — cutover audit)
- **Type:** finding
- **What:** `useShortcut` registers all five shopping-list shortcuts
  unconditionally (`ShoppingListDetail.vue:2112`), but `tickFocusedLine` and
  `untickLastTicked` both guard on `detail.status !== 'shopping'` and return
  immediately. The gate is **correct** — v3 deliberately removed draft ticking,
  and it was verified live that a draft cannot be ticked by keyboard. The problem
  is only that the `?` cheatsheet promises *"space — tick / untick the focused
  line"* on the plan and receipt faces, where pressing it does nothing at all.
- **Why deferred:** it is an honesty defect, not a functional one, and the fix
  touches how `useShortcut` scopes registrations (register conditionally, or let
  a shortcut declare an `enabled` predicate the cheatsheet reads) — a shared-
  composable change that shouldn't be made inside a shopping-list audit.
- **Recommended resolution:** opportunistic — next time `useShortcut` /
  `ShortcutsCheatsheet` is open. Cheap alternative if that never happens: gate
  the two registrations on the run face.

## [OPEN] FU-805 — receipt line reads "estimated, no price entered" while showing a price
- **Raised:** 2026-09-01 (v4 chunk 3 — shopping-list receipt face)
- **Type:** finding
- **What:** On the receipt face, a line whose `estimate_source` is `historic`
  renders the caption "estimated, no price entered" *and* an amount (e.g.
  "~$3.00"). Both halves are true from the code's point of view — the price is
  an estimate carried over, and the user never typed one — but read together
  they contradict each other. Pre-existing copy (baseline E3), carried across
  chunk 3 verbatim rather than reworded, because rewording it is a copy decision
  and not this chunk's call.
- **Why deferred:** scope discipline; the "~" prefix already carries the
  estimate signal, so the caption may want to be dropped rather than reworded,
  and that's a decision, not a fix.
- **Recommended resolution:** now-ish — it is one line of copy and the owner is
  looking at this surface. Suggested: drop the clause entirely and let "~" do
  the work, or say "estimated from what you last paid".

## [OPEN] FU-802 — the planner's rail row is still the third copy of the list-row chrome (see FU-791)
- **Raised:** 2026-09-01 (meal-planner owner batch)
- **Type:** finding
- **What:** not a new problem — a note that this batch touched
  `MealPlanRecipeRow.vue` (removed its meta line and the log-cook button,
  restyled the pool controls) **without** taking the `.dora-list-row` extraction
  [[FU-791]] asks for. The R-001 carve-out comment in that file is still accurate
  and still the third copy.
- **Why deferred:** same reason as FU-791 — the extraction re-skins `StockItemRow`
  and `RecipeRow`, two surfaces the owner has signed off visually, and this unit's
  scope was the planner.
- **Recommended resolution:** opportunistic, with FU-791 — this entry exists only
  so the next reader of FU-791 knows the file moved since it was written.

## [OPEN] FU-801 — `--brand-primary` fails the same ink test as the accent did (R-069)
- **Raised:** 2026-09-01 (accent-ink sweep)
- **Type:** finding
- **What:** measured while fixing the accent. As *ink* on its own theme's
  component/page surfaces, `--brand-primary` lands at **1.63:1** (lemon-tart),
  **2.34:1** (sourdough), **3.89:1** (pesto) and **4.01:1** (blueberry) — only
  cherry-cola clears 4.5. Same class of bug as the accent, same fix shape
  (`--primary-ink` + split call sites by ground, per R-069).
- **Why deferred:** different size of job. The accent was consumed through CSS
  vars at ~20 sites, so it was a contained sweep. Primary is consumed
  overwhelmingly through Quasar's own `color="primary"` / `text-primary`
  machinery (buttons, chips, icons, links) rather than through `var(--…)`, so
  fixing it properly means deciding how the ink token reaches Quasar's classes —
  not a change to bolt onto an owner-feedback batch.
- **Impact check first:** many `color="primary"` sites are *fills* (a solid
  button paints `--text-on-primary` over it) and are perfectly fine. The job
  starts with an inventory of primary-as-ink sites, not with a blanket swap.
- **Recommended resolution:** later, as its own unit — pair it with the next
  theme/contrast pass.

## [OPEN] FU-800 — the burger glyph wants an eyes-on pass at 12–14px
- **Raised:** 2026-09-01 (Dora-voice icon unification)
- **Type:** follow-up
- **What:** every "Dora thinks…" / "Dora suggests…" surface now draws
  `ICONS.dora_voice` (`mdi-hamburger`, the mascot). Verified rendering live at
  22px in the attention-rules dialog. The small sizes (12px on the meal-plan
  rail chip and the shopping-list note, 14px in chat and the plan row, 16px in
  the stock row) were not seen at paint — the browser pane doesn't composite.
- **Why deferred:** it's an aesthetic call only the owner can make, and it needs
  a real browser. The risk to look for is a 12px burger reading as a hamburger
  *menu*; `mdi-menu` is three bars and the two never appear together, so this is
  a legibility question rather than a correctness one.
- **Recommended resolution:** now-ish — walk the DORA_VERIFY "Dora's voice"
  checklist. If the small sizes are mushy, the fallback is a size floor
  (14px) on this glyph rather than a different icon.

## [OPEN] FU-799 — sweep the other prose-parsed domain facts (R-068)
- **Raised:** 2026-09-01 (cook-mode feedback batch)
- **Type:** follow-up
- **What:** cook mode's step timer was recovered by regex from the step's text;
  it now reads a real `RecipeStep.timer_minutes` and labels the fallback as
  inferred. Generalised as **R-068**. The same instinct is available anywhere
  the schema is thinner than the feature — the nearest neighbour is the recipe
  importer's serving/time/quantity parsing (`_parse_recipe_from_text.py`), which
  is arguably *fine* under R-068's non-goal (it proposes, the user confirms),
  but has never been checked against it. Grep for regexes over `.text` /
  `.notes` / `.instructions` and confirm each one either only affects
  presentation, or proposes-and-confirms, or is labelled.
- **Why deferred:** out of scope for a cook-mode feedback batch, and each hit
  needs its own read of whether it drives behaviour or just presentation.
- **Recommended resolution:** opportunistic — next time the importer is open.

---

## [OPEN] FU-798 — sweep the other full-page surfaces for a pinned-palette shell (R-067)
- **Raised:** 2026-09-01 (stocktake feedback batch)
- **Type:** follow-up
- **What:** the stocktake runner pinned its shell to `--palette-neutral-900`
  under every theme; that's now fixed and generalised as **R-067**. The same
  instinct is available to any other route-level "focus mode". Grep
  `background: var(--palette-` across `web_app/src/pages` + `src/components`
  and check each hit against R-067 — cook mode and the shopping-list run face
  are the named candidates.
- **Why deferred:** out of scope for a stocktake feedback batch, and each hit
  needs its own look at whether the surface is genuinely inverted-by-design (a
  scrim, a toast) or just hard-coded.
- **Recommended resolution:** opportunistic — next time either surface is open.

---

## [OPEN] FU-797 — the Firefox-mobile login line is mitigated, not confirmed fixed
- **Raised:** 2026-08-31 (recipe-view feedback batch)
- **Type:** finding
- **What:** owner reported a thin grey vertical line, roughly the mascot's
  height, immediately left of it on the login screen, flickering for a few
  seconds then settling — **Firefox on Android only, Chrome clean**. It can't
  be a DOM element (nothing is drawn there, and anything that was would render
  in Chrome too), so it's read as the left edge of the mascot's own composite
  layer: `drop-shadow` + an animated `transform`, promoted to a GPU layer while
  the blurred `mix-blend-mode: screen` blobs behind it are still rasterising.
  `will-change: transform` + `backface-visibility: hidden` now declare that
  promotion up front (`AuthShell.vue`, commented in place).
- **Why deferred:** **not reproduced.** Playwright's Firefox isn't installed on
  this box and the system Firefox can't be driven (no Juggler); a mobile-GPU
  compositing artifact wouldn't reproduce on desktop Firefox regardless. The
  fix is reasoned, not observed.
- **Recommended resolution:** confirm in browser — on the reporting device
  (Firefox, Android). See `DORA_VERIFY.md`. If it survives, the next lever is
  dropping the mascot's `drop-shadow` filter, which is what creates the layer.

## [OPEN] FU-796 — `.page-counts-footer` overflows a 375px viewport by 8px on /my-products
- **Raised:** 2026-08-31 (recipe-view feedback batch — the "where else?" sweep)
- **Type:** finding
- **What:** swept all 13 main routes at 375px for horizontal page overflow while
  answering the owner's *"where else might this be an issue?"*. Twelve are clean;
  `/my-products` overflows by **8px**, and the offender is
  `PageCountsFooter.vue`'s `margin: 16px -16px -16px` outdent — it assumes the
  page wrapper's padding is 16px per side, and on this page it isn't, so the
  bar comes out 391px wide in a 375px viewport. D-011 (no page h-scroll).
- **Why deferred:** unrelated to the recipe surface this batch was scoped to,
  and the footer is shared — the fix wants checking on every page that mounts
  it, not just this one.
- **Recommended resolution:** opportunistic — next time anything touches
  `PageCountsFooter` or the My Products page.

## [OPEN] FU-795 — two chip selects bypass `BaseSelect` and so miss every rule it owns
- **Raised:** 2026-08-31 (recipe-view feedback batch)
- **Type:** finding
- **What:** `ReportsPage.vue` (the price-picker) and
  `settings/AuditLogSettings.vue` (the severity filter) use a raw `q-select`
  with `multiple use-chips` rather than `BaseSelect`. They therefore miss
  everything BaseSelect exists to decide — the menu-vs-dialog rule on mobile,
  the dialog close bar, the empty-text handling — and they're outside the
  chip-wrap fix landed this round, so they may still run chips off the side of
  their field. (Not confirmed either way: the audit-log route 404'd from
  `/settings/audit-log`, so it wasn't reachable to measure.)
- **Why deferred:** out of scope for a recipe-page batch, and it's a
  conversion, not a patch.
- **Recommended resolution:** opportunistic — when either page is next touched.

## [OPEN] FU-794 — candidate rule: a component-wide style rule must be scoped to the variant it was written for
- **Raised:** 2026-08-31 (recipe-view feedback batch)
- **Type:** follow-up (ADR evaluation, per the engineering-standards close-gate)
- **What:** the page-h-scroll bug fixed this round came from `BaseSelect`'s
  `:deep(.q-field__native) { flex-wrap: nowrap }` — added 2026-08-21 to make a
  *single-value* select's text truncate, applied to *every* select in the app,
  and silently wrong for the chip ones (chips can't ellipsis, so they just ran
  off the side). A shared component's global rule should be conditioned on the
  variant that motivated it. Possible new `R-0NN` + ADR; the fix pattern is the
  `base-select--chips` class now in that file.
- **Why deferred:** promoting a standing rule is a governance call, not a
  side-effect of a UI batch.
- **Recommended resolution:** now — owner decides whether this earns an R-rule.

## [OPEN] FU-793 — the dense seed has no missing ingredient that also carries substitutes
- **Raised:** 2026-08-31 (recipe-view feedback batch)
- **Type:** finding
- **What:** the recipe row's missing chip has three states, and **two of them
  have no fixture in either seed**: every missing ingredient in `seed_dense.py`
  (Pecorino Romano, Sourdough Loaf, Tasty Cheese, Orange Juice) has zero
  recorded substitutes, so `Missing · N swaps` and `Swap ready` can only be seen
  by faking the API response. Same class of gap as FU-754 (no structured/image
  cook-mode fixture): a surface that can't be reached from the seed is a surface
  nobody looks at. `Extra Virgin Olive Oil` has a substitute but is stocked.
- **Why deferred:** a seed change is its own unit, and this batch was verified
  by intercepting the `/stock-items/:id/detail` response instead.
- **Recommended resolution:** later — next time `seed_dense.py` is touched.
  Cheapest fix: give one already-missing item a substitute that's in stock and
  another a substitute that isn't.

## [OPEN] FU-791 — the list-row chrome is now a third private copy (bordered card + accent hover)
- **Raised:** 2026-08-30 (meal-planner rail, Unit 2)
- **Type:** finding
- **What:** the "bordered flat surface, accent-tinted hover, no lift" list-row
  look exists three times now. It originated on `StockItemRow.vue`, was copied
  to `RecipeRow.vue`, and `MealPlanRecipeRow.vue` (new) is the third. The rail
  brief's §4.5 explicitly asked for it to be **promoted to a shared class**
  rather than copied again, citing the `.dora-subbar` extraction as precedent
  (R-022 / ADR-018).
- **Why deferred:** doing it properly means re-skinning `StockItemRow` and
  `RecipeRow` — two heavily-used surfaces the owner has signed off visually —
  inside a work unit whose scope was the meal-planner rail. That is exactly the
  adjacent-surface creep R-007 exists to stop, and a silent re-skin of the stock
  row is how you get a "why does my pantry look different" report. The
  duplication is commented in place in `MealPlanRecipeRow.vue` naming R-001.
- **Fix shape:** extract a `.dora-list-row` class (border, radius, surface,
  hover tint, focus ring) into `app.scss`, then have all three rows compose it
  and keep only their own layout. Diff the three current declarations first —
  they are *not* byte-identical, so the extraction has to pick a winner per
  property and that choice is visible on the stock row.
- **Recommended resolution:** opportunistic — pairs naturally with [[FU-691]]'s
  off-token stylesheet sweep or the next design-remediation chunk, since all
  three are the same class of drift. Not urgent; nothing is broken.

---

## [OPEN] FU-790 — `name: dashy-dora` orphans the deployed container, and `container_name` makes it fatal
- **Raised:** 2026-08-29 (owner hit it on a real deploy)
- **Type:** finding
- **What:** the uncommitted `name: dashy-dora` in `compose.yml` pins the Compose
  project name. The server had already been deployed *without* it, so its stack
  runs under the directory-derived project **`discountdora`**. After the deploy
  rsyncs the new file, every `docker compose` call addresses the **new** project:
  `down -v` matches nothing and leaves the old container running, then `up` fails
  with *Conflict. The container name "/dashy_dora" is already in use*. The
  conflict is fatal rather than harmless because `container_name: dashy_dora`
  (compose.yml:30) is a **global** name that ignores Compose's per-project
  namespace — without it the two projects would coexist as
  `discountdora-dashy_dora-1` / `dashy-dora-dashy_dora-1`. Compose can't
  self-heal this: from the new project's view that container is a stranger, not
  an orphan, so `--remove-orphans` doesn't touch it.
- **State:** owner chose (2026-08-29) to **keep** `container_name` and harden the
  deploy script instead of dropping it. A `reclaim_container_name` step was
  written into `~/Desktop/deploy-dora.sh` — it detects a container holding the
  name that isn't in `docker compose ps -aq` for the current project, and tears
  it down through *its own* project (taking that project's volumes too when
  `WIPE_DB=true`, so the old `discountdora_*` volumes don't strand). **The
  function is defined but not yet wired into `deploy()`** — the final edit was
  blocked by a session permission check, so the script still behaves exactly as
  before. Three lines are outstanding; they're in the 2026-08-29 worklog entry.
- **Why it stays open:** (a) the wiring above; (b) the one-time server cleanup
  (`docker compose -p discountdora down -v`) has not been confirmed run — SSH
  was blocked this session, so nothing here was verified against the live
  daemon; (c) the script remains **only** on the desktop, untracked by this repo
  (see the existing note under PROJECT_STATE's needs-attention item on
  `deploy-dora.sh`), so this hardening is one `rm` from being lost.
- **Recommended resolution:** now — it blocks deploying.

## [OPEN] FU-788 — Voice input can't work in Firefox without server-side transcription
- **Raised:** 2026-08-29 (settings feedback batch)
- **Type:** follow-up
- **What:** speech *recognition* is the browser's `SpeechRecognition` API, which
  Firefox has never shipped and offers no flag for. Batch 1 replaced the flat
  grey "your browser doesn't expose the Web Speech API" line with a warning card
  that names the browsers that do work (owner picked "better messaging only"),
  so nobody is left thinking they've misconfigured something — but Firefox users
  still cannot talk to Dora. Making them able to needs Dora to transcribe
  server-side (record audio in the browser, POST it, run Whisper or similar),
  which is the input-side mirror of what Piper already does for output.
- **Why deferred:** owner call 2026-08-29 — messaging now, the feature later. It
  would add a second optional heavyweight binary dependency with the same
  "not installable from pip on Windows" shape as Piper (R-018 / ADR-013), so it
  wants the same packaging treatment and its own decision.
- **Recommended resolution:** when voice input is worth a phase of its own — or
  opportunistically alongside any future Piper/packaging work, since the
  install story is shared.

## [OPEN] FU-787 — Piper's absence from a from-source install is a packaging gap, not just a copy problem
- **Raised:** 2026-08-29 (settings feedback batch)
- **Type:** finding
- **What:** the owner's reaction to "Dora's neural-voice engine isn't installed
  on this server" was *"In what situations does this happen? I'd expect it to
  always work."* The honest answer is that Piper is deliberately not a hard
  dependency (R-018 / ADR-013 — `piper-phonemize` has no Windows wheel), so the
  Docker image installs it and the desktop bundle ships it, but `pip install -r
  requirements.txt` + `python -m dora_api.startup` gets you an install with no
  neural voice at all. Batch 1 made the Voice page say exactly that and stopped
  offering 60–110MB voice downloads for an engine that cannot run them — but the
  expectation the owner voiced ("I'd expect it to always work") is the right one
  and the copy is only managing the gap.
- **Why deferred:** closing it for real means either finding a Windows-safe
  install path for Piper, vendoring the standalone binary per-platform the way
  `packaging/fetch_piper.py` already does for the desktop build, or picking a
  different engine. That is a packaging decision, out of scope for a settings
  copy pass.
- **Recommended resolution:** opportunistic — next time the packaging or
  desktop-build story is open.

## [OPEN] FU-786 — A legacy free-text ingredient unit can never be re-selected once changed away
- **Raised:** 2026-08-29 (recipe-view feedback batch)
- **Type:** finding
- **What:** the owner's reproduction case was an ingredient measured in
  **`loaf`** — a word that predates the closed unit vocabulary and is not in
  `UNIT_TABLE` at all. `useUnitOptions`' `includeValue` escape hatch exists so a
  row keeps its own unit offered, but it only works for canonical units the
  *measurement system* excludes (a `lb` on a metric install); a unit with no
  table entry has no dimension, so `isOffered` can never return true for it.
  Confirmed live: the dropdown on that row offered 14 units and `loaf` was not
  among them. The field still *displays* `loaf` and saving without touching it
  preserves it, so nothing is silently lost — but change it once and it is
  unrecoverable from the UI.
- **Why deferred:** the fix is a vocabulary decision, not a code one. Either
  (a) add the genuinely-common count words (`loaf`, `slice`, `clove`, `sprig`,
  `head`, `bunch`, `can`, `tin`, `jar`, `bottle`) to `dora_api/domain/units.py`
  as universal count units — which is the pantry-shaped answer and also fixes
  every recipe importer that parses them — or (b) widen `includeValue` to pass
  an unknown unit straight through as a synthetic option, which keeps one row
  working and leaves the importer producing units nothing can offer. (a) is
  clearly better and clearly out of a feedback batch's scope.
- **Recommended resolution:** **opportunistic** — next time the unit table or the
  recipe importer is open. Worth a count of what's actually in the wild first:
  `SELECT unit, COUNT(*) FROM RecipeIngredient WHERE unit IS NOT NULL GROUP BY 1`
  names the words users have really typed.

## [OPEN] FU-785 — A benign `ResizeObserver` loop warning shows an "Oops" toast **and rolls back optimistic mutations**
- **Raised:** 2026-08-29 (shopping-list UX v3 verify pass)
- **Type:** finding
- **What:** `boot/globalErrorHandler.ts:24` installs a blanket `window.onerror`
  that calls `executeRollbacks()` and `Notify.create({ type: 'oopsie' })` for
  *anything* the browser reports. Browsers report **"ResizeObserver loop
  completed with undelivered notifications"** through that channel — a
  spec-benign signal meaning an observation was deferred a frame, carrying no
  `Error` and nothing to act on. The user sees a red *"Oops, something went
  wrong"* for a successful interaction, and — the worse half — **every
  registered rollback fires**, so an in-flight optimistic mutation can be
  reverted by a layout hiccup.
- **Re-confirmed 2026-09-01** (v4 chunk 3): still live. Fires on `/#/`,
  `/#/stock` and `/#/shopping-lists/<id>` (plan *and* receipt faces) on any
  viewport resize; `/#/recipes` did not reproduce. Worth noting for whoever
  picks this up — it is easy to mistake for a defect in whatever page you are
  currently working on, which is what happened here before this entry was found.
- **Reproduction (verified live, 2026-08-29):** resize the viewport across the
  `md` breakpoint on `/#/shopping-lists/<id>`, `/#/meal-plans` or the dashboard —
  2 errors, 1 toast, every time. The observer is
  `components/menu/MainMenuButtonStrip.vue:47`, i.e. app chrome, not any one
  page. `/#/stock`, `/#/recipes` and the templates page do **not** trip it.
- **Why deferred:** found while verifying UX-v3 and initially mistaken for its
  cause; confirmed pre-existing by hiding the new overview card (no change) and
  by reproducing on two untouched pages. Fixing it means changing app-wide
  error handling and/or the menu strip's measurement — cross-cutting work that
  deserves its own consideration, not a drive-by inside a shopping-list unit.
- **Recommended resolution:** now-ish — the rollback half is a correctness bug,
  not cosmetics. Smallest honest fix is an ignore-list in `window.onerror` for
  `ResizeObserver loop` messages (they are unactionable by contract); the
  better one also stops `MainMenuButtonStrip` from writing layout inside its own
  observer callback.

## [OPEN] FU-784 — `DoraBubble` has no placement budget against page-level bottom chrome
- **Raised:** 2026-08-29 (shopping-list UX v3 audit)
- **Type:** finding
- **What:** `components/dora/DoraBubble.vue:396-406` is `position: fixed; bottom:
  18px + safe-area; z-index: 3000`, ~88px tall, bottom-right. Any page-level
  bottom chrome lands underneath it. Today's concrete collision is the shopping
  list's `.sld-shop-footer` (`ShoppingListDetail.vue:3574`, z-index **3**), whose
  "Finish & restock" CTA sits exactly there on narrow screens. Quasar toasts were
  already lifted 112px for the same reason (`css/app.scss:54`) — a one-off patch,
  not a rule. D-009 ("toasts & floating chrome respect a placement budget") says
  this should be systematic.
- **Why deferred:** v3 shipped 2026-08-29 and deleted `.sld-shop-footer`
  outright, so **the instance is gone** — the shopping list has no bottom chrome
  left for the mascot to sit on. The *class* of bug survives for the next page
  that grows some.
- **Recommended resolution:** when another page adds fixed/sticky bottom chrome —
  at that point define the budget once (a `--bottom-chrome-offset` token or a
  shared composable) rather than patching a third caller.



## [OPEN] FU-781 — A hypothesis property test fails intermittently, full-suite only
- **Raised:** 2026-08-28 (shopping-list batch 3 — seen in a close-gate suite run)
- **Type:** finding
- **What:** `tests/test_domain_properties.py::test__discount_percent__property__
  lower_price_never_ranks_worse` failed once in a full `pytest tests/` run, then
  passed on every re-run in isolation (7 explicit `--hypothesis-seed` values, 6
  plain re-runs). The file is unmodified since commit `22a11bc4` and nothing in
  this session touches `discount_percent`.
- **Two candidate causes, neither confirmed** (the traceback wasn't captured
  before the re-run, which is the mistake to avoid next time):
  1. **`filter_too_much` health check.** The property is
     `assume(now_a < was and now_b < was)` over three independent price floats,
     so ~⅚ of generated inputs are discarded. Reproducing the same shape
     standalone trips `FailedHealthCheck: 8 inputs generated, 50 filtered out`
     — so the test is genuinely near that threshold and whether it crosses
     depends on the seed. `pytest-randomly` reseeds every run, which is exactly
     how a seed-sensitive test becomes an intermittent one.
  2. **`DeadlineExceeded`.** Hypothesis's default 200ms-per-example deadline is
     easy to blow under a loaded full-suite run and impossible to hit alone.
  Both fit "passes alone, fails in the suite"; they want different fixes
  (restructure the strategy to generate `was` then two prices below it, vs
  `deadline=None`).
- **The maths looks sound**, for what it's worth: `discount_percent` is
  `round((was - now) / was * 100)` with a `now >= was → None` guard, and `round`
  is monotone, so the property itself should hold. This reads as a test-harness
  flake, not a domain bug — but that is a static read, not proof.
- **Recommended resolution:** opportunistic — **capture the traceback next time
  the full suite goes red** rather than re-running immediately. Cheap to fix
  once the cause is known; noisy to leave, because a suite that fails at random
  trains everyone to re-run instead of read.

## [OPEN] FU-780 — `ShoppingListDetail.vue` is 3,784 lines and violates R-001
- **Raised:** 2026-08-28 (shopping-list feedback batch 2)
- **Type:** finding (R-001 — componentisation-first)
- **What:** the page is **3,784 lines** against 110–344 for every component beside
  it. Two feedback batches have now *deleted* from it (the bulk bar, the substitute
  swap, draft ticking, copy-to-new, the switch-list dialog — several hundred lines)
  and it is still by far the largest file on the surface, because the plan face's
  row template alone runs ~450 lines inside a single `v-for`. The run and receipt
  faces are already their own components; the plan face never was.
- **Why deferred:** extracting `ShoppingListPlanFace.vue` is a real chunk — the row
  template reaches ~20 handlers and several composables on the page — and doing it
  inside a visual-feedback batch would have buried a large mechanical refactor in a
  diff the owner needs to read for behaviour. Batch 3 rebuilds the same row
  (`planned_store_id` + the line editor), so the honest sequence is to land that
  behaviour first and extract once the shape has settled.
- **Recommended resolution:** later — immediately after shopping-list batch 3,
  while the surface is still fresh. `ShoppingListRunFace.vue` is the template to
  copy.

## [OPEN] FU-779 — The QR centre mark needs a proper asset; the wordmark reads as crap
- **Raised:** 2026-08-28 (owner, on seeing the first render)
- **Type:** design / needs an asset from the owner
- **What:** the D/D mark now centred in every stock-item QR
  (`dora_api/assets/dora_qr_mark.png`, composited by `_paste_centre_mark` in
  [barcodes.py](dora_api/features/data/barcodes.py)) was rasterised from
  `web_app/public/icons/safari-pinned-tab.svg` — chosen because it was the only
  flat monochrome mark in the repo, not because it suits this job. It doesn't.
  It's a **2.5:1 wordmark**, so at 26% of the code's width it lands as a thin
  horizontal strip of letterforms: it reads as small text sitting on the code
  rather than as a logo embedded in it, and the two `D` bowls are close enough
  to the surrounding module noise that the eye doesn't lock onto it. A centre
  mark wants a compact, roughly square, high-contrast glyph — the shape the rest
  of the industry uses — and Dora doesn't currently own one.
- **What's needed from the owner:** a single flat mark, ideally SVG:
  - **roughly square** (1:1 to 4:3). This is the main thing the current asset
    gets wrong.
  - **one solid colour on transparent**, pure black preferred (it is composited
    onto a white knockout; a mid-tone or a gradient loses contrast against the
    quiet ring and reads muddy at label size).
  - **chunky strokes, no hairlines and no fine interior detail** — the mark
    renders ~47px wide on a 180px print-sheet cell.
  - not the `dorabot-*` illustrations: already ruled out, far too detailed to
    survive that size.
- **Then what:** genuinely a drop-in. Re-run
  `inkscape <mark>.svg --export-type=png --export-filename=dora_api/assets/dora_qr_mark.png --export-width=1520 --export-background-opacity=0`,
  crop to the alpha bbox, and it works — the compositor derives its aspect from
  the asset. Two knobs may want a nudge for a squarer mark: `_MARK_WIDTH_RATIO`
  (0.26) and, in `tests/test_qr_centre_mark.py`, the hardcoded `544 / 1350`
  aspect used to locate the ring. The area guard in that file
  (`box_w * box_h < 0.08`) is the safety rail — a squarer mark at the same width
  covers ~2.4× the area, so **re-run the decode + degradation sweep** rather
  than assuming the ERROR_CORRECT_H budget still covers it.
- **Meanwhile:** the codes scan correctly, so this is cosmetic only. If it
  bothers you before an asset exists, setting `_MARK_MIN_SIZE` above
  `QR_MAX_SIZE` (1024) turns the mark off everywhere in one line and renders
  plain codes — the missing-asset path is already tested to degrade that way.
- **Recommended resolution:** **when you have a mark** — blocked on the asset,
  nothing to investigate.

## [OPEN] FU-778 — A Quasar portal timer fires after teardown in the vitest run
- **Raised:** 2026-08-28 (seen while re-running the suite for the toast change)
- **Type:** finding
- **What:** `npx vitest run` reports **`Errors 1 error`** alongside its 562 passes:
  `ReferenceError: document is not defined` from `quasar.client.js` →
  `showPortal` → `removeFocusWaitFlag`, originating in
  `test/unit/addToListButton.spec.ts`. A QDialog's portal timeout fires after the
  jsdom environment has been torn down. Vitest's own message is the reason this
  is worth logging: *"This might cause false positive tests."*
- **Confirmed pre-existing:** the full suite was re-run with that session's
  `notifyTypeRegistration.ts` + `app.scss` changes stashed and the error appeared
  **identically** — so it is not a regression from the toast work. It also does
  not reproduce when that spec runs alone, only in the full run.
- **Why deferred:** unrelated to the batch that found it, and it fails nothing today.
- **Recommended resolution:** **opportunistic** — next time `AddToListButton` or
  its spec is touched. Likely fixed by awaiting the dialog's close (or a
  `vi.useFakeTimers()` drain) before the test ends.

## [OPEN] FU-777 — `ExpiringChip`'s neutral state uses a numbered Quasar palette class
- **Raised:** 2026-08-28 (found by the widened R-002 detector during the toast fix)
- **Type:** finding
- **What:** [ExpiringChip.vue:67](web_app/src/components/recipes/ExpiringChip.vue)'s
  default branch returns `{ color: 'grey-7', textColor: 'white' }`. `grey-7` is a
  numbered Quasar palette class, which **R-002 names explicitly** as a violation —
  it's a fixed mid-grey that ignores the theme, so the "at risk but not urgent"
  chip reads the same in every palette and sits wrong on the dark ones. R-002's
  own **Apply** clause prescribes the fix: route the neutral branch through
  `dora-bg-sunken dora-text-secondary` and keep only the saturated
  `negative`/`warning` branches on `color=`/`text-color="white"`.
- **Why deferred:** scope — the session that found it was fixing toasts, and this
  is a different component on a different surface. Pre-existing, not introduced.
- **Recommended resolution:** **needs an owner call, then one-line.** Updated
  2026-09-01: the recipe-view chip batch touched the adjacent run and did *not*
  fix this, deliberately. There are now two shared chip classes in
  `colours.scss` and this chip sits between them — `.dora-chip--neutral`
  (yesterday's answer for the cookbook's dietary + belief chips, which this
  chip sits beside) and `.dora-chip--tint` (today's answer for the recipe
  row's missing / "Use soon" pair, which says the same *thing*). Picking one is
  a design decision on a surface the owner signed off two days ago, not a
  cleanup, so it wasn't taken unasked. Either target fixes the R-002 violation,
  since both are token-driven. Ask which, then it's a one-line change.

## [OPEN] FU-776 — Should the buy verdict's plan axis discount items already on a shopping list?
- **Raised:** 2026-08-28 (buy-verdict plan-axis brief)
- **Type:** design question
- **What:** if the plan axis (see
  [BRIEF_BUY_VERDICT_PLAN_AXIS.md](docs/04_proposals/BRIEF_BUY_VERDICT_PLAN_AXIS.md))
  pushes tomato sauce to `buy` for Thursday's Bolognese, but the user already
  put it on a list via the meal planner's one-shot add, the verdict is noise —
  the need is handled. Reading open-list membership would suppress that, at the
  cost of a further cross-entity read in `_gather_inputs`.
- **Why deferred:** it only matters if the axis is built at all (FU-774 gates it).
- **Recommended resolution:** **when FU-774 is answered yes** — decide it as part
  of the implementation plan, not before. Note it must be server-side: a client
  computing "is this already on a list" is a straight state-ownership violation.

## [OPEN] FU-775 — Pick the gate for the buy-verdict plan axis
- **Raised:** 2026-08-28 (buy-verdict plan-axis brief)
- **Type:** design question
- **What:** the inference overlay's per-surface opt-ins live on `User`
  (`inference_meal_plan_enabled` et al.), but the buy verdict is gated
  install-wide by `AppSetting.buy_verdict_enabled` plus the R-058 money
  prerequisite. A per-user flag on an install-wide surface is a mismatch. The
  brief recommends a new install-wide `AppSetting.buy_verdict_plan_axis_enabled`
  defaulting **off**, matching how the overlay's three newer surface flags
  default.
- **Why deferred:** downstream of FU-774; pointless to migrate a column for an
  axis that may not be approved.
- **Recommended resolution:** **when FU-774 is answered yes.**

## [OPEN] FU-774 — Owner call: may a planned meal change a buy verdict?
- **Raised:** 2026-08-28 (owner asked whether planned meals should feed the buy verdict)
- **Type:** decision
- **What:** the owner's idea — *"high confidence you should buy tomato sauce
  because you planned spaghetti Bolognese but you're out"* — is a good one, and
  the brief
  ([BRIEF_BUY_VERDICT_PLAN_AXIS.md](docs/04_proposals/BRIEF_BUY_VERDICT_PLAN_AXIS.md))
  argues it is the *strongest* need evidence the oracle can hold, because unlike
  the recorded level and the cadence estimate it is a stated intention rather
  than an inference. **But it is currently forbidden.** `inference_overlay.py:23`
  records an explicit owner directive of 2026-08-17 that "a planned meal's
  shortfall is unchanged" and that everything plan-derived is additive
  commentary only. An axis that moves a verdict from `unsure` to `buy` breaks
  that directly.
  - Argument for reversing *on this surface*: the directive was written about
    the inference overlay, whose remarks come from a Dora-generated *belief*.
    A planned meal is user-entered data, so the directive's stated rationale
    ("a low-confidence guess contradicting a recorded fact is noise") doesn't
    obviously reach it.
  - Argument against: the buy verdict is exactly the surface the directive was
    protecting, and the overlay's `SURFACE_MEAL_PLAN` flag exists because
    annotating meal plans at all was thought intrusive enough to need an opt-in.
  - If the answer is **no**, the fallback is a reason line that names the meal
    but never affects strength or direction — worth much less, and the brief
    closes as considered-and-declined.
- **Why deferred:** it is a product call about how much authority Dora's own
  plans get over its own advice. Not an agent's to make.
- **Recommended resolution:** **now** — it gates FU-775 and FU-776 and the whole
  axis. Nothing was built.

## [OPEN] FU-773 — The desktop filter row wraps to three lines at 1280px, not the two the owner asked for
- **Raised:** 2026-08-28 (cookbook rating + kcal batch)
- **Type:** finding
- **What:** the ask was "on desktop only, make it two rows of filters under the
  quick filters". `FilterRow` gained a `wide-wraps` mode that wraps instead of
  scrolling sideways above 600px; measured at 1280×900 the cookbook's twelve
  visible controls take **three** lines (`flex-wrap: wrap`, `overflow: visible`
  — both confirmed in the browser). Wrapping was chosen over pinning it at two
  because the count is window-dependent: two rows would overflow at 1024px and
  leave a half-empty second line at 1920px, and the row grows or shrinks by two
  controls depending on whether nutrition and batch cooking are on.
- **Why deferred:** it's a judgement call about what "two rows" meant — a literal
  count, or "stop making me scroll sideways". The second reading is delivered.
- **Recommended resolution:** **owner call** — say the word if you want it forced
  to two lines (achievable by narrowing the shared control width track on the
  cookbook only) or if three lines at your usual window size is fine.
- **2026-08-29 update:** the width-consistency fix in the same feedback batch
  retired the 230px numeric track, so five controls shrank to 210px and the row
  lost ~100px of total width. Re-measured live at 1280×900 with nutrition on:
  still **three** lines (5 / 5 / 3 controls, thirteen visible), no clipped
  labels. So the ask is still open on the same terms — the lever left is
  narrowing the shared track below 210px, which the owner already pushed *up*
  from 180 on 2026-08-21.

## [OPEN] FU-772 — The rating pill's tint has had no dark-theme pass
- **Raised:** 2026-08-28 (cookbook rating + kcal batch)
- **Type:** finding
- **What:** `RecipeRatingChip`'s score pill paints `--brand-primary-soft` behind
  `--text-primary`, with the star glyph on `--brand-primary`. Light themes define
  that token as a pale opaque tint, but **every dark theme defines it as a
  translucent wash of the theme's own accent** (`hsla(...)` — see
  `themes.scss`), so the pill's effective contrast in dark mode depends on what
  it happens to sit on. Reasoned to be safe (D-002) and not measured: the chip
  only paints in complex nutrition mode, which no verify instance can reach.
- **Why deferred:** unreachable without an imported food catalogue; the same
  wall that has kept the whole rating surface unverified since 2026-08-27.
- **Recommended resolution:** with the `DORA_VERIFY` → "Cookbook: the 2026-08-28
  rating + kcal batch" walk, on a dark theme. Cites **D-002**.

## [OPEN] FU-771 — Nutrition mode/scheme changes don't invalidate the recipe list
- **Raised:** 2026-08-28 (cookbook rating + kcal batch)
- **Type:** finding
- **What:** R-062's invalidation covers stock writes, which is where the owner's
  bug was. Two install-wide levers move every recipe's rollup and are **not**
  covered: switching nutrition mode / rating scheme on
  `AdminSystemNutritionSettings.vue`, and a dataset import completing. Both
  currently rely on the user reloading — plausible for a settings change, less so
  for an import that finishes while they're on another page.
- **Why deferred:** both also change cached *feature flags*, which the SPA reads
  once per session, so a store invalidation alone wouldn't make the surfaces
  correct — it needs the flag-refresh seam thought through, which is wider than
  this batch.
- **Recommended resolution:** opportunistic — next time the health-flag caching
  or the admin nutrition page is open. Cites **R-062**.

## [OPEN] FU-770 — `RecipeCard` and `RecipeRow` still carry the kcal chip twice (FU-747's other half)
- **Raised:** 2026-08-28 (cookbook rating + kcal batch)
- **Type:** finding
- **What:** FU-747 called for one `RecipeSignalChips` covering both the rating and
  the kcal block. Half of it landed — the rating is now wholly inside
  `RecipeRatingChip`, and this batch removed the duplicated rating wrapper and the
  `--part { opacity: .55 }` rule from both hosts. The **kcal** figure is still
  written out in both files, and they have now deliberately *diverged*: the card
  renders a `q-chip` beside Difficulty, the row renders plain text on its meta
  line. Same data, same asterisk rule, two renderings.
- **Why deferred:** they diverged because the owner asked them to — a shared
  component would need a `variant` prop, which is worth doing only if a third
  caller appears. The duplication that actually bites (the asterisk rule and the
  tooltip copy) is two lines.
- **Recommended resolution:** opportunistic, and only if a third surface needs a
  kcal figure. Supersedes the kcal half of **FU-747**; cites **R-001**.

## [OPEN] FU-769 — Changing a line's store reportedly doesn't move it between store groups
- **Raised:** 2026-08-28 (shopping-list feedback batch 1)
- **Type:** finding
- **What:** owner reports that setting "Bought from" on a line leaves it in its old
  bucket under **Order by → Store**. A static read says it should work: the price
  editor writes `purchased_store_id`, which is **rung 1** of the server's store
  ladder (`get_shopping_list_detail.py:591`), and the grouping key is
  `resolved_store_name` (`useLineSections.ts:69`), so a refetch ought to re-bucket
  the row. Did **not** reproduce in the read — but the report came from real usage
  and the plausible failure is a *refresh* gap (the popover's save path patches the
  line optimistically and may not refetch the detail), which a code read is bad at
  seeing.
- **Why deferred:** batch 1 was deletions + the tick model; this sits on the store
  work in batch 3, which rebuilds the same editor anyway.
- **Recommended resolution:** **confirm in browser** — set a store on a draft line
  with Order-by=Store active and watch whether the row moves without a reload. Fold
  into batch 3 (`planned_store_id`).

## [OPEN] FU-768 — Four surfaces still treat "line has a price" as "line was bought"
- **Raised:** 2026-08-28 (shopping-list feedback batch 1)
- **Type:** finding
- **What:** the sibling of the budget bug fixed this session. `picked_offer_price`
  is snapshotted at **add** time, so an unticked line carries a price it never cost.
  These four read that price with no `is_ticked` filter:
  `suggestions/generators.py:186` (whose comment asserts the opposite is true),
  `stock_items/pantry_belief.py:329` (invents purchase dates for items never
  bought), `stock_items/get_buy_verdict.py:762` (pollutes `price_samples` /
  `purchases_12mo`), and `waste/waste.py:113` (value-at-risk — and it doesn't even
  filter to done lists).
- **Why deferred:** unlike the budget, this isn't one filter — it's a question about
  what counts as proof of purchase across four features with different tolerances
  for a false positive. `_line_price.py` is the natural chokepoint for a
  `line_purchased_unit_price()` that answers it once (R-003), but that's a design
  call, not a reflex.
- **Recommended resolution:** now-ish — these feed belief, verdicts and waste, all
  of which the owner reads as signal. One decision, then mechanical.

## [OPEN] FU-766 — Server-side `bulk-tick` endpoint and `has_substitutes` are now unread
- **Raised:** 2026-08-28 (shopping-list feedback batch 1)
- **Type:** leftover
- **What:** removing the bulk-select bar and the substitute swap left two server
  contracts with no client caller: `POST /shopping-lists/<id>/lines/bulk-tick`
  (`bulk_operations.py:82`) and the per-line `has_substitutes` flag on the detail
  DTO (`shoppingList.ts:113`), which the server computes on every line of every
  read for nobody. The client-side `bulkTickAsync` was deleted this session; these
  weren't.
- **Why deferred:** deleting a live endpoint plus its tests is a bigger call than a
  UI batch should make unilaterally, and R-057/ADR-054 is explicit that a replaced
  endpoint's response is an inventory to check, not a casualty list. `has_substitutes`
  in particular may be wanted by a future shop-mode swap if INV-8's original
  recommendation is ever revisited.
- **Recommended resolution:** opportunistic — owner's call. Delete both, or keep
  `has_substitutes` and note why.

## [OPEN] FU-765 — Cook mode never re-fetches when the route's recipe id changes
- **Raised:** 2026-08-28 (cook-mode feedback batch — found while verifying)
- **Type:** finding
- **What:** `RecipeCookMode.vue` fetches its recipe in `onMounted` only. Vue reuses
  the component instance across `/cookbook/A/cook` → `/cookbook/B/cook`, so the
  page keeps rendering recipe **A** — right down to its steps, ingredients and
  finish flow — under recipe B's URL. Reproduced live: hopping between two cook
  routes left the first recipe's step card on screen indefinitely; only a hard
  reload corrected it. There is no `watch` on `route.params.id`.
  **Re-confirmed live 2026-09-01** during the cook-mode batch, and it has a
  second face worth recording: after a *failed* load the page latches
  "Recipe not found." for every subsequent id too, because `recipe.value = null`
  is set in `onMounted`'s `catch` and nothing ever retries. Whatever the fix is,
  it has to clear that state as well.
- **Why deferred:** out of scope for a visual-feedback batch, and it needs a
  decision rather than a reflex `watch`: re-fetching mid-cook must not silently
  discard session state (headcount, session swaps, the timer, the step position),
  so the honest fix may be `:key="route.params.id"` on the route component — which
  remounts and resets deliberately — rather than a watcher that mutates a live
  cook session underneath the user.
- **Why it may not matter much:** no in-app path currently jumps between two cook
  routes (you exit to the cookbook first), so this is reachable mainly by a pasted
  link or a back/forward pair. Worth fixing anyway — the failure is silent and
  wrong, not merely stale.
- **Recommended resolution:** opportunistic — next time cook mode is touched.

## [OPEN] FU-764 — No lint gate on undefined CSS custom properties (four more files affected)
- **Raised:** 2026-08-28 (cook-mode feedback batch — root cause of the squish)
- **Type:** finding
- **What:** an undefined `var(--token)` with no fallback invalidates its whole
  declaration and silently falls back to the initial value; nothing in the
  toolchain catches it (see R-060 / ADR-057). The cook-mode files are fixed. A
  repo-wide grep found the remaining users of tokens that `css/` never declares:
  - `components/filters/TriStateFilter.vue:278` — `background: var(--surface-card)`,
    **no fallback**, so the control has no background at all. Same class of bug as
    the cook-mode one, still live.
  - `components/settings/VoicePicker.vue:355` — `var(--surface-card, transparent)`.
  - `components/stock/MarkAsWastedDialog.vue:112-123` — `--c-line`, `--c-surface-2`,
    `--c-surface-3`, `--c-line-strong`.
  - `pages/StocktakeRunner.vue:953` — `--c-line`.
  - `pages/DashboardPage.vue` declares `--c-line` locally at :2303 and then uses it
    at four sites, which works but entrenches a second naming scheme.

  All but `TriStateFilter` carry fallbacks, so they render — but they render the
  fallback, never the theme value, which means they do not follow the theme.
- **Why deferred:** the fix is two things and only one is urgent. Repointing five
  files at real tokens is mechanical; the durable answer is a stylelint rule (or a
  small build check) that fails on a custom property `css/` never declares, and
  that is a tooling change with its own rollout.
- **Recommended resolution:** later, when the CSS/design-token surface is next
  worked on — but pull the `TriStateFilter` one-liner forward opportunistically,
  since that one is visibly broken today.

## [OPEN] FU-763 — Cook-mode step text at `text-h4` on a phone: observed, owner's call
- **Raised:** 2026-08-28 (supersedes the browser-pass ask in FU-752)
- **Type:** finding
- **What:** FU-752 asked for a phone walk of the step card. Done at 375×812 this
  session: the card does not overflow, wraps cleanly, and the page has zero
  horizontal scroll. A six-word step fills roughly five lines and about half the
  viewport height, which pushes the Previous/Repeat/Next row toward the fold.
  That is the *intent* (read it from across the kitchen), so there is no bug —
  only a taste question the owner owns.
- **Why deferred:** shrinking cook-mode type is a judgement about the feature's
  whole point, not a layout defect, and the owner did not raise it in this round.
- **Recommended resolution:** when the owner next cooks from a phone — if the step
  card feels too tall in real use, drop it to `text-h5` below `sm`; otherwise close.

## [OPEN] FU-762 — Four buy-verdict e2e tests fail against the (uncommitted) money gate
- **Raised:** 2026-08-27 (Nutri-Score build — found incidentally)
- **Type:** finding
- **What:** `tests/e2e/dora_api/test_list_buy_verdicts.py` fails 4 of 4 —
  `one_entry_per_line_item`, `match_the_per_item_endpoint`,
  `empty_list_is_an_empty_map`, `unknown_list_is_404`. All four get a 403
  *"Buy verdicts need money features, which are turned off for this install"*
  where they expect 200/404. The money prerequisite added by the previous
  session's (still uncommitted) buy-verdict work is correct; these four fixtures
  simply never enabled money, and the unit suite the worklog quotes (**870
  passed**) does not include the e2e directory, so they went unnoticed.
- **Verified pre-existing:** stashing *all* uncommitted work makes them pass,
  and nothing in this unit touches the buy verdict. Not caused by the
  rating-scheme change.
- **Why deferred:** R-007 — it is the other work unit's fixture to fix, and
  guessing at its intent (enable money in the fixture vs. assert the 403) could
  contradict what that session meant to assert.
- **Recommended resolution:** **now**, before the buy-verdict work is committed
  — a red e2e suite blocks everyone. Likely a one-line fixture change.

## [OPEN] FU-761 — `kcal_to_kj` is imported from the HSR module by a Nutri-Score caller
- **Raised:** 2026-08-27 (Nutri-Score build)
- **Type:** finding
- **What:** `recipe_rollup.py` builds the Nutri-Score profile with
  `hsr.kcal_to_kj(...)`, because the kcal→kJ factor lives in
  `domain/health_star_rating.py` and both schemes score energy in kJ.
  Duplicating the constant into `domain/nutri_score.py` would have been a
  straight **R-003** violation, so the shared read is the lesser evil — but a
  generic unit conversion sitting inside one scheme's module, imported by the
  other's caller, reads oddly and will read worse if a third scheme appears.
- **Why deferred:** `domain/units.py` is the natural home, but moving it churns
  a module that shipped hours earlier and whose tests import the symbol by name.
  Not worth bundling into this diff.
- **Recommended resolution:** opportunistic — next time `domain/units.py` or
  either rating module is open. Cites **R-003**.

## [OPEN] FU-760 — The cookbook's stored rating filter/sort keys were renamed, so saved views silently reset
- **Raised:** 2026-08-27 (Nutri-Score build)
- **Type:** finding
- **What:** `RecipesOverview` renamed its filter ref `healthStarsMin` →
  `ratingMin` and its sort key `'health_stars'` → `'rating'`, both of which are
  persisted. A user whose stored cookbook view held either will find that facet
  quietly back at its default on next load. Correct rename — neither name was
  true once Nutri-Score existed — but the reset is real.
- **Why deferred:** pre-release, and the blast radius is one filter chip and one
  sort axis reverting to default, not data loss. A migration shim for stored
  view state is exactly the compat scaffolding this project has said it doesn't
  want before release.
- **Recommended resolution:** **no action expected** — logged so it isn't
  mistaken for a bug if it's noticed. Close it if release is still ahead.

## [OPEN] FU-759 — Two more copies of the install-wide money read, now that `access.money_features_enabled` exists
- **Raised:** 2026-08-27 (buy-verdict money gate)
- **Type:** finding
- **What:** the buy-verdict gate needed an install-wide money read in two files,
  so one was added as `money_features_enabled()` in
  `dora_api/features/app_settings/access.py` — beside the memoised singleton
  accessor, so gating costs no extra query. Two pre-existing private copies now
  duplicate it: `swap_suggestions._money_features_on` (line ~324) and the money
  half of `build_week._household_budget_amount` (line ~377). Both do their own
  `repository.get(AppSetting).all()` rather than going through the memoised
  accessor, so they also re-query a single-row table FU-560 already cached.
- **Why deferred:** R-007 — the ask was gating the buy verdict. Both call sites
  are inside meal-plan reasoning with their own tests; folding them in means
  re-reading that suite, which is its own piece of work rather than a line in
  this diff.
- **Recommended resolution:** opportunistic — next time either meal-plan file is
  open. Cites **R-003** (one domain fact, one reader) and FU-560.

## [OPEN] FU-758 — `.claude/launch.json` verify configs point at :5170 with `DORA_ALLOW_DESTRUCTIVE=true`
- **Raised:** 2026-08-27 (buy-verdict money gate)
- **Type:** finding
- **What:** all four `dora-verify-backend*` configs bind **port 5170** — the dev
  backend's port, against the real dev DB — while setting
  `DORA_ALLOW_DESTRUCTIVE=true`, which drop_alls on boot. The intended isolated
  verify setup is a **scratch backend on 5171** with the SPA on 5174 (CORS, hash
  routing, seeded e2e fixture login); an agent following the launch config as
  written would destroy the dev database instead. This session declined to start
  a preview for exactly this reason, so the browser pass for the money gate is
  owed (logged in `DORA_VERIFY.md`).
- **Why deferred:** it's the owner's local tooling and the safe port/DB pairing
  is his call — guessing a port and a `DORA_DB_PATH` into a committed config is
  how the next agent gets a *differently* wrong instance.
- **Update 2026-08-28 — the safe pairing now exists and is proven, but the four
  dangerous configs are still there.** The cook-mode session needed a live verify
  with the owner's backend running on :5170, and added two configs rather than
  editing his: **`dora-verify-backend-5171-linux`** (`DORA_API_PORT=5171`,
  `DORA_DB_PATH=data/scratch-verify.db` — gitignored, `DORA_ALLOW_DESTRUCTIVE=true`)
  and **`dora-spa-5171`** (SPA on 5174 with `VITE_API_BASE_URL` pointed at 5171).
  Both were driven end to end: fresh DB seeded on boot, login, cook mode at two
  viewports, screenshots. So the port/DB pairing is no longer a guess. What
  remains is the owner's call on the **four `dora-verify-backend*` entries that
  still bind :5170 with destructive mode on** — the footgun is unchanged for
  anyone who picks one of those by name.
- **Recommended resolution:** **now-ish** — either point those four at the proven
  5171 pairing, or delete them in favour of the new pair. One decision, no
  investigation left to do.

## [OPEN] FU-757 — "New shopping list → start from a meal plan" still drops unlinked ingredients silently
- **Raised:** 2026-08-27 (meal-plan add-to-list unification)
- **Type:** finding
- **What:** `NewListDialog.vue`'s `startFrom: 'meal_plan'` branch calls
  `mealPlanApi.getIngredientsAsync` and now reads `.items` off the new envelope,
  but ignores the `unlinked` field beside it. So a plan whose recipes carry
  unmatched ingredients seeds a list that quietly omits them — exactly the gap
  FU-505 opened and the one the shared picker just closed on the planner and the
  recipe page. Same file's `recipe` branch has the same shape.
- **Why deferred:** R-007 — the ask was the meal-plan/recipe add-to-list flow;
  the new-list dialog is a third surface with its own composed form and its own
  "pre-seeded / skipped" counters, so folding the report in properly is its own
  small piece of work rather than a line in this diff.
- **Recommended resolution:** opportunistic — next time that dialog is open for
  any reason. Cites **R-057**; the data is already on the wire, so it's a
  rendering job, not an API change.

## [OPEN] FU-756 — `web_app/test/` is outside the lint scope and has drifted
- **Raised:** 2026-08-27 (meal-plan add-to-list unification)
- **Type:** finding
- **What:** the project lints `web_app/src` only. Running eslint over `test/` as
  well surfaces one pre-existing error —
  `test/unit/useBuyVerdict.spec.ts:34` uses an `import()` type annotation, which
  `@typescript-eslint/consistent-type-imports` forbids. One error across 46 spec
  files means the specs are essentially compliant already, so widening the scope
  is cheap; leaving it means the next drift is equally invisible.
- **Why deferred:** unrelated to the change in hand (R-007), and widening a lint
  scope is the kind of thing that should land on its own so a red gate has one
  obvious cause.
- **Recommended resolution:** opportunistic — fix the one error and add `test` to
  the lint script's paths in the same small change.

## [OPEN] FU-792 — `seed_showcase.py` has no structured- or image-mode recipe
- **Raised:** 2026-08-31 (dense-seed unit; the surviving half of the now-resolved FU-754)
- **Type:** finding
- **What:** The dense dev seed now carries both faces — a ten-step structured
  recipe with sub-steps, sections and per-step links, and a five-photo image
  recipe — so the *dev* half of FU-754 is closed. `seed_showcase.py` (the demo
  dataset) is still 100% `steps_mode: 'freeform'`, so the public demo shows only
  one of cook mode's three faces.
- **Why deferred:** R-007 — the ask was a dev dataset. The showcase is a
  different audience with a different bar: its photos are the ones strangers
  see, so it wants real food photography rather than the drawn step cards the
  dev seed uses (`scripts/generate_seed_dense_images.py`), which is a content
  decision, not a code one.
- **Recommended resolution:** opportunistic — next time the showcase dataset or
  the demo instance is touched. The mechanism is already proven: build the
  recipe, then call `replace_sections_for_recipe` / `replace_steps_for_recipe` /
  `replace_step_images_for_recipe` after a `save_changes()` (R-064), exactly as
  `seed_dense.py` does.

## [OPEN] FU-753 — `PRICE_PICKER_CANONICAL_UNITS` is not narrowed by measurement system
- **Raised:** 2026-08-27 (owner feedback batch — units config)
- **Type:** finding
- **What:** `units.PRICE_PICKER_CANONICAL_UNITS` is a fixed server-side whitelist
  (`ml`/`L`/`g`/`kg`/`oz`/`lb`/`ea`/`dozen`/`pack`) that predates the measurement
  system and mixes metric and imperial mass in one list. The **client** picker in
  `PriceEntry.vue` now filters it by the install's system, so the UI is right; the
  server-side constant it derives from is not, and anything else reading that
  constant directly still sees both systems.
- **Why deferred:** the constant's only consumer is `supported_price_units()`,
  which feeds the same picker, so narrowing it server-side would be a second filter
  in front of the one that already works — and it is the sort of duplicate authority
  R-003 exists to prevent. The right fix is probably to derive the whitelist from
  `units_for_system` rather than to filter it twice.
- **Recommended resolution:** later, when price-entry is next touched.

## [OPEN] FU-751 — Firefox TTS improved but not verified on Firefox
- **Raised:** 2026-08-27 (owner feedback batch — settings/voice)
- **Type:** finding
- **What:** Owner asked *"TTS isn't supported on Firefox for some reason? What
  browsers can we support?"* The cause was identified as an empty voice list rather
  than a missing API (`'speechSynthesis' in window` was true, so Dora reported
  itself available and then said nothing), and the fix is shipped: the browser voice
  is probed for actual voices, Piper is probed unconditionally, a user on the device
  voice with no voices falls back to Piper, and Settings → Voice explains which
  engine is live. **None of it has been run in Firefox** — this session's browser
  pane is Chromium.
- **Why deferred:** no Firefox available in the pane.
- **Recommended resolution:** confirm in browser — open Dora in Firefox, go to
  Settings → Voice, and check that the note about missing device voices matches
  what Firefox actually reports, and that Dora still speaks via the neural voice.

Resolved entries carry one extra line, and live in `DORA_FOLLOWUPS_RESOLVED.md`:

```
## [RESOLVED] FU-NNN — short title
- **Raised:** YYYY-MM-DD (prompt id / task)
- **Type:** follow-up | deferred job | leftover | finding
- **What:** one or two lines.
- **Why deferred:** the reason it wasn't done in-line.
- **Recommended resolution:** now | later during <Phase/Prompt X> | when <trigger> | opportunistic
- **State note:** (filled in when resolved — date + how)
```

---

# Open

## [OPEN] FU-750 — Existing installs have no `food_category`, so every Health Star Rating scores 0% fvnl until a re-import
- **Raised:** 2026-08-27 (Health Star Rating build)
- **Type:** finding.
- **What:** `NutritionFood.food_category` is populated by the dataset importer
  from `food_category.csv`. It cannot be backfilled — the value lives in the
  source archive, not in anything already stored — so foods imported before
  migration `d1e5b8c3f7a2` keep NULL, `is_fvnl_category` returns False for all
  of them, and every recipe scores **0 fvnl points**. That is not neutral: on a
  dish with ≥13 baseline points it *also* locks out the protein credit (the
  FSANZ gate), so an unmigrated install's ratings are systematically pessimistic
  in exactly the wrong direction.
- **Why deferred:** the fix is "re-run the import", which is a user action, not
  a code change. What's missing is the *prompt* — the admin nutrition page says
  nothing about it, so an existing install has no way to know its ratings are
  thin.
- **Recommended resolution:** now-ish, and small — a banner on
  `AdminSystemNutritionSettings.vue` when `health_star_rating_enabled` is on and
  some non-zero share of `NutritionFood` rows have a NULL `food_category`.
  Needs one count endpoint or an extra field on the existing dataset-status
  response.

## [OPEN] FU-749 — Fruit *juices* and fried potato products score full fvnl points
- **Raised:** 2026-08-27 (Health Star Rating build)
- **Type:** finding.
- **What:** the fvnl test keys off USDA's food-group description, and two of the
  five qualifying groups contain members HSR would treat differently.
  *Measured* on SR Legacy: "Fruits and Fruit Juices" is 355 rows of which **88
  are juices/nectars**, and "Vegetables and Vegetable Products" is 814 rows of
  which **36 are fried/chip-shaped** (french fries, crisps, tempura). The guide
  does allow juice to score, so that half is arguably correct for a recipe; the
  fried-potato half is the clearer miss.
- **Why deferred:** it moves a rating by at most one V-point band on a recipe
  built mostly of chips, and the fix is a name-level exclusion list, which is
  the kind of heuristic that wants a real example to justify it rather than
  being written speculatively.
- **Recommended resolution:** opportunistic — revisit if a real recipe rates
  visibly wrong. The place to fix it is `features/nutrition/food_categories.py`,
  which already owns the vocabulary.

## [OPEN] FU-748 — Health Star Rating uses raw ingredient weight as its per-100g denominator
- **Raised:** 2026-08-27 (Health Star Rating build)
- **Type:** decision, recorded rather than open.
- **What:** HSR scores per 100 g of the food **as consumed**. Dora sums *raw*
  ingredient weights, so a sauce that reduces reads too kindly and a soup made
  with water nobody listed as an ingredient reads too harshly. An optional
  "finished weight" field on the recipe would make it exact.
- **Why deferred:** the owner's explicit call 2026-08-27 was to accept the
  approximation and label the rating an estimate rather than add a field most
  people would leave blank. Logged so the trade-off is findable rather than
  buried in a module docstring, and so a future complaint about a soup's rating
  has somewhere to land.
- **Recommended resolution:** when <someone reports a rating that looks wrong on
  a reduced or watered dish>.

## [OPEN] FU-746 — The AU/NZ Health Star Rating nudge has no automated cover
- **Raised:** 2026-08-27 (Health Star Rating build)
- **Type:** finding.
- **What:** `isAustralasian` in `AdminSystemRegionSettings.vue` decides whether
  "Match this device" offers the rating. It reads the IANA timezone *and* the
  BCP-47 region — the timezone half was added after finding this machine
  reports `en-GB` with `Australia/Sydney`, which the language-only version would
  have silently ignored forever. It was verified live, once, on one device.
- **Why deferred:** the function is private to the SFC, so pinning it means
  extracting it — worth doing, but it is a lookup with no state, and the verify
  stance says automate stable contracts, not everything.
- **Recommended resolution:** opportunistic — lift `isAustralasian` into a
  plain `.ts` helper and give it a table test (`en-GB`+`Australia/Sydney` → true,
  `en-AU`+`UTC` → true, `en-GB`+`Europe/London` → false, `Pacific/Fiji` → false).

## [OPEN] FU-744 — Recipe tool derivation has no migration for existing structured recipes
- **Raised:** 2026-08-27 (recipe-view feedback batch)
- **Type:** finding.
- **What:** a structured recipe's `tool_ids` is now the union of its steps'
  tools, re-derived on every create/update. Recipes last saved *before* this
  keep whatever tool set was typed by hand until something PATCHes them — so
  the cookbook's tool filter can disagree with what the steps say, in either
  direction, on untouched recipes.
- **Why deferred:** pre-release, no real users, and the drift self-heals on the
  next save of each recipe. A one-shot data migration over every structured
  recipe is more risk than the inconsistency is worth right now.
- **Recommended resolution:** opportunistic — a data migration calling
  `sync_recipe_tools_from_steps` for every recipe with `steps_mode='structured'`
  would close it in about ten lines, if the filter ever misbehaves visibly.

## [OPEN] FU-743 — `web_app/test/` is outside the lint script, and already has an error in it
- **Raised:** 2026-08-26 (recipe-view feedback batch)
- **Type:** finding.
- **What:** `npm run lint` globs `./src*/**/*` only, so nothing has ever linted
  `web_app/test/`. Running eslint over it by hand turns up one real error —
  `test/unit/useBuyVerdict.spec.ts:34` uses an `import()` type annotation, which
  `@typescript-eslint/consistent-type-imports` forbids. Pre-existing; found while
  checking this batch's own files.
- **Why deferred:** widening the lint glob is a repo-wide config change that may
  surface more than one error, and this batch's files lint clean on their own.
- **Recommended resolution:** opportunistic — one line in `package.json` plus
  whatever the widened run reports.

## [OPEN] FU-742 — The recipe facts strip got longer when it gained icons
- **Raised:** 2026-08-26 (recipe-view feedback batch)
- **Type:** finding.
- **What:** every fact in the masthead (Serves · Prep · Cook · Total · Difficulty
  · When) now carries a glyph, which adds ~18px each. Measured live at 375px: the
  strip has 72px of overflow inside its own `overflow-x: auto` container. The page
  itself doesn't scroll sideways (0px) and the sideways strip is the design, so
  nothing is broken — but before the icons it very likely fitted, and the last
  fact now needs a swipe.
- **Why deferred:** the owner asked for the icons explicitly, and hiding the
  labels on narrow screens to buy the space back would trade a swipe for an
  unlabelled glyph. Wants an eye on it before anything changes.
- **Recommended resolution:** with the `DORA_VERIFY` phone walk of the 2026-08-26
  batch — if it reads badly, the levers are dropping `Total` (it's derived from
  the two beside it) or shrinking the icon.

## [OPEN] FU-741 — `is_favourite` on a new recipe version resets deliberately; nothing says so in the UI
- **Raised:** 2026-08-26 (recipe-view feedback batch)
- **Type:** finding.
- **What:** while auditing "new version doesn't copy all fields properly" (the
  real cause was sections — fixed), three fields were confirmed to be *deliberately*
  not copied: `is_favourite` (reset to false), `last_made_on` (null) and
  `available_meals` (0). Each is defensible — they're facts about a recipe's history
  in the household, not about the recipe — and each is commented in
  `new_recipe_version.py`. But the toast only says "Both versions are equal peers",
  so a user who favourited the original and then makes a v2 sees it silently
  un-favourited and may well read that as the same copy bug.
- **Why deferred:** it's a copy/UX question, not a defect, and the batch's ask was
  the actual missing data.
- **Recommended resolution:** opportunistic — either say it in the toast caption or
  decide `is_favourite` should in fact carry (the other two clearly shouldn't).

## [OPEN] FU-740 — No bulk "Remove" on the shopping list: there is no remove-by-line-ids endpoint
- **Raised:** 2026-08-26 (shopping-list feedback batch)
- **Type:** leftover.
- **What:** the rebuilt bulk bar carries Tick / Untick / Move to list…, but no
  Remove. Stock overview's equivalent has destructive actions, so its absence is
  noticeable once you're selecting things. The blocker is that
  `shoppingListApiService` has `bulk-add` and `bulk-remove-by-stock-item` but no
  "remove these line ids", and looping N `deleteLineAsync` calls is precisely the
  per-item request loop [[FU-713]]/[[FU-714]] exist to eliminate.
- **Why deferred:** the feedback batch didn't ask for it, and adding an endpoint
  plus a UI affordance unprompted is scope growth. A comment in
  `ShoppingListDetail.vue`'s bulk bar records the reasoning in place.
- **Recommended resolution:** opportunistic — next time `bulk_operations.py` is
  touched. `BulkRemoveByLineIdsHandler` is a near-copy of the existing
  by-stock-item one.

## [OPEN] FU-739 — Run and receipt faces weren't re-driven after the 2026-08-26 toolbar rebuild
- **Raised:** 2026-08-26 (shopping-list feedback batch)
- **Type:** follow-up.
- **What:** the session drove the **plan face** hard at 375px and 1280px (row
  relayout, bulk bar, store card, finish dialog, live move-to-new-list) and only
  passed through the run and receipt faces in transit. Both share the rebuilt
  toolbar — the run face gains "Switch list" where the rail would be, the receipt
  face gains Amend and Put away — and both were only seen as a side effect of
  starting/finishing a shop, not walked.
- **Why it matters:** the run face is the one surface designed for a thumb in a
  supermarket, and its sticky footer plus the new destructive footer now both sit
  at the bottom of the page. Nothing observed suggested they collide, but that
  combination was never looked at deliberately.
- **Recommended resolution:** now-ish — folds into [[FU-729]]'s real-device walk,
  which is already owed for exactly these two faces.

## [OPEN] FU-738 — The lifecycle CTA is the button that scrolls off the shopping-list toolbar
- **Raised:** 2026-08-26 (shopping-list feedback batch)
- **Type:** finding (needs an owner call).
- **What:** the rebuilt toolbar is a sideways-scrolling band, as asked ("horizontal
  scrollable toolbar, no overflow menu"). With the full set on — New list · Add
  item · Bulk select · Templates · Refresh deals · Export · Start shopping — it
  needs ~1000px, and at 1280px the lists rail leaves the main column ~948px. So
  the band scrolls, and the button clipped at the right edge is **the lifecycle
  CTA**, the most important one on the page.
- **Why deferred:** it is the requested behaviour working correctly, not a bug,
  and every fix is a design trade: pin the CTA outside the scroller, put it first,
  or let the band wrap on desktop and scroll only on phones. That's an owner call,
  not an implementation detail.
- **Recommended resolution:** now-ish — one decision, then a few lines. Worth
  pairing with the `DORA_VERIFY` walk, since it's most obvious at desktop widths.

## [OPEN] FU-737 — The preview pane could not paint this session; screenshots and Quasar popups were unverifiable
- **Raised:** 2026-08-23 (recipe-view feedback batch)
- **Type:** finding.
- **What:** every `computer{action:"screenshot"}` timed out and
  `requestAnimationFrame` never fired in the preview tab, so Quasar's
  transition-driven surfaces (`q-menu` option lists, and therefore every
  dropdown's contents) stayed stuck mid-enter at 0×0. Dialogs, layout, computed
  styles and the DOM were all readable and were what this unit's verification
  ran on; nothing *visual* was confirmed by eye. Restarting the tab, closing the
  second tab and resizing all failed to recover it.
- **Why deferred:** it's an environment fault, not app code — but it means
  "verified" for this unit reads "verified structurally", and the next session
  should know why there are no screenshots.
- **Recommended resolution:** opportunistic — if it recurs, try a fresh preview
  server rather than a fresh tab, and fall back to the real-Chrome surface.

## [OPEN] FU-736 — Ingredient free-text flow has no automated cover; the Quasar slot trap that caused it is unguarded
- **Raised:** 2026-08-23 (recipe-view feedback batch)
- **Type:** finding.
- **What:** the "Add ingredient doesn't allow free text" defect had a precise
  cause: `QSelect.getAllOptions()` returns the `no-option` slot **instead of**
  the whole option list — `before-options`/`after-options` included — so the
  free-text action, offered only from `after-options`, disappeared exactly when
  the filter matched nothing. Fixed by offering it from both slots. A component
  spec was written to pin it and **abandoned**: the option menu never renders
  under vitest's jsdom (Quasar's position engine needs `requestAnimationFrame`),
  so the assertion could only ever have tested the mount, not the slot.
- **Why deferred:** the remaining route is a Playwright spec, which the
  2026-07-20 verification stance rules out for feature flows.
- **Recommended resolution:** **confirm in browser** (also listed in
  `DORA_VERIFY.md` → Cookbook / recipe page). If the same slot trap shows up a
  third time, promote it to a "known fixes" entry in `ENGINEERING_STANDARDS.md`
  rather than a test.

## [OPEN] FU-735 — per-serving `kcal` is a masthead fact but isn't in the masthead edit grid
- **Raised:** 2026-08-23 (recipe-view feedback batch)
- **Type:** leftover.
- **What:** the masthead's edit face carries name, collection, cuisine, category,
  serves, prep, cook, difficulty and when. **Per-serving kcal** is displayed as a
  fact but is still only editable from the "Calories" disclosure below (and in
  complex nutrition mode it's server-derived, so it isn't editable at all) — so
  one visible fact doesn't flip with its neighbours.
- **Why deferred:** scope — the owner's batch didn't name it, and the right
  answer depends on whether simple-mode kcal should live in the masthead at all
  now that the disclosure list is shorter.
- **Recommended resolution:** opportunistic — next time the recipe masthead or
  the nutrition mode split is touched.

## [OPEN] FU-734 — Recipe-page masthead selects have no accessible name
- **Raised:** 2026-08-23 (recipe-view feedback batch)
- **Type:** finding.
- **What:** in the masthead's edit face the five `BaseSelect`s (collection,
  cuisine, category, difficulty, when) read as bare `generic` in the
  accessibility tree — Quasar renders the label as a `div`, not a `<label for>`,
  so nothing associates it. The `q-input`s beside them are fine. This is a
  `BaseSelect`-wide trait, not specific to this page (the same shows on every
  surface that uses it), which is why it isn't fixed inline here.
- **Why deferred:** fixing it properly means giving `BaseSelect` an
  `aria-labelledby` wired to its own label id, app-wide — a shared-component
  change with ~72 call sites' worth of blast radius, not a recipe-page edit.
- **Recommended resolution:** now-ish, as its own small unit — it is a
  one-component fix with a broad win, and A6/axe coverage would catch it.

## [OPEN] FU-732 — Sub-cent unit prices still read "$0.00 / g" everywhere except the recipe cost modal
- **Raised:** 2026-08-24 (recipe-view feedback batch).
- **Type:** finding.
- **What:** `formatMoney` formats to the currency's minor unit, so a price of
  $0.003/g renders as **$0.00 / g** — a real price that reads as free. The new
  recipe cost modal fixes it locally (`unitPriceLabel` in
  `RecipeCostDialog.vue` re-quotes g→kg and ml→L when the figure is under 5c),
  but that is one call site's patch, not a shared rule. Anywhere else that
  prints a per-unit price off a fine-grained unit has the same bug — the
  shopping-list line price rows and the stock-item price surfaces are the
  likely ones; not surveyed.
- **Why deferred:** the reported surface was the recipe page, and the fix that
  belongs in `useMoney` (a `formatUnitPrice(amount, unit)` that owns the
  rescale, R-003) is a cross-surface change with its own verify.
- **Recommended resolution:** when money formatting is next touched — promote
  `unitPriceLabel` into `useMoney` and point every per-unit price at it.

## [OPEN] FU-731 — `q-popup-edit` on a phone: the keyboard-over-the-field problem is only fixed for free-text instructions
- **Raised:** 2026-08-24 (recipe-view feedback batch).
- **Type:** finding.
- **What:** the owner reported that editing free-text instructions on a phone
  opened the keyboard over the input with nothing to scroll. That path now goes
  through a maximised dialog (`RecipeMethodEditorDialog`) and is fixed. The
  same `q-popup-edit` pattern used to drive the recipe **title**, the eyebrow
  selects, the six **facts**, a structured **step's text** and an ingredient's
  **quantity** — and there is nothing about the reported failure that is
  specific to the instructions field. It may simply not bite on the short ones
  (a popup anchored to a short field near the top of the page has room), which
  is exactly what the owner described.
- **Narrowed by the 2026-08-24 merge (R-055 port).** The masthead popups and the
  ingredient-quantity popup are gone — the masthead flips as a block and the row
  opens its own editor. **Two** popups remain on this page: a structured step's
  text and a section's name. This FU now covers only those two.
- **Why deferred:** it needs a real device to know which of them actually
  misbehave; converting all of them to dialogs unprompted would undo the
  inline-editing feel the page was built around.
- **Recommended resolution:** when the phone walk in `DORA_VERIFY.md` (recipe
  section, 2026-08-24) runs — fix only the ones that reproduce.

## [OPEN] FU-730 — `Recipe.updated_at` is stamped by the PATCH handler only
- **Raised:** 2026-08-24 (recipe-view feedback batch).
- **Type:** finding.
- **What:** the new edit stamp is written in `update_recipe.handle`. Deliberate
  — cooking, favouriting and meal-pool adjustments change what *happened* to a
  recipe, not what it is, and the version panel would be useless if "last
  updated" moved every time you cooked. But two writers do change the recipe's
  content and don't stamp it: the **URL/text importer**
  (`import_recipe_from_content.py`) when it writes into an existing recipe, and
  any future bulk/vocabulary migration that rewrites recipe rows in place.
- **Why deferred:** the importer's overwrite path isn't reachable from the
  recipe page (FU-689 closed won't-do), so nothing user-visible is wrong today.
- **Recommended resolution:** opportunistic — whenever a second recipe write
  path is added, stamp it there too (or lift the stamp into the repository's
  save path for `Recipe`).
## [OPEN] FU-729 — Run/receipt faces have never been walked on a real phone
- **Raised:** 2026-08-23 (FU-727 build)
- **Type:** follow-up.
- **What:** both new faces were driven in a 430×900 headless Chrome and behave
  correctly, but the run face is the one surface in the app explicitly designed
  for a thumb in a supermarket — 60px rows, whole-row tap target, a bottom sheet
  under a real on-screen keyboard, and a sticky footer that must not cover the
  last row. None of that is proven by a headless viewport.
- **Why deferred:** it needs the owner's own device.
- **Recommended resolution:** now-ish — see the Shopping list section of
  `DORA_VERIFY.md`.

## [OPEN] FU-728 — Cook mode and Stocktake are the other two surfaces R-054 applies to
- **Raised:** 2026-08-23 (FU-727 / ADR-050)
- **Type:** finding.
- **What:** R-054 ("a lifecycle phase that changes what the user *does* gets its
  own composition") was established from the shopping list, but two other
  surfaces have the same shape: cook mode (planning vs cooking) and Stocktake's
  three-phase runner (review / walk / sweep). Neither was inspected in this unit.
- **Why it matters:** the rule's whole point is that the wrong shape is invisible
  — nobody notices a missing surface when something is already rendering. If
  either of those is a disabled-copy-of-one-surface, the same hidden-feature cost
  applies.
- **Recommended resolution:** opportunistic — next time either surface is
  touched, read it against R-054 before adding to it. Not worth a sweep of its
  own.

## [OPEN] FU-725 — Line-price ladder has no e2e coverage of the historic rung
- **Raised:** 2026-08-23 (shopping-list redesign)
- **Type:** test gap.
- **What:** `compute_list_totals` + the store breakdown are unit-tested
  (`tests/test_shopping_list_store_breakdown.py`, 7 cases) and the sectioning is
  covered in `useLineSections.spec.ts` (19 cases). The **ladders themselves** —
  actual→historic→offer for money, and purchased→usual→historic→offer for store —
  run inside `GetShoppingListDetailHandler` and are only verified by having been
  driven once in a browser against seed data.
- **Why it matters:** these are exactly the "stable, low-churn domain contract"
  the verification stance says is worth pinning, and a silent regression would
  show up as *wrong money*, which is the least forgivable kind.
- **Recommended resolution:** opportunistic — next time the detail handler is
  touched. One e2e test per rung, asserting `estimate_source` and
  `resolved_store_id`, would cover it.

## [OPEN] FU-724 — `src-pwa/custom-service-worker.ts` is dead code, and it's the file you'd reach for
- **Raised:** 2026-08-23 (offline read-only work)
- **Type:** finding.
- **What:** `web_app/src-pwa/custom-service-worker.ts` is never built. Its own
  header says it is picked up "ONLY if `workboxMode` is set to `InjectManifest`",
  and `quasar.config.ts:238` sets `workboxMode: 'GenerateSW'`. The service worker
  that actually ships is generated from `extendGenerateSWOptions` in
  `quasar.config.ts` (that's where the `/api/**` `NetworkFirst` rule and the
  navigate-fallback live).
- **Why it matters more than ordinary dead code:** now that **offline is
  read-only (R-052)**, the read cache *is* the offline story — and the file a
  future agent will open to change offline caching behaviour is the one named
  `custom-service-worker.ts`. Edits there would have no effect, silently, with
  no build error and no test failure. That's the same invisible-failure shape as
  FU-719/FU-720.
- **Why deferred:** deleting it is a one-liner but it's outside the scope of the
  read-only change, and it's worth a moment's thought first: either delete it, or
  switch to `InjectManifest` and move the runtime-caching rules into it (a real
  choice — `GenerateSW` is the lower-friction route the config comment
  deliberately picked, so deleting is the likely answer).
- **Recommended resolution:** opportunistic. If deleting, leave a one-line
  pointer comment in `quasar.config.ts` saying the SW is generated there, so the
  next person looks in the right place.

## [OPEN] FU-722 — voiced text loses the start of the sentence (unconfirmed; two candidate fixes shipped)
- **Raised:** 2026-08-23 (cook-mode voice feedback)
- **Type:** finding.
- **What:** the owner reports Sous Chef "cuts out the beginning of the sentence
  frequently — random how much gets cut", on mobile, over VPN, and suspects it
  affects anywhere text is voiced. **Ruled out server-side:** `POST /api/tts`
  buffers the entire WAV (`tts_synthesize.py:187` — `subprocess.run` +
  `capture_output`, no streaming, no trim), `res.blob()` awaits the whole body,
  and the default voice params leave `pitch_semitones` at 0.0 so the ffmpeg
  pitch-shift path (the one place a malformed piped WAV header could appear) is
  never entered. The audio leaving the server is complete and well-formed, so
  this is client-side playback.
- **Two candidate fixes shipped 2026-08-23** in `useSpeechOutput.ts`, both
  correct hardening on their own merit but **neither confirmed to be the cause**:
  (a) `speakBrowser` had a redundant second `synth.cancel()` immediately before
  `synth.speak()` — Chrome/Android treat `cancel()` as internally async and clip
  or drop an utterance queued in the same task, by a varying amount, which is
  exactly the reported signature. Removed, plus a 120ms settle when something
  was genuinely still speaking. (b) `playPiper` called `audio.play()` on a
  freshly constructed element; now waits for `canplay`/`canplaythrough` (1.5s
  cap) with `preload='auto'`, so playback can't start ahead of the decoder.
  (c) the third candidate — recognizer restarts stealing audio focus
  mid-playback, the only one that explains "mobile, in cook mode" — was fixed
  too on 2026-08-23; see **FU-723 (resolved)**. All three candidates are now
  addressed, so a retest that still clips means the cause is something none of
  us has thought of yet.
- **Diagnosability fixed 2026-08-23.** `useSpeechOutput` now tracks
  `lastEngine` ('piper' | 'browser'), and cook mode's Sous Chef popover shows
  **"Voice: Piper (server)"** or **"Voice: Browser fallback"** once she has
  spoken. This was the missing instrument: the fallback was silent, the two
  engines clip for different reasons, and over a slow VPN a Piper timeout
  falling back to the browser is likely — so knowing which one spoke decides
  which mechanism you are looking at.
- **Why deferred:** unreproducible from this session — it needs a real phone, a
  real VPN hop, and an ear. **A diagnosability gap makes it worse:** the Piper→
  browser fallback is completely silent, so the owner cannot tell which engine
  actually spoke, and the two engines have *different* clipping mechanisms. Over
  a slow VPN a Piper timeout falling back to the browser voice is very likely,
  which would mean the symptom he sees is (a), not (b).
- **Recommended resolution:** now — confirm on the phone. **Open the Sous Chef
  "?" popover first and note which engine is speaking**; that single fact
  decides which of the three fixes was even relevant. Then: does it still clip?
  Does it clip in **Dora chat** too (no continuous mic there, so chat-clipping
  rules the FU-723 mechanism out and points at the engine)? If it still clips
  with the engine known, that's new information and this entry should be rewritten
  rather than extended — three plausible mechanisms have now been closed.

## [OPEN] FU-721 — revive `.github/workflows/` (CI + Release) and prove they actually work
- **Raised:** 2026-08-23 (owner request)
- **Type:** deferred job.
- **What:** both workflows are **fully commented out** — `ci.yml` (95 lines) and
  `release.yml` (164 lines), every line prefixed `#`, to preserve GitHub
  free-tier minutes during rapid Claude-assisted development. Uncomment them,
  then treat them as untested code: they have never run in their current shape,
  and the repo has moved under them for ~7 weeks (`ci.yml` last touched
  2026-07-10, `release.yml` 2026-07-01). Reviving them blind would just trade a
  silent gap for a red badge.
- **Known-stale already found (2026-08-23, static read):**
  - **CI pins Node 20 and that is now wrong.** `ci.yml`'s frontend job sets
    `node-version: "20"`, but `package-lock.json` resolves
    `@quasar/app-vite@2.6.0`, whose `engines.node` is `^30 || ^28 || ^26 || ^24
    || ^22`. The `Dockerfile` already moved to NodeSource 22 for exactly this
    reason. `web_app/package.json`'s own `engines.node` still lists `^20 || ^18`
    and is the stale one — reconcile all three, don't copy the loosest.
  - **`release.yml` has never been exercised at all** and is the riskier of the
    two (it builds + publishes). It predates the P8-01 Dashy-Dora rename
    landing, the Postgres-standard decision, and the current `dora.spec` /
    packaging layout, so its artifact names, image refs and version handling all
    need re-reading against today's reality rather than assumed-good.
  - **Verified fine, so don't "fix" it:** `pytest` in CI needs **no** live
    server. `tests/e2e/dora_api/conftest.py` calls `startup(is_test_env=True)`
    and adapts `http://localhost:5170/...` URLs onto a Flask test client, and
    `tests/db_backend.py` defaults to a throwaway SQLite file. A Postgres
    service container is *optional* (`DORA_TEST_DB=postgres`) and worth adding
    as a second matrix leg only if the SQLite-vs-Postgres divergence class
    (FU-526 / FU-533) is judged worth the minutes.
  - Both suites are green locally as of 2026-08-23 (backend 1936 passed,
    frontend 502 vitest, `vue-tsc` clean), so a red CI on first run means the
    workflow is wrong, not the code — a useful signal to keep in mind.
- **Why deferred:** the standing policy is that these stay commented during
  rapid development to protect the GitHub free tier, and that policy hasn't
  changed yet — reviving them mid-stream would burn minutes on every push of a
  branch that changes 20 times a day. This FU is the record of the debt, not a
  licence to switch it on now.
- **Recommended resolution:** when the feedback-polish stream slows, or at the
  first real release — whichever comes first. It gates/pairs with **FU-405**
  (ops/CI), which in turn gates FU-520 and FU-404, and it belongs with the
  Phase-4 open-source release work (FU-406). Do CI first and let it go green on
  a throwaway branch before touching `release.yml`; a broken release workflow is
  discovered at the worst possible moment.

## [OPEN] FU-720 — nothing verifies the deployed route map; a deploy can delete a feature silently
- **Raised:** 2026-08-23 (FU-717 post-mortem)
- **Type:** finding.
- **What:** FU-717 was an rsync exclude (`--exclude='data'`, unanchored) deleting
  `dora_api/features/data/` from the server on every deploy. The app then booted
  **completely clean** — no warning, no error, healthcheck green — and served
  `"Endpoint was not found."` for all 15 endpoints that had silently vanished.
  There is no boot-time or post-deploy check that the route map is what the
  build intended, so a whole feature can disappear and the only signal is a user
  hitting a page weeks later.
- **Why deferred:** wants a decision on shape before building. Options, cheapest
  first: (a) log the registered route count per blueprint at boot, so
  `DATA_ROUTER: 0 routes` is visible in `docker compose logs`; (b) a boot
  assertion that every `*_ROUTER` in `features/routers.py` has ≥1 rule — a
  blueprint with none is always a packaging bug, never intentional; (c) a
  post-deploy smoke script that curls one known endpoint per blueprint. (b) is
  the strongest per line of code and would have failed this deploy loudly at
  startup. Pairs naturally with **FU-719** (same file, same class of silent
  discovery failure) and belongs with the ops/CI work in FU-405.
- **Recommended resolution:** opportunistic, or now alongside FU-719 — the two
  are one small hardening pass over `startup.py` / `infrastructure/utils.py`.

## [OPEN] FU-719 — `_iter_submodules` silently swallows a feature subpackage that fails to import
- **Raised:** 2026-08-23 (chasing FU-717)
- **Type:** finding (robustness / diagnosability).
- **What:** route discovery is
  `get_attributes_ending_with('router', 'dora_api.features')` →
  `_iter_submodules` (`infrastructure/utils.py:47`), which calls
  `pkgutil.walk_packages(pkg.__path__, prefix=...)` **with no `onerror`**.
  Verified against the CPython source in this venv: when `walk_packages`
  imports a subpackage to recurse into it, `except ImportError:` with
  `onerror is None` **swallows the error and moves on**. So if any
  `dora_api/features/<x>/__init__.py` fails to import, that entire feature's
  modules are never yielded, its routes are never attached to the blueprint,
  and **the app boots perfectly happily** — the blueprint still registers
  (every `*_ROUTER` lives in `features/routers.py`, which is imported
  independently), just with a hole in it. The user-visible result is exactly
  FU-717's shape: some `/api/*` paths serve normally, others return the app's
  own `"Endpoint was not found."` 404 (via the middleware for
  POST/PATCH/DELETE, or `serve_spa.py:110`'s catch-all for GET), with nothing
  in the logs. Non-package modules are imported by `_iter_submodules` itself
  and *do* raise loudly, so this hole is subpackage-granular only.
- **Not the cause of FU-717** (checked 2026-08-23): that turned out to be an
  rsync exclude *deleting* `features/data/` off the server, and an absent
  directory yields no subpackage and no ImportError — there was nothing for this
  hole to swallow. It stays open on its own merit: the failure mode is real and
  would be indistinguishable from FU-717 if it ever fires.
- **Why deferred:** wants the owner's go-ahead — it's infrastructure the whole
  app boots through, and the fix should be verified against a deliberately
  broken feature package.
- **Recommended resolution:** now, alongside **FU-720** (same file, same class of
  silent discovery failure — one hardening pass covers both). Pass an
  `onerror` that logs the module name + exception and **re-raises**: a feature
  that can't import should fail the boot loudly, not serve a silently
  incomplete API. Whatever the cause of FU-717, this is worth doing on its own
  merit — it is the reason a whole-blueprint hole is invisible.

## [OPEN] FU-716 — Backup & Restore page bypasses the API service layer
- **Raised:** 2026-08-23 (image-quality settings split)
- **Type:** finding (R-005 / portable data access + one HTTP client).
- **What:** every call in `AdminDataBackupRestore.vue` is a hand-rolled `fetch`
  with `credentials: 'include'` and a hand-assembled `csrfHeader()`, rather than
  going through `AxiosHttpClient` / an api service. Consequences: no
  `X-Request-Id` correlation id, so a failure like FU-717 has no matching server
  log line to look up; no normalised error, so the toast caption is a raw
  `Error: List failed (404)` instead of `toastCaption(err)`; and no shared retry
  policy. `backup_retention_count` / `backup_storage_path` are also absent from
  the `AppSettings` type, which is *why* the page reached for raw `fetch` in the
  first place — `image_quality` / `image_max_dimension` were in the same boat
  and were added to the type when the image card moved out (2026-08-23).
- **Why deferred:** the current unit only moved the image card; rewiring five
  more call sites (create / download / restore / delete / library settings,
  two of which stream files) is its own change and wants its own verify.
- **Recommended resolution:** opportunistic — fold in next time this page is
  touched, or immediately after FU-717 is diagnosed, since the correlation id
  is exactly what would have made FU-717 a five-minute answer.

## [OPEN] FU-715 — reported "Needs attention filter is broken" did not reproduce
- **Raised:** 2026-08-22 (stock-overview feedback batch)
- **Type:** finding.
- **What:** the owner reported the **Needs attention** chip as broken "since
  recent changes", then on being asked for the symptom said "seems to work now,
  skip". Logged rather than dropped, per the standing rule — a report from real
  usage plus a static read that finds nothing is not proof it is fixed. What the
  investigation *did* establish: `24ca1786` replaced the composite client-side
  predicate with a bare `item.needs_attention === true` read
  (`useStockFilters.ts:217`) and deliberately provides **no client fallback**, so
  the chip matches nothing at all if the server field is absent — a stale API
  build, a cached bundle, or any `StockItem` that reached the store without going
  through `GET /stock-items` hydration. Two adjacent live gaps found on the way,
  either of which could produce "it's broken" intermittently: (a) optimistic /
  offline-queued mutations no longer recompute attention, so an essential item set
  to Out doesn't enter the filter until a refetch (`stockItemStore.ts:133`,
  `:177-181`); (b) the rule honours `AlertPreference` mutes but not
  `AlertInteraction` snooze/dismiss, unlike the bell (`get_alerts.py:284-341`) —
  so the chip and the bell disagree on a real install. Existing coverage is green
  (35 `useStockFilters` unit tests, 69 backend attention tests).
- **Why deferred:** owner said it works now; no reproduction to fix against.
- **Recommended resolution:** confirm in browser — specifically after a bulk
  action or an offline-queued edit, which is where (a) would bite. Cross-ref
  [[FU-702]] (same coupling on the "Expiring soon" chip).

## [OPEN] FU-714 — `useShoppingListActions.addItems` still loops; the bulk endpoint exists now
- **Raised:** 2026-08-22 (bulk-endpoint work)
- **Type:** leftover.
- **What:** the stock overview's bulk paths were moved onto
  `POST /api/shopping-lists/<id>/lines/bulk-add`, but `addItems`
  (`useShoppingListActions.ts:41`) still `await`s `addLineAsync` per item. It has
  ~16 call sites and several pass genuinely multi-item arrays — "add all missing
  ingredients" on both recipe pages, `DoraChat`'s matched-items add, the
  stock-item detail substitutes/related adds, `StocktakeRunner`, `QuickAddSheet`.
  Those surfaces still pay one round-trip per item.
- **Why deferred:** out of the reported scope (stock overview), and `addItems`
  accepts full `AddLineCommand`s — product-anchored lines, quantities,
  `selected_product_id` — which the bulk endpoint doesn't take. Doing it properly
  means either widening the endpoint's request model or branching on "is every
  command a bare stock_item_id", and the branch is the kind of implicit
  cleverness R-019 warns about.
- **Recommended resolution:** opportunistic — next time shopping-list adds are
  touched. Widening `bulk-add` to accept the same line shape as `AddLineHandler`
  is the cleaner of the two options.

## [OPEN] FU-713 — bulk set-level and bulk add/remove commit once per item
- **Raised:** 2026-08-22 (bulk-endpoint work)
- **Type:** finding.
- **What:** `bulk-set-level`, `bulk-add` and `bulk-remove-by-stock-item` loop the
  existing single-item handlers server-side, and each of those ends in its own
  `save_changes()`. So a 40-item bulk restock is 1 HTTP round-trip but 40 commits.
  That was a deliberate trade — a level change stamps two timestamps, appends a
  `StockLevelChange`, may record a `ConsumptionEvent` and may fire the auto-add
  hook, and a second implementation of that would drift (R-003) — but it means
  the win is latency, not database work. `bulk-move` does not have this shape; it
  is two queries and one commit.
- **Why deferred:** correctness first, and the reported symptom was latency.
- **Recommended resolution:** when <a bulk action is measurably slow on a real
  pantry>. The fix is to let the inner handlers defer their commit (an explicit
  `commit: bool` argument, not an implicit unit-of-work), not to inline the rules.

## [OPEN] FU-712 — `expiryIndicator` tooltips now format dates; check the two recipe pages don't drift
- **Raised:** 2026-08-22 (expiry-menu work)
- **Type:** leftover.
- **What:** `expiryIndicatorFor` was echoing the raw ISO date into its tooltip
  (a D-006 violation) and now routes through `formatDate`. The recipe page builds
  the *same* two phrases ("Expired {when}" / "Expires {when}") by hand rather than
  calling the helper — which is how the ISO leak survived in the first place.
- **Why deferred:** out of scope; the page was mid-redesign with two live copies
  and folding them in would have collided.
- **Recommended resolution:** **now-ish — the blocker cleared.** [[FU-688]]
  resolved 2026-08-26 and there is only one recipe page again
  (`web_app/src/pages/RecipeDetailPage.vue`, formerly `RecipeDetailNext.vue`).
  Point the survivor at `expiryIndicatorFor` — search it for "Expires ".

## [OPEN] FU-711 — "open / in-use" wording is now split across surfaces
- **Raised:** 2026-08-21 (stock-item detail feedback batch)
- **Type:** finding.
- **What:** the detail page's row is now labelled **Opened** (owner-picked), but
  `StockItemRow.vue` still says "Mark as open / in-use" (aria-label + tooltip) and
  `components/help/AttentionRulesDialog.vue` still explains "the open / in-use toggle".
  Same control, two names.
- **Why deferred:** the feedback was scoped to the detail page; renaming the row's
  aria-label + the help copy touches the attention-rules explainer, which has its own
  wording review.
- **Recommended resolution:** opportunistic — next time either surface is touched, or
  as part of a copy sweep. One word, three call sites.

## [OPEN] FU-710 — Barcode register POSTs 404 on the owner's install (same module as the QR 404)
- **Raised:** 2026-08-21 (stock-item detail feedback batch)
- **Type:** finding.
- **What:** pasting an EAN into Add-barcode answered **"Endpoint was not found."** —
  the body Flask returns when *no route matched* (`middleware.handle_incoming_request` /
  the SPA catch-all), not a validation failure. Proven green here on 2026-08-21 against
  a real HTTP server (`POST /api/data/barcodes` with the owner's exact ISBN-13
  `9788817071673` → 200 + a `barcode_id`), and `GET /api/stock-items/<id>/qr?size=512`
  → 200 `image/png` in the same session. Both endpoints live in **one module**
  (`dora_api/features/data/barcodes.py`), and it is the *only* module whose endpoints
  the owner reports 404s from — so the running API almost certainly doesn't carry that
  module's routes, i.e. the server process is older than the SPA build talking to it.
- **Why deferred:** not reproducible from here; it's install state, not code.
- **Recommended resolution:** **confirm in browser** on the owner's install. Two
  one-minute checks: (a) open `<host>/api/data/barcodes/lookup?value=x` — a
  *third* endpoint in the same module — if that 404s too, the module isn't registered
  and restarting the backend fixes it; (b) the Add-barcode dialog now names a route
  miss explicitly ("This server has no barcode endpoint at … — its API is older than
  this page"), so the next attempt self-diagnoses. Paired with FU-648.

## [OPEN] FU-703 — Decide the fate of the product price axis (`/price-history`, My Products)
- **Raised:** 2026-08-21 (prices-surface UX investigation — `docs/05_investigations/PRICES_SURFACE_UX_ASSESSMENT.md`)
- **Type:** follow-up (structural decision)
- **What:** Products were demoted to a push-your-own-data niche, but **all** the
  price *reading* capability — compare up to 5, range control (30d/90d/1y/all),
  alerts — still lives on the product axis, on `/price-history`, which has **no
  nav entry at all** (reachable only from a My Products overflow item, a
  `SubscriptionsPanel` link, and the onboarding tour that calls it "Prices").
  The everyday user's own data (stock-item observations) gets a single-item
  modal with no range and no compare, so *"which of my items got more
  expensive?"* has no surface. Three options were put to the owner: absorb +
  retire the product surfaces; keep `/price-history` as an explicitly advanced
  page; or keep both and just fix nav + naming. Owner leans **option 3
  (keep both, fix nav + naming)** but wants more thought before committing.
  Answered in the same session and **not** part of this fork: the everyday user's
  jobs (all four — triage / lookup / capture / trend), placement (a **price lens
  on Stock overview** + a **trend section in Reports**; no new top-level nav
  entry), and alerts (**advanced-only, hide cleanly** — they need an inbound feed,
  so no stock-item watchlist). Those three are recorded as D2/D3/D4 in the memo.
- **Owner idea added 2026-08-24 — a "Shopping" tab on the stock item.** Rename
  the stock-item detail page's **Lists** tab to **Shopping**, and gather the
  money surfaces into it: the buy-verdict collapsible card (today on Overview),
  usual store, preferred buys, the price widget and the purchase-history log.
  Owner is "not 100% on this idea" and asked for it to be weighed here rather
  than built, because it is a **fourth candidate placement** for the everyday
  price job alongside the memo's D3 (price lens on Stock overview + trend
  section in Reports). Note the two aren't exclusive — D3 answers *"which of my
  items got more expensive?"* across the pantry, this answers *"what do I know
  about buying **this** one?"* on a single item, and it would give the buy
  verdict a home next to the price history it reasons from. Weigh it when this
  fork is decided; it changes nothing about the keep/cut call on `/price-history`
  itself.
- **PARTIALLY ANSWERED IN CODE 2026-09-02 (Reports chunk 4).** D3's *"trend
  section in Reports"* half is **built**: `/reports` now carries a **Price
  changes** card driven by a new `GET /reports/item-price-movers`, which ranks
  the user's own stock items by per-unit price movement inside the range and
  opens each one into the shared price chart. That answers the **trend** and
  **triage** jobs from D2 for a household with no product catalogue at all —
  which is the strongest evidence yet for the fork below, because the everyday
  price question now has a home that does not involve `/price-history`. Still
  open and unchanged: the **keep/cut call on the product-keyed surfaces**, and
  the D3 *"price lens on Stock overview"* half.
- **Why deferred:** owner's call; it decides whether FU-704…708 are polish on a
  surviving page or throwaway work on one that gets retired.
- **Recommended resolution:** now-ish, before any of FU-704…708 — it sets their scope.

## [OPEN] FU-704 — `PriceEntry` is desktop-shaped, and all its help is hover-only
- **Raised:** 2026-08-21 (prices-surface UX investigation)
- **Type:** finding
- **What:** The log-a-price form is the one screen used standing in a supermarket
  aisle on a phone, and it has no responsive treatment: **Price / Size / Unit
  three-across** in a bare `row q-gutter-sm` with no `col-12 col-sm-*`
  (`PriceEntry.vue:36`) — ~105px per field at 375px. `type="number"` with no
  `inputmode="decimal"`, so wrong keypad plus spinner arrows eating width. And
  every explanation is a `q-tooltip`, i.e. **hover-only and invisible on touch** —
  including the pack-count help (the most confusing field) and the two
  `help_outline` tooltips that *define* "usually" / "above usual", so the
  trust-critical copy is desktop-only. Also: the store select vanishes entirely
  when no stores exist (`v-if="storeOptions.length > 0"`) with no "add a store"
  path, silently removing the dimension that makes "where is this cheapest"
  answerable.
- **Why deferred:** out of scope of the read-only investigation; wants a single
  pass over the form rather than piecemeal edits.
- **Recommended resolution:** now — independent of FU-703; the form survives
  whichever way that decision goes.

## [OPEN] FU-705 — `PriceHistoryChart` has no touch interaction
- **Raised:** 2026-08-21 (prices-surface UX investigation)
- **Type:** finding
- **What:** The chart binds `@mousemove` / `@mouseleave` only
  (`PriceHistoryChart.vue:2`), so on a phone it is a static picture — the
  crosshair and value tooltip are unreachable and no number can be read off it.
  Fix is pointer events (`@pointerdown` / `@pointermove`) or an explicit
  "no chart below `sm`" decision. Same component, secondary issues: no y-axis
  unit label (nothing stops $/L and $/kg sharing one axis), 5 series draw 5
  dashed baselines in the same faint style with 5 labels stacked in the same
  right gutter, and `preserveAspectRatio="none"` will distort if the SVG is ever
  CSS-scaled.
- **Why deferred:** read-only investigation.
- **Recommended resolution:** now — it is shared by the widget sheet and the page,
  so it pays off under either FU-703 outcome.

## [OPEN] FU-706 — Logged prices can be deleted but never edited, and delete has no confirm
- **Raised:** 2026-08-21 (prices-surface UX investigation)
- **Type:** finding
- **What:** `deleteObservation` (`StockItemDetailPage.vue:1829`) fires straight
  through — no confirm, no undo — and there is **no edit path at all**. A
  fat-fingered `1250` for `12.50` poisons the median it feeds and can only be
  fixed by delete + retype. There is also no date field anywhere in
  `PriceEntry`: `observed_at` is server-set, so a receipt from yesterday cannot
  be entered. And the raw observation list under the widget is untitled,
  uncapped and ungrouped (no store/dimension grouping, no "show more") — it will
  run to hundreds of rows mid-Overview-tab for a frequently-logged item, in
  contrast to the History tab which does honest truncation.
- **Why deferred:** read-only investigation; edit needs a PATCH endpoint that
  does not exist yet.
- **Recommended resolution:** now-ish — the no-edit path is a data-quality hole in
  the dataset the whole feature exists to build.

## [OPEN] FU-707 — "Your prices" signal: only bad news, no confidence, four phrasings, silent dimension flip
- **Raised:** 2026-08-21 (prices-surface UX investigation)
- **Type:** finding
- **What:** `your_prices.py` is clean and correctly server-owned (R-003); the
  *presentation* has four problems. (1) **Only bad news gets a chip** —
  above-usual renders a warning chip, below-usual a muted `· about average` text
  fragment, so a money-saving app nags on overpay and stays silent on a win.
  (2) The **warning colour** implies user error when the fact is shelf inflation
  (D-rule colour semantics). (3) **Confidence is invisible** — 3 samples and 40
  render identically, with `Based on N prices` demoted to a caption under a
  full-strength conclusion. (4) **Four phrasings of one number** across surfaces:
  `Usually $X` / `Your usual: $X` / `Usually $X/L` / `above usual` vs
  `paying more than usual`. Separately: baselines are per-dimension and "the most
  recent dimension wins for the headline", so a single count-based log (`1 ea`)
  can move a mass-based item's headline baseline with **zero** UI signal.
- **Why deferred:** read-only investigation; the dimension-flip fix needs a
  server-side signal on the DTO, not just copy.
- **Recommended resolution:** now-ish. If it lands as described, run the ADR
  evaluation on the candidate rule noted in the memo §9 — *a domain signal must
  not be presented as a warning when the user did not cause it*.

## [OPEN] FU-708 — `/price-history` copy + affordance bugs (incl. 6 unresolved PRODUCT HISTORY feedback bullets)
- **Raised:** 2026-08-21 (prices-surface UX investigation)
- **Type:** finding
- **What:** **Mis-parented tooltip** — `All-time low: $X · currently N% above`
  (`PriceHistoryPage.vue:147`) carries a tooltip saying *"You're paying more than
  your own usual price… Not a comparison to the all-time-low"*, which contradicts
  the label it is attached to; that copy belongs on the "Your usual" line below,
  which already has its own. **"Manage alerts" cannot create an alert** — the
  modal only lists and deletes, so the prominent affordance is the incomplete
  one. On mobile the `col-12 col-md-3` picker rail stacks a 360px scrolling list
  *above* the chart on every visit, and the chart empty state still reads *"Pick
  one or more products on the left."* Also carries the still-open PRODUCT HISTORY
  feedback bullets PH3–PH9: squished card / clipped notify-under placeholder, no
  decimal formatting on the price input, tiny %-off text, %-off chip not using the
  shared deal chip (R-001), the graph not reaching the box edge (real — reserved
  right padding for baseline labels), and **PH7 "hover bubble not theme-aware,
  white on white in dark mode" — not reproduced in the static read, so per the
  mandatory rule it stays open and needs confirming in the browser.**
- **Why deferred:** read-only investigation, and the whole page's future is FU-703.
- **Recommended resolution:** after FU-703 — don't polish a page that may be
  retired. Exception: PH7 can be confirmed in the browser at any time.

## [OPEN] FU-702 — "Expiring soon" chip is coupled to the notifications system
- **Raised:** 2026-08-21 (stock-overview quick-filter review)
- **Type:** finding
- **What:** `isExpiryFlagged` reads `item.attention_kinds`, and the server filters
  those by the requesting user's `AlertPreference` (`get_stock_items.py:140`). So a
  user who mutes expiry *notifications* silently loses the **Expiring soon**
  *filter* — the chip stays on screen, tappable, and matches nothing. Owner's
  reaction: it's weird that a filter is tied to the notification system at all.
  Whether an item is near its expiry date is a fact about the item; whether Dora
  pings you about it is a preference. Suggested fix: carry an unfiltered expiry
  state on the DTO (computed from the household window, prefs not applied) and
  have the chip read that; leave `needs_attention` / the bell as the pref-aware
  pair. Same class of dead-control risk applies to **Needs attention** when a
  user mutes every kind.
- **Why deferred:** needs a DTO/contract change + a call on whether
  `needs_attention` should also stop honouring per-user mutes.
- **Recommended resolution:** now-ish — it's a live wrong-behaviour path, and the
  chip rename below wants to land in the same pass.

## [OPEN] FU-701 — "Expiring soon" wording + its overlap with "Needs attention"
- **Raised:** 2026-08-21 (stock-overview quick-filter review)
- **Type:** follow-up
- **What:** two things about the same chip. (a) The label says "Expiring soon" but
  the predicate also matches **already expired** items. (b) Its set is a strict
  subset of **Needs attention** (`expired ∪ expiring_soon` vs
  `expired ∪ expiring_soon ∪ essential_low`), so the row shows A∪B beside B as
  visual peers, and the only slice of A they don't share is roughly what the
  **Essential** chip gets you. Recommendation on the table: rename to a
  freshness-axis label that honestly covers both states, and decide whether the
  two chips collapse into one alert chip + a reason control.
- **Why deferred:** owner is choosing the wording.
- **Recommended resolution:** now — pairs with FU-702.

## [OPEN] FU-700 — the stocktake install switch isn't gated on the dashboard / help copy
- **Raised:** 2026-08-20 (stock-overview feedback batch).
- **Type:** leftover.
- **What:** `AppSetting.stocktake_enabled` now hides the Stock-overview button,
  the "Needs check" filter, the per-item mute toggle and the runner, and empties
  the server-side overdue map. Three surfaces still speak as if the feature is
  always on: `DoraScoreCard`'s "Do a stocktake" action (`/stock?stocktake=1`),
  `AttentionRulesDialog` + `StockRowLegend` ("due for a stocktake check"), and
  `AlertsPage`'s copy about the default stocktake reminder.
- **Why deferred:** the reported items were the overview and the per-item
  toggle; the Dora-Score action in particular needs a call on whether the score
  should still *carry* a staleness component when stocktake is off (server-side
  question), not just whether to hide a link.
- **Recommended resolution:** later, alongside FU-182's app-wide feature-gate
  sweep — or now if the owner intends to actually run with stocktake off.

## [OPEN] FU-699 — full backend suite not run for the stocktake-switch change
- **Raised:** 2026-08-20 (stock-overview feedback batch).
- **Type:** finding.
- **What:** the session was cut short mid-verification. What did run and pass:
  240 backend tests matching `stocktake or app_setting or settings or stock_item
  or health`, the refreshed `dto_snapshots.json` contract test (27 passed), the
  full frontend suite (504), `vue-tsc` (0 errors) and eslint on every touched
  file. The **whole** `pytest tests` run did not.
- **Why deferred:** out of session time.
- **Recommended resolution:** now — one `pytest tests -q` before this lands.

## [OPEN] FU-698 — "Deselect all" and "Cancel bulk select" are now the same action
- **Raised:** 2026-08-20 (stock-overview feedback batch).
- **Type:** design question.
- **What:** per owner feedback, Deselect-all now exits bulk mode (matching what
  unticking the last item already did), which makes it behaviourally identical
  to the toolbar's Cancel. It was kept because on a phone the bulk bar is what's
  on screen and the toolbar Cancel may be scrolled away — but two buttons doing
  one thing is the kind of thing D-rules exist to catch.
- **Why deferred:** removing a button the owner didn't ask to remove is his call.
- **Recommended resolution:** opportunistic — next time the bulk bar is touched.

## [OPEN] FU-697 — I destroyed the tail of the "later 8" worklog entry; partial reconstruction is in place
- **Raised:** 2026-08-20 (DR-15 micro-motion pass).
- **Type:** finding.
- **What:** while appending this session's worklog entry I first wrote it with
  PowerShell `Get-Content`/`Set-Content`, which in PS 5.1 reads as ANSI and
  mangled every em-dash in the file. Reaching for `git checkout --
  DORA_WORKLOG.md` to undo that was the actual mistake: `DORA_WORKLOG.md` had
  **uncommitted** changes (the *later 8* Cookbook-feedback-batch-3 entry), and
  the checkout took them with the corruption. I reconstructed that entry verbatim
  from a read taken at session start, which covered it down to the "Serves filter
  added" bullet; **anything it said past that point is gone.** The entry now
  carries a banner marking the truncation. Nothing else was affected — only
  `DORA_WORKLOG.md` was checked out, the code changes and every other modified
  file are intact, and the product-level record of that work survives in
  `CHANGELOG.md`.
- **Why deferred:** it can't be fixed by me — only the owner (or the session that
  wrote it) knows what the missing tail said. Filed so the gap is on the record
  rather than looking like the entry simply ended there.
- **Recommended resolution:** now, if the owner remembers what the batch-3 entry
  covered after the Serves filter (likely: the verify/close-gate sections); then
  delete the banner. Otherwise leave the banner and close.
- **Process note for the next session:** in this repo, edit these UTF-8 markdown
  logs with Python (`encoding='utf-8'`) or the Write/Edit tools — never PS 5.1
  `Get-Content`/`Set-Content` without `-Encoding utf8`. And never `git checkout
  --` a file that `git status` shows as modified; the logs are append-mostly and
  routinely carry uncommitted work.

## [OPEN] FU-695 — `PantryBeliefChip.vue` is orphaned; nothing imports it
- **Raised:** 2026-08-20 (DR-15 micro-motion pass).
- **Type:** finding.
- **What:** `components/stock/PantryBeliefChip.vue` has **no importer left** in
  `web_app/src` — only comments in `PantryBeliefCard.vue`, `StockItemRow.vue`
  and `StockItemDetailPage.vue` still refer to it. The row-level belief hint it
  rendered was folded into the level picker (ring + menu header) during the
  2026-08-15 Chunk-4 work, and the chip was left behind. Note it *did* receive a
  real fix afterwards (the DR-8 fade-in) — i.e. dead code that is still being
  maintained, which is the expensive kind.
- **Why deferred:** deciding between "delete it" and "it's the intended
  component for a surface that hasn't been rebuilt yet" is a product call, and
  the three comments referencing it need rewording either way — more than a
  ride-along on a motion pass.
- **Recommended resolution:** now (a delete + three comment edits, if the owner
  confirms the row-level chip isn't coming back).

## [OPEN] FU-694 — route-change transitions: the last critique §6 bullet, deliberately deferred
- **Raised:** 2026-08-20 (DR-15 micro-motion pass).
- **Type:** deferred job.
- **What:** the UX critique §6 asked for route changes to stop being instant
  swaps. DR-15 covered everything else in that section — the four
  high-frequency gestures (D-010), and DR-8 had already handled the belief-chip
  reflow and the dashboard loading→content swap via the shared skeletons — but
  page-level transitions are not built.
- **Why deferred:** the app has now been bitten **twice** by sequencing state
  behind paint (the DR-8 splash wedge; DR-15's own first-draft rAF class write),
  which is what R-050/ADR-046 were written for this session. A route transition
  is precisely where that failure goes fatal rather than silent — a wedged
  `<Transition>` leaves the user on a blank or half-left page. It also has to
  co-exist with scroll restoration and the per-page skeletons. That's its own
  unit with its own risk, not a ride-along on a 120ms-feedback pass. (The verify
  pane already demonstrates the failure: its route transitions wedge in
  `dora-fade-leave-active` and never complete.)
- **Recommended resolution:** opportunistic — and only with a non-paint timeout
  driving the unmount (R-050), never `transitionend` alone.

## [OPEN] FU-693 — the two compact-list row names sit off the D-003 type scale
- **Raised:** 2026-08-20 (cookbook feedback batch 3).
- **Type:** finding.
- **What:** `StockItemRow.vue`'s `.stock-row__name` is `font-size: 1.05rem` — a
  raw size, not one of the `--font-size-*` ratios D-003 requires (`md` = 1,
  `lg` = 1.125; 1.05 is neither). `RecipeRow.vue`'s `.recipe-row__name` now
  carries the same raw value, because the owner's ask this session was
  explicitly *parity with the stock row* and the only way to match a
  tokenless value is to repeat it. Carve-out is commented in place in
  `RecipeRow.vue` naming the rule.
- **Why deferred:** it has to be done as a **pair or not at all** — tokenising
  one breaks the parity the request created, and tokenising both moves the Stock
  Overview name type the owner signed off on days ago (24ca1786 / 8073ac04). So
  it's a small deliberate design call, not a mechanical sweep.
- **Fix shape:** decide whether a list-row name is `--font-size-md` (16, back
  down a step) or earns a new `--font-size-md-plus` ratio, then change both
  declarations in the same commit. Check any other `.…__name` in a list row for
  the same value while there.
- **2026-08-30 update — a third site was AVOIDED, not created.** The meal
  planner's new rail row (`MealPlanRecipeRow.vue`, Unit 2 of the rail brief)
  would have been the third `.…__name` at `1.05rem`; the brief's §4.5 asked for
  a decision either way and the recommendation was to tokenise. It uses
  `--font-size-md`, on the grounds that a 280px rail is not where a 0.05rem
  parity with a full-width stock row is legible. So the pair described above is
  unchanged and still has to move together — but the rail is already on the
  scale and must NOT be "brought back into line" with them if they stay raw.
- **Recommended resolution:** opportunistic — pairs with the next design-
  remediation chunk, or with [[FU-691]] since both are D-rule type/token drift.

## [OPEN] FU-692 — `ICONS.restaurant` means four different things
- **Raised:** 2026-08-20 (cookbook feedback batch 3 — icon crossover item).
- **Type:** finding.
- **What:** the owner's report was "inconsistent and crossover icons between
  filters and recipe cards", naming difficulty and cook-time/time-of-day. Those
  three are fixed. Auditing them turned up a fourth, wider one that was **not**
  in scope: `ICONS.restaurant` (fork-and-knife) currently stands for *a meal*
  (meal-plan chips/cards, the `no_planned_meals` alert, the dashboard,
  `UpcomingTimeline`, onboarding, Help), *the admin Cooking settings page*,
  *the About page*. Servings was a fifth meaning until this session moved it to
  `ICONS.people`. **The recipe-tools crossover resolved itself** on 2026-08-26:
  it lived in the old recipe page's chip row, which [[FU-688]] deleted; the
  surviving page doesn't glyph its Tools panel at all.
- **Why deferred:** it spans meal plans, dashboard, alerts, settings, help and
  onboarding — six surfaces the owner hasn't reviewed — and the fix is a
  glossary decision ("what is the one thing fork-and-knife means?") before it's
  an edit. Doing it as a side effect of a cookbook fix is how you get a diff
  nobody can review.
- **Fix shape:** pin `restaurant` = "a meal / an occasion of eating" (its
  dominant use), then repoint the outliers: tools → `blender`, the admin
  Cooking page and About row → something that isn't a plate.
- **Recommended resolution:** opportunistic, or as part of the next icon/design
  pass — worth doing before the icon set gets a sixth meaning.

## [OPEN] FU-691 — the recipe page's stylesheet is off-token throughout (D-017)
- **Raised:** 2026-08-20 (recipe-view parity pass).
- **Type:** finding.
- **What:** the page's ~350-line `<style scoped>` block predates any D-017 check
  on it. Two patterns, both throughout: **token fallbacks**
  (`var(--space-2, 8px)` — ~40 occurrences, so the literal is what a missing
  token would actually render) and **off-scale literals** for font-size
  (`0.8125rem`, `0.75rem`, `0.875rem` where `--font-size-xs/sm` exist), padding
  (`padding: 0 3px`) and shadow (`0 2px 10px var(--overlay-dim)` against
  `--elevation-*`). D-017 bans exactly these. The new CSS added in this pass
  matches the file's existing style deliberately rather than leaving two
  conventions in one stylesheet — flagged here instead, per the explain-or-flag
  rule, because a half-converted stylesheet is worse than either end state.
- **Why deferred:** it is a mechanical sweep of one file with no behaviour
  change. Its original blocker — the old page and the masthead question — cleared
  on 2026-08-26 when [[FU-688]] resolved, and the file is now
  `web_app/src/pages/RecipeDetailPage.vue`. The owner was offered it as part of
  that swap and **chose to defer**: the merged page still has no browser walk
  behind it, so a whole-stylesheet rewrite would tangle any spacing regression up
  with the swap and the icon work in one diff. The 2026-08-26 batch's new CSS
  (`.rn__brow`, the `.rn__factk` icon rules) again matches the file's existing
  style rather than leaving two conventions in one stylesheet.
- **Recommended resolution:** **after the `DORA_VERIFY` walk of the merged recipe
  page**, as a standalone tidy with nothing else in the diff.

## [OPEN] FU-686 — `PantryBeliefChip.vue` is orphaned and still described everywhere as the live row form
- **Raised:** 2026-08-20 (stock-signal consolidation, Chunk 4).
- **Type:** finding.
- **What:** `components/stock/PantryBeliefChip.vue` is imported by **nothing**. The
  row stopped using it on 2026-08-15 when the belief hint moved onto the level picker,
  and Chunk 4 removed the ring that replaced it. Its own header comment plus comments
  in `PantryBeliefCard.vue` and `StockItemDetailPage.vue` still describe it as the
  live *row* form of the belief chip, which will mislead the next reader into thinking
  the row still shows one.
  **Correction to this entry (2026-08-20, same day):** it originally also listed
  `BaseButton`'s `attention` prop as dead. That was true for about an hour — the
  owner then reinstated the Stocktake glow gated on essentials, so
  `StockOverview.vue` calls it again and the prop, `dora-btn--attention` and its
  keyframes are all **live**. Do not delete them. Recorded rather than quietly edited
  out, because "nothing glows any more" was the wrong conclusion, not just a stale
  fact — the design landed on *gate the condition*, not *remove the channel*.
- **Why deferred:** the chip is named by three planning docs, so deleting a component
  they reference deserves its own line rather than vanishing inside a UI chunk.
- **Recommended resolution:** opportunistic. Deleting it is a two-line job (the file
  plus the three stale comments); it carries no behaviour.

## [OPEN] FU-685 — the row's expiry "soon" band is still a client-side 7 days while the outline reads the server's window
- **Raised:** 2026-08-20 (stock-signal consolidation, Chunk 4).
- **Type:** finding.
- **What:** `helpers/expiryIndicator.ts` keeps its own `SOON_WINDOW_DAYS = 7` and
  colours the row's expiry button amber off it. Chunk 3 killed the *other* copy of
  that 7 (B1) by having the outline read the server's configurable window — so an
  install that sets the expiring-soon window to, say, 14 days now gets a row that is
  **outlined** for an item whose expiry button is still **green**. The file documents
  the literal as display-only and that reading is defensible, but the two are visibly
  on one row and B1 was exactly this shape.
- **Why deferred:** it needs a call, not a fix: either the window rides the DTO to
  the client (the honest one-rule answer, and `attention_kinds` already carries
  `expiring_soon`, so the button could just read that) or the button's colour is
  deliberately a fixed-scale "how close is the date" and the mismatch is intended.
- **Recommended resolution:** **now-ish** — one decision, and if the answer is
  "read `attention_kinds`" the fix is ~5 lines in `StockItemRow.vue`.

## [OPEN] FU-684 — ~20 more `item.stock_level` readers carry the same R-032 exposure the buy verdict just proved live
- **Raised:** 2026-08-19 (stock-signal consolidation, Chunk 1).
- **Type:** finding.
- **What:** `GET /api/stock-items/<id>/buy-verdict` included `STOCK_LEVEL` on its
  load and *still* read `item.stock_level is None`, so `_stock_level_band` returned
  `"unknown"`, the `need` axis collapsed to thin-data, and the endpoint answered
  **`unsure/low` for every item** — including an out-of-stock one, which is its
  most confident `buy`. That is R-032's identity-map corollary biting with the
  `.include()` present: the session already tracked the instance with the
  relationship unset, and `contains_eager` didn't repopulate it. Belief's
  `recorded_sequence` read the same relationship and had the same exposure (it
  would have silently fallen through to its no-data path). Both now resolve the
  level by FK through the new
  `dora_api/features/stock_items/_level_access.py::resolve_levels_by_item`.
  **Not swept:** every other reader of the relationship — `alerts/get_alerts.py:215`
  (the attention engine — a silent `None` there suppresses the out/low alerts
  Chunk 3 is about to consolidate onto), `domain/recipe_cookability.py:62,109`,
  `assistant/confirm_actions.py:87,159,661`, `assistant/shopping_actions.py:39`,
  `assistant/tools.py:1012,1146,1454,1514,1515`, `alerts/act_on_alert.py:78`.
  Each needs the same question asked: is the instance guaranteed fresh on this
  query, or could the session hand back a noload-empty one?
- **Why deferred:** scope. The chunk's job was the cadence/constant consolidation;
  the verdict bug was found because D-11 made belief read the same field. Sweeping
  a dozen unrelated features unasked is the drive-by the standards warn against.
- **Fix shape:** audit the list above; where the read isn't provably safe, resolve
  by FK (`item._stock_level_id`) via `resolve_levels_by_item` rather than adding
  more `.include()`s — an include is what failed here. `get_alerts.py` is the
  highest-value one and Chunk 3 opens that file anyway.
- **Recommended resolution:** the alerts reader **with Chunk 3** (same file, same
  rebuild); the rest opportunistically. If several turn out to be live bugs, R-032
  needs a stronger "don't trust `.include()` alone" clause.

## [OPEN] FU-683 — stock-surface signal consolidation: 7 live bugs + 5 duplications, plan written, Step 0 gates the main chunk
- **Raised:** 2026-08-19 (stock overview signal-crossover design session)
- **Type:** deferred job + findings
- **What:** the owner flagged that Stock Overview has too many competing signals
  (stocktake, Dora thinks, expiry, needs attention, essential, needs check, buy
  verdict, open/in-use). The investigation found nine visual channels on one row
  sharing a two-colour palette with **inverted meanings** (red level box = "buy
  this urgently", red cart ring eight pixels away = "don't buy this"), plus two
  independent attention engines and three independent cadence implementations.
  Full context, evidence register, and a 6-chunk plan:
  **`docs/04_proposals/IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md`**.
  **Live bugs found (all verifiable independently of the plan):**
  - **B1** `useStockFilters.ts:137` hardcodes a 7-day expiring-soon window while
    the server resolves a configurable one — admin changes it, row outlines and
    the "Needs attention" count don't move.
  - **B2** per-user `AlertPreference` is honoured by the bell and **ignored
    entirely** by the overview; disabling a kind silences the bell but not the rows.
  - **B3** `AlertsPage.vue:331` deep-links to `/stock?attention=true`, which
    filters by a *different rule* than the count that was tapped.
  - **B4** non-essential out-of-stock is a MEDIUM **actionable** alert server-side
    but the row is **dimmed** — same item is "act on this" and de-emphasised.
  - **B5** `StockItemRow.vue:390` fires **one HTTP request per rendered row** for
    the buy verdict (the module cache dedupes by id, it doesn't stop fan-out);
    200-item pantry = 200 requests to render a ring that's suppressed at low
    confidence. `useBuyVerdict.ts`'s own comment claims otherwise — it's wrong.
  - **B6** same per-line N+1 on the shopping list (`BuyVerdictBadgeInline`);
    survives B5's fix and becomes the primary surface after it.
  - **B7** `buy_verdict_enabled` is a household AppSetting despite being a pure
    per-user display overlay — **owner confirmed this is a mistake**.
  - **D1–D3 (R-003):** `14`-day and `90`-day windows each declared twice across
    `stocktake.py` / `cadence.py` (one carries a comment admitting the mirror);
    and **three** implementations of "mean gap between movements" —
    `pantry_belief._mean_gap_days`, `get_buy_verdict._cadence_detail` (identical
    inputs, identical math), `cadence.auto_band_from_history`.
  - **D4 (R-003):** `hasAlert` computes a cross-entity domain rule client-side.
- **Why deferred:** Chunk 3 (the one attention rule) is **gated on a Step-0
  assessment of the alerts system with the owner** — it was largely AI-built from
  loose ideas and has never been vetted (9 kinds, 2 tiers, per-user prefs, a page,
  a bell, `act_on_alert`, a digest email). Consolidating onto an unvetted
  foundation makes it harder to change later, not easier. Chunks 1 and 2 have no
  such dependency.
- **Fix shape:** the plan's §3. Chunks 1 (constant + cadence consolidation) and 2
  (verdict off the row + settings scope) can land immediately; 3–6 follow Step 0.
- **Progress (2026-08-19):** **Chunk 1 is done** — D1/D2 constants collapsed onto
  `cadence.py` (now public `AUTO_HISTORY_WINDOW_DAYS` / `LOW_OUT_BUMP_WINDOW_DAYS`);
  D3 resolved by a shared `domain/cadence_math.py::mean_gap_days` that all three
  cadence readers now call; **D-11 landed** — the verdict's `need` axis consumes
  `compute_belief`, hedges its wording when the band is an inference that disagrees
  with the recorded level, and steps its own confidence down for one; **B6** has its
  bulk endpoint (`GET /api/shopping-lists/<id>/buy-verdicts`); the misleading
  `useBuyVerdict.ts` cache comment (B5) is corrected. Landing D-11 also exposed a
  live bug that made the whole verdict feature inert — see **FU-684**.
  **Chunk 2 is done (2026-08-19):** D-10 — the verdict ring is off `StockItemRow`
  and `AddToListButton`'s `verdict` prop, branch, tooltip block and CSS are
  deleted (it had no other caller); B5 — the overview fires **zero** verdict
  requests, measured in a browser drive, not inferred; D-12/B7 —
  `buy_verdict_enabled` moved AppSetting → User (migration `d9f4b2c7e803`,
  clean drop-and-add, no backfill shim), the toggle moved Admin→Features to
  Settings→Assistant, the `features.buy_verdict` health flag is gone and
  `useBuyVerdictEnabled` now reads `/auth/me`; B6 — `ShoppingListDetail`
  primes the whole list's verdicts through the Chunk-1 endpoint in **one**
  request (also measured).
  **Step 0 is DONE (2026-08-20)** — the owner answered all five questions; the
  canonical attention rule is written into the plan's §3. Cuts: `out_of_stock`,
  `low_stock`, `stocktake_overdue` (Q1, wider than the plan proposed); per-user
  `tier_override` (Q2/Q3, on/off survives); the digest email (Q4). Q5 is
  superseded — with the kind cut there is nothing to demote, though **D-8's row
  half still governs Chunk 4**.
  **Chunk 3 is done (2026-08-20)**, split 3a/3b on size. 3a: the cuts above, plus
  `acknowledge_stocktake` (the retired kind's only action, now a pinned 422) and
  migration `e4b1c7a95d20`. 3b: **B1–B4 all closed** by a single server-owned rule
  in `features/stock_items/stock_attention.py` — `get_alerts.py` emits its three
  per-item kinds from the same predicates, the stock DTO carries
  `needs_attention` / `attention_severity` / `attention_kinds`, client `hasAlert`
  is a read, the hardcoded 7-day window is deleted (B1), disabled kinds now reach
  the rows (B2), the deep-link and the count run one rule (B3), and non-essential
  out is no longer "actionable and dimmed" (B4). D-7's single outline landed with
  it. 15 new unit tests on the rule.
  **Still open:** Chunks 4–6 (row treatments + sort, queue ranking, runner
  rebuild). Browser-verify of Chunk 3 is owed — see `DORA_VERIFY.md`.
- **Recommended resolution:** **Chunk 4 next** — it is unblocked and its input
  (`attention_severity`) is already on the DTO.

## [OPEN] FU-682 — three more `window.open(apiUrl)` print views still violate R-045
- **Raised:** 2026-08-19 (recipe view feedback batch)
- **Type:** finding
- **What:** the recipe Print button was reported as "404s" and turned out to be a
  straight R-045 violation — `window.open` on a URL built from `resolveBaseURL()`,
  which is authenticated only if the browser volunteers the session cookie. Fixed
  by routing it through the new shared `services/files/printView.openHtmlDocumentAsync`
  (fetch through `AxiosHttpClient`, tab claimed on the gesture per R-046).
  **Three siblings were left untouched and have the identical defect:**
  `useShoppingListExport.ts:22`, `useMealPlanExport.ts:13`,
  `useStockOverviewExport.ts:51`. All three will fail the same way on a split
  `app.`/`api.` host and in the Capacitor shell, and will look like a 404 to the user.
- **Why deferred:** the reported surface was the recipe page; the other three are
  different pages the owner hasn't reviewed this round, and each needs its own
  error copy + a walk. The mechanic they need already exists, so each is a ~10-line
  change.
- **Fix shape:** replace each `window.open(...)` with `openHtmlDocumentAsync(path, title)`
  (keep the call a sync entry point — no `await` before it), and give each a toast
  with `toastCaption(err)` + the `PopupBlockedError` branch, as
  `useRecipeExport.openPrintView` now does. `useQrLabels` is already migrated.
- **Recommended resolution:** now-ish — it's a known-broken class with a proven fix
  sitting next to it. Otherwise opportunistically, whenever each page is next open.

## [OPEN] FU-680 — the ingredient-unit reconciliation has no density bridge
- **Raised:** 2026-08-19 (recipe view feedback batch)
- **Type:** follow-up
- **What:** recipe costing now converts an ingredient's quantity into the unit its
  price is per, and leaves the ingredient **unpriced** when the two can't bridge.
  `units.convert` *can* cross mass↔volume when given an ingredient name that's in
  `INGREDIENT_DENSITY_G_PER_ML`, but `recipe_cost._line_cost` doesn't pass one — so
  "200 ml of milk" against a price per kg reads as unpriceable even though the
  density table knows the answer.
- **Why deferred:** the reported bug was a wildly *wrong* number; an honest gap is
  the correct floor and shipping it doesn't depend on this. Passing a name also needs
  a decision about which name (the stock item's, which is user-typed, vs the linked
  product's) and how loudly to flag a density-derived estimate.
- **Fix shape:** pass `ingredient=<stock item name lowercased>` into `units.convert`
  from `_line_cost`, and mark the resulting `CostLine` so the breakdown can show the
  estimate is density-derived.
- **Recommended resolution:** when the cost card next comes up, or if the owner
  reports "it says it can't price something it obviously can".

## [OPEN] FU-678 — every `.dora-btn` is 36px tall, under D-004's 44px touch floor
- **Raised:** 2026-08-19 (cookbook feedback batch 2)
- **Type:** finding
- **What:** `BaseButton`'s base rule is `min-height: 36px` for every variant, and
  the icon variants are 36×36. B1 says "min height **44px** on touch (36px
  desktop-dense chrome only)" and D-004 sets a 44×44 effective floor "on any
  surface a finger uses". Dora is a pantry/mobile app, so almost no button
  qualifies for the desktop-dense allowance. This came up because the filter row's
  controls **were** raised to 44px this session (in the new shared `FilterRow`,
  where it's one number), which makes the 36px buttons beside them the outlier.
- **Why deferred:** it resizes **every button in the app** — toolbars, dialogs,
  bulk bars, list-row actions — and several of those rows are width-constrained on
  a phone already. That's a design pass with a real-device walk, not a side effect
  of a filter-row fix. The new `subtle` variant deliberately matches its siblings
  at 36px rather than becoming a lone 44px exception (commented in place naming
  the rule).
- **Recommended resolution:** later, as its own unit — pairs naturally with the
  next mobile-UX pass, and with [[FU-675]] since both want a real phone.

## [OPEN] FU-677 — adopt the new `subtle` BaseButton variant at the remaining small-action sites
- **Raised:** 2026-08-19 (cookbook feedback batch 2)
- **Type:** deferred job
- **What:** the owner's report was specific but general in intent — "select all /
  select missing buttons don't have the appearance of buttons. **I've seen a few of
  these smaller UI elements pop up (e.g. in settings).** Might be good to
  componentise to get a consistent look." A `subtle` variant now exists on
  `BaseButton` (tinted fill + border + radius, quieter than `secondary`) and the
  ingredient picker uses it. The other sites — the `variant="ghost"` +
  `dense` + `size="sm"` combination, which renders as bare tinted text — were
  **not** swept, by agreement, because that's a diff across Settings and other
  surfaces the owner hasn't reviewed.
- **Fix shape:** inventory the `ghost` + `dense`/`size="sm"` call sites
  (`git grep -n 'variant="ghost"' web_app/src | xargs`-style, then filter to ones
  that also pass `dense` or `size`), decide per site whether it's a genuine
  tertiary text action (leave as ghost) or a small *control* (flip to `subtle`),
  and flip the latter. Settings is the surface the owner named.
- **Recommended resolution:** opportunistic, or as the first half of the next
  Settings polish unit.


## [OPEN] FU-675 — migrate the remaining ~64 `q-select`s onto `BaseSelect`
- **Raised:** 2026-08-19; **substantially delivered 2026-08-19 (later 3)** —
  reduced to a migration backlog.
- **Type:** deferred job
- **Decided and built:** `components/BaseSelect.vue` owns the menu-vs-dialog
  rule (≤8 options and no typeahead → `menu`; longer or `use-input` →
  `default`, i.e. dialog on mobile) plus a close affordance in the dialog case.
  Pinned by `test/unit/baseSelect.spec.ts` (9 tests). **8 call sites migrated**:
  the five cookbook filter selects, the three StockOverview ones, and
  `SortControl` (which the cookbook and stock rows both use).
- **What remains:** ~64 `q-select`s elsewhere — settings pages, dialogs
  (`CreateStockItemDialog`, `PutAwayDialog`, `BulkMoveLocationDialog`,
  `SubstituteMetadataDialog`), `ShoppingListDetail`, `MyProductsPage`,
  `ReportsPage`, `RecipeDetailPage`, onboarding. Until they move, they keep
  Quasar's unconfigured default, so the owner's original inconsistency persists
  on those surfaces.
- **Migration gotcha — read before doing the rest.** `BaseSelect` declares
  `useInput` (the rule reads it), which means **Vue consumes it and drops it
  from `$attrs`**; it is forwarded explicitly. Any *other* q-select prop that
  BaseSelect ever declares must be forwarded the same way. This bit once
  already: the stock location picker's typeahead silently stopped working while
  the control still looked correct — caught live, now covered by a test.
  `BaseSelect` also applies `dense`+`outlined` itself, so drop that pair at each
  call site rather than passing it twice.
- **Recommended resolution:** opportunistic, a surface at a time, each with a
  glance at the page afterwards — a mechanical all-at-once sweep across 64 sites
  is exactly where a dropped slot or prop would hide.

## [OPEN] FU-674 — `--text-on-primary` fails the D-002 contrast floor in three themes
- **Raised:** 2026-08-19 (cookbook feedback batch — segmented-control fix)
- **Type:** finding
- **What:** fixing the unreadable sort toggle moved every segmented control's
  active label onto `--text-on-primary`. **Measured live** against each theme's
  `--brand-primary`: pesto-dark **5.18:1** ✅, lemon-tart **9.47:1** ✅, but
  **pesto 3.88:1**, **blueberry 4.21:1**, **midnight 2.86:1** — all below
  D-002's 4.5 floor. Those three define the token as pure white over a
  mid-brightness primary. The reported bug (pesto-dark, measured at **1.0:1** —
  literally invisible) is fixed; this is a pre-existing token-level problem the
  measurement exposed, and it affects **anything** painting `--text-on-primary`
  over `--brand-primary`, not just segmented controls.
- **Why deferred:** the fix is either darkening those themes' ink (changes every
  primary button's look in three themes) or darkening their `--brand-primary`
  (changes the brand colour) — a design call the owner should make, not a
  side-effect of a filter-toggle fix. Same family as [[FU-671]].
- **Recommended resolution:** now-ish — it's a one-decision fix once the owner
  picks which lever; worth doing before the next design-remediation chunk.

## [OPEN] FU-673 — three test files carry pre-existing lint errors
- **Raised:** 2026-08-19 (cookbook feedback batch)
- **Type:** finding
- **What:** `npx eslint src test` reports 11 errors, all in
  `test/unit/offlineQueue.spec.ts`, `test/unit/useBuyVerdict.spec.ts`,
  `test/unit/useOfflineQueue.spec.ts` — `@typescript-eslint/require-await` and
  `consistent-type-imports`. None are in `src/`; none were touched by this
  batch. They mean a plain `eslint src test` is not currently green, so a real
  regression in a test file would be lost in the noise.
- **Why deferred:** unrelated to the work in flight; mechanical but wants its
  own commit so the diff is reviewable as "lint only".
- **Recommended resolution:** opportunistic.

## [OPEN] FU-672 — settings page-header icon is declared twice per page (nav + page)
- **Raised:** 2026-08-18 (settings heading-icon sweep)
- **Type:** finding
- **What:** every settings page's heading icon is now set on the page itself
  (`SettingsPageHeader :icon` / `TaxonomyManagerPage :icon`) while the *same*
  icon is declared independently in `SettingsShell.vue`'s nav definitions. They
  agree today (verified live across all 31 pages) but only by hand — an
  R-003-shaped duplication, the same "one source for the IA" argument that made
  both navs read one `navGroups`.
- **Why deferred:** the structural fix is a shared route→icon map both the nav
  and the pages read, which touches all 31 page components; out of scope for a
  polish pass that was asked to add the missing icons.
- **Recommended resolution:** opportunistic — fold into the next settings-IA
  change that touches `SettingsShell.vue` nav definitions anyway.

## [OPEN] FU-671 — `text-color="white"` on semantic chips fails the D-002 contrast floor
- **Raised:** 2026-08-17 (expiring-ingredient chips).
- **Type:** finding (D-002 / R-035).
- **What:** measured against the actual theme tokens, white text on the **warning** chip
  is **1.7–3.0:1** and on the **negative** chip **2.96–3.9:1**. D-002's floor for text
  this size is **4.5:1**. `text-color="dark"` clears it everywhere (warning 5.5–9.5,
  negative 4.3–5.6). **17 call sites** app-wide (`color="warning"` + white ×9,
  `color="negative"` + white ×8) — including the "Uses N expiring" badge on the cookbook
  card and compact row, and the **Missing** chip sitting directly beside the new at-risk
  chips on the recipe page.
- **Why deferred:** the owner asked for an ingredient chip; flipping 17 chips across
  eight surfaces is a design sweep that wants one decision and one screenshot pass.
  The new chips were built correct (`dark`), so until the sweep lands the recipe
  ingredient row shows a white-ink Missing chip next to dark-ink at-risk chips.
- **Recommended resolution:** now-ish — it's mechanical, and the mixed treatment on the
  recipe page is visible. Worth deciding at the same time whether B2's prescribed
  "`-soft` background + semantic ink" replaces solid semantic chips generally.

## [OPEN] FU-670 — At-risk ingredient chips are read-view only (not cook mode / edit rows)
- **Raised:** 2026-08-17 (expiring-ingredient chips).
- **Type:** follow-up.
- **What:** `RecipeIngredientDto.is_expiring` / `is_expired` now ship on both the list
  and detail endpoints, but only the recipe **read view** renders a chip. The two other
  places the same ingredients appear don't: **cook mode** (arguably where it matters
  most — you're standing at the bench deciding what to use) and the **edit-mode
  ingredient rows** (which already show Missing + stock-level chips, so the slot exists).
  The data is already on the wire; each is a template addition reading `expiringChip`.
- **Why deferred:** the owner asked for the recipe page specifically; adding two more
  surfaces uninvited is the anti-creep principle's exact target.
- **Recommended resolution:** now, if the owner wants it — it's small and the server
  half is done. Otherwise opportunistic, next time either surface is open.

## [OPEN] FU-669 — The cookbook's at-risk horizon still lives in two languages
- **Raised:** 2026-08-17 (expiring-ingredient chips).
- **Type:** finding (R-003).
- **What:** `EXPIRING_HORIZON_DAYS = 14` is now the server's constant and the
  per-ingredient chips read it. The **filter** still takes the horizon as a request
  param, and `RecipesOverview.vue` passes its own `EXPIRING_FILTER_HORIZON_DAYS = 14`
  — so the number is declared twice and they agree only by hand. Change one and the
  filter silently stops matching the chips, which is the exact confusion this work was
  reported to fix. Documented in place as an R-003 carve-out at both sites.
- **Why deferred:** unifying it means an explicit API change (a `uses_expiring=true`
  param the server resolves the horizon for, replacing the client-supplied number).
  That's a deliberate contract decision, not a bug fix, and a blank-value-means-default
  shortcut was rejected as magic.
- **Recommended resolution:** when the recipes filter API is next touched — or now, if
  you'd rather not carry the hand-sync risk. Needs a call on whether
  `expiring_within_days` stays for other callers.

## [OPEN] FU-668 — Audit every list store for the unpaged-first-page trap
- **Raised:** 2026-08-17 (cookbook truncation bug).
- **Type:** finding.
- **What:** the cookbook bug (recipes past the 50th invisible because the store took
  one default page and filtered client-side) is the *second* instance of this exact
  defect — stock items had it as FU-035. The shape is: a store hydrates via a bare
  `getAllAsync()`, and a page filters/searches over that collection in the browser.
  Any such surface silently caps at `DEFAULT_LIMIT` (50) and misreports its own
  counts. Recipes and stock items now page; **meal plans, shopping lists, shopping-list
  templates, locations, stock groups and stores have not been checked.** Grep for
  `getAllAsync()` with no args in `web_app/src/stores/`.
- **Why deferred:** out of scope for the reported bug; fixing recipes was the ask.
- **Recommended resolution:** now-ish — it's a read of ~8 stores, and each hit is a
  user-visible "my data vanished" bug waiting for the install to grow past 50 rows.

## [OPEN] FU-667 — Client-side filtering over a fully-hydrated collection is the real
  design smell behind FU-668
- **Raised:** 2026-08-17 (cookbook truncation bug).
- **Type:** finding.
- **What:** paging-until-exhausted fixes the correctness bug but keeps the underlying
  posture: the cookbook downloads every recipe (with ingredients, stock levels and
  locations eager-loaded) to filter and search 20-odd axes in the browser. That's a
  growing payload and it sits awkwardly against R-003 — the server already owns
  `cookable` / `max_missing` / `expiring_within_days` as query params, and the client
  re-implements the rest. Not urgent at personal-cookbook scale (68 recipes today);
  worth a decision before it's 500.
- **Why deferred:** moving 20 filter axes server-side is a design job, not a bug fix,
  and the charter's anti-creep principle says fix the reported defect first.
- **Recommended resolution:** later — when a cookbook/pantry gets big enough to feel
  it, or opportunistically alongside any other recipes-list work.

## [OPEN] FU-664 — Handler call sites can drift from entity signatures silently
- **Raised:** 2026-08-17 (first-setup onboarding bug).
- **Type:** finding.
- **What:** `SeedDemoHandler` was still passing `image=None` to `StockItem` long after
  the entity dropped the field. Nothing caught it because the only path that constructs
  those rows is gated behind an idempotency check that's already satisfied on every
  seeded/dev/e2e database — so a genuine first install was the *only* way to hit it.
  Worth a sweep for other "only runs once, on a truly empty DB" branches (the rest of
  the onboarding seeders, `seed_showcase`, the demo-reset path) that no test reaches.
- **Why deferred:** out of scope for a bug fix; the reported defect itself is fixed and
  now covered by `tests/e2e/dora_api/test_onboarding_seed_demo.py`.
- **Recommended resolution:** opportunistic — or now, if a fresh-install smoke test is
  wanted before the next release.

## [OPEN] FU-663 — The chat header's Basic/AI slider is a 24px tap target (D-004)
- **Raised:** 2026-08-17 (assistant chat-window feedback pass).
- **Type:** finding.
- **What:** `DoraModeSlider.vue` is `height: 24px; min-width: 96px`. D-004 floors touch
  targets at 44×44px. This was tolerable while the slider was mouse-territory chrome,
  but this session made it **deliberately tappable on touch** — when AI isn't configured
  it now routes to Settings → Assistant rather than sitting inert behind a hover-only
  tooltip. So it is now a primary touch affordance at roughly half the required height.
- **Why deferred:** growing it changes the chat header's whole vertical rhythm (the
  header row also holds three icon buttons and the D.O.R.A. wordmark), which is a design
  call, not a CSS tweak. Same family as **FU-641** (header icon buttons at 36px) — the
  two should be resolved together as one header-density pass rather than piecemeal.
- **Recommended resolution:** later, folded into FU-641. Cheapest compliant shape is
  probably an invisible `::after` hit-area expanding the slider to 44px vertically
  without moving the pill itself.

## [OPEN] FU-660 — Failed offline syncs have nowhere to go — no conflict UI
- **Raised:** 2026-08-17 (offline-sync audit).
- **Type:** finding / deferred job.
- **What:** `useOfflineQueue` maintains a `conflicts` pile for queued mutations the
  server rejects on replay for a non-network reason (422, 409, a since-deleted item).
  It's exposed — `conflicts`, `conflictCount`, `discardConflict`, `retryConflict` — and
  **nothing in the app consumes any of it**. The user gets one 5-second toast and the
  change is then unreachable: no list, no retry, no way to see what was dropped. This
  session made the pile survive a reload (it was memory-only, so a refresh erased the
  record entirely), which turns silent loss into recoverable loss — but only for
  someone reading localStorage.
- **Why deferred:** the transport bugs were the blocker (nothing could sync at all —
  see the same-day CSRF fix), and surfacing conflicts needs a real design call: where
  does it live (a banner? Settings? a dedicated "unsynced changes" page?), and what are
  the resolve verbs beyond retry/discard.
- **Recommended resolution:** later, once the fixed sync path has been exercised in
  anger — the shape of the UI should follow what conflicts actually turn out to be.
  Pairs with FU-661.

## [OPEN] FU-661 — Offline coverage is six mutation kinds; is that the right set?
- **Raised:** 2026-08-17 (offline-sync audit).
- **Type:** design question.
- **What:** exactly six things queue offline — `stock_level_update`, `mark_open`,
  `mark_restocked`, `push_expiry`, `clear_expiry`, `shopping_list_line_tick` — from three
  call sites (`stockItemStore` ×2, `ShoppingListDetail`). Everything else fails loudly by
  design (`useOfflineQueue`'s header: creates, deletes and anything identity-changing are
  excluded because a phantom item appearing an hour later is worse than an error now).
  That's a defensible line, but it was drawn at F3 and never revisited against how the
  app is actually used mid-shop. Candidates worth a look: adding an item to a shopping
  list (a create, but an idempotent-ish one), the stocktake runner's check/snooze (a
  walk-the-pantry flow, i.e. exactly the "in a cupboard with no signal" case), and
  cook-mode's finish step.
- **Why deferred:** each addition needs its own replay-safety argument, and two of the
  three are creates — the category the current design deliberately excludes.
- **Recommended resolution:** opportunistic, or when the real-device field test (FU-389)
  says which of these actually bites.

## [OPEN] FU-662 — `attempts` is counted on queued mutations but never acted on
- **Raised:** 2026-08-17 (offline-sync audit).
- **Type:** finding.
- **What:** `QueuedMutation.attempts` is incremented on every failed replay and read
  nowhere. There's no cap, so a mutation that keeps failing retries forever, and no
  staleness check, so a level set three days ago can replay over a newer value with
  last-write-wins and no warning — `createdAt` is recorded but unused. Neither has bitten
  yet (the queue could never drain at all until today's fix), which is precisely why it's
  worth deciding now rather than after it does.
- **Why deferred:** picking a cap and a staleness window is a product call, not a
  mechanical fix — "drop it", "conflict it", and "replay it anyway" are all defensible.
- **Recommended resolution:** with FU-660 — the answer to "too old / too many tries"
  is "it goes in the conflict pile", so the two want designing together.

## [OPEN] FU-656 — The password-strength rule is asserted in two languages
- **Raised:** 2026-08-17 (admin-settings rework).
- **Type:** finding.
- **Why it matters (R-003):** `auth_helpers.validate_password` is the authority — length
  **plus** a common-password blocklist — and it's the only thing that can reject a save.
  But three forms need to say "at least 8 characters" *before* the round-trip, so the
  number is now also a frontend constant (`web_app/src/models/password.ts`
  `MIN_PASSWORD_LENGTH`). That's one copy on each side of the wire; raising the server
  rule would silently leave the forms hinting the old number, and the blocklist half is
  invisible to the client entirely (you only learn "that's a common password" after
  submitting).
- **What:** publish the policy from the server — `min_length` (and ideally a
  `rules` blurb, `PASSWORD_RULES_DOC` already exists) on `GET /auth/capabilities`,
  which is already unauthenticated and already read on the login screen — then delete
  the literal and have `password.ts` read the published value with the current number
  as a boot fallback.
- **Why deferred:** the duplication is a hint string, not a security boundary — the
  server still rejects anything weak — and doing it properly means a small policy store
  + fallback on the client, which is more than the admin-settings unit should carry.
- **Recommended resolution:** opportunistic — natural pairing with any future auth or
  capabilities work.

## [OPEN] FU-655 — Deactivation only bites on `/auth/me` and the admin gate, not on every authenticated route
- **Raised:** 2026-08-17 (admin-settings rework).
- **Type:** finding.
- **What:** switching a user off is enforced in exactly three places — `login` refuses to
  mint a session, `get_me` clears an existing cookie on the next probe, and
  `auth/admin_gate.require_admin` re-checks before any admin action. A deactivated user
  holding a live cookie who never hits `/auth/me` could still call ordinary
  (non-admin) API routes until the SPA's next `/me`. In practice the SPA probes `/me`
  on boot and on refocus, so the window is short and the surfaces reachable in it are
  household-shared data the person already had — but "short" isn't "closed".
- **Why deferred:** there is no shared authenticated-route resolver to hang the check
  on — that's exactly the ~13-way hand-rolled `session['user_id']` → `User` dance in
  **FU-654**. Adding a 14th copy of the check to each feature is the wrong fix; the
  right one is a single `current_user()` that refuses inactive users, which lands with
  FU-654's sweep.
- **Recommended resolution:** with FU-654 — the check is two lines once the resolver
  exists.

## [OPEN] FU-654 — `session['user_id']` → `User` is hand-rolled in ~13 features (R-001)
- **Raised:** 2026-08-17 (FU-653 build).
- **Type:** finding.
- **What:** the same 8-line dance — read `session["user_id"]`, `UUID()` it inside a
  try/except, `repo.get(User).by_id(...)` — is copy-pasted across `features/alerts/*`
  (5 files), `features/assistant/*` (2), `features/budget/budget.py`,
  `features/dashboard/get_dora_score.py`, `features/stock_items/get_pantry_beliefs.py`
  and now `features/stock_items/inference_overlay.current_user` (which at least gives the
  three new surfaces one copy between them, with a comment pointing here).
- **Why deferred:** mechanical and wide; folding it into one
  `infrastructure/auth_helpers.current_user(repo)` touches a dozen files and belongs in a
  tidy-up pass, not in the middle of a feature.
- **Recommended resolution:** opportunistic — next time something is being changed across
  those features anyway (a natural pairing with the FU-512 unit-of-work sweep).

## [OPEN] FU-650 — Two `stockLevelDot` unit tests fail on `main`-as-of-this-branch
- **Raised:** 2026-08-16 (stock-overview filter feedback).
- **Type:** finding.
- **What:** `web_app/test/unit/stockLevelDot.spec.ts` has 2 failing assertions — it
  expects `bg-negative` for the out-of-stock sequence and `dora-bg-neutral` for
  out-of-stock *and* unknown; the component now renders `bg-negative` for out-of-stock
  and reserves `dora-bg-neutral` for unknown only. Confirmed pre-existing: the same two
  fail with this session's changes stashed. Everything else is green (434 passing).
- **Why deferred:** out of scope — it's the D-001 escalation (Out = red) landing in the
  component without the test following, not a regression from this unit.
- **Recommended resolution:** opportunistic — decide which is right (the test looks
  stale against D-001) and fix the losing side.

## [OPEN] FU-652 — Sweep the remaining `secondary` colour uses against D-020
- **Raised:** 2026-08-16 (stock-overview dark-mode colour fix).
- **Type:** follow-up.
- **What:** D-020 (new) says an indicator painted in `secondary` must read
  `--brand-secondary-strong`, not the surface-grade token. This unit converted the three
  Stock-Overview marks (row stripe, filter chips, footer count). Not swept: the
  `color="secondary"` icons in `RecipeDetailPage.vue:643`, `RecipeCookMode.vue:314`,
  `AdminSystemRegionSettings.vue:40,104`, and `DoraChat.vue:617`'s
  `background: var(--q-secondary)` scrollbar thumb. Each needs a look at whether it's a
  mark-on-page (convert) or genuinely surface-ish (leave).
- **Why deferred:** scope — the owner reported two specific surfaces; converting the
  rest unasked is exactly the drive-by the standards warn against.
- **Recommended resolution:** opportunistic — next time one of those files is open.

## [OPEN] FU-648 — QR: "Print one" root-caused and fixed; the dialog failure still unexplained
- **Raised:** 2026-08-16 (stock-item detail feedback batch). **Re-reported 2026-08-17**
  by the owner after the first fix: "when I tap on it I get 'couldn't load…' and then
  print one gives me an error."
- **Type:** finding.
- **What (updated 2026-08-17 — this round stopped guessing and measured):**
  - **Server half: proven green.** New e2e pin `tests/e2e/dora_api/test_qr_labels.py`
    (7 tests) exercises both endpoints through the real stack: PNG renders with the
    right magic bytes, `size=512` (what the dialog asks for) is accepted, absurd sizes
    400, an unknown item 404s, the sheet renders in caller order, skips unknown ids,
    prints-all with no ids, and — the load-bearing one — contains
    `data:image/png;base64,` and **no** `/api/stock-items` back-reference.
  - **Transport half: proven green.** Driven live from the Browser pane at `:5174`
    against the API at `:5170` — i.e. genuinely cross-origin with `credentials:
    'include'` — both endpoints answered 200, and `fetchQrImageUrlAsync` from the real
    composable returned a blob URL. So neither CORS, the cookie, nor the base URL is
    broken on this shape of deployment.
  - **"Print one": root-caused and fixed.** ADR-041's fix moved `window.open` to
    *after* the `await`, which every browser treats as an unsolicited pop-up and blocks
    — unconditionally on mobile, which is where the owner tapped. Now opened inside the
    click and navigated when the fetch lands (**R-046 / ADR-042**), with a blocked
    pop-up reported as its own message.
  - **"Couldn't load…": still not reproduced**, on the third attempt. It is now
    *instrumented* rather than guessed at: the dialog reports the HTTP status and the
    correlation-id prefix instead of a flat sentence, and network errors are worded
    differently from server errors.
- **Why it matters:** the remaining unknown is specific to the owner's install, and the
  previous two rounds failed precisely because the error message carried no evidence.
- **Recommended resolution:** confirm in browser on the owner's actual install. If the
  dialog still fails, **the message now names the cause** — quote it verbatim (status +
  `Ref:` prefix) and this closes in one pass. If it works, close. See DORA_VERIFY → Stock.
- **Round 4 (2026-08-21) — re-reported as "still getting 'Couldn't load this item's QR
  code (error 404)'". Two findings, both fixed; the cause is now named on screen:**
  - **The instrumentation was blind.** `getBlob` sets `responseType: 'blob'`, which
    applies to the *error* body too — so the server's problem-detail JSON arrived as a
    Blob, `isCustomApiErrorResponse` rejected it, and `details`/`title` were always
    empty. That is why three rounds of "the message will tell us next time" told us
    nothing. `AxiosHttpClient.getBlob` now reads the Blob back into JSON before
    normalising (all blob endpoints benefit).
  - **A 404 has two meanings and the copy conflated them.** `describeQrFailure` now
    splits them on the server's `title`: *route* miss ("This server has no QR endpoint
    at … — its API is older than this page. Restart or update the Dora server") vs
    *entity* miss ("That stock item no longer exists"). Server re-proven green over
    real HTTP the same day (200 + `image/png` at `size=512`).
  - **Now paired with FU-710** (the barcode POST in the same module 404s too on the
    same install) — one shared explanation is far more likely than two: the running API
    doesn't carry `features/data/barcodes`. Next step is the FU-710 lookup-URL check.

## [OPEN] FU-647 — `print-view` and the CSV export still build API URLs by hand (R-045)
- **Raised:** 2026-08-16 (QR fix — noticed in the same composable).
- **Type:** finding.
- **What:** `useStockOverviewExport.openPrintView` still does
  `window.open(`${baseUrl}/stock-items/print-view…`)`, which is the exact pattern
  R-045 now forbids and the exact pattern that broke the QR sheet. `downloadCsv` uses
  `fetch(..., { credentials: 'include' })`, which is *correct* but is a second
  hand-rolled auth path next to `AxiosHttpClient`. Other server-rendered print views
  (shopping list, recipe) likely have the same shape — not surveyed.
- **Why deferred:** out of scope for a stock-item-detail feedback batch, and the QR
  path was the one actually reported broken. Converting print-view needs the same
  server-side treatment (any `/api/...` asset it references must be inlined), so it's
  its own small unit.
- **Recommended resolution:** opportunistic — grep for `resolveBaseURL` /
  `getBackendBaseUrl` in templates and `window.open` calls, convert the document
  endpoints to the `useQrLabels` shape, and route `downloadCsv` through the client.

## [OPEN] FU-646 — The recipe nutrition rollup still aggregates only the original four nutrients
- **Raised:** 2026-08-16 (nutrition macros+ build).
- **Type:** deferred job.
- **What:** `NutritionFood` now stores sugars, saturated fat, fibre and sodium, and the
  stock-item detail page displays them. `features/nutrition/recipe_rollup.py` still sums
  only kcal/protein/carbs/fat, so a recipe's nutrition card can't show the new four.
- **Why deferred:** the feedback was about the stock-item detail page. The rollup has
  its own coverage/uncounted contract (R-041) that every added nutrient has to satisfy,
  and it feeds the meal planner's per-day figures — a bigger blast radius than this
  unit was scoped for.
- **Recommended resolution:** when the recipe nutrition card is next touched. Note the
  data caveat: existing catalogue rows have NULL for all four until the dataset is
  re-imported, so the rollup would report them as uncounted for a while.
- **Widened 2026-08-17:** the gap is now four nutrients plus fifteen — the
  vitamins-and-minerals block (migration `b6e04c9a2f18`) is likewise stock-item-detail
  only. This does **not** mean the rollup should grow all nineteen: a per-recipe
  potassium total is a different (and much more caveated) claim than a per-100g
  catalogue figure. Decide the scope deliberately when the card is next opened.

## [OPEN] FU-657 — The new micronutrients' Open Food Facts scale factors are unverified against a real response
- **Raised:** 2026-08-17 (nutrition micronutrients build).
- **Type:** finding.
- **What:** the fifteen new nutrients carry OFF `off_scale` values derived from OFF's
  documented convention that every non-energy `*_100g` nutriment is normalised to
  **grams** — so minerals are ×1000 (g→mg) and the µg-declared vitamins are ×1,000,000.
  That's the same reasoning the existing (and correct) sodium ×1000 rests on, and the
  USDA side of all fifteen is exercised by the importer's own `(name, unit)` matching.
  But **no test and no live OFF response** covers the new keys, so a mis-scaled vitamin
  would read as a 1000× error on a number people watch — the exact hazard the sodium
  comment in `nutrients.py` warns about.
- **Why deferred:** verifying it properly means hitting the live OFF API (the suite
  deliberately keeps network sources off, and the local catalogue is USDA), so it's a
  live-lookup check rather than a unit test.
- **Recommended resolution:** opportunistic — next time OFF lookup is switched on, scan
  a packaged good with a rich panel and sanity-check calcium/vitamin C against the pack.
  A wrong order of magnitude is obvious at a glance.

## [OPEN] FU-645 — Existing nutrition catalogue rows have no sugars/saturates/fibre/sodium until re-import
- **Raised:** 2026-08-16 (nutrition macros+ build).
- **Type:** follow-up.
- **What:** migration `d3a7f2b91c60` adds four nullable columns with no backfill —
  correct, because the values were never downloaded and inventing them would be a lie
  (P12). Any install that imported a USDA dataset before today shows blanks in the new
  Details table until it re-runs the import under System → Nutrition. Nothing in the UI
  currently says so.
- **Why deferred:** needs a product call on how loud to be — a one-line hint on the
  admin Nutrition page ("re-import to pick up newly-tracked nutrients") is probably
  enough; a banner would be over-nagging for a display-only gap.
- **Recommended resolution:** now-ish, alongside any next visit to the admin Nutrition
  page. Cheap either way.
- **Widened 2026-08-17:** migration `b6e04c9a2f18` adds fifteen more on the same terms
  (the vitamins-and-minerals block), so a pre-today install now shows an *empty*
  optional section rather than a partial one — which reads as "this food has no
  vitamins" instead of "we haven't downloaded them". That makes the one-line hint on
  the admin Nutrition page more worth doing, not less.

## [OPEN] FU-644 — Preferred buys are hidden when Products is on, with no migration path for existing rows
- **Raised:** 2026-08-16 (stock-item detail feedback batch — owner decision).
- **Type:** finding.
- **What:** the owner ruled the two systems mutually exclusive and chose "Products
  wins". Implemented as a pure `v-if` — rows are kept, never deleted, and reappear if
  Products is switched off. But an install that has been curating preferred buys and
  then enables Products loses sight of that text with no notice and no way to carry it
  across into a real product link.
- **Why deferred:** the right answer isn't obvious (a one-time "you have N preferred
  buys hidden — review them?" nudge? a read-only list on the Products tab? nothing at
  all?) and it only bites installs that used both, which may be none.
- **Recommended resolution:** when the Products overlay's Phase-F tail is next picked
  up (alongside FU-214). Decide then; nothing is lost in the meantime.

## [OPEN] FU-643 — The nutrition matcher has no vocabulary layer: regional synonyms score zero
- **Raised:** 2026-08-15 (nutrition auto-suggest build).
- **Type:** finding.
- **What:** matching is set-overlap on de-pluralised words, so two names for the same
  food never meet. "Tinned tomatoes" vs USDA's "Tomatoes, canned" scores 0.40 and is
  rejected; the same goes for aubergine/eggplant, coriander/cilantro, mince/ground
  beef, prawns/shrimp, capsicum/bell pepper — the whole AU/UK-vs-US split, against a
  catalogue that is entirely US-vocabulary. The user isn't stranded (Search still
  finds it), but this is the largest single source of "no match" on an AU pantry,
  which is the app's primary audience.
- **Why deferred:** a synonym table is its own design call — where it lives (code
  constant vs seeded table vs per-install editable), whether it's regional or global,
  and how it interacts with `AppSetting.locale`. Out of scope for the build, and
  guessing at it would be worse than the honest gap.
- **Recommended resolution:** when the owner has walked the matching page against a
  real USDA import (see the `DORA_VERIFY.md` item) and can say how often it actually
  bites — that read should decide whether this is a 30-word constant or a real feature.

## [OPEN] FU-642 — `stockLevelDot.spec.ts` has 2 failing tests on the working tree
- **Raised:** 2026-08-15 (mobile-header task — hit while running the frontend suite).
- **Type:** finding.
- **What:** `web_app/test/unit/stockLevelDot.spec.ts` fails 2 of 3 cases: the
  out-of-stock / unknown avatar is expected to carry `dora-bg-neutral` but renders
  `bg-negative`. Suite is otherwise green (434 passing).
- **Why deferred:** Pre-existing — reproduced identically on a `git stash`ed tree,
  so it belongs to the in-flight stock-row work, not the header change. Out of scope
  to fix blind (the spec or the component is the stale one; that's a call for whoever
  owns the current `StockLevelDot` colour semantics, and D-001 governs it).
- **Recommended resolution:** now — it's a red suite, and whoever is mid-flight on
  the stock-row rework can settle it in a minute.

## [OPEN] FU-641 — Header icon buttons sit at 36px, under the D-004 44px touch floor
- **Raised:** 2026-08-15 (mobile-header task).
- **Type:** finding.
- **What:** `BaseButton`'s `icon` / `danger-icon` / `filled-icon` variants set
  `min-height: 36px; min-width: 36px` (`web_app/src/components/BaseButton.vue`), so
  the mobile toolbar's hamburger, alerts bell and account avatar are 36×36 effective —
  below the **D-004** 44×44 floor. `DonateButton` next to them is 44px, so the row is
  also inconsistent. Not introduced here: the mobile shrink deliberately touched only
  glyph/avatar font-size and left the hit boxes alone, so nothing regressed.
- **Why deferred:** `dora-btn--icon` is app-wide — raising it to 44px re-flows every
  toolbar, table row and card action in the app, which is its own unit with its own
  browser pass. Way outside a header tweak.
- **Also in scope (2026-08-17):** the Users page's new per-row `⋮` actions menu is the
  same `icon` variant, so on a phone it's a 36px target carrying that row's Edit /
  Change-password / Delete. Not a new fault — it inherits the app-wide floor and will be
  fixed by the same one-line change to `dora-btn--icon`. Called out so the sweep knows to
  re-check row-level (not just toolbar) icon buttons.
- **Recommended resolution:** later — fold into the next design-remediation pass, or
  whenever the FU-578 UX/UI review is triaged into fix units.

## [OPEN] FU-640 — A user-visible failure produced an empty log bundle: 4xx responses aren't logged
- **Raised:** 2026-08-15 (FU-639 investigation — the owner's log bundle contained nothing useful).
- **Type:** finding.
- **What:** The owner hit two hard failures (dataset download, food linking) and
  collected logs. The bundle held: `compose-logs.txt` = 7 lines of boot output,
  `app-logs/dapi.log` = **0 bytes**, health = ok. Cause: both failures were
  **400 responses**, and a `bad_request(...)` return isn't logged at all — while
  the container's default `DORA_LOG_LEVEL=ERROR` suppresses the INFO request
  line that would at least have shown the endpoint being hit. So the app failed
  loudly in the UI and left no trace on disk, and the diagnosis had to be done
  by reproducing locally instead.
- **Why deferred:** the fix is a policy call, not a bug fix — (a) log 4xx on
  mutating endpoints at WARNING with the reason, and/or (b) raise the container's
  default log level to WARNING. Both change operator-facing behaviour and touch
  R-030 territory, so they're the owner's call rather than something to slip in
  alongside a bug hunt.
- **Recommended resolution:** now-ish — this is the difference between a log
  bundle that answers the question and one that costs a session. Pairs naturally
  with FU-405 (ops/observability).

## [OPEN] FU-639 — Camera scanning needs HTTPS on the **web** build; pick the self-host TLS story
- **Raised:** 2026-08-15 (stock-overview feedback round)
- **Type:** deferred job
- **What:** `navigator.mediaDevices` only exists in a **secure context**, so on a
  self-hosted install reached at `http://192.168.x.x:PORT` in a *browser* the
  scan overlay can never open the camera. **Scope confirmed 2026-08-15 — this is
  web-only:** Capacitor sets `androidScheme: "https"`
  (`src-capacitor/capacitor.config.json`), so the Android app's WebView origin is
  `https://localhost` — a secure context — and `allowMixedContent: true` lets it
  keep talking to a plain-http backend. `android.permission.CAMERA` is already in
  the manifest. **So the Android app can scan against any instance**, and there is
  no desktop build to consider (`quasar.config.ts` carries an Electron block but
  there is no `src-electron/`, so it has never been built).
  Communication is done (2026-08-15): shared `helpers/cameraAvailability.ts`
  drives an explainer panel in the scan overlay, a live warning under the admin
  Scanning toggle, and a Help guide entry. **What's left is the capability
  itself** — options, none yet chosen: optional self-signed TLS in the container,
  a documented reverse proxy (Caddy gets a cert in one line), or leaning on
  Tailscale/`*.ts.net` which serves HTTPS for free. Same constraint gates push
  notifications and PWA install, so one decision covers all three.
- **Why deferred:** it's a deployment/distribution decision, not a code fix, and
  it wants the same answer as the Phase-4 self-host release story rather than a
  one-off patch. Out of scope for a UI feedback round.
- **Recommended resolution:** later during Phase 4 (open-source release
  readiness — bundle with FU-406's README/release work). Not urgent for the owner
  personally: the Android app already covers his phone-scanning case.

## [OPEN] FU-640 — iOS Capacitor shell has no `NSCameraUsageDescription`
- **Raised:** 2026-08-15 (while scoping FU-639)
- **Type:** finding
- **What:** `src-capacitor/ios/App/App/Info.plist` declares no camera usage
  string. iOS *hard-terminates* an app that touches the camera without one, so
  the scan overlay would kill the app rather than fail softly. Android's manifest
  has its `CAMERA` permission; iOS was never given the equivalent.
- **Why deferred:** the iOS target is unbuilt Capacitor scaffolding — P8-10
  shipped an **Android** APK only, and nothing has ever run this code on iOS. It
  is a latent trap, not a live bug.
- **Recommended resolution:** when an iOS build is first attempted — add the key
  before the first device run, not after the first crash.

## [OPEN] FU-638 — Cookbook renders "No recipes match the current filters" while its own footer counts 11 shown
- **Raised:** 2026-08-14 (FU-637 — spotted while verifying the kcal badge).
- **Type:** finding.
- **What:** On `#/cookbook` in the agent's browser pane, the grid renders the
  empty state (`filteredRecipes.length === 0`) while the sticky footer — reading
  **the same computed** — shows "11 Shown / 8 Cookable now / 1 Favourites".
  Zero `.recipe-group` and zero `.recipe-card` nodes in the DOM; **no console
  error** of any kind (console capture verified working — Vite/Quasar messages
  come through). `GET /api/recipes` returns all 11 rows correctly.
- **Why deferred / not attributed:** **not caused by the FU-637 changes** —
  reproduced with `nutrition_mode = off`, where the new filter path isn't
  reached at all, and observed earlier in the same session before
  `RecipesOverview.vue` was touched. Reproduced in a fresh tab (so not the
  known stale-tab-after-backend-restart trap) and after a hard reload. Could
  not be attributed further from a static read: two readers of one computed
  disagreeing, with nothing thrown, points at either a render-time wedge
  (`FadeTransition mode="out-in"` wraps the grid — the R-037/FU-609 blank-page
  signature) or something specific to the agent's embedded browser.
- **Recommended resolution:** **confirm in browser** — open the cookbook in a
  real browser (dev *and* a production build) and see whether recipe cards
  render. If they do, this is an agent-pane artifact and can be closed with a
  note; if they don't, it's a live cookbook regression and the transition
  wrapper is the first suspect.
- **2026-08-17 evidence (cookbook toolbar/compact-view work) — now strongly
  looks like the pane artifact.** Reproduced exactly on the **first** navigation
  to `#/cookbook` (empty state rendered, footer read "15 Shown / 9 Cookable"),
  then **navigating away and back rendered 2 groups / 15 cards with no empty
  state** — i.e. it only misses when the data arrives *during* the transition.
  That is the rAF-wedge signature: `requestAnimationFrame` never fires in the
  agent pane, so a Vue `<Transition>` (here `FadeTransition mode="out-in"`
  around the grid) can wedge mid-leave, leaving the pre-data branch on screen
  while the footer — outside the transition — updates normally. Same failure
  mode as the DR-8 boot-splash wedge. Still needs the real-browser check to
  close, but the transition wrapper is now the confirmed first suspect and the
  bug is unlikely to exist outside the pane.

## [OPEN] FU-636 — USDA Foundation dataset URL carries a release date and will eventually 404
- **Raised:** 2026-08-14 (nutrition complex-mode build).
- **Type:** finding.
- **What:** FDC bulk-download filenames embed the release date
  (`FoodData_Central_foundation_food_csv_2026-04-30.zip`). SR Legacy is frozen
  so its URL is stable forever, but Foundation ships a couple of times a year,
  so the built-in default will 404 after the next release.
- **Why deferred:** handled defensively rather than solved — the import endpoint
  accepts a `url` override, and a 404 is caught and rewritten to "that release
  has probably been superseded; paste the current CSV link". No schema column
  was added for it (R-007).
- **Recommended resolution:** opportunistic — if it bites, either expose the
  override in the admin UI (the API already supports it) or scrape the current
  link from the downloads page at import time.
- **Update 2026-08-15 (FU-639):** still open, but the *host* was wrong too and is
  now fixed (`www.usda.gov` 403s automated downloads; `fdc.nal.usda.gov` serves
  them). The 2026-04-30 Foundation release is currently live on the correct host,
  so this is still a future-dated risk rather than a present break, and the 404
  path now has an actionable message pointing at the downloads page.

## [OPEN] FU-633 — Stock locations has no "not stored anywhere" row (items with no location are invisible)
- **Raised:** 2026-08-14 (stock-locations settings redesign).
- **Type:** deferred job.
- **What:** Deleting a location unassigns its items ("the items themselves stay in your
  stock"), and items can be created without a location — but no surface counts or lists
  them, so they silently fall out of the location view entirely. The redesign's mockup
  had a "Not stored anywhere — N items → Review" row at the foot of the zone list; it
  was cut from the build for want of the data.
- **Why deferred:** needs a server-side count (R-003 — the client must not sum stock items
  to derive it). `GET /locations` returns a bare `List[LocationNodeDto]`, so adding
  `unassigned_item_count` means either an envelope (breaking the picker + StockOverview,
  which both consume the bare list) or a separate small endpoint. Out of scope for a
  layout redesign — R-007.
- **Recommended resolution:** opportunistic — next time the locations API is touched.
  Note `get_location_tree.py:62` already says "None = unassigned, surfaced separately in
  the UI", which was never true.

## [OPEN] FU-632 — DR-14 carve-outs: first-boot region derivation (#48) + theme-mechanism reconciliation (#7b)
- **Raised:** 2026-08-13 (design-remediation DR-14; carved from FU-578 #48/#7b).
- **Type:** follow-up (two distinct concerns split from the DR-14 date-format authority).
- **What:** DR-14 shipped the date-format authority (`useDateFormat`, reads the shared
  household locale via `useMoney`'s `locale_policy`) and migrated all 26 call sites, so
  dates now render in the household locale (en-AU default) not the browser's US format
  (#9 fixed). Two adjacent pieces from the DR-14 backlog remain:
  1. **First-boot region derivation (#48).** The health `locale_policy` comes back
     **null** on a fresh install — locale/timezone are never asked. Onboarding SETUP has
     no region step, while Admin → System → Timezone already has a "Use this device"
     one-click derivation that nothing invokes at first run. So money/date formats rely
     on the en-AU *default* until an admin finds that page. Wire a first-boot
     derivation (browser `Intl.DateTimeFormat().resolvedOptions()` → locale + tz) or a
     one-line SETUP step, persisted server-side, keeping the admin override. Backend
     endpoint already exists. **Also add a timezone to `locale_policy`** so datetime
     renders (currently browser-tz) become household-tz correct.
  2. **Theme-mechanism reconciliation (#7b).** `body--dark` (Quasar Dark plugin) and raw
     `prefers-color-scheme` CSS are two sources of theme truth that disagree until a full
     reload — boot dark + flip the OS to light with no reload and the header/row cards go
     light while the page bg/toolbar/footer stay dark (screenshot-confirmed). Pick one
     authority (drive everything off the Quasar dark state, or off the media query, not
     both). R-002/R-003-adjacent.
- **Why deferred:** DR-14's core (D-006 "one date/number authority" + the visible #9
  bug) is shipped and verified; these two are separable — #48 spans onboarding +
  backend, #7b is a theming-system fix — each its own focused unit. Same split pattern
  as DR-7 → FU-624, DR-9 → FU-631.
- **Recommended resolution:** #48 opportunistically or in a Phase-4 onboarding pass; #7b
  in a theming turn. Cross-ref: `DESIGN_REMEDIATION_PLAN.md` DR-14, D-006, [[FU-578]].

## [OPEN] FU-631 — DR-9 carve-outs: mobile toolbar tidy, stock-row overflow menu, stranded dashboard cards
- **Raised:** 2026-08-13 (design-remediation DR-9; carved from FU-578 #15b/#19/#30).
- **Type:** follow-up (redesign-scope layout work carved from DR-9).
- **What:** DR-9 shipped the core toolbar-overflow fix (shared `PageToolbar` now
  wraps its actions — verified: 0 horizontal scroll at 375px, no title collision at
  1280px) + a mobile stock-row **name 2-line wrap** so names stop truncating at ~10
  chars. Three heavier pieces from the DR-9 backlog are carved here because each is
  a mini-redesign with real interaction/layout risk that deserves its own focused
  unit:
  1. **Shopping-list toolbar mobile tidy (#4 refinement).** The wrap fix removed the
     overflow, but at 375px the action cluster wraps to ~165px of stacked toolbar
     chrome (Quick add · [No grouping|Location|Store] segmented · Refresh deals ·
     Select · More). Cleaner: on mobile collapse the secondary actions (grouping,
     Refresh deals, Select) into the existing **More** menu so only Quick add + More
     stay inline. Needs per-page work in `ShoppingListDetail.vue` (the segmented
     grouping control is the widest offender).
  2. **Stock-row trailing-icon overflow menu (#15b).** On phones the expiry / open /
     cart cluster still squeezes the row; the prescribed fix is to collapse the
     trailing action buttons into a single ⋮ overflow menu on mobile. Deferred
     because each button carries a rich nested interaction (expiry date-picker +
     push-menu, open→dialog, cart=`AddToListButton`) that a naive menu-in-menu would
     regress. **Tap-target pass (#19)** rides with it: `RowActionButton` is `size="md"`
     (~36px); D-004 wants ≥44px on touch surfaces.
     **⚠️ Measured addition (2026-09-02, dashboard chunk 6) — it is not only the
     tap target, it is the label.** Quasar's `size` prop sets a button's
     *font-size* directly, and **`sm` is 10px** — under D-003's 12px hard floor,
     on an interactive element where B2 asks for 14. Counted live on the
     dashboard at 1440px: **10 action-button labels at 10px** — "Cook" ×3,
     "Mark restocked" ×2, "Open item" ×2, "Dismiss" ×2, "Add", "Push 7 days",
     "Clear expiry". Chunk 6 fixed the *segmented-control* half of this in
     `BaseSegmented.vue` (one component, 19 consumers) and deliberately left the
     action buttons here: `size="sm"` on `q-btn` is an app-wide pattern, and
     re-scaling it is a design change across every surface, not a token sweep.
     The fix is one rule on a shared button wrapper, the same shape as
     `BaseSegmented`'s — not per-call-site edits.
  3. **Dashboard / reports stranded half-width cards (#30).** A lone `col-lg-6` card
     at the end of a zone sits beside dead air (D-011). The dashboard uses a CSS
     `order`-based zone system, so "make a lone last-in-zone card full-width" needs
     per-zone odd-count logic (the page already computes `zoneHasVisibleCards`), not
     a pure-CSS rule — hence its own unit.
     **✅ RESOLVED for the dashboard 2026-09-02 (chunk 2).** The reports half of
     this item is still open; the dashboard half is done and measured.
     *Amended then corrected:* the dashboard review claimed **five** dead regions
     "on a default desktop", which measurement showed is true at **≥1440px** and
     wrong below — because `col-lg-*` engages at Quasar's `lg` (**≥1440**), not at
     the app's own ≥1024 "desktop" (A8). Measured with the old classes re-applied
     in a browser: **1920px → 5 · 1440px → 5 · 1280px → 2 · 1024px → 2 ·
     768px → 2**. Two causes: mixed widths (`meal_plan` at `col-lg-8` could not
     share a row above 1440 and stranded a card above it *and* a third beside it;
     Kitchen's three `col-lg-4`s rendered 4+4 because `reconcile_pending` is
     hide-when-empty) and odd counts (an odd number of half-width cards always
     strands its last — the pair visible at *every* width).
     *Fix:* `helpers/dashboardGrid.ts` — `zoneColClasses()` gives the last card of
     any odd run of consecutive half-width cards the full row. Parity is per
     **run**, not per zone, because a genuinely full-width card mid-zone (the
     fortnight calendar) splits the zone into independent runs. Driven by a new
     `cardRendered()` predicate that folds in the two data guards (`budget`'s
     loaded status, `reconcile_pending`'s empty queue) so the layout maths cannot
     disagree with the template's `v-if` (R-003). All 17 wrappers now bind
     `cardCol(id)`; the ad-hoc `col-lg-4`/`col-lg-8`/missing-`col-sm-6` variants
     are gone, and the grid gutter moved to `q-col-gutter-lg` (24px = `--space-6`,
     which is what B4 specifies). **Verified: 0 dead regions at 375 / 768 / 1024 /
     1280 / 1440 / 1920**, measured in a browser, plus 16 unit tests including an
     exhaustive sweep of zone sizes 1–8. Spun off: **[[FU-836]]** (the
     `col-lg-*`-means-desktop trap) and **[[FU-837]]** (short cards stretching to
     a tall row-mate, seen in the chunk-2 screenshot).
- **Why deferred:** DR-9's accept criteria ("no horizontal scroll at 375px; row
  names readable on mobile") are met by the shipped toolbar wrap + name wrap; these
  three are quality refinements, each redesign-scope and higher-risk. Splitting keeps
  the shipped fix clean and verifiable (mirrors DR-7 → FU-624).
- **Recommended resolution:** opportunistic, or a dedicated mobile-layout turn. Cross-ref:
  `DESIGN_REMEDIATION_PLAN.md` DR-9, D-011/D-004, [[FU-578]].

## [OPEN] FU-630 — Assess inline corrections in the auto-mode meal-reconcile log
- **Raised:** 2026-08-13 (meal-reconcile auto-mode log; owner decision).
- **Type:** follow-up (deferred scope).
- **What:** The new auto-mode reconcile **log** (`MealReconcileLog.vue`, view `/meal-plans/reconcile` when `reconcile_policy.auto_drain` is true) is **view-only** by owner call — a record of what Dora did, no per-row actions. If a user spots a wrong auto-assumption ("Dora logged this cooked but I didn't"), there's currently **no correction path in auto mode** (the runner, which carries the verbs, only shows in manual mode). Assess whether the log needs a lightweight per-row correction (at least "Didn't cook" / "Adjust"), which would call the existing `POST /meal-plans/reconcile/<entry_id>` verb endpoint (the backend already supports correcting an `unresolved_auto` entry — see `submit_verb`). The verb API + receipt model already handle this; it's purely a UI addition.
- **Why deferred:** owner chose "view-only first, assess need for corrections later" — ship the log, see if corrections are actually wanted before adding per-row action affordances.
- **Recommended resolution:** when the owner has used the log a while, or a wrong auto-log is hit in practice. Add per-row "Didn't cook / Adjust" to `MealReconcileLog.vue` wired to `submitReconcileVerbAsync`.

## [OPEN] FU-628 — Confirm the neural-voice Preview now plays on mobile
- **Raised:** 2026-08-13 (Voice settings feedback, item 4 — reported defect).
- **Type:** finding (reported bug, fix applied, unverified on the failing platform).
- **What:** Owner reported the Settings → Voice **neural-voice Preview** worked on the server's own desktop browser but **errored on his phone (Firefox + Chrome)**. Root cause found: `VoicePicker.onPreview` did `fetch → await synth → new Audio → play()` with no audio-unlock, so the mobile autoplay policy blocked the post-`await` `play()` (the user-gesture activation is gone by then). Fixed by creating + priming the `<audio>` element **inside the click gesture** (silent-WAV prime via new `utils/audioUnlock.primeAudioForGesture`), then swapping in the synth blob. Desktop was unaffected (sticky activation) so this can only be confirmed on a real phone.
- **Why deferred:** no mobile device in this session; static analysis is not proof the mobile browser now allows it.
- **Recommended resolution:** confirm in browser — on a phone (Android Chrome + Firefox), open Settings → Voice, tap Preview on a downloaded neural voice → it should play, not error. Also added to `DORA_VERIFY.md`. Flip to RESOLVED once walked.

## [OPEN] FU-629 — Neural voice in chat / cook-mode may fall back to browser voice on mobile
- **Raised:** 2026-08-13 (Voice settings feedback, item 4 — related root cause).
- **Type:** finding.
- **What:** Same mobile-autoplay wall as FU-628, but for `useSpeechOutput.playPiper` (Dora chat replies + cook-mode narration). Those `speak()` calls are **not inside a user gesture** (they fire after an LLM round-trip, or off a cook-mode timer), so the same-element in-gesture trick can't apply — only the session-level silent-WAV primer, which claims iOS credit but doesn't grant Chrome/Android unmuted-playback credit. Net: on mobile, neural TTS may silently **fall back to the browser voice** (graceful — the user still hears a reply, just not the neural one), so it degrades rather than errors (which is why only the Preview surfaced as a visible bug).
- **Why deferred:** inherent mobile-autoplay limitation for non-gesture playback; a real fix needs Web Audio (AudioContext resumed at gesture time) — a heavier rework. Degrades gracefully today.
- **Recommended resolution:** opportunistic / only if owner wants neural voice guaranteed on mobile. Would pair with a gesture-time `AudioContext.resume()` primer.

## [OPEN] FU-626 — Admin "a newer Dora release is available to deploy" notification
- **Raised:** 2026-08-13 (Notifications settings feedback, item 10).
- **Type:** deferred job (new feature).
- **What:** Distinct from the in-app "reload for the new frontend" banner shipped this unit (that's the *already-deployed* build activating). This is the **operator-facing** signal the owner wants: "the Dora project has published a newer release than the one this server runs — admin, go update the deployment." Owner's shape: an **admin-only banner on the Settings page**, plus a **flashy attention affordance on the Settings nav/menu button for admins** to draw them to it. Needs a source of truth for "latest available release" (e.g. poll GitHub Releases / a version manifest) compared against `CURRENT_VERSION` from `/api/health`; must degrade gracefully when the check is unavailable or disabled (self-host / air-gapped), and probably be an opt-in check (don't phone home by default). `BaseButton` already has an `attention` pulse modifier that could drive the nav-button glow.
- **Why deferred:** genuinely new feature with a design fork (where does "latest release" come from? is the check opt-in? how does it behave offline / self-host?) — out of scope for a settings-copy/gating polish unit. Owner explicitly acknowledged this is its own task.
- **Recommended resolution:** later — needs a short design note first (release-source + opt-in posture), then build. Check §7.5 distribution-posture (no phone-home by default).

## [OPEN] FU-627 — Per-user deals-email opt-in ignores the install-wide `deals_email` admin flag
- **Raised:** 2026-08-13 (Notifications settings feedback, item 2).
- **Type:** finding.
- **What:** The deals-email section (NotificationsSettings) + the admin users-page column are now gated on `products` (data-presence) and SMTP, per owner feedback. But neither honours the separate install-wide `deals_email_enabled` AppSetting flag (admin toggle in Settings → System → Features, surfaced as `features.deals_email`). So with products present + SMTP configured but the admin master switch **off**, users can still toggle a deals-email subscription that the feature won't act on. Pre-existing (the section never gated on it); products-gating was what the feedback asked for.
- **Why deferred:** owner's item 2 specified `products` as the gate, not the master flag; adding a second gate is a scope-adjacent correctness call better made deliberately. Decide whether `deals_email` install-flag should also hide the section (likely yes) or whether `products` presence is intended to subsume it.
- **Recommended resolution:** opportunistic — when next touching deals-email. Fold `features.deals_email` into the `v-if` alongside `productsEnabled` if kept as a real master switch.

---

## [OPEN] FU-625 — Per-user LLM provider config is not round-tripped by shared backups
- **Raised:** 2026-08-12 (Assistant redesign / multi-provider).
- **Type:** finding (backup coverage gap).
- **What:** The Assistant redesign moved per-user LLM config off the `User` row into a new `UserLlmProvider` table. That table is **not** a section in `restore_shared.py SECTIONS`, so a shared backup no longer round-trips a user's provider settings (base URL, model). The **API key was never backed up** (deliberately excluded, FU-387) and still isn't — no secret regression. Only the non-secret provider prefs are now dropped from backups; before, they rode along in the `User` section.
- **Why deferred:** minor pre-release preference loss; adding a `UserLlmProvider` backup section (with `api_key_encrypted` in `excluded_columns` for the same FU-387 defence-in-depth) is a clean but out-of-scope addition, and the restore-time secret-exclusion pattern must be mirrored.
- **Recommended resolution:** opportunistic — when next touching `restore_shared.py` or backup coverage. Add a `UserLlmProvider` section keyed on (user, provider) with `api_key_encrypted` excluded.

---

## [OPEN] FU-624 — Toast lifecycle: single-column `notify()` wrapper + dismiss-on-route-change
- **Raised:** 2026-08-12 (FU-578 DR-7 carve-out).
- **Type:** deferred job (cross-cutting tidy).
- **What:** DR-7 de-congested the toast corner (CSS lift of the bottom-right column clear of the Dora launcher) but did **not** fix the other half of FU-578 #41 — a toast fired just before navigation **persists across the route change** past its read time. The robust fix is a single `notify()`/`useNotify()` wrapper that (a) is the one place toast position/timeout defaults live and (b) tracks active dismiss handles so a `router.afterEach` can clear them on navigation. There are **~296 `$q.notify({ position: 'bottom-right' })` call sites** to migrate to it (also lets us drop the repeated inline `position`/`timeout` and centralise the column — R-003). A boot-level monkeypatch of `Notify.create` was rejected: `$q.notify` captures the original reference at install time (before boot files run), so the wrapper is bypassed — call-site migration is the correct path.
- **Why deferred:** the mechanism is small but the 296-site migration is its own unit with real churn/regression surface; out of scope for a placement-polish unit. The visible congestion (the headline complaint) is already resolved by the CSS lift.
- **Recommended resolution:** opportunistic, or a dedicated tidy turn. Cross-ref: `DESIGN_REMEDIATION_PLAN.md` DR-7, D-009, [[FU-578]].

## [OPEN] FU-623 — Centralise `$q.dialog` behind a `noCaps`-injecting wrapper (enforce R-039)
- **Raised:** 2026-08-12 (FU-578 DR-3 dialog-casing sweep).
- **Type:** deferred job (tidy / single-source).
- **What:** DR-3 fixed ~15 files where `$q.dialog` buttons rendered ALL-CAPS by converting every `cancel: true` / string-shorthand `ok:`/`cancel:` to `{ label, noCaps: true }`. That matches the ~15 sites that already spelled `noCaps` out, but the app now has **~30 hand-rolled `$q.dialog` calls each re-stating `noCaps`** — R-039 is enforced by convention, not code. A thin composable (e.g. `useDoraDialog()` returning a wrapper that injects `noCaps: true` into `ok`/`cancel` unless already set, passing `{ component }` dialogs straight through, and preserving the returned `DialogChainObject` so `.onOk().onCancel().onDismiss()` chains are untouched) would make R-039 structural.
- **Why deferred / not done in-audit:** a **half-migrated** wrapper (some sites through it, some raw) is worse than the current consistent explicit pattern; migrating all ~30 sites — including `options`/`prompt`/`component` dialogs and chained resolvers — is its own unit with real regression surface, out of scope for a casing detail-audit.
- **Recommended resolution:** opportunistic — when next touching dialog code in bulk, or as a dedicated tidy. Cross-ref: R-039 / ADR-035 in `ENGINEERING_STANDARDS.md`, `DESIGN_REMEDIATION_PLAN.md` DR-3.

## [OPEN] FU-622 — Build an app-wide colour options / assessment board (visual tool)
- **Raised:** 2026-08-12 (FU-578 DR-1b; owner: "build this options board, i want to assess all the colours in the app with it").
- **Type:** deferred job (tooling / design aid). **Not now** — owner wants it logged, built in a later turn.
- **What:** an interactive visual board (Artifact / standalone page) for assessing **every colour token in the app**, not just brand-secondary. Per theme (all 10 = 5 families × light/dark), render each token in its **real roles** (surface, text-on-surface, toolbar bg with its ink, button bg with label, chip, edge-stripe, badge) with **live WCAG contrast ratios** and a pass/fail against the D-002 floors. Support **candidate values side-by-side** (current vs proposed) so the owner can react and pick. Pull token values straight from `web_app/src/css/tokens.scss` + `themes.scss` so it stays in sync.
- **Serves / supersedes-as-vehicle:** the resolution vehicle for [[FU-621]] (brand-secondary rethink), [[FU-224]] (app-wide colour-usage assessment — primary vs secondary vs accent/info), and [[FU-010]] (late-game holistic theme/colour review). Those are "look at the colours and decide"; this board is *how* you look.
- **Reuse:** the WCAG ratio probe already written for DR-1 lives in the session scratchpad (`contrast_probe.mjs` / `ratio.mjs`) — fold its hsl→sRGB→luminance→ratio math into the board. The DR-1 muted-ramp fix + DR-1b badge fixes are already probe-verified, so the board should show them green.
- **Recommended resolution:** a dedicated design turn — build the board, owner walks all tokens with it, decisions flow back into `tokens.scss`/`themes.scss` (and close FU-621/224/010 as they're settled).

## [OPEN] FU-621 — Rethink the brand-secondary colour (feels off; invisible as text on dark themes)
- **Raised:** 2026-08-12 (FU-578 DR-1b contrast pass; owner: "adjust the secondary colour, it has been feeling off for a while, not sure what to make it").
- **Type:** finding + design task.
- **What:** `--brand-secondary` is doing two incompatible jobs. In **light** themes it's a dark colour that works as both a toolbar background (white text on it) and as accent text on white cards. In **dark** themes it's set to a near-black mud (e.g. cherry-cola-dark `hsl(2 16% 19%)` sitting on a `hsl(2 16% 16%)` component) that reads as almost nothing — which is why the **Stock "Essential" footer count** (renders in brand-secondary via `PageCountsFooter` `tone:'secondary'` → Quasar `text-secondary`) measured **1.10:1** on Cherry-Cola-Dark, 2.26 Pesto-Dark, 2.94 Sourdough-Dark (probe, 2026-08-12). Light themes pass (5.7–14.5).
- **Two coupled fixes:** (1) **lift the dark-theme `--brand-secondary` values** into legible accents (like the dark-theme `--text-secondary` were lifted) — mind that secondary is also used as `-soft` chip bg + secondary-button bg, so check those roles don't invert; (2) give the **Essential footer count** a proper text ink (either the corrected secondary if it becomes legible, or a dedicated legible tone) so it stops using a dark accent as small text.
- **Why deferred / not blind-edited:** brand-secondary is an interlocking token (toolbar bg / accent / soft / button) and the owner is unsure of the target hue — this needs **visual iteration**, not a computed blind swap. Plan: render a per-theme options board (current secondary in its roles + candidate values with contrast ratios) for the owner to react to, then apply the chosen values.
- **Recommended resolution:** next design turn — driven via the app-wide colour options board [[FU-622]] (get the owner's pick there), then apply + re-probe. Cross-ref: `DESIGN_REMEDIATION_PLAN.md` DR-1b, [[FU-578]], [[FU-224]], [[FU-010]].

## [OPEN] FU-608 — Owner checklist: stand up the open-source + donation infrastructure, then swap the in-app placeholders
- **Raised:** 2026-07-31 (donation / open-source pivot — [[FU-562]]/[[FU-567]] resolved; part of the reframed [[FU-406]] release readiness).
- **Type:** deferred job (owner/external actions + a one-pass placeholder swap).
- **What:** the in-app donation buttons, `FUNDING.yml`, README, and issue/support links were **built with placeholders** on 2026-07-31 (see that worklog entry). This FU is the owner's checklist to stand up the real external accounts and then swap the placeholders to live URLs in one pass.
- **Owner checklist (external, do in this order):**
  - [ ] **Make the GitHub repo public** — `github.com/BenTalese/dashy-dora`. Until it's public, every restored issue/support link 404s for outsiders. (Confirm the canonical slug is `dashy-dora`, not the stale `DashyDora`/`DiscountDora` the old README/SECURITY.md carried — both are being corrected to `dashy-dora`.)
  - [ ] **Set up GitHub Sponsors** — apply at `github.com/sponsors`, complete Stripe/payout onboarding (has an approval wait). Once live, the profile is `github.com/sponsors/BenTalese`.
  - [ ] **Set up Buy Me a Coffee** — create the page, note the handle (`buymeacoffee.com/<handle>`). Instant, no approval wait — good candidate for the **primary** in-app CTA while Sponsors is pending.
  - [ ] **Set up PayPal.me** — the universal catch-all (owner added 2026-07-31). Create/confirm your `paypal.me/<handle>` link (near-zero setup). Already wired as the third in-app option + `FUNDING.yml` + README — just needs the real handle at swap time. *(Decided: these three only — they span one-off↔recurring↔catch-all and casual↔developer. Skip Ko-fi (dupes BMC), Patreon/Open Collective (overkill).)*
  - [ ] **Pick the primary in-app CTA** — currently Buy Me a Coffee (instant). Switch to whichever is live first if that changes.
  - [ ] **Supply README media** — real banner + screenshots + the feature GIFs (placeholder `<!-- GIF: … -->` blocks are already marked in `README.md`).
- **Then swap placeholders (one pass — all point at the sentinel `PLACEHOLDER`):**
  - [ ] `web_app/src/config/donationLinks.ts` — the single source for all donation URLs + which is primary (R-003). Swap the `PLACEHOLDER` values; the three button placements (menu bar, auth shell, settings) + tests read from here.
  - [ ] `.github/FUNDING.yml` — swap the placeholder handles so the repo's native **Sponsor** button lights up.
  - [ ] `README.md` — donation section links + media.
  - [ ] `dora_api/features/support/support_channel.py` — `_DEFAULT_SUPPORT_URL` is set to the real `dashy-dora` issues URL; confirm it once the repo is public (auto-lights Help / page errors / DoraBot report).
  - [x] GitHub **issue templates** written 2026-07-31 — `.github/ISSUE_TEMPLATE/{config.yml,bug_report.yml,feature_request.yml}` (YAML issue forms + a security/donate chooser). Remaining: (optional) enable GitHub **Discussions** and uncomment the Discussions contact link in `config.yml`; the donate contact link in `config.yml` also carries the `PLACEHOLDER` and rides the swap above.
- **Why deferred:** every account setup is an out-of-app owner action with signup/approval/payout steps; only the owner can do them.
- **Recommended resolution:** when you're ready to publish the repo publicly. Cross-ref: [[FU-406]] (release readiness), [[FU-557]] (support channel — the issues URL doubles as the support channel).

## [OPEN] FU-579 — `quasar dev` vite-checker overlay: pre-existing type errors block fresh-browser interaction
- **Raised:** 2026-07-18 (building the drive.mjs app driver)
- **Type:** finding
- **What:** `quasar dev` runs vue-tsc in watch mode via vite-plugin-checker, and its
  full-screen error overlay intercepts ALL pointer events in any fresh browser session.
  The errors are pre-existing: `e2e/bulk-waste.spec.ts` ×12 `noUncheckedIndexedAccess`
  ("Object is possibly 'undefined'" on `items[name]` index access) + `src-pwa/*` ×5
  (workbox module types / `ServiceWorkerGlobalScope` not in the SPA-mode tsconfig lib).
  The tree's standalone `vue-tsc` task has been reported clean in past sessions, so the
  dev-watch config evidently checks a wider file set than the CI task — worth aligning.
  `drive.mjs` works around it by CSS-hiding the overlay; a human dev opening `quasar
  dev` fresh sees the overlay too.
- **Why deferred:** driver-tooling unit; fixing spec types + tsconfig scoping is its own
  small change (R-008).
- **Recommended resolution:** opportunistic — null-guard the index accesses in
  bulk-waste.spec.ts, exclude `src-pwa` from the SPA-mode checker (or add webworker lib),
  and confirm dev-watch and the `vue-tsc` task check the same set.
- **Update 2026-07-18 (verify Batch 3 session):** the **bulk-waste half is FIXED** —
  the ×12 index-access errors turned out to hard-fail `npx quasar build` too (exit 2,
  no `dist/spa`), breaking `npm run test:e2e` from a clean tree; `itemsByName` now
  returns a throwing accessor and `vue-tsc --noEmit` is clean. Note the earlier "not
  visible in the vue-tsc task" observation was wrong — plain `vue-tsc --noEmit` did
  report them. **Still open:** the `src-pwa/*` ×5 workbox-type errors in the dev-watch
  checker only (they do NOT appear in `vue-tsc --noEmit` or `quasar build`), so the
  overlay problem in `quasar dev` may persist — re-test `quasar dev` fresh and scope
  the checker if it still trips.

## [OPEN] FU-578 — UX/UI review findings (owner-requested critical drive, 2026-07-18)
- **Raised:** 2026-07-18 (owner asked for a critical UX/UI pass; app driven live via the
  in-app browser pane — DOM/geometry/computed-style audit, no pixel rendering available)
- **Type:** finding (bundle — split into fix units as the owner prioritises)
- **ACTIONING (2026-07-18):** every item below is mapped to a work unit in
  `docs/04_proposals/DESIGN_REMEDIATION_PLAN.md` (DR-1..DR-16 — see its coverage
  table; three units flagged for owner sign-off: DR-6 scope, DR-10, DR-16). The
  standing rules extracted from this audit are now
  `docs/01_charter/DESIGN_STYLE_GUIDE.md` (D-001..D-015, enforced via R-035/ADR-031).
  This FU stays open as the finding-of-record until the DR units close; resolve
  items by DR unit, not piecemeal.
- **PROGRESS:** DR-6 ✅ closed 2026-07-22 (finish-pickers cut confirmed).
  **DR-1 ➗ ramp done 2026-08-12** — `--text-muted` retuned to ≥4.5:1 across all 10
  themes (probe-verified; worst Pesto 3.0→4.62); `--text-secondary` already passed.
  **DR-1b (2026-08-12):** ✅ alerts count badge + ✅ Buy/Wait/Skip verdict badge
  fixed (probe-verified AA all themes). New-item primary button + wordmark →
  owner-call "leave" (brand pairing / WCAG logo exemption). Essential stat +
  brand-secondary rethink spun out as [[FU-621]] (needs a visual options board).
  **DR-4 ✅ done 2026-08-12** — copy/leakage sweep shipped (items #1/10/12/13/14/17/21/22/38;
  #13 was already fixed by the account redesign; **#49 won't-do** — pre-release wants
  *no* back-compat redirects, so the uneven-alias finding is resolved by leaving both
  legacy paths 404-ing, not adding one). Backend 36 tests green, vue-tsc + eslint
  clean; live walk queued in DORA_VERIFY. **Note:** the existing legacy-redirect
  block in `router/routes.ts` (`/data*`, `stock-locations`, `stock-groups`,
  `recipe-vocab`, `admin/stores`, `meal-plans/board`, `stocktake/run`) is all dead
  back-compat aliases (confirmed unreferenced) — a pre-release strip is an available
  opportunistic cleanup if the owner wants it. **Remaining units:**
  DR-1 (contrast tokens), DR-2 (level colours + row legend), DR-3 (a11y/casing/glyphs),
  DR-5 (open-toggle mutation trap), DR-7 (toast/bubble placement), DR-8 (loading states),
  DR-9 (toolbar/grid layout), DR-10 (nav labels — owner call), DR-11 (recipe read-mode),
  DR-12 (alerts order + calendars), DR-13 (history grouping), DR-14 (locale/theme authority),
  DR-15 (micro-motion), DR-16 (onboarding activation — owner call). Suggested next: DR-1 then DR-3/DR-5.
- **What (bugs — concrete, verified in DOM/server):**
  1. **Copy bug:** "Vanilla Ice Cream expires expired 3 days ago." — `generators.py:113`
     composes `"{name} expires {window}"` but the past branch (line 98) already reads
     "expired N days ago". Only the `days < 0` branch is wrong.
  2. **Open-toggle click is an instant mutation with no cancel:** the stock-row
     open/sealed icon button PATCHes `is_open=true` immediately; the "Marking as open"
     dialog only governs expiry (Skip / Update — no Cancel), Escape doesn't close it,
     and backdrop-dismiss leaves the item open silently (server-verified). No undo toast.
  3. **Same button is unlabelled:** no aria-label, no tooltip (every other row action
     has one) — a11y + discoverability.
  4. **Mobile (375px) shopping-list detail overflows horizontally by ~255px** — the
     `page-toolbar-actions` row (Quick add / grouping / Store / Refresh deals / More)
     is 930px and never wraps. Confirmed visually (headless-Chrome screenshot): the
     grouping control clips at "Store", Refresh deals/More unreachable without
     horizontal scroll, page title truncates to "Shoppin…".
  5. **Main nav is icon-only with no labels at every width** (desktop included) —
     six ambiguous glyphs (box/bag/book/calendar/cart/chart) with no text, no
     active-page label. Discoverability cost for anyone who hasn't memorised them.
     [Corrected 2026-07-18 with real rendering: mobile properly collapses to a
     hamburger — the original "24px sliver" reading was the hidden strip.]
  6. **Dora helper bubble + tip toast float OVER page content on every page** —
     screenshots show the tip covering stock rows and sitting directly on top of the
     item-detail Level controls; the mascot overlaps the dashboard attention card and
     the footer stats. Carries an unexplained "6" badge. Needs safe-area placement
     (and the tip should auto-dismiss). [Replaces the retracted peek-at-phone-width
     item — real mobile row-tap correctly navigates to the detail page.]
  7. **Light-theme contrast fails broadly (WCAG AA):** muted secondary text
     rgb(117,138,134) at 12px ≈3.0–3.7:1 (footer stats, chips, captions); ghost toolbar
     buttons green 3.5:1; BUY badge 2.5:1@11px; brand-yellow titlebar text 2.8:1; count
     digits 2.9:1. Dark theme also: alerts badge 3.0:1, "New item" button 3.6:1,
     Essential stat 2.3:1 (visually confirmed barely legible in the footer).
  7b. **Split-theme render under System mode (REAL, screenshot evidence):** with the
     app booted dark and the OS scheme flipping to light (no reload), the header and
     row cards flip light while the page background, toolbar, and footer stay dark —
     `body--dark` (Quasar Dark plugin) and raw `prefers-color-scheme` CSS are two
     sources of theme truth that disagree until a full reload. R-002/R-003-adjacent.
- **What (friction / polish):**
  8. Belief chip copy "Dora: ~Low · low" — band and confidence both read "low"
     with different meanings; confidence needs a label or icon.
  9. US date format everywhere ("7/17/2026", "7/13 – 7/19") for an AU-market install —
     check default locale derivation (FU-043 surface).
  10. Alert copy "Expired 3 day(s) ago" / "Expires in 1 day(s)" — "(s)" pluralisation
     in the bell/alerts, while other surfaces pluralise properly.
  11. Recipe detail "Available meals: 0 unallocated of 1 cooked" next to "Last cooked:
     Never" — adjacent widgets disagree (seed data or display rule).
  12. "Add (file)" button label (recipe image + profile picture) is cryptic.
  13. Account page displays the user's raw UUID under their email.
  14. Cookbook card chips can duplicate ("Dessert · Dessert" when cuisine = category).
  15. ~~Meal-plans renders blank with no skeleton~~ RETRACTED — real rendering shows
     proper skeletons (they're textless, so the blind DOM probe missed them). Still
     true on the **dashboard**: async cards show literal "Loading totals…" /
     "Loading…" text instead of skeletons, so the page settles piecemeal.
  15b. Stock rows on mobile truncate names hard ("Barilla Pa…", "Brown O…",
     "Chicken …") — three always-visible 36px trailing icons (expiry, open-toggle,
     cart) eat the name column; consider collapsing to an overflow menu on phones.
     Also the belief chip crowds/overlaps the location line on rows that have one,
     and page titles truncate in the mobile header ("Stock it…", "Meal pla…").
  15c. The open/sealed toggle renders as a **padlock** (locked = sealed, green
     unlocked = open) — reads as security/permissions, not food state.
  15d. Item-peek tab strip clips off-screen at desktop width ("Substitu…" cut, no
     scroll affordance); Location breadcrumb truncates mid-word ("Middle shel…").
  15e. Dashboard desktop layout leaves large dead zones — several rows render a
     lone half-width card with empty space beside it (Next to cook, Best deals).
  16. Meal-plans header stats confusing: "1 planned / fully stocked" vs the sidebar's
     "0 / fully stocked for this week"; week shows 6 planned slots.
  17. Bell suggestion text/action mismatch: "Add it to your shopping list —
     flagged essential" but the only offered action is "Mark restocked".
  18. Stock rows aren't real links (no href) — no middle-click/new-tab on desktop.
  19. Tap targets 32–36px across stock rows/toolbars (guideline 44–48px); in-store
     tick checkboxes are properly 50×50.
  20. Kitchen-health "Stocktake 0/100" punishes an account that simply hasn't used
     stocktake yet — drags the overall score before first use (Effortless-charter rub).
  21. Dashboard greeting "Good afternoon, dora" — raw lowercase username.
  22. "$1 saves vs rrp" stat grammar ("saved"/"savings"; "RRP").
- **Second pass (2026-07-18, drive.mjs screenshots — cook mode / stocktake / reports / alerts):**
  26. **Full page load sits on the boot splash 2+ seconds** (warm dev reload): every
     hard navigation shows "Waking up Dora…" full-screen well past 2s before any
     content. Check what the splash is actually waiting on (and against a prod build).
  27. Stocktake runner's current-level button (e.g. red "Low Stock (change)") reads as
     an *action* ("set it to Low") next to the green "Still correct" — it's actually a
     state display that opens the picker. The "(change)" subscript carries all the
     disambiguation; consider "Change level" wording or a dropdown affordance.
  28. Alerts page leads with the 14-day "Upcoming" calendar — a huge, mostly-empty
     grid with unlabeled ~4px dots — while the 7 actionable alerts are below the
     fold. On a page named Alerts, the list should come first; the calendar dots
     need labels/counts on the day cells.
  29. Reports "Meals cooked" chart renders as one solid filled block (binary 0/1
     y-axis over the whole range) — adds no information next to the per-recipe list;
     the stock-value chart's dense 2-day x-labels are near-unreadable at 10px muted.
  30. Reports/dashboard share the lone-half-width-card dead-zone layout pattern
     ("Savings captured", "You keep running out of these" mostly empty at 2×768px).
  31. The Dora tip bubble confirmed overlapping content on cook mode (ingredient
     list), reports (Top-10 rows), and the alerts calendar — reinforces item 6; in
     cook mode it collides with the surface's whole big-text hands-free purpose.
  32. **History tab has no grouping/collapsing for repetitive events:** the chatty
     seed item renders 50 consecutive "Pushed expiry +N days" cards as a 6,500px
     monotonous wall (cap + footer work, but a "×50 over 3 months" collapse or
     per-kind filter chips are needed for it to be readable). Each card also mixes
     date formats — US timestamp header ("7/16/2026, 12:15:37 PM") over an ISO body
     ("2026-10-08 → 2026-10-10").
  33. **Unexplained dimmed row state on Stock Overview:** Parmesan Cheese renders
     fully greyed (muted name, grey level square, ghost icons) with no tooltip or
     legend saying why, while its BUY-badged neighbour Sourdough is normal. Whatever
     the state is (inactive? unknown level?), it needs to say so.
  34. My Products: solid surface (price + strikethrough + % off + store + linked-item
     chip + Link… affordance). Nits: the permanent "Select products to add them to a
     list, unlink, or mark inactive" instruction banner spends a full-width row on a
     rare mode; "Stock items without products (15)" reads as data, not as the filter
     button it is; two different cart glyphs (filled vs plus-variant) carry meaning
     (on-list vs add) with no cue.
  35. Dora helper panel is genuinely good (context "On this page" actions, the P8-07
     quick-check card with Why?/Snooze/Dismiss, Basic/AI toggle). Nits: "Hi, dora!
     Burger online. What's the move?" — lowercase raw username again + "Burger
     online" is cute but cryptic; the disabled "AI" segment shows only a hammer
     glyph with no hint why it's off (no LLM configured).
  36. Item detail's standalone page tabs fit fine — the tab-strip clipping (15d) is
     peek-pane-specific.
- **Fourth pass (2026-07-18, onboarding via fresh `qa-ux-walk` account + draft-shop + add-item):**
  37. Register form shows **"Username is required" before the user has typed anything**
     (eager validation on a pristine form).
  38. Onboarding STORY scenes are excellent copy ("The weekly shop is detective
     work.", "every part of Dora is a toggle."); nit: the final scene's CTA renames
     Next → "Set up in about a minute", fine for humans. SETUP step 1's "I batch-cook"
     explainer is jargon-heavy for a first run ("cook-pool controls", "'N free' chip",
     "shortfall warning") — the Preferences page says the same thing more simply.
  39. The "You're all set!" hub offers **Price history as a first destination** — on a
     brand-new account that page is empty by definition (data-gated); dead-end risk.
     No guided "add your first items / import" step in SETUP — pantry seeding is just
     one of eight equal cards, yet it's the activation make-or-break for this app.
  40. Shopping-lists page at 1280px: the page title wraps ("Shopping / lists") with
     the Quick-add button colliding beside it — toolbar spacing is off even at
     desktop (same toolbar that overflows on mobile, item 4).
  41. Bottom-right congestion: success toasts, the Dora tip toast, and the mascot all
     stack in the same corner; the "Drafted 10 items." toast also **persists across
     route changes** well past its read time.
  42. "Draft my shop" flow itself is great (10 items, lands on the review list, clear
     toast copy) and the Add-a-stock-item dialog is exemplary (4 fields, optionals
     marked, Essential info hint) — keep both as-is.
- **Fifth pass (2026-07-18, light theme + finish flow + cook-mode end):**
  43. Light theme seen with real pixels: broadly pleasant (white cards read well);
     the faint bits match the earlier AA numbers — belief-chip "· low" suffix and
     footer stats are visibly weak; the yellow-on-green wordmark is loud/borderline.
     Theme save is eager with a "Theme updated." toast ✓.
  44. **Row state visual language is undocumented and inconsistently signalled:**
     rows carry meaningful edge/tint codes (blue edge = on a list, amber = attention,
     red = out, cream tint = ?) with no legend anywhere; Canned Tomatoes shows a
     cream tint with NO matching icon signal, and the dimmed Parmesan (33) is still
     unexplained. One legend (or tooltips on the edge) would pay for itself.
  45. The missing restock-review pickers were FU-582 — **resolved 2026-07-22 as not-a-gap**: the picker was cut on purpose in `a3b82644`; the contract has now been removed server-side too. Not a finding.
  46. Cook mode end-state: "Finish ✓" swaps in for Next, and the step's ingredient
     row highlights as you advance — excellent detail, keep.
- **Sixth pass (2026-07-18, plan wizard / kitchen-setup + admin settings / search / tablet):**
  47. Plan step-by-step wizard: the same recipe appears in multiple groups
     (Favourites AND All recipes) **each with its own checkbox** — duplicate
     selectable rows in one pick list (same duplication in the meal-plans left
     rail). Dedupe or visually link the instances.
  48. **Locale/timezone root cause of the US dates (item 9):** household timezone
     ships as UTC and locale is never asked — onboarding SETUP has no region step,
     while Admin → System → Timezone even has a "Use this device" one-click
     derivation that nothing invokes at first run. Money/date formats are wrong
     until an admin finds that page. Recommend: derive tz/locale from the browser
     at first boot (or a one-line SETUP step), keep admin override.
  49. Trivial: `/settings/stores` has no legacy alias (404s) while sibling
     `/settings/stock-locations` redirects — uneven alias coverage; real nav is fine.
  50. Meal-plans' mini month calendar (right rail) shares the alerts-calendar
     problem (28): a big grid of featureless cells with one outline + one dot.
  Keep-as-is positives this pass: Stock-locations settings page (tree + counts +
  explainer copy is the best settings page in the app); Admin → System sidebar
  organisation; stock search (instant substring filter, footer stats re-scope to
  the matches, clear-X affordance).
- **Seventh pass (2026-07-18, reconcile queue / bulk mode / export):**
  51. Reconcile queue reuses the stocktake card-runner pattern (progress bar, one
     card, verb buttons incl. red "Didn't cook" + "Skip for now") — consistency
     keep-as-is. But its date reads "Mon, Jul 13" while the meal-plans grid shows
     "7/13/2026" for the same slot — one more face of the locale/format family
     (9/48): the app has no single date-format authority.
  52. **Belief chips pop in late and shift row layout:** consecutive shots of the
     same stock list show rows first without, then with "Dora: ~Low" chips — the
     async beliefs fetch reflows the name/location line after paint. Reserve the
     space or fade in without reflow.
  53. Bulk-select bar at 0 selected: disabled actions ("Add to list…", "Log
     waste…" — functionally disabled, e2e-pinned) render in the same white as
     enabled ones; only "Deselect all" greys. Style the disabled state.
  54. Export menu (CSV / Print-PDF) is clean — keep.
  (Positives worth keeping as-is: cook mode's step layout — big type, progress,
  location-grouped scaled ingredients, per-ingredient swap, tools chips — is the
  strongest screen in the app; stocktake's focused card flow; reports' friendly
  empty states and wastage-reason tiles.)
- **Needs a real-browser check (pane is hidden → paint/rAF-gated, may be harness-only):**
  23. Splash "Waking up Dora..." dismissal is transition-gated (`splash-fade-leave-active`
      wedged at opacity 1, z-9000, pointer-events auto — it ate clicks). Check a
      backgrounded/throttled first load on a real device.
  24. UPGRADED to 7b (confirmed real in headless Chrome — split-theme render).
  25. One Vue render error in console during login→dashboard: `AuthShell.vue:114`
      renderSlot "Cannot read properties of null ('ce')" (twice, also captured by the
      client-log channel). Reproduce cleanly before chasing.
- **Why deferred:** review unit was assessment-only per owner instruction; no code
  changed.
- **Recommended resolution:** owner triages this list; quick wins (1, 3, 10, 12, 13, 21,
  22, 14) are one-line-ish fixes; 2 needs a design call (defer mutation until dialog
  resolution, or add Cancel+undo); 4–6 are a mobile-layout unit; 7 is a theme-token
  contrast pass (R-002 territory); 23–25 go to DORA_VERIFY after triage.

## [OPEN] FU-576 — uploads.spec.ts L79 pin fails under the system-Chrome e2e channel
- **Raised:** 2026-07-17 (verify-campaign Batch 2, running the e2e suite)
- **Type:** finding
- **What:** `e2e/uploads.spec.ts:46` ("Remove clears the picked file without reopening
  the picker", FU-545 L79 pin) fails when the suite runs under `DORA_E2E_CHANNEL=chrome`:
  clicking **Remove file** emits one `filechooser` event (`pickerOpened` = 1, expected 0).
  The two functional assertions in the same test PASS — the idle "choose a spreadsheet"
  prompt returns and the picked filename is cleared — so the Remove UX itself works; only
  the picker-reopen instrumentation trips. Reproduces in isolation; **not** caused by the
  stocktake work this session (that spec is green). Suspected browser-channel difference in
  how `filechooser` fires on the hidden `<input type=file>` — the campaign's green baseline
  ran the bundled Chromium, which isn't installed on this box (`npx playwright install`
  couldn't fetch it, hence the `chrome` fallback).
- **Why deferred:** out of scope for the stocktake slice; needs a bundled-Chromium run to
  confirm channel-only vs a real Remove-handler regression, and possibly a channel-tolerant
  assertion.
- **Recommended resolution:** when a bundled-Chromium (or CI) e2e run is available — re-run
  `uploads.spec.ts`; if green there, harden the L79 assertion against the Chrome channel
  (or pin the channel for the pin). Only treat as a product bug if it also fails on Chromium.

## [OPEN] FU-575 — Stock-item / recipe name uniqueness is application-level only (concurrent-create race) + recipe name not whitespace-normalised
- **Raised:** 2026-07-17 (Codex review of stock-item create — P3, + a parallel spotted while fixing P1/P2).
- **Type:** finding (low priority).
- **What:**
  1. **P3 — no DB unique constraint on `StockItem.name`.** `CreateStockItemHandler` checks for an existing (case-insensitive) name before insert (`create_stock_item.py:~90`), but the column has no unique constraint, so two tabs/devices can both pass the check and insert the same name (a soft duplicate — not corruption). Same shape on `Recipe.name`.
  2. **Recipe name whitespace parallel** — the P2 fix added a `strip` `field_validator` to `Create/UpdateStockItemRequest`; `create_recipe.py` / `update_recipe.py` use `Field(min_length=1, max_length=255)` **without** it, so recipes still accept `" Foo "` / `"   "`. Same class, different surface (R-code-style consistency).
- **Why deferred:** the race is vanishingly unlikely + low-harm on a single-household self-host app (Codex itself rated it low). A real fix means a **unique constraint + migration + a case-insensitivity decision** (a plain unique index is case-sensitive on Postgres; case-insensitive uniqueness needs a functional index / `citext`, which differs SQLite↔Postgres — R-005/R-006 care). Disproportionate right now.
- **Recommended resolution:** opportunistic. (a) The recipe-name strip is a trivial 4-line `field_validator` mirror of the stock-item fix — do it next time recipes are touched. (b) The unique-constraint/race is a data-model call — bundle with the FU-045 Postgres/migration work or whenever concurrent-write hardening is on the table; decide case-insensitive-uniqueness semantics then.

## [OPEN] FU-557 — Stand up + wire the real support channel (FU-370 hook-up)
- **Raised:** 2026-07-14 (FU-370 build).
- **Type:** deferred job (out-of-app operator action + a one-line code change).
- **What:** FU-370 shipped the full support/"Report an issue" plumbing **dormant** —
  it renders nothing until a channel is configured. To turn it on:
  1. Pick + stand up a channel (see `docs/04_proposals/PROPOSAL_SUPPORT_CHANNEL.md`
     §3 / §6 — Option A public `dashy-dora-issues` repo w/ a `bug_report.yml`
     template is the recommendation; Option B hosted form; Option C email).
  2. Set the target in **one** place: either edit `_DEFAULT_SUPPORT_URL` /
     `_DEFAULT_SUPPORT_EMAIL` in
     [`support_channel.py`](dora_api/features/support/support_channel.py) and commit,
     OR set `DORA_SUPPORT_URL` / `DORA_SUPPORT_EMAIL` env for that install.
  3. Rewrite the Help "About" copy (currently a solid honest draft) into your own
     voice if you want — `HelpPage.vue`, the `support-copy` block.
  Once set, the Help button, the error-state "Report this" button, and the DoraBot
  `report_issue` link all light up automatically. No further code needed.
- **Why deferred:** the channel is an out-of-app decision that involves creating
  external infrastructure (repo/form/alias) — the user's to make, on his time.
- **2026-07-31 (donation / open-source pivot):** with the paid model dropped, support is
  now explicitly **best-effort, not contractual**. Option A (a public GitHub issues repo
  with a `bug_report.yml` template) is now clearly the right fit — it's the natural
  open-source channel and doubles as the "show it off" surface. No commercial SLA framing.
- **Recommended resolution:** when you're ready to point people at a channel (the
  user asked for this FU explicitly so the hook-up isn't forgotten). Natural to pair with
  the open-source release work in [[FU-406]].

## [OPEN] FU-520 — Test-suite improvements Phase 4: frontend Vitest + Hypothesis + Postgres CI + scraper/emailer fixture tests
- **Raised:** 2026-07-09 (split from FU-169 close-out).
- **Type:** deferred job (large — should be its own multi-session unit).
- **What:** the Phase-4 slice of [`docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md`](docs/04_proposals/PROPOSAL_TEST_SUITE_IMPROVEMENTS.md) §5.E-F P2. Status after the 2026-07-10 targeted sweep:
  1. **Frontend Vitest + Vue Test Utils — SHIPPED incl. first component tests (2026-07-10, two passes).** 9 util/composable spec files (139 tests) + `stockLevelDot.spec.ts` (11 component tests over both StockLevelDot components) → 203 total, ~1.5s. The Quasar component-mount pattern is now established in `vitest.config.ts` + that spec: `@vitejs/plugin-vue` wired, `quasar` aliased to its client bundle (the SSR bundle throws under vitest), real Quasar components registered per-mount, per-file `// @vitest-environment jsdom` pragma. **Remaining:** `AddToListButton` (601 lines, API-coupled — needs service mocking) + shopping rail + lifecycle-coupled composables (`useMealPlanExport`, `useOfflineQueue`); all unblocked by the established pattern.
  2. **`merchant_api` scraper tests** against saved HTML fixtures — **still open**; the scraper lives in the sibling `dora-companion` repo, so this belongs there ([[FU-161]] Aldi net).
  3. **`emailer` tests — SHIPPED 2026-07-10.** `tests/test_email_templates.py` (13) + `tests/test_email_sender.py` (16): all 5 content templates + layout + autoescape, MIME assembly, SMTP wire choreography via fake transport, dry-run degradation, error propagation. Found [[FU-522]].
  4. **Hypothesis property tests — SHIPPED 2026-07-10.** `tests/test_domain_properties.py` (26): invariants over `recipe_cookability` (incl. the canonical *cookable ⇒ nothing required missing*), `stock_status`, `product_offer`, `units`. Found [[FU-524]]. `hypothesis` pinned in requirements.txt.
  5. **Postgres-backed CI test runs** once CI is un-commented ([[FU-405]] / `.github/workflows/ci.yml`) — **still open**. Note the commented workflow was fixed 2026-07-10 to run bare `pytest` (full suite) + `npm test`, so un-commenting inherits the right scope.
- **2026-07-11 update:** component-level Vitest expanded — **AddToListButton (20, the queued item), AlertRow (13, incl. the unknown-kind degrade regression), DoraModeSlider (6), SettingsFileDrop (12)**; frontend suite now 254 tests / 15 files. Pattern note for future specs: module-boundary Pinia store mocks must return `reactive({...})`, not plain objects of refs (`storeToRefs` rewraps computeds — documented in `addToListButton.spec.ts`). Remaining: scraper tests (companion repo), Postgres CI.
- **2026-07-12 update:** **Pinia store layer** now covered — `stockItemStore` (16, incl. optimistic level-swap + rollback-registry contract + FU-511 cross-store toast), `shoppingListStore` (10), `alertStore` (9, pins server-owned `actionable_count` = R-003), `locationStore` (9). Frontend suite now **298 tests / 19 files**. `authStore` (bootstrap retry / in-flight sharing / 401 clear) flagged as the strongest remaining single-store candidate; thin fetch-wrapper stores deliberately skipped. Store oddities noted (not bugs): `stockItemStore` rollback is index-captured (narrow race) and only fires via the global unhandled-rejection handler — a caller that `catch`es strands optimistic state (documented design). Remaining: scraper tests (companion repo), Postgres CI, authStore spec.
- **2026-07-13 update — parent FU-371 resolved; this FU tightened to its three real remnants (everything else shipped):**
  1. **Postgres-backed CI + coverage gate/ratchet** — blocked on CI being un-commented ([[FU-405]] P7-09 Ops; `.github/workflows/ci.yml` is deliberately fully commented). No point gating coverage while CI doesn't run. Un-blocks as a set when FU-405 lands.
  2. **`merchant_api` scraper fixture tests** — the scraper lives in the sibling `dora-companion` repo; belongs there under [[FU-161]], not this repo.
  3. **Opportunistic component/composable specs** — `authStore` (strongest remaining candidate), shopping rail, lifecycle-coupled composables (`useMealPlanExport`, `useOfflineQueue`); pattern is established, done per-touch when the surface next changes.
- **2026-07-14 update — item 3 `authStore` SHIPPED.** `web_app/test/unit/authStore.spec.ts` (17 tests): bootstrap probe (existing-session /me, fresh-install skip, **shared in-flight promise**, post-boot short-circuit), the **parked-promise boot-retry loop** (network vs generic message; real `NormalisedApiError` so the `isNetworkError` branch runs), credential entry points, the **FU-355 logout + silent-401 → clear-user + `clearAllListState`** contract (401 handler captured via a spied `setUnauthorizedHandler`), and the avatar cache-bust. Frontend suite now **360 tests / 27 files**. Pattern note: partial-mock `axiosHttpClient` with `vi.importActual` to keep the real error class while spying the unauthorized-handler setter. Remaining item-3 surfaces (shopping rail, `useMealPlanExport`, `useOfflineQueue`) stay opportunistic.
- **2026-07-14 update (later) — Postgres runs + scraper fixtures + two divergence bug fixes SHIPPED; item 1 reduced to CI wiring only.** Ran the **full backend suite on real Postgres** via a new `DORA_TEST_DB=postgres` selector (`tests/db_backend.py`) + a Postgres per-test isolation snapshot (DELETE-all reverse-FK + bulk reinsert; `tests/e2e/dora_api/conftest.py`). 37 failures → **0**; 1490 passed on both PG and SQLite (no regression). The failures traced to **two systemic SQLite-vs-Postgres divergence bugs, fixed at source** (real runtime bugs on a PG deployment): (a) **raw-`text()` UUID bind is dialect-dependent** — SQLite wants `bytes`, Postgres wants `str` (a wrong bind is a 500 on PG / silent zero-rows on SQLite); fixed `recipes/pool.py:bump_pool`, `meal_plans/reconcile.py:_id_bytes`, `tests/support.py:uuid_bind`; (b) **over-length `alert_key` (String(255)) 500s on Postgres** (`StringDataRightTruncation`) but passes silently on SQLite — `alerts/interact_with_alert.py` now length-guards to an idempotent no-op. **Item 2 (scraper fixtures) DONE** — `dora-companion/tests/test_provider_parsers.py` (8: Coles JSON translate + Aldi HTML parse via real selectors). **Item 3 leftovers:** shopping-rail (`shoppingListRailItem.spec.ts`, 9) + `useMealPlanExport` (3) DONE; frontend suite **372**. So item 1 is now **just the CI wiring** (gated on [[FU-405]]); only `useOfflineQueue` remains opportunistic on item 3. The dialect-aware-bind lesson is recorded in the `sqlite-uuid-text-binding` memory for future hand-rolled `text()` sites.
- **2026-07-15 update — item 3 fully drained; `useOfflineQueue` SHIPPED.** `web_app/test/unit/useOfflineQueue.spec.ts` (13 tests): `tryWithQueue` swallow-network-only vs rethrow-others vs pass-through-success; `drain` replays oldest-first, STOPS on the first network error (rest stay queued, `attempts` counted), shunts a non-network rejection into the conflict pile and continues; the false→true `apiReachable` auto-drain edge; `discardConflict`/`retryConflict` (retry re-queues + drains); per-user localStorage isolation + rehydrate-on-user-switch + corrupt-payload degrade-to-empty. Pattern note for future singleton-composable specs: the module registers **module-level watchers that are never torn down**, so the reactive seams (`useNetworkStatus`, `authStore`) must be re-mocked with a FRESH ref per test via `vi.doMock` in `beforeEach` (a hoisted `vi.mock` shares one ref across `resetModules`, letting a prior test's zombie watcher fire on the current flip and drain its stale queue). Import `NormalisedApiError` fresh alongside the composable so `instanceof` lines up with the re-evaluated class. Frontend suite now **385 tests / 30 files**. **Only item 1 (Postgres CI wiring) remains — nothing else on this FU is actionable in-repo.**
- **Recommended resolution (remaining):** item 1's *run-on-Postgres* half is done (suite is green on PG via the selector) — only the CI wiring remains, gated on [[FU-405]]. Item 3 is now fully done (all component/composable surfaces covered). **Recommended resolution point:** Postgres CI with [[FU-405]] — that is the sole remaining trigger.
- **Cross-ref:** parent [[FU-371]] (RESOLVED 2026-07-13); [[FU-519]] Phase 3 (RESOLVED 2026-07-13).

## [OPEN] FU-214 — Products-as-overlay Phase F tail: product-surface browser verify + L197/205/206/223/225 items
- **Raised:** 2026-06-22 (Phase F kickoff — reconstructed 2026-07-01 from `PRODUCTS_OVERLAY_RUNBOOK.md` + 8 worklog references; **the FU entry itself was missing from both ledgers**).
- **Type:** deferred job (multi-item Phase-F tail).
- **What:** Original scope was **product-surface browser verify + build the L205/206 bulk-select variants + decide L197 hard-delete**. Over time it accumulated:
  - **L197** — hard-delete decision for products (still not made).
  - **L205 / L206** — bulk-select variants on product surfaces (not built).
  - **L223** — Price-History hover-bubble dark-mode bug (added 2026-06-22 worklog).
  - **L225** — Price-History box-fit bug (redirected here from FU-227 scope, worklog).
  - Product-surface browser verify (My Products page, Price History page, stock-item Products tab) — waits on a running app.
  - **PH residuals (folded in from FU-431, 2026-07-16 — no redesign brief):** (a) **PH-2** "can select products but no change occurs on the Price History page" — behaviour verify with real product data (reported-defect, confirm in browser). (b) **PH-10 optional** — the desktop bottom-sheet the feedback asked for already exists (`PriceHistoryBottomSheet.vue`, built for FU-227) but is wired to the stock-item "your prices" widget; My Products currently *navigates* to the full `/price-history` page instead. Reusing the bottom sheet for the My-Products→product flow is a small **opportunistic** enhancement — evaluate it with real data on-screen during this pass; don't build blind. (c) **PH-1** discoverability is **decided** (see FU-431 in `_RESOLVED`): contextual entry is the right model, so just confirm during verify that My-Products / Subscriptions / onboarding entry points feel adequate — no nav tab.
- **Why deferred:** every item needs a running browser session; bulk-select is real UI work; L197 is a design call.
- **Recommended resolution:** when the next browser-verify session opens **and** the products layer has real data — knock out L223/L225 as bugs, do the browser-verify checklist, then split L197 (design call) and L205/206 (build) into their own FUs if this one gets too heavy. **This FU is the runbook's Phase F blocker** ([`PRODUCTS_OVERLAY_RUNBOOK.md`](docs/04_proposals/PRODUCTS_OVERLAY_RUNBOOK.md) §Status row F). Related: [[FU-227]] (resolved), [[FU-212]] (resolved), [[FU-210]] (resolved).

## [OPEN] FU-406 — Open-source release readiness (was: self-host launch; de-commercialized 2026-07-31)
- **Raised:** 2026-07-01 (legacy prompt-plan audit). **Narrowed 2026-07-14 (self-host-first). Reframed 2026-07-31 (donation / open-source pivot).**
- **Type:** deferred job (release gate for the open-source product).
- **What (post-pivot):** the checklist to **release Dora as free open-source software**:
  a **project README / showcase** (what it is, screenshots, how to self-host, a donation/
  Sponsors link), a **release process** (GitHub Releases + versioning + changelog — no paid
  download gate), and pointing at a **support channel** (best-effort, [[FU-557]]).
- **Dropped by the pivot ([[FU-562]] / [[FU-567]] resolved won't-do):** the *sales* landing
  page, the licence change (keeping MIT), the scraping/terms disclaimer (owner dropped it),
  and any billing/download-gate wiring. The "never overpay — personal price intelligence"
  framing survives as a **product story** for the README, not a sales pitch.
- **Relocated (unchanged):** the operate-the-service sliver — uptime/SLA, on-call, escalation
  — stays in `docs/04_proposals/OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md` §3 (hosted-only).
- **Why deferred:** last-mile; do it when you're ready to publish the repo publicly.
- **Recommended resolution:** at the open-source release. **QA half already covered by [FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md)** (Track 1 FST + release-gate). Remaining: README/showcase, release process, support-channel stand-up ([[FU-557]]).

## [OPEN] FU-405 — P7-09 Ops (observability, CI/CD deploy, staging, backups)
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job (Phase 4).
- **What:** P7-09 — production ops. CI is deliberately disabled in this repo (`.github/workflows/*.yml` commented out to preserve GH free-tier — see memory `feedback_ci_disabled_policy`). Observability, staging, backups all unplanned. **Do not silently re-enable CI as part of this** — separate call.
- **Why deferred:** Phase 4 + CI-cost policy.
- **Recommended resolution:** Phase 4 — pair with billing (P7-06) so ops cost lands with revenue.
- **Note (2026-07-09, FU-387 audit):** when CI is re-enabled at Phase 4, wire in dependency scanning as part of this FU — a scheduled `pip-audit -r requirements.txt` + `npm audit --prefix web_app` job that opens an issue on new advisories. FU-387 shipped a manual `scripts/security-audit.sh` runner as the interim; promoting it to CI belongs here, not in a fresh FU. See [SECURITY_REVIEW.md](docs/security/SECURITY_REVIEW.md) §6 for the current baseline the CI job should measure against.

## [OPEN] FU-404 — P7-08 Compliance (privacy policy, DSAR, deletion) — hosted/controller-scoped
- **Raised:** 2026-07-01 (legacy prompt-plan audit). **Scoped 2026-07-16 (self-host-first, FU-412 plan).**
- **Type:** deferred job (hosted/managed — not a self-host sale prerequisite).
- **What:** P7-08 — the privacy-law **compliance contract**: privacy policy + ToS wording, and self-service **data export + account/data deletion (DSAR)**. Overlaps with [[FU-401]] (P5-02 Privacy). Security-headers half already shipped (FU-387).
- **Scoping (2026-07-16):** the DSAR/compliance obligation follows the **data controller**. On self-host that's the *operator*, not the software vendor (`COMMERCIALIZATION_REPORT.md` §1.2 — "self-hosted sidesteps most; SaaS does not"), so this **activates only when you host user data** → it now lives with the parked hosted work in [`OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md`](docs/04_proposals/OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md) §3. The **self-host** track keeps only a short honest **privacy statement** (`SELF_HOST_COMMERCIALIZATION_PLAN.md` Track 3), drafted with the licence text. Self-service export/delete may still ship as optional *product features* on the repository seam, but they're driven by this hosted need, not by the self-host sale.
- **Why deferred:** hosted-path work; no near-term trigger while the product is self-host-only.
- **Recommended resolution:** when a hosted/managed offering is opened (OPTIONAL_SAAS revisit trigger). **Partially covered by [FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md)** — the multi-user + admin FST persona flows (Track 1) will *exercise* any export/delete/privacy surfaces that do get built; the senior-review pass on auth + backup catches security-header/credential-exclusion drift. **Not covered:** the legal drafting + compliance contract wording (owner + lawyer).

## [OPEN] FU-389 — P5-04 Mobile / PWA field test
- **Raised:** 2026-07-01 (legacy prompt-plan audit).
- **Type:** deferred job.
- **What:** P5-04 — real-device mobile / PWA testing pass. Overlaps with [[FU-411]] platform builds + P8-10 native.
- **Why deferred:** Phase 3-adjacent.
- **Recommended resolution:** fold into the P8-10 native-app brief; a device-lab pass is a natural gate before deciding native vs PWA-only.

## [OPEN] FU-363 — Cross-cutting / niche feedback (Bucket C in COVERAGE_GAPS) — 4 of 8 actioned
- **Raised:** 2026-07-01 (COVERAGE_GAPS sweep).
- **Type:** deferred job (bundle — 8 sub-items; **items 2, 5, 6, 7 actioned 2026-07-15, 4 remain**).
- **What:** `COVERAGE_GAPS.md` Bucket C cross-cutting items with no per-surface home:
  1. **[OPEN]** Full systems QA test doc (final regression walkthrough of every feature). User wants done LAST to capture the final product.
  2. **[ACTIONED — design, then WON'T-DO for self-host 2026-07-16]** Usage analytics / telemetry. Designed in [`PROPOSAL_USAGE_TELEMETRY.md`](docs/04_proposals/PROPOSAL_USAGE_TELEMETRY.md), then owner decided **not to build for self-host** — the ask is the maintainer's and only pays off as hosted aggregate analytics; the self-host efficiency lens was dropped as not useful to the operator. Whole topic **relocated to `OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md`** (hosted-only). FU-566 resolved WON'T-DO (see `_RESOLVED`).
  3. **[OPEN]** UI uniqueness / polish design pass — "looks just okay, not polished/unique."
  4. **[OPEN]** Push notifications between users (share a shopping list via notify).
  5. **[ACTIONED 2026-07-15 — decided: CUT]** Kivy P2P sync branch — no home in the current client-server architecture; recorded in [`MULTI_USER_READINESS.md`](docs/05_investigations/MULTI_USER_READINESS.md) §5.1.
  6. **[ACTIONED 2026-07-15 — shipped]** Main menu bottom border — removed the `q-header bordered` border per the feedback lean (`MainLayout.vue`); browser-verify queued.
  7. **[ACTIONED 2026-07-15 — declined]** Real ALDI/IGA logos — WON'T-DO (trademark/licensing risk; Dora ships zero logos by design per `StoreLogo.vue`). Existing workaround: per-store logo **upload** already exists (`StoresSettings.vue`). Recorded in `DORA_FOLLOWUPS_RESOLVED.md`.
  8. **[OPEN]** General UI consistency — cross-cutting.
- **Why deferred:** no per-surface home; the 4 remaining are Phase 3/4-timed or design-only.
- **Recommended resolution:** split into per-item FUs *only when picked up*. Remaining: items 1 (QA test doc) + 3 (polish pass) + 8 (UI consistency) are natural Phase-4 gates; item 4 (push notifications) is a Phase-3-ish feature build. Close this bundle once those four are picked up.

## [OPEN] FU-224 — App-wide colour-usage assessment (primary vs secondary vs accent)
- **Raised:** 2026-06-18 (Stock-pages feedback pass)
- **Type:** deferred job
- **What:** During the feedback pass the user noted that the open / in-use button on the
  Stock Overview row was using `secondary` and was hard to see in Pesto dark — that fix
  landed by promoting to `primary`, but the user flagged that the broader pattern
  ("majority primary usage; not sure where secondary actually pulls weight") may need a
  separate audit. Walk the app, list every place `color="secondary"` (and other lower-used
  semantics like `info`, `accent`) appears, decide which deserve to stay vs. which should
  consolidate to `primary` or theme tokens for visual hierarchy reasons. Likely outputs:
  a short proposal under `docs/04_proposals/` + targeted fixes.
- **Why deferred:** intentionally out of scope for the feedback pass (R-007). The user
  explicitly called it out as a separate task to think about.
- **Recommended resolution:** opportunistic — fold in next time a theming/styling pass
  comes around, or after FU-046 (theme-token compliance) gets another round. **Ride-along with [FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md) Track 3** — every chunk's senior-review pass logs any `color="secondary" | info | accent"` sites worth reconsidering against this FU, so by plan close the shortlist is already assembled. Actual resolution still needs eyes-on-the-app judgement, not a code walk — so this FU stays open past plan close.

## [OPEN] FU-358 — Check / upgrade the Aldi scraper (site appears updated)
- **Raised:** 2026-06-12 (user note during Phase 1 wrap-up)
- **Type:** deferred job
- **What:** User flagged that Aldi's website appears to have
  changed; the existing Aldi scraper in the companion / merchant
  scraping module likely needs revisiting. Concrete steps when
  picked up:
  1. Hit a representative Aldi product page in a browser, compare
     the live DOM to what the scraper's selectors expect.
  2. Run the scraper against a known SKU and inspect the result
     (price, size, on-special detection) — note any fields that
     come back null / wrong / missing.
  3. Decide whether it's a selector tweak or a structural
     rewrite. Aldi historically uses a different layout from
     Coles/Woolworths, so changes there can ripple more than a
     simple class rename.
  4. If structural: cross-check the merchant scraping posture
     (`RECONCILED_FINISHING_PLAN.md` Decision 1 — scraper is the
     companion-app-only path; the core repo doesn't ship live
     scrape).
- **Why deferred:** out of scope of the current finishing-pass
  stream; needs live URLs + the companion app to investigate
  properly.
- **Recommended resolution:** opportunistic — when the user
  next needs Aldi pricing data, or as a focused session in the
  companion repo.

## [OPEN] FU-010 — Late-game holistic theme / colour / overall-look review
- **Raised:** 2026-06-05 (user request)
- **Type:** finding / deferred job
- **What:** A dedicated end-to-end pass over all themes, colours, and the overall
  visual feel of the app — viewed as a whole, in the browser, across the full
  theme set — rather than the per-chunk token work done piecemeal in A1/A1b.
- **Known input — Pesto looks over-dulled:** the user believes Pesto was dulled
  *too far*. Likely cause: the brightness tuning in A1b happened while a theme-logic
  bug was overriding the new values (the `themeService.ts` `THEMES` dict clobbering
  `themes.scss` via `setCssVar` — see the 2026-06-04 A1b round-2 worklog entry and
  the structural fix tracked in [[FU-004]]). So the dulling may have over-corrected
  against values that weren't actually rendering. Now that Pesto/Pesto Dark were
  synced, the *final* dulled value should be re-judged from scratch.
- **Also feed in:** the structural dual-source collapse ([[FU-004]]) so the review
  isn't fighting a moving target. (Note: FU-003 — the Pesto-only `--text-muted`
  42% bump — was reverted 2026-07-06; all light themes are back on the original
  50% baseline, so this holistic review starts from parity across the family.)
- **Why deferred:** look-and-feel polish is best judged late, in one sitting, on a
  near-final app — not litigated token-by-token mid-build.
- **Recommended resolution:** later — a dedicated pass during **Phase 3 (champion
  polish)** or just before **Phase 4 (commercialize)**, once the app is feature-
  complete enough to eyeball holistically. Requires the app actually running
  (deps installed) and ideally a side-by-side across all themes. **Ride-along with [FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md) Track 3** — every chunk's senior-review pass logs theme/colour anomalies against this FU so the eventual holistic pass starts with a triaged shortlist instead of a blank slate. Doesn't replace the eyes-on-app judgement pass; complements it.

