"""H1-filter — SuperTrend BUY se ejecuta solo si F&G ≤ threshold.

Tesis: BUY entries durante "Extreme Fear" (F&G ≤ 25) anticipan rebotes mejor
que BUY entries indiscriminados. SELL entries del SuperTrend se mantienen
intactos (no filtramos exits — la idea es proteger entradas, no atrapar exits).

Si en algún bar el SuperTrend emite BUY pero F&G > threshold → el BUY se anula.
"""

from __future__ import annotations

import pandas as pd

from src.signals._alignment import align_daily_to_4h
from src.signals._supertrend_baseline import supertrend_signal

DEFAULT_FG_THRESHOLD = 25


def h1_fg_filter_signal(
    ohlcv: pd.DataFrame,
    fng_df: pd.DataFrame,
    threshold: int = DEFAULT_FG_THRESHOLD,
    st_period: int = 10,
    st_multiplier: float = 3.0,
) -> pd.Series:
    """Filter SuperTrend BUY by F&G ≤ threshold.

    Args:
        ohlcv: 4h OHLCV.
        fng_df: F&G daily (columns: date, value, ...).
        threshold: F&G upper bound for BUY admission (default 25).
        st_period, st_multiplier: SuperTrend params (matches bot defaults).

    Returns:
        Series[int] in {-1, 0, 1}.
    """
    base = supertrend_signal(ohlcv, period=st_period, multiplier=st_multiplier)
    fg_value = align_daily_to_4h(fng_df, ohlcv, value_col="value", date_col="date")

    out = base.copy()
    # Cancel BUY (1 → 0) where F&G > threshold OR F&G missing
    mask_block = (fg_value.isna()) | (fg_value > threshold)
    buy_mask = (base == 1) & mask_block
    out.loc[buy_mask] = 0
    out.name = f"h1_fg_filter_le_{threshold}"
    return out.astype(int)
