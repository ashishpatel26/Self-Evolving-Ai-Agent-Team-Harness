"""Generates docs/assets/architecture.svg (animated data-flow architecture).

    uv run python docs/assets/gen_architecture.py docs/assets/architecture.svg
"""
import pathlib, sys

W, H = 1640, 1090
out = []
add = out.append

COL = {  # lane: (x, w, title, icon, color)
    "fe":   (30,  300, "FRONTEND", "Next.js portal · ui/", "#22d3ee"),
    "os":   (370, 310, "RUNTIME", "AgentOS · FastAPI :7777", "#a78bfa"),
    "core": (720, 520, "AGENT CORE", "eat/ · Agno SDK", "#f472b6"),
    "data": (1280, 330, "DATA · MODELS · TOOLS", "local-first infra", "#34d399"),
}
FLOW = {"req": "#a78bfa", "live": "#22d3ee", "data": "#34d399", "tel": "#fbbf24"}

def card(id_, x, y, w, h, icon, title, sub="", chips=(), accent="#a78bfa", delay=0.0):
    add(f'<g id="{id_}" class="card" style="animation-delay:{delay:.2f}s">')
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" class="box" stroke="{accent}"/>')
    add(f'<rect x="{x}" y="{y}" width="4" height="{h}" rx="2" fill="{accent}"/>')
    add(f'<circle cx="{x+26}" cy="{y+22}" r="14" fill="{accent}" fill-opacity="0.14" class="ico" style="animation-delay:{delay*1.7:.2f}s"/>')
    add(f'<text x="{x+26}" y="{y+27}" class="emoji">{icon}</text>')
    add(f'<text x="{x+48}" y="{y+21}" class="t">{title}</text>')
    if sub:
        add(f'<text x="{x+48}" y="{y+36}" class="s">{sub}</text>')
    cx, cy = x + 12, y + (59 if sub else 46)
    for c in chips:
        cw = 7 * len(c) + 16
        if cx + cw > x + w - 8:
            cx, cy = x + 12, cy + 22
        add(f'<rect x="{cx}" y="{cy-13}" width="{cw}" height="18" rx="9" class="chip" stroke="{accent}"/>')
        add(f'<text x="{cx+cw/2}" y="{cy}" class="c">{c}</text>')
        cx += cw + 6
    add('</g>')
    return (x, y, w, h)

# ---------- document ----------
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
    'aria-label="Animated architecture of the Evolving Support Team: Next.js portal, AgentOS runtime, Agno agent core, and local data, model and tool infrastructure">')
