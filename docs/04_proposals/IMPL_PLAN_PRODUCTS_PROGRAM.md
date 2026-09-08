# Implementation plan — Products program (Dora + companion)

**Status: COMPLETE — all eight batches done (2026-09-06 → 2026-09-07).**
A · B · C · C2 · D · E · F · G. The Aldi rewrite landed once the owner confirmed
Aldi publishes no sales data, which was the one thing blocking it.
**OD-1 closed** (card actions) · **OD-3 answered** — no third-party grocery
source is worth hooking into; don't add aggregators · **OD-4 answered** — the
companion's bearer key stays env-only. **OD-2 (manual product entry) is the last
open question**; see §6.

**Every June feedback bullet for My Products and Price History is now actioned**
— §8's coverage table has no open rows, and **FU-214 is closed**.

The Dora↔companion data path is now complete end to end: save what you picked
(B) · keep receipts when it goes (C2) · unsave/delete (C) · refresh on a
schedule (D). What remains is scraper quality and the Dora-side UI.

Governing doc for the multi-batch program that (a) actions the June My Products /
Price History feedback that was parked as **FU-214**, and (b) settles the
**data-flow contract between Dora and the standalone companion** so the products
layer has a defensible ownership story before more UI is built on it.

**Spans two repos.** Dora (`DiscountDora/`) and the companion
(`../dora-companion/`, sibling checkout). Each batch below is tagged with the
repo it lands in. The companion has **no planning-doc library and no follow-ups
ledger of its own** — companion-side findings are tracked here and in
`DORA_FOLLOWUPS.md` until that changes.

Supersedes the Phase-F tail scope of **FU-214**, which is now a pointer to this
doc. Related: `PROPOSAL_PRODUCTS_AS_OVERLAY.md` (the 2026-06-17 pivot that made
Products a data-gated overlay), `PRODUCTS_OVERLAY_RUNBOOK.md` (Phase F status).

---

## 1. Data-flow contract (durable rules)

These are the standing rules for how product data moves. They outlive the
batches below — a later agent changing the products layer checks against these,
not against the batch list.

**PF-1 — Dora is the source of truth for what is saved.** The companion is a
*discovery and acquisition* tool. What exists in Dora's product layer is decided
in Dora, never by a scraper's opinion of what is interesting.

**PF-2 — Search is in-memory and unsaved.** The user searches in the companion;
results hit the selected stores, are held in memory and displayed. Nothing
reaches Dora as a side effect of searching.

**PF-3 — Saving pushes the offer already in hand.** A save sends the *concrete
scraped offer the user is looking at*. It must never re-scrape, re-query, or
re-derive which product was meant. (Violating this is FU-881 — see §5.)

**PF-4 — Unsaving deletes through the same *behaviour* Dora's own UI uses.** One
delete handler, one cascade policy, no companion-specific back door. Two
authenticated front doors onto it, because the SPA presents a session cookie and
an ingestion source presents a bearer key (PF-9): `DELETE /api/products/<id>` and
`DELETE /api/ingest/products/<id>`. Same split as the read side
(`/api/ingest/link-status`). *Clarified 2026-09-06 when batch C hit it.*

**PF-5 — The companion can read what Dora already holds.** Via
`POST /api/ingest/link-status`, so search results can show "already in Dora" /
"linked to <stock item>" and the user is never guessing.

**PF-6 — Dora never calls the companion.** Dora issues no outbound request to
it, depends on it for no computation, and has no notion of "the scraper" in any
domain logic. The weekly deals email is computed purely from what is currently
in Dora; keeping data fresh enough for the email is the user's business, done by
syncing beforehand. (R-005 source-invisibility applied to the product layer.)

> **Corrected 2026-09-06 (batch A), which is what the "confirm PF-6" step was
> for.** This rule originally read *"Dora holds no companion URL"*, and that was
> simply false: `AppSetting.product_search_url` exists and the SPA's
> `openProductSearch` opens it. Verified what actually matters instead — Dora's
> only outbound HTTP anywhere is TTS voice provisioning and a version check,
> neither of them the companion. So the *substance* holds (no server-to-server
> dependency, nothing in Dora breaks if the companion vanishes) and the stored
> URL is a **browser-navigation convenience, not a coupling**: it is a link the
> user's browser follows, never an address Dora dials. Rule reworded to claim
> only what is true.

**PF-7 — The companion pulls, on a schedule the user configures.** It fetches
Dora's saved-product list, re-scrapes offers for those products, and pushes the
results back. Pull-then-push, never Dora-initiated.

**PF-8 — Inactive means "do not scrape".** `Product.is_active = false` is not
merely a display filter; it excludes the product from the scheduled refresh in
PF-7. This gives the flag a functional cost and is why its on-screen state has
to be legible (MP-8). Carried forward from the original spec — see §7.

**PF-9 — The companion authenticates as an ordinary external client.** An
admin mints a bearer key in Dora (`IngestionSource`); the companion is
configured with it. Dora grants the companion no privilege that any other
ingestion source lacks.

---

## 2. What already exists — do not rebuild

Verified by reading the code on 2026-09-06. A later agent should not
re-implement any of this.

| Capability | Where | State |
|---|---|---|
| Bearer-key auth for ingestion, admin-minted | `features/ingestion_sources/ingestion_source_admin.py` — `POST /api/ingestion-sources` mints, raw key shown once | ✅ Built. **PF-9 is already the design** |
| Batch ingest endpoint | `features/ingestion/submit_ingestion_batch.py` — `{products[], offers[]}`, idempotency key, per-record accept/skip/fail, store-mapping quarantine | ✅ Built, and its shape is fine for PF-3 |
| "Already in Dora?" lookup | `features/ingestion/get_link_status.py` — `POST /api/ingest/link-status` | ✅ Built |
| Companion renders the link state | `ProductSearchCard.vue` — "Linked in Dora: X" / "Already in Dora (not linked)" | ✅ Built. **PF-5 is done** |
| Weekly deals email is self-contained | `features/deals/send_deals_email.py` reads Dora's own products/offers for opted-in users | ✅ **PF-6 already true** |
| Scheduler infrastructure in companion | `merchant_api/startup.py` — `BackgroundScheduler` running a daily provider health check | ✅ Present; PF-7 adds a job, not infrastructure |
| Per-product refresh path on providers | `MerchantDataProvider.get_product(DoraProduct)` | ⚠️ Exists but is **currently unused** — this is the hook PF-7 wants |
| Two-mode list view (cards ⇄ compact rows) | `useListViewMode('cookbook-overview')` + `RecipeCard` / `RecipeRow` in `RecipesOverview.vue` | ✅ Built for the cookbook; batch F reuses this machinery |
| Sticky page counts | `PageCountsFooter` — already on My Products | ✅ Built (closes MP-22) |
| Standard list-page toolbar | `stock-toolbar__actions` scroll band + `__find` row + `compactToolbar`, in `StockOverview.vue` / `RecipesOverview.vue` | ✅ Built — My Products and Price History have **not** adopted it |
| Shared bulk-action bar | `dora-subbar` / `css/subbar.scss`, adopted by stock + shopping list 2026-08-26 | ✅ Built — My Products has **not** adopted it |

