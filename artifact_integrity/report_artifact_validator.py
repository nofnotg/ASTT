from __future__ import annotations

import json
from pathlib import Path

from head_controller.llm_secret_sanitizer import scan_report_secrets

FORBIDDEN_READINESS = {"MICRO_LIVE_READY", "LIVE_READY"}


def validate_report_artifacts(reports_dir: str | Path) -> dict:
    reports = [Path(reports_dir) / name for name in [
        "latest_entry_discovery_summary.json",
        "latest_head_controller_draft_summary.json",
        "latest_realistic_paper_summary.json",
    ]]
    failures: list[str] = []
    warnings: list[str] = []
    checked: list[str] = []
    entry_count = None
    stale = False
    for path in reports:
        if not path.exists():
            warnings.append(f"MISSING_REPORT:{path.name}")
            continue
        checked.append(str(path))
        data = json.loads(path.read_text(encoding="utf-8"))
        manifest = data.get("artifact_manifest")
        readiness = data.get("live_readiness") or data.get("live_readiness_opinion")
        if readiness in FORBIDDEN_READINESS:
            failures.append(f"FORBIDDEN_READINESS:{path.name}")
        if path.name == "latest_entry_discovery_summary.json":
            entry_count = int(data.get("candidate_count", 0) or 0)
            if not manifest:
                failures.append("ENTRY_DISCOVERY_MISSING_MANIFEST")
                stale = True
            else:
                if manifest.get("is_test_artifact"):
                    failures.append("ENTRY_DISCOVERY_TEST_ARTIFACT")
                    stale = True
                if manifest.get("generated_by") == "TEST":
                    failures.append("ENTRY_DISCOVERY_GENERATED_BY_TEST")
                    stale = True
                if entry_count < int(manifest.get("min_expected_candidate_count", 30)):
                    failures.append("ENTRY_DISCOVERY_CANDIDATE_COUNT_LOW")
                    stale = True
                if manifest.get("artifact_integrity_status") == "FAIL":
                    failures.append("ENTRY_DISCOVERY_MANIFEST_FAIL")
                    stale = True
    secret_scan = scan_report_secrets(reports_dir)
    if secret_scan["secret_scan_status"] != "PASS":
        failures.extend(f"SECRET_SCAN:{Path(f).name}" for f in secret_scan["failures"])
    return {
        "artifact_integrity_status": "FAIL" if failures else ("WARNING" if warnings else "PASS"),
        "checked_reports": checked,
        "failures": failures,
        "warnings": warnings,
        "latest_entry_discovery_candidate_count": entry_count or 0,
        "stale_or_test_artifact_detected": stale,
        "secret_scan": secret_scan,
    }
