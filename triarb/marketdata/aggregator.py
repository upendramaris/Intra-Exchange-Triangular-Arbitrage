from __future__ import annotations

import asyncio
import logging
from typing import Sequence

from triarb.marketdata.orderbook import OrderBookStore
from triarb.marketdata.ws_client import BinanceWsClient

log = logging.getLogger(__name__)


class MarketDataAggregator:
    def __init__(self, symbols: Sequence[str]):
        self.store = OrderBookStore()
        self.ws_client = BinanceWsClient(symbols, self.store)
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self.ws_client.start())
            log.info("marketdata.start", extra={"symbols": len(self.ws_client.symbols)})

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    def best_bid_ask(self, symbol: str):
        return self.store.best_bid_ask(symbol)

    def cumulative_depth(self, symbol: str, side: str, levels: int):
        return self.store.cumulative_depth(symbol, side, levels)
