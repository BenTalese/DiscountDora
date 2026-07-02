# IMPL_PLAN_AUTH_SHELL — Execution plan for C-19 (auth-shell + AuthButton)

**Source proposal:** [`PROPOSAL_AUTH_SHELL.md`](PROPOSAL_AUTH_SHELL.md).
**Prompt:** `docs/03_prompts/C_big_rock_design_briefs.md` §C-19.
**Written:** 2026-07-02.
**Ships as:** one PR. Splitting the drift removal + naming-collision fix
across releases risks a partial state where some pre-auth pages have the
collision-safe shell and others don't.

## 0. Decisions baked in (D1–D10)

The user's calls on the §7 open decisions of PROPOSAL_AUTH_SHELL, resolved
2026-07-02:

- **D1** — one `--auth-shell-*` ladder across all pre-auth surfaces.
- **D2** — Splash / cannot-connect wraps `AuthShell backdrop="quiet"`
  (blobs frozen + low opacity, no CPU cost during bootstrap).
- **D3** — Onboarding wraps in the shell (WelcomeLayout only; scene
  choreography stays with PROPOSAL_ONBOARDING).
- **D4** — All four auxiliary pre-auth pages fold in
  (`VerifyEmailPage`, `ForgotPasswordPage`, `ResetPasswordPage`,
  `ConfirmEmailChangePage`).
- **D5** — Palette lives component-scoped inside `AuthShell.vue`. Not
  promoted to `:root`.
- **D6** — Mascot is a positional prop (`top-right` / `top-centre` /
  `none`), not a slot.
- **D7** — `index.html`'s `#pre-mount-splash` hardcodes `#1f2647`. Drop
  the `prefers-color-scheme: dark` block.
- **D8** — Original spec's "configurable landing background" — out of
  scope; logged as historical `consider (deferred)` in the proposal.
- **D9** — Dedicated `AuthButton.vue` (composes `BaseButton`); no
  gradient variants on `BaseButton`.
- **D10** — New `--auth-shell-accent-amber-strong` token for the
  secondary button's two-stop amber gradient.

## 1. Scope + non-goals

**In scope**

- Extract the pre-auth chrome (blob backdrop, mascot, frosted-card wrap,
  reduced-motion + force-light wiring, token ladder) into
  `AuthShell.vue`.
- Extract the current LP submit-button treatment into `AuthButton.vue`
  (primary/secondary/ghost), scoped by name to the auth moment.
- Migrate all nine pre-auth surfaces onto the shell + button:
  LoginPage, SetupAdminPage, SplashScreen (+ index.html pre-mount),
  WelcomeLayout, VerifyEmailPage, ForgotPasswordPage, ResetPasswordPage,
  ConfirmEmailChangePage. OnboardingStory glyphs re-tune to the new
  midnight canvas (colours only; no choreography change).
- Update ledgers: close FU-440 (SetupAdmin `--lp-*` drift), FU-441
  (`.auth-shell` name collision), FU-443 (this deferred job).

**Out of scope**

- Onboarding cinematic scene choreography, motion, autoplay — owned by
  `PROPOSAL_ONBOARDING §2.4 / §3.1`.
- Password-policy feedback (FU-442 stays open — different work unit).
- User-configurable pre-auth background (§8 of the proposal — P10
  anti-creep).
- Any backend / API / store change.

## 2. Engineering-standards check (pre-flight)

Rules touched:

- **R-001 / R-005** — componentise the pattern. `AuthShell` + `AuthButton`
  are the two new primitives; every consumer becomes a thin shell.
