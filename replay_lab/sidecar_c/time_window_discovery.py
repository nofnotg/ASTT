from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from html import escape
from pathlib import Path
from typing import Iterable

import pandas as pd

from replay_lab.data.historical_loader import HistoricalLoader
from replay_lab.paths import REPLAY_STORE_DIR


@dataclass(frozen=True)
class TimeWindowDiscoveryConfig:
    start_date: date
    end_date: date
    markets: list[str]
    entry_times: list[str]
    top_markets: int | None = None
    load_missing: bool = False
    pre_minutes: int = 10
    context_minutes: int = 60
    target_minutes: int = 30
    exit_minutes: int = 60
    target_move_pct: float = 1.0
    max_adverse_pct: float = -0.8


class TimeWindowDiscovery:
    def __init__(self, store_dir: Path = REPLAY_STORE_DIR, loader: HistoricalLoader | None = None) -> None:
        self.store_dir = store_dir
        self.loader = loader or HistoricalLoader(store_dir=store_dir)

    def run(self, config: TimeWindowDiscoveryConfig) -> Path:
        markets = config.markets[: config.top_markets or len(config.markets)]
        out_dir = self.store_dir / "reports" / "sidecar_c"
        out_dir.mkdir(parents=True, exist_ok=True)
        rows = []
        day = config.start_date
        while day <= config.end_date:
            if config.load_missing:
                self.loader.load_batch_intraday_days(markets, day, day)
            for market in markets:
                frame = self._load_frame(market)
                if frame.empty:
                    continue
                day_frame = self._day_slice(frame, day)
                if day_frame.empty:
                    continue
                for entry_time in config.entry_times:
                    row = self._evaluate_window(day_frame, market, day, entry_time, config)
                    if row:
                        rows.append(row)
            day += timedelta(days=1)

        raw = pd.DataFrame(rows)
        summary = self._summarize(raw)
        payload = {
            "config": {
                "start_date": config.start_date.isoformat(),
                "end_date": config.end_date.isoformat(),
                "markets": markets,
                "entry_times": config.entry_times,
                "pre_minutes": config.pre_minutes,
                "context_minutes": config.context_minutes,
                "target_minutes": config.target_minutes,
                "exit_minutes": config.exit_minutes,
                "target_move_pct": config.target_move_pct,
                "max_adverse_pct": config.max_adverse_pct,
            },
            "summary": summary,
            "raw_count": int(len(raw)),
        }
        if not raw.empty:
            raw.to_parquet(out_dir / "time_window_raw.parquet", index=False)
        (out_dir / "time_window_discovery.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._write_html(out_dir / "time_window_discovery.html", payload)
        return out_dir

    def _load_frame(self, market: str) -> pd.DataFrame:
        path = self.store_dir / "normalized" / "candles_1m" / f"{market}.parquet"
        if not path.exists():
            return pd.DataFrame()
        frame = pd.read_parquet(path)
        frame["candle_time_kst"] = pd.to_datetime(frame["candle_time_kst"])
        return frame.sort_values("candle_time_kst")

    def _day_slice(self, frame: pd.DataFrame, day: date) -> pd.DataFrame:
        start = pd.Timestamp(datetime.combine(day, time.min))
        end = pd.Timestamp(datetime.combine(day, time.max))
        return frame[(frame["candle_time_kst"] >= start) & (frame["candle_time_kst"] <= end)].copy()

    def _evaluate_window(
        self,
        frame: pd.DataFrame,
        market: str,
        day: date,
        entry_time: str,
        config: TimeWindowDiscoveryConfig,
    ) -> dict | None:
        entry_at = pd.Timestamp(datetime.combine(day, self._parse_time(entry_time)))
        pre_start = entry_at - pd.Timedelta(minutes=config.pre_minutes)
        context_start = entry_at - pd.Timedelta(minutes=config.context_minutes)
        target_end = entry_at + pd.Timedelta(minutes=config.target_minutes)
        exit_end = entry_at + pd.Timedelta(minutes=config.exit_minutes)
        context = frame[(frame["candle_time_kst"] >= context_start) & (frame["candle_time_kst"] < pre_start)]
        pre = frame[(frame["candle_time_kst"] >= pre_start) & (frame["candle_time_kst"] < entry_at)]
        target = frame[(frame["candle_time_kst"] >= entry_at) & (frame["candle_time_kst"] <= target_end)]
        exit_window = frame[(frame["candle_time_kst"] >= entry_at) & (frame["candle_time_kst"] <= exit_end)]
        if pre.empty or target.empty or exit_window.empty:
            return None
        entry_price = float(target.iloc[0]["open"])
        if entry_price <= 0:
            return None
        context_value_avg = float(context["trade_price"].mean()) if not context.empty else float(pre["trade_price"].mean())
        pre_value = float(pre["trade_price"].sum())
        pre_value_avg = float(pre["trade_price"].mean())
        pre_rvol = pre_value_avg / context_value_avg if context_value_avg else 0.0
        pre_return = (float(pre.iloc[-1]["close"]) - float(pre.iloc[0]["open"])) / float(pre.iloc[0]["open"]) * 100
        max_up = (float(target["high"].max()) - entry_price) / entry_price * 100
        max_down = (float(target["low"].min()) - entry_price) / entry_price * 100
        exit_return = (float(exit_window.iloc[-1]["close"]) - entry_price) / entry_price * 100
        success = max_up >= config.target_move_pct and max_down >= config.max_adverse_pct
        flow_score = self._flow_score(pre_rvol, pre_return, max_up, max_down, exit_return)
        return {
            "date_kst": day.isoformat(),
            "market": market,
            "entry_time": entry_time,
            "day_type": "weekend" if day.weekday() >= 5 else "weekday",
            "weekday": day.weekday(),
            "pre_rvol": pre_rvol,
            "pre_trade_value_krw": pre_value,
            "pre_return_pct": pre_return,
            "target_max_up_pct": max_up,
            "target_max_down_pct": max_down,
            "exit_return_pct": exit_return,
            "success": bool(success),
            "flow_score": flow_score,
        }

    def _flow_score(self, pre_rvol: float, pre_return: float, max_up: float, max_down: float, exit_return: float) -> float:
        score = 0.0
        score += min(pre_rvol, 5.0) * 12
        score += max(pre_return, 0.0) * 8
        score += max(max_up, 0.0) * 10
        score += max(exit_return, 0.0) * 6
        score += max(max_down, -5.0) * 4
        return round(max(score, 0.0), 4)

    def _summarize(self, raw: pd.DataFrame) -> list[dict]:
        if raw.empty:
            return []
        rows = []
        for (entry_time, day_type), group in raw.groupby(["entry_time", "day_type"], sort=True):
            success_rate = float(group["success"].mean())
            avg_flow_score = float(group["flow_score"].mean())
            avg_max_up = float(group["target_max_up_pct"].mean())
            avg_drawdown = float(group["target_max_down_pct"].mean())
            avg_exit_return = float(group["exit_return_pct"].mean())
            active_days = int(group["date_kst"].nunique())
            weeks = max(1, int(pd.to_datetime(group["date_kst"]).dt.to_period("W").nunique()))
            score = success_rate * 45 + avg_flow_score * 0.35 + max(avg_exit_return, 0) * 8 + min(active_days / weeks, 7) * 2
            rows.append(
                {
                    "entry_time": entry_time,
                    "day_type": day_type,
                    "samples": int(len(group)),
                    "active_days": active_days,
                    "suggested_days_per_week": round(active_days / weeks, 2),
                    "success_rate": success_rate,
                    "avg_flow_score": avg_flow_score,
                    "avg_target_max_up_pct": avg_max_up,
                    "avg_target_max_down_pct": avg_drawdown,
                    "avg_exit_return_pct": avg_exit_return,
                    "pinpoint_score": round(score, 4),
                    "recommendation": self._recommendation(score, len(group), success_rate),
                }
            )
        return sorted(rows, key=lambda row: row["pinpoint_score"], reverse=True)

    def _recommendation(self, score: float, samples: int, success_rate: float) -> str:
        if samples < 30:
            return "표본 부족"
        if score >= 65 and success_rate >= 0.55:
            return "우선 검증 시간대"
        if score >= 50:
            return "후보 시간대"
        return "보류"

    def _write_html(self, path: Path, payload: dict) -> None:
        summary = payload["summary"]
        config = payload["config"]
        rows = self._table(summary)
        html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ASTT Sidecar C 타점 탐색 리포트</title>
  <style>
    body {{ margin:0; background:#f4f6f8; color:#161a1d; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif; line-height:1.55; }}
    main {{ max-width:1180px; margin:0 auto; padding:36px 24px 64px; }}
    section {{ background:#fff; border:1px solid #d9dee7; border-radius:8px; padding:22px; margin:16px 0; }}
    h1 {{ margin:8px 0; font-size:34px; letter-spacing:0; }}
    h2 {{ margin:0 0 14px; font-size:22px; }}
    .pill {{ display:inline-flex; border-radius:999px; padding:5px 10px; background:#e6f4f1; color:#0f766e; font-weight:700; font-size:12px; }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th,td {{ padding:9px 10px; border-bottom:1px solid #d9dee7; text-align:right; white-space:nowrap; }}
    th:first-child,td:first-child {{ text-align:left; }}
    th {{ color:#667085; background:#f8fafc; }}
    .table-wrap {{ overflow-x:auto; }}
    .note {{ color:#667085; }}
  </style>
</head>
<body>
<main>
  <div class="pill">Sidecar C</div>
  <h1>타점 시간대 탐색 리포트</h1>
  <section>
    <h2>분석 기준</h2>
    <p class="note">{escape(config["start_date"])}부터 {escape(config["end_date"])}까지, 진입 전 {config["pre_minutes"]}분 흐름과 진입 후 {config["target_minutes"]}분/{config["exit_minutes"]}분 흐름을 함께 봅니다.</p>
    <p class="note">단순 수익률 순위가 아니라 거래대금 가속, 사전 방향성, 목표 구간 상승폭, 하락폭, 종료 수익률을 종합한 pinpoint_score로 정렬합니다.</p>
  </section>
  <section>
    <h2>추천 시간대</h2>
    <div class="table-wrap">{rows}</div>
  </section>
  <section>
    <h2>해석 원칙</h2>
    <ul>
      <li>표본 부족 시간대는 실제 전략 타점으로 쓰지 않습니다.</li>
      <li>평일과 주말은 분리해서 봅니다.</li>
      <li>이 결과는 09:00 전략을 대체하지 않고, 어떤 시간대를 추가 검증할지 좁히는 Sidecar C 연구 산출물입니다.</li>
    </ul>
  </section>
</main>
</body>
</html>"""
        path.write_text(html, encoding="utf-8")

    def _table(self, rows: list[dict]) -> str:
        if not rows:
            return "<p>데이터가 아직 없습니다.</p>"
        headers = list(rows[0].keys())
        head = "".join(f"<th>{escape(self._label(key))}</th>" for key in headers)
        body = ""
        for row in rows:
            body += "<tr>" + "".join(f"<td>{escape(self._value(row.get(key)))}</td>" for key in headers) + "</tr>"
        return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"

    def _label(self, key: str) -> str:
        return {
            "entry_time": "진입시간",
            "day_type": "구분",
            "samples": "표본",
            "active_days": "활성일",
            "suggested_days_per_week": "주당후보일",
            "success_rate": "성공률",
            "avg_flow_score": "평균흐름점수",
            "avg_target_max_up_pct": "30분상승폭",
            "avg_target_max_down_pct": "30분하락폭",
            "avg_exit_return_pct": "60분종료수익",
            "pinpoint_score": "핀포인트점수",
            "recommendation": "판정",
        }.get(key, key)

    def _value(self, value: object) -> str:
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value)

    def _parse_time(self, value: str) -> time:
        hour, minute = [int(part) for part in value.split(":")]
        return time(hour, minute)


def default_entry_times(step_minutes: int = 30) -> list[str]:
    values = []
    current = datetime.combine(date.today(), time(0, 30))
    end = datetime.combine(date.today(), time(22, 30))
    while current <= end:
        values.append(current.strftime("%H:%M"))
        current += timedelta(minutes=step_minutes)
    return values

