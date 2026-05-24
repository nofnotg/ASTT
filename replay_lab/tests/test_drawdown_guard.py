from capital.drawdown_guard import check_drawdown_guard, update_drawdown


def test_drawdown_guard_blocks_session_drawdown():
    dd = update_drawdown(494000, 500000)
    result = check_drawdown_guard(dd)
    assert result["allowed"] is False
