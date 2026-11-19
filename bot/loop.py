"""One orchestrated nightly cycle: research -> paper -> learning -> report."""

from __future__ import annotations

from typing import Any

from . import events, monitor, paper, research, review, robustness, schedule
from .config import iso_utc, load_config
from .data import sources_registered
from .journal import write_report
from .config import ROOT


def run_once(cfg: dict | None = None, notify: bool = True) -> dict[str, Any]:
    cfg = cfg or load_config()
    status = {
        "mode": cfg["mode"],
        "capital_usd": cfg["capital_usd"],
        "risk_per_trade_pct": cfg["risk_per_trade_pct"],
        "daily_loss_pct": cfg["max_daily_loss_pct"],
        "kill_switch_pct": cfg["kill_switch_drawdown_pct"],
        "max_leverage": cfg["max_leverage"],
        "verified_sources": sources_registered(ROOT / "data" / "sources.md", cfg["data"]["min_sources_for_price"]),
        "data_issues": [] if sources_registered(ROOT / "data" / "sources.md", cfg["data"]["min_sources_for_price"]) else ["no verified dataset loaded — synthetic smoke test only"],
    }
    research_result = research.nightly(cfg, notify=notify)
    paper_result = paper.paper_cycle(cfg, notify=notify)
    monitor_result = monitor.run(cfg)
    eligible = [r for r in research_result["results"] if r["trades"] >= 20]
    best = max(eligible or research_result["results"], key=lambda r: r["expectancy_R"])
    robustness_result = robustness.run(cfg, strategy=best["strategy"])
    comparison = review.compare()
    weekly = review.weekly()
    next_task = schedule.next_task(cfg)

    body = "\n".join([
        f"Date UTC : {iso_utc()}",
        f"Statut : {status['mode']} · sources vérifiées : {status['verified_sources']}",
        f"Recherche : {research_result['strategies']} stratégies · source {research_result['data_source']}",
        f"Paper : equity {paper_result['equity_usd']} USD · trades {paper_result['trades_closed']} · kill-switch {paper_result['kill_switch']}",
        f"Monitoring : {len(monitor_result['alerts'])} alerte(s)",
        f"Robustesse ({best['strategy']}) : signe stable = {robustness_result['stable_sign_across_variants']} ; {robustness_result['verdict']}",
        f"Paper vs backtest : {comparison['report']}",
        f"Revue hebdomadaire : {weekly['report']}",
        f"Prochaine tâche UTC : {next_task['time_utc']} — {next_task['task']}",
        "Meilleur trade : non mesuré en réel · Pire trade : non mesuré en réel",
        "P&L : données synthétiques, pas une preuve",
        "Levier et max trades/jour : confirmés le 2026-11-18 (5x / 5 trades)",
        "Une leçon : confirmer la fenêtre d'approbation 08:00–20:00 UTC",
        "Approbation demandée : oui (fenêtre UTC)",
    ])
    report = write_report("daily", body)
    return {
        "status": status,
        "research": research_result,
        "paper": paper_result,
        "monitor": monitor_result,
        "robustness": robustness_result,
        "comparison": comparison,
        "weekly": weekly,
        "next_task": next_task,
        "report": str(report),
    }


def compact(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": result["status"]["mode"],
        "verified_sources": result["status"]["verified_sources"],
        "strategies_tested": result["research"]["strategies"],
        "paper_trades": result["paper"]["trades_closed"],
        "paper_equity_usd": result["paper"]["equity_usd"],
        "alerts": result["monitor"]["alerts"],
        "robustness_stable": result["robustness"]["stable_sign_across_variants"],
        "strategies_passing_bar": result["research"]["passed_strategies"],
        "next_task_utc": result["next_task"]["time_utc"],
        "report": result["report"],
    }
