# Platform builds audit (FU-327)

**Status:** **complete; report only — no code changes.**
**Date / task:** 2026-06-30 (FU-327, originally FU-288 before the
2026-06-29 renumber). User asked: "properly set up builds for all
platforms we can deliver to; beyond FU-327, audit what we can deliver
to and identify compat/incompat + workarounds."

This document is the audit report. FU-327 itself stays open as the
scoped build-script work; the broader gaps surfaced here are logged as
new follow-ups (see § Follow-ups spun off below).

## TL;DR

- **Tier 1 (already shipping or one config-flip away):** Linux desktop
  bundle + AppImage; Docker self-host; **PWA** (config is complete, but
  the build mode is never actually selected — see new FU-NEW-PWA).
- **Tier 2 (FU-327's named scope):** Windows `.bat` and macOS `.sh`
  build scripts mirroring `packaging/build-linux.sh`. The
  `dora.spec`, `fetch_piper.py`, and `fetch_default_voice.py` are all
  already platform-aware; only the orchestration is missing.
- **Tier 3 (possible but expensive):** iOS / Android via Capacitor —
  Quasar scaffold is there, backend CORS already allows
  `capacitor://localhost`, but ship as **PWA first** (covers 80% of
  the value at 0% of the App Store cost).
- **Tier 4 (skip):** Electron (PyInstaller already does this job
  better for an app with a Python backend); Cordova; BEX.
- **The real blocker isn't a build script — it's the dead CI.** Every
  workflow in `.github/workflows/` is commented out (see § CI status
  below). Until CI runs, every release ships hand-built and untested.
  **However the user has explicitly decided to keep CI disabled
  during rapid Claude-driven development to avoid burning the
  GitHub Actions free-tier allowance.** This audit recommends a
  matrix once CI is back on; it does *not* recommend turning it back
  on now.

## Inventory — what packaging exists today

| Asset | Status | Location |
|---|---|---|
| Linux desktop bundle script | ✅ Working | [packaging/build-linux.sh](../../packaging/build-linux.sh) |
| Linux AppImage wrap | ✅ Working | [packaging/appimage/build-appimage.sh](../../packaging/appimage/build-appimage.sh) |
| PyInstaller spec (platform-agnostic) | ✅ Working | [dora.spec](../../dora.spec) |
| Piper binary fetcher (linux/win/macos all wired) | ✅ Working | [packaging/fetch_piper.py](../../packaging/fetch_piper.py) |
| Default-voice fetcher | ✅ Working | [packaging/fetch_default_voice.py](../../packaging/fetch_default_voice.py) |
| Docker image (monolithic Flask + nginx) | ✅ Working | [Dockerfile](../../Dockerfile), [compose.yml](../../compose.yml) |
| PWA manifest + Workbox SW (config) | ✅ Fully wired | [web_app/quasar.config.ts:226-347](../../web_app/quasar.config.ts) |
| PWA — actually built? | ⚠️ **No** — `npm run build` runs SPA mode, not `quasar build -m pwa` | — |
| Windows `.bat` / `.ps1` build script | ❌ Missing | — |
| macOS `.sh` build script (arm64 + x86_64) | ❌ Missing | — |
| Electron / Capacitor / Cordova / BEX modes | ⚠️ Quasar config stanzas only, no `src-*` dirs | [web_app/quasar.config.ts:349-407](../../web_app/quasar.config.ts) |
| CI workflows | ⚠️ **Intentionally disabled** (user policy — GH free-tier preservation during rapid Claude dev) | [.github/workflows/ci.yml](../../.github/workflows/ci.yml), [release.yml](../../.github/workflows/release.yml) |

## Deliverable targets — reachability + cost

### Tier 1 — already shipping (or one script away)

**1. Linux desktop bundle (`AppImage` / `dist/Dora/`)**

Works end-to-end. PyInstaller one-folder + optional AppImage wrap.
Piper fetched per-arch via `fetch_piper.py`.

**Notable wart:** pywebview/GTK was abandoned during build hardening —
the "desktop app" actually launches the user's default browser
pointed at a local Flask server, not a native pywebview window. See
[desktop_app.py:209-217](../../desktop_app.py). Functionally OK; less
native-feeling than a real WebView, but reliably packageable across
distros. Revisiting GTK bundling is its own task and not needed for
shipping.

**2. Docker / self-host (Linux x86_64 + arm64 via buildx)**

[Dockerfile](../../Dockerfile) is mature. Defaults to SQLite for the
zero-dependency self-host path; `DORA_DB_URL` switches to Postgres.
Image ships Piper via `pip install piper-tts==1.2.0` (works on Linux)
and prefetches a default voice. The release pipeline that would
build + push multi-arch images is written but commented out.

**3. PWA**

The configuration is **complete**: Workbox `GenerateSW`, manifest with
4 app shortcuts (primary list, shop-now, scan, add-item),
NetworkFirst caching for `/api/`, CacheFirst for stock/merchant
images, offline.html fallback. Service-worker lifecycle + push
subscription wiring already exist client-side
([usePwaLifecycle.ts](../../web_app/src/composables/usePwaLifecycle.ts),
[usePushSubscription.ts](../../web_app/src/composables/usePushSubscription.ts))
and the backend has Web Push end-to-end
([push_sender.py](../../dora_api/infrastructure/push_sender.py)).

**But:** `npm run build` runs `quasar build` (SPA mode), not
`quasar build -m pwa`. So **none of the SW/manifest config is actually
emitted in shipped artifacts today.** This is the single highest-ROI
fix in the whole audit — one build-command flip and the same code
becomes installable on every modern mobile + desktop with no
platform-specific work. Logged as **FU-NEW-PWA-BUILD-MODE**.

### Tier 2 — FU-327's named scope

**4. Windows desktop bundle (`.exe` / future `.msi`)**

[dora.spec](../../dora.spec) is platform-agnostic.
[fetch_piper.py:47](../../packaging/fetch_piper.py) already maps
`windows_amd64`. Missing: `packaging/build-windows.bat` (or
`.ps1`) that runs:

1. `cd web_app && npm install && npm run build`
2. `python packaging/fetch_piper.py --platform windows_amd64`
3. `python packaging/fetch_default_voice.py`
4. `pyinstaller --noconfirm dora.spec`

PyInstaller emits `dist/Dora/Dora.exe`. For a friendlier deliverable,
wrap with WiX or Inno Setup (both Windows-only tooling — needs a
Windows runner). MSI/installer is optional; the directory bundle is
already runnable.

**Compatibility notes:**
- `tzdata` is in [requirements.txt](../../requirements.txt) precisely
  because Windows lacks the IANA tz database — already handled.
- Spec excludes `tkinter` so no tk dependency surprises.
- pywebview's WebView2 backend would be implicit if used; but the
  current desktop entry launches the system browser instead, so
  WebView2 isn't actually exercised.
- `piper-tts` (pip) doesn't install on Windows because of
  `piper-phonemize`'s wheel gap — bypassed by bundling the standalone
  binary instead (R-018 / ADR-013). This is *why* `requirements.txt`
  deliberately doesn't pin `piper-tts`.

**Without code-signing:** Windows SmartScreen shows "Windows protected
your PC" until the binary builds enough reputation. EV code-signing
certs ($300–700/yr) skip the reputation curve; standard certs help
but don't eliminate it. Acceptable as "More info → Run anyway"
fallback for early users.

**5. macOS desktop bundle (`.app` / `.dmg`)**

Same shape as Windows. Two separate builds needed (PyInstaller's
`universal2` support is fragile) — `build-macos-arm64.sh` and
`build-macos-x64.sh`, each running the same four steps with the
appropriate `--platform` flag on `fetch_piper.py`.

**The harder problem is notarisation.** Without Apple's notarisation:
- Gatekeeper shows a scare screen
- Users must right-click → Open the first time
- Some users will give up

With notarisation: Apple Developer Program ($99/yr) + `codesign` +
`xcrun notarytool` + a Mac runner. **Recommendation: ship unsigned
first**, document the right-click-Open workaround, and pay for
signing only when there's a real user asking. This matches the
charter's "Effortless ≥ Anti-creep" tiebreak: don't pay $99/yr for a
hypothetical Mac user.

### Tier 3 — possible but disproportionate effort

**6. iOS (via Capacitor)**

- Quasar config has the Capacitor stanza
  ([quasar.config.ts:355](../../web_app/quasar.config.ts))
- Backend CORS already permits `capacitor://localhost`
  ([configuration_manager.py:39](../../dora_api/infrastructure/configuration_manager.py))
- Needs `quasar mode add capacitor` to scaffold `web_app/src-capacitor/`,
  then an Xcode build on a Mac.

**Hard blockers:**

- **No backend on-device.** The Flask backend is Python — there is no
  realistic path to ship Python + SQLAlchemy + Alembic inside iOS. A
  Capacitor build would be the SPA pointed at a **remote** (Docker-
  hosted) backend. That makes it a sync client, not a self-contained
  app. Fundamentally changes the deployment story.
- **iOS WKWebView autoplay rules** — already a known issue
  ([FU-287](../../DORA_FOLLOWUPS.md)) for Piper TTS and the cook-mode
  timer narration. Capacitor inherits the same constraint; needs a
  silent-audio unlock primer.
- **Apple Developer Program** ($99/yr) + Mac for Xcode + App Store
  review process.

**Recommendation:** ship as **PWA** (install via Safari → Share →
Add to Home Screen). Loses native push on iOS pre-16.4 and a couple
of integrations, but skips every gatekeeping pain point and reuses
the same artifact as Android + desktop browsers.

**7. Android (via Capacitor)**

Same shape as iOS — but **easier**:
- No Apple gatekeeping; can sideload APKs from a GitHub Release
- Play Store costs $25 one-off if you want the storefront
- Same backend-elsewhere constraint as iOS

**Recommendation:** still ship as PWA first. Chrome on Android has a
genuine "Install" prompt; the install flow is good. Move to a real
Capacitor APK only if a specific Android feature (camera intent
quirks, background-task ergonomics) becomes a real ask.

**8. Electron desktop**

Quasar scaffold present but no `src-electron/` dir. Would duplicate
the existing PyInstaller path (both produce a "desktop app with the
SPA inside"). The current PyInstaller path *also* bundles the Python
backend; Electron alone wouldn't — you'd still need to subprocess-
launch the Flask binary alongside Electron, which means *both*
packaging stacks for one outcome.

**Recommendation: don't add Electron.** PyInstaller + system-browser
launch is simpler and already works.

### Tier 4 — not worth pursuing

**9. Browser Extension (BEX)** — Quasar mode scaffolded but Dora is a
full app, not a one-screen utility. Skip.

**10. SSR** — Quasar config has `ssr.pwa: false`. Dora is heavily
authenticated + interactive; SSR would buy nothing. Skip.

## Cross-platform compatibility risks worth knowing

Not speculative — these are things the audit hit in the code.

| Risk | Where | Mitigation today | What to actually do |
|---|---|---|---|
| Piper TTS optional everywhere | `piper-tts` can't install on Windows. Bundle ships standalone binary instead. | Already handled — Piper-absent falls back to browser voice (R-018 / ADR-013). | None — just verify the Win bundle picks up `piper.exe` when added. |
| iOS WKWebView autoplay across `await` | Chat TTS + cook-mode timers | Known, [FU-287](../../DORA_FOLLOWUPS.md) deferred | Silent-audio unlock primer if iOS becomes a target. |
| Camera access requires HTTPS or localhost | [ScanOverlay.vue](../../web_app/src/components/ScanOverlay.vue) `getUserMedia` for barcode scan | None — silently fails on plain-HTTP intranets | Document: "scanning needs HTTPS (or localhost)" in self-host deploy docs. Reverse proxy with Let's Encrypt is the standard answer. |
| Service Worker requires HTTPS | PWA push, offline cache | None | Same HTTPS-or-localhost-only constraint. Same answer. |
| Web Push needs VAPID + reachable Mozilla/Google FCM endpoints | [push_sender.py](../../dora_api/infrastructure/push_sender.py) | Self-gates when VAPID env unset | Document the network egress need in self-host docs. |
| Windows lacks IANA tz database | Household-tz boundary logic | `tzdata` pinned in [requirements.txt](../../requirements.txt) | Already handled. |
| No mobile-app target without remote backend | Backend is Python | — | Scope mobile as **PWA-only**. If a user needs full-fat mobile, they're really asking for a hosted instance. |
| macOS Gatekeeper / notarisation | Unsigned `.app` | — | Ship unsigned with documented right-click-Open; pay for Apple Dev only when a real user asks. |
| Windows SmartScreen | Unsigned `.exe` | UPX disabled in spec (helps AV false-positive rate) | "More info → Run anyway" for early users. Code-signing cert when a real user asks. |
| CI entirely off (policy) | [.github/workflows/](../../.github/workflows/) | — | See § CI status. |

## CI status — intentional, user-policy

Both `.github/workflows/ci.yml` and `.github/workflows/release.yml`
are **commented out in their entirety** since commit `20176e8`
("Comment out github workflows temporarily").

This is **deliberate user policy, not bit-rot.** The user is doing
rapid Claude-driven development and has chosen to keep CI off to
avoid burning the GitHub Actions free-tier allowance on every push
during this development cadence.

While CI is off:
- Every release ships hand-built and untested on the dev box
- A Windows / macOS / Docker regression won't be caught by automation
- Build scripts for new platforms bit-rot fast (untested = broken
  within weeks, typically)

This is an **accepted trade-off** for the rapid-development phase.
The recommended sequencing below assumes CI revival happens later —
when the development cadence slows or when a real release deadline
makes the burned-allowance worthwhile.

When CI does come back, the natural revival shape is:
1. Un-comment `ci.yml`, keep it scoped to the existing
   `pytest tests/e2e/dora_api` + frontend lint/typecheck (no
   platform matrix yet) — the cheap, on-every-push net.
2. Un-comment `release.yml` separately, gate on
   `workflow_dispatch` only (no auto-fire), so the cost is paid
   only when a release is explicitly tagged. Add the
   Windows/macOS matrix here, not in `ci.yml`, because those
   runners burn minutes ~5× faster than Linux.

[FU-169](../../DORA_FOLLOWUPS.md) tracks the broader CI revival.

## Recommended target matrix (priority order)

| # | Target | Effort | Pre-reqs | Worth it? |
|---|---|---|---|---|
| 1 | **PWA build-mode flip + install banner** | ~1 hour | None — config already there | **Highest ROI.** One build-command flip; instantly installable on every modern mobile + desktop. |
| 2 | **Windows `.bat` build script** | half-day | None (just the script) | Yes when needed. Spec is ready. |
| 3 | **macOS `.sh` build scripts (arm64 + x86_64)** | half-day | None for unsigned; $99/yr Apple Dev for notarised | Yes for arm64 unsigned. Notarisation only when a real user asks. |
| 4 | **Docker multi-arch publish (linux/amd64 + linux/arm64)** | 1–2 hours | Tied to CI revival (off by user policy) | Yes when CI comes back — Raspberry Pi self-host is explicit in the charter. |
| 5 | **CI revival** ([FU-169](../../DORA_FOLLOWUPS.md)) | half-day code + ongoing $$ | User decision to spend GH minutes | **Deferred by user policy** during rapid Claude dev. |
| 6 | **Android via Capacitor** | 1–2 days + Android Studio | Items 1–4, OR explicit decision PWA isn't enough | Only if PWA proves insufficient. |
| 7 | **iOS via Capacitor** | 2–3 days + Mac + Apple Dev | Item 6 done | Probably not. PWA-on-iOS gets you 80% of the way. |
| 8 | Electron / Cordova / BEX | — | — | Skip — PyInstaller already does Electron's job. |

## Follow-ups spun off from this audit

- **FU-NEW-PWA-BUILD-MODE** — `npm run build` runs `quasar build`
  (SPA mode), not `quasar build -m pwa`. Workbox/manifest config is
  fully wired but never emitted in shipped artifacts. ~1 hour to fix.
- **FU-NEW-PLATFORM-DELIVERABLES-DOC** — README / desktop-onboarding
  copy references AppImage / `.exe` / `.dmg` as if all three exist;
  only AppImage actually does. Either build the others or correct
  the docs to set expectations.
- **FU-327** stays open; this audit reframes its scope: the named
  Windows + macOS scripts are still wanted (items #2 and #3 in the
  matrix above), but the higher-ROI moves are the PWA build-mode
  flip (item #1) and — when user policy allows — CI revival
  (item #5). The build scripts and the CI matrix that exercises
  them want to ship paired, not weeks apart.

## What this audit deliberately did NOT do

- **No code changes.** Audit-only per the user's scope decision.
- **No CI revival.** Explicit user policy: keep workflows disabled
  during rapid Claude dev to preserve the GH free-tier allowance.
- **No mobile scaffold.** `quasar mode add capacitor` would create
  ~300 files of Capacitor scaffolding that gets stale instantly
  without an active mobile workstream.
- **No notarisation work.** Speculative until a real user asks.
- **No code-signing cert procurement.** Same reason.
