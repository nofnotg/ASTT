from __future__ import annotations


def update_drawdown(equity_krw: float, peak_equity_krw: float) -> dict:
    peak = max(float(peak_equity_krw), float(equity_krw))
    drawdown = (float(equity_krw) - peak) / peak * 100 if peak else 0.0
    return {
        "equity_krw": float(equity_krw),
        "peak_equity_krw": peak,
        "drawdown_pct": drawdown,
        "max_drawdown_pct": min(0.0, drawdown),
        "drawdown_guard_triggered": drawdown <= -1.0,
    }


def check_drawdown_guard(drawdown: dict, daily_stop_loss_pct: float = -2.0, session_stop_loss_pct: float = -1.0) -> dict:
    dd = float(drawdown.get("drawdown_pct", 0.0))
    if dd <= daily_stop_loss_pct:
        return {"allowed": False, "reason": "DAILY_DRAWDOWN_GUARD"}
    if dd <= session_stop_loss_pct:
        return {"allowed": False, "reason": "SESSION_DRAWDOWN_GUARD"}
    return {"allowed": True, "reason": "OK"}
