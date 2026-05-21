"""Tier-3 research: long/short perpetual engine with real funding (critique #1).

The spot engine is long-only. This engine models a 1x perpetual future that can
hold long OR short, charging/earning the REAL historical funding rate every 8h.

Why 1x (no leverage): it isolates the effect of *shorting* (capturing bear
markets as profit) from the confound of liquidation risk. Leverage would add
liquidation mechanics that are a separate study; 1x is the cleanest test of
"does the ability to short add edge?".

Funding convention (Binance perpetuals):
    At each 8h settlement, a position pays  qty * mark_price * funding_rate.
    funding_rate > 0  => longs pay shorts (long loses, short gains).
    Applied as:  cash -= position_qty * mark_price * funding_rate
    (position_qty > 0 long, < 0 short).

Fill model: signal at close[t] → fill at open[t+1] (next_open), same as spot.
Costs: taker fee + slippage per side on every entry/exit/flip.

Returns the same BacktestResult shape as the spot engine.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.backtest.engine import BacktestConfig, BacktestResult, Trade, _apply_fill_price


def _funding_by_bar(funding_df: pd.DataFrame, ts: np.ndarray) -> np.ndarray:
    """Map each 4h bar to the funding rate settled within [ts_i, ts_i + 4h).

    Returns an array aligned to bars; 0.0 where no settlement falls in the bar.
    """
    ftime = pd.to_datetime(funding_df["funding_time"], utc=True).astype("int64").to_numpy()
    frate = funding_df["funding_rate"].to_numpy(dtype=float)
    bar_ns = pd.to_datetime(pd.Series(ts), utc=True).astype("int64").to_numpy()
    step_ns = int(pd.Timedelta(hours=4).value)
    out = np.zeros(len(bar_ns), dtype=float)
    j = 0
    n_f = len(ftime)
    for i in range(len(bar_ns)):
        lo, hi = bar_ns[i], bar_ns[i] + step_ns
        while j < n_f and ftime[j] < lo:
            j += 1
        # sum any settlements that fall in [lo, hi) — normally 0 or 1
        k = j
        acc = 0.0
        while k < n_f and ftime[k] < hi:
            acc += frate[k]
            k += 1
        out[i] = acc
    return out


def simulate_long_short(
    ohlcv: pd.DataFrame,
    signal: pd.Series,
    funding_df: pd.DataFrame,
    config: BacktestConfig | None = None,
) -> BacktestResult:
    """1x long/short perpetual backtest with real funding.

    Signal semantics:
        +1 => target LONG, -1 => target SHORT, 0 => hold current position.
    Position is flipped on opposite signal (close + open), filled next_open.
    """
    if config is None:
        config = BacktestConfig()
    if len(signal) != len(ohlcv):
        raise ValueError("signal length differs from ohlcv length")
    if not ohlcv["ts"].is_monotonic_increasing:
        raise ValueError("ohlcv ts must be monotonic ascending")

    n = len(ohlcv)
    ts = ohlcv["ts"].to_numpy()
    opens = ohlcv["open"].to_numpy(dtype=float)
    closes = ohlcv["close"].to_numpy(dtype=float)
    sigs = signal.to_numpy(dtype=int)
    funding = _funding_by_bar(funding_df, ts)

    # Fully-funded accounting (consistent with the spot engine):
    #   open:  cash -= qty*entry  (long qty>0 spends cash; short qty<0 receives)
    #   close: cash += qty*exit
    #   equity = cash + qty*close   (= cash0 + qty*(close-entry), i.e. unrealised PnL)
    # This is a 1x perpetual: notional = position_pct of equity, no leverage.
    cash = config.initial_capital
    qty = 0.0           # >0 long, <0 short
    entry_price = 0.0
    equity = np.zeros(n, dtype=float)
    trades: list[Trade] = []
    open_trade: Trade | None = None
    pending = 0

    def _open(direction: int, i: int) -> tuple[float, float, Trade]:
        nonlocal cash
        side = "BUY" if direction > 0 else "SELL"
        fill_px = _apply_fill_price(opens[i], side, config.slippage_per_side)
        # size off current equity (cash, since we open only when flat)
        notional = cash * config.position_pct
        new_qty = (notional / fill_px) * (1 if direction > 0 else -1)
        fee = abs(new_qty) * fill_px * config.fee_per_side
        cash -= new_qty * fill_px   # long spends, short receives
        cash -= fee
        tr = Trade(entry_idx=i, entry_ts=pd.Timestamp(ts[i]), entry_price=fill_px,
                   qty=new_qty, fees_paid=fee)
        return new_qty, fill_px, tr

    def _close(i: int, cur_qty: float, cur_entry: float, tr: Trade | None) -> None:
        nonlocal cash
        side = "SELL" if cur_qty > 0 else "BUY"
        fill_px = _apply_fill_price(opens[i], side, config.slippage_per_side)
        fee = abs(cur_qty) * fill_px * config.fee_per_side
        cash += cur_qty * fill_px   # long sells back, short buys back
        cash -= fee
        if tr is not None:
            tr.exit_idx = i
            tr.exit_ts = pd.Timestamp(ts[i])
            tr.exit_price = fill_px
            tr.fees_paid += fee
            tr.pnl_usd = cur_qty * (fill_px - cur_entry) - tr.fees_paid
            trades.append(tr)

    for i in range(n):
        # 1) act on pending signal at open[i]
        if pending != 0:
            target = pending
            if qty == 0:
                qty, entry_price, open_trade = _open(target, i)
            elif (qty > 0) != (target > 0):
                _close(i, qty, entry_price, open_trade)
                qty, entry_price, open_trade = _open(target, i)
            pending = 0

        # 2) funding settlement (if any) while holding
        if qty != 0 and funding[i] != 0.0:
            cash -= qty * closes[i] * funding[i]

        # 3) mark-to-market (unrealised PnL via cash + qty*close)
        equity[i] = cash + qty * closes[i]

        # 4) observe signal
        if sigs[i] != 0:
            pending = int(sigs[i])

    # close residual at last close (no slippage on synthetic close-out)
    if qty != 0 and open_trade is not None:
        fill_px = closes[-1]
        fee = abs(qty) * fill_px * config.fee_per_side
        cash += qty * fill_px - fee
        open_trade.exit_idx = n - 1
        open_trade.exit_ts = pd.Timestamp(ts[-1])
        open_trade.exit_price = fill_px
        open_trade.fees_paid += fee
        open_trade.pnl_usd = qty * (fill_px - entry_price) - open_trade.fees_paid
        trades.append(open_trade)
        qty = 0.0
        equity[-1] = cash

    equity_curve = pd.Series(equity, index=pd.DatetimeIndex(ts, name="ts"), name="equity_ls")
    final = float(equity_curve.iloc[-1])
    return BacktestResult(
        config=config,
        equity_curve=equity_curve,
        trades=trades,
        final_equity=final,
        total_return_pct=(final - config.initial_capital) / config.initial_capital,
        metadata={"n_bars": n, "n_trades_closed": len(trades), "kind": "long_short_1x"},
    )
