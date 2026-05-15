from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
REPLAY_STORE_DIR = ROOT_DIR / "replay_store"


def ensure_replay_store() -> None:
    for relative in [
        "raw",
        "normalized",
        "features",
        "experiments",
        "reports",
        "exports",
        "manifests",
    ]:
        (REPLAY_STORE_DIR / relative).mkdir(parents=True, exist_ok=True)

