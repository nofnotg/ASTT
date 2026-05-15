from datetime import date, datetime, timedelta

import pandas as pd

from replay_lab.clock.replay_clock import ReplayClock
from replay_lab.data.replay_data_provider import ReplayDataProvider
from replay_lab.replay import investment_v2
from replay_lab.replay.investment_v2 import EntryGateDecision, entry_gate
from replay_lab.feedback.investment_v2_report import InvestmentV2ReportBuilder


def _features() -> dict[str, float]:
    return {
        "weekly_trend_score": 70.0,
        "daily_trend_score": 72.0,
        "h4_trend_score": 68.0,
        "morning_liquidity_score": 71.0,
        "preopen_volume_score": 73.0,
        "btc_context_score": 55.0,
    }


def _frame(day: date, market: str) -> pd.DataFrame:
    start = datetime.combine(day, datetime.min.time()).replace(hour=7, minute=0)
    rows = []
    price = 1000.0
    for idx in range(190):
        ts = start + timedelta(minutes=idx)
        close = price * 1.0008
        rows.append(
            {
                "market": market,
                "timeframe": "1m",
                "candle_time_kst": ts.isoformat(),
                "open": price,
                "high": close * 1.003,
                "low": price * 0.997,
                "close": close,
                "volume": 1000 + idx,
                "trade_price": close * (1000 + idx),
            }
        )
        price = close
    return pd.DataFrame(rows)


def test_entry_gate_rejects_iris_veto():
    result = entry_gate(95, {"Rezo": 90, "Maggie": 90}, {"Iris": "VETO"}, "GOOD", _features())
    assert result.decision == "REJECT"
    assert "Iris" in result.reason


def test_entry_gate_holds_when_rezo_or_maggie_are_low():
    result = entry_gate(95, {"Rezo": 79, "Maggie": 90}, {"Iris": "PASS"}, "GOOD", _features())
    assert result.decision == "HOLD"
    assert "Rezo" in result.reason

    result = entry_gate(95, {"Rezo": 90, "Maggie": 79}, {"Iris": "PASS"}, "GOOD", _features())
    assert result.decision == "HOLD"
    assert "Maggie" in result.reason


def test_stage_filter_reduces_to_valid_candidates():
    assert investment_v2._stage_pass(_features())
    weak = {**_features(), "h4_trend_score": 20.0}
    assert not investment_v2._stage_pass(weak)


def test_run_day_v2_limits_to_one_entry(monkeypatch):
    day = date(2026, 1, 2)
    clock = ReplayClock(datetime.combine(day, datetime.min.time()).replace(hour=8, minute=59))
    provider = ReplayDataProvider(
        clock,
        {
            ("KRW-BTC", "1m"): _frame(day, "KRW-BTC"),
            ("KRW-ETH", "1m"): _frame(day, "KRW-ETH"),
        },
    )
    monkeypatch.setattr(investment_v2, "build_v2_features", lambda *args, **kwargs: _features())
    monkeypatch.setattr(investment_v2, "entry_gate", lambda *args, **kwargs: EntryGateDecision("ENTER", 88.0, "test pass"))
    monkeypatch.setattr(
        investment_v2,
        "_simulate_trade",
        lambda provider, clock, day, market, session_id, final_score, gate, features: {
            "session_id": session_id,
            "date_kst": day.isoformat(),
            "market": market,
            "pnl_pct": 1.0,
            "exit_reason": "take_profit",
        },
    )

    result = investment_v2.run_day_v2(day, ["KRW-BTC", "KRW-ETH"], provider, clock, 2, 1, 500000, "exp_test")

    assert len(result["paper_trades"]) == 1
    assert result["decisions"]["entered_by_v2"].sum() == 1
    assert "daily entry limit" in result["decisions"].iloc[1]["entry_gate_reason"]


def test_v2_report_includes_no_entry_days(tmp_path):
    exp = tmp_path / "experiments" / "exp_20260101_000000_v2"
    exp.mkdir(parents=True)
    (exp / "config.json").write_text('{"mode":"PAPER_REPLAY_V2"}', encoding="utf-8")
    pd.DataFrame(
        [
            {
                "session_id": "s1",
                "date_kst": "2026-01-01",
                "market": "KRW-BTC",
                "entry_gate_decision": "HOLD",
                "entry_gate_confidence": 55.0,
                "entry_gate_reason": "confidence 55.0 < 70.0",
                "no_entry_reason": "confidence 55.0 < 70.0",
                "entered_by_v2": False,
                "final_score": 81.0,
                "weekly_trend_score": 70.0,
                "daily_trend_score": 70.0,
                "h4_trend_score": 70.0,
                "morning_liquidity_score": 70.0,
                "preopen_volume_score": 70.0,
            }
        ]
    ).to_parquet(exp / "decisions.parquet", index=False)
    pd.DataFrame(columns=["session_id", "date_kst", "market", "pnl_pct"]).to_parquet(exp / "paper_trades.parquet", index=False)
    pd.DataFrame(
        [{"session_id": "s1", "date_kst": "2026-01-01", "market": "KRW-BTC", "persona": "Rezo", "score": 80.0, "decision": "PASS"}]
    ).to_parquet(exp / "persona_scores.parquet", index=False)
    pd.DataFrame(
        [{"date_kst": "2026-01-01", "market": "KRW-BTC", "universe_stage": "candidate_pool", "passed": True, "universe_score": 70.0}]
    ).to_parquet(exp / "universe_stages.parquet", index=False)

    out = InvestmentV2ReportBuilder(tmp_path, capital_krw=500000).build("2026-01-01", "2026-01-01")
    html = out.read_text(encoding="utf-8")

    assert "ASTT 2차 투자 검증 리포트" in html
    assert "confidence 55.0" in html
    assert (tmp_path / "reports" / "investment_v2" / "investment_v2_report.json").exists()
