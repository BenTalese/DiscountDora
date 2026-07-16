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
6. Fails → new `DORA_FOLLOWUPS.md` entries (type=finding). Passes → tell the
   owner; **he deletes the items from DORA_VERIFY.md** (his file, his delete).
7. Flip the batch's status here and log the unit in `DORA_WORKLOG.md`.

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
| 0 | **Pilot** — Password policy + SettingsFileDrop + BuyVerdictCard + Runtime backend URL | 71–99, 111–115, 82–89 | 22 | 🟡 (this session) |
| 1 | Top block remainder — Onboarding story, Dora bubble, Currency & locale, Stores logo, PWA-dev-checkable parts | 11–49, 63–70 | ~40 | ⚪ |
| 2 | Stock A — recent fixes + stocktake redesign (668–814) | 668–814 | ~120 | ⚪ |
| 3 | Stock B — remainder (816–1009) | 816–1009 | ~115 | ⚪ |
| 4 | Cookbook A — filters, free-text, importer, DnD (132–195) | 132–195 | ~53 | ⚪ |
| 5 | Cookbook B — chunk sections + image-steps (197–321) | 197–321 | ~120 | ⚪ |
| 6 | Cook mode (327–369) | 327–369 | ~36 | ⚪ |
| 7 | Meal plans (375–476) | 375–476 | ~83 | ⚪ |
| 8 | Shopping lists A — recent (482–563) | 482–563 | ~69 | ⚪ |
| 9 | Shopping lists B — cart button + P6-01 chunks (565–662) | 565–662 | ~75 | ⚪ |
| 10 | Dashboard (1015–1108) | 1015–1108 | ~75 | ⚪ |
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

Notes:
- **FU-214** (open FU) rides on batch 14 — its product-surface browser-verify pass
  plus the 3 Product-History residuals folded in by FU-431 (2026-07-16).
- **FU-010 / FU-224** (theme + colour review FUs) collect signal from every
  V-pack walk — note anything relevant in reports.
- Batch 19/20 overlap heavily with automated migration tests (FU-536/549/563–565
  schema-match + from-empty chain); the residual manual value is the
  populated-DB / real-toolchain legs only.

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

**Item-level rewrites/deletes (43):** with evidence, by batch —
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
  `dora-spa` (:5174). SQLite dev DB at repo root.
- **Postgres leg:** `compose.dev.yml` PG + `DORA_TEST_DB=postgres`; batch 19.
- **Built-PWA checks:** `quasar build -m pwa` + `quasar serve` or the Docker
  image; batch 17.
- Line refs in this doc = 2026-07-16 snapshot of DORA_VERIFY.md.
