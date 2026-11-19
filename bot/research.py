"""Nightly research: backtests with costs, private leaderboard and a short brief.

Before real data is connected this runs a clearly-labelled synthetic smoke test.
Learning proposals are written as proposals only; rules are never auto-changed.
"""

from __future__ import annotations

import hashlib
from copy import deepcopy
from typing import Any

from . import strategies
from .backtest import combine, run_backtest, walk_forward
from .config import ROOT, STRATEGIES_DIR, iso_utc
from .data import INTERVAL_MS, generate_synthetic, sources_registered
from .journal import append_lesson, save_backtest, write_report
from .models import BacktestResult
from .notify import send
from .selection import evaluate, write_report as write_selection_report
from .telegram import list_pending, queue_approval


def _synthetic_bars(cfg: dict, count: int = 1500) -> list:
    symbol = cfg["data"]["synthetic_symbols"][0]
    return generate_synthetic(symbol, count, INTERVAL_MS["4h"], seed=42)


def _data_fingerprint(bars: list) -> str:
    payload = f"{bars[0].ts}|{bars[-1].ts}|{bars[0].close}|{bars[-1].close}|SIM01".encode()
    return hashlib.sha256(payload).hexdigest()


def leaderboard_markdown(results: list[BacktestResult], synthetic: bool) -> str:
    lines = [
        "# Leaderboard privé",
        "",
        f"Généré le {iso_utc()} · source : "
        + ("**SYNTHETIQUE — SMOKE TEST, PAS UNE PREUVE**" if synthetic else "données vérifiées")
        + ". Coûts inclus : fees, slippage, funding.",
        "",
        "| rang | stratégie | trades | P&L USD | expectancy R | pire R | max DD % | verdict |",
        "|---|---|---|---|---|---|---|---|",
    ]
    ordered = sorted(results, key=lambda r: (r.trades >= 50, r.expectancy_R, r.pnl_usd), reverse=True)
    for n, r in enumerate(ordered, 1):
        verdict = "NOT_EVIDENCE (synthétique)"
        if r.trades < 50:
            verdict += " · <50 trades, non significatif"
        lines.append(
            f"| {n} | {r.strategy} | {r.trades} | {r.pnl_usd:.2f} | {r.expectancy_R:.3f} | "
            f"{r.worst_R:.3f} | {r.max_drawdown_pct:.2f} | {verdict} |"
        )
    lines += [
        "",
        "Une poignée de trades est du bruit : la barre des 50 trades hors-échantillon n'est pas validée ici.",
        "Pass bar (section 6) : 4+ années dont un marché baissier, 50+ trades hors-échantillon,",
        "walk-forward 12m tune / 3m test, profitable après coûts, drawdown dans la limite,",
        "meilleur que buy & hold risk-adjusted. Aucune stratégie ne l'a encore franchi.",
    ]
    return "\n".join(lines) + "\n"


def nightly(cfg: dict, notify: bool = True) -> dict[str, Any]:
    verified = sources_registered(ROOT / "data" / "sources.md", cfg["data"]["min_sources_for_price"])
    bars = _synthetic_bars(cfg)
    fingerprint = _data_fingerprint(bars)
    results: list[BacktestResult] = []
    stress_results: dict[str, BacktestResult] = {}

    for name in strategies.REGISTRY:
        result = run_backtest(bars, name, cfg, synthetic=not verified, data_sha256=fingerprint)
        save_backtest(result)
        results.append(result)
        stress = run_backtest(bars, name, cfg, synthetic=not verified, data_sha256=fingerprint, stress=True)
        stress_results[name] = stress
        save_backtest(stress)

    # Walk-forward is exercised with compressed windows for the synthetic smoke test.
    # Real validation MUST use 12m tune / 3m test from config (see playbook).
    wf_cfg = deepcopy(cfg)
    if not verified:
        wf_cfg["backtest"]["walk_forward_tune_months"] = 1
        wf_cfg["backtest"]["walk_forward_test_months"] = 1
    top = sorted(results, key=lambda r: r.expectancy_R, reverse=True)[:2]
    wf_summaries: list[dict[str, Any]] = []
    for r in top:
        windows = walk_forward(bars, r.strategy, wf_cfg, synthetic=not verified, data_sha256=fingerprint)
        combined = combine(windows, r.strategy, synthetic=not verified)
        save_backtest(combined)
        wf_summaries.append({
            "strategy": r.strategy,
            "windows": len(windows),
            "trades": combined.trades,
            "pnl_usd": round(combined.pnl_usd, 4),
            "worst_R": round(combined.worst_R, 4),
            "note": ("compressed 1m/1m windows — smoke test only" if not verified
                     else "12m/3m combined test windows"),
        })

    (STRATEGIES_DIR / "leaderboard.md").write_text(
        leaderboard_markdown(results, synthetic=not verified), encoding="utf-8"
    )

    evaluations = [
        evaluate(r, cfg, bars, synthetic=not verified, stress_result=stress_results[r.strategy])
        for r in results
    ]
    selection_report = write_selection_report(evaluations)

    if not any(r["id"] == "window_utc" for r in list_pending()):
        queue_approval(
            "window_utc",
            "Confirmer la fenêtre d'approbation 08:00-20:00 UTC",
            "Hors fenêtre, aucune règle ni taille ni marché ne peut être modifié ; le live reste verrouillé.",
        )

    best = max(results, key=lambda r: r.expectancy_R)
    brief = [
        f"Date UTC : {iso_utc()}",
        "Statut : **paper / données synthétiques** — aucune preuve de performance.",
        f"Stratégies évaluées : {len(results)} · meilleur expectancy R : {best.strategy} {best.expectancy_R:.3f} "
        f"sur {best.trades} trades ({'non significatif, <50 trades' if best.trades < 50 else 'effectif suffisant'})",
        f"Pire trade du meilleur : {best.worst_R:.3f} R · max drawdown : {best.max_drawdown_pct:.2f} %",
        "Meilleur trade : non pertinent sur données synthétiques. Pire trade : voir leaderboard.",
        "Live vs paper vs backtest : live indisponible (aucun compte connecté).",
        "Une seule proposition du jour : confirmer la fenêtre d'approbation 08:00–20:00 UTC.",
        "Approbation demandée : oui (fenêtre UTC) — /yes window_utc ou /no window_utc.",
        "",
        "Walk-forward (fenêtres combinées) :",
        *[f"- {w['strategy']}: {w}" for w in wf_summaries],
    ]
    path = write_report("nightly-research", "\n".join(brief))
    append_lesson("recherche nocturne : fenêtre d'approbation 08:00–20:00 UTC à confirmer")
    if notify:
        send(f"Brief BotEx ({iso_utc()}) : {len(results)} stratégies testées en synthétique. "
             "Aucune preuve. Une approbation attendue : fenêtre UTC 08:00–20:00.", cfg)
    return {
        "data_source": "SYNTHETIC_SMOKE_TEST" if not verified else "verified",
        "sha256": fingerprint,
        "strategies": len(results),
        "results": [r.as_dict() for r in results],
        "walk_forward": wf_summaries,
        "leaderboard": str(STRATEGIES_DIR / "leaderboard.md"),
        "selection_report": str(selection_report),
        "passed_strategies": sum(1 for e in evaluations if e["passed"]),
        "report": str(path),
    }
