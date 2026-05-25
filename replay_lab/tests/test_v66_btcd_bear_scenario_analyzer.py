from __future__ import annotations

from analysis.v66_btcd_saved_loss_missed_profit import net_effect


def test_v66_saved_loss_net_effect():
    assert net_effect(1000, 250) == 750

