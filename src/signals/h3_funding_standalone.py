"""H3-standalone — sin SuperTrend. Funding 8h como driver direccional.

Tesis: funding extremo es señal contrarian autosuficiente.

Reglas:
- BUY (1) cuando funding 8h cruza por debajo del buy_threshold (capitulation).
- SELL (-1) cuando funding 8h cruza por encima del sell_threshold (over-greed).
- HOLD (0) en el resto.

Las cruzadas se detectan con el funding settled inmediatamente anterior al
cierre de la vela. La señal se emite en la vela en que se observa la cruzada.
"""

from __future__ import annotations

import pandas as pd

from src.signals._alignment import align_funding_to_4h

# Two thresholds for capitulation (per pre_registration §3 / alignment_spec §7
# flag amarillo): -0.02% es estricto pero sample chico; -0.01% relajado.
DEFAULT_BUY_THRESHOLD = -0.0002  # -0.02% por 8h
DEFAULT_SELL_THRESHOLD = 0.0005  # +0.05% por 8h


def h3_funding_standalone_signal(
    ohlcv: pd.DataFrame,
    funding_df: pd.DataFrame,
    buy_threshold: float = DEFAULT_BUY_THRESHOLD,
    sell_threshold: float = DEFAULT_SELL_THRESHOLD,
) -> pd.Series:
    """Standalone funding-rate cross signal.

    Args:
        ohlcv: 4h OHLCV.
        funding_df: funding 8h.
        buy_threshold: funding ≤ this triggers BUY on cross-below.
        sell_threshold: funding ≥ this triggers SELL on cross-above.

    Returns:
        Series[int] in {-1, 0, 1}.
    """
    if buy_threshold >= sell_threshold:
        raise ValueError(
            f"buy_threshold ({buy_threshold}) must be < sell_threshold ({sell_threshold})"
        )
    fund_now = align_funding_to_4h(funding_df, ohlcv, agg="last")
    fund_prev = fund_now.shift(1)

    out = pd.Series(0, index=ohlcv.index, dtype="int64")
    buy_cross = (fund_prev > buy_threshold) & (fund_now <= buy_threshold)
    sell_cross = (fund_prev < sell_threshold) & (fund_now >= sell_threshold)
    out.loc[buy_cross] = 1
    out.loc[sell_cross] = -1
    out.name = f"h3_funding_standalone_b{buy_threshold}_s{sell_threshold}"
    return out
