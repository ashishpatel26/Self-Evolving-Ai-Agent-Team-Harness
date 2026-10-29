"""Record the portal demo video (docs/assets/demo.mp4 + demo.gif).

Needs the backend on :7777 and the portal on :3000 already running, e.g.
    EAT_OFFLINE=1 uv run python -m eat.os_app      (simulator: fast, deterministic)
    cd ui && npm run start
then:
    uv run --with playwright python docs/assets/record_demo.py
Needs ffmpeg on PATH for the mp4/gif conversion.
"""
import shutil
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
URL = "http://localhost:3000"
W, H = 1440, 900


def nav(page, label):
    page.get_by_role("button", name=label).first.click()
    page.wait_for_timeout(1200)


def run_ticket(page, snippet, wait_ms):
    page.get_by_text(snippet).first.click()
    page.wait_for_timeout(700)
    page.get_by_role("button", name="Run with team").click()
    page.wait_for_timeout(wait_ms)


def launch(p):
    for channel in ("chrome", "msedge"):
        try:
            return p.chromium.launch(channel=channel)
        except Exception:
            pass
    return p.chromium.launch()


with sync_playwright() as p:
    browser = launch(p)
    tmp = HERE / "_video"
    ctx = browser.new_context(viewport={"width": W, "height": H}, record_video_dir=str(tmp), record_video_size={"width": W, "height": H})
    page = ctx.new_page()
    page.goto(URL)
    page.wait_for_timeout(3000)

    # 1. Live Desk: a real order question, then a prompt-injection attack
    run_ticket(page, "Where is order 1042", 16000)
    page.mouse.wheel(0, 700)
    page.wait_for_timeout(3500)
    page.mouse.wheel(0, -700)
    run_ticket(page, "Ignore previous instructions", 7000)

    # 2. Evolution: fresh team from v1, human approves every redesign in the UI
    nav(page, "Evolution")
    page.get_by_role("button", name="Start evolution").click()
    for _ in range(3):
        try:
            approve = page.get_by_role("button", name="Approve & launch")
            approve.wait_for(timeout=60000)
            page.wait_for_timeout(3500)  # let the viewer read the proposal
            approve.click()
        except Exception:
            break
    page.wait_for_timeout(9000)

    # 3. History and knowledge
    nav(page, "Team History")
    page.wait_for_timeout(5000)
    page.mouse.wheel(0, 800)
    page.wait_for_timeout(3000)
    nav(page, "Knowledge")
    page.wait_for_timeout(5000)

    video = page.video.path()
    ctx.close()
    browser.close()

webm = HERE / "demo.webm"
shutil.move(video, webm)
shutil.rmtree(tmp, ignore_errors=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(webm), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "26",
                "-movflags", "+faststart", str(HERE / "demo.mp4")], check=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(webm), "-vf",
                "fps=8,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=160[p];[b][p]paletteuse=dither=none",
                str(HERE / "demo.gif")], check=True)
webm.unlink()
for f in ("demo.mp4", "demo.gif"):
    print(f, f"{(HERE / f).stat().st_size / 1e6:.1f} MB")
