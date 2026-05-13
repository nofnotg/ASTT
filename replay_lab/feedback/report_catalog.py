from __future__ import annotations

import json
from dataclasses import dataclass
from html import escape
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
            "insights": self._build_insights(daily),
        }
        self._write_outputs(catalog)
        return catalog

    def load_or_build(self) -> dict[str, list[dict] | dict]:
        path = self.reports_dir / "catalog" / "replay_report_catalog.json"
        if path.exists():
            catalog = json.loads(path.read_text(encoding="utf-8"))
            if "insights" not in catalog:
                catalog["insights"] = self._build_insights(catalog.get("daily", []))
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

    def _build_insights(self, daily: list[dict]) -> dict:
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
            potential.append(f"현재 누적 리플레이 PnL은 {total_pnl:.2f}%로 양수가 아니므로, 수익성보다 필터와 리스크 검증 단계로 해석해야 한다.")
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
        self._write_html_report(out_dir / "replay_report.html", catalog)

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

    def _write_html_report(self, path: Path, catalog: dict[str, list[dict] | dict]) -> None:
        insights = catalog.get("insights", {})
        summary = insights.get("summary", {})
        html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ASTT Replay Lab Report</title>
  <style>
    :root {{ --bg:#f6f7f9; --panel:#fff; --text:#161a1d; --muted:#667085; --border:#d9dee7; --accent:#0f766e; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif; line-height:1.5; }}
    main {{ max-width:1180px; margin:0 auto; padding:36px 24px 64px; }}
    header {{ margin-bottom:28px; }}
    h1 {{ margin:0 0 8px; font-size:34px; line-height:1.18; letter-spacing:0; }}
    h2 {{ margin:0 0 16px; font-size:22px; letter-spacing:0; }}
    p {{ margin:0; color:var(--muted); }}
    section {{ background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:22px; margin:16px 0; }}
    .grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }}
    .metric {{ border:1px solid var(--border); border-radius:8px; padding:14px; background:#fbfcfe; }}
    .metric span {{ display:block; color:var(--muted); font-size:12px; }}
    .metric strong {{ display:block; margin-top:6px; font-size:22px; }}
    .pill {{ display:inline-flex; border-radius:999px; padding:5px 10px; background:#e6f4f1; color:var(--accent); font-weight:700; font-size:12px; }}
    ul {{ margin:0; padding-left:20px; }}
    li {{ margin:7px 0; }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th,td {{ padding:9px 10px; border-bottom:1px solid var(--border); text-align:right; }}
    th:first-child,td:first-child {{ text-align:left; }}
    th {{ color:var(--muted); background:#f8fafc; font-weight:700; }}
    .table-wrap {{ overflow-x:auto; }}
    .note {{ color:var(--muted); font-size:13px; margin-top:12px; }}
    @media (max-width:820px) {{ .grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} main {{ padding:24px 14px 48px; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <div class="pill">Replay Lab Sidecar</div>
    <h1>ASTT Replay Lab Report</h1>
    <p>일별, 주간, 월간 리플레이 통계와 앱 가능성·한계·개선 인사이트를 정리한 렌더링 문서입니다.</p>
  </header>
  <section>
    <h2>Executive Summary</h2>
    <div class="grid">
      {self._metric("표본 품질", summary.get("sample_quality", "UNKNOWN"))}
      {self._metric("총 일수", summary.get("total_days", 0))}
      {self._metric("진입 수", summary.get("total_entries", 0))}
      {self._metric("승률", self._pct(summary.get("win_rate", 0.0)))}
      {self._metric("진입률", self._pct(summary.get("entry_rate", 0.0)))}
      {self._metric("Veto율", self._pct(summary.get("veto_rate", 0.0)))}
      {self._metric("누적 PnL", f"{float(summary.get('total_pnl_pct', 0.0)):.2f}%")}
      {self._metric("총 판단", summary.get("total_decisions", 0))}
    </div>
  </section>
  {self._list_section("앱의 가능성", insights.get("potential", []))}
  {self._list_section("현재 한계", insights.get("limits", []))}
  {self._list_section("디벨롭된 내용", insights.get("developments", []))}
  {self._list_section("추가 개선 인사이트", insights.get("improvement_insights", []))}
  {self._table_section("일별 리포트", catalog.get("daily", []))}
  {self._table_section("주간 통계", catalog.get("weekly", []))}
  {self._table_section("월간 통계", catalog.get("monthly", []))}
  <section>
    <h2>적용 원칙</h2>
    <ul>
      <li>이 리포트는 연구용 산출물이며 실전 설정을 자동 변경하지 않습니다.</li>
      <li>config patch는 DRAFT → BACKTESTED → SHADOW_TESTED → APPROVED 이후에만 메인 import 대상입니다.</li>
    </ul>
    <p class="note">Generated from replay_store/reports/catalog/replay_report_catalog.json</p>
  </section>
</main>
</body>
</html>
"""
        path.write_text(html, encoding="utf-8")

    def _metric(self, label: str, value) -> str:
        return f'<div class="metric"><span>{escape(str(label))}</span><strong>{escape(str(value))}</strong></div>'

    def _pct(self, value: float) -> str:
        return f"{float(value):.2%}"

    def _list_section(self, title: str, items: list[str]) -> str:
        body = "".join(f"<li>{escape(str(item))}</li>" for item in items) or "<li>No data.</li>"
        return f"<section><h2>{escape(title)}</h2><ul>{body}</ul></section>"

    def _table_section(self, title: str, rows: list[dict]) -> str:
        if not rows:
            return f"<section><h2>{escape(title)}</h2><p>No replay data available.</p></section>"
        body = "".join(
            "<tr>"
            f"<td>{escape(str(row.get('period', '')))}</td>"
            f"<td>{int(row.get('sessions', 0))}</td>"
            f"<td>{int(row.get('decisions', 0))}</td>"
            f"<td>{int(row.get('entries', 0))}</td>"
            f"<td>{int(row.get('wins', 0))}</td>"
            f"<td>{self._pct(row.get('win_rate', 0.0))}</td>"
            f"<td>{float(row.get('total_pnl_pct', 0.0)):.2f}%</td>"
            f"<td>{int(row.get('veto_count', 0))}</td>"
            "</tr>"
            for row in rows
        )
        return f"""<section>
  <h2>{escape(title)}</h2>
  <div class="table-wrap">
    <table>
      <thead><tr><th>Period</th><th>Sessions</th><th>Decisions</th><th>Entries</th><th>Wins</th><th>Win Rate</th><th>PnL</th><th>Veto</th></tr></thead>
      <tbody>{body}</tbody>
    </table>
  </div>
</section>"""
