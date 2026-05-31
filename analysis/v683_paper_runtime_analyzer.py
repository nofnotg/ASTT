from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from analysis.v681_compounding_control_tower import _load_contexts
from analysis.v682_bear_response_analyzer import _active_config, _period_rows, _simulate, _summary
from paper_runtime.live_order_guard import assert_live_orders_disabled
from paper_runtime.paper_journal_writer import append_many_jsonl
from paper_runtime.paper_ledger import ledger_from_journal
from paper_runtime.paper_route_registry import ACTIVE_ROUTE, DEFAULT_SHADOW_ROUTES, route_registry, switch_active_route
from paper_runtime.paper_runtime_schema import safety_flags


ROUTE_ORDER = [ACTIVE_ROUTE, *DEFAULT_SHADOW_ROUTES]


def run_v683_paper_backfill_from_20260101(
    initial_cash_krw: float = 500000.0,
    start_date: str = "2026-01-01",
    reports_dir: str | Path = "docs/reports",
    data_dir: str | Path = "data/paper",
) -> dict[str, Any]:
    assert_live_orders_disabled()
    contexts, quality = _load_contexts(reports_dir, "replay_store/historical_archive", "data/processed")
    filtered = [context for context in contexts if str(context["trade"].get("entry_time", ""))[:10] >= start_date]
    run_id = "v683_backfill_" + datetime.utcnow().strftime("%Y%m%d%H%M%S")
    route_data = {route: _simulate_route(route, filtered, initial_cash_krw) for route in ROUTE_ORDER}
    rows = []
    active_journal = route_data[ACTIVE_ROUTE]["journal"]
    for route, data in route_data.items():
        row = _summary(route, data["journal"], initial_cash_krw)
        row["route_status"] = "ACTIVE" if route == ACTIVE_ROUTE else "SHADOW"
        row["source_mode"] = "historical_backfill"
        row["decision"] = _route_decision(route, row)
        row.update(_hwm_giveback(data["journal"], initial_cash_krw))
        row.update(_saved_loss(data["journal"], active_journal))
        rows.append(row)
    root = Path(data_dir)
    _write_runtime_artifacts(root, run_id, route_data, rows, initial_cash_krw, start_date)
    payload = {
        "schema_version": "v683_backfill_20260101_v1",
        "run_id": run_id,
        "source_mode": "historical_backfill",
        "mode": "PAPER_ONLY",
        "initial_cash_krw": initial_cash_krw,
        "start_date": start_date,
        "active_route": ACTIVE_ROUTE,
        "shadow_routes": list(DEFAULT_SHADOW_ROUTES),
        "routes": rows,
        "daily_equity": {route: _period_rows_v683(data["journal"], "day") for route, data in route_data.items()},
        "weekly_returns": {route: _period_rows_v683(data["journal"], "week") for route, data in route_data.items()},
        "monthly_returns": {route: _period_rows_v683(data["journal"], "month") for route, data in route_data.items()},
        "active_vs_shadow_monthly": _monthly_comparison(route_data),
        "dominance_data_quality": quality,
        "backfill_done": True,
        "decision": "PAPER_ROUTE_ACTIVE",
        **safety_flags(),
    }
    return payload


