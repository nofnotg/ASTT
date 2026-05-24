# ASTT V5.R3 Strategy Learning Report

## Conclusion
- Live readiness: LIVE_NOT_ALLOWED
- Paper trades: 0
- PnL evaluable: False
- Real orders enabled: False

## Market Regime
- Dominant regime: CHOP
- BTC return pct: -0.2854954390362788
- Breadth up ratio: 0.0

## Setup Candidates
- Candidate count: 64
- By setup: {"LEADER_ROTATION_SURGE": {"count": 15, "avg_score": 61.24343452961645, "grade_counts": {"B": 6, "A": 3, "C": 5, "S": 1}}, "PULLBACK_RECLAIM": {"count": 11, "avg_score": 71.47090198031368, "grade_counts": {"B": 5, "A": 3, "S": 3}}, "ROLE_FLIP_SUPPORT": {"count": 9, "avg_score": 55.93913440151499, "grade_counts": {"B": 4, "C": 5}}, "VWAP_RECLAIM_WITH_VOLUME": {"count": 19, "avg_score": 60.76713919213459, "grade_counts": {"B": 7, "C": 8, "S": 1, "A": 3}}, "RANGE_BREAKOUT": {"count": 8, "avg_score": 71.22333391128896, "grade_counts": {"S": 2, "A": 3, "B": 3}}, "COMPRESSION_EXPANSION": {"count": 2, "avg_score": 67.13875598086125, "grade_counts": {"B": 1, "A": 1}}}

## Scenario Replay
- Scenario count: 144
- Scenario types: {"ALT_ROTATION": 15, "PULLBACK_SUCCESS": 11, "BTC_CHOP": 11, "VOLUME_SURGE": 19, "BREAKOUT_FAIL": 8, "FAKE_RANK_SURGE": 39, "NO_FOLLOW_THROUGH": 41}

## Aggressive Paper Learning
- Enter count: 0
- Win rate: None
- Profit factor: None
- Expectancy pct: None
- Total PnL KRW: 0.0
- Total return pct: 0.0
- Max drawdown pct: 0.0

## LLM Strategy Review
- Completion tokens: 258
- Fallback used: True
- Primary problem: NO_PAPER_ENTER
- Next experiments: ["Replay only RISK_ON and SELECTIVE_ALT clips with setup gating", "Compare B/A/S allocation curves before any V5.6 forward", "Separate avoided loss from missed opportunity in the next scenario batch"]

## Safety
- real_order_enabled: false
- live_order_allowed: false
- auto_apply_allowed: false