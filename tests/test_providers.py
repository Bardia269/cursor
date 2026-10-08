from types import SimpleNamespace as NS

import httpx2
import pytest
from openai import BadRequestError

from seo_os.config import TaskSpec
from seo_os.llm import AnthropicProvider, OpenAIProvider, Refusal, TruncatedOutput
from seo_os.schemas import Metadata

META = Metadata(title_tag="t", meta_description="d", slug="s")


def _openai_response(**extra):
    usage = NS(input_tokens=1200, output_tokens=300, input_tokens_details=NS(cached_tokens=200))
    return NS(usage=usage, status="completed", output_text="texte", output_parsed=META, output=[], **extra)


@pytest.fixture
def openai_provider(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    return OpenAIProvider(timeout=10, max_retries=0)


def test_openai_structured_call_shape_and_usage(openai_provider):
    seen = {}

    def parse(**kwargs):
        seen.update(kwargs)
        return _openai_response()

    openai_provider.client = NS(responses=NS(parse=parse))
    spec = TaskSpec(task="metadata", provider="openai", model="gpt-6-luna", max_output_tokens=500, effort="low")
    result = openai_provider.generate(spec, "sys", "user", Metadata)
    assert seen["text_format"] is Metadata and seen["reasoning"] == {"effort": "low"}
    assert seen["instructions"] == "sys" and seen["input"] == "user" and seen["max_output_tokens"] == 500
    assert result.parsed == META
    assert (result.usage.input_tokens, result.usage.cached_input_tokens, result.usage.output_tokens) == (1000, 200, 300)


def test_openai_retries_without_reasoning_when_rejected(openai_provider):
    calls = []
    request = httpx2.Request("POST", "https://api.openai.com/v1/responses")

    def create(**kwargs):
        calls.append(kwargs)
        if "reasoning" in kwargs:
            raise BadRequestError(
                "Unsupported parameter: 'reasoning.effort'",
                response=httpx2.Response(400, request=request),
                body=None,
            )
        return _openai_response()

    openai_provider.client = NS(responses=NS(create=create))
    spec = TaskSpec(task="write", provider="openai", model="m", max_output_tokens=100, effort="medium")
    openai_provider.generate(spec, "s", "u", None)
    openai_provider.generate(spec, "s", "u", None)
    assert ["reasoning" in c for c in calls] == [True, False, False]


def test_openai_incomplete_response_is_truncation(openai_provider):
    resp = _openai_response()
    resp.status = "incomplete"
    resp.incomplete_details = NS(reason="max_output_tokens")
    openai_provider.client = NS(responses=NS(create=lambda **k: resp))
    spec = TaskSpec(task="write", provider="openai", model="m", max_output_tokens=100)
    with pytest.raises(TruncatedOutput) as err:
        openai_provider.generate(spec, "s", "u", None)
    assert err.value.usage.output_tokens == 300


def test_openai_web_search_collects_citations_and_counts_calls(openai_provider):
    output = [
        NS(type="web_search_call", action=NS(sources=[NS(url="https://www.sbfi.admin.ch/a")])),
        NS(type="message", content=[NS(annotations=[NS(type="url_citation", url="https://b.ch", title="B")])]),
    ]
    seen = {}

    def create(**kwargs):
        seen.update(kwargs)
        return NS(**{**_openai_response().__dict__, "output": output})

    openai_provider.client = NS(responses=NS(create=create))
    spec = TaskSpec(task="search", provider="openai", model="gpt-6-luna", max_output_tokens=100)
    result = openai_provider.web_search(spec, "s", "u", ["admin.ch"], "CH")
    assert seen["tools"][0]["filters"] == {"allowed_domains": ["admin.ch"]}
    assert seen["tools"][0]["user_location"]["country"] == "CH"
    assert result.usage.web_search_calls == 1
    assert [u for u, _ in result.citations] == ["https://www.sbfi.admin.ch/a", "https://b.ch"]


class _Stream:
    def __init__(self, message):
        self.message = message

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get_final_message(self):
        return self.message


def _anthropic_message(text, stop_reason="end_turn"):
    usage = NS(input_tokens=900, output_tokens=400, cache_read_input_tokens=5000, cache_creation_input_tokens=0)
    return NS(usage=usage, stop_reason=stop_reason, content=[NS(type="thinking"), NS(type="text", text=text)])


def _anthropic(message, seen):
    provider = AnthropicProvider(timeout=10, max_retries=0)

    def stream(**kwargs):
        seen.update(kwargs)
        return _Stream(message)

    provider.client = NS(messages=NS(stream=stream))
    return provider


def test_anthropic_structured_call_caches_system_and_sets_effort():
    seen = {}
    provider = _anthropic(_anthropic_message(META.model_dump_json()), seen)
    spec = TaskSpec(task="brief", provider="anthropic", model="claude-sonnet-5-5", max_output_tokens=800, effort="medium")
    result = provider.generate(spec, "bible", "brief", Metadata)
    assert seen["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert seen["output_config"]["effort"] == "medium"
    assert seen["output_config"]["format"]["type"] == "json_schema"
    assert "thinking" not in seen
    assert result.parsed == META and result.usage.cached_input_tokens == 5000


def test_anthropic_refusal_and_truncation_raise():
    spec = TaskSpec(task="write", provider="anthropic", model="claude-sonnet-5-5", max_output_tokens=800)
    with pytest.raises(Refusal):
        _anthropic(_anthropic_message("", "refusal"), {}).generate(spec, "s", "u", None)
    with pytest.raises(TruncatedOutput):
        _anthropic(_anthropic_message("…", "max_tokens"), {}).generate(spec, "s", "u", None)
