# Proposal — Surfacing the Zero-Input belief beyond the stock pages (FU-653)

**Status: BUILT 2026-08-17** (server + SPA + tests, agent-verified live at the
API layer; three client renders owed a browser walk — see `DORA_VERIFY.md`).

Owner ask, verbatim (2026-08-17):

> How could the inference "zero input" engine be surfaced usefully with recipes
> and shopping lists (other locations stock items surface). For example, recipes
> recording all ingredients as available but according to the inference engine
> one of the stock items is out and therefore Dora can infer the possibility of
> the recipe not being cookable (and vice versa with not cookable but actually
> might be). Of course that would not actually impact the other functionality
> (its cookable state shouldn't be changed based on that, and it shouldn't be
> filtered based on that either). Shopping lists could suggest items based on
> inference (but not get in the way of the normal flow). Possibly other ways the
> stock items inference engine could surface in the app? Meal planner? Also each
> of these should be a separate toggle with the current one being the stock
> overview/detail toggle.

---

## 1. The problem

P8-07 built a belief engine that can say "I think you're out of tinned tomatoes",
and then showed it in exactly one place: the stock overview and the stock-item
detail. Everywhere else a stock item *appears* — as a recipe ingredient, as a
line you didn't put on a shopping list, as the thing Thursday's dinner needs —
the app reads only the recorded level. So the same install can simultaneously
show "Dora thinks you're out of tuna" on the stock page and "cookable now" on a
tuna recipe, and never connect the two.

## 2. The rule this design is built around

**The overlay adds a remark. It never changes an answer.** Stated by the owner
and treated here as the load-bearing constraint:

- `cookable` / `missing_count` stay computed from **recorded** levels by
  `domain/recipe_cookability.py`. Untouched.
- The cookbook is **never filtered or sorted** on a belief.
- Shopping lists get **suggestions**, never lines. Nothing is auto-added.
- The meal planner's shortfall and "need to buy" figures are **unchanged**.

Consequence for the architecture: the overlay lives in its own module
(`features/stock_items/inference_overlay.py`) next to the belief engine, *not*
inside `recipe_cookability`. Putting it there would invite exactly the merge
this rule forbids.

## 3. When Dora is allowed to speak (the honesty gates)

A belief is only remarked on when **all** of:

