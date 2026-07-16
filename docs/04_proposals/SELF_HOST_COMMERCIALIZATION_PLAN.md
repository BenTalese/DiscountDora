# Self-host commercialization plan

**Type:** 🟡 active plan (self-host track). **Owns:** the sequence to get Dashy Dora
sold as **self-hosted software**. **Raised by:** FU-412 (action the
`docs/05_investigations/COMMERCIALIZATION_REPORT.md` into a real plan).

> **Scope.** This is the self-host track only — the report's live sections
> **§1–2 (legal de-risk)**, **§3–4 (robustness)**, and the **product-value half of
> §6 (what's worth paying for)**. The hosted/SaaS material (report §5, §7,
> freemium/plan-gating) is **out of scope**, parked in
> [`OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md`](OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md).
> The pricing/billing *decision* lives in `DORA_FOLLOWUPS.md` **FU-562**; this doc
> is the umbrella that sequences it alongside legal, compliance, and launch.

> **Not legal advice.** The legal items below are engineering-informed risk notes.
> Engage an Australian IP/commercial lawyer before selling — especially on the
> scraping question and the licence change.

---

## TL;DR — where this actually stands

**The good news: the report's hard technical work is already done.** When the
report was written it recommended a productionization program (Postgres, a real
WSGI server, dropping the GPL fuzzy-match dep, demoting scraping). **All of that has
since shipped.** So selling self-host is *not* an engineering project any more — it's
a **legal + packaging + billing** project.

**Four tracks remain, only one of which is new:**

| Track | What's left | Owner FU | State |
|---|---|---|---|
| **1. Legal de-risk** | Relicense off MIT; scraping disclaimer + recipe-import note in terms | **FU-567 (new)** + FU-562 note | 🔴 decision |
| **2. Billing / product-value** | Offline licence key + entitlements gate + Settings→License; tier split already decided | **FU-562** | 🟡 decided, build pending |
| **3. Compliance** | Privacy policy; self-service data export + account deletion (DSAR) | **FU-404** | ⚪ mostly unbuilt |
| **4. Launch readiness** | Positioning/marketing, release process, support channel | **FU-406** + FU-557 | ⚪ last-mile |

**The single most important finding:** the repo ships under an **MIT licence**, which
lets anyone take the code and resell or redistribute it for free — directly
undermining the paid-self-host model (FU-562's leverage is gating updates, which MIT
defeats). **Relicensing is a prerequisite to charging, not a nice-to-have.** Spawned
as **FU-567**.

---

## 1. Current-state reality check (report §3–4 vs today)

The report's productionization recommendations, and their status now:

