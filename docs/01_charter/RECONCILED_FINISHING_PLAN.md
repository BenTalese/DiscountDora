# Reconciled Finishing Plan — Dashy Dora

**Status:** Active — all decisions resolved (§7). This is the finishing plan; the rest of the doc set feeds it.
**Date:** 2026-06-04
**Reconciles:** the planning library (00_DOCS_INDEX, PROMPT_PLAN 1–7, DASHY_DORA_CHAMPION_PLAN/Part 8, COMMERCIALIZATION_REPORT, STATUS) · the code (CHANGELOG + current state) · your `Feedback / Fixes (MASTER).md` · the proposals & prompt pack generated this session.

---

## 0. How to use these documents (orchestration map)

**Start here (this doc)** = the master: strategy, resolved decisions (§7), and the phase sequence (§5). It governs *order and scope*. Everything below feeds it.

| Document | Role | Use it when |
|---|---|---|
| **RECONCILED_FINISHING_PLAN.md** (this) | Master — phases, decisions, in/out of scope | Always first; the arbiter |
| `FEEDBACK_TRIAGE_AND_PLAN.md` | Feedback → work mapping (cross-cutting themes, bug clusters, per-item detail) | To see *why* a task exists / trace a feedback point |
| `prompts/` (+ `prompts/00_INDEX.md`) | Executable units — runnable prompts per task | To *run* a task |
| `SHOPPING_LIST_REDESIGN_PROPOSAL.md` | Design for P6-01/06/07 (Phase 1) | Designing the shop/restock loop |
| `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` | Server-owned derived state (Phase 1 enabler) | Before P6 features + the assistant refactor |
| `DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md` | One capability registry (Phase 1/3) | Untangling the assistant; pairs with state-ownership |
| `MULTI_USER_READINESS.md` | Pre-flight for households/tenancy (Phase 4) | Before any multi-user work |
| `AUTH_ASSISTANT_SECURITY_FINDINGS.md` | Security fixes (CSRF/email → Phase 0; rest → Phase 4) | Phase 0 hardening + pre-sale |
| `PROJECT_STATE.md` (register) + `PROMPT_PLAN_*`, `DASHY_DORA_CHAMPION_PLAN.md`, `COMMERCIALIZATION_REPORT.md` | The underlying vision/spec: the Charter, Part 6/7/8 tasks | For the source spec behind a phase |

**Orchestration order:** Phase 0 → run `prompts/` Waves A + B + INV (incl. INV-6). Phase 1 → the loop: state-ownership enabler first, then shopping-list + cook-mode, each gated by its C-brief/proposal. Phase 2 → extract scraper + build the ingestion API (§6.6). Phase 3 → champion (Part 8). Phase 4 → commercialize (Part 7).

**Vocabulary:** the prompt pack says "Wave A/B/C"; this plan says "Phase 0–4". **Wave A + B + INV = Phase 0; Wave C = Phases 1–3.** This doc owns *order*; the pack owns *execution*.

---

## 1. The core finding: three trajectories, only partly aligned

| Trajectory | What it says | State |
|---|---|---|
| **The plan library** (Charter + Part 6/7/8) | A strategic **pivot**: kill central scraping & the deal-comparison identity; become *Dashy Dora* — effortless, **personal-price**, **zero-input pantry**, anti-creep, legally defensible; then commercialize. | **Designed, coherent, governing.** |
| **The code** (per CHANGELOG/STATUS) | Built the **old** *Discount Dora*: scraping + deal-comparison product search, stock map (N9), substitutes graph (N7), barcodes, plus Part-2 intelligence bolt-ons (P2-02/04/05/06/08/11/13). **No P6/P7/P8 entries.** | **On the pre-pivot path** — but see below. |
| **Your feedback** | Page-by-page polish of the app **as it exists today**, largely without the pivot lens. Heavy investment in product search, merchants, comparison. | **Polish altitude.** |

