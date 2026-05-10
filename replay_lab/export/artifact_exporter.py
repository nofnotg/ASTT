from __future__ import annotations

import json
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

