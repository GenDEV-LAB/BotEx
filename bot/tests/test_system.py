"""Unit tests. All market data here is synthetic and clearly labelled."""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from bot.backtest import buy_hold_benchmark, run_backtest, walk_forward
from bot.config import ApprovalError, assert_live_allowed, is_approval_window, load_config
from bot.data import (
    INTERVAL_MS,
    generate_synthetic,
    integrity_issues,
    prices_match,
    write_bars,
)
from bot.events import Event, is_blackout, position_scale
from bot.feeds import CsvFeed, register_dataset, verify_sources
from bot.exchange import PaperAdapter
from bot.review import paper_stats
from bot.selection import evaluate
from bot.state import RuntimeState, apply_to_risk, from_risk, load_state, save_state
from bot.models import Bar, Signal
from bot.risk import RiskEngine, gap_through_stop, position_size, require_exchange_stop


class TestRisk(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()

    def test_position_size_uses_stop_distance(self):
        a = position_size(1000, 1, 100, 99, 5, 5, 5)
        b = position_size(1000, 1, 100, 95, 5, 5, 5)
        self.assertGreater(a["qty"], b["qty"])  # wider stop -> smaller size
        self.assertLessEqual(a["notional_usd"], 1000 * 5)

    def test_leverage_cap(self):
        r = position_size(1000, 50, 100, 99.9, 5, 5, 2)
        self.assertTrue(r["capped_by_leverage"])
        self.assertLessEqual(r["notional_usd"], 2000 + 1e-6)

    def test_daily_loss_blocks_entries(self):
        r = RiskEngine(equity=1000)
        r.update_equity(948)  # -5.2% from day start
        ok, reason = r.can_open()
        self.assertFalse(ok)
        self.assertIn("daily loss", reason)

    def test_kill_switch_and_hwm(self):
        r = RiskEngine(equity=1000, kill_switch_pct=10)
        r.update_equity(1200)
        r.update_equity(1080)  # -10% from HWM
        self.assertTrue(r.kill_switch)
        self.assertFalse(r.can_open()[0])

    def test_stop_required_and_gap(self):
        pos = type("P", (), {"trade_id": "x", "symbol": "SIM01", "stop_on_exchange": False})()
        with self.assertRaises(RuntimeError):
            require_exchange_stop(pos)
        self.assertTrue(gap_through_stop(98, 100, "long"))
        self.assertFalse(gap_through_stop(101, 100, "long"))


class TestData(unittest.TestCase):
    def test_integrity_detects_duplicates_and_bad_ohlc(self):
        t = 1_700_000_000_000
        bars = [
            Bar("SIM01", t, 10, 11, 9, 10.5, 1),
            Bar("SIM01", t, 10, 11, 9, 10.5, 1),
            Bar("SIM01", t + INTERVAL_MS["1h"] * 10, 10, 8, 9, 10.5, 1),
        ]
        issues = integrity_issues(bars, INTERVAL_MS["1h"])
        self.assertTrue(any("duplicate" in i for i in issues))
        self.assertTrue(any("gap" in i for i in issues))
        self.assertTrue(any("OHLC" in i for i in issues))

    def test_two_source_price_match(self):
        self.assertTrue(prices_match(100, 100.02, 5))
        self.assertFalse(prices_match(100, 101, 5))

    def test_synthetic_is_deterministic(self):
        a = generate_synthetic("SIM01", 50, seed=1)
        b = generate_synthetic("SIM01", 50, seed=1)
        self.assertEqual([x.close for x in a], [x.close for x in b])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.csv"
            write_bars(path, a)
            self.assertEqual(len(path.read_text().splitlines()), 51)


class TestExecution(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()

    def test_signal_requires_stop(self):
        with self.assertRaises(ValueError):
            Signal("s", "SIM01", 1, "long", 100, 101, "1h")
        Signal("s", "SIM01", 1, "long", 100, 99, "1h")

    def test_paper_stops_and_costs(self):
        adapter = PaperAdapter(self.cfg, equity=1000)
        sig = Signal("trend_following", "SIM01", 1_700_000_000_000, "long", 100, 98, "1h")
        sizing = position_size(1000, 1, 100, 98, 5, 5, 5)
        adapter.place(sig, sizing, "trend_following")
        t = 1_700_000_000_000
        adapter.on_bar(Bar("SIM01", t + 3_600_000, 99.5, 100.5, 99.0, 100.2, 1))
        self.assertEqual(len(adapter.closed), 0)
        trades = adapter.on_bar(Bar("SIM01", t + 7_200_000, 99.0, 99.2, 97.5, 98.0, 1))
        self.assertEqual(len(trades), 1)
        self.assertLess(trades[0].pnl_usd, 0)
        self.assertGreater(trades[0].fee_usd, 0)
        self.assertGreater(trades[0].slippage_usd, 0)

    def test_gap_through_stop_logged(self):
        adapter = PaperAdapter(self.cfg, equity=1000)
        sig = Signal("s", "SIM01", 1_700_000_000_000, "long", 100, 98, "1h")
        adapter.place(sig, position_size(1000, 1, 100, 98, 5, 5, 5), "s")
        trades = adapter.on_bar(Bar("SIM01", 1_700_000_003_600, 95, 96, 94, 95, 1))
        self.assertEqual(len(trades), 1)
        self.assertTrue(any("gap" in i for i in adapter.incidents))

    def test_backtest_is_labelled_synthetic(self):
        bars = generate_synthetic("SIM01", 600, INTERVAL_MS["1h"], seed=3)
        result = run_backtest(bars, "trend_following", load_config(), synthetic=True)
        self.assertTrue(result.synthetic)
        self.assertEqual(result.as_dict()["verdict"], "NOT_EVIDENCE")
        self.assertIsInstance(result.pnl_usd, float)
        self.assertGreaterEqual(result.trades, 0)

    def test_walk_forward_returns_test_windows_only(self):
        cfg = load_config()
        cfg["backtest"]["walk_forward_tune_months"] = 1
        cfg["backtest"]["walk_forward_test_months"] = 1
        bars = generate_synthetic("SIM01", 3000, INTERVAL_MS["4h"], seed=5)
        windows = walk_forward(bars, "trend_following", cfg, synthetic=True)
        self.assertGreaterEqual(len(windows), 1)
        for w in windows:
            self.assertIn("wf-test", w.run_id)


class TestApprovals(unittest.TestCase):
    def test_live_blocked_without_approval(self):
        cfg = load_config()
        cfg["mode"] = "live"
        os.environ.pop("BOTEX_LIVE_APPROVAL", None)
        with self.assertRaises(ApprovalError):
            assert_live_allowed(cfg)

    def test_approval_window(self):
        cfg = load_config()
        self.assertTrue(is_approval_window(cfg, datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)))
        self.assertFalse(is_approval_window(cfg, datetime(2026, 1, 1, 3, 0, tzinfo=timezone.utc)))


class TestEventsAndReview(unittest.TestCase):
    def test_blackout_window(self):
        cfg = load_config()
        t = 1_700_000_000_000
        events = [Event(t, "CPI", "BLS")]
        self.assertTrue(is_blackout(t - 29 * 60_000, cfg, events))
        self.assertTrue(is_blackout(t, cfg, events))
        self.assertTrue(is_blackout(t + 29 * 60_000, cfg, events))
        self.assertFalse(is_blackout(t + 31 * 60_000, cfg, events))

    def test_no_invented_events(self):
        self.assertEqual(events_load_count(), 0)

    def test_paper_stats_aggregates_costs(self):
        import csv
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trades.csv"
            with open(path, "w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["trade_id", "strategy", "market", "side", "entry_time", "entry_price",
                            "exit_time", "exit_price", "size", "stop_price", "R_multiple",
                            "fee_usd", "slippage_usd", "funding_usd", "pnl_usd", "notes"])
                w.writerow(["T1", "s", "SIM01", "long", "t", 100, "t2", 101, 1, 99,
                            -0.5, 0.1, 0.2, 0.0, -5.0, "SYNTHETIC"])
                w.writerow(["T2", "s", "SIM01", "long", "t", 100, "t2", 102, 1, 99,
                            1.0, 0.1, 0.2, 0.0, 10.0, "SYNTHETIC"])
            stats = paper_stats(path)["s"]
            self.assertEqual(stats["trades"], 2)
            self.assertEqual(stats["pnl_usd"], 5.0)
            self.assertEqual(stats["expectancy_R"], 0.25)


