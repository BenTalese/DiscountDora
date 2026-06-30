# Dora Assistant Architecture Proposal

**Status:** Draft for discussion
**Date:** 2026-06-04
**Scope:** Untangle the three overlapping "what should Dora do?" systems into one coherent model, and resolve the capability cliff between AI and Basic modes. Companion to `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` (the duplication here is a special case of that thesis).

---

## 1. Why

Dora decides what to do via **three independent systems** that overlap and disagree:

1. **Server-side LLM tools** — `tools.py` (25+ data tools, 8 action tools) driven by Ollama function-calling in `ask_assistant.py`. The capable path.
2. **Client-side rule engine** — `doraIntents.ts` (~19 hardcoded intents). The "Basic mode" fallback when no LLM is configured.
3. **Client-side contextual chips** — `doraContextualActions.ts` (~7 page-aware quick actions) that route through local composables and **never touch the LLM at all**.

The consequences:

- **The same request takes different paths with different outcomes.** "Add milk to my list" via the LLM runs the `add_to_shopping_list` proposal+disambiguation flow; the Basic-mode intent for the same phrasing just reports list *status* and adds nothing. The contextual "Add to list" chip on a stock page calls a composable directly with **no confirmation** — a third behavior for one intent.
- **A capability cliff.** Basic mode reimplements a fraction of the tools (no conversions, no expiry-rescue, no price stats). Whether Dora can do a thing depends on whether an LLM is wired up — invisibly to the user.
- **Duplicated derived logic.** `DoraChat.vue` recomputes "missing ingredients" client-side — the same Type-A duplication catalogued in the state-ownership proposal, now a *fourth* copy living in the chat.
- **Two confirmation UIs.** The multi-item add-to-list card and the generic Confirm/Cancel card are separate patterns for semantically identical "approve this mutation" moments.

The mutation gate itself is good (`ask_assistant.py:187-190` — actions propose, never auto-execute; keep this). The problem is everything *around* deciding what to propose.

---

## 2. The model: one capability registry, two renderers

The core idea: **there is one list of things Dora can do, defined once on the server. How a request is *routed* to that list can vary; what Dora *can do* cannot.**

```
                 ┌─────────────────────────────┐
   user input →  │  Router (LLM  OR  rules)     │  ← the ONLY thing that differs
                 └─────────────┬───────────────┘     between AI and Basic mode
                               ▼
                 ┌─────────────────────────────┐
                 │  Capability Registry         │  ← ONE definition, server-owned
                 │  (data tools + action tools) │     name, args schema, scope, gate
                 └─────────────┬───────────────┘
                               ▼
                 ┌─────────────────────────────┐
                 │  Execution                   │  data → run; action → propose
                 │  (gate enforced here)        │     then user-confirm
                 └─────────────────────────────┘
```

### 2.1 One capability registry (server)
`tools.py` already *is* this — the fix is to make it the **single** source, and let the other two systems consume it rather than reimplement it.

- Each capability declares: name, arg schema, whether it's data or action (the gate), and (post-multi-user) its scope.
- Contextual chips and Basic-mode intents become **routing shortcuts that resolve to a registry capability**, not parallel implementations.

### 2.2 Two routers, one capability set
The only legitimate difference between AI and Basic mode is **how user text maps to a capability**:

