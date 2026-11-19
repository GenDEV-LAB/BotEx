"""Cost-aware backtests with walk-forward windows.

Every number in a result comes from a logged run. Synthetic runs are labelled
NOT_EVIDENCE. No result is called 'proven', 'guaranteed' or 'risk-free'.
"""

from __future__ import annotations

import hashlib
import time
from copy import deepcopy
from datetime import datetime, timezone
from typing import Optional

from . import strategies
from .data import INTERVAL_MS, generate_synthetic
from .events import is_blackout, load_events, position_scale
from .exchange import PaperAdapter
from .models import BacktestResult, Bar
from .risk import RiskEngine


def _warmup(params: dict) -> int:
    return max(60, int(params.get("slow", 0)), int(params.get("ema", 0)),
               int(params.get("lookback", 0)) * 2 + 20, int(params.get("period", 0)) + 20) + 15


def run_backtest(
    bars: list[Bar],
    strategy: str,
    cfg: dict,
    params: Optional[dict] = None,
    synthetic: bool = True,
    stress: bool = False,
    data_sha256: str = "",
    interval_ms: int = INTERVAL_MS["1h"],
    start_ms: Optional[int] = None,
    end_ms: Optional[int] = None,
) -> BacktestResult:
    if strategy not in strategies.REGISTRY:
        raise ValueError(f"unknown strategy: {strategy}")
    p = deepcopy(strategies.DEFAULT_PARAMS.get(strategy, {}))
    p.update(params or {})
    # For smoke tests only: distinct synthetic series stand in for other assets.
    # With real data these MUST come from verified datasets in data/clean/.
    if strategy == "relative_value" and "other_bars" not in p:
        if synthetic:
            p["other_bars"] = generate_synthetic("SIM02", len(bars), interval_ms, seed=43,
                                                 start_ms=bars[0].ts if bars else None)
        else:
            p["other_bars"] = bars
    universe = {}
    for n, sym in enumerate(cfg["data"]["synthetic_symbols"]):
        series = (generate_synthetic(sym, len(bars), interval_ms, seed=40 + n,
                                     start_ms=bars[0].ts if bars else None)
                  if synthetic else bars)
        universe.setdefault(sym, series)
    p.setdefault("universe_bars", universe)

    local_cfg = deepcopy(cfg)
    if stress:
        local_cfg["costs"]["slippage_bps_per_side"] *= local_cfg["costs"]["stress_slippage_multiplier"]

    source = [b for b in bars if (start_ms is None or b.ts >= start_ms) and (end_ms is None or b.ts < end_ms)]
    if len(source) < _warmup(p) + 2:
        return BacktestResult(
            run_id=f"empty-{time.time_ns()}", strategy=strategy, symbol=bars[0].symbol if bars else "?",
            synthetic=synthetic, trades=0, win_rate=0.0, pnl_usd=0.0, expectancy_R=0.0,
            best_R=0.0, worst_R=0.0, max_drawdown_pct=0.0, fees_usd=0.0, slippage_usd=0.0,
            funding_usd=0.0, notes="insufficient data for warmup; no test run", data_sha256=data_sha256,
        )

    risk = RiskEngine(
        equity=cfg["capital_usd"],
        risk_per_trade_pct=cfg["risk_per_trade_pct"],
        max_daily_loss_pct=cfg["max_daily_loss_pct"],
        kill_switch_pct=cfg["kill_switch_drawdown_pct"],
        max_trades_per_day=cfg["max_trades_per_day"],
        max_leverage=cfg["max_leverage"],
    )
    adapter = PaperAdapter(local_cfg, risk.equity)
    peak = risk.equity
    max_dd = 0.0
    fn = strategies.REGISTRY[strategy]
    calendar_events = load_events()
    blackout_bars = 0

    for i, bar in enumerate(source):
        adapter.on_bar(bar)
        risk.update_equity(adapter.equity())
        peak = max(peak, adapter.equity())
        if peak > 0:
            max_dd = max(max_dd, (peak - adapter.equity()) / peak * 100)
        if i < _warmup(p) or risk.kill_switch:
            continue
        if is_blackout(bar.ts, cfg, calendar_events):
            blackout_bars += 1
            continue  # sections 9/10: no new entries around scheduled events
        # Pass only data up to the current bar: no lookahead.
        window = source[: i + 1]
        sig = fn(window, i, p)
        if sig is None:
            continue
        allowed, _ = risk.can_open(bar.ts)
        if not allowed:
            continue
        sizing = risk.size_for(sig, local_cfg, position_scale(bar.ts, cfg, calendar_events))
        if adapter.place(sig, sizing, strategy):
            risk.register_entry()

    trades = adapter.closed
    rs = [t.R_multiple for t in trades]
    wins = sum(1 for r in rs if r > 0)
    pnl = sum(t.pnl_usd for t in trades)
    result = BacktestResult(
        run_id=f"{strategy}-{('stress' if stress else 'base')}-{time.time_ns()}",
        strategy=strategy,
        symbol=source[0].symbol,
        synthetic=synthetic,
        trades=len(trades),
        win_rate=wins / len(trades) if trades else 0.0,
        pnl_usd=pnl,
        expectancy_R=sum(rs) / len(rs) if rs else 0.0,
        best_R=max(rs) if rs else 0.0,
        worst_R=min(rs) if rs else 0.0,
        max_drawdown_pct=max_dd,
        fees_usd=sum(t.fee_usd for t in trades),
        slippage_usd=sum(t.slippage_usd for t in trades),
        funding_usd=sum(t.funding_usd for t in trades),
        config_snapshot={"params": {k: v for k, v in p.items() if not k.endswith("_bars")},
                         "costs": local_cfg["costs"], "stress": stress},
        data_sha256=data_sha256,
        notes="SYNTHETIC SMOKE TEST — not evidence" if synthetic else "combined out-of-sample test windows",
    )
    if risk.kill_switch:
        result.notes += "; kill switch triggered (drawdown from high-water mark)"
    if blackout_bars:
        result.notes += f"; {blackout_bars} bars blocked by event blackout"
    if adapter.incidents:
        result.notes += "; " + " | ".join(adapter.incidents[:5])
    return result


