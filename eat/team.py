"""Turns a TeamDesign into running Agno agents (5, 8, 9-12) and solves tickets with it."""
import uuid

from agno.agent import Agent
from agno.run.base import RunStatus
from agno.team import Team
from agno.team.mode import TeamMode
from agno.tools.mcp import MCPTools
from agno.tools.reasoning import ReasoningTools

from eat.config import MCP_SERVER, get_model
from eat.events import publish, tool_hook
from eat.fs import TeamFS
from eat.guards import POST_HOOKS, PRE_HOOKS, is_injection
from eat.schemas import RoleSpec, TeamDesign, TicketIn, TicketReply

BLOCKED = TicketReply(category="blocked", issues=[], reply="Sorry, I can't help with that request.")


class TeamRunner:
    def __init__(self, design: TeamDesign, fs: TeamFS, kb, db, run: str = "eval"):
        self.design, self.fs, self.kb, self.db, self.run = design, fs, kb, db, run  # run: event channel (eval, live, ...)
        self.run_id = uuid.uuid4().hex[:8]  # every evaluation gets fresh sessions, so scores never see earlier runs
        self.model, self.fallbacks = get_model()
        self.mcp = MCPTools(server_params=MCP_SERVER, include_tools=["lookup_order"]) \
            if any("orders" in r.tools for r in design.roles) else None
        self.context = fs.context_for(design)  # the new team reads K before starting (component 3)
        self.roles = {r.name: r for r in design.roles}
        self.outputs = []  # every stage/member RunOutput of the last ticket, for evals

    async def __aenter__(self):
        if self.mcp:
            await self.mcp.connect()
        return self

    async def __aexit__(self, *exc):
        if self.mcp:
            await self.mcp.close()

    # --- building -------------------------------------------------------------------------
    def agent(self, role: RoleSpec, final: bool, ticket: TicketIn) -> Agent:
        tools = []
        if "reasoning" in role.tools:
            tools.append(ReasoningTools(add_instructions=True))  # ReAct: think/analyze before acting (8)
        if "orders" in role.tools and self.mcp:
            tools.append(self.mcp)  # MCP tools (7)
        return Agent(
            name=role.name, model=self.model, fallback_models=self.fallbacks or None,
            description=f"ROLE: {role.name}",
            instructions=[f"Your mandate: {role.mandate}", f"Team v{self.design.version} knowledge:\n{self.context}"],
            tools=tools,
            knowledge=self.kb if "knowledge" in role.tools else None,
            search_knowledge="knowledge" in role.tools,
            output_schema=TicketReply if final else None,  # structured output on the final answer (17)
            db=self.db, user_id=ticket.customer_id,  # per-customer isolation (9)
            add_history_to_context=True, num_history_runs=2,  # short-term memory inside this ticket's session (10)
            enable_agentic_memory=final,  # long-term user memory, written by the agent itself (10)
            session_state={"team_version": self.design.version},  # shared, persisted state (11)
            add_session_state_to_context=True,
            compress_tool_results=True,  # shrink long tool results (12)
            tool_call_limit=6, pre_hooks=PRE_HOOKS, post_hooks=POST_HOOKS,
            tool_hooks=[tool_hook(role.name, self.run)],  # live tool events for the portal
        )

    def stage(self, names: list[str], final: bool, ticket: TicketIn):
        if len(names) == 1:
            return self.agent(self.roles[names[0]], final, ticket)
        members = [self.agent(self.roles[n], False, ticket) for n in names]
        return Team(name="+".join(names), members=members, model=self.model, fallback_models=self.fallbacks or None,
                    mode=TeamMode.broadcast, instructions=["Send the task to all members, then return their answers unchanged."],
                    db=self.db, user_id=ticket.customer_id, tool_call_limit=6, pre_hooks=PRE_HOOKS, post_hooks=POST_HOOKS)

    # --- running --------------------------------------------------------------------------
    async def solve(self, ticket: TicketIn) -> TicketReply:
        """Run the stages in order. Raises RuntimeError / ValidationError on infrastructure or format failures,
        so the harness can tell them apart from a deliberate guardrail block."""
        tid = ticket.ticket_id
        publish("ticket_start", run=self.run, ticket=tid, text=ticket.text, version=self.design.version, stages=self.design.stages)
        if is_injection(ticket.text):
            publish("guardrail", run=self.run, ticket=tid, detail="prompt injection blocked before any model call")
            publish("ticket_end", run=self.run, ticket=tid, reply=BLOCKED.model_dump())
            return BLOCKED  # guardrail (15): refuse before any model call
        text, stages = f"TICKET: {ticket.text}", self.design.stages
        for i, names in enumerate(stages):
            last = i == len(stages) - 1
            publish("stage_start", run=self.run, ticket=tid, stage=i, roles=names)
            out = await self.stage(names, last, ticket).arun(
                text, user_id=ticket.customer_id, session_id=f"{self.run_id}-{ticket.ticket_id}-v{self.design.version}-s{i}")
            self.outputs += [out, *(getattr(out, "member_responses", None) or [])]
            content = out.content.model_dump() if hasattr(out.content, "model_dump") else str(out.content)[:1200]
            publish("stage_end", run=self.run, ticket=tid, stage=i, roles=names, ok=out.status != RunStatus.error, output=content,
                    tokens=getattr(out.metrics, "total_tokens", 0) or 0)
            if out.status == RunStatus.error:
                raise RuntimeError(f"stage {names} failed: {str(out.content)[:120]}")
            if last:
                reply = out.content if isinstance(out.content, TicketReply) else TicketReply.model_validate_json(out.content)
                publish("ticket_end", run=self.run, ticket=tid, reply=reply.model_dump())
                return reply
            text += f"\nPREVIOUS ({'+'.join(names)}): {str(out.content)[:1200]}"  # compact hand-off between stages (12)
        raise RuntimeError("design has no stages")
