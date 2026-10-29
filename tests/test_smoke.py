"""One offline end-to-end check: the supervisor must beat the fixed team. Run: EAT_OFFLINE=1 uv run python -m tests.test_smoke"""
import asyncio
import os

os.environ["EAT_OFFLINE"] = "1"

from eat import harness  # noqa: E402
from eat.config import RUNS, get_db, get_knowledge  # noqa: E402
from eat.supervisor import Supervisor  # noqa: E402


async def main():
    (RUNS / "test.db").unlink(missing_ok=True)
    sup = Supervisor("test", get_db("test"), get_knowledge())
    await sup.run()
    scores = [c.score for c in sup.fs.history()]
    assert scores[0] < 0.85 and scores[-1] >= 0.95, scores  # v1 has known weaknesses, evolved team fixes them
    assert scores == sorted(scores), scores  # every restructuring helped
    assert "RULE:" in sup.fs.read("LEARNINGS.md") and "v1 -> v2" in sup.fs.read("EVOLUTION.md")  # K was written
    blocked = next(t for t in harness.TICKETS if t["category"] == "blocked")
    assert harness.score_ticket(blocked, harness.TicketReply(category="blocked", reply="no"))[0] == 1.0
    print("OK", scores)


if __name__ == "__main__":
    asyncio.run(main())
