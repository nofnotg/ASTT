from capital.entry_ladder import build_entry_ladder
from capital.exit_ladder import build_exit_ladder
from execution.ladder_position_manager import validate_ladder_position_plan


def test_ladder_position_manager_validates_pct_totals():
    result = validate_ladder_position_plan(build_entry_ladder(500000), build_exit_ladder())
    assert result["valid"] is True
    assert result["entry_pct_total"] == 1.0
    assert result["exit_pct_total"] == 1.0
