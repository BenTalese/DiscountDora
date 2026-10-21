"""Unit tests for `features/stores/_logo_colour.dominant_colour`.

Pure function over image bytes, so the whole contract is testable without a
DB or an app context. Worth pinning per the verification stance: the derived
colour is written once at upload and then persisted, so a regression here
doesn't show up until someone re-uploads a logo — and by then the wrong
colour is already in the column.
"""
import base64
import io

from PIL import Image, ImageDraw

from dora_api.features.stores._logo_colour import dominant_colour


def _logo(colour, *, background=(255, 255, 255), mode="RGB", mark="ellipse") -> bytes:
    """A 200x200 canvas with a smallish mark on it — deliberately mostly
    background, which is what a real retail logo looks like."""
    image = Image.new(mode, (200, 200), background)
    draw = ImageDraw.Draw(image)
    box = [60, 60, 140, 140]
    if mark == "ellipse":
        draw.ellipse(box, fill=colour)
    else:
        draw.rectangle(box, fill=colour)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{encoded}".encode("utf-8")


def _rgb(hex_colour: str) -> tuple[int, int, int]:
    value = hex_colour.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def _close(actual: str, expected: tuple[int, int, int], tolerance: int = 12) -> bool:
    """Anti-aliasing at the mark's edge pulls the bucket average a few steps
    toward the background, so exact equality is the wrong assertion."""
    return all(
        abs(a - e) <= tolerance for a, e in zip(_rgb(actual), expected)
    )


def test__dominant_colour__GreenMarkOnWhite__ReturnsGreen():
    # The Woolworths case from the feedback: majority of the *pixels* are
    # white, but the brand colour is the green mark.
    result = dominant_colour(_logo((23, 140, 60)))
    assert result is not None
    assert _close(result, (23, 140, 60))


def test__dominant_colour__RedMarkOnWhite__ReturnsRed():
    result = dominant_colour(_logo((224, 26, 32), mark="rectangle"))
    assert result is not None
    assert _close(result, (224, 26, 32))


def test__dominant_colour__DarkBlueMarkOnWhite__ReturnsBlue():
    # Navy is dark enough to brush the value floor; it must still survive.
    result = dominant_colour(_logo((0, 45, 114), mark="rectangle"))
    assert result is not None
    assert _close(result, (0, 45, 114))


def test__dominant_colour__ColouredMarkOnDarkCanvas__IgnoresTheCanvas():
    result = dominant_colour(_logo((240, 190, 20), background=(0, 0, 0)))
    assert result is not None
    assert _close(result, (240, 190, 20))


def test__dominant_colour__GreyscaleLogo__ReturnsNone():
    # No hue to find. None is the honest answer — the SPA keeps its
    # deterministic hash swatch rather than being handed a grey.
    assert dominant_colour(_logo((30, 30, 30))) is None


def test__dominant_colour__TransparentBackground__IgnoresTheTransparentPixels():
    image = Image.new("RGBA", (200, 200), (255, 255, 255, 0))
    ImageDraw.Draw(image).ellipse([60, 60, 140, 140], fill=(200, 40, 120, 255))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    blob = (
        "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
    ).encode("utf-8")
    result = dominant_colour(blob)
    assert result is not None
    assert _close(result, (200, 40, 120))


def test__dominant_colour__NoImage__ReturnsNone():
    assert dominant_colour(None) is None
    assert dominant_colour(b"") is None


def test__dominant_colour__NotADataUrl__ReturnsNone():
    assert dominant_colour(b"https://example.com/logo.png") is None


def test__dominant_colour__UndecodableImage__ReturnsNone():
    # A well-formed data URL whose payload isn't an image. Must not raise —
    # a broken logo still has to let the store save.
    assert dominant_colour(b"data:image/png;base64,bm90LWFuLWltYWdl") is None
