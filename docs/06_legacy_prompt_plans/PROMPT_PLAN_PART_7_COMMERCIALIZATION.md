# Dashy Dora (formerly Discount Dora) — Prompt Plan Part 7: Commercialization (branching)

> **Doc library:** see [00_DOCS_INDEX.md](00_DOCS_INDEX.md). The product is **Dashy Dora**; code identifiers still read "DiscountDora" until **P8-01** renames them, so prompts here intentionally reference the current code name. Governance (verify-state-first + the Dora Decision Charter) lives in DASHY_DORA_CHAMPION_PLAN.md Parts II–III.

Paste-ready prompts to take DiscountDora to market. **This plan branches** — you do
NOT run all of it. Read **COMMERCIALIZATION_REPORT.md** first, make the Section 8
decisions, then follow the branch map below.

Each prompt is self-contained and starts with READ FIRST so it survives code drift.
Do not run two prompts in parallel if they touch the same tables, routes, or stores.

---

## How to choose your branch

```
                         ┌─────────────────────────────────────────┐
                         │  SHARED — everyone runs these first       │
                         │  P7-01 De-risk scraping → personal prices │  ← legal gate
                         │  P7-02 RapidFuzz swap (drop GPL)          │
                         └─────────────────────────────────────────┘
                                          │
                 ┌────────────────────────┴───────────────────────┐
                 │  Want to HOST it (managed or SaaS)?              │
                 │  If selling SELF-HOSTED software only → stop     │
                 │  after SHARED + (optional) P7-02; you're done.   │
                 └────────────────────────┬───────────────────────┘
                                          │ yes, hosting
                         ┌─────────────────────────────────────────┐
                         │  PRODUCTIONIZE — both hosting paths       │
                         │  P7-03 Postgres · P7-04 WSGI + worker     │
                         │  P7-05 Redis + object storage             │
                         └─────────────────────────────────────────┘
                                          │
                      ┌───────────────────┴────────────────────┐
            PATH B (start here)                        PATH A (graduate later)
        Managed single-tenant instances              True multi-tenant
            P7-B1 Provisioning control plane          P7-A1 Households-as-tenant + admin split
                                                      P7-A2 Repository-enforced isolation + tests
                      └───────────────────┬────────────────────┘
                                          │
                         ┌─────────────────────────────────────────┐
                         │  SHARED SaaS LAYER — both paths           │
                         │  P7-06 Stripe billing                     │
                         │  P7-07 Plan gating + usage limits         │
                         │  P7-08 Compliance (privacy/data rights)   │
                         │  P7-09 Ops (observability/CI-CD/backups)  │
                         │  P7-10 Launch readiness                   │
                         └─────────────────────────────────────────┘
```

**Recommended:** SHARED → PRODUCTIONIZE → **Path B** → SHARED SaaS LAYER. Migrate to
Path A (`P7-A1`/`P7-A2`) once paying customers + real load justify the isolation work.

## Cross-cutting rules

- **De-risk (P7-01) is a hard gate before any hosting.** Hosting = you scrape centrally
  = the dominant legal risk. Land P7-01 first.
- **Do not rewrite the framework.** Productionize Flask. No FastAPI/C# migration.
- **Preview → approve → commit; undoable; explainable.** Same as Part 6.
- **Never log secrets/PII.** Billing + auth touch sensitive data.
- Read CHANGELOG.md after each prompt; adjust the next if code drifted.

---

# SHARED TIER (run first, both paths)

## P7-01 — De-risk: scraping → personal price intelligence

> The legal gate. Relocates "deals" onto the user's own purchase history, transforms
> merchant products into a user-defined catalog, and demotes scraping to an
> off-by-default, self-hosted-only module. Depends on P6-01 (paid_price history).

