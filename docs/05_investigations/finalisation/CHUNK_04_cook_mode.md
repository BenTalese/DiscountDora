# Chunk 04 — Cook Mode

**Analysed:** 2026-10-23 · **Analyst session:** finalisation overnight run (single session, no sub-agents)
**Scope (from PLAN §4):** `/cookbook/:id/cook` — step / sub-step / section / hint rendering, structured vs free-text vs photo faces, per-step ingredient + tool highlight, headcount scaling, timers, Sous Chef (speech out) + hands-free commands (speech in), wake lock, cook-session substitutes, finish flow (levels, cart, extra servings), `POST /recipes/<id>/cook`, the pool primitive.
**Boundaries:** the cook-mode *guard* dialog + `cookModeGuard.ts` → Chunk 1 (01-R1); `adjust_recipe_meals` + pool UI on the recipe page → Chunk 1; `StockLevelPicker` / `NumberStepper` internals → Chunks 5/20; `VoiceSettings` / `VoicePicker` / `/api/tts` → Chunk 13; `useSpeechOutput` + `useVoiceInput` are reviewed here as cook mode's primary consumer (DoraChat is the other → Chunk 11 ticks); CSP middleware → Chunk 19 (one-line fix proposed here).

## 0. Reading list + files walked

**Planning docs consulted:** `PROPOSAL_RECIPE_IMAGE_STEPS.md`, `IMPL_PLAN_RECIPE_IMPORTER.md` §Chunk 4, cookbook revision §1.9, feedback `# COOK MODE` (L317–337), open FUs: FU-853, 765, 763, 728, 722, 670, 628, 629, 788, 793, 754, 764, 654.

**Files walked (every file opened):**

| File | Lines | Role |
|---|---|---|
| `web_app/src/pages/RecipeCookMode.vue` | 2042 | the page |
| `web_app/src/components/recipes/{CookStepProgress,RecipeCookModeImageView,CookNotesSection}.vue` | 547 | progress, photo face, notes band |
| `web_app/src/composables/{useCookingPolicy,useWakeLock,useSpeechOutput,useVoiceInput}.ts` | 870 | policy, wake lock, voice out/in |
| `web_app/src/helpers/{scaleQuantity,substituteRatio}.ts` | 121 | DEC-4 rounding, ratio caption |
| `web_app/src/utils/audioUnlock.ts` (exports) | — | silent-WAV primer |
| `dora_api/features/recipes/{cook_recipe,adjust_recipe_meals,pool}.py` | 246 | cook endpoint, pool twin, pool primitive |
| `dora_api/infrastructure/middleware.py:147–180` | — | CSP (FU-853) |
| Tests inventoried: `tests/test_recipe_pool.py` (pure helper only), e2e cook pins in `test_reconcile_*`, `test_stock_item_history_feeds.py`, `test_delete_integrity.py`, `test_reports_router.py`, `test_recipe_router.py`; vitest `scaleQuantity.spec.ts`, `cookModeGuard.spec.ts` (Chunk 1), `voicePicker.spec.ts` (Chunk 13). **No** spec exists for the step flattener, the timer, or the voice dispatcher — all three live inline in the page. | | |

## A. Full Systems Test — Cook Mode

### A1. Preconditions
- Three recipes: **free-text** (numbered lines, one with "simmer 20 minutes"), **structured** (sections, one sub-step, per-step ingredients + tools, one `timer_minutes`, a hint, notes), **photo** (`steps_mode='image'`, ≥ 3 images). (FU-754: the dense seed lacks structured/image fixtures — seed them first.)
- One ingredient low/out **with** a recorded substitute carrying a ratio + note (FU-793: the dense seed lacks this — add).
- Household headcount set (`/settings/admin/system/cooking`); run twice: cook-style **Fresh** and **Batch** (the "Extra servings" stepper and the "You saved N meals" toast exist only in Batch).
- Sous Chef: once with Piper configured, once browser-voice only, once on Firefox (no `SpeechRecognition` → no mic button).

