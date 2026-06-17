# Implementation Plan — Products as a data-presence overlay (execution order)

> **⭐ Drive the effort from `PRODUCTS_OVERLAY_RUNBOOK.md`** — it owns the *current* order + live
> status (re-sequenced 2026-06-17: companion divorce before the rename) and per-phase
> steps/acceptance/verify. This IMPL plan remains the per-chunk detail reference.

**Status:** Plan for execution · **Date:** 2026-06-17 · phased chunks.
**Source proposal:** `PROPOSAL_PRODUCTS_AS_OVERLAY.md` (co-designed 2026-06-17).
**Tracks the follow-ups:** FU-208 (link repair), FU-209 (gate reframe), FU-210 (onboarding
de-persona), FU-211 (`PreferredBuy`), FU-212 (docs), FU-213 (price substrate), FU-214 (verify +
gaps), FU-186 (companion + search relocation), FU-189 (Stores rename + `usual_store_id`), FU-190
(no-auto-create stores on ingest). Ingestion build follows `PROPOSAL_INGESTION_API.md` §6.

**Two tracks.** Almost everything is **Dora-side** (Stages 0–2 + 4). One piece — the **companion**
(Stage 3) — is a separate standalone project that only depends on Dora's ingestion contract
existing. Stages 0–2 + 4 complete Dora's entire side; products light up the moment *any* source
(even a throwaway script hitting `/api/ingest`) pushes data, so the full companion is not required
to validate Dora.

**Critical path:** S0-1 → S1-4 → S2-8 → S2-9 → S3-11 → S3-12. Everything else hangs off these.

> **Re-sequenced 2026-06-17 — companion divorce BEFORE the rename.** FU-189 (Merchant→Store, was
> S1-4) is moved to **last**. Reason: "merchant" means two intertwined things — the `Merchant`
> *entity* and the `merchant_api` *companion* (`ApiBackend 'merchant'`, `MerchantApiService`/
> `Management`, `MerchantsSettings`, `VITE_MERCHANT_API_*`, in-app live `ProductSearch`). A blind
> rename corrupts the companion wiring + splits the FE/BE contract. Real order now: **(a) scaffold
> the companion** (separate sibling repo — DONE at `../dora-companion`) → **(b) ingestion API**
> (S2-9, the push target) → **(c) companion standalone + wired** → **(d) decommission
> `merchant_api`/`emailer` from Dora (FU-186) + the search-URL nav** → **(e) the now-clean FU-189
> rename + `usual_store_id` + Stores page.** S1-5/6/7 (PreferredBuy / money / price substrate) +
> FU-216 already shipped (static-only).

**Prerequisites to confirm before Stage 1:** (a) how much of the **Money/spend opt-in** already
exists (PROPOSAL_CONFIG_AND_OPTINS §2.2); (b) the **shopping-list redesign** status (the close-out
price-entry surface in S1-7 rides on it).

---

## Stage 0 — Decouple products from the user (small, no-regret, do first)

One tight mini-wave: make products a data-presence overlay and remove the flag. No ingestion
needed. Build together to avoid leaving the tree half-flagged.

### S0-1 — Gate reframe (FU-209)
- Drop `AppSetting.products_enabled` (entity + table mapping + a clean drop migration,
  pre-release — no preservation).
- `health_check.py`: derive `features.products = (Product.count() > 0)` via the repo (R-003 —
  single server-derived fact; same try/except envelope as today). Open: `Product` alone vs
  `Product OR ProductOffer` — rec. `Product` alone (proposal §7-1).
- Drop the `products_enabled` field from `get_app_settings` DTO + `update_app_settings` request,
  and the admin toggle in System settings.
- Remove the `products_enabled` write from the onboarding persona payload + `INSTALL_FLAG_META`
  (the full fork UI removal is S0-2).
- **Keep every `v-if="productsEnabled"` gate** — only the boolean's source changes.
- **Acceptance:** with no `Product` rows, `/api/health` `features.products = false` and the product
  surfaces are hidden; insert a `Product` row → `true` and they appear. Migration up+down clean,
  single Alembic head. `vue-tsc` + eslint clean. Candidate **ADR** (data-presence-gated surfaces).

### S0-2 — Onboarding de-persona (FU-210)
- Remove the persona fork (Cooking/Spend/Everything) + all product framing + the stock-vs-product
  explainer. Keep the structural chunks (intro, hero loop, starter packs, household headcount,
  finish) **un-personalized** — drop C-5.2 persona preview + C-5.6 persona tailoring.
- **Money/budgeting becomes a Settings toggle only** — onboarding shows the feature exists, no
  fork/forced choice.
- Depends on S0-1 (flag dropped). NB: the fork + flag have shipped, so this is a *removal*.
- **Acceptance:** one un-personalized "show everything" flow; no product/persona/explainer copy;
  money set only via Settings; structural chunks intact; sell-copy re-checked (FU-184).

### S0-3 — My Products link repair (FU-208)
- Rebuild a working link path (consume `link_product_id` on detail, or link in place via
  `POST /api/stock-items/{id}/products`). Link pre-existing products only — no manual creation.
- Pairs with S0-1.
- **Acceptance:** from My Products, "Link…" → pick stock item → the product is actually linked
  (browser-verified); the dead `link_product_id` route no longer no-ops.

---

## Stage 1 — The everyday stock-item layer (parallelizable; no ingestion)

S1-4/5/6 are independent of each other; S1-7 depends on S1-6.

### S1-4 — Stores rename + `usual_store_id` (FU-189)
- `Merchant → Store` app-wide (one migration, no compat shims). User-curated management page; **no
  prefilled stores, no auto-create** from any path. Per-store image upload (reuse C-cross §2.8
  infra; ship zero logos). Add `StockItem.usual_store_id` (nullable FK).
