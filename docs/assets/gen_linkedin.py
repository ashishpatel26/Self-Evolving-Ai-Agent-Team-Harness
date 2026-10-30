"""LinkedIn post version of the architecture animation: 1080x1350 (4:5 portrait, the feed's largest format).

    uv run --with playwright python docs/assets/gen_linkedin.py

Writes linkedin-architecture.html (the design), then frame-steps it in Chrome/Edge and encodes
linkedin-architecture.gif and linkedin-architecture.mp4 (native video autoplays best on LinkedIn). Needs ffmpeg on PATH.
"""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
W, H, LOOP, FPS = 1080, 1350, 6.0, 15
REPO = "github.com/ashishpatel26/Self-Evolving-Ai-Agent-Team-Harness"

svg = (HERE / "architecture.svg").read_text(encoding="utf-8")
# crop the diagram's own title and legend; the post supplies its own
svg = re.sub(r'viewBox="[^"]+" width="\d+" height="\d+"', 'viewBox="12 96 1616 908" width="1048" height="589"', svg, count=1)

STATS = [("42", "components"), ("30", "live data flows"), ("4", "layers"), ("0", "cloud APIs")]
STEPS = ["Launch", "Score", "Reflect", "Diagnose", "Redesign", "Approve", "Adopt v+1"]
LEGEND = [("#a78bfa", "requests"), ("#22d3ee", "live events"), ("#34d399", "data · vectors"), ("#fbbf24", "telemetry")]

