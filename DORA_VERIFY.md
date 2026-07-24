# Dora Verification Checklist

The QA pile — anything that needs eyes on the running thing to confirm.
Browser observations, boot-time / operator smoke checks, container startup,
migration round-trips, CLI/desktop launch checks — whatever needs manual
verification lives here. Grouped by surface; pick one and walk it
top-to-bottom.

> **Campaign in progress (2026-07-16):** this pile is being cleared via
> agent-verified evidence reports — see `DORA_VERIFY_TRIAGE.md` (repo root)
> for the batch plan, per-section classification, and session protocol.
>
> **⚠️ STANCE (owner, 2026-07-20) — verify by driving the app once, don't
> auto-test everything.** Clear an item by **driving the running app** (agent or
> owner) to confirm it works, then delete the line — that's the default. Write an
> automated test only for a **stable, low-churn contract** that's costly to
> re-check by hand (prefer backend/Vitest). **Playwright is smoke-only now**
> (`auth.setup`+`login`+`smoke`); the feature-flow specs were deleted 2026-07-20.
> Some pinned-notes below cite a now-deleted Playwright spec — those items are
> just manual once-off checks under this stance; backend/Vitest pin-notes remain
> valid. Full rationale: `DORA_VERIFY_TRIAGE.md` top banner.

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
- [ ] AI mode ON → "add milk" still uses the richer LLM propose→confirm flow (unchanged), not the Basic path.
- [ ] **Greeting once-per-user (FU-360.5).** Fresh browser, log in as user A → the "Hi! I'm Dora" hint appears once; dismiss it → it doesn't return for A across reloads/logins. Log in as a *different* user B in the same browser → B sees the hint once (proving it's per-user, not per-browser).
- [ ] **Mode slider — enabled/toggle path (FU-360.3).** With AI mode configured (Settings → Assistant: provider + model + base URL/api key saved, install master ON), open Dora → the chat header shows a two-position pill "Basic | AI" with a skewed thick knob glowing on the active side. Tap the inactive side → knob slides across with the glow, PATCH `/auth/me` fires, and `/assistant/status` re-probes; the "AI mode unavailable" banner appears if the LLM isn't currently reachable. Tap back → returns to Basic. *(The disabled/no-LLM state + rem-scaling are verified above; this enabled-toggle path needs a configured LLM → owner-walk.)*
- [ ] **FU-360.4 (DS4 hover-flash regression) — fix landed 2026-07-12.** Hover the launcher / mascot repeatedly, and specifically *hover off* → mascot should stay put, no disappear-and-animate-back-in. Cause: the one-shot `dora-entrance` keyframes lived on the base `.dora-bubble-launcher-inner` rule, so when the hover-bob animation stopped and the base declaration reasserted, `dora-entrance` (with 300ms delay + `both` fill) restarted from its `scale(0) opacity: 0` frame. Moved onto a `.is-entering` modifier removed via `@animationend` after the entrance plays.
- [ ] **FU-386 (cookable chip).** Open Dora on the Dashboard or Cookbook → tap the **"Cookable now"** / "Find a recipe to cook" chip → lands on the cookbook filtered to cookable recipes (the `?cookable=true` contract, confirmed live end-to-end).
- [ ] **FU-515 B.3 (tool-arg bound, AI mode only).** With AI mode on, ask Dora to **"push the milk expiry by 99999 days"** → she declines with a "more than ~10 years — give me a sensible number" style message rather than proposing an absurd date. (Sanity check on the boundary cap; normal pushes like "+3 days" still work.)