add('''<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#06060c"/><stop offset="1" stop-color="#0c0a1c"/></linearGradient>
<linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8b5cf6"/><stop offset="1" stop-color="#22d3ee"/></linearGradient>
<pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="#fff" stroke-opacity="0.04"/></pattern>
<radialGradient id="g1"><stop offset="0" stop-color="#8b5cf6" stop-opacity=".35"/><stop offset="1" stop-color="#8b5cf6" stop-opacity="0"/></radialGradient>
<radialGradient id="g2"><stop offset="0" stop-color="#22d3ee" stop-opacity=".25"/><stop offset="1" stop-color="#22d3ee" stop-opacity="0"/></radialGradient>
<radialGradient id="g3"><stop offset="0" stop-color="#34d399" stop-opacity=".22"/><stop offset="1" stop-color="#34d399" stop-opacity="0"/></radialGradient>
<filter id="blur" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="2.5"/></filter>
</defs>
<style>
text{font-family:'Segoe UI','Inter',system-ui,-apple-system,sans-serif}
.h1{font-size:30px;font-weight:800;fill:#f5f5ff;letter-spacing:-.5px}
.h2{font-size:14px;fill:#9a9ac0}
.lane{fill:#ffffff;fill-opacity:.018;stroke:#ffffff;stroke-opacity:.07}
.lt{font-size:11px;font-weight:700;letter-spacing:2.4px}
.ls{font-size:13px;font-weight:600;fill:#d9d9f2}
.box{fill:#110f24;fill-opacity:.92;stroke-width:1.2;stroke-opacity:.55}
.t{font-size:13px;font-weight:700;fill:#f1f1ff}
.s{font-size:11px;fill:#9a9ac0}
.c{font-size:10.5px;font-weight:600;fill:#d4d4f0;text-anchor:middle;font-family:ui-monospace,'Cascadia Code',Consolas,monospace}
.chip{fill:#ffffff;fill-opacity:.04;stroke-opacity:.35}
.emoji{font-size:14px;text-anchor:middle}
.card{}
.ico{animation:breathe 3.2s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
.wire{fill:none;stroke-width:1.5;stroke-opacity:.28}
.flow{fill:none;stroke-width:1.6;stroke-dasharray:5 9;animation:dash 1.4s linear infinite}
.rev{animation-direction:reverse}
.lg{font-size:12px;fill:#c9c9e6}
.blob{animation:drift 16s ease-in-out infinite alternate}
@keyframes in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes breathe{0%,100%{transform:scale(1);fill-opacity:.12}50%{transform:scale(1.25);fill-opacity:.3}}
@keyframes dash{to{stroke-dashoffset:-28}}
@keyframes drift{from{transform:translate(0,0)}to{transform:translate(50px,-40px)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}.card{opacity:1}}
</style>''')
add(f'<rect width="{W}" height="{H}" fill="url(#bg)"/><rect width="{W}" height="{H}" fill="url(#grid)"/>')
add('<circle class="blob" cx="560" cy="420" r="320" fill="url(#g1)"/>')
add('<circle class="blob" cx="1430" cy="700" r="300" fill="url(#g3)" style="animation-delay:-6s"/>')
add('<circle class="blob" cx="180" cy="300" r="240" fill="url(#g2)" style="animation-delay:-3s"/>')
add('<text x="30" y="52" class="h1">🧬 Evolving Support Team · architecture &amp; data flow</text>')
add('<text x="32" y="78" class="h2">Every box is a real component in this repo. Dots show live traffic: requests, streamed events, persistence and telemetry.</text>')

TOP, BOT = 100, 1000
for k, (x, w, t, s, col) in COL.items():
    add(f'<rect x="{x-10}" y="{TOP}" width="{w+20}" height="{BOT-TOP}" rx="18" class="lane"/>')
    add(f'<text x="{x+4}" y="{TOP+26}" class="lt" fill="{col}">{t}</text>')
    add(f'<text x="{x+4}" y="{TOP+45}" class="ls">{s}</text>')

C = {}
cyan, vio, pink, grn, amb = "#22d3ee", "#a78bfa", "#f472b6", "#34d399", "#fbbf24"
d = iter(i * 0.07 for i in range(200))

# ---------- frontend ----------
x, w = 30, 300
C["user"] = card("user", x, 165, w, 52, "🧑‍💼", "Support lead / user", "browser · http://localhost:3000", accent=cyan, delay=next(d))
C["live"] = card("live", x, 235, w, 74, "🎫", "Live Desk", "submit ticket · watch agents work",
                 ("agent graph", "tool chips", "reply"), cyan, next(d))
C["evo"] = card("evo", x, 323, w, 74, "🔁", "Evolution", "supervisor loop, live",
                ("score grid", "loss bars", "gate modal"), cyan, next(d))
C["hist"] = card("hist", x, 411, w, 74, "📈", "Team History", "versions · lineage · evals",
                 ("score chart", "invented roles"), cyan, next(d))
C["know"] = card("know", x, 499, w, 56, "📚", "Knowledge", "LEARNINGS.md · EVOLUTION.md", accent=cyan, delay=next(d))
C["motion"] = card("motion", x, 573, w, 74, "✨", "Motion layer", "framer-motion · event playback queue",
                   ("~350ms pacing", "SVG chart"), cyan, next(d))
C["sse_c"] = card("sse_c", x, 665, w, 56, "📡", "EventSource client", "GET /api/events (SSE)", accent=cyan, delay=next(d))
C["proxy"] = card("proxy", x, 739, w, 74, "🔀", "API proxy · route.js", "app/api/[...path] → :7777/ui/*",
                  ("adds Bearer key", "streams SSE"), cyan, next(d))
