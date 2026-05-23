from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR, ROOT_DIR


@dataclass(frozen=True)
class MicroEntryDiagnosticsHTMLReportBuilder:
    store_dir: Path = REPLAY_STORE_DIR
    docs_root: Path = ROOT_DIR / "docs" / "reports"

    @property
    def out_dir(self) -> Path:
        return self.store_dir / "reports" / "micro_entry_diagnostics"

    def build(self) -> Path:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.docs_root.mkdir(parents=True, exist_ok=True)
        payload = self._payload()
        html = self._html(payload)
        md = self._markdown(payload)
        summary = _summary(payload)
        (self.out_dir / "micro_entry_diagnostics_report.html").write_text(html, encoding="utf-8")
        (self.out_dir / "micro_entry_diagnostics_report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        (self.out_dir / "micro_entry_diagnostics_report.md").write_text(md, encoding="utf-8")
        (self.docs_root / "latest_micro_entry_diagnostics_report.html").write_text(html, encoding="utf-8")
        (self.docs_root / "latest_micro_entry_diagnostics_report.md").write_text(md, encoding="utf-8")
        (self.docs_root / "latest_micro_entry_diagnostics_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return self.out_dir / "micro_entry_diagnostics_report.html"

    def _payload(self) -> dict:
        return {
            "schema_version": "1.0",
            "generated_at": datetime.utcnow().isoformat(),
            "gate_diagnostics": _read_json(self.out_dir / "gate_diagnostics_v554.json"),
            "gate_abtest": _read_json(self.out_dir / "gate_abtest_v554.json"),
            "priority_ws": _read_json(self.out_dir / "priority_external_strategy_ws_v554.json"),
            "latest_forward_ws": _latest_forward_ws(self.store_dir / "sessions" / "forward_ws_v554"),
        }

    def _markdown(self, payload: dict) -> str:
        s = _summary(payload)
        lines = [
            "# ASTT V5.5.4 Micro Entry Diagnostics",
            "",
            "## 한눈에 보는 결론",
            f"- 실전 판정: {s['live_readiness']}",
            f"- candidate_count: {s['candidate_count']}",
            f"- ENTER_count: {s['enter_count']}",
            f"- 가장 큰 차단 이유: {s['top_block_reason']}",
            "",
            "지금은 수익률을 볼 단계가 아니라 실제 진입이 가능한지 확인하는 단계입니다.",
            "WAIT/CANCEL은 매수하지 않은 후보이므로 손익에 포함하지 않습니다.",
            "EXPLORATORY는 연구용 조건이며 실전 판정에 사용하지 않습니다.",
            "0.05% 비용에서 버티지 못하면 초단타 실전은 금지입니다.",
        ]
        return "\n".join(lines) + "\n"

    def _html(self, payload: dict) -> str:
        s = _summary(payload)
        cards = [
            ("실전 판정", s["live_readiness"]),
            ("후보 수", s["candidate_count"]),
            ("ENTER", s["enter_count"]),
            ("ENTER rate", f"{s['enter_rate']:.2f}%"),
            ("최대 차단 이유", s["top_block_reason"]),
            ("GOOD/PARTIAL", s["good_partial_count"]),
        ]
        card_html = "".join(f"<div class='card'><span>{escape(str(k))}</span><strong>{escape(str(v))}</strong></div>" for k, v in cards)
        block_rows = "".join(f"<tr><td>{escape(row['block_reason'])}</td><td>{row['count']}</td><td>{row['pct']:.1f}%</td></tr>" for row in payload.get("gate_diagnostics", {}).get("block_reason_table", [])[:12])
        profile_rows = "".join(
            f"<tr><td>{escape(name)}</td><td>{row['candidate_count']}</td><td>{row['enter_count']}</td><td>{row['wait_count']}</td><td>{row['cancel_count']}</td><td>{row['pf_realistic_1']}</td><td>{row['research_only']}</td></tr>"
            for name, row in payload.get("gate_abtest", {}).get("profiles", {}).items()
        )
        ws = payload.get("latest_forward_ws", {})
        strategy_rows = "".join(
            f"<tr><td>{escape(row['strategy'])}</td><td>{row['candidate_count']}</td><td>{row['enter_count']}</td><td>{escape(row['main_block_reason'])}</td><td>{row['orderbook_available_ratio']:.2f}</td><td>{row['realistic_1_cost_survival']}</td></tr>"
            for row in payload.get("priority_ws", {}).get("strategy_results", [])
        )
        return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>ASTT V5.5.4 Micro Entry Diagnostics</title><style>body{{margin:0;background:#0b1120;color:#e5e7eb;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif}}main{{max-width:1120px;margin:auto;padding:28px 18px}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}.card,section{{background:#111827;border:1px solid #273449;border-radius:8px;padding:16px}}.card span{{display:block;color:#9ca3af;font-size:13px}}.card strong{{display:block;font-size:22px;margin-top:6px}}section{{margin-top:14px}}p{{line-height:1.65;color:#cbd5e1}}table{{width:100%;border-collapse:collapse}}td,th{{border-bottom:1px solid #2d3b52;padding:9px;text-align:left}}@media(max-width:800px){{.grid{{grid-template-columns:1fr}}}}</style></head><body><main><h1>ASTT V5.5.4 Micro Entry Gate Decomposition</h1><div class="grid">{card_html}</div><section><h2>한눈에 보는 결론</h2><p>지금은 수익률을 볼 단계가 아니라 실제 진입이 가능한지 확인하는 단계입니다. WAIT/CANCEL은 매수하지 않은 후보이므로 손익에 포함하지 않습니다.</p></section><section><h2>ENTER를 막은 조건 TOP</h2><table><thead><tr><th>Block Reason</th><th>Count</th><th>%</th></tr></thead><tbody>{block_rows}</tbody></table></section><section><h2>STRICT / BALANCED / EXPLORATORY 비교</h2><p>EXPLORATORY는 연구용 조건이며 실전 판정에 사용하지 않습니다.</p><table><thead><tr><th>Profile</th><th>Candidate</th><th>ENTER</th><th>WAIT</th><th>CANCEL</th><th>PF realistic_1</th><th>Research Only</th></tr></thead><tbody>{profile_rows}</tbody></table></section><section><h2>실제 WS forward session 결과</h2><p>session_id: {escape(str(ws.get('session_id', 'NO_DATA')))} / trade: {ws.get('trade_event_count', 0)} / orderbook: {ws.get('orderbook_event_count', 0)} / real_order_enabled: {escape(str(ws.get('real_order_enabled', False)))}</p></section><section><h2>외부 전략 3개 우선 검증</h2><table><thead><tr><th>Strategy</th><th>Candidate</th><th>ENTER</th><th>Main Block</th><th>Orderbook Available</th><th>Cost Survival</th></tr></thead><tbody>{strategy_rows}</tbody></table></section><section><h2>실전 전환 판단</h2><p><b>{escape(s['live_readiness'])}</b>. 이번 단계에서는 MICRO_LIVE_READY를 출력하지 않습니다.</p></section></main></body></html>"""


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _latest_forward_ws(root: Path) -> dict:
    paths = sorted(root.glob("*/session_summary.json")) if root.exists() else []
    return json.loads(paths[-1].read_text(encoding="utf-8")) if paths else {}


def _summary(payload: dict) -> dict:
    diag = payload.get("gate_diagnostics", {})
    ws = payload.get("latest_forward_ws", {})
    candidate_count = diag.get("candidate_count", 0)
    enter_count = diag.get("ENTER_count", 0)
    primary = diag.get("primary_block_reason_counts", {})
    top = max(primary.items(), key=lambda item: item[1])[0] if primary else "NO_DATA"
    live = "LIVE_NOT_ALLOWED"
    if enter_count > 0 and ws.get("status") == "COMPLETED":
        live = "PAPER_MORE_REQUIRED"
    return {
        "schema_version": "1.0",
        "generated_at": payload.get("generated_at"),
        "live_readiness": live,
        "candidate_count": candidate_count,
        "enter_count": enter_count,
        "enter_rate": enter_count / candidate_count * 100 if candidate_count else 0.0,
        "top_block_reason": top,
        "good_partial_count": diag.get("good_partial_count", 0),
        "realistic_1_survives": False,
    }
