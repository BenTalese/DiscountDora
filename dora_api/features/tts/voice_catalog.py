"""The curated Piper voice catalog — the single server-side source of truth.

Dora speaks with a Piper neural voice (see `tts_synthesize.py`). This module
owns *which* voices exist, what they're called, where to download each model,
and the per-voice Piper tuning that gives each a pleasant, on-brand "Dora"
character. The frontend never hardcodes any of this — it learns the catalog +
each voice's download/availability state via `GET /api/tts/voices` and picks
one by `id` (R-003 / state-ownership: catalog + tuning are domain facts owned
by the server, not copied to the client).

Voice models are **not** shipped in the repo (a single medium model is ~60 MB —
git bloat). Instead they're downloaded on demand into the runtime data dir
(`<DORA_DATA_DIR>/voices`, overridable with `DORA_PIPER_VOICE_DIR`) when the
user picks a voice in onboarding / Settings → Voice. See `voice_provision.py`
for the download + integrity check, and `tts_synthesize.py` for resolution. A
voice is *available* once its `<filename>.onnx` is present there (and the
`piper` binary is reachable).

Tuning note: the default `params` leave `pitch_semitones` at 0 so the standard
experience never depends on ffmpeg (pitch shift is an optional ffmpeg
post-process — see `tts_synthesize.py`). The settings Preview may still pass
explicit knobs to audition a voice.
"""
from dataclasses import dataclass

# All catalog voices live in the official Piper voices repo. The `resolve`
# endpoint serves the actual file (the `raw` endpoint serves the LFS pointer);
# `<HF_BASE>/<hf_path>.onnx` and `.onnx.json` are the two files per voice.
HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"


@dataclass(frozen=True, slots=True)
class VoiceDef:
    id: str
    label: str
    description: str
    gender: str           # "female" | "male" | "neutral"
    filename: str         # the .onnx model filename (the .onnx.json sits beside it)
    hf_path: str          # path under HF_BASE, without extension
    size_bytes: int       # the .onnx download size (shown in the UI)
    sha256: str           # integrity check for the downloaded .onnx
    params: dict[str, float]  # default Piper knobs for this voice

    @property
    def onnx_url(self) -> str:
        return f"{HF_BASE}/{self.hf_path}.onnx"

    @property
    def json_url(self) -> str:
        return f"{HF_BASE}/{self.hf_path}.onnx.json"


# Near-Piper-default tuning with a slightly longer inter-sentence pause for a
# calmer, friendlier cadence that suits a kitchen assistant.
_DORA_CADENCE: dict[str, float] = {
    "length_scale": 1.0,
    "noise_scale": 0.667,
    "noise_w": 0.8,
    "sentence_silence": 0.25,
    "pitch_semitones": 0.0,
}

VOICE_CATALOG: tuple[VoiceDef, ...] = (
    VoiceDef(
        id="amy",
        label="Amy",
        description="Warm, friendly American woman — Dora's default voice.",
        gender="female",
        filename="en_US-amy-medium.onnx",
        hf_path="en/en_US/amy/medium/en_US-amy-medium",
        size_bytes=63201294,
        sha256="b3a6e47b57b8c7fbe6a0ce2518161a50f59a9cdd8a50835c02cb02bdd6206c18",
        params=dict(_DORA_CADENCE),
    ),
    VoiceDef(
        id="ryan",
        label="Ryan",
        description="Easy-going American man.",
        gender="male",
        filename="en_US-ryan-medium.onnx",
        hf_path="en/en_US/ryan/medium/en_US-ryan-medium",
        size_bytes=63201294,
        sha256="abf4c274862564ed647ba0d2c47f8ee7c9b717d27bdad9219100eb310db4047a",
        params=dict(_DORA_CADENCE),
    ),
    VoiceDef(
        id="jenny",
        label="Jenny",
        description="Soft, natural British woman.",
        gender="female",
        filename="en_GB-jenny_dioco-medium.onnx",
        hf_path="en/en_GB/jenny_dioco/medium/en_GB-jenny_dioco-medium",
        size_bytes=63201294,
        sha256="469c630d209e139dd392a66bf4abde4ab86390a0269c1e47b4e5d7ce81526b01",
        params=dict(_DORA_CADENCE),
    ),
    VoiceDef(
        id="kristin",
        label="Kristin",
        description="Bright, upbeat American woman.",
        gender="female",
        filename="en_US-kristin-medium.onnx",
        hf_path="en/en_US/kristin/medium/en_US-kristin-medium",
        size_bytes=63531379,
        sha256="5849957f929cbf720c258f8458692d6103fff2f0e3d3b19c8259474bb06a18d4",
        params=dict(_DORA_CADENCE),
    ),
    VoiceDef(
        id="lessac",
        label="Lessac",
        description="Clear, neutral American narrator.",
        gender="neutral",
        filename="en_US-lessac-medium.onnx",
        hf_path="en/en_US/lessac/medium/en_US-lessac-medium",
        size_bytes=63201294,
        sha256="5efe09e69902187827af646e1a6e9d269dee769f9877d17b16b1b46eeaaf019f",
        params=dict(_DORA_CADENCE),
    ),
)

# The default voice a fresh user gets. Resolution falls back to it when a
# user's saved voice_id isn't downloaded yet.
DEFAULT_VOICE_ID = "amy"

_BY_ID: dict[str, VoiceDef] = {v.id: v for v in VOICE_CATALOG}

# Closed set of valid voice ids — imported by update_me.py for boundary
# validation (R-010 carve-out, same shape as nutrition_mode).
VOICE_IDS: tuple[str, ...] = tuple(_BY_ID.keys())


def get_voice(voice_id: str) -> VoiceDef | None:
    return _BY_ID.get(voice_id)
