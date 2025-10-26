from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class Level:
    price: float
    qty: float


@dataclass
class OrderBook:
    symbol: str
    bids: List[Level] = field(default_factory=list)
    asks: List[Level] = field(default_factory=list)

    def update(self, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]]) -> None:
        self.bids = [Level(price, qty) for price, qty in sorted(bids, key=lambda x: -x[0])]
        self.asks = [Level(price, qty) for price, qty in sorted(asks, key=lambda x: x[0])]

    def best_bid_ask(self) -> Tuple[Level | None, Level | None]:
        bid = self.bids[0] if self.bids else None
        ask = self.asks[0] if self.asks else None
        return bid, ask

    def cumulative_depth(self, side: str, levels: int) -> float:
        book = self.bids if side == "bid" else self.asks
        qty = 0.0
        for level in book[:levels]:
            qty += level.qty
        return qty


class OrderBookStore:
    def __init__(self):
        self.books: Dict[str, OrderBook] = {}

    def upsert(self, symbol: str, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]]) -> None:
        book = self.books.setdefault(symbol, OrderBook(symbol))
        book.update(bids, asks)

    def best_bid_ask(self, symbol: str) -> Tuple[Level | None, Level | None]:
        return self.books.get(symbol, OrderBook(symbol)).best_bid_ask()

    def cumulative_depth(self, symbol: str, side: str, levels: int) -> float:
        return self.books.get(symbol, OrderBook(symbol)).cumulative_depth(side, levels)
