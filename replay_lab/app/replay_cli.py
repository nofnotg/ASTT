from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path

from replay_lab.clock.replay_clock import ReplayClock
from replay_lab.data.historical_loader import HistoricalLoader
from replay_lab.data.replay_data_provider import ReplayDataProvider
from replay_lab.export.artifact_exporter import export_approved_patch, export_research_summary
from replay_lab.feedback.athena_reviewer import review_experiment
from replay_lab.feedback.fear_divergence_report import FearDivergenceReportBuilder
from replay_lab.feedback.fear_exhaustion_v41_report import FearExhaustionV41ReportBuilder
from replay_lab.feedback.investment_report import InvestmentReportBuilder
from replay_lab.feedback.investment_v2_report import InvestmentV2ReportBuilder
from replay_lab.feedback.report_catalog import ReplayReportCatalog
from replay_lab.feedback.small_seed_report import SmallSeedReportBuilder
from replay_lab.feedback.structure_reversal_report_v5 import StructureReversalV5ReportBuilder
from replay_lab.feedback.fractal_v52_report import FractalV52ReportBuilder
from replay_lab.feedback.fractal_v53_report import FractalV53ReportBuilder
from replay_lab.feedback.edge_isolation_report_v54 import EdgeIsolationV54ReportBuilder
from replay_lab.feedback.micro_execution_html_report import MicroExecutionHTMLReportBuilder
from replay_lab.feedback.forward_micro_html_report import ForwardMicroHTMLReportBuilder
from replay_lab.feedback.upbit_real_api_html_report import UpbitRealAPIHTMLReportBuilder
from live_data.second_candle_collector import collect_second_candles
from execution.forward_paper_micro_runner import run_forward_paper_micro_session
from replay_lab.paths import REPLAY_STORE_DIR, ensure_replay_store
from replay_lab.replay.batch_replay import run_batch_0900, run_daily_study_0900
from replay_lab.replay.investment_v2 import run_study_v2
from replay_lab.replay.replay_runner_0900 import ReplayRunner0900
from replay_lab.replay.replay_session import ReplaySessionConfig
from replay_lab.replay.fear_divergence_v4 import run_fear_divergence_v4
from replay_lab.replay.fear_exhaustion_v41 import run_fear_exhaustion_v41
from replay_lab.replay.small_seed_v3 import run_small_seed_v3
from replay_lab.replay.structure_reversal_v5 import run_structure_reversal_v5
from replay_lab.replay.fractal_v52 import run_fractal_v52
from replay_lab.replay.fractal_v53 import run_fractal_v53
from replay_lab.replay.edge_isolation_v54 import run_edge_isolation_v54
from replay_lab.replay.second_candle_replay import replay_second_candles as replay_second_candles_fn
from replay_lab.replay.micro_execution_replay import run_micro_execution_replay
from replay_lab.replay.walk_forward import build_walk_forward_windows
from replay_lab.research.fear_divergence_compare_v3 import compare_v3_v4
from replay_lab.research.fear_divergence_sweep_v4 import run_fear_divergence_sweep_v4
from replay_lab.research.fear_exhaustion_compare_v4 import compare_v4_v41
from replay_lab.research.fear_exhaustion_funnel_v41 import build_fear_exhaustion_funnel_v41
from replay_lab.research.fear_exhaustion_sweep_v41 import run_fear_exhaustion_sweep_v41
from replay_lab.research.preopen_confirmed_compare import run_preopen_confirmed_compare
from replay_lab.research.threshold_sweep_v3 import run_threshold_sweep_v3
from replay_lab.research.time_window_sweep_v3 import run_time_window_sweep_v3
from replay_lab.research.mtf_context_compare_v5 import compare_mtf_context_v5
from replay_lab.research.structure_reversal_compare_all import compare_all_strategies_v5
from replay_lab.research.structure_reversal_sweep_v5 import run_structure_reversal_sweep_v5
from replay_lab.research.weekly_sniper_v5 import run_weekly_sniper_v5
from replay_lab.research.fractal_v52_sweep import run_fractal_v52_sweep
from replay_lab.research.fractal_v52_walk_forward import run_fractal_v52_walk_forward
from replay_lab.research.full_seed_compounding_compare import compare_full_seed_v52
from replay_lab.research.zone_engine_validation import validate_zone_engine_v52
from replay_lab.research.allocation_diagnostic_v53 import diagnose_allocation_v53
from replay_lab.research.cache_benchmark_v53 import benchmark_cache_v53
from replay_lab.research.fractal_v53_walk_forward import run_fractal_v53_walk_forward
from replay_lab.research.runner_exit_sweep_v53 import sweep_runner_exit_v53
from replay_lab.research.zone_reaction_validation_v53 import validate_zone_reaction_v53
from replay_lab.research.edge_isolation_sweep_v54 import run_edge_isolation_sweep_v54
from replay_lab.research.exit_model_compare_v54 import compare_exit_models_v54
from replay_lab.research.module_ablation_v54 import run_module_ablation_v54
from replay_lab.research.zone_quality_research_v54 import research_zone_quality_v54
from replay_lab.research.trade_review_dataset_v54 import export_trade_review_v54
from replay_lab.research.micro_entry_timing_validation import validate_micro_entry_timing
from replay_lab.research.micro_exit_validation import validate_micro_exit
from replay_lab.research.latency_slippage_simulation import simulate_latency_slippage
from replay_lab.research.forward_micro_validation import validate_forward_micro_sessions
from replay_lab.research.micro_cost_survival_test import run_micro_cost_survival_test
from replay_lab.research.micro_data_quality_audit import audit_micro_data_quality
from replay_lab.research.micro_entry_exit_effectiveness import validate_micro_entry_exit_effectiveness
from replay_lab.replay.forward_micro_replay import replay_recorded_micro_session
from data.candidate_second_window_fetcher import fetch_candidate_second_window
from live_data.upbit_real_ws_session import run_upbit_real_ws_session
from live_data.upbit_ws_smoke_test import run_upbit_ws_smoke_test
from replay_lab.research.candidate_second_window_validation import validate_candidate_second_windows
from replay_lab.research.candidate_second_window_validation import validate_candidate_second_windows_v553
from replay_lab.research.micro_candidate_filter_validation import validate_micro_candidate_filter_v553
from replay_lab.research.external_strategy_backtest_lab import run_external_strategy_lab
from replay_lab.research.open_strategy_report_builder import build_open_strategy_report
from replay_lab.research.micro_entry_gate_decomposition_v554 import diagnose_micro_entry_gates_v554
from replay_lab.research.micro_entry_gate_abtest_v554 import run_micro_entry_gate_abtest_v554
from replay_lab.research.forward_ws_accumulation_v554 import run_forward_ws_accumulation_v554
from replay_lab.research.priority_external_strategy_ws_validation import validate_priority_external_strategies_ws_v554
from replay_lab.research.enterability_report_builder_v554 import build_enterability_report_v554
from execution.realistic_paper_runner import run_realistic_paper_session_v555
from replay_lab.research.realistic_paper_validation_v555 import validate_realistic_paper_v555
from replay_lab.research.micro_candidate_source_comparison_v555 import compare_micro_candidate_sources_v555
from replay_lab.research.micro_cost_survival_v555 import test_micro_cost_survival_v555
from replay_lab.feedback.realistic_paper_html_report_v555 import RealisticPaperHTMLReportV555
from replay_lab.research.wait_path_analysis_v556 import run_wait_path_analysis_v556
from replay_lab.research.hold_time_sweep_v556 import run_hold_time_sweep_v556
from replay_lab.research.entry_discovery_v556 import run_entry_discovery_v556
from replay_lab.research.head_controller_draft_v556 import run_head_controller_draft_v556
from replay_lab.feedback.entry_discovery_html_report_v556 import EntryDiscoveryHTMLReportV556
from replay_lab.feedback.head_controller_html_report_v556 import HeadControllerHTMLReportV556
from head_controller.llm_config import build_head_controller_llm_config
from replay_lab.research.artifact_integrity_check_v5561 import check_artifact_integrity_v5561, scan_report_secrets_v5561
from replay_lab.research.regenerate_v556_reports_v5561 import regenerate_v556_production_reports_v5561
from replay_lab.research.head_controller_llm_guard_v5561 import run_head_controller_llm_guard_v5561
from replay_lab.feedback.artifact_integrity_html_report_v5561 import ArtifactIntegrityHTMLReportV5561
from replay_lab.feedback.head_controller_llm_guard_report_v5561 import HeadControllerLLMGuardReportV5561
from replay_lab.research.head_controller_openai_live_check_v5562 import (
    run_head_controller_openai_live_smoke_v5562,
    run_head_controller_unsafe_prompt_test_v5562,
)
from replay_lab.feedback.head_controller_openai_live_report_v5562 import HeadControllerOpenAILiveReportV5562
from execution.full_seed_paper_runner import run_full_seed_paper_session_v557
from replay_lab.research.sizing_mode_comparison_v557 import compare_sizing_modes_v557
from replay_lab.research.ladder_entry_exit_validation_v557 import validate_ladder_entry_exit_v557
from replay_lab.research.head_controller_evaluation_v557 import run_head_controller_evaluation_v557
from replay_lab.feedback.full_seed_allocator_html_report_v557 import FullSeedAllocatorHTMLReportV557
from replay_lab.feedback.head_controller_evaluation_html_report_v557 import HeadControllerEvaluationHTMLReportV557
from replay_lab.research.winner_trace_mining_v558 import detect_winner_events_v558, extract_winner_traces_v558
from replay_lab.research.winner_capture_rate_v558 import analyze_winner_capture_rate_v558
from replay_lab.research.missed_winner_analysis_v558 import analyze_missed_winners_v558
from winner_mining.winner_pattern_miner import mine_winner_patterns
from replay_lab.research.redesigned_candidate_source_validation_v558 import validate_redesigned_candidate_sources_v558
from replay_lab.research.full_seed_winner_candidate_validation_v558 import validate_full_seed_winner_candidates_v558
from replay_lab.research.head_controller_winner_pattern_review_v558 import run_head_controller_winner_review_v558
from replay_lab.feedback.winner_trace_html_report_v558 import WinnerTraceHTMLReportV558
from replay_lab.feedback.candidate_source_redesign_html_report_v558 import CandidateSourceRedesignHTMLReportV558
from replay_lab.feedback.head_controller_winner_review_html_report_v558 import HeadControllerWinnerReviewHTMLReportV558
from replay_lab.research.winner_quality_filter_v559 import run_winner_quality_filter_v559
from replay_lab.research.non_winner_sampling_v559 import run_non_winner_sampling_v559
from replay_lab.research.false_positive_control_v559 import run_false_positive_control_v559
from replay_lab.research.source_discriminative_power_v559 import run_source_discriminative_power_v559
from replay_lab.research.refined_source_validation_v559 import validate_refined_sources_v559, verify_post_mfe_calculation_v559
from replay_lab.research.redesigned_source_forward_test_v559 import run_redesigned_source_forward_test_research_v559
from replay_lab.research.full_seed_refined_source_validation_v559 import validate_full_seed_refined_sources_v559
from replay_lab.research.head_controller_false_positive_review_v559 import run_head_controller_false_positive_review_v559
from replay_lab.feedback.winner_quality_filter_html_report_v559 import WinnerQualityFilterHTMLReportV559
from replay_lab.feedback.false_positive_control_html_report_v559 import FalsePositiveControlHTMLReportV559
from replay_lab.feedback.redesigned_source_forward_html_report_v559 import RedesignedSourceForwardHTMLReportV559
from replay_lab.feedback.head_controller_false_positive_review_html_report_v559 import HeadControllerFalsePositiveReviewHTMLReportV559
from replay_lab.research.tradable_winner_mining_v5510 import mine_tradable_winners_v5510, extract_tradable_traces_v5510
from replay_lab.research.high_volatility_session_collection_v5510 import collect_high_volatility_session_v5510
from replay_lab.research.tradable_candidate_source_design_v5510 import design_tradable_candidate_sources_v5510
from replay_lab.research.tradable_source_forward_validation_v5510 import (
    run_tradable_source_live_forward_v5510,
    run_tradable_source_live_smoke_v5510,
    validate_tradable_source_recorded_v5510,
)
from replay_lab.research.full_seed_tradable_source_validation_v5510 import validate_full_seed_tradable_sources_v5510
from replay_lab.research.head_controller_tradable_winner_review_v5510 import run_head_controller_tradable_winner_review_v5510
from replay_lab.feedback.tradable_winner_mining_html_report_v5510 import TradableWinnerMiningHTMLReportV5510
from replay_lab.feedback.high_volatility_session_html_report_v5510 import HighVolatilitySessionHTMLReportV5510
from replay_lab.feedback.tradable_source_forward_html_report_v5510 import TradableSourceForwardHTMLReportV5510
from replay_lab.feedback.head_controller_tradable_winner_review_html_report_v5510 import HeadControllerTradableWinnerReviewHTMLReportV5510
from replay_lab.research.timing_event_collection_v5r1 import run_timing_lab_live_v5r1
from replay_lab.research.event_clip_replay_v5r1 import replay_timing_lab_v5r1
from replay_lab.research.timing_label_validation_v5r1 import label_event_clips
from replay_lab.research.entry_state_machine_validation_v5r1 import validate_entry_state_machine_v5r1
from replay_lab.research.llm_usage_audit_v5r1 import audit_llm_usage_v5r1
from replay_lab.research.head_controller_timing_review_v5r1 import run_head_controller_timing_review_v5r1
from timing_lab.entry_window_analyzer import analyze_entry_windows
from execution.timing_based_paper_runner import run_timing_based_paper_v5r1
from replay_lab.feedback.timing_lab_html_report_v5r1 import TimingLabHTMLReportV5R1
from replay_lab.feedback.entry_timing_html_report_v5r1 import EntryTimingHTMLReportV5R1
from replay_lab.feedback.llm_usage_html_report_v5r1 import LLMUsageHTMLReportV5R1
from replay_lab.feedback.head_controller_timing_review_html_report_v5r1 import HeadControllerTimingReviewHTMLReportV5R1
from timing_lab.fake_signal_decomposer import decompose_fake_signals
from timing_lab.follow_through_failure_analyzer import analyze_follow_through_failures
from timing_lab.event_type_quality_scorer import score_event_types
from timing_lab.detector_gap_analyzer import analyze_detector_gaps
from timing_lab.calibration.armed_threshold_tuner import tune_armed_thresholds
from timing_lab.calibration.confirmation_threshold_tuner import tune_confirmation_thresholds
from timing_lab.calibration.calibration_grid_runner import run_calibration_grid
from llm_ops.llm_live_call_repair import repair_llm_completion_v5r2, run_llm_minimum_completion_test
from timing_lab.timing_project_scorecard import build_project_scorecard
from replay_lab.research.head_controller_v5r2_review import run_head_controller_v5r2_review
from replay_lab.feedback.fake_signal_decomposition_html_report_v5r2 import FakeSignalDecompositionHTMLReportV5R2
from replay_lab.feedback.confirmation_calibration_html_report_v5r2 import ConfirmationCalibrationHTMLReportV5R2
from replay_lab.feedback.llm_completion_repair_html_report_v5r2 import LLMCompletionRepairHTMLReportV5R2
from replay_lab.feedback.project_scorecard_html_report_v5r2 import ProjectScorecardHTMLReportV5R2
from replay_lab.feedback.head_controller_v5r2_review_html_report import HeadControllerV5R2ReviewHTMLReport
from market_intelligence.regime_engine import build_market_regime_v5r3
from setup_intelligence.setup_engine import build_setup_candidates_v5r3
from scenario_lab.scenario_factory import build_scenarios_v5r3
from execution.aggressive_paper_learning_runner import (
    run_aggressive_paper_learning_v5r3,
    run_scenario_replay_v5r3,
)
from replay_lab.research.llm_strategy_review_v5r3 import run_llm_strategy_review_v5r3
from replay_lab.feedback.v5r3_strategy_learning_html_report import V5R3StrategyLearningHTMLReport
from replay_lab.research.v6_ohlcv_collection import run_v6_ohlcv_collection
from replay_lab.research.v6_mtf_context_generation import run_v6_mtf_context_generation
from replay_lab.research.v6_daddy_strategy_backtest import run_v6_daddy_backtest
from replay_lab.research.v6_ict_strategy_backtest import run_v6_ict_backtest
from replay_lab.research.v6_combined_strategy_backtest import run_v6_combined_backtest
from replay_lab.research.v6_weekly_paper_simulation import run_v6_weekly_paper_simulation
from replay_lab.research.head_controller_v6_review import run_head_controller_v6_review
from replay_lab.feedback.v6_mtf_report_html import V6MTFReportHTML
from replay_lab.feedback.v6_daddy_strategy_report_html import V6DaddyStrategyReportHTML
from replay_lab.feedback.v6_ict_strategy_report_html import V6ICTStrategyReportHTML
from replay_lab.feedback.v6_combined_strategy_report_html import V6CombinedStrategyReportHTML
from replay_lab.feedback.v6_weekly_performance_report_html import V6WeeklyPerformanceReportHTML
from replay_lab.feedback.head_controller_v6_review_html import HeadControllerV6ReviewHTML
from market_data.ohlcv_coverage_reporter import build_ohlcv_coverage
from replay_lab.research.v61_long_horizon_collection import run_v61_long_horizon_collection
from replay_lab.research.v61_strategy_robustness_backtest import run_v61_strategy_robustness_backtest
from replay_lab.research.v61_regime_backtest import run_v61_regime_backtest
from replay_lab.research.v61_big_win_dependency import run_v61_big_win_dependency
from replay_lab.research.v61_failure_success_analysis import run_v61_failure_success_analysis
from replay_lab.research.v61_risk_parameter_sweep import run_v61_risk_sweep
from replay_lab.research.v61_train_test_split_validation import run_v61_train_test_validation
from replay_lab.research.v61_final_strategy_decision import build_v61_final_decision
from replay_lab.research.head_controller_v61_review import run_head_controller_v61_review
from replay_lab.feedback.v61_coverage_report_html import V61CoverageReportHTML
from replay_lab.feedback.v61_strategy_robustness_report_html import V61StrategyRobustnessReportHTML
from replay_lab.feedback.v61_regime_report_html import V61RegimeReportHTML
from replay_lab.feedback.v61_big_win_dependency_report_html import V61BigWinDependencyReportHTML
from replay_lab.feedback.v61_failure_success_report_html import V61FailureSuccessReportHTML
from replay_lab.feedback.v61_risk_sweep_report_html import V61RiskSweepReportHTML
from replay_lab.feedback.v61_final_decision_report_html import V61FinalDecisionReportHTML
from replay_lab.feedback.head_controller_v61_review_html import HeadControllerV61ReviewHTML
from replay_lab.research.v62_capital_growth_backtest import run_v62_capital_growth_backtest
from replay_lab.research.v62_strategy_router_validation import validate_v62_strategy_router
from replay_lab.research.v62_real_exit_sweep import run_v62_real_exit_sweep
from replay_lab.research.v62_investment_report_generation import build_v62_investment_reports
from replay_lab.research.v62_risk_strengthen_review import run_v62_risk_strengthen_review
from replay_lab.research.head_controller_v62_review import run_head_controller_v62_review
from replay_lab.feedback.v62_trade_journal_html import V62TradeJournalHTML
from replay_lab.feedback.v62_weekly_report_html import V62WeeklyReportHTML
from replay_lab.feedback.v62_monthly_report_html import V62MonthlyReportHTML
from replay_lab.feedback.v62_full_investment_report_html import V62FullInvestmentReportHTML
from replay_lab.feedback.v62_strategy_router_report_html import V62StrategyRouterReportHTML
from replay_lab.feedback.v62_risk_report_html import V62RiskReportHTML
from replay_lab.feedback.head_controller_v62_review_html import HeadControllerV62ReviewHTML
from market_data.upbit_historical_archive_collector import collect_upbit_historical_archive
from portfolio.walk_forward_investment_simulator import run_true_walk_forward_paper
from replay_lab.research.investor_dashboard_builder import build_investor_dashboard
from replay_lab.research.drawdown_defense_revalidation import run_drawdown_defense_revalidation
from replay_lab.feedback.drawdown_defense_html_report import DrawdownDefenseHTMLReport
from replay_lab.research.v64_causal_defense_rerun import run_v64_causal_defense_rerun
from replay_lab.research.v64_return_amplification_lab import run_v64_return_amplification_lab
from replay_lab.research.v64_scenario_comparison import build_v64_scenario_comparison
from replay_lab.research.v64_hindsight_audit import run_v64_hindsight_audit
from replay_lab.research.v64_investor_summary import build_v64_investor_summary
from replay_lab.research.v64_policy_blend_analysis import build_v64_policy_blend_analysis
from replay_lab.research.v64_policy_compounding_analysis import build_v64_policy_compounding_analysis
from replay_lab.research.head_controller_v64_review import run_head_controller_v64_review
from replay_lab.feedback.v64_causal_defense_html_report import V64CausalDefenseHTMLReport
from replay_lab.feedback.v64_return_amplification_html_report import V64ReturnAmplificationHTMLReport
from replay_lab.feedback.v64_scenario_comparison_html_report import V64ScenarioComparisonHTMLReport
from replay_lab.feedback.v64_hindsight_audit_html_report import V64HindsightAuditHTMLReport
from replay_lab.feedback.v64_investor_summary_html_report import V64InvestorSummaryHTMLReport
from replay_lab.feedback.head_controller_v64_review_html import HeadControllerV64ReviewHTML
from replay_lab.research.v65_ma_regime_filter_lab import build_v65_ma_features
from replay_lab.research.v65_ma_scenario_comparison import (
    analyze_v65_yearly_weakness_repair,
    build_v65_ma_risk_report,
    run_v65_ma_policy_router_lab,
    run_v65_ma_scenario_lab,
)
from replay_lab.research.head_controller_v65_review import run_head_controller_v65_review
from replay_lab.feedback.v65_ma_scenario_report_html import (
    V65MAPolicyRouterReportHTML,
    V65MARiskReportHTML,
    V65MAScenarioReportHTML,
    V65YearlyRepairReportHTML,
)
from replay_lab.feedback.head_controller_v65_review_html import HeadControllerV65ReviewHTML
from replay_lab.research.v66_btcd_data_preparation import (
    audit_v66_btcd_inclusion,
    build_v66_btcd_data_quality_report,
    prepare_v66_btcd_data,
)
from replay_lab.research.v66_btcd_rolling_balanced_lab import run_v66_btcd_rolling_balanced_lab
from replay_lab.research.v66_btcd_bear_regime_lab import (
    run_v66_btcd_bear_bounce_lab,
    run_v66_btcd_bear_regime_lab,
)
from replay_lab.research.v66_btcd_short_research_lab import run_v66_btcd_short_research_lab
from replay_lab.research.v66_btcd_hybrid_router_lab import run_v66_btcd_hybrid_router_lab
from replay_lab.research.v66_btcd_scenario_comparison import build_v66_btcd_scenario_comparison
from replay_lab.research.head_controller_v66_review import run_head_controller_v66_review
from replay_lab.feedback.v66_btcd_reports_html import (
    V66BTCD202411FocusHTML,
    V66BTCDBearScenarioHTML,
    V66BTCDDataQualityHTML,
    V66BTCDHybridRouterHTML,
    V66BTCDInclusionAuditHTML,
    V66BTCDRollingBalancedHTML,
    V66BTCDScenarioComparisonHTML,
    V66BTCDSavedLossMissedProfitHTML,
    V66BTCDShortResearchHTML,
)
from replay_lab.feedback.head_controller_v66_review_html import HeadControllerV66ReviewHTML
from replay_lab.research.v67_global_btcd_data_preparation import (
    build_v67_global_btcd_data_quality_report,
    prepare_v67_global_btcd_data,
)
from replay_lab.research.v67_global_btcd_scenario_lab import run_v67_global_btcd_scenario_lab
from replay_lab.research.v67_global_btcd_compact_router_lab import run_v67_global_btcd_compact_router_lab
from replay_lab.research.v67_global_btcd_scenario_comparison import (
    build_v67_global_btcd_rejected_scenarios_report,
    build_v67_global_btcd_saved_loss_report,
    build_v67_global_btcd_yearly_report,
)
from replay_lab.research.head_controller_v67_review import run_head_controller_v67_review
from replay_lab.feedback.v67_global_btcd_reports_html import (
    V67GlobalBTCDCompactRouterHTML,
    V67GlobalBTCDDataQualityHTML,
    V67GlobalBTCDRejectedHTML,
    V67GlobalBTCDSavedLossHTML,
    V67GlobalBTCDScenarioHTML,
    V67GlobalBTCDYearlyHTML,
)
from replay_lab.feedback.head_controller_v67_review_html import HeadControllerV67ReviewHTML
from replay_lab.research.v672_btcdom_index_data_preparation import (
    build_v672_btcdom_index_data_quality_report,
    prepare_v672_btcdom_index_data,
)
from replay_lab.research.v672_btcdom_index_scenario_lab import run_v672_btcdom_index_scenario_lab
from replay_lab.research.v672_btcdom_index_compact_router_lab import run_v672_btcdom_index_compact_router_lab
from replay_lab.research.v672_btcdom_index_scenario_comparison import (
    build_v672_btcdom_index_rejected_scenarios_report,
    build_v672_btcdom_index_saved_loss_report,
    build_v672_btcdom_index_yearly_report,
)
from replay_lab.research.head_controller_v672_review import run_head_controller_v672_review
from replay_lab.feedback.v672_btcdom_index_reports_html import (
    V672BTCDOMIndexCompactRouterHTML,
    V672BTCDOMIndexDataQualityHTML,
    V672BTCDOMIndexRejectedHTML,
    V672BTCDOMIndexSavedLossHTML,
    V672BTCDOMIndexScenarioHTML,
    V672BTCDOMIndexYearlyHTML,
)
from replay_lab.feedback.head_controller_v672_review_html import HeadControllerV672ReviewHTML
from replay_lab.research.v673_dominance_data_preparation import (
    build_v673_dominance_data_quality_report,
    prepare_v673_dominance_data,
)
from replay_lab.research.v673_rolling_balanced_dominance_matrix_lab import run_v673_rolling_balanced_dominance_matrix_lab
from replay_lab.research.v673_bear_agent_lab import run_v673_bear_agent_lab
from replay_lab.research.v673_scenario_agent_router_lab import run_v673_scenario_agent_router_lab
from replay_lab.research.v673_agent_comparison import (
    build_v673_high_watermark_report,
    build_v673_rejected_scenarios_report,
    build_v673_saved_loss_report,
    build_v673_yearly_market_state_report,
)
from replay_lab.research.head_controller_v673_review import run_head_controller_v673_review
from replay_lab.feedback.v673_reports_html import (
    HeadControllerV673ReviewHTML,
    V673AgentMatrixHTML,
    V673BearAgentHTML,
    V673DominanceDataQualityHTML,
    V673HighWatermarkHTML,
    V673RejectedScenariosHTML,
    V673ScenarioRouterHTML,
)
from replay_lab.research.v681_control_tower_lab import (
    audit_v681_compounding_vs_dominance_ledger_lab,
    build_v681_integrated_investment_report_html,
    register_v681_shadow_route_lab,
    run_v681_bear_compounding_agent_lab,
    run_v681_compounding_dominance_lab,
    run_v681_compounding_scenario_router_lab,
    run_v681_control_tower_review_lab,
    run_v681_paper_backfill_lab,
    start_v681_paper_server_lab,
)
from replay_lab.research.v682_bear_response_lab import (
    build_v682_bear_bounce_report_html,
    build_v682_bear_defense_insight_report_html,
    build_v682_bear_response_router_report_html,
    build_v682_bounce_case_study_lab,
    build_v682_bounce_case_study_report_html,
    register_v682_bear_shadow_route_lab,
    run_v682_bear_bounce_profit_lab,
    run_v682_bear_defense_deep_insight_lab,
    run_v682_bear_response_router_lab,
)
from replay_lab.research.v683_paper_runtime_lab import (
    build_v683_active_shadow_comparison_lab,
    build_v683_paper_dashboard_html_lab,
    build_v683_route_router_report_lab,
    check_v683_paper_health_lab,
    register_v683_shadow_route_lab,
    run_v683_control_tower_review_lab,
    run_v683_paper_backfill_lab,
    start_v683_live_forward_paper_lab,
    switch_v683_active_paper_route_lab,
)
from replay_lab.research.v684_bear_indicator_validation import (
    build_v684_bear_windows_lab,
    build_v684_bear_windows_report_html,
    build_v684_dashboard_html,
    build_v684_indicator_effectiveness_report_html,
    build_v684_loss_guard_indicator_report_html,
    run_v684_indicator_effectiveness,
    run_v684_loss_guard_indicator,
)
from replay_lab.research.v684_bear_bounce_v3_research import (
    build_v684_bear_bounce_v3_report_html,
    run_v684_bear_bounce_v3,
)
from replay_lab.research.v684_risk_sizing_research import (
    build_v684_risk_sizing_report_html,
    run_v684_risk_sizing,
)
from replay_lab.research.v684_bear_router_research import (
    build_v684_bear_router_report_html,
    run_v684_bear_router,
)
from replay_lab.research.v685_atr_precision_research import (
    build_v685_atr_precision_report_html,
    build_v685_atr_price_path_report_html,
    build_v685_atr_sensitivity_report_html,
    run_v685_atr_precision,
    run_v685_atr_price_path,
    run_v685_atr_sensitivity,
)
from replay_lab.research.v685_bear_window_research import (
    build_v685_bear_window_classification,
    build_v685_bear_window_classification_report_html,
    build_v685_bear_window_performance_report_html,
    run_v685_bear_window_performance,
)
from replay_lab.research.v685_bear_router_window_aware_research import (
    build_v685_bear_router_window_aware_report_html,
    run_v685_bear_router_window_aware,
)
from replay_lab.feedback.v685_reports_html import V685ReportsHTML
from replay_lab.research.v686_atr_ltf_research import (
    build_v686_atr_ltf_coverage_report_html,
    build_v686_atr_ltf_replay_report_html,
    build_v686_atr_model_comparison_report_html,
    build_v686_atr_precision_v2_report_html,
    build_v686_bear_window_atr_replay_report_html,
    run_v686_atr_ltf_coverage_lab,
    run_v686_atr_ltf_replay_lab,
    run_v686_atr_precision_v2_lab,
    run_v686_bear_window_atr_replay_lab,
)
from replay_lab.research.v686_runtime_dashboard_research import (
    build_v686_active_shadow_dashboard_data_lab,
    build_v686_local_dashboard_report_html,
    check_v686_local_dashboard_health_lab,
    register_v686_shadow_routes_lab,
    run_v686_control_tower_dashboard_review_lab,
    run_v686_paper_backfill_with_v685_router_lab,
)
from local_dashboard.dashboard_app import start_dashboard as start_v686_dashboard
from research_external.strategy_candidate_registry import build_external_strategy_registry
from replay_lab.research.mock_vs_real_data_audit import audit_mock_vs_real_data
from replay_lab.research.upbit_auth_safety_check import run_upbit_auth_safety_check
from replay_lab.sidecar_c.time_window_discovery import TimeWindowDiscovery, TimeWindowDiscoveryConfig, default_entry_times


