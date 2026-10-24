# Chunk 16 — Ingestion API + companion seam

**Session:** 2026-10-23 overnight (solo, no subagents) · **Stage:** 1 (analysis only — no code changed)
**Surface:** the machine-facing door into Dora and the admin page that controls it — `POST /api/ingest` (batch upsert), `POST /api/ingest/link-status`, `GET /api/ingest/products`, `DELETE /api/ingest/products/<id>`, `GET /api/ingest/stores` + `/stores/<id>/image`; the bearer-key lane (`infrastructure/ingestion_auth.py`), the shared offer-append rule (`offer_mapping.py`), admin CRUD over `IngestionSource` + `IngestionStoreMapping`, the `/settings/admin/api-access` page, the power-user guide `docs/INGESTION_GUIDE.md`, and the *contract* half of the companion (`../dora-companion/companion_common/dora_ingest.py`, `merchant_api/features/push_to_dora.py`) — read only to check both sides still agree.
**Boundaries:** everything the pushed data turns into (My products, price history, deals, `StoreLogo`) → chunk 10; `PATCH /products/<id>` price bypass of the offer rule → 10-R5 (already recorded); the Product Search nav link + `product_search_url` → 13-R4; the companion's own UI/scrapers/health (feedback `# PRODUCT SEARCH` bullets 2–6, 8, 12–31) → companion repo (FU-924/891/886/887 hold its debts); session-cookie auth, CSRF for the SPA → chunk 15; the "Dora Stores" page → chunk 13.

---

## 0. Reading list + files walked

