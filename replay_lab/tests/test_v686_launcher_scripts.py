from __future__ import annotations

from pathlib import Path


def test_v686_launcher_scripts_exist_and_do_not_call_orders() -> None:
    for name in ("start_astt_dashboard.ps1", "check_astt_dashboard.ps1", "start_v686_paper_runtime.ps1", "build_v686_reports.ps1"):
        text = (Path("scripts") / name).read_text(encoding="utf-8")
        assert "orders/test" not in text
        assert "withdraw" not in text.lower()
