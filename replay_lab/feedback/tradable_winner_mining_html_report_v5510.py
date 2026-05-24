from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR


class TradableWinnerMiningHTMLReportV5510:
    def build(self, output_dir: str | Path = "docs/reports") -> dict:
        payload = _read(REPLAY_STORE_DIR / "tradable_winner" / "tradable_winners.json")
        summary = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), **payload.get("summary", {})}
        return _write_report(output_dir, "latest_tradable_winner_mining", "Tradable Winner Mining V5.5.10", summary)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"summary": {}}


def _write_report(output_dir: str | Path, stem: str, title: str, summary: dict) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{stem}_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    md = f"# {title}\n\n실제 주문 금지. effective-return-first 기준입니다.\n"
    (out / f"{stem}_report.md").write_text(md, encoding="utf-8")
    html = f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title></head><body><h1>{title}</h1><p>실제 주문 금지. 50만 원 체결 가능성 선필터.</p><pre>{json.dumps(summary, ensure_ascii=False, indent=2)}</pre></body></html>"
    (out / f"{stem}_report.html").write_text(html, encoding="utf-8")
    return summary
