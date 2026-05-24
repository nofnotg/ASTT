# ASTT V5.R2 Head Controller Review

## Head Controller Summary

```json
{
  "live_readiness_opinion": "PROJECT_KILL_RECOMMENDED",
  "primary_problem": "PROJECT_LOW_EXPECTANCY",
  "timing_assessment": "NOT_READY",
  "recommended_event_types": [
    "VOLUME_SPIKE",
    "ORDERFLOW_SHIFT"
  ],
  "event_types_to_pause": [
    "MARKET_RANK_SURGE",
    "SPREAD_CONTRACTION",
    "DEPTH_RECOVERY",
    "RAW_MICRO_WINNER"
  ],
  "state_transition_findings": [],
  "next_experiments": [
    "Run one V5.R3 high-volatility collection with tightened ARMED rules"
  ],
  "risk_flags": [
    "ENTRY_WINDOW remains zero",
    "CONFIRMED remains zero",
    "paper ENTER remains zero"
  ],
  "config_proposals": [],
  "auto_apply_allowed": false,
  "live_order_allowed": false,
  "active": false,
  "human_approved": false,
  "project_decision": "KILL_RECOMMENDED",
  "scorecard_score": 26,
  "calibration_recommendations": [
    "Use armed min_required_conditions=3",
    "Keep TRIGGERED->CONFIRMED strict until ENTRY_WINDOW exists"
  ],
  "llm_provider": "openai",
  "llm_used": true,
  "fallback_used": false
}
```

## Primary Problem

```json
{
  "live_readiness_opinion": "PROJECT_KILL_RECOMMENDED",
  "primary_problem": "PROJECT_LOW_EXPECTANCY",
  "timing_assessment": "NOT_READY",
  "recommended_event_types": [
    "VOLUME_SPIKE",
    "ORDERFLOW_SHIFT"
  ],
  "event_types_to_pause": [
    "MARKET_RANK_SURGE",
    "SPREAD_CONTRACTION",
    "DEPTH_RECOVERY",
    "RAW_MICRO_WINNER"
  ],
  "state_transition_findings": [],
  "next_experiments": [
    "Run one V5.R3 high-volatility collection with tightened ARMED rules"
  ],
  "risk_flags": [
    "ENTRY_WINDOW remains zero",
    "CONFIRMED remains zero",
    "paper ENTER remains zero"
  ],
  "config_proposals": [],
  "auto_apply_allowed": false,
  "live_order_allowed": false,
  "active": false,
  "human_approved": false,
  "project_decision": "KILL_RECOMMENDED",
  "scorecard_score": 26,
  "calibration_recommendations": [
    "Use armed min_required_conditions=3",
    "Keep TRIGGERED->CONFIRMED strict until ENTRY_WINDOW exists"
  ],
  "llm_provider": "openai",
  "llm_used": true,
  "fallback_used": false
}
```

## Project Decision

```json
{
  "live_readiness_opinion": "PROJECT_KILL_RECOMMENDED",
  "primary_problem": "PROJECT_LOW_EXPECTANCY",
  "timing_assessment": "NOT_READY",
  "recommended_event_types": [
    "VOLUME_SPIKE",
    "ORDERFLOW_SHIFT"
  ],
  "event_types_to_pause": [
    "MARKET_RANK_SURGE",
    "SPREAD_CONTRACTION",
    "DEPTH_RECOVERY",
    "RAW_MICRO_WINNER"
  ],
  "state_transition_findings": [],
  "next_experiments": [
    "Run one V5.R3 high-volatility collection with tightened ARMED rules"
  ],
  "risk_flags": [
    "ENTRY_WINDOW remains zero",
    "CONFIRMED remains zero",
    "paper ENTER remains zero"
  ],
  "config_proposals": [],
  "auto_apply_allowed": false,
  "live_order_allowed": false,
  "active": false,
  "human_approved": false,
  "project_decision": "KILL_RECOMMENDED",
  "scorecard_score": 26,
  "calibration_recommendations": [
    "Use armed min_required_conditions=3",
    "Keep TRIGGERED->CONFIRMED strict until ENTRY_WINDOW exists"
  ],
  "llm_provider": "openai",
  "llm_used": true,
  "fallback_used": false
}
```