C["env_fe"] = card("env_fe", x, 831, w, 56, "🔐", ".env (server-side)", "EAT_API_URL · OS_SECURITY_KEY", accent=cyan, delay=next(d))

# ---------- runtime ----------
x, w = 370, 310
C["auth"] = card("auth", x, 165, w, 56, "🛡️", "Bearer auth", "OS_SECURITY_KEY · 401 otherwise", accent=vio, delay=next(d))
C["portal"] = card("portal", x, 239, w, 96, "🧩", "Portal API · ui_api.py", "/ui/*",
                   ("GET state", "POST tickets", "POST evolve", "POST gate"), vio, next(d))
C["sse"] = card("sse", x, 353, w, 56, "📡", "SSE stream", "GET /ui/events · backlog + keep-alive", accent=vio, delay=next(d))
C["bus"] = card("bus", x, 427, w, 74, "🛰️", "Event bus · events.py", "publish() from any thread",
                ("tool hooks", "stage events", "phases"), vio, next(d))
C["native"] = card("native", x, 519, w, 74, "⚙️", "AgentOS native API", "/workflows · /agents · /docs",
                   ("streaming", "background runs"), vio, next(d))
C["cron"] = card("cron", x, 611, w, 56, "⏰", "Scheduler", "cron supervisor-check · */30", accent=vio, delay=next(d))
C["trace"] = card("trace", x, 685, w, 74, "🔭", "Observability", "setup_tracing · OpenInference",
                  ("AgnoInstrumentor", "OTLP exporter"), vio, next(d))
C["meter"] = card("meter", x, 777, w, 56, "🧮", "Token meter", "post-hook · matched budget", accent=vio, delay=next(d))
C["cli"] = card("cli", x, 851, w, 74, "⌨️", "CLI entry points", "uv run python -m …",
                ("eat.demo", "eat.os_app", "test_smoke"), vio, next(d))

# ---------- core: two sub-columns ----------
xa, xb, w = 720, 990, 250
C["sup"] = card("sup", xa, 165, w, 118, "🧑‍✈️", "Supervisor Workflow", "supervisor.py · Agno Workflow",
                ("Loop", "Parallel", "Condition", "Step", "session_state"), pink, next(d))
C["refl"] = card("refl", xa, 301, w, 74, "🪞", "Reflector agent", "patterns → lessons",
                 ("LearningMachine", "agentic"), pink, next(d))
C["diag"] = card("diag", xa, 393, w, 56, "🩺", "Diagnoser agent", "cause · focus tag · plateau", accent=pink, delay=next(d))
C["design"] = card("design", xa, 467, w, 74, "📐", "Designer agent", "new TeamDesign, validated, 3 retries",
                   ("ReasoningTools", "v = N+1"), pink, next(d))
C["gate"] = card("gate", xa, 559, w, 74, "🙋", "Human gate", "approve · edit · reject",
                 ("cli ask", "portal ui", "auto"), pink, next(d))
C["harness"] = card("harness", xa, 651, w, 74, "📊", "Harness · harness.py", "score = .3 category + .7 facts",
                    ("failure tags", "plateau"), pink, next(d))
C["evals"] = card("evals", xa, 743, w, 74, "✅", "Agno evals · evals.py", "per version, outside budget",
                  ("Accuracy", "Judge", "Reliability"), pink, next(d))
C["fs"] = card("fs", xa, 835, w, 96, "🗂️", "Persistent FS · K", "fs.py · agno.fs.FileSystem",
               ("LEARNINGS.md", "EVOLUTION.md", "teams/vN/*.json"), pink, next(d))

C["runner"] = card("runner", xb, 165, w, 74, "🏗️", "TeamRunner · team.py", "TeamDesign → agents",
                   ("solo", "pipeline", "parallel"), pink, next(d))
C["guard"] = card("guard", xb, 257, w, 74, "🛡️", "Guardrails · pre-hooks", "intake screen before any model call",
                  ("injection", "PII mask", "length"), pink, next(d))
C["agents"] = card("agents", xb, 349, w, 118, "🤖", "Agents &amp; Teams", "stage = Agent · multi-role = Team",
                   ("Planner", "Responder", "Critic", "+ invented", "broadcast"), pink, next(d))
