from research_external.strategy_candidate_registry import get_initial_strategy_specs
from research_external.strategy_spec_schema import validate_strategy_spec


def test_strategy_spec_schema_validates_required_fields_and_license():
    spec = get_initial_strategy_specs()[0]
    result = validate_strategy_spec(spec)

    assert result["valid"] is True
    assert result["missing_fields"] == []


def test_strategy_spec_schema_rejects_bad_license():
    spec = {**get_initial_strategy_specs()[0], "license_status": "MAYBE"}

    result = validate_strategy_spec(spec)

    assert result["valid"] is False
    assert "invalid_license_status" in result["warnings"]
