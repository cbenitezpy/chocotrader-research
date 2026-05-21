"""H3-filter — SuperTrend BUY se ejecuta solo si funding promedio 24h < threshold.

Tesis: cuando funding 24h-avg es alto (>0.03%), el mercado está sobrecomprado
en perpetuals, lo que reduce probabilidad de continuación alcista en spot.
Filtramos esos BUYs.

SELL del SuperTrend: se mantiene + adicionalmente se ejecuta si funding 24h-avg
sobrepasa un umbral más extremo (sobre-greed → tomar profits).
"""

from __future__ import annotations

import pandas as pd

from src.signals._alignment import align_funding_to_4h
from src.signals._supertrend_baseline import supertrend_signal

DEFAULT_BUY_BLOCK = 0.0003  # 0.03% por 8h promedio 24h
DEFAULT_SELL_TRIGGER = 0.0006  # 0.06% por 8h promedio 24h


def h3_funding_filter_signal(
    ohlcv: pd.DataFrame,
    funding_df: pd.DataFrame,
    buy_block_threshold: float = DEFAULT_BUY_BLOCK,
    sell_trigger_threshold: float = DEFAULT_SELL_TRIGGER,
    st_period: int = 10,
    st_multiplier: float = 3.0,
) -> pd.Series:
    """Filter SuperTrend by funding rate 24h average.

    Args:
        ohlcv: 4h OHLCV.
        funding_df: funding 8h (columns: funding_time, funding_rate).
        buy_block_threshold: si avg 24h ≥ esto, anular BUY.
        sell_trigger_threshold: si avg 24h ≥ esto, emitir SELL extra.

    Returns:
        Series[int] in {-1, 0, 1}.
    """
    if buy_block_threshold > sell_trigger_threshold:
        raise ValueError(
            f"buy_block ({buy_block_threshold}) must be <= sell_trigger ({sell_trigger_threshold})"
        )
    base = supertrend_signal(ohlcv, period=st_period, multiplier=st_multiplier)
    funding_24h = align_funding_to_4h(funding_df, ohlcv, agg="avg", window_hours=24)

    out = base.copy()
    # Block BUY where avg funding too high or missing
    block_buy = (funding_24h.isna()) | (funding_24h >= buy_block_threshold)
    out.loc[(base == 1) & block_buy] = 0
    # Force SELL on extreme greed (overrides HOLD; preserves existing SELL)
    force_sell = (funding_24h.notna()) & (funding_24h >= sell_trigger_threshold) & (base != -1)
    out.loc[force_sell] = -1
    out.name = "h3_funding_filter"
    return out.astype(int)
