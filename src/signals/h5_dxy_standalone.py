"""H5-standalone — sin SuperTrend. DXY como driver direccional.

Tesis: cuando DXY cruza por debajo de su MA20, comienza un régimen débil de
USD → favorable para BTC. Inverso al cruzar por arriba.

Reglas:
- BUY (1) en la primera vela donde DXY cruza desde arriba de MA20 hacia abajo.
- SELL (-1) en la primera vela donde DXY cruza desde abajo hacia arriba.
- HOLD (0) en el resto.

Las cruzadas usan close[t] vs MA[t] y close[t-bar_lookback] vs MA[t-bar_lookback].
"""

from __future__ import annotations

import pandas as pd

from src.signals._alignment import align_dxy_to_4h

MA_WINDOW = 20  # días
BARS_PER_DAY_4H = 6


def h5_dxy_standalone_signal(
    ohlcv: pd.DataFrame,
    dxy_df: pd.DataFrame,
    ma_window_days: int = MA_WINDOW,
) -> pd.Series:
    """Cross of DXY vs its own MA — contrarian for BTC.

    Args:
        ohlcv: 4h OHLCV.
        dxy_df: DXY daily.
        ma_window_days: MA period in DAYS (converted to bars internally).

    Returns:
        Series[int] in {-1, 0, 1}.
    """
    dxy = align_dxy_to_4h(dxy_df, ohlcv)
    ma_bars = ma_window_days * BARS_PER_DAY_4H
    ma = dxy.rolling(ma_bars, min_periods=ma_bars).mean()

    # Cast to nullable boolean dtype to handle NaN cleanly; fillna(False) before
    # the bitwise ops to avoid `~float` errors at warm-up.
    above_now = (dxy > ma).fillna(False).astype(bool)
    above_prev = above_now.shift(1).fillna(False).astype(bool)

    out = pd.Series(0, index=ohlcv.index, dtype="int64")
    cross_below = above_prev & (~above_now)
    cross_above = (~above_prev) & above_now
    out.loc[cross_below] = 1
    out.loc[cross_above] = -1
    out.name = f"h5_dxy_standalone_ma{ma_window_days}d"
    return out
