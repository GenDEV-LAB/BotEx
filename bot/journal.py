"""Append-only journals: trades, lessons, incidents, backtests and reports."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .config import BACKTESTS_DIR, INCIDENTS_MD, LEARNING_MD, REPORTS_DIR, TRADES_CSV, iso_utc
from .models import BacktestResult, TradeRecord

FIELDS = [
    "trade_id", "strategy", "market", "side", "entry_time", "entry_price", "exit_time",
    "exit_price", "size", "stop_price", "R_multiple", "fee_usd", "slippage_usd",
    "funding_usd", "pnl_usd", "notes",
]


def append_trade(rec: TradeRecord, path: Path = TRADES_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with open(path, "a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow(rec.as_row())


def append_lesson(text: str, path: Path = LEARNING_MD) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"| {iso_utc()} | {text.strip()} | ⏳ en attente d'approbation |\n")


def append_incident(text: str, path: Path = INCIDENTS_MD) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"| {iso_utc()} | warn | {text.strip()} | ouvert |\n")


def save_backtest(result: BacktestResult, directory: Path = BACKTESTS_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{result.run_id}.json"
    path.write_text(json.dumps(result.as_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_report(name: str, body: str, directory: Path = REPORTS_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{iso_utc().replace(':', '-')}-{name}.md"
    path.write_text(f"# {name}\n\n{body}\n", encoding="utf-8")
    return path
