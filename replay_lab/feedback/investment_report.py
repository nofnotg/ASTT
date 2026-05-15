from __future__ import annotations

import json
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR


@dataclass(frozen=True)
class InvestmentReportBuilder:
    store_dir: Path = REPLAY_STORE_DIR
    capital_krw: float = 500000

    @property
    def experiments_dir(self) -> Path:
        return self.store_dir / "experiments"

    @property
    def out_dir(self) -> Path:
        return self.store_dir / "reports" / "investment_2026"

    def build(self, start_date: str = "2026-01-01", end_date: str | None = None) -> Path:
        end_date = end_date or pd.Timestamp.today().date().isoformat()
        frames = self._load_current_frames(start_date, end_date)
        daily = self._daily_rows(frames["decisions"], frames["trades"], frames["personas"])
        weekly = self._period_rows(daily, "W-SUN")
        monthly = self._period_rows(daily, "M")
        personas = self._persona_rows(frames["personas"], frames["trades"])
        summary = self._summary(daily, personas)
        payload = {
            "summary": summary,
            "daily": daily,
            "weekly": weekly,
            "monthly": monthly,
            "persona_validity": personas,
            "sidecar_c": self._sidecar_c_rows(),
            "meta": frames["meta"],
        }
        self.out_dir.mkdir(parents=True, exist_ok=True)
        (self.out_dir / "investment_report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._write_html(self.out_dir / "investment_report.html", payload)
        return self.out_dir / "investment_report.html"

    def _load_current_frames(self, start_date: str, end_date: str) -> dict[str, Any]:
        experiments = sorted(self.experiments_dir.glob("exp_*")) if self.experiments_dir.exists() else []
        frames: dict[str, list[pd.DataFrame]] = {"decisions": [], "trades": [], "personas": []}
        for exp in experiments:
            config_path = exp / "config.json"
            config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
            if config.get("mode") != "PAPER_REPLAY_DAILY_STUDY":
                continue
            for key, filename in [("decisions", "decisions.parquet"), ("trades", "paper_trades.parquet"), ("personas", "persona_scores.parquet")]:
                path = exp / filename
                if path.exists():
                    frame = pd.read_parquet(path)
                    frame["experiment_id"] = exp.name
                    frames[key].append(frame)
        loaded = {key: pd.concat(value, ignore_index=True) if value else pd.DataFrame() for key, value in frames.items()}
        decisions = loaded["decisions"]
        if not decisions.empty:
            for required in ["target_window_end_time_kst", "no_entry_reason"]:
                if required not in decisions:
                    decisions[required] = pd.NA
            decisions = decisions[decisions["target_window_end_time_kst"].notna()]
            decisions = decisions[(pd.to_datetime(decisions["date_kst"]) >= pd.Timestamp(start_date)) & (pd.to_datetime(decisions["date_kst"]) <= pd.Timestamp(end_date))]
            latest_by_date = decisions.groupby("date_kst")["experiment_id"].max().to_dict()
            decisions = decisions[decisions.apply(lambda row: row["experiment_id"] == latest_by_date.get(row["date_kst"]), axis=1)]
        session_ids = set(decisions.get("session_id", pd.Series(dtype=str)).astype(str).tolist())

        def related(frame: pd.DataFrame) -> pd.DataFrame:
            if frame.empty or not session_ids or "session_id" not in frame:
                return frame.iloc[0:0] if not session_ids else frame
            return frame[frame["session_id"].astype(str).isin(session_ids)].copy()

        trades = related(loaded["trades"])
        personas = related(loaded["personas"])
        return {
            "decisions": decisions,
            "trades": trades,
            "personas": personas,
            "meta": {
                "start_date": start_date,
                "end_date": end_date,
                "decision_count": int(len(decisions)),
                "trade_count": int(len(trades)),
                "persona_count": int(len(personas)),
            },
        }

    def _daily_rows(self, decisions: pd.DataFrame, trades: pd.DataFrame, personas: pd.DataFrame) -> list[dict]:
        if decisions.empty:
            return []
        rows = []
        for day, day_decisions in decisions.groupby("date_kst", sort=True):
            day_trades = trades[trades["date_kst"].astype(str) == str(day)] if not trades.empty and "date_kst" in trades else pd.DataFrame()
            allocation = self.capital_krw / len(day_trades) if len(day_trades) else 0
            pnl_krw = float((day_trades["pnl_pct"].astype(float) / 100 * allocation).sum()) if len(day_trades) and "pnl_pct" in day_trades else 0.0
            top_decision = day_decisions.sort_values(["final_score", "market"], ascending=[False, True]).iloc[0]
            persona_slice = personas[(personas["date_kst"].astype(str) == str(day)) & (personas["market"].astype(str) == str(top_decision["market"]))] if not personas.empty else pd.DataFrame()
            persona_brief = self._persona_brief(persona_slice)
            entries = []
            for _, trade in day_trades.iterrows():
                entries.append(
                    {
                        "market": trade.get("market", ""),
                        "pnl_pct": float(trade.get("pnl_pct", 0.0)),
                        "pnl_krw": float(trade.get("pnl_pct", 0.0)) / 100 * allocation if allocation else 0.0,
                        "exit_reason": trade.get("exit_reason", ""),
                        "forced": bool(trade.get("forced_entry", False)),
                        "entry_price": float(trade.get("entry_price", 0.0)),
                        "exit_price": float(trade.get("exit_price", 0.0)),
                    }
                )
            rows.append(
                {
                    "date": str(day),
                    "day_type": "weekend" if pd.Timestamp(day).weekday() >= 5 else "weekday",
                    "candidates": int(len(day_decisions)),
                    "entries": int(len(day_trades)),
                    "wins": int((day_trades.get("pnl_pct", pd.Series(dtype=float)).astype(float) > 0).sum()) if len(day_trades) else 0,
                    "win_rate": float((day_trades.get("pnl_pct", pd.Series(dtype=float)).astype(float) > 0).mean()) if len(day_trades) else 0.0,
                    "pnl_krw": round(pnl_krw),
                    "return_pct": pnl_krw / self.capital_krw * 100 if self.capital_krw else 0.0,
                    "top_market": str(top_decision.get("market", "")),
                    "top_score": float(top_decision.get("final_score", 0.0)),
                    "decision": str(top_decision.get("final_decision", "")),
                    "no_entry_reason": str(top_decision.get("no_entry_reason", "")),
                    "persona_brief": persona_brief,
                    "entries_detail": entries,
                }
            )
        return rows

    def _period_rows(self, daily: list[dict], freq: str) -> list[dict]:
        if not daily:
            return []
        frame = pd.DataFrame(daily)
        frame["period"] = pd.to_datetime(frame["date"]).dt.to_period(freq).dt.start_time.dt.date.astype(str)
        rows = []
        for period, group in frame.groupby("period", sort=True):
            entries = int(group["entries"].sum())
            wins = int(group["wins"].sum())
            pnl = float(group["pnl_krw"].sum())
            rows.append(
                {
                    "period": period,
                    "days": int(len(group)),
                    "entries": entries,
                    "wins": wins,
                    "win_rate": wins / entries if entries else 0.0,
                    "pnl_krw": round(pnl),
                    "return_pct": pnl / self.capital_krw * 100 if self.capital_krw else 0.0,
                }
            )
        return rows

    def _persona_rows(self, personas: pd.DataFrame, trades: pd.DataFrame) -> list[dict]:
        if personas.empty:
            return []
        frame = personas.copy()
        frame["persona"] = frame["persona"].map(self._persona_name)
        keys = ["session_id", "date_kst", "market"]
        if not trades.empty and all(key in trades.columns for key in keys):
            frame = frame.merge(trades[keys + ["pnl_pct"]], on=keys, how="left")
        else:
            frame["pnl_pct"] = pd.NA
        rows = []
        for name, group in frame.groupby("persona", sort=True):
            trade_rows = group[group["pnl_pct"].notna()]
            corr = self._corr(trade_rows, "score", "pnl_pct")
            win_rate = float((trade_rows["pnl_pct"].astype(float) > 0).mean()) if len(trade_rows) else 0.0
            validity = max(0, min(100, 50 + corr * 35 + win_rate * 15 + min(len(trade_rows) / 100, 1) * 20))
            rows.append(
                {
                    "persona": name,
                    "samples": int(len(group)),
                    "trade_samples": int(len(trade_rows)),
                    "avg_score": float(group["score"].astype(float).mean()),
                    "win_rate": win_rate,
                    "score_pnl_corr": corr,
                    "validity_pct": round(validity, 2),
                    "insight": self._persona_insight(name, validity, len(trade_rows)),
                }
            )
        return rows

    def _summary(self, daily: list[dict], personas: list[dict]) -> dict:
        entries = sum(int(row["entries"]) for row in daily)
        wins = sum(int(row["wins"]) for row in daily)
        pnl = sum(float(row["pnl_krw"]) for row in daily)
        return {
            "days": len(daily),
            "entries": entries,
            "wins": wins,
            "win_rate": wins / entries if entries else 0.0,
            "pnl_krw": round(pnl),
            "return_pct": pnl / self.capital_krw * 100 if self.capital_krw else 0.0,
            "capital_krw": self.capital_krw,
            "best_persona": max(personas, key=lambda row: row["validity_pct"], default={}).get("persona", ""),
        }

    def _write_html(self, path: Path, payload: dict) -> None:
        summary = payload["summary"]
        html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ASTT 2026 일자별 투자검증 보고서</title>
  <style>
    :root {{ --bg:#eef2f6; --panel:#fff; --ink:#15171a; --muted:#697586; --line:#d8dee8; --accent:#0f766e; --soft:#ecfdf5; --loss:#b42318; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif; line-height:1.55; }}
    main {{ max-width:1240px; margin:0 auto; padding:36px 22px 72px; }}
    header {{ margin-bottom:24px; }}
    h1 {{ margin:8px 0; font-size:34px; letter-spacing:0; }}
    h2 {{ margin:0 0 14px; font-size:22px; }}
    h3 {{ margin:0 0 8px; font-size:17px; }}
    section {{ background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:22px; margin:16px 0; box-shadow:0 1px 2px rgba(15,23,42,.04); }}
    .pill {{ display:inline-flex; border-radius:999px; padding:5px 10px; background:#dff7ef; color:var(--accent); font-weight:700; font-size:12px; }}
    .grid {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:12px; }}
    .metric {{ background:#f8fafc; border:1px solid var(--line); border-radius:8px; padding:13px; }}
    .metric span {{ display:block; color:var(--muted); font-size:12px; }}
    .metric strong {{ display:block; margin-top:5px; font-size:21px; }}
    .table-wrap {{ overflow-x:auto; }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th,td {{ padding:9px 10px; border-bottom:1px solid var(--line); text-align:right; white-space:nowrap; }}
    th:first-child,td:first-child {{ text-align:left; }}
    th {{ background:#f8fafc; color:var(--muted); }}
    .daily {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }}
    .day-card {{ border:1px solid var(--line); border-radius:10px; padding:16px; background:#fff; }}
    .day-head {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }}
    .win {{ color:var(--accent); font-weight:700; }}
    .loss {{ color:var(--loss); font-weight:700; }}
    .muted {{ color:var(--muted); }}
    .small {{ font-size:13px; }}
    @media (max-width:900px) {{ .grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .daily {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <div class="pill">Daily Forced Replay Study</div>
    <h1>ASTT 2026 일자별 투자검증 보고서</h1>
    <p class="muted">2026-01-01 이후 데이터를 기준으로, 매일 최고 후보를 PAPER 진입시켜 표본을 만들고 페르소나 판단의 유효성을 검증합니다.</p>
  </header>
  <section>
    <h2>핵심 요약</h2>
    <div class="grid">
      {self._metric("분석 일수", summary["days"])}
      {self._metric("진입 표본", f"{summary['entries']}건")}
      {self._metric("승률", self._pct(summary["win_rate"]))}
      {self._metric("누적 손익", self._krw(summary["pnl_krw"]))}
      {self._metric("최고 페르소나", summary.get("best_persona", ""))}
    </div>
  </section>
  {self._table_section("주간 투자보고서", payload["weekly"])}
  {self._table_section("월간 투자보고서", payload["monthly"])}
  {self._table_section("페르소나 유효성 평가", payload["persona_validity"])}
  {self._table_section("Sidecar C 타점 탐색", payload["sidecar_c"])}
  {self._daily_section(payload["daily"])}
</main>
</body>
</html>"""
        path.write_text(html, encoding="utf-8")

    def _daily_section(self, rows: list[dict]) -> str:
        cards = []
        for row in rows:
            cls = "win" if row["pnl_krw"] > 0 else "loss" if row["pnl_krw"] < 0 else "muted"
            entry_text = ", ".join(f"{item['market']} {item['pnl_pct']:.2f}% ({self._krw(item['pnl_krw'])})" for item in row["entries_detail"]) or "진입 없음"
            cards.append(
                f"""<article class="day-card">
  <div class="day-head">
    <div><h3>{escape(row['date'])} <span class="muted small">{escape(row['day_type'])}</span></h3><div class="small muted">최고 후보: {escape(row['top_market'])} / 점수 {row['top_score']:.1f}</div></div>
    <div class="{cls}">{self._krw(row['pnl_krw'])}</div>
  </div>
  <p class="small">진입: {row['entries']}건 / 승률: {self._pct(row['win_rate'])}</p>
  <p class="small">거래 기록: {escape(entry_text)}</p>
  <p class="small muted">미진입 사유 또는 원판정: {escape(row['no_entry_reason'] or row['decision'])}</p>
  <p class="small muted">페르소나: {escape(row['persona_brief'])}</p>
</article>"""
            )
        return f"<section><h2>일자별 투자보고서</h2><div class=\"daily\">{''.join(cards)}</div></section>"

    def _table_section(self, title: str, rows: list[dict]) -> str:
        if not rows:
            return f"<section><h2>{escape(title)}</h2><p class=\"muted\">데이터가 없습니다.</p></section>"
        headers = [key for key in rows[0].keys() if key not in {"entries_detail", "insight"}]
        head = "".join(f"<th>{escape(self._label(key))}</th>" for key in headers)
        body = ""
        for row in rows:
            body += "<tr>" + "".join(f"<td>{escape(self._display(row.get(key)))}</td>" for key in headers) + "</tr>"
        if title.startswith("페르소나"):
            body += "".join(f"<tr><td colspan=\"{len(headers)}\" style=\"text-align:left;color:#697586\">{escape(row['persona'])}: {escape(row.get('insight',''))}</td></tr>" for row in rows)
        return f"<section><h2>{escape(title)}</h2><div class=\"table-wrap\"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div></section>"

    def _persona_brief(self, frame: pd.DataFrame) -> str:
        if frame.empty:
            return "페르소나 기록 없음"
        items = []
        for _, row in frame.sort_values("score", ascending=False).iterrows():
            items.append(f"{self._persona_name(row['persona'])} {float(row['score']):.0f}")
        return " / ".join(items)

    def _sidecar_c_rows(self) -> list[dict]:
        path = self.store_dir / "reports" / "sidecar_c" / "time_window_discovery.json"
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload.get("summary", [])

    def _persona_name(self, value: Any) -> str:
        name = str(value)
        if name in {"留ㅺ린", "筌띲끆由?", "Maggie"}:
            return "매기"
        return name

    def _persona_insight(self, name: str, validity: float, trades: int) -> str:
        if trades < 30:
            return "거래 표본이 아직 작아 방향성만 참고합니다. 강제 일일 진입 실행 후 재평가가 필요합니다."
        if validity >= 70:
            return "현재 표본에서 판단 점수와 결과의 연결성이 비교적 좋습니다."
        if validity <= 45:
            return "점수와 결과가 약하거나 반대로 움직일 수 있어 기준 재조정 후보입니다."
        return "중립입니다. 단독 판단보다 다른 페르소나와 조합해 봐야 합니다."

    def _corr(self, frame: pd.DataFrame, left: str, right: str) -> float:
        if len(frame) < 3 or left not in frame or right not in frame:
            return 0.0
        data = frame[[left, right]].dropna().copy()
        if len(data) < 3 or data[left].nunique() < 2 or data[right].nunique() < 2:
            return 0.0
        return float(pd.to_numeric(data[left], errors="coerce").corr(pd.to_numeric(data[right], errors="coerce")))

    def _metric(self, label: str, value: Any) -> str:
        return f"<div class=\"metric\"><span>{escape(str(label))}</span><strong>{escape(str(value))}</strong></div>"

    def _label(self, key: str) -> str:
        return {
            "period": "기간",
            "days": "일수",
            "entries": "진입",
            "wins": "승리",
            "win_rate": "승률",
            "pnl_krw": "손익",
            "return_pct": "수익률",
            "persona": "페르소나",
            "samples": "표본",
            "trade_samples": "거래표본",
            "avg_score": "평균점수",
            "score_pnl_corr": "점수-손익상관",
            "validity_pct": "유효성%",
            "entry_time": "진입시간",
            "day_type": "구분",
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

    def _display(self, value: Any) -> str:
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value)

    def _pct(self, value: float) -> str:
        return f"{float(value):.2%}"

    def _krw(self, value: float) -> str:
        return f"{float(value):,.0f}원"
