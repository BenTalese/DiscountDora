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
## [OPEN] FU-NNN — short title
- **Raised:** YYYY-MM-DD (prompt id / task)
- **Type:** follow-up | deferred job | leftover | finding
- **What:** one or two lines.
- **Why deferred:** the reason it wasn't done in-line.
- **Recommended resolution:** now | later during <Phase/Prompt X> | when <trigger> | opportunistic
```

---

## [OPEN] FU-NNN — short title
- **Raised:** YYYY-MM-DD (prompt id / task)
- **Type:** follow-up | deferred job | leftover | finding
- **What:** one or two lines.
- **Why deferred:** the reason it wasn't done in-line.
- **Recommended resolution:** now | later during <Phase/Prompt X> | when <trigger> | opportunistic
- **State note:** (filled in when resolved — date + how)
```

---

# Open

## [OPEN] FU-591 — Playwright e2e suite doesn't run green in one long single-worker pass (14 failures; degrades over the 20-min run)
- **Raised:** 2026-07-20 (verify campaign — pivoting to e2e specs)
- **Type:** finding (test-infra).
- **What:** a full `npx playwright test` run (87 tests, **1 worker**, ~20 min)
  came back **65–67 passed / 14 failed / 6–8 did-not-run** across two runs. The
  14 failures are dominated by environment degradation, not logic: `Target
  page, context or browser has been closed` (browser crash), 30s "waiting for
  element" timeouts, null `boundingBox`es — on ~13 specs that were individually
  green (buy-verdict, detail-products, detail-recipes, dora-score, history-tab
  ×4, recipe-deeplink ×3, stock-pickers, stock, cook-mode-finish). Several fail
  *before* any new spec runs, so it isn't data pollution — it's the long-lived
  debug-mode SQLite backend + browser degrading under a 20-min single-worker
  grind (verbose per-request DEBUG logging is a prime suspect for backend
  slowdown).
- **Why it matters:** the verify campaign's premise is "a UAT round re-verifies
  everything by running `npm run test:e2e`" — that only holds if the suite runs
  green. Right now a single long run is unreliable on this box, which also
  blocks pinning new UI flows via e2e (see the cook-mode-finish.wip.ts casualty).
- **Candidate fixes:** raise `workers` (parallel shards finish faster, each
  browser context shorter-lived); quiet the e2e backend logging
  (`serve.py` debug → INFO/WARN, or disable per-request DEBUG) to cut backend
  latency; split the suite into batches in CI; add per-spec browser-context
  recycling. NOTE: `workers>1` is NOT a drop-in — the specs share ONE seeded
  backend + DB (no per-test rollback in e2e), so parallel workers would collide
  on shared fixtures; it needs per-worker DB isolation first.
- **Mitigation attempted 2026-07-20 — DID NOT FIX IT (kept anyway):** added a
  `DORA_LOG_LEVEL` env override (`logging_setup.py`) + `DORA_LOG_LEVEL=WARNING`
  in the e2e webServer env. Confirmed effective at the log layer (raw run log
  dropped ~5 MB → a few KB). BUT the re-measured full run came back **16 failed /
  59 passed / 19.2 min — WORSE than the prior 14**, and some failures are *early*
  (e.g. `auto-add-on-low:110`, test 5, 30s toast timeout) so they aren't
  cumulative-degradation at all. Conclusion: **backend log volume was not the
  (main) cause.** The `DORA_LOG_LEVEL` knob is kept as a real operator/ops
  improvement, but it is NOT the FU-591 fix.
- **Revised read:** the suite has (a) a set of *inherently flaky* specs
  (toast/element-timing 30s timeouts that trip even on a fresh box) and (b)
  single-worker fragility / browser-process degradation over 87 tests. This is a
  **real infra project**, not a quick inline fix — candidate work: give each
  worker its own seeded backend+DB so `workers>1` is safe (parallel = shorter
  browser lifetimes + faster), recycle the browser context/process periodically,
  and separately harden the individual flaky specs' waits (await the specific
  toast/row, not `networkidle`). **Do NOT keep re-running the full 20-min suite
  to chase this** — it doesn't converge; it needs a dedicated, designed fix.
