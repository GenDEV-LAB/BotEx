"""Event blackout enforcement (section 10 of the prompt).

Events must be registered with an exact UTC timestamp and a named official source.
No row means no scheduled blackout; the bot never invents an event date.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .config import ROOT


@dataclass(frozen=True)
class Event:
    ts_ms: int
    label: str
    source: str


def load_events(path: Path = ROOT / "data" / "events.csv") -> list[Event]:
    if not path.exists():
        return []
    events: list[Event] = []
    with open(path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                ts = int(datetime.strptime(row["ts_utc"].strip(), "%Y-%m-%dT%H:%M:%SZ")
                         .replace(tzinfo=timezone.utc).timestamp() * 1000)
            except (ValueError, KeyError, TypeError):
                raise ValueError(f"invalid event timestamp in {path}: {row}")
            if not row.get("source", "").strip():
                raise ValueError(f"event without an official source in {path}: {row}")
            events.append(Event(ts, row["label"].strip(), row["source"].strip()))
    return sorted(events, key=lambda e: e.ts_ms)


def is_blackout(ts_ms: int, cfg: dict, events: list[Event] | None = None) -> bool:
    events = load_events() if events is None else events
    window = cfg.get("event_blackout_minutes", {"before": 30, "after": 30})
    before = window["before"] * 60_000
    after = window["after"] * 60_000
    return any(e.ts_ms - before <= ts_ms <= e.ts_ms + after for e in events)


def upcoming(events: list[Event], now_ms: int, limit: int = 5) -> list[Event]:
    return [e for e in events if e.ts_ms >= now_ms][:limit]


def position_scale(ts_ms: int, cfg: dict, events: list[Event] | None = None) -> float:
    """After an event: wait 15 min, then trade at half size until the UTC day ends.

    Section 10 of the prompt, applied as a global rule to every strategy.
    """
    events = load_events() if events is None else events
    window = cfg.get("event_blackout_minutes", {"after": 30, "post_release_wait": 15})
    wait = window["post_release_wait"] * 60_000
    after = window["after"] * 60_000
    for e in events:
        resume = e.ts_ms + max(after, wait)
        if ts_ms < resume:
            continue
        end = datetime.fromtimestamp(e.ts_ms / 1000, tz=timezone.utc).replace(
            hour=23, minute=59, second=59, microsecond=999000)
        if ts_ms <= int(end.timestamp() * 1000):
            return 0.5
    return 1.0