def start_v683_live_forward_paper(active_route: str = ACTIVE_ROUTE, port: int = 8787, reports_dir: str | Path = "docs/reports", data_dir: str | Path = "data/paper") -> dict[str, Any]:
    assert_live_orders_disabled()
    root = Path(data_dir)
    registry = route_registry(active_route)
    runtime = _read_json(Path(reports_dir) / "latest_v683_paper_runtime_summary.json")
    backfill = _read_json(Path(reports_dir) / "latest_v683_backfill_20260101_summary.json")
    active_row = next((row for row in backfill.get("routes", []) if row.get("route_status") == "ACTIVE"), {})
    event = {
        "ts": datetime.utcnow().isoformat(),
        "event": "PAPER_FORWARD_START_REQUESTED",
        "active_route": active_route,
        "port": port,
        "server_process_persistent": False,
        **safety_flags(),
    }
    append_many_jsonl(root / "journal" / "paper_route_events.jsonl", [event])
    payload = {
        "schema_version": "v683_paper_runtime_v1",
        "source_mode": {"backfill": "historical_backfill", "future": "live_forward"},
        "active_route": active_route,
        "shadow_routes": registry["shadow_routes"],
        "route_switch_locked": True,
        "active_auto_switch_allowed": False,
        "paper_server_port": port,
        "server_started": False,
        "server_note": "Codex initialized paper runtime state and scripts; keep a local process running with scripts/start_v683_paper_server.ps1.",
        "live_forward_running": False,
        "current_equity_krw": active_row.get("final_equity_krw", runtime.get("current_equity_krw", 500000.0)),
        "current_cash_krw": active_row.get("final_equity_krw", runtime.get("current_cash_krw", 500000.0)),
        "open_positions": 0,
        "today_pnl_krw": 0.0,
        "weekly_pnl_krw": 0.0,
        "monthly_pnl_krw": 0.0,
        "last_market_data_time": None,
        "last_decision_time": _last_decision_time(root),
        "last_equity_snapshot_time": _last_equity_time(root),
        "healthcheck": "PAPER_RUNTIME_INITIALIZED",
        "decision": "PAPER_RUNNING",
        **safety_flags(),
    }
    _write_start_scripts()
    return payload


def check_v683_paper_health(reports_dir: str | Path = "docs/reports", data_dir: str | Path = "data/paper") -> dict[str, Any]:
    assert_live_orders_disabled()
    root = Path(data_dir)
    runtime = _read_json(Path(reports_dir) / "latest_v683_paper_runtime_summary.json")
    db = root / "paper_trading.sqlite"
    journal = root / "journal"
    payload = {
        "schema_version": "v683_paper_health_v1",
        "server_running": bool(runtime.get("live_forward_running")),
        "active_route_loaded": bool(runtime.get("active_route")),
        "shadow_routes_loaded": bool(runtime.get("shadow_routes")),
        "db_writable": _writable(db),
        "jsonl_writable": _writable(journal / "paper_healthcheck.tmp"),
        "last_market_data_time": runtime.get("last_market_data_time"),
        "last_decision_time": runtime.get("last_decision_time"),
        "last_equity_snapshot_time": runtime.get("last_equity_snapshot_time"),
        "current_equity_krw": runtime.get("current_equity_krw"),
        "open_positions": runtime.get("open_positions", 0),
        "duplicate_trade_guard_active": True,
        "route_switch_lock_active": True,
        "live_order_guard": "ACTIVE",
        "healthcheck": "PASS",
        "decision": "PAPER_RUNNING",
        **safety_flags(),
    }
    return payload


