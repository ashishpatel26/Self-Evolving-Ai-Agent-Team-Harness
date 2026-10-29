"""Models + fallback (6), database (9), knowledge/RAG (13). One place for every provider choice."""
import os
import sys
from pathlib import Path

from agno.db.sqlite import SqliteDb
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb

from mcp import StdioServerParameters

from eat.offline import HashEmbedder, MockModel

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RUNS = ROOT / "runs"
MCP_SERVER = StdioServerParameters(command=sys.executable, args=["-m", "eat.mcp_server"], cwd=str(ROOT))  # any install path
TARGET_SCORE = 0.95

# .env support without a dependency: KEY=VALUE lines, real environment variables win
for _line in (ROOT / ".env").read_text(encoding="utf-8").splitlines() if (ROOT / ".env").exists() else []:
    if "=" in _line and not _line.lstrip().startswith("#"):
        os.environ.setdefault(_line.split("=", 1)[0].strip(), _line.split("=", 1)[1].strip())

OFFLINE = os.getenv("EAT_OFFLINE") == "1"  # rule-based simulator for tests/CI only, never the default
LLM = os.getenv("EAT_MODEL", "qwen3.5-4b-16k:latest")  # local Qwen served by Ollama
FALLBACK_LLM = os.getenv("EAT_FALLBACK_MODEL", "gemma2:9b")  # local fallback if Qwen errors
EMBED = os.getenv("EAT_EMBED_MODEL", "nomic-embed-text")  # the single embedder for knowledge + lessons
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


def ollama(model_id: str):
    from agno.models.ollama import Ollama
    return Ollama(id=model_id, host=OLLAMA_HOST, options={"temperature": 0, "num_ctx": 16384}, request_params={"think": False}, timeout=600)


def get_model():
    """Primary model + fallbacks (6). Returns (primary, [fallbacks])."""
    if OFFLINE:
        return MockModel(), []
    return ollama(LLM), [ollama(FALLBACK_LLM)] if FALLBACK_LLM else []


def get_embedder():
    if OFFLINE:
        return HashEmbedder()
    from agno.knowledge.embedder.ollama import OllamaEmbedder
    return OllamaEmbedder(id=EMBED, dimensions=768, host=OLLAMA_HOST)


def get_db(name: str = "eat") -> SqliteDb:
    RUNS.mkdir(exist_ok=True)
    return SqliteDb(db_file=str(RUNS / f"{name}.db"))


def get_knowledge() -> Knowledge:
    """Policy RAG (13): LanceDB vector store + the one Ollama embedder."""
    embedder = get_embedder()
    kb = Knowledge(name="policies", max_results=1,  # ponytail: top-1 keeps context small; raise if recall suffers
                   vector_db=LanceDb(uri=str(RUNS / "lancedb"), table_name=f"policies_{type(embedder).__name__}", embedder=embedder))
    kb.insert(path=str(DATA / "policies"), skip_if_exists=True)
    return kb
