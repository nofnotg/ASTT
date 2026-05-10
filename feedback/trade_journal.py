from __future__ import annotations

from data.storage import Storage


def latest_trade_count(storage: Storage) -> int:
    with storage.session() as session:
        from sqlalchemy import func, select
        from data.schemas import PaperTrade

        return session.scalar(select(func.count()).select_from(PaperTrade)) or 0

