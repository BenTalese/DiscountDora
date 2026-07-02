# Dashy Dora — Champion Vision & Prompt Plan (Part 8)

> **Doc library:** see [PROJECT_STATE.md](../../PROJECT_STATE.md) (front door + document register). The **Dora Decision Charter** (Part II) and the verify-state-first procedure (Part III) in this doc govern the entire library.

A single-file strategic report **and** prompt plan for turning Discount Dora into
**Dashy Dora**, the category champion. Companion to the earlier docs
(PROMPT_PLAN_PART_6_POLISH = the closed loop; PROMPT_PLAN_PART_7_COMMERCIALIZATION =
de-risk + SaaS; COMMERCIALIZATION_REPORT). Read those first where dependencies are
called out.

> **How to use this file:** Part I is the report (the *why*). Part II is the **Dora
> Decision Charter** — the rubric every agent must obey. Part III is the **mandatory
> operating procedure** for running any prompt (verify-state-first + charter-check).
> Part IV is the **prompt plan**. Part V is sequencing. The prompts are deliberately
> written to *survive drift*: each one re-checks reality before acting.

---

# PART I — Strategic Report

## 1. The name: Dashy Dora (settled)

- **Dashy Dora** replaces "Discount Dora." Same two-trochee cadence (DASH-y DO-ra),
  keeps the D.D. alliteration.
- **Why it fits:** "dash" = a culinary measure (food), *and* speed/effortlessness
  (the founding promise), *and* a touch of flair ("dashing"). It also drops the
  "Discount" promise we can no longer keep (central deal scraping is being removed —
  see Part 7 / COMMERCIALIZATION_REPORT §1–2).
- **Coined-word upside:** easier to trademark + secure a clean `.com` than a real word.
- **Tagline directions:** *"A dash of Dora."* · *"Your pantry, sorted in a dash."* ·
  *"Never overpay, never run out."*
- **Logo:** keep the burger; add a "dash"/motion or *"a dash of"* garnish accent to
  nudge it from "fast food" toward "fast + fresh."
- **Caveats:** run a trademark search (software class), keep the visual identity clear
  of *Dora the Explorer*, grab `dashydora.com` + handles.

## 2. Competitive landscape (researched June 2026)

Three camps; **Dora uniquely spans all three**, which is the entire opportunity.

**Price/deal (AU) — the camp we are leaving:**
- WiseList (~$5/mo, 350k users, **now adding pantry + AI + receipt scanning** — the
  real convergence threat), Frugl (free; stale/inaccurate prices, missing unit prices),
  Zyft (650k users, in-aisle barcode compare), Bargeroo/Save On/GroceryWise.

**Pantry/inventory trackers:**
- KitchenPal (free), Pantry Check (free + IAP to 10k items), NoWaste ($7/yr; wrong
  scanned expiries), **Grocy** (self-hosted, powerful but overwhelming — our original
  foil).

**Meal/list/recipe:**
- AnyList ($9.99/yr indiv, **$14.99/yr household** — the pricing anchor; best shared
  lists), Samsung Food ($6.99/mo; recipes + AI + nutrition + fridge sync), Paprika,
  Mealime.

## 3. The unifying insight (the war we're actually in)

Every camp dies of the **same disease**:

- **Trackers die of maintenance burden.** Grocy review: users felt *"they were working
  for Grocy rather than it working for them."* The fatal flaw of all barcode pantries:
  *"scanning in is easy; remembering to scan out half a can of chickpeas? Nobody does
  that."* Inventory drifts → goes wrong → abandoned.
- **Deal apps die of staleness/inaccuracy.** Generic scraped prices don't match shelves.
- **Meal/list apps are shallow** — no pantry, no prices.

**The category graveyard is full of apps that asked the user to do more work than the
value returned, or fed them data too stale to trust.** That — not "more deals" — is the
battle.

## 4. The champion vision — three pillars

**Pillar 1 — Effortlessness is the killer feature.** Dora is architected *not* to die of
the maintenance disease:
- Coarse stock flags (Out/Low/Stocked), not exact counts → drift-tolerant by design.
- Cook→consume (P6-07) captures consumption automatically → solves the scan-out problem
  *nobody else solves*.
