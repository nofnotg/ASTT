from __future__ import annotations

import json
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR


@dataclass(frozen=True)
class ReplayReportCatalog:
    store_dir: Path = REPLAY_STORE_DIR
    capital_krw: float = 500000

    @property
    def experiments_dir(self) -> Path:
        return self.store_dir / "experiments"

    @property
    def reports_dir(self) -> Path:
        return self.store_dir / "reports"

    def build(self) -> dict[str, list[dict] | dict]:
        experiments = self._load_experiments()
        decisions = self._load_frame("decisions.parquet", experiments)
        trades = self._load_frame("paper_trades.parquet", experiments)
        sessions = self._load_frame("session_results.parquet", experiments)
        personas = self._load_frame("persona_scores.parquet", experiments)

        daily = self._aggregate(decisions, trades, sessions, "D")
        weekly = self._aggregate(decisions, trades, sessions, "W-SUN")
        monthly = self._aggregate(decisions, trades, sessions, "M")
        time_windows = self._time_window_summary(trades, decisions)
        persona_validity = self._persona_validity(personas, decisions, trades)
        catalog = {
            "daily": daily,
            "weekly": weekly,
            "monthly": monthly,
            "time_windows": time_windows,
            "persona_validity": persona_validity,
            "macro_persona_context": self._macro_persona_context(),
            "no_entry_summary": self._no_entry_summary(decisions),
            "experiments": self._experiment_rows(experiments),
            "insights": self._build_insights(daily, time_windows),
            "glossary": self._glossary(),
            "report_options": {"capital_krw": self.capital_krw},
        }
        self._write_outputs(catalog)
        return catalog

    def load_or_build(self) -> dict[str, list[dict] | dict]:
        path = self.reports_dir / "catalog" / "replay_report_catalog.json"
        if path.exists():
            catalog = json.loads(path.read_text(encoding="utf-8"))
            if "insights" not in catalog or "time_windows" not in catalog:
                return self.build()
            return catalog
        return self.build()

    def _load_experiments(self) -> list[Path]:
        if not self.experiments_dir.exists():
            return []
        return sorted(path for path in self.experiments_dir.glob("exp_*") if path.is_dir())

    def _load_frame(self, filename: str, experiments: list[Path]) -> pd.DataFrame:
        frames = []
        for exp_dir in experiments:
            path = exp_dir / filename
            if path.exists():
                frame = pd.read_parquet(path)
                frame["experiment_id"] = exp_dir.name
                frames.append(frame)
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    def _aggregate(self, decisions: pd.DataFrame, trades: pd.DataFrame, sessions: pd.DataFrame, freq: str) -> list[dict]:
        if decisions.empty and trades.empty and sessions.empty:
            return []
        rows = []
        for period_start, period_dates in self._period_groups(self._date_index(decisions, trades, sessions), freq):
            date_values = set(period_dates)
            decision_slice = self._filter_dates(decisions, date_values)
            trade_slice = self._filter_dates(trades, date_values)
            session_slice = self._filter_dates(sessions, date_values)
            entries = len(trade_slice)
            wins = int((trade_slice.get("pnl_pct", pd.Series(dtype=float)) > 0).sum()) if entries else 0
            pnl_pct_sum = float(trade_slice.get("pnl_pct", pd.Series(dtype=float)).sum()) if entries else 0.0
            pnl_krw = self._portfolio_pnl_krw(trade_slice)
            day_type = self._period_day_type(period_dates)
            rows.append(
                {
                    "period": period_start,
                    "day_type": day_type,
                    "sessions": int(len(session_slice)),
                    "decisions": int(len(decision_slice)),
                    "entries": int(entries),
                    "wins": wins,
                    "win_rate": wins / entries if entries else 0.0,
                    "total_pnl_pct": pnl_pct_sum,
                    "portfolio_pnl_krw": round(pnl_krw),
                    "portfolio_return_pct": pnl_krw / self.capital_krw * 100 if self.capital_krw else 0.0,
                    "veto_count": int((decision_slice.get("vetoed", pd.Series(dtype=bool)) == True).sum()) if not decision_slice.empty else 0,
                    "weekday_entries": self._day_type_count(trade_slice, "weekday"),
                    "weekend_entries": self._day_type_count(trade_slice, "weekend"),
                    "weekday_pnl_krw": round(self._portfolio_pnl_krw(self._filter_day_type(trade_slice, "weekday"))),
                    "weekend_pnl_krw": round(self._portfolio_pnl_krw(self._filter_day_type(trade_slice, "weekend"))),
                    "experiments": sorted(set(decision_slice.get("experiment_id", pd.Series(dtype=str)).dropna().tolist())),
                }
            )
        return rows

    def _portfolio_pnl_krw(self, trades: pd.DataFrame) -> float:
        if trades.empty or "pnl_pct" not in trades:
            return 0.0
        total = 0.0
        for _, group in trades.groupby(trades["date_kst"].astype(str)):
            allocation = self.capital_krw / len(group) if len(group) else 0.0
            total += float((group["pnl_pct"].astype(float) / 100 * allocation).sum())
        return total

    def _day_type_count(self, frame: pd.DataFrame, day_type: str) -> int:
        if frame.empty:
            return 0
        return int(len(self._filter_day_type(frame, day_type)))

    def _filter_day_type(self, frame: pd.DataFrame, day_type: str) -> pd.DataFrame:
        if frame.empty:
            return pd.DataFrame()
        if "date_kst" not in frame:
            if "day_type" in frame:
                return frame[frame["day_type"].astype(str) == day_type]
            return pd.DataFrame()
        dates = pd.to_datetime(frame["date_kst"])
        target = dates.dt.weekday >= 5 if day_type == "weekend" else dates.dt.weekday < 5
        return frame[target]

    def _period_day_type(self, dates: list[str]) -> str:
        weekdays = sum(1 for item in dates if pd.Timestamp(item).weekday() < 5)
        weekends = len(dates) - weekdays
        if weekdays and weekends:
            return "mixed"
        return "weekend" if weekends else "weekday"

    def _time_window_summary(self, trades: pd.DataFrame, decisions: pd.DataFrame) -> list[dict]:
        if trades.empty and decisions.empty:
            return []
        source = trades if not trades.empty else decisions
        if "entry_time_kst" not in source:
            return []
        frame = source.copy()
        frame["entry_hhmm"] = pd.to_datetime(frame["entry_time_kst"]).dt.strftime("%H:%M")
        frame = frame[frame["entry_hhmm"].notna()]
        if frame.empty:
            return []
        if "day_type" not in frame and "date_kst" in frame:
            frame["day_type"] = pd.to_datetime(frame["date_kst"]).dt.weekday.map(lambda value: "weekend" if value >= 5 else "weekday")
        rows = []
        for (entry_hhmm, day_type), group in frame.groupby(["entry_hhmm", "day_type"], dropna=False):
            entries = len(group) if "pnl_pct" in group else 0
            wins = int((group.get("pnl_pct", pd.Series(dtype=float)) > 0).sum()) if entries else 0
            pnl_krw = self._portfolio_pnl_krw(group) if "pnl_pct" in group else 0.0
            rows.append(
                {
                    "entry_time": str(entry_hhmm),
                    "day_type": str(day_type),
                    "entries": int(entries),
                    "wins": wins,
                    "win_rate": wins / entries if entries else 0.0,
                    "portfolio_pnl_krw": round(pnl_krw),
                    "portfolio_return_pct": pnl_krw / self.capital_krw * 100 if self.capital_krw else 0.0,
                    "avg_pnl_pct": float(group["pnl_pct"].astype(float).mean()) if entries and "pnl_pct" in group else 0.0,
                }
            )
        return sorted(rows, key=lambda row: (row["entry_time"], row["day_type"]))

    def _persona_validity(self, personas: pd.DataFrame, decisions: pd.DataFrame, trades: pd.DataFrame) -> list[dict]:
        if personas.empty:
            return []
        frame = personas.copy()
        frame["persona"] = frame["persona"].map(self._persona_display_name)
        keys = [key for key in ["session_id", "date_kst", "market"] if key in frame.columns]
        if decisions.empty or not all(key in decisions.columns for key in keys):
            frame["final_decision"] = ""
            frame["entered"] = False
        else:
            decision_cols = keys + [col for col in ["final_decision", "final_score", "vetoed"] if col in decisions.columns]
            frame = frame.merge(decisions[decision_cols], on=keys, how="left")
            frame["entered"] = frame.get("final_decision", pd.Series(dtype=str)).astype(str).eq("ENTER")
        if trades.empty or not all(key in trades.columns for key in keys):
            frame["pnl_pct"] = pd.NA
        else:
            trade_cols = keys + [col for col in ["pnl_pct", "exit_reason", "ambiguous_fill"] if col in trades.columns]
            frame = frame.merge(trades[trade_cols], on=keys, how="left")
        rows = []
        for persona, group in frame.groupby("persona", sort=True):
            threshold = self._persona_threshold(persona)
            trade_rows = group[group["pnl_pct"].notna()] if "pnl_pct" in group else pd.DataFrame()
            high = group[group["score"].astype(float) >= threshold] if "score" in group else pd.DataFrame()
            high_trades = high[high["pnl_pct"].notna()] if not high.empty and "pnl_pct" in high else pd.DataFrame()
            low = group[group["score"].astype(float) < threshold] if "score" in group else pd.DataFrame()
            low_trades = low[low["pnl_pct"].notna()] if not low.empty and "pnl_pct" in low else pd.DataFrame()
            score_entry_corr = self._corr(group, "score", "entered")
            score_pnl_corr = self._corr(trade_rows, "score", "pnl_pct")
            high_win_rate = self._win_rate(high_trades)
            low_win_rate = self._win_rate(low_trades)
            validity = self._validity_label(len(group), len(trade_rows), score_entry_corr, score_pnl_corr, high_win_rate, low_win_rate)
            validity_pct = self._validity_pct(len(group), len(trade_rows), score_entry_corr, score_pnl_corr, high_win_rate, low_win_rate)
            rows.append(
                {
                    "persona": persona,
                    "role": self._persona_role(persona),
                    "samples": int(len(group)),
                    "trade_samples": int(len(trade_rows)),
                    "avg_score": float(group["score"].astype(float).mean()) if "score" in group and len(group) else 0.0,
                    "pass_threshold": threshold,
                    "pass_count": int(group["decision"].astype(str).eq("PASS").sum()) if "decision" in group else 0,
                    "watch_count": int(group["decision"].astype(str).eq("WATCH").sum()) if "decision" in group else 0,
                    "reject_count": int(group["decision"].astype(str).eq("REJECT").sum()) if "decision" in group else 0,
                    "veto_count": int(group.get("veto", pd.Series(dtype=bool)).fillna(False).astype(bool).sum()),
                    "high_score_samples": int(len(high)),
                    "high_score_trade_samples": int(len(high_trades)),
                    "high_score_win_rate": high_win_rate,
                    "low_score_win_rate": low_win_rate,
                    "score_entry_corr": score_entry_corr,
                    "score_pnl_corr": score_pnl_corr,
                    "validity_pct": validity_pct,
                    "validity": validity,
                    "review_note": self._persona_review_note(persona, validity),
                }
            )
        return rows

    def _no_entry_summary(self, decisions: pd.DataFrame) -> list[dict]:
        if decisions.empty or "no_entry_reason" not in decisions:
            return []
        frame = decisions[decisions.get("final_decision", pd.Series(dtype=str)).astype(str) != "ENTER"].copy()
        if frame.empty:
            return []
        frame["no_entry_reason"] = frame["no_entry_reason"].fillna("reason unavailable").replace("", "reason unavailable")
        frame = frame[frame["no_entry_reason"] != "reason unavailable"]
        if frame.empty:
            return []
        rows = []
        for reason, group in frame.groupby("no_entry_reason", sort=True):
            rows.append(
                {
                    "reason": reason,
                    "count": int(len(group)),
                    "share": len(group) / len(frame) if len(frame) else 0.0,
                    "example_market": str(group.iloc[0].get("market", "")),
                    "example_date": str(group.iloc[0].get("date_kst", "")),
                }
            )
        return sorted(rows, key=lambda row: row["count"], reverse=True)

    def _persona_display_name(self, value: Any) -> str:
        name = str(value)
        if name in {"留ㅺ린", "Maggie"}:
            return "매기"
        return name

    def _persona_threshold(self, persona: str) -> float:
        return {"Mr.K": 65.0, "매기": 85.0, "Rezo": 80.0, "CostA": 60.0, "Iris": 80.0}.get(persona, 80.0)

    def _persona_role(self, persona: str) -> str:
        return {
            "Mr.K": "시장 국면과 큰 방향성 판단",
            "매기": "가격 구조, 매물대, 돌파 여지 판단",
            "Rezo": "거래량, VWAP, 수급 proxy 판단",
            "CostA": "분할매수/노출 규모와 탈출 가능성 판단",
            "Iris": "위험 차단과 veto 판단",
        }.get(persona, "보조 판단")

    def _win_rate(self, frame: pd.DataFrame) -> float:
        if frame.empty or "pnl_pct" not in frame:
            return 0.0
        return float((frame["pnl_pct"].astype(float) > 0).mean())

    def _corr(self, frame: pd.DataFrame, left: str, right: str) -> float:
        if frame.empty or left not in frame or right not in frame or len(frame) < 3:
            return 0.0
        data = frame[[left, right]].copy()
        data[left] = pd.to_numeric(data[left], errors="coerce")
        if data[right].dtype == bool:
            data[right] = data[right].astype(int)
        else:
            data[right] = pd.to_numeric(data[right], errors="coerce")
        data = data.dropna()
        if len(data) < 3 or data[left].nunique() < 2 or data[right].nunique() < 2:
            return 0.0
        return float(data[left].corr(data[right]))

    def _validity_label(
        self,
        samples: int,
        trade_samples: int,
        score_entry_corr: float,
        score_pnl_corr: float,
        high_win_rate: float,
        low_win_rate: float,
    ) -> str:
        if samples < 30 or trade_samples < 20:
            return "검증 부족"
        if score_pnl_corr >= 0.15 and high_win_rate >= low_win_rate:
            return "유효성 긍정"
        if score_pnl_corr <= -0.15:
            return "역효과 의심"
        if score_entry_corr >= 0.20:
            return "진입 선별에는 유효"
        return "중립/추가 검증"

    def _validity_pct(
        self,
        samples: int,
        trade_samples: int,
        score_entry_corr: float,
        score_pnl_corr: float,
        high_win_rate: float,
        low_win_rate: float,
    ) -> float:
        sample_score = min(trade_samples / 100, 1.0) * 25
        entry_score = max(min(score_entry_corr, 1.0), -1.0) * 20
        pnl_score = max(min(score_pnl_corr, 1.0), -1.0) * 30
        lift_score = max(min(high_win_rate - low_win_rate, 1.0), -1.0) * 25
        raw = 50 + sample_score + entry_score + pnl_score + lift_score
        if samples < 30 or trade_samples < 20:
            raw = min(raw, 59)
        return round(max(0, min(100, raw)), 2)

    def _persona_review_note(self, persona: str, validity: str) -> str:
        base = {
            "Mr.K": "거시/시장 국면을 가장 직접적으로 받아야 하는 페르소나입니다.",
            "매기": "차트 구조가 실제 09:00 돌파 성공과 이어지는지 봐야 합니다.",
            "Rezo": "거래량 급증이 진짜 수급인지 뉴스성 일시 급등인지 분리해야 합니다.",
            "CostA": "수익 예측보다 손실 복구 가능성과 노출 제한이 타당한지 봐야 합니다.",
            "Iris": "막은 거래가 실제로 나쁜 거래였는지 확인해야 합니다.",
        }.get(persona, "보조 판단의 실제 기여도를 확인해야 합니다.")
        return f"{base} 현재 판정: {validity}."

    def _macro_persona_context(self) -> list[dict]:
        return [
            {
                "persona": "Mr.K",
                "macro_link": "미국장 마감, BTC 전체 추세, 달러/금리, 국내 위험선호 변화가 시장 국면 점수에 반영되어야 합니다.",
                "current_gap": "현재는 캔들 기반 regime만 사용하므로 거시/국내정세는 직접 입력되지 않습니다.",
                "validation_rule": "거시 리스크가 큰 날 Mr.K 점수가 낮아지고, 진입 억제와 손실 감소가 함께 나타나는지 검증합니다.",
            },
            {
                "persona": "매기",
                "macro_link": "정세 이벤트 자체보다 그 결과로 만들어진 가격 구조와 돌파 여지를 봅니다.",
                "current_gap": "뉴스 원인은 모르고 차트 구조만 봅니다.",
                "validation_rule": "매기 고점수 후보가 저점수 후보보다 09:00 이후 목표가 도달률이 높은지 검증합니다.",
            },
            {
                "persona": "Rezo",
                "macro_link": "정책/규제/상장/악재 뉴스는 거래량 폭증으로 나타날 수 있어 Rezo에 강하게 영향을 줍니다.",
                "current_gap": "과거 호가창과 실제 체결 방향을 완전 복원하지 못해 proxy 판단입니다.",
                "validation_rule": "Rezo 고점수 후보가 진입 후 추세 지속성과 승률을 실제로 높이는지 검증합니다.",
            },
            {
                "persona": "CostA",
                "macro_link": "급락장, 변동성 확대, 유동성 축소 때 분할매수 노출 한도가 중요해집니다.",
                "current_gap": "현재는 거시 변동성별 노출 조절이 세분화되어 있지 않습니다.",
                "validation_rule": "손실 구간에서 CostA 기준이 손실 확대를 줄였는지 검증합니다.",
            },
            {
                "persona": "Iris",
                "macro_link": "규제 뉴스, BTC 급락, 데이터 품질 저하, 과도한 스프레드 같은 위험을 최종 차단해야 합니다.",
                "current_gap": "국내정세/거시 뉴스 veto는 아직 자동화되어 있지 않습니다.",
                "validation_rule": "Iris가 막은 거래의 평균 성과가 실제 진입 거래보다 낮아야 veto가 타당합니다.",
            },
        ]

    def _date_index(self, *frames: pd.DataFrame) -> list[str]:
        values: set[str] = set()
        for frame in frames:
            if not frame.empty and "date_kst" in frame:
                values.update(str(item) for item in frame["date_kst"].dropna().tolist())
        return sorted(values)

    def _period_groups(self, dates: list[str], freq: str) -> list[tuple[str, list[str]]]:
        if not dates:
            return []
        frame = pd.DataFrame({"date_kst": pd.to_datetime(dates)})
        frame["period"] = frame["date_kst"].dt.to_period(freq).dt.start_time.dt.date.astype(str)
        return [(period, group["date_kst"].dt.date.astype(str).tolist()) for period, group in frame.groupby("period", sort=True)]

    def _filter_dates(self, frame: pd.DataFrame, dates: set[str]) -> pd.DataFrame:
        if frame.empty or "date_kst" not in frame:
            return pd.DataFrame()
        return frame[frame["date_kst"].astype(str).isin(dates)]

    def _experiment_rows(self, experiments: list[Path]) -> list[dict]:
        rows = []
        for exp_dir in experiments:
            metrics_path = exp_dir / "metrics.json"
            report_path = exp_dir / "report.md"
            config_path = exp_dir / "config.json"
            metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
            config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
            rows.append({"experiment_id": exp_dir.name, "report_path": str(report_path) if report_path.exists() else "", **config, **metrics})
        return rows

    def _build_insights(self, daily: list[dict], time_windows: list[dict]) -> dict:
        total_days = len(daily)
        total_sessions = sum(int(row.get("sessions", 0)) for row in daily)
        total_decisions = sum(int(row.get("decisions", 0)) for row in daily)
        total_entries = sum(int(row.get("entries", 0)) for row in daily)
        total_wins = sum(int(row.get("wins", 0)) for row in daily)
        total_veto = sum(int(row.get("veto_count", 0)) for row in daily)
        total_pnl_krw = sum(float(row.get("portfolio_pnl_krw", 0.0)) for row in daily)
        win_rate = total_wins / total_entries if total_entries else 0.0
        entry_rate = total_entries / total_decisions if total_decisions else 0.0
        veto_rate = total_veto / total_decisions if total_decisions else 0.0
        best_day = max(daily, key=lambda row: float(row.get("portfolio_pnl_krw", 0.0)), default=None)
        worst_day = min(daily, key=lambda row: float(row.get("portfolio_pnl_krw", 0.0)), default=None)
        profitable_days = sum(1 for row in daily if float(row.get("portfolio_pnl_krw", 0.0)) > 0)
        losing_days = sum(1 for row in daily if float(row.get("portfolio_pnl_krw", 0.0)) < 0)
        flat_days = max(0, total_days - profitable_days - losing_days)
        sample_quality = "LOW"
        if total_entries >= 100 and total_days >= 30:
            sample_quality = "ACCEPTABLE"
        if total_entries >= 300 and total_days >= 90:
            sample_quality = "GOOD"

        best_window = max(time_windows, key=lambda row: float(row.get("portfolio_pnl_krw", 0.0)), default=None)
        weekday_pnl = sum(float(row.get("weekday_pnl_krw", 0.0)) for row in daily)
        weekend_pnl = sum(float(row.get("weekend_pnl_krw", 0.0)) for row in daily)
        weekday_entries = sum(int(row.get("weekday_entries", 0)) for row in daily)
        weekend_entries = sum(int(row.get("weekend_entries", 0)) for row in daily)

        potential = [
            f"50만원을 매일 배정하는 보수적 가정에서 누적 손익은 {total_pnl_krw:,.0f}원입니다.",
            f"실제 진입은 {total_entries}건, 승리 거래는 {total_wins}건이며 승률은 {win_rate:.2%}입니다.",
            f"평일 진입 {weekday_entries}건의 손익은 {weekday_pnl:,.0f}원, 주말 진입 {weekend_entries}건의 손익은 {weekend_pnl:,.0f}원입니다.",
        ]
        if best_day:
            potential.append(f"가장 좋은 일자는 {best_day['period']}이며 일간 손익은 {float(best_day.get('portfolio_pnl_krw', 0.0)):,.0f}원입니다.")
        if best_window:
            potential.append(f"현재 표본에서 가장 좋은 진입 시간 후보는 {best_window['entry_time']} {best_window['day_type']} 구간입니다. 손익은 {float(best_window.get('portfolio_pnl_krw', 0.0)):,.0f}원입니다.")

        limits = [
            f"표본 품질은 {sample_quality}입니다. 최소 90일, 진입 100건 이상이 되기 전까지는 설정 변경 근거로 쓰기 어렵습니다.",
            "현재 체결 모델은 분봉 기반 PAPER 체결입니다. 같은 분봉에서 익절과 손절이 동시에 닿으면 보수적으로 손절을 먼저 적용합니다.",
            "과거 호가창, 실제 주문 대기열, 체결 지연은 완전 복원할 수 없습니다. Rezo는 리플레이에서 proxy 모드로 해석해야 합니다.",
            "거시경제와 국내정세는 자동 데이터 소스가 아직 붙지 않았습니다. 리포트에는 검토 필요 가설로만 표시합니다.",
        ]
        if worst_day:
            limits.append(f"가장 손실이 큰 일자는 {worst_day['period']}이며 일간 손익은 {float(worst_day.get('portfolio_pnl_krw', 0.0)):,.0f}원입니다.")

        developments = [
            "08:50~08:59 분석과 09:00 진입을 분리했습니다. 판단 로직에는 09:00 이후 캔들이 들어가지 않게 했습니다.",
            "일별, 주간, 월간 통계를 같은 HTML 문서에서 볼 수 있게 했습니다.",
            "평일과 주말을 분리해 진입 수, 승률, 원화 손익을 비교할 수 있게 했습니다.",
            "09:00 외 시간대 실험을 위해 batch-windows 명령을 추가했습니다.",
            "메인 앱 프론트엔드의 Replay Reports 카테고리에서 HTML 리포트 파일을 확인할 수 있습니다.",
        ]
        improvement_insights = [
            "우선 3개월 전체를 상위 20~50개 KRW 마켓으로 돌려 진입 100건 이상을 확보해야 합니다.",
            "09:00 후보가 유효하면 01:00, 05:00, 13:00, 17:00, 21:00 후보와 같은 조건으로 비교해야 합니다.",
            "주말 성과가 낮으면 주말에는 Rezo 기준을 올리거나 Iris veto를 강화하는 후보 패치를 만들어야 합니다.",
            "손실일에는 매기 점수, Rezo proxy 점수, Iris veto 사유를 드릴다운해 반복 실패 패턴을 분리해야 합니다.",
            "수익률이 양수라도 최대낙폭, 연속 손실, 진입 수 급감이 나쁘면 APPROVED로 승격하지 않아야 합니다.",
        ]
        macro_context = [
            "[검토 필요] KST 09:00은 한국 주식시장 개장과 겹치므로 국내 위험선호 변화가 KRW 코인 거래대금에 영향을 줄 수 있습니다.",
            "[검토 필요] KST 오전은 미국 장 마감 이후 구간과 가까워 전일 미국 증시, 달러, 비트코인 뉴스의 잔여 영향이 나타날 수 있습니다.",
            "[검토 필요] 금리, 환율, 규제 뉴스, 국내 정치 이벤트는 자동 수집원이 연결되기 전까지 리포트의 확정 원인으로 쓰지 않습니다.",
        ]
        return {
            "summary": {
                "sample_quality": sample_quality,
                "capital_krw": self.capital_krw,
                "total_days": total_days,
                "total_sessions": total_sessions,
                "total_decisions": total_decisions,
                "total_entries": total_entries,
                "total_wins": total_wins,
                "win_rate": win_rate,
                "entry_rate": entry_rate,
                "veto_rate": veto_rate,
                "portfolio_pnl_krw": round(total_pnl_krw),
                "portfolio_return_pct": total_pnl_krw / self.capital_krw * 100 if self.capital_krw else 0.0,
                "profitable_days": profitable_days,
                "losing_days": losing_days,
                "flat_days": flat_days,
                "weekday_entries": weekday_entries,
                "weekend_entries": weekend_entries,
                "weekday_pnl_krw": round(weekday_pnl),
                "weekend_pnl_krw": round(weekend_pnl),
                "best_day": best_day,
                "worst_day": worst_day,
                "best_time_window": best_window,
            },
            "potential": potential,
            "limits": limits,
            "developments": developments,
            "improvement_insights": improvement_insights,
            "macro_context": macro_context,
        }

    def _glossary(self) -> list[dict[str, str]]:
        return [
            {"term": "PAPER 체결", "meaning": "실제 주문을 넣지 않고 과거 가격으로 가상 매수와 매도를 기록하는 방식입니다."},
            {"term": "승률", "meaning": "수익으로 끝난 거래 수를 전체 진입 거래 수로 나눈 비율입니다."},
            {"term": "PnL", "meaning": "손익입니다. 이 리포트에서는 원화 기준 이익 또는 손실로 함께 표시합니다."},
            {"term": "MDD", "meaning": "최고점 대비 가장 크게 빠진 손실 폭입니다. 돈이 얼마나 흔들렸는지를 보는 지표입니다."},
            {"term": "Lookahead bias", "meaning": "그 시점에는 알 수 없었던 미래 데이터를 판단에 섞는 오류입니다."},
            {"term": "Veto", "meaning": "위험 조건이 감지되어 진입을 막는 안전장치입니다."},
            {"term": "Proxy", "meaning": "완전한 과거 데이터가 없을 때 비슷한 지표로 대신 추정하는 방식입니다."},
        ]

    def _write_outputs(self, catalog: dict[str, list[dict] | dict]) -> None:
        out_dir = self.reports_dir / "catalog"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "replay_report_catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
        for key in ["daily", "weekly", "monthly", "time_windows", "persona_validity"]:
            self._write_markdown(out_dir / f"{key}_replay_report.md", key, catalog[key])
        self._write_insight_markdown(out_dir / "replay_insight_report.md", catalog["insights"])
        self._write_html_report(out_dir / "replay_report.html", catalog)

    def _write_markdown(self, path: Path, title: str, rows: list[dict]) -> None:
        lines = [f"# Replay {title.replace('_', ' ').title()} Report", ""]
        if not rows:
            lines.append("No replay data available.")
        else:
            headers = list(rows[0].keys())
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("|" + "|".join("---" for _ in headers) + "|")
            for row in rows:
                lines.append("| " + " | ".join(self._format_markdown_value(row.get(key)) for key in headers) + " |")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _format_markdown_value(self, value: Any) -> str:
        if isinstance(value, float):
            return f"{value:.4f}"
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def _write_insight_markdown(self, path: Path, insights: dict) -> None:
        summary = insights.get("summary", {})
        lines = [
            "# Replay Lab Insight Report",
            "",
            "## 요약",
            f"- 기준 자금: {float(summary.get('capital_krw', self.capital_krw)):,.0f}원",
            f"- 표본 품질: {summary.get('sample_quality', 'UNKNOWN')}",
            f"- 전체 일수: {summary.get('total_days', 0)}",
            f"- 실제 진입: {summary.get('total_entries', 0)}건",
            f"- 승률: {float(summary.get('win_rate', 0.0)):.2%}",
            f"- 원화 손익: {float(summary.get('portfolio_pnl_krw', 0.0)):,.0f}원",
            "",
        ]
        for title, key in [
            ("앱의 가능성", "potential"),
            ("현재 한계", "limits"),
            ("디벨롭한 내용", "developments"),
            ("추가 개선 인사이트", "improvement_insights"),
            ("거시경제/국내정세 인사이트", "macro_context"),
        ]:
            lines.extend([f"## {title}", *[f"- {item}" for item in insights.get(key, [])], ""])
        lines.extend(["## 페르소나 유효성 검증"])
        for row in insights.get("persona_validity", []):
            lines.append(f"- {row}")
        lines.append("")
        lines.extend(
            [
                "## 적용 원칙",
                "- 이 리포트는 연구용 산출물이며 실전 설정을 자동 변경하지 않습니다.",
                "- config patch는 DRAFT -> BACKTESTED -> SHADOW_TESTED -> APPROVED 이후에만 메인 앱 import 대상이 됩니다.",
            ]
        )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_html_report(self, path: Path, catalog: dict[str, list[dict] | dict]) -> None:
        insights = catalog.get("insights", {})
        summary = insights.get("summary", {})
        html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ASTT Replay Lab 투자 리포트</title>
  <style>
    :root {{ --bg:#f5f7fb; --panel:#fff; --text:#171717; --muted:#667085; --border:#d9dee7; --accent:#0f766e; --danger:#b42318; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif; line-height:1.55; }}
    main {{ max-width:1180px; margin:0 auto; padding:36px 24px 64px; }}
    header {{ margin-bottom:26px; }}
    h1 {{ margin:8px 0 8px; font-size:34px; line-height:1.2; letter-spacing:0; }}
    h2 {{ margin:0 0 14px; font-size:22px; letter-spacing:0; }}
    p {{ margin:0; color:var(--muted); }}
    section {{ background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:22px; margin:16px 0; }}
    .grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }}
    .metric {{ border:1px solid var(--border); border-radius:8px; padding:14px; background:#fbfcfe; }}
    .metric span {{ display:block; color:var(--muted); font-size:12px; }}
    .metric strong {{ display:block; margin-top:6px; font-size:22px; word-break:keep-all; }}
    .pill {{ display:inline-flex; border-radius:999px; padding:5px 10px; background:#e6f4f1; color:var(--accent); font-weight:700; font-size:12px; }}
    ul {{ margin:0; padding-left:20px; }}
    li {{ margin:7px 0; }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th,td {{ padding:9px 10px; border-bottom:1px solid var(--border); text-align:right; white-space:nowrap; }}
    th:first-child,td:first-child {{ text-align:left; }}
    th {{ color:var(--muted); background:#f8fafc; font-weight:700; }}
    .table-wrap {{ overflow-x:auto; }}
    .note {{ color:var(--muted); font-size:13px; margin-top:12px; }}
    .warn {{ color:var(--danger); font-weight:700; }}
    @media (max-width:820px) {{ .grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} main {{ padding:24px 14px 48px; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <div class="pill">Replay Lab Sidecar</div>
    <h1>ASTT Replay Lab 투자 리포트</h1>
    <p>08:50~08:59 분석 후 09:00 진입하는 초단타 전략을 50만원 기준 원화 손익으로 정리한 연구용 HTML 문서입니다.</p>
  </header>
  <section>
    <h2>요약</h2>
    <div class="grid">
      {self._metric("기준 자금", self._krw(summary.get("capital_krw", self.capital_krw)))}
      {self._metric("표본 품질", summary.get("sample_quality", "UNKNOWN"))}
      {self._metric("전체 일수", summary.get("total_days", 0))}
      {self._metric("실제 진입", f"{summary.get('total_entries', 0)}건")}
      {self._metric("승률", self._pct(summary.get("win_rate", 0.0)))}
      {self._metric("진입률", self._pct(summary.get("entry_rate", 0.0)))}
      {self._metric("누적 손익", self._krw(summary.get("portfolio_pnl_krw", 0)))}
      {self._metric("수익률", self._pct(summary.get("portfolio_return_pct", 0.0) / 100))}
    </div>
    <p class="note">원화 손익은 같은 날짜에 여러 진입이 있으면 50만원을 해당 거래 수로 나눠 배정한 보수적 연구 지표입니다.</p>
  </section>
  {self._list_section("앱의 가능성", insights.get("potential", []))}
  {self._list_section("현재 한계", insights.get("limits", []))}
  {self._list_section("디벨롭한 내용", insights.get("developments", []))}
  {self._list_section("추가 개선 인사이트", insights.get("improvement_insights", []))}
  {self._list_section("거시경제/국내정세 인사이트", insights.get("macro_context", []))}
  {self._table_section("페르소나 유효성 검증", catalog.get("persona_validity", []))}
  {self._table_section("거시/국내정세와 페르소나 연결 검토", catalog.get("macro_persona_context", []))}
  {self._table_section("미진입 사유 요약", catalog.get("no_entry_summary", []))}
  {self._table_section("시간대별 후보 비교", catalog.get("time_windows", []))}
  {self._table_section("일별 리포트", catalog.get("daily", []))}
  {self._table_section("주간 통계", catalog.get("weekly", []))}
  {self._table_section("월간 통계", catalog.get("monthly", []))}
  {self._glossary_section(catalog.get("glossary", []))}
  <section>
    <h2>적용 원칙</h2>
    <ul>
      <li>이 리포트는 연구용 산출물이며 실전 설정을 자동 변경하지 않습니다.</li>
      <li>APPROVED 상태의 산출물만 메인 앱 import 대상이 됩니다.</li>
      <li class="warn">표본이 부족하거나 거시/정세 원인이 검토 필요 상태이면 실거래 근거로 쓰지 않습니다.</li>
    </ul>
  </section>
</main>
</body>
</html>"""
        path.write_text(html, encoding="utf-8")

    def _metric(self, label: str, value: Any) -> str:
        return f"<div class=\"metric\"><span>{escape(str(label))}</span><strong>{escape(str(value))}</strong></div>"

    def _list_section(self, title: str, items: list[str]) -> str:
        body = "".join(f"<li>{escape(str(item))}</li>" for item in items) or "<li>데이터가 아직 없습니다.</li>"
        return f"<section><h2>{escape(title)}</h2><ul>{body}</ul></section>"

    def _table_section(self, title: str, rows: list[dict]) -> str:
        if not rows:
            return f"<section><h2>{escape(title)}</h2><p>데이터가 아직 없습니다.</p></section>"
        headers = [key for key in rows[0].keys() if key != "experiments"]
        header_html = "".join(f"<th>{escape(self._header_label(key))}</th>" for key in headers)
        row_html = ""
        for row in rows:
            row_html += "<tr>" + "".join(f"<td>{escape(self._display_value(key, row.get(key)))}</td>" for key in headers) + "</tr>"
        return f"<section><h2>{escape(title)}</h2><div class=\"table-wrap\"><table><thead><tr>{header_html}</tr></thead><tbody>{row_html}</tbody></table></div></section>"

    def _glossary_section(self, rows: list[dict]) -> str:
        items = "".join(f"<li><strong>{escape(row['term'])}</strong>: {escape(row['meaning'])}</li>" for row in rows)
        return f"<section><h2>쉬운 용어 해설</h2><ul>{items}</ul></section>"

    def _display_value(self, key: str, value: Any) -> str:
        if value is None:
            return ""
        if key.endswith("_krw") or key in {"portfolio_pnl_krw", "weekday_pnl_krw", "weekend_pnl_krw"}:
            return self._krw(value)
        if key.endswith("_corr"):
            return f"{float(value):.3f}"
        if key.endswith("_rate") or key.endswith("_return_pct") or key.endswith("_pnl_pct"):
            return f"{float(value):.2f}%" if key.endswith("_pct") else self._pct(value)
        if isinstance(value, float):
            return f"{value:.4f}"
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def _header_label(self, key: str) -> str:
        labels = {
            "period": "기간",
            "day_type": "구분",
            "sessions": "세션",
            "decisions": "판단",
            "entries": "진입",
            "wins": "승리",
            "win_rate": "승률",
            "total_pnl_pct": "거래손익합",
            "portfolio_pnl_krw": "원화손익",
            "portfolio_return_pct": "수익률",
            "veto_count": "Veto",
            "weekday_entries": "평일진입",
            "weekend_entries": "주말진입",
            "weekday_pnl_krw": "평일손익",
            "weekend_pnl_krw": "주말손익",
            "entry_time": "진입시간",
            "avg_pnl_pct": "평균손익",
            "persona": "페르소나",
            "role": "역할",
            "samples": "표본",
            "trade_samples": "거래표본",
            "avg_score": "평균점수",
            "pass_threshold": "통과기준",
            "pass_count": "PASS",
            "watch_count": "WATCH",
            "reject_count": "REJECT",
            "high_score_samples": "고점수표본",
            "high_score_trade_samples": "고점수거래",
            "high_score_win_rate": "고점수승률",
            "low_score_win_rate": "저점수승률",
            "score_entry_corr": "점수-진입상관",
            "score_pnl_corr": "점수-손익상관",
            "validity_pct": "유효성%",
            "validity": "유효성 판정",
            "review_note": "검토 메모",
            "macro_link": "거시/정세 연결",
            "current_gap": "현재 한계",
            "validation_rule": "검증 기준",
            "reason": "미진입 사유",
            "count": "건수",
            "share": "비중",
            "example_market": "예시마켓",
            "example_date": "예시일자",
        }
        return labels.get(key, key)

    def _pct(self, value: Any) -> str:
        return f"{float(value):.2%}"

    def _krw(self, value: Any) -> str:
        return f"{float(value):,.0f}원"
