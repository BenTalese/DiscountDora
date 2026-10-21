# CROWD_PRICES_ASSESSMENT — INV-11

> **⚠ OUTCOME 2026-07-02 — P8-04 CUT.** User decision after this
> assessment: retire the crowd-sourced price graph. Champion order
> becomes `P8-01 → P8-02 → P8-03 → P8-05 → P8-06 → P8-07 → P8-08 →
> P8-09 → P8-10` (P8-04 removed). Landed in
> `RECONCILED_FINISHING_PLAN.md §7` Decision 6 and
> `DASHY_DORA_CHAMPION_PLAN.md` Part V sequencing. Unblocks FU-438
> (P8-06 wait-until). This memo is preserved as the argument trail.

**Date:** 2026-07-02 · **Type:** Read-only, no code changes · One-page memo.
**Question:** FU-436 — should P8-04 (crowd-sourced anonymised price graph) ship
as originally spec'd, ship in a shrunk form, or be cut? Prompted by the user's
feasibility concern at P8-05 kickoff: *"i don't think the logistics of
sharing/pooling community data is feasible for this app. how could it even be
possible?"*

---

## What P8-04 is (as originally spec'd)

From `DASHY_DORA_CHAMPION_PLAN.md:297-324` — an opt-in community price graph.
Users optionally contribute anonymised facts `(item, price, store, coarse
region, date)` to a shared graph; Dora aggregates to community medians/lows
and surfaces "others near you pay ~$X" **only** where the user lacks personal
history. Personal data always wins.

**Rationale in the original spec:** helps new users with no personal history,
and thickens the signal for the wait-or-buy oracle (P8-06). Charter 8
(opt-in privacy-preserving) is explicitly acknowledged.

## The four structural problems

Each is a property of the market or the ops shape, not a design gap:

**1. Privacy.** Even with `(item, price, store, coarse region, date)`
anonymised at the record level, aggregation over small cohorts leaks purchase
behaviour: a region with three contributors becomes a fingerprint. The
"privacy-preserving" claim requires a differential-privacy layer *or* a large
minimum-cohort threshold before any figure surfaces. Both add material ops
complexity: DP noise-calibration + threshold enforcement + a re-identification
audit process. Dora-core has none of this scaffolding.

**2. Incentive / cold-start.** For crowd data to be useful, you need
volume. For volume, you need contributors. Contributors need value back.
Value back needs volume. Classic chicken-and-egg with no distribution
channel to bootstrap — Dora-core has no user base to lean on, and the
companion is deliberately private (Decision 1). A brand-new install
sees an empty graph indefinitely.

**3. Freshness.** Australian grocery pricing rotates weekly per catalogue.
A 7-day-old crowd median for "Coles Full Cream Milk 2L" is describing last
week's promo, not this week's shelf. This isn't a design fix — it's a
property of the market P8-04 is meant to help with. To be useful the graph
would need near-real-time contributions at scale, which returns us to
problem (2).

**4. Ops / brokerage role.** A "central store, opt-in contributions" model
is a data-broker service: uptime, moderation, abuse detection, incident
response, privacy policies, data-processing agreements. This is exactly
the role `RECONCILED_FINISHING_PLAN.md §7 Decision 1` retired when the
scraper was extracted to the private companion. Reintroducing it via
P8-04 walks straight back into what Decision 1 was written to avoid.

## Charter read

- **Charter 4 (personal, not deals):** decisions come from *your* history,
  loyalty, opt-in crowd. Note the "opt-in crowd" clause **allows** it in
  principle — the question is whether Dora-core is the right venue.
- **Charter 8 (opt-in / privacy-preserving):** permits contributions but
  doesn't mandate them.
- **Charter P3 (Honest coarse):** P8-05 shipped with an `unsure/low`
  branch on thin history — that's the honest answer, not a bug crowd data
  should paper over.
- **Charter P10 (Anti-creep):** building a data-broker service is a
  significant expansion of what Dora is. High cost, uncertain payoff.

The champion plan's own P8-06 spec is the tell: line 366 says
> "If crowd data (P8-04) is absent, design to work on personal data alone."

