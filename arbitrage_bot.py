"""Basic configuration and scaffolding for a triangular arbitrage trading bot."""

import asyncio
import json
from contextlib import suppress
from typing import Any, Dict, List, Optional, Sequence

import websockets
import ccxt.async_support as ccxt  # type: ignore

# --- Configuration ---------------------------------------------------------
CONFIG = {
    "exchange_id": "binance",  # Target exchange identifier recognized by ccxt
    "api_key": "API_KEY",  # Placeholder; replace with your actual API key
    "api_secret": "API_SECRET",  # Placeholder; replace with your actual API secret
    "base_asset": "USDT",  # Asset to start and end each triangular loop with
    "initial_amount": 1_000.0,  # Amount of base asset used per arbitrage attempt
    "min_profit_percent": 0.05,  # Minimum net profit percentage required to trade
    "trading_fee_percent": 0.1,  # Exchange trading fee percentage per trade leg
}


async def initialize_exchange():
    """Create and return an authenticated ccxt exchange instance."""
    exchange_class = getattr(ccxt, CONFIG["exchange_id"])
    return exchange_class({
        "apiKey": CONFIG["api_key"],
        "secret": CONFIG["api_secret"],
        "options": {"defaultType": "spot"},
        "enableRateLimit": True,
    })


async def get_all_triangular_pairs(
    exchange: Optional[ccxt.Exchange] = None,
) -> List[List[Dict[str, str]]]:
    """
    Discover all triangular arbitrage loops that start and end with CONFIG['base_asset'].

    Each loop is represented as a list of legs, and each leg contains the trading pair
    along with the direction of conversion, e.g.:

        [
            {"symbol": "BTC/USDT", "from": "USDT", "to": "BTC"},
            {"symbol": "ETH/BTC", "from": "BTC", "to": "ETH"},
            {"symbol": "ETH/USDT", "from": "ETH", "to": "USDT"},
        ]
    """
    owns_exchange = exchange is None
    if exchange is None:
        exchange = await initialize_exchange()

    loops: List[List[Dict[str, str]]] = []
    seen_signatures: set[str] = set()
    base_asset = CONFIG["base_asset"]

    try:
        markets = await exchange.load_markets()

        adjacency: Dict[str, List[Dict[str, str]]] = {}
        for market in markets.values():
            base = market.get("base")
            quote = market.get("quote")
            symbol = market.get("symbol")
            if not base or not quote or not symbol:
                continue

            adjacency.setdefault(base, []).append({
                "symbol": symbol,
                "from": base,
                "to": quote,
            })
            adjacency.setdefault(quote, []).append({
                "symbol": symbol,
                "from": quote,
                "to": base,
            })

        for leg1 in adjacency.get(base_asset, []):
            asset1 = leg1["to"]
            if asset1 == base_asset:
                continue

            for leg2 in adjacency.get(asset1, []):
                asset2 = leg2["to"]
                if asset2 in (base_asset, asset1):
                    continue

                for leg3 in adjacency.get(asset2, []):
                    if leg3["to"] != base_asset:
                        continue
                    if leg3["symbol"] in (leg1["symbol"], leg2["symbol"]):
                        continue

                    signature = "|".join([
                        f"{leg1['symbol']}:{leg1['from']}->{leg1['to']}",
                        f"{leg2['symbol']}:{leg2['from']}->{leg2['to']}",
                        f"{leg3['symbol']}:{leg3['from']}->{leg3['to']}",
                    ])
                    if signature in seen_signatures:
                        continue

                    seen_signatures.add(signature)
                    loops.append([
                        dict(leg1),
                        dict(leg2),
                        dict(leg3),
                    ])
    finally:
        if owns_exchange:
            await exchange.close()

    return loops


