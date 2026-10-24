# Hand-rolled vs libraries — consolidated verdicts

**Assembled 2026-10-23** from each chunk's §C9 table (PLAN §3.3 / §7 DoD step 5, ex-FU-510). Verdicts: **keep** (hand-rolled is right-sized), **replace** (a library wins — each becomes a per-swap follow-up at plan close), **wrap** (keep the surface, swap the engine). "Keep" is a legitimate verdict and is the majority: the app's hand-rolled pieces are mostly thin, token-aware wrappers the libraries would re-wrap.

## Replace / wrap verdicts (the ones that spawn work)

| Chunk | Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|---|
| 03 | `attachment_access` raw Core | ORM bypass | the mapped entity | **replace** (03-R37) | S | Same engine; just use the repository. |
| 04 | `useWakeLock` | Screen Wake Lock | `@vueuse/core useWakeLock` | **replace-candidate** | S | VueUse's version does the same (request/release/visibility re-acquire). Only two callers; swap if `@vueuse/core` is already a dependency, else keep (not worth a dep for 100 lines). |
| 06 | `allLocationOptions` tree walk (L1610–1621) | path labels | `helpers/locationDisplay.ts` / 05-R25 `locationStore.pathOptions` | **replace** | S | Same walk as `CreateStockItemDialog` / `PutAwayDialog`; 05-R25 is the one home. |
| 14 | `q-select` ×4 in the wizard | timezone, group, location pickers | `BaseSelect` | **replace** | S | FU-675's migration list +4. |
| 17 | `useWakeLock` | Wake Lock wrapper | `@vueuse/core` `useWakeLock` | **replace-candidate, low priority** | S | VueUse's version does the same incl. visibility re-acquire; swap only if VueUse is adopted elsewhere (chunk 20 decides). |
| 19 | `get_version._semver_tuple` | 8 lines | `packaging.version` | **replace** | S | `packaging` is already a transitive dep; `Version("0.10.0") > Version("0.7.0")` is right where the naive tuple also is, but pre-release handling (`v0.8.0-rc.1`, which `release.yml` explicitly allows) is wrong in the hand version. |

## Every verdict