C["react"] = card("react", xb, 485, w, 56, "💭", "ReAct · ReasoningTools", "think · analyze before acting", accent=pink, delay=next(d))
C["mem"] = card("mem", xb, 559, w, 74, "🧠", "Memory &amp; sessions", "per-customer user_id isolation",
                ("history", "summaries", "memory"), pink, next(d))
C["ctx"] = card("ctx", xb, 651, w, 74, "🗜️", "Context management", "compress tool results · K compaction",
                ("RULE kept", "1200-char hand-off"), pink, next(d))
C["schema"] = card("schema", xb, 743, w, 74, "📦", "Pydantic IO · schemas.py", "structured output",
                   ("TicketReply", "TeamDesign", "+4"), pink, next(d))
C["fallback"] = card("fallback", xb, 835, w, 56, "🛟", "Model fallback", "primary → fallback_models", accent=pink, delay=next(d))

# ---------- data ----------
x, w = 1280, 330
C["ollama"] = card("ollama", x, 165, w, 96, "🦙", "Ollama · localhost:11434", "the only LLM provider",
                   ("qwen3.5-4b-16k", "gemma2:9b", "nomic-embed-text"), grn, next(d))
C["lance"] = card("lance", x, 279, w, 74, "🧭", "LanceDB · vector DB", "768-dim embeddings",
                  ("policies_*", "lessons_*"), grn, next(d))
C["kb"] = card("kb", x, 371, w, 56, "📖", "Agno Knowledge · RAG", "search_knowledge_base · top-1", accent=grn, delay=next(d))
C["sqlite"] = card("sqlite", x, 445, w, 118, "🗄️", "SQLite · runs/*.db", "SqliteDb · aiosqlite",
                   ("sessions", "memories", "FS K", "evals", "traces", "schedules"), grn, next(d))
C["mcp"] = card("mcp", x, 581, w, 74, "🔌", "MCP server · mcp_server.py", "stdio · MCPTools",
                ("lookup_order", "1042 · 1043 · 1044"), grn, next(d))
C["files"] = card("files", x, 673, w, 74, "📄", "data/", "policy docs + benchmark tickets",
                  ("policies/*.md", "tickets.json"), grn, next(d))
C["langfuse"] = card("langfuse", x, 765, w, 74, "📈", "Langfuse cloud", "OTLP /api/public/otel",
                     ("traces", "spans", "costs"), amb, next(d))
C["offline"] = card("offline", x, 857, w, 74, "🧪", "Offline simulator", "EAT_OFFLINE=1 · tests/CI only",
                    ("MockModel", "HashEmbedder"), grn, next(d))

# ---------- edges ----------
def anchor(k, side):
    x, y, w, h = C[k]
    return {"r": (x + w, y + h / 2), "l": (x, y + h / 2), "t": (x + w / 2, y), "b": (x + w / 2, y + h)}[side]

edges = []
def edge(a, sa, b, sb, kind, dur=2.6, rev=False, bend=0):
    (x1, y1), (x2, y2) = anchor(a, sa), anchor(b, sb)
    if sa in "rl" and sb in "rl":
        dx = max(40, abs(x2 - x1) / 2)
        c1 = x1 + (dx if sa == "r" else -dx)
        c2 = x2 + (-dx if sb == "l" else dx)
        p = f"M{x1:.0f} {y1:.0f} C{c1:.0f} {y1+bend:.0f} {c2:.0f} {y2+bend:.0f} {x2:.0f} {y2:.0f}"
    else:
        p = f"M{x1:.0f} {y1:.0f} C{x1:.0f} {(y1+y2)/2:.0f} {x2:.0f} {(y1+y2)/2:.0f} {x2:.0f} {y2:.0f}"
    edges.append((p, FLOW[kind], dur, rev))

