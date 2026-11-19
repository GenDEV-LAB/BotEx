"""Configuration and the live-trading gate.

The configuration mirrors playbook.md. Secrets are never read from this file;
only environment variables on the server may hold API keys.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "bot" / "config.json"
APPROVALS_DIR = ROOT / "approvals"
TRADES_CSV = ROOT / "trades.csv"
CLEAN_DIR = ROOT / "data" / "clean"
RAW_DIR = ROOT / "data" / "raw"
SOURCES_MD = ROOT / "data" / "sources.md"
BACKTESTS_DIR = ROOT / "backtests"
STRATEGIES_DIR = ROOT / "strategies"
REPORTS_DIR = ROOT / "reports"
LEARNING_MD = ROOT / "learning.md"
INCIDENTS_MD = ROOT / "incidents.md"
PLAYBOOK_MD = ROOT / "playbook.md"


class ApprovalError(RuntimeError):
    """Raised when an action needs the owner's explicit approval."""


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        cfg = json.load(fh)
    if cfg.get("risk_per_trade_pct", 0) > 1:
        raise ValueError("risk per trade above the mandate (1%)")
    if cfg.get("max_daily_loss_pct", 0) > 5:
        raise ValueError("daily loss limit above the mandate (5%)")
    if cfg.get("kill_switch_drawdown_pct", 0) > 10:
        raise ValueError("kill switch above the mandate (10% drawdown)")
    if cfg.get("data", {}).get("allow_real_symbols") and not cfg.get("data", {}).get("sources_verified"):
        raise ValueError("real symbols require verified sources in data/sources.md")
    return cfg


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(ts_ms: int | None = None) -> str:
    if ts_ms is None:
        return now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ms_utc(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def is_approval_window(cfg: dict[str, Any], when: datetime | None = None) -> bool:
    when = when or now_utc()
    start, end = cfg["approval_window_utc"]
    fmt = "%H:%M"
    t = when.strftime(fmt)
    return datetime.strptime(start, fmt).time() <= when.time() <= datetime.strptime(end, fmt).time()


def assert_live_allowed(cfg: dict[str, Any]) -> None:
    """Two independent keys are required: a signed file and an env variable.

    Even then this repository's LiveAdapter is a stub: no real venue is connected.
    """
    if cfg.get("mode", "paper") != "live":
        return
    if os.environ.get("BOTEX_LIVE_APPROVAL") != "GO_LIVE":
        raise ApprovalError("live mode blocked: BOTEX_LIVE_APPROVAL=GO_LIVE is missing")
    signed = [p for p in APPROVALS_DIR.glob("go_live-*.md") if "J'autorise" in p.read_text(encoding="utf-8")]
    if not signed:
        raise ApprovalError("live mode blocked: no signed approval file in approvals/")
    for key in ("new_market", "strategy_swap", "leverage_change", "rule_change"):
        if key not in cfg.get("approvals_required", []):
            raise ApprovalError(f"live mode blocked: {key} missing from approvals_required")


def mode(cfg: dict[str, Any]) -> str:
    assert_live_allowed(cfg)
    return cfg.get("mode", "paper")
