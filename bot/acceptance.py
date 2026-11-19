"""Final acceptance check for the development hand-off.

Verifies structure, golden rules, unit tests and that the main CLI commands run.
It never connects to a venue and never enables live mode.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from .config import ROOT, load_config

REQUIRED = [
    "playbook.md", "calendar.md", "ideas.md", "trades.csv", "learning.md", "incidents.md",
    "data/raw/README.md", "data/clean/README.md", "data/sources.md", "data/events.csv",
    "strategies/README.md", "strategies/leaderboard.md", "strategies/robustness.md",
    "strategies/selection.md", "bot/config.json", "howto.md", "README.md",
    "approvals/README.md",
]


def run() -> dict[str, Any]:
    cfg = load_config()
    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    check("section 15 file structure", not missing, f"missing: {missing}" if missing else "all present")

    check("paper mode", cfg["mode"] == "paper", cfg["mode"])
    check("real symbols disabled", not cfg["data"]["allow_real_symbols"])
    check("exchange stop mandatory", cfg["risk_rules"]["exchange_stop_required"])
    check("risk limits", cfg["risk_per_trade_pct"] <= 1 and cfg["max_daily_loss_pct"] <= 5
          and cfg["kill_switch_drawdown_pct"] <= 10)
    check("approved limits recorded", cfg.get("max_leverage_confirmed") and cfg.get("max_trades_per_day") == 5)
    no_go_live = not list((ROOT / "approvals").glob("go_live-*.md"))
    check("no go-live approval file", no_go_live)

    for command in ("status", "check-data", "events", "schedule", "review"):
        proc = subprocess.run([sys.executable, "-m", "bot.cli", "--json", command],
                              cwd=ROOT, capture_output=True, text=True, timeout=120)
        check(f"cli {command}", proc.returncode == 0, proc.stderr.strip()[:200])

    proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "bot/tests"],
                          cwd=ROOT, capture_output=True, text=True, timeout=300)
    check("unit tests", proc.returncode == 0, proc.stderr.strip()[-300:])

    passed = sum(1 for c in checks if c["ok"])
    return {"passed": passed, "total": len(checks), "all_ok": passed == len(checks), "checks": checks}