- **R-002 (theme-tokens-only)** — the `--auth-shell-*` ladder is an
  explicit **DEC-2 carve-out** for pre-auth surfaces (force-light before
  the user's theme is known). The rationale sits physically next to the
  token declarations in `AuthShell.vue`, not scattered.
- **R-003 (single source of truth)** — removes the `--lp-*` /
  `SetupAdminPage` duplication that FU-440 flagged. `.auth-shell` class
  name freed from the aux pages resolves FU-441.
- **R-006 (framework discipline)** — pure Vue 3 SFC + Quasar; no
  framework rewrite.
- **R-007 (scope discipline)** — no adjacent cleanup rides along; scene
  choreography, password policy, and configurable-background all left
  alone.
- **R-008 (code-style minimalism)** — no filler comments; DEC-2 gets
  one block, nothing else editorialises.
- **R-010 (scope discipline of primitives)** — the auth-button gradient
  stays out of `BaseButton`; keeps drift risk zero.

Close-gate re-check at end of unit (§8).

## 3. Component API contracts

### 3.1 `AuthShell.vue`

Location: `web_app/src/components/AuthShell.vue`.

```
<AuthShell
  :backdrop="'blobs' | 'quiet' | 'none'"           // default 'blobs'
  :mascot="'top-right' | 'top-centre' | 'none'"    // default 'top-right'
  :variant="'card' | 'full-bleed'"                 // default 'card'
  :role="string"                                   // default 'main'
  :aria-busy="boolean | undefined"                 // splash sets true
>
  <template #card-head>...</template>              // optional: title + sub
  <template #default>...</template>                // main content
  <template #card-foot>...</template>              // optional: link/toggle row
</AuthShell>
```

- Roots on `<div class="dora-auth-shell">` (project-prefixed; avoids the
  live `.auth-shell` collision on aux pages).
- Blob backdrop keyframes + reduced-motion freeze live here, not in
  consumers. `backdrop="quiet"` = motion-frozen, opacity `0.3`.
  `backdrop="none"` = flat `--auth-shell-bg-base`, no blob nodes emitted.
- Mascot: `top-right` = current LoginPage placement (with the
  `<760px` and `<360px` responsive shrinks). `top-centre` = above the
  slot content (splash's pulsing-logo idiom overrides mascot itself
  and passes its own image via slot; `mascot="none"` on splash).
- `variant="card"` renders the frosted-card wrap around the default
  slot; `full-bleed` skips it and hands the slot the raw padded area.
- Force-light `q-field` overrides moved off `LoginPage.vue` and into
  the shell so aux pages inherit them.

### 3.2 `AuthButton.vue`

Location: `web_app/src/components/AuthButton.vue`.

```
<AuthButton
  colour="primary" | "secondary" | "ghost"    // default 'primary'
  type="submit" | "button"                    // passes through to BaseButton
  :loading?="boolean"
  :disable?="boolean"
  :label?="string"
  :icon?="string"
  :to?="string"
  @click="..."
/>
```

- Composes `BaseButton` (variant fixed to `primary` under the hood; the
  colour prop drives the *auth* colour treatment via scoped CSS
  overrides).
- Size pinned to `lg` full-width — the whole point is a consistent hit
  target inside the auth moment.
- Slot forwards to BaseButton so `<AuthButton>Custom text</AuthButton>`
  works.

**Colours (all backed by `--auth-shell-*` tokens):**

| `colour` | Treatment |
|---|---|
| `primary` | Linear-gradient(135deg, `--auth-shell-accent-strong` → `--auth-shell-accent`); shadow; hover translate. Identical visual to today's `.login-submit`. |
| `secondary` | Linear-gradient(135deg, `--auth-shell-accent-amber-strong` → `--auth-shell-blob-2`); same shape/shadow, amber palette. Feedback's "gradient of dora yellow". |
| `ghost` | Flat transparent; `--auth-shell-accent` text; `border-radius: 12px` hit target. Kills the fine-print router-link feel. |

**Enforcement of "auth-only":** an inline comment in `AuthButton.vue`
notes it's paired with `AuthShell`; no runtime injection check (adding
one adds ceremony for zero real risk).

### 3.3 Token ladder (component-scoped)

```
.dora-auth-shell {
  /* R-002 DEC-2 carve-out: pre-auth surfaces render before the user's
     theme is known. Force-light + raw hex is deliberate; do NOT flow
     --data-theme-* tokens through. */
  --auth-shell-bg-base:            #1f2647;
  --auth-shell-blob-1:             #ff7ad9;
  --auth-shell-blob-2:             #f5c462;
  --auth-shell-blob-3:             #4cd5b7;
  --auth-shell-card-bg:            rgba(255, 255, 255, 0.94);
  --auth-shell-card-border:        rgba(255, 255, 255, 0.60);
  --auth-shell-text:               #1f2330;
  --auth-shell-text-muted:         #5b6173;
  --auth-shell-accent:             #006a80;
  --auth-shell-accent-strong:      #17b073;
  --auth-shell-accent-amber-strong:#c88a1e;  /* D10 — two-stop amber partner for blob-2 */
  --auth-shell-shadow:             0 30px 80px -30px rgba(20, 12, 50, 0.55);
  color-scheme: light;
}
```

## 4. Migration steps

Each step is reversible and ends with a compilable, visibly-identical
app before the next.

