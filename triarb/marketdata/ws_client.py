from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, Sequence

import websockets

from triarb.config import get_settings
from triarb.marketdata.orderbook import OrderBookStore

log = logging.getLogger(__name__)


class BinanceWsClient:
    def __init__(self, symbols: Sequence[str], store: OrderBookStore):
        self.symbols = symbols
        self.store = store
        self.settings = get_settings()
        streams = "/".join([f"{symbol.lower().replace('/', '')}@depth5@100ms" for symbol in symbols])
        base = self.settings.binance_ws_base_url.rstrip("/")
        self.uri = f"{base}/stream?streams={streams}"
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        while True:
            try:
                async with websockets.connect(self.uri, ping_interval=20, ping_timeout=20) as ws:
                    async for message in ws:
                        data = json.loads(message)
                        payload = data.get("data", {})
                        symbol = payload.get("s")
                        if not symbol:
                            continue
                        bids = [(float(p), float(q)) for p, q in payload.get("b", [])]
                        asks = [(float(p), float(q)) for p, q in payload.get("a", [])]
                        self.store.upsert(symbol_map(symbol), bids, asks)
            except Exception as exc:  # noqa: BLE001
                log.warning("WebSocket reconnect due to %s", exc)
                await asyncio.sleep(1)


def symbol_map(raw: str) -> str:
    raw = raw.upper()
    quotes = ["USDT", "BTC", "ETH", "BNB"]
    for quote in quotes:
        if raw.endswith(quote):
            base = raw[: -len(quote)]
            return f"{base}/{quote}"
    return raw