| Chunk | Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|---|
| 01 | `_parse_recipe_from_text.py` (1,201 lines of regex heuristics) | paste-text recipe parser | `recipe-scrapers` (needs HTML + network, which FU-104/199 ruled out), `ingredient-parser-nlp` | **keep** | — | Operating on pasted plain text is the legal posture; corpus tests pin it. |
| 01 | `import_recipe_from_content.py` RapidFuzz `extractOne` | ingredient→pantry name match | already a library | **keep** | — | — |
| 01 | `nutrition/suggestions.py` token-recall scorer | item→food name match | RapidFuzz `token_set_ratio` | **keep** | — | Explainability (R-019) is the stated reason; threshold calibration documented. |
| 01 | `nutrition/lookup.py` `urlopen` + retry | OFF/USDA HTTP | `requests` (already a dependency: `requests_cache` in requirements) | **wrap-thin-adapter** | S | One `http_get_json(url, ua, timeout)` in `infrastructure/` shared with `dataset_import._download`; keeps retry policy in one place. **execute**. |
| 01 | `dataset_import.py` daemon thread + in-memory state | background import | APScheduler job / RQ | **keep** | — | Same shape as Piper voice download; a queue is anti-creep. |
| 01 | `pool.bump_pool` raw `text()` UPDATE … RETURNING | atomic floor-at-zero | ORM `update().returning()` | **keep** | — | Portability note documented; ORM form would need the same dialect split for bytes binding. |
| 01 | `recipeApiService.encodeFilterQueryString` | query-string build | `URLSearchParams` (used) vs `queryStringBuilder.createQueryString` | **wrap** | S | Fold the repeated-param encoding into `queryStringBuilder` so there is one encoder (Chunk 20 decides the shape). |
| 01 | `useDragDropList` in `RecipeStructuredMethod` | DnD | vuedraggable (`recipeStepImageEditorTypes.ts:13` comment still mentions it) | **keep** (R-022) | — | Fix the stale comment at execution. |
| 02 | `reconcile.py` raw-SQL cursor pagination + latest-receipt `NOT EXISTS` | keyset paging | SQLAlchemy Core `select()` with window functions | **keep** (as refactored by 02-R9) | — | SQLite < 3.25 has no window functions; the comment says so. |
| 02 | `reconcile_consumed_meals.py` connection-level sweep | daily job body | — | **keep** | — | Decoupled transaction is the point. |
| 02 | `build_week.select_recipes` greedy ranker + `random.Random` sampling | week generator | an optimiser (OR-tools) | **keep** | — | Anti-creep; fixture-tested. |
| 02 | `weekDates.ts` (`shiftDays`, `mondayOf`, `parseLocalIso`) | date arithmetic | `date-fns` / `dayjs` | **keep** | — | Six small pure functions with a spec; a date library would be the app's only one. |
| 02 | `useMealPlanner` touch swipe (`onTouchStart/End`, 60px threshold) | gesture | Quasar `TouchSwipe` directive (already in the framework) | **wrap** | S | `v-touch-swipe.vertical` replaces 10 lines and gains velocity handling; execute with 02-R19. |
| 02 | `MealPlanCalendar` roving-tabindex grid | a11y grid | — | **keep** | — | Correct and measured. |
| 03 | `useDragDropList` whole-row DnD (R-022) | pointer drag-reorder | `vuedraggable` / SortableJS | **keep** | — | Already the app-wide shared affordance (ADR-018); touch uses arrows by design. |
| 03 | `useLineSections` bucketing | grouping + ordering | lodash `groupBy` | **keep** | — | Pure, spec'd, carries domain rules (Unsorted bucket, availability). |
| 03 | `trim_to_budget` tier classifier | rules engine | — | **keep** | — | Five explicit tiers with constants; a rules library would obscure it. |
| 03 | `attachment_access` raw Core | ORM bypass | the mapped entity | **replace** (03-R37) | S | Same engine; just use the repository. |
| 03 | `budget.period_bounds` | week/month windows | `dateutil.relativedelta` | **keep** | — | Two branches; R-021 handled at the caller. |
| 03 | `QuickAddSheet` / `LogPriceSheet` search + rank | client filter | fuse.js | **keep** | — | `includes()` over ≤ a few hundred names; ranking is the point, not fuzziness. |
| 03 | `useListState` module cache | nav-state persistence | pinia + `sessionStorage` | **keep** | — | Deliberately reset-on-reload (A8 §3). |
| 04 | `useVoiceInput` Web Speech wrapper | STT | `vue-use-speech-recognition` / `@vueuse/core useSpeechRecognition` | **keep** | — | VueUse lacks the defer-restart (FU-723) and continuous-restart handling; ours is 270 lines with the fixes. |
| 04 | `useSpeechOutput` two-engine TTS | TTS | `@vueuse/core useSpeechSynthesis` | **keep** | — | Piper path + fallback + supersede token is the product. |
| 04 | `useWakeLock` | Screen Wake Lock | `@vueuse/core useWakeLock` | **replace-candidate** | S | VueUse's version does the same (request/release/visibility re-acquire). Only two callers; swap if `@vueuse/core` is already a dependency, else keep (not worth a dep for 100 lines). |
| 04 | timer `setInterval` countdown | timer | `@vueuse/core useIntervalFn` + `useTimestamp` | **keep (rewrite per 04-R8)** | — | Deadline arithmetic is the fix, not a library. |
| 04 | `playTimerFinishTone` oscillator | chime | a bundled WAV | **keep** | — | WebAudio sidesteps the `media-src` and autoplay issues a file would reintroduce. |
| 04 | `cookSteps` flattener | tree → list | — | **keep** | — | Pure; needs a spec (§D). |
| 05 | `useStockFilters` client filter+sort over the hydrated collection | in-memory filtering | server-side query params (`parse_query_options` already supports `filter=`/`sort=`) | **keep (for now)** | — | FU-667 owns the question; at ≤ 500 items client-side is the right call and the deep-link chips depend on it. |
| 05 | `q-virtual-scroll` + fixed row metric | virtualisation | — | **keep** | — | Correct use of the framework. |
| 05 | `useDragDropList` (not used here), `v-touch-hold` | gestures | — | **keep** | — | Quasar directive. |
| 05 | `cadence.py` band resolver | rules | — | **keep** | — | Pure, tested. |
| 05 | `queue_ranking.sort_key` tuple sort | ranking | — | **keep** | — | Deterministic, tested. |
| 05 | `sweep._latest_activity_by_item` two aggregates | event dating | an `engagement_events` table | **keep** | — | Documented trade: derive, don't store. |
| 05 | `locationStore.breadcrumb` rebuilds parent/name maps per call | tree walk | memoised maps | **wrap** | S | Build the two maps once per tree load (computed); called per row. |
| 06 | `PriceHistoryChart.vue` inline SVG | charting | ECharts (removed, FU-833) | **keep** | — | Deliberate; a11y text alternative only possible as SVG. |
| 06 | `useBuyVerdict` Map cache | per-item cache | Pinia / TanStack Query | **keep** | — | Documented rationale; `primeBuyVerdicts` handles bulk. |
| 06 | `relativeTime.ts` | relative time | `Intl.RelativeTimeFormat` / date-fns | **wrap** | S | A 20-line formatter is fine, but it should respect the install locale (R-056) — route through `useDateFormat`'s locale when it gains relative output. |
| 06 | `_trimmed_mean`, `statistics.median/pstdev` | stats | numpy | **keep** | — | Stdlib. |
| 06 | `q-date` in the expiry dialog | date picker | — | **keep** | — | Framework. |
| 06 | `allLocationOptions` tree walk (L1610–1621) | path labels | `helpers/locationDisplay.ts` / 05-R25 `locationStore.pathOptions` | **replace** | S | Same walk as `CreateStockItemDialog` / `PutAwayDialog`; 05-R25 is the one home. |
| 06 | `DoraTabs` | tabs | `q-tabs` | **keep** | — | Owner-chosen indicator. |
| 06 | `NutritionFoodPicker` search token | race guard | AbortController | **keep** | — | Correct and small. |
| 07 | `compute_belief` | hand-rolled depletion model | a forecasting lib | **keep** | — | Coarse-by-design (Charter P2); a library would add precision the product refuses. |
| 07 | `mean_gap_days` | arithmetic | `statistics.fmean` over diffs | **keep** | — | The sorting/zero-gap rule is the point. |
| 07 | module caches (`usePantryBeliefs`, `usePlannedDemand`) | cache | Pinia store / TanStack Query | **wrap** (07-R6) | S | One factory, not a dependency. |
| 07 | `SURFACE_FLAGS` string map | config | enum | **keep** | — | Closed set, R-010 carve-out documented. |
| 08 | SVG donut + ring (`PantryDonutCard`, `DoraScoreCard`) | charts | ECharts (removed, FU-833) | **keep** | — | `stroke-dasharray` on r=15.915 is the idiom; a11y labels present. |
| 08 | `useDragDropList` + tap up/down | reorder | SortableJS / vuedraggable | **keep** | — | Native DnD with a tap fallback is the C13 mandate. |
| 08 | `zoneColClasses` parity | layout | CSS grid `auto-fit` | **keep** | — | Order is dynamic and persisted; CSS can't widen "the last of an odd run". Tested. |
| 08 | `dashboardMessages` pools + `epochDay` | rotation | — | **keep** | — | Deterministic, gated, tested. |
| 08 | three module caches | cache | one factory (07-R6) | **wrap** | S | 08-R10. |
| 08 | `parseLayout` JSON narrowing | validation | zod | **keep** | — | Six lines; a schema lib for one field is creep. |
| 09 | `pywebpush` wrapper (`push_sender.py`) | web push | — | **keep** | — | Already a library; dry-run mode is the right local story. |
| 09 | `push-sw.js` hand-written SW | service worker | Workbox | **keep** | — | Push-only, 90 lines, coexists with the PWA SW; Workbox adds nothing here. |
| 09 | APScheduler `BackgroundScheduler` in-process | scheduling | Celery / cron | **keep** | — | Single-worker constraint documented; externalising is the SaaS tail. |
| 09 | Derived alerts (no stored alert rows) + interaction ledger | event model | a notifications table | **keep** | — | The proposal's central decision; it is what makes "one rule" possible. |
| 09 | `_select_for_display` fairness | ranking | — | **keep** | — | Pure, tested (FU-593). |
| 09 | `urlBase64ToUint8Array` | base64url | a lib | **keep** | — | 8 lines, the canonical snippet. |
| 10 | Surface | Hand-rolled | Verdict |
| 10 | `PriceHistoryChart.vue` (566 lines, SVG, crosshair, legend, baseline) | Yes | **keep** — already the one chart for three callers (FU-833), spec-pinned; a chart library would bring 100 KB for one SVG. Touch support is FU-705. |
| 10 | `TrendSparkline.vue` | Yes (40 lines) | **keep** — but read tokens via `var()` in `style`, not `getComputedStyle` (10-R36). |
| 10 | `deals_digest.format_money` | Yes (flat symbol table) | **keep** — documented; one email's worth of prices. Lift to `infrastructure/money.py` (10-R41). |
| 10 | `CustomProductDialog.splitSize` regex | Yes | **keep** — tiny; validate against `UNIT_TABLE` (10-R8). |
| 10 | `StoreLogo` hash-swatch | Yes | **keep** — deterministic, zero logos shipped by design. |
| 11 | Surface | Hand-rolled | Verdict |
| 11 | `doraIntents.ts` rule engine (1,422 lines) | Yes | **keep** — decided; it is the default experience and the offline fallback. |
| 11 | Client `tryConvert` parser (logic mirrors server `convert_measurement`; data shared via codegen) | Yes | **keep** — Basic/offline path; the data is already single-sourced. Add the substitution table to the same codegen (11-R12). |
| 11 | `DoraMascot` frame controller, typewriter, mood hold | Yes | **keep** (extract the typewriter, 11-R30). |
| 11 | `with_lead_in` WAV rebuild, `voice_provision` streaming download | Yes | **keep** — small, correct, dependency-free (`requests` already present). |
| 11 | LLM clients (`infrastructure/llm/*`) | Yes (HTTP) | **keep** — four thin clients beat four SDKs for a self-hosted app; revisit if streaming lands. |
| 12 | Surface | Hand-rolled | Verdict |
| 12 | Kitchen-memory column track (CSS bars) | Yes | **keep** — review §4.6 chose no chart library; integers as columns, `role="img"` label. |
| 12 | `ProportionBar` (spend composition) | Yes (shared) | **keep** — one implementation with the shopping list. |
| 12 | `PriceHistoryChart` drill-in | Shared | **keep** (chunk 10 verdict). |
| 12 | Range/bucket maths | Yes | **keep**, consolidated in `_ranges.py` (12-R24/10-R15). |
| 13 | `DoraSegmented.vue` | radiogroup segmented control | `BaseSegmented` (q-btn-toggle) | **merge** into one component (FU-848) | M / low | Dora's wraps + scrolls + has radio semantics; make Base the thin wrapper or retire Base. Decide in FU-848, execute at Stage 2 of chunk 20. |
| 13 | `SettingsMobileNav.vue` | tab strip + chips | `q-tabs`/`q-route-tab` | **keep** | – | 44 px, badge, group→first-leaf semantics; q-tabs would need the same custom chips. |
| 13 | `EncryptionKeyBanner.generateFernetKey` | 32 random bytes → url-safe b64 | none needed | **keep** | – | 6 lines, correct. |
| 13 | `AuditLogSettings.exportCsv` | CSV escape + blob download | `papaparse` / `quasar exportFile` | **wrap** — use Quasar's `exportFile` for the download half | S / low | Keep the 8-line escaper. |
| 13 | `AdminSystemRegionSettings` preview + choices | Intl-based preview, static choice lists | — | **keep** | – | Plain Intl, no round-trip. |
| 13 | `StockLocationsSettings` expansion in localStorage | persisted set | `useStorage` (VueUse — not a dep) | **keep** | – | R-026 carve-out documented. |
| 14 | `OnboardingConfetti.vue` | 40 CSS-animated spans, deterministic | `canvas-confetti` | **keep** | – | 70 lines, reduced-motion aware, no dep. |
| 14 | `OnboardingLoop.vue` ring | SVG circle + positioned buttons | d3 / anime.js | **keep** | – | One `pathLength` trick; no library earns its weight. |
| 14 | `OnboardingStepRail.vue` | dots rail | `q-stepper` | **keep** | – | Non-linear, two sections; q-stepper is linear by design. |
| 14 | `OnboardingPickPanel.vue` chips | role=checkbox buttons | `q-chip selectable` | **keep** | – | Caption + removable variants; q-chip can't carry both cleanly. |
| 14 | Wizard draft in `localStorage` | hand JSON round-trip | VueUse `useStorage` (not a dep) | **keep** | – | Debounce it (14-R26). |
| 14 | `q-select` ×4 in the wizard | timezone, group, location pickers | `BaseSelect` | **replace** | S | FU-675's migration list +4. |
| 15 | `auth_helpers.rate_limit` | in-memory sliding window | `Flask-Limiter` | **keep** (single-instance posture, A.6) | – | Add `ProxyFix` (15-R1); revisit at Phase-4 scaling with a shared store. |
| 15 | `csrf.py` double-submit | hand-rolled | `Flask-WTF` CSRF | **keep** | – | 100 lines, tested, matches the SPA's cookie-echo model; Flask-WTF assumes forms. |
| 15 | `auth_helpers` token plumbing | SHA-256 + `AuthToken` table | `itsdangerous` signed tokens | **keep** | – | Server-side revocation (single-use, sibling revoke) needs the table anyway. |
| 15 | `axiosHttpClient` retry/backoff | hand-rolled | `axios-retry` | **keep** | – | Boot-probe-specific ceilings; 40 lines. |
| 15 | `AuthShell` blobs/mascot | CSS | – | **keep** | – | FU-797 mitigation in place. |
| 15 | Password policy deny-list | 60 bundled words | HIBP k-anonymity API | **keep** | – | Offline self-host (R-005); documented. |
| 16 | `ingestion_auth.extract_bearer_token` + `find_ingestion_source` | 30-line bearer parse + SHA-256 match | `flask-httpauth` `HTTPTokenAuth` | **keep** | — | One scheme, one table; the library adds a decorator we'd still wrap in `authenticate_ingestion_request`. |
| 16 | `IdempotencyKey` table + TTL | 40 lines | none worth it | **keep** | — | Fix 16-R2/R3 instead. |
| 16 | Payload validation | pydantic `extra="forbid"` | — | already library | — | — |
| 16 | `copyToClipboard` | Quasar util | — | already library | — | — |
| 16 | Rate limiting on the bearer lane | none | `flask-limiter` | **keep (none)** | — | 256-bit keys; a limiter would need the same `ProxyFix` fix as 15-R1 first. |
| 17 | `useNetworkStatus` | 261-line singleton poller + backoff | `@vueuse/core` `useNetwork`/`useOnline` | **keep** | — | VueUse only wraps `navigator.onLine`; the `/health` probe, backoff and the forced Retry are the value. |
| 17 | `usePwaLifecycle` | install prompt + `controllerchange` | `vite-plugin-pwa`'s `useRegisterSW` | **keep** | — | Quasar owns the build; the composable is 148 lines. |
| 17 | `useWakeLock` | Wake Lock wrapper | `@vueuse/core` `useWakeLock` | **replace-candidate, low priority** | S | VueUse's version does the same incl. visibility re-acquire; swap only if VueUse is adopted elsewhere (chunk 20 decides). |
| 17 | GenerateSW runtime caching | config | InjectManifest hand-written SW | **keep GenerateSW** | — | FU-724's conclusion; 17-R1 adds `importScripts` for push. |
| 17 | `backendUrl.ts` | Preferences/localStorage URL store | — | keep | — | — |
| 17 | `keyboardInset.ts` | visualViewport insets | — | keep | — | 36 lines, one listener. |
| 18 | Chunked resumable upload (`uploads.py` + `useChunkedUpload`) | 380 lines both sides | tus / flask-tus, Uppy | **keep** | — | Admin-only, two callers, 8 MB chunks with resume-by-offset; a protocol library adds a client bundle and a server dep for no new capability. |
| 18 | Streaming JSON inspect | `ijson` | — | already library | — | — |
| 18 | Spreadsheet parsing | `openpyxl` + stdlib `csv` | pandas | **keep** | — | pandas would be the heaviest dep in the app for one importer. |
| 18 | Restore FK resolution | hand-rolled maps in `restore_shared.py` | — | **keep** | — | Reflection-driven (`_resolve_fk_target` reads SQLAlchemy FKs); the hand maps are the *policy* (hard/soft/required), not the plumbing. Fix the stale entries (18-R1). |
| 18 | `_coerce_to_date` | 4 strptime formats | `dateutil.parser` | **keep + locale order** (18-R12) | — | `dateutil` guesses; the install knows. |
| 18 | Client CSV escaping | 15 lines | papaparse | **keep, centralise** (18-R8) | — | — |
| 19 | `configuration_manager.py` (env → JSON → profile) | 410-line hand layering | `pydantic-settings` | **keep, shrink** | — | After 19-R13/D2 it is ~200 lines of env readers with dir side-effects; pydantic-settings would add a dependency to replace `os.environ.get`. Not worth it. |
| 19 | `profile.py` production gate | 60 lines | — | keep | — | — |
| 19 | `logging_setup.py` | stdlib handlers | `structlog` / `loguru` | **keep** | — | Request-id contextvar filter is 15 lines; structured JSON logging isn't asked for. |
| 19 | APScheduler in-process | library | Celery / RQ / cron | **keep** | — | Single-worker contract documented thrice; externalising is the parked Path-A work. |
| 19 | `get_version._semver_tuple` | 8 lines | `packaging.version` | **replace** | S | `packaging` is already a transitive dep; `Version("0.10.0") > Version("0.7.0")` is right where the naive tuple also is, but pre-release handling (`v0.8.0-rc.1`, which `release.yml` explicitly allows) is wrong in the hand version. |
| 19 | `scripts/dev-restart.sh` | 99 lines | `flask --debug` reloader | keep | — | `is_reloader_enabled()` is deliberately False (double-boot + scheduler); the script is the honest workaround. |
| 19 | Docker healthcheck via nginx `/healthz` | — | hit `/api/health` | keep | — | Documented trade-off; 19-D3 would make `/api/health` a better target later. |
| 20 | `useMoney` / `useDateFormat` | `Intl.*` wrappers + one cache | `vue-i18n` `n()`/`d()` | **keep; remove vue-i18n** (20-R2) | S | The wrappers are 260 lines and already the authority; vue-i18n would re-wrap the same `Intl` calls. |
| 20 | `useShortcut` | 139-line registry with sequences | `@vueuse/core` `useMagicKeys` / `tinykeys` | **keep** | — | Sequences (`g s`), typing-target guard and the cheatsheet registry are the value; tinykeys would still need the registry. |
| 20 | `rollbackRegistry` | 26 lines | undo/redo libs | **keep** | — | It is not an undo stack; it reverts optimistic UI on crash. |
| 20 | `AppSkeleton` | 71 lines | `q-skeleton` | **keep** | — | Quasar's is per-type and not token-aware; this one reads `--surface-sunken`/`--text-muted`. |
| 20 | Toast layer | Quasar Notify + 2 registered types | — | keep; **set one default position** (20-R10) | S | — |
| 20 | `apiErrorHandler` + `error_translation` | FU-099 shape | — | keep | — | Server-authoritative copy is the right call; 6 + tests pin it. |
| 20 | Theme tokens + `themeService` | hand-rolled CSS-var system, 14 themes | Quasar's `setCssVar` only / a design-token build | **keep** | — | The `themeService` already re-points Quasar's palette; a token build step would add tooling for no new capability. |
| 20 | `formatQuantity`/`scaleQuantity` | 150 lines | `Intl.NumberFormat` unit style / fraction libs | **keep; single-source the lists** (20-R3/R4) | S | Fraction glyph snapping and the DEC-3 spacing rule are domain, not formatting. |
| 20 | `useFormErrors` | 80 lines | VeeValidate / vuelidate | **keep** | — | Server-side validation is the authority (R-020); a client validator would duplicate it. |
| 20 | `submit_client_log` rate limit | in-memory sliding window | `flask-limiter` | **keep** (fix eviction, 20-R9) | — | Same single-worker constraint as 15-R1 notes. |

