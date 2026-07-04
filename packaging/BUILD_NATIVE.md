# Native mobile builds — Dashy Dora

**Landed:** P8-10, 2026-07-04. Capacitor 8 wraps the existing Quasar SPA
for iOS and Android. **One codebase, no SPA fork** — the same
`web_app/src/**` that runs on the desktop PWA is what ships inside the
native shells.

## What's here

- `web_app/src-capacitor/` — Capacitor project (own `package.json`,
  its own `node_modules`).
- `web_app/src-capacitor/android/` — Android Studio project.
- `web_app/src-capacitor/ios/` — Xcode project (scaffolded only, never
  built — needs a Mac session).
- `web_app/src-capacitor/capacitor.config.json` — appId, appName,
  webDir, platform overrides.

Capacitor plugins installed at scaffold time:
`@capacitor/app`, `@capacitor/preferences`, `@capacitor/splash-screen`,
`@capacitor/status-bar`.

## Prerequisites (Android build box)

- **Java 21+** — already present on Linux dev boxes (`openjdk 21`).
- **Android SDK** — either Android Studio (recommended: it bundles
  everything) or the standalone command-line tools:
  - Platform: `android-34` (API 34, latest stable)
  - Build tools: `34.0.0`
  - Set `ANDROID_HOME` / `ANDROID_SDK_ROOT` before running any build.
- **Node 20+** — same runtime the SPA already uses.

For iOS builds you need a Mac with Xcode 15+ and (for a store upload) an
Apple Developer Program account ($99/yr). Neither is required to keep the
scaffold in the tree.

## Build an Android APK

From `web_app/`:

```bash
# 1. Build the SPA into src-capacitor/www.
npx quasar build -m capacitor -T android

# 2. That command drops you into src-capacitor/, syncs the built SPA
#    into the Android project's assets, and (in the default flow) opens
#    Android Studio for you. If you want the APK directly on the CLI:
cd src-capacitor/android
./gradlew assembleDebug

# The APK lands at:
#   app/build/outputs/apk/debug/app-debug.apk
```

A release (signed) APK follows the same shape — `./gradlew assembleRelease`
after configuring a keystore. Keystore setup is a one-off and lives outside
this repo; see the Android developer docs for `signingConfigs`.

## First-run flow

On the very first launch of the APK, the app opens on `/setup/backend`.
The user enters the URL of their Dora instance (e.g.
`https://dora.mybox.example`), we ping `/api/auth/me` to confirm the
backend answered, and persist the URL to `@capacitor/preferences`.

The router guard blocks every other route (including `/login`) until
that step completes. Users can change the instance URL later from
Settings → About → **Change**.

## Permissions declared

`web_app/src-capacitor/android/app/src/main/AndroidManifest.xml`:

- `INTERNET` — every network call.
- `CAMERA` — barcode scanning (`ScanOverlay.vue` `getUserMedia`).
- `WAKE_LOCK` — shop-mode and cook-mode `useWakeLock` composable.
- `VIBRATE` — Quasar's Notify uses it opportunistically.
- `POST_NOTIFICATIONS` (Android 13+) — declared for the day native push
  is wired.

Web push (VAPID) is **not** supported inside the Android WebView. On
native, the push toggle in Settings shows 'unsupported'. If a user
wants proactive alerts on their phone, the PWA-install path is the
supported route today; a native push bridge via
`@capacitor/push-notifications` + FCM is a future prompt (see
`DORA_FOLLOWUPS.md` FU-native-push).

## iOS

The `ios/` folder exists so a future Mac session can open the Xcode
project directly. There is no CI matrix, no signing certs, no
provisioning profile — that all lands the day someone needs iOS.

## Live-reload during development

Point Capacitor at your dev server so hot-reload works on-device:

```bash
# Set the dev backend the app should talk to (native ignores window.location).
export CAPACITOR_SERVER_URL="http://192.168.1.42:9000"
npx quasar dev -m capacitor -T android
```

The dev server serves the SPA at that URL; the Android emulator (or a
real device on the same LAN) opens it and hot-reloads on file save.

## Store submission

Not attempted. See `docs/04_proposals/PLAY_STORE_LISTING.md` for the
draft copy + screenshot plan; the actual submission is a future prompt.
