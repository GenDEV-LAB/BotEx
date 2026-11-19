"""Nine strategy families. All functions are causal: they only see bars[:i+1].

A strategy returns a Signal with a mandatory stop, or None. Parameter tuning happens
in walk-forward training windows only; the combined test windows are reported separately.
"""

from __future__ import annotations

from typing import Callable, Optional

from .models import Bar, Signal

SignalFn = Callable[[list[Bar], int, dict], Optional[Signal]]


def sma(values: list[float], period: int) -> Optional[float]:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def ema_series(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    alpha = 2 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * alpha + out[-1] * (1 - alpha))
    return out


def atr(bars: list[Bar], period: int) -> Optional[float]:
    if len(bars) < period + 1:
        return None
    trs = []
    for prev, cur in zip(bars[-period - 1 : -1], bars[-period:]):
        trs.append(max(cur.high - cur.low, abs(cur.high - prev.close), abs(cur.low - prev.close)))
    return sum(trs) / len(trs)


def zscore(values: list[float], period: int) -> Optional[float]:
    if len(values) < period:
        return None
    window = values[-period:]
    mean = sum(window) / period
    var = sum((v - mean) ** 2 for v in window) / period
    if var <= 0:
        return None
    return (values[-1] - mean) / var**0.5


DEFAULT_PARAMS: dict[str, dict] = {
    "trend_following": {"fast": 20, "slow": 50, "atr_stop": 2.0, "min_adx_proxy": 0.0},
    "mean_reversion": {"period": 20, "z_entry": 2.0, "atr_stop": 1.5},
    "breakout_pullback": {"lookback": 20, "atr_stop": 1.5},
    "carry_basis": {"funding_threshold": 0.0005, "ema": 200, "atr_stop": 2.0},
    "relative_value": {"period": 30, "z_entry": 2.0, "atr_stop": 2.0},
    "volatility_breakout": {"lookback": 20, "percentile": 20, "atr_stop": 1.0},
    "cross_sectional_momentum": {"lookback": 12, "top": 2, "atr_stop": 2.0},
    "event_calendar": {"blackout": True},
    "session_momentum": {"lookback": 20, "start_hour": 7, "end_hour": 12, "atr_stop": 1.5},
}


def _atr_stop(bars: list[Bar], side: str, multiplier: float) -> Optional[float]:
    a = atr(bars, 14)
    if a is None:
        return None
    price = bars[-1].close
    return price - multiplier * a if side == "long" else price + multiplier * a


def trend_following(bars: list[Bar], i: int, p: dict) -> Optional[Signal]:
    if i < p["slow"] + 15:
        return None
    window = bars[: i + 1]
    closes = [b.close for b in window]
    fast = ema_series(closes, p["fast"])
    slow = ema_series(closes, p["slow"])
    if fast[-2] <= slow[-2] and fast[-1] > slow[-1]:
        side = "long"
    elif fast[-2] >= slow[-2] and fast[-1] < slow[-1]:
        side = "short"
    else:
        return None
    stop = _atr_stop(window, side, p["atr_stop"])
    if stop is None:
        return None
    return Signal("trend_following", window[-1].symbol, window[-1].ts, side, window[-1].close, stop, "1h", reason="EMA cross")


def mean_reversion(bars: list[Bar], i: int, p: dict) -> Optional[Signal]:
    if i < p["period"] + 15:
        return None
    window = bars[: i + 1]
    z = zscore([b.close for b in window], p["period"])
    if z is None or abs(z) < p["z_entry"]:
        return None
    side = "short" if z > 0 else "long"
    stop = _atr_stop(window, side, p["atr_stop"])
    if stop is None:
        return None
    return Signal("mean_reversion", window[-1].symbol, window[-1].ts, side, window[-1].close, stop, "15m", reason=f"z={z:.2f}")


def breakout_pullback(bars: list[Bar], i: int, p: dict) -> Optional[Signal]:
    if i < p["lookback"] + 15:
        return None
    window = bars[: i + 1]
    prior = window[-p["lookback"] - 1 : -1]
    high, low = max(b.high for b in prior), min(b.low for b in prior)
    last = window[-1]
    if last.close > high:
        side = "long"
    elif last.close < low:
        side = "short"
    else:
        return None
    stop = _atr_stop(window, side, p["atr_stop"])
    if stop is None:
        return None
    return Signal("breakout_pullback", last.symbol, last.ts, side, last.close, stop, "1h", reason="range breakout")


