"""Position sizing from the stop, daily loss limit, kill switch and stop enforcement."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .models import Position, Signal

EPS = 1e-9


def position_size(
    equity: float,
    risk_pct: float,
    entry: float,
    stop: float,
    fee_bps_per_side: float,
    slippage_bps_per_side: float,
    leverage_cap: float,
) -> dict:
    """Size = (account risk) / (stop distance + costs), capped by leverage.

    No leverage beyond the cap, no Martingale, no adding to losers.
    """
    if equity <= 0 or entry <= 0 or stop <= 0:
        raise ValueError("equity, entry and stop must be positive")
    distance = abs(entry - stop) / entry
    if distance <= EPS:
        raise ValueError("stop distance is zero")
    risk_usd = equity * risk_pct / 100.0
    cost_buffer = (fee_bps_per_side + slippage_bps_per_side * 2) / 10_000.0
    notional = risk_usd / (distance + cost_buffer)
    cap_notional = equity * leverage_cap
    capped = notional > cap_notional
    notional = min(notional, cap_notional)
    return {
        "qty": notional / entry,
        "notional_usd": notional,
        "risk_usd": risk_usd,
        "stop_distance_pct": distance * 100,
        "capped_by_leverage": capped,
        "fee_usd_est": notional * fee_bps_per_side / 10_000.0,
        "slippage_usd_est": notional * slippage_bps_per_side / 10_000.0,
    }


@dataclass
class RiskEngine:
    equity: float
    risk_per_trade_pct: float = 1.0
    max_daily_loss_pct: float = 5.0
    kill_switch_pct: float = 10.0
    max_trades_per_day: int = 3
    max_leverage: float = 5.0
    hwm: float = field(init=False)
    day_start_equity: float = field(init=False)
    current_day: str = field(init=False)
    trades_today: int = field(init=False, default=0)
    kill_switch: bool = field(init=False, default=False)
    blocked_reason: str = field(init=False, default="")

    def __post_init__(self) -> None:
        self.hwm = self.equity
        self.day_start_equity = self.equity
        self.current_day = datetime.now(timezone.utc).date().isoformat()

    def on_bar_time(self, ts_ms: int | None = None) -> None:
        day = (
            datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).date().isoformat()
            if ts_ms is not None
            else datetime.now(timezone.utc).date().isoformat()
        )
        if day != self.current_day:
            self.current_day = day
            self.day_start_equity = self.equity
            self.trades_today = 0

    def update_equity(self, new_equity: float) -> None:
        self.equity = new_equity
        self.hwm = max(self.hwm, new_equity)
        if self.hwm > 0 and (self.hwm - new_equity) / self.hwm * 100 >= self.kill_switch_pct:
            self.kill_switch = True
            self.blocked_reason = "kill switch: drawdown from high-water mark"

    def can_open(self, ts_ms: int | None = None) -> tuple[bool, str]:
        self.on_bar_time(ts_ms)
        if self.kill_switch:
            return False, self.blocked_reason
        if self.day_start_equity > 0:
            daily = (self.day_start_equity - self.equity) / self.day_start_equity * 100
            if daily >= self.max_daily_loss_pct:
                return False, f"daily loss limit reached ({daily:.2f}%)"
        if self.trades_today >= self.max_trades_per_day:
            return False, "max trades per day reached"
        return True, ""

    def register_entry(self) -> None:
        self.trades_today += 1

    def size_for(self, signal: Signal, cfg: dict, scale: float = 1.0) -> dict:
        costs = cfg["costs"]
        fee = costs["fee_bps_per_side_spot"]
        return position_size(
            self.equity,
            self.risk_per_trade_pct * scale,
            signal.entry,
            signal.stop,
            fee,
            costs["slippage_bps_per_side"],
            self.max_leverage,
        )


def require_exchange_stop(position: Position) -> None:
    """Golden rule: no stop resting on the exchange, no trade."""
    if not position.stop_on_exchange:
        raise RuntimeError(f"trade blocked: no exchange stop for {position.trade_id} ({position.symbol})")


def gap_through_stop(bar_open: float, stop: float, side: str) -> bool:
    """A gap through the stop must be closed at the open and logged as an incident."""
    return (side == "long" and bar_open <= stop) or (side == "short" and bar_open >= stop)
