# Optional deployment strategy — multi-tenant SaaS + managed single-tenant

**Type:** 🔵 deferred option — NOT a committed plan. A "revisit later" bucket.

> **Decision (2026-07-14, owner):** Dashy Dora will be **sold as self-hosted
> software** first. Everything in this document — multi-tenant SaaS (Path A) and
> managed single-tenant hosting (Path B), plus the scale/billing/operational work
> that only those models require — is **deliberately deferred** and kept *out* of
> the active self-host commercialization track. It's parked here so it isn't lost,
> and so the active follow-ups ledger isn't cluttered with work that only matters
> if the deployment strategy changes. **Revisit** this doc if/when hosting Dora for
> customers (rather than shipping it to them) becomes a real goal.

This is the counterpart to the **self-host commercialization track** (which lives
in `docs/05_investigations/COMMERCIALIZATION_REPORT.md` §1–4/§6-product-value and
the active `DORA_FOLLOWUPS.md` items). Selling self-host needs legal de-risk,
robustness, a licence + launch, and support — none of which is in here.

---

## 1. Why this is separate

The one artifact runs three ways (RECONCILED_FINISHING_PLAN **Decision 5** / §7.5):
**(a)** self-hosted single instance — *the chosen near-term product*; **(b)**
managed single-tenant instance you operate for a customer (**Path B**); **(c)**
multi-tenant hosted SaaS (**Path A**). Only (b) and (c) require the work below.
Keeping them in one blended "commercialization plan" would make the self-host
launch look far heavier than it is — hence the split.

## 2. The two deferred paths (from COMMERCIALIZATION_REPORT §7)

- **Path A — true multi-tenant.** One app, one Postgres, isolated by
  `household_id` on every row/query. Best margins/scale; the scary isolation work
  (one missed scope = cross-customer leak). **Months.**
- **Path B — managed single-tenant instances.** One container + one DB per
  customer, with automated provisioning + billing + hosting on top. No isolation
  problem (customers are physically separate). Worse margins, far faster/lower
  risk. **Weeks.**
- **Report's recommendation** (unchanged, for when this is revisited): start
  **Path B**, migrate to **Path A** once paying customers + real load justify the
  isolation investment.
- **Hard prerequisite:** SaaS = you host = **no central scraping** (the §2
  de-risk must land before/with any hosted move).

## 3. The parked work (relocated from the active ledger 2026-07-14)

Identity / tenancy (Path A):
- **FU-400** — Households-as-tenant; split `admin` into household-owner vs
  platform/instance-admin (report §5). Gated by MULTI_USER_READINESS §5.
