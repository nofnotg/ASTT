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
from replay_lab.paths import REPLAY_STORE_DIR, ensure_replay_store
from replay_lab.replay.batch_replay import run_batch_0900
from replay_lab.replay.replay_runner_0900 import ReplayRunner0900
from replay_lab.replay.replay_session import ReplaySessionConfig
from replay_lab.replay.walk_forward import build_walk_forward_windows


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


def run_0900(args: argparse.Namespace) -> int:
    day = date.fromisoformat(args.date)
    clock = ReplayClock(datetime.combine(day, datetime.min.time()).replace(hour=8, minute=50))
    provider = ReplayDataProvider(clock)
    config = ReplaySessionConfig(session_id=f"manual_{day.isoformat()}", date_kst=day, markets=_resolve_markets(args.markets, provider=provider, top_limit=args.top_markets))
    result = ReplayRunner0900(provider, clock).run(config, top_market_limit=args.top_markets)
    print(json.dumps({key: len(value) for key, value in result.items()}, ensure_ascii=False))
    return 0


def batch_0900(args: argparse.Namespace) -> int:
    provider = ReplayDataProvider(ReplayClock(datetime.now()))
    exp_dir = run_batch_0900(args.days, _resolve_markets(args.markets, provider=provider, top_limit=args.top_markets), args.top_markets)
    print(f"experiment: {exp_dir}")
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


def main(argv: list[str] | None = None) -> int:
    ensure_replay_store()
    parser = argparse.ArgumentParser(description="ASTT Replay Lab sidecar CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("load-markets")
    p.set_defaults(func=load_markets)

    p = sub.add_parser("load-candles")
    p.add_argument("--market", required=True)
    p.add_argument("--timeframe", default="1m", choices=["1m", "5m", "15m", "1h", "1d"])
    p.add_argument("--days", type=int, default=90)
    p.set_defaults(func=load_candles)

    p = sub.add_parser("load-0900")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.set_defaults(func=load_0900)

    p = sub.add_parser("run-0900")
    p.add_argument("--date", required=True)
    p.add_argument("--markets")
    p.add_argument("--top-markets", type=int)
    p.set_defaults(func=run_0900)

    p = sub.add_parser("batch-0900")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--top-markets", type=int, default=50)
    p.add_argument("--markets")
    p.set_defaults(func=batch_0900)

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

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

