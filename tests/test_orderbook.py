from triarb.marketdata.orderbook import OrderBookStore


def test_best_bid_ask():
    store = OrderBookStore()
    store.upsert("BTC/USDT", [(100, 1)], [(101, 2)])
    bid, ask = store.best_bid_ask("BTC/USDT")
    assert bid.price == 100
    assert ask.price == 101
