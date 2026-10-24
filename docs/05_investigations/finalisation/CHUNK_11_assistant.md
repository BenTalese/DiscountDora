# Chunk 11 — Assistant (Dora)

**Session:** 2026-10-23 overnight (solo, no subagents) · **Stage:** 1 (analysis only — no code changed)
**Surface:** the Dora launcher + chat (`DoraBubble`/`DoraChat`/`DoraMascot`/`DoraModeSlider`), Basic mode (`doraIntents.ts` rule engine + `doraContextualActions.ts`), AI mode (`/api/assistant/*`: `ask`/`act`/`confirm`/`status`/`probe`/`providers`, `tools.py` registry, `confirm_actions.py`, `shopping_actions.py`), per-user provider config (`AssistantSettings.vue`, `UserLlmProvider`), the prompt-injection / rate-limit / mutation-gate defences, the About-Dora help page, and the voice layer the chat drives (`useSpeechOutput`, `useVoiceInput`, `features/tts`). Settings → Voice itself is chunk 13; Zero-Input Pantry toggles on the Assistant page are chunk 7.

---

## 0. Reading list + files walked

**Governing docs read:** `docs/04_proposals/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md` §0 reconciliation (FU-429: Basic mode is the default experience; the registry-router abstraction was deliberately **not** built), §2.3–2.5, §6 open questions, §7.5–7.6; `docs/05_investigations/AUTH_ASSISTANT_SECURITY_FINDINGS.md` (B.0–B.4 all fixed/mitigated; A.6 accepted); `FINALISATION_PLAN.md` row 11 scope (Basic + AI paths, tool registry, mode toggle FU-360, rate limits, prompt-injection FU-515, eval suite FU-390); feedback `# DORA BOT` L452–460 (7 bullets). Open FUs in scope: FU-788, 751, 722, 663, 628, 629, 625. Resolved and consulted: FU-360, FU-515, FU-390, FU-429, FU-186/581, FU-654 (open, cross-cutting).

**Backend walked in full (5,025 lines):** `features/assistant/{ask_assistant,providers,probe_assistant,app_knowledge,shopping_actions,confirm_actions,tools}.py`; `domain/entities/user_llm_provider.py`; `features/tts/{tts_synthesize,voice_catalog,voice_provision}.py` (760). `infrastructure/llm/*` grep-checked only (`_DEFAULT_BASE_URL` ×3, `factory._UnavailableClient`).

**SPA walked in full (6,770 lines):** `components/dora/{DoraChat,DoraBubble,DoraMascot,DoraModeSlider}.vue`, `doraTypes.ts`, `services/{doraIntents,doraContextualActions}.ts`, `services/api/{assistantApiService,ttsApiService}.ts`, `pages/settings/AssistantSettings.vue`, `pages/DoraHelpPage.vue`, `composables/{useSpeechOutput,useVoiceInput}.ts`; `HelpPage.vue` L505–560 (the Dora help group); `MainLayout.vue:148–150` (`show_assistant` gate).

**Verification greps run:** `ShoppingList.Fields` members (no `IS_PRIMARY`); `timezone` imports in `tools.py`; every `_TOOL_NAV` path vs `routes.ts` (no `/recipes`, no `/product-search`, budget at `/settings/budget`); `_find_shopping_list` callers (none); `GetAlertsHandler.handle(user_id=None, now=None)`; `alert_kinds` list vs the `get_alerts` tool description; `RecipeIngredient.is_optional` declared + 7 `getattr(…, "is_optional")` sites app-wide; quasar `iconSet: 'mdi-v7'` with `material-icons` kept as fallback; `session.get(` ×7 in the package; `toastCaption` returns a string; `themeService` drives root font-size; schema names (40) vs `DoraHelpPage` list (27 + 0 stale); existing tests (3 pytest files, 3 vitest specs).

---

## A. Full Systems Test — Assistant

