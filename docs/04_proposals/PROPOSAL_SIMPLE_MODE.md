# Simple Mode — minimal user as a first-class workflow

**Status:** proposal, ready for co-design.
**Promotes:** `99_scratch/MINIMAL_USER_PRODUCTS_OFF_FRICTION.md` (the
talk-time assessment + the 2026-06-15 brainstorm addendum).
**Closes / consumes:** FU-182 (this is its promoted form).
**Depends on:** FU-189 (Stores rename + management + uploads), FU-190
(ingestion API no-auto-create).
**Amends:** PROPOSAL_CONFIG_AND_OPTINS.md §2.6 (elevates `products_enabled`
from one candidate flag among several to *the* app-shaping flag), and
points at the C-5 v3 onboarding redesign which already lands the upstream
persona + flag.

**Anchor principle:** *Minimal users must be supported as much as power
users — same charter-level care, not a degraded fallback.* Charter
tiebreakers Effortless + Anti-creep both lean toward a clean, complete
minimal experience as the default for new users; this proposal defines
what "complete" actually means surface by surface.

---

## 1. Re-grounding (verified against live code + in-flight design)

**What exists today:**
- `Product` + `ProductOffer` + the `StockItemProduct` m2m underpin price
  history, the stock-value report, recipe cost estimates, the shopping-list
  offer picker / cheapest-merchant sort, the cart button, the deals email,
  the My Products page, Product Search, and the (Phase 2) ingestion API.
- The codebase still says "merchant" everywhere; merchants are name-only
  records referenced by `ProductOffer`.
- `AppSetting` already holds install-level flags (e.g. `llm_enabled`); the
  C-cross §2.6 feature-flag panel pattern is established.
- Per-user money opt-in (PROPOSAL_CONFIG_AND_OPTINS §2.2) is designed but
  not built — it governs *personal* visibility of dollar surfaces.

**What's in flight (do not re-design here):**
- `IMPL_PLAN_ONBOARDING.md` C-5.3 introduces the **`products_enabled`**
  install flag plus the **3-persona fork** (Cooking / Savings / Everything)
  that sets it. Cooking persona = `products_enabled` off; it also branches
  the wizard to skip the stock-item-vs-product explainer.
- `PROPOSAL_ONBOARDING.md` §3.3 owns the *explainer step copy*; this
  proposal supplies the milk-example wording it adopts.
- `PROPOSAL_HELP_OVERLAY.md` §2.3 owns the *glossary entry*; this proposal
  defines its content.

**What this proposal owns:**
- The data-model substrate that makes "Products off" a clean mode rather
  than a hole.
- The per-surface sweep of what disappears, what collapses, and what
  replaces it when `products_enabled` is off.
- The "Simple mode" identity decoupled from the technical flag name.
- The Money + Products independence (the 2×2) and how onboarding personas
  must reach all four cells.

---

## 2. The design

### 2.1 The pricing substrate — unify the read path, don't flatten

**Reframe:** `StockItem` + new `StockItemPriceObservation` is the universal
substrate for price data. `Product` + `ProductOffer` is an optional
SKU-resolution overlay that *feeds* the same substrate.

```
StockItemPriceObservation:
  stock_item_id    (FK, required)
  price            (decimal, required)
  qty              (decimal, required)
  unit             (string, required — matches stock-item unit conventions)
  observed_at      (datetime, required)
  source           (enum: 'manual' | 'shopping_close_out' | 'product_offer')
  # NO merchant — see §2.6
```

Stock-item price-history chart reads:
- **Products off:** direct observations only.
- **Products on:** `direct observations ∪ observations-derived-from-linked-
  products` (offers per `StockItemProduct` m2m, reduced to per-time price
  points).

This means every consumer (cost estimates, stock-value report, recipe
budget rollup, shopping-list pricing) is rewritten *against the substrate*,
with Products as an enriching data source when present.

**Server-owned helper:** `get_stock_item_unit_cost_at(stock_item, when)`
picks the best signal — product-derived cheapest if available *and* Products
on, else most recent direct observation, else null. R-003 — single derived
fact, server-owned; no client-side cost math.

