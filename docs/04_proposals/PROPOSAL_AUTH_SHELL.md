# PROPOSAL_AUTH_SHELL — Shared auth-shell styling (C-19)

**Prompt:** `docs/03_prompts/C_big_rock_design_briefs.md` §C-19.
**Written:** 2026-07-02.
**Status:** design proposal — no code. Awaiting user's calls on the open
decisions in §7, then produces an `IMPL_PLAN_AUTH_SHELL.md`.

**Type:** design brief. Folds in retired FU-002 / DEC-2 (the `--lp-*` ladder
revisit).

**Scope in a sentence.** The pre-auth / auth-failure quartet — **splash,
cannot-connect, login, onboarding** — share a moment (user is either not yet
signed in, or the app can't reach the server). Right now only `LoginPage.vue`
carries the intended visual language. This proposal defines a **shared
`AuthShell` component** the four surfaces (plus the auxiliary pre-auth pages
that fell out of scope in the brief) all wrap in, and settles the fate of the
`--lp-*` colour ladder.

---

## 1. TL;DR — the shape

1. Extract **one `AuthShell.vue` component** that owns the animated
   blob backdrop, the floating mascot, the frosted-glass card wrap, the
   reduced-motion wiring, and a coherent set of tokens.
2. **Promote** the 11-token `--lp-*` ladder from `LoginPage.vue` to
   `--auth-shell-*` on the shell. It's already used in two places today
   (LoginPage + a **verbatim copy** in `SetupAdminPage.vue` — R-003 drift
   discovered during this audit); the shell layer is the SSoT.
3. Migrate **five files** to `AuthShell`: `LoginPage`, `SetupAdminPage` (drift
   fix), `SplashScreen` (loading + cannot-connect variant), the `/welcome`
   layout (as a *backdrop* only — the wizard content stays independent), and
   the auxiliary `Verify` / `Forgot` / `Reset` / `ConfirmEmailChange` pages
   (which today collide on a **differently-defined** `.auth-shell` class —
   real bug waiting to bite; §5.5).
4. Align the pre-mount inline splash in `index.html` to the shell's
   midnight base (`#1f2647`), so the cold-load handoff doesn't flash
   light-then-midnight.
5. **Do NOT** re-design the onboarding cinematic scenes here
   (`PROPOSAL_ONBOARDING.md` owns that). The shell wraps them; that's it.

Trade-off summary: this deletes ~130 lines of duplicated CSS and puts a
single token surface behind four+ pages, at the cost of one new component
+ a light per-surface variant matrix. Charter tie-break **Effortless +
Anti-creep** both point the same way — one shell, four masks over it.

---

## 2. Current state — audit before we redesign

The brief lists **four** surfaces. Live-code reading turns up **two visual
families and a naming collision** across **nine** pre-auth files.

### 2.1 File-by-file

| File | Role | Backdrop | Palette source | Notes |
|---|---|---|---|---|
| `web_app/index.html` — `#pre-mount-splash` | Pre-Vue paint (~200ms cold-load flash) | Solid `#E8F6F3` (or `#1B2026` if OS-dark) + pulsing icon | Hardcoded HTML | Cannot use Vue tokens; tracks OS scheme. |
| `web_app/src/components/SplashScreen.vue` | Post-mount splash + **cannot-connect** error variant (single component, two states via `error` prop) | Theme-aware (`--q-page` / `--surface-component`) — **no blobs** | Theme tokens | Rendered by `App.vue` while `authStore` bootstraps. |
| `web_app/src/pages/LoginPage.vue` | `/login` route | **Blobs + mascot + frosted card** on deep-midnight base, force-light | **`--lp-*` ladder (11 tokens)** | The one screen the brief calls "designed for it." |
| `web_app/src/pages/SetupAdminPage.vue` | `/setup` — first-admin bootstrap | **Same blob backdrop as Login** | **Verbatim copy of `--lp-*` ladder** (`--setup-*` selector names, identical values) | **R-003 drift** — the second copy of a private ladder is exactly the risk `--lp-*` was left "private" to avoid. |
| `web_app/src/layouts/WelcomeLayout.vue` | `/welcome` layout for onboarding | Standard theme background; mini header with mascot + sign-out; OfflineBanner | Standard theme tokens | Wraps `WelcomeWizard.vue` and its cinematic `OnboardingStory.vue`. |
| `web_app/src/pages/onboarding/WelcomeWizard.vue` | The wizard steps | Sits on `WelcomeLayout`'s theme-standard background | Standard tokens | Uses `dora-text-*`, `--brand-*`, `--surface-*`. |
| `web_app/src/pages/onboarding/OnboardingStory.vue` | Cinematic scenes preceding setup | Same theme background; scene glyphs use `--brand-accent` / `--brand-primary` on `--surface-page` | Standard tokens | Motion/scene choreography owned by `PROPOSAL_ONBOARDING.md`. |
| `web_app/src/pages/VerifyEmailPage.vue` | `/verify-email` | **Plain** — `min-height:100vh` centred, `--surface-page` bg, no blobs, no mascot | Standard tokens | **Class name `.auth-shell` — collides with our proposed component.** |
| `web_app/src/pages/ForgotPasswordPage.vue` | `/forgot-password` | Same plain shell | Standard tokens | Same class collision. Feedback L16 explicitly asks it match Login. |
| `web_app/src/pages/ResetPasswordPage.vue` | `/reset-password` | Same plain shell | Standard tokens | Same class collision. |
| `web_app/src/pages/ConfirmEmailChangePage.vue` | `/confirm-email-change` | Same plain shell | Standard tokens | Same class collision. |

### 2.2 What the audit revealed that the brief didn't anticipate

- **The brief mentions four surfaces; there are actually nine pre-auth
  files.** The `Verify` / `Forgot` / `Reset` / `ConfirmEmailChange` /
  `SetupAdminPage` set was implicitly out of scope but is directly
  affected — either we fold them in or we consciously leave them looking
  different.
- **Naming collision is live, right now.** Four pages define
  `.auth-shell` in a scoped `<style>` block as a plain centred container
  with `--surface-page` background. If we ship an `AuthShell.vue`
  component that renders `<div class="auth-shell">`, we get a real cascade
  overlap (scoped styles limit blast radius but the class name in the
  DOM still reads misleadingly). The **shell's root class must be
  something else** (recommend `.dora-auth-shell`), and the four affected
  pages get folded in or explicitly renamed.
- **`--lp-*` is already duplicated.** The retired FU-002 / DEC-2 kept the
  ladder "private on purpose"; `SetupAdminPage` copying the ladder
  verbatim is the exact drift that "keep private" was supposed to
  prevent. This alone flips the recommendation to **promote**.
- **Splash + cannot-connect are the same component** with an `error`
  prop. Treat them as one surface with a mode toggle, not two.

---

## 3. Feedback anchors (from
`docs/02_feedback/Feedback _ Fixes - as of [06-Jun-2026].md`)

