"""H1-standalone — sin SuperTrend. Sólo F&G como driver.

Tesis: F&G extremos son señales contrarian autosuficientes.

Reglas:
- BUY (1) cuando F&G cruza HACIA ABAJO el threshold_buy (i.e. era > thr y pasa a ≤).
- SELL (-1) cuando F&G cruza HACIA ARRIBA el threshold_sell (i.e. era < thr y pasa a ≥).
- HOLD (0) en el resto.

Por construcción, "cruzar" se detecta con el valor del día previo. Esto
garantiza que la señal del bar T se genera con info de los días T-1 y T-2.
"""

from __future__ import annotations

import pandas as pd

from src.signals._alignment import align_daily_to_4h

DEFAULT_BUY_THRESHOLD = 25
DEFAULT_SELL_THRESHOLD = 75


def h1_fg_standalone_signal(
    ohlcv: pd.DataFrame,
    fng_df: pd.DataFrame,
    buy_threshold: int = DEFAULT_BUY_THRESHOLD,
    sell_threshold: int = DEFAULT_SELL_THRESHOLD,
) -> pd.Series:
    """Standalone F&G threshold-cross signal.

    Args:
        ohlcv: 4h OHLCV.
        fng_df: F&G daily.
        buy_threshold: emit BUY when F&G crosses below this.
        sell_threshold: emit SELL when F&G crosses above this.

    Returns:
        Series[int] in {-1, 0, 1}.
    """
    if buy_threshold >= sell_threshold:
        raise ValueError(
            f"buy_threshold ({buy_threshold}) must be < sell_threshold ({sell_threshold})"
        )
    fg_now = align_daily_to_4h(fng_df, ohlcv, value_col="value", date_col="date")
    # fg_prev = F&G a bar T-1 (= shift forward by 1 bar — esto es ALINEADO al
    # input, no a la fuente externa, así que es seguro: ya pasó por el helper
    # de alignment sin look-ahead).
    fg_prev = fg_now.shift(1)

    out = pd.Series(0, index=ohlcv.index, dtype="int64")
    buy_cross = (fg_prev > buy_threshold) & (fg_now <= buy_threshold)
    sell_cross = (fg_prev < sell_threshold) & (fg_now >= sell_threshold)
    out.loc[buy_cross] = 1
    out.loc[sell_cross] = -1
    out.name = f"h1_fg_standalone_b{buy_threshold}_s{sell_threshold}"
    return out
