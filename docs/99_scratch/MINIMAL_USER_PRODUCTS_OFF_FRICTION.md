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

Tracked as FU-181 — promote this scratch into a proper assessment / §2.6
amendment with a per-surface coverage table against the feedback bullets, so
the minimal-user path is supported as a first-class workflow rather than a
fallback.
