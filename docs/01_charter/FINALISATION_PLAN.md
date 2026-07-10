# Finalisation Plan — Dashy Dora

**Status:** 🔵 designed, not started
**Owner:** the last stretch of the project, before Phase 4 launch readiness closes out.
**Companion register:** [FINALISATION_COVERAGE.md](FINALISATION_COVERAGE.md) — the
per-chunk × per-track status matrix. Update it every session; it's what makes
"nothing was skipped" auditable.

---

## 1. Why this exists

Several late-game jobs share the same shape: **walk the entire codebase feature-
by-feature, and from that walk produce a small set of end deliverables.** Doing
each one as its own separate cross-cutting pass duplicates the walk and lets
things fall through the cracks between passes. This plan bundles them into one
disciplined sweep so each chunk of the code is read once, deeply, and every
track is advanced from the same reading.

The four tracks built up in parallel per chunk:

1. **Full Systems Test (FST) procedure** — a manual walkthrough document the
   user follows to verify the whole app end-to-end from multiple perspectives,
   living at [../04_proposals/FULL_SYSTEMS_TEST.md](../04_proposals/FULL_SYSTEMS_TEST.md)
   (to be created on first chunk).
2. **In-app help & guides content** — plain-English behaviour docs for every
   feature, landing on `HelpPage.vue` + the `(?)` help chips + DoraBot answers.
   Resolves [[FU-361]] + [[FU-320]].
3. **Senior code review findings** — a running assessment doc capturing bugs,
   dead code, refactors worth the churn, and library-vs-hand-rolled verdicts.
   Resolves [[FU-395]] and folds in the Phase-1 (assessment) half of
   [[FU-510]]. Lives at
   [../05_investigations/FINALISATION_REVIEW.md](../05_investigations/FINALISATION_REVIEW.md)
   (created on first chunk).
4. **Test plan** — for every chunk, list the unit / integration / e2e tests
   that *should* exist to protect the surface long-term. **Do not write the
   tests** in this pass; capture enough that they can be written cold later.
   Feeds [[FU-519]] / [[FU-520]].

Each chunk also cross-checks the four tracks against the shipped `(?)` help
chips (FU-503/044), the state-ownership audit
(`STATE_OWNERSHIP_REFACTOR_PROPOSAL.md`), and the engineering standards
(`ENGINEERING_STANDARDS.md`).

---

## 2. Scope discipline (what this plan is not)

- **Not** a fresh design pass. Anything that would rewrite a feature belongs
  in a new proposal doc, not here. If a senior-review finding is large enough
  to need design, log it as a new `FU-NNN` and keep walking.
- **Not** the browser-verify pile. `DORA_VERIFY.md` stays the user's manual
  walk list; the FST doc is different — it's the *reproducible protocol* the
  user (or a fresh collaborator) follows on a near-final build to certify
  release-readiness. FST rows will *become* verify items when picked up.
- **Not** a documentation project for internal architecture. The Help track
  is user-facing copy only. Architecture stays in the charter + proposal docs.
- **Not** a bulk refactor. Findings get logged; whether to act on them is a
  separate decision per finding, sequenced by risk + blast-radius.

---

## 3. The four output tracks — formatting rules

### 3.1 FST document (`04_proposals/FULL_SYSTEMS_TEST.md`)

The document is a **persona × surface × condition** matrix, rendered as
walkthrough scripts the user can follow with the app open.

**Personas** (all covered before we ship):

| Persona | Represents |
|---|---|
| **Fresh install / first-time user** | Empty DB, onboarding not run, no data, no prefs. Cold discovery. |
| **Dense / long-tenure user** | ~1 year of data — many stock items, several open lists, hundreds of recipes, full price history. Perf + information density under load. |
| **Minimal user** | Runs the loop but ignores optional features (no LLM, no scanning, no email/push, no substitutes recorded). Tests hide-when-off (R-029) is real. |
| **Power user** | Everything on — LLM configured, notifications wired, all opt-ins enabled, using shortcuts (`g s`, `?`, etc.). Tests advanced surfaces don't collide. |
| **Admin** | The only user in a household who edits install-wide settings (Currency/locale, Stocktake, Reconcile, Notifications, LLM master, Image compression, Import templates, Backup library, Kitchen setup, QR labels). |
| **Multi-user household** | Two accounts on the same install with separate `AppSetting` where the setting is per-user; shared where install-wide. Tests per-user vs install-wide boundaries. |
| **Self-host operator** | Docker/desktop-bundle deployment; walks the `2` remaining env vars, backup/restore, migration up/down. |
| **Managed / Path-B** | Runs the same artifact behind a managed URL; auth flows, redirects, PWA install path. |

