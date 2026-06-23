# Products-as-Overlay — Master Runbook & Status

**This is the single driver for completing the products-as-overlay effort end-to-end:** the everyday
stock-item layer, the ingestion-fed Product overlay, the **standalone companion app running**, the
`Merchant → Store` rename, and the product-feature feedback — all in the order we determined is safest.

**On session start:** read this file + the top of `DORA_WORKLOG.md`. As you finish a step: tick it
in the Status table below, append a `DORA_WORKLOG.md` entry, and move/resolve the relevant
`DORA_FOLLOWUPS.md` items. **This runbook owns ORDER + STATUS;** design detail lives in
`PROPOSAL_PRODUCTS_AS_OVERLAY.md` (vision), `PROPOSAL_INGESTION_API.md` (the seam), and
`IMPL_PLAN_PRODUCTS_AS_OVERLAY.md` (chunk detail).

---

## Definition of done (the vision, fully realised)

- Products are a **data-presence overlay** — visible only when product data exists, no user flag. ✅ (gate built)
- Everyday users get **`PreferredBuy`**, **price observations** (own unit-cost), and **`usual_store_id`** on stock items; the word "product" never appears for them.
- The rich **`Product`/offer** layer is fed **only** by the companion via `POST /api/ingest` — Dora never scrapes/calls out.
- The **companion app runs standalone** (scraper + product search + deals email), pushing into Dora; its existence is invisible in Dora except one unnamed "Product search" URL.
- `merchant_api`/`emailer` are **gone from the Dora repo**; `Merchant` is renamed **`Store`**.
- The product-feature feedback (Appendix A of the proposal) is addressed; **everything is verified on a real env.**

---

## ⚠️ Verification debt — READ BEFORE TRUSTING ANY OF PHASE 0

**Update 2026-06-17 — Phase A env-verify ran on the local Linux env: backend GREEN.** Full pytest
suite **381/381 passed** (incl. the 3 new FU-211/213/215 files — 11/11), `vue-tsc` clean, `npm run
lint` clean. **One blocker was found and fixed:** the FU-209 migration shipped with a duplicate
Alembic `revision = 'f1a2b3c4d5e6'` (collision with the 2026-05-20 `app_settings` migration), which
made `flask db heads` raise `CycleDetected`; the FU-209 migration was re-issued as
**`f1d5b8a2c4e6`** and `a2c4e6f8b1d3.down_revision` was repointed.

Everything built **2026-06-17** (FU-208, 209, 210-core, 211, 213, 215, 216) was originally
code-complete but static-only. Per-feature verify checklists remain on each FU in
`DORA_FOLLOWUPS.md`. **FU-216** numeric verify is GREEN (no existing test pinned old totals broke).
**Still pending:** per-FU **browser passes** (FU-202/208/211/213/214/215 + the FU-216 stock-value /
recipe surfaces) — they need the running app. **FU-189** (rename) remains deferred. **FU-178** is
still a real fresh-SQLite boot blocker (chain dies at `d7c9e4a8c2b1`, batch-mode unnamed
constraints); tests bypass it via `drop_all + create_all`.

Single Alembic head after Phase 0: **`c4e6a8b1d3f5`** (chain:
`e9a4b6c2d8f1 → f1d5b8a2c4e6 (FU-209) → a2c4e6f8b1d3 (FU-211) → b3d5f7a9c2e4 (FU-213) → c4e6a8b1d3f5 (FU-215)`).
New test files: `tests/e2e/dora_api/test_preferred_buys.py`, `test_price_observations.py`,
`test_shopping_line_preferred_buy.py`.

---

## Status snapshot

