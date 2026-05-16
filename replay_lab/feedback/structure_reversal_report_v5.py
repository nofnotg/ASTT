from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from replay_lab.paths import ROOT_DIR, REPLAY_STORE_DIR
from replay_lab.replay.structure_reversal_v5 import latest_structure_reversal_v5_experiment, live_readiness_v5


@dataclass(frozen=True)
class StructureReversalV5ReportBuilder:
    store_dir: Path = REPLAY_STORE_DIR
    capital_krw: float = 500000
    order_krw: float = 10000
    docs_root: Path = ROOT_DIR / "docs" / "reports"

    @property
    def out_dir(self) -> Path:
        return self.store_dir / "reports" / "structure_reversal_v5"

    def build(self, start_date: str = "2026-01-01", end_date: str | None = None) -> Path:
        end_date = end_date or datetime.utcnow().date().isoformat()
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.docs_root.mkdir(parents=True, exist_ok=True)
        payload = self._payload(start_date, end_date)
        html = self.out_dir / "structure_reversal_v5_report.html"
        json_path = self.out_dir / "structure_reversal_v5_report.json"
        md = self.out_dir / "structure_reversal_v5_report.md"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        md.write_text(self._markdown(payload), encoding="utf-8")
        self._write_html(html, payload)
        (self.docs_root / "latest_structure_reversal_v5_summary.json").write_text(json.dumps(self._summary(payload), ensure_ascii=False, indent=2), encoding="utf-8")
        (self.docs_root / "latest_structure_reversal_v5_report.md").write_text(self._markdown(payload), encoding="utf-8")
        return html

    def _payload(self, start_date: str, end_date: str) -> dict[str, Any]:
        exp = latest_structure_reversal_v5_experiment(self.store_dir, mode="small_seed_daily") or latest_structure_reversal_v5_experiment(self.store_dir)
        metrics = _read_json(exp / "metrics.json") if exp else {}
        sweep = _read_json(self.out_dir / "structure_reversal_sweep_v5.json")
        context = _read_json(self.out_dir / "mtf_context_compare_v5.json")
        compare = _read_json(self.out_dir / "structure_reversal_compare_all.json")
        readiness = metrics.get("live_readiness") or live_readiness_v5(metrics)
        return {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "period": {"start_date": start_date, "end_date": end_date}, "capital_krw": self.capital_krw, "order_krw": self.order_krw, "latest_experiment": str(exp) if exp else "", "metrics": metrics, "sweep": sweep, "context_compare": context, "compare_all": compare, "live_readiness": readiness, "insights": self._insights(metrics, sweep, context, compare)}

    def _summary(self, payload: dict[str, Any]) -> dict[str, Any]:
        metrics = payload.get("metrics", {})
        return {"schema_version": "1.0", "generated_at": payload["generated_at"], "period": payload["period"], "capital_krw": payload["capital_krw"], "order_krw": payload["order_krw"], "v5_result": {key: metrics.get(key, 0) for key in ["entry_count", "win_rate", "profit_factor", "account_return_pct", "max_drawdown_pct", "consecutive_loss_max", "total_order_pnl_krw"]}, "best_v5_config": payload.get("sweep", {}).get("best", {}), "best_context_stack": payload.get("context_compare", {}).get("best_context_stack", ""), "compare_verdict": payload.get("compare_all", {}).get("verdict", "NO_COMPARE"), "live_readiness": payload.get("live_readiness", "LIVE_NOT_ALLOWED"), "insights": payload.get("insights", [])}

    def _insights(self, metrics: dict, sweep: dict, context: dict, compare: dict) -> list[str]:
        insights = []
        best_stack = context.get("best_context_stack", "NO_CONTEXT")
        insights.append(f"MTF context best stack은 {best_stack}이다. 이 값이 No MTF보다 낫지 않다면 상위 필터는 후보 품질보다 후보 축소 효과가 더 컸다는 뜻이다.")
        if metrics.get("entry_count", 0) < 30:
            insights.append("진입 수가 30개 미만이면 V5는 아직 표본 부족이며, weekly/daily/h4 threshold 중 어느 축을 완화할지 먼저 확인해야 한다.")
        if metrics.get("profit_factor", 0.0) < 1.1:
            insights.append("Profit Factor가 1.1 미만이면 진입 구조보다 청산 방식 또는 Risk Gate의 저항 근접 veto가 우선 개선 대상이다.")
        if compare.get("verdict"):
            insights.append(f"V3/V4.1/V5 비교 판정은 {compare.get('verdict')}이다.")
        insights.append("Weekly Sniper는 표본이 적어도 연속손실을 낮추는지 확인하는 보조 축으로 유지한다.")
        return insights

    def _markdown(self, payload: dict[str, Any]) -> str:
        m = payload.get("metrics", {})
        sweep = payload.get("sweep", {})
        context = payload.get("context_compare", {})
        compare = payload.get("compare_all", {})
        return f"""# ASTT V5 다중 시간봉 구조반전 검증 리포트

## 1. V5 전략 개요
V5는 주봉/일봉/4H 상위 구조를 먼저 확인하고 1H/15M 셋업, 5M/1M 트리거, Risk Gate를 통과한 경우에만 PAPER 진입하는 구조반전 전략이다.

## 2. Small Seed Daily 결과
- entry_count: {m.get('entry_count', 0)}
- win_rate: {m.get('win_rate', 0) * 100:.2f}%
- profit_factor: {m.get('profit_factor', 0):.4f}
- account_return_pct: {m.get('account_return_pct', 0):.4f}%
- max_drawdown_pct: {m.get('max_drawdown_pct', 0):.4f}%
- consecutive_loss_max: {m.get('consecutive_loss_max', 0)}

## 3. Sweep 최고 설정
```json
{json.dumps(sweep.get('best', {}), ensure_ascii=False, indent=2)}
```

## 4. MTF Context Compare
- best_context_stack: {context.get('best_context_stack', 'NO_CONTEXT')}

## 5. V3/V4.1/V5 비교
- verdict: {compare.get('verdict', 'NO_COMPARE')}

## 6. 실전 전환 판정
- {payload.get('live_readiness', 'LIVE_NOT_ALLOWED')}

## 7. 인사이트
{chr(10).join(f'- {item}' for item in payload.get('insights', []))}
"""

    def _write_html(self, path: Path, payload: dict[str, Any]) -> None:
        m = payload.get("metrics", {})
        html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ASTT V5 다중 시간봉 구조반전 검증 리포트</title>