async def data_collector(
    pairs: Sequence[str],
    order_book_cache: Dict[str, Dict[str, float]],
) -> None:
    """
    Subscribe to real-time order-book ticker data and keep the cache updated.

    Parameters
    ----------
    pairs:
        Iterable of trading pair symbols (e.g., ['BTC/USDT', 'ETH/BTC']) to monitor.
    order_book_cache:
        Shared dictionary that will be updated in-place with the latest bid/ask data:
        {
            'BTC/USDT': {
                'bid_price': 26800.1,
                'bid_qty': 0.52,
                'ask_price': 26800.2,
                'ask_qty': 0.48,
                'update_id': 123456789,
            }
        }
    """
    if not pairs:
        return

    exchange_id = CONFIG["exchange_id"]
    if exchange_id != "binance":
        raise NotImplementedError(
            "data_collector currently implements the Binance bookTicker stream only.",
        )

    stream_symbols = []
    symbol_map: Dict[str, str] = {}
    for pair in pairs:
        normalized = pair.replace("/", "").lower()
        stream_symbols.append(f"{normalized}@bookTicker")
        symbol_map[normalized.upper()] = pair

    streams = "/".join(stream_symbols)
    uri = f"wss://stream.binance.com:9443/stream?streams={streams}"

    while True:
        try:
            async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as ws:
                async for raw_message in ws:
                    envelope = json.loads(raw_message)
                    payload = envelope.get("data", envelope)
                    symbol = payload.get("s")
                    if not symbol:
                        continue

                    pair = symbol_map.get(symbol)
                    if pair is None:
                        continue

                    order_book_cache[pair] = {
                        "bid_price": float(payload["b"]),
                        "bid_qty": float(payload["B"]),
                        "ask_price": float(payload["a"]),
                        "ask_qty": float(payload["A"]),
                        "update_id": int(payload.get("u", 0)),
                    }
        except asyncio.CancelledError:
            raise
        except (websockets.ConnectionClosedError, websockets.InvalidStatusCode) as exc:
            print(f"WebSocket connection issue ({exc}); retrying shortly...")
            await asyncio.sleep(1)
        except Exception as exc:  # noqa: BLE001
            print(f"Unexpected data_collector error: {exc}")
            await asyncio.sleep(1)


async def execute_trades(
    instructions: Sequence[Dict[str, Any]],
    exchange: Optional[ccxt.Exchange] = None,
) -> List[Any]:
    """
    Submit three market orders concurrently according to the provided instructions.

    Each instruction must contain: 'symbol', 'side' (buy/sell), and 'amount'.
    """
    if len(instructions) != 3:
        raise ValueError("execute_trades expects exactly three trade instructions.")

    owns_exchange = exchange is None
    if exchange is None:
        exchange = await initialize_exchange()

    async def place_order(instruction: Dict[str, Any]) -> Any:
        symbol = instruction["symbol"]
        side = instruction["side"].lower()
        amount = float(instruction["amount"])
        if side not in {"buy", "sell"}:
            raise ValueError(f"Unsupported order side '{instruction['side']}' for {symbol}.")
        if amount <= 0:
            raise ValueError(f"Amount must be positive for {symbol}.")

        print(f"Submitting {side.upper()} market order on {symbol} for {amount} units.")
        return await exchange.create_order(symbol, "market", side, amount)

    try:
        if not getattr(exchange, "markets", None):
            await exchange.load_markets()

        tasks = [place_order(instr) for instr in instructions]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                raise result

        return results
    finally:
        if owns_exchange:
            await exchange.close()


def calculate_profitability(
    loop: Sequence[Dict[str, str]],
    initial_amount: float,
    market_data: Dict[str, Dict[str, float]],
) -> float:
    """
    Evaluate whether a three-leg loop yields a net profit given current order-book data.

    Returns the percentage gain (positive) or loss (negative) versus the starting amount.
    """
    if len(loop) != 3:
        raise ValueError("Triangular loops must contain exactly three legs.")
    if initial_amount <= 0:
        raise ValueError("initial_amount must be greater than zero.")

    fee_rate = CONFIG["trading_fee_percent"] / 100
    amount = initial_amount

    for idx, leg in enumerate(loop, start=1):
        symbol = leg["symbol"]
        tick = market_data.get(symbol)
        if tick is None:
            raise ValueError(f"Missing market data for symbol '{symbol}'.")

        try:
            base_asset, quote_asset = symbol.split("/")
        except ValueError as exc:
            raise ValueError(f"Unexpected symbol format '{symbol}'.") from exc

        direction = (leg["from"], leg["to"])
        if direction == (quote_asset, base_asset):
            # Buying the base asset using the quote currency -> pay ask price.
            price = tick["ask_price"]
            if price <= 0:
                raise ValueError(f"Invalid ask price for {symbol}.")
            amount = (amount / price) * (1 - fee_rate)
        elif direction == (base_asset, quote_asset):
            # Selling the base asset for the quote currency -> receive bid price.
            price = tick["bid_price"]
            if price <= 0:
                raise ValueError(f"Invalid bid price for {symbol}.")
            amount = (amount * price) * (1 - fee_rate)
        else:
            raise ValueError(
                f"Leg direction {direction} is incompatible with symbol {symbol} "
                f"(base={base_asset}, quote={quote_asset})."
            )

    profit_percent = ((amount - initial_amount) / initial_amount) * 100
    return profit_percent


