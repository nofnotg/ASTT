from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR, ROOT_DIR
from replay_lab.research.external_indicator_screen_v553 import screen_external_indicators_v553
from research_external.strategy_candidate_registry import build_external_strategy_registry


@dataclass(frozen=True)
class OpenStrategyHTMLReportBuilder:
    store_dir: Path = REPLAY_STORE_DIR
    docs_root: Path = ROOT_DIR / "docs" / "reports"

    @property
    def out_dir(self) -> Path:
        return self.store_dir / "reports" / "open_strategy"

    def build(self) -> Path:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.docs_root.mkdir(parents=True, exist_ok=True)
        payload = self._payload()
        html = self._html(payload)
        md = self._markdown(payload)
        summary = _summary(payload)
        (self.out_dir / "open_strategy_report.html").write_text(html, encoding="utf-8")
        (self.out_dir / "open_strategy_report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        (self.out_dir / "open_strategy_report.md").write_text(md, encoding="utf-8")
        (self.docs_root / "latest_open_strategy_report.html").write_text(html, encoding="utf-8")
        (self.docs_root / "latest_open_strategy_report.md").write_text(md, encoding="utf-8")
        (self.docs_root / "latest_open_strategy_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return self.out_dir / "open_strategy_report.html"

    def _payload(self) -> dict:
        registry_path = self.out_dir / "external_strategy_registry.json"
        lab_path = self.out_dir / "external_strategy_lab.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.exists() else build_external_strategy_registry()
        lab = json.loads(lab_path.read_text(encoding="utf-8")) if lab_path.exists() else {"strategy_results": []}
        return {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "registry": registry, "indicator_screen": screen_external_indicators_v553(), "external_strategy_lab": lab}

    def _markdown(self, payload: dict) -> str:
        summary = _summary(payload)
        lines = [
            "# ASTT V5.5.3 Open Strategy Research Report",
            "",
            "## 핵심 결론",
            f"- 외부 전략 스펙 수: {summary['strategy_specs_created']}",
            f"- realistic_1 비용 통과 전략: {summary['accepted_strategy_count']}",
            "- WAIT/CANCEL은 실제 매수하지 않은 후보이므로 손익에 넣지 않습니다.",
            "- 외부 전략은 유명하다고 좋은 게 아니라, 업비트 데이터와 비용 조건에서 살아남아야 합니다.",
            "",
            "## 전략별 결과",
            "| Strategy | Family | ENTER | PF realistic_1 | Expectancy | Survives Cost |",
            "|---|---|---:|---:|---:|---|",
        ]
        for row in payload.get("external_strategy_lab", {}).get("strategy_results", []):
            lines.append(f"| {row['strategy_name']} | {row['strategy_family']} | {row['enter_count']} | {row['pf_realistic_1']:.4f} | {row['expectancy_realistic_1']:.4f} | {row['survives_cost']} |")
        return "\n".join(lines) + "\n"

    def _html(self, payload: dict) -> str:
        summary = _summary(payload)
        rows = payload.get("external_strategy_lab", {}).get("strategy_results", [])
        row_html = "".join(
            "<tr>"
            f"<td>{escape(row['strategy_name'])}</td>"
            f"<td>{escape(row['strategy_family'])}</td>"
            f"<td>{row['enter_count']}</td>"
            f"<td>{row['pf_realistic_1']:.4f}</td>"
            f"<td>{row['expectancy_realistic_1']:.4f}%</td>"
            f"<td>{'PASS' if row['survives_cost'] else 'FAIL'}</td>"
            "</tr>"
            for row in rows
        )
        cards = [
            ("수집 전략", summary["strategy_specs_created"]),
            ("지표 그룹", len(summary["indicator_groups"])),
            ("라이선스 검토 필요", summary["license_review_required_count"]),
            ("비용 통과", summary["accepted_strategy_count"]),
        ]
        card_html = "".join(f"<div class='card'><span>{escape(str(k))}</span><strong>{escape(str(v))}</strong></div>" for k, v in cards)
        return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>ASTT Open Strategy Lab</title><style>body{{margin:0;background:#f8fafc;color:#172033;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif}}main{{max-width:1080px;margin:auto;padding:28px 18px}}.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}}.card,section{{background:white;border:1px solid #dbe3ef;border-radius:8px;padding:16px;box-shadow:0 10px 30px rgba(15,23,42,.06)}}.card span{{display:block;color:#64748b;font-size:13px}}.card strong{{display:block;font-size:24px;margin-top:6px}}section{{margin-top:16px}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{border-bottom:1px solid #e2e8f0;text-align:left;padding:10px}}p{{line-height:1.65;color:#475569}}@media(max-width:760px){{.grid{{grid-template-columns:1fr}}}}</style></head><body><main><h1>ASTT V5.5.3 Open Strategy Research Lab</h1><div class="grid">{card_html}</div><section><h2>일반 투자자용 해석</h2><p>PF가 1보다 작으면 잃은 돈이 번 돈보다 많다는 뜻입니다. realistic_1은 수수료와 0.05% 슬리피지, 500ms 지연을 포함한 최소 비용 조건입니다. WAIT/CANCEL은 실제 매수하지 않은 후보이므로 손익에 넣으면 안 됩니다.</p></section><section><h2>외부 전략 검증 결과</h2><table><thead><tr><th>Strategy</th><th>Family</th><th>ENTER</th><th>PF realistic_1</th><th>Expectancy</th><th>Cost</th></tr></thead><tbody>{row_html}</tbody></table></section><section><h2>살아남은 전략</h2><p>{escape(', '.join(row['strategy_name'] for row in rows if row['survives_cost']) or '없음')}</p></section><section><h2>폐기 또는 추가 검증 전략</h2><p>{escape(', '.join(row['strategy_name'] for row in rows if not row['survives_cost']) or '없음')}</p></section></main></body></html>"""


def _summary(payload: dict) -> dict:
    registry = payload.get("registry", {})
    lab = payload.get("external_strategy_lab", {})
    indicator = payload.get("indicator_screen", {})
    return {
        "schema_version": "1.0",
        "generated_at": payload.get("generated_at"),
        "source_count": registry.get("source_count", 0),
        "strategy_specs_created": registry.get("strategy_specs_created", 0),
        "indicator_groups": indicator.get("indicator_groups", []),
        "license_review_required_count": registry.get("license_review_required_count", 0),
        "do_not_use_count": registry.get("do_not_use_count", 0),
        "accepted_strategy_count": lab.get("accepted_strategy_count", 0),
    }
