# Dora Follow-ups Ledger

Stateful backlog of **follow-ups, deferred jobs, leftovers, and findings**
surfaced while running prompts — the stuff that's easy for the user to miss in a
long session summary. Distinct from the other two logs:

- `CHANGELOG.md` = product/code changes that shipped.
- `DORA_WORKLOG.md` = per-session handoff narrative.
- `DORA_FOLLOWUPS.md` (this file) = **open loops** that outlive a single session,
  each with a tracked state so every session knows what's still pending.

## How to use this file

- **On session start:** scan for `[OPEN]` items. Surface the ones whose
  *recommended resolution point* is "now" or matches the work about to start, and
  **ask the user** whether they want to review/resolve them now or defer.
- **On ending a work unit:** add any new follow-ups/leftovers/findings you
  generated. Mark items you actually resolved as `[RESOLVED]` (don't delete them —
  the trail matters), with a one-line note on how.
- Keep the newest items near the top of the Open section.

## Entry template

```
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

## [OPEN] FU-018 — B7: wider sweep for "store mutation + page toast" double-emits
- **Raised:** 2026-06-05 (Wave-B self-audit)
- **Type:** finding
- **What:** B7's "no other double-toast patterns" verdict only walked
  `useShoppingListActions.addItems` callers. Same pattern could exist
  for any store mutation that toasts internally and a page handler that
  toasts on success after. Worth grepping for `$q.notify` and
  `notifyOk` calls inside store/composable methods, then cross-checking
  every caller for a follow-up notify.
- **Why deferred:** out of B7's original scope; opportunistic cleanup.
- **Recommended resolution:** opportunistic — fold into the next polish
  pass.

## [OPEN] FU-017 — B3: user re-test "can't save unless I change the name"
- **Raised:** 2026-06-05 (Wave-B self-audit)
- **Type:** open verification
- **What:** Static read says every update handler already does the right
  thing (`model_fields_set` + exclude-self on the name-uniqueness check).
  No code changed this session for B3. But the user originally reported
  the symptom in browser testing, and the Wave-B self-audit found two
  other "looked fine on paper, broken in browser" cases — so this might
  also reproduce despite the static evidence.
  - To re-test: edit a stock item, change only e.g. `expiry_date`, save.
    Then edit a recipe, change only `servings`, save. Both should
    succeed without a "name already exists" 422.
  - If it reproduces, capture the request payload + response body and
    share — that will tell us whether (a) wrong endpoint is being hit
    (e.g. the create-new path), (b) the frontend is sending a
    different `name` value than displayed, or (c) something else.
- **Why deferred:** can't reproduce statically; cheaper to wait for a
  live error than keep tracing speculative paths.
- **Recommended resolution:** when the user gets a browser session up
  next — try the test above; report back.

## [OPEN] FU-016 — Audit other "frontend cache vs backend mutation" guard races
- **Raised:** 2026-06-05 (B5 follow-up)
- **Type:** finding
- **What:** The onboarding "dead button" bug was a stale `authStore.currentUser`
  read by the router guard after `onboardingApi.completeAsync()` updated the
  backend. The same shape could exist for any flow where the backend mutates
  user-scoped state that a guard or computed reads from a frontend cache —
  candidates worth scanning: account changes (email/role/admin flag), data
  import/restore, restart-onboarding, and stock-item Undo restore. Look for
  `currentUser?.*` reads in router and layout guards, and pair each with the
  store mutation that should refresh them.
- **Why deferred:** out of B5's bug-fix scope; cross-cutting audit.
- **Recommended resolution:** opportunistic — fold into a Wave-A or polish
  pass once one obvious symptom shows up; not worth a dedicated session.

## [OPEN] FU-015 — B5: Onboarding tour "Alerts" card points at stock, not /alerts
- **Raised:** 2026-06-05 (B5)
- **Type:** finding
- **What:** `WelcomeWizard.vue` `TOUR_CARDS` "Alerts — Dora pings you" still
  routes to `/stock?attention=true` (its description even says "deep-link
  into Stock"). Now that `/alerts` exists as a real page, the tour card
  could go there instead — or keep both as different teaching moments
  (Stock + filter vs the dedicated list).
- **Why deferred:** out of B5's bug-fix scope; user-style decision.
- **Recommended resolution:** opportunistic, or fold into the C-wave
  alerts control centre brief.

## [OPEN] FU-014 — B1: confirm `image` field round-trips for product create
- **Raised:** 2026-06-05 (B1)
- **Type:** finding
- **What:** `CreateProductRequest.image` is typed `Base64Bytes | None` but the
  frontend ships `offer.image` as a string (likely a raw URL or a `data:` URL).
  B1 didn't change this — pre-existing — but the offer-spread fix in
  `ensureSaved` now sends `image` explicitly, so it'll exercise the parse path
  every save. If creates 422 on `image`, switch the request model to
  `str | None` (a URL, not bytes) or make the frontend omit the field.
- **Why deferred:** out of B1's scope (B1 was field-list mismatches, not type
  mismatches); no node_modules so couldn't test live.
- **Recommended resolution:** opportunistic — first time the user actually
  saves a scraped product in browser, watch for a 422 on `image`.

## [OPEN] FU-013 — A4 leftover: "consistent multi-select control" only partial
- **Raised:** 2026-06-05 (A4)
- **Type:** leftover
- **What:** A4 standardised the filter-bar shell (panel/search/active-count/clear)
  but did NOT build a dedicated shared multi-select control. Multi-selects remain
  page-specific: `RecipesOverview` uses `q-select multiple use-chips`,
  `ProductSearch` merchant picker + `StockOverview` levels are bespoke chip UIs.
- **Why deferred:** the bespoke chip pickers carry extra behaviour (health
  icons, level colours, counts) that a generic control would lose; forcing one
  control would be a regression. The shell was the high-value standardisation.
- **Recommended resolution:** opportunistic — only if a future page needs a plain
  multi-select; otherwise leave the bespoke ones. Not no-regret.

## [OPEN] FU-012 — FilterBar panel has no visual container
- **Raised:** 2026-06-05 (A4)
- **Type:** finding
- **What:** `FilterBar`'s collapsible panel is a plain div. `ProductSearch`
  previously wrapped its filters in a bordered `q-card`; that border is now gone
  (so all four pages match the borderless inline style the others always used).
- **Why deferred:** consistency was the goal; the other 3 pages never had a card.
  Whether the panel wants subtle containment (border/elevation) is a design call.
- **Recommended resolution:** fold into the FU-010 holistic look review, or a
  quick tweak to `FilterBar.vue` if the panel reads as too bare in the browser.

## [OPEN] FU-011 — AuditLogSettings filtering not standardised
- **Raised:** 2026-06-05 (A4)
- **Type:** finding
- **What:** `settings/AuditLogSettings.vue` has ~9 filter fields with its own
  apply/clear UX. A4 deliberately did not touch it (the prompt scoped A4 to the
  four data-list pages and excluded the deferred/settings pages); its filtering
  is also server-side (sends a query), not the client-predicate pattern FilterBar
  assumes.
- **Why deferred:** out of A4's defined scope; different (server-side) mechanism.
- **Recommended resolution:** later — only if settings/admin gets a dedicated
  polish pass; low priority.

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
- **Also feed in:** other light themes' `--text-muted` contrast nudge ([[FU-003]]),
  and the structural dual-source collapse ([[FU-004]]) so the review isn't fighting
  a moving target.
- **Why deferred:** look-and-feel polish is best judged late, in one sitting, on a
  near-final app — not litigated token-by-token mid-build.
- **Recommended resolution:** later — a dedicated pass during **Phase 3 (champion
  polish)** or just before **Phase 4 (commercialize)**, once the app is feature-
  complete enough to eyeball holistically. Requires the app actually running
  (deps installed) and ideally a side-by-side across all themes.

## [OPEN] FU-009 — Decide fate of the 3 specialised overlays vs BaseDialog
- **Raised:** 2026-06-05 (A3)
- **Type:** finding
- **What:** `AlertsBell` (seamless drawer), `CommandPalette` (search overlay), and
  `ScanOverlay` (persistent camera) were intentionally left on raw `q-dialog` —
  they aren't standard card modals.
- **Why deferred:** folding them into BaseDialog adds no value and risks their
  custom layout/positioning.
- **Recommended resolution:** now (quick yes/no from user) — otherwise leave as the
  documented permanent exception.

## [OPEN] FU-008 — Unify dialog chrome via BaseDialog `title`/`#actions` slots
- **Raised:** 2026-06-05 (A3)
- **Type:** deferred job
- **What:** A3 migrated dialogs as a shell transform; each still carries its own
  header/footer markup. BaseDialog already exposes `title`/`closable`/`#actions`
  to standardise chrome.
