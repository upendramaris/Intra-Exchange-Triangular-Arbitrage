from __future__ import annotations

from triarb.config import get_settings


def taker_fee(exchange: str) -> float:
    settings = get_settings()
    return settings.fee_table.get(exchange, {}).get("taker", 0.001)
