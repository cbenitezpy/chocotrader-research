"""Research v6 — signal generators (no I/O, pure functions).

Each signal generator takes:
    - ohlcv: pd.DataFrame with columns [ts, open, high, low, close, volume]
    - external: dict[str, pd.DataFrame] with pre-loaded F&G / funding / DXY

and returns:
    - pd.Series[int] indexed identically to ohlcv, values in {-1, 0, 1}
        (-1 = SELL, 0 = HOLD, 1 = BUY)

See research/v6/data/alignment_spec.md for alignment contract.
"""
