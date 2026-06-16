# Proposal — Ingestion API + "Your Prices" intelligence (C-10)

**Status:** Co-designed draft v2 (supersedes 2026-06-06) · **Date:** 2026-06-15 · Changes NO code.
**Scope:** An authenticated, **source-agnostic** inbound endpoint **inside Dora-core (`dora_api`)**
that external sources push product / offer / price data into, with **admin-managed API keys**
(a Settings page) as the auth, and a **"your prices" intelligence layer** that turns the
ingested data + the user's own receipts into a personal price history with a "paying more than
usual" signal. **Dora-core only** — the producer is a separate, private, off-by-default app the
admin runs; **its existence is never referenced anywhere in the app.**

> **Architecture (settled with the user):** the ingestion API is **NOT its own service** — it's
> new routes (`POST /api/ingest`) + a bearer-auth lane inside the existing `dora_api` Flask app
> (the one that owns the DB). No new moving part. The *producer* (an external scraper the admin
> runs) is the separate app; today's `merchant_api` sibling service is the prototype of that
> producer. The charter boundary (P9: Dora never calls out; sources call in) is preserved by
> *direction* — `/api/ingest` is passive inbound — not by hosting it elsewhere.

> **Charter tie-break:** P9 No-scrape + P3 Honest + P12 No-invent. One well-defined inbound door;
> Dora-core stays scrape-free, legally clean, sellable, and **ignorant of who's pushing**.

> **Invisibility principle (HARD RULE — new):** the producer/companion's existence must **not be
> known or referenced anywhere in the app** — no "scraper", "companion", "import deals", brand
> name, or "where do products come from" copy in any UI, empty state, help, or setting. The
> ingestion API is **fully source-agnostic**: it accepts batches from *an authenticated source*,
> full stop. The admin labels their own key (free text); the app never names or assumes the
> other end. These committed planning docs also stay generic about the producer (referenced only
> as "an external/admin-owned ingestion source").

---

## 1. Current state (what we map into)

Products are a **shared catalogue** (no `user_id`):
- `Product` — name, brand, size/size_unit/size_value, `merchant`, `merchant_stockcode`, image,
  is_active, is_available, web_url, **`current_offer`** (1:1 `ProductOffer`), **`historic_offers`**
  (1:N `ProductHistoricOffer`, append-only — what the price-history view reads).
- `ProductOffer` / `ProductHistoricOffer` — `offered_on`, `price_now`, `price_was`.
- `Merchant` — **just `name`** (no source/provider/`is_enabled` — C-8 territory).
- `ShoppingListLine` carries the **user's own receipt snapshots**: `actual_unit_price`,
  `picked_offer_price`, `list_price_at_pick`, `purchased_merchant_id`. **These are the receipts
  half of "your prices" and are not unioned into price history today.**

How data enters today + the gaps:
- `POST /api/products` (`create_product.py`) — single item, session auth, dedupe by
  **(stockcode + merchant + name)**, creates a `ProductOffer`. **Confirmed gap:** it **409s on a
  duplicate and does NOT append a new offer** — so there's *no clean "new price for an existing
  product" path*, and price history barely accrues. The ingestion `offer` record fixes exactly
  this.
- **No machine auth** (session-cookie only: `require_auth_if_protected` middleware + `_require_admin`
  for admin). `IngestionSource` + a bearer lane is net-new but small.
- **`companion_ingestion_enabled` flag exists but nothing consumes it.** No `/ingest`, no ingestion
  folder. `merchant_api` (port 5172) is a sibling scraper service — post-divorce it (or a successor)
  becomes the private external producer that pushes via `/ingest`.
- **No `PriceObservation`**, no `source` label, no batching, no idempotency, no conflict policy.

---

## 2. The contract

### 2.1 Auth — admin-minted API keys (the Settings page)
An **`IngestionSource`** credential, separate from user auth: `id`, `label` (admin free-text,
e.g. "home box"), `key_hash` (SHA-256 of the secret, mirroring `AuthToken.token_hash`), `enabled`,
`trust` (tier, §2.6), `created_at`, `last_used_at`.
- `/api/ingest` is **exempt from the session middleware** and instead validates a **`Bearer
  <key>`** header (hash + match + enabled). A small auth helper mirrors `auth_helpers._hash_token`.