## Scorecard Score

```json
{
  "live_readiness_opinion": "PROJECT_KILL_RECOMMENDED",
  "primary_problem": "PROJECT_LOW_EXPECTANCY",
  "timing_assessment": "NOT_READY",
  "recommended_event_types": [
    "VOLUME_SPIKE",
    "ORDERFLOW_SHIFT"
  ],
  "event_types_to_pause": [
    "MARKET_RANK_SURGE",
    "SPREAD_CONTRACTION",
    "DEPTH_RECOVERY",
    "RAW_MICRO_WINNER"
  ],
  "state_transition_findings": [],
  "next_experiments": [
    "Run one V5.R3 high-volatility collection with tightened ARMED rules"
  ],
  "risk_flags": [
    "ENTRY_WINDOW remains zero",
    "CONFIRMED remains zero",
    "paper ENTER remains zero"
  ],
  "config_proposals": [],
  "auto_apply_allowed": false,
  "live_order_allowed": false,
  "active": false,
  "human_approved": false,
  "project_decision": "KILL_RECOMMENDED",
  "scorecard_score": 26,
  "calibration_recommendations": [
    "Use armed min_required_conditions=3",
    "Keep TRIGGERED->CONFIRMED strict until ENTRY_WINDOW exists"
  ],
  "llm_provider": "openai",
  "llm_used": true,
  "fallback_used": false
}
```

## Recommended Event Types

```json
{
  "live_readiness_opinion": "PROJECT_KILL_RECOMMENDED",
  "primary_problem": "PROJECT_LOW_EXPECTANCY",
  "timing_assessment": "NOT_READY",
  "recommended_event_types": [
    "VOLUME_SPIKE",
    "ORDERFLOW_SHIFT"
  ],
  "event_types_to_pause": [
    "MARKET_RANK_SURGE",
    "SPREAD_CONTRACTION",
    "DEPTH_RECOVERY",
    "RAW_MICRO_WINNER"
  ],
  "state_transition_findings": [],
  "next_experiments": [
    "Run one V5.R3 high-volatility collection with tightened ARMED rules"
  ],
  "risk_flags": [
    "ENTRY_WINDOW remains zero",
    "CONFIRMED remains zero",
    "paper ENTER remains zero"
  ],
  "config_proposals": [],
  "auto_apply_allowed": false,
  "live_order_allowed": false,
  "active": false,
  "human_approved": false,
  "project_decision": "KILL_RECOMMENDED",
  "scorecard_score": 26,
  "calibration_recommendations": [
    "Use armed min_required_conditions=3",
    "Keep TRIGGERED->CONFIRMED strict until ENTRY_WINDOW exists"
  ],
  "llm_provider": "openai",
  "llm_used": true,
  "fallback_used": false
}
```

## Event Types To Pause

```json
{
  "live_readiness_opinion": "PROJECT_KILL_RECOMMENDED",
  "primary_problem": "PROJECT_LOW_EXPECTANCY",
  "timing_assessment": "NOT_READY",
  "recommended_event_types": [
    "VOLUME_SPIKE",
    "ORDERFLOW_SHIFT"
  ],
  "event_types_to_pause": [
    "MARKET_RANK_SURGE",
    "SPREAD_CONTRACTION",
    "DEPTH_RECOVERY",
    "RAW_MICRO_WINNER"
  ],
  "state_transition_findings": [],
  "next_experiments": [
    "Run one V5.R3 high-volatility collection with tightened ARMED rules"
  ],
  "risk_flags": [
    "ENTRY_WINDOW remains zero",
    "CONFIRMED remains zero",
    "paper ENTER remains zero"
  ],
  "config_proposals": [],
  "auto_apply_allowed": false,
  "live_order_allowed": false,
  "active": false,
  "human_approved": false,
  "project_decision": "KILL_RECOMMENDED",
  "scorecard_score": 26,
  "calibration_recommendations": [
    "Use armed min_required_conditions=3",
    "Keep TRIGGERED->CONFIRMED strict until ENTRY_WINDOW exists"
  ],
  "llm_provider": "openai",
  "llm_used": true,
  "fallback_used": false
}
```

