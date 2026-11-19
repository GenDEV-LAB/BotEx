"""UTC structured logging. Never log API keys or secrets."""

from __future__ import annotations

import logging
from pathlib import Path

from .config import ROOT


def setup(level: int = logging.INFO) -> None:
    log_dir = ROOT / "reports"
    log_dir.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)sZ %(levelname)s %(name)s %(message)s")
    formatter.converter = __import__("time").gmtime
    file_handler = logging.FileHandler(log_dir / "bot.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logging.basicConfig(level=level, handlers=[file_handler, stream], force=True)