- **AI router:** the LLM function-calls the capability (today's path).
- **Rules router:** a keyword/intent matcher maps phrasing to the *same* capability and extracts args.

Crucially, the **rules router calls the same server capabilities** the LLM does. Basic mode stops being a separate, impoverished feature set — it's a dumber *router* over the *same* abilities. "What's the cliff?" disappears: Basic mode can do everything AI mode can *that it can successfully parse*; it just parses less cleverly. A capability is never silently unavailable.

### 2.2.1 Rules-router mechanism — tokenise → slot-extract → filter

> **Status:** the FU-150 *minimal* fix already shipped (2026-06-12) —
> broadened the `find_recipe` trigger list to catch bare-noun cases
> ("i need a recipe", "any breakfast ideas", "show me a vegetarian
> recipe") and rewrote the handler to **stop yanking "the noun after
> a preposition"** in favour of tokenising the whole message (minus
> stopwords) and substring-matching each token against `name +
> cuisine + category + timeOfDay + dietaryTagNames`. Vocab arrives
> via the extended `RecipeSnapshot` (`dietaryTagNames`, `timeOfDay`)
> hydrated in `DoraChat.vue` from the existing Pinia stores. Net
> effect: "i need a vegetarian recipe" routes to `find_recipe` +
> filters by the 'vegetarian' tag; "asian breakfast recipe" requires
> both 'asian' (cuisine) + 'breakfast' (timeOfDay) to hit. Reply
> echoes the matched tokens via `queryDisplay`.
>
> What lands here in §2.2.1 is the **structural redesign** that
> replaces that minimal fix once the registry from §2.1 + the
> sequencing from §5 are in place. Keyword-list + token-substring
> with a hand-coded stopword list doesn't scale — synonyms ("veggie"
> → "vegetarian") aren't resolved, two-word tags + free-text in the
> same message can produce surprising AND-filters, and the first-
> match-wins matcher prefers whichever intent's keyword appears
> first in the trigger list. The redesign below replaces that with
> a four-layer pipeline so the rules router is a maintainable
> equal-citizen alongside the LLM router, not a perpetually-leaky
> keyword bag.

The rules router runs the user's message through four layers, in
order. Each layer is the consumer of the previous layer's output —
no layer reaches back upstream.

**Layer 1 — Vocab-derived triggers.** At chat init, load the Cuisine,
DietaryTag, Category, MealSlot, and Tool catalogues (all already
available via existing Pinia stores). Each catalogue name contributes
a `term → intent-prior` entry into a single trigger map. The matcher
now knows out of the box that "vegetarian"/"asian"/"slow cooker"/
"breakfast" all route to `find_recipe`, *because the user added
them as their own household vocab*. New vocab the user creates
becomes a new trigger the next session over with no developer
involvement.

**Layer 2 — Slot extraction, separate from intent detection.** After
the intent fires, walk the message once and capture slots
declaratively:

```ts
type ChatSlots = {
    cuisines: string[];      // Cuisine ids matched
    dietaryTags: string[];   // DietaryTag ids matched
    categories: string[];    // Category ids matched
    timeOfDay: string | null;
    tools: string[];
    stockItems: string[];    // by stock_item_id
    freeText: string;        // residue — non-vocab tokens
};
```

Slot extraction uses the *same* vocab map as Layer 1 (one source of
truth — feedback term-by-term is wasteful), augmented with a small
synonym table (`veggie → vegetarian`, `gf → gluten-free`, `crockpot
→ slow cooker`). Synonyms live on the server alongside the
catalogues so a household admin could in principle curate them
(out of scope for the initial drop; build the column).

Handlers consume slots **declaratively**: `filterRecipes({
dietary: ['vegetarian'], cuisine: 'asian' })`. No more ad-hoc
substring searches inside the handler, no more "did this token
come from a preposition?" parsing.

**Layer 3 — Intent scoring (optional, post-shipment).** First-match-
wins is brittle: "i'm hungry, what veggie thing can I make?" trips
`find_recipe` because "recipe" appears in its trigger list, even
though the message *means* "what's for dinner?". Replace with a
score per intent — each intent contributes:

- keyword hits (current heuristic);
- vocab hits (cuisine/dietary/timeOfDay/etc.);
- structural cues (does the message end in a question mark, does it
  contain `?`-words like "what/which/should", does it contain an
  action verb like "add/remove/plan"?).

Highest-score intent wins; tie → the lower-confidence fallback that
explains the ambiguity. Worth deferring until the data tools and
slot extractor are in place so the scoring layer has something
useful to score over.