## Calibration Recommendations

```json
{
  "live_readiness_opinion": "PROJECT_KILL_RECOMMENDED",
  "primary_problem": "PROJECT_LOW_EXPECTANCY",
  "timing_assessment": "NOT_READY",
  "recommended_event_types": [
    "VOLUME_SPIKE",
    "ORDERFLOW_SHIFT"
  ],
  "event_types_to_pause": [
    "MARKET_RANK_SURGE",
    "SPREAD_CONTRACTION",
    "DEPTH_RECOVERY",
    "RAW_MICRO_WINNER"
  ],
  "state_transition_findings": [],
  "next_experiments": [
    "Run one V5.R3 high-volatility collection with tightened ARMED rules"
  ],
  "risk_flags": [
    "ENTRY_WINDOW remains zero",
    "CONFIRMED remains zero",
    "paper ENTER remains zero"
  ],
  "config_proposals": [],
  "auto_apply_allowed": false,
  "live_order_allowed": false,
  "active": false,
  "human_approved": false,
  "project_decision": "KILL_RECOMMENDED",
  "scorecard_score": 26,
  "calibration_recommendations": [
    "Use armed min_required_conditions=3",
    "Keep TRIGGERED->CONFIRMED strict until ENTRY_WINDOW exists"
  ],
  "llm_provider": "openai",
  "llm_used": true,
  "fallback_used": false
}
```

## Next Experiments

```json
{
  "live_readiness_opinion": "PROJECT_KILL_RECOMMENDED",
  "primary_problem": "PROJECT_LOW_EXPECTANCY",
  "timing_assessment": "NOT_READY",
  "recommended_event_types": [
    "VOLUME_SPIKE",
    "ORDERFLOW_SHIFT"
  ],
  "event_types_to_pause": [
    "MARKET_RANK_SURGE",
    "SPREAD_CONTRACTION",
    "DEPTH_RECOVERY",
    "RAW_MICRO_WINNER"
  ],
  "state_transition_findings": [],
  "next_experiments": [
    "Run one V5.R3 high-volatility collection with tightened ARMED rules"
  ],
  "risk_flags": [
    "ENTRY_WINDOW remains zero",
    "CONFIRMED remains zero",
    "paper ENTER remains zero"
  ],
  "config_proposals": [],
  "auto_apply_allowed": false,
  "live_order_allowed": false,
  "active": false,
  "human_approved": false,
  "project_decision": "KILL_RECOMMENDED",
  "scorecard_score": 26,
  "calibration_recommendations": [
    "Use armed min_required_conditions=3",
    "Keep TRIGGERED->CONFIRMED strict until ENTRY_WINDOW exists"
  ],
  "llm_provider": "openai",
  "llm_used": true,
  "fallback_used": false
}
```

## Risk Flags

```json
{
  "live_readiness_opinion": "PROJECT_KILL_RECOMMENDED",
  "primary_problem": "PROJECT_LOW_EXPECTANCY",
  "timing_assessment": "NOT_READY",
  "recommended_event_types": [
    "VOLUME_SPIKE",
    "ORDERFLOW_SHIFT"
  ],
  "event_types_to_pause": [
    "MARKET_RANK_SURGE",
    "SPREAD_CONTRACTION",
    "DEPTH_RECOVERY",
    "RAW_MICRO_WINNER"
  ],
  "state_transition_findings": [],
  "next_experiments": [
    "Run one V5.R3 high-volatility collection with tightened ARMED rules"
  ],
  "risk_flags": [
    "ENTRY_WINDOW remains zero",
    "CONFIRMED remains zero",
    "paper ENTER remains zero"
  ],
  "config_proposals": [],
  "auto_apply_allowed": false,
  "live_order_allowed": false,
  "active": false,
  "human_approved": false,
  "project_decision": "KILL_RECOMMENDED",
  "scorecard_score": 26,
  "calibration_recommendations": [
    "Use armed min_required_conditions=3",
    "Keep TRIGGERED->CONFIRMED strict until ENTRY_WINDOW exists"
  ],
  "llm_provider": "openai",
  "llm_used": true,
  "fallback_used": false
}
```