- Confidence + decision-driven stocktake (P6-13) → self-correcting and honest.
- Reconciliation (P6-01), self-drafting shop (P6-10), barcode-to-add → strips input work.
- Positioning: **"Every other pantry app makes you work for it. Dashy Dora works for you."**

**Pillar 2 — The closed loop = features single-camp apps structurally cannot build.**
should-I-buy oracle, deal/expiry-driven meals, week costing, daily briefing. Only Dora
holds pantry + recipes + consumption + personal prices together.

**Pillar 3 — Personal accuracy + ownership.** Personal price history is always accurate
*for you* (beats stale scraped data). Self-hosted / your-data / no-ads / BYO-LLM is a
defensible niche none of these serve.

## 5. Threats we must beat (honest)

1. **WiseList convergence** (integrated + AI + 350k users + native app) → out-execute on
   effortlessness, the *true* loop, and ownership; not on deal breadth.
2. **No native app (PWA only)** → the #1 structural must-fix; "effortless" rings hollow
   vs native barcode apps until closed.
3. **Input friction** without barcode-to-add → trackers beat us on first-entry speed.
4. **Cheap market** (AnyList $15/yr) → justify premium via the loop + ownership, or price
   aggressively.

## 6. Novel features (invented for Dora; do not exist elsewhere)

- **⭐ The Zero-Input Pantry (inferred inventory)** — the flagship. Dora does **not** ask
  you to maintain inventory; it infers a confidence-weighted *belief* about your kitchen
  from the loop (purchases + cooking + cadence + recipe draw-down) and only asks a tiny,
  targeted question when a real decision depends on it. Flips the category's founding
  assumption ("log everything") to "log nothing; I'll infer and ask only when it
  matters." Only possible because Dora holds the whole loop. Tagline: **"The pantry app
  you never have to update."**
- **Wait-or-Buy personal price oracle** — advises *your* best time to buy from *your*
  cadence + price history (+ optional crowd). Personalised; doesn't exist for groceries.
- **Household culinary memory** — the compounding moat: years of meals, prices, rhythms,
  preferences → irreplaceable, and impossible for ad-driven rivals who monetise the data.
- **The Dora Score** — a single self-running-kitchen health metric (low waste, on-budget,
  fresh, few run-outs) that makes the invisible loop work visible and gently game-able.

## 7. The one-sentence vision

**Dashy Dora is the only grocery app that maintains itself and thinks across your whole
kitchen — coarse-by-design so it never drifts, self-correcting so it stays true, personal
so its prices are always right, and yours so your data never becomes the product —
winning not on the most deals, but on being the one app in the category that doesn't make
you work for it.**

---

# PART II — The Dora Decision Charter (the rubric every agent must obey)

> Every prompt below requires the agent to make design choices. **Those choices must be
> checked against this charter.** If a proposed change violates a principle, the agent
> must choose a different approach or PAUSE and flag it — never silently ship something
> off-vision. When a decision is ambiguous or trades one principle against another, the
> agent must stop and surface the trade-off rather than guess.

1. **Effortless above all.** It works for the user; the user never works for it. Reject
   anything that adds recurring manual burden (the disease that kills the whole category).
2. **Coarse-by-design.** Prefer bands/flags over exact counts; robustness over precision.
   Drift-tolerance beats false accuracy.
3. **Self-correcting & honest.** Surface confidence/staleness; never let the app silently
   go wrong. An honest "I'm not sure, quick check?" beats a confident wrong answer.
4. **Personal beats generic.** Personal price history and patterns beat scraped/generic
   data. Relevance over breadth.
5. **Leverage the closed loop.** Features should use *and strengthen* the
   pantry↔recipes↔meals↔lists↔prices↔consumption loop. Prefer connecting silos over
   adding new ones.
6. **Every insight leads to one action.** No dead-end notifications.
7. **Preview → approve → commit. Undoable. Explainable.** No silent writes; always show
   *why*.
