"""Agno evals per team version (19): accuracy, reliability, agent-as-judge, on the multi-issue ticket T3."""
from agno.eval.accuracy import AccuracyEval
from agno.eval.agent_as_judge import AgentAsJudgeEval
from agno.eval.reliability import ReliabilityEval

from eat.config import get_model
from eat.events import publish
from eat.fs import TeamFS
from eat.harness import TICKETS
from eat.schemas import TeamDesign, TicketIn
from eat.team import TeamRunner


async def run_evals(design: TeamDesign, fs: TeamFS, kb, db) -> dict:
    t = next(t for t in TICKETS if t["id"] == "T3")
    model, _ = get_model()
    async with TeamRunner(design, fs, kb, db, run="evals") as runner:
        reply = await runner.solve(TicketIn(ticket_id="E3", customer_id="eval", text=t["text"]))
        outputs = runner.outputs
    expected = ", ".join(t["facts"])
    accuracy = await AccuracyEval(model=model, input=t["text"], expected_output=expected, name=f"accuracy-v{design.version}", db=db) \
        .arun_with_output(output=reply.reply, print_summary=False, print_results=False)
    judge = await AgentAsJudgeEval(model=model, criteria="The reply is polite and states only policy or order facts.",
                                   scoring_strategy="numeric", threshold=5, name=f"judge-v{design.version}", db=db) \
        .arun(input=t["text"], output=reply.reply)
    knowledge_run = next((o for o in outputs if any("search_knowledge" in (x.tool_name or "") for x in (o.tools or []))), None)
    reliability = ReliabilityEval(agent_response=knowledge_run, expected_tool_calls=["search_knowledge_base"],
                                  allow_additional_tool_calls=True, db=db).run() if knowledge_run else None
    result = {"version": design.version,
              "accuracy": getattr(accuracy.results[0], "score", None) if accuracy and accuracy.results else None,
              "judge_avg": getattr(judge, "avg_score", None),
              "reliability": getattr(reliability, "eval_status", "no knowledge call")}
    fs.save(design.version, "evals", result)
    publish("evals_done", **result)
    return result
