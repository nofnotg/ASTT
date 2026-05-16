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
from replay_lab.paths import REPLAY_STORE_DIR, ensure_replay_store
from replay_lab.replay.batch_replay import run_batch_0900, run_daily_study_0900
from replay_lab.replay.investment_v2 import run_study_v2
from replay_lab.replay.replay_runner_0900 import ReplayRunner0900
from replay_lab.replay.replay_session import ReplaySessionConfig
from replay_lab.replay.fear_divergence_v4 import run_fear_divergence_v4
from replay_lab.replay.fear_exhaustion_v41 import run_fear_exhaustion_v41
from replay_lab.replay.small_seed_v3 import run_small_seed_v3
from replay_lab.replay.structure_reversal_v5 import run_structure_reversal_v5
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

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