| Phase | What | Status | Repo |
|---|---|---|---|
| **0** | Everyday layer + gate (FU-208/209/210-core/211/213/215/216) | **code-complete; backend env-verify GREEN; browser still pending** | dora_api + web_app |
| **—** | Companion scaffold | **DONE** | `../dora-companion` |
| **A** | Verify the Phase-0 stack on a real env | **backend GREEN** (pytest 381/381, tsc, lint; FU-209 mig-id collision fixed); **browser pending** | both |
| **B** | Ingestion API | **backend GREEN** (pytest 401/401, tsc, lint; FU-190 honoured via quarantining store mappings); **browser pending** | dora_api + web_app |
| **C** | Companion: standalone + wired to `/api/ingest` | **DONE** — backend GREEN (5 unit + 4 round-trip integration tests against live in-process `dora_api`); FE shipped (FU-219 resolved — Vue 3 + Quasar + Pinia in `../dora-companion/web_app/`) | `../dora-companion` |
| **D** | Decommission `merchant_api`/`emailer` from Dora + search-URL nav (FU-186) | **DONE** — directories deleted; FE + BE + infra wiring stripped; new `AppSetting.product_search_url` powers the re-pointed nav (data-gated + R-014 disabled-with-hint); pytest 405/405, tsc + lint clean | dora_api + web_app |
| **E** | `Merchant → Store` rename + `usual_store_id` + Stores page (FU-189) | **unblocked** — "merchant" = entity only now | dora_api + web_app |
| **F** | Finish overlay: "your prices" intelligence, FU-210 tail, FU-214, FU-212 docs, FU-180 | **in progress** — "your prices" ✅ (FU-227 resolved 2026-06-22 + multipack/locale follow-up 2026-06-23); FU-212 ✅; FU-180 ✅ (closed 2026-06-23 — `PreferredBuy` + `usual_store_id` cover the intent); FU-232 ✅ (companion contract `pack_count` 2026-06-23); FU-210 tail **code-complete, browser-verify pending**; FU-214 not started (needs running app) | various |

---

## The order — do these in sequence

### Phase A — Verify the foundation (DO FIRST when an env exists)
- **Why first:** ~9 chunks shipped static-only; stacking more on unverified code compounds risk.
- **Steps:** provision Python venv + `npm ci` in `web_app`; migrate base→head (single head
  `c4e6a8b1d3f5`, up **and** down); run the full backend e2e incl. the 3 new test files; `vue-tsc` +
  eslint; browser pass per the FU checklists (FU-202, FU-208, FU-211/213/215 acceptance). **FU-216:**
  confirm the new stock-value/recipe-cost numbers and update any test pinning old totals.
- **Done when:** green suite + single head + clean tsc/eslint + checklists pass → flip those FUs to resolved.

### Phase B — Ingestion API (in `dora_api`)
- **Goal:** the inbound seam the companion pushes into. Follows `PROPOSAL_INGESTION_API.md` §6.
- **Steps:** `IngestionSource` entity/table/migration; bearer-auth lane (exempt from session
  middleware); admin **"API access"** page (CRUD + observability) — **always accessible, NOT
  products-gated** (`PROPOSAL_PRODUCTS_AS_OVERLAY.md` §4.3); `POST /api/ingest` (batched,
  `Idempotency-Key`, append-only, `source` column, per-record result DTO); refactor `create_product`
  to share the ingest mapping; honour **no-auto-create-stores** (FU-190 — map/quarantine unknown stores).
- **Acceptance:** a bearer-authed batch upserts products/offers/observations idempotently; unknown
  stores are mapped/quarantined, never auto-created; keys page shows last-used + accepted/skipped/failed.

### Phase C — Companion: standalone + wired (`../dora-companion`)
- **Goal:** make the seeded companion a real runnable app that pushes to Dora's `/api/ingest`.
- **Steps:** resolve shared imports it pulled from the Dora repo (e.g. `logging_setup`); add the
  product-search UI + a settings page (extract Dora's `ProductSearch.vue` + the scraper-provider
  `MerchantsSettings.vue` here — they LEAVE Dora in Phase D); implement the push to `/api/ingest`
  (map each companion merchant → a Dora store per FU-190; push products/offers/observations); finish
  the `emailer`. Keep the **invisibility rule**.
- **Acceptance:** companion runs standalone; a scrape→push round-trip lands products in Dora and they
  appear in Dora's product surfaces (the data-presence gate flips on).

