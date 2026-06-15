# Proposal — Alerts & Notifications Control Centre (C-9)

**Status:** Co-designed draft (supersedes the 2026-06-06 draft) · **Date:** 2026-06-15 · Changes NO code.
**Scope:** Turn Alerts from "a live list of what's wrong now" into a **trustworthy, tunable,
forward-looking notifications platform**: a real control-centre **page** (summary + an
**Upcoming "this fortnight" timeline** + grouped list + management + history), a single
"what counts" model that fixes the bell-count mismatch, **per-user** opt-in/out per type,
a small **persistent per-user interaction ledger** (read/unread + server-side snooze +
dismiss + delivery dedup) layered over the existing **live evaluator**, **phased delivery
channels** (in-app → email digest → web push), new alert types (no-planned-meals,
shopping-day, a subscriptions tier for price / back-in-stock, and a system tier), and a
slimmed bell. Defines the (deferred) dashboard alert-card contract.

> **Charter tie-break:** Effortless (P1) + Anti-creep (P10). "Dora is as quiet or noisy as
> they want" (L441). The control centre's job is to make alerts *trustworthy* (the count
> means something), *tunable* (turn off / re-prioritise what you don't care about, choose
> how you're told), and *forward-looking* (see what's coming, not just what already broke)
> — **not** to add noise. Every new capability is opt-in or default-quiet.

> **Co-design note (2026-06-15):** This draft replaces the original. Direction set with the
> user across four question rounds. Headline changes from the first draft: (a) a deliberate
> **derived-conditions + persistent-interaction-ledger** data model (not a naive stored-
> notification table, which would go stale); (b) **multi-user / "notify another user"
> (L505) dropped entirely** — shared-household means everyone already sees the same alerts,
> so there is no recipient routing and not even a seam (YAGNI, and the §7.5 distribution
> posture forbids speculative multi-tenancy); (c) **delivery channels phased** in-app →
> email → push; (d) the deferred **"this fortnight" calendar (L61) pulled into the hub** as
> an Upcoming timeline; (e) per-type control is **per-user**.

---

## 1. Current state (from live code, 2026-06-15)

- **6 inventory alert kinds**, computed on-the-fly per request
  (`features/alerts/get_alerts.py`): `expired` (high), `expiring_soon` (med, window
  hardcoded 7d via `EXPIRING_SOON_WINDOW_DAYS`), `out_of_stock` (med), `low_stock` (low),
  `essential_low` (high — flagged items, covers both essential-low and essential-out),
  `stocktake_overdue` (low). Severity = high/med/low; ordered severity-then-name. All
  signals derive from existing `StockItem` columns — **no alert tables today.**
- **Stable alert id** = `<stock_item_id>:<kind>` (`AlertDto.alert_id`). `act_on_alert.py`
  parses the UUID out of it and routes by action — so the id format currently *assumes every
  alert is tied to a stock item* (this breaks for no-planned-meals / shopping-day / system,
  see §4.1).
- **Bell** (`AlertsBell.vue`) — already rich: badge + right-drawer, grouped by severity,
  per-kind icons, inline actions (push/clear expiry, mark restocked, acknowledge stocktake),
  snooze 7d, "view in context" (deep-links to Stock `attention` filter), and a bulk
  "add all low/out to primary list." Polls every 60 s.
- **Page** (`AlertsPage.vue`) — a **read-only grouped list** with a "full control centre is
  on the way" banner that tells users actions live on the bell. Click a row → stock item.
  No summary, no management, no per-kind styling, no actions. This is the surface we build
  into the hub. (The old L59 "Alerts → 404" is fixed; **confirm in browser** — FU.)
- **No per-type preferences**; thresholds **hardcoded**. Only per-item
  `stocktake_alerts_are_enabled` + `days_until_stocktake_alert` exist on `StockItem`.
- **Price alerts are a separate island** (`PriceAlert`, set on `PriceHistoryPage`, fired by
  the scrape pipeline) — not surfaced in the bell or alerts page.
- **Snooze is client-side `localStorage`, per-device** (`alertStore.ts`). The
  `notification.py` entity is an **empty stub** (`# notification / message / alert, one of
  these...`).
- **Infra already present (de-risks the later phases):** a `BackgroundScheduler`
  (APScheduler + `CronTrigger`) runs in `startup.py` (nightly audit sweep; a deals-email
  schedule is referenced) — the **email-digest and push evaluators hang off this, no new
  scheduling infra needed**. `DoraSuggestionSuppression` (`kind`/`dedup_key`/`decision`/
  `snoozed_until`/`created_at`) is the **proven pattern** the interaction ledger mirrors.
  `emailer` infra (INV-4) + `deals_email_enabled`/`deals_email_compact` on `User` are the
  pattern the email channel reuses.

