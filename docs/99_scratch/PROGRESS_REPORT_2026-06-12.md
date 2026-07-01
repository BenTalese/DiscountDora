# Dashy Dora — Real Progress Report (2026-06-12)

> **⚠️ STALE SNAPSHOT — 2026-07-01.** This is a point-in-time report from 12 June. Since then: Phase 2 ingestion API landed in full (C-10.1 → C-10.4), Phase 1 loop is effectively closed (P6-04 suggestions, P6-09 costing, P6-13 stocktake all done; P6-10 plumbing done and tracked as **FU-351**; P6-12 daily briefing is unbuilt and tracked as **FU-352**), the C-1b Stock Item Detail brief closed the 16-bullet Bucket A-1 NO_HOME cluster, and Products-as-overlay reshaped the My Products / Product History surfaces. For **current** state read the top entry of `DORA_WORKLOG.md` + `CHANGELOG.md`; do **not** treat the numbers below as current. The residual NO_HOME clusters from this snapshot are tracked as **FU-359** (Data page), **FU-360** (Dora Bot polish), **FU-361** (Help content), **FU-362** (A-5 Settings), **FU-363** (Bucket C bundle), **FU-430** (Stocktake residuals), **FU-431** (Product History), **FU-432** (Recipe Detail residuals). Kept for the historical audit trail.

The detailed per-bullet audit is at [docs/99_scratch/FEEDBACK_AUDIT_2026-06-12.md](FEEDBACK_AUDIT_2026-06-12.md). Here's the full report combining pathway + feedback.

---

## Part 1 — Pathway progress (5-phase plan)

| Phase | What it contains | Real status |
|---|---|---|
| **Phase 0 — Foundations & truth** | Wave A (theme/buttons/modals/filters/skeleton/text-size/sticky footer/renames) + Wave B bugs + INVs + cross-cutting C-cross config/opt-ins + STATUS re-baseline. | **~95% done.** Wave A all chunks shipped; Wave B clusters shipped; INV-1..6 run; C-cross Chunks 1–5 shipped. **Still open:** P8-01 rename ("DiscountDora" → "Dashy Dora" in code), STATUS.md re-baseline, INV-7/8/9/10 not yet run. |
| **Phase 1 — Close the loop (Part 6)** | Shopping lists (P6-01), cook mode (P6-07), barcode/QR cleanup (P6-02), suggestions (P6-04), confidence-driven stocktake (P6-13), costing/self-drafting/daily-briefing (P6-09/10/12). State-ownership refactor as enabler. | **~85% done.** Cart Button C-7 Chunks 1–4 + FU-131 ✅. State Ownership Chunks 1–6 ✅ (7 deferred). Shopping Lists Chunks 1–7 ✅. Stock Overview Chunks 1–6 ✅. Cookbook Chunks 1–10 ✅. Cook Mode Chunks 1–6 ✅. **Still open:** P6-04 suggestions/run-out, P6-09 costing, P6-10 self-drafting, P6-12 daily briefing, P6-13 confidence-driven stocktake. P6-02 barcode/QR cleanup ✅. |
| **Phase 2 — Ingestion API** | C-10 ingestion API (Dora-core seam) so the standalone scraper companion can push products/offers/observations. | **0% done.** [PROPOSAL_INGESTION_API.md](../04_proposals/PROPOSAL_INGESTION_API.md) is written. No code. |
| **Phase 3 — Champion (Part 8)** | P8-07 Zero-Input Pantry (flagship), P8-02 barcode-to-add via Open Food Facts, P8-05/06 buy/wait oracles, P8-08 Dora Score, P8-09 culinary memory, P8-10 native app. | **0% done.** No proposals beyond the part-8 plan stubs. |
| **Phase 4 — Commercialize** | Postgres migration (FU-045), Path B managed instances → Path A multi-tenant, Stripe, compliance. | **0% done.** Distribution-posture checklist (§7.5) actively gates everyday work; that's all. |

### Open browser-verify backlog (Phase 1 lock-in)

Code is shipped, manual verification pending. 18 FUs:

- Cart Button: FU-127 (Chunk 1), FU-130 (Chunk 2), FU-132 (Chunk 3), FU-135 (Chunk 4), FU-145 (Chunk 3 UI)
- State Ownership: FU-141 (Chunk 4), FU-142 (Chunk 6)
- Stock Overview: FU-120, FU-121, FU-122, FU-123, FU-124, FU-125 (Chunks 1–6)
- Cookbook: FU-103, FU-105, FU-116, FU-119 (Chunks 7–10)
- C-cross: FU-110, FU-111, FU-112, FU-113, FU-114 (Chunks 1–5)

### Pathway summary

You are **at the boundary between Phase 1 (~85% done) and Phase 2 (0% done).** The remaining 15% of Phase 1 is the strategic Part-6 features that haven't been touched (suggestions/run-out, costing, self-drafting shop, daily briefing, confidence-driven stocktake) — not just polish.

---

## Part 2 — Feedback actioned (per-bullet audit)

**Denominator:** 309 discrete asks across 30 surfaces (the document has more bullet *lines* but some are sub-asks under a parent; the auditor counted only discrete requests).

