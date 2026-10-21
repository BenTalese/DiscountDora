# Proposal — Onboarding Redesign (C-5)

**Status:** Co-designed draft v3 (supersedes 2026-06-06 and the 2026-06-15 v2) · **Date:**
2026-06-15 · Changes NO code.
**Scope:** Reframe first-run from "a wizard that collects data" into a **cinematic, frictionless
on-ramp that sells the app** — hooks the user on the core premise (Dora turns the chaotic weekly
shop into one loop that mostly runs itself), shows how the features interlock, never overwhelms,
and lets them skip / jump / see-progress at will with keynote-grade motion. A **persona fork**
(Cooking / Spend-tracking / Everything) sets the install flags — including a new
`products_enabled` flag — and **branches** the wizard. Then the fastest path to value (category
**starter-packs + opt-in demo data**), **household headcount**, and a celebratory finish that
recaps the loop and points into the help guides. **Preferred-stores dropped** (→ FU-180).

> **⚠️ UPDATE (2026-06-17) — personas removed; see `PROPOSAL_PRODUCTS_AS_OVERLAY.md` §5.** The
> **persona fork (Cooking / Spend-tracking / Everything) and the `products_enabled` flag it set
> are CUT.** Onboarding becomes **one standard "show everything" path, un-personalized**: no
> fork, no product framing, and the **stock-item-vs-product explainer is retired** (the everyday
> user never meets "products"). **Keep** the structural pieces — cinematic intro, hero loop,
> starter packs, household headcount, finish celebration — but **remove persona previews /
> persona-relevant tailoring** (C-5.2 preview, C-5.6 flow-card tailoring) and show the full loop /
> full card set. **Money/budgeting is a Settings toggle only** — onboarding shows the feature
> exists, it does not fork or force a choice. The rest of this doc stands; treat the persona /
> products / explainer sections as superseded.

