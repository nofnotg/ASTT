import json

from replay_lab.export.artifact_exporter import export_research_summary
from replay_lab.paths import REPLAY_STORE_DIR


def test_research_summary_export(tmp_path, monkeypatch):
    monkeypatch.setattr("replay_lab.export.artifact_exporter.REPLAY_STORE_DIR", tmp_path)
    exp_dir = tmp_path / "experiments" / "exp_test"
    exp_dir.mkdir(parents=True)
    (exp_dir / "metrics.json").write_text(json.dumps({"entries": 1}), encoding="utf-8")
    (exp_dir / "report.md").write_text("# report", encoding="utf-8")
    out = export_research_summary("exp_test")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["artifact_type"] == "research_summary"
    assert data["metrics"]["entries"] == 1