- **Admin Settings page — "API access" (generic name):** create (shows the raw key **once**),
  label, enable/disable, **revoke** keys — plus **observability** per key: `last_used_at` and
  recent **accepted / skipped / failed** counts, so the admin can see a source is working. No
  scraping references anywhere on the page.

### 2.2 Payloads (batched; each record carries `source`)
```
POST /api/ingest        Authorization: Bearer <key>        Idempotency-Key: <batch id>
{
  "products":           [ { ref, name, brand?, size?, size_unit?, size_value?, merchant,
                            merchant_stockcode?, web_url?, source } ],
  "offers":             [ { product_ref, price_now, price_was?, valid_until?, observed_at, source } ],
  "price_observations": [ { product_ref?, stock_item_ref?, price, observed_at, source } ]
}
```
- **product** → upsert the catalogue. **offer** → set `current_offer` + **append a
  `ProductHistoricOffer`** (the history point). **price_observation** → a lighter point (price +
  when + source) that attaches to a product **or** a stock item, feeding personal price history
  without a full product row.

### 2.3 Idempotency & dedup (accepted defaults)
- **Batch idempotency** via `Idempotency-Key` (store processed keys w/ TTL; re-send = no-op).
- **Record dedup:** products by (source + merchant + stockcode), fallback (source + merchant +
  name); offers/observations by (product + source + observed_at + price). **Append-only; never
  overwrite.** Unchanged offer → nothing; changed price → one new historic point + move
  `current_offer`.

### 2.4 The `source` seam (string now; C-8 later)
Every record carries a `source` string; store it as a **column** on historic offers / observations
(provenance). The **full merchant↔provider taxonomy is C-8** — C-10 only reserves the seam.

### 2.5 "Your prices" intelligence layer ★ (the user-facing payoff — in scope)
The reason the data is worth pushing. A **personal price-history service** that **unions**:
- **pushed** data (`ProductHistoricOffer` / observations for products linked to the item), and
- the **user's own receipts** (`ShoppingListLine.actual_unit_price` / `picked_offer_price` for that
  stock item) —
into one per-item/per-product timeline ("what this has cost, from offers *and* what you've paid").
From that series, compute a **typical/baseline price** and a **"paying more than usual" signal**
(latest/current notably above baseline) — the honest, legal "spend smarter" insight (no scraping,
all from data the install already holds).
- **Surfacing (reuse existing surfaces, no new page):** the **Stock Item Detail** price section
  (C-1b consumes this), the existing **Price History** page, and **optionally a C-9 "inflated
  price" alert** (cross-ref; fed by ingestion). **This is also what makes the onboarding "Insight"
  stage real** (FU-184).
- **v1 producer:** designed source-agnostic; the **admin's own private external source** is the
  first producer (high `trust`), with **in-app receipt logging** already contributing the receipts
  half. Parsed receipt emails (P8-03) and crowd (P8-04) are later sources on the same contract.