> **Charter tie-break:** Effortless (P1) + Honest (P3) + Anti-creep (P10). The whole point is to
> get the user to *value* and *belief* fast — Effortless. But **P3 Honest is load-bearing here**:
> we sell only what the app actually does. Auto deal-scraping is **divorced from the core app**
> (companion-only, per the master plan's removed-features), so the sell is the durable, legal
> story — a self-running smart pantry — not a deals engine.

> **Co-design note (2026-06-15, v3):** Direction set across four question rounds + two
> interactive hero prototypes the user played with. Decisions: **cinematic intro → setup with
> instant jump + a shared progress map** (free, non-linear navigation, nothing gated); **3–4
> punchy scenes, big visuals, minimal words**; the **hero "how it connects" visual = hybrid**
> (auto-reveals once, then every stage — and Dora — is tappable to drill in), **no persona-
> dimming in the hero** (it sells the full power); the **core loop dropped "Deals"** (scraping
> divorced) in favour of a self-running pantry with **Dora as the brain in the centre**;
> personas reframe to **Cooking / Spend-tracking / Everything**. **The loop's exact stages +
> all sell-copy are PROVISIONAL and must be reconciled against the running app before copy
> ships (§6, FU-184)** — an emerging price-insight stage in particular isn't finished.

---

## 1. Current state (from live code, 2026-06-15)

`WelcomeWizard.vue` — 5 linear steps (Welcome name/theme/font → Admin → Seed groups/locations →
First item → 4-card Tour). Backend `onboarding.py` seeds only groups + locations.

**Already done (verify-state-first — old §1 is partly stale):** B5 dead-nav fixed; theme
system/light/dark; admin says "Invite teammates later"; inline "(N added)" counter; draft to
localStorage. **The feature-flag settings panel EXISTS** (`SystemSettings.vue` + `AppSetting`
flags + admin PATCH) — the old "deferred panel" is obsolete; the persona is a thin writer over
it. **Help/guides exist** (`HelpPage.vue`). **Meal slots seeded by migration.**

**Missing (this redesign delivers):** no vision/sell, no story, no motion; no persona fork; no
`products_enabled`; no `household_headcount` (cook-mode TODO waits on it); no starter-item packs
/ demo data; no celebration; bare 4-card tour; "Skip everything" not "Skip"; prefs persist
incrementally (not draft-until-finish); Grocy named + import navigates away.

---

## 2. The experience (the heart of this redesign)

### 2.1 Principles
1. **Frictionless** — the user can jump from the story to setup (and back) **instantly**, sees
   exactly how far along they are, and nothing is gated. Skipping is always one tap.
2. **Sell, don't slog** — really hook them on the premise; big visuals, almost no text. Short
   enough that the *story* never feels like a chore (P1).
3. **Never overwhelm** — progressive reveal; one idea per scene; depth is opt-in (tap to drill,
   or the help guides), never front-loaded.
4. **Show how it connects** — the payoff is the user *getting* that the features form one loop,
   with Dora as the intelligence tying it together.
5. **Honest** — every claim maps to real behaviour (§6).

### 2.2 The narrative / sell arc (3–4 cinematic scenes)
Full-screen, auto-advancing-but-skippable scenes, each one idea, big type + a hero visual:
1. **The problem** — the weekly shop is detective work: what's run out, what's already in the
   back of the cupboard, what to cook, what it costs. (Big, empathetic, ~6 words.)
2. **The loop** — *this* is the hero (§2.3): Dora turns it into one self-running loop.
3. **Dora is the brain** — the assistant + alerts + price memory watching over it, doing the
   remembering so you don't.
4. **You're in control** — as quiet or as powerful as you want (sets up the persona fork).

Then: **"Set up in about a minute →"** drops into setup. A persistent **"Skip to setup"** is
present from scene 1.

### 2.3 The hero loop visual (PROVISIONAL — see §6)
The centrepiece of "how it all connects." A ring of stages with **Dora at the centre as the
brain**. **Interaction = hybrid** (decided from the prototypes): it **auto-plays the reveal
once** (each stage lights and hands off to the next), then **stays on screen and becomes
tappable** — tap any stage, or Dora, to drill into what it does and how it hands off.

**Default state = full power** — the auto-reveal plays the Everything-persona shape (all
stages + Dora-centre + the candidate Insight node) so the first impression sells the
ceiling. **Persona-preview affordance** (amends the earlier "no persona-dim" call —
2026-06-15): a small segmented control sits below the loop with three buttons — *Simple*,
*Mid*, *Full* (working labels — co-design open thread §2.3.a below). Tapping a button
smoothly transitions the loop to that persona's shape: nodes fade/scale in or out, stage
subtitles update, and the Dora-centre copy swaps. Tapping the currently-selected button is
a no-op. The persona buttons **do not restart the auto-reveal** — once the reveal has
played, the loop is in interactive mode.

**What each preview shows:**

| Preview | Loop shape | Stage-subtitle differences | Dora-centre copy |
|---|---|---|---|
| **Simple** (Cooking) | Stock → Plan → List → Shop → Restock → Cook; **no Insight node**. | List/Shop drop the "log what you paid" beat (Money off) or keep it without merchant attribution (Money on, Products off). | *"Watching expiry & stock, suggesting what to cook."* |
| **Mid** (Spend-tracking) | All 6 stages + **Insight node** illuminated. | Shop carries the full "log what you paid — Dora remembers every price" subtitle. | *"…and learning what you pay."* |
| **Full** (Everything) | Mid state + any **peripheral nodes** the Everything persona turns on (e.g. scanning, companion/ingestion, nutrition — whichever survive §6 validation). | Full copy on every stage. | Full copy. |

**Animation principles for the persona transition:**
- Sub-cinematic budget — the persona transition is **lighter than the auto-reveal** (≈250–
  350ms, single eased curve). It's a UI affordance, not a second show; users will tap
  through multiple times and a heavy animation would grate.
- **Transform + opacity only** (GPU-friendly, consistent with §2.4).
- **Reduced-motion path** — under `prefers-reduced-motion`, the transition becomes a
  near-instant cross-fade with no scale/translate. No autoplay loops on either path.
- **Layout stability** — the loop's outer footprint stays constant across personas;
  removed nodes leave their slot collapsed-but-allocated so the ring doesn't reflow and
  jump nearby content. (Implementation detail to confirm in prototyping.)

**Loop draw-in still plays once** (full state) as the cinematic moment; the persona
buttons appear *after* the reveal completes (or immediately if the user has skipped/seen
it before per the draft-until-finish state).

#### 2.3.a Open threads on the persona-preview affordance
- **Button labels** — *Simple / Mid / Full* are working labels. Alternatives to weigh:
  (a) the persona names themselves (*Cooking / Spend-tracking / Everything*) for
  consistency with §3.2; (b) outcome-led labels (*Just cooking / + Spend tracking /
  Everything*); (c) icon-first with a tooltip. Co-design.
- **Default button on first paint** — *Full* by intent (sells the ceiling). Confirm
  this isn't read as "you're being shown the busy option first" by users who'd prefer
  the calmer start. Worst case, the auto-reveal plays Full → the first interactive
  state remains Full → user can downshift.
- **Relationship to the §3.2 persona fork step** — does the persona-preview *replace*
  the discrete fork step (the previewed persona becomes the selection), become a
  *pre-confirmation* ("you previewed Simple — set this as your starting point?"), or
  stay purely illustrative with the fork step unchanged? Recommendation: **pre-
  confirmation** — the hero introduces the concept and lets users preview; the fork
  step is where they commit, pre-filled with whatever they last previewed. Preserves
  the explicit choice moment while removing the blind-commit friction. Confirm.
- **Customise visibility** — *Customise* is an existing fourth persona (§3.2). It
  doesn't fit the loop-preview metaphor (it's "pick your own flags," not a shaped
  loop). Recommendation: keep it off the hero buttons; surface it only at the §3.2
  fork step, labelled e.g. "or customise it yourself." Confirm.
