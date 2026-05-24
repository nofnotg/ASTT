from execution.entry_discovery_simulator import simulate_entry_discovery


def test_entry_discovery_excludes_diagnostic_from_live():
    wait = {"rows": [{"best_mfe_pct": 0.25, "worst_mae_pct": -0.1, "wait_classification": "MISSED_WIN"}]}
    result = simulate_entry_discovery(wait, ["STRICT", "ENTRY_DISCOVERY", "DIAGNOSTIC_ONLY"])
    rows = {row["profile"]: row for row in result["profiles"]}
    assert rows["STRICT"]["enter"] == 0
    assert rows["ENTRY_DISCOVERY"]["enter"] == 1
    assert rows["ENTRY_DISCOVERY"]["research_only"] is True
    assert rows["DIAGNOSTIC_ONLY"]["enter"] == 0
