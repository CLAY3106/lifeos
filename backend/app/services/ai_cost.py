"""
AI cost estimation.

One place for model prices, so the number logged to ai_usage_log matches what
Anthropic actually bills. Prices are USD per million tokens, from
https://platform.claude.com/docs/en/about-claude/pricing (checked Nov 2026).
Update this table when you change models or prices change.
"""

BRIEFING_MODEL = "claude-haiku-4-5-20251001"

# model -> (input $/MTok, output $/MTok)
PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5-20251001": (1.00, 5.00),
}


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimated USD cost of one call. Raises KeyError for an unpriced model,
    so a model switch can't silently log $0."""
    input_price, output_price = PRICES_PER_MTOK[model]
    return round((input_tokens * input_price + output_tokens * output_price) / 1_000_000, 6)