- **Layout-stability collapse** — confirm in prototyping whether removed nodes
  collapse-but-allocate (cleanest, no reflow) or whether the ring should subtly
  re-circle to fewer nodes (more honest to the simpler shape but reflows surrounding
  copy). Trade-off; both defensible.

**Working loop (provisional spine):**

| Stage | The one-line sell (provisional) |
|---|---|
| **Stock** | Everything you keep — levels, locations, expiry — always current, no manual counting |
| **Plan** | See what you can cook from what's in; plan the week; Dora flags the gaps |
| **List** | Low, out, and meal-plan gaps flow onto a shopping list that builds itself |
| **Shop** | Tick off as you go and log what you paid — Dora remembers every price |
| **Restock** | Finish the shop and your pantry refills itself |
| **Cook** | Cook mode walks each step and counts ingredients down |
| **· Dora (centre) ·** | The brain — watching expiry & stock, answering questions, learning what you pay |

**Emerging stage (NOT final — validate + finish first):** an **"Insight" / "Spend smarter"**
beat — link products to stock items, and from your own receipts Dora flags when something's
**costing more than it usually does** (shrinkflation / overpay awareness). This is the honest,
legal replacement for deal-scraping and the spine of the **Spend-tracking** persona. Represent
it as a **candidate 7th node / a facet of Dora-centre**, flagged provisional — do not ship copy
that promises it until the feature is real (§6).

### 2.4 Motion & visual language ("like an Apple keynote")
- **Big** — oversized icons, diagrams and headlines; generous negative space; one focal object
  per scene.
- **Reveal, don't dump** — content arrives via **scale + fade + short translate** with eased
  curves (`cubic-bezier(.2,.8,.2,1)`), staggered; the loop draws itself stage-by-stage; numbers
  count up; the next scene gently displaces the last (no hard cuts).
- **Cinematic surface** — in the **app**, a calm dark canvas with the real **Dora yellow** as
  the single accent (the prototypes are deliberately flat/themed to Claude's canvas; production
  gets the full treatment). Restrained, premium, never busy.
