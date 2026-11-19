"""Hourly automatic checks (section 11 of the prompt)."""

from __future__ import annotations

from pathlib import Path

from .config import ROOT, TRADES_CSV, assert_live_allowed, iso_utc, now_utc
from .events import is_blackout, load_events, upcoming
from .state import STATE_PATH, load_state
from .data import sources_registered
from .notify import alert_immediately


def hourly_check(cfg: dict) -> list[str]:
    alerts: list[str] = []
    assert_live_allowed(cfg)  # raises if someone enabled live without approval

    if not sources_registered(ROOT / "data" / "sources.md", cfg["data"]["min_sources_for_price"]):
        alerts.append("no verified price sources: trading must stay paper/synthetic")

    if cfg["mode"] != "paper":
        alerts.append(f"unexpected mode {cfg['mode']!r}: verify signed approval")

    if not cfg["risk_rules"]["exchange_stop_required"]:
        alerts.append("CRITICAL: exchange stop requirement disabled")
        alert_immediately("exchange stop requirement is disabled", cfg)

    state_path = Path(str(STATE_PATH))
    if state_path.exists():
        state = load_state(cfg=cfg)
        if state.kill_switch:
            alert_immediately(f"kill switch active since {state.updated_at_utc}: no new entries", cfg)
            alerts.append("kill switch persisted in state.json")
        missing = [p.get("trade_id", "?") for p in state.open_positions if not p.get("stop_on_exchange")]
        if missing:
            alert_immediately(f"missing exchange stops: {missing}", cfg)
            alerts.append(f"reconciliation: {len(missing)} position(s) without exchange stop")

    if not TRADES_CSV.exists() or TRADES_CSV.stat().st_size == 0:
        alerts.append("trades.csv has no rows: no executed trades yet (expected in setup)")

    now_ms = int(now_utc().timestamp() * 1000)
    events = load_events()
    if is_blackout(now_ms, cfg, events):
        alerts.append("event blackout active: no new entries")
    next_events = upcoming(events, now_ms, 1)
    if next_events:
        alerts.append(f"next scheduled event: {next_events[0].label} ({next_events[0].source})")

    heartbeat_file = ROOT / "reports" / "heartbeat.txt"
    if heartbeat_file.exists():
        age_min = (now_utc().timestamp() - heartbeat_file.stat().st_mtime) / 60
        if age_min > 120:
            alert_immediately(f"heartbeat stale ({age_min:.0f} min)", cfg)
            alerts.append("heartbeat stale")

    return alerts


def heartbeat(path: Path = ROOT / "reports" / "heartbeat.txt") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(iso_utc(), encoding="utf-8")


def run(cfg: dict) -> dict:
    alerts = hourly_check(cfg)
    heartbeat()
    return {"checked_at_utc": iso_utc(), "alerts": alerts, "mode": cfg["mode"]}
