# Proposal — Usage telemetry / product analytics (privacy-first)

**Status:** 🔵 designed, not built (2026-07-15). Design-only; no code. Build is
**gated on owner sign-off** of §7 (see the build-gate follow-up spawned there).
Origin: FU-363 item 2 (split out of the Bucket-C cross-cutting bundle when picked up).

**Motivating feedback (06-Jun-2026):**
> *"I'd like a way to know how people are using my app. I know some companies
> track where their users go and what they do (e.g. which features get hit the
> most)."*

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

**Recommendation: build A first and unconditionally; make B a deferred, opt-in
add-on that reuses A's event store.** A satisfies the spirit of the ask for the
maintainer's *own* dogfooding install today with zero privacy cost, and de-risks B
by proving the event taxonomy before any data egress exists.

## 3. Surface A — Local usage insight (recommended core)

**What:** a local-only, append-only event counter. Feature surfaces emit a tiny
named event (`event_key`, e.g. `cook_mode.started`, `list.generated_from_plan`,
`oracle.verdict_requested`); the server increments a per-key, per-day counter row.
An operator-only Settings → Admin → **Usage** panel renders the counts (top features,
7/30-day trend, never-used surfaces).

**Data model (illustrative, not final):** one narrow table
`usage_event_daily(event_key TEXT, day DATE, count INT)` — pre-aggregated at write
time, so there is no per-action row, no timestamp precision, and nothing that can be
tied back to a user or a session. (R-003: the server owns the counter; the client
only fires the event name.)

**Why pre-aggregate at write:** it is structurally incapable of storing behavioural
detail — you *can't* later data-mine a sequence of actions because the sequence was
never recorded. This is the local-first privacy guarantee baked into the schema, not
bolted on as policy.

**Event taxonomy:** a small, curated, **enum-like registry** of event keys
(committed constant, not free-form strings) so the set is auditable at a glance and
can't silently sprawl (P10). Start with ~20–30 keys covering the headline flows
(stock add/check, cook mode, meal-plan generate, list generate, oracle verdict,
barcode scan, import, dashboard load). Grow deliberately.

## 4. Surface B — Aggregate product analytics (deferred, opt-in)

Only if A proves insufficient for the "across installs" question. Shape:

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
  dashboards. That is the "some companies" surveillance shape P8 rejects — and it is
  overkill for a solo maintainer who needs "which features get hit most", not a
  growth-analytics suite (P10).
- No client-side beacons to any external domain from the SPA.
- No telemetry in the shared **demo** beyond Surface A's local counters (the demo is
  single-dataset per FU-555; its counts are fine to read locally, never to attribute).

## 6. Rollout shape (when built)

1. Event registry + `usage_event_daily` table + a `record_event(key)` server seam.
2. Instrument the ~20–30 headline surfaces to fire keys (thin, one line each).
3. Settings → Admin → Usage read panel (operator-only; hidden for non-admins, R-029
   posture — gone-not-greyed for users who can't see it).
4. *(Deferred, gated)* Surface B opt-in toggle + collector + k-anon view.

Steps 1–3 are a self-contained, ship-anytime unit. Step 4 waits on §7 sign-off.

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

*(Sweep confirmation: no live undecided items remain in this block — 1 & 3 answered
inline, 2 spawned as an FU.)*

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
