"""Autonomous AI Co-Worker agent module (root level export)."""

from coworker.agent import (
    CoworkerAgent,
    Coworker,
    EvaluatorOutput,
    WORKER_PROMPT,
    TolerateToolErrors,
)
from coworker.config import SANDBOX_DIR as SANDBOX, MAX_EVALUATION_ATTEMPTS as MAX_ATTEMPTS

__all__ = [
    "CoworkerAgent",
    "Coworker",
    "EvaluatorOutput",
    "WORKER_PROMPT",
    "TolerateToolErrors",
    "SANDBOX",
    "MAX_ATTEMPTS",
]