```
Remove DiscountDora's dependence on centrally scraping retailers, WITHOUT losing the
price-intelligence magic. Relocate "deals" onto the user's own purchase-price history,
turn merchant products into a lightweight user-defined catalog, and demote live
scraping to a self-hosted-only module that is OFF by default. See
COMMERCIALIZATION_REPORT.md sections 1–2 for rationale.

READ FIRST:
- merchant_api/* — the scrapers (infrastructure/merchant_data_providers/*),
  get_product_offers.py, the in-process APScheduler that drives refresh.
- dora_api/features/{merchants,products,price_history}/* and web_app
  ProductSearch.vue, PriceHistoryPage.vue.
- dora_api/features/assistant/tools.py — compare_prices (cross-store; to be retired),
  purchase_price_stats (personal; to be kept/expanded), find_deals.
- P6-01 (paid_price / purchase_events) and P6-03 (deal-quality scoring) — this prompt
  re-points both onto personal history.
- dora_api/domain/entities/{product.py,product_offer.py,product_historic_offer.py}
  and stock_item.preferred_product_id + the StockItemProduct m2m.
- dora_api/features/app_settings/* for the settings/feature-flag pattern.
- CHANGELOG.md.

A) DEMOTE SCRAPING (do not delete the code):
- Gate all live scraping behind a setting `scraping_enabled` (default FALSE) AND a
  build/deploy flag so a HOSTED deployment can hard-disable it regardless of setting.
- When disabled: the APScheduler scrape jobs do not register/run; no outbound requests
  to retailers; merchant_api exposes no live-offer endpoints. Document that scraping is
  a self-hosted, personal-use-only option.

B) MERCHANT PRODUCT → USER-DEFINED CATALOG:
- Products become lightweight, user/household-owned: name, optional store label,
  optional brand — NO scraped images/descriptions. Drop reliance on scraped offer
  fields for the hosted path.
- preferred_product_id becomes "your usual brand/store", user-entered.
- Stop ingesting/storing retailer product images in the hosted path.

C) RELOCATE PRICE INTELLIGENCE ONTO PERSONAL HISTORY:
- Re-point P6-03 scoring to run over paid_price history (P6-01) instead of scraped
  historic_offers: lowest_in_window, percentile, and "you're paying more than usual"
  (the personal analogue of fake-markdown). good_deal alerts fire on "your cheapest
  logged price" rather than a scraped special.
- Re-point P6-09 costing to use paid_price (then preferred-store price) — never scraped
  offers in the hosted path.
- Retire compare_prices (cross-store) from the hosted assistant toolset; keep
  purchase_price_stats and expand it as the primary price tool.

D) UI / COPY:
- Replace the cross-store deals/product-search surfaces with a "your prices" view:
  per-item price history, your cheapest/typical price, and good-price flagging.
- Reposition copy from "compare store prices" to "know your prices, never overpay"
  (see report §2 Naming). Keep it factual; remove retailer logos/branding from hosted UI.

DONE WHEN:
- With scraping disabled (default), the app makes zero outbound retailer requests and
  has no cross-store deal UI, yet price intelligence still works over personal history.
- P6-03 and P6-09 produce scores/costs from paid_price with no scraped-offer dependency.
- Scraping still runs when explicitly enabled in a self-hosted build (manual verify).
- No retailer images are stored/served in the hosted path.
- pytest covers personal-history scoring + costing and the disabled-scraping no-egress
  guarantee. Lint + typecheck green. CHANGELOG.md updated.
```

## P7-02 — Swap fuzzywuzzy → RapidFuzz (drop the GPL dependency)

```
Replace the GPLv2 fuzzywuzzy dependency in DiscountDora with MIT-licensed RapidFuzz to
remove a copyleft obligation before commercial distribution.

READ FIRST:
- requirements.txt (fuzzywuzzy==0.18.0; possibly python-Levenshtein transitively).
- Every import/use of fuzzywuzzy (grep "fuzzywuzzy", "fuzz.", "process.extract").
- CHANGELOG.md.

DO:
- Add rapidfuzz, remove fuzzywuzzy (and python-Levenshtein if only pulled by it).
- Port call sites: rapidfuzz exposes fuzz.ratio/partial_ratio/token_sort_ratio and
  process.extract with compatible-enough signatures; adjust score scaling/args as
  needed. Verify match results are equivalent on existing fixtures.

DONE WHEN:
- No fuzzywuzzy/python-Levenshtein in the dependency tree.
- Fuzzy-match behaviour is equivalent (tests over the same inputs pass).
- Lint + typecheck + pytest green. CHANGELOG.md updated.
```

> **If you are selling self-hosted software only**, you can stop here. The rest of
> Part 7 is for HOSTING (managed or SaaS).

---

# PRODUCTIONIZE TIER (both hosting paths)