- **Why deferred:** rewriting ~28 heterogeneous dialogs' internals is large and
  risky for a cosmetic-consistency gain.
- **Recommended resolution:** opportunistic — convert a dialog's chrome whenever
  it's being touched for another reason; no dedicated pass needed.

## [OPEN] FU-007 — Eyeball A3 modals in a real browser
- **Raised:** 2026-06-05 (A3)
- **Type:** leftover
- **What:** A3 was verified statically only — `node_modules` isn't installed in
  this checkout, so no lint / `quasar build` / dev-server run happened. Need to
  confirm backdrop+Esc dismiss without committing, and that the comparison /
  orphans / quick-add cards (scoped-class → `card-style` fix) still size right.
- **Why deferred:** can't run the app without installing deps.
- **Recommended resolution:** now-ish — once deps are installed / before signing
  off Wave A.

## [OPEN] FU-006 — Migrate the remaining ~289 `q-btn` to BaseButton
- **Raised:** 2026-06-04 (A2 Phase 2); rescoped 2026-06-05
- **Type:** deferred job
- **What:** A2 took the app from 399 → ~304 `q-btn`; it currently sits at **~289
  plain `q-btn`** (+ 4 `q-btn-dropdown`, 6 `q-btn-toggle`) across ~40 files. This
  is **NOT part of the standard plan** — A2's prompt was scoped to *toolbar*
  buttons + "New X" placement only, and no other prompt covers the rest. So the
  remainder is a genuine unplanned leftover, captured here on purpose.
