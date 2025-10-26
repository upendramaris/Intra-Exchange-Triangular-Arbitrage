from __future__ import annotations

import asyncio
import json
import logging
from typing import Sequence

import websockets
from websockets.exceptions import InvalidStatusCode

from triarb.config import get_settings
from triarb.marketdata.orderbook import OrderBookStore

log = logging.getLogger(__name__)


class BinanceWsClient:
    def __init__(self, symbols: Sequence[str], store: OrderBookStore):
        self.symbols = symbols
        self.store = store
        self.settings = get_settings()
        streams = "/".join([f"{symbol.lower().replace('/', '')}@depth5@100ms" for symbol in symbols])
        self._uris = [f"{base}/stream?streams={streams}" for base in self.settings.binance_ws_urls]
        self._uri_index = 0
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        backoff = 1
        while True:
            try:
                uri = self._current_uri
                async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as ws:
                    backoff = 1
                    async for message in ws:
                        data = json.loads(message)
                        payload = data.get("data", {})
                        symbol = payload.get("s")
                        if not symbol:
                            continue
                        bids = [(float(p), float(q)) for p, q in payload.get("b", [])]
                        asks = [(float(p), float(q)) for p, q in payload.get("a", [])]
                        self.store.upsert(symbol_map(symbol), bids, asks)
            except InvalidStatusCode as exc:
                log.warning("WebSocket reconnect due to HTTP %s (%s)", exc.status_code, self._current_uri)
                if exc.status_code == 451 and self._advance_uri():
                    log.info("Switching Binance WS endpoint to %s", self._current_uri)
            except Exception as exc:  # noqa: BLE001
                log.warning("WebSocket reconnect due to %s (%s)", exc, self._current_uri)

            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)

    @property
    def _current_uri(self) -> str:
        return self._uris[self._uri_index]

    def _advance_uri(self) -> bool:
        if len(self._uris) <= 1:
            return False
        self._uri_index = (self._uri_index + 1) % len(self._uris)
        return True


def symbol_map(raw: str) -> str:
    raw = raw.upper()
    quotes = ["USDT", "BTC", "ETH", "BNB"]
    for quote in quotes:
        if raw.endswith(quote):
            base = raw[: -len(quote)]
            return f"{base}/{quote}"
    return raw