## P7-03 — SQLite → PostgreSQL

```
Move DiscountDora from SQLite to PostgreSQL so concurrent writes stop serializing on
SQLite's single-writer lock. SQLAlchemy is already DB-agnostic; this is mostly config,
migration cleanup, and testing.

READ FIRST:
- dora_api/app.py (SQLALCHEMY_DATABASE_URI, the _enable_sqlite_foreign_keys pragma).
- dora_api/infrastructure/configuration_manager.py (get_db_connection_string,
  the sqlite:/// path builder, data-dir resolution).
- dora_api/startup.py (migrate_legacy_db, which strips sqlite:/// — must handle pg).
- dora_api/persistence/migrations/versions/* (notes about SQLite-vs-Postgres
  constraint naming and the FK quirks) and sqlalchemy_repository.py.
- compose.yml (dora_data volume) and .env.example.
- CHANGELOG.md.

DO:
- Add a postgresql+psycopg driver dependency. Make get_db_connection_string return a
  Postgres URL from env (DORA_DATABASE_URL) when set, else fall back to sqlite for
  local/self-hosted dev.
- Make the sqlite-only FK pragma conditional (Postgres enforces FKs natively).
- Audit migrations for SQLite-specific bits (unnamed constraints, batch ops); ensure
  `flask db upgrade` runs clean on a fresh Postgres DB. Add named constraints where
  Postgres needs them.
- compose.yml: add a postgres service (or document managed Postgres via env) with its
  own volume and healthcheck; wire DORA_DATABASE_URL.
- Provide a one-shot data migration path (sqlite → pg) for existing self-host users.

DONE WHEN:
- App boots and all features work against Postgres; `flask db upgrade` is clean on a
  fresh pg DB.
- SQLite still works for local/self-hosted dev (no hard Postgres requirement there).
- A documented sqlite→pg migration moves an existing DB without data loss.
- Full pytest suite passes against Postgres (CI matrix updated). CHANGELOG.md updated.
```

## P7-04 — Production WSGI server + web/worker split

```
Replace Flask's dev server with a production WSGI server and move scraping/scheduled
jobs out of the web process into a dedicated worker, so the web tier scales
independently and a long job can't block requests.

READ FIRST:
- dora_api/startup.py (app.run — the dev server) and server_settings.py (the existing
  "run via gunicorn -c server_settings.py startup:app" note).
- startup.sh (monolithic entrypoint: 3 python procs + nginx), Dockerfile, nginx.conf.
- The in-process APScheduler usage (merchant_api + any dora_api schedules).
- merchant_api/startup.py (werkzeug make_server in a thread).
- CHANGELOG.md.

DO:
- Serve dora_api (and merchant_api if retained) via gunicorn/uvicorn-workers behind
  nginx; tune worker count via env. Keep app.run only as a dev fallback.
- Extract scheduled/scraping jobs into a SEPARATE worker process (a lightweight queue —
  RQ or APScheduler-in-its-own-process is fine to start). The web process must not run
  the scheduler.
- Split the container story: a `web` role and a `worker` role (same image, different
  entrypoint) so they can scale/deploy independently. Update startup.sh / compose to
  express the roles. nginx proxies API + serves SPA as today.

DONE WHEN:
- The web tier runs under gunicorn/uvicorn-workers (no dev server in the hosted path).
- No scheduler/scraping runs inside a web worker; the worker role handles jobs.
- web and worker can be scaled/restarted independently (verify with compose scale).
- Health endpoints distinguish web vs worker liveness. CHANGELOG.md updated.
```

## P7-05 — Redis (sessions/cache/rate-limit) + object storage for images

```
Add Redis for shared session/cache/rate-limit state and move image storage off the
local volume/DB to object storage, so multiple web workers share state and images
don't bloat the database or pin the app to one host.

READ FIRST:
- dora_api auth/session handling (cookie/session store) and any in-memory caching or
  rate limiting (A1 rate limits).
- Where images are currently stored (stock_item.image bytes; image cache dir;
  DORA_CACHE_DIR in compose.yml).
- requests_cache usage (merchant_api) — can move to Redis backend.
- CHANGELOG.md.

DO:
- Add Redis; back sessions, app-level caching, and rate limiting with it (configurable
  via env; in-memory fallback for self-hosted single-process).
- Move binary images (stock_item.image, cached images) to S3-compatible object storage
  (env-configured bucket/endpoint); store keys/URLs in the DB, not bytes. Provide a
  migration for existing images. Self-hosted can keep a local-disk driver.

DONE WHEN:
- Two web workers share session + rate-limit state via Redis (verify a session works
  across workers).
- Images are served from object storage; the DB no longer stores image bytes; existing
  images migrated.
- Self-hosted single-process still works with in-memory/local-disk fallbacks.
- pytest covers the storage abstraction (object vs local). CHANGELOG.md updated.
```

