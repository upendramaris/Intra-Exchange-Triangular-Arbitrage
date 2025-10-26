from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

from triarb.config import get_settings
from triarb.engine.risk import RiskManager
from triarb.engine.signals import Opportunity
from triarb.exchange.base import ExchangeAdapter
from triarb.marketdata.orderbook import OrderBookStore

log = logging.getLogger(__name__)


class Executor:
    def __init__(self, adapter: ExchangeAdapter, store: OrderBookStore, risk: RiskManager):
        self.adapter = adapter
        self.store = store
        self.risk = risk
        self.settings = get_settings()

    async def execute(self, opportunity: Opportunity) -> None:
        notional = opportunity.notional_quote
        if not self.risk.allow_cycle(notional):
            log.info("risk.reject", extra={"reason": "limits"})
            return

        try:
            instructions = self._build_instructions(opportunity)
        except ValueError as exc:
            log.warning("executor.build_failed", extra={"error": str(exc)})
            self.risk.release_cycle()
            return

        async def submit(order: Dict[str, Any]):
            log.info("order.submit", extra=order)
            return await self.adapter.create_bulk_orders([order])

        tasks = [submit(order) for order in instructions]

        try:
            await asyncio.gather(*tasks)
            log.info("cycle.executed", extra={"net_bps": opportunity.net_bps})
        except Exception as exc:  # noqa: BLE001
            log.error("executor.failed", extra={"error": str(exc)})
            self.risk.register_failure()
        else:
            self.risk.release_cycle()

    def _build_instructions(self, opportunity: Opportunity) -> List[Dict[str, Any]]:
        holdings = opportunity.notional_quote
        asset = self.settings.quote
        instructions: List[Dict[str, Any]] = []
        fee_rate = self.adapter.fee_rate("")
        slippage = self.settings.slippage_bps / 10_000

        for leg in opportunity.triangle.legs:
            bid, ask = self.store.best_bid_ask(leg.symbol)
            if not (bid and ask):
                raise ValueError(f"Missing book for {leg.symbol}")
            base, quote = leg.symbol.split("/")
            if asset == quote and leg.from_asset == quote:
                price = ask.price * (1 + slippage)
                qty = holdings / price
                instructions.append({"symbol": leg.symbol, "side": "buy", "type": "market", "amount": qty})
                holdings = qty * (1 - fee_rate)
                asset = base
            elif asset == base and leg.from_asset == base:
                price = bid.price * (1 - slippage)
                qty = holdings
                instructions.append({"symbol": leg.symbol, "side": "sell", "type": "market", "amount": qty})
                holdings = qty * price * (1 - fee_rate)
                asset = quote
            else:
                raise ValueError(f"Asset mismatch for {leg.symbol}")

        if asset != self.settings.quote:
            raise ValueError("Cycle does not return to quote asset.")

        return instructions
