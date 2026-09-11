"""LLM provider dispatch — offline-safe defaults."""

import importlib.util

import pytest

from app.core.config import settings
from app.services.ai.llm import StubLLM, get_llm

_HAS_ANTHROPIC = importlib.util.find_spec("anthropic") is not None


def test_get_llm_defaults_to_stub():
    llm = get_llm()
    assert isinstance(llm, StubLLM)
    assert llm.name == "stub-llm"


def test_stub_does_not_fabricate_numbers():
    # The stub only echoes the grounded prompt; nothing beyond it appears.
    out = get_llm().complete(system="s", prompt="[der:x] 0.42", language="en")
    assert "0.42" in out.text
    assert out.model_name == "stub-llm"


def test_anthropic_provider_without_key_falls_back_to_stub(monkeypatch):
    # Provider selected but no API key configured → stay on the offline stub.
    monkeypatch.setattr(settings, "llm_provider", "anthropic")
    monkeypatch.setattr(settings, "llm_api_key", None)
    assert isinstance(get_llm(), StubLLM)


@pytest.mark.skipif(_HAS_ANTHROPIC, reason="anthropic SDK installed; fallback path not exercised")
def test_anthropic_provider_missing_sdk_falls_back_to_stub(monkeypatch):
    # Provider + key set, but the optional `anthropic` SDK isn't installed here
    # → construction raises ImportError and get_llm falls back to the stub.
    monkeypatch.setattr(settings, "llm_provider", "anthropic")
    monkeypatch.setattr(settings, "llm_api_key", "sk-ant-test")
    assert isinstance(get_llm(), StubLLM)
