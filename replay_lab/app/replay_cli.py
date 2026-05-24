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
    result = run_head_controller_draft_v556(args.reports_dir)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


def build_entry_discovery_report_v556_command(args: argparse.Namespace) -> int:
    out = EntryDiscoveryHTMLReportV556().build(args.sessions_dir)
    print(f"entry discovery report: {out}")
    return 0


def build_head_controller_report_v556_command(args: argparse.Namespace) -> int:
    out = HeadControllerHTMLReportV556().build(args.reports_dir)
    print(f"head controller report: {out}")
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
    p.set_defaults(func=run_head_controller_draft_v556_command)

    p = sub.add_parser("build-entry-discovery-report-v556")
    p.add_argument("--sessions-dir", default=str(REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555"))
    p.set_defaults(func=build_entry_discovery_report_v556_command)

    p = sub.add_parser("build-head-controller-report-v556")
    p.add_argument("--reports-dir", default="docs/reports")
    p.set_defaults(func=build_head_controller_report_v556_command)

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

