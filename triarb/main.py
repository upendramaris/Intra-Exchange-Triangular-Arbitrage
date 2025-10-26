from __future__ import annotations

import asyncio
import logging

from triarb.config import get_settings
from triarb.engine.executor import Executor
from triarb.engine.risk import RiskManager
from triarb.engine.signals import SignalEngine
from triarb.engine.triangle import build_triangles
from triarb.exchange.binance import BinanceAdapter
from triarb.logging import configure_logging
from triarb.marketdata.aggregator import MarketDataAggregator

log = logging.getLogger(__name__)


async def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    triangles = build_triangles(settings.quote, settings.base_symbols)
    unique_symbols = sorted({symbol for triangle in triangles for symbol in triangle.symbols})

    market = MarketDataAggregator(unique_symbols)
    await market.start()

    adapter = BinanceAdapter(config={})
    risk = RiskManager()
    signal_engine = SignalEngine(triangles, market.store)
    executor = Executor(adapter, market.store, risk)

    log.info("engine.start", extra={"triangles": len(triangles)})

    try:
        while True:
            opportunities = signal_engine.evaluate()
            for opp in opportunities:
                await executor.execute(opp)
            await asyncio.sleep(0.25)
    finally:
        await market.stop()


if __name__ == "__main__":
    asyncio.run(run())
