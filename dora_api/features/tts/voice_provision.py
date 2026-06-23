"""Download Piper voice models on demand into the runtime voices dir.

Voice models aren't shipped in the repo (~60 MB each). When a user picks a
voice in onboarding / Settings → Voice, the SPA calls
`POST /api/tts/voices/<id>/download`, which kicks off a background download
here: fetch the `.onnx` + `.onnx.json` from the catalog's pinned HuggingFace
URLs into `<voices dir>`, verify the `.onnx` against the catalog SHA-256, and
atomically move it into place. `GET /api/tts/voices` reports each voice's
state so the UI can show Download / Downloading… / Ready / Retry.

State is process-local (an in-memory set + last-error map). That's fine: the
*file on disk* is the source of truth for "ready" (any worker sees it), and the
download status is only a transient UI hint while a fetch is in flight. A
second download request for an already-in-flight voice is a no-op.
"""
import hashlib
import logging
import threading
from pathlib import Path

import requests

from dora_api.features.tts.voice_catalog import VoiceDef, get_voice
from dora_api.infrastructure.configuration_manager import DORA_CONFIG

_LOG = logging.getLogger(__name__)

# Per-voice download state, guarded by _LOCK. `_IN_FLIGHT` holds ids currently
# downloading; `_ERRORS` holds the last error message per id (cleared on a
# fresh attempt / success).
_LOCK = threading.Lock()
_IN_FLIGHT: set[str] = set()
_ERRORS: dict[str, str] = {}

# Hard ceiling so a bad URL / redirect to something huge can't fill the disk.
_MAX_BYTES = 200 * 1024 * 1024
_CHUNK = 1024 * 256


def voices_dir() -> Path:
    return DORA_CONFIG.get_voices_dir()


def model_path(voice: VoiceDef) -> Path:
    return voices_dir() / voice.filename


def is_downloaded(voice: VoiceDef) -> bool:
    return model_path(voice).exists()


def status_for(voice: VoiceDef) -> str:
    """One of: ready | downloading | error | downloadable."""
    if is_downloaded(voice):
        return "ready"
    with _LOCK:
        if voice.id in _IN_FLIGHT:
            return "downloading"
        if voice.id in _ERRORS:
            return "error"
    return "downloadable"


def error_for(voice_id: str) -> str | None:
    with _LOCK:
        return _ERRORS.get(voice_id)


def start_download(voice: VoiceDef) -> str:
    """Begin (or no-op) a background download. Returns the resulting status:
    `ready` (already present), `downloading` (started or already running)."""
    if is_downloaded(voice):
        return "ready"
    with _LOCK:
        if voice.id in _IN_FLIGHT:
            return "downloading"
        _IN_FLIGHT.add(voice.id)
        _ERRORS.pop(voice.id, None)
    thread = threading.Thread(
        target=_run_download, args=(voice,), name=f"tts-download-{voice.id}", daemon=True,
    )
    thread.start()
    return "downloading"


def _run_download(voice: VoiceDef) -> None:
    try:
        _download_voice(voice)
        _LOG.info("Downloaded Piper voice '%s' (%s)", voice.id, voice.filename)
        with _LOCK:
            _ERRORS.pop(voice.id, None)
    except Exception as exc:  # noqa: BLE001 — surface any failure as UI state
        _LOG.exception("Failed to download Piper voice '%s'", voice.id)
        with _LOCK:
            _ERRORS[voice.id] = str(exc) or exc.__class__.__name__
    finally:
        with _LOCK:
            _IN_FLIGHT.discard(voice.id)


def _download_voice(voice: VoiceDef) -> None:
    dest_dir = voices_dir()
    onnx = dest_dir / voice.filename
    onnx_tmp = dest_dir / f"{voice.filename}.part"
    json_final = dest_dir / f"{voice.filename}.json"
    json_tmp = dest_dir / f"{voice.filename}.json.part"

    # The model first (big, integrity-checked), then the small config sidecar.
    _fetch(voice.onnx_url, onnx_tmp, expected_sha256=voice.sha256)
    _fetch(voice.json_url, json_tmp, expected_sha256=None)

    # Atomic-ish swap: rename both only once both fetched + verified, so a
    # partial download never looks "ready".
    onnx_tmp.replace(onnx)
    json_tmp.replace(json_final)


def _fetch(url: str, tmp_path: Path, expected_sha256: str | None) -> None:
    hasher = hashlib.sha256()
    total = 0
    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(tmp_path, "wb") as handle:
            for chunk in resp.iter_content(chunk_size=_CHUNK):
                if not chunk:
                    continue
                total += len(chunk)
                if total > _MAX_BYTES:
                    raise ValueError(f"download exceeded {_MAX_BYTES} bytes")
                hasher.update(chunk)
                handle.write(chunk)
    if total == 0:
        raise ValueError("empty download")
    if expected_sha256 and hasher.hexdigest() != expected_sha256:
        tmp_path.unlink(missing_ok=True)
        raise ValueError("checksum mismatch — download discarded")


def ensure_voice(voice_id: str) -> bool:
    """Synchronous download for build/CLI use (e.g. packaging prefetch).
    Returns True if the voice is present afterwards. Used by
    `python -m dora_api.features.tts.voice_provision <id...>`."""
    voice = get_voice(voice_id)
    if voice is None:
        raise ValueError(f"unknown voice '{voice_id}'")
    if is_downloaded(voice):
        return True
    _download_voice(voice)
    return is_downloaded(voice)


if __name__ == "__main__":
    import sys

    from dora_api.features.tts.voice_catalog import DEFAULT_VOICE_ID

    logging.basicConfig(level=logging.INFO)
    ids = sys.argv[1:] or [DEFAULT_VOICE_ID]
    for vid in ids:
        ok = ensure_voice(vid)
        print(f"{vid}: {'ready' if ok else 'FAILED'}")