---

## Per-chunk tables (verbatim)

### Chunk 01 — Cookbook
*Source: [`CHUNK_01_cookbook.md`](../05_investigations/finalisation/CHUNK_01_cookbook.md)*

##### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `_parse_recipe_from_text.py` (1,201 lines of regex heuristics) | paste-text recipe parser | `recipe-scrapers` (needs HTML + network, which FU-104/199 ruled out), `ingredient-parser-nlp` | **keep** | — | Operating on pasted plain text is the legal posture; corpus tests pin it. |
| `import_recipe_from_content.py` RapidFuzz `extractOne` | ingredient→pantry name match | already a library | **keep** | — | — |
| `nutrition/suggestions.py` token-recall scorer | item→food name match | RapidFuzz `token_set_ratio` | **keep** | — | Explainability (R-019) is the stated reason; threshold calibration documented. |
| `nutrition/lookup.py` `urlopen` + retry | OFF/USDA HTTP | `requests` (already a dependency: `requests_cache` in requirements) | **wrap-thin-adapter** | S | One `http_get_json(url, ua, timeout)` in `infrastructure/` shared with `dataset_import._download`; keeps retry policy in one place. **execute**. |
| `dataset_import.py` daemon thread + in-memory state | background import | APScheduler job / RQ | **keep** | — | Same shape as Piper voice download; a queue is anti-creep. |
| `pool.bump_pool` raw `text()` UPDATE … RETURNING | atomic floor-at-zero | ORM `update().returning()` | **keep** | — | Portability note documented; ORM form would need the same dialect split for bytes binding. |
| `recipeApiService.encodeFilterQueryString` | query-string build | `URLSearchParams` (used) vs `queryStringBuilder.createQueryString` | **wrap** | S | Fold the repeated-param encoding into `queryStringBuilder` so there is one encoder (Chunk 20 decides the shape). |
| `useDragDropList` in `RecipeStructuredMethod` | DnD | vuedraggable (`recipeStepImageEditorTypes.ts:13` comment still mentions it) | **keep** (R-022) | — | Fix the stale comment at execution. |

