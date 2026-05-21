"""Sanity tests for the long/short perpetual engine."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.backtest.engine import BacktestConfig
from src.backtest.metrics import compute_metrics
from src.robustness.long_short_engine import simulate_long_short


def _ohlcv(prices: list[float], start="2024-01-01") -> pd.DataFrame:
    ts = pd.date_range(start, periods=len(prices), freq="4h", tz="UTC")
    return pd.DataFrame({"ts": ts, "open": prices, "high": prices,
                         "low": prices, "close": prices, "volume": [1.0] * len(prices)})


def _no_funding(ts_index) -> pd.DataFrame:
    return pd.DataFrame({"funding_time": pd.to_datetime([], utc=True), "funding_rate": []})


def test_short_profits_in_downtrend():
    """A short held through a falling market must make money (no funding)."""
    prices = list(np.linspace(100.0, 50.0, 60))  # monotonic down
    df = _ohlcv(prices)
    sig = pd.Series([0] * 60, index=df.index)
    sig.iloc[1] = -1   # go short at bar 1 → fill open[2]
    sig.iloc[55] = 0
    cfg = BacktestConfig(initial_capital=1000.0, fee_per_side=0.0, slippage_per_side=0.0)
    r = simulate_long_short(df, sig, _no_funding(df.index), cfg)
    assert r.final_equity > 1000.0, f"short should profit in downtrend, got {r.final_equity}"


def test_long_loses_in_downtrend():
    """A long held through a falling market must lose money."""
    prices = list(np.linspace(100.0, 50.0, 60))
    df = _ohlcv(prices)
    sig = pd.Series([0] * 60, index=df.index)
    sig.iloc[1] = 1
    cfg = BacktestConfig(initial_capital=1000.0, fee_per_side=0.0, slippage_per_side=0.0)
    r = simulate_long_short(df, sig, _no_funding(df.index), cfg)
    assert r.final_equity < 1000.0


def test_funding_charged_to_long():
    """With positive funding and a flat price, a long bleeds funding."""
    prices = [100.0] * 30
    df = _ohlcv(prices)
    sig = pd.Series([0] * 30, index=df.index)
    sig.iloc[0] = 1  # long from bar 1 onward
    # Positive funding every 8h at 00:00 and 08:00 and 16:00 UTC
    ftime = pd.date_range("2024-01-01", periods=10, freq="8h", tz="UTC")
    funding = pd.DataFrame({"funding_time": ftime, "funding_rate": [0.001] * 10})
    cfg = BacktestConfig(initial_capital=1000.0, fee_per_side=0.0, slippage_per_side=0.0)
    r = simulate_long_short(df, sig, funding, cfg)
    # flat price, positive funding, long pays → equity below start
    assert r.final_equity < 1000.0, f"long should bleed funding, got {r.final_equity}"


def test_short_earns_funding():
    """With positive funding and flat price, a short EARNS funding."""
    prices = [100.0] * 30
    df = _ohlcv(prices)
    sig = pd.Series([0] * 30, index=df.index)
    sig.iloc[0] = -1
    ftime = pd.date_range("2024-01-01", periods=10, freq="8h", tz="UTC")
    funding = pd.DataFrame({"funding_time": ftime, "funding_rate": [0.001] * 10})
    cfg = BacktestConfig(initial_capital=1000.0, fee_per_side=0.0, slippage_per_side=0.0)
    r = simulate_long_short(df, sig, funding, cfg)
    assert r.final_equity > 1000.0, f"short should earn funding, got {r.final_equity}"
