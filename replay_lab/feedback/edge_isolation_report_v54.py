from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from replay_lab.paths import ROOT_DIR, REPLAY_STORE_DIR
from replay_lab.replay.edge_isolation_v54 import latest_edge_isolation_v54_experiment
from replay_lab.research.trade_review_dataset_v54 import export_trade_review_v54


@dataclass(frozen=True)
class EdgeIsolationV54ReportBuilder:
    store_dir: Path = REPLAY_STORE_DIR
    docs_root: Path = ROOT_DIR / "docs" / "reports"

    @property
    def out_dir(self) -> Path:
        return self.store_dir / "reports" / "edge_isolation_v54"

    def build(self, start_date: str = "2026-01-01", end_date: str | None = None) -> Path:
        end_date = end_date or datetime.utcnow().date().isoformat()
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.docs_root.mkdir(parents=True, exist_ok=True)
        export_trade_review_v54(datetime.fromisoformat(start_date).date(), datetime.fromisoformat(end_date).date(), store_dir=self.store_dir, docs_root=self.docs_root)
        payload = self._payload(start_date, end_date)
        html = self.out_dir / "edge_isolation_v54_report.html"
        md = self.out_dir / "edge_isolation_v54_report.md"
        js = self.out_dir / "edge_isolation_v54_report.json"
        js.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        md.write_text(self._markdown(payload), encoding="utf-8")
        html.write_text(self._html(payload), encoding="utf-8")
        (self.docs_root / "latest_edge_isolation_v54_summary.json").write_text(json.dumps(self._summary(payload), ensure_ascii=False, indent=2), encoding="utf-8")
        (self.docs_root / "latest_edge_isolation_v54_report.md").write_text(self._markdown(payload), encoding="utf-8")
        return html

    def _payload(self, start_date: str, end_date: str) -> dict:
        exp = latest_edge_isolation_v54_experiment(self.store_dir)
        metrics = json.loads((exp / "metrics.json").read_text(encoding="utf-8")) if exp else {}
        zone = _read_json(self.out_dir / "zone_quality_research_v54.json")
        trades = pd.read_parquet(exp / "edge_trades.parquet") if exp and (exp / "edge_trades.parquet").exists() else pd.DataFrame()
        insights = _insights(metrics)
        return {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "period": {"start_date": start_date, "end_date": end_date}, "metrics": metrics, "zone_quality": zone, "trade_count": int(len(trades)), "live_readiness": metrics.get("live_readiness", "LIVE_NOT_ALLOWED"), "insights": insights}

    def _summary(self, payload: dict) -> dict:
        m = payload.get("metrics", {})
        return {"schema_version": "1.0", "generated_at": payload["generated_at"], "period": payload["period"], "strategy_results": m.get("strategy_results", []), "exit_model_results": m.get("exit_model_results", []), "module_ablation_results": m.get("module_ablation_results", []), "best_simple_strategy": m.get("best_simple_strategy", {}), "zone_quality": payload.get("zone_quality", {}), "trade_review_count": m.get("trade_review_count", 0), "live_readiness": payload.get("live_readiness"), "insights": payload.get("insights", [])}

    def _markdown(self, payload: dict) -> str:
        m = payload.get("metrics", {})
        strategy_rows = "\n".join(f"| {r.get('strategy_id')} | {r.get('entry_count')} | {r.get('win_rate',0)*100:.2f}% | {r.get('profit_factor',0):.4f} | {r.get('expectancy_pct',0):.4f}% | {r.get('max_drawdown_pct',0):.4f}% | {r.get('consecutive_loss_max',0)} |" for r in m.get("strategy_results", []))
        exit_rows = "\n".join(f"| {r.get('exit_model')} | {r.get('entry_count')} | {r.get('win_rate',0)*100:.2f}% | {r.get('profit_factor',0):.4f} | {r.get('avg_win_pct',0):.4f}% | {r.get('avg_loss_pct',0):.4f}% | {r.get('expectancy_pct',0):.4f}% |" for r in m.get("exit_model_results", []))
        ablation_rows = "\n".join(f"| {r.get('module_stack')} | {r.get('entry_count')} | {r.get('profit_factor',0):.4f} | {r.get('expectancy_pct',0):.4f}% | {r.get('max_drawdown_pct',0):.4f}% |" for r in m.get("module_ablation_results", []))
        return f"""# ASTT V5.4 Edge Isolation & Strategy Simplification Report

## 1. V5.3 Failure Summary
V5.3 mixed MTF, zone, target, runner, allocation, and compounding. The result was LIVE_NOT_ALLOWED. V5.4 disables full_seed, grade allocation, runner, and compounding for the base comparison.

## 2. Strategy Isolation
| Strategy | Entry | Win Rate | PF | Expectancy | MDD | Consecutive Loss |
|---|---:|---:|---:|---:|---:|---:|
{strategy_rows}

## 3. Exit Model Compare
| Exit Model | Entry | Win Rate | PF | Avg Win | Avg Loss | Expectancy |
|---|---:|---:|---:|---:|---:|---:|
{exit_rows}

## 4. Module Ablation
| Module Stack | Entry | PF | Expectancy | MDD |
|---|---:|---:|---:|---:|
{ablation_rows}

## 5. Zone Quality V54
- zone_count: {payload.get('zone_quality', {}).get('zone_count', 0)}
- quality_grade_performance: {payload.get('zone_quality', {}).get('quality_grade_performance', [])}

## 6. Trade Review Dataset
- review row count: {m.get('trade_review_count', 0)}
- markdown: docs/reports/trade_review_v54.md
- csv: docs/reports/trade_review_v54.csv

## 7. Live Readiness
{payload.get('live_readiness', 'LIVE_NOT_ALLOWED')}

## 8. Insights
{chr(10).join(f'- {item}' for item in payload.get('insights', []))}
"""

    def _html(self, payload: dict) -> str:
        md = self._markdown(payload)
        return f"<html><head><meta charset='utf-8'><title>ASTT V5.4 Edge Isolation</title><style>body{{font-family:Segoe UI,Noto Sans KR,sans-serif;max-width:1100px;margin:32px auto;background:#f6f8fb;color:#111}}pre,section{{background:white;border:1px solid #ddd;border-radius:8px;padding:16px;white-space:pre-wrap}}</style></head><body><section>{md}</section></body></html>"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _insights(metrics: dict) -> list[str]:
    best = metrics.get("best_simple_strategy", {})
    items = []
    if not metrics.get("full_validation_completed", False):
        items.append("Full coverage is not proven from the available seed, so live transition remains blocked.")
    if best.get("profit_factor", 0) >= 1.1 and best.get("entry_count", 0) >= 30:
        items.append(f"Best isolated strategy is {best.get('strategy_id')} with a positive simple-edge signal.")
    else:
        items.append("No isolated strategy has enough PF and sample quality to claim edge.")
    items.append("V5.4 intentionally does not output MICRO_LIVE_READY.")
    return items