8. **Ownership & privacy.** The user's data is theirs — no ads, never sold; local-first /
   BYO where possible; anything external is opt-in and documented.
9. **No legal-risk data sourcing.** No central scraping of retailers. Price/product data
   comes only from the user, their personal history, their loyalty/email, opt-in crowd
   contribution, or open data (e.g. Open Food Facts).
10. **Anti-feature-creep (anti-Grocy).** If a feature adds surface area without clearly
    serving the vision, cut it. Niche features default OFF. Simplicity is a feature.
11. **Fast & frictionless UX.** Speed is a feature. Mobile-first / one-handed where the
    usage context calls for it.
12. **Don't invent facts.** AI features use real app data and tool calls only.

**Tie-breaker:** when principles conflict (e.g. a useful feature adds some burden), favour
**Effortless (1)** and **Anti-creep (10)** — being the app that doesn't make you work is
the whole strategy.

---

# PART III — Mandatory operating procedure (apply to EVERY prompt)

Each prompt in Part IV is written assuming the codebase **will have drifted** since this
file was written. Before building anything, every agent MUST run these two steps and
state their findings:

### STEP 0 — VERIFY CURRENT STATE (do this first, every time)
1. Read the **top entry of `DORA_WORKLOG.md`** (canonical "where we are") and **`CHANGELOG.md`** (product-level history) for current implementation state. The legacy `STATUS.md` audit lives at `docs/06_legacy_prompt_plans/STATUS.md` for historical reference only — it was last regenerated 2026-05-27 and is not authoritative.
2. Read the **prior prompt plans** (PROMPT_PLAN_PART_6 / _7) to see what this prompt
   depends on and whether those dependencies are actually built yet.
3. Read the **actual code** named in the prompt's READ list and confirm the files,
   features, tables, routes, and entities still exist and behave as the prompt assumes.
4. **Reconcile prompt vs reality.** Explicitly note any drift (renamed/removed/changed
   things — e.g. the substitute graph and stock map were *removed*; locations is now a
   simple tree; "Discount Dora" may already be "Dashy Dora"; product barcodes were
   removed). If the prompt's assumptions are stale, **adapt the plan to the current code
   and say how** — do not blindly execute stale instructions.
5. Confirm **dependencies are present.** If a prerequisite (e.g. P6-01 price history,
   P6-07 cook→consume, P7-01 de-risk) is missing, STOP and report what's needed rather
   than building on a missing foundation.

### STEP 1 — CHARTER CHECK (before and after design)
- Before building: state how the planned approach honours the **Dora Decision Charter**
  (Part II), and confirm it violates none. If it does, pick another approach or PAUSE.
- While building: prefer the option that maximises Effortless (1) and Anti-creep (10).
- In the DONE WHEN: include *"design decisions documented against the Charter; no
  principle violated (or trade-offs explicitly surfaced and approved)."*