| Status | Count | % |
|---|---:|---:|
| **SHIPPED** (in code) | **109** | **35.3%** |
| **PROPOSED** (designed, not built) | **142** | **45.9%** |
| **NO_HOME** (no design home anywhere) | **58** | **18.8%** |

So: **~35% of your feedback is in the running app.** Another **46% is fully designed but waiting for someone to build it**. The remaining **19% has no plan at all yet.**

### Where the shipped work landed

Top-shipping surfaces (highest absolute counts of bullets converted to code):

| Surface | Shipped / Total |
|---|---:|
| Stock Overview | **32 / 41** (78%) |
| Cookbook (Recipes Overview) | **22 / 28** (79%) |
| Recipe Detail | **17 / 33** (52%) |
| Cook Mode | **16 / 19** (84%) |
| My Products | **8 / 23** (35%) |
| Shopping Lists | **8 / 8** (100%) |
| Stock Item Detail | **7 / 29** (24%) |
| Product Search | **7 / 32** (22%) |
| Dashboard | **4 / 11** (36%) |
| Onboarding | **4 / 24** (17%) |

### Where the designed-but-unbuilt work sits

By proposal (these are your **Phase 2/3 work queue**):

| Proposal | PROPOSED bullets |
|---|---:|
| `PROPOSAL_MEAL_PLANS.md` (C-2) | **~45** |
| `PROPOSAL_INGESTION_API.md` (C-10) + Product Search | **~22** |
| `PROPOSAL_ONBOARDING.md` (C-5) | **~20** |
| `PROPOSAL_COOKBOOK.md` (C-4) tail | ~11 |
| `PROPOSAL_CART_BUTTON.md` (C-7) extensions | ~13 |
| Product History redesign | ~7 |
| Dashboard card redesigns | ~7 |
| Stock Overview minor | ~7 |
| `PROPOSAL_ALERTS.md` (C-9) | ~4 |

**Single biggest unbuilt block: Meal Plans.** 45 bullets designed, 1 shipped. That's the largest concentrated piece of design debt — it's a whole surface waiting for an impl plan.

### Where there's no plan at all (NO_HOME — 58 bullets)

These are bullets without a home in any brief, proposal, or INV:

| Cluster | Count | Source |
|---|---:|---|
| **Stock Item Detail polish** (layout, button placement, open design) | **16** | COVERAGE_GAPS A-1 |
| **Data page** (move under Settings, formats, schema templates, …) | **8** | COVERAGE_GAPS A-2 |
| **Dora Bot polish** (text size, chip toggle, animation, "Hi I'm Dora") | **5** | COVERAGE_GAPS A-3 |
| **Help content overhaul** (per-feature, FAQ, diagrams) | **5** | COVERAGE_GAPS A-4 |
| **Settings deferred** (theme type/identity split, profile picture) | **2** | COVERAGE_GAPS A-5 |
| **Cross-cutting Bucket C** (telemetry, full-QA doc, UI polish pass, ALDI/IGA logos, P2P sync, push notifs between users, gamification, main-menu border) | **~9** | COVERAGE_GAPS C |
| **Login/forgot misc** (sponsorship button, button centring nuances) | ~3 | uncovered |
| **Stocktake mode UX** (deeper redesign) | ~4 | uncovered |
| **Recipe Detail / Product History minor** | ~6 | uncovered |

**The single biggest no-plan cluster: Stock Item Detail polish (16 bullets).** That's a whole user-facing surface with zero design coverage. **Next biggest: Data page (8 bullets).** Both deserve their own Wave-C brief.

---

## Part 3 — The honest read

**You are not blind to progress — but the headline number is misleading either way you slice it.**

- "35% shipped" sounds low but is **front-loaded on the loop surfaces** (Cookbook 79%, Cook Mode 84%, Shopping Lists 100%, Stock Overview 78%). Those are the surfaces a user touches every day. The loop is real.
- "65% not shipped" is also misleading — most of that is **Meal Plans** (45 bullets) and the **scraper-companion seam** (22 bullets), both of which are deliberately gated behind Phase 2/3 in the master plan. You are NOT behind on them; they are scheduled to come later.
- The genuinely concerning gap is the **NO_HOME 19%** — and within that, the **Stock Item Detail polish (16 bullets)** is the single biggest unsurfaced piece of design work. A Stock Item Detail brief (call it C-1b) would close ~5% of the entire backlog in one stroke.

### Recommended next moves (in priority order)

1. **Drain the 18-FU browser-verify queue** in one focused smoke session — this converts ~15% of "shipped but unverified" into "shipped and locked".
2. **Write the C-1b Stock Item Detail brief** — closes the biggest NO_HOME cluster.
3. **Start the Meal Plans impl plan** (C-2 → IMPL_PLAN_MEAL_PLANS) — the biggest designed-but-unbuilt block. This is your largest single lever on the SHIPPED %.
4. **OR** start Phase 2 ingestion API (different shape — net-new feature, unlocks Phase 3 champion features).
5. **Re-baseline STATUS.md** — overdue; not on the critical path but cheap.

Full per-bullet detail (every one of the 309 with status + home/evidence) is in [docs/99_scratch/FEEDBACK_AUDIT_2026-06-12.md](FEEDBACK_AUDIT_2026-06-12.md).
