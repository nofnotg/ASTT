from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


class HeadControllerV672ReviewHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        data = _read(self.reports_dir / "latest_head_controller_v672_review_summary.json")
        path = self.reports_dir / "latest_head_controller_v672_review_report.html"
        path.write_text(_html(data), encoding="utf-8")
        return {"html": str(path)}


def _html(data: dict[str, Any]) -> str:
    rows = "".join(f"<tr><th>{_esc(k)}</th><td>{_esc(v)}</td></tr>" for k, v in data.items())
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>V6.7.2 Head Controller Review</title><style>body{{font-family:Arial,'Malgun Gothic',sans-serif;background:#f7f9fc;color:#172033;line-height:1.6;margin:0}}main{{max-width:1000px;margin:auto;padding:24px}}header{{background:#0f172a;color:white;padding:28px}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{border-bottom:1px solid #e2e8f0;padding:10px;text-align:left}}</style></head>
<body><header><h1>V6.7.2 Head Controller Review</h1><p>BTCDOM Index Proxy 결과 요약입니다. 자동 적용과 실제 주문은 금지입니다.</p></header><main><table>{rows}</table></main></body></html>"""


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)