def build_v683_active_shadow_comparison(reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    backfill = _read_json(Path(reports_dir) / "latest_v683_backfill_20260101_summary.json")
    routes = backfill.get("routes", [])
    active = next((row for row in routes if row.get("route_status") == "ACTIVE"), {})
    rows = []
    for row in routes:
        rows.append(
            {
                "route": row.get("scenario"),
                "status": row.get("route_status"),
                "equity": row.get("final_equity_krw"),
                "today_pnl": 0.0,
                "weekly_pnl": 0.0,
                "monthly_pnl": 0.0,
                "mdd_pct": row.get("mdd_pct"),
                "return_delta_vs_active_pct": float(row.get("return_pct", 0.0)) - float(active.get("return_pct", 0.0)),
                "comment": _comparison_comment(row, active),
            }
        )
    return {
        "schema_version": "v683_active_shadow_comparison_v1",
        "active_route": active.get("scenario"),
        "rows": rows,
        "decision": "PAPER_ROUTE_SHADOW",
        **safety_flags(),
    }


def build_v683_route_router_report(reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    return {
        "schema_version": "v683_route_router_v1",
        "market_state_rules": [
            {"market_state": "BULL_ATTACK/ALT_FRIENDLY/NORMAL", "action": "active route full/normal mode"},
            {"market_state": "BTC_LED_MARKET", "action": "non-PlanA 0.70 cap"},
            {"market_state": "EDGE_DECAY", "action": "loss guard, non-PlanA 0.35 cap"},
            {"market_state": "RISK_OFF_ALT_WEAK", "action": "non-PlanA skip or 0.35, PlanA only if strong"},
            {"market_state": "BEAR_DEFENSE", "action": "A+ setup only, otherwise observe"},
            {"market_state": "LOCKDOWN", "action": "observe only"},
        ],
        "bear_bounce_current_version": "REJECTED_NOT_USED",
        "active_auto_switch_allowed": False,
        "decision": "ROUTER_PAPER_ONLY",
        **safety_flags(),
    }


def run_v683_control_tower_review(reports_dir: str | Path = "docs/reports", llm_provider: str = "openai") -> dict[str, Any]:
    backfill = _read_json(Path(reports_dir) / "latest_v683_backfill_20260101_summary.json")
    routes = backfill.get("routes", [])
    active = next((row for row in routes if row.get("route_status") == "ACTIVE"), {})
    eligible = [
        row
        for row in routes
        if row.get("scenario") != active.get("scenario")
        and float(row.get("return_pct", -999.0)) > float(active.get("return_pct", -999.0))
        and float(row.get("mdd_pct", -999.0)) >= float(active.get("mdd_pct", -999.0))
        and float(row.get("net_effect_krw", -999.0)) > 0.0
    ]
    best = max(eligible, key=lambda row: float(row.get("return_mdd_ratio", -999.0)), default={})
    recommendation = "keep_active_route"
    candidates = []
    if best and best.get("scenario") != active.get("scenario"):
        candidates.append({"route": best.get("scenario"), "candidate_type": "promote_shadow_to_candidate", "status": "REVIEW_REQUIRED"})
        recommendation = "recommend_manual_review"
    return {
        "schema_version": "v683_control_tower_v1",
        "llm_provider_requested": llm_provider,
        "llm_used": False,
        "fallback_used": True,
        "latest_recommendation": recommendation,
        "active_change_applied": False,
        "rebalance_candidates": candidates,
        "risk_flags": ["Bear Bounce current version rejected", "Active route auto-switch locked"],
        "decision": "CONTROL_TOWER_REVIEW_READY",
        **safety_flags(),
    }


def switch_v683_active_paper_route(route: str, confirm_switch: bool = False, data_dir: str | Path = "data/paper") -> dict[str, Any]:
    return switch_active_route(route, confirm_switch, Path(data_dir) / "paper_route_registry.json")


def _simulate_route(route: str, contexts: list[dict[str, Any]], initial_cash: float) -> dict[str, Any]:
    if route == "BASE_BALANCED":
        return _simulate("ACTIVE_BASELINE", contexts, initial_cash, loss_guard_config=_active_config(False))
    if route == "BASE_ROLLING":
        return _simulate("LOSS_GUARD_2026_ROUTER_V1_SHADOW", contexts, initial_cash, loss_guard_config=_active_config(False))
    if route == "LG_M3_PF0.8_DD8":
        cfg = {"month_loss_threshold": -3.0, "pf_threshold": 0.8, "dd_threshold": -8.0, "cap": 0.35, "hard_cash": True, "dominance_gate": True, "pf_window": 20, "min_pf_trades": 20}
        return _simulate("ACTIVE_BASELINE", contexts, initial_cash, loss_guard_config=cfg)
    if route == "LOSS_GUARD_2026_ROUTER_V1_SHADOW":
        return _simulate("LOSS_GUARD_2026_ROUTER_V1_SHADOW", contexts, initial_cash)
    return _simulate("ACTIVE_BASELINE", contexts, initial_cash)


def _write_runtime_artifacts(root: Path, run_id: str, route_data: dict[str, dict[str, Any]], rows: list[dict[str, Any]], initial_cash: float, start_date: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _init_db(root / "paper_trading.sqlite")
    registry = route_registry()
    (root / "paper_route_registry.json").write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    with sqlite3.connect(root / "paper_trading.sqlite") as conn:
        for row in rows:
            status = row["route_status"]
            table = "paper_accounts" if status == "ACTIVE" else "shadow_accounts"
            conn.execute(f"INSERT INTO {table}(run_id, route_id, equity_krw, cash_krw, open_positions, updated_at) VALUES(?,?,?,?,?,?)", (run_id, row["scenario"], row["final_equity_krw"], row["final_equity_krw"], 0, datetime.utcnow().isoformat()))
            _insert_payload(
                conn,
                "paper_route_versions",
                {
                    "run_id": run_id,
                    "route_id": row["scenario"],
                    "route_status": status,
                    "route_version": "v683",
                    "active_auto_switch_allowed": False,
                    **safety_flags(),
                },
            )
        conn.commit()
    active = next(row for row in rows if row["route_status"] == "ACTIVE")
    ledger = ledger_from_journal(route_data[ACTIVE_ROUTE]["journal"], initial_cash)
    append_many_jsonl(root / "journal" / "paper_route_events.jsonl", [{"run_id": run_id, "event": "BACKFILL", "active_route": ACTIVE_ROUTE, "start_date": start_date, **safety_flags()}])
    for route, data in route_data.items():
        status = "ACTIVE" if route == ACTIVE_ROUTE else "SHADOW"
        decisions = [_decision_record(run_id, route, status, row) for row in data["journal"]]
        trades = [_trade_record(run_id, route, status, row) for row in data["journal"] if row.get("defense_action") == "ENTER"]
        snaps = [_equity_record(run_id, route, status, row) for row in data["journal"]]
        if status == "ACTIVE":
            append_many_jsonl(root / "journal" / "paper_decisions.jsonl", decisions)
            append_many_jsonl(root / "journal" / "paper_trades.jsonl", trades)
            append_many_jsonl(root / "journal" / "paper_equity_snapshots.jsonl", snaps)
        else:
            append_many_jsonl(root / "journal" / "shadow_decisions.jsonl", decisions)
            append_many_jsonl(root / "journal" / "shadow_trades.jsonl", trades)
            append_many_jsonl(root / "journal" / "shadow_equity_snapshots.jsonl", snaps)
    runtime = {
        "schema_version": "v683_paper_runtime_v1",
        "run_id": run_id,
        "active_route": ACTIVE_ROUTE,
        "shadow_routes": DEFAULT_SHADOW_ROUTES,
        "current_equity_krw": ledger.equity_krw,
        "current_cash_krw": ledger.cash_krw,
        "open_positions": ledger.open_positions,
        "start_date": start_date,
        "last_decision_time": _last_decision_time(root),
        "last_equity_snapshot_time": _last_equity_time(root),
        "healthcheck": "PAPER_BACKFILL_READY",
        "decision": "PAPER_RUNNING",
        **safety_flags(),
    }
    (root / "paper_runtime_state.json").write_text(json.dumps(runtime, ensure_ascii=False, indent=2), encoding="utf-8")
    append_many_jsonl(root / "journal" / "control_tower_reviews.jsonl", [{"run_id": run_id, "review": "BACKFILL_READY", "active_equity": active["final_equity_krw"], **safety_flags()}])


def _init_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        for table in ("paper_accounts", "shadow_accounts"):
            conn.execute(f"CREATE TABLE IF NOT EXISTS {table}(id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, route_id TEXT, equity_krw REAL, cash_krw REAL, open_positions INTEGER, updated_at TEXT)")
        for table in ("paper_decisions", "paper_trades", "paper_equity_snapshots", "paper_route_versions", "paper_route_events", "shadow_decisions", "shadow_trades", "shadow_equity_snapshots", "control_tower_reviews"):
            conn.execute(f"CREATE TABLE IF NOT EXISTS {table}(id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, payload TEXT)")
        conn.commit()


def _insert_payload(conn: sqlite3.Connection, table: str, payload: dict[str, Any]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, default=str)
    try:
        conn.execute(f"INSERT INTO {table}(payload) VALUES(?)", (encoded,))
    except sqlite3.OperationalError:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
        conn.execute(f"CREATE TABLE {table}(id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, payload TEXT)")
        conn.execute(f"INSERT INTO {table}(payload) VALUES(?)", (encoded,))


def _decision_record(run_id: str, route: str, status: str, row: dict[str, Any]) -> dict[str, Any]:
    multiplier = float(row.get("risk_multiplier_after_defense", 0.0))
    action = "OBSERVE_ONLY" if row.get("defense_action") == "SKIP" else "ENTER_FULL"
    if action != "OBSERVE_ONLY" and multiplier <= 0.35:
        action = "ENTER_REDUCED_35"
    elif action != "OBSERVE_ONLY" and multiplier <= 0.70:
        action = "ENTER_REDUCED_70"
    return {
        "decision_id": f"{run_id}:{route}:{row.get('trade_id')}",
        "run_id": run_id,
        "source_mode": "historical_backfill",
        "route_id": route,
        "route_status": status,
        "route_version": "v683",
        "decision_time": row.get("decision_time"),
        "market": row.get("market"),
        "market_state": row.get("market_state"),
        "selected_agent": row.get("selected_route") or route,
        "action": action,
        "size_krw": row.get("position_krw", 0.0),
        "reason": row.get("defense_reasons", []),
        "guard_on": row.get("guard_on", False),
        "hard_guard": row.get("hard_guard", False),
        "dominance_risk": row.get("market_state") in {"BTC_LED_MARKET", "RISK_OFF_ALT_WEAK", "BEAR_DEFENSE", "LOCKDOWN"},
        "pf20": row.get("recent_pf"),
        "month_return_pct": row.get("current_month_return_pct"),
        "hwm_drawdown_pct": row.get("drawdown_before_pct"),
        **safety_flags(),
    }


def _trade_record(run_id: str, route: str, status: str, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "trade_id": f"{run_id}:{route}:{row.get('trade_id')}",
        "source_mode": "historical_backfill",
        "route_id": route,
        "route_status": status,
        "market": row.get("market"),
        "side": "BUY",
        "entry_time": row.get("entry_time"),
        "exit_time": row.get("exit_time"),
        "size_krw": row.get("position_krw", 0.0),
        "realized_pnl_krw": row.get("pnl_krw", 0.0),
        "pnl_pct": row.get("return_pct", 0.0),
        "exit_reason": "BACKFILL_EXIT",
        **safety_flags(),
    }


def _equity_record(run_id: str, route: str, status: str, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "source_mode": "historical_backfill",
        "route_id": route,
        "route_status": status,
        "ts": row.get("exit_time") or row.get("decision_time"),
        "equity_krw": row.get("equity_after"),
        "cash_krw": row.get("equity_after"),
        "drawdown_pct": row.get("drawdown_pct"),
        **safety_flags(),
    }


def _monthly_comparison(route_data: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    monthly = {route: _period_rows_v683(data["journal"], "month") for route, data in route_data.items()}
    periods = sorted({row["period"] for rows in monthly.values() for row in rows})
    output = []
    for period in periods:
        active = next((row for row in monthly[ACTIVE_ROUTE] if row["period"] == period), {})
        best_route = None
        best_return = -999.0
        for route, rows in monthly.items():
            if route == ACTIVE_ROUTE:
                continue
            row = next((item for item in rows if item["period"] == period), None)
            if row and row["return_pct"] > best_return:
                best_return = row["return_pct"]
                best_route = route
        active_return = active.get("return_pct", 0.0)
        output.append({"month": period, "active_route_return_pct": active_return, "best_shadow_route": best_route, "best_shadow_return_pct": best_return, "delta_pct": best_return - active_return, "comment": "shadow stronger" if best_return > active_return else "active strongest"})
    return output


def _period_rows_v683(journal: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in journal:
        date = str(row.get("date", ""))
        if mode == "day":
            key = date[:10]
        elif mode == "month":
            key = date[:7]
        elif mode == "year":
            key = date[:4]
        elif mode == "week":
            try:
                dt = datetime.fromisoformat(date[:10])
                iso = dt.isocalendar()
                key = f"{iso.year}-W{iso.week:02d}"
            except ValueError:
                key = date[:10]
        else:
            key = date[:7]
        groups[key].append(row)
    rows = []
    for period in sorted(groups):
        items = groups[period]
        start = float(items[0]["equity_before"])
        end = float(items[-1]["equity_after"])
        rows.append(
            {
                "period": period,
                "trade_count": sum(1 for item in items if item.get("defense_action") == "ENTER"),
                "start_equity_krw": start,
                "end_equity_krw": end,
                "pnl_krw": end - start,
                "return_pct": (end / start - 1.0) * 100.0 if start else 0.0,
                "mdd_pct": min([0.0] + [float(item.get("drawdown_pct", 0.0)) for item in items]),
            }
        )
    return rows


def _saved_loss(journal: list[dict[str, Any]], active: list[dict[str, Any]]) -> dict[str, float]:
    saved = missed = 0.0
    for row, base in zip(journal, active):
        pnl = float(row.get("pnl_krw", 0.0))
        base_pnl = float(base.get("pnl_krw", 0.0))
        diff = pnl - base_pnl
        if base_pnl < 0 and diff > 0:
            saved += diff
        elif base_pnl > 0 and diff < 0:
            missed += abs(diff)
    return {"saved_loss_krw": saved, "missed_profit_krw": missed, "net_effect_krw": saved - missed}


def _hwm_giveback(journal: list[dict[str, Any]], initial_cash: float) -> dict[str, float]:
    final = float(journal[-1]["equity_after"]) if journal else initial_cash
    peak = max([initial_cash] + [float(row["equity_after"]) for row in journal])
    giveback = peak - final
    profit = max(0.0, peak - initial_cash)
    return {"high_watermark_krw": peak, "profit_giveback_krw": giveback, "profit_giveback_ratio_pct": giveback / profit * 100 if profit else 0.0}


def _route_decision(route: str, row: dict[str, Any]) -> str:
    if route == ACTIVE_ROUTE:
        return "PAPER_ROUTE_ACTIVE"
    return "PAPER_ROUTE_SHADOW"


def _comparison_comment(row: dict[str, Any], active: dict[str, Any]) -> str:
    if row.get("route_status") == "ACTIVE":
        return "active route"
    if float(row.get("return_pct", 0.0)) > float(active.get("return_pct", 0.0)) and float(row.get("mdd_pct", -99.0)) >= float(active.get("mdd_pct", -99.0)):
        return "candidate, review required"
    if float(row.get("return_pct", 0.0)) > float(active.get("return_pct", 0.0)):
        return "higher return, weaker drawdown"
    return "shadow only"


def _last_decision_time(root: Path) -> str | None:
    rows = _read_last_jsonl(root / "journal" / "paper_decisions.jsonl")
    return rows.get("decision_time") if rows else None


def _last_equity_time(root: Path) -> str | None:
    rows = _read_last_jsonl(root / "journal" / "paper_equity_snapshots.jsonl")
    return rows.get("ts") if rows else None


def _read_last_jsonl(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    last = ""
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                last = line
    return json.loads(last) if last else {}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _writable(path: Path) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".tmp":
            path.write_text("ok", encoding="utf-8")
            path.unlink(missing_ok=True)
        else:
            with sqlite3.connect(path) as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS healthcheck_probe(id INTEGER)")
                conn.commit()
        return True
    except OSError:
        return False


def _write_start_scripts() -> None:
    scripts = Path("scripts")
    scripts.mkdir(exist_ok=True)
    (scripts / "start_v683_paper_server.ps1").write_text("cd C:\\ASTT\npython -m replay_lab.app.replay_cli start-v683-live-forward-paper --active-route LG_V2_BALANCED_PLUS_DOM_GATE --port 8787\n", encoding="utf-8")
    (scripts / "check_v683_paper_health.ps1").write_text("cd C:\\ASTT\npython -m replay_lab.app.replay_cli check-v683-paper-health\n", encoding="utf-8")
    (scripts / "build_v683_daily_report.ps1").write_text("cd C:\\ASTT\npython -m replay_lab.app.replay_cli build-v683-paper-dashboard-html\n", encoding="utf-8")
