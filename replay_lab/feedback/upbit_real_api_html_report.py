from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path

from replay_lab.paths import ROOT_DIR, REPLAY_STORE_DIR
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
        (self.out_dir / "upbit_real_api_report.html").write_text(html, encoding="utf-8")
        (self.out_dir / "upbit_real_api_report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        (self.out_dir / "upbit_real_api_report.md").write_text(md, encoding="utf-8")
        (self.docs_root / "latest_upbit_real_api_report.html").write_text(html, encoding="utf-8")
        (self.docs_root / "latest_upbit_real_api_report.md").write_text(md, encoding="utf-8")
        (self.docs_root / "latest_upbit_real_api_summary.json").write_text(json.dumps(_summary(payload), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return self.out_dir / "upbit_real_api_report.html"

    def _payload(self) -> dict:
        ws = _latest_summary(self.store_dir / "sessions" / "upbit_ws")
        validation = _read_json(self.out_dir / "candidate_second_window_validation.json")
        audit = audit_mock_vs_real_data(self.store_dir / "sessions")
        live = _readiness(ws, validation, audit)
        return {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "websocket_smoke": ws, "candidate_window_validation": validation, "mock_vs_real_audit": audit, "live_readiness": live}

    def _markdown(self, payload: dict) -> str:
        s = _summary(payload)
        return f"""# ASTT V5.5.2 Upbit Real API Report

## 한눈에 보는 결론
- 실제 업비트 데이터 연결: {s['upbit_ws_connected']}
- Mock 데이터 섞임: {s['mixed_data_detected']}
- GOOD/PARTIAL 초봉 window: {s['good_partial_windows']}
- realistic_1 PF: {s['profit_factor_realistic_1']}
- 실전 전환 판단: {s['live_readiness']}

초봉은 전체 기간을 모두 긁는 데이터가 아니라, 후보 종목의 진입 전후 흐름을 확인하는 실행 데이터입니다.

초봉 데이터가 없다는 것은 API 실패가 아니라 해당 초에 체결이 없었다는 뜻일 수 있습니다.

Mock 데이터는 시스템 테스트용이며 실전성 판단에 사용하지 않습니다.

0.05% 비용 조건에서 수익성이 무너지면 초단타 실전은 금지입니다.
"""

    def _html(self, payload: dict) -> str:
        s = _summary(payload)
        cards = [
            ("실제 업비트 데이터인가?", s["upbit_ws_connected"]),
            ("Mock 데이터 섞임", s["mixed_data_detected"]),
            ("초봉 window 품질", f"GOOD/PARTIAL {s['good_partial_windows']}"),
            ("0.05% 비용 생존", s["realistic_1_survives"]),
            ("실전 전환 판단", s["live_readiness"]),
        ]
        card_html = "".join(f"<div class='card'><span>{escape(str(k))}</span><strong>{escape(str(v))}</strong></div>" for k, v in cards)
        return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>ASTT V5.5.2 Upbit Real API</title><style>body{{margin:0;background:#0f172a;color:#e5e7eb;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif}}main{{max-width:1120px;margin:auto;padding:28px 18px}}.grid{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}}.card,section{{background:#111c33;border:1px solid #24324d;border-radius:8px;padding:16px}}.card span{{display:block;color:#9ca3af;font-size:13px}}.card strong{{display:block;font-size:20px;margin-top:6px}}section{{margin-top:14px}}p{{color:#cbd5e1;line-height:1.65}}@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}</style></head><body><main><h1>ASTT V5.5.2 Upbit Real API Connection</h1><div class="grid">{card_html}</div><section><h2>이번 검증의 의미</h2><p>초봉은 전체 기간을 모두 긁는 데이터가 아니라, 후보 종목의 진입 전후 흐름을 확인하는 실행 데이터입니다.</p></section><section><h2>Mock vs 실제 Upbit 데이터 구분</h2><p>{escape(json.dumps(payload['mock_vs_real_audit'], ensure_ascii=False))}</p></section><section><h2>실제 WebSocket smoke test 결과</h2><p>{escape(json.dumps(payload['websocket_smoke'], ensure_ascii=False, default=str))}</p></section><section><h2>Candidate-window 초봉 조회 결과</h2><p>{escape(json.dumps(payload['candidate_window_validation'], ensure_ascii=False, default=str)[:3000])}</p></section><section><h2>데이터 제한과 한계</h2><p>초봉 데이터가 없다는 것은 API 실패가 아니라 해당 초에 체결이 없었다는 뜻일 수 있습니다. Mock 데이터는 시스템 테스트용이며 실전성 판단에 사용하지 않습니다. 0.05% 비용 조건에서 수익성이 무너지면 초단타 실전은 금지입니다.</p></section><section><h2>실전 전환 판단</h2><p><b>{escape(str(s['live_readiness']))}</b>. 이번 단계에서는 MICRO_LIVE_READY를 출력하지 않습니다.</p></section></main></body></html>"""


def _latest_summary(root: Path) -> dict:
    paths = sorted(root.glob("*/session_summary.json")) if root.exists() else []
    return json.loads(paths[-1].read_text(encoding="utf-8")) if paths else {}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _summary(payload: dict) -> dict:
    ws = payload.get("websocket_smoke", {})
    validation = payload.get("candidate_window_validation", {})
    good_partial = validation.get("good_window_count", 0) + validation.get("partial_window_count", 0)
    return {"schema_version": "1.0", "generated_at": payload.get("generated_at"), "data_source": ws.get("data_source", "NONE"), "upbit_ws_connected": bool(ws.get("trade_event_count", 0) and ws.get("orderbook_event_count", 0)), "mock_data_used": payload.get("mock_vs_real_audit", {}).get("mock_session_count", 0) > 0, "mixed_data_detected": payload.get("mock_vs_real_audit", {}).get("mixed_data_detected", False), "good_partial_windows": good_partial, "profit_factor_realistic_1": validation.get("profit_factor_realistic_1", 0.0), "expectancy_realistic_1": validation.get("expectancy_realistic_1", 0.0), "realistic_1_survives": validation.get("profit_factor_realistic_1", 0.0) >= 1.1 and validation.get("expectancy_realistic_1", 0.0) > 0, "live_readiness": payload.get("live_readiness", "LIVE_NOT_ALLOWED")}


def _readiness(ws: dict, validation: dict, audit: dict) -> str:
    good_partial = validation.get("good_window_count", 0) + validation.get("partial_window_count", 0)
    if not (ws.get("trade_event_count", 0) and ws.get("orderbook_event_count", 0)):
        return "LIVE_NOT_ALLOWED"
    if audit.get("mixed_data_detected"):
        return "LIVE_NOT_ALLOWED"
    if validation.get("profit_factor_realistic_1", 0.0) < 1.1 or validation.get("expectancy_realistic_1", 0.0) <= 0:
        return "LIVE_NOT_ALLOWED"
    if good_partial < 30:
        return "PAPER_MORE_REQUIRED" if good_partial > 0 else "LIVE_NOT_ALLOWED"
    return "PAPER_MORE_REQUIRED"
