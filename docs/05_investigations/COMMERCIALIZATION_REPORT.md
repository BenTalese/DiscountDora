# Dashy Dora (formerly Discount Dora) — Commercialization Report

> **Doc library:** see [00_DOCS_INDEX.md](00_DOCS_INDEX.md). The product is **Dashy Dora**; code identifiers still read "DiscountDora" until **P8-01** renames them, so references to "DiscountDora" mean the current code name.

A strategic analysis of selling DiscountDora (self-hosted, managed, or SaaS), the
legal exposure, the architectural reality, monetization, and the branching paths to
market. Companion to **PROMPT_PLAN_PART_7_COMMERCIALIZATION.md**, which turns the
decisions here into runnable prompts.

> **Self-host-first decision (2026-07-14).** The near-term plan is to **sell Dora
> as self-hosted software**. The **multi-tenant SaaS (Path A) + managed
> single-tenant (Path B)** material in this report — **§5 (households/tenancy
> reframe)**, **§7 (path to SaaS)**, and the **freemium / plan-gating parts of §6**
> — is **deferred and relocated** to
> [`../04_proposals/OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md`](../04_proposals/OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md).
> Read those sections there when/if a hosted offering is revisited. The
> **self-host commercialization track** stays here: §1–2 (legal de-risk), §3–4
> (robustness), and the *product-value* half of §6 (what's worth paying for),
> monetised via a one-time licence / paid download rather than subscriptions.

> **Not legal advice.** Sections on legal risk are engineering-informed risk
> analysis. Before selling, engage an Australian IP/commercial lawyer — especially
> on the retailer-scraping question, which is the dominant risk.

---

## Executive summary

- **The code is fine; the *data source* is the legal nightmare.** Centrally scraping
  Coles/Woolworths/Aldi/IGA at commercial scale (and reproducing their images) is the
  dominant risk. It is also the only feature that *requires* scraping.
- **You do not need a rewrite.** The concurrency ceiling is SQLite + Flask's dev
  server, not Flask. Productionize the existing stack; do **not** move to FastAPI or
  C#.
- **The fix preserves the magic.** Relocate "deals" from scraped shelf prices to the
  user's **own purchase-price history** (already pipelined by P6-01). You lose only
  pre-purchase cross-store discovery — the single most radioactive feature.
- **"SaaS" has two shapes.** True multi-tenant (months, scary isolation work) vs
  managed single-tenant instances (weeks, no isolation problem). **Start managed,
  graduate to multi-tenant once paying customers exist.**
- **Your single `SqlAlchemyRepository` is a strategic asset** — it makes eventual
  multi-tenant isolation enforceable in one place instead of across every query.
- **Monetize the intelligence, not the basics.** Free = core pantry + a taste of
  personal price intelligence. Paid = the entire P6 proactivity/household/reconciliation
  layer.

---

## 1. Legal exposure

### 1.1 Scraping (the dominant risk)

Dora scrapes retailer sites directly (`merchant_api/infrastructure/merchant_data_providers/`),
pulling prices **and product images**. Hobby self-host = invisible. Commercial =
exposed on multiple fronts:

| Vector | Risk |
|---|---|
| **Breach of website Terms of Use** (contract) | Coles/Woolworths ToU prohibit automated access. A paid product built on that data is an ongoing breach — cease-and-desist, breach-of-contract. |
| **Copyright** | Prices are facts (not copyrightable); **product images and descriptions are**. The scrapers copy images. |
| **Trademark** | Naming retailers factually is OK (nominative use); implying endorsement or using logos is not. |
| **Scale = detection** | Retailers actively block scrapers. Central commercial scraping is detectable and worth their legal attention. |

**The architectural-legal link that decides your business model:**

- **Self-hosted / edge scraping** — the *user's* machine scrapes from *their* IP for
  *personal* use. Far more defensible; liability sits largely with the user.
- **Centrally-hosted SaaS scraping** — *you* scrape at commercial scale and redistribute.
  Dramatically higher exposure.

→ **Any hosted/SaaS model effectively forces you to stop central scraping.**

### 1.2 Other items

- **AI/LLM** — bring-your-own, nothing bundled. No model-licensing liability. Keep it.
- **`fuzzywuzzy` is GPLv2** (may pull GPL `python-Levenshtein`). A copyleft landmine
  for distributed software. **Swap for RapidFuzz (MIT)** — near drop-in. Do this
  regardless of path.
- **Recipe URL import** — copying instructions is copyright; fine for personal import,
  risky if recipes are redistributed between users.
- **Privacy law** — selling makes you a data controller. AU Privacy Act (and GDPR for
  any EU users) requires a privacy policy, data export, and data/account deletion
  (P5-02, not started). Self-hosted sidesteps most; SaaS does not.
- **Your code is MIT; Clapy is your own project** — no inbound issue. Note MIT lets
  others resell your code; consider relicensing future versions if that matters.

---

## 2. The de-risk strategy (keep the magic, shed the exposure)

**Reframe:** the legal problem is *who scrapes and what data source*, not "tracking
prices." Relocate price intelligence onto data the user owns.

- **Deals become personal.** Using P6-01 reconciliation (`paid_price` per item), Dora
  learns *your* prices: "You usually pay $4.50 — you just logged $3.00, your cheapest
  ever." Legal, and more personal than a shelf price. The **P6-03 engine works
  unchanged** over personal history (lowest-in-90-days, fake-markdown → "you're paying
  more than usual", good-deal alerts).
- **What survives (almost everything):** pantry, expiry, recipes, meal plans,
  cook→consume (P6-07), lists, self-drafting shop (P6-10), *cook the expiring* (P6-08),
  briefing/inbox (P6-04/12), household (P6-05), personal price intelligence (P6-03 over
  paid_price), costing/budget defense (P6-09 over logged prices).
- **The only true casualties** are **cross-store "where is X cheapest now"** and
  **pre-purchase "X is on special at Woolies this week"** — which are *also the most
  radioactive features.*

### The spectrum (risk drops top→bottom)

1. Centrally-hosted SaaS that scrapes — *current_. Max exposure. Avoid.
2. **Manual + personal purchase-price history** — fully legal, simple. Recommended core.
3. **+ Optional self-hosted/BYO edge scraping** — off by default, you never operate it.
   Restores full magic for the BYO crowd; liability is personal-use.
4. **+ Community-contributed prices (later)** — users share prices; you aggregate facts.
   Legally restores cross-store comparison at the cost of scale + moderation.

### Recommendation

Layered hybrid: **core = manual + personal price history; demote (don't delete)
scraping to a self-hosted-only, off-by-default module; leave a seam for community
prices.** Critically, **lean on P6-01** so price capture is a frictionless byproduct of
finishing a shop — otherwise de-scraping trades legal risk for friction risk and kills
the "fast" brand.

### Naming

"Discount Dora" implies "compare store discounts." With personal price history,
reposition to *"never overpay — Dora knows your prices."* Name still works; the promise
shifts from "find the cheapest store" to "know a good price when you see one."

---

## 3. Robustness & the framework question

**Current stack (verified):** SQLite + Flask's built-in dev server (`app.run()` in
`dora_api/startup.py`) + a monolithic container running three Python processes +
in-process APScheduler scraping + nginx. A textbook **single-household self-hosted**
design — well-built for that, not for many concurrent users.

**Why it won't scale as-is (none of these are "Flask's fault"):**

1. **SQLite is the hard ceiling** — single-writer lock; concurrent writers serialize.
2. **Flask dev server** is single-process, not production-grade. (Code is already
   gunicorn-aware — `server_settings.py`.)
3. **In-process APScheduler** competes with web requests and can't scale independently.

**FastAPI? Mostly no — and not for concurrency.** The bottleneck is SQLite + the dev
server, both fixable without touching the framework. Flask behind gunicorn + Postgres
serves thousands of concurrent users. FastAPI's real edge is async I/O (scrape fan-out,
LLM streaming) — a targeted win, not a rewrite trigger.

- **FastAPI migration effort: large.** Business logic (`features/*`, Clapy interactors)
  is portable; the plumbing is deeply Flask-coupled (routers, `@has_request_body`,
  `flask_sqlalchemy`/`flask_migrate`, cookie auth, `dependency_injector`,
  `SqlAlchemyRepository`). Weeks-to-months of risky, low-user-value work.
- **C#: worse.** Full rewrite, many months, throws away everything. Rule it out.

**Recommendation:** Don't rewrite. Productionize Flask. Add FastAPI *alongside* later
only for specific streaming/scrape endpoints if a *measured* async bottleneck appears.

---

## 4. Architectural changes for reliability / efficiency

Priority order (mostly framework-independent):

1. **SQLite → PostgreSQL** — the non-negotiable one. SQLAlchemy is already DB-agnostic;
   migrations/repository show some Postgres awareness. ~1–2 weeks incl. cleaning
   SQLite-specific migration bits and FK/`ON DELETE` testing. Use managed Postgres.
2. **Proper WSGI server** — gunicorn/uvicorn-workers behind nginx. Days; big win.
3. **Extract scraping into a separate worker + queue** (RQ/Celery/arq), out of the web
   process. If you keep any scraping: **scrape once, share across tenants** — central
   dedup is a big efficiency win *and* reduces legal footprint.
4. **Redis** — sessions, cached data, rate limiting.
5. **Object storage (S3-style) for images** — not the data volume/DB.
6. **Multi-tenant isolation** (Path A) — enforce at the `SqlAlchemyRepository` choke
   point + tests proving cross-tenant reads are impossible.
7. **Observability & ops** — centralized logs, metrics, error tracking (Sentry),
   uptime monitoring beyond nginx `/healthz`.
8. **Security & privacy gaps** — security headers (P5-01), data export/delete (P5-02).

**Net:** Postgres + real WSGI + a separate scrape worker + Redis ≈ 95% of SaaS-grade
scalability for a fraction of a rewrite's cost.

---

## 5. Households & the admin reframe

> **Deferred → self-host-first (2026-07-14).** This is multi-tenant (Path A) work,
> relocated to `../04_proposals/OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md`. Retained
> here for the strategic record.

Going commercial is bigger than "add households" (P6-05) — it's **multi-tenancy**, and
the single `admin` role splits into two distinct concepts you must not conflate:

- **Household owner** — manages their household (invites, members, billing). The P6-05
  reframe.
- **Platform/instance admin** — you, operating the service (support, abuse, config).

Today's single "admin" assumes operator == user. Untangling that, and proving household
A can never read household B's data, is the real work and a prerequisite to charging.

---

## 6. Monetization

**Principle:** the free tier must deliver the "aha" or nobody converts. Paywall what
compounds *after* the hook, especially recurring-cost and household/power features.

**Free (the hook):**
- Full pantry tracking, expiry/low alerts, basic lists, recipes, manual stocktake.
- A *taste* of price intelligence: personal price history on a **limited number of
  items** (e.g. 5–10) — enough to feel "it watches my prices."
- Single user.

**Paid (the power & the cost-drivers):**
- **Unlimited price tracking + price-drop / good-deal alerts** (P6-03) — the natural
  upgrade trigger when they hit the free cap.
- **The proactivity layer** — suggestion inbox, deal→list matching, run-out prediction
  (P6-04), self-drafting shop (P6-10), daily briefing (P6-12).
- **Household sharing** beyond 1–2 members + realtime (P6-05).
- **Receipt/email reconciliation** (P6-01) and **recipe/week costing + budget defense**
  (P6-09).
- **Cost-drivers:** cloud hosting + automated backup; (if ever hosted) AI usage caps.

**The story:** the P6 wiring tier *is* your premium tier. Free proves the concept on
today's state; paid is everything that makes Dora think.

---

## 7. The path to SaaS

> **Deferred → self-host-first (2026-07-14).** The entire SaaS/managed path
> (both forks) is relocated to
> `../04_proposals/OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md` as a "revisit later"
> option. Retained here for the strategic record; act from the optional doc if the
> hosted path is reopened.

### The fork that decides everything

- **Path A — True multi-tenant.** One app, one Postgres, isolated by `household_id` on
  every row/query. Best margins/scale. Hard, scary isolation work (one missed scope =
  cross-customer leak). **Months.**
- **Path B — Managed single-tenant instances.** One container + one DB per customer,
  with automated provisioning + billing + hosting on top. No isolation problem (customers
  are physically separate). Worse margins, far faster/lower-risk. **Weeks.**

**Recommendation:** **Start Path B, migrate to Path A** once paying customers and real
load justify the isolation investment. Productionization (Phase 1) carries over.

**Your advantage for Path A:** the single `SqlAlchemyRepository` lets you enforce tenant
scoping in *one* place rather than auditing every query.

### Hard prerequisite

**SaaS = you host = no central scraping.** The Section 2 de-risk must land **before or
with** the SaaS move. Don't build SaaS on top of centralized scraping.

### Phased roadmap

- **Phase 0 — Decide & de-risk:** pick tenancy model (B first); land scraping de-risk;
  pick hosting (Fly.io/Render/Railway suit your Docker setup; AWS/GCP for headroom).
- **Phase 1 — Productionize:** Postgres; gunicorn/uvicorn; split web vs worker; Redis;
  object storage. (Required either path; carries over.)
- **Phase 2 — Identity & tenancy:** households as tenant (P6-05); admin → owner +
  platform-admin; harden signup/login/email-verify (you have A1 auth — harden, don't
  replace). Path A: repository-enforced isolation + leak tests.
- **Phase 3 — Billing & plans:** Stripe (Checkout + Customer Portal + webhooks);
  plan-gating (Section 6); server-side usage limits.
- **Phase 4 — Compliance & trust:** privacy policy + ToS; data export + account/data
  deletion (P5-02); security headers (P5-01); encrypted backups; breach plan.
- **Phase 5 — Operations:** observability (Sentry/logs/metrics); CI/CD deploy +
  staging; status page; support inbox.
- **Phase 6 — Launch readiness:** load test (Postgres write path); demo/seed; first-run
  onboarding (P5-06/07).

### Build vs buy

**Buy/rent:** billing (Stripe), error tracking (Sentry), transactional email
(Postmark/SES — better deliverability than self-hosted SMTP), hosting + managed Postgres.
**Keep your own:** the app, auth (harden, don't replace), domain logic.

### Honest effort

- **Path B managed-instances MVP:** weeks (mostly ops/glue).
- **Path A multi-tenant, production-ready:** months.

The trap is jumping straight to Path A before validating demand.

---

## 8. Decision checklist (fill these before running prompts)

1. **Business model:** sell self-hosted software / managed instances (Path B) / true
   SaaS (Path A)? → determines which Part 7 branch you run.
2. **Scraping:** removed entirely / demoted to self-hosted off-by-default / community
   prices later? → P7-01 scope.
3. **Hosting target:** Fly.io / Render / Railway / AWS / GCP?
4. **Pricing:** free caps (tracked-item limit, household size), paid tiers, price points.
5. **Geography:** AU only (Privacy Act) or also EU (GDPR)? → compliance scope.
6. **Name/positioning:** keep "Discount Dora" with the personal-price reframe, or
   reposition?

---

## Recommended reading order

1. This report (decisions).
2. **PROMPT_PLAN_PART_7_COMMERCIALIZATION.md** — run the **shared tier** (de-risk +
   productionize), then **your chosen branch** (B or A), then the **shared SaaS layer**
   (billing, compliance, ops).
3. PROMPT_PLAN_PART_6_POLISH.md — the feature-wiring that becomes your premium tier;
   sequence it against the SaaS work (P6-01 especially is a de-risk dependency).
