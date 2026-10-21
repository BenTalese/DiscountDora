"""Progress reporting for the two long downloads (nutrition datasets, Piper voices).

The bug being guarded is not "the number is wrong" — it's the class of thing
that turns a progress bar into a liar. Two shapes recur:

  * dividing by a total the origin never sent (`Content-Length` absent →
    `bytes_total: 0` → a bar pinned at Infinity or NaN), and
  * a bar that stalls short of 100% because the final chunk didn't reach the
    reporting tick.

Both are invisible in a unit test of the parser and expensive to reproduce by
hand — you need a real multi-minute download, and the second only shows up at
the very end of it. Hence tests rather than a DORA_VERIFY line.
"""
import io
import zipfile

import pytest

from dora_api.features.nutrition import dataset_import as di


class _FakeResponse:
    """Stands in for `urlopen`'s context manager: a chunked reader plus
    headers. `headers.get` is all the code under test uses."""

    def __init__(self, payload: bytes, content_length):  # noqa: ANN001
        self._buffer = io.BytesIO(payload)
        self.headers = {} if content_length is None else {"Content-Length": content_length}

    def read(self, size=-1):  # noqa: ANN001
        return self._buffer.read(size)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def _patch_download(monkeypatch, payload: bytes, content_length):  # noqa: ANN001
    monkeypatch.setattr(
        di, "urlopen", lambda *_a, **_kw: _FakeResponse(payload, content_length),
    )


def test__download_reports_bytes_against_the_declared_total(monkeypatch):
    payload = b"x" * (di._DOWNLOAD_TICK_BYTES * 3 + 17)
    _patch_download(monkeypatch, payload, str(len(payload)))

    seen = []
    got = di._download("https://example.invalid/f.zip", on_progress=lambda d, t: seen.append((d, t)))

    assert got == payload
    assert seen[0] == (0, len(payload)), "the total should be published before the first chunk"
    assert all(total == len(payload) for _, total in seen)
    assert [d for d, _ in seen] == sorted(d for d, _ in seen), "byte count went backwards"


def test__a_finished_download_lands_exactly_on_the_total(monkeypatch):
    """The trailing partial chunk is the whole point: without the final
    unconditional report, a completed download rests just under 100% forever
    and reads as a stall at the worst possible moment."""
    payload = b"x" * (di._DOWNLOAD_TICK_BYTES + 1)
    _patch_download(monkeypatch, payload, str(len(payload)))

    seen = []
    di._download("https://example.invalid/f.zip", on_progress=lambda d, t: seen.append((d, t)))

    done, total = seen[-1]
    assert done == total == len(payload)


@pytest.mark.parametrize("header", [None, "not-a-number"])
def test__a_missing_or_junk_content_length_reports_zero_not_a_guess(monkeypatch, header):
    """0 is the agreed "unknown" signal the client checks before dividing.
    A guessed denominator here would produce a confidently wrong percentage."""
    payload = b"x" * 4096
    _patch_download(monkeypatch, payload, header)

    seen = []
    di._download("https://example.invalid/f.zip", on_progress=lambda d, t: seen.append((d, t)))

    assert seen[0] == (0, 0)
    # The closing report may substitute the observed size once the length is
    # actually known — that's honest, it happened. What must never appear is a
    # total invented mid-flight.
    assert all(total in (0, len(payload)) for _, total in seen)


def test__download_without_a_progress_sink_still_works(monkeypatch):
    """`_download` is called with no callback from `ensure_voice`-style paths
    and the parser tests; the optional sink must stay optional."""
    payload = b"x" * 1024
    _patch_download(monkeypatch, payload, str(len(payload)))
    assert di._download("https://example.invalid/f.zip") == payload


def _tiny_bundle() -> bytes:
    """The smallest archive `parse_fdc_csv_zip` will accept, with enough rows
    to cross the parse tick at least once."""
    rows = di._PARSE_TICK_ROWS + 100
    food = "fdc_id,description,food_category_id\n" + "".join(
        f"{i},Food {i},1\n" for i in range(rows)
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("d/food.csv", food)
        archive.writestr("d/nutrient.csv", "id,name,unit_name\n1,Energy,kcal\n")
        archive.writestr("d/food_nutrient.csv", "fdc_id,nutrient_id,amount\n0,1,100\n")
    return buffer.getvalue()


def test__parsing_reports_a_cumulative_climbing_row_count():
    seen = []
    di.parse_fdc_csv_zip(_tiny_bundle(), "usda_foundation", on_rows=seen.append)

    assert seen, "no parse progress was reported at all"
    assert seen == sorted(seen), "the row count is not cumulative across files"
    assert seen[0] >= di._PARSE_TICK_ROWS


def test__parsing_without_a_sink_is_unchanged():
    """The parser's own tests call this with two arguments; keeping the sink
    optional is what lets them stay that way."""
    foods, _ = di.parse_fdc_csv_zip(_tiny_bundle(), "usda_foundation")
    # Only fdc_id 0 was given an energy value, and foods without one are
    # dropped as unusable — so exactly one survives.
    assert len(foods) == 1