def walk_forward(
    bars: list[Bar], strategy: str, cfg: dict, synthetic: bool = True,
    data_sha256: str = "", interval_ms: int = INTERVAL_MS["1h"],
) -> list[BacktestResult]:
    """Rolling 12-month tune / 3-month test. Only test-window results are returned.

    The tuning step is a placeholder: no parameter search is performed, so default
    parameters are used. This is recorded in the result notes rather than hidden.
    """
    tune_ms = cfg["backtest"]["walk_forward_tune_months"] * 30 * 24 * 3_600_000
    test_ms = cfg["backtest"]["walk_forward_test_months"] * 30 * 24 * 3_600_000
    if not bars:
        return []
    start, end = bars[0].ts, bars[-1].ts + interval_ms
    results: list[BacktestResult] = []
    cursor = start
    while cursor + tune_ms + test_ms <= end:
        test_start = cursor + tune_ms
        test_end = min(test_start + test_ms, end)
        res = run_backtest(bars, strategy, cfg, synthetic=synthetic, data_sha256=data_sha256,
                           interval_ms=interval_ms, start_ms=test_start, end_ms=test_end)
        res.run_id += "-wf-test"
        res.notes += "; default params (no parameter search implemented)"
        results.append(res)
        cursor = test_start
    return results


def buy_hold_benchmark(bars: list[Bar], cfg: dict, synthetic: bool = True) -> BacktestResult:
    """Same costs as a strategy test, but simply long from first to last bar."""
    if len(bars) < 2:
        raise ValueError("buy & hold benchmark needs at least two bars")
    # Use the same cost assumptions; synthetic prices must be labelled by the caller.
    costs = cfg["costs"]
    fee = costs["fee_bps_per_side_spot"] / 10_000
    slip = costs["slippage_bps_per_side"] / 10_000
    entry = bars[0].close * (1 + slip)
    exit_ = bars[-1].close * (1 - slip)
    qty = cfg["capital_usd"] / entry
    fee_usd = (entry + exit_) * qty * fee
    pnl = (exit_ - entry) * qty - fee_usd
    peak = entry
    worst = 0.0
    for b in bars:
        peak = max(peak, b.close)
        worst = max(worst, (peak - b.close) / peak * 100)
    return BacktestResult(
        run_id=f"buy-hold-benchmark-{time.time_ns()}",
        strategy="buy_and_hold_benchmark", symbol=bars[0].symbol, synthetic=synthetic,
        trades=1, win_rate=1.0 if pnl > 0 else 0.0, pnl_usd=pnl,
        expectancy_R=0.0, best_R=0.0, worst_R=0.0, max_drawdown_pct=worst,
        fees_usd=fee_usd, slippage_usd=slip * (entry + exit_) * qty, funding_usd=0.0,
        notes="SYNTHETIC — not evidence" if synthetic else "benchmark on verified data",
    )


def combine(results: list[BacktestResult], strategy: str, synthetic: bool = True) -> BacktestResult:
    """Combine the out-of-sample test windows into a single reported result."""
    if not results:
        return BacktestResult("combined-empty", strategy, "?", synthetic, 0, 0.0, 0.0, 0.0, 0.0, 0.0,
                              0.0, 0.0, 0.0, 0.0, notes="no completed test windows")
    total = sum(r.trades for r in results)
    pnl = sum(r.pnl_usd for r in results)
    rsum = sum(r.expectancy_R * r.trades for r in results)
    return BacktestResult(
        run_id=f"combined-{strategy}-{time.time_ns()}",
        strategy=strategy, symbol=results[0].symbol, synthetic=synthetic,
        trades=total, win_rate=sum(r.win_rate * r.trades for r in results) / total if total else 0.0,
        pnl_usd=pnl, expectancy_R=rsum / total if total else 0.0,
        best_R=max(r.best_R for r in results), worst_R=min(r.worst_R for r in results),
        max_drawdown_pct=max(r.max_drawdown_pct for r in results),
        fees_usd=sum(r.fees_usd for r in results), slippage_usd=sum(r.slippage_usd for r in results),
        funding_usd=sum(r.funding_usd for r in results),
        config_snapshot={"windows": len(results)},
        notes="combined out-of-sample test windows only; " + ("SYNTHETIC — not evidence" if synthetic else ""),
    )