| Report rec | Status | Evidence |
|---|---|---|
| §1.2 Drop GPL `fuzzywuzzy` → RapidFuzz (MIT) — "do regardless of path" | ✅ **done** | `requirements.txt` (FU-196); RapidFuzz throughout `features/recipes/` |
| §4.1 SQLite → PostgreSQL (portable, PG the target) | ✅ **done** | `psycopg[binary]` pinned; FU-045; SQLite still supported for lightweight self-host |
| §4.2 Real WSGI server instead of Flask dev server | ✅ **done** | `gunicorn` pinned; FU-397 (single-worker gthread; scheduler stays singular) |
| §3 / §2 Demote central scraping to self-hosted, off-by-default | ✅ **done** | Scraper extracted to the standalone `dora-companion`; core ships no live scrape (RECONCILED_FINISHING_PLAN Decision 1) |
| §4.8 Security headers (P5-01) | ✅ **done** | `middleware.py` — CSP, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`; FU-387 hardening bundle |
| §4.3 Separate scrape worker + queue | ➗ **n/a for self-host** | Scraping left the core; the web-vs-worker split is a *scale* concern parked in OPTIONAL_SAAS §3 (FU-397 worker half) |
| §4.4–4.6 Redis / object storage / multi-tenant isolation | 🔵 **parked** | Scale/hosted concerns — OPTIONAL_SAAS §3 (FU-398/400/401) |
| §4.8 Data export/delete (P5-02 / DSAR) | ⚪ **unbuilt** | Only `delete_user_as_admin.py` exists; no self-service export or account deletion → Track 3 / FU-404 |

**Takeaway:** everything framework/robustness-related that the report treated as a
blocker is complete. Do **not** re-open the "should we move to FastAPI/C#?" question —
the report ruled it out and the concurrency ceiling it worried about (SQLite + dev
server) is already lifted. The remaining work is non-code (legal, marketing) plus two
bounded builds (billing gate, DSAR).

---

## 2. Track 1 — Legal de-risk (report §1–2)

The report's headline: *"the code is fine; the data source is the legal nightmare."*
The architectural de-risk (scraping → companion) already landed. What remains is
**paperwork that gates selling**, not engineering:

- **🔴 Relicense off MIT → FU-567.** MIT permits resale and redistribution of the
  source — fatal for a paid product. Options: a **source-available commercial
  licence** (e.g. PolyForm Noncommercial / a custom "you may run it, not resell it"
  licence), a **dual licence** (free for personal/non-commercial, paid for a
  commercial licence), or **BSL** (converts to open after N years). This is a
  decision the owner + a lawyer make; see FU-567.
- **Scraping disclaimer in the licence + terms.** The core ships no scraper, but the
  companion does. The licence/terms must state that live retailer scraping is the
  *self-hoster's* responsibility and disclaim it — pushing residual liability to the
  operator (report §1.1's "liability sits with the user"). Currently tracked only as a
  buried note in FU-562; promoted here into Track 1, drafted with the licence.
- **Recipe-import personal-use note.** Recipe URL/paste import copies instructions —
  fine for personal import, risky if redistributed. A one-line terms note ("imported
  recipes are for your own use") closes it. Low effort.
- **Privacy posture is a self-host advantage.** Self-hosted sidesteps most data-controller
  obligations (the user runs their own instance) — but if you offer *any* managed
  option later, that flips (OPTIONAL_SAAS). For self-host, the privacy policy is a
  short honest statement, folded into Track 3.

---

## 3. Track 2 — Billing & product-value (report §6-product-value → FU-562)

This track is **already designed** — FU-562 holds the decisions. Summary so it's legible
here; FU-562 stays the source of truth:

- **Enforcement = offline signed licence key** (Ed25519, bundled public key). No
  phone-home (Charter P8; air-gap-friendly). Bypassable by determined users — accepted;
  the real leverage is gating **updates/downloads**, which is why **FU-567 (relicensing)
  gates this** (MIT would let someone strip the check and redistribute legally).
- **Platform = Lemon Squeezy** (merchant-of-record; issues + validates keys, hosts
  download/update delivery — most of the plumbing comes built-in).
- **Tier split — decided:** Free "Core" (pantry/stock/stocktake/recipes+cook/lists/
  dashboard/**Basic no-LLM assistant**/import-backup/expiry+low alerts, **no item caps**)
  vs Paid "Full" (the whole intelligence/proactivity layer + meal plans + AI assistant
  mode + native app + updates/support).
- **After-trial = fall back to Core** (no bricking; hide-don't-nag upsell, R-029).
- **One server-side entitlements service = single source of truth (R-003).** SPA learns
  its tier via the existing `/api/auth/capabilities` probe (extend it). Route through the
  existing `AdminSystemFeaturesSettings.vue` flags + `master_llm_enabled`.
- **Still-open forks (FU-562):** revenue model (annual / one-time+upgrades / perpetual /
  donations), trial delivery mechanism (first-run grace / issued key / demo-only), trial
  length (14 vs 30d). These block the *build*, not this plan.
- **Note vs report §6:** the report's per-item free caps (5–10 tracked items) were a
  *SaaS* monetization shape and are **rejected for self-host** (item caps break a pantry
  app + feel petty on a box the user owns) — the split is by *feature layer*, not volume.

---

## 4. Track 3 — Compliance (report §4.8 / P5-02 → FU-404)

- **Self-service data export** — a user can download their own data. Unbuilt.
- **Account + data deletion (DSAR)** — a user can delete their account and data. Only an
  *admin-deletes-a-user* path exists (`delete_user_as_admin.py`); no self-service.
- **Privacy policy + ToS hooks** — a place in-app to surface them. Unbuilt.
- **Security headers** — ✅ already shipped (§1 table).

Scope note (from FU-404): the FINALISATION_PLAN Track-1 FST persona flows will *exercise*
these once built; the **legal drafting** of the policy/ToS wording stays owner+lawyer work.
For self-host the bar is lower than SaaS (the operator is the data controller), but export
+ delete are table-stakes and cheap to build on the existing repository seam.

---

## 5. Track 4 — Launch readiness (report §2-naming + §8 → FU-406 + FU-557)

- **Positioning / naming (report §2).** The rename to **Dashy Dora** shipped (P8-01), but
  the *promise* reframe hasn't been made deliberately: from "compare store discounts" →
  **"never overpay — Dora knows your prices"** (personal price history over the user's own
  `paid_price`, which survives de-scraping). Cross-store "cheapest right now" still appears
  in copy (`DoraChat.vue`, `StockItemDetailPage.vue`) — architecturally fine (it runs over
  *linked products* fed via the ingestion API, not core scraping), but the marketing story
  should lead with personal price intelligence. **Decision folded into FU-406 marketing**,
  not a separate FU.
- **Marketing** — landing/sales page. Unbuilt (FU-406).
- **Support / incident channel** — the plumbing shipped dormant (FU-370); standing up a
  real channel is **FU-557**.
- **Release process** — how a paying self-hoster gets + updates the build (ties to the
  Lemon Squeezy download gate in Track 2). Unbuilt (FU-406).
- **QA / systems test** — already owned by `FINALISATION_PLAN.md` Track 1 (FST +
  release-gate); not re-scoped here.

---

## 6. Recommended sequence

1. **Decide the licence (FU-567)** — everything else about charging is undermined until
   this is settled; it's also the longest lead-time item (needs a lawyer). Start here.
2. **Resolve FU-562's open forks** (revenue model, trial mechanism, length) — a short
   owner decision session; unblocks the billing build.
3. **Build Track 2** (FU-562 build sequence: entitlements service → gate the intelligence
   surfaces → trial mechanism → extend `/api/auth/capabilities` → SPA tier-awareness).
   This is the bulk of the code.
4. **Build Track 3** (FU-404: data export + self-service account deletion) — bounded,
   sits on the repository seam.
5. **Track 1 paperwork + Track 4 launch** (licence text, scraping disclaimer, privacy
   policy, positioning copy, landing page, support channel FU-557, release process) — the
   last-mile, much of it non-code, done close to launch.

Tracks 1–2 are the critical path; Tracks 3–4 can proceed in parallel once the licence is
decided.

---

## 7. Report-section coverage

Every live section of `COMMERCIALIZATION_REPORT.md` mapped to a home (audit at a glance):

| Report § | Topic | Home | Status |
|---|---|---|---|
| §1.1 | Scraping legal risk | Track 1 (architectural de-risk done; disclaimer pending) | ➗ |
| §1.2 | GPL dep, AI BYO, recipe copyright, privacy, MIT resale | RapidFuzz ✅; MIT → **FU-567**; recipe note Track 1; privacy Track 3 | ➗ |
| §2 | De-risk strategy (personal price history) + naming | Architectural ✅ (P6-01 `paid_price`); positioning → Track 4 / FU-406 | ➗ |
| §3 | Framework question (don't rewrite) | ✅ resolved — productionized on Flask; **do not reopen** | ✅ |
| §4.1–4.2, 4.8-headers | Postgres, WSGI, security headers | ✅ done (FU-045, FU-397, FU-387) | ✅ |
| §4.3–4.6 | Scrape worker, Redis, object storage, multi-tenant | 🔵 parked — OPTIONAL_SAAS §3 (scale/hosted) | 🔵 |
| §4.8-DSAR | Data export/delete | Track 3 / FU-404 | ⚪ |
| §5 | Households / admin reframe (multi-tenant) | 📦 parked — OPTIONAL_SAAS (Path A) | 📦 |
| §6 product-value | What's worth paying for (feature-layer split) | Track 2 / FU-562 | 🟡 |
| §6 freemium/caps | Per-item free caps, SaaS freemium framing | 📦 parked — OPTIONAL_SAAS (rejected for self-host) | 📦 |
| §7 | Path to SaaS (A/B) | 📦 parked — OPTIONAL_SAAS | 📦 |
| §8 | Decision checklist | Model=self-host ✅; scraping=companion ✅; pricing/geography/naming → FU-562 + FU-567 + FU-406 | ➗ |

Status key: ✅ done · ➗ done-with-carve-outs · 🟡 active · ⚪ not-started · 🔴 needs-a-decision · 🔵 designed-not-built · 📦 superseded/parked.

---

## 8. Open decisions — closed

Per the CLAUDE.md close-out rule, every fork this plan surfaced is either answered inline
or spawned as an FU:

- **Licence model (MIT → what?)** → spawned as **FU-567** (owner + lawyer decision).
- **Scraping disclaimer wording** → Track 1, drafted with FU-567's licence text (no separate FU).
- **Revenue model / trial mechanism / trial length** → already open in **FU-562** (unchanged).
- **Positioning reframe (personal-price story)** → folded into **FU-406** marketing (no separate FU).
- **DSAR build scope** → **FU-404** (unchanged).
- **Everything hosted/SaaS** → **out of scope**, OPTIONAL_SAAS doc (unchanged).

No live undecided fork remains in this doc.

---

## 9. New follow-up spawned

- **FU-567** — Relicense Dashy Dora off MIT for the paid self-host model (source-available /
  dual / BSL). Prerequisite to FU-562's update-gating leverage. Owner + lawyer decision.

*(All other work maps to existing FU-562 / FU-404 / FU-406 / FU-557.)*
