"""Gateway behavior tests use scripted providers and never contact a real model."""

import json

import httpx
import pytest

from cropcover.llm.gateway import (
    CircuitBreaker,
    FakeLLM,
    LLMError,
    LLMGateway,
    LLMResult,
    LLMUnavailable,
    OpenAICompatProvider,
    Reply,
    cost_inr,
)

ASK = [{"role": "user", "content": "How do I claim?"}]


async def test_retries_transient_failure_then_succeeds():
    transient = LLMError("HTTP 503: busy", retryable=True)
    primary = FakeLLM("gemini", script=[transient, "Recovered"])
    gateway = LLMGateway([primary], sleep=lambda _: _nothing())
    result = await gateway.generate(ASK)
    assert result.text == "Recovered" and result.attempts == 2


async def _nothing():
    return None


async def test_falls_back_after_primary_auth_failure():
    primary = FakeLLM("gemini", script=[LLMError("401 invalid key", retryable=False)])
    backup = FakeLLM("groq", script=["Backup answer"])
    result = await LLMGateway([primary, backup]).generate(ASK)
    assert result.provider == "groq" and result.fallback_used


async def test_wrong_key_is_not_retried_and_fallback_is_recorded():
    primary = FakeLLM("gemini", script=[LLMError("401", retryable=False)])
    backup = FakeLLM("groq", script=["Backup answer"])
    rows = []

    async def record(row):
        rows.append(row)

    result = await LLMGateway([primary, backup], recorder=record).generate(ASK)
    assert primary.calls == 1 and result.provider == "groq"
    assert [row["status"] for row in rows] == ["error", "ok"]


async def test_all_providers_down_raises_unavailable():
    gateway = LLMGateway(
        [
            FakeLLM("gemini", script=[LLMError("401", retryable=False)]),
            FakeLLM("groq", script=[LLMError("401", retryable=False)]),
        ]
    )
    with pytest.raises(LLMUnavailable, match="gemini.*groq"):
        await gateway.generate(ASK)


async def test_empty_provider_list_reports_not_configured():
    with pytest.raises(LLMUnavailable, match="no LLM provider"):
        await LLMGateway([]).generate(ASK)


async def test_transient_failure_waits_for_retry_after():
    failure = LLMError("429", retryable=True, retry_after=3)
    waits = []

    async def sleep(seconds):
        waits.append(seconds)

    provider = FakeLLM("gemini", script=[failure, "second attempt"])
    result = await LLMGateway([provider], sleep=sleep).generate(ASK)
    assert result.attempts == 2 and waits[0] >= 3


async def test_circuit_breaker_skips_provider_until_cooldown_then_recovers():
    now = [0.0]
    failure = LLMError("401", retryable=False)
    primary = FakeLLM("gemini", script=[failure] * 3 + ["Recovered"])
    backup = FakeLLM("groq")
    gateway = LLMGateway(
        [primary, backup], breaker_threshold=3, breaker_cooldown=10, clock=lambda: now[0]
    )
    for _ in range(3):
        await gateway.generate(ASK)
    assert gateway.breakers["gemini"].state == "open"
    await gateway.generate(ASK)
    assert primary.calls == 3
    now[0] = 11
    result = await gateway.generate(ASK)
    assert result.provider == "gemini" and gateway.breakers["gemini"].state == "closed"


def test_breaker_moves_closed_open_half_open_and_back():
    now = [0.0]
    breaker = CircuitBreaker(2, 10, clock=lambda: now[0])
    breaker.failure()
    assert breaker.state == "closed"
    breaker.failure()
    assert breaker.state == "open" and not breaker.allow()
    now[0] = 11
    assert breaker.state == "half-open" and breaker.allow()
    breaker.failure()
    assert breaker.state == "open"
    now[0] = 22
    breaker.success()
    assert breaker.state == "closed" and breaker.failures == 0


async def test_stream_yields_answer_and_result_metadata():
    rows = []

    async def record(row):
        rows.append(row)

    stream = LLMGateway(
        [FakeLLM("gemini", script=["Declare it in the path string."])], recorder=record
    ).stream(ASK, prompt_version="chat_system_v1")
    items = [item async for item in stream]
    assert "".join(items[:-1]).strip() == "Declare it in the path string."
    assert isinstance(items[-1], LLMResult) and items[-1].tokens_out == 6
    assert rows[0]["prompt_version"] == "chat_system_v1"


async def test_stream_falls_back_before_sending_any_piece():
    primary = FakeLLM(
        "gemini", script=[LLMError("503", retryable=True), LLMError("503", retryable=True)]
    )
    backup = FakeLLM("groq", script=["From backup"])
    items = [item async for item in LLMGateway([primary, backup]).stream(ASK)]
    assert "".join(items[:-1]).strip() == "From backup"
    assert items[-1].fallback_used


