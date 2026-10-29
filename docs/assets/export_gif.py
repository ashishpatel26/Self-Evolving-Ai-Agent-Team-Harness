"""Export the animated SVGs in this folder to GIFs (frame-stepped, so motion is smooth and deterministic).

    uv run --with playwright --with pillow python docs/assets/export_gif.py

Uses the locally installed Chrome (or Edge); no browser download.
"""
import io
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
JOBS = [  # (svg, width, height, loop seconds, fps)
    ("header.svg", 1200, 400, 12.0, 12),
    ("architecture.svg", 1640, 1090, 6.0, 10),
]

SEEK = """t => {
  document.getAnimations().forEach(a => { a.pause(); a.currentTime = t * 1000; });
  const svg = document.querySelector('svg');
  if (svg.pauseAnimations) { svg.pauseAnimations(); svg.setCurrentTime(t); }
}"""


def launch(p):
    for channel in ("chrome", "msedge"):
        try:
            return p.chromium.launch(channel=channel)
        except Exception:
            pass
    return p.chromium.launch()


with sync_playwright() as p:
    browser = launch(p)
    for name, w, h, seconds, fps in JOBS:
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto((HERE / name).resolve().as_uri())
        page.wait_for_timeout(500)
        frames = []
        for i in range(int(seconds * fps)):
            page.evaluate(SEEK, i / fps)
            frames.append(Image.open(io.BytesIO(page.screenshot(type="png"))).convert("RGB"))
        palette = frames[len(frames) // 2].quantize(colors=255, method=Image.Quantize.MEDIANCUT)  # one shared palette: no flicker
        gif = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
        out = HERE / name.replace(".svg", ".gif")
        gif[0].save(out, save_all=True, append_images=gif[1:], duration=int(1000 / fps), loop=0, optimize=True, disposal=1)
        print(f"{out.name}: {len(frames)} frames, {out.stat().st_size / 1e6:.1f} MB")
        page.close()
    browser.close()