| Gate | Why |
|---|---|
| `is_inferred` | Not an echo of a level you confirmed this week — that's not inference, it's your own data read back to you. |
| `differs_from_recorded` | Agreement is not news. (The seed's "Crackers (agrees, silent)" fixture is the control case.) |
| confidence is `high` or `medium` | A low-confidence guess contradicting a recorded fact is noise — and this appears on pages the user opened for a different reason. |

Two directions come out of it: **believed_out** (recorded available, believed
out) and **believed_available** (recorded missing, believed back).

Band choice: only the **`out`** band can put a recipe at risk, because
`stock_status.is_missing` counts out-of-stock (not low) as missing for
cookability. Following the same contract keeps the remark and the verdict
talking about the same thing.

## 4. Per-surface design

### 4.1 Recipes (`inference_recipes_enabled`)

Two hint kinds, computed by the pure `recipe_hint(rows, divergence, *,
missing_count, unlinked_count)`:

- **`at_risk`** — recorded cookable (`missing_count == 0`), and ≥1 required,
  linked ingredient is believed out. Chip: *"May be short"*, outline amber.
- **`maybe_cookable`** — recorded not-cookable, and **every** recorded-missing
  required ingredient is believed available. Chip: *"May be cookable"*, outline
  green. *All*, not *any*: rescuing one of three missing ingredients still
  leaves you unable to cook it.

Silent when: any required ingredient is **unlinked** (recorded cookability is
already the honest `None` — a guess layered on an admitted unknown is worse than
silence); the recipe has no linked required ingredients; nothing diverges.

Optional ingredients are ignored, matching cookbook revision §1.9.

Renders as an outline chip on the recipe card (the filled chips there state
facts; this is an opinion) and as a bordered remark card **under** the
cookability verdict on the detail page — deliberately separate so the two can't
be read as one contradictory verdict.

### 4.2 Shopping lists (`inference_shopping_enabled`)

A dismissible strip **above** the lines: *"Dora thinks you may be out of…"* with
one tappable chip per item; tapping adds it as an ordinary line. Scoped to items
**recorded as available** — an item you've already recorded as out is the
existing low-stock machinery's job, and re-suggesting it would be Dora taking
credit for what you told her. Capped at 6, name-sorted (stable between
refreshes), never shown on a finished list. Dismissal is in-session only:
persisting "hidden" would need a per-item ledger and an expiry policy to answer
"hidden until when?".

### 4.3 Meal planner (`inference_meal_plan_enabled`)

The same recipe rule applied to each planned entry, rendered as a small glyph on
the entry chip with the explanation on its tooltip. Never on an entry that's
already been cooked — a warning about a meal you've eaten is noise.

### 4.4 Considered and not built

- **Dashboard tile** ("3 things Dora thinks you're out of") — the dashboard is
  already the most-contested surface in the app, and the alerts/quick-check
  generator (`features/suggestions/generators.py`) covers "ask me about the
  uncertain ones" without a new card. Revisit only if asked.
- **Cook mode** — mid-cook is the worst possible moment for a hedge. You're
  standing at the bench; either the tin is there or it isn't.
- **Filtering / sorting anything by belief** — explicitly ruled out by the owner.

## 5. The toggles

| Surface | Column | Default |
|---|---|---|
| Stock overview + item detail | `inferred_pantry_enabled` (unchanged, P8-07) | **on** |
| Recipes | `inference_recipes_enabled` | off |
| Shopping lists | `inference_shopping_enabled` | off |
| Meal planner | `inference_meal_plan_enabled` | off |

The three new ones default **off** (unlike the stock one, which is the headline
experience of a page about stock levels): they annotate pages the user opened to
do something else. Charter P10, anti-creep. All four sit together under
Settings → Assistant → Zero-Input Pantry.

`SURFACE_FLAGS` in the overlay module is the single map from surface id to
column; no surface reads a flag by hand, and `resolve_divergence` returns the
empty overlay when a surface is off, so "off" and "nothing to say" are the same
code path.

## 6. Cost

`gather_beliefs_for_items` is 3 queries for any number of items, so each surface
does **one bulk gather** for the items its page references — not per recipe, not
the whole pantry (except shopping lists, where the candidate set genuinely is
"everything not already on the list"). A user with the surface off pays one
`User` read.

## 7. Open decisions — closed

- *Should the recipe hint also cover the `low` band?* **No** — `is_missing`
  counts only out-of-stock, and a hint using a different threshold from the
  verdict it sits beside would be incoherent. Recorded here so it isn't
  re-litigated.
- *Should suggestions be persisted-dismissible?* **No** (§4.2 rationale).
- *Dashboard / cook mode?* **Won't build** (§4.4). If the owner disagrees, they
  are additive — a new surface id, a new column, one hydration step.

No item in this section is left open; nothing was spawned as a follow-up.

## 8. Feedback coverage

The ask is one bullet from the owner's 2026-08-17 Settings feedback list (not
the `Feedback _ Fixes - as of [06-Jun-2026].md` set, which pre-dates the belief
engine). Mapped in full:

| # | Owner's bullet | Where |
|---|---|---|
| 1 | Surface the inference engine with **recipes** | §4.1 |
| 2 | Recipe reads cookable but an ingredient is believed out → flag the possibility | §4.1 `at_risk` |
| 3 | …and the inverse (not cookable, but might be) | §4.1 `maybe_cookable` |
| 4 | Must **not** change the cookable state | §2 — `cookable` untouched; verified live (hint present, `cookable: true`, `missing_count: 0`) |
| 5 | Must **not** filter on it | §2 — no filter/sort axis added |
| 6 | Surface with **shopping lists**, suggestions that don't get in the way | §4.2 — suggestions strip, nothing auto-added, dismissible |
| 7 | "Possibly other ways… Meal planner?" | §4.3 built; §4.4 records what was considered and declined |
| 8 | Each gets its **own toggle**, the current one being stock overview/detail | §5 |

## 9. From the original spec

`docs/00_original_spec/` pre-dates the belief engine entirely (P8-07 came out of
the champion plan, not the first spec), so there is nothing there to extract for
this surface.
