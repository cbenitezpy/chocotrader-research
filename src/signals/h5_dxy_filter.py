"""H5-filter — SuperTrend BUY se ejecuta solo si DXY NO está en uptrend 20d.

Tesis: en régimen de fortalecimiento del USD (DXY uptrend), los activos
de riesgo como BTC tienden a underperform. Filtramos BUYs durante esos
períodos.

"DXY uptrend 20d" se define como: close > MA20 y MA20 con pendiente positiva
(MA20[t] > MA20[t-5]) — un trend filter estable, no instantáneo.
"""

from __future__ import annotations

import pandas as pd

from src.signals._alignment import align_dxy_to_4h
from src.signals._supertrend_baseline import supertrend_signal

MA_WINDOW = 20
SLOPE_LOOKBACK = 5


def _dxy_in_uptrend(dxy_aligned: pd.Series) -> pd.Series:
    """Returns boolean Series: True where DXY is in uptrend 20d.

    Implementation: aligned DXY is 4h-frequency forward-filled from daily.
    Computing rolling 20-day on 4h sampling = rolling 20*6=120 bars. To keep
    semantics close to "20 days", use rolling 120 bars.
    """
    bars_per_day_4h = 6
    ma_bars = MA_WINDOW * bars_per_day_4h  # 120 bars
    slope_bars = SLOPE_LOOKBACK * bars_per_day_4h  # 30 bars
    ma = dxy_aligned.rolling(ma_bars, min_periods=ma_bars).mean()
    slope_up = ma > ma.shift(slope_bars)
    above_ma = dxy_aligned > ma
    return (above_ma & slope_up).fillna(False)


def h5_dxy_filter_signal(
    ohlcv: pd.DataFrame,
    dxy_df: pd.DataFrame,
    st_period: int = 10,
    st_multiplier: float = 3.0,
) -> pd.Series:
    """Filter SuperTrend BUY by absence of DXY uptrend.

    Args:
        ohlcv: 4h OHLCV.
        dxy_df: DXY daily.
        st_period, st_multiplier: SuperTrend params.

    Returns:
        Series[int] in {-1, 0, 1}.
    """
    base = supertrend_signal(ohlcv, period=st_period, multiplier=st_multiplier)
    dxy = align_dxy_to_4h(dxy_df, ohlcv)
    uptrend = _dxy_in_uptrend(dxy)

    out = base.copy()
    out.loc[(base == 1) & uptrend] = 0  # cancel BUY during DXY uptrend
    out.name = "h5_dxy_filter"
    return out.astype(int)
