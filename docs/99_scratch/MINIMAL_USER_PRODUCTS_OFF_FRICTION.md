# Minimal-user workflow — friction with Products off

**Date:** 2026-06-14
**Status:** scratch — talk-time assessment, not a proposal yet. Captured for
later promotion (see FU-181).
**Trigger:** user asked to assess the workflow of someone who wants the
fuss-free experience and may not want to use the Products feature — what
friction would they hit, and how do we upgrade their experience to prevent it.

Grounding: C-cross §2.6 (install-level feature-flag panel) + §2.2 (per-user
money opt-in) already exist as the levers; this doc audits whether the
surfaces collapse cleanly when Products is the flag turned off, and proposes
the upgrade direction.

---

## What "the fuss-free user" actually wants

Pantry + recipes + meal plan + a shopping list that's a checklist. They never
want to think about merchants, offers, price history, or "which exact Coles
SKU did I buy." Products-as-a-feature (My Products, Product Search, linked-
product offers, cart button, deals email, ingestion API, price history) is
exactly the surface they're opting out of.

C-cross §2.6 names this as an install-level capability flag, and §2.2 handles
the money/cost dimension as a separate per-user opt-in. So the levers exist —
the question is whether every surface honours them cleanly or just empties
out and leaves scar tissue.

---

## Friction inventory for "Products off"

Surface-by-surface — places the current code (or in-flight design) still
assumes Products are on:

1. **Shopping list** — biggest one. Offer picker per line, cheapest-merchant
   sort, merchant grouping, cart button, "log what you paid" close-out. For a
   no-Products user this is ~70% noise. They want: stock-item name, quantity,
   checkbox, done.
2. **Stock-item detail** — linked-products list, product offers, price-history
   chart. Whole right-hand section is dead.
3. **Stock-item *creation*** — if the form ever nudges "link a product / add
   price," it's selling a concept they rejected. Should silently drop those
   affordances.
4. **Recipe ingredients** — any "no linked product" empty state or
   "link product" affordance on an ingredient row is friction; ingredients
   are just stock items to this user.
5. **Recipe cost estimate / meal-plan budget rollup** — already covered by
   the money opt-in (§2.2), but the *compound* state (money on, products off)
   needs to degrade cleanly: cost estimate just isn't available, not a
   broken/disabled control.
6. **Navigation** — My Products, Product Search, Deals, Cart all need to
   disappear from the nav, not grey-out.
7. **Settings** — preferred stores, scanning, deals-email, ingestion/companion
   — all hidden, not visible-but-disabled.
8. **Onboarding** — the C-5 stock-item-vs-product explainer is *literally
   teaching the concept they don't want*. If they flip Products off at the
   feature-flag wizard step, the explainer step and the preferred-stores step
   should be skipped, not just shown-then-ignored.
9. **Global search / barcode scan** — search scope narrows to stock items +
   recipes; barcode scanning loses its product-resolution purpose (Dora's own
   QR labels still work for navigation).
10. **Alerts (C-9)** — deal/price-drop alert types vanish from the matrix.
11. **Empty states** — "You haven't linked any products yet" is the worst
    possible message for this user. The fix isn't a better empty state; it's
    no surface at all.

---

## How to upgrade the experience

Two principles, then specifics.

### A. Install flag must collapse surfaces, not blank them

The current §2.6 design correctly says "feature off at install level hides it
for everyone" but the implementation discipline matters: nav items removed,
tabs removed, columns removed, settings sections removed. A user who turned
Products off should genuinely not be able to tell Products *exists* in the
app. Anything less leaves them wondering what they're missing.

### B. The shopping list needs a first-class "checklist mode"

It's the surface most damaged by Products being off, and its current design
assumes Products on. Worth its own design decision: when Products is off,
the shopping list defaults to grouped-by-location (aisle order) or just a
flat checklist — no offer column, no cart button, no merchant logic, no
price logging. Close-out is just "mark all bought."

### Specific upgrades (ordered by leverage)

- **Onboarding wizard branches on the feature-flag step.** If user disables
  Products there, the wizard skips the stock-vs-product explainer, the
  preferred-stores step, and the "money features" step (it's moot — there's
  nothing to price). Shorter onboarding *is* the upgrade.
- **Stock-item create/edit form has zero product affordances when off.** No
  "link product later," no "add price." Just name, location, quantity, unit.
- **Shopping list collapses to checklist mode.** Group by location if the
  user has set aisle order, otherwise flat. Quantity + checkbox. Close-out
  marks consumption events without asking what they paid.
- **Recipe detail ingredients hide all product/cost affordances.** Just the
  ingredient line, quantity, in-stock pill. Cost estimate section absent
  (not "—" placeholder).
- **Nav + settings render conditionally.** My Products, Product Search,
  Deals, Cart, Ingestion, Companion, Preferred Stores, Scanning, Deals Email
  — all hidden, not disabled.
