# QA run — agent 1 (2026-10-22/23)

An independent QA pass over the whole app, written for a later fixing agent. I
changed no product code. **Triage:** move each finding into `DORA_FOLLOWUPS.md`
(as `finding`, citing the ID here). Purely "look at the running app" items go to
`DORA_VERIFY.md`. I left the ledgers alone because another agent was working in
the repo at the same time.

- **Baseline:** `main` @ `26a1d6f7`, clean tree.
- **Method:**
  1. All gates run.
  2. A seeded throwaway backend (`DORA_SEED_MONEY_ON` + `DORA_SEED_QA_FIXTURES`) serving the production PWA build.
  3. A Playwright sweep of all 80 SPA routes at desktop 1366×900 and phone 390×844. Each route was checked for console errors, page errors, HTTP ≥ 400, horizontal overflow, and stray `undefined`/`NaN`/`null`/`[object Object]`/`Invalid Date` text, with a screenshot.
  4. API probes: anonymous access, garbage bodies, an unprivileged member account, and semantic flows.
  5. Five parallel static code reviews, one per surface.
- **Confirmation status:** **Live** = I reproduced it against the running server this session. **Code** = traced end-to-end in the code but not run. **Likely** = depends on timing or deployment.

## Gates

| Gate | Result |
|---|---|
| backend pytest | ✅ 2431 passed, 1 skipped, 1 xfailed (once the colliding run had cleared, see QA1-2) |
| vitest | ✅ 747 / 66 files |
| vue-tsc | ✅ clean |
| eslint | ✅ clean |
| `npm run build` (pwa) | ✅ ok |
| Route sweep, desktop | ✅ 80/80 routes, no overflow, page errors, stray tokens or unexpected HTTP errors |
| Route sweep, phone | ✅ 80/80 routes, no page-level horizontal overflow, no page errors. Two pages clip content at the edge (QA1-11) |

The suites are green. Every finding below is a gap the tests don't cover.

---

## 🔴 Critical / High — fix first

### Security

**SEC-1 · Critical · Live — Stored XSS through image endpoints. Any account can escalate to admin.**
- **Cause:** the image writers store any `data:<mime>;base64` string:
  - stores: `stores/manage_stores.py`
  - products create: `products/create_product.py`
  - user avatar: `auth/update_me.py`, `users/update_user_as_admin.py`
  - recipe image: `recipes/create_recipe.py` / `update_recipe.py`
  - weaker, but still accepts `data:image/svg+xml`: product update, recipe step images, shopping-list attachments, ingest
- The `GET …/image` routes then serve those bytes from the app origin with the stored MIME type.
- **Live repro:** `POST /api/stores {"name":"x","image":"data:text/html;base64,<script…>"}`, then `GET /api/stores/<id>/image`. The response came back `Content-Type: text/html` under the app CSP, which has `script-src 'self' 'unsafe-inline' 'unsafe-eval'`, so the script runs.
- **Escalation:** the `dora_csrf` cookie is readable by JS, so a script can PATCH `/api/users/<me> {"is_admin":true}` from an admin's browser.
- **Fix:**
  - One shared validator on write: raster allow-list (`png/jpeg/webp/gif`), no SVG, no text.
  - On serve: re-check the type, add `X-Content-Type-Options: nosniff`, `Content-Disposition: inline` and `Content-Security-Policy: sandbox; default-src 'none'`.
- **Found independently by:** three reviewers (SEC-1 / S-4 / RC-2).

**SEC-3 · High · Live — Anyone can self-register, is signed in at once, and gets full household data.**
- **Live:** an anonymous `POST /api/auth/register` returned 200 with a session. The new user could then `GET /api/stock-items` (200).
- **Where:** `features/auth/register_user.py`. The login page always offers "Register" (`LoginPage.vue:73-76`), and no install setting disables it.
- **Impact:** combined with SEC-1, any internet visitor can become admin.
- **Fix:** install-wide `registration_enabled` setting, off by default (admin-create / invite only), enforced on the server.
- **Owner call needed:** confirm that open registration isn't intended. No FU covers it.

