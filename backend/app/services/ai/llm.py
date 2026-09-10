"""LLM abstraction.

A thin provider interface so the rest of the engine is model-agnostic. The
default ``StubLLM`` is deterministic and offline. A real provider (Anthropic /
Bedrock / etc.) implements the same ``complete`` signature and reports its
``name`` + ``version`` so they land in the audit record.

Grounding contract: callers pass ONLY retrieved evidence + computed derived
metrics as context. The LLM is asked to explain/synthesize, never to invent
facts or do arithmetic on raw data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.core.config import settings


@dataclass
class LLMResult:
    text: str
    model_name: str
    model_version: str


class LLM(Protocol):
    def complete(self, *, system: str, prompt: str, language: str = "en") -> LLMResult: ...


class StubLLM:
    """Deterministic stand-in. Produces grounded-looking text from the context.

    It does NOT fabricate figures: numbers must already be present in the
    context (evidence/derived) the caller assembles.
    """

    name = "stub-llm"
    version = "v0"

    def complete(self, *, system: str, prompt: str, language: str = "en") -> LLMResult:
        lead = "ملخص تم إنشاؤه آليًا:" if language == "ar" else "Auto-generated summary:"
        # Echo the grounded prompt body so the caller can see what was cited.
        body = prompt.strip()
        text = f"{lead}\n{body}"
        return LLMResult(text=text, model_name=self.name, model_version=self.version)


def get_llm() -> LLM:
    # STUB: dispatch on settings.llm_provider to a real client in production.
    if settings.llm_provider == "stub":
        return StubLLM()
    # e.g. return AnthropicLLM(api_key=settings.llm_api_key, model=settings.llm_model)
    return StubLLM()
