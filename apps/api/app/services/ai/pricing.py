"""OpenAI model pricing (USD per 1M tokens). Update when OpenAI changes rates."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

_ONE_M = Decimal("1000000")


@dataclass(frozen=True)
class ModelPricing:
    input_price_per_1m: Decimal
    output_price_per_1m: Decimal
    cached_input_price_per_1m: Decimal | None = None
    reasoning_price_per_1m: Decimal | None = None


@dataclass(frozen=True)
class CostEstimate:
    input_cost: Decimal
    output_cost: Decimal
    cached_cost: Decimal
    total_cost: Decimal
    pricing_configured: bool = True


OPENAI_MODEL_PRICING: dict[str, ModelPricing] = {
    "gpt-5.4-nano": ModelPricing(
        input_price_per_1m=Decimal("0.05"),
        output_price_per_1m=Decimal("0.20"),
        cached_input_price_per_1m=Decimal("0.025"),
    ),
    "gpt-5.4-mini": ModelPricing(
        input_price_per_1m=Decimal("0.15"),
        output_price_per_1m=Decimal("0.60"),
        cached_input_price_per_1m=Decimal("0.075"),
    ),
    "gpt-5.4": ModelPricing(
        input_price_per_1m=Decimal("1.00"),
        output_price_per_1m=Decimal("4.00"),
        cached_input_price_per_1m=Decimal("0.50"),
    ),
    "gpt-5.5": ModelPricing(
        input_price_per_1m=Decimal("2.50"),
        output_price_per_1m=Decimal("10.00"),
        cached_input_price_per_1m=Decimal("1.25"),
    ),
    "gpt-4o-mini": ModelPricing(
        input_price_per_1m=Decimal("0.15"),
        output_price_per_1m=Decimal("0.60"),
        cached_input_price_per_1m=Decimal("0.075"),
    ),
    "gpt-4o": ModelPricing(
        input_price_per_1m=Decimal("2.50"),
        output_price_per_1m=Decimal("10.00"),
        cached_input_price_per_1m=Decimal("1.25"),
    ),
    "gpt-4o-2024-08-06": ModelPricing(
        input_price_per_1m=Decimal("2.50"),
        output_price_per_1m=Decimal("10.00"),
        cached_input_price_per_1m=Decimal("1.25"),
    ),
    "o1-mini": ModelPricing(
        input_price_per_1m=Decimal("3.00"),
        output_price_per_1m=Decimal("12.00"),
        reasoning_price_per_1m=Decimal("12.00"),
    ),
}


def estimate_usage_cost(
    model: str,
    *,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cached_input_tokens: int = 0,
    reasoning_tokens: int = 0,
) -> CostEstimate | None:
    pricing = OPENAI_MODEL_PRICING.get(model)
    if pricing is None:
        logger.warning("model pricing not configured for %s", model)
        return None

    billable_input = max(0, input_tokens - cached_input_tokens)
    input_cost = Decimal(billable_input) * pricing.input_price_per_1m / _ONE_M
    output_cost = Decimal(output_tokens) * pricing.output_price_per_1m / _ONE_M
    cached_cost = Decimal(0)
    if cached_input_tokens > 0 and pricing.cached_input_price_per_1m is not None:
        cached_cost = Decimal(cached_input_tokens) * pricing.cached_input_price_per_1m / _ONE_M
    if reasoning_tokens > 0 and pricing.reasoning_price_per_1m is not None:
        output_cost += Decimal(reasoning_tokens) * pricing.reasoning_price_per_1m / _ONE_M

    total = input_cost + output_cost + cached_cost
    return CostEstimate(
        input_cost=input_cost,
        output_cost=output_cost,
        cached_cost=cached_cost,
        total_cost=total,
    )
