"""Exchange adapters. Paper is fully simulated; live is deliberately a locked stub."""

from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from typing import Callable, Optional

from .config import ApprovalError, assert_live_allowed, iso_utc
from .models import Bar, Position, Signal, TradeRecord
from .risk import gap_through_stop, require_exchange_stop


class ExchangeAdapter(ABC):
    @abstractmethod
    def place(self, signal: Signal, sizing: dict, strategy: str) -> Optional[Position]:
        ...

    @abstractmethod
    def on_bar(self, bar: Bar) -> list[TradeRecord]:
        ...

    @abstractmethod
    def equity(self) -> float:
        ...


class PaperAdapter(ExchangeAdapter):
    """Simulated fills with fees, slippage and funding. Never contacts a venue."""

    def __init__(self, cfg: dict, equity: float, on_trade: Optional[Callable[[TradeRecord], None]] = None):
        self.cfg = cfg
        self._equity = float(equity)
        self.positions: dict[str, list[Position]] = {}
        self.closed: list[TradeRecord] = []
        self.on_trade = on_trade
        self._ids = itertools.count(1)
        self.costs = cfg["costs"]
        self.max_hold_ms = cfg.get("max_holding_hours", 48) * 3_600_000
        self.default_rr = cfg.get("default_reward_risk", 2.0)
        self.incidents: list[str] = []
        self.entry_fees: dict[str, float] = {}
        self.entry_slip: dict[str, float] = {}
        self.entry_risk: dict[str, float] = {}

    def equity(self) -> float:
        return self._equity

    def _fee_bps(self) -> float:
        return self.costs["fee_bps_per_side_perps"]

    def _fill(self, price: float, side: str) -> tuple[float, float]:
        slip = self.costs["slippage_bps_per_side"] / 10_000
        filled = price * (1 + slip) if side == "long" else price * (1 - slip)
        return filled, abs(filled - price)

    def place(self, signal: Signal, sizing: dict, strategy: str) -> Optional[Position]:
        qty = sizing["qty"]
        if qty <= 0 or sizing["notional_usd"] > self._equity * self.cfg["max_leverage"] + 1e-6:
            return None
        filled, slip_price = self._fill(signal.entry, signal.side)
        risk_dist = abs(filled - signal.stop)
        target = signal.target
        if target is None:
            # Assumption (to confirm): default 2R target; the mandatory stop is never removed.
            target = filled + self.default_rr * risk_dist if signal.side == "long" else filled - self.default_rr * risk_dist
        pos = Position(
            trade_id=f"PAPER-{next(self._ids):04d}",
            strategy=strategy,
            symbol=signal.symbol,
            side=signal.side,
            entry_time=signal.ts,
            entry_price=filled,
            size=qty,
            stop_price=signal.stop,
            stop_on_exchange=True,  # paper simulates a stop resting on the venue
            target=target,
        )
        # The stop is mandatory: this call raises if the adapter did not accept it.
        require_exchange_stop(pos)
        self.positions.setdefault(signal.symbol, []).append(pos)
        self.entry_fees[pos.trade_id] = filled * qty * self._fee_bps() / 10_000
        self.entry_slip[pos.trade_id] = slip_price * qty
        self.entry_risk[pos.trade_id] = sizing["risk_usd"]
        return pos

    def on_bar(self, bar: Bar) -> list[TradeRecord]:
        out: list[TradeRecord] = []
        for pos in list(self.positions.get(bar.symbol, [])):
            exit_price: Optional[float] = None
            reason = "exit"
            if gap_through_stop(bar.open, pos.stop_price, pos.side):
                exit_price = bar.open
                reason = "GAP_THROUGH_STOP"
                self.incidents.append(f"{iso_utc(bar.ts)} gap through stop {pos.trade_id} ({pos.symbol})")
            elif pos.side == "long" and bar.low <= pos.stop_price:
                exit_price = pos.stop_price
                reason = "stop"
            elif pos.side == "short" and bar.high >= pos.stop_price:
                exit_price = pos.stop_price
                reason = "stop"
            elif pos.target is not None and pos.side == "long" and bar.high >= pos.target:
                exit_price = pos.target
                reason = "target"
            elif pos.target is not None and pos.side == "short" and bar.low <= pos.target:
                exit_price = pos.target
                reason = "target"
            elif bar.ts - pos.entry_time > self.max_hold_ms:
                exit_price = bar.close
                reason = "time_exit"
            if exit_price is None:
                continue
            filled, slip_price = self._fill(exit_price, "short" if pos.side == "long" else "long")
            gross = (filled - pos.entry_price) * pos.size * (1 if pos.side == "long" else -1)
            fee = self.entry_fees.pop(pos.trade_id, 0.0) + filled * pos.size * self._fee_bps() / 10_000
            slip_usd = self.entry_slip.pop(pos.trade_id, 0.0) + slip_price * pos.size
            funding = self._funding(pos, bar.ts)
            pnl = gross - fee - slip_usd - funding
            # R is computed after ALL costs (fees, slippage, funding), divided by the
            # dollar risk taken at entry — not by the raw price distance.
            risk = self.entry_risk.pop(pos.trade_id, 0.0)
            r = pnl / risk if risk > 0 else 0.0
            rec = TradeRecord(
                trade_id=pos.trade_id,
                strategy=pos.strategy,
                market=pos.symbol,
                side=pos.side,
                entry_time=iso_utc(pos.entry_time),
                entry_price=pos.entry_price,
                exit_time=iso_utc(bar.ts),
                exit_price=filled,
                size=pos.size,
                stop_price=pos.stop_price,
                R_multiple=r,
                fee_usd=fee,
                slippage_usd=slip_usd,
                funding_usd=funding,
                pnl_usd=pnl,
                notes=f"paper; {reason}; risk_usd={risk:.4f}",
            )
            self._equity += pnl
            self.closed.append(rec)
            self.positions[bar.symbol].remove(pos)
            if self.on_trade:
                self.on_trade(rec)
            out.append(rec)
        return out

    def _funding(self, pos: Position, exit_ts: int) -> float:
        eight_hours = 8 * 3_600_000
        intervals = max(0, (exit_ts - pos.entry_time) // eight_hours)
        return pos.entry_price * pos.size * self.costs["funding_per_8h"] * intervals


class LiveAdapter(ExchangeAdapter):
    """Locked stub. No venue, keys, orders or withdrawals are implemented here."""

    def __init__(self, cfg: dict):
        assert_live_allowed(cfg)
        raise ApprovalError(
            "live adapter is a stub: no exchange is connected. Complete the playbook "
            "checklist and implement/test a venue adapter with withdrawal disabled."
        )

    def place(self, signal: Signal, sizing: dict, strategy: str) -> Optional[Position]:
        raise ApprovalError("live trading not available")

    def on_bar(self, bar: Bar) -> list[TradeRecord]:
        raise ApprovalError("live trading not available")

    def equity(self) -> float:
        raise ApprovalError("live trading not available")
