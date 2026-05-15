from __future__ import annotations

import json
import shutil
from pathlib import Path

from replay_lab.export.main_import_contract import MainImportArtifact
from replay_lab.paths import REPLAY_STORE_DIR


def export_approved_patch(patch_path: Path, validation: dict | None = None, source_experiment_id: str = "") -> Path:
    patch = json.loads(patch_path.read_text(encoding="utf-8"))
    if patch.get("status") != "APPROVED":
        raise ValueError("Only APPROVED patches can be exported to the main app")
    artifact = MainImportArtifact(
        artifact_type="config_patch",
        status="APPROVED",
        source_experiment_id=source_experiment_id or patch.get("source_experiment_id", ""),
        base_config_version=patch["base_config_version"],
        target_config_version=patch["target_config_version"].replace("_candidate", ""),
        patch=patch.get("patch", {}),
        validation=validation or {},
    )
    out_dir = REPLAY_STORE_DIR / "exports" / "main_app" / "approved_config_patches"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{patch['patch_id']}_APPROVED.json"
    out.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
    return out


def export_research_summary(experiment_id: str) -> Path:
    exp_dir = REPLAY_STORE_DIR / "experiments" / experiment_id
    metrics_path = exp_dir / "metrics.json"
    report_path = exp_dir / "report.md"
    if not metrics_path.exists() or not report_path.exists():
        raise FileNotFoundError("Experiment metrics.json and report.md are required for research summary export")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    out_dir = REPLAY_STORE_DIR / "exports" / "main_app" / "research_summary"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "artifact_type": "research_summary",
        "schema_version": "1.0",
        "status": "COMPLETED",
        "source_experiment_id": experiment_id,
        "metrics": metrics,
        "report_path": str(out_dir / "latest_replay_report.md"),
        "note": "Research summaries are readable by the main app but do not change configuration.",
    }
    out = out_dir / "latest_replay_summary.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copy2(report_path, out_dir / "latest_replay_report.md")
    return out

