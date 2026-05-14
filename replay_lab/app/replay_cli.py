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
from replay_lab.feedback.investment_report import InvestmentReportBuilder
from replay_lab.feedback.report_catalog import ReplayReportCatalog
from replay_lab.paths import REPLAY_STORE_DIR, ensure_replay_store
from replay_lab.replay.batch_replay import run_batch_0900, run_daily_study_0900
from replay_lab.replay.replay_runner_0900 import ReplayRunner0900
from replay_lab.replay.replay_session import ReplaySessionConfig
from replay_lab.replay.walk_forward import build_walk_forward_windows
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

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

