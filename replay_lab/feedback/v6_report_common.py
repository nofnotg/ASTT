from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def build_json_html_report(source_json: str, html_name: str, title: str, output_dir: str | Path = "docs/reports") -> dict[str, str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    payload = _read(root / source_json)
    html_path = root / html_name
    html_path.write_text(_html(title, payload), encoding="utf-8")
    return {"html": str(html_path), "source": str(root / source_json)}


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _html(title: str, payload: dict[str, Any]) -> str:
    safe = html.escape(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{html.escape(title)}</title>"
        "<style>body{font-family:Arial,sans-serif;margin:32px;color:#1f2937}"
        "pre{background:#f6f8fa;padding:16px;overflow:auto}h1{font-size:24px}</style></head><body>"
        f"<h1>{html.escape(title)}</h1><pre>{safe}</pre></body></html>"
    )
