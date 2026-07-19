# DORA_VERIFY triage & campaign tracker

**What this is:** the working plan for clearing the QA pile in `DORA_VERIFY.md`
(1,406 unchecked items as of 2026-07-16) without the owner hand-walking all of it.
Agreed approach (owner, 2026-07-16): **triage → agent-verified evidence reports per
surface → guided-walkthrough packs for eyeball items → device packs for hardware
items**. Playwright E2E conversion (the durable-tests option) is deliberately
deferred to a later session.

**How a verify session uses this doc:**
1. Pick the next ⚪ batch from the batch plan below (or the one the owner names).
2. Re-read the target sections in `DORA_VERIFY.md` (line refs here are a
   **2026-07-16 snapshot** — they drift as the file is edited; grep the heading).
3. Seed/contrive the data states, walk every **A** item in the running app,
   and record pass/fail + evidence in a report to the owner.
4. **V** items: stage + screenshot, hand to the owner as a walkthrough pack.
5. **H** items: leave for the matching device pack (Appendix A).
6. Fails → new `DORA_FOLLOWUPS.md` entries (type=finding). Passes → **delete
   the lines from DORA_VERIFY.md in the same session** (owner delegation
   2026-07-18, replacing the old "owner-deletable" marker convention; this doc
   + the worklog keep the evidence trail). Reword surviving neighbour bullets
   so they stand alone; failed/partial items stay.
7. Flip the batch's status here and log the unit in `DORA_WORKLOG.md`.

> **2026-07-18 sweep note:** every line previously marked "owner-deletable"
> (Batches 0/2/3 — ~85 checkboxes: SettingsFileDrop, BuyVerdictCard, Password
> policy, Runtime-URL L112, the six backend-pinned Stock fix sections,
> FU-507/508, stocktake settings dials + alert-threshold removal +
> "Needs check" behavioural bullets, the full stocktake-runner codified
> blocks, bulk-waste, auto-add, 3-band collapse) **has now been deleted from
> DORA_VERIFY.md**. Line refs in the progress notes below pre-date that sweep.

**Classification key:**
- **A** — agent-verifiable (browser/API/DB/CLI on this box, incl. viewport
  emulation, drag automation, typed barcode entry, DevTools-style checks).
- **V** — agent-stageable, human-eyeball verdict (theme readability, animation
  feel, copy tone). Agent stages + screenshots; owner judges.
- **H** — hardware/human-only (real Android/iPhone/Mac, camera, mic, audible
  audio, real inbox, physical print, product-scope decisions).

**Status key:** ⚪ not started · 🟡 in progress · ✅ verified + reported ·
➗ done with carve-outs · 🗑 stale — recommend delete (owner call).

---

## The numbers (2026-07-16 snapshot)

| Slice | Lines | Items | A | V | H | Stale-suspect |
|---|---|---|---|---|---|---|
| Top block (recent surfaces) | 11–129 | 80 | 65 | 0 | 15 | 1 |
| Cookbook & recipes + Cook mode | 130–372 | 191 | 182 | 4 | 5 | 8 |
| Meal plans + Shopping lists | 373–665 | 227 | 217 | 7 | 3 | 9 |
| Stock | 666–1012 | 245 | 234 | 11 | 0 | 8 |
| Dashboard + Alerts + Settings | 1013–1378 | 267 | 260 | 6 | 1 | 17 |
| Onboarding + Products + Build + Operator | 1379–1636 | 164 | 143 | 11 | 10 | 15 |
| Cross-cutting | 1637–1948 | 232 | 199 | 27 | 6 | 3 |
| **Total** | | **1,406** | **1,300 (92%)** | **66** | **40** | **61** |

Owner's realistic residual workload: read the evidence reports, walk ~66 eyeball
items from pre-staged screenshots/walkthroughs, run 2–3 device packs (~40 items,
of which 7 are blocked on having a Mac), and decide the 61 stale recommendations.

---

## Batch plan (verify sessions, in order)

Sized so one batch ≈ one session. Order: pilot first, then newest/highest-risk
surfaces, then the long tail, then env-gated batches.

