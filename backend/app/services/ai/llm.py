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
from app.core.logging import get_logger

log = get_logger(__name__)

# Default real model when the Anthropic provider is selected but no model is
# pinned (the config default is the stub sentinel).
_DEFAULT_ANTHROPIC_MODEL = "claude-opus-5"


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


class AnthropicLLM:
    """Anthropic-backed generation. Preserves the grounding contract: the
    caller's system prompt forbids inventing facts or doing arithmetic on raw
    data; this class only relays the grounded system+prompt and returns text.

    Constructed lazily by ``get_llm`` only when the provider is ``anthropic``
    AND an API key is configured — so the scaffold and CI stay fully offline on
    the stub. The ``anthropic`` SDK is an optional dependency (extra ``llm``).
    """

    name = "anthropic"

    def __init__(self, *, api_key: str, model: str) -> None:
        import anthropic  # lazy: optional dependency, imported only when used

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(self, *, system: str, prompt: str, language: str = "en") -> LLMResult:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1500,  # narrative sections are short
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        if response.stop_reason == "refusal":
            text = "[content unavailable: the model declined to generate this narrative]"
        else:
            # Concatenate only text blocks (skip thinking / other block types).
            text = "".join(b.text for b in response.content if b.type == "text").strip()
        # Record the served model string for the audit record.
        return LLMResult(text=text, model_name=self.name, model_version=response.model)


def _anthropic_model() -> str:
    pinned = settings.llm_model
    return pinned if pinned and pinned != "stub-llm-v0" else _DEFAULT_ANTHROPIC_MODEL


def get_llm() -> LLM:
    """Return the configured LLM client.

    Defaults to the deterministic offline ``StubLLM``. Returns ``AnthropicLLM``
    only when the provider is ``anthropic`` and an API key is configured; any
    failure (missing SDK, bad config) falls back to the stub so a request never
    crashes on LLM setup.
    """
    if settings.llm_provider == "anthropic" and settings.llm_api_key:
        try:
            return AnthropicLLM(api_key=settings.llm_api_key, model=_anthropic_model())
        except Exception as exc:  # noqa: BLE001 - never let LLM setup break a request
            log.warning(
                "anthropic LLM unavailable; falling back to stub",
                extra={"extra_fields": {"error": str(exc)}},
            )
            return StubLLM()
    return StubLLM()