<style>body{{margin:0;background:#f3f6f9;color:#111827;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif;line-height:1.6}}main{{max-width:1180px;margin:0 auto;padding:34px 20px 72px}}.hero{{background:#102033;color:white;border-radius:8px;padding:24px}}.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}}section,.card{{background:white;border:1px solid #d8e0ea;border-radius:8px;padding:16px;margin-top:14px}}.metric b{{display:block;font-size:24px}}table{{width:100%;border-collapse:collapse}}th,td{{border-bottom:1px solid #e2e8f0;padding:8px;text-align:left}}@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}</style></head><body><main>
<div class="hero"><h1>ASTT V5 다중 시간봉 구조반전 검증 리포트</h1><p>Replay Lab PAPER 전용 검증 결과입니다. 실거래 전환 근거로 단독 사용하지 않습니다.</p></div>
<div class="grid">{self._metric('Entry', m.get('entry_count',0))}{self._metric('Win Rate', f"{m.get('win_rate',0)*100:.2f}%")}{self._metric('PF', f"{m.get('profit_factor',0):.3f}")}{self._metric('Account', f"{m.get('account_return_pct',0):.4f}%")}</div>
<section><h2>1. V5 구조</h2><p>Weekly Bias → Daily Structure → 4H Flow → 1H/15M Setup → 5M/1M Trigger → Risk Gate 순서로 후보를 줄인다.</p></section>
<section><h2>2. MTF Context Compare</h2>{self._context_table(payload.get('context_compare',{}).get('context_results', []))}</section>
<section><h2>3. 전략 유형별 성과</h2>{self._strategy_table(m.get('strategy_type_performance', []))}</section>
<section><h2>4. V3/V4.1/V5 비교</h2><p>{escape(payload.get('compare_all',{}).get('verdict','NO_COMPARE'))}</p></section>
<section><h2>5. 실전 전환 판정</h2><strong>{escape(payload.get('live_readiness','LIVE_NOT_ALLOWED'))}</strong></section>
<section><h2>6. 인사이트</h2><ul>{"".join(f"<li>{escape(item)}</li>" for item in payload.get('insights', []))}</ul></section>
</main></body></html>"""
        path.write_text(html, encoding="utf-8")

    def _metric(self, label: str, value: Any) -> str:
        return f"<div class='card metric'><span>{escape(str(label))}</span><b>{escape(str(value))}</b></div>"

    def _context_table(self, rows: list[dict]) -> str:
        if not rows:
            return "<p>context compare 데이터 없음</p>"
        body = "".join(f"<tr><td>{escape(row.get('context_stack',''))}</td><td>{row.get('entry_count',0)}</td><td>{row.get('win_rate',0)*100:.2f}%</td><td>{row.get('profit_factor',0):.3f}</td><td>{row.get('account_return_pct',0):.4f}%</td><td>{row.get('max_drawdown_pct',0):.4f}%</td></tr>" for row in rows)
        return "<table><thead><tr><th>Context Stack</th><th>Entry</th><th>Win Rate</th><th>PF</th><th>Account</th><th>MDD</th></tr></thead><tbody>" + body + "</tbody></table>"

    def _strategy_table(self, rows: list[dict]) -> str:
        if not rows:
            return "<p>전략 유형별 데이터 없음</p>"
        body = "".join(f"<tr><td>{escape(row.get('key',''))}</td><td>{row.get('entry_count',0)}</td><td>{row.get('win_rate',0)*100:.2f}%</td><td>{row.get('profit_factor',0):.3f}</td><td>{row.get('account_return_pct',0):.4f}%</td></tr>" for row in rows)
        return "<table><thead><tr><th>Strategy</th><th>Entry</th><th>Win Rate</th><th>PF</th><th>Account</th></tr></thead><tbody>" + body + "</tbody></table>"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
