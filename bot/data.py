"""Data loading, integrity checks and a clearly-labelled synthetic generator."""

from __future__ import annotations

import csv
import hashlib
import math
import random
from pathlib import Path
from typing import Iterable

from .models import Bar

INTERVAL_MS = {"5m": 300_000, "15m": 900_000, "30m": 1_800_000, "1h": 3_600_000, "4h": 14_400_000}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_bars(path: Path) -> list[Bar]:
    bars: list[Bar] = []
    with open(path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {"ts", "symbol", "open", "high", "low", "close", "volume"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path}: missing columns {sorted(required - set(reader.fieldnames or []))}")
        for row in reader:
            bar = Bar(
                symbol=row["symbol"],
                ts=int(row["ts"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )
            bar.validate()
            bars.append(bar)
    return bars


def write_bars(path: Path, bars: Iterable[Bar]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ts", "symbol", "open", "high", "low", "close", "volume"])
        for b in bars:
            writer.writerow([b.ts, b.symbol, b.open, b.high, b.low, b.close, b.volume])


def integrity_issues(bars: list[Bar], interval_ms: int, symbol: str | None = None) -> list[str]:
    """Return a list of problems. An empty list means the series passed the checks."""
    issues: list[str] = []
    if not bars:
        return ["no bars"]
    subset = [b for b in bars if symbol is None or b.symbol == symbol]
    if not subset:
        return [f"no bars for {symbol}"]
    ts = [b.ts for b in subset]
    if ts != sorted(ts):
        issues.append("timestamps are not sorted ascending")
    if len(set(ts)) != len(ts):
        issues.append("duplicate timestamps")
    gaps = [(b.ts - a.ts) for a, b in zip(subset, subset[1:]) if b.ts - a.ts > 2 * interval_ms]
    if gaps:
        issues.append(f"{len(gaps)} gaps larger than 2 intervals (max {max(gaps)} ms)")
    for b in subset:
        try:
            b.validate()
        except ValueError as exc:
            issues.append(str(exc))
            break
    return issues


def prices_match(a: float, b: float, tolerance_bps: float = 5.0) -> bool:
    """Two independent sources must agree before a price can be trusted."""
    if min(a, b) <= 0:
        return False
    return abs(a - b) / ((a + b) / 2) * 10_000 <= tolerance_bps


def sources_registered(sources_md: Path, min_sources: int = 2) -> bool:
    """Count non-placeholder rows in the sources registry."""
    if not sources_md.exists():
        return False
    rows = 0
    for line in sources_md.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or "---" in line or "dataset_id" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0] not in ("", "—", "-") and len(cells) > 2 and cells[1] not in ("", "—"):
            rows += 1
    return rows >= min_sources


def generate_synthetic(
    symbol: str,
    count: int = 2000,
    interval_ms: int = INTERVAL_MS["1h"],
    seed: int = 42,
    start_ms: int | None = None,
    regimes: bool = True,
) -> list[Bar]:
    """Deterministic synthetic OHLCV. NEVER a substitute for verified market data."""
    rng = random.Random(seed)
    start = start_ms or 1_700_000_000_000
    price = 100.0
    bars: list[Bar] = []
    for i in range(count):
        phase = (i // 240) % 4 if regimes else 0
        drift = [0.0004, -0.0006, 0.0001, -0.0002][phase]
        vol = [0.006, 0.014, 0.004, 0.009][phase]
        shock = rng.gauss(drift, vol)
        nxt = max(0.01, price * math.exp(shock))
        o = price
        c = nxt
        wick = abs(rng.gauss(0, vol)) * price
        h = max(o, c) + wick
        low = min(o, c) - abs(rng.gauss(0, vol)) * price
        bar = Bar(symbol, start + i * interval_ms, o, h, max(0.01, low), c, 1000 + rng.random() * 500)
        bar.validate()
        bars.append(bar)
        price = c
    return bars


def write_synthetic(path: Path, symbol: str, count: int, interval_ms: int, seed: int) -> list[Bar]:
    bars = generate_synthetic(symbol, count, interval_ms, seed)
    write_bars(path, bars)
    return bars
