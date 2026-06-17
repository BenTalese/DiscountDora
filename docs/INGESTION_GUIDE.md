# Power-user guide — sourcing product data for Dora

**Audience:** admins and power-users running this install. Not part of the
end-user onboarding (see [PROPOSAL_PRODUCTS_AS_OVERLAY](04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md) §5).

Dora is built to be **legally clean and easy to ship** (Charter Decision 1):
it never scrapes retailer sites, never makes live merchant calls, and never
hosts a deal-comparison engine inside the app. That means the product layer
(My Products, Price History, the per-stock-item Products tab, best-deals) is
**off by default and stays off unless you provide the data yourself**.

You provide the data by pushing it into Dora through one authenticated inbound
endpoint: **`POST /api/ingest`**. As soon as the first record lands, the
product surfaces light up automatically — there is no on/off switch.

## What "lights up" when product data is present

Dora derives the `features.products` capability from **data presence** alone
(`GET /api/health` → `features.products`). The moment a `Product` row exists,
these surfaces appear; the moment the last one is gone, they disappear:

- The **My Products** page (in the side nav, admin section).
- The **Price History** page (with charting + per-product notify-under).
- The per-stock-item **Products** tab (link-to-product, cheapest highlighted).
- Cart / best-deals integrations that depend on linked products.

The **API access** page itself is **always available** (Settings → Admin ·
global → API access) — it is the way you bootstrap the data, so gating it on
data-presence would be a chicken-and-egg.

## Step 1 — mint a key

1. Sign in as an admin and go to **Settings → API access**.
2. **New key** → give it a free-text label (e.g. "home box"). The label is
   for your own bookkeeping — Dora itself never names or assumes anything
   about the source on the other end.
3. **Copy the key immediately.** It is shown **once**. If you lose it, revoke
   it and mint a new one.
4. The new row shows `Created ... · Never used · Accepted 0 / Skipped 0 / Failed 0`.

You can disable a key (without deleting it) or revoke it (delete it). A
disabled or revoked key is rejected with **401** on the next call.

## Step 2 — map the stores you plan to push

Dora **never auto-creates merchants** when you push (FU-190). For each store
name your external source uses, you map it to one of your Dora merchants
through the **Store mappings** panel on the source's row.

Two ways the panel populates:

- **You pre-map it.** Open the source → Store mappings → assign each external
  name to a Dora merchant via the picker.
- **You push and let Dora flag it.** The first time you push a record for an
  unknown external name, Dora creates a **quarantined** mapping
  (`merchant_id` is null), skips that record with reason `store_not_mapped`,
  and surfaces a `pending` badge on the source's header. Open the panel,
  assign it, and re-push.

Either way, **stores are never created on the fly**. The picker only shows
merchants that already exist in this install.

## Step 3 — push records

Call `POST /api/ingest` with:

```http
POST /api/ingest
Authorization: Bearer <your raw key>
Idempotency-Key: <a stable batch id, optional but recommended>
Content-Type: application/json

{
  "products":           [ ... ],
  "offers":             [ ... ],
  "price_observations": [ ... ]
}
```

### Auth

`Authorization: Bearer <key>` against the raw key minted on the API access
page. No session cookie required — the session middleware exempts this one
endpoint. A missing / wrong / disabled key yields **401**.

### Idempotency

Set `Idempotency-Key` to a stable string per batch (UUID, hash, whatever).
If you re-send the same key under the same source within ~7 days, Dora
returns a no-op:

```json
{ "accepted": [], "skipped": [], "failed": [], "idempotent_replay": true }
```

This makes retries safe over flaky networks.

### Payload — records

