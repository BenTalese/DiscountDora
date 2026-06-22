# Products as a data-presence-gated overlay — Stock Item as the universal first-class entity

**Status:** proposal, co-designed with the user 2026-06-17. Changes NO code (sequences it).
**Supersedes (in part):** `PROPOSAL_SIMPLE_MODE.md` — replaces its *spine* (the user-set
`products_enabled` persona flag, "Simple mode as a named identity", and the Money×Products
2×2 onboarding gymnastics). **Keeps** its pricing-substrate design (§2.1 there) intact and
re-homes it here.
**Reshapes:** `PROPOSAL_INGESTION_API.md` (invisibility carve-out for the search-URL nav;
ingestion/API-keys are general infra, not products-gated), `PROPOSAL_ONBOARDING.md` /
`IMPL_PLAN_ONBOARDING.md` (personas removed — see §6), the C-1b "find & link a product" UX.
**Closes:** FU-182 (superseded — its premise changed). **Confirms:** FU-186, FU-189, FU-190.
**Relates:** FU-180 (preferred product/merchant reconsideration), the My-Products link
dead-end (FU-208, new).

**Anchor principle:** *There is one standard way to use Dora. The everyday user gets the whole
loop — including a lightweight, honest way to remember what they buy, where, and what it costs —
without ever meeting "Products." The rich Product/Offer machinery is a power-user overlay that
only appears when real data has been pushed in, and is otherwise completely invisible.* This is
the Charter tiebreak (Effortless + Anti-creep + P3 Honest) applied literally: **don't sell a
feature the user can't easily use, and never ship it half-baked.**

---

## 1. The decision (what changed, and why)

The earlier plan (PROPOSAL_SIMPLE_MODE) treated Products as a **user-facing mode**: an install
flag `products_enabled` set by an onboarding persona ("Cooking" = off), with a per-surface sweep
that collapsed the app around a "simple mode" identity, and a Money×Products 2×2 the onboarding
had to reach all four corners of.

The user's revised position — and the reasoning behind it:

1. **Manual product entry is a dead end.** The rich `Product` entity (brand, size, SKU,
   merchant, offers) is only worth anything when data flows in *automatically* (ingestion from a
   private external source). Nobody will hand-type it. A "products feature minus the scraping,
   filled in by hand" is exactly the half-baked thing to refuse to build.
