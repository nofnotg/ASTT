from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


class V673DominanceDataQualityHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        return _build(self.reports_dir, "latest_v673_dominance_data_quality_summary.json", "latest_v673_dominance_data_quality_report.html", "ASTT V6.7.3 Dominance Data Quality", _quality_body)


class V673AgentMatrixHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        return _build(self.reports_dir, "latest_v673_agent_matrix_summary.json", "latest_v673_agent_matrix_report.html", "ASTT V6.7.3 Agent Matrix", _scenario_body)


class V673BearAgentHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        return _build(self.reports_dir, "latest_v673_bear_agent_summary.json", "latest_v673_bear_agent_report.html", "ASTT V6.7.3 Bear Agents", _bear_body)


class V673ScenarioRouterHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        return _build(self.reports_dir, "latest_v673_scenario_router_summary.json", "latest_v673_scenario_router_report.html", "ASTT V6.7.3 Scenario Router", _scenario_body)


class V673HighWatermarkHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        return _build(self.reports_dir, "latest_v673_high_watermark_summary.json", "latest_v673_high_watermark_report.html", "ASTT V6.7.3 High Watermark", _hwm_body)


class V673RejectedScenariosHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        return _build(self.reports_dir, "latest_v673_rejected_scenarios_summary.json", "latest_v673_rejected_scenarios_report.html", "ASTT V6.7.3 Rejected Scenarios", _rejected_body)


class HeadControllerV673ReviewHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        return _build(self.reports_dir, "latest_head_controller_v673_review_summary.json", "latest_head_controller_v673_review_report.html", "ASTT V6.7.3 Head Controller Review", _review_body)


def _build(root: Path, source: str, target: str, title: str, body_fn) -> dict[str, str]:
    data = _read(root / source)
    path = root / target
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_html(title, body_fn(data)), encoding="utf-8")
    return {"html": str(path)}


def _html(title: str, body: str) -> str:
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(title)}</title><style>
body{{margin:0;background:#f8fafc;color:#111827;font-family:Arial,'Malgun Gothic',sans-serif;line-height:1.6}}
header{{background:#111827;color:#fff;padding:28px 22px}}main{{max-width:1180px;margin:auto;padding:22px}}
section{{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin-top:14px}}
table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{border-bottom:1px solid #e5e7eb;padding:8px;text-align:left}}th{{background:#eef2ff}}
.notice{{background:#fff7ed;border-left:5px solid #f97316;padding:12px 14px;border-radius:6px;margin-top:14px}}
</style></head><body><header><h1>{_esc(title)}</h1><p>PAPER research only. No live orders. No auto apply.</p></header><main>
<div class="notice"><strong>Safety:</strong> real_order_enabled=false, live_order_allowed=false, auto_apply_allowed=false.</div>{body}</main></body></html>"""


def _quality_body(data: dict[str, Any]) -> str:
    rows = "".join(
        f"<tr><td>{_esc(tf)}</td><td>{_esc(item.get('exists'))}</td><td>{_esc(item.get('rows'))}</td><td>{_esc(item.get('start'))}</td><td>{_esc(item.get('end'))}</td><td>{_esc(item.get('source_type'))}</td><td>{_esc(item.get('quality'))}</td></tr>"
        for tf, item in data.get("files", {}).items()
    )
    return f"<section><h2>Summary</h2><p>quality: {_esc(data.get('data_quality'))}</p><p>coverage: {_esc(data.get('common_coverage_start'))} ~ {_esc(data.get('common_coverage_end'))}</p><p>fake_data_generated: {_esc(data.get('fake_data_generated'))}</p></section><section><h2>Files</h2><table><tr><th>TF</th><th>Exists</th><th>Rows</th><th>Start</th><th>End</th><th>Source</th><th>Quality</th></tr>{rows}</table></section>"


def _scenario_body(data: dict[str, Any]) -> str:
    return f"<section><h2>Scenario Matrix</h2>{_scenario_table(data.get('scenarios', []))}</section><section><h2>Lookahead Audit</h2><pre>{_esc(json.dumps(data.get('lookahead_audit', data.get('audit', {})), ensure_ascii=False, indent=2))}</pre></section>"


def _bear_body(data: dict[str, Any]) -> str:
    return f"<section><h2>Bear Agents</h2>{_scenario_table(data.get('agents', []))}</section>"


def _hwm_body(data: dict[str, Any]) -> str:
    rows = "".join(f"<tr><td>{_esc(r.get('peak_date'))}</td><td>{_esc(r.get('trough_date'))}</td><td>{_money(r.get('peak_equity'))}</td><td>{_money(r.get('trough_equity'))}</td><td>{_pct(r.get('drawdown_pct'))}</td><td>{_esc(r.get('active_agent'))}</td></tr>" for r in data.get("peak_defense_events", []))
    return f"<section><h2>High Watermark</h2><p>best scenario: {_esc(data.get('best_hwm_scenario'))}</p><p>score: {_num(data.get('high_watermark_preservation_score'))}</p><table><tr><th>Peak</th><th>Trough</th><th>Peak Equity</th><th>Trough Equity</th><th>DD</th><th>Agent</th></tr>{rows}</table></section>"


def _rejected_body(data: dict[str, Any]) -> str:
    rejected = "".join(f"<tr><td>{_esc(r.get('scenario'))}</td><td>{_esc(r.get('reject_reason'))}</td></tr>" for r in data.get("rejected_scenarios", []))
    kept = "".join(f"<tr><td>{_esc(r.get('scenario'))}</td><td>{_esc(r.get('keep_reason'))}</td><td>{_esc(r.get('forward_candidate'))}</td></tr>" for r in data.get("kept_candidates", []))
    return f"<section><h2>Rejected</h2><table><tr><th>Scenario</th><th>Reason</th></tr>{rejected}</table></section><section><h2>Kept</h2><table><tr><th>Scenario</th><th>Reason</th><th>Forward</th></tr>{kept}</table></section>"


def _review_body(data: dict[str, Any]) -> str:
    return f"<section><h2>Final Decision</h2><p>{_esc(data.get('final_decision'))}</p><pre>{_esc(json.dumps(data, ensure_ascii=False, indent=2))}</pre></section>"


def _scenario_table(rows: list[dict[str, Any]]) -> str:
    body = "".join(f"<tr><td>{_esc(r.get('scenario'))}</td><td>{_money(r.get('final_equity_krw'))}</td><td>{_pct(r.get('total_return_pct'))}</td><td>{_pct(r.get('mdd_pct'))}</td><td>{_num(r.get('profit_factor'))}</td><td>{_esc(r.get('trade_count'))}</td><td>{_num(r.get('return_mdd_ratio'))}</td><td>{_esc(r.get('decision'))}</td></tr>" for r in rows if r)
    return f"<table><tr><th>Scenario</th><th>Final Equity</th><th>Return</th><th>MDD</th><th>PF</th><th>Trades</th><th>Return/MDD</th><th>Decision</th></tr>{body}</table>"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _money(value: Any) -> str:
    try:
        return f"{float(value):,.0f} KRW"
    except (TypeError, ValueError):
        return "N/A"


def _pct(value: Any) -> str:
    try:
        return f"{float(value):+.2f}%"
    except (TypeError, ValueError):
        return "N/A"


def _num(value: Any) -> str:
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return "N/A"


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)
