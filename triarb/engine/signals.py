from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from triarb.config import get_settings
from triarb.engine.fees import taker_fee
from triarb.engine.triangle import Triangle
from triarb.marketdata.orderbook import OrderBookStore
from triarb.utils.math import bps_to_ratio


@dataclass
class Opportunity:
    triangle: Triangle
    gross_bps: float
    net_bps: float
    notional_quote: float


class SignalEngine:
    def __init__(self, triangles: Sequence[Triangle], store: OrderBookStore):
        self.triangles = triangles
        self.store = store
        self.settings = get_settings()
        self.fee = taker_fee(self.settings.exchange)
        self.slip = bps_to_ratio(self.settings.slippage_bps)

    def evaluate(self) -> List[Opportunity]:
        opportunities: List[Opportunity] = []
        target = self.settings.target_notional_quote

        for triangle in self.triangles:
            amount = target
            holdings_asset = self.settings.quote
            viable = True

            for leg in triangle.legs:
                bid, ask = self.store.best_bid_ask(leg.symbol)
                if not (bid and ask):
                    viable = False
                    break

                base, quote = leg.symbol.split("/")
                fee_slip = self.fee + self.slip

                if leg.from_asset == quote and holdings_asset == quote:
                    price = ask.price
                    amount = (amount / price) * (1 - fee_slip)
                    holdings_asset = base
                elif leg.from_asset == base and holdings_asset == base:
                    price = bid.price
                    amount = (amount * price) * (1 - fee_slip)
                    holdings_asset = quote
                else:
                    viable = False
                    break

            if not viable or holdings_asset != self.settings.quote:
                continue

            gross_edge = ((amount - target) / target) * 10_000
            net_edge = gross_edge - (self.settings.slippage_bps * 3)

            if gross_edge >= self.settings.min_gross_edge_bps and net_edge >= self.settings.min_net_edge_bps:
                opportunities.append(
                    Opportunity(
                        triangle=triangle,
                        gross_bps=gross_edge,
                        net_bps=net_edge,
                        notional_quote=min(self.settings.max_leg_notional_quote, target),
                    )
                )

        return opportunities
