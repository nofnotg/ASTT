from app.config import get_settings
from data.storage import Storage
from execution.order_intent import OrderIntent, create_entry_intent
from simulation.paper_broker import PaperBroker


def test_paper_buy_and_sell(tmp_path):
    db = tmp_path / "test.sqlite"
    settings = get_settings(TRADING_MODE="PAPER", DATABASE_URL=f"sqlite:///{db.as_posix()}")
    storage = Storage(settings)
    broker = PaperBroker(storage, settings)
    buy = create_entry_intent(1, "KRW-BTC", 10000, "PAPER")
    buy_result = broker.submit(buy, best_ask=1000)
    assert buy_result["volume"] > 0
    position = storage.latest_open_position("KRW-BTC")
    assert position is not None
    assert position.avg_price > 1000
    sell = OrderIntent(signal_id=1, market="KRW-BTC", side="ask", ord_type="market", volume=position.volume, reason="take profit", mode="PAPER")
    sell_result = broker.submit(sell, best_bid=1020)
    assert sell_result["realized_pnl_krw"] > 0