2. **So Products stops being a user choice at all.** It is an **overlay that is either fully ON
   (real product data exists in the DB) or fully OFF (it doesn't)** — never "half on". No
   user-facing toggle, no persona, no onboarding mention. The poweruser switches it on by
   *sourcing the data* (setting up ingestion), not by flipping a setting.
3. **The everyday user still needs to remember what they buy.** That need is met *on the stock
   item itself* with three lightweight, honest constructs that require no scraping and no Product
   rows (§3). The stock item becomes **the** first-class entity for both stock and everyday
   product info; the rich Product takes a permanent back seat.
4. **The two systems stay completely separate** (the everyday stock-item constructs vs the
   power-user Product overlay). This is deliberate: a clean separation is what prevents the
   "half-baked product feature" failure mode. They are not two states of one thing.

This is mostly a *sharpening* of the existing direction — scraping was already divorced to a
companion, ingestion was already the only intended inbound path, and the
`StockItemPriceObservation` substrate + `usual_store_id` were already designed. The genuinely new
moves are: **(a) gate Products on data-presence instead of a flag; (b) add `PreferredBuy`; (c)
remove products/personas from onboarding entirely; (d) keep the product *pages* in Dora but move
only the *search page* out to the companion behind a configured URL.**

---

## 2. The gate — `features.products` derived from data presence

**Keep the existing gate, change its source.** Every product surface already reads
`features.products` (frontend `useFeatureFlags().products`, fed by `GET /api/health`). Today
`health_check.py` derives that from `AppSetting.products_enabled`. The change:

```
features.products  ==  (a Product row exists)      # server-derived, NOT an admin toggle
```

- Server-side: `health_check` computes `repo.get(Product).count() > 0` (cheap; same try/except
  envelope as today). Optionally widen to "any Product OR ProductOffer row" — but Product rows
  are the natural anchor (offers hang off products). Decision §7-1.
- **The `AppSetting.products_enabled` column is dropped** (clean migration — pre-release, no
  preservation needed). So is its admin PATCH field, its `get_app_settings` DTO field, and the
  onboarding persona dimension that set it.
- **Every `v-if="productsEnabled"` gate stays exactly as written** — the C-1b.3 per-surface
  hiding work is *not* wasted; only what feeds the boolean changes. This is the whole reason the
  reframe is cheap.

**Why a boolean, not "count > 0" sprinkled around:** R-003 — the gate is a single server-derived
fact, exposed once via `/health`, consumed everywhere. No client counts Product rows.

**Edge: data appears/disappears.** The everyday user never has product data and never sees the
surfaces — no flicker. A poweruser who ingests data sees the surfaces appear and, in practice,
they stay (ingestion is monotonic). If a poweruser deletes *all* products the surfaces vanish —
acceptable and correct (there's nothing to show). The rule is simply "≥1 product row → on";
reactivity is whatever `/health` refresh cadence already provides.

---

## 3. The everyday layer — three constructs on the Stock Item

These hang off `StockItem`, are **always available** (not gated by Products data-presence), and
require no Product rows. The everyday user meets only these; the word "product" never appears.

### 3.1 `PreferredBuy` (NEW) — free-text "what I actually buy" reminders

A short list of **free-text labels** the user keeps against a stock item to remind themselves of
their favourite buys — e.g. they'd type `Vitasoy Oat Milky 1L` against the "Milk" stock item.
Purely a memory aid + shopping hint. **No price, no SKU, no merchant, no validation.**

```
PreferredBuy:
  id              (PK)
  stock_item_id   (FK, required, ondelete=CASCADE)
  label           (string, required — free text, whatever the user types)
  position        (int, for manual ordering)
  created_at      (datetime)
```

- **Naming (locked with the user): `PreferredBuy` / "preferred buys".** Deliberately *not*
  "related products" (collides with the `Product` entity) or "store items" (collides with both
  *stock items* and the *Stores* rename, FU-189). The name self-documents the everyday,
  user-typed, no-entity nature and reads naturally next to the shopping-list-hint use.
- **Surface:** a "Preferred buys" section on the **Stock Item Detail** page — add / edit / delete
  / reorder free-text rows. Available to every user, always (it's part of the stock item, like
  notes). Not behind Products, not behind Money.
- **Shopping-list hint:** when a stock item is on a list, its preferred buys are offered as a
  selectable **hint** on the line ("get the Vitasoy Oat Milky 1L"). Mechanism:
  `ShoppingListLine.preferred_buy_id` (nullable FK) — displayed as hint text, carries **no
  pricing or product semantics**. Choosing one is optional; it's a reminder, not a constraint.
- **Strictly separate from `Product`.** A `PreferredBuy` never "upgrades" into a `Product` and a
  `Product` never demotes into a `PreferredBuy`. The two systems coexist on the same stock item
  without bridging — per the user's "completely separate systems" principle.

### 3.2 Price observations — "what this costs me" (Money opt-in)

This is `PROPOSAL_SIMPLE_MODE.md §2.1`'s `StockItemPriceObservation`, re-homed here unchanged in
substance. The everyday user records **total price + quantity/unit** from a finished shopping
trip (or a manual entry); **per-unit price is derived server-side** — the user never does the
division.

```
StockItemPriceObservation:
  stock_item_id   (FK, required)
  price           (decimal, required — the total paid)
  qty             (decimal, required)
  unit            (string, required)
  observed_at     (datetime, required)
  source          (enum: 'manual' | 'shopping_close_out' | 'product_offer')
  # NO merchant attribution in the everyday layer — "what it cost me", not a cross-store compare
```

- Per-unit cost is computed by the server-owned `get_stock_item_unit_cost_at(stock_item, when)`
  helper (R-003 — single derived fact; no client-side cost math). It prefers product-derived
  cheapest *when Products is on*, else the most recent direct observation, else null.
- **Gated by the Money/budgeting opt-in** (its own independent feature — §5), not by Products.
  Price-entry surfaces: shopping-list close-out (per-line, on tick → `shopping_close_out`),
  stock-item detail "log a price" (→ `manual`), quick-add modal (→ `manual`).
- When Products is on, linked `ProductOffer` points union into the same chart as a
  `product_offer` source — the overlay *enriches* the substrate, never replaces it.

### 3.3 `usual_store_id` — "where I usually buy this"

`StockItem.usual_store_id` (nullable FK to Store) — a single "I usually buy this at Coles" hint.
Always available (no dollars, no products); drives shopping-list grouping, with a per-line
override at trip-build time. This is FU-189's field; tracked there, noted here as part of the
everyday stock-item model. The `Merchant → Store` rename and the no-auto-create rule (FU-190)
are prerequisites and unchanged.

---

## 4. The power-user overlay — Products, ingestion-only, invisible until present

When (and only when) real product data has been pushed in via the ingestion API, the full
Product layer **appears in place**, integrated so it feels native:

| Surface | Disposition under this proposal |
|---|---|
| **My Products page** | **Stays in Dora.** Visible/navigable only when `features.products`. Linking products to stock items is a power-user action available here + on stock-item detail (the dead-end link flow is repaired — §4.2). |
| **Price History page** | **Stays in Dora.** Visible only when `features.products`. |
| **Stock-item Products tab** | **Stays in Dora.** The `v-if="productsEnabled"` gate is retained, now fed by data-presence. |
| **Product Search page** | **Moves to the companion app** (it requires live scraping, which Dora-core must never do). Dora keeps the **nav entry**; clicking it navigates to an **install-configured URL** (the companion's search page) so it feels like part of Dora — see §4.1. |
| **Shopping-list product behaviour** (offer picker, cheapest sort, merchant grouping, cart) | Stays in Dora; gated on `features.products`. Cross-ref `PROPOSAL_CART_BUTTON.md`. |
| **Dashboard best-deals** | Stays; gated on `features.products`. |
| **Ingestion API + admin "API access" keys page** | **Always accessible** — see §4.3. |

**Building the Product overlay up as a first-class feature remains the goal.** All the deferred
"fancy" product ideas (price intelligence, "paying more than usual", back-in-stock, etc.) live
here and are built on the assumption that data arrives via ingestion. This proposal does not
design those; it sets the gate and the boundary so they can be built cleanly later.

### 4.1 Search-page nav → configured companion URL (invisibility carve-out)

The search page leaves Dora-core for the companion. But the **"Product Search" nav button stays
visible when `features.products`** and navigates to an **install-level configured URL** (the
companion's search page). To the user it feels like a native part of Dora — they click "Product
Search" and land on a search experience.

- **New install setting: a "Product search URL"** (admin-configured, install-wide). Only
  relevant/shown when `features.products` (i.e. data is present).
- If `features.products` is true but no URL is configured: the nav entry routes to that admin
  setting (for the admin) / is hidden (for non-admins). Decision §7-2.
- Open in same tab vs new tab: default **same tab** (feels native); revisit if the companion
  needs to be clearly external. Decision §7-3.

**This is a deliberate, bounded relaxation of the ingestion "invisibility is a HARD RULE"
(PROPOSAL_INGESTION_API §header).** The spirit is preserved: the companion is **never named** —
no "companion", "scraper", "import", or brand text anywhere. It simply appears as "Product
Search". This carve-out is the *only* place Dora links outward, it is user-initiated, and it is
unlabelled. Recorded explicitly here so it reads as a conscious decision, not drift.

### 4.2 Repair the My-Products → stock-item link dead-end (FU-208)

C-1b.3 removed the saved-products picker dialog from `StockItemDetailPage.vue`, but
`MyProductsPage.vue` still routes its "Link…" action to `/stock/{id}?link_product_id=...` — and
**nothing consumes `link_product_id`**, so the link silently never happens. Under this proposal
linking is a legitimate power-user action (it only appears when data is present), so the fix is
to **rebuild a working link path**, not delete it:

- Re-add a working link affordance (either consume `link_product_id` on the detail page, or link
  in place on My Products via the existing `POST /api/stock-items/{id}/products` endpoint).
- **Do not** rebuild anything implying manual *product creation* — linking pre-existing
  (ingested) products only.

### 4.3 Ingestion / API keys are general infra (always accessible)

Per the user: API-key setup is **not strictly a product feature**. The admin "API access" page
(ingestion source CRUD + observability, PROPOSAL_INGESTION_API §2.1) is **always available**,
independent of `features.products`. This is what lets a poweruser bootstrap: configure a key,
push the first batch, *then* the product surfaces light up. It avoids the chicken-and-egg of
"surfaces gated on data, but you need a surface to get data in."

---

## 5. Onboarding — back to one standard path (personas removed)

Per the user: **no personas. One standard way to use the app; people use the parts they want.**
Onboarding becomes "show them everything," un-personalized.

- **Remove the persona fork** (C-5.3) and the `products_enabled` dimension it set.
- **Remove all product framing from onboarding** — including the **stock-item-vs-product
  explainer** (now moot: the everyday user never meets "products"). The milk-vs-Vitasoy
  explainer copy is retired from onboarding.
- **Keep the structural C-5 improvements** (decided with the user): the cinematic intro, the
  hero "loop" diagram, starter packs, household headcount, and the finish celebration — but
  **un-personalized** (no persona previews in C-5.2, no persona-relevant tailoring in C-5.6;
  show the full loop and the full set of flow-cards).
- **Money/budgeting is a Settings toggle only** (decided with the user). Onboarding shows the
  feature exists like everything else; it does not fork or force a choice. The money opt-in lives
  in Settings (PROPOSAL_CONFIG_AND_OPTINS §2.2), enabled whenever the user wants it.
- The onboarding sell-copy honesty gate (FU-184) still applies to whatever loop copy ships; the
  "Insight / spend-smarter" beat stays a *candidate* until the price-intelligence layer is real.

This removes the part of PROPOSAL_SIMPLE_MODE that the most: "Simple mode as a named identity",
the persona table, and the 2×2-reachability problem all evaporate — there is no mode to name,
because the everyday experience *is* the app.

---

## 6. What this supersedes / reshapes in existing docs

| Doc | Change |
|---|---|
| `PROPOSAL_SIMPLE_MODE.md` | **Spine superseded.** §2.2 (2×2 onboarding reachability), §2.4 ("Simple mode" identity), §2.5 (per-surface sweep keyed to a *user-chosen* flag), the persona dependencies in §1/§5/§8. **Survives & re-homed here:** §2.1 pricing substrate (→ §3.2), §2.6 stores/`usual_store_id` (→ §3.3, still FU-189), §2.7 price-entry surfaces (→ §3.2). A supersession banner is added to that file pointing here. |
| `PROPOSAL_INGESTION_API.md` | Invisibility HARD RULE gains the §4.1 search-URL carve-out (companion never *named*). API-keys page explicitly **always accessible**, not products-gated (§4.3). FU-186 reshaped: the companion is a *complete app* (merchant_api + the moved search page + a settings page) in its own repo. |
| `PROPOSAL_ONBOARDING.md` / `IMPL_PLAN_ONBOARDING.md` | Personas removed; product framing + stock-vs-product explainer removed; structural chunks kept un-personalized; money via Settings. |
| `RECONCILED_FINISHING_PLAN.md` §7 | A new resolved-decision pointer added (products = data-presence overlay; no user flag). Decision 1 (scraper→companion) is unchanged and reinforced. |
| `COVERAGE_GAPS.md` | Product/feature-flag bullets re-noted to point here where the home changed. |
| C-1b stock-item detail | The Products tab gate is retained (source changes); the My-Products link dead-end is repaired (§4.2); a "Preferred buys" section is added (§3.1). |

---

## 7. Open decisions (for build-time)

1. **Gate source:** `Product.count() > 0` alone, or `Product OR ProductOffer`?
   *Recommendation: `Product.count() > 0` — offers can't exist without products; the product row
   is the natural anchor.*
2. **Search nav when data present but URL unset:** route admins to the config setting, hide for
   non-admins, or show-disabled with a hint?
   *Recommendation: route admins to the setting; hide for non-admins (R-014 reveal-disable spirit
   — don't show a dead button to someone who can't fix it).*
3. **Search URL target:** same tab or new tab?
   *Recommendation: same tab (feels native); the companion is unlabelled either way.*
4. **`PreferredBuy` on the shopping line:** persist a chosen hint via `preferred_buy_id` FK, or a
   free-text snapshot copied onto the line?
   *Recommendation: `preferred_buy_id` FK (nullable, ondelete SET NULL) — keeps it a live
   reference; snapshotting is over-engineering for a reminder.*

---

## 8. Suggested sequencing

The doc work (this proposal + the reconciliations in §6 + the ledger) lands now. The code is
sequenced as follows — each is its own work unit:

1. **Gate reframe** — drop `AppSetting.products_enabled` + its admin/DTO/onboarding-persona
   surface; re-derive `features.products` from `Product.count() > 0` in `health_check`. Small,
   self-contained, unblocks everything else. (New FU-209.)
2. **Onboarding de-persona** — strip the persona fork + product framing + explainer; keep the
   structural chunks un-personalized; money→Settings. (New FU-210.)
3. **`PreferredBuy`** — table + migration + stock-item-detail section + shopping-line hint.
   Always-available everyday feature. (New FU-211.)
4. **Price substrate** — `StockItemPriceObservation` + `get_stock_item_unit_cost_at` + the two
   read-path consumers (stock-value report fallback, recipe cost estimate), Money-gated. (This is
   PROPOSAL_SIMPLE_MODE Chunk A, carried forward.)
5. **My-Products link repair** (§4.2, FU-208) — pairs naturally with (1).
6. **Search-page extraction → companion + configured-URL nav** (§4.1) — pairs with FU-186; Phase 2
   ingestion territory. Needs the companion repo to exist to land the moved page.
7. **FU-189 (Stores rename + `usual_store_id`) / FU-190 (no-auto-create)** — prerequisites for
   shopping-list grouping; independent of the above.

Steps 1–3 are no-regret and can land in Phase 0/1; 4–7 thread through the loop / Phase 2 ingestion
work.

---

## 9. From the original spec (historical — `docs/00_original_spec/`)

Cross-check per CLAUDE.md "Consulting the original spec" rule. Historical only; pre-dates the
charter + ~100k LOC.

- **`Feature Boards/!Dump ~ No Area.md` line 14** — *"I can use product features without linking
  products to stock items"* — **superseded.** The original framed product features as
  independently usable; this proposal makes the *stock item* the independent first-class entity
  and the rich Product a data-gated overlay — the opposite emphasis, reached deliberately via the
  feedback + the scraping-divorce.
- **`Feature Boards/Products.md`** (product-search features) — **superseded** by Decision 1
  (scraper→companion); the search page itself now lives in the companion (§4.1).
- **No "PreferredBuy" / "favourite buys" concept in the original spec** — this is new, reached
  via the user's 2026-06-17 reframe. No historical name to preserve.

Tag summary: **superseded (original product-search intent)**, **new (PreferredBuy, data-presence
gating)**.

---

## 10. Feedback coverage

Bullets from `02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md` for the surfaces this
proposal targets (products gating, the everyday stock-item layer, product-search placement,
onboarding's product framing). Re-homed from PROPOSAL_SIMPLE_MODE's table where the design moved.

| Bullet | Topic | Home in this proposal |
|---|---|---|
| L42 | Admin first-login feature enable/disable | §2 — **products is no longer an admin toggle** (data-presence). Money/nutrition/scanning flags remain admin-toggleable (PROPOSAL_CONFIG_AND_OPTINS §2.6). |
| L45 | "Which stores do you prefer to shop at?" — preferred stores | **superseded** (dropped in C-5 v3; FU-180 fold) — replaced by `usual_store_id` per stock item (§3.3). |
| L46 | Stock-item-vs-product explainer before "add stock items" | **superseded / removed** — the everyday user never meets products, so the explainer is retired from onboarding (§5). |
| L84 | Cart-button complexity branching on linked-products presence | §4 (cart is part of the product overlay; absent when no data) + cross-ref `PROPOSAL_CART_BUTTON.md`. |
| L125 | "Find deals" button placement | **out of scope** — product-overlay UX detail (C-1b.3 already addressed placement). |
| L130 | No way to add product of choice to list (just cheapest) | **out of scope** — product-overlay UX detail; cart-button proposal. |
| L131 | Preferred merchant/product fluff vs value | §3.1 (`PreferredBuy` gives the everyday "remember what I buy" without the rich entity); §3.3 (`usual_store_id`); preferred-product removed 2026-06-14 (FU-180). |
| L158 | Merchant vs data-provider conflation on manage-merchants page | §4.3 + FU-189 (Stores are user-curated; data providers/ingestion sources are the generic "API access" page; the producer is never named). |
| L184 | Link button as merchant logo | FU-189 (user-uploaded store images, no shipped logos). |
| L191 | My Products: features should be standalone-usable | §3 anchor — the **stock item** is the standalone-usable entity; the products-standalone-on-list direction stays `PROPOSAL_CART_BUTTON.md`'s scope. §4.2 repairs the broken My-Products link path. |
| L192 | No way to add custom products (non-major-4 stores) | **out of scope / by design** — manual product entry is explicitly refused (§1). The everyday substitute is `PreferredBuy` (§3.1); real products arrive via ingestion. |
| L226 | Price history view design | §3.2 (substrate chart reads direct observations; visual treatment out of scope). The Price History *page* stays in Dora, data-gated (§4). |
| L254 | Recipe cost estimate + all money features opt-out | §3.2 (substrate enables cost estimate without products); §5 (money is an independent Settings opt-in). Money opt-in design itself lives in PROPOSAL_CONFIG_AND_OPTINS §2.2. |

Bullets outside this proposal's surfaces (recipes, meal plans, cook mode, nutrition, deep
product-overlay UX) are not enumerated — per CLAUDE.md the table covers bullets for the surfaces
this proposal targets.

---

## 11. Engineering-standards check (R-001..R-0NN)

- **R-001 (componentisation/reuse):** the gate reframe reuses the existing `features.products`
  plumbing end-to-end (only the server source changes); the price-input + chart reuse existing
  primitives; `PreferredBuy`'s editor is a free-text list (reuse existing list/input components).
- **R-002 (theme tokens):** no new colours introduced by this proposal.
- **R-003 (state ownership):** `features.products` is a single server-derived fact (no client
  counting of Product rows); `get_stock_item_unit_cost_at` is the single server-owned cost fact
  (no client cost math). Both explicitly forbid client duplication.
- **R-005 (Postgres/SQLite portability):** `PreferredBuy` and `StockItemPriceObservation` are
  plain tables; dropping `products_enabled` is a portable column drop.
- **R-006 (clean migrations):** one migration per change, reversible, no idempotent guards;
  `products_enabled` dropped cleanly (pre-release — no preservation).
- **R-007 (scope discipline):** explicit non-goals — does not build the price-intelligence layer,
  does not design the companion app's internals, does not rebuild manual product entry.
- **R-014 (reveal-disable):** the search nav follows reveal-disable when the URL is unconfigured
  (§7-2).

**ADR evaluation:** this introduces a reusable pattern worth an ADR — *"feature surfaces gated on
data-presence rather than a user/admin flag, exposed as a single server-derived `/health`
boolean."* Recommend promoting to a new `R-0NN` when the gate-reframe code lands (it generalises
beyond products — any optional data-fed surface could use it).

---

## Appendix A — Complete product-feedback coverage & status (2026-06-17)

**Does the pivot drop any product feedback? No.** This audits **every** product-related bullet in
`02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md` against its status under the new model.
Headline: **most product UX feedback is already BUILT, and the pivot keeps those pages in Dora
(data-gated), so none of that work is discarded.** What genuinely changes: the *search page* moves
to the companion (its feedback goes with it), manual product entry is replaced by `PreferredBuy` +
ingestion, and the onboarding explainer is mooted. A bug-and-polish cluster needs browser
verification (FU-214).

Legend: **BUILT** = shipped in Dora · **VERIFY** = reported bug, looks fixed on a static read,
needs browser confirm · **COMPANION** = moves with the search page · **REPLACED** = disposition
changed by the pivot (needs user OK) · **GAP** = small, not yet built · **TRACKED** = design/UX
owned by a named proposal/FU.

### Stock Item Detail (product bullets)
| L | Bullet | Status | Where |
|---|---|---|---|
| L119 | Unlink button throws ("kaboom") | VERIFY | `onUnlink` wired; confirm no exception — FU-202 |
| L125 | "Find deals" only in products tab, when empty | **BUILT** | C-1b.3 empty-state CTA; toolbar Find-deals removed |
| L130 | Per-product list-add + highlight cheapest | **BUILT** | C-1b.3 cheapest-card highlight + per-product add-to-list |
| L131 | Preferred merchant/product fluff vs value | ADDRESSED | preferred-product removed (FU-180); everyday "what I buy" → `PreferredBuy` (FU-211); preferred-*store* reconsideration open (FU-180) |

### My Products
| L | Bullet | Status | Where |
|---|---|---|---|
| L190 | Standalone-usable; product-only line + nesting + removal modal | **BUILT** | C-7 cart button (schema + UI) |
| L191 | Add custom products (non-major-4 stores) | **REPLACED** | manual product entry refused; everyday = `PreferredBuy` free-text (FU-211); rich = ingestion. **Needs user OK** |
| L193 | "Mark inactive: Extra inputs not permitted" | VERIFY | bulk + per-row mark-inactive wired; confirm the validation bug is gone — FU-214 |
| L195 | Link-button placement + grey/green icon + link/unlink modal | PARTIAL | link dialog exists but the **handoff is broken (FU-208)**; grey/green styling — VERIFY |
| L196 | Componentise the cart button | **BUILT** | unified `AddToListButton` (5 variants) |
| L197 | Remove a saved product | ADDRESSED (soft) | mark-inactive is the soft equivalent; hard-delete intentionally absent under the ingestion model. **Confirm acceptable** (FU-214) |
| L198 | Inactive-product styling unclear | VERIFY | FU-214 |
| L205/206 | Bulk "select low-stock-on-deal" / "out-of-stock-on-deal" | **GAP** | only a generic "Select on-deal" bulk exists; the stock-level-filtered variants aren't built — FU-214 |

### Product Search (page moves to companion — §4.1)
| L | Bullet | Status | Where |
|---|---|---|---|
| L157 | Merchant vs data-provider conflation | ADDRESSED | Stores user-curated (FU-189); providers = ingestion "API access" page; the conflated page splits |
| L159 | Provider connection-health dropdown | COMPANION | lives on the search page |
| L160 | Search-bar dark-mode white-on-white + consistency | COMPANION (search bar) + VERIFY other Dora search bars (FU-214) |
| L164 | Data-accuracy disclaimer | COMPANION | |
| L166-168 | "Cannot save / quick-add / link: Extra inputs not permitted" | COMPANION + ingestion | save-from-search becomes a companion→ingestion action; Dora endpoints refactored under ingestion |
| L169 | Old (bigger, centred) save button | COMPANION | |
| L170 | %off label more obvious / card styling | COMPANION | |
| L184 | Link button as merchant logo | ADDRESSED | Phase E landed user-uploaded store images on `StoreLogo` with a hash-swatch + initial fallback (zero shipped logos). Rendered on `ProductChip`, `StockItemDetailPage` linked-products, `MyProductsPage` cards, and the Stores admin grid. |

### Price History (stays in Dora — §4)
| L | Bullet | Status | Where |
|---|---|---|---|
| L216 | "Major feature, hidden away" | TRACKED | discoverability; page stays, data-gated |
| L218 | Select products → no change on page | VERIFY | chart is multi-series; confirm selection updates — FU-214 |
| L219 | Card squished / notify placeholder cut | VERIFY | FU-214 |
| L220 | Notify-under should format as a price | VERIFY | FU-214 |
| L221 | %off text tiny | VERIFY | FU-214 |
| L222 | %off chip colour inconsistent / componentise | VERIFY | discount-chip component; confirm consistency — FU-214 |
| L225 | Graph doesn't reach the box edge | VERIFY | FU-214 |
| L226 | Price-history as a bottom-sheet from My Products | TRACKED | design idea; §4 + open |

### Shopping (product-touching) & Onboarding
| L | Bullet | Status | Where |
|---|---|---|---|
| L418 | Substitutes in shop mode | TRACKED | INV-8 (cook-session swap kept) |
| L419 | Shopping list becomes the receipt; log prices | **BUILT/PLANNED** | price-observation substrate (FU-213) + shopping close-out price entry |
| L46 | Stock-vs-product explainer before adding stock items | **REPLACED (mooted)** | the everyday user never meets products, so the explainer is retired (§5). **Needs user awareness** |

**Net:** of ~30 product bullets, the large majority are **BUILT** or **TRACKED**; ~3 change
disposition under the pivot (L191, L46, and the search-page cluster → companion) and want a quick
user confirm; a bug-and-polish cluster + two small gaps (L197, L205/206) are logged as **FU-214**
for the next browser pass. **Nothing is silently dropped.**
