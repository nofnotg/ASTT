from __future__ import annotations

import json
from pathlib import Path

from artifact_integrity.report_artifact_validator import validate_report_artifacts
from head_controller.llm_secret_sanitizer import scan_report_secrets
from replay_lab.paths import REPLAY_STORE_DIR


def check_artifact_integrity_v5561(reports_dir: str | Path = "docs/reports") -> dict:
    result = validate_report_artifacts(reports_dir)
    out = REPLAY_STORE_DIR / "reports" / "artifact_integrity_v5561"
    out.mkdir(parents=True, exist_ok=True)
    (out / "artifact_integrity.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result


def scan_report_secrets_v5561(reports_dir: str | Path = "docs/reports") -> dict:
    return scan_report_secrets(reports_dir)