---

## 3. Batches

No sequencing constraint from the owner ("not fussed with sequence… this is
prerelease code"). Dependencies below are technical, not priority.

### Batch A — Data-flow contract + companion target surface — ➗ **DONE with a carve-out 2026-09-06**
**Repos:** companion (Dora needed no change, as predicted).

- ✅ §1 is the contract, and **PF-6 was corrected rather than confirmed** — see
  the note under that rule. The check was worth running: the rule claimed
  something false about Dora holding no companion URL.
- ✅ New `GET /api/push/config` reports **what the backend is actually
  configured with**. The Dora Target page previously displayed
  `VITE_DORA_LABEL` — a *frontend build-time* variable with no link to the
  backend's `DORA_INGEST_URL` — while using it to tell the operator where
  pushes land. It could name the wrong Dora with complete confidence. The page
  now shows the backend's real URL, whether a key is set, and which half is
  missing when it isn't ("set the env vars" being useless advice when one of
  the two already is).
- ✅ The key is **never** in the response. Pinned by a test that plants a
  distinctive secret and greps the raw body, plus an exhaustive field-set
  assertion so a future field can't leak it by accident.

**❌ NOT built: a browser-editable key field — deliberately, and it needs an
owner decision.** This batch's original description said to let the user paste
the key into the companion's settings UI. On reaching the code, that turns out
to reverse a documented security posture, and the page said so in as many
words: *"not editable from the browser, by design."*

