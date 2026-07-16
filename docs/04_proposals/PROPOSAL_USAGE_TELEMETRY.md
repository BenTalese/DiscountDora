# Proposal — Usage telemetry / product analytics (privacy-first)

**Status:** 📦 **parked → hosted-only (2026-07-16, owner).** Design-only; no code, and
**none planned for self-host.** Governed by
[`OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md`](OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md).
Origin: FU-363 item 2. Build FU **FU-566 resolved WON'T-DO (self-host).**

> **Decision (2026-07-16, owner): don't build any of this for self-host; migrate the
> whole topic into the optional SaaS plan.** The motivating ask ("know how people use
> my app") is the *maintainer's* — it only pays off as **hosted, cross-install
> aggregate** analytics (Surface B). The self-host **"efficiency lens" (Surface A) was
> designed below, stress-tested, and dropped**: on a self-host box the reader is the
> household *operator*, whose real questions are outcomes (pantry accuracy, waste,
> spend) not feature-engagement — and most of those are already answerable from
> existing domain data without a telemetry system. So there's no useful self-host
> product here. The design below is **retained for the record / re-open value** if a
> hosted offering is ever built; the live home is the SaaS doc's "Product analytics
> (hosted-only)" bucket. **Everything from §3 down is historical**, not a plan.

**Motivating feedback (06-Jun-2026):**
> *"I'd like a way to know how people are using my app. I know some companies
> track where their users go and what they do (e.g. which features get hit the
> most)."*

**Owner reframe (2026-07-16):** the valuable product here isn't a usage dashboard —
it's an **efficiency lens** shown to the *admin of an install*, framed around getting
more out of the app. Underneath it's the same usage-event collection; the difference
is entirely in how it's *interpreted and delivered*: "you'd do this faster this way,"
"this install uses only 5 of Dora's features," "your least-used feature is X,"
"cook-mode use is up 3× this month." All **system-wide** (about the install, never an
individual user). **Off by default, opt-in by the admin.** On self-host
it is **strictly local admin reporting** — nothing egresses. The traditional
"share my usage data to improve the app" checkbox is a *hosted-only* flavour (Surface
B, §4), added in the optional SaaS plan — never on self-host.

---

## 1. The tension this must resolve

The ask is legitimate — a solo maintainer wants to know which features earn their
keep. But it collides head-on with two charter principles, so it cannot be built
the "some companies" way:

- **P8 — Ownership & privacy.** "The user's data is theirs — no ads, never sold;
  local-first / BYO where possible; anything external is opt-in and documented."
- **P10 — Anti-feature-creep.** "Niche features default OFF."

And with the distribution posture (§7.5): the product is self-hostable, so there is
**no central server every install already talks to**. Adding a mandatory phone-home
would (a) leak usage off the user's box, (b) require the author to run + secure a
collection endpoint, and (c) turn a local-first app into one that watches its users
— exactly the "your data becomes the product" pattern the champion plan's tagline
(line 120) rejects.

**Hard nos, up front:**
- **No third-party analytics SaaS** (Google Analytics, Mixpanel, Segment, Amplitude,
  etc.). Embedding any of them ships user behaviour to a third party — a flat P8
  violation, and a legal-exposure surface (consent banners, DPAs) the app has
  deliberately avoided elsewhere (cf. Decision 1, the crowd-price cut FU-436).
- **No content, ever.** Telemetry may record *that* a feature was used, never *what*
  was in it. No item names, list contents, prices, recipe text, free-text, or user
  identifiers.
- **Off by default.** Any egress is opt-in per install, documented, and reversible.

## 2. The two things "telemetry" actually means here — keep them separate

The feedback bundles two different needs that have different privacy shapes:

| | **A. Local usage insight** | **B. Aggregate product analytics** |
|---|---|---|
| Question it answers | "On *this* install, what gets used?" | "Across *all* installs, what gets used?" |
| Data leaves the box? | **No** — stays in the local DB | **Yes** — opt-in egress to an author-run collector |
| Who sees it | The install's operator | The maintainer |
| Privacy shape | Trivial — never leaves | Sensitive — must be anonymous + aggregate + opt-in |
| Charter fit | Clean (local-first) | Needs the full opt-in/anonymise treatment |

**Recommendation: build A first (opt-in per install, admin-enabled, off by default);
make B a deferred, hosted-only add-on that reuses A's event store.** A is the
self-host product — an efficiency lens the operator turns on for their *own* install;
it never egresses, and it de-risks B by proving the event taxonomy before any data
egress exists. A is opt-in (not "unconditional") because it's a distinct feature that
collects usage — the admin should choose it on, per P8/P10.

## 3. Surface A — the efficiency lens (self-host core; opt-in, admin-only, local)

**The reframe.** Surface A is not a stats dashboard — the raw counts are just the
substrate. What the admin sees is an **interpreted, actionable lens** over their own
install: usage data turned into **efficiency coaching**, framed as "here's how to get
more out of Dora / do this faster," never as surveillance. Same collection underneath
as the telemetry originally described; the value is entirely in the presentation.

Two layers:

**Layer 1 — collection (the event substrate).** Feature surfaces emit a tiny named
event from a committed enum registry (`event_key`, e.g. `stock.added_manual`,
`stock.added_scan`, `cook_mode.started`, `list.generated_from_plan`,
`oracle.verdict_requested`); the server records it locally. Runs **only** when the
admin has enabled the lens (off by default). (R-003: the server owns the counters;
the client only fires the event name.)

**Layer 2 — the lens (the product).** A small, curated set of **insight rules** read
the local store and emit plain-language, ranked findings in a digestible format — a
handful of "tips," not a wall of charts. All insights are **system-wide** (about the
install, not any individual user). The kinds of insight (catalogue in §3.2):
- "You log stock by hand a lot — barcode scan is faster here." *(do-this-faster)*
- "This install uses only 5 of Dora's ~40 features." *(adoption)*
- "Your least-used feature is Product History — hide it, or here's what it's for." *(prune-or-learn)*
- "Cook-mode use is up 3× this month." *(trend)*

**Event taxonomy:** a small, curated, **enum-like registry** of event keys (committed
constant, not free-form strings) so the set is auditable at a glance and can't
silently sprawl (P10). Start with ~20–30 keys covering the headline flows (stock
add-by-hand vs add-by-scan, cook mode, meal-plan generate, list generate, oracle
verdict, barcode scan, import, dashboard load). Grow deliberately.

### 3.1 Data model — deliberately minimal (system-wide counts only)

One narrow table, **pre-aggregated at write**:
`usage_event_daily(event_key TEXT, day DATE, count INT)` — no `user_id`, no per-action
row, no timestamp precision, no sequence. It is *structurally* incapable of storing
behavioural detail: you can't data-mine a user, a session, or an order of actions
because none of that is ever recorded. This is the privacy guarantee baked into the
schema, not bolted on as policy — and it's cheap because the lens is deliberately
kept simple.

**Two things intentionally cut (2026-07-16, owner — don't over-engineer):**
- **Per-user attribution** ("this user uses 5%") — dropped. All insights are
  **system-wide** (about the install). Avoids the more sensitive per-user dimension
  entirely and keeps the schema above.
- **Order/flow advice** ("sub-optimal order") — dropped. It would need some notion of
  sequence, which the daily-count schema can't (and now won't) see. Its slot in the
  catalogue is taken by a plain **trend** stat (rising/falling feature use over time),
  which is pure daily-count math.

The **no-content** rule remains absolute (event *names* only), and **nothing about
Surface A ever egresses on self-host**.

### 3.2 Candidate insight catalogue (the "what's most useful" question)

The design work the owner named — *defining the most useful info and how to deliver it
digestibly.* A starter menu, grouped by intent (curated + auditable like the event
registry; grow deliberately):

| Intent | Example insight | Needs |
|---|---|---|
| **Do-this-faster** | "You add stock by hand often — scanning is faster" | feature-substitution rules |
| **Adoption** | "This install uses 5 of ~40 features; here are 3 you might like" | install-wide coverage |
| **Prune** | "Least-used: Product History — hide it or learn what it's for" | install-wide counts |
| **Trend** | "Cook-mode use is up 3× this month" | daily-count deltas |
| **Habit/cadence** | "No stocktake in 6 weeks — your pantry may be drifting" | coarse last-used |
| **Health** | "Cook mode used but consumption rarely logged — pantry drifts from reality" | cross-feature counts |

**Delivery format:** a compact **"Insights"** section at the top of Settings → Admin →
**Usage** — a few ranked, dismissible tips in prose, each with a one-tap link to the
relevant feature. Not a BI dashboard. The raw counts stay available underneath for the
curious, but the *headline* is the coaching. (This mirrors the app's existing
alert/nudge idiom rather than inventing a charts surface.)

## 4. Surface B — Aggregate product analytics (hosted-only, opt-in "share to improve")

**On self-host, Surface B does not exist** — usage never leaves the operator's box
(§3). Surface B is the **hosted** shape: in the optional SaaS/managed plan, present the
familiar **"Share my usage data to help improve Dora" checkbox** (default **OFF**),
which opts a hosted install into sending Surface A's *aggregates only* to the author.
This is the one place the traditional-telemetry framing is appropriate, and it's gated
to the hosted context. Cross-ref
[`OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md`](OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md).
Build it only if A proves insufficient for the "across installs" question. Shape:

- **Opt-in toggle** in Settings → Admin (default **OFF**), with plain-language copy
  stating exactly what is sent and to whom, and a link to a short public
  data-statement. Mirrors the existing opt-in posture (config/opt-ins framework).
- **Payload = A's daily aggregates only**, plus a coarse install fingerprint that is
  *not* a stable identity: app version, and a **rotating** random install token (or
  no token at all — a pure anonymous count POST). No IP retention, no PII, no content.
- **Collector = author-run, self-hostable, minimal.** A single endpoint that appends
  `{version, event_key, day, count}`. **Not** a third-party SaaS. If a hosted
  privacy-first tool is ever used, it must be self-hosted (e.g. Plausible/PostHog on
  the author's own infra) and still fed only aggregates — but rolling a 50-line
  collector is lower-risk than operating another service (cf. the FU-370 "a queue you
  can't drain is worse than none" reasoning).
- **k-anonymity floor:** the maintainer-facing view suppresses any bucket below a
  small install-count threshold, so a rarely-used feature on a handful of installs
  can't single anyone out (the small-cohort re-identification blocker that helped
  sink crowd prices, FU-436 — respected here by only ever showing aggregates above a
  floor).

## 5. What NOT to build

- No session recording, no funnels, no per-user journeys, no cohort/retention
  dashboards, **no per-user attribution**. That is the "some companies" surveillance
  shape P8 rejects — and it is overkill for a solo maintainer who needs "which
  features get hit most", not a growth-analytics suite (P10). The efficiency lens is
  **system-wide only** — every insight is about the install, never an individual user.
- No client-side beacons to any external domain from the SPA.
- No telemetry in the shared **demo** beyond Surface A's local counters (the demo is
  single-dataset per FU-555; its counts are fine to read locally, never to attribute).

## 6. Rollout shape (when built)

1. **Admin opt-in toggle** (Settings → Admin, default OFF) that gates all collection.
2. Event registry + `usage_event_daily(event_key, day, count)` table + a
   `record_event(key)` server seam (no-ops unless the toggle is on).
3. Instrument the ~20–30 headline surfaces to fire keys (thin, one line each),
   including the paired do-it-by-hand vs do-it-the-fast-way events the lens compares.
4. **Insight-rule engine** — a small curated ruleset (§3.2) that reads the daily counts
   and produces ranked plain-language, system-wide tips.
5. Settings → Admin → **Usage** panel: **Insights** section on top (the lens),
   raw counts underneath; operator-only (hidden for non-admins, R-029 — gone-not-greyed).
6. *(Hosted-only, deferred, gated)* Surface B "share to improve" checkbox + collector +
   k-anon view — SaaS plan only, never self-host.

Steps 1–5 are the self-contained self-host unit (FU-566). Step 6 is hosted-only and
waits on §7 sign-off + the OPTIONAL_SAAS revisit.

## 7. Open decisions — closed

Per the proposal close-out rule, every fork is resolved inline or spawned as an FU:

1. **Build A now, or wait?** → *Answered:* A is charter-clean and useful for
   dogfooding; it is buildable whenever it's prioritised. No blocker. (Not scheduled
   here — it competes with the rest of the backlog like any other unit.)
