from capital.exit_ladder import build_exit_ladder


def test_exit_ladder_uses_50_30_20():
    plan = build_exit_ladder()["exit_plan"]
    assert [row["pct"] for row in plan] == [0.5, 0.3, 0.2]
