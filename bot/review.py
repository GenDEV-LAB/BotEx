"""Paper vs backtest comparison and the first weekly review (kickoff day 7)."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .config import BACKTESTS_DIR, TRADES_CSV, iso_utc
from .journal import write_report


def paper_stats(path: Path = TRADES_CSV) -> dict[str, dict[str, float]]:
    if not path.exists():
        return {}
    grouped: dict[str, list[dict]] = defaultdict(list)
    with open(path, "r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            grouped[row["strategy"]].append(row)
    out: dict[str, dict[str, float]] = {}
    for strategy, rows in grouped.items():
        rs = [float(r["R_multiple"]) for r in rows]
        pnls = [float(r["pnl_usd"]) for r in rows]
        slips = [float(r["slippage_usd"]) for r in rows]
        out[strategy] = {
            "trades": len(rows),
            "pnl_usd": round(sum(pnls), 4),
            "expectancy_R": round(sum(rs) / len(rs), 4),
            "win_rate": round(sum(1 for r in rs if r > 0) / len(rs), 4),
            "avg_slippage_usd": round(sum(slips) / len(slips), 6),
        }
    return out


def latest_backtest(strategy: str) -> dict | None:
    files = sorted(BACKTESTS_DIR.glob("combined-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("strategy") == strategy:
            return data
    return None


def compare() -> dict[str, Any]:
    stats = paper_stats()
    rows = []
    for strategy, p in stats.items():
        b = latest_backtest(strategy)
        rows.append({
            "strategy": strategy,
            "paper": p,
            "backtest": ({"trades": b["trades"], "pnl_usd": b["pnl_usd"],
                          "expectancy_R": b["expectancy_R"]} if b else None),
            "delta_expectancy_R": (round(p["expectancy_R"] - b["expectancy_R"], 4) if b else None),
        })
    def fmt_row(r: dict) -> str:
        b = r["backtest"]
        bt = f"{b['expectancy_R']:.3f}" if b else "n/a"
        delta = f"{r['delta_expectancy_R']:+.3f}" if r["delta_expectancy_R"] is not None else "n/a"
        return (f"| {r['strategy']} | {r['paper']['trades']} | {r['paper']['pnl_usd']:.2f} "
                f"| {r['paper']['expectancy_R']:.3f} | {bt} | {delta} |")

    body = "\n".join([
        f"Date UTC : {iso_utc()}",
        "Comparaison paper / backtest. Données paper issues de `trades.csv` (smoke test synthétique).",
        "",
        "| stratégie | trades paper | P&L paper | expectancy paper | expectancy backtest | delta |",
        "|---|---|---|---|---|---|",
        *[fmt_row(r) for r in rows],
        "",
        "Un écart important signale un problème de slippage, de fills ou de logique :",
        "investiguer avant tout passage en live.",
    ])
    path = write_report("paper-vs-backtest", body)
    return {"compared_at_utc": iso_utc(), "rows": rows, "report": str(path)}


def weekly() -> dict[str, Any]:
    stats = paper_stats()
    total_trades = sum(v["trades"] for v in stats.values())
    total_pnl = round(sum(v["pnl_usd"] for v in stats.values()), 4)
    body = "\n".join([
        f"Semaine se terminant le {iso_utc()}",
        f"Trades : {total_trades} · P&L USD : {total_pnl} · source : SYNTHETIQUE, pas une preuve.",
        *[f"- {s}: {v['trades']} trades, expectancy {v['expectancy_R']:.3f} R, slippage moyen {v['avg_slippage_usd']:.4f} USD"
          for s, v in stats.items()],
        "",
        "Revue : trades, P&L, live vs backtest (live indisponible), slippage, ce qui a cassé.",
        "Règles modifiées cette semaine : aucune. Le playbook n'est mis à jour qu'après approbation.",
        "Champion en titre : aucun (effectifs insuffisants). Challengers : voir leaderboard.",
    ])
    path = write_report("weekly-review", body)
    return {"reviewed_at_utc": iso_utc(), "trades": total_trades, "pnl_usd": total_pnl, "report": str(path)}