### Chunk 02 — Meal Plans
*Source: [`CHUNK_02_meal_plans.md`](../05_investigations/finalisation/CHUNK_02_meal_plans.md)*

##### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `reconcile.py` raw-SQL cursor pagination + latest-receipt `NOT EXISTS` | keyset paging | SQLAlchemy Core `select()` with window functions | **keep** (as refactored by 02-R9) | — | SQLite < 3.25 has no window functions; the comment says so. |
| `reconcile_consumed_meals.py` connection-level sweep | daily job body | — | **keep** | — | Decoupled transaction is the point. |
| `build_week.select_recipes` greedy ranker + `random.Random` sampling | week generator | an optimiser (OR-tools) | **keep** | — | Anti-creep; fixture-tested. |
| `weekDates.ts` (`shiftDays`, `mondayOf`, `parseLocalIso`) | date arithmetic | `date-fns` / `dayjs` | **keep** | — | Six small pure functions with a spec; a date library would be the app's only one. |
| `useMealPlanner` touch swipe (`onTouchStart/End`, 60px threshold) | gesture | Quasar `TouchSwipe` directive (already in the framework) | **wrap** | S | `v-touch-swipe.vertical` replaces 10 lines and gains velocity handling; execute with 02-R19. |
| `MealPlanCalendar` roving-tabindex grid | a11y grid | — | **keep** | — | Correct and measured. |

