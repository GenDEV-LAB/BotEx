"""Command-line entry points for BotEx. Everything is paper by default."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import acceptance, events, feeds, loop, monitor, paper, research, review, robustness, schedule, simple, strategies, telegram
from .backtest import run_backtest
from .config import RAW_DIR, CLEAN_DIR, ROOT, TRADES_CSV, is_approval_window, load_config, ms_utc, now_utc
from .logging_setup import setup as setup_logging
from .data import INTERVAL_MS, integrity_issues, sha256_file, sources_registered, write_synthetic
from .journal import save_backtest


def cmd_status(cfg: dict, args: argparse.Namespace) -> dict:
    trades = 0
    if TRADES_CSV.exists():
        trades = max(0, sum(1 for _ in TRADES_CSV.open(encoding="utf-8")) - 1)
    data = {
        "fund": cfg["fund_name"],
        "mode": cfg["mode"],
        "capital_usd": cfg["capital_usd"],
        "risk_per_trade_pct": cfg["risk_per_trade_pct"],
        "max_daily_loss_pct": cfg["max_daily_loss_pct"],
        "kill_switch_drawdown_pct": cfg["kill_switch_drawdown_pct"],
        "max_leverage": cfg["max_leverage"],
        "leverage_confirmed": cfg.get("max_leverage_confirmed", False),
        "note": "5x confirmed by owner; live still requires a separate signed approval",
        "timeframes": cfg["timeframes"],
        "timezone": cfg["timezone"],
        "verified_sources": sources_registered(ROOT / "data" / "sources.md", cfg["data"]["min_sources_for_price"]),
        "journaled_trades": trades,
        "watchlist": [i["symbol"] for i in cfg.get("watchlist", [])],
        "blocked": [
            "no exchange/broker account connected",
            "no real market data source registered",
            "no server / Telegram configured",
        ],
    }
    return data


def cmd_make_synthetic(cfg: dict, args: argparse.Namespace) -> dict:
    symbol = args.symbol
    if not symbol.startswith("SIM") and not cfg["data"]["allow_real_symbols"]:
        raise ValueError("real symbols are blocked: register two verified sources first")
    path = ROOT / "data" / "raw" / f"{symbol}.synthetic.csv"
    seed = 42 + sum(ord(ch) for ch in symbol) % 1000
    bars = write_synthetic(path, symbol, args.bars, INTERVAL_MS["4h"], seed)
    return {"file": str(path), "symbol": symbol, "bars": len(bars),
            "warning": "SYNTHETIC SMOKE TEST DATA — not evidence"}


def cmd_instrument(cfg: dict, args: argparse.Namespace) -> dict:
    matches = [i for i in cfg.get("watchlist", []) if i["symbol"].upper() == args.symbol.upper()]
    if not matches:
        raise ValueError(f"{args.symbol} is not in the watchlist; a new market needs owner approval")
    item = matches[0]
    return {
        "instrument": item,
        "blockers": [
            "venue / broker not configured",
            f"data source not configured (status: {item['status']})",
            "two verified sources with 4+ years required before real symbols",
            "spot shorting disabled by mandate; use a perp/CFD venue and approval for shorts",
        ],
        "proxy_for_tests": item["synthetic_proxy"],
    }


def cmd_check_data(cfg: dict, args: argparse.Namespace) -> dict:
    files = sorted(CLEAN_DIR.glob("*.csv"))
    out = []
    for path in files:
        bars = []
        try:
            from .data import read_bars
            bars = read_bars(path)
        except Exception as exc:
            out.append({"file": str(path), "error": f"{type(exc).__name__}: {exc}"})
            continue
        out.append({
            "file": str(path),
            "bars": len(bars),
            "sha256": sha256_file(path),
            "issues": integrity_issues(bars, INTERVAL_MS["1h"]),
        })
    if not files:
        out.append({"info": "no files in data/clean — register sources in data/sources.md first"})
    return {"files": out, "sources_registered": sources_registered(ROOT / "data" / "sources.md", 2)}


def cmd_backtest(cfg: dict, args: argparse.Namespace) -> dict:
    bars = write_synthetic(ROOT / "data" / "raw" / "SIM01.synthetic.csv", "SIM01", 1500, INTERVAL_MS["4h"], 42)
    results = []
    for name in strategies.REGISTRY:
        res = run_backtest(bars, name, cfg, synthetic=True)
        save_backtest(res)
        results.append({
            "strategy": name, "trades": res.trades, "pnl_usd": round(res.pnl_usd, 3),
            "expectancy_R": round(res.expectancy_R, 4), "worst_R": round(res.worst_R, 4),
            "max_drawdown_pct": round(res.max_drawdown_pct, 2),
        })
    return {"source": "SYNTHETIC — NOT EVIDENCE", "results": results, "saved_in": "backtests/"}



def cmd_events(cfg: dict, args: argparse.Namespace) -> dict:
    from datetime import datetime, timezone

    from .config import ms_utc
    items = events.load_events()
    return {
        "registered_events": len(items),
        "upcoming": [{"ts_utc": datetime.fromtimestamp(e.ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                      "label": e.label, "source": e.source} for e in events.upcoming(items, ms_utc(now_utc()))],
        "in_blackout_now": events.is_blackout(ms_utc(now_utc()), cfg, items),
        "blackout_minutes": cfg["event_blackout_minutes"],
    }


def cmd_robustness(cfg: dict, args: argparse.Namespace) -> dict:
    return robustness.run(cfg, strategy=args.strategy)


def cmd_review(cfg: dict, args: argparse.Namespace) -> dict:
    return {"comparison": review.compare(), "weekly": review.weekly()}


def cmd_schedule(cfg: dict, args: argparse.Namespace) -> dict:
    return {"schedule": schedule.daily_schedule(cfg),
            "next": schedule.next_task(cfg),
            "approval_window_now": is_approval_window(cfg)}



def cmd_fetch(cfg: dict, args: argparse.Namespace) -> dict:
    feed = feeds.CcxtFeed(args.exchange)
    symbol = args.symbol or "BTC/USDT"
    if not args.apply:
        return {
            "dry_run": True,
            "would_fetch": {"symbol": symbol, "timeframe": args.timeframe,
                            "limit": args.limit, "days": args.days},
            "network_called": False,
            "note": "ajouter --apply et BOTEX_DATA_ENABLED=1 pour télécharger réellement",
        }
    since = ms_utc(now_utc()) - args.days * 24 * 3_600_000
    bars = feed.fetch(symbol, args.timeframe, since, args.limit, dry_run=False)
    path = RAW_DIR / f"{symbol.replace('/', '_')}_{args.timeframe}.csv"
    feeds.save_bars(path, bars)
    registry = feeds.register_dataset(path, feed.name, args.url or feed.name, symbol,
                                      args.timeframe, f"{args.days} days", "to verify")
    return {"bars": len(bars), "file": str(path), "symbol": symbol, "registry": registry}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m bot.cli")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("go")
    sub.add_parser("status")
    p_syn = sub.add_parser("make-synthetic")
    p_syn.add_argument("--bars", type=int, default=4000)
    p_syn.add_argument("--symbol", default="SIM01")
    sub.add_parser("check-data")
    sub.add_parser("backtest")
    sub.add_parser("research")
    sub.add_parser("paper")
    sub.add_parser("monitor")
    sub.add_parser("run-once")
    sub.add_parser("events")
    p_rob = sub.add_parser("robustness")
    p_rob.add_argument("--strategy", default="trend_following")
    sub.add_parser("review")
    sub.add_parser("schedule")
    sub.add_parser("telegram")
    sub.add_parser("acceptance")
    p_ins = sub.add_parser("instrument")
    p_ins.add_argument("--symbol", default="XAUUSD")
    p_fetch = sub.add_parser("fetch")
    p_fetch.add_argument("--exchange", default="binance")
    p_fetch.add_argument("--symbol", default=None)
    p_fetch.add_argument("--timeframe", default="1h")
    p_fetch.add_argument("--limit", type=int, default=500)
    p_fetch.add_argument("--days", type=int, default=1460)
    p_fetch.add_argument("--url", default="")
    p_fetch.add_argument("--apply", action="store_true", help="really fetch (needs BOTEX_DATA_ENABLED=1)")
    args = parser.parse_args(argv)
    setup_logging()
    cfg = load_config()

    handlers = {
        "status": cmd_status,
        "make-synthetic": cmd_make_synthetic,
        "check-data": cmd_check_data,
        "backtest": cmd_backtest,
        "research": lambda c, a: research.nightly(c),
        "paper": lambda c, a: paper.paper_cycle(c),
        "monitor": lambda c, a: monitor.run(c),
        "run-once": lambda c, a: loop.compact(loop.run_once(c)),
        "events": cmd_events,
        "robustness": cmd_robustness,
        "review": cmd_review,
        "schedule": cmd_schedule,
        "telegram": lambda c, a: {"answers": telegram.poll_commands(c)},
        "acceptance": lambda c, a: acceptance.run(),
        "instrument": cmd_instrument,
        "fetch": cmd_fetch,
    }
    if args.command == "go":
        simple.run()
        return 0

    try:
        result = handlers[args.command](cfg, args)
    except Exception as exc:
        print(f"ERROR ({type(exc).__name__}): {exc}")
        return 1

    if args.command == "research":
        result = {
            "data_source": result["data_source"], "strategies": result["strategies"],
            "walk_forward": result["walk_forward"], "leaderboard": result["leaderboard"],
            "selection_report": result["selection_report"],
            "passed_strategies": result["passed_strategies"], "report": result["report"],
        }
    if args.json or args.command in ("backtest", "run-once", "robustness"):
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    print(f"UTC: {now_utc().isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
