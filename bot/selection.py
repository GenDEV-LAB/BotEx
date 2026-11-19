"""Pass bar for promoting a strategy (section 6 of the prompt).

A strategy is promoted only when every gate is met. With synthetic data every run
fails the verified-source and history gates by construction.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .backtest import buy_hold_benchmark
from .config import ROOT, BACKTESTS_DIR, iso_utc
from .data import sources_registered
from .models import BacktestResult


def risk_adjusted(result: BacktestResult) -> float:
    if result.max_drawdown_pct <= 0:
        return 0.0
    return result.pnl_usd / result.max_drawdown_pct


def evaluate(
    result: BacktestResult,
    cfg: dict,
    bars: list,
    synthetic: bool = True,
    stress_result: BacktestResult | None = None,
) -> dict[str, Any]:
    benchmark = buy_hold_benchmark(bars, cfg, synthetic=synthetic)
    verified = sources_registered(ROOT / "data" / "sources.md", cfg["data"]["min_sources_for_price"])
    checks = {
        "verified_two_sources": verified,
        "history_4y_with_bear_market": (not synthetic) and cfg["data"]["lookback_years"] >= 4,
        "out_of_sample_trades_50": result.trades >= cfg["backtest"]["min_out_of_sample_trades"],
        "walk_forward_combined_test": "wf-test" in result.run_id or "combined" in result.run_id,
        "profitable_after_all_costs": result.pnl_usd > 0,
        "drawdown_within_limit": result.max_drawdown_pct <= cfg["kill_switch_drawdown_pct"],
        "beats_buy_hold_risk_adjusted": risk_adjusted(result) > risk_adjusted(benchmark),
        "profitable_under_stress": (stress_result.pnl_usd > 0) if stress_result else False,
    }
    return {
        "strategy": result.strategy,
        "evaluated_at_utc": iso_utc(),
        "synthetic": synthetic,
        "checks": checks,
        "passed": all(checks.values()),
        "benchmark": {
            "pnl_usd": round(benchmark.pnl_usd, 4),
            "max_drawdown_pct": round(benchmark.max_drawdown_pct, 2),
            "risk_adjusted": round(risk_adjusted(benchmark), 4),
        },
        "strategy_risk_adjusted": round(risk_adjusted(result), 4),
    }


def write_report(evaluations: list[dict[str, Any]]) -> Path:
    lines = [
        "# Pass bar — sélection des stratégies",
        "",
        f"Évalué le {iso_utc()}. Toutes les cases cochées sont requises.",
        "",
        "| stratégie | sources | historique | 50+ trades OOS | walk-forward | profitable | drawdown | > buy&hold | stress | VERDICT |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    keys = ("verified_two_sources", "history_4y_with_bear_market", "out_of_sample_trades_50",
            "walk_forward_combined_test", "profitable_after_all_costs", "drawdown_within_limit",
            "beats_buy_hold_risk_adjusted", "profitable_under_stress")
    for e in evaluations:
        cells = ["✅" if e["checks"][k] else "❌" for k in keys]
        lines.append(f"| {e['strategy']} | " + " | ".join(cells) + f" | {'PASS' if e['passed'] else 'REJECTED'} |")
    lines += ["", "Données synthétiques : aucun verdict PASS n'est possible sans sources vérifiées.", ""]
    path = ROOT / "strategies" / "selection.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
