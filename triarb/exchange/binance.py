from __future__ import annotations

import asyncio
from typing import Any, Dict, Sequence

import ccxt.async_support as ccxt

from triarb.config import get_settings
from triarb.exchange.base import ExchangeAdapter


class BinanceAdapter(ExchangeAdapter):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        settings = get_settings()
        self.paper = settings.paper_mode
        self._fee_table = settings.fee_table.get("binance", {"taker": 0.0004})
        self._client = ccxt.binance({
            "apiKey": settings.binance_api_key,
            "secret": settings.binance_api_secret,
            "enableRateLimit": True,
        })
        self._markets_ready = asyncio.create_task(self._client.load_markets())

    async def fetch_balances(self) -> Dict[str, float]:
        await self._markets_ready
        if self.paper:
            return {"USDT": 1_000_000}
        balances = await self._client.fetch_balance()
        return {asset: float(entry["free"]) for asset, entry in balances["total"].items()}

    async def create_bulk_orders(self, orders: Sequence[Dict[str, Any]]) -> Sequence[Any]:
        await self._markets_ready
        if self.paper:
            return [{"id": f"paper-{idx}", **order} for idx, order in enumerate(orders)]

        tasks = [
            self._client.create_order(order["symbol"], order["type"], order["side"], order["amount"])
            for order in orders
        ]
        return await asyncio.gather(*tasks)

    def fee_rate(self, symbol: str) -> float:
        return float(self._fee_table.get("taker", 0.0004))