**Devices / conditions** (applied as row-modifiers, not their own personas):

- Android PWA (Chrome, installed from banner) + native Capacitor build (P8-10).
- Desktop installer (Linux `.deb`, Windows `.msi`, macOS `.dmg`, per `packaging/`).
- iOS PWA (Safari, Add to Home Screen) — voice-unlock gotcha (FU-287).
- Bad network — throttled to slow-3G / offline (offline queue, service worker
  fallback, sync-when-back).
- Small viewport (360×640) vs desktop wide (1920+).
- All five themes × light/dark toggle (feeds FU-010 ride-along).
- Reduced-motion + high-contrast OS preference on.

**Surface sections** — one per feature chunk (§4). Each section:

1. **Preconditions** — what state the persona/device must be in.
2. **Golden path** — steps + expected result, with the persona named.
3. **Edge cases** — one bullet per known edge (permission denial, empty state,
   validation failures, race conditions, offline mid-write, session expiry).
4. **Persona coverage matrix** — a tick-table showing which of the 8 personas
   this section applies to (some surfaces are admin-only; some don't render
   for minimal users).
5. **Condition matrix** — which device/condition modifiers are load-bearing
   for this surface.

The document ends with a **release-gate checklist**: the small set of "before
tagging a release, tick these" rows — the outputs of the FST used as a launch
tollgate. This is what fulfils [[FU-395]] and the FST portion of [[FU-406]].

### 3.2 Help content (`HelpPage.vue` / `(?)` chips / DoraBot corpus)

Content per feature chunk follows the same shape everywhere:

1. **What it does** — one plain sentence.
2. **When it fires / how to trigger it** — user action or auto-trigger.
3. **What controls it** — link to the exact setting toggle (relative
   `/settings/...` URL). **Never** "the app does this" with no escape hatch —
   FU-320 rule.
4. **What it costs / what it might get wrong** — honesty about limits (P3
   Honest tie-break).
5. **Related** — cross-links to adjacent help rows.

For every auto-behaviour catalogued in
`docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md`, the chunk that owns the
surface writes the corresponding help entry. The completed set is the
receipt that closes [[FU-320]].

FAQ / navigation / screenshots (the other 4 bullets in `COVERAGE_GAPS.md`
A-4) land as their own sub-passes after the per-feature content is written.

### 3.3 Senior review (`05_investigations/FINALISATION_REVIEW.md`)

Per chunk, one section with these buckets:

- **Bugs** (verified reproducible or high-confidence latent). Each gets a
  new `FU-NNN` opened immediately with an "urgent" recommended resolution.
- **Refactors worth doing** — non-load-bearing improvements. Log to
  `DORA_FOLLOWUPS.md` with a state note "sequence after finalisation review
  closes". Do not action inline.
- **Dead code / unused fields** — kept as a running list; action as one
  batch at plan close (cheaper than per-chunk tidy).
- **Hand-rolled-vs-library verdicts** — per the [[FU-510]] Phase 1 shape:
  what it is · what would replace it · verdict `keep` / `replace` /
  `wrap-thin-adapter` · effort/risk. Charter tie-breaks
  (Effortless + Anti-creep) are load-bearing — don't default to "prefer
  library". Each `replace` verdict spawns a follow-on FU at close.
- **Standards drift** — every `R-0NN` violation found becomes an inline
  comment (fix), a rule-cited exception (explain), or a follow-up (defer),
  per the standards close-gate rule in `CLAUDE.md`.
- **Ride-along signals for [[FU-010]] / [[FU-224]]** — anything about
  theme / colour / visual polish gets logged against those FUs so the
  eventual look-and-feel pass has a starting shortlist. Do not resolve
  either FU from here (they need eyes-on-app judgement, not a code walk).

### 3.4 Test plan (`04_proposals/TEST_PLAN_INVENTORY.md`)

Per chunk, one table with:

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| e.g. `test__cook_recipe__decrements_pool_via_bump_pool` | e2e | **must-write-before-ship** | The pool R-003 invariant is critical for FU-317. |
| e.g. `test__useCookMode__preserves_step_position_across_reload` | vitest | nice-to-have | Cook mode has no vitest coverage; low blast-radius. |
| e.g. property `cookable ⇒ every ingredient in stock` | hypothesis | nice-to-have | Feeds [[FU-520]]. |

**Priority cap:** the "must-write-before-ship" bucket is expected to be
small — regression tests for the loop spine + anything the senior review
flags as fragile. Everything else is "nice-to-have"; that's the honest
bucket. Do not padre the must-write list.