- **Continuity** — the **loop diagram is one reusable component** (`OnboardingLoop`) used in the
  hero scene *and* recapped at finish (§3.6) so the story bookends (R-001).
- **Performance** — transform/opacity only (GPU-friendly); lazy-mount heavy scenes; target 60fps
  on a mid phone; total motion budget kept tight so it feels snappy, not slow.
- **Accessibility (mandatory)** — honour `prefers-reduced-motion`: replace transforms with quick
  cross-fades, no parallax, no autoplay loop (show the final state). Full keyboard nav; visible
  focus; captions/labels on every visual. Motion is polish, never a gate to the content.

### 2.5 Navigation & progress model (frictionless)
- **Two sections, instant cross-jump** — *Story* (intro scenes) and *Setup* (the steps). A
  persistent control jumps **straight to setup** from any scene, and back to the story any time.
- **Free, non-linear map** — a persistent **step rail** (section dots, like an Apple product
  page) shows every section, the current position, and lets the user **jump to any** at will.
  Nothing is gated; setup steps are optional and resumable.
- **Always-visible progress** — the rail doubles as the "how far through" indicator.
- **Draft-until-finish** — selections (prefs, persona, seed picks, headcount) are held as a
  local draft and **applied once on Finish**, so jumping around or bailing leaves nothing
  half-applied (L35). Refresh resumes the draft.

---

## 3. The flow (branched by persona)

### 3.1 Vision / intro (§2.2, §2.3, §2.4) — L41, L43, L24
The cinematic scenes + the hero loop. Auth-shell styling (C19). Display name + theme + font fold
into a light "make it yours" beat (not a blocking form up front).

### 3.2 Persona fork + `products_enabled` flag (L42) — reframed
After the hook, **"What do you want Dora to do for you?"** — **three presets** (+ a "Customise"
card → the flat toggle list):

| Persona | products | money/spend | meal_planning | nutrition | companion / scanning / voice |
|---|---|---|---|---|---|
| **Pantry & cooking** | off | off | on | off | off |
| **Pantry + spend tracking** | on | on | on | off | off |
| **Everything (power user)** | on | on | on | on | on* |

- Reframed from "grocery savings (deals)" → **spend tracking & less waste** (price memory from
  receipts + expiry/cook-what-you-have + buy-only-what-you-need). Honest with no scraping.
- **New `AppSetting.products_enabled`** (default **on**; the Cooking persona turns it off). C-5
  **introduces + sets** it via the existing flag machinery. With scraping divorced, products
  (linked products, price history, ingestion for self-scrapers) is a **minority/power layer** —
  which *strengthens* Cooking as the common default. **Per-surface Products-off gating = FU-182**
  (not C-5). \*config-gated flags degrade gracefully (§7.5).
- Copy: "changeable later in admin settings" (true today — the panel exists).

### 3.3 Conditional stock-item-vs-product explainer (L46)
Shows **only when `products_enabled`** (Spend-tracking / Everything). The Cooking persona
**skips it** — teaching the product concept to someone who opted out is the friction FU-182
flags. Before any add-items step.

**Copy guidance (from FU-182 brainstorm — `99_scratch/MINIMAL_USER_PRODUCTS_OFF_FRICTION.md`
§5).** The explainer must use the milk example concretely — *"'Milk' is a stock item — a
thing you keep. 'Vitasoy Oat Milky 1L @ Coles' is a product — a specific thing you can
buy."* Pair with a direct *don't*: *"Don't name your stock items after brands — that's
what products are for."* The stock-item-vs-product confusion is the dominant UX risk of
the Products-on model; this step is the primary mitigation, with the help-overlay
glossary (`PROPOSAL_HELP_OVERLAY.md` §2.3) as the secondary surface.

### 3.2.a Open thread — Products off + money on combination
The persona table in §3.2 bundles `products` and `money/spend` together (both off in
Cooking, both on in Spend-tracking). FU-182's resolved decisions accept (B) — money is a
**separate question** from products, so the (Products off + money on) combination must
be reachable somewhere: either via the Customise branch (preferred) or by splitting
"Pantry & cooking" into two variants. Confirm before C-5 ships. Not adding a fourth
preset speculatively — Customise is the existing escape hatch.

