from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from paper_runtime.live_order_guard import assert_live_orders_disabled
from paper_runtime.paper_runtime_schema import safety_flags


ACTIVE_ROUTE = "LG_V2_BALANCED_PLUS_DOM_GATE"
SHADOW_ROUTES = [
    "BEAR_ROUTER_V685_WINDOW_AWARE_SHADOW",
    "BEAR_ROUTER_V684_SHADOW",
    "LG_COMBINED_GUARD",
    "LG_M3_PF0.8_DD8",
    "BASE_BALANCED",
    "BASE_ROLLING",
]
RESEARCH_ROUTES = [
    "LG_ATR_STOP",
    "ATR_TRAILING_STOP",
    "ATR_POSITION_SIZING",
    "BEAR_BOUNCE_CURRENT",
    "SRR_LOW_SAMPLE",
    "BTCDOM_HARD_BLOCK_ONLY",
    "MA_HARD_FILTER_ONLY",
    "SINGLE_INDICATOR_ENTRY",
]
ALIASES = {
    "LG_V2_BALANCED_PLUS_DOM_GATE": "LGv2-DOM",
    "LG_M3_PF0.8_DD8": "LG-M3",
    "BEAR_ROUTER_V685_WINDOW_AWARE_SHADOW": "Bear-V685",
    "BEAR_ROUTER_V684_SHADOW": "Bear-V684",
    "LG_COMBINED_GUARD": "LG-Combo",
    "BASE_BALANCED": "Balanced",
    "BASE_ROLLING": "Rolling",
}
ALLOWED_ACTIONS = {
    "REPORT_ONLY",
    "SHADOW_EXPERIMENT",
    "PARAM_SENSITIVITY_TEST",
    "DASHBOARD_WARNING",
    "MANUAL_REVIEW",
    "DEPRECATED_CANDIDATE",
}


def read_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return {}
    return json.loads(p.read_text(encoding="utf-8-sig"))


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    assert_live_orders_disabled()
    payload = {
        **payload,
        "generated_at": payload.get("generated_at") or datetime.utcnow().isoformat(),
        **safety_flags(),
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return payload


def write_html(path: str | Path, title: str, sections: list[tuple[str, Any]]) -> str:
    assert_live_orders_disabled()
    rows = [
        "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\">",
        f"<title>{html.escape(title)}</title>",
        "<style>body{font-family:Arial,'Malgun Gothic',sans-serif;margin:28px;background:#f7f8fa;color:#17202a}"
        "section{background:white;border:1px solid #dde2e8;border-radius:8px;padding:18px;margin:14px 0}"
        "table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid #e5e9ef;padding:8px;text-align:left}"
        "th{background:#f0f3f7}.safe{color:#087f5b;font-weight:700}.warn{color:#b08900;font-weight:700}"
        "pre{white-space:pre-wrap;background:#f6f8fa;padding:12px;border-radius:6px}</style></head><body>",
        f"<h1>{html.escape(title)}</h1>",
        "<p class=\"safe\">LIVE_NOT_ALLOWED / PAPER_ONLY / manual review required</p>",
    ]
    for heading, body in sections:
        rows.append(f"<section><h2>{html.escape(heading)}</h2>{render_html_body(body)}</section>")
    rows.append("</body></html>")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("".join(rows), encoding="utf-8")
    return str(path)


def render_html_body(body: Any) -> str:
    if isinstance(body, list) and body and isinstance(body[0], dict):
        keys = list(dict.fromkeys(key for row in body[:50] for key in row.keys()))
        head = "".join(f"<th>{html.escape(str(key))}</th>" for key in keys)
        trs = []
        for row in body[:200]:
            trs.append("<tr>" + "".join(f"<td>{html.escape(str(row.get(key, '-')))}</td>" for key in keys) + "</tr>")
        return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(trs)}</tbody></table>"
    return f"<pre>{html.escape(json.dumps(body, ensure_ascii=False, indent=2, default=str))}</pre>"


def route_label(route_id: str | None) -> str:
    if not route_id:
        return "-"
    return ALIASES.get(route_id, route_id.replace("_", "-")[:22])


def load_context(reports_dir: str | Path = "docs/reports", data_dir: str | Path = "data/paper") -> dict[str, Any]:
    reports = Path(reports_dir)
    data = Path(data_dir)
    backfill = read_json(reports / "latest_v683_backfill_20260101_summary.json")
    runtime = read_json(reports / "latest_v686_active_shadow_runtime_summary.json")
    trades = read_jsonl(data / "journal" / "paper_trades.jsonl")
    decisions = read_jsonl(data / "journal" / "paper_decisions.jsonl")
    forward_events, forward_summary = load_forward_candidates()
    return {
        "reports": reports,
        "data": data,
        "backfill": backfill,
        "runtime": runtime,
        "trades": trades,
        "decisions": decisions,
        "forward_events": forward_events,
        "forward_summary": forward_summary,
    }


