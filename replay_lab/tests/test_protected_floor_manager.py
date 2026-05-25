from __future__ import annotations

from portfolio.protected_floor_manager import ProtectedFloorManager


def test_protected_floor_caps_loss_multiplier():
    manager = ProtectedFloorManager()

    multiplier, capped = manager.cap_multiplier(1_300_000, -500_000, 1.0)

    assert capped is True
    assert multiplier == 0.6