- **FU-401** — Repository-enforced tenant isolation + cross-tenant leak tests
  (§7.5 discipline #1 keeps this a one-layer change).

Managed hosting (Path B):
- **FU-399** — Provisioning control plane (automated per-customer instance
  stand-up / upgrade / backup). Path-B-specific; irrelevant to self-host.

Scale prerequisites (only at multi-process / multi-node — a single self-host box
uses the in-memory / local-disk fallbacks by design, §7.5 #6):
- **FU-398** — Redis (sessions / cache / rate-limit) + object storage (S3-ish) for
  images.
- **FU-397 (worker-split half only)** — separate web vs background-worker tier.
  *(The "use a real WSGI server instead of the Flask dev server" half **shipped
  2026-07-14** in the self-host track — gunicorn, single-worker; see CHANGELOG /
  FU-397 RESOLVED. The scheduler currently runs in that single gunicorn worker;
  splitting it into a dedicated background-worker tier — so the web tier can scale
  to N workers/nodes — is the part parked here.)*

Billing & plan enforcement (hosted-only):
- **FU-402 (subscription half)** — Stripe *recurring subscription* billing tied to
  tenancy (Checkout + Customer Portal + webhooks). *(Selling self-host needs only a
  one-time licence / paid-download payment — a separate, lighter self-host-track
  decision, not this.)*
- **FU-403** — Plan gating + server-side usage limits. Only enforceable when *you*
  control the runtime; on self-host the customer owns the box, so tiering can't be
  enforced without DRM. Inherently SaaS.
- **SaaS freemium model** (COMMERCIALIZATION_REPORT §6) — the free-tier "aha" +
  paywall-what-compounds framing and per-item free caps are a hosted-SaaS
  monetization shape; the underlying *product value* (proactivity layer, household
  sharing, unlimited price tracking) is universal and stays in the self-host track.

Compliance (data-controller obligation — hosted-only):
- **FU-404** — Privacy-law compliance contract: privacy policy + ToS wording, and
  self-service **data export + account/data deletion (DSAR)**. The obligation
  follows the *data controller*; on self-host that's the operator, not the vendor
  (COMMERCIALIZATION_REPORT §1.2 — "self-hosted sidesteps most; SaaS does not"), so
  this activates only when *you* host user data. The self-host track keeps only a
  short honest **privacy statement** (SELF_HOST_COMMERCIALIZATION_PLAN Track 3);
  security headers already shipped (FU-387). *(Export/delete may still ship as
  optional product features earlier, but they're driven by this hosted need, not by
  the self-host sale.)*

Product analytics (hosted-only — the whole topic lives here as of 2026-07-16):
- **Usage analytics / telemetry** (design: `PROPOSAL_USAGE_TELEMETRY.md`, now 📦 parked).
  **Decided 2026-07-16 (owner): nothing is built for self-host.** The motivating ask
  ("know how people use my app") is the *maintainer's* and only pays off as **hosted,
  cross-install aggregate** analytics — the "**Share my usage data to help improve
  Dora**" checkbox (default OFF) that opts a *hosted* install into sending anonymised,
  aggregate usage counts to the author (proposal §4). It is the app's first outbound
  behavioural egress and is owner-sign-off-gated. **The self-host "efficiency lens"
  (proposal Surface A) was considered and dropped** — on a self-host box the reader is
  the household operator, whose real questions are outcomes (pantry accuracy, waste,
  spend), most of which are already answerable from existing domain data without a
  telemetry system. **Revisit only if a hosted offering opens**; until then, no build.
  (FU-566 resolved WON'T-DO for self-host.)

Operations (managed-service sliver):
- **FU-406 (on-call sliver only)** — uptime/SLA, on-call rotation, escalation. Only
  meaningful when you operate the service. *(Marketing, legal/licence, support/
  incident channel, and release process stay in the self-host launch track.)*
- Hosted ops from report §-Operations (Sentry/observability, CI/CD deploy +
  staging, status page) — the self-host-relevant bits (backups, dependency
  scanning) stay live under FU-405; the hosted-only bits belong here.

## 4. Gating questions — settle these first

`docs/05_investigations/MULTI_USER_READINESS.md §5` is the SaaS-path parking place
for the design questions that gate all of the above (household-vs-user tenancy;
same-deployment-vs-per-install; shared-vs-per-household catalogs). It also carries
the full pre-flight of single-tenant assumptions to dismantle (its §1–4).

## 5. The insurance already in place (so revisiting is a project, not a rewrite)

The distribution posture (Decision 5 / §7.5) is deliberately maintained *now* so
this door stays open cheaply — do not undo it while building self-host:
1. All data access routed through the `SqlAlchemyRepository` seam (tenant scoping
   injectable in one layer).
2. DB layer portable, Postgres the long-term target, SQLite still supported
   (FU-045).
3. Every cloud-vs-self-host difference is env/config-driven (same artifact).
4. No speculative `tenant_id` columns (single-tenant = tenancy of size 1).
5. Managed conveniences (relay, LLM, email, Redis, object storage) degrade
   gracefully to "feature absent" on the self-host default.

The only genuinely hard-to-retrofit piece is **multi-tenant isolation** (Path A).
Per the report, the Path B→A jump is a 6–12 month project *because* these
disciplines held — not a rewrite.

## 6. Revisit trigger

Open this doc when: (a) demand validates a hosted offering, or (b) a customer
explicitly wants Dora run *for* them rather than shipped to them. First stop:
MULTI_USER_READINESS §5. Until then, no build work here — it's a posture, not a task.