edge("live", "r", "proxy", "r", "req", bend=0)
edge("proxy", "r", "auth", "l", "req")
edge("auth", "b", "portal", "t", "req", 1.6)
edge("portal", "r", "sup", "l", "req")
edge("portal", "r", "runner", "l", "req", 3.0, bend=-30)
edge("cron", "r", "sup", "l", "req", 3.2, bend=-60)
edge("native", "r", "sup", "l", "req", 3.0, bend=-40)
edge("sup", "r", "runner", "l", "req", 2.0)
edge("harness", "r", "runner", "l", "req", 2.8)
edge("runner", "b", "guard", "t", "req", 1.2)
edge("guard", "b", "agents", "t", "req", 1.2)
edge("agents", "r", "ollama", "l", "req", 2.2)
edge("agents", "r", "kb", "l", "req", 2.4)
edge("kb", "b", "lance", "b", "data", 1.4)
edge("agents", "r", "mcp", "l", "req", 2.6)
edge("files", "l", "kb", "l", "data", 3.0, bend=0)
edge("refl", "r", "lance", "l", "data", 3.4, bend=40)
edge("design", "r", "ollama", "l", "req", 3.6, bend=-120)
edge("fs", "r", "sqlite", "l", "data", 3.0, bend=-60)
edge("mem", "r", "sqlite", "l", "data", 2.4)
edge("evals", "r", "sqlite", "l", "data", 3.0, bend=-30)
edge("trace", "r", "langfuse", "l", "tel", 4.0, bend=200)
edge("trace", "r", "sqlite", "l", "tel", 4.2, bend=120)
# live events flow back to the browser
edge("sup", "l", "bus", "r", "live", 2.0)
edge("agents", "l", "bus", "r", "live", 2.4, bend=40)
edge("harness", "l", "bus", "r", "live", 2.6)
edge("bus", "t", "sse", "b", "live", 1.0)
edge("sse", "l", "sse_c", "r", "live", 2.0)
edge("sse_c", "t", "motion", "b", "live", 1.0)
edge("motion", "t", "know", "b", "live", 1.0)

add('<g id="edges">')
for i, (p, col, dur, rev) in enumerate(edges):
    add(f'<path id="p{i}" d="{p}" class="wire" stroke="{col}"/>')
    add(f'<path d="{p}" class="flow{" rev" if rev else ""}" stroke="{col}" stroke-opacity=".7"/>')
    begin = (i * 0.37) % dur
    add(f'<circle r="5" fill="{col}" filter="url(#blur)"><animateMotion dur="{dur}s" begin="-{begin:.2f}s" repeatCount="indefinite" rotate="auto"><mpath href="#p{i}"/></animateMotion></circle>')
    add(f'<circle r="2.4" fill="#fff"><animateMotion dur="{dur}s" begin="-{begin:.2f}s" repeatCount="indefinite"><mpath href="#p{i}"/></animateMotion></circle>')
add('</g>')

# cards above edges: move card group after edges
cards_start = next(i for i, s in enumerate(out) if s.startswith('<g id="user"'))
edges_block = out[out.index('<g id="edges">'):]
del out[out.index('<g id="edges">'):]
out[cards_start:cards_start] = edges_block

# legend
lx, ly = 30, 1030
add(f'<rect x="{lx-10}" y="{ly-22}" width="{W-40}" height="44" rx="12" class="lane"/>')
for i, (lab, col) in enumerate((("request / control flow", FLOW["req"]), ("live events → portal (SSE)", FLOW["live"]),
                                 ("persistence · vectors", FLOW["data"]), ("telemetry · OpenInference → Langfuse", FLOW["tel"]))):
    px = lx + i * 330
    add(f'<line x1="{px}" y1="{ly}" x2="{px+34}" y2="{ly}" stroke="{col}" stroke-width="2" class="flow"/>')
    add(f'<circle cx="{px+17}" cy="{ly}" r="3.5" fill="{col}"/>')
    add(f'<text x="{px+44}" y="{ly+4}" class="lg">{lab}</text>')
add(f'<text x="{W-30}" y="{ly+4}" class="lg" text-anchor="end" fill="#8a8ab0" style="fill:#8a8ab0">21 harness components · Agno SDK only · 100% local models</text>')
add('</svg>')

pathlib.Path(sys.argv[1]).write_text("\n".join(out), encoding="utf-8")
print("edges", len(edges), "cards", len(C))