Consumers to rebase:
- `StockValueOverTimeHandler` (just refactored — see 2026-06-14 worklog) —
  fall back to `get_stock_item_unit_cost_at` when no linked products exist
  or Products is off. The "cheapest most-recent linked-product price"
  semantics extend cleanly: when no product is linked, use the substrate.
- Recipe cost estimate (PROPOSAL_COOKBOOK Chunk N) — sum
  `unit_cost × required_qty` over ingredients. The unit cost source is
  irrelevant to the recipe; it just calls the helper.
- Meal-plan budget rollup — same; derives from recipe cost estimates,
  which derive from substrate.

### 2.2 Money + Products are independent layers — the 2×2

|  | Money on | Money off |
|---|---|---|
| **Products on** | Full SKU + price (today's behaviour) | SKU mapping only, no dollar amounts anywhere |
| **Products off** | Stock-item price logging (the substrate, no merchant attribution) | Pure checklist — no dollars anywhere, no SKU concept |

The Money opt-in (PROPOSAL_CONFIG_AND_OPTINS §2.2) governs *whether dollars
render at all*; the Products flag governs *whether SKU-level concepts
exist*. They compose; neither implies the other.

**Open thread for onboarding (§4-2):** the C-5 v3 persona table bundles
products+money together — Cooking is both off, Savings is both on. The
(Products off + money on) cell — "simple pantry + track grocery spend" — is
a real persona (the user who wants price memory without merchant or SKU
modelling) and must be reachable. Two options:
- **(A) Customise branch handles it** — personas are presets; the
  Customise path exposes the flags independently. Minimal change.
- **(B) Add a fourth preset** — e.g. "Pantry + spend, no SKUs."
  Discoverable but adds another decision at first-login.

Recommendation: **(A)**, with the Customise branch wording made explicit
about the four combinations. Pointer note already in
`PROPOSAL_ONBOARDING.md` §3.2.a.

### 2.3 Stock-item-vs-product confusion — the real UX risk

The data model is internally clean, but the *concept* sits two-thirds up
the abstraction ladder for non-technical users. Confusion arises only in
Products-on mode (in simple mode the word "product" doesn't appear in the
UI at all — which is itself a strong argument for simple mode being a good
default).

**Layered mitigations:**
1. **Onboarding explainer copy** (owned by `PROPOSAL_ONBOARDING.md` §3.3,
   pointer added). Required wording shape: *"'Milk' is a stock item — a
   thing you keep. 'Vitasoy Oat Milky 1L @ Coles' is a product — a
   specific thing you can buy."* Paired with a *don't*: *"Don't name your
   stock items after brands — that's what products are for."*
2. **Glossary entry in the help overlay** (owned by
   `PROPOSAL_HELP_OVERLAY.md` §2.3, pointer added). "What's a stock
   item?" / "What's a product?" pair, milk example, reachable from any
   surface where either term appears. Suppressed in simple mode.
3. **In-context micro-copy** on the stock-item-create form (Products-on
   only): *"A type of thing you keep — like 'milk' or 'flour.' Don't name
   it after a brand — that's what products are for."*
4. **Empty-state copy on My Products** (Products-on only): *"Products are
   the specific brands/SKUs you buy. They link to stock items."* with the
   milk → Vitasoy example.
5. **Simple mode amplifies clarity, doesn't muddy it.** Confusion can
   only arise in Products-on mode or at the transition between modes.

### 2.4 "Simple mode" — a named identity, not the absence of Products

`products_enabled = false` is the flag; **"Simple mode" is the user-facing
identity.** Decoupling matters: the user is in a *complete* product, not a
stripped-down one, and the UI should communicate that.

- **Onboarding** — the Cooking persona effectively *is* simple mode. The
  label "Simple mode" can also appear in settings as the user-visible name
  for the flag's off-state, so the identity carries across the lifecycle
  (not just at first-login).
- **Settings indicator** — small "Simple mode" chip on the settings page
  with a one-line explainer and a "switch to full mode" affordance. **No
  persistent app-shell badge** — would feel like a downgrade reminder; the
  point is simple mode is a complete product.
- **Codebase flag name** stays technical (`products_enabled`). UI label
  decoupled. Standard pattern.
- **No condescension in copy.** Simple mode isn't "Dora Lite." It's
  "Pantry & cooking" — a chosen identity.

### 2.5 Per-surface sweep — what changes when Products is off

The discipline: **collapse surfaces, don't blank them.** Nav items removed,
tabs removed, columns removed, settings sections removed. A simple-mode
user should not be able to tell Products exists in the app.

| Surface | Products-on behaviour | Products-off behaviour |
|---|---|---|
| **Nav** | My Products, Product Search, Deals, Cart visible | All four removed (not greyed) |
| **Shopping list** | Per-line offer picker, cheapest-merchant sort, merchant grouping, cart button, "log what you paid" close-out | **Checklist mode** — name + qty + checkbox; group by `usual_store_id` if set, else flat; close-out marks consumption; price input per line gated by Money opt-in (writes a `manual` observation, not an offer) |
| **Stock-item detail** | Linked-products tab/list, product offers, price-history chart with merchant lines | Linked-products tab removed; price-history chart shows direct observations only (gated by Money opt-in) |
| **Stock-item create/edit** | "Link a product later" affordance + micro-copy | Form is name, location, qty, unit only. No product affordances. No tooltip mentioning products. |
| **Recipe ingredients** | "Linked product" affordance on each ingredient, empty states | Just ingredient line + qty + in-stock pill |
| **Recipe cost estimate** (Money on) | Derived from linked product offers + observations | Derived from `get_stock_item_unit_cost_at` on the substrate only |
| **Meal-plan budget rollup** (Money on) | Sum over recipe cost estimates | Same — recipe cost just uses the substrate |
| **Stock-value report** (Money on) | Cheapest most-recent linked-product price | `get_stock_item_unit_cost_at` per item per cursor; substrate-only data |
| **Settings** | Stores list, scanning, deals-email, ingestion/companion, preferred stores | All hidden. The Stores management page (§2.6) stays if Money is on (for shopping-list grouping); hidden if both flags off. |
| **Alerts (C-9)** | Deal/price-drop types available | Those types removed from the matrix; expiry/use-up types remain |
| **Global search** | Stock items + recipes + products | Stock items + recipes only |
| **Barcode scanning** | Resolves real EANs to Products → StockItem; Dora's own QR labels navigate | Real EANs do nothing (acceptable — minimal users aren't scan-flow optimizers); Dora's own QR labels still navigate |
| **Ingestion API** | Receives products/offers from companion | Endpoint disabled at the feature-flag layer — `products_enabled` off means the companion has nowhere to push |