### Step 1 — Create `AuthShell.vue`

New file. No consumer yet. Includes:

- Template: root `<div class="dora-auth-shell" :class="variantClasses" :role="role" :aria-busy="ariaBusy">`, conditional blob backdrop, conditional mascot, conditional card wrap around default slot, card-head + card-foot slots inside the card.
- Script: `defineProps` for `backdrop | mascot | variant | role | ariaBusy`; `defineSlots`.
- Style: token ladder + all backdrop/mascot/card CSS lifted verbatim from `LoginPage.vue`, plus `backdrop="quiet"` opacity/motion freeze, `backdrop="none"` short-circuit, plus the `:deep(.q-field...)` force-light overrides.
- Reduced-motion block covers blobs, mascot, card-enter.

**Acceptance:** file compiles under `vue-tsc --noEmit`. Nothing renders it yet, so no visual regression is possible.

### Step 2a — Create `AuthButton.vue`

New file. Composes `BaseButton` with `variant="primary"` under the hood; colour prop drives scoped-CSS overrides via `:deep(.q-btn)`.

**Acceptance:** file compiles under `vue-tsc --noEmit`. Standalone unit render matches today's `.login-submit` for `colour="primary"`.

### Step 2b — Migrate `LoginPage.vue`

Replace the entire template chrome with `<AuthShell backdrop="blobs" mascot="top-right">…</AuthShell>`. Move title/sub into `#card-head`; form into default slot; toggle + forgot-password into `#card-foot`.

Rework the button set:

1. Submit → `<AuthButton colour="primary" type="submit" :loading="submitting" :label="mode === 'login' ? 'Sign In' : 'Create Account'" />`.
2. Mode toggle → `<AuthButton colour="secondary" :label="mode === 'login' ? 'Need an account? Register' : 'Have an account? Sign in'" @click="toggleMode" />`.
3. Forgot password → `<AuthButton colour="ghost" label="Forgot password?" @click="router.push('/forgot-password')" />` (only when `mode === 'login'`).

Delete the entire `<style scoped>` block (all of `--lp-*` ladder, `.login-shell`, blob CSS, mascot CSS, card CSS, `.login-submit`, `.login-link-btn`, `.login-link`, `.login-fineprint`, `.full-width`, reduced-motion media query). Anything the shell doesn't own — e.g. `.login-fineprint` for the register-mode password policy note — stays inline via `class="text-caption dora-text-muted"` (already an existing token class).

**Acceptance:** visual — primary submit identical; register toggle now a full amber-gradient button; forgot-password now a ghost button (was fine-print link). Password-policy note under register still readable. Mode toggle preserves the pre-existing `resetErrors()` semantics.

### Step 3 — Migrate `SetupAdminPage.vue` (fixes FU-440)

Same shape as LoginPage. The "One-time setup" badge lives in `#card-head` above the title. Delete the entire `<style scoped>` block (all of `--lp-*` ladder, blob/mascot CSS, `.setup-*` classes, reduced-motion). Submit → `<AuthButton colour="primary" type="submit">`. Setup fineprint retained as `text-caption dora-text-muted` copy.

**Acceptance:** visual — no intended diff vs. today; drift removed.

### Step 4 — Migrate `SplashScreen.vue` + `index.html` pre-mount

`SplashScreen.vue`:

- Template: `<AuthShell backdrop="quiet" mascot="none" variant="full-bleed" role="status" :aria-busy="!error">…</AuthShell>`.
- Splash's own pulsing logo image + `<img :src="error ? offlineSrc : logoSrc">` stays inside the default slot (not shell mascot — the pulse animation is splash-specific).
- Retry → `<AuthButton colour="primary" label="Try again" @click="emit('retry')" />`.
- Delete the `.splash-screen` background/color CSS (shell owns it); keep `.splash-logo`, `.splash-logo--pulse`, `.splash-text`, `.splash-loading-message`, `.splash-error-*`, and `.splash-retry` — these are splash-specific layout inside the shell's slot.
- Force `.splash-screen` internals to override `position: fixed; inset: 0; z-index: 9000` responsibilities into shell wrapper positioning: since AuthShell renders `min-height: 100vh`, splash's `position: fixed; inset: 0; z-index: 9000` needs to move onto `.dora-auth-shell` when consumed by splash. Concrete approach: splash template wraps the AuthShell in `<div class="splash-overlay"><AuthShell>…</AuthShell></div>` where `.splash-overlay { position: fixed; inset: 0; z-index: 9000; }`. Splash is the only surface with an overlay concern; not worth an `AuthShell` prop.