def load_forward_candidates(root: str | Path = "replay_store/sessions/forward_ws_v554") -> tuple[list[dict[str, Any]], dict[str, Any]]:
    base = Path(root)
    summaries = sorted(base.glob("*/session_summary.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for summary_path in summaries:
        summary = read_json(summary_path)
        if not summary.get("session_id"):
            continue
        events = summary.get("candidate_events")
        if not isinstance(events, list):
            event_path = summary_path.parent / "candidate_events.json"
            events = json.loads(event_path.read_text(encoding="utf-8-sig")) if event_path.exists() else []
        source = summary.get("source_session", {}) if isinstance(summary.get("source_session"), dict) else {}
        timestamp = summary.get("ended_at") or source.get("ended_at") or source.get("started_at")
        normalized = []
        for idx, event in enumerate(events if isinstance(events, list) else [], start=1):
            if isinstance(event, dict):
                normalized.append(
                    {
                        **event,
                        "event_id": f"{summary.get('session_id')}:{idx}",
                        "timestamp": timestamp,
                        "date": str(timestamp or "")[:10],
                        "active_decision": event.get("entry_decision", "WAIT"),
                    }
                )
        return normalized, summary
    return [], {}


def daily_rows_from_backfill(backfill: dict[str, Any], route_id: str | None = None) -> list[dict[str, Any]]:
    selected = route_id or backfill.get("active_route") or ACTIVE_ROUTE
    rows = []
    for row in backfill.get("daily_equity", {}).get(selected, []):
        period = str(row.get("period", ""))
        pnl = float(row.get("pnl_krw", 0.0) or 0.0)
        rows.append(
            {
                "date": period[:10],
                "scenario_id": selected,
                "route_status": "ACTIVE" if selected == ACTIVE_ROUTE else "SHADOW",
                "market_state": row.get("market_state", "UNKNOWN"),
                "realized_pnl_krw": pnl,
                "daily_return_pct": float(row.get("return_pct", 0.0) or 0.0),
                "max_intraday_drawdown": row.get("mdd_pct"),
                "trade_count": int(row.get("trade_count", 0) or 0),
                "candidate_count": int(row.get("candidate_count", 0) or 0),
                "enter_count": int(row.get("trade_count", 0) or 0),
                "wait_count": int(row.get("wait_count", 0) or 0),
                "skip_count": 0,
                "exit_count": int(row.get("trade_count", 0) or 0),
                "data_quality_flags": [],
            }
        )
    return rows


def latest_equity(backfill: dict[str, Any]) -> float:
    routes = backfill.get("routes", [])
    active = next((row for row in routes if row.get("scenario") == backfill.get("active_route")), {})
    if active.get("final_equity_krw") is not None:
        return float(active.get("final_equity_krw") or 0.0)
    route = backfill.get("active_route") or ACTIVE_ROUTE
    rows = backfill.get("daily_equity", {}).get(route, [])
    if rows:
        return float(rows[-1].get("end_equity_krw", rows[-1].get("start_equity_krw", 0.0)) or 0.0)
    return float(backfill.get("initial_cash_krw", 0.0) or 0.0)


def summarize_pnl(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key, ""))].append(row)
    out = []
    for period, items in sorted(grouped.items()):
        pnl = sum(float(item.get("realized_pnl_krw", item.get("pnl_krw", 0.0)) or 0.0) for item in items)
        trades = sum(int(item.get("trade_count", item.get("enter_count", 0)) or 0) for item in items)
        candidates = sum(int(item.get("candidate_count", item.get("candidates_seen", 0)) or 0) for item in items)
        out.append({"period": period, "pnl_krw": pnl, "trade_count": trades, "candidate_count": candidates})
    return out


def profit_factor(values: list[float]) -> float:
    wins = sum(v for v in values if v > 0)
    losses = abs(sum(v for v in values if v < 0))
    return wins / losses if losses else (wins if wins else 0.0)


def win_rate(values: list[float]) -> float:
    if not values:
        return 0.0
    return len([v for v in values if v > 0]) / len(values) * 100.0


def top_counts(values: list[Any], limit: int = 3) -> list[dict[str, Any]]:
    return [{"value": key, "count": count} for key, count in Counter([v for v in values if v]).most_common(limit)]


def safe_status() -> dict[str, Any]:
    return {
        "order_api_called": False,
        "active_change_applied": False,
        "active_route_change_applied": False,
        "llm_active_change_applied": False,
        "manual_review_required": True,
        "default_readiness": "LIVE_NOT_ALLOWED",
        **safety_flags(),
    }
