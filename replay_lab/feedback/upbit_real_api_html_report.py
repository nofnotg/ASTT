from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR, ROOT_DIR
from replay_lab.research.mock_vs_real_data_audit import audit_mock_vs_real_data


@dataclass(frozen=True)
class UpbitRealAPIHTMLReportBuilder:
    store_dir: Path = REPLAY_STORE_DIR
    docs_root: Path = ROOT_DIR / "docs" / "reports"

    @property
    def out_dir(self) -> Path:
        return self.store_dir / "reports" / "upbit_real_api"

    def build(self) -> Path:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.docs_root.mkdir(parents=True, exist_ok=True)
        payload = self._payload()
        html = self._html(payload)
        md = self._markdown(payload)
        summary = _summary(payload)
        (self.out_dir / "upbit_real_api_report.html").write_text(html, encoding="utf-8")
        (self.out_dir / "upbit_real_api_report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        (self.out_dir / "upbit_real_api_report.md").write_text(md, encoding="utf-8")
        (self.docs_root / "latest_upbit_real_api_report.html").write_text(html, encoding="utf-8")
        (self.docs_root / "latest_upbit_real_api_report.md").write_text(md, encoding="utf-8")
        (self.docs_root / "latest_upbit_real_api_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return self.out_dir / "upbit_real_api_report.html"

    def _payload(self) -> dict:
        ws = _latest_summary(self.store_dir / "sessions" / "upbit_ws")
        validation = _read_json(self.out_dir / "candidate_second_window_validation.json")
        filter_validation = _read_json(self.out_dir / "micro_candidate_filter_validation_v553.json")
        audit = audit_mock_vs_real_data(self.store_dir / "sessions")
        live = _readiness(ws, validation, audit)
        return {
            "schema_version": "1.1",
            "generated_at": datetime.utcnow().isoformat(),
            "websocket_smoke": ws,
            "candidate_window_validation": validation,
            "micro_candidate_filter_validation": filter_validation,
            "mock_vs_real_audit": audit,
            "live_readiness": live,
        }

    def _markdown(self, payload: dict) -> str:
        s = _summary(payload)
        return f"""# ASTT V5.5.3 Upbit Real API Report

## 한눈에 보는 결론
- 실제 업비트 WebSocket 연결: {s['upbit_ws_connected']}
- Mock 데이터 readiness 제외: {s['mock_excluded_from_readiness']}
- GOOD/PARTIAL 초봉 window: {s['good_partial_windows']}
- ENTER만 손익 집계: {s['enter_only_pnl']}
- WAIT/CANCEL 오류 경고: {s['wait_cancel_warning']}
- realistic_1 PF: {s['profit_factor_realistic_1']}
- 실전 전환 판단: {s['live_readiness']}

초봉은 전체 기간을 모두 긁는 데이터가 아니라, 후보 종목의 진입 전후 흐름을 확인하는 실행 데이터입니다.

초봉 데이터가 없다는 것은 API 실패가 아니라 해당 초에 체결이 없었다는 뜻일 수 있습니다.

Mock 데이터는 시스템 테스트용이며 실전성 판단에 사용하지 않습니다.

WAIT/CANCEL은 실제 매수하지 않은 후보이므로 손익에 넣으면 안 됩니다.

0.05% 비용 조건에서 수익성이 무너지면 초단타 실전은 금지입니다.
"""

    def _html(self, payload: dict) -> str:
        s = _summary(payload)
        validation = payload.get("candidate_window_validation", {})
        representative = [row for row in validation.get("results", [])[:3]]
        trade_rows = "".join(
            "<tr>"
            f"<td>{escape(str(row.get('market')))}</td>"
            f"<td>{escape(str(row.get('entry_decision')))}</td>"
            f"<td>{escape(str(row.get('data_quality')))}</td>"
            f"<td>{escape(str(row.get('net_pnl_pct')))}</td>"
            f"<td>{escape(str(row.get('included_in_pnl')))}</td>"
            "</tr>"
            for row in representative
        )
        cards = [
            ("실제 Upbit 데이터", s["upbit_ws_connected"]),
            ("Mock 제외", s["mock_excluded_from_readiness"]),
            ("GOOD/PARTIAL", s["good_partial_windows"]),
            ("realistic_1 PF", s["profit_factor_realistic_1"]),
            ("WAIT/CANCEL 경고", s["wait_cancel_warning"]),
            ("실전 판단", s["live_readiness"]),
        ]
        card_html = "".join(f"<div class='card'><span>{escape(str(k))}</span><strong>{escape(str(v))}</strong></div>" for k, v in cards)
        quality_bar = _quality_bar(validation)
        return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>ASTT V5.5.3 Upbit Real API</title><style>body{{margin:0;background:#0f172a;color:#e5e7eb;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif}}main{{max-width:1120px;margin:auto;padding:28px 18px}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}.card,section{{background:#111c33;border:1px solid #24324d;border-radius:8px;padding:16px}}.card span{{display:block;color:#9ca3af;font-size:13px}}.card strong{{display:block;font-size:22px;margin-top:6px}}section{{margin-top:14px}}p{{color:#cbd5e1;line-height:1.65}}table{{width:100%;border-collapse:collapse}}td,th{{border-bottom:1px solid #263a5f;padding:9px;text-align:left}}.bar{{display:flex;height:20px;border-radius:999px;overflow:hidden;background:#1f2937}}.good{{background:#22c55e}}.partial{{background:#f59e0b}}.poor{{background:#ef4444}}.unavailable{{background:#64748b}}details{{margin-top:10px}}summary{{cursor:pointer;color:#93c5fd}}@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}</style></head><body><main><h1>ASTT V5.5.3 Upbit Real API Validation</h1><div class="grid">{card_html}</div><section><h2>한눈에 보는 결론</h2><p>이 리포트는 실제 주문이 아니라 PAPER 검증입니다. 실전 전환 판단은 데이터 품질과 0.05% 비용 생존 여부를 기준으로 합니다. PF가 높아도 데이터 품질이 낮으면 믿을 수 없습니다.</p></section><section><h2>GOOD/PARTIAL/POOR/UNAVAILABLE</h2>{quality_bar}<p>GOOD/PARTIAL만 실전성 평가 대상입니다. POOR/UNAVAILABLE은 별도로 표시하고 성과 포장에 쓰지 않습니다.</p></section><section><h2>WAIT/CANCEL 손익 제외 검사</h2><p>ENTER만 포지션을 만들고 손익에 포함합니다. WAIT/CANCEL은 observation-only입니다. 현재 경고: <b>{escape(str(s['wait_cancel_warning']))}</b></p></section><section><h2>대표 후보 3개</h2><table><thead><tr><th>Market</th><th>Decision</th><th>Quality</th><th>Net PnL %</th><th>Included</th></tr></thead><tbody>{trade_rows}</tbody></table></section><section><h2>Mock vs 실제 Upbit 데이터</h2><p>Mock 데이터는 시스템 테스트용이며 실전성 판단에 사용하지 않습니다. 실제 WebSocket eligible session 수: {escape(str(payload.get('mock_vs_real_audit', {}).get('readiness_eligible_session_count', 0)))}</p></section><section><h2>접어둔 원본 요약</h2><details><summary>candidate-window 요약 JSON 보기</summary><pre>{escape(json.dumps({k: v for k, v in validation.items() if k != 'results'}, ensure_ascii=False, indent=2, default=str))}</pre></details></section><section><h2>실전 전환 판단</h2><p><b>{escape(str(s['live_readiness']))}</b>. 이번 단계에서는 MICRO_LIVE_READY를 출력하지 않습니다.</p></section></main></body></html>"""


def _latest_summary(root: Path) -> dict:
    paths = sorted(root.glob("*/session_summary.json")) if root.exists() else []
    return json.loads(paths[-1].read_text(encoding="utf-8")) if paths else {}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _summary(payload: dict) -> dict:
    ws = payload.get("websocket_smoke", {})
    validation = payload.get("candidate_window_validation", {})
    rows = validation.get("results", [])
    good_partial = validation.get("good_window_count", 0) + validation.get("partial_window_count", 0)
    wait_cancel_with_pnl = [
        row for row in rows
        if row.get("entry_decision") in {"WAIT", "CANCEL"} and row.get("included_in_pnl") is True
    ]
    return {
        "schema_version": "1.1",
        "generated_at": payload.get("generated_at"),
        "data_source": ws.get("data_source", "NONE"),
        "upbit_ws_connected": bool(ws.get("trade_event_count", 0) and ws.get("orderbook_event_count", 0)),
        "mock_data_used": payload.get("mock_vs_real_audit", {}).get("mock_session_count", 0) > 0,
        "mock_excluded_from_readiness": not payload.get("mock_vs_real_audit", {}).get("mixed_data_detected", False),
        "mixed_data_detected": payload.get("mock_vs_real_audit", {}).get("mixed_data_detected", False),
        "good_partial_windows": good_partial,
        "entry_count": validation.get("entry_count", 0),
        "wait_count": validation.get("wait_count", 0),
        "cancel_count": validation.get("cancel_count", 0),
        "enter_only_pnl": not wait_cancel_with_pnl,
        "wait_cancel_warning": "OK" if not wait_cancel_with_pnl else f"{len(wait_cancel_with_pnl)} WAIT/CANCEL rows included in PnL",
        "profit_factor_realistic_1": validation.get("profit_factor_realistic_1", 0.0),
        "expectancy_realistic_1": validation.get("expectancy_realistic_1", 0.0),
        "realistic_1_survives": validation.get("profit_factor_realistic_1", 0.0) >= 1.1 and validation.get("expectancy_realistic_1", 0.0) > 0,
        "live_readiness": payload.get("live_readiness", "LIVE_NOT_ALLOWED"),
    }


def _readiness(ws: dict, validation: dict, audit: dict) -> str:
    rows = validation.get("results", [])
    good_partial = validation.get("good_window_count", 0) + validation.get("partial_window_count", 0)
    wait_cancel_with_pnl = any(row.get("entry_decision") in {"WAIT", "CANCEL"} and row.get("included_in_pnl") is True for row in rows)
    if wait_cancel_with_pnl:
        return "LIVE_NOT_ALLOWED"
    if not (ws.get("trade_event_count", 0) and ws.get("orderbook_event_count", 0)):
        return "LIVE_NOT_ALLOWED"
    if audit.get("mixed_data_detected"):
        return "LIVE_NOT_ALLOWED"
    if validation.get("profit_factor_realistic_1", 0.0) < 1.1 or validation.get("expectancy_realistic_1", 0.0) <= 0:
        return "LIVE_NOT_ALLOWED"
    if good_partial < 30:
        return "PAPER_MORE_REQUIRED" if good_partial > 0 else "LIVE_NOT_ALLOWED"
    return "PAPER_MORE_REQUIRED"


def _quality_bar(validation: dict) -> str:
    counts = {
        "GOOD": validation.get("good_window_count", 0),
        "PARTIAL": validation.get("partial_window_count", 0),
        "POOR": validation.get("poor_window_count", 0),
        "UNAVAILABLE": validation.get("unavailable_window_count", 0),
    }
    total = max(1, sum(counts.values()))
    parts = []
    cls = {"GOOD": "good", "PARTIAL": "partial", "POOR": "poor", "UNAVAILABLE": "unavailable"}
    for key, count in counts.items():
        width = count / total * 100
        parts.append(f"<div class='{cls[key]}' style='width:{width:.2f}%' title='{key}: {count}'></div>")
    labels = " / ".join(f"{key}: {value}" for key, value in counts.items())
    return f"<div class='bar'>{''.join(parts)}</div><p>{escape(labels)}</p>"