- **Breakdown / nuance (don't treat as one uniform job):**
  - **Inline list-row action buttons** — the bulk (recipe cards, stock rows,
    shopping-list lines, settings rows). Low visual impact, the main target.
  - **Products surface** (`MyProductsPage` ~20, `ProductSearch` ~18) — **skip
    these**: that surface is moving to the companion app (master Decision 1), so
    it's intentionally minimal-touch. Migrating them is likely wasted effort.
  - **`q-btn` in `q-input` append slots** (search-clear, copy-to-clipboard) —
    intentionally the minimal pop-out style; leave as-is.
  - **`q-btn-dropdown` / `q-btn-toggle`** — different APIs, out of BaseButton
    scope by design (see FU-005).
  - **`DoraChat` (~14)** — its own component; migrate only if DoraChat is being
    reworked anyway.
- **Why deferred:** out of A2's defined scope; high count, mostly low-impact, and
  a chunk of it (products) shouldn't be migrated at all.
- **Recommended resolution:** later — a dedicated low-priority pass *after* Wave A,
  explicitly excluding the products surface, q-input append buttons, and the
  dropdown/toggle variants. Or purely opportunistic (migrate a page's inline
  buttons whenever that page is open for other work). Not no-regret; not urgent.

## [OPEN] FU-005 — `q-btn-dropdown` / split-button wrapper component
- **Raised:** 2026-06-04 (A2)
- **Type:** deferred job
- **What:** 4 `q-btn-dropdown` + 6 `q-btn-toggle` usages are out of BaseButton's
  scope (different APIs). A wrapper would unify split-buttons if there's appetite.
- **Why deferred:** different component API; not needed for A2.
- **Recommended resolution:** later — only if a design need arises; not no-regret.

## [OPEN] FU-004 — Collapse `themeService.ts` THEMES dict into CSS-var reads
- **Raised:** 2026-06-04 (A1b)
- **Type:** finding
- **What:** 7 themes still have the dual-source coupling between the `THEMES`
  palette dict in `themeService.ts` and `themes.scss`. Their values currently
  match (Pesto / Pesto Dark / Lemon Tart Dark were synced), but it's a latent
  drift hazard.
- **Why deferred:** values match today, so it doesn't block anything.
- **Recommended resolution:** later — a clean-up before commercialise (Phase 4),
  or when a theme bug points back to the dual source.

## [OPEN] FU-003 — Other light themes' `--text-muted` contrast nudge
- **Raised:** 2026-06-04 (A1b)
- **Type:** follow-up
- **What:** only the Pesto family got the `--text-muted` 50→42 lightness bump.
  Other light themes (Lemon Tart, Blueberry, Cherry Cola light, Sourdough light)
  may want the same for AA contrast.
- **Why deferred:** wanted to eyeball Pesto first before touching the whole family.
- **Recommended resolution:** later during a dedicated A1b contrast pass, after the
  user has eyeballed the themes.

## [OPEN] FU-002 — LoginPage `--lp-*` token ladder revisit
- **Raised:** 2026-06-04 (A1)
- **Type:** deferred job
- **What:** `LoginPage.vue`'s private `--lp-*` colour ladder was deliberately left
  untouched (DEC-2 — intentional splash).
- **Why deferred:** it's a one-off intentional design, not theme drift.
- **Recommended resolution:** later during **C19** (shared auth-shell) — revisit
  the whole auth surface together.

---

# Resolved

## [RESOLVED] FU-001 — "Flat danger" BaseButton variant for low-emphasis deletes
- **Raised:** 2026-06-04 (A2 Phase 2)
- **Type:** follow-up
- **What:** A2 left flat-negative delete buttons as raw `q-btn` because BaseButton
  had no flat-danger shape.
- **Why deferred:** needed a new BaseButton variant.
- **State note:** RESOLVED 2026-06-05 — `danger-ghost` variant added
  (`{ flat: true, color: 'negative' }`) and wired into `StockItemDetailPage`
  (Delete + clear-expiry) and `MealPlansOverview` (Delete plan).
