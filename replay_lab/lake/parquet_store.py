from __future__ import annotations

from pathlib import Path

import pandas as pd


class ParquetStore:
    def write(self, frame: pd.DataFrame, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(path, index=False)
        return path

    def read(self, path: Path) -> pd.DataFrame:
        return pd.read_parquet(path)

    def append_dedup(self, frame: pd.DataFrame, path: Path, subset: list[str]) -> pd.DataFrame:
        if path.exists():
            existing = self.read(path)
            frame = pd.concat([existing, frame], ignore_index=True)
        if subset and not frame.empty:
            frame = frame.drop_duplicates(subset=subset).sort_values(subset)
        self.write(frame, path)
        return frame