**SEC-2 · High · Code — Password-reset links can be pointed at an attacker's host through the `Origin` header.**
- **Cause:** `infrastructure/auth_helpers.py:262-266` (`public_base_url()`) falls back to the request's `Origin` when `AppSetting.public_url` is empty, which is the default.
- **Repro:** `forgot-password` with `Origin: https://evil.tld`. The real reset token is mailed inside an evil.tld link.
- **Also affected:** verify-email and register links.
- **Fix:** never build these links from request headers. Require `public_url` / `DORA_PUBLIC_URL` in production, and refuse to send without it.

**SEC-4 · High · Code — Changing or resetting a password does not end other sessions.**
- **Cause:** the `pwd_v` staleness check exists only in `auth/get_me.py:58-66`. Neither `middleware.py:233` nor `require_admin` (`admin_gate.py`) checks it.
- **Impact:** an old or stolen cookie keeps working on every route except `/auth/me`, including admin routes. Sessions for deleted users stay valid on non-admin routes. Cookies are client-side, last 31 days and refresh on every request.
- **Fix:** one `current_user()` resolver in middleware that checks the user exists, `is_active` and `pwd_v`. Consider a session generation counter.
- **Related:** broader than FU-654/FU-655, which cover deactivation only.

**SEC-11 · High · Code — DOM XSS from recipe names.**
- **Where:** `pages/StockItemDetailPage.vue:2565-2577`.
- **Cause:** when deleting a stock item is blocked, the blocking recipe names are joined into `<li>${r.name}</li>` and shown with `$q.dialog({ html: true })`, unescaped.
- **Repro:** name a recipe `<img src=x onerror=…>` (or import one), link it to item X, then try to delete X.
- **Same pattern, Low:** `AdminDataImport.vue:559` with spreadsheet sheet names.
- **Fix:** escape the names, or don't use `html: true`.
- **Found independently by:** two reviewers (SEC-11 / S-1).

### Data integrity

**QA1-5 · High · Live — Re-finishing a finished list puts its items back to Stocked.**
- **Where:** `shopping_lists/manage_shopping_list.py` `FinishShoppingListHandler.handle` never checks the list's status.
- **Live repro:** finish a list, set its ticked item to Out of Stock, then `POST …/finish` again. The response is 200 and the item is back to **Stocked**. `completed_at` and the snapshots are rewritten too.
- **Fix:** return 409 when the list is already done.

**SL-3 / SL-8 · High · Live — A finished list (a receipt) can be wiped, added to, or silently reopened.**
- **Live:**
  - `POST …/clear` on a done list returned 200 and deleted all of its lines, taking that period's budget spend with it.
  - `POST …/lines` on a done list returned 200.
  - `PATCH {status:"draft"}` on a done list returned 204, reopened it and cleared `completed_at`. `/start` and `/back-to-draft` both refuse this.
- **UI:** "Clear all items" is shown on the receipt face (`ShoppingListDetail.vue:684-691`).
- **Fix:**
  - Status guards in `list_actions.py` (`ClearListHandler`, `discard-unticked`), `AddLine`/`bulk-add`, and `UpdateShoppingList`.
  - Hide the danger footer on done lists.

**MP-1 · High · Code — Applying a meal-plan template doesn't refresh the planner, and the next edit undoes the template.**
- **Where:** `composables/useMealPlanner.ts:951-1004`. `refreshAfterMutation` reloads ingredients and recipes only.
- **Effect:**
  - On a planned week, the next add or remove sends a PATCH built from the stale entries, and the server drops the template's entries.
  - On an empty week, the next add creates a **second plan for the same Monday**.
- **Fix:** call `mealPlanStore.getMealPlansAsync()` after apply and after recurring apply.

