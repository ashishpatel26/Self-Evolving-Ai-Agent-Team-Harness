"""Offline simulator so the whole harness runs with no API key (demo + tests).

MockModel is a tiny rule-based "LLM": it obeys the prompt it is given (mandates, learnings,
tool results) and makes real ReAct tool calls. It is NOT a language model; with real keys
config.get_model() returns Claude/OpenAI instead and none of this file is used.
"""
import hashlib
import json
import math
import re
import uuid
from dataclasses import dataclass
from typing import Any

from agno.knowledge.embedder.base import Embedder
from agno.metrics import MessageMetrics
from agno.models.base import Model
from agno.models.response import ModelResponse

from eat.schemas import RoleSpec, TeamDesign

# ponytail: keyword router, a real model would classify; learned RULE lines override it.
DEFAULT_ROUTES = [("return", "refund"), ("refund", "refund"), ("broken", "damaged"), ("order", "shipping"),
                  ("package", "shipping"), ("warranty", "warranty"), ("stopped working", "warranty"),
                  ("password", "account"), ("cancel", "subscription")]
RULE = re.compile(r'RULE: if ticket mentions "([^"]+)" then category=(\w+)')


def route(ticket: str, rules_text: str) -> str:
    t = ticket.lower()
    for kw, cat in RULE.findall(rules_text):
        if kw in t:
            return cat
    return next((cat for kw, cat in DEFAULT_ROUTES if kw in t), "account")


def split_issues(ticket: str) -> list[str]:
    return [p.strip() for p in re.split(r"\s+and\s+", ticket) if p.strip()]


def ticket_of(text: str) -> str:
    m = re.search(r"TICKET: (.*)", text)
    return m.group(1) if m else text


def clean(result: str) -> str:
    """Keep the useful text of a knowledge-search result (a real LLM would summarise it the same way)."""
    try:
        docs = json.loads(result)
        return " ".join(" ".join(d["content"].split()) for d in docs)
    except (ValueError, TypeError, KeyError):
        return " ".join(result.split())


def args_for(tool: dict, hints: dict) -> str:
    """Fill a tool call's arguments from its JSON schema."""
    params = tool["function"].get("parameters", {})
    out = {}
    for name in params.get("required", list(params.get("properties", {}))):
        kind = params["properties"].get(name, {}).get("type", "string")
        out[name] = hints.get(name, 0.8 if kind == "number" else 1 if kind == "integer" else "ok")
    return json.dumps(out)


def fill(schema: dict) -> dict:
    """Generic structured answer for schemas we do not simulate (judges, summaries)."""
    out = {}
    for name, p in schema.get("properties", {}).items():
        kind = p.get("type") or next((o.get("type") for o in p.get("anyOf", []) if o.get("type") != "null"), None)
        out[name] = (8 if "score" in name else 1) if kind in ("integer", "number") else True if kind == "boolean" \
            else [] if kind == "array" else {} if kind == "object" else "ok"
    return out


def design_next(payload: dict) -> dict:
    """Mock supervisor policy: fix the failure tag that costs most (what an LLM supervisor does by reasoning)."""
    d = TeamDesign(**payload["design"])
    tag = payload["focus_tag"]
    roles, stages = list(d.roles), [list(s) for s in d.stages]
    names = {r.name for r in roles}
    why = f"fix '{tag}' without touching what already works"
    if tag == "missing_policy_facts" and "Issue Splitter" not in names:
        roles.append(RoleSpec(name="Issue Splitter", mandate="Split the ticket into separate issues, one per line. Never answer."))
        i = next(i for i, s in enumerate(stages) if "Responder" in s)
        stages.insert(i, ["Issue Splitter"])
        why = "single-query retrieval misses facts on multi-issue tickets; add a focused splitter before the responder"
    elif tag == "missing_order_facts" and "Order Investigator" not in names:
        roles.append(RoleSpec(name="Order Investigator", tools=["orders"],
                              mandate="Look up the order id in the ticket and report its status. Never quote policy."))
        next(s for s in stages if "Responder" in s).append("Order Investigator")
        why = "responder has no order access; add a parallel branch that owns order lookups"
    elif payload.get("diagnosis", {}).get("cause") == "local_optimum" and "Challenger" not in names:
        roles.append(RoleSpec(name="Challenger", tools=["knowledge"], mandate="Question the answer and look for facts the team skipped."))
        next(s for s in stages if "Responder" in s).append("Challenger")
        why = "score plateaued: add a fresh-eyes challenger beside the responder"
    elif tag == "wrong_category":
        why = "routing errors are a knowledge gap; learned RULE lines were added to LEARNINGS.md which every agent reads"
    return TeamDesign(version=d.version + 1, stages=stages, roles=roles, reads=d.reads, rationale=why).model_dump()


