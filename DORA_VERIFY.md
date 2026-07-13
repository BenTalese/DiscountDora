# Dora Verification Checklist

The QA pile — anything that needs eyes on the running thing to confirm.
Browser observations, boot-time / operator smoke checks, container startup,
migration round-trips, CLI/desktop launch checks — whatever needs manual
verification lives here. Grouped by surface; pick one and walk it
top-to-bottom.

---

## Onboarding story pass (2026-07-12)
- [ ] Launch onboarding as a fresh install → scene 1 (problem) renders and **does not auto-advance**; sitting on it 10+ seconds waits for you.
- [ ] Click Next → scene 2 (loop) draws in ring + nodes, then Dora at centre; the "What you're here for" persona-chip bar **does not appear anywhere** below the loop.
- [ ] Tap Dora in the centre → detail panel reads the new stronger sell ("expiry, stock, spend and habits, hinting at what you can cook now, and answering when you ask"). Tap each stage (Stock / Plan / List / Shop / Restock / Cook) → each renders its own sell line.
- [ ] Confirm scene 2 has **no** headline sub — the second "Tap any stage — or Dora in the middle" hint below the loop is gone; only the one hint under the ring remains.
- [ ] Next → scene 3 (brain) does not auto-advance; Next → scene 4 (control).
- [ ] Scene 4 shows the tune icon plus a stylised **switch panel** with four rows (AI assistant, Spend tracking, Voice replies, Barcode scanning); switches show mixed on/off states. Headline reads "every part of Dora is a toggle." Copy no longer mentions Cooking / Spend / Everything.
- [ ] Skip button (top-right) reads **"Skip onboarding"** on every scene (not just "Skip"); clicking it skips the whole wizard as before.
- [ ] Refresh mid-story → draft resumes at the same scene; no console errors about a missing `personaPreview` field on the persisted draft (old drafts should hydrate cleanly and just ignore that key).
- [ ] Reduced-motion OS setting → the ring/nodes still appear in their final state without motion (no regression from removing autoplay).

## Dora assistant / helper bubble (FU-429 + FU-360)
- [ ] **Basic-mode add-to-list (FU-429).** With AI mode OFF (no LLM configured), open Dora and type **"add milk"** → she resolves it against your pantry and confirms "Added Milk to your list. 🛒" with an "Open shopping lists" button; the item is actually on your primary list.
- [ ] Type **"add eggs and bread"** → both added in one go (comma / "and" / "&" all split); reply names both.
- [ ] Type **"buy <something not in your pantry>"** → reply says it couldn't find it and points at the Stock page; nothing spurious added.
- [ ] Type an item whose name matches **two** pantry items → reply says it matched more than one and asks you to pick the exact one in Stock; it does **not** guess/add either.
- [ ] With **no primary list set** → "add milk" replies that you need to pick a primary list first, with an "Open shopping lists" button; nothing added.
- [ ] Bare **"add to my list"** (no item) → Dora asks what to add rather than erroring.
- [ ] AI mode ON → "add milk" still uses the richer LLM propose→confirm flow (unchanged), not the Basic path.
- [ ] **Hide Dora (FU-360.6).** Settings → Assistant → toggle **"Show Dora on every page"** OFF → save toast "Dora helper hidden." → the floating bubble disappears from every page immediately; reload confirms it stays gone. Toggle back ON → bubble returns.
- [ ] **Greeting once-per-user (FU-360.5).** Fresh browser, log in as user A → the "Hi! I'm Dora" hint appears once; dismiss it → it doesn't return for A across reloads/logins. Log in as a *different* user B in the same browser → B sees the hint once (proving it's per-user, not per-browser).
- [ ] **Mode slider (FU-360.3).** With AI mode configured (Settings → Assistant: provider + model + base URL/api key saved, install master ON), open Dora → the chat header shows a two-position pill "Basic | AI" with a skewed thick knob glowing on the active side. Tap the inactive side → knob slides across with the glow, PATCH `/auth/me` fires, and `/assistant/status` re-probes; the "AI mode unavailable" banner appears if the LLM isn't currently reachable. Tap back → returns to Basic. Slider grows with the text-size preference (rem-based).
- [ ] **Mode slider — disabled states (FU-360.3).** With **no LLM configured** (fresh user) → slider renders dimmed, cursor `not-allowed`, tooltip explains what to save in Settings → Assistant first; tapping does nothing. With **install master OFF** (Admin → System → AI assistant) → slider dimmed with tooltip "AI mode is disabled install-wide…"; tapping does nothing.
- [ ] **FU-360.1 (text size honoured).** Set a large text size in Preferences → open Dora → the chat message text scales up with it (appears already fixed by the A6 rem migration — this is a confirm, not a known bug).
- [ ] **FU-360.4 (DS4 hover-flash regression) — fix landed 2026-07-12.** Hover the launcher / mascot repeatedly, and specifically *hover off* → mascot should stay put, no disappear-and-animate-back-in. Cause: the one-shot `dora-entrance` keyframes lived on the base `.dora-bubble-launcher-inner` rule, so when the hover-bob animation stopped and the base declaration reasserted, `dora-entrance` (with 300ms delay + `both` fill) restarted from its `scale(0) opacity: 0` frame. Moved onto a `.is-entering` modifier removed via `@animationend` after the entrance plays.
- [ ] **FU-386 (cookable chip).** Open Dora on the Dashboard or Cookbook → tap the **"Cookable now"** / "Find a recipe to cook" chip → lands on the cookbook filtered to cookable recipes (the `?cookable=true` contract, confirmed live end-to-end).
- [ ] **FU-515 B.3 (tool-arg bound, AI mode only).** With AI mode on, ask Dora to **"push the milk expiry by 99999 days"** → she declines with a "more than ~10 years — give me a sensible number" style message rather than proposing an absurd date. (Sanity check on the boundary cap; normal pushes like "+3 days" still work.)

