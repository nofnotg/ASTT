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

    def build(self) -> dict[str, list[dict]]:
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
        }
        self._write_outputs(catalog)
        return catalog

    def load_or_build(self) -> dict[str, list[dict]]:
        path = self.reports_dir / "catalog" / "replay_report_catalog.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
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

    def _write_outputs(self, catalog: dict[str, list[dict]]) -> None:
        out_dir = self.reports_dir / "catalog"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "replay_report_catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
        for key in ["daily", "weekly", "monthly"]:
            self._write_markdown(out_dir / f"{key}_replay_report.md", key, catalog[key])

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
