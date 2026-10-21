# Implementation Plan — Alerts & Notifications Control Centre (C-9 impl)

**Status:** Plan for review · **Date:** 2026-06-15 · **No code yet** — phased plan +
reviewable chunks.
**Source proposal:** `PROPOSAL_ALERTS.md` (co-designed 2026-06-15; decisions resolved §7).
**Adjacent IMPL plans / surfaces:**
- `IMPL_PLAN_MEAL_PLANS.md` (C-2, **done**) — `no_planned_meals` reads meal-plan entries +
  `AppSetting.timezone` (C-2.K) for the household "today/next-week" boundary. The **C-2.D
  custom calendar widget** is a reuse candidate for the Upcoming timeline (R-001 — verify fit
  before forking).
- `IMPL_PLAN_CONFIG_AND_OPTINS.md` (C-cross, **done**) — `AppSetting` singleton + admin
  `PATCH` is the pattern for the new threshold fields; `useFeatureFlags` + the
  shown-disabled-until-configured idiom (R-014) is the pattern for the channel toggles.
- **Suggestions (P2-04, done)** — `DoraSuggestionSuppression` + `suggestions.py` is the
  proven `kind/dedup_key/decision/snoozed_until` + "fetch-all-and-filter-in-Python" pattern
  the interaction ledger mirrors (extended with `user_id` + `read_at`). `_current_user_id()`
  via `session.get("user_id")` is the per-user hook.
- **Shopping lists (P6-01, done)** — `ShoppingList.planned_shop_date` **already exists**; the
  `shopping_day` alert + timeline read it (no shopping-list change).
- **Price history** — `PriceAlert` (set on `PriceHistoryPage`, fired by the scrape pipeline)
  is surfaced/managed in the new subscriptions tier.
**Phase:** Master plan **Phase 1 (the loop)** for the in-app hub (Phase A below) — alerts are
the "what needs my attention" spine the dashboard + assistant both consume. The email/push
channels (Phases B/C) touch **§7.5 distribution posture** (config-driven, SMTP-gated, no new
infra) and edge into Phase-1/3 territory; the system tier + dashboard card are last.

---

## 0. Verify-state-first: no drift

Re-checked 2026-06-15 against the live code (`features/alerts/{get_alerts,act_on_alert}.py`,
`AlertsBell.vue`, `AlertsPage.vue`, `alertStore.ts`, `models/alert.ts`, `alertApiService.ts`,
`domain/entities/{notification,dora_suggestion_suppression,price_alert,shopping_list,
stock_item}.py`, `domain/stock_status.py`, `startup.py`, `features/suggestions/suggestions.py`,
`app_setting.py`, `PreferencesSettings.vue`).

