"""Live event bus for the portal (eat/ui_api.py streams it as SSE). In-process, no broker.

publish() is safe from any thread; every subscriber gets every event. A short backlog lets a refreshed page catch up.
"""
import asyncio
import inspect
import time

_subs: set[tuple[asyncio.Queue, asyncio.AbstractEventLoop]] = set()
BACKLOG: list[dict] = []  # ponytail: in-memory, lost on restart; the DB + traces keep the durable record


def publish(kind: str, **data) -> None:
    ev = {"kind": kind, "ts": time.time(), **data}
    BACKLOG.append(ev)
    del BACKLOG[:-400]
    for q, loop in list(_subs):
        loop.call_soon_threadsafe(q.put_nowait, ev)


def subscribe() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _subs.add((q, asyncio.get_running_loop()))
    return q


def unsubscribe(q: asyncio.Queue) -> None:
    _subs.difference_update({s for s in _subs if s[0] is q})


def tool_hook(role: str, run: str):
    """Agno tool hook: one tool_start/tool_end pair per call, tagged with the role and run that made it."""
    async def hook(function_name: str, func, args: dict):
        publish("tool_start", run=run, role=role, tool=function_name, args={k: str(v)[:200] for k, v in args.items()})
        try:
            result = func(**args)
            if inspect.isawaitable(result):
                result = await result
        except Exception as e:
            publish("tool_end", run=run, role=role, tool=function_name, ok=False, result=str(e)[:300])
            raise
        publish("tool_end", run=run, role=role, tool=function_name, ok=True, result=str(result)[:600])
        return result
    return hook
