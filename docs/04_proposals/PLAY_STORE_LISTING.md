# Dashy Dora — Play Store listing (draft)

**Status:** draft copy + screenshot plan; no submission yet. Kept in the
repo alongside the Capacitor scaffold (P8-10, 2026-07-04) so the day we
publish, the copy doesn't need to be reinvented. All wording is
consistent with the Charter language and the current UI.

## Store metadata

| Field | Value |
|---|---|
| App name | **Dashy Dora** |
| Short description (80 chars) | Your pantry at your fingertips — plan meals, shop smart, waste less. |
| Package name | `io.github.bentalese.dashydora` |
| Category | Food & Drink (secondary: Lifestyle) |
| Content rating | Everyone |
| Contains ads | No |
| In-app purchases | No |

### Full description (draft, ≤ 4000 chars)

Dashy Dora is a household pantry, shopping list and meal planner that
actually knows what you have. Track what's on your shelves. Cook what
you can make right now. Shop only for what you're really out of.

Dora is designed for the household that hates food waste. Every stock
item you add builds a picture of your kitchen; when it's time to shop,
Dora tells you what's actually low. When you're standing in front of
the fridge wondering what to make, she tells you which of your saved
recipes you can cook right now — no missing ingredients, no
last-minute dashes to the shop.

**What Dora does**

- **Pantry tracking** — add items by scanning, typing, or importing.
  Track expiry dates so nothing gets buried and forgotten.
- **Shopping lists** — one primary list you shop from, plus lists for
  themed trips. Tick items off as you shop; the pantry updates itself
  when you're done.
- **Meal plans + recipes** — save recipes, plan the week, generate a
  shop list from the plan. Cook mode reads steps aloud so you keep
  your hands in the mixing bowl.
- **Kitchen health** — a Dora Score that tracks waste, budget,
  freshness, run-outs and stocktake. See how you're doing this month
  versus last.
- **Culinary memory** — meals cooked, spend by category, year-over-
  year — the report page answers "what did we make last Christmas?"
  and "how has dairy changed year on year?"

**Bring your own instance**

Dashy Dora is a companion app — it needs a Dora backend to talk to.
Run one at home on any old laptop or Raspberry Pi, or point it at a
hosted instance if a friend runs one for you. On first launch the app
asks for the instance URL; that's the only setup step.

**Privacy**

Your data lives on your Dora instance, not on our servers — we run
none. Purchase history, recipe library, and pantry contents never
leave the box you point the app at.

## Screenshot plan

Play Store wants 2–8 screenshots at 1080 × 1920 (portrait) or higher.
Capture these in order — the first three are what shows in the
grid without expanding, so lead with the strongest.

1. **Dashboard** with the Dora Score card at the top + Kitchen zone
   (dora_score, stock, expiring, shopping-list-progress).
   Caption: "Your pantry at a glance."
2. **Cookbook grid** with a mix of recipe cards, some green
   ("cookable now") and some amber. Caption: "Cook what you actually
   can, right now."
3. **Shopping list in shop mode** — a themed list with three ticked
   lines, a categorised group header visible. Caption: "Shop the list,
   the pantry updates itself."
4. **Recipe cook mode** — step 3 of a real recipe, timer running,
   ingredient panel visible. Caption: "Hands in the bowl, Dora reads
   the steps."
5. **Reports → Memory** — spend-by-category donut + YoY list.
   Caption: "See what you actually made and spent — no invention."
6. **Add a stock item** — quick add sheet with the scan button.
   Caption: "Add what you buy, however you want."

Capture at 1080 × 2400 (Pixel 6 viewport) using Chrome DevTools mobile
emulation on the running SPA. Save into `packaging/store-assets/play/`
before submission (dir doesn't exist yet — no submission planned).

## Feature graphic (1024 × 500)

Dora mascot on the primary yellow (#f5c462) with the wordmark to the
right and the tagline "Your pantry at your fingertips."

## Icon

Adaptive icon: `mipmap-anydpi-v26/ic_launcher.xml`, foreground = the
Dora mascot at ~66% of the safe zone on transparent, background =
`#F5C462`. Generated from `web_app/public/icons/web-app-manifest-512x512.png`
at P8-10 time. See `web_app/src-capacitor/android/app/src/main/res/mipmap-*/`.

## Not in scope for P8-10

- Actual submission (needs a Google Play Console account, $25 one-off).
- iOS App Store listing — the iOS platform is scaffolded but has never
  been built. Draft copy above is platform-neutral and reusable.
- Localised store listings — English (Australia) only until there's
  interest.
