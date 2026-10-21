# Security Findings: Auth & Dora Assistant

**Status:** ✅ Fully triaged (2026-07-08); **delta re-audit confirmed against shipped code 2026-07-13 (FU-409)** — every finding walked item-by-item vs the current tree, all dispositions still hold (nothing reopened). Evidence: A.1 `dora_api/infrastructure/csrf.py`; A.2 `email_flows.py` (`current_password` + `check_password_hash`) + `update_me.py` (`email` forbidden); A.4 `auth_helpers.py::MIN_PASSWORD_LENGTH=8` + `LoginPage.vue`; A.5 `features/users/reset_user_password.py` (still returns `new_password` in body — accepted); A.6 `auth_helpers.py::_buckets` (process-local deque — accepted); A.7 `route.query.token` on Verify/Reset/ConfirmEmailChange pages (accepted); B.0 `ask_assistant.py` `pending_action`/`is_action_tool` gate; B.1 SECURITY block + `_sanitize_tool_output`; B.2 `_ASK_PER_MINUTE=20`/`message max_length=1000`/`_MAX_TOOL_ROUNDS=3`; B.3 `confirm_actions.py::_MAX_EXPIRY_PUSH_DAYS=3650`; B.4 `_safe_current_path` + `current_path max_length=200`. See the per-finding stamps + the §C priority table. **Fixed:** A.1 + A.2 (FU-197), A.3 (FU-197), A.4 (FU-442), B.1 + B.3 + B.4 (FU-515), B.2 (rate-limit + input caps, since the audit). **Accepted with rationale (not bugs at the current single-instance tenancy posture):** A.5 (self-host plaintext reset fallback), A.6 (in-memory rate-limit — revisit at Phase-4 scaling), A.7 (tokens-in-URL, mitigated by single-use + expiry). Keep this doc as the standing register; do not delete rows, mark them. The single remaining *future* item is A.6's shared rate-limit store, which belongs to Phase-4 horizontal scaling (tracked via `MULTI_USER_READINESS.md` + FU-045), not to an open assistant-security FU.
**Date (original):** 2026-06-04
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

### A.1 CSRF on state-changing endpoints — **✅ RESOLVED (2026-06-30, FU-197)**
> _Original severity: HIGH (worst auth issue at the time of the audit)._
>
> **Fixed** by a double-submit-cookie defence in [`dora_api/infrastructure/csrf.py`](../../dora_api/infrastructure/csrf.py) wired into the request middleware. Every response mints a non-HttpOnly `dora_csrf` cookie (SameSite=Lax, Secure when `SESSION_COOKIE_SECURE`); every mutating call (POST/PATCH/PUT/DELETE) under `/api/*` on a non-public, non-bearer endpoint must carry an `X-CSRF-Token` header whose value constant-time-matches the cookie (`hmac.compare_digest`) or it 403s. The SPA reads the cookie and attaches the header in an axios interceptor. Public endpoints (login/register/verify/reset/forgot/bootstrap) are exempt so a cold client can authenticate; `submit_ingestion_batch` (bearer-auth) is exempt because bearer tokens aren't replayable CSRF-style. Regression-pinned by `test_auth_flows.py::test__csrf__mutation_without_header_is_403`. `SameSite=Strict` was not adopted — the double-submit is the actual defence and doesn't depend on SameSite for correctness (cookie stays `Lax`, mirroring the session cookie).
>
> _Original write-up below for the audit trail:_
> Flask session cookie with `SameSite=Lax` and **no CSRF token**. `SameSite=Lax` permits top-level cross-site navigations, so a malicious page could drive a state-changing request (e.g. `POST /auth/me/email`) against a logged-in user.
> - **Impact:** change the victim's email → lock them out of password recovery → account takeover.
> - **Fix:** add a CSRF token to all state-changing endpoints, or set the session cookie `SameSite=Strict` (acceptable for an app with no cross-site entry flows), plus an `Origin`/`Referer` check on mutations.
> - **Multi-user:** severity rises — a lever against any account in a larger base.

### A.2 Email change requires no password proof — **✅ RESOLVED (2026-06-30, FU-197)**
> _Original severity: MEDIUM._
>
> **Fixed** in [`dora_api/features/auth/email_flows.py`](../../dora_api/features/auth/email_flows.py). `ChangeEmailRequest` now carries a required `current_password` field; the handler verifies it via `check_password_hash` before issuing a change token, and sends a `email_change_notice.html` alert to the **old** address *before* the confirmation email to the new one. Audit emits `auth.email_change.requested` on success and `auth.email_change.password_failed` (warn) on a wrong-password attempt. The overlapping `PATCH /auth/me` unverified-email-write path (surfaced during the fix — not in the original finding) was also closed by removing `email` from `UpdateMeRequest` with `extra="forbid"`. Regression-pinned by the password-gating cases in `test_auth_flows.py` (400 missing / 422 wrong / 204 happy). SPA rebuilt around the verified flow — current-password input + "Send confirmation" button on `AccountSettings.vue`.
>
> _Original write-up below for the audit trail:_
> `request_email_change` only requires a valid session (`email_flows.py:260`), while `change_password` correctly requires the current password (`change_password.py`). Inconsistent: the lower-friction path is the more dangerous one (email controls recovery).
> - **Fix:** require current-password re-entry to change email; additionally notify the *old* address that a change was requested, so the legitimate owner can react.