**Crucial nuance on "state":** at the time this plan was drafted, the code copy was stale and `STATUS.md` (dated 2026-05-27) was already trailing reality. The pivot has since closed (Cookbook / Cook Mode / C-cross / Stock Overview Chunks 1–6 / Cart Button / Shopping Lists / State Ownership all done — see `CHANGELOG.md` + the top entry of `DORA_WORKLOG.md`); `STATUS.md` was retired to `docs/06_legacy_prompt_plans/STATUS.md` on 2026-06-12 because its audit framing (against the original PROMPT_PLAN docs) no longer matched the active proposal/IMPL lineage. "Phase 0 re-baseline" as originally written is therefore obsolete — the live worklog is the new baseline.

**The reconciliation problem in one line:** the plan is pivoting the boat; the feedback is repainting cabins — some of them cabins the plan is about to remove.

---

## 2. The arbiter: your own Decision Charter

The Champion Plan defines a **12-principle Dora Decision Charter** (tie-break: **Effortless (1)** + **Anti-creep (10)**). It is the right instrument to settle plan-vs-feedback conflicts, because it's *your own* stated strategy. Every triage call below is made against it. The ones that bite hardest:

- **P4 Personal > generic** and **P9 No legal-risk scraping** → the product-search/deals direction.
- **P10 Anti-feature-creep** → comparison tools, gamification, nutrition-DB depth.
- **P1 Effortless / P5 Leverage the loop** → why the Zero-Input Pantry is the flagship, not the polish.

---

## 3. The central conflict you may not have clocked: product search / scraping

This is the big one, and it's exactly the "you might not realise how what you said changes things" case.

- **Your plan already decided to remove central scraping** — Charter P9, **P7-01** (de-risk → personal price history), and the very rename from *Discount* → *Dashy* Dora (P8-01 drops the deal-comparison promise). The COMMERCIALIZATION_REPORT is blunt: hosted scraping is the dominant legal risk and **any hosted/SaaS model forces you to stop it**.
- **Your feedback pours effort into the opposite** — 20–30s search optimisation, anti-blocking, the merchant-vs-data-provider model, keeping/​improving comparison.

**If the pivot holds, a large slice of your product-search feedback is moot** — you'd be polishing a feature you're removing from the hosted product (it survives only as a self-hosted, off-by-default module). That includes my own prompt-pack items **C-6 (search performance)** and **C-8 (merchant/provider model)** — written before I'd read the plan; they push *against* P7-01.

**RESOLVED (2026-06-04):** the scraper/product-search is **extracted into a separate private companion** (standalone app or private fork) that pushes data into Dora via Dora's API. Dora-core stays Charter-clean and commercially viable; your product-search feedback is actioned in the *companion's* scope. See §7 Decision 1 + the new ingestion-API work item.

---

## 4. Feedback triaged through the Charter

At the category level (the full item-by-item mapping lives in `FEEDBACK_TRIAGE_AND_PLAN.md`):

**Aligned — proceed (serves the Charter and/or maps onto Part 6/8):**
- Theming/dark-mode, consistency, modals, loading, text-size, sticky footers, renames → **P11 fast UX**; the rename *is* **P8-01**.
- The bug clusters (extra-inputs, PATCH, delete-FK, dead nav, toasts) → just broken; fix.
- Shop-mode-as-receipt + finish→restock-all → **literally P6-01 + P6-07**.
- Alerts control centre + alerts-as-launchpads → **P6-12**; per-type opt-in → **P3-13/Charter P6**.
- Opt-in budget & nutrition, hide money features → **Charter P8/P10** (you already framed these as opt-in).
- **Remove the comparison tools** (you said "useless") → **Charter P10 agrees** — even though STATUS marks X2/X3 *done*. Easy aligned cut.

**Conflicts with the Charter — cut/defer/demote (per your *own* principles):**
- Deep product-search polish + merchant/provider model → **P9 + P7-01** (de-risk). **Moved to the companion app** (§7 Decision 1) — not Dora-core.
- Gamification (new-feature idea) → **P10 anti-creep.**
- Nutrition-DB complexity → **P10** (you hedged this yourself: "maybe just off/simple").

