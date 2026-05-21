"""SuperTrend baseline — thin wrapper over ``src.signals.supertrend``.

Keeps the signal identical to the production configuration used in the study
(period=10, multiplier=3.0). If this diverges, the research would be measuring
a different thing.

Returns a pd.Series[int] in {-1, 0, 1} aligned to the ohlcv index.
"""

from __future__ import annotations

import pandas as pd

from src.signals.supertrend import compute_supertrend_signals


def supertrend_signal(
    ohlcv: pd.DataFrame,
    period: int = 10,
    multiplier: float = 3.0,
) -> pd.Series:
    """Wrap the SuperTrend signal in the research SignalFn contract.

    Output: pd.Series[int] indexed identical to ohlcv, values in {-1, 0, 1}.
    """
    df = compute_supertrend_signals(ohlcv, period=period, multiplier=multiplier)
    return pd.Series(df["signal"].astype(int).values, index=ohlcv.index, name="supertrend_signal")


def supertrend_direction(
    ohlcv: pd.DataFrame,
    period: int = 10,
    multiplier: float = 3.0,
) -> pd.Series:
    """Direction (1 / -1 / 0) — for inspecting state across bars, not for
    BUY/SELL signals (those come from `supertrend_signal`)."""
    df = compute_supertrend_signals(ohlcv, period=period, multiplier=multiplier)
    return pd.Series(df["direction"].astype(int).values, index=ohlcv.index, name="supertrend_direction")
