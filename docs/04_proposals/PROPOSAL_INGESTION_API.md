# Proposal — Ingestion-API Contract (C-10)

**Status:** Draft for discussion · **Date:** 2026-06-06 · Changes NO code.  
**Scope:** Design the authenticated, Dora-core endpoint that **external sources
push product / offer / price data into**. The seam between Dora and the scraper
companion (C-6/C-8), reused later by P8-03 (loyalty email) and P8-04 (crowd
prices). Dora-core only — the companion is a separate project.

> **Why this exists (and the dependency to be honest about):** this contract is
> necessary **because of** the resolved decision to extract the scraper into a
> companion (`RECONCILED_FINISHING_PLAN.md §7 Decision 1`). If that decision were
> reversed, in-process scraping would write to the DB directly and this API would
> not be needed. It is downstream of that call — confirmed in-scope.

> **Charter tie-break:** the boundary is the point — **Dora never calls out;
> sources call in.** Dora-core stays Charter-clean (no scraping, no merchant
> connections), legally safe, and sellable; the messy outside world is held behind
> one well-defined door.

---

## 1. Current state (what we map into)

Products are a **shared catalogue** (no `user_id`):

- `Product` — name, brand, size/size_unit/size_value, `merchant`, `merchant_stockcode`,
  image, is_active, is_available, web_url, **`current_offer`** (a `ProductOffer`),
  **`historic_offers`** (a list of `ProductHistoricOffer`).
- `ProductOffer` — `offered_on`, `price_now`, `price_was`. The *current* price.
- `ProductHistoricOffer` — an **append-only log** of past offers; this is what the
  **price-history view (P6) reads** (`price_history.py:8-10`) for the series +
  all-time-low; the current point comes from `ProductOffer`.
- `Merchant` — **just a `name`** (no source/provider concept — C-8 territory).
- `PriceAlert` — per-user "notify under" subscription.

How data enters today:
- The **separate `merchant_api` service** scrapes live (per-merchant providers) and
  the product-search UI shows results.
- Saving one is `POST /api/products` (`create_product.py`) — **single item,
  logged-in user session, dedupe-by (name+merchant+stockcode)-or-skip**, creates a
  fresh `ProductOffer` each call. A de-facto single-item ingestion, but built for
  interactive UI saves.

**Gaps vs a push seam:** no machine auth (only `AuthToken`, which is email-flow
only), no batching, no idempotency, **no `source` label**, no first-class
`price_observation`, no conflict policy.

---

## 2. The contract

### 2.1 Auth — a machine credential, not a user session
Introduce an **`IngestionSource`** credential, separate from user auth:

- Fields: `id`, `label` (e.g. "companion-scraper", "loyalty-email", "crowd"),
  `key_hash` (SHA-256 of the secret, like `AuthToken.token_hash`), `enabled`,
  `created_at`, `last_used_at`, optional `trust` tier (§2.6 / P8-04).
- The ingestion endpoints authenticate via a **bearer token** (the raw key);
  Dora hashes + matches. **Admin creates/revokes** sources (Settings → admin).
- The authenticated source provides the **default `source` label**; a payload may
  carry a finer `source` (a multi-provider companion pushing for several
  providers) — but only within what its credential is allowed to assert.

> No machine auth exists today, so this is net-new (small: one table + a
> decorator mirroring the existing auth middleware).

### 2.2 Payloads (batched; each record carries `source`)
One endpoint, batched, three record types (per §6.6, fleshed against the model):

```
POST /api/ingest        Authorization: Bearer <source-key>
Idempotency-Key: <client batch id>
{
  "products": [
    { "ref": "<client-stable id>", "name", "brand?", "size?", "size_unit?",
      "size_value?", "merchant", "merchant_stockcode?", "web_url?", "source" }
  ],
  "offers": [
    { "product_ref": "<ref|stockcode>", "price_now", "price_was?",
      "valid_until?", "observed_at", "source" }
  ],
  "price_observations": [
    { "product_ref?" , "stock_item_ref?", "price", "observed_at", "source" }
  ]
}
```

- **product** → upsert into the catalogue.
- **offer** → set the product's `current_offer` + **append a `ProductHistoricOffer`**
  (the price-history point).
- **price_observation** → a lighter point (price + when + source) that may attach
  to a product **or** a stock item, feeding **personal price history** (P6-01
  costing, P6-03 intelligence) without requiring a full product row.

### 2.3 Idempotency & dedup
- **Batch idempotency** via an `Idempotency-Key` header — re-sending the same batch
  is a no-op (store processed keys with a TTL).
- **Record dedup** by natural key: products by **(source + merchant +
  stockcode)**, falling back to (source + merchant + name) when no stockcode;
  offers/observations deduped by **(product, source, observed_at, price)** so a
  re-push doesn't double the history.
- Re-pushing an unchanged offer updates nothing; a changed price appends one new
  historic point and moves `current_offer`.

