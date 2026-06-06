# Proposal — Onboarding Redesign (C-5)

**Status:** Draft for discussion · **Date:** 2026-06-06 · Changes NO code.  
**Scope:** Redesign the first-run wizard — sell the vision before asking for data,
explain stock-item-vs-product, offer a pick-and-choose **starter template** (the
fastest path to value), capture headcount + preferred stores, add a finish
celebration, and fix the seed/copy rough edges. Ripples to the seed system, cook
mode (C-3 headcount), and settings feature-flags (deferred).

> **Charter tie-break:** Effortless (P1). Onboarding's job is to get a user to
> *value* fast without a slog. "The worst part of using this app will be getting
> data in" (L37) — so the redesign's centre of gravity is **a starter template
> that fills the pantry in a few taps**, wrapped in just enough story to explain
> why it matters.

---

## 1. Current state (from live code)

`WelcomeWizard.vue` is a 5-step wizard (4 for non-first users): **Welcome**
(name + theme + font) → **You're the admin** (first-user info card) → **Seed
catalogues** (toggle default groups / locations) → **First stock item** (a form)
→ **Take the tour** (4 feature cards). Backend: `onboarding.py` (`/seed`,
`/complete`, `/restart`; state query with `has_groups`/`has_locations`).

What's missing or rough:
- **No vision/values/workflow framing** — it jumps to data entry (L41, L43).
- **No stock-item-vs-product explainer** (L46).
- **Seed is all-or-nothing** per category; no preview, no item-level template
  (L34, L37).
- **No headcount** (L44) or **preferred-stores** (L45) capture.
- **No starter template of common items** — the highest-value gap (L37).
- **No celebration** (L39); tour covers only stock/shopping/alerts (L40).
- Theme step exposes system/light/dark but should map explicitly to
  system/pesto-light/pesto-dark (L28).
- Copy/labels: "Skip everything" → "Skip" (L35); Grocy named explicitly + the
  import is a nav-away rather than inline (L30); "you already have groups/
  locations" copy confuses on first-run (L32, L33 — see §2.6).

> **Already fixed (B5):** the dead nav (skip/finish/"show me X" did nothing —
> L25-27). Static read confirms `complete()`, `onSkipEverything()`, and the tour
> cards all navigate now. The original reports pre-date B5; **confirm in browser**.

---

## 2. The redesign

### 2.1 Sell the vision first (L41, L43) — shared auth-shell styling (L24)
Open with **why Dora exists**, not a form. A short, skimmable intro to the core
values and **the loop** (pantry → deals → meals → lists → cook → restock) using
**simple diagrams / flowcharts**, not walls of text. Style it like the login
screen (shared auth-shell — coordinates with the C19 auth-shell work). Keep it
**short** (P1) — sell it, then move on. Display name + theme + font live here.

### 2.2 Core-concept explainer — stock item vs product (L46)
**Before** asking the user to add anything: a one-screen explainer —
> **Stock item** = the thing you keep ("Milk"). Simplified, yours.
> **Product** = a specific buyable ("Vitasoy Oat Milk @ Coles"). Detailed, exact.
> You track *stock items*; you link *products* to them to find deals.

This is the mental model everything else rests on; it must land before "add stock
items."

### 2.3 Admin & features (first-user only) (L29, L42)
- Fix wording to **"Invite other users later"** (L29).
- **Feature enable/disable toggles** at first login — pick which parts of Dora are
  on (e.g. deals/scraping, meal plans, budget/money, nutrition, voice). Tell them
  **it's changeable later in admin settings** — **which means the settings side
  must gain a matching feature-flag panel** (L42; settings is deferred — noted as a
  dependency, §5/§6).

> **Open (brief):** exactly which features are toggleable at first-login (§5).

### 2.4 Household & stores (L44, L45)
- **"How many people do you cook for normally?"** → stored as the household
  headcount default that **cook mode's serving auto-adjust (C-3) reads**.