html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0}}
body{{width:{W}px;height:{H}px;overflow:hidden;background:#06060c;font-family:'Segoe UI','Inter',system-ui,sans-serif;color:#f5f5ff}}
.bg{{position:absolute;inset:0;background:
  radial-gradient(600px 400px at 85% 8%,rgba(139,92,246,.30),transparent 70%),
  radial-gradient(520px 420px at 8% 92%,rgba(34,211,238,.20),transparent 70%),
  linear-gradient(160deg,#06060c,#0d0b1f);}}
.grid{{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px);background-size:30px 30px}}
.wrap{{position:relative;padding:54px 16px 0}}
.tag{{margin:0 30px;display:inline-flex;gap:10px;align-items:center;font-size:15px;font-weight:700;letter-spacing:3px;color:#c4b5fd}}
.dot{{width:9px;height:9px;border-radius:50%;background:#34d399;box-shadow:0 0 0 0 rgba(52,211,153,.7);animation:ping 1.6s ease-out infinite}}
h1{{margin:18px 30px 0;font-size:60px;line-height:1.04;font-weight:800;letter-spacing:-1.8px}}
h1 span{{background:linear-gradient(90deg,#8b5cf6,#22d3ee);-webkit-background-clip:text;background-clip:text;color:transparent}}
.sub{{margin:18px 30px 0;font-size:22px;line-height:1.4;color:#a8a8c8}}
.sub b{{color:#e9e9ff;font-weight:600}}
.diagram{{margin:30px 0 0;border-radius:22px;border:1px solid rgba(255,255,255,.09);background:rgba(10,9,22,.6);padding:0;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.5),0 0 0 1px rgba(139,92,246,.15) inset}}
.diagram svg{{display:block}}
.legend{{display:flex;gap:22px;justify-content:center;margin:16px 0 0;font-size:15px;color:#c9c9e6}}
.legend i{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:8px;vertical-align:middle}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:22px 14px 0}}
.stat{{padding:16px 10px;border-radius:16px;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.08);text-align:center}}
.stat b{{display:block;font-size:40px;font-weight:800;background:linear-gradient(90deg,#c4b5fd,#67e8f9);-webkit-background-clip:text;background-clip:text;color:transparent}}
.stat span{{font-size:15px;color:#a8a8c8}}
.foot{{position:absolute;left:46px;right:46px;bottom:36px;display:flex;justify-content:space-between;align-items:flex-end;font-size:15px;color:#8f8fb2}}
.foot b{{display:block;color:#e9e9ff;font-size:17px;font-weight:600;margin-bottom:4px}}
.loop{{margin:26px 14px 0;padding:18px 18px 16px;border-radius:18px;border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.025)}}
.loop-t{{font-size:13px;font-weight:700;letter-spacing:2.6px;color:#f9a8d4;margin:0 0 12px 4px}}
.steps{{display:flex;align-items:center;gap:6px}}
.step{{flex:1;text-align:center;padding:11px 4px;border-radius:12px;font-size:16px;font-weight:600;color:#a8a8c8;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);animation:lit {LOOP}s linear infinite}}
.arr{{color:#5b5b80;font-size:16px}}
@keyframes lit{{0%,14%{{color:#fff;background:linear-gradient(90deg,rgba(139,92,246,.55),rgba(34,211,238,.45));border-color:rgba(167,139,250,.9);box-shadow:0 0 22px rgba(139,92,246,.45)}}18%,100%{{color:#a8a8c8;background:rgba(255,255,255,.04);border-color:rgba(255,255,255,.08);box-shadow:none}}}}
@keyframes ping{{0%{{box-shadow:0 0 0 0 rgba(52,211,153,.7)}}100%{{box-shadow:0 0 0 12px rgba(52,211,153,0)}}}}
</style></head><body><div class="bg"></div><div class="grid"></div><div class="wrap">
<div class="tag"><span class="dot"></span>OPEN SOURCE · AGNO SDK · 100% LOCAL LLMs</div>
<h1>An AI agent team that<br><span>rebuilds itself.</span></h1>
<p class="sub">A supervisor <b>diagnoses failures</b>, <b>invents new roles</b>, a human approves,<br>and team v<b>N+1</b> launches — streamed live to a Next.js portal.</p>
<div class="diagram">{svg}</div>
<div class="legend">{''.join(f'<span><i style="background:{c}"></i>{t}</span>' for c, t in LEGEND)}</div>
<div class="loop"><div class="loop-t">THE SUPERVISOR LOOP · EVERY TEAM VERSION</div><div class="steps">{'<span class="arr">→</span>'.join(f'<div class="step" style="animation-delay:{i * LOOP / len(STEPS) - LOOP:.3f}s">{t}</div>' for i, t in enumerate(STEPS))}</div></div>
<div class="stats">{''.join(f'<div class="stat"><b>{n}</b><span>{t}</span></div>' for n, t in STATS)}</div>
</div>
<div class="foot"><div><b>{REPO}</b>Next.js · AgentOS · Agno · Ollama + Qwen · LanceDB · SQLite · MCP · Langfuse</div>
<div style="text-align:right">Based on “Evolving Agent Teams”<br>UC Berkeley · arXiv 2610.36848</div></div>
</body></html>"""
page_file = HERE / "linkedin-architecture.html"
page_file.write_text(html, encoding="utf-8")

SEEK = """t => {
  document.getAnimations().forEach(a => { a.pause(); a.currentTime = t * 1000; });
  document.querySelectorAll('svg').forEach(s => { s.pauseAnimations(); s.setCurrentTime(t); });
}"""

frames = Path(tempfile.mkdtemp())
with sync_playwright() as p:
    browser = None
    for channel in ("chrome", "msedge", None):
        try:
            browser = p.chromium.launch(channel=channel) if channel else p.chromium.launch()
            break
        except Exception:
            pass
    page = browser.new_page(viewport={"width": W, "height": H})
    page.goto(page_file.resolve().as_uri())
    page.wait_for_timeout(600)
    for i in range(int(LOOP * FPS)):
        page.evaluate(SEEK, i / FPS)
        page.screenshot(path=str(frames / f"f{i:04d}.png"))
    browser.close()

src = ["-framerate", str(FPS), "-i", str(frames / "f%04d.png")]
# mp4: loop the seamless 6 s cycle 3x (18 s) so LinkedIn's player shows it moving long enough
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "2", *src, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-crf", "20", "-r", "30", "-movflags", "+faststart", str(HERE / "linkedin-architecture.mp4")], check=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *src, "-vf",
                "fps=10,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle",
                "-loop", "0", str(HERE / "linkedin-architecture.gif")], check=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(frames / "f0030.png"), str(HERE / "linkedin-architecture.png")], check=True)
shutil.rmtree(frames, ignore_errors=True)
for f in ("linkedin-architecture.mp4", "linkedin-architecture.gif", "linkedin-architecture.png"):
    print(f, f"{(HERE / f).stat().st_size / 1e6:.1f} MB")