Crowd was scoped as an **optional blend** from day one — not
load-bearing. And P8-05 has now proven the oracle works on pure personal
data with an honest thin-data branch.

## Options weighed

### KEEP — build P8-04 as spec'd
Rebuilds the hosted-broker service pattern Decision 1 retired. Charter
tension is real: legal (privacy policies + DPAs), ops (uptime + abuse
+ incident response), infra ($). Cold-start problem is structural. Even
if all that is solved, the freshness problem (7-day-old catalogues)
caps the useful value at the edge cases where personal data is *newest*
and *most useful* — the same cases where P8-05 already produces a good
answer. **Cost far exceeds payoff.**

### SHRINK — three lighter shapes weighed

- **(a) Static bundled reference.** Ship a JSON table of typical Aus
  prices sourced once (e.g. from a public catalogue snapshot) and
  bundled with the app. No service, no contributions, updates via app
  releases. Cheap to ship. But it substitutes stale reference for
  honest coarseness (Charter P3) — a user in week two of a new install
  gets to real personal signal in ~3 shops; a static baseline mostly
  fills that same window with lower-quality data. Not zero value,
  but small; and it introduces a "typical price" concept the app then
  has to defend and maintain.
- **(b) Peer / local-only mesh.** Two users on a household network
  share observations via a local sync channel. Charter-clean but
  audience is tiny — the "new user, no personal history" case is
  precisely the case where there's no established peer either.
  Doesn't answer the motivating question.
- **(c) Companion-published aggregate.** The private companion
  (which already has an ingestion API) could publish an aggregate
  feed of its own user population's contributions, and Dora consumes
  it as another ingested source. This isn't building a crowd graph —
  it's an optional feature of the companion. Doesn't belong in
  Dora-core's scope.

**None of the three earns its keep at the Dora-core layer.** (a) is
the only one that ships without new infra, and its value is
marginal against P8-05's honest thin-data branch.

### CUT — retire P8-04, no re-litigation
- P8-04 comes off the champion sequence entirely.
- P8-06's spec already covers this (line 366): personal data only.
- Champion order becomes `P8-01 → P8-02 → P8-03 → P8-05 → P8-06 →
  P8-07 → P8-08 → P8-09 → P8-10`.
- Unblocks FU-438 (P8-06 wait-until) which the ledger had held
  pending this decision.
- No code changes: grep for `crowd_baseline` / `community_baseline`
  in `dora_api/` and `web_app/src/` returns zero. The
  `PROPOSAL_BUY_VERDICT_ORACLE.md:183` hedge ("can trivially blend a
  crowd baseline in later") gets updated to reflect the CUT
  resolution.
- Someday-list line in `RECONCILED_FINISHING_PLAN.md:181` ("Crowd
  price graph (P8-04), native app (P8-10) — already in Part 8 but
  post-loop") gets split: P8-10 stays on someday, P8-04 moves to a
  new Decision 6 with the CUT record.

**What CUT loses:** the "brand-new user, first week, no personal
data" experience gets P8-05's honest "not enough history yet" answer
until the user completes ~3 shops. Real, but recoverable within two
weeks of normal use and honest per Charter P3.

## Recommendation: **CUT**

The four problems above are structural, not design failures. The
champion plan already framed crowd data as optional-blend. P8-05
shipped this session working on pure personal data. Decision 1 in the
reconciled plan already retired the hosted-broker role that P8-04
would reintroduce. Nothing about the Dora-core distribution posture
argues for taking that role back on.

What would flip the call: evidence that the empty-first-week
experience drives churn. In its absence, CUT.

---

## Feedback coverage

| User-flagged item | Finding |
|---|---|
| *"i don't think the logistics of sharing/pooling community data is feasible for this app. how could it even be possible?"* (user, 2026-07-02, P8-05 kickoff) | Confirmed — four structural blockers (privacy small-cohort leakage, cold-start chicken/egg, weekly-catalogue freshness cap, hosted-broker ops role reintroduces the pattern §7 Decision 1 retired). **Recommend CUT.** |