- **"Which stores do you prefer to shop at?"** → preferred merchants (off-by-
  default scraping stays the admin's call; this just seeds preferences).

### 2.5 Starter data — the fastest path to value (L34, L37, L38)
The centrepiece. Three layers, all pick-and-choose:

1. **Default groups & locations** — keep, but **all/none/some** with a **preview**
   of what gets created (the hierarchy), not a blunt toggle (L34).
2. **Starter template of common household stock items** (L37) — a curated list
   pre-populated with sensible locations (cheese → Fridge, apples → Fridge, ice
   cream → Freezer, …). **Tick on/off, customise**, then create in one go. This is
   the single biggest friction-killer — "we want people started as soon as
   possible."
3. **Demo recipe / meal / meal-plan toggles** (L38) — opt-in, each **clearly
   warned that it creates demo data** (and easily removable later).
4. **Inline import** (L30) — offer "import from a spreadsheet or another app"
   **on this page** (not a nav-away), and **don't name Grocy specifically** in the
   primary copy (the importer still supports it).

### 2.6 Fix the "you already have groups/locations" copy (L32, L33)
Assume an **empty DB** on first-run (only migration-seeded *system* data, never
user groups/locations). The conditional "you already have…" copy should appear
**only when it's genuinely true** (a later user on a shared install, or a re-run).
Static read shows it's already gated on `has_groups`/`has_locations` — so the user
likely saw it because their DB carried dev/seed data. **Confirm in browser on a
clean DB** (logged as FU-041) and ensure no migration pre-creates *user* groups.

### 2.7 First stock item — show an "added" list (L36)
If they add items here, show a **slim running list of what's been added** so they
can track it; the "× added" counter folds **into that list** rather than being a
standalone number.

### 2.8 Finish — celebrate + teach the workflows (L39, L40, L43)
- **Celebration** (confetti / a "you're set up!" moment) on finish (L39).
- Replace the bare "nav to features" tour with a **workflow / power-user explainer**
  covering **more of the key areas** (not just stock/shopping/alerts — add recipes/
  cookbook, meal plans, deals, the assistant) (L40), each a **short diagram/flow**
  that **points to the help/guides section** for depth (L43). Sell how Dora shines,
  in as few words as possible.

### 2.9 Persistence & labels (L35)
- "Skip everything" → **"Skip"** (L35).
- **Only persist choices once they finish** — keep selections as a draft until the
  final step (so a mid-wizard bail leaves nothing half-applied).

---

## 3. Theme step (L28)
Offer **System / Light / Dark** only, mapping explicitly to **system / pesto-light
/ pesto-dark**; the full palette stays a post-onboarding Settings choice.
(Coordinates with the theme/A8 work.)

---

## 4. From the original spec (historical — `docs/00_original_spec/`)
The original spec barely covers onboarding — it only anticipated **"pre-defined
stock groups / locations on first usage"** (Stock Items board). That's the seed
step (§2.5.1), which exists. **The rich wizard, the vision explainer, and the
starter *item* template are all newer feedback** with no original-spec
counterpart — nothing to extract or that it supersedes. (Worth noting: the
starter-template idea L37 goes beyond the original "pre-seed structural defaults"
to pre-seeding actual items — a genuine evolution.)

---

## 5. Open decisions (for co-design)
1. **Which features are toggleable at first-login** (L42) — candidates: deals/
   scraping, meal plans, budget/money, nutrition, voice/sous-chef, assistant.
   Confirm the set (and that the settings feature-flag panel gets built — §6).
2. **Starter-template contents** (L37) — the curated item list + default
   locations. Co-design the list; how many items; categories covered.
3. **Demo-data scope** (L38) — what a demo recipe / meal / plan contains, and how
   it's flagged for easy removal.
4. **How much vision content** (L41/L43) — depth of the diagrams vs keeping
   onboarding short (P1). Where's the line before it's a slog?
5. **Headcount granularity** (L44) — a single number, or adults/children (affects
   cook-mode scaling)?

---

## 6. Ripple & dependencies
- **Seed system** must extend beyond groups/locations to **starter items + demo
  recipe/meal/plan** (new seed payloads + idempotent dedupe like today's).
- **Settings feature-flags** (L42) — needs a matching admin panel; **settings is a
  deferred surface**, so flag it as a dependency, don't build it here.
- **Cook mode (C-3)** reads the household headcount default (§2.4).
- **Theme / A8** — the system/pesto mapping (§3).
- **Auth-shell (C19)** — shared styling (§2.1).
- **B5** already fixed the dead nav (§1) — confirm in browser.

---

## 7. Suggested sequencing
1. **Copy/label fixes** (§2.6, §2.9, L29, L30) + theme mapping (§3) — trivial, no
   new systems.
2. **Vision + stock-vs-product explainer** (§2.1, §2.2) — content/UI only.
3. **Household + stores capture** (§2.4) — small; unlocks cook-mode scaling.
4. **Starter template + demo-data toggles** (§2.5) — the big rock; needs seed-
   system work. Highest value.
5. **Finish celebration + workflow explainer** (§2.8).
6. **Admin feature toggles** (§2.3) — gated on the settings feature-flag panel.

---

## 8. Feedback coverage

Maps ONBOARDING (L24-46).

| Bullet (line) | Summary | Where |
|---|---|---|
| L24 | Same styling as login screen | §2.1 (auth-shell / C19) |
| L25 | Skip-everything does nothing | §1 → **B5** (fixed; confirm) |
| L26 | Finish does nothing | §1 → **B5** (fixed; confirm) |
| L27 | "Show me X" cards non-functional | §1 → **B5** (fixed; confirm) |
| L28 | Theme = system/light/dark → system/pesto-light/pesto-dark | §3 |
| L29 | Admin wording "Invite other users later" | §2.3 |
| L30 | Grocy named + import navigates away | §2.5.4 (inline, unnamed) |
| L32, L33 | "You already have groups/locations" copy on first-run | §2.6 (+ FU-041 confirm) |
| L34 | Seed page pick all/none/some | §2.5.1 |
| L35 | "Skip everything" → "Skip"; persist on finish only | §2.9 |
| L36 | Show slim "added" list; move counter into it | §2.7 |
| L37 | Pre-done starter template, tick on/off | §2.5.2 |
| L38 | Demo recipe/meal/plan toggles (warn demo data) | §2.5.3 |
| L39 | Confetti celebration on finish | §2.8 |
| L40 | Tour should cover more key areas | §2.8 |
| L41 | Explain core values / vision / how to best use | §2.1 |
| L42 | Admin first-login feature enable/disable (+ settings) | §2.3 (+ open 1; settings dep) |
| L43 | Explain core workflows / power-user, diagrams, link to guides | §2.8 |
| L44 | "How many do you cook for?" → cook-mode adjust | §2.4 (C-3) |
| L45 | "Which stores do you prefer?" | §2.4 |
| L46 | Stock-item-vs-product explainer BEFORE add-items | §2.2 |