def carry_basis(bars: list[Bar], i: int, p: dict) -> Optional[Signal]:
    if i < p["ema"] + 15:
        return None
    window = bars[: i + 1]
    closes = [b.close for b in window]
    ema = ema_series(closes, p["ema"])[-1]
    funding = float(p.get("funding_rate", p["funding_threshold"] * 1.5))
    side = None
    if funding > p["funding_threshold"] and closes[-1] > ema:
        side = "long"
    elif funding < -p["funding_threshold"] and closes[-1] < ema:
        side = "short"
    if side is None:
        return None
    stop = _atr_stop(window, side, p["atr_stop"])
    if stop is None:
        return None
    return Signal("carry_basis", window[-1].symbol, window[-1].ts, side, window[-1].close, stop, "4h", reason=f"funding={funding:.5f}")


def relative_value(bars: list[Bar], i: int, p: dict) -> Optional[Signal]:
    other = p.get("other_bars")
    if other is None or i >= len(other) or i < p["period"] + 15:
        return None
    window = bars[: i + 1]
    other_by_ts = {b.ts: b.close for b in other}
    spread = [b.close - other_by_ts.get(b.ts, b.close) for b in window]
    z = zscore(spread, p["period"])
    if z is None or abs(z) < p["z_entry"]:
        return None
    side = "long" if z < 0 else "short"  # buy the laggard, sell the leader
    stop = _atr_stop(window, side, p["atr_stop"])
    if stop is None:
        return None
    return Signal("relative_value", window[-1].symbol, window[-1].ts, side, window[-1].close, stop, "1h", reason=f"spread z={z:.2f}")


def volatility_breakout(bars: list[Bar], i: int, p: dict) -> Optional[Signal]:
    if i < p["lookback"] * 2 + 15:
        return None
    window = bars[: i + 1]
    ranges = [b.high - b.low for b in window[-p["lookback"] * 2 :]]
    current = ranges[-1]
    threshold = sorted(ranges[-p["lookback"] :])[max(0, len(ranges[-p["lookback"] :]) * p["percentile"] // 100)]
    if current <= threshold:
        return None
    side = "long" if window[-1].close > window[-2].close else "short"
    stop = _atr_stop(window, side, p["atr_stop"])
    if stop is None:
        return None
    return Signal("volatility_breakout", window[-1].symbol, window[-1].ts, side, window[-1].close, stop, "1h", reason="ATR compression then expansion")


def cross_sectional_momentum(bars: list[Bar], i: int, p: dict) -> Optional[Signal]:
    universe: dict[str, list[Bar]] = p.get("universe_bars", {})
    if len(universe) < 4 or i < p["lookback"] + 15:
        return None
    scores = []
    current_ts = bars[-1].ts
    step = bars[-1].ts - bars[-2].ts if len(bars) > 1 else 3_600_000
    for sym, series in universe.items():
        by_ts = {b.ts: b.close for b in series}
        cur = by_ts.get(current_ts)
        past = by_ts.get(current_ts - p["lookback"] * step)
        if not cur or not past:
            continue
        scores.append((cur / past - 1, sym, series))
    if len(scores) < 4:
        return None
    scores.sort()
    current_symbol = bars[-1].symbol
    if current_symbol == scores[-1][1] and p["top"] > 0:
        side = "long"
    elif current_symbol == scores[0][1] and p["top"] > 0:
        side = "short"
    else:
        return None
    stop = _atr_stop(bars[: i + 1], side, p["atr_stop"])
    if stop is None:
        return None
    return Signal("cross_sectional_momentum", current_symbol, bars[-1].ts, side, bars[-1].close, stop, "4h", reason="cross-sectional rank")


def event_calendar(bars: list[Bar], i: int, p: dict) -> Optional[Signal]:
    """A rule, not a trade: no entries inside the blackout window."""
    if not p.get("blackout", True):
        return None
    return None


def session_momentum(bars: list[Bar], i: int, p: dict) -> Optional[Signal]:
    from datetime import datetime, timezone

    hour = datetime.fromtimestamp(bars[-1].ts / 1000, tz=timezone.utc).hour
    if not (p["start_hour"] <= hour < p["end_hour"]):
        return None
    if i < p["lookback"] + 15:
        return None
    window = bars[: i + 1]
    prior = window[-p["lookback"] - 1 : -1]
    high, low = max(b.high for b in prior), min(b.low for b in prior)
    last = window[-1]
    if last.close > high:
        side = "long"
    elif last.close < low:
        side = "short"
    else:
        return None
    stop = _atr_stop(window, side, p["atr_stop"])
    if stop is None:
        return None
    return Signal("session_momentum", last.symbol, last.ts, side, last.close, stop, "15m", reason="London session range breakout")


REGISTRY: dict[str, SignalFn] = {
    "trend_following": trend_following,
    "mean_reversion": mean_reversion,
    "breakout_pullback": breakout_pullback,
    "carry_basis": carry_basis,
    "relative_value": relative_value,
    "volatility_breakout": volatility_breakout,
    "cross_sectional_momentum": cross_sectional_momentum,
    "event_calendar": event_calendar,
    "session_momentum": session_momentum,
}