def events_load_count():
    from bot.events import load_events
    return len(load_events())




class TestPersistenceAndGates(unittest.TestCase):
    def test_state_roundtrip_preserves_kill_switch(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            state = load_state(path, load_config())
            engine = RiskEngine(1000)
            engine.update_equity(890)
            from_risk(engine, state)
            save_state(state, path)
            restored = load_state(path, load_config())
            self.assertTrue(restored.kill_switch)
            engine2 = RiskEngine(1000)
            apply_to_risk(restored, engine2)
            self.assertTrue(engine2.kill_switch)
            self.assertFalse(engine2.can_open()[0])

    def test_half_size_after_event(self):
        cfg = load_config()
        t = 1_700_000_000_000
        events = [Event(t, "CPI", "BLS")]
        self.assertEqual(position_scale(t - 29 * 60_000, cfg, events), 1.0)
        self.assertEqual(position_scale(t + 31 * 60_000, cfg, events), 0.5)
        self.assertEqual(position_scale(t + 3 * 24 * 3_600_000, cfg, events), 1.0)

    def test_selection_gates_reject_synthetic(self):
        cfg = load_config()
        bars = generate_synthetic("SIM01", 300, INTERVAL_MS["4h"], seed=9)
        result = run_backtest(bars, "trend_following", cfg, synthetic=True)
        verdict = evaluate(result, cfg, bars, synthetic=True)
        self.assertFalse(verdict["passed"])
        self.assertFalse(verdict["checks"]["verified_two_sources"])

    def test_buy_hold_benchmark_includes_costs(self):
        bars = generate_synthetic("SIM01", 100, INTERVAL_MS["4h"], seed=11)
        bench = buy_hold_benchmark(bars, load_config())
        self.assertGreater(bench.fees_usd, 0)
        self.assertGreater(bench.slippage_usd, 0)
        self.assertTrue(bench.synthetic)

    def test_telegram_pending_approval(self):
        import bot.telegram as telegram
        with tempfile.TemporaryDirectory() as tmp:
            old_pending, old_decided = telegram.PENDING, telegram.DECIDED
            telegram.PENDING = Path(tmp) / "pending.md"
            telegram.DECIDED = Path(tmp) / "decisions.md"
            try:
                telegram.queue_approval("test1", "tester", "impact")
                self.assertEqual(len(telegram.list_pending()), 1)
                telegram.resolve_approval("test1", True)
                self.assertEqual(telegram.list_pending(), [])
                self.assertIn("test1", telegram.DECIDED.read_text(encoding="utf-8"))
            finally:
                telegram.PENDING, telegram.DECIDED = old_pending, old_decided




class TestFeeds(unittest.TestCase):
    def test_csv_feed_and_registry(self):
        cfg = load_config()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bars = generate_synthetic("SIM01", 40, INTERVAL_MS["1h"], seed=13)
            data_path = root / "SIM01.csv"
            write_bars(data_path, bars)
            feed = CsvFeed(data_path)
            fetched = feed.fetch("SIM01", "1h", bars[10].ts, 5)
            self.assertEqual(len(fetched), 5)
            registry = root / "sources.md"
            registry.write_text("| dataset_id | source | URL | symbols | timeframe | couverture UTC | sha256 | récupéré à | licence | contrôles |\n"
                                "|---|---|---|---|---|---|---|---|---|---|\n", encoding="utf-8")
            entry = register_dataset(data_path, "test", "local", "SIM01", "1h", "40 bars", "n/a", registry)
            self.assertEqual(len(entry["sha256"]), 64)
            self.assertIn("SIM01.csv", registry.read_text(encoding="utf-8"))
            self.assertTrue(verify_sources(100, 100.02, cfg))
            self.assertFalse(verify_sources(100, 101, cfg))




class TestWatchlist(unittest.TestCase):
    def test_xauusd_registered_but_blocked(self):
        cfg = load_config()
        item = next(i for i in cfg["watchlist"] if i["symbol"] == "XAUUSD")
        self.assertTrue(item["spot"])
        self.assertFalse(item["short_allowed"])
        self.assertEqual(item["status"], "LOCAL_PAPER")
        self.assertEqual(item["synthetic_proxy"], "SIMXAU")

    def test_instrument_command_lists_blockers(self):
        import argparse
        from bot.cli import cmd_instrument, cmd_make_synthetic
        result = cmd_instrument(load_config(), argparse.Namespace(symbol="XAUUSD"))
        self.assertTrue(any("data source" in b for b in result["blockers"]))
        with self.assertRaises(ValueError):
            cmd_make_synthetic(load_config(), argparse.Namespace(symbol="XAUUSD", bars=10))




if __name__ == "__main__":
    unittest.main()
