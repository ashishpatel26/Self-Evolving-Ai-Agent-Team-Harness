"""Pydantic contracts for every agent input/output (component 17)."""
from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["refund", "shipping", "damaged", "warranty", "account", "billing", "subscription", "blocked"]
Tool = Literal["knowledge", "orders", "reasoning"]  # capability bundles a role may use


class TicketIn(BaseModel):
    ticket_id: str
    customer_id: str
    text: str


class TicketReply(BaseModel):
    category: Category
    issues: list[str] = Field(default_factory=list, description="each distinct customer issue")
    reply: str = Field(description="customer-facing answer, built only from retrieved policy and order facts")


class RoleSpec(BaseModel):
    name: str
    mandate: str = Field(description="what this role must do, and what it must not do")
    tools: list[Tool] = Field(default_factory=list)


class TeamDesign(BaseModel):
    """T = (Roles, Coordination, Knowledge) from the paper."""
    version: int
    stages: list[list[str]] = Field(description="role names; stages run in order, roles inside a stage run in parallel")
    roles: list[RoleSpec]
    reads: list[str] = Field(default_factory=lambda: ["LEARNINGS.md"], description="files every agent reads first")
    rationale: str = ""

    @property
    def coordination(self) -> str:
        if len(self.stages) == 1 and len(self.stages[0]) == 1:
            return "solo"
        return "parallel" if any(len(s) > 1 for s in self.stages) else "pipeline"


class Failure(BaseModel):
    ticket_id: str
    tag: Literal["wrong_category", "missing_policy_facts", "missing_order_facts", "blocked_wrongly", "run_error"]
    detail: str
    loss: float
    expected: str = ""  # expected category, for routing failures
    keyword: str = ""   # ticket word that is unique to this category (candidate routing rule)


class ScoreCard(BaseModel):
    version: int
    score: float
    tokens: int
    per_ticket: dict[str, float]
    failures: list[Failure]


class Reflection(BaseModel):
    patterns: list[str] = Field(description="observed failure and success patterns")
    lessons: list[str] = Field(description="empirical observations to append to LEARNINGS.md")


class Diagnosis(BaseModel):
    cause: Literal["knowledge_gap", "missing_capability", "bad_coordination", "local_optimum", "none"]
    summary: str
    focus_tag: str = Field(description="the failure tag that costs the most score")
