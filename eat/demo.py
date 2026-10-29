"""Demo + key ablation (R7): evolving team vs fixed teams at a matched token budget.

    uv run python -m eat.demo [--approve auto|ask|reject]
"""
import argparse
import asyncio
import json
import shutil

from eat import harness
from eat.config import OFFLINE, RUNS, get_db, get_knowledge, get_model
from eat.fs import TeamFS
from eat.guards import METER
from eat.observability import setup_observability
from eat.schemas import RoleSpec, TeamDesign
from eat.supervisor import Supervisor

SOLO = TeamDesign(version=1, stages=[["Solo"]], rationale="single generalist agent baseline", roles=[
    RoleSpec(name="Solo", tools=["knowledge", "reasoning"], mandate="Answer the ticket yourself using the policy knowledge base.")])


async def fixed_baseline(name: str, design: TeamDesign, budget: int, kb, db, max_runs: int = 3) -> list[tuple[int, float]]:
    """Re-run an unchanged team until it has spent the same tokens as the evolving run."""
    fs, start, curve = TeamFS(db, name), METER.tokens, []
    fs.save_team(design)
    while METER.tokens - start < budget and len(curve) < max_runs:  # cap: real LLM episodes take minutes
        card = await harness.evaluate(design, fs, kb, db)
        curve.append((METER.tokens - start, card.score))
    return curve


def best_within(curve, budget):
    return max((s for t, s in curve if t <= budget), default=0.0)


async def main(approve: str, versions: int):
    (RUNS / "demo.db").unlink(missing_ok=True)  # fresh run: K lives in this database
    for stale in (RUNS / "lancedb").glob("lessons_demo*"):  # and so do the Reflector's learned lessons
        shutil.rmtree(stale, ignore_errors=True)
    db, kb = get_db("demo"), get_knowledge()
    print(setup_observability(db))  # observability (20)
    print(f"model: {get_model()[0].id}" + ("  (OFFLINE rule-based simulator, wiring only)" if OFFLINE else "  via Ollama") + "\n")

    sup = Supervisor("demo-evolving", db, kb, approve=approve, max_iterations=versions)
    await sup.run()
    budget = sup.curve[-1][0]  # tokens up to the last scored team version, supervisor overhead included
    print(f"{'ver':>3} {'score':>6} {'tokens':>7} {'coordination':<9} stages")
    for card, (cum, _) in zip(sup.fs.history(), sup.curve):
        d = TeamDesignLoad(sup.fs, card.version)
        print(f"v{card.version:<2} {card.score:>6.3f} {cum:>7} {d.coordination:<9} {d.stages}")
        print(f"      evals: {sup.fs.read(f'teams/v{card.version}/evals.json').replace(chr(10), ' ')}")

    fixed = await fixed_baseline("demo-fixed", harness.SEED, budget, kb, db)
    solo = await fixed_baseline("demo-solo", SOLO, budget, kb, db)
    print(f"\nMatched budget = {budget} tokens (evolving run incl. supervisor overhead)")
    print(f"{'budget':>8} {'evolving':>9} {'fixed 3-role':>13} {'solo':>6}")
    for frac in (0.25, 0.5, 0.75, 1.0):
        b = int(budget * frac)
        print(f"{b:>8} {best_within(sup.curve, b):>9.3f} {best_within(fixed, b):>13.3f} {best_within(solo, b):>6.3f}")
    (RUNS / "demo-results.json").write_text(json.dumps({"budget": budget, "evolving": sup.curve, "fixed": fixed, "solo": solo}), encoding="utf-8")
    print("\nLEARNINGS.md (read by every later team):")
    print(sup.fs.read("LEARNINGS.md"))


def TeamDesignLoad(fs: TeamFS, version: int) -> TeamDesign:
    return TeamDesign.model_validate_json(fs.read(f"teams/v{version}/design.json"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--approve", default="auto", choices=["auto", "ask", "reject"], help="human gate for each redesign")
    ap.add_argument("--versions", type=int, default=5, help="max team versions the supervisor may evaluate")
    args = ap.parse_args()
    asyncio.run(main(args.approve, args.versions))
