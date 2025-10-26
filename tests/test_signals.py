from triarb.engine.signals import SignalEngine
from triarb.engine.triangle import Triangle, TriangleLeg
from triarb.marketdata.orderbook import OrderBookStore


def make_triangle():
    return Triangle(
        (
            TriangleLeg("BTC/USDT", "USDT", "BTC"),
            TriangleLeg("ETH/BTC", "BTC", "ETH"),
            TriangleLeg("ETH/USDT", "ETH", "USDT"),
        )
    )


def test_signal_no_data():
    store = OrderBookStore()
    engine = SignalEngine([make_triangle()], store)
    assert engine.evaluate() == []