def _build_trade_instructions(
    loop: Sequence[Dict[str, str]],
    initial_amount: float,
    market_data: Dict[str, Dict[str, float]],
) -> List[Dict[str, Any]]:
    """Derive executable trade instructions that mirror the simulated loop."""
    fee_rate = CONFIG["trading_fee_percent"] / 100
    holdings_amount = initial_amount
    holdings_asset = CONFIG["base_asset"]
    instructions: List[Dict[str, Any]] = []

    for leg in loop:
        symbol = leg["symbol"]
        tick = market_data.get(symbol)
        if tick is None:
            raise ValueError(f"Missing market data for symbol '{symbol}'.")

        base_asset, quote_asset = symbol.split("/")
        direction = (leg["from"], leg["to"])
        if leg["from"] != holdings_asset:
            raise ValueError(
                f"Loop leg asset mismatch: expected {holdings_asset}, "
                f"but leg starts from {leg['from']}."
            )

        if direction == (quote_asset, base_asset):
            price = tick["ask_price"]
            if price <= 0:
                raise ValueError(f"Invalid ask price for {symbol}.")
            base_qty = holdings_amount / price
            instructions.append({
                "symbol": symbol,
                "side": "buy",
                "amount": base_qty,
            })
            holdings_amount = base_qty * (1 - fee_rate)
            holdings_asset = base_asset
        elif direction == (base_asset, quote_asset):
            price = tick["bid_price"]
            if price <= 0:
                raise ValueError(f"Invalid bid price for {symbol}.")
            base_qty = holdings_amount
            instructions.append({
                "symbol": symbol,
                "side": "sell",
                "amount": base_qty,
            })
            holdings_amount = base_qty * price * (1 - fee_rate)
            holdings_asset = quote_asset
        else:
            raise ValueError(
                f"Leg direction {direction} does not align with {symbol} "
                f"(base={base_asset}, quote={quote_asset})."
            )

    return instructions


async def main() -> None:
    """Main orchestration loop for discovering and acting on arbitrage routes."""
    exchange = await initialize_exchange()
    market_cache: Dict[str, Dict[str, float]] = {}

    try:
        loops = await get_all_triangular_pairs(exchange)
        if not loops:
            print("No triangular loops found; exiting.")
            return

        unique_pairs = sorted({leg["symbol"] for loop in loops for leg in loop})
        collector_task = asyncio.create_task(data_collector(unique_pairs, market_cache))
        print(
            f"Monitoring {len(unique_pairs)} pairs across {len(loops)} loops "
            f"for base asset {CONFIG['base_asset']}."
        )

        try:
            while True:
                if not market_cache:
                    await asyncio.sleep(0.1)
                    continue

                for loop in loops:
                    try:
                        profit = calculate_profitability(
                            loop,
                            CONFIG["initial_amount"],
                            market_cache,
                        )
                    except ValueError:
                        continue

                    if profit >= CONFIG["min_profit_percent"]:
                        symbol_sequence = " -> ".join(leg["symbol"] for leg in loop)
                        print(
                            f"Profitable opportunity detected ({profit:.4f}%): {symbol_sequence}"
                        )
                        try:
                            instructions = _build_trade_instructions(
                                loop,
                                CONFIG["initial_amount"],
                                market_cache,
                            )
                            await execute_trades(instructions, exchange)
                        except ValueError as exc:
                            print(f"Skipping execution due to data inconsistency: {exc}")
                await asyncio.sleep(0.25)
        finally:
            collector_task.cancel()
            with suppress(asyncio.CancelledError):
                await collector_task
    finally:
        await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())