- **Persona-led default.** Worth considering: during onboarding, ask "what
  do you want Dora to do for you?" with two presets — *Pantry & meal
  planning* (Products off, money off) vs *Pantry + save money on groceries*
  (Products on, money on). The flags exist for fine control later; the
  preset is the effortless path.

---

## The decision worth flagging

§2.6 currently lists Products as one candidate among several capability
flags. It deserves to be treated as **the** flag that most reshapes the app —
not a peer with "deals email" or "nutrition." It cleaves the product into
two genuinely different products: a pantry+cooking app and a
pantry+cooking+savings app. Worth elevating in the proposal so the
implementation chunk explicitly audits every Products-touching surface for
the off path, rather than treating it as a generic capability flag.

Tiebreaker check: Effortless + Anti-creep both favour the
off-by-default-for-new-users reading, or at least the persona-preset path.
The original spec is Products-centric, but charter rules say current charter
wins.

---

## Next step

Tracked as FU-182 — promote this scratch into a proper assessment / §2.6
amendment with a per-surface coverage table against the feedback bullets, so
the minimal-user path is supported as a first-class workflow rather than a
fallback.

---

# Addendum — 2026-06-15 brainstorm round (data model, naming, ingestion)

Continuing the talk-time. Captures the model + UX decisions reached after
the initial assessment so they're not lost before promotion to a proposal.
Some of this overlaps the onboarding C-5 v3 redesign — see §3.2 personas +
§3.3 conditional explainer there for what's already in flight; this scratch
holds the *deeper* model + naming decisions C-5 doesn't own.

## 1. Pricing model — unify the read path, don't flatten

Reframe: **`StockItem` + `StockItemPriceObservation` is the universal
substrate. `Product` + `ProductOffer` is an optional SKU-resolution layer
that feeds the same substrate.**

- New canonical record: `StockItemPriceObservation(stock_item_id, price,
  qty, unit, observed_at, source: 'manual' | 'shopping_close_out' |
  'product_offer')`. **No merchant on the observation** — see §3.
- Stock-item price-history chart reads `direct observations ∪
  observations-derived-from-linked-products` (Products on) or just direct
  observations (Products off).
- "Products off" is not a degraded mode — it's the substrate without the
  optional overlay. Every consumer (cost estimates, stock-value report,
  shopping-list pricing, recipe budgets) is rewritten *against the
  substrate*, with Products as an enriching data source when present.
- Server-owned helper `get_stock_item_unit_cost_at(item, when)` picks the
  best signal (product-derived if available + Products on, else direct
  observation, else null). R-003 — single derived fact, server-owned.

### Mode-flip behaviour (non-destructive both ways)

- **Off → on:** existing direct observations stay; new ProductOffers add
  merchant-attributed points alongside on the chart.
- **On → off:** ProductOffer history isn't deleted, just hidden from the
  chart. Don't roll up — mixing sources after a mode switch is exactly the
  messiness the user flagged. Hidden ≠ destroyed.

### Money + Products are independent layers (2×2)

|  | Money on | Money off |
|---|---|---|
| **Products on** | full SKU + price (today) | SKU mapping only, no $ |
| **Products off** | stock-item price logging | pure checklist |

The bottom-left (Products off + money on) is the persona the current C-5
v3 onboarding does **not** directly expose — both "Pantry & cooking" and
"Pantry + spend tracking" bundle products+money together. **Open thread
for onboarding:** ensure the Customise branch lets this combo be reached,
or add it as a fourth preset.

## 2. Shopping-list-as-receipt — yes, and not only in shopping mode

- Shopping-list close-out is the most natural place for the price input,
  but log-a-price affordances should also live on: stock-item detail
  ("log a price" button), a quick-add modal, future receipt-import flow.
- All write into `StockItemPriceObservation` with appropriate `source`.
- Gated by **money opt-in**, not Products. The price input simply doesn't
  render when money is off, regardless of Products.

## 3. Merchant on observations — DROPPED for simple mode

Decision: `StockItemPriceObservation` carries no merchant attribution.
Rationale: in simple mode prices are just "how much does this cost me,"
not a cross-merchant comparison. Comparison is exactly what
Products-on is for.

For shopping-list grouping (still useful in simple mode):

- **`StockItem.usual_merchant_id` (nullable)** — user sets "I usually buy
  this at Coles" once. Shopping list groups by it.