def _markets(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _resolve_markets(value: str | None, loader: HistoricalLoader | None = None, provider: ReplayDataProvider | None = None, top_limit: int | None = None) -> list[str]:
    explicit = _markets(value)
    if explicit:
        return explicit
    if provider:
        cached = provider.get_markets()
        if cached:
            return cached
    if loader:
        if top_limit:
            return loader.load_top_krw_markets(top_limit)
        return loader.load_markets()
    return ["KRW-BTC"]


def load_markets(_: argparse.Namespace) -> int:
    markets = HistoricalLoader().load_markets()
    print(json.dumps({"count": len(markets), "markets": markets}, ensure_ascii=False))
    return 0


def load_candles(args: argparse.Namespace) -> int:
    end = datetime.now()
    start = end - timedelta(days=args.days)
    path = HistoricalLoader().load_candles(args.market, args.timeframe, start, end)
    print(f"cached: {path}")
    return 0


def load_0900(args: argparse.Namespace) -> int:
    loader = HistoricalLoader()
    markets = _resolve_markets(args.markets, loader=loader, top_limit=args.top_markets)
    start = date.today() - timedelta(days=args.days - 1)
    paths = loader.load_batch_0900_windows(markets[: args.top_markets], start, date.today())
    print(f"cached windows: {len(paths)}")
    return 0


def load_intraday(args: argparse.Namespace) -> int:
    loader = HistoricalLoader()
    markets = _resolve_markets(args.markets, loader=loader, top_limit=args.top_markets)
    start = date.today() - timedelta(days=args.days - 1)
    paths = loader.load_batch_intraday_days(markets[: args.top_markets], start, date.today())
    print(f"cached intraday days: {len(paths)}")
    return 0


def run_0900(args: argparse.Namespace) -> int:
    day = date.fromisoformat(args.date)
    clock = ReplayClock(datetime.combine(day, datetime.min.time()).replace(hour=8, minute=50))
    provider = ReplayDataProvider(clock)
    config = ReplaySessionConfig(
        session_id=f"manual_{day.isoformat()}",
        date_kst=day,
        markets=_resolve_markets(args.markets, provider=provider, top_limit=args.top_markets),
        scan_time=args.scan_time,
        pre_score_time=args.pre_score_time,
        decision_time=args.decision_time,
        entry_time=args.entry_time,
        target_window_end_time=args.target_window_end_time,
        trade_end_time=args.trade_end_time,
        strategy_label=args.strategy_label,
    )
    result = ReplayRunner0900(provider, clock).run(config, top_market_limit=args.top_markets)
    print(json.dumps({key: len(value) for key, value in result.items()}, ensure_ascii=False))
    return 0


def batch_0900(args: argparse.Namespace) -> int:
    provider = ReplayDataProvider(ReplayClock(datetime.now()))
    exp_dir = run_batch_0900(
        args.days,
        _resolve_markets(args.markets, provider=provider, top_limit=args.top_markets),
        args.top_markets,
        scan_time=args.scan_time,
        pre_score_time=args.pre_score_time,
        decision_time=args.decision_time,
        entry_time=args.entry_time,
        target_window_end_time=args.target_window_end_time,
        trade_end_time=args.trade_end_time,
        strategy_label=args.strategy_label,
    )
    print(f"experiment: {exp_dir}")
    return 0


def study_0900_range(args: argparse.Namespace) -> int:
    loader = HistoricalLoader()
    markets = _resolve_markets(args.markets, loader=loader, top_limit=args.top_markets)
    exp_dir = run_daily_study_0900(
        date.fromisoformat(args.start_date),
        date.fromisoformat(args.end_date),
        markets,
        args.top_markets,
        load_first=not args.no_load_first,
        use_seconds=args.use_seconds,
        force_daily_entries=args.force_daily_entries,
        force_daily_count=args.force_daily_count,
        scan_time=args.scan_time,
        pre_score_time=args.pre_score_time,
        decision_time=args.decision_time,
        entry_time=args.entry_time,
        target_window_end_time=args.target_window_end_time,
        trade_end_time=args.trade_end_time,
        strategy_label=args.strategy_label,
    )
    print(f"experiment: {exp_dir}")
    return 0


def _window_config(entry_time: str) -> dict[str, str]:
    entry = datetime.strptime(entry_time, "%H:%M")
    scan = entry - timedelta(minutes=10)
    pre = entry - timedelta(minutes=1)
    target_end = entry + timedelta(minutes=30)
    trade_end = entry + timedelta(minutes=60)
    if scan.day != entry.day or trade_end.day != entry.day:
        raise ValueError("entry times must leave room for same-day 10 minute analysis and 60 minute trade window")
    return {
        "scan_time": scan.strftime("%H:%M"),
        "pre_score_time": pre.strftime("%H:%M"),
        "decision_time": pre.strftime("%H:%M"),
        "entry_time": entry.strftime("%H:%M"),
        "target_window_end_time": target_end.strftime("%H:%M"),
        "trade_end_time": trade_end.strftime("%H:%M"),
        "strategy_label": f"{scan.strftime('%H%M')}_{entry.strftime('%H%M')}_scalp",
    }


def batch_windows(args: argparse.Namespace) -> int:
    provider = ReplayDataProvider(ReplayClock(datetime.now()))
    markets = _resolve_markets(args.markets, provider=provider, top_limit=args.top_markets)
    entry_times = [item.strip() for item in args.entry_times.split(",") if item.strip()]
    experiments = []
    for entry_time in entry_times:
        config = _window_config(entry_time)
        exp_dir = run_batch_0900(args.days, markets, args.top_markets, **config)
        experiments.append(str(exp_dir))
    print(json.dumps({"experiments": experiments}, ensure_ascii=False, indent=2))
    return 0


def walk_forward(args: argparse.Namespace) -> int:
    windows = build_walk_forward_windows(args.days)
    out = REPLAY_STORE_DIR / "reports" / "walk_forward_metrics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"days": args.days, "windows": windows}, indent=2), encoding="utf-8")
    print(f"walk-forward: {out}")
    return 0


def athena_review(args: argparse.Namespace) -> int:
    exp_dir = REPLAY_STORE_DIR / "experiments" / args.experiment_id
    review = review_experiment(exp_dir)
    out = exp_dir / "athena_review.json"
    out.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"athena review: {out}")
    return 0


def export_approved(args: argparse.Namespace) -> int:
    out = export_approved_patch(Path(args.patch_path), source_experiment_id=args.experiment_id or "")
    print(f"exported: {out}")
    return 0


def export_summary(args: argparse.Namespace) -> int:
    out = export_research_summary(args.experiment_id)
    print(f"summary exported: {out}")
    return 0


def build_report_catalog(args: argparse.Namespace) -> int:
    catalog = ReplayReportCatalog(capital_krw=args.capital_krw, start_date=args.start_date, current_schema_only=args.current_schema_only).build()
    print(json.dumps({key: len(value) for key, value in catalog.items()}, ensure_ascii=False))
    return 0


def build_investment_report(args: argparse.Namespace) -> int:
    out = InvestmentReportBuilder(capital_krw=args.capital_krw).build(start_date=args.start_date, end_date=args.end_date)
    print(f"investment report: {out}")
    return 0


def study_v2(args: argparse.Namespace) -> int:
    loader = HistoricalLoader()
    markets = _resolve_markets(args.markets, loader=loader, top_limit=args.top_markets)
    exp_dir = run_study_v2(
        start_date=date.fromisoformat(args.start_date),
        end_date=date.fromisoformat(args.end_date),
        markets=markets,
        candidate_limit=args.candidate_limit,
        max_daily_entries=args.max_daily_entries,
        capital_krw=args.capital_krw,
        load_first=not args.no_load_first,
    )
    print(f"investment v2 experiment: {exp_dir}")
    return 0


def build_investment_v2_report(args: argparse.Namespace) -> int:
    out = InvestmentV2ReportBuilder(capital_krw=args.capital_krw).build(start_date=args.start_date, end_date=args.end_date)
    print(f"investment v2 report: {out}")
    return 0


def sidecar_c_time_scan(args: argparse.Namespace) -> int:
    loader = HistoricalLoader()
    markets = _resolve_markets(args.markets, loader=loader, top_limit=args.top_markets)
    entry_times = _markets(args.entry_times) if args.entry_times else default_entry_times(args.step_minutes)
    out_dir = TimeWindowDiscovery().run(
        TimeWindowDiscoveryConfig(
            start_date=date.fromisoformat(args.start_date),
            end_date=date.fromisoformat(args.end_date),
            markets=markets,
            entry_times=entry_times,
            top_markets=args.top_markets,
            load_missing=args.load_missing,
            target_move_pct=args.target_move_pct,
            max_adverse_pct=args.max_adverse_pct,
        )
    )
    print(f"sidecar-c report: {out_dir}")
    return 0


def sweep_v3_thresholds(args: argparse.Namespace) -> int:
    out_dir = run_threshold_sweep_v3(
        start_date=date.fromisoformat(args.start_date),
        end_date=date.fromisoformat(args.end_date),
        capital_krw=args.capital_krw,
        order_krw=args.order_krw,
        top_markets=args.top_markets,
    )
    print(f"threshold sweep v3: {out_dir}")
    return 0


def sweep_time_windows_v3(args: argparse.Namespace) -> int:
    loader = HistoricalLoader()
    provider = ReplayDataProvider(ReplayClock(datetime.now()))
    markets = _resolve_markets(args.markets, loader=loader, provider=provider, top_limit=args.top_markets)
    out_dir = run_time_window_sweep_v3(
        start_date=date.fromisoformat(args.start_date),
        end_date=date.fromisoformat(args.end_date),
        markets=markets[: args.top_markets],
        capital_krw=args.capital_krw,
        order_krw=args.order_krw,
        step_minutes=args.step_minutes,
    )
    print(f"time window sweep v3: {out_dir}")
    return 0


def compare_entry_mode_v3(args: argparse.Namespace) -> int:
    loader = HistoricalLoader()
    provider = ReplayDataProvider(ReplayClock(datetime.now()))
    markets = _resolve_markets(args.markets, loader=loader, provider=provider, top_limit=args.top_markets)
    out_dir = run_preopen_confirmed_compare(
        start_date=date.fromisoformat(args.start_date),
        end_date=date.fromisoformat(args.end_date),
        markets=markets[: args.top_markets],
        capital_krw=args.capital_krw,
        order_krw=args.order_krw,
    )
    print(f"entry mode compare v3: {out_dir}")
    return 0


def run_small_seed_v3_command(args: argparse.Namespace) -> int:
    loader = HistoricalLoader()
    provider = ReplayDataProvider(ReplayClock(datetime.now()))
    markets = _resolve_markets(args.markets, loader=loader, provider=provider, top_limit=args.top_markets)
    exp_dir = run_small_seed_v3(
        start_date=date.fromisoformat(args.start_date),
        end_date=date.fromisoformat(args.end_date),
        markets=markets,
        capital_krw=args.capital_krw,
        order_krw=args.order_krw,
        max_daily_entries=args.max_daily_entries,
        top_markets=args.top_markets,
        strategy_mode=args.strategy_mode,
    )
    print(f"small seed v3 experiment: {exp_dir}")
    return 0


def build_small_seed_report(args: argparse.Namespace) -> int:
    out = SmallSeedReportBuilder(capital_krw=args.capital_krw, order_krw=args.order_krw).build(start_date=args.start_date, end_date=args.end_date)
    print(f"small seed v3 report: {out}")
    return 0


def sweep_fear_divergence_v4(args: argparse.Namespace) -> int:
    loader = HistoricalLoader()
    provider = ReplayDataProvider(ReplayClock(datetime.now()))
    markets = _resolve_markets(args.markets, loader=loader, provider=provider, top_limit=args.top_markets)
    out_dir = run_fear_divergence_sweep_v4(
        start_date=date.fromisoformat(args.start_date),
        end_date=date.fromisoformat(args.end_date),
        markets=markets,
        capital_krw=args.capital_krw,
        order_krw=args.order_krw,
        timeframe=args.timeframe,
        top_markets=args.top_markets,
    )
    print(f"fear divergence sweep v4: {out_dir}")
    return 0


def run_fear_divergence_v4_command(args: argparse.Namespace) -> int:
    loader = HistoricalLoader()
    provider = ReplayDataProvider(ReplayClock(datetime.now()))
    markets = _resolve_markets(args.markets, loader=loader, provider=provider, top_limit=args.top_markets)
    exp_dir = run_fear_divergence_v4(
        start_date=date.fromisoformat(args.start_date),
        end_date=date.fromisoformat(args.end_date),
        markets=markets,
        capital_krw=args.capital_krw,
        order_krw=args.order_krw,
        timeframe=args.timeframe,
        top_markets=args.top_markets,
    )
    print(f"fear divergence v4 experiment: {exp_dir}")
    return 0


def compare_v3_v4_command(args: argparse.Namespace) -> int:
    out_dir = compare_v3_v4(
        start_date=date.fromisoformat(args.start_date),
        end_date=date.fromisoformat(args.end_date),
        capital_krw=args.capital_krw,
        order_krw=args.order_krw,
    )
    print(f"v3 vs v4 compare: {out_dir}")
    return 0


def build_fear_divergence_report(args: argparse.Namespace) -> int:
    out = FearDivergenceReportBuilder(capital_krw=args.capital_krw, order_krw=args.order_krw).build(start_date=args.start_date, end_date=args.end_date)
    print(f"fear divergence report: {out}")
    return 0


def _timeframes(value: str | None) -> list[str]:
    items = _markets(value) if value else ["1m", "5m"]
    invalid = [item for item in items if item not in {"1m", "5m"}]
    if invalid:
        raise ValueError(f"unsupported timeframes: {invalid}")
    return items


def sweep_fear_exhaustion_v41(args: argparse.Namespace) -> int:
    loader = HistoricalLoader()
    provider = ReplayDataProvider(ReplayClock(datetime.now()))
    markets = _resolve_markets(args.markets, loader=loader, provider=provider, top_limit=args.top_markets)
    out_dir = run_fear_exhaustion_sweep_v41(
        start_date=date.fromisoformat(args.start_date),
        end_date=date.fromisoformat(args.end_date),
        markets=markets,
        capital_krw=args.capital_krw,
        order_krw=args.order_krw,
        timeframes=_timeframes(args.timeframes),
        top_markets=args.top_markets,
    )
    print(f"fear exhaustion sweep v4.1: {out_dir}")
    return 0


def run_fear_exhaustion_v41_command(args: argparse.Namespace) -> int:
    loader = HistoricalLoader()
    provider = ReplayDataProvider(ReplayClock(datetime.now()))
    markets = _resolve_markets(args.markets, loader=loader, provider=provider, top_limit=args.top_markets)
    exp_dir = run_fear_exhaustion_v41(
        start_date=date.fromisoformat(args.start_date),
        end_date=date.fromisoformat(args.end_date),
        markets=markets,
        capital_krw=args.capital_krw,
        order_krw=args.order_krw,
        timeframe=args.timeframe,
        top_markets=args.top_markets,
    )
    print(f"fear exhaustion v4.1 experiment: {exp_dir}")
    return 0


def build_fear_exhaustion_funnel_v41_command(args: argparse.Namespace) -> int:
    loader = HistoricalLoader()
    provider = ReplayDataProvider(ReplayClock(datetime.now()))
    markets = _resolve_markets(args.markets, loader=loader, provider=provider, top_limit=args.top_markets)
    out_dir = build_fear_exhaustion_funnel_v41(
        start_date=date.fromisoformat(args.start_date),
        end_date=date.fromisoformat(args.end_date),
        markets=markets,
        timeframes=_timeframes(args.timeframes),
        top_markets=args.top_markets,
    )
    print(f"fear exhaustion funnel v4.1: {out_dir}")
    return 0


def compare_v4_v41_command(args: argparse.Namespace) -> int:
    out_dir = compare_v4_v41(
        start_date=date.fromisoformat(args.start_date),
        end_date=date.fromisoformat(args.end_date),
        capital_krw=args.capital_krw,
        order_krw=args.order_krw,
    )
    print(f"v4 vs v4.1 compare: {out_dir}")
    return 0


