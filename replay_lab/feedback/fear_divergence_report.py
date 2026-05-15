from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from replay_lab.paths import ROOT_DIR, REPLAY_STORE_DIR
from replay_lab.replay.fear_divergence_v4 import latest_fear_divergence_experiment, live_readiness_v4


@dataclass(frozen=True)
class FearDivergenceReportBuilder:
    store_dir: Path = REPLAY_STORE_DIR
    capital_krw: float = 500000
    order_krw: float = 10000
    docs_root: Path = ROOT_DIR / "docs" / "reports"

    @property
    def out_dir(self) -> Path:
        return self.store_dir / "reports" / "fear_divergence_v4"

    def build(self, start_date: str = "2026-01-01", end_date: str | None = None) -> Path:
        end_date = end_date or datetime.utcnow().date().isoformat()
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.docs_root.mkdir(parents=True, exist_ok=True)
        payload = self._payload(start_date, end_date)
        html = self.out_dir / "fear_divergence_v4_report.html"
        json_path = self.out_dir / "fear_divergence_v4_report.json"
        md = self.out_dir / "fear_divergence_v4_report.md"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        md.write_text(self._markdown(payload), encoding="utf-8")
        self._write_html(html, payload)
        (self.docs_root / "latest_fear_divergence_summary.json").write_text(json.dumps(self._summary(payload), ensure_ascii=False, indent=2), encoding="utf-8")
        (self.docs_root / "latest_fear_divergence_report.md").write_text(self._markdown(payload), encoding="utf-8")
        return html

    def _payload(self, start_date: str, end_date: str) -> dict[str, Any]:
        exp = latest_fear_divergence_experiment(self.store_dir)
        metrics = _read_json(exp / "metrics.json") if exp else {}
        sweep = _read_json(self.out_dir / "fear_divergence_sweep_v4.json")
        compare = _read_json(self.out_dir / "fear_divergence_compare_v3.json")
        readiness = metrics.get("live_readiness") or live_readiness_v4(metrics, True)
        return {
            "schema_version": "1.0",
            "generated_at": datetime.utcnow().isoformat(),
            "period": {"start_date": start_date, "end_date": end_date},
            "capital_krw": self.capital_krw,
            "order_krw": self.order_krw,
            "latest_experiment": str(exp) if exp else "",
            "metrics": metrics,
            "sweep": sweep,
            "compare_v3": compare,
            "live_readiness": readiness,
            "next_actions": self._next_actions(metrics, sweep, compare),
        }

    def _summary(self, payload: dict[str, Any]) -> dict[str, Any]:
        metrics = payload.get("metrics", {})
        sweep = payload.get("sweep", {})
        compare = payload.get("compare_v3", {})
        return {
            "schema_version": "1.0",
            "generated_at": payload["generated_at"],
            "period": payload["period"],
            "capital_krw": payload["capital_krw"],
            "order_krw": payload["order_krw"],
            "best_v4_config": sweep.get("best", {}),
            "v4_result": {
                "entry_count": metrics.get("entry_count", 0),
                "win_rate": metrics.get("win_rate", 0.0),
                "profit_factor": metrics.get("profit_factor", 0.0),
                "account_return_pct": metrics.get("account_return_pct", 0.0),
                "max_drawdown_pct": metrics.get("max_drawdown_pct", 0.0),
                "consecutive_loss_max": metrics.get("consecutive_loss_max", 0),
                "skeptic_reject_count": metrics.get("skeptic_reject_count", 0),
            },
            "v3_vs_v4": compare.get("verdict", "NO_COMPARE"),
            "live_readiness": payload.get("live_readiness", "LIVE_NOT_ALLOWED"),
            "next_actions": payload.get("next_actions", []),
        }

    def _next_actions(self, metrics: dict, sweep: dict, compare: dict) -> list[str]:
        actions = []
        if metrics.get("entry_count", 0) < 30:
            actions.append("V4 표본이 30회 미만이면 실전 판단을 금지하고 조건 완화/기간 확장 검증을 먼저 한다.")
        if sweep.get("best", {}).get("status", "").startswith("NO_VALID"):
            actions.append("유효 V4 설정이 없으면 divergence/reentry/support 임계값을 분리해 민감도 실험을 추가한다.")
        if compare.get("verdict") == "V4_INSUFFICIENT_SAMPLE":
            actions.append("V3와의 우열 판단 전에 V4 이벤트 표본을 늘린다.")
        actions.append("V4.1에서 상단 밴드 익절, 1분봉, 15분봉, 청산 방식을 분리 실험한다.")
        return actions

    def _markdown(self, payload: dict[str, Any]) -> str:
        m = payload.get("metrics", {})
        sweep = payload.get("sweep", {})
        compare = payload.get("compare_v3", {})
        return f"""# ASTT V4 공포 소진 다이버전스 검증 리포트

## 1. 전략 개요
급락 후 가격은 낮은 저점을 만들지만 공포 압력이 약해지는 구간을 찾고, 볼린저 하단 내부 복귀와 지지/추세/이평 맥락을 확인합니다.

## 2. VIX 다이버전스 → 코인 공포 오실레이터
VIX Fix, 변동성 공포, 거래량 패닉을 합성해 0~100 공포 점수를 만듭니다.

## 3. 5분봉 기준 검증 결과
- entry_count: {m.get('entry_count', 0)}
- win_rate: {m.get('win_rate', 0) * 100:.2f}%
- profit_factor: {m.get('profit_factor', 0):.4f}
- account_return_pct: {m.get('account_return_pct', 0):.4f}%
- max_drawdown_pct: {m.get('max_drawdown_pct', 0):.4f}%
- consecutive_loss_max: {m.get('consecutive_loss_max', 0)}

## 4. 이평선/매물대/추세선 결합 효과
V4 score는 divergence, bollinger re-entry, body zone, trendline, MA, liquidity를 합산합니다.

## 5. Skeptic Guard가 막은 신호
- skeptic_reject_count: {m.get('skeptic_reject_count', 0)}
- candidate_count: {m.get('candidate_count', 0)}

## 6. V3와 비교
- 판정: {compare.get('verdict', 'NO_COMPARE')}

## 7. 50만 원 시드 기준 실제 주문금액 손익
- total_order_pnl_krw: {m.get('total_order_pnl_krw', 0):,.0f}원
- account_return_pct: {m.get('account_return_pct', 0):.4f}%

## 8. 통과/실패 원인
- sweep best: {sweep.get('best', {})}

## 9. 실전 전환 판정
- {payload.get('live_readiness')}

## 10. 다음 실험
{chr(10).join(f'- {item}' for item in payload.get('next_actions', []))}
"""

    def _write_html(self, path: Path, payload: dict[str, Any]) -> None:
        m = payload.get("metrics", {})
        html = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ASTT V4 공포 소진 다이버전스 검증 리포트</title>