### 1.1 The count mismatch (L438) — root cause confirmed
The badge and the list disagree on **two** axes:
- **Severity:** badge = `high_count + medium_count` (`alertStore.ts:99`) — **excludes low**;
  the list **shows all severities**. The "I see 6 [badge], the bell shows 10 [list]" gap is
  the 4 low-severity alerts the badge omits.
- **Snooze:** the list filters client-snoozed alerts; the badge is recomputed from the
  *filtered* set client-side, but because snooze is **per-device** localStorage the number is
  inconsistent across devices and invisible to the server / any future channel.

Both stem from there being **no single server-side definition of "what counts."** Fixing
this is the spine of the redesign (§3.4) and is now gated by the interaction ledger (§4),
because a trustworthy count must respect server-side snooze/dismiss and per-user opt-outs.

---

## 2. The model in one picture

```
            ┌────────────────────────────────────────────┐
   request →│  LIVE EVALUATOR  (source of truth)          │  what is true NOW + what's
            │  inventory kinds + meal/shopping/system     │  coming (Upcoming timeline)
            │  + surfaced subscriptions; thresholds from  │
            │  AppSetting; ordered, keyed by alert_key    │
            └───────────────┬────────────────────────────┘
                            │  every live alert carries a stable alert_key
                            ▼
            ┌────────────────────────────────────────────┐
   per-user │  INTERACTION LEDGER  (persisted, per user)  │  read/unread · snooze ·
   filter & │  fill notification.py → AlertInteraction    │  dismiss · first_seen ·
   decisions│  + per-type prefs (on/off, tier override)   │  (phase 2/3) delivery dedup
            └───────────────┬────────────────────────────┘
                            ▼
       ┌───────────────┬───────────────┬──────────────────┐
       │  IN-APP       │  EMAIL digest  │  WEB PUSH (PWA)  │  ← per-user channel prefs
       │  bell + hub   │  (phase 2)     │  (phase 3)       │     (global across types)
       └───────────────┴───────────────┴──────────────────┘
```

**Why this shape (the key design insight):** most alerts are **live conditions** (expired,
low-stock), not one-time events — storing them as rows goes stale the moment you restock. So
the evaluator stays the truth, and the ledger stores only **per-user events and decisions**
keyed by the stable `alert_key`: when you first saw it, whether you've read it, whether it's
snoozed/dismissed, and (phases 2/3) whether we've already emailed/pushed it. That delivers
history, read-state, server-side snooze, and dedup **without** a stale-row reconciliation
problem.

---

## 3. The redesign

### 3.1 The Alerts hub page (L437, L59, L60, L224)
Rebuild `AlertsPage.vue` as the control centre. Four regions, top to bottom:

1. **Summary** — a row of per-type boxes (count + plain-language theme: "5 expiring soon",
   "3 essential low", "2 expired"), each with the type's icon/colour. At-a-glance "what's
   going on." This is also the **contract the deferred dashboard card mirrors** (§3.10).
2. **Upcoming timeline** (§3.7) — the forward-looking "this fortnight" view (L61).
3. **Active list** — grouped by tier, **per-kind icons & styling** (extend the existing
   `iconFor(kind)`/`colorFor`), each row with its inline actions (the ones that live on the
   bell today move here as the primary home), read/unread affordance, and snooze. Read items
   visually de-emphasised; a "mark all read" control.
4. **Manage** — per-type on/off + tier (§3.3) and configurable thresholds (§3.3) hosted
   here (Settings is deferred). A link out to the user's channel preferences (§3.5).
5. **History** (collapsible) — recently-cleared / dismissed / snoozed items from the ledger
   (the audit trail the persistence unlocks). Answers "what *was* alerting me?"

### 3.2 The bell becomes a slim peek (Bell-vs-page decision)
The page is the hub; the bell is the **fast peek + jump**: counts, the top few unread/
actionable items, "mark read," and **"Open Alerts"** → the hub. Keep the single most useful
in-context action (mark-restocked / push-expiry) on a peek row, but the rich management,
history, timeline, and bulk operations live on the page. This avoids two competing rich
surfaces and the R-003 duplication risk (shared rendering + the store stay the single source).