def build_fear_exhaustion_v41_report(args: argparse.Namespace) -> int:
    out = FearExhaustionV41ReportBuilder(capital_krw=args.capital_krw, order_krw=args.order_krw).build(start_date=args.start_date, end_date=args.end_date)
    print(f"fear exhaustion v4.1 report: {out}")
    return 0


def _v5_markets(args: argparse.Namespace) -> list[str]:
    provider = ReplayDataProvider(ReplayClock(datetime.now()))
    loader = HistoricalLoader()
    return _resolve_markets(args.markets if hasattr(args, "markets") else None, provider=provider, loader=loader, top_limit=args.top_markets if hasattr(args, "top_markets") else None)


def sweep_structure_reversal_v5(args: argparse.Namespace) -> int:
    out = run_structure_reversal_sweep_v5(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), _v5_markets(args), top_markets=args.top_markets, capital_krw=args.capital_krw, order_krw=args.order_krw)
    print(f"structure reversal sweep v5: {out}")
    return 0


def run_structure_reversal_v5_command(args: argparse.Namespace) -> int:
    exp = run_structure_reversal_v5(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), _v5_markets(args), top_markets=args.top_markets, capital_krw=args.capital_krw, order_krw=args.order_krw, mode=args.mode)
    print(f"structure reversal v5 experiment: {exp}")
    return 0


def run_weekly_sniper_v5_command(args: argparse.Namespace) -> int:
    exp = run_weekly_sniper_v5(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), _v5_markets(args), top_markets=args.top_markets, capital_krw=args.capital_krw, order_krw=args.order_krw)
    print(f"weekly sniper v5 experiment: {exp}")
    return 0


def compare_mtf_context_v5_command(args: argparse.Namespace) -> int:
    out = compare_mtf_context_v5(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), _v5_markets(args), top_markets=args.top_markets, capital_krw=args.capital_krw, order_krw=args.order_krw)
    print(f"mtf context compare v5: {out}")
    return 0


def compare_all_strategies_v5_command(args: argparse.Namespace) -> int:
    out = compare_all_strategies_v5(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), capital_krw=args.capital_krw, order_krw=args.order_krw)
    print(f"all strategies compare v5: {out}")
    return 0


def build_structure_reversal_v5_report(args: argparse.Namespace) -> int:
    out = StructureReversalV5ReportBuilder(capital_krw=args.capital_krw, order_krw=args.order_krw).build(start_date=args.start_date, end_date=args.end_date)
    print(f"structure reversal v5 report: {out}")
    return 0


def run_fractal_v52_command(args: argparse.Namespace) -> int:
    exp = run_fractal_v52(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), _v5_markets(args), top_markets=args.top_markets, initial_equity_krw=args.initial_equity_krw, max_daily_entries=args.max_daily_entries, allocation_model=args.allocation_model, exit_model=args.exit_model)
    print(f"fractal v5.2 experiment: {exp}")
    return 0


def sweep_fractal_v52_command(args: argparse.Namespace) -> int:
    out = run_fractal_v52_sweep(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), _v5_markets(args), top_markets=args.top_markets, initial_equity_krw=args.initial_equity_krw)
    print(f"fractal v5.2 sweep: {out}")
    return 0


def validate_zone_engine_v52_command(args: argparse.Namespace) -> int:
    out = validate_zone_engine_v52(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), _v5_markets(args), top_markets=args.top_markets)
    print(f"zone engine v5.2 validation: {out}")
    return 0


def walk_forward_fractal_v52_command(args: argparse.Namespace) -> int:
    out = run_fractal_v52_walk_forward(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), _v5_markets(args), top_markets=args.top_markets, initial_equity_krw=args.initial_equity_krw)
    print(f"fractal v5.2 walk-forward: {out}")
    return 0


def compare_full_seed_v52_command(args: argparse.Namespace) -> int:
    out = compare_full_seed_v52(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), _v5_markets(args), top_markets=args.top_markets, initial_equity_krw=args.initial_equity_krw)
    print(f"full seed v5.2 compare: {out}")
    return 0


def build_fractal_v52_report(args: argparse.Namespace) -> int:
    out = FractalV52ReportBuilder(initial_equity_krw=args.initial_equity_krw).build(start_date=args.start_date, end_date=args.end_date)
    print(f"fractal v5.2 report: {out}")
    return 0


def _bool_arg(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "y", "on"}


def run_fractal_v53_command(args: argparse.Namespace) -> int:
    exp = run_fractal_v53(
        date.fromisoformat(args.start_date),
        date.fromisoformat(args.end_date),
        _v5_markets(args),
        top_markets=args.top_markets,
        initial_equity_krw=args.initial_equity_krw,
        max_daily_entries=args.max_daily_entries,
        allocation_model=args.allocation_model,
        exit_model=args.exit_model,
        btc_dominance_path=args.btc_dominance_path,
        use_cache=_bool_arg(args.use_cache),
    )
    print(f"fractal v5.3 experiment: {exp}")
    return 0


def diagnose_allocation_v53_command(args: argparse.Namespace) -> int:
    out = diagnose_allocation_v53(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), top_markets=args.top_markets, initial_equity_krw=args.initial_equity_krw)
    print(f"allocation diagnostic v5.3: {out}")
    return 0


def validate_zone_reaction_v53_command(args: argparse.Namespace) -> int:
    out = validate_zone_reaction_v53(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), _v5_markets(args), top_markets=args.top_markets)
    print(f"zone reaction validation v5.3: {out}")
    return 0


def sweep_runner_exit_v53_command(args: argparse.Namespace) -> int:
    out = sweep_runner_exit_v53(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), top_markets=args.top_markets, initial_equity_krw=args.initial_equity_krw)
    print(f"runner exit sweep v5.3: {out}")
    return 0


def walk_forward_fractal_v53_command(args: argparse.Namespace) -> int:
    out = run_fractal_v53_walk_forward(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), _v5_markets(args), top_markets=args.top_markets, initial_equity_krw=args.initial_equity_krw, use_cache=_bool_arg(args.use_cache))
    print(f"fractal v5.3 walk-forward: {out}")
    return 0


def benchmark_cache_v53_command(args: argparse.Namespace) -> int:
    out = benchmark_cache_v53(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), top_markets=args.top_markets)
    print(f"cache benchmark v5.3: {out}")
    return 0


def build_fractal_v53_report(args: argparse.Namespace) -> int:
    out = FractalV53ReportBuilder(initial_equity_krw=args.initial_equity_krw).build(start_date=args.start_date, end_date=args.end_date)
    print(f"fractal v5.3 report: {out}")
    return 0


def run_edge_isolation_v54_command(args: argparse.Namespace) -> int:
    exp = run_edge_isolation_v54(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), top_markets=args.top_markets, fixed_order_krw=args.fixed_order_krw)
    print(f"edge isolation v5.4 experiment: {exp}")
    return 0


def compare_exit_models_v54_command(args: argparse.Namespace) -> int:
    out = compare_exit_models_v54(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), top_markets=args.top_markets, fixed_order_krw=args.fixed_order_krw)
    print(f"exit model compare v5.4: {out}")
    return 0


def ablate_modules_v54_command(args: argparse.Namespace) -> int:
    out = run_module_ablation_v54(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), top_markets=args.top_markets, fixed_order_krw=args.fixed_order_krw)
    print(f"module ablation v5.4: {out}")
    return 0


def research_zone_quality_v54_command(args: argparse.Namespace) -> int:
    out = research_zone_quality_v54(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), top_markets=args.top_markets)
    print(f"zone quality research v5.4: {out}")
    return 0


def export_trade_review_v54_command(args: argparse.Namespace) -> int:
    out = export_trade_review_v54(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), top_markets=args.top_markets)
    print(f"trade review v5.4: {out}")
    return 0


def build_edge_isolation_v54_report(args: argparse.Namespace) -> int:
    out = EdgeIsolationV54ReportBuilder().build(start_date=args.start_date, end_date=args.end_date)
    print(f"edge isolation v5.4 report: {out}")
    return 0


def collect_second_candles_command(args: argparse.Namespace) -> int:
    result = collect_second_candles(_markets(args.markets), days=args.days, count_per_request=args.count_per_request)
    print(json.dumps(result, ensure_ascii=False))
    return 0


def replay_second_candles_command(args: argparse.Namespace) -> int:
    result = replay_second_candles_fn(args.market, args.start_time, args.end_time)
    print(json.dumps({k: v for k, v in result.items() if k != "seconds"}, ensure_ascii=False))
    return 0


def run_micro_execution_replay_command(args: argparse.Namespace) -> int:
    exp = run_micro_execution_replay(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), top_markets=args.top_markets, fixed_order_krw=args.fixed_order_krw, max_hold_seconds=args.max_hold_seconds)
    print(f"micro execution experiment: {exp}")
    return 0


def validate_micro_entry_timing_command(args: argparse.Namespace) -> int:
    out = validate_micro_entry_timing(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), top_markets=args.top_markets, fixed_order_krw=args.fixed_order_krw)
    print(f"micro entry timing validation: {out}")
    return 0


def validate_micro_exit_command(args: argparse.Namespace) -> int:
    out = validate_micro_exit(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), top_markets=args.top_markets, fixed_order_krw=args.fixed_order_krw)
    print(f"micro exit validation: {out}")
    return 0


def simulate_latency_slippage_command(args: argparse.Namespace) -> int:
    out = simulate_latency_slippage(date.fromisoformat(args.start_date), date.fromisoformat(args.end_date), top_markets=args.top_markets, fixed_order_krw=args.fixed_order_krw)
    print(f"latency/slippage simulation: {out}")
    return 0


def build_micro_execution_html_report_command(args: argparse.Namespace) -> int:
    out = MicroExecutionHTMLReportBuilder().build(start_date=args.start_date, end_date=args.end_date)
    print(f"micro execution report: {out}")
    return 0


def run_live_micro_session_command(args: argparse.Namespace) -> int:
    result = run_forward_paper_micro_session(duration_minutes=args.duration_minutes, markets=_markets(getattr(args, "markets", None)), top_markets=args.top_markets, fixed_order_krw=args.fixed_order_krw, mode=args.mode)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def record_live_micro_data_command(args: argparse.Namespace) -> int:
    result = run_forward_paper_micro_session(duration_minutes=args.duration_minutes, markets=_markets(args.markets), top_markets=len(_markets(args.markets)) or 3, fixed_order_krw=10000, mode="record_only")
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def replay_forward_micro_session_command(args: argparse.Namespace) -> int:
    result = replay_recorded_micro_session(args.session_id)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def validate_forward_micro_sessions_command(args: argparse.Namespace) -> int:
    result = validate_forward_micro_sessions(args.sessions_dir, min_quality=args.min_quality)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def audit_micro_data_quality_command(args: argparse.Namespace) -> int:
    result = audit_micro_data_quality(args.sessions_dir)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def test_micro_cost_survival_command(args: argparse.Namespace) -> int:
    result = run_micro_cost_survival_test(args.sessions_dir, min_quality=args.min_quality)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def validate_micro_entry_exit_effectiveness_command(args: argparse.Namespace) -> int:
    result = validate_micro_entry_exit_effectiveness(args.sessions_dir, min_quality=args.min_quality)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def build_forward_micro_html_report_command(args: argparse.Namespace) -> int:
    out = ForwardMicroHTMLReportBuilder().build(args.sessions_dir)
    print(f"forward micro report: {out}")
    return 0


def run_upbit_ws_smoke_test_command(args: argparse.Namespace) -> int:
    result = run_upbit_ws_smoke_test(_markets(args.markets), duration_seconds=args.duration_seconds)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def run_upbit_real_ws_session_command(args: argparse.Namespace) -> int:
    result = run_upbit_real_ws_session(_markets(args.markets), duration_seconds=args.duration_seconds, include_trade=str(args.include_trade).lower() == "true", include_orderbook=str(args.include_orderbook).lower() == "true")
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def fetch_candidate_second_window_command(args: argparse.Namespace) -> int:
    result = fetch_candidate_second_window(args.market, args.candidate_time, pre_seconds=args.pre_seconds, post_seconds=args.post_seconds)
    print(json.dumps({k: v for k, v in result.items() if k != "seconds"}, ensure_ascii=False, default=str))
    return 0


def validate_candidate_second_windows_command(args: argparse.Namespace) -> int:
    result = validate_candidate_second_windows(args.start_date, args.end_date, top_markets=args.top_markets, pre_seconds=args.pre_seconds, post_seconds=args.post_seconds, max_candidates=args.max_candidates, fixed_order_krw=args.fixed_order_krw)
    print(json.dumps({k: v for k, v in result.items() if k != "results"}, ensure_ascii=False, default=str))
    return 0


def validate_candidate_second_windows_v553_command(args: argparse.Namespace) -> int:
    result = validate_candidate_second_windows_v553(args.start_date, args.end_date, top_markets=args.top_markets, pre_seconds=args.pre_seconds, post_seconds=args.post_seconds, max_candidates=args.max_candidates, fixed_order_krw=args.fixed_order_krw)
    print(json.dumps({k: v for k, v in result.items() if k != "results"}, ensure_ascii=False, default=str))
    return 0


def validate_micro_candidate_filter_v553_command(args: argparse.Namespace) -> int:
    result = validate_micro_candidate_filter_v553(args.start_date, args.end_date, top_markets=args.top_markets, max_candidates=args.max_candidates)
    print(json.dumps({k: v for k, v in result.items() if k not in {"filter_rows", "results"}}, ensure_ascii=False, default=str))
    return 0


def build_external_strategy_registry_command(args: argparse.Namespace) -> int:
    result = build_external_strategy_registry()
    print(json.dumps({k: v for k, v in result.items() if k != "strategies"}, ensure_ascii=False, default=str))
    return 0


def run_external_strategy_lab_command(args: argparse.Namespace) -> int:
    result = run_external_strategy_lab(start_date=args.start_date, end_date=args.end_date, top_markets=args.top_markets, fixed_order_krw=args.fixed_order_krw, cost_scenario=args.cost_scenario)
    print(json.dumps({k: v for k, v in result.items() if k not in {"registry"}}, ensure_ascii=False, default=str))
    return 0


def build_open_strategy_report_command(args: argparse.Namespace) -> int:
    result = build_open_strategy_report()
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def diagnose_micro_entry_gates_v554_command(args: argparse.Namespace) -> int:
    result = diagnose_micro_entry_gates_v554(args.start_date, args.end_date, top_markets=args.top_markets, max_candidates=args.max_candidates)
    print(json.dumps({k: v for k, v in result.items() if k != "diagnostics"}, ensure_ascii=False, default=str))
    return 0


def abtest_micro_entry_gates_v554_command(args: argparse.Namespace) -> int:
    result = run_micro_entry_gate_abtest_v554(args.start_date, args.end_date, top_markets=args.top_markets, max_candidates=args.max_candidates)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def run_forward_ws_accumulation_v554_command(args: argparse.Namespace) -> int:
    result = run_forward_ws_accumulation_v554(duration_minutes=args.duration_minutes, top_markets=args.top_markets, priority_strategies=args.priority_strategies, fixed_order_krw=args.fixed_order_krw)
    print(json.dumps({k: v for k, v in result.items() if k not in {"source_session", "candidate_events"}}, ensure_ascii=False, default=str))
    return 0


def validate_priority_external_strategies_ws_v554_command(args: argparse.Namespace) -> int:
    result = validate_priority_external_strategies_ws_v554(args.sessions_dir)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def build_micro_entry_diagnostics_report_v554_command(args: argparse.Namespace) -> int:
    result = build_enterability_report_v554()
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def run_realistic_paper_session_v555_command(args: argparse.Namespace) -> int:
    strategies = [item.strip() for item in args.strategies.split(",") if item.strip()]
    result = run_realistic_paper_session_v555(duration_minutes=args.duration_minutes, top_markets=args.top_markets, initial_cash_krw=args.initial_cash_krw, fixed_order_krw=args.fixed_order_krw, strategies=strategies, scenario=args.scenario)
    print(json.dumps({k: v for k, v in result.items() if k not in {"sessions"}}, ensure_ascii=False, default=str))
    return 0


def validate_realistic_paper_v555_command(args: argparse.Namespace) -> int:
    result = validate_realistic_paper_v555(args.sessions_dir)
    print(json.dumps({k: v for k, v in result.items() if k != "sessions"}, ensure_ascii=False, default=str))
    return 0


def compare_micro_candidate_sources_v555_command(args: argparse.Namespace) -> int:
    result = compare_micro_candidate_sources_v555(args.sessions_dir)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def test_micro_cost_survival_v555_command(args: argparse.Namespace) -> int:
    result = test_micro_cost_survival_v555(args.sessions_dir)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def build_realistic_paper_report_v555_command(args: argparse.Namespace) -> int:
    out = RealisticPaperHTMLReportV555().build(args.sessions_dir)
    print(f"realistic paper report: {out}")
    return 0


def analyze_wait_path_v556_command(args: argparse.Namespace) -> int:
    result = run_wait_path_analysis_v556(args.sessions_dir)
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, ensure_ascii=False, default=str))
    return 0


def run_hold_time_sweep_v556_command(args: argparse.Namespace) -> int:
    result = run_hold_time_sweep_v556(args.sessions_dir, args.hold_seconds)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def run_entry_discovery_v556_command(args: argparse.Namespace) -> int:
    result = run_entry_discovery_v556(args.sessions_dir, args.profiles)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def run_head_controller_draft_v556_command(args: argparse.Namespace) -> int:
    result = run_head_controller_draft_v556(args.reports_dir, args.llm_provider, args.key_file)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def build_entry_discovery_report_v556_command(args: argparse.Namespace) -> int:
    out = EntryDiscoveryHTMLReportV556().build(args.sessions_dir)
    print(f"entry discovery report: {out}")
    return 0


def build_head_controller_report_v556_command(args: argparse.Namespace) -> int:
    out = HeadControllerHTMLReportV556().build(args.reports_dir, args.llm_provider, args.key_file)
    print(f"head controller report: {out}")
    return 0


def check_head_controller_llm_config_command(args: argparse.Namespace) -> int:
    result = build_head_controller_llm_config(args.llm_provider, args.key_file)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def check_artifact_integrity_v5561_command(args: argparse.Namespace) -> int:
    print(json.dumps(check_artifact_integrity_v5561(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def scan_report_secrets_v5561_command(args: argparse.Namespace) -> int:
    print(json.dumps(scan_report_secrets_v5561(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def regenerate_v556_production_reports_v5561_command(args: argparse.Namespace) -> int:
    print(json.dumps(regenerate_v556_production_reports_v5561(args.sessions_dir), ensure_ascii=False, default=str))
    return 0


def run_head_controller_llm_smoke_v5561_command(args: argparse.Namespace) -> int:
    result = run_head_controller_llm_guard_v5561(args.reports_dir, args.llm_provider, args.key_file, smoke=True)
    print(json.dumps({k: v for k, v in result.items() if k not in {"artifact_integrity"}}, ensure_ascii=False, default=str))
    return 0


def run_head_controller_llm_guard_v5561_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_head_controller_llm_guard_v5561(args.reports_dir, args.llm_provider, args.key_file, smoke=False), ensure_ascii=False, default=str))
    return 0


def build_head_controller_llm_guard_report_v5561_command(args: argparse.Namespace) -> int:
    ArtifactIntegrityHTMLReportV5561().build(args.reports_dir)
    out = HeadControllerLLMGuardReportV5561().build(args.reports_dir, args.llm_provider, args.key_file)
    print(f"head controller llm guard report: {out}")
    return 0


def run_head_controller_openai_live_smoke_v5562_command(args: argparse.Namespace) -> int:
    result = run_head_controller_openai_live_smoke_v5562(args.reports_dir, args.llm_provider, args.key_file)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def test_head_controller_unsafe_prompt_v5562_command(args: argparse.Namespace) -> int:
    result = run_head_controller_unsafe_prompt_test_v5562(args.llm_provider)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def build_head_controller_openai_live_report_v5562_command(args: argparse.Namespace) -> int:
    out = HeadControllerOpenAILiveReportV5562().build(args.reports_dir, args.llm_provider, args.key_file)
    print(f"head controller openai live report: {out}")
    return 0


def run_full_seed_paper_session_v557_command(args: argparse.Namespace) -> int:
    strategies = [item.strip() for item in str(args.strategies).split(",") if item.strip()]
    result = run_full_seed_paper_session_v557(args.duration_minutes, args.initial_cash_krw, args.sizing_mode, strategies, args.scenario, str(args.research_mode).lower() == "true")
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def compare_sizing_modes_v557_command(args: argparse.Namespace) -> int:
    result = compare_sizing_modes_v557(args.sessions_dir, args.initial_cash_krw)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def validate_ladder_entry_exit_v557_command(args: argparse.Namespace) -> int:
    result = validate_ladder_entry_exit_v557(args.sessions_dir)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def run_head_controller_evaluation_v557_command(args: argparse.Namespace) -> int:
    result = run_head_controller_evaluation_v557(args.reports_dir, args.llm_provider)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def build_full_seed_allocator_report_v557_command(args: argparse.Namespace) -> int:
    out = FullSeedAllocatorHTMLReportV557().build()
    print(f"full seed allocator report: {out}")
    return 0


def build_head_controller_evaluation_report_v557_command(args: argparse.Namespace) -> int:
    out = HeadControllerEvaluationHTMLReportV557().build(args.reports_dir, args.llm_provider)
    print(f"head controller evaluation report: {out}")
    return 0


def detect_winner_events_v558_command(args: argparse.Namespace) -> int:
    print(json.dumps(detect_winner_events_v558(args.sessions_dir, args.winner_types), ensure_ascii=False, default=str))
    return 0


def extract_winner_traces_v558_command(args: argparse.Namespace) -> int:
    print(json.dumps(extract_winner_traces_v558(args.winner_events, args.trace_windows), ensure_ascii=False, default=str))
    return 0


def analyze_winner_capture_rate_v558_command(args: argparse.Namespace) -> int:
    print(json.dumps(analyze_winner_capture_rate_v558(args.winner_traces, args.candidate_sources), ensure_ascii=False, default=str))
    return 0


def analyze_missed_winners_v558_command(args: argparse.Namespace) -> int:
    print(json.dumps(analyze_missed_winners_v558(args.winner_traces), ensure_ascii=False, default=str))
    return 0


def mine_winner_patterns_v558_command(args: argparse.Namespace) -> int:
    print(json.dumps(mine_winner_patterns(args.winner_traces), ensure_ascii=False, default=str))
    return 0


def validate_redesigned_candidate_sources_v558_command(args: argparse.Namespace) -> int:
    print(json.dumps(validate_redesigned_candidate_sources_v558(args.winner_traces), ensure_ascii=False, default=str))
    return 0


def validate_full_seed_winner_candidates_v558_command(args: argparse.Namespace) -> int:
    print(json.dumps(validate_full_seed_winner_candidates_v558(args.reports_dir, args.initial_cash_krw), ensure_ascii=False, default=str))
    return 0


def run_head_controller_winner_review_v558_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_head_controller_winner_review_v558(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def build_winner_trace_report_v558_command(args: argparse.Namespace) -> int:
    out = WinnerTraceHTMLReportV558().build()
    print(f"winner trace report: {out}")
    return 0


def build_candidate_source_redesign_report_v558_command(args: argparse.Namespace) -> int:
    out = CandidateSourceRedesignHTMLReportV558().build()
    print(f"candidate source redesign report: {out}")
    return 0


def build_head_controller_winner_review_report_v558_command(args: argparse.Namespace) -> int:
    out = HeadControllerWinnerReviewHTMLReportV558().build(args.reports_dir, args.llm_provider)
    print(f"head controller winner review report: {out}")
    return 0


def filter_winner_quality_v559_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_winner_quality_filter_v559(args.winner_traces, args.initial_cash_krw), ensure_ascii=False, default=str))
    return 0


def sample_non_winners_v559_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_non_winner_sampling_v559(args.sessions_dir, args.sample_ratio), ensure_ascii=False, default=str))
    return 0


def analyze_false_positives_v559_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_false_positive_control_v559(args.quality_winners, args.non_winners, args.sources), ensure_ascii=False, default=str))
    return 0