- **Recommended resolution:** owner decision — schedule as a dedicated e2e-infra
  hardening task; until then, treat e2e as a best-effort smoke layer, not a
  clean UAT gate, and codify via backend/Vitest where possible instead.

## [OPEN] FU-586 — Dashboard money loaders race the one-shot /api/health flags probe on a cold mount
- **Raised:** 2026-07-19 (verify Batch 10 — codifying FU-300/FU-297)
- **Type:** finding
- **What:** `DashboardPage.loadAll()` fires all card loaders on mount, and each
  money loader (`loadBudget`, `loadSavings`, `loadSpendByStore`,
  `loadPantryValue`, `loadSwapSummary`, …) early-returns when
  `moneyEnabled.value` is false. On a cold page load the `useFeatureFlags`
  `/api/health` probe usually hasn't resolved by mount, so `installEnabled` is
  still false, the loaders skip, and **nothing re-runs them when the flags
  land** (no `watch(moneyEnabled)`, no await on `flagsLoaded`). Reproduced
  deterministically in e2e: with money ON at both layers, a hard reload of
  `/#/` fires zero `GET /api/budget/status`. The reactive template bits (Log
  price button) recover; the fetched card bodies don't until the user
  navigates away and back.
- **Why deferred:** product fix out of scope for a test-codify unit; needs a
  small design call (await `flagsLoaded` in `loadAll` vs a one-shot
  `watch(moneyEnabled)` re-trigger). `dashboard-log-price.spec.ts` deliberately
  does NOT pin the money-ON budget-status request — add that assertion when
  this is fixed.
- **Recommended resolution:** now — it's user-visible (money cards missing
  after a hard reload / PWA cold start until a second navigation).
- **2026-07-19 addendum:** same race, same fix needed for the
  **products-gated** loaders (`loadPriceDrops`, `loadBestDeals` gate on
  `productsEnabled` from the same one-shot probe). The
  `dashboard-price-drops.spec.ts` spec works around it by warm-navigating
  (land on `/#/stock`, then in-app goto `/#/`) — un-warm those specs when
  this is fixed.

## [OPEN] FU-585 — LogPriceSheet back arrow keeps the search query; FU-300 verify bullet expected it cleared
- **Raised:** 2026-07-19 (verify Batch 10 — codifying FU-300)
- **Type:** finding
- **What:** in `LogPriceSheet.vue`, the step-2 back arrow calls
  `clearSelection()` which drops only the selected item — the search query
  survives, so the user returns to their filtered shortlist. The DORA_VERIFY
  FU-300 bullet said "Back arrow returns to the picker with the search input
  cleared". The full reset (query + selection) happens on dialog dismiss
  (`onHide`), which IS pinned. Preserved-query-on-back is arguably the better
  UX (picked the wrong milk → back → still see milks), so this wasn't
  blind-patched to match the checklist.
- **Why deferred:** behaviour-vs-checklist design call, not a clear defect.
  `dashboard-log-price.spec.ts` pins the current behaviour with a comment
  naming this FU — flip the assertion if the call goes the other way.
- **Recommended resolution:** opportunistic — one-word decision; likely
  "keep code behaviour, checklist was aspirational".