At close, "must-write-before-ship" rows are opened as their own FUs and
sequenced into [[FU-519]]; "nice-to-have" rows accumulate against
[[FU-520]] as a menu.

---

## 4. Feature chunks (walk order)

Ordering is **loop spine → adjacent surfaces → infrastructure**. This gets
FST persona scripts hanging off the surfaces the personas actually spend
time on first.

| # | Chunk | Rough scope |
|---|---|---|
| 1 | **Cookbook** | Recipes CRUD, import (paste + share target), Recipe Detail, tags, favourites, cookability, meals-worth, cost estimate. |
| 2 | **Meal Plans** | Board / Calendar / Templates, Shortfall, Reconcile (FU-317), Suggestions signposts. |
| 3 | **Shopping Lists** | DRAFT→SHOPPING→DONE, auto-add hooks (FU-315), remembered-list, cheapest chip (FU-318 pending), substitute swap (FU-407), templates, copy, batch actions. |
| 4 | **Cook Mode** | Sous Chef, hands-free, wake-lock, personal notes (FU-432), consume-on-finish (FU-449). |
| 5 | **Stock Overview + Stocktake** | 3-band level, buy-verdict badges, filters, `Needs check`, Stocktake runner + Push/Mute, waste log. |
| 6 | **Stock-Item Detail** | Overview, prices, offers, expiry, substitutes, images, history, per-item settings. |
| 7 | **Zero-Input Pantry (P8-07)** | Belief chip, quick-checks, per-user opt-out, `/beliefs`. |
| 8 | **Dashboard** | Kitchen zone (Dora Score / Reconcile chip / stocktake pulse / draft-shop), Money zone (Budget / Deals / Price Drops / Log price), quick actions. |
| 9 | **Alerts + Suggestions** | ALERT_ROUTER, digest, push, snooze, alert prefs, suggestions generator + snooze prune (FU-513). |
| 10 | **Products / History / Deals** | Products overlay, Product Search, Product History, offers, price entry, Your Prices. |
| 11 | **Assistant (Dora)** | Basic + AI paths, tool registry, mode toggle (FU-360), rate limits, prompt-injection defence (FU-515), eval suite (FU-390). |
| 12 | **Reports / Memory (P8-09)** | `/reports` sections, meals cooked, spend-by-category, YoY, ranges (2y/5y). |
| 13 | **Settings shell** | Account, Kitchen setup, Admin (Currency/locale, Stocktake, Meal reconciliation, Assistant, Notifications, Email, Import, Backup & restore, System features, Theme). |
| 14 | **Onboarding** | Fresh-install flow, per-name picks, paste-rows, seed-items (FU-514 fix). |
| 15 | **Auth shell** | Login / register / reset / setup-admin / change-email / password policy (FU-442), CSRF (FU-197), rate limits. |
| 16 | **Ingestion API + companion seam** | `/api/ingest` bearer lane, admin keys page, standalone companion round-trip. |
| 17 | **Offline / PWA / native** | Service worker (FU-336 — first!), install banner, offline queue, wake-lock, Capacitor Android/iOS shells, backend-URL runtime picker. |
| 18 | **Backup & restore + Import** | Library, restore-preview, credential exclusion (FU-387), CSV templates (FU-343/348), the two data pages' shared design language (FU-359). |
| 19 | **Ops / self-host** | The `2` env vars, migrations up/down (SQLite + Postgres), desktop first-run, log rotation, APScheduler jobs, security-audit.sh. |
| 20 | **Cross-cutting concerns** | i18n/locale/currency (FU-043), text-scale + component-internal text (FU-025), theme system (feeds FU-010), color-usage patterns (feeds FU-224), keyboard shortcuts + cheatsheet, PWA shortcuts. |

Chunk numbering is stable — the coverage register uses it. New chunks
added later (e.g. Phase 4 tenancy) become 21+, they don't renumber.

---

## 5. How to run a chunk (per-session recipe)

1. **Open [FINALISATION_COVERAGE.md](FINALISATION_COVERAGE.md).** Pick the
   top unstarted chunk. Confirm with the user before starting.
2. **Assemble the reading list** (anti-drift rule from `CLAUDE.md`):
   - The relevant proposal/impl-plan under `04_proposals/`.
   - The relevant `01_charter/` anchors (Champion Plan, Reconciled §5,
     Engineering Standards).
   - The relevant `02_feedback/` bullets for the surface.
   - Any open FU on that surface.
