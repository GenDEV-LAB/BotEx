"""Notifications. Telegram is optional and disabled by default; no secrets in files."""

from __future__ import annotations

import json
import os
import urllib.request


def send(message: str, cfg: dict) -> bool:
    """Print locally; send to Telegram only if explicitly configured.

    Returns True when a Telegram message was actually delivered.
    """
    print(message)
    if not cfg.get("notifications", {}).get("telegram_enabled"):
        return False
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat, "text": message[:4000]}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as exc:  # network problem: log, never crash the bot silently
        print(f"telegram delivery failed: {type(exc).__name__}")
        return False


def alert_immediately(message: str, cfg: dict) -> None:
    """Kill switch, missing stop, exchange problem: escalate at once."""
    send(f"ALERTE IMMEDIATE — {message}", cfg)
