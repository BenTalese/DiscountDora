# Piper voice models

Dora's neural voice (`POST /api/tts`) plays Piper `.onnx` voice models. They are
**downloaded on demand**, not shipped in the repo (a single medium model is
~60 MB — git bloat), and they do **not** live in this directory at runtime.

- **Where they go:** the runtime data dir — `<DORA_DATA_DIR>/voices` (e.g.
  `./data/voices` in dev, the mounted volume in Docker, the per-user data dir on
  desktop). Override with `DORA_PIPER_VOICE_DIR`. See
  `infrastructure/configuration_manager.py::get_voices_dir`.
- **How they get there:** the user picks a voice in onboarding / Settings →
  Voice and clicks **Download** (male / female / etc). The SPA calls
  `POST /api/tts/voices/<id>/download`; the server fetches the model from the
  catalog's pinned HuggingFace URLs, verifies the SHA-256, and stores it.
  `GET /api/tts/voices` reports each voice's state (downloadable / downloading /
  ready / error). No manual filesystem steps.
- **The catalog** — labels, descriptions, gender, download URL, size, SHA-256,
  per-voice tuning — is defined once in [`../voice_catalog.py`](../voice_catalog.py)
  (the single source of truth). Download/verify logic is in
  [`../voice_provision.py`](../voice_provision.py).

This directory is intentionally (almost) empty — it just holds this note.

## The Piper binary

Synthesis also needs the `piper` binary. Shipped artifacts include it
automatically (Docker installs `piper-tts`; the desktop bundle ships
`piper`/`piper.exe`). For a bare source / pip run, install it yourself —
`pip install piper-tts` on Linux/macOS, or download the binary from
<https://github.com/rhasspy/piper/releases> and point `DORA_PIPER_BIN` at it.
Without Piper the `/api/tts` endpoint returns 503 and the app falls back to the
browser's built-in speech voice, so nothing breaks.

## Offline prefetch (optional)

To pre-place models without going through the UI (airgapped installs, baking an
image):

```sh
python -m dora_api.features.tts.voice_provision amy ryan
```

Downloads the named catalog voices into the voices dir.
