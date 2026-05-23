import json

from replay_lab.research.priority_external_strategy_ws_validation import validate_priority_external_strategies_ws_v554


def test_priority_external_strategy_ws_validation_groups_three_strategies(tmp_path, monkeypatch):
    import replay_lab.research.priority_external_strategy_ws_validation as mod

    session = tmp_path / "s1"
    session.mkdir()
    (session / "candidate_events.json").write_text(
        json.dumps(
            [
                {"strategy_id": "VWAP_PULLBACK", "entry_decision": "WAIT", "primary_block_reason": "MICRO_STATE_WEAK", "orderbook_available": True},
                {"strategy_id": "EMA_PULLBACK", "entry_decision": "WAIT", "primary_block_reason": "MICRO_STATE_WEAK", "orderbook_available": True},
                {"strategy_id": "ORDERBOOK_IMBALANCE", "entry_decision": "WAIT", "primary_block_reason": "ORDERBOOK_UNAVAILABLE", "orderbook_available": False},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "REPLAY_STORE_DIR", tmp_path)

    result = validate_priority_external_strategies_ws_v554(tmp_path)

    assert len(result["strategy_results"]) == 3
    assert result["strategy_results"][0]["strategy"] == "VWAP Pullback"
