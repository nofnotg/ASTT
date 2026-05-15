from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd

from replay_lab.paths import ROOT_DIR, REPLAY_STORE_DIR
from replay_lab.replay.small_seed_v3 import latest_small_seed_experiment, live_readiness


@dataclass(frozen=True)
class SmallSeedReportBuilder:
    store_dir: Path = REPLAY_STORE_DIR
    capital_krw: float = 500000
    order_krw: float = 10000
    docs_root: Path = ROOT_DIR / "docs" / "reports"

    @property
    def out_dir(self) -> Path:
        return self.store_dir / "reports" / "small_seed_v3"

    @property
    def docs_dir(self) -> Path:
        return self.docs_root

    def build(self, start_date: str = "2026-01-01", end_date: str | None = None) -> Path:
        end_date = end_date or pd.Timestamp.today().date().isoformat()
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        payload = self._payload(start_date, end_date)
        html_path = self.out_dir / "small_seed_v3_report.html"
        json_path = self.out_dir / "small_seed_v3_report.json"
        md_path = self.out_dir / "small_seed_v3_report.md"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(self._markdown(payload), encoding="utf-8")
        self._write_html(html_path, payload)
        (self.docs_dir / "latest_small_seed_summary.json").write_text(json.dumps(self._summary_for_docs(payload), ensure_ascii=False, indent=2), encoding="utf-8")
        (self.docs_dir / "latest_small_seed_report.md").write_text(self._markdown(payload), encoding="utf-8")
        return html_path

    def _payload(self, start_date: str, end_date: str) -> dict[str, Any]:
        threshold = self._read_json("threshold_sweep_v3.json")
        windows = self._read_json("time_window_sweep_v3.json")
        compare = self._read_json("preopen_confirmed_compare_v3.json")
        exp = latest_small_seed_experiment(self.store_dir)
        metrics = {}
        daily = pd.DataFrame()
        weekly = pd.DataFrame()
        monthly = pd.DataFrame()
        trades = pd.DataFrame()
        if exp:
            metrics_path = exp / "metrics.json"
            metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
            daily = pd.read_parquet(exp / "daily_account.parquet") if (exp / "daily_account.parquet").exists() else pd.DataFrame()
            weekly = pd.read_parquet(exp / "weekly_account.parquet") if (exp / "weekly_account.parquet").exists() else pd.DataFrame()
            monthly = pd.read_parquet(exp / "monthly_account.parquet") if (exp / "monthly_account.parquet").exists() else pd.DataFrame()
            trades = pd.read_parquet(exp / "paper_trades.parquet") if (exp / "paper_trades.parquet").exists() else pd.DataFrame()
        readiness = metrics.get("live_readiness") or live_readiness(metrics)
        return {
            "schema_version": "1.0",
            "generated_at": datetime.utcnow().isoformat(),
            "period": {"start_date": start_date, "end_date": end_date},
            "capital_krw": self.capital_krw,
            "order_krw": self.order_krw,
            "latest_experiment": str(exp) if exp else "",
            "small_seed_result": metrics,
            "live_readiness": readiness,
            "daily": daily.to_dict("records"),
            "weekly": weekly.to_dict("records"),
            "monthly": monthly.to_dict("records"),
            "trades": trades.to_dict("records"),
            "threshold_sweep": threshold,
            "time_window_sweep": windows,
            "preopen_vs_confirmed": compare,
            "next_actions": self._next_actions(metrics, threshold, windows, compare),
        }

    def _summary_for_docs(self, payload: dict[str, Any]) -> dict[str, Any]:
        windows = payload.get("time_window_sweep", {}).get("rows", [])
        reliable_windows = [row for row in windows if row.get("entry_count", 0) >= 30]
        threshold = payload.get("threshold_sweep", {}).get("best", {})
        compare = payload.get("preopen_vs_confirmed", {})
        result = payload.get("small_seed_result", {})
        return {
            "schema_version": "1.0",
            "generated_at": payload["generated_at"],
            "period": payload["period"],
            "capital_krw": payload["capital_krw"],
            "order_krw": payload["order_krw"],
            "best_time_windows": (reliable_windows or windows)[:5],
            "best_threshold_config": threshold,
            "preopen_vs_confirmed": {
                "better_mode": compare.get("better_mode"),
                "preopen": compare.get("preopen", {}),
                "confirmed": compare.get("confirmed", {}),
            },
            "small_seed_result": {
                "entry_count": result.get("entry_count", 0),
                "win_rate": result.get("win_rate", 0.0),
                "total_order_pnl_krw": result.get("total_order_pnl_krw", 0.0),
                "account_return_pct": result.get("account_return_pct", 0.0),
                "max_drawdown_pct": result.get("max_drawdown_pct", 0.0),
                "profit_factor": result.get("profit_factor", 0.0),
                "consecutive_loss_max": result.get("consecutive_loss_max", 0),
            },
            "live_readiness": payload.get("live_readiness", "LIVE_NOT_ALLOWED"),
            "next_actions": payload.get("next_actions", []),
        }

    def _next_actions(self, metrics: dict, threshold: dict, windows: dict, compare: dict) -> list[str]:
        actions = []
        if threshold.get("best", {}).get("status") == "NO_VALID_THRESHOLD":
            actions.append("Threshold Sweep에서 유효 후보가 없으므로 EntryGate 완화 범위를 더 넓혀 재실험한다.")
        if metrics.get("entry_count", 0) < 50:
            actions.append("진입 수가 50회 미만이면 수익률이 양수여도 신뢰하지 않는다. 시간창/임계값을 넓혀 표본을 늘린다.")
        if metrics.get("account_return_pct", 0) <= 0:
            actions.append("계좌 성장률이 양수가 아니므로 MICRO LIVE 전환은 금지하고 PAPER 검증을 지속한다.")
        if compare.get("better_mode") == "confirmed":
            actions.append("Confirmed 모드가 더 적합하면 09:03 확인 후 진입을 기본 후보로 둔다.")
        if windows.get("rows"):
            actions.append("상위 시간창 3개만 대상으로 2주 Live Paper 검증 시나리오를 만든다.")
            if windows["rows"][0].get("entry_count", 0) < 30:
                actions.append("시간창 랭킹 상단에 표본 30회 미만 구간이 있으면 참고 후보로만 보고, 신뢰 후보는 entry_count 30회 이상으로 제한한다.")
        return actions or ["현재 설정을 유지하고 2주 이상 PAPER 검증 표본을 추가한다."]

    def _read_json(self, name: str) -> dict:
        path = self.out_dir / name
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def _markdown(self, payload: dict[str, Any]) -> str:
        result = payload.get("small_seed_result", {})
        threshold = payload.get("threshold_sweep", {}).get("best", {})
        windows = payload.get("time_window_sweep", {}).get("rows", [])
        compare = payload.get("preopen_vs_confirmed", {})
        return f"""# ASTT V3 소액 시드 자동매매 검증 리포트

## 1. 최종 요약
- 기간: {payload['period']['start_date']} ~ {payload['period']['end_date']}
- 시드: {payload['capital_krw']:,.0f}원
- 주문금액: {payload['order_krw']:,.0f}원
- 진입 수: {result.get('entry_count', 0)}
- 승률: {result.get('win_rate', 0) * 100:.2f}%
- 실제 주문금액 손익: {result.get('total_order_pnl_krw', 0):,.0f}원
- 계좌 성장률: {result.get('account_return_pct', 0):.4f}%
- MDD: {result.get('max_drawdown_pct', 0):.4f}%
- Profit Factor: {result.get('profit_factor', 0):.4f}
- 실전 전환 판정: {payload.get('live_readiness')}

## 2. 거래 수익률 vs 실제 주문금액 손익
1만 원 주문에서 +1%는 100원이며, 50만 원 계좌 기준으로는 +0.02%입니다. 이 리포트는 거래 수익률과 계좌 성장률을 분리합니다.

## 3. Threshold Sweep 결과
- 상태: {threshold.get('status', 'NO_DATA')}
- 설정: final={threshold.get('final_score')}, setup={threshold.get('setup_score')}, trigger={threshold.get('trigger_score')}, confidence={threshold.get('confidence')}
- entry_count: {threshold.get('entry_count', 0)}
- account_return_pct: {threshold.get('account_return_pct', 0):.4f}
- max_drawdown_pct: {threshold.get('max_drawdown_pct', 0):.4f}

## 4. 시간창별 기대값
{self._md_window_rows(windows[:10])}

## 5. PreOpen vs Confirmed
- 더 적합한 모드: {compare.get('better_mode', 'NO_DATA')}
- PreOpen: {compare.get('preopen', {})}
- Confirmed: {compare.get('confirmed', {})}

## 6. 다음 개발 과제
{chr(10).join(f'- {item}' for item in payload.get('next_actions', []))}
"""

    def _write_html(self, path: Path, payload: dict[str, Any]) -> None:
        result = payload.get("small_seed_result", {})
        html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ASTT V3 소액 시드 자동매매 검증 리포트</title>
  <style>
    :root {{ --bg:#f5f7fa; --panel:#fff; --line:#d8e0ea; --ink:#111827; --muted:#64748b; --accent:#0f766e; --loss:#b42318; --gain:#067647; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif; line-height:1.55; }}
    main {{ max-width:1260px; margin:0 auto; padding:34px 20px 72px; }}
    h1 {{ margin:0 0 8px; font-size:32px; }}
    h2 {{ margin:0 0 12px; font-size:21px; }}
    section,.card {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; margin-top:14px; }}
    .grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }}
    .metric b {{ display:block; font-size:24px; margin-top:4px; }}
    .small {{ color:var(--muted); font-size:13px; }}
    .gain {{ color:var(--gain); }} .loss {{ color:var(--loss); }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th,td {{ padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
    th {{ background:#f8fafc; color:#334155; }}
    .scroll {{ max-height:540px; overflow:auto; border:1px solid var(--line); border-radius:8px; }}
    @media(max-width:900px) {{ .grid {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
<main>
  <h1>ASTT V3 소액 시드 자동매매 검증 리포트</h1>
  <p class="small">50만 원 시드에서는 거래 수익률과 실제 계좌 성장률이 다릅니다. 이 문서는 주문금액 {payload['order_krw']:,.0f}원 기준으로 계산합니다.</p>
  <div class="grid">
    {self._metric("진입 수", f"{result.get('entry_count', 0):,}회")}
    {self._metric("승률", f"{result.get('win_rate', 0) * 100:.2f}%")}
    {self._metric("주문금액 손익", f"{result.get('total_order_pnl_krw', 0):,.0f}원", "gain" if result.get("total_order_pnl_krw", 0) >= 0 else "loss")}
    {self._metric("계좌 성장률", f"{result.get('account_return_pct', 0):.4f}%", "gain" if result.get("account_return_pct", 0) >= 0 else "loss")}
  </div>
  <section><h2>1. 최종 요약</h2>{self._summary_table(result, payload.get("live_readiness"))}</section>
  <section><h2>2. 거래 수익률 vs 실제 주문금액 손익</h2><p>1만 원 주문에서 +1% 수익은 100원입니다. 50만 원 전체 계좌 기준으로는 +0.02%입니다. 따라서 이 리포트는 거래 자체 수익률과 계좌 성장률을 분리합니다.</p></section>
  <section><h2>3. 일자별 진입/미진입 기록</h2><div class="scroll">{self._daily_table(payload.get("daily", []))}</div></section>
  <section><h2>4. 주간 손익</h2>{self._period_table(payload.get("weekly", []))}</section>
  <section><h2>5. 월간 손익</h2>{self._period_table(payload.get("monthly", []))}</section>
  <section><h2>6. 시간창별 기대값 랭킹</h2>{self._window_table(payload.get("time_window_sweep", {}).get("rows", []))}</section>
  <section><h2>7. Threshold Sweep 결과</h2>{self._threshold_table(payload.get("threshold_sweep", {}).get("rows", []), payload.get("threshold_sweep", {}).get("best", {}))}</section>
  <section><h2>8. PreOpen vs Confirmed 비교</h2>{self._compare_table(payload.get("preopen_vs_confirmed", {}))}</section>
  <section><h2>9. 손실 방어 규칙 작동 여부</h2><p>진입 수, MDD, 연속 손실 수, Profit Factor 기준으로 판정합니다. 조건 미달이면 MICRO LIVE 전환은 금지합니다.</p></section>
  <section><h2>10. 실전 전환 가능성 판정</h2><strong>{escape(payload.get("live_readiness", "LIVE_NOT_ALLOWED"))}</strong></section>
  <section><h2>11. 다음 개발 과제</h2><ul>{"".join(f"<li>{escape(item)}</li>" for item in payload.get("next_actions", []))}</ul></section>
</main>
</body>
</html>"""
        path.write_text(html, encoding="utf-8")

    def _metric(self, label: str, value: str, klass: str = "") -> str:
        return f'<div class="card metric"><span class="small">{escape(label)}</span><b class="{klass}">{escape(value)}</b></div>'

    def _summary_table(self, result: dict, readiness: str) -> str:
        rows = [
            ("entry_count", result.get("entry_count", 0)),
            ("win_rate", f"{result.get('win_rate', 0) * 100:.2f}%"),
            ("total_order_pnl_krw", f"{result.get('total_order_pnl_krw', 0):,.0f}원"),
            ("account_return_pct", f"{result.get('account_return_pct', 0):.4f}%"),
            ("max_drawdown_pct", f"{result.get('max_drawdown_pct', 0):.4f}%"),
            ("consecutive_loss_max", result.get("consecutive_loss_max", 0)),
            ("profit_factor", f"{result.get('profit_factor', 0):.4f}"),
            ("live_readiness", readiness),
        ]
        return "<table><tbody>" + "".join(f"<tr><th>{escape(str(k))}</th><td>{escape(str(v))}</td></tr>" for k, v in rows) + "</tbody></table>"

    def _daily_table(self, rows: list[dict]) -> str:
        if not rows:
            return "<p>일자별 데이터가 없습니다.</p>"
        body = "".join(
            f"<tr><td>{escape(str(row.get('date_kst')))}</td><td>{row.get('entries', 0)}</td><td>{row.get('wins', 0)}</td><td>{row.get('losses', 0)}</td><td>{row.get('order_pnl_krw', 0):,.0f}원</td><td>{row.get('daily_account_pnl_pct', 0):.4f}%</td><td>{row.get('drawdown_pct', 0):.4f}%</td></tr>"
            for row in rows
        )
        return "<table><thead><tr><th>날짜</th><th>진입</th><th>승</th><th>패</th><th>손익</th><th>계좌%</th><th>DD</th></tr></thead><tbody>" + body + "</tbody></table>"

    def _period_table(self, rows: list[dict]) -> str:
        if not rows:
            return "<p>기간 집계가 없습니다.</p>"
        body = "".join(
            f"<tr><td>{escape(str(row.get('period')))}</td><td>{row.get('entries', 0)}</td><td>{row.get('win_rate', 0) * 100:.2f}%</td><td>{row.get('order_pnl_krw', 0):,.0f}원</td><td>{row.get('account_return_pct', 0):.4f}%</td><td>{row.get('max_drawdown_pct', 0):.4f}%</td></tr>"
            for row in rows
        )
        return "<table><thead><tr><th>기간</th><th>진입</th><th>승률</th><th>손익</th><th>계좌%</th><th>MDD</th></tr></thead><tbody>" + body + "</tbody></table>"

    def _window_table(self, rows: list[dict]) -> str:
        if not rows:
            return "<p>시간창 sweep 결과가 없습니다.</p>"
        reliable = [row for row in rows if row.get("entry_count", 0) >= 30]
        display_rows = (reliable or rows)[:20]
        body = "".join(
            f"<tr><td>{escape(str(row.get('window')))}</td><td>{row.get('entry_count', 0)}</td><td>{row.get('win_rate', 0) * 100:.2f}%</td><td>{row.get('account_return_pct', 0):.4f}%</td><td>{row.get('max_drawdown_pct', 0):.4f}%</td><td>{row.get('profit_factor', 0):.3f}</td><td>{row.get('risk_adjusted_score', 0):.3f}</td></tr>"
            for row in display_rows
        )
        return "<p class='small'>표본 30회 이상인 시간창을 우선 표시합니다. 표본 3회 같은 구간은 수익이어도 신뢰 후보가 아닙니다.</p><table><thead><tr><th>시간창</th><th>진입</th><th>승률</th><th>계좌%</th><th>MDD</th><th>PF</th><th>점수</th></tr></thead><tbody>" + body + "</tbody></table>"

    def _threshold_table(self, rows: list[dict], best: dict) -> str:
        if not rows:
            return "<p>Threshold Sweep 결과가 없습니다.</p>"
        best_html = f"<p>추천 상태: <strong>{escape(str(best.get('status', 'NO_DATA')))}</strong></p>"
        body = "".join(
            f"<tr><td>{row.get('final_score')}</td><td>{row.get('setup_score')}</td><td>{row.get('trigger_score')}</td><td>{row.get('confidence')}</td><td>{row.get('entry_count', 0)}</td><td>{row.get('account_return_pct', 0):.4f}%</td><td>{row.get('max_drawdown_pct', 0):.4f}%</td><td>{row.get('profit_factor', 0):.3f}</td></tr>"
            for row in rows[:20]
        )
        return best_html + "<table><thead><tr><th>Final</th><th>Setup</th><th>Trigger</th><th>Conf</th><th>진입</th><th>계좌%</th><th>MDD</th><th>PF</th></tr></thead><tbody>" + body + "</tbody></table>"

    def _compare_table(self, payload: dict) -> str:
        if not payload:
            return "<p>PreOpen/Confirmed 비교 결과가 없습니다.</p>"
        rows = [payload.get("preopen", {}), payload.get("confirmed", {})]
        body = "".join(
            f"<tr><td>{escape(str(row.get('mode')))}</td><td>{row.get('entry_count', 0)}</td><td>{row.get('win_rate', 0) * 100:.2f}%</td><td>{row.get('total_order_pnl_krw', 0):,.0f}원</td><td>{row.get('account_return_pct', 0):.4f}%</td><td>{row.get('max_drawdown_pct', 0):.4f}%</td><td>{row.get('false_breakout_loss_count', 0)}</td><td>{row.get('time_exit_count', 0)}</td></tr>"
            for row in rows
        )
        return f"<p>더 적합한 모드: <strong>{escape(str(payload.get('better_mode')))}</strong></p><table><thead><tr><th>모드</th><th>진입</th><th>승률</th><th>손익</th><th>계좌%</th><th>MDD</th><th>가짜돌파 손실</th><th>시간청산</th></tr></thead><tbody>{body}</tbody></table>"

    def _md_window_rows(self, rows: list[dict]) -> str:
        if not rows:
            return "- 시간창 결과 없음"
        return "\n".join(f"- {row.get('window')}: entry={row.get('entry_count')}, account={row.get('account_return_pct', 0):.4f}%, score={row.get('risk_adjusted_score', 0):.3f}" for row in rows)