### 3.4 Household headcount (L44) — single number
**`User.household_headcount`** (new); cook mode's scaler initialises from it (resolves the
`RecipeCookMode.vue:545-547` TODO).

### 3.5 Starter data — fastest path to value (L34, L37, L38, L30, L36)
All drafted until Finish: (1) groups/locations **all/none/some + preview**; (2) **category
starter-packs** of pre-located common items, toggle packs → tick items (new `starter_packs.json`
+ idempotent seed endpoint); (3) **opt-in demo recipe/meal/plan**, warned, **plain rows (no
`is_demo` marking)**; (4) **inline import**, un-named (not "Grocy"); (5) first stock item with a
**slim "added" list** (count folds in).

### 3.6 Finish — celebrate + recap the loop + into help (L39, L40, L43)
**Confetti / "you're all set!"** (L39). Recap with the **same `OnboardingLoop` component**
(bookend), then **flow-cards** for the persona-relevant key areas, each **linking into the
existing `/help` guides** (L43, L40). Fixes **FU-015** (tour Alerts card → `/alerts`).

### 3.7 Copy, theme & persistence fixes
"Skip everything" → **"Skip"** (L35); **draft-until-finish** (L35); theme → **system /
pesto-light / pesto-dark** (L28); **"you already have groups/locations"** confirmed not to show
on a clean first-run DB (**FU-041**).

### 3.8 Preferred stores — DROPPED (L45)
Not built — same uncertain bucket as the preferred-*product* removal (FU-180): merchants are
name-only, scraping is companion-scope and may not ship, and capturing a preference with nowhere
to apply it is premature. Folded into FU-180.

---

## 4. Data model
- **New** `AppSetting.products_enabled` (bool, default True) — persona sets it; gating = FU-182.
- **New** `User.household_headcount` (int, nullable) — cook mode reads it.
- **New seed payloads** `features/onboarding/starter_packs.json` + demo payload(s); idempotent
  endpoints (dedupe by name). **No `is_demo` column. No Merchant change.**
- Migrations: plain, reversible, portable SQLite + Postgres (R-005/R-006, §7.5); single head.

---

## 5. Resolved decisions (co-design 2026-06-15)
- Cinematic **intro → setup, instant cross-jump, shared progress**; **free non-linear** nav,
  nothing gated; **3–4 punchy scenes**, big visuals, minimal words.
- Hero = **hybrid** (auto-reveal once → tappable), **Dora at centre**. **Default state =
  full power** (Everything shape) so the first impression sells the ceiling. *Amended
  2026-06-15:* the original "no persona-dim in the hero" call is superseded by a
  **persona-preview segmented control** (Simple / Mid / Full) under the loop — users can
  smoothly preview how the loop collapses for each persona without leaving the hero
  (§2.3). Default-on-load remains Full so the cinematic reveal still sells the ceiling.
- Core loop **drops Deals** (scraping divorced); **Stock → Plan → List → Shop → Restock → Cook**
  + Dora-centre; an **emerging Spend-smarter/Insight stage** flagged provisional.
- Personas: **Cooking / Spend-tracking / Everything** (+ Customise).
- `products_enabled` introduced in C-5; **gating = FU-182**.
- Starter **packs + opt-in demo** (demo rows plain). Headcount = **single number**. Preferred
  stores **dropped**.
- **Motion honours `prefers-reduced-motion`**; reuse one `OnboardingLoop` component.

---

## 6. Provisional — reconcile the sell against actual app behaviour (MANDATORY gate)
The loop's exact stages, the emerging Insight beat, and **every sell-line are provisional**.
Before any onboarding copy ships:
- **Walk the running app** and confirm each stage's claim is literally true (e.g. does finishing
  a shop really auto-restock? does cook mode decrement? does price memory + an "inflated price"
  signal actually exist, or is it aspirational?). **Cut or soften any claim the app doesn't back
  (P3 Honest).**
