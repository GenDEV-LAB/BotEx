"""Market-data feeds and source registration.

Nothing here contacts a venue unless BOTEX_DATA_ENABLED=1 is set explicitly on the
server. Any fetched file is written to data/raw with its source and sha256 registered
in data/sources.md before it can be used by a backtest.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from .config import SOURCES_MD, iso_utc
from .data import prices_match, read_bars, sha256_file
from .models import Bar


class DataFeed(ABC):
    name = "base"

    @abstractmethod
    def fetch(self, symbol: str, timeframe: str, since_ms: int, limit: int,
              dry_run: bool = True) -> list[Bar]:
        ...


class CsvFeed(DataFeed):
    """Read a previously registered, checked CSV file. No network access."""

    def __init__(self, path: Path, name: str = "local-csv"):
        self.path = path
        self.name = name

    def fetch(self, symbol: str, timeframe: str, since_ms: int, limit: int,
              dry_run: bool = True) -> list[Bar]:
        bars = [b for b in read_bars(self.path) if b.symbol == symbol and b.ts >= since_ms]
        return bars[:limit]


class CcxtFeed(DataFeed):
    """Optional CCXT adapter for exchange REST data. Disabled by default.

    Public market data needs no API key. If keys are present they are read from the
    environment only and never logged.
    """

    def __init__(self, exchange_id: str = "binance"):
        self.exchange_id = exchange_id
        self.name = f"ccxt:{exchange_id}"

    def fetch(self, symbol: str, timeframe: str, since_ms: int, limit: int,
              dry_run: bool = True) -> list[Bar]:
        if dry_run:
            return []
        if os.environ.get("BOTEX_DATA_ENABLED") != "1":
            raise RuntimeError("data fetching disabled: set BOTEX_DATA_ENABLED=1 after registering the source")
        try:
            import ccxt  # type: ignore
        except ImportError as exc:
            raise RuntimeError("ccxt is not installed; pip install ccxt on the server") from exc
        exchange = getattr(ccxt, self.exchange_id)({"enableRateLimit": True})
        raw = exchange.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=limit)
        out = []
        for ts, o, h, low, c, vol in raw:
            bar = Bar(symbol, int(ts), float(o), float(h), float(low), float(c), float(vol))
            bar.validate()
            out.append(bar)
        exchange.close()
        return out


def register_dataset(
    path: Path,
    source: str,
    url: str,
    symbol: str,
    timeframe: str,
    coverage_utc: str,
    license_: str,
    sources_md: Path = SOURCES_MD,
) -> dict[str, str]:
    """Append one registry row with a checksum. Duplicate paths are not duplicated."""
    digest = sha256_file(path)
    lines = sources_md.read_text(encoding="utf-8").splitlines() if sources_md.exists() else [
        "| dataset_id | source | URL | symbols | timeframe | couverture UTC | sha256 | récupéré à | licence | contrôles |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    if any(digest in line for line in lines):
        raise ValueError(f"dataset already registered: {path.name}")
    row = (f"| {path.name} | {source} | {url} | {symbol} | {timeframe} | {coverage_utc} | "
           f"{digest} | {iso_utc()} | {license_} | pending |")
    lines.append(row)
    sources_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"dataset_id": path.name, "sha256": digest, "registered_at_utc": iso_utc()}


def verify_sources(price_a: float, price_b: float, cfg: dict) -> bool:
    return prices_match(price_a, price_b, cfg["data"]["price_match_tolerance_bps"])


def save_bars(path: Path, bars: list[Bar]) -> Path:
    from .data import write_bars
    path.parent.mkdir(parents=True, exist_ok=True)
    write_bars(path, bars)
    return path
