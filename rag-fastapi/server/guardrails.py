# guardrails.py
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError, constr


# -------------------------
# 1) Schema: strict output
# -------------------------
class FinalAnswer(BaseModel):
    """
    Strict, validated output schema for the agent response (Pydantic v1).
    """
    answer: constr(strip_whitespace=True, min_length=1, max_length=2000)
    sources: List[str] = Field(default_factory=list)
    cost_tokens: int = Field(ge=0)

    class Config:
        extra = "forbid"  # fail closed if extra keys appear


# -------------------------
# 2) Content policy checks
# -------------------------
# Basic patterns. For stronger protections, integrate a DLP tool.
_PATTERNS = {
    # OpenAI key-like strings
    "api_key_like": re.compile(r"\b(sk-[A-Za-z0-9]{20,})\b"),

    # AWS Access Key ID heuristic
    "aws_access_key_id": re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),

    # Email addresses
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),

    # US SSN heuristic (adapt for your region)
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),

    # Credit card heuristic (not a full Luhn check)
    "credit_card": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
}

_REDACTIONS = {
    "api_key_like": "[REDACTED_API_KEY]",
    "aws_access_key_id": "[REDACTED_AWS_KEY]",
    "email": "[REDACTED_EMAIL]",
    "ssn": "[REDACTED_SSN]",
    "credit_card": "[REDACTED_CARD]",
}


@dataclass
class PolicyResult:
    ok: bool
    violations: List[str]
    redacted_text: Optional[str] = None


def policy_scan(text: str, redact: bool = True) -> PolicyResult:
    """
    Scan output text for likely secrets/PII patterns.
    Returns which rules triggered; optionally returns a redacted version.
    """
    violations: List[str] = []
    redacted = text

    for name, pattern in _PATTERNS.items():
        if pattern.search(text):
            violations.append(name)
            if redact:
                redacted = pattern.sub(_REDACTIONS[name], redacted)

    return PolicyResult(
        ok=(len(violations) == 0),
        violations=violations,
        redacted_text=(redacted if redact else None),
    )


# -----------------------------------------
# 3) Separation: schema vs policy validation
# -----------------------------------------
class SchemaValidationError(ValueError):
    """Raised when payload doesn't conform to the FinalAnswer schema."""


class ContentPolicyError(ValueError):
    """Raised when secrets/PII patterns are detected in the answer."""

    def __init__(self, message: str, violations: List[str], redacted: Optional[str] = None):
        super().__init__(message)
        self.violations = violations
        self.redacted = redacted


def validate_answer(payload: Dict[str, Any], *, redact_on_fail: bool = True) -> FinalAnswer:
    """
    1) Validate JSON payload against schema (fail closed).
    2) Run content policy scan on the 'answer' field.
    3) Raise explicit errors so telemetry can record what failed.
    """
    try:
        obj = FinalAnswer(**payload)  # Pydantic v1 validation
    except ValidationError as e:
        raise SchemaValidationError(f"Schema validation failed: {e}") from e

    policy = policy_scan(obj.answer, redact=redact_on_fail)
    if not policy.ok:
        raise ContentPolicyError(
            message="Content policy violation detected in answer.",
            violations=policy.violations,
            redacted=policy.redacted_text,
        )

    return obj