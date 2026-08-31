"""Regenerates `dora_api/persistence/seed_dense_images.py`.

The dense dev seed (`seed_dense.py`) needs real image bytes for the two
surfaces that store them: image-mode recipe steps (`RecipeStepImage`) and
shopping-list receipt attachments (`ShoppingListAttachment`). Both store the
same `data:image/png;base64,...` UTF-8 shape a browser upload lands, so the
seed can't fabricate them inline without either a runtime image dependency or
a pair of placeholder pixels — and FU-754 explicitly called out placeholder
pixels as not worth having: you cannot tell a broken image face from a working
one when every photo is 1x1 grey.

So the images are generated ONCE, here, and checked in as base64 constants.
They are drawn, not photographed: a numbered card with the step's own caption
and a simple diagram of the stage. That is honest about what they are while
still being individually recognisable, which is the property the image face
actually needs to be verifiable (are they in order? is the right one showing?).

Run from the repo root after editing the captions below:

    python scripts/generate_seed_dense_images.py

Requires Pillow (already a dependency — `dora_api/features/data/barcodes.py`
rasterises QR labels with it).
"""
from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image, ImageDraw

WIDTH, HEIGHT = 480, 360

# (constant_name, step_number, caption, background, ink, accent)
_RECIPE_STEPS = [
    ("FOCACCIA_STEP_1", 1, "Mix the dough", (247, 240, 226), (74, 59, 42), (214, 176, 108)),
    ("FOCACCIA_STEP_2", 2, "Rise until doubled", (243, 234, 216), (74, 59, 42), (206, 162, 92)),
    ("FOCACCIA_STEP_3", 3, "Dimple with oiled hands", (240, 229, 208), (74, 59, 42), (198, 148, 76)),
    ("FOCACCIA_STEP_4", 4, "Scatter rosemary and salt", (238, 226, 202), (74, 59, 42), (122, 148, 84)),
    ("FOCACCIA_STEP_5", 5, "Bake until deep gold", (233, 216, 184), (74, 59, 42), (176, 116, 48)),
]


def _card(step: int, caption: str, bg, ink, accent) -> bytes:
    """One step card: a numbered disc, the caption, and a diagram of the
    stage that changes shape step to step (so the five are distinguishable
    at thumbnail size, which is how cook mode shows them)."""
    image = Image.new("RGB", (WIDTH, HEIGHT), bg)
    draw = ImageDraw.Draw(image)

    # Pan / tray the food sits in — same framing every step, so what changes
    # between images is the food, not the composition.
    draw.rounded_rectangle((60, 96, 420, 300), radius=28, outline=ink, width=4)

    if step == 1:  # a shaggy ball of dough
        draw.ellipse((190, 150, 290, 250), fill=accent, outline=ink, width=3)
    elif step == 2:  # risen — fills more of the tray
        draw.ellipse((130, 130, 350, 270), fill=accent, outline=ink, width=3)
    elif step == 3:  # dimpled slab
        draw.rounded_rectangle((90, 126, 390, 274), radius=18, fill=accent, outline=ink, width=3)
        for row in range(2):
            for col in range(5):
                cx, cy = 130 + col * 60, 172 + row * 56
                draw.ellipse((cx - 11, cy - 11, cx + 11, cy + 11), outline=ink, width=3)
    elif step == 4:  # dimpled slab, now topped
        draw.rounded_rectangle((90, 126, 390, 274), radius=18, fill=(214, 176, 108), outline=ink, width=3)
        for i in range(6):
            x = 120 + i * 50
            draw.line((x, 160, x + 18, 196), fill=accent, width=5)
            draw.line((x + 18, 196, x + 4, 236), fill=accent, width=5)
    else:  # baked — darker, with a cut slice
        draw.rounded_rectangle((90, 126, 390, 274), radius=18, fill=accent, outline=ink, width=3)
        draw.line((240, 126, 240, 274), fill=ink, width=4)
        draw.line((90, 200, 390, 200), fill=ink, width=4)

    # Step number in a disc, top-left, plus the caption along the bottom.
    draw.ellipse((28, 24, 84, 80), fill=ink)
    draw.text((49, 42), str(step), fill=bg)
    draw.text((100, 44), f"Step {step} of {len(_RECIPE_STEPS)}", fill=ink)
    draw.text((60, 320), caption, fill=ink)
    return _encode(image)


def _receipt() -> bytes:
    """A stand-in receipt photo for the shopping-list attachment fixture.
    Deliberately unreadable line-noise rather than fake prices: attachments
    are pure record-keeping (no OCR, no parsing), so legible numbers would
    imply a matching behaviour the app does not have."""
    image = Image.new("RGB", (360, 480), (250, 249, 245))
    draw = ImageDraw.Draw(image)
    ink = (86, 86, 82)
    draw.rectangle((70, 40, 290, 440), fill=(255, 255, 255), outline=ink, width=3)
    draw.text((116, 64), "GROCERY RECEIPT", fill=ink)
    draw.line((90, 96, 270, 96), fill=ink, width=2)
    for i in range(14):
        y = 120 + i * 20
        draw.line((92, y, 92 + 90 + (i * 13) % 70, y), fill=(178, 178, 172), width=4)
        draw.line((228, y, 268, y), fill=(178, 178, 172), width=4)
    draw.line((90, 412, 270, 412), fill=ink, width=2)
    draw.text((100, 420), "TOTAL", fill=ink)
    return _encode(image)


def _encode(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    # Palette + optimise keeps each card ~2 KB, so the checked-in module
    # stays a readable size rather than a wall of base64.
    image.convert("P", palette=Image.ADAPTIVE, colors=32).save(
        buffer, format="PNG", optimize=True
    )
    return buffer.getvalue()


def _data_url(png: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


def main() -> None:
    lines = [
        '"""Generated image fixtures for the dense dev seed — DO NOT HAND-EDIT.',
        "",
        "Regenerate with `python scripts/generate_seed_dense_images.py`; that script",
        "carries the rationale (FU-754) and the drawing code. Each constant is the",
        "`data:image/png;base64,...` string a browser upload would have produced, which",
        "is the exact shape `RecipeStepImage.image` / `ShoppingListAttachment.image`",
        "store (UTF-8 bytes of the data URL, decoded by the bytes endpoints).",
        '"""',
        "",
    ]
    for name, step, caption, bg, ink, accent in _RECIPE_STEPS:
        lines.append(f"# Step {step} — {caption}")
        lines.append(f'{name} = (\n    "{_data_url(_card(step, caption, bg, ink, accent))}"\n)')
        lines.append("")
    lines.append("FOCACCIA_STEP_IMAGES = [")
    for name, _step, _caption, _bg, _ink, _accent in _RECIPE_STEPS:
        lines.append(f"    {name},")
    lines.append("]")
    lines.append("")
    lines.append("# Receipt photo for the finished-shop attachment fixture.")
    lines.append(f'RECEIPT_PHOTO = (\n    "{_data_url(_receipt())}"\n)')
    lines.append("")

    target = Path(__file__).resolve().parents[1] / "dora_api" / "persistence" / "seed_dense_images.py"
    target.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {target} ({target.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
