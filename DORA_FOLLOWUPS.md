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

## [OPEN] FU-675 — mobile dropdown behaviour: no shared select wrapper to apply a rule through
- **Raised:** 2026-08-19 (cookbook feedback batch — owner asked for an assessment)
- **Type:** finding / deferred job
- **What:** the app has **72 `q-select`s and none set `behavior`**, so every one
  inherits Quasar's default — an anchored menu on desktop, a **full-screen
  dialog on mobile** — while the three `BaseDropdown` consumers (the tri-state
  filters) are always menus. That's the inconsistency the owner reported, and
  it is entirely accidental rather than chosen. The recommendation (below, and
  in the worklog entry for 2026-08-19) is a rule keyed on option count, not a
  blanket flip either way — but there is **no shared select wrapper** to apply
  it through, so it currently means touching 72 call sites.
- **Recommended shape:** add `BaseSelect.vue` (the `SearchInput` / `SortControl`
  pattern from this same batch), give it `behavior="menu"` for short closed
  vocabularies and a **constrained** dialog (max-height ~70vh + max-width, so
  the backdrop stays tappable) with an explicit close affordance for long or
  `use-input` lists — 13 selects use typeahead today. The owner's actual
  complaint ("difficult to tap out of") is a *dismissal* defect: with a long
  list the dialog fills the viewport and leaves no backdrop to tap, and there's
  no visible Done. That is fixable without changing which surface style is used.
- **Why deferred:** it's an app-wide control refactor, well outside a cookbook
  polish batch, and it wants its own verify pass on a real phone (the desktop
  preview can't show the failure mode).
- **Recommended resolution:** later, as its own unit — pairs naturally with the
  next mobile-UX pass.
- **Update 2026-08-19** (cookbook feedback batch 2): the *"no shared wrapper"*
  half is now partly false — `components/filters/BaseFilterField.vue` exists and
  the three tri-state filters route through it, so a rule could be applied there
  in one place. But that wrapper hosts a **custom panel**, not an options list:
  the **72 `q-select`s still have no wrapper**, and nothing about the mobile
  `behavior` question (menu vs constrained dialog, and the dismissal defect) has
  been decided or changed. This FU stays open for exactly that.

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

## [OPEN] FU-651 — Stray editor temp file committed-adjacent in `web_app/src/pages/`
- **Raised:** 2026-08-16 (stock-overview filter feedback).
- **Type:** leftover.
- **What:** `web_app/src/pages/StockItemDetailPage.vue.tmp.1272799.ae577f7b1f87` (138KB,
  untracked, dated 2026-08-16 16:56) is sitting next to the real page — an editor/agent
  temp file from the previous unit that never got cleaned up. It is not imported, but it
  IS inside the SPA source tree.
- **Why deferred:** not mine to delete unreviewed — it may be a copy the owner kept
  deliberately, and it's 138KB of page source, not scratch.
- **Recommended resolution:** now — confirm it's junk and `rm` it (it's untracked, so
  nothing is lost from git either way).

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

## [OPEN] FU-649 — Buy-verdict quick filter on Stock Overview needs a bulk verdicts endpoint
- **Raised:** 2026-08-16 (stock-overview filter feedback — owner deferred).
- **Type:** deferred job.
- **What:** the owner asked whether a quick filter for buy-verdict rows is worth adding.
  It can't be built client-side: `useBuyVerdict` fetches **one verdict per item, lazily,
  as each row mounts**, so the page only knows verdicts for rows already rendered —
  filtering on that would silently miss everything below the fold. The honest version is
  a bulk `GET /api/stock-items/buy-verdicts` (id + verdict + confidence for the pantry,
  computed with batched queries rather than looping `_gather_inputs`), which would drive
  the filter *and* pre-warm the row badges — killing the current one-request-per-row
  pattern at the same time.
- **Why deferred:** owner said "skip this for now" when asked (the other four items in
  the batch were pure UI).
- **Recommended resolution:** when the buy-verdict surface is next opened — pair it with
  the N-request cleanup, since they're the same endpoint.

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
  3. **Dashboard / reports stranded half-width cards (#30).** A lone `col-lg-6` card
     at the end of a zone sits beside dead air (D-011). The dashboard uses a CSS
     `order`-based zone system, so "make a lone last-in-zone card full-width" needs
     per-zone odd-count logic (the page already computes `zoneHasVisibleCards`), not
     a pure-CSS rule — hence its own unit.
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

