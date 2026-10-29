"""Guardrails (15) and hooks (16): pre-run validation, post-run token metering for the budget comparison."""
from contextlib import contextmanager

from agno.exceptions import InputCheckError
from agno.guardrails import PIIDetectionGuardrail, PromptInjectionGuardrail
from agno.run.agent import RunInput

MAX_INPUT_CHARS = 4000


class Meter:
    """Counts tokens: the shared budget that makes team-vs-baseline comparisons fair."""

    def __init__(self):
        self.tokens, self.paused = 0, False

    def spend(self, n: int) -> None:
        if not self.paused:
            self.tokens += n

    @contextmanager
    def exclude(self):
        """Evals are measurement, not work: keep their tokens out of the budget."""
        self.paused = True
        try:
            yield
        finally:
            self.paused = False


METER = Meter()


def validate_input(run_input) -> None:
    if len(run_input.input_content_string()) > MAX_INPUT_CHARS:
        raise InputCheckError("Input too long.")


def is_injection(text: str) -> bool:
    """Intake screen: the same Agno guardrail the agents run as a pre-hook, applied once before any model call."""
    try:
        PromptInjectionGuardrail().check(RunInput(input_content=text))
        return False
    except InputCheckError:
        return True


def capture_run(run_output) -> None:
    """Post-hook: add each run's tokens to the budget meter (full run history lives in the Agno DB and traces)."""
    METER.spend(getattr(run_output.metrics, "total_tokens", 0) or 0)


PRE_HOOKS = [validate_input, PromptInjectionGuardrail(), PIIDetectionGuardrail(mask_pii=True)]  # PII masked, injection blocked
POST_HOOKS = [capture_run]
