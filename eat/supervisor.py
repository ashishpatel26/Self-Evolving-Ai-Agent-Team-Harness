"""The supervisor (1, 2, 5, 14, 18): an Agno Workflow that evolves the team.

Loop body:  launch+score -> (monitor || digest) -> if below target: reflect -> diagnose -> redesign -> human gate -> adopt
Triggers:   a team finishing (every loop pass) and the scheduler (AgentOS cron re-enters the workflow, see os_app.py).
"""
import asyncio
import json
from collections import defaultdict

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.learn import LearnedKnowledgeConfig, LearningMachine, LearningMode
from agno.tools.reasoning import ReasoningTools
from agno.vectordb.lancedb import LanceDb
from agno.workflow import Condition, Loop, Parallel, Step, Workflow
from agno.workflow.types import StepInput, StepOutput

from eat import harness
from eat.evals import run_evals
from eat.events import publish
from eat.config import RUNS, TARGET_SCORE, get_embedder, get_model
from eat.fs import TeamFS
from eat.guards import METER, POST_HOOKS
from eat.schemas import Diagnosis, Reflection, ScoreCard, TeamDesign

SUPERVISOR_RULES = [
    "You are the supervisor of a support-ticket team. Diagnose WHY the score is stuck, then change roles, stages or knowledge.",
    "Invent focused roles when needed; never edit roles that already work. Fix the costliest failure tag first.",
    "Role tools: knowledge = search policy documents; orders = look up an order status; reasoning = think step by step.",
    "TeamDesign.stages run in order; roles inside one stage run in parallel. The last stage is one role that writes the reply.",
    "Fixes: missing_order_facts -> add a role with tools ['orders'] into the Responder stage; "
    "missing_policy_facts -> insert a role 'Issue Splitter' (no tools, mandate: split the ticket into issues, one per line) before the Responder; "
    "wrong_category -> keep the structure and rely on the RULE lines in LEARNINGS.md. "
    "local_optimum (score stopped moving) -> add a 'Challenger' role with tools ['knowledge'] into the Responder stage to question the answer.",
    "The new design MUST have version = current version + 1 and reuse existing roles unchanged.",
]


def validate_design(d: TeamDesign, current: TeamDesign, knowledge_only: bool) -> TeamDesign:
    if d.version != current.version + 1:
        raise ValueError(f"version must be {current.version + 1}")
    if not knowledge_only and d.stages == current.stages and d.roles == current.roles:
        raise ValueError("the design is unchanged; add or restructure a role to fix the failure")
    names = {r.name for r in d.roles}
    if not d.stages or len(d.stages[-1]) != 1:
        raise ValueError("last stage must be one integrator role")
    if {n for s in d.stages for n in s} - names:
        raise ValueError("stage uses an undefined role")
    return d


def loss_by_tag(card: ScoreCard) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for f in card.failures:
        out[f.tag] += f.loss
    return dict(out)


