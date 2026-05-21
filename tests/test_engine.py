"""Tests for backtest engine + metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.backtest.engine import (
    BacktestConfig,
    simulate,
    simulate_buy_and_hold,
)
from src.backtest.metrics import compute_metrics


def _flat_ohlcv(n: int, price: float = 100.0) -> pd.DataFrame:
    ts = pd.date_range("2024-01-01", periods=n, freq="4h", tz="UTC")
    return pd.DataFrame(
        {
            "ts": ts,
            "open": [price] * n,
            "high": [price] * n,
            "low": [price] * n,
            "close": [price] * n,
            "volume": [1.0] * n,
        }
    )


def _trending_up_ohlcv(n: int) -> pd.DataFrame:
    ts = pd.date_range("2024-01-01", periods=n, freq="4h", tz="UTC")
    prices = np.linspace(100.0, 200.0, n)
    return pd.DataFrame(
        {
            "ts": ts,
            "open": prices,
            "high": prices,
            "low": prices,
            "close": prices,
            "volume": [1.0] * n,
        }
    )


def test_no_signal_no_change():
    """No signals → equity stays at initial (only mark-to-market, no trades)."""
    df = _flat_ohlcv(50)
    sig = pd.Series([0] * 50, index=df.index)
    r = simulate(df, sig)
    assert r.final_equity == pytest.approx(100.0)
    assert len(r.trades) == 0


def test_buy_then_sell_pnl_positive_uptrend():
    """BUY at bar 1, SELL at bar 30 in uptrend → PnL > 0 net of fees."""
    df = _trending_up_ohlcv(50)
    sig = pd.Series([0] * 50, index=df.index)
    sig.iloc[1] = 1  # signal at bar 1 → fill open[2]
    sig.iloc[30] = -1  # signal at bar 30 → fill open[31]
    r = simulate(df, sig, BacktestConfig(slippage_per_side=0.0, fee_per_side=0.0))
    assert len(r.trades) == 1
    assert r.trades[0].pnl_usd > 0
    # Price ~doubled, position_pct=0.40 → expected gain ~ 0.40 * (~80% rise) ~ 32% on equity.
    assert r.total_return_pct > 0.2


def test_fees_eat_zero_move_trade():
    """In flat market a round-trip should lose ~fees+slippage*2."""
    df = _flat_ohlcv(50)
    sig = pd.Series([0] * 50, index=df.index)
    sig.iloc[1] = 1
    sig.iloc[30] = -1
    cfg = BacktestConfig()  # 0.10% fee, 0.05% slippage per side
    r = simulate(df, sig, cfg)
    # 1 trade, both sides paid → equity below initial.
    assert r.total_return_pct < 0
    assert len(r.trades) == 1


def test_signal_executes_at_next_open_not_close():
    """Verifying fill_mode=next_open: signal at bar t means trade entry_idx = t+1."""
    df = _flat_ohlcv(10)
    sig = pd.Series([0] * 10, index=df.index)
    sig.iloc[3] = 1
    r = simulate(df, sig, BacktestConfig(slippage_per_side=0.0, fee_per_side=0.0))
    assert len(r.trades) == 1
    assert r.trades[0].entry_idx == 4  # next bar


def test_buy_and_hold_baseline():
    """B&H on flat market → equity stays flat (minus fee on entry)."""
    df = _flat_ohlcv(100)
    r = simulate_buy_and_hold(df)
    # One-side fee + slippage applied at entry
    assert r.final_equity < 100.0  # fees eat into it
    assert r.final_equity > 99.0  # but not by much


def test_metrics_smoke():
    df = _trending_up_ohlcv(500)
    sig = pd.Series([0] * 500, index=df.index)
    sig.iloc[10] = 1
    sig.iloc[400] = -1
    r = simulate(df, sig)
    m = compute_metrics(r)
    assert m.n_trades == 1
    assert m.total_return > 0
    assert m.max_drawdown <= 0
    # In linearly uptrending market, our PnL should be > 0 but our sharpe
    # may be modest because returns are flat then jump at entry/exit.
    assert m.final_equity > 100.0


def test_metrics_signal_length_mismatch_raises():
    df = _flat_ohlcv(10)
    sig = pd.Series([0] * 9, index=range(9))
    with pytest.raises(ValueError, match="length"):
        simulate(df, sig)
