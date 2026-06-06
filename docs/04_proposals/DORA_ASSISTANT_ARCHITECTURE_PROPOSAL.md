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
