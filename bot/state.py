"""Persistent runtime state: equity, high-water mark, kill switch, open positions.

Written atomically so a crash or a VPS restart cannot reset risk limits. Secrets are
never stored here: this file holds no keys, no credentials and no personal data.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import ROOT, iso_utc


STATE_PATH = ROOT / "state.json"


@dataclass
class RuntimeState:
    version: int = 1
    updated_at_utc: str = ""
    mode: str = "paper"
    equity_usd: float = 1000.0
    high_water_mark_usd: float = 1000.0
    day_start_equity_usd: float = 1000.0
    current_day: str = ""
    trades_today: int = 0
    kill_switch: bool = False
    blocked_reason: str = ""
    open_positions: list[dict[str, Any]] = field(default_factory=list)
    last_report_utc: str = ""


def load_state(path: Path = STATE_PATH, cfg: dict | None = None) -> RuntimeState:
    capital = float(cfg["capital_usd"]) if cfg else 1000.0
    mode = cfg.get("mode", "paper") if cfg else "paper"
    if not path.exists():
        return RuntimeState(equity_usd=capital, high_water_mark_usd=capital,
                            day_start_equity_usd=capital, mode=mode,
                            current_day=datetime.now(timezone.utc).date().isoformat())
    data = json.loads(path.read_text(encoding="utf-8"))
    state = RuntimeState(**{k: v for k, v in data.items() if k in RuntimeState.__dataclass_fields__})
    state.mode = mode  # the config, not a stale file, decides the mode
    return state


def save_state(state: RuntimeState, path: Path = STATE_PATH) -> None:
    state.updated_at_utc = iso_utc()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".state-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(asdict(state), fh, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def from_risk(engine, state: RuntimeState, positions: list[dict] | None = None) -> RuntimeState:
    state.equity_usd = engine.equity
    state.high_water_mark_usd = engine.hwm
    state.day_start_equity_usd = engine.day_start_equity
    state.current_day = engine.current_day
    state.trades_today = engine.trades_today
    state.kill_switch = engine.kill_switch
    state.blocked_reason = engine.blocked_reason
    if positions is not None:
        state.open_positions = positions
    return state


def apply_to_risk(state: RuntimeState, engine) -> None:
    """Restore risk limits after a restart; never re-enable a tripped kill switch."""
    engine.equity = state.equity_usd
    engine.hwm = max(state.high_water_mark_usd, state.equity_usd)
    engine.day_start_equity = state.day_start_equity_usd
    engine.current_day = state.current_day
    engine.trades_today = state.trades_today
    engine.kill_switch = state.kill_switch
    engine.blocked_reason = state.blocked_reason