**MP-4 / MP-5 · High · Code — Applying a template deletes unreconciled past meals; a deleted template in a set wipes weeks.**
- **MP-4:** `meal_plan_templates/manage_templates.py:412-414` keeps only *consumed* entries, so unreconciled past meals and their receipts are cascade-deleted. FU-595 fixed this on the update path, not this one.
- **MP-5:** set items reference `template_id` with no FK, and deleting a template doesn't clean up its sets. A recurring apply then writes `[]` over each affected week, and still reports success.
- **Fix:** keep `consumed_at is not None or scheduled_for < today` entries. Skip or reject missing templates, and remove set items when a template is deleted.

**MP-2 · High · Code — A Lighter/budget swap on one day of a linked cook batch leaves the week unsaveable.**
- **Where:** `meal_plans/swap_suggestions.py:587-686`. The swap ignores `cook_batch_id`.
- **Effect:** once one day is swapped, every later edit to that week fails `validate_cook_groups` ("A cook batch must use a single recipe", 400).
- **Fix:** exclude batched entries from swaps, or swap the whole batch.

**S-2 · High · Code — Stocktake "That's right" records the opposite of what the user confirmed.**
- **Where:** `components/stocktake/StocktakeReviewPhase.vue`, `pages/StocktakeRunner.vue:onReviewConfirm`, `stocktake.py:bulk_check`.
- **Cause:** a pre-ticked row reads "Dora thinks **Low** · currently **Stocked**". Confirming it only stamps `last_checked_at`, which then makes the *recorded* level (Stocked) authoritative at high confidence.
- **Fix:** write the believed level for ticked rows that disagree, or don't pre-tick disagreeing rows.

**S-3 · High · Code — The stock overview is stale after a stocktake.**
- **Cause:** `StocktakeRunner.vue` mutates through a raw `StockItemApiService` and never touches `stockItemStore`. `StockOverview` only calls `ensureLoadedAsync()`, which is a no-op once loaded.
- **Effect:** old levels show, and swept-away (deleted) items stay listed and 404 when opened. Recipe cookable counts go stale (no `invalidateRecipes`). The `auto_added` PATCH response is dropped, so there's no "added to list" toast.
- **Fix:** route the runner's writes through the store, or force a reload plus invalidation at the end of the run.

