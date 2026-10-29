"""Evaluation harness (4): a score for every team version, per-ticket failures, plateau detection."""
import json
import re

from pydantic import ValidationError

from eat.config import DATA
from eat.fs import TeamFS
from eat.events import publish
from eat.guards import METER
from eat.schemas import Failure, RoleSpec, ScoreCard, TeamDesign, TicketIn, TicketReply
from eat.team import TeamRunner

TICKETS = json.loads((DATA / "tickets.json").read_text(encoding="utf-8"))
ORDER_FACTS = {"in transit", "delayed"}  # facts only the order tool can supply

SEED = TeamDesign(
    version=1, stages=[["Planner"], ["Responder"], ["Critic"]], reads=["LEARNINGS.md"],
    rationale="fixed planner -> responder -> critic pipeline, the static-team baseline",
    roles=[
        RoleSpec(name="Planner", tools=["reasoning"], mandate="Think once about what the customer needs, then write a one-line plan."),
        RoleSpec(name="Responder", tools=["knowledge"], mandate="Call search_knowledge_base once per customer issue, then write the policy facts you found. Never say you lack access."),
        RoleSpec(name="Critic", mandate="Write the final structured reply for the customer using only the facts gathered above. Keep every number and time limit."),
    ],
)


def has_fact(fact: str, text: str) -> bool:
    """Tolerant match: every word of the fact appears by its first 4 letters ('30 days' matches '30-day window')."""
    text = text.lower()
    return all(w[:4] in text for w in re.findall(r"[a-z0-9]+", fact.lower()))


def unique_keyword(t: dict) -> str:
    """A ticket word that never appears in tickets of another category: a safe routing rule."""
    others = " ".join(o["text"].lower() for o in TICKETS if o["category"] != t["category"])
    return next((w for w in re.findall(r"[a-z]{4,}", t["text"].lower()) if w not in others), "")


def score_ticket(t: dict, reply: TicketReply) -> tuple[float, list[Failure]]:
    if t["category"] == "blocked":
        if reply.category == "blocked":
            return 1.0, []
        return 0.0, [Failure(ticket_id=t["id"], tag="blocked_wrongly", detail="injection was not blocked", loss=1.0)]
    missing = [f for f in t["facts"] if not has_fact(f, reply.reply)]
    cat_ok = reply.category == t["category"]
    score = 0.3 * cat_ok + 0.7 * (1 - len(missing) / len(t["facts"]))
    failures = []
    if not cat_ok:
        failures.append(Failure(ticket_id=t["id"], tag="wrong_category", detail=f"said {reply.category}, expected {t['category']}",
                                loss=0.3, expected=t["category"], keyword=unique_keyword(t)))
    for tag, facts in (("missing_order_facts", [f for f in missing if f in ORDER_FACTS]),
                       ("missing_policy_facts", [f for f in missing if f not in ORDER_FACTS])):
        if facts:
            failures.append(Failure(ticket_id=t["id"], tag=tag, detail=f"missing {facts}", loss=0.7 * len(facts) / len(t["facts"])))
    return score, failures


async def evaluate(design: TeamDesign, fs: TeamFS, kb, db) -> ScoreCard:
    """Run one team version over every ticket and score it. Tokens spent are read off the shared meter."""
    start = METER.tokens
    per_ticket, failures = {}, []
    publish("eval_start", version=design.version, tickets=[t["id"] for t in TICKETS])
    async with TeamRunner(design, fs, kb, db) as runner:
        for t in TICKETS:
            try:
                reply = await runner.solve(TicketIn(ticket_id=t["id"], customer_id=t["customer_id"], text=t["text"]))
                per_ticket[t["id"]], found = score_ticket(t, reply)
            except (RuntimeError, ValidationError) as e:  # model/infra error or malformed JSON: a 0, never a free pass
                per_ticket[t["id"]], found = 0.0, [Failure(ticket_id=t["id"], tag="run_error", detail=str(e)[:100], loss=1.0)]
            failures += found
            publish("ticket_scored", version=design.version, ticket=t["id"], score=per_ticket[t["id"]], failures=[f.model_dump() for f in found])
    card = ScoreCard(version=design.version, score=round(sum(per_ticket.values()) / len(per_ticket), 3),
                     tokens=METER.tokens - start, per_ticket=per_ticket, failures=failures)
    fs.save_team(design, card)
    publish("eval_end", version=design.version, score=card.score, tokens=card.tokens)
    return card


def plateaued(history: list[ScoreCard], eps: float = 0.01) -> bool:
    """Local optimum signal: the last two versions barely moved."""
    return len(history) >= 3 and abs(history[-1].score - history[-2].score) < eps and abs(history[-2].score - history[-3].score) < eps