---

# PATH B — Managed single-tenant instances (recommended first)

## P7-B1 — Provisioning control plane

```
Build a control plane that provisions and manages one DiscountDora instance (container
+ database) per customer, so you can sell hosted Dora WITHOUT solving multi-tenant
isolation. Each customer is physically separate.

READ FIRST:
- COMMERCIALIZATION_REPORT.md §7 (Path B).
- Dockerfile, compose.yml, startup.sh, nginx.conf — the unit you'll provision.
- P7-03/04/05 — each instance should run the productionized roles.
- Your chosen host's API (Fly.io / Render / Railway / a container orchestrator).
- CHANGELOG.md.

BUILD (a small separate service — NOT inside dora_api):
- A control-plane service with its own store of customers → instances (subdomain,
  instance id, status, plan, db handle, created_at).
- Provision: on signup/checkout, spin up a per-customer instance (container + dedicated
  database) and route a subdomain (customer.app-domain) to it. Deprovision/suspend on
  cancellation.
- Lifecycle: start/stop/restart, image upgrade (roll customers to a new app version),
  per-instance backup/restore, and health monitoring.
- A thin admin UI/API for you to see and operate all instances.
- Keep the app itself essentially single-tenant — minimal app changes.

DONE WHEN:
- Signing up a new customer provisions an isolated instance + DB and routes their
  subdomain automatically.
- You can suspend/resume/upgrade/back-up an individual customer from the control plane.
- Cancellation deprovisions (or archives) cleanly.
- A documented runbook covers provision/upgrade/restore/deprovision. CHANGELOG.md
  updated.
```

> Path B uses the SHARED SaaS LAYER below for billing/compliance/ops. Billing
> (P7-06) drives the control-plane provisioning hooks.

---

# PATH A — True multi-tenant (graduate to this later)

## P7-A1 — Households-as-tenant + admin → owner / platform-admin split

```
Make a household the tenant boundary in DiscountDora and split the single admin role
into household owner vs platform admin. Builds on Part 6 P6-05.

READ FIRST:
- PROMPT_PLAN_PART_6_POLISH.md P6-05 (households, members, invites, attribution).
- dora_api/features/{auth,users}/* and the current "admin" role/usage.
- Every feature that owns user data: stock_items, shopping_lists, recipes, meal_plans,
  suggestions, budget, purchase_events (P6-01), consumption_events (P6-07).
- web_app auth/session stores; WelcomeWizard/onboarding.
- CHANGELOG.md.

DO:
- Land P6-05 if not already (households, household_members, invites, household_id on
  shared entities, backfill into a default household).
- Roles: HOUSEHOLD OWNER (manage their household: members, invites, billing) vs
  PLATFORM ADMIN (operate the service: support, abuse, config). Remove the conflated
  single "admin"; migrate existing admins appropriately.
- Every user-facing data read/write is scoped to the caller's household.

DONE WHEN:
- A household owner manages only their household; a platform admin can operate the
  service but is distinct from any household role.
- All shared data is household-scoped; existing single-user data migrated into a
  default household with the user as owner.
- pytest covers the role split and scoping. CHANGELOG.md updated.
```

## P7-A2 — Repository-enforced tenant isolation + leak tests

