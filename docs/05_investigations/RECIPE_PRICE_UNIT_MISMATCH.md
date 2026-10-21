# Recipe price-unit mismatch — how often do shelf units and recipe units disagree, and what should Dora do about it?

**Type:** investigation · **Status:** 🟡 open — recommendation made, owner decision pending
**Raised:** 2026-09-05 (owner feedback batch, recipe view item 1)
**Relates to:** FU-855, FU-856, ADR-073, R-076, `recipe_cost.py`, `domain/units.py`

> *"Is there a UX issue with the price estimation? What is the most common
> units for sold products and recipes and do they match (complete overlap) or
> are there discrepancies and if so how do we combat that. For example I can
> think of someone buying ice cream that is priced in litres (1L), but then the
> recipe may go by weight (200g). How do we approach this situation in a
> meaningful way for the end user? Do we guess? Do we omit non convertible
> price observations … for the ingredients unit and make it more obvious to the
> end user in the explanation modal?"* — owner, 2026-09-05

**Note on evidence.** The owner's install holds invented seed data, so the
"what units do real products and recipes actually use" half of the question
cannot be answered from this database and was researched externally instead
(sources at the end). The "what does Dora do today" half is answered from the
code and is exact.

---

## 1. Answer up front

**Yes, there is a UX issue, and it is larger than the ice-cream case.**

1. The units **mostly** overlap, but the residue is not evenly spread — it
   concentrates in a few predictable, nameable classes, of which ice cream is a
   textbook member (§3).
2. **Dora already owns the machinery to solve the biggest class and does not
   use it.** `domain/units.py` carries a 77-entry ingredient density table that
   converts mass↔volume, and `recipe_cost.py` calls the converter *without*
   passing the ingredient name, so the density branch is dead code on this path
   (§4). This is a one-keyword-argument bug sitting under a design question.
3. The honest-gap stance (ADR-073) is **right** and should not be reverted. But
   "we can't price this" is currently the answer to two very different
   situations — *nothing could bridge these units* and *we didn't look up a
   fact we already have* — and the explanation modal cannot tell the user which
   (§5).
4. **Recommendation: bridge what is knowable, never guess, and say which.**
   Three tiers, §6. No revert of ADR-073, no density guessing for unknown
   ingredients.

---

## 2. What Dora does today, exactly

Pricing runs through `recipe_cost._line_cost`. Each ingredient is either
*measured* (its unit resolves to a mass/volume/count dimension) or *counted*
(no unit, an unknown unit like "tins", or an explicit count unit).

| Recipe side | Price side | Today |
|---|---|---|
| mass (`200 g`) | per mass (`$/kg`) | ✅ converts, prices |
| volume (`200 ml`) | per volume (`$/L`) | ✅ converts, prices |
| count (`2`, `2 tins`) | per item (`pack_count`, or count-dimension size) | ✅ prices |
| **mass (`200 g`)** | **per volume (`$/L`)** | ❌ **`unit_mismatch` — the ice-cream case** |
| **volume (`200 ml`)** | **per mass (`$/kg`)** | ❌ `unit_mismatch` — the inverse |
| count (`2 tins`) | per mass/volume, no `pack_count` | ❌ `unit_mismatch` (FU-855) |
| mass/volume | per count (`$/bottle`, no size) | ❌ `unit_mismatch` — genuinely unknowable |

The last row is correct and must stay: a price per bottle with no recorded
bottle size says nothing about what 200 ml costs. This is the `$1590 Juice
Bowl` the 2026-08-19 fix removed.

Rows 4 and 5 are the subject of this document.

---

## 3. Do the units overlap? Mostly — and the gaps are predictable

**Products.** Packaged-goods labelling is not a free-for-all; it is regulated,
and the regulation is what makes the mismatch classes predictable. The general
rule across AU, US and CA is that **solid, semi-solid and viscous foods declare
by weight, and liquids declare by volume**. In Australia the measurement
marking is enforced by the National Measurement Institute and must be metric.

The interesting part is the **exceptions** — products that are solid-ish but
sold by volume anyway, by established trade custom:

- **Ice cream and frozen desserts** — the owner's example, and the canonical
  case. Sold in litres/pints because the industry has always done so (and
  because *overrun*, the air whipped into it, makes volume the commercially
  meaningful figure while weight varies with aeration).
- Some beverages, stocks and concentrates that recipes treat by weight.

**Recipes.** Recipe units are genuinely mixed and the mixture is cultural:
metric recipes (AU/UK) lean to `g`/`ml`, US recipes lean to volumetric `cups`
and spoons even for dry solids. Dora's own vocabulary reflects this — 14
canonical volume units against 6 mass units.

**So:** overlap is high but not complete, and the residue clusters in two
shapes — *a solid sold by volume* (ice cream), and *a solid measured by volume*
(a cup of flour against a `$/kg` bag). Both are mass↔volume. Both are
**exactly what a density table is for.**

