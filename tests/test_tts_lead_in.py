"""FU-722: every Piper clip starts with silence, so a phone's audio output
waking up swallows silence rather than the first words."""
import io
import struct
import wave

from dora_api.features.tts.tts_synthesize import with_lead_in


def _wav(frames: bytes, rate: int = 22050) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(frames)
    return buf.getvalue()


def _read(wav: bytes) -> tuple[int, bytes]:
    with wave.open(io.BytesIO(wav)) as w:
        return w.getframerate(), w.readframes(w.getnframes())


def test__silence_is_put_before_the_speech():
    speech = struct.pack("<4h", 100, -100, 200, -200)

    rate, frames = _read(with_lead_in(_wav(speech), 0.5))

    assert rate == 22050
    assert frames == b"\x00" * (11025 * 2) + speech


def test__a_placeholder_data_size_from_a_pipe_still_works():
    speech = struct.pack("<2h", 7, 8)
    wav = bytearray(_wav(speech))
    data_at = wav.index(b"data")
    wav[data_at + 4:data_at + 8] = struct.pack("<I", 0xFFFFFFFF)

    _, frames = _read(with_lead_in(bytes(wav), 0.01))

    assert frames.endswith(speech)
    assert len(frames) == 220 * 2 + len(speech)


def test__something_that_is_not_a_wav_is_returned_unchanged():
    assert with_lead_in(b"not audio", 0.35) == b"not audio"
