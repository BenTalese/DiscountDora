"""Piper voice download — the two fetches must land as real files.

Why this test exists: `_download_voice` fetches the model and its JSON sidecar
into `<name>.part` files and only then renames both into place. On 2026-09-03
that trailing rename block had drifted into `_record_progress`, a function
where `onnx_tmp` / `json_tmp` / `onnx` / `json_final` are not in scope — so
*every* voice download failed with ``name 'onnx_tmp' is not defined`` the
moment the first progress tick fired, and the UI showed that raw NameError as
the voice's error state (owner report).

Nothing covered the provisioning path at all, which is how a plain NameError
shipped. This pins the contract that survives any future refactor of the
progress/rename split: after a successful download, the two final files exist,
carry the fetched bytes, and no `.part` files are left behind.
"""
from pathlib import Path

import pytest

from dora_api.features.tts import voice_provision
from dora_api.features.tts.voice_catalog import VoiceDef


@pytest.fixture
def voice() -> VoiceDef:
    return VoiceDef(
        id="test-voice",
        label="Test voice",
        description="fixture",
        gender="neutral",
        filename="test_voice.onnx",
        hf_path="test/voice",
        size_bytes=4,
        sha256="",
        params={},
    )


def test__download_voice__renames_both_part_files_into_place(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, voice: VoiceDef,
) -> None:
    monkeypatch.setattr(voice_provision, "voices_dir", lambda: tmp_path)

    def fake_fetch(url, tmp_path_, expected_sha256, on_progress=None):  # noqa: ANN001, ANN202
        tmp_path_.write_bytes(b"onnx" if url.endswith(".onnx") else b"json")
        # The real fetch reports progress for the model; that call is what used
        # to blow up, so drive it here rather than trusting the happy path.
        if on_progress is not None:
            on_progress(0, 4)
            on_progress(4, 4)

    monkeypatch.setattr(voice_provision, "_fetch", fake_fetch)

    voice_provision._download_voice(voice)

    assert (tmp_path / "test_voice.onnx").read_bytes() == b"onnx"
    assert (tmp_path / "test_voice.onnx.json").read_bytes() == b"json"
    # A `.part` left behind means the rename never ran — the exact shape of the
    # regression, since a partial download would then read as "not ready".
    assert list(tmp_path.glob("*.part")) == []


def test__run_download__records_no_error_on_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, voice: VoiceDef,
) -> None:
    """The UI reads `error_for()`; a NameError inside the download surfaced
    there as the voice's state, which is how the owner saw it."""
    monkeypatch.setattr(voice_provision, "voices_dir", lambda: tmp_path)
    monkeypatch.setattr(
        voice_provision,
        "_fetch",
        lambda url, tmp, expected_sha256, on_progress=None: tmp.write_bytes(b"x"),
    )

    voice_provision._run_download(voice)

    assert voice_provision.error_for(voice.id) is None
    assert (tmp_path / "test_voice.onnx").exists()