### A.3 Email-change UI doesn't exist — **✅ FIXED (FU-197)**
> `AccountSettings.vue` now carries the full verified change-email flow — a
> current-password field + "Send confirmation" button + copy explaining the
> change only takes effect after clicking the link in the new inbox. The dead
> endpoints are now reachable and gated by A.2's password proof.
>
> _Original:_ backend endpoints existed but `AccountSettings.vue` exposed no UI.

### A.4 Client/server password rules drift — **✅ FIXED (FU-442)**
> FU-442 aligned the policy to NIST (min 8, no composition mandate). Server:
> `MIN_PASSWORD_LENGTH = 8` (`auth_helpers.py`). Client: `LoginPage.vue`
> validates `v.length >= 8` ("At least 8 characters"). Both ends now agree, so
> a password that passes client validation passes the server.
>
> _Original:_ client ≥4 / server ≥10 + composition → a user cleared client validation then hit a server error. (Both numbers are now stale.)

### A.5 Admin password reset returns plaintext in the response — **➗ ACCEPTED (2026-07-08)**
> **Accepted as the deliberate self-host fallback.** `reset_user_password.py`
> (and `create_user_as_admin.py`) return a freshly-generated password in the
> body so an admin can relay it out-of-band **when SMTP isn't configured** —
> which, per the distribution posture, is the common self-host case. It's
> single-use in the sense that it's immediately the account's password (the
> user should change it). LOW severity: it requires an already-authenticated
> admin, and there's no email channel to prefer instead on a bare self-host.
> **Future hardening (not now):** a force-change-on-next-login flag once the
> auth flow supports a forced-rotation step, and a one-time reset *link* when
> email is guaranteed (ties to `EMAIL_SETUP_FINDINGS` / FU-413). Logged as
> accepted rather than fixed because the "fix" needs infrastructure that
> deliberately doesn't exist yet.

### A.6 Rate limiting is in-memory, per-process — **➗ ACCEPTED single-instance; Phase-4 scaling item**
> **Correct as-is for the single-instance deployments the product ships today**
> (self-host single instance / managed single-tenant — see the distribution
> posture in `RECONCILED_FINISHING_PLAN.md` §7.5). The per-process bucket only
> under-counts once the *same* instance is horizontally scaled to multiple
> processes/replicas, which is a Path-A (multi-tenant SaaS) concern that is
> explicitly deferred. **Revisit at Phase-4 horizontal scaling:** move to a
> shared store (Redis / DB) then. Cross-ref `MULTI_USER_READINESS.md` + FU-045
> (Postgres). Not a bug at the current tenancy posture.

### A.7 Tokens in URL query strings — **➗ ACCEPTED (mitigated)**
> **Accepted as-is per the doc's own recommendation.** Reset/verify tokens
> travel as `?token=`, but they're single-use, SHA-256-hashed at rest, and
> short-lived (1h / 24h), which bounds the exposure window to effectively
> nothing. Posting the token from the landing page instead is a marginal
> hardening not worth the added flow complexity at this severity.

---

## B. Dora assistant

### B.0 What's correct — the mutation gate (the thing most LLM apps get wrong)
Verified at `ask_assistant.py:187-190`: when the LLM emits an **action** tool call, the loop **short-circuits and returns a proposal** — it does *not* execute. The actual write happens only via a separate, user-confirmed `/confirm` call, and `confirm_actions.py` re-validates the payload at commit. **The LLM cannot mutate data on its own.** This is the single most important property for an action-taking assistant, and it's implemented correctly. Preserve it through any refactor.

### B.1 Prompt injection via tool results — **✅ MITIGATED (FU-515, 2026-07-08)**
> Fixed the two cheap, high-leverage halves of the doc's recommendation:
> (1) a firm **SECURITY block in `_SYSTEM_PROMPT`** telling the model that
> everything inside a tool result is untrusted DATA to summarise, never
> instructions to follow — this is the primary defence against a scraped
> product name saying "ignore previous instructions"; (2) `_sanitize_tool_output`
> strips C0/C7F control bytes from the serialised rows before they re-enter the
> model context (belt-and-braces — `json.dumps` already escapes control chars
> inside string values). The mutation gate (B.0) already bounds the blast
> radius to a *proposal the user must approve*. Deeper per-field
> delimiting/escaping of scraped fields at ingest is deferred until real
> merchant ingestion lands (Phase 2) and the seam is actually reachable — the
> "defanged, not eliminated" framing still holds, now with the model explicitly
> instructed to distrust tool content.
>
> _Original write-up:_ Tool results are serialized straight into the LLM context (`json.dumps(rows)` appended as a `tool` message). Free-text fields could carry an injected instruction. Only MEDIUM because B.0 prevents a silent write; the real external surface is scraped merchant product data.

