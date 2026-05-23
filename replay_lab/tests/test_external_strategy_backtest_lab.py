import json

from replay_lab.research.external_strategy_backtest_lab import run_external_strategy_lab


def test_external_strategy_lab_excludes_wait_cancel_and_applies_realistic_cost(tmp_path, monkeypatch):
    import replay_lab.research.external_strategy_backtest_lab as lab

    monkeypatch.setattr(lab, "REPLAY_STORE_DIR", tmp_path)
    source = tmp_path / "reports" / "upbit_real_api"
    source.mkdir(parents=True)
    (source / "candidate_second_window_validation_v553.json").write_text(
        json.dumps(
            {
                "results": [
                    {"data_quality": "GOOD", "entry_decision": "WAIT", "included_in_pnl": False, "net_pnl_pct": None},
                    {"data_quality": "GOOD", "entry_decision": "CANCEL", "included_in_pnl": False, "net_pnl_pct": None},
                    {"data_quality": "PARTIAL", "entry_decision": "ENTER", "included_in_pnl": True, "net_pnl_pct": -0.1, "gross_pnl_pct": 0.05, "net_pnl_krw": -10, "hold_seconds": 5},
                ]
            }
        ),
        encoding="utf-8",
    )

    result = run_external_strategy_lab(strategy_specs=[{"strategy_id": "s1", "strategy_name": "S1", "name": "S1", "strategy_family": "breakout", "license_status": "OK"}], cost_scenario="realistic_1")

    assert result["mock_data_excluded"] is True
    row = result["strategy_results"][0]
    assert row["pf_realistic_1"] < 1.1
    assert row["survives_cost"] is False