- **The emerging Insight/Spend-smarter stage** is not a finished feature — do **not** promise it
  in copy until it's real; until then it's a design placeholder, not a shipped beat.
- This can't be done from a static read — it needs the running app. Tracked as **FU-184**; it is
  a **close-gate on the onboarding-copy chunk** (C-5.1/C-5.2/C-5.6), not optional polish.

---

## 7. Ripple & dependencies
- **C-cross (done):** writes existing flags + new `products_enabled`; reuses `useFeatureFlags`.
- **FU-182:** C-5 ships the persona + flag; **FU-182 consumes it** for the per-surface sweep.
- **Cook mode (C-3, done):** reads `household_headcount`.
- **Help (exists):** finish-step deep-links into guides.
- **FU-180:** absorbs preferred-stores; relates to the products/price-memory uncertainty.
- **Master plan removed-features:** confirms hosted scraping is companion-only — the sell aligns.
- **Theme/A8** (pesto mapping); **Auth-shell/C19** (vision styling); **B5/FU-015/FU-041**.
- **FU-184 (new):** validate the sell against real behaviour before copy ships.

---

## 8. From the original spec (historical)
Only "pre-defined groups/locations on first usage" (Stock Items board) — the seed step. The
cinematic sell, persona fork, hero loop, and starter-packs are all newer; nothing to extract or
that it supersedes.

---

## 9. Suggested sequencing (→ IMPL_PLAN_ONBOARDING)
1. Copy/label/persistence + theme (§3.7) — quick wins.
2. **Cinematic intro + `OnboardingLoop` hero + motion/nav/progress shell** (§2, §3.1) — the
   experience spine. **Gated by FU-184 copy validation.**
3. Persona fork + `products_enabled` + branching + conditional explainer (§3.2, §3.3).
4. Household headcount (§3.4).
5. Starter data: packs + demo + preview + import + added-list (§3.5).
6. Finish: celebration + loop recap + help flow-cards (§3.6).

---

## 10. Feedback coverage

Maps ONBOARDING (L24-46).

| Bullet (line) | Summary | Where |
|---|---|---|
| L24 | Same styling as login screen | §3.1 (auth-shell / C19) |
| L25–L27 | Skip / Finish / "Show me X" do nothing | §1 → B5 (fixed; confirm) + §3.6 rebuild |
| L28 | Theme system/light/dark → system/pesto | §3.7 |
| L29 | Admin wording "Invite other users later" | §1 (✅ done) |
| L30 | Grocy named + import navigates away | §3.5 (inline, unnamed) |
| L32, L33 | "You already have groups/locations" on first-run | §3.7 (+ FU-041) |
| L34 | Seed page pick all/none/some + preview | §3.5 |
| L35 | "Skip everything" → "Skip"; persist on finish only | §3.7, §2.5 |
| L36 | Slim "added" list; counter folds in | §3.5 |
| L37 | Pre-done starter template, tick on/off | §3.5 (category packs) |
| L38 | Demo recipe/meal/plan toggles (warn) | §3.5 (plain rows) |
| L39 | Confetti celebration on finish | §3.6 |
| L40 | Tour should cover more key areas | §3.6 (persona-relevant flow cards) |
| L41 | Explain core values / vision / how to use | §2.2 (cinematic sell) |
| L42 | Admin first-login feature enable/disable | §3.2 (persona fork; panel exists) |
| L43 | Core workflows / power-user, diagrams, link to guides | §2.3, §3.6 |
| L44 | "How many do you cook for?" → cook-mode | §3.4 (`household_headcount`) |
| L45 | "Which stores do you prefer?" | §3.8 **Out of scope** → FU-180 |
| L46 | Stock-item-vs-product explainer before add-items | §3.3 (conditional) |

After acceptance + the FU-184 validation, flip the covered ONBOARDING rows in
`docs/02_feedback/COVERAGE_GAPS.md` gap → covered (L45 stays out-of-scope w/ reason).