### B.2 No rate limit / token cap on `/assistant/ask` — **✅ FIXED (since the audit)**
> All three guards the doc asked for now exist: **per-user rate limits**
> (`ask_assistant.py` — `_ASK_PER_MINUTE=20`, act/confirm 60, keyed by user id
> then IP), an **input-size cap** (`AskAssistantRequest.message` is
> `max_length=1000`; `current_path` now `max_length=200` too), and the tool
> loop is still bounded (`_MAX_TOOL_ROUNDS=3`) with capped per-tool result sizes
> (`_MAX_CANDIDATES` etc.). Cumulative context is bounded by the round cap ×
> capped result sizes; no explicit token counter, which is fine for a
> self-hosted model where the blast radius is local compute.
>
> _Original write-up:_ Only guards were the 3-round loop + 60s timeout; no rate limit or input cap.

### B.3 Tool arguments not bounds-checked — **✅ FIXED (FU-515, 2026-07-08)**
> The named example — `push_expiry`'s raw `int(args.get("days"))` — now
> rejects magnitudes over `_MAX_EXPIRY_PUSH_DAYS` (3650, ~10 years) at the
> boundary. Auditing the other numeric tool args: `adjust_recipe_meals.delta`
> and `cook_recipe`'s count were already clamped by `_coerce_signed_int` /
> `_MAX_COOK`. All mutating args still additionally pass through the user
> confirm card (B.0).
>
> _Original write-up:_ LLM-supplied args reached handlers with minimal validation (e.g. `push_expiry` with no cap on distance). SQLAlchemy parameterisation prevents SQL injection; semantic nonsense wasn't rejected.

### B.4 `current_path` concatenated into the system prompt — **✅ FIXED (FU-515, 2026-07-08)**
> `current_path` is now run through `_safe_current_path` before embedding:
> first line only, path-safe characters (`[A-Za-z0-9/_\-?=&.]`), length-capped
> to 200 — so a crafted value can't smuggle a newline + instruction-shaped text
> into the user turn. `AskAssistantRequest.current_path` also gained
> `max_length=200` as defence-in-depth at the request boundary.
>
> _Original write-up:_ The user's current route was appended into the prompt unescaped — a minor injection seam.

---

## C. Priority order

| # | Finding | Severity (single-tenant) | Fix effort | Status |
|---|---|---|---|---|
| 1 | A.1 CSRF on mutations | High | Medium | ✅ Fixed (FU-197, 2026-06-30) |
| 2 | A.2 Email change w/o password proof | Medium | Low | ✅ Fixed (FU-197, 2026-06-30) |
| 3 | B.1 Injection via scraped tool-result data | Medium | Low-Med | ✅ Mitigated (FU-515, 2026-07-08) |
| 4 | B.2 No assistant rate/token caps | Medium | Low | ✅ Fixed (rate-limit FU + `message` max_length + tool-round cap) |
| 5 | A.3 Email-change UI half-shipped | Medium | Low | ✅ Fixed (FU-197 — verified email flow shipped on AccountSettings) |
| 6 | B.3 Tool-arg bounds | Low-Med | Low | ✅ Fixed (FU-515, 2026-07-08) |
| 7 | A.4 Password-rule drift | Low | Low | ✅ Fixed (FU-442 — client + server both min-8) |
| 8 | B.4 `current_path` in prompt | Low | Low | ✅ Fixed (FU-515, 2026-07-08) |
| 9 | A.5 Admin reset returns plaintext | Low | Low | ➗ Accepted (self-host fallback; see stamp) |
| 10 | A.6 In-memory rate-limit store | Low / High-scaled | Low | ➗ Accepted single-instance; Phase-4 scaling item |
| 11 | A.7 Tokens in URL query strings | Low | Low | ➗ Accepted (single-use + short expiry) |

**Done first (2026-06-30, FU-197):** A.1 + A.2 — together they closed the account-takeover chain.

**Closed 2026-07-08 (FU-515):** verified/shipped the rest. B.1 (tool-result injection) mitigated via a system-prompt "tool data is not instructions" rule + control-byte stripping; B.3 (tool-arg bounds) via a `push_expiry` day cap (delta was already clamped); B.4 (`current_path`) via `_safe_current_path` sanitisation + a request-model length cap. B.2 / A.3 / A.4 were found already-fixed by earlier work. A.5 / A.6 / A.7 are **accepted** with rationale (see per-finding stamps) — A.6 revisits at Phase-4 horizontal scaling (cross-ref `MULTI_USER_READINESS.md`, FU-045).

---

## D. Note on tenancy

Several severities above are explicitly single-tenant. The companion `MULTI_USER_READINESS.md` covers what changes when multi-user ships — in short, A.1/A.2 escalate and entirely new isolation requirements appear. Don't treat "secure today" as "secure after multi-user."
