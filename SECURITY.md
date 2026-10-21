# Security policy

## Reporting a vulnerability

If you believe you've found a security issue in Dashy Dora — a bug that
would let one user read or change another user's data, an admin gate
that can be bypassed, a way to extract stored secrets, a chain that
leads to remote code execution, or anything else with a
confidentiality / integrity / availability impact — please report it
privately rather than opening a public issue.

**Where to send it**

- Email `Ben.Talese@CompanionSystems.com.au` with the subject line
  starting `[dora-security]`.
- If you'd prefer end-to-end encryption or the GitHub Security
  Advisories flow, open a
  [private advisory on this repository](https://github.com/BenTalese/dashy-dora/security/advisories/new).

**What to include** — enough for us to reproduce it:
- Affected area (route, feature, or file path).
- Repro steps or a minimal proof-of-concept.
- Your assessment of the impact.
- Whether you'd like to be credited when the fix ships.

**What to expect back**
- Acknowledgement within **5 working days**.
- A first assessment (accepted / need-more-info / duplicate / out-of-scope)
  within **14 days**.
- Coordinated disclosure once a fix is available — we'll agree a
  release window with you before publishing details.

Please give us a reasonable window (typically **90 days**) to ship a
fix before public disclosure. If we go quiet, ping again — a missed
email is more likely than a deliberate stall.

## Scope

**In scope**
- The Dora backend (`dora_api/`) — auth, session, CSRF, admin gates,
  data-access filters, audit log, upload handling, backup/restore.
- The SPA (`web_app/src/`) — anything that touches auth state, tokens,
  or lets untrusted content escape sanitisation.
- The container image and its default runtime configuration.
- Documented dependencies with a directly-reachable, non-theoretical
  attack path.

**Out of scope**
- Vulnerabilities that require a compromised admin account — Dora
  trusts its admins by design.
- Findings that only apply to a deliberate insecure-development
  configuration (`DORA_ENV=development`, `DORA_CSRF_DISABLED=true`,
  `DORA_DISABLE_SECURITY_HEADERS=1`). These flags exist so operators
  can debug; using them in production is on the operator.
- Denial-of-service via resource exhaustion at network layer.
- Reports from automated scanners without a demonstrated impact.
- Social-engineering, physical, or phishing scenarios.

## Current posture

See `docs/security/SECURITY_REVIEW.md` for the standing audit — what
Dora hardens, what's accepted with rationale, and what's tracked as
follow-up work. If your finding is already covered there, we'll link
you to the row.

## Supported versions

Dora is pre-release at time of writing; there is no long-term-support
line yet. Security fixes ship against `main` and any tagged release
still marked "supported" once tagged releases exist. When we cut a
first stable release the support window will be documented here.