The count↔measure gap (FU-855) is a different and harder shape, because no
table can say how many tins are in a 400 g product.

---

## 4. The finding: the density bridge exists and is never called

`domain/units.py` defines:

```python
INGREDIENT_DENSITY_G_PER_ML: dict[str, float] = { ... }   # 77 entries
```

and `convert()` accepts an `ingredient=` keyword that switches on it:

```python
if {src.dimension, dst.dimension} == {MASS, VOLUME}:
    if not ingredient:
        return None
    density = INGREDIENT_DENSITY_G_PER_ML.get(ingredient.lower())
```

`recipe_cost._line_cost` calls it like this:

```python
converted = units.convert(qty, ing_unit, price.unit)   # no ingredient=
```

Demonstrated against the live table:

```
convert(200, 'g', 'L')                      -> None      # today: "unpriced"
convert(200, 'g', 'L', ingredient='cream')  -> 0.2       # available, unused
'ice cream' in INGREDIENT_DENSITY_G_PER_ML  -> False     # and not in the table
```

So the ice-cream case fails **twice**: the call site discards the one argument
that would let it work, and the table wouldn't have the entry if it didn't.
The table is currently consumed only by the assistant's conversion tool — it
was built there and never wired into pricing.

This is not a guess and not a heuristic. A density lookup for a *named* known
ingredient is the same species of fact as a unit factor, and it is precisely
what professional recipe-costing systems do — the trade reference is literally
a book of per-ingredient weight-to-volume equivalents (*The Book of Yields*),
and costing software is expected to convert purchase units to recipe units off
a per-ingredient factor rather than a global rule.

---

## 5. The UX half: one message is doing three jobs

`unit_mismatch` renders as **"Units don't match the price"** for all of:

- *we know the density, we just never looked* (fixable — §4);
- *this is a real unknown* (a `$/bottle` price and a `200 ml` ask);
- *this is a counted item against a measured pack* (FU-855).

The user cannot tell which, so the modal cannot tell them what to **do**. The
third case has a concrete user action (record the pack count — blocked by
FU-856), the second has one (record the product's size), and the first has
none because it shouldn't have happened.

This is the owner's own instinct in the question — *"make it more obvious to
the end user in the explanation modal"* — and it is correct, but the message
split only becomes useful **after** §4, because today most of what lands in
this bucket is the fixable case.

### On "do we omit non-convertible price observations?"

The owner asked whether, when an item's observations are mostly in one unit and
some in another, the odd ones should be dropped.

**Finding: this is already how it works** — `your_prices.py` picks one
dimension and skips every observation outside it:

```python
active_dim = latest_def.dimension          # the MOST RECENT observation's
...
if obs_def is None or obs_def.dimension != active_dim:
    continue                               # minority-dimension rows dropped
```

Within the chosen dimension everything normalises to a canonical unit (`L`,
`kg`, `ea`), so `ml` and `L` observations combine correctly. Across dimensions
they never mix. So there is no population of odd-unit observations being
silently averaged in, and the owner's proposed fix is already the behaviour.

**But the selection rule is worth a second look, and it is a new finding.**
The surviving dimension is whichever the *latest* observation happened to use —
not the majority. An item with nine observations in `kg` and one stray in `ea`
will, if the stray was logged most recently, throw away all nine and compute a
baseline from the one. Recency is a defensible tiebreak (it tracks how you buy
the thing *now*), but it is not what the owner assumed was happening, and a
single mis-keyed entry can silently reset an item's price history. Logged as
**FU-876**; it is a pricing-substrate question, not a recipe-costing one, which
is why it isn't in §6's tiers.

---

## 6. Recommendation — three tiers, no guessing

**Tier 1 — bridge what is knowable (do this).**
Pass the ingredient name into `units.convert` from `_line_cost`, and extend
`INGREDIENT_DENSITY_G_PER_ML` with the pantry items it lacks (ice cream and
frozen desserts first, since that is the reported case). Cost: one argument
plus table rows. This converts the largest mismatch class from "unpriced" to
correctly priced, using a fact the app already holds.

**Tier 2 — split the explanation (do this, after tier 1).**
Break `unit_mismatch` into reasons that imply an action:

| Reason | Message | Action it implies |
|---|---|---|
| `unit_unknown_density` | "We don't know what a litre of this weighs" | none — or offer to record it |
| `unit_no_pack_size` | "This is priced per pack, and we don't know the pack's size" | record the product size |
| `unit_no_pack_count` | "This is priced by weight, and we don't know how many are in a pack" | record `pack_count` (FU-856) |

Each is a sentence the user can act on, which the current one is not.

**Tier 3 — do NOT guess (recommend against).**
Do not apply a default density (~1.0 g/ml) to unknown ingredients. It is right
for water and wrong for everything else by up to 2.5×, and it would reintroduce
exactly the confident-wrong-number failure that ADR-073 and the 2026-08-19 fix
were written to end. An honest gap still beats a confident wrong number — that
stance is unchanged and this document does not propose relaxing it.

**A note on scope creep:** professional costing also applies *yield/shrinkage*
(AP vs EP — a peeled onion costs more per usable gram than a bought one). That
is real and correct, and it is deliberately **out of scope** here: it is a
second multiplier per ingredient, it needs its own data, and Dora is a
household pantry app, not a commercial kitchen. Noted only so a future reader
knows it was considered and set aside.

---

## 7. Open decisions — closed

| # | Decision | Resolution |
|---|---|---|
| D1 | Do we guess at densities for unknown ingredients? | **No.** Recommended against in §6 tier 3; preserves ADR-073. Closed inline. |
| D2 | Do we omit minority-unit price observations? | **Already the behaviour** — §5; the premise doesn't hold. But the *selection rule* is recency, not majority, which is a separate finding → **FU-876**. Closed inline. |
| D3 | Ship tier 1 (density bridge)? | **Owner call.** Spawned as **FU-874**. Recommended yes. |
| D4 | Ship tier 2 (split the mismatch reasons)? | **Owner call.** Spawned as **FU-875**. Recommended yes, after D3. |
| D5 | Does the narrowed count-vs-pack coverage (FU-855) read acceptably? | Unchanged, still owner's. Left with **FU-855**; this doc supplies the context it was waiting on. |

No undecided items remain in this document.

---

## 8. Feedback coverage

Maps the owner's 2026-09-05 recipe-view bullets. (The 06-Jun-2026 feedback file
has no bullet on price-unit reconciliation — this surface post-dates it; the
nearest relatives are the cost items already closed by ADR-073/R-076.)