**RC-1 · High · Code (the parser was run directly) — The recipe text parser reads an ingredient's first letter as its unit.**
- **Where:** `recipes/_parse_recipe_from_text.py:56-75`. The unit alternation has no word boundary.
- **Examples:**
  - `"2 garlic cloves"` → `2 g "arlic cloves"`
  - `"1 large onion"` → `1 l "arge onion"`
  - `"2 lbs beef"` → `l "bs beef"`
  - `"½ cup sugar"` → no quantity (Unicode fractions aren't parsed)
- **Effect:** wrong quantities and units flow into cost, nutrition, shopping and cook-mode scaling.
- **Fix:** `(?![a-z])` after the unit group; put `lbs` before `lb`/`l`; normalise fraction glyphs first.

**SH-1 · High · Code — When a session expires, the user is never sent to the login page.**
- **Where:** `stores/authStore.ts:161-169` and `services/api/axiosHttpClient.ts:255-258`. Both comments say "route to login", but nothing does it.
- **Effect:** the header controls vanish, every card shows "couldn't load", and every save fails with 401, until the user navigates.
- **Fix:** `router.replace({ path: '/login', query: { redirect } })` in `handleSessionExpired`.

**SH-2 / S-5 · High · Code — The optimistic stock-level rollback registry is global and unsafe.**
- **Where:** `stores/stockItemStore.ts:117-145`.
- **Problems:**
  - Any success clears *every* in-flight rollback.
  - When a caller catches the error itself, the optimistic level stays on screen and its rollback stays queued. It then fires on the next *unrelated* error.
  - Rows are written back by an index captured before the `await`, so a reorder or reload hits the wrong row.
- **Repro:** go offline, then "Mark restocked". The toast says "Could not restock", yet the row shows Stocked.
- **Other affected paths:** cook mode's `Promise.allSettled` finish, buy-verdict actions, scan-to-level.
- **Fix:** per-call rollback in the store's own `catch`, rethrow, and look rows up by id after each await.
- **Related:** FU-889.

---

## 🟠 Medium

### Security / auth
- **SEC-5 · Code:** `PATCH /auth/me` changes the email with no current password and marks it **verified** (`auth/update_me.py:130-148`). With SEC-1/SEC-4 this is a durable account takeover. FU-620 records it as an owner trade-off, but `AUTH_ASSISTANT_SECURITY_FINDINGS.md` A.2 and `SECURITY_REVIEW.md` §1 still say "fixed". At minimum require `current_password` and don't auto-verify.
- **SEC-6 · Code:** rate limits key on `remote_addr` and there is no `ProxyFix`. Behind a TLS proxy every client shares one bucket, so 5 junk logins a minute lock everyone out, and audit `actor_ip` is always the proxy.
- **SEC-7 · Live:** there is no `MAX_CONTENT_LENGTH`. Anonymous `POST /api/client-logs` accepted a 100 KB `context` (204) and writes it into the admin audit log, so anyone can forge audit rows and grow the DB.
- **SEC-8 · Likely:** first-admin bootstrap is gated only by a guessable `ADMIN_BOOTSTRAP_EMAIL`, and the count-then-insert isn't atomic. Use a one-time setup token.
- **SEC-9 · Code (demo deployments):** the demo login `demo/demo` is an **admin** (`seed_showcase.py:156-162`). That exposes `piper_bin` (an executable path), backup paths, SMTP and the probe SSRF to the public.
- **SEC-10 · Likely (Postgres):** `X-Request-Id` is copied verbatim into `AuditEvent.request_id` (String 64). A long header makes every audit write fail silently.
- **QA1-1 / SEC-15 · Live:** unauthenticated `GET /api/health` returns the household budget (`{amount: 220, period: weekly}`), the headcount, the full feature map, and whether SMTP, VAPID and encryption are configured. Split it into a public liveness payload and an authenticated config payload.

### Functional
- **AD-1 · Live:** `PATCH /api/app-settings {"nutrition_mode":"bogus"}` returns **500**. `update_app_settings.py:174` returns a tuple where a response object is expected, and line 463 then raises AttributeError.
- **AD-2 · Code:** admin email edits aren't normalised, format-checked or uniqueness-checked (`users/update_user_as_admin.py:96`), and there's no DB unique constraint. A mixed-case email is never found by forgot-password.
- **AD-3 · Code:** the last-admin delete guard counts *deactivated* admins (`delete_user_as_admin.py:64`), so the only active admin can be deleted.
- **S-9 · Live:** `POST /stock-items/<B>/products` with a product already linked to item A returns **500** (an IntegrityError on `UNIQUE(product_id)`). Return a 422 "already linked to …", or move the link.
- **RC-3 · Live:** `PATCH /recipes/<id> {"servings": -2}` is accepted (204). Create has `ge=1`, but update has no bounds on servings or times, and ingredient `quantity` has no `ge=0`. Negative servings make shopping quantities and costs negative.
- **RC-4 · Code:** clearing an ingredient's quantity box sends `quantity: ""`, which fails the *whole* recipe save.
- **RC-5 · Code:** saving in freeform or image step mode re-creates the ingredients and sections. The stored structured steps silently lose every ingredient link and their section.
- **RC-6 · Code:** recipe edits are thrown away with no prompt when moving between versions (`/cookbook/a` → `/cookbook/b`), because there's no `onBeforeRouteUpdate`.
- **RC-7 / RC-8 · Code (cook mode):**
  - The global keydown handler ignores open dialogs. Space re-opens Finish and wipes the level picks; Esc in the Finish dialog exits without finishing.
  - `confirmFinish` hides failed stock updates behind "Enjoy your meal".
  - A failed `cookAsync` call isn't caught at all.
  - Two ingredients on the same stock item give duplicate keys and racing PATCHes.
- **RC-9 · Code:** "Per serving" kcal shows whole-recipe kcal when no servings are set (the page re-derives the figure instead of using `kcal_per_serving`).
- **RC-10 · Code:** `/api/tts` has no input validation. `pitch_semitones: "inf"` loops forever (hang / out of memory), large values give a 500, and text length is unbounded.
- **RC-11 · Code:** recipe import fuzzy-links on the whole line, case-sensitively. "1 onion" stays unlinked, while "1 tsp onion powder" links to Onion.
- **RC-12 · Code:** a degraded import loses the pasted text even though the toast says it's in Instructions. A duplicate name shows the raw "Request failed with status code 422". New-version names can collide or pass 255 characters.
- **MP-6 · Code:** "Apply recurring" overwrites up to 26 weeks without the confirmation that single-week apply shows.
- **MP-7 · Code:** reconcile queue and log pagination uses a date-only cursor, so rows are skipped whenever a page ends mid-day, which is the normal case with 2–3 slots a day. Use a `(scheduled_for, id)` cursor.
- **MP-8 · Code:** the meal-plan ingredient aggregate adds quantities across units, so 200 g + 1 cup gives "201 g".
- **MP-9 · Likely:** past, unconsumed entries still count as forward demand (need-to-buy, costs, auto-generated list).
- **MP-10 · Code:** "Clear this week" DELETEs the whole plan, including cooked history and receipts. The history-keeping PATCH clear exists but isn't used.
- **MP-11 · Likely:** planner edits are full-list PATCHes with no in-flight guard. Two quick edits lose one; two quick adds on an empty week create duplicate plans. `MealPlan.start_date` has no unique constraint and no Monday check.
- **MP-3 / S-8 · Code (FU-668 class):**
  - The planner fetches only the first 50 meal plans, in uuid order, so random weeks vanish past about 50.
  - `productStore` fetches only the first 50 products, so My Products and the Price History picker hide the rest without saying so.
  - FU-668 doesn't list products. Add it.
- **SL-1 · Code:** budget periods compare `completed_at` against UTC midnight and UTC dates, not the household zone (R-021). In Sydney, a Monday-morning shop is billed to the previous week.
- **SL-2 · Code:** a receipt's "spent" uses the picked offer's *current* price as a fallback, so it differs from the budget's figure and drifts over time (R-003).
- **SL-4 · Code:** move-to-list de-duplicates on `stock_item_id` only. Product-only lines (`None`) all count as duplicates, so they're stranded on the archived list after "move leftovers".
- **SL-5 · Code:** "Save as template" returns a 500 (IntegrityError) when the list has a product-only or orphaned line, because the template line's `stock_item_id` is NOT NULL.
- **SL-6 · Likely:** list detail loads don't drop stale responses. Switching lists mid-refresh can paint list A on B's route, and rapid ticks flicker.
- **SL-7 · Likely:** trim-to-budget leaves ticked lines and other active lists out of the headroom, so it under-trims mid-shop.
- **S-6 · Code:** price-history rows mean different things depending on the writer:
  - ingest appends the *new* price;
  - a manual product create writes nothing;
  - `PATCH` archives the *old* price.
  - **Effects:** empty charts for custom products, a duplicated latest point, and an all-time low that ignores the current price.
- **S-7 · Code:** My Products bulk delete/inactivate stops at the first failure and doesn't refresh, so deleted rows stay selected and the retry 404s.
- **AL-1 · Code:** `send_alerts_push.py:152-175` stamps `last_pushed_at` even when every device failed, so a transient failure means the alert is never pushed.
- **DB-1 · Code:** Kitchen-health Freshness counts items expiring *today* as expired (`<=`), and uses the UTC date. The bell says "Expires today" at the same moment.
- **DB-2 · Code:** "What's coming" orders a day's meals by slot *name* (Dessert before Dinner and Lunch) (`alerts/get_upcoming.py:136`). The owner reported this exact bug, and it was fixed only for Next-to-cook.
- **DB-3 · Code:** a failed Kitchen-health fetch renders the "will appear once you've been using Dora" empty state, a failure shown as empty (FU-840 / D-007 pattern).
- **RP-1 · Likely:** the Reports range picker has no stale-response guard, so a slow 5-year response can overwrite a later 30-day one.

---

## 🟡 Low

- **QA1-2 · tooling · Live:** backend pytest hard-codes `data/dora.test.db` (`tests/e2e/dora_api/conftest.py:21-22`), so two concurrent runs corrupt each other. Seen this session: `index … already exists` at setup.
- **QA1-3 · tooling · Live:** two `web_app/e2e/serve.py` instances can bind the same port on Windows (Werkzeug sets `SO_REUSEADDR`), and requests then split between two DBs. Fail loudly if the port is taken.
- **QA1-4 · hygiene · Live:** the empty `vtsc-errors.txt` and `test-results/.last-run.json` are committed. `git rm` both and ignore `test-results/`.
- **QA1-7 · Live (screenshot):** three different "not found" treatments for a deleted or old link:
  - `/stock/<bad>`: "Could not load this stock item." (a 404 shown as a load failure).
  - `/cookbook/<bad>`: a raw "Recipe with the ID '0000…' was not found. · ref: …" with no heading or back link.
  - `/shopping-lists/<bad>`: a red banner with the raw entity ID *and* a "Couldn't open this list" empty state; "Retry" is pointless on a 404, and Add item / Print / Save as template stay enabled.

  Use one shared not-found state. The stock detail page also fires a `buy-verdict` request for the missing item.
- **QA1-8 · Live (screenshot + code):** the Reports date range ignores the household locale. `ReportsPage.vue:369` is the only `toLocaleDateString(undefined, …)` in the SPA, so an en-AU install shows "Sep 22, 2026 – Oct 22, 2026". Use `formatLocaleDate`, as the other pages do.
- **QA1-9 · Live (screenshot):** scaled quantities in cook mode keep the stored plural unit, so you see "1 sticks Celery", "1 cloves Garlic", "⅓ whole Carrots". `displayQuantity` → `formatQuantity` (`RecipeCookMode.vue:924`, `helpers/formatQuantity.ts`) never singularises the unit.
- **QA1-10 · Live (screenshot):** the recipe detail page shows an empty "Nothing in this section yet." block above the first named section when every ingredient is in a section (Sunday Ragu).
- **QA1-11 · Live (phone screenshots, 390 px):** two rows run off the right edge with no fade or chevron to show they scroll:
  - The Stock toolbar: Bulk select, Log price and Export are hidden or cut in half.
  - The recipe facts row: "DIFFICULTY / Mec…" is clipped, and When and Per serving can't be seen.

  The settings chip rails and the stock-detail tabs also scroll off-screen, but read as deliberate rails. Add an overflow affordance, or wrap these two rows / move the extra actions into a menu.
- **QA1-12 · Live:** a second meal plan for the same `start_date` is accepted (`POST /api/meal-plans`, 201). This is the server half of MP-3/MP-11's duplicate-week risk. Add a unique `start_date` (or upsert) and a Monday check.
- **QA1-13 · Live:** `POST /api/meal-plans/auto-build {"emphasis":"bogus"}` returns 200 and silently uses the default. Validate the enum.
- **QA1-14 · Live:** a shopping-line `quantity` of 10⁹ is accepted, because there's no upper bound (`manage_shopping_list_lines.py:55,239`). `meals_cooked` already caps at 999 "against fat-fingers"; mirror that here.
- **QA1-15 · Live:** `POST /recipes/<id>/cook {"meals_cooked":0}` returns 204 (`ge=0`). Check whether a zero-meal cook writes a "cooked" event that feeds Kitchen memory or Last cooked. If it does, require `ge=1`.
- **QA1-16 · Live (already tracked, FU-575):** whitespace-only recipe names are created (201). Still open.
- **QA1-17 · Live, minor:** admin routes validate the body *before* the admin check, so a member gets 400 with the full schema instead of 403. Validated against real admin routes: the gates themselves hold (users, app-settings, audit, backups, import, ingestion sources). Put the admin check first.
- **QA1-6 · question:** shopping-list line quantity is a whole number only (`int, ge=1`), so "1.5" isn't possible. Confirm this is intended.
- **S-10:** a single-item move to Unassigned doesn't persist (`move_stock_item.py:46`; the `noload` relationship needs `_stock_location_id = None`).
- **S-11:** stores, stock groups and locations accept whitespace-only names (min-length is checked before `strip`). Legacy `/stock-locations` and `create_product` have no `max_length`, so long names 500 on Postgres.
- **S-12:** re-adding a custom product with the same name and store silently discards the new brand, size, image and pack count, but the toast still says "added".
- **S-13:** Price History has no stale-response guard and double-fetches on mount.
- **S-14:** "Could not log any as wasted" appears when only the refresh failed, and there's no Undo. `bulkMove` ignores `missing_ids`.
- **S-15:** `GET /api/stock-items` 500s for the *whole list* if any item has a NULL level (`get_stock_items.py:72`).
- **S-16:** an area or section location can be re-parented to the root via `parent_id: null`.
- **S-17:** `withBusyReload` on the stock detail page swallows server 4xx messages behind the generic "oopsie" toast and trips the rollback registry.
- **RC-13 / RC-14:** after vocab changes in Settings, or after an unlinked-ingredient bulk link, the recipe pickers and the cookbook stay stale until a reload.
- **RC-15:** recipe collections have no management UI, so the Collection picker is a dead control on a fresh install.
- **RC-16 / RC-17 / RC-18 / RC-19 (cook mode):**
  - A finished timer can be restarted at 0, ticks to −1 and fires again.
  - "1 hour 30 minutes" gives a 30-minute timer.
  - `"1.5 litres…"` is split into "5 litres…".
  - The ingredient highlight matches substrings ("oil" in "boil").
- **RC-20:** duplicate step `client_id`s give a 500 instead of a 400.
- **RC-21:** a failed favourite toggle gives no feedback.
- **MP-12 / MP-13 / MP-14:**
  - Future entries can be reconciled through the API.
  - The reconcile receipt id is stored as TEXT on SQLite.
  - Duplicating a week or applying a template drops `cook_fresh` and batch links.
- **SH-3:** `AlertsBell` registers its interval after an await, so it can leak a 60-second poller per login.
- **AL-2:** push stale-flag cleanup nulls the daily brief's dedup ledger rows.
- **DB-4 (owner call):** waste scores 100 with zero events, so a brand-new install shows "Kitchen health 100" and the "not enough data yet" state can never render. The test name says None, but the test asserts 100.
- **RP-2:** `StockValueOverTimeHandler` reads `noload` relationships (R-032). The endpoint has no SPA caller now, so fix it or delete it.
- **RP-3:** savings with `range=all` can 500 on legacy NULL `completed_at` (naive and aware datetimes compared).
- **RP-4:** a ticked line with quantity 0 is counted three different ways across spend-by-store, by-category and usage-stats (R-003).
- **RP-5:** if the range-window call fails, the waste card silently shows a full year.
- **SEC-12 / SEC-13 / SEC-14 / SEC-16:**
  - SEC-12: `upload_id` isn't validated in `staged_path()` (admin-only path traversal to `*.bin`).
  - SEC-13: push endpoints and LLM base URLs aren't scheme-limited (`file://` reaches urllib).
  - SEC-14: `Product.web_url` allows `javascript:`.
  - SEC-16: login timing reveals which usernames exist; there's no rate limit on change-password guesses; the CSRF cookie is never rotated; the USDA key is stored and backed up in plaintext; CSV exports have no formula-injection guard.
- **Minor:**
  - The Help changelog error has an empty reason on a 5xx.
  - The PWA install button stays after an error.
  - The 7-day windows are 8 days inclusive.
  - An empty shopping list still enables "Shop" and "Clear all items".

---

## API robustness probe (live) — mostly clean
The probe sent about 2,400 requests. Every mutating route got 8 kinds of bad body: none, malformed JSON, `[]`, `{}`, empty name, 5000-character name, nulls and negatives, and wrong types/dates. On top of that, random-UUID ids on every parameterised route, and 14 abusive query strings on every list or report GET.
- **No 5xx anywhere** in that probe. AD-1 and S-9 only fail with *valid-but-wrong* input, which the targeted repros above caught.
- **Anonymous access:** only `/auth/bootstrap-required`, `/auth/capabilities` and `/health` answer without a session. `/health` is the problem (QA1-1).
- **CSRF:** an authenticated POST with no `X-CSRF-Token` returns 403, as it should.
- **Minor:** `DELETE /api/waste/events/<unknown>` and `DELETE /api/alerts/<unknown>/suppression` return 204, while other DELETEs return 404 for unknown ids. Pick one convention.
- **Side observation, supports SEC-6:** while probing, failed logins for a *nonexistent* user plus my own successful logins tripped the shared 5-per-minute login limit and locked out the real `dora` login from the same IP for a minute. Behind a reverse proxy, that would lock out the whole household.

## Checked and found fine (so nobody re-checks them)
- **Auth plumbing:**
  - The 401 interceptor doesn't loop.
  - The login `?redirect=` isn't an open redirect.
  - Bootstrap returns 410 once a user exists.
  - Reset tokens are single-use, with a 1-hour expiry.
  - Ingest bearer keys are hashed and compared in constant time.
  - The `DORA_CSRF_DISABLED` and `DORA_ALLOW_DESTRUCTIVE` switches are refused in production.
- **Injection / unsafe code:** SPA static serving is traversal-safe; no `v-html`; Jinja autoescape is on; no SQL is built with string formatting; no pickle, yaml or eval.
- **Formatting and maths:**
  - Money and date formatters handle NaN, null and negative values.
  - Divide-by-zero guards exist in YoY, price drops, your-prices and deal-quality.
  - Stock-item duplicate names are checked case-insensitively.
  - Price observations require `gt=0` and a unit dimension check.
- **Shopping / meal plans:**
  - Shopping-list finish doesn't duplicate price observations.
  - The week-date helpers and the period year rollover are correct.
  - The shopping-list DTOs match the TS models.
  - v-for keys on the reviewed pages are fine.
- **Empty state:** a fresh empty install renders the dashboard, restock radar, use-it-up and usage stats without crashing.

## Harnesses (throwaway; agent-1 session scratchpad on the owner's box)
- `sweep.mjs`: the route sweep.
- `confirm.py`, `confirm2.py`: the live repros above.
- `api_probe.py`, `member_probe.py`, `flows.py`: the broader probes (results below).

**To boot the backend:** `web_app/e2e/serve.py` with `DORA_DEBUG=true DORA_ALLOW_DESTRUCTIVE=true DORA_SEED_MONEY_ON=true DORA_SEED_QA_FIXTURES=true`, a throwaway `DORA_DB_PATH`, a *copied* `DORA_SPA_DIR`, and an unusual port (QA1-3). Then pass `http://127.0.0.1:<port>` to each script.
