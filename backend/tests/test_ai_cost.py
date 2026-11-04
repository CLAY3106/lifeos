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