| # | Batch | Sections (snapshot lines) | Items | Status |
|---|---|---|---|---|
| 0 | **Pilot** — Password policy + SettingsFileDrop + BuyVerdictCard + Runtime backend URL | 71–99, 111–115, 82–89 | 22 | ✅ **COMPLETE 07-17** (Password policy 8/8; SettingsFileDrop 5/5; BuyVerdictCard 6/6 — FU-572 found+fixed mid-walk; Runtime URL walked — L113 recovery clause FAILS → FU-574 open, remove-toast over-count → FU-573) |
| 1 | Top block remainder — Onboarding story, Dora bubble, Currency & locale, Stores logo, PWA-dev-checkable parts | 11–49, 63–70 | ~40 | ⚪ |
| 2 | Stock A — recent fixes + stocktake redesign (668–814) | 668–814 | ~120 | 🟡 (2026-07-17: FU-508+FU-507 codified green; 5 fix-pins confirmed backend-tested→delete; scan-mode→device-pack; **stocktake runner Chunk 2 fully codified — all 5 verbs + help + add-to-list green**; Chunk 3 settings dials + **"Needs check" Overview filter + alert-threshold removal codified green**; tail = non-admin banner + auto→runner cadence effect) |
| 3 | Stock B — remainder (816–1009) | 816–1009 | ~115 | ➗ (2026-07-17: **FU-226 waste section fully codified green** — `bulk-waste.spec.ts`, 6 tests; L830/831/833/834/835/836 owner-deletable. **Auto-add-on-low first slice codified** — `auto-add-on-low.spec.ts`, 2 tests: settings dial loads/saves/persists + `all`-mode Low-drop toast + `auto: low stock` chip; L843/844/847/849 owner-deletable; server-branching negatives → [[FU-577]]. 2026-07-18: **P8-05 buy-verdict section fully codified** — engine already unit-pinned; 3 new e2e tests (flag off/on, low-confidence silence, out-of-stock Buy walk) + new `useBuyVerdict.spec.ts` client-cache spec; L734–744 deleted, one Wait-badge visual stays; found [[FU-580]] (flag flip needs a reload). **History tab both sections codified** — new backend `test_stock_item_history_feeds.py` (7 tests: Bought/Cooked feed contracts) + new `history-tab.spec.ts` (4 tests: cap footer, mixed feed, meals badge, expiry-trail render); old L758–783 deleted, one colours/singular-footer visual stays. **FU-109 deep-link + no-dim codified** — new `recipe-deeplink.spec.ts` (4 tests), both sections deleted; found+fixed 2 real bugs (phantom chip on dead recipe id; empty-state Clear leaving `?recipe=`) + fixed FU-579's bulk-waste half (was hard-failing `quasar build`). **Stock pickers behavioural halves codified** — new `stock-pickers.spec.ts` (2 tests: detail Level round-trip + console-clean filter clear); section down to one dot-styling visual. **C-1b triaged** (pinned+stale deleted; compressed to walks + 2 codify-next candidates) and **Chunks 2/4 codified** — new `useStockItemActionsPushExpiry.spec.ts` (8 Vitest: FU-123 push matrix) + Chunk-2 stock.spec describe (panel persistence, retired-filter guard). **C-1b.4 codified** — new `detail-recipes-tab.spec.ts` (3 tests: favourite toggle, Add-all-to-list, substitutes Remove/no-Swap). **C-1b.3 codified** — new `detail-products-tab.spec.ts` (cheapest highlight, empty CTA); found [[FU-581]] (three surfaces route to the FU-186-retired `/product-search` → 404). Remaining: visual walks + viewport-gated bullets (Chunk 5, mobile panel, products-OFF half) + Offers sidecar line — **agent-verifiable work done 2026-07-18; flipped ➗, remainder is owner-walk only**) |
| 4 | Cookbook A — filters, free-text, importer, DnD (132–195) | 132–195 | ~53 | ⚪ |
| 5 | Cookbook B — chunk sections + image-steps (197–321) | 197–321 | ~120 | ⚪ |
| 6 | Cook mode (327–369) | 327–369 | ~36 | ⚪ |
| 7 | Meal plans (375–476) | 375–476 | ~83 | ⚪ |
| 8 | Shopping lists A — recent (482–563) | 482–563 | ~69 | ⚪ |
| 9 | Shopping lists B — cart button + P6-01 chunks (565–662) | 565–662 | ~75 | ⚪ |
| 10 | Dashboard (1015–1108) | 1015–1108 | ~75 | 🟡 (2026-07-18: **Draft-my-shop (FU-351) codified** — new backend `test_auto_generate_draft_shop.py` (no-phantom-list defer + explicit name) + new `dashboard-draft-shop.spec.ts` (happy path toast→navigate→chips; Cards-menu toggle); section down to empty-case/error/consumed walk bullets. Rest of batch untriaged) |
| 11 | Alerts (1114–1157) | 1114–1157 | ~34 | ⚪ |
| 12 | Settings A — data/admin pages (1163–1283) | 1163–1283 | ~86 | ⚪ |
| 13 | Settings B — account/assistant/misc (1285–1375) | 1285–1375 | ~72 | ⚪ |
| 14 | Onboarding (1381–1471, **after stale cleanup**) + Products (1477–1511) | 1381–1511 | ~66 | ⚪ |
| 15 | Cross-cutting A (1639–1780) | 1639–1780 | ~100 | ⚪ |
| 16 | Cross-cutting B (1782–1945) | 1782–1945 | ~95 | ⚪ |
| 17 | **Env-gated: built-PWA mode** — PWA install/offline (100–110), share-target dev-checkable parts, manifest checks | various | ~10 | ⚪ |
| 18 | **Env-gated: Docker/WSL** — gunicorn (1593), voice bundling (1554–1570), demo mode (1619), secure-cookies HTTPS leg (1632), companion round-trip (1616) | 1554–1633 | ~25 | ⚪ |
| 19 | **Env-gated: Postgres leg** — alembic-on-PG halves of every migration item (compose.dev PG; `DORA_TEST_DB=postgres`) | scattered | ~12 | ⚪ |
| 20 | **Operator migrations on populated DB** — FU-563/564/565 (1576–1591), Windows desktop build (1517–1528), fresh-install boots (1542–1552, 1613) | 1517–1614 | ~26 | ⚪ |

### Close-out rule — every batch, every check gets a disposition (2026-07-17)

The campaign's durable artifact is the **Playwright regression suite**
(`web_app/e2e/`, see its README), not the walk itself. On closing a batch,
classify each check:

1. **`verified-once → delete`** — one-time confirmations (copy, layout,
   subjective calls, migration ran). Verified live, owner deletes from
   DORA_VERIFY, no code.
2. **`codified → spec + delete`** — behaviour that could regress under
   future change (flows, gates, integration seams). Verify live FIRST, then
   pin it as a Playwright spec (or push it down to Vitest/backend tests when
   a browser isn't needed). The manual check is then deleted *permanently* —
   a UAT round re-verifies it by running `npm run test:e2e`.
3. **`env-gated → device pack`** — hardware/host-bound checks; stay manual.

Every real bug the campaign finds gets a pinned regression test where
feasible (FU-571/FU-572 are the reference shape). Keep the suite curated —
core journeys + bug pins, not a checkbox dump.

**Batch 0 retro-codified (2026-07-17):** password-policy (5 specs, FU-442 +
FU-568 pins), uploads/FileDrop (2 specs, FU-571 + FU-545 pins), buy-verdict
(4 specs, FU-454 + FU-572 pins), plus the pre-existing login/smoke layer
hardened (hash-mode routes now actually load; per-route title asserted; e2e
backend isolated to :5171 with the QA-fixture seed).
**Suite GREEN 2026-07-17: 19/19 (~2.6 min), Vitest 387/387, vue-tsc clean.**
Two spec-side fixes landed getting there: `/shopping-lists` returns a bare
summary array (not `{items}`), and a same-document hash-only `page.goto`
(dashboard → detail) doesn't reliably drive vue-router — engineer state via
`page.request` first, then do ONE full-document goto to the target route
(pattern now in buy-verdict.spec.ts). Watch item: the meal-plans smoke test
flaked once in a full run (networkidle timing), passed on both re-runs.

Notes:
- **FU-214** (open FU) rides on batch 14 — its product-surface browser-verify pass
  plus the 3 Product-History residuals folded in by FU-431 (2026-07-16).
- **FU-010 / FU-224** (theme + colour review FUs) collect signal from every
  V-pack walk — note anything relevant in reports.
- Batch 19/20 overlap heavily with automated migration tests (FU-536/549/563–565
  schema-match + from-empty chain); the residual manual value is the
  populated-DB / real-toolchain legs only.

---

## Pilot results — Password policy (FU-442), 2026-07-16

Walked live against `localhost:5174` (dev SPA) + `:5170` (backend). Test
accounts created: `qa-admin` (admin, via first-run setup page — which the DB's
zero-user state surfaced; bonus pre-exercise of FU-200), `qa-user-1`,
`qa-user-2`. **These live in the repo-root `dora.data.db`** (see the caveat
below).

| Check (snapshot line) | Verdict | Evidence |
|---|---|---|
| L91 8-char letters-only succeeds | ➗ **intent PASS, example stale** | `abcdefgh` → 422 **breach-list** rejection (it's a breached string — correct NIST behaviour, impossible example); `zxqvbnmk` (letters-only, non-breached) → 200, account created. No digit rule anywhere. Checklist needs a new example password. |
| L92 `passphrase please` succeeds | ✅ PASS | POST register → 200, account created. |
| L93 `abc123` rejected ≥8 | ✅ PASS | 422, `"Password must be at least 8 characters."` |
| L94 breach rejection, case-insensitive | ✅ PASS | `password123` → 422 breach message; `QWERTY123` → identical 422 (case-insensitive confirmed). UI renders it inline under the field + "Registration failed" banner (evidenced on the register form). |
| L95 reset-flow fineprint + no digit language | ✅ PASS (2026-07-17, post-FU-568 fix) | Fineprint restored on all four surfaces; rendered live on LoginPage register mode + ResetPasswordPage ("At least 8 characters — a passphrase works well."). "No letter-and-digit language" half already PASSED. Owner can delete L95. |
| L96 change-password validator ≥8 | ✅ PASS (2026-07-16, session 2) | Live on `/settings/account`: typed `abc` into New password → inline "At least 8 characters" under both new + confirm fields. |
| L97 pre-policy password still logs in | ✅ PASS (2026-07-16, session 2) | UI login as seed user `dora`/`dora` (4-char, pre-policy) → 200, session valid, admin. Set-time-only policy confirmed. |
| L98 no policy-loosening admin toggle | ✅ PASS (2026-07-16, session 2) | Walked the full settings tree in-app: personal pages (Account/Preferences/Notifications/Money/Voice/Nutrition/Assistant/About), kitchen-setup, and the complete Admin mode (Users; System ×12 incl. Features/Email/Push/Hosting; Data ×3; Audit log; API access) — no password-policy surface anywhere. Matches code grep. |

**Findings spun off:** FU-568 (fineprint regression), FU-569 (Windows console
logging spam), FU-570 (silent boot on stale-schema DB — the cause of the
dashboard 500s seen mid-pilot; *not* a fresh-install product bug).

**Environment caveat learned (now a standing rule, see Appendix D):** the
preview-launched backend used the repo-root SQLite `dora.data.db` — a July-10
`create_all` artifact with **no `alembic_version`** and a stale schema — while
shell-resolved config pointed at Postgres. Anything beyond the auth tables
500s on it. **Before batch 1: create a dedicated disposable verify DB**
(`alembic upgrade head` + FU-388 dev seed on a fresh file, pointed at via env),
and re-run the deferred L96–L98 there.

### Batch 0 continuation (2026-07-16, session 2) — dedicated DB stood up; SettingsFileDrop + BuyVerdictCard partials; FU-571 found

**Verify DB:** root `dora.data.db` rebuilt (old file backed up to session scratchpad):
`drop_all` + `create_all` + `seed_dev_data(bulk_stock_items=500)` → 1 user
(`dora`/`dora`, admin), 521 stock items. Dashboard renders clean (the pilot's
500s are gone — confirms FU-570 was schema drift, not product).

**SettingsFileDrop (FU-545), 3/5 verified + blocked tail:**
- L76 click-to-open: ✅ **complete** (tail closed 2026-07-17 post-FU-571 fix) —
  click forwarding proven earlier; filename+size display now verified live:
  pick → upload 200 → steady `file-drop--filled` showing "fu545_tail.csv 36 B".
- L77 keyboard: ✅ — hidden input is tab-reachable; `:focus-within` restyles the
  zone (bg tint). Enter/Space = native `<input type=file>` activation.
- L78 drag-and-drop: ✅ — dragover → `file-drop--dragging` (dashed→solid,
  tint); dragleave calms; drop feeds the same pick path (now 200s post-fix).
- L79 Remove-doesn't-reopen: ✅ (2026-07-17) — from steady filled state,
  Remove click → zone back to idle copy, instrumented `input.click()` counter
  stayed 0 (picker never reopened).
- L80 busy/disabled inert: ✅ (2026-07-17) — `--busy` caught live mid-upload;
  `input.disabled === true` during it; zone click during busy → 0 picker
  opens; settles to `--filled` with filename. **Section 5/5 complete — owner
  can delete DORA_VERIFY L76–L80.**
- **FU-571 found here** (chunked uploads always 403 — CSRF header missing from
  `useChunkedUpload`'s raw fetches; Import + Backup-restore broken in browser).

**BuyVerdictCard (FU-454), state engineered + API-verified:**
- Fixture created (survives in the verify DB): stock item **"QA Verdict
  Cheese"** (`b5f476ac-fb96-4e3f-8a5d-c0d0238ab394`), level Stocked, 3 priced
  lines on 3 done lists ("QA verdict shop 1–3", 90/60/30 days ago), 2 waste
  events (45/20 days) → waste rate 67%.
- `GET …/buy-verdict` → `verdict: skip, confidence: high, one_tap_action:
  {kind: mark_stocked, label: "Already stocked"}`, waste reason "You've wasted
  this 67% of the time". ✅ the mark_stocked *state* is real and reproducible.
- Overview row renders the **Skip** chip (seen live). The tap-the-button UI
  walk (L83–88) is **deferred to the Playwright runner** (below) — the card
  lives in the detail view, which this harness pane can't mount (no-paint
  limitation). For `remove_from_list`: add the fixture item to any open list
  and the same card flips (code path `_pick_action`, is_on_open_list).

### Batch 0 blocker fixes (2026-07-17, session 3) — FU-571/568/569 fixed + verified

- **FU-571 FIXED + verified:** `csrfHeader()` helper exported from
  `axiosHttpClient.ts`; swept into all raw-fetch mutating sites (chunked
  upload start/chunk/finish/abort, import inspect/commit, backup
  create/inspect/restore, 2× app-settings PATCH on the Backup page,
  `/client-logs`, `/tts`). Live proof: real `useChunkedUpload().upload()`
  (imported via Vite in-page) ran start→chunk→finish → 200 + upload_id;
  `/data/import/spreadsheet/inspect` on that upload → 200 with auto-mapping;
  header-less POST still 403s (FU-197 defence intact). **L79/L80 tail +
  Import/Backup batch-12 checks are unblocked.**
- **FU-568 FIXED + verified:** hint prop on the 4 auth surfaces; rendered live
  on LoginPage (register mode) + ResetPasswordPage. L95 flipped to PASS above.
- **FU-569 FIXED + verified:** `stdout.reconfigure(encoding='utf-8',
  errors='replace')` in `configure_logging`; probe under forced
  `PYTHONIOENCODING=cp1252` emits `→ é ✓` cleanly, no logging traceback.

### Batch 0 completion (2026-07-17, session 3 cont.) — BuyVerdictCard L87–92 + Runtime URL L112–114 walked; FU-572 found+fixed; FU-573/574 opened

**Harness note first:** the full Appendix-D recipe (rAF stub + zero-duration CSS
+ **in-SPA hash nav, stub applied in-session, no reload**) mounts the stock
**detail page and its BuyVerdictCard** after all — the earlier "detail never
mounts" result was pre-recipe. The Playwright runner is still the right call for
screenshot/V-pack batches, but tap-walks are doable in-pane with this recipe.

**BuyVerdictCard one-tap actions (FU-454) — section COMPLETE:**
- L87 mark_stocked ✅ both surfaces — Stock Overview popover + Stock Item
  Detail card: tap → level set, positive toast, fresh verdict on
  re-render. **Found + fixed FU-572 mid-walk:** the detail card kept the stale
  one-tap until remount (invalidate never refetched) and the cart quick-add
  seams never invalidated — post-fix, the card updates **in place** (verified:
  remove_from_list → "Already stocked" live, no remount).
- L88 list-line mark_stocked ✅ — tap on ShoppingListDetail line badge →
  "Marked as Stocked." (new data-driven copy), level flipped, **line stayed
  on both lists**. (State reached via cached verdict after an out-of-band
  add — mark_stocked + on-open-list is otherwise mutually exclusive by
  `_pick_action` precedence, so this pairing only occurs via staleness.)
- L89 remove_from_list on Overview ✅ — toast fired, server-verified gone from
  every open list (3), reopened popover shows fresh mark_stocked verdict.
  **Toast over-counts** (fan-out no-ops counted) → **FU-573**.
- L90 remove_from_list on Detail ✅ — tap → toast, line gone server-side, card
  live-updated to the fresh one-tap (FU-572 fix proven here).
- L91 per-line semantics ✅ — on ShoppingListDetail, tap removed ONLY the
  current line ("Removed QA Verdict Cheese."); the same item's line on the
  other draft list survived (server-verified).
- L92 no fallback toasts ✅ — ~8 taps across 3 surfaces, zero "use the row
  controls"-style toasts.
- Owner can delete DORA_VERIFY's whole BuyVerdictCard section (L87–92).

**Runtime backend URL (P8-10, L112–114) — walked, one FAIL:**
- L112 ✅ — About shows "Dora API endpoint http://localhost:5170/api"; Change
  opens the prompt pre-filled with the current URL.
- L113 ➗ — bogus URL saved → persists to `dora.backendBaseUrl` + full reload →
  friendly full-page "Can't reach Dora's brain" screen, **no crash** ✅; but the
  only affordance is "Try again" — `#/settings/about` renders the same error
  screen, so the fix-it prompt is **unreachable** → **FU-574** (recovery clause
  FAILS).
- L114 ➗ — restoring the original URL recovers cleanly on reload (About +
  session intact) — but had to be done via localStorage, since the prompt is
  unreachable in the broken state (same FU-574).
- Owner can delete L112; L113/L114 stay until FU-574 is fixed + re-verified.

**Fixture left in the documented state:** "QA Verdict Cheese" Stocked, on no
open list, verdict skip/high + mark_stocked one-tap — ready for reuse.

---

### Batch 2 (Stock) progress (2026-07-17, session 4) — first codified increment

Applying the close-out rule: codify regression-worthy behavioural flows; delete
what's already pinned or verified-once; route hardware to device packs.

**Codified → green (`web_app/e2e/stock.spec.ts`, 7 tests):**
- **FU-508 StockItem.image dropped (L730–734)** — 3 pins: no `/stock-items/<id>/image`
  request fires on overview or detail; no "row images" toolbar toggle; detail
  Overview tab has zero `input[type=file]`. Cheap, stable, high regression value
  (guards the column/upload creeping back). → **owner can delete L730–733**;
  L734 (recipes/avatars/store-logos still render) is a separate-features
  cross-check — left as a one-time confirm.
- **FU-507 expiry-on-open (L723–728)** — 4 pins on the curated sealed-with-expiry
  item "Kensington Pride Mangoes": fixture-contract (sealed + has expiry);
  detail toggle → "Marking … as open" prompt → Update expiry saves is_open +
  new expiry in one PATCH (server-verified); re-sealing fires **no** dialog and
  restores state. Note the detail-page toggle is silent (no toast — that's the
  row path), so pins assert server truth. Row-path L724–726 share the same
  handler; detail path pinned as the representative. → **owner can delete
  L723–728** (row vs detail is the same code).

**Verified-once → already backend-pinned → delete (no e2e dup):** the five
fix-verify sections are all owned by green backend regression tests — confirmed
passing this session (86 green across the representative files):
- L693–695 product unlink (FU-528) → `test_delete_integrity.py`, `test_api_fuzz.py`
- L702–705 stocktake snooze 500 (FU-526) → snooze regression suite
- L707–710 consumption/re-confirm level (FU-533) → `test_patch_semantics.py`, `test_concurrency.py`
- L712–715 rename-to-own-name (FU-528) → `test_patch_semantics.py`
- L717–718 unlinked-ingredients loads (FU-532) → `test_unlinked_ingredients.py`
- L720–721 reconcile pagination (fuzz) → `test_reconcile_verbs.py`, `test_api_fuzz.py`
  → **owner can delete all six sections** — the browser confirm is redundant
  once the backend tests own the behaviour (that was the whole point of the
  campaign's "codify" disposition).

**Device-pack (hardware):** Scan mode (FU-378, L679–691) needs `scanning_enabled`
ON **and a camera**. The manual-entry level-set loop is A-codifiable behind a
scanning-enabled seed knob, but the camera-decode half is Pack 1 (Android). →
moved whole to **Appendix A Pack 1**; codify the manual-entry loop opportunistically
when a scanning-enabled e2e seed flag is worth adding.

**Stocktake Chunk 2 runner — first slice CODIFIED green (2026-07-17, session 5;
`web_app/e2e/stocktake.spec.ts`, 5 tests):** legacy `/stocktake/run` → `/stocktake`
redirect; runner opens straight on the first item (no landing) with the cadence/
overdue caption + "Still correct" + the level-tinted "(change)" button, and NO
"Out of stock" button; the **Still-correct walk** drains the whole queue to the
completion summary (checked counter > 0) and **Done** returns to `/stock`;
re-entering the drained queue shows the "You're all caught up." card. Covers
DORA_VERIFY L774–777, L781, L784, L788–790, L819–820 (partial), L825. →
**owner can delete those lines.**

**Stocktake Chunk 2 runner — REMAINING VERBS NOW CODIFIED green (2026-07-17,
session 6; `web_app/e2e/stocktake.spec.ts` grew to 5 tests):** the four
remaining verbs + help + add-to-list are pinned as one deterministic **verb-walk**
that uses each verb exactly once and drains the queue: **Skip** (session-only →
item re-queued to the end, no API, `skipped` counter), **Change level** (picker
dialog → "Out of Stock" → `changed` counter + clock reset), **Push 3 days**
(snooze → `pushed` counter), **Mute** (confirm dialog "Mute X?" → `muted` counter),
then **Still-correct** the re-queued Skipped item (`checked` counter). Asserts the
five-counter completion summary (each = 1), the **SK-7 batch add-to-list** prompt
("1 item went Low or Out" → "Add to list…" → radio dialog on seeded "This week" →
"Added."), and **Done → /stock**. Plus a separate **(?) help dialog** test
asserting all five verb definition-terms render. Determinism rests on the curated
seed's exactly-four overdue items (Vanilla Ice Cream / Brazil Nuts / Hot Crispy
Chippies / Broccoli). Covers DORA_VERIFY **L792–797 (Change), L798–801 (Skip),
L803–806 (Push), L808–812 (Mute), L814–816 (help), L821–824 (add-to-list)** →
**owner can delete those lines.** Full spec **5/5 green**; full e2e suite otherwise
green (one unrelated pre-existing uploads channel failure — see FU-576).
- **Stocktake Chunk 3 settings — CODIFIED green (2026-07-17, session 7;
  `web_app/e2e/stocktake-settings.spec.ts`, 3 tests):** the Settings → Admin →
  System → Stocktake page's two global dials. Page loads with the three cadence
  bands + server default Fortnightly; **cadence** tap → "Default cadence saved."
  toast → PATCH persists across a reload → restored; **Auto self-tuning** flip
  → "Auto self-tuning off."/"...on." toasts → persists across reload → restored.
  Asserted against server truth (`/app-settings`) not Quasar active-button
  styling. **Self-restoring** (ends at Fortnightly + Auto on) so it doesn't
  perturb the stocktake queue (sorts + runs before `stocktake.spec.ts`). Covers
  DORA_VERIFY **L741–746** → owner can delete (L743/745/746 fully pinned;
  L741/742/744 behaviourally pinned — only the visual "highlighted"/"de-activates"
  nuance stays V-pack). **Remaining, not codified:** L740 (nav-entry placement/icon
  — one-time), L747 (non-admin banner — needs a non-admin session), L748–749 (Auto
  on/off actually reshaping the runner's cadence — deeper behaviour).
- **Alert-threshold removal (L752–753)** — CODIFIED (2026-07-17, session 8):
  `alert-thresholds.spec.ts` pins that the "Default stocktake reminder" section
  is gone from Settings → Admin → System → Alert thresholds (asserts no
  "stocktake reminder" copy + exactly one numeric dial survives) AND that the
  surviving "Expiring-soon window" still edits/saves/persists on blur (toast
  "Alert thresholds saved.", server truth `/app-settings`). Self-restoring to 7.
  → owner can delete L752–753.
- The **pulse outline / reduced-motion / dark/light** checks (L762–768) are V-pack
  (eyeball) → Appendix B. The **"Needs check" Overview filter** (L755–760) is
  CODIFIED (2026-07-17, session 8) in `stock.spec.ts`: opens the Filters panel,
  flips "Needs check" → `.stock-row` count narrows to exactly `/stocktake/queue`
  total (and each queued name is visible) → toggle off restores the full list;
  also pins the "Stocktake (N)" toolbar label mirrors the same server count.
  Read-only, runs before the queue is drained. → owner can delete L755–760
  behavioural bullets (the icon/position bullet stays V-pack, one-time visual).
- **Add-a-stock-item dialog (L672–677, Codex)** — backend fully unit-tested (trim/
  dedup/over-long); the dialog-renders-expiry+Essential visual bits are a
  one-time confirm; the trim/dedup behaviour is already pinned. Low priority.

**Batch 2 disposition tally (updated 2026-07-17 session 8):** ~120 items →
~40 codified green (stock + full stocktake runner + Chunk 3 settings dials +
"Needs check" Overview filter + alert-threshold removal) · ~15 delete
(backend-pinned) · ~11 delete (FU-507/508 codified) · ~20 device-pack (scan) ·
codify-next tail now just non-admin banner (L747, needs a non-admin session) +
auto→runner cadence effect (L748–749, deeper behaviour) · rest V-pack/one-time
(pulse/reduced-motion/dark → Appendix B). Manual pile for this batch has now
shrunk by ~72; runner + settings dials + Overview filter + alerts-removal pinned.

### Batch 3 (Stock B) progress (2026-07-17, session 9) — first codified increment

**Codified → green (new `web_app/e2e/bulk-waste.spec.ts`, 4 tests):** the bulk
**"Log waste…"** action on Stock Overview (DORA_VERIFY **L827–836**, origin
FU-226). Enters bulk mode, ticks stable no-expiry seed items (Canned Tomatoes /
Brown Onions / Garlic — untouched by any other spec):
- **L834** — with 0 selected the "Log waste…" bulk-bar button is disabled.
- **L830 + L831** — select 3 → the MarkAsWastedDialog opens with header "Why did
  this go to waste?", subject "3 items", subline "One reason applies to every
  selected item."; tapping the **Spoiled** tile closes the dialog, exits bulk
  mode, and fires one plural summary toast "Logged 3 items as wasted." with Undo.
- **L832 (data half)** — server truth: exactly one `spoiled` StockItemWasteEvent
  per selected item (`/waste/events`). The Reports→waste-insights *UI* surface
  itself stays a one-time eyeball (V-pack).
- **L833** — Undo on the summary toast removes all events ("Undone." toast) and
  restores each item's original expiry (covered by the expiry test below).
- **L835** — a single selection uses singular copy ("Logged 1 item as wasted.").
- **expiry clear+restore** — a 4th test PATCHes an expiry onto Garlic, logs
  waste (expiry cleared, asserted server-side), Undoes (expiry restored), then
  resets the seed item — fully self-contained.

**Self-restoring:** every test ends via the UI Undo it's pinning; an `afterAll`
safety net then hard-resets via the API (deletes any lingering event for the
three ids, nulls any expiry) from a context rebuilt off `e2e/.auth/user.json`,
so a mid-flow failure can't leak into later specs.

**L836 (single-item row expiry-menu waste path)** — CODIFIED (session 10, 6th
test): PATCH an expiry onto Canned Tomatoes so the row's expiry button opens the
push/clear/log-waste **menu** (a no-expiry item shows a date picker instead) →
open it via the `Expires <date>` accessible name → "Log waste" → Spoiled → the
**per-item** toast `Logged "Canned Tomatoes" as wasted.` (distinct copy from the
bulk summary) → server event + expiry cleared → Undo restores both → reset to
null. Confirms the bulk flow didn't regress the single path.

**Not codified here:** L829's "trash icon" + L832's Reports-UI render are
one-time visuals (V-pack). The whole FU-226 waste section is now behaviourally
pinned.

**Verification:** `DORA_E2E_CHANNEL=chrome npx playwright test` — `bulk-waste.spec.ts`
**6/6** green (incl. the auth setup); full suite **40 passed / 1 failed**, the one
failure the same pre-existing unrelated `uploads.spec.ts:46` channel flake
([[FU-576]]). No new FU.

**Auto-add-on-low (L838–857, FU-315/464/511)** — first codified increment
(session 11) in `auto-add-on-low.spec.ts` (2 tests, serial, self-restoring).
Seed reality that made it testable: the Playwright webServer sets
`DORA_SEED_BULK_ITEMS=0`, so the `big_list` draft never seeds → **"This week" is
the sole draft**, i.e. `resolve_primary_target` returns "single" and the happy
path is deterministic. But **every** flagged+Stocked seed item is already on an
active list (eggs/olive-oil/coffee on "Saturday shop", brazil already Low), so
the Essential-mode happy path can't fire on the seed without restructuring shared
list state — instead the spec drives the **`All items` mode** path on a clean
non-Essential item (Jasmine Rice: Stocked, on no list, untouched by other specs),
which exercises the identical toast + line-chip seam and *is itself* L849's
deliberate 3-state expansion.
- Test 1 (L843): Settings → Admin → System → Stock dial loads (reads seeded
  `essential_only`), saves each state eagerly with the "Auto-add mode saved."
  toast, persists across a hard reload (server truth via `/app-settings`),
  restores to `essential_only`.
- Test 2 (L844 + L847 + L849): mode→`all`, drop Jasmine Rice Stocked→Low Stock
  via the row level menu → toast **"Added Jasmine Rice to <display_name>."** +
  caption "Auto-added because it went low." → server truth: the draft list now
  carries a line for the item tagged `added_via=auto_low_stock` → the list-detail
  render shows the `auto: low stock` chip. Restores via API (delete the auto line
  by-stock-item, reset level to Stocked, mode back to `essential_only`); an
  afterAll re-asserts the clean state.
- Test 3 (L856/857): the **retired per-item auto-add UI stays gone** — read-only
  absence guard against the `auto_add_when_low` toggle (collapsed into the
  install-wide mode by FU-511) creeping back. Stock overview: no "Will auto-add on
  low" filter chip, no "Auto-add" footer count (asserted alongside a surviving
  "Essential" control so it's not a blank-page false pass); detail page: no
  "Auto-add" toggle row (item name rendered as the render sanity).
→ **owner can delete L843, L844, L847, L849, L856, L857.**

**Not codified here (stay owner-verify / other homes):** L845 (Out transition —
same handler, not separately driven), L846 (no-manual-refresh timing — UX, not
asserted), L848 + L850 (Off / Essential-only *negative* paths), L851 (dedup) +
L852 (0/2+ draft ambiguity) → **server-owned branching, routed to a backend
follow-up** [[FU-577]], L853 (detail-page Level row), L854 (cook-mode decrement,
multi-toast), L855 (offline queue).

**Verification:** `auto-add-on-low.spec.ts` **4/4** green (incl. auth setup); full
suite **43 passed / 1 failed** — the one failure the same pre-existing unrelated
`uploads.spec.ts:46` channel flake ([[FU-576]]). New FU-577 logged for the
untested server-side branching matrix.

**FU-577 backend truth-table CODIFIED (2026-07-18):** new
`tests/e2e/dora_api/test_update_stock_item_auto_add.py` (12 tests, green; full
backend suite 1505 passed) pins the whole server-owned matrix directly against
`PATCH /api/stock-items/<id>`: mode × flagged (Off never; Essential-only iff
flagged; All regardless), **L845** Stocked→Out fires, transition guard (Low→Out
+ Out→Stocked silent), **L851** dedup (on the target draft AND on a
SHOPPING-status list), **L852** draft-count (0 and 2+ silent; draft+SHOPPING
still fires onto the draft). Firing cases assert the 200 `auto_added` body +
the `added_via=auto_low_stock` line; silent cases 204 + no line.
→ **owner can also delete L845, L848, L850, L851, L852** (backend-pinned).
Remaining owner-verify in this section: L846 (refresh timing), L853 (detail
Level row), L854 (cook-mode multi-toast), L855 (offline queue).

**3-band StockLevel collapse (DORA_VERIFY L874–883) — triaged + gaps codified
(2026-07-18):** the section is mostly backend-owned; three surfaces had *no*
server test — now pinned in new `tests/e2e/dora_api/test_stock_level_collapse.py`
(6 tests) + one test added to `test_data_router.py` (7 new total, green; full
backend suite **1512 passed**):
- **L875** — `POST /shopping-lists/<id>/finish` with an empty body flips every
  *ticked* line's item to Stocked (sequence identity), returns
  `{items_restocked: N}`; a second test pins that *unticked* lines' items keep
  their level (finishing only restocks what you bought).
- **L876 (server half)** — a `level_overrides` entry wins over the Stocked
  default (part-restock lands on Low, unlisted sibling still Stocked); an
  override naming an unknown level id is a 422 and nothing mutates (list not
  done, level untouched).
- **L877** — alert action `mark_restocked` sets the item to Stocked + bumps
  `stock_level_last_updated`; contrast test pins `acknowledge_stocktake`
  bumping the stamp with the level **untouched** (was previously untested —
  only `reset_expiry` had a test).
- **L879** — spreadsheet import: a mapped Level column with a **blank cell
  defaults to Stocked**, and "Stocked"/"Low"/"Out of stock" land on sequences
  0/1/2 — asserted on the created items' actual levels (the old test only
  counted rows).

Already pinned elsewhere (verified this session, no new tests needed):
**L878** `review/complete` → `{set_stocked, checked}` + item flips Stocked in
`test_stocktake_router.py`; **L880** "sufficient"/"ok"/"fine"/"well stocked" →
STOCKED aliases in `test_confirm_actions_resolve_level.py` (resolves by
sequence, rename-proof); **L881** cookability Low-counts-as-have /
Out-doesn't in `test_recipe_cookability.py`.

→ L875/877/878/879/880/881 **deleted from DORA_VERIFY 2026-07-18**
(delete-on-pass sweep). Stay one-time eyeballs (V-pack): the modal render
(3 options, no "Sufficient" label — merged with L875's UI half), onboarding
"Restock" scene copy, buy-verdict popover "Stocked" need-axis label (adjacent
to the Batch-0 BuyVerdictCard walk).

**Zero-Input Pantry (P8-07) — HTTP seam codified (2026-07-18):** the belief
*engine* was already unit-pinned (`test_pantry_belief.py`, 11 tests: bands,
cook drift, override-wins, thin-history caution, differs flag) but the HTTP
layer had zero tests. New `tests/e2e/dora_api/test_pantry_beliefs_endpoint.py`
(3 tests, green; full backend suite **1515 passed**) pins: `GET
/stock-items/beliefs` default-on shape (enabled:true + per-item
believed_band/confidence_band/reason contract), the per-user opt-out gate
(`PATCH /auth/me inferred_pantry_enabled:false` → `{enabled:false,
beliefs:{}}`, persists, re-enables), and the override-wins pin end-to-end (a
fresh level PATCH reads back as that band at HIGH confidence). DORA_VERIFY
section trimmed per delete-on-pass: the OFF-endpoint bullet, thin-history
bullet, and manual-change bullet deleted (pinned); toggle + drift-outline
bullets reworded to their remaining UI halves. Remaining owner/e2e checks:
chip render + tooltip, buy/cook loop reasons, warning-outline render,
quick-check suggestions (×2), dark-mode tokens, backup/restore recompute.

**P8-05 buy-verdict oracle (DORA_VERIFY L733–744) — codified (2026-07-18):**
the engine was already fully unit-pinned (`tests/test_buy_verdict.py`, 27
tests: verdict matrix incl. out-of-stock/low+cheap/stocked+wasteful/
stocked+above, thin-data collapse, reason labels + `$last vs $usual` details,
wait-hint, fake-markdown) and the Skip walk e2e'd (Batch 0 + `buy-verdict.
spec.ts` tests 1–3). This session pinned the three remaining UI seams (3 new
tests → `buy-verdict.spec.ts` now 6, suite 46 pass / 1 pre-existing FU-576
flake) + the whole client cache (new `web_app/test/unit/useBuyVerdict.spec.ts`,
7 tests; frontend Vitest → **394/31**):
- **Feature flag** — Settings → Admin → System → Features toggle off → toast +
  server truth → full reload → fixture row renders with **no** badge; toggle on
  → reload → Skip badge back. Found **FU-580** en route: the toggle never
  refreshes the once-per-document health probe, so the flip needs a full reload
  in a live session (test pins the verify bullet's reload wording as-is).
- **Silent on low-confidence** — thin-history seed item (Jasmine Rice):
  `/buy-verdict` answers `confidence: low`, row renders name but zero
  `.dora-buy-verdict-badge` (fixture row asserted as the non-blank control
  elsewhere in the file).
- **Out-of-stock → buy walk** — fixture PATCHed to Out of Stock → API canary
  (buy/high, `reasons[0] = out_of_stock`, one-tap `add_to_list`) → green Buy
  chip → popover "You're out of stock" → one-tap "Add to primary list" →
  "1 added." toast → server truth: line on the draft → restored.
- **Client cache (Vitest)** — one request per item shared across concurrent
  consumers, cache-serve inside the 5-min window, stale-but-usable background
  refresh past it, FU-572 live-entry invalidation refetches immediately (and
  stays lazy on a null entry), error → null badge + captured message,
  disabled-gate no-fetch until the flag flips, clearBuyVerdictCache drops all.

→ L734–744 **deleted from DORA_VERIFY** (delete-on-pass); the section keeps one
V-pack line (orange **Wait** badge look — the only variant never walked). An
afterAll safety net (flag on, fixture Stocked + off-list) was added to the spec.

**History tab — both sections codified (2026-07-18):** the expiry-emission +
cap/older-count server halves were already pinned (`test_stock_item_router.py`);
the two feeds with zero server tests are now pinned in new
`tests/e2e/dora_api/test_stock_item_history_feeds.py` (7 tests; full backend
suite **1522 passed**):
- **Bought** — ticked+priced line on a finished list surfaces one
  `purchase_events` entry (price/list-name/stamp; store `None` when uncaptured);
  price-less/store-less line still surfaces (title-only render contract); a
  seeded store id resolves to `store_name`; an **unticked** line never
  surfaces; a ticked line on an in-flight (`shopping`) list is mid-shop, not
  bought.
- **Cooked** — `POST /recipes/<id>/cook` writes one `cook_events` entry on
  ingredient items only (bystander item stays clean — the RecipeIngredient
  join, not a wildcard), `meals_cooked` rides along for the "× N meals" badge;
  a zero-meal cook (bare `last_made_on` bump, 204) records nothing.

UI halves in new `web_app/e2e/history-tab.spec.ts` (4 tests; full e2e suite
**50 pass / 1 pre-existing FU-576 flake**): Sriracha chatty-seed walk (66
seeded expiry events → "16 older events not shown", count stable across a
reload), Milk under-cap mixed feed (Bought/Wasted/Pushed interleaved, no
footer), Garlic "Used in <recipe> · N meals" batch badge, and an engineered
item walking the full Set → Pushed +7 days (with `A → B` body) → Cleared
(with "Was <date>" body) family, self-deleting. Migration-downgrade bullet
dispositioned to `tests/test_migrations.py` (SQLite xfail carve-out; Postgres
leg batch 19).

→ both History sections (old L758–783) **deleted from DORA_VERIFY**, replaced
by one merged section holding a single one-time visual line (event-kind theme
colours + the singular footer branch).

**FU-109 deep-link filter + no-dim — codified, 2 real bugs found + fixed
(2026-07-18):** narrowing/orphan/AND-compose were already Vitest-pinned
(`useStockFilters.spec.ts`); new `web_app/e2e/recipe-deeplink.spec.ts` (4
tests) pins the URL/chip wiring: card filter icon → `/stock?recipe=` chip +
list narrowed to exactly the aglio ingredients, chip-× teardown (param
stripped, full list back), toolbar **Clear** strips `?recipe=` with a reload
unable to reinstate it, bogus id leaves the list intact with no chip, filter
icon only on the detail Recipes tab (cookbook cards asserted icon-free), and
every card on that tab at computed opacity 1 (the dim code no longer exists in
`RecipeCard`). **Bugs found by the spec, fixed inline (CHANGELOG'd):**
(1) a bogus/dead `?recipe=` id stranded a phantom "Ingredients of: this
recipe" chip — the hydration-fallback label leaked into the
loaded-but-unresolved state; fixed by making the recipe store's hydration
latch reactive (`recipesHydrated`) and gating the chip on resolved-context-or-
still-loading. (2) the Stock Overview empty-state "Clear" button called the
raw filter reset, leaving `?recipe=` in the URL for a refresh to reinstate —
now routed through the page's `clearAllFilters` wrapper. **Also unblocked the
pipeline:** the FU-579 bulk-waste type errors hard-failed `quasar build`
(exit 2, no `dist/spa`) — fixed via a throwing items-by-name accessor;
`vue-tsc --noEmit` now fully clean; FU-579 amended (src-pwa dev-watch half
stays open). Both FU-109 sections **deleted from DORA_VERIFY** (nothing
remains — the tooltip text lives in the component template). Full e2e suite
**54 pass / 1 pre-existing FU-576 flake**; Vitest 394/31.

**Stock pickers + Log Waste — behavioural halves codified (2026-07-18):** new
`web_app/e2e/stock-pickers.spec.ts` (2 tests; full e2e now **56 pass / 1
FU-576 flake**): (1) the detail-page Level row round-trip on a throwaway item
(created via API so auto-add/seed state can't interfere) — dropdown pick
Stocked→Low Stock → "Updated just now" stamp + trigger re-label + server
truth, self-deleting; (2) the overview level filter set→clear cycle — narrows
on pick, clear-× restores the full list with the "Any level" fallback trigger,
and the whole interaction captured console-clean (warnings/errors/pageerrors
all asserted empty). The row expiry-menu Log-waste behavioural path was
already pinned by `bulk-waste.spec.ts` test 6. Section reworded to a single
one-time visual (dot styling parity across the three pickers + the
destructive-red Log-waste entry).

**C-1b detail section triaged + Chunks 2/4 codified (2026-07-18, session
close):** the big C-1b section rewritten against current coverage — deleted
as pinned (Level row round-trip, lifecycle timeline, clear semantics, expiry
dialog, unsaved-changes composable) and as **stale** (the C-1b.1
header-level-chip bullet superseded by the Overview Level row; every
auto-add-toggle / footer-Auto-add mention, retired by FU-511 with absence
pinned). Remainder compressed to: one layout/visual walk line, splitter-peek
walk, the picker-× wiring, **two codify-next candidates** (C-1b.4
Recipes/Lists/Substitutes actions; C-1b.3 Products tab incl. the products-off
tab-gating), and the unpinned History extras (Restocked/Dropped labels,
synthetic Opened, empty copy). New coverage this close: **`useStockItemActions
PushExpiry.spec.ts`** (8 Vitest tests — the FU-123 `max(today, current)+N`
push matrix incl. past-expiry→tomorrow, fallback, toast + error path; Chunk-4
bullet deleted) and a **Chunk-2 describe in `stock.spec.ts`** (2 tests:
desktop filter-panel persistence reload round-trip both directions; retired
"Used in a recipe" filter absent + bare "Search" placeholder; Chunk-2
reworded, stale Flagged/Auto-add footer-order bullet corrected to the current
labels). Suites: e2e **58 pass / 1 FU-576 flake**, Vitest **402/32**.
Batch-3 tail now: Chunk-2 mobile-hidden bullet (viewport-gated), Chunk 5
(responsive nav/long-press — device/viewport pack), Offers sidecar (1
money-gated walk line), + the compressed visual walks.

**C-1b.4 codify-next candidate CODIFIED (2026-07-18):** new
`web_app/e2e/detail-recipes-tab.spec.ts` (3 tests + setup, fully throwaway
universe — two API-created Stocked items + a recipe using both, torn down in
afterAll): heart toggles favourite on AND off with server truth (this surface
once shipped with the toggle wired to a dead listener); the cookable card's
cart action ("Add all to list") lands both ingredients on the primary draft
("2 added." toast + list truth) and the Lists tab reflects membership with no
dead `open_in_new`; a substitutes row renders without the retired per-row
"Swap into list" and Remove unlinks (detail-DTO truth + row gone). Triage
note: the old "styled Primary badge" wording was stale — Round-17 replaced
the pill with a warning-toned star (folded into the visual walk). Full e2e
suite **61 pass / 1 FU-576 flake**. Remaining C-1b codify-next: the
Products-tab gating (C-1b.3, products-flag-dependent).

**C-1b.3 Products tab codified → real bug FU-581 (2026-07-18):** new
`web_app/e2e/detail-products-tab.spec.ts` (2 tests): Milk's two linked
products render with exactly ONE Cheapest chip + `--cheapest` highlight
class, the quiet "Link another" header action, per-card Add-to-list, and no
retired "Get cheapest" button anywhere; a throwaway no-products item shows
the centred "Find & link a product" CTA (and no "Link another"),
self-deleting. **Bug found: the CTA routes to the FU-186-retired
`/product-search` route and lands on the 404** — same dead link on
`MyProductsPage.vue` (×2) and the Dashboard "Hunt for deals →" CTA; logged
as [[FU-581]] (design call: external `product_search_url` vs My Products vs
hide) rather than blind-patched, and the spec deliberately does NOT pin the
destination until that's decided. The products-OFF half (tab hidden +
`?section=products` → Overview fallback) needs a productless install — kept
as the section's one remaining bullet. Full e2e **63 pass / 1 FU-576
flake**.

**Batch 10 (Dashboard) opened — Draft-my-shop (FU-351) codified
(2026-07-18):** server halves in new
`tests/e2e/dora_api/test_auto_generate_draft_shop.py` (2 tests; full backend
suite **1524 passed**): zero candidates on the create-new path answer
`nothing_to_add: true` + null `shopping_list_id` + **no phantom list** (the
collection is byte-identical before/after), and the card's explicit
"Weekly shop · <date>" name is honoured on the created list. UI seams in new
`web_app/e2e/dashboard-draft-shop.spec.ts` (2 tests + afterAll safety net
deleting any "Weekly shop ·" list so the sole-draft assumption other specs
rely on holds): the card renders in the act zone (blurb + button), one click
→ "Drafted N items." toast + caption → navigates to the named draft with
`auto:` provenance chips rendering; the Cards-menu row's q-toggle hides and
restores the card. Provenance priority + the single-commit contract were
already pinned (`test_auto_generate_priority.py` /
`test_auto_generate_unit_of_work.py`). Left as walk bullets: the empty-case
UI half (needs a fresh install), the forced-500 error toast, and the
consumed-entry guard (consumed_at only written by the cook-reconcile job —
code-visible at `auto_generate.py:418`). Full e2e **65 pass / 1 FU-576
flake**.

**Dora Score / Kitchen health (P8-08) codified (2026-07-19):** the engine was
already unit-pinned (`test_dora_score.py`, 8 suites) and the endpoint
shape/anonymous-401 backend-pinned (dashboard router + DTO snapshot +
route-auth sweep). Added: the L923 log-line contract as a backend test
(`test_dashboard_router.py::test__dora_score__EveryRequestLogsTheScoreLine…` —
one "Dora Score user=… composite=… trend=… (delta=…)" record per request, no
NaN/negatives/exceptions; backend suite **1525 passed**) and new
`web_app/e2e/dora-score.spec.ts` (3 tests): hero + five ordered component rows
asserted against `/dashboard/dora-score` server truth (labels, reasons,
bar-per-scored-row), the **dormant contract on real data** (seed has no budget
→ Budget row renders "—", dormant class, no mini-bar, composite still a
number), card-above-Pantry placement, the action links (Budget/Freshness/
Run-outs/Stocktake navigate, none 404; **Waste deliberately has no link** —
D10 dissolved `/waste`, pinned as an absence; the old L920 `/waste`
expectation was stale), and the Cards-menu q-toggle hide/restore. **Found
[[FU-583]]** en route: `?expiring=1`/`?stocktake=1` on the Freshness/Stocktake
links are silently ignored by `StockOverview.applyQueryFilters()` (honours
only location_id/attention/level_id) — exactly what L920 asked to flag.
DORA_VERIFY section trimmed per delete-on-pass (8 bullets deleted/absorbed;
survivors: trend-chip both-direction render, bar traffic-light colours,
fresh-install empty state, week-long trend flip, kitchen-zone drag-reorder).

**Log-price quick action (FU-300) + budget money-gate (FU-297) codified
(2026-07-19):** new `web_app/e2e/dashboard-log-price.spec.ts` (4 tests + a
beforeAll/afterAll that flips BOTH money layers on — the e2e seed ships money
OFF at install AND user level — and restores seed state after). Pinned: the
three-button quick-action bar; the LogPriceSheet picker (≤12-row low/out-first
shortlist asserted against stock-items/stock-levels server truth, live "milk"
filtering, selection → "Log a price · <name>" title, prefill seeded from the
detail DTO's `price_entry_prefill` — exercised, the seed harvests Milk
observations); submit happy path ($6.40 / 2 L → toast, sheet closes, exactly
one new observation with the folded shape in the detail DTO, and the
Your-Prices widget rendering the server-derived "$3.20 / L" on a fresh
single-goto page — FU-584 dodge); dismiss-means-cancel (zero POSTs) + fresh
reopen; money OFF hiding Log price AND the budget card (dashboard + Cards
menu, zero `GET /api/budget/status`). **Two findings en route:** [[FU-585]] —
the back arrow keeps the search query (code) vs the verify bullet expecting it
cleared (spec pins current behaviour, not blind-patched); [[FU-586]] — the
dashboard money loaders race the one-shot /api/health flags probe on a cold
mount and never re-run when flags land (reproduced: money ON, hard reload,
zero budget-status requests), so the spec deliberately does NOT pin the
money-ON request. FU-300 section deleted (fully covered); FU-297 keeps one
FU-586-blocked walk bullet. Full e2e suite **73 passed / 0 failed** (the
FU-584 flakes stayed quiet this run). Box note: this machine needed
`npx playwright install chromium` (headless-shell v1228 missing).

**Donut deep-links (FU-299) + "Next to cook" (FU-298) codified (2026-07-19):**
new `web_app/e2e/dashboard-donut.spec.ts` (3 tests, read-only on seed):
legend low/out rows + "View →" hrefs pinned against `/stock-levels` server
truth and the in-stock legend row + whole card proven inert; the donut's
exactly-two link segments (role/tabindex/class + "View low items"/"View out
items" aria-labels) with the green arc inert even to a dispatched click; a
**real pointer click on the low arc** (point computed from the
`/dashboard/summary` proportions — pins that the rotated SVG stroke is
actually hittable, needed a `scrollIntoViewIfNeeded` since `page.mouse`
doesn't scroll) landing `/stock?level_id=<low>` with the FilterBar level
select showing the level name and `.stock-row` count matching server truth;
Enter on the out arc and Space on the low arc both navigating. Whole
DORA_VERIFY FU-299 section deleted. New `web_app/e2e/dashboard-next-cook.spec.ts`
(2 tests) on a throwaway universe (Stocked + Out items; ready / missing-one /
no-ingredients recipes planned TODAY in "Breakfast" — sorts ahead of the
seed's Dinner/Lunch so the trio owns the card's top-3 deterministically; the
ready recipe planned twice to pin the recipe-dedupe): rows mirror the DTO's
order with "Today breakfast · serves N" meta and Ready / Missing 1 /
No ingredients badges backed by explicitly asserted DTO truths
(missing_count 0 / 1 / null); name → `/cookbook/{id}`, Cook →
`/cookbook/{id}/cook`. FU-298 section trimmed to the one plan-free-install
empty-state bullet. **FU-584 addendum found en route:** the hash-router race
also fires on a *warm* `goBack()` → `router.push` sequence (deterministic
blank-document wedge in the next-cook spec; both new specs route around it
via reload → fresh goto). Full e2e suite **78 passed / 0 failed**.

**Price-drops widget (FU-296) codified → real bug found + fixed
(2026-07-19):** backend (`test_reports_router.py` +4): ranking pinned
(%-desc, dollar-amount tie-break, filtered to the test's own products),
`is_active=false` exclusion, limit clamp (0/−3→1 row, 999→≤20, missing and
`abc`→exactly 5 against six seeded drops). **The ranking test's second
price-PATCH 500'd — real bug:** `update_product.py` appended the archived
`ProductHistoricOffer` to the relationship without `repo.add()`, so the
cascaded insert carried `EMPTY_UUID` and the second-ever price change in an
install collided on the PK (the ingest path and seed both `add()`; this was
the odd one out). One-line fix + comment; the new tests are the regression
pin; CHANGELOG entry added. Backend suite **1528 passed**. UI
(`dashboard-price-drops.spec.ts`, 2 tests): defaultHidden honoured, Cards-
menu enable → honest empty state on seed truth (rows==0 asserted first),
engineered drop (create product $10 → PATCH to $8, link to a throwaway
item) renders name/store/deep-link/"was $10.00"/"20% off" + "My products →",
deactivate → empty state returns, toggle restored to defaultHidden. Specs
**warm-navigate** (land `/#/stock`, then in-app goto `/#/`) because the
products-gated loaders lose the same cold-mount flags race as FU-586
(addendum added there). No DELETE /products exists — cleanup is
deactivation, which the report excludes (itself backend-pinned). Full e2e
suite **80 passed / 0 failed**.

**Cards-menu reorder (FU-294) + `dashboard_layout` backend (FU-292)
codified (2026-07-19):** new `web_app/e2e/dashboard-cards-reorder.spec.ts`
(4 tests + a beforeAll/afterAll capturing and restoring the user's
`dashboard_layout`): tap down/up arrows reorder within the Today zone
(first-row up + last-row down disabled — note the zone's true last menu row
is the defaultHidden "This fortnight", which still lists), asserted against
menu render + the `/auth/me` layout JSON + a full reload; native HTML5
drag (`dragTo` on the `.dora-dnd-handle`) lands drop-on semantics and the
order follows the user to a second browser context (FU-292's cross-device
contract); cross-zone drag (Pantry → Today) leaves both the menu and the
server layout byte-identical; an iPhone-UA run (Quasar's platform.is.mobile
is UA-based, not viewport) pins the handle column hidden with tap arrows +
toggle remaining. FU-292's other halves were already covered (migration
applies on every suite boot; `test__dashboard_layout__set_and_clear` green).
Spec note: the up/down arrows are icon-only BaseButtons with tooltips but
no aria-label → no accessible name, so the spec targets them positionally
(pre-existing, FU-578's unlabelled-buttons bucket — not re-logged). FU-292
section deleted; FU-294 down to the one mid-drag transient-visuals bullet.
Full e2e suite **84 passed / 0 failed**.

---

**Harness lesson (major — shapes every future browser batch):** the in-app
preview pane runs **hidden** (`visibilityState: hidden`): no paint, no
`requestAnimationFrame`, screenshots time out. Vue `<Transition>`s double-rAF
before resolving, so **any transition-gated content wedges** — route swaps
after the first, and the stock detail page's skeleton→content `FadeTransition`
(cold-load included). Partial workaround (in Appendix D): rAF stub +
zero-duration CSS un-wedges top-level route swaps, but not the C-1b desktop
peek. **Decision: browser A-checks move to a Playwright-driven runner**
(already in the repo — FU-540, `test:e2e`; headless Chromium paints, rAF runs,
screenshots work → also produces the V-pack artifacts). Claude in Chrome is
the alternative if the extension gets connected. The pane stays fine for
API-level checks, single-view cold loads, and DOM instrumentation.

**2026-07-18 — interactive driver now exists:** `web_app/e2e/drive.mjs`
(JSON-plan steps over headless system Chrome: goto/click/fill/viewport/scheme/
shot/eval, auto-login, kills the vite-checker overlay — FU-579). This is the
tool for ad-hoc UX walks and **V-pack screenshot staging** — point the plan's
`outDir` at a folder, collect the PNGs. See the worklog entry (2026-07-18
later 5) for setup.

---

## Section register

Status per section. Lines are the 2026-07-16 snapshot. "Env" lists only hard
gates (flags, PG, Docker, device, built PWA). Test-pinned = the origin fix
already has regression tests (low-risk re-confirm, per CHANGELOG/worklog).

### Top block (recent surfaces)

| Section | Lines | Items | A/V/H | Stale | Env / notes | Status |
|---|---|---|---|---|---|---|
| Onboarding story pass (2026-07-12) | 11–21 | 9 | 8/0/1 | 0 | fresh install; reduced-motion (emulable) | ⚪ |
| Dora assistant / helper bubble (FU-429+360) | 22–38 | 15 | 15/0/0 | 0 | LLM configured + no-LLM user; 2 accounts | ⚪ |
| Currency & locale (FU-043) | 39–49 | 9 | 8/0/1 | 0 | admin; mic item H | ⚪ |
| Native Android build (P8-10) | 50–62 | 11 | 2/0/9 | 1 | Android toolchain + device → device pack | ⚪ |
| StoresSettings logo upload (FU-335) | 63–70 | 6 | 5/0/1 | 0 | sample images; camera item H | ⚪ |
| SettingsFileDrop (FU-545) | 71–81 | 5 | 5/0/0 | 0 | admin; sample files | 🟡 pilot |
| BuyVerdictCard one-tap (FU-454) | 82–89 | 6 | 6/0/0 | 0 | engineered verdict states | 🟡 pilot |
| Password policy (FU-442) | 90–99 | 8 | 8/0/0 | 0 | registration open; DB-seed legacy account | 🟡 pilot |
| PWA install + offline (FU-336) | 100–110 | 8 | 5/0/3 | 0 | **built PWA over HTTPS/localhost**; iPhone items H | ⚪ |
| Runtime backend URL | 111–115 | 3 | 3/0/0 | 0 | deliberately breaks connectivity — reversible | 🟡 pilot |

### Cookbook & recipes + Cook mode

| Section | Lines | Items | A/V/H | Stale | Env / notes | Status |
|---|---|---|---|---|---|---|
| Cookability + expiring filters | 132–138 | 6 | 6/0/0 | 0 | test-pinned (4 filter tests) | ⚪ |
| Free-text ingredient path (FU-506) | 140–146 | 6 | 6/0/0 | 0 | | ⚪ |
| RecipeEditDialog stub-creator (FU-095) | 148–154 | 6 | 6/0/0 | 0 | | ⚪ |
| Importer bulk-linker + share target (C6) | 156–168 | 12 | 11/0/1 | 0 | share-sheet item → Android pack | ⚪ |
| Importer paste-based rebuild (C5) | 170–179 | 9 | 9/0/0 | 0 | corpus pages; taste.com.au2 fixture exists | ⚪ |
| Ingredient DnD (FU-118/161) | 181–195 | 14 | 14/0/0 | 0 | drag automation | ⚪ |
| Chunk 6 structured steps (FU-093) | 197–206 | 9 | 9/0/0 | 2 | SQLite+PG alembic | ⚪ |
| Chunk 7 source URL + URL importer (FU-103) | 208–217 | 9 | 9/0/0 | 4 | mostly stale — URL importer deleted | ⚪ |
| Chunk 8 recipe versions (FU-105) | 219–230 | 11 | 11/0/0 | 0 | SQLite+PG alembic | ⚪ |
| Chunk 9 cost + nutrition (FU-116) | 232–247 | 15 | 14/1/0 | 0 | Money+Nutrition flags; priced products | ⚪ |
| Chunk 10 multi-part sections (FU-119) | 249–255 | 6 | 6/0/0 | 0 | SQLite+PG alembic | ⚪ |
| Chunk 4 detail cleanup (FU-089) | 257–266 | 9 | 8/1/0 | 0 | | ⚪ |
| Chunk 3 card redesign (FU-088) | 268–274 | 6 | 6/0/0 | 1 | command-palette half of L274 stale | ⚪ |
| Chunk 3+ revision (FU-088r) | 276–288 | 12 | 12/0/0 | 0 | 2 sessions for per-user persistence | ⚪ |
| Chunk 5 images + tools (FU-091) | 290–296 | 6 | 6/0/0 | 0 | image files incl. >4MB | ⚪ |
| Chunk 2 tag taxonomy (FU-085) | 298–303 | 5 | 5/0/0 | 0 | | ⚪ |
| FU-085 second round (FU-151) | 305–311 | 6 | 6/0/0 | 0 | assistant enabled | ⚪ |
| Recipe image-steps mode | 313–321 | 8 | 6/0/2 | 0 | camera + voice items → packs | ⚪ |
| Personal notes in cook mode (FU-432) | 327–331 | 4 | 4/0/0 | 0 | | ⚪ |
| Cook Mode Chunks 1–3 (FU-096) | 333–344 | 11 | 10/0/1 | 0 | audible-beep item → audio pack | ⚪ |
| Cook Mode Chunk 5 (FU-100) | 346–356 | 10 | 8/1/1 | 1 | voice verbs → mic pack; "8 commands" count stale | ⚪ |
| Cook Mode Chunk 6 rescale (FU-101) | 358–369 | 11 | 10/1/0 | 0 | | ⚪ |

### Meal plans + Shopping lists

| Section | Lines | Items | A/V/H | Stale | Env / notes | Status |
|---|---|---|---|---|---|---|
| Meal reconcile (FU-317 C5) | 375–390 | 15 | 13/2/0 | 0 | past-dated plans; auto-drain both ways | ⚪ |
| Budget-defense swaps (FU-451) | 392–400 | 8 | 8/0/0 | 0 | money on; budget; over-budget week | ⚪ |
| Unlinked-ingredient warning (FU-505) | 402–408 | 6 | 6/0/0 | 0 | | ⚪ |
| Meals-per-week pref (FU-181) | 410–416 | 6 | 6/0/0 | 0 | | ⚪ |
| In-context Print (FU-338) | 418–422 | 4 | 4/0/0 | 0 | print VIEW opens = A | ⚪ |
| useListState sweep (FU-354/355) | 424–432 | 8 | 8/0/0 | 0 | Vitest spec exists; browser walks not pinned | ⚪ |
| Show-all-slots persistence (FU-306) | 434–440 | 6 | 6/0/0 | 0 | | ⚪ |
| Templates drawer (FU-308) | 442–449 | 7 | 7/0/0 | 0 | | ⚪ |
| Planner R-Phases 1–6 (FU-305) | 451–459 | 8 | 8/0/0 | 0 | | ⚪ |
| Meal Plans C-2 full walk (FU-179) | 461–476 | 15 | 15/0/0 | 2 | | ⚪ |
| Substitute-swap gating (FU-407) | 482–486 | 4 | 4/0/0 | 0 | | ⚪ |
| Put-away dialog (FU-452) | 488–500 | 12 | 12/0/0 | 0 | | ⚪ |
| Quick-add toast + pref (FU-316) | 502–510 | 8 | 8/0/0 | 0 | | ⚪ |
| Receipt-photo attachments (FU-334) | 512–524 | 12 | 10/0/2 | 0 | phone camera items → device pack | ⚪ |
| Image-source picker sweep (R-024) | 526–531 | 5 | 4/0/1 | 0 | camera item → device pack | ⚪ |
| Trim-to-budget + Deferred (FU-448) | 533–547 | 14 | 14/0/0 | 0 | money on; rich line mix | ⚪ |
| Shopping list UX v2 (FU-165) | 549–563 | 14 | 14/0/0 | 0 | | ⚪ |
| Cart Button C2 (FU-130) | 565–572 | 7 | 7/0/0 | 0 | | ⚪ |
| Cart Button C3 API (FU-132) | 574–580 | 6 | 6/0/0 | 0 | SQLite+PG | ⚪ |
| Cart Button C3 UI (FU-145) | 582–588 | 6 | 6/0/0 | 0 | | ⚪ |
| Cart Button C4 (FU-135) | 590–595 | 5 | 5/0/0 | 0 | | ⚪ |
| Snapshot-at-add (FU-142) | 597–603 | 6 | 6/0/0 | 0 | DB seed for NULL legacy line | ⚪ |
| P6-01 C3 lifecycle (FU-066) | 605–611 | 6 | 5/1/0 | 1 | finish flow superseded by UX v2 | ⚪ |
| P6-01 C4 new-list dialog (FU-068) | 613–623 | 10 | 9/1/0 | 0 | | ⚪ |
| P6-01 C5 selector (FU-069) | 625–633 | 8 | 7/1/0 | 2 | selector superseded by UX v2 rail | ⚪ |
| P6-01 C6 in-store + drag (FU-073) | 635–641 | 6 | 5/1/0 | 1 | drag fix re-covered by UX v2 L562 | ⚪ |
| C6 audit pricing (FU-072) | 643–645 | 2 | 2/0/0 | 0 | | ⚪ |
| P6-01 C7 shop day (FU-076) | 647–655 | 8 | 7/1/0 | 2 | chip/selector superseded by UX v2 | ⚪ |
| Chunk 2 picker + Shop-now (FU-060) | 657–662 | 5 | 5/0/0 | 1 | re-prompt superseded by FU-316 | ⚪ |

### Stock

| Section | Lines | Items | A/V/H | Stale | Env / notes | Status |
|---|---|---|---|---|---|---|
| Action-first scan mode (FU-378) | 668–680 | 11 | 11/0/0 | 0 | scanning_enabled; typed-entry = camera stand-in | ⚪ |
| Product unlink fix (FU-528) | 682–684 | 2 | 2/0/0 | 0 | test-pinned | ⚪ |
| Register barcode (FU-373) | 686–689 | 3 | 3/0/0 | 0 | scanning_enabled | ⚪ |
| Stocktake snooze 500 fix (FU-526) | 691–694 | 3 | 3/0/0 | 0 | test-pinned | ⚪ |
| Consumption events restored (FU-533) | 696–699 | 3 | 3/0/0 | 0 | test-pinned | ⚪ |
| Rename-to-own-name (FU-528) | 701–704 | 3 | 3/0/0 | 0 | test-pinned ×5 | ⚪ |
| Unlinked-ingredients page (FU-532) | 706–707 | 1 | 1/0/0 | 0 | test-pinned | ⚪ |
| Reconcile-queue pagination | 709–710 | 1 | 1/0/0 | 0 | test-pinned | ⚪ |
| Expiry-on-open prompt (FU-507) | 712–717 | 5 | 5/0/0 | 0 | | ⚪ |
| StockItem.image dropped (FU-508) | 719–723 | 4 | 4/0/0 | 0 | | ⚪ |
| Stocktake C3 settings + surfacing | 725–757 | 23 | 20/3/0 | 0 | admin + non-admin | ⚪ |
| Stocktake C2 runner rebuild | 759–814 | 36 | 36/0/0 | 0 | overdue queue seeded | ⚪ |
| Bulk Log waste (FU-226) | 816–825 | 8 | 8/0/0 | 0 | long-press emulation | ⚪ |
| Auto-add-on-low (FU-315/464/511) | 827–846 | 15 | 13/2/0 | 0 | Essential items; 0/1/2+ lists | ⚪ |
| ⭐ Zero-Input Pantry (P8-07) | 848–861 | 12 | 12/0/0 | 0 | purchase+cook history | ⚪ |
| 3-band StockLevel collapse | 863–872 | 9 | 9/0/0 | 0 | | ⚪ |
| P8-05 buy-verdict oracle | 874–885 | 10 | 10/0/0 | 0 | price history + waste events | ⚪ |
| P8-02 barcode via OFF | 887–897 | 9 | 9/0/1* | 1 | outbound net + block capability; *camera-decode fidelity untestable | ⚪ |
| History tab — retention/cap | 899–909 | 9 | 9/0/0 | 0 | fresh destructive reseed | ⚪ |
| History tab — event kinds | 911–924 | 11 | 11/0/0 | 0 | flask db downgrade leg | ⚪ |
| Stock pickers + Log Waste | 926–931 | 5 | 5/0/0 | 0 | | ⚪ |
| Recipe-ingredients deep-link (FU-109) | 933–940 | 7 | 7/0/0 | 0 | | ⚪ |
| Recipe card no dim (FU-109) | 942–944 | 2 | 2/0/0 | 0 | | ⚪ |
| Stock Item Detail C-1b + marquee (FU-202) | 946–972 | 26 | 22/4/0 | 4 | in-section supersessions — walk Round-2 versions | ⚪ |
| Detail + Overview feedback (FU-222) | 974–979 | 5 | 3/2/0 | 1 | | ⚪ |
| Overview C2 toolbar/filters (FU-121) | 981–990 | 9 | 9/0/0 | 2 | | ⚪ |
| Overview C4 expiry control (FU-123) | 992–998 | 6 | 6/0/0 | 0 | | ⚪ |
| Overview C5 responsive + long-press (FU-124) | 1000–1006 | 6 | 6/0/0 | 0 | | ⚪ |
| Offers sidecar (FU-230) | 1008–1009 | 1 | 1/0/0 | 0 | ingested offers; money on | ⚪ |

*(P8-02 H nuance: no checkbox isolates camera decode; typed entry covers all listed items — counted 9A + noted.)*

### Dashboard + Alerts + Settings

| Section | Lines | Items | A/V/H | Stale | Env / notes | Status |
|---|---|---|---|---|---|---|
| Draft my shop (FU-351) | 1015–1026 | 11 | 11/0/0 | 0 | | ⚪ |
| ⭐ Dora Score (P8-08) | 1028–1039 | 11 | 11/0/0 | 0 | waste/budget/expiry seed | ⚪ |
| Log-price quick action (FU-300) | 1041–1050 | 9 | 9/0/0 | 0 | | ⚪ |
| Stock donut deep-links (FU-299) | 1052–1061 | 9 | 9/0/0 | 0 | | ⚪ |
| Price-drops widget (FU-296) | 1063–1073 | 10 | 10/0/0 | 0 | products flag; historic offers | ⚪ |
| Dashboard rebuild walk (FU-301) | 1075–1083 | 8 | 5/3/0 | 0 | Playwright partially overlaps basics | ⚪ |
| Next to cook (FU-298) | 1085–1091 | 6 | 6/0/0 | 0 | | ⚪ |
| Budget money-gate (FU-297) | 1093–1096 | 3 | 3/0/0 | 0 | | ⚪ |
| Cards DnD reorder (FU-294) | 1098–1103 | 5 | 5/0/0 | 0 | | ⚪ |
| dashboard_layout backend (FU-292) | 1105–1108 | 3 | 3/0/0 | 0 | test-pinned | ⚪ |
| Alerts C-9.1 spine (FU-183) | 1114–1123 | 9 | 9/0/0 | 0 | | ⚪ |
| Cross-app undo push-expiry (FU-357) | 1125–1128 | 3 | 3/0/0 | 0 | | ⚪ |
| good_deal + fake-markdown (FU-450) | 1130–1134 | 4 | 4/0/0 | 0 | offers + observations | ⚪ |
| C-9.7 email digest (FU-205) | 1136–1144 | 8 | 6/1/1 | 2 | SMTP via admin page now (not env) | ⚪ |
| C-9.8 web-push (FU-206) | 1146–1157 | 10 | 10/0/0 | 2 | VAPID via admin page now (not env) | ⚪ |
| Data pages UI revamp (FU-359) | 1163–1168 | 4 | 4/0/0 | 0 | | ⚪ |
| FU-333 close-out C+D | 1170–1181 | 10 | 10/0/0 | 0 | env manipulation + restarts | ⚪ |
| FU-333 Bucket B (historical) | 1183–1190 | 6 | 6/0/0 | **6** | whole block self-declared superseded; salvage Voice/Hosting rows | 🗑 |
| Users admin Add/Delete (FU-461) | 1192–1208 | 15 | 15/0/0 | 0 | 2nd admin; DB SET NULL checks | ⚪ |
| Admin cache-race (FU-016) | 1210–1214 | 3 | 3/0/0 | 0 | two admins | ⚪ |
| Backup library (FU-342) | 1216–1227 | 11 | 11/0/0 | 1 | filesystem access | ⚪ |
| Image compression (FU-345) | 1229–1237 | 8 | 8/0/0 | 1 | | ⚪ |
| Import Options alignment (FU-344) | 1239–1242 | 3 | 3/0/0 | 1 | presentation superseded by FU-359 | ⚪ |
| Import templates (FU-343/349) | 1244–1251 | 7 | 7/0/0 | 1 | | ⚪ |
| Backup retention + path (FU-342) | 1253–1258 | 5 | 5/0/0 | 1 | | ⚪ |
| Data relocation (FU-341) | 1260–1267 | 7 | 7/0/0 | 2 | | ⚪ |
| FU-198 admin gate | 1269–1276 | 2 | 2/0/0 | 0 | | ⚪ |
| QR labels relocated (FU-340) | 1278–1283 | 5 | 5/0/0 | 0 | scanning_enabled | ⚪ |
| Email change + CSRF (FU-197) | 1285–1296 | 11 | 11/0/0 | 0 | links extractable server-side | ⚪ |
| Assistant banner/Test/docs (FU-330/331/332) | 1298–1316 | 18 | 18/0/0 | 0 | **owner pre-saves real API key once**; fake keys for failure paths | ⚪ |
| Assistant per-user config PR1 (FU-153) | 1318–1340 | 22 | 22/0/0 | 0 | partly test-pinned; owner-saved keys | ⚪ |
| Visual rebuild P3 cross-theme (FU-283) | 1342–1344 | 2 | 0/2/0 | 0 | pure V-pack | ⚪ |
| Phase 4 profile picture (FU-286) | 1346–1349 | 3 | 3/0/0 | 0 | partly test-pinned | ⚪ |
| VocabListEditor empty copy (FU-285) | 1351–1353 | 2 | 2/0/0 | 0 | | ⚪ |
| Speech toggle w/o SpeechSynthesis (FU-289) | 1355–1358 | 3 | 3/0/0 | 0 | CDP stub | ⚪ |
| API access page (FU-218) | 1360–1367 | 7 | 7/0/0 | 0 | curl bearer client | ⚪ |
| Decommission scraping (FU-186) | 1369–1371 | 2 | 2/0/0 | 0 | | ⚪ |
| Ingestion quarantine (FU-190) | 1373–1375 | 2 | 2/0/0 | 0 | ingestion key | ⚪ |

### Onboarding + Products + Build + Operator

| Section | Lines | Items | A/V/H | Stale | Env / notes | Status |
|---|---|---|---|---|---|---|
| FU-184 sell-copy honesty pass | 1381–1392 | 5 | 5/0/0 | 1 | | ⚪ |
| FU-195 starter-data picks | 1394–1410 | 16 | 16/0/0 | 0 | blank DB | ⚪ |
| Onboarding C-5.1–5.6 (FU-192) | 1412–1439 | 27 | 26/1/0 | **10** | heavy supersession by 07-12 story + de-persona | ⚪ |
| De-persona remaining (FU-210) | 1441–1449 | 8 | 5/3/0 | 1 | | ⚪ |
| Demo dataset toggle (FU-194) | 1451–1457 | 6 | 6/0/0 | 0 | | ⚪ |
| Expiring-soon window (FU-187) | 1459–1463 | 4 | 4/0/0 | 0 | assistant answering | ⚪ |
| Sell-copy honesty P3 gate (FU-184 dup) | 1465–1471 | 6 | 4/2/0 | 2 | largely duplicates 1381–1392 | ⚪ |
| My Products + Price History (FU-214) | 1477–1489 | 12 | 6/4/2 | 0 | + 3 PH residuals from FU-431 (not yet listed) | ⚪ |
| My Products Link (FU-208) | 1491–1493 | 2 | 2/0/0 | 0 | | ⚪ |
| PreferredBuy (FU-211) | 1495–1497 | 2 | 2/0/0 | 0 | | ⚪ |
| Preferred-buy hint (FU-215) | 1499–1501 | 2 | 2/0/0 | 0 | | ⚪ |
| Stock-item Prices (FU-213) | 1503–1506 | 3 | 3/0/0 | 0 | | ⚪ |
| Unit-cost rebase (FU-216) | 1508–1511 | 3 | 3/0/0 | 0 | | ⚪ |
| Windows desktop build (FU-327) | 1517–1528 | 8 | 7/0/1 | 0 | **this IS a Windows box — runnable**; audio item H | ⚪ |
| macOS desktop build (FU-327) | 1530–1540 | 7 | 0/0/7 | 0 | **blocked: no Mac** | ⚪ |
| Fresh-install bootstrap (FU-200) | 1542–1552 | 9 | 9/0/0 | 0 | blank DB; ADMIN_BOOTSTRAP_EMAIL | ⚪ |
| Docker/desktop voice bundling (FU-286) | 1554–1557 | 3 | 3/0/0 | 0 | Docker; WSL | ⚪ |
| Piper synthesis walk (FU-291) | 1559–1565 | 5 | 5/0/0 | 0 | Piper present | ⚪ |
| Piper auto-provisioning (FU-290) | 1567–1570 | 3 | 3/0/0 | 1 | wording only (FU-288 precondition met) | ⚪ |
| FK-index migration (FU-563) | 1576–1579 | 2 | 2/0/0 | 0 | populated DB; test-pinned (schema-match) | ⚪ |
| FK ondelete rebuild (FU-565) | 1581–1585 | 3 | 3/0/0 | 0 | populated DB; test-pinned | ⚪ |
| Product nullability (FU-564) | 1587–1591 | 3 | 3/0/0 | 0 | populated DB; test-pinned | ⚪ |
| gunicorn WSGI (FU-397) | 1593–1600 | 6 | 6/0/0 | 0 | **Docker/WSL only** (POSIX) | ⚪ |
| Dev seed under load (FU-388) | 1602–1607 | 4 | 3/1/0 | 0 | destructive reseed | ⚪ |
| Playwright CI re-run (FU-540) | 1609–1611 | 1 | 1/0/0 | 0 | blocked on FU-405 CI | ⚪ |
| Fresh-install migration boot (FU-549) | 1613–1614 | 1 | 1/0/0 | 0 | test-pinned; clean-venv leg manual | ⚪ |
| Companion push round-trip (FU-554) | 1616–1617 | 1 | 1/0/0 | 0 | dora-companion checkout (software) | ⚪ |
| Demo / showcase mode (FU-392) | 1619–1624 | 5 | 5/0/0 | 0 | env restarts; 2-min waits | ⚪ |
| Secure-cookies warning (FU-460) | 1626–1633 | 7 | 7/0/0 | 0 | HTTPS-front for one item | ⚪ |

### Cross-cutting

| Section | Lines | Items | A/V/H | Stale | Env / notes | Status |
|---|---|---|---|---|---|---|
| Menu bar border removed (FU-363 i6) | 1639–1642 | 2 | 1/1/0 | 0 | | ⚪ |
| Support channel (FU-370) | 1644–1651 | 6 | 6/0/0 | 0 | env restarts | ⚪ |
| Text-scale follow-through (FU-025) | 1653–1663 | 9 | 0/9/0 | 0 | flagship V-pack; computed-font-size could promote most to A | ⚪ |
| R-029 Product Search nav (FU-500) | 1665–1671 | 5 | 5/0/0 | 0 | | ⚪ |
| BaseButton sweep (FU-504) | 1673–1680 | 6 | 3/3/0 | 0 | | ⚪ |
| Security headers (FU-459) | 1682–1691 | 8 | 8/0/0 | 0 | curl | ⚪ |
| Recipe-picker toast (FU-319) | 1693–1695 | 2 | 2/0/0 | 0 | | ⚪ |
| Help chips (FU-503/044) | 1697–1717 | 17 | 17/0/0 | 0 | ~14 surfaces seeded | ⚪ |
| iOS/macOS audio-unlock (FU-287) | 1719–1729 | 7 | 1/0/6 | 0 | → Apple device pack | ⚪ |
| Filters toolbar alignment (R-027) | 1731–1737 | 6 | 6/0/0 | 0 | getBoundingClientRect | ⚪ |
| C-19 auth-shell (FU-540-adjacent) | 1739–1759 | 20 | 13/7/0 | 0 | Playwright covers login/nav, not visuals | ⚪ |
| P8-01 rename sweep | 1761–1766 | 5 | 5/0/0 | 0 | | ⚪ |
| D.O.R.A. easter egg | 1768–1772 | 4 | 4/0/0 | 0 | | ⚪ |
| Nav-state policy (A8 §3) | 1774–1780 | 6 | 6/0/0 | 0 | | ⚪ |
| /data/barcodes redirects (FU-340) | 1782–1786 | 4 | 4/0/0 | 0 | | ⚪ |
| /data/export retired (FU-339) | 1788–1795 | 7 | 7/0/0 | 1 | card-count half of L1789 stale | ⚪ |
| Settings dual scroll | 1797–1803 | 6 | 6/0/0 | 0 | | ⚪ |
| Mobile header wordmark | 1805–1809 | 4 | 4/0/0 | 0 | | ⚪ |
| Menu indicator colour fix | 1811–1815 | 4 | 2/2/0 | 0 | | ⚪ |
| Header peer buttons | 1817–1828 | 11 | 10/1/0 | 0 | | ⚪ |
| Sign-out in Settings header | 1830–1836 | 6 | 6/0/0 | 0 | | ⚪ |
| R-016 lazy hydration (FU-221) | 1838–1841 | 3 | 3/0/0 | 0 | | ⚪ |
| R-016 extension ×5 stores | 1843–1850 | 7 | 7/0/0 | 0 | | ⚪ |
| DnD affordance parity (FU-326) | 1852–1858 | 6 | 6/0/0 | 0 | | ⚪ |
| Error-handling rollout (FU-099-V) | 1860–1866 | 6 | 6/0/0 | 0 | kill API mid-save | ⚪ |
| formatQuantity rollout (FU-321) | 1868–1873 | 5 | 5/0/0 | 0 | | ⚪ |
| Unsaved-changes guard (FU-322) | 1875–1879 | 4 | 4/0/0 | 0 | FU-539 suite covers guard logic | ⚪ |
| Chunks 3–5 query paths (FU-051) | 1881–1890 | 9 | 9/0/0 | 0 | server side test-pinned | ⚪ |
| C-cross C1 feature flags (FU-110) | 1892–1902 | 10 | 9/1/0 | 2 | toggle-count + health-keys enumerations stale | ⚪ |
| C-cross C2 money opt-in (FU-111) | 1904–1914 | 10 | 9/1/0 | 0 | | ⚪ |
| C-cross C3 nutrition (FU-112) | 1916–1929 | 13 | 12/1/0 | 0 | | ⚪ |
| C-cross C5 image opt-in (FU-114) | 1931–1945 | 14 | 13/1/0 | 0 | | ⚪ |

---

## Appendix A — Human/hardware packs (40 items)

Grouped so each pack is one sitting with one device.

**Pack 1 — Android device (~12 items):** Native Android build section L51–60
(9 items: Studio/Gradle sync, APK install + icon, setup gate, endpoint change,
camera barcode scan, cook/shop wake-locks, push-unsupported); PWA share target
L166; recipe camera capture L316; receipt-photo camera L515–516; image-picker
camera L528; store-logo camera L69; Android voice-output spot-check L1728 (half).

**Pack 2 — iPhone/iPad (~6 items):** home-screen icon L108; Safari pinned-tab
L109 (low priority, legacy); iOS audio-unlock L1723–1726 (4 items: reply plays,
browser voice engine, cook narration, timer tone).

**Pack 3 — macOS (7 items, BLOCKED — no Mac):** macOS build script section
L1534–1540 + WKWebView audio checks L1727. Park until a Mac is available or
consciously accept as untested at launch.

**Pack 4 — mic / voice / audio on this desktop (~5 items):** currency-locale
speech recognition L46; Sous Chef voice verbs L354 + standalone timer via voice
L319; cook-mode beep audible L338 (fires = agent; audible = you);
Windows-desktop narration audio L1525.

**Pack 5 — misc human (~10 items):** browser Install-prompt UX L103 (agent
proxies via manifest + beforeinstallprompt); email digest arrives in a real
inbox L1141 (content verifiable server-side first); FU-214 product-scope
decisions L1481–1482 (owner calls, not QA); reduced-motion OS-level L20 if
DevTools emulation isn't accepted as equivalent.

## Appendix B — Eyeball (V) walkthrough packs (66 items)

Agent pre-stages + screenshots; owner judges. Natural bundles:

- **Text-scale pack (9):** FU-025 section L1655–1663 — Small vs XL across stock
  overview/detail, recipe edit, DoraScore, cookbook FilterBar, shopping detail,
  cook mode; icons deliberately don't scale.
- **Theme-read pack (~20):** three-theme reads scattered everywhere — L247, 263,
  356, 386–387, 611, 623, 633, 641, 655, 752/756/757, 963, 977, 1137, 1343–1344,
  1902, 1914, 1929, 1945. One staged sweep per theme, screenshots grouped per
  surface. (Feeds FU-010/FU-224 signal collection.)
- **Animation/feel pack (~10):** DoraTabs wobble L953, pulse halo L752, hover-bob
  L35-adjacent, menu-indicator slide L1814–1815, header ring fade L1826, auth
  mascot pulse L1740–1741, drag ghosting.
- **Layout/copy pack (~27):** breathing-room / not-squished / copy-tone items —
  L369, 836, 843, 952, 968, 975, 1077, 1082–1083, 1427, 1442, 1447–1448,
  1470–1471, 1480, 1484, 1486, 1488, 1605, 1641, 1676, 1678, 1680, 1743, 1749,
  1755–1756, 1759.

## Appendix C — Stale-suspect items (61) — owner decides delete/rewrite

Each verify session should confirm + action its batch's entries; the whole-block
ones below can be decided up front.

**Whole blocks recommended for deletion (18 items):**
- **FU-333 Bucket B, L1183–1190 (6):** block's own preamble says the close-out
  block above supersedes it. Salvage: fold the Voice/Hosting page rows
  (L1189–1190) into the close-out walk. → 🗑
- **Onboarding C-5.3 persona block, L1428–1433 (6) + L1413, 1421, 1423, 1438
  (4):** superseded by the 2026-07-12 story pass + FU-210 de-persona (persona
  chips, auto-advance, Skip label, personaPreview field all gone). → 🗑
- **Chunk 7 URL-importer items, L212–215 (4):** the URL importer was deleted by
  the paste-based rebuild (L178 pins the 404). Keep L209/216/217 (migration,
  legacy source, backup round-trip). → 🗑

**Item-level rewrites/deletes (43 + 1 found in pilot):** with evidence, by batch —
- L91 — example password `abcdefgh` is itself on breach lists, so the check can
  never pass as written (pilot-verified: 422 breach rejection). Rewrite with a
  non-breached letters-only example (e.g. `zxqvbnmk`); the intent (no digit
  rule) is confirmed working.
- L57 — scan now opens stock item, add-flow retired (FU-378). Rewrite.
- L202–203 — HowToStep/HowToSection import went with URL importer. Delete.
- L274 — command palette CUT; keep `g r` half. Rewrite.
- L337 — "8 commands" count wrong post-Done-removal (L354). Rewrite count.
- L470 — contradicted by L471 (Jump-to-plan dropdown gone). Delete.
- L475 — templates page now Sets-only (FU-308, L446). Rewrite.
- L607 — finish flow reworked by UX v2 (L555). Delete.
- L628, 633 — selector replaced by UX v2 rail/dropdown (L550–551). Delete.
- L639 — re-covered by UX v2 L562; verify once. Delete.
- L648, 654 — shop-day chip + selector sort superseded (L550–553). Delete.
- L658 — re-prompt semantics reworked by FU-316 (L506–510). Delete.
- L947 — contradicted by C-1b.1 Round-2 (L958–959). Walk Round-2 version.
- L960 — auto-add toggle collapsed by FU-511 (L846). Rewrite.
- L968 — references dropped StockItem.image (FU-508). Rewrite.
- L971 — auto-add footer count retired (L845). Rewrite.
- L978 — Auto-add retired + Flagged→Essential rename. Rewrite.
- L982 — Scan hidden unless scanning_enabled. Add precondition.
- L989 — footer enumeration stale (auto-add/Essential). Rewrite.
- L897 — StockItem.image path gone (FU-508). Delete assertion.
- L1138, 1141 — SMTP/PUBLIC_URL env vars removed by FU-333; config via admin
  pages, no restart. Rewrite setup steps.
- L1148–1149 — VAPID env gating gone (FU-333). Rewrite setup steps.
- L1226, 1230, 1240, 1245, 1254, 1262–1263 — presentation wording superseded by
  FU-359 revamp; behaviour halves live. Rewrite.
- L1391 — persona preview deleted 07-12. Delete.
- L1447 — persona chips removed entirely. Delete.
- L1466, 1471 — PERSONA_PREVIEWS/LOOP_INSIGHT deleted; question moot. Delete.
- L1570 — "when scripts land per FU-288" — landed (FU-327). Drop precondition.
- L1789 — `/data` card count now two (L1784). Rewrite count half.
- L1894, 1898 — feature-toggle count + health-key enumeration outgrown
  (products flag, demo_mode). Verify named keys, drop exhaustiveness.

## Appendix D — Standing constraints for verify sessions

- **Credentials:** agent never types real API keys/passwords. Owner pre-saves
  paid-provider LLM keys once (Settings → Assistant); failure paths use
  obviously-fake keys. Test accounts use throwaway credentials recorded in the
  session report.
- **Destructive ops:** fresh-install / reseed checks (`DORA_ALLOW_DESTRUCTIVE`)
  run against a **copy** of the dev DB or an explicitly disposable one — never
  the owner's live dev data without asking.
- **App launch:** `.claude/launch.json` has `dora-backend` (:5170) and
  `dora-spa` (:5174). **Do not verify against the repo-root `dora.data.db`** —
  it's a stale `create_all` artifact with no `alembic_version` (see FU-570 and
  the pilot caveat). First step of every verify session: point the backend at
  the **dedicated disposable verify DB** (fresh file + `alembic upgrade head` +
  FU-388 dev seed), e.g. via `DORA_DB_PATH` in the backend's environment.
  Pilot-created test accounts in the root DB: `qa-admin` /
  `dora-qa-admin-2026` (admin), `qa-user-1`/`zxqvbnmk`, `qa-user-2`/
  `passphrase please` — owner may delete at leisure.
- **Vue form automation:** programmatic `form_input`/typed keystrokes don't
  reliably reach Quasar v-models in the preview pane; use the native-setter +
  `input`-event injection pattern (worked everywhere in the pilot).
- **Preview-pane limits (2026-07-16 session 2):** the pane tab is *hidden* —
  no paint, no rAF, screenshots time out. Vue `<Transition>`-gated content
  (route swaps after the first; StockItemDetail's skeleton→content fade) never
  mounts. Partial fix: stub `requestAnimationFrame` with setTimeout + inject
  `*{transition:none!important;animation:none!important}` after boot — fixes
  top-level route swaps only. **Use the Playwright runner for real UI walks**
  (repo already has it: `web_app` `test:e2e`, FU-540); pane is fine for
  API checks, cold-load single views, and DOM instrumentation. App router is
  **hash mode** (`/#/stock`), and the SPA default route on plain URLs.
- **Verify fixtures in the DB:** "QA Verdict Cheese" + "QA verdict shop 1–3"
  (see Batch 0 continuation) — reusable for BuyVerdictCard; delete whenever.
- **Postgres leg:** `compose.dev.yml` PG + `DORA_TEST_DB=postgres`; batch 19.
- **Built-PWA checks:** `quasar build -m pwa` + `quasar serve` or the Docker
  image; batch 17.
- Line refs in this doc = 2026-07-16 snapshot of DORA_VERIFY.md.
