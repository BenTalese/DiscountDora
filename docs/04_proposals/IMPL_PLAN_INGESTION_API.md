# Implementation Plan — Ingestion API + "Your Prices" intelligence (C-10 impl)

**Status:** Plan for review · **Date:** 2026-06-15 · **No code yet** — phased plan + chunks.
**Source proposal:** `PROPOSAL_INGESTION_API.md` v2 (co-designed 2026-06-15; decisions §5).
**Adjacent:**
- **C-1b (Stock Item Detail)** — its price section consumes the "your prices" layer (C-10.4).
- **C-9 (Alerts)** — optional "inflated price" / back-in-stock alert fed by ingestion (cross-ref).
- **C-5 onboarding / FU-184** — the "your prices" layer is what makes the Insight stage real.
- **C-cross config (done)** — `companion_ingestion_enabled` flag exists; admin settings pattern
  (`SystemSettings.vue` + admin PATCH) is the model for the keys page.
- **FU-180** (preferred product removed — n/a), **FU-053** (best-deals client-side fetch — server
  seam this helps), **FU-045** (Postgres — keep tables portable).
**Phase:** Master plan **Phase 2 (ingestion API)** — after the loop; enables Decision 1 (the
scraper extraction). Touches **§7.5 distribution posture** (machine auth, portable schema,
config-gated, degrades when no source configured).

---

## 0. Verify-state-first: no drift

Re-checked 2026-06-15 (Product/ProductOffer/ProductHistoricOffer + mappings, Merchant,
`create_product.py`, `AuthToken` + `auth_helpers`, middleware `require_auth_if_protected` +
`_require_admin`, `app_setting.py`, `price_history.py` / `get_price_history.py`,
`shopping_list.py` snapshots).

**Already true (reuse):** product/offer model + append-only `ProductHistoricOffer`; `Merchant` =
name only; `create_product` dedupes by (stockcode+merchant+name) and **409s on dup without
appending an offer** (the gap /ingest fixes); session-cookie auth via `require_auth_if_protected`
+ `_require_admin`; `auth_helpers._hash_token` (SHA-256) to mirror; `companion_ingestion_enabled`
flag present but unconsumed; `extra="forbid"` request models + the seed-style `{created,skipped}`
result DTO; `ShoppingListLine` receipt snapshots present. **No** machine auth, `/ingest`,
`PriceObservation`, `source` column, idempotency mechanism, or personal-price-history union.

**Hard rule carried into every chunk (proposal § header):** source-agnostic + **no companion/
scraper references anywhere in the app** (UI, copy, help, settings, empty states).

**Tests:** new `tests/e2e/dora_api/test_ingest*.py`; migrations portable (SQLite + Postgres),
reversible, single head. Backend-heavy → strong e2e; the keys page + price views → vue-tsc/eslint.

---

## 1. Chunked plan (each chunk = one reviewable PR)

