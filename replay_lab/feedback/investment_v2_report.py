from __future__ import annotations

import json
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR


@dataclass(frozen=True)
class InvestmentV2ReportBuilder:
    store_dir: Path = REPLAY_STORE_DIR
    capital_krw: float = 500000

    @property
    def experiments_dir(self) -> Path:
        return self.store_dir / "experiments"

    @property
    def out_dir(self) -> Path:
        return self.store_dir / "reports" / "investment_v2"

    def build(self, start_date: str = "2026-01-01", end_date: str | None = None) -> Path:
        end_date = end_date or pd.Timestamp.today().date().isoformat()
        frames = self._load_frames(start_date, end_date)
        daily = self._daily_rows(frames["decisions"], frames["trades"], frames["personas"])
        weekly = self._period_rows(daily, "W-SUN")
        monthly = self._period_rows(daily, "M")
        personas = self._persona_rows(frames["personas"], frames["trades"], frames["decisions"])
        thresholds = self._threshold_rows(frames["decisions"], frames["trades"])
        universe = self._universe_rows(frames["universe"])
        comparison = self._comparison(self._summary(daily), start_date, end_date)
        payload = {
            "summary": self._summary(daily),
            "daily": daily,
            "weekly": weekly,
            "monthly": monthly,
            "persona_validity": personas,
            "thresholds": thresholds,
            "universe_stages": universe,
            "comparison_with_v1": comparison,
            "improvement_insights": self._improvement_insights(daily, personas, thresholds, comparison),
            "meta": frames["meta"],
        }
        self.out_dir.mkdir(parents=True, exist_ok=True)
        (self.out_dir / "investment_v2_report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._write_html(self.out_dir / "investment_v2_report.html", payload)
        return self.out_dir / "investment_v2_report.html"

    def _load_frames(self, start_date: str, end_date: str) -> dict[str, Any]:
        frames: dict[str, list[pd.DataFrame]] = {"decisions": [], "trades": [], "personas": [], "universe": []}
        experiments = sorted(self.experiments_dir.glob("exp_*_v2")) if self.experiments_dir.exists() else []
        for exp in experiments:
            config_path = exp / "config.json"
            config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
            if config.get("mode") != "PAPER_REPLAY_V2":
                continue
            for key, filename in [
                ("decisions", "decisions.parquet"),
                ("trades", "paper_trades.parquet"),
                ("personas", "persona_scores.parquet"),
                ("universe", "universe_stages.parquet"),
            ]:
                path = exp / filename
                if path.exists():
                    frame = pd.read_parquet(path)
                    frame["experiment_id"] = exp.name
                    frames[key].append(frame)

        loaded = {key: pd.concat(value, ignore_index=True) if value else pd.DataFrame() for key, value in frames.items()}
        decisions = self._filter_latest_by_date(loaded["decisions"], start_date, end_date)
        session_ids = set(decisions.get("session_id", pd.Series(dtype=str)).astype(str).tolist())

        def related(frame: pd.DataFrame) -> pd.DataFrame:
            if frame.empty or not session_ids or "session_id" not in frame:
                return frame.iloc[0:0] if not session_ids else frame
            return frame[frame["session_id"].astype(str).isin(session_ids)].copy()

        trades = related(loaded["trades"])
        personas = related(loaded["personas"])
        universe = loaded["universe"]
        if not universe.empty:
            universe = universe[(pd.to_datetime(universe["date_kst"]) >= pd.Timestamp(start_date)) & (pd.to_datetime(universe["date_kst"]) <= pd.Timestamp(end_date))]
            if "experiment_id" in universe and not decisions.empty:
                allowed = set(decisions["experiment_id"].astype(str).unique())
                universe = universe[universe["experiment_id"].astype(str).isin(allowed)]

        return {
            "decisions": decisions,
            "trades": trades,
            "personas": personas,
            "universe": universe,
            "meta": {
                "start_date": start_date,
                "end_date": end_date,
                "decision_count": int(len(decisions)),
                "trade_count": int(len(trades)),
                "persona_count": int(len(personas)),
                "universe_stage_count": int(len(universe)),
            },
        }

    def _filter_latest_by_date(self, decisions: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
        if decisions.empty:
            return decisions
        required = {
            "entry_gate_decision": "HOLD",
            "entry_gate_confidence": 0.0,
            "entry_gate_reason": "",
            "no_entry_reason": "",
            "entered_by_v2": False,
        }
        for key, default in required.items():
            if key not in decisions:
                decisions[key] = default
        decisions = decisions[(pd.to_datetime(decisions["date_kst"]) >= pd.Timestamp(start_date)) & (pd.to_datetime(decisions["date_kst"]) <= pd.Timestamp(end_date))]
        latest_by_date = decisions.groupby("date_kst")["experiment_id"].max().to_dict()
        return decisions[decisions.apply(lambda row: row["experiment_id"] == latest_by_date.get(row["date_kst"]), axis=1)].copy()

    def _daily_rows(self, decisions: pd.DataFrame, trades: pd.DataFrame, personas: pd.DataFrame) -> list[dict[str, Any]]:
        if decisions.empty:
            return []
        rows = []
        for day, group in decisions.groupby("date_kst", sort=True):
            day_trades = trades[trades["date_kst"].astype(str) == str(day)] if not trades.empty and "date_kst" in trades else pd.DataFrame()
            pnl_krw = float(day_trades["pnl_pct"].astype(float).sum() / 100 * self.capital_krw) if len(day_trades) and "pnl_pct" in day_trades else 0.0
            sort_cols = [col for col in ["entered_by_v2", "entry_gate_confidence", "final_score", "market"] if col in group]
            ascending = [False, False, False, True][: len(sort_cols)]
            top = group.sort_values(sort_cols, ascending=ascending).iloc[0] if sort_cols else group.iloc[0]
            persona_slice = personas[(personas["date_kst"].astype(str) == str(day)) & (personas["market"].astype(str) == str(top.get("market", "")))] if not personas.empty else pd.DataFrame()
            trade = day_trades.iloc[0] if len(day_trades) else None
            entered = len(day_trades) > 0
            rows.append(
                {
                    "date": str(day),
                    "day_type": "weekend" if pd.Timestamp(day).weekday() >= 5 else "weekday",
                    "candidate_count": int(len(group[group["market"].astype(str) != ""])) if "market" in group else int(len(group)),
                    "entered": entered,
                    "entry_count": int(len(day_trades)),
                    "market": str(top.get("market", "")),
                    "entry_gate_decision": str(top.get("entry_gate_decision", "HOLD")),
                    "entry_gate_confidence": float(top.get("entry_gate_confidence", 0.0)),
                    "entry_gate_reason": str(top.get("entry_gate_reason", "")),
                    "no_entry_reason": "" if entered else str(top.get("no_entry_reason", top.get("entry_gate_reason", ""))),
                    "final_score": float(top.get("final_score", 0.0)),
                    "weekly_trend_score": float(top.get("weekly_trend_score", 0.0)),
                    "daily_trend_score": float(top.get("daily_trend_score", 0.0)),
                    "h4_trend_score": float(top.get("h4_trend_score", 0.0)),
                    "morning_liquidity_score": float(top.get("morning_liquidity_score", 0.0)),
                    "preopen_volume_score": float(top.get("preopen_volume_score", 0.0)),
                    "pnl_pct": float(trade.get("pnl_pct", 0.0)) if trade is not None else 0.0,
                    "pnl_krw": round(pnl_krw),
                    "exit_reason": str(trade.get("exit_reason", "")) if trade is not None else "",
                    "fill_timeframe": str(trade.get("fill_timeframe", "")) if trade is not None else "",
                    "persona_brief": self._persona_brief(persona_slice),
                }
            )
        return rows

    def _period_rows(self, daily: list[dict[str, Any]], freq: str) -> list[dict[str, Any]]:
        if not daily:
            return []
        frame = pd.DataFrame(daily)
        frame["period"] = pd.to_datetime(frame["date"]).dt.to_period(freq).dt.start_time.dt.date.astype(str)
        rows = []
        for period, group in frame.groupby("period", sort=True):
            entries = int(group["entry_count"].sum())
            wins = int((group[group["entered"]]["pnl_pct"].astype(float) > 0).sum()) if entries else 0
            pnl = float(group["pnl_krw"].sum())
            rows.append(
                {
                    "period": period,
                    "days": int(len(group)),
                    "entries": entries,
                    "holds": int(len(group) - entries),
                    "wins": wins,
                    "win_rate": wins / entries if entries else 0.0,
                    "pnl_krw": round(pnl),
                    "return_pct": pnl / self.capital_krw * 100 if self.capital_krw else 0.0,
                }
            )
        return rows

    def _persona_rows(self, personas: pd.DataFrame, trades: pd.DataFrame, decisions: pd.DataFrame) -> list[dict[str, Any]]:
        if personas.empty:
            return []
        frame = personas.copy()
        keys = ["session_id", "date_kst", "market"]
        if not trades.empty and all(key in trades.columns for key in keys):
            frame = frame.merge(trades[keys + ["pnl_pct"]], on=keys, how="left")
        else:
            frame["pnl_pct"] = pd.NA
        if not decisions.empty and all(key in decisions.columns for key in keys):
            frame = frame.merge(decisions[keys + ["entry_gate_decision", "entry_gate_confidence"]], on=keys, how="left")
        rows = []
        for name, group in frame.groupby("persona", sort=True):
            score = group["score"].astype(float)
            trade_rows = group[group["pnl_pct"].notna()].copy()
            corr = self._corr(trade_rows, "score", "pnl_pct")
            win_rate = float((trade_rows["pnl_pct"].astype(float) > 0).mean()) if len(trade_rows) else 0.0
            std = float(score.std()) if len(score) > 1 else 0.0
            variance_penalty = 20.0 if std < 3.0 else 0.0
            sample_bonus = min(len(group) / 150, 1) * 15
            trade_bonus = min(len(trade_rows) / 40, 1) * 10
            validity = max(0.0, min(100.0, 45 + corr * 30 + win_rate * 20 + sample_bonus + trade_bonus - variance_penalty))
            rows.append(
                {
                    "persona": str(name),
                    "candidate_samples": int(len(group)),
                    "trade_samples": int(len(trade_rows)),
                    "avg_score": round(float(score.mean()), 2),
                    "score_std": round(std, 2),
                    "win_rate": win_rate,
                    "score_pnl_corr": corr,
                    "variance_penalty": variance_penalty,
                    "validity_pct": round(validity, 2),
                    "insight": self._persona_insight(str(name), validity, std, len(trade_rows)),
                }
            )
        return rows

    def _threshold_rows(self, decisions: pd.DataFrame, trades: pd.DataFrame) -> list[dict[str, Any]]:
        if decisions.empty:
            return []
        frame = decisions.copy()
        keys = ["session_id", "date_kst", "market"]
        if not trades.empty and all(key in trades.columns for key in keys):
            frame = frame.merge(trades[keys + ["pnl_pct"]], on=keys, how="left")
        else:
            frame["pnl_pct"] = pd.NA
        rows = []
        for label, column, minimum in [
            ("Final Score 82+", "final_score", 82),
            ("Final Score 90+", "final_score", 90),
            ("EntryGate 70+", "entry_gate_confidence", 70),
            ("EntryGate 80+", "entry_gate_confidence", 80),
            ("Morning Liquidity 60+", "morning_liquidity_score", 60),
            ("Preopen Volume 60+", "preopen_volume_score", 60),
        ]:
            if column not in frame:
                continue
            scoped = frame[frame[column].astype(float) >= minimum]
            trade_rows = scoped[scoped["pnl_pct"].notna()]
            rows.append(
                {
                    "threshold": label,
                    "candidate_count": int(len(scoped)),
                    "entries": int(len(trade_rows)),
                    "win_rate": float((trade_rows["pnl_pct"].astype(float) > 0).mean()) if len(trade_rows) else 0.0,
                    "avg_pnl_pct": float(trade_rows["pnl_pct"].astype(float).mean()) if len(trade_rows) else 0.0,
                }
            )
        return rows

    def _universe_rows(self, universe: pd.DataFrame) -> list[dict[str, Any]]:
        if universe.empty:
            return []
        rows = []
        for stage, group in universe.groupby("universe_stage", sort=True):
            rows.append(
                {
                    "stage": str(stage),
                    "checked": int(len(group)),
                    "passed": int(group["passed"].astype(bool).sum()) if "passed" in group else 0,
                    "pass_rate": float(group["passed"].astype(bool).mean()) if "passed" in group and len(group) else 0.0,
                    "avg_score": round(float(group["universe_score"].astype(float).mean()), 2) if "universe_score" in group and len(group) else 0.0,
                }
            )
        return rows

    def _summary(self, daily: list[dict[str, Any]]) -> dict[str, Any]:
        entries = sum(int(row["entry_count"]) for row in daily)
        wins = sum(1 for row in daily if row["entered"] and float(row["pnl_pct"]) > 0)
        pnl = sum(float(row["pnl_krw"]) for row in daily)
        return {
            "days": len(daily),
            "entries": entries,
            "holds": len(daily) - entries,
            "wins": wins,
            "win_rate": wins / entries if entries else 0.0,
            "pnl_krw": round(pnl),
            "return_pct": pnl / self.capital_krw * 100 if self.capital_krw else 0.0,
            "capital_krw": self.capital_krw,
        }

    def _comparison(self, v2_summary: dict[str, Any], start_date: str, end_date: str) -> dict[str, Any]:
        path = self.store_dir / "reports" / "investment_2026" / "investment_report.json"
        if not path.exists():
            return {"available": False}
        payload = json.loads(path.read_text(encoding="utf-8"))
        v1 = payload.get("summary", {})
        return {
            "available": True,
            "period": f"{start_date}~{end_date}",
            "v1_entries": int(v1.get("entries", 0)),
            "v1_win_rate": float(v1.get("win_rate", 0.0)),
            "v1_pnl_krw": round(float(v1.get("pnl_krw", 0.0))),
            "v2_entries": int(v2_summary.get("entries", 0)),
            "v2_win_rate": float(v2_summary.get("win_rate", 0.0)),
            "v2_pnl_krw": round(float(v2_summary.get("pnl_krw", 0.0))),
            "pnl_delta_krw": round(float(v2_summary.get("pnl_krw", 0.0)) - float(v1.get("pnl_krw", 0.0))),
            "win_rate_delta": float(v2_summary.get("win_rate", 0.0)) - float(v1.get("win_rate", 0.0)),
        }

    def _improvement_insights(self, daily: list[dict[str, Any]], personas: list[dict[str, Any]], thresholds: list[dict[str, Any]], comparison: dict[str, Any]) -> list[str]:
        insights = [
            "EntryGate는 강제진입을 기본값에서 제거하고, 조건 미달일을 HOLD로 남긴다. 손실 방어력은 진입 수 감소와 함께 평가해야 한다.",
            "08:50~08:59만 보지 않고 전일, 당일 오전, 08:30~08:49 예열 흐름을 함께 반영한다. 즉 9시 직전 거래량만 튄 코인보다 준비된 흐름을 우선한다.",
            "CostA처럼 점수가 거의 고정되는 페르소나는 분산 부족 패널티를 적용했다. 점수가 매번 비슷하면 예측 신호라기보다 안전장치 성격에 가깝다.",
        ]
        if comparison.get("available"):
            delta = comparison.get("pnl_delta_krw", 0)
            insights.append(f"1차 대비 손익 차이는 {delta:,.0f}원이다. 승률뿐 아니라 보류일 증가와 손실 회피를 같이 봐야 한다.")
        if thresholds:
            best = max(thresholds, key=lambda row: row.get("avg_pnl_pct", 0.0))
            insights.append(f"현재 임계값 그룹 중 평균 손익이 가장 나은 구간은 {best['threshold']}이다. 다음 실험은 이 구간을 중심으로 EntryGate confidence를 조정한다.")
        weak = [row for row in personas if row.get("variance_penalty", 0) > 0]
        if weak:
            names = ", ".join(row["persona"] for row in weak)
            insights.append(f"분산 부족 패널티 대상 페르소나: {names}. 해당 페르소나는 단독 진입 근거보다 보조 필터로 쓰는 편이 타당하다.")
        if daily and not any(row["entered"] for row in daily):
            insights.append("검증 기간에 실제 진입이 없다면 EntryGate 임계값이 과도하게 보수적이다. 후보 필터와 confidence 기준을 분리해 완화 실험이 필요하다.")
        return insights

    def _persona_brief(self, personas: pd.DataFrame) -> list[dict[str, Any]]:
        if personas.empty:
            return []
        return [
            {
                "persona": str(row.get("persona", "")),
                "score": round(float(row.get("score", 0.0)), 1),
                "decision": str(row.get("decision", "")),
            }
            for _, row in personas.sort_values("persona").iterrows()
        ]

    def _persona_insight(self, name: str, validity: float, std: float, trade_samples: int) -> str:
        if std < 3:
            return "점수 변화가 작아 방향 예측력보다 안전/구조 체크 역할로 보는 편이 맞다."
        if trade_samples < 10:
            return "후보 평가 표본은 있으나 실제 진입 표본이 적어 다음 배치에서 보강해야 한다."
        if validity >= 65:
            return "현재 표본에서는 손익과 비교적 잘 맞는 편이다. 진입 근거 가중치를 유지하거나 소폭 상향할 수 있다."
        return "단독 판단 근거로 쓰기에는 약하다. 다른 페르소나와 결합 조건으로 제한하는 편이 낫다."

    def _corr(self, frame: pd.DataFrame, left: str, right: str) -> float:
        if frame.empty or len(frame) < 2 or left not in frame or right not in frame:
            return 0.0
        left_values = frame[left].astype(float)
        right_values = frame[right].astype(float)
        if float(left_values.std()) == 0.0 or float(right_values.std()) == 0.0:
            return 0.0
        value = left_values.corr(right_values)
        return 0.0 if pd.isna(value) else float(value)

    def _write_html(self, path: Path, payload: dict[str, Any]) -> None:
        summary = payload["summary"]
        html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ASTT 2차 투자 검증 리포트</title>
  <style>
    :root {{ --bg:#f4f6f8; --panel:#ffffff; --ink:#111827; --muted:#64748b; --line:#dbe3ea; --accent:#0f766e; --accent2:#2563eb; --warn:#b45309; --loss:#b42318; --gain:#067647; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif; line-height:1.55; }}
    main {{ max-width:1280px; margin:0 auto; padding:34px 20px 72px; }}
    header {{ display:grid; gap:12px; margin-bottom:22px; }}
    h1 {{ margin:0; font-size:32px; letter-spacing:0; }}
    h2 {{ margin:0 0 14px; font-size:21px; }}
    h3 {{ margin:0 0 10px; font-size:16px; }}
    .note {{ color:var(--muted); max-width:900px; }}
    .grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }}
    .card {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; }}
    .metric b {{ display:block; font-size:24px; margin-top:4px; }}
    .pill {{ display:inline-flex; align-items:center; border-radius:999px; padding:3px 9px; font-size:12px; background:#e6f4f1; color:#0f766e; }}
    .loss {{ color:var(--loss); }} .gain {{ color:var(--gain); }}
    section {{ margin-top:18px; }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th,td {{ border-bottom:1px solid var(--line); padding:9px 8px; text-align:left; vertical-align:top; }}
    th {{ color:#334155; background:#f8fafc; position:sticky; top:0; }}
    .scroll {{ max-height:620px; overflow:auto; border:1px solid var(--line); border-radius:8px; background:white; }}
    .two {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
    ul {{ margin:8px 0 0 20px; padding:0; }}
    .small {{ font-size:12px; color:var(--muted); }}
    @media (max-width:900px) {{ .grid,.two {{ grid-template-columns:1fr; }} h1 {{ font-size:26px; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <span class="pill">Replay Lab Sidecar · V2 EntryGate</span>
    <h1>ASTT 2차 투자 검증 리포트</h1>
    <p class="note">매일 최대 1회만 진입하되, EntryGate 페르소나가 ENTER/HOLD/REJECT를 결정합니다. 어려운 표현은 바로 옆에 쉬운 설명을 붙였습니다. 손익 단위는 50만원 기준 원화입니다.</p>
  </header>
  <section class="grid">
    {self._metric("검증일", f"{summary['days']:,}일")}
    {self._metric("진입", f"{summary['entries']:,}회")}
    {self._metric("승률", self._pct(summary["win_rate"]))}
    {self._metric("손익", self._krw(summary["pnl_krw"]), "gain" if summary["pnl_krw"] >= 0 else "loss")}
  </section>
  <section class="card">
    <h2>1. 종합 요약</h2>
    {self._comparison_html(payload["comparison_with_v1"])}
    <p class="small">HOLD는 “조건이 부족해서 오늘은 들어가지 않음”입니다. 손실을 피한 날도 전략의 결과로 기록합니다.</p>
  </section>
  <section class="card">
    <h2>2. 일자별 투자보고서</h2>
    <div class="scroll">{self._daily_table(payload["daily"])}</div>
  </section>
  <section class="two">
    <div class="card"><h2>3. 주간 투자보고서</h2>{self._period_table(payload["weekly"])}</div>
    <div class="card"><h2>4. 월간 투자보고서</h2>{self._period_table(payload["monthly"])}</div>
  </section>
  <section class="two">
    <div class="card"><h2>5. 페르소나별 유효성</h2>{self._persona_table(payload["persona_validity"])}</div>
    <div class="card"><h2>6. 점수 임계값별 성과</h2>{self._threshold_table(payload["thresholds"])}</div>
  </section>
  <section class="card">
    <h2>7. 후보군 선별 단계</h2>
    <p class="small">전체 KRW 마켓에서 주봉/일봉/4시간/오전 유동성/9시 직전 예열 흐름을 차례로 본 뒤 최종 후보를 줄입니다.</p>
    {self._universe_table(payload["universe_stages"])}
  </section>
  <section class="card">
    <h2>8. 개선 인사이트와 다음 실험</h2>
    <ul>{"".join(f"<li>{escape(item)}</li>" for item in payload["improvement_insights"])}</ul>
  </section>
</main>
</body>
</html>"""
        path.write_text(html, encoding="utf-8")

    def _metric(self, label: str, value: str, klass: str = "") -> str:
        return f'<div class="card metric"><span class="small">{escape(label)}</span><b class="{klass}">{escape(value)}</b></div>'

    def _comparison_html(self, row: dict[str, Any]) -> str:
        if not row.get("available"):
            return "<p>1차 리포트 JSON을 찾지 못해 비교 섹션은 대기 상태입니다.</p>"
        return (
            '<div class="grid">'
            + self._metric("1차 진입", f"{row['v1_entries']:,}회")
            + self._metric("1차 손익", self._krw(row["v1_pnl_krw"]), "gain" if row["v1_pnl_krw"] >= 0 else "loss")
            + self._metric("2차 진입", f"{row['v2_entries']:,}회")
            + self._metric("손익 차이", self._krw(row["pnl_delta_krw"]), "gain" if row["pnl_delta_krw"] >= 0 else "loss")
            + "</div>"
        )

    def _daily_table(self, rows: list[dict[str, Any]]) -> str:
        if not rows:
            return "<p>아직 V2 일자별 결과가 없습니다.</p>"
        body = []
        for row in rows:
            reason = row["entry_gate_reason"] if row["entered"] else row["no_entry_reason"]
            body.append(
                "<tr>"
                f"<td>{escape(row['date'])}<br><span class='small'>{escape(row['day_type'])}</span></td>"
                f"<td>{escape(row['market']) or '-'}</td>"
                f"<td>{'진입' if row['entered'] else '보류'}</td>"
                f"<td>{row['entry_gate_confidence']:.1f}</td>"
                f"<td>{row['final_score']:.1f}</td>"
                f"<td>{self._krw(row['pnl_krw'])}<br><span class='small'>{self._pct(row['pnl_pct'] / 100)}</span></td>"
                f"<td>{escape(row['exit_reason']) or '-'}</td>"
                f"<td>{escape(reason)}</td>"
                f"<td>{self._persona_inline(row['persona_brief'])}</td>"
                "</tr>"
            )
        return "<table><thead><tr><th>날짜</th><th>선택 코인</th><th>결정</th><th>Gate</th><th>Final</th><th>손익</th><th>청산</th><th>진입/미진입 사유</th><th>페르소나</th></tr></thead><tbody>" + "".join(body) + "</tbody></table>"

    def _period_table(self, rows: list[dict[str, Any]]) -> str:
        if not rows:
            return "<p>집계할 데이터가 없습니다.</p>"
        body = "".join(
            f"<tr><td>{escape(row['period'])}</td><td>{row['days']}</td><td>{row['entries']}</td><td>{row['holds']}</td><td>{self._pct(row['win_rate'])}</td><td>{self._krw(row['pnl_krw'])}</td></tr>"
            for row in rows
        )
        return "<table><thead><tr><th>기간</th><th>일수</th><th>진입</th><th>보류</th><th>승률</th><th>손익</th></tr></thead><tbody>" + body + "</tbody></table>"

    def _persona_table(self, rows: list[dict[str, Any]]) -> str:
        if not rows:
            return "<p>페르소나 표본이 없습니다.</p>"
        body = "".join(
            f"<tr><td>{escape(row['persona'])}</td><td>{row['validity_pct']:.1f}%</td><td>{row['candidate_samples']}</td><td>{row['trade_samples']}</td><td>{row['avg_score']:.1f}</td><td>{row['score_std']:.1f}</td><td>{escape(row['insight'])}</td></tr>"
            for row in rows
        )
        return "<table><thead><tr><th>페르소나</th><th>유효성</th><th>후보 표본</th><th>진입 표본</th><th>평균점수</th><th>점수변화</th><th>해석</th></tr></thead><tbody>" + body + "</tbody></table>"

    def _threshold_table(self, rows: list[dict[str, Any]]) -> str:
        if not rows:
            return "<p>임계값 분석 데이터가 없습니다.</p>"
        body = "".join(
            f"<tr><td>{escape(row['threshold'])}</td><td>{row['candidate_count']}</td><td>{row['entries']}</td><td>{self._pct(row['win_rate'])}</td><td>{row['avg_pnl_pct']:.2f}%</td></tr>"
            for row in rows
        )
        return "<table><thead><tr><th>구간</th><th>후보</th><th>진입</th><th>승률</th><th>평균손익률</th></tr></thead><tbody>" + body + "</tbody></table>"

    def _universe_table(self, rows: list[dict[str, Any]]) -> str:
        if not rows:
            return "<p>후보군 단계 기록이 없습니다.</p>"
        body = "".join(
            f"<tr><td>{escape(row['stage'])}</td><td>{row['checked']}</td><td>{row['passed']}</td><td>{self._pct(row['pass_rate'])}</td><td>{row['avg_score']:.1f}</td></tr>"
            for row in rows
        )
        return "<table><thead><tr><th>단계</th><th>검사</th><th>통과</th><th>통과율</th><th>평균점수</th></tr></thead><tbody>" + body + "</tbody></table>"

    def _persona_inline(self, rows: list[dict[str, Any]]) -> str:
        if not rows:
            return "-"
        return "<br>".join(f"{escape(row['persona'])}: {row['score']:.1f} {escape(row['decision'])}" for row in rows)

    def _krw(self, value: float) -> str:
        return f"{value:,.0f}원"

    def _pct(self, value: float) -> str:
        return f"{value * 100:.2f}%"
