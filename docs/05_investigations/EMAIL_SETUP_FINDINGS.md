# EMAIL_SETUP_FINDINGS — INV-4

**Date:** 2026-06-06  
**Type:** Read-only investigation. No code changes.  
**Purpose:** Trace the password-reset email flow end to end, state whether it
works out-of-the-box, and outline (1) a flexible admin email-setup approach and
(2) the "hide forgot-password if no sender configured" logic.

> **Status: ✅ PROPOSAL SHIPPED 2026-07-14 (FU-413 closed).** Both halves of the
> §"Proposal" below are live, delivered via the R-030 / FU-333 operational-config
> work rather than a standalone IMPL plan:
> - **Admin email setup on `AppSetting`** — `smtp_host`/`smtp_port`/`smtp_username`/
>   `smtp_from`/`smtp_use_tls` + Fernet-encrypted `smtp_password_encrypted`;
>   `resolved_operational_config()` resolves them; `email_sender._config()` reads
>   DB → degrades to dry-run (`dry_run = not username`); admin UI is
>   `AdminSystemEmailSettings.vue`; the DTO exposes `smtp_password_configured`
>   (bool) and never the ciphertext. Password **encryption at rest** (proposal
>   Phase 3) also shipped.
> - **Hide forgot-password when unconfigured** — pre-auth
>   `GET /api/auth/capabilities` returns `email_sender_configured`
>   (`email_sender.email_sender_configured()` = `not dry_run`); `LoginPage.vue`
>   gates the link on it. **Open question answered: dry-run counts as NOT
>   configured** (a normal user can't read the server log).
> - **Superseded, deliberately not built:** the proposal's "PATCH refuses
>   `email_enabled=true` unless host/from/creds present" hard-validation — the
>   degrade-to-dry-run design + a capability derived from *actual sendability*
>   (username presence) serves the same need better (no "enabled but dead-end"
>   state, sensible host/from defaults). **Phase-3 "future sugar"** (provider
>   presets like SendGrid/Mailgun, an onboarding email step) stays parked
>   (Anti-creep) — resurface only if a hosted-onboarding polish pass wants it.
> Verified 2026-07-14 end-to-end: dry-run install → `email_sender_configured:false`;
> setting an SMTP username → `true`. Test coverage: `test_email_sender.py` (16).

---

## TL;DR

- The flow is **fully implemented and works out-of-the-box** — with a twist:
  if no SMTP username is set it runs in **dry-run mode** and *logs* the reset
  link instead of emailing it (deliberate, for self-hosted/desktop installs).
- SMTP config is **env-var only** (`DORA_SMTP_*`). There is **no UI** to set it,
  and changing it needs a restart.
- The user's proposal (admin configures a sender in onboarding; hide the button
  if unset) is sensible and lands naturally on the existing **`AppSetting`
  singleton + admin GET/PATCH** plumbing.

---

## (a) The flow as it exists today

### Request a reset — `dora_api/features/auth/email_flows.py:159-192`
- `POST /api/auth/forgot-password` `{email}`.
- Rate-limited (5/min per email+IP); **always returns 204** (anti-enumeration —
  never reveals whether the email exists).
- If the user exists: mints a reset token (`issue_token(…, PURPOSE_RESET_PASSWORD,
  RESET_PASSWORD_TTL)`, TTL 1h, `auth_helpers.py:79`) and calls
  `try_send(send_email, …)`.

### Send — `dora_api/infrastructure/email_sender.py`
- Config from env (`_config()`, lines 54-64):
  `DORA_SMTP_HOST` (default `smtp.gmail.com`), `DORA_SMTP_PORT` (587),
  `DORA_SMTP_USERNAME`, `DORA_SMTP_PASSWORD`, `DORA_SMTP_FROM`,
  `DORA_SMTP_USE_TLS` (default true).
- **Dry-run = `not username`** (line 63). When the username is empty
  (lines 86-91), it logs `"DRY-RUN email | to=… | subject=…"` with the body
  (which contains the reset link) and returns — **no crash, no send**.
- With a username/password set, it does a normal STARTTLS SMTP send
  (lines 93-110).