### Cross-cutting build rules
- Preview → approve → commit; undoable; explainable. Never log secrets/PII.
- Read CHANGELOG.md after landing; update it; adjust downstream prompts if code drifted.
- Do not rewrite the framework (no FastAPI/C#). Productionize what exists.

---

# PART IV — The Prompt Plan (Part 8)

> Every prompt begins with STEP 0 + STEP 1 from Part III. The READ lists below are the
> *starting points* for STEP 0, not the full extent — follow the code where it leads.

## P8-01 — Rebrand: Discount Dora → Dashy Dora

```
Rename the product from "Discount Dora" to "Dashy Dora" across the codebase and assets,
and adjust positioning copy away from "deals/discounts" toward "effortless pantry +
never overpay" (Charter 1, 4).

STEP 0 (verify state): grep the whole repo for "Discount Dora", "DiscountDora",
"Discount", "discount" (code, README, docs, package names, manifest, PWA name, email
templates, the prompt plans). Establish every place the old name/brand promise appears.
Read README.md and web_app PWA manifest/app title.

STEP 1 (charter): the new copy must not promise central deal scraping (Charter 9). Lead
with effortlessness + personal value, not store-deal comparison.

DO:
- Replace user-facing "Discount Dora" → "Dashy Dora" (app title, PWA manifest, README,
  email templates, help copy). Keep internal package/module names if renaming them is
  risky — note any left for a follow-up.
- Update the tagline/positioning copy (Part I §1). Remove "compare store prices" claims.
- Logo: document the "burger + dash accent" direction for the designer (no need to
  produce final art); update the favicon/app-icon references if a new asset is provided.

DONE WHEN:
- No user-facing "Discount Dora" remains; the app presents as "Dashy Dora".
- Positioning copy no longer promises store-deal comparison.
- Decisions documented against the Charter. Lint/typecheck/build green. CHANGELOG updated.
```

## P8-02 — Effortless input: barcode-to-add via Open Food Facts

```
Let users scan a packaged product's barcode to instantly add a pantry item with name /
category / image pre-filled, using the OPEN, free Open Food Facts database. This is a
fast-INPUT feature (Charter 1, 11), legally clean (Charter 9, open data), and DISTINCT
from the removed product-barcode-for-deals subsystem.

STEP 0 (verify state): confirm the product-barcode/deal subsystem is removed (it was) but
the QR ScanOverlay camera component still exists and works. Read web_app ScanOverlay.vue,
the stock-item create flow, and dora_api stock_items create. Confirm whether QR scanning
is behind the off-by-default qr_labels_enabled flag and how scanning is surfaced.

STEP 1 (charter): scan-to-add must REDUCE effort, not add a maintenance loop. Coarse model
stays (Charter 2) — scanning sets name/category and an initial stock level, not exact
counts. Open Food Facts data is a SUGGESTION the user confirms (Charter 3, 7).

DO:
- Add an Open Food Facts lookup service (by EAN). Cache results locally. Handle "unknown
  barcode" gracefully → fall back to manual name entry (no dead end).
- Extend the scanner/add-item flow: scan packaging → pre-fill name, category, image →
  one-tap confirm into the pantry at a chosen stock level. Never silently write.
- Do NOT resurrect EAN→merchant-product mapping or any deal lookup. This is add-only.

DONE WHEN:
- Scanning a real product barcode pre-fills a confirmable new pantry item from Open Food
  Facts; unknown barcodes fall back to manual entry cleanly.
- No deal/merchant lookup is reintroduced.
- Charter documented. pytest covers lookup + unknown fallback. Lint/typecheck green.
  CHANGELOG updated.
```

## P8-03 — Automatic prices, legally: loyalty + email ingestion

```
Bring real prices and purchases in automatically WITHOUT scraping retailers, by parsing
the user's own loyalty/offer emails and online-order confirmation emails (Charter 9, 1).
Feeds the personal price history that powers P6-03 and the oracles below.

STEP 0 (verify state): confirm P6-01 (paid_price / purchase_events) and P7-01 (de-risk:
personal price history) exist — if not, STOP and flag, since this feeds them. Read the
emailer service, P6-01 reconciliation, and the price-history store.

STEP 1 (charter): opt-in, documented, user's own data (Charter 8). Parsed rows are
confirmable suggestions, not silent writes (Charter 7). No credential storage / no
portal scraping (Charter 9).

DO:
- Inbound-email ingestion: a per-user forwarding address (or inbound webhook via the mail
  provider). Parse, per source, into the existing P6-01 reconciliation preview:
  - Online-order confirmation emails (Coles/Woolworths) → itemized purchases + prices.
  - Loyalty offer emails (Everyday Rewards / Flybuys) → personalized offers on items the
    user buys → surface as suggestions (Charter 6: each links to add-to-list).
- Provider-shaped parsers (one per source) so more can be added. Confirm before commit.
- Explicitly DO NOT log into or scrape loyalty portals; email only.

DONE WHEN:
- A forwarded sample order email yields a correct reconciliation preview; a sample offer
  email yields actionable suggestions.
- All ingestion is opt-in; nothing is written without confirmation; no credentials handled.
- Charter documented. pytest covers one fixture per parser. CHANGELOG updated.
```

## P8-04 — Crowd-sourced price graph (opt-in, privacy-preserving)

```
Build an opt-in community price graph so users (and especially new users with no history)
get a price baseline — from facts users contribute, never from scraping (Charter 9, 4).

STEP 0 (verify state): read the (de-risked) products/price-history features and how
personal prices are stored. Confirm there is no remaining central scraper to entangle
with. Check whether households/tenancy (P7-A1) exists, as contributions may be
household-scoped.

STEP 1 (charter): opt-in and privacy-preserving (Charter 8) — contributions are
anonymised facts (item, price, store, date/region), never tied to identity in the shared
graph. Personal data stays personal; only the user CHOOSES to contribute.

DO:
- Let a user optionally contribute a logged price (item + price + store + coarse
  region/date) to a shared graph. Aggregate to community medians/lows per item+store+region.
- Surface community baselines ONLY where the user lacks personal history ("others near you
  pay ~$X"), clearly labelled as community data (Charter 3). Personal history always wins.
- Basic abuse/quality controls (outlier rejection); no PII in the shared store.

DONE WHEN:
- A user can opt in, contribute, and see community baselines where they lack personal data;
  opting out removes their contributions.
- No PII in the shared graph; personal prices take precedence over community.
- Charter documented. pytest covers aggregation + outlier rejection + opt-out. CHANGELOG.
```

## P8-05 — The "Should I Buy This?" oracle (in-aisle decision engine)

```
Build the in-aisle decision feature: the user checks an item and Dora answers using THEIR
data — a decision, not a deal feed (Charter 4, 5, 6). A flagship differentiator no
single-camp competitor can build.

STEP 0 (verify state): confirm the inputs exist — personal price intelligence (P6-03 /
P7-01), stock level + run-out signal (P6-04), waste signal (P6-06), purchase cadence
(P6-01). If key inputs are missing, STOP and report. Read the assistant tools
(purchase_price_stats, pantry_health) and the mobile/shop surfaces.

STEP 1 (charter): the answer must be explainable (Charter 7) and honest about confidence
(Charter 3). One-tap action attached (Charter 6).

DO:
- A "should I buy this?" check (by item search, or scan via P8-02): Dora returns a verdict
  + reason synthesised from the user's data:
  - price verdict ("cheapest you've paid in 3 months" / "you usually pay less"),
  - need verdict (current level + predicted run-out),
  - waste warning ("you waste this ~60% of the time — still stocked"),
  - confidence + the data behind it.
- Verdict → one-tap action (add to list / skip / mark stocked). Mobile-first, one-handed.

DONE WHEN:
- Checking/scanning an item returns a personal buy/skip verdict with reasons, confidence,
  and a one-tap action; degrades gracefully with thin data (Charter 3).
- Uses only the user's own data (no scraping). Charter documented. pytest covers verdict
  logic across price/need/waste cases. CHANGELOG updated.
```

## P8-06 — Wait-or-Buy personal price oracle

```
Advise the user's BEST TIME to buy from their own purchase cadence + price history (+
optional crowd), e.g. "don't buy now — you usually hit a lower price ~fortnightly"
(Charter 4). Novel; doesn't exist for groceries.

STEP 0 (verify state): confirm personal price history (P6-03/P7-01) and cadence
(P6-01/P6-04) exist with enough depth. Read purchase_price_stats and the price-history
store. If crowd data (P8-04) is absent, design to work on personal data alone.

STEP 1 (charter): only advise when confidence is real (Charter 3); never fabricate a
cycle from one data point. Explain the basis (Charter 7).

DO:
- Detect personal price cycles / typical low points per item from price history + cadence.
- Produce a wait/buy recommendation with the basis ("your last 4 buys were lower than this;
  your usual low lands ~end of fortnight"). Optionally blend crowd baselines (P8-04).
- Surface in item detail and within the should-I-buy oracle (P8-05). Stay silent (low
  confidence) when history is thin.

DONE WHEN:
- For an item with enough history, Dora gives a wait/buy call with a clear basis; stays
  quiet on thin data.
- Charter documented. pytest covers cycle detection + thin-data silence. CHANGELOG updated.
```

## P8-07 — ⭐ The Zero-Input Pantry (inferred inventory) — FLAGSHIP

```
Build the category-defining feature: an inventory the user NEVER maintains. Dora holds a
confidence-weighted BELIEF about what's in the kitchen, inferred from the closed loop, and
asks a tiny targeted question only when a real decision depends on it. This is the purest
expression of the vision (Charter 1, 2, 3, 5). Read Part I §6 before building.

STEP 0 (verify state): this is the crown on the P6 loop — CONFIRM these exist and report
if not: P6-01 reconciliation (intake), P6-07 cook→consume (depletion), P6-04 run-out
prediction (cadence), P6-13 confidence/decision-driven stocktake (correction). If any are
missing, STOP — do not build inference on a missing foundation. Read the stock_item model
(coarse StockLevel flags, last_checked_at, stock_level_last_updated) and the suggestion
inbox.

STEP 1 (charter): MUST be coarse (Charter 2 — infer a BAND/flag, never a fake exact
count), MUST be honest (Charter 3 — show confidence + the reasoning), MUST reduce effort
(Charter 1 — replace logging, do not add a new logging chore). A confidently-wrong
inference is worse than none — design for humble uncertainty.

DO:
- An inference service that maintains, per stock item, a probabilistic belief about its
  level (Out/Low/Stocked band) + a confidence, derived from: last purchase + cadence
  (P6-04), cooking depletion (P6-07), reconciliation intake (P6-01), and time decay.
- Make inferred levels the DEFAULT the user sees, clearly marked as inferred with their
  basis ("~Low — bought 11 days ago, you usually finish in ~14"). Manual overrides always
  win and reset confidence.
- "Ask only when it matters": when a decision (recipe suggestion, deal/should-I-buy, shop
  draft) hinges on an uncertain item, surface a single targeted quick-check (reuse P6-13)
  — never bulk prompts.
- Provide a clear way to see/trust the inference, and an off switch (Charter 10 — some
  users want manual control).

DONE WHEN:
- A new pantry item's level updates itself from purchases + cooking + time WITHOUT manual
  logging; the UI shows the inferred band, confidence, and reason.
- Decisions that depend on an uncertain item trigger a single targeted quick-check, not a
  bulk prompt; manual overrides win and persist.
- Inference is coarse (band, not count) and never presents a confident wrong answer
  without a confidence cue.
- Charter documented (this prompt is the charter's flagship — call out how each principle
  is honoured). pytest covers belief updates from each signal, time-decay, override
  precedence, and the ask-only-when-it-matters trigger. CHANGELOG updated.
```

## P8-08 — The Dora Score (self-running-kitchen health metric)

```
Add a single, honest score for how well the kitchen is running — making the invisible
closed-loop value visible and gently game-able (Charter 5, 6).

STEP 0 (verify state): confirm the input signals exist — waste (P6-06), budget (P6-09 /
budget feature), run-outs/stock freshness (alerts, P6-04), stocktake confidence (P6-13).
Read the reports feature and DashboardPage.

STEP 1 (charter): the score must be honest and explainable (Charter 3, 7) and must never
nag or shame (Charter 1 — it should feel good, not like a chore). Each component links to
an action (Charter 6).

DO:
- Compute a Dora Score from: low waste, on-budget, stock freshness, few unplanned
  run-outs, low staleness. Show the breakdown + trend ("waste down $4 this month").
- Each weak component links to the feature that improves it (waste→expiry rescue,
  budget→swaps, run-outs→self-drafting shop). Surface on the dashboard.

DONE WHEN:
- A Dora Score with an explainable breakdown + trend appears; each component links to a
  remediating action; tone is encouraging, never nagging.
- Charter documented. pytest covers score computation + component→action wiring. CHANGELOG.
```

## P8-09 — Household culinary memory (the long-term moat)

```
Make Dora the persistent memory of how the household eats — a compounding, irreplaceable
asset and switching-cost moat (Part I §6; Charter 8 — the user owns it).

STEP 0 (verify state): confirm households/tenancy state (P6-05 / P7-A1) and the data that
accumulates — cooked meals (P6-07 consumption_events), prices paid (P6-01), meal plans,
preferences. Read those stores. If households aren't built, scope to single-user memory
and note the household extension.

STEP 1 (charter): the memory is the user's, never sold (Charter 8). Recall must be useful,
not clutter (Charter 10).

DO:
- A "memory" / history surface that answers recall questions over time: meals cooked
  (and when, and who liked them), price history per item, seasonal/occasion patterns
  ("what did we make last Christmas?"), spend trends ("dairy up 8% over 2 years").
- Make it queryable via the assistant (compose existing tools; no invented facts —
  Charter 12). Lightweight, searchable, not a heavy new module.

DONE WHEN:
- Users can recall past meals, prices, and patterns over time via a memory surface and the
  assistant; it draws only on real stored data.
- Charter documented. pytest covers recall queries over fixture history. CHANGELOG updated.
```

## P8-10 — Native mobile app (close the #1 structural gap)

```
Ship Dora as a real native mobile app, not just a PWA — the top structural gap vs every
competitor (Part I §5). Wrap the existing SPA rather than rewriting (Charter 11; do not
rewrite the framework).

STEP 0 (verify state): read the web_app build/PWA setup, the ScanOverlay camera usage, and
any existing mobile/offline infra (M1 PWA, shop mode). Determine the lightest wrapper that
fits the stack (e.g. Capacitor wrapping the built SPA) and what native bridges are needed
(camera for P8-02/05, push notifications, wake lock).

STEP 1 (charter): the native app must make the experience FASTER/easier (Charter 1, 11),
add push for proactive value (Charter 6 — alerts/suggestions become actionable
notifications), and not fork the codebase (one SPA, wrapped).

DO:
- Wrap the SPA in a native shell (Capacitor or equivalent) for iOS/Android; reuse the SPA.
- Wire native camera (for barcode-to-add / should-I-buy), push notifications (proactive
  alerts, deal-for-you, run-out, expiry), and wake lock (shop mode).
- Keep self-hosted/server config working (point the app at the user's instance or the SaaS).
- Set up the store listing scaffolding (icons, names = Dashy Dora, screenshots).

DONE WHEN:
- A native iOS/Android build wraps the SPA, with working camera + push + wake lock, pointing
  at a configurable backend.
- One codebase (no SPA fork). Charter documented. Build instructions in docs. CHANGELOG.
```

---

# PART V — Sequencing

This plan assumes the **P6 closed loop** and **P7-01 de-risk** are built or in progress —
much of Part 8 depends on them. Each prompt's STEP 0 must confirm this and STOP if a
foundation is missing.

Recommended order:

1. **P8-01 Rebrand** — cheap, foundational identity. Do first.
2. **P8-02 Barcode-to-add** — closes the input-friction gap; quick competitive parity win.
3. **P8-03 Loyalty/email ingestion** → **P8-04 Crowd prices** — feed personal + community
   price data (P8-03 before P8-04; both depend on P6-01/P7-01).
4. **P8-05 Should-I-Buy oracle** → **P8-06 Wait-or-Buy oracle** — the decision features;
   depend on the price data above + P6-03/P6-04.
5. **P8-07 Zero-Input Pantry (FLAGSHIP)** — only after the P6 loop (P6-01/04/07/13) is
   solid. This is the crown; don't rush it onto a shaky foundation.
6. **P8-08 Dora Score** → **P8-09 Culinary memory** — engagement + moat; depend on
   accumulated loop data.
7. **P8-10 Native app** — high priority and fairly independent; can run in parallel with
   the data/feature work since it wraps the SPA. Schedule it early enough that the
   above features are tested on-device.

**Do not run in parallel** any two prompts touching the same tables/stores (e.g. P8-03 and
P8-04 both touch price data; P8-07 touches everything in the loop). And above all: **every
prompt verifies current state first (Part III) and checks every decision against the Dora
Decision Charter (Part II).** That is how this stays true to the vision as the code drifts
beneath it — and how Dashy Dora becomes the champion, not just another app that makes you
work for it.