Each record carries an optional `source` provenance string (defaults to the
source's id if omitted). Empty arrays are fine — push only what you have.

**`products`** — upsert a catalogue entry.

| Field                 | Required | Notes                              |
|-----------------------|----------|------------------------------------|
| `ref`                 | yes      | Stable id in this batch — referenced by `offers` / `price_observations` |
| `name`                | yes      |                                    |
| `merchant`            | yes      | The external store name; resolved via the store mapping |
| `merchant_stockcode`  | no       | Primary dedupe key when present    |
| `brand`               | no       |                                    |
| `size`, `size_unit`, `size_value` | no | Free strings + numeric size |
| `web_url`             | no       |                                    |
| `source`              | no       | Provenance string                  |

Dedupe — a product is matched on **`(merchant_id, merchant_stockcode)`**
first; failing that, **`(merchant_id, name)`**. Source is provenance, **not
identity** — pushing the same product from two different IngestionSources
collapses to one `Product` row (shared catalogue).

**`offers`** — append a price point and move the catalogue's "current" price.

| Field         | Required | Notes                                            |
|---------------|----------|--------------------------------------------------|
| `product_ref` | yes      | Matches a `ref` in `products`                    |
| `price_now`   | yes      | > 0                                              |
| `price_was`   | no       | Defaults to `price_now`                          |
| `observed_at` | yes      | ISO 8601 with timezone preferred                 |
| `source`      | no       |                                                  |

Dedupe — `(product_id, observed_at, price_now)`. Append-only; an identical
record is `skipped` with reason `duplicate`.

**`price_observations`** — a single price point, anchored either to a product
(routes into the same historic-offer substrate as `offers`) or to one of your
**Dora stock items** by id.

| Field            | Required | Notes                                       |
|------------------|----------|---------------------------------------------|
| `product_ref`    | one-of   | Targets a product pushed in this batch      |
| `stock_item_ref` | one-of   | The Dora stock-item UUID                    |
| `price`          | yes      | > 0                                         |
| `qty`            | no       | Quantity for the per-unit derivation        |
| `unit`           | no       | Unit string                                 |
| `observed_at`    | yes      |                                             |
| `source`         | no       |                                             |

Exactly one of `product_ref` and `stock_item_ref` must be set.

### Result DTO

Bad records never fail the batch. The response groups every record into
`accepted`, `skipped`, or `failed`:

```json
{
  "accepted": [
    { "kind": "product", "ref": "p1", "id": "...", "note": "created (...)" },
    { "kind": "offer",   "ref": "p1", "id": "...", "note": "appended" }
  ],
  "skipped": [
    { "kind": "offer", "ref": "p1", "reason": "duplicate" }
  ],
  "failed": [
    { "kind": "offer", "ref": "p9", "reason": "product_unknown" }
  ],
  "idempotent_replay": false
}
```

Stable `reason` codes (will only grow, not change meaning):

- `store_not_mapped` — the external `merchant` name has no resolved mapping.
- `duplicate` — same `(product, observed_at, price)` already on file.
- `product_unknown` — an offer / observation referenced a `ref` not in this
  batch's products and no existing product matched.
- `stock_item_ref_not_uuid` — a `price_observation.stock_item_ref` wasn't a
  UUID.

Every batch also bumps the source's **Accepted / Skipped / Failed** counters
(visible on the API access page) and refreshes its `last_used_at`.

## The Product Search nav entry

When product data is present, Dora's left nav surfaces a **Product Search**
link. By default this points nowhere — set the **Product search URL** in the
admin app settings to point at whatever search surface you run yourself. From
the user's perspective it just looks like "Product Search"; Dora never names
or references the destination.

This is the **only** outward link the Dora app ever opens — and only when
product data exists (data-gated). See
[PROPOSAL_PRODUCTS_AS_OVERLAY](04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md) §4.1.

## Trust tiers

The `IngestionSource.trust` column is captured but not yet enforced
(`high` is the default). It exists so that future low-trust sources (e.g.
crowd-sourced pushes) can be labelled and filtered without a schema change.
For now, treat all keys as equally privileged — issue them only to producers
you actually trust.

## What this guide deliberately does not say

- **Where the data comes from.** That's your call. Dora is source-agnostic
  by design; the in-app surfaces never name a producer.
- **Whether you should scrape, parse receipt emails, or hand-curate.** All
  three feed the same `/api/ingest` contract. Dora doesn't care.

For the design rationale, see
[PROPOSAL_INGESTION_API](04_proposals/PROPOSAL_INGESTION_API.md) and the
runbook at [PRODUCTS_OVERLAY_RUNBOOK](04_proposals/PRODUCTS_OVERLAY_RUNBOOK.md).