### Failure handling — `dora_api/infrastructure/auth_helpers.py:266-274`
- `try_send` swallows all send exceptions and logs a warning, so a broken SMTP
  config never surfaces to the user (also anti-enumeration — "couldn't send
  mail" would leak whether the address is known).

### Consume the token — `email_flows.py:203-250`
- `POST /api/auth/reset-password` `{token, new_password}`.
- Validates password (≥10 chars, ≥1 letter + ≥1 digit), constant-time token
  lookup, updates `password_hash` + `password_changed_at`, marks token consumed,
  revokes the user's other live reset tokens, sends a "password changed"
  confirmation.

### Frontend
- `LoginPage.vue:104-108` — a "Forgot password?" link, shown whenever
  `mode === 'login'`. **No conditional hiding today.**
- `ForgotPasswordPage.vue` — posts the email, always shows "if that address is
  registered…" (anti-enumeration), no error feedback.
- `ResetPasswordPage.vue` — reads `?token=`, posts the new password, shows
  success.

### Verdict: **does it work out-of-the-box?**
**Yes.** On a fresh install with no SMTP env vars, the reset flow runs and the
link is written to the logs (dry-run). For a real install, the admin sets
`DORA_SMTP_*` env vars and it sends via SMTP. What's missing is any **in-app way
to configure a sender** and any signal to the user about which mode they're in.

---

## (b) Existing settings plumbing

`AppSetting` (`dora_api/domain/entities/app_setting.py:6-23`) is a **singleton
row** that today only holds LLM config (`llm_enabled`, `llm_base_url`,
`llm_model`). It already has:
- get-or-create accessor (`features/app_settings/access.py`),
- admin-only `GET` / `PATCH /api/app-settings` (`get_app_settings.py`,
  `update_app_settings.py`), with validation-on-enable,
- a DTO serialization pattern (`AppSettingsDto`).

This is the natural home for SMTP config — no new architecture needed.

---

## Proposal

### 1. Flexible admin email setup (minimal complexity)
Extend `AppSetting` with email fields and let the sender prefer them, falling
back to env vars (so existing deployments keep working):

```
smtp_enabled: bool
smtp_provider: str | None        # "smtp" now; room for "sendgrid"/"mailgun" presets later
smtp_host / smtp_port: …
smtp_username / smtp_password: …  # password write-only in the DTO; encrypt at rest later
smtp_from_address: str | None
```
- Migration adds the columns; `AppSettingsDto` gains the fields (password masked
  on read); the PATCH handler refuses `smtp_enabled=true` unless host/from/creds
  are present (mirrors the existing LLM enable-validation).
- `email_sender.py:_config()` reads **DB settings first, then env, then dry-run**
  — keeping the env path as the backward-compatible fallback.
- Keep `provider` as a thin abstraction: "smtp" maps to the current path;
  presets are future sugar, not required now (Anti-creep / P10).

### 2. "Hide forgot-password if no sender configured"
- Add a backend capability: `email_sender_configured: bool` (true if DB
  `smtp_enabled` with required fields, OR `DORA_SMTP_USERNAME` set). Expose it on
  an unauthenticated bootstrap/capabilities endpoint the login page can read
  (e.g. extend an existing `/api/auth/capabilities` or bootstrap response).
- `LoginPage.vue:104-108`: render the "Forgot password?" link only when the
  capability is true; otherwise show a muted "Contact your admin to reset your
  password." line.
- **Design note:** dry-run *is* a working sender for self-hosted single-admin
  use (link in logs). Decide whether dry-run should count as "configured" for the
  purpose of showing the button. Recommendation: treat dry-run as **not**
  configured for the public login page (a normal user can't read server logs),
  but the admin can still trigger resets. Confirm with the user.

### Where to put the setup UI
- Smallest: an **Email** section in `SystemSettings.vue` next to the AI/LLM
  section (same "test connection → enable" pattern). Recommended first.
- Optional later: an onboarding step in `WelcomeWizard.vue` after "you're the
  admin." Defer unless onboarding polish is in scope.

---

## Effort

| Phase | Scope | Rough effort |
|---|---|---|
| 1 | Capability flag + hide button (env-based check only) | small (~2-3h) |
| 2 | `AppSetting` SMTP fields + SystemSettings UI + sender DB fallback | medium (~4-6h) |
| 3 | Onboarding step, provider presets, password encryption-at-rest | nice-to-have |

---

## Key file references

| Component | File | Lines |
|---|---|---|
| Forgot-password endpoint | `dora_api/features/auth/email_flows.py` | 159-192 |
| Reset-password endpoint | `dora_api/features/auth/email_flows.py` | 203-250 |
| Email sender + SMTP config | `dora_api/infrastructure/email_sender.py` | 54-110 |
| Dry-run branch | `dora_api/infrastructure/email_sender.py` | 86-91 |
| Failure swallow (`try_send`) | `dora_api/infrastructure/auth_helpers.py` | 266-274 |
| AppSetting entity | `dora_api/domain/entities/app_setting.py` | 6-23 |
| AppSetting GET/PATCH | `dora_api/features/app_settings/` | get / update / access |
| Login forgot link | `web_app/src/pages/LoginPage.vue` | 104-108 |
| Forgot/reset pages | `web_app/src/pages/ForgotPasswordPage.vue`, `ResetPasswordPage.vue` | — |
| Settings UI host | `web_app/src/pages/settings/SystemSettings.vue` | — |

---

## Feedback coverage

| User-flagged item | Finding |
|---|---|
| "how does forgot-password email actually work?" | Full flow traced (request → token → SMTP send → consume). Works OOTB; dry-run logs the link when SMTP unset. |
| "admin sets up a sending account in onboarding" | Lands on existing `AppSetting` singleton + admin PATCH. Proposed phased: SystemSettings section first, onboarding step optional later. |
| "if unset, hide the forgot-password button" | Proposed `email_sender_configured` capability exposed pre-auth; `LoginPage.vue:104-108` renders link conditionally. Open Q: does dry-run count as "configured"? |
