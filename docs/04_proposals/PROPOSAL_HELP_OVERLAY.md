# C-help — Opt-in contextual help overlay → `PROPOSAL_HELP_OVERLAY.md`

**Type:** 🔵 design brief — produces this proposal, changes **NO code.**

**Origin.** User-floated (2026-06-06): *"add an info button that can be clicked at
any time on a page to show/hide info panels that pop up around all the UI elements
explaining what a user can do. Sort of like a better version of an interactive
tutorial. Interactive first-time tutorials always get in the way — this is
opt-in."*

**The core insight.** This is the **opt-in inverse of a first-run tour.** C-5
(onboarding) deliberately *ditched* the intrusive "nav to features" tour because
forced tutorials get in the way (feedback L43). The gap that leaves: a user who
later wonders "what does this button do?" has nowhere in-context to look — they'd
have to leave for the Help page. A **persistent "?" toggle that overlays
explanatory bubbles on the current page's controls, on demand, dismissible**, fills
that gap without ever taxing the default experience. It's the same philosophy as
C-cross's opt-ins: off by default, *gone* not greyed, never forced.

**Charter check.** Effortless + Anti-creep. The mechanism is cheap and adds zero
friction to the core flow (one icon in the toolbar, dark until pressed). The real
cost is **content** — a hint per UI element, kept from rotting — so the design
prioritises a low-maintenance content model over a clever overlay engine.

---

## 1. Current state (grounded in code)

Dora already has a **help *section***, distinct from what's proposed:
- `HelpPage.vue` — "Guides by area, what's new (changelog), a fun fact"; links to
  `DoraHelpPage.vue` (the DoraBot assistant) and to GitHub issues.
- `helpApiService.ts` — version/changelog/food-fact endpoints.
- The **Dora assistant** (`DoraChat.vue`, `ask_assistant.py`) answers free-form
  questions including app-help/navigation.

