# Security Findings: Auth & Dora Assistant

**Status:** Draft for discussion
**Date:** 2026-06-04
**Scope:** Security review of the auth domain and the LLM-powered Dora assistant, **scoped to the current single-tenant design** (one shared household per install — see `MULTI_USER_READINESS.md` for what changes at multi-user). Severities here assume single-tenant; several rise sharply post-multi-user, flagged inline.

---

## 0. Posture summary

Fundamentals are good. This is **not** a leaky codebase — the worrying-on-paper findings were checked against the code and several were downgraded:

- The assistant **cannot silently mutate data** — verified server-side gate (§B.0).
- There is **no cross-user data leak** — single-tenant by design; no per-user data exists to leak.
- Auth tokens, hashing, and anti-enumeration are done correctly.

The genuine issues are CSRF, an inconsistent email-change flow, prompt-injection-via-scraped-data, and missing abuse controls on the assistant. None are five-alarm fires single-tenant; the first two are worth fixing now because they enable account takeover and get worse at scale.

---

## A. Auth

### A.0 What's correct (don't touch)
- Password hashing via werkzeug (bcrypt-family).
- Reset / verify / email-change tokens: random, single-use, **SHA-256-hashed at rest**, expiring (1h / 24h), constant-time compared (`auth_helpers.py`).
- Anti-enumeration: forgot-password and resend-verification return **204 regardless** of whether the email exists.
- Login rate-limiting exists (per-IP).
- Sessions are signed HTTP-only cookies; password change invalidates other sessions via a `password_changed_at` staleness check (`get_me.py`, `change_password.py`).

### A.1 CSRF on state-changing endpoints — **HIGH** (worst auth issue)
Flask session cookie with `SameSite=Lax` and **no CSRF token**. `SameSite=Lax` permits top-level cross-site navigations, so a malicious page could drive a state-changing request (e.g. `POST /auth/me/email`) against a logged-in user.
- **Impact:** change the victim's email → lock them out of password recovery → account takeover.
- **Fix:** add a CSRF token to all state-changing endpoints, or set the session cookie `SameSite=Strict` (acceptable for an app with no cross-site entry flows), plus an `Origin`/`Referer` check on mutations.
- **Multi-user:** severity rises — a lever against any account in a larger base.

### A.2 Email change requires no password proof — **MEDIUM**
`request_email_change` only requires a valid session (`email_flows.py:260`), while `change_password` correctly requires the current password (`change_password.py`). Inconsistent: the lower-friction path is the more dangerous one (email controls recovery).
- **Fix:** require current-password re-entry to change email; additionally notify the *old* address that a change was requested, so the legitimate owner can react.

