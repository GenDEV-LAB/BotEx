"""Paper trading engine — one pass over the data, no venue connection."""

from __future__ import annotations

from typing import Any

from . import strategies
from .config import iso_utc
from .data import INTERVAL_MS, generate_synthetic
from .events import is_blackout, load_events, position_scale
from .exchange import PaperAdapter
from .journal import append_trade
from .state import RuntimeState, apply_to_risk, from_risk, load_state, save_state
from .risk import RiskEngine


def _positions(adapter: PaperAdapter) -> list[dict]:
    out = []
    for positions in adapter.positions.values():
        for p in positions:
            out.append({
                "trade_id": p.trade_id, "strategy": p.strategy, "symbol": p.symbol,
                "side": p.side, "entry_time": p.entry_time, "entry_price": p.entry_price,
                "size": p.size, "stop_price": p.stop_price,
                "stop_on_exchange": p.stop_on_exchange, "target": p.target,
            })
    return out


def paper_cycle(cfg: dict, notify: bool = False, journal: bool = True) -> dict[str, Any]:
    # Synthetic smoke tests are isolated: they must not touch the live runtime state.
    smoke = not cfg["data"]["allow_real_symbols"]
    state = (RuntimeState(equity_usd=cfg["capital_usd"], high_water_mark_usd=cfg["capital_usd"],
                          day_start_equity_usd=cfg["capital_usd"], mode=cfg["mode"])
             if smoke else load_state(cfg=cfg))
    risk = RiskEngine(
        equity=state.equity_usd,
        risk_per_trade_pct=cfg["risk_per_trade_pct"],
        max_daily_loss_pct=cfg["max_daily_loss_pct"],
        kill_switch_pct=cfg["kill_switch_drawdown_pct"],
        max_trades_per_day=cfg["max_trades_per_day"],
        max_leverage=cfg["max_leverage"],
    )
    apply_to_risk(state, risk)

    def on_trade(rec):
        rec.notes = "SYNTHETIC_SMOKE_TEST; " + rec.notes
        if journal:
            append_trade(rec)

    adapter = PaperAdapter(cfg, risk.equity, on_trade=on_trade)
    symbol = cfg["data"]["synthetic_symbols"][0]
    bars = generate_synthetic(symbol, 800, INTERVAL_MS["15m"], seed=7)
    params = strategies.DEFAULT_PARAMS["trend_following"]
    calendar_events = load_events()
    blackout_bars = 0

    killed_this_run = False
    for i, bar in enumerate(bars):
        adapter.on_bar(bar)
        risk.update_equity(adapter.equity())
        if not smoke and i % 100 == 0:
            save_state(from_risk(risk, state, _positions(adapter)))
        if risk.kill_switch and not killed_this_run:
            killed_this_run = True
            if not smoke:
                save_state(from_risk(risk, state, _positions(adapter)))
        if i < params["slow"] + 15 or risk.kill_switch:
            continue
        if is_blackout(bar.ts, cfg, calendar_events):
            blackout_bars += 1
            continue
        sig = strategies.trend_following(bars[: i + 1], i, params)
        if sig is None:
            continue
        allowed, _ = risk.can_open(bar.ts)
        if not allowed:
            continue
        sizing = risk.size_for(sig, cfg, position_scale(bar.ts, cfg, calendar_events))
        if adapter.place(sig, sizing, "trend_following"):
            risk.register_entry()

    if not smoke:
        save_state(from_risk(risk, state, _positions(adapter)))
    return {
        "checked_at_utc": iso_utc(),
        "mode": "paper",
        "data": "SYNTHETIC_SMOKE_TEST",
        "equity_usd": round(adapter.equity(), 4),
        "trades_closed": len(adapter.closed),
        "trades_open": sum(len(v) for v in adapter.positions.values()),
        "kill_switch": risk.kill_switch,
        "incidents": adapter.incidents,
        "blackout_bars": blackout_bars,
    }
