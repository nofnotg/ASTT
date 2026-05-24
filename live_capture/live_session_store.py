from __future__ import annotations

import json
from pathlib import Path


class LiveSessionStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def append_jsonl(self, relative_path: str, row: dict) -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    def write_json(self, relative_path: str, row: dict) -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(row, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