`index.html`:

- Change `#pre-mount-splash { background: #E8F6F3; }` to `background: #1f2647;`.
- Delete the `@media (prefers-color-scheme: dark) { #pre-mount-splash { background: #1B2026; } }` block.
- Add a one-line comment naming this proposal (`/* C-19: shell base #1f2647 to avoid pre-mount → auth handoff flash */`).

**Acceptance:** cold-load reads as a single unified midnight moment. Retry button matches primary auth-button treatment. Cannot-connect error still shows the offline mascot + retry.

### Step 5 — Wrap `WelcomeLayout.vue` + retune `OnboardingStory` glyphs

`WelcomeLayout.vue`:

- Wrap `<q-page-container>` in `<AuthShell backdrop="blobs" mascot="top-right" variant="full-bleed">`. The existing `<q-header>` + toolbar stays *outside* the shell (header sits on the shell's midnight, so its `.welcome-header { color: var(--text-primary); }` needs to switch to `color: var(--auth-shell-text);` — or better, override with a shell-token-aware colour so the header reads over midnight).
- Actually simpler: move the header *inside* the shell so it inherits the shell's force-light context. The shell's `full-bleed` variant leaves the slot uncardified; header + `<q-page-container>` sit stacked over the midnight-with-blobs canvas.
- OfflineBanner and `<router-view>` unchanged.

`OnboardingStory.vue`:

- `.story-glyph--scatter .g` colour → `var(--auth-shell-text-muted, var(--text-muted))` so it degrades cleanly outside the shell context (but always renders inside `AuthShell` in practice).
- `.story-glyph--scatter .g--q` → `var(--auth-shell-blob-2, var(--brand-accent))` (the amber blob colour reads well on midnight).
- `.story-glyph--control .g--big` → `var(--auth-shell-accent-strong, var(--brand-primary))`.
- `.story-pill` → light frosted glass: `background: var(--auth-shell-card-bg); color: var(--auth-shell-text); border: 1px solid var(--auth-shell-card-border);` (falls back to the current tokens outside the shell).

No motion or scene-copy changes.

**Acceptance:** onboarding canvas matches Login. Scene glyphs legible on midnight. Sign-out button (in WelcomeLayout's header) still tappable, still uses BaseButton, colour reads over midnight.

### Step 6 — Fold the four auxiliary pages (fixes FU-441)

For each of `VerifyEmailPage.vue`, `ForgotPasswordPage.vue`, `ResetPasswordPage.vue`, `ConfirmEmailChangePage.vue`:

- Replace `<div class="auth-shell">` with `<AuthShell backdrop="blobs" mascot="none">`.
- Move the icon + h6 + caption stack into `#card-head`.
- Move form / banner content into default slot.
- Move `<q-card-actions>` buttons into `#card-foot`, converting each `<BaseButton variant="primary">` to `<AuthButton colour="primary">` and each `<BaseButton variant="ghost">` to `<AuthButton colour="ghost">`.
- Delete the local `<style scoped>` block entirely (`.auth-shell` + `.auth-card`). Where a page has extra classes like `.full-width`, drop them — `AuthButton` is already full-width by default.
- Keep the inline `BaseDialog` (Resend verification) inside default slot; it's unchanged.

**Acceptance:** four aux pages render with the shared shell. `git grep '\.auth-shell'` returns matches only inside `AuthShell.vue` (as `.dora-auth-shell`). Feedback L16 (Forgot Password matches Login) satisfied.

### Step 7 — Close-gate

Run in order:

1. `git grep -n -- '--lp-\|--setup-'` in `web_app/src/` — must return **zero** results.
2. `git grep -n -- '\.auth-shell'` in `web_app/src/` — must return only the `AuthShell.vue` class token (with its `.dora-auth-shell` prefix).
3. `git grep -n 'login-shell\|login-bg\|login-blob\|login-mascot\|login-card\|login-submit\|login-link\|login-fineprint\|setup-shell\|setup-bg\|setup-blob\|setup-mascot\|setup-card\|setup-submit\|setup-fineprint\|setup-badge' web_app/src/` — must return only `AuthShell.vue` (if any of the class names survive as sub-selectors) or **zero**.
4. `cd web_app && npx vue-tsc --noEmit` — clean (bar the pre-existing FU-434 exactOptional errors on `AdminDataImport.vue`, which are pre-existing and out-of-scope for this unit).
5. `cd web_app && npx quasar build` — succeeds.
6. Cold-load smoke test (manual, folded into `DORA_VERIFY.md`): slow-3G throttle, verify no light-then-midnight flash between pre-mount and shell.

Then update ledgers:

- `CHANGELOG.md` — one entry under the current section: "Extract shared auth-shell (C-19). Login, setup, splash/cannot-connect, onboarding wrapper, and four auxiliary pre-auth pages now share a single `AuthShell` + `AuthButton`. `.login-submit` register-text-too-small feedback resolved."
- `DORA_WORKLOG.md` — new top entry with acceptance results.
- `DORA_FOLLOWUPS.md` → `DORA_FOLLOWUPS_RESOLVED.md` — move FU-440, FU-441, FU-443 with `[RESOLVED]` state notes.
- `DORA_VERIFY.md` — append verify checks (§7 below).

## 5. Verify checklist (goes to `DORA_VERIFY.md §Cross-cutting`)

Browser-verify items owed after this unit ships:

- Login form primary submit still identical to pre-migration (teal gradient, hover lift).
- Register mode toggle reads as a full amber-gradient button, size matches primary.
- Forgot-password reads as a ghost button, hit target obvious.
- Setup-admin (`/setup`) — visual diff should be zero vs. pre-migration.
- Splash bootstrap: cold-load on slow-3G shows no light→midnight flash; pulsing logo still 60fps.
- Cannot-connect: retry button matches primary auth-button treatment.
- Reduced-motion: blobs and mascot both freeze; card enter animation off.
- Onboarding: cinematic scenes render legibly on the midnight canvas (scatter icons visible, brain mascot centred, pills readable).
- Sign-out button in WelcomeLayout still tappable + reads over midnight.
- Verify / Forgot / Reset / ConfirmEmailChange pages all share the login look. Forgot-password matches Login (feedback L16).
- Resend verification dialog opens and submits normally from `VerifyEmailPage`.

## 6. Ripple summary

- **New:** `AuthShell.vue`, `AuthButton.vue` (~330 LOC combined).
- **Rewritten:** `LoginPage.vue` (~-130 LOC net), `SetupAdminPage.vue` (~-160 LOC net), `SplashScreen.vue` (~-20 LOC net), 4× auxiliary pages (~-40 LOC total).
- **Edited:** `WelcomeLayout.vue` (shell wrap), `OnboardingStory.vue` (glyph colours only), `index.html` (pre-mount base + drop OS-switch).
- **Ledgers:** CHANGELOG, DORA_WORKLOG, DORA_FOLLOWUPS + DORA_FOLLOWUPS_RESOLVED, DORA_VERIFY.

Net delta ≈ **-200 LOC** (five duplicated CSS blocks collapsed into one component).

## 7. Rollback plan

Single PR; revert = revert. Each migration step is a discrete commit within the PR so a step can be reverted individually if a specific consumer regresses in review. The two new components are unused in mainline until Step 2b, so a Step-1/2a-only partial revert leaves the tree buildable.

## 8. Engineering-standards close-gate (checkoff at end of unit)

- **R-001 / R-005 (componentise).** Two new primitives; five consumers shrink. Pass.
- **R-002 (theme tokens).** DEC-2 carve-out documented inline; no new raw hex outside the token ladder. Pass.
- **R-003 (single source of truth).** `--lp-*` / `--setup-*` duplications gone; `.auth-shell` name collision gone. Pass.
- **R-004 (framework).** Pure Vue 3 SFC. Pass.
- **R-006 (migrations).** No DB changes. N/A.
- **R-007 (scope discipline).** Onboarding choreography, password policy, configurable-background, `BaseButton` variants — all deliberately left alone. Pass.
- **R-008 (code-style minimalism).** DEC-2 gets one block; no other prose. Pass.
- **R-010 (strong types).** New components typed via `defineProps<>()` unions, not stringly-typed. Pass.
- **R-019 (no magic).** Explicit prop enums, explicit tokens, no clever reflection. Pass.

If any of the above fails at close-gate, the failing rule gets an inline `// R-0NN carve-out: …` comment naming the reason, or a `DORA_FOLLOWUPS.md` finding logged. No silent drift.

## 9. ADR evaluation

This unit does *not* introduce a new recurring pattern that promotes to a
new `R-0NN`. The auth-shell is a single instance of R-001/R-003/R-005
being applied correctly; it doesn't generalise. No ADR added.
