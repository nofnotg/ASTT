from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


class HeadControllerV67ReviewHTML:
    def __init__(self, reports_dir: str = "docs/reports") -> None:
        self.reports_dir = Path(reports_dir)

    def build(self) -> dict[str, str]:
        data = _read(self.reports_dir / "latest_head_controller_v67_review_summary.json")
        path = self.reports_dir / "latest_head_controller_v67_review_report.html"
        rows = "".join(f"<tr><td>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>" for k, v in data.items())
        path.write_text(f"<!doctype html><html lang='ko'><head><meta charset='utf-8'><title>Head Controller V6.7 Review</title></head><body><h1>Head Controller V6.7 Review</h1><p>자동 적용은 금지이며, 실전 주문은 허용되지 않습니다.</p><table>{rows}</table></body></html>", encoding="utf-8")
        return {"html": str(path)}


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