@dataclass
class MockModel(Model):
    id: str = "mock-sim"
    name: str = "MockModel"
    provider: str = "mock"
    supports_native_structured_outputs: bool = True  # Agno then passes the pydantic class itself as response_format

    # --- the single decision function -------------------------------------------------
    def _respond(self, messages, response_format, tools) -> ModelResponse:
        system = next((str(m.content) for m in messages if m.role == "system"), "")
        last_user = max(i for i, m in enumerate(messages) if m.role == "user")
        user, after = str(messages[last_user].content), messages[last_user + 1:]
        tool_defs = {t["function"]["name"]: t for t in (tools or [])}
        results = [str(m.content) for m in after if m.role == "tool"]
        done = [tc["function"]["name"] + tc["function"]["arguments"] for m in after if m.role == "assistant"
                for tc in (m.tool_calls or [])]
        call = self._next_call(system, user, tool_defs, done)
        if call:
            name, hints = call
            tc = {"id": str(uuid.uuid4()), "type": "function",
                  "function": {"name": name, "arguments": args_for(tool_defs[name], hints)}}
            return self._wrap(content=None, tool_calls=[tc], size=len(user))
        return self._wrap(content=self._final(system, user, results, response_format), size=len(user))

    def _next_call(self, system, user, tool_defs, done):
        ticket = ticket_of(user)
        plan: list[tuple[str, dict]] = []
        if "think" in tool_defs:
            plan.append(("think", {"title": "plan", "thought": f"Plan how to resolve: {ticket}"}))
        if "delegate_task_to_members" in tool_defs:
            plan.append(("delegate_task_to_members", {"task": user}))
        knowledge = next((n for n in tool_defs if "search_knowledge" in n), None)
        if knowledge:
            issues = re.search(r"ISSUES: (.*)", user)
            for q in (issues.group(1).split(" | ") if issues else [ticket]):
                plan.append((knowledge, {"query": q}))
        order = re.search(r"\b10\d\d\b", ticket)
        if "lookup_order" in tool_defs and order:
            plan.append(("lookup_order", {"order_id": order.group()}))
        for name, hints in plan:
            key = name + args_for(tool_defs[name], hints)
            if key not in done:
                return name, hints
        return None

    def _final(self, system, user, results, response_format):
        schema = getattr(response_format, "__name__", "")
        ticket = ticket_of(user)
        if schema == "TicketReply":
            evidence = " ".join(re.findall(r"FACTS: (.*)", user) + [clean(r) for r in results])
            m = re.search(r"ISSUES: (.*)", user)
            issues = m.group(1).split(" | ") if m else [ticket]
            return json.dumps({"category": route(ticket, system + user), "issues": issues,
                               "reply": f"Hello, thanks for contacting us. {evidence}"})
        if schema == "AccuracyAgentResponse":  # judge: share of expected facts present in the output
            want = re.search(r"<expected_output>\s*(.*?)\s*</expected_output>", user, re.S).group(1).split(", ")
            got = re.search(r"<agent_output>(.*?)</agent_output>", user, re.S).group(1).lower()
            hit = sum(w.lower() in got for w in want)
            return json.dumps({"accuracy_score": round(1 + 9 * hit / len(want)), "accuracy_reason": f"{hit}/{len(want)} expected facts present"})
        if schema == "Reflection":
            return json.dumps(self._reflect(user))
        if schema == "Diagnosis":
            p = json.loads(user.split("PAYLOAD:", 1)[1])
            tag = p["focus_tag"]
            cause = {"wrong_category": "knowledge_gap", "missing_order_facts": "missing_capability",
                     "missing_policy_facts": "bad_coordination"}.get(tag, "none")
            return json.dumps({"cause": "local_optimum" if p.get("plateau") else cause,
                               "summary": f"most score lost to {tag}", "focus_tag": tag})
        if schema == "TeamDesign":
            return json.dumps(design_next(json.loads(user.split("PAYLOAD:", 1)[1])))
        if response_format is not None:
            js = response_format if isinstance(response_format, dict) else response_format.model_json_schema()
            return json.dumps(fill(js.get("json_schema", {}).get("schema", js)))
        low = system.lower()
        if "role: planner" in low:
            return "PLAN: resolve the ticket using policy facts"
        if "mandate: split" in low:
            return "ISSUES: " + " | ".join(split_issues(ticket))
        body = " ".join(clean(r) for r in results) if results else user
        return f"{'FACTS' if results else 'REVIEWED'}: {body}"

    def _reflect(self, user):
        p = json.loads(user.split("PAYLOAD:", 1)[1])
        patterns = [f"{f['ticket_id']}: {f['tag']} ({f['detail']})" for f in p["failures"]]
        lessons = []
        for f in p["failures"]:
            if f["tag"] == "wrong_category" and p["focus_tag"] == "wrong_category":
                lessons.append(f'RULE: if ticket mentions "{f["keyword"]}" then category={f["expected"]}')
            else:
                lessons.append(f"{f['ticket_id']} lost {f['loss']:.2f} to {f['tag']}: {f['detail']}")
        return {"patterns": patterns or ["no failures"], "lessons": lessons}

    def _wrap(self, content, size, tool_calls=None) -> ModelResponse:
        r = ModelResponse(role="assistant", content=content, tool_calls=tool_calls or [])
        n = size // 4 + 1
        r.response_usage = MessageMetrics(input_tokens=n, output_tokens=len(content or "x") // 4 + 1, total_tokens=n + len(content or "x") // 4 + 1)
        return r

    # --- Agno Model plumbing ------------------------------------------------------------
    def invoke(self, messages, assistant_message=None, response_format=None, tools=None, **kw):
        return self._respond(messages, response_format, tools)

    async def ainvoke(self, messages, assistant_message=None, response_format=None, tools=None, **kw):
        return self._respond(messages, response_format, tools)

    def invoke_stream(self, messages, assistant_message=None, response_format=None, tools=None, **kw):
        yield self._respond(messages, response_format, tools)

    async def ainvoke_stream(self, messages, assistant_message=None, response_format=None, tools=None, **kw):
        yield self._respond(messages, response_format, tools)

    def _parse_provider_response(self, response: Any, **kw) -> ModelResponse:
        return response

    def _parse_provider_response_delta(self, response: Any) -> ModelResponse:
        return response


STOPWORDS = set("i my me you your we the a an is are was were of to and for in it on at after also how do get back where "
                "if or but be been with this that from by as has have had will can".split())


@dataclass
class HashEmbedder(Embedder):
    """Bag-of-words hashing embedder: offline stand-in for OpenAIEmbedder (same Embedder interface)."""
    dimensions: int = 1024

    def get_embedding(self, text: str) -> list[float]:
        vec = [0.0] * self.dimensions
        for w in re.findall(r"[a-z0-9]+", text.lower()):
            if w in STOPWORDS:
                continue
            w = re.sub(r"(ing|ed|s)$", "", w)
            vec[int(hashlib.md5(w.encode()).hexdigest(), 16) % self.dimensions] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def get_embedding_and_usage(self, text):
        return self.get_embedding(text), None

    async def async_get_embedding(self, text):
        return self.get_embedding(text)

    async def async_get_embedding_and_usage(self, text):
        return self.get_embedding(text), None
