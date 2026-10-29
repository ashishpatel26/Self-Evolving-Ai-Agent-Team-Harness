"""Portal API (/ui/*): live SSE events, team state from K, run a ticket, start an evolution, answer the human gate.

Mounted into AgentOS as its base app (see os_app.py). The Next.js portal in ui/ proxies to it.
"""
import asyncio
import json
import os
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from eat import events, harness
from eat.config import LLM, OFFLINE
from eat.fs import TeamFS
from eat.schemas import TeamDesign, TicketIn
from eat.supervisor import Supervisor
from eat.team import TeamRunner


def require_key(authorization: str = Header(default="")):
    key = os.getenv("OS_SECURITY_KEY")
    if key and authorization != f"Bearer {key}":
        raise HTTPException(401, "invalid or missing bearer key")


class TicketBody(BaseModel):
    text: str
    customer_id: str = "portal-user"


class EvolveBody(BaseModel):
    approve: str = "ui"  # ui (decide in the portal) | auto | reject
    max_iterations: int = 4
    fresh: bool = False  # start a new team namespace from the v1 seed instead of continuing K


class GateBody(BaseModel):
    decision: str  # approve | reject
    rationale: str = ""


def build_router(sup: Supervisor) -> APIRouter:
    r = APIRouter(prefix="/ui", dependencies=[Depends(require_key)])
    tasks: dict[str, asyncio.Task] = {}  # keeps background runs alive; "evolve" guards a single supervisor run

    def evolving() -> bool:
        return "evolve" in tasks and not tasks["evolve"].done()

    @r.get("/state")
    def state():
        fs = sup.fs
        history = []
        for card in fs.history():
            v = card.version
            evals = fs.read(f"teams/v{v}/evals.json")
            design = TeamDesign.model_validate_json(fs.read(f"teams/v{v}/design.json"))
            history.append({**card.model_dump(), "design": design.model_dump(), "coordination": design.coordination,
                            "evals": json.loads(evals) if evals else None})
        current = fs.latest_design() or harness.SEED
        return {"model": "offline simulator" if OFFLINE else LLM, "offline": OFFLINE, "namespace": fs.name,
                "current": {**current.model_dump(), "coordination": current.coordination}, "history": history,
                "learnings": fs.read("LEARNINGS.md"), "evolution": fs.read("EVOLUTION.md"),
                "tickets": harness.TICKETS, "evolving": evolving(), "gate_open": sup.gate is not None,
                "gate_proposal": getattr(sup, "gate_proposal", None) if sup.gate is not None else None}

    @r.get("/events")
    async def stream():
        q = events.subscribe()

        async def gen():
            try:
                for ev in list(events.BACKLOG):
                    yield f"data: {json.dumps(ev, default=str)}\n\n"
                yield f"data: {json.dumps({'kind': 'ready'})}\n\n"
                while True:
                    try:
                        ev = await asyncio.wait_for(q.get(), timeout=15)
                        yield f"data: {json.dumps(ev, default=str)}\n\n"
                    except asyncio.TimeoutError:
                        yield ": keep-alive\n\n"
            finally:
                events.unsubscribe(q)

        return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @r.post("/tickets")
    async def solve(body: TicketBody):
        """Run the current team on one ticket; progress arrives on /ui/events under run=live-<id>."""
        tid = f"L-{uuid.uuid4().hex[:6]}"
        design = sup.fs.latest_design() or harness.SEED
        sample = next((t for t in harness.TICKETS if t["text"].strip() == body.text.strip()), None)

        async def go():
            try:
                async with TeamRunner(design, sup.fs, sup.kb, sup.db, run=f"live-{tid}") as runner:
                    reply = await runner.solve(TicketIn(ticket_id=tid, customer_id=body.customer_id, text=body.text[:4000]))
                if sample:  # a known ticket: show how the harness would score this reply
                    score, failures = harness.score_ticket(sample, reply)
                    events.publish("live_scored", run=f"live-{tid}", ticket=tid, sample=sample["id"], score=score,
                                   failures=[f.model_dump() for f in failures])
            except Exception as e:  # surface every failure to the portal instead of dying silently
                events.publish("ticket_error", run=f"live-{tid}", ticket=tid, error=str(e)[:300])

        tasks[tid] = asyncio.create_task(go())
        return {"ticket": tid, "run": f"live-{tid}", "version": design.version}

    @r.post("/evolve")
    async def evolve(body: EvolveBody):
        if evolving():
            raise HTTPException(409, "an evolution run is already in progress")
        if body.approve not in ("ui", "auto", "reject"):
            raise HTTPException(422, "approve must be ui, auto or reject")
        sup.approve, sup.max_iterations = body.approve, max(1, min(body.max_iterations, 8))
        if body.fresh:
            sup.fs = TeamFS(sup.db, f"team-{uuid.uuid4().hex[:6]}")

        async def go():
            try:
                await sup.run()
            except Exception as e:
                events.publish("run_error", error=str(e)[:300])

        tasks["evolve"] = asyncio.create_task(go())
        return {"started": True, "approve": sup.approve, "max_iterations": sup.max_iterations}

    @r.post("/gate")
    def gate(body: GateBody):
        if sup.gate is None or sup.gate.done():
            raise HTTPException(409, "no proposal is waiting for a decision")
        sup.gate.set_result(("a" if body.decision == "approve" else "r", body.rationale.strip()))
        return {"ok": True}

    return r
