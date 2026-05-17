from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd

from replay_lab.paths import ROOT_DIR, REPLAY_STORE_DIR
from replay_lab.replay.fractal_v53 import latest_fractal_v53_experiment, live_readiness_v53


@dataclass(frozen=True)
class FractalV53ReportBuilder:
    store_dir: Path = REPLAY_STORE_DIR
    docs_root: Path = ROOT_DIR / "docs" / "reports"
    initial_equity_krw: float = 500000

    @property
    def out_dir(self) -> Path:
        return self.store_dir / "reports" / "fractal_v53"

    def build(self, start_date: str = "2026-01-01", end_date: str | None = None) -> Path:
        end_date = end_date or datetime.utcnow().date().isoformat()
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.docs_root.mkdir(parents=True, exist_ok=True)
        payload = self._payload(start_date, end_date)
        html = self.out_dir / "fractal_v53_report.html"
        json_path = self.out_dir / "fractal_v53_report.json"
        md = self.out_dir / "fractal_v53_report.md"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        md.write_text(self._markdown(payload), encoding="utf-8")
        html.write_text(self._html(payload), encoding="utf-8")
        (self.docs_root / "latest_fractal_v53_summary.json").write_text(json.dumps(self._summary(payload), ensure_ascii=False, indent=2), encoding="utf-8")
        (self.docs_root / "latest_fractal_v53_report.md").write_text(self._markdown(payload), encoding="utf-8")
        return html

    def _payload(self, start_date: str, end_date: str) -> dict[str, Any]:
        exp = latest_fractal_v53_experiment(self.store_dir)
        metrics = _read_json(exp / "metrics.json") if exp else {}
        trades = pd.read_parquet(exp / "paper_trades.parquet") if exp and (exp / "paper_trades.parquet").exists() else pd.DataFrame()
        allocation = _read_json(self.out_dir / "allocation_diagnostic_v53.json")
        zone = _read_json(self.out_dir / "zone_reaction_validation_v53.json")
        runner = _read_json(self.out_dir / "runner_exit_sweep_v53.json")
        wf = _read_json(self.out_dir / "fractal_v53_walk_forward.json")
        cache = _read_json(self.out_dir / "cache_benchmark_v53.json")
        compare = _allocation_compare(trades, self.initial_equity_krw)
        readiness = live_readiness_v53(metrics, wf, zone, runner)
        metrics["live_readiness"] = readiness
        return {
            "schema_version": "1.0",
            "generated_at": datetime.utcnow().isoformat(),
            "period": {"start_date": start_date, "end_date": end_date},
            "metrics": metrics,
            "cache_benchmark": cache,
            "allocation_diagnostic": allocation,
            "zone_reaction_validation": zone,
            "runner_exit_sweep": runner,
            "walk_forward": wf,
            "allocation_compare": compare,
            "trades": trades.head(300).to_dict("records") if not trades.empty else [],
            "live_readiness": readiness,
            "insights": _insights(metrics, allocation, zone, runner, wf, compare),
        }

    def _summary(self, payload: dict) -> dict:
        m = payload.get("metrics", {})
        return {
            "schema_version": "1.0",
            "generated_at": payload["generated_at"],
            "period": payload["period"],
            "fractal_v53_result": {k: m.get(k, 0) for k in ["entry_count", "win_rate", "profit_factor", "initial_equity_krw", "final_equity_krw", "equity_return_pct", "total_pnl_krw", "max_drawdown_pct", "consecutive_loss_max", "full_validation_completed"]},
            "cache_benchmark": payload.get("cache_benchmark", {}),
            "allocation_diagnostic": {k: payload.get("allocation_diagnostic", {}).get(k) for k in ["good_trade_underallocated_count", "bad_trade_overallocated_count", "allocation_alpha_krw", "summary"]},
            "zone_reaction_validation": {k: payload.get("zone_reaction_validation", {}).get(k) for k in ["zone_count", "bounce_success_rate", "rejection_success_rate", "breakdown_fail_rate", "no_reaction_rate", "zone_strength_correlation", "validation_passed"]},
            "runner_exit_sweep": {k: payload.get("runner_exit_sweep", {}).get(k) for k in ["best_runner_model", "best_trailing_model", "best_runner_contribution_krw"]},
            "walk_forward": {k: payload.get("walk_forward", {}).get(k) for k in ["window_count", "positive_window_ratio", "avg_test_profit_factor", "median_test_profit_factor", "avg_test_return_pct", "worst_window_mdd_pct", "stable"]},
            "allocation_compare": payload.get("allocation_compare", []),
            "live_readiness": payload.get("live_readiness", "LIVE_NOT_ALLOWED"),
            "insights": payload.get("insights", []),
        }

    def _markdown(self, payload: dict) -> str:
        m = payload["metrics"]
        cache = payload.get("cache_benchmark", {})
        alloc = payload.get("allocation_diagnostic", {})
        zone = payload.get("zone_reaction_validation", {})
        runner = payload.get("runner_exit_sweep", {})
        wf = payload.get("walk_forward", {})
        compare_rows = "\n".join(
            f"| {row['model']} | {row['entry_count']} | {row['profit_factor']:.4f} | {row['final_equity_krw']:,.0f} | {row['return_pct']:.4f}% | {row['max_drawdown_pct']:.4f}% | {row['consecutive_loss_max']} |"
            for row in payload.get("allocation_compare", [])
        )
        grade_rows = "\n".join(
            f"| {row.get('grade')} | {row.get('entry_count',0)} | {row.get('win_rate',0)*100:.2f}% | {row.get('profit_factor',0):.4f} | {row.get('avg_allocation_pct',0):.3f} | {row.get('total_pnl_krw',0):,.0f} | {row.get('allocation_alpha_krw',0):,.0f} |"
            for row in alloc.get("grade_table", [])
        )
        return f"""# ASTT V5.3 Full Validation / Allocation / Zone Reaction / Runner Report

## 1. V5.2 to V5.3 Change Summary
V5.3 does not add a new entry signal. It adds validation speed, allocation diagnostics, stricter zone reaction labels, runner/trailing diagnostics, and wider walk-forward checks.

## 2. Final V5.3 Result
- period: {payload['period']['start_date']} ~ {payload['period']['end_date']}
- entry_count: {m.get('entry_count', 0)}
- win_rate: {m.get('win_rate', 0)*100:.2f}%
- profit_factor: {m.get('profit_factor', 0):.4f}
- initial_equity_krw: {m.get('initial_equity_krw', 0):,.0f}
- final_equity_krw: {m.get('final_equity_krw', 0):,.0f}
- equity_return_pct: {m.get('equity_return_pct', 0):.4f}%
- max_drawdown_pct: {m.get('max_drawdown_pct', 0):.4f}%
- consecutive_loss_max: {m.get('consecutive_loss_max', 0)}
- full_validation_completed: {m.get('full_validation_completed', False)}

## 3. Cache Benchmark
- cache_hit_rate: {cache.get('cache_hit_rate', 0):.4f}
- cache_off_time: {cache.get('cache_off_time', 0):.4f}s
- cache_on_time: {cache.get('cache_on_time', 0):.4f}s
- speedup_ratio: {cache.get('speedup_ratio', 0):.2f}
- full_validation_estimated_time: {cache.get('full_validation_estimated_time', 0):.2f}s

## 4. Allocation Diagnostic
| Grade | Entry | Win Rate | PF | Avg Alloc | Total PnL | Allocation Alpha |
|---|---:|---:|---:|---:|---:|---:|
{grade_rows}

- good_trade_underallocated_count: {alloc.get('good_trade_underallocated_count', 0)}
- bad_trade_overallocated_count: {alloc.get('bad_trade_overallocated_count', 0)}
- allocation_alpha_krw: {alloc.get('allocation_alpha_krw', 0):,.0f}
- summary: {alloc.get('summary', '')}

## 5. Zone Reaction Validation
- zone_count: {zone.get('zone_count', 0)}
- bounce_success_rate: {zone.get('bounce_success_rate', 0):.4f}
- rejection_success_rate: {zone.get('rejection_success_rate', 0):.4f}
- breakdown_fail_rate: {zone.get('breakdown_fail_rate', 0):.4f}
- no_reaction_rate: {zone.get('no_reaction_rate', 0):.4f}
- zone_strength_correlation: {zone.get('zone_strength_correlation', 0):.4f}
- validation_passed: {zone.get('validation_passed', False)}

## 6. Runner / Trailing Sweep
- best_runner_model: {runner.get('best_runner_model', '')}
- best_trailing_model: {runner.get('best_trailing_model', '')}
- best_runner_contribution_krw: {runner.get('best_runner_contribution_krw', 0):,.0f}

## 7. Walk-forward
- window_count: {wf.get('window_count', 0)}
- positive_window_ratio: {wf.get('positive_window_ratio', 0):.4f}
- avg_test_profit_factor: {wf.get('avg_test_profit_factor', 0):.4f}
- median_test_profit_factor: {wf.get('median_test_profit_factor', 0):.4f}
- avg_test_return_pct: {wf.get('avg_test_return_pct', 0):.4f}%
- worst_window_mdd_pct: {wf.get('worst_window_mdd_pct', 0):.4f}%
- stable: {wf.get('stable', False)}

## 8. Fixed 10k vs Full Seed vs Grade-Based V53
| Model | Entry | PF | Final Equity | Return % | MDD | Consecutive Loss |
|---|---:|---:|---:|---:|---:|---:|
{compare_rows}

## 9. Live Readiness
{payload.get('live_readiness', 'LIVE_NOT_ALLOWED')}

## 10. Insights
{chr(10).join(f'- {item}' for item in payload.get('insights', []))}
"""

    def _html(self, payload: dict) -> str:
        m = payload["metrics"]
        trades = payload.get("trades", [])[:120]
        cards = [
            ("Entry", m.get("entry_count", 0)),
            ("PF", f"{m.get('profit_factor', 0):.3f}"),
            ("Final Equity", f"{m.get('final_equity_krw', 0):,.0f} KRW"),
            ("Return", f"{m.get('equity_return_pct', 0):.3f}%"),
            ("Full Validation", str(m.get("full_validation_completed", False))),
            ("Readiness", payload.get("live_readiness", "LIVE_NOT_ALLOWED")),
        ]
        card_html = "".join(f"<div class='card'><span>{escape(str(k))}</span><strong>{escape(str(v))}</strong></div>" for k, v in cards)
        trade_rows = "".join(
            f"<tr><td>{escape(str(t.get('date_kst','')))}</td><td>{escape(str(t.get('market','')))}</td><td>{escape(str(t.get('entry_time_kst','')))}</td><td>{float(t.get('realized_pnl_pct',0)):.3f}%</td><td>{float(t.get('allocation_pct',0)):.3f}</td><td>{float(t.get('trade_pnl_krw',0)):,.0f}</td><td>{float(t.get('equity_after_trade',0)):,.0f}</td><td>{escape(str(t.get('runner_exit_reason','')))}</td></tr>"
            for t in trades
        )
        insight_items = "".join(f"<li>{escape(item)}</li>" for item in payload.get("insights", []))
        return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>ASTT V5.3 Report</title><style>body{{margin:0;background:#eef3f8;color:#172033;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif}}main{{max-width:1240px;margin:0 auto;padding:32px 20px}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}.card,section{{background:#fff;border:1px solid #d6dee8;border-radius:8px;padding:16px}}.card span{{display:block;color:#667085;font-size:13px}}.card strong{{font-size:22px}}section{{margin-top:14px}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{border-bottom:1px solid #e7edf3;padding:8px;text-align:left}}.badge{{display:inline-block;padding:6px 10px;border-radius:999px;background:#172033;color:white}}@media(max-width:840px){{.grid{{grid-template-columns:1fr}}}}</style></head><body><main><h1>ASTT V5.3 검증 리포트</h1><p class="badge">{escape(payload.get('live_readiness','LIVE_NOT_ALLOWED'))}</p><div class="grid">{card_html}</div><section><h2>핵심 인사이트</h2><ul>{insight_items}</ul></section><section><h2>거래별 상세</h2><table><thead><tr><th>Date</th><th>Market</th><th>Entry Time</th><th>PnL %</th><th>Allocation</th><th>PnL KRW</th><th>Equity</th><th>Runner Exit</th></tr></thead><tbody>{trade_rows}</tbody></table></section></main></body></html>"""


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _allocation_compare(trades: pd.DataFrame, initial: float) -> list[dict]:
    if trades.empty:
        return []
    pct = trades["realized_pnl_pct"].astype(float).tolist()
    return [
        _simulate_model("fixed_10k", pct, [min(1.0, 10000 / initial)] * len(pct), initial),
        _simulate_model("full_seed", pct, [1.0] * len(pct), initial),
        _simulate_model("grade_based_v53", pct, trades["allocation_pct"].astype(float).tolist(), initial),
    ]


def _simulate_model(name: str, pnls: list[float], allocations: list[float], initial: float) -> dict:
    equity = initial
    peak = initial
    mdd = 0.0
    streak = 0
    max_streak = 0
    money_rows = []
    for pnl_pct, alloc in zip(pnls, allocations):
        money = equity * alloc * pnl_pct / 100
        equity += money
        peak = max(peak, equity)
        mdd = min(mdd, (equity - peak) / peak * 100 if peak else 0.0)
        streak = streak + 1 if money < 0 else 0
        max_streak = max(max_streak, streak)
        money_rows.append(money)
    gp = sum(x for x in money_rows if x > 0)
    gl = abs(sum(x for x in money_rows if x < 0))
    return {"model": name, "entry_count": len(pnls), "profit_factor": gp / gl if gl else (999.0 if gp else 0.0), "final_equity_krw": equity, "return_pct": (equity - initial) / initial * 100 if initial else 0.0, "max_drawdown_pct": mdd, "consecutive_loss_max": max_streak}


def _insights(metrics: dict, allocation: dict, zone: dict, runner: dict, wf: dict, compare: list[dict]) -> list[str]:
    items = []
    if not metrics.get("full_validation_completed", False):
        items.append("Full top50 coverage was not proven from the available V5.2 seed, so MICRO_LIVE_READY is blocked.")
    if allocation.get("allocation_alpha_krw", 0) < 0:
        items.append("Grade-based allocation reduced performance versus full-seed counterfactual; grade logic is still not reliable enough.")
    else:
        items.append("Grade-based allocation added defensive alpha versus full-seed counterfactual in this replay sample.")
    if zone.get("validation_passed"):
        items.append("Zone reaction labels show enough bounce/reaction evidence to keep zone targeting in the next experiment.")
    else:
        items.append("Zone reaction validation is not strong enough yet; zone strength needs more discriminating labels.")
    if runner.get("best_runner_contribution_krw", 0) > 0:
        items.append("Runner/trailing produced positive contribution in the diagnostic sweep, but it still needs walk-forward confirmation.")
    else:
        items.append("Runner did not add positive contribution, so simpler exits remain a valid baseline.")
    if not wf.get("stable", False):
        items.append("Walk-forward is not stable; this is the main blocker for any live transition.")
    if compare:
        best = max(compare, key=lambda row: row.get("final_equity_krw", 0))
        items.append(f"Best allocation model in the current comparison: {best.get('model')}.")
    return items
