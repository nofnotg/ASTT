from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


class HeadControllerV65ReviewHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        summary = _read(self.reports_dir / "latest_head_controller_v65_review_summary.json")
        path = self.reports_dir / "latest_head_controller_v65_review_report.html"
        body = "".join(
            f"<tr><td>{html.escape(str(key))}</td><td>{html.escape(str(value))}</td></tr>"
            for key, value in summary.items()
        )
        path.write_text(
            f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>ASTT V6.5 Head Controller Review</title>
<style>body{{font-family:Arial,'Malgun Gothic',sans-serif;background:#f8fafc;color:#172033;margin:0}}header{{background:#111827;color:white;padding:28px}}main{{max-width:980px;margin:auto;padding:22px}}table{{width:100%;border-collapse:collapse;background:white}}td,th{{border-bottom:1px solid #e5e7eb;padding:10px;text-align:left}}th{{background:#eef2ff}}</style></head>
<body><header><h1>ASTT V6.5 Head Controller Review</h1><p>LLM 자동 적용 없이 MA 필터/라우터 결과를 보수적으로 복기했습니다.</p></header><main><table>{body}</table><p>LIVE 전환은 금지이며, 다음 단계는 forward paper 검증입니다.</p></main></body></html>""",
            encoding="utf-8",
        )
        return {"html": str(path)}


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