3. **Read the code**, front to back, for the chunk. Backend features first,
   then SPA components/pages, then tests. Grep every entry point.
4. **Advance all four tracks in the same pass** — don't split them. Follow
   the formatting rules in §3.
5. **Update the coverage register** with the chunk's row set to ✅ and the
   date; write a one-line "what came out of it" note (link the sections
   added to each track doc).
6. **Standards close-gate** (per `CLAUDE.md`) — every `R-0NN` violation
   surfaced is fixed / explained / logged.
7. **Worklog entry** on session end.

Expect **one chunk per session** at most for the loop spine chunks
(1-9) and Assistant/Settings (11/13). The smaller chunks (5→6 sub-splits,
7, 14, 16, 18) may pair up. Do not batch more than two chunks in a session
— the review track loses depth.

---

## 6. Followups rolled into this plan

Marked here as **fully rolled in**, **partially rolled in**, or
**ride-along**.

**Fully rolled in — closed 2026-07-10, plan is the sole tracker:**

- **FU-361 A-4 Help content overhaul** → Track 2 (Help & guides).
  Moved to `DORA_FOLLOWUPS_RESOLVED.md` 2026-07-10.
- **FU-320 Document every auto-behaviour + link its setting** →
  Track 2 formatting rule §3.2. Moved to `DORA_FOLLOWUPS_RESOLVED.md`
  2026-07-10.
- **FU-395 P5-11 Production readiness review** → Track 3 (Senior
  review) + the FST release-gate checklist. Moved to
  `DORA_FOLLOWUPS_RESOLVED.md` 2026-07-10.

**Partially rolled in — corresponding FU stays open:**

- **[[FU-510]] hand-rolled vs library sweep** — Phase 1 (assessment)
  rolled into Track 3 as a per-chunk `keep / replace /
  wrap-thin-adapter` bucket. **Phase 2 (per-swap actions) stays open**
  — this plan produces the shortlist, doesn't ship the swaps. Each
  `replace` verdict spawns its own per-swap FU at plan close.

**Partially rolled in — cross-referenced, corresponding FU stays open:**

- **[[FU-406]] P7-10 Launch readiness** — the FST doc + release-gate
  checklist cover the *QA half*. Marketing / legal / on-call / incident
  channels do not fit code-traversal; those stay in FU-406.
- **[[FU-404]] P7-08 Compliance** — the FST persona flows will *exercise*
  the privacy policy, DSAR export, and delete surfaces (multi-user + admin
  personas). Legal drafting + the compliance contract itself do not fit
  here.

**Ride-along — not resolved, but every chunk feeds them:**

- **[[FU-010]] Late-game holistic theme / colour review** — Track 3
  captures every theme/color anomaly against this FU. Actual resolution
  needs eyes-on-the-running-app at close.
- **[[FU-224]] App-wide colour-usage assessment** — same treatment;
  Track 3 collects every `color="secondary" | info | accent` site
  worth reconsidering as we walk.

Follow-on FUs opened by this plan (opened at plan close, not before):

- Every "must-write-before-ship" test row → new FU each, sequenced into
  [[FU-519]].
- Every "replace" verdict from Track 3 → new per-swap FU per
  [[FU-510]] Phase 2.
- Every bug found → new urgent FU at discovery (don't wait for close).

---

## 7. Definition of done for the plan

This plan closes when:

1. Every chunk in §4 shows ✅ in
   [FINALISATION_COVERAGE.md](FINALISATION_COVERAGE.md) across all four
   tracks (some tracks may be `N/A` for a chunk — e.g. ops chunks may
   have no in-app help — but every cell has an explicit value).
2. The FST document has been walked once end-to-end by the user on a
   near-final build, and the release-gate checklist is green.
3. The Help content is deployed and the `(?)` chips + HelpPage + DoraBot
   corpus reflect it.
4. The senior review has been triaged: every `replace` / refactor /
   dead-code item is either fixed, opened as an FU with a resolution
   point, or explicitly waived with reasoning in the doc.
5. FU-361 / FU-320 / FU-395 are already in `DORA_FOLLOWUPS_RESOLVED.md`
   (closed 2026-07-10 when this plan was drafted; the plan is their
   sole tracker). At plan close, FU-510 gets a state note there marking
   Phase 1 done; Phase 2 stays open. FU-406 + FU-404 get state notes
   ("finalisation plan covered the FST/exercise portion; remaining
   scope: X").
6. The plan doc itself gets a "Closed" banner + a link from
   `PROJECT_STATE.md` moves from the workstreams table to the
   "recently shipped" section.