**Governing docs read:** `PROPOSAL_INGESTION_API.md` (§2.1–2.7 contract, §5 resolved decisions — no open-decisions block, §8 coverage), `IMPL_PLAN_INGESTION_API.md` (§0 verify-state, C-10.1–10.5, §3), `PROPOSAL_PRODUCTS_AS_OVERLAY.md` §3.3 (store mapping) / §4.3 (API page never products-gated) / §7 (closed), `PRODUCTS_OVERLAY_RUNBOOK.md` status table (Phases B, C, D DONE), `docs/INGESTION_GUIDE.md` (209 lines — the power-user doc FU-212 produced), feedback `# PRODUCT SEARCH` (31 bullets, lines 156–188). Open FUs: FU-919 (name-based mapping unused by the companion — owner decision), FU-918 (companion 502 — confirm on the owner's setup), FU-924 (companion debts; (d) says the proposal omits `image`), FU-891/886/887 (companion repo). Resolved and consulted via code comments: FU-190 (never auto-create stores), FU-227 J1 (observations removed from the producer path), FU-232 (`pack_count`), FU-422 (link-status), FU-866 (one shared auth gate; the install-wide switch later dropped by migration `e7a2c4f9b361`).

**Backend walked in full (1,821 lines):**

| File | Lines | Role |
|---|---|---|
| `dora_api/features/ingestion/submit_ingestion_batch.py` | 495 | `POST /api/ingest` — schema, dedupe, idempotency, store resolution |
| `dora_api/features/ingestion/offer_mapping.py` | 100 | shared append-only offer rule (also used by `create_product`) |
| `dora_api/features/ingestion/get_link_status.py` | 268 | `POST /api/ingest/link-status` |
| `dora_api/features/ingestion/get_ingestable_products.py` | 187 | `GET /api/ingest/products` (the refresh list, PF-7/PF-8) |
| `dora_api/features/ingestion/get_ingest_stores.py` | 138 | `GET /api/ingest/stores`, `/stores/<id>/image` |
| `dora_api/features/ingestion/delete_ingested_product.py` | 64 | `DELETE /api/ingest/products/<id>` → `DeleteProductHandler` |
| `dora_api/features/ingestion_sources/ingestion_source_admin.py` | 220 | admin CRUD over `IngestionSource` |
| `dora_api/features/ingestion_sources/store_mappings.py` | 205 | admin CRUD over `IngestionStoreMapping` |
| `dora_api/infrastructure/ingestion_auth.py` | 128 | hash / mint / find / `authenticate_ingestion_request` / `stamp_used` |
| `dora_api/domain/entities/{ingestion_source,ingestion_store_mapping,product_offer,idempotency_key}.py` | 41+35+17+23 | entities |
| `dora_api/persistence/table_mappings.py:1210–1265, 1320–1329` | — | the three tables + unique indexes |
| `dora_api/infrastructure/middleware.py:29–66, 236–252` | — | `PUBLIC_ENDPOINTS`, `CSRF_EXEMPT_ENDPOINTS` |

**SPA walked in full (683 lines):** `pages/settings/ApiAccessSettings.vue` (572), `services/api/ingestionSourcesApiService.ts` (110); `router/routes.ts:512–515`; `HelpPage.vue:466–474` (the one entry that mentions the seam); `assistant/app_knowledge.py:21–22`.

**Tests read (45 pytest, 0 vitest):** `tests/e2e/dora_api/test_ingest_batch.py` (12), `test_ingest_link_status.py` (9), `test_ingest_list_products.py` (7), `test_ingest_stores.py` (6), `test_ingestion_sources.py` (5), `test_ingestion_store_mappings.py` (6); `test_delete_product.py:140–165` (the bearer delete door); `test_route_auth_enforcement.py:140, 207–214` (anonymous + admin sweeps cover every admin route here).

**Companion seam read (contract half only):** `companion_common/dora_ingest.py` (~530: `build_payload`, `push_offers`, `check_link_status`, `fetch_saved_products`, `delete_product`, `fetch_dora_stores`, `fetch_store_image`, `check_target`), `merchant_api/features/push_to_dora.py` (~230). 63 companion tests exist on this contract; not run.

**Verification greps run:** `valid_until` in `dora_api` (**none** — proposal §2.2 names a field that was never built); `\.trust\b|TRUST_LOW|TRUST_HIGH` outside the entity + admin file (**none** — trust is stored, never read; proposal §2.6 says enforcement deferred); `scrapedProductOfferLogic` across `web_app/src` + `web_app/test` (**only the definition** — a Phase-D leftover); `captionFor` (`ApiAccessSettings.vue:41,370` — always returns `''`); `stamp_used(` callers (4 of the 6 bearer routes; the two `/stores` routes don't); `metadata.tables` under ingestion (5 raw readers: `get_ingestable_products.py:81,89`, `get_ingest_stores.py:49`, `get_link_status.py:217`, `ingestion_auth.py:43`); `6_000_000` (**9 copies** of the image cap: `update_me.py:80`, `submit_ingestion_batch.py:106`, `create_product.py:33`, `update_product.py:37`, `create_recipe.py:158`, `update_recipe.py:149`, `manage_stores.py:135,191`, `update_user_as_admin.py:42` — plus the companion's `MAX_IMAGE_DATA_URL_CHARS`); `IdempotencyKey|idempotency` (no purge path anywhere — only the lookup + the insert); unique index `ix_idempotency_key_source_key` on `(source_id, key)` (`table_mappings.py:1320`, migration `e7a1c3b8d5f4:42`); `product_links.linked_stock_items` (**exists**, `products/product_links.py:25` — returns `{product_id: LinkedStockItem(stock_item_id, name)}`, exactly what `get_link_status._stamp_linked_stock_items` re-implements); `is_custom` in `get_link_status.py` (**absent** — the read side has no OD-2 filter, the write side does at `submit_ingestion_batch.py:345–346`); `is_available` writers (`submit_ingestion_batch.py:408` hardcodes `True`; the SPA renders an OUT OF STOCK badge on `!is_available` at `ProductCard.vue:38` / `ProductRow.vue:39`; the companion's `_OfferLike.is_available` is declared at `dora_ingest.py:42` and never put in the payload); `text-color="white"` ×4, `$q.dialog` ×2, `HelpHint` ×0 in `ApiAccessSettings.vue`; `INGESTION_GUIDE.md` for `store_id|image|/stores|/products|link-status` (**none** — the guide still documents `merchant` as the required store field, line 108, and "Dora merchants" / `merchant_id` at 46–53); `storesApiService.ts` (exists — `listAsync(): Page<Store>`; `ingestionSourcesApiService.listStoresAsync` re-declares the call and a `DoraStore` type against `/stores`).

---

## A. Full Systems Test — Ingestion API + API access

### A1. Preconditions
- An admin session; at least one Dora store created (Settings → Stores); a terminal with `curl` (or the companion configured with `DORA_INGEST_URL` + `DORA_INGEST_KEY`).
- One run on SQLite, one on Postgres (the idempotency expiry path depends on DateTime(timezone) round-tripping — the code carries a SQLite tz-coercion comment at `submit_ingestion_batch.py:252–258`).
- A second, non-admin user for the permission edges.

### A2. Golden path (persona: self-host admin wiring an external producer)
| # | Step | Expect |
|---|---|---|
| G1 | Settings → Admin → **API access** | Header "API access — Bearer keys for authenticated sources that push data into Dora"; empty state "No keys yet…"; Refresh + **New key** actions. Page reachable with zero products (never gated on `features.products`). |
| G2 | New key → label "home box" → Create | Reveal-once dialog "Copy this key now"; copy → toast "Key copied"; Done. Row appears: avatar key icon in primary, "Created …", "Never used", "Accepted 0 · Skipped 0 · Failed 0". `GET /ingestion-sources` never carries `key` or `key_hash`. |
| G3 | `curl -H "Authorization: Bearer <key>" POST /api/ingest` with one product using `"store": "ExternalMart"` + one offer | 200 `{accepted: [], skipped: [{kind: product, ref, reason: store_not_mapped}], failed: [{kind: offer, reason: product_unknown}], idempotent_replay: false}`. Row counters: Skipped 1 · Failed 1; "Last used" stamped. |
| G4 | Expand the row | **Store mappings** card lists "ExternalMart" with a `pending` badge, "Awaiting mapping · last pushed …"; the row header shows "1 pending". |
| G5 | Pick a Dora store in the picker | `PUT …/store-mappings` → badge gone, caption "→ <store>". |
| G6 | Re-push the same batch (new `Idempotency-Key`) | `accepted: [product "created (provenance: …)", offer "appended"]`. Product appears under My products at that store with the pushed price (chunk 10). Counters: Accepted +2. |
| G7 | Re-push the identical batch with the **same** `Idempotency-Key` | 200 `idempotent_replay: true`, all three arrays empty, counters unchanged. |
| G8 | Re-push with a new key, same `observed_at` + `price_now` | product `updated`; offer `skipped: duplicate`. New price at a new `observed_at` → `appended` and the product's current price moves. |
| G9 | Push by `store_id` instead of `store` (the companion's path) | Accepted without any mapping row; an unknown id → `skipped: store_unknown`; both fields at once → 400 "Give exactly one of `store` or `store_id`". |
| G10 | `POST /api/ingest/link-status` with the same `(store, merchant_stockcode)` | `product_id` set, `linked_stock_item_*` null. Link the product to a stock item in Dora → repeat → `linked_stock_item_id` + name filled. |
| G11 | `GET /api/ingest/products` | The pushed product listed with `store` = "ExternalMart" (the caller's own name), `store_id`, `merchant_stockcode`. Mark the product inactive in My products → it drops out of the list (PF-8). |
| G12 | `DELETE /api/ingest/products/<id>` | 204; gone from My products; second call 404. |
| G13 | `GET /api/ingest/stores` + `/stores/<id>/image` | Every Dora store with `has_image`; the image route serves the uploaded logo with `Cache-Control: max-age=3600`, 404 when none. |
| G14 | Overflow menu → **Disable** | Badge "disabled", avatar greyed; next push → 401 "Bearer token missing or invalid." Enable → accepted again. |
| G15 | Rename → "garage box" | Header label updates in place. |
| G16 | **Revoke** → confirm | Row removed; push → 401; `GET …/store-mappings` for that id → 404 (mappings cascade-deleted). |

### A3. Edge cases
- Missing header / `Basic` scheme / empty token / unknown key → 401 on every `/api/ingest*` route (middleware exempts them from the session cookie; auth is entirely in `authenticate_ingestion_request`).
- Non-admin session on `/api/ingestion-sources*` → 403 (pinned by `test_route_auth_enforcement.py:207–214`); anonymous → 401. The SPA route is admin-gated by the shared `admin/*` router guard.
- Malformed JSON / unknown field (`price_observations[]`, `merchant`) → 400 `{detail: "Malformed payload.", errors: "<pydantic text>"}` — the batch is rejected whole, nothing lands (contrast: a bad *record* never fails the batch).
- `pack_count: 0`, `price_now: 0`, `size_value: 0` → 400 (Field `gt=0`); `price_was` absent → stored as `price_now`.
- An image that isn't a `data:image/…;base64,` URL → dropped, product still accepted, previous image kept; > 6,000,000 chars → whole-batch 400 (the companion drops such images client-side before sending).
- Store deleted in Dora while mapped → mapping's `store_id` goes NULL (`ondelete=SET NULL`) → next push for that name quarantines again with `store_not_mapped`; a push by the deleted `store_id` → `store_unknown`.
- Hand-entered (custom) product with the same name at the same store → ingest creates its own row (OD-2) — **but `link-status` reports the custom row as "already in Dora"** (16-R8).
- Product pushed with **no offer** (companion: out-of-stock, `price_now ≤ 0`) → lands as an *available* product at **$0.00** (16-R5).
- Replay of an `Idempotency-Key` **after its 7-day TTL** → 500 (16-R2).
- link-status with 201 items → 400 (`_MAX_ITEMS = 200`); `GET /ingest/products?limit=banana|0`, `offset=-1` → 400; `limit=9999` silently capped at 500.
- Rate limiting: none on the bearer lane (32-byte `token_urlsafe` keys; brute force infeasible — waived, see C9).
- Phone width: the row's three actions collapse into one overflow menu (owner 2026-10-15); mapping rows wrap the picker under the name at < 600 px.

### A4. Persona coverage
| Fresh install | Dense | Minimal | Power | Admin | Multi-user | Self-host op | Managed |
|---|---|---|---|---|---|---|---|
| ✓ (page works with zero products) | – | – | ✓ (curl path, guide) | ✓ (owner of the page) | ✓ (members: 403 on API, no nav entry) | ✓ (key lives in the producer's env; proxy/TLS → chunk 19) | ✓ (same artifact; key per instance) |

### A5. Load-bearing conditions
- **Postgres + SQLite** — idempotency `expires_at` tz round-trip; unique index behaviour on replay (16-R2).
- **360×640** — the API access row + mapping picker wrap (owner-fixed 2026-10-15; keep as a regression check).
- **Bad network** — the companion treats a non-2xx as "Push failed"; the body text is what the user reads (16-R34).
- Themes × light/dark — `text-color="white"` badges on `warning`/`grey` (D-002 floor on Pesto Dark; C11).

### A6. Release-gate rows
1. Mint → copy → push → counters → revoke → 401 round-trip (G2–G3, G14–G16) on the release build.
2. Idempotent replay is a no-op, and a replay after the TTL does **not** 500 (G7 + 16-R2 fix).
3. `link-status` never reports a custom product (16-R8 fix) — the companion's "unsave" deletes by that id.
4. The power-user guide's sample `curl` body is accepted verbatim by the release build (16-R1).

---

## B. Help content — Ingestion API + API access

### B1. Current help audit
- `HelpPage.vue:466–474` — "Search for products" (group *Shopping & deals*): *"Product Search opens an admin-configured external search surface in a new tab. The destination pushes data back into Dora via the ingestion seam."* — "ingestion seam" and "external search surface" are engineering vocabulary, not copy (D-rules: plain-English voice). Stale in spirit too: the entry routes to `/` while the link lives in the nav. **Reword.**
- `app_knowledge.py:21–22` — the same two sentences for DoraBot. **Reword** (B3).
- No entry anywhere for **API access**, keys, store mappings, or why a push was skipped. `ApiAccessSettings.vue` has no `HelpHint`. The in-page copy is good (header description, mapping explainer at :131–135, empty states, reveal-once warning) — the help entries below mostly lift it.
- `docs/INGESTION_GUIDE.md` is the producer-facing doc and is **wrong on the wire** (16-R1) — a reader following it gets a 400.
- Invisibility rule (`PROPOSAL_INGESTION_API` header): nothing below may name a scraper, companion or producer. Honoured in every entry.

### B2. Help entries

#### Create an API key (admin)
- **Group:** Settings & admin
- **What it does:** Lets an outside program you run push products and prices into Dora. Each key is a separate "source" with its own label.
- **When it fires / how to trigger it:** Settings → Admin → API access → New key. The key is shown **once**, right after you create it — copy it then.
- **What controls it:** `/settings/admin/api-access`. Admins only. Works before any product data exists.
- **What it costs / might get wrong:** Anyone holding the key can add, update or delete products in this install (it can't sign in as you or read anything else). Lose it → revoke and make a new one; there is no "show again".
- **Related:** Disable or revoke a key · Map the store names a source uses · See whether a source is working.
- **Chip:** `ApiAccessSettings.vue:3–8` (SettingsPageHeader title slot) → `<HelpHint topic="Create an API key (admin)">`.
- **Source:** PROPOSAL_INGESTION_API §2.1; `ingestion_source_admin.py`.

#### Map the store names a source uses (admin)
- **Group:** Settings & admin
- **What it does:** When a source pushes a product under a store name Dora hasn't seen, the record is held back and the name shows as *pending* under that key. Pick which of your stores it means and the next push goes through.
- **When it fires / how to trigger it:** Automatically on the first push with an unknown name; or pre-map by expanding the key's row. A source can also name your stores by id and skip this entirely.
- **What controls it:** The *Store mappings* card under each key on `/settings/admin/api-access`. Stores themselves are managed under Settings → Stores — Dora never creates a store from a push.
- **What it costs / might get wrong:** Records pushed before you map the name are **not** queued — the source has to push them again. Clearing the picker puts the name back to pending; the bin drops the mapping entirely.
- **Related:** Create an API key · Why a push was skipped · Manage stores (admin).
- **Chip:** `ApiAccessSettings.vue:127–130` (card subtitle "Store mappings") → `<HelpHint topic="Map the store names a source uses (admin)">`.
- **Source:** FU-190; PROPOSAL_PRODUCTS_AS_OVERLAY §3.3; `store_mappings.py`, `submit_ingestion_batch._resolve_store`.

#### See whether a source is working (admin)
- **Group:** Settings & admin
- **What it does:** Each key's row shows when it was last used and running totals of records accepted, skipped and failed, so you can tell a silent source from a working one.
- **When it fires / how to trigger it:** Updated on every push, lookup or list the source makes. Refresh the page to see new numbers.
- **What controls it:** Always on — no setting. The totals never reset; revoke and re-create the key to start from zero.
- **What it costs / might get wrong:** "Accepted" counts records, not products — a product with its price is two. A re-sent batch Dora recognised as a repeat changes nothing.
- **Related:** Why a push was skipped · Create an API key.
- **Chip:** none (the caption line is the surface).
- **Source:** PROPOSAL_INGESTION_API §2.1 observability; `IngestionSourceDto`.

#### Why a push was skipped (admin)
- **Group:** Settings & admin
- **What it does:** Dora answers every record individually: *accepted*, *skipped* (store not mapped, store unknown, price already on file) or *failed* (price for a product that wasn't in the batch). One bad record never blocks the rest.
- **When it fires / how to trigger it:** In the response the source receives, and in the totals on the key's row.
- **What controls it:** Always on — no setting.
- **What it costs / might get wrong:** A batch with a field Dora doesn't know is refused **whole** (nothing lands) — that's the one case where fixing one record fixes all of them. Dora never overwrites a product you typed in yourself; a pushed match gets its own entry.
- **Related:** Map the store names a source uses · See whether a source is working.
- **Chip:** none.
- **Source:** PROPOSAL_INGESTION_API §2.7; `IngestBatchResult`; OD-2 in `_apply_product`.

#### Disable or revoke a key (admin)
- **Group:** Settings & admin
- **What it does:** *Disable* pauses a source — pushes are refused until you enable it again, mappings and totals stay. *Revoke* deletes the key for good, with its store mappings.
- **When it fires / how to trigger it:** The ⋮ menu on the key's row.
- **What controls it:** `/settings/admin/api-access`.
- **What it costs / might get wrong:** Neither removes the products the source already pushed — delete those under My products. A revoked key can't be restored; make a new one and update the program that uses it.
- **Related:** Create an API key.
- **Chip:** none.
- **Source:** `ingestion_source_admin.py` PATCH/DELETE; `IngestionStoreMapping` FK `ondelete=CASCADE`.

#### Search for products *(reword of the existing entry)*
- **Group:** Shopping & deals (unchanged)
- **New summary:** *"Product Search opens a search page your admin has set up, in a new tab. Anything you save there turns up under My products in Dora, at the store it was found."* Path → `/my-products` (chunk 10 owns the destination; today's `/` is wrong).
- **Source:** 13-R4 (members must see the link), FU-186, PROPOSAL_PRODUCTS_AS_OVERLAY §4.1.

### B3. DoraBot corpus delta
Replace `app_knowledge.py:21–22` with:
> - Product Search: a link in the left nav that opens a search page the admin configured, in a new tab. Products saved there appear under My products.
> - API access (admin): Settings → Admin → API access creates keys an outside program uses to push products and prices into Dora. Each key shows when it was last used and how many records were accepted, skipped or failed; unknown store names wait there as "pending" until the admin maps them to a Dora store.

---

## C. Senior review — Ingestion API + companion seam

### C1. Bugs (verified or high-confidence latent)

**16-R1 — The power-user guide documents a payload the API rejects.** class: docs-as-contract · where: `docs/INGESTION_GUIDE.md:46–53, 108, 172` (and `PROPOSAL_INGESTION_API.md:§2.2` lines 70–76) · what's wrong: the required store field is documented as `merchant` (Phase-E rename made it `store`, and `store_id` was added 2026-10-15); `extra="forbid"` means a reader following the guide gets `400 Malformed payload … Extra inputs are not permitted … Give exactly one of store or store_id`. The guide also still says "Dora merchants"/`merchant_id` for the mapping table, and documents **none** of `store_id`, `image`, `GET /api/ingest/products`, `DELETE /api/ingest/products/<id>`, `GET /api/ingest/stores(+/image)`, `POST /api/ingest/link-status`. The proposal §2.2 additionally lists `valid_until` (never built — grep: none) and omits `image` (FU-924 d). · exact change: rewrite guide Step 2 (stores, not merchants; `store` **or** `store_id`), Step 3 field table (`store`/`store_id`, `image`, drop `merchant`), add a "Read-side endpoints" section (products list + paging, link-status, stores + image, delete) with one `curl` each; in the proposal §2.2 replace the payload block with the current shape and strike `valid_until` with a one-line "never built" note · blast: S (docs) · guard: none — the A6.4 release row is the check · verdict: **execute** · tracked: FU-924 (d) partially.

**16-R2 — Replaying an `Idempotency-Key` after its 7-day TTL raises on commit (500) and loses the batch.** class: verified latent bug · where: `submit_ingestion_batch.py:245–271` · what's wrong: `_already_processed` returns `False` for an **expired** row (:258–261, comment "the new write will replace it") but `_stamp_idempotency` (:264–271) *adds* a second `IdempotencyKey` with the same `(source_id, key)` — the unique index `ix_idempotency_key_source_key` (`table_mappings.py:1320`; migration `e7a1c3b8d5f4:42`) rejects it at `save_changes()` (:240), **after** the whole batch has been applied in the session, so the IntegrityError rolls everything back and the producer sees a 500. Any producer that reuses a stable key (the companion's `idempotency_key` parameter — "e.g. the scheduler tick id") will hit this a week after first use. · exact change: have `_already_processed` return the existing row (or `None`); when it is expired, refresh `expires_at`/`created_at` on that row in `_stamp_idempotency` instead of adding; when absent, add. Fix the misleading comment. · blast: S · guard: none → D1 (must-write) · verdict: **execute**.

**16-R3 — Idempotency rows are never purged; "the table stays bounded" is false.** class: verified · where: `submit_ingestion_batch.py:68–71, 264–271`; `idempotency_key.py` docstring · what's wrong: nothing reads `expires_at` except the single-row lookup; every companion save generates a fresh `uuid4` key (`dora_ingest.py:217`) → one row per push, forever. Revoking a source also orphans its rows (`source_id` is `String(36)` with no FK). · exact change: in `_stamp_idempotency`, before adding, delete rows where `expires_at < now` (repository `.all(field_expires.lt(now))` → `remove`, or one bulk `delete()`); one line, bounded by the TTL. · blast: S · guard: D2 (nice) · verdict: **execute**.

**16-R4 — `GET /api/ingest/stores` and `/stores/<id>/image` never stamp `last_used_at`.** class: verified inconsistency · where: `get_ingest_stores.py:43–62, 65–80` vs the other four bearer routes (`submit_ingestion_batch.py:234`, `get_link_status.py:260`, `get_ingestable_products.py:180`, `delete_ingested_product.py:60`) · what's wrong: a source that only lists stores (the companion's first-run store sync, `check_target` aside) shows "Never used" on the API access page. · exact change: in `ingest_list_stores`, keep the returned `source`, call `stamp_used(source)` + `SqlAlchemyRepository().save_changes()` (mirror `get_ingestable_products.py:176–181`); leave the image route alone (cached, hot). · blast: S · guard: D4 · verdict: **execute**.

**16-R5 — A product pushed without an offer lands as an *available* product at $0.00.** class: verified latent (contract gap) · where: `submit_ingestion_batch.py:398–418` (`ProductOffer(price_now=0.0, price_was=0.0)`, `is_available=True`); companion `dora_ingest.build_payload:185–187` (omits the offer when `price_now <= 0`, i.e. out of stock / price unavailable) · what's wrong: the SPA renders `formatMoney(price_now ?? 0)` → "$0.00" (`ProductCard.vue:59`) and never shows the OUT OF STOCK badge because `is_available` is hardcoded `True`, although the badge exists (`ProductCard.vue:38`, `ProductRow.vue:39`) and the companion already holds `is_available` (`_OfferLike:42`) — it just isn't on the wire. The comment at :394–397 ("v1 producers always push an offer") no longer holds since the companion's price normalisation (FU-918 fix). · exact change (two repos): add `is_available: bool | None = None` to `_ProductIn`; on create set `is_available=raw.is_available if not None else True`, on update `existing.is_available = raw.is_available if raw.is_available is not None else existing.is_available`; companion `build_payload` sends `"is_available": offer.is_available`. Leave the $0 initial offer (changing `current_offer` nullability is L). · blast: M (cross-repo) · guard: D3 · verdict: **FU** (needs the companion change in the same window; owner-visible behaviour) · see §E.

**16-R8 — `link-status` reports a hand-entered (custom) product as "already in Dora"; the companion's *unsave* then deletes it.** class: verified · where: `get_link_status.py:179–201` (`_find_product` — no `is_custom` filter) vs `submit_ingestion_batch.py:345–370` (`not_custom` on both lookups, OD-2) · what's wrong: read and write disagree on identity. A user who typed "Mince" at Woolworths, then searches "Mince" in the companion, sees a filled heart (in Dora + maybe linked), and tapping it calls `DELETE /api/ingest/products/<custom id>` → `DeleteProductHandler` removes the user's own product (the delete door has no custom guard either — PF-4 says it shouldn't need one, because the id should never have been handed out). · exact change: extract `find_ingested_product(repository, store_id, stockcode, name) -> Product | None` (stockcode-first, name fallback, `not_custom`) into `features/ingestion/product_identity.py`; use it from both `_apply_product` and `_find_product`. · blast: S · guard: D5 (must-write) · verdict: **execute**.

**16-R34 — Validation errors go to the producer as one concatenated pydantic string.** class: verified (feedback-linked) · where: `submit_ingestion_batch.py:476–479`, `get_link_status.py:253–256` (`"errors": str(exc)`) · what's wrong: `str(ValidationError)` is the multi-line text the owner saw as *"Extra inputs are not permitted Extra inputs are not permitted …"* ×5 (feedback `# PRODUCT SEARCH` bullets 9–11); the companion surfaces `response.text[:500]` verbatim (`dora_ingest.py:243`). · exact change: return `exc.errors(include_url=False)` (a list of `{loc, msg, type}`) under `errors`, keep `detail`; or route both through `has_request_body` / 15-R7's `api_response.validation_failed`. · blast: S (the companion only displays it) · guard: `test_ingest_batch::test__ingest__rejects_price_observations_field` asserts on the text — adjust to the list · verdict: **execute** (with 16-R9).

### C2. Redundancy / DRY (R-001, R-003)

**16-R6 — The store-mapping lookup is written three times.** where: `submit_ingestion_batch.py:283–292` (write side, quarantines), `get_link_status.py:166–175` (read side), `store_mappings.py:116–125` (admin upsert) — each builds `EntityField(SOURCE_ID)` & `EntityField(EXTERNAL_NAME)` and `.one(...)`. change: `IngestionStoreMapping` gets a module-level `find_mapping(repository, source_id, external_name)` (or a static on the entity's repository helper); three call sites. blast: S · guard: existing 6 mapping tests + 3 quarantine tests · verdict: **execute**.

**16-R7 — `_stamp_linked_stock_items` re-implements `product_links.linked_stock_items`.** where: `get_link_status.py:203–241` (39 lines, raw `db.metadata.tables["StockItemProduct"]` select + `StockItem` lookup) vs `products/product_links.py:25` which already returns `{product_id: LinkedStockItem(stock_item_id, name)}` and is shared by the products list, best-deals and the price-drop alert. The docstring (:208–213) explains why it isn't the *DTO-mutating* helper — but the lower-level map helper is right there. change: `links = linked_stock_items(self.repository, [p.id for _, p in resolved])`, then build the `_LinkStatusResult`s; delete the private method, the `select`/`db`/`StockItem` imports. blast: S · guard: `test_ingest_link_status` (9) · verdict: **execute**. Also clears one FU-923 raw-table reader.

**16-R9 — Two bearer routes hand-roll the body-parse-and-400 that `has_request_body` already does.** where: `submit_ingestion_batch.py:476–479`, `get_link_status.py:253–256` vs `@has_request_body(...)` on every admin route in this chunk. change: decorate both routes, read with `get_request_body()`; the decorator's error shape then also fixes 16-R34 (verify it emits structured errors; if it emits text, fix it there — one place). blast: S · guard: the two `rejects_*` tests · verdict: **execute**.

**16-R10 — `_one_store` validator duplicated.** where: `submit_ingestion_batch.py:109–113`, `get_link_status.py:74–78`. change: `class _StoreRef(BaseModel)` mixin with `store`/`store_id` + the validator in `product_identity.py` (16-R8's module); `_ProductIn(_StoreRef)`, `_LookupItem(_StoreRef)`. blast: S · verdict: **execute**.

**16-R11 — The 6,000,000-char image cap is written 9× in `dora_api` (+ once in the companion).** where: see §0 grep. change: `infrastructure/images.py: MAX_IMAGE_DATA_URL_LEN = 6_000_000` + one `ImageField = Field(default=None, max_length=MAX_IMAGE_DATA_URL_LEN)`; 9 call sites; the companion imports nothing from Dora, so its constant stays with a comment naming the source. blast: S (mechanical) · verdict: **execute in chunk 20** (cross-cutting; R-003).

**16-R12 — `.settings-list` border + `color-mix(… --text-primary 8%)` copied across settings pages.** where: `ApiAccessSettings.vue:545–548` (+2 pages, 25 occurrences of the mix) → already 13-R9's settings-shell consolidation. verdict: **execute under 13-R9**; no separate finding.

**16-R16 — `CSRF_EXEMPT_ENDPOINTS` re-lists two members of `PUBLIC_ENDPOINTS`.** where: `middleware.py:243–247` adds `submit_ingestion_batch`, `ingest_link_status` to a set that is `PUBLIC_ENDPOINTS | {...}` and already contains them (:52, :55). The union is a no-op; the comment is the only value. change: drop the two literals, keep the comment on `PUBLIC_ENDPOINTS` ("bearer routes are CSRF-exempt by being public"). blast: S · guard: `test_route_auth_enforcement` · verdict: **execute** (or waive as documentation — Stage 2's call; recommend execute to stop the two sets drifting).

### C3. Dead code / unused fields / unread endpoints

**16-R13 — `web_app/src/helpers/scrapedProductOfferLogic.ts` has no consumer.** evidence: `grep -rn scrapedProductOfferLogic web_app/src web_app/test` → only the definition. A Phase-D leftover (the in-app `ProductSearch.vue` it served was deleted). change: delete the file. verdict: **execute**.

**16-R14 — Dead `q-expansion-item` header props + `captionFor`.** where: `ApiAccessSettings.vue:40–42` (`:icon`, `:label`, `:caption="captionFor(src)"`) are ignored because the `#header` slot (:45–123) replaces the header; `captionFor` (:370–373) returns `''` unconditionally. change: remove the three props and the function. verdict: **execute**.

**16-R15 — `formatDate` is a one-line wrapper.** where: `ApiAccessSettings.vue:448–451` wraps `formatDateTime` (imported under an alias at :324). change: import `formatDateTime` and use it in the template. verdict: **execute**.

**16-R17 — `trust` is stored and never read; the SPA type carries `trust?` the page never sends.** where: `IngestionSource.trust`, `CreateIngestionSourceCommand.trust?` (`ingestionSourcesApiService.ts:17`), `ALLOWED_TRUSTS` validation (`ingestion_source_admin.py:188`). Proposal §2.6 records the deferral explicitly. verdict: **waive** (documented seam; cost is one column). Drop the optional `trust?` from the TS command type only if 16-R23 touches the file anyway.

**16-R18 — Stale docstrings.** `ingestion_source.py:15–16` "products/offers/**observations**" (observations left the producer path at J1); `test_ingestion_sources.py:9–10` "exercised once the ingest endpoint lands (C-10.2)". change: two one-line edits. verdict: **execute** (ride-along).

**16-R19 — `_IngestionContext.store_cache` is documented as "external store name → mapping row (resolved Store or None)" but caches the mapping only; the Store is re-fetched per product (`:310`).** Cosmetic; folds into 16-R6 (cache `(mapping, store)`). verdict: **execute with 16-R6**.

### C4. Componentisation opportunities (R-001)

**16-R20 — `ApiAccessSettings.vue` (572 lines) is one page = list + per-row header + mappings panel + three dialogs.** change: extract `components/settings/IngestionSourceRow.vue` (header slot content + overflow menu; emits `toggle`/`rename`/`revoke`) and `components/settings/StoreMappingsPanel.vue` (the card; props `mappings`, `storeOptions`; emits `assign`/`drop`); the page keeps state, API calls and the three dialogs. blast: M · guard: none (vue-tsc + manual G1–G16) · verdict: **execute**.

**16-R21 — Reveal-once dialog as a `SecretRevealDialog` component.** One site only. verdict: **waive** (YAGNI; revisit if a second secret appears — e.g. an assistant provider key).

**16-R22 — `$q.dialog` ×2 (`:405–412`, `:516–523`) → `useConfirm`.** tracked: 13-R26 (chunk 20 builds the composable). verdict: **execute in chunk 20**.

### C5. Placement / layering (R-003, R-005)

**16-R23 — `IngestionSourcesApiService.listStoresAsync` + `DoraStore` duplicate `StoresApiService.listAsync` + `Store`.** where: `ingestionSourcesApiService.ts:48–51, 104–109` call `/stores` (a different resource) and re-declare the row type; `storesApiService.ts:11` already returns `Page<Store>` with `store_id`/`name`. change: page imports `StoresApiService`, maps `page.items`; delete `DoraStore` + `listStoresAsync`. Note the default page size is 50 (`query_options.py:22`, FU-668) — pass `limit` explicitly or use the store list the Stores page already caches (chunk 13). blast: S · verdict: **execute**.

**16-R24 — Five raw `db.metadata.tables[...]` readers in this chunk.** where: `get_ingestable_products.py:81,89`, `get_ingest_stores.py:49`, `get_link_status.py:217` (gone with 16-R7), `ingestion_auth.py:43`. `find_ingestion_source` mirrors `auth_helpers.find_token` (also raw, `auth_helpers.py:193–207`) so the two should move together. tracked: **FU-923** (repository-routed access sweep, R-005). verdict: **FU** (already tracked; add these four sites to its list).

**16-R25 — `offer_mapping.py` lives under `features/ingestion/` but is the products domain's rule and is imported by `products/create_product.py:12`.** change: move to `features/products/offer_mapping.py`; two import sites. Also type `repository: SqlAlchemyRepository` → the `Repository` port (it only uses `.get()` and `.add()`), and `_IngestionContext.repository` likewise (`submit_ingestion_batch.py:194`). blast: S · verdict: **execute** (also lets 10-R5's PATCH-price fix import from the right package).

**16-R26 — Function-level import to dodge a cycle that doesn't exist.** where: `ingestion_auth.py:84` imports `api_response.unauthorized` inside `authenticate_ingestion_request`; `api_response.py` imports only stdlib + flask (grep). change: hoist to module level. verdict: **execute**.

### C6. Naming & idiom

**16-R27 — `logging.getLogger(__name__)` inline ×3 instead of the module `_Logger` every other file in the chunk uses.** where: `ingestion_source_admin.py:191, 222`, `store_mappings.py:188`; also the local `ok = …` in `ingestion_source_admin.py:216` / `store_mappings.py:202` reads as `api_response.ok`. change: module `_Logger`; rename `ok` → `deleted`. verdict: **execute**.

**16-R28 — `UpsertStoreMappingHandler.handle` returns `(dto | None, "source_not_found" | "store_not_found" | None)`.** where: `store_mappings.py:104–139, 183–187` — string-coded tuples are the same shape 13-R1's bug came from. change: a small frozen `UpsertStoreMappingResult(mapping, source_not_found, store_not_found)` like `DeleteProductHandler`'s `product_not_found`, or raise two domain exceptions caught in the route. verdict: **execute** (S).

**16-R29 — `_apply_product` writes `note=f"created (provenance: {record_source})"` — provenance smuggled into a free-text note while `record_source` is otherwise unused on the product path.** where: `submit_ingestion_batch.py:371, 422–425`. The docstring (:374–376) says provenance is recorded by the next offer push. change: `note="created"`; drop the dead `record_source` on the product path. verdict: **execute** (companion `summarise_push` keys on `kind`, not `note` — safe).

### C7. Efficiency

**16-R30 — `ListStoreMappingsHandler` does one `by_id` per distinct store.** where: `store_mappings.py:86–91`. change: one `.all(EntityField(Store,"id").in_(store_ids))`. verdict: **execute** (S; mapping lists are tiny, but it's the idiom the rest of the file uses).

**16-R31 — `_apply_product` issues up to two product lookups + a Store fetch per record; a 200-record batch ≈ 500 queries.** Bounded, synchronous v1 by design (§2.7). verdict: **waive**.

**16-R32 — `get_ingestable_products` loads every store name per call for the fallback.** Dozens of rows at most. verdict: **waive**.

**16-R33 — `find_ingestion_source` scans every enabled source with `compare_digest`.** n ≈ 1–3; mirrors `auth_helpers`. verdict: **waive** (keep the timing-safe idiom).

### C8. Design-level findings — out of Stage-2 scope

- **16-D1 (= FU-919) — Keep or cut the name-based store mapping?** The companion pushes by `store_id`; the quarantine path + the *Store mappings* panel serve only a producer that pushes by name (the guide's `curl` reader). Recommendation: **keep** — it is the contract a third-party producer gets without reading Dora's store ids first, it is 200 lines, and the panel is hidden until a mapping exists. If cut, 16-R6 shrinks to one site and the panel + `IngestionStoreMapping` go. Owner's call; Stage 2 proceeds either way.
- **16-D2 — Availability on the wire (16-R5).** Adding `is_available` is a small contract addition in both repos; the alternative (a product with no price shows "No price yet" instead of $0.00) is a chunk-10 display rule. Recommend both.
- **16-D3 — No key rotation.** Deliberate: revoke + mint (guide + reveal dialog say so). No change.
- **16-D4 — Idempotency semantics are "refuse to re-process", not "return the cached result".** Documented in the module docstring (:10–13); the companion handles `idempotent_replay` explicitly. No change.

### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `ingestion_auth.extract_bearer_token` + `find_ingestion_source` | 30-line bearer parse + SHA-256 match | `flask-httpauth` `HTTPTokenAuth` | **keep** | — | One scheme, one table; the library adds a decorator we'd still wrap in `authenticate_ingestion_request`. |
| `IdempotencyKey` table + TTL | 40 lines | none worth it | **keep** | — | Fix 16-R2/R3 instead. |
| Payload validation | pydantic `extra="forbid"` | — | already library | — | — |
| `copyToClipboard` | Quasar util | — | already library | — | — |
| Rate limiting on the bearer lane | none | `flask-limiter` | **keep (none)** | — | 256-bit keys; a limiter would need the same `ProxyFix` fix as 15-R1 first. |

### C10. Standards drift (R-0NN)
- **R-005** — raw table access ×5 (16-R24 → FU-923); `SqlAlchemyRepository` typed where the `Repository` port suffices (16-R25).
- **R-003** — image cap ×9 (16-R11); mapping lookup ×3 (16-R6); link join ×2 (16-R7); body-parse ×2 (16-R9); store-ref validator ×2 (16-R10).
- **R-001** — 572-line page (16-R20).
- **R-035 / D-rules** (`ApiAccessSettings.vue`): `text-color="white"` ×4 (:50, :61, :69, :150) → FU-671 / `--text-on-primary` (FU-674) sweep; `color="grey"` (:59) is a Quasar palette literal → `dora-bg-sunken dora-text-secondary` like the avatar at :49; inline `style="min-width: 180px"` (:101) → a class; icons all via `ICONS` ✓; confirm dialogs via `$q.dialog` → 13-R26.
- **R-021 (timezone)** — all server stamps are `datetime.now(timezone.utc)` ✓; SQLite tz coercion handled at :252–258 ✓.
- **Invisibility rule** — no "companion/scraper/producer" in any DTO, copy or help ✓ (two code comments in `get_ingest_stores.py:3–7` and `get_ingestable_products.py:4` name "the companion" — comments are fine; keep them out of strings).
- **15-R14** — `require_admin` uses `SESSION_USER_ID_KEY` ✓.

### C11. Ride-along signals for FU-010 / FU-224 (theme / colour)
- `ApiAccessSettings.vue:59` `color="grey"` badge + `text-color="white"` ×4 (warning-on-white "pending"/"N pending" badges — check D-002 contrast on Pesto Dark; FU-924 (b) found the same white-on-semantic pattern in the companion).
- `:545–548` `color-mix(in srgb, var(--text-primary) 8%, transparent)` hairlines ×2 (settings-shell shared rule, 13-R9).

---

## D. Test plan — Ingestion API

| # | Test | Layer | Priority | Trigger to write it |
|---|---|---|---|---|
| D1 | `test__ingest__expired_idempotency_key_is_reprocessed_not_500` — insert an `IdempotencyKey` with `expires_at` in the past (direct repo write inside `app.app_context()` as `test_ingest_batch.py:296–303` does), re-push with that key → 200, records accepted, row refreshed, exactly one row for `(source, key)` | pytest | **must-write-before-ship** | with 16-R2 |
| D2 | `test__ingest__stamping_a_key_purges_expired_rows` | pytest | nice-to-have | with 16-R3 |
| D3 | `test__ingest__is_available_round_trips` (false on create, unchanged on a push without it) | pytest | must-write **when** 16-R5 lands | with the FU |
| D4 | `test__ingest_stores__stamps_last_used_at` | pytest | nice-to-have | with 16-R4 |
| D5 | `test__link_status__never_resolves_a_custom_product` — create a custom product via `POST /products` at the seeded store, look it up by `(store, name)` → `product_not_found`; then push the same name via ingest → the ingested id (not the custom one) | pytest | **must-write-before-ship** | with 16-R8 |
| D6 | `test__ingest__validation_errors_are_structured` — replaces the text assertion in `test__ingest__rejects_price_observations_field:353–354` | pytest | must-write (adjust) | with 16-R34/R9 |
| D7 | `test__ingest_store_image__serves_an_uploaded_logo` (200 path; today only the 404 path is pinned, and it `return`s when no bare store exists) | pytest | nice-to-have | opportunistic |
| — | Vitest for `ApiAccessSettings.vue` | — | **no** | thin page over the API; G1–G16 by hand once |

Existing coverage is strong (45 tests pin auth, dedupe, quarantine, `store_id`, paging, PF-8, image round-trip, admin sweep). No Playwright.

---

## E. Proposed follow-ups (orchestrator allocates ids)

- **urgent · bug** — Idempotency-Key replay after TTL → IntegrityError/500 and the batch is lost (16-R2). Fix in `submit_ingestion_batch._already_processed/_stamp_idempotency`; D1 pins it. Resolution: **now** (Stage 2, chunk 16).
- **urgent · bug** — `link-status` resolves custom products → companion "unsave" deletes a hand-entered product (16-R8). Shared `find_ingested_product` with `not_custom`; D5. Resolution: **now**.
- **bug · docs** — `docs/INGESTION_GUIDE.md` + `PROPOSAL_INGESTION_API §2.2` document `merchant`/`valid_until` and none of the read-side endpoints, `store_id` or `image` (16-R1). Resolution: **now**; closes FU-924 (d) on Dora's side.
- **finding · contract (two repos)** — a product pushed without an offer shows as available at $0.00; `is_available` never crosses the wire though both sides hold it (16-R5 / 16-D2). Resolution: **later, next companion pass** — Dora side first (additive, optional field), then `build_payload`.
- **finding** — idempotency rows never purged; revoked sources orphan them (16-R3). Resolution: **now** (one line with 16-R2).
- **finding** — raw `db.metadata.tables` ×4 remaining after 16-R7 (16-R24) — **append to FU-923**, not a new FU.
- **finding** — image-cap literal ×9 (16-R11) — **chunk 20** consolidation list.
- **decision** — FU-919 (16-D1): keep or cut the name-based mapping path. Recommendation recorded: keep. Resolution: owner, **before Stage 2 touches 16-R6** (so the refactor isn't done on code about to be deleted).
- **companion repo (append to FU-924)** — `dora_ingest.fetch_saved_products` docstring still says "only those whose store is mapped for this source" (Dora stopped filtering 2026-10-15; the caller must skip by `store_id`); `IngestResult.has_pending_store_mappings` only knows `store_not_mapped`, not `store_unknown`.

---

## F. Feedback coverage — `# PRODUCT SEARCH` (31 bullets, lines 156–188)

| Bullet | Status | Where |
|---|---|---|
| 1 merchant vs data-provider conflation | ✅ shipped | Phases D/E: Dora holds *Stores* only; providers live companion-side; `GET /api/ingest/stores` makes Dora's stores the companion's source of truth (2026-10-15). |
| 7 plain-English "at the mercy of the data providers" disclaimer | ➡ companion UI | out of this seam; the invisibility rule forbids it in Dora. |
| 9, 10, 11 "Extra inputs are not permitted ×5" on save / quick-add / link | ✅ root cause gone (stale client vs `extra="forbid"`), **error shape still raw** → **16-R34** | `submit_ingestion_batch.py:479`; bullet 11's "does link also save?" → companion flow: save = push, link happens in Dora (chunk 10). |
| 25 search performance, 26 bot-blocking analysis | ➡ companion | scraping never runs in Dora (charter Decision 1). |
| 2–6, 8, 12–24, 27–31 (companion search UI, filters, cards, compare) | ➡ companion repo | FU-924/891/886/887 hold its open debts; chunk 10 already marked these "(companion)". |

Other sections: `# MY PRODUCTS`, `# PRODUCT HISTORY` → chunk 10; `# DATA` → chunk 18; `# SETTINGS` → chunk 13.

### Register summary
- **FST rows:** 16 golden + 14 edges · **Help entries:** 6 (new 5 / reworded 1) + DoraBot 2 lines · **Review findings:** 34 (execute 24 / FU 3 / waive 7) · **Tests:** 7 (must-write 3) · **Bugs:** 6 (16-R1, R2, R3, R4, R5, R8) + 1 feedback-linked (R34)
- **One line:** the seam works and is well-tested, but its own documentation would 400 a reader, a week-old idempotency key 500s the batch, and the read side can hand the companion a custom product's id to delete — all small fixes; the page is a 572-line single file with a dead header and a duplicated store service.