### 2.6 Trust & later sources
`IngestionSource.trust` is carried now (high = the admin's own data; low = future crowd P8-04) so
observations can be labelled/segregated later; **enforcement is deferred**, the field is captured.

### 2.7 Errors & response
Per-record result DTO (mirrors the seed-result pattern): `{ accepted, skipped, failed: [{ ref,
reason }] }`; a bad record never fails the batch. **Sync (validate-and-commit) v1** (batches are
bounded); async only if sizes grow.

---

## 3. Boundary (non-negotiable)
Sources call in; **Dora never calls out**. No scraping, no merchant connections, no live
product-search/comparison in Dora-core. Dora owns the data model + the "your prices" views; the
external producer owns acquisition. This is what keeps Dora-core legally clean and sellable
(Decision 1) — and the invisibility rule (§ header) keeps the producer unmentioned.

---

## 4. From the original spec (historical)
| Original note | Verdict | Effect |
|---|---|---|
| Taskboard "require an API key to hit the backend API" | **keep** | The `IngestionSource` key is its concrete form (§2.1). |
| "Manually add product offers to saved products" | **keep → share path** | A user-side manual offer-add reuses the same offer-append mapping as an `offer` record. |
| "Notified when a product comes back in stock" | **consider → C-9** | Derivable from offer pushes (is_available flips); the alert lives in C-9, fed by ingestion. |

---

## 5. Resolved decisions (co-design 2026-06-15)
- **In `dora_api` core**, not a separate service. **Source-agnostic + invisible producer** (hard
  rule).
- **Scope = plumbing + admin keys page (CRUD + observability) + the "your prices" intelligence
  layer** (§2.5).
- Auth = admin-minted bearer keys (`IngestionSource`); **keys page is generically named**.
- Sync v1; `Idempotency-Key`; `source` as a string column; **append-only** dedup by
  (product+source+observed_at+price); **keep `POST /products`, refactor to reuse the ingest
  mapping**; **shared catalogue, defer multi-user scoping** (Phase 4); carry `trust`, enforce later.
- **Open (build-time):** whether `price_observations` needs a small new `PriceObservation` table or
  can be a query-time union of historic offers + receipt snapshots (lean to: products+offers fully
  in v1; a minimal observation store only if the producer pushes item-level points).

---

## 6. Suggested sequencing (Phase 2 — after the loop) → IMPL_PLAN_INGESTION_API
1. **`IngestionSource` model + bearer-auth lane + admin keys CRUD + the Settings "API access" page**
   (§2.1).
2. **`POST /api/ingest`** — payload schema + per-record validation + idempotency + result DTO +
   the upsert/dedup mapping into catalogue + historic log + `source` column; **refactor
   `create_product` to share the mapping** (§2.2-2.4, §2.7).
3. **Keys-page observability** — record per-source accepted/skipped/failed + last-used; surface on
   the page (§2.1).
4. **"Your prices" intelligence layer** — the pushed∪receipts union + baseline + "above usual"
   signal; surface on Stock Item Detail (C-1b) + Price History (§2.5).
5. Later: P8-03 email + P8-04 crowd as sources; trust enforcement; the C-9 inflated-price alert.

---

## 7. Ripple & dependencies
- **`merchant_api` / in-app live product search (big ripple):** post-divorce, Dora-core must **not
  scrape live**. The in-app product search that calls `merchant_api` to scrape becomes either a
  search over the **already-ingested catalogue** (products your source pushed) or moves entirely
  to the companion. **This reshapes C-1b's "find & link a product"** (it can't live-search) and is
  a decommissioning sweep — **logged as a follow-up (FU-186)**, not built inside C-10. The same
  follow-up also owns retiring the standalone **`emailer/`** weekly-deals service (scraper-coupled):
  move it into the private companion and finish it there, then delete it here. Transactional
  `email_sender.py` stays; the in-app email need is the C-9.7 alerts digest.
- **C-1b (Stock Item Detail):** consumes the "your prices" layer in its price section.
- **C-9 (Alerts):** an optional "inflated price" / back-in-stock alert type fed by ingestion
  (the price/back-in-stock subscriptions tier C-9 reserved).
- **Onboarding C-5 / FU-184:** the "your prices" layer is what makes the **Insight** stage real —
  validate the onboarding copy against it.
- **FU-180:** preferred product removed; doesn't affect ingestion. **FU-053:** best-deals card
  fetches all products client-side — a server seam this work can help retire.
- **FU-045 (Postgres):** keep the new tables/queries portable (SQLite + Postgres, §7.5).
- **products_enabled (C-5):** the "your prices" surfaces are products-layer — hidden for the
  Cooking persona (FU-182), shown for Spend-tracking/Everything.

---

## 8. Coverage & motivation
Plan-motivated (enables Decision 1's scraper extraction), not feedback-bullet-motivated. Related
inputs: original-spec "API key" (§2.1) + "manually add offers" (§4); personal price history /
costing P6-01/P6-03 (§2.5 is its destination); "product search slow" = **companion scope**, this
is the seam not the fix. **Gates:** the external producer targets this contract. **Reused by:**
P8-03, P8-04, C-9 (alerts), C-1b (detail price section).