### 2.6 Stores (renamed from Merchants) — independent of the flag

The rename and the management page are independent of Products on/off —
stores are useful in simple mode (shopping-list grouping) and in
Products-on mode (offer attribution). Full design tracked in **FU-189**;
summary here:

- **Entity + UI rename** `Merchant` → `Store` app-wide. Plain-language
  ("Coles is a store, not a merchant"). Pre-release, no compat shims, one
  migration, one mechanical pass.
- **Single management page** in settings. User-curated. **No prefilled
  stores** (sidesteps locale-coupling + legal-logos risk). **No
  auto-create** from any other code path — notably the ingestion API
  (FU-190).
- **Per-store image upload** reusing the existing image-upload infra
  (C-cross §2.8). Dora ships zero logos — legal safety. Fallback when no
  image: the hash-swatch + initial pattern from `ProductSearchCard`.
- **`StockItem.usual_store_id`** (nullable) — single "I usually buy this
  at X" field. Drives shopping-list grouping in simple mode. Per-line
  override at trip-build time.

**Observations carry no store attribution in simple mode.** Rationale: in
simple mode, prices are "how much does this cost me," not a cross-store
comparison — comparison is exactly what Products-on is for. Dropping the
field keeps the model honest about what simple mode means.

### 2.7 Shopping-list-as-receipt — the price-entry surface