### A2. Golden path
Persona: **Dense user**, tablet in the kitchen, then phone.
1. Recipe → **Cook** → header: back · name (ellipsised) · Sous Chef (labelled on desktop, icon on phone) · mic (if supported) · `(?)` commands popover (only once Sous Chef or the mic is on) · "Cooking for N" pill seeded from the headcount (or `?for=N` from the planner).
2. Step card: section chip, Sub-step chip, step text at display size, hint band; progress badge + segmented track (≤ 14 steps; segments are jump buttons) → Previous / Repeat / Next one row on a phone.
3. Change "Cooking for" → ingredient quantities rescale (countables to whole numbers ≥ 1, continuous to ½ ⅓ ¼ … or one decimal).
4. Ingredients grouped by recipe section, else by base location, "No location" last; the current step's ingredients and tools highlighted, neighbours dimmed (tools only); optional rows dimmed; notes italic behind a glyph.
5. Low/out ingredient shows the swap button → picker lists substitutes with ratio + note → pick → row shows the substitute chip, "instead of X", the hint line, and an undo.
6. Timer band: declared minutes ("from this step's wording" when sniffed) → Start → MM:SS + bar emptying → Pause / Reset → at zero: toast + chime + "Timer finished" (Sous Chef on).
7. Sous Chef on → step 1 is read on arrival, each step on change, Repeat re-reads; mic on → "next" / "back" / "repeat" / "ingredients" / "tools" / "start timer" / "stop" / "exit" work hands-free; "stop" silences Dora first, pauses the timer second, never exits.
8. All steps panel: numbered circles (shared with the recipe page), current row highlighted, tap to jump.
9. Last step → **Finish** → "Finished cooking?": one row per linked ingredient (substitute replaces the original) with the level swatch picker preselected at the current level + level name + cart button; Batch: "Extra servings for later" stepper at 0 → **Done** → changed levels written as `cook` consumption events, pool bumped, `last_made_on` stamped, celebratory toast, back to the recipe page.
10. Photo recipe: one photo at a time with the same Previous/Next pair, zoom dialog (fit ↔ 2.5× pan, paging inside), last Next = Finish → same dialog.
11. Screen stays awake for the whole cook (where the Wake Lock API exists).

