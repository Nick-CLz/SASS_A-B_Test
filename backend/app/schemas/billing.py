"""Billing invoice response schema (GET /v1/billing/invoice)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class InvoiceLineRead(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float


class InvoiceRead(BaseModel):
    currency: str
    period_start: datetime
    period_end: datetime
    total: float
    lines: list[InvoiceLineRead] = Field(default_factory=list)