## Config Proposals

```json
{
  "live_readiness_opinion": "PROJECT_KILL_RECOMMENDED",
  "primary_problem": "PROJECT_LOW_EXPECTANCY",
  "timing_assessment": "NOT_READY",
  "recommended_event_types": [
    "VOLUME_SPIKE",
    "ORDERFLOW_SHIFT"
  ],
  "event_types_to_pause": [
    "MARKET_RANK_SURGE",
    "SPREAD_CONTRACTION",
    "DEPTH_RECOVERY",
    "RAW_MICRO_WINNER"
  ],
  "state_transition_findings": [],
  "next_experiments": [
    "Run one V5.R3 high-volatility collection with tightened ARMED rules"
  ],
  "risk_flags": [
    "ENTRY_WINDOW remains zero",
    "CONFIRMED remains zero",
    "paper ENTER remains zero"
  ],
  "config_proposals": [],
  "auto_apply_allowed": false,
  "live_order_allowed": false,
  "active": false,
  "human_approved": false,
  "project_decision": "KILL_RECOMMENDED",
  "scorecard_score": 26,
  "calibration_recommendations": [
    "Use armed min_required_conditions=3",
    "Keep TRIGGERED->CONFIRMED strict until ENTRY_WINDOW exists"
  ],
  "llm_provider": "openai",
  "llm_used": true,
  "fallback_used": false
}
```

## Auto Apply Disabled

```json
{
  "live_readiness_opinion": "PROJECT_KILL_RECOMMENDED",
  "primary_problem": "PROJECT_LOW_EXPECTANCY",
  "timing_assessment": "NOT_READY",
  "recommended_event_types": [
    "VOLUME_SPIKE",
    "ORDERFLOW_SHIFT"
  ],
  "event_types_to_pause": [
    "MARKET_RANK_SURGE",
    "SPREAD_CONTRACTION",
    "DEPTH_RECOVERY",
    "RAW_MICRO_WINNER"
  ],
  "state_transition_findings": [],
  "next_experiments": [
    "Run one V5.R3 high-volatility collection with tightened ARMED rules"
  ],
  "risk_flags": [
    "ENTRY_WINDOW remains zero",
    "CONFIRMED remains zero",
    "paper ENTER remains zero"
  ],
  "config_proposals": [],
  "auto_apply_allowed": false,
  "live_order_allowed": false,
  "active": false,
  "human_approved": false,
  "project_decision": "KILL_RECOMMENDED",
  "scorecard_score": 26,
  "calibration_recommendations": [
    "Use armed min_required_conditions=3",
    "Keep TRIGGERED->CONFIRMED strict until ENTRY_WINDOW exists"
  ],
  "llm_provider": "openai",
  "llm_used": true,
  "fallback_used": false
}
```

## Live Order Disabled

```json
{
  "live_readiness_opinion": "PROJECT_KILL_RECOMMENDED",
  "primary_problem": "PROJECT_LOW_EXPECTANCY",
  "timing_assessment": "NOT_READY",
  "recommended_event_types": [
    "VOLUME_SPIKE",
    "ORDERFLOW_SHIFT"
  ],
  "event_types_to_pause": [
    "MARKET_RANK_SURGE",
    "SPREAD_CONTRACTION",
    "DEPTH_RECOVERY",
    "RAW_MICRO_WINNER"
  ],
  "state_transition_findings": [],
  "next_experiments": [
    "Run one V5.R3 high-volatility collection with tightened ARMED rules"
  ],
  "risk_flags": [
    "ENTRY_WINDOW remains zero",
    "CONFIRMED remains zero",
    "paper ENTER remains zero"
  ],
  "config_proposals": [],
  "auto_apply_allowed": false,
  "live_order_allowed": false,
  "active": false,
  "human_approved": false,
  "project_decision": "KILL_RECOMMENDED",
  "scorecard_score": 26,
  "calibration_recommendations": [
    "Use armed min_required_conditions=3",
    "Keep TRIGGERED->CONFIRMED strict until ENTRY_WINDOW exists"
  ],
  "llm_provider": "openai",
  "llm_used": true,
  "fallback_used": false
}
```
