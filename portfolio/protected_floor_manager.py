from __future__ import annotations


class ProtectedFloorManager:
    def floor_for_equity(self, equity_krw: float) -> float:
        equity = float(equity_krw)
        if equity >= 1_300_000:
            return 1_000_000
        if equity >= 1_000_000:
            return 750_000
        if equity >= 750_000:
            return 600_000
        return 0.0

    def cap_multiplier(self, equity_krw: float, proposed_pnl_krw: float, multiplier: float) -> tuple[float, bool]:
        floor = self.floor_for_equity(equity_krw)
        if floor <= 0 or proposed_pnl_krw >= 0:
            return multiplier, False
        worst_after = equity_krw + proposed_pnl_krw * multiplier
        if worst_after >= floor:
            return multiplier, False
        allowed_loss = max(0.0, equity_krw - floor)
        capped = allowed_loss / abs(proposed_pnl_krw) if proposed_pnl_krw else 0.0
        return max(0.0, min(multiplier, capped)), True
