"""SuperTrend indicator + signal (función pura, sin I/O).

SuperTrend is an ATR-based trailing-stop trend indicator that flips between
"uptrend" (price above the lower band) and "downtrend" (price above the upper
band). A flip to uptrend emits BUY; a flip to downtrend emits SELL.

Formulas (classic Olivier Seban construction):

    TR[t]   = max(high[t] - low[t], |high[t] - close[t-1]|, |low[t] - close[t-1]|)
    ATR[t]  = rolling mean of TR over `period` bars (simple MA, NOT Wilder's)
    BUB[t]  = (high[t] + low[t]) / 2 + multiplier * ATR[t]   (basic upper band)
    BLB[t]  = (high[t] + low[t]) / 2 - multiplier * ATR[t]   (basic lower band)

    FUB[t] = BUB[t]    if BUB[t] < FUB[t-1]   or close[t-1] > FUB[t-1]  else FUB[t-1]
    FLB[t] = BLB[t]    if BLB[t] > FLB[t-1]   or close[t-1] < FLB[t-1]  else FLB[t-1]

    ST[t], dir[t]:
        if previous direction was DOWN (ST[t-1] == FUB[t-1]):
            if close[t] > FUB[t]:  direction flips to UP → ST[t]=FLB[t]
            else:                   direction stays DOWN  → ST[t]=FUB[t]
        if previous direction was UP (ST[t-1] == FLB[t-1]):
            if close[t] < FLB[t]:  direction flips to DOWN → ST[t]=FUB[t]
            else:                  direction stays UP       → ST[t]=FLB[t]

Signal:
    BUY  (1) when direction flips UP   at bar t
    SELL (-1) when direction flips DOWN at bar t
    HOLD (0) otherwise
"""

from __future__ import annotations

from typing import Any

import numpy.typing as npt
import pandas as pd

_REQUIRED_COLS = frozenset({"ts", "high", "low", "close"})

_DIR_UP = 1
_DIR_DOWN = -1


def _validate_inputs(ohlcv: pd.DataFrame, period: int, multiplier: float) -> None:
    """Validate SuperTrend input parameters and DataFrame."""
    if period < 2:
        raise ValueError(f"period must be >= 2, got {period}")
    if multiplier <= 0:
        raise ValueError(f"multiplier must be > 0, got {multiplier}")
    missing = _REQUIRED_COLS - set(ohlcv.columns)
    if missing:
        raise ValueError(f"ohlcv missing columns: {missing}")
    if ohlcv.empty:
        raise ValueError("ohlcv DataFrame is empty")


def _compute_true_range(
    high: npt.NDArray[Any], low: npt.NDArray[Any], close: npt.NDArray[Any], n: int
) -> list[float]:
    """Compute True Range array."""
    tr = [high[0] - low[0]] + [0.0] * (n - 1)
    for i in range(1, n):
        tr[i] = max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1]),
        )
    return tr


def _init_first_valid_bar(
    i: int,
    basic_upper: npt.NDArray[Any],
    basic_lower: npt.NDArray[Any],
    close: npt.NDArray[Any],
    final_upper: list[float],
    final_lower: list[float],
    supertrend: list[float],
    direction: list[int],
) -> None:
    """Initialize bands/direction for the first bar with valid ATR."""
    final_upper[i] = basic_upper[i]
    final_lower[i] = basic_lower[i]
    if close[i] <= final_upper[i]:
        supertrend[i] = final_upper[i]
        direction[i] = _DIR_DOWN
    else:
        supertrend[i] = final_lower[i]
        direction[i] = _DIR_UP


def _update_bands_and_direction(
    i: int,
    basic_upper: npt.NDArray[Any],
    basic_lower: npt.NDArray[Any],
    close: npt.NDArray[Any],
    final_upper: list[float],
    final_lower: list[float],
    supertrend: list[float],
    direction: list[int],
) -> None:
    """Update final bands and compute direction for bar i (post-warmup)."""
    # Final upper band
    if basic_upper[i] < final_upper[i - 1] or close[i - 1] > final_upper[i - 1]:
        final_upper[i] = basic_upper[i]
    else:
        final_upper[i] = final_upper[i - 1]
    # Final lower band
    if basic_lower[i] > final_lower[i - 1] or close[i - 1] < final_lower[i - 1]:
        final_lower[i] = basic_lower[i]
    else:
        final_lower[i] = final_lower[i - 1]
    # Direction
    prev_dir = direction[i - 1]
    if prev_dir == _DIR_DOWN:
        if close[i] > final_upper[i]:
            direction[i] = _DIR_UP
            supertrend[i] = final_lower[i]
        else:
            direction[i] = _DIR_DOWN
            supertrend[i] = final_upper[i]
    else:
        if close[i] < final_lower[i]:
            direction[i] = _DIR_DOWN
            supertrend[i] = final_upper[i]
        else:
            direction[i] = _DIR_UP
            supertrend[i] = final_lower[i]


def _build_direction_signals(direction: list[int], n: int) -> list[int]:
    """Build signal array from direction transitions."""
    signal = [0] * n
    for i in range(1, n):
        if direction[i - 1] == 0 or direction[i] == 0:
            continue
        if direction[i] == _DIR_UP and direction[i - 1] == _DIR_DOWN:
            signal[i] = 1
        elif direction[i] == _DIR_DOWN and direction[i - 1] == _DIR_UP:
            signal[i] = -1
    return signal


def compute_supertrend_signals(
    ohlcv: pd.DataFrame,
    period: int = 10,
    multiplier: float = 3.0,
) -> pd.DataFrame:
    """Compute SuperTrend signals.

    Args:
        ohlcv: DataFrame with columns ts, high, low, close (ordered ascending).
        period: ATR lookback period (default 10).
        multiplier: ATR multiplier for bands (default 3.0).

    Returns:
        DataFrame with columns: ts, close, supertrend, direction, signal, atr.
        First `period` bars have signal=0 (warm-up).

    Raises:
        ValueError: on bad params / missing cols / empty df.
    """
    _validate_inputs(ohlcv, period, multiplier)

    high = ohlcv["high"].astype(float).to_numpy()
    low = ohlcv["low"].astype(float).to_numpy()
    close = ohlcv["close"].astype(float).to_numpy()
    n = len(ohlcv)

    tr = _compute_true_range(high, low, close, n)
    atr = pd.Series(tr, dtype=float).rolling(window=period, min_periods=period).mean().to_numpy()

    hl2 = (high + low) / 2.0
    basic_upper = hl2 + multiplier * atr
    basic_lower = hl2 - multiplier * atr

    final_upper = [0.0] * n
    final_lower = [0.0] * n
    supertrend = [0.0] * n
    direction = [0] * n

    for i in range(n):
        if pd.isna(atr[i]):
            continue
        if i == 0 or direction[i - 1] == 0:
            _init_first_valid_bar(
                i, basic_upper, basic_lower, close, final_upper, final_lower, supertrend, direction
            )
        else:
            _update_bands_and_direction(
                i, basic_upper, basic_lower, close, final_upper, final_lower, supertrend, direction
            )

    signal = _build_direction_signals(direction, n)

    return pd.DataFrame(
        {
            "ts": ohlcv["ts"].values,
            "close": close,
            "supertrend": supertrend,
            "direction": direction,
            "signal": signal,
            "atr": list(atr),
        }
    )
