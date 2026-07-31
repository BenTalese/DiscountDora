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

## [OPEN] FU-607 — Stock-item image editing appears gone; `ImageUploadField` docstring still cites it as a consumer
- **Raised:** 2026-07-24 (DORA_VERIFY R-024 image-source-picker sweep)
- **Type:** finding (code/doc drift; possible dropped feature)
- **What:** `ImageUploadField.vue`'s docstring says it was "generalised when the stock-item detail surface adopted it (FU-126 / R-001 second-consumer threshold)", but `StockItemDetailPage.vue` has **no image-upload field** now (grep for `ImageUploadField`/`ImageSourcePicker`/`q-file`/image on that page returns nothing). The only image-upload consumers are recipe hero + avatar (via `ImageUploadField`), recipe step images + store logo + shopping-list receipts (direct `ImageSourcePicker`). Stock items still *display* an image (`stockItemStore.imageVersionOf`, `StockItemRow`), but there's no way to set one in the SPA.
- **Why deferred:** not a user-facing crash; may be an intentional removal (stock items show the linked product's image rather than a user upload). But a docstring naming a consumer that no longer exists is exactly the drift the single-maintainer-legibility goal cares about.
- **Recommended resolution:** opportunistic — confirm whether stock-item image editing is meant to exist. If yes, it regressed (re-wire `ImageUploadField` on the detail page); if no, drop the stale FU-126 clause from the `ImageUploadField` docstring + the "stock item" mention in `imageService.ts`.

## [OPEN] FU-599 — Endpoints with an explicit `audit_emit` also get an auto-audit row, so security-relevant actions are logged twice under two different names
- **Raised:** 2026-07-22 (lean-verify big round #4 — Batch 13, FU-197 audit check)
- **Type:** finding (audit integrity)
- **What:** `auto_audit_after_request` (`dora_api/infrastructure/audit.py:222-255`)
  writes one row per successful mutating `/api/*` request, named after the
  endpoint function. Handlers that *also* call `audit_emit` therefore produce
  **two rows for one operation**. `_NO_AUDIT_ENDPOINTS` exists precisely to
  suppress the generic row in that case — but it only lists `login` and `logout`
  (plus `submit_client_log` / `health_check`).
- **Observed live:** one email-change request produced both
  `request_email_change` (generic, bare endpoint name) **and**
  `auth.email_change.requested` (explicit, dotted domain name) in
  `/api/audit/events`. Confirmed against a full dump of 31 events: it is the only
  action present under both conventions, because it's the only explicitly-audited
  endpoint I exercised.
- **Not a one-off — it's every explicit emitter that isn't on the list.** Grep
  shows `audit_emit` in `register_user`, `change_password`, `bootstrap_admin`,
  `create_user_as_admin`, `delete_user_as_admin`, and five more paths in
  `email_flows.py`. None are in `_NO_AUDIT_ENDPOINTS`, so each will double-log
  when driven. These are exactly the account-security actions an operator reads
  the audit log to review.
- **Why deferred (and why I didn't just add names to the frozenset):** the fix
  direction is obvious, but the risk is asymmetric — suppressing the generic row
  for an endpoint whose explicit emit carries *less* information (entity id,
  payload, actor) silently **loses** audit coverage, which is worse than a
  duplicate. Each endpoint needs its explicit emit checked against what the
  generic row provides before it's added. For `request_email_change` specifically
  the explicit emit is strictly richer (actor + entity + `new_email` payload), so
  that one is safe to suppress today.
- **Worth deciding alongside:** the log currently mixes two naming conventions —
  dotted domain names (`auth.login.success`, `meal_plan.created`) and bare
  endpoint names (`snooze_alert`, `finish_shopping_list`). Picking one would make
  the log readable as a whole rather than per-row.
- **Recommended resolution:** opportunistic, but **before any audit-log UI work**
  — a duplicated, dual-convention feed will look like a rendering bug to whoever
  builds that surface next.

## [OPEN] FU-598 — `--brand-primary` and `--semantic-positive` are the same colour in Pesto (the default theme), so any primary-vs-positive coding is undecodable
- **Raised:** 2026-07-22 (lean-verify big round #3 — Batch 11, C-9.6 Upcoming timeline)
- **Type:** finding (design / theming)
- **What:** measured the two tokens across all five themes (dark variants):

  | Theme | `--brand-primary` | `--semantic-positive` | distinguishable? |
  |---|---|---|---|
  | **Pesto (default)** | `#359766` | `#359766` | **identical** |
  | Lemon Tart | `#ffc400` | `#62bb44` | yes |
  | Blueberry | `#93b5be` | `#66cc99` | yes |
  | **Cherry Cola** | `#a6e085` | `#89d65c` | **near-identical** (two pale greens) |
  | Sourdough | `#eba147` | `#61d186` | yes |

  So in 2 of 5 themes — including the **default** — a surface that distinguishes
  two meanings by primary-vs-positive alone conveys nothing.
- **Concrete instance found:** the Alerts hub's **Upcoming fortnight timeline**
  (`UpcomingTimeline.vue:295-303`) colours its per-category dots
  `expiry → --semantic-warning`, `shopping → --brand-primary`,
  `meal → --semantic-positive`. The component is doing the *right* thing — three
  distinct tokens — but on Pesto the shopping and meal dots render as the same
  `rgb(53,151,102)`, so a day with a shop and a day with a meal look identical.
  The legend above the grid (D-013 is satisfied — a legend exists) doesn't
  rescue it, because the legend's own swatches are those same two colours.
- **Scope:** I only walked the timeline, but this is a *token-level* collision,
  so any other surface that pairs primary with positive is affected. Worth a grep
  for `--semantic-positive` alongside `--brand-primary` in the same component.
- **Why deferred:** the fix is a palette decision (nudge Pesto's positive off the
  brand green? give the timeline a dedicated categorical ramp rather than reusing
  brand/semantic roles? add a second channel — shape or glyph — so colour isn't
  load-bearing, which is also the more accessible answer). All three are the
  owner's call, and the last one is arguably what D-013's spirit wants.
- **Recommended resolution:** opportunistic — fold into the next design pass, or
  into the `DESIGN_REMEDIATION_PLAN` backlog. Cite alongside D-013 (colour-coded
  states get a legend) — the deeper rule this suggests is "colour alone is never
  the only channel", which may deserve its own D-rule.

## [OPEN] FU-593 — `reconcile_meals_pending` is invisible on a busy pantry: severity `low` + the hard 8-suggestion cap
- **Raised:** 2026-07-22 (lean-verify big round — Batch 7 Meal plans, reconcile walk)
- **Type:** finding
- **What:** `/api/suggestions` sorts by severity DESC then title and truncates at
  `_MAX_SUGGESTIONS = 8` (`dora_api/features/suggestions/suggestions.py:42,120-135`).
  `generate_reconcile_meals_pending` emits `SEVERITY_LOW`, so on the seeded verify
  DB it was crowded out entirely by 8 `use_soon` (high) cards — the suggestion
  never reached the SPA even though its signal was firing. Confirmed by pushing
  the expiring stock dates out: the reconcile card then appeared immediately with
  the right payload (`unresolved_count: 3`, `oldest_days_back: 5`). The
  **`meal_reconcile_overdue` alert is unaffected** and did surface, so the nudge
  isn't lost outright — but the suggestions surface silently drops it exactly
  when the kitchen is busiest, which is when reconciling matters most.
- **Why deferred:** the fix is a product judgement (raise the severity? reserve a
  slot per kind? de-duplicate `use_soon` so one noisy category can't fill the
  feed?), not an obvious defect — the cap is working as written.
- **Recommended resolution:** opportunistic — fold into the next suggestions /
  dashboard-feed pass.

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

