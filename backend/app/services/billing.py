"""Billing: apply a rate card to metered usage → a priced invoice.

The computation (usage → line items → total) is deterministic and tested here; it builds on the
usage metering service. Charging via a provider (Stripe) sits on top and is roadmap. Prices are
illustrative — see docs/11-sales.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.usage import UsageSummary


@dataclass(frozen=True)
class RateCard:
    currency: str = "USD"
    per_agent_run: float = 0.10  # $ per AI agent run
    per_1k_tokens: float = 0.01  # $ per 1,000 agent tokens
    per_analysis: float = 0.05  # $ per analysis run


@dataclass
class InvoiceLine:
    description: str
    quantity: float
    unit_price: float
    amount: float


@dataclass
class Invoice:
    currency: str
    lines: list[InvoiceLine] = field(default_factory=list)
    total: float = 0.0


def _money(value: float) -> float:
    return round(value + 1e-9, 2)


def compute_invoice(usage: UsageSummary, rate_card: RateCard | None = None) -> Invoice:
    """Price a usage period against a rate card (metered lines only; seats billed by tier)."""
    rates = rate_card or RateCard()
    lines: list[InvoiceLine] = []

    def add(description: str, quantity: float, unit_price: float) -> None:
        lines.append(
            InvoiceLine(
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                amount=_money(quantity * unit_price),
            )
        )

    add("AI agent runs", usage.agent_runs, rates.per_agent_run)
    add("Agent tokens (per 1k)", usage.agent_cost_tokens / 1000, rates.per_1k_tokens)
    add("Analyses", usage.analyses, rates.per_analysis)

    total = _money(sum(line.amount for line in lines))
    return Invoice(currency=rates.currency, lines=lines, total=total)