### C-10.1 — `IngestionSource` + bearer-auth lane + admin keys CRUD + "API access" Settings page ★ FIRST
**Delivers:** the auth foundation + key management (proposal §2.1).
- **Backend:** `IngestionSource` entity/table/migration (`id, label, key_hash, enabled, trust,
  created_at, last_used_at` + counters for §C-10.3). A **bearer-auth helper** (hash + match +
  enabled; mirrors `_hash_token`) and a way to **exempt `/api/ingest` from the session
  middleware** (add to the middleware's machine-auth allowance / a dedicated check). Admin-only
  CRUD: `GET/POST/DELETE /api/ingestion-sources` (create returns the **raw key once**; never
  re-shown), enable/disable. All gated by `_require_admin`.
- **Frontend:** a new **admin Settings page — "API access"** (generic name): list keys (label,
  enabled, last-used), create (one-time key reveal + copy), disable/revoke. **No scraping/
  companion references.** Reuses the admin settings shell pattern.
- **Risk:** Medium — net-new auth lane; the trap is the middleware exemption (don't accidentally
  open other routes). **Close-gate:** R-005/R-006 (portable reversible migration), §7.5 (machine
  auth behind an interface; degrades when no keys), R-003 (one hashing/auth helper), **invisibility
  rule**. *Acceptance:* an admin mints a key (shown once), `/api/ingest` accepts that bearer +
  rejects a bad/disabled/absent one with 401; revoke takes effect; the page never hints at a
  scraper.

### C-10.2 — `POST /api/ingest` — schema + mapping + dedup + idempotency + share with `create_product`
**Delivers:** the contract itself (proposal §2.2-2.4, §2.7).
- **Backend:** the batched payload model (`extra="forbid"`; products/offers, each with `source`);
  per-record validation; **`Idempotency-Key`** store (small table w/ TTL, re-send = no-op); the
  **upsert/dedup mapping** — products by (source+merchant+stockcode|name), **offers append a
  `ProductHistoricOffer` + move `current_offer`** (fixing the create_product gap), append-only
  dedup by (product+source+observed_at+price); a **`source` string column** on historic offers;
  the per-record **result DTO** `{accepted, skipped, failed[]}` (a bad record never fails the
  batch); **sync** commit. **Refactor `create_product` to reuse the same mapping** (one
  offer-append path — R-003). **FU-227 chunk 7 (2026-06-22):** `price_observations[]` was
  removed from the contract — observations are in-app input only (Idea A); producers that want
  to push item-level points should publish them as `offers[]` (the same historic-offer
  substrate the read-time union already covers).
- **Migrations:** `source` column(s), `IdempotencyKey` table, (maybe) `PriceObservation`.
- **Risk:** Medium-high — the core mapping + dedup + idempotency; correctness of "changed price →
  one new point." **Close-gate:** R-003 (shared mapping; `create_product` + `/ingest` one path),
  R-005/R-006 (migrations), R-010 (validate records), §7.5 (portable). *Acceptance:* a batch
  upserts products, appends history on price change, no-ops on re-send (idempotency) + unchanged
  offers; bad records reported per-record; `create_product` still works via the shared path; price
  history now actually accrues.

### C-10.3 — Keys-page observability
**Delivers:** the admin can see a source working (proposal §2.1).
- **Backend:** record per-source **accepted/skipped/failed** + `last_used_at` on each ingest;
  expose on `GET /api/ingestion-sources`. **Frontend:** show per-key last-used + recent counts.
- **Risk:** Low. **Close-gate:** R-003 (server records, client renders). *Acceptance:* after a
  push, the key's last-used + counts update on the page.

### C-10.4 — "Your prices" intelligence layer ★ (the user-facing payoff)
**Delivers:** proposal §2.5 — the reason any of this matters to the user.
- **Backend:** a **personal price-history service** unioning pushed history (`ProductHistoricOffer`
  / observations for the item's linked products) + **receipt snapshots**
  (`ShoppingListLine.actual_unit_price`/`picked_offer_price` for that stock item) into one
  timeline; compute a **baseline/typical** + an **"above usual" flag**. Server-owned (R-003).
- **Frontend:** surface on the **Stock Item Detail price section (C-1b)** + the existing **Price
  History** page (and feed the optional C-9 alert). Products-layer → **hidden for the Cooking
  persona** (`products_enabled`, FU-182).
- **Risk:** Medium — the union + baseline math; gating by persona. **Close-gate:** R-003
  (server-owned union + baseline; client renders), R-002 (tokens), products_enabled gating,
  **P3/FU-184** (the onboarding "Insight" copy must match what this actually does). *Acceptance:*
  a stock item shows what it's cost across offers + your receipts, flags "more than usual," and
  the Insight onboarding claim is now true; hidden cleanly when products are off.

> Later (separate): P8-03 email + P8-04 crowd sources + trust enforcement; the C-9 inflated-price
> alert type; the **`merchant_api` / in-app live-search decommission** (FU-186).

### C-10.5 — Read-side lookup: "is this product already linked?" (FU-422) ✅ shipped 2026-07-12
**Delivers:** an ingestion source (or any external caller) can decorate its own search results with
an "already linked to a stock item" hint, so a user doesn't try to re-link a product Dora already
has bound. From the original spec — search moved out of Dora, so the rule needs an API hook.
- **Backend (as shipped):** `POST /api/ingest/link-status`. Request shape mirrors the write side —
  `{ items: [{ ref, store, merchant_stockcode?, name? }] }`, stockcode-first / name-fallback
  identity so callers can reuse their `/api/ingest` payload builder. Per-item response
  `{ ref, product_id | null, linked_stock_item_id | null, linked_stock_item_name | null, reason? }`
  (reason ∈ `store_not_mapped` / `product_not_found`). Auth is the existing bearer-key lane from
  C-10.1. Source-agnostic; the response shape says nothing about who is asking (invisibility
  rule). Per-source store-mapping cache scoped to the call. 200-item cap. POST over GET because
  the payload is a batch of tuples, not a single key.
- **Frontend:** none in Dora — MyProducts already shows linked/unlinked state for the local
  catalogue; this endpoint exists so callers *outside* Dora can render the same badge.
- **Risk:** Low. **Close-gate:** R-003 (server owns the fact), R-005 (portable — no
  companion-specific coupling). *Acceptance:* an ingestion source can POST a batch of external-ids
  and receive per-id link status; MyProducts behaviour unchanged.


---

## 2. Sequencing & cross-cutting close-gate
Order C-10.1 → .4 (.1 auth foundation, .2 the contract, .3 observability, .4 the payoff); .5 is a
small read-side add-on that can land any time after .2. The
producer can be pointed at `/ingest` after .2; the user sees value after .4. Cross-cutting:
portable reversible migrations (SQLite+Postgres, single head, §7.5); machine auth behind a helper;
**source-agnostic + zero companion references (invisibility rule)**; one shared offer-append
mapping (R-003); `extra="forbid"` + per-record result DTO; no dead code (R-008); CHANGELOG +
worklog + follow-ups per chunk; e2e + vue-tsc + eslint green.

## 3. Coverage & motivation
Plan-motivated (enables Decision 1), not feedback-bullet-motivated — no COVERAGE_GAPS flip. The
"your prices" layer (C-10.4) is the destination for personal price history (P6-01/P6-03) and the
thing that makes the onboarding Insight stage honest (FU-184).