## Currency & locale (FU-043) — origin FU-043
- [ ] Change currency via the input → blur/Enter → toast "Currency set to USD." + money surfaces re-render without a reload *(q-input `:model-value` not synthetically drivable — formatting/propagation itself proven; this is the keystroke→toast half)*
- [ ] Enter invalid inputs: `US` (2 chars), `USDD` (4 chars), `US1` (digits), lowercase `usd`; invalid locale `en_AU`, `english`, `en AU` — each shows an inline red error, no toast, no server round-trip *(validation logic present in `AdminSystemLocaleSettings.vue` `onSaveCurrency`/`onSaveLocale`; q-input-gated for driving)*
- [ ] Change currency to `EUR`/locale `de-DE` → **MoneySettings budget input prefix** flips to `€` and **PriceEntry dialog price input prefix** flips to `€` (the money-gated input decorations — money features OFF in the verify seed, blocked on [[FU-592]])
- [ ] Dora chat / Cook mode: hold-to-talk mic uses the household locale for speech recognition (device + mic — switch locale then hit the mic and confirm the recognised-text shape follows)

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
*(Dialog body won't paint in the hidden pane; the two-button Add↔Change `(camera)`/`(file)` + swatch + Remove structure is source-confirmed (shared `ImageSourcePicker`). Interactions below need a real OS file picker → owner/device-walk.)*
- [ ] Settings → Stores → **Add store** → the dialog's logo row now shows two buttons (`Add logo (camera)` + `Add logo (file)`) instead of the old drag-drop file input; the `StoreLogo` swatch preview above remains
- [ ] Pick a real PNG / JPEG / WebP from the file browser → preview updates immediately; typing a name + Save creates the store with the logo
- [ ] Retry with an unsupported file (e.g. a PDF) → a red inline caption appears under the picker with a friendly message; no `q-notify` toast, no crash
- [ ] Edit an existing store with a logo → the two buttons now read `Change logo (camera)` + `Change logo (file)`; the "Remove existing logo" button still shows and clears the image
- [ ] After Remove is tapped and a new image picked, the buttons flip back to "Change" labels (the draft has a fresh image)
- [ ] On mobile (or with `forceCamera` on): the camera button opens the OS camera picker directly

## PWA install + offline (build now ships in PWA mode) — origin FU-336
Requires a **built** frontend served over HTTPS or localhost (SW won't register on plain-HTTP). Use the Docker/nginx image, the desktop bundle, or `quasar serve dist/spa` after `npm run build`.
- [ ] DevTools → Application → **Service Workers**: `sw.js` registers + activates (no errors); Application → **Manifest** shows name "Dashy Dora", theme `#f5c462`, the 3 shortcuts, and no manifest warnings
- [ ] Browser offers **Install** (Chrome desktop/Android address-bar install icon); after install the app opens standalone (no browser chrome) and the window/title is Dora
- [ ] Go offline (DevTools → Network → Offline) and reload → the app shell still loads (not the browser's dinosaur); navigating to an uncached route shows Dora's `offline.html`, not a raw error
- [ ] API calls while offline fall back to the last cached GET (NetworkFirst) rather than hanging; coming back online refreshes normally
- [ ] Deploy a new build over the top → within a reload or two the "new version" flow kicks in (skipWaiting/clientsClaim) and you're not pinned to the old worker (confirms the nginx `sw.js` no-cache rule)
- [ ] Web Push: with VAPID configured, subscribe from Settings/Alerts and confirm a push arrives (the SW is what receives it) — ties off the previously-unreachable push path
- [ ] iOS branding (FU-552, fixed 2026-07-15): add to home screen on a real iPhone → the home-screen icon is Dora's D/D on the pale-yellow tile (not a blue gear, no black corners). Android/Chrome/favicon were always Dora-branded — confirm still fine
- [ ] Safari pinned-tab (FU-552, fixed 2026-07-15): on older Safari that still honours `mask-icon`, pin the tab → the `safari-pinned-tab.svg` "D/D" mark renders recoloured to theme gold, not a blue gear. **Low priority / legacy** — Safari 15+ ignores mask-icon and uses the regular icons; this is really just confirming the hand-authored monochrome D/D vector reads acceptably (it couldn't be rendered headlessly this session — the in-app browser blocks `file://`/`localhost`)

## Runtime backend URL (browser + PWA) — origin P8-10
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
*(Server contract fully pinned: `Cookable`/`Not cookable`/`max_missing`/`expiring_within_days` all filter correctly and exclude unlinked recipes from the cookability axes — `test_recipe_filters.py` (14 tests) + `test_recipe_router.py` `CookableTrueFilter`/`CookableFalseFilter`/`MaxMissingFilter`/`ExpiringWithinDaysFilter` [`expiring_ingredient_count` asserted]. The identity-map regression can't recur silently. Only the card-render eyeball stays.)*
- [ ] While filtered, spot-check a recipe card: its ingredients list and cookability badge render correctly (the fix also touched what filtered pages eager-load)

### Free-text ingredient path in the recipe editor — origin FU-506
*(Tri-state cookability server contract pinned: a required unlinked ingredient makes cookability `null`/Unknown [not True/False], multiple unlinked still null, an unlinked *optional* ingredient doesn't gate — `test_recipe_cookability.py` + `test_recipe_router.py` `UnlinkedRequiredIngredient__CookableIsTriStateNull`. The editor UI interactions below stay owner-walk.)*
- [ ] Open any recipe → **Add ingredient** → in the picker, type a name that matches nothing (e.g. "star anise" on a fresh install)
- [ ] Two options appear under the option list: **Create "star anise"** and **Use "star anise" as free text (no pantry link)** (the second option, secondary-coloured with a pencil icon)
- [ ] Tap **Use as free text** → row's picker field label flips to **Free-text ingredient**, and the string `"star anise"` appears as a muted italic caption beneath the picker
- [ ] Save the recipe → refresh → the row still shows as unlinked with the same caption
- [ ] The recipe's cookability badge renders as **Unknown** (not "In stock" / "Missing") — the tri-state *value* is pinned above; this checks the badge render
- [ ] Later, on the same row, type in the picker and pick an actual stock item → row flips back to linked; caption disappears

### RecipeEditDialog stub-creator reshape — origin FU-095
*(Server stub-defaults pinned 2026-07-20 in `test_recipe_router.py` `create_recipe__NameOnly__CreatesFreeformEmptyStub`. **UI verified live 2026-07-22 (browser drive):** Cookbook → **New recipe** opens a modal with **exactly four fields** — Name* / Cuisine / Category / Collection — and **none of the heavy fields** (no ingredients/image/instructions/dietary/tools/times); the primary button reads **"Create & open"**; filling only Name ("QA Stub Recipe") + Create & open **closed the dialog and navigated to `/cookbook/<new-id>`** with the detail page showing the name; **Cancel from an empty form created nothing** (recipe count 11→11). Stub deleted after. The **edit-existing-from-overview** path is **N/A by design** — the recipe cards expose only ♥ / chef-hat / add-to-list and there is **no edit/pencil action anywhere on the overview** (deep edit happens on the detail page); the RecipeEditDialog's edit-mode is not surfaced from the overview.)*

### Recipe importer — bulk-linker + PWA share target (Chunk 6) — origin IMPL_PLAN_RECIPE_IMPORTER
*(Verified live 2026-07-22 (browser drive; fed by an imported recipe with 4 unlinked ingredients): the **Unlinked ingredients** entry renders in the settings sidebar and the page (`/settings/admin/data/unlinked-ingredients`) lists each unlinked ingredient as a group row **`raw_text · Used in N recipes`** with a per-row Link-to-stock-item autocomplete / **Link** / **Create new** — count correct at "Used in 1 recipe" (the **FU-588** "Used in 0" regression is gone). **Create new** on the "1 lemon, juiced" row fired the toast **"Created "1 lemon, juiced" and linked in 1 recipe."** (item = `raw_text`), dropped the group count 4→3, and on the source recipe the lemon row became **linked** (`unlinked_ingredient_count` 4→3) with cookability staying `null` (neutral, still 3 unlinked). Created item + recipe deleted after. Below = the empty-state, the autocomplete/Link-button UI (Quasar q-select not synthetically drivable — endpoint pinned in `test_unlinked_ingredients_bulk_link.py`), and the Android share target.)*
- [ ] With no unlinked rows in the DB, the page shows the empty-state ("Every recipe ingredient is linked to a stock item.")
- [ ] Pick a stock item from the autocomplete → click **Link** → toast confirms "Linked '<raw_text>' in N recipe(s)"; the group disappears *(the `bulk-link` endpoint is pinned in `test_unlinked_ingredients_bulk_link.py`; this bullet is the autocomplete + toast UI — the Create-new sibling path was verified live)*
- [ ] Auto-complete typing filters to matches; empty search shows the top of the alphabetical list (capped at 50)
- [ ] **PWA share target — Android Chrome only.** After installing Dora as a PWA (from the browser's Install prompt), open a recipe on RecipeTin Eats in Chrome → hit Share → **Dashy Dora** appears in the sheet → tap it → Dora opens on the cookbook overview, the paste dialog pops with the page text pre-filled in the textarea + the recipe URL in "Where's this from?" → hit Import → new recipe lands in the cookbook
- [ ] Refresh the page after the share flow — the `?share_text=…&share_url=…` params are gone from the URL, so the dialog doesn't re-open on refresh
- [ ] Recipe-detail edit mode → Freeform steps → textarea shows the hint *"Paste the recipe text or type freeform — Ctrl+V works."* below the box

### Recipe importer — paste-based rebuild (Chunk 5) — origin IMPL_PLAN_RECIPE_IMPORTER
*(Pinned server-side: `import-from-url` is deleted → 404 and `import-from-content` is the only import path (`test_recipe_import_routes.py`); the whole paste corpus parses to a minimum shape (`test_parse_recipe_from_text.py`, parametrized over every fixture); and the **taste.com.au2 video-carousel + Coles price chrome is stripped** — no "Estimate based on"/"Fulfilled by"/"coles-logo"/"Show ingredient quantity" in ingredients, no "Next video thumbnail"/"more" steps, step count fenced (`taste_video_carousel_cruft_stripped`, added 2026-07-20). The browser paste/preview/navigation flow below stays owner-walk.)*
*(Verified live 2026-07-22 (browser drive): the **Import** button opens the paste dialog — a "Paste the recipe here" textarea, a "Where's this from? (optional)" URL input, and a caption naming the Ctrl+A/Ctrl+C→paste flow + supported sites. Pasted a synthetic Quinoa-Salad page + a source URL → **Import → new recipe on the detail page, no degraded banner**; server parse: `name="Zesty Quinoa Salad"`, `servings=4`, source URL stored, **3 freeform steps**, **5 ingredients** with `raw_text` preserved. The **fuzzy matcher linked "2 tbsp extra virgin olive oil" → Olive Oil** while the other 4 stayed unlinked; the detail page renders those as **"Free-text ingredient"** rows showing the quoted text ("1 cup quinoa", "1 lemon, juiced", "100g feta cheese") — confirmed on a fresh GET (survives round-trip). With unlinked rows present the recipe is **`cookable=null` → neutral chip** (not True/False). Recipe deleted after. Below = the multi-site corpus (backend-pinned) + the link-one-row-switches-back half.)*
- [ ] Repeat with an AllRecipes page and a Half Baked Harvest page — each imports without the "couldn't auto-structure" degraded banner *(the parse corpus is backend-pinned over every fixture in `test_parse_recipe_from_text.py`; one live import above showed no degraded banner)*
- [ ] After import, **link one free-text row** to a real stock item → its label/caption switch back to the plain "Stock item" picker with no leftover quote *(the Quasar autocomplete isn't synthetically drivable; the bulk-link endpoint itself is pinned in `test_unlinked_ingredients_bulk_link.py`)*
- [ ] Confirm `Recipe.source` on the imported recipe carries the URL you typed (if any) and is blank when omitted — nothing was fetched server-side
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
- [ ] Backup → restore round-trips `RecipeStep` / `RecipeStepIngredient` / `RecipeStepTool` in FK-correct order

*(Step-text validation pinned 2026-07-20 in `test_recipe_router.py`: a whitespace-only step text → 400 "Every step must have non-empty text." (`WhitespaceOnlyStepText`), a truly empty string → 422 validation (`EmptyStepText`). The structure round-trip + importer + backup bullets above stay owner-walk.)*

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
*(Server contract pinned 2026-07-20 in `tests/e2e/dora_api/test_new_recipe_version_numbering.py`: **numbering** (singleton → v2, then v3, and a version off a copy → v4 = next-by-sibling-count, not parent — fixed **FU-589**, was skipping v2); **group allocation** (singleton allocates `version_group_id`, back-fills the source, peers share it; a grouped source reuses it); **inheritance** (linked + unlinked + optional ingredients, cuisine, category, servings, instructions, source, kcal, notes; copy starts un-favourited with a fresh id); **independence** (editing the copy leaves the source untouched). **Fixed a production-severity bug in the same unit — FU-590: new-version of any recipe WITH ingredients 500'd** (autoflush of unparented clones) and silently unlinked linked ingredients (R-032 noload clone). The tools/steps/tags/collection/image inheritance + the version-card UI below stay owner-walk.)*
- [ ] `alembic upgrade head` applies `e1f6a2b4c8d9` on SQLite + Postgres; `verify_mappings()` passes
- [ ] Open a recipe with structured steps → editor's Structured/Freeform toggle populates correctly (latent bug from Chunk 6 / cook-mode Chunk 5)
- [ ] New version also inherits **tools, structured steps (with sub-step + ingredient refs remapped), dietary tags, collection, and image** (image shows without re-upload) — *the ingredient/cuisine/category/scalar inheritance is pinned above; these richer clones stay owner-walk*
- [ ] Edit the **source** → save → the copy is unchanged (the copy→source direction is pinned above)

*(Verified live 2026-07-22 (browser drive, Veggie Stir Fry — has 5 ingredients): a **singleton hides the "Other versions" card**; kebab → **New version** created **"Veggie Stir Fry (v2)"** with **no 500** (confirms the **FU-590** new-version-with-ingredients fix live), **navigated to the copy**, which **shares a back-filled `version_group_id` with the source** (both list 1 sibling), **inherited all 5 ingredients + cuisine (Asian) + servings (3)** and **starts un-favourited**; the **"Other versions" card + "v2" label render** on the copy, and the **source now shows the card too**. **Deleting the v2** (→204) dropped the source back to a singleton and the **card disappeared** (item "delete → card updates"). Item 191 structured/freeform toggle + the richer-clone inheritance + backup stay owner-walk.)*
- [ ] Meal-plan picker + cookable filter see both siblings; allocations stay per-recipe
- [ ] Backup → restore round-trips `version_group_id`

### Cookbook Chunk 9 — cost + simple nutrition, opt-in — origin FU-116
*(Flags-ON UI verified live 2026-07-23 via FU-592 (cost card, kcal input, nutrition card, Kcal sort/filter, wire shape); residuals below are migration/theme/extra-matrix owner-walks.)*
- [ ] `alembic upgrade head` applies `e5b9d2c8a4f3`; `verify_mappings()` passes
- [ ] Sort-by Kcal **direction toggle** flips the label between "Highest kcal first" / "Lowest kcal first" and recipes with no kcal sink to the bottom *(the Kcal sort option + Kcal≤ filter presence is verified above; this is the direction-label + ordering half)*

*(Cost math pinned 2026-07-20 in `test_recipe_router.py` estimated_cost tests, exercising the real `StockItemProduct → Product → ProductOffer` join: `estimated_cost = Σ qty × (offer.price_now / size_value)` rounded to 2dp; **partial coverage** returns `estimated_cost_priced_count`/`estimated_cost_total_count` counting only priced ingredients; **no priced ingredient → `estimated_cost` is None** (card hidden client-side). Guards the FU-463 SQLite-uuid-binding regression. The card/badge render + the money/nutrition flag matrix below stay owner-walk.)*
- [ ] Old freeform Nutrition expansion gone from detail page; an existing recipe with a `nutrition` text value still saves cleanly
- [ ] Money OFF + Nutrition ON: cost hidden, kcal surfaces visible
- [ ] Money ON + Nutrition OFF: cost visible, no kcal surfaces
- [ ] Pesto Light + Pesto Dark + Cherry Cola Dark — both new cards read

### Cookbook Chunk 10 — multi-part recipes via named sections — origin FU-119
- [ ] `alembic upgrade head` applies `f6c8e3a9b1d2` on SQLite + Postgres; `verify_mappings()` passes for `RecipeSection` + `section_id` on ingredient/step
- [ ] Existing recipes still load (no sections = flat list, location grouping)
- [ ] Create a recipe with two sections ("Sauce", "Filling"), assign per ingredient, save, reload → sections persist; RecipeCard shows "2 parts" badge
- [x] Cook mode: ingredient panel groups under section names; step card shows the section as a chip; "All steps" repeats header at each transition — *verified live 2026-07-22 via a contrived 2-section ("Sauce"/"Assembly") structured recipe: ingredient panel grouped by section, step card carried its section chip, All-steps list showed section headers. (Sections also round-tripped on API create — the "persist across reload" half of the create bullet above.)*
- [ ] Delete a section → rows fall back to "Main" (SET NULL), save/reload → no orphans, no FK error
- [ ] Rename a section without touching rows → rows stay pinned (editor sends ingredients[] + sections[] together)

### Cookbook Chunk 4 — detail page cleanup — origin FU-089
*(Verified live 2026-07-22 (browser drive, seeded, dark theme): **sticky toolbar composition** — Mark cooked / Cook mode / Log cook… / Print / Save + kebab (New version · Delete recipe), with **no CSV** anywhere; **Mark cooked** bumps the pool +1 (available 2→3) + stamps last-cooked to today + fires a "Marked as cooked." toast; the **name field is editable**, and a **blank name blocks save** with the inline error **"Give the recipe a name."** while the server name stays unchanged (Save is dirty-gated — disabled on a clean form); **each ingredient row shows a single chip** (Missing `bg-negative` wins over Stocked `bg-positive`) and **missing rows carry a red `.miss` tint** (stocked rows transparent) — the box was legible in dark theme; the **cook-mode guard on a not-cookable recipe** shows *"Start cook mode? This recipe isn't cookable now — 2 ingredients missing."* with Cancel / Start anyway, and **Cancel closes it without navigating**; **Cook mode → Exit returns to the recipe detail page** (not overview); the **"Available meals"** label renders. Remaining below = layout/visual/dialog-flow owner-walks.)*
- [ ] Sticky toolbar **stays pinned at the top on a narrow window** (layout at phone width)
- [ ] **Log cook…** logs N meals (dialog flow); **Print** opens the print view
- [ ] Ingredient row **without a stock item** blocks save with a prompt *(the unchanged-name-save-succeeds half is backend-pinned — the rename-to-own-name 422 fix)*
- [ ] Cook-mode guard: **outside click doesn't navigate**, and the **unsaved-edits variant** shows "Save & start" which only proceeds on save success
- [ ] meal ± shows no not-allowed cursor flash (subjective)

### Cookbook Chunk 3 — card redesign + naming — origin FU-088
*(Verified live 2026-07-22 (browser drive, seeded): recipe cards render the **placeholder media tile** (initial letter when no image), **emphasised name**, time/servings/difficulty, the **cuisine·category·time-of-day chip line**, and **dietary chips**; **collection groups collapse** on header click (cards → hidden); the **main-nav label reads "Cookbook"**; and the **search box narrows** the grid by name+ingredient (11 → 2 on "egg"). The `g r` keyboard nav is untested; the old "command palette 'Go to Cookbook'" clause is **stale** — the Ctrl/Cmd-K palette was retired. Remaining below = interaction/badge/subjective.)*
- [ ] MealStepper ± adjusts cooked pool live (decrement disabled at 0); also on **stock-item detail's recipe cards** *(Verified live 2026-07-22 on the **recipe detail page**: the ± live-adjusts the pool 3→2→1→0, **"Remove one meal" disables at 0**, and restoring via + persists (server `available_meals`=3). The card + stock-item-detail instances stay owner-walk.)*
- [ ] Allocated badge appears only when `committed_meals > 0`; **red** when `available_meals < committed_meals`, neutral otherwise — API must return `committed_meals` field *(needs a meal-plan allocation to raise `committed_meals` — owner-walk / future contrivance)*
- [ ] Card has only Cook as primary; kebab = add-all-to-list + add-to-meal-plan (no Edit/Duplicate/Delete); clicking the card opens detail *(the [♥][chef-hat][add-to-list] footer render is verified above; the kebab actions + card→detail nav stay owner-walk)*
- [ ] "meals box" on the card + equal-height within a grid row (V-pack eyeball — the meals box hides at 0 meals; equal-height is per-row layout)

### Cookbook Chunk 3+ revision (FU-088 → cookbook card revision) — origin FU-088 (revision)
- [ ] Image hide/show toggle works (per-user, persists across sessions)
- [ ] Allocated badge appears + drops correctly from overview
- [ ] Meals-cooked field relocates to planner correctly
- [ ] Meta-line swap renders correctly
- [ ] Optional ingredients render with `(optional)` hint + dimmed rows in cook mode
- [ ] Cookable signalled via cook-button colour (no separate dim)
- [ ] Difficulty filter + sort axis works
- [ ] Picker modal opens with per-ingredient checkboxes + Optional separator
- [ ] Time-of-day vocabulary in edit dialog
- [ ] Per-row Optional checkbox in both editors
- [ ] Cookability still server-derived

*(Verified live 2026-07-22: the **`[♥][chef-hat][add-to-list]` footer layout** (3 icon buttons per card) and the **meta-line** (cuisine·category·time-of-day + time/servings/difficulty) render correctly on the seeded cards. Image hide/show persistence, allocated-badge drop, optional-ingredient dimming, difficulty filter, and picker modal stay owner-walk.)*

### Cookbook Chunk 5 — images + tools — origin FU-091
- [ ] `alembic upgrade head` applies `b8e3f1a6d2c4` on SQLite + Postgres; `verify_mappings()` passes for `Tool`
- [ ] `GET /api/tools` returns seeded tools; Settings → Recipe tags & categories has a Tools editor (create/rename/delete + recipe counts)
- [ ] Recipe create/update round-trips `tool_ids`; edit dialog + detail page tools multiselect populate + save *(Verified live 2026-07-22: the detail-page **Tools multiselect populates** — Veggie shows "Wok"; and `tool_ids` round-trips on create — the contrived structured recipe was built with 2 tools and both rendered in its cook-mode Tools panel. The edit-dialog populate + in-UI save round-trip stay owner-walk.)*
- [ ] Overview Tools tri-state filter (include/exclude) works
- [ ] Upload on detail page → save → image shows on detail + card (via `GET /recipes/<id>/image`); change + remove work; cache-busts after save; >4MB rejected client-side; create dialog can attach image
- [ ] Backup → restore round-trips Tool/RecipeTool + recipe images

### Cookbook Chunk 2 — tag taxonomy — remaining items — origin FU-085
- [ ] Item 3: `repository.get(Recipe).all()` selectin-loads `recipe.cuisine`/`.category` (no null cuisine/category in assistant + global_search)
- [ ] Item 5: overview cuisine/category single-selects filter end-to-end; tri-state DietaryTagFilter cycles +/−/neutral and stays open; RecipeCard shows names + tag chips *(Verified live 2026-07-22: the Filters panel renders Cuisine/Category/Time-of-day/Difficulty single-selects + Meals≥/Missing≤/#ingredients≤/Collection; RecipeCard shows names + dietary chips; and the filter narrowing works (search 11→2, and the cookability/cuisine/max-missing logic is backend-pinned in `test_recipe_filters.py`). The dietary tri-state **cycle** interaction (+/−/neutral, stays open) is the only unwalked half.)*
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
*(Verified live 2026-07-22 (browser drive, Veggie detail): the **mode toggle shows Structured / Freeform / Image** and each renders its own editor (Freeform textarea "One step per line…"; Structured step editor; Image mode). **Non-destructive flip** confirmed for the freeform payload — the 199-char instructions survived a full Structured → Image → Freeform cycle. The per-mode payload preservation for the structured + image editors, and the image-editor specifics below, stay owner-walk.)*
- [ ] Mode flip preserves the **structured + image** payloads too (only the freeform half was driven)
- [ ] Image-mode editor: pick multiple files from disk; pick via mobile camera prompt (`accept="image/*" capture="environment"`); reorder via ↑/↓; remove; cap warning at 20
- [ ] Save with `steps_mode='image'` posts `step_images[]` as data URLs; `/api/recipes/<id>/step-images/<image_id>` returns the original at the right MIME
- [ ] Cook mode in image-mode renders full-width scroll gallery; tap-to-zoom opens; ingredient panel + finish flow + B8 substitute swaps + Sous Chef behave as before
- [ ] Auto-detect timer card hidden; standalone timer affordance still usable (manual via Sous Chef commands)
- [ ] New-version of an image-mode recipe clones the step images
- [ ] Alembic migration applies cleanly on existing DB; `steps_mode` backfilled to `'structured'` only where `RecipeStep` rows exist

---

## Cook mode

### Recipe personal notes in cook mode — origin FU-432 (RD-29)
*(Server contract pinned in `tests/e2e/dora_api/test_recipe_notes.py`: create/read/update/clear round-trip [existing 2 tests] + **new-version carry-over** [added 2026-07-20]. **Detail-field placement + cook-mode card render verified live 2026-07-22:** the **Personal notes (optional)** field sits **below Source URL** (tops 1691 vs 1601) and is a **distinct textarea** from the freeform instructions field (own placeholder "Your own notes — …"); with a two-line note PATCHed on, cook mode renders a **"Your notes" card** carrying both lines with the **line break preserved** ("Line one… ⏎ Line two…"); a note-free recipe (Veggie pre-note + the contrived structured recipe) shows **no** card. Note cleared afterward.)*

### Cook Mode Chunks 1–3 — origin FU-096
*(Verified live 2026-07-22 (browser drive, seeded, Veggie Stir Fry — freeform, 3 steps, 1 tool): **ingredient grouping by base location** — Pantry (Jasmine Rice / Soy Sauce / Garlic) · Fridge (Broccoli) · Freezer (Chicken Breast); **no mid-cook stock-level chip** on rows (only the substitute `mdi-swap-horizontal` buttons render); **quantity spacing** — `g`/`ml` attach (`300g`, `30ml`) while word units get a space (`2 cloves`, `1 head`); the **Sous Chef** voice button (mic-message icon) + a **(?) "Sous Chef commands"** popover listing Next / Previous·Back / Repeat / Start·Pause·Reset-timer / Exit; and the **step timer auto-detected** "2 minutes" → 02:00 with a fill-bar, Start → live countdown (→01:58) + PAUSE/Reset, Reset → back to 02:00. Remaining below = the timer's expiry behaviour + the no-location fallback group.)*
- [ ] No-location fallback: a recipe with an ingredient whose stock item has **no location** lands it in a **"No location"** group (all seeded Veggie ingredients had locations)
- [ ] Timer expiry: at 0 the bar turns **negative colour**, a **toast fires**, and a **short beep** plays (no-ops on iOS/PWA without a gesture)
*(An e2e driver for the finish flow exists but is **deferred/flaky** — `web_app/e2e/cook-mode-finish.wip.ts` (NOT in the active `*.spec.ts` run; see FU-591): it drives Finish → per-row Down-one/Out/Unchanged → server-verified level drops + "You saved N meals"/"All eaten" + Cancel-fires-nothing and passes cleanly in a fresh env, but flakes under load/repeat [cook-mode loads the stock store async, so a fast "Finish" click can race ahead and the decrement no-ops]. Revive once the e2e infra is stabilised. Until then the whole finish flow below stays owner-walk.)*
- [ ] Chunk 1 finish flow: finish → dialog "Finished cooking?" shows one row per used ingredient with current level chip, action chips (Down one / Out / Unchanged, default Down one), override dropdown, per-row Add-to-list
- [ ] `meals_cooked` defaults to **0**; Done with 0 → toast "All eaten — hope it was good."; N>0 → "You saved N meals — enjoy." (with pluralisation)
- [ ] Per-row override beats action: pick explicit level for one row → Done flips that row's stock_level_id to the override; `Unchanged` rows leave stock alone
- [ ] Fail-soft: a row pointing at a deleted stock item shouldn't stop the others (Promise.allSettled)
- [ ] Click-out cancels: open finish dialog, click outside → dialog closes, **no** level/cook calls fired
- [ ] Session swap interaction: swap an ingredient to its substitute, finish → the substitute's level (not the original) updates

### Cook Mode Chunk 5 — highlight + tools + hints — origin FU-100
*(Verified live 2026-07-22 (browser drive): the freeform path first (unstructured text-match highlight / tools-panel-present / no-checkbox / All-steps-jump / "Done"-gone), then the **structured visuals** via a contrived cookable structured recipe (3 steps incl. a sub-step + hints, 2 tools with one step-referenced, 2 named sections): **step-referenced ingredient rows tint + get a 3px left accent** (blue @0.16 — unreferenced rows flat); the **step-referenced tool lights** (Frypan, opacity 1) while the **unreferenced tool dims** (Saucepan, `.dim`, opacity 0.55); the **"Sub-step" chip** renders on the sub-step card and the sub-step is **indented in "All steps"** (32px vs 16px); a **hint line renders with a lightbulb icon**. (Bonus — Chunk 10 sections: the step card carries its **section chip** and the ingredient panel + All-steps list **group by section name**.) Remaining below = the no-tools case, the deferred finish flow, and cross-theme tint.)*
- [ ] No tools panel when the recipe lists no tools
- [ ] Finish flow lists *every* ingredient on the recipe (with swaps applied), regardless of mid-cook interaction *(finish flow deferred/flaky — see the finish-flow note above)*
- [ ] Pesto Light + Pesto Dark + Cherry Cola Dark — highlight tint reads in dark mode

### Cook Mode Chunk 6 — cooking-for headcount rescale — origin FU-101
*(The `scaleQuantity` rounding contract is fully pinned in `web_app/test/unit/scaleQuantity.spec.ts` (23 tests) — a dedicated describe block added 2026-07-20 pins the literal checklist cases: rescale up/down 1.5×/0.5× [200g→300/100, eggs], fraction snap 1 cup→¾/1½, countable 1 egg→1/2 [0.75 up, floored at 1], floor-at-1, sub-tolerance ½, and the 7.5g→7½ gram edge. The component input-clamp + session-only bits below stay owner-walk.)*
*(Verified live 2026-07-22: the **"Cooking for" input defaults to the recipe's `servings`** — seed recipe `servings=3` → input shows 3 (the seed user has no `household_headcount`, so `servings` wins). The blur-clamp code (`onCookingForBlur`, `RecipeCookMode.vue:670`) is correct by inspection — `<1` or non-finite → 1, else floor — but the numeric clamp + session-only reset couldn't be driven via synthetic events (Quasar's numeric q-input ignores injected values), so the two below stay owner-walk.)*
- [ ] Blur clamp: clear input → blur → re-clamps to 1; quantities don't NaN
- [ ] Min=1: typing 0 + blur → re-clamps to 1
- [ ] Session-only: rescale, exit, come back → input shows original `servings`; saved recipe unchanged

---

## Meal plans

### Meal reconcile — page + dashboard chip + header nudge — origin FU-317 Chunk 5 (2026-07-09)
- [ ] **Settings → Admin → System → Meal reconciliation** (FU-317 Chunk 6): as a **non-admin** user, the page shows the "You don't have admin permissions" banner instead of the settings. (Admin half verified 2026-07-22: page renders with the *Assume past-day meals were cooked* toggle + *Go to reconcile* deep-link; flipping fires a success toast and persists across reload.)

### Budget-defense recipe swaps (Suggestions panel) — origin FU-451
*(Full flow — panel → candidate rows → Preview dialog → Apply/Undo → dashboard bullet — verified live 2026-07-23 (money on via FU-592; needs the desktop planner layout); residuals below are contrivance edge-cases.)*
- [ ] A meal already marked **cooked/consumed** never appears as a swap candidate.
- [ ] **Money features off** → no Suggestions panel, no dashboard bullet at all. *(inverse verified 2026-07-22 flags-off: no money surfaces)*
- [ ] Zero-state: contrive a week that's over budget but where no alternative is cheaper → panel shows "No swap saves you money this week" + an **Open shopping lists** link.
- [ ] Apply a swap, then (in another tab / after editing the week) apply the *same stale* card → server returns a 409 "out of date" and the toast surfaces it; refreshing re-fetches.

### Unlinked-ingredient warning after meal-plan → shopping list — origin FU-505
*(Server contract pinned 2026-07-19 in `test_auto_generate_unlinked.py`: the auto-generate `unlinked_skipped` payload lists ONLY genuinely-unlinked (free-text) ingredients tagged with their recipe, a fully-linked recipe yields none, and linked ingredients still become lines. **Fixed a real bug in the same unit — FU-587: the recipe + meal-plan sources added zero linked ingredients and mis-reported all as unlinked (R-032 noload).** The dialog render + navigation below stay owner-walk.)*
- [ ] Build a meal plan for the week where at least one planned recipe has an ingredient with **no linked stock item** (either a paste-imported recipe that never got linked, or one you added a "Use as free text" ingredient to per FU-506); trigger **Generate shopping list for this week** → success toast, then a dialog titled **Add these manually** listing each unlinked ingredient as `• <ingredient> (<recipe>)` with a single **Got it** button → tap **Got it** → dialog closes, navigation to the new list still happens
- [ ] Repeat with a meal plan whose recipes are **all fully linked** → success toast, no dialog; **and confirm the recipe's non-stocked ingredients actually landed on the new list** (the FU-587 fix — previously nothing from recipes was added)

### In-context Print on the meal planner — origin FU-338 (Board page portion retired with FU-304, 2026-07-07)
- [ ] Tap Print on mobile → a **new tab** actually opens (the popup itself). (Verified 2026-07-22: the button is wired to `openPrintView` → `/api/meal-plans/<id>/print-view`, and that endpoint renders the week's day×slot grid correctly; only the tab-opening half is unwalked.)

### useListState — full sweep across meal planner + shopping list detail — origin FU-354 + FU-355 (2026-07-07)
- [ ] **Silent 401 recovery clears both too**: with the same setup, force a session expiry (server restart, or hand-clear the session cookie in DevTools) → make any API call → the 401 interceptor's `handleSessionExpired` fires → SPA lands on the login page → after re-auth, both list-state values are empty

### Show-all-slots persistence — origin FU-306 (2026-07-07)
- [ ] The setting is per-device — flip on in browser A, open in browser B on the same account → browser B is off (this is a device-scoped preference, not a household one)

### Meal Planner R-Phase 1 extraction + Phases 2–6 — origin FU-305
- [ ] Left palette: **drag-and-drop** from a recipe row to a day-slot (mouse only); pool ± / log-cook dialog; "Cancel" clears focused-target banner. (Verified 2026-07-22: search filters trays; click-add into a focused slot lands in the chosen slot; the focused-target banner reads "Adding to <Slot>, <date> — pick a recipe.")
- [ ] Middle column: ↑/↓ arrows, top/bottom buttons, vertical-swipe on mobile move the focused week. (Verified 2026-07-22: calendar click moves it, and `?monday=` persists across a hard reload — F29.)
- [ ] Drop targets accept dragged recipes; "Other" row appears for off-vocabulary historical entries. (Verified 2026-07-22: per-day slot rows render entries.)
- [ ] Entry chip **view / cook** actions wire through. (Verified 2026-07-22: Today badge renders on the right day; past days carry `day-card--past` at opacity 0.6 with zero clickable slot rows; the chip popover's ± adjust and remove-at-zero work.)
- [ ] Right column: ingredient-row **hover-highlights**, AddToList button, cook-by warning, "Full ingredient demand" expansion, generate-list + C-7 target picker. (Verified 2026-07-22: calendar, this-week-shopping count and the ingredient list with per-row list status + stock chips all render.)
- [ ] Sequential builder: the **generate-list** hand-off from the done screen. (Verified 2026-07-22: the dialog opens, lists recipes, and builds — 4 picks spread one-per-day across the upcoming days.)

### Meal Plans C-2 — full surface walk — origin FU-179
- [ ] Carousel nav — ↑/↓ arrows + keys + mobile swipe move weeks with slide animation; `prefers-reduced-motion` disables; `weekRangeLabel` updates
- [ ] Tap-add — **re-adding to the same slot increments servings**. (Verified 2026-07-22: tapping a day's slot shows the target banner and the entry lands in **that** slot — chose Breakfast, got Breakfast, F35 holds.)
- [ ] Drag — desktop drag onto slot adds; touch disables drag, tap-add works (no scroll-jank)
- [ ] Inline servings — **view / cook** actions work. (Verified 2026-07-22: ± adjusts live ×1→×2→×1, and 0 removes the entry.)
- [ ] Thu-8am-AEST drop repro (F29) no longer 400s (ties to C-2.K). (Verified 2026-07-22: past days dimmed + non-interactive; Today badge on the right day.)
- [ ] Left list — "N free" + inline ± pool stepper + log-cook work; no cookable colour/check. (Verified 2026-07-22: search filters the list.)
- [ ] Off-vocab — entry with deleted/legacy slot renders under "Other"
- [ ] Sidebar/generate work bound to focused week. (Verified 2026-07-22: "Clear this week" confirms then empties it; the old "Jump to a plan" dropdown is gone, replaced by the calendar.)
- [ ] **C-2.D calendar** — the **amber "short"** underline state specifically; month **arrows** page the window. (Verified 2026-07-22: 6 weeks render; planned / consumed / empty day states; today carries the 5px primary dot; focused week outlined; clicking a week jumps the carousel and back; month banner reads the focused month; `?monday=` resumes across a hard reload; the old dropdown is gone.)
- [ ] **C-2.H sidebar** — the add-to-list button (multi-list opens picker); hover (desktop) outlines the using meals. (Verified 2026-07-22: each needed-ingredient row shows list status — e.g. "needs 15g · on This week" — with a stock chip, and membership loads on the planner.)
- [ ] **C-2.I trays** — curated trays hide when empty; 21-day "haven't had" window spot-check. (Verified 2026-07-22: the four tray groups render, searching collapses to "Results (N)", and "Frequently planned" ranks by plan frequency.)
*(C-2.F templates save + apply verified live 2026-07-23: the templates dialog (Save-this-week / Apply-recurring / Manage-sets / empty-state), Save → "Saved this week as a template." + server-created + listed "N meals · Apply", and Apply → "Added N meals." fork onto the focused empty week. Below = the confirm/edit-safety + sets/recurring survivors.)*
- [ ] **C-2.F templates** — confirm before replacing existing future meals; editing/deleting a template leaves a week forked from it untouched
- [ ] **C-2.G sets + recurring** — `/meal-plans/templates` = the rotating-sets manager (**page renders**: "Rotating template sets" + New set; individual templates rename/delete inline in the dialog, not this page); sets new/edit-with-↑↓-reorder/delete; "Apply recurring…" applies a template or rotating set over ≤26 weeks; set rotates week-by-week; 26-week cap + "pick exactly one source" toasts
- [ ] **C-2.J sequential builder** — **Cancel writes nothing**; the generate-list modal fires from the done screen; Print opens the week's print view. (Verified 2026-07-22: the 3-step flow runs pick → "What you'll need" → Build; the preview's buy/in-stock matches the sidebar; 4 picks built one-per-day across upcoming days, skipping past days; the done screen offers Generate shopping list / Print this week / Done. **Note:** there is no Email button at all — the checklist expected one "shown disabled". **Every built meal lands in Breakfast — see FU-596.**)

---

## Shopping lists

### Substitute-swap gating on a line — origin FU-407 (RD-18)
- [ ] A shopping-list line whose stock item **has** a recorded substitute → the swap (⇄) icon is enabled; tooltip "Swap for a substitute item"; tapping opens the substitute chooser.
- [ ] A line whose item has **no** substitute → the swap icon is **disabled**; tooltip "No substitutes recorded for this item" (no dead-end tap→toast).
- [ ] The swap affordance reads as distinct from the "store offers" picker on the same line (no "two Substitute labels" confusion).
- [ ] Product-only line (no stock item) → swap disabled.

### Quick-add toast + "always ask" pref — origin FU-316
*(Resolver + toast/picker/always-ask/session wiring verified 2026-07-24; only the on-screen picker/toast eyeball remains.)*
- [ ] With 2+ drafts, quick-add from a stock row → "Which list?" picker → pick → toast names the list → 2nd quick-add same tab skips the picker; with "Always ask" on, every add re-prompts

### Receipt-photo attachments — origin FU-334 + R-024 follow-on
*(Section-gating/empty-state/desktop "Choose receipt" verified 2026-07-24; CRUD+cascade backend-pinned. Below = device file/camera.)*
- [ ] Mobile: *Take photo* → rear camera; capture → thumb in the strip
- [ ] Mobile: *Choose receipt* → OS picker → pick a photo → thumb appears
- [ ] Desktop: *Choose receipt* → file picker → pick an image → thumb appears
- [ ] >12MB image → inline error + toast "Could not read that image…", nothing added
- [ ] Non-image (PDF) → same error path
- [ ] Tap thumbnail → lightbox ≤80vh; backdrop + Esc close it
- [ ] Trash a thumb → optimistic remove; reload → still gone
- [ ] 3+ receipts render left-to-right in upload order; reload → same order

### Image-source picker — sanity sweep across surfaces — origin R-024
*(All surfaces on the shared `ImageSourcePicker`→`processImageFile`; avatar verified live 2026-07-24 (desktop "Add (file)", camera hidden). Stock-item image-edit surface is gone → [[FU-607]]. Below = device file/camera.)*
- [ ] Each surface (recipe hero, step images, avatar, store logo): pick a real file → resize applied + preview updates; on mobile the camera button captures one photo; step-images accepts multiple

### Trim-to-budget banner + Deferred section — origin FU-448
*(Banner copy + "everything safe" fallback + Dismiss + buy-on-out never-cut verified live 2026-07-24; math pinned in `test_trim_to_budget.py`. Happy path needs a genuinely cuttable line the seed API can't create → owner-walk.)*
- [ ] `money_features_enabled=false` → banner never appears
- [ ] money on, `budget_amount` null → banner never appears
- [ ] **Show what would be cut** → preview card, per-line reason chip + `Keep`
- [ ] `Keep` re-fires preview excluding that line; totals update; no mutation until Apply
- [ ] **Trim to fit** → `deferred_by_budget` on cuts → "Deferred to fit budget (N)" section + "Trimmed $X to fit — see deferred (N)" strip
- [ ] Strip link scrolls to the Deferred section
- [ ] Deferred line: reason chip + price + **Add back** → returns to active list; if back over budget, banner reappears on reload
- [ ] Tier ordering: highest-price cut first inside a tier
- [ ] Never-cut: essentials, meal-in-2-days, sub-$2 all survive (buy-on-low/out verified live)
- [ ] Assistant "trim my shopping list to my budget" → summary + Confirm applies; no-budget / already-under → the two decline replies

### Shopping list UX v2 — origin FU-165
*(`display_name` self-labelling backend-pinned. Rail+next-up marker, doughnut+totals, group-by (Location regroups), bulk-select, and Print all verified live 2026-07-24. Residuals below.)*
- [ ] Mobile dropdown opens + picks (viewport)
- [ ] Shop-day button tones (today/overdue) correct
- [ ] Start shopping → sticky footer → finish-review modal (ticked summary, no per-item level picker — FU-582) → Reopen reverses it
- [ ] Quick-add mid-shop works
- [ ] Row actions: price button, swap, remove
- [ ] Drag-reorder lands on the exact row you drop on (FU-161 fix stays fixed)
- [ ] Dashboard card + Dora-chat add-to-list still work

### Cart Button Chunk 2 — combined modal for 2+ products — origin FU-130
- [ ] Bulk variant — resolves target once + one summary toast regardless of per-item counts

### Cart Button Chunk 3 — standalone product lines + rules 1–3 — origin FU-132
*(Rules 1–3 pinned 2026-07-20 in `tests/e2e/dora_api/test_shopping_list_product_lines.py`: **Rule 1** a `product_id`-only POST creates a line (product_id + null stock_item_id); a no-anchor body → **422** business-rule violation "A line needs at least one of stock_item_id or product_id" [the checklist guessed 400 — 422 is correct for a domain rule; the DB CHECK is the backstop]. **Rule 2** linking the product to a stock item converts the orphan in place (gains stock_item_id, keeps product_id) OR folds into an existing stock-item line + drops the orphan. **Rule 3** deleting the stock-item line (by line-id) cascade-removes the nested product line. The migration, the by-stock-item remove variant, and the TS-compile check below stay owner-walk.)*
- [ ] Migration `d7c9e4a8c2b1` applies on SQLite + Postgres; `verify_mappings()` passes for the now-nullable `stock_item_id` + new `product_id` FK
- [ ] Rule 3 variant: **cart-button remove-by-stock-item** (`DELETE …/lines/by-stock-item/<S>`) also removes the nested product line (the by-line-id path is pinned above)
- [ ] No regressions on stock-item-only adds — existing dedupe by `stock_item_id` still wins
- [ ] TS compile: `ShoppingListLine.stock_item_id: string | null` doesn't break consumers

### Cart Button Chunk 3 UI — origin FU-145
- [ ] Link the product to a stock item later → parent stock-item line appears (rule 2 backend) AND product nests visually under it (rule 2 frontend)
- [ ] Remove nested product → rule-4 modal fires; "Yes" removes both, "No" leaves the parent
- [ ] Remove product-only line whose linked stock item is NOT on the list → no modal
- [ ] Linked products on My Products row still hit `onAddSingle` (stock-item path); ticking nested children works; bulk mode handles parents + children

### Cart Button Chunk 4 — meal-plan generate via Axis B — origin FU-135
- [ ] **0 draft lists**: no picker; creates new list named `Meals: <plan>`; toast; routes *(1-draft preselect + 2+ picker/cancel/create-new/merge verified 2026-07-23)*
- [ ] **1 draft list**: picker preselects that draft + "+ Create new list"; OK on draft → merges + routes
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

### Add-a-stock-item dialog — stock group + Essential + name trim (Codex review, 2026-07-17; expiry→group swap 2026-07-22)
*(Backend fully unit-tested — 6 green incl. over-long/whitespace/trim-dedup; these are the visual/UX confirmations. Dialog opens from Stock Overview "Add".)*
- [ ] The Add dialog shows, under Location: a **Stock group (optional)** picker listing the configured groups (clearable), and an **Essential** toggle with an info tooltip. There is **no Expiry field** — expiry is per-batch and lives on the detail page only
- [ ] Add an item with a group picked + Essential on → open the new item's detail page: the stock group and the Essential toggle both reflect what you chose
- [ ] Add a group in Settings → Stock groups, then reopen the Add dialog → the new group appears in the picker (options refetch on each open)
- [ ] Help → Stock → "Add a stock item" reads "click **New item** … a location, stock group, or the Essential flag. Expiry is set on the item itself once it's added." — button name and field list both match the real dialog
- [ ] Type a name with leading/trailing spaces (e.g. "  Milk  ") → it's stored trimmed ("Milk"); a name that's only spaces is rejected by the form ("Name is required")
- [ ] Adding "  Milk  " when a "Milk" already exists shows the "already exists" error (trim + case-insensitive dedup), not a second row

### Action-first scan mode on Stock Overview — origin FU-378
*(Needs the install-wide `scanning_enabled` flag ON — Settings → Admin, or `DORA_*`/AppSetting — and a device with a camera. Manual-entry box in the overlay works as a camera stand-in.)*
- [ ] With scanning ON, on Stock Overview the **Scan** button opens the camera overlay directly (single button, no menu on the toolbar)
- [ ] Inside the overlay there's a visible **"Action: Open stock item"** chip (with an open-in-new icon) above the manual-entry box, and a caption "Each scan opens that item — the scanner then closes." — i.e. the current action is always shown
- [ ] With the default "Open stock item" action, scan a known item's code (or type it in the manual box) → jumps to that item's detail page and the overlay closes (legacy default behaviour)
- [ ] Reopen Scan → tap the **Action** chip → a menu ("Scan does…") lists **Open stock item** + **Set to <level>** for each configured stock level (each with its colour dot; renamed levels show their custom name); the currently-selected action shows a check mark
- [ ] Pick **Set to <a level>** → the chip updates to "Action: Set to <level>" with the level's colour dot, the caption changes to "Keep scanning — each item is set to this level.", and the overlay **stays open**
- [ ] Scan (or manually enter) a known item's barcode/QR → a green "<item> → <level>" banner + chime shows, and the item's level actually changes (verify on the row after closing) — overlay stays open for the next scan
- [ ] Scan several different items in a row → each is set to the chosen level; the loop never closes on its own
- [ ] **Switch the action mid-session** (tap the chip, pick a different level, or back to "Open stock item") → the next scan uses the newly-selected action; you never have to leave the camera to change it
- [ ] Scan an unknown barcode (or a product with no linked stock item) while a level action is selected → a red banner explains it was skipped ("no pantry item linked" / "add it to your pantry first") and the overlay stays open — it does NOT open the add-item dialog
- [ ] Close the overlay (X) and reopen → the action resets to the "Open stock item" default, and no stale banner from the previous session lingers
- [ ] With scanning OFF (default) → the Scan button does not appear at all

### Register barcode against a Product from My Products — origin FU-373
- [ ] With **scanning ON** (Settings → scanning enabled): open the My Products `⋮` menu on any product → "Register barcode…" is present. Enter a barcode, Register → success toast; the dialog closes.
- [ ] Re-open the menu on the same product and register the **same barcode again** → inline error shows the "already registered" conflict (409), no crash.
- [ ] With **scanning OFF**: the "Register barcode…" `⋮` item is hidden entirely (R-029 hide-don't-nag), leaving the other menu actions intact.

### StockItem.image feature dropped — origin FU-508
- [ ] Recipes still render their images; user avatars still render; store logos still render (these are separate features and must be untouched)

### Stocktake redesign — Chunk 3 Settings + Stock Overview surfacing — origin PROPOSAL_STOCKTAKE_MODE
*Verifies the Settings block + Overview filter chip + row pulse outline. Chunk 3 lands the surfaces users find the redesign from.*

**Settings → Stocktake page**
- [ ] Navigate to **Settings → Admin → System → Stocktake** — the nav entry appears with the clipboard-check icon, between "Alert thresholds" and "AI assistant"
- [ ] Non-admin user visits the page → the red admin-permissions banner shows, the sections don't render
- [ ] With Auto **off**, run stocktake — every item's cadence is the global default (adjusted by Essential = one band faster if flagged)
- [ ] With Auto **on**, an item with recent frequent level changes moves into a shorter cadence band on next queue rebuild (verify by looking at what the runner shows as "Checked every week/fortnight/month")

**Stock Overview — "Needs check" quick-filter**
- [ ] On **Stock Overview**, expand the filter panel → a new **"Needs check"** chip appears in the chip strip, positioned after "Needs attention", with the clipboard-check icon

**Stock Overview — pulse outline around stock-level button**
- [ ] An item that IS in the stocktake queue: its **stock-level button** (the small coloured square left of the item name) has a **subtle pulsing outline** — a soft accent-coloured halo that grows and fades on a 2-second cycle
- [ ] An item NOT in the stocktake queue: no pulse, no outline
- [ ] After tapping **Still correct** in the runner for an item, return to Stock Overview and refresh — its pulse is gone (item left the queue)
- [ ] With `prefers-reduced-motion` on (browser accessibility setting): items still show the outline, but as a **static** ring (no animation) — verify by enabling reduced-motion in devtools and confirming no pulsing
- [ ] Dark mode: the pulse colour still reads well against the darker surface (uses `--brand-accent` theme token)
- [ ] Light mode: same — the halo is visible without being loud

### Stocktake redesign — Chunk 2 SPA runner rebuild — origin PROPOSAL_STOCKTAKE_MODE
*Verifies the redesigned stocktake mode: new engagement gate + cadence bands + buttons + completion screen. Chunk 3 (Settings + Stock Overview surfacing) is not yet built.*

**Runner card + buttons**
- [ ] Item card shows: name (large), location (or "No location"), and a caption line like **"Checked every fortnight · N days overdue"** — plural/singular correct for 1 day vs many
- [ ] The **Change level** button is **tinted to the current level's colour** (Stocked → positive/green, Low → negative/red, Out → neutral/muted) and shows the level's **name** with a small **"(change)"** underneath
- [ ] **Row 2 — three smaller ghost buttons:** **Skip** / **Push 3 days** / **Mute**
- [ ] No **keyboard shortcuts** shown on the buttons; pressing `1`/`2`/`3`/`s` does **nothing**
- [ ] No **Add to list** button on the card (it moved to the completion screen)

### Bulk "Log waste…" on Stock Overview — origin FU-226 chat
*Verifies the new bulk waste action in the Stock Overview bulk-select bar.*
- [ ] Enter bulk-select mode (long-press a row on mobile, or the toolbar toggle on desktop) → select 3 items, at least one with an expiry date set and at least one without → the "Log waste…" button in the bulk bar is enabled and shows the trash icon
- [ ] After bulk-logging those 3 items as wasted (Spoiled): open **Reports → waste-insights** (or the Dashboard "recently wasted" surface) — the 3 items appear with reason `spoiled` and the same `occurred_at`; the item that had an expiry date now shows expiry cleared on Stock Overview

### Auto-add-on-low toast + line chip — origin FU-315 (re-verify: FU-464 fixed a Low-transition regression 2026-07-04; FU-511 collapsed the per-item toggle to an install-wide 3-state setting 2026-07-07)
*Auto-add is now controlled by **Settings → Admin → System → Stock** — three modes:*
*`Off` never fires. `Essential only` (default) fires only for items with the Essential flag on. `All items` fires on any Stocked → Low/Out transition. Server owns the branching in `update_stock_item._try_auto_add`.*

*For the toast-behaviour checks below, set the install to `Essential only` (default) and use a stock item with the Essential flag on and exactly one open draft shopping list.*
- [ ] Trigger an auto-add (drop a qualifying Stocked item to Low from the overview) → then open the draft list: the new line renders **without a manual refresh** (the store refreshed itself)
- [ ] Item level change on the detail page (Level row) → the auto-add toast fires the same way (`updateStockItemAsync` path)
- [ ] Cook mode's per-ingredient level decrement that flips an ingredient to Low → toast fires per triggered item (multiple toasts stack — verify readability)
- [ ] Offline stock-level flip → queued (blue "Queued: Update stock level" toast); when back online + queue drains → auto-add toast fires *if* the flipped item genuinely transitions on the server side and the mode allows it

### ⭐ Zero-Input Pantry — inferred inventory (P8-07) — origin champion plan
*(Server side largely test-pinned: the belief engine — bands, cook drift, override-wins, thin-history caution, differs flag — in `test_pantry_belief.py`; the endpoint shape, per-user opt-out gate `{enabled:false, beliefs:{}}`, toggle persistence via PATCH `/auth/me`, and the fresh-level-change→HIGH-confidence pin end-to-end in `test_pantry_beliefs_endpoint.py`, 2026-07-18. The checks below are the remaining UI/loop halves.)*
- [ ] Preferences → Pantry: "Infer stock levels" toggle is present in the UI; flipping it hides/shows the chips live (the server gate + persistence are backend-pinned)
- [ ] With inference ON, stock overview rows show a "Dora: ~Band · confidence" chip beside items that have purchase history; tooltip shows the reason (e.g. "~Low — bought 11 days ago; you usually finish in about 14 days")
- [ ] Buy an item (finish a shop with it ticked + priced), reload → its belief reads Stocked with a recent-purchase reason
- [ ] Cook a recipe using that item (finish dialog → mark it "down one"/"out") → a ConsumptionEvent is written; the item's belief drifts more depleted than purchase cadence alone would, and the reason mentions "cooked with N× since"
- [ ] Let an item go well past its usual cadence with no check so the belief drifts while the recorded level still says Stocked → the chip shows the warning outline ("differs from recorded" — the drift itself is engine-pinned; this checks the outline render)
- [ ] Add an uncertain item to a draft shopping list → a single "Still have X?" quick-check appears in the suggestions inbox (not a bulk prompt); its action opens the item; dismiss/snooze work; capped at 3 across all in-play items
- [ ] Plan a meal this week whose ingredient is uncertain → same quick-check fires via the cook-decision path
- [ ] Dark-mode + non-money themes: chip colours ride semantic tokens (positive/warning/negative dots), no hardcoded colour
- [ ] Backup → restore: ConsumptionEvent is an event log (like CookEvent) and intentionally NOT in the backup sections — confirm restore still succeeds and beliefs recompute from surviving purchases/cooks

### 3-band StockLevel collapse (Sufficient axed, 2026-07-02)
- [ ] No stock-level picker anywhere still offers a "Sufficient" middle option — only Stocked / Low / Out. (The shopping-list finish modal is out of scope: its per-item picker was cut, FU-582.)
- [ ] Onboarding "Restock" scene copy reads "Finishing the shop bumps what you bought back to stocked — no re-counting" (was "well-stocked")
- [ ] Buy-verdict popover on a Stocked item: reads "Stocked" as the need-axis label (was "Well stocked")

### P8-05 "Should I buy?" buy-verdict oracle
*(Test-pinned 2026-07-18: the verdict engine — full matrix, thin-data collapse, reason
labels/details, wait-hint — in `tests/test_buy_verdict.py`; the UI seams — feature-flag
off/on across a reload, low-confidence rows stay silent, out-of-stock Buy walk with the
"You're out of stock" lead + one-tap add landing on the draft, Skip walk with both
one-tap variants and the FU-572 in-place repaint — in `web_app/e2e/buy-verdict.spec.ts`;
the client request cache (one fetch per item, 5-min stale window, invalidation refetch)
in `web_app/test/unit/useBuyVerdict.spec.ts`. Only the visual below remains.)*
- [ ] One-time visual: the orange **Wait** badge + its popover ("Above your usual price"
  with the `$last vs $usual` detail, and the wait-hint sub-caption when a cycle is
  confident) render legibly across themes — the content is engine-pinned; this is only
  the orange variant's look (the Buy/Skip variants have been walked)

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

### History tab — origin 2026-06-30 feedback
*(Test-pinned 2026-07-18. Server halves: expiry-event emission (set/pushed/cleared +
no-op silence) and the per-kind cap → `history_older_count` in
`tests/e2e/dora_api/test_stock_item_router.py`; the Bought feed (ticked+finished only,
price/store optional, mid-shop tick not yet bought) and the Cooked feed
(RecipeIngredient join only, `meals_cooked` badge data, zero-meal cook silent) in new
`tests/e2e/dora_api/test_stock_item_history_feeds.py`; migration reversibility owned by
`tests/test_migrations.py` (SQLite downgrade xfail is a known carve-out; Postgres leg
rides batch 19). UI halves in new `web_app/e2e/history-tab.spec.ts`: the Sriracha
chatty-seed cap walk ("16 older events not shown", server-stable across reload),
under-cap busy item interleaves Bought/Wasted/Pushed with no footer, "Used in <recipe>
· N meals" batch badge, and the full Set/Pushed +7 days/Cleared title+body family on an
engineered item. Only the visuals below remain.)*
- [ ] One-time visual: event-kind colours ride their theme tokens (Bought
  `--lifecycle-bought`, cook `severity-high` deep-orange, waste negative-red, cleared
  muted `--lifecycle-cleared`) and stay legible across themes; and the footer's
  singular branch ("1 older event not shown") reads right if you ever see it — both
  are template one-liners whose plural/colour siblings are test-pinned

### Stock pickers + Log Waste — overview/dialog/detail consistency — origin 2026-06-30 feedback
*(Behavioural halves test-pinned 2026-07-18: the row expiry-menu **Log waste** path
(menu entry → reason dialog → event + toast + Undo) in `bulk-waste.spec.ts`; the
detail-page Level picker round-trip (dropdown pick → "Updated just now" stamp →
server truth) and the level filter's set→clear cycle staying console-clean with the
fallback trigger in new `stock-pickers.spec.ts`. Only the styling below remains.)*
- [ ] One-time visual: the three level pickers (overview filter, Add-item dialog,
  detail Level row) render the same `StockLevelDot` treatment in trigger + option
  rows (muted sunken dot when cleared), and the row expiry-menu's **Log waste**
  entry reads destructive-red (icon + label) matching Clear expiry

### Stock Item Detail — C-1b focused pass + C-1b.1 marquee — origin FU-202
*(Triaged 2026-07-18. Already test-pinned and deleted: the Level row round-trip +
"Updated just now" (`stock-pickers.spec.ts`); the lifecycle timeline's event kinds,
cap, and footer (`history-tab.spec.ts` + backend feed tests); location/group/notes
clear semantics and round-trips (server-pinned in `test_patch_semantics.py` +
`test_stock_item_router.py` — explicit null clears, level null is ignored); the
expiry editor dialog (`stock.spec.ts` FU-507); the unsaved-changes composable
(`useUnsavedChangesGuard.spec.ts`). Deleted as stale: the C-1b.1 "level chip in
header" bullet (superseded — the level lives in the Overview Level row, which is what
the tests pin) and every "auto-add toggle / footer Auto-add count" mention (retired by
FU-511; their absence is itself pinned by `auto-add-on-low.spec.ts`). What remains is
the owner walk below.)*
- [ ] **Layout/visual walk (one pass, light + dark):** header back/close · name ·
  (Show QR when scanning on) · danger-ghost Delete, no secondary toolbar row;
  toolbar = Mark open · Set expiry · Add-to-list (no Restock / Find-deals); "—"
  placeholders on unset Location/Stock group/Usual store/Expiry; single-column
  editors with even padding in full-page AND peek mode; Notes auto-grows; DoraTabs
  underline slide/wobble + hover accent (also `BarcodesQR.vue` / `HelpPage.vue`);
  tabs legible in every theme; QR tooltip explains QR vs real-barcode; footer counts
  Stocked-positive / Low-negative / Out-muted with the "Essential" label; row button
  cluster (expiry / flag / open / cart) same round shape
- [ ] **Splitter peek:** opens at 50%, clamps to [40%, 65%], closing restores 100%;
  gripper dots stay viewport-centred on long lists; the whole panel scrolls with the
  page (name + Delete never hidden)
- [ ] **Location/group picker × in the browser:** clearing via the picker's × (and
  Tab-blur) leaves it empty after a refresh — the server null-clear is pinned; this
  is just the q-select→PATCH wiring
*(C-1b.4 Recipes/Lists/Substitutes behaviours codified 2026-07-18 in new
`web_app/e2e/detail-recipes-tab.spec.ts` — heart toggles favourite both ways,
cookable "Add all to list" lands every ingredient on the draft, Lists tab reflects
membership with no dead `open_in_new`, Substitutes row has no "Swap into list" and
Remove unlinks. The old "styled Primary badge" wording was stale — Round-17 replaced
the pill with a warning-toned star; that's part of the visual walk above.)*
*(C-1b.3 Products tab codified 2026-07-18 in new
`web_app/e2e/detail-products-tab.spec.ts` — linked products render with exactly one
Cheapest chip/highlight + the quiet "Link another" header + no retired "Get
cheapest" button; the empty state shows the centred "Find & link a product" CTA.
**The CTA's destination is NOT pinned: it routes to the FU-186-retired
`/product-search` and 404s — real bug, logged as FU-581 (also hits My Products +
the Dashboard "Hunt for deals" CTA).** The old `?q=` seeding expectation is dead
with the route.)*
- [ ] **C-1b.3 products-OFF half (needs a productless install):** with zero Product
  rows the Products tab disappears entirely and a stranded `?section=products` URL
  falls back to Overview — not drivable against the seeded e2e DB
- [ ] **History extras not yet pinned:** level changes label as "Restocked → X" /
  "Dropped to X", the synthetic "Opened" entry renders while an item is open, and an
  empty item shows "Nothing logged for this item yet…"

### Stock Item Detail + Stock Overview feedback pass — origin FU-222
- [ ] Stock Overview row — image / level / name have visible breathing room; right cluster (expiry, open, cart) larger; recipe-count chip gone; hover no longer "lifts" — surface tints + border picks up accent; first row's outline doesn't clip under page chrome
- [ ] Essential indicator: flag → 3px warning stripe on left edge + flag icon in right cluster
- [ ] Open icon pops in Pesto dark (primary, not barely-visible secondary)
- [ ] Footer counts: "Shown" reads in default text colour (not primary); per-level counts use stock-level palette; Flagged / Auto-add / Needs attention keep semantic tones
- [ ] Filter toggle on Stock Overview, My Products, Cookbook overview: "Filters" button + badge + "Clear" all in main toolbar row; no second toolbar row above the filter panel

### Stock Overview Chunk 2 — top toolbar + filters + footer — origin FU-121
*(Behavioural halves test-pinned 2026-07-18 in `stock.spec.ts` (new Chunk-2 describe:
desktop panel-persistence reload round-trip both directions; retired "Used in a
recipe" filter absent with a surviving control; bare "Search" placeholder) +
`stock-pickers.spec.ts` (single clearable "Any level" dropdown narrows/restores,
console-clean incl. the dropped-reference errors bullet) + `useStockFilters.spec.ts`
(footer counts reflect the filtered set). The old footer-order bullet listed
"Flagged / Auto-add" — stale: Auto-add's absence is pinned by
`auto-add-on-low.spec.ts` and the label is now "Essential".)*
- [ ] Visual walk: toolbar order New item · (Scan) · Stocktake · Bulk select ·
  Export · spacer · Search, with Bulk select flipping to "Cancel"; Clear sits LEFT
  of Filters and appears/disappears without the Filters button shifting; footer
  count order Shown · Needs attention · Stocked · Low · Out · Essential · On a list
- [ ] Mobile (< md): filterable pages start with the panel hidden regardless of the
  desktop-saved state; in-session open works, reload returns to hidden

### Stock Overview Chunk 4 — expiry control — origin FU-123
*(Partially test-pinned 2026-07-18: the **+X push semantics** — `max(today, current
expiry) + N`, future pushes from the expiry, past pushes land tomorrow, no-expiry
falls back to today+N, unparseable degrades safely, toast + failure path — in new
`test/unit/useStockItemActionsPushExpiry.spec.ts` (8 tests). The
menu-vs-date-picker split (expiry set → menu; unset → picker) and the Clear-null
round-trip are exercised by `bulk-waste.spec.ts` test 6 + the FU-507 dialog specs.)*
- [ ] No expiry set → date picker (popup desktop / dialog mobile); picking a future
  date PATCHes and the row reflects it; past dates blocked by `dateOptionsFuture`
- [ ] Expiry-set menu shows exactly **+1 day · +7 days · +14 days · Clear** (no +30);
  tone outline flips amber `<7d` / red past; right-cluster unaffected
- [ ] Detail-panel peek staleness: with a peek open, drive the row's expiry menu /
  open-toggle / flag-toggle / level dropdown → the peek's matching field updates
  without closing/reopening (same full-screen on mobile via a different surface)

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
*(Test-pinned 2026-07-18. UI seams in new `web_app/e2e/dashboard-draft-shop.spec.ts`:
card renders in the act zone with blurb + button; one-click happy path → "Drafted N
items." toast + caption → navigates to the new draft named "Weekly shop · <date>"
(sidebar included — the store refresh precedes the push) with `auto:` provenance
chips rendering; Cards-menu q-toggle hides and restores the card. Server halves in
new `tests/e2e/dora_api/test_auto_generate_draft_shop.py`: zero candidates on the
create-new path → `nothing_to_add` + null id + **no phantom list**, and the explicit
"Weekly shop ·" name honoured; provenance priority already pinned in
`test_auto_generate_priority.py`, the single-commit contract in
`test_auto_generate_unit_of_work.py`. The NewListDialog merge path is untouched by
the defer change (it always passes `merge_into_list_id` — code-visible at
`auto_generate.py` §handle).)*
- [ ] Empty-case UI half (needs a fresh install — seed always has candidates): click
  → info toast "Nothing to draft yet." + caption, stays on the dashboard (the
  server's no-phantom-list half is backend-pinned)
- [ ] Error case — force a 500 mid-click: negative "Could not draft the shop." toast
  with caption; button un-spins and re-enables
- [ ] Consumed-entry window sanity: a meal-plan entry marked consumed (cook
  reconcile) does not reappear on a re-draft — the `consumed_at IS NULL` guard at
  `auto_generate.py:418` is code-visible but untestable via the API (consumed_at is
  only written by the reconcile job)

### ⭐ P8-08 Dora Score — Kitchen health card — origin champion-plan §P8-08
*(Behavioural halves test-pinned 2026-07-19: engine in `test_dora_score.py`; endpoint shape/401/log-line in `test_dashboard_router.py` + route-auth sweep; card render vs server truth, ordered rows, dormant-Budget contract, action links incl. the deliberate no-Waste-link, and the Cards-menu toggle in `web_app/e2e/dora-score.spec.ts`. The `?expiring=1`/`?stocktake=1` params being ignored by StockOverview is FU-583. Remaining below = visuals/gated.)*
- [ ] Trend chip render: green up-arrow with `+N` when direction is `up`, red down-arrow with `-N` when `down`, and **no chip** when `flat`/unavailable (needs score history in both directions — eyeball when the trend is live)
- [ ] Mini-bar traffic-light thresholds read right in both themes: green ≥80, amber 50–79, red <50
- [ ] Brand-new install (no data anywhere): card shows the calm "appears once you've been using Dora for a bit" empty state, not a 0 score (fresh-install gated)
- [ ] Trend arrow reflects `score - (score computed on the 30d window ending 7 days ago)` — logging a waste event shifts the composite down over the next week, and the arrow should flip from up/flat to down (background refresh happens 5 min after mutation; a full reload picks it up sooner)
- [ ] Drag-reorder within the kitchen zone still works with the Kitchen health card present

### Dashboard price-drops widget — origin FU-296
*(Test-pinned 2026-07-19. Server halves in `test_reports_router.py`: new-low
honesty + no-history exclusion were already pinned; added ranking (% desc,
amount tie-break), the `is_active=false` exclusion, and the limit clamp
(1/−3→1, 999→≤20, missing/`abc`→5) — which flushed out a real bug, fixed
inline: PATCH price-update inserted the archived historic offer without an
id, so the second-ever price change 500'd (see CHANGELOG). The null-current-
offer exclusion has no API path to engineer and stays code-visible
(`current_offer is not None` in `PriceDropsHandler`). UI halves in new
`web_app/e2e/dashboard-price-drops.spec.ts`: hidden by default → Cards-menu
enable → honest empty state on seed (every seeded product sits AT its low),
an engineered 20% drop rendering name · store · linked-item deep-link ·
$8.00/"was $10.00" · "20% off" badge + the "My products →" action, deactivate
→ empty state returns, toggle restored. Specs warm-navigate around the
FU-586 flags race.)*
- [ ] Products feature OFF: card absent from both the dashboard and the Cards menu (needs a productless install)
- [ ] Product images: `has_image=true` rows fetch `/api/products/{id}/image` (needs a product with an image; the placeholder half renders in the e2e run)
- [ ] Dark-mode: row colours/badge ride semantic tokens (no hardcoded red/green)

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
*(Test-pinned 2026-07-19 in `web_app/e2e/dashboard-next-cook.spec.ts` on a
throwaway recipes+plan universe: rows mirror the summary DTO's dedupe/order,
"Today breakfast · serves N" meta, Ready / Missing 1 / No ingredients badges
against engineered stock truth, recipe-name → `/cookbook/{id}` and Cook →
`/cookbook/{id}/cook`. The FU-299 donut section was fully codified the same
day in `dashboard-donut.spec.ts` — incl. a real pointer click on the SVG low
arc — and deleted.)*
- [ ] Empty state when nothing is planned for the next week → "Nothing planned for the next week" + "Plan a meal →" link to `/meal-plans` (needs a plan-free install — the seed always has a current-week plan)

### Dashboard Cards menu drag-and-drop reorder — origin FU-294
*(Test-pinned 2026-07-19 in `web_app/e2e/dashboard-cards-reorder.spec.ts`,
which also closed out the FU-292 `dashboard_layout` section — migration
applied on every suite boot, `test__dashboard_layout__set_and_clear` green
in the backend suite, and the browser-walk halves now automated: tap up/down
reorders within the zone with first/last arrows disabled and both directions
working; native HTML5 drag-handle drop reorders with drop-on semantics;
cross-zone drop rejected with the server layout untouched; every reorder
asserted against menu render + the `/auth/me` `dashboard_layout` JSON +
reload persistence + a second browser context ["another device"]; iPhone-UA
run pins handle hidden with arrows + toggle remaining. The arrows are
unlabelled icon-buttons — FU-578's a11y bucket.)*
- [ ] Mid-drag visuals: the grabbed row dims and the valid drop-target row shows the primary ring; a cross-zone target shows no ring (transient states — eyeball on a real drag)

---

## Alerts & notifications

### Alerts C-9.1 — spine — remaining browser smoke — origin FU-183
- [ ] **C-9.2:** the admin **Expiring-soon window** field's own save path (type a value + Save in the UI). (Verified 2026-07-22: the setting round-trips server-side 7→2→7 and reshapes the feed — expiring_soon 13→2, badge follows; **disabling a kind** removes its 11 rows from the list; **demote/promote** moved `expired` between tiers with exact accounting — actionable 34↔23, FYI 18↔29, badge tracking. UI-typing half is blocked by the Quasar synthetic-input limitation, not by a defect.)
- [ ] **C-9.3:** dark-mode sweep of the hub. (Verified 2026-07-22: hub renders — summary tiles, tiered active list, Manage panel, collapsible History; bell is a slim peek with top rows + bulk-add + "Open Alerts"; shared `AlertRow` actions work from both; History lists dismiss/snooze/read with stock name resolved — **found + fixed a copy bug there: `out_of_stock` rendered "out of_stock"**. **Bell/page DO diverge — see [[FU-597]]:** the page only refetches when the store is empty, so it can show a stale feed all session.)
- [ ] **C-9.5 price watch — residuals:** the **last-alerted** timestamp on a watch that has actually *fired* (armed one never fired); and driving the **arm** UI itself (per-product "Notify me below" q-input didn't render/take in the hidden pane — armed via the API the button calls). *(Verified live 2026-07-23: empty-state; armed→panel lists product·merchant·"notify below $2.50"; View→explorer deep-linked to the product; Remove→gone+"Price watch removed."; hidden when the INSTALL money flag is off. Per-user-vs-install gating → [[FU-604]].)*
- [ ] **C-9.6:** empty-state; "refresh works". (Verified 2026-07-22: mini-calendar renders; per-category dots for expiry/shopping/meal; out-of-window at opacity 0.35; today ringed in primary; clicking a day selects it and expands the detail list; all three link targets navigate — expiry → `/stock/:id`, shopping → `/shopping-lists/:id`, meal → `/cookbook/:recipe_id`. **Dots survive theme switch but shopping and meal are the SAME colour in Pesto — [[FU-598]]**.)

### Cross-app undo after push-expiry (fixes 2026-07-10) — origin FU-357
- [ ] From the **Dashboard's dashboard-card push-expiry action** (i.e. the push-expiry rendered on the Dashboard alerts card, not just the bell) → toast now reads **"Done."** (this used to be silent — fixed 2026-07-10). Confirm the toast fires on Dashboard, Bell peek, and `/alerts` page — all three surfaces should behave identically.
- [ ] Push expiry via bell/dashboard/`/alerts`, then navigate to the stock item detail page → **Clear** its expiry → no stale toast reappears, the expiry field reads empty, and no undo affordance fires against the cleared field. (Static read confirmed: no undo exists on the push_expiry path anywhere in the SPA. This step is the last belt-and-braces check.)

### good_deal alerts + fake-markdown buy verdict — origin FU-450
*(**FINDING [[FU-602]] (2026-07-23):** the `good_deal` alert + the "Good & great/Great only" deal-band control (first two bullets) appear **absent** — likely a deliberate descope (the deal-quality band feeds buy-verdict only), unconfirmed. The buy-verdict half IS live. Confirm intent via FU-602.)*
- [ ] **Money features on.** For a product linked to a tracked stock item, add a *fresh* offer that's the lowest it's been (great band) → an alert appears in AlertsPage: "«item» — «brand product» is at its lowest price in months · $X · usually $Y", green tag icon, FYI tier (doesn't inflate the bell badge). Tapping it opens the stock item (where add-to-list lives).
- [ ] **Threshold.** Settings → Notifications → **Deal alerts** shows a "Good & great" / "Great only" segmented control (only when money features are on). Set "Great only" → a merely-`good`-band product stops alerting; a `great` one still does.
- [ ] **fake markdown.** For a product where the merchant claims a "special" (was > now) but you've logged paying *less* recently (price observations below the special) → the item's **Buy Verdict** card shows "Markdown looks inflated — you've paid less than this 'special' recently" and a price-driven `buy` reads as **wait**. An out-of-stock item stays **buy** (need wins) but still shows the inflated-markdown reason.
- [ ] **Money off** → no Deal-alerts settings section, no `good_deal` alerts, no fake-markdown demotion.

### C-9.7 alerts email digest — origin FU-205
- [ ] Heading + caption of the "Alerts email digest" card read cleanly across all themes. (Verified 2026-07-22: the card renders directly after Weekly deals — **note the checklist says Settings → Preferences; it actually lives on Settings → Notifications**, doc drift from a settings-tree reorganisation.)
- [ ] **SMTP-gating (R-014), the ON half:** with `DORA_SMTP_USERNAME` set + restart the toggle enables, the caption hides, and `GET /api/health` shows `features.email_smtp_configured: true`. (Verified 2026-07-22: the OFF half — toggle disabled with "Email isn't set up on this install yet — ask an admin to configure SMTP and this toggle will unlock." and health `false`.)
- [ ] Opt-in round-trip: master toggle on → toast → cadence select appears (Daily default); switch Weekly → day select; pick a day; reload survives. Network panel: master sends `{alerts_email_enabled, alerts_email_cadence}` together; later edits send single changed field
- [ ] `GET /api/auth/me` returns `alerts_email_enabled`, `alerts_email_cadence`, `alerts_email_day` on user payload
- [ ] Real SMTP send: real env + opted-in + an expired stock item → trigger job → inbox receives digest with actionable item in "Needs action", "Open Alerts" button linking to `<DORA_PUBLIC_URL>/alerts`, plain-text fallback
- [ ] Dedup: trigger again → no second email; mark item not-expired/delete → trigger → no email + `last_emailed_at` clears; re-add same name → trigger → fresh email
- [ ] Weekly day gating: cadence=weekly, day=Monday; non-Monday → trigger → no email; Monday → email lands
- [ ] Schedule fires: confirm `alerts_digest` job in APScheduler's job list (07:00 CronTrigger)

### C-9.8 web-push channel — origin FU-206
*Prereq: generate VAPID keys per FU-207*
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
*Requires admin login.*
*(Server contract pinned 2026-07-20 in `tests/e2e/dora_api/test_users_admin.py`: create → 200 + a one-time password (≥12 chars) in the body + the user is listed (admin flag honoured); create with a **taken username** / **taken email** / **malformed email** → 422; **delete your own account → 403** ("your own account"); delete another user → 204 and they leave the list; delete unknown → 404. The PATCH last-admin-demotion guard is pinned in `test_patch_semantics.py`. The dialog/result/copy/badge/tooltip renders below stay owner-walk.)*
- [ ] Settings → Admin → Users: the header now has **Add user** (primary button, account-plus icon) alongside the refresh button.
- [ ] Click **Add user** → dialog opens with Username / Email (optional) / Admin toggle. Cancel closes without side effects.
- [ ] Submit with only a username filled → dialog closes → "User created" result dialog appears with the one-time password + Copy button (the server contract is pinned above; this checks the dialog render).
- [ ] Copy button copies the password; toast "Copied to clipboard." Close the dialog — password is gone (no way to retrieve it; admin must reset if lost).
- [ ] Log in as the new user with the copied password → login succeeds → normal onboarding path.
- [ ] Taken-username / malformed-email / taken-email adds render the error **inline** under the offending field (the 422s are pinned above; this checks the inline render, not the status).
- [ ] Try Add with the Admin toggle on → new user appears in the list with the yellow "admin" badge.
- [ ] Each row now has a **Delete** button (red text, trash icon).
- [ ] Delete on **your own row**: the button is **disabled** + tooltip "You can't delete your own account." (the server also refuses it — 403, pinned above).
- [ ] Delete on another user → confirm dialog appears with negative-coloured Delete CTA + honest scope copy ("sessions, alert prefs, push subs removed; household-shared things survive"). Cancel closes with no change.
- [ ] Confirm delete → toast "Deleted 'X'." → user disappears (the delete itself is pinned above); their historical audit events still exist (audit-log page keeps the row with the now-orphan actor_user_id).
- [ ] Recipes / shopping lists that the deleted user authored / cooked survive with a null author (RecipeCookEvent.cooked_by_user_id and ShoppingList.created_by_user_id are SET NULL).
- [ ] With only one admin remaining, attempt to delete that admin → toast "Delete failed." with caption "Refusing to delete the last admin — promote someone else first." No deletion happens. *(Delete-guard hard to reach in tests — self-delete precedence; the symmetric PATCH-demotion guard is pinned.)*

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
- [ ] **Inbox A (new address):** "Confirm your new Dashy Dora email" with the confirmation link — click → /confirm-email-change → success → the next /auth/me probe surfaces the new address in the menu
- [ ] **Inbox B (old address):** "An email change was requested on your Dashy Dora account" notice rendered from `email_change_notice.html` arrives **before** the confirmation in inbox A (same task; best-effort, but expected when SMTP is up). Old address never loses anything until the confirmation link is clicked
- [ ] With `DORA_SECURE_COOKIES=1` set on the server, the `dora_csrf` cookie also carries **Secure**. (Verified 2026-07-22 without that env: `Set-Cookie: dora_csrf=…; Path=/; SameSite=Lax`, no HttpOnly — so `document.cookie` can read it, which the double-submit design requires.)

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
- [ ] **Paid-provider flow (OpenAI / Anthropic / Gemini)** without `DORA_LLM_KEY_ENCRYPTION_KEY` set:
  - [ ] Try to save an API key → 422 with caption "`DORA_LLM_KEY_ENCRYPTION_KEY` isn't configured — paid-provider API keys can't be saved." (Or the friendly form via the error toast.)
  - [ ] Ollama saves still work.
- [ ] **Paid-provider flow with the env var set** (generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`, set in API server's env, restart):
  - [ ] Save API key → toast "API key saved." → page shows "••••••••• (saved)" placeholder. Refresh: still shows saved.
  - [ ] Save model name. Toggle AI on. Send a chat message → routes to the chosen paid provider (verify via outbound network log or by using a deliberately-wrong key and seeing the LlmUnavailable fallback fire).
  - [ ] "Remove saved key" button clears the key (server: `has_llm_api_key` flips false). AI toggle disables again with "Save an API key first" hint.
- [ ] **Per-user isolation**: User A configures Ollama + enables. User B configures OpenAI + enables. Both can chat at once; A's request hits Ollama, B's hits OpenAI. (Logs or outbound network confirm.)
- [ ] **Anthropic + Gemini smoke**: configure one of each with a valid key, send a chat that triggers a tool call (e.g. "what's low?"). The response shows the data — confirming the tool-call adapter round-tripped through `ask_assistant`.
- [ ] **Backup → restore** round-trips the new User columns + `master_llm_enabled` (the api-key ciphertext should survive a backup/restore — it's stored as a `LargeBinary` blob like `User.image`).

### Visual rebuild Phase 3 — cross-theme walk — origin FU-283
- [ ] Walk every settings page in Pesto Light + Pesto Dark + Cherry Cola Dark
- [ ] Confirm: sticky nav, dropped card chrome, DoraSegmented in sunken-fill mode, theme card 2px accent border + check_circle badge, page padding breath all read

### Settings Phase 4 — profile picture — origin FU-286
- [ ] `flask db upgrade` applies `a4f7c2e9b6d1` up **and** down, single head
- [ ] `pytest tests/e2e/dora_api/test_auth_flows.py` green (two new tests + no regressions)
- [ ] Browser: upload picture on Account → appears immediately on menu bar (cache-bust), Account header, admin Users row; clear → all revert to icon/initials; hard-refresh both states survive; >4.5MB image rejected with a usable message

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

### PreferredBuy — origin FU-211
*(Backend fully pinned: add / rename / delete, alphabetical detail listing, blank-label reject, wrong-item-scope 404 (`test_preferred_buys.py`) + CASCADE-on-item-delete → 0 rows (`test_delete_integrity.py`). **"reorder (up-down)" is stale** — the manual reorder UI + `position` column + `reorder` endpoint were retired by FU-225 (2026-06-18); the SPA now sorts alphabetically client-side. Only the add/rename/remove detail render stays owner-walk.)*
- [ ] Stock item detail: add / rename / remove preferred-buy entries renders correctly (server contract + cascade pinned above)

### Shopping line preferred-buy hint — origin FU-215
- [ ] Pick a preferred-buy hint on a shopping line → persists across reload
- [ ] Clear the hint → persists across reload

### Stock-item Prices section — origin FU-213
*(Backend fully pinned in `test_price_observations.py`: logging an observation derives `unit_cost` (latest-wins), removing it clears `unit_cost`, plus dimension/unit-alias/store-resolution + non-positive/unknown-store rejects. The money-off gating below is client-side.)*
- [ ] Section is hidden when money features are off (the log/remove/unit_cost contract is pinned above)

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

### FK-index migration applies incrementally on a populated DB — origin FU-563 (2026-07-15)
*The test suite covers the from-empty upgrade and the `create_all` path; this confirms the additive index migration also applies cleanly to an already-populated existing install (the real self-host upgrade path).*
- [ ] On an **existing** install with real data at the previous head (`a1b7f3e9c2d4`), run the app's startup upgrade (or `flask db upgrade`) → migration `b9d4f2a7c3e1_20260715_fk_covering_indexes` runs, boot completes, no error, and the app behaves identically (indexes are transparent).
- [ ] Optional Postgres pass (when a disposable PG is available, FU-405): `DORA_TEST_DB=postgres` full suite stays green — confirms the 43 `CREATE INDEX`es apply on Postgres too, not just SQLite.

### FK ondelete rebuild preserves data + fixes delete behaviour — origin FU-565 (2026-07-15)
*Migration `d3f8b1a6c4e2_20260715_fk_ondelete_drift` rebuilds `StockItem`, `Product`, `ProductOffer`, `ProductHistoricOffer` on SQLite to recreate 6 FKs with their correct on-delete rule. `StockItem` is the biggest/most-referenced rebuild in this arc — confirm on real data.*
- [ ] On an install with real `StockItem` (and ideally `Product`/offer) data, run the startup upgrade → migration runs, **all rows survive**, and the FU-563 covering indexes + `StockItem.usual_store_id`'s existing SET NULL are intact.
- [ ] Spot-check the fixed behaviour: delete a `StockLevel`/`StockGroup`/`StockLocation` that a stock item references → the item's link **clears (SET NULL)** instead of erroring; deleting a `Product` cleans up its offers (**CASCADE**); a `Store` still referenced by a product is **blocked (RESTRICT)**.
- [ ] Optional Postgres pass (FU-405): same migration via native DROP/ADD CONSTRAINT (no rebuild) — `DORA_TEST_DB=postgres` suite green.

### Product nullability rebuild preserves data on a populated DB — origin FU-564 (2026-07-15)
*Migration `c1e8a5f3d9b2_20260715_product_nullability` rebuilds the `Product` table on SQLite (`batch_alter_table`) to tighten `is_active`/`is_available` to NOT NULL and loosen `merchant_stockcode` — a table rebuild is more invasive than the FU-563 `CREATE INDEX`, so confirm on real data. (No-op on installs with no products.)*
- [ ] On an install with **real Product rows** (products layer populated), run the startup upgrade → migration runs, all Product rows survive the rebuild, `store_id` FK + the `ix_Product_store_id` index are intact, and product surfaces (My Products, Price History, stock-item Products tab) render normally.
- [ ] Confirm any pre-existing `Product` rows with NULL `is_active`/`is_available` (if any) came through as active/available (backfilled to true), and that a product insert now requires those flags (dev + prod agree).
- [ ] Optional Postgres pass (FU-405): the same migration applies via native `ALTER COLUMN` (no rebuild) — `DORA_TEST_DB=postgres` suite green.

### Production WSGI server (gunicorn) — origin FU-397 (shipped 2026-07-14)
*Can't be run on the Windows dev box (gunicorn needs POSIX/fcntl) — confirm in the Linux container or a Linux/WSL checkout.*
- [ ] Build + boot the container with `DORA_ENV=production` (compose default) and the required prod vars set → container logs show `[startup] dora_api via gunicorn (production WSGI, gunicorn.conf.py)` and gunicorn's own boot lines (`Booting worker`, `Listening at: http://0.0.0.0:5170`), **not** Flask's `WARNING: This is a development server`.
- [ ] Confirm exactly **one** gunicorn worker by default (`ps aux | grep gunicorn` inside the container → one master + one worker); the SPA + API respond normally through nginx on `:5174`/`:5170`.
- [ ] Scheduler still fires once: check the logs over a reset interval (or set `DORA_DEMO_MODE=true` + `DORA_DEMO_RESET_MINUTES=2`) → the demo reset / scheduled jobs run **once** per interval, not duplicated.
- [ ] Force the dev server in a container with `DORA_API_SERVER=flask` → logs show `via Flask dev server`; force gunicorn in a dev profile with `DORA_API_SERVER=gunicorn` → gunicorn boots. (`auto` picks by `DORA_ENV`.)
- [ ] Set `DORA_WEB_CONCURRENCY=2` → boot logs carry the loud `WARNING: DORA_WEB_CONCURRENCY>1 duplicates scheduled jobs` line (don't run a self-host instance this way).
- [ ] Restart-cleanliness: `docker compose restart` → gunicorn comes back up, migrations run once, no port bind race with nginx.

### Dev seed runs under load by default — origin FU-388 (2026-07-14)
*The dev seed now appends ~500 bulk "load" stock items (+ products/offers, history, ~62 recipes, a big shopping list) so every interactive session runs loaded. Env-gated via `DORA_SEED_BULK_ITEMS`; the e2e suite passes 0. Quick eyes-on to confirm it seeds and the app stays usable under load.*
- [ ] Boot a dev instance with `DORA_ALLOW_DESTRUCTIVE=true` (default `DORA_SEED_BULK_ITEMS`) → Stock overview shows ~521 items ("Load item 0000 · …" through ~0499) alongside the curated fixtures; the page renders + filters without hanging.
- [ ] Dashboard, Locations heatmap, Cookbook (with ~68 recipes), and a big shopping list ("Big load list") all render under the load — note anything that feels slow (that's the FU-388 sweep's input).
- [ ] Boot with `DORA_SEED_BULK_ITEMS=0` → back to the ~22 curated items only (no "Load item …" rows), for when you want a light DB.
- [ ] `DORA_SEED_BULK_ITEMS=2000` → seeds the larger set without erroring (upper-bound sanity).

### Playwright browser-E2E smoke — CI / cross-OS re-run — origin FU-540
- [x] First run GREEN on this Windows dev box (2026-07-12, driving system Chrome via `DORA_E2E_CHANNEL=chrome` since the bundled binary won't download here) — 9 tests: login good/bad creds + authed nav over dashboard/stock/cookbook/meal-plans/shopping-lists + a real /api handshake. Selectors confirmed against the running app.
- [ ] Re-run in CI (bundled Chromium, `DORA_E2E_CHANNEL` unset) once CI is un-commented (FU-405), and on Linux, to confirm cross-OS. (Complements, does not replace, the manual walks below.)

### Fresh-install migration boot — origin FU-549 (FIXED 2026-07-13 — confirm on a clean install)
- [ ] On a machine with a clean `pip install -r requirements.txt` (now pins `alembic==1.14.1`), point at an **empty** database and boot in production mode (the path that runs `flask_migrate.upgrade()`, not the create_all seed path) → the app migrates cleanly to head and starts, **no** `a3e9f6c2d8b4` Alembic batch `'BINARY' has no attribute 'name'` crash. The crash was fixed 2026-07-13 (batch renames now pass `sa.BINARY(16)` instead of `UUIDType()`) and is now covered by `tests/test_migrations.py::test__migrations__upgrade_head_from_empty_succeeds` — this is the eyes-on-the-running-thing confirmation on the real prod toolchain.

### Companion push round-trip after `merchant`→`store` field fix — origin FU-554 (FIXED 2026-07-13)
- [ ] With both services standing, push a scraped offer from the companion (`dora-companion` — single-push button or batch-push toolbar) → Dora accepts it (no `400 unexpected key 'merchant'` from `_ProductIn`'s `extra="forbid"`); the product lands / quarantines as `store_not_mapped` rather than schema-rejecting. The payload field was renamed `merchant`→`store` in `companion_common/dora_ingest.py::build_payload` to match Dora's Phase-E `_ProductIn`. If both services are up, also re-run `dora-companion/tests/test_integration_dora_roundtrip.py` (needs a live Dora).

### Demo / sellable-showcase mode — origin FU-392 (shipped 2026-07-13)
- [ ] Boot the API with `DORA_DEMO_MODE=true` (any profile) → on boot the DB is wiped + re-seeded from the curated showcase dataset (`seed_showcase.py`), NOT the dev fixture: no "Sriracha (chatty history test)" item, no real personal email, clean pantry/recipes/meal-plan/shopping story. Log in as `demo` / `demo` (admin).
- [ ] With demo mode on, the SPA shows the persistent floating **"Demo mode — this is sample data that resets periodically."** pill (bottom-centre, brand-accent) on every screen, pre-auth and post-auth. It does not reflow layout or cover the mobile bottom nav.
- [ ] Boot **without** `DORA_DEMO_MODE` (normal install) → **no** demo banner anywhere; `GET /api/auth/capabilities` returns `demo_mode:false`; the normal dev-seed / prod-upgrade boot path runs unchanged.
- [ ] Leave demo mode running with default `DORA_DEMO_RESET_MINUTES` (60) — or set it low (e.g. `2`) to test faster — make a visible change (tick a shopping-list line, delete a stock item), wait for the interval, reload → the dataset is back to its curated baseline (scheduled `reset_showcase` fired).
- [ ] Boot with `DORA_DEMO_MODE=true` + `DORA_DEMO_RESET_MINUTES=0` → showcase seeds once on boot but the scheduled reset job is NOT registered (static demo); changes persist until the next manual restart.

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

### Main menu bar bottom border removed — origin FU-363 item 6 (2026-07-15)
*Subjective micro-polish — trivially revertible (re-add `bordered` to the `q-header` in `MainLayout.vue`) if it reads worse.*
- [ ] On desktop, the app header/main-menu bar no longer has a hairline bottom border; it still reads as a distinct bar from the page below (the toolbar background separates it). Check in both light and Pesto-dark themes.
- [ ] On mobile, the left side drawer still has its border (only the top header border was removed).

### Support / "Report an issue" channel — origin FU-370 (2026-07-14)
*Shipped **dormant**: with no channel configured (`support_channel.py` constants blank + no `DORA_SUPPORT_*` env) nothing new should render. Verify both states — dormant, then configured (easiest: boot the API with `DORA_SUPPORT_URL=https://example.com/new?template=bug_report.yml`, or `DORA_SUPPORT_EMAIL=you@example.com` to check the mailto path).*
*(Server contract confirmed 2026-07-20 by a once-off in-process check: dormant default → `GET /api/health` `support: {url:'', email:''}` (client self-gates → no button); `DORA_SUPPORT_URL` set → resolver returns it with URL winning over a set email; `DORA_SUPPORT_EMAIL`-only → `{url:'', email:…}` (mailto path). So the `/health` value that drives every button below is verified — the remaining bullets are just the **UI renders** for each state, which stay owner-walk.)*
- [ ] **Dormant (default):** Help page header shows **no** "Report an issue" button; the About tab reads the honest one-person copy ending "…pass it to whoever runs this Dora instance"; DoraBot "this is broken" reply points at Help with no external link; a forced full-page error shows no "Report this" button
- [ ] **With `DORA_SUPPORT_URL` set:** Help header shows a **Report an issue** button that opens the URL in a new tab with `?title=…&body=…` appended (and the existing `?template=` preserved via `&`); About tab's last paragraph now points at "the **Report an issue** button at the top of this page"
- [ ] DoraBot: type "something's broken" → the reply offers a **Report it** button that opens the same URL in a new tab
- [ ] Force a page error (e.g. break a route) → the error screen's **Report this** button opens the channel pre-filled with the screen/path/reference/error message
- [ ] **With only `DORA_SUPPORT_EMAIL` set (URL blank):** all the above open a `mailto:` link with a pre-filled subject/body instead of a URL
- [ ] Non-admin user sees the button too (the channel comes from `/api/health`, not an admin-only setting)

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
*(Verified live 2026-07-20 (browser drive): seed state is products-on + url-blank, and the main nav renders Stock / My Products / Cookbook / Meal plans / Shopping lists / Reports with **no Product Search entry** and no disabled tooltip — the R-029 "hide, don't nag" behaviour. The products-off and valid-URL states below need a Settings toggle to walk.)*
- [ ] With **products off** in Settings → System → Features → Products: no Product Search entry in the main navigation (unchanged behaviour)
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
*(Header **presence + values** pinned 2026-07-20 in `tests/e2e/dora_api/test_security_headers.py`: all four headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer-when-downgrade`, CSP with `default-src 'self'` / `frame-ancestors 'none'` / `img-src … data: blob: https:` / `base-uri` / `form-action`) land on a 200, a 404, AND a domain-error response. The `curl -I` operator check and the browser CSP-violation walk below stay owner-walk.)*
- [ ] Cold-load the SPA → no CSP violations in Console
- [ ] Walk Dashboard, Stock overview, Stock item detail, Cookbook overview, Recipe detail (with an image), Cook mode, Meal plans, Shopping list detail, Settings → each page renders normally, no red CSP errors on any surface
- [ ] Recipe / product / store images render (base64 `data:` blobs + external `https:` sources both work under `img-src`)
- [ ] Upload a recipe/user image (data-URL / blob path) → preview renders (blob: is allowed)
- [ ] Print view opens and renders (if any style-src / script-src violation would clobber it, it'd be visible here)
- [ ] Piper TTS synthesis + assistant chat still work end-to-end (connect-src covers the `/api` calls; anything to an external LLM URL relies on `https:` allowance)

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
*(Verified 2026-07-23: zero "Discount Dora" in FE+BE source or DOM; tab titles/mascot alt/About/version-replies all "Dashy Dora". Only the PWA-install app-name below → device.)*
- [ ] PWA install prompt (Chrome address bar → install app) shows "Dashy Dora" as the app name (from productName in package.json)

### D.O.R.A. bot rename + acronym easter egg (2026-07-01)
*(Verified 2026-07-23: D.O.R.A. chat-header label renders live; acronym tooltip + "Meet D.O.R.A." Help button + `/help/dora` copy source-confirmed. Only the Thanks-chip below → owner-walk.)*
- [ ] Chat suggestion chips include "Thanks D.O.R.A." (not "Thanks DoraBot"). Clicking it replies with the sparkle/thanks flow the old chip triggered

### Nav-state policy: filters survive navigate-back, reset on reload (A8 §3, 2026-07-01)
- [ ] Stock Overview: type in the search box, tick a couple of filter chips, change the sort. Click into any stock item detail → hit browser back → search text, chip states, and sort are all preserved. Scroll position on Stock Overview is restored too
- [ ] Cookbook: same drill — set search, toggle favourites-only + cookable-now-only, change sort axis + direction. Navigate to a recipe → back → all preserved, including expanding/dietary/tools filters
- [ ] My Products: set search text + a store filter + the "On deal only" chip. Navigate to another route (Dashboard) → back → preserved
- [ ] Hit F5 (full reload) on any of those three pages → all filters reset to defaults, scroll to top. This is the intended "clean slate" behaviour
- [ ] Sign out and sign back in as the same user → filters reset (sign-out flow currently does a full reload; if it doesn't in future, FU-355 will wire an explicit clear)
- [ ] Other list pages (MealPlans, ShoppingLists, Stocktake, admin settings) still reset on nav-back — they haven't been migrated yet (FU-354). That's expected, not a bug

### `/data/barcodes` redirects + shell shows two cards — origin FU-340 (2026-07-01)
*(Verified 2026-07-23: `/data/barcodes` (+`?action=scan`) → qr-labels. The "two cards" shell is gone — FU-341 relocated `/data/*` under `/settings/admin/data` (`#/data` → backup). Only the tooltip below → owner-walk.)*
- [ ] Stock item detail page: the "Print label" tooltip on a stock item's Dora-QR button no longer references "Data → Barcodes" — the copy explains barcodes register a Product, not a stock item

### `/data/export` page retired — origin FU-339 (2026-07-01)
*(Verified 2026-07-23: `/data/export` + `/data` → `/settings/admin/data/backup` (FU-341 relocation; a clean redirect, not a 404 — retirement intent met). Print-still-works bullets below → owner-walk.)*
- [ ] From a recipe detail: the Print action still opens the print-view in a new tab (unchanged)
- [ ] From a shopping list detail: the toolbar menu still exposes "Print / Save as PDF" (unchanged)
- [ ] From `/stock`: the toolbar export menu still exposes CSV + Print (unchanged)
- [ ] From `/meal-plans`: the Print icon-button added in FU-338 still opens the print-view (unchanged). *(FU-304 closed 2026-07-07: `/meal-plans/board` retired; nothing to check on the old Board page.)*
- [ ] No console errors on any of the above about a missing route or a missing component

### Settings shell — independent sidebar/main scroll — origin worklog 2026-07-01- [ ] Scroll the main pane deep into a long settings page (e.g. Preferences) — the sidebar stays exactly where it is (no drift, no sticky-header jitter)
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
*(Verified 2026-07-23: Help/avatar nav + no dropdown chevron (avatar tooltip is "Account settings"). Ring pulse/fade + theme bullets below → V-pack.)*
- [ ] No Sign-out anywhere in the app toolbar (MainLayout) — Sign-out now lives in the Settings shell page header (see below), not on the Account page anymore
- [ ] On `/help` or `/help/dora`: **Help icon pulses** in the slide-flash colour, then settles into the 3px accent ring. Avatar stays inactive (no ring)
- [ ] On any `/settings/*` page: **avatar pulses + settles** to the accent ring. Help icon stays inactive
- [ ] Switching between Settings sub-pages (`/settings/account` → `/settings/preferences` → `/settings/notifications`) — avatar ring stays lit, **no re-pulse**
- [ ] Switching between `/help` and `/help/dora` — Help ring stays lit, **no re-pulse**
- [ ] Cross between sections (`/settings/account` → `/help`): avatar ring fades out (~320ms), Help ring pulses + settles. Reverse direction also smooth
- [ ] Navigating between Help/Settings and the main menu (e.g. `/help` → `/cookbook`): header ring fades out, main-menu Cookbook underline fades in. No stuck flash colour
- [ ] Theme switch — both buttons' flash + resting colours follow the active theme's `--nav-slide-flash` + `--brand-accent` tokens

### Sign-out moved into the Settings shell header (2026-07-13)
- [ ] On any `/settings/*` page: a **"Sign out"** button (logout icon, danger-ghost styling) sits on the **right** of the shell header, inline with the Settings/Admin toggle (admins) or the "Settings" title (non-admins)
- [ ] Click it → you're signed out and land on `/login`; the button shows its loading state while the request is in flight
- [ ] Settings → Account no longer has a "Sign out" section/card at the bottom (it moved to the header)
- [ ] Both admin (toggle shown) and non-admin (plain title) accounts show the button correctly right-aligned; no overlap/wrap at narrow desktop widths, and it still renders on the mobile settings layout
- [ ] Mobile (`<md`): both buttons render in the header (next to the AlertsBell), rings still work
- [ ] **Reduced-motion** (DevTools → Rendering → "Emulate CSS prefers-reduced-motion: reduce"): rings appear in the resting accent colour **without** the pulse beat on either button

### R-016 lazy hydration sweep — five pages — origin FU-221
*(Verified 2026-07-23 (XHR-instrumented nav sweep): stock-items + recipe list fire once, 0 on revisit. Post-mutation refresh bullet below → owner-walk.)*
- [ ] Post-mutation refresh paths still work (e.g. create a stock item → list updates; rename one → name updates) — those still call the raw `getXAsync()` and must not have been broken by the sweep

### R-016 extension to recipe / shoppingList / location / recipeVocab / mealSlot stores- [ ] Recipe create / edit / delete still refreshes the overview (post-mutation calls `recipeStore.getRecipesAsync()` directly — must keep working)
- [ ] Shopping-list mutations (add line, finish shopping, remove from list) still refresh summaries (post-mutation calls `shoppingListStore.refreshAsync()` — must keep working)
- [ ] Location CRUD on settings → Stock Locations still refreshes the tree (post-mutation calls `locationStore.refreshAsync()` — must keep working)
- [ ] QuickAddSheet open → shopping-list summaries appear; CreateStockItemDialog open → location picker has options
- [ ] DoraChat: ask a recipe-aware question on a cold session — recipes + vocab populate before the answer; ask again on a warm session — no second fetch

### Drag-and-drop affordance parity (post `useDragDropList` refactor) — origin FU-326
*(Class parity verified 2026-07-23: shopping lines + recipe ingredients both use `.dora-dnd-row`/`.dora-dnd-handle` (old per-surface classes gone). The drag interaction below → owner-walk.)*
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

### `formatQuantity` rollout — origin FU-321- [ ] Meal-plan "This week's shopping" — `unit="g"` reads `"needs 250g · …"`; `unit="tbsp"` reads `"needs 1 tbsp · …"`; null unit reads just the quantity
- [ ] Sequential Builder Dialog preview list — same three cases; rounded number is what `formatQuantity` receives
- [ ] Substitute ratio caption on stock-item detail: `1 tbsp → 3 tsp` reads exactly that (both halves spaced); direction "this → that"
- [ ] Substitute ratio caption in cook-mode swap picker: same ratio reads identically. `250 g → 1 cup` reads `"250g → 1 cup"` (asymmetric — mass tight, volume spaced)
- [ ] Recipe print view (window.open from RecipeDetailPage export): `2 tbsp olive oil` → `"olive oil — 2 tbsp"`; `250 g flour` → `"flour — 250g"`; `1 onion` (no unit) → `"onion — 1"`; `salt` (both null) → just the name, no em-dash

### Unsaved-changes guard rollout — origin FU-322- [ ] **AccountSettings** — edit `usernameDraft`, click a sidebar link → confirm dialog. Cancel → still on page. Confirm → nav completes. Repeat for `emailDraft`. Revert draft → nav with no prompt
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
*(Verified 2026-07-23: Features panel renders 7 toggles (checklist's "5" is stale) with captions, every state matches `/api/health`. Persistence/non-admin/migration/theme bullets below → owner-walk.)*
- [ ] `alembic upgrade head` applies `a3b8e2f4c1d7` on SQLite + Postgres; `verify_mappings()` passes for reshaped `AppSetting`
- [ ] Each toggle on → toast + persists across reload
- [ ] Each toggle off → toast + persists
- [ ] As non-admin: panel renders "no admin permissions" banner; toggles not visible
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