So three help modalities exist: **(1) the Help page** (deep, leave-the-page docs),
**(2) the assistant** (ask a question, get an answer). What's **missing is (3)
in-context, glanceable "what does *this* do" hints overlaid on the live page** —
the thing the user is asking for. It complements, not replaces, (1) and (2): the
overlay points to the page; the Help page explains in depth; the assistant answers
specifics. (Feedback L43 explicitly wants onboarding to "point users to the
guides/help section" — the overlay is the natural in-context bridge to it.)

There is **no existing tour/coachmark/tooltip-overlay system** to extend — this is
a net-new cross-cutting component (Wave-A-flavoured).

---

## 2. The design

### 2.1 The mechanism — a page-level "help mode" toggle

- A **"?" toggle in the app toolbar**, present on every page, dark/off by default.
- Pressing it enters **help mode**: the page dims slightly and **info bubbles
  appear anchored to registered UI elements**, each a short "what you can do here."
  Press again (or Esc, or tap a bubble's close) to exit. **Fully dismissible, never
  auto-opens.**
- **Per-page, not a linear walkthrough.** Unlike a tour, there's no "next → next →
  finish" rail trapping the user; all hints for the current page show at once (or
  on hover/tap of a highlighted element — §4-1), and the user reads whatever they
  want in any order, then leaves. This is the "better than an interactive tutorial"
  the user wants.
- **State:** help-mode on/off is **ephemeral view state** (not persisted) — it
  resets per session/page. Optionally remember "user has used help mode" only to
  stop nudging (none proposed). No server state needed for the mechanism itself.

### 2.2 The content model — the part that actually matters (§4-2)

The overlay engine is easy; **keeping a hint per element accurate as the UI evolves
is the hard part.** Two models:

| Model | How hints are authored | Pros | Cons |
|---|---|---|---|
| **A. Co-located registrations** | Each component declares its own hint inline (a directive/prop, e.g. `v-help="'...'"` on the element) | Hint lives next to the control → least rot; new control without a hint is locally obvious | Content scattered; no single review surface; harder to translate |
| **B. Central hint catalogue** | A keyed catalogue (`page → element → text`); elements reference a key | One place to review/edit/translate all copy; content people can edit without touching components | Drifts from the UI (delete a control, the orphaned key lingers); indirection |

**Recommend A (co-located `v-help` directive) as the spine**, because hint-rot is
the dominant failure mode and co-location fights it best; **with a build/dev-time
check** that flags registered hints whose target no longer renders and (optionally)
interactive elements with no hint. If translation (C-locale Layer C) is ever
greenlit, the directive can resolve through `$t()` keys — so A doesn't foreclose B's
benefit.

### 2.3 Authoring scope — start where it pays

Hints are **content, written per surface**, so this brief defines the *system* and a
*rollout order*, not 200 hint strings up front:
- **Seed the high-traffic / high-confusion surfaces first** — exactly the ones with
  the heaviest feedback clusters: stock overview (the stock-level button, the cart
  button, expiry), the meal-plan builder (the calendar widget, allocation), cook
  mode, the cookbook card. These are where "what does this do?" is most asked.
- **Each Wave-C surface adds its own hints as it's implemented** — fold "register
  help hints for the new controls" into each per-surface implementation prompt, so
  content lands with the feature instead of as a doomed retro-documentation pass.
- A surface with **no hints simply shows nothing in help mode** — graceful, not
  broken.

### 2.4 Relationship to the other help modalities
- **Overlay (this) → in-context "what is this".** Bubbles can deep-link to the Help
  page section or open the assistant pre-seeded with "tell me about X" for depth.
- **Help page → guides/changelog/fun-fact** (exists). The overlay's "learn more"
  targets it (closes the L43 loop).
- **Assistant → ask anything** (exists). The overlay is the *visual* counterpart to
  the assistant's *conversational* help; they should feel like one help system, not
  three (note for the deferred settings/help-shell work).

### 2.5 The DoraBot tie-in (optional, charm)
The original spec wanted *"basic tips and tricks from Dora based on the page I'm
on"* and a non-obtrusive mascot. Help mode is a natural home: the mascot can
present the hints ("Here's what you can do on this page!") so the overlay has
personality and reuses `DoraMascot`. Keep it optional — the mechanism must work
plainly without the character (Anti-creep).

### 2.6 Explicitly out of scope
- **A forced first-run tour** — the opposite of this brief; C-5 already removed it.
- **Writing the full hint corpus** here — that's per-surface content, rolled out
  per §2.3.
- **Re-architecting the Help page or unifying the three modalities into one shell**
  — that's deferred settings/help-surface work; this brief only ensures the overlay
  *links* into the existing Help page and assistant.

---

## 3. Data-model summary

Essentially **none server-side** — the mechanism is client view-state. The only
possible additions:
- Hint content lives in code (co-located directive, §2.2-A) — not the DB.
- *Optional:* a per-user "don't show the help-mode discoverability nudge again"
  flag — only if a nudge is added (none proposed). Default: no new columns.

This is deliberately a **front-end cross-cutting component**, not a data feature.

---

## 4. Open decisions (for co-design)

1. **Reveal style (§2.1)** — show *all* page hints at once on toggle (denser,
   scan-everything), or highlight elements and reveal each hint on hover/tap
   (cleaner, more interaction)? Recommend hover/tap-to-reveal with a subtle marker
   on each hinted element, so a busy page doesn't explode into bubbles.
2. **Content model (§2.2)** — co-located `v-help` directive (recommended) vs central
   catalogue?
3. **DoraBot presentation (§2.5)** — mascot-fronted hints or plain bubbles
   (recommend plain-with-optional-mascot)?
4. **Discoverability** — how does a user learn help mode exists? Options: a one-time
   subtle pulse on the "?" icon, a mention on the onboarding finish card (C-5), or
   nothing (rely on the universal "?" affordance). Recommend the C-5 finish-card
   mention — it's where C-5 already points users to help.

---

## 5. Ripple & dependencies

- **C-5 (onboarding)** — the overlay is the opt-in counterpart to the tour C-5
  removed; C-5's finish card should mention it (§4-4). Strong pairing.
- **Every per-surface brief (C-1..C-9)** — each gains a "register help hints for new
  controls" step at implementation time (§2.3); this brief defines the directive
  they use.
- **Existing Help page + assistant** — the overlay links into both (§2.4); no change
  to their internals.
- **C-locale** — if full translation (Layer C) is ever done, hints resolve via
  `$t()` keys; the directive design should keep that path open (§2.2).
- **A1 theme** — bubbles/dim-layer must use theme tokens (no hardcoded colours),
  per the Wave-A standard.
- **Deferred help/settings shell** — unifying the three help modalities is later
  work; noted, not built.

---

## 6. From the original spec (historical — `docs/00_original_spec/`)

Non-authoritative. From the **Help, Guides & Assistant** board:

| Original note | Verdict | Effect |
|---|---|---|
| *"I get basic tips and tricks from Dora based on the page I'm on"* | **keep — grounds §2.1/§2.5** | Direct precedent for *per-page, in-context* help; the overlay is the concrete realisation, made opt-in. |
| *"The Dora assistant pops up onto the screen in a non-obtrusive way"* | **keep → §2.5** | Reinforces non-obtrusive/opt-in; the mascot can front help mode. |
| *"I can open a help section to see guides and instructions"* | **already built** | `HelpPage.vue`; the overlay *links* to it (§2.4), doesn't replace it. |
| *"The Dora assistant acts as a help/guide section"* | **partially built → §2.4** | The assistant exists; the overlay is the missing *visual* third modality alongside it. |

The board confirms in-context, page-aware help was always intended — this brief
makes it opt-in and decoupled from the (now-removed) forced tour.

---

## 7. Feedback coverage

User-originated in conversation, so per the CLAUDE.md cross-cutting rule there's no
feedback cluster to exhaustively map; related bullets for traceability:

| Source | Summary | Where |
|---|---|---|
| User idea (2026-06-06) | Opt-in info overlay, not a forced tutorial | §2 (whole) |
| L43 | Onboarding should point to guides/help, not force a tour | §2.4 (overlay bridges to Help), §4-4 |
| L191 | "Noted in instructions/guides that features are standalone — use as much as you want" | §2.3 (hints can convey this in-context) |
| L444-449 (HELP) | Detailed, easily-navigable help for every part | §2.4 (overlay complements the deep Help page; doesn't replace the "detailed guides" ask) |
| C-5 design | First-run tour removed as intrusive | §2.6 (this is its opt-in inverse) |

This brief *complements* the L444-449 "detailed help" ask (that's the Help page's
job) rather than closing it; it closes the in-context gap none of the existing
modalities cover.

---

## 8. Suggested sequencing

1. **The overlay mechanism + `v-help` directive + dev-time orphan check (§2.1,
   §2.2)** — the reusable system, themed, with the "?" toggle. No content yet.
2. **Seed hints on the highest-confusion surfaces (§2.3)** — stock overview,
   meal-plan builder, cook mode, cookbook card.
3. **Wire the C-5 finish-card mention + bubble "learn more" deep-links (§2.4,
   §4-4).**
4. **Per-surface hint rollout** folded into each C-1..C-9 implementation prompt as
   it lands.

No code until approved — this is a brief.