class Supervisor:
    def __init__(self, name: str, db, kb, approve: str = "auto", token_budget: int = 10**9, max_iterations: int = 8):
        self.fs, self.db, self.kb, self.approve = TeamFS(db, name), db, kb, approve
        self.token_budget, self.max_iterations, self.done, self.start_tokens = token_budget, max_iterations, False, 0
        self.gate: asyncio.Future | None = None  # approve == "ui": the portal resolves this with (choice, rationale)
        self.curve: list[tuple[int, float]] = []  # (cumulative tokens incl. supervisor overhead, score) per team version
        self.model, self.fallbacks = get_model()
        embedder = get_embedder()  # the one embedder, so the lessons table is per namespace and per embedder (dimensions differ)
        lessons_kb = Knowledge(name="lessons", vector_db=LanceDb(
            uri=str(RUNS / "lancedb"), table_name=f"lessons_{name}_{type(embedder).__name__}".replace("-", "_"), embedder=embedder))
        self.reflector = self._agent("Reflector", Reflection, learning=LearningMachine(  # learning (14): lessons persist, searchable
            db=db, model=self.model, knowledge=lessons_kb, learned_knowledge=LearnedKnowledgeConfig(mode=LearningMode.AGENTIC)))
        self.diagnoser = self._agent("Diagnoser", Diagnosis)
        self.designer = self._agent("Designer", TeamDesign, tools=[ReasoningTools(add_instructions=True)])  # ReAct (8)

    def _agent(self, name, schema, **kw) -> Agent:
        return Agent(name=name, model=self.model, fallback_models=self.fallbacks or None, description=f"ROLE: {name}",
                     instructions=SUPERVISOR_RULES, output_schema=schema, db=self.db, user_id="supervisor",
                     enable_session_summaries=True, add_session_summary_to_context=True,  # memory of earlier cycles (9, 10)
                     post_hooks=POST_HOOKS, **kw)

    async def _ask(self, agent: Agent, instruction: str, payload: dict):
        out = await agent.arun(f"{instruction}\nPAYLOAD:{json.dumps(payload)}", user_id="supervisor",
                               session_id=f"sup-{self.fs.name}")
        return out.content

    # --- workflow steps: all state lives in the shared, persisted session_state (11) -----------------
    async def launch_and_score(self, step_input: StepInput, run_context) -> StepOutput:
        st = run_context.session_state
        self.done, st["iteration"] = False, st.get("iteration", 0) + 1
        if st["iteration"] == 1:
            self.start_tokens, self.curve = METER.tokens, []
        design = self.fs.latest_design() or harness.SEED  # K is the source of truth, so a cron re-entry continues where we stopped
        st["design"] = design.model_dump()
        publish("phase", phase="launch", iteration=st["iteration"], version=design.version, design=st["design"], coordination=design.coordination)
        self.fs.save_team(design)  # artifacts of this team version
        known = self.fs.history()
        if known and known[-1].version == design.version and known[-1].score >= TARGET_SCORE:
            card = known[-1]  # cron re-entry on a team that already meets the target: do not pay to re-score it
        else:
            card = await harness.evaluate(design, self.fs, self.kb, self.db)
        st["card"] = card.model_dump()
        st.setdefault("scores", []).append(card.score)
        self.curve.append((METER.tokens - self.start_tokens, card.score))
        return StepOutput(content=f"v{design.version} score={card.score} tokens={card.tokens}")

    async def monitor(self, step_input: StepInput, run_context) -> StepOutput:
        st = run_context.session_state
        card = ScoreCard(**st["card"])
        losses = loss_by_tag(card)
        st["focus_tag"] = max(losses, key=losses.get) if losses else "none"
        st["plateau"] = harness.plateaued(self.fs.history())  # local-optimum signal
        spent = METER.tokens - self.start_tokens
        self.done = st["done"] = card.score >= TARGET_SCORE or spent >= self.token_budget
        publish("phase", phase="monitor", version=card.version, score=card.score, losses=losses, focus_tag=st["focus_tag"], plateau=st["plateau"], done=st["done"])
        return StepOutput(content={"losses": losses, "plateau": st["plateau"], "done": st["done"]})

    async def evals(self, step_input: StepInput, run_context) -> StepOutput:
        """Agno evals for this version, run next to the monitor. Their tokens are excluded from the budget."""
        design = TeamDesign(**run_context.session_state["design"])
        with METER.exclude():
            return StepOutput(content=await run_evals(design, self.fs, self.kb, self.db))

    def below_target(self, step_input: StepInput, run_context) -> bool:
        """Redesign only if we are short of the target AND another pass will evaluate the result."""
        st = run_context.session_state
        return not st["done"] and st["iteration"] < self.max_iterations

    async def reflect(self, step_input: StepInput, run_context) -> StepOutput:
        st = run_context.session_state
        card = ScoreCard(**st["card"])
        refl = await self._ask(self.reflector, "Reflect on failure and success patterns of this team version.", {
            "failures": [f.model_dump() for f in card.failures], "focus_tag": st["focus_tag"], "scores": st["scores"]})
        self.fs.add_learnings(card.version, refl.lessons)  # empirical observations go to K
        st["reflection"] = "; ".join(refl.patterns)
        publish("phase", phase="reflect", version=card.version, patterns=refl.patterns, lessons=refl.lessons)
        return StepOutput(content=refl.model_dump())

    async def diagnose(self, step_input: StepInput, run_context) -> StepOutput:
        st = run_context.session_state
        diag = await self._ask(self.diagnoser, "Diagnose the root cause of the plateau.", {
            "focus_tag": st["focus_tag"], "plateau": st["plateau"], "reflection": st["reflection"]})
        st["diagnosis"] = diag.model_dump()
        publish("phase", phase="diagnose", **st["diagnosis"])
        return StepOutput(content=diag.model_dump())

    async def redesign(self, step_input: StepInput, run_context) -> StepOutput:
        st = run_context.session_state
        current, error = TeamDesign(**st["design"]), ""
        st["proposal"], st["approved"] = None, False  # nothing carries over from the previous cycle
        for _ in range(3):  # re-ask with the validation error until the proposal is usable
            new = await self._ask(self.designer, "Design the next team: roles, stages (solo/pipeline/parallel) and files to read.", {
                "design": st["design"], "focus_tag": st["diagnosis"]["focus_tag"], "diagnosis": st["diagnosis"], "previous_error": error})
            try:
                st["proposal"] = validate_design(new, current, st["diagnosis"]["cause"] == "knowledge_gap").model_dump()
                publish("phase", phase="redesign", proposal=st["proposal"], coordination=new.coordination)
                return StepOutput(content=f"proposal v{new.version}: {new.coordination} {new.stages} because {new.rationale}")
            except ValueError as e:
                error = str(e)
                publish("phase", phase="redesign_retry", error=error)
        st["proposal"] = None
        self.done = st["done"] = True
        publish("phase", phase="redesign_failed", error=error)
        return StepOutput(content=f"no valid proposal: {error}")

    async def human_gate(self, step_input: StepInput, run_context) -> StepOutput:
        """Human-in-the-loop (18): approve, reject, or edit the rationale before the new team launches."""
        st = run_context.session_state
        if not st.get("proposal"):
            return StepOutput(content="no proposal")
        p = TeamDesign(**st["proposal"])
        choice = "r" if self.approve == "reject" else "a"
        if self.approve == "ui":  # the portal shows the proposal and POSTs the decision to /ui/gate
            self.gate = asyncio.get_running_loop().create_future()
            self.gate_proposal = st["proposal"]  # so a reloaded portal can reopen the gate from /ui/state
            publish("gate_waiting", proposal=st["proposal"])
            try:
                choice, rationale = await asyncio.wait_for(self.gate, timeout=1800)
            except asyncio.TimeoutError:
                choice, rationale = "r", ""  # nobody answered: fail safe, do not adopt
            if rationale:
                p.rationale = rationale
                st["proposal"] = p.model_dump()
            self.gate = None
        elif self.approve == "ask":
            print(f"\nProposed v{p.version}: {p.coordination} {p.stages}\n  why: {p.rationale}")
            choice = ""
            try:
                while choice not in ("a", "r", "e"):  # re-prompt on typos; input() runs off the event loop
                    choice = (await asyncio.to_thread(input, "[a]pprove / [r]eject / [e]dit rationale > ")).strip().lower()
                if choice == "e":
                    p.rationale, choice = await asyncio.to_thread(input, "new rationale > "), "a"
                    st["proposal"] = p.model_dump()
            except EOFError:
                choice = "r"  # no terminal attached: fail safe, do not adopt
        st["approved"] = choice == "a"
        self.done = st["done"] = st["done"] or not st["approved"]
        publish("phase", phase="gate", approved=st["approved"], mode=self.approve)
        return StepOutput(content="approved" if st["approved"] else "rejected")

    async def adopt(self, step_input: StepInput, run_context) -> StepOutput:
        st = run_context.session_state
        if not (st.get("approved") and st.get("proposal")):
            self.fs.add_learnings(st["card"]["version"], ["supervisor proposal was rejected or invalid, team kept"])
            return StepOutput(content="kept current team")
        new = TeamDesign(**st["proposal"])
        self.fs.log_evolution(st["card"]["version"], st["reflection"], new)  # evolution history in K
        self.fs.save_team(new)  # the next launch_and_score reads it from K
        publish("phase", phase="adopt", version=new.version, design=new.model_dump(), coordination=new.coordination)
        st["design"] = new.model_dump()
        return StepOutput(content=f"launching v{new.version}")

    # --- assembly ---------------------------------------------------------------------------------------
    def workflow(self) -> Workflow:
        redesign = Condition(name="redesign_if_below_target", evaluator=self.below_target, steps=[
            Step(name="reflect", executor=self.reflect), Step(name="diagnose", executor=self.diagnose),
            Step(name="redesign", executor=self.redesign), Step(name="human_gate", executor=self.human_gate),
            Step(name="adopt", executor=self.adopt)])
        loop = Loop(name="supervisor_loop", max_iterations=self.max_iterations, end_condition=lambda outs: self.done, steps=[
            Step(name="launch_and_score", executor=self.launch_and_score),
            Parallel(Step(name="monitor", executor=self.monitor), Step(name="evals", executor=self.evals), name="observe"),
            redesign])
        return Workflow(name="evolving-supervisor", id="evolving-supervisor", db=self.db, steps=[loop],
                        session_state={"design": harness.SEED.model_dump()})  # overwritten from K on every launch

    async def run(self):
        publish("run_start", namespace=self.fs.name, approve=self.approve, max_iterations=self.max_iterations)
        try:
            return await self.workflow().arun(input="evolve the support team", user_id="supervisor")
        finally:
            publish("run_end", namespace=self.fs.name, scores=[c.score for c in self.fs.history()])
