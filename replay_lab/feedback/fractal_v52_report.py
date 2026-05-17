from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from replay_lab.paths import ROOT_DIR, REPLAY_STORE_DIR
from replay_lab.replay.fractal_v52 import latest_fractal_v52_experiment, live_readiness_v52


@dataclass(frozen=True)
class FractalV52ReportBuilder:
    store_dir: Path = REPLAY_STORE_DIR
    docs_root: Path = ROOT_DIR / "docs" / "reports"
    initial_equity_krw: float = 500000

    @property
    def out_dir(self) -> Path:
        return self.store_dir / "reports" / "fractal_v52"

    def build(self, start_date: str = "2026-01-01", end_date: str | None = None) -> Path:
        end_date = end_date or datetime.utcnow().date().isoformat()
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.docs_root.mkdir(parents=True, exist_ok=True)
        payload = self._payload(start_date, end_date)
        html = self.out_dir / "fractal_v52_report.html"
        json_path = self.out_dir / "fractal_v52_report.json"
        md = self.out_dir / "fractal_v52_report.md"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        md.write_text(self._markdown(payload), encoding="utf-8")
        self._write_html(html, payload)
        (self.docs_root / "latest_fractal_v52_summary.json").write_text(json.dumps(self._summary(payload), ensure_ascii=False, indent=2), encoding="utf-8")
        (self.docs_root / "latest_fractal_v52_report.md").write_text(self._markdown(payload), encoding="utf-8")
        return html

    def _payload(self, start_date: str, end_date: str) -> dict[str, Any]:
        exp = latest_fractal_v52_experiment(self.store_dir)
        metrics = _read_json(exp / "metrics.json") if exp else {}
        trades = []
        if exp and (exp / "paper_trades.parquet").exists():
            import pandas as pd

            trades = pd.read_parquet(exp / "paper_trades.parquet").to_dict("records")
        zone = _read_json(self.out_dir / "zone_engine_validation_v52.json")
        compare = _read_json(self.out_dir / "full_seed_compounding_compare_v52.json")
        wf = _read_json(self.out_dir / "fractal_v52_walk_forward.json")
        readiness = live_readiness_v52(metrics, full_period_completed=False, walk_forward_completed=bool(wf.get("windows")))
        return {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "period": {"start_date": start_date, "end_date": end_date}, "metrics": metrics, "trades": trades[:200], "zone_validation": zone, "full_seed_compare": compare, "walk_forward": wf, "live_readiness": readiness, "insights": self._insights(metrics, zone, compare, wf)}

    def _summary(self, payload: dict) -> dict:
        m = payload.get("metrics", {})
        return {"schema_version": "1.0", "generated_at": payload["generated_at"], "period": payload["period"], "fractal_v52_result": {k: m.get(k, 0) for k in ["entry_count", "win_rate", "profit_factor", "initial_equity_krw", "final_equity_krw", "equity_return_pct", "total_pnl_krw", "max_drawdown_pct", "consecutive_loss_max"]}, "zone_validation": payload.get("zone_validation", {}), "best_allocation_model": payload.get("full_seed_compare", {}).get("best_allocation_model", ""), "walk_forward": {k: payload.get("walk_forward", {}).get(k) for k in ["avg_test_profit_factor", "avg_test_return_pct", "worst_window_mdd_pct", "stable"]}, "live_readiness": payload.get("live_readiness"), "insights": payload.get("insights", [])}

    def _insights(self, metrics: dict, zone: dict, compare: dict, wf: dict) -> list[str]:
        items = []
        if metrics.get("entry_count", 0) < 30:
            items.append("entry_count가 30 미만이면 full-seed 성과는 참고값이며 실전 판단 불가다.")
        if metrics.get("final_equity_krw", 0) <= metrics.get("initial_equity_krw", 0):
            items.append("복리 equity가 초기자본을 넘지 못하면 position sizing보다 신호/청산 개선이 우선이다.")
        if zone:
            items.append("Zone validation은 현재 OHLCV proxy 기반이며, 추후 실제 반응 라벨을 보강해야 한다.")
        if compare.get("best_allocation_model"):
            items.append(f"현재 비교에서 가장 나은 allocation model은 {compare.get('best_allocation_model')}이다.")
        if not wf.get("stable"):
            items.append("walk-forward 안정성이 부족하거나 전체 window가 부족하면 MICRO_LIVE_READY 금지다.")
        return items

    def _markdown(self, payload: dict) -> str:
        m = payload.get("metrics", {})
        z = payload.get("zone_validation", {})
        wf = payload.get("walk_forward", {})
        return f"""# ASTT V5.2 Fractal MTF + BTC Dominance + Zone Target + Full-Seed Compounding 검증 리포트

## 1. V5.2 전략 개요
V5.2는 V5의 MTF 신호 위에 BTC regime, zone target space, dynamic exit, full-seed position sizing, compounding portfolio를 얹은 PAPER 전용 검증이다.

## 2. Full-Seed Compounding 결과
- entry_count: {m.get('entry_count', 0)}
- win_rate: {m.get('win_rate', 0) * 100:.2f}%
- profit_factor: {m.get('profit_factor', 0):.4f}
- initial_equity_krw: {m.get('initial_equity_krw', 0):,.0f}
- final_equity_krw: {m.get('final_equity_krw', 0):,.0f}
- equity_return_pct: {m.get('equity_return_pct', 0):.4f}%
- max_drawdown_pct: {m.get('max_drawdown_pct', 0):.4f}%
- consecutive_loss_max: {m.get('consecutive_loss_max', 0)}

## 3. Zone Engine 검증
- zone_count: {z.get('zone_count', 0)}
- demand_zone_bounce_rate: {z.get('demand_zone_bounce_rate', 0):.4f}
- supply_zone_rejection_rate: {z.get('supply_zone_rejection_rate', 0):.4f}
- zone_target_hit_rate: {z.get('zone_target_hit_rate', 0):.4f}

## 4. Walk-forward
- window_count: {len(wf.get('windows', []))}
- avg_test_profit_factor: {wf.get('avg_test_profit_factor', 0):.4f}
- avg_test_return_pct: {wf.get('avg_test_return_pct', 0):.4f}
- stable: {wf.get('stable', False)}

## 5. 실전 전환 판정
- {payload.get('live_readiness', 'LIVE_NOT_ALLOWED')}

## 6. 인사이트
{chr(10).join(f'- {item}' for item in payload.get('insights', []))}
"""

    def _write_html(self, path: Path, payload: dict) -> None:
        m = payload.get("metrics", {})
        rows = payload.get("trades", [])[:80]
        table = "".join(
            f"<tr><td>{escape(str(r.get('date_kst','')))}</td><td>{escape(str(r.get('market','')))}</td><td>{escape(str(r.get('entry_time_kst','')))}</td><td>{r.get('entry_price',0):.4f}</td><td>{escape(str(r.get('weekly_state','')))}</td><td>{escape(str(r.get('fractal_state','')))}</td><td>{escape(str(r.get('btc_regime','')))}</td><td>{r.get('target_1',0):.4f}</td><td>{r.get('target_space_pct',0):.3f}%</td><td>{escape(str(r.get('signal_grade','')))}</td><td>{r.get('allocation_pct',0):.2f}</td><td>{r.get('position_size_krw',0):,.0f}</td><td>{r.get('realized_pnl_pct',0):.3f}%</td><td>{r.get('trade_pnl_krw',0):,.0f}</td><td>{r.get('equity_after_trade',0):,.0f}</td><td>{escape(str(r.get('exit_reason','')))}</td></tr>"
            for r in rows
        )
        html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>ASTT V5.2 Fractal MTF Report</title><style>body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif;background:#f4f7fb;color:#111827;margin:0}}main{{max-width:1280px;margin:auto;padding:32px 20px}}section,.card{{background:white;border:1px solid #d8e0ea;border-radius:8px;padding:16px;margin-top:14px}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{border-bottom:1px solid #e5e7eb;padding:7px;text-align:left}}@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}</style></head><body><main><h1>ASTT V5.2 Fractal MTF + Zone Target + Full-Seed Compounding 검증 리포트</h1><div class="grid"><div class="card">Entry<br><b>{m.get('entry_count',0)}</b></div><div class="card">PF<br><b>{m.get('profit_factor',0):.3f}</b></div><div class="card">Final Equity<br><b>{m.get('final_equity_krw',0):,.0f}원</b></div><div class="card">Return<br><b>{m.get('equity_return_pct',0):.3f}%</b></div></div><section><h2>거래별 상세 표</h2><table><thead><tr><th>date</th><th>market</th><th>entry_time</th><th>entry</th><th>weekly</th><th>fractal</th><th>btc</th><th>target1</th><th>space</th><th>grade</th><th>alloc</th><th>size</th><th>pnl%</th><th>pnl</th><th>equity</th><th>exit</th></tr></thead><tbody>{table}</tbody></table></section><section><h2>실전 전환 판정</h2><strong>{escape(payload.get('live_readiness','LIVE_NOT_ALLOWED'))}</strong></section></main></body></html>"""
        path.write_text(html, encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
