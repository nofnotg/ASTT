from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

from app.config import ROOT_DIR
from replay_lab.export.main_import_contract import MainImportArtifact


EXPORT_DIR = ROOT_DIR / "replay_store" / "exports" / "main_app" / "approved_config_patches"
SUMMARY_DIR = ROOT_DIR / "replay_store" / "exports" / "main_app" / "research_summary"
BACKUP_DIR = ROOT_DIR / "config" / "backups"


def discover_artifacts() -> list[Path]:
    if not EXPORT_DIR.exists():
        return []
    return sorted(EXPORT_DIR.glob("*_APPROVED.json"))


def preview() -> list[dict]:
    artifacts = []
    for path in discover_artifacts():
        data = json.loads(path.read_text(encoding="utf-8"))
        artifact = MainImportArtifact(**data)
        artifact.assert_importable()
        artifacts.append({"path": str(path), "target_config_version": artifact.target_config_version, "patch": artifact.patch})
    summary_path = SUMMARY_DIR / "latest_replay_summary.json"
    if summary_path.exists():
        data = json.loads(summary_path.read_text(encoding="utf-8"))
        artifacts.append({"path": str(summary_path), "artifact_type": "research_summary", "source_experiment_id": data.get("source_experiment_id"), "metrics": data.get("metrics", {})})
    return artifacts


def backup_configs() -> Path:
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    target = BACKUP_DIR / stamp
    target.mkdir(parents=True, exist_ok=True)
    for path in (ROOT_DIR / "config").glob("*.yaml"):
        shutil.copy2(path, target / path.name)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preview APPROVED Replay Lab artifacts for main app import")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--backup-only", action="store_true")
    args = parser.parse_args(argv)
    if args.backup_only:
        print(f"backup: {backup_configs()}")
        return 0
    if args.preview:
        print(json.dumps(preview(), ensure_ascii=False, indent=2))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

