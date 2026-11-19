"""Une seule commande, un seul rapport lisible. Tout est paper, rien n'est connecté."""

from __future__ import annotations

from . import loop, telegram
from .config import iso_utc, load_config


def run() -> str:
    cfg = load_config()
    r = loop.run_once(cfg, notify=False)
    research = r["research"]
    paper = r["paper"]
    monitor = r["monitor"]
    eligible = [x for x in research["results"] if x["trades"] >= 20]
    best = max(eligible or research["results"], key=lambda x: x["expectancy_R"])
    pending = len(telegram.list_pending())

    lines = [
        "BotEx — rapport paper",
        f"Date UTC : {iso_utc()}",
        "",
        f"Stratégies testées : {research['strategies']} · sources vérifiées : {r['status']['verified_sources']}",
        f"Meilleure stratégie : {best['strategy']} ({best['trades']} trades synthétiques)",
        f"Paper : {paper['trades_closed']} trades · equity {paper['equity_usd']:.2f} USD · kill-switch {'OUI' if paper['kill_switch'] else 'non'}",
        f"Stratégies validées pour le live : {research['passed_strategies']}",
        f"Robustesse : {'stable' if r['robustness']['stable_sign_across_variants'] else 'instable'} — aucune preuve",
        "",
        f"Alertes : {len(monitor['alerts'])}",
        *[f"  - {a}" for a in monitor["alerts"]],
        "",
        f"Approbations en attente : {pending}",
        "Mode : PAPER. Aucun compte, aucune clé, aucun ordre réel.",
        "",
        f"Rapport complet : {r['report']}",
    ]
    text = "\n".join(lines)
    print(text)
    return text