| Feedback (surface, quoted phrase) | What it asks for | This proposal addresses in |
|---|---|---|
| §SPLASH — "would be better if it shared the same colouring as the login screen" | Splash + Login share visual language | §5.3, §5.1 |
| §CANNOT CONNECT — "Same styling as login, splash, etc., ensuring to keep the logo/dora pic animation and location/placement" | Cannot-connect matches Login/Splash; mascot animation preserved | §5.3 (mascot lives in the shell; animation is a shell primitive) |
| §LOGIN — "Forgot password screen should match styling of login screen" | Forgot password matches Login | §5.5 (auxiliary pages folded in) |
| §LOGIN — "Register text is too small, make it a button same as sign in but another colour, maybe gradient of the dora yellow (match gradient style of login button); 'have an account, sign in' should also be a button with same styling" | Preserve the current LP submit-button size/gradient/shadow as the reference; extract into a dedicated `AuthButton.vue` that composes `BaseButton`; expose `primary` (teal, current LP look), `secondary` (amber gradient — "dora yellow"), `ghost` (flat with hit target). Register/mode-toggle → `secondary`; Forgot → `ghost`. | §5.8 (card-internal button set + `AuthButton` extraction — new) |
| §ONBOARDING — "Should be same styling as login screen" | Onboarding shares Login's canvas | §5.4 |

All five bullets are directly addressed; nothing is punted.

### 3.1 Wave-A dependencies (cross-cutting styling discipline)

The brief mandates honouring Wave A's cross-cutting standards. Making
that ripple explicit so the impl-plan doesn't silently drift:

- **A1 (theme token-compliance).** The shell's force-light
  `color-scheme` + raw-hex `--auth-shell-*` ladder is a **documented
  carve-out** from A1's "all styling reads from theme tokens" rule.
  Rationale: pre-auth surfaces render before / independent of the
  user's theme choice; letting `--data-theme-*` tokens flow through
  would produce dark-mode midnight-on-midnight illegibility. The
  carve-out is captured as DEC-2 next to the tokens (§5.2) so a
  future A1 audit doesn't try to "fix" it.
- **A2 (standard button / toolbar).** The shell does NOT extend
  `BaseButton` with new gradient variants — the gradient/shadow/hover
  treatment is deliberately contextual (see §5.8) and gets its own
  `AuthButton.vue` that composes `BaseButton` internally. A2's
  standard-toolbar-button contract stays generic; auth surfaces get
  their own paired primitive. No bespoke `.login-submit` /
  `.login-link-btn` classes survive extraction. Retry button on the
  splash / cannot-connect variant also uses `AuthButton`.
