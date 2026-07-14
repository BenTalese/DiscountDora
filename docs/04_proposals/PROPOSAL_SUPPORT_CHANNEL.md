# Dashy Dora — Support & feedback channel → `PROPOSAL_SUPPORT_CHANNEL.md`

**Type:** 🟠 action plan — mixes out-of-app operator steps + a small code change.

> **Status: ➗ BUILT (dormant) 2026-07-14 — FU-370.** The code half below shipped,
> **off by default** (no affordance renders until a channel is configured), with
> **one deliberate, settled divergence directed by the project owner:** the two
> `AppSetting` columns + migration + admin editor in §4.1/§4.2 were **NOT built and
> never will be.** Owner directive: *"I wouldn't want this to be controllable by
> admins ever, this is something I control only."* So the support target is a
> hardcoded commit-and-done switch + env override in
> `dora_api/features/support/support_channel.py`. This is **out of R-030's scope by
> design** (R-030 governs *admin-tweakable* operational config; this is
> author/deploy-controlled and off-limits to household admins) — not a carve-out
> awaiting promotion. Settled in **FU-558** (resolved). Everything else in §4.3–§4.5
> shipped as written (health block, `useSupportChannel`, HelpPage button + copy,
> `PageErrorState` wiring, DoraBot intent). **Standing up the actual channel +
> setting the target is FU-557** (the out-of-app §6 action list). **Open decisions
> — closed:** the §3 channel fork is deferred to FU-557 (owner chose "decide later;
> ship dormant + channel-agnostic"); §4.1/§4.2 (AppSetting/admin editor) are
> **withdrawn**, not deferred; no live forks remain.

**Origin.** Follow-on to FU-146 (GitHub-issues sweep after the repo went
private). That sweep removed every dead link but left the app with no
in-product way for a user to reach anyone. The Help-page copy now reads:
> *"Found a bug or want a feature? Note the steps you took and what you
> expected, and pass it to whoever runs this Dora instance."*

That's functional but passive-aggressive: it puts the burden on the user
to figure out who "whoever runs this Dora instance" is, sets no
expectations, and reads like *software dumped, your problem*.

**The core insight.** This is a **communication problem, not a support-
infrastructure problem.** The developer is one person, side project, no
SLA. Any in-app inbox / feedback queue would rot silently. What actually
fixes the perception is:

1. **Say the honest thing, once, in the Help page.** "One person, side
   project, best-effort, I read everything."
2. **Give exactly one channel** the operator will actually read.
3. **Wire it minimally in-app** so the button is one click from every
   surface that plausibly needs it.

Everything below is that plan.

**Charter check.** Effortless + Anti-creep. Zero background jobs, no new
tables, no queue-that-never-drains. Two AppSettings + one banner-of-copy
+ two buttons that render only when configured. Off by default (matches
the C-cross "gone, not greyed" posture per R-014).

---

## 1. The current state (grounded in code)

- [`HelpPage.vue`](web_app/src/pages/HelpPage.vue) — guides + changelog
  + version check. A **"Meet DoraBot"** button up top. **No "Report an
  issue" button.** The About tab ends with the passive-aggressive
  paragraph quoted above.
- [`PageErrorState.vue`](web_app/src/components/PageErrorState.vue) —
  the error-boundary component still accepts a `showReport` prop, but
  the button never renders because nothing sets `reportUrl` (FU-146
  retired that path).
- **DoraBot `report_issue` intent** — still there in the assistant, but
  now navigates the user to `/help` instead of an external tracker.
- **Backend:** no `SupportRequest` table, no feedback endpoints,
  nothing.
- **AppSettings:** none for support.

**Net:** the surface is stubbed for a "Report" affordance that the code
knows how to render, but nothing points at anywhere real, so the button
never appears. This proposal makes it appear when — and only when —
the operator has actually set something up.

---

## 2. What NOT to build

Deliberately-rejected shapes:

- **In-app inbox / `SupportRequest` table + admin Feedback page.**
  Every unread count becomes a source of guilt. A solo dev is not going
  to reliably drain it. Building infrastructure you can't maintain is
  worse than having none.
- **DoraBot "help me write a bug report" flow.** Adds token cost + a
  layer of indirection between the user and the report. Users know how
  to say "the button doesn't work."
- **Multi-tier "priority support" language.** There is one tier: it's
  best-effort. Pretending otherwise sets expectations that will get
  broken.
- **An SLA, uptime commitment, or 24/7 language anywhere in the copy.**
- **A live-chat widget.** No.
- **A public GitHub Discussions on the private repo.** GitHub
  Discussions inherits repo visibility — private repo = only invitees
  see it. Doesn't solve the discoverability half of the problem.

---

## 3. Pick a channel (out-of-app decision)

The three that actually make sense for a solo hobby-scale dev:

### Option A — Public "issues-only" GitHub repo (**recommended**)
Create a **second, public** repo — e.g. `dashy-dora-issues` — whose only
purpose is holding an issue tracker. Code stays private in the existing
repo; issues stay public in the new one.

**Pros:**
- Users get the familiar GitHub Issues shape: search-before-filing,
  labels, threads, notifications, links to specific commits/releases
  once you PR-close them.
- Zero infra cost. GitHub does the hosting.
- Existing DoraBot `report_issue` intent maps to it cleanly.
- Public log of known-issues gives new users confidence the project is
  alive.

**Cons:**
- Requires the reporter to have a GitHub account (small barrier for
  non-technical household users, non-issue for self-hosters).
- You have to reply *somewhere visible*. That's a plus for
  accountability, a minus for "I'm not in the mood today."

### Option B — Hosted form (Tally / Google Form / Notion form)
A single form that drops submissions into an inbox or spreadsheet you
own.

**Pros:**
- No account needed to report.
- Lowest friction for non-technical users.
- Fully private — you triage privately, users don't see the queue.

**Cons:**
- Loses the "public log of known issues" benefit — every reporter
  independently reports the same three papercuts.
- Feels less serious. Google-form-support is fine for "beta signup",
  less fine for "the app I run on my pantry data".
- Yet another SaaS integration to configure.

### Option C — Just your email
An alias like `dora@yourname.com` forwarding to your personal inbox.

**Pros:** most personal, most direct.
**Cons:** worst discoverability (nothing to search); highest cognitive
load on you (every duplicate report costs a reply); no way for another
user to see "yes, that's a known one".

### Recommendation
**Option A.** Best cost/benefit for a solo dev running a project that
looks like it wants to be taken semi-seriously. Fallback: if you don't
want the accountability of public issues, take Option B and be honest
in the Help copy that it's a private submit-and-wait channel.

---

## 4. The code side (small, opt-in)

Two new install-wide `AppSetting` columns, one Help-page copy rewrite,
one button wired into two places. All the plumbing already exists — this
just fills in the last mile.

### 4.1 New AppSettings

Following the pattern established by `product_search_url` (FU-186 —
admin-configurable external URL, blank = feature hidden):

| Column | Type | Default | Notes |
|---|---|---|---|
| `support_url` | `String(500)` | `""` | External URL the "Report an issue" button opens in a new tab. Public issues repo, form, whatever the operator picked. |
| `support_email` | `String(255)` | `""` | Fallback email; if set and `support_url` is blank, the button is a `mailto:` link. |

**Validation:** same shape as `product_search_url` — non-blank
`support_url` must start with `http://` or `https://`; non-blank
`support_email` must contain `@` (cheapest possible check; the browser's
own `mailto:` handling forgives more than we should reject).

**Precedence when both are set:** `support_url` wins (public log ≫
private mailbox). The `mailto:` fallback exists mainly for operators
who *only* want the email path.

### 4.2 Backend touches

- Migration adds both columns to `AppSetting`.
- `AppSetting` entity + `Fields` + table mapping updated.
- `AppSettingsDto` + `_to_dto` in
  [`get_app_settings.py`](dora_api/features/app_settings/get_app_settings.py)
  surface both.
- `UpdateAppSettingsRequest` in
  [`update_app_settings.py`](dora_api/features/app_settings/update_app_settings.py)
  accepts both, validates as above.
- **Health probe:** `/api/health` gains a small `support` block —
  `{url, email}` — so the button can decide whether to render for
  every user, not just admins. Same pattern as `image_policy` (FU-345).
  Empty strings when unset. Non-admin users only need the read.

### 4.3 Frontend touches

- New composable `useSupportChannel` — module-level state, one health
  probe, mirrors `useImagePolicy` / `useScanningEnabled`. Exposes
  `{ url, email, hasChannel }`.
- **HelpPage rewrite** — the About tab's final section becomes the
  copy in §5.
- **HelpPage "Report an issue" button** — sits next to "Meet DoraBot"
  in the page header. Rendered only when `hasChannel` is true.
  Behaviour: prefer `url` (opens in new tab); fall back to `mailto:`
  with a pre-filled subject.
- **PageErrorState** — reuse the existing (unwired) `showReport` prop
  path. Pass the same `useSupportChannel` value; render only when
  channel exists.
- **DoraBot `report_issue` intent** — surface the URL/email in the
  reply rather than just navigating to `/help`.
- **Admin editor** — the "Report / support" pair lands on **Settings →
  Admin → System → Features** (same page that hosts
  `product_search_url`, so the "external URLs Dora points at" story is
  in one place). Two text inputs, save, done.

### 4.4 Pre-fill contract

When the button opens a `mailto:` link, pre-fill:
```
subject: [Dora] Bug — v{version} on {current_path}
body:    "\n\n---\nDora {version} | {schema_version} | {profile}"
```
When it opens a URL, append `?title={encoded subject}&body={encoded body}`.
GitHub Issues honours these query params; Tally / Google Forms
ignore them (fine — no harm done).

### 4.5 What stays exactly as it is

- The private code repo. Not renamed, not made public.
- The DoraBot fallback bank — it already reads well post-FU-146.
- The AboutSettings page — no repo links to restore.
- The `showReport` prop on `PageErrorState` — kept its wiring; this
  proposal is just what it finally points at.

---

## 5. The copy

The block on the Help page (or wherever the support block ends up).
Replace the existing "pass it to whoever runs this Dora instance"
paragraph with this. Rewrite in your own voice before shipping — the
draft below is a template, not a finished string.

> **Getting help & reporting issues**
>
> Dashy Dora is built by one person as a side project. Bug reports and
> feature requests are welcome, and I read every one — but replies can
> take days or weeks. There's no on-call, no SLA, and no support team;
> just me, doing this in evenings and weekends.
>
> If a family member set up this Dora for you, ask them first — most
> problems are quicker to solve locally than through me.
>
> Otherwise, use the **Report an issue** button above. Before filing,
> note the steps you took, what you expected, and what happened
> instead. Screenshots help.
>
> Thanks for using it. This project only exists because a handful of
> people find it useful.

**Copy notes:**
- "One person / side project" — set the expectation up front. Loses
  nothing; buys enormous goodwill.
- "Ask them first" — deliberately routes the household case away from
  you. Non-technical users don't need to touch GitHub to get help.
- "Weeks" — err on the side of *longer*. If you reply the same day
  it's a happy surprise; if the copy said "24 hours" and you didn't,
  that's a broken promise.
- No apology theatre. No "we're sorry for the inconvenience". Honest
  and matter-of-fact reads better than deferential.

---

## 6. Action list (concrete, in order)

**Out-of-app (yours — do these first):**
1. Decide channel — recommendation is Option A (public issues repo).
2. If Option A:
   - Create `dashy-dora-issues` (or similar) as a **public** GitHub
     repo.
   - Add one issue template — `bug_report.yml` — with fields for:
     what you did, what you expected, what happened, Dora version,
     browser + OS. Keep it short; long templates suppress reports.
   - Add a `README.md` that says "this is the public issue tracker
     for [Dashy Dora](link-to-project-page-or-just-a-blurb). Code is
     private; issues are public."
   - Optionally: enable Discussions on this repo too, for
     Q&A-shaped things that aren't bugs.
   - Grab the "new issue" URL (e.g.
     `https://github.com/<you>/dashy-dora-issues/issues/new?template=bug_report.yml`).
3. If Option B: create the form; grab the URL; decide whether it's the
   `support_url` (opens direct) or lives behind the `support_email`
   (you paste it in an autoresponder). URL is cleaner.
4. Decide the email fallback address if any. Optional.
5. Rewrite the copy in §5 in your voice.

**In-app (code — one focused FU when you're ready):**
6. Migration + AppSetting columns.
7. Entity / DTO / update-request wiring.
8. `/api/health.support` block.
9. `useSupportChannel` composable.
10. HelpPage: header button + copy rewrite.
11. PageErrorState: wire the existing `showReport` prop.
12. DoraBot `report_issue` intent: surface the channel in the reply.
13. Admin editor on Settings → Admin → System → Features.
14. Set the two AppSettings via the admin UI. Ship.

**Follow-ups (not blockers):**
- If Option A: link the public issues repo from your personal site /
  README / wherever else external users find the project.
- Consider a `/help/status` page later — one line "last release: <date>
  / open issues: N / read every one" — if you ever want a lightweight
  "yes this is alive" signal. Not this FU.

---

## 7. Alternatives considered

Documented so the next re-open of this question doesn't re-invent them.

| Alternative | Why not |
|---|---|
| In-app `SupportRequest` table + inbox at Settings → Admin → Feedback | Queue-you-can't-drain problem. See §2. |
| GitHub Discussions on the private repo | Discussions inherit repo visibility. Private = invitees only. |
| Making the main repo public | Bigger decision — not this proposal's scope. Would obsolete Option A but not the copy work. |
| Multi-channel (email + form + repo) | Discoverability > flexibility. One place. |
| Live chat / Intercom-style widget | See §2. Absolutely not. |
| Requiring users to log in to see support info | The Help page is authenticated anyway (the router guards `/help`). Non-issue. |
| Pre-filling the reporter's username in the mailto/URL | Would leak `currentUser.email` into `mailto:` clients. Cheap-looking privacy risk; not worth it. Users can identify themselves in the body if they want. |

---

## 8. Coverage — feedback bullets that motivated this

This is cross-cutting work, not per-surface. The one bullet that
motivated it:

| Bullet | Source | Where addressed |
|---|---|---|
| "should remove any mention of github issues as the repo is now private" | FU-085 browser-verify → FU-146 | Closed the *removal* half; this proposal closes the *what-goes-there-instead* half. §3–§5 pick the new channel and rewrite the copy. |

No other feedback bullets touch the support/reporting surface. If more
land later, they attach to whichever section they fit.

---

## 9. Recommended resolution point

**Ship when:** you've picked a channel (Option A / B / C in §3), stood
it up out-of-app, and are ready to point people at it. The code half
(§4) is small and can land in one FU-scoped PR once the URL exists —
before that it has nothing to point at.

**Blocker check:** none — this is orthogonal to every other open FU.
Depends only on the `AppSetting` + `/api/health` patterns already in
place (FU-186 + FU-345 respectively).

**Effort:** ~2–4 hours of code once the channel exists. The rest is
your choice + your writing.