<style>
body{{margin:0;background:#f4f6f8;color:#111827;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif;line-height:1.55}}
main{{max-width:1180px;margin:0 auto;padding:34px 20px 72px}}section,.card{{background:white;border:1px solid #d8e0ea;border-radius:8px;padding:16px;margin-top:14px}}
.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}}.metric b{{display:block;font-size:24px}}table{{width:100%;border-collapse:collapse}}td,th{{border-bottom:1px solid #d8e0ea;padding:8px;text-align:left}}.small{{color:#64748b}}@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><main>
<h1>ASTT V4 공포 소진 다이버전스 검증 리포트</h1>
<p class="small">PAPER 전용 검증입니다. Skeptic Guard가 REJECT한 후보는 진입하지 않습니다.</p>
<div class="grid">
{self._metric('진입', f"{m.get('entry_count',0):,}회")}
{self._metric('승률', f"{m.get('win_rate',0)*100:.2f}%")}
{self._metric('PF', f"{m.get('profit_factor',0):.3f}")}
{self._metric('계좌%', f"{m.get('account_return_pct',0):.4f}%")}
</div>
<section><h2>1. 전략 개요</h2><p>가격 lower low와 공포 lower high를 찾고, 볼린저 하단 내부 복귀와 지지 맥락을 확인합니다.</p></section>
<section><h2>2. 공포 오실레이터</h2><p>VIX Fix, 변동성 공포, 거래량 패닉을 0~100 점수로 합성합니다.</p></section>
<section><h2>3. 검증 결과</h2>{self._table(m)}</section>
<section><h2>4. Skeptic Guard</h2><p>reject_count: {m.get('skeptic_reject_count',0)} / candidate_count: {m.get('candidate_count',0)}</p></section>
<section><h2>5. V3와 비교</h2><p>{escape(payload.get('compare_v3',{}).get('verdict','NO_COMPARE'))}</p></section>
<section><h2>6. 실전 전환 판정</h2><strong>{escape(payload.get('live_readiness','LIVE_NOT_ALLOWED'))}</strong></section>
<section><h2>7. 다음 실험</h2><ul>{"".join(f"<li>{escape(item)}</li>" for item in payload.get("next_actions", []))}</ul></section>
</main></body></html>"""
        path.write_text(html, encoding="utf-8")

    def _metric(self, label: str, value: str) -> str:
        return f"<div class='card metric'><span class='small'>{escape(label)}</span><b>{escape(value)}</b></div>"

    def _table(self, metrics: dict) -> str:
        keys = ["entry_count", "win_rate", "profit_factor", "account_return_pct", "max_drawdown_pct", "consecutive_loss_max", "total_order_pnl_krw", "live_readiness"]
        return "<table><tbody>" + "".join(f"<tr><th>{key}</th><td>{escape(str(metrics.get(key, '')))}</td></tr>" for key in keys) + "</tbody></table>"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