### Chunk 03 — Shopping Lists
*Source: [`CHUNK_03_shopping_lists.md`](../05_investigations/finalisation/CHUNK_03_shopping_lists.md)*

##### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `useDragDropList` whole-row DnD (R-022) | pointer drag-reorder | `vuedraggable` / SortableJS | **keep** | — | Already the app-wide shared affordance (ADR-018); touch uses arrows by design. |
| `useLineSections` bucketing | grouping + ordering | lodash `groupBy` | **keep** | — | Pure, spec'd, carries domain rules (Unsorted bucket, availability). |
| `trim_to_budget` tier classifier | rules engine | — | **keep** | — | Five explicit tiers with constants; a rules library would obscure it. |
| `attachment_access` raw Core | ORM bypass | the mapped entity | **replace** (03-R37) | S | Same engine; just use the repository. |
| `budget.period_bounds` | week/month windows | `dateutil.relativedelta` | **keep** | — | Two branches; R-021 handled at the caller. |
| `QuickAddSheet` / `LogPriceSheet` search + rank | client filter | fuse.js | **keep** | — | `includes()` over ≤ a few hundred names; ranking is the point, not fuzziness. |
| `useListState` module cache | nav-state persistence | pinia + `sessionStorage` | **keep** | — | Deliberately reset-on-reload (A8 §3). |

### Chunk 04 — Cook Mode
*Source: [`CHUNK_04_cook_mode.md`](../05_investigations/finalisation/CHUNK_04_cook_mode.md)*

##### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `useVoiceInput` Web Speech wrapper | STT | `vue-use-speech-recognition` / `@vueuse/core useSpeechRecognition` | **keep** | — | VueUse lacks the defer-restart (FU-723) and continuous-restart handling; ours is 270 lines with the fixes. |
| `useSpeechOutput` two-engine TTS | TTS | `@vueuse/core useSpeechSynthesis` | **keep** | — | Piper path + fallback + supersede token is the product. |
| `useWakeLock` | Screen Wake Lock | `@vueuse/core useWakeLock` | **replace-candidate** | S | VueUse's version does the same (request/release/visibility re-acquire). Only two callers; swap if `@vueuse/core` is already a dependency, else keep (not worth a dep for 100 lines). |
| timer `setInterval` countdown | timer | `@vueuse/core useIntervalFn` + `useTimestamp` | **keep (rewrite per 04-R8)** | — | Deadline arithmetic is the fix, not a library. |
| `playTimerFinishTone` oscillator | chime | a bundled WAV | **keep** | — | WebAudio sidesteps the `media-src` and autoplay issues a file would reintroduce. |
| `cookSteps` flattener | tree → list | — | **keep** | — | Pure; needs a spec (§D). |

### Chunk 05 — Stock Overview + Stocktake
*Source: [`CHUNK_05_stock_overview_stocktake.md`](../05_investigations/finalisation/CHUNK_05_stock_overview_stocktake.md)*

##### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `useStockFilters` client filter+sort over the hydrated collection | in-memory filtering | server-side query params (`parse_query_options` already supports `filter=`/`sort=`) | **keep (for now)** | — | FU-667 owns the question; at ≤ 500 items client-side is the right call and the deep-link chips depend on it. |
| `q-virtual-scroll` + fixed row metric | virtualisation | — | **keep** | — | Correct use of the framework. |
| `useDragDropList` (not used here), `v-touch-hold` | gestures | — | **keep** | — | Quasar directive. |
| `cadence.py` band resolver | rules | — | **keep** | — | Pure, tested. |
| `queue_ranking.sort_key` tuple sort | ranking | — | **keep** | — | Deterministic, tested. |
| `sweep._latest_activity_by_item` two aggregates | event dating | an `engagement_events` table | **keep** | — | Documented trade: derive, don't store. |
| `locationStore.breadcrumb` rebuilds parent/name maps per call | tree walk | memoised maps | **wrap** | S | Build the two maps once per tree load (computed); called per row. |

### Chunk 06 — Stock-Item Detail
*Source: [`CHUNK_06_stock_item_detail.md`](../05_investigations/finalisation/CHUNK_06_stock_item_detail.md)*

##### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `PriceHistoryChart.vue` inline SVG | charting | ECharts (removed, FU-833) | **keep** | — | Deliberate; a11y text alternative only possible as SVG. |
| `useBuyVerdict` Map cache | per-item cache | Pinia / TanStack Query | **keep** | — | Documented rationale; `primeBuyVerdicts` handles bulk. |
| `relativeTime.ts` | relative time | `Intl.RelativeTimeFormat` / date-fns | **wrap** | S | A 20-line formatter is fine, but it should respect the install locale (R-056) — route through `useDateFormat`'s locale when it gains relative output. |
| `_trimmed_mean`, `statistics.median/pstdev` | stats | numpy | **keep** | — | Stdlib. |
| `q-date` in the expiry dialog | date picker | — | **keep** | — | Framework. |
| `allLocationOptions` tree walk (L1610–1621) | path labels | `helpers/locationDisplay.ts` / 05-R25 `locationStore.pathOptions` | **replace** | S | Same walk as `CreateStockItemDialog` / `PutAwayDialog`; 05-R25 is the one home. |
| `DoraTabs` | tabs | `q-tabs` | **keep** | — | Owner-chosen indicator. |
| `NutritionFoodPicker` search token | race guard | AbortController | **keep** | — | Correct and small. |

### Chunk 07 — Zero-Input Pantry (P8-07)
*Source: [`CHUNK_07_zero_input_pantry.md`](../05_investigations/finalisation/CHUNK_07_zero_input_pantry.md)*

##### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `compute_belief` | hand-rolled depletion model | a forecasting lib | **keep** | — | Coarse-by-design (Charter P2); a library would add precision the product refuses. |
| `mean_gap_days` | arithmetic | `statistics.fmean` over diffs | **keep** | — | The sorting/zero-gap rule is the point. |
| module caches (`usePantryBeliefs`, `usePlannedDemand`) | cache | Pinia store / TanStack Query | **wrap** (07-R6) | S | One factory, not a dependency. |
| `SURFACE_FLAGS` string map | config | enum | **keep** | — | Closed set, R-010 carve-out documented. |

### Chunk 08 — Dashboard
*Source: [`CHUNK_08_dashboard.md`](../05_investigations/finalisation/CHUNK_08_dashboard.md)*

##### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| SVG donut + ring (`PantryDonutCard`, `DoraScoreCard`) | charts | ECharts (removed, FU-833) | **keep** | — | `stroke-dasharray` on r=15.915 is the idiom; a11y labels present. |
| `useDragDropList` + tap up/down | reorder | SortableJS / vuedraggable | **keep** | — | Native DnD with a tap fallback is the C13 mandate. |
| `zoneColClasses` parity | layout | CSS grid `auto-fit` | **keep** | — | Order is dynamic and persisted; CSS can't widen "the last of an odd run". Tested. |
| `dashboardMessages` pools + `epochDay` | rotation | — | **keep** | — | Deterministic, gated, tested. |
| three module caches | cache | one factory (07-R6) | **wrap** | S | 08-R10. |
| `parseLayout` JSON narrowing | validation | zod | **keep** | — | Six lines; a schema lib for one field is creep. |

### Chunk 09 — Alerts + Suggestions
*Source: [`CHUNK_09_alerts_suggestions.md`](../05_investigations/finalisation/CHUNK_09_alerts_suggestions.md)*

##### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `pywebpush` wrapper (`push_sender.py`) | web push | — | **keep** | — | Already a library; dry-run mode is the right local story. |
| `push-sw.js` hand-written SW | service worker | Workbox | **keep** | — | Push-only, 90 lines, coexists with the PWA SW; Workbox adds nothing here. |
| APScheduler `BackgroundScheduler` in-process | scheduling | Celery / cron | **keep** | — | Single-worker constraint documented; externalising is the SaaS tail. |
| Derived alerts (no stored alert rows) + interaction ledger | event model | a notifications table | **keep** | — | The proposal's central decision; it is what makes "one rule" possible. |
| `_select_for_display` fairness | ranking | — | **keep** | — | Pure, tested (FU-593). |
| `urlBase64ToUint8Array` | base64url | a lib | **keep** | — | 8 lines, the canonical snippet. |

### Chunk 10 — Products / Price History / Deals
*Source: [`CHUNK_10_products_history_deals.md`](../05_investigations/finalisation/CHUNK_10_products_history_deals.md)*

##### C9. Hand-rolled-vs-library verdicts
| Surface | Hand-rolled | Verdict |
|---|---|---|
| `PriceHistoryChart.vue` (566 lines, SVG, crosshair, legend, baseline) | Yes | **keep** — already the one chart for three callers (FU-833), spec-pinned; a chart library would bring 100 KB for one SVG. Touch support is FU-705. |
| `TrendSparkline.vue` | Yes (40 lines) | **keep** — but read tokens via `var()` in `style`, not `getComputedStyle` (10-R36). |
| `deals_digest.format_money` | Yes (flat symbol table) | **keep** — documented; one email's worth of prices. Lift to `infrastructure/money.py` (10-R41). |
| `CustomProductDialog.splitSize` regex | Yes | **keep** — tiny; validate against `UNIT_TABLE` (10-R8). |
| `StoreLogo` hash-swatch | Yes | **keep** — deterministic, zero logos shipped by design. |

### Chunk 11 — Assistant (Dora)
*Source: [`CHUNK_11_assistant.md`](../05_investigations/finalisation/CHUNK_11_assistant.md)*