## Currency & locale (FU-043) — origin FU-043
- [ ] Settings → Admin → System → **Currency & locale** loads; two inputs (Currency 3-letter, Locale BCP-47), a live preview showing `$12.50 · $1,234.56` (or whatever the current setting renders), and a "Use this device" button beside the preview
- [ ] Change currency to `USD` → blur (or Enter) → toast "Currency set to USD."; Dashboard budget / Deals / ReportsPage / ShoppingList totals / StockItem prices / RecipeDetail cost card all re-render with `US$` (or `$` depending on the locale's convention) without a hard reload
- [ ] Change currency to `EUR` and locale to `de-DE` → money renders as `1.234,56 €` (comma decimal, dot thousands, symbol suffix) everywhere; MoneySettings budget input prefix flips to `€`; PriceEntry dialog's price input prefix flips to `€`
- [ ] Change locale to `en-GB` → symbol renders as `£` (currency stayed as previously set) — verifying that locale and currency are independent knobs
- [ ] Enter invalid inputs: `US` (2 chars), `USDD` (4 chars), `US1` (digits), lowercase `usd` (should upper-case-in on blur and succeed); invalid locale `en_AU` (underscore), `english` (not a tag), space `en AU` — each shows inline red error message, no toast, no server round-trip
- [ ] Reset to `AUD` + `en-AU` → money renders `$12.50` again (Australian dollar sign, comma thousands, dot decimal)
- [ ] Dora chat / Cook mode: hold-to-talk mic uses the household locale for speech recognition (verify by switching locale to `en-GB` or `de-DE` on a device where speech-recog supports it, then hitting the mic — the recognised text shape follows the locale)
- [ ] Assistant chat: ask "what can Dora do?" → the answer no longer name-drops "Coles, Woolworths, IGA, Aldi" — it says "the household's configured merchants" or similar
- [ ] Fresh install (or new admin session) sees the AU defaults (`AUD` + `en-AU`) with no explicit save required — existing installs unchanged post-migration

## Native Android build (P8-10) — origin P8-10
- [ ] `web_app/src-capacitor/android/` opens cleanly in Android Studio (File → Open → point at the folder); Gradle sync completes with no errors
- [ ] `./gradlew assembleDebug` from `src-capacitor/android/` produces `app/build/outputs/apk/debug/app-debug.apk` (after `npx quasar build -m capacitor -T android` has synced the SPA into `assets/public/`)
- [ ] APK installs on a real Pixel / Samsung device (or Android Studio emulator) — icon shows the Dora mascot on the yellow (#f5c462) adaptive background; app name reads **Dashy Dora**
- [ ] First launch opens `/setup/backend` (before any login prompt); entering the LAN URL of a running Dora backend (e.g. `http://192.168.x.x:5170`) → toast "Connected. Welcome to Dora!" → app navigates to `/` and the normal login flow appears
- [ ] Second launch (kill + reopen) skips the setup gate — the persisted URL is remembered
- [ ] Settings → About → **Dora API endpoint** shows the saved URL; **Change** button opens the URL prompt; saving a different URL triggers a full reload and hits the new backend
- [ ] Barcode scan (Stock Overview → Scan) triggers Android's Camera permission prompt; scanning a real EAN populates the Add-a-stock-item flow
- [ ] Open a recipe → **Cook mode** → screen stays awake through the whole session (no auto-lock) even with no touch input for 2+ min
- [ ] Open a shopping list → **Start shopping** → screen stays awake for the shop session; leaving shop mode (Finish & restock, or navigating away) releases the lock and the screen dims normally
- [ ] Settings → Notifications → Push toggle reads as **Unsupported** on the native app (no browser Push API in the WebView); PWA-install path still exposes push
- [ ] iOS platform folder (`src-capacitor/ios/`) exists but is deliberately unbuilt on this Linux dev box — verify only that the folder is present + committed; the actual Xcode build is a future prompt

## StoresSettings logo upload — origin FU-335
- [ ] Settings → Stores → **Add store** → the dialog's logo row now shows two buttons (`Add logo (camera)` + `Add logo (file)`) instead of the old drag-drop file input; the `StoreLogo` swatch preview above remains
- [ ] Pick a real PNG / JPEG / WebP from the file browser → preview updates immediately; typing a name + Save creates the store with the logo
- [ ] Retry with an unsupported file (e.g. a PDF) → a red inline caption appears under the picker with a friendly message; no `q-notify` toast, no crash
- [ ] Edit an existing store with a logo → the two buttons now read `Change logo (camera)` + `Change logo (file)`; the "Remove existing logo" button still shows and clears the image
- [ ] After Remove is tapped and a new image picked, the buttons flip back to "Change" labels (the draft has a fresh image)
- [ ] On mobile (or with `forceCamera` on): the camera button opens the OS camera picker directly

## BuyVerdictCard one-tap actions — origin FU-454
- [ ] Find a stock item whose card verdict returns kind `mark_stocked` ("Already stocked" — e.g. an item with waste history that got set back to Well-Stocked accidentally, or engineered by dropping the level from Well-Stocked to Low with waste events present) → tap the button on both Stock Overview AND Stock Item Detail → item flips to Well-Stocked, positive toast fires, verdict card re-renders with the fresh answer
- [ ] Same on Shopping List Detail line card → tap `mark_stocked` → item flips to Well-Stocked; the shopping-list line stays put (line-level removal is a separate action)
- [ ] Find an item whose card verdict returns kind `remove_from_list` ("Remove from list" — item is skip-recommended AND is currently on an open list) → tap on Stock Overview → summary toast reports "Removed from N list" ; verdict card no longer surfaces the button; the line is gone from every open list containing it
- [ ] Same on Stock Item Detail → same behaviour
- [ ] On Shopping List Detail, `remove_from_list` removes ONLY the current line (not other lists — that's the correct per-line semantic)
- [ ] Confirm no "use the row controls" or "use the stock-level control" fallback toasts fire from the card any more — those were the dead-button symptom

## Password policy (NIST/ISO alignment) — origin FU-442
- [ ] Register a new user with password `abcdefgh` (8 chars, letters only) → succeeds (no more "must include a digit")
- [ ] Register with `passphrase please` (a real phrase with a space) → succeeds
- [ ] Register with `abc123` (6 chars) → rejected with "at least 8 characters"
- [ ] Register with `password123` → rejected with the "appears on public breach lists" message; try `QWERTY123` (uppercase) → same rejection (case-insensitive breach check)
- [ ] Reset-password flow shows the updated fineprint ("at least 8 characters, a passphrase works well"); no "letter and digit" language anywhere
- [ ] Settings → Account → Change password inline validator says "At least 8 characters" (not 4)
- [ ] Log in with an existing pre-policy password (e.g. an old 6-char account) still works — the new policy only applies at set-time, not at login
- [ ] No admin toggle exists to loosen the rules (grep the Settings tree in the browser — Preferences, Admin, Security should have no password-policy option)

## PWA install + offline (build now ships in PWA mode) — origin FU-336
Requires a **built** frontend served over HTTPS or localhost (SW won't register on plain-HTTP). Use the Docker/nginx image, the desktop bundle, or `quasar serve dist/spa` after `npm run build`.
- [ ] DevTools → Application → **Service Workers**: `sw.js` registers + activates (no errors); Application → **Manifest** shows name "Dashy Dora", theme `#f5c462`, the 3 shortcuts, and no manifest warnings
- [ ] Browser offers **Install** (Chrome desktop/Android address-bar install icon); after install the app opens standalone (no browser chrome) and the window/title is Dora
- [ ] Go offline (DevTools → Network → Offline) and reload → the app shell still loads (not the browser's dinosaur); navigating to an uncached route shows Dora's `offline.html`, not a raw error
- [ ] API calls while offline fall back to the last cached GET (NetworkFirst) rather than hanging; coming back online refreshes normally
- [ ] Deploy a new build over the top → within a reload or two the "new version" flow kicks in (skipWaiting/clientsClaim) and you're not pinned to the old worker (confirms the nginx `sw.js` no-cache rule)
- [ ] Web Push: with VAPID configured, subscribe from Settings/Alerts and confirm a push arrives (the SW is what receives it) — ties off the previously-unreachable push path
- [ ] ⚠️ iOS/Safari branding gap (FU-552): the iOS add-to-home-screen icon + Safari pinned-tab currently show Quasar's placeholder logo, not Dora — expected until FU-552; Android/Chrome/favicon should be Dora-branded

## Runtime backend URL (browser + PWA) — origin P8-10
- [ ] In a browser tab (dev or PWA), Settings → About → **Dora API endpoint** shows the current URL; clicking **Change** opens the prompt with the current URL pre-filled
- [ ] Save a bogus URL → toast "Instance URL saved", full reload, network banner drops (server unreachable) — confirm the app doesn't hard-crash and the About page still lets you re-open the prompt to fix it
- [ ] Re-save the original URL → app recovers cleanly on reload; API traffic goes back to normal



**Workflow:**
- Newest within each surface is at the top.
- Delete items as you verify them — no archive needed, the end-of-pre-release
  systems test catches anything that slips.
- Prefix `⚠️` on a heading means **blocking** other work — do those first.
- If a verification turns up a real bug, open a regular follow-up in
  `DORA_FOLLOWUPS.md` for the fix; this file is for "does it work, yes/no".
- "Origin FU-NNN" on each item is just a grep handle back to the work that
  spawned it; no two-way link, no archive.

---

## Cookbook & recipes

### Cookbook cookability + expiring filters actually filter (identity-map bug fixed 2026-07-10)
- [ ] Have at least one recipe whose every required ingredient is stocked, one with a required ingredient out of stock, and one with a free-text (unlinked) ingredient
- [ ] Apply the **Cookable** filter → only the fully-stocked recipe shows (before the fix this kept *everything*)
- [ ] Apply the **Not cookable** filter → only the out-of-stock recipe shows; the unlinked one appears in neither (before the fix this returned an *empty* page)
- [ ] Apply a max-missing / "almost cookable" filter if the UI exposes one → recipes over the threshold drop out
- [ ] With a stocked ingredient expiring within a few days, apply the **Uses expiring ingredients** filter → only recipes using that item show, with the expiring count badge
- [ ] While filtered, spot-check a recipe card: its ingredients list and cookability badge render correctly (the fix also touched what filtered pages eager-load)

### Free-text ingredient path in the recipe editor — origin FU-506
- [ ] Open any recipe → **Add ingredient** → in the picker, type a name that matches nothing (e.g. "star anise" on a fresh install)
- [ ] Two options appear under the option list: **Create "star anise"** and **Use "star anise" as free text (no pantry link)** (the second option, secondary-coloured with a pencil icon)
- [ ] Tap **Use as free text** → row's picker field label flips to **Free-text ingredient**, and the string `"star anise"` appears as a muted italic caption beneath the picker
- [ ] Save the recipe → refresh → the row still shows as unlinked with the same caption
- [ ] The recipe's cookability badge is **Unknown** (not "In stock" / "Missing") because a required ingredient is unlinked (tri-state)
- [ ] Later, on the same row, type in the picker and pick an actual stock item → row flips back to linked; caption disappears

### RecipeEditDialog stub-creator reshape — origin FU-095
- [ ] Cookbook → **New Recipe**: the modal now shows exactly four fields — Name, Cuisine, Category, Collection — and nothing else (no ingredients repeater, no image upload, no instructions textarea, no dietary tags / tools multi-selects, no times / servings / difficulty / time-of-day).
- [ ] Primary button reads **Create & open** (not "Save").
- [ ] Fill only Name → click **Create & open** → dialog closes and the URL changes to `/cookbook/<new-id>`; the detail page loads with the new (mostly empty) recipe. All the flesh-out editors (ingredients, structured/freeform/image steps, image, tools, dietary tags, times, servings) live on the detail page as before.
- [ ] Cancel from an empty form → nothing created; grid unchanged.
- [ ] Edit an existing recipe from the overview (the pencil / edit action on a card, if any surface exposes it) → modal opens with the recipe's current Name / Cuisine / Category / Collection populated; button reads **Save**; changing Name and saving → dialog closes, list refreshes with the new name, URL stays on `/cookbook` (no navigation on edit — the deep edit happens on the detail page anyway).
- [ ] Server-side: the created recipe has `steps_mode='freeform'` and `instructions=null` / `ingredients=[]` (defaults) — verify via GET `/api/recipes/<id>` shows an empty stub.

### Recipe importer — bulk-linker + PWA share target (Chunk 6) — origin IMPL_PLAN_RECIPE_IMPORTER
- [ ] Settings → Admin → Data → **Unlinked ingredients** appears in the sidebar under the Data subheader beside Backup & restore and Import
- [ ] With no unlinked rows in the DB, the page shows the empty-state ("Every recipe ingredient is linked to a stock item.")
- [ ] Import a recipe with 2–3 unlinked ingredients → open the bulk-linker → each unlinked ingredient shows as a group row with `raw_text • Used in N recipes`; count matches the number of distinct recipes using that text
- [ ] Two recipes that both paste-imported the same ingredient (e.g. one from AllRecipes, one from HBH — same base name but different casing/whitespace) collapse into ONE group row, count = 2
- [ ] Groups sort by count desc, then alphabetically by display text (case-insensitive)
- [ ] Pick a stock item from the autocomplete → click **Link** → toast confirms "Linked '<raw_text>' in N recipe(s)"; the group disappears from the page
- [ ] Open each affected recipe → the row that was unlinked is now linked to the picked stock item; cookability chip flips from neutral to a real True/False if that recipe had no other unlinked rows
- [ ] Click **Create new** on a group → a new stock item is created (defaulted to the most-stocked level) with `name = raw_text`, and the group's rows link to it in the same tap; toast names the created item
- [ ] Auto-complete typing filters to matches; empty search shows the top of the alphabetical list (capped at 50)
- [ ] **PWA share target — Android Chrome only.** After installing Dora as a PWA (from the browser's Install prompt), open a recipe on RecipeTin Eats in Chrome → hit Share → **Dashy Dora** appears in the sheet → tap it → Dora opens on the cookbook overview, the paste dialog pops with the page text pre-filled in the textarea + the recipe URL in "Where's this from?" → hit Import → new recipe lands in the cookbook
- [ ] Refresh the page after the share flow — the `?share_text=…&share_url=…` params are gone from the URL, so the dialog doesn't re-open on refresh
- [ ] Recipe-detail edit mode → Freeform steps → textarea shows the hint *"Paste the recipe text or type freeform — Ctrl+V works."* below the box

### Recipe importer — paste-based rebuild (Chunk 5) — origin IMPL_PLAN_RECIPE_IMPORTER
- [ ] Open Cookbook overview → "Import" button opens the paste dialog. Caption names the paste flow (Ctrl+A / Ctrl+C on the source, Ctrl+V into Dora)
- [ ] Copy a RecipeTin Eats page (Ctrl+A → Ctrl+C in the browser) → paste into the textarea → optionally type the source URL → "Import" → new recipe lands with name + servings + ingredients + steps; navigator lands on detail
- [ ] Repeat with an AllRecipes page and a Half Baked Harvest page — verify each imports without the "couldn't auto-structure" degraded banner
- [ ] Paste a page that fuzzy-matches < all ingredients → save works with unlinked rows present; recipe detail shows a neutral cookability chip (not True/False) until every row is linked
- [ ] Confirm `Recipe.source` on the imported recipe carries the URL you typed (if any) and is blank when omitted — nothing was fetched server-side
- [ ] Old `POST /api/recipes/import-from-url` returns 404 (route deleted); the new `POST /api/recipes/import-from-content` is the only import path
- [ ] From RecipeDetailPage → kebab → "Import over this recipe" → paste flow, confirm-overwrite dialog, fields patched

### Ingredient DnD — reorder + cross-section move — origin FU-118 (partner-fix from FU-161 2026-07-07)
- [ ] Open a recipe in edit mode that has 2+ sections + several ingredients in each. Each ingredient row has a drag handle (`drag_indicator` icon) on the far left, with grab cursor on hover
- [ ] Grab an ingredient by the handle (NOT by the row body — text inputs and selects should keep their normal click/drag-to-select behaviour); the source row dims to ~50% opacity while dragging
- [ ] Hover over another ingredient row → only that row lights with a primary-coloured outline ring (no flash on other rows; no row-shift)
- [ ] **FU-161 partner-bug regression check.** In a section with ingredients A, B, C, D, E (top→bottom), grab **B** and drop it on **D** (dragging *downwards*). Result must be `A, C, D, B, E` — i.e. B landed *just past D*, not one row above it. Before the fix, B landed at C's original slot (`A, C, B, D, E`), one row above the drop point
- [ ] Same list, grab **D** and drop it on **B** (dragging *upwards*). Result must be `A, D, B, C, E` — D at B's original slot, B pushes down. Same as shopping-list DnD's symmetric-with-shopping-list "insert at target's original slot" behaviour
- [ ] Drop within the same section → the source row lands at the target's slot; section_client_id unchanged; "Save" enables (dirty)
- [ ] Drop onto an ingredient in a *different* section → the source row lands at the target's slot AND the Section picker on the moved row now reads the target's section; "Save" enables
- [ ] Drop onto an unsectioned row → moved ingredient becomes unsectioned (Section picker reads "(Main)")
- [ ] Save → reload → order + section assignments round-trip exactly as left
- [ ] Drag and release outside any row → no change; source row returns to 100% opacity, no drop-over ring lingers
- [ ] Drag → press Esc / cancel → state cleans up (no stale dragging-row visuals)
- [ ] Drop on the *same* row (no movement) → no change, no save dirtying
- [ ] Section picker still works as before (for moving into an *empty* section that has no rows to drop onto)
- [ ] Same stock item appearing in multiple sections still renders as separate rows with distinct quantities/notes/optional flags (verify post-DnD that this stayed working, since the FU also includes a duplicate-ingredient assessment — duplicates remain allowed by design)

### Cookbook Chunk 6 — structured recipe steps — origin FU-093
- [ ] `alembic upgrade head` applies migration `c9d4f8e2a5b6` on SQLite **and** Postgres; `verify_mappings()` passes for `RecipeStep`
- [ ] Switch toggle to **Structured**, add a top step (text + hint + ingredient + tool), add a sub-step, reorder via ↑/↓, save → reload → structure round-trips
- [ ] Switch to **Freeform**, save → `steps[]` wiped server-side; the textarea content remains
- [ ] Toggle back to **Structured**, add steps, save → editor reflects new state
- [ ] URL importer: import a recipe with schema.org `HowToStep` → editor auto-fills Structured. Import a `recipeInstructions`-only string → editor stays in Freeform with textarea filled
- [ ] `HowToSection` import produces top-level "section" steps with sub-steps
- [ ] Delete an ingredient referenced by a step → the chip disappears + save round-trips without errors
- [ ] Save a step with empty text → server returns 400 with "Every step must have non-empty text."
- [ ] Backup → restore round-trips `RecipeStep` / `RecipeStepIngredient` / `RecipeStepTool` in FK-correct order

### Cookbook Chunk 7 — source URL + URL importer — origin FU-103
- [ ] `alembic upgrade head` applies `d0e5f1a3b8c7` on SQLite + Postgres; `verify_mappings()` passes for the reshaped Recipe
- [ ] Detail-page Source URL card appears under Instructions; typed value round-trips through save → reload; clearing the field → save → reload empty
- [ ] Entering an `http(s)://` URL reveals the "Open" ghost button; non-http hides it
- [ ] Importer: import from a schema.org-rich site → URL lands in `source` field (not appended to instructions); steps/ingredients parsed
- [ ] Degraded fallback: import a no-JSON-LD page → no 422; title + body text land in name/instructions; warning toast "Couldn't auto-structure that page" fires; `source` is set
- [ ] Overview "Import from URL" button opens dialog → paste URL → new recipe in cache → router lands on detail
- [ ] Unmatched-ingredients toast counts them ("3 ingredients couldn't be matched")
- [ ] An existing recipe with the old in-instructions "Source: …" still loads
- [ ] Backup → restore round-trips `source` column

### Cookbook Chunk 8 — recipe versions + detail-endpoint fix — origin FU-105
- [ ] `alembic upgrade head` applies `e1f6a2b4c8d9` on SQLite + Postgres; `verify_mappings()` passes
- [ ] Open a recipe with structured steps → editor's Structured/Freeform toggle populates correctly (latent bug from Chunk 6 / cook-mode Chunk 5)
- [ ] Open recipe → kebab → "New version". Singleton source allocates a `version_group_id` + back-fills source. Both share the id
- [ ] Already-grouped source: copy reuses the group
- [ ] "Other versions" card lists siblings on both source and copy; singletons hide the card
- [ ] Naming: first "New version" → "(v2)"; second click on source → "(v3)"; click on copy → also next number (server counts siblings, not parent)
- [ ] New version inherits ingredients, tools, structured steps (with sub-step + ingredient refs remapped), tags, cuisine, category, collection, source URL, image — image shows without re-upload
- [ ] Edit copy → save → source unchanged. Same the other way
- [ ] Delete one version → siblings stay; "Other versions" card updates
- [ ] Meal-plan picker + cookable filter see both siblings; allocations stay per-recipe
- [ ] Backup → restore round-trips `version_group_id`

### Cookbook Chunk 9 — cost + simple nutrition, opt-in — origin FU-116
- [ ] `alembic upgrade head` applies `e5b9d2c8a4f3`; `verify_mappings()` passes
- [ ] Both flags off (default): no kcal input next to servings; no cost/nutrition cards; cookbook overview has no Kcal sort/filter
- [ ] Turn on Nutrition (Simple, install layer on): kcal input appears next to servings; value persists across save/reload
- [ ] Nutrition card appears in detail sidebar when a kcal value is set
- [ ] Cookbook overview: Sort by → Kcal option; flip direction toggles label between "Highest kcal first" / "Lowest kcal first"; recipes with no kcal sink to the bottom
- [ ] Kcal ≤ filter narrows the list; recipes with no kcal value remain visible
- [ ] Turn on Money (install layer on): recipes with linked products + offers show "Estimated cost" card with $, help tooltip, "(N / M ingredients priced)" badge
- [ ] Cost math: pick a 3-ingredient recipe with linked products. Compute expected `Σ qty × current offer price ÷ size_value`. Card matches to 2dp
- [ ] No linked products: cost card hidden
- [ ] Partial coverage: card renders with "(2 / 5 ingredients priced)"
- [ ] Old freeform Nutrition expansion gone from detail page; an existing recipe with a `nutrition` text value still saves cleanly
- [ ] Money OFF + Nutrition ON: cost hidden, kcal surfaces visible
- [ ] Money ON + Nutrition OFF: cost visible, no kcal surfaces
- [ ] Wire shape: changing kcal sends `{ kcal: <int> }` only; clearing sends `{ kcal: null }`
- [ ] Pesto Light + Pesto Dark + Cherry Cola Dark — both new cards read

### Cookbook Chunk 10 — multi-part recipes via named sections — origin FU-119
- [ ] `alembic upgrade head` applies `f6c8e3a9b1d2` on SQLite + Postgres; `verify_mappings()` passes for `RecipeSection` + `section_id` on ingredient/step
- [ ] Existing recipes still load (no sections = flat list, location grouping)
- [ ] Create a recipe with two sections ("Sauce", "Filling"), assign per ingredient, save, reload → sections persist; RecipeCard shows "2 parts" badge
- [ ] Cook mode: ingredient panel groups under section names; step card shows the section as a chip; "All steps" repeats header at each transition
- [ ] Delete a section → rows fall back to "Main" (SET NULL), save/reload → no orphans, no FK error
- [ ] Rename a section without touching rows → rows stay pinned (editor sends ingredients[] + sections[] together)

### Cookbook Chunk 4 — detail page cleanup — origin FU-089
- [ ] Sticky top toolbar: Mark cooked (prominent) / Cook mode / Log cook / Print / Save / kebab(Delete) — stays at the top on narrow window
- [ ] Mark cooked bumps pool +1 + last-cooked; Log cook... logs N; Print opens print view; no CSV
- [ ] Name editable; blank blocks save with inline error
- [ ] Ingredient row without a stock item blocks save (prompt); unchanged name save succeeds
- [ ] Ingredient rows show a single chip (Missing wins) + tinted when missing
- [ ] Cookable/missing box readable in dark themes
- [ ] Cook-mode guard: unsaved edits OR not cookable → confirm dialog with working Cancel; outside click doesn't navigate; "Save & start" only proceeds on save success
- [ ] Cook mode exit returns to recipe detail page (not overview)
- [ ] "Available meals" label; meal ± shows no not-allowed cursor flash

### Cookbook Chunk 3 — card redesign + naming — origin FU-088
- [ ] Cards render with placeholder media tile, emphasised name, chips, dietary chips, meals box; equal-height in grid row
- [ ] MealStepper ± adjusts cooked pool live (decrement disabled at 0); also on recipe detail page and stock-item detail's recipe cards
- [ ] Allocated badge appears only when `committed_meals > 0`; **red** when `available_meals < committed_meals`, neutral otherwise — API must return `committed_meals` field
- [ ] Card has only Cook as primary; kebab = add-all-to-list + add-to-meal-plan (no Edit/Duplicate/Delete); clicking the card opens detail
- [ ] Collection groups are collapsible rounded boxes (header toggles, chevron flips)
- [ ] Naming: menu reads "Cookbook"; `g r` + command palette "Go to Cookbook"; detail breadcrumb "Cookbook"

### Cookbook Chunk 3+ revision (FU-088 → cookbook card revision) — origin FU-088 (revision)
- [ ] Image hide/show toggle works (per-user, persists across sessions)
- [ ] Allocated badge appears + drops correctly from overview
- [ ] Meals-cooked field relocates to planner correctly
- [ ] Meta-line swap renders correctly
- [ ] Optional ingredients render with `(optional)` hint + dimmed rows in cook mode
- [ ] Cookable signalled via cook-button colour (no separate dim)
- [ ] Difficulty filter + sort axis works
- [ ] Picker modal opens with per-ingredient checkboxes + Optional separator
- [ ] New footer layout `[♥][chef-hat][add-to-list]`
- [ ] Time-of-day vocabulary in edit dialog
- [ ] Per-row Optional checkbox in both editors
- [ ] Cookability still server-derived

### Cookbook Chunk 5 — images + tools — origin FU-091
- [ ] `alembic upgrade head` applies `b8e3f1a6d2c4` on SQLite + Postgres; `verify_mappings()` passes for `Tool`
- [ ] `GET /api/tools` returns seeded tools; Settings → Recipe tags & categories has a Tools editor (create/rename/delete + recipe counts)
- [ ] Recipe create/update round-trips `tool_ids`; edit dialog + detail page tools multiselect populate + save
- [ ] Overview Tools tri-state filter (include/exclude) works
- [ ] Upload on detail page → save → image shows on detail + card (via `GET /recipes/<id>/image`); change + remove work; cache-busts after save; >4MB rejected client-side; create dialog can attach image
- [ ] Backup → restore round-trips Tool/RecipeTool + recipe images

### Cookbook Chunk 2 — tag taxonomy — remaining items — origin FU-085
- [ ] Item 3: `repository.get(Recipe).all()` selectin-loads `recipe.cuisine`/`.category` (no null cuisine/category in assistant + global_search)
- [ ] Item 5: overview cuisine/category single-selects filter end-to-end; tri-state DietaryTagFilter cycles +/−/neutral and stays open; RecipeCard shows names + tag chips
- [ ] Item 6 (FU-147): on seeded "egg fried rice", two dietary tags pre-populate the picker; saving with no edit doesn't clear them; adding/removing tags + saving round-trips
- [ ] Item 8: backup → restore round-trips Cuisine/Category/DietaryTag/RecipeTag in FK-correct order
- [ ] Item 9 (FU-150): assistant `search_recipes`/`suggest_recipes` filter by cuisine + dietary tags (Python-side / name-resolved)

### FU-085 fixes — second-round verify items — origin FU-151
- [ ] FU-148 — Cookbook overview "Time of day" dropdown filters to Breakfast/Lunch/Dinner/Dessert/Snack/Any; clearable
- [ ] FU-149 — "# ingredients ≤" filter narrows the list; "# ingredients" sort axis orders ascending by default; direction toggle flips
- [ ] FU-150 step 1 — "i need a vegetarian recipe" lists vegetarian; header says "Filtering by: vegetarian recipe"
- [ ] FU-150 — "i need an asian recipe" applies cuisine filter
- [ ] FU-150 — "show me a breakfast recipe" applies timeOfDay filter
- [ ] FU-150 — "i need a recipe" with no other terms prompts for name/ingredient/cuisine/tag

### Recipe image-steps mode — origin (orphan FU at 2026-06-25, RECIPE_IMAGE_STEPS)
- [ ] Recipe detail mode toggle shows Structured / Freeform / Image; right editor renders for each
- [ ] Mode flip is non-destructive — Structured → Image → Freeform → Structured preserves each payload
- [ ] Image-mode editor: pick multiple files from disk; pick via mobile camera prompt (`accept="image/*" capture="environment"`); reorder via ↑/↓; remove; cap warning at 20
- [ ] Save with `steps_mode='image'` posts `step_images[]` as data URLs; `/api/recipes/<id>/step-images/<image_id>` returns the original at the right MIME
- [ ] Cook mode in image-mode renders full-width scroll gallery; tap-to-zoom opens; ingredient panel + finish flow + B8 substitute swaps + Sous Chef behave as before
- [ ] Auto-detect timer card hidden; standalone timer affordance still usable (manual via Sous Chef commands)
- [ ] New-version of an image-mode recipe clones the step images
- [ ] Alembic migration applies cleanly on existing DB; `steps_mode` backfilled to `'structured'` only where `RecipeStep` rows exist

---

## Cook mode

### Recipe personal notes in cook mode — origin FU-432 (RD-29)
- [ ] Edit a recipe on the detail page → the new **Personal notes** field (below Source URL) saves and round-trips (reload shows it); distinct from the instructions/steps field.
- [ ] Enter cook mode for that recipe → a **"Your notes"** card renders under the step navigation (above the ingredients panel), preserving line breaks.
- [ ] A recipe with **no** note → no notes card in cook mode (not an empty box).
- [ ] Make a **new version** of a recipe that has a note → the note carries onto the new version.

### Cook Mode Chunks 1–3 — origin FU-096
- [ ] Chunk 3 ingredient grouping: open cook mode for a recipe with ingredients across several locations → one card per *base* location (sub-areas collapse); no-location ingredients land in "No location" group
- [ ] No mid-cook stock-level chips: StockItemChip gone from the row; substitute chips + undo still render
- [ ] Quantity spacing: `unit="g"` reads `"250g"`; `unit="tbsp"` reads `"1 tbsp"`; `unit=null` reads just qty
- [ ] Chunk 2 — voice button reads **Sous Chef** with a tooltip; (?) opens popover listing 8 commands
- [ ] Chunk 2 timer: detect a "10 minutes" step → fill-bar below MM:SS → empties as time runs → at 0 turns negative colour, toast fires, short beep plays (no-ops on iOS/PWA without gesture); reset clears
- [ ] Chunk 1 finish flow: mark ingredients used, finish → dialog shows one row per used ingredient with current level chip, action chips (Down one / Out / Unchanged, default Down one), override dropdown, per-row Add-to-list
- [ ] `meals_cooked` defaults to **0**; Done with 0 → toast "All eaten — hope it was good."; N>0 → "You saved N meals — enjoy." (with pluralisation)
- [ ] Per-row override beats action: pick explicit level for one row → Done flips that row's stock_level_id to the override; `Unchanged` rows leave stock alone
- [ ] Fail-soft: a row pointing at a deleted stock item shouldn't stop the others (Promise.allSettled)
- [ ] Click-out cancels: open finish dialog, click outside → dialog closes, **no** level/cook calls fired
- [ ] Session swap interaction: swap an ingredient to its substitute, finish → the substitute's level (not the original) updates

### Cook Mode Chunk 5 — highlight + tools + hints — origin FU-100
- [ ] Open cook mode on a structured recipe → named ingredient rows tint + get a left accent; tools panel shows below ingredients (only when recipe lists tools); step-referenced tools light up, others dim
- [ ] Sub-step shows the "Sub-step" chip above the headline
- [ ] Step with a hint renders the hint line with lightbulb icon
- [ ] Unstructured fallback: recipe with only `instructions` → text-matched highlight fires when ingredient names appear in step text
- [ ] No tools panel when the recipe lists no tools
- [ ] Tick state really gone — no checkbox on ingredient rows; no checkbox in "All steps"; tap step text to jump
- [ ] Finish flow lists *every* ingredient on the recipe (with swaps applied), regardless of mid-cook interaction
- [ ] Voice: "Done" command gone from Sous Chef help; Next/Previous/Repeat/timer verbs still work
- [ ] Step navigation via "All steps" jumps to the right index; sub-steps indented in the list
- [ ] Pesto Light + Pesto Dark + Cherry Cola Dark — highlight tint reads in dark mode

### Cook Mode Chunk 6 — cooking-for headcount rescale — origin FU-101
- [ ] Default: recipe with `servings=4` shows 4 in "Cooking for" input; `servings=null` shows 1
- [ ] Rescale up: 4→6 multiplies ingredient quantities by 1.5× (200g → 300g; 2 eggs → 3)
- [ ] Rescale down: 4→2 halves them (200g → 100g; 4 eggs → 2)
- [ ] Fraction snap: 4-serving with `1 cup`, scaled to 3 → `¾ cup`; scaled to 6 → `1½ cup`
- [ ] Countable rounding: 4-serving with `1 egg`, scaled to 3 → `1 egg` (0.75 rounds up, floored at 1); scaled to 6 → `2 eggs`
- [ ] Floor at 1: countable that would round to 0 stays at 1
- [ ] Sub-tolerance fractions: `0.5 cups` × 1.0 shows `½ cup`
- [ ] Blur clamp: clear input → blur → re-clamps to 1; quantities don't NaN
- [ ] Min=1: typing 0 + blur → re-clamps to 1
- [ ] Session-only: rescale, exit, come back → input shows original `servings`; saved recipe unchanged
- [ ] Gram fraction edge: `7.5g` renders `7½ g`. If that reads weird in practice, flip g/kg/ml/l/mg to integer rounding in `scaleQuantity.ts`

---

## Meal plans

### Meal reconcile — page + dashboard chip + header nudge — origin FU-317 Chunk 5 (2026-07-09)
- [ ] With `AppSetting.auto_drain_past_meals` on the default (TRUE) and a fresh install, create a meal plan for **today - 2 days** with one entry, then hit `GET /api/meal-plans/today` (or open the dashboard) to fire the sweep. Confirm the dashboard now shows a **Reconcile 1 past meal** chip in the *Your kitchen* zone; the meal-plans page shows a **1 past-day meal needs confirming →** link above the planner.
- [ ] Tap the dashboard chip → lands on `/meal-plans/reconcile`. Runner shows the entry: recipe name, scheduled date + slot, planned servings. Five verb buttons: **Cooked** (big primary), **Different portions** + **Cooked later** (secondary pair), **Didn't cook** (danger-ghost), **Skip for now** (small ghost).
- [ ] Tap **Cooked** → the recap card appears with 1 cooked / 0 others; **Done** returns to `/dashboard`. Both the chip and the header link have disappeared (queue empty). Recipe pool unchanged from what the sweep already decremented.
- [ ] Under auto-drain OFF (`PATCH /api/app-settings {auto_drain_past_meals: false}` first), repeat: sweep leaves the pool untouched → Cooked verb applies the drain now. Recipe pool drops by the entry's servings.
- [ ] Try **Different portions** → dialog asks for actual servings; picking 5 for a 2-planned entry drops the pool by an extra 3.
- [ ] Try **Cooked later** → dialog picks a date; the receipt shows a `cooked_on` value (verifiable via DevTools `GET /api/meal-plans/reconcile-queue?include_resolved=true` — currently returns empty in MVP, so a direct DB peek is fine).
- [ ] Try **Didn't cook** on an entry that was already drained → the pool goes back up by the entry's servings; the entry drops out of the queue.
- [ ] Try **Skip for now** → the entry stays in the queue on refresh (drops to a `resolved_deferred` receipt state).
- [ ] Threshold check — build **3 unresolved entries** stretching **5 days back**, trigger the sweep, then check `/alerts` for the `meal_reconcile_overdue` alert kind (message like "3 past meals need confirming") + `/api/suggestions` for the `reconcile_meals_pending` suggestion.
- [ ] `/meal-plans/reconcile` empty state — with zero unresolved entries, the runner renders "Nothing to reconcile" + a Back-to-Meal-plans button. No chip, no header link.
- [ ] Text-size preference (Preferences → Display): flip to XL — the runner card, buttons, and help dialog all scale.
- [ ] Themes: check the runner on Pesto light + Pesto dark + one other family — no hardcoded colours.
- [ ] `(?)` help icon in the top-right of the runner opens the "How reconcile works" dialog listing every verb.
- [ ] **Settings → Admin → System → Meal reconciliation** (FU-317 Chunk 6): the page renders with an *Assume past-day meals were cooked* toggle and a *Go to reconcile* deep-link button. Flipping the toggle fires a success toast and persists across reload. As a non-admin user, the page shows the "You don't have admin permissions" banner instead.
- [ ] Settings left nav shows a **Meal reconciliation** row under **System** with the event-note icon (admins only).

### Budget-defense recipe swaps (Suggestions panel) — origin FU-451
- [ ] With **money features on** and a **budget set**, build a meal-plan week that's projected over budget (priced recipes summing past the budget). A **Suggestions** panel renders below the week grid: "Over budget by $X", Est. week cost + Budget figures, "N swaps could bring it back to $Y".
- [ ] Each candidate row reads "Recipe swap · <Day> <Slot>", shows the from→to recipe names, a reason chip (uses-stock / same-style / cooked-before), and a **−$saved** figure. **Preview** opens a dialog with the after-cost, the saving, and any missing ingredients.
- [ ] **Apply swap** → the week grid updates to the swapped recipe, a "Swap applied · Undo" banner appears. **Undo** restores the original recipe.
- [ ] The Dashboard **budget card** shows a "Save $X this week — N swaps ready · See suggestions →" bullet with the same total; clicking it lands on the planner.
- [ ] A meal already marked **cooked/consumed** never appears as a swap candidate.
- [ ] **Money features off** → no Suggestions panel, no dashboard bullet at all.
- [ ] Zero-state: contrive a week that's over budget but where no alternative is cheaper → panel shows "No swap saves you money this week" + an **Open shopping lists** link.
- [ ] Apply a swap, then (in another tab / after editing the week) apply the *same stale* card → server returns a 409 "out of date" and the toast surfaces it; refreshing re-fetches.

### Unlinked-ingredient warning after meal-plan → shopping list — origin FU-505
- [ ] Build a meal plan for the week where at least one planned recipe has an ingredient with **no linked stock item** (either a paste-imported recipe that never got linked, or one you added a "Use as free text" ingredient to per FU-506)
- [ ] Trigger **Generate shopping list for this week** from the meal-plan surface
- [ ] Success toast fires normally (added-count line)
- [ ] **Immediately after**, a dialog titled **Add these manually** appears listing each unlinked ingredient as `• <ingredient> (<recipe>)`, with a single **Got it** button
- [ ] Tap **Got it** → dialog closes; navigation to the new shopping list still happens
- [ ] Repeat with a meal plan whose recipes are **all fully linked** → success toast, no dialog

### Meals-per-week preference — origin FU-181
- [ ] Preferences → Meal planning shows a **Meals per week** number input under **Cooking style**; placeholder text reads `7`, min 1 / max 21
- [ ] With the field blank, open the sequential builder on `/meal-plans` → the header count still reads `/ 7`, matching the fallback *(FU-304 closed 2026-07-07: `/meal-plans/board` is retired and now redirects to `/meal-plans`; only the surviving planner needs checking.)*
- [ ] Set the input to **5** → save toast reads "Meals per week set to 5." → **without reloading**, reopen the sequential builder → header count now reads `/ 5`
- [ ] Clear the input (or type a value outside 1–21) → save toast reads "Meals per week reset to the default (7)." → builder count returns to `/ 7`; the field snaps to blank (placeholder shows again)
- [ ] Type a decimal (e.g. `3.7`) → server rounds it, saved value is the rounded integer; a value <1 or >21 collapses to null (reset toast)
- [ ] `PATCH /auth/me { meals_per_week: 22 }` from DevTools returns 400 (server-side bounds guard)

### In-context Print on the meal planner — origin FU-338 (Board page portion retired with FU-304, 2026-07-07)
- [ ] `MealPlansOverview` (`/meal-plans`) still has its existing Print icon in the week header — no regression there
- [ ] Resize to mobile (<md) → the mobile focus renders. The Print icon lives in the week-nav row, right of the "Next week" arrow. Only shown when the focused week has ≥1 planned meal
- [ ] Tap Print on mobile → new tab opens the meal-plan print view for the focused week
- [ ] Direct-navigate to `/meal-plans/board` (or any stale bookmark from the old Direction-B page) → clean redirect to `/meal-plans`; the surviving planner's Print icon works as above

### useListState — full sweep across meal planner + shopping list detail — origin FU-354 + FU-355 (2026-07-07)
- [ ] Open `/meal-plans` → type a distinctive search string (e.g. "spag") into the recipe picker's search input → the picker filters to matching recipes
- [ ] Navigate to a recipe from the picker (or any other page, e.g. `/cookbook`) → hit browser back → return to `/meal-plans` → the picker search still reads "spag" (was blank in the pre-FU-354 behaviour)
- [ ] Open any `/shopping-lists/<id>` detail → set the top-right group toggle to **Location** (or **Store**) → navigate away (dashboard or another list) → return → the toggle is still **Location** (was reset to **None** before)
- [ ] Switch to a different shopping list → the group toggle carries over (the scope is per-page, not per-list — verify this matches the intent; the FU note explains why per-list would silently reset on switch-list)
- [ ] **Sign-out clears both**: on `/meal-plans` with a picker search set + on `/shopping-lists/<id>` with a groupBy set → open the account menu → **Sign out** → log back in → the picker search is empty, the group toggle is None again (FU-355's `clearAllListState()` fires in `logoutAsync`)
- [ ] **Silent 401 recovery clears both too**: with the same setup, force a session expiry (server restart, or hand-clear the session cookie in DevTools) → make any API call → the 401 interceptor's `handleSessionExpired` fires → SPA lands on the login page → after re-auth, both list-state values are empty
- [ ] Hard-reload (Ctrl-Shift-R) on either page → both list-state values reset (module-scope Map wipes with the fresh bundle) — this is by A8 §3 design ("a full reload should feel like a clean slate")
- [ ] Grep-verify (`web_app/src/composables/useListState.ts`) the `CACHE` Map is still module-scope (not localStorage) — the persistence contract is session-only

### Show-all-slots persistence — origin FU-306 (2026-07-07)
- [ ] Open `/meal-plans` on desktop. The "Show all slots" toggle above the carousel is **off** by default (only used slots render per day)
- [ ] Flip it **on** → every household slot renders per day → hard-reload the page → toggle stays **on**, all slots still render
- [ ] Flip it **off** → hard-reload → toggle stays **off**, used-slots-only again
- [ ] DevTools → Application → Local Storage → `mealPlanShowAllSlots` is `'1'` when on, `'0'` when off
- [ ] Private-window / storage-disabled sanity: open the page in a private window with storage blocked — the toggle still works within the session; reload reverts to off (no error toast, no console throw)
- [ ] The setting is per-device — flip on in browser A, open in browser B on the same account → browser B is off (this is a device-scoped preference, not a household one)

### Templates drawer owns per-template CRUD; page is Sets-only — origin FU-308 (2026-07-07)
- [ ] Planner (`/meal-plans`) → open the Templates drawer from the right rail's Templates card. Each template row shows **Apply · Rename · Clone · Delete** actions (Clone is a document-copy icon between Rename and Delete)
- [ ] Click Clone on a template → row shows a brief loading spin → positive toast "Cloned." → the drawer's list refreshes and shows the new template (usually named "Copy of …" depending on server behaviour)
- [ ] Click **Manage rotating sets →** at the drawer footer → the drawer closes and the SPA navigates to `/meal-plans/templates`
- [ ] The page header now reads **Rotating template sets** with a caption ending "Manage individual templates from the planner's **Templates** drawer." No **Templates** card is visible on the page anymore — Rotating sets is the only management surface here
- [ ] From the sets page, create a new rotating set → the "Add a template" picker still lists every template (the page still loads the template store for that dropdown, even though it doesn't render its own template list)
- [ ] Direct-navigate to `/meal-plans/templates` (deep-link / bookmark) → lands cleanly on the sets-only page; browser tab title reads **Rotating template sets**
- [ ] Grep-verify (`useMealPlanner.ts`) no longer exports `goToManageTemplates` and nothing in the app tries to call it — no console error, no dead menu item

### Meal Planner R-Phase 1 extraction + Phases 2–6 — origin FU-305
- [ ] Left palette: search filters trays; click-add into a focused slot; drag-and-drop from a recipe row to a day-slot (mouse only); pool ± / log-cook dialog; "Cancel" clears focused-target banner
- [ ] Middle column: ↑/↓ arrows, top/bottom buttons, vertical-swipe on mobile, calendar click all move the focused week; URL `?monday=` persists across reload (F29)
- [ ] Per-day slot rows render entries, drop targets accept dragged recipes, "Other" row appears for off-vocabulary historical entries
- [ ] Today badge + past-day dim still render; entry chip view/cook/remove/adjust wires through
- [ ] Clear-week + print buttons in header work
- [ ] Right column: calendar, this-week-shopping count, ingredient list with hover-highlights, AddToList button, cook-by warning, "Full ingredient demand" expansion, generate-list + C-7 target picker
- [ ] Templates card: save / apply / apply-recurring / manage-templates flows
- [ ] Sequential-builder dialog opens, lists recipes, builds + generates the list

### Meal Plans C-2 — full surface walk — origin FU-179
- [ ] Carousel nav — ↑/↓ arrows + keys + mobile swipe move weeks with slide animation; `prefers-reduced-motion` disables; `weekRangeLabel` updates
- [ ] Tap-add — tap a day's slot (highlights + banner shows target), tap a recipe → entry lands in **that** slot (NOT always "Dinner", F35). Re-adding to same slot increments servings
- [ ] Drag — desktop drag onto slot adds; touch disables drag, tap-add works (no scroll-jank)
- [ ] Implicit create — first add to an unplanned week silently creates the plan; sidebar switches from "no meals planned" to shopping summary
- [ ] Inline servings — ± stepper adjusts live, removes at 0; view/cook/remove work
- [ ] Past days dimmed + reject taps/drops; Today badge on right day; Thu-8am-AEST drop repro (F29) no longer 400s (ties to C-2.K)
- [ ] Left list — search filters; "N free" + inline ± pool stepper + log-cook work; no cookable colour/check
- [ ] Off-vocab — entry with deleted/legacy slot renders under "Other"
- [ ] Sidebar/generate work bound to focused week; "Jump to a plan" focuses chosen week; "Clear this week" empties it
- [ ] **C-2.D calendar** — right column ~6 weeks; status underlines (green planned / amber short / dotted-grey all-consumed / none empty); today has a dot; focused week outlined; clicking a week jumps carousel (and back); month banner + arrows page the window; `?monday=YYYY-MM-DD` resumes on that week; old "Jump to a plan" dropdown is gone
- [ ] **C-2.H sidebar** — each needed-ingredient row shows list status ("on <list>" / "not on a list") + add-to-list button (multi-list opens picker); hovering (desktop) outlines using meals; per-item stock chips use **app-wide colours**; membership loads on the planner
- [ ] **C-2.I trays** — left column groups into Favourites · Haven't-had (oldest/never first) · Frequently-planned · All recipes; curated trays hide when empty; searching collapses to "Results"; 21-day "haven't had" window spot-check; "frequently planned" ranks by plan frequency
- [ ] **C-2.F templates** — right column "Save this week as a template" (only with meals) → name + description; "Apply a template…" forks onto focused week (past skipped; toast shows added/skipped); confirm before replacing existing future meals; editing/deleting a template leaves a week forked from it untouched
- [ ] **C-2.G sets + recurring + manage** — `/meal-plans/templates` (via Manage templates) lists templates (rename/clone/delete) + sets (new/edit-with-↑↓-reorder/delete); "Apply recurring…" applies a template or rotating set over ≤26 weeks; set rotates templates week-by-week; 26-week cap + "pick exactly one source" surface as toasts
- [ ] **C-2.J sequential builder** — planner's "Plan step-by-step" opens 3-step flow (pick → preview → build & generate) ending on done with Print (Email shown disabled). Cancel writes nothing; preview's buy/in-stock matches sidebar; build spreads meals across upcoming days + generate-list modal fires; Print opens the week's print view

---

## Shopping lists

### Substitute-swap gating on a line — origin FU-407 (RD-18)
- [ ] A shopping-list line whose stock item **has** a recorded substitute → the swap (⇄) icon is enabled; tooltip "Swap for a substitute item"; tapping opens the substitute chooser.
- [ ] A line whose item has **no** substitute → the swap icon is **disabled**; tooltip "No substitutes recorded for this item" (no dead-end tap→toast).
- [ ] The swap affordance reads as distinct from the "store offers" picker on the same line (no "two Substitute labels" confusion).
- [ ] Product-only line (no stock item) → swap disabled.

### Put-away dialog on a finished list — origin FU-452
- [ ] Finish a list with a mix of ticked lines whose stock items live in different locations (Fridge, Pantry, Freezer) plus at least one item with no location set → list transitions to `done` → toolbar shows a primary **Put away** button next to *Copy to new list*.
- [ ] Click **Put away** → dialog opens titled "Put away" with grouped cards ("Fridge · 3", "Pantry · 2", "Freezer · 4", "(No location) · 1"). Ticked lines only — un-ticked lines never appear.
- [ ] Click a location group header → group ticks, collapses (items hide), chip flips to positive/green.
- [ ] Click the same header again → group un-ticks, items re-appear, chip reverts.
- [ ] "(No location)" group is pinned to the bottom regardless of alphabetical order — its header has no tick affordance (the ✓ icon slot is empty).
- [ ] Click **Assign** on an unsorted item → small "Assign a location" mini-dialog opens with a searchable location picker → pick a location → **Save** → toast "Sorted *<item>*" → item disappears from "(No location)" and appears in its new group; the mini-dialog closes.
- [ ] Cancel/close the mini-dialog without saving → nothing changes.
- [ ] Close the main Put-away dialog → re-open it → **all group ticks are reset** (ephemeral state is the point).
- [ ] Open the dialog on a list where every ticked line already has a location → no "(No location)" group appears.
- [ ] Open the dialog on a list where every ticked line is unsorted → only "(No location)" shows, with per-line Assign buttons.
- [ ] Open the dialog on a `done` list with zero ticked lines → banner "Nothing to put away — no ticked lines on this list."
- [ ] Put-away button does **not** appear on a non-`done` list (draft or shopping status).

### Quick-add toast + "always ask" pref — origin FU-316
- [ ] Have exactly one draft list open → quick-add a stock item (chip / bulk / detail toolbar) → toast reads **"Added to *<display_name>*."** (destination named — not "Added to your list.")
- [ ] Item already on that list → toast reads **"Already on *<display_name>*."**
- [ ] Open 2+ draft lists → quick-add → picker fires → pick one → toast still names the picked list
- [ ] Same tab session, second quick-add → no picker (session-remembered), toast still names the list
- [ ] **Preferences → Shopping lists → Always ask which list** → toggle on → save toast "Dora will always ask which list."
- [ ] With "always ask" on and 2+ drafts → every quick-add re-prompts (session pick is not remembered); dialog copy reads "Dora will ask again next time (you can change this in Preferences)."
- [ ] Bulk-add a batch of items from Stock Overview with 2+ drafts and "always ask" on → picker fires once on the first item → all remaining items land on the *same* picked list (batch doesn't silently drop items 2..N)
- [ ] Toggle "always ask" back off → save toast "Dora will remember your pick." → next quick-add prompts once, then remembers again

### Receipt-photo attachments — origin FU-334 + R-024 follow-on
- [ ] Open a `draft` list → no Receipts section visible (correct — must Start shopping first)
- [ ] Start shopping → Receipts section appears with empty-state copy "No receipts yet…" and the **two-button picker**: *Take photo* + *Choose receipt* (mobile) or just *Choose receipt* (desktop)
- [ ] On mobile (Android Chrome / iOS Safari): tap *Take photo* → rear camera opens directly; capture → thumb appears in the strip
- [ ] On mobile: tap *Choose receipt* → OS picker offers Photos / Files / (iOS) Scan Documents — pick an existing photo → thumb appears
- [ ] On desktop: the *Take photo* button is hidden (no camera affordance); *Choose receipt* opens the file picker
- [ ] Pick a >12MB image → inline error caption AND toast "Could not read that image…" fires, nothing added
- [ ] Pick a non-image (e.g. PDF) → same error path, nothing added
- [ ] Tap a thumbnail → full-screen lightbox opens with the receipt rendered ≤80vh; backdrop click + Esc both close it
- [ ] Tap the trash icon on a thumb → it disappears optimistically; reload the page → still gone (server confirms)
- [ ] Add 3+ receipts → they render left-to-right in upload order; reload → same order
- [ ] Finish & restock the list → list becomes `done` → Receipts section *stays visible* with all attached photos (record-keeping survives finish)
- [ ] Delete the whole list → no orphaned attachment rows (DB cascade) — the bytes endpoint 404s on a former attachment id

### Image-source picker — sanity sweep across surfaces — origin R-024
- [ ] Recipe **hero image** edit (recipe edit dialog): shows *Add (camera)* + *Add (file)* on mobile, just *Add (file)* on desktop. Both routes process via `processImageFile` (resize visible in payload size)
- [ ] Recipe **step images** editor: *Add images (camera)* + *Add images (files)* — files variant accepts multiple, camera captures one then returns
- [ ] **Stock item image** edit (stock item detail): same split, *Change* verb when an image is set, *Add* when empty
- [ ] **User avatar** (Account Settings): same split, behaves like stock item
- [ ] **Store logo** (Stores Settings): still uses `q-file` (FU-335 carve-out; do not regress)

### Trim-to-budget banner + Deferred section — origin FU-448
- [ ] With `money_features_enabled=false` on the user, the banner never appears on any shopping list, regardless of projected total or budget setting
- [ ] With money features on but `budget_amount` null, banner never appears (endpoint returns `budget_target=null`; SPA self-gates)
- [ ] With money features on, budget_amount=$100/week, spend-so-far=$60: an auto-generated list projecting $80 shows the banner ("Projected $80 · budget remaining $40 — trim $40 to fit")
- [ ] **Show what would be cut** expands a preview card with per-line rows, each with a warning-tint reason chip (one of: `Habit — can wait`, `N days' cover left`, `Not urgent`, `Above your usual price`, `Out, but no meal booked`, `For <Recipe> on <Day>`, `Needed for N meals later`) and a `Keep` button
- [ ] Clicking `Keep` on a preview line re-fires the preview excluding that line; the banner + preview totals update; no mutation until Apply
- [ ] **Trim to fit** flips `deferred_by_budget=true` on the chosen lines, they move to a collapsible "Deferred to fit budget (N)" section below the active list, and the banner switches to a compact "Trimmed $X to fit — see deferred (N)" confirmation strip
- [ ] Tapping the link in the confirmation strip scrolls to the Deferred section
- [ ] Each Deferred line shows the frozen reason chip + line price + an `Add back` button; clicking flips the line back into the active list; if that pushes projected total back over budget, the banner reappears on next load
- [ ] **Dismiss** hides the banner for the current view; refresh brings it back if still over budget
- [ ] Tier ordering (highest-price cut first inside a tier): drop a $5 habit item + a $20 low-stock-with-cover item on the same list, both over-budget triggers → the $20 gets cut first inside its tier; the tier-1 habit item only gets cut if the tier-2 cover doesn't close the gap
- [ ] Never-cut set holds: essentials (`is_flagged=true`), items with a meal booked in next 2 days, verdict=buy on low/out lines, and sub-$2 lines all survive even when we still overshoot after trimming everything else
- [ ] "Trimmed everything safe. Still $X over" fallback surfaces when the safe-cut tiers exhausted before hitting the target
- [ ] Assistant intent: **"trim my shopping list to my budget"** proposes the trim with a specific one-line summary (dollar delta + cut count + list name); Confirm applies + returns a "Done — trimmed $X off … (N items moved to Deferred)" message
- [ ] Assistant intent when the user has no budget → replies "You haven't set a grocery budget yet — Settings → Money is the place to turn it on"; when already under budget → replies "…is already inside your $Y remaining — nothing to trim"

### Shopping list UX v2 — origin FU-165
- [ ] Rail order + auto-scroll + next-up marker works
- [ ] Mobile dropdown opens + picks
- [ ] Rename → clear name → list self-labels (and re-labels when shop day changes)
- [ ] Shop-day button tones (today/overdue) correct
- [ ] Doughnut + totals render correctly
- [ ] Start shopping → sticky footer → restock-review modal (incl. per-item level tweak) → Reopen reverses it
- [ ] Quick-add mid-shop works
- [ ] Row actions: price button, swap, remove
- [ ] Group-by toggle works
- [ ] Bulk select works
- [ ] Print view works
- [ ] No empty-state flash on load
- [ ] Drag-reorder lands on the exact row you drop on (FU-161 root cause was fixed in P6-01 Chunk 6 — confirm it stays fixed)
- [ ] Dashboard card + Dora-chat add-to-list still work (both touched)

### Cart Button Chunk 2 — combined modal for 2+ products — origin FU-130
- [ ] 0 linked products → row cart click adds silently. No modal. One toast
- [ ] 1 linked product → same silent add. No modal
- [ ] 2+ linked products → row cart click opens `QuickAddSheet` pre-populated with stock item; target-list dropdown + offer radio + quantity editable; Add → one toast
- [ ] 2+ products AND 2+ drafts → still one surface, no stacked modals
- [ ] `linked_product_count` on `/stock-items` JSON; 0 with no rows; increments as products linked
- [ ] Bulk variant unaffected — resolves target once + one summary toast regardless of per-item counts
- [ ] **Known repro (2026-06-14):** picker modal NOT popping up when adding to a list with 2+ linked products (silent-add path firing instead). Likely candidates: `linked_product_count` not hydrating, `shouldUseCombinedModal.value` false from store mismatch, or `selected-product-id` short-circuit firing on wrong surface. Capture which screen + which item it fails on

### Cart Button Chunk 3 — standalone product lines + rules 1–3 — origin FU-132
- [ ] Migration `d7c9e4a8c2b1` applies on SQLite + Postgres; `verify_mappings()` passes for the now-nullable `stock_item_id` + new `product_id` FK
- [ ] Rule 1: POST `/api/shopping-lists/<id>/lines` with only `product_id` creates a line; DTO carries `product_id` + null `stock_item_id`. CHECK constraint rejects body with neither (400 before DB)
- [ ] Rule 2: draft list has product-only line for P, P not yet linked. POST `/api/stock-items/<S>/products` with `product_id=P` → orphan line upgrades (`stock_item_id` becomes S, or folded into existing stock-item line with P set)
- [ ] Rule 3: stock-item line for S + separate product-only line for P (P linked to S). DELETE stock-item line by line-id → nested product line gone. Same for cart-button remove-by-stock-item
- [ ] No regressions on stock-item-only adds — existing dedupe by `stock_item_id` still wins
- [ ] TS compile: `ShoppingListLine.stock_item_id: string | null` doesn't break consumers

### Cart Button Chunk 3 UI — origin FU-145
- [ ] Add a product-only line via My Products row ("Add as product") on unlinked product → line lands with product chip + tinted "product only" background
- [ ] Link the product to a stock item later → parent stock-item line appears (rule 2 backend) AND product nests visually under it (rule 2 frontend)
- [ ] Remove nested product → rule-4 modal fires; "Yes" removes both, "No" leaves the parent
- [ ] Remove product-only line whose linked stock item is NOT on the list → no modal
- [ ] Inline-product Axis B with 0 / 1 / 2+ drafts: 0 → "create a draft first" toast; 1 → silent add; 2+ → radio picker, both picks work
- [ ] Linked products on My Products row still hit `onAddSingle` (stock-item path); ticking nested children works; bulk mode handles parents + children

### Cart Button Chunk 4 — meal-plan generate via Axis B — origin FU-135
- [ ] 0 draft lists: no picker; creates new list named `Meals: <plan>`; toast "Shopping list created with N items."; routes to new list
- [ ] 1 draft list: picker opens with that draft preselected + "+ Create new list" row; OK on draft → backend merges, toast "Added N items to your list.", routes to that list
- [ ] 2+ draft lists: lists all drafts (first preselected) + "+ Create new list"; both picks work
- [ ] Cancel/dismiss: no list, no toast, no nav
- [ ] `nothing_to_add` path still emits info toast and doesn't navigate

### State Ownership Chunk 6 — snapshot-at-add — origin FU-142
- [ ] Add line with selected offer → budget's `projected_active` (or post-finish `spent`) reflects planning-time price; price the offer up via companion + confirm snapshot is the original value
- [ ] Change `selected_product_id` via offer chip → snapshot re-captures at new offer's current price
- [ ] Clear selection → snapshot clears (line shows as "no priced intent" in any UI surfacing it)
- [ ] Tick an already-snapshotted line → tick does NOT overwrite snapshot
- [ ] Untick → snapshot persists
- [ ] Tick a legacy line (created before this chunk with `picked_offer_price` NULL) → belt-and-braces hook fills snapshot first time

### P6-01 Chunk 3 — list lifecycle — origin FU-066
- [ ] DRAFT detail → *Start shopping* → router lands on /shop directly
- [ ] SHOPPING /shop → tick a few items → kebab *Finish & restock* AND footer button → dialog lists ticked items (capped at 8 + "and N more") → restock + archive
- [ ] SHOPPING /shop → back-arrow → tooltip "Back to editing", status flips to DRAFT, lands on detail (no bounce-back)
- [ ] DONE detail → *Reopen* → restock changes reverse; status returns to DRAFT
- [ ] PWA "Shop now" — 1 SHOPPING → resume; else 1 DRAFT → open; else overview
- [ ] Open in Pesto Light + Pesto Dark + Cherry Cola Dark — dialog / primary-button styling reads

### P6-01 Chunk 4 — unified "New shopping list" dialog — origin FU-068
- [ ] Toolbar *New list* → *Empty + Create new* → empty list, routes in
- [ ] *Empty + auto-fill: low-or-out + new* → equivalent of old "From all low/out stock"
- [ ] *Template + new* → uses `instantiateAsync`; lines match template
- [ ] *Recipe + new* → bulk-adds the recipe's ingredient stock items
- [ ] *Meal plan + new* → bulk-adds `getIngredientsAsync` results
- [ ] *Empty + auto-fill: flagged + essentials-only + merge into existing* → equivalent of old "Top up the primary list"
- [ ] *Template + merge* — temp-list-then-delete dance leaves no orphan list in overview (refresh after)
- [ ] Empty-state — no active lists and stock has low/out → kickstart "New list" opens dialog with *low-or-out* pre-ticked
- [ ] Cancel discards the form (re-open shows defaults)
- [ ] Pesto Light + Pesto Dark + Cherry Cola Dark

### P6-01 Chunk 5 — merged list selector + landing — origin FU-069
- [ ] `/shopping-lists` with multiple → lands on SHOPPING if any, else newest DRAFT, else newest DONE
- [ ] `/shopping-lists` with zero → empty-state renders New list; click → dialog → submit routes to created list
- [ ] Detail selector: dropdown opens with Active (current highlighted), Archived below separator, + New list at top, Manage templates… at bottom
- [ ] Active row kebab → Copy unticked / Archive / Delete behave correctly; Archived row → Copy archived / Delete
- [ ] Deleting currently-open list bounces to landing + landing picks next list
- [ ] + New list in selector opens dialog; submit routes to created list
- [ ] Switching to a different list via selector loads its detail (status watcher / shop-mode redirect still works for SHOPPING)
- [ ] Mobile width: dropdown usable

### P6-01 Chunk 6 — in-store polish + drag-reorder — origin FU-073
- [ ] Start shopping → tap *Skip* → next item → refresh → skipped item still at end
- [ ] Tap the centre qty number → dialog → type "12" → Save → row shows 12; refresh → still 12
- [ ] Tap **Peek list** → modal lists ticked + unticked → tap an unticked → modal closes + that item is next-up; refresh → still next-up
- [ ] Detail page (DRAFT): drag line from position 1 → position 5 → lands at index 5; drag 5 → 1 → lands at index 1; off-by-one is gone (FU-161 root cause)
- [ ] Detail header: old back-arrow is gone (replaced by list selector)
- [ ] Pesto Light + Pesto Dark + Cherry Cola Dark

### Chunk 6 audit: pricing + group-by-aisle — origin FU-072
- [ ] Price editor still opens mid-shop and saves `actual_unit_price`
- [ ] Toggling group-by-location → none → group-by-merchant doesn't quietly mutate saved order

### P6-01 Chunk 7 — planned shop day — origin FU-076
- [ ] Open a list → header chip reads "No shop day" → click → date dialog → save 2026-07-01 → chip updates → refresh → still set
- [ ] Clear the date via Clear button → chip → "No shop day"
- [ ] Create a list via *New list* dialog with a date → detail loads → chip shows the date
- [ ] Set a DRAFT's date to today → navigate to `/shopping-lists` → lands on that draft (priority pick)
- [ ] With today set: in-detail banner appears with info-tone "Shopping day is today."
- [ ] With a past date set + status still DRAFT: warning-tone banner "Planned shop day was … — still unfinished."
- [ ] Selector dropdown: list with planned date sorts ahead of unscheduled lists; today's list at top of its band
- [ ] Pesto Light + Pesto Dark + Cherry Cola Dark

### Shopping lists Chunk 2 — 2+-draft picker + Shop-now routing + Set-primary removal — origin FU-060
- [ ] 2+ drafts: stock-overview cart click pops disambiguation dialog; chosen draft persists across cart clicks (sessionStorage); finishing the chosen draft clears the hint and the next cart click re-prompts
- [ ] 0 drafts: cart click shows "No draft list" dialog → "Open lists" lands on overview
- [ ] PWA "Shop now": 1 SHOPPING → shop mode; 1 DRAFT (no SHOPPING) → that draft's detail; anything else → overview
- [ ] No "Set as primary" / "Make primary" / "Primary" badge / Primary chip is visible anywhere (overview, detail, ShoppingListTemplates, ExportPrint primary chip)
- [ ] Migration `d5e9f3b2a1c8` applies cleanly on a real dev DB

---

## Stock

### Product unlink fix (str/UUID 404) — origin FU-528 family
- [ ] On a stock item that has a linked product (detail page → linked products), unlink the product → it disappears from the list without an error toast (previously every unlink silently failed with a 404 under the hood)
- [ ] Refresh the page → the product stays unlinked; relink it → link works as before

### Stocktake snooze no longer 500s the queue / breaks the bell (SQLite) — origin FU-526
- [ ] On a SQLite install: with at least one item overdue for stocktake, **snooze** one item from the stocktake queue → the queue still loads (no 500 / error state) and the snoozed item drops off it
- [ ] While that snooze is active, open the **alerts bell** and the `/alerts` page → both load normally (previously any active snooze took the bell down too)
- [ ] Let/ set the snooze to expire (or Check the item) → the item reappears in the queue as expected

### Consumption-event recording restored (cook-mode depletion) — origin FU-533
- [ ] Set a stock item to a full/high level, then **cook a recipe that uses it** (or manually drop its level with a consumption source) so the level DROPS → the depletion is recorded: the item's run-out prediction / "your prices" depletion signal reflects the drop (previously a sourced drop silently recorded nothing)
- [ ] On a stock item, **re-confirm the SAME level** (tap the current level again) → the level-history timeline does NOT gain a phantom "Stocked → Stocked" entry (only the "last checked" stamp bumps)
- [ ] PATCH a recipe's cuisine/category/collection to empty (clear it in the edit form) → the link actually clears and stays cleared after refresh

### Rename-to-own-name fix (str/UUID 422) — origin FU-528 family
- [ ] Open the edit dialog for a **stock item**, change some other field (e.g. notes) but leave the **name** untouched, and save → saves cleanly (previously 422'd "already exists")
- [ ] Same check on a **recipe** (rename dialog, keep the same name), a **stock location**, a **store**, and (as admin) a **user's username** → all save without a spurious duplicate error
- [ ] Sanity: renaming one entity to a *genuinely* existing OTHER entity's name still shows the duplicate error (the guard still works)

### Unlinked-ingredients page loads — origin FU-532/fuzz
- [ ] Navigate to whatever surfaces the "ingredients not linked to stock" review (recipe ingredient linking) → the list loads instead of erroring (the backing `GET /api/recipes/unlinked-ingredients` was 500-ing on every request)

### Reconcile-queue pagination — origin fuzz
- [ ] With enough unresolved past-day meal entries to paginate (>1 page), open the meal-plan reconcile queue and page through → no error, next page loads (cursor previously 500'd on SQLite the moment the queue paginated)

### Expiry-on-open prompt — origin FU-507
- [ ] On a stock item's row, tap the **open / lock** icon on a currently-sealed item — a dialog appears titled **Marking "&lt;name&gt;" as open** with the current expiry prefilled in a date picker and the message "Update its effective expiry?"
- [ ] Pick a new date and tap **Update expiry** → row is marked open AND the new expiry saves (row's expiry chip reflects it)
- [ ] Repeat but tap **Skip** → row is marked open, expiry is unchanged
- [ ] On the stock-item **Detail page**, flip the **Opened** toggle → same dialog fires, same behaviour
- [ ] Toggle a currently-open item back to sealed → **no dialog** (the prompt only fires on open, not on close)

### StockItem.image feature dropped — origin FU-508
- [ ] Stock overview: no image thumbnail column on rows; no "Show row images" / "Hide row images" toggle button in the toolbar next to search
- [ ] Stock-item detail page: no image upload field on the Overview tab (the fact list starts at Name)
- [ ] Nothing calls `/api/stock-items/&lt;id&gt;/image` — network tab clean on stock pages
- [ ] Recipes still render their images; user avatars still render; store logos still render (these are separate features and must be untouched)

### Stocktake redesign — Chunk 3 Settings + Stock Overview surfacing — origin PROPOSAL_STOCKTAKE_MODE
*Verifies the Settings block + Overview filter chip + row pulse outline. Chunk 3 lands the surfaces users find the redesign from.*

**Settings → Stocktake page**
- [ ] Navigate to **Settings → Admin → System → Stocktake** — the nav entry appears with the clipboard-check icon, between "Alert thresholds" and "AI assistant"
- [ ] Page loads with title **"Stocktake"** and a description "How often Dora asks you to check each item…"
- [ ] **Default check cadence** section: three-button toggle showing **Weekly / Fortnightly / Monthly** with the current setting highlighted (Fortnightly on a fresh install)
- [ ] Tap **Weekly** → button becomes active, positive toast fires **"Default cadence saved."** — refresh the page and the change persists
- [ ] Tap **Monthly** → same behaviour, and the previous **Weekly** button de-activates
- [ ] **Auto self-tuning** section: a `q-toggle` (on by default). Flip off → positive toast **"Auto self-tuning off."** — refresh and it stays off
- [ ] Flip back on → toast reads **"Auto self-tuning on."**
- [ ] Non-admin user visits the page → the red admin-permissions banner shows, the sections don't render
- [ ] With Auto **off**, run stocktake — every item's cadence is the global default (adjusted by Essential = one band faster if flagged)
- [ ] With Auto **on**, an item with recent frequent level changes moves into a shorter cadence band on next queue rebuild (verify by looking at what the runner shows as "Checked every week/fortnight/month")

**Alert thresholds — clean removal**
- [ ] Navigate to **Settings → Admin → System → Alert thresholds** — the **"Default stocktake reminder"** section (the numeric-days input) is **gone**; only "Expiring-soon window" remains
- [ ] Expiring-soon window still edits + saves correctly (regression check)

**Stock Overview — "Needs check" quick-filter**
- [ ] On **Stock Overview**, expand the filter panel → a new **"Needs check"** chip appears in the chip strip, positioned after "Needs attention", with the clipboard-check icon
- [ ] With chip **off**: full pantry visible
- [ ] Toggle chip **on**: view narrows to only the items currently in the stocktake queue (the same set surfaced by the runner)
- [ ] The count matches: with the filter on, the visible row count equals what the toolbar's Stocktake button says (e.g. "Stocktake (12)")
- [ ] Toggle chip off: full list returns

**Stock Overview — pulse outline around stock-level button**
- [ ] An item that IS in the stocktake queue: its **stock-level button** (the small coloured square left of the item name) has a **subtle pulsing outline** — a soft accent-coloured halo that grows and fades on a 2-second cycle
- [ ] An item NOT in the stocktake queue: no pulse, no outline
- [ ] After tapping **Still correct** in the runner for an item, return to Stock Overview and refresh — its pulse is gone (item left the queue)
- [ ] With `prefers-reduced-motion` on (browser accessibility setting): items still show the outline, but as a **static** ring (no animation) — verify by enabling reduced-motion in devtools and confirming no pulsing
- [ ] Dark mode: the pulse colour still reads well against the darker surface (uses `--brand-accent` theme token)
- [ ] Light mode: same — the halo is visible without being loud

### Stocktake redesign — Chunk 2 SPA runner rebuild — origin PROPOSAL_STOCKTAKE_MODE
*Verifies the redesigned stocktake mode: new engagement gate + cadence bands + buttons + completion screen. Chunk 3 (Settings + Stock Overview surfacing) is not yet built.*

**Landing gone / empty state**
- [ ] Tap **Stocktake** from the left nav (or hit `/stocktake` directly) → the runner opens **immediately** on the first item; no intermediate "N items need a check" landing
- [ ] Legacy bookmark to `/stocktake/run` → redirects to `/stocktake` and behaves identically
- [ ] With nothing overdue (fresh install / everything Checked): runner shows the **"You're all caught up."** card with a Back-to-Stock button — no crash, no infinite spinner
- [ ] Close **X** in the runner topbar → returns to `/stock`

**Runner card + buttons**
- [ ] Item card shows: name (large), location (or "No location"), and a caption line like **"Checked every fortnight · N days overdue"** — plural/singular correct for 1 day vs many
- [ ] **Row 1 — two big buttons side by side:** **Still correct** (green/positive) and **Change level**
- [ ] The **Change level** button is **tinted to the current level's colour** (Stocked → positive/green, Low → negative/red, Out → neutral/muted) and shows the level's **name** with a small **"(change)"** underneath
- [ ] **Row 2 — three smaller ghost buttons:** **Skip** / **Push 3 days** / **Mute**
- [ ] No **Out of stock** button anywhere (it's a level in the picker now)
- [ ] No **keyboard shortcuts** shown on the buttons; pressing `1`/`2`/`3`/`s` does **nothing**
- [ ] No **Add to list** button on the card (it moved to the completion screen)

**Still correct**
- [ ] Tap **Still correct** → server logs the check, card advances to next item, no visible toast (it's the mainline action, doesn't need one)
- [ ] After a Still-correct action, refresh the queue → the same item does NOT resurface (its clock reset)

**Change level (picker)**
- [ ] Tap **Change level** → dialog opens titled **Set level**, listing every configured level with a **coloured dot on the left** (matches Stock Overview colours pixel-for-pixel)
- [ ] Pick a level → level updates, card advances
- [ ] Change to **Low** or **Out** during a session → item name gets tracked for the completion-screen batch add-to-list (see below)
- [ ] Change back to **Stocked** (or any non-Low/Out) on the same item within the session → item is **removed** from the completion-screen list (dedupe / last-write-wins)

**Skip (session-only)**
- [ ] Tap **Skip** on the first item → card advances, no API call fires (verify in Network tab)
- [ ] Continue skipping through the whole queue → the skipped items **come back at the end**, in the order you skipped them
- [ ] Refresh the page → skips are gone (session-only); the original queue rebuilds fresh

**Push 3 days**
- [ ] Tap **Push 3 days** → `POST /stock-items/<id>/snooze` fires; card advances; item's `last_checked_at` is **unchanged** (verify in DB or via item detail)
- [ ] Refresh the queue → the pushed item does NOT resurface (its `snoozed_until` is 3 days in the future)
- [ ] On a pushed item, hit **Still correct** or **Change level** via any surface → the snooze is **cleared** automatically (Check is stronger than Push)

**Mute (with confirmation)**
- [ ] Tap **Mute** → a confirmation dialog appears with message **"Dora will stop asking about this item entirely. You can un-mute it later from the item's detail page."** and a red **Mute** confirm button
- [ ] Cancel the dialog → nothing changes; card stays on the same item
- [ ] Confirm the dialog → `stocktake_alerts_are_enabled` flips to `false` on the item; card advances
- [ ] Refresh the queue → muted item does NOT resurface (permanent until un-muted from item detail)

**(?) Help affordance**
- [ ] Tap the **?** icon in the topbar → dialog opens titled **How stocktake works** with a definition list covering all five verbs + a footer note about cadence bands / Auto
- [ ] Close and re-open — nothing sticky, no state leaked

**Completion screen**
- [ ] Walk through every item in the queue (any mix of the 5 verbs) → after the last item, the **completion card** replaces the item card
- [ ] Completion card shows the 5 counters — **checked / changed / skipped / pushed / muted** — with the right totals matching what you did
- [ ] If you Changed **≥ 1** item to Low or Out during the session, a prompt appears: **"N items went Low or Out. Add them to a shopping list?"** with an **"Add to list…"** button
- [ ] Tap **Add to list…** → radio dialog listing every active (non-done) shopping list. Pick one, confirm → all tracked items are added; the button shows an **"Added."** confirmation and disables (can't double-fire)
- [ ] With **0 active lists**, the button surfaces an info toast: "No active lists. Create one first."
- [ ] With **0 Low/Out items** in the session, the add-to-list prompt does NOT appear
- [ ] Tap **Done** → returns to `/stock`

### Bulk "Log waste…" on Stock Overview — origin FU-226 chat
*Verifies the new bulk waste action in the Stock Overview bulk-select bar.*
- [ ] Enter bulk-select mode (long-press a row on mobile, or the toolbar toggle on desktop) → select 3 items, at least one with an expiry date set and at least one without → the "Log waste…" button in the bulk bar is enabled and shows the trash icon
- [ ] Tap "Log waste…" → the MarkAsWastedDialog opens with the header **"Why did this go to waste?"**, subject line reads **"3 items"**, and a subline **"One reason applies to every selected item."**
- [ ] Tap one of the four primary reason tiles (e.g. **Spoiled**) → dialog closes; bulk-select mode exits; one summary toast fires **"Logged 3 items as wasted."** with an **Undo** action
- [ ] Open **Reports → waste-insights** (or the Dashboard "recently wasted" surface): the 3 items appear with reason `spoiled` and the same `occurred_at`; the item that had an expiry date now shows expiry cleared on Stock Overview
- [ ] Repeat the flow with **4 items** → tap **Undo** on the summary toast → *all 4* waste events are removed from insights and any previously-set expiry dates are restored on the affected rows (positive "Undone." toast)
- [ ] With 0 items selected, the "Log waste…" button is **disabled** (grey, no click) — matches the other bulk actions
- [ ] "Log waste…" with a single item selected → summary reads **"Logged 1 item as wasted."** (singular)
- [ ] Sanity — the single-item "Log waste" from the row's expiry menu still works and still shows the per-item toast + Undo (bulk path didn't regress the single path)

### Auto-add-on-low toast + line chip — origin FU-315 (re-verify: FU-464 fixed a Low-transition regression 2026-07-04; FU-511 collapsed the per-item toggle to an install-wide 3-state setting 2026-07-07)
*Auto-add is now controlled by **Settings → Admin → System → Stock** — three modes:*
*`Off` never fires. `Essential only` (default) fires only for items with the Essential flag on. `All items` fires on any Stocked → Low/Out transition. Server owns the branching in `update_stock_item._try_auto_add`.*

*For the toast-behaviour checks below, set the install to `Essential only` (default) and use a stock item with the Essential flag on and exactly one open draft shopping list.*
- [ ] Settings → Admin → System → Stock loads; the three-way toggle reads the current mode; switching between modes saves eagerly (positive toast) and survives a hard refresh
- [ ] From stock overview, tap the stock-level chip on a Stocked Essential item → set it to **Low** → positive toast fires **"Added *<item>* to *<draft list display_name>*."** with caption "Auto-added because it went low." (not a silent add)
- [ ] Same setup but set to **Out** on an item that was already Stocked → same toast fires
- [ ] Open the draft list → the new line renders **without a manual refresh** (the store refreshed itself)
- [ ] Line shows an `auto: low stock` chip at normal density — visible next to the item name, not crowded out by price / quantity chips
- [ ] Switch mode to **Off**, then set a Stocked Essential item to Low → **no toast fires**
- [ ] Switch mode to **All items**, then set a Stocked *non-Essential* item to Low → toast fires (previously it wouldn't have — this is the deliberate 3-state expansion)
- [ ] Switch mode back to **Essential only**, then set a Stocked *non-Essential* item to Low → **no toast fires**
- [ ] Set an Essential item to Low when it's already on any active shopping list → no toast (server dedup: "user already knows")
- [ ] Set an Essential item to Low when the user has **0 draft lists** or **2+ draft lists** → no toast (server only auto-adds when the target is unambiguous)
- [ ] Item level change on the detail page (Level row) → toast fires the same way (`updateStockItemAsync` path)
- [ ] Cook mode's per-ingredient level decrement that flips an ingredient to Low → toast fires per triggered item (multiple toasts stack — verify readability)
- [ ] Offline stock-level flip → queued (blue "Queued: Update stock level" toast); when back online + queue drains → auto-add toast fires *if* the flipped item genuinely transitions on the server side and the mode allows it
- [ ] Stock overview no longer shows the "Will auto-add on low" filter chip or the "Auto-add" footer count (both retired with the per-item toggle)
- [ ] Stock-item detail page no longer shows an "Auto-add when low" toggle row (Essential flag remains; the auto-add branching happens off it plus the install-wide mode)

### ⭐ Zero-Input Pantry — inferred inventory (P8-07) — origin champion plan
Server-env first (no Python here): `alembic upgrade head` applies `f2a9c4d7e1b8` (ConsumptionEvent) + `a3e8b1f6c2d9` (User.inferred_pantry_enabled) on SQLite **and** Postgres; `verify_mappings()` passes for `ConsumptionEvent`; `pytest tests/test_pantry_belief.py` green.
- [ ] Preferences → Pantry: "Infer stock levels" toggle is present and defaults ON for a fresh account; flipping it persists across reload
- [ ] With inference ON, stock overview rows show a "Dora: ~Band · confidence" chip beside items that have purchase history; tooltip shows the reason (e.g. "~Low — bought 11 days ago; you usually finish in about 14 days")
- [ ] With inference OFF, no belief chip renders anywhere and `GET /api/stock-items/beliefs` returns `{enabled:false, beliefs:{}}`
- [ ] Items with no history / freshly-created show either no chip or a low-confidence "not enough history" reason — never a confident wrong band
- [ ] Buy an item (finish a shop with it ticked + priced), reload → its belief reads Stocked with a recent-purchase reason
- [ ] Cook a recipe using that item (finish dialog → mark it "down one"/"out") → a ConsumptionEvent is written; the item's belief drifts more depleted than purchase cadence alone would, and the reason mentions "cooked with N× since"
- [ ] Manually change an item's level (or run a stocktake quick-check) → the chip immediately reflects the recorded level at HIGH confidence with "You confirmed this…"/"Updated…" and no "differs" outline (override wins)
- [ ] Let an item go well past its usual cadence with no check → belief drifts to ~Out; if the recorded level still says Stocked the chip shows the warning outline ("differs from recorded")
- [ ] Add an uncertain item to a draft shopping list → a single "Still have X?" quick-check appears in the suggestions inbox (not a bulk prompt); its action opens the item; dismiss/snooze work; capped at 3 across all in-play items
- [ ] Plan a meal this week whose ingredient is uncertain → same quick-check fires via the cook-decision path
- [ ] Dark-mode + non-money themes: chip colours ride semantic tokens (positive/warning/negative dots), no hardcoded colour
- [ ] Backup → restore: ConsumptionEvent is an event log (like CookEvent) and intentionally NOT in the backup sections — confirm restore still succeeds and beliefs recompute from surviving purchases/cooks

### 3-band StockLevel collapse (Sufficient axed, 2026-07-02)
- [ ] Finishing a shopping list — every ticked item flips to "Stocked" (was "Well-Stocked"). No level-override UI still labels a "Sufficient" middle option
- [ ] Restock-review modal on shopping-list finish: only 3 options per item (Stocked / Low / Out)
- [ ] Alerts "Mark as restocked" action — the item's level becomes "Stocked"
- [ ] Stocktake "Set all ticked to Stocked" (the shopping-list review-complete flow) — API request body carries `set_stocked: true` (verify in DevTools network); response body reads `{set_stocked: N, checked: N}`
- [ ] Spreadsheet import (Settings → Data → Import) — items with a blank Level column default to "Stocked" (was "Sufficient Stock"). Items with "Stocked" / "Low" / "Out of stock" in the Level column parse correctly
- [ ] Assistant chat: say "mark milk as sufficient" — assistant proposes setting milk to **Stocked** (the "sufficient" NLU alias now resolves to STOCKED). Similarly "ok" / "fine" / "well stocked" all resolve to Stocked
- [ ] Recipe cookability: an ingredient at Low stock still counts the recipe as cookable (Low ≠ missing); at Out of Stock the recipe is not cookable
- [ ] Onboarding "Restock" scene copy reads "Finishing the shop bumps what you bought back to stocked — no re-counting" (was "well-stocked")
- [ ] Buy-verdict popover on a Stocked item: reads "Stocked" as the need-axis label (was "Well stocked")

### P8-05 "Should I buy?" buy-verdict oracle
*Needs a seed with plausible price history + a few waste events. `buy_verdict_enabled` defaults on.*
- [ ] **Feature flag** — Settings → System → Features → toggle "Should I buy? oracle" **off**. Reload Stock Overview: no badges anywhere. Toggle **on** again: badges reappear.
- [ ] **Silent on low-confidence** — pick an item with < 3 shopping-list price samples. The badge does **not** render on its row (verify in DevTools: `/buy-verdict` request fires and returns `confidence: "low"`, but the row shows nothing).
- [ ] **Out-of-stock → buy (high)** — mark an item Out of Stock. Its row renders a green **Buy** badge with confidence `high`. Popover shows "You're out of stock" as the first reason. One-tap "Add to primary list" — verify the item lands on the current quick-add-target list; the badge refreshes (may briefly show the *new* verdict factoring in the fact that it's on a list).
- [ ] **Stocked + wasteful → skip (high)** — pick a stocked item, log 3+ waste events on it (`POST /waste/events` or via the row expiry menu). Rescan the overview: badge is red **Skip**. Popover reason: "You've wasted this ~N% of the time". One-tap label reads "Already stocked" (or "Remove from list" if it happens to be on an open list).
- [ ] **Low-stock + cheap price → buy (high)** — mark an item Low Stock and log a shopping-list line with price ≤ 92% of its average. Badge is green **Buy** with confidence `high`. Popover reasons: "Running low" + "Cheapest you've paid in 3 months".
- [ ] **Stocked + above usual → wait (medium)** — mark an item Stocked and log a recent purchase ≥ 108% of its average. Badge is orange **Wait**. Popover reason: "Above your usual price". Detail line quotes `$last vs $usual`.
- [ ] **Thin data collapse** — pick a brand-new stock item with no history. Badge should render **only** if the oracle managed to produce a non-low-confidence verdict; typically it should be silent. Force-open the item's `/buy-verdict` in a browser: response reads `verdict: "unsure", confidence: "low", reasons: [{signal: "thin_data"}]`.
- [ ] **In-shop consumer** — open a draft shopping list with a stocked-and-wasteful item on it. The line-row badge reads **Skip**. Popover one-tap action reads "Remove from list"; tapping it calls the existing `onRemoveLine` handler and the line disappears with the same toast the normal remove uses.
- [ ] **Cache behaviour** — reload Stock Overview twice quickly. Backend logs show one `/buy-verdict` request per item on first paint; the second paint hits the module-level cache (no additional requests within the 5-min stale window unless a mutation invalidated an entry).
- [ ] **Mutation invalidation** — add an item to a list via the row's cart button. Its badge refreshes (may flip verdict / hide entirely if the new `is_on_open_list` state changes the one-tap action). Backend log confirms a fresh `/buy-verdict` request after `invalidateBuyVerdict(id)`.

### P8-02 barcode-to-add via Open Food Facts
*Requires `scanning_enabled=true` (Settings → System) and a real camera + real packaged-product barcodes.*
- [ ] **Already-mapped, direct** — scan an EAN already registered against a stock item (Stock item → Barcodes section). Expected: navigate straight to that item's detail page. No dialog. In DevTools network tab: `/api/data/barcodes/lookup` hit, **no** `/api/data/products/off-lookup` hit.
- [ ] **Already-mapped, via Product** — scan an EAN registered against a Product that's linked to a stock item. Expected: same as above (navigate to the linked item; no dialog; no OFF call).
- [ ] **Product-no-link** — scan an EAN registered against a Product with no linked stock item. Expected: Add-Item dialog opens with the barcode-only prefill and a "matches a known product" note. **No OFF call in network tab.** Confirm → new stock item created + EAN now linked to it.
- [ ] **Unknown EAN, OFF hit** — scan a real cereal/beverage/pantry barcode Dora doesn't know. Expected: OFF network hit; dialog opens with name, brand, image, category seeded and a "Suggested from Open Food Facts — review and confirm" banner. Confirm → new stock item created + EAN now registered → rescanning jumps straight to the new item.
- [ ] **Cache** — immediately rescan the same code from step above. Expected: dialog shows identical suggestion; server logs show the OFF request served from cache (no outbound OFF call).
- [ ] **Unknown EAN, OFF miss** — scan a made-up but plausible 13-digit numeric string. Expected: OFF returns `{found: false}`; dialog opens with barcode-only fallback + generic banner. Confirm → item created + EAN registered.
- [ ] **OFF network failure** — kill wifi / block `world.openfoodfacts.org` at the host level. Rescan an unknown EAN. Expected: same barcode-only fallback as OFF-miss; **no error toast**; item creates cleanly.
- [ ] **Scanning off** — flip `scanning_enabled=false` in Settings → System. Stock Overview no longer shows the scan button; the OFF endpoint stays reachable but there's no UI path to it. (Server-side gating of the endpoint itself is deliberately absent — matches `/barcodes/lookup`.)
- [ ] **Charter honesty** — the "Suggested from Open Food Facts" banner is clearly labelled and the image is a *preview*, not silently ingested. After confirm, `StockItem.image` is empty (FU-033 image seam is separate); user can add the image manually.

### History tab — retention, cap, and truncation footer — origin 2026-06-30 feedback
*Requires a fresh dev seed (drop `dora.db` with `DORA_ALLOW_DESTRUCTIVE=1` then reseed).*
- [ ] Stock Overview → search **"Sriracha (chatty history test)"** → open detail → History tab → the timeline renders **50 expiry events** (server-capped) with a small muted footer at the bottom reading *"16 older events not shown"*
- [ ] The 50 rendered events are the newest ones (occurred_at desc); the oldest visible event is well within the last 90 days but not the earliest (that one was dropped past the cap)
- [ ] Same page reload → footer count stays exactly the same (the count is server-derived, not client-drift)
- [ ] Any item with < 50 events per kind → NO footer renders (empty state hidden when `history_older_count === 0`)
- [ ] **Milk** detail → History shows a populated mix: level-changes, purchase events (from the seeded finished lists), expiry set + 2 pushes, one waste event ("spoiled" 45 days ago). No footer (well under the cap on every kind)
- [ ] **Pasta / Rice / Garlic** detail → History shows *"Used in <recipe>"* deep-orange entries for the seeded cook events (aglio, simple_pasta, stir_fry, fried_rice — whichever recipes reference that ingredient)
- [ ] **Broccoli / Icecream / Brazil Nuts** detail → History shows one waste event each in negative-red
- [ ] Cook events with `meals_cooked > 1` badge *"× N meals"* in the title
- [ ] Footer copy pluralises: 1 event → "1 older event not shown"; 2+ → "N older events not shown"

### History tab — Bought / Cook / Expiry events — origin 2026-06-30 feedback
*Requires a fresh migration pass: `flask db upgrade` picks up
`c3d7f1a2b8e4` (CookEvent) + `d4e8f2b1c9a5` (StockItemExpiryEvent).*
- [ ] **Expiry: set** — create a new stock item with an expiry date set. History tab → newest entry is *"Set expiry"* with the date in the body, orange
- [ ] **Expiry: pushed** — on the detail page, edit expiry to a later date (or use the row menu's Push +7 days on the overview). History gets *"Pushed expiry +7 days"* with body *"YYYY-MM-DD → YYYY-MM-DD"*
- [ ] **Expiry: cleared** — clear the expiry (row menu Clear expiry or detail Set-expiry dialog's Clear button). History gets *"Cleared expiry"* in grey with body *"Was YYYY-MM-DD"*
- [ ] **Expiry: no-op** — save the same date again → NO new History entry (a save that doesn't change the value must not emit)
- [ ] **Bought** — with an item that's on a shopping list: Start shopping → tick the item → Finish & restock. History gets *"Bought · &lt;list name&gt;"* with `2× · $2.10/ea · at Coles` (or whichever fields the Finish flow captured); teal icon
- [ ] **Bought — price/store optional** — the Finish flow leaves till-total or store blank → still emits a "Bought" entry, just with fewer body chips (or none — title still renders)
- [ ] **Cooked** — cook a recipe that lists this stock item as an ingredient (via cook mode's Log meals or the recipe detail Log-a-cook action). History gets *"Used in &lt;recipe name&gt;"* deep-orange; batch cook (>1 meal) badges *"× N meals"*
- [ ] **Cook — item not an ingredient** — cook a recipe that DOESN'T reference this stock item as an ingredient → NO cook entry appears on this item's timeline (the join is via `RecipeIngredient.stock_item_id`, not a wildcard)
- [ ] **Timeline ordering** — all three new event kinds interleave date-sorted (newest first) with the existing level changes / waste / list-adds; nothing gets a separate section
- [ ] **Cap** — after >20 events of any single kind, only the most recent 20 render (server-capped; check the response body if unsure)
- [ ] **Migration downgrade** — `flask db downgrade` runs cleanly through both new migrations (drops indexes then tables). Not required to test in normal use, but the R-006 close-gate wants forward-only clean migrations that CAN reverse cleanly

### Stock pickers + Log Waste — overview/dialog/detail consistency — origin 2026-06-30 feedback
- [ ] Stock Overview → expand the filter panel → **Any level** dropdown trigger shows a coloured dot to the left of the picked level (or the muted sunken-bg dot when "Any level" is cleared). Open the dropdown → every option row has the same dot styling, matching the Stock Item detail page's Level picker pixel-for-pixel
- [ ] Click "Add stock item" on the overview → in the dialog the **Stock level** q-select shows the picked level's dot in the trigger, and each option in the dropdown has the same dot. Pick a different level → trigger dot updates instantly
- [ ] On a row's expiry-menu (the calendar-icon kebab), the entry under **Clear expiry** now reads **Log waste** and renders in destructive-red (icon + label both red), visually matching Clear expiry. Click it → the existing waste-reason tile dialog still opens unchanged
- [ ] Stock Item detail page → Level picker still works (the refactor swapped inline avatars for the shared `StockLevelDot` component); changing level updates the dot's colour, "Updated just now" stamp refreshes
- [ ] No console warnings about missing slot props / undefined sequences when the level filter is cleared (the sunken-bg fallback should kick in silently)

### Recipe-ingredients deep-link filter — origin FU-109 close-out
- [ ] Open a stock-item detail page → Recipes-using-this tab. Every recipe card carries a filter icon between the favourite heart and the cook button. Hover tooltip: "Filter stock to this recipe's ingredients"
- [ ] Click that filter icon → lands on Stock Overview with `?recipe=<id>` in the URL, filter panel auto-opens, removable chip reads "Ingredients of: &lt;recipe name&gt;" with a menu-book icon
- [ ] The list narrows to the recipe's ingredient stock items (combine with other filters, e.g. level/location, still works)
- [ ] Click the chip's × → filter clears, chip disappears, URL no longer has `?recipe=`. Refresh/back doesn't reinstate
- [ ] "Clear filters" on the FilterBar also strips `?recipe=` (not just zeroes the chip)
- [ ] Pasting `/stock?recipe=<bogus-id>` doesn't blank the list — the unresolved id silently disables the filter (no chip rendered)
- [ ] RecipeCard's filter button is **only** on the stock-item-detail Recipes tab — not on Cookbook overview, Meal Plan recipe picker, or anywhere else `RecipeCard` is rendered

### Recipe card no longer dims on incomplete-set surfaces — origin FU-109
- [ ] Stock-item detail → Recipes tab: cards never render at reduced opacity, regardless of whether restocking this single item would make them cookable. The "Missing N ingredients" copy on the card face is the only signal
- [ ] Cookbook overview with "Uses ingredients" filter active: same — no dim

### Stock Item Detail — C-1b focused pass + C-1b.1 marquee — origin FU-202
- [ ] Header: back/close · name · (Show QR if scanning on) · Delete. Secondary toolbar row (Mark open / Set expiry / Add to list) GONE. Level chip no longer in header — lives under Name on Overview tab
- [ ] Level row sits between Name and Location; dropdown opens, picks a level, "Updated X ago" refreshes to "just now" on save
- [ ] Location / Stock group clear: with a location set, click picker × (and `Tab`-blur after deleting text) → picker stays empty after refresh. Same for stock group. Network tab shows `{"clear_stock_location": true}` / `{"clear_stock_group": true}`
- [ ] "—" placeholders on Location / Stock group / Usual store / Expiry / Level when unset
- [ ] Notes reads as a row in basics list (auto-grows on type, blur saves)
- [ ] Padding — full-page and embedded peek mode breathe (q-pa-md); nothing touches edge
- [ ] DoraTabs sliding underline: switching tabs slides + wobbles, settles to accent. Same on `pages/data/BarcodesQR.vue` and `HelpPage.vue`
- [ ] Splitter peek opens at 50%; clamped to [40%, 65%] while peeking; closing restores list to 100%
- [ ] **C-1b.5 lifecycle timeline:** History tab shows multiple event kinds (level changes with Restocked/Dropped labels, waste events, past list-adds with provenance, synthetic Opened entry when open). Empty items: "Nothing logged for this item yet…". Busy item: newest → oldest, capped sensibly
- [ ] **C-1b.4 Recipes tab:** heart toggles favourite (and remove); on cookable recipe, "Add all to list" lands every ingredient on primary draft. Lists tab: dead `open_in_new` gone; primary draft has styled Primary badge. Substitutes: per-row "Swap into list" gone; Remove still works; curated list stays
- [ ] **C-1b.3 Products tab:** empty Products → centred Find & link a product CTA → seeded `/product-search?q=<name>`; non-empty shows quieter Link another in header; cheapest linked product visually highlighted (chip + tinted card); no Get cheapest toolbar button; with Products off, the Products tab disappears entirely + a stranded `?section=products` URL falls back to Overview
- [ ] **C-1b.1 marquee:** header has back/close · name · level chip = editor (click → menu) · space · Delete top-right (danger-ghost) in both modes
- [ ] Toolbar: Mark open · Set expiry · Add-to-list · (Show QR) — no Restock, no Find-deals
- [ ] Overview is a single column where every row is its own editor: name (blur saves), location, stock group (new), expiry value + ±1d/+7d/+14d + date dialog + × clear, open toggle with "Opened {date}" + tooltip, essential toggle, auto-add toggle, level-updated read-only, Notes calm at bottom
- [ ] Editors save immediately on change/blur without a Save button — toggle/select round-trips and page reflects the new value
- [ ] Unsaved-changes guard still fires for in-progress text edits (name/notes)
- [ ] Tabs legible in light + dark + any other theme (active tab + indicator stay readable)
- [ ] Show QR tooltip explains the QR vs real-barcode distinction
- [ ] **Round-2 additions:**
  - [ ] Level updated really updates — "Updated X ago" flips to "just now", then drifts forward; same on Stock Overview row
  - [ ] Splitter gripper reachable on long lists — dots stay centred on viewport (sticky)
  - [ ] Overview tab's image / inputs have even breathing room
  - [ ] Peek panel scroll: whole detail panel scrolls with the page; nothing scrolls inside the panel; name + Delete never hidden
  - [ ] DoraTabs hover: inactive tab text transitions to accent, no surface-tint background
  - [ ] Footer counts: Stocked (positive), Low (negative), Out (muted/grey); "Auto-add" default text colour like "Shown"; label is "Essential" (not Flagged); sits between level stats and Auto-add
  - [ ] Row buttons cluster: expiry / flag / open / cart same round shape + size. Click flag → toggles essential (left stripe + warning-tint icon)

### Stock Item Detail + Stock Overview feedback pass — origin FU-222
- [ ] Stock Overview row — image / level / name have visible breathing room; right cluster (expiry, open, cart) larger; recipe-count chip gone; hover no longer "lifts" — surface tints + border picks up accent; first row's outline doesn't clip under page chrome
- [ ] Essential indicator: flag → 3px warning stripe on left edge + flag icon in right cluster
- [ ] Open icon pops in Pesto dark (primary, not barely-visible secondary)
- [ ] Footer counts: "Shown" reads in default text colour (not primary); per-level counts use stock-level palette; Flagged / Auto-add / Needs attention keep semantic tones
- [ ] Filter toggle on Stock Overview, My Products, Cookbook overview: "Filters" button + badge + "Clear" all in main toolbar row; no second toolbar row above the filter panel

### Stock Overview Chunk 2 — top toolbar + filters + footer — origin FU-121
- [ ] Top toolbar order: New item · Scan · Stocktake · Bulk select · Export · (spacer) · Search. Bulk select shows "Cancel" once on
- [ ] Filter panel state remembered per page: toggle open on Stock Overview (desktop), reload — panel stays open. Toggle closed, reload — panel stays closed. Independent state across Stock Overview / My Products / Cookbook overview
- [ ] Mobile (< md): every filterable page starts with the panel hidden regardless of the desktop-saved state. Can still open in-session via the Filters button, but a reload returns it to hidden
- [ ] Clear filters button sits to the LEFT of the Filters button on every filterable page; toggling filters on/off makes Clear appear/disappear without the Filters button shifting position
- [ ] Level filter is a single "Any level" dropdown; selecting filters; clearable; no floating count badges
- [ ] "Used in a recipe" filter is gone
- [ ] Search placeholder reads "Search" (no parenthesised hint)
- [ ] Footer counts in order: Shown · Stocked · Low · Out · Flagged · Auto-add · Needs attention. Reflect filtered set; recompute live
- [ ] No console errors from dropped `usedInRecipeOnly` / `getStockLevelColour` references

### Stock Overview Chunk 4 — expiry control — origin FU-123
- [ ] No expiry set → tap expiry button → q-date picker (popup on desktop, dialog on mobile). Picking future date PATCHes + row reflects new date (icon tone via existing logic); past blocked by `dateOptionsFuture`
- [ ] Expiry set → tap → menu: **+1 day · +7 days · +14 days · Clear** (no +30). Each PATCH the right ISO; Clear nulls + button reverts to date-picker state
- [ ] Tone outline flips: <7 days future → `stock-row--warn` (amber); past → `stock-row--alert` (red)
- [ ] No regressions on right-cluster (#recipes, open/in-use, cart)
- [ ] +X push semantics (FU-123 follow-on): item with future expiry (e.g. +5 days) → "+1 day" PATCHes to current+1 (not today+1); "+7 days" PATCHes to current+7. Item with past expiry → "+1 day" PATCHes to **tomorrow** (max(today, current) + 1), not yesterday
- [ ] Detail-panel peek staleness (FU-123 follow-on): open the peek for an item, then in the row use the expiry menu (+1 day), the open-toggle, the flag-toggle, and the level dropdown. Peek's matching field updates **without** closing/reopening the peek. Same when the page is opened full-screen on mobile and the row mutation happens via a different surface

### Stock Overview Chunk 5 — responsive detail nav + long-press — origin FU-124
- [ ] Desktop (≥ md): tap row → splitter peek opens with shared `StockItemDetailPage` embedded; tap again → closes
- [ ] Mobile (< md): tap row → full-page nav to `/stock/<id>`; no drawer/peek; same `StockItemDetailPage` renders non-embedded; back returns to overview with state preserved
- [ ] Bulk mode (any breakpoint): tap toggles selection (no nav, no peek)
- [ ] Long-press on mobile: enters bulk-select + ticks held item; subsequent taps add/remove; Cancel exits
- [ ] Long-press on desktop: no-op (`<md` guard)
- [ ] Resize across md breakpoint while a peek open — peek stays attached; future row-taps use the new breakpoint's behaviour

### Offers sidecar — origin FU-230
- [ ] During chunk-8 C5 state-matrix walk: open a stock item linked to a product with a current offer (e.g. seeded Milk or Olive Oil) with money on; the widget shows "Current shelf prices: …"

---

## Dashboard

### Draft my shop — one-click card — origin FU-351
- [ ] Dashboard renders a **Draft this week's shop** card in the `act` zone (between Attention and Suggestions) — icon: playlist-check
- [ ] Card body shows the blurb ("One-click starter list — meal plan for the next 7 days, plus anything low, out, or flagged as an essential. Nothing shopped yet; you edit before heading out.") + a **Draft my shop** button (auto-fix icon)
- [ ] Happy path — with an active meal plan (at least one recipe scheduled today+6d), at least one Low/Out stock item, and at least one flagged essential: click Draft my shop → button spins → positive toast "Drafted N items." (caption "Review the list, then start shopping when ready.") → SPA navigates to the newly-created draft's detail page
- [ ] New list appears in the sidebar list-selector under the name `Weekly shop · <weekday> <day> <month>` (e.g. "Weekly shop · Sat 12 Jul") — not the generic "Auto N · date"
- [ ] On the detail page, every produced line renders the existing `added_via` chip — meal-planned recipes' items get "auto: meal plan", low/out items get "auto: low stock", flagged items get "auto: flagged" (with the priority rule: recipe > meal plan > flagged > essential > low stock > frequently added, so an item on both the meal plan and low gets "auto: meal plan")
- [ ] Empty case — a fresh account with no meal plan, no low stock, and no essentials: click Draft my shop → button spins → info toast "Nothing to draft yet." (caption "Plan some meals, or mark items as essential — then try again.") → **stays on the dashboard** (no navigation) → sidebar list-selector shows **no phantom "Weekly shop · …" empty list** (the /auto-generate handler defers list creation on the create-new path until candidates exist)
- [ ] Error case — force a 500 (kill the API or unplug network mid-click): negative toast "Could not draft the shop." with the error caption; button un-spins and re-enables
- [ ] Card is toggleable via the Dashboard's Cards menu (labelled **Draft this week's shop**, grouped under the `act` zone); hiding removes the card, showing it puts it back
- [ ] The existing `NewListDialog` multi-checkbox flow (New list → check "Items that are low or out of stock" / "Flagged as always-include" / "Frequently added") is unchanged — it always passes a `merge_into_list_id` to `/auto-generate`, so the "defer list creation" server change doesn't touch its path
- [ ] Meal-plan window sanity check: click Draft my shop today; then advance a meal-plan entry from today to yesterday (or mark today's entry as consumed) → click again → the "consumed" / past-day entry is filtered by the server's `consumed_at IS NULL` guard and does NOT re-appear on the new draft
- [ ] Sidebar list-selector is refreshed via `listStore.refreshAsync()` before the router push lands on the new detail, so the list-selector shows the new list from the moment the user arrives

### ⭐ P8-08 Dora Score — Kitchen health card — origin champion-plan §P8-08
- [ ] Dashboard renders a new **Kitchen health** card in the "Your kitchen" zone above the Pantry donut card (icon ♥ heart)
- [ ] Card header shows title + a small trend chip on the right when the direction is `up` or `down` (green up-arrow with `+N`, red down-arrow with `-N`); no chip when direction is `flat` or unavailable
- [ ] Big composite number (0–100) renders next to `out of 100 · last 30 days` caption
- [ ] Below the number, five component rows in order: **Waste · Budget · Freshness · Run-outs · Stocktake**. Each row shows the component score, a mini bar filled to that percent (green ≥80, amber 50–79, red <50), a one-sentence server-authored reason, and (when applicable) a right-side action link
- [ ] Component with no data (e.g. no budget set → Budget; no items track expiry → Freshness; no stock items → Stocktake) shows a dashed `—` in place of the score and dims the row; the mini-bar hides. The composite number does **not** drop as a result — dormant components are excluded, not zeroed
- [ ] Brand-new install (no data anywhere): card shows the calm "appears once you've been using Dora for a bit" empty state, not a 0 score
- [ ] Trend arrow reflects `score - (score computed on the 30d window ending 7 days ago)` — logging a waste event shifts the composite down over the next week, and the arrow should flip from up/flat to down (background refresh happens 5 min after mutation; a full reload picks it up sooner)
- [ ] Component action links resolve — Waste → `/waste`, Budget → `/settings/preferences`, Freshness → `/stock?expiring=1`, Run-outs → `/shopping-lists`, Stocktake → `/stock?stocktake=1`. Any that 404 or land on the wrong surface is a bug (some rely on query params the target page needs to honour — flag which ones don't)
- [ ] Dashboard Cards menu lists **Kitchen health** under the "Your kitchen" group; hiding it removes the card, showing it puts it back at the top of the kitchen zone; drag-reorder within the zone still works
- [ ] `GET /api/dashboard/dora-score` returns 401 when signed out; 200 with a valid DTO when signed in
- [ ] Server logs show `Dora Score user=… composite=… trend=… (delta=…)` on each request — no exceptions, no NaN, no negatives

### Log-price quick action — origin FU-300
- [ ] Money features ON: dashboard quick-action bar shows three buttons — Add item · Add to list · Log price
- [ ] Money features OFF: Log price button is hidden (matches row-level Log-a-price posture)
- [ ] Click Log price → bottom sheet titled "Log a price" opens with a search input and a shortlist of stock items (low/out first)
- [ ] Type a partial item name → results filter in real time
- [ ] Pick an item → the sheet title updates to "Log a price · {name}"; PriceEntry form renders in shelf mode with the item's `price_entry_prefill` seeded (if any)
- [ ] Back arrow returns to the picker with the search input cleared
- [ ] Submit a valid entry → success toast ("Logged a price for X."); sheet closes; the observation appears on the stock item's detail Your-Prices widget
- [ ] Cancel from within PriceEntry → sheet closes without a request
- [ ] Sheet dismissed via backdrop / close-X → next open starts fresh (no stale selection or query)

### Dashboard stock donut deep-links — origin FU-299
- [ ] Pantry card no longer navigates as a whole card on click — only the "View →" action link, donut low/out segments, and legend low/out rows are clickable
- [ ] Click the yellow low segment (SVG) → routes to `/stock?level_id=<low>`; the Level filter chip in the FilterBar shows Low Stock and only low items render
- [ ] Click the red out segment → routes to `/stock?level_id=<out>`; only out-of-stock items render
- [ ] Click the "running low" legend row → same low-filtered view
- [ ] Click the "out" legend row → same out-filtered view
- [ ] Click the green in-stock segment or legend row → nothing happens (no filter for the residual bucket)
- [ ] "View →" action still opens the unfiltered `/stock`
- [ ] Keyboard: Tab focuses the low/out segments; Enter/Space navigates to the filtered view
- [ ] Screen reader announces "View low items" / "View out items" for the linkable segments

### Dashboard price-drops widget — origin FU-296
- [ ] Products feature ON: "Price drops" appears in the Cards menu under the Money zone (defaultHidden — enable it from there)
- [ ] Products feature OFF: card is absent from both the dashboard and the Cards menu
- [ ] With no historic offers on any product → card shows the empty state ("Nothing at a new low right now…")
- [ ] Seed a product where `current_offer.price_now` < `min(historic_offers.price_now)` → card lists it with store name, "was $X" from the previous low, "−N%" badge, and a link to the linked stock item when one exists
- [ ] Product with `is_active=false` or with a `null` current offer → excluded from the list
- [ ] Product with no historic offers → excluded (Honesty — the first-ever price isn't a "drop")
- [ ] Rank order: highest drop-% first (ties broken by drop-amount)
- [ ] `/api/reports/price-drops?limit=N` clamps to `[1, 20]`; default is 5
- [ ] Product images: `has_image=true` rows fetch `/api/products/{id}/image`; otherwise show the shopping_bag placeholder
- [ ] Dark-mode + non-money theme themes: colours ride semantic tokens (no hardcoded red/green)

### Dashboard rebuild — full walk Phases 0–7 — origin FU-301
- [ ] **Phase 0** — cards keyboard-focus + middle-click; the dark-mode question reads correctly
- [ ] **Phase 1** — welcome rotates per day; empty states read well; primary-list footer link works
- [ ] **Phase 2** — zone bands render in order; within-zone reorder persists across reload AND another device (exercises FU-292's backend); hidden cards stay hidden
- [ ] **Phase 4** — Money band shows only with money enabled; savings range toggle re-fetches; best_deals hidden without products; money empty states
- [ ] **Phase 5** — restock Add works (toast + list refresh); Add-item dialog creates + refreshes; Add-to-list sheet works
- [ ] **Phase 6** — opt-in "This fortnight" calendar (enable via Cards menu) renders 14-day grid with correct dots; tapping a day expands detail + links work
- [ ] **Phase 7** — at 360/768/1280: zones stack, quick-action bar wraps, touch targets comfortable
- [ ] **FU-293 extraction:** every card looks identical after DashboardCard extraction — shell border/padding/shadow, header icon/title, hover lift on clickable cards (Pantry/week-ahead/budget), header action link/text styling + hover

### Dashboard "Next to cook" card (meal-plan-driven) — origin FU-298
- [ ] Plan a meal in the next 7 days → it appears in the card with the relative day + slot ("Tomorrow dinner") and a green "Ready" badge when nothing is missing
- [ ] Remove one of that recipe's ingredients from stock → reload → badge flips to amber "Missing 1" (or N)
- [ ] Plan the same recipe twice in the week → it appears once in the card (deduped by recipe_id, earliest slot wins)
- [ ] Recipe with no ingredients planned → grey "No ingredients" badge (the card still surfaces it; "Cook" still navigates)
- [ ] Click recipe name → deep links to `/cookbook/{recipe_id}`; click "Cook" → `/cookbook/{recipe_id}/cook`
- [ ] Empty state when nothing is planned for the next week → "Nothing planned for the next week" + "Plan a meal →" link to `/meal-plans`

### Dashboard budget money-gate — origin FU-297
- [ ] Money features OFF: budget card is hidden from the dashboard AND from the Cards menu (same posture as savings / spend / pantry)
- [ ] DevTools network: with money OFF, no `GET /api/budget/status` request fires on dashboard load
- [ ] Money features ON: budget card renders as before — both the "set a target" empty state and the live spend/progress body

### Dashboard Cards menu drag-and-drop reorder — origin FU-294
- [ ] **Desktop** (Cards menu open): grab a card row by the left-side drag handle → row dims, drop-target row gets a primary ring, drop reorders within the zone, layout persists across reload
- [ ] **Cross-zone drop is rejected**: drag a Today-zone card over a Money-zone row → no drop-target ring, no drop accepted
- [ ] **Tap up/down still works** alongside drag (mobile and keyboard mandate, C13)
- [ ] **Mobile** (or touch-emulated): drag handle column is hidden — only tap arrows + visibility toggle visible
- [ ] **Reload + cross-device** persistence (same backend as `dashboard_layout` — exercises FU-292 too): drag-reordered layout follows the user

### Dashboard `dashboard_layout` backend — origin FU-292
- [ ] Run the migration on a Python-capable machine
- [ ] Run the e2e suite (incl. `test__dashboard_layout__set_and_clear`)
- [ ] Browser-walk: reorder/hide cards, reload, confirm layout persists and follows the user to another device/browser

---

## Alerts & notifications

### Alerts C-9.1 — spine — remaining browser smoke — origin FU-183
- [ ] Bell badge equals actionable list count
- [ ] Snooze persists across a reload (server-side)
- [ ] Dismiss hides everywhere
- [ ] Existing inline actions work with the new scoped key
- [ ] **C-9.2:** admin System-settings threshold fields save + round-trip; disabling a kind removes it from list + drops badge; promoting/demoting moves a kind between badge/FYI
- [ ] **C-9.3:** Alerts hub page (summary tiles + tiered active list + Manage panel + collapsible History) renders; bell is now a slim peek (top rows + bulk-add + "Open Alerts"); shared `AlertRow` actions work from both; History lists past dismiss/snooze/read with stock name resolved; dark-mode clean; no bell/page divergence
- [ ] **C-9.4 forward-looking nudges:** with next week's plan empty, `no_planned_meals` FYI row shows and deep-links to `/meal-plans`; planning a meal clears it. `shopping_day` FYI row shows for a list with `planned_shop_date` within 3 days, deep-links; marking list done clears it. Both render through shared `AlertRow` (icon/colour/theme), no stock name, snooze/dismiss work
- [ ] **C-9.5 subscriptions / price-watch tier:** money flag ON + armed price alert → Price watch region lists it (product · merchant · "notify below $X" · last-alerted); View opens price-history explorer with that product; Remove deletes (row gone + toast); empty-state clean; hidden when money flag OFF
- [ ] **C-9.6 Upcoming fortnight timeline (Phase A):** Upcoming mini-calendar renders on hub; days with events show correct per-category dots (warning expiry, primary shopping, positive meal); out-of-window dimmed, today ringed; clicking a day expands its detail list + links navigate (expiry → `/stock/:id`, shopping → `/shopping-lists/:id`, meal → `/cookbook/:recipe_id`); refresh works; empty-state clean; dark-mode clean (token dots survive theme switch)

### Cross-app undo after push-expiry (fixes 2026-07-10) — origin FU-357
- [ ] From the **Dashboard's dashboard-card push-expiry action** (i.e. the push-expiry rendered on the Dashboard alerts card, not just the bell) → toast now reads **"Done."** (this used to be silent — fixed 2026-07-10). Confirm the toast fires on Dashboard, Bell peek, and `/alerts` page — all three surfaces should behave identically.
- [ ] With a **`meal_reconcile_overdue`** alert present (e.g. leave a past-day meal-plan entry unresolved so it fires — see FU-317 Chunk 4) → the bell + `/alerts` page render the row cleanly, use the checklist icon, theme text "meals to reconcile", tapping the row navigates to `/meal-plans/reconcile`, no ErrorBoundary. Regression from FU-317 Chunk 4 fixed 2026-07-10 (SPA `AlertKind` union + five kind-switches extended; defensive `?? []` in AlertRow).
- [ ] Push expiry via bell/dashboard/`/alerts`, then navigate to the stock item detail page → **Clear** its expiry → no stale toast reappears, the expiry field reads empty, and no undo affordance fires against the cleared field. (Static read confirmed: no undo exists on the push_expiry path anywhere in the SPA. This step is the last belt-and-braces check.)

### good_deal alerts + fake-markdown buy verdict — origin FU-450
- [ ] **Money features on.** For a product linked to a tracked stock item, add a *fresh* offer that's the lowest it's been (great band) → an alert appears in AlertsPage: "«item» — «brand product» is at its lowest price in months · $X · usually $Y", green tag icon, FYI tier (doesn't inflate the bell badge). Tapping it opens the stock item (where add-to-list lives).
- [ ] **Threshold.** Settings → Notifications → **Deal alerts** shows a "Good & great" / "Great only" segmented control (only when money features are on). Set "Great only" → a merely-`good`-band product stops alerting; a `great` one still does.
- [ ] **fake markdown.** For a product where the merchant claims a "special" (was > now) but you've logged paying *less* recently (price observations below the special) → the item's **Buy Verdict** card shows "Markdown looks inflated — you've paid less than this 'special' recently" and a price-driven `buy` reads as **wait**. An out-of-stock item stays **buy** (need wins) but still shows the inflated-markdown reason.
- [ ] **Money off** → no Deal-alerts settings section, no `good_deal` alerts, no fake-markdown demotion.

### C-9.7 alerts email digest — origin FU-205
- [ ] Settings → Preferences shows new "Alerts email digest" card after Weekly deals; heading + caption read across all themes
- [ ] **SMTP-gating (R-014):** without `DORA_SMTP_USERNAME`, master toggle disabled, caption "Email isn't set up on this install yet — ask an admin…". With env set + restart: toggle enabled, caption hides; `GET /api/health` shows `features.email_smtp_configured: true`
- [ ] Opt-in round-trip: master toggle on → toast → cadence select appears (Daily default); switch Weekly → day select; pick a day; reload survives. Network panel: master sends `{alerts_email_enabled, alerts_email_cadence}` together; later edits send single changed field
- [ ] `GET /api/auth/me` returns `alerts_email_enabled`, `alerts_email_cadence`, `alerts_email_day` on user payload
- [ ] Real SMTP send: real env + opted-in + an expired stock item → trigger job → inbox receives digest with actionable item in "Needs action", "Open Alerts" button linking to `<DORA_PUBLIC_URL>/alerts`, plain-text fallback
- [ ] Dedup: trigger again → no second email; mark item not-expired/delete → trigger → no email + `last_emailed_at` clears; re-add same name → trigger → fresh email
- [ ] Weekly day gating: cadence=weekly, day=Monday; non-Monday → trigger → no email; Monday → email lands
- [ ] Schedule fires: confirm `alerts_digest` job in APScheduler's job list (07:00 CronTrigger)

### C-9.8 web-push channel — origin FU-206
*Prereq: generate VAPID keys per FU-207*
- [ ] **VAPID gating (R-014):** no `DORA_VAPID_*` → Push card toggle disabled, caption "Push isn't set up on this install yet — ask an admin…"; `GET /api/health` shows `features.push_vapid_configured: false`; `GET /api/alerts/push/vapid-public-key` → 404
- [ ] Set VAPID env, restart → toggle enabled, caption hides; health flag true; key endpoint returns the public key
- [ ] Subscribe flow: toggle on → browser permission prompt → allow → toast → toggle stays on, caption "This device is subscribed…". DevTools → Application → Service Workers: SW at `/push-sw.js` registered + activated
- [ ] Receive: create expired stock item → trigger `send_alerts_push()` → OS notification "Dashy Dora — <name> has expired". Click → focuses an existing Dora tab on `/alerts` (or opens new one)
- [ ] Dedup: trigger again → no second notification. Mark item not-expired → trigger → no notification + `last_pushed_at` clears. Re-add expired → trigger → fresh notification
- [ ] Multi-device: subscribe a second browser (e.g. mobile Chrome on same LAN) → trigger → both buzz
- [ ] Permission denied: fresh profile, deny prompt → caption "Notifications are blocked…"; toggle stays off; subscribe button greys
- [ ] Dead-subscription pruning: DevTools → Application → Push → unregister SW. Trigger → backend gets 404/410, `PushSubscription` deleted, no further attempts
- [ ] Unsubscribe: toggle off → toast → `PushSubscription` gone server-side; browser registration gone (DevTools confirms)
- [ ] Schedule fires: confirm `alerts_push` job registered with `CronTrigger(minute=30)`; an actionable alert created at :25 produces a notification within 5 minutes

---

## Settings

### Data pages UI revamp — Import + Backup & restore — origin FU-359 (2026-07-09)
*Requires admin login. Presentation-only rebuild onto the Settings design language — verify nothing wired regressed.*
- [ ] **Import page** — Settings → Admin → Data → **Import**. Page now uses the standard `SettingsPageHeader` with the **Download template** button in the top-right header (not a body card). Upload area is a drag-and-drop zone: drag an `.xlsx`/`.csv` onto it (or click to browse) → shows filename + size with a clear (✕) button; during upload a spinner + progress bar shows; multi-sheet workbook surfaces a sheet picker; column mapping reflows as a responsive grid; preview table scrolls horizontally; options render as labelled toggle rows; Import + Cancel bottom-right. Run a real import end-to-end → rows land, result dialog reports per-row status.
- [ ] **Backup & restore page** — Settings → Admin → Data → **Backup & restore**. **New backup** button sits in the header; clicking opens the section-picker dialog and Generate still creates a snapshot. Backup library renders as tidy rows (icon + timestamp + size/sections/author + Download/Restore/Delete icon actions); a backup containing users/settings/historic-offers shows the amber **Sensitive** chip. Empty state shows a dashed placeholder. Download / Restore / Delete each still work.
- [ ] **Restore-from-file** — drag a `.json` backup onto the drop zone → inspect spinner → the preview panel appears (backup metadata, selected/duplicate count, Select-all / Clear toolbar, the tick tree). "Restore selection" and "Restore all (skip duplicates)" both still commit and show the restore report dialog.
- [ ] **Library settings + Image compression** — both now render as `SettingsSection` blocks with `SettingsRow` fields (retention + storage path; quality slider + longest-edge input). Discard/Save enable only when dirty and still persist via `PATCH /app-settings`.

### FU-333 close-out — Buckets C + D + strict AppSetting (2026-07-06) — origin FU-333
*Requires admin login. Supersedes the earlier Bucket-B block below — env fallbacks are gone.*
- [ ] `/settings/admin/system/email`: SMTP password row now renders a real password input (not disabled). Empty state label reads "Password"; help text mentions encryption + `DORA_LLM_KEY_ENCRYPTION_KEY`.
- [ ] Type a password, click Save → toast "SMTP password saved."; the row's label flips to "Password (change)" and shows a **Clear** button; the input clears itself; reload the page — same "change" state.
- [ ] Click **Clear** → toast "SMTP password cleared."; row flips back to the "Password" label, no Clear button; the ciphertext column on `AppSetting` is empty (verify via `/api/app-settings` — `smtp_password_configured: false`).
- [ ] `/api/app-settings` **never** returns a `smtp_password` or `smtp_password_encrypted` field — only `smtp_password_configured: bool`.
- [ ] Same behaviour on `/settings/admin/system/push` for VAPID private key: real password textarea, Save then Clear, label flips accordingly, DTO returns only `vapid_private_key_configured`.
- [ ] With both VAPID public key + private key set: `/api/health` returns `features.push_vapid_configured: true`. Clear the private key → next `/health` call returns `false`.
- [ ] Env-var fallback is **gone**: unset `DORA_SMTP_HOST` (etc.) and clear the AppSetting row → the sender is in dry-run (logs the body) rather than reading env. Grep the running server logs for "DRY-RUN email" on any auth flow that would have sent.
- [ ] `.env.example` no longer lists `DORA_SMTP_*` / `DORA_VAPID_*` / `DORA_PIPER_*` / `DORA_EMAIL_ENABLED` / `DORA_AUDIT_RETENTION_DAYS` / `DORA_PUBLIC_URL` (they were removed with the fallback drop).
- [ ] **Bucket D — desktop first-run** (only meaningful when running the PyInstaller bundle, not `python dora_api/app.py`). Delete `<DATA_DIR>/.llm_key_encryption_key` (and `.secret_key`) → relaunch the app → both files reappear; `/api/health` responds normally; login still works (new session key was generated). Any previously-stored SMTP password / VAPID private key cannot decrypt against the new wrapping key — Settings shows them as "not configured" and the log carries a warning line naming the field.
- [ ] Server self-host (docker / manual): explicitly setting `DORA_SECRET_KEY` + `DORA_LLM_KEY_ENCRYPTION_KEY` in env still works — the auto-generation branch only runs when the env var is missing.

### FU-333 Bucket B — env vars promoted to AppSetting + four new admin pages (2026-07-05, historical)
*Requires admin login. Earlier checklist for the Bucket B landing; keep for reference but the FU-333 close-out block above is what should be walked now.*
- [ ] Sidebar under Admin → System now has four new entries in order: **Email** (envelope-check icon), **Push notifications** (bell-ring), **Voice** (microphone-message), **Hosting** (cloud-upload). Non-admin session doesn't see them.
- [ ] `/settings/admin/system/email`: page loads, shows Email enabled toggle + SMTP host/port/username/from/use-TLS + the password input (write-only, post-FU-333 close-out — no longer the Bucket-C disabled placeholder). Type a host, tab out → toast "Email settings saved.", reload survives.
- [ ] `/settings/admin/system/email`: with SMTP username set, `/api/health` returns `features.email_smtp_configured: true`. Clear it → next `/health` call returns `false` (no restart).
- [ ] `/settings/admin/system/push`: page loads with public key + subject fields + the private-key input (write-only). Type a subject, tab out → toast "Push settings saved.", reload survives.
- [ ] `/settings/admin/system/voice`: piper_bin / bundled_voice_dir / legacy voice inputs render; typing a valid path + blur → toast "Voice settings saved."; the assistant Speak action still resolves the same voice as before (the resolver picks the row value now).
- [ ] `/settings/admin/system/hosting`: public URL + audit retention days inputs. Try `javascript:alert(1)` in Public URL → inline red error "Must start with http:// or https://.", nothing saved. `https://dora.example.com` → toast, reload survives.

### Users admin — Add / Delete (2026-07-06) — origin FU-461
*Requires admin login. Second admin account handy for the last-admin + can't-delete-self checks.*
- [ ] Settings → Admin → Users: the header now has **Add user** (primary button, account-plus icon) alongside the refresh button.
- [ ] Click **Add user** → dialog opens with Username / Email (optional) / Admin toggle. Cancel closes without side effects.
- [ ] Submit with only a username filled → dialog closes → "User created" result dialog appears with a 12-char one-time password + Copy button. User list refreshes and the new user appears.
- [ ] Copy button copies the password; toast "Copied to clipboard." Close the dialog — password is gone (no way to retrieve it; admin must reset if lost).
- [ ] Log in as the new user with the copied password → login succeeds → normal onboarding path.
- [ ] Try Add with a **taken username** → inline field error appears under Username; nothing created.
- [ ] Try Add with a **malformed email** ("nope") → inline field error under Email; nothing created.
- [ ] Try Add with a **taken email** (belongs to another user) → inline field error under Email; nothing created.
- [ ] Try Add with the Admin toggle on → new user appears in the list with the yellow "admin" badge.
- [ ] Each row now has a **Delete** button (red text, trash icon).
- [ ] Delete on **your own row**: disabled + tooltip "You can't delete your own account."
- [ ] Delete on another user → confirm dialog appears with negative-coloured Delete CTA + honest scope copy ("sessions, alert prefs, push subs removed; household-shared things survive"). Cancel closes with no change.
- [ ] Confirm delete → toast "Deleted 'X'." → user disappears from the list. Their historical audit events still exist (audit-log page keeps the row with the now-orphan actor_user_id).
- [ ] Recipes / shopping lists that the deleted user authored / cooked survive with a null author (RecipeCookEvent.cooked_by_user_id and ShoppingList.created_by_user_id are SET NULL).
- [ ] With only one admin remaining, attempt to delete that admin → toast "Delete failed." with caption "Refusing to delete the last admin — promote someone else first." No deletion happens.

### Admin cache-race safety net — origin FU-016
*Requires at least two admins in the system (the backend blocks removing the last admin).*
- [ ] As Admin-A on `/settings/admin/users`: toggle **your own** Admin switch off → immediately the sidebar admin section (System · Data · Users · Audit) disappears from Settings, the router refuses `/settings/admin/*` (bounces to `/settings/account`), and the "Admin" pill on your row in the list is gone
- [ ] Same pre-condition, edit **your own** username or email through the admin surface → the header avatar tooltip + Settings → Account username reflect the new name **without a hard reload**
- [ ] Restore a backup that includes the **users** section, then hit **Close** on the report dialog (not "Reload now") → the header identity + admin sidebar reflect whatever the restored state says about *your* row (e.g. if you were demoted in the backup, admin surfaces disappear). Then hit **Reload now** on a subsequent restore to confirm both paths keep the guards honest

### Backup library — origin FU-342 (2026-07-01)
- [ ] As admin on `/settings/admin/data/backup`: the top card is **Backup library** (not the old "Create backup" tile). Empty state text appears until the first backup exists
- [ ] Click **New backup** → dialog opens with the section picker. Default (Core data) sections ticked; Optional sections unticked. No warning banner
- [ ] Tick any Optional section (system settings / users / historic offers) → an inline warning banner appears in the dialog naming what will be included
- [ ] Click **Generate** → dialog closes, a positive toast, the library list gains a new row at the top with today's timestamp + a byte size + section count. Row shows "by dora"
- [ ] With an Optional section included, the row also shows a **Includes sensitive data** warning chip (hover → naming which)
- [ ] Click the row's **Download** button → browser downloads `dora-backup-<date>.json`; opening it shows a `schema_version` + section keys as before
- [ ] Click the row's **Restore** button → confirm dialog appears; confirm → positive toast with a rows-imported summary. Nothing else changes since duplicates are skipped
- [ ] Click the row's **Delete** button → confirm dialog; confirm → the row disappears from the list and the file on disk is gone (check the server's `<DATA_DIR>/backups/` — no leftover)
- [ ] Create ≥ (retention_count + 1) backups → the oldest drops off the list AND its file is removed. Retention default is 5
- [ ] The external-file **Restore from backup** card (right side / below) still works: pick a downloaded backup file → inspect → tree → commit. Unchanged
- [ ] The old `/api/data/backup` GET endpoint no longer exists — no page relies on it; `POST /api/data/backups` is the only writer

### Image compression settings — install-wide (FU-345, 2026-07-01)
- [ ] Settings → Admin → Data → Backup & restore: at the bottom, a new **Image compression** card. Two rows: JPEG/WebP quality (slider, default 85) and Longest edge (numeric input, default 1920)
- [ ] Change quality to 60, hit Save → toast "Image settings saved." with caption "Applies to new uploads; existing images are unchanged."
- [ ] Discard button greys out when nothing's dirty; enables when the slider is moved but not yet saved
- [ ] Bad value guards: try setting quality to 20 (below floor) or 200 (above ceiling) via DevTools; save → 400 with a readable reason. Same for max dimension < 512 or > 8192
- [ ] End-to-end: with default (85 / 1920), upload a photo on a stock item. Note the stored file size (visible via DevTools → download the item's image, check size). Lower quality to 50, save, upload the same photo again → the new stored file is materially smaller
- [ ] Longest-edge cap: with default 1920, upload a photo with a 4000px longest edge → stored image longest edge is 1920. Lower cap to 800, upload the same source photo again → stored longest edge is 800
- [ ] Existing images unchanged after saving new settings — nothing re-encodes, no dashboard flicker
- [ ] Non-admin session: the Image compression card is unreachable (the whole admin sub-tree is gated); a non-admin's uploads still get compressed at whatever the current install policy is (they read via /health, no admin credentials needed)

### Import page Options alignment (FU-344, 2026-07-01)
- [ ] Settings → Admin → Data → Import: past the file picker and mapping (upload a small CSV to reach the Options section) the four options render as SettingsRow blocks — label + short description on the left, toggle on the right. No stacked `<br>` gap between them
- [ ] Each option's caption is descriptive (e.g. "Rolls the whole import back on any row-level failure. Off ⇒ valid rows land; errors are reported row-by-row.")
- [ ] Toggling any option flips the boolean state (verify via the subsequent Import commit: skip_duplicates on/off behaviour is unchanged)

### Import templates — Download template button (FU-343, 2026-07-01; hint row FU-349 2026-07-07)
- [ ] `/settings/admin/data/import`: the "Spreadsheet import" card's header row shows a **Download template** button on the right, next to the title / caption
- [ ] Click it → the browser downloads `dora-import-stock_items.csv`. Opening it in a text editor: first line is `name,level,location,group,expiry,is_essential`; second line is an illustrative row (`Rice,In stock,Pantry,Grains,2027-01-01,no`); **third line begins with `#`** and reads *"# example values are illustrative — replace them, and use your own level/location/group names (see Settings → Kitchen setup)."* (FU-349)
- [ ] Hover the button → tooltip shows the section caption ("One row per pantry item. Only `name` is required; the rest are optional.")
- [ ] Round-trip: open the CSV in Excel / Sheets, edit the example row (or add more), save, upload via the file picker below. Inspect step auto-maps every column; commit succeeds (or reports row-level errors as before)
- [ ] FU-349 round-trip — download the template, DON'T edit it, upload it as-is. Inspect preview shows **one** data row (the Rice example), not two — the `#` hint row is filtered by the parser. Commit with `skip_duplicates=true` creates just the one row (or zero if "Rice" already exists)
- [ ] FU-349 negative case — hand-edit a CSV so the second row starts with `#` (`#TestImport,Low,Pantry,,,`). Upload → inspect + commit → that row does NOT get imported (was filtered as a comment)
- [ ] Non-admin session: `/api/data/import/templates` and `/api/data/import/templates/stock_items.csv` both return 403

### Backup library — retention + storage path settings (FU-342)
- [ ] Scroll to the **Library settings** card at the bottom of the page. Retention shows 5 by default; storage path is blank
- [ ] Change retention to 3, Save → toast "Library settings saved." Create 4+ backups → only 3 rows visible; server has 3 files
- [ ] Enter a **relative** storage path (e.g. `data/backups`) → Save → 400 with a readable reason ("must be absolute")
- [ ] Enter a **non-existent parent** path → Save → 400 with a readable reason mentioning the offending ancestor
- [ ] Enter a valid absolute path on a writeable dir → Save → toast success; the next backup file lands in that directory, not the default. Set back to blank → next backup lands under `<DATA_DIR>/backups` again

### Backup & restore + Import relocated to Admin → Data — origin FU-341 (2026-07-01)
- [ ] As **admin**: Settings → Admin · global sidebar shows a new **Data** sub-header with two entries: **Backup & restore** (cloud-download icon) and **Import** (file-upload icon). Between Features (under the System sub-header) and Audit log
- [ ] Click Backup & restore → page loads with the standard SettingsPageHeader (title + description + cloud-download icon), then the existing Create-backup / Restore-backup two-card layout underneath. All existing controls work (section pickers, chunked upload, restore preview, confirm dialog)
- [ ] Click Import → SettingsPageHeader (Import + file-upload icon) then the existing file picker + column mapping + preview + commit flow. All existing controls work
- [ ] Main menu (top of the app) NO longer has a "Data" entry — the sequence is Stock · Cookbook · Meal Plans · Shopping Lists · Reports (+ My Products / Product Search where enabled). No gap where "Data" used to sit
- [ ] Direct-navigate to `/data`, `/data/backup`, `/data/import`, `/data/export`, `/data/barcodes` → each redirects: /data + /data/backup → the new Backup page; /data/import → Import; /data/export → Backup (nearest sibling); /data/barcodes → QR labels. No 404, no blank flash
- [ ] As **non-admin** (a regular user account): the "Admin · global" sidebar group is not shown at all. Direct-navigating to `/data/backup` or `/settings/admin/data/backup` → router guard bounces to `/settings/account`
- [ ] Onboarding wizard's "Import from a spreadsheet or another app instead" link routes to the new `/settings/admin/data/import` (admins) or bounces to `/settings/account` (non-admins) — no dead route

### FU-198 close-out — admin gate on data endpoints (2026-07-01)
- [ ] As a non-admin session (log in with a non-admin user), open DevTools → Network. Try:
  - `GET /api/data/backup` → **403** with a "Admin role required." problem-details body
  - `POST /api/data/backup/inspect` (empty body is fine) → 403
  - `POST /api/data/backup/restore` (empty body) → 403
  - `POST /api/data/uploads/start` (empty body) → 403
  - `POST /api/data/import/spreadsheet/inspect` (empty body) → 403
- [ ] As an admin session: the same endpoints return their normal 200/4xx-domain-error responses. The Backup page's Create + Restore flows and the Import page's inspect + commit still work end-to-end

### QR labels relocated to Kitchen setup — origin FU-340 (2026-07-01)
- [ ] With `scanning_enabled` **on** (Settings → System → Features toggle): Settings → Kitchen setup sidebar shows a **QR labels** entry between "Stores" and the "Recipe taxonomies" sub-header. Icon is a QR-code glyph
- [ ] Click into it → the page shows the QR labels description, the filter + layout picker, item list with checkboxes, and Print / Open-sheet actions. NO Scan tab, NO Scan card, NO "Open camera" button
- [ ] Filter, All/None, layout picker, and both Print buttons behave the same as they did on the old `/data/barcodes` page — the sheet still opens in a new tab from `/stock-items/qr/sheet`
- [ ] Toggle `scanning_enabled` **off** → the QR labels sidebar entry disappears from Kitchen setup (both desktop sidebar and mobile settings tab strip). Direct-navigate to `/settings/kitchen-setup/qr-labels` → the page renders only the "ask an admin to enable it" banner; no print controls
- [ ] Toggle back on → the entry reappears without a full reload (may require a reload if `useScanningEnabled` cached — this is expected)

### Account — verified email change + CSRF defence — origin FU-197
- [ ] Settings → Account → Email row: enter a new address; the "Send confirmation" button stays disabled until you also fill the **Current password** input
- [ ] Wrong current password → toast "Could not request email change." with the API's 422 reason caption ("Current password is incorrect.")
- [ ] Right current password → toast "Confirmation link sent. Check your new inbox to finish the change.", the password field clears, the address shown above (currentUser) does **not** update yet
- [ ] **Inbox A (new address):** "Confirm your new Dashy Dora email" with the confirmation link — click → /confirm-email-change → success → the next /auth/me probe surfaces the new address in the menu
- [ ] **Inbox B (old address):** "An email change was requested on your Dashy Dora account" notice rendered from `email_change_notice.html` arrives **before** the confirmation in inbox A (same task; best-effort, but expected when SMTP is up). Old address never loses anything until the confirmation link is clicked
- [ ] DevTools network: `PATCH /api/auth/me` with `{"email": "x@y.z"}` returns **400** (the field is now forbidden by the schema). The SPA never sends this — Settings always uses `POST /auth/me/email`
- [ ] DevTools application → Cookies: a `dora_csrf` cookie is set after the first request, non-HttpOnly (so `document.cookie` shows it), SameSite=Lax. When `DORA_SECURE_COOKIES=1` is set on the server it's also Secure
- [ ] DevTools network: every mutating SPA call carries an `X-CSRF-Token` request header whose value matches the `dora_csrf` cookie
- [ ] DevTools console — paste `fetch('/api/auth/me', {method:'PATCH', credentials:'include', headers:{'Content-Type':'application/json'}, body:'{}'})` without the CSRF header → 403 with "Missing or invalid CSRF token."
- [ ] Audit log: a successful change-email request emits `auth.email_change.requested`; a wrong-password attempt emits `auth.email_change.password_failed` (warn severity)
- [ ] Login / register / forgot-password / reset-password / verify-email / bootstrap-admin still work cold (no CSRF cookie yet) — public endpoints are intentionally exempt

### Assistant — banner, Test connection, docs (PR2 finalisation) — origin FU-330 + FU-331 + FU-332
- [ ] **AI-unavailable banner (FU-330):**
  - [ ] User with AI mode ON but pointing at a deliberately-bad URL (e.g. `http://localhost:9` for Ollama) → open the chat panel → banner renders at the top with red icon + the reason ("Couldn't reach Ollama" / "Your LLM didn't respond." etc.) + Retry + Settings buttons
  - [ ] Fix the URL → click Retry → banner disappears once the probe succeeds (mid-session recovery)
  - [ ] User with AI mode OFF (plain Basic) → banner never renders regardless of master flag or anything else (Basic isn't a failure)
  - [ ] Admin flips master kill-switch off → user's chat shows the banner with the master-off reason
  - [ ] DevTools → `/api/assistant/status` returns `{ai_available: bool, reason: string|null}` — reason is null when AI is up, populated when down
- [ ] **Test connection button (FU-332):**
  - [ ] Settings → Assistant → Ollama provider → enter a valid URL + model → click Test → inline green tick + "Connected. N models detected."
  - [ ] Enter a deliberately-bad URL → Test → inline red mark + reason
  - [ ] Edit the URL after a green tick → status clears (no stale tick next to wrong URL)
  - [ ] Switch to OpenAI/Anthropic/Gemini → enter a model + valid API key → Test → green tick. Wrong key → red mark + reason
  - [ ] **Without re-typing the saved key**: after saving a paid-provider key, leave the masked field empty, click Test → still works (server falls back to the saved encrypted blob)
  - [ ] **Rate limit**: hammer Test ~11 times in a minute → 11th call returns the "Too many probes — try again in Xs" message
  - [ ] **Audit trail**: Settings → Admin → Audit log shows an `assistant.probe` event per call with the actor + provider + target host + outcome (host only, no full URL or key)
- [ ] **Docs (FU-331):**
  - [ ] Help → "Dora itself" tab shows the new entries: "Set up AI mode (per account)", "AI mode says unavailable — why?", "Network topology: who reaches the LLM?", "Admin: install-wide AI master switch + API-key encryption"
  - [ ] README's "AI assistant" bullet describes the per-user pattern, all four providers, the `DORA_LLM_KEY_ENCRYPTION_KEY` env var, and the backend-reaches-LLM network topology
  - [ ] AssistantSettings.vue's inline page-level help blurb still renders (didn't accidentally get removed)

### Assistant per-user config (PR1: schema + 4 providers + master kill-switch) — origin FU-153
- [ ] `flask db upgrade head` (or `alembic upgrade head`) applies migration `e5b9d3c7a8f2_20260629_per_user_llm_config` on SQLite **and** Postgres; `verify_mappings()` passes
- [ ] `pytest -q` green (or remaining failures are pre-existing FU-328 ones, not introduced by this work)
- [ ] Backend boots — no `ImportError` from `dora_api.infrastructure.llm`
- [ ] **Settings → Assistant** (the new page) appears in the sidebar between *Nutrition* and *About*. URL is `/settings/assistant`. Reload → still shows.
- [ ] **Ollama path** (no env-var needed):
  - [ ] Pick `Ollama (local)`. Save base URL + model. AI toggle stays disabled until both are present; once saved, toggle enables AI mode → assistant replies route through the configured Ollama.
  - [ ] Old `AdminSystemAssistantSettings.vue` (now stripped) only shows the master kill-switch + a pointer to per-user settings.
- [ ] **Master kill-switch (admin)**: System → AI assistant. Toggle off → every user's Settings → Assistant page shows the "AI mode is disabled install-wide" banner + the per-user toggle is forced off / disabled. Toggle back on → user toggles re-enable.
- [ ] **Paid-provider flow (OpenAI / Anthropic / Gemini)** without `DORA_LLM_KEY_ENCRYPTION_KEY` set:
  - [ ] Try to save an API key → 422 with caption "`DORA_LLM_KEY_ENCRYPTION_KEY` isn't configured — paid-provider API keys can't be saved." (Or the friendly form via the error toast.)
  - [ ] Ollama saves still work.
- [ ] **Paid-provider flow with the env var set** (generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`, set in API server's env, restart):
  - [ ] Save API key → toast "API key saved." → page shows "••••••••• (saved)" placeholder. Refresh: still shows saved.
  - [ ] Save model name. Toggle AI on. Send a chat message → routes to the chosen paid provider (verify via outbound network log or by using a deliberately-wrong key and seeing the LlmUnavailable fallback fire).
  - [ ] "Remove saved key" button clears the key (server: `has_llm_api_key` flips false). AI toggle disables again with "Save an API key first" hint.
- [ ] **Per-user isolation**: User A configures Ollama + enables. User B configures OpenAI + enables. Both can chat at once; A's request hits Ollama, B's hits OpenAI. (Logs or outbound network confirm.)
- [ ] **GET /auth/me** never returns the plaintext API key — `has_llm_api_key: true|false` is what the SPA sees. (Browser DevTools → /auth/me response → no `llm_api_key` field.)
- [ ] **Cross-field validation**: try to PATCH `/auth/me` with `{llm_enabled: true, llm_provider: 'openai'}` without a saved key → 422 with "openai needs an API key — save the key before enabling AI mode."
- [ ] **Health endpoint** `/api/health` — `features.assistant` reflects `master_llm_enabled` (not per-user).
- [ ] **Anthropic + Gemini smoke**: configure one of each with a valid key, send a chat that triggers a tool call (e.g. "what's low?"). The response shows the data — confirming the tool-call adapter round-tripped through `ask_assistant`.
- [ ] **Backup → restore** round-trips the new User columns + `master_llm_enabled` (the api-key ciphertext should survive a backup/restore — it's stored as a `LargeBinary` blob like `User.image`).
- [ ] **Engineering hygiene**: grep for old field references — `grep -rn "llm_enabled\|llm_base_url\|llm_model" web_app/src` should only hit per-user identifiers (User.llm_*, UpdateMe, AuthenticatedUser); no `AppSetting.llm_*` references anywhere except migrations / comments.

### Visual rebuild Phase 3 — cross-theme walk — origin FU-283
- [ ] Walk every settings page in Pesto Light + Pesto Dark + Cherry Cola Dark
- [ ] Confirm: sticky nav, dropped card chrome, DoraSegmented in sunken-fill mode, theme card 2px accent border + check_circle badge, page padding breath all read

### Settings Phase 4 — profile picture — origin FU-286
- [ ] `flask db upgrade` applies `a4f7c2e9b6d1` up **and** down, single head
- [ ] `pytest tests/e2e/dora_api/test_auth_flows.py` green (two new tests + no regressions)
- [ ] Browser: upload picture on Account → appears immediately on menu bar (cache-bust), Account header, admin Users row; clear → all revert to icon/initials; hard-refresh both states survive; >4.5MB image rejected with a usable message

### VocabListEditor empty-state copy — origin FU-285
- [ ] Settings → Kitchen setup → Meal slots: with no slots configured, empty-state row reads "No meal slots yet. Create one to schedule meals against." (not "…tagging recipes")
- [ ] Settings → Kitchen setup → Cuisines / Categories / Tools / Dietary tags: with the taxonomy emptied, empty-state row still reads "No {plural} yet. Create one to start tagging recipes." (default unchanged)

### Speech-output toggle on browser without SpeechSynthesis — origin FU-289
- [ ] In a browser lacking `window.speechSynthesis` (or with it stubbed to undefined via DevTools), Settings → Voice's "Let Dora speak her replies" toggle is **visible** (not hidden) when `GET /api/tts/voices` returns `configured: true`
- [ ] DoraChat mute button is visible in the same scenario
- [ ] Toggle stays hidden when Piper is not configured (the endpoint either 503s or returns `configured: false`)

### API access page (C-10 Phase B) — origin FU-218
- [ ] Sidebar entry appears under Admin · global (admin only)
- [ ] `New key` opens dialog → reveals raw key once → copy works → list shows new row with `Never used` + `Accepted 0 / Skipped 0 / Failed 0`
- [ ] Expanding the row shows "Store mappings" panel
- [ ] Push a record from a bearer client against an unknown store → reload → source row shows pending badge + mapping appears in panel marked "pending"
- [ ] Merchant picker assigns it → badge clears
- [ ] Disable / enable / rename / revoke all round-trip
- [ ] Revoked key is rejected by `/api/ingest` immediately

### Decommission scraping (Phase D) — re-pointed nav — origin FU-186
- [ ] Re-pointed Product Search nav opens the admin-configured URL in a new tab (data-gated; R-014 disabled-with-hint when URL unset)
- [ ] System Settings input for `AppSetting.product_search_url` works (saves + round-trips)

### Ingestion: quarantine queue — origin FU-190
- [ ] Push records with unknown store names → they quarantine + appear on the API access page as pending
- [ ] Admin assigns the mapping → next push for the same name succeeds (no longer quarantined)

---

## Onboarding

### FU-184 — onboarding sell-copy honesty pass (2026-07-06) — origin FU-184
- [ ] Welcome card (`/welcome` step 1) reads "I keep your pantry, **shopping and cooking** in one place…" — no mention of "deals".
- [ ] Cinematic hero loop still shows the six stages (Stock → Plan → List → Shop → Restock → Cook), no seventh "Insight/Spend smarter" candidate node dangling in the middle.
- [ ] Focus each loop stage and confirm the sell line describes something you can actually do in the app:
  - **Stock** → Stock Overview shows levels + locations + expiry chips.
  - **Plan** → Cookbook has a "Cookable now" filter; MealPlans has a week board with a shortfall indicator.
  - **List** → items marked Low / Out (or a meal-plan shortfall) appear on the current draft shopping list without a manual add.
  - **Shop** → tick-off works; a **Finish & restock** button appears once at least one item is checked.
  - **Restock** → clicking Finish & restock bumps the ticked items to Stocked (verify one on Stock Overview after).
  - **Cook** → open a recipe → Cook mode walks steps; on completion the ingredient stock levels drop.
- [ ] Persona preview chip "Mostly cooking" — the Dora-centre sell reads "…and **flagging what you can cook now**" (not "suggesting what to cook").
- [ ] `LOOP_INSIGHT` / dimmed "coming soon" chip: **not present** — should have been removed 2026-06-17.

### FU-195 — starter-data per-name picks + inline paste-rows (2026-07-02)
- [ ] On a fresh install, `/welcome` step 3 shows two collapsed cards: "Use Dora's default stock groups" and "Use Dora's default locations". Master checkbox on each header is **fully ticked** by default (matches pre-FU-195 all-on behaviour)
- [ ] Expand the groups card — 7 rows visible (Pantry, Fridge, Freezer, Cleaning, Toiletries, Pet, Other). Each has its own checkbox
- [ ] Untick "Cleaning" and "Toiletries". Header caption now reads "5 of 7 chosen". Master checkbox flips to **indeterminate**
- [ ] Untick everything else. Header caption reads "0 of 7 chosen". Master flips to **unchecked**
- [ ] Click the master while unchecked → all 7 rows tick on. Click while fully checked → all off. Middle-click on indeterminate = tick-all
- [ ] Expand the locations card — Kitchen (Zone) with Pantry / Fridge / Freezer indented, then Bathroom + Cabinet, then Laundry + Shelf
- [ ] Tick just "Kitchen/Fridge" (leaf), leave the Kitchen zone unticked. Master says "1 of 8 chosen", indeterminate
- [ ] Finish the wizard. In Settings → Stock locations only Kitchen (auto-created as FK parent) + Fridge exist. Bathroom / Laundry / their children are **not** seeded. Kitchen's zone row is NOT visually marked as "already existed"
- [ ] Ticking the zone AND a child (e.g. Kitchen + Kitchen/Fridge) seeds both (zone once, child once). No duplicate rows
- [ ] Case-insensitive: manually PATCH the local draft to have a path `"KITCHEN/fridge"` (in DevTools localStorage) → finish → seeds correctly (path comparison is lowercased server-side)
- [ ] Legacy draft resume: manually inject `{"seedGroups": false}` into the localStorage draft, reload — the groups pick-map defaults to all-**unticked** (respecting the legacy explicit-off intent). Any other legacy value → all-ticked default
- [ ] **Paste-rows affordance:** below the two seed cards, an expansion "Paste rows to bulk-add items" opens a textarea. Paste `Milk, Dairy, Fridge\nOlive oil, Pantry\nEmpty,\n , trailing comma test\n` — caption below reads "3 rows ready — added on Finish" (the empty-name and whitespace-only rows drop silently)
- [ ] Click "Queue 3 rows" → toast fires, textarea clears, the queued rows behave like step-4 draftItems (visible on step 4's "Added" list)
- [ ] Finish the wizard → the pasted rows land as stock items with the given group/location names when those exist as seeded defaults; land without a group/location when unknown (matches the step-4 "unknown name = no group" semantics)
- [ ] Full-importer link ("Bringing in a full spreadsheet? Open the full importer instead →") still routes to `/settings/admin/data/import`
- [ ] `POST /onboarding/seed` in the DevTools Network tab: when every default is ticked, the body sends `group_names: null` / `location_paths: null` (compact wire; matches "seed all" semantic). When a subset is picked, the body carries just the picked names / paths in the original casing

### Onboarding C-5.1 / C-5.2 / C-5.3 / C-5.4 / C-5.5 / C-5.6 — origin FU-192
- [ ] **C-5.1:** header reads "Skip"; bailing mid-wizard applies nothing — no username/theme/font change, no seeded groups/locations, no stock items
- [ ] Finish applies everything in dependency order (prefs → seeds → queued first items) and lands on `/`
- [ ] "Show me X" on the tour applies the draft then navigates (does NOT navigate if apply fails — e.g. invalid display name jumps back to welcome with error)
- [ ] Theme picks persist as `system`/`pesto`/`pesto-dark` and repaint
- [ ] Import line reads "spreadsheet or another app" and links to `/data/import`
- [ ] Mid-wizard refresh resumes draft including queued first items
- [ ] **First-user vs subsequent-user tracks (FU-041):** first ever user on a fresh install walks welcome → admin → seed → first_item → finish. A second user registered afterwards walks welcome → finish only — no admin, no seed catalogues step, no "add your first stock item" step
- [ ] **Batch-cooking toggle on the welcome step (FU-041 follow-up):** sits directly under the headcount input, labelled "I batch-cook" with a caption explaining what it unlocks (cook-pool ± / "N free" / shortfall). Default off. Flipping it on and finishing the wizard → `currentUser.batch_features_enabled === true` and the meal-plan recipe picker now shows "N free" caption + ± buttons. Bailing mid-wizard leaves `batch_features_enabled` untouched (like every other pref). Second run of onboarding pre-fills the toggle from the saved value
- [ ] **C-5.2:** first-run opens on story; scenes auto-advance, hero loop pauses for exploration
- [ ] Loop draws itself once, then stages + Dora are tappable + detail panel updates
- [ ] Persona preview toggles provisional Insight chip + Dora-centre copy; previewed persona persists in draft for C-5.3 fork
- [ ] Rail jumps freely Story↔Setup, nothing gated; Skip to setup + Skip work from any scene
- [ ] Reduced-motion: no autoplay/draw, final state shown, fully usable
- [ ] Keyboard: every node / persona / rail dot tabbable with visible focus
- [ ] Layout holds at narrow phone width
- [ ] **C-5.3 (first user):** persona step shows 3 preset cards + Customise pre-selected from hero preview
- [ ] Cooking drops explainer + shortens wizard; Spend/Everything show stock-vs-product explainer before seeding
- [ ] Customise reveals flat flag toggles; (products-off + money-on) combo reachable
- [ ] Flags land only on Finish — bailing changes nothing
- [ ] After Finish: install reflects chosen flags (Settings → System); first user's money/nutrition prefs match
- [ ] A second (non-first) user sees no persona / explainer
- [ ] **C-5.4:** welcome's "how many people do you cook for?" saves on Finish (blank leaves unset); cook mode with headcount → serving scaler pre-scaled; without headcount → falls back to recipe's servings
- [ ] **C-5.5:** seed step renders 5 starter packs; ticking a pack header selects all items (tri-state when partial); expanding lets you tick individual items
- [ ] First-item step's group/location pickers offer names (defaults + pack groups + existing); queued items in slim added list (removable)
- [ ] Finish: ticked pack items + first items pre-located, no duplicates on re-run
- [ ] **C-5.6:** final step shows confetti (suppressed under reduced-motion); OnboardingLoop recap (no autoplay, tappable); persona-relevant flow-cards Open each area + link to guides; Alerts card → `/alerts` (FU-015)
- [ ] Finish / "Open X" completes onboarding (router guard clears)

### Onboarding de-persona — remaining items — origin FU-210
- [ ] Hero-loop renders well without persona shaping
- [ ] No persona/Customise/products step in setup
- [ ] Defaults applied; spend via Settings
- [ ] Draft resume works
- [ ] Story plays without LOOP_INSIGHT
- [ ] Renamed chips ("Mostly cooking" / "Watching spend" / "All of it") read sensibly
- [ ] Finish step is clean
- [ ] `WelcomeWizard.vue` admin step does NOT say "scrape" merchants (stale post-divorce copy)

### Onboarding demo dataset toggle — origin FU-194
- [ ] Wizard's seed step: the "Add a demo recipe + this-week meal plan" card is **off by default** (no auto-tick)
- [ ] Tick it, walk through to Finish on a fresh account → cookbook shows "Spaghetti Aglio e Olio", stock has Spaghetti pasta / Garlic cloves / Olive oil (created if missing), `/meal-plans` shows a current-week plan with one Dinner entry
- [ ] Dashboard's "Next to cook" card immediately surfaces the entry (with a Ready / Missing badge depending on stock levels)
- [ ] Restart onboarding + Finish again with the toggle on → no duplicates (recipe by name still 1, stock items not doubled)
- [ ] Tick the toggle on an account that already has a Spaghetti pasta starter-pack item → demo reuses it (no second "Spaghetti pasta" row)
- [ ] Demo rows behave as plain rows: deletable, renamable, no special "demo" badge anywhere

### Assistant honours configurable expiring-soon window — origin FU-187
- [ ] Settings → app settings: change `expiring_soon_window_days` from 7 to 3 (or via PATCH `/api/app-settings`)
- [ ] Ask Dora "what's expiring soon?" → only items within 3 days are listed (matching the alerts list and the location heatmap)
- [ ] Ask Dora the pantry summary → "expiring soon" count agrees with the alerts page
- [ ] Reset window to 7 → assistant agrees again

### Onboarding sell-copy honesty (P3 Honest gate) — origin FU-184
- [ ] Walk the running app and confirm each loop-stage claim in `onboardingContent.ts` (`LOOP_STAGES`, `LOOP_CENTRE`, `LOOP_INSIGHT`, `NARRATIVE_SCENES`, `PERSONA_PREVIEWS`) is literally true
- [ ] Does finishing a shop really auto-restock?
- [ ] Does cook mode decrement stock?
- [ ] Does price memory + "inflated price" signal exist? (If not, soften/cut)
- [ ] Cut/soften anything the app doesn't back
- [ ] **Don't promise the Insight beat** unless it's actually built

---

## Products & pricing

### My Products + Price History — feedback gaps — origin FU-214
- [ ] **My Products** — L193 "mark inactive: Extra inputs not permitted" is gone
- [ ] L195 link-icon grey/green styling correct (the handoff itself is FU-208)
- [ ] L198 inactive-product styling legible
- [ ] L205/L206 GAP — only a generic "Select on-deal" bulk exists; build "select low-stock-on-deal" / "out-of-stock-on-deal" variants, OR confirm the generic suffices
- [ ] L197 — only mark-inactive (soft) exists, no hard delete (confirm acceptable under ingestion model)
- [ ] **Price History** — L218 selecting products updates the chart
- [ ] L219 card not squished + notify placeholder visible
- [ ] L220 notify-under formats as a price
- [ ] L221/L222 %off text size + chip colour consistent (componentised)
- [ ] L223 hover bubble is theme-aware (today: white-on-white in dark mode)
- [ ] L225 graph reaches the box edge
- [ ] L160 — confirm no *other* Dora search bar has the dark-mode white-on-white contrast bug

### My Products → stock-item "Link…" — origin FU-208
- [ ] From My Products, "Link…" → pick stock item → product links and shows as linked (no bounce)
- [ ] Error toast on failure

### PreferredBuy — origin FU-211
- [ ] Stock item detail: add / rename / reorder (up-down) / remove preferred-buy entries
- [ ] CASCADE on item delete (preferred buys go too)

### Shopping line preferred-buy hint — origin FU-215
- [ ] Pick a preferred-buy hint on a shopping line → persists across reload
- [ ] Clear the hint → persists across reload

### Stock-item Prices section — origin FU-213
- [ ] Log a price observation → derived unit_cost shows correctly
- [ ] Remove a price observation
- [ ] Section is hidden when money features are off

### Cost consumers rebased to unit-cost helper — origin FU-216
- [ ] Stock-value report numbers look right (observation-only items now contribute, where previously they didn't)
- [ ] Recipe cost estimate numbers look right (observation fallback)
- [ ] Any tests pinning totals for observation-only items — update if broken

---

## Build / install / desktop

### Windows desktop build script — origin FU-327
*Requires a Windows box with Python 3.11, Node + npm, and Xcode-free
PowerShell 5+. Author has no Windows dev machine at this session
close-time; walked opportunistically.*
- [ ] `pip install -r requirements.txt` completes (pywebview + pyinstaller install cleanly on Windows Python 3.11)
- [ ] `.\packaging\build-windows.ps1 -Clean` runs SPA build, fetches Piper (`fetch_piper.py` auto-detects and picks `windows_amd64`), fetches default voice, runs `pyinstaller --noconfirm dora.spec` — no crashes past the "OK. Bundle at dist\Dora\Dora.exe" line
- [ ] `dist\Dora\Dora.exe` exists and launches — Dora window opens, SPA loads
- [ ] With WebView2 Runtime installed (Windows 10 or 11): the WebView2 process spawns; no "MissingWebView2Runtime" error dialog
- [ ] Piper voice works out-of-box: Settings → Voice → Amy shows `status: ready`; cook-mode narration plays through WebView2 audio
- [ ] Data persists to `%LOCALAPPDATA%\Dora\` (check the folder exists after first save)
- [ ] `-SkipSpa` reuses an existing `web_app\dist\spa\` build (skip SPA build step; PyInstaller step still runs)
- [ ] `-SkipPyInstaller` runs only the SPA build (early-exit before PyInstaller)

### macOS desktop build script — origin FU-327
*Requires a macOS box with Python 3.11, Node + npm, and Xcode command-
line tools (`xcode-select --install`). Author has no macOS dev
machine at this session close-time; walked opportunistically.*
- [ ] `pip install -r requirements.txt` completes on the target Python (Apple Silicon: arm64 Python; Intel: x86_64 Python — the interpreter arch determines the bundle arch)
- [ ] `./packaging/build-macos.sh --clean` runs SPA build, auto-detects arch (arm64 → `macos_aarch64`, x86_64 → `macos_x64`) and fetches matching Piper, fetches default voice, runs `pyinstaller --noconfirm dora.spec` — no crashes past the "OK. Bundle at dist/Dora/Dora" line
- [ ] `dist/Dora/Dora` exists, is executable (`ls -l` shows `-rwxr-xr-x`), and launches — Dora window opens, SPA loads
- [ ] Piper voice works out-of-box: Settings → Voice → Amy shows `status: ready`; cook-mode narration plays through WKWebView audio (also exercises the FU-287 iOS/WKWebView primer)
- [ ] Data persists to `~/Library/Application Support/Dora/` (check the folder exists after first save)
- [ ] `--arch macos_x64` on an Apple Silicon Mac fetches the Intel Piper tarball (verify `packaging/piper/piper` is `Mach-O x86_64` via `file`); the bundle interpreter arch still matches the venv you're building in
- [ ] `--skip-spa` and `--skip-pyinstaller` flags behave the same as `build-linux.sh`

### Fresh-install first-admin bootstrap — origin FU-200
*Requires a clean DB — delete `data/dora.db` (or point `DORA_DB_PATH` at a fresh file) and restart the API.*
- [ ] Cold-load the SPA → lands on `/setup` (NOT `/login`); page shows the "One-time setup" pill, "Create the first admin account" copy, and an **Email** field that's required (not optional like /register)
- [ ] Type a username + email + a weak password (e.g. "short") → submit → 422 with the password-rules error inline; no admin created
- [ ] Submit a valid username + email + 10-char letter+digit password → success toast, auto-logged-in, lands on `/` (dashboard); `/me` shows `is_admin: true`, `email_verified: true`
- [ ] Refresh the browser → goes straight to the dashboard (NOT `/setup` again); `/auth/bootstrap-required` returns `{required: false}`
- [ ] Manually navigate to `/setup` → bounced to `/` (already-authed) or `/login` (after logout); page is single-use
- [ ] `POST /api/auth/bootstrap-admin` directly with curl → 410 Gone with problem+json body *"An admin account already exists. Sign in instead."*
- [ ] Log out, then register a normal account via `/login` → toggle to register → submit → new user has `is_admin: false`, `email_verified: false` (verify via DB or `/me`), and the verification email is queued (or visible in dev logs)
- [ ] **With ADMIN_BOOTSTRAP_EMAIL set:** wipe DB, set `ADMIN_BOOTSTRAP_EMAIL=admin@example.com` in env, restart → `/setup` accepts only that email; submitting a different email returns a 410 *"This installation is locked to a pre-configured admin email."* (generic — does NOT leak the configured email back); submitting the matching email succeeds as above
- [ ] No regression: existing single-tenant install still loads `/login` first; existing users sign in normally; `bootstrap_required` audit event NOT emitted on subsequent registrations

### Docker + desktop builds bundle the default voice — origin FU-286
- [ ] Next Docker image build: `GET /api/tts/voices` returns Amy with `status: "ready"` on first boot, before any user touches Settings → Voice
- [ ] Desktop bundle (Linux first): `<dist>/Dora/voices/en_US-amy-medium.onnx` (+ `.json`) present; same UI behaviour
- [ ] If Amy isn't Ready, check: GitHub Actions / build runner blocking HF download (look for WARN line); spec's `if os.path.isdir(...)` guard hiding a path mismatch; `bundled_voices_dir`'s `_MEIPASS`/`packaging/voices` path search missing the runner's layout

### Piper synthesis + browser walk — origin FU-291
*Needs env with Piper present (Docker, desktop bundle, or `pip install piper-tts` on Linux/macOS)*
- [ ] Settings → Voice: download a voice → it flips to Ready
- [ ] Preview each voice; switch engine
- [ ] Dora chat with "speak replies" on
- [ ] Cook mode Sous Chef stepping
- [ ] 503 → browser fallback when Piper is absent

### Piper-binary auto-provisioning — Docker + desktop — origin FU-290
- [ ] Run Docker build → confirm `piper` on PATH in the image
- [ ] Linux desktop build (`packaging/build-linux.sh`) → bundle contains `piper/` and the app synthesises
- [ ] Windows desktop build (when scripts land per FU-288) → same

---

## Operator

### Playwright browser-E2E smoke — CI / cross-OS re-run — origin FU-540
- [x] First run GREEN on this Windows dev box (2026-07-12, driving system Chrome via `DORA_E2E_CHANNEL=chrome` since the bundled binary won't download here) — 9 tests: login good/bad creds + authed nav over dashboard/stock/cookbook/meal-plans/shopping-lists + a real /api handshake. Selectors confirmed against the running app.
- [ ] Re-run in CI (bundled Chromium, `DORA_E2E_CHANNEL` unset) once CI is un-commented (FU-405), and on Linux, to confirm cross-OS. (Complements, does not replace, the manual walks below.)

### Fresh-install migration boot — origin FU-549 (FIXED 2026-07-13 — confirm on a clean install)
- [ ] On a machine with a clean `pip install -r requirements.txt` (now pins `alembic==1.14.1`), point at an **empty** database and boot in production mode (the path that runs `flask_migrate.upgrade()`, not the create_all seed path) → the app migrates cleanly to head and starts, **no** `a3e9f6c2d8b4` Alembic batch `'BINARY' has no attribute 'name'` crash. The crash was fixed 2026-07-13 (batch renames now pass `sa.BINARY(16)` instead of `UUIDType()`) and is now covered by `tests/test_migrations.py::test__migrations__upgrade_head_from_empty_succeeds` — this is the eyes-on-the-running-thing confirmation on the real prod toolchain.

### Prod-mode secure-cookies boot warning — origin FU-460
- [ ] Boot the app with `DORA_ENV=production` set and `DORA_SECURE_COOKIES` **unset** → stderr shows the multi-line `═══ WARNING: DORA_ENV=production but DORA_SECURE_COOKIES is unset. ═══` banner before the DI-container / DB / audit log lines
- [ ] Same boot with `DORA_SECURE_COOKIES=true` set → **no** warning banner in stderr
- [ ] Same boot with `DORA_SECURE_COOKIES=false` set → **no** warning banner (explicit operator choice)
- [ ] Same boot with `DORA_SECURE_COOKIES` unset but `DORA_SKIP_PROD_VALIDATION=true` set → **no** warning banner (escape hatch works)
- [ ] Boot with `DORA_ENV=development` (or unset) and no `DORA_SECURE_COOKIES` → **no** warning banner (dev mode never nags)
- [ ] With `DORA_ENV=production` + `DORA_SECURE_COOKIES=true`, log in to the SPA over HTTPS → DevTools → Application → Cookies → `dora_session` row shows `Secure: ✓`
- [ ] Same setup but with `DORA_SECURE_COOKIES=false` (or unset) → `dora_session` row shows `Secure: ✗`

---

## Cross-cutting

### Text-scale follow-through into component-internal text — origin FU-025 (2026-07-10)
*Fix landed via `quasar.variables.scss` rem-overrides (Quasar's `body { font-size: 14px }` and ~30 component vars) plus `.q-field__bottom` / `.q-bar--dense` rescues in `app.scss`. Walk one form-heavy page and one table-heavy page at both Small and Extra-large in Settings → Appearance → Text size, and confirm the previously-unresponsive text now moves.*
- [ ] Settings → Appearance → **Text size = Small** — cold-load Stock overview: level dropdown value, chip labels ("Needs attention", "Essential", "Open / in-use", "Needs check"), row text, footer counters all render smaller than default
- [ ] Same page, **Text size = Extra-large** — every one of the above renders larger; nothing gets stuck at the default 14px
- [ ] Open Recipe edit (any recipe → Edit): **input labels, field-native text, `.q-field__bottom` helper/error text, dense-field bottom text, toggle labels ("Enable this recipe", etc.), checkbox labels, chip inputs (tags / dietary), button labels ("Save", "Cancel"), the toolbar title** all track the pref at Small and XL
- [ ] Stock item detail: same test — labels, values, dropdown text, `Buy verdict` badge + card headline all scale
- [ ] Dashboard: `DoraScoreCard` hero number, trend badge, per-component captions all scale (they were px-hardcoded)
- [ ] Cookbook overview `FilterBar`: filter chip labels, dropdown labels (Cuisine / Category / etc.), sort dropdown all scale
- [ ] Shopping list detail: line item text, quantity/unit inputs, totals footer all scale
- [ ] Cook mode: step text scales (this was already fine via rem)
- [ ] **Icons stay put.** Quasar's `q-icon`, tab icons, avatar/checkbox/radio glyphs, meal-plan slot icons, decorative Onboarding letters, camera scanner UI, price-history chart labels, dashboard 3px/7.5px micro-gauge — **do not** scale with the pref. This is intentional.

### R-029 hide-don't-nag sweep — Product Search nav entry — origin FU-500 (2026-07-08)
*The one behavioural change from the R-029 sweep: when `features.products` is on but no `product_search_url` is configured, the Product Search entry disappears from the nav instead of rendering disabled-with-tooltip. Quick eye-check to confirm the three states.*
- [ ] With **products off** in Settings → System → Features → Products: no Product Search entry in the main navigation (unchanged behaviour)
- [ ] With **products on** but `product_search_url` **blank**: no Product Search entry in the main navigation (the new behaviour — was previously visible but disabled with a "Not set up yet …" tooltip)
- [ ] With **products on** and a **valid URL** configured: Product Search entry visible, clicking opens the URL in a new tab (unchanged behaviour)
- [ ] Side menu (narrow viewport) mirrors the above: entry appears/disappears in lockstep with the main menu
- [ ] Confirm no other surface still advertises "Product search not set up" — should be silent everywhere except the config row on Settings → System → Features

### Base-component `<BaseButton>` sweep — origin FU-504 (2026-07-08)
*40 raw `<q-btn>` sites were migrated to `<BaseButton>` in one pass; `BaseButton` also gained a new `filled-icon` variant + optional `color` prop. Pure componentisation refactor — visuals should be identical everywhere except MyProductsPage's empty-state CTA (raised → unelevated primary, intentional). Cheap eye-check per surface, no action beyond looking.*
- [ ] **RecipeCard chef-hat button** (cookbook overview, any recipe card) — round filled icon, colour toggles primary/warning based on cookability; click still opens cook mode
- [ ] **DoraChat** — open the assistant panel: header voice / help-what-can-D.O.R.A.-do / close buttons render as round icon buttons; mic + send buttons in the input; chip-row rotate-suggestions button; in-message action rows (Confirm / Cancel / Snooze 1d / Dismiss / Add to <list>) render identically
- [ ] **MyProductsPage** — open the page: bulk-select mode banner buttons (Select / Select all visible / Select on-deal / Add on-deal to list / Unlink / Mark inactive / Done) render + wire; row-overflow menus (`⋮`) still open; empty-state "Open Product Search" CTA is now unelevated primary (visual delta from raised to unelevated is expected); dialog action rows in the "unlink" and "mark inactive" confirmations
- [ ] **ScanOverlay** — trigger the scanner (Stock overview → scan button, if scanning enabled): the Submit button in the overlay renders on the dark background
- [ ] **Settings pages** — Backup & restore (clear-file button), Data import (browse button), Email settings (Save + Clear buttons), Push settings (Test push + Clear subscription), API access (copy token button), Users admin (copy invite-link button) — all render + still wire
- [ ] **Kept-raw carve-outs render unchanged** — Help page "Meet D.O.R.A." accent CTA + release-notes anchor; RecipeCookMode warning-coloured pause button; ShoppingListDetail dynamic-coloured outline buttons; StocktakeRunner change-level big button; Backup/restore grey button; timezone + locale settings secondary-outline buttons

### Security response headers — origin FU-459 (2026-07-07)
*Confirms the app-wide CSP + framing / referrer / sniff headers land on every response and don't break any page. Do this walk with DevTools **Console + Network** panels open — a CSP violation logs a red console error naming the blocked directive.*
- [ ] Any request in DevTools → Network → Headers → **Response Headers** shows `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer-when-downgrade`, `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; …frame-ancestors 'none'; …`
- [ ] Cold-load the SPA → no CSP violations in Console
- [ ] Walk Dashboard, Stock overview, Stock item detail, Cookbook overview, Recipe detail (with an image), Cook mode, Meal plans, Shopping list detail, Settings → each page renders normally, no red CSP errors on any surface
- [ ] Recipe / product / store images render (base64 `data:` blobs + external `https:` sources both work under `img-src`)
- [ ] Upload a recipe/user image (data-URL / blob path) → preview renders (blob: is allowed)
- [ ] Print view opens and renders (if any style-src / script-src violation would clobber it, it'd be visible here)
- [ ] Piper TTS synthesis + assistant chat still work end-to-end (connect-src covers the `/api` calls; anything to an external LLM URL relies on `https:` allowance)
- [ ] `curl -I` any endpoint → same four headers present on the plain HTTP response

### Recipe-picker inline-create toast — origin FU-319 (2026-07-06)
- [ ] Open any recipe in the cookbook, edit ingredients, add a new ingredient row → type a name that doesn't match any existing stock item → tap the "Create '<typed>'" no-option row in the picker → **positive toast reads `Added "<name>" to your pantry.`** (not the old "Created stock item …" copy)
- [ ] After the toast, navigate to Stock overview → the new item is there with the shipping-default level (top of the levels list). Confirms the toast reflects reality.

### Help chips (FU-503 / FU-044) — 2026-07-06
*Walk the surfaces in `docs/04_proposals/IMPL_PLAN_HELP_CHIPS.md`. For each
one: hover the `(?)` icon on desktop and long-press on mobile. Confirm the
tooltip renders (not clipped), and the copy reads correctly.*
- [ ] Dashboard: Kitchen health card title, You've saved card title
- [ ] Reports: Year-over-year card title, Meals-worth metric in Meals cooked card
- [ ] Alerts: header "N need action · M FYI" tooltip; per-kind tier segmented control in the Manage panel
- [ ] Meal plans: Shortfall / cook-by chip in the week status *(FU-304 closed 2026-07-07: Board page retired; the chip lives on `MealPlansOverview` only.)*
- [ ] Recipe detail: "N unallocated of M cooked" caption in the Available meals card
- [ ] Cookbook overview: Cookable now filter chip has a `(?)` beside it explaining the distinction from "Have meals in pool"
- [ ] Cook mode: Sous Chef button tooltip now includes the fuller explanation; hands-free mic tooltip explains it's independent of narration
- [ ] Stock overview: `(?)` beside Essential, Will auto-add on low, Open / in-use, Needs check filter chips
- [ ] Stocktake runner: cadence subline ("Checked every X · Y days overdue") has a `(?)`; Push 3 days button tooltip renders
- [ ] Shopping list detail: Finish & restock button tooltip; Plan-which-day button tooltip renders the extended copy
- [ ] Price history: "currently X% above" has a `(?)`; "Your usual" caption has a `(?)`
- [ ] My products: Select on-deal button tooltip
- [ ] Any product row's PriceEntry (multipack disclosure): "Add pack count (multipack)" ghost button tooltip
- [ ] Notifications settings: Compact format help text now reads "One line per deal (item, price, store). Off = expanded card…"
- [ ] Assistant settings: Enable AI mode description reads "Off keeps every chat reply rule-based. On routes *tool-able requests* through your configured provider — requests that need real actions…"
- [ ] Dark mode + all themes: `(?)` icon inherits colour from parent context (R-002); no hardcoded colour bleeds through
- [ ] Mobile viewport: tooltips are readable at 360px (may need to reflow); long-press activates them

### iOS / macOS-WKWebView audio-unlock primer — origin FU-287
*Needs iPhone / iPad (Safari) or the macOS desktop bundle (WKWebView).
User doesn't have iOS device access as of 2026-07-03 — sits until then.
Every other platform: no visible effect; already worked.*
- [ ] iOS Safari, `speechEnabled` on, `voice_engine=piper`: open Dora chat → type a message → tap send → **Dora's reply plays audibly** (this is the flow that used to lose the gesture credit across the LLM `await` + synth fetch)
- [ ] Same setup, `voice_engine=browser`: reply plays via browser SpeechSynthesis (browser voice was more forgiving but subject to the same gate; primer helps here too)
- [ ] Cook mode on iOS Safari: **start the app, tap around a bit (any interaction), then enter cook mode → "next step" narration plays** — no gesture is needed on the "next" tap itself; the session-level primer covers subsequent voice narration
- [ ] Timer-narration edge case (documented, best-effort): start a timer in cook mode, leave the tab open several minutes without interacting → timer completes → **visible Notify still fires** (load-bearing signal); audio narration + finish tone may or may not — do not treat their absence as a regression
- [ ] macOS desktop bundle (WKWebView): same three checks as iOS — chat reply, cook-mode step narration, in-session timer narration
- [ ] Android Chrome + desktop Chrome/Firefox: **no regression** — voice output still works, nothing sounds different. First-gesture briefly plays a silent muted `data:audio/wav` primer (44 bytes); should be inaudible and invisible in DevTools' network tab
- [ ] Reload the page → primer fires again on the next gesture (session-scoped, not persisted)

### Filters button toolbar alignment (R-027 fix, 2026-07-02)
- [ ] `/stock` — the Filters button (right end of the top toolbar row) sits **flush** with New item / Scan / Stocktake / Bulk select / Export. Zoom in if needed: their tops + bottoms line up pixel-for-pixel
- [ ] `/stock` — when a filter is active, the **Clear** button appears to the left of Filters and BOTH sit flush with the other toolbar buttons (Clear didn't have this bug before either, but verify it's still aligned after the multi-root refactor)
- [ ] `/products` — Filters + Clear flush with Toolbar's other actions
- [ ] `/cookbook` — Filters + Clear flush with the recipe toolbar's other actions
- [ ] Toggling filters on/off doesn't shift any neighbouring button horizontally (FU-121 stability preserved)
- [ ] Active-count badge on the Filters button still renders (floating primary badge) when filters are engaged

### C-19 shared auth-shell + AuthButton (2026-07-02)
- [ ] Cold-load the app on slow-3G throttle. `#pre-mount-splash` paints midnight `#1f2647` immediately; when Vue mounts and `AuthShell` takes over, there is **no** light→midnight flash. One unified moment
- [ ] Splash pulse: the mascot logo pulses at 60fps while `authStore` bootstraps; blobs are visibly present but motion-frozen (D2 `backdrop="quiet"`) — no CPU cost
- [ ] Cannot-connect variant: kill the API (stop `dora_api`), reload. Splash shows the offline mascot + "Can't reach Dora's brain" + the retry button. Retry button matches the login-primary teal gradient
- [ ] `/login` — primary Sign In button is pixel-identical to pre-migration (teal gradient, hover lifts, shadow bump)
- [ ] `/login` — "Need an account? Register" now renders as a **full-width amber-gradient button** at the same size as Sign In (was: tiny ghost text). Toggle click still swaps the form mode
- [ ] `/login` — "Forgot password?" now renders as a **full-width ghost button** at the same size (was: fine-print router-link). Click routes to `/forgot-password`
- [ ] `/login` register mode: password-policy fineprint ("Passwords must be at least 10 characters…") still shows under the form
- [ ] Register with bad credentials → the field-level error still surfaces (regression check on `useFormErrors` plumbing)
- [ ] Login with wrong password → generic "Sign-in failed. Check your username and password." error surfaces (the 401-opaque path still works)
- [ ] `/setup` (bounce a fresh install with `admin_user_present=false` or hit the route while logged out on a bootstrap install) — visual should be **identical** to pre-migration. One-time-setup badge sits above the title; Create admin button is teal-gradient primary
- [ ] `/forgot-password` — canvas matches Login (blobs, mascot NOT shown, frosted card). "Send reset link" primary; "Back to sign in" ghost. Success banner (submit any email) still renders. Feedback L16 satisfied
- [ ] `/reset-password` — with a token: card shows the two password inputs + primary "Reset password" + ghost "Cancel". With no token: banner "This reset link is missing a token" + ghost "Cancel". After success: positive banner + primary "Continue to sign in"
- [ ] `/verify-email?token=<good>` — success card renders with green tick + "Continue to sign in" primary. `?token=<bad>` — error card renders with "Resend verification" ghost. Click it → BaseDialog opens; submit any email → toast + dialog closes
- [ ] `/confirm-email-change?token=<x>` — pending → success/error card renders; "Continue" primary routes to `/`
- [ ] `git grep '\.auth-shell\b' web_app/src/` returns zero from a fresh clone (no aux page still declares the class locally)
- [ ] `/welcome` (onboarding wizard) — canvas now shows the midnight blobs behind the wizard cards. Header ("Dashy Dora" title + mascot avatar + Sign out) is legible over midnight (white text on midnight). Sign out button still tappable and logs you out
- [ ] `/welcome` onboarding scenes — Scene 1 (scatter icons) legible on midnight, question-mark glyph reads amber. Scene 3 (brain mascot) centred + visible. Scene 4 (persona pills) pills readable (frosted-glass background)
- [ ] Reduced-motion (toggle OS setting or DevTools emulation) on `/login`: blobs and mascot freeze in place; card enter animation off; button hover no longer translates
- [ ] Mobile viewport (~360px) on `/login` and `/setup` — mascot shrinks to 72px, tucks above the card (not fighting card overlap)
- [ ] Password policy note under register mode still readable inside the card foot area

### P8-01 rename: no stray "Discount Dora" anywhere user-facing (2026-07-01)
- [ ] Dashboard hero: mascot image alt text (inspect → "Dashy Dora"), any screen-reader announcement of the greeting says "Dashy Dora" nowhere in it (the label is only on the image alt now)
- [ ] Help page → tab "About": header reads "Dashy Dora {version}"; the update-available banner (force it by mocking version if needed, or just eyeball it) reads "A newer version of Dashy Dora is available"
- [ ] Assistant → ask "what's new" and "what version are you" — both replies begin "You're on Dashy Dora …" / "I'm Dashy Dora …" (never "Discount Dora")
- [ ] Browser tab title on every route: `{page} | Dashy Dora`
- [ ] PWA install prompt (Chrome address bar → install app) shows "Dashy Dora" as the app name (from productName in package.json)

### D.O.R.A. bot rename + acronym easter egg (2026-07-01)
- [ ] Chat header (open the burger-mascot chat): the bold label to the left of the AI/Basic chip reads **D.O.R.A.** (dots-and-all). Hover it → tooltip shows "Delicious Organised Restock Assistant"
- [ ] Help page → "Meet D.O.R.A." button appears (the accent-coloured one with the smart-toy icon). Click it → lands on `/help/dora`
- [ ] `/help/dora` header reads "Meet D.O.R.A." with the caption spelling the acronym (bolded initials) followed by "Sentient burger robot. Your in-app pantry buddy. Slightly chaotic."
- [ ] Chat suggestion chips include "Thanks D.O.R.A." (not "Thanks DoraBot"). Clicking it replies with the sparkle/thanks flow the old chip triggered

### Nav-state policy: filters survive navigate-back, reset on reload (A8 §3, 2026-07-01)
- [ ] Stock Overview: type in the search box, tick a couple of filter chips, change the sort. Click into any stock item detail → hit browser back → search text, chip states, and sort are all preserved. Scroll position on Stock Overview is restored too
- [ ] Cookbook: same drill — set search, toggle favourites-only + cookable-now-only, change sort axis + direction. Navigate to a recipe → back → all preserved, including expanding/dietary/tools filters
- [ ] My Products: set search text + a store filter + the "On deal only" chip. Navigate to another route (Dashboard) → back → preserved
- [ ] Hit F5 (full reload) on any of those three pages → all filters reset to defaults, scroll to top. This is the intended "clean slate" behaviour
- [ ] Sign out and sign back in as the same user → filters reset (sign-out flow currently does a full reload; if it doesn't in future, FU-355 will wire an explicit clear)
- [ ] Other list pages (MealPlans, ShoppingLists, Stocktake, admin settings) still reset on nav-back — they haven't been migrated yet (FU-354). That's expected, not a bug

### `/data/barcodes` redirects + shell shows two cards — origin FU-340 (2026-07-01)
- [ ] Direct-navigate to `/data/barcodes` (via URL bar or a stale bookmark) → the router redirects you to `/settings/kitchen-setup/qr-labels`. No blank flash, no 404, no old page contents visible
- [ ] `/data` shell now shows **two** nav cards: Backup & restore, Import. NO "Scanning & QR labels" card (regardless of the `scanning_enabled` flag state)
- [ ] Direct-navigate to `/data/barcodes?action=scan` (the retired PWA shortcut target) → still redirects to the QR labels settings page (query string dropped is fine). No console error
- [ ] Stock item detail page: the "Print label" tooltip on a stock item's Dora-QR button no longer references "Data → Barcodes" — the copy explains barcodes register a Product, not a stock item

### `/data/export` page retired — origin FU-339 (2026-07-01)
- [ ] Navigate to `/data` — the shell now shows **three** section cards: Backup & restore, Import, Scanning & QR labels (the last one gated on `scanning_enabled`). **No** "Export & print" card
- [ ] Direct-navigate to `/data/export` in the URL bar → lands on the app's not-found route (or router error page — whichever the router does today for unknown paths). Does NOT render a blank data shell
- [ ] From a recipe detail: the Print action still opens the print-view in a new tab (unchanged)
- [ ] From a shopping list detail: the toolbar menu still exposes "Print / Save as PDF" (unchanged)
- [ ] From `/stock`: the toolbar export menu still exposes CSV + Print (unchanged)
- [ ] From `/meal-plans`: the Print icon-button added in FU-338 still opens the print-view (unchanged). *(FU-304 closed 2026-07-07: `/meal-plans/board` retired; nothing to check on the old Board page.)*
- [ ] No console errors on any of the above about a missing route or a missing component

### Settings shell — independent sidebar/main scroll — origin worklog 2026-07-01
- [ ] Open `/settings/account` on desktop (≥1024px width). The sidebar sits on the left; the main pane on the right. **The window itself does not scroll** — only the two panes do (no browser scrollbar on the outer page while inside settings)
- [ ] Scroll the main pane deep into a long settings page (e.g. Preferences) — the sidebar stays exactly where it is (no drift, no sticky-header jitter)
- [ ] Scroll deep into the main pane, then click a sidebar nav item → **the window does NOT jump**. The new section loads with the main pane at the top; the sidebar's scroll position and the app header stay put
- [ ] With a very long sidebar (admin users, expand Kitchen setup + Admin sub-groups) — the sidebar itself scrolls independently; the last nav item is reachable via that inner scroll
- [ ] Resize the window to <1024px → the layout collapses to single-column with the top tab strip; window scroll returns for mobile. Resize back to ≥1024px → dual-scroll restored, no layout thrash
- [ ] Navigate from `/settings/*` to a non-settings route (e.g. `/stock`) and back — no visual glitches; scroll positions on other pages behave normally (window scroll back on those pages)

### Mobile header: wordmark hidden, right buttons pushed to edge (2026-07-01)
- [ ] At ~380px width (or DevTools mobile viewport), the top toolbar reads left → right: burger · Dora mascot · page title · (big gap) · alerts bell · profile avatar. **No** "Dashy Dora" text next to the mascot, **no** Help icon
- [ ] Tap the mascot → routes to `/` (Dashboard). Tap the burger → drawer opens with the full nav (Stock, Cookbook, …)
- [ ] Rotate to landscape / resize past ~1024px width → wordmark reappears next to the mascot, MainMenuButtonStrip fills the middle, Help icon reappears between alerts and profile
- [ ] No horizontal scroll or overflow on the toolbar at 320px, 375px, 414px widths

### Main-menu indicator stuck colour after sub-route nav — bug fix (2026-06-30)
- [ ] On `/cookbook` → click into a recipe → the underline indicator under Cookbook stays the **accent** colour (yellow in the default theme), **not** the hot-pink flash colour
- [ ] Same check for: `/stock` → click into a stock item; `/shopping-lists` → click into a list; `/settings/account` → switch tabs within Settings
- [ ] On any of the above pages, navigate to a different top-level (e.g. Cookbook → Stock) and back — flash colour briefly appears during the slide, then settles to accent on the new active button each time
- [ ] No regression to the slide animation when clicking between top-level buttons — the indicator still slides smoothly across with the flash colour during the transition

### Header peer buttons (Help + Account) with active ring — feature (2026-07-01)
- [ ] Header right side shows three icons in order: AlertsBell · **Help & guides** (?) · **Profile avatar**. No dropdown chevron / menu anywhere
- [ ] Click the Help icon → navigates to `/help` (no dropdown opens). Tooltip on hover reads "Help & guides"
- [ ] Click the avatar → navigates to `/settings/account` (no dropdown opens). Tooltip on hover reads the current username
- [ ] No Sign-out anywhere in the header — Sign-out lives only on Settings → Account (the existing red "Sign out" button on that page is still present and works)
- [ ] On `/help` or `/help/dora`: **Help icon pulses** in the slide-flash colour, then settles into the 3px accent ring. Avatar stays inactive (no ring)
- [ ] On any `/settings/*` page: **avatar pulses + settles** to the accent ring. Help icon stays inactive
- [ ] Switching between Settings sub-pages (`/settings/account` → `/settings/preferences` → `/settings/notifications`) — avatar ring stays lit, **no re-pulse**
- [ ] Switching between `/help` and `/help/dora` — Help ring stays lit, **no re-pulse**
- [ ] Cross between sections (`/settings/account` → `/help`): avatar ring fades out (~320ms), Help ring pulses + settles. Reverse direction also smooth
- [ ] Navigating between Help/Settings and the main menu (e.g. `/help` → `/cookbook`): header ring fades out, main-menu Cookbook underline fades in. No stuck flash colour
- [ ] Theme switch — both buttons' flash + resting colours follow the active theme's `--nav-slide-flash` + `--brand-accent` tokens
- [ ] Mobile (`<md`): both buttons render in the header (next to the AlertsBell), rings still work
- [ ] **Reduced-motion** (DevTools → Rendering → "Emulate CSS prefers-reduced-motion: reduce"): rings appear in the resting accent colour **without** the pulse beat on either button

### R-016 lazy hydration sweep — five pages — origin FU-221
- [ ] Cold-load each of `/recipes`, `/recipes/<id>`, `/stock`, `/stock/<id>` — page renders normally (stock items + stock levels populate, no blank pickers / missing names)
- [ ] In DevTools Network, navigate away from one of those pages and back without a full reload — no second `GET /stock-items` or `GET /stock-levels` fires (the store's `ensureLoadedAsync` short-circuits when already hydrated)
- [ ] Post-mutation refresh paths still work (e.g. create a stock item → list updates; rename one → name updates) — those still call the raw `getXAsync()` and must not have been broken by the sweep

### R-016 extension to recipe / shoppingList / location / recipeVocab / mealSlot stores
- [ ] Cold-load `/dashboard`, `/meal-plans`, `/shopping-lists/<id>`, `/cookbook/<id>/cook`, settings → Stock Locations — every page renders normally (recipes, lists, locations, vocab, meal slots all populate)
- [ ] DevTools Network: navigate dashboard → meal-plans → dashboard → meal-plans without full reload — `GET /recipes`, `GET /shopping-lists`, `GET /locations`, `GET /cuisines`/`/categories`/`/dietary-tags`/`/tools`, `GET /meal-slots` fire **once** total, not on every revisit
- [ ] Recipe create / edit / delete still refreshes the overview (post-mutation calls `recipeStore.getRecipesAsync()` directly — must keep working)
- [ ] Shopping-list mutations (add line, finish shopping, remove from list) still refresh summaries (post-mutation calls `shoppingListStore.refreshAsync()` — must keep working)
- [ ] Location CRUD on settings → Stock Locations still refreshes the tree (post-mutation calls `locationStore.refreshAsync()` — must keep working)
- [ ] QuickAddSheet open → shopping-list summaries appear; CreateStockItemDialog open → location picker has options
- [ ] DoraChat: ask a recipe-aware question on a cold session — recipes + vocab populate before the answer; ask again on a warm session — no second fetch

### Drag-and-drop affordance parity (post `useDragDropList` refactor) — origin FU-326
- [ ] **Shopping list lines** (`/shopping-lists/<id>`): on a list that's not done and not mid-shopping with no grouping active and bulk mode off, grab any row → source row dims to ~50% opacity, drop-target row lights with a primary-coloured outline ring. Drop reorders, server persists, refresh round-trips
- [ ] **Shopping list — reorder gates**: list is `done` → no drag (cursor stays default; can't pick up). List `shopping` → no drag. Activate grouping → no drag. Enter bulk mode → no drag. Return to "active draft, no grouping, no bulk" → drag resumes
- [ ] **Recipe steps** (recipe edit, Structured mode): grab a top-level step → source dims, drop-target ring lights; drop within sibling group reorders. Try to drop a top-step onto a sub-step (different parent) → no drop accepted (no ring on dragover). Top-steps still can't become sub-steps via drag (intentional — that's the separate sub-step affordance)
- [ ] **Recipe ingredients** (recipe edit, "Ingredients" card): grab a row → dim + drop ring exactly the same shape and colour as the two surfaces above. Within same section reorders; across sections also moves the row and copies the target's section assignment
- [ ] **Visual identity check**: side-by-side, the three surfaces use the same opacity, same ring colour, same ring thickness, same handle hover treatment. Open browser devtools → both surfaces apply `.dora-dnd-row` / `--dragging` / `--drop-over` classes (not `shopping-line-dragging` / `recipe-step-row--dragging` / `ingredient-row--dragging`)
- [ ] **Cross-list isolation**: start dragging a shopping line, hover over the recipe editor's ingredient list (in a second tab won't work — single-tab check). Start a recipe-step drag while in the recipe-steps editor → only steps light up, never ingredients (because the MIME is distinct per list)

### Error-handling rollout — origin FU-099-V
- [ ] **Friendly translation** — submit a recipe with `servings = "abc"` → inline `error-message` on Servings reads "Must be a whole number." (not "Input should be a valid integer..."); toast caption is the generic "Couldn't save — check the highlighted fields." with `· ref: <8-char>` suffix
- [ ] **Domain error** — create a stock item with a name that already exists → toast caption shows the friendly domain message + ref suffix
- [ ] **5xx path** — induce a 500 (e.g. stop API mid-save) → existing global toast still fires with "ref: <8-char>" (no regression)
- [ ] **Network drop** — kill the API → "Can't reach the server…" caption renders; no `ref:` suffix
- [ ] **Dev visibility** — DevTools: every failed API call (400/401/403/404/422/5xx) shows `[api] METHOD path → status code (correlation-id)` with structured `details` blob
- [ ] **Unknown Pydantic code** — induce one (custom validator raising non-standard error) → toast reads "This value isn't valid."; DevTools shows `raw` + `code` so a dev can add it to `PYDANTIC_FRIENDLY`

### `formatQuantity` rollout — origin FU-321
- [ ] Meal-plan "This week's shopping" — `unit="g"` reads `"needs 250g · …"`; `unit="tbsp"` reads `"needs 1 tbsp · …"`; null unit reads just the quantity
- [ ] Sequential Builder Dialog preview list — same three cases; rounded number is what `formatQuantity` receives
- [ ] Substitute ratio caption on stock-item detail: `1 tbsp → 3 tsp` reads exactly that (both halves spaced); direction "this → that"
- [ ] Substitute ratio caption in cook-mode swap picker: same ratio reads identically. `250 g → 1 cup` reads `"250g → 1 cup"` (asymmetric — mass tight, volume spaced)
- [ ] Recipe print view (window.open from RecipeDetailPage export): `2 tbsp olive oil` → `"olive oil — 2 tbsp"`; `250 g flour` → `"flour — 250g"`; `1 onion` (no unit) → `"onion — 1"`; `salt` (both null) → just the name, no em-dash

### Unsaved-changes guard rollout — origin FU-322
- [ ] **AccountSettings** — edit `usernameDraft`, click a sidebar link → confirm dialog. Cancel → still on page. Confirm → nav completes. Repeat for `emailDraft`. Revert draft → nav with no prompt
- [ ] **AccountSettings exclusions** — pick a new profile picture (saves immediately) then nav → no prompt. Type a new-password value (don't submit) then nav → no prompt
- [ ] **AdminSystemAssistantSettings** — flip `enabledDraft`, edit `baseUrlDraft`, edit `modelDraft` in any combination, then nav → prompt. Save → next nav passes through clean
- [ ] **beforeunload** — dirty page refresh → native "Leave site?" prompt. Clean page refresh → no prompt

### Chunks 3–5 client + DB-backed query paths — origin FU-051
- [ ] `npm install` + `npm run lint` + `quasar dev` boots cleanly
- [ ] Recipes overview: cookable filter + footer count + compare dialog
- [ ] Recipe card chip renders
- [ ] Recipe detail sidebar + editor "Missing" badge
- [ ] Meal-plans palette
- [ ] Dashboard "Cookable tonight" + count
- [ ] Dora's "what's missing" answers
- [ ] Dashboard primary-list stats + shopping-list detail headline totals (Chunk 5) — confirm $ remaining / savings / counts match what the lines imply
- [ ] Server: `GET /api/recipes?cookable=true|false`, `?max_missing=1`, `/api/dashboard/summary`, `GET /api/shopping-lists/<id>` (check `totals` block) against seeded data

### Cookbook C-cross Chunk 1 — feature-flag panel — origin FU-110
- [ ] `alembic upgrade head` applies `a3b8e2f4c1d7` on SQLite + Postgres; `verify_mappings()` passes for reshaped `AppSetting`
- [ ] As admin: Settings → System → **Features** panel — five toggles (Meal planning ON, Money / Nutrition / Companion ingestion / Weekly deals emailer all OFF); captions read
- [ ] Each toggle on → toast + persists across reload
- [ ] Each toggle off → toast + persists
- [ ] As non-admin: panel renders "no admin permissions" banner; toggles not visible
- [ ] `curl /api/health` JSON carries `features.meal_planning` / `features.money` / `features.nutrition` / `features.companion_ingestion` / `features.deals_email` alongside pre-existing `auth` / `audit` / `scanning` / `multi_user` / `email` / `assistant`; values match panel
- [ ] Composable freshness: `flagsLoaded.value` is `true`, computeds match panel; flipping in tab 1 only refreshes tab 1's cache (per-session, documented)
- [ ] Migration safety: install using meal planning sees `meal_planning_enabled=True` after migration
- [ ] Save error path: disable network / PATCH 500-out → toggle reverts + negative toast
- [ ] Pesto Light + Pesto Dark + Cherry Cola Dark — panel reads in all

### C-cross Chunk 2 — per-user money opt-in — origin FU-111
- [ ] `alembic upgrade head` applies `b5c1d9a4e3f2`; `verify_mappings()` passes for reshaped User
- [ ] As regular user: Settings → Account → new **Money & budgets** card appears above Grocery budget with toggle, off by default
- [ ] **Install ON, user OFF (default):** toggle enabled, Grocery budget hidden. Flip on → toast → Grocery budget appears → set budget + period → reload → toggle on, budget settings persisted
- [ ] **Toggle off again:** toast → Grocery budget hides → reload → toggle off, **but saved budget is still on server** (flip back on → same value)
- [ ] **Install OFF (admin disables in System → Features → Money):** per-user toggle disabled with caption "This install has money features turned off…"; Grocery budget stays hidden
- [ ] PATCH wire: flip sends `{ money_features_enabled: true|false }` only (DevTools)
- [ ] `GET /api/users/me` carries `money_features_enabled` in response
- [ ] Composable: `useMoneyEnabled().moneyEnabled.value` = `installEnabled && userEnabled`
- [ ] Error path: PATCH 500s → toggle reverts + negative toast
- [ ] Pesto Light + Dark + Cherry Cola Dark

### C-cross Chunk 3 — per-user nutrition mode + reserved seam — origin FU-112
- [ ] `alembic upgrade head` applies `c8d3f4a9b2e1`; `verify_mappings()` passes for reshaped User + AppSetting
- [ ] Settings → Account → **Nutrition** card: three-way toggle reads **Off** by default; captions read
- [ ] **Install OFF, user Off (default):** whole toggle disabled, caption "This install has nutrition turned off…"
- [ ] Admin enables `nutrition_enabled` in System → Features. Return to Account → Nutrition: Off + Simple now clickable, Complex disabled. Caption explains complex needs a source
- [ ] Flip to Simple → toast → reload → still Simple
- [ ] Flip back to Off → toast → reload → still Off
- [ ] Server rejects complex without seam: PATCH `{ nutrition_mode: 'complex' }` → 400 with "Complex nutrition mode needs a nutrition data source configured…"
- [ ] Configure the seam: admin PATCH `{ nutrition_db_source: 'usda-fdc' }` → `GET /api/health` reports `features.nutrition_complex_available: true`
- [ ] Refresh Settings: Complex now clickable. Pick it → toast → reload → still Complex
- [ ] Re-empty the seam: PATCH `nutrition_db_source: ''`. Refresh: user remains on Complex server-side (no auto-rewrite), but Complex option disabled + caption updates. User can switch back to Off/Simple
- [ ] PATCH wire: `{ nutrition_mode: '<mode>' }` only
- [ ] `/me` carries `nutrition_mode`
- [ ] Pesto Light + Dark + Cherry Cola Dark

### C-cross Chunk 5 — image-display opt-in + deferred image column — origin FU-114
- [ ] `alembic upgrade head` applies `d4a7c9b3e8f1`; `verify_mappings()` passes for reshaped User
- [ ] New user: `show_recipe_images` + `show_stock_images` both default **true**. Existing users post-migration same (server default `'1'`)
- [ ] Cookbook overview header has **image** icon button next to "Import from URL". Tooltip "Hide recipe photos · saved across sessions"
- [ ] Cards render photos as today
- [ ] Recipe detail with image → header preview shows photo
- [ ] **Click toggle:** icon flips to `image_not_supported`; toast "Recipe photos hidden."
- [ ] Cards now show coloured-initial placeholder; DevTools Network: `GET /api/recipes/<id>/image` is **NOT** called for visible cards
- [ ] Recipe detail (with image): header preview shows placeholder; **editor's pick/clear still work** — pick new image → preview shows freshly-picked image (dirty-form branch ignores opt-in). Save → reload → preview hides again (saved image gated)
- [ ] **Toggle back on:** toast "Recipe photos shown."; cards + detail show photos; saved images survived
- [ ] `/me` carries `show_recipe_images` + `show_stock_images` on every load. Toggle PATCH sends only `{ show_recipe_images: bool }`
- [ ] Cross-session persistence: flip toggle, sign out, sign back in → state remains. Second device → same
- [ ] **FU-090 perf fix:** load cookbook overview with N≥10 recipes that all have images. Payload substantially smaller (image bytes no longer in rows; only `has_image: bool`). Backend logs / `sqlalchemy.echo` show no `SELECT image FROM Recipe` on list path
- [ ] **Stock-side flag round-trips** even though no UI writes it yet (FU-106 will land C-1 row redesign): `PATCH /me` body `{ show_stock_images: false }` survives reload
- [ ] Pesto Light + Pesto Dark + Cherry Cola Dark — new icon button reads in all

---