### A3. Edge cases
- `/cookbook/A/cook` → `/cookbook/B/cook` without leaving → **04-R1** (FU-765): recipe A stays on screen until fixed.
- Structured mode with an empty `steps[]` → falls back to the free-text split (honest, documented).
- Free-text step "1 hour 30 minutes" → sniff reads **30** (minutes matched first) — note, not a bug worth fixing (04-R9).
- Unlinked ingredient → plain raw text, no swap, excluded from the finish rows.
- Finish with nothing changed → no writes, no consumption events, pool bump 0 → `204`.
- Timer running → Next → timer **resets** (04-D2: product gap — long timers don't survive a step change).
- Phone backgrounded mid-timer → the 1 s interval is throttled → the countdown runs slow (04-R8).
- Space / arrows while the finish dialog or swap picker is open → still step the recipe underneath (04-R7).
- iOS / WKWebView: the silent-WAV primer is **blocked by CSP** (04-R2) → first Piper utterance after an await may be muted.
- Firefox: no mic button (R-078 copy in Settings explains); browser voice falls back to Piper when configured.
- Exit mid-sentence → narration stops (composable `onBeforeUnmount`); mic indicator clears.
- Reduced motion: progress segment transitions off.

### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (free-text recipe, no headcount → recipe servings) | ✓ | ✓ (Fresh style: no servings stepper) | ✓ (structured + voice + Batch) | ✓ (headcount / cook-style / Piper install) | ✓ (`cooked_by_user_id` on the event; voice prefs per user) | ✓ (Piper present in Docker/desktop) | – |

### A5. Load-bearing conditions
- **375px phone**: header two bands (headcount wraps), nav row three buttons at `md`, step text `text-h4` (FU-763 — owner's call), finish dialog rows one line.
- **Hands-free**: barge-in over narration (FU-723 defer-restart), "stop" semantics, timer chime after a long silence (autoplay gate — toast is load-bearing).
- **Themes × dark**: timer band (`dora-bg-sunken`), highlight tint + accent rule, progress badge `color-mix` washes, `text-color="white"` chips (04-R22).
- **Audio**: Piper vs browser voice vs none; CSP `media-src` (04-R2).
- **Wake lock**: Chromium / Safari 16.4+ / Firefox 126+; silent no-op elsewhere.

### A6. Release-gate rows
- Structured recipe with a sub-step, a declared timer and a swapped substitute: finish → the substitute's level changes (not the original's), a `cook` consumption event per changed row, pool +N (Batch), `last_made_on` = household today, Stock-item history shows "Used in <recipe>".
- Photo recipe end-to-end on a phone including Finish.
- Sous Chef + mic on Android Chrome: "next" heard while Dora is mid-sentence; narration not clipped at the start (FU-722 candidate fixes).
- Navigate between two cook routes without a reload → the second recipe renders (after 04-R1).

## B. Help content — Cook Mode

### B1. Current help audit
- `HelpPage.vue:451–454` *Cook mode*: "Open a recipe and hit Cook. Steps render one card at a time and ingredients show where each one lives (e.g. Pantry > Top shelf)." — stale: grouping is by **base** location (sub-areas collapse; "Top shelf" is exactly what it doesn't show) and sections win when the recipe has them; nothing about headcount, timers, Sous Chef, swaps, finish.
- `HelpPage.vue:397` *Substitutes* entry already covers "a swap made in cook mode is temporary" well — link, don't repeat.
- The in-page `(?)` **commands popover** is fine (it is a mid-cook reference, not help — owner 2026-09-03), but the *explanations* (what Sous Chef is, which browsers, why a timer might be silent) belong in HelpPage.
- `app_knowledge.py:24–27` says "Cook mode ends by asking how many meals were cooked; that count is added" — Batch-only now, and omits levels/consumption, swaps, voice, headcount.

### B2. Help entries

#### Cook mode
- **Group:** Cookbook (replace the existing *Cook mode* entry)
- **What it does:** One step at a time, at a size you can read from across the kitchen. Structured recipes show sections, sub-steps, hints and the ingredients and tools the current step needs (the rest dim); free-text recipes split on lines; photo recipes page through the pictures with zoom. Tap a segment of the progress bar or a row in "All steps" to jump.
- **When it fires / how to trigger it:** **Cook** on a recipe (Dora warns first if you're missing ingredients — see *Can I cook this?*). Keyboard: → / space next, ← previous, R repeat, Esc exit.
- **What it costs / might get wrong:** Which steps you see follows the recipe's chosen mode; a structured recipe with no steps falls back to its text.
- **Related:** Cooking for a different number · Sous Chef · Finishing a cook
- **Chip:** `RecipeCookMode.vue:52` beside the recipe name → `<HelpHint topic="Cook mode">` (icon-only; the header is already tight on a phone).
- **Source:** `RecipeCookMode.vue` `cookSteps`.

#### Cooking for a different number
- **Group:** Cookbook
- **What it does:** The "Cooking for" pill opens at your household headcount (or the servings the meal plan asked for) and rescales every quantity for this cook only — whole numbers for things you count (eggs, cloves, cans), kitchen fractions (½ ⅓ ¼) or one decimal for everything else. The saved recipe is never changed.
- **What controls it:** `/settings/admin/system/cooking` (headcount). A recipe with no servings can't be scaled.
- **Source:** `scaleQuantity.ts` (DEC-4), `useCookingPolicy`.

#### Sous Chef (Dora reads the steps)
- **Group:** Cookbook / Dora
- **What it does:** With Sous Chef on, Dora reads each step as you reach it and "Repeat" reads it again. She uses her own neural voice when it's installed on the server (works in every browser) and the device's voice otherwise. The setting is remembered per user.
- **What controls it:** The Sous Chef button; voice choice under `/settings/voice`.
- **What it costs / might get wrong:** On a phone, a step read *after* a long silence (a timer finishing) may be muted by the browser's autoplay rule — the toast still fires. If the start of a sentence is clipped on Android, see Settings → Voice.
- **Related:** Which browsers can Dora speak in? (Dora itself)
- **Source:** `useSpeechOutput.ts`, FU-722/FU-629.

#### Hands-free commands
- **Group:** Cookbook / Dora
- **What it does:** Turn the mic on and say *next*, *back*, *repeat*, *ingredients*, *tools*, *start / pause / reset timer*, *stop* (quietens Dora, or pauses the timer) or *exit*. Unrecognised speech is ignored on purpose. The mic is independent of Sous Chef — you can listen without narration and vice versa.
- **What controls it:** The mic button, shown only where the browser supports speech recognition (Chrome, Edge, Safari; not Firefox).
- **What it costs / might get wrong:** The browser may pause listening after a long silence; Dora reopens it, waiting until she has finished talking so her own voice isn't clipped.
- **Source:** `useVoiceInput.ts`, `handleVoiceCommand`.

#### Step timers
- **Group:** Cookbook
- **What it does:** A structured step can carry its own timer; otherwise Dora reads a duration out of the step's wording and says so ("from this step's wording"). Start, pause, reset; the bar empties as time passes; at zero you get a toast, a chime and — with Sous Chef on — a spoken "Timer finished". The screen stays awake while you cook.
- **What it costs / might get wrong:** One timer at a time, and moving to another step resets it (02-D2 — under review). A chime after a long idle may be blocked by the browser; the toast is the signal to trust.
- **Source:** `sniffedTimerMinutes`, `timer_minutes`.

#### Swapping an ingredient for this cook
- **Group:** Cookbook
- **What it does:** When an ingredient is low or out, the swap button lists its recorded substitutes with their ratio and note; picking one shows it in the row with the hint, and the finish step adjusts the *substitute's* level. Temporary — the recipe is untouched.
- **Related:** Substitutes (Stock)
- **Source:** B8, `sessionSwaps`.

#### Finishing a cook
- **Group:** Cookbook
- **What it does:** "Finished cooking?" lists each ingredient with its current level preselected — change the ones you used up (or add them to a list from the cart beside each). Changed levels are recorded as cooking consumption, the recipe's "last made" moves to today, and in a Batch household you say how many extra servings you set aside for the pool.
- **What it costs / might get wrong:** Leaving a row alone changes nothing. Unlinked ingredients aren't listed. Finishing a photo recipe works the same way from its last Next.
- **Related:** Meals prepared (Cookbook) · Stock levels (Stock)
- **Source:** `confirmFinish`, `cook_recipe.py`, MAGIC F10.

### B3. DoraBot corpus delta
Replace `app_knowledge.py` L24–27's cook-mode sentences with:
```
  Cook mode shows one step at a time (sections, sub-steps, hints, per-step
  ingredient and tool highlights; photo recipes page through pictures),
  rescales quantities for the number you're cooking for, offers timers, can
  read steps aloud (Sous Chef) and take spoken commands, and lets you swap a
  low ingredient for a recorded substitute for that cook only. Finishing asks
  which ingredient levels changed, records them as cooking consumption, stamps
  the recipe as made today and, in a batch-cooking household, adds any spare
  servings to the recipe's pool.
```

## C. Senior review — Cook Mode

### C1. Bugs (verified or high-confidence latent)

- **04-R1** · **FU-765** (reproduced live twice) · `RecipeCookMode.vue:1766–1798` fetches in `onMounted` only; no watch on `route.params.id`. · **Exact change:** `async function loadRecipe(id)` (fetch + reset `currentStepIndex`, timer, `sessionSwaps`, `announcedFirstStep`); `watch(() => route.params.id, (id) => void loadRecipe(String(id)), { immediate: true })`; `onMounted` keeps the store warm-ups. · S · guard: drive A→B once · **execute (FU-765)**.
- **04-R2** · **FU-853**, re-diagnosed · the CSP (`middleware.py:164–172`) has no `media-src`, so `default-src 'self'` governs media. The timer chime is **already** a WebAudio oscillator (`playTimerFinishTone`, L1403) and is not affected — the FU's "data: WAV chime" description is stale. What *is* blocked is `audioUnlock.ts:21` `SILENT_WAV_DATA_URL` played via `new Audio(data:…)` — the iOS/WKWebView autoplay primer that `useSpeechOutput` and `VoicePicker.onPreview` rely on — hence the violation logged on every load. Piper's `blob:` playback is same-origin and passes `'self'`. · **Exact change:** add `"media-src 'self' blob: data:"` to `_DEFAULT_CSP` with a comment naming the primer; update FU-853's text. · S · guard: `tests/e2e/dora_api/test_security_headers*.py` if present (assert the directive) · **execute (FU-853)**.
- **04-R3** · R-003 layering · `exitCookMode` (L1597) and `onBeforeUnmount` (L1804) call `window.speechSynthesis?.cancel()` directly, bypassing `useSpeechOutput.cancel()` — the composable's own `onBeforeUnmount(cancel)` covers unmount, so Piper audio *does* stop, but `exitCookMode` → `router.push` leaves the Piper `<audio>` playing for the ~frame until unmount and the page holds a second opinion about how to silence Dora. · **Exact change:** `speechOut.cancel()` in both places; drop the raw calls. · S · **execute**.
- **04-R7** · bug · `handleKeydown` is a raw `window` listener (the only page in the app not on `useShortcut`); space/arrows fire while the finish dialog or swap picker is open (stepping the recipe underneath, re-opening Finish), and the keys don't appear in the `?` cheatsheet. · **Exact change:** register via `useShortcut([...], { scope: 'Cook mode' })` (space / arrowright → next, arrowleft → prev, r → repeat, escape → exit) and guard the handlers on `!finishDialogOpen.value && !swapPickerOpen.value`. · S · guard: drive once · **execute**.
- **04-R8** · bug · the countdown decrements by one per `setInterval` tick (L1363–1382); backgrounded tabs throttle intervals (Chrome: ≥ 1 s, then 1/min after 5 min; iOS suspends) so a 20-minute timer runs **slow** when the cook switches apps — the exact case a kitchen timer exists for. · **Exact change:** store `deadlineMs = Date.now() + remaining*1000` on start; each tick sets `remaining = max(0, ceil((deadline - now)/1000))`; re-sync on `visibilitychange`. Extract as `useCookTimer()` (04-R20 seam) so it is unit-testable with fake timers. · S · guard: new `useCookTimer.spec.ts` · **execute**.
- **04-R9** · note · `sniffedTimerMinutes` matches minutes before hours, so "1 hour 30 minutes" → 30. · **waive** (fallback only; declared timers are the mechanism).
- **04-R5** · UX bug · `confirmFinish` uses `Promise.allSettled` for level writes and never reports rejections — a failed level update is silently lost under a "You saved N meals" toast. · **Exact change:** count `rejected`; if > 0 toast `Could not update N level(s).` (negative) before the celebration. · S · **execute**.

### C2. Redundancy / DRY (R-001, R-003)

- **04-R10** · `cook_recipe.py:21–28` `_current_user_id` with the literal `"user_id"` — **FU-654** copy. · **execute (FU-654)**.
- **04-R11** · `levelNameFor` (page L1502) + `levelSequence`/`levelLabel` in `QuickAddSheet.vue:121–126` and `LogPriceSheet.vue:146–151` — three private "stock level id → name / sequence" lookups over `stockLevels.find`. · **Exact change:** `stockLevelStore` gains `byId` (Map), `nameOf(id)`, `sequenceOf(id)`; the three call sites use them. · S · guard: `shoppingListStore.spec`-style store spec (optional) · **execute**.
- **04-R12** · `stockItems.value.find(...)` per ingredient in `ingredientRows` (L1118) and again in `buildFinishRows` (L1521) — linear scans per render; the store has no `byId`. · **Exact change:** `stockItemStore.byId` computed Map; both read it (Chunk 1's `cookModeGuard.missingStockItemIds` benefits too). · S · **execute**.
- **04-R13** · the Previous/Next pair is built three times: page nav (L307–336, with Repeat, `navButtonSize`), `RecipeCookModeImageView` nav (L59–75, fixed `size="lg"` — so the photo face **didn't get the 09-03 phone fit**) and its zoom-dialog nav (L121–136). · **Exact change:** `components/recipes/CookNavRow.vue` (props `canPrev`, `isLast`, `showRepeat`, `repeatDisabled`, `size`; emits prev/repeat/next); three call sites. · S · **execute**.
- **04-R14** · `pool.bump_pool` UUID bind normalisation (L69–78) — the third copy folded by **01-R8** (`uuid_bind`). · **execute (01-R8)**.
- **04-R15** · `cook_recipe.py` and `adjust_recipe_meals.py` share the load-recipe → `bump_pool` → save shape; two small handlers, one shared primitive already — · **waive** (already DRY where it matters).

### C3. Dead code / unused fields / stale copy

- **04-R16** · `useSpeechOutput.lastEngine` — exported, zero readers since the 09-03 popover removal (the page comment L138–143 says "still carries it for whoever needs it next"). FU-722 (unconfirmed clipping) is the one investigation that might want it. · **Exact change:** keep until FU-722 is closed; add `// FU-722 diagnostic` to the export. · **waive (documented)**.
- **04-R17** · page epitaph comments: L930 ("the headcount nudge + its clamp live in NumberStepper now"), L1109–1111 (`hasStructuredSteps` removed), L1318–1321 (`markIngredientsUsedInStep` removed), L1766–1768 (`speechRecognitionAvailable` seeding) — history the worklog holds. · **Exact change:** delete. · S · **execute** (with 04-R20's extraction, since the lines move anyway).
- **04-R18** · HelpPage *Cook mode* entry and `app_knowledge` cook sentences stale (§B1). · **execute (Help track)**.
- **04-R19** · `cook_recipe.py:94–97` returns `204` for `meals_cooked == 0` and `200 {available_meals}` otherwise — two shapes for one endpoint; the client ignores the body (`recipeStore.cookAsync` refetches). · **Exact change:** always `ok({"available_meals": …})`. · S · guard: `test_recipe_router.py` cook case if it asserts 204 · **execute (conditional)**.

### C4. Componentisation opportunities (R-001)

- **04-R20** · `RecipeCookMode.vue` is 2,042 lines with five clean seams already labelled in the script: `useCookSteps(recipe)` (flattener + highlights, L1010–1226), `useCookTimer()` (L978–1426, incl. the tone), `useCookVoice(...)` (Sous Chef toggle + dispatcher, L933–1008 / L1619–1745), `CookIngredientsPanel.vue` (L352–489 + swap picker + `sessionSwaps`), `CookFinishDialog.vue` (L695–777 + `buildFinishRows`/`confirmFinish`). The page keeps route/load/header. · L · guard: vue-tsc + drive all three faces + the finish once; new specs for the flattener, the timer and the dispatcher (§D) · **FU** (same shape as FU-780; execute 04-R8 and 04-R7 as the first two extractions so the rest follows the pattern).
- **04-R21** · `playTimerFinishTone` (WebAudio beep) — only chime in the app; · **waive** (move to `utils/chime.ts` only if a second surface wants one).

### C5. Placement / standards (R-002, D-rules)

- **04-R22** · `text-color="white"` on the Sub-step chip (L222) and the swap chip (L409) → `--text-on-primary` / `--text-on-secondary` (FU-674 governs contrast). · S · **execute**.
- **04-R23** · literal type sizes: `CookStepProgress.vue:133 (0.6875rem), :140 (1.5rem), :147 (0.875rem), :248 (1.25rem)`, page `.cook-section__head { font-size: 1rem }` (L1829), `.all-steps-row--sub { padding-left: 32px }` (L1934) → `--font-size-*` / `--space-*` tokens (D-003 scale). · S · **execute**.
- **04-R24** · two focus-ring tokens in one surface: `CookNotesSection.vue:85` `--ring-focus` (a soft 35 % wash — defined in `themes.scss`) vs `CookStepProgress.vue:220` `--focus-ring` (full brand ink, `tokens.scss:153`). App-wide: 8 files use `--ring-focus`, the rest `--focus-ring`. Not a cook-mode bug but cook mode is where both meet. · **Exact change:** log a **FU** for FU-010/FU-224: pick one focus token (recommend `--focus-ring` for the outline, `--ring-focus` only for soft halos) and sweep. · **FU**.
- **04-R25** · `ease` literal after a motion token (`CookStepProgress.vue:187–189, 238`, page L1870) → `var(--motion-ease)` (D-010). · S · **execute** (with 02-R38's sweep).
- **04-R26** · `useVoiceInput.ts:2` imports `currentMoneyPolicy` from `useMoney` to read the install locale — a voice composable depending on the *money* composable because the locale rides on the money policy. Works, but the dependency direction is odd (R-003 says the locale is one install fact). · **Exact change:** export `currentLocale()` from a `useLocale`/`useRegional` seam (FU-043 Layer B owns this); `useMoney` and `useVoiceInput` both read it. · S · **execute** (if FU-043's regional seam exists at execution; else FU).
- **04-R27** · `pool.py:35` `from dora_api.app import db` + raw `text()` — documented R-005 carve-out (portable `UPDATE … RETURNING`, needed by the connection-level sweep). Keep; comment already names the rule. · **waive**.

### C6. Naming & idiom
- **04-R28** · `RecipeCookModeImageView` vs `CookStepProgress` / `CookNotesSection` — two naming schemes in one folder for cook-mode parts. · **Exact change:** rename to `CookImageView.vue` when 04-R13 touches it. · S · **execute**.

### C7. Efficiency
- 04-R12 above. `highlightedIngredientIds` text-match is per step change over ≤ 30 ingredients — fine.

### C8. Design-level findings — out of Stage-2 scope
- **04-D1** · **FU-728 (cook-mode half) answered:** cook mode is already its own composition — the "planning" phase is the recipe page, and the step/photo faces are modes *within* cooking, not lifecycle phases. No second composition is warranted; the R-001 extraction (04-R20) is size hygiene, not R-054. Record and close the cook-mode half of FU-728 (the stocktake half → Chunk 5).
- **04-D2** · Timers are per-step and reset on navigation (`nextStep`/`prevStep`/`goToStep` all `resetTimer()`). A 40-minute braise timer dies the moment the cook reads ahead. Owner decision: timers persist across steps (a small "running timers" strip) vs. the current single-step model. **FU**.
- **04-D3** · FU-763 (step text size on a phone) — owner's call, unchanged.
- **04-D4** · FU-670: expiring-ingredient chips absent in cook mode — the owner said stock noise doesn't belong mid-cook; the at-risk chip is arguably the one exception ("use this one first"). Leave with FU-670.

### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `useVoiceInput` Web Speech wrapper | STT | `vue-use-speech-recognition` / `@vueuse/core useSpeechRecognition` | **keep** | — | VueUse lacks the defer-restart (FU-723) and continuous-restart handling; ours is 270 lines with the fixes. |
| `useSpeechOutput` two-engine TTS | TTS | `@vueuse/core useSpeechSynthesis` | **keep** | — | Piper path + fallback + supersede token is the product. |
| `useWakeLock` | Screen Wake Lock | `@vueuse/core useWakeLock` | **replace-candidate** | S | VueUse's version does the same (request/release/visibility re-acquire). Only two callers; swap if `@vueuse/core` is already a dependency, else keep (not worth a dep for 100 lines). |
| timer `setInterval` countdown | timer | `@vueuse/core useIntervalFn` + `useTimestamp` | **keep (rewrite per 04-R8)** | — | Deadline arithmetic is the fix, not a library. |
| `playTimerFinishTone` oscillator | chime | a bundled WAV | **keep** | — | WebAudio sidesteps the `media-src` and autoplay issues a file would reintroduce. |
| `cookSteps` flattener | tree → list | — | **keep** | — | Pure; needs a spec (§D). |

### C10. Standards drift (R-0NN)
- **R-003** · 04-R3 (bypassing the speech composable), 04-R26 (locale via money) — fix.
- **R-001** · 04-R13, 04-R20 — fix / FU.
- **R-002 / D-003 / D-010** · 04-R22, 04-R23, 04-R25 — fix.
- **R-019** · 04-R10 — fix (FU-654).
- **R-039** · no `$q.dialog` on this surface (all `BaseDialog`) — clean.
- **D-004** · voice cluster 44px, nav buttons 44px, progress segments 44px hit area, notes head 44px on coarse pointers — clean.
- **Keyboard layer** · 04-R7 — the page is the one surface outside `useShortcut`.
- **FU-764** (undefined tokens) · `--surface-card` fixed in place (L1846); `--space-sm/xs` fixed; `--ring-focus` exists — no new undefined tokens found.

### C11. Ride-along signals for FU-010 / FU-224
- Two focus-ring tokens (04-R24) — app-wide inconsistency surfaced here.
- `CookStepProgress` badge/segments lean entirely on `color-mix(--brand-primary …)` washes (12 % / 20 % / 35 % / 45 % / 65 %) — check pesto dark + high-contrast.
- `.cook-row--dim { opacity: .55 }`, `.ingredient-row--optional { opacity: .65 }` — opacity dimming (D-002 floor), same class as 02/03.
- Swap chip `color="secondary"` + white ink — FU-621/FU-652 secondary shortlist.

## D. Test plan — Cook Mode

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `useCookTimer.spec.ts` (deadline-based remaining; pause/resume; fake timers advanced past a throttle) | vitest | **must-write-before-ship** | 04-R8 — the only way to pin "backgrounding doesn't slow the timer". |
| `cookSteps.spec.ts` (flattener: top/sub ordering, section inheritance, structured-with-empty-steps fallback, numbered-line stripping) | vitest | **must-write-before-ship** | 04-R20 first extraction — the step model is the surface's core and has never had a test. |
| `cookVoiceCommands.spec.ts` (dispatcher: "stop" precedence, "exit" vs "stop", timer verbs, ignored noise) | vitest | nice-to-have | 04-R20 — owner-specified semantics (2026-09-03) worth pinning. |
| `test__cook_recipe__zero_meals_stamps_last_made_only` + `__positive_meals_bumps_pool_and_writes_event` | pytest e2e | nice-to-have | 04-R19 — pins the response shape and the CookEvent rule. |
| `test__csp__has_media_src` | pytest e2e | nice-to-have | 04-R2 — one-line assertion on the header. |
| `stockLevelStore.spec.ts` (`nameOf`/`sequenceOf`) | vitest | nice-to-have | 04-R11. |

Not proposed: tests for `useSpeechOutput`/`useVoiceInput` (browser APIs; verify by driving on Android Chrome per FU-722/FU-723); Playwright.

## E. Proposed follow-ups (orchestrator allocates ids)

- type=follow-up · *Split `RecipeCookMode.vue` into `useCookSteps` / `useCookTimer` / `useCookVoice` + `CookIngredientsPanel` / `CookFinishDialog`* (04-R20) — plan recorded; bundle with FU-780 / 01-R36 / 02-D4 as the "big page splits" group.
- type=finding · *Timers reset on step change* (04-D2) — owner decision.
- type=finding · *Two focus-ring tokens (`--ring-focus` vs `--focus-ring`) across 8 + N files* (04-R24) — attach to FU-010/FU-224.
- type=finding · *FU-728 cook-mode half: no second composition needed* (04-D1) — record in FU-728 and narrow it to stocktake.
- Existing FUs this chunk executes against: **FU-765** (04-R1), **FU-853** (04-R2, re-diagnosed), **FU-654** (04-R10), **FU-754 / FU-793** (seed fixtures — needed for A1; execute as part of Stage 2 if the seed is touched).

## F. Summary for the register

- FST rows: 11 golden + 12 edge + 4 gate · Help entries: 7 (1 stale entry replaced; DoraBot sentences rewritten) · Review findings: 28 (execute 20 / FU 4 / waive 4) · Tests: 6 (must-write 2) · Bugs: 5 (stale recipe on route change [FU-765], CSP blocks the iOS audio primer [FU-853 re-diagnosed], background-throttled timer, global keydown leaks into dialogs, silent level-write failures)
- One-line: cook mode is the surface the owner polished hardest in September and it shows — D-004 everywhere, honest copy, one chokepoint per rule — but its 2,000-line page still owns a step flattener, a timer and a voice dispatcher with no tests between them, the timer is wall-clock-naive, and the long-standing FU-765 route-change bug is a 10-line watch away.