```
Guarantee that no DiscountDora household can ever read or write another household's
data, enforced at the single SqlAlchemyRepository choke point and proven by tests.
This is the make-or-break safety property of multi-tenant SaaS.

READ FIRST:
- dora_api/persistence/sqlalchemy_repository.py — the single repository all queries go
  through (your isolation choke point).
- How the current household/tenant context is established per request (after P7-A1).
- Every entity carrying household_id; any raw SQLAlchemy access that bypasses the
  repository (e.g. the direct StockItemProduct/association queries seen in barcodes.py).
- CHANGELOG.md.

DO:
- Establish an ambient "current tenant" (household_id) per request/job context.
- In SqlAlchemyRepository, AUTOMATICALLY filter every read by current household_id and
  stamp it on every write — so individual features cannot forget to scope. Make
  cross-tenant access require an explicit, audited "system" escalation (platform admin
  / background jobs only).
- Eliminate or wrap any raw-session queries that bypass the repository so they cannot
  leak across tenants.
- Write adversarial tests: user in household A attempts to read/update/delete every
  entity type owned by household B → must fail. Include the bypass paths.

DONE WHEN:
- All reads/writes are tenant-scoped at the repository layer by default; forgetting to
  scope in a feature is structurally impossible.
- Adversarial cross-tenant tests cover every shared entity (and known bypass paths) and
  all fail to leak.
- Background jobs/platform-admin escalation is explicit and audited.
- pytest green incl. the isolation suite. CHANGELOG.md updated.
```

---

# SHARED SaaS LAYER (both paths)

## P7-06 — Stripe billing

```
Add subscription billing to DiscountDora with Stripe. Do NOT build billing yourself.

READ FIRST:
- After P7-A1 (households) OR P7-B1 (control plane) — billing attaches to the
  household/customer record.
- dora_api/features/{auth,users,app_settings}/* and the audit feature.
- COMMERCIALIZATION_REPORT.md §6 (plans).
- CHANGELOG.md.

DO:
- Integrate Stripe Checkout (subscribe/upgrade) + Customer Portal (manage card/cancel).
- Store plan + subscription status on the household/customer; update it from Stripe
  WEBHOOKS (source of truth), verifying webhook signatures. Handle trial, active,
  past_due, canceled.
- Path B: a successful subscription triggers control-plane provisioning (P7-B1); cancel
  triggers suspend/deprovision.
- Never store raw card data; never log secrets. Idempotent webhook handling.

DONE WHEN:
- A user can subscribe, upgrade/downgrade, and cancel; status reflects via webhooks.
- Webhook signatures are verified; handling is idempotent; subscription state is the
  gate consumed by P7-07.
- (Path B) subscribe→provision and cancel→suspend are wired.
- pytest covers webhook state transitions with fixtures. CHANGELOG.md updated.
```

## P7-07 — Plan gating + usage limits

```
Gate DiscountDora features and enforce usage caps by plan, implementing the free/paid
split from COMMERCIALIZATION_REPORT.md §6 — so free delivers the "aha" and paid unlocks
the intelligence layer.

READ FIRST:
- P7-06 (plan/subscription status) and the audit feature.
- The premium features: P6-01 reconciliation, P6-03 price intelligence, P6-04
  proactivity, P6-05 household sharing, P6-09 costing, P6-10 self-drafting shop, P6-12
  briefing.
- app_settings/feature-flag patterns.
- CHANGELOG.md.

DO:
- A single server-side capability check keyed off plan (do NOT trust the client).
  Define capabilities: tracked_items_limit, household_member_limit, price_alerts,
  proactivity, reconciliation, costing, briefing.
- FREE: full pantry/lists/recipes/stocktake; personal price history limited to N items
  (e.g. 5–10); single user.
- PAID: unlimited price tracking + alerts; proactivity; household sharing beyond limit;
  reconciliation; costing/budget defense; briefing.
- Enforce caps server-side with friendly upgrade prompts at the boundary (not hard
  walls that hide the value — show what they'd get).

DONE WHEN:
- Free accounts hit caps with a clear, value-forward upgrade path; paid accounts unlock
  the gated features; all checks are server-side.
- Downgrade handles over-limit data gracefully (read-only / archive, not delete).
- pytest covers each capability gate at free vs paid. CHANGELOG.md updated.
```

## P7-08 — Compliance: privacy policy hooks, data export, account/data deletion, security headers

