from triarb.engine.signals import Opportunity
from triarb.engine.triangle import Triangle, TriangleLeg


def test_triangle_symbols():
    legs = (
        TriangleLeg("BTC/USDT", "USDT", "BTC"),
        TriangleLeg("ETH/BTC", "BTC", "ETH"),
        TriangleLeg("ETH/USDT", "ETH", "USDT"),
    )
    tri = Triangle(legs)
    assert tri.symbols == ["BTC/USDT", "ETH/BTC", "ETH/USDT"]