**Already true (reuse / don't rebuild):**
- **6 inventory alert kinds**, computed live in `get_alerts.py`; severity-ordered; stable id
  `<stock_item_id>:<kind>`. `act_on_alert.py` parses the UUID out of the id (assumes a stock
  item — generalised in C-9.1).
- **Bell is already rich** (`AlertsBell.vue`): grouped, per-kind icons, inline actions,
  client snooze, view-in-context, bulk add low/out → primary list. **Page is read-only** with
  a "coming soon" banner (`AlertsPage.vue`). Both share `iconFor`/`colorFor`/`actionsFor` in
  `models/alert.ts`.
- **Snooze = client localStorage, per-device** (`alertStore.ts`); `notification.py` is an
  **empty stub** ("# notification / message / alert, one of these...").
- **`EXPIRING_SOON_WINDOW_DAYS = 7`** is a hardcoded domain constant (single source) in
  `stock_status.py`; consumed by the evaluator, the location heatmap, and the assistant.
- **`BackgroundScheduler` (APScheduler + `CronTrigger`) already runs** in `startup.py`
  (nightly audit sweep; a deals-email schedule is referenced). **No new scheduling infra for
  Phases B/C.**
- **`DoraSuggestionSuppression`** = `kind/dedup_key/decision(dismissed|snoozed)/snoozed_until/
  created_at`, **no `user_id`** (household-wide today). The alert ledger mirrors it **plus a
  per-user `user_id` + `read_at`** — a deliberate extension (read/snooze are inherently
  per-user, even single-household; §3.3/§4.2 of the proposal).
- **`ShoppingList.planned_shop_date` exists** (P6-01 Chunk 7). **`AppSetting`** is a singleton
  with `timezone` + feature flags + admin `PATCH`. **`User`** carries scalar pref columns incl.
  `deals_email_enabled`/`deals_email_compact` (the channel-pref pattern).

**Not built (this plan delivers it):**
- No persistence for alert read/unread, server snooze, dismiss, history, or delivery dedup.
- No per-type prefs, no tier override, no configurable thresholds.
- No single server-side "what counts" definition → the L438 count mismatch (badge=high+med,
  list=all; snooze per-device). **FU-042 open.**
- No control-centre page (summary / Upcoming timeline / manage / history); bell is the only
  rich surface.
- No `no_planned_meals`, `shopping_day`, subscriptions-tier surfacing, or system tier.
- No delivery channels beyond in-app; no email digest, no web push, no `PushSubscription`.

**Tests:** check for an existing `tests/e2e/dora_api/test_alerts*.py`; every backend chunk
adds/extends an e2e test there. Migrations verified up/down in isolation + single Alembic head
(watch concurrent-session forks, per C-2.F/G).

---

## 1. Chunked plan (each chunk = one reviewable PR)

> **Phase A (C-9.1 … C-9.6)** is the "fully polished in-app hub" — the immediate build scope.
> **Phase B (C-9.7)** email digest, **Phase C (C-9.8)** web push, **Phase D (C-9.9–.10)**
> system tier + dashboard card follow once Phase A is verified.

### C-9.1 — Spine: generalised key + per-user interaction ledger + server snooze + one count ★ FIRST CHUNK
**Closes:** L438, L439 (count half) — **resolves FU-042**. The trustworthiness spine; ships
ahead of the page.

- **Backend:**
  - **Generalise the alert key** to `<scope>:<kind>[:<discriminator>]` (`stock:<uuid>:expired`,
    etc.). Add a small parser; `act_on_alert.py` routes by scope/kind instead of blindly
    `UUID(parts[0])` (item actions still resolve `stock_item_id`; non-item scopes return
    "no action"/their own). Keep ids **stable across evaluations** (ledger rows match — same
    discipline as `dedup_key`).
  - **Fill `notification.py` → `AlertInteraction`** (rename file `alert_interaction.py`, delete
    the placeholder comment — R-008): `{user_id, alert_key, first_seen_at, read_at,
    snoozed_until, dismissed_at, created_at}`. Entity + `table_mappings` + migration (plain,
    reversible, portable; composite index on `(user_id, alert_key)`).
  - **`get_alerts.py`** joins the current user's interactions (via `_current_user_id()`,
    mirroring `suggestions.py`): filters snoozed/dismissed server-side, stamps `read`/`first_
    seen`, and returns **one canonical, derived count split into `actionable` (high+med) and
    `fyi` (low)** — the single "what counts" (proposal §3.4). Fetch-all-interactions-and-filter
    -in-Python is fine (row count is bounded), matching `suggestions.py`.
  - **New endpoints** on `ALERT_ROUTER`: `POST /alerts/<alert_key>/read` (+ `/unread`),
    `POST /alerts/<alert_key>/snooze {days}`, `POST /alerts/<alert_key>/dismiss`,
    `DELETE /alerts/<alert_key>/suppression` (unsnooze/undismiss), `POST /alerts/read-all`.
    All upsert an `AlertInteraction` for the current user.
- **Frontend:** `alertStore.ts` **drops the localStorage snooze map**; snooze/read/dismiss go
  through the API + refresh. Badge = server `actionable` count (no client recompute — R-003).
  `models/alert.ts` + `alertApiService.ts` gain the new fields/calls. The bell + page keep
  rendering; behaviour is now server-backed and consistent across devices.
- **Risk:** Medium — touches the core endpoint, the store, and the id format (ripples
  `act_on_alert`). The trap: an unstable key (e.g. embedding a humanised date) that breaks
  ledger matching.
- **Engineering close-gate:** R-003 (one server-side "what counts"; client never recomputes
  counts/snooze), R-005/R-006 (portable reversible migration), R-008 (repurpose the stub, no
  dead file), R-007 (no UI redesign yet — behaviour only). **ADR check:** the per-user-ledger-
  over-derived-conditions pattern may warrant an ADR if reused (e.g. for suggestions later).
- *Acceptance:* snoozing on one device hides the alert on another; the badge equals the
  actionable list count exactly (no silent low-exclusion surprise); read/dismiss persist; a
  dismissed alert re-appears only if its underlying condition clears and re-fires; e2e covers
  count derivation + snooze/dismiss/read upserts.