```
Add the privacy/security obligations that selling triggers: data export, account and
data deletion, and HTTP security headers. (Implements P5-01/P5-02.)

READ FIRST:
- STATUS.md P5-01 (security headers, dependency scanning) and P5-02 (privacy controls,
  DELETE /api/account, clear-history).
- dora_api auth/users, the data feature (backup/restore/export already exists — reuse),
  and nginx.conf / the app's response middleware.
- The audit feature (record privacy actions).
- CHANGELOG.md.

DO:
- DATA EXPORT: a user/household can export all their data (reuse the existing
  backup/export engine; ensure it's complete and self-serve).
- DELETION: DELETE account + household data (hard delete or documented retention),
  and a "clear history" for purchase/consumption/audit data. Confirm + audit each.
- SECURITY HEADERS: CSP, HSTS, X-Content-Type-Options, Referrer-Policy, frame-ancestors
  via nginx/app middleware. Add dependency scanning to CI.
- Ship a privacy policy + ToS surface (link in app); copy is yours to finalise.

DONE WHEN:
- A user can self-serve export all their data and delete their account/data; both are
  audited.
- Security headers present on all responses (verify with a scan); CI runs dependency
  scanning.
- pytest covers export completeness and deletion cascade. CHANGELOG.md updated.
```

## P7-09 — Operations: observability, CI/CD deploy, staging, backups

```
Make DiscountDora operable as a paid service: error tracking, logs/metrics, automated
deploys with a staging environment, and reliable backups.

READ FIRST:
- .github/workflows/ci.yml (existing lint/typecheck/build/test + manual release).
- compose.yml healthcheck, nginx /healthz, DORA_LOG_* config.
- After P7-03 (Postgres backups) and P7-04 (web/worker roles to monitor).
- CHANGELOG.md.

DO:
- Error tracking (Sentry or equivalent) wired into web + worker; structured logs;
  basic metrics (request rate/latency/error rate, job success/failure).
- Extend CI to deploy: a staging environment on merge to main, production on a tagged
  release (build on the existing manual release flow). Smoke-test after deploy.
- Automated, tested backups of Postgres + object storage; a documented restore drill
  (P5-09). Uptime monitoring + a status page.

DONE WHEN:
- Errors surface in the tracker with request context (no PII/secrets); web+worker health
  is monitored.
- Merge→staging and release→production deploys run automatically with a post-deploy
  smoke test.
- A restore drill recovers DB + images to a known-good state (documented + tested).
  CHANGELOG.md updated.
```

## P7-10 — Launch readiness

```
Final gate before charging real users: load test, demo/seed data, and first-run
onboarding. (Implements P5-03/P5-06/P5-07.)

READ FIRST:
- P7-03/04/05 (the productionized stack to load-test) and P7-07 (plan boundaries).
- F1 onboarding / WelcomeWizard and STATUS.md P5-06/07.
- CHANGELOG.md.

DO:
- Load test the Postgres write path and the worker under realistic concurrency; record
  a baseline and fix the top bottleneck found.
- Demo/seed mode: a one-command realistic dataset so prospects feel Dora immediately
  (and a reset). Mark demo data clearly.
- First-run/first-week onboarding that drives a new user to the "aha" fast (track
  something, see a price insight, get one proactive suggestion).

DONE WHEN:
- A documented load baseline exists; the top bottleneck is addressed.
- Demo seed + reset work via one command and showcase the premium "aha".
- A new user reaches first value quickly via guided onboarding.
- CHANGELOG.md updated.
```

---

## Sequencing & dependency notes

- **P7-01 first, always** — it's the legal gate and it re-points P6-03/P6-09. It depends
  on **P6-01** (paid_price history) being present; if P6-01 isn't done, do it first or
  the personal-price model has no data.
- **P7-02** is independent and tiny — do it anytime (ideally early).
- **PRODUCTIONIZE (P7-03→05)** before either branch. Path B can technically defer P7-03
  per-instance, but Postgres is recommended even for managed instances.
- **Path B (P7-B1)** is the fast route to revenue; **Path A (P7-A1→A2)** is the
  graduation. P7-A1 depends on **P6-05**. P7-A2 depends on P7-A1 and is the
  non-negotiable safety gate for multi-tenant — do not launch Path A without it.
- **SHARED SaaS LAYER:** P7-06 → P7-07 (gating needs billing state). P7-06 wires into
  P7-B1 (provision/suspend) on Path B, or the household record on Path A. P7-08/09/10
  can proceed in parallel with billing but should all land before public launch.
- **Do not run in parallel** any two prompts touching the same entities (e.g. P7-A1 and
  P7-06 both touch the household record; P7-03 and any migration-heavy prompt).
