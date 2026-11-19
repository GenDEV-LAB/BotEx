"""Telegram check-in and approvals (section 16).

No network call is made unless TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set on the
server. Tokens are never written to files or logs. Approvals are stored as plain text
decisions; no money movement is implemented here.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .config import APPROVALS_DIR, iso_utc
from .notify import send

PENDING = APPROVALS_DIR / "pending.md"
DECIDED = APPROVALS_DIR / "decisions.md"
OFFSET = APPROVALS_DIR / "telegram_offset.txt"


def queue_approval(approval_id: str, request: str, impact: str) -> None:
    pending = list_pending()
    pending = [row for row in pending if row["id"] != approval_id]
    pending.append({"id": approval_id, "request": request, "impact": impact, "queued": iso_utc()})
    _write_pending(pending)


def list_pending() -> list[dict[str, str]]:
    if not PENDING.exists():
        return []
    rows = []
    for line in PENDING.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or "---" in line or line.startswith("| id "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4:
            rows.append(dict(zip(("id", "request", "impact", "queued"), cells)))
    return rows


def _write_pending(rows: list[dict[str, str]]) -> None:
    lines = ["| id | demande | impact | queued |", "|---|---|---|---|"]
    lines += [f"| {r['id']} | {r['request']} | {r['impact']} | {r['queued']} |" for r in rows]
    PENDING.write_text("\n".join(lines) + "\n", encoding="utf-8")


def resolve_approval(approval_id: str, approved: bool, decided_by: str = "owner") -> str:
    rows = list_pending()
    target = next((r for r in rows if r["id"] == approval_id), None)
    if target is None:
        return f"approval {approval_id} not found"
    _write_pending([r for r in rows if r["id"] != approval_id])
    with open(DECIDED, "a", encoding="utf-8") as fh:
        fh.write(f"| {iso_utc()} | {approval_id} | {'YES' if approved else 'NO'} | {decided_by} |\n")
    return f"approval {approval_id}: {'APPROVED' if approved else 'REJECTED'}"


def _api(method: str, payload: dict[str, Any]) -> dict | None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return None
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def poll_commands(cfg: dict, limit: int = 10) -> list[str]:
    """Poll new commands and apply them. Returns the answers sent (or printed)."""
    if not cfg.get("notifications", {}).get("telegram_enabled"):
        return ["Telegram désactivé dans la configuration (paper local)."]
    offset = int(OFFSET.read_text(encoding="utf-8").strip() or 0) if OFFSET.exists() else 0
    response = _api("getUpdates", {"offset": offset, "timeout": 5, "limit": limit})
    if not response or not response.get("ok"):
        return ["Telegram non configuré ou API indisponible."]

    answers: list[str] = []
    for update in response.get("result", []):
        offset = max(offset, update["update_id"] + 1)
        msg = update.get("message", {})
        text = (msg.get("text") or "").strip()
        parts = text.split()
        if not parts:
            continue
        cmd = parts[0].lower()
        if cmd == "/status":
            answer = f"BotEx {iso_utc()} · pending approvals: {len(list_pending())}"
        elif cmd == "/approvals" or cmd == "/help":
            answer = "\n".join(f"{r['id']} — {r['request']} — impact: {r['impact']}" for r in list_pending()) or "Aucune approbation en attente."
        elif cmd in ("/yes", "/no") and len(parts) >= 2:
            answer = resolve_approval(parts[1], cmd == "/yes")
        else:
            answer = "Commandes: /status /approvals /yes <id> /no <id>"
        answers.append(answer)
        send(answer, cfg)
    OFFSET.parent.mkdir(parents=True, exist_ok=True)
    OFFSET.write_text(str(offset), encoding="utf-8")
    return answers