### 3.3 Per-type prefs + configurable thresholds (L439, L440, L441) — **per-user**
A management panel on the hub:
- **Enable/disable each alert kind** — **per-user** (honours "as quiet or noisy as *they*
  want", L441). The evaluator computes shared household truth; each user's prefs filter
  *their* in-app view and *their* channel deliveries. A disabled type contributes nothing to
  that user's count, list, or channels.
- **Optional per-type tier override** — defaults are sensible (§5); an advanced control lets
  a user move a kind between tiers (e.g. treat "low stock" as FYI, or promote "stocktake
  overdue" to actionable). This is the concrete "smarter priority / what's actually an alert"
  ask (L439). *Dial-back point:* if this proves like over-engineering, ship on/off-only first
  and add tier override later — the data model supports both.
- **Configurable thresholds (household-wide, server-owned — R-003):** expiring-soon window
  (N days) and a default stocktake timeframe move onto `AppSetting` (like `timezone`). The
  evaluator reads them from `AppSetting`; the current `EXPIRING_SOON_WINDOW_DAYS` constant
  becomes the seeded default. These are **domain thresholds** (they shape the shared derived
  set + the location heatmap + the assistant), so they're household config, not per-user
  noise prefs — and they live in **one** place server-side, never copied to the client.

### 3.4 One "what counts" definition (L438, L439) — fixes the bell
Define a **single canonical, server-derived count** used by the badge, bell peek, page, and
(later) channels alike:
- The count is computed from the **per-user-filtered, unsnoozed, undismissed, enabled** set
  — derived server-side from the evaluator + ledger + that user's prefs, *not* recomputed in
  four places.
- **Badge == count of its tier.** The badge counts the user's **actionable** tier
  (high+medium by default); the **low/FYI** tier is shown in the list but never inflates the
  badge — **no silent exclusion**, the rule is explicit and the FYI section is labelled.
- **Snooze/dismiss respected everywhere** because it's server-side per-user (§4), so every
  surface and channel agrees by construction.

### 3.5 Delivery channels — phased (in-app → email → push)
Per-user channel prefs, **global across alert types** (not a per-type×channel matrix — that
was judged overkill). In-app is always on. Channel toggles + cadence live in the user
**Preferences** area (`PreferencesSettings.vue`), mirroring the existing
`deals_email_enabled`/`deals_email_compact` pattern. Toggles appear in Phase 1 but are
**shown-disabled** (R-014) until their channel is wired.

- **① In-app (Phase A — this is the bulk of the work):** the hub + slim bell + read/unread +
  server-side snooze + per-type prefs + new types + Upcoming timeline. Fully shippable alone.
- **② Email digest (Phase B):** per-user opt-in, **cadence configurable (daily / weekly /
  off)**, SMTP-gated (shown-disabled until email is configured, R-014). A scheduled job (on
  the existing `BackgroundScheduler`) evaluates each opted-in user's actionable set and emails
  a digest, recording delivery in the ledger so the same alert isn't re-sent until it clears
  and re-fires. Reuses `emailer` (INV-4). Natural tie-in to the deferred "daily briefing"
  (P6-12).
- **③ Web push (Phase C):** PWA service worker + VAPID keys + a `PushSubscription` table
  (per-user, per-device) + a backend web-push sender. A scheduled evaluator pushes
  *newly-fired* actionable alerts (transition not-present→present in the ledger), deduped per
  channel. Biggest build; foundation for the future native app (P8-10).

### 3.6 New alert types
All four are in scope (sequenced across phases; generators are additive to the evaluator):
- **`no_planned_meals` (L442):** next week has no meal-plan entries → emit (default-on,
  tunable). Data exists (`meal_plan.py` entries + start_date); needs household "today"
  (C-2.K `AppSetting.timezone`) to compute "next week."
- **`shopping_day` (L403):** a reminder ahead of a shopping list's planned shopping day.
  **The field already exists** — `ShoppingList.planned_shop_date` (P6-01 Chunk 7,
  `shopping_list.py:138`), already drives the landing-page pick and a shopping-day banner. So
  this generator just reads it (emit when a list's `planned_shop_date` is within N days and
  not yet done) — **no new column needed.** (Verify-state-first win: the first draft assumed
  this had to be built.)
- **Subscriptions tier (L224, original spec):** surface the **existing `PriceAlert`** ("notify
  under") and future **back-in-stock** subscriptions in the centre as a distinct *armed-
  thresholds* tier — set-point stays on the price-history explorer, but **list & manage** them
  here with their own icons/styling (L224 explicitly wants central management + per-type
  styling). These fire via the scrape/ingestion pipeline (companion-scope), not the on-the-fly
  evaluator — the centre **displays and manages** them.
- **System tier (original spec):** offline / reconnect / "something serious went wrong" — a
  distinct **system** category, not folded into inventory alerts. Mostly client-detected
  (connectivity) + a server health signal; low/FYI by default. Smallest, latest add.

### 3.7 Upcoming "this fortnight" timeline (L61) — pulled into the hub
A 14-day forward view that aggregates dated events from across the app into one place:
- **Sources:** item **expiries** (`expiry_date`), **planned shopping days**
  (`ShoppingList.planned_shop_date`, already built), **meal-plan days** (entries per day),
  and **armed subscriptions** where a date is known. All data already exists — the timeline
  is an aggregation/read, not new schema.
- **Shape:** a compact date strip / mini-calendar with coloured dots per category; clicking a
  date reveals that day's items + planned meals (exactly the L61 ask). A lightweight
  chronological "next 14 days" list is the fallback shape if the calendar grid proves heavy.
- **Why here:** it turns Alerts from "what already broke" into "what's coming," which is the
  single biggest feature-richness lever and reframes the whole surface as forward-looking.
  The dashboard's future "this fortnight" card becomes a smaller mirror of this (§3.10).

### 3.8 Expiry-after-alert nudge (original spec Feature Note)
The original spec wanted: once an expiry alert is issued, **prompt to set a new expiry** (or
reset it). The bell already has inline `extend_expiry` / `reset_expiry`. Confirm these satisfy
it; if not, add a gentle "set a new expiry" nudge on the expiry row. Low-effort; fold into
Phase A.

### 3.9 Dashboard card contract (L60) — defined here, built later
Dashboard is deferred, but C-9 specifies the card: **top** = the §3.1 summary boxes
(types/counts/themes), **bottom** = a sneak-peek of the top 3 (or 3 distinct types), a
prominent **"see all"** → the hub, and (optionally) a peek at the Upcoming timeline. Same
data, smaller frame — no new logic, it reads the same canonical set.

---

## 4. Data model

### 4.1 Generalise the alert key
`alert_id`/`alert_key` becomes `<scope>:<kind>[:<discriminator>]`, e.g.
`stock:<uuid>:expiring_soon`, `meal:no_planned_meals:<iso_week>`, `list:<uuid>:shopping_day`,
`system:offline`. `act_on_alert.py` stops assuming a stock-item UUID and routes by scope/kind
(item actions still resolve a `stock_item_id`; non-item alerts have their own/no actions). The
key must be **stable across evaluations** so ledger rows match (this is the same discipline
`DoraSuggestionSuppression.dedup_key` already follows).

### 4.2 Fill `notification.py` → `AlertInteraction` (per-user)
Repurpose the empty stub (rename file to `alert_interaction.py`, delete the placeholder
comment — R-008). One row per `(user_id, alert_key)` capturing that user's relationship to a
specific live alert:
- `user_id: UUID`, `alert_key: str`
- `first_seen_at: datetime` — for "new since last visit" + history
- `read_at: datetime | None`
- `snoozed_until: datetime | None` — **server-side snooze** replaces the localStorage map
- `dismissed_at: datetime | None`
- `created_at`
Mirrors `DoraSuggestionSuppression`. Rows are written lazily (first interaction), pruned when
the underlying alert has been gone long enough (a maintenance sweep on the existing scheduler).
**Phase 2/3** add delivery dedup — either `last_emailed_at` / `last_pushed_at` columns here,
or a sibling `AlertDelivery(user_id, alert_key, channel, delivered_at)` table (decide at Phase
B; columns are simpler if dedup stays coarse).

### 4.3 `AlertPreference` (per-user, per-kind)
A small table (not scalar columns — alert kinds grow, and JSON pref blobs aren't the house
pattern; this matches the `MealSlot`-as-entity precedent): `(user_id, kind, enabled: bool,
tier_override: str | None)`. Absent row = default (enabled + default tier per §5). Surfaced
via `GET/PATCH` on a small alerts-prefs route (or folded into `users/me`).

### 4.4 Per-user channel prefs + thresholds
- **Channel prefs** → scalar columns on `User` (mirrors `deals_email_*`):
  `alerts_email_enabled`, `alerts_email_cadence` ('daily'|'weekly'|'off'),
  `alerts_push_enabled`. In-app needs no flag (always on).
- **Push subscriptions** → `PushSubscription(user_id, endpoint, p256dh, auth, created_at)`
  (Phase C).
- **Thresholds** → `AppSetting.expiring_soon_window_days`,
  `AppSetting.default_days_until_stocktake_alert` (household-wide; evaluator reads these;
  `EXPIRING_SOON_WINDOW_DAYS` becomes the seeded default — R-003 single source preserved).

### 4.5 Migrations
Plain, reversible, portable (SQLite **and** Postgres — R-005/R-006, §7.5): create
`alert_interaction`, `alert_preference`, (`push_subscription` at Phase C); add the channel
columns to `user` + the threshold columns to `app_setting`. **No shopping-list migration** —
`planned_shop_date` already exists (§3.6). Keep a single Alembic head (watch for concurrent-
session forks, as seen in C-2.F/G).

---

## 5. Defaults (proposed)
- **Actionable tier (drives the badge), default-on:** `expired` (high), `essential_low`
  (high), `expiring_soon` (medium), `out_of_stock` (medium).
- **FYI tier, default-on but tunable:** `low_stock`, `stocktake_overdue`, `no_planned_meals`,
  `shopping_day`. Shown in the list, don't inflate the badge.
- **Subscriptions (price / back-in-stock):** **off until armed** by the user (they're opt-in
  by nature).
- **System tier:** on (low/FYI) — connectivity/error signals are universally useful and quiet.
- **Channels:** in-app on; email off (opt-in, and shown-disabled until SMTP configured); push
  off (opt-in, Phase C). Email cadence default `daily` when first enabled.
- **Snooze:** default 7 days, server-side, per-user.

---

## 6. Phasing / sequencing (→ becomes IMPL_PLAN_ALERTS chunks)
The trustworthiness spine first; channels last.

1. **Spine — count + ledger + server snooze (§3.4, §4.1, §4.2):** generalise the key, fill
   `AlertInteraction`, move snooze server-side, derive one canonical per-user count. Fixes
   L438/L439 ahead of the full page. (Closes FU-042.)
2. **Per-type prefs + thresholds (§3.3, §4.3, §4.4):** `AlertPreference`, configurable
   `AppSetting` thresholds, the Manage panel. (L440/L441/L439.)
3. **The hub page (§3.1) + slim bell (§3.2) + per-kind styling + history.** (L437/L59/L60
   contract/L224 styling.)
4. **New evaluator types:** `no_planned_meals` (§3.6), then `shopping_day` (after the
   planned-shopping-day field), plus the subscriptions tier surfacing existing `PriceAlert`
   (§3.6/L224). Expiry-after-alert nudge (§3.8).
5. **Upcoming timeline (§3.7).**
6. **Channel B — email digest (§3.5):** cadence prefs + scheduled job + delivery dedup.
7. **Channel C — web push (§3.5):** service worker, VAPID, `PushSubscription`, sender.
8. **System tier (§3.6)** + **dashboard card** (§3.10, when dashboard lands).

Phases 1–5 are the in-app "fully polished hub" the user asked for; 6–8 layer the channels and
the system tier.

---

## 7. Open decisions
**Resolved 2026-06-15 (co-design):**
- Data model = live evaluator + per-user interaction ledger (derived conditions, not stored).
- No multi-user / recipient routing (dropped, not even a seam).
- Channels phased in-app → email → push; per-type on/off **per-user**; channel prefs per-user
  **global** across types; email cadence **configurable** (daily/weekly/off).
- Page = hub, bell = peek; thresholds household-wide on `AppSetting`.
- **Per-type tier override: IN** (ships with on/off in the prefs phase) — delivers the full
  "smarter priority" (L439).
- **Upcoming timeline: full mini-calendar with date dots** (L61 literal), click-a-date to
  expand.
- **Shopping-day alert: IN this work** — and the underlying field (`planned_shop_date`)
  **already exists** (P6-01 Chunk 7), so it's a pure read; the generator + timeline dots both
  consume it, no shopping-list schema change.

**Still open (deferred to their phase, not blocking):**
1. **Delivery dedup storage (Phase B)** — `last_emailed_at`/`last_pushed_at` columns on
   `AlertInteraction` vs a sibling `AlertDelivery` table. Decide at Phase B.

---

## 8. From the original spec (historical — `docs/00_original_spec/`)
The Alerts board corroborates the redesign:

| Original note | Verdict | Effect |
|---|---|---|
| Configurable "not updated in N days" window; turn off unchanging-level warnings; no warnings for out-of-stock items | **keep → §3.3** | Exactly the per-type opt-out + configurable threshold. |
| Expiry alert → reset / prompt for new expiry (+ the two Feature Notes) | **keep → §3.8** | Partly built (inline extend/reset); confirm/finish with a nudge. |
| "Notified when a merchant's product comes back in stock" | **keep → §3.6** | A subscription alert in the new subscriptions tier. |
| Alerted offline / on reconnect / on serious error | **keep → §3.6 (system tier)** | A separate *system* category, phased last. |

(No superseded items. The board's intent maps cleanly onto the redesign.)

---

## 9. Ripple & dependencies
- **Meal plans (C-2, done):** data for `no_planned_meals`; `AppSetting.timezone` for "next
  week."
- **Shopping lists:** the `shopping_day` alert + timeline read the **existing**
  `planned_shop_date` (P6-01 Chunk 7) — no shopping-list change needed (relates to L402/L403).
- **Price history / `PriceAlert`:** surfaced/managed in the subscriptions tier (§3.6); set-
  point stays on the explorer. **Back-in-stock** is companion/ingestion-scope (Phase 2 of the
  master plan) — the centre is *designed to hold it*, fired by the pipeline.
- **AppSetting / config (C-cross):** new threshold fields; reuse the singleton + admin PATCH
  pattern.
- **User preferences:** channel toggles + cadence on `PreferencesSettings.vue` (mirrors
  `deals_email_*`).
- **Dora assistant:** reads the same canonical alert set — the cleaner model directly improves
  "what needs my attention" (and the assistant could *narrate* the Upcoming timeline).
- **Scheduler (`startup.py`):** email/push evaluators + the ledger-prune sweep hang off the
  existing `BackgroundScheduler` — no new infra.
- **Dashboard (deferred):** card contract defined (§3.10).
- **Settings (deferred):** prefs hosted on the hub + Preferences area for now; consolidate
  when Settings is built.
- **Multi-user (deferred, Phase 4):** **explicitly out of scope** — no recipient routing, no
  per-recipient seam. The per-user `user_id` on the ledger/prefs is legitimate (read-state is
  inherently per-user even single-household), **not** speculative tenancy.
- **PWA / native (P8-10):** web push (Phase C) is the foundation.
- **B5** fixed the alerts-route 404 — confirm in browser (FU).

---

## 10. Feedback coverage

Maps `§ALERTS` (L437–442) + the alert-related `§DASHBOARD` and `§PRODUCT HISTORY` and
`§SHOPPING LIST` bullets.

| Bullet (line) | Summary | Where |
|---|---|---|
| L437 | Alert control screen missing | §3.1 (hub) |
| L438 | Count bubble ≠ list count (6 vs 10) | §1.1, §3.4 (+ FU-042) |
| L439 | Smarter priority / what's actually an alert | §3.3 (tier override), §3.4 |
| L440 | Opt in/out of alert types | §3.3 (per-user on/off) |
| L441 | Dora as quiet or noisy as *they* want | §3.3 (per-user), §3.5 (channels) |
| L442 | New "no planned meals next week" alert | §3.6 (`no_planned_meals`) |
| L59 (dash) | Alerts nav broken (404) → build alerts page | §1 (B5 fixed; confirm) + §3.1 |
| L60 (dash) | Alert card redesign (summary boxes + sneak peek + see-all) | §3.10 (contract; dashboard deferred) |
| L61 (dash) | "This fortnight" calendar widget (coloured date dots) | §3.7 (**now in scope** — Upcoming timeline in the hub) |
| L224 (product history) | Manage alerts centrally + unique per-type styling/icons | §3.6 (subscriptions tier), §3.1/§3.2 (per-kind styling) |
| L403 (shopping list) | "Shopping day alert would be good to have" | §3.6 (`shopping_day`; reads the existing `planned_shop_date`) |
| L505 (settings) | Push/notify *another* user (Alexa-style) + share list | **Out of scope** — needs deferred multi-user (Phase 4); dropped deliberately (§ co-design note, §9). Share-list is a separate shopping-list concern. |
| L506 (settings) | Gamification | Out of scope — "someday" per master plan §7. |

A reviewer should be able to audit "is anything missing?" at a glance. After this proposal is
accepted, flip the now-covered rows (esp. L61, L224, L403) in
`docs/02_feedback/COVERAGE_GAPS.md` from gap → covered.
