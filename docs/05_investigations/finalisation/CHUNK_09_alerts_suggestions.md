# Chunk 09 — Alerts + Suggestions

**Analysed:** 2026-10-23 · **Analyst session:** finalisation overnight run (solo, no subagents)
**Scope (from PLAN §4):** `ALERT_ROUTER` (evaluator, interactions, prefs, upcoming, push subscriptions), the push job + the evening brief job, the bell panel + `AlertRow`, Settings → Notifications (in-app kinds · discard window · price watches · push · brief · deals email toggles), the admin threshold/VAPID pages, the suggestions generator + endpoints + snooze prune (FU-513), and the suggestions panel in Dora's chat.
**Boundaries:** `stock_attention.py` and the row outline are Chunk 5 (read here as the evaluator's shared predicates); `/alerts/upcoming`'s consumer (*What's coming*) is Chunk 8; the deals email *content* and `PriceAlert` creation are Chunk 10; `meal_plans/reconcile.py` and `daily_brief.py` content are Chunk 2; `DoraChat`/`DoraBubble` themselves are Chunk 11; the Settings shell is Chunk 13; `startup.py`'s scheduler is Chunk 19.

## 0. Reading list + files walked

**Planning docs consulted:** `PROPOSAL_ALERTS.md` (§3 model, §7 open decisions — closed, §4/§8 coverage) · `IMPL_PLAN_ALERTS.md` (C-9.1…9.10) · `IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md` Step 0 (Q1–Q5, the canonical attention rule) · feedback `[06-Jun-2026]` § ALERTS (L436–442) · `HelpPage.vue` (no alerts group) · `app_knowledge.py` L39–45 · open FUs: FU-916, 917, 702, 701, 700, 627, 624, 654, 671, 684, 513 (resolved), 518, 521, 531.

**Files walked (every file opened, with line count):**

| File | Lines | Role |
|---|---|---|
| `dora_api/features/alerts/get_alerts.py` | 566 | the evaluator: 8 kinds, per-user overlay, counts |
| `dora_api/features/alerts/alert_kinds.py` | 86 | kind → severity registry; derived tier |
| `dora_api/features/alerts/alert_key.py` | 83 | `<scope>:<id>:<variant>:<episode>` keys |
| `dora_api/features/alerts/interact_with_alert.py` | 156 | snooze / dismiss / un-suppress / dismiss-all |
| `dora_api/features/alerts/act_on_alert.py` | 102 | reset / extend expiry |
| `dora_api/features/alerts/manage_alert_prefs.py` | 124 | per-user per-kind on/off |
| `dora_api/features/alerts/get_upcoming.py` | 158 | fortnight feed |
| `dora_api/features/alerts/push_subscriptions.py` | 169 | VAPID key · subscribe · unsubscribe |
| `dora_api/features/alerts/send_alerts_push.py` | 220 | hourly push job |
| `dora_api/features/alerts/send_daily_brief.py` | 225 | 19:00 household-local brief job |
| `dora_api/infrastructure/push_sender.py` (head) | — | pywebpush wrapper, dry-run |
| `dora_api/features/suggestions/generators.py` | 475 | six generators |
| `dora_api/features/suggestions/suggestions.py` | 289 | GET + dismiss / snooze / unsuppress, fairness cap |
| `dora_api/features/suggestions/prune_expired_snoozes.py` | 54 | nightly prune (FU-513) |
| `dora_api/features/stock_items/stock_attention.py` | 180 | shared predicates (Chunk 5 owner) |
| `dora_api/domain/entities/alert_interaction.py` (49), `alert_preference.py` (35), `push_subscription.py` (38), `dora_suggestion_suppression.py` (47) | — | entities |
| `dora_api/startup.py` L95–185 | — | scheduler wiring (push :30, brief :45, prune 03:30) |
| `web_app/public/push-sw.js` | ~90 | push-only service worker |
| `web_app/src/components/AlertsBell.vue` | 294 | the only alerts surface |
| `web_app/src/components/AlertRow.vue` | 230 | the alert card |
| `web_app/src/components/AlertKindAvatar.vue` | 20 | kind icon in severity circle |
| `web_app/src/components/help/AttentionRulesDialog.vue` | 292 | the colours/outlines guide dialog |
| `web_app/src/stores/alertStore.ts` (93), `alertPrefsStore.ts` (52), `suggestionStore.ts` (83) | — | stores |
| `web_app/src/models/alert.ts` | 213 | DTOs + `ALERT_KIND_META` |
| `web_app/src/services/api/alertApiService.ts` (72), `suggestionsApiService.ts` (~70) | — | clients |
| `web_app/src/composables/useAlertActions.ts` (55), `usePushSubscription.ts` (164) | — | composables |
| `web_app/src/pages/settings/NotificationsSettings.vue` | 506 | the user-facing settings |
| `web_app/src/pages/settings/AdminSystemAlertsSettings.vue` (130), `AdminSystemPushSettings.vue` (192) | — | admin pages |
| `web_app/src/components/dora/DoraChat.vue` L100–175, `DoraBubble.vue` (badge + refresh lines) | — | suggestion cards + badge |
| tests: `test_alerts.py` (30), `test_alerts_push.py` (8), `test_stock_attention.py` (18), `test_suggestions_router.py` (14), `test_suggestions_snooze_prune.py` (4), `test_suggestion_selection.py` (4); vitest `alertRow.spec.ts` (12), `alertStore.spec.ts` (9) | — | coverage inventory |

## A. Full Systems Test — Alerts + Suggestions

### A1. Preconditions
- Dense seed with: an expired item, an item inside the household's expiring-soon window, an essential item Out and one Low, a draft list with `planned_shop_date` tomorrow and another dated last week, next week empty on the plan, ≥3 past-day unreconciled meals (auto-drain **off**), a price watch at or above a tracked product's current price; money **on**, products **on**.
- A second user; VAPID keys configured (admin page) in a browser that supports web push; a device without VAPID for the "ask an admin" state.

### A2. Golden path
1. Header bell: badge = **actionable count** (high + medium) — the FYI nudges are listed but never counted; bell colour red when any high, amber when only medium; tooltip *N things need attention*.
2. Open the panel → *What needs your attention* → cards severity-first: *X has expired* (Push 7 days · Clear expiry · **Log waste**), *X expires soon* (Push 7 days · Clear expiry · **Recipes** → `/cookbook?usesStockItem=`), *Essential X is out of stock* (level picker · cart), *Did you forget your shopping?* (Open list), *Shopping day tomorrow: …*, *No meals planned for next week* (Plan meals), *N past meals need confirming* (Reconcile), *Product hit your price* ($ · cart via linked item · Price history).
3. Tap a card → its surface (item page / list / planner / reconcile / price history); tap an action → *Done.* toast, panel refreshes; **Log waste** → the stock row's reason dialog → expiry cleared → alert gone, Undo brings it back.
4. **Snooze** (7 days) → card moves to *Snoozed (N)*; **Unsnooze** restores; **Dismiss** → gone for this **episode** only: push the item's expiry to a new date → a new alert; **Dismiss all** → active set empty, *Nothing to do right now*.
5. Settings → Notifications → *In-app alerts*: toggle a kind off → its cards, counts **and** stock-row outlines vanish for this user only (second user unchanged); *Discard alerts after 7 days* → alerts whose episode began earlier drop out; *Price watches* list with remove.
6. *Push notifications on this device* → permission prompt → subscribed; within the hour a newly fired actionable alert arrives as a notification; tapping it opens Dora with the bell panel open (`?alerts=open`); FYI nudges never push.
7. *Evening brief* on → at 19:00 household-local a single notification with tomorrow's meals + any shopping day; nothing is sent on an empty evening; a second scheduler tick inside the hour does not double-send.
8. Admin → System → Alert thresholds: set the expiring-soon window to 14 → the evaluator, the rows and the *Use it up* card all move together; Admin → System → Push: paste VAPID keys (private key encrypted at rest) → the user-side toggle enables.
9. Dora bubble shows a suggestion count badge (red when any high); open chat → *Suggestions* cards on top: *Use X soon*, *You're over budget this week*, *You're probably due for X*, *Buy less X?*, *Still have X?* (quick check), *N past meals need confirming* — each with its primary action, **Snooze 1d**, **Dismiss**, **Why?**; ≤ 8 with every firing kind guaranteed one slot.
10. Dismiss a suggestion → it stays gone until the condition changes; snooze → back after 24 h; the nightly 03:30 job prunes elapsed snoozes.

### A3. Edge cases
- A kind the client doesn't know (backend ahead) → row renders with only snooze/dismiss and a generic bell icon (pinned by `alertRow.spec`).
- Discard window `Never` (null) keeps everything; an unknown value → 400.
- `shopping_day` and `shopping_overdue` are separate keys on the same list: dismissing the reminder does not silence the missed-shop nudge; moving the planned date is a new episode.
- `no_planned_meals` keys on next week's ISO label → clears the moment a meal lands in that week; its detail formats the date range server-side (`%a %d %b`, 09-R14).
- Essential item restocked then run out again → new episode (`essential_out:<level_since>`); an item with `stock_level_last_updated` None keys on today.
- Price watch: current price ≤ threshold → fires once per **offer**; a new observation at or under the line → a new alert; money off → no price alerts and no toggle.
- Alert key longer than 255 chars → silently a no-op (never a Postgres 500).
- Push: browser unsupported / permission denied / VAPID unset → the right notice above a disabled toggle; unsubscribe tears down server-side first; a 404/410 from the push service prunes the subscription mid-fan; dry-run sender when VAPID is missing never stamps the ledger.
- Daily brief with the user opted in but no device → nothing stamped; subscribe later that evening → the brief still fires that evening.
- Bell polls every 60 s **only while the tab is visible**; returning to the tab refreshes immediately; opening the panel refreshes and hydrates the stock store (for the level picker).
- Suggestions: the household-wide suppression table (no `user_id`) means one user's dismiss hides the suggestion for **everyone** (09-D1).
- Over-budget suggestion body carries `$` literals regardless of the install's currency (09-R6).
- `generate_likely_due` skips items with < 3 purchases or a mean gap > 90 days.
- A user with every kind disabled → bell badge 0, *Nothing to do right now*, no row outlines — and the stock page's *Needs attention* chip matches nothing (FU-702).

### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (one FYI nudge: *No meals planned*) | ✓ (A2) | ✓ (money/products off → 6 kinds, no price watch toggle, no deals email section) | ✓ (push + brief + discard window) | ✓ (thresholds, VAPID) | ✓ (prefs + interactions per user; suppression **not**, 09-D1) | ✓ (single-worker scheduler note, VAPID keygen) | – |

### A5. Load-bearing conditions
- One evaluator: `get_alerts.py` emits the three per-item kinds from `stock_attention`'s predicates; `get_stock_items` reads `resolve_attention_map` with the same user's disabled kinds — the bell, the rows and the chip can't disagree.
- Tier is **derived** from severity (`is_actionable`), never stored; `AlertPreference` is an on/off switch only.
- Every alert is one **episode** (key carries the fact that started it); dismiss holds for the episode; `started_on` is what the discard window measures.
- `AlertInteraction.last_pushed_at` is the only delivery dedup; the push job clears it when a key leaves the user's set so a re-fire re-notifies.
- Scheduler runs in exactly one gunicorn worker; two workers would double-send (documented in `startup.py`).

### A6. Release-gate rows
- Badge count = number of high+medium cards in the panel (feedback L438: "6 vs 10" — pinned by `test__alerts__actionable_count_equals_high_plus_medium_in_items` and `alertStore.spec`).
- Disable `expiring_soon` for user A → A's rows lose their outline, user B's don't.
- Dismiss an expiry alert, change the expiry → a fresh alert.
- With VAPID configured: subscribe, fire an alert, receive the push, tap → panel open.
- 19:00 household-local brief arrives once; 19:20 restart does not resend.

## B. Help content — Alerts + Suggestions

### B1. Current help audit
HelpPage has **no Alerts or Notifications group**; `AttentionRulesDialog` (reachable from the Stock guide) explains the row outline well and says "Turning a kind off under Settings → Notifications turns off its outline too" — accurate. Nothing explains: the bell's badge rule, what each of the eight kinds means and when it fires/clears, snooze vs dismiss and the *episode* rule, the discard window, push setup (user + admin), the evening brief, price watches, or Dora's suggestions and how they differ from alerts. The Notifications InfoTips are good one-liners and stay. `AttentionRulesDialog` still says "Due for a stocktake check" unconditionally (FU-700) and "open / in-use" (FU-711). DoraBot's Alerts paragraph is accurate; it says nothing about suggestions, push or the brief.

### B2. Help entries
New group **Alerts & notifications** (icon `ICONS.notifications`), `path: '/settings/notifications'` unless noted:

1. **The bell** (`path: '/'`) — "The bell in the header is where Dora puts the things that need you. The number on it counts the **actionable** ones — expired food, an essential that's low or out, an item expiring soon, a shopping day you've missed, a price watch that hit — and turns red when any of them is urgent. Lower-key nudges (an unplanned week, a shopping day coming up, meals to confirm) are listed in the panel but never counted. Tap a card to go to the thing; the buttons under it act on it right there — push or clear an expiry, log waste, change the level, add to a list, find recipes."
2. **What each alert means** — the eight kinds, one line each: *Expired* (past its date; high) · *Expiring soon* (inside the household's window, set by an admin; medium) · *Essential low/out* (you flagged it essential and it's low or out; high — a non-essential running low is **not** an alert, the stock row already says it) · *Did you forget your shopping?* (a list's planned day has passed and it's still open; medium) · *Shopping day* (a planned shop in the next three days; low) · *No meals planned for next week* (low) · *Past meals need confirming* (the reconcile queue is long enough to be worth a walk; low; absent when meals reconcile automatically) · *Hit your price* (a product you watch is at or under your price; medium; money features only).
3. **Snooze, dismiss, and why alerts come back** — "Every alert is about one **episode** — this expiry date, this run-out, this shop day. **Dismiss** hides it until that episode is over; the next pack of apples, the next time an essential runs out, is a new alert. **Snooze** hides it for seven days and lists it under *Snoozed* in the panel, where you can bring it back. *Dismiss all* dismisses what's on screen now. *Discard alerts after N days* (Settings → Notifications) quietly drops anything whose episode began longer ago than that, as if you'd dismissed it. There is no read/unread — dismiss is the one way to put an alert away."
4. **Choosing which alerts you get** — "Settings → Notifications → *In-app alerts* lists every kind with a switch. Off means the kind is gone for **you** everywhere — the bell, its count, the stock rows' outlines and push — and leaves everyone else's alerts alone. A kind's weight (how loud it is) is fixed; what you choose is whether you hear it at all. The expiring-soon window is household-wide and lives under Settings → Admin → System → Alert thresholds."
5. **Push notifications** — "Push needs three things: an admin has set VAPID keys (Settings → Admin → System → Push; generate a pair with `py_vapid`), this browser supports web push (on an iPhone the app must be added to the home screen first), and you've switched *Push notifications on this device* on and allowed the permission. Each device subscribes separately. Dora pushes **newly fired actionable** alerts, hourly, once each — never the low-key nudges — and a tap opens the bell panel. Turning the switch off removes this device only."
6. **The evening brief** — "One notification at 7pm in your household's timezone with tomorrow's meals and any shopping day due. It rides push, so push has to be on for the device. It only arrives when there's something to say; an empty evening sends nothing."
7. **Price watches** — "A watch on a product (set from Price history or My products) fires a *hit your price* alert when the shelf price is at or under your figure. Your watches are listed under Settings → Notifications with a remove button. Money features only."
8. **Dora's suggestions** (`path: '/'`) — "Different from alerts: suggestions are Dora's *ideas*, shown as cards at the top of her chat and counted on her bubble. *Use X soon* (expiring within three days), *You're over budget*, *You're probably due for X* (your buying rhythm says so), *Buy less X?* (three or more waste events in 90 days), *Still have X?* (a quick check when a decision depends on an item she's unsure of), and *Past meals need confirming*. **Why?** shows her reasoning. Snooze hides one for a day, Dismiss until the condition changes; at most eight show at once and every kind gets at least one slot. Dismissing a suggestion hides it for the whole household." (09-D1 — state the current behaviour honestly.)

Also: fix `AttentionRulesDialog` copy for FU-700 (gate the stocktake sentence on `stocktake_enabled`) and FU-711 ("Opened").

### B3. DoraBot corpus delta
Append to the Alerts bullet (`app_knowledge.py` L39–45): *"Alerts are about one episode each; dismiss holds for that episode, snooze hides for 7 days, and a per-user discard window drops old ones. Push (VAPID, per device, actionable kinds only, hourly) and a 7pm evening brief are under Settings → Notifications. Dora's **suggestions** are separate: cards in her chat (use soon, over budget, probably due, buy less, quick check, meals to confirm) with Why?, Snooze 1d and Dismiss."*

## C. Senior review — Alerts + Suggestions

Verdict key: **execute** · **FU** · **waive** · **conditional**. Sizes S/M/L.

### C1. Bugs (verified or high-confidence latent)
- **09-R1** · D-006 — `generators.generate_over_budget` (L151–157) bakes `$` into `body` and `reason` five times (`f"Spent ${dto.spent:.2f} of your ${dto.amount:.2f} target…"`) — a EUR/GBP household reads dollars; the buy-verdict fixed exactly this by shipping raw amounts (`VerdictReasonDto.amount_*`). The `payload` already carries `amount/spent/over_by`. · **Exact change:** drop the figures from `body`/`reason` prose (or template them client-side from `payload` through `formatMoney`); `title`'s `period.replace("ly", "")` → a `{weekly: "week", …}` map (08-R13 class). · S · guard: a test asserting no currency symbol in any suggestion string (the verdict's `test__no_reason_string_anywhere__contains_a_currency_symbol` shape). · **execute**.
- **09-R2** · `generate_likely_due` (L209–224) re-implements mean-gap-between-unique-dates — the fourth copy FU-683 D3 counted; `domain/cadence_math.mean_gap_days` is the chokepoint and is already imported by the sibling `pantry_belief`. · **Exact change:** `avg_gap = mean_gap_days(unique_sorted)`; keep the min-samples / max-gap gates. · S · **execute**.
- **09-R3** · `generate_over_budget.primary_action.path = "/settings/preferences"` — that page is **Appearance** (`SettingsShell.vue:124`); the budget lives at `/settings/budget` (`routes.ts:251`). "Review budget" lands the user on the theme picker. · **Exact change:** `/settings/budget`. · S · **execute**.
- **09-R4** · FU-654 — five more `session.get("user_id")` copies in this group: `get_alerts._current_user_id`, `interact_with_alert`, `manage_alert_prefs`, `push_subscriptions`, `suggestions` (plus `get_dora_score` and `get_pantry_beliefs` already counted). · **Exact change:** 02-R12's helper. · S · **execute**.
- **09-R5** · R-003 — the default snooze length is a literal **7** in four places: `AlertRow.vue:88,91` (aria-label + tooltip copy), `alertStore.ts:50`, `alertApiService.ts:28`, and `SnoozeRequest.days = 7` server-side. · **Exact change:** one `DEFAULT_SNOOZE_DAYS` in `models/alert.ts` the three client sites read; copy interpolates it. · S · **execute**.
- **09-R6** · `get_alerts.handle` (L193–194) reads `self.repository.get(AppSetting).all()[0]` — the FU-759 / 06-R15 class (second copy of the install-wide read beside `get_or_create_app_setting`). · S · **execute**.
- **09-R7** · R-031 — two sessions per request: `interact_with_alert.dismiss_all` (L112) and `send_alerts_push._process_user` (L96) construct a fresh `SqlAlchemyRepository()` for `GetAlertsHandler` while mutating through the passed `repository` (the review finding 25 pattern). · **Exact change:** pass `self.repository` / `repository`. · S · **execute**.
- **09-R8** · `push_subscriptions.get_vapid_public_key` (L130–131) returns a hand-built `jsonify({"detail": …}), 404` rather than the app's problem-details `not_found(...)`, so this one 404 has a different shape from every other. · **Exact change:** `not_found("VAPID configuration")` (the SPA only checks the status). · S · **execute**.
- **09-R9** · `send_daily_brief._ledger_row` (L221–225) does `.all(...)` then `rows[0]` where `.one()` exists and is used three lines up in `interact_with_alert._find`. · S · **execute**.

### C2. Redundancy / DRY (R-001, R-003)
- **09-R10** · `AttentionRulesDialog.cheatRows` (L236–247) is a hand-written truth table of `attentionBand()` with a comment saying it "mirrors" it — the drift shape R-003 forbids, on a help page about the very rule. · **Exact change:** derive the band column by calling `attentionBand({needs_attention, is_essential}, outOfStock)` on eight synthetic rows; the table then cannot disagree with the code. · S · **execute**.
- **09-R11** · Two shopping-day nudges and two reconcile nudges are generated twice — once as alerts (`get_alerts._shopping_day_alerts`, `_meal_reconcile_overdue_alerts`) and once as suggestions (`generate_reconcile_meals_pending` with the same `reconcile_overdue_signal`). The reconcile pair is the same fact in two inboxes with two dismiss ledgers (one per user, one household-wide). · **Exact change:** owner call — drop the suggestion twin (the alert kind has the per-user prefs and the bell) or the alert twin; recommend dropping `KIND_RECONCILE_MEALS_PENDING` since every other suggestion is something alerts don't say. · S · **conditional** (execute if the owner agrees the alert is the home; else record).
- **09-R12** · `send_alerts_push._subscriptions_by_user` and `send_daily_brief._subscriptions_by_user` are byte-identical (L79–86 vs L126–133); `_NO_ROW` sentinel + `_interactions_by_key` are the push job's private copies of what `interact_with_alert.AlertInteractionHandler._find` does. · **Exact change:** a tiny `alerts/_ledger.py` with `subscriptions_by_user(repo)` and `interactions_by_key(repo, user_id)`; both jobs import it. · S · **execute**.
- **09-R13** · `NotificationsSettings.visiblePrefs` (L396–400) decides client-side which kinds are *relevant* (`meal_reconcile_overdue` only without auto-drain; `price_drop` only with money) while `/alerts/prefs` returns all eight regardless and the evaluator applies its own gates. · **Exact change:** `AlertPrefDto` gains `available: bool` computed server-side from the same gates the evaluator uses; the page filters on it. · S · **execute**.

### C3. Dead code / unused fields / unread endpoints
- **09-R14** · Stale comments: `get_alerts.AlertDto.kind` says "One of the six" (there are eight; `alert_kinds.py` says so); `alertApiService.ts:41` "Enable/disable a kind + override its tier" (tier override cut at Step-0 Q3); `suggestions.py` module docstring lists `DELETE /api/suggestions/suppression` while the route is `POST /unsuppress` (L275); `alertStore.ts:12` "Dora's 'what needs my attention?' intent" (check the assistant tool still reads the store — Chunk 11). · S · **execute**.
- **09-R15** · `AlertsDto.high_count / medium_count / low_count` — the SPA reads `high_count` and `medium_count` for the bell colour only; `low_count` and `fyi_count` have no reader (grep `low_count|fyi_count` in `web_app/src` → `models/alert.ts` + the store's `EMPTY`). · **Exact change:** drop `low_count` + `fyi_count` from the DTO + TS (keep `actionable_count`, `snoozed_count`); update `test__alerts__actionable_count_equals_high_plus_medium_in_items` if it reads them. · S · **execute**.
- **09-R16** · `suggestionsApiService.SuggestionKind` lists four kinds; the server emits six (`pantry_check`, `reconcile_meals_pending` missing) — the `string & {}` escape hatch hides it. · **Exact change:** add the two. · S · **execute**.
- **09-R17** · `AlertKindMeta.icon` is read only through `iconFor` and `ALERT_KIND_META[kind]?.icon`; `AlertKindAvatar` is the single consumer — fine. `kindTheme` fallback `''` renders an empty toggle label for an unknown kind in Settings; the bell degrades to a generic icon. · **Exact change:** fall back to the raw kind string in `kindLabel`. · S · **execute**.

### C4. Componentisation opportunities (R-001)
- **09-R18** · `DoraChat.vue:106–165` inlines the suggestion card (title · body · Why? · three buttons) — the one place suggestions render, but 60 lines of markup inside a 700+-line chat component. · **Exact change:** `SuggestionCard.vue` with `accept/snooze/dismiss` emits; `DoraChat` keeps the store wiring. · S · **execute** (Chunk 11 may fold it into its chat pass; record here, execute there).
- **09-R19** · `AdminSystemAlertsSettings.vue` is a 130-line page for **one** numeric field. With `default_days_until_stocktake_alert` gone, the page's title ("Alert thresholds", plural) and description ("…and the location heatmap for everyone; each account's own on/off and **priority preferences** layer on top") describe things that no longer exist (tier override cut; no heatmap). · **Exact change:** rename to *Expiring-soon window*, fix the description; or fold the one field into the Admin → System → Stock page. · S · **execute** (copy) / **conditional** (fold — Chunk 13's call).

### C5. Placement / standards (R-002, R-005, R-008, D-rules)
- **09-R20** · R-002 / 02-R37 — `AttentionRulesDialog.vue:258–259` uses Quasar `--q-negative` for the sample outline; the rest of the dialog is on tokens. `font-size: 0.85rem`, `padding: 8px 10px` literals (D-003). · S · **execute**.
- **09-R21** · D-003 — `NotificationsSettings.vue:486–488` `.settings-page__note { font-size: 0.8125rem; margin-top: 4px }`; `AdminSystemAlertsSettings.vue:128 margin: 8px 0`. · S · **execute** (Chunk 13 sweep).
- **09-R22** · R-008 — loggers: `get_alerts`, `act_on_alert`, `get_upcoming` build `_Logger` per request; `interact_with_alert`, `manage_alert_prefs`, `push_subscriptions` call `logging.getLogger(__name__)` inline; the two jobs use a local `log`. · S · **execute** (06-R41 class).
- **09-R23** · `prune_expired_snoozes` uses raw Core `delete(table)` via `db.metadata.tables` — justified (bulk delete; the repo has no bulk-delete port) and documented. · **waive**.
- **09-R24** · `AlertKindAvatar` `text-color="white"` on `severity-critical/-medium/-low` fills — FU-671's class; the severity tokens are "critical" ink-strength by name but D-002 wants a check in the pale themes. · **Exact change:** verify contrast; if any fails, `--text-on-severity-*` tokens. · S · **conditional** (measure; FU-671 sweep).
- **09-R25** · `get_alerts._no_planned_meals_alerts` formats a date range server-side (`strftime('%a %d %b')`, L403–404) — the 06-D1 / 03-R8 class (R-056). · **FU** (one cross-surface decision, already proposed in Chunk 6 E).

### C6. Naming & idiom
- **09-R26** · `generate_use_soon.reason` says "within the 3-day rescue horizon" with a literal 3 beside `_USE_SOON_HORIZON_DAYS = 3` (R-019). · S · **execute**.
- **09-R27** · `get_alerts.py` module docstring says "(C-9.1) … `read` stamped" and "read / snooze / dismiss" (L13–20) though read state was cut 2026-10-15. · S · **execute with 09-R14**.

### C7. Efficiency
- **09-R28** · Every bell poll (60 s per visible tab) runs the full evaluator: every stock item with its level, every open list, next week's entries, the reconcile queue, the user's watches + products, the user's interactions and prefs, plus a `User` read for the discard window. Household scale makes this fine, and the visibility gate stops background cost. · **waive** (note; if it ever matters, an `ETag` on `/alerts` is the cheap fix).
- **09-R29** · `send_alerts_push._process_user` re-evaluates alerts per subscribed user every hour — intended. · **waive**.
- **09-R30** · `generate_pantry_check` loads every open list's lines + a week of plan entries + the belief gather per suggestions call; `generate_likely_due` loads every archived list's lines. Suggestions refresh on bubble mount and on chat close only. · **waive** (bounded; note).

### C8. Design-level findings — out of Stage-2 scope
- **09-D1** · `DoraSuggestionSuppression` has no `user_id`: a dismiss or snooze by one household member hides the suggestion for all, while alert interactions are per user. The entity docstring says "a user's negative decision" but models a household one. Owner call: per-user (add the column, same shape as `AlertInteraction`) or keep household-wide and say so in the copy (B2-8 states the current behaviour). → **FU**.
- **09-D2** · Alerts and suggestions are two inboxes with overlapping kinds (09-R11) and two different dismiss semantics (episode vs condition). Step-0 cut the digest and the Alerts page; it did not ask whether the suggestions inbox survives as a separate concept now that the bell carries nudges. Record for the owner; no change proposed.
- **09-D3** · FU-702 / FU-701 — the *Expiring soon* chip on the stock page reads the pref-filtered `attention_kinds`, so a user who mutes the kind loses the filter; and the chip's label covers already-expired items. Both wait on the owner's wording call.
- **09-D4** · FU-700 — stocktake copy in `AttentionRulesDialog` ungated on the install switch.
- **09-D5** · FU-916 — `AlertInteraction` rows for finished episodes (and the daily-brief ledger keys) are never pruned; a nightly job beside `prune_expired_snoozes` is the natural home when it matters.
- **09-D6** · FU-917 — `PriceAlert.last_fired_at` dead, `threshold_unit_price` misnamed (Chunk 10 owns the entity).
- **09-D7** · FU-627 — deals-email section ignores the install-wide `deals_email` admin flag.

### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `pywebpush` wrapper (`push_sender.py`) | web push | — | **keep** | — | Already a library; dry-run mode is the right local story. |
| `push-sw.js` hand-written SW | service worker | Workbox | **keep** | — | Push-only, 90 lines, coexists with the PWA SW; Workbox adds nothing here. |
| APScheduler `BackgroundScheduler` in-process | scheduling | Celery / cron | **keep** | — | Single-worker constraint documented; externalising is the SaaS tail. |
| Derived alerts (no stored alert rows) + interaction ledger | event model | a notifications table | **keep** | — | The proposal's central decision; it is what makes "one rule" possible. |
| `_select_for_display` fairness | ranking | — | **keep** | — | Pure, tested (FU-593). |
| `urlBase64ToUint8Array` | base64url | a lib | **keep** | — | 8 lines, the canonical snippet. |

### C10. Standards drift (R-0NN)
- **R-003** · 09-R2, 09-R5, 09-R6, 09-R10, 09-R12, 09-R13 — fix; 09-R11 conditional.
- **R-008** · 09-R9, 09-R22 — fix.
- **R-019** · 09-R14, 09-R26, 09-R27 — fix.
- **R-021** · all evaluators anchor on `household_today`; the jobs self-gate on the household clock — clean.
- **R-031** · 09-R7 — fix.
- **R-032 / FU-684** · `get_alerts` reads `item.stock_level` through `is_essential_low` with an include (L181–184, L527) — the same exposure `stock_attention`/`get_stock_items` carry; 07-R2's `levels_by_item` pattern applies when FU-684 executes. → tracked.
- **R-056 / D-006** · 09-R1 — fix; 09-R25 → FU.
- **R-002 / D-003** · 09-R20, 09-R21 — fix; **FU-671** 09-R24 conditional.
- **FU-654** · 09-R4 — five more copies.
- **R-057** · 09-R15, 09-R16 — inventory executed.
- **R-029** (hide when off) · price-watch toggle and section follow `moneyEnabled`; push toggle disabled-with-reason rather than hidden (owner precedent) — clean.

### C11. Ride-along signals for FU-010 / FU-224
- Bell badge: `color-mix(--semantic-negative 65%, black)` to hold white text ≥ 6:1 in dark themes — a bespoke darkening with no token; FU-224 should decide whether a `--semantic-negative-strong` token exists for this.
- `AlertKindAvatar` severity circles with white glyphs — the one place `severity-*` is used as a fill under white (09-R24).
- Dora bubble suggestion badge `negative`/`primary` palette names.

## D. Test plan — Alerts + Suggestions

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `test__suggestions__no_string_carries_a_currency_symbol` | pytest e2e (`test_suggestions_router.py`) | **must-write-before-ship** | 09-R1 — the verdict's precedent, for the other inbox. |
| `test__likely_due__uses_cadence_math` (same inputs → same gap as `mean_gap_days`) | pytest unit | nice-to-have | 09-R2. |
| `test__alert_prefs__available_follows_the_evaluator_gates` (money off → `price_drop.available is False`) | pytest e2e | nice-to-have | 09-R13. |
| `attentionRulesCheatSheet.spec.ts` — derived rows equal the former hand table | vitest | housekeeping | 09-R10. |
| `alertStore.spec.ts` — drop `low_count`/`fyi_count` from `EMPTY` | vitest | housekeeping | 09-R15. |

Not proposed: anything for push delivery beyond the existing eight (`test_alerts_push.py`), the brief hour gate (covered in `test_daily_brief*.py`, Chunk 2), or the bell polling (drive once).

## E. Proposed follow-ups (orchestrator allocates ids)

- type=finding · *Suggestion suppression is household-wide while alert interactions are per user* (09-D1) — owner decision; S if per-user (add `user_id`, same shape as `AlertInteraction`).
- type=finding · *Reconcile nudge is generated as both an alert kind and a suggestion* (09-R11 / 09-D2) — owner decision on which inbox owns nudges; execute the deletion once decided.
- Existing FUs this chunk executes against: **FU-654 / 02-R12** (09-R4), **FU-683 D3** (09-R2), **FU-759 / 06-R15** (09-R6), **06-R41** (09-R22), **FU-671** (09-R24, conditional).
- Existing FUs referenced, unchanged: FU-916, 917, 702, 701, 700, 627, 624, 684.
- Cross-surface FU already proposed (Chunk 6 E, server-formatted dates in prose): add `get_alerts._no_planned_meals_alerts` (09-R25) to its site list.

## F. Summary for the register

- FST rows: 10 golden + 15 edge + 5 gate · Help entries: 9 new (a new **Alerts & notifications** group — none existed) + 2 copy fixes in `AttentionRulesDialog` + DoraBot paragraph extended · Review findings: 30 (execute 21 / FU 1 / waive 4 / conditional 4 / design-record 7) · Tests: 5 (must-write 1) · Bugs: 9 (over-budget suggestion hardcodes `$` five times; a fourth mean-gap implementation; "Review budget" lands on the Appearance page; five more session-user copies; the default snooze length written in four places; a second install-setting read; two sessions per request in two handlers; a hand-shaped 404; `.all()[0]` for `.one()`)
- One-line: the alerts rework landed where the Step-0 principle pointed — one evaluator, derived tiers, episode keys, per-user switches, honest push — and the leftovers are small and local; the real remaining question is structural and the owner's: whether Dora's **suggestions** inbox (household-wide dismiss, two kinds that duplicate alert kinds, dollar-formatted on the server) still earns its place beside the bell.

### Feedback coverage — `# ALERTS` (L436–442) + the Step-0 principle

| # | Feedback bullet | Where it lives now | State |
|---|---|---|---|
| AL1 | An alert control screen feels missing | Built as `/alerts` (C-9.3), then **cut** 2026-10-15 once its toggles moved to Settings → Notifications and the bell rows gained their buttons; `/alerts` redirects to `?alerts=open` | 📦 superseded (bell + Notifications) |
| AL2 | Badge doesn't add up (6 vs 10) | `actionable_count` server-derived = high+medium; FYI listed, never counted; pinned by e2e + `alertStore.spec` | ✅ done |
| AL3 | Alerts could be smarter about priority / what's an alert | Step-0: three kinds cut, severity the one scale, tier derived, episodes | ✅ done |
| AL4 | Opt in/out per type — as quiet or noisy as they want | per-user `AlertPreference` on/off, applied everywhere | ✅ done |
| AL5 | Alert for "no planned meals for next week" | `no_planned_meals` (FYI, ISO-week episode) | ✅ done |
| — | Owner 2026-10-15: "well-defined points when alerts appear and disappear" | episode keys (`alert_key.py`), `started_on`, discard window | ✅ done |
| — | Owner 2026-10-15/17: dismiss only, cards with the thing's buttons, log waste on expired | `AlertRow`, `useLogWaste` | ✅ done |