### A.3 Email-change UI doesn't exist — **MEDIUM (half-shipped)**
The backend endpoints exist; `AccountSettings.vue` exposes no UI for them. The feature is implemented server-side and unreachable client-side. Either finish it (with A.2's password proof) or remove the dead endpoints.

### A.4 Client/server password rules drift — **LOW**
Client validates **≥4 chars** on registration (`LoginPage.vue`); server requires **≥10** plus composition (`auth_helpers.py`). User passes client validation, then gets a server error.
- **Fix:** mirror the server rule on the client. (This is the same client/server-logic-drift disease documented in `STATE_OWNERSHIP_REFACTOR_PROPOSAL.md` — a single shared rule source is the real cure.)

### A.5 Admin password reset returns plaintext in the response — **LOW**
`reset_user_password.py` returns the new password in the HTTP body for the admin to relay out-of-band. Pragmatic given SMTP isn't guaranteed, but it lands in logs / browser history / clipboard.
- **Fix:** mark single-use + force-change-on-next-login (likely already single-use); ensure the response isn't logged; consider a one-time link instead of a plaintext value.

### A.6 Rate limiting is in-memory, per-process — **LOW (single box) / HIGH (scaled)**
`auth_helpers.py` buckets per-IP in process memory. One instance: fine. Multiple instances: the limit multiplies per process.
- **Fix:** move to a shared store (Redis/db) if/when horizontally scaled.

### A.7 Tokens in URL query strings — **LOW**
Reset/verify tokens travel as `?token=` (browser history, referer, logs). Single-use + short expiry bound the window.
- **Fix:** acceptable as-is given mitigations; if hardening, POST the token from the landing page instead.

---

## B. Dora assistant

### B.0 What's correct — the mutation gate (the thing most LLM apps get wrong)
Verified at `ask_assistant.py:187-190`: when the LLM emits an **action** tool call, the loop **short-circuits and returns a proposal** — it does *not* execute. The actual write happens only via a separate, user-confirmed `/confirm` call, and `confirm_actions.py` re-validates the payload at commit. **The LLM cannot mutate data on its own.** This is the single most important property for an action-taking assistant, and it's implemented correctly. Preserve it through any refactor.

### B.1 Prompt injection via tool results — **MEDIUM (defanged, not eliminated)**
Tool results are serialized straight into the LLM context: `json.dumps(rows)` appended as a `tool` message (`ask_assistant.py:195-198`). Those rows contain free-text fields (names, descriptions). An injected instruction in that text could steer the model.
- **Why it's only MEDIUM:** because of B.0, injection **cannot cause a silent write** — the worst it achieves is generating a *proposal card the user must approve*, or producing a misleading text answer.
- **The non-obvious vector:** single-tenant means user-authored content is self-inflicted. The real external surface is **scraped merchant product data** (names/descriptions from `merchant_api`) flowing into tool results — data the user didn't author and can't fully trust.
- **Fix:** delimit/escape untrusted fields in tool results; instruct the model that `tool` content is data, not instructions; consider stripping control characters/newlines from scraped fields at ingest.

### B.2 No rate limit / token cap on `/assistant/ask` — **MEDIUM**
Only guards are a 3-round tool loop (`_MAX_TOOL_ROUNDS = 3`) and a 60s per-call timeout (`ollama_client.py`, `stream=False`). No per-user request rate limit, no input-size or cumulative-token cap.
- **Why not higher:** self-hosted Ollama means no cloud bill; blast radius is local compute exhaustion.
- **Fix:** per-user/session rate limit on the assistant endpoints; cap input context size; keep the loop cap.

### B.3 Tool arguments not bounds-checked — **LOW-MEDIUM**
LLM-supplied args reach handlers with minimal validation — e.g. `int(args.get("days"))` with no range check (`confirm_actions.py`), `push_expiry` with no cap on distance. SQLAlchemy parameterization prevents SQL injection, but semantic nonsense (negative/huge values) isn't rejected.
- **Mitigated by B.0:** these still pass through user confirmation. Still worth validating server-side at the tool boundary.

### B.4 `current_path` concatenated into the system prompt — **LOW**
`ask_assistant.py:158-159` appends the user's current route into the prompt unescaped. Normally a constrained route value, but naive concatenation is a minor injection seam.
- **Fix:** validate against known routes or escape before embedding.

---

## C. Priority order

| # | Finding | Severity (single-tenant) | Fix effort |
|---|---|---|---|
| 1 | A.1 CSRF on mutations | High | Medium |
| 2 | A.2 Email change w/o password proof | Medium | Low |
| 3 | B.1 Injection via scraped tool-result data | Medium | Low-Med |
| 4 | B.2 No assistant rate/token caps | Medium | Low |
| 5 | A.3 Email-change UI half-shipped | Medium | Low |
| 6 | B.3 Tool-arg bounds | Low-Med | Low |
| 7 | A.4 Password-rule drift | Low | Low |
| 8 | A.5 / A.6 / A.7 / B.4 | Low | Low |

**Do first:** A.1 + A.2 (together they close the account-takeover path) and B.1 + B.2 (cheap, and B.1's scraped-data vector is the one genuinely-external injection seam).

---

## D. Note on tenancy

Several severities above are explicitly single-tenant. The companion `MULTI_USER_READINESS.md` covers what changes when multi-user ships — in short, A.1/A.2 escalate and entirely new isolation requirements appear. Don't treat "secure today" as "secure after multi-user."
