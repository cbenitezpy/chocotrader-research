"""Backtest engine for research v6.

Long-only spot, single-pair, fractional position sizing.

Fill model (NON-NEGOTIABLE per ADR-023 §2.5):
    Signal at close[t] → fill at open[t+1] (next_open).
    Fees applied at fill: 0.10% per side (0.20% round-trip default).
    Slippage: 0.05% per side default for BTC/ETH.

Position lifecycle:
    BUY (signal=1) opens a long position with `capital * position_pct` of
    available cash; if already long, BUY is ignored.
    SELL (signal=-1) closes the open position; if flat, SELL is ignored.

Equity tracked bar-by-bar using close prices for mark-to-market.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BacktestConfig:
    """Configuration knobs for the engine.

    Defaults align with ADR-023 §2.5 fill model and constitutional risk
    boundaries (no leverage, long-only).
    """

    initial_capital: float = 100.0  # USD, matches constitution Art. 4 MVP capital
    position_pct: float = 0.40  # 40% of equity per trade (risk.yaml ADR-015)
    fee_per_side: float = 0.0010  # 0.10% per side (no BNB discount)
    slippage_per_side: float = 0.0005  # 0.05% per side, BTC/ETH
    annualization_factor: float = 365.25 * 6  # 4h bars per year
    risk_free_rate: float = 0.0


@dataclass
class Trade:
    """One round-trip trade for accounting."""

    entry_idx: int
    entry_ts: pd.Timestamp
    entry_price: float
    exit_idx: int | None = None
    exit_ts: pd.Timestamp | None = None
    exit_price: float | None = None
    qty: float = 0.0
    fees_paid: float = 0.0
    pnl_usd: float = 0.0

    @property
    def is_closed(self) -> bool:
        return self.exit_idx is not None

    @property
    def return_pct(self) -> float:
        if not self.is_closed or self.entry_price == 0:
            return 0.0
        return (self.exit_price - self.entry_price) / self.entry_price


@dataclass
class BacktestResult:
    """Output of a backtest run."""

    config: BacktestConfig
    equity_curve: pd.Series  # indexed by ts
    trades: list[Trade]
    final_equity: float
    total_return_pct: float
    metadata: dict[str, Any] = field(default_factory=dict)


def _apply_fill_price(price: float, side: str, slippage: float) -> float:
    """Apply slippage to fill price. BUY pays up, SELL pays down."""
    if side == "BUY":
        return price * (1.0 + slippage)
    if side == "SELL":
        return price * (1.0 - slippage)
    raise ValueError(f"unknown side {side!r}")


def simulate(
    ohlcv: pd.DataFrame,
    signal: pd.Series,
    config: BacktestConfig | None = None,
) -> BacktestResult:
    """Run a signal through the backtest engine.

    Args:
        ohlcv: DataFrame with cols ``ts, open, high, low, close, volume``.
            ``ts`` must be tz-aware UTC and ascending.
        signal: int Series in {-1, 0, 1} indexed identically to ohlcv.
        config: BacktestConfig (defaults applied if None).

    Returns:
        BacktestResult with equity_curve, trades, metadata.

    Raises:
        ValueError on schema mismatches.
    """
    if config is None:
        config = BacktestConfig()
    if not {"ts", "open", "high", "low", "close"}.issubset(ohlcv.columns):
        raise ValueError("ohlcv missing required columns")
    if len(signal) != len(ohlcv):
        raise ValueError("signal length differs from ohlcv length")
    if not ohlcv["ts"].is_monotonic_increasing:
        raise ValueError("ohlcv ts must be monotonic ascending")

    n = len(ohlcv)
    ts = ohlcv["ts"].to_numpy()
    opens = ohlcv["open"].to_numpy(dtype=float)
    closes = ohlcv["close"].to_numpy(dtype=float)
    sigs = signal.to_numpy(dtype=int)

    cash = config.initial_capital
    qty_held = 0.0
    equity = np.zeros(n, dtype=float)
    trades: list[Trade] = []
    open_trade: Trade | None = None
    # Pending action: signal observed at bar t; we act at open[t+1].
    pending_action: int = 0
    pending_ts: pd.Timestamp | None = None

    for i in range(n):
        # 1. Execute pending action AT open[i] (from signal observed at i-1).
        if pending_action != 0:
            if pending_action == 1 and qty_held == 0:
                # BUY
                fill_px = _apply_fill_price(opens[i], "BUY", config.slippage_per_side)
                trade_cash = cash * config.position_pct
                gross_qty = trade_cash / fill_px
                fee = trade_cash * config.fee_per_side
                cash -= trade_cash
                cash -= 0  # fee already embedded? No, charge separately:
                cash -= fee
                qty_held += gross_qty
                open_trade = Trade(
                    entry_idx=i,
                    entry_ts=pd.Timestamp(ts[i]),
                    entry_price=fill_px,
                    qty=gross_qty,
                    fees_paid=fee,
                )
            elif pending_action == -1 and qty_held > 0:
                # SELL — close full position
                fill_px = _apply_fill_price(opens[i], "SELL", config.slippage_per_side)
                proceeds = qty_held * fill_px
                fee = proceeds * config.fee_per_side
                cash += proceeds - fee
                if open_trade is not None:
                    open_trade.exit_idx = i
                    open_trade.exit_ts = pd.Timestamp(ts[i])
                    open_trade.exit_price = fill_px
                    open_trade.fees_paid += fee
                    open_trade.pnl_usd = (
                        qty_held * (fill_px - open_trade.entry_price)
                        - open_trade.fees_paid
                    )
                    trades.append(open_trade)
                    open_trade = None
                qty_held = 0.0
            pending_action = 0
            pending_ts = None

        # 2. Mark-to-market AT close[i]
        equity[i] = cash + qty_held * closes[i]

        # 3. Observe signal at close[i], queue for next bar
        if sigs[i] != 0:
            pending_action = int(sigs[i])
            pending_ts = pd.Timestamp(ts[i])

    # If still holding at the end, close at last close (so equity is realised
    # but no trade is left dangling).
    if qty_held > 0 and open_trade is not None:
        fill_px = closes[-1]  # no slippage on synthetic close-out
        fee = qty_held * fill_px * config.fee_per_side
        cash += qty_held * fill_px - fee
        open_trade.exit_idx = n - 1
        open_trade.exit_ts = pd.Timestamp(ts[-1])
        open_trade.exit_price = fill_px
        open_trade.fees_paid += fee
        open_trade.pnl_usd = (
            qty_held * (fill_px - open_trade.entry_price) - open_trade.fees_paid
        )
        trades.append(open_trade)
        qty_held = 0.0
        equity[-1] = cash

    equity_curve = pd.Series(equity, index=pd.DatetimeIndex(ts, name="ts"), name="equity")
    final = float(equity_curve.iloc[-1])
    total_ret = (final - config.initial_capital) / config.initial_capital
    return BacktestResult(
        config=config,
        equity_curve=equity_curve,
        trades=trades,
        final_equity=final,
        total_return_pct=total_ret,
        metadata={
            "n_bars": n,
            "n_trades_closed": len(trades),
        },
    )


def simulate_buy_and_hold(
    ohlcv: pd.DataFrame,
    config: BacktestConfig | None = None,
) -> BacktestResult:
    """B&H baseline — buy at open[0], hold to close[-1].

    Fees applied at entry only (one-side); slippage at entry.
    """
    if config is None:
        config = BacktestConfig()
    n = len(ohlcv)
    ts = ohlcv["ts"].to_numpy()
    opens = ohlcv["open"].to_numpy(dtype=float)
    closes = ohlcv["close"].to_numpy(dtype=float)

    fill_px = _apply_fill_price(opens[0], "BUY", config.slippage_per_side)
    fee = config.initial_capital * config.fee_per_side
    cash_after_fee = config.initial_capital - fee
    qty = cash_after_fee / fill_px

    equity = qty * closes
    equity_curve = pd.Series(equity, index=pd.DatetimeIndex(ts, name="ts"), name="equity_bh")
    trade = Trade(
        entry_idx=0,
        entry_ts=pd.Timestamp(ts[0]),
        entry_price=fill_px,
        exit_idx=n - 1,
        exit_ts=pd.Timestamp(ts[-1]),
        exit_price=float(closes[-1]),
        qty=qty,
        fees_paid=fee,
        pnl_usd=float(equity[-1] - config.initial_capital),
    )
    final = float(equity_curve.iloc[-1])
    return BacktestResult(
        config=config,
        equity_curve=equity_curve,
        trades=[trade],
        final_equity=final,
        total_return_pct=(final - config.initial_capital) / config.initial_capital,
        metadata={"n_bars": n, "n_trades_closed": 1, "kind": "buy_and_hold"},
    )