2. **Build B at all?** → *Answered (recommendation):* only if A proves insufficient.
   B introduces the app's **first-ever outbound behavioural egress**, so it must not
   be built without explicit owner sign-off on the payload + collector + opt-in copy.
   → **Spawned as a build-gate follow-up** (`DORA_FOLLOWUPS.md`) with recommended
   resolution "when the across-installs question becomes real, and only after owner
   signs off on §4."
3. **Collector: roll-your-own vs. self-hosted Plausible/PostHog?** → *Answered:*
   default to a minimal roll-your-own append endpoint; a self-hosted privacy-first
   tool is an acceptable substitute but a third-party SaaS is never acceptable. Final
   pick rides with the item-2 build-gate FU (only relevant if B is built).
4. **Per-user attribution (needed for "this user uses 5%")?** → *Decided (owner,
   2026-07-16): CUT.* All insights are system-wide (about the install). No `user_id`
   dimension; schema stays `usage_event_daily(event_key, day, count)`. Simpler and
   avoids the most sensitive data shape entirely.
5. **Order/flow advice ("sub-optimal order")?** → *Decided (owner, 2026-07-16): CUT*
   to avoid over-engineering. Its catalogue slot is a plain **trend** stat instead
   (rising/falling feature use, pure daily-count math — no sequence stored).

*(Sweep confirmation: 1 & 3 answered inline; 2 spawned as an FU; 4 & 5 decided (cut) —
no undecided fork left.)*

## 8. Feedback coverage

This is cross-cutting (Wave-A shape), so the table maps the **motivating bullet(s)**,
not every app-wide bullet (per the CLAUDE.md cross-check rule).

| Feedback bullet (06-Jun-2026) | Covered by | Notes |
|---|---|---|
| *"I'd like a way to know how people are using my app … which features get hit the most."* | §3 (Surface A, local) + §4 (Surface B, opt-in aggregate) | Split into local-insight (unconditional) + opt-in cross-install analytics; "which features hit most" is exactly Surface A's top-keys view. |

No other 06-Jun bullet targets telemetry. The adjacent *"gamify the app"* idea
(same feedback file, NEW FEATURE IDEAS) is **out of scope** here — it's a separate
someday item (§7 champion plan defers gamification), not analytics.

## 9. From the original spec

`docs/00_original_spec/` (author's pre-~100k-LOC first spec) contains **no telemetry
/ analytics Feature Board or Feature Note** — the local-first framing meant usage
tracking was never specced. Nothing to extract; this proposal is the first design of
the surface. (Checked 2026-07-15.)