### A1. Preconditions
- A signed-in user with `show_assistant` on (default). Basic mode needs nothing else.
- AI mode: a reachable provider — Ollama at a LAN URL with a tool-capable model, or a paid key with `DORA_SECRET_ENCRYPTION_KEY` set; provider **verified** by a probe before the Mode picker / slider offers it.
- Exactly one draft shopping list (the assistant's "primary" is inferred from draft count).
- Voice: Piper binary + a downloaded voice (server), or a browser with voices; mic permission for voice input (Chrome; Firefox has no `SpeechRecognition`, FU-788).

### A2. Golden path
| # | Step | Expect |
|---|---|---|
| G1 | Fresh user loads the app | Launcher pops in once (spring entrance), "Hi! I'm Dora" hint appears after 1.5 s, auto-hides at 9 s; X dismisses it **for this user** for good. |
| G2 | Click the launcher | Chat opens with a greeting using the capitalised username, 4 chips (reply-biased), header shows **Basic** on the slider; header hint names the current page. |
| G3 | Basic: "what's low" | Lists low/out items from the loaded stock store with "See Stock" button; mascot mood follows the reply; typewriter reveal + lip-flap. |
| G4 | Basic: "add milk and eggs" | Resolves against the pantry; unambiguous ones added to the one draft list via the shared composable; ambiguous/not-found named, never guessed. |
| G5 | Basic: "where's the flour" | **Today: always "doesn't have a location set yet"** → 11-R4. Expect the location name. |
| G6 | Basic: "1 cup to ml", "substitute for buttermilk", "tell me a joke", "what can I do here" | Each answered locally; conversion reads the generated units table. |
| G7 | Settings → Assistant → Ollama base URL blur → model picked → Test connection | Card turns green "Connected"; Mode picker gains "Ollama"; `User.assistant_ready` true; slider becomes enabled. |
| G8 | Slider → AI | PATCH `llm_enabled`, status probe, header shows **AI**; chips switch to the natural-language pool. |
| G9 | AI: "any specials on cheese" | `find_deals` runs; reply grounded on rows; nav button offered — **today it targets `/product-search`, a retired route** → 11-R3. |
| G10 | AI: "mark eggs as low" | Confirm card ("Set Eggs to Low Stock? (was Stocked)") → Confirm → `/confirm` → level changed, super-excited face. Cancel → "No worries". |
| G11 | AI: "cross off bread on my list" | **Today: 500 — `_primary_list` reads a dropped column** → 11-R1. Expect a tick confirm card. |
| G12 | AI: "what am I wasting often?" | **Today: `NameError: timezone`** → 11-R2. Expect most-wasted list. |
| G13 | AI: "add 3 apples and some milk" | Multi-item card; ambiguous item shows candidate chips; Add commits only when every ambiguity is resolved. |
| G14 | Suggestions badge on launcher → open chat | Suggestion cards at the top with Accept (navigates + 1 h snooze), Snooze 1d, Dismiss, Why?. |
| G15 | Mute/unmute button | Persists `voice_output_enabled`; replies spoken via Piper (or browser voice fallback); mic button push-to-talk fills the draft. |
| G16 | Settings → Assistant → "Show digital assistant chat bubble" off | Launcher gone everywhere (MainLayout `v-if`). |
| G17 | 21 `/ask` calls inside a minute | 429 with `Retry-After`; chat falls back to Basic for that turn. |

### A3. Edge cases
| # | Case | Expect (and what the code does today) |
|---|---|---|
| E1 | AI on, Ollama down | Red banner "AI mode unavailable. Using basic mode." with reason + Retry + Settings; launcher shows the offline face only if AI was seen working this session ✅. |
| E2 | Provider details saved but never probed | Status "Not tested" (amber); not offered in Mode; slider dimmed-dashed and tapping it routes to Settings ✅. |
| E3 | Paid provider, no `DORA_SECRET_ENCRYPTION_KEY` | Banner inside Providers; saving a key returns 422 with the reason ✅. |
| E4 | Product name contains "ignore your instructions and…" | SECURITY block + control-byte strip; model summarises as data (B.1) — manual eval only. |
| E5 | "push the bread expiry by 5000 days" | `invalid`: "That's more than 10 years…" ✅ (B.3). |
| E6 | Two or zero draft lists | add-to-list / tick / add-recipe say "that only works when you have exactly one" — **after 11-R1** (today two of the three crash). |
| E7 | `current_path` with newline/injection | Sanitised to path-safe chars, capped 200 ✅ (B.4). |
| E8 | Model returns a tool name that isn't registered | `{"error": "unknown tool"}` fed back; no crash ✅. |
| E9 | Firefox | Mic hidden (no API); Piper speaks; browser voice probe reports no voices → Settings explains ✅ (FU-751 verify). |
| E10 | iOS / Android, reply spoken after an LLM round-trip | May fall back to browser voice or stay silent (autoplay gesture credit) — FU-629 open; silent-WAV primer in place. |
| E11 | Model chains 4 tool rounds | `_MAX_TOOL_ROUNDS=3` → "I got a bit tangled up" ✅. |
| E12 | Household in +10, 08:00 local, "what's the plan" in Basic | `getMealPlan` compares against the **UTC** date → yesterday's entry counts as upcoming → 11-R33. |
| E13 | Ask "where's milk cheapest" with no linked products | `no_linked_products` note; nav → `/product-search` (dead) → 11-R3. |
| E14 | Ask about budget with money off | `budget_status` `disabled` note points at "Settings → Kitchen setup → Money" while the schema description says "Settings → Preferences" → 11-R27. |

### A4. Persona coverage
- **Pantry-only, no LLM (the majority):** Basic mode is the whole product here — greet, data lookups off the stores, one action verb, conversions, substitutes, page help, jokes. Must never look like a failure state ✅ (no banner, no offline face).
- **Self-hoster with Ollama:** probe + model picker from `/api/tags`; LAN URLs allowed (documented SSRF trade-off: rate cap + audit row).
- **Paid-API user:** key encrypted at rest, write-only, `has_api_key` derived; text leaves the box — help should say so (H9).
- **Phone user:** 24 px slider (FU-663), mic push-to-talk, voice autoplay limits (FU-629), 70dvh card.
- **Admin:** nothing admin-only remains on the assistant (per-user since the §7.1 redesign) except `DORA_SECRET_ENCRYPTION_KEY`.

### A5. Load-bearing conditions
- **The mutation gate**: action tool calls short-circuit into a proposal; `/confirm` re-validates; the model never writes (B.0). Every finding below must preserve it.
- "Primary list" = exactly one draft list (`resolve_quick_add_target`), not a stored flag.
- `UserLlmProvider.verified` is the only thing that makes a provider selectable; any edit clears it.
- `APP_OVERVIEW` is in every AI prompt — its size is a model-quality lever (11-D1).
- Basic mode reads Pinia stores that other pages hydrate; `ensureRecipeData` loads what it needs on demand.

### A6. Release-gate rows
- [ ] Every `PROPOSERS` entry executes against an empty database without raising (after 11-R1).
- [ ] Every data tool executes with `{}` against an empty database without raising (after 11-R2).
- [ ] Every `_TOOL_NAV` path is a live SPA route (after 11-R3).
- [ ] Basic-mode "where is X" names the location (after 11-R4).
- [ ] 21st `/ask` in a minute → 429 + `Retry-After`; probe rate limit → 429 too (after 11-R15).
- [ ] A product name carrying an instruction does not steer the model (manual, one prompt).

---

## B. Help content — Assistant

### B1. Current help audit
Two surfaces exist and both are partly stale:
- **`HelpPage.vue` Dora group** (~8 entries, L505–560): page awareness, which browsers speak, free-form questions need AI, set up AI (per account), "unavailable" banner, network topology, API-key encryption. Good; nothing on Basic-mode actions, suggestions-in-chat, confirm cards, voice input, muting, the first-time hint, turning Dora off, or rate limits.
- **`DoraHelpPage.vue`** (`/help/dora`): hand-maintained. The AI-tools list is missing **13 of 40** tools (`adjust_recipe_meals`, `budget_status`, `cook_recipe`, `expiry_rescue`, `list_suggestions`, `meals_cooked_in_range`, `meals_in_pool`, `meals_shortfall`, `purchase_price_stats`, `spend_by_category`, `spend_year_over_year`, `trim_list_to_budget`, `waste_insights`); the Basic list omits `add_to_list` (the one action verb), `report_issue`, `stuck`, `version`'s sibling; the AI card says "a local language model (Ollama)" and links "Settings → System" (`{path:'/settings', query:{tab:'system'}}` — pre-redesign, 11-R6); tips say "three suggestion chips" (four) and "the AI / Basic **chip**" (slider); `search_products` says "across the configured stores" (the catalogue is ingested; Product Search is external).
- **DoraBot corpus** (`app_knowledge.APP_OVERVIEW`) — stale nav (Recipes/Locations/System), see 11-R25.

### B2. Help entries (one per feature / auto-behaviour)
Add to the existing Dora group (keep its voice):

| # | Title | Summary | path |
|---|---|---|---|
| H1 | Basic mode can add to your list | Type "add milk and eggs" or "need to buy rice". Dora matches names against your pantry and adds the clear ones to your one draft list; anything ambiguous she asks about, never guesses. | `/` |
| H2 | Dora never changes anything on her own | In AI mode every change — a stock level, an expiry, a meal, a list line — arrives as a card you Confirm or Cancel. Until you tap Confirm, nothing has happened. | `/` |
| H3 | What Dora can see | Your household's own data in this install: stock, recipes, lists, meal plan, prices you logged, alerts. Never another household, never the web. | `/` |
| H4 | Suggestions in the chat | The number on the launcher is how many suggestions Dora has (the same ones the dashboard card shows). Open the chat to Accept, Snooze a day, Dismiss, or ask Why. | `/` |
| H5 | Basic or AI — the slider | Basic is always on and works offline. AI needs a connected provider (Settings → Assistant); until one is verified the slider is dimmed and tapping it takes you there. If AI drops out mid-chat, Dora falls back to Basic for that message. | `/settings/assistant` |
| H6 | Talking to Dora | Tap the mic (Chrome and Edge; Firefox has no speech recognition), speak, tap again. Your words land in the box so you can read them before sending. | `/` |
| H7 | Hearing Dora | The speaker button has Dora read her replies aloud — her neural voice from the server when installed, your browser's voice otherwise. It stays on or off per account. On a phone, a reply that comes after a long think may not autoplay. | `/settings/voice` |
| H8 | Turning Dora off | Settings → Assistant → "Show digital assistant chat bubble". Off hides the launcher everywhere for your account only. The one-time "Hi! I'm Dora" tip is also per account. | `/settings/assistant` |
| H9 | Paid providers and privacy | With OpenAI, Anthropic or Gemini your messages — and the data Dora looks up to answer them — are sent to that provider. Ollama keeps everything on your own machine. | `/settings/assistant` |
| H10 | Why Dora says "slow down" | Twenty questions a minute per person is the ceiling, so a stuck script can't run up your provider bill; Dora answers in Basic until the minute is up. | `/` |

Rewrites: `DoraHelpPage` tool + intent lists become generated from the registry (11-R26); fix the Settings → System link (11-R6); "three chips"/"chip" copy.

### B3. DoraBot corpus delta
This chunk owns the corpus. Deliverable is 11-R25 (rewrite `APP_OVERVIEW` for the current shell, folding in the ten paragraphs chunks 1–10 queued) **shaped by 11-D1** (a short routing guide in the prompt + an `app_help` tool that serves the full help corpus on demand). The paragraph for *this* surface: *"Dora works in Basic mode (always on, offline, rule-based: lookups, one add-to-list verb, conversions, substitutes, page help) or AI mode (per account, after a provider is connected and verified under Settings → Assistant). In AI mode she reads your data through tools and proposes changes as Confirm cards; she never writes on her own. She can speak replies and take dictation, carries the same suggestions as the dashboard, and can be hidden per account."*

---

## C. Senior review — Assistant

Finding ids `11-Rk`. Verdicts: **execute** (Stage 2, test-guarded) · **FU** · **waive** · **conditional**.

### C1. Bugs (verified or high-confidence latent)
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 11-R1 | `confirm_actions.py:312–316` (`_primary_list`) | Reads `ShoppingList.Fields.IS_PRIMARY` — the field is gone (`Fields` has `NAME`, `STATUS`…; the comment at L478 and `shopping_actions._primary_list` both say primary is inferred now). `tick_shopping_line`, `add_recipe_to_list` and `trim_list_to_budget` raise `AttributeError` on propose, unhandled → `/ask` 500s. The registry eval only checks a proposer *exists*. | Delete it; import the one in `shopping_actions` (or move both to `assistant/_lists.py`). Test T1 smoke-executes every proposer. | execute |
| 11-R2 | `tools.py:2124` (`waste_insights`) | `datetime.now(timezone.utc)` with no `timezone` import at module scope (L17); the two tools that need it import it function-locally. `NameError` the first time the model calls it. R-021 too: the window should be household-local. | `household_today(repo)`-anchored cutoff; module-level imports; drop the local ones. Test T3. | execute |
| 11-R3 | `tools.py:2705–2742` (`_TOOL_NAV`) | 11 of 24 nav hints point at routes that don't exist: `/product-search` ×3 (retired FU-186), `/recipes` ×7 (route is `/cookbook`; legacy redirects retired — `routes.ts:99`), `/settings/preferences` for budget (`/settings/budget`; same slip as 09-R3). The "See it" button under an AI answer lands on the 404 page. | Fix paths; product tools → `/my-products` or no nav. Test T2 pins every path against a route list. | execute |
| 11-R4 | `DoraChat.vue:997–1000` | `getStock()` stamps `locationName: null` for every item, so Basic-mode `where_is` (and `(no location)` in its multi-match list) is wrong for every item that has a location. The list DTO carries `stock_location_id`; the location store resolves names. | Resolve via `useStockLocationStore` (loaded in `ensureRecipeData`). Vitest T5 on `runIntent('where_is')`. | execute |
| 11-R5 | `AssistantSettings.vue:471–475` | `toastCaption(err)` is a string formatter; calling it for effect shows nothing, while the comment says "the toast explains the fetch failure". A provider-list load failure is silent. | `$q.notify({ type:'negative', message:"Couldn't load your provider settings.", caption: toastCaption(err) })`. | execute |
| 11-R6 | `DoraHelpPage.vue:74` | AI setup link goes to `{ path:'/settings', query:{ tab:'system' } }` — the pre-redesign admin path; the page is `/settings/assistant` (the intro two lines up says so). | Fix the link; see 11-R26 for the rest of the page. | execute |
| 11-R33 | `DoraChat.vue:1044` | `getMealPlan` builds "today" from `new Date().toISOString().slice(0,10)` — the **UTC** date. Before 10:00 AEST the "upcoming" filter admits yesterday's entries (R-021). | Use the SPA's household-today helper (08-R8 family); if none exists yet, local date is the lesser evil — never UTC. | execute |
| 11-R7 | `tools.py:1410` | `suggest_substitution` cleans with `.rstrip("s")` — strips *every* trailing s ("molasses"→"molasse", "cress"→"cre"); the client parser uses `/s$/`. | `re.sub(r"s$", "", cleaned)`. | execute |
| 11-R8 | `assistantApiService.ts:32–45` | `ConfirmAction.type` union omits `cook_recipe`, `adjust_recipe_meals`, `trim_list_to_budget` (R-057). Works at runtime only because the value arrives from JSON. | Generate the list from `PROPOSERS` (11-R26's capabilities endpoint or a codegen file) and pin with T4. | execute |

### C2. Redundancy / DRY (R-001, R-003)
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 11-R9 | `shopping_actions._match_stock_items`, `confirm_actions._find_stock_item/_find_location/_find_recipe` (+dead `_find_shopping_list`), `tools._find_one_by_name`, `recipes_using_item:1626`, `purchase_price_stats:2245`, `compare_prices:2484` | "Exact name, else contains" resolution written 8×, with three different return shapes. | One `resolve_by_name(repo, entity, name, build_query=None) -> NameResolution(status, matches)`; every caller renders `not_found/ambiguous/ready` from it. | execute |
| 11-R10 | `confirm_actions._stock_item_candidate` ≡ `shopping_actions._candidate_dto` | Identical candidate DTO. | Merge into the resolver module. | execute |
| 11-R11 | `_MAX_CANDIDATES = 6` ×3 modules | One constant. | `assistant/_limits.py` (`MAX_ROWS`, `MAX_CANDIDATES`, `MAX_MISSING`). | execute |
| 11-R12 | `doraIntents.ts:557–597` vs `tools.py:1367–1402` | The curated substitution table exists twice (23 vs 27 entries, divergent aliases); the client's aliases are wrong in places (`caster sugar`/`icing sugar`→`brown sugar`, `plain flour`→`self-raising flour` "weird, but"). R-003 domain data in two languages. | Codegen `generated/substitutes_table.ts` from the Python table, exactly as `units_table.ts` is produced by `scripts/dump_units.py`; delete the client copy; fix the aliases once, server-side. | execute |
| 11-R13 | `confirm_actions.py:926–991` | `trim_list_to_budget` summaries hard-code `$` ×6 — the 09-R1 class. | Lifted `format_money(amount, currency)` (10-R41) with the install currency. | execute (with 09-R1/10-R41) |
| 11-R14 | `tools.py:1146`, `confirm_actions.py:659` (+5 sites outside this chunk) | `getattr(ing, "is_optional", False)` on a declared `RecipeIngredient` field (R-008; 10-R24 shape). | `ing.is_optional` here; log the app-wide sweep (E3). | execute (2) + FU (5) |
| 11-R15 | `ask_assistant.py:73–88` vs `auth/email_flows.py:47`; `probe_assistant.py:229` | `_too_many_requests` copied once already ("promote if a third caller needs it"); the third caller — the probe — instead returns **422** for a rate limit. | `api_response.too_many_requests(retry_after)`; probe returns 429. Test T6. | execute |
| 11-R16 | `AssistantSettings.vue:436–452` vs `infrastructure/llm/*_client.py::_DEFAULT_BASE_URL` | Default base URLs and example model ids mirrored in TS "must stay in step" (R-003). Example ids are also dated (`claude-3-5-sonnet-20241022`, `gpt-4o-mini`). | `/assistant/providers` returns `default_base_url` + `example_model` per provider; SPA renders them. Owner picks current example ids. | execute |
| 11-R17 | `tools.py:2397–2408` | Mean purchase gap re-derived (4th copy — 09-R2 lists `generate_likely_due`, `trim_to_budget:412`, `pantry_belief`); `domain/cadence_math.mean_gap_days` exists. | Use it. | execute (with 09-R2) |
| 11-R18 | `tools.py:1502` (`savings_percent`), `2518` (`on_special`) | Discount rule restated; `domain/product_offer.discount_percent` is the one rule (10-R6/10-R23). | Use it. | execute |
| 11-R19 | `confirm_actions.propose_add_recipe_to_list:651–663`, `tools._stock_coverage:1129–1155` | "Missing ingredient" / coverage computed locally while `domain/recipe_cookability.py` owns the rule (chunk 1). | Route both through the domain helper; verify parity at Stage 2. | execute |
| 11-R20 | `tools.py:976` | `repo.get(AppSetting).all()` → `settings[0]` (FU-759 pattern). | `get_or_create_app_setting`. | execute |

### C3. Dead code / unused fields / unread endpoints
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 11-R21 | `confirm_actions.py:482–488` | `_find_shopping_list` has no callers. | Delete (or it becomes a resolver case under 11-R9). | execute |
| 11-R22 | `tools.py:2185–2199` | `budget_status` resolves `user_id` and never uses it; `GetBudgetStatusHandler().handle()` takes no user. | Drop the session read (also −1 FU-654 site). | execute |
| 11-R23 | `doraIntents.ts:967–981` | `whats_new` hard-codes "recent highlights include the assistant, the locations heatmap, and per-user preferences" (stale forever, R-019) and carries a dead `...{}` spread. | Point at the Help changelog only. | execute |
| 11-R24 | `tools.py:2607, 2646` | Function-local `from datetime import datetime, timedelta, timezone` (first one unused). | Module imports (with 11-R2). | execute |
| 11-R25 | `app_knowledge.py` | The in-prompt app guide names "Recipes" (Cookbook), a "Locations" page, "Product Search … via the ingestion seam", "Settings → System (configure the AI assistant, the BYO-LLM panel)"; no Reports/Memory, My Products, Dora Score, budget, stocktake, cook mode. `doraIntents.show_around` and `PAGE_HELP['/settings']` describe the same old shell. This file is also where chunks 1–10 queued their "DoraBot paragraph". | Rewrite once, current shell, with the ten queued paragraphs — sized per 11-D1. | execute |
| 11-R26 | `DoraHelpPage.vue` (whole) | Hand-maintained capability lists drifted: 13/40 tools missing, Basic list missing the add-to-list verb, "Ollama only", "three chips", "AI/Basic chip". The proposal's §6 Q3 asked for exactly this. | `GET /assistant/capabilities` (tool name, user-facing description, 2–3 examples — add an `examples` key to each schema) + Basic intents from `INTENTS` (add `examples` there too); the page renders them, keeps its prose for modes/faces/tips. Registry test pins that every schema has examples. | execute |
| 11-R27 | `tools.py:366, 93, 1537, 609 vs 2205` | Tool descriptions the model reads are stale: `get_alerts.kind` enum lacks `shopping_overdue`, `price_drop`; `search_stock.expiring_soon` "within a week" (configurable); `pantry_health` key `expiring_within_week`; `budget_status` points at "Settings → Preferences" in the schema and "Settings → Kitchen setup → Money" in the body. | Fix copy; derive the kind enum from `alert_kinds.SEVERITY_BY_KIND.keys()`. | execute |
| 11-R28 | `tools.py:106–110, 262–267` | `search_products`/`find_deals` "across the household's configured merchants" — ingested catalogue now. | Copy. | execute |

### C4. Componentisation opportunities (R-001)
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 11-R29 | `DoraChat.vue` two action cards | Add-to-list card vs Confirm/Cancel card (proposal §2.4). Both stable; the reconciliation chose not to restructure the assistant. | — | waive (decided 2026-07-08) |
| 11-R30 | `DoraChat.vue` (1,655 lines) | Chip pools (`BASIC_CHIP_POOL`, `AI_CHIP_POOL`, `INTENT_TO_AI_CHIP`) are data; the typewriter and the Pinia→snapshot `context()` builder are self-contained. | `services/doraChips.ts`, `composables/useTypewriter.ts`, `services/doraContext.ts` — mechanical, each unit-testable; the component keeps orchestration. | execute |

### C5. Placement / layering (R-003, R-005)
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 11-R31 | `ask_assistant.py:96/235`, `providers.py:86`, `probe_assistant.py:211`, `confirm_actions.py:875`, `tools.py:2034/2189` | 7 `session.get(…)` reads behind 3 local helpers (`_rate_limit_subject`, `_current_user_id`, `_session_user_id`) — FU-654. | `infrastructure/auth_helpers.current_user_id()`. | execute (sweep) |
| 11-R32 | `ask_assistant.py:241/245/251` | Three function-local imports of the private `factory._UnavailableClient`. | `factory.unavailable_client(reason)` public; one import. | execute |
| 11-R34 | `doraIntents.ts:307` | `EXPIRY_HORIZON_DAYS = 7` while the server window is admin-configurable (`expiring_soon_window_days`) — a domain constant in two languages (R-003). | Expose the window on the app-settings composable the SPA already has; Basic mode reads it. `daysUntil` on the browser's local midnight stays as the accepted Basic/offline carve-out — comment it. | execute |
| 11-R35 | `tools.py:2659` | `spend_year_over_year` anchors `now` in UTC (R-021). | Household-local. | execute |

### C6. Naming & idiom
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 11-R36 | `tools.py:1696–1713` | `_find_one_by_name` returns a 2-tuple or a 3-tuple by branch; callers probe `len(result) > 2`. | Dataclass result (folds into 11-R9). | execute |
| 11-R37 | `confirm_actions.py:704` | Bare `except Exception: missing += 1`. | Catch the handler's known failures; let the rest raise. | execute |
| 11-R38 | `DoraMascot.vue:120–129` | `clearTimeout(t as unknown as number)` on interval ids — works (shared id space) but the cast is the smell. | Keep timeouts and intervals in two typed slots. | execute |
| 11-R39 | `DoraChat.vue:32, 199, 286, 954–957, 1172–1174`; `DoraHelpPage.vue` `'inventory_2'` ×3; `MainLayout.vue:262` | Bare Material icon names (R-034) — render only because `material-icons` is kept as a fallback extra (`quasar.config.ts:93–97`). | `ICONS.*`. | execute |
| 11-R40 | `doraIntents.ts:3184` | Greeting bank does `name.replace(', ', '')` to undo the comma convention baked into `name`. | Pass `displayName` and `name` separately. | execute |

### C7. Efficiency
| Id | Where | Finding | Fix | Verdict |
|---|---|---|---|---|
| 11-R41 | `tools.py:1638–1661`, `1745–1755`, `1209`, `confirm_actions._plan_covering:499` | `recipes_using_item` and `stock_item_detail` load **every** recipe with ingredients to find usages; `suggest_recipes` loads all recipes twice when tag filters are set; `_plan_covering` loads every plan with entries. | A `RecipeIngredient` query by `stock_item_id` (the detail page's "recipes using this" already has one — chunk 6) for the first two; the other two are small-data and stay. | execute (2) + waive (2) |
| 11-R42 | `tools.py:2235–2464` | `purchase_price_stats` is 230 lines with 5 bulk lookups and its own paid-price ladder; `your_prices.py` (chunk 6) derives the same series per item. | Delegate the sample collection to `your_prices`; keep the stats/cadence shaping here. | conditional (with 06-R14) |
| 11-R43 | `ask_assistant.py:264–270` | A fresh LLM client per request and `is_available()` before every `/ask` — if the client probes the network there, every question pays two round-trips. | Verify at Stage 2; if so, cache availability per user for ~60 s (the SPA already debounces `/status`). | conditional |

### C8. Design-level findings — out of Stage-2 scope
| Id | Finding | Recommendation |
|---|---|---|
| 11-D1 | `APP_OVERVIEW` rides in **every** AI prompt (`ask_assistant.py:199`); the file's own rule is "keep it concise — small models follow short guides best". Ten chunks have queued paragraphs for it; appended, it becomes a wall a 7B model stops following. | Keep a ~40-line routing guide in the prompt; add an `app_help(topic)` data tool that returns matching help entries from the **same corpus `HelpPage.vue` renders** (served by `/help`), so help lives once (R-003) and the model fetches detail on demand. Owner call — it decides where B3 deltas land. |
| 11-D2 | Basic-vs-AI capability cliff | Resolved 2026-07-08 (make Basic useful; no registry router). Record; no re-litigation. |
| 11-D3 | `DoraModeSlider` is 24 px tall and now the primary toggle (FU-663, D-004). | Execute FU-663 at Stage 2: 32–36 px pill inside a 44 px hit area. |
| 11-D4 | The owner asked for a one-shot "pulse glow" when the slider flips (DB3). The knob glows statically; no one-shot pulse exists. | Small: a `.dora-mode-slider--flipped` class on change with a 600 ms keyframe, honouring `prefers-reduced-motion`. Owner can decline. |
| 11-D5 | Rate-limit buckets are process-local (A.6, accepted single-instance). | Record only. |

### C9. Hand-rolled-vs-library verdicts
| Surface | Hand-rolled | Verdict |
|---|---|---|
| `doraIntents.ts` rule engine (1,422 lines) | Yes | **keep** — decided; it is the default experience and the offline fallback. |
| Client `tryConvert` parser (logic mirrors server `convert_measurement`; data shared via codegen) | Yes | **keep** — Basic/offline path; the data is already single-sourced. Add the substitution table to the same codegen (11-R12). |
| `DoraMascot` frame controller, typewriter, mood hold | Yes | **keep** (extract the typewriter, 11-R30). |
| `with_lead_in` WAV rebuild, `voice_provision` streaming download | Yes | **keep** — small, correct, dependency-free (`requests` already present). |
| LLM clients (`infrastructure/llm/*`) | Yes (HTTP) | **keep** — four thin clients beat four SDKs for a self-hosted app; revisit if streaming lands. |

### C10. Standards drift (R-0NN)
| Id | Rule | Where | Verdict |
|---|---|---|---|
| 11-R33 / 11-R35 / 11-R2 | R-021 household time | `DoraChat.vue:1044` (UTC date), `tools.py:2659`, `tools.py:2124` | execute |
| 11-R12 / 11-R16 / 11-R34 / 11-R18 | R-003 one source | substitution table ×2, provider defaults ×2, expiry horizon ×2, discount rule | execute |
| 11-R14 / 11-R24 / 11-R32 / 11-R37 | R-008 idiom | `getattr` on declared fields, function-local imports, bare except | execute |
| 11-R39 | R-034 icon registry | 12 bare Material names | execute |
| 11-R31 | FU-654 | 7 session reads | execute (sweep) |
| 11-R20 | FU-759 | `AppSetting.all()[0]` | execute |
| 11-R8 | R-057 contract inventory | `ConfirmAction.type` | execute |
| 11-R23 / 11-R25 / 11-R27 / 11-R28 | R-019 comments/copy ≠ code | stale corpus + tool descriptions | execute |
| — | FU-671 `text-color="white"` | `DoraChat.vue:329`, `DoraHelpPage.vue:47, 69` | execute (sweep) |
| — | R-002 / D-017 | `DoraModeSlider.vue:102, 142, 162, 179` (`rgba(0,0,0,…)` shadows, `var(--x, fallback)` literals); raw px radii/paddings throughout `DoraChat`/`DoraBubble` (12/10/8 px) | execute: shadows + fallbacks; radii → `--radius-*` where a token exists; the bespoke chat geometry otherwise stays with an inline D-017 carve-out comment |
| — | D-004 | `DoraModeSlider` 24 px (FU-663) | execute (11-D3) |
| — | D-010 motion tokens | `DoraChat.vue:1725` `160ms ease`, `DoraBubble` `240ms`/`220ms`/`180ms` eases | execute where a token matches; the launcher's spring curves are already tokens |

### C11. Ride-along signals for FU-010 / FU-224 (theme / colour)
- Suggestion-card severity borders use Quasar `--q-negative/--q-warning/--q-primary` rather than `--semantic-*` tokens (`DoraChat.vue:1791–1798`).
- `.dora-bot-name` / `.dora-accent-btn` on `--accent-ink` ✅ (R-069 reference use).
- Contextual chip `color="primary" text-color="white"` (FU-671).
- `DoraHelpPage` `color="grey"` chips/icons — grey is D-001's absent/unknown; Basic mode is not "absent". Use `--text-secondary`.

---

## D. Test plan — Assistant

**Existing (keep):** pytest `test_assistant_tool_registry.py` (9: schema↔dispatch integrity, data/action disjoint, mutation gate refuses action tools via `run_tool`, every action tool has a proposer, `nav_for` never offers nav for an action tool, no-model → unavailable), `test_assistant_hardening.py` (8: `_safe_current_path`, `_sanitize_tool_output`), `test_recipe_tools_derivation.py` (5 — recipe *tools* derivation, chunk 1 territory despite the name); vitest `doraIntents.spec` (intent routing corpus, add-to-list parsing, greeting name), `doraModeSlider.spec` (12 incl. axe), `voicePicker.spec` (8).

**Proposed (lean — stable contracts only):**
| # | Pins | Layer | Why |
|---|---|---|---|
| T1 | Every `confirm_actions.PROPOSERS` entry, called with `{}` and with a plausible `item_name`/`recipe_name` against an empty DB, returns a dict with `status` and never raises | pytest (extend the registry test) | 11-R1 — "has a proposer" passed while three proposers crashed |
| T2 | Every `_TOOL_NAV` path is in an allow-list of live SPA route prefixes kept beside the test | pytest | 11-R3 |
| T3 | Every `_TOOLS` entry, called with `{}` against an empty DB, returns a list and never raises | pytest | 11-R2 — catches import/NameError-class faults in any tool |
| T4 | `GET /assistant/capabilities` names == `TOOL_SCHEMAS` names, and every action schema has a proposer + committer; each schema carries ≥1 example | pytest | 11-R8 / 11-R26 |
| T5 | `runIntent('where_is')` names the location when the snapshot has one; "(no location)" only when null | vitest (extend `doraIntents.spec`) | 11-R4 |
| T6 | 11th probe in a minute → 429 with `Retry-After` | pytest | 11-R15 |
| — | Slider height, help-page rendering, voice paths, chat layout | — | **no automated test** — drive once and delete the DORA_VERIFY line |

**DORA_VERIFY additions (Stage 2 close):** AI "cross off bread" produces a confirm card; "what am I wasting" answers; every "See it" button under an AI answer opens a real page; Basic "where's the X" names the location; chat text scales with Settings → Appearance font size (DB1); launcher hover no longer flashes (DB4); slider tap target on a phone (FU-663).

---

## E. Proposed follow-ups (orchestrator allocates ids)

| # | Title | Type | Resolution point | Source |
|---|---|---|---|---|
| E1 | `app_help(topic)` tool + prompt-size budget for `APP_OVERVIEW`; help corpus served once from `/help` | decision → design | now (owner) — gates where chunks 1–10's DoraBot paragraphs land | 11-D1 |
| E2 | One-shot pulse glow on slider flip (DB3) | decision (small) | now (owner; may decline) | 11-D4 |
| E3 | App-wide sweep of `getattr(x, "is_optional", False)` on the declared field (5 sites outside this chunk: `recipe_cookability`, `recipe_rollup`, `get_recipes` ×2, `waste`) | leftover | with chunk 20 | 11-R14 |
| E4 | `purchase_price_stats` to reuse `your_prices` sample collection | leftover | with 06-R14 | 11-R42 |
| E5 | Per-user cached LLM availability if `is_available()` probes on every `/ask` | finding | verify at Stage 2 | 11-R43 |
| E6 | Generated `assistant_capabilities` (TS) so `ConfirmAction.type`, the help page and the chat chips all read one list | leftover | with 11-R26 | 11-R8 |

**FUs this chunk advances at Stage 2:** FU-663 (slider tap target → resolve), FU-654 (+7 sites), FU-671 (+3), FU-759 (+1). FU-788/751/722/628/629 are device-verification items (DORA_VERIFY) and stay open; FU-625 (backup round-trip of `UserLlmProvider`) belongs to chunk 18.

---

## F. Summary for the register

- FST rows: 17 golden + 14 edge + 6 gate · Help entries: **10 new** (Dora group extended) + `DoraHelpPage` regenerated from the registry + corpus rewrite · Review findings: **43** (`11-R1..R43`) + 5 design (`11-D1..D5`) — **38 execute**, 2 conditional, 3 waive · Tests: 6 proposed (5 pytest, 1 vitest) · FUs: 6 proposed, 4 existing advanced.
- One-line: the security posture and the mutation gate are exactly as the audit left them, Basic mode is the solid default the reconciliation asked for — but AI mode has three confirm actions that crash on a dropped column, a data tool that `NameError`s, and eleven "See it" buttons pointing at retired routes; the help page and the in-prompt app guide have drifted a full redesign behind the code, and the fix for both is to generate them from the registry rather than hand-maintain them.

### Feedback coverage — `# DORA BOT` (L452–460)

| # | Feedback bullet | Where it lives now | State |
|---|---|---|---|
| DB1 | Some text doesn't change size with the user's font setting | `themeService` drives the root font-size (`--dora-base-font-size`) so rem/em text in the chat scales; FU-360 moved the check to DORA_VERIFY | 🟡 confirm in browser |
| DB2 | Basic/AI chip squished/small | Chip → `DoraModeSlider` (FU-360 #3); still 24 px tall → FU-663 / 11-D3 | ➗ |
| DB3 | Slider, AI side disabled if unavailable, per-user preference, slanted thick knob, one-time pulse glow, colourful vs dull | Skewed glowing knob, per-user `llm_enabled`, disabled-but-actionable state, dull Basic / bright AI ✅; **one-shot pulse on flip not built** → 11-D4 | ➗ |
| DB4 | Animations flash on hover since DS4 | `.is-entering` one-shot class (FU-360.4); verify item | 🟡 confirm in browser |
| DB5 | "Hi I'm Dora" bubble once, per user | `dora.helpHintDismissed.<user_id>` + 9 s auto-hide | ✅ done |
| DB6 | Turn the bot off completely | `User.show_assistant` → `MainLayout` `v-if` | ✅ done |
| DB7 | Call it D.O.R.A. | Header + tooltip + About page | ✅ done |

`# HELP` (L444–450) is cross-cutting and lands in chunk 20's coverage table; `docs/02_feedback/COVERAGE_GAPS.md` — no flips needed.
