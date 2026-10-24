# Chunk 15 — Auth shell

**Session:** 2026-10-23 overnight (solo, no subagents) · **Stage:** 1 (analysis only — no code changed)
**Surface:** the pre-auth moment end to end — pre-mount splash (`index.html`), `SplashScreen` (boot + cannot-connect), `/setup` first-admin bootstrap, `/setup/backend` native instance picker, `/login` (sign-in + register), `/forgot-password`, `/reset-password`, `/verify-email`, the fullscreen 404, the shared `AuthShell` + `AuthButton` primitives, `authStore` + the axios client (401 routing, CSRF echo, retry, timeouts), the router's public/bypass sets; backend `features/auth/*` (login, logout, register, bootstrap, capabilities, change-password, the four email flows, admin gate), `infrastructure/{auth_helpers,csrf,middleware}.py`, `security/secret_encryption.py`, and `app.py`'s session-cookie block.
**Boundaries:** `/auth/me` + `/auth/me` PATCH → chunk 13; the welcome wizard → 14; `/api/client-logs` + the error pages inside the layout (`PageErrorState`) → 20; ingestion bearer auth → 16; demo mode + `DORA_*` env/boot → 19; email sending internals (`email_sender.py`) → 19.

---

## 0. Reading list + files walked

**Governing docs read:** `PROPOSAL_AUTH_SHELL.md` (C-19; §5 component contract, §7 D1–D10, §10 coverage — §7 is still headed "Open decisions — for you" although `IMPL_PLAN_AUTH_SHELL.md §0` records every call as resolved 2026-07-02; D4 names `ConfirmEmailChangePage`, retired by FU-620), `IMPL_PLAN_AUTH_SHELL.md` (§4 steps 1–7, §8 close-gate), `AUTH_ASSISTANT_SECURITY_FINDINGS.md` (A.1–A.4 resolved; A.5 plaintext admin reset / A.6 in-memory rate limit / A.7 tokens in query strings — all **accepted**, re-examined below), `EMAIL_SETUP_FINDINGS.md` (INV-4, shipped via FU-413), feedback `# SPLASH` (1), `# CANNOT CONNECT` (1), `# LOGIN / REGISTRATION / FORGOT` (7). Open FUs: FU-797 (Firefox-Android mascot seam — not reproduced), FU-655 (deactivation gate), FU-656 (password rule ×2 languages), FU-654 (session parse). Resolved and consulted: FU-197, 200, 440, 441, 442, 616, 620.

**Backend walked in full (2,230 lines):** `auth/{admin_gate,bootstrap_admin,capabilities,change_password,email_flows,login,logout,register_user}.py`, `infrastructure/{auth_helpers (399),csrf,middleware (310)}.py`, `security/secret_encryption.py`, `app.py:60–130`.

**SPA walked in full (~2,800 lines):** `pages/{LoginPage,SetupAdminPage,VerifyEmailPage,ForgotPasswordPage,ResetPasswordPage,ErrorNotFound}.vue`, `pages/setup/BackendSetupPage.vue`, `pages/errors/{ErrorPageNotFound,ErrorServer}.vue`, `components/{AuthShell,AuthButton,SplashScreen}.vue`, `stores/authStore.ts`, `services/api/{axiosHttpClient (449),backendUrl}.ts`, `boot/globalErrorHandler.ts`, `App.vue`, `index.html:20–70`, `router/{index,routes}.ts` (guard + the seven pre-auth routes).

**Tests read:** `tests/e2e/dora_api/test_auth_flows.py` (28), `test_route_auth_enforcement.py` (6 — anonymous sweep, allowlist-rot guard, admin sweep over a pinned list, reverse call-site count), `web_app/test/unit/authStore.spec.ts` (17), `web_app/e2e/{auth.setup,login.spec,smoke.spec}.ts` (the 3-spec smoke layer, kept).

