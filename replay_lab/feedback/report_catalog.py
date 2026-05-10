from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR


@dataclass(frozen=True)
class ReplayReportCatalog:
    store_dir: Path = REPLAY_STORE_DIR

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

        daily = self._aggregate(decisions, trades, sessions, "D")
        weekly = self._aggregate(decisions, trades, sessions, "W-SUN")
        monthly = self._aggregate(decisions, trades, sessions, "M")
        catalog = {
            "daily": daily,
            "weekly": weekly,
            "monthly": monthly,
            "experiments": self._experiment_rows(experiments),
            "insights": self._build_insights(daily, weekly, monthly),
        }
        self._write_outputs(catalog)
        return catalog

    def load_or_build(self) -> dict[str, list[dict] | dict]:
        path = self.reports_dir / "catalog" / "replay_report_catalog.json"
        if path.exists():
            catalog = json.loads(path.read_text(encoding="utf-8"))
            if "insights" not in catalog:
                catalog["insights"] = self._build_insights(catalog.get("daily", []), catalog.get("weekly", []), catalog.get("monthly", []))
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

        base_dates = self._date_index(decisions, trades, sessions)
        rows = []
        for period_start, period_dates in self._period_groups(base_dates, freq):
            date_values = set(period_dates)
            decision_slice = self._filter_dates(decisions, date_values)
            trade_slice = self._filter_dates(trades, date_values)
            session_slice = self._filter_dates(sessions, date_values)
            entries = len(trade_slice)
            wins = int((trade_slice.get("pnl_pct", pd.Series(dtype=float)) > 0).sum()) if entries else 0
            pnl = float(trade_slice.get("pnl_pct", pd.Series(dtype=float)).sum()) if entries else 0.0
            rows.append(
                {
                    "period": period_start,
                    "sessions": int(len(session_slice)),
                    "decisions": int(len(decision_slice)),
                    "entries": int(entries),
                    "wins": wins,
                    "win_rate": wins / entries if entries else 0.0,
                    "total_pnl_pct": pnl,
                    "veto_count": int((decision_slice.get("vetoed", pd.Series(dtype=bool)) == True).sum()) if not decision_slice.empty else 0,
                    "experiments": sorted(set(decision_slice.get("experiment_id", pd.Series(dtype=str)).dropna().tolist())),
                }
            )
        return rows

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
            metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
            rows.append({"experiment_id": exp_dir.name, "report_path": str(report_path) if report_path.exists() else "", **metrics})
        return rows

    def _build_insights(self, daily: list[dict], weekly: list[dict], monthly: list[dict]) -> dict:
        total_sessions = sum(int(row.get("sessions", 0)) for row in daily)
        total_decisions = sum(int(row.get("decisions", 0)) for row in daily)
        total_entries = sum(int(row.get("entries", 0)) for row in daily)
        total_wins = sum(int(row.get("wins", 0)) for row in daily)
        total_veto = sum(int(row.get("veto_count", 0)) for row in daily)
        total_pnl = sum(float(row.get("total_pnl_pct", 0.0)) for row in daily)
        win_rate = total_wins / total_entries if total_entries else 0.0
        entry_rate = total_entries / total_decisions if total_decisions else 0.0
        veto_rate = total_veto / total_decisions if total_decisions else 0.0
        best_day = max(daily, key=lambda row: float(row.get("total_pnl_pct", 0.0)), default=None)
        worst_day = min(daily, key=lambda row: float(row.get("total_pnl_pct", 0.0)), default=None)
        profitable_days = sum(1 for row in daily if float(row.get("total_pnl_pct", 0.0)) > 0)
        losing_days = sum(1 for row in daily if float(row.get("total_pnl_pct", 0.0)) < 0)
        flat_days = max(0, len(daily) - profitable_days - losing_days)
        sample_quality = "LOW"
        if total_entries >= 100 and len(daily) >= 30:
            sample_quality = "ACCEPTABLE"
        if total_entries >= 300 and len(daily) >= 90:
            sample_quality = "GOOD"

        potential = []
        if total_pnl > 0:
            potential.append(f"현재 누적 리플레이 PnL은 {total_pnl:.2f}%로 양수이며, 전략 후보군이 완전히 무작위는 아닐 가능성을 보여준다.")
        else:
            potential.append(f"현재 누적 리플레이 PnL은 {total_pnl:.2f}%로 양수가 아니므로, 수익성보다 필터/리스크 검증 단계로 해석해야 한다.")
        if total_entries:
            potential.append(f"진입 {total_entries}건 중 {total_wins}건이 수익으로 종료되어 승률은 {win_rate:.2%}이다.")
        if best_day:
            potential.append(f"가장 좋은 일자는 {best_day['period']}이며 일간 PnL은 {float(best_day.get('total_pnl_pct', 0.0)):.2f}%이다.")

        limits = [
            f"표본 품질은 {sample_quality}이다. 현재 진입 수 {total_entries}건, 일수 {len(daily)}일로 90일/100진입 기준에는 아직 부족하다.",
            "현재 리플레이는 1분봉과 proxy 체결을 기반으로 하므로 과거 호가창, 실제 체결 순서, 초봉 기반 익절/손절 순서를 완전히 복원하지 못한다.",
            "동일 날짜가 여러 experiment에 포함되면 연구 실행 기준으로 누적되므로, 운영 성과처럼 해석하면 안 된다.",
        ]
        if worst_day:
            limits.append(f"가장 나쁜 일자는 {worst_day['period']}이며 일간 PnL은 {float(worst_day.get('total_pnl_pct', 0.0)):.2f}%이다.")

        developments = [
            "Replay Lab sidecar가 메인 실시간 경로와 분리되어 public historical data, local cache, PAPER replay, report export 구조로 동작한다.",
            "날짜별/주간/월간 catalog가 생성되어 리플레이 결과를 프론트엔드에서 읽을 수 있다.",
            f"현재 catalog는 sessions {total_sessions}건, decisions {total_decisions}건, entries {total_entries}건을 포함한다.",
            f"Iris veto는 {total_veto}회 발생했고 veto rate는 {veto_rate:.2%}이다.",
        ]

        improvement_insights = [
            "다음 실험은 30일 이상, 상위 20~50개 시장으로 확장해 최소 100건 이상의 진입 표본을 확보한다.",
            "동일 날짜 중복 experiment를 제외하는 latest-only 또는 selected-experiment 필터를 추가해 운영 해석용 통계를 분리한다.",
            "Rezo proxy 한계를 줄이기 위해 최근 7일 구간에는 tick/초봉 보강 리플레이를 별도 실행한다.",
            "일간 손실이 집중된 날짜를 대상으로 매기 자리 판단, Rezo 수급 점수, Iris veto 미발동 사유를 drill-down한다.",
            "총 PnL이 양수라도 MDD, 연속 손실, 진입 수 감소를 함께 보지 않으면 config patch를 승인하지 않는다.",
        ]

        return {
            "summary": {
                "sample_quality": sample_quality,
                "total_days": len(daily),
                "total_sessions": total_sessions,
                "total_decisions": total_decisions,
                "total_entries": total_entries,
                "total_wins": total_wins,
                "win_rate": win_rate,
                "entry_rate": entry_rate,
                "veto_rate": veto_rate,
                "total_pnl_pct": total_pnl,
                "profitable_days": profitable_days,
                "losing_days": losing_days,
                "flat_days": flat_days,
                "best_day": best_day,
                "worst_day": worst_day,
            },
            "potential": potential,
            "limits": limits,
            "developments": developments,
            "improvement_insights": improvement_insights,
        }

    def _write_outputs(self, catalog: dict[str, list[dict] | dict]) -> None:
        out_dir = self.reports_dir / "catalog"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "replay_report_catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
        for key in ["daily", "weekly", "monthly"]:
            self._write_markdown(out_dir / f"{key}_replay_report.md", key, catalog[key])
        self._write_insight_markdown(out_dir / "replay_insight_report.md", catalog["insights"])

    def _write_markdown(self, path: Path, title: str, rows: list[dict]) -> None:
        lines = [f"# Replay {title.title()} Report", ""]
        if not rows:
            lines.append("No replay data available.")
        else:
            lines.append("| Period | Sessions | Decisions | Entries | Wins | Win Rate | PnL % | Veto |")
            lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
            for row in rows:
                lines.append(
                    f"| {row['period']} | {row['sessions']} | {row['decisions']} | {row['entries']} | "
                    f"{row['wins']} | {row['win_rate']:.2%} | {row['total_pnl_pct']:.2f} | {row['veto_count']} |"
                )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_insight_markdown(self, path: Path, insights: dict) -> None:
        summary = insights.get("summary", {})
        lines = [
            "# Replay Lab Insight Report",
            "",
            "## Executive Summary",
            f"- sample_quality: {summary.get('sample_quality', 'UNKNOWN')}",
            f"- total_days: {summary.get('total_days', 0)}",
            f"- total_sessions: {summary.get('total_sessions', 0)}",
            f"- total_decisions: {summary.get('total_decisions', 0)}",
            f"- total_entries: {summary.get('total_entries', 0)}",
            f"- win_rate: {float(summary.get('win_rate', 0.0)):.2%}",
            f"- entry_rate: {float(summary.get('entry_rate', 0.0)):.2%}",
            f"- veto_rate: {float(summary.get('veto_rate', 0.0)):.2%}",
            f"- total_pnl_pct: {float(summary.get('total_pnl_pct', 0.0)):.2f}",
            "",
            "## 앱의 가능성",
            *[f"- {item}" for item in insights.get("potential", [])],
            "",
            "## 현재 한계",
            *[f"- {item}" for item in insights.get("limits", [])],
            "",
            "## 디벨롭된 내용",
            *[f"- {item}" for item in insights.get("developments", [])],
            "",
            "## 추가 개선 인사이트",
            *[f"- {item}" for item in insights.get("improvement_insights", [])],
            "",
            "## 적용 원칙",
            "- 이 리포트는 연구용 산출물이며 실전 설정을 자동 변경하지 않는다.",
            "- config patch는 DRAFT -> BACKTESTED -> SHADOW_TESTED -> APPROVED 이후에만 메인 import 대상이 된다.",
        ]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
