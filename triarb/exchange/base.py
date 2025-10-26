from __future__ import annotations

import abc
from typing import Any, Dict, Sequence


class ExchangeAdapter(abc.ABC):
    """Abstract interface for exchange-specific REST actions."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abc.abstractmethod
    async def fetch_balances(self) -> Dict[str, float]:
        raise NotImplementedError

    @abc.abstractmethod
    async def create_bulk_orders(self, orders: Sequence[Dict[str, Any]]) -> Sequence[Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def fee_rate(self, symbol: str) -> float:
        raise NotImplementedError
