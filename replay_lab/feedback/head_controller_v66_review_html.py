from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


class HeadControllerV66ReviewHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        summary = _read(self.reports_dir / "latest_head_controller_v66_review_summary.json")
        path = self.reports_dir / "latest_head_controller_v66_review_report.html"
        path.write_text(_html(summary), encoding="utf-8")
        return {"html": str(path)}


def _html(summary: dict[str, Any]) -> str:
    rows = "".join(f"<li>{_esc(item)}</li>" for item in summary.get("next_experiments", []))
    risks = "".join(f"<li>{_esc(item)}</li>" for item in summary.get("risk_flags", []))
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Head Controller V6.6 Review</title>
<style>body{{font-family:Arial,'Malgun Gothic',sans-serif;background:#f7f9fc;color:#172033;line-height:1.6;margin:0}}header{{background:#111827;color:white;padding:28px}}main{{max-width:980px;margin:auto;padding:24px}}section{{background:white;border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin-top:16px}}</style></head>
<body><header><h1>Head Controller V6.6 Review</h1><p>LLM/Head Controller는 결과 해석 보조이며 active config를 자동 적용하지 않습니다.</p></header>
<main><section><h2>요약</h2><p>live_readiness_opinion: <strong>{_esc(summary.get('live_readiness_opinion'))}</strong></p><p>best_scenario: <strong>{_esc(summary.get('best_scenario'))}</strong></p><p>forward_candidates: {_esc(summary.get('forward_candidates'))}</p><p>research_only_candidates: {_esc(summary.get('research_only_candidates'))}</p></section>
<section><h2>다음 실험</h2><ul>{rows}</ul></section><section><h2>위험 플래그</h2><ul>{risks}</ul></section>
<section><h2>안전 확인</h2><p>auto_apply_allowed={_esc(summary.get('auto_apply_allowed'))}, live_order_allowed={_esc(summary.get('live_order_allowed'))}, real_order_enabled={_esc(summary.get('real_order_enabled'))}</p></section></main></body></html>"""


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)