- **A6 (text size).** The register-text-too-small symptom disappears
  once the toggle becomes a `BaseButton` (min-height and typography
  come from A6-compliant tokens). No local font-size overrides in
  the shell.
- **A3 (standard modal).** No modals in the shell itself; the
  `Resend verification` dialog inside `VerifyEmailPage` continues to
  use `BaseDialog` (unchanged by this proposal).
- **A5 (loading skeleton).** Splash uses the shell but keeps its
  pulsing-logo idiom rather than the row-shaped skeleton (a
  full-screen bootstrap gate is a different loading model to a
  data-fetch skeleton — A5 doesn't apply here).

---

## 4. Charter + engineering-rules check

- **R-003 (single source of truth).** The `--lp-*` ladder is
  duplicated. Every future pre-auth surface would fork a third copy
  without an owned home. → promote.
- **R-005 (componentisation-first).** Three files today re-implement the
  midnight+blob+mascot+card pattern (LoginPage, SetupAdminPage — and if
  we let it drift, splash/cannot-connect). → one component.
- **R-002 (theme-tokens-only, no raw hex).** `--lp-*` are explicit
  raw-hex custom properties **deliberately** carved out of the general
  theme (DEC-2) because the auth-shell is force-light regardless of
  system theme. Promoting them to `--auth-shell-*` keeps that carve-out
  but *documents* it at the shell layer with a comment naming DEC-2,
  rather than a private hex ladder hiding at the bottom of `LoginPage`.
- **P10 Anti-creep.** Do not build the "background configurable
  globally" feature the original spec floated (§8) — out of scope.
- **P1 Effortless.** The user's four pre-auth surfaces feel like one
  place. One shell, one moment.
- **P11 Fast.** GPU-friendly blobs (transform/opacity only), respect
  `prefers-reduced-motion`, tight motion budget — all already in
  LoginPage; the shell inherits them.

---

## 5. The proposed `AuthShell` component

### 5.1 API (Vue 3 SFC, TS)

```
<AuthShell
  :backdrop="'blobs' | 'quiet' | 'none'"    // default 'blobs'
  :mascot="'top-right' | 'top-centre' | 'none'"  // default 'top-right'
  :force-light="true | false"               // default true (see §5.2)
  variant="card | full-bleed"               // default 'card'
  role="main"                               // default 'main'
>
  <template #card-head>...</template>       // title, sub, badges
  <template #default>...</template>         // main content (form / scene / status)
  <template #card-foot>...</template>       // links, alt-mode toggle
</AuthShell>
```

Slots (rather than a rigid `title`/`sub`/`fields` prop shape) because
the four surfaces have genuinely different content — a login form, a
one-time-setup form, a status message with retry, a wizard's step rail
— and enumerating those as props would grow. R-005 says componentise
the *pattern*, not force-fit a single content model.

### 5.2 The token contract

Promote the 11-token ladder to the shell layer:

```
/* AuthShell.vue — scoped */
.dora-auth-shell {
  /* R-002 DEC-2 carve-out: this shell renders before or during auth
     state, so it deliberately does NOT read from --text-primary or
     any --data-theme-* tokens (they can flip dark before the user
     authenticates). Force light, hex-defined, documented HERE
     (previously duplicated as --lp-* / --setup-*). */
  --auth-shell-bg-base:      #1f2647;   /* deep midnight under the blobs */
  --auth-shell-blob-1:       #ff7ad9;   /* magenta */
  --auth-shell-blob-2:       #f5c462;   /* Dora amber */
  --auth-shell-blob-3:       #4cd5b7;   /* mint */
  --auth-shell-card-bg:      rgba(255, 255, 255, 0.94);
  --auth-shell-card-border:  rgba(255, 255, 255, 0.60);
  --auth-shell-text:         #1f2330;
  --auth-shell-text-muted:   #5b6173;
  --auth-shell-accent:       #006a80;
  --auth-shell-accent-strong:#17b073;
  --auth-shell-shadow:       0 30px 80px -30px rgba(20, 12, 50, 0.55);

  color-scheme: light;   /* input controls pick up light UA styling */
  ...
}
```

Overrides remain trivial — a surface can restyle just the accents by
setting `--auth-shell-accent-*` inline. But there's a *single* place to
change the whole ladder, and the audit trail (why raw hex, why
force-light) sits next to it instead of buried in `LoginPage.vue:216`.

### 5.3 Backdrop variants

The three surfaces put different demands on the backdrop:

- **`blobs`** — the LoginPage design. Three animated colour blobs with
  22–30s ease-in-out drifts, `filter: blur(80px)`, `mix-blend-mode:
  screen`, `will-change: transform`. Reduced-motion locks position and
  softens opacity. Used by **login**, **setup-admin**, **onboarding**,
  and the auxiliary pages.
- **`quiet`** — same midnight base, blobs held at reduced opacity and
  motion-frozen. For **splash / cannot-connect**: the blobs cost paint
  cycles during bootstrap where we're competing for CPU with the boot
  probe. Recommendation: `quiet` on splash so the shell reads as
  visually continuous with login (feedback anchor) but doesn't spend
  animation budget before the app has proved it can reach the server.
- **`none`** — flat `--auth-shell-bg-base`. Escape hatch for a future
  surface (e.g. a status page) that needs the palette but not the
  motion.

**Note on splash bootstrap.** SplashScreen renders *before*
`authStore.isBootstrapped` — so it must not depend on any store, any
theme service, or any dynamic import that isn't already loaded to
paint. AuthShell is a pure-CSS + Vue-template component with no runtime
dependencies; safe to load into the entry chunk.

### 5.4 Per-surface variant matrix

| Surface | `backdrop` | `mascot` | `variant` | Content in default slot |
|---|---|---|---|---|
| `LoginPage.vue` (`/login`) | `blobs` | `top-right` | `card` | Sign-in / register form |
| `SetupAdminPage.vue` (`/setup`) | `blobs` | `top-right` | `card` | First-admin form + one-time-setup badge in `#card-head` |
| `SplashScreen.vue` (bootstrap) | `quiet` | `top-centre` (uses pulsing logo instead of bob) | `full-bleed` | Pulsing logo (loading) or offline logo + `error` + retry (cannot-connect) |
| `WelcomeLayout.vue` wrapping `/welcome` | `blobs` (via `<AuthShell>` around `<q-page-container>`) | `top-right` (subordinate — story is the focal point) | `full-bleed` | The existing header + step rail + `<router-view>` — content stack is unchanged, only the backdrop moves. |
| `VerifyEmailPage.vue` / `ForgotPasswordPage.vue` / `ResetPasswordPage.vue` / `ConfirmEmailChangePage.vue` | `blobs` | `none` (they're compact status/form cards, mascot fights the layout) | `card` | Existing card content, unchanged |

**Onboarding — the interaction with the cinematic scenes.** The
`OnboardingStory` scenes today draw `--brand-accent` / `--brand-primary`
glyphs on `--surface-page`. On top of midnight-with-blobs those need
re-tuning:

- Scene glyphs currently sit on light surface — on midnight they read as
  bright specks. Recommend they promote to a **light-on-dark** treatment
  when inside the shell (a `--auth-shell-content-color` used as the
  glyph fill, and pills switch from bordered-light-card to
  frosted-light-glass matching the card variant).
- **Do NOT re-litigate scene choreography here.** Motion, autoplay,
  scene copy, and reduced-motion pathways are `PROPOSAL_ONBOARDING`'s
  job (§2.4). This proposal only:
  1. wraps the outermost layout in the shell,
  2. exposes the palette tokens the scenes need to re-tune against,
  3. documents the interplay so no one reads them in isolation.

### 5.5 The `.auth-shell` naming collision

**Current live bug in the making.** Four pages define
`.auth-shell` in a **scoped** style block:

```
.auth-shell {
    min-height: 100vh; display: flex; align-items: center; justify-content: center;
    padding: 24px; background: var(--surface-page);
}
```

Scoped styles limit CSS scope, but the DOM class name is the same and
future authors reading `<div class="auth-shell">` in Verify vs. our new
`AuthShell.vue` will confuse the two. Fix: **the shell component's root
uses `.dora-auth-shell`** (project-prefixed, matches `dora-text-*`,
`dora-bg-*` conventions elsewhere in the codebase), and the four pages
fold into `AuthShell` (dropping their local class + style block
entirely).

### 5.6 Pre-mount splash (index.html)

The inline `#pre-mount-splash` in `index.html` paints before Vue mounts,
so it cannot consume Vue tokens. Today it tracks OS colour scheme
(`#E8F6F3` light, `#1B2026` dark). Once `AuthShell` takes over on Vue
mount, the pre-mount light→shell midnight handoff will visibly flash.

**Recommendation:** hardcode the pre-mount background to
`#1f2647` (= `--auth-shell-bg-base`) and drop the OS-scheme switch.
Cold-load reads as a single unified midnight moment. Add a comment
naming this proposal so the next author knows why the OS switch was
removed.

Cost: dark-mode users see a fractionally *darker* pre-mount than the
themed app; light-mode users see a distinctly darker pre-mount than
what follows *inside* the app. Both are one screen, one moment,
consistent with the auth-shell aesthetic across the pre-auth quartet.

### 5.7 Reduced-motion + a11y

- `prefers-reduced-motion` freezes blob drifts, mascot bob, and card
  enter animation — same as today's LoginPage.
- Shell root: `role="main"`, override via prop for splash
  (`role="status" aria-busy="true"`).
- Force-light color-scheme means the shell's `q-field` labels are
  readable regardless of themeService state (already done in
  LoginPage via `:deep(.q-field__native)` etc.; move that block into
  the shell so it's not re-derived at every consumer).
- Focus outlines: shell exposes `--auth-shell-focus-ring` (recommend
  the accent-strong colour) so `q-input` / `BaseButton` on top look
  consistent across surfaces.

### 5.8 The card's internal button set (feedback §LOGIN)

**Design intent — user-stated 2026-07-02.** The current
`LoginPage.vue` submit-button size + gradient is the reference we're
preserving, not redesigning. The bespoke `.login-submit` styling that
today reads:

```
size: lg + full-width;
background: linear-gradient(135deg, var(--lp-accent-strong), var(--lp-accent));
font-weight: 600; letter-spacing: 0.02em;
border-radius: 12px;
box-shadow: 0 10px 24px -10px rgba(0, 106, 128, 0.55);
hover: translateY(-1px) + shadow bump;
```

… is *good* and stays. The problem is only that (a) it's an
`ad-hoc class`, not a reusable primitive, and (b) the register/forgot
elements next to it don't share the treatment (register = tiny ghost
text, forgot = fine-print `<router-link>`) — feedback: "make them
buttons in the same style, different colour".

### Extract `AuthButton.vue` — dedicated component, not a BaseButton variant

**Component location:** `web_app/src/components/AuthButton.vue`
(sibling of `AuthShell.vue`).

**Why its own component, not a `BaseButton variant="gradient-*"`:**
this look is deliberately *contextual* — it should only appear inside
the auth-shell moment. Adding `gradient-primary` / `gradient-secondary`
variants to `BaseButton` invites the treatment to leak (someone
decides the gradient looks great on the dashboard hero) and re-drifts
the styling once it's used in unrelated places. Keeping it in a
dedicated `AuthButton` that pairs with `AuthShell` matches R-005
(componentise the pattern) and R-010 (scope discipline). Trade-off:
one extra component file; no runtime cost.

**Composition — `AuthButton` wraps `BaseButton`.** Rather than
re-implementing loading state / disabled / size / `type="submit"`
plumbing, `AuthButton` renders a `BaseButton` internally and layers
the gradient + shadow + hover on top via `:deep(.q-btn)` overrides
scoped to the component. Base behaviour flows through untouched.

**API:**

```
<AuthButton
  colour="primary" | "secondary" | "ghost"    // default 'primary'
  type="submit" | "button"                   // passes through to BaseButton
  size="lg"                                   // pinned; not exposed (see below)
  :loading="..."
  :disabled="..."
  :label="..."
  @click="..."
/>
```

**Colours:**

| `colour` | Treatment |
|---|---|
| `primary` | Current LP submit — teal gradient (`--auth-shell-accent-strong → --auth-shell-accent`), heavy shadow, hover translate. |
| `secondary` | Amber gradient — feedback names "gradient of dora yellow". Uses `--auth-shell-blob-2` (Dora amber) → a slightly warmer amber tone (a new `--auth-shell-accent-amber-strong` token). Same shape, same shadow, second colour. |
| `ghost` | Flat transparent with `--auth-shell-accent` text; no gradient, no shadow, keeps a `border-radius: 12px` hit target so it visually reads as a button (fixes "forgot password is fine print" feedback). |

**Size is pinned deliberately** — the whole point is
consistency-of-hit-target-inside-the-shell. If a future consumer needs
a smaller button they shouldn't reach for `AuthButton` at all.

### The three consumers on the Login card

Structurally the card foot becomes a stacked button set:

1. **Primary submit** — `<AuthButton colour="primary" type="submit" :label="mode === 'login' ? 'Sign In' : 'Create Account'" :loading="submitting" />`. Kills the private `.login-submit` class.
2. **Mode toggle** — `<AuthButton colour="secondary" :label="mode === 'login' ? 'Need an account? Register' : 'Have an account? Sign in'" @click="toggleMode" />`. Kills the tiny-ghost text. Amber gradient per feedback.
3. **Forgot password** — `<AuthButton colour="ghost" label="Forgot password?" @click="router.push('/forgot-password')" />` (only rendered when `mode === 'login'`). Kills the fine-print `<router-link>`.

The card foot reads as three obviously-tappable buttons of matching
size, with primary → secondary → ghost visual hierarchy. Motor-target
consistency; A6-compliant sizes without local font-size overrides.

### Same treatment on SetupAdmin + aux pages

- `SetupAdminPage` — the "Create the first admin account" submit
  becomes `<AuthButton colour="primary" type="submit">`.
- `ForgotPasswordPage` — "Send reset link" becomes primary; "Back to
  sign in" becomes ghost.
- `ResetPasswordPage`, `VerifyEmailPage`, `ConfirmEmailChangePage` —
  each surface's actions use `AuthButton` colour variants matching the
  hierarchy above.

No consumer of `AuthButton` lives outside `AuthShell`. Enforced by
convention + a lint-friendly comment in `AuthButton.vue`'s script
block; if it needs harder enforcement later, an `inject`-based check
against a shell-provided key would fail loudly.

### Why not just fix the register/forgot styling in-place on LoginPage?

We could. But every other pre-auth surface then has to duplicate the
choice — five files re-declaring "same button style as login", which
is exactly the drift the shell itself is fixing for the *backdrop*.
One component; four consumers; no repetition.

---

## 6. Migration plan

Every step is reversible; each ends with a compilable, visibly-identical
app before the next runs.

| # | Step | Files touched | Result |
|---|---|---|---|
| 1 | Create `web_app/src/components/AuthShell.vue` with the API in §5.1 and tokens in §5.2. Nothing consumes it yet. | `+1` new file | Unused component in tree; no regression risk. |
| 2a | Create `web_app/src/components/AuthButton.vue` (composes `BaseButton`; `primary` / `secondary` / `ghost` colours per §5.8). Nothing consumes it yet. | `+1` new file | Unused component in tree; no regression risk. Primary colour renders identically to today's `.login-submit`. |
| 2b | Migrate `LoginPage.vue` to `<AuthShell backdrop="blobs" mascot="top-right">`. Delete `--lp-*` ladder + blob CSS. Rework the card foot to the three-`AuthButton` stack from §5.8. | `LoginPage.vue` (-~130 lines) | Visual diff: primary submit identical; register-mode toggle now a full amber-gradient button; forgot-password now a ghost button (was fine-print link). |
| 3 | Migrate `SetupAdminPage.vue` — same shape, `card-head` slot carries the one-time-setup badge. Delete the duplicated `--setup-*` ladder + blob CSS. **This step is the R-003 drift fix.** | `SetupAdminPage.vue` (-~130 lines) | Visual diff: none intended. |
| 4 | Migrate `SplashScreen.vue` to `<AuthShell backdrop="quiet" mascot="none" variant="full-bleed">`. Move the pulsing logo + retry into the default slot; retry becomes `<AuthButton colour="primary">`. | `SplashScreen.vue` | Visual change: splash now on midnight+quiet-blobs instead of theme-surface; retry gets the auth-button treatment. |
| 4a | Update `index.html`'s `#pre-mount-splash` to hardcoded `#1f2647`; drop OS-scheme switch. | `index.html` | Cold-load matches step 4's splash. |
| 5 | Wrap `WelcomeLayout.vue` in `<AuthShell backdrop="blobs">`. Re-tune the `OnboardingStory` scene glyphs to sit on midnight (light glyph fills, frosted pills). Coordinate with `PROPOSAL_ONBOARDING` — no scene choreography changes. | `WelcomeLayout.vue`, `OnboardingStory.vue` (glyph colours only) | Onboarding canvas matches Login. |
| 6 | Fold auxiliary pages into `<AuthShell backdrop="blobs" mascot="none">`. Drop the four `.auth-shell` + `--surface-page` blocks; content stays inside the shell card. | `VerifyEmailPage.vue`, `ForgotPasswordPage.vue`, `ResetPasswordPage.vue`, `ConfirmEmailChangePage.vue` | Naming collision gone; Forgot Password matches Login (feedback L16). |
| 7 | End-of-work: engineering-standards close-gate. Confirm no `--lp-*` / `--setup-*` survive; no `.auth-shell` class outside `AuthShell.vue`; the DEC-2 rationale is documented on `AuthShell` not scattered. Verify list appended to `DORA_VERIFY.md`. | — | Ship-ready. |

Estimated size of the resulting `IMPL_PLAN`: ~450 LOC net delete
(five duplicated CSS blocks) + ~250 LOC new component + slot markup at
each consumer. Net LOC ≈ -200.

---

## 7. Open decisions — for you

| # | Decision | Recommendation | Trade-off if we go the other way |
|---|---|---|---|
| D1 | Blob palette per screen — same across all four, or per-surface? | **Same across all four** (single `--auth-shell-*` ladder). Per-surface divergence is what caused SetupAdminPage's drift. | If splash needs a distinctly *quieter* palette to read as "loading" not "welcome", we still have the `backdrop="quiet"` mode reducing opacity + freezing motion — a *palette* fork isn't needed to signal state. |
| D2 | Does Splash / cannot-connect adopt the blob backdrop at all? | **Yes**, via `backdrop="quiet"` (blobs static, low opacity). Directly answers the feedback anchor "Same styling as login". | The alternative is `backdrop="none"` — flat midnight — which is quieter but visibly breaks the "shared moment" feedback ask. |
| D3 | Does onboarding wrap in the shell, or is the shell login-only + splash-only? | **Wrap in the shell.** Onboarding feedback explicitly asks "Should be same styling as login screen." `WelcomeLayout` stays as the layout (keeps its header + OfflineBanner), the shell provides its backdrop. | Keeping onboarding separate leaves the "canvas" feedback bullet unanswered — no. |
| D4 | Do the auxiliary pre-auth pages (Verify, Forgot, Reset, ConfirmEmailChange) get folded in? | **Yes.** The name collision is a real (small) bug; Forgot Password has an explicit feedback ask to match Login; the other three are the same conceptual moment. | Leaving them plain-`--surface-page` means Forgot-password ships broken against feedback, and the collision keeps festering. |
| D5 | Where does the palette live — component-scoped, `:root`, or a `_auth-shell.scss` in the theme layer? | **Component-scoped in `AuthShell.vue`.** Keeps the DEC-2 carve-out rationale physically next to the tokens; the shell is the only consumer. | `:root` promotes them to global tokens where nothing outside the shell should touch them — cleaner theoretically, but tempts the same drift `--lp-*` was hiding from. |
| D6 | Does the mascot live in the shell (positional prop) or as a slot each surface fills? | **Prop.** The mascot placement + bob animation is *identical* everywhere it appears today; positioning per-surface is `top-right` / `top-centre` / `none`. Slot-based over-generalises. | If a future surface wants a totally different hero image, add a `#mascot` slot then; anti-creep says defer. |
| D7 | Pre-mount `#pre-mount-splash` — hardcode midnight, or leave OS-scheme? | **Hardcode midnight** (`#1f2647`). Cold-load reads as a single moment. | Preserving the OS switch honours "match user's theme even for 200ms" but visibly breaks the handoff. |
| D8 | The original spec floated "I can change the background of the landing/login page globally." Fate? | **Out of scope for C-19.** Log as a `keep` note under the from-original-spec section but do **not** build the config surface — one shell, one palette; user-configurable pre-auth backgrounds are the exact P10 Anti-creep target. | Building it now grows the surface area 2× for a want that has zero feedback demand. |
| D9 | Dedicated `AuthButton.vue` vs adding gradient variants to `BaseButton`? | **Dedicated `AuthButton.vue`** (user-affirmed 2026-07-02). Composes `BaseButton`; keeps the gradient/shadow treatment scoped to auth surfaces so it can't leak onto dashboard/random pages. | BaseButton variants get consumed everywhere by design; adding gradient variants there invites the treatment out of the auth moment (drift target). Dedicated component costs one small file and pays for itself the first time someone tries to reuse the styling out-of-context and the naming stops them. |
| D10 | The amber "gradient of the dora yellow" for secondary — does the shell need a new `--auth-shell-accent-amber-strong` token or does the existing `--auth-shell-blob-2` (amber) blob colour reach far enough? | **Add one token** (`--auth-shell-accent-amber-strong`) so the gradient has two-stop depth like the primary (mint → dark teal). Blob-2 is one colour; a gradient needs a partner tone. | Using blob-2 alone yields a flat-amber button, not a gradient — visually mismatched against the primary's depth. |

---

## 8. From the original spec

`docs/00_original_spec/Feature Boards/User & Global Options.md` includes:

- ☐ *I see a landing/login page when I first navigate to Dora.* — **keep**;
  aligns with the shell + `LoginPage` today.
- ☐ *I can change the background of the landing/login page globally.* —
  **consider (deferred, out of C-19).** The spec is from before the
  `--lp-*` ladder existed. A user-configurable pre-auth background is a
  distinct feature (needs a settings UI, admin-scoped, persistence in
  `AppSetting`) that doesn't unblock any current feedback. If it comes
  back on the roadmap it'd sit as a new `R-cross`-style config, not as
  part of the shell itself.
- ☐ *I can choose to stay logged in.* — orthogonal to this proposal; the
  session-lifetime work is a separate follow-up (unrelated to shell
  styling).

Source is ~2 years old (pre-charter, pre-feedback); charter, reconciled
plan, and current feedback override where they disagree.

---

## 9. Ripple

- **`web_app/src/components/AuthShell.vue`** — new (~250 LOC incl.
  scoped tokens, transitions, reduced-motion, force-light input styles).
- **`web_app/src/components/AuthButton.vue`** — new (~80 LOC).
  Composes `BaseButton`; primary/secondary/ghost colours. Deliberately
  scoped-in-name to the auth surfaces.
- **`web_app/src/pages/LoginPage.vue`** — thin consumer; -130 lines net.
- **`web_app/src/pages/SetupAdminPage.vue`** — thin consumer; -130 lines
  net; drift removed.
- **`web_app/src/components/SplashScreen.vue`** — refactor onto shell;
  keep the pulsing-logo + retry logic in the slot.
- **`web_app/index.html`** — hardcode `#1f2647` for the pre-mount splash;
  drop the `prefers-color-scheme: dark` block.
- **`web_app/src/layouts/WelcomeLayout.vue`** — wrap `<q-page-container>`
  in `<AuthShell backdrop="blobs">`; retune header colours to
  auth-shell tokens if needed.
- **`web_app/src/pages/onboarding/OnboardingStory.vue`** — glyph fill
  colours only. Coordinate with `PROPOSAL_ONBOARDING`.
- **`web_app/src/pages/VerifyEmailPage.vue`,
  `ForgotPasswordPage.vue`, `ResetPasswordPage.vue`,
  `ConfirmEmailChangePage.vue`** — thin consumers; delete each local
  `.auth-shell` block.
- **`docs/00_DOC_GRAPH.md`** — new C-19 section (added by this
  session's worklog step).
- **`DORA_VERIFY.md`** — visual-verify checklist (per surface) appended
  when the impl-plan runs.

No backend changes. No API changes. No store changes. No test
infrastructure changes — this is purely presentation.

Downstream proposals whose interlock changes: `PROPOSAL_ONBOARDING`
(§3.1 and §2.4 remain authoritative for cinematic scenes; this
proposal fills the "auth-shell / C19" placeholder those sections
reference).

---

## 10. Feedback coverage table

| Feedback bullet (surface, quoted) | Where addressed | Notes |
|---|---|---|
| §SPLASH — "would be better if it shared the same colouring as the login screen" | §5.3 (`backdrop="quiet"`), §5.4 (Splash row) | Delivered by the shared shell; splash uses the quieter blob variant. |
| §CANNOT CONNECT — "Same styling as login, splash, etc., ensuring to keep the logo/dora pic animation and location/placement" | §5.4 (SplashScreen row — the same component covers cannot-connect), §5.7 (mascot animation preserved as a shell primitive) | The `error` variant of Splash keeps the pulsing logo animation; the shell owns the animation so it never drifts. |
| §LOGIN — "Forgot password screen should match styling of login screen" | §5.4 (auxiliary pages row), §5.5 (naming collision fix), §6 step 6 | Fixed by folding all four aux pages into the shell. |
| §LOGIN — "Register text is too small … same as sign in but another colour (gradient of dora yellow); 'have an account, sign in' should also be a button" | §5.8, §6 step 2 | Current LP submit-button styling is preserved as the reference. Extracted into a dedicated `AuthButton.vue` (composes `BaseButton`) with `primary` / `secondary` (amber) / `ghost` colours. Register/forgot become real buttons at the same visual weight; treatment stays scoped to auth surfaces. |
| §ONBOARDING — "Should be same styling as login screen" | §5.4 (WelcomeLayout row), §6 step 5 | Onboarding canvas becomes the shell backdrop; scene choreography stays with `PROPOSAL_ONBOARDING`. |

No pre-auth feedback bullet is left uncovered by this proposal, and no
adjacent bullet (password policy, dashboard skip banner, wizard copy
errors) is silently pulled in — those live elsewhere on purpose.

---

## 11. Notes for the future `IMPL_PLAN_AUTH_SHELL.md`

- Include the visual-verify list per surface (login form still readable,
  splash pulses at 60fps, blobs freeze under reduced-motion, mascot
  placement identical to pre-migration screenshots, auxiliary pages
  no longer collide on `.auth-shell`).
- Add a checklist item for `git grep -n 'lp-\|--setup-\|\.auth-shell'` at
  the end — the successful cleanup should return nothing outside
  `AuthShell.vue`.
- Cover the pre-mount handoff explicitly: cold-load the app with slow
  3G throttle, confirm no light-then-midnight flash.
- Fold the migration into a single PR — the drift removal + naming
  collision fix are load-bearing together; splitting risks a partial
  state where some pages have the collision-safe shell and others
  don't.