The shopping-list close-out is the most natural place for "how much did I
pay for this" entry, but it shouldn't be the *only* place. Anywhere the
user wants to log a price should work:

- **Shopping list line** — per-line price input visible during the trip,
  writes a `shopping_close_out` observation on tick. Gated by Money on.
- **Stock-item detail** — "log a price" button writes a `manual`
  observation.
- **Quick-add modal** — same.
- **Future receipt-import flow** — when/if it ships, writes
  `manual`-equivalent observations directly to stock items (no Product
  mapping required — the simplification is itself an unlock).

All write to `StockItemPriceObservation` with appropriate `source`. None
require Products. All are gated by Money opt-in.

**Receipt OCR is out of scope** — the shopping list *is* the receipt.

### 2.8 Mode-flip behaviour — non-destructive both ways

- **Off → on:** existing direct observations stay; new ProductOffers add
  store-attributed points alongside on the chart. The chart legend
  distinguishes "manual entries" from "product offers."
- **On → off:** ProductOffer history isn't deleted, just hidden from the
  chart. **Don't roll up** offers into substrate observations on flip —
  mixing sources after a mode switch is exactly the messiness the user
  flagged. Hidden ≠ destroyed; flipping back restores the view.
- `StockItem.usual_store_id` keeps working as a default selection hint in
  either mode.
- No data migration required at the moment of flipping; pure view change.

### 2.9 What this proposal deliberately does NOT do