### 2.4 The `source` seam (where C-8 lands)
Every record carries a **`source` label** — the merchant/provider origin. Today
`Merchant` is only a name and offers have no source. **Minimum for C-10:** store
the `source` string on the historic offer / observation (a column), so provenance
is captured. **Full merchant↔data-provider model is C-8** (companion-informed) —
C-10 just **reserves the seam** (the `source` field + storage), it does not build
the provider taxonomy.

### 2.5 Mapping & ownership (multi-user)
Pushed `product`/`offer` data lands in the **shared catalogue** (all users see it);
**personal price history** is the per-user view that unions pushed data with the
user's **own shopping picks** (the `actual_unit_price` / `picked_offer_price`
snapshots on shopping-list lines — see INV-1). So the ingestion API feeds the
*pushed* half; the user's receipts feed the *personal* half. On a single-user
desktop install this distinction is moot; on a shared install it matters
(open decision §5).

### 2.6 Trust & P8-03/P8-04 reuse
The same contract serves later sources with **different trust**:
- **P8-03 loyalty email** — parsed receipts; high trust (the user's own data).
- **P8-04 crowd** — other users' submissions; **lower trust**. The `IngestionSource.trust`
  tier lets Dora label/segregate crowd observations (e.g. show but don't treat as
  authoritative). Design the contract to carry trust now; enforcement is later.

### 2.7 Errors & response
Per-record results (mirrors the seed endpoint's result-DTO pattern):
`{ accepted, skipped (already-present), failed: [{ ref, reason }] }`. A bad record
never fails the batch.

> **Open (brief):** **sync vs async** (§5) — validate-and-commit inline (simple,
> immediate result) vs accept-202-and-queue (resilient to big batches). Recommend
> **sync for v1** (batches are bounded; simpler), async only if batch sizes grow.

---

## 3. Boundary (the non-negotiable)
- **Sources call in; Dora never calls out.** No scraping, no merchant connections,
  no search/comparison UI in Dora-core — all companion (C-6/C-8).
- Dora owns the product/price **data model** + the "your prices" views; the
  companion owns acquisition.
- This is what keeps Dora-core legally clean and sellable (Decision 1).

---

## 4. From the original spec (historical — `docs/00_original_spec/`)

| Original note | Verdict | Effect |
|---|---|---|
| Taskboard: *"Require an API key to hit the backend API"* | **keep (corroborates §2.1)** | The machine-auth need was anticipated; the `IngestionSource` key is its concrete form for this seam. |
| *"I can manually add product offers to saved scraped products"* | **consider** | A *user-side* manual offer entry — same mapping as an `offer` record but via the UI, not the ingest endpoint. Could share the offer-append path. |
| *"I am notified when a merchant's product comes back in stock"* | **consider → C-9** | A back-in-stock signal could be derived from offer pushes (is_available flips); the alert lives in C-9, fed by ingestion. |

---

## 5. Open decisions (for co-design)
1. **Conflict/overwrite policy for price history** (brief) — proposed **append-only,
   dedup identical (product+source+observed_at+price), never overwrite**. Confirm
   (vs upsert-latest-per-day, or allow corrections).
2. **Sync vs async** (brief) — proposed **sync v1** (§2.7).
3. **`source` storage** — a plain string column now vs a light `DataProvider`
   record; full taxonomy deferred to C-8.
4. **Shared-catalogue ownership** on multi-user installs (§2.5) — does pushed data
   land in one shared catalogue for everyone (proposed), or scope by source/user?
5. **Fate of `POST /products`** — retire it in favour of `/ingest`, or keep it as
   the interactive single-save path (which would then just call the same mapping
   internally)? Proposed: **keep, refactor it to reuse the ingest mapping**.
6. **Trust enforcement** for crowd (P8-04) — carry `trust` now, enforce later
   (proposed), or define enforcement up front?

---

## 6. Suggested sequencing (Phase 2 — after the loop, per master plan)
1. **`IngestionSource` model + bearer-auth decorator** (§2.1) + admin create/revoke.
2. **Payload schema + per-record validation + result DTO** (§2.2, §2.7).
3. **Mapping + dedup + idempotency** (§2.3, §2.5) — products/offers into the
   catalogue + historic log; observations into personal history.
4. **`source` column** on offers/observations (§2.4) — reserve the seam.
5. **Refactor `POST /products`** to reuse the mapping (§5.5); point the **companion**
   at `/ingest`.
6. Later: **P8-03 email** + **P8-04 crowd** as additional sources; trust enforcement.

---

## 7. Coverage & motivation

This is **plan-motivated, not feedback-bullet-motivated** — it exists to enable
Decision 1 (extract the scraper), not to fix a reported UI defect. The only
directly-related inputs:

| Input | Where |
|---|---|
| Taskboard "require an API key to hit the backend API" (original spec) | §2.1 |
| "Product search is very slow" + product-search/merchant feedback | **Companion scope** (C-6/C-8) — this contract is the seam they target, not the fix itself |
| "Manually add product offers" (original spec) | §4 (shared offer-append path) |
| Personal price history / costing (P6-01/P6-03) | §2.2, §2.5 (the destination for observations) |

**Gates:** C-6 and C-8 (the companion targets this contract). **Reused by:** P8-03,
P8-04.
