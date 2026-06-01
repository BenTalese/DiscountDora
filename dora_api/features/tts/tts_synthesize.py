"""POST /api/tts — Piper text-to-speech.

Runs Piper as a subprocess and streams the resulting WAV back to the
client. Piper is a small, MIT-licensed neural TTS that runs offline on
CPU; we ship a single binary + a single voice file so the desktop build
can produce a natural-sounding voice without any cloud calls.

Configuration:
  DORA_PIPER_BIN    — path to the piper executable (default: `piper`
                      on PATH, which works after `pip install piper-tts`)
  DORA_PIPER_VOICE  — path to the `.onnx` voice model. The matching
                      `.onnx.json` must sit next to it. Required.

Request JSON: { "text": str, "length_scale"?: float,
                "noise_scale"?: float, "noise_w"?: float,
                "sentence_silence"?: float, "pitch_semitones"?: float }

`length_scale` is Piper's speed knob: >1 slower, <1 faster. Piper has
no native pitch knob; `pitch_semitones` is applied as a post-process
through ffmpeg (asetrate + atempo) so pitch shifts without dragging
the speed. Requires ffmpeg on PATH — if it's missing and pitch is
non-zero, we return the un-pitched WAV unchanged.
"""
import logging
import os
import shutil
import subprocess
from pathlib import Path

from flask import Response, jsonify, request

from dora_api.features.routers import TTS_ROUTER

_LOG = logging.getLogger(__name__)


def _piper_bin() -> str | None:
    explicit = os.environ.get("DORA_PIPER_BIN")
    if explicit:
        return explicit if Path(explicit).exists() else None
    return shutil.which("piper")


def _voice_path() -> Path | None:
    raw = os.environ.get("DORA_PIPER_VOICE")
    if not raw:
        return None
    p = Path(raw)
    return p if p.exists() else None


@TTS_ROUTER.route("", methods=["POST"])
def synthesize():
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text is required"}), 400

    piper = _piper_bin()
    voice = _voice_path()
    if not piper or not voice:
        return jsonify({
            "error": "Piper is not configured",
            "hint": "Install piper-tts (`pip install piper-tts`) and set "
                    "DORA_PIPER_VOICE to a downloaded .onnx voice file. "
                    "Voices: https://github.com/rhasspy/piper/blob/master/VOICES.md",
        }), 503

    args = [piper, "--model", str(voice), "--output_file", "-"]
    for key in ("length_scale", "noise_scale", "noise_w", "sentence_silence"):
        val = body.get(key)
        if val is None:
            continue
        try:
            args.extend([f"--{key}", str(float(val))])
        except (TypeError, ValueError):
            return jsonify({"error": f"{key} must be a number"}), 400

    pitch_semitones = 0.0
    if body.get("pitch_semitones") is not None:
        try:
            pitch_semitones = float(body["pitch_semitones"])
        except (TypeError, ValueError):
            return jsonify({"error": "pitch_semitones must be a number"}), 400

    try:
        result = subprocess.run(
            args,
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=30,
            check=True,
        )
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Piper timed out"}), 504
    except subprocess.CalledProcessError as exc:
        _LOG.error("Piper failed: %s", exc.stderr.decode("utf-8", "replace"))
        return jsonify({"error": "Piper synthesis failed"}), 500

    wav = result.stdout
    if abs(pitch_semitones) > 0.01:
        wav = _pitch_shift(wav, pitch_semitones) or wav

    return Response(wav, mimetype="audio/wav")


def _pitch_shift(wav: bytes, semitones: float) -> bytes | None:
    """Shift pitch without changing duration. Uses ffmpeg: asetrate
    multiplies the sample-rate header (pitch + speed up together),
    aresample puts it back to the original rate, then atempo undoes
    the speed change. Returns None on failure so the caller can fall
    back to the un-shifted audio."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        _LOG.warning("ffmpeg not on PATH — pitch_semitones ignored")
        return None
    ratio = 2.0 ** (semitones / 12.0)
    # atempo only accepts 0.5–2.0 per filter; chain when out of range.
    tempo = 1.0 / ratio
    tempo_chain: list[str] = []
    remaining = tempo
    while remaining < 0.5:
        tempo_chain.append("atempo=0.5")
        remaining /= 0.5
    while remaining > 2.0:
        tempo_chain.append("atempo=2.0")
        remaining /= 2.0
    tempo_chain.append(f"atempo={remaining:.6f}")
    # Piper WAV is 22050 Hz mono; reading the header would be safer
    # but Piper voices all use 22050 in practice.
    sr = 22050
    filt = f"asetrate={int(sr * ratio)},aresample={sr}," + ",".join(tempo_chain)
    try:
        out = subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error",
             "-f", "wav", "-i", "pipe:0",
             "-filter:a", filt,
             "-f", "wav", "pipe:1"],
            input=wav, capture_output=True, timeout=15, check=True,
        )
        return out.stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        stderr = getattr(exc, "stderr", b"") or b""
        _LOG.error("ffmpeg pitch shift failed: %s", stderr.decode("utf-8", "replace"))
        return None