- **Per-shopping-list-line override** — user reassigns at trip-build time
  (e.g. "this week I'm doing one big Woolies shop, group everything under
  Woolies"). Override lives on the line, not the stock item.
- Single field, no auto-derivation from observation history (because the
  history doesn't carry merchant). Cheap, intuitive, no drift.

## 4. Merchants → Stores rename + user-uploaded logos

UI **and entity** rename to "Store" (pre-release, no compat shims —
R-007 / honest naming). "Merchant" is payments/e-commerce jargon; "Store"
is what a normal person calls Coles.

Sanity checks before the rename:

- Verify no existing `Store` symbol in the codebase means something else
  (Pinia store, "store of value" etc.). Locations is the most adjacent
  concept but unambiguous (locations are in-home, stores are external).
- Future payments/checkout integrations will likely use "merchant" at the
  integration boundary — translate there, not in the domain model.

Management page:

- Single management surface (settings → Stores). **No auto-create from
  any other code path** (notably ingestion — see §6).
- **No prefilled list.** Sidesteps locale-coupling and the legal-logos
  issue in one move. Users add their own (Coles, ALDI, the corner deli,
  whatever).
- **User-uploaded image per store.** Reuse existing image-upload infra
  (recipes/stock items have it from C-cross §2.8). **Dora ships zero
  logos** — legal safety.
- **Fallback when no image:** the existing hash-swatch + initial pattern
  from `ProductSearchCard` (referenced in ENGINEERING_STANDARDS.md). No
  new pattern needed.
- Edit / disable / delete (soft, with referential safety on offers +
  shopping-list lines).

## 5. The stock-item vs product confusion — the real UX risk

Data model is clean, but the *concept* is two-thirds of the way up the
abstraction ladder for non-technical users. Mitigations need to be
layered:

1. **Onboarding explainer** — already planned in C-5 §3.3, conditional on
   `products_enabled`. **Copy guidance for that step:** use the milk
   example concretely — *"'Milk' is a stock item — a thing you keep.
   'Vitasoy Oat Milky 1L @ Coles' is a product — a specific thing you can
   buy."* Pair with a *don't*: *"Don't name your stock items after
   brands."*
2. **Glossary / help entry** — short, plain, milk example. Linked from
   anywhere the term appears. Lives in PROPOSAL_HELP_OVERLAY.md content
   scope.
3. **In-context micro-copy** — stock-item-create form gets a one-line
   tooltip when Products is on: *"A type of thing you keep — like 'milk'
   or 'flour.' Don't name it after a brand — that's what products are
   for."* (In simple mode the tooltip drops the second sentence — the
   word "product" doesn't appear in simple-mode UI at all.)
4. **Empty-state copy** on My Products: *"Products are the specific
   brands/SKUs you buy. They link to stock items."* with the milk →
   Vitasoy example.
5. **Simple mode amplifies clarity, doesn't muddy it.** In simple mode,
   "product" effectively disappears from the UI — there's only one
   concept. Confusion can only arise in Products-on mode or at the
   transition. Argument for simple mode being a strong default for new
   users: zero confusion until they opt into the richer model.

## 6. "Simple mode" as a named identity, not the absence of Products

- Don't expose the flag as "Products feature off" anywhere user-visible.
  UI label: **Simple mode** (or co-design something better).
- **Onboarding preset** — C-5 v3's "Pantry & cooking" persona is
  effectively this; consider surfacing "simple mode" as the explicit
  label outside the persona moment (e.g. a small chip in settings).
- **Settings indicator** — small "Simple mode" chip on the settings page,
  one-line explainer, "switch to full mode" affordance. No persistent
  app-shell badge (would feel like a downgrade reminder; the point is
  simple mode is a *complete* product).
- **Codebase flag name** stays technical (`products_enabled`). UI label
  decoupled. (Standard pattern.)

## 7. No-auto-create implication for the ingestion API (Phase 2)

The companion scraper pushes products + offers + price-observations to
Dora. Each offer references a merchant/store. The "no auto-create" rule
must propagate into the ingestion API design — it cannot silently
materialise stores the user hasn't approved.

Three viable shapes:

- (a) **Hard reject** unknown-store offers. Strictest. Sender must
  pre-register stores via API.
- (b) **Quarantine queue** — unknown-store offers land in "pending
  review"; user resolves by mapping to an existing store or creating a
  new one.
- (c) **Setup mapping step** — user maps each companion-side merchant to
  a Dora store once, before ingestion is live.

Recommendation: **(c) as the happy path, (b) as the safety net** for
never-seen-before stores that appear after setup. This is a hard
constraint on PROPOSAL_INGESTION_API.md — tracked separately as a
follow-up so it lands in that proposal's coverage table.

## 8. Misc decisions confirmed in this round

- **Brand specificity dies in simple mode.** Accepted — don't half-solve
  with a "preferred brand" string field.
- **Receipt OCR — not in scope.** The shopping list *is* the receipt;
  paper-receipt parsing isn't going to ship.
- **Barcode scanning in simple mode** — scan still resolves Dora's own
  QR labels (navigation); real-world EAN scans just don't do anything.
  Acceptable for the minimal user.
- **No cross-user comparison.** Multi-tenancy is deferred (Decision 5);
  this is moot for current scope. Forecloses a future SaaS community-
  price feature, noted not blocking.
