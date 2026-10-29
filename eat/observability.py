"""Observability (20): one OpenInference instrumentation, two destinations.

1. Agno's own trace store (setup_tracing -> database, shown in AgentOS "Traces").
2. Langfuse over OTLP, when LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY are set.
Every agent, team, workflow step, model call and tool call becomes a span.
"""
import base64
import os

from agno.tracing import setup_tracing
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_observability(db) -> str:
    setup_tracing(db=db)  # creates the TracerProvider + OpenInference AgnoInstrumentor
    public, secret = os.getenv("LANGFUSE_PUBLIC_KEY"), os.getenv("LANGFUSE_SECRET_KEY")
    if not (public and secret):
        return "traces: Agno DB only (set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY for Langfuse)"
    host = (os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL") or "https://cloud.langfuse.com").rstrip("/")
    auth = base64.b64encode(f"{public}:{secret}".encode()).decode()
    exporter = OTLPSpanExporter(endpoint=f"{host}/api/public/otel/v1/traces", headers={"Authorization": f"Basic {auth}"})
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(exporter))  # same spans, second sink
    return f"traces: Agno DB + Langfuse ({host})"