| # | Feedback bullet (2026-09-05, recipe view) | Where it lands |
|---|---|---|
| R1 | "Is there a UX issue with the price estimation?" | §1, §5 — yes; two distinct issues identified |
| R2 | "What is the most common units for sold products and recipes" | §3 — products regulated weight-vs-volume; recipes culturally mixed |
| R3 | "do they match (complete overlap) or are there discrepancies" | §3 — high overlap, residue in two nameable classes |
| R4 | "if so how do we combat that" | §6 — three tiers, tier 1 + 2 recommended |
| R5 | The ice-cream 1 L vs 200 g example | §4 — reproduced exactly; fails twice; both failures fixable |
| R6 | "Do we guess?" | §6 tier 3 — **no**, recommended against, with the reason |
| R7 | "Do we omit non convertible price observations…" | §5 — premise doesn't hold; already normalised per dimension |
| R8 | "make it more obvious to the end user in the explanation modal" | §6 tier 2 — split into three actionable reasons |
| R9 | "Consistency. Chef hat should be the icon used for cook now." | Out of scope here — **built** in the same batch (icon unification) |

---

## 9. Sources

- [Net quantity on food labels — Canadian Food Inspection Agency](https://inspection.canada.ca/en/food-labels/labelling/industry/net-quantity)
- [Net Weight Labelling: FDA Compliance Guide — Menusano](https://www.menusano.com/net-weight-labelling-fda-compliance-guide/)
- [Overrun calculations — Ice Cream Technology e-Book, University of Guelph](https://books.lib.uoguelph.ca/icecreamtechnologyebook/chapter/overrun-calculations/)
- [Truth in labelling, weights and measures — Food Standards Australia New Zealand](https://www.foodstandards.gov.au/consumer/labelling/truth)
- [Pre-pack label & weight regulations in Australia — Matthews](https://www.matthews.com.au/blog/quick-compliance-essentials-what-you-need-to-know-about-pre-pack-label-weight-regulations-in-australia)
- [Conversion Factors: International Cookbooks and Ingredient Mass vs. Volume — Chemistry LibreTexts](https://chem.libretexts.org/Ancillary_Materials/Exemplars_and_Case_Studies/Exemplars/Foods/Conversion_Factors:_International_Cookbooks_and_Ingredient_Mass_vs._Volume)
- [Weight vs. Volume Measurement in Cooking — ThermoWorks](https://blog.thermoworks.com/weight-volume-measurements/)
- [Conversions and the Book of Yields — reciProfity](https://costguard.zendesk.com/hc/en-us/articles/235696388-Conversions-and-the-Book-of-Yields)
- [Converting Between Weight and Volume — reciProfity](https://costguard.zendesk.com/hc/en-us/articles/115005853468-Converting-Between-Weight-and-Volume)
- [Never Assume 100% Ingredient Yield — meez](https://www.getmeez.com/blog/never-assume-100-ingredient-yield)
