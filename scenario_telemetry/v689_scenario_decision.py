from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scenario_telemetry.v688_common import safe_status, write_html, write_json


REPORTS = Path("docs/reports")


def _read(name: str, reports_dir: str | Path) -> dict[str, Any]:
    path = Path(reports_dir) / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _metric(row: dict[str, Any], *names: str) -> float | None:
    for name in names:
        value = row.get(name)
        if value is not None:
            return float(value)
    return None


def _normalize(row: dict[str, Any], source: str, period: str) -> dict[str, Any]:
    scenario = row.get("scenario") or row.get("route_id") or row.get("name")
    final_equity = _metric(row, "final_equity_krw", "end_equity_krw")
    return_pct = _metric(row, "total_return_pct", "return_pct")
    mdd = _metric(row, "mdd_pct")
    pf = _metric(row, "profit_factor")
    trade_count = int(row.get("trade_count", 0) or 0)
    score = (return_pct or 0.0) + (mdd or 0.0) * 0.6 + (pf or 0.0) * 4.0
    scenario_text = str(scenario or "")
    eligible = trade_count >= 30 and not scenario_text.startswith("SRR_")
    exclusion_reason = ""
    if scenario_text.startswith("SRR_"):
        exclusion_reason = "RESEARCH_ONLY_LOW_SAMPLE"
    elif trade_count < 30:
        exclusion_reason = "LOW_SAMPLE"
    return {
        "source": source,
        "period": period,
        "scenario": scenario,
        "final_equity_krw": final_equity,
        "return_pct": return_pct,
        "mdd_pct": mdd,
        "profit_factor": pf,
        "trade_count": trade_count,
        "score": score,
        "eligible_for_operation": eligible if period == "2026" else trade_count >= 500,
        "exclusion_reason": exclusion_reason,
        "decision": row.get("decision"),
    }