def analyze_source_discriminative_power_v559_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_source_discriminative_power_v559(args.quality_winners, args.non_winners), ensure_ascii=False, default=str))
    return 0


def validate_refined_sources_v559_command(args: argparse.Namespace) -> int:
    print(json.dumps(validate_refined_sources_v559(args.quality_winners, args.non_winners), ensure_ascii=False, default=str))
    return 0


def verify_post_mfe_calculation_v559_command(args: argparse.Namespace) -> int:
    print(json.dumps(verify_post_mfe_calculation_v559(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_redesigned_source_forward_test_v559_command(args: argparse.Namespace) -> int:
    research_mode = str(args.research_mode).lower() == "true"
    print(json.dumps(run_redesigned_source_forward_test_research_v559(args.duration_minutes, args.top_markets, args.sources, args.initial_cash_krw, args.scenario, research_mode), ensure_ascii=False, default=str))
    return 0


def validate_full_seed_refined_sources_v559_command(args: argparse.Namespace) -> int:
    print(json.dumps(validate_full_seed_refined_sources_v559(args.reports_dir, args.initial_cash_krw), ensure_ascii=False, default=str))
    return 0


def run_head_controller_false_positive_review_v559_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_head_controller_false_positive_review_v559(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def build_winner_quality_filter_report_v559_command(args: argparse.Namespace) -> int:
    print(f"winner quality filter report: {WinnerQualityFilterHTMLReportV559().build()}")
    return 0


def build_false_positive_control_report_v559_command(args: argparse.Namespace) -> int:
    print(f"false positive control report: {FalsePositiveControlHTMLReportV559().build()}")
    return 0


def build_redesigned_source_forward_report_v559_command(args: argparse.Namespace) -> int:
    print(f"redesigned source forward report: {RedesignedSourceForwardHTMLReportV559().build()}")
    return 0


def build_head_controller_false_positive_review_report_v559_command(args: argparse.Namespace) -> int:
    print(f"head controller false positive review report: {HeadControllerFalsePositiveReviewHTMLReportV559().build()}")
    return 0


def mine_tradable_winners_v5510_command(args: argparse.Namespace) -> int:
    print(json.dumps(mine_tradable_winners_v5510(args.sessions_dir, args.initial_cash_krw, args.winner_types), ensure_ascii=False, default=str))
    return 0


def extract_tradable_traces_v5510_command(args: argparse.Namespace) -> int:
    print(json.dumps(extract_tradable_traces_v5510(args.winner_dir, args.trace_windows), ensure_ascii=False, default=str))
    return 0


def collect_high_vol_live_session_v5510_command(args: argparse.Namespace) -> int:
    print(json.dumps(collect_high_volatility_session_v5510(args.session_type, args.duration_minutes, args.top_markets), ensure_ascii=False, default=str))
    return 0


def design_tradable_candidate_sources_v5510_command(args: argparse.Namespace) -> int:
    print(json.dumps(design_tradable_candidate_sources_v5510(args.tradable_traces), ensure_ascii=False, default=str))
    return 0


def validate_tradable_source_recorded_v5510_command(args: argparse.Namespace) -> int:
    print(json.dumps(validate_tradable_source_recorded_v5510(args.sessions_dir, args.initial_cash_krw), ensure_ascii=False, default=str))
    return 0


def run_tradable_source_live_smoke_v5510_command(args: argparse.Namespace) -> int:
    research_mode = str(args.research_mode).lower() == "true"
    print(json.dumps(run_tradable_source_live_smoke_v5510(args.duration_minutes, args.top_markets, args.initial_cash_krw, research_mode), ensure_ascii=False, default=str))
    return 0


def run_tradable_source_live_forward_v5510_command(args: argparse.Namespace) -> int:
    research_mode = str(args.research_mode).lower() == "true"
    print(json.dumps(run_tradable_source_live_forward_v5510(args.duration_minutes, args.top_markets, args.initial_cash_krw, research_mode), ensure_ascii=False, default=str))
    return 0


def validate_full_seed_tradable_sources_v5510_command(args: argparse.Namespace) -> int:
    print(json.dumps(validate_full_seed_tradable_sources_v5510(args.reports_dir, args.initial_cash_krw), ensure_ascii=False, default=str))
    return 0


def run_head_controller_tradable_winner_review_v5510_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_head_controller_tradable_winner_review_v5510(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def build_tradable_winner_mining_report_v5510_command(args: argparse.Namespace) -> int:
    print(f"tradable winner mining report: {TradableWinnerMiningHTMLReportV5510().build()}")
    return 0


def build_high_volatility_session_report_v5510_command(args: argparse.Namespace) -> int:
    print(f"high volatility session report: {HighVolatilitySessionHTMLReportV5510().build()}")
    return 0


def build_tradable_source_forward_report_v5510_command(args: argparse.Namespace) -> int:
    print(f"tradable source forward report: {TradableSourceForwardHTMLReportV5510().build()}")
    return 0


def build_head_controller_tradable_winner_review_report_v5510_command(args: argparse.Namespace) -> int:
    print(f"head controller tradable winner review report: {HeadControllerTradableWinnerReviewHTMLReportV5510().build()}")
    return 0


def run_timing_lab_live_v5r1_command(args: argparse.Namespace) -> int:
    research_mode = str(args.research_mode).lower() == "true"
    print(json.dumps(run_timing_lab_live_v5r1(args.duration_minutes, args.top_markets, args.buffer_minutes, args.post_event_minutes, research_mode), ensure_ascii=False, default=str))
    return 0


def replay_timing_lab_v5r1_command(args: argparse.Namespace) -> int:
    print(json.dumps(replay_timing_lab_v5r1(args.sessions_dir, args.buffer_minutes, args.post_event_minutes), ensure_ascii=False, default=str))
    return 0


def label_event_clips_v5r1_command(args: argparse.Namespace) -> int:
    print(json.dumps(label_event_clips(args.clips_dir), ensure_ascii=False, default=str))
    return 0


def analyze_entry_windows_v5r1_command(args: argparse.Namespace) -> int:
    result = analyze_entry_windows(args.clips_dir)
    out = REPLAY_STORE_DIR / "timing_state_replay" / "latest_entry_window_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def validate_entry_state_machine_v5r1_command(args: argparse.Namespace) -> int:
    print(json.dumps(validate_entry_state_machine_v5r1(args.clips_dir), ensure_ascii=False, default=str))
    return 0


def run_timing_based_paper_v5r1_command(args: argparse.Namespace) -> int:
    research_mode = str(args.research_mode).lower() == "true"
    print(json.dumps(run_timing_based_paper_v5r1(args.clips_dir, args.initial_cash_krw, research_mode), ensure_ascii=False, default=str))
    return 0


def audit_llm_usage_v5r1_command(args: argparse.Namespace) -> int:
    print(json.dumps(audit_llm_usage_v5r1(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_head_controller_timing_review_v5r1_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_head_controller_timing_review_v5r1(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def build_timing_lab_report_v5r1_command(args: argparse.Namespace) -> int:
    print(f"timing lab report: {TimingLabHTMLReportV5R1().build()}")
    return 0


def build_entry_timing_report_v5r1_command(args: argparse.Namespace) -> int:
    print(f"entry timing report: {EntryTimingHTMLReportV5R1().build()}")
    return 0


def build_llm_usage_report_v5r1_command(args: argparse.Namespace) -> int:
    print(f"llm usage report: {LLMUsageHTMLReportV5R1().build()}")
    return 0


def build_head_controller_timing_review_report_v5r1_command(args: argparse.Namespace) -> int:
    print(f"head controller timing review report: {HeadControllerTimingReviewHTMLReportV5R1().build()}")
    return 0


def decompose_fake_signals_v5r2_command(args: argparse.Namespace) -> int:
    print(json.dumps(decompose_fake_signals(args.clips_dir), ensure_ascii=False, default=str))
    return 0


def analyze_follow_through_failures_v5r2_command(args: argparse.Namespace) -> int:
    print(json.dumps(analyze_follow_through_failures(args.clips_dir), ensure_ascii=False, default=str))
    return 0


def score_event_types_v5r2_command(args: argparse.Namespace) -> int:
    print(json.dumps(score_event_types(args.clips_dir), ensure_ascii=False, default=str))
    return 0


def analyze_detector_gaps_v5r2_command(args: argparse.Namespace) -> int:
    print(json.dumps(analyze_detector_gaps(args.clips_dir), ensure_ascii=False, default=str))
    return 0


def calibrate_armed_state_v5r2_command(args: argparse.Namespace) -> int:
    print(json.dumps(tune_armed_thresholds(args.clips_dir), ensure_ascii=False, default=str))
    return 0


def calibrate_confirmation_v5r2_command(args: argparse.Namespace) -> int:
    print(json.dumps(tune_confirmation_thresholds(args.clips_dir), ensure_ascii=False, default=str))
    return 0


def run_calibration_grid_v5r2_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_calibration_grid(args.clips_dir), ensure_ascii=False, default=str))
    return 0


def run_llm_minimum_completion_test_v5r2_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_llm_minimum_completion_test(args.llm_provider), ensure_ascii=False, default=str))
    return 0


def repair_llm_completion_v5r2_command(args: argparse.Namespace) -> int:
    print(json.dumps(repair_llm_completion_v5r2(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def build_project_scorecard_v5r2_command(args: argparse.Namespace) -> int:
    result = build_project_scorecard()
    out = Path(args.reports_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest_project_scorecard_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def run_head_controller_v5r2_review_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_head_controller_v5r2_review(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def build_fake_signal_decomposition_report_v5r2_command(args: argparse.Namespace) -> int:
    print(f"fake signal decomposition report: {FakeSignalDecompositionHTMLReportV5R2().build()}")
    return 0


def build_confirmation_calibration_report_v5r2_command(args: argparse.Namespace) -> int:
    print(f"confirmation calibration report: {ConfirmationCalibrationHTMLReportV5R2().build()}")
    return 0


def build_llm_completion_repair_report_v5r2_command(args: argparse.Namespace) -> int:
    print(f"llm completion repair report: {LLMCompletionRepairHTMLReportV5R2().build()}")
    return 0


def build_project_scorecard_report_v5r2_command(args: argparse.Namespace) -> int:
    print(f"project scorecard report: {ProjectScorecardHTMLReportV5R2().build()}")
    return 0


def build_head_controller_v5r2_review_report_command(args: argparse.Namespace) -> int:
    print(f"head controller v5r2 review report: {HeadControllerV5R2ReviewHTMLReport().build()}")
    return 0


def build_market_regime_v5r3_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_market_regime_v5r3(args.sessions_dir), ensure_ascii=False, default=str))
    return 0


def build_setup_candidates_v5r3_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_setup_candidates_v5r3(args.sessions_dir, args.initial_cash_krw), ensure_ascii=False, default=str))
    return 0


def build_scenarios_v5r3_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_scenarios_v5r3(), ensure_ascii=False, default=str))
    return 0


def run_scenario_replay_v5r3_command(args: argparse.Namespace) -> int:
    print(
        json.dumps(
            run_scenario_replay_v5r3(args.scenario_set, args.initial_cash_krw, args.risk_profile),
            ensure_ascii=False,
            default=str,
        )
    )
    return 0


def run_aggressive_paper_learning_v5r3_command(args: argparse.Namespace) -> int:
    research_mode = str(args.research_mode).lower() == "true"
    print(
        json.dumps(
            run_aggressive_paper_learning_v5r3(
                args.duration_minutes,
                args.top_markets,
                args.initial_cash_krw,
                args.risk_profile,
                research_mode,
            ),
            ensure_ascii=False,
            default=str,
        )
    )
    return 0


def run_llm_strategy_review_v5r3_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_llm_strategy_review_v5r3(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def build_v5r3_strategy_learning_report_command(args: argparse.Namespace) -> int:
    print(f"v5r3 strategy learning report: {V5R3StrategyLearningHTMLReport().build(args.reports_dir)}")
    return 0


def collect_v6_ohlcv_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v6_ohlcv_collection(args.markets, args.months, args.timeframes), ensure_ascii=False, default=str))
    return 0


def build_v6_mtf_context_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v6_mtf_context_generation(args.markets), ensure_ascii=False, default=str))
    return 0


def run_v6_daddy_backtest_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v6_daddy_backtest(args.months, args.initial_cash_krw, args.paper_entry_policy), ensure_ascii=False, default=str))
    return 0


def run_v6_ict_backtest_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v6_ict_backtest(args.months, args.initial_cash_krw, args.paper_entry_policy), ensure_ascii=False, default=str))
    return 0


def run_v6_combined_backtest_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v6_combined_backtest(args.months, args.initial_cash_krw, args.paper_entry_policy), ensure_ascii=False, default=str))
    return 0


def run_v6_weekly_paper_simulation_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v6_weekly_paper_simulation(args.months, args.initial_cash_krw, args.paper_entry_policy), ensure_ascii=False, default=str))
    return 0


def run_head_controller_v6_review_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_head_controller_v6_review(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def build_v6_mtf_report_command(args: argparse.Namespace) -> int:
    print(f"v6 mtf report: {V6MTFReportHTML().build(args.reports_dir)}")
    return 0


def build_v6_daddy_strategy_report_command(args: argparse.Namespace) -> int:
    print(f"v6 daddy report: {V6DaddyStrategyReportHTML().build(args.reports_dir)}")
    return 0


def build_v6_ict_strategy_report_command(args: argparse.Namespace) -> int:
    print(f"v6 ict report: {V6ICTStrategyReportHTML().build(args.reports_dir)}")
    return 0


def build_v6_combined_strategy_report_command(args: argparse.Namespace) -> int:
    print(f"v6 combined report: {V6CombinedStrategyReportHTML().build(args.reports_dir)}")
    return 0


def build_v6_weekly_performance_report_command(args: argparse.Namespace) -> int:
    print(f"v6 weekly report: {V6WeeklyPerformanceReportHTML().build(args.reports_dir)}")
    return 0


def build_head_controller_v6_review_report_command(args: argparse.Namespace) -> int:
    print(f"head controller v6 report: {HeadControllerV6ReviewHTML().build(args.reports_dir)}")
    return 0


def collect_v61_long_ohlcv_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v61_long_horizon_collection(args.markets, args.months, args.timeframes), ensure_ascii=False, default=str))
    return 0


def build_v61_coverage_report_command(args: argparse.Namespace) -> int:
    summary = build_ohlcv_coverage(args.data_dir, 36)
    path = Path("docs/reports/latest_v61_coverage_summary.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, default=str))
    return 0


def run_v61_strategy_robustness_backtest_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v61_strategy_robustness_backtest(args.months, args.initial_cash_krw, args.paper_entry_policy), ensure_ascii=False, default=str))
    return 0


def run_v61_regime_backtest_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v61_regime_backtest(args.initial_cash_krw), ensure_ascii=False, default=str))
    return 0


def analyze_v61_big_win_dependency_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v61_big_win_dependency(), ensure_ascii=False, default=str))
    return 0


def analyze_v61_failure_success_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v61_failure_success_analysis(), ensure_ascii=False, default=str))
    return 0


def run_v61_risk_parameter_sweep_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v61_risk_sweep(), ensure_ascii=False, default=str))
    return 0


def run_v61_train_test_validation_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v61_train_test_validation(args.initial_cash_krw), ensure_ascii=False, default=str))
    return 0


def build_v61_final_strategy_decision_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v61_final_decision(), ensure_ascii=False, default=str))
    return 0


def run_head_controller_v61_review_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_head_controller_v61_review(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def build_v61_coverage_report_html_command(args: argparse.Namespace) -> int:
    print(f"v61 coverage report: {V61CoverageReportHTML().build(args.reports_dir)}")
    return 0


def build_v61_strategy_robustness_report_html_command(args: argparse.Namespace) -> int:
    print(f"v61 robustness report: {V61StrategyRobustnessReportHTML().build(args.reports_dir)}")
    return 0


def build_v61_regime_report_html_command(args: argparse.Namespace) -> int:
    print(f"v61 regime report: {V61RegimeReportHTML().build(args.reports_dir)}")
    return 0


def build_v61_big_win_dependency_report_html_command(args: argparse.Namespace) -> int:
    print(f"v61 big win report: {V61BigWinDependencyReportHTML().build(args.reports_dir)}")
    return 0


def build_v61_failure_success_report_html_command(args: argparse.Namespace) -> int:
    print(f"v61 failure success report: {V61FailureSuccessReportHTML().build(args.reports_dir)}")
    return 0


def build_v61_risk_sweep_report_html_command(args: argparse.Namespace) -> int:
    print(f"v61 risk sweep report: {V61RiskSweepReportHTML().build(args.reports_dir)}")
    return 0


def build_v61_final_decision_report_html_command(args: argparse.Namespace) -> int:
    print(f"v61 final decision report: {V61FinalDecisionReportHTML().build(args.reports_dir)}")
    return 0


def build_head_controller_v61_review_report_html_command(args: argparse.Namespace) -> int:
    print(f"head controller v61 report: {HeadControllerV61ReviewHTML().build(args.reports_dir)}")
    return 0


def run_v62_capital_growth_backtest_command(args: argparse.Namespace) -> int:
    compounding = str(args.compounding).lower() == "true"
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v62_capital_growth_backtest(args.initial_cash_krw, compounding, use_history), ensure_ascii=False, default=str))
    return 0


def validate_v62_strategy_router_command(args: argparse.Namespace) -> int:
    print(json.dumps(validate_v62_strategy_router(args.initial_cash_krw), ensure_ascii=False, default=str))
    return 0


def run_v62_real_exit_sweep_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v62_real_exit_sweep(args.initial_cash_krw), ensure_ascii=False, default=str))
    return 0


def build_v62_investment_reports_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v62_investment_reports(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v62_risk_strengthen_review_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v62_risk_strengthen_review(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_head_controller_v62_review_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_head_controller_v62_review(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def build_v62_trade_journal_report_html_command(args: argparse.Namespace) -> int:
    print(f"v62 trade journal report: {V62TradeJournalHTML().build(args.reports_dir)}")
    return 0


def build_v62_weekly_report_html_command(args: argparse.Namespace) -> int:
    print(f"v62 weekly report: {V62WeeklyReportHTML().build(args.reports_dir)}")
    return 0


def build_v62_monthly_report_html_command(args: argparse.Namespace) -> int:
    print(f"v62 monthly report: {V62MonthlyReportHTML().build(args.reports_dir)}")
    return 0


def build_v62_full_investment_report_html_command(args: argparse.Namespace) -> int:
    print(f"v62 full investment report: {V62FullInvestmentReportHTML().build(args.reports_dir)}")
    return 0


def build_v62_strategy_router_report_html_command(args: argparse.Namespace) -> int:
    print(f"v62 strategy router report: {V62StrategyRouterReportHTML().build(args.reports_dir)}")
    return 0


def build_v62_risk_report_html_command(args: argparse.Namespace) -> int:
    print(f"v62 risk report: {V62RiskReportHTML().build(args.reports_dir)}")
    return 0


def build_head_controller_v62_review_report_html_command(args: argparse.Namespace) -> int:
    print(f"head controller v62 report: {HeadControllerV62ReviewHTML().build(args.reports_dir)}")
    return 0


def collect_upbit_historical_archive_command(args: argparse.Namespace) -> int:
    result = collect_upbit_historical_archive(
        markets=args.markets,
        timeframes=args.timeframes,
        max_lookback_days=args.max_lookback_days,
        archive_dir=args.archive_dir,
    )
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def run_true_walk_forward_paper_command(args: argparse.Namespace) -> int:
    result = run_true_walk_forward_paper(
        initial_cash_krw=args.initial_cash_krw,
        archive_dir=args.archive_dir,
        risk_profile=args.risk_profile,
    )
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def build_investor_dashboard_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_investor_dashboard(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_drawdown_defense_revalidation_command(args: argparse.Namespace) -> int:
    result = run_drawdown_defense_revalidation(
        summary_path=args.summary_path,
        archive_dir=args.archive_dir,
        initial_cash_krw=args.initial_cash_krw,
    )
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def build_drawdown_defense_report_html_command(args: argparse.Namespace) -> int:
    print(f"drawdown defense report: {DrawdownDefenseHTMLReport().build(args.reports_dir)}")
    return 0


def run_v64_causal_defense_rerun_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v64_causal_defense_rerun(args.initial_cash_krw, use_history), ensure_ascii=False, default=str))
    return 0


def run_v64_return_amplification_lab_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v64_return_amplification_lab(args.initial_cash_krw, use_history), ensure_ascii=False, default=str))
    return 0