**Layer 4 — Reply transparency.** Already half-shipped in the FU-150
minimal fix (`queryDisplay`). After the redesign: show the user the
*slots the handler applied*, not just the raw token list —
"Filtering by: vegetarian + asian breakfast" reads cleaner than
"Matched tokens: vegetarian, asian, breakfast" and gives the user
a way to spot misclassification ("I said *no* asian"). When the
extractor *thinks* a token meant a slot but the intent didn't
consume it, surface the residue in the same line ("Ignored: spicy
— I don't have a 'spicy' filter") so the user learns the vocab
shape.

**Where this lives in the codebase:**

- The vocab-trigger build runs alongside `ensureRecipeData()` in
  `DoraChat.vue`, sharing the same Pinia hydration the FU-150 fix
  already does.
- The extractor + scorer live in `web_app/src/composables/
  useChatRouter.ts` (new) — a single composable so the LLM router
  can also call into the slot extractor for "the LLM said
  `find_recipe(text='vegetarian asian dinner')`, resolve the
  slots" cases. Two routers, one extractor.
- The handler-side `filterRecipes({...})` is the **same shape** as a
  capability call — slots in, capability args out — so this layer
  drops cleanly into the §2.1 registry once the registry is
  formalised.

**What this fixes that FU-150's minimal patch left open:**

- Synonyms / aliases (`veggie`, `gf`, `crockpot`).
- Two-word vocab + free-text co-existing in one message.
- First-match-wins ordering bias on the intent table.
- "Filtered by" reply line that maps to *slots*, not raw tokens.

**Why this is paired with the LLM-mode work.** Slot extraction is
the same code path whether the route resolves to a rule-engine
handler or the LLM handler — when the LLM says
`find_recipe(text='vegetarian asian')`, the server still wants
those resolved to `{ dietaryTags: ['vegetarian-id'], cuisines:
['asian-id'] }` before hitting the recipe filter. Building the
extractor once, shared between routers, is cheaper than building
it twice and is the natural moment to do the structural work.

### 2.3 Contextual chips become pre-filled capability calls
`doraContextualActions.ts` chips ("Add to list", "Find substitutes" on a stock page) stop being a third execution path. A chip becomes **a capability invocation with args pre-filled from page context** — routed through the *same* execution + gate as everything else. The "Add to list" chip then gets the same confirmation as the LLM's add-to-list, killing the no-confirmation third behavior.

### 2.4 One confirmation renderer
Collapse the two confirmation cards into one component driven by the capability's declared shape: a generic "approve this action" card that renders disambiguation chips *when the proposal needs input* and a plain Confirm/Cancel *when it doesn't*. The add-to-list flow is just the disambiguation case of the general pattern, not a bespoke UI.

### 2.5 Derived logic comes from the server
The client-side "missing ingredients" recompute in `DoraChat.vue` is deleted — it consumes the server's `missing_count` / `cookable` fields from the state-ownership refactor. The assistant displays server truth instead of re-deriving it.

---

## 3. What this fixes

| Problem today | After |
|---|---|
| 3 systems decide what Dora does | 1 capability registry; routers only differ in *parsing* |
| Same request → different outcomes | Same request → same capability → same outcome |
| Basic mode missing ~70% of abilities | Basic mode = dumber router over the *full* ability set |
| Contextual chip skips confirmation | Chip routes through the same gate + confirmation |
| Two confirmation UIs | One confirmation renderer, parameterized |
| 4th copy of "missing ingredients" | Reads server-derived fields |

---

## 4. Trade-offs & risks

- **The rules router is the real work.** Making Basic mode call real capabilities (with arg extraction) is harder than today's canned responses. Mitigation: it doesn't need to parse *everything* — unparsed input falls back to "I can do X, Y, Z; try one of these," which is still better than silently lacking the ability.
- **Keep the gate exactly as-is.** The propose-then-confirm flow (`ask_assistant.py:187-190`) is the one thing that's correct — this refactor must route *through* it, not around it. The contextual-chip change specifically *adds* the gate where it's currently missing.
- **Don't expand capabilities during the refactor.** Missing tools (delete-list-line, unplan-meal, archive-recipe) are real gaps but are a *separate* workstream — adding them mid-restructure muddies the diff.
- **Streaming is out of scope but noted.** `stream: False` (`ollama_client.py`) means users wait for the full reply with no progress. Worth doing later; orthogonal to this restructure.

---

## 5. Sequencing

1. **Formalize the registry** — make `tools.py` capabilities self-describing (data/action, arg schema) as the single contract.
2. **One confirmation renderer** — merge the two cards; drive from the capability shape.
3. **Chips → capability calls** — route `doraContextualActions.ts` through execution + gate; delete the direct composable path.
4. **Rules router over real capabilities** — rebuild Basic mode as a parser that resolves to registry capabilities; retire the canned `doraIntents.ts` responses. **The mechanism is specified in §2.2.1 (tokenise → slot-extract → filter, four layers).** Step 1 of that mechanism — vocab-derived triggers + whole-message tokenisation for `find_recipe` — already shipped on 2026-06-12 as the FU-150 minimal fix. The §2.2.1 redesign replaces that minimal version with the layered pipeline, sharing the slot extractor with the LLM router.
5. **Delete client-derived logic** — remove the `DoraChat.vue` missing-ingredients recompute; consume server fields.

---

## 6. Open questions

- Should Basic mode (no-LLM) even remain a first-class mode, or degrade to "search + canned suggestions + direct chips" and stop pretending to be conversational? If most installs run Ollama, the rules router may not be worth building — confirm how many users actually run without an LLM.
- Do contextual chips need the full confirmation gate for *read* actions (e.g. "Find cheaper")? Reads don't mutate — likely only action chips need the gate. Worth an explicit data/action split on chips.
- Capability discoverability: with one registry, should there be a generated "here's everything Dora can do" help surface, replacing the hand-maintained `DoraHelpPage.vue`?

---

## 7. LLM provider & connectivity (2026-06-12 addition)

User feedback during browser-verify of FU-085 surfaced four concerns
that the original proposal didn't cover. They all touch the **LLM
client + config** side, not the routing/registry side above.

> **User sign-off 2026-06-12:** §7.1–§7.4 endorsed as written, with
> the clarification that the per-user Assistant config lives in
> `PreferencesSettings.vue` alongside the existing C-cross per-user
> toggles (folded into §7.1). §7.3 explicitly accepted: same
> connectivity story as the rest of the app — frontend needs the
> backend, backend needs the LLM, no special case. Ready for an
> IMPL plan to be drafted from this section.
>
> **PR1 shipped 2026-06-29 (FU-153):** §7.1 + §7.4 + §7.6 landed in
> one PR, with two adjustments to what §7.1/§7.4 originally said.
>
> - **Settings home: not `PreferencesSettings.vue`.** That page
>   ships Appearance only (theme + font + text-size); the actual
>   per-user opt-in pattern in the codebase is *one page per
>   family* (`MoneySettings.vue`, `NutritionSettings.vue`,
>   `VoiceSettings.vue`). PR1 added a sibling
>   `AssistantSettings.vue` instead of grafting an "AI" block onto
>   Appearance. The sidebar entry sits between *Nutrition* and
>   *About*.
> - **Provider client location: kept in `infrastructure/llm/`,
>   not moved to `features/assistant/llm/`.** The `LlmClient` ABC
>   already lived under `infrastructure/llm/`; the three new
>   provider classes (OpenAI, Anthropic, Gemini) ship as siblings
>   to `OllamaClient` there. The factory (`factory.py`) and the
>   key-encryption helper (`key_encryption.py`) sit in the same
>   package. Less file motion (R-007); the abstraction already
>   had the right home.
>
> **PR2 shipped same day 2026-06-29 (FU-330 + FU-331 + FU-332):**
> the three §7 follow-ups also landed, finalising the feature.
>
> - **FU-330 — §7.2 probe + banner.** `/api/assistant/status` now
>   returns `{ai_available, reason}` (factory sentinels surface
>   their own reason; live-probe failures fall back to a generic
>   "didn't respond" copy). `DoraChat.vue` renders a removable
>   negative-soft banner at the top of the chat panel when the
>   user has `llm_enabled=true` but `ai_available=false`,
>   with a **Retry** affordance (re-runs `refreshAiStatus`) and
>   a quick link to **Settings → Assistant**. Plain Basic-mode
>   users (`llm_enabled=false`) never see it — Basic isn't a
>   failure mode. Per the proposal: probe-once-per-open, no
>   background polling.
> - **FU-331 — §7.3 docs sweep.** HelpPage's "Dora itself" guide
>   group gained two new entries explaining the
>   backend-reaches-LLM network topology and the
>   `DORA_LLM_KEY_ENCRYPTION_KEY` env var for paid providers
>   (with a generator one-liner). README's AI-assistant
>   bullet rewritten end-to-end: per-user pattern, all four
>   providers, encryption-key setup, network topology gotcha.
>   AssistantSettings.vue's inline help text kept (the page-
>   local hint stays useful; the HelpPage now carries the
>   longer-form coverage).
> - **FU-332 — per-user probe / Test connection.** New
>   `POST /api/assistant/probe` endpoint (separate from the
>   admin `/api/app-settings/probe` — that one stays admin-only
>   as the historic SSRF gate; the per-user version layers
>   per-user rate-limiting at 10/min + audit logging via
>   `audit_emit('assistant.probe', ...)` capturing actor +
>   provider + target host + outcome). Request body falls back
>   to the saved encrypted key when `api_key` is null so the
>   SPA doesn't force the user to re-type the masked field for
>   every probe. AssistantSettings.vue renders a **Test
>   connection** button next to each provider's fields, with
>   inline success/failure status (cleared on any field edit
>   so a stale green tick can't mislead). For Ollama, a
>   successful probe also reports how many models the endpoint
>   advertises.

### 7.1 Per-user LLM config (replaces install-wide)

**Today:** `AppSetting` is a **singleton install-wide row** holding
`llm_enabled`, `llm_base_url`, `llm_model`. Every user in the install
shares one config; the System → Features admin owns it.

**Problem:** in a household, two users may each run an LLM on their
own desktop, with their own URL/model. The install-wide config can
only point at one of them.

**Proposal:**

- Move `llm_*` from `AppSetting` to a new **per-user**
  configuration: `User.llm_enabled`, `User.llm_base_url`,
  `User.llm_model`, plus the **provider** column from §7.4 below.
- Keep one install-wide knob: a `master_llm_enabled` flag on
  `AppSetting` that lets the admin disable the whole assistant
  feature install-wide (defence in depth — power user opens a port,
  admin can still kill the feature). When this is off, every user's
  AI mode is forced off regardless of their per-user setting.
- Settings UI: **slot into `PreferencesSettings.vue`** alongside
  the existing per-user toggles (`money_features_enabled`,
  `nutrition_mode`, `show_recipe_images`, `show_stock_images`).
  An "Assistant" group on that page carries the per-user
  `llm_enabled` toggle + URL + model + provider (with the
  provider-specific fields surfacing conditionally — see §7.4).
  System → Features keeps the **master enable** as the only
  install-layer knob. **User-confirmed 2026-06-12:** this is the
  natural home — same shape as the other per-user opt-ins that
  C-cross landed.
- Backend: `_build_assistant_client()` reads the **current user's**
  config (already authenticated via the existing middleware), not
  the singleton `AppSetting`.
- Migration: pre-release semantics (no production data to preserve)
  — drop the `AppSetting.llm_*` columns; add the per-user columns
  + a `master_llm_enabled` flag with `server_default='1'`. Logged
  as one Alembic migration when this lands.

### 7.2 Reachability probe + soft fallback

**Today:** `AssistantHandler` calls the LLM **per request**; on
`LlmUnavailable` it returns `defer_to_local=True` and the frontend
**silently** uses the rules engine. The user never finds out why
their "smart" answer is dumber than yesterday.

**Problems:**

1. **Per-request retry cost.** Every send pays the LLM-timeout
   before falling back. If the user's LLM is consistently down
   that's a ~10-second wait on every message.
2. **No user signal.** AI mode looks on but acts off; the user
   thinks the assistant is dumb, not unreachable.

**Proposal:**

- **Probe once per chat open**, not per message. The frontend
  pings a cheap `GET /api/assistant/ping` (new endpoint — backend
  resolves the current user's config, attempts a 1-second
  metadata call against the LLM, returns `{available: bool,
  reason?: string}`). Result cached for the chat session; cleared
  when the chat panel closes/re-opens.
- **Visible degradation banner.** When `available === false &&
  user.llm_enabled === true`, render a small banner at the top
  of the chat: *"AI mode unavailable — using basic mode. Your
  LLM at `<host>` didn't respond."* with a **Retry** affordance.
  Retry re-runs the probe; success removes the banner mid-session.
- **No background polling.** Plan says "not polling, just once
  per open" — explicitly: don't poll on a timer; only re-probe
  on (a) chat panel open, (b) explicit Retry click, (c) user
  changes their LLM config in Settings.
- The existing **per-request `LlmUnavailable` fallback stays**
  as a safety net for "LLM died mid-conversation" (probe says
  up, then turns off). The banner shows on that fall-through too.

### 7.3 Network-topology constraint (document it)

**Reality:** Dora has three movable parts — **device**
(phone/laptop running the SPA), **backend** (Dora API), **LLM host**.
The LLM URL is reached **from the backend**, not from the device's
browser. The frontend never sees the LLM URL.

**Consequence:** the backend must be on a network that can reach
each user's LLM. For "household, two desktops" deployments:
- If backend lives on User A's desktop and User B's LLM also lives
  on User A's desktop → fine (loopback + LAN).
- If backend lives on a third box (NAS, Pi, VPS) → each user has to
  expose their LLM to that box (port forward / Tailscale / similar).
- If User B is on their phone, away from home, their desktop
  asleep → backend can't reach the LLM → per-user fallback fires
  (§7.2), banner explains it.

**Action:** call this out in the Settings → Account "Assistant"
help text + the System → Features admin doc. No code change;
documentation closing the loop so users don't file
"my LLM isn't working" tickets when the real issue is reachability.

### 7.4 Multi-provider support (Ollama + paid APIs)

**Today:** the LLM client is **Ollama-only** (`ollama_client.py`,
function-calling format specific to Ollama's chat API).

**Proposal:** introduce a **provider abstraction**.

- New `dora_api/features/assistant/llm/` package with:
  - `LlmClient` (abstract): `chat(messages, tools) ->
    AssistantMessage`, `is_available()`, `probe()`.
  - `OllamaClient` (existing, moved here).
  - `OpenAiClient` — `https://api.openai.com/v1/chat/completions`;
    OpenAI-style tool calling (close to Ollama's already).
  - `AnthropicClient` — Claude `/v1/messages`; **different tool
    schema** (top-level `tools` + `content[]`-style replies). Worth
    a small adapter layer that normalises tool-call results to
    OpenAI shape before they reach `tools.py`.
  - `GeminiClient` — Google `/v1beta/models/<model>:generateContent`;
    yet another schema (functionDeclarations). Same adapter.
- Per-user config gains a `llm_provider` column: enum of
  `'ollama' | 'openai' | 'anthropic' | 'gemini'`. The Settings UI
  shows different fields per provider — Ollama needs URL + model;
  OpenAI/Anthropic/Gemini need an **API key** + model + (optional
  base URL for self-hosted relays).
- **API key storage.** **Encrypt at rest** with a per-install
  master key (separate from session secrets). The DB column is
  `llm_api_key_encrypted`; the assistant decrypts on use. Never
  log or return the key over the wire (settings GET returns
  `has_api_key: bool`, not the value).
- `_build_assistant_client()` becomes a factory keyed on the
  current user's `llm_provider`.
- **Streaming** stays out of scope (called out in §4 already), but
  the abstraction should leave room for it — most providers
  support SSE.

### 7.5 Adoption ordering for §7

These all touch the LLM-config storage, so do them in one migration:

1. **§7.1 per-user config** + **§7.4 provider column** in the same
   migration (additive — new User columns + master flag on AppSetting,
   drop the old AppSetting.llm_* columns). Backend
   `_build_assistant_client` switches to per-user lookup with
   provider dispatch (Ollama path only, others stub).
2. **§7.4 provider implementations** — Ollama (existing, just
   moved), OpenAI, Anthropic, Gemini. Each with a one-shot
   integration test against a recorded fixture (no live API calls
   in CI).
3. **§7.2 probe + banner** — `/api/assistant/ping` endpoint +
   frontend cache + banner UI. Trivial once §7.1 lands (each
   user's config is on `currentUser`).
4. **§7.3** — documentation only; HelpPage + Settings → Account
   "Assistant" tab help text.

This sequence keeps the schema change in one PR and lets the
provider work + the probe land independently afterwards.

### 7.6 Cross-refs to existing feedback

- The existing DORA BOT feedback (`Feedback _ Fixes - as of
  [06-Jun-2026].md` lines 452-460) covers UX shape (toggle slider,
  per-user mode preference, "turn the bot off completely",
  DoraBot rename). The toggle/preference items pair naturally with
  §7.1's per-user config — the "AI side disabled if unavailable"
  toggle visibly reflects the §7.2 probe result.
- "Users should be able to turn the bot off completely in
  settings" is already covered by `User.llm_enabled` in §7.1; the
  per-user preference makes this trivially per-user too.
