from research_external.strategy_candidate_registry import build_external_strategy_registry, get_initial_strategy_specs


def test_external_strategy_registry_creates_initial_seven_specs(tmp_path):
    result = build_external_strategy_registry(output_dir=tmp_path)
    specs = get_initial_strategy_specs()
    ids = [spec["strategy_id"] for spec in specs]

    assert result["strategy_specs_created"] == 7
    assert len(ids) == len(set(ids))
    assert (tmp_path / "external_strategy_registry.json").exists()
