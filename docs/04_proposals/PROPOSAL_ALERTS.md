# Proposal — Alerts Control Centre (C-9)

**Status:** Draft for discussion · **Date:** 2026-06-06 · Changes NO code.  
**Scope:** A dedicated alerts control centre — summary + full list, **per-type
opt-in/out**, a single priority/"what counts" model (which fixes the bell-count
mismatch), per-type icons/styling, a new "no planned meals next week" alert, and
central management that also covers context-aware subscriptions (price "notify
under", back-in-stock). Defines what the (deferred) dashboard alert card will show.

> **Charter tie-break:** Effortless (P1) + Anti-creep (P10). "Dora is as quiet or
> noisy as they want" (L440) — the control centre's job is to make alerts
> *trustworthy* (the count means something) and *tunable* (turn off what you don't
> care about), not to add more noise.

---

## 1. Current state (from live code)

- **6 inventory alert kinds**, computed on-the-fly per request
  (`get_alerts.py:60-196`): `expired` (high), `expiring_soon` (med, window
  hardcoded 7d), `out_of_stock` (med), `low_stock` (low), `essential_low` (high,
  for flagged items), `stocktake_overdue` (low). Severity = high/med/low; ordered
  severity-then-name.
- **Bell** (`AlertsBell.vue`) — badge + grouped dropdown with inline actions
  (snooze 7d, extend/reset expiry, mark restocked, acknowledge stocktake).
- **Dashboard card** — top-5 by severity (`DashboardPage.vue:89-143`).
- **Alerts page** exists (`AlertsPage.vue`) but is a **stub** with a banner saying
  "full control centre is on the way." (The old "Alerts → 404", L57, is fixed —
  the route resolves now; **confirm in browser**.)
- **No per-type preferences**; thresholds are **hardcoded**
  (`EXPIRING_SOON_WINDOW_DAYS = 7`). Only per-item `stocktake_alerts_are_enabled`
  + `days_until_stocktake_alert` exist.
- **Price alerts are a separate system** (`PriceAlert`, `price_history.py`,
  managed on `PriceHistoryPage`) — not in the bell or alerts page.
- **No persistent Notification entity** (the file is an empty stub); **snooze is
  client-side localStorage** (per-device).

### 1.1 The count mismatch (L438) — root cause found
The badge and the list disagree on **two** axes:
- **Severity:** badge = `high_count + medium_count` (`alertStore:99`) — it
  **excludes low**; the dropdown/page list **shows all severities**. → "I see 6
  [badge], the bell shows 10 [list]" is the **4 low-severity alerts** the badge
  omits.
- **Snooze:** the list filters client-snoozed alerts (`alertStore:81`) but the
  badge counts come from the **raw backend numbers** — so a snoozed high/med alert
  shrinks the list but not the badge.

Both stem from there being **no single definition of "what counts."** Fixing this
is the spine of the whole redesign (§2.3).

---

## 2. The redesign

### 2.1 A real Alerts control centre (page) (L437, L57, L60)
Fill in `AlertsPage.vue` as the hub, two regions (this is also the **contract the
deferred dashboard card will mirror**, L60):

- **Summary (top):** a row of boxes / small chart **by type** — count + plain-
  language theme: "5 expiring soon", "3 essential low", "2 expired". At-a-glance
  "what's going on" (L60 top section).
- **List (below):** grouped by type/severity, **per-type icons & styling**
  (extend the existing `iconFor(kind)`/`colorFor(severity)` into a consistent
  per-kind visual identity), each with its inline actions (already exist on the
  bell). **Top-N preview + "see all"** on the dashboard card; the page shows all.
- **Manage (here too):** the per-type preferences (§2.2) live on this page so
  "control centre" is literal — quiet/noisy tuning where you see the alerts.

### 2.2 Per-type opt-in / out + thresholds (L440)
A preferences panel: **enable/disable each alert kind**, and make the **hardcoded
thresholds configurable** — expiring-soon window (N days), stocktake timeframe
(already per-item; expose a default), and "don't warn me about X" toggles. The
original spec asked for exactly this granularity (configurable stale-level window,
turn off unchanging-level warnings, no warnings for out-of-stock items — §4).

> **Where prefs are stored:** user-level alert preferences (new). The natural home
> is Settings, but **settings is a deferred surface** — so the control-centre page
> can host the prefs directly for now (note the eventual settings move). §6.

### 2.3 One priority model + one "what counts" definition (L438, L439) — fixes the bell
Define a **single canonical alert set and count** used by the **badge, the bell
list, the dashboard card, and the page** alike. Decisions to lock (open, §5):

- **Does the badge count low-severity?** Proposed: the badge counts the **actionable
  (high+medium) unsnoozed** set, and the list **visually separates** a low/"FYI"
  tier so the badge and the *actionable* list agree, with lows shown but not
  inflating the badge. Either way — **badge number == count of items in its tier**,
  no silent exclusion.
- **Snooze respected everywhere:** the badge, list, and dashboard all apply the
  same snooze filter (today only the list does). This requires the count to be
  derived from the **filtered** set, not the raw backend numbers.
- **"Smarter what counts" (L439):** fold the per-type opt-outs (§2.2) into the
  canonical set — a disabled type contributes nothing to any surface.

### 2.4 New alert: "no planned meals next week" (L441)
Generate from meal-plan data: if there are **no meal-plan entries for next week**,
emit a `no_planned_meals` alert (low/medium, opt-in per §2.2). The data exists
(`meal_plan.py` entries + start_date); no handler produces it today.

### 2.5 Unify context-aware subscriptions (brief + original spec §4)
Bring **subscription-style alerts** into the control centre's management view, even
though they fire via the scrape pipeline rather than the on-the-fly evaluator:

- **Price "notify under"** (`PriceAlert.threshold_unit_price`) — keep the set-point
  on the price-history explorer, but **list & manage** all price alerts in the
  control centre.
- **"Back in stock"** (original spec: "notified when a merchant's product comes
  back in stock") — a future subscription of the same shape; design the centre to
  hold it.

So the centre has **two tiers**: *active alerts* (computed now) and *subscriptions*
(thresholds you've armed). This is the "central management that also covers the
context-aware alerts" the brief asks for.

### 2.6 Dashboard card contract (L60) — defined here, built later
Dashboard is deferred, but C-9 specifies what its card shows: **top** = the summary
boxes (types/counts/themes), **bottom** = a sneak-peek of the top-3 (or 3 distinct
types), with a prominent **"see all"** → the control centre. Same data, smaller
frame.

### 2.7 Expiry-after-alert behaviour (original spec §4)
The original spec wanted: on expiry alert, **prompt to set a new expiry** (and/or
reset it). The bell already has inline `extend_expiry` / `reset_expiry` actions —
confirm these satisfy it; if not, add the "prompt for new expiry once alerted"
nudge. (Low-effort; note it.)

---

## 3. Persistence note (snooze) — server vs device
Snooze is **client-side localStorage** (per-device). For a multi-user / multi-
device household, a snooze on one phone doesn't carry to another, and (per §2.3)
the count must be derived from the snooze-filtered set. **Open (§5):** move snooze
server-side (a `DoraSuggestionSuppression`-style table already exists for the
suggestions system and is a ready pattern), or keep per-device. Recommend
**server-side** so counts are consistent everywhere and snooze follows the user.

---

## 4. From the original spec (historical — `docs/00_original_spec/`)
The Alerts board is rich and **corroborates the redesign**:

| Original note | Verdict | Effect |
|---|---|---|
| Configurable "not updated in N days" window; turn off unchanging-level warnings; no warnings for out-of-stock | **keep → §2.2** | These are exactly the per-type opt-out + threshold config. |
| Expiry alert → reset expiry / prompt for new expiry | **keep → §2.7** | Partly built (inline extend/reset); confirm/finish. |
| "Notified when a merchant's product comes back in stock" | **keep → §2.5** | A subscription alert; design the centre to hold it. |
| Alerted offline / on reconnect / on serious error | **consider (system tier)** | A separate *system* alert category (connectivity/errors), distinct from inventory alerts. Likely a small later add — note it; don't fold into the inventory model. |

(No superseded items.)

---

## 5. Open decisions (for co-design)
1. **Priority model / "what counts"** (L438/439) — does the badge count low-
   severity, or only high+medium with lows in a separate FYI tier (proposed)? The
   rule must make badge == its tier's list.
2. **Which alerts default ON** (brief) — proposed defaults: expired, expiring-soon,
   essential-low ON; low-stock, stocktake-overdue, no-planned-meals default-but-
   tunable; back-in-stock/price off until armed.
3. **Snooze: server-side or per-device** (§3) — proposed server-side.
4. **Prefs home** — on the control-centre page now (proposed) vs wait for the
   deferred settings surface.
5. **System alerts** (offline/error, §4) — in scope as a separate tier, or defer?

---

## 6. Ripple & dependencies
- **Dashboard** (deferred) — C-9 defines the card contract (§2.6); build later.
- **Settings** (deferred) — eventual home for alert prefs; hosted on the alerts
  page for now (§2.2).
- **Price history** — price alerts surface/manage in the centre (§2.5); set-point
  stays on the explorer.
- **Meal plans (C-2)** — data for the no-planned-meals alert (§2.4).
- **Suggestions suppression** — reuse the `DoraSuggestionSuppression` pattern if
  snooze goes server-side (§3).
- **B5** fixed the alerts-route 404 (§1) — confirm in browser.

---

## 7. Suggested sequencing
1. **Count fix + single "what counts"** (§2.3) — the trustworthiness spine; can
   ship ahead of the full page. (Logged FU-042.)
2. **Control-centre page** (§2.1) — summary + grouped list + per-kind styling
   (fills the existing stub).
3. **Per-type prefs + configurable thresholds** (§2.2) — hosted on the page.
4. **No-planned-meals alert** (§2.4) — new generator.
5. **Subscriptions tier** (§2.5) — surface price alerts; design for back-in-stock.
6. **Server-side snooze** (§3) + **dashboard card** (§2.6, when dashboard lands).

---

## 8. Feedback coverage

Maps ALERTS (L437-441) + the alert-related DASHBOARD bullets.

| Bullet (line) | Summary | Where |
|---|---|---|
| L437 | Alert control screen missing | §2.1 |
| L438 | Count bubble ≠ list count (6 vs 10) | §1.1, §2.3 (+ FU-042) |
| L439 | Smarter priority / what's actually an alert | §2.3, §2.2 |
| L440 | Opt in/out of alert types (quiet/noisy) | §2.2 |
| L441 | New "no planned meals next week" alert | §2.4 |
| L57 (dash) | Alerts nav broken (404) → build alerts page | §1 (B5 fixed; confirm) + §2.1 |
| L60 (dash) | Alert card redesign (summary boxes + sneak peek + see-all) | §2.6 (contract; dashboard deferred) |
| L61 (dash) | "This fortnight" calendar widget | Out of scope — dashboard/calendar (deferred); noted |
| Price "notify under" / back-in-stock | Context-aware subscriptions in central mgmt | §2.5 |
