"""Regenerate `brand-banner.png` — the header image used by every
transactional email (see `_layout.html` + `email_sender.send_email`).

Email clients don't load web fonts, so the "Dashy Dora" wordmark in the
Cute Dino brand font can't be live HTML text — it's baked into this PNG
alongside the mascot. The rasterisation is done in a real browser (the
only place the woff2 font renders faithfully) via a canvas, so the output
matches the in-app wordmark pixel-for-pixel.

This script only builds the throwaway generator HTML; it does not need any
image library. To regenerate:

  1. python dora_api/email_templates/assets/generate_brand_banner.py
     → writes <output-dir>/banner_gen.html (path printed).
  2. Open that file in a browser (serve it over http:// if file:// is
     blocked), then read `window.__PNG__` (a data: URL) once the tab title
     flips to "DONE".
  3. base64-decode the part after the comma into this folder's
     brand-banner.png.

Source assets (kept in the frontend, the single source of truth for both):
  - font:   web_app/public/fonts/CuteDino.woff2
  - mascot: web_app/src/assets/logo-mascot.png

Banner design: 520×132 (rendered at 2× = 1040×264) on the brand-accent
yellow (#fed224); mascot inset at the left, wordmark centred in dark ink.
"""
from __future__ import annotations

import base64
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]

_HTML = """<!doctype html><html><head><meta charset="utf-8">
<style>
@font-face { font-family:'Cute Dino'; src:url(data:font/woff2;base64,__FONT__) format('woff2'); }
body{margin:0;background:#ccc;} canvas{display:block;}
</style></head><body>
<canvas id="c"></canvas>
<script>
const SCALE=2, W=520, H=132;
const cv=document.getElementById('c');
cv.width=W*SCALE; cv.height=H*SCALE; cv.style.width=W+'px'; cv.style.height=H+'px';
const ctx=cv.getContext('2d'); ctx.scale(SCALE,SCALE);
const BG='#fed224', INK='#1d2733';
const masc=new Image();
async function draw(){
  await document.fonts.load("700 46px 'Cute Dino'");
  await document.fonts.ready;
  await new Promise((res,rej)=>{ masc.onload=res; masc.onerror=()=>rej('mascot load failed'); masc.src='data:image/png;base64,__MASC__'; });
  ctx.fillStyle=BG; ctx.fillRect(0,0,W,H);
  const m=100, my=(H-m)/2, mx=18; ctx.drawImage(masc, mx, my, m, m);
  ctx.fillStyle=INK; ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.font="700 46px 'Cute Dino'"; ctx.fillText('Dashy Dora', W/2, H/2 + 3);
  window.__PNG__=cv.toDataURL('image/png'); document.title='DONE';
}
draw().catch(e=>{ document.title='ERR:'+e; window.__ERR__=String(e); });
</script></body></html>"""


def main(out_dir: str) -> None:
    font_b64 = base64.b64encode(
        (_REPO_ROOT / "web_app/public/fonts/CuteDino.woff2").read_bytes()
    ).decode()
    masc_b64 = base64.b64encode(
        (_REPO_ROOT / "web_app/src/assets/logo-mascot.png").read_bytes()
    ).decode()
    html = _HTML.replace("__FONT__", font_b64).replace("__MASC__", masc_b64)
    out = pathlib.Path(out_dir) / "banner_gen.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