### Phase D — Decommission `merchant_api`/`emailer` from Dora + search-URL nav (FU-186)
- **Goal:** remove the scraper from Dora so "merchant" = the entity only (this unblocks the rename).
- **Steps:** delete `merchant_api/` + `emailer/`; strip wiring — `ApiBackend 'merchant'` + URLs in
  `axiosHttpClient.ts`, `MerchantApiService`/`MerchantManagementApiService`, `MerchantsSettings.vue` +
  `merchantStore` provider-health bits, the `desktop_app.py` spawn, `VITE_MERCHANT_API_*`, the in-app
  live `ProductSearch.vue`; add the install **"Product search URL"** setting + repoint the nav at it
  (data-gated, companion never named — §4.1); clean dead `SOURCE_EMAILER` refs.
- **Acceptance:** Dora boots with no `merchant_api`; the Product Search nav opens the configured URL
  when data is present; no companion/`merchant_api` references remain except the unnamed search URL.

### Phase E — `Merchant → Store` rename + `usual_store_id` + Stores page (FU-189) — ONLY after D
- **Goal:** the now-mechanical rename + the everyday store model.
- **Steps:** with `merchant_api` gone, "merchant" = entity. Rename `Merchant`→`Store` app-wide —
  entity, table, FK columns (`merchant_id`→`store_id`, `purchased_merchant_id`→`purchased_store_id`,
  migration), mappers, DTOs (`merchant_name`→`store_name`), `/api/merchants`→`/api/stores`,
  `MERCHANT_ROUTER`, frontend models/services/store/pages/components, `MerchantLogo`→`StoreLogo`.
  **KEEP `merchant_stockcode`** (a SKU; rename separately if at all). Add `StockItem.usual_store_id`
  (nullable FK) + a **user-curated Stores management page** (CRUD, **no prefilled stores, no
  auto-create** — FU-190) + per-store image upload (reuse the existing image-upload infra; ship zero
  logos, hash-swatch fallback). **Use a compiler** (`vue-tsc` + a python import check) + a final grep
  sweep for stray `Merchant`/`merchant` excluding `merchant_stockcode`. **Do NOT attempt this blind.**
- **Acceptance:** app boots; grep-clean; `usual_store_id` round-trips; Stores CRUD works.

### Phase F — Finish the overlay vision
- ~~**"Your prices" intelligence**~~ ✅ resolved 2026-06-22 (FU-227, 8 chunks) + multipack `pack_count` + AU/US locale follow-up 2026-06-23.
- ~~**FU-212** power-user/ingestion docs~~ ✅ resolved.
- ~~**FU-180** preferred-store/merchant reassessment~~ ✅ closed 2026-06-23 — `PreferredBuy` (per-item product) + `StockItem.usual_store_id` (per-item store) cover the practical intent; app-wide preferred-store is YAGNI / cheap to add later if real usage demands.
- ~~**FU-232** companion ingestion contract `pack_count`~~ ✅ resolved 2026-06-23 — `_ProductIn.pack_count` accepts the multipack count and persists to `Product.pack_count`; docs + round-trip pytest in place (static-only, needs env to execute).
- **FU-210 tail:** the persona-preview removal sweep landed (smaller intentional trim, post-user-direction revert — see FU-210 in `DORA_FOLLOWUPS.md` 2026-06-17 updates). vue-tsc / lint / pytest clean. **Browser-verify pending** — confirm Story plays without LOOP_INSIGHT, renamed chips, Finish step, draft resume.
- **FU-214:** product-surface browser verify + build the L205/206 bulk-select variants + decide L197 hard-delete. Needs running app.

---

## Start here (next concrete action)

**If an env can be provisioned: Phase A** (verify the static-only foundation before stacking more).
**Otherwise: Phase B — the ingestion API** (additive, in-repo, builds toward the companion wiring).
The companion repo is already scaffolded at `../dora-companion` (see its README).

---

## Standing rules (apply to every step)

- Static-only building is acceptable for **additive** chunks (the user's working style), **but
  FU-216 (cost numbers) and FU-189 (rename) MUST be env-verified before shipping.**
- Obey the **Charter** + `ENGINEERING_STANDARDS.md` (run the close-gate each unit). The ingestion
  **invisibility rule is hard** — only the single unnamed "Product search" URL links out.
- Keep every new table/migration **Postgres-portable** (R-005); single Alembic head.
- Each completed step: update this Status table + `DORA_WORKLOG.md` + the `DORA_FOLLOWUPS.md` items.
