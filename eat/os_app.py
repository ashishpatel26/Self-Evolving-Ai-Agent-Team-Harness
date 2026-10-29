"""AgentOS runtime (21): REST API, streaming, background runs, scheduler cron, bearer-key auth.

    OS_SECURITY_KEY=secret uv run python -m eat.os_app      # then open http://localhost:7777/docs
    curl -H "Authorization: Bearer secret" -F message=go -F background=true localhost:7777/workflows/evolving-supervisor/runs
"""
import os

from agno.os import AgentOS
from fastapi import FastAPI
from agno.scheduler import ScheduleManager

from eat.config import get_db, get_knowledge
from eat.observability import setup_observability
from eat.supervisor import Supervisor
from eat.ui_api import build_router

CHECK_CRON = os.getenv("EAT_CHECK_CRON", "*/30 * * * *")  # periodic supervisor check (paper: fixed-interval cron job)
PORT = int(os.getenv("PORT", "7777"))

db, kb = get_db("os"), get_knowledge()
print(setup_observability(db))
supervisor = Supervisor("prod", db, kb, approve="auto", max_iterations=4)  # a server has no stdin: cron auto-approves, the portal uses its own gate
portal = FastAPI(title="Evolving Support Team portal API")
portal.include_router(build_router(supervisor))  # /ui/* for the Next.js portal in ui/

agent_os = AgentOS(
    id="evolving-support-team", name="Evolving Support Team", db=db,
    agents=[supervisor.reflector, supervisor.diagnoser, supervisor.designer],
    workflows=[supervisor.workflow()],
    tracing=True, scheduler=True, scheduler_base_url=f"http://localhost:{PORT}", base_app=portal,
)
app = agent_os.get_app()


# Cron trigger: the AgentOS poller POSTs to the supervisor workflow, which continues from the latest team version in K.
ScheduleManager(db).create(name="supervisor-check", cron=CHECK_CRON, endpoint="/workflows/evolving-supervisor/runs",
                           payload={"message": "periodic supervisor check", "background": "true"}, if_exists="update")


if __name__ == "__main__":
    if not os.getenv("OS_SECURITY_KEY"):
        print("WARNING: OS_SECURITY_KEY not set, the API is unauthenticated.")
    agent_os.serve(app="eat.os_app:app", port=PORT)
