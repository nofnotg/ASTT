from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from replay_lab.paths import ROOT_DIR, REPLAY_STORE_DIR
from replay_lab.replay.fear_exhaustion_v41 import latest_fear_exhaustion_v41_experiment, live_readiness_v41


@dataclass(frozen=True)
class FearExhaustionV41ReportBuilder:
    store_dir: Path = REPLAY_STORE_DIR
    capital_krw: float = 500000
    order_krw: float = 10000
    docs_root: Path = ROOT_DIR / "docs" / "reports"

    @property
    def out_dir(self) -> Path:
        return self.store_dir / "reports" / "fear_exhaustion_v41"

    def build(self, start_date: str = "2026-01-01", end_date: str | None = None) -> Path:
        end_date = end_date or datetime.utcnow().date().isoformat()
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.docs_root.mkdir(parents=True, exist_ok=True)
        payload = self._payload(start_date, end_date)
        html = self.out_dir / "fear_exhaustion_v41_report.html"
        json_path = self.out_dir / "fear_exhaustion_v41_report.json"
        md = self.out_dir / "fear_exhaustion_v41_report.md"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        md.write_text(self._markdown(payload), encoding="utf-8")
        self._write_html(html, payload)
        summary = self._summary(payload)
        (self.docs_root / "latest_fear_exhaustion_v41_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        (self.docs_root / "latest_fear_exhaustion_v41_report.md").write_text(self._markdown(payload), encoding="utf-8")
        return html

    def _payload(self, start_date: str, end_date: str) -> dict[str, Any]:
        exp = latest_fear_exhaustion_v41_experiment(self.store_dir)
        metrics = _read_json(exp / "metrics.json") if exp else {}
        sweep = _read_json(self.out_dir / "fear_exhaustion_sweep_v41.json")
        funnel = _read_json(self.out_dir / "fear_exhaustion_funnel_v41.json")
        compare = _read_json(self.out_dir / "fear_exhaustion_compare_v4.json")
        best = sweep.get("best", {})
        readiness = metrics.get("live_readiness") or live_readiness_v41(best or metrics)
        return {
            "schema_version": "1.0",
            "generated_at": datetime.utcnow().isoformat(),
            "period": {"start_date": start_date, "end_date": end_date},
            "capital_krw": self.capital_krw,
            "order_krw": self.order_krw,
            "latest_experiment": str(exp) if exp else "",
            "metrics": metrics,
            "sweep": sweep,
            "funnel": funnel,
            "compare_v4": compare,
            "live_readiness": readiness,
            "next_actions": self._next_actions(best, metrics, funnel),
        }

    def _summary(self, payload: dict[str, Any]) -> dict[str, Any]:
        best = payload.get("sweep", {}).get("best", {})
        metrics = payload.get("metrics", {})
        compare = payload.get("compare_v4", {})
        return {
            "schema_version": "1.0",
            "generated_at": payload["generated_at"],
            "period": payload["period"],
            "capital_krw": payload["capital_krw"],
            "order_krw": payload["order_krw"],
            "best_v41_config": best,
            "small_seed_result": {
                "entry_count": metrics.get("entry_count", best.get("entry_count", 0)),
                "win_rate": metrics.get("win_rate", best.get("win_rate", 0.0)),
                "profit_factor": metrics.get("profit_factor", best.get("profit_factor", 0.0)),
                "account_return_pct": metrics.get("account_return_pct", best.get("account_return_pct", 0.0)),
                "max_drawdown_pct": metrics.get("max_drawdown_pct", best.get("max_drawdown_pct", 0.0)),
                "consecutive_loss_max": metrics.get("consecutive_loss_max", best.get("consecutive_loss_max", 0)),
                "total_order_pnl_krw": metrics.get("total_order_pnl_krw", best.get("total_order_pnl_krw", 0.0)),
            },
            "v4_vs_v41": compare.get("verdict", "NO_COMPARE"),
            "live_readiness": payload.get("live_readiness", "LIVE_NOT_ALLOWED"),
            "next_actions": payload.get("next_actions", []),
        }

    def _next_actions(self, best: dict, metrics: dict, funnel: dict) -> list[str]:
        actions = []
        entry_count = int(metrics.get("entry_count", best.get("entry_count", 0)) or 0)
        if entry_count < 30:
            actions.append("후보 표본이 30개 미만이면 실전 검증이 아니라 병목 진단 단계로 유지한다.")
        if best.get("profit_factor", 0.0) < 1.1:
            actions.append("수익성 기준이 약하면 상단 밴드 익절보다 먼저 손절/시간청산 조건을 분리 실험한다.")
        if funnel:
            actions.append("퍼널에서 가장 크게 줄어드는 조건을 다음 실험의 1순위 완화 대상으로 둔다.")
        actions.append("Skeptic Guard는 당분간 DIAGNOSTIC으로 유지하고, 표본이 충분해진 뒤 BLOCKING 전환 여부를 판단한다.")
        actions.append("BTC 쇼크 필터와 15분봉 맥락 필터를 추가해 1분봉 노이즈를 줄이는 실험을 분리한다.")
        return actions

    def _markdown(self, payload: dict[str, Any]) -> str:
        best = payload.get("sweep", {}).get("best", {})
        metrics = payload.get("metrics", {})
        compare = payload.get("compare_v4", {})
        funnel_rows = _funnel_rows(payload.get("funnel", {}).get("funnels", payload.get("sweep", {}).get("base_funnels", {})))
        return f"""# ASTT V4.1 Relaxed Fear Exhaustion 검증 리포트

## 1. V4 실패 원인 요약
V4는 정통 공포 다이버전스 조건이 너무 엄격해 후보가 0개에 가까웠다. V4.1은 수익률을 증명하기 전에 후보가 어느 조건에서 사라지는지 보기 위한 병목 진단 버전이다.

## 2. V4.1 완화 로직
- 급락 이벤트: 최근 고점 대비 저점 하락률을 본다.
- 저점 구조: 정통 lower low뿐 아니라 low retest도 허용한다.
- 공포 둔화: fear_score, volume_panic, volatility_fear 중 하나만 둔화해도 통과 가능하다.
- 볼린저 복귀: 하단 밴드 밖 매수는 금지하고 내부 복귀 후만 후보로 본다.
- 최소 지지: 몸통 매물대, 추세선, 이전 저점, MA30 목표 공간, 볼린저 중심선 공간 중 1개 이상을 요구한다.

## 3. 1m vs 5m 최고 결과
- best_timeframe: {best.get('timeframe', '')}
- entry_count: {best.get('entry_count', 0)}
- win_rate: {best.get('win_rate', 0) * 100:.2f}%
- profit_factor: {best.get('profit_factor', 0):.3f}
- account_return_pct: {best.get('account_return_pct', 0):.4f}%

## 4. Funnel Report
| 단계 | count |
| --- | ---: |
{funnel_rows}

## 5. Skeptic Guard 진단 결과
- mode: DIAGNOSTIC
- would_block_count: {metrics.get('skeptic_would_block_count', best.get('skeptic_would_block_count', 0))}
- blocking_applied_count: {metrics.get('blocking_applied_count', 0)}

## 6. 50만 원 시드 기준 손익
- order_krw: {payload.get('order_krw', 0):,.0f}원
- total_order_pnl_krw: {metrics.get('total_order_pnl_krw', 0):,.0f}원
- account_return_pct: {metrics.get('account_return_pct', 0):.4f}%

## 7. V4 vs V4.1 비교
- 판정: {compare.get('verdict', 'NO_COMPARE')}

## 8. 실전 전환 판정
- {payload.get('live_readiness', 'LIVE_NOT_ALLOWED')}

## 9. 다음 실험 제안
{chr(10).join(f'- {item}' for item in payload.get('next_actions', []))}
"""

    def _write_html(self, path: Path, payload: dict[str, Any]) -> None:
        best = payload.get("sweep", {}).get("best", {})
        metrics = payload.get("metrics", {})
        compare = payload.get("compare_v4", {})
        funnels = payload.get("funnel", {}).get("funnels", payload.get("sweep", {}).get("base_funnels", {}))
        html = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ASTT V4.1 Relaxed Fear Exhaustion 검증 리포트</title>
<style>
body{{margin:0;background:#eef2f6;color:#111827;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif;line-height:1.6}}
main{{max-width:1180px;margin:0 auto;padding:36px 20px 72px}}
.hero{{background:#111827;color:white;border-radius:8px;padding:24px;margin-bottom:16px}}
.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}}
.card,section{{background:white;border:1px solid #d8e0ea;border-radius:8px;padding:16px;margin-top:14px}}
.metric b{{display:block;font-size:25px;margin-top:4px}}.small{{color:#64748b}}.hero .small{{color:#cbd5e1}}
table{{width:100%;border-collapse:collapse}}th,td{{border-bottom:1px solid #e2e8f0;padding:9px;text-align:left}}th{{background:#f8fafc}}
.warn{{border-left:4px solid #f59e0b}}.bad{{border-left:4px solid #ef4444}}.good{{border-left:4px solid #10b981}}
@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><main>
<div class="hero"><h1>ASTT V4.1 Relaxed Fear Exhaustion 검증 리포트</h1><p class="small">V4 후보 0개 문제를 분해하기 위한 PAPER 전용 병목 진단 보고서입니다. 실거래 판단으로 쓰지 않습니다.</p></div>
<div class="grid">
{self._metric("최고 timeframe", str(best.get("timeframe", "")))}
{self._metric("진입 수", f"{best.get('entry_count', 0):,}")}
{self._metric("Profit Factor", f"{best.get('profit_factor', 0):.3f}")}
{self._metric("계좌 수익률", f"{best.get('account_return_pct', 0):.4f}%")}
</div>
<section><h2>1. V4 문제와 V4.1 변경점</h2><p>V4는 가격 lower low와 공포 lower high를 동시에 요구해 표본이 거의 만들어지지 않았다. V4.1은 저점 재시험과 공포 둔화 중 일부 조건을 허용해 먼저 표본 생성 가능성을 확인한다.</p></section>
<section><h2>2. Funnel Report</h2>{self._funnel_table(funnels)}</section>
<section><h2>3. 1m vs 5m 비교</h2>{self._timeframe_table(payload.get("sweep", {}).get("results", []))}</section>
<section><h2>4. Skeptic Guard 진단</h2><p>mode: DIAGNOSTIC / would_block_count: {metrics.get('skeptic_would_block_count', best.get('skeptic_would_block_count', 0))} / blocking_applied_count: {metrics.get('blocking_applied_count', 0)}</p></section>
<section><h2>5. V4 vs V4.1</h2><p>{escape(compare.get('verdict', 'NO_COMPARE'))}</p></section>
<section class="{self._readiness_class(payload.get('live_readiness','LIVE_NOT_ALLOWED'))}"><h2>6. 실전 전환 판정</h2><strong>{escape(payload.get('live_readiness','LIVE_NOT_ALLOWED'))}</strong></section>
<section><h2>7. 다음 실험</h2><ul>{"".join(f"<li>{escape(item)}</li>" for item in payload.get("next_actions", []))}</ul></section>
</main></body></html>"""
        path.write_text(html, encoding="utf-8")

    def _metric(self, label: str, value: str) -> str:
        return f"<div class='card metric'><span class='small'>{escape(label)}</span><b>{escape(value)}</b></div>"

    def _funnel_table(self, funnels: dict) -> str:
        if not funnels:
            return "<p class='small'>퍼널 데이터가 없습니다.</p>"
        rows = []
        for timeframe, funnel in funnels.items():
            for key, value in funnel.items():
                if key == "timeframe":
                    continue
                rows.append(f"<tr><td>{escape(str(timeframe))}</td><td>{escape(str(key))}</td><td>{int(value):,}</td></tr>")
        return "<table><thead><tr><th>timeframe</th><th>stage</th><th>count</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"

    def _timeframe_table(self, rows: list[dict]) -> str:
        if not rows:
            return "<p class='small'>sweep 결과가 없습니다.</p>"
        best_by_tf: dict[str, dict] = {}
        for row in rows:
            tf = row.get("timeframe", "")
            current = best_by_tf.get(tf)
            if current is None or (row.get("entry_count", 0), row.get("profit_factor", 0), row.get("account_return_pct", 0)) > (
                current.get("entry_count", 0),
                current.get("profit_factor", 0),
                current.get("account_return_pct", 0),
            ):
                best_by_tf[tf] = row
        body = "".join(
            f"<tr><td>{escape(tf)}</td><td>{row.get('entry_count',0):,}</td><td>{row.get('win_rate',0)*100:.2f}%</td><td>{row.get('profit_factor',0):.3f}</td><td>{row.get('account_return_pct',0):.4f}%</td></tr>"
            for tf, row in sorted(best_by_tf.items())
        )
        return "<table><thead><tr><th>timeframe</th><th>entry</th><th>win_rate</th><th>PF</th><th>account%</th></tr></thead><tbody>" + body + "</tbody></table>"

    def _readiness_class(self, readiness: str) -> str:
        if readiness == "MICRO_LIVE_READY":
            return "good"
        if readiness == "PAPER_MORE_REQUIRED":
            return "warn"
        return "bad"


def _funnel_rows(funnels: dict) -> str:
    if not funnels:
        return "| 데이터 없음 | 0 |"
    rows = []
    for timeframe, funnel in funnels.items():
        for key, value in funnel.items():
            if key != "timeframe":
                rows.append(f"| {timeframe} / {key} | {int(value):,} |")
    return "\n".join(rows)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
