from datetime import datetime

import pytest

from replay_lab.clock.replay_clock import ReplayClock


def test_replay_clock_blocks_future_data():
    clock = ReplayClock(datetime(2026, 2, 10, 8, 50))
    clock.assert_not_future(datetime(2026, 2, 10, 8, 50))
    with pytest.raises(RuntimeError):
        clock.assert_not_future(datetime(2026, 2, 10, 8, 51))


def test_replay_clock_advance_cannot_go_backwards():
    clock = ReplayClock(datetime(2026, 2, 10, 8, 50))
    clock.advance_to(datetime(2026, 2, 10, 9, 3))
    with pytest.raises(ValueError):
        clock.advance_to(datetime(2026, 2, 10, 9, 0))