## [OPEN] FU-584 — Detail-page e2e specs flake on a full-suite run: hash-goto doesn't reliably drive vue-router
- **Raised:** 2026-07-19 (verify Batch 10, running the full Playwright suite)
- **Type:** finding
- **What:** on a clean full-suite run on this box (fresh `dist/spa` build, system
  Chrome channel), ~12 detail-page specs fail — `history-tab.spec.ts`,
  `detail-recipes-tab.spec.ts`, `detail-products-tab.spec.ts`,
  `recipe-deeplink.spec.ts`, `stock-pickers.spec.ts`, one `buy-verdict.spec.ts`.
  **Different** tests fail across runs (flaky, not consistent), and every failure
  snapshot shows the **dashboard still mounted**, not the detail page. Common
  pattern: the spec does `page.goto('/#/')` then `page.goto('/#/stock/<id>')` —
  a same-document hash change that Playwright treats as an anchor navigation, so
  vue-router only routes if it catches the `hashchange`; under load it doesn't,
  the detail page never mounts, and the `getByRole('tab'/'button')` wait times
  out at 30s. This is the exact gotcha the verify-runner notes already document
  ("same-document hash-goto doesn't drive vue-router — engineer state via
  `page.request`, then one full-document goto").
- **Why deferred:** these are the parallel verify session's specs, not the
  Dora Score unit that surfaced the flake; fixing them is a cross-cutting spec
  change. The specs pass individually often enough that the parallel session's
  per-file runs went green — it's the full-suite + machine-load combination that
  trips them here.
- **Recommended resolution:** opportunistic but soon (the full suite can't be a
  reliable green gate until then) — replace the two-step `goto('/#/')` +
  `goto('/#/stock/<id>')` with a single full-document navigation to the detail
  URL (or a `waitForURL` + explicit router-ready wait) across the affected specs;
  a shared `gotoDetail(page, path)` helper is the clean fix. Re-run the full
  suite to confirm the pass count returns to the ~65 the campaign reported.
- **2026-07-19 addendum:** the race also reproduces on a *warm* history
  sequence, not just cold double-gotos — in `dashboard-next-cook.spec.ts` a
  `page.goBack()` to the dashboard followed by a click that `router.push`ed to
  cook mode wedged the router on a blank document (deterministically, even in
  isolation), while the visually identical sequence in `dashboard-donut.spec.ts`
  passed. Both specs now avoid it (reload → fresh hash-goto before the second
  navigation); fold "no history-back followed by another navigation" into the
  same sweep/helper.

## [OPEN] FU-583 — Kitchen-health action links carry query params StockOverview ignores (`?expiring=1`, `?stocktake=1`)
- **Raised:** 2026-07-19 (verify-campaign Batch 10, Dora Score codification)
- **Type:** finding
- **What:** `DoraScoreCard.vue`'s Freshness link navigates to `/stock?expiring=1`
  and Stocktake to `/stock?stocktake=1`, but `StockOverview.vue`'s
  `applyQueryFilters()` only honours `location_id` / `attention` / `level_id`
  (plus `create` and `recipe` handled separately) — both params are silently
  dropped, so the user lands on the full unfiltered pantry instead of "expiring
  items" / stocktake mode. Exactly the failure DORA_VERIFY's P8-08 L920 asked to
  flag. The other links are fine (Budget → preferences, Run-outs →
  shopping-lists); Waste deliberately has no link (D10 dissolved `/waste` — the
  e2e spec pins that absence, and the DORA_VERIFY bullet's `/waste` expectation
  was stale).
- **Why deferred:** codification unit (test-only); the fix is a small
  StockOverview change + choosing what `expiring=1` maps to (the expiring-soon
  filter chip) and whether `stocktake=1` opens the Needs-check filter or routes
  to `/stocktake`.
- **Recommended resolution:** opportunistic — extend `applyQueryFilters()` (or
  repoint the card links at params that exist); then extend
  `web_app/e2e/dora-score.spec.ts`'s link test to assert the filtered result,
  not just navigation.

## [OPEN] FU-581 — Stale `/product-search` links: three surfaces route to the retired route and land on the 404
- **Raised:** 2026-07-18 (verify Batch 3 — codifying the C-1b.3 Products-tab checks)
- **Type:** finding (real bug, needs a design call)
- **What:** FU-186 (Phase D) removed the in-app `/product-search` route — the Product
  Search nav entry now opens the external `AppSetting.product_search_url` in a new
  tab. But at least three call sites still `router.push` / link to the dead route,
  landing users on the 404 page:
  1. `StockItemDetailPage.vue` `onFindAndLink()` — the Products tab's primary
     "Find & link a product" empty-state CTA AND the "Link another" header action
     (it also passes `?q=<item name>` seeding that nothing consumes any more);
  2. `MyProductsPage.vue:184` (`to="/product-search"`) and `:1179` (another push);
  3. `DashboardPage.vue:655` — the empty-state "Hunt for deals →" CTA.
  Caught by the new `detail-products-tab.spec.ts`, which pins the CTA render but
  deliberately NOT its destination until this is decided.
- **Why deferred:** the right target is an FU-186-scoped design call, not a mechanical
  fix — options per surface: open the configured `product_search_url` externally (like
  the nav entry, but then the "link a product to THIS item" flow loses its seeding),
  route to My Products (which owns create/link actions now), or hide the CTA when no
  in-app destination exists. Blind inline patching risks re-conflating what FU-186
  deliberately split.
- **Recommended resolution:** now-ish (it's a user-visible dead end on three
  surfaces) — decide the per-surface target with the owner, then update
  `detail-products-tab.spec.ts` to pin the chosen destination.
- **State note:** (open)

## [OPEN] FU-580 — Features-page flag toggles don't take effect until a full page reload
- **Raised:** 2026-07-18 (verify Batch 3 — codifying the P8-05 feature-flag check)
- **Type:** finding
- **What:** the install-wide feature flags surfaced via `useBuyVerdictEnabled` /
  `useScanningEnabled` (and siblings) probe `/api/health` **once per document** and
  memoise the answer in a module-level ref. The Settings → Admin → System → Features
  toggle handlers (`AdminSystemFeaturesSettings.vue`, e.g. `onBuyVerdictToggle`) PATCH
  the setting and toast success but never call the composable's `refresh*()` — so in
  the running SPA session the badges/buttons gated by the flag don't appear/disappear
  until the next full page load. Surfaced when the e2e flag test failed on a hash-only
  (same-document) navigation; the codified test now reloads, matching the verify
  bullet's "Reload Stock Overview" wording, so current behaviour is pinned as-is.
- **Why deferred:** verification unit (R-008 scope discipline); the fix is a one-line
  `refresh*()` call per toggle handler plus deciding whether already-mounted consumers
  should also live-refetch.
- **Recommended resolution:** opportunistic — next time the Features settings page or
  the enabled-flag composables are touched, wire the toggle handlers to refresh the
  probes (and extend the e2e test to drop its reload).

## [OPEN] FU-582 — Finish & restock modal has NO per-item level pickers (server `level_overrides` contract has no UI)
- *(Renumbered from FU-580 on 2026-07-18 — a parallel session independently issued
  FU-580 for the Features-page reload finding; that one keeps the number.)*
- **Raised:** 2026-07-18 (UX round 5, driving the finish flow live)
- **Type:** finding
- **What:** the "Finish & restock" modal on a SHOPPING list shows only a flat list of
  ticked item names + Cancel / "Restock & finish" — no per-item level choice at all
  (screenshot `30-restock-review-modal.png`). But the UX-v2 M12 restock-review design
  (DORA_VERIFY 3-band bullet: "only 3 options per item — Stocked / Low / Out") and the
  server contract both expect per-item overrides: `FinishShoppingListRequest.level_overrides`
  exists, is documented "per-item level choices from the finish modal", and was
  backend-pinned green this morning (`test_stock_level_collapse.py` — override wins,
  unknown-level 422). The SPA evidently never sends it — a part-restocked item ("bought
  milk but it's still half-empty → Low") can't be expressed at finish time; everything
  ticked flips to Stocked.
- **Why it matters:** the DORA_VERIFY eyeball check for the modal can never pass as
  written; dead server surface (R-003 seam built, client half missing).
- **Recommended resolution:** owner decides — either build the per-item 3-option picker
  into the modal (the designed behaviour), or explicitly cut the override UI and note the
  carve-out (then simplify/keep the server contract for API users). Check git history for
  whether the picker UI was built and lost in a rebuild (C-19-style) before writing new UI.

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
  45. The missing restock-review pickers are FU-582 (functional gap, split out; renumbered from FU-580).
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

## [OPEN] FU-574 — Bogus runtime backend URL: no self-service recovery path in the browser
- **Raised:** 2026-07-17 (verify-campaign Batch 0, Runtime URL walk L112–114)
- **Type:** finding (real gap — verified live)
- **What:** Settings → About → **Change instance URL** (P8-10): saving an
  unreachable URL persists `dora.backendBaseUrl` and reloads — the app then
  renders the friendly full-page "Can't reach Dora's brain" screen (no crash ✅)
  whose **only affordance is "Try again"**. `#/settings/about` renders that
  same error screen, so the Change-URL prompt is unreachable and a browser/PWA
  user is stuck until they hand-clear localStorage. DORA_VERIFY L113 expects
  "the About page still lets you re-open the prompt to fix it" — that clause
  FAILS. (Native/Capacitor may differ — its no-URL guard bounces *to* About;
  not tested here.)
- **Fix shape:** add a "Change instance URL" escape hatch on the network-error
  screen when a runtime override is set (or let /settings/about mount without
  a reachable backend). Small, isolated.
- **Recommended resolution:** later, next time the error-page/runtime-URL
  surface is touched (papercut until the PWA/native distribution push — then
  it matters).

## [OPEN] FU-573 — "Removed from N lists" toast over-counts: server no-ops counted as removals
- **Raised:** 2026-07-17 (verify-campaign Batch 0, BuyVerdictCard walk L89)
- **Type:** finding (cosmetic accuracy — verified live)
- **What:** `useShoppingListActions.removeFromAllLists` fans
  `remove-by-stock-item` out over every open list and counts every
  **non-throwing** call as a removal — but the server endpoint is a deliberate
  no-op success when the list doesn't contain the item. Observed: item on 1
  open list, toast said "Removed from 3 lists." `useBuyVerdictActions.
  removeFromAllOpenLists`'s docstring ("returns the count actually removed")
  is wrong for the same reason.
- **Fix shape:** have the server return whether a line was actually removed
  (or its count) and sum that; or pre-filter `listIds` by the item's known
  membership (`membership.active_lists`) before fanning out.
- **Recommended resolution:** opportunistic (next touch of the shopping-list
  action seams).

## [OPEN] FU-570 — Boot proceeds silently against a stale/unversioned SQLite DB → per-request 500s
- **Raised:** 2026-07-16 (verify-campaign pilot)
- **Type:** finding (needs a decision — operator robustness)
- **What:** the pilot backend booted cleanly against the repo-root
  `dora.data.db` (July-10 vintage, created via `create_all`, **no
  `alembic_version` table**, missing newer columns like
  `AppSetting.auto_drain_past_meals`). No boot-time complaint; the app served
  traffic and 500'd request-by-request on the missing columns (dashboard showed
  7 friendly-error toasts). `/api/health` reported `schema_version:
  d3f8b1a6c4e2` regardless — it evidently reports code-side head, not the
  connected DB's version, which actively misleads during diagnosis. Consider:
  (a) boot-time guard comparing DB `alembic_version` (or its absence) to head —
  warn loudly or refuse with a friendly message; (b) `/api/health` reporting
  the DB's actual version (or both code + DB).
- **Why deferred:** design call (guard semantics for dev vs prod, SQLite vs PG)
  — not a drive-by fix.
- **Recommended resolution:** later, with FU-549's fresh-install-boot verify /
  the finalisation plan's ops chunk; decide guard vs health-field first.

## [OPEN] FU-575 — Stock-item / recipe name uniqueness is application-level only (concurrent-create race) + recipe name not whitespace-normalised
- **Raised:** 2026-07-17 (Codex review of stock-item create — P3, + a parallel spotted while fixing P1/P2).
- **Type:** finding (low priority).
- **What:**
  1. **P3 — no DB unique constraint on `StockItem.name`.** `CreateStockItemHandler` checks for an existing (case-insensitive) name before insert (`create_stock_item.py:~90`), but the column has no unique constraint, so two tabs/devices can both pass the check and insert the same name (a soft duplicate — not corruption). Same shape on `Recipe.name`.
  2. **Recipe name whitespace parallel** — the P2 fix added a `strip` `field_validator` to `Create/UpdateStockItemRequest`; `create_recipe.py` / `update_recipe.py` use `Field(min_length=1, max_length=255)` **without** it, so recipes still accept `" Foo "` / `"   "`. Same class, different surface (R-code-style consistency).
- **Why deferred:** the race is vanishingly unlikely + low-harm on a single-household self-host app (Codex itself rated it low). A real fix means a **unique constraint + migration + a case-insensitivity decision** (a plain unique index is case-sensitive on Postgres; case-insensitive uniqueness needs a functional index / `citext`, which differs SQLite↔Postgres — R-005/R-006 care). Disproportionate right now.
- **Recommended resolution:** opportunistic. (a) The recipe-name strip is a trivial 4-line `field_validator` mirror of the stock-item fix — do it next time recipes are touched. (b) The unique-constraint/race is a data-model call — bundle with the FU-045 Postgres/migration work or whenever concurrent-write hardening is on the table; decide case-insensitive-uniqueness semantics then.

## [OPEN] FU-567 — Relicense Dashy Dora off MIT for the paid self-host model
- **Raised:** 2026-07-16 (FU-412 self-host commercialization plan).
- **Type:** decision + deferred job (legal; prerequisite to charging).
- **What:** The repo ships under an **MIT licence** (`LICENSE`, © 2023 Ben Peter Talese),
  which explicitly permits resale and redistribution of the source. That directly
  undermines the paid-self-host model: FU-562's leverage is gating updates/downloads via
  an offline licence key, but under MIT anyone can legally strip the key check and
  redistribute the build for free. **Relicensing is a prerequisite to charging, not a
  nice-to-have** — the report (`COMMERCIALIZATION_REPORT.md` §1.2) flagged it as "consider";
  the self-host plan promotes it to a blocker.
- **Options (owner + lawyer call):**
  - **(a) Source-available commercial licence** — e.g. PolyForm Noncommercial, or a custom
    "you may run it, not resell/redistribute it" licence. Simplest fit for "sell the right
    to run it."
  - **(b) Dual licence** — free for personal/non-commercial use, paid commercial licence.
    Preserves goodwill + a free tier, adds enforcement teeth.
  - **(c) BSL (Business Source License)** — source-available now, converts to open (e.g.
    Apache) after N years. Popular for commercial OSS.
- **Also settle here:** the **scraping disclaimer** + **recipe-import personal-use note**
  belong in the same licence/terms drafting pass (self-host plan Track 1) — core ships no
  scraper, but the companion does, and the terms must push residual scraping liability to
  the operator (report §1.1).
- **Why deferred:** needs an owner decision + an Australian IP/commercial lawyer; longest
  lead-time item on the self-host track, so start it early even though it lands late.
- **Recommended resolution:** **first** step of the self-host commercialization push
  (`docs/04_proposals/SELF_HOST_COMMERCIALIZATION_PLAN.md` §6 sequence) — before building
  FU-562's key gate, since the gate is only meaningful once the licence forbids
  redistribution. Cross-ref: [[FU-562]] (billing build), [[FU-412]] (RESOLVED — the plan).

## [OPEN] FU-562 — Self-host billing: revenue model + trial delivery mechanism still open (enforcement = offline license key; platform = Lemon Squeezy MoR; tier split + after-trial=Core — all decided)
- **Raised:** 2026-07-14 (billing discussion under the self-host-first decision).
- **Type:** decision + deferred job (self-host commercialization track; the self-host counterpart to the relocated subscription FU-402).
- **The constraint (why self-host billing is different):** the app runs on the customer's machine, so payment/feature-gating **can't be technically enforced** (any binary check is bypassable; self-hosters skew technical). Design around gating the **download/update channel** (which you control), not the running app. This is also why plan-gating/usage-limits (FU-403) is SaaS-only and got parked in `docs/04_proposals/OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md`.
- **DECIDED — enforcement = offline license key.** A signed key file that unlocks the app / gates downloads+updates. Adds friction + legitimacy, bypassable by determined users but standard for paid self-host. **No phone-home activation** (breaks air-gapped self-host + contradicts the privacy posture, Charter P8).
- **OPEN DECISION 1 — revenue model:**
  - **(a) Recurring annual license** — yearly fee = ongoing updates + support; stop paying → keep your last build, lose new updates (JetBrains-style). Predictable income; self-host-friendly because you gate *updates*, not the app. *Best recurring option without runtime DRM.*
  - **(b) One-time + paid upgrades** — buy once, own that version; major versions are a new/discounted purchase (Sublime-style). Lumpier income, no subscription feel.
  - **(c) Pure one-time perpetual** — pay once, own forever, updates included. Simplest/most generous; no recurring revenue.
  - **(d) Free + donations / sponsor** — free to run, optional pay. Max goodwill, minimal/uncertain revenue.
- **DECIDED — payment platform = Lemon Squeezy** (merchant-of-record). Owner chose MoR over raw Stripe to offload global sales-tax/VAT compliance (too much burden for a solo dev), and **Lemon Squeezy** specifically (indie-friendly, simplest onboarding; now Stripe-owned, so effectively Stripe's MoR layer — tax offload without direct-Stripe tax liability). Bonus: LS issues + validates **license keys** and hosts download/update delivery, so most of the decided offline-license-key plumbing comes built-in — the build is mostly wiring the app to check an LS-minted key, not a from-scratch licensing system. Ruled out: raw Stripe (owner tax-liable everywhere + build key issuance/delivery yourself); Paddle (fine too, but LS is the simpler indie fit).
- **TRIAL / FREE-TIER SHAPE — designed 2026-07-15 (planning session with owner). The framing:**
  - **Why self-host inverts the usual SaaS §6 playbook:** (1) can't enforce at runtime → key is a speed-bump + legitimacy signal, real leverage is the update/download gate; (2) **no cost-driver to paywall** (self-hosters pay own hosting, BYO LLM key) → paywall on *value*, not cost; (3) **the "aha" IS the intelligence layer** → a permanently-dumb free tier never lets the user feel what they'd pay for, so it doesn't convert. Conclusion: "get the feel of what's possible" is best delivered by letting them feel the *full* thing time-boxed on their own pantry, not by a crippled free build.
  - **Three trial surfaces, stacked as a funnel (not either/or):** (1) **hosted demo** — the shared `DORA_DEMO_MODE` showcase + interval reset, *already built*; zero-install top-of-funnel, link from landing page. (2) **time-limited full trial** — download the real app, everything unlocked N days on your own data; the real conversion engine (magic is personal). (3) **free "Core" edition** — the useful floor the app runs at with no key / after trial.
  - **DECIDED — after-trial behaviour = fall back to a genuinely useful Core tier** (owner, 2026-07-15). App keeps working as a free pantry manager; intelligence features show a gentle hide-don't-nag (R-029) "unlock" state. No hard bricking (fits Anti-creep + self-host ethos).
  - **DECIDED — free/paid split (owner, 2026-07-15):**
    - **Free "Core" (no key, forever useful):** full pantry/stock tracking (**no item caps** — volume caps break a pantry app + feel petty on self-host), locations, recipes + paste import, cook mode, shopping lists, manual stocktake, dashboard basics, **Basic (no-LLM) assistant** (stays free — it's the default UX per the basic-mode-must-be-useful principle), import/backup/export, expiry + low-stock alerts.
    - **Paid "Full":** the whole intelligence/proactivity layer (buy-verdict oracle, zero-input pantry beliefs, suggestion inbox, budget-defense swaps, personal price intelligence, Dora Score, culinary-memory reports, advanced alerts — price-watch/digests/push, receipt/email reconciliation) **+ meal plans + AI assistant mode + native mobile app** (owner ruled all three of these ambiguous surfaces PAID, not free) **+ ongoing updates + support** (the recurring hook, and the one thing genuinely enforceable via the download gate).
  - **Enforcement mechanics (buildable shape):** one signed key (Ed25519, bundled public key), payload `{kind: trial|annual|perpetual, tier, entitlements[], issued_to, issued_at, expires_at}`, minted by Lemon Squeezy. **One server-side entitlements service = single source of truth (R-003)**; `is_enabled(feature)` reads the key, every gated surface asks it (never re-implements). SPA learns its tier via the existing `/api/auth/capabilities` probe (extend it) + a fuller authed endpoint. **Existing gating seams to route through:** the install-wide feature flags in `AdminSystemFeaturesSettings.vue` (scanning/QR, buy-verdict, product-search) + the `master_llm_enabled` kill-switch. **Two expiry semantics (the subtle bit):** *trial* key expiry → features revert to Core; *annual paid* key expiry → **app keeps every feature working forever on that build**, expiry only gates fetching new updates (matches revenue-option-(a)'s "keep your last build, lose updates"). Accept bypassability — no runtime DRM.
  - **OPEN — trial delivery mechanism (owner deferred, "decide later"):**
    - **(i) First-run grace** *(recommended)* — app self-grants N days full on first boot, no signup/key; lowest friction to the aha; reset-able by reinstall (acceptable, can't enforce anyway).
    - **(ii) Issued trial key** — user requests a time-limited key (LS / a form); captures an email, higher friction, harder to reset.
    - **(iii) Demo-only** — rely on hosted demo for "feel", downloaded app is Core until a full key is bought; simplest, weakest conversion.
    - Also still open: **trial length** (14 vs 30 days).
  - **Rough build sequence:** (1) entitlements service + signed-key verify + Settings → License page; (2) route intelligence surfaces through the gate; (3) trial mechanism per the open fork; (4) extend `/api/auth/capabilities` + SPA tier-awareness + upsell states; (5) landing-page demo link + trial/buy CTA. All net-new (Phase 4 has zero billing code today).
- **Also decide here:** that the licence + terms disclaim scraping (push it to the off-by-default companion — legal de-risk, COMMERCIALIZATION_REPORT §1–2).
- **Why deferred:** no pricing decision made yet; part of the self-host commercialization push.
- **Recommended resolution:** with [[FU-412]] (self-host commercialization plan). **Still open:** revenue model (a–d) + trial delivery mechanism (i–iii) + trial length. **Decided:** enforcement (offline key), platform (Lemon Squeezy), tier split (Core free vs Full paid), after-trial fallback (Core). Next build step once the two open forks are called: entitlements service + signed-key verify + Settings→License page, per the build sequence above. **Recommended resolution point:** at the self-host commercialization push, or sooner if you want to start charging.

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
- **Recommended resolution:** when you're ready to point people at a channel (the
  user asked for this FU explicitly so the hook-up isn't forgotten).

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

## [OPEN] FU-406 — Self-host launch readiness (on-call/SLA sliver relocated)
- **Raised:** 2026-07-01 (legacy prompt-plan audit). **Narrowed 2026-07-14 (self-host-first).**
- **Type:** deferred job (launch gate for the self-host product).
- **What:** the launch checklist for *selling self-host* — **marketing** (landing/sales page), **legal** (a self-host licence + the scraping disclaimer), a **support / incident channel** (the FU-370/557 support-channel work is the seed), and a **release process**. **The operate-the-service sliver — uptime/SLA, on-call rotation, escalation — is relocated** to `docs/04_proposals/OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md` §3 (only meaningful when you host for customers).
- **Why deferred:** last-mile, at the self-host commercialization push.
- **Recommended resolution:** at the self-host launch. **QA half already covered by [FINALISATION_PLAN.md](docs/01_charter/FINALISATION_PLAN.md)** (Track 1 FST + release-gate). Remaining: marketing, legal/licence, support-channel stand-up (FU-557), release process.

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

