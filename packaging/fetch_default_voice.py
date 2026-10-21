#!/usr/bin/env python3
"""Fetch the default Piper voice model into `packaging/voices/` for bundling.

The desktop and Docker builds ship a default voice (Amy) so Dora speaks her
neural voice out of the box — zero clicks, zero downloads on first run
(R-018 / ADR-013). The model is ~60 MB so it isn't committed to git; this
script populates `packaging/voices/` at build time:

  - `dora.spec` bundles `packaging/voices/` → `<desktop bundle>/voices/`.
  - The Dockerfile runs this script so `packaging/voices/` lands in the image.
  - `voice_provision.bundled_voices_dir()` finds the bundled file at runtime
    and reports it as `ready` in `GET /api/tts/voices`, so the user doesn't
    have to click Download before they can use the voice.

Run before `pyinstaller dora.spec` (`build-linux.sh` does this automatically):

    python packaging/fetch_default_voice.py            # default voice
    python packaging/fetch_default_voice.py amy ryan   # specific voices

Voice metadata (URL, checksum, filename) is owned server-side in
`dora_api/features/tts/voice_catalog.py` — this script reads it so the build
and runtime never disagree about which file is "the default voice".

Idempotent: an existing, checksum-matching file is left alone.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
_DEST = _HERE / "voices"

# Import the runtime catalog so build + runtime stay in sync on filename /
# URL / SHA. Adds the repo to sys.path so this script works when invoked
# standalone (`python packaging/fetch_default_voice.py`).
sys.path.insert(0, str(_REPO_ROOT))
from dora_api.features.tts.voice_catalog import (  # noqa: E402
    DEFAULT_VOICE_ID, VOICE_IDS, get_voice,
)


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def fetch(voice_id: str) -> Path:
    voice = get_voice(voice_id)
    if voice is None:
        raise SystemExit(
            f"Unknown voice '{voice_id}'. Choose from: {', '.join(VOICE_IDS)}"
        )
    _DEST.mkdir(parents=True, exist_ok=True)
    onnx = _DEST / voice.filename
    json_path = _DEST / f"{voice.filename}.json"

    if onnx.exists() and _sha256(onnx) == voice.sha256 and json_path.exists():
        print(f"[fetch-voice] already present: {onnx}")
        return onnx

    # `.onnx` first — large + integrity-checked — then the small JSON sidecar.
    print(f"[fetch-voice] downloading {voice.onnx_url}")
    _download_to(voice.onnx_url, onnx, expected_sha256=voice.sha256)
    print(f"[fetch-voice] downloading {voice.json_url}")
    _download_to(voice.json_url, json_path, expected_sha256=None)
    print(f"[fetch-voice] ready: {onnx}")
    return onnx


def _download_to(url: str, dest: Path, expected_sha256: str | None) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    hasher = hashlib.sha256()
    try:
        with urllib.request.urlopen(url) as resp, open(tmp, "wb") as out:  # noqa: S310 — pinned HF URL
            while True:
                chunk = resp.read(1 << 18)
                if not chunk:
                    break
                hasher.update(chunk)
                out.write(chunk)
        if expected_sha256 and hasher.hexdigest() != expected_sha256:
            raise SystemExit(
                f"[fetch-voice] checksum mismatch for {url} — refusing to bundle"
            )
        tmp.replace(dest)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch Piper voice models for build-time bundling.",
    )
    parser.add_argument(
        "voices", nargs="*",
        help=f"Voice ids to fetch (default: {DEFAULT_VOICE_ID}). "
             f"Available: {', '.join(VOICE_IDS)}.",
    )
    args = parser.parse_args()
    ids = args.voices or [DEFAULT_VOICE_ID]
    for vid in ids:
        fetch(vid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
