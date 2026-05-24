from capital.entry_ladder import build_entry_ladder


def test_entry_ladder_uses_30_30_40():
    plan = build_entry_ladder(500000)["ladder_plan"]
    assert [row["pct"] for row in plan] == [0.3, 0.3, 0.4]
    assert sum(row["krw"] for row in plan) == 500000