async def test_stream_retries_transient_failure_before_first_piece():
    async def no_wait(seconds):
        return None

    provider = FakeLLM("gemini", script=[LLMError("503", retryable=True), "Recovered stream"])
    items = [item async for item in LLMGateway([provider], sleep=no_wait).stream(ASK)]
    assert "".join(items[:-1]).strip() == "Recovered stream"
    assert items[-1].attempts == 2 and provider.calls == 2


async def test_stream_failure_after_partial_answer_does_not_switch_provider():
    primary = FakeLLM("gemini", script=[("partial", LLMError("503", retryable=True))])
    backup = FakeLLM("groq")
    seen = []
    with pytest.raises(LLMUnavailable, match="mid-answer"):
        async for item in LLMGateway([primary, backup]).stream(ASK):
            seen.append(item)
    assert "".join(seen).strip() == "Half an answer" and backup.calls == 0


async def test_recorder_failure_does_not_break_answer():
    async def broken(row):
        raise RuntimeError("database down")

    result = await LLMGateway([FakeLLM(script=["Still answered"])], recorder=broken).generate(ASK)
    assert result.text == "Still answered"


async def test_missing_token_usage_is_estimated():
    class NoUsage(FakeLLM):
        async def generate(self, messages, *, temperature=0.2):
            return Reply("x" * 40)

    result = await LLMGateway([NoUsage()]).generate([{"role": "user", "content": "y" * 400}])
    assert (result.tokens_in, result.tokens_out) == (100, 10)


def provider_with(handler):
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return OpenAICompatProvider("gemini", "https://llm.test/v1/", "k", "m", client=client)


async def test_http_provider_sends_openai_request_and_reads_reply():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Hello"}}],
                "usage": {"prompt_tokens": 9, "completion_tokens": 2},
            },
        )

    reply = await provider_with(handler).generate(ASK)
    assert reply == Reply("Hello", 9, 2)
    assert seen["url"].endswith("/v1/chat/completions") and seen["auth"] == "Bearer k"
    assert seen["body"]["model"] == "m" and seen["body"]["messages"] == ASK


async def test_http_provider_classifies_retry_after_and_auth_errors():
    def busy(request):
        return httpx.Response(429, headers={"retry-after": "7"}, json={"error": "busy"})

    with pytest.raises(LLMError) as error:
        await provider_with(busy).generate(ASK)
    assert error.value.retryable and error.value.retry_after == 7

    def unauthorized(request):
        return httpx.Response(401, json={"error": "bad key"})

    with pytest.raises(LLMError) as error:
        await provider_with(unauthorized).generate(ASK)
    assert not error.value.retryable


async def test_http_provider_parses_sse_and_usage():
    chunk = "data: " + json.dumps({"choices": [{"delta": {"content": "Hello "}}]}) + "\n\n"
    end = "data: " + json.dumps(
        {"choices": [], "usage": {"prompt_tokens": 8, "completion_tokens": 1}}
    )
    body = chunk + end + "\n\ndata: [DONE]\n\n"

    def handler(request):
        assert json.loads(request.content)["stream"]
        return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})

    usage = Reply()
    pieces = [piece async for piece in provider_with(handler).stream(ASK, usage)]
    assert pieces == ["Hello "] and (usage.tokens_in, usage.tokens_out) == (8, 1)


async def test_http_provider_rejects_stream_cut_off_before_end_marker():
    body = 'data: {"choices": [{"delta": {"content": "partial"}}]}\n\n'

    def handler(request):
        return httpx.Response(200, text=body)

    pieces = []
    with pytest.raises(LLMError, match="ended early"):
        async for piece in provider_with(handler).stream(ASK, Reply()):
            pieces.append(piece)
    assert pieces == ["partial"]


async def test_timeout_is_not_retried_but_connection_failure_is():
    def timeout(request):
        raise httpx.ReadTimeout("slow")

    def disconnected(request):
        raise httpx.ConnectError("refused")

    with pytest.raises(LLMError) as slow:
        await provider_with(timeout).generate(ASK)
    with pytest.raises(LLMError) as lost:
        await provider_with(disconnected).generate(ASK)
    assert not slow.value.retryable and "ReadTimeout" in str(slow.value)
    assert lost.value.retryable


def test_cost_is_converted_to_rupees_at_list_price():
    assert cost_inr("openai/gpt-oss-20b", 1000, 1000, 95) == 0.035625
    assert cost_inr("gemini-3.8-flash", 1_000_000, 1_000_000, 95) == 427.5
    assert cost_inr("unknown", 1000, 1000, 95) == 0