##### C9. Hand-rolled-vs-library verdicts
| Surface | Hand-rolled | Verdict |
|---|---|---|
| `doraIntents.ts` rule engine (1,422 lines) | Yes | **keep** — decided; it is the default experience and the offline fallback. |
| Client `tryConvert` parser (logic mirrors server `convert_measurement`; data shared via codegen) | Yes | **keep** — Basic/offline path; the data is already single-sourced. Add the substitution table to the same codegen (11-R12). |
| `DoraMascot` frame controller, typewriter, mood hold | Yes | **keep** (extract the typewriter, 11-R30). |
| `with_lead_in` WAV rebuild, `voice_provision` streaming download | Yes | **keep** — small, correct, dependency-free (`requests` already present). |
| LLM clients (`infrastructure/llm/*`) | Yes (HTTP) | **keep** — four thin clients beat four SDKs for a self-hosted app; revisit if streaming lands. |

### Chunk 12 — Reports / Memory (P8-09), Waste, Budget
*Source: [`CHUNK_12_reports_memory.md`](../05_investigations/finalisation/CHUNK_12_reports_memory.md)*

##### C9. Hand-rolled-vs-library verdicts
| Surface | Hand-rolled | Verdict |
|---|---|---|
| Kitchen-memory column track (CSS bars) | Yes | **keep** — review §4.6 chose no chart library; integers as columns, `role="img"` label. |
| `ProportionBar` (spend composition) | Yes (shared) | **keep** — one implementation with the shopping list. |
| `PriceHistoryChart` drill-in | Shared | **keep** (chunk 10 verdict). |
| Range/bucket maths | Yes | **keep**, consolidated in `_ranges.py` (12-R24/10-R15). |

### Chunk 13 — Settings shell
*Source: [`CHUNK_13_settings_shell.md`](../05_investigations/finalisation/CHUNK_13_settings_shell.md)*

##### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `DoraSegmented.vue` | radiogroup segmented control | `BaseSegmented` (q-btn-toggle) | **merge** into one component (FU-848) | M / low | Dora's wraps + scrolls + has radio semantics; make Base the thin wrapper or retire Base. Decide in FU-848, execute at Stage 2 of chunk 20. |
| `SettingsMobileNav.vue` | tab strip + chips | `q-tabs`/`q-route-tab` | **keep** | – | 44 px, badge, group→first-leaf semantics; q-tabs would need the same custom chips. |
| `EncryptionKeyBanner.generateFernetKey` | 32 random bytes → url-safe b64 | none needed | **keep** | – | 6 lines, correct. |
| `AuditLogSettings.exportCsv` | CSV escape + blob download | `papaparse` / `quasar exportFile` | **wrap** — use Quasar's `exportFile` for the download half | S / low | Keep the 8-line escaper. |
| `AdminSystemRegionSettings` preview + choices | Intl-based preview, static choice lists | — | **keep** | – | Plain Intl, no round-trip. |
| `StockLocationsSettings` expansion in localStorage | persisted set | `useStorage` (VueUse — not a dep) | **keep** | – | R-026 carve-out documented. |

### Chunk 14 — Onboarding
*Source: [`CHUNK_14_onboarding.md`](../05_investigations/finalisation/CHUNK_14_onboarding.md)*

##### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `OnboardingConfetti.vue` | 40 CSS-animated spans, deterministic | `canvas-confetti` | **keep** | – | 70 lines, reduced-motion aware, no dep. |
| `OnboardingLoop.vue` ring | SVG circle + positioned buttons | d3 / anime.js | **keep** | – | One `pathLength` trick; no library earns its weight. |
| `OnboardingStepRail.vue` | dots rail | `q-stepper` | **keep** | – | Non-linear, two sections; q-stepper is linear by design. |
| `OnboardingPickPanel.vue` chips | role=checkbox buttons | `q-chip selectable` | **keep** | – | Caption + removable variants; q-chip can't carry both cleanly. |
| Wizard draft in `localStorage` | hand JSON round-trip | VueUse `useStorage` (not a dep) | **keep** | – | Debounce it (14-R26). |
| `q-select` ×4 in the wizard | timezone, group, location pickers | `BaseSelect` | **replace** | S | FU-675's migration list +4. |

### Chunk 15 — Auth shell
*Source: [`CHUNK_15_auth_shell.md`](../05_investigations/finalisation/CHUNK_15_auth_shell.md)*

##### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `auth_helpers.rate_limit` | in-memory sliding window | `Flask-Limiter` | **keep** (single-instance posture, A.6) | – | Add `ProxyFix` (15-R1); revisit at Phase-4 scaling with a shared store. |
| `csrf.py` double-submit | hand-rolled | `Flask-WTF` CSRF | **keep** | – | 100 lines, tested, matches the SPA's cookie-echo model; Flask-WTF assumes forms. |
| `auth_helpers` token plumbing | SHA-256 + `AuthToken` table | `itsdangerous` signed tokens | **keep** | – | Server-side revocation (single-use, sibling revoke) needs the table anyway. |
| `axiosHttpClient` retry/backoff | hand-rolled | `axios-retry` | **keep** | – | Boot-probe-specific ceilings; 40 lines. |
| `AuthShell` blobs/mascot | CSS | – | **keep** | – | FU-797 mitigation in place. |
| Password policy deny-list | 60 bundled words | HIBP k-anonymity API | **keep** | – | Offline self-host (R-005); documented. |

### Chunk 16 — Ingestion API + companion seam
*Source: [`CHUNK_16_ingestion_api.md`](../05_investigations/finalisation/CHUNK_16_ingestion_api.md)*

##### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `ingestion_auth.extract_bearer_token` + `find_ingestion_source` | 30-line bearer parse + SHA-256 match | `flask-httpauth` `HTTPTokenAuth` | **keep** | — | One scheme, one table; the library adds a decorator we'd still wrap in `authenticate_ingestion_request`. |
| `IdempotencyKey` table + TTL | 40 lines | none worth it | **keep** | — | Fix 16-R2/R3 instead. |
| Payload validation | pydantic `extra="forbid"` | — | already library | — | — |
| `copyToClipboard` | Quasar util | — | already library | — | — |
| Rate limiting on the bearer lane | none | `flask-limiter` | **keep (none)** | — | 256-bit keys; a limiter would need the same `ProxyFix` fix as 15-R1 first. |