The reason it is load-bearing: **the companion has no authentication of its
own** (`push_to_dora`'s module docstring: *"Auth — there is none on the
companion side yet"*). Anyone who can reach the companion's web UI can already
scrape and push; making the key editable there would additionally let them
**repoint the target** or, if ever echoed back, **exfiltrate a credential that
now grants DELETE on Dora's product catalogue** (batch C). Dora itself shows a
minted key exactly once, which is the same instinct.

Re-reading the owner's actual words — *"the user must configure an api access
key via admin settings in dora and use that for access in the companion app"* —
that describes the **auth model**, which already existed, not a companion-side
editor. The editor was this plan's own extrapolation. **Owner decision needed
(OD-4)** before building it; the usability half of the ask (knowing what you're
pointed at, and whether it's set) is delivered above without touching the
secret.

**Gates:** companion pytest **51 passed** (4 new); `vue-tsc` clean. Verified
live against a running Dora: `/api/push/config` returns the real URL and no
key; `/api/push/target` with a wrong key returns 502 *"Dora rejected the bearer
key (401)"*.

### Batch B — Push semantics rewrite  ← keystone — ✅ **DONE 2026-09-06**
**Repos:** companion. **Depends on:** A (contract) — built ahead of A; nothing
in B needed A's config surface.

- ✅ `POST /api/push` now accepts **concrete offers** (`{offers: [...]}`) and
  forwards them via the existing `push_offers`. `PushOffer` declares exactly the
  fields `dora_ingest._OfferLike` requires, with `extra="forbid"` so a caller
  sending presentation-only fields (`image`, `price_difference`, `linked_*`)
  fails loudly rather than having them silently dropped.
- ✅ `onSinglePush` sends the offer on screen (FU-881, resolved).
- ✅ `onBatchPush` pushes the ticked selection, or everything displayed when
  nothing is ticked — matching what the button label promises (FU-882, resolved).
- ✅ Dora's `/api/ingest` unchanged, as predicted.
- ✅ **PF-1 and PF-3 are now true**, which is what makes D-1 (hard delete) safe:
  a deleted product can no longer be resurrected by a bulk scrape.

**One thing this batch had to add that wasn't planned.** The Dora Target
settings page's connectivity probe worked by *pushing a search query that
matched nothing* — harmless only because a query that scraped nothing wrote
nothing. Under the new contract there is no harmless push, so the probe became a
read: `companion_common.dora_ingest.check_target` posts an **empty batch to
`/api/ingest/link-status`**, which authenticates the bearer key before doing any
work and accepts an empty `items` list, so it exercises URL + credential and
writes nothing. Exposed as `GET /api/push/target` (503 unconfigured / 502
unreachable-or-rejected / 200 ok — the same codes the SPA already interpreted).

**Gates:** companion pytest **30 passed** (16 new in
`tests/test_push_contract.py`); `npx vue-tsc --noEmit` clean. Verified end to end
over real HTTP against a stub Dora: clicking Save on the 4th of 4 same-named
results pushes that product's own stockcode, and ticking 2 of 4 pushes exactly
those 2. **Not browser-driven** — see the verify note below.

**Carve-outs / owed:**
- The SPA half is typecheck- and contract-verified but **not walked in a
  browser**; driving it needs the companion backend plus live scraping against
  real merchant sites. Logged as a verify item.
- `npm run lint` cannot run in the companion at all (no eslint config) — [[FU-887]].
- A stale SPA bundle sending the old shape gets a 500, not a 4xx — [[FU-886]],
  pre-existing.

### Batch C — Delete / unsave — ✅ **DONE 2026-09-06**
**Repos:** both. **Depends on:** B (done) + C2 (done).

- ✅ Dora: `DELETE /api/products/<id>` — `products/delete_product.py`. Nothing
  blocks it (unlike stock items, a product is reference data no recipe can
  depend on).
- ✅ Cascade per **D-2** needed **no schema change** — `ProductOffer`,
  `ProductHistoricOffer`, `PriceAlert`, `Barcode` and `StockItemProduct` were
  already `CASCADE`, and C2 had already made the shopping-line anchors
  `SET NULL`. Verified rather than assumed.
- ✅ Shopping-line retention reuses C2's `prepare_lines_for_anchor_delete`,
  called with `product_id=` — the reuse the module was written for.
- ✅ Companion unsave wired: `delete_product()` client, companion route
  `DELETE /api/push/product/<id>`, and a save/unsave toggle on
  `ProductSearchCard` driven by the existing link-status decoration, behind a
  destructive confirm.
- ✅ SPA service gained `productApiService.deleteAsync`.

**The auth question this raised, and how it was settled.** PF-4 says unsave
goes "through the same endpoint Dora's own UI uses" — but Dora's product routes
are **session-cookie authenticated**, and the companion authenticates as an
`IngestionSource` with a **bearer key** (PF-9). It cannot present a session.
Resolution: one *behaviour*, two authenticated front doors —
`ingestion/delete_ingested_product.py` is a thin bearer-authed route that calls
the very same `DeleteProductHandler`. That is exactly the shape already used on
the read side (`/api/ingest/link-status` is the bearer door onto product
lookups), so it follows precedent rather than inventing a scheme. **PF-4 should
be read as "one delete behaviour", not "one URL".**

**Deliberately NOT in this batch:** the delete affordance on Dora's own
My Products page. That card is being rebuilt in **batch F** and its action set
is **OD-1**, still undecided — adding a button now would be thrown away. The
capability and its API binding exist; F surfaces it. Today the user-facing way
to remove a product is the companion's Unsave.

**Gates:** **pytest 2333 passed on SQLite** (only the known FU-762 reds);
companion **37 passed**; `vue-tsc` + `eslint src/` clean on both SPAs;
**vitest 705 / 63 files**. 9 new Dora tests
(`tests/e2e/dora_api/test_delete_product.py`) covering both doors, the cascade,
the stock-item surviving, receipt retention, and 401/404 on the bearer door.

**One existing test was inverted, on purpose.**
`test__delete_product__no_delete_endpoint_exists__404` pinned the *absence* of
this endpoint ("the overlay is prunable only by unlinking / deactivating"). That
was the correct pin under the old bulk-push model; D-1 replaces it. Rewritten as
`test__delete_product__hard_deletes` with the reasoning in place, so the change
of decision is legible rather than looking like a deleted test.

**Superseded plan text follows for reference.**

- Dora: `DELETE /api/products/{id}`, used by **both** Dora's UI and the
  companion's unsave (PF-4).
- Cascade policy (owner-agreed, see §4): everything hanging off the product goes
  — offers, historic offers, price alerts, barcodes, stock-item links.
- **Receipt survival** is the subtle half — see batch C2, which this depends on.
- Companion: wire unsave to the endpoint. It already has the Dora `product_id`
  from link-status, so no new lookup is needed.
- Follow the `delete_stock_item.py` precedent for the response shape (structured
  422 + `blocked_by_*` when a delete is refused), if any blocker survives triage.

### Batch C2 — Receipt/done-list survival — ✅ **DONE 2026-09-06**
**Repos:** Dora. **Depends on:** nothing. **Blocks:** C — now unblocked.

Shipped as planned, with one design change forced by reality (below). Migration
`d4f9b2e7a318`. New module `shopping_lists/_line_retention.py` holds both halves
of the rule and is **what batch C reuses for product delete** —
`prepare_lines_for_anchor_delete(repository, product_id=…)` is already written
and takes either anchor.

**The design change worth knowing.** The plan said "snapshot at finish", and
that alone was wrong: a list can reach `done` **without passing through
`POST /finish`** — the dev seed writes finished lists directly, and so does a
restore. Those lines have no snapshot, so nulling their anchor left them with
neither and violated the reworked CHECK, 500-ing the delete. It surfaced as a
real regression in `test__delete_stock_item__DeletingStockItem__StockItemDeleted`
against seeded data. So `prepare_lines_for_anchor_delete` **also backfills any
missing snapshot** at delete time — the last moment the name is reachable.
Finish-time stamping still earns its place (it captures the name as it was at
purchase, per D-5); delete-time is the backstop that makes the invariant hold
regardless of who wrote the row. Both are pinned by tests.

**Gates:** **pytest 2324 passed on SQLite, 2323 on Postgres** (only the known
FU-762 buy-verdict reds, plus [[FU-888]] on PG which is pre-existing and
unrelated). Migration up → down → up clean on SQLite;
`test__migrations__migrated_schema_matches_orm_metadata` — which explicitly
checks **FK ondelete drift** between model and migration chain — green. 7 new
tests in `tests/e2e/dora_api/test_shopping_line_survives_delete.py`.

**Two incidental finds:**
- The CHECK constraint's name had accreted its prefix **four times**
  (`ck_ShoppingListLine_ck_ShoppingListLine_…`) because the naming convention is
  re-applied on every batch rebuild, so its real name differed between a
  migrated DB and a `create_all` one. The migration reflects the name rather
  than assuming it, and normalises it back to a single prefix. **The underlying
  re-prefixing bug is untouched and will recur** on the next batch rebuild of
  any table with a named CHECK.
- [[FU-888]] — `GET /api/nutrition/lookup` 500s on a NUL byte in `q`, Postgres
  only. Found because this batch ran the suite on both backends.

**Superseded plan text follows for reference.**

Independent of the products work and **live today**: deleting a stock item
erases its lines from *every* list including completed ones. See FU-883.

- Add a display-name snapshot to `ShoppingListLine`, written **at finish**
  (`POST /finish`), which is already the snapshotting step — it freezes
  `picked_offer_price` / `list_price_at_pick` for exactly this reason and is
  architecturally enforced as the only path to `done`
  (`manage_shopping_list.py:132` refuses `PATCH status=done`).
- Flip `stock_item_id` and `product_id` from `CASCADE` to `SET NULL`.
- **Rework `ck_shopping_list_line_anchor`** in the same migration. It currently
  demands `stock_item_id IS NOT NULL OR product_id IS NOT NULL`; nulling the
  anchor of a product-only line would violate it. Becomes "anchor OR snapshot".
  ⚠️ This fails loudly on Postgres and **silently on SQLite** — the divergence
  class that has bitten this repo before (see the `sqlite-uuid-text-binding`
  precedent). Test on both backends via `DORA_TEST_DB=postgres`.
- `LineDto.stock_item_name` resolves **join → snapshot → fallback**; it is
  currently non-optional and join-derived
  (`get_shopping_list_detail.py:65`), which is *why* CASCADE was chosen.
- Deletion behaviour by list status (owner call): lines on **draft / shopping**
  lists are deleted; lines on **done** lists are preserved via snapshot. A DB
  constraint cannot be status-conditional, so this lives in the delete handler.
- Reports already tolerate a null anchor (`reports.py:1438`, `:1558` both guard
  `is not None`), so this does not break aggregation.

### Batch D — Scheduled sync — ✅ **DONE 2026-09-06**
**Repos:** both. **Depends on:** B (done). A wasn't needed — the key is still
read from env either way.

- ✅ Dora: `GET /api/ingest/products`
  (`ingestion/get_ingestable_products.py`), bearer-authed, paged. Honours
  **PF-8** — inactive products are excluded, which is what makes "inactive"
  mean *don't scrape me* rather than *don't show me*.
- ✅ The `store` it returns is the **external name this source pushed**, reversed
  through `IngestionStoreMapping` — the inverse of what the write side resolves.
  Read and write must agree on the mapping or a pulled product can't be pushed
  back. Products whose store the source has no mapping for are omitted rather
  than returned with a name the caller can't use.
- ✅ Companion: `fetch_saved_products()` (paged pull),
  `features/sync_saved_products.py` (`run_sync` + `scheduled_sync`),
  `POST /api/sync` for an on-demand run, and an APScheduler job on
  `MAPI_SYNC_INTERVAL_HOURS` (default 24, **0 disables** — the user picks the
  cadence, per PF-7).
- ✅ **This is the first use of `MerchantDataProvider.get_product()`**, which had
  existed unused since the beginning. It looks a product up by its *own
  stockcode* instead of re-searching by name — which matters, because
  re-searching by name is exactly the FU-881 defect in a different costume.

**Gates:** **pytest 2340 on SQLite** (only the known FU-762 reds); companion
**47 passed** (10 new); 7 new Dora tests. Verified end to end over real HTTP
against a stub Dora: the loop pulls with paging, asks each provider for
`sku-1`/`sku-2` **by stockcode**, and pushes the refreshed offers back.

**Robustness the tests pin, because a scheduled job fails differently:** one
product that raises, or that the scraper can't find, must not end the run —
otherwise a single delisted item silently stops the whole refresh until someone
reads the logs. `scheduled_sync` never raises, for the same reason: an
exception out of an APScheduler job kills the job and the next tick never fires.
A product whose store this companion doesn't scrape counts as *unsupported*, not
*failed* — it isn't an error, it just isn't ours.

**Superseded plan text follows for reference.**

- Dora: a read endpoint exposing the saved-product list to an authenticated
  ingestion source (PF-7). Source-agnostic per R-005.
- Companion: an APScheduler job on a user-configured cadence, driving the
  existing-but-unused `get_product(DoraProduct)` provider path, pushing results
  back through batch B's offer-shaped push.
- **Must honour PF-8** — skip `is_active = false` products.

### Batch E — Scraper robustness + Aldi rewrite — ✅ **DONE 2026-09-07**
**Repos:** companion. **Depends on:** OD-3 for new sources; the selector
rewrite depends on having the redesigned markup.

**Done — the parts that need no network:**
- ✅ **All four FU-884 defects fixed**, with 13 tests. Their severity ordering
  changed once measured, which is worth recording:
  - **Cents parsed as dollars** is the severe one and was originally logged
    last as "fragile price parsing". `"80c"` became **80.0, not 0.80** — a 100×
    error that lands in Dora as a real price and poisons the product's history
    and every cheapest-comparison built on it. New `_parse_price` handles the
    cents shape and degrades to `0.0` on junk instead of raising.
  - **`get_product` raised `StopIteration`** despite a `| None` signature.
    Worst inside batch D's scheduled sync, where it would abort an entire
    refresh run over one delisted product.
  - **Caches were class attributes**, shared across instances while the
    category map was per-instance — two providers disagreeing about what they
    held. Now per-instance.
  - **`rstrip` instead of `removesuffix`** for the size suffix. **Downgraded
    from the original claim:** the FU said names "are being mangled today";
    sweeping plausible Aldi listings found *no* case where the two disagree
    (divergence needs the size to repeat or overlap, `"Rice 1kg1kg"`). A latent
    hazard, fixed defensively — not observed corruption.
- ✅ **Selector-drift is now legible.** The health check already detected drift
  implicitly (stale selectors → zero offers → unhealthy) but reported one
  boolean, so "the site is down" and "the site was redesigned" looked identical.
  Providers now record `last_checked_at`, `last_result_count` and `last_error`,
  surfaced on `GET /api/health/data-providers`. **`last_result_count == 0` with
  `last_error == null` is the drift signature.** Also fixed the *same* bare-
  `next()` defect there: with no enabled merchant it raised `StopIteration`,
  which the `except Exception` swallowed and reported as a broken scraper —
  "you switched this shop off" shown as "this scraper is faulty".

**Not done:**
- 🔎 **The Aldi rewrite is now SPEC'D, not built** (owner authorised a fetch,
  2026-09-07). Six requests to the public site established:
  - **The old model is gone entirely, not just restyled.**
    `/groceries/{category}/` **302s to `/products`**, and all six old selectors
    (`box--wrapper`, `box--amount`, `box--decimal`, `box--value`,
    `box--former-price`, `box--baseprice`) appear **zero** times.
  - The site is **Nuxt 3 on Spryker**. Products are **server-rendered as JSON**
    into `<script type="application/json" id="__NUXT_DATA__">` — Nuxt's
    flat-array (devalue) encoding, where integers are indices into one array.
    No API call is made to render them, and `api.aldi.com.au` **403s**
    unauthenticated (not pursued — see below).
  - **30 products per page** (matches the page's own `WEB_PRODUCTS_PER_PAGE`),
    3239 total. Category paths work: `/products/super-savers`,
    `/products/price-reductions`, `/products/lower-prices`.
    `?categoryKey=` does **not** (client-side only).
  - Per product: `sku` · `name` · `brandName` · `sellingSize` ("45 g",
    "1,000 ml") · `urlSlugText` · `price.amount` **as integer cents** ·
    `price.comparisonDisplay` ("$2.20 per 100 g") · `currencyCode`.

  **This is strictly better than what it replaces**, and two of the gains are
  capability, not tidiness:
  - **`merchant_stockcode` finally exists.** The old provider hardcoded
    `merchant_stockcode=None`, which means batch D's refresh-by-stockcode
    **could never work for Aldi** — it had only fuzzy name matching. A real SKU
    fixes that.
  - **`brandName` exists.** The old provider hardcoded `brand=None`.
  - **Integer cents removes the FU-884 price bug by construction** — there is no
    `"80c"` string left to misparse.

  A real-payload fixture is saved at
  `tests/fixtures/aldi_nuxt_payload.json` (5 products, index-preserving) so the
  rewrite can be built and tested without touching the network.

  **One gap blocks a faithful rewrite: the discount shape.** `wasPriceDisplay`
  and `savingsDisplay` exist in the payload's key schema, but **no product on
  any page fetched carried one** — including `super-savers`,
  `lower-prices` and `price-reductions`. That is consistent with Aldi's
  everyday-low-price model rather than markdown pricing, but it means
  `price_was` — which drives Dora's entire discount story, `DiscountChip`, the
  on-deal filters and the bulk on-deal selections — is unverified. **Needed: one
  saved page where an Aldi product is actually showing a was/now price.**

  **Not pursued, deliberately:** `api.aldi.com.au` returned 403 to
  unauthenticated calls. Hunting the frontend for a key to get past that is
  circumventing an access control, so it was dropped as soon as the 403
  appeared. It is also unnecessary — the server-rendered payload is a public,
  stable, and frankly better source.
- 🔎 **New sources researched — the honest answer is "there aren't any to hook
  into" (OD-3).** Australian supermarkets publish **no official price APIs**;
  the ACCC has *recommended* they start, which is a trend to watch, not
  something to build on. The consumer comparison services that exist —
  GroceryWise, Grocery Spy, OzTrolley, WhichGrocer, TrolleyChecker — are
  **front-ends, not data providers**: none offers a public API, and each is
  itself scraping the same retailers. Consuming one would add a hop, inherit
  their staleness, and put us under their terms rather than the retailer's — a
  worse position than scraping the source directly, which is what the existing
  Grocerize / SaveOnGroceries integrations already do.
  **Recommendation: don't add aggregator sources.** Better value is in making
  the four first-party providers solid (this batch's health reporting is the
  start) and revisiting if the ACCC recommendation produces real APIs.
- ❌ **Retry/backoff policy.** The base class carries unused
  `_max_attempt_time_seconds` / `_max_backoff_time_seconds` fields. Left alone
  deliberately: tuning retries is a change whose blast radius is *live requests
  to real retailers*, and it wants the trustworthy health signal above (and
  [[FU-891]]) to measure against first.

**Gates:** companion pytest **69 passed** (18 new); `vue-tsc` clean. Health
endpoint shape confirmed live.

**Superseded plan text follows for reference.**

- **Aldi rewrite.** It is structurally unlike every other provider: Coles hits a
  real JSON search API (`_next/data/{buildId}/en/search.json`); Aldi has *no
  search* and instead scrapes category pages, fuzzy-matching against a curated
  `aldi_products_by_category.json`, cached 7 days. Plus the site has been
  redesigned and the selectors (`box--wrapper`, `box--amount`, `box--decimal`,
  `box--former-price`) are stale. Four code defects independent of the redesign
  are logged as FU-884.
- Shared robustness: retry/backoff policy, selector-drift detection surfaced
  through the existing provider health check, fixture-based parser tests
  (pattern established in `tests/test_provider_parsers.py`).
- **New sources: undecided.** Owner said "more sources possibly". Current set is
  Coles, Woolworths, Aldi, IGA + two aggregators (Grocerize,
  SaveOnGroceries). Start with a research spike on what is viable before
  committing — see §6 OD-3.

### Batch F — My Products rebuild  ← the original ask — ✅ **DONE 2026-09-06**
**Repos:** Dora. **Depends on:** C (done) for the delete affordance, and OD-1,
settled by the owner at the start of the batch as planned.

Built: `ProductCard` (companion-shaped) + `ProductRow` (cookbook-shaped) on the
cookbook's existing `useListViewMode`; `ProductLinkButton` (MP-5) and
`ProductActiveButton` (MP-8); the standard toolbar; bulk-select on `dora-subbar`
with MP-12/14/15/16/17 — the stock-crossed ones reading **server-owned**
`is_low_stock`/`is_out_of_stock`/`is_essential` (R-003). Refresh deleted
(MP-19). One `DiscountChip` across all four surfaces, `ProductChip.vue` deleted
([[FU-885]] resolved).

**Owner's "are my buttons making sense? Better way to do it?" answered:** the
six select-helpers collapse into one *Select…* menu; the actions stay inline.

**Gates:** `vue-tsc` + `eslint` clean · **vitest 717 / 64** (12 new) ·
`quasar build` green · driven live at 1440 and 375 on the isolated :5171 seed.

**Three defects only the browser found** — all of them passed every static gate:
8px of horizontal scroll at 375 (`PageCountsFooter` outdents `-16px` for a
`q-pa-md` parent; this page used `<q-page padding>`, which is 8px at xs — this
page was the only one of four not already saying `q-pa-md`); the card's
placeholder glyph stranded in the corner (`q-avatar` sizes by font-size, so
`size="100%"` can't fill — added a `fill` mode to `ProductThumb` rather than
lose R-045's authenticated fetch); and an **"Oops, something went wrong" toast
on every viewport change**, which turned out to be the browser's benign
"ResizeObserver loop" notice reaching `window.onerror`, where Dora both toasts
**and** `executeRollbacks()`. Filtered; the general shape is [[FU-889]].

**Superseded plan text follows for reference.**

- **Toolbar:** adopt the standard shape (`stock-toolbar__actions` scroll band +
  `__find` row + `compactToolbar` icon-only labels). Currently a single ad-hoc
  row with full-width labels that crushes at 375px.
- **Two view modes** via `useListViewMode('my-products')`, reusing the
  cookbook's existing toggle machinery:
  - `ProductCard.vue` (expanded) — draws on the companion's
    `ProductSearchCard.vue`: 1:1 image, overlaid discount badge, out-of-stock
    overlay, name + size, price + strike-through was-price, sparkline, unit
    label, footer with store logo and actions.
  - `ProductRow.vue` (compact) — draws on `recipes/RecipeRow.vue`.
- **Card interaction (owner call):** drop the "Open stock item" button entirely
  — the link chips already on the card carry that, and the **top half of the
  card is a link that opens the product**.
- **Card action set is NOT yet decided** — owner wants to remove actions first,
  then decide whether to flatten the overflow menu. See §6 OD-1.
- **Bulk select:** move onto `dora-subbar`, move the entry button into the
  toolbar, add deselect-all, "select inactive", and the stock-level-crossed
  variants (low-stock-on-deal, out-of-stock-on-deal, essential-low-on-deal).
  These last are the one genuine unbuilt **GAP** from the June feedback.
- **Link affordance:** grey broken-link / green connected-link button replacing
  the current bare `Link…` text hyperlink, which also fails the 44px floor
  (D-004).
- **Inactive styling:** legible state, now that PF-8 gives it a real cost.
- **Remove the Refresh button** (feedback C16).
- `DiscountChip` component replacing the four `discountPct` implementations;
  delete the dead `ProductChip.vue` (zero importers — owner approved removal).
- Destructive-confirm colours per D-008; single-unlink currently has **no
  confirm at all**.

### Batch G — Price History + stock-item Products tab — ✅ **DONE 2026-09-06**
**Repos:** Dora. **Depends on:** F for `DiscountChip` (done).

- ✅ Price History's ad-hoc `text-h5` + segmented + ghost row → the shared
  `PageToolbar`, which already solves the title-vs-actions crush (FU-578 #40);
  the alerts button drops its label on phones like the list pages.
- ✅ **PH-3/PH-4** — new `components/MoneyInput.vue`: currency symbol as a
  `prefix` (not baked into label text, which is what made the label truncate in
  a `col-md-4` card), value settles to 2dp on blur, symbol from the money policy
  (D-006). The *Set alert* button moved **below** the field so the input gets
  the card's full width. Adoption elsewhere is deliberately deferred —
  [[FU-890]].
- ✅ **MP-6 / L196** — the stock-item Products tab finally uses
  `AddToListButton`. It had a hand-rolled button that silently added to the
  primary list, making it the only product surface without the cart-state UX
  (picker on 2+ lists, smart-remove on one, on-a-list state on the control).
  Confirmed live: the cart renders amber, i.e. already-on-a-list.
- ✅ `DiscountChip` on both surfaces (landed with F).

**FU-214 closed — all four of its browser-confirm bullets are genuinely fixed**
(PH-2 selection, PH-7 dark tooltip, PH-8 alerts page, PH-9 chart fit). The
Phase-F tail that had been open since June is now empty.

**The PH-7 result is worth carrying forward as method, not just outcome.** Two
successive test runs *said the bug reproduced* — the tooltip's product name
rendering dark-on-dark. Both were false positives caused by setting
`data-theme` directly: `themeService.applyThemeKey` also calls `Dark.set()`, so
the body stayed light and text inherited light-theme ink. Only switching the
theme through the real settings UI gave a true answer (dark bg, white text).
**A half-applied theme manufactures exactly the defect you are hunting** — when
verifying a theming bug, drive the app's own theme switch.

**Gates:** `vue-tsc` + `eslint` clean · vitest **717 / 64** · `quasar build`
green · driven at 1440, 375 and in `pesto-dark` on the isolated :5171 seed.
Backend untouched.

**PH-10 (price history as a bottom sheet from My Products) not taken** — it was
scoped "opportunistic, evaluate with real data, don't build blind". With the
page driven: the full page carries a picker rail, a multi-series chart and
per-product alert cards, and My Products' card already reaches it in one tap.
A bottom sheet would either duplicate that surface or ship a lesser one. Left
unbuilt deliberately; revisit only if the owner finds the navigation jarring in
use.

**Superseded plan text follows for reference.**

- Price History: adopt the standard toolbar shape (currently a bare
  `text-h5` + segmented + ghost row); money-formatted notify-under input
  (currently a raw `type="number"`); chip sizing.
- Stock-item Products tab: adopt `AddToListButton` (currently a raw
  `BaseButton` at `StockItemDetailPage.vue:902`) — this is the componentised
  cart button applied to the one surface that missed it — and `DiscountChip`.
- Browser-confirm the four bullets that appear already fixed (§5, FU-214).

---

## 4. Decisions taken (owner, 2026-09-06)

| # | Decision | Rationale |
|---|---|---|
| D-1 | **Hard delete for products**, not inactive-only | Closes the L197 fork open since June. Viable *because* batch B makes the companion push only what the user saved — a deleted product is no longer re-pushed by a bulk scrape |
| D-2 | Delete cascades to everything hanging off the product | Offers, historic offers, alerts, barcodes, links |
| D-3 | **Stock-item price observations cascade too** | Owner: "same as product offers, cascade is correct" |
| D-4 | Done/receipt lists survive stock-item and product deletion; **draft and shop-mode lists do not** | Owner does not care about drafts; a dead line on a list you are about to shop is worse than no line |
| D-5 | Snapshot is written **at finish**, not at add and not at delete | Finish is already the snapshotting step and is the enforced sole path to `done`. Stamp-on-add denormalises ~90% of lines that never outlive their referent; stamp-on-delete must be remembered in N deletion paths and silently loses the name if one is missed |
| D-6 | IDs stay on live lines; free text does **not** replace them | The IDs are load-bearing across ~20 features — `get_membership` (every cart button's state), `_observation_sync` (receipt → price-history harvest), `frequently_added` / `auto_generate` group-bys, `trim_to_budget`, buy verdicts, reports. After deletion `SET NULL` removes the ID, so ID and text never redundantly coexist |
| D-7 | Companion treated as an ordinary external client with an admin-minted key | Already the design; only the companion-side config surface is missing |
| D-8 | Delete "Open stock item" from the product card; top half of the card links to the product | Owner call. Link chips already cover the stock-item route |
| D-9 | Delete the dead `ProductChip.vue` | Owner approved; zero importers |
| D-10 | Two view modes for My Products — compact row + expanded card | Owner: current card is "half way between" the companion's card and a compact row. Expanded draws on the companion, compact on the cookbook |
| D-11 | No batch reordering for urgency | Owner: prerelease code, no live data to protect |

---

## 5. Findings logged this session

All are new `DORA_FOLLOWUPS.md` entries raised 2026-09-06.

| FU | Repo | What |
|---|---|---|
| ~~FU-881~~ | companion | ✅ **Resolved 2026-09-06 (batch B).** `onSinglePush` re-scraped by name instead of pushing the offer on screen — could save a different product than the one clicked |
| ~~FU-882~~ | companion | ✅ **Resolved 2026-09-06 (batch B).** `onBatchPush` used the selection only to derive the merchant list, then re-scraped up to `result_limit` — ticking 2 items could push 50 |
| FU-886 | companion | No global `ValidationError` handler, so a malformed body 500s instead of returning a 4xx. Pre-existing; matters more now the contract changed, since a stale SPA bundle gets an opaque 500 |
| FU-887 | companion | `npm run lint` cannot run (no eslint config anywhere), and the cross-repo roundtrip test fails in setup three different ways. Also flags a possible **Dora** bug: `startup()`'s destructive reset can't `drop_all` against Postgres (`fk_ProductBarcode_product_id_Product`) |
| ~~FU-883~~ | Dora | ✅ **Resolved 2026-09-06 (batch C2).** `ShoppingListLine.stock_item_id` / `product_id` were `CASCADE` — deleting a stock item erased its lines from completed lists |
| FU-884 | companion | Four Aldi provider defects independent of the site redesign: `rstrip(offer.amount)` treats a suffix as a character set and mangles names; two bare `next()` calls raise `StopIteration` despite a `| None` signature; cache dicts are shared mutable **class** attributes; `.lstrip('$').rstrip('c')` price parsing |
| FU-885 | Dora | `discountPct` implemented four times and rendered three ways (negative badge / `positive` `size="sm"` chip / dashboard), plus a dead `ProductChip.vue` |

**FU-214 is retained, narrowed to browser-verification.** Its build scope moves
into batches F and G. Four bullets look already fixed in a static read and per
the mandatory reported-defect rule stay open until confirmed in a running app:
PH-2 (selection does nothing — appears fixed by FU-605's ref reassignment),
PH-7 (dark-mode hover bubble — the tooltip now uses `--surface-component` /
`--text-secondary`), PH-9 (graph box-fit — a `ResizeObserver` now measures the
card), PH-8 (central alerts page exists).

---

## 6. Open decisions

- ~~**OD-1 — My Products card action set.**~~ **CLOSED 2026-09-06 (owner).**
  Three decisions:
  1. **The card's top half opens the store's own product page** (`web_url`,
     new tab). The separate "Open at store" icon is therefore **deleted as
     redundant** — the removal comes for free rather than costing an
     affordance.
  2. **Removed outright:** *Open stock item* (D-8 — the link chip already goes
     there) and *Register barcode* (barcodes are registered from the stock-item
     page; the products surface leaves the barcode story).
  3. **Fully flattened — no overflow menu.** Five actions on the card face:
     link/unlink (grey/green, MP-5) · active toggle (grey/blue, MP-8 — and it
     doubles as the state indicator, which matters now PF-8 makes inactive
     control scraping) · add to list · price history · delete.

  **Why the size objection was dropped:** it was raised against *six* targets.
  The removals above leave five, and 5 × 44px + gaps ≈ 236px fits inside a
  ~311px card at 375px. The objection was arithmetic, and the arithmetic
  changed.

  **The residual risk is real and mitigated, not dismissed:** delete now sits
  on the same row as add-to-list, the most-used control on the page. Build
  requirements, not preferences — (a) delete is pushed to the far right behind
  a `q-space` so it is not adjacent to add-to-list, (b) it renders
  `danger-ghost`, not as a peer of the neutral icons, (c) it always confirms
  through a **red** destructive dialog (D-008), and (d) on the **compact row**
  the face drops to add-to-list + link only, with the rest reachable from the
  expanded view — a row is too dense to carry a destructive control safely.
- **OD-2 — Custom/manual product entry.** `PROPOSAL_PRODUCTS_AS_OVERLAY.md`
  refused it by design (products arrive via ingestion; `PreferredBuy` is the
  everyday substitute). PF-1 makes Dora the source of truth for what is *saved*,
  which does not by itself reopen manual *creation*, but the original spec has
  a "manually add product offers to saved scraped products" note (§7).
  **Resolution point:** revisit only if the owner raises it — not scheduled.
- **OD-3 — New scraper sources.** Undecided which, if any. **Resolution point:**
  a research spike opening batch E, before any provider is written.
- **OD-4 — Should the companion's Dora bearer key be editable from its web UI?**
  Raised by batch A. The companion has **no auth of its own**, so a key field in
  its browser UI is reachable by anyone who can reach the host — and that key
  now grants DELETE on Dora's product catalogue. Env-only is the current,
  documented posture. Options: (a) leave env-only and treat the improved status
  page as the answer; (b) make it editable and accept the exposure on a private
  host; (c) make it editable **after** giving the companion its own login,
  which is a larger piece of work. **Recommendation: (a) for now, (c) if the
  companion is ever exposed beyond a trusted LAN.** **Resolution point:** owner,
  whenever convenient — nothing is blocked on it.

**Open decisions — spawned/deferred:** OD-1 is **closed** (batch F); OD-3 gates
batch E; OD-4 is raised by batch A and blocks nothing; OD-2 is parked with an
explicit trigger. No undecided fork is left implicit in this plan.

---

## 7. From the original spec

Skimmed `00_original_spec/Feature Boards/Products.md` + the products Feature
Notes (author's first spec, pre-~100k-LOC — historical, non-authoritative).

- **KEEP — "I can mark a stock item saved product inactive to omit them from
  being scraped."** Inactive originally meant *excluded from scraping*, not just
  hidden. Adopted as **PF-8**. It gives `is_active` a functional cost and
  strengthens the case for legible inactive styling in batch F. The note also
  floats "mark all linked products as inactive" from the stock item — worth
  considering in batch F, not committed.
- **SUPERSEDED — "I can resave an unsaved product if I accidentally unsaved
  it"**, whose note reads *"This would require hiding unsaved products on
  refresh"*. The original design needed a **tombstone**, because a bulk refresh
  would resurrect anything the user had unsaved. Under PF-1/PF-3 the companion
  only pushes what the user explicitly saves, and PF-7's scheduled sync refreshes
  *Dora's own saved list* — which a deleted product has left. So resurrection is
  designed out and no tombstone is needed; re-saving is simply saving again, and
  link-status will correctly report the product as absent. **Recorded because the
  reasoning is load-bearing: if PF-3 is ever weakened back toward bulk pushes,
  the tombstone requirement returns.**
- **CONSIDER — "I can manually add product offers to saved scraped products."**
  Adjacent to OD-2. Not scheduled.

---

## 8. Feedback coverage

Maps every bullet in the **MY PRODUCTS** and **PRODUCT HISTORY** sections of
`02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md` to a batch, or marks it
out of scope with a reason.

> **Note on L-numbers:** `PROPOSAL_PRODUCTS_AS_OVERLAY.md` numbers these bullets
> inconsistently — its §357-359 table and its §426-432 table are offset by one
> against each other (L191 is "standalone-usable" in the first and "custom
> products" in the second). This table is keyed to **bullet text and order**
> (MP-n / PH-n) to avoid propagating that ambiguity.

| # | Bullet | Disposition |
|---|---|---|
| MP-1 | Standalone-usable; product-only line, nesting, removal modal | **Built** — `AddToListButton` `inline-product` variant. Browser-confirm (FU-214) |
| MP-2 | No way to add custom products | **Out of scope by design** — manual entry refused (`PROPOSAL_PRODUCTS_AS_OVERLAY` §1); see OD-2 |
| MP-3 | "Cannot mark products inactive: Extra inputs are not permitted" | **Built** — update command sends only `{is_active}`. Browser-confirm (FU-214) |
| MP-4 | Buttons could move to the card, remove ellipses | **Batch F**, gated on OD-1 |
| MP-5 | Link button placement; grey broken / green connected; click to link/unlink | **Batch F** |
| MP-6 | Componentise the cart button | **Built** on My Products; **Batch G** applies it to the stock-item Products tab, which missed it |
| MP-7 | No way to remove a saved product | ✅ **Built (batch C)** — hard delete (D-1). Reachable from the companion's Unsave today; the My Products affordance lands with batch F's card rebuild |
| MP-8 | Inactive styling unclear | **Batch F**, reinforced by PF-8 |
| MP-9 | Filter clear button inconsistent with other screens | **Superseded** — `FilterToggleButton` + `useFilterPanelExpanded` standardised this app-wide. No work |
| MP-10 | % off chip small; other card info too tiny | **Batch F** |
| MP-11 | Unlink modal cancel button yellow; componentise, usually red | **Batch F** — reshaped: bulk-unlink now confirms with `color: primary` on a destructive action (D-008 wants red) and single-unlink has **no confirm at all** |
| MP-12 | No way to deselect all in bulk mode | **Batch F** |
| MP-13 | Bulk select area styling inconsistent | **Batch F** — adopt `dora-subbar` |
| MP-14 | Bulk "select inactive" | **Batch F** |
| MP-15 | Bulk "select low stock on deal" | **Batch F** (GAP) |
| MP-16 | Bulk "select out of stock on deal" | **Batch F** (GAP) |
| MP-17 | Bulk "essential low stock on deal" | **Batch F** (GAP) |
| MP-18 | "Stock items without products" should grab attention when > 0 | **Batch F** — `BaseButton` gained an `attention` prop since June |
| MP-19 | Refresh button — why? | **Batch F** — remove (C16) |
| MP-20 | Bulk select button belongs in the toolbar | **Batch F** |
| MP-21 | "Open stock item" button on card unnecessary | **Batch F** — D-8 removes it |
| MP-22 | Page info hidden/tiny → sticky footer | **Done** — `PageCountsFooter`. No work |
| MP-23 | Filter button default-open on desktop, hidden on mobile? | **Superseded** — answered differently by the owner's 2026-08-20 call (panel opens iff something is filtered). The June idea is now the rejected option |
| PH-1 | Major feature, hidden away | **Decided** — contextual entry is the model (FU-431, resolved). No nav tab |
| PH-2 | Can select products but no change occurs | **Appears fixed** (FU-605). Browser-confirm (FU-214) |
| PH-3 | Product card squished; notify placeholder cut off | **Batch G** |
| PH-4 | Notify-under number formatting should be a price | **Batch G** |
| PH-5 | %off and other text tiny | **Batch G** |
| PH-6 | %off chip colouring feels different elsewhere | **Batch F** (`DiscountChip`) + **G** (adoption). Confirmed real: `positive` here vs `negative` elsewhere — FU-885 |
| PH-7 | Hover bubble not theme-aware (white on white in dark mode) | **Appears fixed** — tooltip uses theme tokens. Browser-confirm (FU-214) |
| PH-8 | Central alert-management area with per-type styling | **Built** — `AlertsPage.vue`. Browser-confirm (FU-214) |
| PH-9 | Graph does not extend to the box edge | **Appears fixed** — `ResizeObserver` measures the card. Browser-confirm (FU-214) |
| PH-10 | Bottom-sheet price history from My Products | **Batch F, opportunistic** — `PriceHistoryBottomSheet.vue` exists but is wired only to the stock-item widget; My Products navigates away. Evaluate with real data, don't build blind |

Cross-cutting bullets that also touch these surfaces and are owned elsewhere:
**C-2** (filter bug), **C-3** (toolbar standardisation — the *reason* batches F
and G include toolbar work despite June saying little about it), **C-4** (sticky
footer), **C-7** (cart button), **C-16** (refresh buttons → MP-19).
