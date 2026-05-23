from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR, ROOT_DIR
from replay_lab.research.micro_candidate_source_comparison_v555 import compare_micro_candidate_sources_v555
from replay_lab.research.micro_cost_survival_v555 import test_micro_cost_survival_v555
from replay_lab.research.realistic_paper_validation_v555 import validate_realistic_paper_v555


@dataclass(frozen=True)
class RealisticPaperHTMLReportV555:
    store_dir: Path = REPLAY_STORE_DIR
    docs_root: Path = ROOT_DIR / "docs" / "reports"

    def build(self, sessions_dir: str | Path) -> Path:
        out = self.store_dir / "reports" / "realistic_paper_v555"
        out.mkdir(parents=True, exist_ok=True)
        self.docs_root.mkdir(parents=True, exist_ok=True)
        validation = validate_realistic_paper_v555(sessions_dir)
        sources = compare_micro_candidate_sources_v555(sessions_dir)
        cost = test_micro_cost_survival_v555(sessions_dir)
        payload = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "validation": validation, "sources": sources, "cost_survival": cost}
        html = self._html(payload)
        md = self._md(payload)
        (out / "realistic_paper_report.html").write_text(html, encoding="utf-8")
        (out / "realistic_paper_report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        (out / "realistic_paper_report.md").write_text(md, encoding="utf-8")
        (self.docs_root / "latest_realistic_paper_report.html").write_text(html, encoding="utf-8")
        (self.docs_root / "latest_realistic_paper_report.md").write_text(md, encoding="utf-8")
        (self.docs_root / "latest_realistic_paper_summary.json").write_text(json.dumps(_summary(payload), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return out / "realistic_paper_report.html"

    def _html(self, payload):
        s = _summary(payload)
        cards = [("실전 판정", s["live_readiness"]), ("초기 가상 원금", s["initial_cash_krw"]), ("최종 가상 자산", s["final_equity_krw"]), ("총 손익", s["total_pnl_krw"]), ("거래 수", s["trade_count"]), ("PF", s["profit_factor"])]
        card_html = "".join(f"<div class='card'><span>{escape(str(k))}</span><strong>{escape(str(v))}</strong></div>" for k, v in cards)
        source_rows = "".join(f"<tr><td>{r['source']}</td><td>{r['candidate_count']}</td><td>{r['enter_count']}</td><td>{r['pf_realistic_1']}</td><td>{escape(str(r['expectancy_realistic_1']))}</td><td>{r['total_pnl_krw']}</td></tr>" for r in payload["sources"]["source_results"])
        return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>ASTT V5.5.5 Realistic Paper</title><style>body{{margin:0;background:#101827;color:#e5e7eb;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif}}main{{max-width:1120px;margin:auto;padding:28px 18px}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}.card,section{{background:#162033;border:1px solid #29384f;border-radius:8px;padding:16px}}.card span{{color:#9ca3af}}.card strong{{display:block;font-size:22px;margin-top:6px}}table{{width:100%;border-collapse:collapse}}td,th{{border-bottom:1px solid #31415b;padding:9px;text-align:left}}p{{line-height:1.65;color:#cbd5e1}}@media(max-width:800px){{.grid{{grid-template-columns:1fr}}}}</style></head><body><main><h1>ASTT V5.5.5 Realistic Paper Execution Ledger</h1><div class="grid">{card_html}</div><section><h2>한눈에 보는 결론</h2><p>이 리포트는 실제 주문이 아니라 PAPER 검증입니다. 하지만 체결과 손익은 실제 돈을 넣었다고 가정해 계산했습니다. WAIT/CANCEL은 매수하지 않은 후보이므로 손익에 포함하지 않습니다. 0.05% 비용 조건에서 버티지 못하면 실전 금지입니다.</p></section><section><h2>후보 source별 결과</h2><table><thead><tr><th>Source</th><th>Candidate</th><th>ENTER</th><th>PF</th><th>Expectancy</th><th>PnL</th></tr></thead><tbody>{source_rows}</tbody></table></section><section><h2>실전 전환 판단</h2><p><b>{escape(s['live_readiness'])}</b></p></section></main></body></html>"""

    def _md(self, payload):
        s = _summary(payload)
        return f"# ASTT V5.5.5 Realistic Paper Report\n\n- live_readiness: {s['live_readiness']}\n- trade_count: {s['trade_count']}\n- total_pnl_krw: {s['total_pnl_krw']}\n"


def _summary(payload):
    v = payload["validation"]
    sessions = v.get("sessions", [])
    initial = sessions[-1].get("initial_cash_krw", 500000) if sessions else 500000
    final = sessions[-1].get("final_equity_krw", initial) if sessions else initial
    return {"schema_version": "1.0", "generated_at": payload.get("generated_at"), "live_readiness": "LIVE_NOT_ALLOWED", "initial_cash_krw": initial, "final_equity_krw": final, "total_pnl_krw": v.get("total_pnl_krw", 0.0), "total_return_pct": v.get("total_return_pct", 0.0), "trade_count": v.get("trade_count", 0), "profit_factor": v.get("profit_factor", 0.0), "expectancy_pct": v.get("expectancy_pct")}