### Chunk 17 — Offline / PWA / native
*Source: [`CHUNK_17_offline_pwa_native.md`](../05_investigations/finalisation/CHUNK_17_offline_pwa_native.md)*

##### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `useNetworkStatus` | 261-line singleton poller + backoff | `@vueuse/core` `useNetwork`/`useOnline` | **keep** | — | VueUse only wraps `navigator.onLine`; the `/health` probe, backoff and the forced Retry are the value. |
| `usePwaLifecycle` | install prompt + `controllerchange` | `vite-plugin-pwa`'s `useRegisterSW` | **keep** | — | Quasar owns the build; the composable is 148 lines. |
| `useWakeLock` | Wake Lock wrapper | `@vueuse/core` `useWakeLock` | **replace-candidate, low priority** | S | VueUse's version does the same incl. visibility re-acquire; swap only if VueUse is adopted elsewhere (chunk 20 decides). |
| GenerateSW runtime caching | config | InjectManifest hand-written SW | **keep GenerateSW** | — | FU-724's conclusion; 17-R1 adds `importScripts` for push. |
| `backendUrl.ts` | Preferences/localStorage URL store | — | keep | — | — |
| `keyboardInset.ts` | visualViewport insets | — | keep | — | 36 lines, one listener. |

### Chunk 18 — Backup & restore + Import
*Source: [`CHUNK_18_backup_restore_import.md`](../05_investigations/finalisation/CHUNK_18_backup_restore_import.md)*

##### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| Chunked resumable upload (`uploads.py` + `useChunkedUpload`) | 380 lines both sides | tus / flask-tus, Uppy | **keep** | — | Admin-only, two callers, 8 MB chunks with resume-by-offset; a protocol library adds a client bundle and a server dep for no new capability. |
| Streaming JSON inspect | `ijson` | — | already library | — | — |
| Spreadsheet parsing | `openpyxl` + stdlib `csv` | pandas | **keep** | — | pandas would be the heaviest dep in the app for one importer. |
| Restore FK resolution | hand-rolled maps in `restore_shared.py` | — | **keep** | — | Reflection-driven (`_resolve_fk_target` reads SQLAlchemy FKs); the hand maps are the *policy* (hard/soft/required), not the plumbing. Fix the stale entries (18-R1). |
| `_coerce_to_date` | 4 strptime formats | `dateutil.parser` | **keep + locale order** (18-R12) | — | `dateutil` guesses; the install knows. |
| Client CSV escaping | 15 lines | papaparse | **keep, centralise** (18-R8) | — | — |

### Chunk 19 — Ops / self-host
*Source: [`CHUNK_19_ops_self_host.md`](../05_investigations/finalisation/CHUNK_19_ops_self_host.md)*

##### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `configuration_manager.py` (env → JSON → profile) | 410-line hand layering | `pydantic-settings` | **keep, shrink** | — | After 19-R13/D2 it is ~200 lines of env readers with dir side-effects; pydantic-settings would add a dependency to replace `os.environ.get`. Not worth it. |
| `profile.py` production gate | 60 lines | — | keep | — | — |
| `logging_setup.py` | stdlib handlers | `structlog` / `loguru` | **keep** | — | Request-id contextvar filter is 15 lines; structured JSON logging isn't asked for. |
| APScheduler in-process | library | Celery / RQ / cron | **keep** | — | Single-worker contract documented thrice; externalising is the parked Path-A work. |
| `get_version._semver_tuple` | 8 lines | `packaging.version` | **replace** | S | `packaging` is already a transitive dep; `Version("0.10.0") > Version("0.7.0")` is right where the naive tuple also is, but pre-release handling (`v0.8.0-rc.1`, which `release.yml` explicitly allows) is wrong in the hand version. |
| `scripts/dev-restart.sh` | 99 lines | `flask --debug` reloader | keep | — | `is_reloader_enabled()` is deliberately False (double-boot + scheduler); the script is the honest workaround. |
| Docker healthcheck via nginx `/healthz` | — | hit `/api/health` | keep | — | Documented trade-off; 19-D3 would make `/api/health` a better target later. |

### Chunk 20 — Cross-cutting concerns
*Source: [`CHUNK_20_cross_cutting.md`](../05_investigations/finalisation/CHUNK_20_cross_cutting.md)*

##### C9. Hand-rolled-vs-library verdicts (the plan §3.3 list for this chunk)
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `useMoney` / `useDateFormat` | `Intl.*` wrappers + one cache | `vue-i18n` `n()`/`d()` | **keep; remove vue-i18n** (20-R2) | S | The wrappers are 260 lines and already the authority; vue-i18n would re-wrap the same `Intl` calls. |
| `useShortcut` | 139-line registry with sequences | `@vueuse/core` `useMagicKeys` / `tinykeys` | **keep** | — | Sequences (`g s`), typing-target guard and the cheatsheet registry are the value; tinykeys would still need the registry. |
| `rollbackRegistry` | 26 lines | undo/redo libs | **keep** | — | It is not an undo stack; it reverts optimistic UI on crash. |
| `AppSkeleton` | 71 lines | `q-skeleton` | **keep** | — | Quasar's is per-type and not token-aware; this one reads `--surface-sunken`/`--text-muted`. |
| Toast layer | Quasar Notify + 2 registered types | — | keep; **set one default position** (20-R10) | S | — |
| `apiErrorHandler` + `error_translation` | FU-099 shape | — | keep | — | Server-authoritative copy is the right call; 6 + tests pin it. |
| Theme tokens + `themeService` | hand-rolled CSS-var system, 14 themes | Quasar's `setCssVar` only / a design-token build | **keep** | — | The `themeService` already re-points Quasar's palette; a token build step would add tooling for no new capability. |
| `formatQuantity`/`scaleQuantity` | 150 lines | `Intl.NumberFormat` unit style / fraction libs | **keep; single-source the lists** (20-R3/R4) | S | Fraction glyph snapping and the DEC-3 spacing rule are domain, not formatting. |
| `useFormErrors` | 80 lines | VeeValidate / vuelidate | **keep** | — | Server-side validation is the authority (R-020); a client validator would duplicate it. |
| `submit_client_log` rate limit | in-memory sliding window | `flask-limiter` | **keep** (fix eviction, 20-R9) | — | Same single-worker constraint as 15-R1 notes. |
