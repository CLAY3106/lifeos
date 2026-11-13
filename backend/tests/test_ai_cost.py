import pytest

from app.services.ai_cost import BRIEFING_MODEL, estimate_cost_usd


def test_haiku_4_5_pricing():
    # $1 / MTok input, $5 / MTok output
    assert estimate_cost_usd(BRIEFING_MODEL, 1_000_000, 0) == 1.0
    assert estimate_cost_usd(BRIEFING_MODEL, 0, 1_000_000) == 5.0


def test_typical_briefing_cost():
    # ~600 context tokens + prompt in, up to 300 out
    assert estimate_cost_usd(BRIEFING_MODEL, 900, 300) == pytest.approx(0.0024)


def test_unpriced_model_fails_loudly():
    with pytest.raises(KeyError):
        estimate_cost_usd("some-new-model", 100, 100)


def test_refresh_is_rate_limited(client, demo_user, auth_headers, monkeypatch):
    """/ai/refresh skips the cache, so each call is a paid Claude call. It must be capped."""
    from datetime import datetime, timezone
    from types import SimpleNamespace

    from app.routers import ai

    paid_calls = []

    def fake_generate(db, user, insight_type, prompt):
        paid_calls.append(1)
        return SimpleNamespace(content='{"priorities": [], "summary": "ok"}',
                               generated_at=datetime.now(timezone.utc))

    monkeypatch.setattr(ai, "client", object())  # pretend an API key is configured
    monkeypatch.setattr(ai, "generate_insight", fake_generate)
    ai.limiter.reset()
    try:
        codes = [client.post("/ai/refresh", **auth_headers).status_code for _ in range(11)]
    finally:
        ai.limiter.reset()

    assert codes[:10] == [200] * 10
    assert codes[10] == 429
    assert len(paid_calls) == 10