---

### C-9.2 — Per-type prefs (on/off + tier override) + configurable thresholds
**Closes:** L439 (priority half), L440, L441 (per-type half).

- **Backend:**
  - **`AlertPreference`** entity/table/migration: `{user_id, kind, enabled, tier_override}`.
    Absent row = default (enabled + default tier per proposal §5). `GET/PATCH /alerts/prefs`
    (current user).
  - **Thresholds → `AppSetting`:** `expiring_soon_window_days`,
    `default_days_until_stocktake_alert` columns + migration; surfaced via the existing admin
    `PATCH /app-settings`. **`get_alerts.py` reads the window from `AppSetting`**, not the
    constant; `EXPIRING_SOON_WINDOW_DAYS` becomes the **seeded default** (R-003 — still one
    source; the heatmap + assistant readers also point at the setting or keep the constant as
    default — verify-and-thread carefully so there's no second copy).
  - The evaluator applies the current user's prefs: a disabled kind is **omitted from that
    user's set/count/channels**; a `tier_override` moves the kind between actionable/FYI for
    the count split.
- **Frontend:** `alertPrefsStore` + service; the threshold fields on the admin settings
  surface. (The user-facing Manage **panel** ships with the page in C-9.3; the store/API land
  here so C-9.3 is pure UI.)
- **Risk:** Medium — the threshold-source threading (don't leave a second hardcoded 7).
- **Engineering close-gate:** R-003 (threshold single-source on `AppSetting`; per-user prefs
  server-applied, not client-filtered after the fact), R-005/R-006 (migrations), R-010
  (validate `kind`/`tier` against known values on write).
- *Acceptance:* disabling "low stock" removes it from that user's list/count/channels but not
  another user's; promoting "stocktake overdue" to actionable bumps the badge; changing the
  expiring-soon window to 3 days re-derives `expiring_soon` consistently everywhere (bell,
  page, heatmap); e2e covers pref filtering + tier override + threshold read.

---

### C-9.3 — The hub page + slim bell + per-kind styling + history
**Closes:** L437, L59 (build the page), L60 (summary contract), L224 (per-type styling).

- **Frontend (the big UI chunk):**
  - **Extract shared components (R-001):** `AlertRow.vue` (avatar + message + detail +
    inline actions + read/snooze) and `AlertList.vue` (grouped, tiered) consumed by **both**
    the page and the bell — kill the duplicated row markup currently copy-pasted between them.
  - **Rebuild `AlertsPage.vue`** as the hub: **Summary** boxes (per-type count + theme +
    icon), **Active list** (tiered, per-kind styling, read-state de-emphasis, mark-all-read),
    **Manage** panel (per-type on/off + tier override + thresholds, from C-9.2), **History**
    (collapsible — recently read/dismissed/snoozed from the ledger). (Upcoming timeline slots
    in at C-9.6.)
  - **Slim `AlertsBell.vue`** to a peek+jump: counts, top few unread/actionable rows (the
    shared `AlertRow`), mark-read, one in-context action, and **"Open Alerts" → the hub**.
    Bulk add-low/out stays as a peek shortcut.
  - **Per-kind visual identity** in `models/alert.ts`: a consistent icon + colour per kind
    (A1 tokens only — R-002), including the new kinds' icons.
  - **History endpoint** (backend): either a `history` section on `GET /alerts` or a small
    `GET /alerts/history` reading cleared/dismissed interactions.
- **Risk:** Medium-high — the largest UI surface; the shared-component extraction must not
  regress the bell's existing actions.
- **Engineering close-gate:** R-001 (shared `AlertRow`/`AlertList`; no duplicated markup),
  R-002 (tokens, dark-mode safe), R-003 (page/bell read the same store/canonical set), R-007
  (slim the bell, don't fork a second action system).
- *Acceptance:* the page shows summary + tiered styled list + manage + history; the bell is a
  fast peek that opens the hub; dark mode clean; no double-rendering divergence between bell
  and page; vue-tsc + eslint clean.

---

### C-9.4 — New evaluator types: `no_planned_meals` + `shopping_day` + expiry-after-alert nudge
**Closes:** L442, L403; original-spec expiry-after-alert Feature Note.

- **Backend (additive generators in the evaluator):**
  - **`meal:no_planned_meals:<iso_week>`** — emit when next week (household "today" via
    `AppSetting.timezone`, C-2.K) has no meal-plan entries. Default-on, FYI tier, tunable.
  - **`list:<uuid>:shopping_day`** — emit when a list's `planned_shop_date` is within N days
    and the list isn't `done`. Reads the **existing** field (no schema). Default-on, FYI.
  - **Expiry-after-alert nudge** — confirm the bell/row `extend_expiry`/`reset_expiry` satisfy
    the spec; if not, add a "set a new expiry" affordance on the expired row.
- **Frontend:** render the new kinds (icons + tailored actions — `no_planned_meals` → "Plan
  meals" deep-link to the planner; `shopping_day` → open the list). Defaults wired in C-9.2's
  pref seeds.
- **Risk:** Low-medium — generators are additive; the only subtlety is the household-today
  boundary for "next week."
- **Engineering close-gate:** R-003 (week/threshold logic server-side), R-001 (reuse
  `AlertRow`; per-kind action mapping in the model).
- *Acceptance:* an empty next-week plan surfaces a single no-planned-meals alert that clears
  when a meal is planned; a list with a `planned_shop_date` two days out surfaces a
  shopping-day alert that clears when done; both honour per-user on/off; e2e covers each
  generator's fire/clear.

---

### C-9.5 — Subscriptions tier (surface `PriceAlert`; design for back-in-stock)
**Closes:** L224 (central management of context-aware alerts + styling).

- **Backend:** `GET /alerts/subscriptions` listing the user's armed `PriceAlert`s (+ a
  back-in-stock placeholder shape for the companion/ingestion future); manage (delete/edit
  threshold) from the centre. Set-point creation stays on the price-history explorer.
- **Frontend:** a **Subscriptions** region on the hub — distinct *armed-thresholds* tier with
  its own icon/styling (L224), each row linking to the price-history set-point. Gated by the
  money/deals feature flags where relevant.
- **Risk:** Low-medium — mostly a read/manage surface over existing `PriceAlert`.
- **Engineering close-gate:** R-001 (reuse list components), R-007 (surface/manage only — don't
  reimplement the scrape-side firing), feature-flag gating (C-cross).
- *Acceptance:* armed price alerts appear in the centre with their own styling and a link to
  the explorer; deleting one here removes it; the tier is empty-stated cleanly when nothing is
  armed; e2e covers list + delete.

---

### C-9.6 — Upcoming "this fortnight" timeline (mini-calendar)
**Closes:** L61 (the deferred dashboard calendar, now in the hub).

- **Backend:** `GET /alerts/upcoming?days=14` — a **server-owned aggregation** (R-003)
  returning dated events: expiries (`expiry_date`), planned shopping (`planned_shop_date`),
  meal-plan days (entries per day), dated subscriptions. Grouped by date with category tags.
- **Frontend:** a **mini-calendar with coloured date-dots** per category; click a date →
  expand that day's items + planned meals (the literal L61 ask). **Reuse the C-2.D meal-plan
  calendar component if it fits** (R-001 — verify before forking); fallback shape is a
  grouped "next 14 days" list.
- **Risk:** Medium — the calendar UI + multi-source aggregation; reuse decision matters.
- **Engineering close-gate:** R-003 (aggregation server-side, client renders), R-001 (reuse the
  existing calendar widget over a new one), R-002 (token-based dot colours).
- *Acceptance:* the timeline shows the next 14 days with correct per-category dots; clicking a
  date reveals that day's expiries/shopping/meals; data matches the underlying sources; e2e
  covers the aggregation endpoint.

> **End of Phase A — the polished in-app hub. Verify in browser before Phase B.**

---

### C-9.7 — Phase B: Email digest channel (configurable cadence, SMTP-gated)
**Closes:** the email channel (proposal §3.5).

- **Backend:** `User.alerts_email_enabled` + `alerts_email_cadence` ('daily'|'weekly'|'off')
  columns + migration. A scheduled job on the **existing `BackgroundScheduler`** that, per
  opted-in user + cadence, evaluates their actionable set and emails a digest via `emailer`
  (INV-4); records delivery so the same alert isn't re-sent until it clears and re-fires
  (delivery-dedup: `last_emailed_at` on `AlertInteraction` **or** a sibling `AlertDelivery` —
  decide here, proposal §7 open-1). SMTP-gated.
- **Frontend:** channel toggle + cadence select in `PreferencesSettings.vue`, **shown-disabled
  until email is configured** (R-014, mirroring `deals_email_*`).
- **Risk:** Medium — scheduling cadence + digest templating + dedup correctness.
- **Engineering close-gate:** R-014 (shown-disabled when unconfigured), §7.5 (config/SMTP-
  gated, degrades gracefully), R-003 (digest reads the same canonical set).
- *Acceptance:* an opted-in user with SMTP configured receives a daily/weekly digest of their
  actionable alerts; the same alert isn't re-emailed until it clears; the toggle is disabled
  with a hint when SMTP is off; e2e covers digest selection + dedup.

---

### C-9.8 — Phase C: Web push (PWA)
**Closes:** the push channel (proposal §3.5); foundation for P8-10 native.

- **Backend:** `PushSubscription` table (`user_id, endpoint, p256dh, auth, created_at`) +
  subscribe/unsubscribe endpoints; VAPID keys via config (§7.5); a web-push sender; a scheduled
  evaluator that pushes **newly-fired** actionable alerts (not-present→present in the ledger),
  deduped per channel.
- **Frontend:** service worker + push-permission flow + subscription management; push toggle in
  Preferences (shown-disabled until VAPID configured).
- **Risk:** High — net-new infra (service worker, VAPID, browser permission UX). Isolate so it
  can't destabilise Phases A/B.
- **Engineering close-gate:** §7.5 (config-driven, degrades gracefully when unconfigured),
  R-014, portable.
- *Acceptance:* a subscribed device receives a push when a new actionable alert fires; no
  re-push until clear+refire; unsubscribing stops pushes; graceful when VAPID unset.

---

### C-9.9 — Phase D: System tier (offline / reconnect / serious error)
**Closes:** original-spec system-alert notes.

- A distinct **system** alert category (not inventory): client-detected connectivity
  (offline/reconnect banners feeding the centre) + a server health signal for "something
  serious went wrong." Low/FYI by default.
- **Risk:** Low-medium — mostly client connectivity + a health read; keep separate from the
  inventory evaluator.

---

### C-9.10 — Dashboard alert card (when the dashboard surface lands)
**Gated on the deferred dashboard.** Build the card to the §3.10 contract (summary boxes +
top-3 sneak-peek + "see all" + optional timeline peek) reading the same canonical set. **Not
built now** — contract only, ships with the dashboard redesign.

---

## 2. Sequencing & dependencies
1. **C-9.1** (spine) — everything else assumes the ledger + canonical count.
2. **C-9.2** (prefs + thresholds) — the evaluator's per-user filtering the page's Manage panel
   needs.
3. **C-9.3** (hub page + slim bell) — consumes 9.1/9.2.
4. **C-9.4** (new types) → **C-9.5** (subscriptions) → **C-9.6** (timeline) — additive surfaces
   on the hub; order is by independence (4 and 5 are independent; 6 may reuse C-2.D).
5. **C-9.7** (email) → **C-9.8** (push) — channels, after the hub is verified.
6. **C-9.9** (system tier), **C-9.10** (dashboard card) — last / gated.

**Hard dependencies:** C-9.4 `no_planned_meals` needs `AppSetting.timezone` (✓ C-2.K).
C-9.6 may reuse the C-2.D calendar (✓ exists — verify fit). C-9.7/8 use the existing scheduler
(✓) + `emailer`/VAPID config. **No multi-user dependency anywhere** (per-user `user_id` on the
ledger/prefs is read-state scoping, not tenancy).

## 3. Cross-cutting close-gate (every chunk)
Portable migrations (SQLite + Postgres, §7.5); A1 tokens only (R-002); shared components over
duplication (R-001); server owns derived counts/thresholds/aggregations (R-003); reversible
clean migrations, single Alembic head (R-005/R-006); scope discipline — log adjacent rough
edges as follow-ups, don't fix inline (R-007); no dead code (R-008); `CHANGELOG.md` +
`DORA_WORKLOG.md` + follow-ups updated per chunk; e2e + unit + vue-tsc + eslint green.

## 4. Feedback coverage
Inherits the proposal's **§10 table** (L437–442 + L59/L60/L61 + L224 + L403; L505/L506
out-of-scope). After Phase A verifies in-browser, flip the now-covered rows (esp. L61, L224,
L403, L437–441) in `docs/02_feedback/COVERAGE_GAPS.md` from gap → covered.
