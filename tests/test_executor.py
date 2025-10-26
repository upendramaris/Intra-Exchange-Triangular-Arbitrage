import asyncio

import pytest

from triarb.engine.executor import Executor
from triarb.engine.risk import RiskManager
from triarb.engine.signals import Opportunity
from triarb.engine.triangle import Triangle, TriangleLeg
from triarb.marketdata.orderbook import OrderBookStore


class DummyAdapter:
    def __init__(self):
        self.submitted = 0

    def fee_rate(self, symbol: str) -> float:
        return 0.0

    async def create_bulk_orders(self, orders):
        self.submitted += len(orders)
        return [{"id": "x"} for _ in orders]


@pytest.mark.asyncio
async def test_executor_skips_without_books():
    store = OrderBookStore()
    adapter = DummyAdapter()
    risk = RiskManager()
    executor = Executor(adapter, store, risk)
    triangle = Triangle(
        (
            TriangleLeg("BTC/USDT", "USDT", "BTC"),
            TriangleLeg("ETH/BTC", "BTC", "ETH"),
            TriangleLeg("ETH/USDT", "ETH", "USDT"),
        )
    )
    opp = Opportunity(triangle=triangle, gross_bps=50, net_bps=20, notional_quote=1000)
    await executor.execute(opp)
    assert adapter.submitted == 0