**Verification greps run:** `def _too_many_requests|TOO_MANY_REQUESTS` (five hand-rolled 429 builders: `bootstrap_admin.py:73`, `email_flows.py:47`, `register_user.py:351`, `login.py:63–75` inline, `assistant/ask_assistant.py:72`; `api_response.py` has `conflict/forbidden/unauthorized/…` but no `too_many_requests`); `clear_cookie(` (defined `csrf.py:106`, **never called** — logout leaves `dora_csrf` behind); `ProxyFix|X-Forwarded-For` (none in `dora_api`; `request.remote_addr` is read raw in `auth_helpers.py:319`, `audit.py:199`, `submit_client_log.py:63`); `verification_sent` in `web_app/src` (**no reader** — `register_user.py:347` emits it for a toast the SPA never shows); `length >= 8` (`LoginPage.vue:49`, `SetupAdminPage.vue:51`; `models/password.ts` owns `MIN_PASSWORD_LENGTH`); bare icon strings (`LoginPage.vue:54`, `SetupAdminPage.vue:5,56`, `VerifyEmailPage.vue:5`, `BackendSetupPage.vue:5`; `ICONS` already has `visibility`, `visibility_off`, `mark_email_read`, `auto_awesome`); hex literals outside the DEC-2 ladder (`AuthButton.vue:76,87`, `SetupAdminPage.vue:147`, `BackendSetupPage.vue:121`, `SplashScreen.vue:242,251,257,274`, and the whole `--lost-*` ladder in `ErrorNotFound.vue:60–70` which **re-declares AuthShell's palette verbatim**); password-reveal toggle (`LoginPage`, `SetupAdminPage`, `settings/PasswordSetter`, `MyProductsPage` — four copies); `SESSION_USER_ID_KEY` vs the literal `"user_id"` (`logout.py:15`, `middleware.py:79,233`, `submit_client_log.py:63`); `logging_setup.py` (DEBUG when `debug=True` — the dev default — and `middleware.audit_incoming_request` dumps request JSON at DEBUG, **including `/auth/login` bodies**); tests for logout / session-staleness / deactivated-cookie-on-`/me` (none); `PINNED_ADMIN_ENDPOINTS` includes `/api/app-settings/probe` (13-R19 must drop it).

---

## A. Full Systems Test — Auth shell

### A1. Preconditions
- Fresh DB (no users) for the bootstrap path; a populated DB with `dora`/`dora` + one non-admin for the rest.
- One run with SMTP configured + `DORA_SECRET_ENCRYPTION_KEY` set (email flows live), one without (dry-run → "Forgot password?" hidden).
- Browser cold-load with the API stopped (cannot-connect), then started (retry).
- Native build (Capacitor) for `/setup/backend`; phone width + `prefers-reduced-motion` passes.

### A2. Golden path
| # | Step | Expect |
|---|---|---|
| G1 | Cold load, API down | `#pre-mount-splash` (midnight `#1f2647`, pulsing logo) → Vue mounts → `SplashScreen` quiet-blob backdrop, cycling flavour text → after the 8 s boot-probe timeout + 1 retry: "Can't reach Dora's brain", Try again; "Change instance URL" only when a runtime URL override is set. |
| G2 | Start the API, Try again | Probe resumes the same loop; splash fades (CSS, paint-independent) and unmounts after 360 ms. |
| G3 | Fresh DB → any URL | `/auth/bootstrap-required` true → `/setup` (one-time badge, username / optional email / password) → `POST /auth/bootstrap-admin` → auto-login, `email_verified=true`, redirect `/` → onboarding (chunk 14). Second visit to `/setup` → `/` or `/login`. |
| G4 | `/login` sign-in | Opaque 401 copy on bad creds; success → `redirect` query honoured; 5 wrong attempts/min → 429 with `Retry-After` and the generic "Sign-in failed" line. |
| G5 | Register from `/login` | Amber "Need an account? Register" flips the card; min 8 chars inline; 422 field errors inline; success → auto-login → `/welcome`; verification email queued if an address was given. |
| G6 | Forgot password (SMTP on) | Ghost "Forgot password?" visible; `/forgot-password` → 204 always → "If that address is registered…"; mail carries `#/reset-password?token=…` (hash deep link). |
| G7 | Reset link | `/reset-password?token` → new + confirm → 200 → "Continue to sign in"; every other device of that user is signed out on its next `/me`. Reused/expired/foreign-purpose token → 400 inline. |
| G8 | Verify link | `/verify-email?token` → "Email verified" → `/login?verified=1` toast; bad token → "Resend verification" dialog (anti-enumeration 204). |
| G9 | Native first launch | `/setup/backend` → URL normalised (`https://` + `/api`), probed via `/auth/me`, rolled back on failure, stored in Capacitor Preferences; web visitors to the route → `/settings/about`. |
| G10 | Typo'd URL | Fullscreen 404 with the same blobs + mascot + glass card as login; "Take me home". |
| G11 | Sign out (Settings) | `POST /auth/logout` audited, session cleared, list state + SW API cache wiped, `/login`. |
| G12 | Silent 401 mid-session | Interceptor clears the user + caches; next navigation lands on `/login?redirect=…`. |

### A3. Edge cases
| # | Case | Expect (and what the code does today) |
|---|---|---|
| E1 | Install behind nginx/Caddy/Traefik (the normal self-host) | **Today every user shares one `remote_addr`** (the proxy's): the 5/min login limit, 10/min register limit and the audit `actor_ip` are per-install, not per-client → 15-R1. |
| E2 | Dev server with `debug=True`, someone signs in | **Today the plaintext password is written to the log** by `audit_incoming_request` at DEBUG → 15-R2. |
| E3 | Register with an email | **Today no "check your inbox" toast** — the server's `verification_sent` flag has no reader → 15-R3. |
| E4 | Sign out, then inspect cookies | **Today `dora_csrf` survives** (`clear_cookie` is never called); harmless (re-minted, not a credential) but the pairing the docstring promises doesn't exist → 15-R4. |
| E5 | Deactivated user holding a live cookie hits a non-admin route | Passes until the next `/me` (FU-655, tracked; closes with FU-654). |
| E6 | Admin changes their own password on Users page | Session re-stamped, other devices out ✓ (chunk 13). |
| E7 | Backgrounded tab during boot | Splash fade is CSS + timer, never a Vue transition ✓ (DR-8). |
| E8 | Reduced motion | Blobs static, mascot still, card no enter animation, `will-change` released ✓. |
| E9 | Firefox on Android | Thin seam left of the mascot — mitigated with `will-change`/`backface-visibility`, **unconfirmed** (FU-797; stays a verify item). |
| E10 | Reset-password token in the URL | Accepted risk A.7 (single-use, hashed, 1 h) — unchanged. |
| E11 | 10+ registrations from one test client | In-memory buckets 429 the suite; tests drain `_buckets` directly (`test_route_auth_enforcement.py:231–235`) — a test seam, not a product issue. |
| E12 | Non-admin GETs `/api/app-settings/probe` | 403 today; after 13-R19 the route is gone and the pinned list must shrink or the reverse-count test fails → 15-R12. |

### A4. Persona coverage
- **Fresh self-host op:** G1→G3 in one sitting; `ADMIN_BOOTSTRAP_EMAIL` lock honoured (410 with a generic message). **Member:** G4/G5, no admin surfaces. **Phone:** mascot tucks top-centre at <760, card full-width, 48 px buttons. **Native:** G9 + "Change instance URL" on the error splash. **Managed/demo:** `demo_mode` capability → banner (chunk 19).

### A5. Load-bearing conditions
- One auth gate (`middleware.require_auth_if_protected`) + one allowlist (`PUBLIC_ENDPOINTS`), both pinned by the anonymous sweep and the allowlist-rot test ✓.
- CSRF double-submit: cookie minted on any `/api` response, header echoed by the one axios client; raw-`fetch` callers must spread `csrfHeader()` (R-047) ✓.
- Password policy is one Python authority (`validate_password`, NIST shape, no admin override) — the TS side mirrors only the length (FU-656).
- Session staleness: `pwd_v` stamped at login/register/bootstrap, compared in `get_me`; every password change bumps `password_changed_at` ✓.
- Deep links to the hash router go through `spa_deep_link` only ✓.

### A6. Release-gate rows
- [ ] Behind a reverse proxy, two clients get independent login rate limits and distinct audit IPs (after 15-R1).
- [ ] No request body from `/auth/*` reaches any log at any level (after 15-R2).
- [ ] Register with an email → "Check your inbox" toast (after 15-R3).
- [ ] Fullscreen 404 renders through `AuthShell` (after 15-R6) — one palette, one mascot animation.

---

## B. Help content — Auth shell

### B1. Current help audit
`HelpPage.vue` has nothing on signing in, creating an account, forgotten passwords, email verification, first-time setup or the native instance picker; 'Manage other users (admin)' mentions that an admin can "reset a forgotten password". `APP_OVERVIEW` says nothing. The in-page copy is already good (opaque sign-in failure, anti-enumeration wording, the capability-gated "Forgot password?").

### B2. Help entries

#### Signing in and creating an account
- **Group:** Dora itself
- **What it does:** Sign in with a username and password; "Need an account? Register" creates one (username, optional email, password of at least 8 characters — no symbol rules, just not a common password).
- **When it fires / how to trigger it:** Any signed-out visit; five wrong attempts a minute pauses sign-in briefly.
- **What controls it:** always on. New accounts are never admins; an admin promotes you in Settings → Admin → Users.
- **What it costs / might get wrong:** Sign-in failure never says which half was wrong (deliberate). The email is only used for password resets and the weekly deals mail.
- **Related:** Forgot your password · Who can change what (chunk 13). **Chip:** none. **Source:** `LoginPage.vue`, `login.py`, `register_user.py`, `auth_helpers.py:44–132`.

#### First-time setup (the first admin)
- **Group:** Dora itself
- **What it does:** A brand-new install opens on a one-time setup page that creates the first admin account and signs them in; after that the page is gone for good.
- **What controls it:** Operators can lock it to one address with `ADMIN_BOOTSTRAP_EMAIL`.
- **What it costs / might get wrong:** If you forget the very first password on a self-hosted box with no email set up, the recovery is to wipe and start again.
- **Related:** Your first run (chunk 14). **Chip:** none. **Source:** `SetupAdminPage.vue`, `bootstrap_admin.py`.

#### Forgot your password
- **Group:** Dora itself
- **What it does:** Enter your email and, if it is on an account, a single-use reset link arrives (valid 1 hour). Resetting signs out your other devices.
- **When it fires:** The button only appears when the install can actually send email; otherwise ask an admin to set a new password for you (Settings → Admin → Users).
- **What it costs / might get wrong:** The page always says "if that address is registered" — it never confirms whether an address exists.
- **Related:** Email and push setup (admin) (chunk 13). **Chip:** none. **Source:** `email_flows.py`, `capabilities.py`, `ForgotPasswordPage.vue`.

#### Verifying your email
- **Group:** Dora itself
- **What it does:** Accounts with an address get a 24-hour verification link; scheduled emails (the weekly deals mail) only go to verified addresses. The first admin is verified automatically.
- **What controls it:** Settings → Notifications offers "Send verification email" again.
- **Related:** Notifications: in-app, push, email (chunk 13). **Chip:** none. **Source:** `email_flows.py:68–143`, `NotificationsSettings.vue`.

#### Why was I signed out?
- **Group:** Dora itself
- **What it does:** Changing or resetting a password signs out every other device; an admin deactivating an account signs it out; sessions also end when the browser clears cookies.
- **Related:** Username, email and password (chunk 13). **Chip:** none. **Source:** `get_me.py`, `change_password.py`.

#### The phone app: choosing your Dora
- **Group:** Dora itself
- **What it does:** The Android/iOS app asks for your server's address once; it adds `/api` for you and checks it answers before saving. Change it later in Settings → About, or from the error screen if the saved address stops answering.
- **Related:** Install as an app (chunk 17). **Chip:** none. **Source:** `BackendSetupPage.vue`, `SplashScreen.vue:47–58`, `backendUrl.ts`.

### B3. DoraBot corpus delta
Add: *"New installs start with a one-time setup page for the first admin. Everyone else signs in with a username and password; accounts can be created from the sign-in page and need an admin to become admins. Forgot-password works only when the install can send email."* No tool nav (pre-auth surfaces are unreachable from the assistant).

---

## C. Senior review — Auth shell

### C1. Bugs (verified or high-confidence latent)
- **15-R1** · bug (deployment-shaped) · `auth_helpers.py:317–322`, `audit.py:199`, `submit_client_log.py:63` read `request.remote_addr` with no `ProxyFix`; the documented self-host shape is a reverse proxy, so every client arrives as the proxy's address: one shared login bucket (5/min for the whole household), one shared register bucket, and audit rows all carry the proxy IP. **Change:** wrap the WSGI app in `werkzeug.middleware.proxy_fix.ProxyFix(app.wsgi_app, x_for=N, x_proto=N)` **gated by a new env `DORA_TRUSTED_PROXY_HOPS`** (default `0` = off — trusting `X-Forwarded-For` blindly lets a direct client spoof its address, so the operator opts in); document it beside `DORA_SECURE_COOKIES` in the ops notes (chunk 19). Blast S. Guard: new pytest "`DORA_TRUSTED_PROXY_HOPS=1` → `remote_addr` comes from `X-Forwarded-For`". **execute**.
- **15-R2** · bug (security hygiene) · `middleware.py:274–284` `audit_incoming_request` logs `request.get_json()` for every request at DEBUG; `logging_setup.py:18` makes DEBUG the dev default. A developer signing in on a dev box writes `{"username":…,"password":…}` to the rotating log file. **Change:** skip the body dump when `endpoint_name in PUBLIC_ENDPOINTS` (every auth route) and redact keys matching `password|token|api_key` elsewhere (`new_password`, `current_password`, `smtp_password`, `vapid_private_key`, provider API keys all travel through authenticated PATCHes). Blast S. Guard: unit test on the redactor. **execute**.
- **15-R3** · bug (contract) · `register_user.py:338–347` adds `verification_sent` to the response "so the SPA can decide whether to surface a 'check your email' toast"; no SPA code reads it (R-057), so a registrant who gave an address is never told to look for the mail. **Change:** `LoginPage.onSubmit` register branch toasts "Check your inbox for a verification link" when `verification_sent`; add the field to `AuthenticatedUser`'s register response type. Blast S. **execute**.
- **15-R4** · latent · `csrf.clear_cookie` (`csrf.py:106–108`) is never called; `logout.py` clears the session but leaves `dora_csrf`. Not a vulnerability (the token is not a credential and is re-minted on the next response) but the module's own contract says it is paired with `session.clear()`. **Change:** call it from `logout()` (and on the `get_me` session-clear branches) or delete the function; prefer the call. Blast S. **execute**.
- **15-R5** · latent · `axiosHttpClient.ts:48–55` says the 401 handler "clear[s] user state, redirect[s] to /login"; `authStore.handleSessionExpired` (`:161–168`) only clears. A user parked on a page after a silent 401 sees emptied cards with no redirect until they navigate. **Change:** in the handler, `if (!PUBLIC_PAGE) window.location.hash = '#/login?redirect=' + current` (the store cannot import the router without a cycle; a hash assignment is the honest minimum) — or pass a navigation callback from the router setup. Blast S. **execute** (confirm in browser first — may already be masked by the next fetch failing fast).

### C2. Redundancy / DRY (R-001, R-003)
- **15-R6** · `pages/ErrorNotFound.vue` (237 lines) re-implements AuthShell's backdrop, blobs, mascot bob, glass card and the whole `--lost-*` palette (`:60–70` ≡ `AuthShell.vue:87–98`); it predates C-19 and was left out of IMPL_PLAN step 6. **Change:** `<AuthShell backdrop="blobs" mascot="top-right">` with the 404 copy in `#card-head` and an `AuthButton colour="primary" to="/"`; delete the local CSS. Also answers the `# NO AREA / MISC` "404 page theme" bullet. Blast S. **execute**.
- **15-R7** · five hand-rolled 429 responses (`bootstrap_admin.py:73–83`, `email_flows.py:47–57`, `register_user.py:351–362`, `login.py:63–75`, `assistant/ask_assistant.py:72–86`) and one `_validation_failure` helper (`email_flows.py:60–65`) beside six inline RFC-4918 literals (chunk 13-R14). **Change:** `api_response.too_many_requests(retry_after, detail=…)` and `api_response.validation_failed(errors)`; also `api_response.gone(detail)` for `bootstrap_admin._gone` and reuse the existing `conflict()` for `register_user.py:282–296`'s inline 409. Blast S (6 files). Guard: `test__login__rate_limit_returns_429_eventually`, `test__bootstrap_admin__rejects_when_users_exist`. **execute** (merges 11-R15).
- **15-R8** · password-reveal eye toggle written four times (`LoginPage.vue:52–59`, `SetupAdminPage.vue:54–61`, `settings/PasswordSetter.vue:16–31`, `MyProductsPage.vue`); min-length rule hardcoded as `8` in two of them (`LoginPage.vue:49`, `SetupAdminPage.vue:51`) beside `models/password.ts` (13-R12 found the Account page's four). **Change:** `components/PasswordField.vue` (q-input + reveal + `MIN_PASSWORD_LENGTH` hint/rule, `autocomplete` prop); Login, Setup, Reset, Account and PasswordSetter become callers. Blast S/M. **execute**.
- **15-R9** · `SplashScreen.onChangeInstance` (`:93–129`) is a declared "mirror of `AboutSettings.onChangeInstance`" (`AboutSettings.vue:352–397`). **Change:** `composables/useChangeInstance.ts` returning `promptAndSave()`; both call it (About adds the router replace, Splash the reload). Blast S. **execute**.
- **15-R10** · the DEC-2 ladder is one place by design, yet `#fff` (`AuthButton.vue:76`, `SetupAdminPage.vue:147`, `BackendSetupPage.vue:121`), `#3a2a08` (`AuthButton.vue:87`) and `#ffffff` ×4 (`SplashScreen.vue:242–274`) sit outside it, and `SplashScreen.vue:236–238` explains that `--auth-shell-text` is wrong on the canvas. **Change:** add `--auth-shell-on-accent: #fff`, `--auth-shell-on-amber: #3a2a08`, `--auth-shell-on-canvas: #fff` to the ladder and use them. Blast S. **execute** (R-002).
- **15-R11** · `SetupAdminPage.vue:139–153` and `BackendSetupPage.vue:113–125` carry the same `.setup-badge` pill (gradient, uppercase, 999px). **Change:** `#card-badge` slot on AuthShell with the pill styled there, or an `AuthBadge.vue`. Blast S. **execute**.
- **15-R12** · `test_route_auth_enforcement.PINNED_ADMIN_ENDPOINTS:177` pins `/api/app-settings/probe`; 13-R19 deletes that route. **Change:** drop the row in the same Stage-2 commit as 13-R19 (the reverse-count test enforces it). **execute** (with 13-R19).
- **15-R13** · `middleware.CSRF_EXEMPT_ENDPOINTS = PUBLIC_ENDPOINTS | {submit_ingestion_batch, ingest_link_status}` — both names are already in `PUBLIC_ENDPOINTS` (`:52,55`), and the four newer bearer endpoints aren't in the explicit set either, so the comment describes a distinction the code no longer makes. **Change:** `CSRF_EXEMPT_ENDPOINTS = PUBLIC_ENDPOINTS` + a comment that bearer routes are public-by-session and bearer-checked in-handler. **execute**.
- **15-R14** · the literal `"user_id"` session key (`logout.py:15`, `middleware.py:79,233`, `submit_client_log.py:63`) alongside `SESSION_USER_ID_KEY` everywhere else (R-003). **Change:** import the constant (move `SESSION_USER_ID_KEY`/`SESSION_PWD_V_KEY` out of `register_user.py` into `auth/session_keys.py` so `middleware` isn't importing a feature module — also the natural home for FU-654's resolver). **execute**.

### C3. Dead code / unused fields / unread endpoints
- **15-R15** · `csrf.clear_cookie` unused (14-R4 decides: call it). · `RegisterUserResponse.verify_username` duplicates `request.username` the route already holds. · `auth_helpers.__all__` exports `PURPOSE_*` it only re-imports. **Change:** trim with 15-R7. **execute**.
- **15-R16** · `BackendSetupPage.vue:80–85` probes with a bare `axios.get(url + '/auth/me')` — no `X-Request-Id`, no shared timeout policy, a second axios instance. **Change:** after `setBackendBaseUrl`, call `new AuthApiService().getMeAsync()` (it already treats 401 as "answered") inside the same try/rollback. Blast S. **execute** (R-003; also removes a raw-client site from FU-571's list).

### C4. Componentisation opportunities (R-001)
- Covered by 15-R6 (404 → shell), 15-R8 (`PasswordField`), 15-R11 (badge). Nothing further — `AuthShell`/`AuthButton` are the right size.

### C5. Placement / layering (R-003, R-005)
- **15-R17** · R-019 comment≠code: `register_user.py:4` and `auth_helpers.py:4` still state the retired policy "min 10 chars, ≥1 letter + ≥1 digit" (policy is min 8, no composition — `auth_helpers.py:44–67`); `capabilities.py:4–6` "exposes just one flag" (two); `test_auth_flows.py:171–179` describes the retired verified change-email flow; `PROPOSAL_AUTH_SHELL.md §7` heading "Open decisions — for you" + D4's `ConfirmEmailChangePage`. **Change:** fix the four comments; add "Open decisions — closed 2026-07-02, see IMPL_PLAN §0" under §7. **execute**.
- **15-R18** · `register_user.py:344` and `change_password.py:108–109` each open a second `SqlAlchemyRepository()` to re-read the user the handler just saved. **Change:** return the entity (or its email) from the handler. Blast S. **execute**.
- **15-R19** · `login.py:103,121` and `register_user.py:282–283` import inside the function body for no cycle reason (`SESSION_PWD_V_KEY`, `get_provider_config`, `jsonify`). **Change:** module-level imports (cycle-safe — same package). **execute**.

### C6. Naming & idiom
- **15-R20** · R-034 bare icon names: `LoginPage.vue:54`, `SetupAdminPage.vue:5,56`, `VerifyEmailPage.vue:5` (`'mark_email_read' | 'error' | 'mail_lock'`), `BackendSetupPage.vue:5` (`dns`). **Change:** `ICONS.*` (add `mail_lock`, `error`, `dns` to the registry if absent). **execute**.
- **15-R21** · f-string logging with the `%s` idiom beside it: `login.py:82,94,112`, `register_user.py:298,301,337`, `change_password.py:134`, `bootstrap_admin.py:207`, `logout.py:35`. **Change:** `%s` args. **execute**.
- **15-R22** · `LoginRequest` fields use `Field(min_length = 1, …)` with spaces around `=` (`login.py:28–29`) — the one file in the package with that style. **execute**.

### C7. Efficiency
- **15-R23** · `find_active_token` (`auth_helpers.py:184–214`) loads **every** live token of a purpose and compares each hash in Python (constant-time per row). Correct, and O(live tokens) is tiny for a household; for a managed instance with many users a `WHERE token_hash = :h` lookup (the hash is deterministic — equality in SQL leaks nothing the timing-safe compare protects) is the standard shape. **Change:** query by `token_hash` then re-verify with `compare_digest`. Blast S. **execute** (comment the reasoning).
- **15-R24** · `bootstrap_required` runs a `COUNT(*)` on `User` on every cold load for every client; `bootstrap_admin` counts twice. Fine for a household; a `SELECT 1 … LIMIT 1` (`exists`) is the honest query. **waive** (negligible; note only).

### C8. Design-level findings — out of Stage-2 scope
- **15-D1** · Feedback "allow admins to turn the restrictions off" — **deliberately not built** (`auth_helpers.py:65–67`: NIST posture, no operator override). Record as out-of-scope with reason; the only remaining restriction is min 8 + a 60-word deny list, so the ask is largely moot.
- **15-D2** · A.5 (admin-set password returned in plaintext once, when generated) stays accepted — it is the self-host fallback; A.6 (in-memory rate limit) stays accepted for single-instance but **15-R1 makes it per-client**, which is the part that actually bites today; A.7 (token in URL) stays accepted.
- **15-D3** · `WelcomeLayout` pins `data-theme="pesto-dark"` rather than wrapping `AuthShell` as D3 of the proposal decided; the 2026-10-17 wizard rebuild chose a flat dark canvas on purpose (CHUNK_14). Feedback L24 "same styling as login" is therefore met in spirit (dark continuity) not letter (no blobs/mascot). Owner: accept as is (default) or wrap.
- **15-D4** · `authStore.handleSessionExpired` redirect (15-R5) — if the owner prefers "stay on the page and show a sign-in dialog", that is a design change; the default above is the minimal redirect.
- **15-D5** · Register is a mode toggle on the login card rather than its own route — fine, but there is no way to deep-link to "create account" (e.g. from an invite). Note only.

### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `auth_helpers.rate_limit` | in-memory sliding window | `Flask-Limiter` | **keep** (single-instance posture, A.6) | – | Add `ProxyFix` (15-R1); revisit at Phase-4 scaling with a shared store. |
| `csrf.py` double-submit | hand-rolled | `Flask-WTF` CSRF | **keep** | – | 100 lines, tested, matches the SPA's cookie-echo model; Flask-WTF assumes forms. |
| `auth_helpers` token plumbing | SHA-256 + `AuthToken` table | `itsdangerous` signed tokens | **keep** | – | Server-side revocation (single-use, sibling revoke) needs the table anyway. |
| `axiosHttpClient` retry/backoff | hand-rolled | `axios-retry` | **keep** | – | Boot-probe-specific ceilings; 40 lines. |
| `AuthShell` blobs/mascot | CSS | – | **keep** | – | FU-797 mitigation in place. |
| Password policy deny-list | 60 bundled words | HIBP k-anonymity API | **keep** | – | Offline self-host (R-005); documented. |

### C10. Standards drift (R-0NN)
- **15-R25** · R-002: hex outside the DEC-2 ladder (15-R10) and the duplicated ladder (15-R6). **execute**.
- **15-R26** · R-034: bare icons (15-R20). **execute**.
- **15-R27** · R-019: stale policy/flag/flow comments (15-R17). **execute**.
- **15-R28** · R-057 contract: `verification_sent` emitted, never typed or read (15-R3). **execute**.
- **15-R29** · R-003: the session-key literal (15-R14); FU-654 +2 sites here (`change_password.py:75–82`, `logout.py:15`). **execute** under FU-654.
- **15-R30** · R-005 distribution posture: no proxy-awareness knob (15-R1) — the one gap the §7.5 checklist would have caught. **execute**.

### C11. Ride-along signals for FU-010 / FU-224 (theme / colour)
- The auth ladder is a deliberate R-002 carve-out (DEC-2) — leave it; only the leaks (15-R10) and the duplicate (15-R6) move. `ErrorServer`/`PageErrorState` (in-layout) are themed normally — fine.

---

## D. Test plan — Auth shell

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| With `DORA_TRUSTED_PROXY_HOPS=1`, `X-Forwarded-For: 10.0.0.9` → `remote_addr == 10.0.0.9`; with 0 (default) the header is ignored | pytest | must-write-before-ship | 15-R1 |
| DEBUG request logging never includes a `password`/`token` value (capture the log handler, POST `/auth/login`) | pytest | must-write-before-ship | 15-R2 |
| `POST /auth/logout` clears the session (`/me` → 401) and emits `auth.logout`; `Set-Cookie` deletes `dora_csrf` | pytest | nice-to-have | 15-R4 (no logout test exists) |
| Session staleness: login on client A, change password on client B → A's `/me` → 401 | pytest | nice-to-have | pins `get_me:50–61` (untested today) |
| Deactivated user's live cookie → `/me` 401 with the deactivated message | pytest | nice-to-have | pins `get_me:40–48` (untested) |
| `api_response.too_many_requests` sets `Retry-After ≥ 1` and problem+json | pytest (unit) | nice-to-have | 15-R7 |
| `PasswordField` shows the `MIN_PASSWORD_LENGTH` rule from `models/password.ts` | vitest | nice-to-have | 15-R8 |
| `find_active_token` equality lookup still rejects a hash-collision-shaped wrong token | pytest | nice-to-have | 15-R23 |

Existing: 28 + 6 pytest, 17 vitest, 3 Playwright (smoke layer — unchanged). No new Playwright.

---

## E. Proposed follow-ups (orchestrator allocates ids)

- **urgent** · bug · no `ProxyFix` → per-install rate limits + proxy IP in audit behind a reverse proxy (15-R1). Stage 2; env-gated.
- **urgent** · finding (security hygiene) · DEBUG body logging captures login passwords and every secret-bearing PATCH (15-R2). Stage 2.
- bug · `verification_sent` has no reader; registrants aren't told to check mail (15-R3). Stage 2.
- finding · fullscreen 404 duplicates the auth-shell palette and chrome (15-R6). Stage 2.
- finding · five 429 builders + validation/gone/conflict literals → `api_response` helpers (15-R7, merges 11-R15 + 13-R14). Stage 2.
- finding · `PasswordField` ×4 copies + hardcoded 8 ×2 (15-R8; with 13-R12 / FU-656). Stage 2.
- finding · silent-401 handler clears state but never redirects (15-R5). Confirm in browser, then Stage 2.
- finding · `clear_cookie` never called (15-R4). Stage 2.
- decision · 15-D3 wrap `WelcomeLayout` in `AuthShell` (proposal D3) vs keep the flat dark canvas. Owner (default keep).
- decision · 15-D4 session-expiry UX (redirect vs dialog). Owner (default redirect).
- advance · FU-654 +2 (`change_password`, `logout`); FU-655 unchanged (closes with 654); FU-656 → resolve via 15-R8 + 13-R12 (publish `password_min_length` on `/auth/capabilities`); FU-571 −1 raw-client site (15-R16); FU-797 stays a verify item.
- close-out · `PROPOSAL_AUTH_SHELL.md §7` gets its "closed" line; D4's `ConfirmEmailChangePage` struck (FU-620). Doc tidy at Stage 2.

## F. Summary for the register

- FST rows: 12 golden + 12 edge + 4 gate · Help entries: 6 (all new — the surface had none) · Review findings: 30 (execute 27 / waive 1 / decisions 5 in C8) · Tests: 8 (must-write 2) · Bugs: 3 verified (R1–R3) + 2 latent (R4–R5)
- Feedback coverage — `# SPLASH` "same colouring as login" → ✅ (`AuthShell backdrop="quiet"`, D2). `# CANNOT CONNECT` "same styling, keep the logo animation and placement" → ✅ (same `SplashScreen`, error variant, pulsing logo). `# LOGIN / REGISTRATION / FORGOT`: min 8 ✅; "admins can turn restrictions off" → **out of scope, deliberate** (15-D1); forgot-password matches login ✅ (folded into the shell); forgot-password email + hide the button when no sender ✅ (`/auth/capabilities`, INV-4); floating Dora on mobile → ✅ (`top-centre` under 760 px); buttons centred ✅ (`AuthButton` full-width); Register as an amber-gradient button + "Have an account? Sign in" ✅; donation button bottom-left with animation ✅ (`DonateButton variant="floating"`). `# NO AREA / MISC` "404 page theme" → 15-R6.
- One-liner: the pre-auth shell is finished and the security posture is sound; what remains is deployment-shaped — no proxy awareness (so a self-host behind nginx rate-limits the whole household as one client), debug logging that captures passwords, a register toast the server emits a flag for but the SPA never shows, and a fullscreen 404 that still carries its own copy of the shell.
