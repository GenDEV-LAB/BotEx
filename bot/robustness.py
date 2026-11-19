"""Robustness tests for the surviving strategies (kickoff day 4).

A strategy that only works with one parameter set, one seed or one cost assumption
is rejected. Every run is saved with its settings; synthetic runs are not evidence.
"""

from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .backtest import run_backtest
from .config import BACKTESTS_DIR, ROOT, iso_utc
from .data import INTERVAL_MS, generate_synthetic


def run(cfg: dict, strategy: str = "trend_following", bars: list | None = None,
        synthetic: bool = True) -> dict[str, Any]:
    bars = bars or generate_synthetic("SIM01", 1500, INTERVAL_MS["4h"], seed=42)
    variants: list[dict[str, Any]] = []

    def add(label: str, local_cfg: dict, params: dict | None = None, series: list | None = None) -> None:
        res = run_backtest(series or bars, strategy, local_cfg, params=params, synthetic=synthetic,
                           stress=(label == "slippage_x2"))
        variants.append({
            "variant": label,
            "trades": res.trades,
            "pnl_usd": round(res.pnl_usd, 4),
            "expectancy_R": round(res.expectancy_R, 4),
            "worst_R": round(res.worst_R, 4),
            "max_drawdown_pct": round(res.max_drawdown_pct, 2),
            "run_id": res.run_id,
        })

    base_cfg = deepcopy(cfg)
    add("base", base_cfg)

    fee_cfg = deepcopy(cfg)
    fee_cfg["costs"]["fee_bps_per_side_perps"] *= 2
    add("fees_x2", fee_cfg)

    add("slippage_x2", deepcopy(cfg))  # run_backtest applies the stress multiplier

    for label, params in (
        ("atr_stop_1.5", {"atr_stop": 1.5}),
        ("atr_stop_2.5", {"atr_stop": 2.5}),
        ("faster_ema", {"fast": 15, "slow": 40}),
        ("slower_ema", {"fast": 25, "slow": 60}),
    ):
        add(label, deepcopy(cfg), params)

    for seed in (7, 101, 202):
        other = generate_synthetic("SIM01", len(bars), INTERVAL_MS["4h"], seed=seed,
                                   start_ms=bars[0].ts if bars else None)
        add(f"seed_{seed}", deepcopy(cfg), None, other)

    signs = [1 if v["expectancy_R"] > 0 else -1 if v["expectancy_R"] < 0 else 0 for v in variants]
    stable = all(s == signs[0] for s in signs) and signs[0] != 0
    result = {
        "generated_at_utc": iso_utc(),
        "strategy": strategy,
        "source": "SYNTHETIC_SMOKE_TEST — not evidence" if synthetic else "verified data",
        "stable_sign_across_variants": stable,
        "variants": variants,
        "verdict": "PENDING: requires verified data and 50+ out-of-sample trades",
    }
    run_id = f"robustness-{strategy}-{time.time_ns()}"
    BACKTESTS_DIR.mkdir(parents=True, exist_ok=True)
    (BACKTESTS_DIR / f"{run_id}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        f"# Robustesse — {strategy}",
        "",
        f"Généré le {result['generated_at_utc']} · {result['source']}",
        "",
        "| variante | trades | P&L USD | expectancy R | pire R | max DD % |",
        "|---|---|---|---|---|---|",
    ]
    for v in variants:
        lines.append(f"| {v['variant']} | {v['trades']} | {v['pnl_usd']:.2f} | {v['expectancy_R']:.3f} "
                     f"| {v['worst_R']:.3f} | {v['max_drawdown_pct']:.2f} |")
    lines += ["", f"Signe stable sur toutes les variantes : **{stable}**.",
              "Ce test ne valide aucune stratégie : données synthétiques, effectifs insuffisants.", ""]
    (ROOT / "strategies" / "robustness.md").write_text("\n".join(lines), encoding="utf-8")
    result["run_id"] = run_id
    result["report"] = str(ROOT / "strategies" / "robustness.md")
    return result