- Prereq for shopping-list grouping (S1-7) and ingestion store-mapping (S2-8/9).
- **Acceptance:** rename complete (no stray `Merchant` symbol); management CRUD with referential
  safety; `usual_store_id` round-trips; image fallback = hash-swatch.

### S1-5 — `PreferredBuy` (FU-211)
- New `PreferredBuy(id, stock_item_id FK cascade, label free-text, position, created_at)` +
  migration. "Preferred buys" section on stock-item detail (add/edit/delete/reorder).
  `ShoppingListLine.preferred_buy_id` (nullable FK, SET NULL) shown as a line hint — no pricing.
  Strictly separate from `Product`.
- **Always-available** (not gated by products or money). Independent — easiest standalone win.
- **Acceptance:** preferred buys persist per item; a chosen hint shows on the list line; works with
  products both present and absent.

### S1-6 — Money/spend opt-in (Settings toggle)
- Build the opt-in itself (PROPOSAL_CONFIG_AND_OPTINS §2.2) if not already present. Gates dollar
  surfaces + price logging. Prereq for S1-7.
- **Acceptance:** toggling spend on/off reveals/hides dollar surfaces; no dollars anywhere when off.

### S1-7 — Price substrate (FU-213)
- `StockItemPriceObservation(stock_item_id, price, qty, unit, observed_at, source)` (per-unit
  derived server-side — user enters total + qty) + server-owned `get_stock_item_unit_cost_at`
  helper (R-003). Rebase consumers (stock-value report fallback, recipe cost estimate). Price-entry
  surfaces: shopping close-out (per-line on tick), stock-item detail "log a price", quick-add.
- Depends on S1-6 (money); uses S1-4 (`usual_store_id`) for shopping grouping; close-out rides on
  the shopping-list redesign.
- **Acceptance:** logging total+qty yields a correct per-unit cost; consumers read the helper, not
  client math; no merchant attribution in the everyday layer; all gated by money opt-in.

---

## Stage 2 — Ingestion seam (Phase 2; lights products up)

### S2-8 — Amend ingestion proposal for no-auto-create stores (FU-190)
- Doc-only: PROPOSAL_INGESTION_API §2 gets the no-auto-create constraint + (c) happy-path mapping +
  (b) quarantine safety net + a coverage-table row citing FU-189. Depends on S1-4. Quick.

### S2-9 — Build the ingestion API (PROPOSAL_INGESTION_API §6.1–6.3)
- `IngestionSource` model + bearer-auth lane + the **always-accessible** admin "API access" keys
  page (CRUD + observability) + `POST /api/ingest` (batched, idempotent via `Idempotency-Key`,
  append-only, `source` column) + refactor `create_product` to share the ingest mapping. Honour
  the store-mapping rule (S2-8). Depends on S1-4, S2-8. Large.
- **Acceptance:** a bearer-authed batch upserts products/offers/observations idempotently; unknown
  stores are mapped/quarantined, never auto-created; keys page shows last-used + accepted/skipped/
  failed; `create_product` and `/ingest` share one mapping.

### S2-10 — "Your prices" intelligence (PROPOSAL_INGESTION_API §6.4)
- Union pushed data + user receipts → baseline + "paying more than usual" signal; surface on
  stock-item detail + Price History. Depends on S2-9, S1-7.

---

## Stage 3 — Companion app + search relocation (separate project; depends on ingestion)

### S3-11 — Stand up the companion repo (FU-186)
- Extract `merchant_api` + the Product Search page + a settings page into its own project; push to
  `/api/ingest`; finish the `emailer` there. Standalone build; out of scope for "finishing Dora"
  except the seam. Depends on S2-9. Large.

### S3-12 — Dora-side search relocation (FU-186 + proposal §4.1)
- Add the install **"Product search URL"** setting; repoint the Product Search nav entry to it
  (data-gated; **companion never named** — the bounded invisibility carve-out); remove the in-app
  search page + its `merchant_api` calls; delete `emailer/` from Dora; clean dead `SOURCE_EMAILER`
  refs. Depends on S3-11.
- **Acceptance:** with data present + URL set, the nav entry opens the configured search; with data
  absent it's hidden; no `merchant_api` call from Dora; no "companion/scraper/import" copy anywhere.

---

## Stage 4 — Verify, polish, document

### S4-13 — Product-feedback verify + gaps (FU-214)
- Browser-verify the My Products + Price History bug/polish cluster (proposal Appendix A); build the
  L205/206 bulk variants if wanted; decide L197 hard-delete. Partly doable with seeded products;
  fully after ingestion. Stock-item-detail product bullets are under FU-202; the link handoff is
  S0-3/FU-208.

### S4-14 — Power-user / ingestion docs (FU-212)
- How to source product data (keys page + `/api/ingest` + the search URL); how data-presence lights
  the surfaces; the no-auto-create mapping step. Not in onboarding; producer unnamed. Depends on
  S2-9, S3-12.

### S4-15 — Postgres portability (FU-045 lane)
- Keep `PreferredBuy` + `StockItemPriceObservation` + `IngestionSource` portable (SQLite +
  Postgres) as they land — ongoing discipline, not a discrete step.

---

## The no-companion-yet shortcut

To get the entire Dora experience real and testable without building the companion first:
**Stage 0 → Stage 1 → S2-8/S2-9 (ingestion) → push test data with a throwaway script → S4-13
verify.** The companion (S3-11) and search relocation (S3-12) follow whenever.

## Downstream / later (not in this plan's core)
- C-9 "inflated price" alert + back-in-stock subscriptions (FU-188), fed by ingestion.
- Trust-tier enforcement on ingestion sources; P8-03 email + P8-04 crowd sources on the same
  contract.
