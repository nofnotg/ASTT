from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session, sessionmaker

from app.config import ROOT_DIR, Settings, get_settings
from data.schemas import (
    Base,
    Candle,
    DailyReport,
    OrderIntentRow,
    OrderTestResult,
    PaperPosition,
    PaperTrade,
    PersonaScore,
    Signal,
    Tick,
)


def _sqlite_path(database_url: str) -> str:
    if database_url.startswith("sqlite:///"):
        raw = database_url.replace("sqlite:///", "", 1)
        path = Path(raw)
        if not path.is_absolute():
            path = ROOT_DIR / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path.as_posix()}"
    return database_url


def make_engine(settings: Settings | None = None):
    settings = settings or get_settings()
    return create_engine(_sqlite_path(settings.database_url), future=True)


def init_db(settings: Settings | None = None) -> None:
    engine = make_engine(settings)
    Base.metadata.create_all(engine)


class Storage:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.engine = make_engine(self.settings)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(self.engine, expire_on_commit=False, future=True)

    def session(self) -> Session:
        return self.SessionLocal()

    def upsert_candles(self, candles: Iterable[dict], timeframe: str) -> int:
        rows = []
        for item in candles:
            rows.append(
                {
                    "market": item["market"],
                    "timeframe": timeframe,
                    "candle_time_kst": item.get("candle_date_time_kst") or item.get("candle_time_kst"),
                    "open": float(item.get("opening_price", item.get("open", 0))),
                    "high": float(item.get("high_price", item.get("high", 0))),
                    "low": float(item.get("low_price", item.get("low", 0))),
                    "close": float(item.get("trade_price", item.get("close", 0))),
                    "volume": float(item.get("candle_acc_trade_volume", item.get("volume", 0))),
                    "trade_price": float(item.get("candle_acc_trade_price", item.get("trade_price", 0))),
                }
            )
        if not rows:
            return 0
        with self.session() as session:
            stmt = insert(Candle).values(rows)
            stmt = stmt.on_conflict_do_nothing(index_elements=["market", "timeframe", "candle_time_kst"])
            result = session.execute(stmt)
            session.commit()
            return result.rowcount or 0

    def save_tick(self, event: dict, store_raw: bool = False) -> None:
        market = event.get("code") or event.get("market") or ""
        row = Tick(
            market=market,
            tick_type=event.get("type", "unknown"),
            event_time_kst=str(event.get("trade_time") or event.get("timestamp") or datetime.utcnow().isoformat()),
            trade_price=event.get("trade_price") or event.get("trade_price_24h"),
            trade_volume=event.get("trade_volume"),
            ask_bid=event.get("ask_bid"),
            orderbook_json=json.dumps(event.get("orderbook_units"), ensure_ascii=False) if event.get("orderbook_units") else None,
            raw_json=json.dumps(event, ensure_ascii=False) if store_raw else None,
        )
        with self.session() as session:
            session.add(row)
            session.commit()

    def purge_old_ticks(self, retention_hours: int) -> None:
        cutoff = datetime.utcnow() - timedelta(hours=retention_hours)
        with self.session() as session:
            session.execute(delete(Tick).where(Tick.created_at < cutoff))
            session.commit()

    def save_persona_scores(self, results: list, signal_id: int | None = None) -> None:
        with self.session() as session:
            for result in results:
                session.add(
                    PersonaScore(
                        signal_id=signal_id,
                        market=result.market,
                        persona_name=result.persona_name,
                        score=float(result.score),
                        decision=result.decision,
                        reasons_json=json.dumps(result.reasons, ensure_ascii=False),
                        warnings_json=json.dumps(result.warnings, ensure_ascii=False),
                        veto=bool(result.veto),
                        payload_json=json.dumps(result.payload, ensure_ascii=False),
                    )
                )
            session.commit()

    def save_signal(self, decision) -> int:
        row = Signal(
            market=decision.market,
            final_score=float(decision.final_score),
            final_decision=decision.decision,
            vetoed=bool(decision.vetoed),
            veto_reason=decision.veto_reason,
            top_reasons_json=json.dumps(decision.reasons, ensure_ascii=False),
            config_version="v0.1",
        )
        with self.session() as session:
            session.add(row)
            session.commit()
            return row.id

    def save_order_intent(self, intent, status: str = "CREATED") -> int:
        row = OrderIntentRow(
            signal_id=intent.signal_id,
            market=intent.market,
            side=intent.side,
            ord_type=intent.ord_type,
            price=intent.price,
            volume=intent.volume,
            krw_amount=intent.krw_amount,
            identifier=intent.identifier,
            status=status,
        )
        with self.session() as session:
            session.add(row)
            session.commit()
            return row.id

    def save_order_test_result(self, order_intent_id: int | None, market: str, request: dict, response: dict | None, error: dict | None, status: str) -> int:
        with self.session() as session:
            row = OrderTestResult(
                order_intent_id=order_intent_id,
                market=market,
                request_json=json.dumps(request, ensure_ascii=False),
                response_json=json.dumps(response, ensure_ascii=False) if response else None,
                error_json=json.dumps(error, ensure_ascii=False) if error else None,
                status=status,
            )
            session.add(row)
            session.commit()
            return row.id

    def latest_open_position(self, market: str) -> PaperPosition | None:
        with self.session() as session:
            return session.execute(select(PaperPosition).where(PaperPosition.market == market, PaperPosition.status == "OPEN").order_by(PaperPosition.id.desc())).scalar_one_or_none()

    def add_position(self, market: str, avg_price: float, volume: float, invested_krw: float) -> int:
        with self.session() as session:
            row = PaperPosition(market=market, avg_price=avg_price, volume=volume, invested_krw=invested_krw)
            session.add(row)
            session.commit()
            return row.id

    def update_position(self, position: PaperPosition) -> None:
        with self.session() as session:
            session.merge(position)
            session.commit()

    def add_paper_trade(self, **kwargs) -> int:
        with self.session() as session:
            row = PaperTrade(**kwargs)
            session.add(row)
            session.commit()
            return row.id

    def count_open_positions(self) -> int:
        with self.session() as session:
            return session.scalar(select(func.count()).select_from(PaperPosition).where(PaperPosition.status == "OPEN")) or 0

