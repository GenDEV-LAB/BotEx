"""Daily schedule from section 9, expressed in UTC (owner window 08:00-20:00 assumed)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .config import is_approval_window


TASKS = [
    ("00:00", "Heartbeat, lecture des positions, contrôle des arrêts et du kill-switch"),
    ("07:45", "Brief du matin : P&L, trades, alertes, leçon du jour, test de ce soir"),
    ("08:00", "Health check : bot en ligne, mode paper, horloge UTC, solde cohérent"),
    ("08:15", "Calendrier économique : marquer les événements, règles de pause, fenêtre d'approbation"),
    ("12:00", "Contrôle de mi-journée : staleness des données, fills, slippage, limites"),
    ("16:00", "Session de l'après-midi : stratégies adaptées au régime uniquement"),
    ("20:00", "Recherche nocturne : backtests avec coûts, walk-forward, leaderboard"),
    ("20:30", "Comparer paper et backtest ; journaliser ce qui a cassé"),
    ("21:00", "Scoreboard, une leçon écrite sous forme de règle, proposition d'approbation"),
]


def daily_schedule(cfg: dict, when: datetime | None = None) -> list[dict[str, Any]]:
    when = when or datetime.now(timezone.utc)
    return [
        {"time_utc": t, "task": task,
         "owner_approval_window": is_approval_window(cfg, when)} for t, task in TASKS
    ]


def next_task(cfg: dict, when: datetime | None = None) -> dict[str, Any]:
    when = when or datetime.now(timezone.utc)
    current = when.strftime("%H:%M")
    for entry in daily_schedule(cfg, when):
        if entry["time_utc"] > current:
            return entry
    return daily_schedule(cfg, when)[0]
