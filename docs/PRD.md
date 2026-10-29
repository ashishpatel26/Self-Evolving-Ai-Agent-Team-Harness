# PRD: Self-Evolving Support Team (Evolving Agent Teams on Agno)

## 1. Problem
Fixed agent teams plateau. In "Evolving Agent Teams" (Cao et al., UC Berkeley, arXiv 2610.36848) a fixed 4-role team
reached 0.31x of expert performance and a single agent 0.28x, while a team that is restructured by a supervisor
reached 0.74x at the same token budget. Reason: each phase of a hard task needs different roles, coordination and
knowledge, and a static team stays mismatched to the current phase.

## 2. Paper in one page
| Idea | Detail |
|---|---|
| Team `T = (Roles R, Coordination Pi, Knowledge M)` | all three are designed by a supervisor, none is fixed |
| Supervisor loop | Monitor -> Reflect -> Redesign -> Launch next team `T(v+1)` |
| Triggers | a team finishes, or a periodic cron check |
| Invented roles | Disciplinarian, Focused Debugger, Knowledge Integrator, Challenger, Fresh-Eyes, Profiler ... (paper Table 3) |
| Coordination | solo, pipeline (research -> implement -> profile), parallel branches, or a mix |
| Persistent file system `K` | `LEARNINGS.md` (empirical observations), evolution history (reflections + designs), per-team artifacts |
| Key ablation | evolving team vs fixed team vs single agent at a **matched token budget** |

## 3. Use case: customer-support ticket resolution
A team answers support tickets. A fixed rubric scores each reply, so every team version has a number.

**Why it suits a self-evolving team**
- The work has phases with different bottlenecks: first routing and policy lookup, then multi-issue tickets, then live order data.
- Failures are diagnosable and differ per version (wrong category vs missing facts vs missing tool access), so the right fix is a new role, a new coordination shape, or new knowledge. Tuning the same prompt does not fix them.
- Knowledge must survive restructuring (routing rules learned in v2 must still be used by v5), which is the persistent-file-system argument of the paper.
- Cheap to score, deterministic to test, safe to run repeatedly.

**Score** (per ticket, mean over the ticket set): `0.3 * category correct + 0.7 * required-fact coverage`.
Injection tickets score 1.0 only when the guardrail blocks them.

**Starting team v1 (the fixed baseline)**: Planner -> Responder -> Critic (pipeline).
Known weaknesses the supervisor must discover itself:
1. multi-issue tickets get one retrieval query, so facts are missing (T3, T8)
2. the Responder cannot see live order status (T2, T8)
3. keyword routing mislabels two categories (T6, T8)

**Roles the supervisor may invent**: Issue Splitter, Order Investigator, Knowledge Integrator, Challenger, Fresh-Eyes. Free-form, not a fixed list.

## 4. Goals
1. Working supervisor loop that improves the team across >= 3 versions.
2. Matched-budget comparison against the fixed v1 team (paper's key ablation).
3. All 21 listed components implemented with Agno features, readable code, `uv` portable setup.
4. Runs with **no API key** (offline simulator) and with real models (Claude / OpenAI, fallback chain).

## 5. Non-goals
- GPU kernels or code-writing agents (the paper's domain). Only the *mechanism* is reproduced.
- Real customer data, real refunds, production auth beyond a bearer key.
- Statistical claims. Offline runs are deterministic simulation and prove wiring, not LLM quality.

## 6. Requirements
| # | Requirement | Acceptance |
|---|---|---|
| R1 | Supervisor is an Agno Workflow: run -> monitor -> reflect -> diagnose -> redesign -> approve -> launch, in a Loop | each cycle writes a new `teams/vN/` |
| R2 | Supervisor invents roles and picks stages (solo / pipeline / parallel) via a Pydantic `TeamDesign` | v3 contains a role not in v1 |
| R3 | `runs/<name>/` holds `LEARNINGS.md`, `EVOLUTION.md`, `teams/vN/{design,scorecard}.json` | new team reads them first |
| R4 | Score per version, plateau detection | `plateaued()` triggers a local-optimum diagnosis |
| R5 | Human approves, rejects or edits a proposed redesign | `--approve ask|auto|reject` |
| R6 | Guardrails (PII, injection, size, tool-call limit) via pre-hooks; logging + score capture via post-hooks | T7 blocked |
| R7 | Evolving vs fixed team, same token budget, printed table | `python -m eat.demo` |
| R8 | AgentOS app with streaming, background runs, scheduler, bearer auth | `python -m eat.os_app` |

## 7. Success metrics
- Evolving team score rises monotonically-ish v1 -> v4 and reaches >= 0.95.
- At equal token budget, evolving best score > fixed team best score.
- Zero un-blocked injection tickets; PII masked.
- Fresh clone to demo in 3 commands (`uv sync`, `uv run python -m eat.demo`).

## 8. Risks
| Risk | Mitigation |
|---|---|
| Offline simulator looks like real intelligence | README and demo output label it a rule-based simulator; real keys switch to real LLMs |
| Agno API drift (v3) | pin range in `pyproject.toml`, wiring tested against installed 3.1.x |
| Supervisor loop thrash | one failure class fixed per version, human gate, max iterations |

## 9. Milestones
1. PRD + paper study (done) 2. core harness (fs, schemas, team runner, scoring) 3. supervisor workflow
4. evals, tracing, learning, HITL 5. AgentOS + scheduler 6. demo + README + diagram