**Neutral polish:** everything else — fold into Phase 0/1 as the relevant surface is touched.

---

## 5. The reconciled phased plan

Merges all three trajectories. Sequenced so we never polish a surface the pivot is about to rebuild.

### Phase 0 — Foundations & truth *(now)*
- **Re-baseline STATUS** against current code (it's stale; pivot partly done). Cheap, unblocks honest planning.
- **Wave A foundations** (theming/filters/modals/loading/text/sticky-footer/renames incl. **P8-01 Dashy Dora**) + **Wave B bugs**. This is where ~most of the feedback lands, and it's all Charter-aligned (effortless/fast/consistent). Prompt pack already written.
- **Comparison tools:** product comparison (X3) leaves with the scraper → companion; recipe comparison (X2) → assess via **INV-6** before rework/cut. Drop other P10-conflicting cruft.

### Phase 1 — Close the loop *(Part 6 — the strategic core)*
Order per the plan's own dependencies:
- **P6-02** barcode→QR cleanup (removes surface first).
- **P6-01** purchase reconciliation = **your shopping-list redesign** (DRAFT→SHOPPING→DONE, shop-as-receipt, finish→restock). *My `SHOPPING_LIST_REDESIGN_PROPOSAL` is this.*
- **P6-07** cook→consume = **your cook-mode finish-restock** feedback.
- **P6-04** suggestions/run-out prediction; **P6-13** confidence/decision-driven stocktake.
- **P6-09/10/12** costing, self-drafting shop, daily briefing.
- *Enabler:* the **state-ownership refactor** (server-owned `cookable`/prices) underpins P6 and satisfies Charter P3/P12 — do it early in this phase.

### Phase 2 — Extract the scraper & build Dora's ingestion API *(P7-01, resolved)*
- Move the merchant-API + product-search/comparison **out of Dora-core** into the private companion (standalone app **recommended over a fork** — forks rot; a clean API boundary doesn't).
- Build Dora's authenticated **ingestion API**: the companion pushes products / offers / price-observations into Dora's personal price history (feeds P6-01/P6-03; adjacent to P8-03/04 ingestion).
- **Boundary:** Dora-core keeps the product/price *data model* + "your prices" views; the companion owns scraping, merchant connections, and the search/comparison UI. Your product-search feedback (incl. C-6/C-8) applies to the companion.

### Phase 3 — Champion features *(Part 8 — the differentiators)*
- **P8-07 Zero-Input Pantry** (flagship — requires P6-01/04/07/13 from Phase 1; *do not start before them*).
- P8-02 barcode-to-add (Open Food Facts), P8-05/06 buy/wait oracles, P8-08 Dora Score, P8-09 culinary memory, **P8-10 native app**.

### Phase 4 — Commercialize *(rest of Part 7 — only when selling)*
- Productionize (Postgres/gunicorn/Redis), tenancy (Path B managed instances first → Path A multi-tenant = **my MULTI_USER_READINESS / P6-05 / P7-A1+A2**), Stripe, compliance (security headers/data rights = P5-01/02), ops, launch readiness.
- **SaaS-only work parked in follow-ups** — resurrect these FUs when Phase 4 kicks off; they're deliberately not worth doing for self-host / single-tenant:
  - **FU-461** (resolved 2026-07-06 as admin Add/Delete) — self-serve GDPR "right to erasure" endpoint at `/settings/account` danger-zone. Only load-bearing under a hosted/SaaS obligation; the admin-side plumbing already shipped (soft-vs-hard call, cascade behaviour, last-admin guard) informs the surface but doesn't build it. See `DORA_FOLLOWUPS_RESOLVED.md`.
  - **FU-465** (resolved 2026-07-07 as parked-until-SaaS) — native push on the Capacitor build via `@capacitor/push-notifications` + Firebase Cloud Messaging (Android) / APNS (iOS), plus a parallel subscription store + fan-out in `push_sender.py`. VAPID web push already covers browser + PWA install. Adds a Firebase dependency, so only worth the cost once the native APK is the primary distribution or Phase 4 wants push parity across install types.

---

## 6. Reconciling this session's proposals & prompt pack against the plan

| Artifact | Verdict |
|---|---|
| `SHOPPING_LIST_REDESIGN_PROPOSAL` | **Aligned** — it *is* P6-01/06/07. Promote into Phase 1. |
| `STATE_OWNERSHIP_REFACTOR_PROPOSAL` | **Aligned** — Charter P3/P12; enables P6. Phase 1 enabler. |
| `MULTI_USER_READINESS` | **Aligned** — it's P6-05 + P7-A1/A2. Phase 4 (or Phase 1 if households land early). |
| `DORA_ASSISTANT_ARCHITECTURE_PROPOSAL` | **Aligned** — Charter P12; relates to P5-05. Fold in during Phase 1/3. |
| `AUTH_ASSISTANT_SECURITY_FINDINGS` | **Aligned** — feeds P7-08 compliance; CSRF/email fixes are Phase 0/4. |
| Prompt pack **Wave A / Wave B / INV** | **Aligned** — Phase 0. |
| Prompt pack **C-6 search perf, C-8 merchant/provider** | **Re-scoped, not cut** — belongs to the **private companion app**, not Dora-core. Action your product-search feedback there. C-8's merchant-vs-source distinction also informs Dora's ingestion-API contract (how pushed data is labelled). |
| My earlier "you didn't review Stock Map" note | **Retract** — Stock Map is a *removed* feature; I was reading stale code. |

---

## 6.5 Cross-doc coordination (so two refactors don't collide)

- **State-ownership ↔ Dora-assistant:** both delete the *same* client-side missing-ingredients recompute (the 4th copy lives in `DoraChat.vue`). `STATE_OWNERSHIP` adds the server `cookable`/`missing_count` field; `DORA_ASSISTANT` deletes the client copy. **Sequence state-ownership first**, then the assistant refactor reads the server field.
- **Shopping-list ↔ state-ownership:** the finish→restock path (P6-01) writes stock-level deltas server-side; land the state-ownership stock-status contract *before* implementing finish-restock so reopen/undo is reliable.

## 6.6 Ingestion-API contract *(delivered — see the proposal + IMPL plan for authority)*

**Status (2026-07-01):** the sketch below was the plan-doc's original framing. It has been **superseded in detail** by `04_proposals/PROPOSAL_INGESTION_API.md` + `04_proposals/IMPL_PLAN_INGESTION_API.md`, and shipped as C-10.1 → C-10.4 (bearer auth + admin keys page, `POST /api/ingest` batched idempotent, observability, "your prices" intelligence layer). Read those proposals for the current contract; keep this section as the plan-level anchor only.

**Key deviation from the original sketch:** `price_observation` is **NOT accepted** by the ingestion endpoint. Per FU-227 chunk 7 (`PROPOSAL_PRODUCTS_AS_OVERLAY.md §2.5 "Idea A"`), price observations are in-app user input only; the ingest payload is `{ products[], offers[] }` and `extra="forbid"` rejects observations at the boundary. The offer append path feeds `ProductHistoricOffer` and unions with in-app observations inside `dora_api/features/stock_items/your_prices.py`.

**Original sketch (kept for historical framing — do not build against this):**
- **Accepts** (batched, idempotent): `product {name, brand?, size?, source}`, `offer {product_ref, price_now, price_was?, valid_until?, source}`. ~~`price_observation`~~ *(dropped per FU-227 J1)*. The `source` field carries the merchant/provider label — this is where C-8's distinction lands.
- **Dora maps to:** product/price data model (dedup by source+code — implemented as `(store_id + stockcode)` else `(store_id + name)`), optional stock-item link, personal price history (feeds P6-01 costing, P6-03 intelligence).
- **Out of scope for Dora:** scraping, merchant connections, search/comparison UI — all companion. Dora never calls the companion; the companion calls Dora.
- **Also added by implementation** (not in the original sketch): FU-190 store-mapping quarantine (stores are never auto-created); C-10.1 admin "API access" page for key CRUD + per-key observability.

---

## 7. Decisions (resolved 2026-06-04)

1. **Identity & scraping — RESOLVED: separate the scraper.** Dora-core = the Charter-clean, personal-price, commercially-viable product with **no central scraping**. The merchant-API + product-search/deal-comparison is **extracted into a private companion** that **pushes data into Dora via Dora's public ingestion API**. Your product-search feedback is actioned in the *companion's* scope; Dora-core stays legally clean and sellable.
   - **Derived — RESOLVED: standalone companion, not a private fork.** A fork diverges and must re-merge every Dora change forever; a standalone tool with a clean API boundary doesn't decay and forces the ingestion contract Dora needs anyway. The companion is its own project, out of scope for *finishing Dora* except for the ingestion-API seam.
   - **New Dora-core work item — the ingestion API.** An authenticated endpoint that receives pushed products/offers/price-observations and folds them into personal price history (feeds P6-01/P6-03; adjacent to P8-03/04). **Boundary:** Dora keeps the product/price *data model* + "your prices" views; the companion owns scraping, merchant connections, search/comparison UI.
   - **Refinement (2026-06-17) — Products is a data-presence overlay, not a user flag.** The rich `Product`/`ProductOffer` layer is either fully ON (real product data has been ingested) or fully OFF, gated on data-presence (`features.products` derived from `Product` rows), with **no user-facing toggle and no onboarding persona**. The everyday user gets product-ish memory on the stock item itself (`PreferredBuy`, price observations, `usual_store_id`). Only the **search page** moves to the companion (behind a configured URL); the other product pages (My Products, Price History, the stock-item Products tab) **stay in Dora**, data-gated. Full design: `04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md` (supersedes the spine of `PROPOSAL_SIMPLE_MODE.md`; this also retires the onboarding persona fork).
2. **Sequencing — RESOLVED: Foundations → loop → champion.** Phase 0 now; Part 6 loop; Part 8 champion. Polish each surface as the pivot reaches it.
3. **Charter cuts — RESOLVED (per item):**
   - **Product comparison (X3)** → leaves with the scraper to the companion.
   - **Recipe comparison (X2)** → **assess its real worth first** (new task INV-6), *then* rework or cut on the evidence — not a blind keep.
   - **Gamification** → **someday-list** (captured, not built during finishing). *Re-checked 2026-07-07 against the shipped P8-08 Dora Score card (FU-356 co-decided with FU-352): still parked. The Score card already carries a mild "you're improving" signal via its `trend_direction` / `trend_delta` chip; streaks / badges / "N shops on budget in a row" would be a whole new feedback surface (extra UI + server-side counters + a notifications channel), not a small addition, so Charter Anti-creep + P3 keep the park.*
   - **Nutrition** → ~~**off + simple (kcal) only**; no complex linked nutrition-DB.~~ **REVERSED by the owner, 2026-08-14 — complex is being built.** The original cut was made on a feasibility worry the owner raised in the 06-Jun feedback ("my concern … is the complexity in being accurate with quantities in recipes"). Reviewing the built state showed `complex` had shipped as a *fake seam* — a `nutrition_db_source` string with no UI, gating a mode with zero implementation — which is worse than either building or cutting it. On review the feasibility picture had also changed: USDA FoodData Central is CC0, its two generic-food datasets are only ~10MB zipped, and it ships a `food_portion` table mapping household measures ("1 cup", "1 medium") to gram weights, which answers most of the original quantity worry. Decided shape: install-wide mode (off/simple/complex), multi-source lookup (USDA datasets downloaded on demand + optional USDA API key + Open Food Facts for barcodes) with every result badged by source, **explicit human confirmation** on every stock-item↔food link (P12 No-invent), and recipe nutrition shown **per serving with a coverage line** ("from 9 of 12 ingredients") so a partial total can never pass itself off as complete. Simple (hand-typed kcal) is unchanged and remains the no-data-source option. Build status + remaining chunks: `DORA_FOLLOWUPS.md` FU-635.
4. **Commercialize — RESOLVED: someday, not near-term — but it IS a real goal.** Phases 0–3 first; Part 7 (productionize/tenancy/billing/compliance) when validated. Because selling is a genuine future goal, Dora-core must stay Charter-clean *now* — which is exactly what Decision 1 secures.
5. **Distribution & tenancy posture — RESOLVED: build the GitLab model — ONE codebase, SaaS-style, self-hostable.** The product is a normal client → server → database app (current Flask + Quasar stack). It ships as **one artifact** that runs three ways, differing only by *configuration*, never by code fork: (a) **self-hosted single instance** (the everyday self-host default — SQLite, no email server required), (b) **managed single-tenant instance** you operate for a customer (= the charter's **Path B**), (c) **multi-tenant hosted SaaS** (= **Path A**, deferred to Phase 4). SaaS and self-host are **not conflicting architectures** — they agree the server owns the domain logic and is the source of truth; only *who runs the box*, *tenant isolation*, and *which managed conveniences are on* differ. (This is why local-first was rejected and this wasn't: local-first disagreed on *where the source of truth lives*; self-host-vs-SaaS does not.)
   - **The five disciplines that keep Path A reachable without paying for it now** (check new work against these — see §7.5):
     1. **Route all data access through repositories** (Clapy clean-arch already does) so tenant scoping can be injected in **one layer**, not 400 query sites, if/when Path A lands.
     2. **Keep the DB layer portable, with Postgres as the standard target.** **Postgres is the chosen long-term datastore** for dev + hosted (SQLite feels too unstable for the long haul). **SQLite stays supported** as the zero-dependency lightweight self-host option, so the everyday-person self-host story survives — so the ORM/migration layer must remain portable *both* ways: don't lean on Postgres-only quirks that SQLite can't express, nor SQLite-only behaviour. (The UUID/`text()` binding sharp edge — see memory — is exactly the kind of SQLite wrinkle Postgres removes natively; treat such cases as "make it generic / prefer the Postgres-native path.") Migration to Postgres-default is tracked as a follow-up (see `DORA_FOLLOWUPS.md`); it is **not** Postgres-*only* — retiring SQLite would raise the self-host bar and is explicitly not chosen.
     3. **Every cloud-vs-self-host difference is env/config-driven, never a build flag or branch.** `DATABASE_URL`, `RELAY_URL`, `SMTP_*` (optional), feature toggles on `AppSetting`. Same artifact, different env.
     4. **Auth behind an interface with a local provider as the default** (username/password against own DB; no mandatory external IdP or email server). Leave room for a hosted provider later.
     5. **Do NOT pre-build multi-tenancy.** No unused `tenant_id` columns. The repository *seam* is the insurance; the column is dead weight + a migration headache until Path A is real. Treat the single-tenant assumption as "a tenancy of size 1."
   - **The one genuine caveat:** the only thing truly hard to retrofit is **multi-tenant isolation** (strangers' data in one DB, per-tenant backups/migrations/rate-limits) — that's Path A, deferred. "SaaS-style" meaning *managed single-tenant instances* (Path B) costs ~nothing today. The five disciplines are exactly what keep the Path B→A jump a **6–12 month project, not a rewrite**.
   - **No new build work now** — this is a posture, not a task. It records what to *avoid* (the irreversible mistakes) while finishing, so the SaaS door stays open. Confirms and supersedes nothing in Decision 4; it makes Decision 4's "Path B → Path A" concrete at the code level.

6. **Crowd price graph (P8-04) — RESOLVED 2026-07-02: CUT** (FU-436). The originally-spec'd opt-in community price graph is retired. Four structural blockers, not fixable by design: (a) small-cohort re-identification even under anonymisation, (b) cold-start with no distribution channel to bootstrap contributor volume, (c) weekly Aus catalogue rotation caps the useful freshness window, (d) hosted-broker ops role (uptime + moderation + abuse detection + DPAs) reintroduces exactly the pattern Decision 1 retired when the scraper was extracted. The champion plan's own P8-06 spec (line 366) already read "design to work on personal data alone" — crowd was framed as optional-blend, never load-bearing. P8-05 shipped this session on pure personal data with an honest thin-data branch (Charter P3); the "brand-new user, no history" experience it produces is honest, not broken. **Champion order becomes `P8-01 → P8-02 → P8-03 → P8-05 → P8-06 → P8-07 → P8-08 → P8-09 → P8-10`** (P8-04 removed) — further updated by Decision 7. Full argument trail: [`docs/05_investigations/CROWD_PRICES_ASSESSMENT.md`](../05_investigations/CROWD_PRICES_ASSESSMENT.md) (INV-11). Unblocks FU-438 (P8-06 wait-until).

7. **Email ingestion (P8-03) — RESOLVED 2026-07-02: CUT** ([FU-453](../../DORA_FOLLOWUPS_RESOLVED.md)). *"Cut anyways, not worth the work — dora excels elsewhere."* Adjacent to Decision 6 but on a different failure surface: P8-04 fails on privacy + incentive + freshness + broker-role; P8-03 fails on ops-shape + parser-fragility + architectural fit. Concretely — the mail-receiving surface is SaaS-shaped ops that adds ongoing per-install burden (Postmark/SES/SendGrid inbound, or IMAP creds, or per-shop hand-forwarding — against §7.5); retailer email HTML is the same silent-fragility class as scraping (exactly what the Decision-1 pivot was designed to escape); loyalty offer emails (Everyday Rewards / Flybuys) are increasingly image-only by design (unparseable); and `Finish & restock` (P6-01) already captures `paid_price` from the list at the till with dramatically less ops risk. If email ingestion is ever worth doing, it plugs into `/api/ingest` from a companion — same seam the retailer-scraper companion uses (Decision 1). **Dora-core does not learn to parse email. Champion order (superseding Decision 6's line): `P8-01 → P8-02 → P8-05 → P8-06 → P8-07 → P8-08 → P8-09 → P8-10`** (P8-03 and P8-04 both removed).

### Someday-list (captured, not in finishing scope)
- Gamification (rewards / notify-users / streaks).
- The standalone scraper/product-search companion (its own project; Dora-core only owes it the ingestion API).
- Native app (P8-10) — already in Part 8 but post-loop. (Crowd price graph P8-04 was cut per Decision 6, and email ingestion P8-03 was cut per Decision 7; see above.)

### Immediate next step
Phase 0 is unblocked and no-regret — start the **Wave A foundation + Wave B bug prompts**. One small parallel task: **INV-6** (assess recipe-comparison worth). (The ingestion-API contract note from earlier drafts is superseded: the API shipped, and its downstream consumers no longer include P8-03/04 — Decision 6.)

---

## 7.5 Distribution-posture checklist (check new work against this)

A lightweight gate for any prompt that touches data access, auth, config, or deployment — keeps the GitLab "one codebase, self-host-or-cloud" door open (Decision 5). Pass = no action; fail = fix now or log a `DORA_FOLLOWUPS.md` finding, don't silently ship.

- [ ] **Data access goes through a repository**, not a raw query at the call site (so tenant scoping is a one-layer change later).
- [ ] **Portable both ways — Postgres is the standard target.** No SQLite-only assumption that would block Postgres (the long-term datastore), and no Postgres-only behaviour that breaks the still-supported lightweight SQLite self-host. Prefer the Postgres-native path where SQLite forces a wrinkle (e.g. UUID handling).
- [ ] **New cloud-vs-self-host difference is read from env/config**, not hardcoded or behind a build flag.
- [ ] **New auth/identity path resolves through the auth interface**, with the local provider working when no external IdP/SMTP is configured.
- [ ] **No `tenant_id` / multi-tenant scaffolding introduced** "just in case" (single-tenant = tenancy of size 1).
- [ ] **A required managed convenience** (relay, LLM, email, companion) **degrades gracefully to "feature absent"** when unconfigured — never a hard crash on the self-host default.
