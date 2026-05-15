import json

import pytest

from replay_lab.export.artifact_exporter import export_approved_patch
from replay_lab.export.main_import_contract import MainImportArtifact


def test_draft_artifact_is_not_importable():
    artifact = MainImportArtifact(artifact_type="config_patch", status="DRAFT", source_experiment_id="exp", base_config_version="v0.1", target_config_version="v0.2")
    with pytest.raises(ValueError):
        artifact.assert_importable()


def test_export_requires_approved_patch(tmp_path):
    patch = tmp_path / "patch.json"
    patch.write_text(json.dumps({"patch_id": "patch_test", "status": "DRAFT", "base_config_version": "v0.1", "target_config_version": "v0.2_candidate", "patch": {}}), encoding="utf-8")
    with pytest.raises(ValueError):
        export_approved_patch(patch)