def build_v64_scenario_comparison_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v64_scenario_comparison(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v64_hindsight_audit_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v64_hindsight_audit(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v64_investor_summary_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v64_investor_summary(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v64_policy_blend_analysis_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v64_policy_blend_analysis(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v64_policy_compounding_analysis_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v64_policy_compounding_analysis(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_head_controller_v64_review_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_head_controller_v64_review(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def build_v64_causal_defense_report_html_command(args: argparse.Namespace) -> int:
    print(f"v64 causal defense report: {V64CausalDefenseHTMLReport().build(args.reports_dir)}")
    return 0


def build_v64_return_amplification_report_html_command(args: argparse.Namespace) -> int:
    print(f"v64 return amplification report: {V64ReturnAmplificationHTMLReport().build(args.reports_dir)}")
    return 0


def build_v64_scenario_comparison_report_html_command(args: argparse.Namespace) -> int:
    print(f"v64 scenario comparison report: {V64ScenarioComparisonHTMLReport().build(args.reports_dir)}")
    return 0


def build_v64_hindsight_audit_report_html_command(args: argparse.Namespace) -> int:
    print(f"v64 hindsight audit report: {V64HindsightAuditHTMLReport().build(args.reports_dir)}")
    return 0


def build_v64_investor_summary_report_html_command(args: argparse.Namespace) -> int:
    print(f"v64 investor report: {V64InvestorSummaryHTMLReport().build(args.reports_dir)}")
    return 0


def build_head_controller_v64_review_report_html_command(args: argparse.Namespace) -> int:
    print(f"head controller v64 report: {HeadControllerV64ReviewHTML().build(args.reports_dir)}")
    return 0


def build_v65_ma_features_command(args: argparse.Namespace) -> int:
    summary = build_v65_ma_features(archive_dir=str(REPLAY_STORE_DIR / "historical_archive"))
    print(json.dumps({"feature_count": summary.get("feature_count"), "lookahead_fail_count": summary.get("lookahead_fail_count")}, ensure_ascii=False))
    return 0


def run_v65_ma_scenario_lab_command(args: argparse.Namespace) -> int:
    summary = run_v65_ma_scenario_lab(args.initial_cash_krw, archive_dir=str(REPLAY_STORE_DIR / "historical_archive"))
    print(json.dumps({"scenarios": len(summary.get("scenarios", [])), "best": summary.get("recommendation", {}).get("best_scenario")}, ensure_ascii=False))
    return 0


def run_v65_ma_policy_router_lab_command(args: argparse.Namespace) -> int:
    summary = run_v65_ma_policy_router_lab(args.initial_cash_krw, archive_dir=str(REPLAY_STORE_DIR / "historical_archive"))
    print(json.dumps({"best_scenario": summary.get("best_scenario")}, ensure_ascii=False))
    return 0


def analyze_v65_yearly_weakness_repair_command(args: argparse.Namespace) -> int:
    summary = analyze_v65_yearly_weakness_repair(args.reports_dir)
    print(json.dumps({"years": len(summary.get("yearly_comparison", []))}, ensure_ascii=False))
    return 0


def build_v65_ma_risk_report_command(args: argparse.Namespace) -> int:
    summary = build_v65_ma_risk_report(args.reports_dir)
    print(json.dumps({"final_judgement": summary.get("final_judgement")}, ensure_ascii=False))
    return 0


def run_head_controller_v65_review_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_head_controller_v65_review(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def build_v65_ma_scenario_report_html_command(args: argparse.Namespace) -> int:
    print(f"v65 ma scenario report: {V65MAScenarioReportHTML(args.reports_dir).build()}")
    return 0


def build_v65_ma_policy_router_report_html_command(args: argparse.Namespace) -> int:
    print(f"v65 ma policy router report: {V65MAPolicyRouterReportHTML(args.reports_dir).build()}")
    return 0


def build_v65_yearly_repair_report_html_command(args: argparse.Namespace) -> int:
    print(f"v65 yearly repair report: {V65YearlyRepairReportHTML(args.reports_dir).build()}")
    return 0


def build_v65_ma_risk_report_html_command(args: argparse.Namespace) -> int:
    print(f"v65 ma risk report: {V65MARiskReportHTML(args.reports_dir).build()}")
    return 0


def build_head_controller_v65_review_report_html_command(args: argparse.Namespace) -> int:
    print(f"head controller v65 report: {HeadControllerV65ReviewHTML(args.reports_dir).build()}")
    return 0


def audit_v66_btcd_inclusion_command(args: argparse.Namespace) -> int:
    print(json.dumps(audit_v66_btcd_inclusion(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def prepare_v66_btcd_data_command(args: argparse.Namespace) -> int:
    print(json.dumps(prepare_v66_btcd_data(archive_dir=str(REPLAY_STORE_DIR / "historical_archive")), ensure_ascii=False, default=str))
    return 0


def build_v66_btcd_data_quality_report_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v66_btcd_data_quality_report(args.reports_dir, str(REPLAY_STORE_DIR / "historical_archive")), ensure_ascii=False, default=str))
    return 0


def run_v66_btcd_rolling_balanced_lab_command(args: argparse.Namespace) -> int:
    summary = run_v66_btcd_rolling_balanced_lab(args.initial_cash_krw, archive_dir=str(REPLAY_STORE_DIR / "historical_archive"))
    print(json.dumps({"scenarios": len(summary.get("scenarios", []))}, ensure_ascii=False))
    return 0


def run_v66_btcd_bear_regime_lab_command(args: argparse.Namespace) -> int:
    summary = run_v66_btcd_bear_regime_lab(args.initial_cash_krw, archive_dir=str(REPLAY_STORE_DIR / "historical_archive"))
    print(json.dumps({"scenarios": len(summary.get("scenarios", []))}, ensure_ascii=False))
    return 0


def run_v66_btcd_bear_bounce_lab_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v66_btcd_bear_bounce_lab(args.initial_cash_krw, archive_dir=str(REPLAY_STORE_DIR / "historical_archive")), ensure_ascii=False, default=str))
    return 0


def run_v66_btcd_short_research_lab_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v66_btcd_short_research_lab(args.initial_cash_krw, archive_dir=str(REPLAY_STORE_DIR / "historical_archive")), ensure_ascii=False, default=str))
    return 0


def run_v66_btcd_hybrid_router_lab_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v66_btcd_hybrid_router_lab(args.initial_cash_krw, archive_dir=str(REPLAY_STORE_DIR / "historical_archive")), ensure_ascii=False, default=str))
    return 0


def build_v66_btcd_scenario_comparison_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v66_btcd_scenario_comparison(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_head_controller_v66_review_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_head_controller_v66_review(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def build_v66_btcd_inclusion_audit_report_html_command(args: argparse.Namespace) -> int:
    print(f"v66 btcd inclusion audit report: {V66BTCDInclusionAuditHTML(args.reports_dir).build()}")
    return 0


def build_v66_btcd_data_quality_report_html_command(args: argparse.Namespace) -> int:
    print(f"v66 btcd data quality report: {V66BTCDDataQualityHTML(args.reports_dir).build()}")
    return 0


def build_v66_btcd_rolling_balanced_report_html_command(args: argparse.Namespace) -> int:
    print(f"v66 btcd rolling balanced report: {V66BTCDRollingBalancedHTML(args.reports_dir).build()}")
    return 0


def build_v66_btcd_bear_scenario_report_html_command(args: argparse.Namespace) -> int:
    print(f"v66 btcd bear scenario report: {V66BTCDBearScenarioHTML(args.reports_dir).build()}")
    return 0


def build_v66_btcd_2024_11_focus_report_html_command(args: argparse.Namespace) -> int:
    print(f"v66 btcd 2024-11 focus report: {V66BTCD202411FocusHTML(args.reports_dir).build()}")
    return 0


def build_v66_btcd_saved_loss_missed_profit_report_html_command(args: argparse.Namespace) -> int:
    print(f"v66 btcd saved loss missed profit report: {V66BTCDSavedLossMissedProfitHTML(args.reports_dir).build()}")
    return 0


def build_v66_btcd_scenario_comparison_report_html_command(args: argparse.Namespace) -> int:
    print(f"v66 btcd scenario comparison report: {V66BTCDScenarioComparisonHTML(args.reports_dir).build()}")
    return 0


def build_v66_btcd_short_research_report_html_command(args: argparse.Namespace) -> int:
    print(f"v66 btcd short research report: {V66BTCDShortResearchHTML(args.reports_dir).build()}")
    return 0


def build_v66_btcd_hybrid_router_report_html_command(args: argparse.Namespace) -> int:
    print(f"v66 btcd hybrid router report: {V66BTCDHybridRouterHTML(args.reports_dir).build()}")
    return 0


def build_head_controller_v66_review_report_html_command(args: argparse.Namespace) -> int:
    print(f"head controller v66 report: {HeadControllerV66ReviewHTML(args.reports_dir).build()}")
    return 0


def prepare_v67_global_btcd_data_command(args: argparse.Namespace) -> int:
    print(json.dumps(prepare_v67_global_btcd_data(use_available_history=str(args.use_available_history).lower() == "true"), ensure_ascii=False, default=str))
    return 0


def build_v67_global_btcd_data_quality_report_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v67_global_btcd_data_quality_report(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v67_global_btcd_scenario_lab_command(args: argparse.Namespace) -> int:
    summary = run_v67_global_btcd_scenario_lab(args.initial_cash_krw, archive_dir=str(REPLAY_STORE_DIR / "historical_archive"))
    print(json.dumps({"scenarios": len(summary.get("scenarios", [])), "full_period_validation_possible": summary.get("full_period_validation_possible")}, ensure_ascii=False))
    return 0


def run_v67_global_btcd_compact_router_lab_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v67_global_btcd_compact_router_lab(), ensure_ascii=False, default=str))
    return 0


def build_v67_global_btcd_rejected_scenarios_report_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v67_global_btcd_rejected_scenarios_report(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v67_global_btcd_saved_loss_report_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v67_global_btcd_saved_loss_report(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v67_global_btcd_yearly_report_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v67_global_btcd_yearly_report(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_head_controller_v67_review_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_head_controller_v67_review(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def build_v67_global_btcd_data_quality_report_html_command(args: argparse.Namespace) -> int:
    print(f"v67 global btcd data quality report: {V67GlobalBTCDDataQualityHTML(args.reports_dir).build()}")
    return 0


def build_v67_global_btcd_scenario_report_html_command(args: argparse.Namespace) -> int:
    print(f"v67 global btcd scenario report: {V67GlobalBTCDScenarioHTML(args.reports_dir).build()}")
    return 0


def build_v67_global_btcd_saved_loss_report_html_command(args: argparse.Namespace) -> int:
    print(f"v67 global btcd saved loss report: {V67GlobalBTCDSavedLossHTML(args.reports_dir).build()}")
    return 0


def build_v67_global_btcd_yearly_report_html_command(args: argparse.Namespace) -> int:
    print(f"v67 global btcd yearly report: {V67GlobalBTCDYearlyHTML(args.reports_dir).build()}")
    return 0


def build_v67_global_btcd_rejected_scenarios_report_html_command(args: argparse.Namespace) -> int:
    print(f"v67 global btcd rejected scenarios report: {V67GlobalBTCDRejectedHTML(args.reports_dir).build()}")
    return 0


def build_v67_global_btcd_compact_router_report_html_command(args: argparse.Namespace) -> int:
    print(f"v67 global btcd compact router report: {V67GlobalBTCDCompactRouterHTML(args.reports_dir).build()}")
    return 0


def build_head_controller_v67_review_report_html_command(args: argparse.Namespace) -> int:
    print(f"head controller v67 report: {HeadControllerV67ReviewHTML(args.reports_dir).build()}")
    return 0


def prepare_v672_btcdom_index_data_command(args: argparse.Namespace) -> int:
    print(json.dumps(prepare_v672_btcdom_index_data(args.source_dir, use_available_history=str(args.use_available_history).lower() == "true"), ensure_ascii=False, default=str))
    return 0


def build_v672_btcdom_index_data_quality_report_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v672_btcdom_index_data_quality_report(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v672_btcdom_index_scenario_lab_command(args: argparse.Namespace) -> int:
    summary = run_v672_btcdom_index_scenario_lab(args.initial_cash_krw, archive_dir=str(REPLAY_STORE_DIR / "historical_archive"))
    print(json.dumps({"scenarios": len(summary.get("scenarios", [])), "coverage_period_validation_possible": summary.get("coverage_period_validation_possible")}, ensure_ascii=False))
    return 0


def run_v672_btcdom_index_compact_router_lab_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v672_btcdom_index_compact_router_lab(args.initial_cash_krw, archive_dir=str(REPLAY_STORE_DIR / "historical_archive")), ensure_ascii=False, default=str))
    return 0


def build_v672_btcdom_index_rejected_scenarios_report_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v672_btcdom_index_rejected_scenarios_report(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v672_btcdom_index_saved_loss_report_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v672_btcdom_index_saved_loss_report(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v672_btcdom_index_yearly_report_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v672_btcdom_index_yearly_report(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_head_controller_v672_review_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_head_controller_v672_review(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def build_v672_btcdom_index_data_quality_report_html_command(args: argparse.Namespace) -> int:
    print(f"v672 btcdom index data quality report: {V672BTCDOMIndexDataQualityHTML(args.reports_dir).build()}")
    return 0


def build_v672_btcdom_index_scenario_report_html_command(args: argparse.Namespace) -> int:
    print(f"v672 btcdom index scenario report: {V672BTCDOMIndexScenarioHTML(args.reports_dir).build()}")
    return 0


def build_v672_btcdom_index_saved_loss_report_html_command(args: argparse.Namespace) -> int:
    print(f"v672 btcdom index saved loss report: {V672BTCDOMIndexSavedLossHTML(args.reports_dir).build()}")
    return 0


def build_v672_btcdom_index_yearly_report_html_command(args: argparse.Namespace) -> int:
    print(f"v672 btcdom index yearly report: {V672BTCDOMIndexYearlyHTML(args.reports_dir).build()}")
    return 0


def build_v672_btcdom_index_rejected_scenarios_report_html_command(args: argparse.Namespace) -> int:
    print(f"v672 btcdom index rejected scenarios report: {V672BTCDOMIndexRejectedHTML(args.reports_dir).build()}")
    return 0


def build_v672_btcdom_index_compact_router_report_html_command(args: argparse.Namespace) -> int:
    print(f"v672 btcdom index compact router report: {V672BTCDOMIndexCompactRouterHTML(args.reports_dir).build()}")
    return 0


def build_head_controller_v672_review_report_html_command(args: argparse.Namespace) -> int:
    print(f"head controller v672 report: {HeadControllerV672ReviewHTML(args.reports_dir).build()}")
    return 0


def prepare_v673_dominance_data_command(args: argparse.Namespace) -> int:
    print(json.dumps(prepare_v673_dominance_data(args.source_dir, str(args.use_available_history).lower() == "true", args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v673_dominance_data_quality_report_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v673_dominance_data_quality_report(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v673_rolling_balanced_dominance_matrix_lab_command(args: argparse.Namespace) -> int:
    summary = run_v673_rolling_balanced_dominance_matrix_lab(args.initial_cash_krw, str(args.use_available_history).lower() == "true", args.reports_dir, str(REPLAY_STORE_DIR / "historical_archive"))
    print(json.dumps({"scenarios": len(summary.get("scenarios", [])), "coverage_period_validation_possible": summary.get("coverage_period_validation_possible")}, ensure_ascii=False))
    return 0


def run_v673_bear_agent_lab_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v673_bear_agent_lab(args.initial_cash_krw, str(args.use_available_history).lower() == "true", args.reports_dir, str(REPLAY_STORE_DIR / "historical_archive")), ensure_ascii=False, default=str))
    return 0


def run_v673_scenario_agent_router_lab_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v673_scenario_agent_router_lab(args.initial_cash_krw, str(args.use_available_history).lower() == "true", args.reports_dir, str(REPLAY_STORE_DIR / "historical_archive")), ensure_ascii=False, default=str))
    return 0


def build_v673_high_watermark_report_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v673_high_watermark_report(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v673_rejected_scenarios_report_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v673_rejected_scenarios_report(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v673_saved_loss_report_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v673_saved_loss_report(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v673_yearly_market_state_report_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v673_yearly_market_state_report(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_head_controller_v673_review_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_head_controller_v673_review(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def build_v673_dominance_data_quality_report_html_command(args: argparse.Namespace) -> int:
    print(f"v673 dominance data quality report: {V673DominanceDataQualityHTML(args.reports_dir).build()}")
    return 0


def build_v673_agent_matrix_report_html_command(args: argparse.Namespace) -> int:
    print(f"v673 agent matrix report: {V673AgentMatrixHTML(args.reports_dir).build()}")
    return 0


def build_v673_bear_agent_report_html_command(args: argparse.Namespace) -> int:
    print(f"v673 bear agent report: {V673BearAgentHTML(args.reports_dir).build()}")
    return 0


def build_v673_scenario_router_report_html_command(args: argparse.Namespace) -> int:
    print(f"v673 scenario router report: {V673ScenarioRouterHTML(args.reports_dir).build()}")
    return 0


def build_v673_high_watermark_report_html_command(args: argparse.Namespace) -> int:
    print(f"v673 high watermark report: {V673HighWatermarkHTML(args.reports_dir).build()}")
    return 0


def build_v673_rejected_scenarios_report_html_command(args: argparse.Namespace) -> int:
    print(f"v673 rejected scenarios report: {V673RejectedScenariosHTML(args.reports_dir).build()}")
    return 0


def build_head_controller_v673_review_report_html_command(args: argparse.Namespace) -> int:
    print(f"head controller v673 report: {HeadControllerV673ReviewHTML(args.reports_dir).build()}")
    return 0


def audit_v681_compounding_vs_dominance_ledger_command(args: argparse.Namespace) -> int:
    print(json.dumps(audit_v681_compounding_vs_dominance_ledger_lab(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v681_compounding_dominance_lab_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v681_compounding_dominance_lab(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v681_bear_compounding_agent_lab_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v681_bear_compounding_agent_lab(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v681_compounding_scenario_router_lab_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v681_compounding_scenario_router_lab(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v681_control_tower_review_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v681_control_tower_review_lab(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def run_v681_paper_backfill_from_20260101_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v681_paper_backfill_lab(args.initial_cash_krw, args.start_date, args.active_route, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def start_v681_paper_server_command(args: argparse.Namespace) -> int:
    print(json.dumps(start_v681_paper_server_lab(args.active_route, args.port, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def register_v681_shadow_route_command(args: argparse.Namespace) -> int:
    print(json.dumps(register_v681_shadow_route_lab(args.route, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v681_integrated_investment_report_html_command(args: argparse.Namespace) -> int:
    print(f"v681 integrated investment report: {build_v681_integrated_investment_report_html(args.reports_dir)}")
    return 0


def run_v682_bear_defense_deep_insight_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v682_bear_defense_deep_insight_lab(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v682_bear_bounce_profit_lab_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v682_bear_bounce_profit_lab(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v682_bear_response_router_lab_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v682_bear_response_router_lab(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v682_bounce_case_study_report_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v682_bounce_case_study_lab(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v682_bear_defense_insight_report_html_command(args: argparse.Namespace) -> int:
    print(f"v682 bear defense insight report: {build_v682_bear_defense_insight_report_html(args.reports_dir)}")
    return 0


def build_v682_bear_bounce_report_html_command(args: argparse.Namespace) -> int:
    print(f"v682 bear bounce report: {build_v682_bear_bounce_report_html(args.reports_dir)}")
    return 0


def build_v682_bear_response_router_report_html_command(args: argparse.Namespace) -> int:
    print(f"v682 bear response router report: {build_v682_bear_response_router_report_html(args.reports_dir)}")
    return 0


def build_v682_bounce_case_study_report_html_command(args: argparse.Namespace) -> int:
    print(f"v682 bounce case study report: {build_v682_bounce_case_study_report_html(args.reports_dir)}")
    return 0


def register_v682_bear_shadow_route_command(args: argparse.Namespace) -> int:
    print(json.dumps(register_v682_bear_shadow_route_lab(args.route, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v683_paper_backfill_from_20260101_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v683_paper_backfill_lab(args.initial_cash_krw, args.start_date, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def start_v683_live_forward_paper_command(args: argparse.Namespace) -> int:
    print(json.dumps(start_v683_live_forward_paper_lab(args.active_route, args.port, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def check_v683_paper_health_command(args: argparse.Namespace) -> int:
    print(json.dumps(check_v683_paper_health_lab(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v683_active_shadow_comparison_report_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v683_active_shadow_comparison_lab(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v683_paper_dashboard_html_command(args: argparse.Namespace) -> int:
    print(f"v683 paper dashboard: {build_v683_paper_dashboard_html_lab(args.reports_dir)}")
    return 0


def run_v683_control_tower_review_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v683_control_tower_review_lab(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def build_v683_route_router_report_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v683_route_router_report_lab(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def register_v683_shadow_route_command(args: argparse.Namespace) -> int:
    print(json.dumps(register_v683_shadow_route_lab(args.route, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def switch_v683_active_paper_route_command(args: argparse.Namespace) -> int:
    confirm = str(args.confirm_switch).lower() == "true"
    print(json.dumps(switch_v683_active_paper_route_lab(args.route, confirm, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v684_bear_windows_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(build_v684_bear_windows_lab(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v684_indicator_effectiveness_lab_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v684_indicator_effectiveness(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v684_loss_guard_indicator_lab_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v684_loss_guard_indicator(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v684_bear_bounce_v3_lab_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v684_bear_bounce_v3(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v684_risk_sizing_lab_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v684_risk_sizing(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v684_bear_router_lab_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v684_bear_router(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v684_bear_windows_report_html_command(args: argparse.Namespace) -> int:
    print(f"v684 bear windows report: {build_v684_bear_windows_report_html(args.reports_dir)}")
    return 0


def build_v684_indicator_effectiveness_report_html_command(args: argparse.Namespace) -> int:
    print(f"v684 indicator effectiveness report: {build_v684_indicator_effectiveness_report_html(args.reports_dir)}")
    return 0


def build_v684_loss_guard_indicator_report_html_command(args: argparse.Namespace) -> int:
    print(f"v684 loss guard indicator report: {build_v684_loss_guard_indicator_report_html(args.reports_dir)}")
    return 0


def build_v684_bear_bounce_v3_report_html_command(args: argparse.Namespace) -> int:
    print(f"v684 bear bounce v3 report: {build_v684_bear_bounce_v3_report_html(args.reports_dir)}")
    return 0


def build_v684_risk_sizing_report_html_command(args: argparse.Namespace) -> int:
    print(f"v684 risk sizing report: {build_v684_risk_sizing_report_html(args.reports_dir)}")
    return 0


def build_v684_bear_router_report_html_command(args: argparse.Namespace) -> int:
    print(f"v684 bear router report: {build_v684_bear_router_report_html(args.reports_dir)}")
    return 0


def build_v684_dashboard_html_command(args: argparse.Namespace) -> int:
    print(f"v684 dashboard: {build_v684_dashboard_html(args.reports_dir)}")
    return 0


def run_v685_atr_precision_audit_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v685_atr_precision(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v685_atr_price_path_audit_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v685_atr_price_path(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v685_atr_sensitivity_lab_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v685_atr_sensitivity(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v685_bear_window_classification_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(build_v685_bear_window_classification(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v685_bear_window_performance_lab_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v685_bear_window_performance(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v685_bear_router_window_aware_lab_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v685_bear_router_window_aware(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v685_atr_precision_report_html_command(args: argparse.Namespace) -> int:
    print(f"v685 atr precision report: {build_v685_atr_precision_report_html(args.reports_dir)}")
    return 0


def build_v685_atr_price_path_report_html_command(args: argparse.Namespace) -> int:
    print(f"v685 atr price path report: {build_v685_atr_price_path_report_html(args.reports_dir)}")
    return 0


def build_v685_atr_sensitivity_report_html_command(args: argparse.Namespace) -> int:
    print(f"v685 atr sensitivity report: {build_v685_atr_sensitivity_report_html(args.reports_dir)}")
    return 0


def build_v685_bear_window_classification_report_html_command(args: argparse.Namespace) -> int:
    print(f"v685 bear window classification report: {build_v685_bear_window_classification_report_html(args.reports_dir)}")
    return 0


def build_v685_bear_window_performance_report_html_command(args: argparse.Namespace) -> int:
    print(f"v685 bear window performance report: {build_v685_bear_window_performance_report_html(args.reports_dir)}")
    return 0


def build_v685_bear_router_window_aware_report_html_command(args: argparse.Namespace) -> int:
    print(f"v685 bear router window aware report: {build_v685_bear_router_window_aware_report_html(args.reports_dir)}")
    return 0


def build_v685_dashboard_html_command(args: argparse.Namespace) -> int:
    print(f"v685 dashboard: {V685ReportsHTML(args.reports_dir).build_dashboard()}")
    return 0


def run_v686_atr_ltf_coverage_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v686_atr_ltf_coverage_lab(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v686_atr_ltf_replay_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v686_atr_ltf_replay_lab(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v686_atr_precision_v2_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v686_atr_precision_v2_lab(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v686_bear_window_atr_replay_command(args: argparse.Namespace) -> int:
    use_history = str(args.use_available_history).lower() == "true"
    print(json.dumps(run_v686_bear_window_atr_replay_lab(args.initial_cash_krw, use_history, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def register_v686_shadow_routes_command(args: argparse.Namespace) -> int:
    print(json.dumps(register_v686_shadow_routes_lab(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def run_v686_paper_backfill_with_v685_router_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v686_paper_backfill_with_v685_router_lab(args.initial_cash_krw, args.start_date, args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v686_active_shadow_dashboard_data_command(args: argparse.Namespace) -> int:
    print(json.dumps(build_v686_active_shadow_dashboard_data_lab(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def start_v686_local_dashboard_command(args: argparse.Namespace) -> int:
    start_v686_dashboard(args.host, args.port, args.reports_dir)
    return 0


def check_v686_local_dashboard_health_command(args: argparse.Namespace) -> int:
    print(json.dumps(check_v686_local_dashboard_health_lab(args.reports_dir), ensure_ascii=False, default=str))
    return 0


def build_v686_local_dashboard_report_html_command(args: argparse.Namespace) -> int:
    print(f"v686 local dashboard report: {build_v686_local_dashboard_report_html(args.reports_dir, args.host, args.port)}")
    return 0


def run_v686_control_tower_dashboard_review_command(args: argparse.Namespace) -> int:
    print(json.dumps(run_v686_control_tower_dashboard_review_lab(args.reports_dir, args.llm_provider), ensure_ascii=False, default=str))
    return 0


def build_v686_atr_ltf_coverage_report_html_command(args: argparse.Namespace) -> int:
    print(f"v686 atr ltf coverage report: {build_v686_atr_ltf_coverage_report_html(args.reports_dir)}")
    return 0


def build_v686_atr_ltf_replay_report_html_command(args: argparse.Namespace) -> int:
    print(f"v686 atr ltf replay report: {build_v686_atr_ltf_replay_report_html(args.reports_dir)}")
    return 0


def build_v686_atr_precision_v2_report_html_command(args: argparse.Namespace) -> int:
    print(f"v686 atr precision v2 report: {build_v686_atr_precision_v2_report_html(args.reports_dir)}")
    return 0


def build_v686_atr_model_comparison_report_html_command(args: argparse.Namespace) -> int:
    print(f"v686 atr model comparison report: {build_v686_atr_model_comparison_report_html(args.reports_dir)}")
    return 0


def build_v686_bear_window_atr_replay_report_html_command(args: argparse.Namespace) -> int:
    print(f"v686 bear window atr replay report: {build_v686_bear_window_atr_replay_report_html(args.reports_dir)}")
    return 0


def audit_mock_vs_real_data_command(args: argparse.Namespace) -> int:
    result = audit_mock_vs_real_data(args.sessions_dir)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def check_upbit_auth_safety_command(args: argparse.Namespace) -> int:
    result = run_upbit_auth_safety_check(read_check=str(args.read_check).lower() == "true")
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def build_upbit_real_api_report_command(args: argparse.Namespace) -> int:
    out = UpbitRealAPIHTMLReportBuilder().build()
    print(f"upbit real api report: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ensure_replay_store()
    parser = argparse.ArgumentParser(description="ASTT Replay Lab sidecar CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("load-markets")
    p.set_defaults(func=load_markets)

    p = sub.add_parser("load-candles")
    p.add_argument("--market", required=True)
    p.add_argument("--timeframe", default="1m", choices=["1s", "1m", "5m", "15m", "1h", "1d"])
    p.add_argument("--days", type=int, default=90)
    p.set_defaults(func=load_candles)

    p = sub.add_parser("load-0900")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.set_defaults(func=load_0900)

    p = sub.add_parser("load-intraday")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.set_defaults(func=load_intraday)

    p = sub.add_parser("run-0900")
    p.add_argument("--date", required=True)
    p.add_argument("--markets")
    p.add_argument("--top-markets", type=int)
    p.add_argument("--scan-time", default="08:50")
    p.add_argument("--pre-score-time", default="08:59")
    p.add_argument("--decision-time", default="08:59")
    p.add_argument("--entry-time", default="09:00")
    p.add_argument("--target-window-end-time", default="09:30")
    p.add_argument("--trade-end-time", default="10:00")
    p.add_argument("--strategy-label", default="0850_0900_scalp")
    p.set_defaults(func=run_0900)

    p = sub.add_parser("batch-0900")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--scan-time", default="08:50")
    p.add_argument("--pre-score-time", default="08:59")
    p.add_argument("--decision-time", default="08:59")
    p.add_argument("--entry-time", default="09:00")
    p.add_argument("--target-window-end-time", default="09:30")
    p.add_argument("--trade-end-time", default="10:00")
    p.add_argument("--strategy-label", default="0850_0900_scalp")
    p.set_defaults(func=batch_0900)

    p = sub.add_parser("study-0900-range")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--no-load-first", action="store_true")
    p.add_argument("--use-seconds", action="store_true")
    p.add_argument("--force-daily-entries", action="store_true")
    p.add_argument("--force-daily-count", type=int, default=1)
    p.add_argument("--scan-time", default="08:50")
    p.add_argument("--pre-score-time", default="08:59")
    p.add_argument("--decision-time", default="08:59")
    p.add_argument("--entry-time", default="09:00")
    p.add_argument("--target-window-end-time", default="09:30")
    p.add_argument("--trade-end-time", default="10:00")
    p.add_argument("--strategy-label", default="0850_0900_scalp")
    p.set_defaults(func=study_0900_range)

    p = sub.add_parser("batch-windows")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--entry-times", default="01:00,05:00,09:00,13:00,17:00,21:00")
    p.set_defaults(func=batch_windows)

    p = sub.add_parser("walk-forward")
    p.add_argument("--days", type=int, default=90)
    p.add_argument("--top-markets", type=int, default=50)
    p.set_defaults(func=walk_forward)

    p = sub.add_parser("athena-review")
    p.add_argument("--experiment-id", required=True)
    p.set_defaults(func=athena_review)

    p = sub.add_parser("export-approved")
    p.add_argument("--patch-path", required=True)
    p.add_argument("--experiment-id")
    p.set_defaults(func=export_approved)

    p = sub.add_parser("export-summary")
    p.add_argument("--experiment-id", required=True)
    p.set_defaults(func=export_summary)

    p = sub.add_parser("build-report-catalog")
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--start-date", default="2026-01-01")
    p.add_argument("--current-schema-only", action="store_true", default=True)
    p.add_argument("--include-legacy", action="store_false", dest="current_schema_only")
    p.set_defaults(func=build_report_catalog)

    p = sub.add_parser("build-investment-report")
    p.add_argument("--start-date", default="2026-01-01")
    p.add_argument("--end-date", default=date.today().isoformat())
    p.add_argument("--capital-krw", type=float, default=500000)
    p.set_defaults(func=build_investment_report)

    p = sub.add_parser("study-v2")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--max-daily-entries", type=int, default=1)
    p.add_argument("--candidate-limit", type=int, default=10)
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--markets")
    p.add_argument("--top-markets", type=int)
    p.add_argument("--no-load-first", action="store_true")
    p.set_defaults(func=study_v2)

    p = sub.add_parser("build-investment-v2-report")
    p.add_argument("--start-date", default="2026-01-01")
    p.add_argument("--end-date", default=date.today().isoformat())
    p.add_argument("--capital-krw", type=float, default=500000)
    p.set_defaults(func=build_investment_v2_report)

    p = sub.add_parser("sidecar-c-time-scan")
    p.add_argument("--start-date", default="2026-01-01")
    p.add_argument("--end-date", default=date.today().isoformat())
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--entry-times")
    p.add_argument("--step-minutes", type=int, default=30)
    p.add_argument("--load-missing", action="store_true")
    p.add_argument("--target-move-pct", type=float, default=1.0)
    p.add_argument("--max-adverse-pct", type=float, default=-0.8)
    p.set_defaults(func=sidecar_c_time_scan)

    p = sub.add_parser("sweep-v3-thresholds")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.set_defaults(func=sweep_v3_thresholds)

    p = sub.add_parser("sweep-time-windows-v3")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.add_argument("--step-minutes", type=int, default=None)
    p.set_defaults(func=sweep_time_windows_v3)

    p = sub.add_parser("compare-entry-mode-v3")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.set_defaults(func=compare_entry_mode_v3)

    p = sub.add_parser("run-small-seed-v3")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.add_argument("--max-daily-entries", type=int, default=1)
    p.add_argument("--strategy-mode", choices=["confirmed", "preopen", "threshold"], default="confirmed")
    p.set_defaults(func=run_small_seed_v3_command)

    p = sub.add_parser("build-small-seed-report")
    p.add_argument("--start-date", default="2026-01-01")
    p.add_argument("--end-date", default=date.today().isoformat())
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.set_defaults(func=build_small_seed_report)

    p = sub.add_parser("sweep-fear-divergence-v4")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.add_argument("--timeframe", default="5m", choices=["1m", "5m"])
    p.set_defaults(func=sweep_fear_divergence_v4)

    p = sub.add_parser("run-fear-divergence-v4")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.add_argument("--timeframe", default="5m", choices=["1m", "5m"])
    p.set_defaults(func=run_fear_divergence_v4_command)

    p = sub.add_parser("compare-v3-v4")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.set_defaults(func=compare_v3_v4_command)

    p = sub.add_parser("build-fear-divergence-report")
    p.add_argument("--start-date", default="2026-01-01")
    p.add_argument("--end-date", default=date.today().isoformat())
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.set_defaults(func=build_fear_divergence_report)

    p = sub.add_parser("sweep-fear-exhaustion-v41")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.add_argument("--timeframes", default="1m,5m")
    p.set_defaults(func=sweep_fear_exhaustion_v41)

    p = sub.add_parser("run-fear-exhaustion-v41")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.add_argument("--timeframe", default="1m", choices=["1m", "5m"])
    p.set_defaults(func=run_fear_exhaustion_v41_command)

    p = sub.add_parser("build-fear-exhaustion-funnel-v41")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--timeframes", default="1m,5m")
    p.set_defaults(func=build_fear_exhaustion_funnel_v41_command)

    p = sub.add_parser("compare-v4-v41")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.set_defaults(func=compare_v4_v41_command)

    p = sub.add_parser("build-fear-exhaustion-v41-report")
    p.add_argument("--start-date", default="2026-01-01")
    p.add_argument("--end-date", default=date.today().isoformat())
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.set_defaults(func=build_fear_exhaustion_v41_report)

    p = sub.add_parser("sweep-structure-reversal-v5")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.set_defaults(func=sweep_structure_reversal_v5)

    p = sub.add_parser("run-structure-reversal-v5")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.add_argument("--mode", choices=["small_seed_daily", "weekly_sniper"], default="small_seed_daily")
    p.set_defaults(func=run_structure_reversal_v5_command)

    p = sub.add_parser("run-weekly-sniper-v5")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.set_defaults(func=run_weekly_sniper_v5_command)

    p = sub.add_parser("compare-mtf-context-v5")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.set_defaults(func=compare_mtf_context_v5_command)

    p = sub.add_parser("compare-all-strategies-v5")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.set_defaults(func=compare_all_strategies_v5_command)

    p = sub.add_parser("build-structure-reversal-v5-report")
    p.add_argument("--start-date", default="2026-01-01")
    p.add_argument("--end-date", default=date.today().isoformat())
    p.add_argument("--capital-krw", type=float, default=500000)
    p.add_argument("--order-krw", type=float, default=10000)
    p.set_defaults(func=build_structure_reversal_v5_report)

    p = sub.add_parser("run-fractal-v52")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--initial-equity-krw", type=float, default=500000)
    p.add_argument("--max-daily-entries", type=int, default=1)
    p.add_argument("--allocation-model", choices=["fixed_10k", "full_seed", "grade_based"], default="grade_based")
    p.add_argument("--exit-model", choices=["target_zone_full_exit", "partial_tp_runner", "conservative_partial", "trailing_runner"], default="partial_tp_runner")
    p.set_defaults(func=run_fractal_v52_command)

    p = sub.add_parser("sweep-fractal-v52")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--initial-equity-krw", type=float, default=500000)
    p.set_defaults(func=sweep_fractal_v52_command)

    p = sub.add_parser("validate-zone-engine-v52")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.set_defaults(func=validate_zone_engine_v52_command)

    p = sub.add_parser("walk-forward-fractal-v52")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--initial-equity-krw", type=float, default=500000)
    p.set_defaults(func=walk_forward_fractal_v52_command)

    p = sub.add_parser("compare-full-seed-v52")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--initial-equity-krw", type=float, default=500000)
    p.set_defaults(func=compare_full_seed_v52_command)

    p = sub.add_parser("build-fractal-v52-report")
    p.add_argument("--start-date", default="2026-01-01")
    p.add_argument("--end-date", default=date.today().isoformat())
    p.add_argument("--initial-equity-krw", type=float, default=500000)
    p.set_defaults(func=build_fractal_v52_report)

    p = sub.add_parser("run-fractal-v53")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--initial-equity-krw", type=float, default=500000)
    p.add_argument("--max-daily-entries", type=int, default=1)
    p.add_argument("--allocation-model", choices=["fixed_10k", "full_seed", "grade_based_v53"], default="grade_based_v53")
    p.add_argument("--exit-model", choices=["runner_sweep_best", "no_runner", "partial_tp_runner"], default="runner_sweep_best")
    p.add_argument("--btc-dominance-path")
    p.add_argument("--use-cache", default="true")
    p.set_defaults(func=run_fractal_v53_command)

    p = sub.add_parser("diagnose-allocation-v53")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--initial-equity-krw", type=float, default=500000)
    p.set_defaults(func=diagnose_allocation_v53_command)

    p = sub.add_parser("validate-zone-reaction-v53")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.set_defaults(func=validate_zone_reaction_v53_command)

    p = sub.add_parser("sweep-runner-exit-v53")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--initial-equity-krw", type=float, default=500000)
    p.set_defaults(func=sweep_runner_exit_v53_command)

    p = sub.add_parser("walk-forward-fractal-v53")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.add_argument("--initial-equity-krw", type=float, default=500000)
    p.add_argument("--use-cache", default="true")
    p.set_defaults(func=walk_forward_fractal_v53_command)

    p = sub.add_parser("benchmark-cache-v53")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=30)
    p.set_defaults(func=benchmark_cache_v53_command)

    p = sub.add_parser("build-fractal-v53-report")
    p.add_argument("--start-date", default="2026-01-01")
    p.add_argument("--end-date", default=date.today().isoformat())
    p.add_argument("--initial-equity-krw", type=float, default=500000)
    p.set_defaults(func=build_fractal_v53_report)

    p = sub.add_parser("run-edge-isolation-v54")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--fixed-order-krw", type=float, default=10000)
    p.set_defaults(func=run_edge_isolation_v54_command)

    p = sub.add_parser("compare-exit-models-v54")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--fixed-order-krw", type=float, default=10000)
    p.set_defaults(func=compare_exit_models_v54_command)

    p = sub.add_parser("ablate-modules-v54")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--fixed-order-krw", type=float, default=10000)
    p.set_defaults(func=ablate_modules_v54_command)

    p = sub.add_parser("research-zone-quality-v54")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.set_defaults(func=research_zone_quality_v54_command)

    p = sub.add_parser("export-trade-review-v54")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=50)
    p.set_defaults(func=export_trade_review_v54_command)

    p = sub.add_parser("build-edge-isolation-v54-report")
    p.add_argument("--start-date", default="2026-01-01")
    p.add_argument("--end-date", default=date.today().isoformat())
    p.set_defaults(func=build_edge_isolation_v54_report)

    p = sub.add_parser("collect-second-candles")
    p.add_argument("--markets", required=True)
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--count-per-request", type=int, default=200)
    p.set_defaults(func=collect_second_candles_command)

    p = sub.add_parser("replay-second-candles")
    p.add_argument("--market", required=True)
    p.add_argument("--start-time", required=True)
    p.add_argument("--end-time", required=True)
    p.set_defaults(func=replay_second_candles_command)

    p = sub.add_parser("run-micro-execution-replay")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=30)
    p.add_argument("--fixed-order-krw", type=float, default=10000)
    p.add_argument("--max-hold-seconds", type=int, default=120)
    p.set_defaults(func=run_micro_execution_replay_command)

    p = sub.add_parser("validate-micro-entry-timing")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=30)
    p.add_argument("--fixed-order-krw", type=float, default=10000)
    p.set_defaults(func=validate_micro_entry_timing_command)

    p = sub.add_parser("validate-micro-exit")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=30)
    p.add_argument("--fixed-order-krw", type=float, default=10000)
    p.set_defaults(func=validate_micro_exit_command)

    p = sub.add_parser("simulate-latency-slippage")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=30)
    p.add_argument("--fixed-order-krw", type=float, default=10000)
    p.set_defaults(func=simulate_latency_slippage_command)

    p = sub.add_parser("build-micro-execution-html-report")
    p.add_argument("--start-date", default="2026-04-01")
    p.add_argument("--end-date", default="2026-05-15")
    p.set_defaults(func=build_micro_execution_html_report_command)

    p = sub.add_parser("run-live-micro-session")
    p.add_argument("--duration-minutes", type=int, default=60)
    p.add_argument("--top-markets", type=int, default=20)
    p.add_argument("--fixed-order-krw", type=float, default=10000)
    p.add_argument("--mode", default="record_and_forward_paper")
    p.set_defaults(func=run_live_micro_session_command)

    p = sub.add_parser("record-live-micro-data")
    p.add_argument("--duration-minutes", type=int, default=60)
    p.add_argument("--markets", required=True)
    p.add_argument("--output", default="replay_store/raw/live_micro")
    p.set_defaults(func=record_live_micro_data_command)

    p = sub.add_parser("replay-forward-micro-session")
    p.add_argument("--session-id", required=True)
    p.set_defaults(func=replay_forward_micro_session_command)

    p = sub.add_parser("validate-forward-micro-sessions")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions" / "live_micro"))
    p.add_argument("--min-quality", default="PARTIAL")
    p.set_defaults(func=validate_forward_micro_sessions_command)

    p = sub.add_parser("audit-micro-data-quality")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions" / "live_micro"))
    p.set_defaults(func=audit_micro_data_quality_command)

    p = sub.add_parser("test-micro-cost-survival")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions" / "live_micro"))
    p.add_argument("--min-quality", default="PARTIAL")
    p.set_defaults(func=test_micro_cost_survival_command)

    p = sub.add_parser("validate-micro-entry-exit-effectiveness")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions" / "live_micro"))
    p.add_argument("--min-quality", default="PARTIAL")
    p.set_defaults(func=validate_micro_entry_exit_effectiveness_command)

    p = sub.add_parser("build-forward-micro-html-report")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions" / "live_micro"))
    p.set_defaults(func=build_forward_micro_html_report_command)

    p = sub.add_parser("run-upbit-ws-smoke-test")
    p.add_argument("--markets", required=True)
    p.add_argument("--duration-seconds", type=int, default=300)
    p.set_defaults(func=run_upbit_ws_smoke_test_command)

    p = sub.add_parser("run-upbit-real-ws-session")
    p.add_argument("--markets", required=True)
    p.add_argument("--duration-seconds", type=int, default=900)
    p.add_argument("--include-trade", default="true")
    p.add_argument("--include-orderbook", default="true")
    p.set_defaults(func=run_upbit_real_ws_session_command)

    p = sub.add_parser("fetch-candidate-second-window")
    p.add_argument("--market", required=True)
    p.add_argument("--candidate-time", required=True)
    p.add_argument("--pre-seconds", type=int, default=120)
    p.add_argument("--post-seconds", type=int, default=180)
    p.set_defaults(func=fetch_candidate_second_window_command)

    p = sub.add_parser("validate-candidate-second-windows")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=30)
    p.add_argument("--pre-seconds", type=int, default=120)
    p.add_argument("--post-seconds", type=int, default=180)
    p.add_argument("--max-candidates", type=int, default=50)
    p.add_argument("--fixed-order-krw", type=float, default=10000)
    p.set_defaults(func=validate_candidate_second_windows_command)

    p = sub.add_parser("validate-candidate-second-windows-v553")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=30)
    p.add_argument("--pre-seconds", type=int, default=120)
    p.add_argument("--post-seconds", type=int, default=180)
    p.add_argument("--max-candidates", type=int, default=50)
    p.add_argument("--fixed-order-krw", type=float, default=10000)
    p.set_defaults(func=validate_candidate_second_windows_v553_command)

    p = sub.add_parser("validate-micro-candidate-filter-v553")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=30)
    p.add_argument("--max-candidates", type=int, default=50)
    p.set_defaults(func=validate_micro_candidate_filter_v553_command)

    p = sub.add_parser("build-external-strategy-registry")
    p.set_defaults(func=build_external_strategy_registry_command)

    p = sub.add_parser("run-external-strategy-lab")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=30)
    p.add_argument("--fixed-order-krw", type=float, default=10000)
    p.add_argument("--cost-scenario", default="realistic_1")
    p.set_defaults(func=run_external_strategy_lab_command)

    p = sub.add_parser("build-open-strategy-report")
    p.set_defaults(func=build_open_strategy_report_command)

    p = sub.add_parser("diagnose-micro-entry-gates-v554")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=30)
    p.add_argument("--max-candidates", type=int, default=50)
    p.set_defaults(func=diagnose_micro_entry_gates_v554_command)

    p = sub.add_parser("abtest-micro-entry-gates-v554")
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--top-markets", type=int, default=30)
    p.add_argument("--max-candidates", type=int, default=50)
    p.set_defaults(func=abtest_micro_entry_gates_v554_command)

    p = sub.add_parser("run-forward-ws-accumulation-v554")
    p.add_argument("--duration-minutes", type=int, default=60)
    p.add_argument("--top-markets", type=int, default=20)
    p.add_argument("--priority-strategies", default="VWAP_PULLBACK,EMA_PULLBACK,ORDERBOOK_IMBALANCE")
    p.add_argument("--fixed-order-krw", type=float, default=10000)
    p.set_defaults(func=run_forward_ws_accumulation_v554_command)

    p = sub.add_parser("validate-priority-external-strategies-ws-v554")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions" / "forward_ws_v554"))
    p.set_defaults(func=validate_priority_external_strategies_ws_v554_command)

    p = sub.add_parser("build-micro-entry-diagnostics-report-v554")
    p.set_defaults(func=build_micro_entry_diagnostics_report_v554_command)

    p = sub.add_parser("run-realistic-paper-session-v555")
    p.add_argument("--duration-minutes", type=int, default=60)
    p.add_argument("--top-markets", type=int, default=20)
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--fixed-order-krw", type=float, default=10000)
    p.add_argument("--strategies", default="MICRO_ACCELERATION,VWAP_RECLAIM,EMA_PULLBACK,ORDERBOOK_IMBALANCE")
    p.add_argument("--scenario", default="realistic_1")
    p.set_defaults(func=run_realistic_paper_session_v555_command)

    p = sub.add_parser("validate-realistic-paper-v555")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555"))
    p.set_defaults(func=validate_realistic_paper_v555_command)

    p = sub.add_parser("compare-micro-candidate-sources-v555")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555"))
    p.set_defaults(func=compare_micro_candidate_sources_v555_command)

    p = sub.add_parser("test-micro-cost-survival-v555")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555"))
    p.set_defaults(func=test_micro_cost_survival_v555_command)

    p = sub.add_parser("build-realistic-paper-report-v555")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555"))
    p.set_defaults(func=build_realistic_paper_report_v555_command)

    p = sub.add_parser("analyze-wait-path-v556")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555"))
    p.set_defaults(func=analyze_wait_path_v556_command)

    p = sub.add_parser("run-hold-time-sweep-v556")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555"))
    p.add_argument("--hold-seconds", default="60,120,180,300,600")
    p.set_defaults(func=run_hold_time_sweep_v556_command)

    p = sub.add_parser("run-entry-discovery-v556")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555"))
    p.add_argument("--profiles", default="STRICT,BALANCED,ENTRY_DISCOVERY,DIAGNOSTIC_ONLY")
    p.set_defaults(func=run_entry_discovery_v556_command)

    p = sub.add_parser("run-head-controller-draft-v556")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="off", choices=["off", "auto", "openai", "gemini"])
    p.add_argument("--key-file", default=None)
    p.set_defaults(func=run_head_controller_draft_v556_command)

    p = sub.add_parser("build-entry-discovery-report-v556")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555"))
    p.set_defaults(func=build_entry_discovery_report_v556_command)

    p = sub.add_parser("build-head-controller-report-v556")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="off", choices=["off", "auto", "openai", "gemini"])
    p.add_argument("--key-file", default=None)
    p.set_defaults(func=build_head_controller_report_v556_command)

    p = sub.add_parser("check-head-controller-llm-config")
    p.add_argument("--llm-provider", default="auto", choices=["off", "auto", "openai", "gemini"])
    p.add_argument("--key-file", default=None)
    p.set_defaults(func=check_head_controller_llm_config_command)

    p = sub.add_parser("check-artifact-integrity-v5561")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=check_artifact_integrity_v5561_command)

    p = sub.add_parser("scan-report-secrets-v5561")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=scan_report_secrets_v5561_command)

    p = sub.add_parser("regenerate-v556-production-reports-v5561")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555"))
    p.set_defaults(func=regenerate_v556_production_reports_v5561_command)

    p = sub.add_parser("run-head-controller-llm-smoke-v5561")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="auto", choices=["off", "auto", "openai", "gemini"])
    p.add_argument("--key-file", default=None)
    p.set_defaults(func=run_head_controller_llm_smoke_v5561_command)

    p = sub.add_parser("run-head-controller-llm-guard-v5561")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="auto", choices=["off", "auto", "openai", "gemini"])
    p.add_argument("--key-file", default=None)
    p.set_defaults(func=run_head_controller_llm_guard_v5561_command)

    p = sub.add_parser("build-head-controller-llm-guard-report-v5561")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="auto", choices=["off", "auto", "openai", "gemini"])
    p.add_argument("--key-file", default=None)
    p.set_defaults(func=build_head_controller_llm_guard_report_v5561_command)

    p = sub.add_parser("run-head-controller-openai-live-smoke-v5562")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai", choices=["openai"])
    p.add_argument("--key-file", default=None)
    p.set_defaults(func=run_head_controller_openai_live_smoke_v5562_command)

    p = sub.add_parser("test-head-controller-unsafe-prompt-v5562")
    p.add_argument("--llm-provider", default="openai", choices=["openai", "gemini", "off"])
    p.set_defaults(func=test_head_controller_unsafe_prompt_v5562_command)

    p = sub.add_parser("build-head-controller-openai-live-report-v5562")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai", choices=["openai"])
    p.add_argument("--key-file", default=None)
    p.set_defaults(func=build_head_controller_openai_live_report_v5562_command)

    p = sub.add_parser("run-full-seed-paper-session-v557")
    p.add_argument("--duration-minutes", type=int, default=60)
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--sizing-mode", default="FULL_SEED_LADDER")
    p.add_argument("--strategies", default="MICRO_ACCELERATION,VWAP_RECLAIM,EMA_PULLBACK,ORDERBOOK_IMBALANCE")
    p.add_argument("--scenario", default="realistic_1")
    p.add_argument("--research-mode", default="true")
    p.set_defaults(func=run_full_seed_paper_session_v557_command)

    p = sub.add_parser("compare-sizing-modes-v557")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555"))
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.set_defaults(func=compare_sizing_modes_v557_command)

    p = sub.add_parser("validate-ladder-entry-exit-v557")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555"))
    p.set_defaults(func=validate_ladder_entry_exit_v557_command)

    p = sub.add_parser("run-head-controller-evaluation-v557")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai", choices=["off", "auto", "openai", "gemini"])
    p.set_defaults(func=run_head_controller_evaluation_v557_command)

    p = sub.add_parser("build-full-seed-allocator-report-v557")
    p.set_defaults(func=build_full_seed_allocator_report_v557_command)

    p = sub.add_parser("build-head-controller-evaluation-report-v557")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai", choices=["off", "auto", "openai", "gemini"])
    p.set_defaults(func=build_head_controller_evaluation_report_v557_command)

    p = sub.add_parser("detect-winner-events-v558")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions"))
    p.add_argument("--winner-types", default="MICRO_WINNER,SCALP_WINNER,MOMENTUM_WINNER,SPIKE_WINNER")
    p.set_defaults(func=detect_winner_events_v558_command)

    p = sub.add_parser("extract-winner-traces-v558")
    p.add_argument("--winner-events", default=str(REPLAY_STORE_DIR / "winner_mining" / "events"))
    p.add_argument("--trace-windows", default="10,30,60,180,300")
    p.set_defaults(func=extract_winner_traces_v558_command)

    p = sub.add_parser("analyze-winner-capture-rate-v558")
    p.add_argument("--winner-traces", default=str(REPLAY_STORE_DIR / "winner_mining" / "traces"))
    p.add_argument("--candidate-sources", default="MICRO_ACCELERATION,VWAP_RECLAIM,EMA_PULLBACK,ORDERBOOK_IMBALANCE")
    p.set_defaults(func=analyze_winner_capture_rate_v558_command)

    p = sub.add_parser("analyze-missed-winners-v558")
    p.add_argument("--winner-traces", default=str(REPLAY_STORE_DIR / "winner_mining" / "traces"))
    p.set_defaults(func=analyze_missed_winners_v558_command)

    p = sub.add_parser("mine-winner-patterns-v558")
    p.add_argument("--winner-traces", default=str(REPLAY_STORE_DIR / "winner_mining" / "traces"))
    p.set_defaults(func=mine_winner_patterns_v558_command)

    p = sub.add_parser("validate-redesigned-candidate-sources-v558")
    p.add_argument("--winner-traces", default=str(REPLAY_STORE_DIR / "winner_mining" / "traces"))
    p.set_defaults(func=validate_redesigned_candidate_sources_v558_command)

    p = sub.add_parser("validate-full-seed-winner-candidates-v558")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.set_defaults(func=validate_full_seed_winner_candidates_v558_command)

    p = sub.add_parser("run-head-controller-winner-review-v558")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai", choices=["off", "auto", "openai", "gemini"])
    p.set_defaults(func=run_head_controller_winner_review_v558_command)

    p = sub.add_parser("build-winner-trace-report-v558")
    p.set_defaults(func=build_winner_trace_report_v558_command)

    p = sub.add_parser("build-candidate-source-redesign-report-v558")
    p.set_defaults(func=build_candidate_source_redesign_report_v558_command)

    p = sub.add_parser("build-head-controller-winner-review-report-v558")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai", choices=["off", "auto", "openai", "gemini"])
    p.set_defaults(func=build_head_controller_winner_review_report_v558_command)

    p = sub.add_parser("filter-winner-quality-v559")
    p.add_argument("--winner-traces", default=str(REPLAY_STORE_DIR / "winner_mining" / "traces"))
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.set_defaults(func=filter_winner_quality_v559_command)

    p = sub.add_parser("sample-non-winners-v559")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions"))
    p.add_argument("--sample-ratio", type=float, default=2.0)
    p.set_defaults(func=sample_non_winners_v559_command)

    p = sub.add_parser("analyze-false-positives-v559")
    p.add_argument("--quality-winners", default=str(REPLAY_STORE_DIR / "winner_quality"))
    p.add_argument("--non-winners", default=str(REPLAY_STORE_DIR / "non_winner_samples"))
    p.add_argument("--sources", default="ORDERFLOW_SURGE,VOLUME_RANGE_BREAKOUT,RANGE_COMPRESSION_EXPANSION")
    p.set_defaults(func=analyze_false_positives_v559_command)

    p = sub.add_parser("analyze-source-discriminative-power-v559")
    p.add_argument("--quality-winners", default=str(REPLAY_STORE_DIR / "winner_quality"))
    p.add_argument("--non-winners", default=str(REPLAY_STORE_DIR / "non_winner_samples"))
    p.set_defaults(func=analyze_source_discriminative_power_v559_command)

    p = sub.add_parser("validate-refined-sources-v559")
    p.add_argument("--quality-winners", default=str(REPLAY_STORE_DIR / "winner_quality"))
    p.add_argument("--non-winners", default=str(REPLAY_STORE_DIR / "non_winner_samples"))
    p.set_defaults(func=validate_refined_sources_v559_command)

    p = sub.add_parser("verify-post-mfe-calculation-v559")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=verify_post_mfe_calculation_v559_command)

    p = sub.add_parser("run-redesigned-source-forward-test-v559")
    p.add_argument("--duration-minutes", type=int, default=15)
    p.add_argument("--top-markets", type=int, default=20)
    p.add_argument("--sources", default="ORDERFLOW_SURGE_REFINED,VOLUME_RANGE_BREAKOUT_REFINED,RANGE_COMPRESSION_EXPANSION_REFINED")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--scenario", default="realistic_1")
    p.add_argument("--research-mode", default="true")
    p.set_defaults(func=run_redesigned_source_forward_test_v559_command)

    p = sub.add_parser("validate-full-seed-refined-sources-v559")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.set_defaults(func=validate_full_seed_refined_sources_v559_command)

    p = sub.add_parser("run-head-controller-false-positive-review-v559")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai", choices=["off", "auto", "openai", "gemini"])
    p.set_defaults(func=run_head_controller_false_positive_review_v559_command)

    p = sub.add_parser("build-winner-quality-filter-report-v559")
    p.set_defaults(func=build_winner_quality_filter_report_v559_command)

    p = sub.add_parser("build-false-positive-control-report-v559")
    p.set_defaults(func=build_false_positive_control_report_v559_command)

    p = sub.add_parser("build-redesigned-source-forward-report-v559")
    p.set_defaults(func=build_redesigned_source_forward_report_v559_command)

    p = sub.add_parser("build-head-controller-false-positive-review-report-v559")
    p.set_defaults(func=build_head_controller_false_positive_review_report_v559_command)

    p = sub.add_parser("mine-tradable-winners-v5510")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions"))
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--winner-types", default="TRADABLE_SCALP_WINNER,TRADABLE_MOMENTUM_WINNER,TRADABLE_SPIKE_WINNER")
    p.set_defaults(func=mine_tradable_winners_v5510_command)

    p = sub.add_parser("extract-tradable-traces-v5510")
    p.add_argument("--winner-dir", default=str(REPLAY_STORE_DIR / "tradable_winner"))
    p.add_argument("--trace-windows", default="30,60,180,300,600")
    p.set_defaults(func=extract_tradable_traces_v5510_command)

    p = sub.add_parser("collect-high-vol-live-session-v5510")
    p.add_argument("--session-type", default="RANDOM_CONTROL")
    p.add_argument("--duration-minutes", type=int, default=30)
    p.add_argument("--top-markets", type=int, default=20)
    p.set_defaults(func=collect_high_vol_live_session_v5510_command)

    p = sub.add_parser("design-tradable-candidate-sources-v5510")
    p.add_argument("--tradable-traces", default=str(REPLAY_STORE_DIR / "tradable_trace"))
    p.set_defaults(func=design_tradable_candidate_sources_v5510_command)

    p = sub.add_parser("validate-tradable-source-recorded-v5510")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions"))
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.set_defaults(func=validate_tradable_source_recorded_v5510_command)

    p = sub.add_parser("run-tradable-source-live-smoke-v5510")
    p.add_argument("--duration-minutes", type=int, default=15)
    p.add_argument("--top-markets", type=int, default=20)
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--research-mode", default="true")
    p.set_defaults(func=run_tradable_source_live_smoke_v5510_command)

    p = sub.add_parser("run-tradable-source-live-forward-v5510")
    p.add_argument("--duration-minutes", type=int, default=60)
    p.add_argument("--top-markets", type=int, default=30)
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--research-mode", default="true")
    p.set_defaults(func=run_tradable_source_live_forward_v5510_command)

    p = sub.add_parser("validate-full-seed-tradable-sources-v5510")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.set_defaults(func=validate_full_seed_tradable_sources_v5510_command)

    p = sub.add_parser("run-head-controller-tradable-winner-review-v5510")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai", choices=["off", "auto", "openai", "gemini"])
    p.set_defaults(func=run_head_controller_tradable_winner_review_v5510_command)

    p = sub.add_parser("build-tradable-winner-mining-report-v5510")
    p.set_defaults(func=build_tradable_winner_mining_report_v5510_command)

    p = sub.add_parser("build-high-volatility-session-report-v5510")
    p.set_defaults(func=build_high_volatility_session_report_v5510_command)

    p = sub.add_parser("build-tradable-source-forward-report-v5510")
    p.set_defaults(func=build_tradable_source_forward_report_v5510_command)

    p = sub.add_parser("build-head-controller-tradable-winner-review-report-v5510")
    p.set_defaults(func=build_head_controller_tradable_winner_review_report_v5510_command)

    p = sub.add_parser("run-timing-lab-live-v5r1")
    p.add_argument("--duration-minutes", type=int, default=60)
    p.add_argument("--top-markets", type=int, default=30)
    p.add_argument("--buffer-minutes", type=int, default=30)
    p.add_argument("--post-event-minutes", type=int, default=30)
    p.add_argument("--research-mode", default="true")
    p.set_defaults(func=run_timing_lab_live_v5r1_command)

    p = sub.add_parser("replay-timing-lab-v5r1")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions"))
    p.add_argument("--buffer-minutes", type=int, default=30)
    p.add_argument("--post-event-minutes", type=int, default=30)
    p.set_defaults(func=replay_timing_lab_v5r1_command)

    p = sub.add_parser("label-event-clips-v5r1")
    p.add_argument("--clips-dir", default=str(REPLAY_STORE_DIR / "timing_clips"))
    p.set_defaults(func=label_event_clips_v5r1_command)

    p = sub.add_parser("analyze-entry-windows-v5r1")
    p.add_argument("--clips-dir", default=str(REPLAY_STORE_DIR / "timing_clips"))
    p.set_defaults(func=analyze_entry_windows_v5r1_command)

    p = sub.add_parser("validate-entry-state-machine-v5r1")
    p.add_argument("--clips-dir", default=str(REPLAY_STORE_DIR / "timing_clips"))
    p.set_defaults(func=validate_entry_state_machine_v5r1_command)

    p = sub.add_parser("run-timing-based-paper-v5r1")
    p.add_argument("--clips-dir", default=str(REPLAY_STORE_DIR / "timing_clips"))
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--research-mode", default="true")
    p.set_defaults(func=run_timing_based_paper_v5r1_command)

    p = sub.add_parser("audit-llm-usage-v5r1")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=audit_llm_usage_v5r1_command)

    p = sub.add_parser("run-head-controller-timing-review-v5r1")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai", choices=["off", "auto", "openai", "gemini"])
    p.set_defaults(func=run_head_controller_timing_review_v5r1_command)

    p = sub.add_parser("build-timing-lab-report-v5r1")
    p.set_defaults(func=build_timing_lab_report_v5r1_command)

    p = sub.add_parser("build-entry-timing-report-v5r1")
    p.set_defaults(func=build_entry_timing_report_v5r1_command)

    p = sub.add_parser("build-llm-usage-report-v5r1")
    p.set_defaults(func=build_llm_usage_report_v5r1_command)

    p = sub.add_parser("build-head-controller-timing-review-report-v5r1")
    p.set_defaults(func=build_head_controller_timing_review_report_v5r1_command)

    p = sub.add_parser("decompose-fake-signals-v5r2")
    p.add_argument("--clips-dir", default=str(REPLAY_STORE_DIR / "timing_clips"))
    p.set_defaults(func=decompose_fake_signals_v5r2_command)

    p = sub.add_parser("analyze-follow-through-failures-v5r2")
    p.add_argument("--clips-dir", default=str(REPLAY_STORE_DIR / "timing_clips"))
    p.set_defaults(func=analyze_follow_through_failures_v5r2_command)

    p = sub.add_parser("score-event-types-v5r2")
    p.add_argument("--clips-dir", default=str(REPLAY_STORE_DIR / "timing_clips"))
    p.set_defaults(func=score_event_types_v5r2_command)

    p = sub.add_parser("analyze-detector-gaps-v5r2")
    p.add_argument("--clips-dir", default=str(REPLAY_STORE_DIR / "timing_clips"))
    p.set_defaults(func=analyze_detector_gaps_v5r2_command)

    p = sub.add_parser("calibrate-armed-state-v5r2")
    p.add_argument("--clips-dir", default=str(REPLAY_STORE_DIR / "timing_clips"))
    p.set_defaults(func=calibrate_armed_state_v5r2_command)

    p = sub.add_parser("calibrate-confirmation-v5r2")
    p.add_argument("--clips-dir", default=str(REPLAY_STORE_DIR / "timing_clips"))
    p.set_defaults(func=calibrate_confirmation_v5r2_command)

    p = sub.add_parser("run-calibration-grid-v5r2")
    p.add_argument("--clips-dir", default=str(REPLAY_STORE_DIR / "timing_clips"))
    p.set_defaults(func=run_calibration_grid_v5r2_command)

    p = sub.add_parser("run-llm-minimum-completion-test-v5r2")
    p.add_argument("--llm-provider", default="openai", choices=["openai", "off"])
    p.set_defaults(func=run_llm_minimum_completion_test_v5r2_command)

    p = sub.add_parser("repair-llm-completion-v5r2")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai", choices=["openai", "off"])
    p.set_defaults(func=repair_llm_completion_v5r2_command)

    p = sub.add_parser("build-project-scorecard-v5r2")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_project_scorecard_v5r2_command)

    p = sub.add_parser("run-head-controller-v5r2-review")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai", choices=["off", "auto", "openai", "gemini"])
    p.set_defaults(func=run_head_controller_v5r2_review_command)

    p = sub.add_parser("build-fake-signal-decomposition-report-v5r2")
    p.set_defaults(func=build_fake_signal_decomposition_report_v5r2_command)

    p = sub.add_parser("build-confirmation-calibration-report-v5r2")
    p.set_defaults(func=build_confirmation_calibration_report_v5r2_command)

    p = sub.add_parser("build-llm-completion-repair-report-v5r2")
    p.set_defaults(func=build_llm_completion_repair_report_v5r2_command)

    p = sub.add_parser("build-project-scorecard-report-v5r2")
    p.set_defaults(func=build_project_scorecard_report_v5r2_command)

    p = sub.add_parser("build-head-controller-v5r2-review-report")
    p.set_defaults(func=build_head_controller_v5r2_review_report_command)

    p = sub.add_parser("build-market-regime-v5r3")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions"))
    p.set_defaults(func=build_market_regime_v5r3_command)

    p = sub.add_parser("build-setup-candidates-v5r3")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions"))
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.set_defaults(func=build_setup_candidates_v5r3_command)

    p = sub.add_parser("build-scenarios-v5r3")
    p.set_defaults(func=build_scenarios_v5r3_command)

    p = sub.add_parser("run-scenario-replay-v5r3")
    p.add_argument("--scenario-set", default=str(REPLAY_STORE_DIR / "scenarios"))
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--risk-profile", default="aggressive", choices=["aggressive"])
    p.set_defaults(func=run_scenario_replay_v5r3_command)

    p = sub.add_parser("run-aggressive-paper-learning-v5r3")
    p.add_argument("--duration-minutes", type=int, default=60)
    p.add_argument("--top-markets", type=int, default=30)
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--risk-profile", default="aggressive", choices=["aggressive"])
    p.add_argument("--research-mode", default="true")
    p.set_defaults(func=run_aggressive_paper_learning_v5r3_command)

    p = sub.add_parser("run-llm-strategy-review-v5r3")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai", choices=["off", "auto", "openai", "gemini"])
    p.set_defaults(func=run_llm_strategy_review_v5r3_command)

    p = sub.add_parser("build-v5r3-strategy-learning-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v5r3_strategy_learning_report_command)

    p = sub.add_parser("collect-v6-ohlcv")
    p.add_argument("--markets", default="TOP_KRW_50")
    p.add_argument("--months", type=int, default=12)
    p.add_argument("--timeframes", default="1w,1d,4h,1h,15m,5m,1m")
    p.set_defaults(func=collect_v6_ohlcv_command)

    p = sub.add_parser("build-v6-mtf-context")
    p.add_argument("--markets", default="TOP_KRW_50")
    p.set_defaults(func=build_v6_mtf_context_command)

    p = sub.add_parser("run-v6-daddy-backtest")
    p.add_argument("--months", type=int, default=12)
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--paper-entry-policy", default="ACTIVE_RESEARCH", choices=["ACTIVE_RESEARCH"])
    p.set_defaults(func=run_v6_daddy_backtest_command)

    p = sub.add_parser("run-v6-ict-backtest")
    p.add_argument("--months", type=int, default=12)
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--paper-entry-policy", default="ACTIVE_RESEARCH", choices=["ACTIVE_RESEARCH"])
    p.set_defaults(func=run_v6_ict_backtest_command)

    p = sub.add_parser("run-v6-combined-backtest")
    p.add_argument("--months", type=int, default=12)
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--paper-entry-policy", default="ACTIVE_RESEARCH", choices=["ACTIVE_RESEARCH"])
    p.set_defaults(func=run_v6_combined_backtest_command)

    p = sub.add_parser("run-v6-weekly-paper-simulation")
    p.add_argument("--months", type=int, default=12)
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--paper-entry-policy", default="ACTIVE_RESEARCH", choices=["ACTIVE_RESEARCH"])
    p.set_defaults(func=run_v6_weekly_paper_simulation_command)

    p = sub.add_parser("run-head-controller-v6-review")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai", choices=["off", "auto", "openai", "gemini"])
    p.set_defaults(func=run_head_controller_v6_review_command)

    p = sub.add_parser("build-v6-mtf-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v6_mtf_report_command)

    p = sub.add_parser("build-v6-daddy-strategy-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v6_daddy_strategy_report_command)

    p = sub.add_parser("build-v6-ict-strategy-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v6_ict_strategy_report_command)

    p = sub.add_parser("build-v6-combined-strategy-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v6_combined_strategy_report_command)

    p = sub.add_parser("build-v6-weekly-performance-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v6_weekly_performance_report_command)

    p = sub.add_parser("build-head-controller-v6-review-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_head_controller_v6_review_report_command)

    p = sub.add_parser("collect-v61-long-ohlcv")
    p.add_argument("--markets", default="TOP_KRW_100")
    p.add_argument("--months", type=int, default=36)
    p.add_argument("--timeframes", default="1w,1d,4h,1h,15m,5m,1m")
    p.set_defaults(func=collect_v61_long_ohlcv_command)

    p = sub.add_parser("build-v61-coverage-report")
    p.add_argument("--data-dir", default="replay_store/v6_ohlcv")
    p.set_defaults(func=build_v61_coverage_report_command)

    p = sub.add_parser("run-v61-strategy-robustness-backtest")
    p.add_argument("--months", type=int, default=36)
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--paper-entry-policy", default="ACTIVE_RESEARCH", choices=["ACTIVE_RESEARCH"])
    p.set_defaults(func=run_v61_strategy_robustness_backtest_command)

    p = sub.add_parser("run-v61-regime-backtest")
    p.add_argument("--months", type=int, default=36)
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.set_defaults(func=run_v61_regime_backtest_command)

    p = sub.add_parser("analyze-v61-big-win-dependency")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=analyze_v61_big_win_dependency_command)

    p = sub.add_parser("analyze-v61-failure-success")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=analyze_v61_failure_success_command)

    p = sub.add_parser("run-v61-risk-parameter-sweep")
    p.add_argument("--months", type=int, default=36)
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.set_defaults(func=run_v61_risk_parameter_sweep_command)

    p = sub.add_parser("run-v61-train-test-validation")
    p.add_argument("--months", type=int, default=36)
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.set_defaults(func=run_v61_train_test_validation_command)

    p = sub.add_parser("build-v61-final-strategy-decision")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v61_final_strategy_decision_command)

    p = sub.add_parser("run-head-controller-v61-review")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai", choices=["off", "auto", "openai", "gemini"])
    p.set_defaults(func=run_head_controller_v61_review_command)

    p = sub.add_parser("build-v61-coverage-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v61_coverage_report_html_command)

    p = sub.add_parser("build-v61-strategy-robustness-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v61_strategy_robustness_report_html_command)

    p = sub.add_parser("build-v61-regime-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v61_regime_report_html_command)

    p = sub.add_parser("build-v61-big-win-dependency-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v61_big_win_dependency_report_html_command)

    p = sub.add_parser("build-v61-failure-success-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v61_failure_success_report_html_command)

    p = sub.add_parser("build-v61-risk-sweep-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v61_risk_sweep_report_html_command)

    p = sub.add_parser("build-v61-final-decision-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v61_final_decision_report_html_command)

    p = sub.add_parser("build-head-controller-v61-review-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_head_controller_v61_review_report_html_command)

    p = sub.add_parser("run-v62-capital-growth-backtest")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--compounding", default="true")
    p.add_argument("--use-available-history", default="true")
    p.set_defaults(func=run_v62_capital_growth_backtest_command)

    p = sub.add_parser("validate-v62-strategy-router")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.set_defaults(func=validate_v62_strategy_router_command)

    p = sub.add_parser("run-v62-real-exit-sweep")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.set_defaults(func=run_v62_real_exit_sweep_command)

    p = sub.add_parser("build-v62-investment-reports")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v62_investment_reports_command)

    p = sub.add_parser("run-v62-risk-strengthen-review")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v62_risk_strengthen_review_command)

    p = sub.add_parser("run-head-controller-v62-review")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai", choices=["off", "auto", "openai", "gemini"])
    p.set_defaults(func=run_head_controller_v62_review_command)

    p = sub.add_parser("build-v62-trade-journal-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v62_trade_journal_report_html_command)

    p = sub.add_parser("build-v62-weekly-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v62_weekly_report_html_command)

    p = sub.add_parser("build-v62-monthly-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v62_monthly_report_html_command)

    p = sub.add_parser("build-v62-full-investment-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v62_full_investment_report_html_command)

    p = sub.add_parser("build-v62-strategy-router-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v62_strategy_router_report_html_command)

    p = sub.add_parser("build-v62-risk-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v62_risk_report_html_command)

    p = sub.add_parser("build-head-controller-v62-review-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_head_controller_v62_review_report_html_command)

    p = sub.add_parser("collect-upbit-historical-archive")
    p.add_argument("--markets", default="TOP_KRW_50")
    p.add_argument("--timeframes", default="1d,4h,1h,15m,5m,1m")
    p.add_argument("--max-lookback-days", type=int, default=1460)
    p.add_argument("--archive-dir", default=str(REPLAY_STORE_DIR / "historical_archive"))
    p.set_defaults(func=collect_upbit_historical_archive_command)

    p = sub.add_parser("run-true-walk-forward-paper")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--archive-dir", default=str(REPLAY_STORE_DIR / "historical_archive"))
    p.add_argument("--risk-profile", default="aggressive")
    p.set_defaults(func=run_true_walk_forward_paper_command)

    p = sub.add_parser("build-investor-dashboard")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_investor_dashboard_command)

    p = sub.add_parser("run-drawdown-defense-revalidation")
    p.add_argument("--summary-path", default="docs/reports/latest_true_walk_forward_summary.json")
    p.add_argument("--archive-dir", default=str(REPLAY_STORE_DIR / "historical_archive"))
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.set_defaults(func=run_drawdown_defense_revalidation_command)

    p = sub.add_parser("build-drawdown-defense-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_drawdown_defense_report_html_command)

    p = sub.add_parser("run-v64-causal-defense-rerun")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--use-available-history", default="true")
    p.set_defaults(func=run_v64_causal_defense_rerun_command)

    p = sub.add_parser("run-v64-return-amplification-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--use-available-history", default="true")
    p.set_defaults(func=run_v64_return_amplification_lab_command)

    p = sub.add_parser("build-v64-scenario-comparison")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v64_scenario_comparison_command)

    p = sub.add_parser("run-v64-hindsight-audit")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v64_hindsight_audit_command)

    p = sub.add_parser("build-v64-investor-summary")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v64_investor_summary_command)

    p = sub.add_parser("build-v64-policy-blend-analysis")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v64_policy_blend_analysis_command)

    p = sub.add_parser("build-v64-policy-compounding-analysis")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v64_policy_compounding_analysis_command)

    p = sub.add_parser("run-head-controller-v64-review")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai")
    p.set_defaults(func=run_head_controller_v64_review_command)

    p = sub.add_parser("build-v64-causal-defense-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v64_causal_defense_report_html_command)

    p = sub.add_parser("build-v64-return-amplification-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v64_return_amplification_report_html_command)

    p = sub.add_parser("build-v64-scenario-comparison-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v64_scenario_comparison_report_html_command)

    p = sub.add_parser("build-v64-hindsight-audit-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v64_hindsight_audit_report_html_command)

    p = sub.add_parser("build-v64-investor-summary-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v64_investor_summary_report_html_command)

    p = sub.add_parser("build-head-controller-v64-review-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_head_controller_v64_review_report_html_command)

    p = sub.add_parser("build-v65-ma-features")
    p.add_argument("--use-available-history", default="true")
    p.set_defaults(func=build_v65_ma_features_command)

    p = sub.add_parser("run-v65-ma-scenario-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--use-available-history", default="true")
    p.set_defaults(func=run_v65_ma_scenario_lab_command)

    p = sub.add_parser("run-v65-ma-policy-router-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--use-available-history", default="true")
    p.set_defaults(func=run_v65_ma_policy_router_lab_command)

    p = sub.add_parser("analyze-v65-yearly-weakness-repair")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=analyze_v65_yearly_weakness_repair_command)

    p = sub.add_parser("build-v65-ma-risk-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v65_ma_risk_report_command)

    p = sub.add_parser("run-head-controller-v65-review")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai")
    p.set_defaults(func=run_head_controller_v65_review_command)

    p = sub.add_parser("build-v65-ma-scenario-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v65_ma_scenario_report_html_command)

    p = sub.add_parser("build-v65-ma-policy-router-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v65_ma_policy_router_report_html_command)

    p = sub.add_parser("build-v65-yearly-repair-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v65_yearly_repair_report_html_command)

    p = sub.add_parser("build-v65-ma-risk-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v65_ma_risk_report_html_command)

    p = sub.add_parser("build-head-controller-v65-review-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_head_controller_v65_review_report_html_command)

    p = sub.add_parser("audit-v66-btcd-inclusion")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=audit_v66_btcd_inclusion_command)

    p = sub.add_parser("prepare-v66-btcd-data")
    p.add_argument("--use-available-history", default="true")
    p.set_defaults(func=prepare_v66_btcd_data_command)

    p = sub.add_parser("build-v66-btcd-data-quality-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v66_btcd_data_quality_report_command)

    p = sub.add_parser("run-v66-btcd-rolling-balanced-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--use-available-history", default="true")
    p.set_defaults(func=run_v66_btcd_rolling_balanced_lab_command)

    p = sub.add_parser("run-v66-btcd-bear-regime-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--use-available-history", default="true")
    p.set_defaults(func=run_v66_btcd_bear_regime_lab_command)

    p = sub.add_parser("run-v66-btcd-bear-bounce-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--use-available-history", default="true")
    p.set_defaults(func=run_v66_btcd_bear_bounce_lab_command)

    p = sub.add_parser("run-v66-btcd-short-research-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--use-available-history", default="true")
    p.set_defaults(func=run_v66_btcd_short_research_lab_command)

    p = sub.add_parser("run-v66-btcd-hybrid-router-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--use-available-history", default="true")
    p.set_defaults(func=run_v66_btcd_hybrid_router_lab_command)

    p = sub.add_parser("build-v66-btcd-scenario-comparison")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v66_btcd_scenario_comparison_command)

    p = sub.add_parser("run-head-controller-v66-review")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai")
    p.set_defaults(func=run_head_controller_v66_review_command)

    p = sub.add_parser("build-v66-btcd-inclusion-audit-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v66_btcd_inclusion_audit_report_html_command)

    p = sub.add_parser("build-v66-btcd-data-quality-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v66_btcd_data_quality_report_html_command)

    p = sub.add_parser("build-v66-btcd-rolling-balanced-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v66_btcd_rolling_balanced_report_html_command)

    p = sub.add_parser("build-v66-btcd-bear-scenario-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v66_btcd_bear_scenario_report_html_command)

    p = sub.add_parser("build-v66-btcd-2024-11-focus-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v66_btcd_2024_11_focus_report_html_command)

    p = sub.add_parser("build-v66-btcd-saved-loss-missed-profit-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v66_btcd_saved_loss_missed_profit_report_html_command)

    p = sub.add_parser("build-v66-btcd-scenario-comparison-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v66_btcd_scenario_comparison_report_html_command)

    p = sub.add_parser("build-v66-btcd-short-research-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v66_btcd_short_research_report_html_command)

    p = sub.add_parser("build-v66-btcd-hybrid-router-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v66_btcd_hybrid_router_report_html_command)

    p = sub.add_parser("build-head-controller-v66-review-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_head_controller_v66_review_report_html_command)

    p = sub.add_parser("prepare-v67-global-btcd-data")
    p.add_argument("--use-available-history", default="true")
    p.set_defaults(func=prepare_v67_global_btcd_data_command)

    p = sub.add_parser("build-v67-global-btcd-data-quality-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v67_global_btcd_data_quality_report_command)

    p = sub.add_parser("run-v67-global-btcd-scenario-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--use-available-history", default="true")
    p.set_defaults(func=run_v67_global_btcd_scenario_lab_command)

    p = sub.add_parser("run-v67-global-btcd-compact-router-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--use-available-history", default="true")
    p.set_defaults(func=run_v67_global_btcd_compact_router_lab_command)

    p = sub.add_parser("build-v67-global-btcd-rejected-scenarios-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v67_global_btcd_rejected_scenarios_report_command)

    p = sub.add_parser("build-v67-global-btcd-saved-loss-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v67_global_btcd_saved_loss_report_command)

    p = sub.add_parser("build-v67-global-btcd-yearly-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v67_global_btcd_yearly_report_command)

    p = sub.add_parser("run-head-controller-v67-review")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai")
    p.set_defaults(func=run_head_controller_v67_review_command)

    p = sub.add_parser("build-v67-global-btcd-data-quality-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v67_global_btcd_data_quality_report_html_command)

    p = sub.add_parser("build-v67-global-btcd-scenario-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v67_global_btcd_scenario_report_html_command)

    p = sub.add_parser("build-v67-global-btcd-saved-loss-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v67_global_btcd_saved_loss_report_html_command)

    p = sub.add_parser("build-v67-global-btcd-yearly-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v67_global_btcd_yearly_report_html_command)

    p = sub.add_parser("build-v67-global-btcd-rejected-scenarios-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v67_global_btcd_rejected_scenarios_report_html_command)

    p = sub.add_parser("build-v67-global-btcd-compact-router-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v67_global_btcd_compact_router_report_html_command)

    p = sub.add_parser("build-head-controller-v67-review-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_head_controller_v67_review_report_html_command)

    p = sub.add_parser("prepare-v672-btcdom-index-data")
    p.add_argument("--source-dir", default="C:/ASTT")
    p.add_argument("--use-available-history", default="true")
    p.set_defaults(func=prepare_v672_btcdom_index_data_command)

    p = sub.add_parser("build-v672-btcdom-index-data-quality-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v672_btcdom_index_data_quality_report_command)

    p = sub.add_parser("run-v672-btcdom-index-scenario-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--use-available-history", default="true")
    p.set_defaults(func=run_v672_btcdom_index_scenario_lab_command)

    p = sub.add_parser("run-v672-btcdom-index-compact-router-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000)
    p.add_argument("--use-available-history", default="true")
    p.set_defaults(func=run_v672_btcdom_index_compact_router_lab_command)

    p = sub.add_parser("build-v672-btcdom-index-rejected-scenarios-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v672_btcdom_index_rejected_scenarios_report_command)

    p = sub.add_parser("build-v672-btcdom-index-saved-loss-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v672_btcdom_index_saved_loss_report_command)

    p = sub.add_parser("build-v672-btcdom-index-yearly-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v672_btcdom_index_yearly_report_command)

    p = sub.add_parser("run-head-controller-v672-review")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai")
    p.set_defaults(func=run_head_controller_v672_review_command)

    p = sub.add_parser("build-v672-btcdom-index-data-quality-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v672_btcdom_index_data_quality_report_html_command)

    p = sub.add_parser("build-v672-btcdom-index-scenario-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v672_btcdom_index_scenario_report_html_command)

    p = sub.add_parser("build-v672-btcdom-index-saved-loss-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v672_btcdom_index_saved_loss_report_html_command)

    p = sub.add_parser("build-v672-btcdom-index-yearly-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v672_btcdom_index_yearly_report_html_command)

    p = sub.add_parser("build-v672-btcdom-index-rejected-scenarios-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v672_btcdom_index_rejected_scenarios_report_html_command)

    p = sub.add_parser("build-v672-btcdom-index-compact-router-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v672_btcdom_index_compact_router_report_html_command)

    p = sub.add_parser("build-head-controller-v672-review-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_head_controller_v672_review_report_html_command)

    p = sub.add_parser("prepare-v673-dominance-data")
    p.add_argument("--source-dir", default="C:/ASTT")
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=prepare_v673_dominance_data_command)

    p = sub.add_parser("build-v673-dominance-data-quality-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v673_dominance_data_quality_report_command)

    p = sub.add_parser("run-v673-rolling-balanced-dominance-matrix-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v673_rolling_balanced_dominance_matrix_lab_command)

    p = sub.add_parser("run-v673-bear-agent-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v673_bear_agent_lab_command)

    p = sub.add_parser("run-v673-scenario-agent-router-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v673_scenario_agent_router_lab_command)

    p = sub.add_parser("build-v673-high-watermark-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v673_high_watermark_report_command)

    p = sub.add_parser("build-v673-rejected-scenarios-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v673_rejected_scenarios_report_command)

    p = sub.add_parser("build-v673-saved-loss-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v673_saved_loss_report_command)

    p = sub.add_parser("build-v673-yearly-market-state-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v673_yearly_market_state_report_command)

    p = sub.add_parser("run-head-controller-v673-review")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai")
    p.set_defaults(func=run_head_controller_v673_review_command)

    p = sub.add_parser("build-v673-dominance-data-quality-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v673_dominance_data_quality_report_html_command)

    p = sub.add_parser("build-v673-agent-matrix-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v673_agent_matrix_report_html_command)

    p = sub.add_parser("build-v673-bear-agent-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v673_bear_agent_report_html_command)

    p = sub.add_parser("build-v673-scenario-router-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v673_scenario_router_report_html_command)

    p = sub.add_parser("build-v673-high-watermark-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v673_high_watermark_report_html_command)

    p = sub.add_parser("build-v673-rejected-scenarios-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v673_rejected_scenarios_report_html_command)

    p = sub.add_parser("build-head-controller-v673-review-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_head_controller_v673_review_report_html_command)

    p = sub.add_parser("audit-v681-compounding-vs-dominance-ledger")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=audit_v681_compounding_vs_dominance_ledger_command)

    p = sub.add_parser("run-v681-compounding-dominance-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v681_compounding_dominance_lab_command)

    p = sub.add_parser("run-v681-bear-compounding-agent-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v681_bear_compounding_agent_lab_command)

    p = sub.add_parser("run-v681-compounding-scenario-router-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v681_compounding_scenario_router_lab_command)

    p = sub.add_parser("run-v681-control-tower-review")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai")
    p.set_defaults(func=run_v681_control_tower_review_command)

    p = sub.add_parser("run-v681-paper-backfill-from-20260101")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--start-date", default="2026-01-01")
    p.add_argument("--active-route", default="BALANCED_GROWTH_COMPOUNDING_BASELINE")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v681_paper_backfill_from_20260101_command)

    p = sub.add_parser("start-v681-paper-server")
    p.add_argument("--active-route", default="BALANCED_GROWTH_COMPOUNDING_BASELINE")
    p.add_argument("--port", type=int, default=8787)
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=start_v681_paper_server_command)

    p = sub.add_parser("register-v681-shadow-route")
    p.add_argument("--route", required=True)
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=register_v681_shadow_route_command)

    p = sub.add_parser("build-v681-integrated-investment-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v681_integrated_investment_report_html_command)

    p = sub.add_parser("run-v682-bear-defense-deep-insight")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v682_bear_defense_deep_insight_command)

    p = sub.add_parser("run-v682-bear-bounce-profit-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v682_bear_bounce_profit_lab_command)

    p = sub.add_parser("run-v682-bear-response-router-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v682_bear_response_router_lab_command)

    p = sub.add_parser("build-v682-bounce-case-study-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v682_bounce_case_study_report_command)

    p = sub.add_parser("build-v682-bear-defense-insight-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v682_bear_defense_insight_report_html_command)

    p = sub.add_parser("build-v682-bear-bounce-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v682_bear_bounce_report_html_command)

    p = sub.add_parser("build-v682-bear-response-router-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v682_bear_response_router_report_html_command)

    p = sub.add_parser("build-v682-bounce-case-study-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v682_bounce_case_study_report_html_command)

    p = sub.add_parser("register-v682-bear-bounce-shadow-route")
    p.add_argument("--route", default="BEAR_BOUNCE_PROFIT_AGENT")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=register_v682_bear_shadow_route_command)

    p = sub.add_parser("register-v682-bear-response-shadow-route")
    p.add_argument("--route", default="FULL_BEAR_RESPONSE_ROUTER")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=register_v682_bear_shadow_route_command)

    p = sub.add_parser("run-v683-paper-backfill-from-20260101")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--start-date", default="2026-01-01")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v683_paper_backfill_from_20260101_command)

    p = sub.add_parser("start-v683-live-forward-paper")
    p.add_argument("--active-route", default="LG_V2_BALANCED_PLUS_DOM_GATE")
    p.add_argument("--port", type=int, default=8787)
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=start_v683_live_forward_paper_command)

    p = sub.add_parser("check-v683-paper-health")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=check_v683_paper_health_command)

    p = sub.add_parser("build-v683-active-shadow-comparison-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v683_active_shadow_comparison_report_command)

    p = sub.add_parser("build-v683-paper-dashboard-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v683_paper_dashboard_html_command)

    p = sub.add_parser("run-v683-control-tower-review")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai")
    p.set_defaults(func=run_v683_control_tower_review_command)

    p = sub.add_parser("build-v683-route-router-report")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v683_route_router_report_command)

    p = sub.add_parser("register-v683-shadow-route")
    p.add_argument("--route", required=True)
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=register_v683_shadow_route_command)

    p = sub.add_parser("switch-v683-active-paper-route")
    p.add_argument("--route", required=True)
    p.add_argument("--confirm-switch", default="false")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=switch_v683_active_paper_route_command)

    p = sub.add_parser("build-v684-bear-windows")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v684_bear_windows_command)

    p = sub.add_parser("run-v684-indicator-effectiveness-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v684_indicator_effectiveness_lab_command)

    p = sub.add_parser("run-v684-loss-guard-indicator-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v684_loss_guard_indicator_lab_command)

    p = sub.add_parser("run-v684-bear-bounce-v3-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v684_bear_bounce_v3_lab_command)

    p = sub.add_parser("run-v684-risk-sizing-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v684_risk_sizing_lab_command)

    p = sub.add_parser("run-v684-bear-router-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v684_bear_router_lab_command)

    p = sub.add_parser("build-v684-bear-windows-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v684_bear_windows_report_html_command)

    p = sub.add_parser("build-v684-indicator-effectiveness-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v684_indicator_effectiveness_report_html_command)

    p = sub.add_parser("build-v684-loss-guard-indicator-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v684_loss_guard_indicator_report_html_command)

    p = sub.add_parser("build-v684-bear-bounce-v3-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v684_bear_bounce_v3_report_html_command)

    p = sub.add_parser("build-v684-risk-sizing-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v684_risk_sizing_report_html_command)

    p = sub.add_parser("build-v684-bear-router-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v684_bear_router_report_html_command)

    p = sub.add_parser("build-v684-paper-dashboard-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v684_dashboard_html_command)

    p = sub.add_parser("run-v685-atr-precision-audit")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v685_atr_precision_audit_command)

    p = sub.add_parser("run-v685-atr-price-path-audit")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v685_atr_price_path_audit_command)

    p = sub.add_parser("run-v685-atr-sensitivity-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v685_atr_sensitivity_lab_command)

    p = sub.add_parser("build-v685-bear-window-classification")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v685_bear_window_classification_command)

    p = sub.add_parser("run-v685-bear-window-performance-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v685_bear_window_performance_lab_command)

    p = sub.add_parser("run-v685-bear-router-window-aware-lab")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v685_bear_router_window_aware_lab_command)

    p = sub.add_parser("build-v685-atr-precision-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v685_atr_precision_report_html_command)

    p = sub.add_parser("build-v685-atr-price-path-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v685_atr_price_path_report_html_command)

    p = sub.add_parser("build-v685-atr-sensitivity-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v685_atr_sensitivity_report_html_command)

    p = sub.add_parser("build-v685-bear-window-classification-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v685_bear_window_classification_report_html_command)

    p = sub.add_parser("build-v685-bear-window-performance-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v685_bear_window_performance_report_html_command)

    p = sub.add_parser("build-v685-bear-router-window-aware-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v685_bear_router_window_aware_report_html_command)

    p = sub.add_parser("build-v685-paper-dashboard-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v685_dashboard_html_command)

    p = sub.add_parser("run-v686-atr-ltf-coverage")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v686_atr_ltf_coverage_command)

    p = sub.add_parser("run-v686-atr-ltf-replay")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v686_atr_ltf_replay_command)

    p = sub.add_parser("run-v686-atr-precision-v2")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v686_atr_precision_v2_command)

    p = sub.add_parser("run-v686-bear-window-atr-replay")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--use-available-history", default="true")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v686_bear_window_atr_replay_command)

    p = sub.add_parser("register-v686-shadow-routes")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=register_v686_shadow_routes_command)

    p = sub.add_parser("run-v686-paper-backfill-with-v685-router")
    p.add_argument("--initial-cash-krw", type=float, default=500000.0)
    p.add_argument("--start-date", default="2026-01-01")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=run_v686_paper_backfill_with_v685_router_command)

    p = sub.add_parser("build-v686-active-shadow-dashboard-data")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v686_active_shadow_dashboard_data_command)

    p = sub.add_parser("start-v686-local-dashboard")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8787)
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=start_v686_local_dashboard_command)

    p = sub.add_parser("check-v686-local-dashboard-health")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=check_v686_local_dashboard_health_command)

    p = sub.add_parser("build-v686-local-dashboard-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8787)
    p.set_defaults(func=build_v686_local_dashboard_report_html_command)

    p = sub.add_parser("run-v686-control-tower-dashboard-review")
    p.add_argument("--reports-dir", default="docs/reports")
    p.add_argument("--llm-provider", default="openai")
    p.set_defaults(func=run_v686_control_tower_dashboard_review_command)

    p = sub.add_parser("build-v686-atr-ltf-coverage-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v686_atr_ltf_coverage_report_html_command)

    p = sub.add_parser("build-v686-atr-ltf-replay-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v686_atr_ltf_replay_report_html_command)

    p = sub.add_parser("build-v686-atr-precision-v2-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v686_atr_precision_v2_report_html_command)

    p = sub.add_parser("build-v686-atr-model-comparison-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v686_atr_model_comparison_report_html_command)

    p = sub.add_parser("build-v686-bear-window-atr-replay-report-html")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_v686_bear_window_atr_replay_report_html_command)

    p = sub.add_parser("audit-mock-vs-real-data")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions"))
    p.set_defaults(func=audit_mock_vs_real_data_command)

    p = sub.add_parser("check-upbit-auth-safety")
    p.add_argument("--read-check", default="false")
    p.set_defaults(func=check_upbit_auth_safety_command)

    p = sub.add_parser("build-upbit-real-api-report")
    p.set_defaults(func=build_upbit_real_api_report_command)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
