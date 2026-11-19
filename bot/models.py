"""Small data structures shared by the bot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Bar:
    """One OHLCV bar. ``ts`` is epoch milliseconds UTC."""

    symbol: str
    ts: int
    open: float
    high: float
    low: float
    close: float
    volume: float

    def validate(self) -> None:
        if self.ts <= 0 or min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError(f"invalid bar price/timestamp: {self}")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError(f"inconsistent OHLC bar: {self}")


@dataclass(frozen=True)
class Signal:
    """Entry proposal. A stop is mandatory: no stop, no trade."""

    strategy: str
    symbol: str
    ts: int
    side: str
    entry: float
    stop: float
    timeframe: str
    target: Optional[float] = None
    reason: str = ""

    def __post_init__(self) -> None:
        if self.side not in ("long", "short"):
            raise ValueError("side must be long or short")
        if self.entry <= 0 or self.stop <= 0:
            raise ValueError("entry and stop must be positive")
        if self.side == "long" and self.stop >= self.entry:
            raise ValueError("long stop must be below entry")
        if self.side == "short" and self.stop <= self.entry:
            raise ValueError("short stop must be above entry")


@dataclass
class Position:
    trade_id: str
    strategy: str
    symbol: str
    side: str
    entry_time: int
    entry_price: float
    size: float
    stop_price: float
    stop_on_exchange: bool = False
    target: Optional[float] = None


@dataclass
class TradeRecord:
    """One row of trades.csv. Every cost field must be a number, never blank."""

    trade_id: str
    strategy: str
    market: str
    side: str
    entry_time: str
    entry_price: float
    exit_time: str
    exit_price: float
    size: float
    stop_price: float
    R_multiple: float
    fee_usd: float
    slippage_usd: float
    funding_usd: float
    pnl_usd: float
    notes: str = ""

    def as_row(self) -> dict:
        return {
            "trade_id": self.trade_id,
            "strategy": self.strategy,
            "market": self.market,
            "side": self.side,
            "entry_time": self.entry_time,
            "entry_price": round(self.entry_price, 8),
            "exit_time": self.exit_time,
            "exit_price": round(self.exit_price, 8),
            "size": round(self.size, 8),
            "stop_price": round(self.stop_price, 8),
            "R_multiple": round(self.R_multiple, 4),
            "fee_usd": round(self.fee_usd, 6),
            "slippage_usd": round(self.slippage_usd, 6),
            "funding_usd": round(self.funding_usd, 6),
            "pnl_usd": round(self.pnl_usd, 6),
            "notes": self.notes,
        }


@dataclass
class BacktestResult:
    """Costs are always included. No result is ever labelled 'proven'."""

    run_id: str
    strategy: str
    symbol: str
    synthetic: bool
    trades: int
    win_rate: float
    pnl_usd: float
    expectancy_R: float
    best_R: float
    worst_R: float
    max_drawdown_pct: float
    fees_usd: float
    slippage_usd: float
    funding_usd: float
    config_snapshot: dict = field(default_factory=dict)
    data_sha256: str = ""
    notes: str = ""

    def as_dict(self) -> dict:
        data = dict(self.__dict__)
        data["data_source"] = "SYNTHETIC_SMOKE_TEST" if self.synthetic else "VERIFIED_DATA"
        data["verdict"] = "NOT_EVIDENCE" if self.synthetic else "see playbook pass bar"
        return data