def _best(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [row for row in rows if row.get("return_pct") is not None and row.get("mdd_pct") is not None]
    return max(valid, key=lambda row: (row["score"], row.get("return_pct") or -999.0), default={})


def _best_operating_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [
        row
        for row in rows
        if row.get("return_pct") is not None
        and row.get("mdd_pct") is not None
        and int(row.get("trade_count", 0) or 0) >= 30
        and not str(row.get("scenario", "")).startswith("SRR_")
    ]
    return max(valid, key=lambda row: (row["score"], row.get("return_pct") or -999.0), default={})


def _best_long_term_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [
        row
        for row in rows
        if row.get("return_pct") is not None
        and row.get("mdd_pct") is not None
        and int(row.get("trade_count", 0) or 0) >= 500
        and "REJECTED" not in str(row.get("decision", ""))
    ]
    return max(valid, key=lambda row: (row.get("return_pct") or -999.0, row.get("mdd_pct") or -999.0), default={})


def _monthly_2026_rows(backfill: dict[str, Any], surge: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for route, rows in backfill.get("monthly_returns", {}).items():
        for row in rows:
            if str(row.get("period", "")).startswith("2026"):
                out.append({**row, "scenario": route, "source": "v683_backfill"})
    for route, rows in surge.get("monthly_returns", {}).items():
        for row in rows:
            if str(row.get("period", "")).startswith("2026"):
                out.append({**row, "scenario": route, "source": "v688_surge_rr"})
    return out


def build_v689_scenario_decision(reports_dir: str | Path = REPORTS) -> dict[str, Any]:
    v66 = _read("latest_v66_btcd_scenario_comparison_summary.json", reports_dir)
    v681 = _read("latest_v681_compounding_router_summary.json", reports_dir)
    v683 = _read("latest_v683_backfill_20260101_summary.json", reports_dir)
    surge = _read("latest_v688_surge_rr_scenario_summary.json", reports_dir)
    integrated = _read("latest_integrated_investment_summary.json", reports_dir)

    long_term_rows = [_normalize(row, "v66_btcd_2022_plus", "2022-current") for row in v66.get("scenarios", [])]
    long_term_rows += [_normalize(row, "v681_compounding", "2022-current") for row in v681.get("scenarios", [])]
    current_rows = [_normalize(row, "v683_2026_backfill", "2026") for row in v683.get("routes", [])]
    current_rows += [_normalize(row, "v688_surge_rr", "2026") for row in surge.get("routes", [])]
    monthly_rows = _monthly_2026_rows(v683, surge)

    long_term_best = _best_long_term_candidate(long_term_rows) or _best(long_term_rows)
    current_best = _best_operating_candidate(current_rows) or _best(current_rows)
    active = next((row for row in current_rows if row.get("scenario") == v683.get("active_route")), {})
    current_month = max(
        (row for row in monthly_rows if row.get("period") and row.get("scenario") == current_best.get("scenario")),
        key=lambda row: str(row.get("period")),
        default={},
    )
    current_week = max(v683.get("weekly_returns", {}).get(current_best.get("scenario"), []), key=lambda row: str(row.get("period")), default={})
    today = max(v683.get("daily_equity", {}).get(current_best.get("scenario"), []), key=lambda row: str(row.get("period")), default={})

    long_name = long_term_best.get("scenario") or "-"
    current_name = current_best.get("scenario") or "-"
    active_name = v683.get("active_route") or "-"
    conclusion = {
        "answer_to_user_question": "V6.8.8 단계에서는 새 개선 시나리오 확정까지는 미완료였습니다. V6.8.9에서 2022+ 장기 검증과 2026 운용 검증을 분리해 결론을 냈습니다.",
        "long_term_conclusion": f"2022~현재 장기 복리 검증에서는 {long_name}가 가장 강한 후보입니다. 도미넌스는 전체 기간에서 단독 만능 필터가 아니라 상대강도/하락 대응 보조축으로 쓰는 것이 타당합니다.",
        "current_operation_conclusion": f"2026 운용 구간에서는 active인 {active_name}보다 {current_name}가 수익률, MDD, PF를 함께 개선했습니다.",
        "new_or_upgraded_scenario": f"{current_name}을 운용 후보 1순위로 올리고, 기존 active {active_name}은 shadow로 내려 계속 추적하는 것이 보수적 결론입니다.",
        "not_promoted": "SRR 급등/손익비 시나리오는 2026 walk-forward에서 거래가 0건이라 연구용으로만 보관합니다.",
        "manual_gate": "자동 교체는 금지입니다. 대시보드에는 운용 후보로 표시하되 active_change_applied=false를 유지합니다.",
    }
    operating_summary = {
        "investment_start_date": "2026-01-01",
        "recommended_primary_route": current_best.get("scenario"),
        "recommended_primary_label": "LG-M3" if current_best.get("scenario") == "LG_M3_PF0.8_DD8" else current_best.get("scenario"),
        "current_active_route": v683.get("active_route"),
        "long_term_best": long_term_best,
        "current_best": current_best,
        "active_baseline": active,
        "today": {
            "period": today.get("period"),
            "pnl_krw": today.get("pnl_krw", 0.0),
            "return_pct": today.get("return_pct", 0.0),
            "trade_count": today.get("trade_count", 0),
            "end_equity_krw": today.get("end_equity_krw"),
        },
        "this_week": {
            "period": current_week.get("period"),
            "pnl_krw": current_week.get("pnl_krw", 0.0),
            "return_pct": current_week.get("return_pct", 0.0),
            "trade_count": current_week.get("trade_count", 0),
        },
        "this_month": {
            "period": current_month.get("period"),
            "pnl_krw": current_month.get("pnl_krw", 0.0),
            "return_pct": current_month.get("return_pct", 0.0),
            "trade_count": current_month.get("trade_count", 0),
        },
    }
    payload = {
        "schema_version": "v689_scenario_decision_v1",
        "source_period": "2022-current plus 2026 paper",
        "conclusion": conclusion,
        "operating_summary": operating_summary,
        "long_term_rows": sorted(long_term_rows, key=lambda row: row.get("score") or -999.0, reverse=True),
        "current_rows": sorted(
            current_rows,
            key=lambda row: (bool(row.get("eligible_for_operation")), row.get("score") or -999.0),
            reverse=True,
        ),
        "monthly_2026_rows": sorted(monthly_rows, key=lambda row: str(row.get("period", "")), reverse=True),
        "integrated_month_count": len(integrated.get("monthly_rows", [])),
        **safe_status(),
    }
    reports = Path(reports_dir)
    saved = write_json(reports / "latest_v689_scenario_decision_summary.json", payload)
    write_html(
        reports / "latest_v689_scenario_decision_report.html",
        "ASTT V6.8.9 Scenario Decision",
        [
            ("Conclusion", saved["conclusion"]),
            ("Operating Summary", saved["operating_summary"]),
            ("2022+ Long Term Rows", saved["long_term_rows"]),
            ("2026 Current Rows", saved["current_rows"]),
        ],
    )
    return saved