- Does not redesign the onboarding wizard — that's C-5 / `PROPOSAL_
  ONBOARDING.md`. This proposal supplies the explainer copy and flags the
  persona-table gap, nothing more.
- Does not own the help-overlay system — that's `PROPOSAL_HELP_OVERLAY.
  md`. This proposal supplies the glossary content.
- Does not own the Money opt-in design — that's `PROPOSAL_CONFIG_AND_
  OPTINS.md §2.2`. This proposal just relies on its existence.
- Does not own the Stores rename + management page — that's FU-189. This
  proposal depends on it.
- Does not own the ingestion API constraint — that's FU-190.
- Does not design a "deals email" replacement, a brand-loyalty surface,
  or any feature retired with the scraper.
- Does not introduce multi-tenant or shared price data (Decision 5,
  deferred).

---

## 3. Data-model summary

| Change | Home | Default | Gated feature |
|---|---|---|---|
| `StockItemPriceObservation` (new table) | new | n/a (rows on write) | written iff Money on; surface depends on Products |
| `StockItem.usual_store_id` (FK, nullable) | existing | NULL | n/a — used by shopping-list grouping regardless of Products |
| `Merchant` → `Store` rename | existing | n/a | FU-189 |
| `AppSetting.products_enabled` | existing (introduced in C-5.3) | on | this proposal's spine |

Migrations:
- One migration for `StockItemPriceObservation` + the `StockItem.
  usual_store_id` FK. Batch-mode for SQLite portability (R-005). Single
  reversible downgrade.
- The `Merchant` → `Store` rename is its own migration under FU-189.
- No conditional/idempotent guards (R-006).

DTO additions:
- `LinePriceInputDto` on shopping-list lines (Money on only).
- `StockItemPriceObservationDto` on stock-item detail (Money on only).
- `RecipeCostEstimateDto` rebased on the substrate helper (Money on only).

---

## 4. Open decisions (for co-design)

1. **Personas and the 2×2** — (A) Customise branch reaches all four cells,
   or (B) add a fourth preset for "Pantry + spend, no SKUs"?
   *Recommendation: (A).*
2. **"Simple mode" as the user-facing label** — confirm the name. Other
   candidates: "Pantry mode," "Lite," "Just the basics."
   *Recommendation: "Simple mode" — short, honest, no implicit downgrade.*
3. **Per-line store override on shopping list** — does the override
   persist to the *next* shopping list ("I switched to Aldi for everything
   this month") or always reset to `usual_store_id`?
   *Recommendation: always reset; persistent change = user updates
   `usual_store_id`.*
4. **Recipe cost estimate fidelity in simple mode** — when only direct
   observations exist, do we surface confidence ("estimate based on 2
   observations from 4 months ago") or just show the number?
   *Recommendation: a small "based on N observations" footnote; honesty
   over false precision (P3).*
5. **Settings → Stores visibility when both flags off** — hide the page
   entirely, or keep it as a no-op management surface? Stores have no
   consumer if Money is off (no observation attribution) and Products is
   off (no offers).
   *Recommendation: hide. Re-show if either flag flips on.*

---

## 5. Ripple & dependencies

- **C-5 onboarding (in flight)** — already lands the persona + flag.
  Confirm §3.2.a thread before C-5 ships.
- **PROPOSAL_CONFIG_AND_OPTINS.md** — this proposal amends §2.6 (Products
  elevated from candidate to spine flag). §2.2 (Money opt-in) is a
  prerequisite consumer.
- **PROPOSAL_HELP_OVERLAY.md §2.3** — content note added.
- **PROPOSAL_INGESTION_API.md** — must be amended per FU-190 to honour
  no-auto-create-stores.
- **PROPOSAL_COOKBOOK.md / IMPL_PLAN_COOKBOOK.md** — recipe cost estimate
  must rebase on `get_stock_item_unit_cost_at`.
- **PROPOSAL_SHOPPING_LIST_UX_V2.md / SHOPPING_LIST_REDESIGN_PROPOSAL.md**
  — must define checklist-mode rendering when Products is off.
- **PROPOSAL_STOCK_OVERVIEW.md** — minor; stock rows shed any product
  affordances.
- **Stock-value report** — already refactored 2026-06-14; needs a
  follow-up patch to call `get_stock_item_unit_cost_at` and degrade to
  substrate observations when no linked products exist.

---

## 6. From the original spec (historical — `docs/00_original_spec/`)

Cross-check per CLAUDE.md "Consulting the original spec" rule. Source
predates this branch's ~100k LOC; historical only.

- **`Feature Boards/!Dump ~ No Area.md` line 14** — *"I can use product
  features without linking products to stock items (e.g. no usage of stock
  item features)"* — **keep, reframed.** The original intent of features
  being independently usable is preserved here; this proposal makes the
  *opposite* direction first-class (stock-item features without product
  features), which the original framing was silent on. The "products
  without stock items" direction is covered separately by feedback L191
  (My Products page: dangling products on shopping list).
- **`Feature Boards/Products.md`** — many product-search features; **all
  superseded** by the scraping-divorce decision (master Decision 1). No
  extraction.
- **No "Simple mode" or persona framing** in the original spec — this is
  a new concept reached via the feedback (L191 + L254) and the C-5 v3
  persona redesign. No historical name to preserve.

Tag summary: **keep (1, reframed)**, **superseded (rest)**.

---

## 7. Feedback coverage

Bullets mapped from `02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md`.

| Bullet | Topic | Home in this proposal |
|---|---|---|
| L42 | Admin first-login feature enable/disable | §2.4, §2.5 (consumes the flag C-5 introduces) |
| L45 | "Which stores do you prefer to shop at?" — preferred stores | **superseded** — dropped in C-5 v3 §3.8 (FU-180 fold); replaced by `usual_store_id` per stock item (§2.6) |
| L46 | Stock-item-vs-product explainer before "add stock items" | §2.3 (copy supplied; explainer step owned by C-5 §3.3) |
| L84 | Cart-button complexity branching on linked-products presence | §2.5 (cart removed when Products off — simplifies the branch matrix) + cross-ref to `PROPOSAL_CART_BUTTON.md` |
| L125 | "Find deals" button placement | **out of scope** — Products-on UX detail; not this proposal |
| L130 | No way to add product of choice to shopping list (just cheapest) | **out of scope** — Products-on UX detail; cart-button proposal |
| L131 | Preferred merchant / preferred product fluff vs value | §2.6 (`usual_store_id` replaces preferred-merchant intent; preferred-product was removed 2026-06-14 — FU-180) |
| L158 | Merchant vs data-provider conflation on manage merchants page | §2.6 (Stores management page is user-curated; data providers are companion-scope, not Dora) |
| L184 | Link button as merchant logo | §2.6 (user-uploaded store images, no shipped logos) |
| L191 | **My Products: features should be standalone usable** | §1 anchor principle; **inverse direction** (stock items standalone-usable without products) is what this whole proposal delivers. The originally requested direction (products standalone on shopping list) is `PROPOSAL_CART_BUTTON.md`'s scope. |
| L192 | No way to add custom products (non-major-4 stores) | **out of scope** — Products-on UX; not this proposal |
| L226 | Price history view design | §2.1 (substrate chart reads direct observations; visual treatment out of scope) |
| L254 | Recipe cost estimate + all money features opt-out | §2.1 (substrate enables cost estimate without products); §2.2 (Money/Products independence). Money opt-in itself lives in PROPOSAL_CONFIG_AND_OPTINS §2.2 |
| L263 | Nutrition opt-in tiers | **out of scope** — owned by PROPOSAL_CONFIG_AND_OPTINS §2.3 |

Bullets outside this proposal's surface (recipes, meal plans, cook mode,
nutrition detail, product-search UX detail) are not enumerated — per
CLAUDE.md the table covers bullets *for the surfaces this proposal
targets*.

---

## 8. Suggested sequencing

The simple-mode sweep is non-trivial — it touches data model, several
read paths, the shopping list, settings, nav, and a fair chunk of UI
copy. Sequence to land it without thrashing:

1. **C-5 onboarding (in flight)** ships `products_enabled` + the persona
   fork. Prereq — already in plan.
2. **FU-189** — Stores rename, management page, user-uploaded images,
   no-auto-create rule, `StockItem.usual_store_id` column. Independent of
   simple mode but a prereq for shopping-list grouping in §2.5.
3. **This proposal's Chunk A — substrate.** Land
   `StockItemPriceObservation` + the `get_stock_item_unit_cost_at` helper
   + the two consumers most affected (stock-value report fallback, recipe
   cost estimate rebase). No UI changes yet; pure model + read-path work.
4. **This proposal's Chunk B — per-surface sweep.** Conditional nav,
   collapsed shopping list (checklist mode), stock-item-detail + recipe-
   ingredient affordance hiding, settings collapsing, "Simple mode" chip.
   Consumes the flag, the substrate, and the renamed Stores.
5. **This proposal's Chunk C — micro-copy + glossary.** Onboarding
   explainer copy lands in C-5; the help-overlay glossary entry lands
   when the overlay system ships; in-context micro-copy on stock-item-
   create + My Products empty state.
6. **FU-190** — PROPOSAL_INGESTION_API.md amendment for no-auto-create
   stores. Lands during Phase 2 ingestion-API design.

Chunks A and B can land in either Phase 3 polish or as their own
mini-wave; Chunk C threads through whatever surface ships next.

---

## 9. Engineering-standards check (R-001..R-0NN)

- **R-001 (componentisation)** — checklist-mode shopping list is a
  rendering variant of the existing list component; the new price-input
  field reuses existing input primitives.
- **R-002 (theme tokens)** — no new colours; "Simple mode" chip uses
  existing tokens.
- **R-003 (state ownership)** — `get_stock_item_unit_cost_at` is the
  spine: server-owned, single derived fact, no client duplication of cost
  math. This proposal explicitly forbids "compute cost on the client."
- **R-005 (Postgres/SQLite portability)** — `StockItemPriceObservation`
  is a plain table with no JSON, no UUID-text gymnastics beyond the
  existing pattern. Migration is batch-mode.
- **R-006 (clean migrations)** — one migration per data-model change,
  reversible downgrades, no idempotent guards.
- **R-007 (scope discipline)** — this proposal is explicit about what it
  does not own (§2.9). Adjacent rough code (e.g. the cart-button branching
  in L84) is cross-referenced, not absorbed.

No new ADR proposed — the substrate reframe is a R-003 application, not a
new pattern.
