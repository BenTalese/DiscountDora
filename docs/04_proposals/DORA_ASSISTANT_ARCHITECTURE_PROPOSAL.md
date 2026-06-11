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
4. **Rules router over real capabilities** — rebuild Basic mode as a parser that resolves to registry capabilities; retire the canned `doraIntents.ts` responses.
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
